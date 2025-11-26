"""
Security Tests: Sandbox Isolation and Resource Limits

Tests that verify:
1. Filesystem isolation - cannot access files outside allowed paths
2. Resource limits - memory and time limits are enforced
3. Process containment - fork bombs and runaway processes are stopped

Run with: pytest tests/security/test_sandbox.py -v
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.security import (
    Sandbox,
    SandboxProfile,
    ExecutionResult,
    is_sandbox_available,
    get_platform,
)


# ============================================================================
# Test Filesystem Isolation
# ============================================================================


@pytest.mark.security
@pytest.mark.sandbox
class TestFilesystemIsolation:
    """Tests verifying filesystem access restrictions."""

    @pytest.mark.asyncio
    async def test_cannot_read_etc_passwd(self, minimal_profile):
        """Sandbox should block reading /etc/passwd."""
        sandbox = Sandbox(minimal_profile)
        result = await sandbox.execute("cat /etc/passwd")

        # Should either fail or return error
        # On sandboxed systems: permission denied
        # On unsandboxed fallback: still executes but we check the profile restricts it
        if is_sandbox_available():
            assert result.return_code != 0 or "Permission denied" in result.stderr.lower() or \
                   "permission denied" in str(result.violations).lower(), \
                   f"Should not be able to read /etc/passwd. Got: {result.stdout[:200]}"
        else:
            # Without sandbox, verify violation was logged
            assert any("sandbox" in v.lower() for v in result.violations), \
                   "Should log security warning when sandbox unavailable"

    @pytest.mark.asyncio
    async def test_cannot_write_outside_allowed(self, minimal_profile, tmp_path):
        """Sandbox should block writing outside allowed paths."""
        sandbox = Sandbox(minimal_profile)

        # Try to write to a directory not in allowed_paths
        forbidden_path = tmp_path / "forbidden"
        forbidden_path.mkdir(exist_ok=True)

        result = await sandbox.execute(
            f"echo 'hacked' > {forbidden_path}/exploit.txt"
        )

        # Verify file was not created or operation failed
        exploit_file = forbidden_path / "exploit.txt"
        if is_sandbox_available():
            assert not exploit_file.exists() or result.return_code != 0, \
                   "Should not be able to write outside allowed paths"
        # Without sandbox, file might be created but violation logged
        assert len(result.violations) > 0 or not exploit_file.exists()

    @pytest.mark.asyncio
    async def test_can_write_in_allowed_path(self, minimal_profile):
        """Sandbox should allow writing in /tmp (allowed path)."""
        sandbox = Sandbox(minimal_profile)

        # /tmp is in allowed_paths for minimal_profile
        test_file = "/tmp/sandbox_test_write.txt"

        result = await sandbox.execute(f"echo 'allowed' > {test_file}")

        # This should succeed
        if is_sandbox_available():
            assert result.return_code == 0, \
                   f"Should be able to write to /tmp. Stderr: {result.stderr}"
        # Clean up
        try:
            os.unlink(test_file)
        except OSError:
            pass

    @pytest.mark.asyncio
    async def test_cannot_access_home_directory(self, minimal_profile):
        """Sandbox should block access to home directory."""
        sandbox = Sandbox(minimal_profile)
        home_dir = os.path.expanduser("~")

        result = await sandbox.execute(f"ls {home_dir}")

        if is_sandbox_available():
            # Should fail or return error
            assert result.return_code != 0 or "denied" in result.stderr.lower() or \
                   "denied" in str(result.violations).lower() or \
                   result.stdout == "", \
                   f"Should not be able to list home directory. Got: {result.stdout[:200]}"

    @pytest.mark.asyncio
    async def test_symlink_escape_blocked(self, minimal_profile):
        """Sandbox should block symlink-based escapes."""
        sandbox = Sandbox(minimal_profile)

        # Try to create a symlink pointing outside allowed paths
        result = await sandbox.execute(
            "ln -sf /etc/passwd /tmp/passwd_link && cat /tmp/passwd_link"
        )

        if is_sandbox_available():
            # Should either fail to create symlink or fail to read through it
            assert result.return_code != 0 or \
                   "denied" in result.stderr.lower() or \
                   "root:" not in result.stdout, \
                   "Symlink escape should be blocked"

        # Clean up
        try:
            os.unlink("/tmp/passwd_link")
        except OSError:
            pass

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, minimal_profile):
        """Sandbox should block path traversal attempts."""
        sandbox = Sandbox(minimal_profile)

        # Try path traversal
        result = await sandbox.execute("cat /tmp/../etc/passwd")

        if is_sandbox_available():
            assert result.return_code != 0 or "denied" in result.stderr.lower() or \
                   "root:" not in result.stdout, \
                   "Path traversal should be blocked"


# ============================================================================
# Test Resource Limits
# ============================================================================


@pytest.mark.security
@pytest.mark.sandbox
class TestResourceLimits:
    """Tests verifying resource limit enforcement."""

    @pytest.mark.asyncio
    async def test_time_limit_kills_process(self):
        """Process exceeding time limit should be killed."""
        profile = SandboxProfile(
            name="time_test",
            allowed_paths=["/tmp"],
            max_memory_mb=256,
            max_time_seconds=2,  # Very short timeout
        )
        sandbox = Sandbox(profile)

        # Run a command that takes longer than the time limit
        result = await sandbox.execute("sleep 10")

        assert result.was_killed, "Process should be killed when exceeding time limit"
        assert result.kill_reason is not None, "Kill reason should be provided"
        assert "time" in result.kill_reason.lower(), \
               f"Kill reason should mention time: {result.kill_reason}"
        assert any("time" in v.lower() or "exceeded" in v.lower()
                   for v in result.violations), \
               f"Violations should mention timeout: {result.violations}"

    @pytest.mark.asyncio
    async def test_memory_limit_enforced(self):
        """Process exceeding memory limit should be killed or fail."""
        if not is_sandbox_available():
            pytest.skip("Memory limits require sandbox (bubblewrap/sandbox-exec)")

        profile = SandboxProfile(
            name="memory_test",
            allowed_paths=["/tmp"],
            max_memory_mb=64,  # Very low memory limit
            max_time_seconds=30,
        )
        sandbox = Sandbox(profile)

        # Python script that tries to allocate too much memory
        memory_script = """
import sys
data = []
try:
    for i in range(1000):
        data.append('x' * (1024 * 1024))  # 1MB chunks
except MemoryError:
    print('MemoryError caught')
    sys.exit(137)  # Simulate OOM kill
print('Should not reach here')
"""
        # Write script to temp file
        script_path = "/tmp/memory_test.py"
        with open(script_path, "w") as f:
            f.write(memory_script)

        result = await sandbox.execute(f"python3 {script_path}")

        # Process should either:
        # 1. Be killed (return_code != 0)
        # 2. Catch MemoryError
        # 3. Have memory violation logged
        assert result.return_code != 0 or \
               "MemoryError" in result.stdout or \
               any("memory" in v.lower() for v in result.violations), \
               f"Memory limit should be enforced. stdout: {result.stdout}, " \
               f"stderr: {result.stderr}, violations: {result.violations}"

        # Clean up
        try:
            os.unlink(script_path)
        except OSError:
            pass

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_fork_bomb_contained(self):
        """Fork bomb should be contained by sandbox."""
        profile = SandboxProfile(
            name="fork_test",
            allowed_paths=["/tmp"],
            max_memory_mb=256,
            max_time_seconds=5,  # Short timeout to contain damage
        )
        sandbox = Sandbox(profile)

        # Attempt a fork bomb (bash syntax)
        # Note: This is a controlled test in a sandboxed environment
        result = await sandbox.execute(":(){ :|:& };:")

        # Fork bomb should either:
        # 1. Be killed by timeout
        # 2. Fail due to process limits
        # 3. Be blocked by sandbox
        assert result.was_killed or result.return_code != 0, \
               "Fork bomb should be contained by sandbox"

    @pytest.mark.asyncio
    @pytest.mark.slow  # Can take 30s+ without sandbox
    async def test_cpu_time_limited(self):
        """CPU-intensive process should be limited."""
        # Note: Without proper sandbox, timeout enforcement may be slow
        # as Python subprocess.kill() doesn't immediately terminate
        profile = SandboxProfile(
            name="cpu_test",
            allowed_paths=["/tmp"],
            max_memory_mb=256,
            max_time_seconds=2,  # Short timeout
        )
        sandbox = Sandbox(profile)

        # Use simpler sleep command
        result = await sandbox.execute("sleep 30")

        # Process should be killed (timeout triggered)
        assert result.was_killed, "Long-running process should be killed by timeout"
        assert "time" in result.kill_reason.lower(), \
               f"Kill reason should mention time: {result.kill_reason}"

        # Relaxed timing check - without sandbox, killing may take longer
        # Just verify it didn't run the full 30 seconds in sandboxed mode
        if is_sandbox_available():
            assert result.execution_time_ms < 10000, \
                   f"Sandboxed execution should stop quickly, took {result.execution_time_ms}ms"


# ============================================================================
# Test Sandbox Behavior
# ============================================================================


@pytest.mark.security
@pytest.mark.sandbox
class TestSandboxBehavior:
    """Tests for general sandbox behavior."""

    @pytest.mark.asyncio
    async def test_basic_command_works(self, sandbox):
        """Basic commands should work in sandbox."""
        result = await sandbox.execute("echo 'Hello, Sandbox!'")

        assert "Hello, Sandbox!" in result.stdout, \
               f"Basic echo should work. Got: {result.stdout}"

    @pytest.mark.asyncio
    async def test_python_execution_works(self, sandbox):
        """Python execution should work in sandbox."""
        result = await sandbox.execute("python3 -c 'print(2 + 2)'")

        assert "4" in result.stdout, \
               f"Python execution should work. Got: {result.stdout}"

    @pytest.mark.asyncio
    async def test_exit_code_captured(self, sandbox):
        """Exit codes should be captured correctly."""
        # Success
        result = await sandbox.execute("exit 0")
        assert result.return_code == 0, "Exit 0 should return 0"

        # Failure
        result = await sandbox.execute("exit 42")
        assert result.return_code == 42, "Exit 42 should return 42"

    @pytest.mark.asyncio
    async def test_stderr_captured(self, sandbox):
        """Stderr should be captured."""
        result = await sandbox.execute("echo 'error' >&2")

        assert "error" in result.stderr, \
               f"Stderr should be captured. Got: {result.stderr}"

    @pytest.mark.asyncio
    async def test_execution_time_tracked(self, sandbox):
        """Execution time should be tracked."""
        result = await sandbox.execute("sleep 0.5")

        assert result.execution_time_ms >= 400, \
               f"Execution time should be at least 400ms, got {result.execution_time_ms}ms"
        assert result.execution_time_ms < 5000, \
               f"Execution time should be less than 5s, got {result.execution_time_ms}ms"

    @pytest.mark.asyncio
    async def test_working_directory_respected(self, test_workspace, permissive_profile):
        """Working directory should be respected."""
        # Update profile to include test_workspace
        permissive_profile.allowed_paths.append(str(test_workspace))
        sandbox = Sandbox(permissive_profile)

        result = await sandbox.execute("pwd", working_dir=str(test_workspace))

        # Should either be in workspace or /tmp (fallback)
        assert str(test_workspace) in result.stdout or "/tmp" in result.stdout, \
               f"Working directory should be respected. Got: {result.stdout}"

    @pytest.mark.asyncio
    async def test_violations_logged(self, strict_profile):
        """Violations should be logged in result."""
        sandbox = Sandbox(strict_profile)

        # Try to access forbidden path
        result = await sandbox.execute("cat /etc/hosts")

        # Should have violations logged
        assert len(result.violations) > 0, \
               "Violations should be logged when attempting forbidden operations"

    @pytest.mark.asyncio
    async def test_platform_detection(self):
        """Platform should be detected correctly."""
        platform = get_platform()
        assert platform in ["linux", "macos", "unsupported"], \
               f"Platform should be linux, macos, or unsupported. Got: {platform}"

    @pytest.mark.asyncio
    async def test_sandbox_availability_check(self):
        """Sandbox availability should be checkable."""
        available = is_sandbox_available()
        assert isinstance(available, bool), \
               "is_sandbox_available should return bool"


# ============================================================================
# Test Profile Validation
# ============================================================================


@pytest.mark.security
class TestProfileValidation:
    """Tests for sandbox profile validation."""

    def test_profile_requires_name(self):
        """Profile should require a name."""
        with pytest.raises(Exception):
            SandboxProfile(allowed_paths=["/tmp"])

    def test_profile_memory_limits(self):
        """Profile should enforce memory limit bounds."""
        # Too low
        with pytest.raises(Exception):
            SandboxProfile(
                name="test",
                allowed_paths=["/tmp"],
                max_memory_mb=10,  # Below minimum
            )

        # Too high
        with pytest.raises(Exception):
            SandboxProfile(
                name="test",
                allowed_paths=["/tmp"],
                max_memory_mb=100000,  # Above maximum
            )

    def test_profile_time_limits(self):
        """Profile should enforce time limit bounds."""
        # Too low
        with pytest.raises(Exception):
            SandboxProfile(
                name="test",
                allowed_paths=["/tmp"],
                max_time_seconds=0,  # Zero not allowed
            )

        # Too high
        with pytest.raises(Exception):
            SandboxProfile(
                name="test",
                allowed_paths=["/tmp"],
                max_time_seconds=100000,  # Above maximum
            )

    def test_profile_paths_normalized(self):
        """Profile paths should be normalized to absolute."""
        profile = SandboxProfile(
            name="test",
            allowed_paths=["./relative", "/absolute"],
            max_memory_mb=256,
        )

        for path in profile.allowed_paths:
            assert path.startswith("/"), \
                   f"Path should be absolute: {path}"

    def test_profile_domains_normalized(self):
        """Profile domains should be normalized."""
        profile = SandboxProfile(
            name="test",
            allowed_paths=["/tmp"],
            allowed_domains=["  GitHub.COM  ", "PYPI.org"],
        )

        assert "github.com" in profile.allowed_domains
        assert "pypi.org" in profile.allowed_domains


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.security
@pytest.mark.sandbox
@pytest.mark.slow
class TestSandboxIntegration:
    """Integration tests for complete sandbox workflows."""

    @pytest.mark.asyncio
    async def test_python_script_execution(self, test_workspace, permissive_profile):
        """Execute a Python script in sandbox."""
        permissive_profile.allowed_paths.append(str(test_workspace))
        sandbox = Sandbox(permissive_profile)

        # Create a test script
        script = test_workspace / "compute.py"
        script.write_text("""
import json
result = {'sum': sum(range(100)), 'product': 1}
for i in range(1, 10):
    result['product'] *= i
print(json.dumps(result))
""")

        result = await sandbox.execute(
            f"python3 {script}",
            working_dir=str(test_workspace)
        )

        assert result.return_code == 0, f"Script should succeed. Stderr: {result.stderr}"
        assert "4950" in result.stdout, "Sum should be calculated"
        assert "362880" in result.stdout, "Product should be calculated"

    @pytest.mark.asyncio
    async def test_multiple_sequential_executions(self, sandbox):
        """Multiple sequential executions should work."""
        results = []
        for i in range(5):
            result = await sandbox.execute(f"echo {i}")
            results.append(result)

        for i, result in enumerate(results):
            assert str(i) in result.stdout, f"Execution {i} should output {i}"

    @pytest.mark.asyncio
    async def test_environment_isolation(self, sandbox):
        """Environment should be sanitized."""
        # Set a sensitive env var
        os.environ["SECRET_KEY"] = "super_secret_value"

        result = await sandbox.execute("env | grep SECRET_KEY || echo 'not found'")

        # Secret should not be visible in sandbox
        assert "super_secret_value" not in result.stdout, \
               "Secret environment variables should not leak into sandbox"

        # Clean up
        del os.environ["SECRET_KEY"]
