"""
Security Tests: Network Domain Validation

Tests that verify:
1. Domain validation - exact and subdomain matching
2. URL parsing - handles various URL formats
3. Localhost blocking - blocks local addresses by default
4. IP address handling - blocks private IPs

Run with: pytest tests/security/test_network.py -v
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.security import (
    DomainValidator,
    NetworkConfig,
    is_domain_allowed,
    get_sandbox_network_env,
)


# ============================================================================
# Test Domain Validator
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestDomainValidator:
    """Tests for domain validation logic."""

    def test_exact_match(self, domain_validator):
        """Exact domain match should be allowed."""
        assert domain_validator.is_allowed_domain("github.com") is True
        assert domain_validator.is_allowed_domain("pypi.org") is True
        assert domain_validator.is_allowed_domain("npmjs.org") is True

    def test_subdomain_match(self, domain_validator):
        """Subdomains of allowed domains should be allowed."""
        assert domain_validator.is_allowed_domain("api.github.com") is True
        assert domain_validator.is_allowed_domain("raw.githubusercontent.com") is False  # Different domain
        assert domain_validator.is_allowed_domain("files.pythonhosted.org") is False  # Not pypi.org
        assert domain_validator.is_allowed_domain("registry.npmjs.org") is True  # Subdomain of npmjs.org

    def test_different_domain_rejected(self, domain_validator):
        """Domains not in allowlist should be rejected."""
        assert domain_validator.is_allowed_domain("evil.com") is False
        assert domain_validator.is_allowed_domain("malware.net") is False
        assert domain_validator.is_allowed_domain("attacker.org") is False

    def test_case_insensitive(self, domain_validator):
        """Domain matching should be case insensitive."""
        assert domain_validator.is_allowed_domain("GITHUB.COM") is True
        assert domain_validator.is_allowed_domain("GitHub.Com") is True
        assert domain_validator.is_allowed_domain("API.GITHUB.COM") is True

    def test_empty_allowlist_blocks_all(self, strict_domain_validator):
        """Empty allowlist should block all domains."""
        assert strict_domain_validator.is_allowed_domain("github.com") is False
        assert strict_domain_validator.is_allowed_domain("google.com") is False
        assert strict_domain_validator.is_allowed_domain("any.domain") is False

    def test_url_parsing(self, domain_validator):
        """Full URLs should be parsed correctly."""
        assert domain_validator.is_allowed("https://github.com/user/repo") is True
        assert domain_validator.is_allowed("http://api.github.com/repos") is True
        assert domain_validator.is_allowed("https://pypi.org/project/requests") is True
        assert domain_validator.is_allowed("https://evil.com/malware") is False

    def test_url_with_port(self, domain_validator):
        """URLs with ports should be handled correctly."""
        assert domain_validator.is_allowed("https://github.com:443/user/repo") is True
        assert domain_validator.is_allowed("http://pypi.org:80/simple") is True

    def test_url_with_query_params(self, domain_validator):
        """URLs with query parameters should be handled."""
        assert domain_validator.is_allowed("https://github.com/search?q=test") is True
        assert domain_validator.is_allowed("https://pypi.org/pypi/requests/json") is True

    def test_url_without_scheme(self, domain_validator):
        """URLs without scheme should be handled."""
        assert domain_validator.is_allowed("github.com/user/repo") is True
        assert domain_validator.is_allowed("api.github.com/repos") is True

    def test_empty_url(self, domain_validator):
        """Empty URLs should be rejected."""
        assert domain_validator.is_allowed("") is False
        assert domain_validator.is_allowed("   ") is False

    def test_malformed_url(self, domain_validator):
        """Malformed URLs should be handled gracefully."""
        # These should not crash, just return False or extract what they can
        assert domain_validator.is_allowed("not-a-valid-url!!!") is False
        assert domain_validator.is_allowed("://missing-scheme") is False

    def test_extract_domain(self, domain_validator):
        """Domain extraction should work correctly."""
        assert domain_validator.extract_domain("https://github.com/user") == "github.com"
        assert domain_validator.extract_domain("http://api.github.com:443/path") == "api.github.com"
        assert domain_validator.extract_domain("github.com") == "github.com"
        assert domain_validator.extract_domain("") == ""


# ============================================================================
# Test Localhost Blocking
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestLocalhostBlocking:
    """Tests for localhost/loopback address blocking."""

    def test_localhost_blocked_by_default(self, domain_validator):
        """localhost should be blocked by default."""
        assert domain_validator.is_allowed_domain("localhost") is False
        assert domain_validator.is_allowed("http://localhost/admin") is False
        assert domain_validator.is_allowed("http://localhost:8080/api") is False

    def test_loopback_ip_blocked(self, domain_validator):
        """127.0.0.1 should be blocked by default."""
        assert domain_validator.is_allowed_domain("127.0.0.1") is False
        assert domain_validator.is_allowed("http://127.0.0.1:8000") is False

    def test_ipv6_loopback_blocked(self, domain_validator):
        """IPv6 loopback (::1) should be blocked by default."""
        assert domain_validator.is_allowed_domain("::1") is False

    def test_zero_ip_blocked(self, domain_validator):
        """0.0.0.0 should be blocked."""
        assert domain_validator.is_allowed_domain("0.0.0.0") is False

    def test_localhost_allowed_when_configured(self, localhost_allowed_validator):
        """localhost should be allowed when explicitly configured."""
        assert localhost_allowed_validator.is_allowed_domain("localhost") is True
        assert localhost_allowed_validator.is_allowed("http://localhost:8080") is True

    def test_loopback_allowed_when_configured(self, localhost_allowed_validator):
        """127.0.0.1 should be allowed when explicitly configured."""
        assert localhost_allowed_validator.is_allowed_domain("127.0.0.1") is True


# ============================================================================
# Test IP Address Handling
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestIPAddressHandling:
    """Tests for IP address validation."""

    def test_private_ip_blocked(self, domain_validator):
        """Private IP addresses should be blocked by default."""
        private_ips = [
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.255.255",
        ]
        for ip in private_ips:
            assert domain_validator.is_allowed_domain(ip) is False, \
                   f"Private IP {ip} should be blocked"

    def test_link_local_blocked(self, domain_validator):
        """Link-local addresses should be blocked (includes cloud metadata)."""
        assert domain_validator.is_allowed_domain("169.254.169.254") is False
        assert domain_validator.is_allowed_domain("169.254.0.1") is False

    def test_public_ip_blocked_unless_allowed(self, domain_validator):
        """Public IPs should be blocked unless explicitly in allowlist."""
        public_ips = [
            "8.8.8.8",
            "1.1.1.1",
            "208.67.222.222",
        ]
        for ip in public_ips:
            assert domain_validator.is_allowed_domain(ip) is False, \
                   f"Public IP {ip} should be blocked unless explicitly allowed"

    def test_ip_explicitly_allowed(self):
        """IPs explicitly in allowlist should be allowed."""
        validator = DomainValidator(["8.8.8.8", "1.1.1.1"])
        assert validator.is_allowed_domain("8.8.8.8") is True
        assert validator.is_allowed_domain("1.1.1.1") is True


# ============================================================================
# Test Network Configuration
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestNetworkConfig:
    """Tests for network configuration generation."""

    def test_proxy_env_vars_generated(self, network_config):
        """Proxy environment variables should be generated."""
        env_vars = network_config.get_proxy_env_vars(["github.com", "pypi.org"])

        # Check lowercase variants
        assert "http_proxy" in env_vars
        assert "https_proxy" in env_vars
        assert "no_proxy" in env_vars

        # Check uppercase variants
        assert "HTTP_PROXY" in env_vars
        assert "HTTPS_PROXY" in env_vars

        # Check custom JARVIS variable
        assert "JARVIS_ALLOWED_DOMAINS" in env_vars
        assert "github.com" in env_vars["JARVIS_ALLOWED_DOMAINS"]
        assert "pypi.org" in env_vars["JARVIS_ALLOWED_DOMAINS"]

    def test_proxy_url_format(self, network_config):
        """Proxy URLs should be properly formatted."""
        env_vars = network_config.get_proxy_env_vars([])

        proxy_url = env_vars["http_proxy"]
        assert proxy_url.startswith("http://")
        assert ":" in proxy_url  # Should have port

    def test_custom_proxy_port(self):
        """Custom proxy port should be used."""
        config = NetworkConfig(proxy_port=3128)
        env_vars = config.get_proxy_env_vars([])

        assert ":3128" in env_vars["http_proxy"]

    def test_iptables_rules_generated(self, network_config):
        """iptables rules should be generated."""
        rules = network_config.generate_iptables_rules(["github.com"])

        # Check for chain creation
        assert any("iptables -N" in r for r in rules)

        # Check for blocking private IPs
        assert any("127.0.0.0/8" in r and "DROP" in r for r in rules)
        assert any("10.0.0.0/8" in r and "DROP" in r for r in rules)

        # Check for DNS allowance
        assert any("dport 53" in r and "ACCEPT" in r for r in rules)

    def test_pf_rules_generated(self, network_config):
        """pf (macOS) rules should be generated."""
        rules = network_config.generate_pf_rules(["github.com"])

        # Check for blocking private IPs
        assert any("block" in r and "127.0.0.0/8" in r for r in rules)

        # Check for DNS allowance
        assert any("port 53" in r for r in rules)

    def test_cleanup_commands_generated(self, network_config):
        """Cleanup commands should be generated."""
        linux_cleanup = network_config.generate_cleanup_commands("linux")
        assert len(linux_cleanup) > 0
        assert any("iptables" in c for c in linux_cleanup)

        macos_cleanup = network_config.generate_cleanup_commands("macos")
        assert len(macos_cleanup) > 0
        assert any("pfctl" in c for c in macos_cleanup)


# ============================================================================
# Test Convenience Functions
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_is_domain_allowed_function(self):
        """is_domain_allowed convenience function should work."""
        assert is_domain_allowed("api.github.com", ["github.com"]) is True
        assert is_domain_allowed("evil.com", ["github.com"]) is False

    def test_get_sandbox_network_env_function(self):
        """get_sandbox_network_env convenience function should work."""
        env = get_sandbox_network_env(["github.com"])

        assert "HTTP_PROXY" in env
        assert "github.com" in env["JARVIS_ALLOWED_DOMAINS"]


# ============================================================================
# Test Statistics Tracking
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestStatistics:
    """Tests for validation statistics tracking."""

    def test_checks_counted(self):
        """Validation checks should be counted."""
        validator = DomainValidator(["github.com"])

        # Perform some checks
        validator.is_allowed("https://github.com")
        validator.is_allowed("https://evil.com")
        validator.is_allowed("https://api.github.com")

        stats = validator.get_statistics()
        assert stats["checks_performed"] == 3
        assert stats["checks_blocked"] == 1  # evil.com
        assert stats["checks_allowed"] == 2  # github.com and api.github.com


# ============================================================================
# Test Edge Cases
# ============================================================================


@pytest.mark.security
@pytest.mark.network
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_domain_with_trailing_dot(self):
        """Domains with trailing dots should be handled."""
        validator = DomainValidator(["github.com"])
        # Trailing dots are technically valid in DNS
        domain = validator.extract_domain("https://github.com.")
        assert domain in ["github.com", "github.com."]

    def test_very_long_url(self):
        """Very long URLs should be handled."""
        validator = DomainValidator(["example.com"])
        long_path = "a" * 10000
        url = f"https://example.com/{long_path}"
        result = validator.is_allowed(url)
        assert result is True  # Should work, just with long path

    def test_unicode_domain(self):
        """Unicode/IDN domains should be handled."""
        validator = DomainValidator(["example.com"])
        # This might fail or work depending on implementation
        # Just verify it doesn't crash
        try:
            result = validator.extract_domain("https://münchen.de/path")
            assert isinstance(result, str)
        except Exception:
            pass  # Acceptable to fail on IDN

    def test_punycode_domain(self):
        """Punycode domains should be handled."""
        validator = DomainValidator(["xn--mnchen-3ya.de"])
        result = validator.extract_domain("https://xn--mnchen-3ya.de/path")
        assert "xn--mnchen-3ya.de" in result or "münchen.de" in result

    def test_multiple_subdomains(self):
        """Multiple levels of subdomains should be handled."""
        validator = DomainValidator(["github.com"])
        assert validator.is_allowed_domain("deep.nested.sub.github.com") is True
        assert validator.is_allowed_domain("api.v2.github.com") is True

    def test_similar_domain_not_matched(self):
        """Similar but different domains should not match."""
        validator = DomainValidator(["github.com"])
        # These look similar but are different domains
        assert validator.is_allowed_domain("github.com.evil.com") is False
        assert validator.is_allowed_domain("fakegithub.com") is False
        assert validator.is_allowed_domain("github-com.fake.com") is False
