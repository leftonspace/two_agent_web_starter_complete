# Stage 7: Web Dashboard

**Stage 7** adds a local web interface for controlling and monitoring the multi-agent orchestrator. This provides a user-friendly alternative to the command-line interface while maintaining all existing functionality.

## Overview

The web dashboard provides:
- **Project selection** with visual configuration forms
- **Run control** to start orchestrator runs with custom parameters
- **Run history** with detailed logs and cost breakdowns
- **Live feedback** showing run results and iteration logs
- **RESTful API** for programmatic access

## Architecture

### Components

1. **`agent/runner.py`** - Programmatic API
   - `run_project(config)` - Run orchestrator with given configuration
   - `list_projects()` - List available projects in sites/
   - `list_run_history()` - List recent runs
   - `get_run_details(run_id)` - Get detailed run information

2. **`agent/webapp/`** - Web dashboard
   - `app.py` - FastAPI application with routes
   - `templates/` - Jinja2 HTML templates
   - `static/` - CSS, JavaScript (if needed)

3. **Routes**
   - `GET /` - Home page with form and history
   - `POST /run` - Start a new orchestrator run
   - `GET /run/{run_id}` - View run details
   - `GET /api/projects` - List projects (JSON)
   - `GET /api/history` - List run history (JSON)
   - `GET /api/run/{run_id}` - Get run details (JSON)
   - `GET /health` - Health check

### Design Principles

- **Backward compatibility** - CLI still works exactly as before
- **No breaking changes** - Existing orchestrator code unchanged
- **Minimal dependencies** - FastAPI, Jinja2, Uvicorn only
- **Production-safe** - All web features are optional
- **Clean separation** - Web layer doesn't modify core logic

## Installation

Install the required dependencies:

```bash
pip install fastapi jinja2 uvicorn
```

Or if you have a requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Web Dashboard

**Method 1: Direct execution**
```bash
cd agent/webapp
python app.py
```

**Method 2: Using uvicorn**
```bash
uvicorn agent.webapp.app:app --reload --host 127.0.0.1 --port 8000
```

**Method 3: Using Python module syntax**
```bash
python -m agent.webapp.app
```

The dashboard will be available at: **http://127.0.0.1:8000**

### Using the Web Interface

#### 1. Home Page

The home page displays:
- **Project selector** - Choose from available projects in `sites/`
- **Configuration form** - Set mode, rounds, costs, options
- **Run history** - Recent runs with status and costs

#### 2. Starting a Run

Fill out the form with:
- **Project** - Select from dropdown (auto-populated from sites/)
- **Mode** - Choose 2-loop or 3-loop
- **Task** - Describe what to build
- **Max Rounds** - Number of iteration cycles (typically 1-5)
- **Cost Limit** - Hard stop if exceeded (USD)
- **Cost Warning** - Show warning threshold (USD)
- **Visual Review** - Enable DOM analysis and screenshots
- **Git Integration** - Commit changes after each iteration

Click "Start Run" to execute. The page will block until the run completes, then redirect to the run detail page.

#### 3. Viewing Run Details

The run detail page shows:
- **Run metadata** - ID, project, mode, timestamps
- **Configuration** - All settings used for the run
- **Cost breakdown** - Estimated vs actual, per-model usage
- **Iteration log** - Detailed timeline with status and notes
- **Raw JSON** - Complete run data for debugging

#### 4. Run History

The home page lists recent runs with:
- Run ID (clickable link)
- Project name
- Mode (2loop/3loop)
- Status (color-coded badge)
- Rounds completed
- Total cost
- Start time

### Using the Programmatic API

You can also use the runner API directly in Python code:

```python
from agent.runner import run_project, list_projects, list_run_history

# List available projects
projects = list_projects()
print(f"Found {len(projects)} projects")

# Configure and run a project
config = {
    "mode": "3loop",
    "project_subdir": "my_project",
    "task": "Build a landing page with hero section and contact form",
    "max_rounds": 3,
    "max_cost_usd": 1.5,
    "cost_warning_usd": 0.8,
    "use_visual_review": True,
    "use_git": True,
    "interactive_cost_mode": "off",
    "prompts_file": "prompts_default.json",
}

# Run the orchestrator
run_summary = run_project(config)

print(f"Run completed: {run_summary.run_id}")
print(f"Final status: {run_summary.final_status}")
print(f"Total cost: ${run_summary.cost_summary['total_usd']:.4f}")

# List run history
history = list_run_history(limit=10)
for run in history:
    print(f"{run['run_id']}: {run['final_status']} (${run['cost_summary']['total_usd']:.4f})")
```

## Configuration

### Project Structure

Projects must exist under `sites/` directory:

```
sites/
├── my_project/         # Your project
│   ├── index.html
│   └── style.css
├── another_project/    # Another project
└── fixtures/          # (Auto-generated test content, ignored)
```

### Run Logs

Run logs are stored in `run_logs/<run_id>/`:

```
run_logs/
├── abc123/
│   └── run_summary.json    # Complete run data
├── def456/
│   └── run_summary.json
└── ...
```

Each `run_summary.json` contains:
- Run metadata (ID, timestamps, mode, project)
- Configuration used
- Iteration logs with status and notes
- Cost breakdown (estimated and actual)
- Final status and results

## API Reference

### `run_project(config: dict) -> RunSummary`

Run the orchestrator with the given configuration.

**Args:**
- `config` (dict): Configuration with keys:
  - `mode` (str): "2loop" or "3loop"
  - `project_subdir` (str): Folder name under sites/
  - `task` (str): Task description
  - `max_rounds` (int): Maximum iterations
  - `use_visual_review` (bool): Enable DOM analysis
  - `use_git` (bool): Enable git commits
  - `max_cost_usd` (float): Cost limit
  - `cost_warning_usd` (float): Warning threshold
  - `interactive_cost_mode` (str): "off", "once", or "always"
  - `prompts_file` (str): Prompts JSON file name

**Returns:**
- `RunSummary`: Complete run results

**Raises:**
- `ValueError`: Invalid configuration
- `FileNotFoundError`: Project directory not found
- `Exception`: Orchestrator error

### `list_projects() -> list[dict]`

List all available projects in the sites/ directory.

**Returns:**
- List of dicts with keys:
  - `name` (str): Project folder name
  - `path` (str): Full path to project
  - `exists` (bool): True if directory exists
  - `file_count` (int): Number of files in project

### `list_run_history(limit: int = 50) -> list[dict]`

List recent runs from the run_logs/ directory.

**Args:**
- `limit` (int): Maximum number of runs to return (default 50)

**Returns:**
- List of run summary dicts, sorted by start time (newest first)

### `get_run_details(run_id: str) -> dict | None`

Get detailed information about a specific run.

**Args:**
- `run_id` (str): Run identifier

**Returns:**
- Run summary dict, or None if run not found

## Testing

Run the Stage 7 tests:

```bash
# Run all Stage 7 tests
pytest agent/tests_stage7/

# Run specific test file
pytest agent/tests_stage7/test_runner.py
pytest agent/tests_stage7/test_webapp.py

# Run with verbose output
pytest agent/tests_stage7/ -v
```

Tests cover:
- Runner API functions (list_projects, list_history, get_run_details)
- Web routes (home, start run, view run details)
- API endpoints (JSON responses)
- Error handling (missing fields, invalid config, not found)

## Limitations & Future Enhancements

### Current Limitations

1. **Blocking execution** - The web UI blocks until the run completes
2. **No live progress** - Can't see iterations in real-time
3. **No run cancellation** - Can't stop a running orchestrator
4. **No authentication** - Web dashboard is unprotected (local only)
5. **Single instance** - Can't run multiple orchestrators concurrently

### Planned Enhancements

1. **Background execution** - Run orchestrator in background task
2. **WebSocket support** - Stream live progress updates
3. **Run control** - Pause/resume/cancel running orchestrators
4. **Multi-user support** - Authentication and user sessions
5. **Run comparison** - Compare results across multiple runs
6. **Cost analytics** - Charts and trends for token usage
7. **Project templates** - Quick-start templates for common tasks

## Troubleshooting

### Port already in use

If port 8000 is already taken:

```bash
uvicorn agent.webapp.app:app --reload --port 8001
```

### Module import errors

Ensure you're running from the project root:

```bash
cd /path/to/two_agent_web_starter_complete
python -m agent.webapp.app
```

### Templates not found

The webapp looks for templates relative to `agent/webapp/templates/`. Ensure:
- You're running from the project root, OR
- The `templates_dir` path in `app.py` is correct

### Run logs missing

Run logs are stored in `run_logs/` at the project root. If missing:
- Check that `run_mode.py` or `runner.py` completed successfully
- Verify write permissions on the `run_logs/` directory

## Integration with Existing Workflows

### CLI still works

The existing CLI entry point is unchanged:

```bash
# Original CLI usage
cd agent
python run_mode.py
```

### Dev tools integration

The web dashboard complements existing dev tools:

```bash
# Generate fixture for testing
python make.py fixture

# Run via web UI
python -m agent.webapp.app

# View logs (command-line)
python dev/view_logs.py --latest

# View logs (web UI)
# Visit http://127.0.0.1:8000
```

### Auto-pilot mode

Auto-pilot mode (STAGE 4) still works from CLI. Future enhancement will add web UI support for auto-pilot sessions.

## Design Decisions

### Why FastAPI?

- **Modern Python** - Async support, type hints, automatic docs
- **Minimal** - Lightweight, no heavy framework overhead
- **Well-documented** - Easy to extend and maintain
- **Fast** - Good performance for local dashboard

### Why not Flask?

Flask would also work well. FastAPI was chosen for:
- Built-in Pydantic validation
- Automatic OpenAPI/Swagger docs
- Modern async/await support
- Better type safety

### Why blocking execution?

The current implementation blocks during run execution for simplicity. This is acceptable for Stage 7 MVP because:
- Runs typically complete in minutes
- Local-only usage (no concurrent users)
- Easier to implement and test
- Future enhancement can add background tasks

### Why no database?

Run logs are stored as JSON files instead of a database because:
- Simple file-based storage is sufficient for MVP
- No additional dependencies required
- Easy to inspect and debug
- Compatible with existing run_logger.py
- Can migrate to database later if needed

## Summary

Stage 7 adds a clean, functional web dashboard while preserving all existing CLI and scripting workflows. The programmatic `run_project()` API enables future automation and integration possibilities. The web UI makes the orchestrator more accessible to non-technical users and provides better visibility into run history and costs.

**Key takeaways:**
- 🌐 Web dashboard at http://127.0.0.1:8000
- 🐍 Programmatic API via `runner.py`
- 🔄 Full backward compatibility with CLI
- 📊 Run history and detailed logs
- 💰 Cost tracking and breakdowns
- ✅ Comprehensive test coverage
