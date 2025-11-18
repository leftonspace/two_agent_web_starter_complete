#!/usr/bin/env python3
# dev/run_autopilot.py
"""
Run auto-pilot mode with detailed session summary.

Forces auto_pilot.enabled = true and runs the orchestrator in auto-pilot mode.
Reports session results: session_id, sub-runs, final decision, best score.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).resolve().parent.parent / "agent"
sys.path.insert(0, str(agent_dir))


def main() -> None:
    """Run auto-pilot mode with detailed session reporting."""
    print("\n" + "=" * 70)
    print("  DEV TOOL: Auto-Pilot Mode")
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

    # Force auto-pilot mode
    if "auto_pilot" not in config:
        config["auto_pilot"] = {}

    config["auto_pilot"]["enabled"] = True

    # Set default max_sub_runs if not specified
    if "max_sub_runs" not in config["auto_pilot"]:
        config["auto_pilot"]["max_sub_runs"] = 3

    # Write back config temporarily
    original_config = config_path.read_text(encoding="utf-8")
    try:
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

        # Extract config values
        mode = config.get("mode", "3loop")
        project_subdir = config.get("project_subdir", "unknown")
        max_sub_runs = config["auto_pilot"]["max_sub_runs"]
        max_rounds_per_run = config.get("max_rounds", 1)

        print("📋 Auto-Pilot Configuration:")
        print(f"   Mode:             {mode}")
        print(f"   Project:          {project_subdir}")
        print(f"   Max sub-runs:     {max_sub_runs}")
        print(f"   Rounds per run:   {max_rounds_per_run}")
        print()

        print("=" * 70)
        print("  Starting Auto-Pilot Session")
        print("=" * 70 + "\n")

        # Run the orchestrator (auto-pilot will be triggered)
        from run_mode import main as run_main

        run_main()

        print("\n" + "=" * 70)
        print("  ✅ Auto-Pilot Session Completed")
        print("=" * 70 + "\n")

        # Try to find and display the latest session summary
        try:
            run_logs_dir = agent_dir.parent / "run_logs"
            if run_logs_dir.exists():
                # Find most recent directory with session_summary.json
                session_dirs = []
                for d in run_logs_dir.iterdir():
                    if d.is_dir() and (d / "session_summary.json").exists():
                        session_dirs.append(d)

                if session_dirs:
                    # Sort by modification time
                    session_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
                    latest_session_dir = session_dirs[0]
                    summary_file = latest_session_dir / "session_summary.json"

                    summary = json.loads(summary_file.read_text(encoding="utf-8"))

                    print(f"📊 Session Results:")
                    print(f"   Session ID:      {summary.get('session_id', 'unknown')}")
                    print(f"   Final decision:  {summary.get('final_decision', 'unknown')}")
                    print(f"   Sub-runs:        {len(summary.get('runs', []))}")
                    print(f"   Total cost:      ${summary.get('total_cost_usd', 0.0):.4f}")

                    # Find best overall score
                    runs = summary.get("runs", [])
                    if runs:
                        best_score = max(
                            (r.get("evaluation", {}).get("overall_score", 0.0) for r in runs),
                            default=0.0,
                        )
                        print(f"   Best score:      {best_score:.3f}")

                        # Show individual run results
                        print(f"\n   Individual Runs:")
                        for i, run in enumerate(runs, 1):
                            run_id = run.get("run_id", "unknown")
                            final_status = run.get("final_status", "unknown")
                            eval_result = run.get("evaluation", {})
                            score = eval_result.get("overall_score", 0.0)
                            recommendation = eval_result.get("recommendation", "unknown")

                            print(f"      {i}. {run_id[:12]}: {final_status} (score={score:.3f}, rec={recommendation})")

                    print(f"\n   Log location:    {latest_session_dir}")
                else:
                    print("⚠️  No session logs found")
        except Exception as e:
            print(f"⚠️  Could not read session summary: {e}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Session interrupted by user (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Session failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restore original config
        config_path.write_text(original_config, encoding="utf-8")


if __name__ == "__main__":
    main()
