"""
FastAPI web dashboard for the multi-agent orchestrator.

Provides a clean web interface for:
- Project selection and configuration
- Running orchestrator with custom parameters
- Viewing run history and detailed logs

STAGE 7: Web dashboard implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add agent/ to path to import our modules
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

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
    Start a new orchestrator run with the specified configuration.

    This endpoint:
    1. Validates the form data
    2. Builds a configuration dict
    3. Calls run_project() to execute the orchestrator
    4. Redirects to the run detail page

    Note: This is currently blocking (waits for run to complete).
    Future enhancement: Run in background with progress updates.
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
        # Run the orchestrator (blocking for now)
        run_summary = run_project(config)

        # Redirect to run detail page
        return RedirectResponse(url=f"/run/{run_summary.run_id}", status_code=303)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Run failed: {str(e)}")


@app.get("/run/{run_id}", response_class=HTMLResponse)
async def view_run(request: Request, run_id: str):
    """
    View detailed information about a specific run.

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
