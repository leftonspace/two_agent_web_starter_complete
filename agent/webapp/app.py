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
import file_explorer

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
