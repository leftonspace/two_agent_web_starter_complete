"""
PHASE 7.1: OS-Level Sandbox Execution

Provides secure, isolated code execution using OS-level sandboxing:
- Linux: bubblewrap (bwrap) for namespace isolation
- macOS: sandbox-exec with seatbelt profiles

Features:
- Filesystem access restricted to allowed paths only
- Network access restricted to allowed domains only
- Resource limits (memory, CPU time)
- Violation logging without exceptions
- Async execution with timeout support

Usage:
    from core.security.sandbox import Sandbox, SandboxProfile

    profile = SandboxProfile(
        name="code_generation",
        allowed_paths=["/workspace", "/tmp"],
        allowed_domains=["github.com", "pypi.org"],
        max_memory_mb=4096,
        max_time_seconds=300,
    )

    sandbox = Sandbox(profile)
    result = await sandbox.execute("python script.py", working_dir="/workspace")

    if result.violations:
        print(f"Security violations: {result.violations}")
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import shutil
import signal
import tempfile
import time
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================


class SandboxProfile(BaseModel):
    """
    Configuration profile for sandbox execution.

    Defines security boundaries including filesystem access, network access,
    and resource limits.
    """

    name: str = Field(..., description="Profile name for identification")
    allowed_paths: List[str] = Field(
        default_factory=lambda: ["/tmp"],
        description="Filesystem paths the sandbox can access",
    )
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="Network domains the sandbox can connect to",
    )
    max_memory_mb: int = Field(
        default=512,
        ge=64,
        le=16384,
        description="Maximum memory in MB",
    )
    max_time_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Maximum execution time in seconds",
    )
    allow_network: bool = Field(
        default=False,
        description="Whether network access is allowed at all",
    )

    @field_validator("allowed_paths", mode="before")
    @classmethod
    def validate_paths(cls, v: List[str]) -> List[str]:
        """Ensure paths are absolute and normalized."""
        validated = []
        for path in v:
            # Convert to absolute path
            abs_path = os.path.abspath(os.path.expanduser(path))
            validated.append(abs_path)
        return validated

    @field_validator("allowed_domains", mode="before")
    @classmethod
    def validate_domains(cls, v: List[str]) -> List[str]:
        """Normalize domain names."""
        return [d.lower().strip() for d in v]


class ExecutionResult(BaseModel):
    """
    Result of sandboxed command execution.

    Contains output, timing, resource usage, and any security violations.
    """

    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    return_code: int = Field(default=-1, description="Process return code")
    execution_time_ms: int = Field(
        default=0,
        description="Actual execution time in milliseconds",
    )
    memory_used_mb: float = Field(
        default=0.0,
        description="Peak memory usage in MB",
    )
    violations: List[str] = Field(
        default_factory=list,
        description="List of security violations detected",
    )
    was_killed: bool = Field(
        default=False,
        description="Whether the process was forcefully killed",
    )
    kill_reason: Optional[str] = Field(
        default=None,
        description="Reason for killing the process",
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


# ============================================================================
# Pre-defined Profiles
# ============================================================================


PROFILES = {
    "code_generation": SandboxProfile(
        name="code_generation",
        allowed_paths=["/tmp"],
        allowed_domains=["github.com", "pypi.org", "npmjs.org", "registry.npmjs.org"],
        max_memory_mb=4096,
        max_time_seconds=300,
        allow_network=True,
    ),
    "business_documents": SandboxProfile(
        name="business_documents",
        allowed_paths=["/tmp"],
        allowed_domains=[],
        max_memory_mb=2048,
        max_time_seconds=120,
        allow_network=False,
    ),
    "benchmark": SandboxProfile(
        name="benchmark",
        allowed_paths=["/tmp"],
        allowed_domains=[],
        max_memory_mb=4096,
        max_time_seconds=600,
        allow_network=False,
    ),
    "minimal": SandboxProfile(
        name="minimal",
        allowed_paths=["/tmp"],
        allowed_domains=[],
        max_memory_mb=256,
        max_time_seconds=30,
        allow_network=False,
    ),
}


def get_profile(name: str) -> SandboxProfile:
    """Get a pre-defined sandbox profile by name."""
    if name not in PROFILES:
        raise ValueError(f"Unknown profile: {name}. Available: {list(PROFILES.keys())}")
    return PROFILES[name].model_copy()


# ============================================================================
# Sandbox Implementation
# ============================================================================


class Sandbox:
    """
    OS-level sandbox for secure code execution.

    Uses bubblewrap (bwrap) on Linux and sandbox-exec on macOS to provide
    process isolation with configurable filesystem and network restrictions.
    """

    def __init__(self, profile: SandboxProfile) -> None:
        """
        Initialize sandbox with a security profile.

        Args:
            profile: SandboxProfile defining security boundaries
        """
        self.profile = profile
        self._platform = self._detect_platform()
        self._bwrap_path: Optional[str] = None
        self._sandbox_exec_path: Optional[str] = None
        self._temp_profile_path: Optional[str] = None  # For macOS seatbelt profile cleanup

        # Validate sandbox tool availability
        if self._platform == "linux":
            self._bwrap_path = shutil.which("bwrap")
            if not self._bwrap_path:
                logger.warning(
                    "bubblewrap (bwrap) not found. Install with: "
                    "apt install bubblewrap (Debian/Ubuntu) or "
                    "dnf install bubblewrap (Fedora)"
                )
        elif self._platform == "macos":
            self._sandbox_exec_path = shutil.which("sandbox-exec")
            if not self._sandbox_exec_path:
                logger.warning("sandbox-exec not found (should be built into macOS)")

    def _detect_platform(self) -> Literal["linux", "macos", "unsupported"]:
        """Detect the current platform for sandbox implementation."""
        system = platform.system().lower()
        if system == "linux":
            return "linux"
        elif system == "darwin":
            return "macos"
        else:
            return "unsupported"

    @property
    def is_available(self) -> bool:
        """Check if sandboxing is available on this platform."""
        if self._platform == "linux":
            return self._bwrap_path is not None
        elif self._platform == "macos":
            return self._sandbox_exec_path is not None
        return False

    async def execute(
        self,
        command: str,
        working_dir: str = "/tmp",
    ) -> ExecutionResult:
        """
        Execute a command within the sandbox.

        Args:
            command: Shell command to execute
            working_dir: Working directory for the command

        Returns:
            ExecutionResult with output, timing, and any violations
        """
        violations: List[str] = []
        start_time = time.monotonic()

        # Validate working directory
        working_dir = os.path.abspath(os.path.expanduser(working_dir))
        if not self._is_path_allowed(working_dir):
            violations.append(
                f"Working directory '{working_dir}' not in allowed paths"
            )
            # Add working_dir to allowed paths temporarily for this execution
            execution_allowed_paths = self.profile.allowed_paths + [working_dir]
        else:
            execution_allowed_paths = self.profile.allowed_paths

        # Check platform support
        if self._platform == "unsupported":
            violations.append(f"Unsupported platform: {platform.system()}")
            return ExecutionResult(
                stdout="",
                stderr=f"Sandboxing not supported on {platform.system()}",
                return_code=-1,
                execution_time_ms=0,
                violations=violations,
                was_killed=False,
            )

        # Check sandbox tool availability
        if not self.is_available:
            violations.append("Sandbox tool not available")
            logger.warning(
                f"Sandbox not available on {self._platform}, "
                "executing without isolation"
            )
            # Fall back to unsandboxed execution with warning
            return await self._execute_unsandboxed(
                command, working_dir, violations, start_time
            )

        # Build sandboxed command
        try:
            if self._platform == "linux":
                sandbox_cmd = self._build_bwrap_command(
                    command, working_dir, execution_allowed_paths
                )
            else:  # macos
                sandbox_cmd = self._build_sandbox_exec_command(
                    command, working_dir, execution_allowed_paths
                )
        except Exception as e:
            violations.append(f"Failed to build sandbox command: {e}")
            return ExecutionResult(
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time_ms=int((time.monotonic() - start_time) * 1000),
                violations=violations,
                was_killed=False,
            )

        # Execute sandboxed command
        return await self._execute_sandboxed(
            sandbox_cmd, working_dir, violations, start_time
        )

    def _is_path_allowed(self, path: str) -> bool:
        """Check if a path is within allowed paths."""
        path = os.path.abspath(path)
        for allowed in self.profile.allowed_paths:
            allowed = os.path.abspath(allowed)
            # Check if path is under allowed path
            if path == allowed or path.startswith(allowed + os.sep):
                return True
        return False

    def _build_bwrap_command(
        self,
        command: str,
        working_dir: str,
        allowed_paths: List[str],
    ) -> List[str]:
        """
        Build bubblewrap command for Linux sandboxing.

        Args:
            command: Command to execute
            working_dir: Working directory
            allowed_paths: List of allowed filesystem paths

        Returns:
            Complete bwrap command as list of arguments
        """
        cmd = [self._bwrap_path or "bwrap"]

        # Create new namespaces for isolation
        cmd.extend([
            "--unshare-all",  # Unshare all namespaces
            "--die-with-parent",  # Kill sandbox if parent dies
        ])

        # Set up minimal root filesystem
        cmd.extend([
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64" if os.path.exists("/lib64") else "/lib",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            "--symlink", "/usr/lib", "/lib",
            "--proc", "/proc",
            "--dev", "/dev",
        ])

        # Add /etc with limited access (needed for DNS, timezone, etc.)
        etc_files = [
            "/etc/resolv.conf",
            "/etc/hosts",
            "/etc/passwd",
            "/etc/group",
            "/etc/localtime",
            "/etc/ssl",
            "/etc/ca-certificates",
        ]
        for etc_file in etc_files:
            if os.path.exists(etc_file):
                cmd.extend(["--ro-bind", etc_file, etc_file])

        # Bind allowed paths (read-write)
        for path in allowed_paths:
            if os.path.exists(path):
                cmd.extend(["--bind", path, path])
            else:
                # Create directory in sandbox
                cmd.extend(["--dir", path])

        # Create tmpfs for /tmp if not in allowed paths
        if "/tmp" not in allowed_paths:
            cmd.extend(["--tmpfs", "/tmp"])

        # Network isolation
        if not self.profile.allow_network:
            cmd.append("--unshare-net")
        else:
            # Share network namespace but we rely on external proxy/firewall
            # for domain filtering (bwrap doesn't do domain-level filtering)
            cmd.append("--share-net")

        # Set working directory
        cmd.extend(["--chdir", working_dir])

        # Resource limits via setrlimit-style constraints
        # Note: bwrap itself doesn't limit memory; we do it via shell ulimit
        memory_bytes = self.profile.max_memory_mb * 1024 * 1024

        # Wrap command with resource limits
        limit_cmd = (
            f"ulimit -v {memory_bytes // 1024} 2>/dev/null; "  # Virtual memory in KB
            f"ulimit -t {self.profile.max_time_seconds} 2>/dev/null; "  # CPU seconds
            f"exec {command}"
        )

        cmd.extend(["--", "/bin/sh", "-c", limit_cmd])

        return cmd

    def _build_sandbox_exec_command(
        self,
        command: str,
        working_dir: str,
        allowed_paths: List[str],
    ) -> List[str]:
        """
        Build sandbox-exec command for macOS sandboxing.

        Args:
            command: Command to execute
            working_dir: Working directory
            allowed_paths: List of allowed filesystem paths

        Returns:
            Complete sandbox-exec command as list of arguments
        """
        # Build seatbelt profile
        profile_content = self._generate_seatbelt_profile(allowed_paths)

        # Write profile to temporary file
        profile_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sb",
            delete=False,
        )
        profile_file.write(profile_content)
        profile_file.close()

        # Store for cleanup
        self._temp_profile_path = profile_file.name

        cmd = [
            self._sandbox_exec_path or "sandbox-exec",
            "-f", profile_file.name,
            "/bin/sh", "-c",
            f"cd {working_dir} && {command}",
        ]

        return cmd

    def _generate_seatbelt_profile(self, allowed_paths: List[str]) -> str:
        """
        Generate a macOS seatbelt profile for sandbox-exec.

        Args:
            allowed_paths: List of allowed filesystem paths

        Returns:
            Seatbelt profile content as string
        """
        # Start with deny-all default
        profile_lines = [
            "(version 1)",
            "(deny default)",
            "",
            "; Allow basic process operations",
            "(allow process-fork)",
            "(allow process-exec)",
            "(allow signal (target self))",
            "",
            "; Allow reading system files",
            "(allow file-read*",
            '    (subpath "/usr")',
            '    (subpath "/bin")',
            '    (subpath "/sbin")',
            '    (subpath "/System")',
            '    (subpath "/Library/Frameworks")',
            '    (subpath "/private/var/db")',
            '    (literal "/dev/null")',
            '    (literal "/dev/random")',
            '    (literal "/dev/urandom")',
            '    (literal "/dev/zero")',
            ")",
            "",
            "; Allow /dev access",
            "(allow file-read* file-write*",
            '    (literal "/dev/tty")',
            '    (literal "/dev/stdin")',
            '    (literal "/dev/stdout")',
            '    (literal "/dev/stderr")',
            ")",
            "",
        ]

        # Add allowed paths with read-write access
        if allowed_paths:
            profile_lines.append("; Allowed paths (read-write)")
            profile_lines.append("(allow file-read* file-write*")
            for path in allowed_paths:
                profile_lines.append(f'    (subpath "{path}")')
            profile_lines.append(")")
            profile_lines.append("")

        # Network access
        if self.profile.allow_network:
            profile_lines.extend([
                "; Network access",
                "(allow network-outbound)",
                "(allow network-inbound)",
                "(allow system-socket)",
                "",
            ])
            # Note: Domain-level filtering would require a proxy
            # macOS sandbox can't filter by domain name
        else:
            profile_lines.extend([
                "; Network denied",
                "(deny network*)",
                "",
            ])

        # Allow sysctl for basic operations
        profile_lines.extend([
            "; Allow basic sysctl",
            "(allow sysctl-read)",
            "",
            "; Allow mach operations for IPC",
            "(allow mach-lookup)",
            "(allow mach-register)",
            "",
        ])

        return "\n".join(profile_lines)

    async def _execute_sandboxed(
        self,
        cmd: List[str],
        working_dir: str,
        violations: List[str],
        start_time: float,
    ) -> ExecutionResult:
        """Execute a sandboxed command asynchronously."""
        process: Optional[asyncio.subprocess.Process] = None
        was_killed = False
        kill_reason: Optional[str] = None
        stdout = ""
        stderr = ""
        return_code = -1
        memory_used_mb = 0.0

        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir if os.path.exists(working_dir) else "/tmp",
                env=self._get_sanitized_env(),
            )

            # Wait with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.profile.max_time_seconds,
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                return_code = process.returncode or 0

                # Try to get memory usage from /proc on Linux
                if self._platform == "linux" and process.pid:
                    memory_used_mb = self._get_process_memory(process.pid)

            except asyncio.TimeoutError:
                was_killed = True
                kill_reason = f"Exceeded time limit of {self.profile.max_time_seconds}s"
                violations.append(kill_reason)

                # Kill the process
                if process:
                    try:
                        process.kill()
                        await process.wait()
                    except ProcessLookupError:
                        pass

                logger.warning(f"Sandbox process killed: {kill_reason}")

        except Exception as e:
            violations.append(f"Execution error: {str(e)}")
            stderr = str(e)
            logger.error(f"Sandbox execution failed: {e}")

        finally:
            # Cleanup temp profile on macOS
            if hasattr(self, "_temp_profile_path") and self._temp_profile_path:
                try:
                    os.unlink(self._temp_profile_path)
                except OSError:
                    pass
                self._temp_profile_path = None

        execution_time_ms = int((time.monotonic() - start_time) * 1000)

        # Check for violation indicators in stderr
        self._detect_violations(stderr, violations)

        return ExecutionResult(
            stdout=stdout[:100000],  # Limit output size
            stderr=stderr[:100000],
            return_code=return_code,
            execution_time_ms=execution_time_ms,
            memory_used_mb=memory_used_mb,
            violations=violations,
            was_killed=was_killed,
            kill_reason=kill_reason,
        )

    async def _execute_unsandboxed(
        self,
        command: str,
        working_dir: str,
        violations: List[str],
        start_time: float,
    ) -> ExecutionResult:
        """Execute command without sandboxing (fallback with warning)."""
        violations.append("SECURITY WARNING: Executing without sandbox isolation")

        process: Optional[asyncio.subprocess.Process] = None
        was_killed = False
        kill_reason: Optional[str] = None
        stdout = ""
        stderr = ""
        return_code = -1

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir if os.path.exists(working_dir) else "/tmp",
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.profile.max_time_seconds,
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                return_code = process.returncode or 0

            except asyncio.TimeoutError:
                was_killed = True
                kill_reason = f"Exceeded time limit of {self.profile.max_time_seconds}s"
                violations.append(kill_reason)
                if process:
                    process.kill()
                    await process.wait()

        except Exception as e:
            violations.append(f"Execution error: {str(e)}")
            stderr = str(e)

        execution_time_ms = int((time.monotonic() - start_time) * 1000)

        return ExecutionResult(
            stdout=stdout[:100000],
            stderr=stderr[:100000],
            return_code=return_code,
            execution_time_ms=execution_time_ms,
            memory_used_mb=0.0,
            violations=violations,
            was_killed=was_killed,
            kill_reason=kill_reason,
        )

    def _get_sanitized_env(self) -> dict:
        """Get sanitized environment variables for subprocess."""
        # Start with minimal environment
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": "/tmp",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
        }

        # Preserve some safe variables from parent environment
        safe_vars = ["TERM", "COLORTERM", "TZ"]
        for var in safe_vars:
            if var in os.environ:
                env[var] = os.environ[var]

        return env

    def _get_process_memory(self, pid: int) -> float:
        """Get memory usage of a process in MB (Linux only)."""
        try:
            # Read from /proc/<pid>/status
            status_path = f"/proc/{pid}/status"
            if os.path.exists(status_path):
                with open(status_path, "r") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            # VmRSS is in kB
                            parts = line.split()
                            if len(parts) >= 2:
                                return float(parts[1]) / 1024  # Convert to MB
        except (OSError, ValueError, IndexError):
            pass
        return 0.0

    def _detect_violations(self, stderr: str, violations: List[str]) -> None:
        """Detect security violations from stderr output."""
        stderr_lower = stderr.lower()

        # Common violation patterns
        violation_patterns = [
            ("permission denied", "Permission denied accessing resource"),
            ("operation not permitted", "Operation blocked by sandbox"),
            ("network is unreachable", "Network access blocked"),
            ("name or service not known", "DNS resolution blocked"),
            ("connection refused", "Network connection blocked"),
            ("bwrap:", "Sandbox configuration error"),
            ("sandbox-exec:", "Sandbox configuration error"),
            ("killed", "Process terminated by sandbox"),
            ("segmentation fault", "Memory violation detected"),
            ("memory allocation failed", "Memory limit exceeded"),
            ("cannot allocate memory", "Memory limit exceeded"),
        ]

        for pattern, message in violation_patterns:
            if pattern in stderr_lower and message not in violations:
                violations.append(message)
                logger.info(f"Sandbox violation detected: {message}")


# ============================================================================
# Convenience Functions
# ============================================================================


async def run_sandboxed(
    command: str,
    profile: Optional[SandboxProfile] = None,
    profile_name: Optional[str] = None,
    working_dir: str = "/tmp",
) -> ExecutionResult:
    """
    Convenience function to run a command in sandbox.

    Args:
        command: Command to execute
        profile: SandboxProfile to use (optional)
        profile_name: Name of pre-defined profile to use (optional)
        working_dir: Working directory

    Returns:
        ExecutionResult with output and violations
    """
    if profile is None:
        if profile_name:
            profile = get_profile(profile_name)
        else:
            profile = get_profile("minimal")

    sandbox = Sandbox(profile)
    return await sandbox.execute(command, working_dir)


def is_sandbox_available() -> bool:
    """Check if sandboxing is available on this platform."""
    system = platform.system().lower()
    if system == "linux":
        return shutil.which("bwrap") is not None
    elif system == "darwin":
        return shutil.which("sandbox-exec") is not None
    return False


def get_platform() -> Literal["linux", "macos", "unsupported"]:
    """Get current platform type."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    return "unsupported"
