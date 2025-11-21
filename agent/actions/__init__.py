"""
Action execution module.

PHASE 8.1: Code execution engine with sandboxing.

Provides safe execution of Python, JavaScript, and shell commands
with security controls, timeout protection, and output capture.
"""

from agent.actions.code_executor import (
    CodeExecutor,
    ExecutionResult
)
from agent.actions.sandbox import (
    SandboxValidator,
    create_restricted_python_globals,
    SAFE_SHELL_COMMANDS,
    DANGEROUS_MODULES
)

__all__ = [
    "CodeExecutor",
    "ExecutionResult",
    "SandboxValidator",
    "create_restricted_python_globals",
    "SAFE_SHELL_COMMANDS",
    "DANGEROUS_MODULES"
]
