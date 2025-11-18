# test_exec_tools.py
"""
Unit tests for exec_tools.py (Stage 2.1 - Tool Registry)

Tests cover:
- Tool availability checks (shutil.which() mocking)
- Tool invocation with missing executables
- Tool registry metadata generation
- Error handling for invalid inputs
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import exec_tools


class TestToolAvailability:
    """Test that tools check for executable availability before invocation."""

    def test_format_code_missing_ruff(self, tmp_path):
        """Test format_code when ruff is not installed."""
        with mock.patch("exec_tools.shutil.which", return_value=None):
            result = exec_tools.format_code(str(tmp_path), formatter="ruff")

            assert result["status"] == "failed"
            assert result["exit_code"] == 127
            assert "not installed" in result["error"].lower()
            assert "ruff" in result["error"]

    def test_format_code_missing_black(self, tmp_path):
        """Test format_code when black is not installed."""
        with mock.patch("exec_tools.shutil.which", return_value=None):
            result = exec_tools.format_code(str(tmp_path), formatter="black")

            assert result["status"] == "failed"
            assert result["exit_code"] == 127
            assert "not installed" in result["error"].lower()
            assert "black" in result["error"]

    def test_run_unit_tests_missing_pytest(self, tmp_path):
        """Test run_unit_tests when pytest is not installed."""
        with mock.patch("exec_tools.shutil.which", return_value=None):
            result = exec_tools.run_unit_tests(str(tmp_path))

            assert result["status"] == "failed"
            assert result["exit_code"] == 127
            assert "pytest" in result["error"].lower()
            assert result["passed"] == 0
            assert result["failed"] == 0
            assert result["skipped"] == 0

    def test_git_diff_missing_git(self, tmp_path):
        """Test git_diff when git is not installed."""
        # Create fake .git directory
        (tmp_path / ".git").mkdir()

        with mock.patch("exec_tools.shutil.which", return_value=None):
            result = exec_tools.git_diff(str(tmp_path))

            assert result["status"] == "failed"
            assert result["exit_code"] == 127
            assert "git" in result["error"].lower()
            assert "not installed" in result["error"].lower()

    def test_git_status_missing_git(self, tmp_path):
        """Test git_status when git is not installed."""
        # Create fake .git directory
        (tmp_path / ".git").mkdir()

        with mock.patch("exec_tools.shutil.which", return_value=None):
            result = exec_tools.git_status(str(tmp_path))

            assert result["status"] == "failed"
            assert result["exit_code"] == 127
            assert "git" in result["error"].lower()


class TestGitRepositoryChecks:
    """Test that git tools verify repository existence."""

    def test_git_diff_non_repo(self, tmp_path):
        """Test git_diff in a non-git directory."""
        result = exec_tools.git_diff(str(tmp_path))

        assert result["status"] == "failed"
        assert result["exit_code"] == 128
        assert "not a git repository" in result["error"].lower()

    def test_git_status_non_repo(self, tmp_path):
        """Test git_status in a non-git directory."""
        result = exec_tools.git_status(str(tmp_path))

        assert result["status"] == "failed"
        assert result["exit_code"] == 128
        assert "not a git repository" in result["error"].lower()


class TestInvalidInputs:
    """Test error handling for invalid inputs."""

    def test_format_code_nonexistent_directory(self):
        """Test format_code with a directory that doesn't exist."""
        result = exec_tools.format_code("/nonexistent/path/12345")

        assert result["status"] == "failed"
        assert result["exit_code"] == 1
        assert "not found" in result["error"].lower()

    def test_format_code_invalid_formatter(self, tmp_path):
        """Test format_code with an invalid formatter name."""
        result = exec_tools.format_code(str(tmp_path), formatter="invalid_formatter")

        assert result["status"] == "failed"
        assert result["exit_code"] == 1
        assert "unknown formatter" in result["error"].lower()

    def test_run_unit_tests_nonexistent_directory(self):
        """Test run_unit_tests with a directory that doesn't exist."""
        result = exec_tools.run_unit_tests("/nonexistent/path/12345")

        assert result["status"] == "failed"
        assert result["exit_code"] == 1
        assert "not found" in result["error"].lower()


class TestToolRegistry:
    """Test the tool registry and metadata generation."""

    def test_tool_registry_structure(self):
        """Test that TOOL_REGISTRY has expected structure."""
        assert "format_code" in exec_tools.TOOL_REGISTRY
        assert "run_unit_tests" in exec_tools.TOOL_REGISTRY
        assert "run_integration_tests" in exec_tools.TOOL_REGISTRY
        assert "git_diff" in exec_tools.TOOL_REGISTRY
        assert "git_status" in exec_tools.TOOL_REGISTRY

        # Verify run_shell is NOT in the registry (security hardening)
        assert "run_shell" not in exec_tools.TOOL_REGISTRY

    def test_tool_registry_entries(self):
        """Test that each tool entry has required fields."""
        for tool_name, tool_info in exec_tools.TOOL_REGISTRY.items():
            assert "func" in tool_info, f"{tool_name} missing 'func'"
            assert "description" in tool_info, f"{tool_name} missing 'description'"
            assert "category" in tool_info, f"{tool_name} missing 'category'"
            assert "parameters" in tool_info, f"{tool_name} missing 'parameters'"

            # Verify func is callable
            assert callable(tool_info["func"]), f"{tool_name} func is not callable"

    def test_get_tool_metadata(self):
        """Test get_tool_metadata returns proper structure."""
        metadata = exec_tools.get_tool_metadata()

        assert isinstance(metadata, list)
        assert len(metadata) > 0

        # Check first metadata entry structure
        entry = metadata[0]
        assert "name" in entry
        assert "description" in entry
        assert "category" in entry
        assert "parameters" in entry

    def test_tool_descriptions_clarity(self):
        """Test that tool descriptions mention requirements."""
        # run_unit_tests should mention default path
        unit_test_entry = exec_tools.TOOL_REGISTRY["run_unit_tests"]
        assert "tests/unit" in unit_test_entry["description"]

        # run_integration_tests should mention default path
        integration_test_entry = exec_tools.TOOL_REGISTRY["run_integration_tests"]
        assert "tests/integration" in integration_test_entry["description"]


class TestCallTool:
    """Test the call_tool dispatcher."""

    def test_call_tool_invalid_name(self):
        """Test call_tool with a tool that doesn't exist."""
        result = exec_tools.call_tool("nonexistent_tool")

        assert result["status"] == "failed"
        assert result["exit_code"] == 1
        assert "tool not found" in result["error"].lower()

    def test_call_tool_invalid_args(self):
        """Test call_tool with invalid arguments."""
        result = exec_tools.call_tool("format_code")  # Missing required project_dir

        assert result["status"] == "failed"
        assert result["exit_code"] == 1
        assert "invalid arguments" in result["error"].lower()


class TestRunShellSecurity:
    """Test that run_shell is properly secured."""

    def test_run_shell_not_in_registry(self):
        """Verify run_shell is NOT exposed in TOOL_REGISTRY."""
        assert "run_shell" not in exec_tools.TOOL_REGISTRY

    def test_run_shell_internal_exists(self):
        """Verify _run_shell_internal exists for internal use."""
        assert hasattr(exec_tools, "_run_shell_internal")
        assert callable(exec_tools._run_shell_internal)

    def test_run_shell_not_in_metadata(self):
        """Verify run_shell does not appear in tool metadata."""
        metadata = exec_tools.get_tool_metadata()
        tool_names = [entry["name"] for entry in metadata]

        assert "run_shell" not in tool_names
        assert "_run_shell_internal" not in tool_names


class TestParsePytestResults:
    """Test the pytest output parser."""

    def test_parse_basic_results(self):
        """Test parsing basic pytest output."""
        output = "5 passed, 2 failed, 1 skipped in 0.12s"
        passed, failed, skipped = exec_tools._parse_pytest_results(output)

        assert passed == 5
        assert failed == 2
        assert skipped == 1

    def test_parse_only_passed(self):
        """Test parsing output with only passed tests."""
        output = "10 passed in 0.05s"
        passed, failed, skipped = exec_tools._parse_pytest_results(output)

        assert passed == 10
        assert failed == 0
        assert skipped == 0

    def test_parse_no_results(self):
        """Test parsing output with no test results."""
        output = "No tests collected"
        passed, failed, skipped = exec_tools._parse_pytest_results(output)

        assert passed == 0
        assert failed == 0
        assert skipped == 0
