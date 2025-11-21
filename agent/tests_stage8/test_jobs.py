"""
Tests for the jobs module.

STAGE 8: Tests job lifecycle and JobManager operations.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))


@pytest.fixture
def temp_state_file(tmp_path):
    """Temporary jobs state file."""
    return tmp_path / "jobs_state.json"


@pytest.fixture
def job_manager(temp_state_file):
    """Create a JobManager with temporary state file."""
    from jobs import JobManager

    return JobManager(state_file=temp_state_file)


@pytest.fixture
def sample_config():
    """Sample job configuration."""
    return {
        "mode": "3loop",
        "project_subdir": "test_project",
        "task": "Build a test website",
        "max_rounds": 2,
        "max_cost_usd": 1.0,
        "cost_warning_usd": 0.5,
        "use_visual_review": False,
        "use_git": False,
        "interactive_cost_mode": "off",
        "prompts_file": "prompts_default.json",
    }


def test_job_manager_init(job_manager, temp_state_file):
    """Test JobManager initialization."""
    assert job_manager.state_file == temp_state_file
    assert len(job_manager.jobs) == 0
    assert not temp_state_file.exists()


def test_create_job(job_manager, sample_config):
    """Test job creation."""
    job = job_manager.create_job(sample_config)

    assert job.id is not None
    assert len(job.id) == 12  # 12-char UUID
    assert job.status == "queued"
    assert job.config == sample_config
    assert job.created_at is not None
    assert job.updated_at is not None
    assert job.logs_path is not None
    assert job.result_summary is None
    assert not job.cancelled


def test_create_job_persists(job_manager, sample_config, temp_state_file):
    """Test that created jobs are persisted to disk."""
    job = job_manager.create_job(sample_config)

    assert temp_state_file.exists()

    # Load from file
    with open(temp_state_file, "r") as f:
        data = json.load(f)

    assert "jobs" in data
    assert len(data["jobs"]) == 1
    assert data["jobs"][0]["id"] == job.id


def test_get_job(job_manager, sample_config):
    """Test retrieving a job by ID."""
    job = job_manager.create_job(sample_config)

    retrieved = job_manager.get_job(job.id)
    assert retrieved is not None
    assert retrieved.id == job.id
    assert retrieved.config == sample_config


def test_get_job_not_found(job_manager):
    """Test retrieving non-existent job."""
    result = job_manager.get_job("nonexistent_id")
    assert result is None


def test_list_jobs_empty(job_manager):
    """Test listing jobs when none exist."""
    jobs = job_manager.list_jobs()
    assert jobs == []


def test_list_jobs(job_manager, sample_config):
    """Test listing multiple jobs."""
    job1 = job_manager.create_job(sample_config)
    time.sleep(0.01)  # Ensure different timestamps
    job2 = job_manager.create_job(sample_config)

    jobs = job_manager.list_jobs()
    assert len(jobs) == 2
    # Should be sorted by created_at (newest first)
    assert jobs[0].id == job2.id
    assert jobs[1].id == job1.id


def test_list_jobs_with_limit(job_manager, sample_config):
    """Test listing jobs with limit."""
    for _ in range(5):
        job_manager.create_job(sample_config)
        time.sleep(0.01)

    jobs = job_manager.list_jobs(limit=3)
    assert len(jobs) == 3


def test_list_jobs_with_status_filter(job_manager, sample_config):
    """Test listing jobs filtered by status."""
    job1 = job_manager.create_job(sample_config)
    job2 = job_manager.create_job(sample_config)

    # Update one job's status
    job_manager.update_job(job1.id, status="running")

    # Filter by running
    running_jobs = job_manager.list_jobs(status="running")
    assert len(running_jobs) == 1
    assert running_jobs[0].id == job1.id

    # Filter by queued
    queued_jobs = job_manager.list_jobs(status="queued")
    assert len(queued_jobs) == 1
    assert queued_jobs[0].id == job2.id


def test_update_job(job_manager, sample_config):
    """Test updating a job."""
    job = job_manager.create_job(sample_config)

    updated = job_manager.update_job(job.id, status="running", started_at="2024-01-01T10:00:00")

    assert updated is not None
    assert updated.status == "running"
    assert updated.started_at == "2024-01-01T10:00:00"
    assert updated.updated_at != job.updated_at  # Should be updated


def test_update_job_not_found(job_manager):
    """Test updating non-existent job."""
    result = job_manager.update_job("nonexistent_id", status="running")
    assert result is None


def test_cancel_job(job_manager, sample_config):
    """Test cancelling a job."""
    job = job_manager.create_job(sample_config)

    success = job_manager.cancel_job(job.id)
    assert success

    updated_job = job_manager.get_job(job.id)
    assert updated_job.cancelled


def test_cancel_running_job(job_manager, sample_config):
    """Test cancelling a running job."""
    job = job_manager.create_job(sample_config)
    job_manager.update_job(job.id, status="running")

    success = job_manager.cancel_job(job.id)
    assert success


def test_cancel_completed_job(job_manager, sample_config):
    """Test that completed jobs cannot be cancelled."""
    job = job_manager.create_job(sample_config)
    job_manager.update_job(job.id, status="completed")

    success = job_manager.cancel_job(job.id)
    assert not success


def test_cancel_job_not_found(job_manager):
    """Test cancelling non-existent job."""
    success = job_manager.cancel_job("nonexistent_id")
    assert not success


def test_get_job_logs_no_file(job_manager, sample_config):
    """Test getting logs when no log file exists."""
    job = job_manager.create_job(sample_config)

    logs = job_manager.get_job_logs(job.id)
    assert logs == ""


def test_get_job_logs_with_content(job_manager, sample_config, tmp_path):
    """Test getting logs with content."""
    job = job_manager.create_job(sample_config)

    # Create log file with content
    log_file = Path(job.logs_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("Line 1\nLine 2\nLine 3\n")

    logs = job_manager.get_job_logs(job.id)
    assert "Line 1" in logs
    assert "Line 2" in logs
    assert "Line 3" in logs


def test_get_job_logs_with_tail(job_manager, sample_config, tmp_path):
    """Test getting last N lines of logs."""
    job = job_manager.create_job(sample_config)

    # Create log file with content
    log_file = Path(job.logs_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

    logs = job_manager.get_job_logs(job.id, tail_lines=2)
    assert "Line 1" not in logs
    assert "Line 4" in logs
    assert "Line 5" in logs


@pytest.mark.skip(reason="Requires mocked run_project for full integration test")
def test_start_job_integration(job_manager, sample_config):
    """Test starting a job in background (integration test)."""
    # This would require mocking run_project and testing the full lifecycle
    # For now, we test the individual components
    pass


def test_job_manager_loads_existing_state(temp_state_file, sample_config):
    """Test that JobManager loads existing jobs from state file."""
    from jobs import JobManager

    # Create first manager and add a job
    manager1 = JobManager(state_file=temp_state_file)
    job = manager1.create_job(sample_config)

    # Create second manager - should load the existing job
    manager2 = JobManager(state_file=temp_state_file)
    assert len(manager2.jobs) == 1
    assert job.id in manager2.jobs
