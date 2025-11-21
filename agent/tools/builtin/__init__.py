"""
PHASE 2.1: Built-in Development Tools

This package contains built-in tools for software development tasks.
These tools are migrated from the legacy exec_tools.py module and
converted to the new plugin system.

Available Tools:
- format_code: Code formatting with ruff/black/prettier
- run_tests: Execute pytest unit and integration tests
- git_operations: Git diff and status
- sandbox_python: Execute Python code in sandbox

All tools in this directory are automatically discovered and registered
by the ToolRegistry at startup.
"""

__all__ = []
