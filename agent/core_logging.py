# core_logging.py
"""
Core logging system for main orchestrator runs.

STAGE 2.2 (HARDENED): Provides centralized, structured logging for the main orchestrator,
separate from safety execution logs.

Logs are written as JSONL (one JSON object per line) to:
    run_logs_main/<run_id>.jsonl

Each log entry is a LogEvent with:
- run_id: Unique identifier for this run
- timestamp: Unix timestamp (seconds since epoch)
- event_type: Type of event (start, iteration_begin, llm_call, etc.)
- payload: Dict with event-specific data
- schema_version: Log schema version for future compatibility

This is best-effort logging - failures do not crash the orchestrator.

LOG ROTATION / SIZE MANAGEMENT:
Currently, there is NO automatic log rotation or size limit enforcement.
Logs will accumulate indefinitely in run_logs_main/.

TODO (Future Stage): Implement log rotation strategy:
- Option 1: Delete logs older than N days
- Option 2: Compress old logs (gzip)
- Option 3: Limit total number of runs (keep last N runs)
- Option 4: Implement size-based rotation (truncate when directory exceeds X MB)

For now, users should manually clean up run_logs_main/ if disk space is a concern.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════

# Logs directory (relative to agent/)
LOGS_DIR = Path(__file__).resolve().parent / "run_logs_main"

# Log schema version for future evolution
# Increment this if the LogEvent structure or payload format changes significantly
LOG_SCHEMA_VERSION = "1.0"


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
        schema_version: Log schema version for future compatibility (optional, default: current version)
    """
    run_id: str
    timestamp: float
    event_type: str
    payload: Dict[str, Any]
    schema_version: str = LOG_SCHEMA_VERSION


# Event types (for documentation and validation)
# NOTE: "error", "warning", and "info" are now used in Phase 3
EVENT_TYPES = {
    # Stage 2 events (existing)
    "start": "Run started",
    "iteration_begin": "Iteration started",
    "iteration_end": "Iteration completed",
    "llm_call": "LLM API call made",
    "file_write": "File written to disk",
    "safety_check": "Safety checks executed",
    "final_status": "Run completed with final status",

    # Phase 3 events (workflow management)
    "workflow_initialized": "Workflow created with initial roadmap",
    "stage_started": "Stage execution started",
    "stage_completed": "Stage execution completed",
    "roadmap_mutated": "Roadmap changed (merge, split, reorder, etc.)",
    "stage_reopened": "Previous stage reopened for rework",
    "auto_advance": "Auto-advanced to next stage (zero findings)",

    # Phase 3 events (agent communication)
    "agent_message": "Inter-agent message sent",
    "agent_response": "Response to inter-agent message",

    # Phase 3 events (memory & regression)
    "memory_created": "Stage memory initialized",
    "memory_updated": "Stage memory updated",
    "regression_detected": "Regression detected in previous stage",
    "finding_added": "Supervisor finding added to memory",
    "decision_recorded": "Agent decision recorded",

    # Generic events (now used)
    "error": "Error occurred",
    "warning": "Warning logged",
    "info": "Informational message",

    # Stage 4 events (merge manager & git)
    "merge_manager_diff_summary": "Git diff analyzed by merge manager",
    "semantic_commit_summary": "Semantic commit message generated",
    "git_commit_attempt": "Attempted to create git commit",
    "git_commit_success": "Git commit created successfully",
    "git_commit_skipped": "Git commit skipped (no changes or disabled)",
    "git_commit_failed": "Git commit failed",

    # Stage 5 events (model routing)
    "model_selected": "Model selected by router for LLM call"
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
    - Includes schema_version for future compatibility

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
    # Create log event with schema version
    event = LogEvent(
        run_id=run_id,
        timestamp=time.time(),
        event_type=event_type,
        payload=payload,
        schema_version=LOG_SCHEMA_VERSION
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

    Handles schema version compatibility: events without schema_version field
    are treated as valid (for backward compatibility with logs created before
    schema versioning was introduced).

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
                    # Handle backward compatibility: add schema_version if missing
                    if "schema_version" not in data:
                        data["schema_version"] = "1.0"  # Assume version 1.0 for old logs
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


def log_cost_checkpoint(
    run_id: str,
    checkpoint: str,
    total_cost_usd: float,
    max_cost_usd: float,
    cost_summary: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    STAGE 5.2: Log cost checkpoint during orchestrator run.

    Args:
        run_id: Run identifier
        checkpoint: Checkpoint name (e.g., "after_planning", "iteration_1", "final")
        total_cost_usd: Current total cost in USD
        max_cost_usd: Maximum cost cap in USD (0 if no cap)
        cost_summary: Optional detailed cost breakdown from cost_tracker
        **kwargs: Additional cost-related metadata
    """
    payload = {
        "checkpoint": checkpoint,
        "total_cost_usd": round(total_cost_usd, 6),
        "max_cost_usd": round(max_cost_usd, 6) if max_cost_usd else 0.0,
        "remaining_budget_usd": (
            round(max_cost_usd - total_cost_usd, 6) if max_cost_usd > 0 else None
        ),
        "percent_of_cap": (
            round(100.0 * total_cost_usd / max_cost_usd, 2) if max_cost_usd > 0 else None
        ),
        **kwargs
    }
    if cost_summary:
        payload["cost_summary"] = cost_summary

    log_event(run_id, "cost_checkpoint", payload)


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


# ══════════════════════════════════════════════════════════════════════
# PHASE 3: Workflow & Stage Management Logging
# ══════════════════════════════════════════════════════════════════════


def log_workflow_initialized(
    run_id: str,
    roadmap_version: int,
    total_stages: int,
    stage_names: list[str],
    **kwargs
) -> None:
    """
    Log workflow initialization with initial roadmap.

    Args:
        run_id: Run identifier
        roadmap_version: Initial roadmap version
        total_stages: Number of stages in roadmap
        stage_names: List of stage names
        **kwargs: Additional metadata
    """
    payload = {
        "roadmap_version": roadmap_version,
        "total_stages": total_stages,
        "stage_names": stage_names,
        **kwargs
    }
    log_event(run_id, "workflow_initialized", payload)


def log_stage_started(
    run_id: str,
    stage_id: str,
    stage_name: str,
    stage_number: int,
    total_stages: int,
    **kwargs
) -> None:
    """
    Log stage execution start.

    Args:
        run_id: Run identifier
        stage_id: Stage identifier
        stage_name: Human-readable stage name
        stage_number: Stage number (1-indexed)
        total_stages: Total number of stages
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "stage_name": stage_name,
        "stage_number": stage_number,
        "total_stages": total_stages,
        **kwargs
    }
    log_event(run_id, "stage_started", payload)


def log_stage_completed(
    run_id: str,
    stage_id: str,
    stage_name: str,
    status: str,
    iterations: int,
    audit_count: int,
    duration_seconds: float,
    **kwargs
) -> None:
    """
    Log stage execution completion.

    Args:
        run_id: Run identifier
        stage_id: Stage identifier
        stage_name: Stage name
        status: Final status (completed, skipped, failed)
        iterations: Number of iterations
        audit_count: Number of audits performed
        duration_seconds: Stage duration
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "stage_name": stage_name,
        "status": status,
        "iterations": iterations,
        "audit_count": audit_count,
        "duration_seconds": duration_seconds,
        **kwargs
    }
    log_event(run_id, "stage_completed", payload)


def log_roadmap_mutated(
    run_id: str,
    old_version: int,
    new_version: int,
    mutation_type: str,
    reason: str,
    created_by: str,
    **kwargs
) -> None:
    """
    Log roadmap mutation.

    Args:
        run_id: Run identifier
        old_version: Previous roadmap version
        new_version: New roadmap version
        mutation_type: Type of mutation (merge, split, reorder, skip, reopen)
        reason: Reason for mutation
        created_by: Agent that requested mutation
        **kwargs: Additional metadata
    """
    payload = {
        "old_version": old_version,
        "new_version": new_version,
        "mutation_type": mutation_type,
        "reason": reason,
        "created_by": created_by,
        **kwargs
    }
    log_event(run_id, "roadmap_mutated", payload)


def log_stage_reopened(
    run_id: str,
    stage_id: str,
    stage_name: str,
    reason: str,
    regression_source: Optional[str] = None,
    **kwargs
) -> None:
    """
    Log stage being reopened for rework.

    Args:
        run_id: Run identifier
        stage_id: Stage being reopened
        stage_name: Stage name
        reason: Reason for reopening
        regression_source: Stage that caused regression (if applicable)
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "stage_name": stage_name,
        "reason": reason,
        "regression_source": regression_source,
        **kwargs
    }
    log_event(run_id, "stage_reopened", payload)


def log_auto_advance(
    run_id: str,
    stage_id: str,
    stage_name: str,
    reason: str = "Zero findings in audit",
    **kwargs
) -> None:
    """
    Log auto-advance to next stage.

    Args:
        run_id: Run identifier
        stage_id: Stage being auto-advanced
        stage_name: Stage name
        reason: Reason for auto-advance
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "stage_name": stage_name,
        "reason": reason,
        **kwargs
    }
    log_event(run_id, "auto_advance", payload)


# ══════════════════════════════════════════════════════════════════════
# PHASE 3: Inter-Agent Communication Logging
# ══════════════════════════════════════════════════════════════════════


def log_agent_message(
    run_id: str,
    message_id: str,
    from_agent: str,
    to_agent: str,
    message_type: str,
    subject: str,
    **kwargs
) -> None:
    """
    Log inter-agent message.

    Args:
        run_id: Run identifier
        message_id: Message identifier
        from_agent: Sender agent
        to_agent: Recipient agent
        message_type: Type of message
        subject: Message subject
        **kwargs: Additional metadata
    """
    payload = {
        "message_id": message_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": message_type,
        "subject": subject,
        **kwargs
    }
    log_event(run_id, "agent_message", payload)


def log_agent_response(
    run_id: str,
    response_id: str,
    original_message_id: str,
    from_agent: str,
    to_agent: str,
    **kwargs
) -> None:
    """
    Log response to inter-agent message.

    Args:
        run_id: Run identifier
        response_id: Response message identifier
        original_message_id: ID of message being responded to
        from_agent: Responder agent
        to_agent: Original sender
        **kwargs: Additional metadata
    """
    payload = {
        "response_id": response_id,
        "original_message_id": original_message_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        **kwargs
    }
    log_event(run_id, "agent_response", payload)


# ══════════════════════════════════════════════════════════════════════
# PHASE 3: Memory & Regression Logging
# ══════════════════════════════════════════════════════════════════════


def log_memory_created(
    run_id: str,
    stage_id: str,
    stage_name: str,
    **kwargs
) -> None:
    """
    Log stage memory creation.

    Args:
        run_id: Run identifier
        stage_id: Stage identifier
        stage_name: Stage name
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "stage_name": stage_name,
        **kwargs
    }
    log_event(run_id, "memory_created", payload)


def log_memory_updated(
    run_id: str,
    stage_id: str,
    update_type: str,
    description: str,
    **kwargs
) -> None:
    """
    Log stage memory update.

    Args:
        run_id: Run identifier
        stage_id: Stage identifier
        update_type: Type of update (decision, finding, clarification, note)
        description: Brief description of update
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "update_type": update_type,
        "description": description,
        **kwargs
    }
    log_event(run_id, "memory_updated", payload)


def log_regression_detected(
    run_id: str,
    current_stage_id: str,
    regressing_stage_id: str,
    issue_count: int,
    description: str,
    **kwargs
) -> None:
    """
    Log regression detection.

    Args:
        run_id: Run identifier
        current_stage_id: Stage where regression was detected
        regressing_stage_id: Stage that caused regression
        issue_count: Number of issues traced back
        description: Human-readable description
        **kwargs: Additional metadata
    """
    payload = {
        "current_stage_id": current_stage_id,
        "regressing_stage_id": regressing_stage_id,
        "issue_count": issue_count,
        "description": description,
        **kwargs
    }
    log_event(run_id, "regression_detected", payload)


def log_finding_added(
    run_id: str,
    stage_id: str,
    finding_severity: str,
    finding_category: str,
    description: str,
    **kwargs
) -> None:
    """
    Log supervisor finding added to memory.

    Args:
        run_id: Run identifier
        stage_id: Stage identifier
        finding_severity: Severity (error, warning, info)
        finding_category: Category
        description: Finding description
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "finding_severity": finding_severity,
        "finding_category": finding_category,
        "description": description,
        **kwargs
    }
    log_event(run_id, "finding_added", payload)


def log_decision_recorded(
    run_id: str,
    stage_id: str,
    agent: str,
    decision_type: str,
    description: str,
    **kwargs
) -> None:
    """
    Log agent decision recorded in memory.

    Args:
        run_id: Run identifier
        stage_id: Stage identifier
        agent: Agent making decision
        decision_type: Type of decision
        description: Decision description
        **kwargs: Additional metadata
    """
    payload = {
        "stage_id": stage_id,
        "agent": agent,
        "decision_type": decision_type,
        "description": description,
        **kwargs
    }
    log_event(run_id, "decision_recorded", payload)
