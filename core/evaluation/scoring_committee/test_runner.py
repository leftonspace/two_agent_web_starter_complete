"""
PHASE 7.5: Test Runner Component

Runs tests for code artifacts and calculates pass/fail score.
Uses pytest for Python, jest for JavaScript.

Usage:
    from core.evaluation.scoring_committee import TestRunner

    runner = TestRunner()
    score = await runner.run(task_result)  # 0.0 to 1.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ..base import TaskResult


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Test Result Models
# ============================================================================


class TestCaseResult(BaseModel):
    """Result of a single test case."""
    name: str
    passed: bool
    duration_ms: float = 0.0
    error_message: Optional[str] = None


class TestRunResult(BaseModel):
    """Result of a test run."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: float = 0.0
    test_cases: List[TestCaseResult] = Field(default_factory=list)
    output: str = ""
    error: Optional[str] = None

    @property
    def score(self) -> float:
        """Calculate 0-1 score from results."""
        if self.total == 0:
            return 1.0  # No tests = pass (nothing to fail)
        return self.passed / self.total


# ============================================================================
# Test Runner
# ============================================================================


class TestRunner:
    """
    Run tests for code artifacts.

    Detects test framework based on file types:
    - Python (.py): pytest
    - JavaScript (.js, .ts): jest (if available)

    Usage:
        runner = TestRunner()
        score = await runner.run(task_result)
    """

    # Timeout for test execution (seconds)
    DEFAULT_TIMEOUT = 60

    # File patterns that indicate tests
    TEST_PATTERNS = [
        r"test_.*\.py$",
        r".*_test\.py$",
        r".*\.test\.(js|ts)$",
        r".*\.spec\.(js|ts)$",
    ]

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        pytest_args: Optional[List[str]] = None,
    ):
        """
        Initialize the test runner.

        Args:
            timeout: Maximum time for test execution
            pytest_args: Additional pytest arguments
        """
        self._timeout = timeout
        self._pytest_args = pytest_args or ["-v", "--tb=short"]

    async def run(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Run tests and return score.

        Args:
            result: Task result with artifacts to test
            context: Additional context (e.g., test directory)

        Returns:
            Score from 0.0 to 1.0
        """
        # Find test files in artifacts
        test_files = self._find_test_files(result.artifacts)

        if not test_files:
            # Check if response contains testable code
            if self._contains_python_code(result.response):
                # Try to run inline tests if any
                return await self._run_inline_tests(result)
            # No tests to run
            logger.debug(f"No test files found for task {result.task_id}")
            return 1.0  # Pass by default if no tests

        # Determine test framework
        python_tests = [f for f in test_files if f.endswith(".py")]
        js_tests = [f for f in test_files if f.endswith((".js", ".ts"))]

        scores = []

        # Run Python tests
        if python_tests:
            py_result = await self._run_pytest(python_tests, context)
            scores.append(py_result.score)
            logger.info(
                f"Pytest: {py_result.passed}/{py_result.total} passed "
                f"(score={py_result.score:.2f})"
            )

        # Run JS tests
        if js_tests:
            js_result = await self._run_jest(js_tests, context)
            scores.append(js_result.score)
            logger.info(
                f"Jest: {js_result.passed}/{js_result.total} passed "
                f"(score={js_result.score:.2f})"
            )

        # Return average score across frameworks
        if scores:
            return sum(scores) / len(scores)
        return 1.0

    def _find_test_files(self, artifacts: List[str]) -> List[str]:
        """Find test files in artifacts."""
        test_files = []
        for artifact in artifacts:
            for pattern in self.TEST_PATTERNS:
                if re.search(pattern, artifact):
                    test_files.append(artifact)
                    break
        return test_files

    def _contains_python_code(self, response: str) -> bool:
        """Check if response contains Python code."""
        # Look for code blocks or function definitions
        patterns = [
            r"```python",
            r"def \w+\(",
            r"class \w+:",
            r"import \w+",
        ]
        return any(re.search(p, response) for p in patterns)

    async def _run_pytest(
        self,
        test_files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> TestRunResult:
        """Run pytest on test files."""
        try:
            # Build command
            cmd = ["python", "-m", "pytest"] + self._pytest_args

            # Add JSON output for parsing
            cmd.extend(["--json-report", "--json-report-file=-"])

            # Add test files
            cmd.extend(test_files)

            # Get working directory
            cwd = context.get("cwd") if context else None

            # Run pytest
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
                return TestRunResult(error="Test execution timed out")

            # Parse results
            return self._parse_pytest_output(
                stdout.decode(),
                stderr.decode(),
                process.returncode or 0,
            )

        except FileNotFoundError:
            logger.warning("pytest not found, trying basic execution")
            return await self._run_basic_python_tests(test_files, context)
        except Exception as e:
            logger.error(f"Pytest execution failed: {e}")
            return TestRunResult(error=str(e))

    def _parse_pytest_output(
        self,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> TestRunResult:
        """Parse pytest output."""
        result = TestRunResult(output=stdout)

        # Try to parse JSON report
        try:
            # Look for JSON in output
            json_match = re.search(r"\{.*\}", stdout, re.DOTALL)
            if json_match:
                report = json.loads(json_match.group())
                summary = report.get("summary", {})
                result.total = summary.get("total", 0)
                result.passed = summary.get("passed", 0)
                result.failed = summary.get("failed", 0)
                result.skipped = summary.get("skipped", 0)
                result.errors = summary.get("errors", 0)
                return result
        except (json.JSONDecodeError, AttributeError):
            pass

        # Fallback: parse text output
        # Look for "X passed, Y failed" pattern
        match = re.search(
            r"(\d+) passed.*?(\d+) failed",
            stdout,
            re.IGNORECASE,
        )
        if match:
            result.passed = int(match.group(1))
            result.failed = int(match.group(2))
            result.total = result.passed + result.failed
            return result

        # Look for just passed
        match = re.search(r"(\d+) passed", stdout, re.IGNORECASE)
        if match:
            result.passed = int(match.group(1))
            result.total = result.passed
            return result

        # Use return code as fallback
        if returncode == 0:
            result.total = 1
            result.passed = 1
        else:
            result.total = 1
            result.failed = 1
            result.error = stderr or "Tests failed"

        return result

    async def _run_jest(
        self,
        test_files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> TestRunResult:
        """Run jest on test files."""
        try:
            cmd = ["npx", "jest", "--json"] + test_files
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
                return TestRunResult(error="Jest execution timed out")

            return self._parse_jest_output(stdout.decode(), stderr.decode())

        except FileNotFoundError:
            logger.warning("jest not found")
            return TestRunResult(total=0, passed=0)
        except Exception as e:
            logger.error(f"Jest execution failed: {e}")
            return TestRunResult(error=str(e))

    def _parse_jest_output(self, stdout: str, stderr: str) -> TestRunResult:
        """Parse jest JSON output."""
        result = TestRunResult(output=stdout)

        try:
            report = json.loads(stdout)
            result.total = report.get("numTotalTests", 0)
            result.passed = report.get("numPassedTests", 0)
            result.failed = report.get("numFailedTests", 0)
        except json.JSONDecodeError:
            # Fallback parsing
            if "PASS" in stdout:
                result.total = 1
                result.passed = 1
            elif "FAIL" in stdout:
                result.total = 1
                result.failed = 1

        return result

    async def _run_basic_python_tests(
        self,
        test_files: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> TestRunResult:
        """Run Python test files directly (fallback)."""
        result = TestRunResult()

        for test_file in test_files:
            try:
                cmd = ["python", test_file]
                cwd = context.get("cwd") if context else None

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=cwd,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )

                result.total += 1
                if process.returncode == 0:
                    result.passed += 1
                else:
                    result.failed += 1

            except Exception as e:
                result.total += 1
                result.errors += 1
                logger.error(f"Failed to run {test_file}: {e}")

        return result

    async def _run_inline_tests(self, result: TaskResult) -> float:
        """Try to run tests embedded in the response."""
        # Extract code blocks
        code_blocks = re.findall(
            r"```python\n(.*?)```",
            result.response,
            re.DOTALL,
        )

        if not code_blocks:
            return 1.0  # No code to test

        # Check if any block contains test code
        test_blocks = [
            b for b in code_blocks
            if "def test_" in b or "assert " in b
        ]

        if not test_blocks:
            return 1.0  # No tests in code

        # Write to temp file and run
        passed = 0
        total = len(test_blocks)

        for block in test_blocks:
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    delete=False,
                ) as f:
                    f.write(block)
                    temp_path = f.name

                process = await asyncio.create_subprocess_exec(
                    "python",
                    temp_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                await asyncio.wait_for(
                    process.communicate(),
                    timeout=self._timeout,
                )

                if process.returncode == 0:
                    passed += 1

                Path(temp_path).unlink(missing_ok=True)

            except Exception as e:
                logger.debug(f"Inline test failed: {e}")

        return passed / total if total > 0 else 1.0
