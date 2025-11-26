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
from typing import Optional

# Make sure the repo root, agent/, and webapp/ are on sys.path
webapp_dir = Path(__file__).resolve().parent            # .../agent/webapp
agent_dir = webapp_dir.parent                           # .../agent
project_root = agent_dir.parent                         # .../two_agent_web_starter_clean_new

for p in (project_root, agent_dir, webapp_dir):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import qa  # now Python can see agent/qa.py

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import analytics  # noqa: E402
import brain  # noqa: E402
import file_explorer  # noqa: E402
from jobs import get_job_manager  # noqa: E402
from runner import get_run_details, list_projects, list_run_history, run_qa_only  # noqa: E402


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

class ConversationalAgent:
    """
    Temporary stub so the web UI can run even if conversational_agent.py is broken.
    """

    async def chat(self, message: str):
        # Simple placeholder response
        return "Conversational agent is not fully configured yet, but the dashboard is running."

    def get_active_tasks(self):
        return []

    def get_task_status(self, task_id: str):
        return None

    def get_agent_messages(self, since_id: Optional[str] = None):
        return []

    def get_pending_agent_responses(self):
        return []

    def respond_to_agent(self, message_id: str, response: str):
        return False


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

# Mount React UI build from ui/dist/ if it exists
ui_dist_dir = project_root / "ui" / "dist"
if ui_dist_dir.exists():
    # Mount assets folder for Vite build
    ui_assets_dir = ui_dist_dir / "assets"
    if ui_assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(ui_assets_dir)), name="ui_assets")
    print(f"[Startup] React UI available at /ui/* (served from {ui_dist_dir})")

# PHASE 1.1: Include authentication routers
app.include_router(auth_router)
app.include_router(api_keys_router)

# JARVIS CHAT: Include chat API router
try:
    from chat_api import router as chat_router
    app.include_router(chat_router)
    print("[Startup] Jarvis chat API loaded")
except ImportError as e:
    print(f"[Startup] Chat API not available: {e}")

# JARVIS VOICE: Include voice API router
try:
    from voice_api import router as voice_router
    app.include_router(voice_router)
    print("[Startup] Jarvis voice API loaded")
except ImportError as e:
    print(f"[Startup] Voice API not available: {e}")

# AI AGENTS: Include agents dashboard API router
try:
    from agents_api import router as agents_router
    app.include_router(agents_router)
    print("[Startup] AI Agents dashboard API loaded")
except ImportError as e:
    print(f"[Startup] Agents API not available: {e}")

# JARVIS VISION: Include vision API router
try:
    from vision_api import router as vision_router
    app.include_router(vision_router)
    print("[Startup] Jarvis vision API loaded")
except ImportError as e:
    print(f"[Startup] Vision API not available: {e}")

# CODE API: Include code analysis/completion API for VS Code extension and CLI
try:
    from code_api import router as code_router
    app.include_router(code_router)
    print("[Startup] Code API loaded (VS Code extension support)")
except ImportError as e:
    print(f"[Startup] Code API not available: {e}")

# FINANCE API: Include finance tools API for spreadsheets, documents, and templates
try:
    from finance_api import router as finance_router
    app.include_router(finance_router)
    print("[Startup] Finance API loaded (spreadsheet, document intelligence, templates)")
except ImportError as e:
    print(f"[Startup] Finance API not available: {e}")

# ADMIN API: Include admin tools for email, calendar, and workflow automation
try:
    from admin_api import router as admin_router
    app.include_router(admin_router)
    print("[Startup] Admin API loaded (email, calendar, workflow automation)")
except ImportError as e:
    print(f"[Startup] Admin API not available: {e}")

# JARVIS AGENT API: Include agent API for real-time tool-using agent
try:
    from agent_api import router as agent_router
    app.include_router(agent_router)
    print("[Startup] Jarvis Agent API loaded (real-time tool execution)")
except ImportError as e:
    print(f"[Startup] Agent API not available: {e}")

# ============================================================================
# JARVIS 2.0: Mount new Dashboard/Evaluation/Benchmark/Tasks API routes
# These provide the full JARVIS Specialist Dashboard API
# ============================================================================
try:
    from api.routes.dashboard import router as dashboard_api_router
    app.include_router(dashboard_api_router)
    print("[Startup] JARVIS Dashboard API loaded (/api/dashboard/*)")
except ImportError as e:
    print(f"[Startup] Dashboard API not available: {e}")

try:
    from api.routes.evaluation import router as evaluation_api_router
    app.include_router(evaluation_api_router)
    print("[Startup] JARVIS Evaluation API loaded (/api/evaluation/*)")
except ImportError as e:
    print(f"[Startup] Evaluation API not available: {e}")

try:
    from api.routes.benchmark import router as benchmark_api_router
    app.include_router(benchmark_api_router)
    print("[Startup] JARVIS Benchmark API loaded (/api/benchmark/*)")
except ImportError as e:
    print(f"[Startup] Benchmark API not available: {e}")

try:
    from api.routes.tasks import router as tasks_api_router
    app.include_router(tasks_api_router)
    print("[Startup] JARVIS Tasks API loaded (/api/tasks/*)")
except ImportError as e:
    print(f"[Startup] Tasks API not available: {e}")

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
    Redirect to Jarvis chat interface.

    The new default interface is the conversational Jarvis chat.
    For the old orchestrator dashboard, use /dashboard
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/jarvis")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Orchestrator dashboard with project selection form and run history.

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
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA execution failed: {str(e)}") from e




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
async def api_list_projects(current_user: User = Depends(require_auth)):
    """
    API endpoint to list all available projects.

    Returns:
        JSON array of project objects with name, path, file_count
    """
    return list_projects()


@app.get("/api/history")
async def api_list_history(limit: int = 50, current_user: User = Depends(require_auth)):
    """
    API endpoint to list run history.

    Args:
        limit: Maximum number of runs to return (default 50)

    Returns:
        JSON array of run summary objects
    """
    return list_run_history(limit=limit)


@app.get("/api/run/{run_id}")
async def api_get_run(run_id: str, current_user: User = Depends(require_auth)):
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
async def api_list_jobs(status: Optional[str] = None, limit: Optional[int] = None, current_user: User = Depends(require_auth)):
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
async def api_get_job(job_id: str, current_user: User = Depends(require_auth)):
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
async def api_get_job_logs(job_id: str, tail: Optional[int] = None, current_user: User = Depends(require_auth)):
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
    Run QA for a completed job.

    Returns:
        {
          "job_id": "...",
          "status": "passed" | "warning" | "failed",
          "summary": "...",
          "qa_report": {...}
        }
    """
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Determine project path from job config
    project_subdir = (job.config or {}).get("project_subdir")
    if not project_subdir:
        raise HTTPException(status_code=400, detail="Job is missing project_subdir in config")

    project_dir = agent_dir.parent / "sites" / project_subdir

    try:
        qa_report = run_qa_only(project_dir)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Stage10 tests expect a 500 on QA execution failure
        raise HTTPException(status_code=500, detail=f"QA execution failed: {str(e)}")

    # Convert report to dict
    qa_dict = qa_report.to_dict() if hasattr(qa_report, "to_dict") else dict(qa_report)

    # Update job QA fields
    job.qa_status = qa_dict.get("status")
    job.qa_summary = qa_dict.get("summary") or ""
    job.qa_report = qa_dict
    # The JobManager in tests is a MagicMock; this will just record the call.
    manager.save_job(job)

    return {
        "job_id": job.id,
        "status": job.qa_status,
        "summary": job.qa_summary,
        "qa_report": job.qa_report,
    }



@app.get("/api/jobs/{job_id}/qa")
def api_get_job_qa(job_id: str):
    """
    Get existing QA result for a job, if any.

    Returns:
        If QA exists:
          { "job_id": ..., "status": ..., "summary": ..., "qa_report": {...} }

        If QA has not been run:
          { "job_id": ..., "status": None, "summary": None, "qa_report": None }
    """
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.qa_report:
        # Important: tests expect a 'qa_report' key set to None or {}
        return {
            "job_id": job.id,
            "status": job.qa_status,
            "summary": job.qa_summary,
            "qa_report": None,
        }

    return {
        "job_id": job.id,
        "status": job.qa_status,
        "summary": job.qa_summary,
        "qa_report": job.qa_report,
    }



# ============================================================================
# STAGE 9: Project Explorer API Endpoints
# ============================================================================


@app.get("/api/projects/{project_id}/tree")
async def api_get_project_tree(project_id: str, path: Optional[str] = None, current_user: User = Depends(require_auth)):
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
async def api_get_project_file(project_id: str, path: str, current_user: User = Depends(require_auth)):
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
async def api_list_snapshots(project_id: str, current_user: User = Depends(require_auth)):
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
async def api_get_snapshot_tree(project_id: str, snapshot_id: str, path: Optional[str] = None, current_user: User = Depends(require_auth)):
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
async def api_get_snapshot_file(project_id: str, snapshot_id: str, path: str, current_user: User = Depends(require_auth)):
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
    current_user: User = Depends(require_auth),
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
async def api_analytics_summary(current_user: User = Depends(require_auth)):
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
async def api_analytics_projects(current_user: User = Depends(require_auth)):
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
async def api_analytics_models(current_user: User = Depends(require_auth)):
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
async def api_analytics_timeseries(current_user: User = Depends(require_auth)):
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
async def api_analytics_qa(current_user: User = Depends(require_auth)):
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
async def api_analytics_export_json(current_user: User = Depends(require_auth)):
    """
    Export complete analytics as JSON file.

    STAGE 11: Downloads all analytics data as JSON.

    Returns:
        JSON file download
    """
    from fastapi.responses import Response

    config = analytics.load_analytics_config()
    analytics.get_analytics(config)

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
async def api_analytics_export_csv(current_user: User = Depends(require_auth)):
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
async def api_get_project_profile(project_id: str, current_user: User = Depends(require_auth)):
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
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}") from e



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
    comments: Optional[str] = Form(None),
    current_user: User = Depends(require_auth)  # SECURITY: Use authenticated user
):
    """
    Approve an approval request.

    PHASE 3.1: Processes an approval decision.
    SECURITY: Uses authenticated user from session, not client-supplied data.

    Args:
        request_id: ID of the approval request
        comments: Optional comments
        current_user: Authenticated user from session

    Returns:
        JSON with updated request status
    """
    try:
        # SECURITY: Use authenticated user's ID and role from session
        updated_request = approval_engine.process_decision(
            request_id=request_id,
            approver_user_id=current_user.id,
            decision=DecisionType.APPROVE,
            comments=comments,
            approver_role=current_user.role
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
        raise HTTPException(status_code=500, detail="Failed to approve request")


@app.post("/api/approvals/{request_id}/reject")
async def api_reject_request(
    request_id: str,
    comments: Optional[str] = Form(None),
    current_user: User = Depends(require_auth)  # SECURITY: Use authenticated user
):
    """
    Reject an approval request.

    PHASE 3.1: Processes a rejection decision.
    SECURITY: Uses authenticated user from session, not client-supplied data.

    Args:
        request_id: ID of the approval request
        comments: Optional comments
        current_user: Authenticated user from session

    Returns:
        JSON with updated request status
    """
    try:
        # SECURITY: Use authenticated user's ID and role from session
        updated_request = approval_engine.process_decision(
            request_id=request_id,
            approver_user_id=current_user.id,
            decision=DecisionType.REJECT,
            comments=comments,
            approver_role=current_user.role
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
        raise HTTPException(status_code=500, detail="Failed to reject request")


@app.post("/api/approvals/{request_id}/escalate")
async def api_escalate_request(
    request_id: str,
    comments: Optional[str] = Form(None),
    current_user: User = Depends(require_auth)  # SECURITY: Use authenticated user
):
    """
    Escalate an approval request.

    PHASE 3.1: Escalates a request to the next level.
    SECURITY: Uses authenticated user from session, not client-supplied data.

    Args:
        request_id: ID of the approval request
        comments: Optional comments
        current_user: Authenticated user from session

    Returns:
        JSON with updated request status
    """
    try:
        # SECURITY: Use authenticated user's ID and role from session
        updated_request = approval_engine.process_decision(
            request_id=request_id,
            approver_user_id=current_user.id,
            decision=DecisionType.ESCALATE,
            comments=comments,
            approver_role=current_user.role
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
        raise HTTPException(status_code=500, detail="Failed to escalate request")


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
async def api_list_integrations(current_user: User = Depends(require_auth)):
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
async def api_add_integration(config: Dict = Form(...), current_user: User = Depends(require_auth)):
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
async def api_get_integration(connector_id: str, current_user: User = Depends(require_auth)):
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
async def api_connect_integration(connector_id: str, current_user: User = Depends(require_auth)):
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
async def api_disconnect_integration(connector_id: str, current_user: User = Depends(require_auth)):
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
async def api_test_integration(connector_id: str, current_user: User = Depends(require_auth)):
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
async def api_delete_integration(connector_id: str, current_user: User = Depends(require_auth)):
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


@app.get("/jarvis", response_class=HTMLResponse)
async def jarvis_chat_page(request: Request):
    """
    Serve Jarvis conversational interface.

    NEW: Modern chat interface with intelligent task routing.
    Routes to multi-agent orchestrator for complex tasks.
    """
    return templates.TemplateResponse(
        "jarvis.html",
        {"request": request}
    )


@app.get("/jarvis-dashboard", response_class=HTMLResponse)
async def jarvis_dashboard_page(request: Request):
    """
    Serve JARVIS Specialist Dashboard.

    PHASE 7: Comprehensive dashboard for monitoring specialist AI system:
    - Domain cards with specialist performance
    - Benchmark control panel
    - Task history and feedback
    - Budget monitoring
    - Evolution/graveyard tracking
    """
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


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
async def chat_endpoint(request: Request, current_user: User = Depends(require_auth)):
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
async def get_active_tasks(current_user: User = Depends(require_auth)):
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
async def get_task_status(task_id: str, current_user: User = Depends(require_auth)):
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


@app.get("/api/chat/agent-messages")
async def get_agent_messages(since_id: Optional[str] = None, current_user: User = Depends(require_auth)):
    """
    Get agent messages for streaming (Manager/Supervisor/Employee).

    PHASE 7.2: Returns new agent messages since given ID for real-time updates.

    Query params:
        since_id: Only return messages after this ID

    Returns:
        {"messages": [...], "pending_responses": [...]}
    """
    global conversational_agent

    if conversational_agent is None:
        return JSONResponse({"messages": [], "pending_responses": []})

    messages = conversational_agent.get_agent_messages(since_id)
    pending = conversational_agent.get_pending_agent_responses()

    return JSONResponse({
        "messages": messages,
        "pending_responses": pending
    })


@app.post("/api/chat/respond")
async def respond_to_agent(request: Request, current_user: User = Depends(require_auth)):
    """
    Respond to an agent's question/approval request.

    PHASE 7.2: Allows user to respond to Manager/Supervisor/Employee questions.

    POST /api/chat/respond
    Body: {"message_id": "msg_abc123", "response": "yes"}
    Response: {"success": true}
    """
    global conversational_agent

    if conversational_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Conversational agent not initialized"
        )

    try:
        data = await request.json()
        message_id = data.get("message_id", "")
        response = data.get("response", "")

        if not message_id or not response:
            return JSONResponse(
                {"error": "message_id and response required"},
                status_code=400
            )

        # Provide response to agent
        success = conversational_agent.respond_to_agent(message_id, response)

        return JSONResponse({
            "success": success
        })

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


# ══════════════════════════════════════════════════════════════════════
# JARVIS Specialist Dashboard API Endpoints
# ══════════════════════════════════════════════════════════════════════


@app.get("/api/specialists")
async def get_specialists():
    """
    Get list of all specialists with their current stats.

    Returns:
        List of specialists grouped by domain with performance metrics.
    """
    # TODO: Integrate with actual specialist pool manager
    # For now, return mock data for dashboard development
    specialists = {
        "administration": [
            {
                "id": "admin-1",
                "name": "Admin Pro",
                "score": 0.94,
                "tasks_completed": 42,
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "id": "admin-2",
                "name": "Admin Elite",
                "score": 0.88,
                "tasks_completed": 38,
                "status": "active",
                "created_at": "2024-01-20T14:45:00Z"
            },
            {
                "id": "admin-3",
                "name": "Admin Helper",
                "score": 0.72,
                "tasks_completed": 15,
                "status": "probation",
                "created_at": "2024-02-01T09:00:00Z"
            }
        ],
        "code_generation": [
            {
                "id": "code-1",
                "name": "Code Master",
                "score": 0.91,
                "tasks_completed": 67,
                "status": "active",
                "created_at": "2024-01-10T08:00:00Z"
            },
            {
                "id": "code-2",
                "name": "Code Helper",
                "score": 0.65,
                "tasks_completed": 23,
                "status": "probation",
                "created_at": "2024-02-05T11:30:00Z"
            }
        ],
        "business_documents": [
            {
                "id": "docs-1",
                "name": "Doc Writer",
                "score": 0.82,
                "tasks_completed": 28,
                "status": "active",
                "created_at": "2024-01-25T16:00:00Z"
            }
        ]
    }
    return JSONResponse(specialists)


@app.get("/api/specialists/{specialist_id}")
async def get_specialist_detail(specialist_id: str):
    """
    Get detailed information about a specific specialist.

    Returns:
        Specialist details including performance history and configuration.
    """
    # TODO: Fetch from actual specialist pool
    specialist = {
        "id": specialist_id,
        "name": "Admin Pro",
        "domain": "administration",
        "score": 0.94,
        "tasks_completed": 42,
        "success_rate": 0.96,
        "status": "active",
        "created_at": "2024-01-15T10:30:00Z",
        "model": "claude-3-sonnet",
        "temperature": 0.7,
        "system_prompt": "You are an expert administrative assistant...",
        "performance_history": [
            {"date": "2024-02-01", "score": 0.92},
            {"date": "2024-02-08", "score": 0.93},
            {"date": "2024-02-15", "score": 0.94},
            {"date": "2024-02-22", "score": 0.94}
        ],
        "recent_tasks": [
            {"id": "task-001", "description": "Schedule meeting", "score": 0.95, "status": "completed"},
            {"id": "task-002", "description": "Draft email", "score": 0.92, "status": "completed"},
            {"id": "task-003", "description": "Organize files", "score": 0.96, "status": "completed"}
        ]
    }
    return JSONResponse(specialist)


@app.get("/api/domains")
async def get_domains():
    """
    Get list of all domains with aggregate statistics.

    Returns:
        Domain list with specialist counts and average scores.
    """
    domains = [
        {
            "id": "administration",
            "name": "Administration",
            "icon": "terminal",
            "specialist_count": 3,
            "avg_score": 0.87,
            "tasks_today": 12,
            "tasks_total": 95
        },
        {
            "id": "code_generation",
            "name": "Code Generation",
            "icon": "code",
            "specialist_count": 2,
            "avg_score": 0.78,
            "tasks_today": 8,
            "tasks_total": 90
        },
        {
            "id": "business_documents",
            "name": "Business Documents",
            "icon": "file-text",
            "specialist_count": 1,
            "avg_score": 0.82,
            "tasks_today": 4,
            "tasks_total": 28
        }
    ]
    return JSONResponse(domains)


@app.get("/api/benchmark/status")
async def get_benchmark_status():
    """
    Get current benchmark status.

    Returns:
        Benchmark state including progress and results if available.
    """
    # TODO: Integrate with actual benchmark runner
    status = {
        "state": "idle",  # idle, running, paused, completed
        "progress": 0,
        "total_tasks": 0,
        "completed_tasks": 0,
        "current_domain": None,
        "last_run": {
            "timestamp": "2024-02-20T15:30:00Z",
            "avg_score": 0.84,
            "tasks_evaluated": 30,
            "domains_tested": 3
        }
    }
    return JSONResponse(status)


@app.post("/api/benchmark/run")
async def run_benchmark(request: Request):
    """
    Start a new benchmark run.

    Body:
        domains: Optional list of domain IDs to benchmark (default: all)
        task_count: Number of tasks per domain (default: 10)

    Returns:
        Benchmark run ID and initial status.
    """
    try:
        data = await request.json()
        domains = data.get("domains", ["administration", "code_generation", "business_documents"])
        task_count = data.get("task_count", 10)

        # TODO: Actually start benchmark
        run_id = f"bench-{int(datetime.now().timestamp())}"

        return JSONResponse({
            "run_id": run_id,
            "status": "started",
            "domains": domains,
            "task_count": task_count,
            "message": "Benchmark started successfully"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/benchmark/pause")
async def pause_benchmark():
    """
    Pause the currently running benchmark.

    Returns:
        Updated benchmark status.
    """
    # TODO: Actually pause benchmark
    return JSONResponse({
        "status": "paused",
        "message": "Benchmark paused"
    })


@app.get("/api/tasks")
async def get_tasks(
    domain: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Get task history with optional filtering.

    Query params:
        domain: Filter by domain ID
        status: Filter by status (completed, pending, failed)
        limit: Max results to return
        offset: Pagination offset

    Returns:
        List of tasks with metadata.
    """
    # TODO: Fetch from actual task history
    tasks = [
        {
            "id": "task-001",
            "description": "Schedule team meeting for project review",
            "domain": "administration",
            "specialist": "Admin Pro",
            "score": 0.95,
            "status": "completed",
            "timestamp": "2024-02-22T14:30:00Z",
            "cost": 0.0012,
            "feedback": "positive"
        },
        {
            "id": "task-002",
            "description": "Generate Python API endpoint",
            "domain": "code_generation",
            "specialist": "Code Master",
            "score": 0.88,
            "status": "completed",
            "timestamp": "2024-02-22T14:15:00Z",
            "cost": 0.0045,
            "feedback": None
        },
        {
            "id": "task-003",
            "description": "Draft quarterly report summary",
            "domain": "business_documents",
            "specialist": "Doc Writer",
            "score": 0.72,
            "status": "completed",
            "timestamp": "2024-02-22T13:45:00Z",
            "cost": 0.0023,
            "feedback": "negative"
        },
        {
            "id": "task-004",
            "description": "Refactor authentication module",
            "domain": "code_generation",
            "specialist": "Code Helper",
            "score": None,
            "status": "pending",
            "timestamp": "2024-02-22T14:45:00Z",
            "cost": 0.0,
            "feedback": None
        },
        {
            "id": "task-005",
            "description": "Parse email attachments",
            "domain": "administration",
            "specialist": "Admin Helper",
            "score": 0.45,
            "status": "failed",
            "timestamp": "2024-02-22T12:30:00Z",
            "cost": 0.0008,
            "feedback": None,
            "error": "Unable to access attachment - permission denied"
        }
    ]

    # Apply filters
    if domain:
        tasks = [t for t in tasks if t["domain"] == domain]
    if status:
        tasks = [t for t in tasks if t["status"] == status]

    return JSONResponse({
        "tasks": tasks[offset:offset + limit],
        "total": len(tasks),
        "limit": limit,
        "offset": offset
    })


@app.post("/api/tasks")
async def create_task(request: Request):
    """
    Create a new task for specialist processing.

    Body:
        description: Task description
        domain: Target domain (optional, auto-routed if not specified)
        priority: Task priority (low, normal, high)

    Returns:
        Created task with assigned specialist.
    """
    try:
        data = await request.json()
        description = data.get("description", "")
        domain = data.get("domain")
        priority = data.get("priority", "normal")

        if not description:
            return JSONResponse({"error": "description required"}, status_code=400)

        # TODO: Actually route and create task
        task_id = f"task-{int(datetime.now().timestamp())}"

        return JSONResponse({
            "id": task_id,
            "description": description,
            "domain": domain or "auto",
            "priority": priority,
            "status": "pending",
            "specialist": None,
            "message": "Task created and queued for processing"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/tasks/{task_id}/feedback")
async def submit_task_feedback(task_id: str, request: Request):
    """
    Submit feedback for a completed task.

    Body:
        type: Feedback type (positive, negative)
        comment: Optional comment

    Returns:
        Updated task status.
    """
    try:
        data = await request.json()
        feedback_type = data.get("type", "")
        comment = data.get("comment", "")

        if feedback_type not in ("positive", "negative"):
            return JSONResponse({"error": "type must be 'positive' or 'negative'"}, status_code=400)

        # TODO: Store feedback and update specialist scores
        return JSONResponse({
            "task_id": task_id,
            "feedback": feedback_type,
            "comment": comment,
            "message": "Feedback recorded successfully"
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/budget/status")
async def get_budget_status():
    """
    Get current budget status across all tiers.

    Returns:
        Budget usage for production, benchmark, and development tiers.
    """
    import os

    # Get limits from environment or use defaults
    budget = {
        "production": {
            "spent_daily": 12.50,
            "limit_daily": float(os.getenv("BUDGET_PRODUCTION_DAILY", 20.00)),
            "limit_weekly": float(os.getenv("BUDGET_PRODUCTION_WEEKLY", 100.00)),
            "limit_monthly": float(os.getenv("BUDGET_PRODUCTION_MONTHLY", 300.00))
        },
        "benchmark": {
            "spent_daily": 2.30,
            "limit_daily": float(os.getenv("BUDGET_BENCHMARK_DAILY", 5.00)),
            "limit_weekly": float(os.getenv("BUDGET_BENCHMARK_WEEKLY", 25.00)),
            "limit_monthly": float(os.getenv("BUDGET_BENCHMARK_MONTHLY", 75.00))
        },
        "development": {
            "spent_daily": 0.0,
            "limit_daily": float(os.getenv("BUDGET_DEVELOPMENT_DAILY", 10.00)),
            "limit_weekly": float(os.getenv("BUDGET_DEVELOPMENT_WEEKLY", 50.00)),
            "limit_monthly": float(os.getenv("BUDGET_DEVELOPMENT_MONTHLY", 150.00))
        },
        "warn_percent": int(os.getenv("BUDGET_WARN_PERCENT", 80)),
        "critical_percent": int(os.getenv("BUDGET_CRITICAL_PERCENT", 95))
    }
    return JSONResponse(budget)


@app.post("/api/evolution/trigger")
async def trigger_evolution():
    """
    Manually trigger an evolution cycle.

    Returns:
        Evolution cycle results including any culled specialists.
    """
    # TODO: Actually trigger evolution
    return JSONResponse({
        "status": "completed",
        "specialists_evaluated": 6,
        "specialists_culled": 0,
        "specialists_promoted": 1,
        "message": "Evolution cycle completed. No specialists culled."
    })


@app.get("/api/graveyard")
async def get_graveyard():
    """
    Get list of retired/culled specialists.

    Returns:
        List of retired specialists with retirement reasons.
    """
    graveyard = [
        {
            "id": "admin-retired-1",
            "name": "Admin Trainee",
            "domain": "administration",
            "final_score": 0.52,
            "tasks_completed": 8,
            "retired_at": "2024-02-10T12:00:00Z",
            "reason": "Score below threshold (0.6) for 7 consecutive days"
        },
        {
            "id": "code-retired-1",
            "name": "Code Rookie",
            "domain": "code_generation",
            "final_score": 0.48,
            "tasks_completed": 5,
            "retired_at": "2024-02-05T09:30:00Z",
            "reason": "Failed 3 consecutive tasks"
        }
    ]
    return JSONResponse(graveyard)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        JSON with status "ok"
    """
    return {"status": "ok"}


@app.get("/version")
async def get_version():
    """
    Get API and JARVIS version information.

    Returns:
        JSON with version info
    """
    return {
        "api_version": "2.0.0",
        "jarvis_version": "2.0.0",
        "architecture": "JARVIS 2.0 Domain-Based Specialist Pools",
        "features": [
            "Domain-based specialist pools",
            "Scoring Committee evaluation",
            "AI Council evaluation",
            "Benchmark-driven evolution",
            "User feedback integration",
            "Budget management"
        ]
    }


# ============================================================================
# React UI Routes - Serve the JARVIS Dashboard React app
# ============================================================================

@app.get("/ui")
@app.get("/ui/{path:path}")
async def serve_react_ui(request: Request, path: str = ""):
    """
    Serve the React JARVIS Dashboard UI.

    This serves the built React app from ui/dist/ and handles client-side routing
    by returning index.html for all non-asset routes.

    Access the new React dashboard at: /ui
    """
    from fastapi.responses import FileResponse

    ui_dist_dir = project_root / "ui" / "dist"

    if not ui_dist_dir.exists():
        return HTMLResponse(
            content="""
            <html>
            <head><title>JARVIS Dashboard</title></head>
            <body style="background: #0a0a0f; color: #e5e5e8; font-family: sans-serif; padding: 40px;">
                <h1>React UI Not Built</h1>
                <p>The React dashboard has not been built yet.</p>
                <p>To build it, run:</p>
                <pre style="background: #1a1a2f; padding: 20px; border-radius: 8px;">
cd ui
npm install
npm run build
                </pre>
                <p>Or use the legacy dashboard at <a href="/jarvis-dashboard" style="color: #00ff88;">/jarvis-dashboard</a></p>
            </body>
            </html>
            """,
            status_code=200
        )

    # Serve index.html for all routes (React handles routing)
    index_file = ui_dist_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)


# Main entry point for running the app
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  🤖 JARVIS 2.0 - AI Specialist System")
    print("=" * 60)
    print()
    print("  Dashboard (React):   http://127.0.0.1:8000/ui")
    print("  Dashboard (Legacy):  http://127.0.0.1:8000/jarvis-dashboard")
    print("  Chat Interface:      http://127.0.0.1:8000/jarvis")
    print("  Orchestrator:        http://127.0.0.1:8000/dashboard")
    print()
    print("  API Endpoints:")
    print("    /api/dashboard/*   - Dashboard data")
    print("    /api/evaluation/*  - Evaluation control")
    print("    /api/benchmark/*   - Benchmark execution")
    print("    /api/tasks/*       - Task management")
    print("    /health            - Health check")
    print("    /version           - Version info")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    uvicorn.run(
        "agent.webapp.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload on code changes during development
        log_level="info",
    )
