# exec_analysis.py
"""
Static code analysis module for the multi-agent orchestrator.

Performs basic static analysis on Python files:
- Syntax error detection
- Bare except detection
- Very long functions (>200 lines)
- TODO/FIXME detection
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Dict, List

Issue = Dict[str, Any]


def analyze_project(project_dir: str | Path) -> List[Issue]:
    """
    Perform static analysis on all Python files in the project directory.

    Args:
        project_dir: Path to the project root directory

    Returns:
        List of issues found, each with:
        {
            "file": "relative/path/to/file.py",
            "line": line_number,
            "message": "description of the issue",
            "severity": "info" | "warning" | "error"
        }
    """
    issues: List[Issue] = []
    project_path = Path(project_dir)

    if not project_path.exists():
        return issues

    # Find all Python files
    py_files: List[Path] = list(project_path.rglob("*.py"))

    for py_file in py_files:
        # Skip files in hidden directories (like .git, .history, __pycache__)
        if any(part.startswith(".") or part == "__pycache__" for part in py_file.parts):
            continue

        rel_path = py_file.relative_to(project_path).as_posix()

        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception as e:
            issues.append(
                {
                    "file": rel_path,
                    "line": 0,
                    "message": f"Failed to read file: {e}",
                    "severity": "warning",
                }
            )
            continue

        # Check for syntax errors
        syntax_issues = _check_syntax(rel_path, content)
        issues.extend(syntax_issues)

        # Only continue with other checks if syntax is valid
        if not syntax_issues:
            # Check for bare excepts
            bare_except_issues = _check_bare_excepts(rel_path, content)
            issues.extend(bare_except_issues)

            # Check for very long functions
            long_func_issues = _check_long_functions(rel_path, content)
            issues.extend(long_func_issues)

        # Check for TODO/FIXME (syntax-independent)
        todo_issues = _check_todos(rel_path, content)
        issues.extend(todo_issues)

    return issues


def _check_syntax(file_path: str, content: str) -> List[Issue]:
    """Check for Python syntax errors."""
    issues: List[Issue] = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        issues.append(
            {
                "file": file_path,
                "line": e.lineno or 0,
                "message": f"Syntax error: {e.msg}",
                "severity": "error",
            }
        )
    except Exception as e:  # pragma: no cover - defensive
        issues.append(
            {
                "file": file_path,
                "line": 0,
                "message": f"Failed to parse file: {str(e)}",
                "severity": "error",
            }
        )
    return issues


def _check_bare_excepts(file_path: str, content: str) -> List[Issue]:
    """Check for bare except clauses (except: without exception type)."""
    issues: List[Issue] = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Look for "except:" (bare except), ignoring things like "except Exception:"
        if re.match(r"^except\s*:", stripped):
            issues.append(
                {
                    "file": file_path,
                    "line": line_num,
                    "message": "Bare except clause found (consider specifying exception type)",
                    "severity": "warning",
                }
            )

    return issues


def _check_long_functions(file_path: str, content: str) -> List[Issue]:
    """Check for functions that are too long (>200 lines)."""
    issues: List[Issue] = []

    try:
        tree = ast.parse(content)
    except Exception:
        # If we can't parse, skip this check (syntax handled elsewhere)
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = getattr(node, "lineno", None)
            end_line = getattr(node, "end_lineno", None)

            if isinstance(start_line, int) and isinstance(end_line, int):
                func_length = end_line - start_line + 1
                if func_length > 200:
                    issues.append(
                        {
                            "file": file_path,
                            "line": start_line,
                            "message": (
                                f"Function '{node.name}' is very long "
                                f"({func_length} lines, consider refactoring)"
                            ),
                            "severity": "warning",
                        }
                    )

    return issues


def _check_todos(file_path: str, content: str) -> List[Issue]:
    """Check for TODO and FIXME comments."""
    issues: List[Issue] = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        if "TODO" in line or "FIXME" in line:
            comment_match = re.search(r"#\s*(TODO|FIXME).*", line, re.IGNORECASE)
            if comment_match:
                issues.append(
                    {
                        "file": file_path,
                        "line": line_num,
                        "message": (
                            f"Found {comment_match.group(1).upper()} comment: "
                            f"{comment_match.group(0)}"
                        ),
                        "severity": "info",
                    }
                )

    return issues
