"""
FastAPI web dashboard for the multi-agent orchestrator.

Provides a clean web interface for:
- Project selection and configuration
- Running orchestrator with custom parameters
- Viewing run history and detailed logs

STAGE 7: Web dashboard implementation.
STAGE 8: Job manager with background execution, live logs, and cancellation.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add agent/ to path to import our modules
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from jobs import get_job_manager
from runner import get_run_details, list_projects, list_run_history, run_project, run_qa_only
import file_explorer
import qa
import analytics
import brain

# PHASE 7.1: Conversational Agent
from conversational_agent import ConversationalAgent

# PHASE 1.1: Authentication
from agent.webapp.auth import (
    User,
    get_current_user,
    require_admin,
    require_auth,
    require_developer,
)
from agent.webapp.auth_routes import (
    auth_router,
    api_keys_router,
    initialize_auth_system,
)

# Initialize FastAPI app
app = FastAPI(
    title="AI Dev Team Dashboard",
    description="Control and monitor the multi-agent orchestrator",
    version="1.0.0",
)

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files (CSS, JS) if directory exists
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# PHASE 1.1: Include authentication routers
app.include_router(auth_router)
app.include_router(api_keys_router)

# PHASE 7.1: Global conversational agent instance
conversational_agent: Optional[ConversationalAgent] = None

# Initialize auth system on startup
@app.on_event("startup")
async def startup_event():
    """Initialize authentication and conversational agent systems."""
    global conversational_agent
    initialize_auth_system()
    conversational_agent = ConversationalAgent()
    print("[Startup] Conversational agent initialized")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Home page with project selection form and run history.

    Shows:
    - Form to configure and start a new run
    - List of recent runs with quick links
    """
    projects = list_projects()
    history = list_run_history(limit=20)  # Show 20 most recent runs

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "projects": projects,
            "history": history,
        },
    )


@app.post("/run")
async def start_run(
    project_subdir: str = Form(...),
    mode: str = Form(...),
    task: str = Form(...),
    max_rounds: int = Form(...),
    max_cost_usd: float = Form(0.0),
    cost_warning_usd: float = Form(0.0),
    use_visual_review: bool = Form(False),
    use_git: bool = Form(False),
    current_user: User = Depends(require_developer),  # PHASE 1.1: Require developer role
):
    """
    Start a new orchestrator run in the background.

    STAGE 8: This endpoint now creates a background job instead of blocking.

    This endpoint:
    1. Validates the form data
    2. Builds a configuration dict
    3. Creates a job and starts it in the background
    4. Redirects to the job detail page

    The job runs asynchronously, allowing the UI to remain responsive.
    """
    # Build configuration
    config = {
        "project_subdir": project_subdir,
        "mode": mode,
        "task": task,
        "max_rounds": max_rounds,
        "max_cost_usd": max_cost_usd,
        "cost_warning_usd": cost_warning_usd,
        "use_visual_review": use_visual_review,
        "use_git": use_git,
        "interactive_cost_mode": "off",  # Always off for web runs
        "prompts_file": "prompts_default.json",
    }

    try:
        # Create and start background job
        job_manager = get_job_manager()
        job = job_manager.create_job(config)
        job_manager.start_job(job.id)

        # Redirect to job detail page
        return RedirectResponse(url=f"/jobs/{job.id}", status_code=303)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")


@app.get("/jobs", response_class=HTMLResponse)
async def list_jobs_page(request: Request, status: Optional[str] = None):
    """
    Job list page showing all background jobs.

    STAGE 8: New job list page with status filtering.

    Args:
        status: Optional filter by status (queued, running, completed, etc.)

    Shows:
    - Table of all jobs with status, timestamps, and actions
    - Ability to view details, cancel, or rerun jobs
    """
    job_manager = get_job_manager()
    jobs = job_manager.list_jobs(status=status)

    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "filter_status": status,
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def view_job(request: Request, job_id: str):
    """
    Job detail page with live log streaming.

    STAGE 8: New job detail page with live logs and cancel/rerun actions.

    Shows:
    - Job configuration and status
    - Live-updating logs (via JavaScript polling)
    - Cost breakdown if completed
    - Cancel button if running
    - Rerun button for any job
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return templates.TemplateResponse(
        "job_detail.html",
        {
            "request": request,
            "job": job,
        },
    )


@app.post("/jobs/{job_id}/rerun")
async def rerun_job(job_id: str, current_user: User = Depends(require_developer)):
    """
    Rerun a job with the same configuration.

    STAGE 8: Create a new job using the configuration from an existing job.

    Args:
        job_id: ID of job to rerun

    Returns:
        Redirect to new job detail page
    """
    job_manager = get_job_manager()
    old_job = job_manager.get_job(job_id)

    if old_job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Create new job with same config
    new_job = job_manager.create_job(old_job.config)
    job_manager.start_job(new_job.id)

    # Redirect to new job
    return RedirectResponse(url=f"/jobs/{new_job.id}", status_code=303)


@app.get("/run/{run_id}", response_class=HTMLResponse)
async def view_run(request: Request, run_id: str):
    """
    View detailed information about a specific run.

    STAGE 7: Original run detail page (still supported for backward compatibility).

    Shows:
    - Run metadata (mode, project, task, timestamps)
    - Cost breakdown (estimated vs actual)
    - Iteration logs with status and notes
    - Final status and results
    """
    run_data = get_run_details(run_id)

    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return templates.TemplateResponse(
        "run_detail.html",
        {
            "request": request,
            "run": run_data,
        },
    )


# ============================================================================
# STAGE 9: Project & Snapshot Explorer Routes
# ============================================================================


@app.get("/projects", response_class=HTMLResponse)
async def list_projects_page(request: Request):
    """
    Projects list page showing all available projects.

    STAGE 9: Browse all projects under sites/ directory.

    Shows:
    - List of all projects with file counts
    - Links to explore each project
    """
    projects = list_projects()

    return templates.TemplateResponse(
        "projects.html",
        {
            "request": request,
            "projects": projects,
        },
    )


@app.get("/projects/{project_id}", response_class=HTMLResponse)
async def view_project(request: Request, project_id: str):
    """
    Project detail page with file explorer and snapshot browser.

    STAGE 9: Interactive file tree, snapshot list, and diff viewer.

    Shows:
    - File tree for browsing project files
    - File viewer for inspecting contents
    - List of snapshots for this project
    - Diff viewer for comparing versions
    """
    # Get project root
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    # Verify project exists
    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Get snapshots for this project
    snapshots = file_explorer.list_snapshots(project_path)

    return templates.TemplateResponse(
        "project_detail.html",
        {
            "request": request,
            "project_id": project_id,
            "project_path": str(project_path),
            "snapshots": snapshots,
        },
    )


@app.get("/api/projects")
async def api_list_projects():
    """
    API endpoint to list all available projects.

    Returns:
        JSON array of project objects with name, path, file_count
    """
    return list_projects()


@app.get("/api/history")
async def api_list_history(limit: int = 50):
    """
    API endpoint to list run history.

    Args:
        limit: Maximum number of runs to return (default 50)

    Returns:
        JSON array of run summary objects
    """
    return list_run_history(limit=limit)


@app.get("/api/run/{run_id}")
async def api_get_run(run_id: str):
    """
    API endpoint to get run details.

    Args:
        run_id: Run identifier

    Returns:
        JSON object with run details

    Raises:
        404: If run not found
    """
    run_data = get_run_details(run_id)

    if run_data is None:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return run_data


@app.get("/api/jobs")
async def api_list_jobs(status: Optional[str] = None, limit: Optional[int] = None):
    """
    API endpoint to list all jobs.

    STAGE 8: List jobs with optional filtering.

    Args:
        status: Filter by status (queued, running, completed, etc.)
        limit: Maximum number of jobs to return

    Returns:
        JSON array of job objects
    """
    job_manager = get_job_manager()
    jobs = job_manager.list_jobs(limit=limit, status=status)
    return [asdict(job) for job in jobs]


@app.get("/api/jobs/{job_id}")
async def api_get_job(job_id: str):
    """
    API endpoint to get job details.

    STAGE 8: Get full job information including status and results.

    Args:
        job_id: Job identifier

    Returns:
        JSON object with job details

    Raises:
        404: If job not found
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return asdict(job)


@app.get("/api/jobs/{job_id}/logs")
async def api_get_job_logs(job_id: str, tail: Optional[int] = None):
    """
    API endpoint to get job logs.

    STAGE 8: Poll logs for live updates in the UI.

    Args:
        job_id: Job identifier
        tail: If specified, return only last N lines

    Returns:
        JSON object with logs as string

    Raises:
        404: If job not found
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    logs = job_manager.get_job_logs(job_id, tail_lines=tail)
    return {"logs": logs}


@app.post("/api/jobs/{job_id}/cancel")
async def api_cancel_job(job_id: str, current_user: User = Depends(require_developer)):
    """
    API endpoint to cancel a running job.

    STAGE 8: Set cancellation flag for graceful shutdown.

    Args:
        job_id: Job identifier

    Returns:
        JSON with success status

    Raises:
        404: If job not found
        400: If job cannot be cancelled (already finished)
    """
    job_manager = get_job_manager()
    success = job_manager.cancel_job(job_id)

    if not success:
        job = job_manager.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status}",
            )

    return {"success": True, "message": f"Job {job_id} cancellation requested"}


@app.post("/api/jobs/{job_id}/qa")
async def api_run_job_qa(job_id: str, current_user: User = Depends(require_developer)):
    """
    Run QA checks on an existing job's project.

    STAGE 10: Run quality checks on demand for any completed job.

    Args:
        job_id: Job identifier

    Returns:
        JSON with QA report

    Raises:
        404: If job or project not found
        400: If project files don't exist
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Get project path from job config
    project_subdir = job.config.get("project_subdir")
    if not project_subdir:
        raise HTTPException(status_code=400, detail="Job config missing project_subdir")

    project_path = agent_dir.parent / "sites" / project_subdir

    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project directory not found: {project_path}")

    # Get QA config from job config or use defaults
    qa_config_dict = job.config.get("qa", {})

    try:
        # Run QA checks
        qa_report = run_qa_only(project_path, qa_config_dict)

        # Update job with QA results
        from safe_io import safe_timestamp
        with job_manager.lock:
            job.qa_status = qa_report.status
            job.qa_summary = qa_report.summary
            job.qa_report = qa_report.to_dict()
            job.updated_at = safe_timestamp()
            job_manager._save_jobs()

        return qa_report.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA execution failed: {str(e)}")


@app.get("/api/jobs/{job_id}/qa")
async def api_get_job_qa(job_id: str):
    """
    Get QA report for a job.

    STAGE 10: Retrieve existing QA results.

    Args:
        job_id: Job identifier

    Returns:
        JSON with QA report or null if not run

    Raises:
        404: If job not found
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.qa_report:
        return job.qa_report
    else:
        return {
            "status": None,
            "summary": "QA not run for this job",
            "checks": None,
            "issues": [],
        }


# ============================================================================
# STAGE 9: Project Explorer API Endpoints
# ============================================================================


@app.get("/api/projects/{project_id}/tree")
async def api_get_project_tree(project_id: str, path: Optional[str] = None):
    """
    API endpoint to get file tree for a project.

    STAGE 9: Returns hierarchical file tree as JSON.

    Args:
        project_id: Project identifier (directory name under sites/)
        path: Optional subdirectory path (relative to project root)

    Returns:
        JSON array of file/directory nodes

    Raises:
        404: If project not found
        403: If path is outside project directory
    """
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Get relative path if provided
    relative_root = Path(path) if path else None

    # Get tree
    tree = file_explorer.get_project_tree(project_path, relative_root)

    return tree


@app.get("/api/projects/{project_id}/file")
async def api_get_project_file(project_id: str, path: str):
    """
    API endpoint to get file content from a project.

    STAGE 9: Returns file content with metadata.

    Args:
        project_id: Project identifier
        path: File path relative to project root

    Returns:
        JSON with file content and metadata

    Raises:
        404: If project or file not found
        403: If path is outside project directory
        400: If file is binary or too large
    """
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Get file content
    result = file_explorer.get_file_content(project_path, path)

    if result["error"]:
        if "Access denied" in result["error"]:
            raise HTTPException(status_code=403, detail=result["error"])
        elif "not found" in result["error"]:
            raise HTTPException(status_code=404, detail=result["error"])
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/api/projects/{project_id}/snapshots")
async def api_list_snapshots(project_id: str):
    """
    API endpoint to list all snapshots for a project.

    STAGE 9: Returns list of available snapshots (iterations).

    Args:
        project_id: Project identifier

    Returns:
        JSON array of snapshot objects

    Raises:
        404: If project not found
    """
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    snapshots = file_explorer.list_snapshots(project_path)

    # Convert to dicts for JSON
    return [asdict(snapshot) for snapshot in snapshots]


@app.get("/api/projects/{project_id}/snapshots/{snapshot_id}/tree")
async def api_get_snapshot_tree(project_id: str, snapshot_id: str, path: Optional[str] = None):
    """
    API endpoint to get file tree for a snapshot.

    STAGE 9: Returns hierarchical file tree for a specific iteration.

    Args:
        project_id: Project identifier
        snapshot_id: Snapshot identifier (e.g., "iteration_1")
        path: Optional subdirectory path

    Returns:
        JSON array of file/directory nodes

    Raises:
        404: If project or snapshot not found
    """
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    snapshot_path = project_path / ".history" / snapshot_id

    if not snapshot_path.exists() or not snapshot_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")

    # Get relative path if provided
    relative_root = Path(path) if path else None

    # Get tree (use snapshot_path as project_path for tree generation)
    tree = file_explorer.get_project_tree(snapshot_path, relative_root)

    return tree


@app.get("/api/projects/{project_id}/snapshots/{snapshot_id}/file")
async def api_get_snapshot_file(project_id: str, snapshot_id: str, path: str):
    """
    API endpoint to get file content from a snapshot.

    STAGE 9: Returns file content from a specific iteration.

    Args:
        project_id: Project identifier
        snapshot_id: Snapshot identifier
        path: File path relative to snapshot root

    Returns:
        JSON with file content and metadata

    Raises:
        404: If project, snapshot, or file not found
        403: If path is outside snapshot directory
    """
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    snapshot_path = project_path / ".history" / snapshot_id

    if not snapshot_path.exists() or not snapshot_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")

    # Get file content
    result = file_explorer.get_file_content(snapshot_path, path)

    if result["error"]:
        if "Access denied" in result["error"]:
            raise HTTPException(status_code=403, detail=result["error"])
        elif "not found" in result["error"]:
            raise HTTPException(status_code=404, detail=result["error"])
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.get("/api/diff")
async def api_compute_diff(
    project_id: str,
    file_path: str,
    source_type: str,  # "current" or "snapshot"
    source_id: Optional[str] = None,  # snapshot_id if source_type is "snapshot"
    target_type: str = "current",  # "current" or "snapshot"
    target_id: Optional[str] = None,  # snapshot_id if target_type is "snapshot"
):
    """
    API endpoint to compute diff between two file versions.

    STAGE 9: Compare file across snapshots or current version.

    Args:
        project_id: Project identifier
        file_path: Relative path to file
        source_type: "current" or "snapshot"
        source_id: Snapshot ID if source_type is "snapshot"
        target_type: "current" or "snapshot"
        target_id: Snapshot ID if target_type is "snapshot"

    Returns:
        JSON with diff text and metadata

    Raises:
        404: If project or files not found
        400: If parameters are invalid
    """
    sites_dir = agent_dir.parent / "sites"
    project_path = sites_dir / project_id

    if not project_path.exists() or not project_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Build source path
    if source_type == "current":
        source_file_path = project_path / file_path
        source_label = f"current/{file_path}"
    elif source_type == "snapshot":
        if not source_id:
            raise HTTPException(status_code=400, detail="source_id required when source_type is 'snapshot'")
        source_file_path = project_path / ".history" / source_id / file_path
        source_label = f"{source_id}/{file_path}"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid source_type: {source_type}")

    # Build target path
    if target_type == "current":
        target_file_path = project_path / file_path
        target_label = f"current/{file_path}"
    elif target_type == "snapshot":
        if not target_id:
            raise HTTPException(status_code=400, detail="target_id required when target_type is 'snapshot'")
        target_file_path = project_path / ".history" / target_id / file_path
        target_label = f"{target_id}/{file_path}"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid target_type: {target_type}")

    # Compute diff
    result = file_explorer.compute_diff(
        source_file_path,
        target_file_path,
        file1_label=source_label,
        file2_label=target_label,
    )

    return result


# ══════════════════════════════════════════════════════════════════════
# STAGE 11: Analytics Endpoints
# ══════════════════════════════════════════════════════════════════════


@app.get("/tuning", response_class=HTMLResponse)
async def tuning_page(request: Request):
    """
    Tuning & optimization page showing recommendations and auto-tune controls.

    STAGE 12: Displays self-learning recommendations based on historical data.
    """
    # Get tuning config
    tuning_config = brain.load_tuning_config()

    # For now, use the first project or a default
    # In a real implementation, this could be project-specific
    # Get all projects
    projects = list_projects()

    if not projects:
        # No projects, show empty state
        return templates.TemplateResponse(
            "tuning.html",
            {
                "request": request,
                "profile": None,
                "recommendations": [],
                "sufficient_data": False,
                "runs_count": 0,
                "min_runs": tuning_config.min_runs_for_recommendations,
                "auto_tune_enabled": tuning_config.enabled,
            },
        )

    # Use first project for demo (in real app, user would select)
    project_id = projects[0]["name"]

    # Load current config
    config_file = agent_dir / "project_config.json"
    current_config = {}
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                current_config = json.load(f)
        except Exception:
            pass

    # Get tuning analysis
    analysis = brain.get_tuning_analysis(project_id, current_config)

    return templates.TemplateResponse(
        "tuning.html",
        {
            "request": request,
            "profile": analysis["profile"],
            "recommendations": analysis["recommendations"],
            "sufficient_data": analysis["profile"]["sufficient_data"],
            "runs_count": analysis["profile"]["runs_count"],
            "min_runs": tuning_config.min_runs_for_recommendations,
            "auto_tune_enabled": tuning_config.enabled,
        },
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """
    Analytics dashboard page showing metrics, trends, and insights.

    STAGE 11: Displays aggregated analytics across all runs and jobs.
    """
    # Check if analytics is enabled
    config = analytics.load_analytics_config()
    if not config.get("enabled", True):
        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "enabled": False,
            },
        )

    # Get analytics data
    data = analytics.get_analytics(config)

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "enabled": True,
            "summary": data["summary"],
            "projects": data["projects"],
            "models": data["models"],
            "timeseries": data["timeseries"],
            "qa": data["qa"],
        },
    )


@app.get("/api/analytics/summary")
async def api_analytics_summary():
    """
    API endpoint for overall analytics summary.

    STAGE 11: Returns top-level KPIs and metrics.

    Returns:
        JSON with AnalyticsSummary data
    """
    config = analytics.load_analytics_config()
    data = analytics.get_analytics(config)
    return data["summary"]


@app.get("/api/analytics/projects")
async def api_analytics_projects():
    """
    API endpoint for per-project analytics.

    STAGE 11: Returns analytics broken down by project.

    Returns:
        JSON array of ProjectSummary objects
    """
    config = analytics.load_analytics_config()
    data = analytics.get_analytics(config)
    return data["projects"]


@app.get("/api/analytics/models")
async def api_analytics_models():
    """
    API endpoint for per-model analytics.

    STAGE 11: Returns analytics broken down by model.

    Returns:
        JSON array of ModelSummary objects
    """
    config = analytics.load_analytics_config()
    data = analytics.get_analytics(config)
    return data["models"]


@app.get("/api/analytics/timeseries")
async def api_analytics_timeseries():
    """
    API endpoint for time-series analytics.

    STAGE 11: Returns daily aggregates for charts.

    Returns:
        JSON object with 'daily' array of TimeSeriesPoint objects
    """
    config = analytics.load_analytics_config()
    data = analytics.get_analytics(config)
    return {"daily": data["timeseries"]}


@app.get("/api/analytics/qa")
async def api_analytics_qa():
    """
    API endpoint for QA analytics.

    STAGE 11: Returns QA-specific metrics and distributions.

    Returns:
        JSON with QASummary data
    """
    config = analytics.load_analytics_config()
    data = analytics.get_analytics(config)
    return data["qa"]


@app.get("/api/analytics/export/json")
async def api_analytics_export_json():
    """
    Export complete analytics as JSON file.

    STAGE 11: Downloads all analytics data as JSON.

    Returns:
        JSON file download
    """
    from fastapi.responses import Response

    config = analytics.load_analytics_config()
    data = analytics.get_analytics(config)

    # Convert data models back to objects for export
    runs = analytics.load_all_runs()
    jobs = analytics.load_all_jobs()

    summary = analytics.compute_overall_summary(runs, jobs, config)
    project_summaries = analytics.compute_project_summaries(runs)
    model_summaries = analytics.compute_model_summaries(runs)
    timeseries_days = config.get("timeseries_days", 30)
    timeseries = analytics.compute_timeseries(runs, days=timeseries_days)

    json_content = analytics.export_analytics_json(
        summary, project_summaries, model_summaries, timeseries
    )

    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=analytics.json"},
    )


@app.get("/api/analytics/export/csv")
async def api_analytics_export_csv():
    """
    Export analytics as CSV file.

    STAGE 11: Downloads analytics data as CSV.

    Returns:
        CSV file download
    """
    from fastapi.responses import Response

    config = analytics.load_analytics_config()

    # Load and compute analytics
    runs = analytics.load_all_runs()
    jobs = analytics.load_all_jobs()

    summary = analytics.compute_overall_summary(runs, jobs, config)
    project_summaries = analytics.compute_project_summaries(runs)
    model_summaries = analytics.compute_model_summaries(runs)

    csv_content = analytics.export_analytics_csv(
        summary, project_summaries, model_summaries
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics.csv"},
    )


# ══════════════════════════════════════════════════════════════════════
# STAGE 12: Self-Optimization & Auto-Tuning Endpoints
# ══════════════════════════════════════════════════════════════════════


@app.get("/api/projects/{project_id}/profile")
async def api_get_project_profile(project_id: str):
    """
    Get project profile and tuning analysis.

    STAGE 12: Returns historical performance data and recommendations.

    Args:
        project_id: Project identifier

    Returns:
        JSON with profile, recommendations, and tuning config
    """
    # Load current config for this project
    agent_dir_path = agent_dir.parent / "sites" / project_id
    if not agent_dir_path.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # Get current config from project_config.json as baseline
    config_file = agent_dir / "project_config.json"
    current_config = {}
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                current_config = json.load(f)
        except Exception:
            pass

    # Get tuning analysis
    analysis = brain.get_tuning_analysis(project_id, current_config)

    return analysis


@app.get("/api/projects/{project_id}/recommendations")
async def api_get_recommendations(project_id: str):
    """
    Get current recommendations for a project.

    STAGE 12: Returns just the recommendations without full profile.

    Args:
        project_id: Project identifier

    Returns:
        JSON array of recommendations
    """
    # Load current config
    config_file = agent_dir / "project_config.json"
    current_config = {}
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                current_config = json.load(f)
        except Exception:
            pass

    # Build profile and generate recommendations
    profile = brain.build_project_profile(project_id)
    recommendations = brain.generate_recommendations(profile, current_config)

    return {
        "recommendations": [asdict(r) for r in recommendations],
        "sufficient_data": profile.sufficient_data,
        "runs_count": profile.runs_count,
    }


@app.post("/api/auto-tune/toggle")
async def api_toggle_auto_tune(enabled: bool = Form(...), current_user: User = Depends(require_admin)):
    """
    Toggle auto-tune on/off globally.

    STAGE 12: Updates project_config.json to enable/disable auto-tuning.

    Args:
        enabled: True to enable, False to disable

    Returns:
        JSON with new auto-tune status
    """
    config_file = agent_dir / "project_config.json"

    if not config_file.exists():
        raise HTTPException(status_code=404, detail="Configuration file not found")

    try:
        # Read current config
        with config_file.open("r", encoding="utf-8") as f:
            config = json.load(f)

        # Update auto-tune setting
        if "auto_tune" not in config:
            config["auto_tune"] = {}

        config["auto_tune"]["enabled"] = enabled

        # Write back
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "enabled": enabled,
            "message": f"Auto-tune {'enabled' if enabled else 'disabled'}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@app.get("/api/strategies")
async def api_get_strategies():
    """
    Get available prompt strategies.

    STAGE 12: Returns list of available prompt strategies.

    Returns:
        JSON with available strategies
    """
    strategies = brain.get_available_strategies()

    return {
        "strategies": strategies,
        "default": "baseline"
    }


# ══════════════════════════════════════════════════════════════════════
# PHASE 3.1: Approval Workflows
# ══════════════════════════════════════════════════════════════════════

from approval_engine import ApprovalEngine, DecisionType
from datetime import datetime, timedelta

# Initialize approval engine
approval_engine = ApprovalEngine()


@app.get("/approvals", response_class=HTMLResponse)
async def approvals_page(request: Request):
    """
    Approval dashboard page.

    PHASE 3.1: Shows pending approvals and allows approve/reject/escalate actions.

    Returns:
        HTML approval dashboard
    """
    return templates.TemplateResponse(
        "approvals.html",
        {
            "request": request,
        },
    )


@app.get("/api/approvals")
async def api_get_approvals(
    domain: Optional[str] = None,
    role: Optional[str] = None,
    user_id: Optional[str] = None
):
    """
    Get pending approvals.

    PHASE 3.1: Returns list of pending approval requests filtered by domain/role/user.

    Args:
        domain: Filter by domain (hr, finance, legal, etc.)
        role: Filter by approver role
        user_id: Filter by specific user ID

    Returns:
        JSON with approvals list and statistics
    """
    try:
        # Get pending approvals
        approvals = approval_engine.get_pending_approvals(
            user_id=user_id,
            role=role,
            domain=domain
        )

        # Calculate statistics
        total_pending = len(approvals)
        overdue = sum(1 for a in approvals if a.get('is_overdue', False))

        # Get today's approved/rejected (from last 24 hours)
        conn = approval_engine._get_connection()
        cursor = conn.cursor()

        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()

        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM approval_requests
            WHERE completed_at > ?
            GROUP BY status
        """, (yesterday,))

        rows = cursor.fetchall()
        conn.close()

        stats = {
            'pending': total_pending,
            'overdue': overdue,
            'approved_today': 0,
            'rejected_today': 0
        }

        for row in rows:
            if row['status'] == 'approved':
                stats['approved_today'] = row['count']
            elif row['status'] == 'rejected':
                stats['rejected_today'] = row['count']

        return {
            'approvals': approvals,
            'statistics': stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approvals: {str(e)}")


@app.post("/api/approvals/{request_id}/approve")
async def api_approve_request(
    request_id: str,
    approver_user_id: str = Form(...),
    approver_role: Optional[str] = Form(None),
    comments: Optional[str] = Form(None)
):
    """
    Approve an approval request.

    PHASE 3.1: Processes an approval decision.

    Args:
        request_id: ID of the approval request
        approver_user_id: ID of the user approving
        approver_role: Role of the approver
        comments: Optional comments

    Returns:
        JSON with updated request status
    """
    try:
        updated_request = approval_engine.process_decision(
            request_id=request_id,
            approver_user_id=approver_user_id,
            decision=DecisionType.APPROVE,
            comments=comments,
            approver_role=approver_role
        )

        return {
            'success': True,
            'request_id': request_id,
            'status': updated_request.status.value,
            'message': 'Request approved successfully'
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve request: {str(e)}")


@app.post("/api/approvals/{request_id}/reject")
async def api_reject_request(
    request_id: str,
    approver_user_id: str = Form(...),
    approver_role: Optional[str] = Form(None),
    comments: Optional[str] = Form(None)
):
    """
    Reject an approval request.

    PHASE 3.1: Processes a rejection decision.

    Args:
        request_id: ID of the approval request
        approver_user_id: ID of the user rejecting
        approver_role: Role of the approver
        comments: Optional comments

    Returns:
        JSON with updated request status
    """
    try:
        updated_request = approval_engine.process_decision(
            request_id=request_id,
            approver_user_id=approver_user_id,
            decision=DecisionType.REJECT,
            comments=comments,
            approver_role=approver_role
        )

        return {
            'success': True,
            'request_id': request_id,
            'status': updated_request.status.value,
            'message': 'Request rejected'
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject request: {str(e)}")


@app.post("/api/approvals/{request_id}/escalate")
async def api_escalate_request(
    request_id: str,
    approver_user_id: str = Form(...),
    approver_role: Optional[str] = Form(None),
    comments: Optional[str] = Form(None)
):
    """
    Escalate an approval request.

    PHASE 3.1: Escalates a request to the next level.

    Args:
        request_id: ID of the approval request
        approver_user_id: ID of the user escalating
        approver_role: Role of the approver
        comments: Optional comments

    Returns:
        JSON with updated request status
    """
    try:
        updated_request = approval_engine.process_decision(
            request_id=request_id,
            approver_user_id=approver_user_id,
            decision=DecisionType.ESCALATE,
            comments=comments,
            approver_role=approver_role
        )

        return {
            'success': True,
            'request_id': request_id,
            'status': updated_request.status.value,
            'message': 'Request escalated'
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to escalate request: {str(e)}")


@app.get("/api/approvals/{request_id}")
async def api_get_approval_details(request_id: str):
    """
    Get detailed information about an approval request.

    PHASE 3.1: Returns full request details including all decisions.

    Args:
        request_id: ID of the approval request

    Returns:
        JSON with request details
    """
    try:
        request = approval_engine.get_request(request_id)

        if not request:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")

        workflow = approval_engine.get_workflow(request.workflow_id)

        return {
            'request_id': request.request_id,
            'workflow_id': request.workflow_id,
            'workflow_name': workflow.workflow_name if workflow else None,
            'mission_id': request.mission_id,
            'domain': request.domain,
            'task_type': request.task_type,
            'status': request.status.value,
            'payload': request.payload,
            'current_step_index': request.current_step_index,
            'created_at': request.created_at,
            'updated_at': request.updated_at,
            'completed_at': request.completed_at,
            'decisions': [
                {
                    'decision_id': d.decision_id,
                    'step_id': d.step_id,
                    'approver_user_id': d.approver_user_id,
                    'approver_role': d.approver_role,
                    'decision': d.decision.value,
                    'comments': d.comments,
                    'decided_at': d.decided_at
                }
                for d in request.decisions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get request details: {str(e)}")


@app.get("/api/workflows")
async def api_get_workflows(domain: Optional[str] = None):
    """
    Get available approval workflows.

    PHASE 3.1: Returns list of registered workflows.

    Args:
        domain: Filter by domain (hr, finance, legal, etc.)

    Returns:
        JSON with workflows list
    """
    try:
        conn = approval_engine._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM approval_workflows"
        params = []

        if domain:
            query += " WHERE domain = ?"
            params.append(domain)

        query += " ORDER BY domain, task_type"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        workflows = []
        for row in rows:
            workflows.append({
                'workflow_id': row['workflow_id'],
                'domain': row['domain'],
                'task_type': row['task_type'],
                'workflow_name': row['workflow_name'],
                'description': row['description'],
                'created_at': row['created_at']
            })

        return {'workflows': workflows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


# ══════════════════════════════════════════════════════════════════════
# PHASE 3.2: System Integrations
# ══════════════════════════════════════════════════════════════════════

import sys
from pathlib import Path as PathLib

# Add integrations to path
integrations_path = PathLib(__file__).parent.parent / "integrations"
if str(integrations_path) not in sys.path:
    sys.path.insert(0, str(integrations_path))

from integrations.base import get_registry
from integrations.hris.bamboohr import BambooHRConnector
from integrations.database import DatabaseConnector

# Initialize global registry
integration_registry = get_registry()


@app.get("/integrations", response_class=HTMLResponse)
async def integrations_page(request: Request):
    """
    Integrations management page.

    PHASE 3.2: Manage external system connections.

    Returns:
        HTML integrations management page
    """
    return templates.TemplateResponse(
        "integrations.html",
        {
            "request": request,
        },
    )


@app.get("/api/integrations")
async def api_list_integrations():
    """
    List all registered integrations.

    PHASE 3.2: Returns list of connectors with health status.

    Returns:
        JSON with integrations list
    """
    try:
        health = integration_registry.get_health_summary()
        return {
            'integrations': health['connectors'],
            'summary': {
                'total': health['total_connectors'],
                'connected': health['connected'],
                'disconnected': health['disconnected'],
                'error': health['error']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list integrations: {str(e)}")


@app.post("/api/integrations")
async def api_add_integration(config: Dict = Form(...)):
    """
    Add a new integration.

    PHASE 3.2: Create and register a new connector.

    Args:
        config: Integration configuration

    Returns:
        JSON with created connector info
    """
    try:
        import uuid
        connector_id = str(uuid.uuid4())
        integration_type = config.get('type')

        if integration_type == 'bamboohr':
            connector = BambooHRConnector(
                connector_id=connector_id,
                subdomain=config['subdomain'],
                api_key=config['api_key']
            )

        elif integration_type in ['postgresql', 'mysql', 'sqlite']:
            connector = DatabaseConnector(
                connector_id=connector_id,
                engine=config.get('engine', integration_type),
                config=config
            )

        else:
            raise ValueError(f"Unsupported integration type: {integration_type}")

        # Register connector
        integration_registry.register(connector)

        # Connect
        await connector.connect()

        return {
            'success': True,
            'connector_id': connector_id,
            'name': connector.name,
            'status': connector.status.value
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add integration: {str(e)}")


@app.get("/api/integrations/{connector_id}")
async def api_get_integration(connector_id: str):
    """
    Get integration details.

    PHASE 3.2: Returns detailed connector information.

    Args:
        connector_id: Connector ID

    Returns:
        JSON with connector details
    """
    try:
        connector = integration_registry.get(connector_id)

        if not connector:
            raise HTTPException(status_code=404, detail=f"Integration {connector_id} not found")

        health = connector.get_health()

        return {
            'connector_id': health['connector_id'],
            'name': health['name'],
            'type': connector.__class__.__name__,
            'status': health['status'],
            'authenticated': health['authenticated'],
            'metrics': health['metrics'],
            'rate_limiter': health['rate_limiter']
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integration: {str(e)}")


@app.post("/api/integrations/{connector_id}/connect")
async def api_connect_integration(connector_id: str):
    """
    Connect an integration.

    PHASE 3.2: Establish connection to external system.

    Args:
        connector_id: Connector ID

    Returns:
        JSON with connection status
    """
    try:
        connector = integration_registry.get(connector_id)

        if not connector:
            raise HTTPException(status_code=404, detail=f"Integration {connector_id} not found")

        success = await connector.connect()

        return {
            'success': success,
            'status': connector.status.value,
            'message': 'Connected successfully' if success else 'Connection failed'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")


@app.post("/api/integrations/{connector_id}/disconnect")
async def api_disconnect_integration(connector_id: str):
    """
    Disconnect an integration.

    PHASE 3.2: Close connection to external system.

    Args:
        connector_id: Connector ID

    Returns:
        JSON with disconnection status
    """
    try:
        connector = integration_registry.get(connector_id)

        if not connector:
            raise HTTPException(status_code=404, detail=f"Integration {connector_id} not found")

        await connector.disconnect()

        return {
            'success': True,
            'status': connector.status.value,
            'message': 'Disconnected successfully'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@app.get("/api/integrations/{connector_id}/test")
async def api_test_integration(connector_id: str):
    """
    Test integration connection.

    PHASE 3.2: Tests connection and returns latency/health info.

    Args:
        connector_id: Connector ID

    Returns:
        JSON with test results
    """
    try:
        connector = integration_registry.get(connector_id)

        if not connector:
            raise HTTPException(status_code=404, detail=f"Integration {connector_id} not found")

        # Ensure connected
        if connector.status != ConnectionStatus.CONNECTED:
            await connector.connect()

        # Run test
        result = await connector.test_connection()

        return result

    except Exception as e:
        return {
            'success': False,
            'latency_ms': 0,
            'message': str(e),
            'details': {'error': str(e)}
        }


@app.delete("/api/integrations/{connector_id}")
async def api_delete_integration(connector_id: str):
    """
    Delete an integration.

    PHASE 3.2: Remove connector and cleanup.

    Args:
        connector_id: Connector ID

    Returns:
        JSON with deletion status
    """
    try:
        connector = integration_registry.get(connector_id)

        if not connector:
            raise HTTPException(status_code=404, detail=f"Integration {connector_id} not found")

        # Disconnect first
        await connector.disconnect()

        # Unregister
        integration_registry.unregister(connector_id)

        return {
            'success': True,
            'message': 'Integration deleted successfully'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")


# ══════════════════════════════════════════════════════════════════════
# PHASE 7.1: Conversational Agent Endpoints
# ══════════════════════════════════════════════════════════════════════


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """
    Serve conversational chat interface.

    PHASE 7.1: Chat UI for natural language interaction with System-1.2.
    """
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )


@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """
    Conversational chat endpoint.

    PHASE 7.1: Main endpoint for natural language chat interaction.

    POST /api/chat
    Body: {"message": "your message here"}
    Response: {"response": "agent response", "active_tasks": [...]}
    """
    global conversational_agent

    if conversational_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Conversational agent not initialized"
        )

    try:
        data = await request.json()
        message = data.get("message", "")

        if not message:
            return JSONResponse(
                {"error": "Message required"},
                status_code=400
            )

        # Process message through conversational agent
        response = await conversational_agent.chat(message)

        # Get active tasks
        active_tasks = conversational_agent.get_active_tasks()

        return JSONResponse({
            "response": response,
            "active_tasks": active_tasks
        })

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.get("/api/chat/tasks")
async def get_active_tasks():
    """
    Get list of active tasks.

    PHASE 7.1: Returns all tasks currently being executed by the agent.

    Returns:
        {"tasks": [{"task_id": "...", "description": "...", "status": "...", "progress": "..."}]}
    """
    global conversational_agent

    if conversational_agent is None:
        return JSONResponse({"tasks": []})

    tasks = conversational_agent.get_active_tasks()
    return JSONResponse({"tasks": tasks})


@app.get("/api/chat/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get detailed status of a specific task.

    PHASE 7.1: Returns detailed information about a task.

    Args:
        task_id: Task identifier

    Returns:
        Task details or 404 if not found
    """
    global conversational_agent

    if conversational_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Conversational agent not initialized"
        )

    status = conversational_agent.get_task_status(task_id)

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Task not found: {task_id}"
        )

    return JSONResponse(status)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        JSON with status "ok"
    """
    return {"status": "ok"}


# Main entry point for running the app
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  AI Dev Team Dashboard")
    print("=" * 60)
    print("  Starting web server on http://127.0.0.1:8000")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes during development
        log_level="info",
    )
