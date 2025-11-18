# core_logging.py
"""
Core logging system for main orchestrator runs.

STAGE 2.2: Provides centralized, structured logging for the main orchestrator,
separate from safety execution logs.

Logs are written as JSONL (one JSON object per line) to:
    run_logs_main/<run_id>.jsonl

Each log entry is a LogEvent with:
- run_id: Unique identifier for this run
- timestamp: Unix timestamp (seconds since epoch)
- event_type: Type of event (start, iteration_begin, llm_call, etc.)
- payload: Dict with event-specific data

This is best-effort logging - failures do not crash the orchestrator.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict


# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════

# Logs directory (relative to agent/)
LOGS_DIR = Path(__file__).resolve().parent / "run_logs_main"


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class LogEvent:
    """
    A single log event in the orchestrator run.

    Attributes:
        run_id: Unique identifier for the run
        timestamp: Unix timestamp (seconds since epoch, with milliseconds)
        event_type: Type of event (see EVENT_TYPES below)
        payload: Event-specific data as a dict
    """
    run_id: str
    timestamp: float
    event_type: str
    payload: Dict[str, Any]


# Event types (for documentation and validation)
EVENT_TYPES = {
    "start": "Run started",
    "iteration_begin": "Iteration started",
    "iteration_end": "Iteration completed",
    "llm_call": "LLM API call made",
    "file_write": "File written to disk",
    "safety_check": "Safety checks executed",
    "final_status": "Run completed with final status",
    "error": "Error occurred",
    "warning": "Warning logged",
    "info": "Informational message"
}


# ══════════════════════════════════════════════════════════════════════
# Public API
# ══════════════════════════════════════════════════════════════════════


def new_run_id() -> str:
    """
    Generate a unique run ID for a main orchestrator run.

    Returns:
        12-character hex string (e.g., "a1b2c3d4e5f6")
    """
    return uuid.uuid4().hex[:12]


def log_event(run_id: str, event_type: str, payload: Dict[str, Any]) -> None:
    """
    Append a JSONL log entry to run_logs_main/<run_id>.jsonl.

    This is best-effort logging:
    - Ensures the directory exists
    - Creates the log file if it doesn't exist
    - Appends a JSON line
    - Does NOT crash the program if logging fails (prints warning to stderr)

    Args:
        run_id: Unique identifier for this run
        event_type: Type of event (see EVENT_TYPES)
        payload: Event-specific data (must be JSON-serializable)

    Example:
        log_event("abc123", "start", {
            "project_folder": "/path/to/project",
            "task_description": "Build a website",
            "config": {...}
        })
    """
    # Create log event
    event = LogEvent(
        run_id=run_id,
        timestamp=time.time(),
        event_type=event_type,
        payload=payload
    )

    # Ensure logs directory exists
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[CoreLog] Warning: Failed to create logs directory: {e}", file=sys.stderr)
        return

    # Get log file path
    log_file = LOGS_DIR / f"{run_id}.jsonl"

    # Write log entry
    try:
        with log_file.open("a", encoding="utf-8") as f:
            json_line = json.dumps(asdict(event), ensure_ascii=False)
            f.write(json_line + "\n")
    except Exception as e:
        print(f"[CoreLog] Warning: Failed to write log entry: {e}", file=sys.stderr)
        # Don't crash - logging is best-effort


def load_run_events(run_id: str) -> list[LogEvent]:
    """
    Load all log events for a given run ID.

    Args:
        run_id: Run identifier

    Returns:
        List of LogEvent objects, or empty list if log file doesn't exist
        or if there are parsing errors (malformed entries are skipped)
    """
    log_file = LOGS_DIR / f"{run_id}.jsonl"

    if not log_file.exists():
        return []

    events = []

    try:
        with log_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    event = LogEvent(**data)
                    events.append(event)
                except (json.JSONDecodeError, TypeError) as e:
                    print(
                        f"[CoreLog] Warning: Skipping malformed log entry "
                        f"(line {line_num}): {e}",
                        file=sys.stderr
                    )
                    continue
    except Exception as e:
        print(f"[CoreLog] Warning: Failed to load log file {log_file}: {e}", file=sys.stderr)

    return events


def get_run_summary(run_id: str) -> Dict[str, Any]:
    """
    Generate a summary of a run from its log events.

    Computes:
    - Start and end timestamps
    - Duration
    - Number of iterations
    - Models used
    - Safety check status
    - Final status

    Args:
        run_id: Run identifier

    Returns:
        Dict with summary information, or empty dict if no logs found
    """
    events = load_run_events(run_id)

    if not events:
        return {}

    # Extract summary info
    start_time = None
    end_time = None
    iterations = set()
    models = set()
    safety_status = None
    final_status = None

    for event in events:
        # Track start and end times
        if event.event_type == "start":
            start_time = event.timestamp
        elif event.event_type == "final_status":
            end_time = event.timestamp
            final_status = event.payload.get("status")

        # Track iterations
        if event.event_type in ("iteration_begin", "iteration_end"):
            iteration = event.payload.get("iteration")
            if iteration is not None:
                iterations.add(iteration)

        # Track models
        if event.event_type == "llm_call":
            model = event.payload.get("model")
            if model:
                models.add(model)

        # Track safety checks
        if event.event_type == "safety_check":
            safety_status = event.payload.get("summary_status")

    # Compute duration
    duration = None
    if start_time and end_time:
        duration = end_time - start_time

    return {
        "run_id": run_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "num_iterations": len(iterations),
        "models_used": sorted(models),
        "safety_status": safety_status,
        "final_status": final_status,
        "total_events": len(events)
    }


# ══════════════════════════════════════════════════════════════════════
# Helper Functions (for specific event types)
# ══════════════════════════════════════════════════════════════════════


def log_start(
    run_id: str,
    project_folder: str,
    task_description: str,
    config: Dict[str, Any]
) -> None:
    """
    Log the start of a run.

    Args:
        run_id: Run identifier
        project_folder: Path to project directory
        task_description: Task description
        config: Configuration dict (sanitized - no secrets)
    """
    log_event(run_id, "start", {
        "project_folder": project_folder,
        "task_description": task_description,
        "config": config
    })


def log_iteration_begin(
    run_id: str,
    iteration: int,
    mode: str,
    **kwargs
) -> None:
    """
    Log the beginning of an iteration.

    Args:
        run_id: Run identifier
        iteration: Iteration number
        mode: "2loop" or "3loop"
        **kwargs: Additional iteration metadata
    """
    payload = {
        "iteration": iteration,
        "mode": mode,
        **kwargs
    }
    log_event(run_id, "iteration_begin", payload)


def log_iteration_end(
    run_id: str,
    iteration: int,
    status: str,
    **kwargs
) -> None:
    """
    Log the end of an iteration.

    Args:
        run_id: Run identifier
        iteration: Iteration number
        status: "approved", "needs_changes", etc.
        **kwargs: Additional iteration results
    """
    payload = {
        "iteration": iteration,
        "status": status,
        **kwargs
    }
    log_event(run_id, "iteration_end", payload)


def log_llm_call(
    run_id: str,
    role: str,
    model: str,
    prompt_length: int,
    **kwargs
) -> None:
    """
    Log an LLM API call.

    Args:
        run_id: Run identifier
        role: "manager", "employee", "supervisor"
        model: Model name
        prompt_length: Length of prompt (characters or tokens)
        **kwargs: Additional LLM call metadata (e.g., response_length, cost)
    """
    payload = {
        "role": role,
        "model": model,
        "prompt_length": prompt_length,
        **kwargs
    }
    log_event(run_id, "llm_call", payload)


def log_file_write(
    run_id: str,
    files: list[str],
    summary: str = "",
    **kwargs
) -> None:
    """
    Log file write operations.

    Args:
        run_id: Run identifier
        files: List of file paths written
        summary: Brief summary of what was written
        **kwargs: Additional metadata
    """
    payload = {
        "files": files,
        "file_count": len(files),
        "summary": summary,
        **kwargs
    }
    log_event(run_id, "file_write", payload)


def log_safety_check(
    run_id: str,
    summary_status: str,
    error_count: int,
    warning_count: int,
    safety_run_id: str = "",
    **kwargs
) -> None:
    """
    Log safety check execution.

    Args:
        run_id: Run identifier
        summary_status: "passed" or "failed"
        error_count: Number of error-level issues
        warning_count: Number of warning-level issues
        safety_run_id: Safety pack run ID (if separate)
        **kwargs: Additional safety check metadata
    """
    payload = {
        "summary_status": summary_status,
        "error_count": error_count,
        "warning_count": warning_count,
        "safety_run_id": safety_run_id,
        **kwargs
    }
    log_event(run_id, "safety_check", payload)


def log_final_status(
    run_id: str,
    status: str,
    reason: str = "",
    iterations: int = 0,
    **kwargs
) -> None:
    """
    Log the final status of a run.

    Args:
        run_id: Run identifier
        status: "success", "aborted", "failed", etc.
        reason: Reason for the final status
        iterations: Number of iterations completed
        **kwargs: Additional final status metadata
    """
    payload = {
        "status": status,
        "reason": reason,
        "iterations": iterations,
        **kwargs
    }
    log_event(run_id, "final_status", payload)
