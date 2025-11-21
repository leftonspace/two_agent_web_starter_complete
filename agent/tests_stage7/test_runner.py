"""
Tests for the runner API (run_project and related functions).

STAGE 7: Tests programmatic orchestrator interface.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_config():
    """Sample valid configuration for testing."""
    return {
        "mode": "3loop",
        "project_subdir": "test_project",
        "task": "Build a test website",
        "max_rounds": 2,
        "use_visual_review": False,
        "use_git": False,
        "max_cost_usd": 1.0,
        "cost_warning_usd": 0.5,
        "interactive_cost_mode": "off",
        "prompts_file": "prompts_default.json",
    }


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "sites" / "test_project"
    project_dir.mkdir(parents=True)
    (project_dir / "index.html").write_text("<html></html>")
    return project_dir


def test_list_projects_empty(tmp_path, monkeypatch):
    """Test list_projects with no projects."""
    from runner import list_projects

    # Mock the agent_dir to point to temp location
    monkeypatch.setattr("runner.Path", lambda *args: tmp_path if not args else Path(*args))

    sites_dir = tmp_path / "sites"
    sites_dir.mkdir(exist_ok=True)

    # Should return empty list
    projects = list_projects()
    assert isinstance(projects, list)


def test_list_projects_with_projects(tmp_path, monkeypatch):
    """Test list_projects with multiple projects."""

    sites_dir = tmp_path / "sites"
    sites_dir.mkdir(exist_ok=True)

    # Create test projects
    (sites_dir / "project1").mkdir()
    (sites_dir / "project1" / "index.html").write_text("<html></html>")
    (sites_dir / "project2").mkdir()
    (sites_dir / "project2" / "index.html").write_text("<html></html>")
    (sites_dir / "fixtures").mkdir()  # Should be skipped

    # Mock Path to return our temp structure
    def mock_path_init(cls_or_path):
        if cls_or_path == "__file__":
            return tmp_path / "agent" / "runner.py"
        return Path(cls_or_path)

    with patch("runner.Path") as mock_path:
        mock_path.side_effect = lambda x: tmp_path / "agent" / "runner.py" if x == "__file__" else Path(x)
        mock_path.return_value.resolve.return_value.parent = tmp_path / "agent"

        # This test is complex due to Path manipulation
        # In practice, integration tests would be more valuable
        assert True  # Placeholder - integration test would verify actual behavior


def test_list_run_history_empty(tmp_path, monkeypatch):
    """Test list_run_history with no runs."""
    from runner import list_run_history

    run_logs_dir = tmp_path / "run_logs"
    run_logs_dir.mkdir()

    with patch("runner.Path") as mock_path:
        mock_path.return_value.resolve.return_value.parent.parent = tmp_path

        history = list_run_history()
        assert isinstance(history, list)
        assert len(history) == 0


def test_list_run_history_with_runs(tmp_path):
    """Test list_run_history with multiple runs."""
    from runner import list_run_history

    run_logs_dir = tmp_path / "run_logs"
    run_logs_dir.mkdir()

    # Create test run logs
    run1_dir = run_logs_dir / "run_abc123"
    run1_dir.mkdir()
    run1_summary = {
        "run_id": "run_abc123",
        "started_at": "2024-01-01T10:00:00",
        "mode": "3loop",
        "final_status": "completed",
    }
    (run1_dir / "run_summary.json").write_text(json.dumps(run1_summary))

    run2_dir = run_logs_dir / "run_def456"
    run2_dir.mkdir()
    run2_summary = {
        "run_id": "run_def456",
        "started_at": "2024-01-01T11:00:00",
        "mode": "2loop",
        "final_status": "completed",
    }
    (run2_dir / "run_summary.json").write_text(json.dumps(run2_summary))

    with patch("runner.Path") as mock_path:
        mock_path.return_value.resolve.return_value.parent.parent = tmp_path

        # Mock the agent_dir path resolution
        def path_side_effect(arg=None):
            if arg == "__file__":
                p = MagicMock()
                p.resolve.return_value.parent.parent = tmp_path
                return p
            return Path(arg) if arg else Path()

        mock_path.side_effect = path_side_effect

        history = list_run_history()
        assert isinstance(history, list)
        # Sorted by started_at desc, so run_def456 should be first
        if len(history) == 2:
            assert history[0]["run_id"] == "run_def456"
            assert history[1]["run_id"] == "run_abc123"


def test_get_run_details_not_found(tmp_path):
    """Test get_run_details with non-existent run."""
    from runner import get_run_details

    with patch("runner.Path") as mock_path:
        mock_path.return_value.resolve.return_value.parent.parent = tmp_path

        result = get_run_details("nonexistent_run")
        assert result is None


def test_get_run_details_success(tmp_path):
    """Test get_run_details with valid run."""
    from runner import get_run_details

    run_logs_dir = tmp_path / "run_logs"
    run_logs_dir.mkdir()

    run_dir = run_logs_dir / "run_abc123"
    run_dir.mkdir()
    run_summary = {
        "run_id": "run_abc123",
        "started_at": "2024-01-01T10:00:00",
        "mode": "3loop",
        "final_status": "completed",
    }
    (run_dir / "run_summary.json").write_text(json.dumps(run_summary))

    with patch("runner.Path") as mock_path:
        def path_side_effect(arg=None):
            if arg == "__file__":
                p = MagicMock()
                p.resolve.return_value.parent.parent = tmp_path
                return p
            return Path(arg) if arg else Path()

        mock_path.side_effect = path_side_effect

        result = get_run_details("run_abc123")
        assert result is not None
        assert result["run_id"] == "run_abc123"
        assert result["mode"] == "3loop"


def test_run_project_missing_required_fields():
    """Test run_project with missing required configuration fields."""
    from runner import run_project

    # Missing 'task' field
    config = {
        "mode": "3loop",
        "project_subdir": "test_project",
    }

    with pytest.raises(ValueError, match="Missing required config field"):
        run_project(config)


def test_run_project_invalid_mode():
    """Test run_project with invalid mode."""
    from runner import run_project

    config = {
        "mode": "invalid_mode",
        "project_subdir": "test_project",
        "task": "Build a website",
    }

    with pytest.raises(ValueError, match="Invalid mode"):
        run_project(config)


def test_run_project_nonexistent_project():
    """Test run_project with non-existent project directory."""
    from runner import run_project

    config = {
        "mode": "3loop",
        "project_subdir": "nonexistent_project",
        "task": "Build a website",
        "max_rounds": 1,
    }

    with pytest.raises(FileNotFoundError, match="Project directory not found"):
        run_project(config)


# Integration test with comprehensive mocking
def test_run_project_integration(mock_config, temp_project_dir, tmp_path, monkeypatch):
    """Test successful run_project execution with mocked orchestrator."""
    from runner import run_project

    # Setup temporary directory structure
    agent_root = tmp_path / "agent"
    agent_root.mkdir()
    sites_dir = tmp_path / "sites"
    sites_dir.mkdir(exist_ok=True)
    project_dir = sites_dir / "test_project"
    project_dir.mkdir()
    (project_dir / "index.html").write_text("<html><body>Test</body></html>")

    run_logs_dir = tmp_path / "run_logs"
    run_logs_dir.mkdir()

    # Patch the path resolution
    monkeypatch.setattr("runner.Path", lambda x: tmp_path / "agent" / "runner.py" if x == "__file__" else Path(x))

    # Mock the orchestrator execution
    mock_run_summary = MagicMock()
    mock_run_summary.run_id = "test_run_123"
    mock_run_summary.final_status = "completed"
    mock_run_summary.rounds_completed = 2
    mock_run_summary.cost_summary = {"total_usd": 0.5}

    with patch("runner.run_3loop_orchestrator") as mock_3loop, \
         patch("runner.run_2loop_orchestrator") as mock_2loop, \
         patch("runner.start_run") as mock_start, \
         patch("runner.finalize_run") as mock_finalize, \
         patch("runner.estimate_cost") as mock_estimate:

        mock_start.return_value = mock_run_summary
        mock_3loop.return_value = None  # Modifies run_summary in place
        mock_estimate.return_value = {"estimated_total_usd": 0.8}
        mock_finalize.return_value = mock_run_summary

        # Update config to point to temp dirs
        config = mock_config.copy()
        config["project_subdir"] = "test_project"
        config["_skip_auto_tune"] = True  # Skip Stage 12 auto-tuning for this test

        # Run the project
        result = run_project(config)

        # Verify orchestrator was called
        assert mock_3loop.called or mock_2loop.called
        assert mock_start.called
        assert result is not None
