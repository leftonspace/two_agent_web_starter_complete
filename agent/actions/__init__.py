"""
Action execution module.

PHASE 8.1: Code execution engine with sandboxing.
PHASE 8.2: API integration system with authentication and retry.
PHASE 8.3: File system operations with git integration.

Provides safe execution of Python, JavaScript, and shell commands
with security controls, timeout protection, and output capture.

Provides robust HTTP client for external API integration with
authentication, rate limiting, and exponential backoff retry.

Provides safe file system operations with workspace restrictions
and git repository management.
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
from agent.actions.api_client import (
    APIClient,
    AuthType
)
from agent.actions.rate_limiter import (
    RateLimiter
)
from agent.actions.file_ops import (
    FileOperations
)
from agent.actions.git_ops import (
    GitOps
)

__all__ = [
    "CodeExecutor",
    "ExecutionResult",
    "SandboxValidator",
    "create_restricted_python_globals",
    "SAFE_SHELL_COMMANDS",
    "DANGEROUS_MODULES",
    "APIClient",
    "AuthType",
    "RateLimiter",
    "FileOperations",
    "GitOps"
]
