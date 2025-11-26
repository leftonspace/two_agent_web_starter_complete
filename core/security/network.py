"""
PHASE 7.1: Network Domain Validation and Configuration

Provides domain-based network restrictions for sandbox execution:
- DomainValidator: Check if URLs/domains are in the allowlist
- NetworkConfig: Generate proxy env vars and firewall rules

This module complements the SSRF protection in agent/security/network.py
by providing sandbox-specific network configuration.

Usage:
    from core.security.network import DomainValidator, NetworkConfig

    # Validate domains
    validator = DomainValidator(["github.com", "pypi.org"])
    if validator.is_allowed("https://api.github.com/repos"):
        print("URL is allowed")

    # Generate proxy configuration
    config = NetworkConfig()
    env_vars = config.get_proxy_env_vars(["github.com"])
    iptables = config.generate_iptables_rules(["github.com"])
"""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Localhost patterns that are blocked by default
LOCALHOST_PATTERNS: Set[str] = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
}

# Private IP ranges (blocked by default)
PRIVATE_IP_RANGES: List[str] = [
    "127.0.0.0/8",      # Loopback
    "10.0.0.0/8",       # Private Class A
    "172.16.0.0/12",    # Private Class B
    "192.168.0.0/16",   # Private Class C
    "169.254.0.0/16",   # Link-local (includes cloud metadata)
    "::1/128",          # IPv6 loopback
    "fc00::/7",         # IPv6 unique local
    "fe80::/10",        # IPv6 link-local
]

# Default proxy port for validation proxy
DEFAULT_PROXY_PORT = 8118


# ============================================================================
# Domain Validator
# ============================================================================


class DomainValidator:
    """
    Validates URLs and domains against an allowlist.

    Rules:
    - Exact match: "github.com" matches "github.com"
    - Subdomain match: "github.com" allows "api.github.com", "raw.githubusercontent.com" does NOT
    - Subdomains of allowed domains are automatically allowed
    - localhost and private IPs blocked by default
    - IP addresses blocked unless explicitly allowed
    """

    def __init__(
        self,
        allowed_domains: List[str],
        allow_localhost: bool = False,
        allow_private_ips: bool = False,
    ) -> None:
        """
        Initialize domain validator.

        Args:
            allowed_domains: List of allowed domain names
            allow_localhost: Whether to allow localhost (default: False)
            allow_private_ips: Whether to allow private IP ranges (default: False)
        """
        # Normalize and store allowed domains
        self._allowed_domains: Set[str] = {
            d.lower().strip().lstrip(".")
            for d in allowed_domains
            if d and d.strip()
        }
        self._allow_localhost = allow_localhost
        self._allow_private_ips = allow_private_ips

        # Parse private IP networks
        self._private_networks: List[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for cidr in PRIVATE_IP_RANGES:
            try:
                self._private_networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError:
                pass

        # Statistics
        self.checks_performed = 0
        self.checks_blocked = 0

    @property
    def allowed_domains(self) -> List[str]:
        """Get list of allowed domains."""
        return sorted(self._allowed_domains)

    def is_allowed(self, url: str) -> bool:
        """
        Check if a URL is allowed based on its domain.

        Args:
            url: Full URL to check (e.g., "https://api.github.com/repos")

        Returns:
            True if allowed, False if blocked
        """
        self.checks_performed += 1

        try:
            domain = self.extract_domain(url)
            if not domain:
                self.checks_blocked += 1
                return False

            result = self.is_allowed_domain(domain)
            if not result:
                self.checks_blocked += 1
            return result

        except Exception as e:
            logger.debug(f"URL validation error for '{url}': {e}")
            self.checks_blocked += 1
            return False

    def is_allowed_domain(self, domain: str) -> bool:
        """
        Check if a domain is in the allowlist.

        Args:
            domain: Domain name to check (e.g., "api.github.com")

        Returns:
            True if allowed, False if blocked
        """
        if not domain:
            return False

        domain = domain.lower().strip()

        # Check localhost
        if domain in LOCALHOST_PATTERNS:
            if self._allow_localhost:
                return True
            logger.debug(f"Domain '{domain}' blocked: localhost not allowed")
            return False

        # Check if it's an IP address
        if self._is_ip_address(domain):
            return self._is_ip_allowed(domain)

        # Check domain allowlist
        # Empty allowlist means nothing is allowed
        if not self._allowed_domains:
            logger.debug(f"Domain '{domain}' blocked: no domains in allowlist")
            return False

        # Check exact match or subdomain match
        for allowed in self._allowed_domains:
            if domain == allowed:
                return True
            # Check if domain is a subdomain of allowed domain
            if domain.endswith("." + allowed):
                return True

        logger.debug(f"Domain '{domain}' blocked: not in allowlist")
        return False

    def extract_domain(self, url: str) -> str:
        """
        Extract domain from a URL.

        Args:
            url: URL to parse

        Returns:
            Domain name (lowercase), or empty string if invalid

        Examples:
            "https://api.github.com/repos" -> "api.github.com"
            "http://localhost:8080/path" -> "localhost"
            "github.com" -> "github.com" (assumes https)
        """
        if not url:
            return ""

        url = url.strip()

        # Add scheme if missing (for urlparse to work correctly)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', url):
            url = "https://" + url

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if hostname:
                return hostname.lower()

            return ""

        except Exception as e:
            logger.debug(f"Failed to parse URL '{url}': {e}")
            return ""

    def _is_ip_address(self, value: str) -> bool:
        """Check if a string is an IP address."""
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def _is_ip_allowed(self, ip_str: str) -> bool:
        """Check if an IP address is allowed."""
        try:
            ip = ipaddress.ip_address(ip_str)

            # Check localhost
            if ip.is_loopback:
                return self._allow_localhost

            # Check private ranges
            if ip.is_private or ip.is_link_local or ip.is_reserved:
                if not self._allow_private_ips:
                    logger.debug(f"IP '{ip_str}' blocked: private/reserved IP")
                    return False

            # Check if IP is in private networks
            if not self._allow_private_ips:
                for network in self._private_networks:
                    if ip in network:
                        logger.debug(f"IP '{ip_str}' blocked: in private range {network}")
                        return False

            # For public IPs, check if explicitly in allowlist
            # IPs must be explicitly allowed (not subdomain matching)
            if ip_str in self._allowed_domains:
                return True

            logger.debug(f"IP '{ip_str}' blocked: IP addresses must be explicitly allowed")
            return False

        except ValueError:
            return False

    def get_statistics(self) -> Dict[str, int]:
        """Get validation statistics."""
        return {
            "checks_performed": self.checks_performed,
            "checks_blocked": self.checks_blocked,
            "checks_allowed": self.checks_performed - self.checks_blocked,
        }


# ============================================================================
# Network Configuration Generator
# ============================================================================


class NetworkConfig:
    """
    Generates network configuration for sandbox isolation.

    Supports:
    - HTTP/HTTPS proxy environment variables
    - Linux iptables rules
    - macOS pf (packet filter) rules
    """

    def __init__(
        self,
        proxy_host: str = "127.0.0.1",
        proxy_port: int = DEFAULT_PROXY_PORT,
    ) -> None:
        """
        Initialize network configuration generator.

        Args:
            proxy_host: Host for proxy server
            proxy_port: Port for proxy server
        """
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def get_proxy_env_vars(
        self,
        allowed_domains: List[str],
        include_no_proxy: bool = True,
    ) -> Dict[str, str]:
        """
        Generate environment variables for proxy configuration.

        These env vars tell applications to route traffic through a proxy
        that can enforce the domain allowlist.

        Args:
            allowed_domains: List of allowed domains (for documentation)
            include_no_proxy: Whether to include NO_PROXY for localhost

        Returns:
            Dictionary of environment variables
        """
        proxy_url = f"http://{self.proxy_host}:{self.proxy_port}"

        env_vars = {
            # Standard proxy variables (lowercase)
            "http_proxy": proxy_url,
            "https_proxy": proxy_url,
            # Uppercase versions (some apps use these)
            "HTTP_PROXY": proxy_url,
            "HTTPS_PROXY": proxy_url,
            # Custom variable for our proxy to read allowed domains
            "JARVIS_ALLOWED_DOMAINS": ",".join(allowed_domains),
        }

        if include_no_proxy:
            # NO_PROXY bypasses the proxy for these hosts
            # We only bypass localhost if explicitly needed
            env_vars["no_proxy"] = "127.0.0.1,::1"
            env_vars["NO_PROXY"] = "127.0.0.1,::1"

        return env_vars

    def generate_iptables_rules(
        self,
        allowed_domains: List[str],
        chain_name: str = "JARVIS_EGRESS",
        interface: str = "eth0",
    ) -> List[str]:
        """
        Generate iptables rules for Linux network filtering.

        Note: These rules filter by IP, not domain. For domain filtering,
        a proxy or DNS-based solution is needed.

        Args:
            allowed_domains: List of allowed domains (resolved to IPs)
            chain_name: Name for the iptables chain
            interface: Network interface to filter

        Returns:
            List of iptables commands
        """
        rules = []

        # Create new chain
        rules.append(f"iptables -N {chain_name} 2>/dev/null || true")
        rules.append(f"iptables -F {chain_name}")

        # Allow established connections
        rules.append(
            f"iptables -A {chain_name} -m state --state ESTABLISHED,RELATED -j ACCEPT"
        )

        # Allow DNS (needed for domain resolution)
        rules.append(f"iptables -A {chain_name} -p udp --dport 53 -j ACCEPT")
        rules.append(f"iptables -A {chain_name} -p tcp --dport 53 -j ACCEPT")

        # Block localhost/private ranges by default
        rules.append(f"iptables -A {chain_name} -d 127.0.0.0/8 -j DROP")
        rules.append(f"iptables -A {chain_name} -d 10.0.0.0/8 -j DROP")
        rules.append(f"iptables -A {chain_name} -d 172.16.0.0/12 -j DROP")
        rules.append(f"iptables -A {chain_name} -d 192.168.0.0/16 -j DROP")
        rules.append(f"iptables -A {chain_name} -d 169.254.0.0/16 -j DROP")

        # Resolve domains to IPs and allow them
        resolved_ips = self._resolve_domains(allowed_domains)
        for ip in resolved_ips:
            rules.append(f"iptables -A {chain_name} -d {ip} -j ACCEPT")

        # Default deny for HTTP/HTTPS
        rules.append(f"iptables -A {chain_name} -p tcp --dport 80 -j DROP")
        rules.append(f"iptables -A {chain_name} -p tcp --dport 443 -j DROP")

        # Add chain to OUTPUT
        rules.append(
            f"iptables -C OUTPUT -o {interface} -j {chain_name} 2>/dev/null || "
            f"iptables -A OUTPUT -o {interface} -j {chain_name}"
        )

        return rules

    def generate_pf_rules(
        self,
        allowed_domains: List[str],
        anchor_name: str = "jarvis_sandbox",
    ) -> List[str]:
        """
        Generate pf (packet filter) rules for macOS network filtering.

        Note: macOS requires pf to be enabled: sudo pfctl -e

        Args:
            allowed_domains: List of allowed domains (resolved to IPs)
            anchor_name: Name for the pf anchor

        Returns:
            List of pf rule lines (write to /etc/pf.anchors/jarvis_sandbox)
        """
        rules = []

        # Header comment
        rules.append(f"# JARVIS Sandbox Network Rules")
        rules.append(f"# Anchor: {anchor_name}")
        rules.append("")

        # Block all by default for HTTP/HTTPS
        rules.append("# Default: block outgoing HTTP/HTTPS")
        rules.append("block out proto tcp from any to any port 80")
        rules.append("block out proto tcp from any to any port 443")
        rules.append("")

        # Allow DNS
        rules.append("# Allow DNS")
        rules.append("pass out proto udp from any to any port 53")
        rules.append("pass out proto tcp from any to any port 53")
        rules.append("")

        # Block private ranges
        rules.append("# Block private/localhost")
        rules.append("block out from any to 127.0.0.0/8")
        rules.append("block out from any to 10.0.0.0/8")
        rules.append("block out from any to 172.16.0.0/12")
        rules.append("block out from any to 192.168.0.0/16")
        rules.append("block out from any to 169.254.0.0/16")
        rules.append("")

        # Resolve domains and allow
        rules.append("# Allowed destinations")
        resolved_ips = self._resolve_domains(allowed_domains)
        for ip in resolved_ips:
            rules.append(f"pass out proto tcp from any to {ip} port {{ 80 443 }}")
        rules.append("")

        # Keep state for allowed connections
        rules.append("# Keep state for allowed")
        rules.append("pass out proto tcp from any to any port 443 keep state")

        return rules

    def generate_cleanup_commands(
        self,
        platform: str = "linux",
        chain_name: str = "JARVIS_EGRESS",
    ) -> List[str]:
        """
        Generate commands to clean up firewall rules.

        Args:
            platform: "linux" or "macos"
            chain_name: Chain/anchor name to clean up

        Returns:
            List of cleanup commands
        """
        if platform == "linux":
            return [
                f"iptables -D OUTPUT -j {chain_name} 2>/dev/null || true",
                f"iptables -F {chain_name} 2>/dev/null || true",
                f"iptables -X {chain_name} 2>/dev/null || true",
            ]
        elif platform == "macos":
            return [
                f"pfctl -a {chain_name} -F all 2>/dev/null || true",
            ]
        else:
            return []

    def _resolve_domains(self, domains: List[str]) -> List[str]:
        """
        Resolve domain names to IP addresses.

        Args:
            domains: List of domain names

        Returns:
            List of resolved IP addresses
        """
        resolved: Set[str] = set()

        for domain in domains:
            domain = domain.lower().strip()
            if not domain:
                continue

            try:
                # Get all IP addresses for the domain
                results = socket.getaddrinfo(domain, None, socket.AF_UNSPEC)
                for family, _, _, _, sockaddr in results:
                    ip = str(sockaddr[0])
                    resolved.add(ip)
                    logger.debug(f"Resolved {domain} -> {ip}")

            except socket.gaierror as e:
                logger.warning(f"Failed to resolve domain '{domain}': {e}")
                continue

        return sorted(resolved)


# ============================================================================
# Convenience Functions
# ============================================================================


def create_validator(allowed_domains: List[str]) -> DomainValidator:
    """
    Create a domain validator with the given allowlist.

    Args:
        allowed_domains: List of allowed domain names

    Returns:
        Configured DomainValidator instance
    """
    return DomainValidator(allowed_domains)


def is_domain_allowed(domain: str, allowed_domains: List[str]) -> bool:
    """
    Quick check if a domain is in the allowlist.

    Args:
        domain: Domain to check
        allowed_domains: List of allowed domains

    Returns:
        True if allowed, False if blocked
    """
    validator = DomainValidator(allowed_domains)
    return validator.is_allowed_domain(domain)


def get_sandbox_network_env(allowed_domains: List[str]) -> Dict[str, str]:
    """
    Get environment variables for sandbox network configuration.

    Args:
        allowed_domains: List of allowed domains

    Returns:
        Dictionary of environment variables
    """
    config = NetworkConfig()
    return config.get_proxy_env_vars(allowed_domains)
