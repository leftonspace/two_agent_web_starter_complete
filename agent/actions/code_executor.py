"""
Code execution engine with sandboxing.

PHASE 8.1: Safe code execution for Python, JavaScript, and shell commands
with security controls, timeout protection, and output capture.
"""

import asyncio
import subprocess
import tempfile
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from agent.actions.sandbox import (
    SandboxValidator,
    create_restricted_python_globals,
    SAFE_SHELL_COMMANDS
)
from agent.core_logging import log_event


class ExecutionResult:
    """Result of code execution"""

    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        return_code: int = 0,
        execution_time: float = 0.0,
        language: str = "",
        violations: Optional[List[str]] = None
    ):
        self.success = success
        self.output = output
        self.error = error
        self.return_code = return_code
        self.execution_time = execution_time
        self.language = language
        self.violations = violations or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "return_code": self.return_code,
            "execution_time": self.execution_time,
            "language": self.language,
            "violations": self.violations
        }


class CodeExecutor:
    """
    Safe code execution engine with sandboxing.

    Features:
    - Python execution in isolated subprocess
    - JavaScript execution via Node.js
    - Shell command execution (whitelisted only)
    - Timeout protection
    - Output capture (stdout, stderr)
    - Security validation
    - Resource limits

    Example:
        executor = CodeExecutor()

        # Execute Python
        result = await executor.execute_python('''
        def factorial(n):
            return 1 if n <= 1 else n * factorial(n-1)
        print(factorial(5))
        ''')

        # Execute JavaScript
        result = await executor.execute_javascript('''
        console.log([1,2,3,4,5].map(x => x * 2));
        ''')

        # Execute shell
        result = await executor.execute_shell('ls -la')
    """

    def __init__(
        self,
        default_timeout: int = 30,
        max_output_size: int = 10000,
        enable_network: bool = False
    ):
        """
        Initialize code executor.

        Args:
            default_timeout: Default execution timeout in seconds
            max_output_size: Maximum output size in characters
            enable_network: Allow network access (disabled by default)
        """
        self.default_timeout = default_timeout
        self.max_output_size = max_output_size
        self.enable_network = enable_network
        self.validator = SandboxValidator()

    async def execute_python(
        self,
        code: str,
        timeout: Optional[int] = None,
        capture_output: bool = True
    ) -> ExecutionResult:
        """
        Execute Python code in sandboxed subprocess.

        Args:
            code: Python code to execute
            timeout: Execution timeout (uses default if None)
            capture_output: Whether to capture output

        Returns:
            ExecutionResult with output and status
        """
        start_time = datetime.now()
        timeout = timeout or self.default_timeout

        # Validate code
        is_safe, violations = self.validator.validate_python_imports(code)
        if not is_safe:
            log_event("python_execution_blocked", {
                "violations": violations
            })
            return ExecutionResult(
                success=False,
                error=f"Security violations: {', '.join(violations)}",
                language="python",
                violations=violations
            )

        # Validate resource limits
        is_valid, issues = self.validator.validate_resource_limits(timeout)
        if not is_valid:
            return ExecutionResult(
                success=False,
                error=f"Invalid resource limits: {', '.join(issues)}",
                language="python"
            )

        # Create temporary file for code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute Python code in subprocess
            process = await asyncio.create_subprocess_exec(
                'python3',
                temp_file,
                stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                # Security: Limit environment variables
                env={
                    'PATH': os.environ.get('PATH', ''),
                    'PYTHONDONTWRITEBYTECODE': '1',
                    'PYTHONUNBUFFERED': '1'
                }
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                # Decode output
                output = stdout.decode('utf-8', errors='replace')[:self.max_output_size]
                error = stderr.decode('utf-8', errors='replace')[:self.max_output_size]

                execution_time = (datetime.now() - start_time).total_seconds()

                log_event("python_execution_completed", {
                    "return_code": process.returncode,
                    "execution_time": execution_time
                })

                return ExecutionResult(
                    success=process.returncode == 0,
                    output=output,
                    error=error,
                    return_code=process.returncode,
                    execution_time=execution_time,
                    language="python"
                )

            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.wait()

                log_event("python_execution_timeout", {
                    "timeout": timeout
                })

                return ExecutionResult(
                    success=False,
                    error=f"Execution exceeded {timeout}s timeout",
                    return_code=-1,
                    execution_time=timeout,
                    language="python"
                )

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    async def execute_javascript(
        self,
        code: str,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute JavaScript code via Node.js.

        Args:
            code: JavaScript code to execute
            timeout: Execution timeout (uses default if None)

        Returns:
            ExecutionResult with output and status
        """
        start_time = datetime.now()
        timeout = timeout or self.default_timeout

        # Validate resource limits
        is_valid, issues = self.validator.validate_resource_limits(timeout)
        if not is_valid:
            return ExecutionResult(
                success=False,
                error=f"Invalid resource limits: {', '.join(issues)}",
                language="javascript"
            )

        # Check if Node.js is available
        try:
            node_check = await asyncio.create_subprocess_exec(
                'node',
                '--version',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await node_check.wait()

            if node_check.returncode != 0:
                return ExecutionResult(
                    success=False,
                    error="Node.js not available",
                    language="javascript"
                )
        except FileNotFoundError:
            return ExecutionResult(
                success=False,
                error="Node.js not installed",
                language="javascript"
            )

        # Create temporary file for code
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.js',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute JavaScript code
            process = await asyncio.create_subprocess_exec(
                'node',
                temp_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={'PATH': os.environ.get('PATH', '')}
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                output = stdout.decode('utf-8', errors='replace')[:self.max_output_size]
                error = stderr.decode('utf-8', errors='replace')[:self.max_output_size]

                execution_time = (datetime.now() - start_time).total_seconds()

                log_event("javascript_execution_completed", {
                    "return_code": process.returncode,
                    "execution_time": execution_time
                })

                return ExecutionResult(
                    success=process.returncode == 0,
                    output=output,
                    error=error,
                    return_code=process.returncode,
                    execution_time=execution_time,
                    language="javascript"
                )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

                log_event("javascript_execution_timeout", {
                    "timeout": timeout
                })

                return ExecutionResult(
                    success=False,
                    error=f"Execution exceeded {timeout}s timeout",
                    return_code=-1,
                    execution_time=timeout,
                    language="javascript"
                )

        finally:
            try:
                os.unlink(temp_file)
            except:
                pass

    async def execute_shell(
        self,
        command: str,
        timeout: Optional[int] = None,
        working_dir: Optional[str] = None
    ) -> ExecutionResult:
        """
        Execute shell command (whitelisted only).

        Args:
            command: Shell command to execute
            timeout: Execution timeout (uses default if None)
            working_dir: Working directory for command

        Returns:
            ExecutionResult with output and status
        """
        start_time = datetime.now()
        timeout = timeout or self.default_timeout

        # Validate command
        is_safe, violations = self.validator.validate_shell_command(command)
        if not is_safe:
            log_event("shell_execution_blocked", {
                "command": command,
                "violations": violations
            })
            return ExecutionResult(
                success=False,
                error=f"Security violations: {', '.join(violations)}",
                language="shell",
                violations=violations
            )

        # Validate resource limits
        is_valid, issues = self.validator.validate_resource_limits(timeout)
        if not is_valid:
            return ExecutionResult(
                success=False,
                error=f"Invalid resource limits: {', '.join(issues)}",
                language="shell"
            )

        try:
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env={'PATH': os.environ.get('PATH', '')}
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                output = stdout.decode('utf-8', errors='replace')[:self.max_output_size]
                error = stderr.decode('utf-8', errors='replace')[:self.max_output_size]

                execution_time = (datetime.now() - start_time).total_seconds()

                log_event("shell_execution_completed", {
                    "command": command.split()[0],
                    "return_code": process.returncode,
                    "execution_time": execution_time
                })

                return ExecutionResult(
                    success=process.returncode == 0,
                    output=output,
                    error=error,
                    return_code=process.returncode,
                    execution_time=execution_time,
                    language="shell"
                )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

                log_event("shell_execution_timeout", {
                    "command": command.split()[0],
                    "timeout": timeout
                })

                return ExecutionResult(
                    success=False,
                    error=f"Execution exceeded {timeout}s timeout",
                    return_code=-1,
                    execution_time=timeout,
                    language="shell"
                )

        except Exception as e:
            log_event("shell_execution_error", {
                "command": command,
                "error": str(e)
            })

            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}",
                return_code=-1,
                language="shell"
            )

    def get_safe_commands(self) -> List[str]:
        """Get list of whitelisted shell commands"""
        return sorted(list(SAFE_SHELL_COMMANDS))

    def is_command_safe(self, command: str) -> tuple[bool, List[str]]:
        """
        Check if shell command is safe to execute.

        Returns:
            (is_safe, list_of_violations)
        """
        return self.validator.validate_shell_command(command)
