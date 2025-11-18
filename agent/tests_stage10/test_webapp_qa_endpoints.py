"""
Tests for Stage 10 QA webapp API endpoints.

Tests the QA-specific web API endpoints that allow running QA checks
on jobs and retrieving QA reports.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))


@pytest.fixture
def client():
    """Create FastAPI test client."""
    from webapp.app import app

    return TestClient(app)


@pytest.fixture
def mock_job():
    """Create a mock completed job."""
    from jobs import Job
    from datetime import datetime

    return Job(
        id="test_job_123",
        status="completed",
        config={
            "project_subdir": "test_project",
            "mode": "3loop",
            "task": "Build a test site",
        },
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        logs_path="run_logs/test_job_123/job.log",
        result_summary={
            "run_id": "run_123",
            "final_status": "completed",
        },
    )


@pytest.fixture
def mock_qa_report():
    """Create a mock QA report."""
    return {
        "status": "passed",
        "summary": "All quality checks passed",
        "checks": {
            "html": {
                "has_title": True,
                "has_meta_description": True,
                "num_empty_links": 0,
            },
            "accessibility": {
                "total_images": 5,
                "images_missing_alt": 0,
            },
            "static": {
                "total_files": 10,
                "large_files": 0,
                "console_log_count": 2,
            },
        },
        "issues": [],
        "timestamp": "2024-01-01T10:00:00",
    }


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary test project directory."""
    project_dir = tmp_path / "sites" / "test_project"
    project_dir.mkdir(parents=True)

    # Create a simple HTML file
    index_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="description" content="Test project">
        <title>Test Project</title>
    </head>
    <body>
        <h1>Test Page</h1>
        <img src="image.jpg" alt="Test image">
    </body>
    </html>
    """
    (project_dir / "index.html").write_text(index_html)

    return project_dir


def test_api_run_job_qa_success(client, mock_job, mock_qa_report, temp_project, tmp_path):
    """Test POST /api/jobs/{job_id}/qa successfully runs QA checks."""
    from qa import QAReport

    # Mock QA report as dataclass
    qa_report_obj = MagicMock(spec=QAReport)
    qa_report_obj.to_dict.return_value = mock_qa_report

    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("webapp.app.run_qa_only", return_value=qa_report_obj) as mock_run_qa, \
         patch("webapp.app.agent_dir", tmp_path):

        mock_manager = MagicMock()
        mock_manager.get_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        response = client.post("/api/jobs/test_job_123/qa")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["summary"] == "All quality checks passed"
        assert "checks" in data

        # Verify QA was run
        assert mock_run_qa.called

        # Verify job was updated with QA results
        assert mock_manager.update_job.called
        update_call = mock_manager.update_job.call_args[1]
        assert "qa_status" in update_call
        assert update_call["qa_status"] == "passed"


def test_api_run_job_qa_job_not_found(client):
    """Test POST /api/jobs/{job_id}/qa with non-existent job."""
    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.get_job.return_value = None  # Job not found
        mock_get_manager.return_value = mock_manager

        response = client.post("/api/jobs/nonexistent_job/qa")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_api_run_job_qa_project_not_found(client, mock_job):
    """Test POST /api/jobs/{job_id}/qa when project directory doesn't exist."""
    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("webapp.app.run_qa_only") as mock_run_qa, \
         patch("webapp.app.agent_dir", Path("/tmp/nonexistent")):

        mock_manager = MagicMock()
        mock_manager.get_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        # run_qa_only will raise error for missing project
        mock_run_qa.side_effect = FileNotFoundError("Project not found")

        response = client.post("/api/jobs/test_job_123/qa")

        assert response.status_code == 404


def test_api_run_job_qa_handles_errors(client, mock_job):
    """Test POST /api/jobs/{job_id}/qa handles QA execution errors gracefully."""
    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("webapp.app.run_qa_only") as mock_run_qa:

        mock_manager = MagicMock()
        mock_manager.get_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        # Simulate QA error
        mock_run_qa.side_effect = Exception("QA execution failed")

        response = client.post("/api/jobs/test_job_123/qa")

        assert response.status_code == 500
        assert "error" in response.json()["detail"].lower()


def test_api_get_job_qa_with_report(client, mock_job, mock_qa_report):
    """Test GET /api/jobs/{job_id}/qa returns existing QA report."""
    # Add QA report to job
    mock_job.qa_status = "passed"
    mock_job.qa_summary = "All checks passed"
    mock_job.qa_report = mock_qa_report

    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.get_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/jobs/test_job_123/qa")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["summary"] == "All checks passed"


def test_api_get_job_qa_without_report(client, mock_job):
    """Test GET /api/jobs/{job_id}/qa when QA hasn't been run yet."""
    # Job has no QA report
    mock_job.qa_status = None
    mock_job.qa_summary = None
    mock_job.qa_report = None

    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.get_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/jobs/test_job_123/qa")

        assert response.status_code == 200
        data = response.json()
        # Should return null or empty structure
        assert data["qa_report"] is None or data["qa_report"] == {}


def test_api_get_job_qa_job_not_found(client):
    """Test GET /api/jobs/{job_id}/qa with non-existent job."""
    with patch("webapp.app.get_job_manager") as mock_get_manager:
        mock_manager = MagicMock()
        mock_manager.get_job.return_value = None
        mock_get_manager.return_value = mock_manager

        response = client.get("/api/jobs/nonexistent_job/qa")

        assert response.status_code == 404


def test_api_run_qa_updates_job_status(client, mock_job, mock_qa_report, temp_project, tmp_path):
    """Test that running QA updates the job's QA status fields."""
    from qa import QAReport

    qa_report_obj = MagicMock(spec=QAReport)
    qa_report_obj.to_dict.return_value = mock_qa_report

    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("webapp.app.run_qa_only", return_value=qa_report_obj), \
         patch("webapp.app.agent_dir", tmp_path):

        mock_manager = MagicMock()
        mock_manager.get_job.return_value = mock_job
        mock_get_manager.return_value = mock_manager

        response = client.post("/api/jobs/test_job_123/qa")

        assert response.status_code == 200

        # Verify job was updated with all QA fields
        update_call = mock_manager.update_job.call_args
        assert update_call[0][0] == "test_job_123"  # Job ID
        updates = update_call[1]
        assert "qa_status" in updates
        assert "qa_summary" in updates
        assert "qa_report" in updates
        assert updates["qa_status"] == "passed"
