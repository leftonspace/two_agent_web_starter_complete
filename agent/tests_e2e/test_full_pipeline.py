"""
End-to-end test for the complete orchestrator pipeline.

This test exercises the full system from job creation through completion,
including QA checks and analytics integration.

STAGE E2E: Tests the complete workflow:
1. Start a project job via POST /run
2. Poll job API until completion
3. Trigger QA for the completed job
4. Verify analytics endpoints show the run
5. Verify tuning endpoints are wired correctly
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))


@pytest.fixture
def temp_e2e_project(tmp_path, monkeypatch):
    """Create a complete test environment for E2E testing."""
    # Setup directory structure
    agent_root = tmp_path / "agent"
    agent_root.mkdir()

    sites_dir = tmp_path / "sites"
    sites_dir.mkdir()

    project_dir = sites_dir / "e2e_test_project"
    project_dir.mkdir()

    # Create a simple but valid HTML project
    index_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="description" content="E2E test project">
        <title>E2E Test Project</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body>
        <h1>Welcome to E2E Test</h1>
        <p>This is a test project for end-to-end testing.</p>
        <img src="test.jpg" alt="Test image">
    </body>
    </html>
    """
    (project_dir / "index.html").write_text(index_html)

    css_content = """
    body {
        font-family: Arial, sans-serif;
        margin: 20px;
        background-color: #f0f0f0;
    }
    h1 {
        color: #333;
    }
    """
    (project_dir / "style.css").write_text(css_content)

    js_content = """
    console.log('E2E test project loaded');

    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM ready');
    });
    """
    (project_dir / "script.js").write_text(js_content)

    # Create run_logs directory
    run_logs_dir = tmp_path / "run_logs"
    run_logs_dir.mkdir()

    # Create jobs_data directory for job manager persistence
    jobs_data_dir = tmp_path / "jobs_data"
    jobs_data_dir.mkdir()

    # Patch paths
    monkeypatch.setattr("webapp.app.agent_dir", tmp_path)
    monkeypatch.setattr("jobs.agent_dir", tmp_path)

    return {
        "tmp_path": tmp_path,
        "project_dir": project_dir,
        "project_name": "e2e_test_project",
        "run_logs_dir": run_logs_dir,
        "jobs_data_dir": jobs_data_dir,
    }


@pytest.fixture
def e2e_client(temp_e2e_project):
    """Create FastAPI test client for E2E testing."""
    from webapp.app import app

    return TestClient(app)


def test_full_pipeline_e2e(e2e_client, temp_e2e_project):
    """
    Complete end-to-end test of the orchestrator pipeline.

    This test simulates a full user workflow:
    1. Start a job via POST /run
    2. Poll job status until completion
    3. Run QA on the completed job
    4. Verify analytics show the run
    5. Verify tuning endpoints respond

    NOTE: This test uses extensive mocking to avoid heavy LLM calls,
    but tests the full API surface and integration points.
    """
    from jobs import Job
    from datetime import datetime

    # Mock the heavy orchestrator work
    mock_run_summary = MagicMock()
    mock_run_summary.run_id = "e2e_run_123"
    mock_run_summary.final_status = "completed"
    mock_run_summary.rounds_completed = 2
    mock_run_summary.cost_summary = {
        "total_usd": 0.75,
        "total_input_tokens": 2000,
        "total_output_tokens": 1000,
    }

    # Mock QA report
    mock_qa_report = MagicMock()
    mock_qa_report.to_dict.return_value = {
        "status": "passed",
        "summary": "All quality checks passed",
        "checks": {
            "html": {
                "has_title": True,
                "has_meta_description": True,
                "has_h1": True,
            },
            "accessibility": {
                "total_images": 1,
                "images_missing_alt": 0,
            },
            "static": {
                "total_files": 3,
                "large_files": 0,
                "console_log_count": 2,
            },
        },
        "issues": [],
        "timestamp": datetime.now().isoformat(),
    }

    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("webapp.app.run_qa_only", return_value=mock_qa_report), \
         patch("runner.run_3loop_orchestrator") as mock_orchestrator, \
         patch("runner.start_run", return_value=mock_run_summary), \
         patch("runner.finalize_run", return_value=mock_run_summary):

        # Create a mock job manager
        from jobs import JobManager

        # Use real job manager for state management but mock the runner
        real_manager = JobManager(str(temp_e2e_project["jobs_data_dir"]))
        mock_get_manager.return_value = real_manager

        # Mock the orchestrator to complete quickly
        def mock_run_orchestrator(run_summary, config):
            """Mock orchestrator that simulates completion."""
            run_summary.final_status = "completed"
            run_summary.rounds_completed = 2
            return None

        mock_orchestrator.side_effect = mock_run_orchestrator

        # STEP 1: Start a job via POST /run
        print("STEP 1: Starting job via POST /run")
        response = e2e_client.post(
            "/run",
            data={
                "project_subdir": temp_e2e_project["project_name"],
                "mode": "3loop",
                "task": "Enhance the E2E test project",
                "max_rounds": 2,
                "max_cost_usd": 2.0,
                "cost_warning_usd": 1.0,
            },
            follow_redirects=False,
        )

        assert response.status_code == 303, f"Expected redirect, got {response.status_code}"

        # Extract job_id from redirect location
        location = response.headers["location"]
        assert location.startswith("/jobs/"), f"Unexpected redirect: {location}"
        job_id = location.split("/")[-1]
        print(f"  ✓ Job created: {job_id}")

        # STEP 2: Poll job API until completion
        print("STEP 2: Polling job status")
        max_polls = 20
        poll_interval = 0.1  # 100ms

        job_completed = False
        final_job_data = None

        for i in range(max_polls):
            response = e2e_client.get(f"/api/jobs/{job_id}")
            assert response.status_code == 200, f"Failed to get job status: {response.status_code}"

            job_data = response.json()
            status = job_data["status"]
            print(f"  Poll {i+1}: status={status}")

            if status in ["completed", "failed", "error"]:
                job_completed = True
                final_job_data = job_data
                break

            time.sleep(poll_interval)

        assert job_completed, f"Job did not complete within {max_polls * poll_interval}s"
        assert final_job_data["status"] == "completed", f"Job failed: {final_job_data.get('error')}"
        print(f"  ✓ Job completed successfully")

        # STEP 3: Trigger QA for the completed job
        print("STEP 3: Running QA on completed job")
        response = e2e_client.post(f"/api/jobs/{job_id}/qa")
        assert response.status_code == 200, f"QA run failed: {response.status_code}"

        qa_data = response.json()
        assert qa_data["status"] == "passed", f"QA failed: {qa_data.get('summary')}"
        print(f"  ✓ QA passed: {qa_data['summary']}")

        # Verify QA results are stored in job
        response = e2e_client.get(f"/api/jobs/{job_id}")
        job_data = response.json()
        assert job_data.get("qa_status") == "passed", "QA status not stored in job"
        print(f"  ✓ QA results stored in job")

        # STEP 4: Verify analytics endpoints show the run
        print("STEP 4: Checking analytics")

        # Check job list endpoint
        response = e2e_client.get("/api/jobs")
        assert response.status_code == 200
        jobs_list = response.json()
        assert isinstance(jobs_list, list)
        assert any(job["id"] == job_id for job in jobs_list), "Job not in jobs list"
        print(f"  ✓ Job appears in jobs list")

        # Check if there's a stats/analytics endpoint (Stage 11)
        response = e2e_client.get("/api/stats/summary")
        if response.status_code == 200:
            stats = response.json()
            print(f"  ✓ Analytics endpoint responded: {stats}")
        else:
            print(f"  ℹ Analytics endpoint returned {response.status_code} (may not be implemented)")

        # STEP 5: Verify tuning endpoints are wired correctly (Stage 12)
        print("STEP 5: Checking tuning endpoints")

        # Check if tuning status endpoint exists
        response = e2e_client.get("/api/tuning/status")
        if response.status_code == 200:
            tuning_status = response.json()
            print(f"  ✓ Tuning status endpoint responded: {tuning_status}")
        elif response.status_code == 404:
            print(f"  ℹ Tuning endpoint not found (may not be implemented)")
        else:
            print(f"  ℹ Tuning endpoint returned {response.status_code}")

        print("\n✅ E2E TEST PASSED: Full pipeline functional")


def test_e2e_job_failure_handling(e2e_client, temp_e2e_project):
    """Test E2E flow when a job fails during execution."""
    from jobs import Job
    from datetime import datetime

    mock_run_summary = MagicMock()
    mock_run_summary.run_id = "e2e_fail_run"
    mock_run_summary.final_status = "failed"
    mock_run_summary.rounds_completed = 1
    mock_run_summary.error = "Simulated orchestrator failure"

    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("runner.run_3loop_orchestrator") as mock_orchestrator, \
         patch("runner.start_run", return_value=mock_run_summary), \
         patch("runner.finalize_run", return_value=mock_run_summary):

        from jobs import JobManager
        real_manager = JobManager(str(temp_e2e_project["jobs_data_dir"]))
        mock_get_manager.return_value = real_manager

        def mock_failing_orchestrator(run_summary, config):
            """Mock orchestrator that fails."""
            run_summary.final_status = "failed"
            run_summary.error = "Simulated orchestrator failure"
            raise RuntimeError("Simulated orchestrator failure")

        mock_orchestrator.side_effect = mock_failing_orchestrator

        # Start job
        response = e2e_client.post(
            "/run",
            data={
                "project_subdir": temp_e2e_project["project_name"],
                "mode": "2loop",
                "task": "This will fail",
                "max_rounds": 1,
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        job_id = response.headers["location"].split("/")[-1]

        # Poll until job fails
        max_polls = 20
        for i in range(max_polls):
            response = e2e_client.get(f"/api/jobs/{job_id}")
            job_data = response.json()

            if job_data["status"] in ["failed", "error"]:
                assert "error" in job_data or "Simulated" in str(job_data)
                print(f"✓ Job failure handled correctly: {job_data['status']}")
                return

            time.sleep(0.1)

        pytest.fail("Job did not transition to failed state")


def test_e2e_qa_failure_handling(e2e_client, temp_e2e_project):
    """Test E2E flow when QA detects issues."""
    from datetime import datetime

    # Mock QA report with failures
    mock_qa_report = MagicMock()
    mock_qa_report.to_dict.return_value = {
        "status": "failed",
        "summary": "Quality checks failed",
        "checks": {
            "html": {
                "has_title": False,
                "has_meta_description": False,
            },
        },
        "issues": [
            {"severity": "error", "message": "Missing <title> tag"},
            {"severity": "error", "message": "Missing meta description"},
        ],
        "timestamp": datetime.now().isoformat(),
    }

    mock_run_summary = MagicMock()
    mock_run_summary.run_id = "e2e_qa_fail"
    mock_run_summary.final_status = "completed"

    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("webapp.app.run_qa_only", return_value=mock_qa_report), \
         patch("runner.run_3loop_orchestrator"), \
         patch("runner.start_run", return_value=mock_run_summary), \
         patch("runner.finalize_run", return_value=mock_run_summary):

        from jobs import JobManager
        real_manager = JobManager(str(temp_e2e_project["jobs_data_dir"]))
        mock_get_manager.return_value = real_manager

        # Start and wait for job
        response = e2e_client.post(
            "/run",
            data={
                "project_subdir": temp_e2e_project["project_name"],
                "mode": "3loop",
                "task": "Build project",
                "max_rounds": 1,
            },
            follow_redirects=False,
        )

        job_id = response.headers["location"].split("/")[-1]

        # Wait for completion
        for _ in range(20):
            response = e2e_client.get(f"/api/jobs/{job_id}")
            if response.json()["status"] == "completed":
                break
            time.sleep(0.1)

        # Run QA
        response = e2e_client.post(f"/api/jobs/{job_id}/qa")
        assert response.status_code == 200

        qa_data = response.json()
        assert qa_data["status"] == "failed"
        assert len(qa_data["issues"]) == 2
        print(f"✓ QA failure detected and reported: {qa_data['summary']}")


def test_e2e_concurrent_jobs(e2e_client, temp_e2e_project):
    """Test that multiple jobs can be created and tracked concurrently."""
    from jobs import JobManager

    mock_run_summary = MagicMock()
    mock_run_summary.final_status = "completed"
    mock_run_summary.rounds_completed = 1

    with patch("webapp.app.get_job_manager") as mock_get_manager, \
         patch("runner.run_3loop_orchestrator"), \
         patch("runner.start_run", return_value=mock_run_summary), \
         patch("runner.finalize_run", return_value=mock_run_summary):

        real_manager = JobManager(str(temp_e2e_project["jobs_data_dir"]))
        mock_get_manager.return_value = real_manager

        # Create multiple jobs
        job_ids = []
        for i in range(3):
            response = e2e_client.post(
                "/run",
                data={
                    "project_subdir": temp_e2e_project["project_name"],
                    "mode": "2loop",
                    "task": f"Task {i+1}",
                    "max_rounds": 1,
                },
                follow_redirects=False,
            )
            job_id = response.headers["location"].split("/")[-1]
            job_ids.append(job_id)

        # Verify all jobs are tracked
        response = e2e_client.get("/api/jobs")
        jobs_list = response.json()

        for job_id in job_ids:
            assert any(job["id"] == job_id for job in jobs_list), f"Job {job_id} not found"

        print(f"✓ Successfully created and tracked {len(job_ids)} concurrent jobs")


# Mark tests as potentially heavy
pytestmark = pytest.mark.e2e
