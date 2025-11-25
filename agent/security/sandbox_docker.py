"""
PHASE 1.1: Docker-Based Sandbox Execution

Provides isolated code execution in ephemeral Docker containers to prevent
host system compromise from malicious or buggy code.

Features:
- Ephemeral containers (auto-removed after execution)
- Memory limits (default 512MB)
- CPU limits
- Network isolation (disabled by default)
- Non-root execution
- Timeout protection
- Output capture (stdout/stderr)

Requirements:
    pip install docker

Usage:
    from agent.security.sandbox_docker import DockerSandbox, run_in_sandbox

    # Using the class
    sandbox = DockerSandbox()

    # Run Python code
    result = await sandbox.run_python('''
    def factorial(n):
        return 1 if n <= 1 else n * factorial(n-1)
    print(factorial(10))
    ''')
    print(result.output)  # "3628800"

    # Run shell command
    result = await sandbox.run_shell("ls -la /tmp")

    # Or use the convenience function
    result = await run_in_sandbox("print('Hello from sandbox!')", language="python")
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.core_logging import log_event

# Try to import Docker SDK
try:
    import docker
    from docker.errors import ContainerError, ImageNotFound, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None


class SandboxLanguage(Enum):
    """Supported languages for sandboxed execution."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SHELL = "shell"


@dataclass
class SandboxResult:
    """Result of sandboxed code execution."""
    success: bool
    output: str
    error: str
    exit_code: int
    execution_time: float
    language: SandboxLanguage
    container_id: Optional[str] = None
    memory_used_mb: Optional[float] = None
    timed_out: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "language": self.language.value,
            "container_id": self.container_id,
            "memory_used_mb": self.memory_used_mb,
            "timed_out": self.timed_out,
        }


# Default Docker images for each language
DEFAULT_IMAGES: Dict[SandboxLanguage, str] = {
    SandboxLanguage.PYTHON: "python:3.11-slim",
    SandboxLanguage.JAVASCRIPT: "node:20-slim",
    SandboxLanguage.SHELL: "alpine:latest",
}


class DockerSandbox:
    """
    Docker-based sandbox for secure code execution.

    Runs code in ephemeral containers with resource limits and network isolation.
    """

    def __init__(
        self,
        memory_limit: str = "512m",
        cpu_period: int = 100000,
        cpu_quota: int = 50000,  # 50% of one CPU
        network_disabled: bool = True,
        default_timeout: int = 30,
        auto_remove: bool = True,
        custom_images: Optional[Dict[SandboxLanguage, str]] = None,
    ):
        """
        Initialize Docker sandbox.

        Args:
            memory_limit: Container memory limit (e.g., "512m", "1g")
            cpu_period: CPU period in microseconds
            cpu_quota: CPU quota in microseconds (cpu_quota/cpu_period = CPU fraction)
            network_disabled: Disable network access in container
            default_timeout: Default execution timeout in seconds
            auto_remove: Automatically remove container after execution
            custom_images: Custom Docker images for each language
        """
        if not DOCKER_AVAILABLE:
            raise ImportError(
                "Docker SDK not available. Install with: pip install docker"
            )

        self.memory_limit = memory_limit
        self.cpu_period = cpu_period
        self.cpu_quota = cpu_quota
        self.network_disabled = network_disabled
        self.default_timeout = default_timeout
        self.auto_remove = auto_remove

        # Merge custom images with defaults
        self.images = DEFAULT_IMAGES.copy()
        if custom_images:
            self.images.update(custom_images)

        # Initialize Docker client
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self._docker_available = True
        except Exception as e:
            log_event("docker_sandbox_init_failed", {"error": str(e)})
            self._docker_available = False
            self.client = None

        # Statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.timeout_count = 0

    def is_available(self) -> bool:
        """Check if Docker sandbox is available."""
        return self._docker_available and self.client is not None

    async def run_python(
        self,
        code: str,
        timeout: Optional[int] = None,
        packages: Optional[List[str]] = None,
    ) -> SandboxResult:
        """
        Run Python code in sandbox.

        Args:
            code: Python code to execute
            timeout: Execution timeout (default from config)
            packages: Additional pip packages to install

        Returns:
            SandboxResult with output and status
        """
        return await self._run_code(
            code=code,
            language=SandboxLanguage.PYTHON,
            timeout=timeout,
            packages=packages,
        )

    async def run_javascript(
        self,
        code: str,
        timeout: Optional[int] = None,
        packages: Optional[List[str]] = None,
    ) -> SandboxResult:
        """
        Run JavaScript code in sandbox.

        Args:
            code: JavaScript code to execute
            timeout: Execution timeout (default from config)
            packages: Additional npm packages to install

        Returns:
            SandboxResult with output and status
        """
        return await self._run_code(
            code=code,
            language=SandboxLanguage.JAVASCRIPT,
            timeout=timeout,
            packages=packages,
        )

    async def run_shell(
        self,
        command: str,
        timeout: Optional[int] = None,
    ) -> SandboxResult:
        """
        Run shell command in sandbox.

        Args:
            command: Shell command to execute
            timeout: Execution timeout (default from config)

        Returns:
            SandboxResult with output and status
        """
        return await self._run_code(
            code=command,
            language=SandboxLanguage.SHELL,
            timeout=timeout,
        )

    async def _run_code(
        self,
        code: str,
        language: SandboxLanguage,
        timeout: Optional[int] = None,
        packages: Optional[List[str]] = None,
    ) -> SandboxResult:
        """
        Internal method to run code in a Docker container.

        Args:
            code: Code to execute
            language: Programming language
            timeout: Execution timeout
            packages: Additional packages to install

        Returns:
            SandboxResult with output and status
        """
        if not self.is_available():
            return SandboxResult(
                success=False,
                output="",
                error="Docker sandbox not available. Ensure Docker is running.",
                exit_code=-1,
                execution_time=0,
                language=language,
            )

        self.total_executions += 1
        timeout = timeout or self.default_timeout
        start_time = datetime.now()

        # Get image for language
        image = self.images[language]

        # Build command based on language
        if language == SandboxLanguage.PYTHON:
            # Write code to temp file in container
            cmd = self._build_python_command(code, packages)
        elif language == SandboxLanguage.JAVASCRIPT:
            cmd = self._build_javascript_command(code, packages)
        else:  # Shell
            cmd = ["sh", "-c", code]

        container = None
        try:
            # Pull image if not available
            try:
                self.client.images.get(image)
            except ImageNotFound:
                log_event("docker_pulling_image", {"image": image})
                self.client.images.pull(image)

            # Run container
            log_event("docker_sandbox_start", {
                "language": language.value,
                "image": image,
                "timeout": timeout,
            })

            # Run in a thread pool since Docker SDK is synchronous
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.run(
                    image,
                    command=cmd,
                    mem_limit=self.memory_limit,
                    cpu_period=self.cpu_period,
                    cpu_quota=self.cpu_quota,
                    network_disabled=self.network_disabled,
                    remove=False,  # Don't auto-remove so we can get logs
                    user="nobody",  # Never run as root
                    detach=True,
                    working_dir="/tmp",
                    environment={
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONUNBUFFERED": "1",
                    },
                )
            )

            # Wait for container with timeout
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: container.wait(timeout=timeout)
                    ),
                    timeout=timeout + 5  # Extra buffer for Docker overhead
                )
                exit_code = result.get("StatusCode", -1)
                timed_out = False

            except asyncio.TimeoutError:
                # Kill container on timeout
                await loop.run_in_executor(None, container.kill)
                exit_code = -1
                timed_out = True
                self.timeout_count += 1

            # Get logs
            stdout = await loop.run_in_executor(
                None,
                lambda: container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            )
            stderr = await loop.run_in_executor(
                None,
                lambda: container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            )

            # Get container stats (memory usage)
            memory_used_mb = None
            try:
                stats = await loop.run_in_executor(
                    None,
                    lambda: container.stats(stream=False)
                )
                if "memory_stats" in stats and "usage" in stats["memory_stats"]:
                    memory_used_mb = stats["memory_stats"]["usage"] / (1024 * 1024)
            except Exception:
                pass  # Stats might not be available

            execution_time = (datetime.now() - start_time).total_seconds()

            success = exit_code == 0 and not timed_out

            if success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1

            log_event("docker_sandbox_complete", {
                "language": language.value,
                "exit_code": exit_code,
                "execution_time": execution_time,
                "timed_out": timed_out,
                "success": success,
            })

            return SandboxResult(
                success=success,
                output=stdout[:50000],  # Limit output size
                error=stderr[:50000] if not timed_out else f"Execution timed out after {timeout}s",
                exit_code=exit_code,
                execution_time=execution_time,
                language=language,
                container_id=container.id[:12] if container else None,
                memory_used_mb=memory_used_mb,
                timed_out=timed_out,
            )

        except ContainerError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.failed_executions += 1

            log_event("docker_sandbox_container_error", {
                "language": language.value,
                "error": str(e),
            })

            return SandboxResult(
                success=False,
                output="",
                error=f"Container error: {e}",
                exit_code=e.exit_status if hasattr(e, "exit_status") else -1,
                execution_time=execution_time,
                language=language,
            )

        except APIError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.failed_executions += 1

            log_event("docker_sandbox_api_error", {
                "language": language.value,
                "error": str(e),
            })

            return SandboxResult(
                success=False,
                output="",
                error=f"Docker API error: {e}",
                exit_code=-1,
                execution_time=execution_time,
                language=language,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.failed_executions += 1

            log_event("docker_sandbox_error", {
                "language": language.value,
                "error": str(e),
            })

            return SandboxResult(
                success=False,
                output="",
                error=f"Sandbox error: {e}",
                exit_code=-1,
                execution_time=execution_time,
                language=language,
            )

        finally:
            # Clean up container
            if container and self.auto_remove:
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: container.remove(force=True)
                    )
                except Exception:
                    pass  # Best effort cleanup

    def _build_python_command(
        self,
        code: str,
        packages: Optional[List[str]] = None
    ) -> List[str]:
        """Build command for Python execution."""
        # Create a script that installs packages and runs code
        script_parts = []

        if packages:
            pkg_list = " ".join(packages)
            script_parts.append(f"pip install --quiet {pkg_list}")

        # Escape code for shell
        escaped_code = code.replace("'", "'\"'\"'")
        script_parts.append(f"python3 -c '{escaped_code}'")

        full_script = " && ".join(script_parts)
        return ["sh", "-c", full_script]

    def _build_javascript_command(
        self,
        code: str,
        packages: Optional[List[str]] = None
    ) -> List[str]:
        """Build command for JavaScript execution."""
        script_parts = []

        if packages:
            pkg_list = " ".join(packages)
            script_parts.append(f"npm install --silent {pkg_list}")

        # Escape code for shell
        escaped_code = code.replace("'", "'\"'\"'")
        script_parts.append(f"node -e '{escaped_code}'")

        full_script = " && ".join(script_parts)
        return ["sh", "-c", full_script]

    def get_statistics(self) -> Dict[str, Any]:
        """Get sandbox statistics."""
        return {
            "available": self.is_available(),
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "timeout_count": self.timeout_count,
            "success_rate": self.successful_executions / max(self.total_executions, 1),
        }


# ============================================================================
# Convenience Functions
# ============================================================================

# Global sandbox instance
_default_sandbox: Optional[DockerSandbox] = None


def get_default_sandbox() -> DockerSandbox:
    """Get or create the default Docker sandbox."""
    global _default_sandbox
    if _default_sandbox is None:
        _default_sandbox = DockerSandbox()
    return _default_sandbox


async def run_in_sandbox(
    code: str,
    language: str = "python",
    timeout: Optional[int] = None,
    packages: Optional[List[str]] = None,
) -> SandboxResult:
    """
    Convenience function to run code in sandbox.

    Args:
        code: Code to execute
        language: Programming language ("python", "javascript", "shell")
        timeout: Execution timeout in seconds
        packages: Additional packages to install

    Returns:
        SandboxResult with output and status
    """
    sandbox = get_default_sandbox()

    lang = SandboxLanguage(language.lower())

    if lang == SandboxLanguage.PYTHON:
        return await sandbox.run_python(code, timeout, packages)
    elif lang == SandboxLanguage.JAVASCRIPT:
        return await sandbox.run_javascript(code, timeout, packages)
    else:
        return await sandbox.run_shell(code, timeout)


def is_sandbox_available() -> bool:
    """Check if Docker sandbox is available."""
    try:
        sandbox = get_default_sandbox()
        return sandbox.is_available()
    except ImportError:
        return False
