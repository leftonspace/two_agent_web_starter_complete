"""
Tests for the FastAPI web dashboard.

STAGE 7: Tests web interface routes and responses.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Skip all tests if FastAPI not installed
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from webapp.app import app

    return TestClient(app)


@pytest.fixture
def mock_projects():
    """Mock project list."""
    return [
        {"name": "project1", "path": "/sites/project1", "exists": True, "file_count": 5},
        {"name": "project2", "path": "/sites/project2", "exists": True, "file_count": 3},
    ]


@pytest.fixture
def mock_history():
    """Mock run history."""
    return [
        {
            "run_id": "run_abc123",
            "started_at": "2024-01-01T10:00:00",
            "finished_at": "2024-01-01T10:05:00",
            "mode": "3loop",
            "project_dir": "/sites/project1",
            "task": "Build a website",
            "max_rounds": 3,
            "rounds_completed": 2,
            "final_status": "completed",
            "cost_summary": {"total_usd": 0.25},
        },
        {
            "run_id": "run_def456",
            "started_at": "2024-01-01T11:00:00",
            "finished_at": "2024-01-01T11:03:00",
            "mode": "2loop",
            "project_dir": "/sites/project2",
            "task": "Create a landing page",
            "max_rounds": 2,
            "rounds_completed": 2,
            "final_status": "approved",
            "cost_summary": {"total_usd": 0.15},
        },
    ]


@pytest.fixture
def mock_run_detail():
    """Mock detailed run data."""
    return {
        "run_id": "run_abc123",
        "started_at": "2024-01-01T10:00:00",
        "finished_at": "2024-01-01T10:05:00",
        "mode": "3loop",
        "project_dir": "/sites/project1",
        "task": "Build a test website",
        "max_rounds": 3,
        "rounds_completed": 2,
        "final_status": "completed",
        "cost_summary": {
            "total_usd": 0.25,
            "total_input_tokens": 1000,
            "total_output_tokens": 500,
            "by_model": {
                "gpt-5-mini": {
                    "input_tokens": 1000,
                    "output_tokens": 500,
                    "cost_usd": 0.25,
                }
            },
        },
        "config": {
            "use_visual_review": False,
            "use_git": True,
        },
        "iterations": [
            {
                "index": 1,
                "role": "manager",
                "status": "ok",
                "notes": "Planning completed",
                "timestamp": "2024-01-01T10:01:00",
            },
            {
                "index": 2,
                "role": "manager",
                "status": "approved",
                "notes": "Iteration completed successfully",
                "timestamp": "2024-01-01T10:04:00",
                "safety_status": "passed",
            },
        ],
    }


def test_home_page(client, mock_projects, mock_history):
    """Test home page renders correctly."""
    with patch("webapp.app.list_projects", return_value=mock_projects), patch(
        "webapp.app.list_run_history", return_value=mock_history
    ):
        response = client.get("/")
        assert response.status_code == 200
        assert b"AI Dev Team Dashboard" in response.content
        assert b"project1" in response.content
        assert b"project2" in response.content


def test_start_run_missing_fields(client):
    """Test POST /run with missing required fields."""
    response = client.post(
        "/run",
        data={
            "project_subdir": "test_project",
            # Missing mode, task, max_rounds
        },
    )
    # FastAPI will return 422 for missing required fields
    assert response.status_code == 422


def test_start_run_invalid_project(client):
    """Test POST /run with non-existent project (Stage 8: job created but fails)."""
    from datetime import datetime

    from jobs import Job

    # Stage 8: Job is created successfully, but will fail in background
    mock_job = Job(
        id="job_fail_project",
        status="queued",
        config={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        logs_path="run_logs/job_fail_project/job.log"
    )

    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.create_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/run",
            data={
                "project_subdir": "nonexistent_project",
                "mode": "3loop",
                "task": "Build a website",
                "max_rounds": 2,
                "max_cost_usd": 1.0,
                "cost_warning_usd": 0.5,
            },
            follow_redirects=False,
        )
        # Stage 8: Job creation succeeds, returns redirect
        assert response.status_code == 303
        assert "/jobs/" in response.headers["location"]
        # Job will fail when background thread runs (tested in Stage 8 tests)


def test_start_run_invalid_config(client):
    """Test POST /run with invalid configuration (Stage 8: job created but fails)."""
    from datetime import datetime

    from jobs import Job

    # Stage 8: Job is created successfully, but will fail in background
    mock_job = Job(
        id="job_fail_config",
        status="queued",
        config={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        logs_path="run_logs/job_fail_config/job.log"
    )

    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.create_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/run",
            data={
                "project_subdir": "test_project",
                "mode": "invalid_mode",
                "task": "Build a website",
                "max_rounds": 2,
                "max_cost_usd": 1.0,
                "cost_warning_usd": 0.5,
            },
            follow_redirects=False,
        )
        # Stage 8: Job creation succeeds, returns redirect
        assert response.status_code == 303
        assert "/jobs/" in response.headers["location"]
        # Job will fail when background thread runs (tested in Stage 8 tests)


def test_start_run_success(client):
    """Test successful POST /run creates a background job (Stage 8 behavior)."""
    from datetime import datetime

    from jobs import Job

    # Mock job manager and job creation
    mock_job = Job(
        id="job_123",
        status="queued",
        config={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        logs_path="run_logs/job_123/job.log"
    )

    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.create_job.return_value = mock_job
        mock_manager.start_job.return_value = None
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/run",
            data={
                "project_subdir": "test_project",
                "mode": "3loop",
                "task": "Build a test website",
                "max_rounds": 2,
                "max_cost_usd": 1.0,
                "cost_warning_usd": 0.5,
            },
            follow_redirects=False,
        )
        # Stage 8: Should redirect to job detail page
        assert response.status_code == 303
        assert response.headers["location"] == "/jobs/job_123"

        # Verify job was created and started
        assert mock_manager.create_job.called
        assert mock_manager.start_job.called


def test_start_run_creates_job_in_manager(client):
    """Test that POST /run actually creates a job in the job manager."""
    from datetime import datetime

    from jobs import Job

    mock_job = Job(
        id="job_456",
        status="queued",
        config={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        logs_path="run_logs/job_456/job.log"
    )

    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.create_job.return_value = mock_job
        mock_manager.get_job.return_value = mock_job  # Job should be retrievable
        mock_get_manager.return_value = mock_manager

        response = client.post(
            "/run",
            data={
                "project_subdir": "test_project",
                "mode": "2loop",
                "task": "Create a landing page",
                "max_rounds": 3,
            },
            follow_redirects=False,
        )

        # Verify job was created with correct config
        assert mock_manager.create_job.called
        create_call_args = mock_manager.create_job.call_args
        config = create_call_args[0][0]  # First argument to create_job
        assert config["mode"] == "2loop"
        assert config["project_subdir"] == "test_project"
        assert config["task"] == "Create a landing page"

        # Verify job was started
        mock_manager.start_job.assert_called_once_with("job_456")

        # Verify redirect
        assert response.status_code == 303


def test_view_run_not_found(client):
    """Test GET /run/{run_id} with non-existent run."""
    with patch("webapp.app.get_run_details", return_value=None):
        response = client.get("/run/nonexistent_run")
        assert response.status_code == 404


def test_view_run_success(client, mock_run_detail):
    """Test GET /run/{run_id} with valid run."""
    with patch("webapp.app.get_run_details", return_value=mock_run_detail):
        response = client.get("/run/run_abc123")
        assert response.status_code == 200
        assert b"run_abc123" in response.content
        assert b"Build a test website" in response.content
        assert b"completed" in response.content


def test_api_list_projects(client, mock_projects):
    """Test GET /api/projects."""
    with patch("webapp.app.list_projects", return_value=mock_projects):
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "project1"


def test_api_list_history(client, mock_history):
    """Test GET /api/history."""
    with patch("webapp.app.list_run_history", return_value=mock_history):
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2


def test_api_list_history_with_limit(client, mock_history):
    """Test GET /api/history with limit parameter."""
    with patch("webapp.app.list_run_history", return_value=mock_history[:1]) as mock_list:
        response = client.get("/api/history?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        mock_list.assert_called_once_with(limit=1)


def test_api_get_run_not_found(client):
    """Test GET /api/run/{run_id} with non-existent run."""
    with patch("webapp.app.get_run_details", return_value=None):
        response = client.get("/api/run/nonexistent_run")
        assert response.status_code == 404


def test_api_get_run_success(client, mock_run_detail):
    """Test GET /api/run/{run_id} with valid run."""
    with patch("webapp.app.get_run_details", return_value=mock_run_detail):
        response = client.get("/api/run/run_abc123")
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run_abc123"
        assert data["mode"] == "3loop"


def test_health_check(client):
    """Test GET /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
