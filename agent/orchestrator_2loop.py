# orchestrator_2loop.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import cost_tracker

# PHASE 1.3: Import prompt security for injection defense
import prompt_security

# PHASE 1.5: Import dependency injection context
from orchestrator_context import OrchestratorContext

# Legacy imports kept for backward compatibility with helper functions
# All actual usage in main() now uses context-based calls


def _load_config() -> Dict[str, Any]:
    """Load project_config.json from the agent folder."""
    cfg_path = Path(__file__).resolve().parent / "project_config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"project_config.json not found at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _ensure_out_dir(cfg: Dict[str, Any]) -> Path:
    root = Path(__file__).resolve().parent.parent  # .. from agent to root
    sites_dir = root / "sites"
    out_dir = sites_dir / cfg["project_subdir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _run_simple_tests(out_dir: Path, task: str) -> Dict[str, Any]:
    """Very small sanity checks on the generated site."""
    index_path = out_dir / "index.html"
    index_exists = index_path.exists()
    index_not_empty = False
    contains_task_keyword = False

    if index_exists:
        text = index_path.read_text(encoding="utf-8", errors="ignore")
        index_not_empty = len(text.strip()) > 0
        # Heuristic: try a title-case token from the task as the project name
        key = ""
        for token in task.split():
            if token.istitle() and len(token) > 3:
                key = token
                break
        if not key:
            key = "Hello"
        contains_task_keyword = key in text

    all_passed = index_exists and index_not_empty

    return {
        "index_exists": index_exists,
        "index_not_empty": index_not_empty,
        "contains_task_keyword": contains_task_keyword,
        "all_passed": all_passed,
    }


def _choose_employee_model(
    iteration: int,
    last_status: Optional[str],
    last_tests: Optional[Dict[str, Any]],
) -> str:
    """
    Decide which model the Employee should use.

    Constraint (your requirement):
    - Iteration 1: never use gpt-5 → use cheaper model (gpt-5-mini).
    - Iteration 2 or 3:
        * If previous status was 'needs_changes' OR tests failed → use gpt-5.
        * Otherwise → stay on gpt-5-mini.
    - Any iteration > 3: stay on gpt-5-mini (safety default).
    """
    if iteration <= 1:
        return "gpt-5-mini"

    if iteration in (2, 3):
        tests_failed = False
        if last_tests is not None:
            tests_failed = not bool(last_tests.get("all_passed"))

        if (last_status == "needs_changes") or tests_failed:
            return "gpt-5"
        else:
            return "gpt-5-mini"

    return "gpt-5-mini"


def _maybe_confirm_cost(cfg: Dict[str, Any], stage_label: str) -> bool:
    """
    Ask the user once whether they accept the current cost and want to continue.

    Uses:
      - cfg['interactive_cost_mode']: 'off' or 'once'
      - cfg['max_cost_usd'] (optional)
    """
    mode = str(cfg.get("interactive_cost_mode", "off")).lower().strip()
    if mode != "once":
        return True

    total_cost = cost_tracker.get_total_cost_usd()
    max_cost = float(cfg.get("max_cost_usd", 0.0) or 0.0)

    print("\n[Cost Check] Stage:", stage_label)
    print(f"  Current estimated cost so far: ~${total_cost:.4f} USD")
    if max_cost:
        print(f"  Configured cost cap:           ${max_cost:.4f} USD")

    answer = input("Continue with this run? [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def main(context: Optional[OrchestratorContext] = None) -> None:
    # PHASE 1.5: Initialize dependency injection context
    if context is None:
        context = OrchestratorContext.create_default(None)
        print("[DI] Using default production context")
    else:
        print("[DI] Using provided context (likely test context)")

    cfg = _load_config()
    out_dir = _ensure_out_dir(cfg)

    task: str = cfg["task"]

    # PHASE 1.3: Sanitize and validate task input to prevent prompt injection (V1)
    original_task = task
    task, detected_patterns, was_blocked = prompt_security.check_and_sanitize_task(
        task,
        context="orchestrator_2loop",
        strict_mode=False,  # Allow with sanitization rather than blocking
    )

    if detected_patterns:
        print(f"[Security] Detected injection patterns: {', '.join(detected_patterns)}")
        if was_blocked:
            print("[Security] CRITICAL: Task blocked due to high-severity injection attempt")
            print(f"[Security] Original task: {original_task[:200]}...")
            print("[Security] Aborting 2-loop orchestrator due to security violation")
            return
        else:
            print(f"[Security] Task sanitized (patterns detected but not blocked)")

    max_rounds: int = int(cfg.get("max_rounds", 1))
    use_visual_review: bool = bool(cfg.get("use_visual_review", False))
    prompts_file: str = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd: float = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd: float = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode: str = cfg.get("interactive_cost_mode", "off")
    use_git: bool = bool(cfg.get("use_git", False))

    # PHASE 1.4: Git secret scanning configuration
    git_secret_scanning_enabled: bool = bool(cfg.get("git_secret_scanning_enabled", True))

    print("=== PROJECT CONFIG (2-loop) ===")
    print(f"Project folder: {out_dir}")
    print(f"Task: {task}")
    print(f"use_visual_review: {use_visual_review}")
    print(f"max_rounds: {max_rounds}")
    print(f"prompts_file: {prompts_file}")
    print(f"max_cost_usd: {max_cost_usd}")
    print(f"cost_warning_usd: {cost_warning_usd}")
    print(f"interactive_cost_mode: {interactive_cost_mode}")
    print(f"use_git: {use_git}")
    print(f"git_secret_scanning_enabled: {git_secret_scanning_enabled}")

    # snapshots: per-iteration copies
    snapshots_root = out_dir / ".history"
    snapshots_root.mkdir(parents=True, exist_ok=True)

    # Git setup
    git_ready = False
    if use_git:
        git_ready = context.git_utils.ensure_repo(out_dir)

    # Cost tracker: reset state for this run
    context.cost_tracker.reset()

    # Load prompts/personas
    prompts = context.prompts.load_prompts(prompts_file)
    manager_plan_sys = prompts["manager_plan_sys"]
    manager_review_sys = prompts["manager_review_sys"]
    employee_sys = prompts["employee_sys"]

    # PHASE 1.6: Initialize core_logging (structured event system)
    mode = "2loop"
    core_run_id = context.logger.new_run_id()
    context.logger.log_start(
        core_run_id,
        project_folder=str(out_dir),
        task_description=task,
        config=cfg,
    )

    # PHASE 1.6: Removed run_logger.start_run() - now using core_logging only
    # run_record = context.run_logger.start_run(cfg, mode, out_dir)

    # 1) Manager planning
    print("\n====== MANAGER PLANNING (2-loop) ======")
    plan = context.llm.chat_json("manager", manager_plan_sys, task)
    print("\n-- Manager Plan --")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    total_cost = context.cost_tracker.get_total_cost_usd()
    print(f"\n[Cost] After planning: ~${total_cost:.4f} USD")

    if max_cost_usd and total_cost > max_cost_usd:
        print("[Cost] Max cost exceeded during planning. Aborting run.")
        final_status = "aborted_cost_cap_planning"
        final_cost_summary = context.cost_tracker.get_summary()
        # PHASE 1.6: core_logging.log_final_status() handles this now
        context.logger.log_final_status(
            core_run_id,
            status=final_status,
            reason="Cost cap exceeded during planning phase",
            iterations=0,
            total_cost_usd=total_cost,
        )
        return

    # Optional interactive confirmation (once)
    if not _maybe_confirm_cost(cfg, "after_planning"):
        print("[User] Aborted run after planning.")
        final_status = "aborted_by_user_after_planning"
        final_cost_summary = context.cost_tracker.get_summary()
        # PHASE 1.6: core_logging.log_final_status() handles this now
        context.logger.log_final_status(
            core_run_id,
            status=final_status,
            reason="Run aborted by user after planning",
            iterations=0,
            total_cost_usd=context.cost_tracker.get_total_cost_usd(),
        )
        return

    # Track last review/tests to drive model choice
    last_status: Optional[str] = None
    last_tests: Optional[Dict[str, Any]] = None
    last_feedback: Optional[Any] = None

    # 2) Iterative manager <-> employee loop
    for iteration in range(1, max_rounds + 1):
        print(f"\n====== ITERATION {iteration} / {max_rounds} ======")

        # PHASE 1.6: Log iteration start
        context.logger.log_iteration_begin(
            core_run_id,
            iteration=iteration,
            phase="2loop_iteration",
        )

        employee_model = _choose_employee_model(iteration, last_status, last_tests)
        print(f"[ModelSelect] Employee will use model: {employee_model}")

        existing_files = context.site_tools.load_existing_files(out_dir)
        if existing_files:
            print(f"[Files] Loaded {len(existing_files)} existing files from {out_dir}")
        else:
            print("[Files] No existing files loaded; starting fresh.")

        emp_payload = {
            "task": task,
            "plan": plan,
            "previous_files": existing_files,
            "feedback": last_feedback,
            "iteration": iteration,
        }

        print("\n[Employee] Building / updating site...")
        emp = context.llm.chat_json(
            "employee",
            employee_sys,
            json.dumps(emp_payload, ensure_ascii=False),
            model=employee_model,
        )

        files_dict = emp.get("files", {})
        if not isinstance(files_dict, dict):
            raise RuntimeError(
                f"Employee response 'files' must be an object/dict, got {type(files_dict)}"
            )

        # Write files
        print("\n[Orchestrator] Writing files to disk...")
        for rel_path, content in files_dict.items():
            dest = out_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            print(f"  wrote {dest}")

        # Snapshot for this iteration
        snap_dir = snapshots_root / f"iteration_{iteration}"
        snap_dir.mkdir(parents=True, exist_ok=True)
        for rel_path, content in files_dict.items():
            snap_path = snap_dir / rel_path
            snap_path.parent.mkdir(parents=True, exist_ok=True)
            snap_path.write_text(content, encoding="utf-8")

        # Basic tests
        print("\n[Tests] Running simple checks on current result...")
        test_results = _run_simple_tests(out_dir, task)
        print(json.dumps(test_results, indent=2, ensure_ascii=False))

        # Visual / DOM analysis
        browser_summary = None
        screenshot_path = None
        if use_visual_review:
            print("\n[Analysis] Reading index.html DOM for manager...")
            analysis = context.site_tools.analyze_site(out_dir)
            browser_summary = analysis.get("dom_info")
            screenshot_path = analysis.get("screenshot_path")
            print("\n-- Browser Summary (DOM/style) --")
            print(json.dumps(browser_summary, indent=2, ensure_ascii=False))

        # Manager review
        print("\n[Manager] Reviewing current iteration...")
        mgr_payload = {
            "task": task,
            "plan": plan,
            "files_summary": context.site_tools.summarize_files_for_manager(context.site_tools.load_existing_files(out_dir)),
            "tests": test_results,
            "browser_summary": browser_summary,
            "screenshot_path": screenshot_path,
            "iteration": iteration,
        }
        review = context.llm.chat_json(
            "manager",
            manager_review_sys,
            json.dumps(mgr_payload, ensure_ascii=False),
        )
        print("\n-- Manager Review --")
        print(json.dumps(review, indent=2, ensure_ascii=False))

        status = review.get("status", "needs_changes")
        feedback = review.get("feedback")

        last_status = status
        last_tests = test_results
        last_feedback = feedback

        # PHASE 1.6: Log iteration end
        context.logger.log_iteration_end(
            core_run_id,
            iteration=iteration,
            status=status,
            tests_passed=test_results.get("all_passed", False),
            files_written=len(files_dict),
        )

        # Git commit
        if git_ready:
            commit_message = (
                f"2loop iteration {iteration}: "
                f"status={status}, all_passed={test_results.get('all_passed')}"
            )
            # PHASE 1.4: Pass secret scanning configuration
            commit_success = context.git_utils.commit_all(out_dir, commit_message, git_secret_scanning_enabled)
            if not commit_success:
                print(f"[Git] Warning: Commit failed for iteration {iteration}")

        # PHASE 1.6: Removed run_logger.log_iteration_legacy() - now using core_logging only
        # Already using: context.logger.log_iteration_begin() (line ~255)
        # Already using: context.logger.log_iteration_end() (line ~351)
        # context.run_logger.log_iteration_legacy(
        #     run_record,
        #     {
        #         "iteration": iteration,
        #         "status": status,
        #         "tests": test_results,
        #         "employee_model": employee_model,
        #         "screenshot_path": screenshot_path,
        #         "feedback_size": len(feedback) if isinstance(feedback, list) else None,
        #     },
        # )

        # Cost checks after this iteration
        total_cost = context.cost_tracker.get_total_cost_usd()
        print(f"\n[Cost] After iteration {iteration}: ~${total_cost:.4f} USD")

        if cost_warning_usd and total_cost > cost_warning_usd:
            print(
                f"[Cost] Warning: total cost ~${total_cost:.4f} exceeds warning threshold "
                f"${cost_warning_usd:.4f}"
            )

        if max_cost_usd and total_cost > max_cost_usd:
            print(
                f"[Cost] Cap exceeded (~${total_cost:.4f} > ${max_cost_usd:.4f}). "
                "Stopping further iterations."
            )
            break

        if status == "approved":
            print("\n[Manager] Approved – stopping iterations.")
            break
        else:
            print("\n[Manager] Requested changes – will continue if rounds remain.")

    # Final status & cost
    final_status = last_status or "completed_no_status"
    final_cost_summary = context.cost_tracker.get_summary()

    print("\n====== DONE (2-loop) ======")
    print(f"Final status: {final_status}")
    print("\n[Cost] Final summary:")
    print(json.dumps(final_cost_summary, indent=2, ensure_ascii=False))

    # Persist cost summary to file
    agent_dir = Path(__file__).resolve().parent
    cost_log_dir = agent_dir / "cost_logs"
    cost_log_dir.mkdir(parents=True, exist_ok=True)
    cost_log_file = cost_log_dir / f"{cfg['project_subdir']}.jsonl"

    context.cost_tracker.append_history(
        log_file=cost_log_file,
        project_name=cfg["project_subdir"],
        task=task,
        status=final_status,
        extra={"max_rounds": max_rounds, "mode": "2loop"},
    )

    # PHASE 1.6: Log final status with core_logging
    context.logger.log_final_status(
        core_run_id,
        status=final_status,
        reason=f"2-loop orchestration completed with status: {final_status}",
        iterations=max_rounds,
        total_cost_usd=context.cost_tracker.get_total_cost_usd(),
    )

    # PHASE 1.6: Removed run_logger.finish_run_legacy() - now using core_logging only
    # Already using: context.logger.log_final_status() (line above)
    # context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)


if __name__ == "__main__":
    main()
