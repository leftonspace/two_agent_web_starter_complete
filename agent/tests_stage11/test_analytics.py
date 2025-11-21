"""
Tests for analytics module functionality.

STAGE 11: Tests analytics aggregations, time-series, and exports.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))

import analytics  # noqa: E402


@pytest.fixture
def sample_runs():
    """Create sample run data for testing."""
    now = datetime.utcnow()

    runs = []

    # Create runs over the last 10 days
    for i in range(10):
        run_date = now - timedelta(days=i)
        run_date_str = run_date.isoformat() + "Z"
        finish_date = run_date + timedelta(minutes=5)
        finish_date_str = finish_date.isoformat() + "Z"

        run = {
            "run_id": f"run_{i}",
            "started_at": run_date_str,
            "finished_at": finish_date_str,
            "mode": "3loop" if i % 2 == 0 else "2loop",
            "project_dir": f"/sites/project_{i % 3}",  # 3 different projects
            "task": f"Task {i}",
            "max_rounds": 3,
            "rounds_completed": 2,
            "final_status": "COMPLETED",
            "models_used": {
                "manager": "gpt-5-mini",
                "supervisor": "gpt-5-nano",
                "employee": "gpt-5",
            },
            "cost_summary": {
                "total_cost_usd": 0.5 + i * 0.1,
                "by_role": {
                    "manager": {
                        "model": "gpt-5-mini",
                        "total_tokens": 1000 + i * 100,
                        "total_cost_usd": 0.1 + i * 0.01,
                    },
                    "supervisor": {
                        "model": "gpt-5-nano",
                        "total_tokens": 500 + i * 50,
                        "total_cost_usd": 0.05 + i * 0.005,
                    },
                    "employee": {
                        "model": "gpt-5",
                        "total_tokens": 2000 + i * 200,
                        "total_cost_usd": 0.35 + i * 0.035,
                    },
                },
            },
            "qa_status": ["passed", "warning", "failed", None][i % 4],
            "qa_summary": f"QA summary for run {i}",
        }

        runs.append(run)

    return runs


@pytest.fixture
def sample_jobs():
    """Create sample job data for testing."""
    jobs = [
        {
            "id": "job_1",
            "status": "completed",
            "created_at": "2024-01-01T10:00:00Z",
            "result_summary": {"run_id": "run_1"},
        },
        {
            "id": "job_2",
            "status": "completed",
            "created_at": "2024-01-02T10:00:00Z",
            "result_summary": {"run_id": "run_2"},
        },
        {
            "id": "job_3",
            "status": "failed",
            "created_at": "2024-01-03T10:00:00Z",
            "error": "Some error",
        },
        {
            "id": "job_4",
            "status": "running",
            "created_at": "2024-01-04T10:00:00Z",
        },
        {
            "id": "job_5",
            "status": "cancelled",
            "created_at": "2024-01-05T10:00:00Z",
        },
    ]

    return jobs


def test_compute_overall_summary(sample_runs, sample_jobs):
    """Test overall analytics summary computation."""
    summary = analytics.compute_overall_summary(sample_runs, sample_jobs)

    assert summary.total_runs == 10
    assert summary.total_jobs == 5
    assert summary.total_tokens > 0
    assert summary.total_cost > 0
    assert summary.avg_cost_per_run > 0
    assert summary.avg_duration_seconds > 0

    # Check job status counts
    assert summary.jobs_completed == 2
    assert summary.jobs_failed == 1
    assert summary.jobs_running == 1
    assert summary.jobs_cancelled == 1

    # Check mode breakdown
    assert summary.runs_2loop == 5
    assert summary.runs_3loop == 5


def test_compute_project_summaries(sample_runs):
    """Test per-project analytics computation."""
    project_summaries = analytics.compute_project_summaries(sample_runs)

    # Should have 3 unique projects
    assert len(project_summaries) == 3

    # Check structure
    for summary in project_summaries:
        assert summary.project_name
        assert summary.runs_count > 0
        assert summary.total_tokens > 0
        assert summary.total_cost > 0

    # Summaries should be sorted by runs_count descending
    for i in range(len(project_summaries) - 1):
        assert project_summaries[i].runs_count >= project_summaries[i + 1].runs_count


def test_compute_model_summaries(sample_runs):
    """Test per-model analytics computation."""
    model_summaries = analytics.compute_model_summaries(sample_runs)

    # Should have 3 models
    assert len(model_summaries) == 3

    model_names = {s.model_name for s in model_summaries}
    assert "gpt-5-mini" in model_names
    assert "gpt-5-nano" in model_names
    assert "gpt-5" in model_names

    # Check structure
    for summary in model_summaries:
        assert summary.total_tokens > 0
        assert summary.total_cost > 0
        assert summary.usage_count > 0

    # Summaries should be sorted by total_cost descending
    for i in range(len(model_summaries) - 1):
        assert model_summaries[i].total_cost >= model_summaries[i + 1].total_cost


def test_compute_timeseries(sample_runs):
    """Test time-series aggregation."""
    timeseries = analytics.compute_timeseries(sample_runs, days=30)

    # Should have 30 data points (one per day)
    assert len(timeseries) == 30

    # Points should be sorted by date
    for i in range(len(timeseries) - 1):
        assert timeseries[i].date <= timeseries[i + 1].date

    # Check that recent days have data
    recent_points = timeseries[-10:]
    total_runs = sum(p.runs for p in recent_points)
    assert total_runs == 10  # All 10 sample runs should be in the last 10 days


def test_compute_qa_summary(sample_runs):
    """Test QA analytics computation."""
    qa_summary = analytics.compute_qa_summary(sample_runs)

    # We have 10 runs with QA statuses cycling through passed/warning/failed/None
    assert qa_summary.total_qa_runs == 8  # 8 runs with QA status (not None)
    assert qa_summary.qa_passed == 3  # runs 0, 4, 8
    assert qa_summary.qa_warning == 3  # runs 1, 5, 9
    assert qa_summary.qa_failed == 2  # runs 2, 6
    assert qa_summary.qa_not_run == 2  # runs 3, 7

    # Pass rate should be passed / (passed + warning + failed)
    expected_pass_rate = 3 / 8
    assert abs(qa_summary.pass_rate - expected_pass_rate) < 0.01


def test_compute_current_month_cost(sample_runs):
    """Test current month cost calculation."""
    # All sample runs are recent (last 10 days), so should all be in current month
    cost = analytics.compute_current_month_cost(sample_runs)

    # Should be sum of all run costs
    expected_cost = sum(r["cost_summary"]["total_cost_usd"] for r in sample_runs)
    assert abs(cost - expected_cost) < 0.01


def test_export_analytics_json(sample_runs, sample_jobs):
    """Test JSON export."""
    summary = analytics.compute_overall_summary(sample_runs, sample_jobs)
    project_summaries = analytics.compute_project_summaries(sample_runs)
    model_summaries = analytics.compute_model_summaries(sample_runs)
    timeseries = analytics.compute_timeseries(sample_runs, days=30)

    json_str = analytics.export_analytics_json(
        summary, project_summaries, model_summaries, timeseries
    )

    # Should be valid JSON
    data = json.loads(json_str)

    assert "summary" in data
    assert "projects" in data
    assert "models" in data
    assert "timeseries" in data

    assert len(data["projects"]) == 3
    assert len(data["models"]) == 3
    assert len(data["timeseries"]) == 30


def test_export_analytics_csv(sample_runs, sample_jobs):
    """Test CSV export."""
    summary = analytics.compute_overall_summary(sample_runs, sample_jobs)
    project_summaries = analytics.compute_project_summaries(sample_runs)
    model_summaries = analytics.compute_model_summaries(sample_runs)

    csv_str = analytics.export_analytics_csv(
        summary, project_summaries, model_summaries
    )

    # Should contain expected sections
    assert "OVERALL SUMMARY" in csv_str
    assert "PER-PROJECT SUMMARY" in csv_str
    assert "PER-MODEL SUMMARY" in csv_str

    # Should contain metric names
    assert "Total Runs" in csv_str
    assert "Total Cost" in csv_str
    assert "gpt-5-mini" in csv_str or "gpt-5" in csv_str


def test_get_analytics(sample_runs, sample_jobs, monkeypatch):
    """Test main analytics API."""

    # Mock the load functions
    def mock_load_runs():
        return sample_runs

    def mock_load_jobs():
        return sample_jobs

    def mock_load_config():
        return {"enabled": True, "monthly_budget": 50.0, "timeseries_days": 30}

    monkeypatch.setattr(analytics, "load_all_runs", mock_load_runs)
    monkeypatch.setattr(analytics, "load_all_jobs", mock_load_jobs)
    monkeypatch.setattr(analytics, "load_analytics_config", mock_load_config)

    data = analytics.get_analytics()

    # Check all keys present
    assert "summary" in data
    assert "projects" in data
    assert "models" in data
    assert "timeseries" in data
    assert "qa" in data

    # Check data structure
    summary = data["summary"]
    assert summary["total_runs"] == 10
    assert summary["total_jobs"] == 5
    assert len(data["projects"]) == 3
    assert len(data["models"]) == 3


def test_analytics_config_defaults():
    """Test analytics config loading with defaults."""
    config = analytics.load_analytics_config()

    # Should return defaults if file doesn't exist or no analytics section
    assert "enabled" in config
    assert "monthly_budget" in config
    assert "timeseries_days" in config


def test_project_summary_dataclass():
    """Test ProjectSummary dataclass."""
    summary = analytics.ProjectSummary(
        project_name="test_project",
        runs_count=10,
        total_tokens=50000,
        total_cost=5.43,
    )

    assert summary.project_name == "test_project"
    assert summary.runs_count == 10
    assert summary.total_tokens == 50000
    assert summary.total_cost == 5.43


def test_model_summary_dataclass():
    """Test ModelSummary dataclass."""
    summary = analytics.ModelSummary(
        model_name="gpt-5",
        total_tokens=100000,
        total_cost=12.34,
        usage_count=25,
    )

    assert summary.model_name == "gpt-5"
    assert summary.total_tokens == 100000
    assert summary.total_cost == 12.34
    assert summary.usage_count == 25


def test_timeseries_point_dataclass():
    """Test TimeSeriesPoint dataclass."""
    point = analytics.TimeSeriesPoint(
        date="2024-01-15",
        runs=5,
        tokens=25000,
        cost=2.5,
        qa_passed=3,
        qa_warning=1,
        qa_failed=1,
    )

    assert point.date == "2024-01-15"
    assert point.runs == 5
    assert point.tokens == 25000
    assert point.cost == 2.5
    assert point.qa_passed == 3
    assert point.qa_warning == 1
    assert point.qa_failed == 1


def test_empty_runs_handling():
    """Test analytics with no runs."""
    summary = analytics.compute_overall_summary([], [])

    assert summary.total_runs == 0
    assert summary.total_tokens == 0
    assert summary.total_cost == 0.0
    assert summary.avg_cost_per_run == 0.0


def test_missing_fields_handling(sample_runs):
    """Test analytics with missing/incomplete data."""
    # Create runs with missing fields
    incomplete_runs = [
        {
            "run_id": "run_1",
            "started_at": "2024-01-01T10:00:00Z",
            # Missing finished_at, cost_summary, qa_status, etc.
        },
        {
            "run_id": "run_2",
            "started_at": "2024-01-02T10:00:00Z",
            "cost_summary": {},  # Empty cost summary
        },
    ]

    # Should not crash
    summary = analytics.compute_overall_summary(incomplete_runs, [])
    assert summary.total_runs == 2
    assert summary.total_cost == 0.0

    # Per-project should also handle missing data
    project_summaries = analytics.compute_project_summaries(incomplete_runs)
    assert len(project_summaries) >= 0
