"""
PHASE 2.1: Test Execution Tool Plugin

Migrated from exec_tools.py run_unit_tests() and run_integration_tests() functions.
Provides pytest test execution with detailed results.
"""

from __future__ import annotations

import re
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


class RunTestsTool(ToolPlugin):
    """
    Run tests using pytest.

    Supports:
    - Unit tests
    - Integration tests
    - Specific test paths or entire test suites
    - Detailed test result parsing
    """

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="run_tests",
            version="2.1.0",
            description="Run unit or integration tests using pytest with detailed results",
            domains=["coding"],
            roles=["manager", "supervisor", "employee"],
            required_permissions=["filesystem_read", "code_execute"],
            input_schema={
                "type": "object",
                "properties": {
                    "test_type": {
                        "type": "string",
                        "enum": ["unit", "integration", "all"],
                        "default": "unit",
                        "description": "Type of tests to run"
                    },
                    "test_path": {
                        "type": "string",
                        "description": "Specific test path (e.g., 'tests/unit/test_foo.py')",
                        "default": ""
                    },
                    "extra_args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional pytest arguments (e.g., ['-v', '-k', 'test_name'])",
                        "default": []
                    },
                    "verbose": {
                        "type": "boolean",
                        "default": False,
                        "description": "Run tests in verbose mode"
                    }
                },
                "required": []
            },
            output_schema={
                "type": "object",
                "properties": {
                    "passed": {"type": "integer"},
                    "failed": {"type": "integer"},
                    "skipped": {"type": "integer"},
                    "total": {"type": "integer"},
                    "success": {"type": "boolean"},
                    "exit_code": {"type": "integer"},
                    "output": {"type": "string"},
                    "duration_seconds": {"type": "number"}
                },
                "required": ["passed", "failed", "total", "success", "exit_code"]
            },
            cost_estimate=0.0,
            timeout_seconds=300,
            requires_filesystem=True,
            examples=[
                {
                    "input": {
                        "test_type": "unit",
                        "test_path": "",
                        "verbose": False
                    },
                    "output": {
                        "passed": 45,
                        "failed": 0,
                        "skipped": 2,
                        "total": 47,
                        "success": True,
                        "exit_code": 0,
                        "duration_seconds": 12.5
                    }
                },
                {
                    "input": {
                        "test_type": "unit",
                        "test_path": "tests/unit/test_model_registry.py",
                        "verbose": True
                    },
                    "output": {
                        "passed": 20,
                        "failed": 0,
                        "skipped": 0,
                        "total": 20,
                        "success": True,
                        "exit_code": 0,
                        "duration_seconds": 0.8
                    }
                }
            ],
            tags=["testing", "pytest", "quality", "ci"],
            author="System",
            documentation_url="https://docs.pytest.org/"
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute pytest tests"""
        test_type = params.get("test_type", "unit")
        test_path = params.get("test_path", "")
        extra_args = params.get("extra_args", [])
        verbose = params.get("verbose", False)

        # Check if pytest is installed
        if not shutil.which("pytest"):
            return create_error_result(
                "pytest is not installed or not on PATH. "
                "Install with: pip install pytest",
                exit_code=127
            )

        # Determine test path
        if not test_path:
            if test_type == "unit":
                test_path = "tests/unit"
            elif test_type == "integration":
                test_path = "tests/integration"
            elif test_type == "all":
                test_path = "tests"
            else:
                return create_error_result(
                    f"Unknown test_type: {test_type}",
                    valid_types=["unit", "integration", "all"]
                )

        # Check if test path exists
        full_test_path = context.project_path / test_path
        if not full_test_path.exists():
            return create_error_result(
                f"Test path not found: {test_path}",
                project_path=str(context.project_path),
                test_path=test_path
            )

        # Build pytest command
        cmd = ["pytest", test_path, "--tb=short"]
        if verbose:
            cmd.append("-v")
        cmd.extend(extra_args)

        # Dry run mode
        if context.dry_run:
            return create_success_result(
                {
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "total": 0,
                    "success": True,
                    "exit_code": 0,
                    "output": f"DRY RUN: Would execute: {' '.join(cmd)}",
                    "duration_seconds": 0.0
                },
                dry_run=True
            )

        # Execute pytest
        try:
            import time
            start_time = time.time()

            manifest = self.get_manifest()
            result = subprocess.run(
                cmd,
                cwd=context.project_path,
                capture_output=True,
                text=True,
                timeout=manifest.timeout_seconds,
                shell=False
            )

            duration = time.time() - start_time

            # Parse test results
            passed, failed, skipped = self._parse_pytest_results(result.stdout)
            total = passed + failed + skipped
            success = result.returncode == 0

            if success:
                return create_success_result(
                    {
                        "passed": passed,
                        "failed": failed,
                        "skipped": skipped,
                        "total": total,
                        "success": True,
                        "exit_code": result.returncode,
                        "output": result.stdout,
                        "duration_seconds": round(duration, 2)
                    },
                    test_type=test_type,
                    test_path=test_path,
                    command=" ".join(cmd)
                )
            else:
                return create_error_result(
                    f"Tests failed: {failed} failure(s)",
                    passed=passed,
                    failed=failed,
                    skipped=skipped,
                    total=total,
                    exit_code=result.returncode,
                    output=result.stdout,
                    duration_seconds=round(duration, 2)
                )

        except subprocess.TimeoutExpired:
            return create_error_result(
                f"Tests timed out after {manifest.timeout_seconds} seconds",
                exit_code=124,
                test_type=test_type
            )
        except Exception as e:
            return create_error_result(
                f"Test execution failed: {str(e)}",
                exception_type=type(e).__name__,
                test_type=test_type
            )

    def _parse_pytest_results(self, output: str) -> tuple[int, int, int]:
        """
        Parse pytest output to extract test counts.

        Returns:
            (passed, failed, skipped) tuple
        """
        passed = failed = skipped = 0

        # Look for pytest summary line
        # Examples:
        # "= 45 passed, 2 skipped in 12.5s ="
        # "= 20 passed in 0.8s ="
        # "= 5 failed, 40 passed in 10.2s ="

        # Try to find summary line
        summary_patterns = [
            r"(\d+) passed",
            r"(\d+) failed",
            r"(\d+) skipped",
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, output)
            if match:
                count = int(match.group(1))
                if "passed" in pattern:
                    passed = count
                elif "failed" in pattern:
                    failed = count
                elif "skipped" in pattern:
                    skipped = count

        return passed, failed, skipped
