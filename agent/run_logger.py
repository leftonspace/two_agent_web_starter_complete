# run_logger.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _now_iso() -> str:
    """Return current UTC time as ISO string with milliseconds."""
    return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"


def start_run(config: Dict[str, Any], mode: str, out_dir: Path) -> Dict[str, Any]:
    """
    Create an in-memory record for this run.
    This does NOT write anything to disk yet.
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


def log_iteration(run_record: Dict[str, Any], iteration_data: Dict[str, Any]) -> None:
    """
    Append one iteration summary (status, tests, cost, etc.)
    to the in-memory run_record.
    """
    iters: List[Dict[str, Any]] = run_record.setdefault("iterations", [])
    iters.append(dict(iteration_data))
    run_record["iterations_run"] = len(iters)


def finish_run(
    run_record: Dict[str, Any],
    final_status: str,
    cost_summary: Dict[str, Any],
    out_dir: Path,
) -> None:
    """
    Finalize run_record and append it as one JSON line to:

      agent/run_logs/<project_subdir>_<mode>.jsonl

    Never crashes the main program — errors are only printed.
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
