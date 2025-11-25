"""
PHASE 1.2: Network Egress Filtering & SSRF Protection

Prevents Server-Side Request Forgery (SSRF) attacks by blocking:
- Localhost/loopback addresses (127.0.0.0/8)
- Private network ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Link-local addresses (169.254.0.0/16)
- Cloud metadata endpoints (169.254.169.254)

Usage:
    from agent.security.network import NetworkSecurityValidator, is_url_safe

    validator = NetworkSecurityValidator()

    # Check URL before making request
    is_safe, reason = validator.validate_url("https://api.example.com/data")
    if not is_safe:
        raise SecurityError(f"URL blocked: {reason}")

    # Or use the convenience function
    if not is_url_safe("http://localhost:8080"):
        print("URL is blocked!")
"""

from __future__ import annotations

import ipaddress
import re
import socket
from typing import List, Optional, Set, Tuple
from urllib.parse import urlparse

from agent.core_logging import log_event


# ============================================================================
# Blocked IP Ranges (CIDR notation)
# ============================================================================

BLOCKED_IP_RANGES: List[str] = [
    # Localhost/Loopback
    "127.0.0.0/8",          # IPv4 loopback
    "::1/128",              # IPv6 loopback

    # Private Networks (RFC 1918)
    "10.0.0.0/8",           # Class A private
    "172.16.0.0/12",        # Class B private
    "192.168.0.0/16",       # Class C private

    # Link-local
    "169.254.0.0/16",       # IPv4 link-local (includes cloud metadata!)
    "fe80::/10",            # IPv6 link-local

    # Carrier-grade NAT
    "100.64.0.0/10",

    # Documentation/Test ranges
    "192.0.2.0/24",         # TEST-NET-1
    "198.51.100.0/24",      # TEST-NET-2
    "203.0.113.0/24",       # TEST-NET-3

    # Broadcast
    "255.255.255.255/32",

    # IPv6 special
    "fc00::/7",             # Unique local address
    "ff00::/8",             # Multicast
]

# Specific IPs to always block (cloud metadata endpoints)
BLOCKED_IPS: Set[str] = {
    "169.254.169.254",      # AWS/GCP/Azure metadata
    "metadata.google.internal",
    "metadata.gcp.internal",
}

# Blocked hostnames
BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "metadata.gcp.internal",
    "169.254.169.254",
}

# Blocked URL schemes
BLOCKED_SCHEMES: Set[str] = {
    "file",
    "ftp",
    "gopher",
    "data",
    "javascript",
}

# Allowed schemes
ALLOWED_SCHEMES: Set[str] = {
    "http",
    "https",
}


class SSRFError(Exception):
    """Raised when a URL fails SSRF validation."""
    pass


class NetworkSecurityValidator:
    """
    Validates URLs and IPs against security policies to prevent SSRF attacks.

    Features:
    - Block private/internal IP ranges
    - Block cloud metadata endpoints
    - DNS rebinding protection
    - Scheme validation
    - Custom allowlist/blocklist support
    """

    def __init__(
        self,
        additional_blocked_ranges: Optional[List[str]] = None,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        allow_localhost: bool = False,
    ):
        """
        Initialize network security validator.

        Args:
            additional_blocked_ranges: Extra CIDR ranges to block
            allowed_domains: Allowlist of domains (if set, only these are allowed)
            blocked_domains: Blocklist of specific domains
            allow_localhost: Allow localhost connections (DANGEROUS - only for testing)
        """
        self.allow_localhost = allow_localhost
        self.allowed_domains = allowed_domains
        self.blocked_domains = blocked_domains or set()

        # Parse blocked IP networks
        self._blocked_networks: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for cidr in BLOCKED_IP_RANGES:
            try:
                self._blocked_networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                pass  # Skip invalid CIDR

        # Add additional blocked ranges
        if additional_blocked_ranges:
            for cidr in additional_blocked_ranges:
                try:
                    self._blocked_networks.append(ipaddress.ip_network(cidr, strict=False))
                except ValueError:
                    pass

        # Statistics
        self.total_checks = 0
        self.blocked_count = 0

    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a URL against security policies.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_safe, rejection_reason)
            - is_safe: True if URL is safe to request
            - rejection_reason: Human-readable reason if blocked, None if safe
        """
        self.total_checks += 1

        try:
            parsed = urlparse(url)
        except Exception as e:
            self.blocked_count += 1
            return False, f"Invalid URL format: {e}"

        # Check scheme
        scheme = parsed.scheme.lower()
        if scheme in BLOCKED_SCHEMES:
            self._log_blocked(url, f"blocked scheme: {scheme}")
            return False, f"Blocked URL scheme: {scheme}"

        if scheme not in ALLOWED_SCHEMES:
            self._log_blocked(url, f"unknown scheme: {scheme}")
            return False, f"Unknown URL scheme: {scheme}"

        # Check hostname
        hostname = parsed.hostname
        if not hostname:
            self._log_blocked(url, "missing hostname")
            return False, "URL missing hostname"

        hostname_lower = hostname.lower()

        # Check blocked hostnames
        if hostname_lower in BLOCKED_HOSTNAMES and not self.allow_localhost:
            self._log_blocked(url, f"blocked hostname: {hostname}")
            return False, f"Blocked hostname: {hostname}"

        # Check allowed domains (allowlist mode)
        if self.allowed_domains:
            if not self._domain_matches_allowlist(hostname_lower):
                self._log_blocked(url, "not in allowlist")
                return False, f"Domain not in allowlist: {hostname}"

        # Check blocked domains
        if self._domain_matches_blocklist(hostname_lower):
            self._log_blocked(url, f"blocked domain: {hostname}")
            return False, f"Blocked domain: {hostname}"

        # Resolve hostname and check IP
        try:
            ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            for family, _, _, _, sockaddr in ip_addresses:
                ip_str = sockaddr[0]

                # Check if IP is blocked
                is_blocked, reason = self._is_ip_blocked(ip_str)
                if is_blocked:
                    self._log_blocked(url, f"resolves to blocked IP: {ip_str} ({reason})")
                    return False, f"URL resolves to blocked IP: {ip_str} ({reason})"

        except socket.gaierror as e:
            # DNS resolution failed - could be a sign of DNS rebinding attack
            # For security, we block unresolvable hostnames
            self._log_blocked(url, f"DNS resolution failed: {e}")
            return False, f"DNS resolution failed for {hostname}"

        return True, None

    def _is_ip_blocked(self, ip_str: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an IP address is in blocked ranges.

        Args:
            ip_str: IP address string

        Returns:
            Tuple of (is_blocked, reason)
        """
        # Check specific blocked IPs
        if ip_str in BLOCKED_IPS:
            return True, "cloud metadata endpoint"

        try:
            ip = ipaddress.ip_address(ip_str)

            # Allow localhost if configured
            if self.allow_localhost and ip.is_loopback:
                return False, None

            # Check against blocked networks
            for network in self._blocked_networks:
                if ip in network:
                    return True, f"in blocked range {network}"

            # Additional checks
            if ip.is_private:
                return True, "private IP"
            if ip.is_loopback:
                return True, "loopback address"
            if ip.is_link_local:
                return True, "link-local address"
            if ip.is_multicast:
                return True, "multicast address"
            if ip.is_reserved:
                return True, "reserved address"

            return False, None

        except ValueError:
            return True, "invalid IP address"

    def _domain_matches_allowlist(self, hostname: str) -> bool:
        """Check if hostname matches any allowed domain."""
        if not self.allowed_domains:
            return True

        for domain in self.allowed_domains:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return True
        return False

    def _domain_matches_blocklist(self, hostname: str) -> bool:
        """Check if hostname matches any blocked domain."""
        for domain in self.blocked_domains:
            if hostname == domain or hostname.endswith(f".{domain}"):
                return True
        return False

    def _log_blocked(self, url: str, reason: str) -> None:
        """Log blocked URL attempt."""
        self.blocked_count += 1
        log_event("ssrf_blocked", {
            "url": url[:200],  # Truncate for logging
            "reason": reason,
        })

    def get_statistics(self) -> dict:
        """Get validation statistics."""
        return {
            "total_checks": self.total_checks,
            "blocked_count": self.blocked_count,
            "block_rate": self.blocked_count / max(self.total_checks, 1),
        }


# ============================================================================
# Convenience Functions
# ============================================================================

# Global validator instance
_default_validator: Optional[NetworkSecurityValidator] = None


def get_default_validator() -> NetworkSecurityValidator:
    """Get or create the default network security validator."""
    global _default_validator
    if _default_validator is None:
        _default_validator = NetworkSecurityValidator()
    return _default_validator


def is_url_safe(url: str) -> bool:
    """
    Quick check if a URL is safe to request.

    Args:
        url: URL to check

    Returns:
        True if safe, False if blocked
    """
    validator = get_default_validator()
    is_safe, _ = validator.validate_url(url)
    return is_safe


def is_ip_blocked(ip_str: str) -> bool:
    """
    Check if an IP address is in blocked ranges.

    Args:
        ip_str: IP address string

    Returns:
        True if blocked, False if allowed
    """
    validator = get_default_validator()
    is_blocked, _ = validator._is_ip_blocked(ip_str)
    return is_blocked


def validate_url_or_raise(url: str) -> None:
    """
    Validate URL and raise SSRFError if blocked.

    Args:
        url: URL to validate

    Raises:
        SSRFError: If URL is blocked
    """
    validator = get_default_validator()
    is_safe, reason = validator.validate_url(url)
    if not is_safe:
        raise SSRFError(f"SSRF protection blocked URL: {reason}")
