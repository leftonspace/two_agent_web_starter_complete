"""
PHASE 7.5: Linter Component

Runs linting on code artifacts and calculates quality score.
Uses ruff for Python, eslint for JavaScript.

Usage:
    from core.evaluation.scoring_committee import Linter

    linter = Linter()
    score = await linter.run(task_result)  # 0.0 to 1.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..base import TaskResult


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Lint Result Models
# ============================================================================


class LintIssue(BaseModel):
    """A single lint issue."""
    file: str
    line: int
    column: int = 0
    code: str  # Rule code (e.g., "E501")
    message: str
    severity: str = "error"  # error, warning, info


class LintResult(BaseModel):
    """Result of linting."""
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    info: int = 0
    issues: List[LintIssue] = Field(default_factory=list)
    files_checked: int = 0
    output: str = ""
    error: Optional[str] = None

    @property
    def score(self) -> float:
        """
        Calculate 0-1 score from lint results.

        Scoring:
        - 0 errors = 1.0
        - 1-5 errors = 0.8
        - 6-10 errors = 0.6
        - 11-20 errors = 0.4
        - 20+ errors = 0.2
        """
        if self.errors == 0:
            return 1.0
        elif self.errors <= 5:
            return 0.8
        elif self.errors <= 10:
            return 0.6
        elif self.errors <= 20:
            return 0.4
        else:
            return 0.2


# ============================================================================
# Linter
# ============================================================================


class Linter:
    """
    Run linting on code artifacts.

    Detects language and uses appropriate linter:
    - Python: ruff (fast, modern) or flake8 (fallback)
    - JavaScript/TypeScript: eslint

    Usage:
        linter = Linter()
        score = await linter.run(task_result)
    """

    # Timeout for lint execution (seconds)
    DEFAULT_TIMEOUT = 30

    # File extensions by language
    PYTHON_EXTENSIONS = {".py"}
    JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        ruff_args: Optional[List[str]] = None,
    ):
        """
        Initialize the linter.

        Args:
            timeout: Maximum time for lint execution
            ruff_args: Additional ruff arguments
        """
        self._timeout = timeout
        self._ruff_args = ruff_args or ["--select=E,F,W"]

    async def run(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Run linting and return score.

        Args:
            result: Task result with artifacts to lint
            context: Additional context

        Returns:
            Score from 0.0 to 1.0
        """
        # Categorize files by language
        python_files = []
        js_files = []

        for artifact in result.artifacts:
            path = Path(artifact)
            suffix = path.suffix.lower()

            if suffix in self.PYTHON_EXTENSIONS:
                python_files.append(artifact)
            elif suffix in self.JS_EXTENSIONS:
                js_files.append(artifact)

        # Also check for inline code in response
        if not python_files and not js_files:
            if self._contains_python_code(result.response):
                return await self._lint_inline_python(result.response)
            # No lintable code
            return 1.0

        scores = []

        # Lint Python files
        if python_files:
            py_result = await self._lint_python(python_files, context)
            scores.append(py_result.score)
            logger.info(
                f"Python lint: {py_result.errors} errors, {py_result.warnings} warnings "
                f"(score={py_result.score:.2f})"
            )

        # Lint JS files
        if js_files:
            js_result = await self._lint_javascript(js_files, context)
            scores.append(js_result.score)
            logger.info(
                f"JS lint: {js_result.errors} errors, {js_result.warnings} warnings "
                f"(score={js_result.score:.2f})"
            )

        # Return average score
        if scores:
            return sum(scores) / len(scores)
        return 1.0

    def _contains_python_code(self, text: str) -> bool:
        """Check if text contains Python code."""
        patterns = [
            r"```python",
            r"def \w+\(",
            r"class \w+:",
        ]
        return any(re.search(p, text) for p in patterns)

    async def _lint_python(
        self,
        files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> LintResult:
        """Lint Python files with ruff."""
        # Try ruff first (faster and modern)
        result = await self._run_ruff(files, context)
        if result.error and "not found" in result.error.lower():
            # Fallback to flake8
            result = await self._run_flake8(files, context)
        return result

    async def _run_ruff(
        self,
        files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> LintResult:
        """Run ruff linter."""
        try:
            cmd = ["ruff", "check", "--output-format=json"] + self._ruff_args + files
            cwd = context.get("cwd") if context else None

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return LintResult(error="Ruff execution timed out")

            return self._parse_ruff_output(stdout.decode(), stderr.decode())

        except FileNotFoundError:
            return LintResult(error="ruff not found")
        except Exception as e:
            logger.error(f"Ruff execution failed: {e}")
            return LintResult(error=str(e))

    def _parse_ruff_output(self, stdout: str, stderr: str) -> LintResult:
        """Parse ruff JSON output."""
        result = LintResult(output=stdout)

        try:
            issues = json.loads(stdout) if stdout.strip() else []

            for issue in issues:
                lint_issue = LintIssue(
                    file=issue.get("filename", ""),
                    line=issue.get("location", {}).get("row", 0),
                    column=issue.get("location", {}).get("column", 0),
                    code=issue.get("code", ""),
                    message=issue.get("message", ""),
                    severity="error" if issue.get("code", "").startswith("E") else "warning",
                )
                result.issues.append(lint_issue)

                if lint_issue.severity == "error":
                    result.errors += 1
                else:
                    result.warnings += 1

            result.total_issues = len(issues)

        except json.JSONDecodeError:
            # Fallback: count lines in output
            result.errors = len(stdout.strip().split("\n")) if stdout.strip() else 0
            result.total_issues = result.errors

        return result

    async def _run_flake8(
        self,
        files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> LintResult:
        """Run flake8 linter (fallback)."""
        try:
            cmd = ["flake8", "--format=json"] + files
            cwd = context.get("cwd") if context else None

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return LintResult(error="Flake8 execution timed out")

            return self._parse_flake8_output(stdout.decode())

        except FileNotFoundError:
            return LintResult(error="flake8 not found")
        except Exception as e:
            return LintResult(error=str(e))

    def _parse_flake8_output(self, stdout: str) -> LintResult:
        """Parse flake8 output."""
        result = LintResult(output=stdout)

        # Parse line-by-line format: file:line:col: code message
        for line in stdout.strip().split("\n"):
            if not line:
                continue

            match = re.match(
                r"(.+):(\d+):(\d+): (\w+) (.+)",
                line,
            )
            if match:
                issue = LintIssue(
                    file=match.group(1),
                    line=int(match.group(2)),
                    column=int(match.group(3)),
                    code=match.group(4),
                    message=match.group(5),
                    severity="error" if match.group(4).startswith("E") else "warning",
                )
                result.issues.append(issue)

                if issue.severity == "error":
                    result.errors += 1
                else:
                    result.warnings += 1

        result.total_issues = len(result.issues)
        return result

    async def _lint_javascript(
        self,
        files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> LintResult:
        """Lint JavaScript/TypeScript files with eslint."""
        try:
            cmd = ["npx", "eslint", "--format=json"] + files
            cwd = context.get("cwd") if context else None

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return LintResult(error="ESLint execution timed out")

            return self._parse_eslint_output(stdout.decode())

        except FileNotFoundError:
            return LintResult(error="eslint not found")
        except Exception as e:
            return LintResult(error=str(e))

    def _parse_eslint_output(self, stdout: str) -> LintResult:
        """Parse eslint JSON output."""
        result = LintResult(output=stdout)

        try:
            reports = json.loads(stdout) if stdout.strip() else []

            for report in reports:
                for message in report.get("messages", []):
                    severity = "error" if message.get("severity") == 2 else "warning"
                    issue = LintIssue(
                        file=report.get("filePath", ""),
                        line=message.get("line", 0),
                        column=message.get("column", 0),
                        code=message.get("ruleId", ""),
                        message=message.get("message", ""),
                        severity=severity,
                    )
                    result.issues.append(issue)

                    if severity == "error":
                        result.errors += 1
                    else:
                        result.warnings += 1

            result.total_issues = len(result.issues)

        except json.JSONDecodeError:
            # Count errors from return code
            result.errors = 1 if stdout.strip() else 0

        return result

    async def _lint_inline_python(self, text: str) -> float:
        """Lint Python code embedded in text."""
        # Extract code blocks
        code_blocks = re.findall(
            r"```python\n(.*?)```",
            text,
            re.DOTALL,
        )

        if not code_blocks:
            return 1.0

        total_errors = 0

        for block in code_blocks:
            try:
                # Write to temp file
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    delete=False,
                ) as f:
                    f.write(block)
                    temp_path = f.name

                # Lint it
                result = await self._run_ruff([temp_path], None)
                total_errors += result.errors

                Path(temp_path).unlink(missing_ok=True)

            except Exception as e:
                logger.debug(f"Inline lint failed: {e}")

        # Calculate score based on total errors
        if total_errors == 0:
            return 1.0
        elif total_errors <= 5:
            return 0.8
        elif total_errors <= 10:
            return 0.6
        elif total_errors <= 20:
            return 0.4
        else:
            return 0.2
