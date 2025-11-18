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

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add agent/ to path to import our modules
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from jobs import get_job_manager
from runner import get_run_details, list_projects, list_run_history, run_project

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
async def rerun_job(job_id: str):
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
async def api_cancel_job(job_id: str):
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
