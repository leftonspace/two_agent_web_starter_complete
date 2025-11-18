# run_mode.py
"""
Main entry point for the multi-agent orchestrator.

Loads configuration, performs cost estimation, and runs either:
- Auto-pilot mode (multiple sub-runs with self-evaluation)
- Single-run mode (2loop or 3loop)

STAGE 5: Enhanced with status codes and improved error handling.
"""

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
from cost_estimator import estimate_run_cost, format_cost_estimate
from run_logger import (
    RunSummary,
    finalize_run,
    log_iteration,
    save_run_summary,
    start_run,
)

# STAGE 5: Import status codes
from status_codes import (
    SUCCESS,
    COMPLETED,
    MAX_ROUNDS,
    TIMEOUT,
    COST_EXCEEDED,
    SAFETY_FAILED,
    USER_ABORT,
    SESSION_COMPLETED,
    SESSION_GAVE_UP,
    UNKNOWN,
    EXCEPTION,
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

    # Check for auto-pilot mode
    auto_pilot_cfg = cfg.get("auto_pilot")
    auto_pilot_enabled = auto_pilot_cfg and auto_pilot_cfg.get("enabled", False)

    print("======================================")
    print("  Two-Agent / Multi-Agent Runner")
    print("======================================")
    print(f"Mode:             {mode}  (2loop = Manager↔Employee, 3loop = Manager↔Supervisor↔Employee)")

    if auto_pilot_enabled:
        max_sub_runs = auto_pilot_cfg.get("max_sub_runs", 3)
        print(f"Auto-Pilot:       ENABLED (max {max_sub_runs} sub-runs)")

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


def _run_auto_pilot_mode(cfg: dict, auto_pilot_cfg: dict) -> None:
    """
    Run in auto-pilot mode with multiple sub-runs and self-evaluation.

    Args:
        cfg: Main project configuration
        auto_pilot_cfg: Auto-pilot specific configuration
    """
    from auto_pilot import run_auto_pilot

    # Extract configuration
    mode = cfg.get("mode", "3loop").lower().strip()
    project_subdir = cfg.get("project_subdir", "unknown_project")
    task = cfg.get("task", "")

    # Determine project directory
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    project_dir = project_root / "sites" / project_subdir

    # Auto-pilot settings
    max_sub_runs = int(auto_pilot_cfg.get("max_sub_runs", 3))
    max_rounds_per_run = int(cfg.get("max_rounds", 1))

    # Model configuration
    models_used = {
        "manager": DEFAULT_MANAGER_MODEL,
        "supervisor": DEFAULT_SUPERVISOR_MODEL,
        "employee": DEFAULT_EMPLOYEE_MODEL,
    }

    # Build config for sub-runs
    run_config = {
        "use_visual_review": cfg.get("use_visual_review", False),
        "use_git": cfg.get("use_git", False),
        "max_cost_usd": cfg.get("max_cost_usd", 0.0),
        "cost_warning_usd": cfg.get("cost_warning_usd", 0.0),
        "interactive_cost_mode": cfg.get("interactive_cost_mode", "off"),
    }

    print(f"[AutoPilot] Starting auto-pilot mode")
    print(f"[AutoPilot] Project: {project_dir}")
    print(f"[AutoPilot] Max sub-runs: {max_sub_runs}")
    print(f"[AutoPilot] Max rounds per run: {max_rounds_per_run}")
    print()

    try:
        session = run_auto_pilot(
            mode=mode,
            project_dir=str(project_dir),
            task=task,
            max_sub_runs=max_sub_runs,
            max_rounds_per_run=max_rounds_per_run,
            models_used=models_used,
            config=run_config,
        )

        print(f"\n[AutoPilot] Session completed: {session.session_id}")
        print(f"[AutoPilot] Total runs: {len(session.runs)}")
        print(f"[AutoPilot] Total cost: ${session.total_cost_usd:.4f}")
        print(f"[AutoPilot] Final decision: {session.final_decision}")

    except KeyboardInterrupt:
        print("\n[AutoPilot] Session interrupted by user")

    except Exception as e:
        print(f"\n[AutoPilot] Session failed with exception: {e}")
        raise


def main() -> None:
    cfg = _load_config()
    _print_summary(cfg)

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 4: Check for Auto-Pilot Mode
    # ──────────────────────────────────────────────────────────────────────
    auto_pilot_cfg = cfg.get("auto_pilot")
    if auto_pilot_cfg and auto_pilot_cfg.get("enabled", False):
        _run_auto_pilot_mode(cfg, auto_pilot_cfg)
        return

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

    # ──────────────────────────────────────────────────────────────────────
    # STAGE 3: Cost Estimation & Interactive Approval
    # ──────────────────────────────────────────────────────────────────────
    max_cost_usd = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode = cfg.get("interactive_cost_mode", "off")

    # Compute cost estimate
    cost_estimate = estimate_run_cost(
        mode=mode,
        max_rounds=max_rounds,
        models_used=models_used,
    )

    # Store estimate in run_summary
    run_summary.estimated_cost_usd = cost_estimate["estimated_total_usd"]

    # Display cost estimate
    print()
    print(format_cost_estimate(cost_estimate, max_cost_usd, cost_warning_usd))
    print()

    # Interactive approval if configured
    if interactive_cost_mode in ("once", "always"):
        prompt_msg = f"\n[Cost Control] Proceed with this run? "
        prompt_msg += f"Estimated cost: ${cost_estimate['estimated_total_usd']:.4f} USD"
        if max_cost_usd > 0:
            prompt_msg += f" (max allowed: ${max_cost_usd:.4f} USD)"
        prompt_msg += " [y/N]: "

        try:
            user_input = input(prompt_msg).strip().lower()
        except (EOFError, KeyboardInterrupt):
            user_input = "n"

        if user_input not in ("y", "yes"):
            print("\n[COST] Run aborted by user.")
            # Finalize and save run summary (STAGE 5: use status constant)
            run_summary = finalize_run(
                run_summary,
                final_status=USER_ABORT,
                safety_status=None,
                cost_summary=cost_tracker.get_summary(),
            )
            save_run_summary(run_summary)
            print(f"[RUN] Run summary saved (aborted before execution)")
            return

        print("[COST] User approved. Continuing...")

    # Warn if estimate exceeds cap (in "off" mode)
    elif max_cost_usd > 0 and cost_estimate["estimated_total_usd"] > max_cost_usd:
        print(f"\n⚠️  [Cost Control] WARNING: Estimated cost exceeds max_cost_usd!")
        print(f"    Estimate: ${cost_estimate['estimated_total_usd']:.4f}")
        print(f"    Max cap:  ${max_cost_usd:.4f}")
        print(f"    Proceeding anyway (interactive_cost_mode is 'off')...")

    # Reset cost tracking for this run
    cost_tracker.reset()

    # ──────────────────────────────────────────────────────────────────────
    # Run the orchestrator
    # ──────────────────────────────────────────────────────────────────────
    # STAGE 5: Use status constants
    final_status = "unknown"
    safety_status = None

    try:
        if mode == "2loop":
            from orchestrator_2loop import main as main_2loop
            # 2loop doesn't support run_summary yet
            main_2loop()
            final_status = COMPLETED
        else:
            # Default to 3-loop if anything else
            from orchestrator import main as main_3loop
            # Pass run_summary to enable STAGE 2 logging
            main_3loop(run_summary=run_summary)
            final_status = COMPLETED

    except KeyboardInterrupt:
        print("\n[RUN] Run interrupted by user")
        final_status = USER_ABORT
        log_iteration(
            run_summary,
            index=run_summary.rounds_completed + 1,
            role="system",
            status=ITER_INTERRUPTED,
            notes="Run interrupted by user (Ctrl+C)",
        )

    except Exception as e:
        print(f"\n[RUN] Run failed with exception: {e}")
        final_status = EXCEPTION
        log_iteration(
            run_summary,
            index=run_summary.rounds_completed + 1,
            role="system",
            status=ITER_EXCEPTION,
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
