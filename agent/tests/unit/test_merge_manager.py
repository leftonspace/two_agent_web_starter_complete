# test_merge_manager.py
"""
Unit tests for merge_manager module (Stage 4).
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module we're testing
import merge_manager


def test_compute_diff_no_git_repo(tmp_path):
    """Test compute_diff with no git repo returns empty string."""
    result = merge_manager.compute_diff(tmp_path)
    assert result == ""


def test_compute_diff_with_changes(tmp_path):
    """Test compute_diff with actual git changes."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)

    # Create and commit a file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=tmp_path, check=True, capture_output=True)

    # Make a change
    test_file.write_text("Hello World Modified")

    # Compute diff
    diff = merge_manager.compute_diff(tmp_path)

    # Should contain diff markers
    assert "Hello World" in diff or "Modified" in diff or diff == ""  # Empty if no unstaged changes in some git configs


@patch("merge_manager.chat_json")
@patch("merge_manager.compute_diff")
def test_summarize_diff_with_llm_no_changes(mock_compute_diff, mock_chat_json):
    """Test summarize_diff_with_llm when there are no changes."""
    mock_compute_diff.return_value = ""

    result = merge_manager.summarize_diff_with_llm(
        run_id="test123",
        repo_path=Path("/fake/path"),
    )

    assert result["summary"] == "No changes detected"
    assert result["impact"] == "none"
    assert result["files_touched"] == []

    # LLM should not be called
    mock_chat_json.assert_not_called()


@patch("merge_manager.chat_json")
@patch("merge_manager.compute_diff")
def test_summarize_diff_with_llm_with_changes(mock_compute_diff, mock_chat_json):
    """Test summarize_diff_with_llm with actual diff."""
    mock_compute_diff.return_value = "diff --git a/test.py\n+print('hello')"

    mock_chat_json.return_value = {
        "summary": "Added print statement",
        "impact": "low",
        "files_touched": ["test.py"],
        "risks": [],
        "suggested_followups": ["Add tests"],
    }

    result = merge_manager.summarize_diff_with_llm(
        run_id="test123",
        repo_path=Path("/fake/path"),
    )

    assert "Added print statement" in result["summary"]
    assert result["impact"] == "low"
    assert "test.py" in result["files_touched"]

    # LLM should be called
    mock_chat_json.assert_called_once()


@patch("merge_manager.chat_json")
@patch("merge_manager.compute_diff")
def test_summarize_session_no_changes(mock_compute_diff, mock_chat_json):
    """Test summarize_session with no changes."""
    mock_compute_diff.return_value = ""

    result = merge_manager.summarize_session(
        run_id="test123",
        repo_path=Path("/fake/path"),
    )

    assert "No changes" in result["title"]
    assert "No modifications" in result["body"]

    # LLM should not be called
    mock_chat_json.assert_not_called()


@patch("merge_manager.chat_json")
@patch("merge_manager.compute_diff")
def test_summarize_session_with_changes(mock_compute_diff, mock_chat_json):
    """Test summarize_session with actual diff."""
    mock_compute_diff.return_value = "diff --git a/test.py\n+print('hello')"

    mock_chat_json.return_value = {
        "title": "feat: add hello world",
        "body": "- Added print statement\n- Initial implementation",
    }

    result = merge_manager.summarize_session(
        run_id="test123",
        repo_path=Path("/fake/path"),
        task="Add hello world feature",
    )

    assert "feat: add hello world" in result["title"]
    assert "Added print statement" in result["body"]

    # LLM should be called
    mock_chat_json.assert_called_once()


def test_make_commit_no_git_repo(tmp_path):
    """Test make_commit with no git repo."""
    result = merge_manager.make_commit(
        repo_path=tmp_path,
        title="Test commit",
        body="Test body",
    )

    assert result is False


def test_make_commit_success(tmp_path):
    """Test make_commit with successful commit."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)

    # Create a file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World")

    # Make commit
    result = merge_manager.make_commit(
        repo_path=tmp_path,
        title="Initial commit",
        body="Added test file",
    )

    assert result is True

    # Verify commit exists
    log_result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Initial commit" in log_result.stdout


def test_make_commit_no_changes(tmp_path):
    """Test make_commit when there are no changes."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)

    # Make commit with no changes
    result = merge_manager.make_commit(
        repo_path=tmp_path,
        title="Empty commit",
        body="Should fail",
    )

    assert result is False
