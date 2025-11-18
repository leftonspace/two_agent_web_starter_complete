# run_mode.py
from __future__ import annotations

import json
from pathlib import Path

# We import defaults just for display purposes.
try:
    from llm import (
        DEFAULT_EMPLOYEE_MODEL,
        DEFAULT_MANAGER_MODEL,
        DEFAULT_SUPERVISOR_MODEL,
    )
except ImportError:
    # Fallback labels if constants are not accessible for any reason.
    DEFAULT_MANAGER_MODEL = "gpt-5-mini"
    DEFAULT_SUPERVISOR_MODEL = "gpt-5-nano"
    DEFAULT_EMPLOYEE_MODEL = "gpt-5"

# STAGE 2: Import run logging and cost tracking
import cost_tracker
from run_logger import (
    RunSummary,
    finalize_run,
    log_iteration,
    save_run_summary,
    start_run,
)


def _load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "project_config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"project_config.json not found at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _print_summary(cfg: dict) -> None:
    mode = cfg.get("mode", "3loop")
    project = cfg.get("project_subdir", "<unknown>")
    task = cfg.get("task", "").strip()
    short_task = (task[:120] + "…") if len(task) > 120 else task

    max_rounds = int(cfg.get("max_rounds", 1))
    use_visual_review = bool(cfg.get("use_visual_review", False))
    prompts_file = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode = cfg.get("interactive_cost_mode", "off")

    print("======================================")
    print("  Two-Agent / Multi-Agent Runner")
    print("======================================")
    print(f"Mode:             {mode}  (2loop = Manager↔Employee, 3loop = Manager↔Supervisor↔Employee)")
    print(f"Project subdir:   {project}")
    print(f"Task (short):     {short_task}")
    print(f"Max rounds:       {max_rounds}")
    print(f"Visual review:    {use_visual_review}")
    print(f"Prompts file:     {prompts_file}")
    print("--------------------------------------")
    print(f"Cost warning:     {cost_warning_usd or 0.0:.4f} USD")
    print(f"Cost cap:         {max_cost_usd or 0.0:.4f} USD")
    print(f"Interactive cost: {interactive_cost_mode!r}  (off|once)")
    print("--------------------------------------")
    print("Default models (can be overridden by env vars):")
    print(f"  Manager:   {DEFAULT_MANAGER_MODEL}")
    print(f"  Supervisor:{DEFAULT_SUPERVISOR_MODEL}")
    print(f"  Employee:  {DEFAULT_EMPLOYEE_MODEL}")
    print("======================================\n")


def main() -> None:
    cfg = _load_config()
    _print_summary(cfg)

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 2: Initialize Run Logging
    # ──────────────────────────────────────────────────────────────────────
    mode = cfg.get("mode", "3loop").lower().strip()
    project_subdir = cfg.get("project_subdir", "unknown_project")
    task = cfg.get("task", "")
    max_rounds = int(cfg.get("max_rounds", 1))

    # Determine project directory
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    project_dir = project_root / "sites" / project_subdir

    # Create RunSummary for this run
    models_used = {
        "manager": DEFAULT_MANAGER_MODEL,
        "supervisor": DEFAULT_SUPERVISOR_MODEL,
        "employee": DEFAULT_EMPLOYEE_MODEL,
    }

    run_summary = start_run(
        mode=mode,
        project_dir=str(project_dir),
        task=task,
        max_rounds=max_rounds,
        models_used=models_used,
        config={
            "use_visual_review": cfg.get("use_visual_review", False),
            "use_git": cfg.get("use_git", False),
            "max_cost_usd": cfg.get("max_cost_usd", 0.0),
            "cost_warning_usd": cfg.get("cost_warning_usd", 0.0),
            "interactive_cost_mode": cfg.get("interactive_cost_mode", "off"),
        },
    )

    print(f"\n[RunLog] Started run: {run_summary.run_id}")
    print(f"[RunLog] Mode: {mode}, Max rounds: {max_rounds}")

    # Reset cost tracking for this run
    cost_tracker.reset()

    # ──────────────────────────────────────────────────────────────────────
    # Run the orchestrator
    # ──────────────────────────────────────────────────────────────────────
    final_status = "unknown"
    safety_status = None

    try:
        if mode == "2loop":
            from orchestrator_2loop import main as main_2loop
            # 2loop doesn't support run_summary yet
            main_2loop()
            final_status = "completed"
        else:
            # Default to 3-loop if anything else
            from orchestrator import main as main_3loop
            # Pass run_summary to enable STAGE 2 logging
            main_3loop(run_summary=run_summary)
            final_status = "completed"

    except KeyboardInterrupt:
        print("\n[RunMode] Run interrupted by user")
        final_status = "aborted_by_user"
        log_iteration(
            run_summary,
            index=run_summary.rounds_completed + 1,
            role="system",
            status="interrupted",
            notes="Run interrupted by user (Ctrl+C)",
        )

    except Exception as e:
        print(f"\n[RunMode] Run failed with exception: {e}")
        final_status = "exception"
        log_iteration(
            run_summary,
            index=run_summary.rounds_completed + 1,
            role="system",
            status="exception",
            notes=f"Exception: {type(e).__name__}: {str(e)}",
        )
        # Re-raise to preserve traceback if needed
        # raise

    finally:
        # ──────────────────────────────────────────────────────────────────
        # STAGE 2: Finalize and Save Run Log
        # ──────────────────────────────────────────────────────────────────
        cost_summary = cost_tracker.get_summary()

        run_summary = finalize_run(
            run_summary,
            final_status=final_status,
            safety_status=safety_status,
            cost_summary=cost_summary,
        )

        # Save the run summary
        log_path = save_run_summary(run_summary)

        print(f"\n[RunLog] Finalized run: {run_summary.run_id}")
        print(f"[RunLog] Final status: {final_status}")
        print(f"[RunLog] Rounds completed: {run_summary.rounds_completed}")
        if log_path:
            print(f"[RunLog] Log saved to: {log_path}")


if __name__ == "__main__":
    main()
