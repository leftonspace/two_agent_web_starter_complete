# Two-Agent Web Starter (Complete)

A multi-agent AI orchestrator system for building web projects autonomously. This system uses multiple AI agents (Manager, Supervisor, Employee) working together to plan, build, and iterate on web projects.

## Features

### Core Orchestration (Stages 0-3)
- **2-loop mode**: Manager ↔ Employee direct collaboration
- **3-loop mode**: Manager ↔ Supervisor ↔ Employee with task phasing
- **Git integration**: Automatic commits after each iteration
- **Visual review**: DOM analysis and screenshot capture
- **Cost control**: Token tracking, warnings, and hard caps
- **Interactive gating**: Approve costs before execution

### Advanced Features (Stages 4-6)
- **Auto-pilot mode**: Multiple sub-runs with self-evaluation
- **Safety checks**: Static analysis, dependency scanning, execution safety
- **Run logging**: Structured JSON logs for all runs and sessions
- **Developer tools**: Helper scripts for common tasks
- **VSCode integration**: Debug configs and build tasks
- **Documentation**: Auto-generated API reference

### Web Dashboard (Stage 7-8) 🆕
- **Visual interface**: Clean web UI for project management
- **Background jobs**: Non-blocking execution with live progress ✨
- **Job management**: List, view, cancel, and rerun jobs ✨
- **Live log streaming**: Watch logs update in real-time ✨
- **Run history**: Browse past runs with detailed logs
- **Cost tracking**: View token usage and cost breakdowns
- **RESTful API**: Programmatic access to all features

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd two_agent_web_starter_complete

# Install dependencies
pip install -r requirements.txt

# Install web dashboard dependencies
pip install fastapi jinja2 uvicorn
```

### 2. Choose Your Interface

#### Option A: Web Dashboard (Recommended)

```bash
# Start the web server
python -m agent.webapp.app

# Open your browser to:
# http://127.0.0.1:8000
```

Then:
1. Select a project from the dropdown
2. Configure mode (2loop or 3loop), rounds, and costs
3. Enter your task description
4. Click "Start Run"
5. View results and history

#### Option B: Command Line

```bash
cd agent
python run_mode.py
```

Configure your run in `agent/project_config.json`:

```json
{
  "project_name": "My Website",
  "project_subdir": "my_project",
  "task": "Build a modern landing page with hero section",
  "max_rounds": 3,
  "mode": "3loop",
  "use_visual_review": true,
  "use_git": true,
  "max_cost_usd": 1.5,
  "cost_warning_usd": 0.8
}
```

### 3. View Results

**Web UI:**
- Browse to http://127.0.0.1:8000
- Click on a run ID to see details

**Command Line:**
```bash
# View logs in browser
python dev/view_logs.py --latest

# Or check JSON directly
cat run_logs/<run_id>/run_summary.json
```

## Project Structure

```
two_agent_web_starter_complete/
├── agent/                      # Core orchestrator code
│   ├── orchestrator.py         # 3-loop orchestrator
│   ├── orchestrator_2loop.py   # 2-loop orchestrator
│   ├── run_mode.py            # Main CLI entry point
│   ├── runner.py              # Programmatic API (Stage 7)
│   ├── cost_tracker.py        # Token and cost tracking
│   ├── run_logger.py          # Structured run logging
│   ├── auto_pilot.py          # Auto-pilot mode
│   ├── self_eval.py           # Self-evaluation
│   ├── exec_safety.py         # Safety checks
│   ├── status_codes.py        # Normalized status codes
│   ├── safe_io.py             # Safe I/O helpers
│   ├── project_config.json    # Configuration file
│   ├── webapp/                # Web dashboard (Stage 7)
│   │   ├── app.py            # FastAPI application
│   │   └── templates/        # HTML templates
│   └── tests_stage7/         # Web dashboard tests
├── sites/                     # Generated web projects
│   ├── my_project/
│   └── another_project/
├── run_logs/                  # Run history and logs
│   ├── <run_id>/
│   │   └── run_summary.json
│   └── ...
├── dev/                       # Developer tools
│   ├── run_once.py           # Run single orchestrator
│   ├── run_autopilot.py      # Run auto-pilot mode
│   ├── clean_logs.py         # Clean/archive logs
│   ├── profile_run.py        # Performance profiling
│   ├── generate_fixture.py   # Generate test fixture
│   └── view_logs.py          # View logs in browser
├── docs/                      # Documentation
│   ├── STAGE7_WEB_UI.md      # Web dashboard guide
│   ├── REFERENCE.md          # API reference
│   └── generate_docs.py      # Doc generator
├── DEVELOPER_GUIDE.md         # Developer guide
└── make.py                    # Command dispatcher
```

## Usage

### Web Dashboard

**Start the server:**
```bash
python -m agent.webapp.app
```

**Access the dashboard:**
- Home: http://127.0.0.1:8000
- Run detail: http://127.0.0.1:8000/run/<run_id>
- API: http://127.0.0.1:8000/api/projects

**Features:**
- 📋 Project selection from sites/ directory
- ⚙️ Visual configuration forms
- 🚀 One-click run execution
- 📊 Run history with filtering
- 💰 Cost breakdown per run
- 📝 Detailed iteration logs

See [docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md) for complete documentation.

### Command Line

**Single run:**
```bash
python dev/run_once.py
```

**Auto-pilot mode:**
```bash
python dev/run_autopilot.py
```

**Using make.py:**
```bash
python make.py run        # Run single orchestrator
python make.py auto       # Run auto-pilot mode
python make.py test       # Run sanity tests
python make.py docs       # Generate documentation
python make.py fixture    # Generate test fixture
python make.py view       # View logs in browser
python make.py clean      # Clean run logs
python make.py profile    # Profile a run
```

### Programmatic API

```python
from agent.runner import run_project, list_projects, list_run_history

# List available projects
projects = list_projects()

# Run a project
config = {
    "mode": "3loop",
    "project_subdir": "my_project",
    "task": "Build a landing page",
    "max_rounds": 3,
    "max_cost_usd": 1.5,
    "use_git": True,
}
run_summary = run_project(config)

# View history
history = list_run_history(limit=10)
```

## Configuration

### Project Configuration (project_config.json)

```json
{
  "project_name": "My Project",
  "project_subdir": "my_project",
  "task": "Build a modern website...",
  "max_rounds": 3,
  "mode": "3loop",
  "use_visual_review": true,
  "use_git": true,
  "prompts_file": "prompts_default.json",
  "max_cost_usd": 1.5,
  "cost_warning_usd": 0.8,
  "interactive_cost_mode": "once"
}
```

### Auto-Pilot Configuration

Add to project_config.json:

```json
{
  "auto_pilot": {
    "enabled": true,
    "max_sub_runs": 3,
    "acceptance_threshold": 0.8
  }
}
```

### Environment Variables

```bash
# Override default models
export MANAGER_MODEL=gpt-5
export SUPERVISOR_MODEL=gpt-5-mini
export EMPLOYEE_MODEL=gpt-5

# Set API keys
export OPENAI_API_KEY=your-key-here
```

## Testing

```bash
# Run all tests
pytest

# Run sanity tests
python agent/tests_sanity/test_sanity.py

# Run Stage 7 tests
pytest agent/tests_stage7/

# Run specific test file
pytest agent/tests_stage7/test_webapp.py -v

# Using make.py
python make.py test
```

## Development

### VSCode Integration

Launch configurations and tasks are provided in `.vscode/`:

**Debug Configurations:**
- Run Single Orchestrator Run
- Run Auto-Pilot Mode
- Debug Orchestrator (3-loop)
- Profile Run
- Run Sanity Tests
- Generate Documentation

**Build Tasks:**
- Run: Single Orchestrator Run
- Run: Auto-Pilot Mode
- Test: Sanity Tests
- Test: MyPy
- Test: Ruff
- Clean: Delete Logs
- Docs: Generate Reference

### Git Hooks

Install the pre-commit hook:

```bash
git config core.hooksPath .githooks
```

The hook runs:
- Import validation
- Sanity tests
- Ruff linting
- MyPy type checking

All checks are graceful - missing tools won't fail the commit.

### Documentation

**Generate API reference:**
```bash
python docs/generate_docs.py
```

**View developer guide:**
```bash
cat DEVELOPER_GUIDE.md
```

**View Stage 7 docs:**
```bash
cat docs/STAGE7_WEB_UI.md
```

## Documentation

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Complete developer documentation
- **[docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md)** - Web dashboard guide
- **[docs/STAGE8_JOB_MANAGER.md](docs/STAGE8_JOB_MANAGER.md)** - Job manager guide 🆕
- **[docs/REFERENCE.md](docs/REFERENCE.md)** - Auto-generated API reference

## Architecture

### Orchestration Flow

**3-loop mode:**
```
User → Manager (planning)
     → Supervisor (phasing)
     → Employee (implementation per phase)
     → Manager (review)
     → [iterate or approve]
```

**2-loop mode:**
```
User → Manager (planning)
     → Employee (implementation)
     → Manager (review)
     → [iterate or approve]
```

### Web Dashboard Flow (Stage 7-8)

**Stage 7 (Blocking):**
```
User → Web UI (form)
     → FastAPI app (validation)
     → runner.run_project() (API)
     → Orchestrator (execution)
     → run_logger (save results)
     → Web UI (display)
```

**Stage 8 (Background Jobs):**
```
User → Web UI (form)
     → FastAPI app (create job)
     → JobManager (background thread)
     → runner.run_project() (API)
     → Orchestrator (execution)
     → run_logger (save results)
     → Job state updated
User polls → Job detail page
          → API (get logs)
          → Live updates
```

### Key Components

- **orchestrator.py**: 3-loop orchestration logic
- **run_mode.py**: CLI entry point with cost estimation
- **runner.py**: Programmatic API for web dashboard
- **jobs.py**: Job manager for background execution (Stage 8)
- **webapp/app.py**: FastAPI web application
- **run_logger.py**: Structured logging (RunSummary, SessionSummary)
- **cost_tracker.py**: Token usage and cost tracking
- **auto_pilot.py**: Multi-run self-evaluation
- **exec_safety.py**: Safety checks and analysis

## Stages

- **Stage 0**: Baseline 2-loop orchestrator
- **Stage 1**: Safety pack (execution safety, analysis, dependency scanning)
- **Stage 2**: Run logging and evaluation layer
- **Stage 3**: Cost control and quality-of-life features
- **Stage 4**: Auto-pilot mode with self-evaluation
- **Stage 5**: Production hardening (status codes, safe I/O, tests)
- **Stage 6**: Developer experience (dev tools, VSCode, docs)
- **Stage 7**: Web dashboard with forms and history
- **Stage 8**: Job manager with background execution 🆕

## Contributing

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for:
- Coding standards
- Testing guidelines
- How to extend the system
- Architecture details

## License

[Your license here]

## Support

For issues or questions:
- Check [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- Check [docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md)
- Review existing run logs for debugging
- Check sanity tests: `python make.py test`
