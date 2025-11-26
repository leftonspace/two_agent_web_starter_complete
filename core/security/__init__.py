"""
PHASE 7: Security Foundation

OS-level sandboxing for secure code execution.

Components:
- sandbox: OS-level isolation using bubblewrap (Linux) or sandbox-exec (macOS)

Usage:
    from core.security import Sandbox, SandboxProfile, ExecutionResult

    # Create profile
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

    # Or use convenience function with pre-defined profiles
    from core.security import run_sandboxed, get_profile

    result = await run_sandboxed("echo hello", profile_name="minimal")
"""

from .sandbox import (
    # Models
    SandboxProfile,
    ExecutionResult,
    # Main class
    Sandbox,
    # Pre-defined profiles
    PROFILES,
    get_profile,
    # Convenience functions
    run_sandboxed,
    is_sandbox_available,
    get_platform,
)

__all__ = [
    # Models
    "SandboxProfile",
    "ExecutionResult",
    # Main class
    "Sandbox",
    # Pre-defined profiles
    "PROFILES",
    "get_profile",
    # Convenience functions
    "run_sandboxed",
    "is_sandbox_available",
    "get_platform",
]
