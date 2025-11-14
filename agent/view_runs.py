# view_runs.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_run_logs(run_logs_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all JSONL log files from run_logs/ and return a flat list of run dicts.
    Each line in each file is one JSON object (one run).
    """
    runs: List[Dict[str, Any]] = []

    if not run_logs_dir.exists():
        return runs

    for log_file in sorted(run_logs_dir.glob("*.jsonl")):
        try:
            with log_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        if isinstance(rec, dict):
                            rec["_log_file"] = str(log_file.name)
                            runs.append(rec)
                    except json.JSONDecodeError:
                        # Skip malformed lines instead of crashing
                        continue
        except Exception as e:
            print(f"[view_runs] Could not read {log_file}: {e}")

    # Sort newest first by started_at_utc if present
    def _key(rec: Dict[str, Any]):
        return rec.get("started_at_utc", "")

    runs.sort(key=_key, reverse=True)
    return runs


def print_run_summary(run: Dict[str, Any]) -> None:
    """Print a compact summary of one run."""
    run_id = run.get("run_id", "unknown")
    mode = run.get("mode", "unknown")
    proj = run.get("project_subdir", "unknown_project")
    status = run.get("final_status", "unknown")
    started = run.get("started_at_utc", "unknown")
    finished = run.get("finished_at_utc", "unknown")
    iterations = run.get("iterations_run", 0)
    cost_summary = run.get("cost_summary") or {}
    total_cost = cost_summary.get("total_usd", 0.0)

    print("=" * 72)
    print(f"Project : {proj}")
    print(f"Mode    : {mode}")
    print(f"Run ID  : {run_id}")
    print(f"Status  : {status}")
    print(f"Started : {started}")
    print(f"Finished: {finished}")
    print(f"Iterations run: {iterations}")
    print(f"Total cost (USD, est.): {total_cost:.4f}")

    # Show quick per-iteration statuses if available
    iterations_list = run.get("iterations") or []
    if iterations_list:
        print("\n  Iterations:")
        for it in iterations_list:
            it_no = it.get("iteration")
            it_status = it.get("status", "unknown")
            it_cost = it.get("cost_total_usd", 0.0)
            tests = it.get("tests") or {}
            all_passed = tests.get("all_passed")
            print(
                f"    #{it_no}: status={it_status}, "
                f"all_passed={all_passed}, cost=${it_cost:.4f}"
            )

    print()  # blank line at end


def main():
    agent_dir = Path(__file__).resolve().parent
    run_logs_dir = agent_dir / "run_logs"

    # Arguments:
    #   python view_runs.py              -> show last 5 runs (any project)
    #   python view_runs.py projectName -> show last 5 for that project
    #   python view_runs.py projectName 10 -> last 10 for that project
    args = sys.argv[1:]
    project_filter = None
    max_to_show = 5

    if len(args) >= 1:
        project_filter = args[0].strip()
    if len(args) >= 2:
        try:
            max_to_show = int(args[1])
        except ValueError:
            max_to_show = 5

    runs = load_run_logs(run_logs_dir)
    if not runs:
        print("No run logs found in:", run_logs_dir)
        return

    if project_filter:
        runs = [r for r in runs if r.get("project_subdir") == project_filter]
        if not runs:
            print(f"No runs found for project_subdir='{project_filter}'.")
            return

    runs_to_show = runs[:max_to_show]

    print(f"Showing {len(runs_to_show)} run(s)")
    if project_filter:
        print(f"  Filter: project_subdir = {project_filter}")
    print()

    for run in runs_to_show:
        print_run_summary(run)


if __name__ == "__main__":
    main()
