"""
PHASE 3.1: Sandbox Execution Environment

Provides safe, resource-limited execution environments for running code:
- Process-based sandboxing with resource limits
- Time limits (timeouts)
- Memory limits (via ulimit/resource module)
- Network isolation (optional)
- Filesystem restrictions (chroot-like, working directory isolation)

Usage:
    >>> from agent import sandbox
    >>> result = sandbox.run_in_sandbox(
    ...     command=["python", "test.py"],
    ...     working_dir="/path/to/project",
    ...     timeout_seconds=30,
    ...     memory_limit_mb=512
    ... )
    >>> if result["success"]:
    ...     print(result["stdout"])
"""

from __future__ import annotations

import os
import resource
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports
try:
    import paths as paths_module
    PATHS_AVAILABLE = True
except ImportError:
    PATHS_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Resource Limit Helpers
# ══════════════════════════════════════════════════════════════════════


def _set_resource_limits(memory_limit_mb: Optional[int] = None) -> None:
    """
    Set resource limits for the subprocess.

    This function is called via preexec_fn in subprocess.Popen.
    Only works on Unix-like systems (Linux, macOS).

    Args:
        memory_limit_mb: Memory limit in MB (default: None = no limit)
    """
    # Set memory limit (virtual memory)
    if memory_limit_mb is not None:
        try:
            memory_bytes = memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        except (ValueError, OSError) as e:
            # May fail on some systems or if limit is too high
            print(f"[Sandbox] Warning: Could not set memory limit: {e}")

    # Prevent core dumps
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    except (ValueError, OSError):
        pass

    # Limit CPU time (not wall clock time, but actual CPU seconds)
    # Set to 5 minutes of CPU time max
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
    except (ValueError, OSError):
        pass


# ══════════════════════════════════════════════════════════════════════
# Sandbox Execution
# ══════════════════════════════════════════════════════════════════════


def run_in_sandbox(
    command: List[str],
    working_dir: Optional[Path] = None,
    timeout_seconds: int = 120,
    memory_limit_mb: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
    network_isolation: bool = False,
) -> Dict[str, Any]:
    """
    Run a command in a sandboxed environment with resource limits.

    Args:
        command: Command and arguments to execute
        working_dir: Working directory for the command (default: temp directory)
        timeout_seconds: Maximum execution time in seconds (default: 120)
        memory_limit_mb: Memory limit in MB (default: None = no limit)
        env: Environment variables for the subprocess (default: inherit parent)
        network_isolation: If True, attempt to disable network (Linux only, requires unshare)

    Returns:
        Dict with:
            success: bool - True if command succeeded
            exit_code: int - Process exit code
            stdout: str - Standard output
            stderr: str - Standard error
            timeout: bool - True if process was killed due to timeout
            error: Optional[str] - Error message if execution failed
    """
    # Validate working directory
    if working_dir is None:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="sandbox_"))
        working_dir = temp_dir
        cleanup_temp = True
    else:
        working_dir = Path(working_dir)
        cleanup_temp = False

    if not working_dir.exists():
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"Working directory does not exist: {working_dir}",
        }

    # Safety check: Ensure working_dir is safe
    if PATHS_AVAILABLE:
        if not paths_module.is_safe_path(working_dir):
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "timeout": False,
                "error": f"Unsafe working directory: {working_dir}",
            }

    # Build environment
    if env is None:
        env = os.environ.copy()

    # Network isolation (Linux only, requires unshare command)
    if network_isolation and os.name == "posix":
        # Prepend unshare command to disable network namespace
        # NOTE: Requires root or CAP_NET_ADMIN capability
        command = ["unshare", "--net", "--"] + command

    # Prepare resource limit callback
    def preexec() -> None:
        _set_resource_limits(memory_limit_mb=memory_limit_mb)

    # Execute command
    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            env=env,
            capture_output=True,
            timeout=timeout_seconds,
            preexec_fn=preexec if os.name == "posix" else None,  # Only on Unix
        )

        success = (result.returncode == 0)

        return {
            "success": success,
            "exit_code": result.returncode,
            "stdout": result.stdout.decode("utf-8", errors="replace"),
            "stderr": result.stderr.decode("utf-8", errors="replace"),
            "timeout": False,
            "error": None,
        }

    except subprocess.TimeoutExpired as e:
        # Command exceeded timeout
        stdout = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
        stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""

        return {
            "success": False,
            "exit_code": -1,
            "stdout": stdout,
            "stderr": stderr,
            "timeout": True,
            "error": f"Command exceeded timeout of {timeout_seconds}s",
        }

    except Exception as e:
        # Other execution errors
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"Sandbox execution failed: {str(e)}",
        }

    finally:
        # Cleanup temporary directory if created
        if cleanup_temp and temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════
# PHASE 3.1: Language-Specific Snippet Execution
# ══════════════════════════════════════════════════════════════════════


def run_python_snippet(
    code: str,
    working_dir: Optional[Path] = None,
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    """
    Execute Python code snippet in a sandboxed environment.

    Args:
        code: Python code to execute
        working_dir: Working directory (default: temp directory)
        timeout_seconds: Timeout in seconds (default: 30)

    Returns:
        Sandbox execution result dict

    Example:
        >>> result = run_python_snippet("print('Hello, World!')")
        >>> print(result['stdout'])
        Hello, World!
    """
    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False,
        encoding='utf-8',
    ) as f:
        f.write(code)
        temp_file = Path(f.name)

    try:
        result = run_in_sandbox(
            command=['python3', str(temp_file)],
            working_dir=working_dir,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=256,  # 256MB for snippets
        )
        return result
    finally:
        # Clean up temporary file
        try:
            temp_file.unlink()
        except Exception:
            pass


def run_node_snippet(
    code: str,
    working_dir: Optional[Path] = None,
    timeout_seconds: int = 30,
) -> Dict[str, Any]:
    """
    Execute Node.js code snippet in a sandboxed environment.

    Args:
        code: JavaScript code to execute
        working_dir: Working directory (default: temp directory)
        timeout_seconds: Timeout in seconds (default: 30)

    Returns:
        Sandbox execution result dict

    Example:
        >>> result = run_node_snippet("console.log('Hello from Node')")
        >>> print(result['stdout'])
        Hello from Node
    """
    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.js',
        delete=False,
        encoding='utf-8',
    ) as f:
        f.write(code)
        temp_file = Path(f.name)

    try:
        result = run_in_sandbox(
            command=['node', str(temp_file)],
            working_dir=working_dir,
            timeout_seconds=timeout_seconds,
            memory_limit_mb=256,  # 256MB for snippets
        )
        return result
    finally:
        # Clean up temporary file
        try:
            temp_file.unlink()
        except Exception:
            pass


def run_script(
    script_path: Path,
    args: Optional[List[str]] = None,
    working_dir: Optional[Path] = None,
    timeout_seconds: int = 60,
    interpreter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute a script file in a sandboxed environment.

    Args:
        script_path: Path to the script file
        args: Optional command-line arguments
        working_dir: Working directory (default: script directory)
        timeout_seconds: Timeout in seconds (default: 60)
        interpreter: Optional interpreter (e.g., 'python3', 'node', 'bash')

    Returns:
        Sandbox execution result dict

    Example:
        >>> result = run_script(Path('test.py'), interpreter='python3')
        >>> print(result['success'])
        True
    """
    if not script_path.exists():
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"Script file does not exist: {script_path}",
        }

    # Determine working directory
    if working_dir is None:
        working_dir = script_path.parent

    # Build command
    if interpreter:
        command = [interpreter, str(script_path)]
    else:
        command = [str(script_path)]

    # Add arguments
    if args:
        command.extend(args)

    return run_in_sandbox(
        command=command,
        working_dir=working_dir,
        timeout_seconds=timeout_seconds,
        memory_limit_mb=512,  # 512MB for scripts
    )


# ══════════════════════════════════════════════════════════════════════
# High-Level Sandbox Functions
# ══════════════════════════════════════════════════════════════════════


def run_tests_sandboxed(
    project_dir: Path,
    test_command: Optional[List[str]] = None,
    timeout_seconds: int = 300,
) -> Dict[str, Any]:
    """
    Run tests in a sandboxed environment.

    Args:
        project_dir: Project directory
        test_command: Test command (default: ["pytest"])
        timeout_seconds: Timeout in seconds (default: 300 = 5 minutes)

    Returns:
        Sandbox execution result dict
    """
    if test_command is None:
        test_command = ["pytest", "--tb=short", "-v"]

    return run_in_sandbox(
        command=test_command,
        working_dir=project_dir,
        timeout_seconds=timeout_seconds,
        memory_limit_mb=1024,  # 1GB limit for tests
    )


def run_linter_sandboxed(
    project_dir: Path,
    linter_command: Optional[List[str]] = None,
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """
    Run linter in a sandboxed environment.

    Args:
        project_dir: Project directory
        linter_command: Linter command (default: ["ruff", "check", "."])
        timeout_seconds: Timeout in seconds (default: 120 = 2 minutes)

    Returns:
        Sandbox execution result dict
    """
    if linter_command is None:
        linter_command = ["ruff", "check", "."]

    return run_in_sandbox(
        command=linter_command,
        working_dir=project_dir,
        timeout_seconds=timeout_seconds,
        memory_limit_mb=512,  # 512MB limit for linter
    )


def run_build_sandboxed(
    project_dir: Path,
    build_command: List[str],
    timeout_seconds: int = 600,
) -> Dict[str, Any]:
    """
    Run build command in a sandboxed environment.

    Args:
        project_dir: Project directory
        build_command: Build command (e.g., ["npm", "run", "build"])
        timeout_seconds: Timeout in seconds (default: 600 = 10 minutes)

    Returns:
        Sandbox execution result dict
    """
    return run_in_sandbox(
        command=build_command,
        working_dir=project_dir,
        timeout_seconds=timeout_seconds,
        memory_limit_mb=2048,  # 2GB limit for builds
    )


# ══════════════════════════════════════════════════════════════════════
# Docker-based Sandboxing (Future Enhancement)
# ══════════════════════════════════════════════════════════════════════


def run_in_docker_sandbox(
    command: List[str],
    working_dir: Path,
    docker_image: str = "python:3.11-slim",
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """
    Run a command in a Docker container for maximum isolation.

    NOTE: This requires Docker to be installed and accessible.
    This is a future enhancement placeholder - not fully implemented.

    Args:
        command: Command to execute
        working_dir: Working directory to mount
        docker_image: Docker image to use
        timeout_seconds: Timeout in seconds

    Returns:
        Sandbox execution result dict
    """
    # Check if docker is available
    import shutil
    if not shutil.which("docker"):
        return {
            "success": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": "Docker is not installed or not on PATH",
        }

    # Build docker run command
    # Mount working directory read-only for safety
    docker_command = [
        "docker", "run",
        "--rm",  # Remove container after exit
        "--network", "none",  # Disable network
        "--memory", "512m",  # Memory limit
        "--cpus", "1.0",  # CPU limit
        "-v", f"{working_dir}:/workspace:ro",  # Mount read-only
        "-w", "/workspace",
        docker_image,
    ] + command

    return run_in_sandbox(
        command=docker_command,
        working_dir=None,  # Docker handles working directory
        timeout_seconds=timeout_seconds,
        network_isolation=False,  # Docker already handles this
    )


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for sandbox testing."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Sandbox Execution Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        nargs="+",
        help="Command to execute in sandbox",
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        help="Working directory (default: temp directory)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--memory",
        type=int,
        help="Memory limit in MB (default: no limit)",
    )
    parser.add_argument(
        "--network-isolation",
        action="store_true",
        help="Enable network isolation (Linux only)",
    )

    args = parser.parse_args()

    working_dir = Path(args.working_dir) if args.working_dir else None

    result = run_in_sandbox(
        command=args.command,
        working_dir=working_dir,
        timeout_seconds=args.timeout,
        memory_limit_mb=args.memory,
        network_isolation=args.network_isolation,
    )

    print(f"Exit code: {result['exit_code']}")
    print(f"Success: {result['success']}")
    print(f"Timeout: {result['timeout']}")

    if result.get("error"):
        print(f"Error: {result['error']}")

    if result["stdout"]:
        print(f"\n--- STDOUT ---\n{result['stdout']}")

    if result["stderr"]:
        print(f"\n--- STDERR ---\n{result['stderr']}")

    sys.exit(result["exit_code"])


if __name__ == "__main__":
    main()
