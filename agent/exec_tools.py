# exec_tools.py
"""
Centralized tool registry for the multi-agent orchestrator.

STAGE 2.1 (HARDENED): Provides tools that agents can request, including:
- Code formatting (ruff/black)
- Unit and integration tests (pytest)
- Git operations (diff, status)

All tools return structured results with status, exit_code, and output.

SECURITY NOTES:
- All tools check for executable availability before invocation using shutil.which()
- Shell command execution (run_shell) has been removed from the public tool registry
  to prevent command injection attacks in multi-agent environments
- All subprocess calls use shell=False and explicit timeouts

OS COMPATIBILITY:
- Tools depend on external executables (ruff, black, pytest, git)
- If these are not installed or not on PATH, tools will fail gracefully with
  structured error messages (exit_code 127)
- Tested on Unix-like systems; Windows compatibility depends on having these
  tools installed and available on PATH
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Tool Implementation
# ══════════════════════════════════════════════════════════════════════


def format_code(
    project_dir: str,
    formatter: str = "ruff",
    paths: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Format source code using ruff or black.

    REQUIRES: ruff or black to be installed and available on PATH

    Args:
        project_dir: Path to the project directory
        formatter: "ruff" or "black" (default: "ruff")
        paths: Optional list of specific paths to format (default: format entire project)

    Returns:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str,
            "error": str
        }
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Project directory not found: {project_dir}"
        }

    # Validate formatter choice
    if formatter not in ("ruff", "black"):
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Unknown formatter: {formatter}. Use 'ruff' or 'black'."
        }

    # Check if formatter is installed (OS-agnostic availability check)
    if not shutil.which(formatter):
        return {
            "status": "failed",
            "exit_code": 127,
            "output": "",
            "error": f"{formatter} is not installed or not on PATH. Install with: pip install {formatter}"
        }

    # Build command
    if formatter == "ruff":
        cmd = ["ruff", "format"]
    else:  # black
        cmd = ["black"]

    # Add paths
    if paths:
        cmd.extend(paths)
    else:
        cmd.append(".")

    # Run formatter
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False  # Explicit: never use shell=True
        )

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "exit_code": 124,
            "output": "",
            "error": "Formatting timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Formatting failed: {str(e)}"
        }


def run_unit_tests(
    project_dir: str,
    test_path: str = "tests/unit",
    extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run unit tests using pytest.

    REQUIRES: pytest to be installed and available on PATH

    Args:
        project_dir: Path to the project directory
        test_path: Path to unit tests directory (default: "tests/unit")
        extra_args: Optional extra arguments to pass to pytest

    Returns:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str,
            "error": str,
            "passed": int,
            "failed": int,
            "skipped": int
        }
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Project directory not found: {project_dir}",
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

    # Check if pytest is installed (OS-agnostic availability check)
    if not shutil.which("pytest"):
        return {
            "status": "failed",
            "exit_code": 127,
            "output": "",
            "error": "pytest is not installed or not on PATH. Install with: pip install pytest",
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }

    # Build command
    cmd = ["pytest", "-v", "--tb=short"]
    if extra_args:
        cmd.extend(extra_args)

    # Add test path if it exists
    if (project_path / test_path).exists():
        cmd.append(test_path)
    # else: pytest will search default locations

    # Run pytest
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
            shell=False  # Explicit: never use shell=True
        )

        # Parse test results from output
        passed, failed, skipped = _parse_pytest_results(result.stdout)

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr,
            "passed": passed,
            "failed": failed,
            "skipped": skipped
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "exit_code": 124,
            "output": "",
            "error": "Tests timed out after 300 seconds",
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    except Exception as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Test execution failed: {str(e)}",
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }


def run_integration_tests(
    project_dir: str,
    test_path: str = "tests/integration",
    extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run integration tests using pytest.

    REQUIRES: pytest to be installed and available on PATH

    Args:
        project_dir: Path to the project directory
        test_path: Path to integration tests directory (default: "tests/integration")
        extra_args: Optional extra arguments to pass to pytest

    Returns:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str,
            "error": str,
            "passed": int,
            "failed": int,
            "skipped": int
        }
    """
    # Integration tests use the same implementation as unit tests, just different path
    return run_unit_tests(project_dir, test_path, extra_args)


def git_diff(
    project_dir: str,
    options: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Show git diff for the repository.

    REQUIRES: git to be installed and available on PATH
    REQUIRES: project_dir must be a git repository

    Args:
        project_dir: Path to the project directory (should be a git repo)
        options: Optional git diff options (e.g., ["--staged", "--stat"])

    Returns:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str (diff text, may be truncated if >10KB),
            "error": str,
            "truncated": bool
        }
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Project directory not found: {project_dir}",
            "truncated": False
        }

    # Check if git is installed (OS-agnostic availability check)
    if not shutil.which("git"):
        return {
            "status": "failed",
            "exit_code": 127,
            "output": "",
            "error": "git is not installed or not on PATH. Install git to use this tool.",
            "truncated": False
        }

    # Check if .git exists
    git_dir = project_path / ".git"
    if not git_dir.exists():
        return {
            "status": "failed",
            "exit_code": 128,
            "output": "",
            "error": f"Not a git repository: {project_dir} (no .git directory found)",
            "truncated": False
        }

    # Build command
    cmd = ["git", "diff"]
    if options:
        cmd.extend(options)

    # Run git diff
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False  # Explicit: never use shell=True
        )

        output = result.stdout
        truncated = False

        # Truncate if too large (>10KB)
        max_size = 10 * 1024
        if len(output) > max_size:
            output = output[:max_size] + "\n... [truncated] ..."
            truncated = True

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": output,
            "error": result.stderr,
            "truncated": truncated
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "exit_code": 124,
            "output": "",
            "error": "git diff timed out after 30 seconds",
            "truncated": False
        }
    except Exception as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"git diff failed: {str(e)}",
            "truncated": False
        }


def git_status(
    project_dir: str,
    short: bool = True
) -> Dict[str, Any]:
    """
    Show git status for the repository.

    REQUIRES: git to be installed and available on PATH
    REQUIRES: project_dir must be a git repository

    Args:
        project_dir: Path to the project directory (should be a git repo)
        short: Use short format (default: True)

    Returns:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str,
            "error": str
        }
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Project directory not found: {project_dir}"
        }

    # Check if git is installed (OS-agnostic availability check)
    if not shutil.which("git"):
        return {
            "status": "failed",
            "exit_code": 127,
            "output": "",
            "error": "git is not installed or not on PATH. Install git to use this tool."
        }

    # Check if .git exists
    git_dir = project_path / ".git"
    if not git_dir.exists():
        return {
            "status": "failed",
            "exit_code": 128,
            "output": "",
            "error": f"Not a git repository: {project_dir} (no .git directory found)"
        }

    # Build command
    cmd = ["git", "status"]
    if short:
        cmd.extend(["--short", "--branch"])

    # Run git status
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False  # Explicit: never use shell=True
        )

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "exit_code": 124,
            "output": "",
            "error": "git status timed out after 10 seconds"
        }
    except Exception as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"git status failed: {str(e)}"
        }


# ══════════════════════════════════════════════════════════════════════
# Internal / Private Functions (not exposed to agents)
# ══════════════════════════════════════════════════════════════════════


def _run_shell_internal(
    project_dir: str,
    command: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    INTERNAL ONLY: Run a shell command in the project directory.

    SECURITY WARNING: This function is intentionally NOT exposed in TOOL_REGISTRY
    to prevent command injection attacks in multi-agent environments.

    This function is kept for internal orchestrator use only (e.g., for trusted
    operations that require shell access). If you need to expose this to agents,
    you MUST implement command whitelisting and input sanitization.

    Args:
        project_dir: Path to the project directory
        command: Shell command to execute
        timeout: Timeout in seconds (default: 30)

    Returns:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str,
            "error": str
        }
    """
    project_path = Path(project_dir)

    if not project_path.exists():
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Project directory not found: {project_dir}"
        }

    # For internal use, we still use shell=True but with explicit warnings
    # A safer approach would be to use shlex.split() and shell=False
    try:
        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True  # WARNING: Command injection risk
        )

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "exit_code": 124,
            "output": "",
            "error": f"Command timed out after {timeout} seconds"
        }
    except Exception as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Command execution failed: {str(e)}"
        }


# ══════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════


def _parse_pytest_results(output: str) -> tuple[int, int, int]:
    """
    Parse pytest output to extract pass/fail/skip counts.

    Returns:
        (passed, failed, skipped)
    """
    import re

    passed = 0
    failed = 0
    skipped = 0

    # Look for pytest summary line like:
    # "5 passed, 2 failed, 1 skipped in 0.12s"
    # "3 passed in 0.05s"
    # "1 failed, 2 passed in 0.08s"

    match = re.search(r"(\d+)\s+passed", output)
    if match:
        passed = int(match.group(1))

    match = re.search(r"(\d+)\s+failed", output)
    if match:
        failed = int(match.group(1))

    match = re.search(r"(\d+)\s+skipped", output)
    if match:
        skipped = int(match.group(1))

    return passed, failed, skipped


# ══════════════════════════════════════════════════════════════════════
# Tool Registry
# ══════════════════════════════════════════════════════════════════════

# TOOL_REGISTRY: Central registry of tools available to agents
#
# Each tool entry contains:
# - func: The function to call
# - description: What the tool does (shown to agents in prompts)
# - category: Tool category for organization
# - parameters: Parameter descriptions (shown to agents)
#
# SECURITY NOTE: Only safe, sandboxed tools should be included here.
# Shell execution (run_shell) has been intentionally removed to prevent
# command injection attacks.

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "format_code": {
        "func": format_code,
        "description": "Format source code using ruff (default) or black formatter. Requires ruff/black to be installed.",
        "category": "code_quality",
        "parameters": {
            "project_dir": "Path to the project directory (required)",
            "formatter": "Formatter to use: 'ruff' (default) or 'black' (optional)",
            "paths": "Optional list of specific paths to format; defaults to entire project (optional)"
        }
    },
    "run_unit_tests": {
        "func": run_unit_tests,
        "description": "Run unit tests using pytest. Default test path: tests/unit. Requires pytest to be installed.",
        "category": "tests",
        "parameters": {
            "project_dir": "Path to the project directory (required)",
            "test_path": "Path to unit tests directory; default: 'tests/unit' (optional)",
            "extra_args": "Optional extra arguments for pytest, e.g. ['-v', '-k', 'test_name'] (optional)"
        }
    },
    "run_integration_tests": {
        "func": run_integration_tests,
        "description": "Run integration tests using pytest. Default test path: tests/integration. Requires pytest to be installed.",
        "category": "tests",
        "parameters": {
            "project_dir": "Path to the project directory (required)",
            "test_path": "Path to integration tests directory; default: 'tests/integration' (optional)",
            "extra_args": "Optional extra arguments for pytest, e.g. ['-v', '-k', 'test_name'] (optional)"
        }
    },
    "git_diff": {
        "func": git_diff,
        "description": "Show git diff for the repository. Requires git to be installed and project_dir to be a git repository.",
        "category": "git",
        "parameters": {
            "project_dir": "Path to the project directory (must be a git repo) (required)",
            "options": "Optional git diff options, e.g. ['--staged', '--stat'] (optional)"
        }
    },
    "git_status": {
        "func": git_status,
        "description": "Show git status for the repository. Requires git to be installed and project_dir to be a git repository.",
        "category": "git",
        "parameters": {
            "project_dir": "Path to the project directory (must be a git repo) (required)",
            "short": "Use short format; default: True (optional)"
        }
    }
    # NOTE: run_shell has been intentionally removed from the public tool registry
    # to prevent command injection attacks. It is available as _run_shell_internal()
    # for trusted internal use only.
}


def get_tool_metadata() -> List[Dict[str, Any]]:
    """
    Return a JSON-serializable list of tool metadata for LLM prompts.

    This function is used by the orchestrator to inject tool awareness into
    agent prompts, allowing them to request specific tools by name.

    Returns:
        [
            {
                "name": "format_code",
                "description": "...",
                "category": "code_quality",
                "parameters": {...}
            },
            ...
        ]
    """
    metadata = []

    for name, info in TOOL_REGISTRY.items():
        metadata.append({
            "name": name,
            "description": info["description"],
            "category": info["category"],
            "parameters": info.get("parameters", {})
        })

    return metadata


def call_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Call a tool by name with the given arguments.

    This is the main entry point for tool invocation. It validates that the
    tool exists in the registry and dispatches to the appropriate function.

    Args:
        tool_name: Name of the tool to call (must exist in TOOL_REGISTRY)
        **kwargs: Arguments to pass to the tool

    Returns:
        Tool result dict with structure:
        {
            "status": "success" | "failed",
            "exit_code": int,
            "output": str,
            "error": str,
            ...  # tool-specific fields
        }

        Or error dict if tool not found:
        {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": "Tool not found: ..."
        }
    """
    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Tool not found: {tool_name}. Available tools: {list(TOOL_REGISTRY.keys())}"
        }

    tool_func = TOOL_REGISTRY[tool_name]["func"]

    try:
        return tool_func(**kwargs)
    except TypeError as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Invalid arguments for tool '{tool_name}': {str(e)}"
        }
    except Exception as e:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Tool '{tool_name}' failed: {str(e)}"
        }
