# Multi-Agent Orchestrator - API Reference

*Auto-generated documentation from code docstrings*

---

## Table of Contents

- [auto_pilot](#auto_pilot)
- [code_review_bot](#code_review_bot)
- [cost_estimator](#cost_estimator)
- [cost_tracker](#cost_tracker)
- [exec_analysis](#exec_analysis)
- [exec_deps](#exec_deps)
- [exec_safety](#exec_safety)
- [git_utils](#git_utils)
- [llm](#llm)
- [orchestrator](#orchestrator)
- [orchestrator_2loop](#orchestrator_2loop)
- [prompts](#prompts)
- [run_logger](#run_logger)
- [run_mode](#run_mode)
- [safe_io](#safe_io)
- [self_eval](#self_eval)
- [site_tools](#site_tools)
- [status_codes](#status_codes)
- [tests.e2e.test_smoke_hello_kevin](#testse2etest_smoke_hello_kevin)
- [tests.integration.test_snapshots_and_files](#testsintegrationtest_snapshots_and_files)
- [tests.unit.test_cost_tracker](#testsunittest_cost_tracker)
- [tests_sanity.test_sanity](#tests_sanitytest_sanity)
- [view_runs](#view_runs)

---

## `auto_pilot`

**File:** `auto_pilot.py`

Auto-pilot orchestration for the multi-agent system.

Runs multiple sub-runs back-to-back with self-evaluation between each run.
Makes decisions to continue, retry with adjustments, or stop based on evaluation scores.

STAGE 5: Enhanced with status codes and improved error handling.

### Functions

#### `run_auto_pilot(mode, project_dir, task, max_sub_runs, max_rounds_per_run, models_used, config)`

Run auto-pilot mode: multiple sub-runs with self-evaluation.

Args:
    mode: "2loop" or "3loop"
    project_dir: Path to the project directory
    task: Task description
    max_sub_runs: Maximum number of sub-runs allowed
    max_rounds_per_run: Maximum rounds per individual run
    models_used: Dict of role -> model name
    config: Configuration dict with cost caps, etc.

Returns:
    SessionSummary instance with complete session results

---

## `code_review_bot`

**File:** `code_review_bot.py`

Simple local "code review bot" for your agent project.

- Runs Ruff (lint) and MyPy (types) on the agent folder.
- Optionally asks an LLM to summarize the findings if USE_AI_CODE_REVIEW=1.

### Functions

#### `run_static_checks()`

Run Ruff + MyPy and return their raw outputs.

#### `ask_ai_for_review(outputs)`

Optionally ask the LLM to summarize lint/type issues and suggest fixes.

#### `main()`

*No documentation available*

---

## `cost_estimator`

**File:** `cost_estimator.py`

Cost estimation module for the multi-agent orchestrator.

Provides rough cost estimates before starting a run based on:
- Mode (2loop vs 3loop)
- Max rounds
- Models used per role
- Token budgets per round

### Functions

#### `estimate_run_cost(mode, max_rounds, models_used)`

Estimate the rough upper-bound cost for a multi-agent run.

Args:
    mode: "2loop" or "3loop"
    max_rounds: Maximum number of iterations
    models_used: Dict mapping role -> model name
        e.g., {"manager": "gpt-5-mini", "supervisor": "gpt-5-nano", "employee": "gpt-5"}
    tokens_per_round_prompt: Estimated prompt tokens per round per role
    tokens_per_round_completion: Estimated completion tokens per round per role

Returns:
    Dict with structure:
    {
        "per_round": {
            "manager": {"model": "...", "prompt_tokens": ..., "completion_tokens": ..., "usd": ...},
            "supervisor": {...} or None,
            "employee": {...},
        },
        "max_rounds": max_rounds,
        "estimated_total_usd": ...,
    }

#### `format_cost_estimate(estimate, max_cost_usd, cost_warning_usd)`

Format a cost estimate as a human-readable string.

Args:
    estimate: Result from estimate_run_cost()
    max_cost_usd: Maximum cost cap (if set)
    cost_warning_usd: Warning threshold (if set)

Returns:
    Formatted multi-line string

---

## `cost_tracker`

**File:** `cost_tracker.py`

### Classes

#### `CallRecord`


#### `CostState`

**Methods:**

- **`add_call(self, role, model, prompt_tokens, completion_tokens)`**

- **`summary(self)`**


### Functions

#### `reset()`

Reset the global cost tracking state for a new run.

#### `register_call(role, model, prompt_tokens, completion_tokens)`

Register a single API call for cost accounting.

#### `get_summary()`

Get a structured summary of costs and tokens for the current run.

#### `get_total_cost_usd()`

Return the estimated total cost in USD for the current run.

#### `load_history()`

Load the shared history from HISTORY_FILE. Best-effort and safe on errors.

#### `save_history(history)`

Persist the shared history to HISTORY_FILE.

#### `append_history(log_file, project_name, task, status, extra)`

Append a history record.

Two usage modes:

1) Tests call this with an explicit `log_file` and metadata fields
   (project_name, task, status, extra). We append one JSON line to
   that file. The field is named "project" to match test expectations.

2) Runtime usage logging from llm.chat_json() passes cost-related
   fields (total_usd, prompt_tokens, completion_tokens, model) with
   log_file=None. We append to the default history file via
   load_history/save_history.

---

## `exec_analysis`

**File:** `exec_analysis.py`

Static code analysis module for the multi-agent orchestrator.

Performs basic static analysis on Python files:
- Syntax error detection
- Bare except detection
- Very long functions (>200 lines)
- TODO/FIXME detection

### Functions

#### `analyze_project(project_dir)`

Perform static analysis on all Python files in the project directory.

Args:
    project_dir: Path to the project root directory

Returns:
    List of issues found, each with:
    {
        "file": "relative/path/to/file.py",
        "line": line_number,
        "message": "description of the issue",
        "severity": "info" | "warning" | "error"
    }

---

## `exec_deps`

**File:** `exec_deps.py`

Dependency vulnerability scanning module for the multi-agent orchestrator.

Scans Python dependencies for known vulnerabilities using the OSV API.

### Functions

#### `scan_dependencies(project_dir)`

Scan dependencies in requirements.txt for known vulnerabilities.

Args:
    project_dir: Path to the project root directory

Returns:
    List of vulnerability issues found, each with:
    {
        "package": "package-name",
        "version": "version-string or 'unknown'",
        "severity": "critical" | "medium" | "low",
        "summary": "description of the vulnerability"
    }

---

## `exec_safety`

**File:** `exec_safety.py`

Safety checks orchestrator for the multi-agent system.

Coordinates static analysis, dependency scanning, and runtime tests.

STAGE 5: Enhanced with status codes and safe I/O.

### Functions

#### `run_safety_checks(project_dir, task_description)`

Run comprehensive safety checks on the project.

Performs:
- Static code analysis (syntax, code quality)
- Dependency vulnerability scanning
- Docker/runtime tests (stub for now)

Args:
    project_dir: Path to the project directory to check
    task_description: Original task description (for context)

Returns:
    {
        "static_issues": [...],
        "dependency_issues": [...],
        "docker_tests": {"status": "...", "details": "..."},
        "status": "passed" | "failed",
        "run_id": "<unique-id>",
        "timestamp": <unix-timestamp>
    }

Safety check fails if:
- Any static_issues with severity="error"
- OR any dependency_issues with severity="critical"

---

## `git_utils`

**File:** `git_utils.py`

### Functions

#### `ensure_repo(root)`

Ensure there is a Git repo at `root`.

- If Git is not installed, returns False and prints a message.
- If `.git` exists, returns True.
- Otherwise tries `git init` and returns True on success.
- Never raises; on failure returns False and prints a short reason.

#### `commit_all(root, message)`

Stage all changes and create a commit with the given message.

- If `.git` is missing, does nothing.
- If there is nothing to commit, prints a friendly message.
- Never raises; logs any errors and continues.

---

## `llm`

**File:** `llm.py`

### Functions

#### `chat_json(role, system_prompt, user_content)`

High-level helper that:
- Selects a model (manager / supervisor / employee) if not provided.
- Calls `_post` and records usage via `cost_tracker`.
- Returns parsed JSON (default) or raw text if `expect_json=False`.

`system_prompt` is the original parameter name.
`system` is an alias used by some callers (e.g. code_review_bot).
If both are provided, `system` wins.

---

## `orchestrator`

**File:** `orchestrator.py`

### Functions

#### `main(run_summary)`

Main 3-loop orchestrator function.

Args:
    run_summary: Optional RunSummary for STAGE 2 logging.
                 If provided, iterations will be logged automatically.

---

## `orchestrator_2loop`

**File:** `orchestrator_2loop.py`

### Functions

#### `main()`

*No documentation available*

---

## `prompts`

**File:** `prompts.py`

### Functions

#### `load_prompts(file_name)`

Load a persona file (e.g. prompts_default.json) and construct:

  - manager_plan_sys    (system prompt for planning)
  - manager_review_sys  (system prompt for reviewing)
  - supervisor_sys      (system prompt for phasing / persona selection)
  - employee_sys        (system prompt for building files)
  - manager_behaviour   (behaviour config from the JSON, if any)

---

## `run_logger`

**File:** `run_logger.py`

Run logging and evaluation layer for the multi-agent orchestrator.

Provides two APIs:
1. Legacy dict-based API (for backward compatibility)
2. STAGE 2 dataclass-based API (for structured logging)

STAGE 5: Enhanced with status codes and safe I/O.

### Classes

#### `IterationLog`

Log entry for a single iteration of the orchestrator loop.


#### `RunSummary`

Complete summary of an orchestrator run.

Tracks a single run from start to finish, including iterations,
costs, safety results, and final status.


#### `SessionSummary`

Summary of an auto-pilot session containing multiple runs.

Tracks an entire auto-pilot session with multiple sub-runs,
evaluations, and the final decision.


### Functions

#### `start_run(mode, project_dir, task, max_rounds, models_used, config)`

Create a new RunSummary for tracking an orchestrator run.

Args:
    mode: "2loop" or "3loop"
    project_dir: Path to the project directory
    task: Task description
    max_rounds: Maximum number of iterations
    models_used: Dict of role -> model name
    config: Optional additional configuration

Returns:
    RunSummary instance with run_id and started_at populated

#### `log_iteration(run, index, role, status, notes, safety_status)`

Append an iteration log entry to the RunSummary.

Args:
    run: RunSummary instance
    index: Iteration number (1-based)
    role: "manager", "supervisor", "employee"
    status: "ok", "timeout", "safety_failed", etc.
    notes: Free-text description
    safety_status: Optional "passed"/"failed"

#### `finalize_run(run, final_status, safety_status, cost_summary)`

Finalize a RunSummary with final status and cost information.

Args:
    run: RunSummary instance
    final_status: "success", "max_rounds_reached", "timeout", "aborted", etc.
    safety_status: Optional final safety status
    cost_summary: Optional cost summary from cost_tracker

Returns:
    Updated RunSummary instance

#### `save_run_summary(run, base_dir)`

Save RunSummary to disk as JSON.

Creates: <base_dir>/<run_id>/run_summary.json

STAGE 5: Uses safe I/O helpers for error resilience.

Args:
    run: RunSummary instance
    base_dir: Base directory for logs (default: "run_logs")

Returns:
    Path to the saved JSON file, or empty string on failure

#### `start_session(task, max_sub_runs, session_config)`

Create a new SessionSummary for tracking an auto-pilot session.

Args:
    task: Task description for the session
    max_sub_runs: Maximum number of sub-runs allowed
    session_config: Optional session-level configuration

Returns:
    SessionSummary instance with session_id and started_at populated

#### `log_session_run(session, run_summary, eval_result)`

Append a run summary and evaluation to the session.

Args:
    session: SessionSummary instance
    run_summary: RunSummary as dict (from asdict())
    eval_result: Evaluation result from self_eval.evaluate_run()

#### `finalize_session(session, final_decision)`

Finalize a SessionSummary with final decision.

Args:
    session: SessionSummary instance
    final_decision: "success", "max_runs_reached", "stopped", etc.

Returns:
    Updated SessionSummary instance

#### `save_session_summary(session, base_dir)`

Save SessionSummary to disk as JSON.

Creates: <base_dir>/<session_id>/session_summary.json

STAGE 5: Uses safe I/O helpers for error resilience.

Args:
    session: SessionSummary instance
    base_dir: Base directory for logs (default: "run_logs")

Returns:
    Path to the saved JSON file, or empty string on failure

#### `start_run_legacy(config, mode, out_dir)`

Legacy dict-based API for backward compatibility.
Create an in-memory record for this run.

#### `log_iteration_legacy(run_record, iteration_data)`

Legacy dict-based API for backward compatibility.
Append one iteration summary to the in-memory run_record.

#### `finish_run_legacy(run_record, final_status, cost_summary, out_dir)`

Legacy dict-based API for backward compatibility.
Finalize run_record and append it as one JSON line to:
  agent/run_logs/<project_subdir>_<mode>.jsonl

---

## `run_mode`

**File:** `run_mode.py`

Main entry point for the multi-agent orchestrator.

Loads configuration, performs cost estimation, and runs either:
- Auto-pilot mode (multiple sub-runs with self-evaluation)
- Single-run mode (2loop or 3loop)

STAGE 5: Enhanced with status codes and improved error handling.

### Functions

#### `main()`

*No documentation available*

---

## `safe_io`

**File:** `safe_io.py`

Safe I/O utilities for the multi-agent system.

Provides error-resilient wrappers for common file and network operations
to prevent crashes from I/O failures, malformed JSON, network issues, etc.

### Functions

#### `safe_json_read(path)`

Safely read and parse a JSON file.

Args:
    path: Path to JSON file

Returns:
    Parsed JSON dict, or None if reading/parsing fails

#### `safe_json_write(path, data)`

Safely write data to a JSON file.

Args:
    path: Path to write to
    data: Data to serialize
    indent: JSON indentation (default: 2)

Returns:
    True if successful, False otherwise

#### `safe_timestamp()`

Generate a safe ISO timestamp.

Returns:
    ISO formatted timestamp string, or fallback if datetime fails

#### `safe_file_read(path)`

Safely read a text file.

Args:
    path: Path to file
    encoding: Text encoding (default: utf-8)

Returns:
    File contents, or None if reading fails

#### `safe_file_write(path, content)`

Safely write content to a text file.

Args:
    path: Path to write to
    content: Content to write
    encoding: Text encoding (default: utf-8)

Returns:
    True if successful, False otherwise

#### `safe_mkdir(path)`

Safely create a directory (and parents).

Args:
    path: Directory path to create

Returns:
    True if successful or already exists, False on error

#### `safe_path_resolve(path_str)`

Safely resolve a path string to an absolute Path.

Args:
    path_str: Path string

Returns:
    Resolved Path object, or None if resolution fails

#### `safe_get_config_value(config, key, default)`

Safely get a configuration value with optional type casting.

Args:
    config: Configuration dictionary
    key: Key to retrieve
    default: Default value if key missing or cast fails
    cast: Optional type to cast to (int, float, str, bool)

Returns:
    Configuration value or default

---

## `self_eval`

**File:** `self_eval.py`

Self-evaluation module for the multi-agent orchestrator.

Evaluates RunSummary results to compute quality, safety, and cost scores.
Used by auto-pilot mode to decide whether to retry, adjust, or stop.

STAGE 5: Enhanced with status codes and improved docstrings.

### Functions

#### `evaluate_run(run_summary)`

Evaluate a completed run and compute quality/safety/cost scores.

Args:
    run_summary: RunSummary as a dict (from asdict() or dict-based API)
        Expected keys:
        - final_status: "completed", "max_rounds_reached", "cost_cap_exceeded", etc.
        - safety_status: "passed", "failed", or None
        - rounds_completed: int
        - max_rounds: int
        - cost_summary: dict with "total_usd"
        - config: dict with "max_cost_usd"

Returns:
    Dict with structure:
    {
        "score_quality": float (0-1),
        "score_safety": float (0-1),
        "score_cost": float (0-1),
        "overall_score": float (0-1),
        "reasoning": str,
        "recommendation": "continue" | "retry" | "stop"
    }

---

## `site_tools`

**File:** `site_tools.py`

### Classes

#### `_SimpleHTMLAnalyzer`

**Methods:**

- **`__init__(self)`**

- **`handle_starttag(self, tag, attrs)`**

- **`handle_endtag(self, tag)`**

- **`handle_data(self, data)`**


### Functions

#### `load_existing_files(root)`

Load existing project files into a dict: { 'relative/path': 'content' }.
Only picks web-related files (html, css, js, etc.).
Skips .git and .history folders to avoid submodule confusion.

#### `summarize_files_for_manager(files)`

Summarize files without sending full code back every time.

#### `analyze_site(index_path)`

Very lightweight 'visual' analysis:
- Parses title, headings, links, and buttons from index.html.
- No screenshots, no external dependencies.

Returns:
  {
    "dom_info": { ... },
    "screenshot_path": None
  }

---

## `status_codes`

**File:** `status_codes.py`

Normalized status codes for the multi-agent system.

All modules must use these constants instead of raw strings to ensure
consistency across run summaries, session summaries, and status reporting.

### Functions

#### `is_terminal_status(status)`

Check if a run status is terminal (no further processing needed).

Args:
    status: Run status code

Returns:
    True if status indicates run is finished

#### `is_success_status(status)`

Check if a run status indicates successful completion.

Args:
    status: Run status code

Returns:
    True if status indicates success

#### `is_failure_status(status)`

Check if a run status indicates failure.

Args:
    status: Run status code

Returns:
    True if status indicates failure

---

## `tests.e2e.test_smoke_hello_kevin`

**File:** `tests/e2e/test_smoke_hello_kevin.py`

### Functions

#### `test_project_config_loads_and_has_basic_keys()`

*No documentation available*

#### `test_orchestrator_module_imports_and_has_main()`

*No documentation available*

---

## `tests.integration.test_snapshots_and_files`

**File:** `tests/integration/test_snapshots_and_files.py`

### Functions

#### `test_site_tools_imports()`

Lightweight integration check:
- agent/site_tools.py is importable

---

## `tests.unit.test_cost_tracker`

**File:** `tests/unit/test_cost_tracker.py`

### Functions

#### `test_register_and_summary_basic()`

*No documentation available*

#### `test_get_total_cost_usd_matches_summary()`

*No documentation available*

#### `test_append_history_creates_file(tmp_path)`

*No documentation available*

---

## `tests_sanity.test_sanity`

**File:** `tests_sanity/test_sanity.py`

Sanity tests for the multi-agent system.

Run with: python3 -m pytest agent/tests_sanity/ -v
Or simply: python3 agent/tests_sanity/test_sanity.py

### Functions

#### `test_imports()`

Test that all core modules import without errors.

#### `test_cost_estimation()`

Test cost estimation with dummy data.

#### `test_self_evaluation()`

Test self-evaluation with synthetic RunSummary.

#### `test_safety_checks()`

Test safety checks on empty temporary directory.

#### `test_run_logger()`

Test run logger dataclass creation.

#### `test_status_codes()`

Test status codes module.

#### `run_all_tests()`

Run all sanity tests.

---

## `view_runs`

**File:** `view_runs.py`

### Functions

#### `load_run_logs(run_logs_dir)`

Load all JSONL log files from run_logs/ and return a flat list of run dicts.
Each line in each file is one JSON object (one run).

#### `print_run_summary(run)`

Print a compact summary of one run.

#### `main()`

*No documentation available*

---

## Notes

This documentation is automatically generated from code docstrings.
For more detailed information, consult the source code directly.

To regenerate this documentation, run:
```bash
python3 docs/generate_docs.py
```
