"""
PHASE 7: Security Foundation

OS-level sandboxing for secure code execution.

Components:
- sandbox: OS-level isolation using bubblewrap (Linux) or sandbox-exec (macOS)
- profiles: YAML-based profile configuration and loading
- network: Domain validation and network configuration for sandboxes

Usage:
    from core.security import Sandbox, SandboxProfile, ExecutionResult

    # Create profile manually
    profile = SandboxProfile(
        name="my_profile",
        allowed_paths=["/workspace", "/tmp"],
        allowed_domains=["github.com"],
        max_memory_mb=4096,
        max_time_seconds=300,
    )

    # Execute in sandbox
    sandbox = Sandbox(profile)
    result = await sandbox.execute("python script.py", working_dir="/workspace")

    # Or load profile from YAML configuration
    from core.security import ProfileLoader, load_profile

    loader = ProfileLoader()
    profile = loader.load_profile("code_generation")

    # Validate network domains
    from core.security import DomainValidator, NetworkConfig

    validator = DomainValidator(["github.com", "pypi.org"])
    if validator.is_allowed("https://api.github.com/repos"):
        print("URL allowed")
"""

from .sandbox import (
    # Models
    SandboxProfile,
    ExecutionResult,
    # Main class
    Sandbox,
    # Pre-defined profiles (built-in)
    PROFILES,
    get_profile,
    # Convenience functions
    run_sandboxed,
    is_sandbox_available,
    get_platform,
)

from .profiles import (
    # Profile loader
    ProfileLoader,
    ProfileValidationError,
    ProfileNotFoundError,
    # Convenience functions
    get_loader,
    load_profile,
    load_all_profiles,
    get_default_profile,
    list_profile_names,
)

from .network import (
    # Network validation
    DomainValidator,
    NetworkConfig,
    # Convenience functions
    create_validator,
    is_domain_allowed,
    get_sandbox_network_env,
)

__all__ = [
    # Models
    "SandboxProfile",
    "ExecutionResult",
    # Main class
    "Sandbox",
    # Pre-defined profiles (built-in)
    "PROFILES",
    "get_profile",
    # Sandbox convenience functions
    "run_sandboxed",
    "is_sandbox_available",
    "get_platform",
    # Profile loader
    "ProfileLoader",
    "ProfileValidationError",
    "ProfileNotFoundError",
    # Profile convenience functions
    "get_loader",
    "load_profile",
    "load_all_profiles",
    "get_default_profile",
    "list_profile_names",
    # Network validation
    "DomainValidator",
    "NetworkConfig",
    "create_validator",
    "is_domain_allowed",
    "get_sandbox_network_env",
]
