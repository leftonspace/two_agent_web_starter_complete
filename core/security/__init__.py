"""
PHASE 7: Security Foundation

OS-level sandboxing for secure code execution.

Components:
- sandbox: OS-level isolation using bubblewrap (Linux) or sandbox-exec (macOS)
- profiles: YAML-based profile configuration and loading

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

    # Or use convenience functions
    from core.security import run_sandboxed, get_default_profile

    result = await run_sandboxed("echo hello", profile_name="minimal")
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
]
