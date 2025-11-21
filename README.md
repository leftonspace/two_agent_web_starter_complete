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

### Web Dashboard (Stage 7-11) 🆕
- **Visual interface**: Clean web UI for project management
- **Background jobs**: Non-blocking execution with live progress ✨
- **Job management**: List, view, cancel, and rerun jobs ✨
- **Live log streaming**: Watch logs update in real-time ✨
- **Project explorer**: Browse files, view snapshots, compare versions ✨
- **Diff viewer**: Interactive comparison between iterations ✨
- **Quality assurance**: Automated quality checks with configurable gates ✨
- **QA dashboard**: View quality status, issues, and metrics ✨
- **Analytics dashboard**: Comprehensive metrics, trends, and insights ✨
- **Cost analytics**: Track spending, budgets, and model costs ✨
- **Performance metrics**: Duration, token usage, and efficiency trends ✨
- **Data export**: Download analytics as JSON or CSV ✨
- **Run history**: Browse past runs with detailed logs
- **Cost tracking**: View token usage and cost breakdowns
- **RESTful API**: Programmatic access to all features

### Conversational Agent (Phase 7.1) 🚀
- **Natural language interface**: Chat with the system instead of writing mission files ✨
- **Intent understanding**: Automatically parses requests and selects appropriate tools ✨
- **Multi-step planning**: Breaks complex tasks into executable steps ✨
- **Background execution**: Long-running tasks execute asynchronously ✨
- **Web chat UI**: Interactive chat interface at `/chat` ✨
- **CLI chat mode**: Command-line chat with `/status`, `/task`, `/help` commands ✨
- **Task tracking**: Monitor active tasks and their progress in real-time ✨
- **Context awareness**: Maintains conversation history for better understanding ✨

### Action Execution Tools (Phase 7.4) 🎯
- **Domain purchase**: Buy domains via Namecheap API with approval workflow ✨
- **Website deployment**: Deploy to Vercel (auto-creates GitHub repo, pushes code, deploys) ✨
- **SMS messaging**: Send SMS via Twilio for notifications and alerts ✨
- **Payment processing**: Accept payments via Stripe with refund support ✨
- **Approval workflows**: User approval required for paid or risky actions ✨
- **Cost estimation**: Know the cost before executing any action ✨
- **Rollback support**: Undo actions when possible (refunds, deletions) ✨
- **Risk assessment**: LOW/MEDIUM/HIGH/CRITICAL risk levels with 2FA for critical actions ✨
- **Audit logging**: Complete trail of all action attempts and approvals ✨
- **Dry-run mode**: Test actions without actually executing them ✨

### Meeting Platform Integration (Phase 7A.1) 🎤
- **Zoom integration**: Join Zoom meetings as a participant, capture audio streams ✨
- **Microsoft Teams**: Join Teams meetings via Graph API with audio capture ✨
- **Live audio capture**: Record in-person meetings using microphone (PyAudio) ✨
- **Participant management**: List meeting participants and their status ✨
- **Chat integration**: Send messages to meeting chat automatically ✨
- **Platform abstraction**: Uniform API across Zoom, Teams, and live audio ✨
- **Privacy compliance**: Configurable recording announcements and consent handling ✨
- **Meeting lifecycle**: Connect → Join → Capture → Transcribe → Leave workflow ✨

### Real-Time Speech Transcription (Phase 7A.2) 🎙️
- **Multi-provider support**: Deepgram (streaming), OpenAI Whisper (batch), Google, Azure ✨
- **Automatic failover**: Switches to backup provider if primary fails ✨
- **True streaming**: <100ms latency with Deepgram WebSocket streaming ✨
- **High accuracy**: Best-in-class accuracy with OpenAI Whisper ✨
- **Punctuation**: Automatic punctuation and capitalization ✨
- **Multi-language**: Supports 99+ languages (Whisper), 36+ languages (Deepgram) ✨
- **Interim results**: Real-time interim transcripts before final results ✨
- **Confidence scores**: Quality metrics for each transcript segment ✨
- **Latency optimization**: <2s for Whisper, <100ms for Deepgram ✨

### Speaker Diarization (Phase 7A.3) 👥
- **Speaker segmentation**: Identifies who spoke when in meetings (95%+ accuracy) ✨
- **Voice fingerprinting**: Creates 512-dimensional voice embeddings for recognition ✨
- **Speaker identification**: Matches voices to known speakers across meetings ✨
- **Platform integration**: Combines voice data with Zoom/Teams participant lists ✨
- **Speaker mapping**: Maps anonymous speaker IDs to actual people ✨
- **Transcript attribution**: Combines transcripts with speaker information ✨
- **Known speaker database**: Registers speakers with voice samples for future meetings ✨
- **Pyannote.audio**: State-of-the-art deep learning models for diarization ✨
- **Automatic speaker count**: Detects number of speakers from meeting participants ✨
- **Speaker statistics**: Tracks who spoke, when, and for how long ✨

### Meeting Intelligence & Real-Time Action (Phase 7A.4) 🧠
- **Action item extraction**: Automatically identifies tasks from meeting discussion ✨
- **Decision tracking**: Captures decisions with rationale and alternatives considered ✨
- **Question identification**: Tracks questions needing answers (answered/unanswered) ✨
- **Real-time analysis**: Analyzes transcripts every 30 seconds during meetings ✨
- **Smart execution**: Executes simple, safe tasks immediately during meetings ✨
- **Meeting context**: Accumulates topics, decisions, and action items throughout session ✨
- **Action types**: Query data, search info, create documents, send messages, schedule meetings ✨
- **Chat integration**: Announces actions in meeting chat for transparency ✨
- **Meeting summaries**: Generates comprehensive summaries with action items, decisions, questions ✨
- **Safety controls**: Configurable limits on actions per meeting and confirmation requirements ✨

### Execution Strategy Decider (Phase 7B.1) 🎯
- **Intelligent strategy selection**: Analyzes tasks to choose optimal execution approach ✨
- **4 execution modes**: Direct (JARVIS solo), Reviewed (Employee+Supervisor), Full Loop (Manager+Employee+Supervisor), Human Approval ✨
- **Complexity analysis**: Scores tasks 0-10 based on code generation, APIs, file changes, steps ✨
- **Risk assessment**: Evaluates production impact, reversibility, security, downtime risk ✨
- **Cost estimation**: Predicts LLM API costs before execution ✨
- **Manual overrides**: Predefined patterns for known tasks (deploy→approval, query→direct) ✨
- **Urgency handling**: Immediate tasks skip review (unless high risk) ✨
- **Conservative by default**: Overestimates complexity/risk for safety ✨
- **Decision rationale**: Explains why each strategy was chosen ✨
- **Timeout suggestions**: Recommends appropriate timeouts per complexity level ✨

### Direct Execution Mode (Phase 7B.2) ⚡
- **Fast path execution**: JARVIS executes simple tasks immediately without multi-agent review ✨
- **7 action types**: query_database, search_info, create_document, send_message, calculate, api_call, file_read ✨
- **Safety-first design**: Only whitelisted actions, read-only by default ✨
- **Database safety**: Blocks UPDATE, DELETE, INSERT, DROP, ALTER, CREATE - allows SELECT only ✨
- **API safety**: Blocks POST, PUT, PATCH, DELETE - allows GET and HEAD only ✨
- **File safety**: Blocks access to system directories (/etc, /sys, /proc, C:\Windows) ✨
- **Timeout protection**: 30-second max execution time prevents hung tasks ✨
- **Automatic validation**: Validates results before returning ✨
- **LLM-powered planning**: Uses GPT-4o-mini for fast action planning ✨
- **Error handling**: Graceful failures with detailed error messages ✨

### Self-Optimization (Stage 12) 🆕
- **Project profiling**: Historical behavior analysis per project ✨
- **Intelligent recommendations**: Data-driven optimization suggestions ✨
- **Prompt strategies**: A/B testing for different prompt sets ✨
- **Auto-tuning**: Automatic application of recommendations ✨
- **Confidence scoring**: High/medium/low confidence levels ✨
- **Safety mechanisms**: Minimum data requirements and graceful fallbacks ✨
- **Tuning dashboard**: View recommendations and control auto-tune ✨
- **Quality-first optimization**: 70/30 QA vs cost weighting ✨

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

#### Option B: Conversational Chat (New! 🚀)

Chat naturally with the system without writing mission files:

**Web Chat:**
```bash
# Start web server
python -m agent.webapp.app

# Navigate to http://127.0.0.1:8000/chat
```

Then chat naturally:
```
You: Format the code in src/
Agent: ✓ Code formatted successfully

You: Run the test suite
Agent: ✓ 47 tests passed

You: Create a portfolio website
Agent: I'll build that! Working on 5 steps...
```

**CLI Chat:**
```bash
python -m agent.cli_chat
```

See [docs/CONVERSATIONAL_AGENT.md](docs/CONVERSATIONAL_AGENT.md) for full guide.

#### Option C: Command Line

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
│   ├── jobs.py                # Job manager (Stage 8)
│   ├── file_explorer.py       # File & snapshot explorer (Stage 9)
│   ├── analytics.py           # Analytics engine (Stage 11)
│   ├── brain.py               # Self-optimization engine (Stage 12)
│   ├── cost_tracker.py        # Token and cost tracking
│   ├── run_logger.py          # Structured run logging
│   ├── auto_pilot.py          # Auto-pilot mode
│   ├── self_eval.py           # Self-evaluation
│   ├── exec_safety.py         # Safety checks
│   ├── status_codes.py        # Normalized status codes
│   ├── safe_io.py             # Safe I/O helpers
│   ├── project_config.json    # Configuration file
│   ├── webapp/                # Web dashboard (Stage 7-12)
│   │   ├── app.py            # FastAPI application
│   │   └── templates/        # HTML templates
│   ├── tests_stage7/         # Web dashboard tests
│   ├── tests_stage8/         # Job manager tests
│   ├── tests_stage9/         # Project explorer tests
│   ├── tests_stage10/        # QA pipeline tests
│   ├── tests_stage11/        # Analytics tests
│   └── tests_stage12/        # Self-optimization tests
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
│   ├── STAGE9_PROJECT_EXPLORER.md  # Project explorer guide
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
- 📁 Project file explorer (Stage 9)
- 📸 Snapshot browsing (Stage 9)
- 🔄 Version comparison & diff viewer (Stage 9)

See [docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md) for complete dashboard documentation.

**Project Explorer (Stage 9):**

Browse and explore your generated projects:

```bash
# Navigate to Projects in the web dashboard
# http://127.0.0.1:8000/projects
```

Features:
- 🗂️ **File Tree Browser**: Navigate project files with expand/collapse
- 📄 **File Viewer**: View file contents with syntax highlighting
- 📸 **Snapshot Browser**: Explore iteration history
- 🔄 **Diff Viewer**: Compare versions with unified diff
- 🔗 **Job Integration**: Direct links from job pages to project files

See [docs/STAGE9_PROJECT_EXPLORER.md](docs/STAGE9_PROJECT_EXPLORER.md) for complete explorer documentation.

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

### Test Organization

The project includes comprehensive test coverage across all stages:

```
agent/
├── tests_sanity/          # Smoke tests for core functionality
├── tests_stage7/          # Web dashboard tests
├── tests_stage8/          # Job manager tests
├── tests_stage9/          # Project explorer tests
├── tests_stage10/         # QA pipeline tests
├── tests_stage11/         # Analytics tests
├── tests_stage12/         # Self-optimization tests
├── tests_shared/          # Reusable fixtures and helpers
└── tests_e2e/             # End-to-end integration tests
```

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run tests by stage:**
```bash
# Stage 7: Web dashboard
pytest agent/tests_stage7/ -v

# Stage 8: Job manager
pytest agent/tests_stage8/ -v

# Stage 9: Project explorer
pytest agent/tests_stage9/ -v

# Stage 10: QA pipeline
pytest agent/tests_stage10/ -v

# Stage 11: Analytics
pytest agent/tests_stage11/ -v

# Stage 12: Self-optimization
pytest agent/tests_stage12/ -v
```

**Run specific test files:**
```bash
# Web API endpoints
pytest agent/tests_stage7/test_webapp.py -v

# QA edge cases
pytest agent/tests_stage10/test_qa_edge_cases.py -v

# E2E pipeline test
pytest agent/tests_e2e/test_full_pipeline.py -v
```

**Run with coverage:**
```bash
pytest --cov=agent --cov-report=html
open htmlcov/index.html  # View coverage report
```

**Run E2E tests (marked with @pytest.mark.e2e):**
```bash
pytest -m e2e -v
```

**Using make.py:**
```bash
python make.py test        # Run sanity tests
```

### Test Coverage by Stage

**Stage 7 - Web Dashboard:**
- `test_webapp.py`: FastAPI routes, job creation, error handling
- `test_runner.py`: Programmatic API, integration tests

**Stage 8 - Job Manager:**
- `test_job_manager.py`: Job CRUD, state persistence, background execution
- `test_job_endpoints.py`: Job API endpoints, cancellation, log streaming

**Stage 9 - Project Explorer:**
- `test_webapp_routes.py`: File tree, snapshots, diff viewer, path traversal protection
- `test_file_explorer.py`: File system operations, snapshot management

**Stage 10 - QA Pipeline:**
- `test_webapp_qa_endpoints.py`: QA API endpoints (9 tests)
- `test_runner_qa_integration.py`: QA integration with runner (7 tests)
- `test_qa_edge_cases.py`: Edge cases and error conditions (20+ tests)
  - Missing HTML tags (title, meta, lang, h1)
  - Accessibility issues (images without alt, empty buttons)
  - Code quality (large files, excessive console.logs)
  - Smoke test failures and timeouts
  - Malformed HTML and empty projects
  - Config handling and report serialization

**Stage 11 - Analytics:**
- `test_analytics.py`: Metrics aggregation, cost tracking, trends
- `test_analytics_endpoints.py`: Analytics API, data export

**Stage 12 - Self-Optimization:**
- `test_brain.py`: Recommendations, profiling, auto-tuning
- `test_brain_endpoints.py`: Tuning API, confidence scoring

**End-to-End Tests:**
- `test_full_pipeline.py`: Complete workflow testing
  - Job creation and polling
  - QA execution and reporting
  - Analytics integration
  - Tuning endpoint verification
  - Failure handling scenarios
  - Concurrent job management

### Shared Test Fixtures

The `tests_shared/fixtures.py` module provides reusable test fixtures:

```python
from agent.tests_shared.fixtures import (
    temp_agent_dir,              # Temporary directory structure
    sample_project_dir,           # Sample HTML/CSS/JS project
    sample_project_with_snapshots, # Project with iteration history
    sample_run_summary,           # Mock run data
    sample_job,                   # Mock Job object
    sample_qa_config,             # QA configuration
    sample_qa_report,             # QA report data
    create_minimal_html_project,  # Helper function
)
```

### Writing New Tests

**Example test structure:**

```python
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from webapp.app import app
    return TestClient(app)

def test_example_endpoint(client):
    """Test description."""
    response = client.get("/api/example")
    assert response.status_code == 200
    assert "expected_key" in response.json()
```

**Best practices:**
- Use descriptive test names: `test_<what>_<condition>`
- Mock heavy operations (LLM calls, file I/O)
- Use temporary directories (`tmp_path` fixture)
- Test both success and error cases
- Verify status codes, data structure, and error messages
- Use shared fixtures to reduce duplication

### Continuous Integration

GitHub Actions CI workflow runs on every push:

```yaml
# .github/workflows/tests.yml
- Python 3.9+ compatibility
- All unit tests
- E2E tests (optional)
- Coverage reporting
```

To run the same checks locally:
```bash
pytest --cov=agent --cov-report=term
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
- **[docs/STAGE8_JOB_MANAGER.md](docs/STAGE8_JOB_MANAGER.md)** - Job manager guide
- **[docs/STAGE9_PROJECT_EXPLORER.md](docs/STAGE9_PROJECT_EXPLORER.md)** - Project explorer guide
- **[docs/STAGE10_QA_PIPELINE.md](docs/STAGE10_QA_PIPELINE.md)** - Quality assurance guide
- **[docs/STAGE11_ANALYTICS_DASHBOARD.md](docs/STAGE11_ANALYTICS_DASHBOARD.md)** - Analytics & insights guide 🆕
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
- **analytics.py**: Analytics engine with aggregations (Stage 11)
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
- **Stage 8**: Job manager with background execution
- **Stage 9**: Project explorer with snapshots and diff viewer
- **Stage 10**: Quality assurance pipeline with automated checks
- **Stage 11**: Analytics & insights dashboard
- **Stage 12**: Self-optimization & auto-tuning layer ("brain") 🆕

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
