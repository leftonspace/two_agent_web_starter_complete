"""
Tests for code execution engine.

PHASE 8.1: Tests for safe code execution with sandboxing, security validation,
and timeout protection.
"""

import pytest
import asyncio
from agent.actions.code_executor import CodeExecutor, ExecutionResult
from agent.actions.sandbox import SandboxValidator


# ══════════════════════════════════════════════════════════════════════
# Python Execution Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_python_simple_execution():
    """Test simple Python code execution"""
    executor = CodeExecutor()

    result = await executor.execute_python('print("Hello, World!")')

    assert result.success is True
    assert "Hello, World!" in result.output
    assert result.return_code == 0
    assert result.language == "python"


@pytest.mark.asyncio
async def test_python_with_math():
    """Test Python with math operations"""
    executor = CodeExecutor()

    code = """
x = 10
y = 20
print(x + y)
"""

    result = await executor.execute_python(code)

    assert result.success is True
    assert "30" in result.output


@pytest.mark.asyncio
async def test_python_with_functions():
    """Test Python with function definitions"""
    executor = CodeExecutor()

    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))
"""

    result = await executor.execute_python(code)

    assert result.success is True
    assert "120" in result.output


@pytest.mark.asyncio
async def test_python_blocked_imports():
    """Test dangerous Python imports are blocked"""
    executor = CodeExecutor()

    # Try to import os (dangerous)
    result = await executor.execute_python('import os\nprint(os.listdir())')

    assert result.success is False
    assert "Security violations" in result.error
    assert "os" in result.error or "Dangerous module" in result.error
    assert len(result.violations) > 0


@pytest.mark.asyncio
async def test_python_blocked_subprocess():
    """Test subprocess import is blocked"""
    executor = CodeExecutor()

    result = await executor.execute_python('import subprocess\nsubprocess.run(["ls"])')

    assert result.success is False
    assert "Security violations" in result.error


@pytest.mark.asyncio
async def test_python_blocked_eval():
    """Test eval() is blocked"""
    executor = CodeExecutor()

    result = await executor.execute_python('eval("print(1)")')

    assert result.success is False
    assert "eval" in result.error.lower()


@pytest.mark.asyncio
async def test_python_timeout():
    """Test Python execution timeout"""
    executor = CodeExecutor()

    # Infinite loop
    code = """
while True:
    pass
"""

    result = await executor.execute_python(code, timeout=2)

    assert result.success is False
    assert "timeout" in result.error.lower()
    assert result.execution_time >= 2


@pytest.mark.asyncio
async def test_python_safe_modules():
    """Test safe modules are allowed"""
    executor = CodeExecutor()

    code = """
import math
import json
import datetime

print(math.pi)
print(json.dumps({"key": "value"}))
print(datetime.datetime.now().year >= 2020)
"""

    result = await executor.execute_python(code)

    # Should execute successfully
    assert result.success is True
    assert "3.14" in result.output


# ══════════════════════════════════════════════════════════════════════
# JavaScript Execution Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_javascript_simple_execution():
    """Test simple JavaScript execution"""
    executor = CodeExecutor()

    result = await executor.execute_javascript('console.log("Hello from JS")')

    # Node.js might not be installed, check for that
    if "not installed" in result.error or "not available" in result.error:
        pytest.skip("Node.js not installed")

    assert result.success is True
    assert "Hello from JS" in result.output
    assert result.language == "javascript"


@pytest.mark.asyncio
async def test_javascript_with_arrays():
    """Test JavaScript with array operations"""
    executor = CodeExecutor()

    code = """
const numbers = [1, 2, 3, 4, 5];
const doubled = numbers.map(x => x * 2);
console.log(JSON.stringify(doubled));
"""

    result = await executor.execute_javascript(code)

    if "not installed" in result.error:
        pytest.skip("Node.js not installed")

    assert result.success is True
    assert "2,4,6,8,10" in result.output or "[2,4,6,8,10]" in result.output


@pytest.mark.asyncio
async def test_javascript_timeout():
    """Test JavaScript execution timeout"""
    executor = CodeExecutor()

    code = """
while (true) {
    // Infinite loop
}
"""

    result = await executor.execute_javascript(code, timeout=2)

    if "not installed" in result.error:
        pytest.skip("Node.js not installed")

    assert result.success is False
    assert "timeout" in result.error.lower()


# ══════════════════════════════════════════════════════════════════════
# Shell Execution Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_shell_safe_command():
    """Test safe shell command execution"""
    executor = CodeExecutor()

    result = await executor.execute_shell('echo "test"')

    assert result.success is True
    assert "test" in result.output
    assert result.language == "shell"


@pytest.mark.asyncio
async def test_shell_ls_command():
    """Test ls command"""
    executor = CodeExecutor()

    result = await executor.execute_shell('ls')

    assert result.success is True
    # Should have some output
    assert len(result.output) > 0


@pytest.mark.asyncio
async def test_shell_dangerous_command_blocked():
    """Test dangerous shell commands are blocked"""
    executor = CodeExecutor()

    # Try to execute rm (dangerous)
    result = await executor.execute_shell('rm -rf /tmp/test')

    assert result.success is False
    assert "Security violations" in result.error
    assert len(result.violations) > 0


@pytest.mark.asyncio
async def test_shell_sudo_blocked():
    """Test sudo is blocked"""
    executor = CodeExecutor()

    result = await executor.execute_shell('sudo ls')

    assert result.success is False
    assert "Security violations" in result.error


@pytest.mark.asyncio
async def test_shell_pipe_to_sh_blocked():
    """Test piping to sh is blocked"""
    executor = CodeExecutor()

    result = await executor.execute_shell('echo "ls" | sh')

    assert result.success is False
    assert "Security violations" in result.error


@pytest.mark.asyncio
async def test_shell_timeout():
    """Test shell command timeout"""
    executor = CodeExecutor()

    # Use sleep which should timeout
    result = await executor.execute_shell('sleep 100', timeout=2)

    assert result.success is False
    assert "timeout" in result.error.lower()


# ══════════════════════════════════════════════════════════════════════
# Sandbox Validator Tests
# ══════════════════════════════════════════════════════════════════════


def test_sandbox_validate_safe_imports():
    """Test validation of safe Python imports"""
    validator = SandboxValidator()

    code = """
import math
import json
print(math.pi)
"""

    is_safe, violations = validator.validate_python_imports(code)

    assert is_safe is True
    assert len(violations) == 0


def test_sandbox_validate_dangerous_imports():
    """Test validation catches dangerous imports"""
    validator = SandboxValidator()

    code = """
import os
import sys
import subprocess
"""

    is_safe, violations = validator.validate_python_imports(code)

    assert is_safe is False
    assert len(violations) >= 3


def test_sandbox_validate_safe_shell():
    """Test validation of safe shell commands"""
    validator = SandboxValidator()

    is_safe, violations = validator.validate_shell_command('ls -la')

    assert is_safe is True
    assert len(violations) == 0


def test_sandbox_validate_dangerous_shell():
    """Test validation catches dangerous shell commands"""
    validator = SandboxValidator()

    is_safe, violations = validator.validate_shell_command('rm -rf /')

    assert is_safe is False
    assert len(violations) > 0


# ══════════════════════════════════════════════════════════════════════
# Utility Tests
# ══════════════════════════════════════════════════════════════════════


def test_get_safe_commands():
    """Test getting list of safe commands"""
    executor = CodeExecutor()

    commands = executor.get_safe_commands()

    assert len(commands) > 0
    assert "ls" in commands
    assert "cat" in commands
    assert "echo" in commands
    # Dangerous commands should not be in list
    assert "rm" not in commands
    assert "sudo" not in commands


def test_is_command_safe():
    """Test command safety check"""
    executor = CodeExecutor()

    # Safe command
    is_safe, violations = executor.is_command_safe('ls -la')
    assert is_safe is True

    # Dangerous command
    is_safe, violations = executor.is_command_safe('rm test.txt')
    assert is_safe is False
    assert len(violations) > 0


def test_execution_result_to_dict():
    """Test ExecutionResult conversion to dict"""
    result = ExecutionResult(
        success=True,
        output="test output",
        error="",
        return_code=0,
        execution_time=1.5,
        language="python"
    )

    result_dict = result.to_dict()

    assert result_dict["success"] is True
    assert result_dict["output"] == "test output"
    assert result_dict["execution_time"] == 1.5
    assert result_dict["language"] == "python"
