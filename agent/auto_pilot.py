# auto_pilot.py
"""
Auto-pilot orchestration for the multi-agent system.

Runs multiple sub-runs back-to-back with self-evaluation between each run.
Makes decisions to continue, retry with adjustments, or stop based on evaluation scores.

STAGE 5: Enhanced with status codes and improved error handling.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

import cost_tracker
from run_logger import (
    RunSummary,
    SessionSummary,
    finalize_run,
    finalize_session,
    log_session_run,
    save_run_summary,
    save_session_summary,
    start_run,
    start_session,
)
from self_eval import evaluate_run

# STAGE 5: Import status codes
from status_codes import (
    COMPLETED,
    EVAL_CONTINUE,
    EVAL_RETRY,
    EVAL_STOP,
    EXCEPTION,
    SESSION_MAX_RUNS_REACHED,
    SESSION_STOPPED_BY_EVAL,
    SESSION_SUCCESS,
    SESSION_UNKNOWN_RECOMMENDATION,
    UNKNOWN,
    USER_ABORT,
)


def run_auto_pilot(
    mode: str,
    project_dir: str,
    task: str,
    max_sub_runs: int,
    max_rounds_per_run: int,
    models_used: Dict[str, str],
    config: Dict[str, Any],
) -> SessionSummary:
    """
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
    """
    print("\\n" + "=" * 70)
    print("  AUTO-PILOT MODE")
    print("=" * 70)
    print(f"Task: {task[:100]}...")
    print(f"Max sub-runs: {max_sub_runs}")
    print(f"Max rounds per run: {max_rounds_per_run}")
    print("=" * 70 + "\\n")

    # Start session
    session = start_session(
        task=task,
        max_sub_runs=max_sub_runs,
        session_config={
            "mode": mode,
            "project_dir": project_dir,
            "max_rounds_per_run": max_rounds_per_run,
            "models_used": models_used,
            **config,
        },
    )

    print(f"[AutoPilot] Started session: {session.session_id}")

    # Track session state
    task_context = task  # May be augmented with feedback from previous runs

    # Run sub-runs loop
    for run_index in range(1, max_sub_runs + 1):
        print(f"\\n{'=' * 70}")
        print(f"  SUB-RUN {run_index}/{max_sub_runs}")
        print(f"{'=' * 70}\\n")

        # Run a single sub-run
        run_summary, eval_result = _run_single_iteration(
            run_index=run_index,
            mode=mode,
            project_dir=project_dir,
            task=task_context,
            max_rounds=max_rounds_per_run,
            models_used=models_used,
            config=config,
        )

        # Log the run in the session
        run_summary_dict = asdict(run_summary)
        log_session_run(session, run_summary_dict, eval_result)

        # Save individual run summary
        save_run_summary(run_summary)

        # Display evaluation
        print(f"\\n[AutoPilot] Evaluation for run {run_index}:")
        print(f"  Overall score: {eval_result['overall_score']:.3f}")
        print(f"  Quality: {eval_result['score_quality']:.3f}")
        print(f"  Safety: {eval_result['score_safety']:.3f}")
        print(f"  Cost: {eval_result['score_cost']:.3f}")
        print(f"  Reasoning: {eval_result['reasoning']}")
        print(f"  Recommendation: {eval_result['recommendation']}")

        # Make decision based on recommendation (STAGE 5: use constants)
        recommendation = eval_result["recommendation"]

        if recommendation == EVAL_STOP:
            print(f"\n[AUTO] Stopping session after run {run_index} (recommendation: stop)")
            final_decision = SESSION_STOPPED_BY_EVAL
            break

        elif recommendation == EVAL_CONTINUE:
            # Check if this was the last allowed run
            if run_index >= max_sub_runs:
                print(f"\n[AUTO] Reached max_sub_runs ({max_sub_runs})")
                final_decision = SESSION_MAX_RUNS_REACHED
                break

            # Success! Task appears complete
            if eval_result["overall_score"] >= 0.8:
                print(f"\n[AUTO] High score achieved ({eval_result['overall_score']:.3f}), session complete!")
                final_decision = SESSION_SUCCESS
                break

            # Continue to next run with same task
            print(f"\n[AUTO] Continuing to sub-run {run_index + 1}...")
            task_context = task  # Keep original task

        elif recommendation == EVAL_RETRY:
            # Retry with augmented task context
            print("\n[AUTO] Retrying with feedback from evaluation...")
            task_context = _augment_task_with_feedback(task, eval_result, run_summary_dict)

            # Check if we've reached max runs
            if run_index >= max_sub_runs:
                print(f"\n[AUTO] Reached max_sub_runs ({max_sub_runs})")
                final_decision = SESSION_MAX_RUNS_REACHED
                break

        else:
            # Unknown recommendation
            print(f"\n[AUTO] Unknown recommendation '{recommendation}', stopping")
            final_decision = SESSION_UNKNOWN_RECOMMENDATION
            break

    else:
        # Loop completed without break
        final_decision = SESSION_MAX_RUNS_REACHED

    # Finalize session
    session = finalize_session(session, final_decision)

    # Save session summary
    save_session_summary(session)


    print(f"\\n{'=' * 70}")
    print("  AUTO-PILOT SESSION COMPLETE")
    print(f"{'=' * 70}")
    print(f"Session ID: {session.session_id}")
    print(f"Total runs: {len(session.runs)}")
    print(f"Total cost: ${session.total_cost_usd:.4f}")
    print(f"Final decision: {final_decision}")
    print(f"{'=' * 70}\\n")

    return session


def _run_single_iteration(
    run_index: int,
    mode: str,
    project_dir: str,
    task: str,
    max_rounds: int,
    models_used: Dict[str, str],
    config: Dict[str, Any],
) -> tuple[RunSummary, Dict[str, Any]]:
    """
    Run a single sub-run and evaluate it.

    Args:
        run_index: Sub-run number (1-based)
        mode: "2loop" or "3loop"
        project_dir: Path to project
        task: Task description (may be augmented with feedback)
        max_rounds: Max rounds for this run
        models_used: Model configuration
        config: Additional config

    Returns:
        (RunSummary, evaluation_result)
    """
    # Create RunSummary
    run_summary = start_run(
        mode=mode,
        project_dir=project_dir,
        task=task,
        max_rounds=max_rounds,
        models_used=models_used,
        config=config,
    )

    print(f"[AUTO] Starting run {run_index}: {run_summary.run_id}")

    # Reset cost tracking for this run
    cost_tracker.reset()

    # Run the orchestrator (STAGE 5: use status constants)
    final_status = UNKNOWN
    safety_status = None

    try:
        if mode == "2loop":
            from orchestrator_2loop import main as main_2loop
            main_2loop()
            final_status = COMPLETED
        else:
            # Default to 3-loop
            from orchestrator import main as main_3loop
            main_3loop(run_summary=run_summary)
            final_status = COMPLETED

    except KeyboardInterrupt:
        print(f"\\n[AUTO] Run {run_index} interrupted by user")
        final_status = USER_ABORT

    except Exception as e:
        print(f"\\n[AUTO] Run {run_index} failed with exception: {e}")
        final_status = EXCEPTION

    finally:
        # Finalize run
        cost_summary = cost_tracker.get_summary()
        run_summary = finalize_run(
            run_summary,
            final_status=final_status,
            safety_status=safety_status,
            cost_summary=cost_summary,
        )

    # Evaluate the run
    run_summary_dict = asdict(run_summary)
    eval_result = evaluate_run(run_summary_dict)

    return run_summary, eval_result


def _augment_task_with_feedback(
    original_task: str,
    eval_result: Dict[str, Any],
    run_summary: Dict[str, Any],
) -> str:
    """
    Augment the task description with feedback from the evaluation.

    Args:
        original_task: Original task description
        eval_result: Evaluation result from self_eval
        run_summary: RunSummary as dict

    Returns:
        Augmented task description with feedback
    """
    feedback_parts = []

    # Add original task
    feedback_parts.append(f"ORIGINAL TASK:\\n{original_task}")
    feedback_parts.append("\\n---\\n")

    # Add feedback based on evaluation
    feedback_parts.append("FEEDBACK FROM PREVIOUS RUN:")

    # Quality issues
    if eval_result["score_quality"] < 0.7:
        final_status = run_summary.get("final_status", "unknown")
        rounds_completed = run_summary.get("rounds_completed", 0)
        max_rounds = run_summary.get("max_rounds", 1)

        feedback_parts.append(f"- Previous run had quality issues (score: {eval_result['score_quality']:.2f})")
        feedback_parts.append(f"  Status: {final_status}, Rounds: {rounds_completed}/{max_rounds}")

        if final_status == "max_rounds_reached":
            feedback_parts.append("  Consider breaking the task into smaller steps")

    # Safety issues
    if eval_result["score_safety"] < 0.7:
        feedback_parts.append(f"- Previous run had safety concerns (score: {eval_result['score_safety']:.2f})")
        feedback_parts.append("  Ensure code follows best practices and security guidelines")

    # Cost issues
    if eval_result["score_cost"] < 0.7:
        feedback_parts.append(f"- Previous run was costly (score: {eval_result['score_cost']:.2f})")
        feedback_parts.append("  Try to be more efficient with iterations")

    # General guidance
    feedback_parts.append("\\nPlease address the above feedback in this retry.")

    return "\\n".join(feedback_parts)
