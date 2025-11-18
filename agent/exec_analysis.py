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
from typing import List, Dict, Any


# Severity levels for static analysis issues
# These map to the safety check failure criteria in exec_safety.py
SEVERITY_ERROR = "error"      # Blocking issues (syntax errors, undefined names)
SEVERITY_WARNING = "warning"  # Code quality issues (bare except, long functions)
SEVERITY_INFO = "info"        # Informational (TODOs, FIXMEs)


def analyze_project(project_dir: str) -> List[Dict[str, Any]]:
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
    issues: List[Dict[str, Any]] = []
    project_path = Path(project_dir)

    if not project_path.exists():
        return issues

    # Find all Python files
    py_files = list(project_path.rglob("*.py"))

    for py_file in py_files:
        # Skip files in hidden directories (like .git, .history, __pycache__)
        if any(part.startswith(".") or part == "__pycache__" for part in py_file.parts):
            continue

        rel_path = py_file.relative_to(project_path).as_posix()

        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception as e:
            issues.append({
                "file": rel_path,
                "line": 0,
                "message": f"Failed to read file: {e}",
                "severity": SEVERITY_WARNING
            })
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

            # STAGE 1 AUDIT FIX: Check for dangerous constructs
            dangerous_issues = _check_dangerous_constructs(rel_path, content)
            issues.extend(dangerous_issues)

        # Check for TODO/FIXME (syntax-independent)
        todo_issues = _check_todos(rel_path, content)
        issues.extend(todo_issues)

    return issues


def _check_syntax(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for Python syntax errors."""
    issues = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        issues.append({
            "file": file_path,
            "line": e.lineno or 0,
            "message": f"Syntax error: {e.msg}",
            "severity": SEVERITY_ERROR
        })
    except Exception as e:
        issues.append({
            "file": file_path,
            "line": 0,
            "message": f"Failed to parse file: {str(e)}",
            "severity": SEVERITY_ERROR
        })
    return issues


def _check_bare_excepts(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for bare except clauses (except: without exception type)."""
    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Look for "except:" (bare except)
        # Exclude "except Exception" or "except SomeError"
        stripped = line.strip()
        if re.match(r"^except\s*:", stripped):
            issues.append({
                "file": file_path,
                "line": line_num,
                "message": "Bare except clause found (consider specifying exception type)",
                "severity": SEVERITY_WARNING
            })

    return issues


def _check_long_functions(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for functions that are too long (>200 lines)."""
    issues = []

    try:
        tree = ast.parse(content)
    except Exception:
        # If we can't parse, skip this check
        return issues

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Calculate function length
            if hasattr(node, "end_lineno") and hasattr(node, "lineno"):
                func_length = node.end_lineno - node.lineno + 1
                if func_length > 200:
                    issues.append({
                        "file": file_path,
                        "line": node.lineno,
                        "message": f"Function '{node.name}' is very long ({func_length} lines, consider refactoring)",
                        "severity": SEVERITY_WARNING
                    })

    return issues


def _check_dangerous_constructs(file_path: str, content: str) -> List[Dict[str, Any]]:
    """
    Check for dangerous code patterns that could pose security risks.

    STAGE 1 AUDIT FIX: Detects risky functions and patterns.

    Checks for:
    - eval(), exec(), compile() - arbitrary code execution
    - os.system(), subprocess with shell=True - command injection risks
    - __import__() - dynamic imports can be exploited
    - open() with 'w' mode in loops - potential file overwrites

    Returns:
        List of issues with ERROR severity for dangerous patterns
    """
    issues = []
    lines = content.split("\n")

    # Patterns to detect (function_name, severity, message)
    dangerous_patterns = [
        (r"\beval\s*\(", SEVERITY_ERROR, "Use of eval() detected - arbitrary code execution risk"),
        (r"\bexec\s*\(", SEVERITY_ERROR, "Use of exec() detected - arbitrary code execution risk"),
        (r"\bcompile\s*\(", SEVERITY_WARNING, "Use of compile() detected - review for security implications"),
        (r"\b__import__\s*\(", SEVERITY_WARNING, "Dynamic import detected - review for security implications"),
        (r"os\.system\s*\(", SEVERITY_ERROR, "Use of os.system() detected - command injection risk"),
        (r"subprocess\.[^(]*\(.*shell\s*=\s*True", SEVERITY_ERROR, "subprocess with shell=True - command injection risk"),
        (r"pickle\.loads?\s*\(", SEVERITY_WARNING, "Use of pickle detected - can execute arbitrary code if data untrusted"),
    ]

    for line_num, line in enumerate(lines, start=1):
        # Skip comments
        if line.strip().startswith("#"):
            continue

        for pattern, severity, message in dangerous_patterns:
            if re.search(pattern, line):
                issues.append({
                    "file": file_path,
                    "line": line_num,
                    "message": message,
                    "severity": severity
                })

    return issues


def _check_todos(file_path: str, content: str) -> List[Dict[str, Any]]:
    """Check for TODO and FIXME comments."""
    issues = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, start=1):
        # Look for TODO or FIXME in comments
        if "TODO" in line or "FIXME" in line:
            # Extract the comment part
            comment_match = re.search(r"#\s*(TODO|FIXME).*", line, re.IGNORECASE)
            if comment_match:
                issues.append({
                    "file": file_path,
                    "line": line_num,
                    "message": f"Found {comment_match.group(1).upper()} comment: {comment_match.group(0)}",
                    "severity": SEVERITY_INFO
                })

    return issues
