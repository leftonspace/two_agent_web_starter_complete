"""
Analytics and insights module for the multi-agent orchestrator.

Provides aggregated metrics, trends, and reports across all runs and jobs.

STAGE 11: Analytics & Insights Dashboard
"""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from safe_io import safe_timestamp


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class TimeSeriesPoint:
    """A single point in a time-series dataset."""

    date: str  # YYYY-MM-DD
    runs: int = 0
    tokens: int = 0
    cost: float = 0.0
    qa_passed: int = 0
    qa_warning: int = 0
    qa_failed: int = 0


@dataclass
class ProjectSummary:
    """Analytics summary for a single project."""

    project_name: str
    runs_count: int = 0
    last_run_time: Optional[str] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_duration_seconds: float = 0.0
    qa_passed: int = 0
    qa_warning: int = 0
    qa_failed: int = 0
    qa_not_run: int = 0


@dataclass
class ModelSummary:
    """Analytics summary for a single model."""

    model_name: str
    total_tokens: int = 0
    total_cost: float = 0.0
    usage_count: int = 0  # How many runs used this model


@dataclass
class QASummary:
    """Analytics summary for QA checks."""

    total_qa_runs: int = 0
    qa_passed: int = 0
    qa_warning: int = 0
    qa_failed: int = 0
    qa_error: int = 0
    qa_not_run: int = 0
    pass_rate: float = 0.0  # passed / (passed + warning + failed)


@dataclass
class AnalyticsSummary:
    """Complete analytics summary with all metrics."""

    # Overall metrics
    total_runs: int = 0
    total_jobs: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_cost_per_run: float = 0.0
    avg_duration_seconds: float = 0.0

    # Job statuses
    jobs_completed: int = 0
    jobs_failed: int = 0
    jobs_cancelled: int = 0
    jobs_running: int = 0
    jobs_queued: int = 0

    # Mode breakdown
    runs_2loop: int = 0
    runs_3loop: int = 0

    # QA metrics
    qa_summary: QASummary = field(default_factory=QASummary)

    # Budget tracking
    monthly_budget: Optional[float] = None
    current_month_cost: float = 0.0
    budget_remaining: Optional[float] = None

    # Timestamp
    generated_at: str = field(default_factory=safe_timestamp)


# ══════════════════════════════════════════════════════════════════════
# Data Loading
# ══════════════════════════════════════════════════════════════════════


def _get_project_root() -> Path:
    """Get the project root directory."""
    agent_dir = Path(__file__).resolve().parent
    return agent_dir.parent


def load_all_runs() -> List[Dict[str, Any]]:
    """
    Load all run summaries from run_logs directory.

    Returns:
        List of run summary dicts
    """
    project_root = _get_project_root()
    run_logs_dir = project_root / "run_logs"

    if not run_logs_dir.exists():
        return []

    runs = []

    for run_dir in run_logs_dir.iterdir():
        if not run_dir.is_dir():
            continue

        summary_file = run_dir / "run_summary.json"
        if not summary_file.exists():
            continue

        try:
            with summary_file.open("r", encoding="utf-8") as f:
                run_data = json.load(f)
                runs.append(run_data)
        except Exception:
            # Skip invalid/corrupted run logs
            continue

    return runs


def load_all_jobs() -> List[Dict[str, Any]]:
    """
    Load all jobs from jobs_state.json.

    Returns:
        List of job dicts
    """
    agent_dir = Path(__file__).resolve().parent
    jobs_file = agent_dir / "jobs_state.json"

    if not jobs_file.exists():
        return []

    try:
        with jobs_file.open("r", encoding="utf-8") as f:
            jobs_data = json.load(f)
            return jobs_data.get("jobs", [])
    except Exception:
        return []


def load_analytics_config() -> Dict[str, Any]:
    """
    Load analytics configuration from project_config.json.

    Returns:
        Analytics config dict with defaults
    """
    agent_dir = Path(__file__).resolve().parent
    config_file = agent_dir / "project_config.json"

    defaults = {
        "enabled": True,
        "monthly_budget": None,
        "timeseries_days": 30,
    }

    if not config_file.exists():
        return defaults

    try:
        with config_file.open("r", encoding="utf-8") as f:
            config = json.load(f)
            analytics_config = config.get("analytics", {})
            return {**defaults, **analytics_config}
    except Exception:
        return defaults


# ══════════════════════════════════════════════════════════════════════
# Aggregation Functions
# ══════════════════════════════════════════════════════════════════════


def compute_overall_summary(
    runs: List[Dict[str, Any]],
    jobs: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> AnalyticsSummary:
    """
    Compute overall analytics summary.

    Args:
        runs: List of run summary dicts
        jobs: List of job dicts
        config: Analytics configuration

    Returns:
        AnalyticsSummary with aggregated metrics
    """
    if config is None:
        config = load_analytics_config()

    summary = AnalyticsSummary()
    summary.total_runs = len(runs)
    summary.total_jobs = len(jobs)

    # Aggregate tokens and costs
    total_tokens = 0
    total_cost = 0.0
    total_duration = 0.0
    run_count_with_duration = 0
    runs_2loop = 0
    runs_3loop = 0

    for run in runs:
        # Cost summary
        cost_summary = run.get("cost_summary", {})
        run_cost = cost_summary.get("total_cost_usd", 0.0)
        total_cost += run_cost

        # Tokens (sum across all roles)
        for role_data in cost_summary.get("by_role", {}).values():
            total_tokens += role_data.get("total_tokens", 0)

        # Duration
        started_at = run.get("started_at")
        finished_at = run.get("finished_at")
        if started_at and finished_at:
            try:
                start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                duration = (end - start).total_seconds()
                total_duration += duration
                run_count_with_duration += 1
            except Exception:
                pass

        # Mode
        mode = run.get("mode", "").lower()
        if mode == "2loop":
            runs_2loop += 1
        elif mode == "3loop":
            runs_3loop += 1

    summary.total_tokens = total_tokens
    summary.total_cost = total_cost
    summary.avg_cost_per_run = total_cost / len(runs) if runs else 0.0
    summary.avg_duration_seconds = (
        total_duration / run_count_with_duration if run_count_with_duration else 0.0
    )
    summary.runs_2loop = runs_2loop
    summary.runs_3loop = runs_3loop

    # Job statuses
    job_status_counts = defaultdict(int)
    for job in jobs:
        status = job.get("status", "unknown")
        job_status_counts[status] += 1

    summary.jobs_completed = job_status_counts.get("completed", 0)
    summary.jobs_failed = job_status_counts.get("failed", 0)
    summary.jobs_cancelled = job_status_counts.get("cancelled", 0)
    summary.jobs_running = job_status_counts.get("running", 0)
    summary.jobs_queued = job_status_counts.get("queued", 0)

    # QA summary
    summary.qa_summary = compute_qa_summary(runs)

    # Budget tracking
    monthly_budget = config.get("monthly_budget")
    if monthly_budget is not None:
        summary.monthly_budget = monthly_budget
        summary.current_month_cost = compute_current_month_cost(runs)
        summary.budget_remaining = monthly_budget - summary.current_month_cost

    return summary


def compute_project_summaries(runs: List[Dict[str, Any]]) -> List[ProjectSummary]:
    """
    Compute per-project analytics summaries.

    Args:
        runs: List of run summary dicts

    Returns:
        List of ProjectSummary objects, sorted by runs_count descending
    """
    # Group runs by project
    project_data: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for run in runs:
        project_dir = run.get("project_dir", "")
        # Extract project name from path (last component)
        project_name = Path(project_dir).name if project_dir else "unknown"
        project_data[project_name].append(run)

    # Compute summaries
    summaries = []

    for project_name, project_runs in project_data.items():
        summary = ProjectSummary(project_name=project_name)
        summary.runs_count = len(project_runs)

        # Last run time
        run_times = [r.get("started_at") for r in project_runs if r.get("started_at")]
        if run_times:
            summary.last_run_time = max(run_times)

        # Total tokens and cost
        total_tokens = 0
        total_cost = 0.0
        total_duration = 0.0
        duration_count = 0

        qa_counts = {"passed": 0, "warning": 0, "failed": 0, "not_run": 0}

        for run in project_runs:
            # Cost and tokens
            cost_summary = run.get("cost_summary", {})
            total_cost += cost_summary.get("total_cost_usd", 0.0)

            for role_data in cost_summary.get("by_role", {}).values():
                total_tokens += role_data.get("total_tokens", 0)

            # Duration
            started_at = run.get("started_at")
            finished_at = run.get("finished_at")
            if started_at and finished_at:
                try:
                    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                    duration = (end - start).total_seconds()
                    total_duration += duration
                    duration_count += 1
                except Exception:
                    pass

            # QA status
            qa_status = run.get("qa_status")
            if qa_status in qa_counts:
                qa_counts[qa_status] += 1
            elif qa_status is None:
                qa_counts["not_run"] += 1

        summary.total_tokens = total_tokens
        summary.total_cost = total_cost
        summary.avg_duration_seconds = total_duration / duration_count if duration_count else 0.0
        summary.qa_passed = qa_counts["passed"]
        summary.qa_warning = qa_counts["warning"]
        summary.qa_failed = qa_counts["failed"]
        summary.qa_not_run = qa_counts["not_run"]

        summaries.append(summary)

    # Sort by runs count descending
    summaries.sort(key=lambda s: s.runs_count, reverse=True)

    return summaries


def compute_model_summaries(runs: List[Dict[str, Any]]) -> List[ModelSummary]:
    """
    Compute per-model analytics summaries.

    Args:
        runs: List of run summary dicts

    Returns:
        List of ModelSummary objects, sorted by total_cost descending
    """
    # Aggregate by model
    model_data: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"tokens": 0, "cost": 0.0, "usage_count": 0}
    )

    for run in runs:
        cost_summary = run.get("cost_summary", {})
        by_role = cost_summary.get("by_role", {})

        # Track which models were used in this run
        used_models = set()

        for role, role_data in by_role.items():
            # Extract model name from cost_summary if available
            # Otherwise fall back to models_used
            model = None

            # Try to get model from cost summary
            if "model" in role_data:
                model = role_data["model"]
            else:
                # Fall back to models_used
                models_used = run.get("models_used", {})
                model = models_used.get(role)

            if not model:
                model = f"{role}_unknown"

            tokens = role_data.get("total_tokens", 0)
            cost = role_data.get("total_cost_usd", 0.0)

            model_data[model]["tokens"] += tokens
            model_data[model]["cost"] += cost

            used_models.add(model)

        # Increment usage count for all models used in this run
        for model in used_models:
            model_data[model]["usage_count"] += 1

    # Create summaries
    summaries = []
    for model_name, data in model_data.items():
        summary = ModelSummary(
            model_name=model_name,
            total_tokens=data["tokens"],
            total_cost=data["cost"],
            usage_count=data["usage_count"],
        )
        summaries.append(summary)

    # Sort by total cost descending
    summaries.sort(key=lambda s: s.total_cost, reverse=True)

    return summaries


def compute_timeseries(
    runs: List[Dict[str, Any]], days: int = 30
) -> List[TimeSeriesPoint]:
    """
    Compute daily time-series aggregates.

    Args:
        runs: List of run summary dicts
        days: Number of days to include (default 30)

    Returns:
        List of TimeSeriesPoint objects, sorted by date ascending
    """
    # Create date buckets for the last N days
    today = datetime.utcnow().date()
    date_buckets: Dict[str, TimeSeriesPoint] = {}

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.isoformat()
        date_buckets[date_str] = TimeSeriesPoint(date=date_str)

    # Aggregate runs into buckets
    for run in runs:
        started_at = run.get("started_at")
        if not started_at:
            continue

        try:
            # Parse timestamp and extract date
            run_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            run_date = run_dt.date().isoformat()

            # Only include if within our time window
            if run_date not in date_buckets:
                continue

            bucket = date_buckets[run_date]
            bucket.runs += 1

            # Tokens and cost
            cost_summary = run.get("cost_summary", {})
            bucket.cost += cost_summary.get("total_cost_usd", 0.0)

            for role_data in cost_summary.get("by_role", {}).values():
                bucket.tokens += role_data.get("total_tokens", 0)

            # QA status
            qa_status = run.get("qa_status")
            if qa_status == "passed":
                bucket.qa_passed += 1
            elif qa_status == "warning":
                bucket.qa_warning += 1
            elif qa_status == "failed":
                bucket.qa_failed += 1

        except Exception:
            continue

    # Convert to sorted list
    points = list(date_buckets.values())
    points.sort(key=lambda p: p.date)

    return points


def compute_qa_summary(runs: List[Dict[str, Any]]) -> QASummary:
    """
    Compute QA analytics summary.

    Args:
        runs: List of run summary dicts

    Returns:
        QASummary with QA metrics
    """
    summary = QASummary()

    qa_counts = defaultdict(int)

    for run in runs:
        qa_status = run.get("qa_status")
        if qa_status:
            qa_counts[qa_status] += 1
            summary.total_qa_runs += 1
        else:
            qa_counts["not_run"] += 1

    summary.qa_passed = qa_counts.get("passed", 0)
    summary.qa_warning = qa_counts.get("warning", 0)
    summary.qa_failed = qa_counts.get("failed", 0)
    summary.qa_error = qa_counts.get("error", 0)
    summary.qa_not_run = qa_counts.get("not_run", 0)

    # Compute pass rate
    total_with_status = summary.qa_passed + summary.qa_warning + summary.qa_failed
    if total_with_status > 0:
        summary.pass_rate = summary.qa_passed / total_with_status

    return summary


def compute_current_month_cost(runs: List[Dict[str, Any]]) -> float:
    """
    Compute total cost for the current calendar month.

    Args:
        runs: List of run summary dicts

    Returns:
        Total cost for current month in USD
    """
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year

    total_cost = 0.0

    for run in runs:
        started_at = run.get("started_at")
        if not started_at:
            continue

        try:
            run_dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
            if run_dt.month == current_month and run_dt.year == current_year:
                cost_summary = run.get("cost_summary", {})
                total_cost += cost_summary.get("total_cost_usd", 0.0)
        except Exception:
            continue

    return total_cost


# ══════════════════════════════════════════════════════════════════════
# Export Functions
# ══════════════════════════════════════════════════════════════════════


def export_analytics_json(
    summary: AnalyticsSummary,
    project_summaries: List[ProjectSummary],
    model_summaries: List[ModelSummary],
    timeseries: List[TimeSeriesPoint],
) -> str:
    """
    Export analytics as JSON string.

    Args:
        summary: Overall analytics summary
        project_summaries: Per-project summaries
        model_summaries: Per-model summaries
        timeseries: Time-series data

    Returns:
        JSON string
    """
    export_data = {
        "summary": asdict(summary),
        "projects": [asdict(p) for p in project_summaries],
        "models": [asdict(m) for m in model_summaries],
        "timeseries": [asdict(t) for t in timeseries],
    }

    return json.dumps(export_data, indent=2, ensure_ascii=False)


def export_analytics_csv(
    summary: AnalyticsSummary,
    project_summaries: List[ProjectSummary],
    model_summaries: List[ModelSummary],
) -> str:
    """
    Export analytics as CSV string.

    Creates multiple sections:
    1. Overall Summary
    2. Per-Project Summary
    3. Per-Model Summary

    Args:
        summary: Overall analytics summary
        project_summaries: Per-project summaries
        model_summaries: Per-model summaries

    Returns:
        CSV string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Section 1: Overall Summary
    writer.writerow(["OVERALL SUMMARY"])
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Runs", summary.total_runs])
    writer.writerow(["Total Jobs", summary.total_jobs])
    writer.writerow(["Total Tokens", summary.total_tokens])
    writer.writerow(["Total Cost (USD)", f"{summary.total_cost:.4f}"])
    writer.writerow(["Avg Cost Per Run (USD)", f"{summary.avg_cost_per_run:.4f}"])
    writer.writerow(["Avg Duration (seconds)", f"{summary.avg_duration_seconds:.2f}"])
    writer.writerow(["Runs (2-loop)", summary.runs_2loop])
    writer.writerow(["Runs (3-loop)", summary.runs_3loop])
    writer.writerow(["Jobs Completed", summary.jobs_completed])
    writer.writerow(["Jobs Failed", summary.jobs_failed])
    writer.writerow(["Jobs Cancelled", summary.jobs_cancelled])
    writer.writerow(["QA Pass Rate", f"{summary.qa_summary.pass_rate:.2%}"])
    writer.writerow([])

    # Section 2: Per-Project Summary
    writer.writerow(["PER-PROJECT SUMMARY"])
    writer.writerow([
        "Project",
        "Runs",
        "Last Run",
        "Total Tokens",
        "Total Cost (USD)",
        "Avg Duration (s)",
        "QA Passed",
        "QA Warning",
        "QA Failed",
    ])

    for proj in project_summaries:
        writer.writerow([
            proj.project_name,
            proj.runs_count,
            proj.last_run_time or "N/A",
            proj.total_tokens,
            f"{proj.total_cost:.4f}",
            f"{proj.avg_duration_seconds:.2f}",
            proj.qa_passed,
            proj.qa_warning,
            proj.qa_failed,
        ])

    writer.writerow([])

    # Section 3: Per-Model Summary
    writer.writerow(["PER-MODEL SUMMARY"])
    writer.writerow(["Model", "Total Tokens", "Total Cost (USD)", "Usage Count"])

    for model in model_summaries:
        writer.writerow([
            model.model_name,
            model.total_tokens,
            f"{model.total_cost:.4f}",
            model.usage_count,
        ])

    return output.getvalue()


# ══════════════════════════════════════════════════════════════════════
# Main Analytics API
# ══════════════════════════════════════════════════════════════════════


def get_analytics(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get complete analytics data.

    This is the main entry point for the analytics system.

    Args:
        config: Optional analytics configuration

    Returns:
        Dict with keys:
        - summary: AnalyticsSummary (as dict)
        - projects: List[ProjectSummary] (as dicts)
        - models: List[ModelSummary] (as dicts)
        - timeseries: List[TimeSeriesPoint] (as dicts)
        - qa: QASummary (as dict)
    """
    if config is None:
        config = load_analytics_config()

    # Load data
    runs = load_all_runs()
    jobs = load_all_jobs()

    # Compute analytics
    summary = compute_overall_summary(runs, jobs, config)
    project_summaries = compute_project_summaries(runs)
    model_summaries = compute_model_summaries(runs)
    timeseries_days = config.get("timeseries_days", 30)
    timeseries = compute_timeseries(runs, days=timeseries_days)

    return {
        "summary": asdict(summary),
        "projects": [asdict(p) for p in project_summaries],
        "models": [asdict(m) for m in model_summaries],
        "timeseries": [asdict(t) for t in timeseries],
        "qa": asdict(summary.qa_summary),
    }
