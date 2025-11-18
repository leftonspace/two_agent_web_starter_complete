# exec_tools.py
"""
Centralized tool registry for the multi-agent orchestrator.

STAGE 2.1: Provides tools that agents can request, including:
- Code formatting (ruff/black)
- Unit and integration tests (pytest)
- Git operations (diff, status)
- Shell commands

All tools return structured results with status, exit_code, and output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


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

    # Build command
    if formatter == "ruff":
        cmd = ["ruff", "format"]
    elif formatter == "black":
        cmd = ["black"]
    else:
        return {
            "status": "failed",
            "exit_code": 1,
            "output": "",
            "error": f"Unknown formatter: {formatter}. Use 'ruff' or 'black'."
        }

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
            timeout=60
        )

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "exit_code": result.returncode,
            "output": result.stdout,
            "error": result.stderr
        }
    except FileNotFoundError:
        return {
            "status": "failed",
            "exit_code": 127,
            "output": "",
            "error": f"{formatter} not found. Install with: pip install {formatter}"
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

    # Check if tests exist
    test_dir = project_path / test_path
    if not test_dir.exists():
        # Try running pytest anyway (might have tests in default locations)
        test_dir = project_path

    # Build command
    cmd = ["pytest", "-v", "--tb=short"]
    if extra_args:
        cmd.extend(extra_args)

    # Add test path if it exists
    if (project_path / test_path).exists():
        cmd.append(test_path)

    # Run pytest
    try:
        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
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
    except FileNotFoundError:
        return {
            "status": "failed",
            "exit_code": 127,
            "output": "",
            "error": "pytest not found. Install with: pip install pytest",
            "passed": 0,
            "failed": 0,
            "skipped": 0
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

    # Check if .git exists
    git_dir = project_path / ".git"
    if not git_dir.exists():
        return {
            "status": "failed",
            "exit_code": 128,
            "output": "",
            "error": "Not a git repository",
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
            timeout=30
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

    # Check if .git exists
    git_dir = project_path / ".git"
    if not git_dir.exists():
        return {
            "status": "failed",
            "exit_code": 128,
            "output": "",
            "error": "Not a git repository"
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
            timeout=10
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


def run_shell(
    project_dir: str,
    command: str,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Run a shell command in the project directory.

    WARNING: Use with caution. Sanitize inputs to avoid command injection.

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

    # Run command
    try:
        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=True  # Note: shell=True is a security risk if command is user-controlled
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


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "format_code": {
        "func": format_code,
        "description": "Format source code using ruff or black formatter",
        "category": "code_quality",
        "parameters": {
            "project_dir": "Path to the project directory",
            "formatter": "Formatter to use: 'ruff' (default) or 'black'",
            "paths": "Optional list of specific paths to format"
        }
    },
    "run_unit_tests": {
        "func": run_unit_tests,
        "description": "Run unit tests using pytest",
        "category": "tests",
        "parameters": {
            "project_dir": "Path to the project directory",
            "test_path": "Path to unit tests directory (default: tests/unit)",
            "extra_args": "Optional extra arguments for pytest"
        }
    },
    "run_integration_tests": {
        "func": run_integration_tests,
        "description": "Run integration tests using pytest",
        "category": "tests",
        "parameters": {
            "project_dir": "Path to the project directory",
            "test_path": "Path to integration tests directory (default: tests/integration)",
            "extra_args": "Optional extra arguments for pytest"
        }
    },
    "git_diff": {
        "func": git_diff,
        "description": "Show git diff for the repository",
        "category": "git",
        "parameters": {
            "project_dir": "Path to the project directory",
            "options": "Optional git diff options (e.g., ['--staged', '--stat'])"
        }
    },
    "git_status": {
        "func": git_status,
        "description": "Show git status for the repository",
        "category": "git",
        "parameters": {
            "project_dir": "Path to the project directory",
            "short": "Use short format (default: True)"
        }
    },
    "run_shell": {
        "func": run_shell,
        "description": "Run a shell command in the project directory (use with caution)",
        "category": "shell",
        "parameters": {
            "project_dir": "Path to the project directory",
            "command": "Shell command to execute",
            "timeout": "Timeout in seconds (default: 30)"
        }
    }
}


def get_tool_metadata() -> List[Dict[str, Any]]:
    """
    Return a JSON-serializable list of tool metadata for LLM prompts.

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

    Args:
        tool_name: Name of the tool to call
        **kwargs: Arguments to pass to the tool

    Returns:
        Tool result dict, or error dict if tool not found
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
