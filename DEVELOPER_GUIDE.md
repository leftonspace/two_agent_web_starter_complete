# Developer Guide - Multi-Agent Orchestrator

This guide provides everything you need to develop, test, debug, and extend the multi-agent orchestrator system.

## Table of Contents

- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Running the Orchestrator](#running-the-orchestrator)
- [Development Tools](#development-tools)
- [Configuration](#configuration)
- [Understanding Logs](#understanding-logs)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Debugging](#debugging)
- [Extending the System](#extending-the-system)

---

## Repository Structure

```
two_agent_web_starter_complete/
├── agent/                      # Core orchestrator code
│   ├── orchestrator.py         # 3-loop orchestration (Manager ↔ Supervisor ↔ Employee)
│   ├── orchestrator_2loop.py   # 2-loop orchestration (Manager ↔ Employee)
│   ├── llm.py                  # LLM interaction layer
│   ├── run_mode.py             # Entry point for runs
│   ├── run_logger.py           # Structured logging (Stages 2-4)
│   ├── auto_pilot.py           # Auto-pilot mode (Stage 4)
│   ├── self_eval.py            # Self-evaluation (Stage 4)
│   ├── exec_safety.py          # Safety orchestrator (Stage 1)
│   ├── exec_analysis.py        # Static code analysis (Stage 1)
│   ├── exec_deps.py            # Dependency scanning (Stage 1)
│   ├── cost_estimator.py       # Cost estimation (Stage 3)
│   ├── cost_tracker.py         # Cost tracking
│   ├── status_codes.py         # Normalized status constants (Stage 5)
│   ├── safe_io.py              # Safe I/O helpers (Stage 5)
│   ├── site_tools.py           # File loading utilities
│   ├── git_utils.py            # Git snapshot utilities
│   ├── prompts.py              # Prompt templates
│   ├── tests_sanity/           # Sanity tests (Stage 5)
│   └── project_config.json     # Project configuration
│
├── dev/                        # Developer tools (Stage 6)
│   ├── run_once.py             # Run single orchestrator run
│   ├── run_autopilot.py        # Run auto-pilot mode
│   ├── profile_run.py          # Profile performance
│   ├── clean_logs.py           # Clean/archive logs
│   ├── generate_fixture.py     # Generate test fixtures
│   ├── view_logs.py            # View logs in browser
│   └── templates/              # HTML templates for log viewer
│
├── docs/                       # Documentation (Stage 6)
│   ├── generate_docs.py        # Documentation generator
│   └── REFERENCE.md            # API reference (auto-generated)
│
├── .vscode/                    # VSCode configuration (Stage 6)
│   ├── launch.json             # Debug configurations
│   └── tasks.json              # Build tasks
│
├── .githooks/                  # Git hooks (Stage 6)
│   └── pre-commit              # Pre-commit validation
│
├── sites/                      # Project sites to orchestrate
│   ├── fixtures/               # Test fixture site
│   └── <your-project>/         # Your project files
│
├── run_logs/                   # Run summaries (gitignored)
├── run_logs_exec/              # Safety check logs (gitignored)
├── make.py                     # Command dispatcher (Stage 6)
└── DEVELOPER_GUIDE.md          # This file

```

---

## Quick Start

### 1. Install Dependencies

```bash
# Core dependencies (required)
pip install openai  # For LLM API calls

# Optional dependencies
pip install psutil  # For memory profiling
pip install ruff mypy  # For linting and type checking
```

### 2. Configure Your Project

Edit `agent/project_config.json`:

```json
{
  "mode": "3loop",
  "project_subdir": "your_project_name",
  "task": "Your task description here",
  "max_rounds": 3,
  "max_cost_usd": 1.0,
  "cost_warning_usd": 0.5,
  "interactive_cost_mode": "once"
}
```

### 3. Run Your First Orchestrator Run

```bash
# Using the dev tool
python3 dev/run_once.py

# Or using the make command
python3 make.py run

# Or directly
python3 agent/run_mode.py
```

---

## Running the Orchestrator

### Single Run Mode

Run the orchestrator once with your configured task:

```bash
python3 dev/run_once.py
```

This will:
- Load configuration from `project_config.json`
- Display cost estimate
- Run the orchestrator (2loop or 3loop)
- Save logs to `run_logs/<run_id>/`
- Display summary with run_id, status, cost

### Auto-Pilot Mode

Run multiple iterations with self-evaluation:

```bash
python3 dev/run_autopilot.py
```

Or enable in `project_config.json`:

```json
{
  "auto_pilot": {
    "enabled": true,
    "max_sub_runs": 3
  }
}
```

Auto-pilot will:
- Run multiple sub-runs back-to-back
- Evaluate each run (quality, safety, cost)
- Decide to continue, retry, or stop
- Save session summary to `run_logs/<session_id>/session_summary.json`

### Safety-Only Mode

Run safety checks without executing the full orchestrator:

```bash
python3 -c "from agent.exec_safety import run_safety_checks; print(run_safety_checks('sites/your_project', 'Task description'))"
```

---

## Development Tools

All tools are in the `dev/` folder and can be called via `make.py`:

### make.py - Command Dispatcher

```bash
python3 make.py <command>
```

Available commands:
- `run` - Run single orchestrator run
- `auto` - Run auto-pilot mode
- `safety` - Run safety checks only
- `clean` - Clean logs
- `docs` - Generate documentation
- `profile` - Profile a run
- `fixture` - Generate test fixture

### Individual Tools

#### run_once.py
Run a single orchestrator run with detailed output.

```bash
python3 dev/run_once.py
```

#### run_autopilot.py
Run auto-pilot mode (forces auto_pilot.enabled = true temporarily).

```bash
python3 dev/run_autopilot.py
```

#### profile_run.py
Profile runtime, CPU, and memory usage.

```bash
python3 dev/profile_run.py
```

Saves `profile.json` alongside run logs with:
- Wall-clock time
- CPU time
- Memory usage (if psutil available)
- Cost summary

#### clean_logs.py
Clean or archive run logs.

```bash
# Delete with confirmation
python3 dev/clean_logs.py

# Delete without confirmation
python3 dev/clean_logs.py --hard --yes

# Archive logs
python3 dev/clean_logs.py --archive ./archived_logs

# Include exec logs
python3 dev/clean_logs.py --exec
```

#### view_logs.py
View logs in a browser with an HTML interface.

```bash
# View latest run
python3 dev/view_logs.py --latest

# View all runs
python3 dev/view_logs.py --all

# View specific log
python3 dev/view_logs.py run_logs/<run_id>/run_summary.json
```

#### generate_fixture.py
Generate a test fixture site for testing without AI costs.

```bash
python3 dev/generate_fixture.py
```

Creates `sites/fixtures/` with simple HTML/CSS/JS files.

---

## Configuration

### project_config.json

Located at `agent/project_config.json`, this is the main configuration file.

```json
{
  "mode": "3loop",                    // "2loop" or "3loop"
  "project_subdir": "my_project",     // Folder name under sites/
  "task": "Build a landing page",     // Task description
  "max_rounds": 3,                    // Max orchestrator iterations

  // Cost control (Stage 3)
  "max_cost_usd": 1.0,                // Hard cap on API costs
  "cost_warning_usd": 0.5,            // Warning threshold
  "interactive_cost_mode": "once",    // "off", "once", "always"

  // Safety checks (Stage 1)
  "use_safety_checks": true,          // Enable safety pack

  // Git integration
  "use_git": false,                   // Create git snapshots

  // Auto-pilot (Stage 4)
  "auto_pilot": {
    "enabled": false,                 // Enable auto-pilot mode
    "max_sub_runs": 3                 // Max number of sub-runs
  },

  // Model selection (optional overrides)
  "manager_model": "gpt-4o-mini",
  "supervisor_model": "gpt-4o-mini",
  "employee_model": "gpt-4o"
}
```

### Environment Variables

Override models via environment variables:

```bash
export MANAGER_MODEL="gpt-4o-mini"
export SUPERVISOR_MODEL="gpt-4o-mini"
export EMPLOYEE_MODEL="gpt-4o"
export OPENAI_API_KEY="sk-..."
```

---

## Understanding Logs

### Run Logs Structure

```
run_logs/
└── <run_id>/
    ├── run_summary.json    # Complete run summary
    └── profile.json        # Performance profile (if profiled)
```

### run_summary.json Schema

```json
{
  "run_id": "abc123",
  "started_at": "2025-01-01T12:00:00.000Z",
  "finished_at": "2025-01-01T12:05:00.000Z",
  "mode": "3loop",
  "project_dir": "/path/to/sites/my_project",
  "task": "Task description",
  "max_rounds": 3,
  "rounds_completed": 2,
  "final_status": "completed",        // From status_codes.py
  "safety_status": "passed",          // "passed", "failed", null
  "models_used": {
    "manager": "gpt-4o-mini",
    "supervisor": "gpt-4o-mini",
    "employee": "gpt-4o"
  },
  "cost_summary": {
    "total_usd": 0.1234,
    "total_tokens": 5000,
    "breakdown": { ... }
  },
  "iterations": [
    {
      "index": 1,
      "role": "manager",
      "status": "ok",
      "notes": "Planning phase",
      "safety_status": null,
      "timestamp": "2025-01-01T12:01:00.000Z"
    }
  ],
  "config": { ... },
  "estimated_cost_usd": 0.15
}
```

### Session Logs (Auto-Pilot)

```
run_logs/
└── <session_id>/
    ├── session_summary.json    # Session-level summary
    ├── <run_id_1>/
    │   └── run_summary.json    # Individual run
    ├── <run_id_2>/
    │   └── run_summary.json
    └── ...
```

### session_summary.json Schema

```json
{
  "session_id": "xyz789",
  "started_at": "2025-01-01T12:00:00.000Z",
  "finished_at": "2025-01-01T12:20:00.000Z",
  "task": "Task description",
  "max_sub_runs": 3,
  "runs": [
    {
      "run_id": "abc123",
      "final_status": "completed",
      "rounds_completed": 2,
      "cost_usd": 0.1234,
      "evaluation": {
        "score_quality": 0.95,
        "score_safety": 1.0,
        "score_cost": 0.90,
        "overall_score": 0.94,
        "reasoning": "...",
        "recommendation": "continue"
      },
      "full_summary": { ... }
    }
  ],
  "final_decision": "success",     // From status_codes.py
  "total_cost_usd": 0.3702,
  "session_config": { ... }
}
```

---

## Coding Standards

All code follows the conventions established in STAGE 5:

### Type Hints

All public functions must have complete type hints:

```python
def process_data(input: str, max_retries: int = 3) -> Dict[str, Any]:
    """Process data with retries."""
    ...
```

### Docstrings

All modules, classes, and public functions need docstrings:

```python
def my_function(arg1: str, arg2: int) -> bool:
    """
    Short description.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When validation fails
    """
    ...
```

### Status Codes

Always use constants from `status_codes.py`:

```python
from status_codes import SUCCESS, COMPLETED, MAX_ROUNDS_REACHED

final_status = COMPLETED  # ✓ Good
final_status = "completed"  # ✗ Bad
```

### Logging Prefixes

Use standardized prefixes:

```python
print("[SYS] System message")
print("[RUN] Run-level message")
print("[AUTO] Auto-pilot message")
print("[COST] Cost-related message")
print("[SAFETY] Safety check message")
print("[LLM] LLM interaction message")
```

### Error Handling

Use safe I/O helpers from `safe_io.py`:

```python
from safe_io import safe_json_write, safe_json_read, safe_timestamp

# Instead of:
with open(path, 'w') as f:
    json.dump(data, f)

# Use:
safe_json_write(path, data)
```

---

## Testing

### Sanity Tests

Quick smoke tests to verify core functionality:

```bash
python3 agent/tests_sanity/test_sanity.py
```

Tests:
- Module imports
- Status codes
- Cost estimation
- Self-evaluation
- Run logging
- Safety checks

### Running with Fixtures

Use the generated fixture site for testing without AI costs:

```bash
# Generate fixture
python3 dev/generate_fixture.py

# Update config to use fixture
# Edit agent/project_config.json: "project_subdir": "fixtures"

# Run
python3 dev/run_once.py
```

### Linting & Type Checking

```bash
# Run ruff linter
ruff check agent/

# Run mypy type checker
mypy agent/ --ignore-missing-imports

# Format code
ruff format agent/
```

---

## Debugging

### VSCode Debugging

Use the provided launch configurations in `.vscode/launch.json`:

1. **🚀 Run Single Orchestrator Run** - Debug a single run
2. **🔄 Run Auto-Pilot Mode** - Debug auto-pilot
3. **🛡️ Run Safety Checks Only** - Debug safety pack
4. **🐛 Debug Orchestrator (3-loop)** - Step through orchestrator logic

Set breakpoints and press F5 to start debugging.

### Manual Debugging

Add breakpoints in code:

```python
import pdb; pdb.set_trace()  # Python debugger
```

Or use print debugging with logging prefixes:

```python
print(f"[DEBUG] Variable value: {my_var}")
```

### Viewing Logs

Use the log viewer for easier log analysis:

```bash
python3 dev/view_logs.py --latest
```

This opens an HTML interface in your browser with:
- Sidebar listing all runs
- Detailed run summaries
- Iteration logs
- Cost breakdowns
- Session information (for auto-pilot)

---

## Extending the System

### Adding New Roles

To add a new agent role (e.g., "Reviewer"):

1. Update `llm.py` with new model constant:
   ```python
   DEFAULT_REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "gpt-4o-mini")
   ```

2. Add prompts in `prompts.py` or `prompts_default.json`

3. Integrate into orchestrator flow in `orchestrator.py`

4. Update configuration schema in `project_config.json`

### Adding New Safety Checks

To add a new safety check (e.g., "license compliance"):

1. Create new module: `agent/exec_licenses.py`
   ```python
   def scan_licenses(project_dir: str) -> List[Dict[str, Any]]:
       """Scan for license compliance issues."""
       ...
   ```

2. Integrate in `exec_safety.py`:
   ```python
   from exec_licenses import scan_licenses

   license_issues = scan_licenses(project_dir)
   ```

3. Add to status determination logic

### Implementing New Agents

To create a new orchestration agent type:

1. Create module: `agent/orchestrator_custom.py`
2. Implement main loop similar to `orchestrator.py`
3. Add mode to `run_mode.py`:
   ```python
   if mode == "custom":
       from orchestrator_custom import main as main_custom
       main_custom(run_summary=run_summary)
   ```
4. Update config schema and documentation

### Modifying Cost Estimation

Edit `agent/cost_estimator.py`:

```python
PRICES_USD_PER_TOKEN = {
    "gpt-4o": {"prompt": 0.005 / 1000, "completion": 0.015 / 1000},
    "your-model": {"prompt": 0.001 / 1000, "completion": 0.002 / 1000},
}
```

---

## Additional Resources

- **API Reference**: See `docs/REFERENCE.md` (auto-generated from docstrings)
- **Status Codes**: See `agent/status_codes.py` for all normalized status constants
- **Safe I/O Helpers**: See `agent/safe_io.py` for error-resilient file operations
- **Sanity Tests**: See `agent/tests_sanity/test_sanity.py` for test examples

---

## Getting Help

1. Check this guide first
2. Review the API reference: `docs/REFERENCE.md`
3. Look at the source code - it's well-documented
4. Run sanity tests to verify your environment
5. Use the log viewer to understand run behavior

---

## Pre-Commit Hook (Optional)

Install the pre-commit hook to run checks before commits:

```bash
git config core.hooksPath .githooks
```

The hook will:
- Check imports
- Run sanity tests (if available)
- Run ruff (if installed)
- Run mypy (if installed)

All checks are graceful - missing tools won't fail the commit.

---

**Happy developing!** 🚀
