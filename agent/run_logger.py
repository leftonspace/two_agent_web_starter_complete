# run_logger.py
"""
Run logging and evaluation layer for the multi-agent orchestrator.

Provides two APIs:
1. Legacy dict-based API (for backward compatibility)
2. STAGE 2 dataclass-based API (for structured logging)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# STAGE 2: Dataclass-based Structured Logging
# ══════════════════════════════════════════════════════════════════════


@dataclass
class IterationLog:
    """Log entry for a single iteration of the orchestrator loop."""
    index: int                              # Iteration number (1-based)
    role: str                               # "manager", "supervisor", "employee"
    status: str                             # "ok", "timeout", "safety_failed", etc.
    notes: str                              # Free-text summary
    safety_status: Optional[str] = None     # "passed"/"failed"/None
    timestamp: Optional[str] = None         # ISO timestamp


@dataclass
class RunSummary:
    """Complete summary of an orchestrator run."""
    run_id: str                                          # Unique identifier
    started_at: str                                      # ISO timestamp (UTC)
    finished_at: Optional[str] = None                    # ISO timestamp (UTC)
    mode: str = "3loop"                                  # "2loop" or "3loop"
    project_dir: str = ""                                # Path to project
    task: str = ""                                       # Original task description
    max_rounds: int = 1                                  # Maximum iterations allowed
    rounds_completed: int = 0                            # Actual iterations run
    final_status: str = "unknown"                        # "success", "max_rounds_reached", etc.
    safety_status: Optional[str] = None                  # "passed"/"failed"/None
    models_used: Dict[str, str] = field(default_factory=dict)    # {"manager": "...", ...}
    cost_summary: Dict[str, Any] = field(default_factory=dict)   # From cost_tracker
    iterations: List[IterationLog] = field(default_factory=list) # Per-iteration logs
    config: Dict[str, Any] = field(default_factory=dict)         # Additional config
    estimated_cost_usd: Optional[float] = None           # STAGE 3: Pre-run cost estimate


@dataclass
class SessionSummary:
    """Summary of an auto-pilot session containing multiple runs."""
    session_id: str                                      # Unique session identifier
    started_at: str                                      # ISO timestamp (UTC)
    finished_at: Optional[str] = None                    # ISO timestamp (UTC)
    task: str = ""                                       # Original task description
    max_sub_runs: int = 3                                # Maximum sub-runs allowed
    runs: List[Dict[str, Any]] = field(default_factory=list)  # List of run summaries + eval scores
    final_decision: str = "unknown"                      # "success", "max_runs_reached", "stopped", etc.
    total_cost_usd: float = 0.0                          # Total cost across all runs
    session_config: Dict[str, Any] = field(default_factory=dict)  # Session-level config


def _now_iso() -> str:
    """Return current UTC time as ISO string with milliseconds."""
    return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"


def start_run(
    mode: str,
    project_dir: str,
    task: str,
    max_rounds: int,
    models_used: Dict[str, str],
    config: Optional[Dict[str, Any]] = None,
) -> RunSummary:
    """
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
    """
    run_id = uuid.uuid4().hex[:12]  # 12-char unique ID
    started_at = _now_iso()

    return RunSummary(
        run_id=run_id,
        started_at=started_at,
        mode=mode,
        project_dir=str(project_dir),
        task=task,
        max_rounds=max_rounds,
        models_used=models_used,
        config=config or {},
    )


def log_iteration(
    run: RunSummary,
    index: int,
    role: str,
    status: str,
    notes: str,
    safety_status: Optional[str] = None,
) -> None:
    """
    Append an iteration log entry to the RunSummary.

    Args:
        run: RunSummary instance
        index: Iteration number (1-based)
        role: "manager", "supervisor", "employee"
        status: "ok", "timeout", "safety_failed", etc.
        notes: Free-text description
        safety_status: Optional "passed"/"failed"
    """
    iteration = IterationLog(
        index=index,
        role=role,
        status=status,
        notes=notes,
        safety_status=safety_status,
        timestamp=_now_iso(),
    )
    run.iterations.append(iteration)
    run.rounds_completed = len(run.iterations)


def finalize_run(
    run: RunSummary,
    final_status: str,
    safety_status: Optional[str] = None,
    cost_summary: Optional[Dict[str, Any]] = None,
) -> RunSummary:
    """
    Finalize a RunSummary with final status and cost information.

    Args:
        run: RunSummary instance
        final_status: "success", "max_rounds_reached", "timeout", "aborted", etc.
        safety_status: Optional final safety status
        cost_summary: Optional cost summary from cost_tracker

    Returns:
        Updated RunSummary instance
    """
    run.finished_at = _now_iso()
    run.final_status = final_status
    if safety_status is not None:
        run.safety_status = safety_status
    if cost_summary is not None:
        run.cost_summary = cost_summary
    return run


def save_run_summary(run: RunSummary, base_dir: str = "run_logs") -> str:
    """
    Save RunSummary to disk as JSON.

    Creates: <base_dir>/<run_id>/run_summary.json

    Args:
        run: RunSummary instance
        base_dir: Base directory for logs (default: "run_logs")

    Returns:
        Path to the saved JSON file
    """
    # Get project root (parent of agent/)
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent

    # Create run-specific directory
    run_dir = project_root / base_dir / run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON
    json_file = run_dir / "run_summary.json"
    try:
        # Convert dataclass to dict
        run_dict = asdict(run)

        # Write with nice formatting
        json_file.write_text(
            json.dumps(run_dict, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"[RunLog] Saved run summary to {json_file}")
        return str(json_file)
    except Exception as e:
        print(f"[RunLog] Failed to save run summary: {e}")
        return ""


# ══════════════════════════════════════════════════════════════════════
# STAGE 4: Session-Level Logging (Auto-Pilot)
# ══════════════════════════════════════════════════════════════════════


def start_session(
    task: str,
    max_sub_runs: int,
    session_config: Optional[Dict[str, Any]] = None,
) -> SessionSummary:
    """
    Create a new SessionSummary for tracking an auto-pilot session.

    Args:
        task: Task description for the session
        max_sub_runs: Maximum number of sub-runs allowed
        session_config: Optional session-level configuration

    Returns:
        SessionSummary instance with session_id and started_at populated
    """
    session_id = uuid.uuid4().hex[:12]  # 12-char unique ID
    started_at = _now_iso()

    return SessionSummary(
        session_id=session_id,
        started_at=started_at,
        task=task,
        max_sub_runs=max_sub_runs,
        session_config=session_config or {},
    )


def log_session_run(
    session: SessionSummary,
    run_summary: Dict[str, Any],
    eval_result: Dict[str, Any],
) -> None:
    """
    Append a run summary and evaluation to the session.

    Args:
        session: SessionSummary instance
        run_summary: RunSummary as dict (from asdict())
        eval_result: Evaluation result from self_eval.evaluate_run()
    """
    run_entry = {
        "run_id": run_summary.get("run_id"),
        "final_status": run_summary.get("final_status"),
        "rounds_completed": run_summary.get("rounds_completed"),
        "cost_usd": run_summary.get("cost_summary", {}).get("total_usd", 0.0),
        "evaluation": eval_result,
        "full_summary": run_summary,  # Include full details for later analysis
    }
    session.runs.append(run_entry)

    # Update total cost
    session.total_cost_usd += run_entry["cost_usd"]


def finalize_session(
    session: SessionSummary,
    final_decision: str,
) -> SessionSummary:
    """
    Finalize a SessionSummary with final decision.

    Args:
        session: SessionSummary instance
        final_decision: "success", "max_runs_reached", "stopped", etc.

    Returns:
        Updated SessionSummary instance
    """
    session.finished_at = _now_iso()
    session.final_decision = final_decision
    return session


def save_session_summary(session: SessionSummary, base_dir: str = "run_logs") -> str:
    """
    Save SessionSummary to disk as JSON.

    Creates: <base_dir>/<session_id>/session_summary.json

    Args:
        session: SessionSummary instance
        base_dir: Base directory for logs (default: "run_logs")

    Returns:
        Path to the saved JSON file
    """
    # Get project root (parent of agent/)
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent

    # Create session-specific directory
    session_dir = project_root / base_dir / session.session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON
    json_file = session_dir / "session_summary.json"
    try:
        # Convert dataclass to dict
        session_dict = asdict(session)

        # Write with nice formatting
        json_file.write_text(
            json.dumps(session_dict, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"[SessionLog] Saved session summary to {json_file}")
        return str(json_file)
    except Exception as e:
        print(f"[SessionLog] Failed to save session summary: {e}")
        return ""


# ══════════════════════════════════════════════════════════════════════
# LEGACY API (Backward Compatibility)
# ══════════════════════════════════════════════════════════════════════


def start_run_legacy(config: Dict[str, Any], mode: str, out_dir: Path) -> Dict[str, Any]:
    """
    Legacy dict-based API for backward compatibility.
    Create an in-memory record for this run.
    """
    project_subdir = str(config.get("project_subdir", out_dir.name))
    task = str(config.get("task", ""))

    run_record: Dict[str, Any] = {
        "run_id": f"{_now_iso()}_{mode}",
        "mode": mode,
        "project_subdir": project_subdir,
        "task": task,
        "config": {
            "max_rounds": config.get("max_rounds"),
            "use_visual_review": config.get("use_visual_review"),
            "use_git": config.get("use_git"),
            "max_cost_usd": config.get("max_cost_usd"),
            "cost_warning_usd": config.get("cost_warning_usd"),
        },
        "started_at_utc": _now_iso(),
        "finished_at_utc": None,
        "final_status": None,
        "iterations_run": 0,
        "iterations": [],
        "cost_summary": None,
        "history_folder": str(out_dir / ".history"),
    }
    return run_record


def log_iteration_legacy(run_record: Dict[str, Any], iteration_data: Dict[str, Any]) -> None:
    """
    Legacy dict-based API for backward compatibility.
    Append one iteration summary to the in-memory run_record.
    """
    iters: List[Dict[str, Any]] = run_record.setdefault("iterations", [])
    iters.append(dict(iteration_data))
    run_record["iterations_run"] = len(iters)


def finish_run_legacy(
    run_record: Dict[str, Any],
    final_status: str,
    cost_summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """
    Legacy dict-based API for backward compatibility.
    Finalize run_record and append it as one JSON line to:
      agent/run_logs/<project_subdir>_<mode>.jsonl
    """
    run_record["finished_at_utc"] = _now_iso()
    run_record["final_status"] = final_status
    run_record["cost_summary"] = cost_summary
    run_record["history_folder"] = str(out_dir / ".history")

    try:
        agent_dir = Path(__file__).resolve().parent
        logs_dir = agent_dir / "run_logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        project = run_record.get("project_subdir", "unknown_project")
        mode = run_record.get("mode", "unknown_mode")
        log_file = logs_dir / f"{project}_{mode}.jsonl"

        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(run_record, ensure_ascii=False) + "\n")

        print(f"[RunLog] Appended entry to {log_file}")
    except Exception as e:
        print(f"[RunLog] Failed to write run log: {e}")


# ══════════════════════════════════════════════════════════════════════
# Compatibility Aliases (orchestrator.py uses these names)
# ══════════════════════════════════════════════════════════════════════

# Map new names to legacy functions for existing code
start_run_dict = start_run_legacy
log_iteration_dict = log_iteration_legacy
finish_run_dict = finish_run_legacy
