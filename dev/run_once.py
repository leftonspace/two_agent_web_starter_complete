#!/usr/bin/env python3
# dev/run_once.py
"""
Run a single orchestrator run with detailed summary output.

Wrapper around agent/run_mode.py that:
- Auto-detects project_config.json
- Prints configuration summary
- Estimates and displays cost
- Runs the orchestrator
- Reports results (run_id, final_status, total cost)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).resolve().parent.parent / "agent"
sys.path.insert(0, str(agent_dir))


def main() -> None:
    """Run a single orchestrator run with detailed output."""
    print("\n" + "=" * 70)
    print("  DEV TOOL: Single Run")
    print("=" * 70 + "\n")

    # Load project config
    config_path = agent_dir / "project_config.json"
    if not config_path.exists():
        print(f"❌ Error: project_config.json not found at {config_path}")
        sys.exit(1)

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Error reading project_config.json: {e}")
        sys.exit(1)

    # Extract config values
    mode = config.get("mode", "3loop")
    project_subdir = config.get("project_subdir", "unknown")
    task = config.get("task", "")
    max_rounds = config.get("max_rounds", 1)
    auto_pilot_cfg = config.get("auto_pilot", {})
    auto_pilot_enabled = auto_pilot_cfg.get("enabled", False)
    max_cost_usd = config.get("max_cost_usd", 0.0)
    cost_warning_usd = config.get("cost_warning_usd", 0.0)

    # Print configuration summary
    print("📋 Configuration Summary:")
    print(f"   Mode:             {mode}")
    print(f"   Project:          {project_subdir}")
    print(f"   Max rounds:       {max_rounds}")
    print(f"   Auto-pilot:       {'ENABLED' if auto_pilot_enabled else 'DISABLED'}")
    if auto_pilot_enabled:
        max_sub_runs = auto_pilot_cfg.get("max_sub_runs", 3)
        print(f"   Max sub-runs:     {max_sub_runs}")
    print(f"   Cost warning:     ${cost_warning_usd:.4f}")
    print(f"   Cost cap:         ${max_cost_usd:.4f}")
    print(f"\n📝 Task (truncated):")
    task_preview = task[:200] + "..." if len(task) > 200 else task
    print(f"   {task_preview}\n")

    # Estimate cost
    try:
        from cost_estimator import estimate_run_cost

        models_used = {
            "manager": config.get("manager_model", "gpt-4o-mini"),
            "supervisor": config.get("supervisor_model", "gpt-4o-mini"),
            "employee": config.get("employee_model", "gpt-4o"),
        }

        cost_estimate = estimate_run_cost(mode, max_rounds, models_used)
        print(f"💰 Estimated cost: ${cost_estimate['estimated_total_usd']:.4f}")
    except Exception as e:
        print(f"⚠️  Cost estimation failed: {e}")

    print("\n" + "=" * 70)
    print("  Starting Orchestrator Run")
    print("=" * 70 + "\n")

    # Run the orchestrator
    try:
        from run_mode import main as run_main

        run_main()

        print("\n" + "=" * 70)
        print("  ✅ Run Completed")
        print("=" * 70 + "\n")

        # Try to find and display the latest run summary
        try:
            run_logs_dir = agent_dir.parent / "run_logs"
            if run_logs_dir.exists():
                # Find most recent run directory
                run_dirs = sorted(
                    [d for d in run_logs_dir.iterdir() if d.is_dir()],
                    key=lambda d: d.stat().st_mtime,
                    reverse=True,
                )

                if run_dirs:
                    latest_run_dir = run_dirs[0]
                    summary_file = latest_run_dir / "run_summary.json"

                    if summary_file.exists():
                        summary = json.loads(summary_file.read_text(encoding="utf-8"))

                        print(f"📊 Run Results:")
                        print(f"   Run ID:          {summary.get('run_id', 'unknown')}")
                        print(f"   Final status:    {summary.get('final_status', 'unknown')}")
                        print(f"   Rounds:          {summary.get('rounds_completed', 0)}/{summary.get('max_rounds', 0)}")
                        print(f"   Safety status:   {summary.get('safety_status', 'N/A')}")

                        cost_sum = summary.get("cost_summary", {})
                        total_cost = cost_sum.get("total_usd", 0.0)
                        print(f"   Total cost:      ${total_cost:.4f}")
                        print(f"\n   Log location:    {latest_run_dir}")
                    else:
                        print("⚠️  Run summary file not found")
                else:
                    print("⚠️  No run logs found")
        except Exception as e:
            print(f"⚠️  Could not read run summary: {e}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Run interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Run failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
