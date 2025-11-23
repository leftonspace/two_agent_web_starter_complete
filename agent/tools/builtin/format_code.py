"""
PHASE 2.1: Code Formatting Tool Plugin

Migrated from exec_tools.py format_code() function.
Provides code formatting using ruff, black, or prettier.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
    create_error_result,
    create_success_result,
)


class FormatCodeTool(ToolPlugin):
    """
    Format source code using ruff, black, or prettier.

    Supports:
    - Python: ruff, black
    - JavaScript/TypeScript: prettier
    - Auto-detection based on file extensions
    """

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="format_code",
            version="2.1.0",
            description="Format source code files using ruff (Python), black (Python), or prettier (JavaScript/TypeScript)",
            domains=["coding"],
            roles=["manager", "supervisor", "employee"],
            required_permissions=["filesystem_write"],
            input_schema={
                "type": "object",
                "properties": {
                    "formatter": {
                        "type": "string",
                        "enum": ["ruff", "black", "prettier", "auto"],
                        "default": "auto",
                        "description": "Formatter to use ('auto' detects based on file types)"
                    },
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific files/directories to format (empty = format entire project)",
                        "default": []
                    },
                    "check_only": {
                        "type": "boolean",
                        "default": False,
                        "description": "Check formatting without making changes"
                    }
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "formatted": {"type": "boolean"},
                    "files_changed": {"type": "integer"},
                    "exit_code": {"type": "integer"},
                    "output": {"type": "string"},
                    "formatter_used": {"type": "string"}
                },
                "required": ["formatted", "exit_code"]
            },
            cost_estimate=0.0,
            timeout_seconds=60,
            requires_filesystem=True,
            examples=[
                {
                    "input": {
                        "formatter": "ruff",
                        "paths": [],
                        "check_only": False
                    },
                    "output": {
                        "formatted": True,
                        "files_changed": 5,
                        "exit_code": 0,
                        "formatter_used": "ruff"
                    }
                },
                {
                    "input": {
                        "formatter": "black",
                        "paths": ["main.py", "utils.py"],
                        "check_only": False
                    },
                    "output": {
                        "formatted": True,
                        "files_changed": 2,
                        "exit_code": 0,
                        "formatter_used": "black"
                    }
                }
            ],
            tags=["code", "formatting", "quality", "python", "javascript"],
            author="System",
            documentation_url="https://github.com/astral-sh/ruff"
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute code formatting"""
        formatter = params.get("formatter", "auto")
        paths = params.get("paths", [])
        check_only = params.get("check_only", False)

        # Auto-detect formatter if needed
        if formatter == "auto":
            formatter = self._detect_formatter(context.project_path, paths)

        # Check if formatter is installed
        if not shutil.which(formatter):
            return create_error_result(
                f"{formatter} is not installed or not on PATH. "
                f"Install with: pip install {formatter}",
                exit_code=127,
                formatter=formatter
            )

        # Build command
        cmd = self._build_command(formatter, paths, check_only)

        # Dry run mode
        if context.dry_run:
            return create_success_result(
                {
                    "formatted": True,
                    "files_changed": 0,
                    "exit_code": 0,
                    "output": f"DRY RUN: Would execute: {' '.join(cmd)}",
                    "formatter_used": formatter
                },
                dry_run=True
            )

        # Execute formatter
        try:
            manifest = self.get_manifest()
            result = subprocess.run(
                cmd,
                cwd=context.project_path,
                capture_output=True,
                text=True,
                timeout=manifest.timeout_seconds,
                shell=False
            )

            success = result.returncode == 0

            # Parse output for files changed (if possible)
            files_changed = self._count_files_changed(
                formatter,
                result.stdout,
                result.stderr
            )

            if success:
                return create_success_result(
                    {
                        "formatted": True,
                        "files_changed": files_changed,
                        "exit_code": result.returncode,
                        "output": result.stdout,
                        "formatter_used": formatter
                    },
                    formatter=formatter,
                    command=" ".join(cmd)
                )
            else:
                return create_error_result(
                    f"Formatting failed: {result.stderr}",
                    exit_code=result.returncode,
                    output=result.stdout,
                    formatter_used=formatter
                )

        except subprocess.TimeoutExpired:
            return create_error_result(
                f"Formatting timed out after {manifest.timeout_seconds} seconds",
                exit_code=124,
                formatter=formatter
            )
        except Exception as e:
            return create_error_result(
                f"Formatting failed: {str(e)}",
                exception_type=type(e).__name__,
                formatter=formatter
            )

    def _detect_formatter(
        self,
        project_path: Path,
        paths: List[str]
    ) -> str:
        """Auto-detect appropriate formatter based on file types"""
        # Check for Python files
        if paths:
            has_python = any(
                p.endswith(".py") for p in paths
            )
            has_js = any(
                p.endswith((".js", ".jsx", ".ts", ".tsx")) for p in paths
            )
        else:
            # Check project directory
            has_python = len(list(project_path.glob("**/*.py"))) > 0
            has_js = len(list(project_path.glob("**/*.{js,jsx,ts,tsx}"))) > 0

        # Prefer ruff for Python (faster than black)
        if has_python:
            return "ruff"
        elif has_js:
            return "prettier"
        else:
            # Default to ruff
            return "ruff"

    def _build_command(
        self,
        formatter: str,
        paths: List[str],
        check_only: bool
    ) -> List[str]:
        """Build the formatter command"""
        if formatter == "ruff":
            cmd = ["ruff", "format"]
            if check_only:
                cmd.append("--check")
            if paths:
                cmd.extend(paths)
            else:
                cmd.append(".")

        elif formatter == "black":
            cmd = ["black"]
            if check_only:
                cmd.append("--check")
            if paths:
                cmd.extend(paths)
            else:
                cmd.append(".")

        elif formatter == "prettier":
            cmd = ["prettier", "--write"]
            if check_only:
                cmd.remove("--write")
                cmd.append("--check")
            if paths:
                cmd.extend(paths)
            else:
                cmd.extend(["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"])

        else:
            raise ValueError(f"Unknown formatter: {formatter}")

        return cmd

    def _count_files_changed(
        self,
        formatter: str,
        stdout: str,
        stderr: str
    ) -> int:
        """Parse formatter output to count files changed"""
        # This is best-effort parsing - different formatters have different output formats
        try:
            if formatter == "ruff":
                # Ruff outputs "N files left unchanged" or "N files reformatted"
                if "reformatted" in stdout:
                    parts = stdout.split("reformatted")
                    if parts:
                        return int(parts[0].split()[-1])

            elif formatter == "black":
                # Black outputs "N files reformatted"
                if "reformatted" in stderr:
                    parts = stderr.split("reformatted")
                    if parts:
                        return int(parts[0].split()[-1])

            elif formatter == "prettier":
                # Prettier lists each file changed
                return stdout.count("\n")

        except (ValueError, IndexError, AttributeError):
            pass

        return 0  # Unknown
