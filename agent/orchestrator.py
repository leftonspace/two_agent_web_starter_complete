# orchestrator.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import cost_tracker
from exec_safety import run_safety_checks
from git_utils import commit_all, ensure_repo
from llm import chat_json
from prompts import load_prompts
from run_logger import (
    finish_run_legacy as finish_run,
    log_iteration_legacy as log_iteration_dict,
    start_run_legacy as start_run,
)
# STAGE 2: Import new run logging API
from run_logger import RunSummary, log_iteration as log_iteration_new
from site_tools import (
    analyze_site,
    load_existing_files,
    summarize_files_for_manager,
)
# STAGE 2.1: Import tool registry for metadata
from exec_tools import get_tool_metadata
# STAGE 2.2: Import core logging for main run events
import core_logging


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


def _build_safety_feedback(safety_result: Dict[str, Any]) -> List[str]:
    """
    Build human-readable feedback from safety check results.

    STAGE 1 AUDIT FIX: Prefixes all safety feedback with "SAFETY:" to make
    it easy for the manager model to parse and distinguish from other feedback.

    Args:
        safety_result: Result from run_safety_checks()

    Returns:
        List of feedback strings for the manager, each prefixed with "SAFETY:"
    """
    feedback = []

    # Add header (prefixed for easy parsing)
    feedback.append("SAFETY: ══════════════════════════════════════════════════════")
    feedback.append("SAFETY: SAFETY CHECKS FAILED - The following issues must be fixed:")
    feedback.append("SAFETY: ══════════════════════════════════════════════════════")

    # Static analysis issues
    static_issues = safety_result.get("static_issues", [])
    if static_issues:
        # Group by severity
        errors = [i for i in static_issues if i.get("severity") == "error"]
        warnings = [i for i in static_issues if i.get("severity") == "warning"]

        if errors:
            feedback.append(f"SAFETY: Static Analysis ERRORS ({len(errors)} found):")
            for issue in errors[:5]:  # Show first 5
                feedback.append(
                    f"SAFETY:   - {issue['file']}:{issue['line']} - {issue['message']}"
                )
            if len(errors) > 5:
                feedback.append(f"SAFETY:   ... and {len(errors) - 5} more errors")

        if warnings:
            feedback.append(f"SAFETY: Static Analysis WARNINGS ({len(warnings)} found - should be fixed):")
            for issue in warnings[:3]:  # Show first 3
                feedback.append(
                    f"SAFETY:   - {issue['file']}:{issue['line']} - {issue['message']}"
                )
            if len(warnings) > 3:
                feedback.append(f"SAFETY:   ... and {len(warnings) - 3} more warnings")

    # Dependency issues
    # STAGE 1 AUDIT FIX: Now uses consistent severity mapping (error/warning/info)
    dep_issues = safety_result.get("dependency_issues", [])
    if dep_issues:
        # Group by severity (now using error/warning/info)
        errors = [i for i in dep_issues if i.get("severity") == "error"]
        warnings = [i for i in dep_issues if i.get("severity") == "warning"]

        if errors:
            feedback.append(f"SAFETY: Dependency ERRORS ({len(errors)} found - CRITICAL/HIGH vulnerabilities):")
            for issue in errors[:3]:  # Show first 3
                feedback.append(
                    f"SAFETY:   - {issue['package']} ({issue.get('version', 'unknown')}): {issue['summary']}"
                )
            if len(errors) > 3:
                feedback.append(f"SAFETY:   ... and {len(errors) - 3} more error-level issues")

        if warnings:
            feedback.append(f"SAFETY: Dependency WARNINGS ({len(warnings)} found - MEDIUM vulnerabilities, should review):")
            for issue in warnings[:2]:  # Show first 2
                feedback.append(
                    f"SAFETY:   - {issue['package']} ({issue.get('version', 'unknown')}): {issue['summary']}"
                )
            if len(warnings) > 2:
                feedback.append(f"SAFETY:   ... and {len(warnings) - 2} more warning-level issues")

    # Docker tests
    docker = safety_result.get("docker_tests", {})
    if docker.get("status") == "failed":
        feedback.append(f"SAFETY: Docker/Runtime Tests FAILED: {docker.get('details', 'No details')}")

    # Footer for clarity
    feedback.append("SAFETY: ══════════════════════════════════════════════════════")
    feedback.append("SAFETY: All ERROR-level issues must be fixed before approval.")
    feedback.append("SAFETY: ══════════════════════════════════════════════════════")

    return feedback


def _choose_employee_model(
    iteration: int,
    last_status: Optional[str],
    last_tests: Optional[Dict[str, Any]],
) -> str:
    """
    Decide which model the Employee should use.

    Constraint:
    - Iteration 1: always gpt-5-mini (cheap first pass).
    - Iteration 2 or 3:
        * If previous status was 'needs_changes' OR tests failed → gpt-5.
        * Otherwise → gpt-5-mini.
    - Iteration > 3: default to gpt-5-mini.
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

    Uses cfg['interactive_cost_mode'] == 'off' or 'once'.
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


def _build_supervisor_sys(manager_plan_sys: str) -> str:
    """
    Build a supervisor system prompt from the base manager planning prompt.
    The supervisor's job is to turn the plan into phases with categories.
    """
    return (
        manager_plan_sys
        + "\n\nYou are now acting as a SUPERVISOR.\n"
        + "Your task:\n"
        + "- Take the manager's plan and acceptance criteria.\n"
        + "- Break the work into 3–6 sequential phases.\n"
        + "- Each phase should list:\n"
        + "  * name: short descriptive name.\n"
        + "  * categories: tags like layout_structure, visual_design, content_ux,\n"
        + "    interaction_logic, qa_docs, performance_seo.\n"
        + "  * plan_steps: indices of steps from the original plan that belong here.\n\n"
        + "OUTPUT RULES:\n"
        + "- Respond ONLY in JSON.\n"
        + "- Structure:\n"
        + "  { \"phases\": [ { \"name\": \"...\", \"categories\": [\"...\"], \"plan_steps\": [0, 1] }, ... ] }\n"
        + "- No other top-level keys."
    )


def main(run_summary: Optional[RunSummary] = None) -> None:
    """
    Main 3-loop orchestrator function.

    Args:
        run_summary: Optional RunSummary for STAGE 2 logging.
                     If provided, iterations will be logged automatically.
    """
    # STAGE 2.2: Create run ID for core logging
    core_run_id = core_logging.new_run_id()

    cfg = _load_config()
    out_dir = _ensure_out_dir(cfg)

    task: str = cfg["task"]
    max_rounds: int = int(cfg.get("max_rounds", 1))
    use_visual_review: bool = bool(cfg.get("use_visual_review", False))
    prompts_file: str = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd: float = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd: float = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode: str = cfg.get("interactive_cost_mode", "off")
    use_git: bool = bool(cfg.get("use_git", False))

    # STAGE 1: Safety configuration
    safety_config = cfg.get("safety", {})
    run_safety_before_final: bool = bool(safety_config.get("run_safety_before_final", True))
    allow_extra_iteration_on_failure: bool = bool(safety_config.get("allow_extra_iteration_on_failure", True))

    print("=== PROJECT CONFIG (3-loop) ===")
    print(f"Project folder: {out_dir}")
    print(f"Task: {task}")
    print(f"use_visual_review: {use_visual_review}")
    print(f"max_rounds: {max_rounds}")
    print(f"prompts_file: {prompts_file}")
    print(f"max_cost_usd: {max_cost_usd}")
    print(f"cost_warning_usd: {cost_warning_usd}")
    print(f"interactive_cost_mode: {interactive_cost_mode}")
    print(f"use_git: {use_git}")
    print(f"run_safety_before_final: {run_safety_before_final}")
    print(f"allow_extra_iteration_on_failure: {allow_extra_iteration_on_failure}")

    # snapshots
    snapshots_root = out_dir / ".history"
    snapshots_root.mkdir(parents=True, exist_ok=True)

    # Git
    git_ready = False
    if use_git:
        git_ready = ensure_repo(out_dir)

    # Cost tracker
    cost_tracker.reset()

    # Load prompts
    prompts = load_prompts(prompts_file)
    manager_plan_sys = prompts["manager_plan_sys"]
    manager_review_sys = prompts["manager_review_sys"]
    employee_sys_base = prompts["employee_sys"]

    supervisor_sys = _build_supervisor_sys(manager_plan_sys)

    # STAGE 2.1: Get tool metadata for injection into prompts
    tool_metadata = get_tool_metadata()
    tool_metadata_json = json.dumps(tool_metadata, indent=2, ensure_ascii=False)

    # STAGE 2.1: Inject tool metadata into agent prompts
    tools_section = (
        "\n\n=== AVAILABLE TOOLS ===\n"
        "You have access to the following tools (you may request the orchestrator to call them on your behalf):\n\n"
        f"{tool_metadata_json}\n"
        "======================\n"
    )

    # Append to prompts (this gives agents awareness of tools)
    manager_plan_sys = manager_plan_sys + tools_section
    manager_review_sys = manager_review_sys + tools_section
    employee_sys_base = employee_sys_base + tools_section

    # Run log
    mode = "3loop"
    run_record = start_run(cfg, mode, out_dir)

    # STAGE 2.2: Log run start
    core_logging.log_start(
        core_run_id,
        project_folder=str(out_dir),
        task_description=task,
        config={
            "max_rounds": max_rounds,
            "use_visual_review": use_visual_review,
            "mode": mode,
            "run_safety_before_final": run_safety_before_final,
            "allow_extra_iteration_on_failure": allow_extra_iteration_on_failure,
        }
    )

    # 1) Manager planning
    print("\n====== MANAGER PLANNING ======")
    print(f"[CoreLog] Run ID: {core_run_id}")

    # STAGE 2.2: Log LLM call
    core_logging.log_llm_call(
        core_run_id,
        role="manager",
        model="gpt-5",  # Default model for planning
        prompt_length=len(manager_plan_sys) + len(task),
        phase="planning"
    )

    plan = chat_json("manager", manager_plan_sys, task)
    print("\n-- Manager Plan --")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    # STAGE 2: Log manager planning phase
    if run_summary is not None:
        log_iteration_new(
            run_summary,
            index=0,  # Planning phase (pre-iteration)
            role="manager",
            status="ok",
            notes="Manager created initial plan and acceptance criteria",
        )

    total_cost = cost_tracker.get_total_cost_usd()
    print(f"\n[Cost] After planning: ~${total_cost:.4f} USD")

    if max_cost_usd and total_cost > max_cost_usd:
        print("[Cost] Max cost exceeded during planning. Aborting run.")
        final_status = "aborted_cost_cap_planning"
        final_cost_summary = cost_tracker.get_summary()
        finish_run(run_record, final_status, final_cost_summary, out_dir)
        return

    # 2) Supervisor phasing
    print("\n====== SUPERVISOR PHASING ======")
    sup_payload = {
        "task": task,
        "plan": plan.get("plan", []),
        "acceptance_criteria": plan.get("acceptance_criteria", []),
    }

    # STAGE 2.2: Log LLM call
    core_logging.log_llm_call(
        core_run_id,
        role="supervisor",
        model="gpt-5",  # Default model
        prompt_length=len(supervisor_sys) + len(json.dumps(sup_payload)),
        phase="supervisor_phasing"
    )

    phases = chat_json(
        "supervisor",
        supervisor_sys,
        json.dumps(sup_payload, ensure_ascii=False),
    )
    print("\n-- Supervisor Phases --")
    print(json.dumps(phases, indent=2, ensure_ascii=False))

    phase_list: List[Dict[str, Any]] = phases.get("phases", [])
    if not isinstance(phase_list, list) or not phase_list:
        phase_list = [
            {
                "name": "All work",
                "categories": ["layout_structure", "visual_design", "content_ux"],
                "plan_steps": list(range(len(plan.get("plan", [])))),
            }
        ]

    # Optional interactive cost check after planning+phasing
    if not _maybe_confirm_cost(cfg, "after_planning_and_supervisor"):
        print("[User] Aborted run after planning & supervisor phasing.")
        final_status = "aborted_by_user_after_planning"
        final_cost_summary = cost_tracker.get_summary()
        finish_run(run_record, final_status, final_cost_summary, out_dir)
        return

    # Track last review status/tests to drive model choice
    last_status: Optional[str] = None
    last_tests: Optional[Dict[str, Any]] = None
    last_feedback: Optional[Any] = None

    # STAGE 3: Cost tracking flags
    cost_warning_shown = False  # Prevent spamming warning

    # STAGE 1: Safety failure tracking for final iteration policy
    safety_failed_on_final = False  # Track if safety fails on last planned iteration
    extra_iteration_granted = False  # Prevent infinite loops

    # 3) Iterations: Supervisor → Employee (per phase) → Manager review
    for iteration in range(1, max_rounds + 1):
        print(f"\n====== ITERATION {iteration} / {max_rounds} ======")

        # STAGE 2.2: Log iteration begin
        core_logging.log_iteration_begin(
            core_run_id,
            iteration=iteration,
            mode=mode,
            max_rounds=max_rounds
        )

        employee_model = _choose_employee_model(iteration, last_status, last_tests)
        print(f"[ModelSelect] Employee will use model: {employee_model}")

        existing_files = load_existing_files(out_dir)
        if existing_files:
            print(f"[Files] Loaded {len(existing_files)} existing files from {out_dir}")
        else:
            print("[Files] No existing files loaded; starting from scratch.")

        for phase_index, phase in enumerate(phase_list, start=1):
            print(
                f"\n====== EMPLOYEE PHASES (iteration {iteration}) ======\n"
                f"[Phase {phase_index}] {phase.get('name', 'Unnamed phase')} "
                f"categories={phase.get('categories', [])}"
            )

            phase_payload = {
                "task": task,
                "plan": plan,
                "phase": phase,
                "previous_files": existing_files,
                "feedback": last_feedback,
                "iteration": iteration,
            }

            employee_sys_phase = employee_sys_base

            print(
                f"\n[Employee] Running phase {phase_index}: "
                f"{phase.get('name', 'Unnamed phase')}"
            )

            # STAGE 2.2: Log LLM call
            core_logging.log_llm_call(
                core_run_id,
                role="employee",
                model=employee_model,
                prompt_length=len(employee_sys_phase) + len(json.dumps(phase_payload)),
                iteration=iteration,
                phase_index=phase_index,
                phase_name=phase.get('name', 'Unnamed phase')
            )

            emp = chat_json(
                "employee",
                employee_sys_phase,
                json.dumps(phase_payload, ensure_ascii=False),
                model=employee_model,
            )

            files_dict = emp.get("files", {})
            if not isinstance(files_dict, dict):
                raise RuntimeError(
                    f"Employee response 'files' must be an object/dict, got {type(files_dict)}"
                )

            print("\n[Orchestrator] Writing files to disk...")
            written_files = []
            for rel_path, content in files_dict.items():
                dest = out_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"  wrote {dest}")
                written_files.append(rel_path)

            # STAGE 2.2: Log file writes
            if written_files:
                core_logging.log_file_write(
                    core_run_id,
                    files=written_files,
                    summary=f"Employee phase {phase_index} wrote {len(written_files)} files",
                    iteration=iteration,
                    phase_index=phase_index
                )

            # refresh for next phase
            existing_files = load_existing_files(out_dir)

        # Snapshot for this iteration
        snap_dir = snapshots_root / f"iteration_{iteration}"
        snap_dir.mkdir(parents=True, exist_ok=True)
        final_files = load_existing_files(out_dir)
        for rel_path, content in final_files.items():
            snap_path = snap_dir / rel_path
            snap_path.parent.mkdir(parents=True, exist_ok=True)
            snap_path.write_text(content, encoding="utf-8")

        # Basic tests
        print("\n[Tests] Running simple checks on final result...")
        test_results = _run_simple_tests(out_dir, task)
        print(json.dumps(test_results, indent=2, ensure_ascii=False))

        # Visual / DOM analysis
        browser_summary: Optional[Dict[str, Any]] = None
        screenshot_path: Optional[str] = None
        if use_visual_review:
            try:
                print("\n[Analysis] Reading index.html DOM...")
                index_path = out_dir / "index.html"
                analysis = analyze_site(index_path)
                browser_summary = analysis["dom_info"]
                screenshot_path = analysis["screenshot_path"]
            except Exception as e:  # pragma: no cover - best effort only
                print(f"[Analysis] Skipped visual review due to error: {e}")

        # Manager review
        print("\n[Manager] Final review...")
        mgr_payload = {
            "task": task,
            "plan": plan,
            "phases": phase_list,
            "files_summary": summarize_files_for_manager(final_files),
            "tests": test_results,
            "browser_summary": browser_summary,
            "screenshot_path": screenshot_path,
            "iteration": iteration,
        }

        # STAGE 2.2: Log LLM call
        core_logging.log_llm_call(
            core_run_id,
            role="manager",
            model="gpt-5",  # Default model for review
            prompt_length=len(manager_review_sys) + len(json.dumps(mgr_payload)),
            iteration=iteration,
            phase="review"
        )

        review = chat_json(
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

        # ─────────────────────────────────────────────────────────────
        # SAFETY CHECKS (STAGE 1 Integration)
        # ─────────────────────────────────────────────────────────────
        # STAGE 1.1: Configurable safety checks
        # Safety runs when:
        # - Manager approves the work (status == "approved"), OR
        # - We're on the last iteration (final chance to catch issues)
        # - AND the run_safety_before_final config flag is enabled
        #
        # Final Iteration Failure Policy (STAGE 1 Audit Fix):
        # If safety fails on the final planned iteration AND no extra iteration
        # has been granted yet, we automatically add one more iteration dedicated
        # to fixing safety issues. This prevents runs from ending with unresolved
        # safety problems.
        #
        # If safety fails:
        # - Status is overridden to "needs_changes"
        # - Feedback is injected for the manager to create fix tasks
        # - The loop continues (if rounds remain OR if we grant extra iteration)
        run_safety = False
        iteration_safety_status = None

        if run_safety_before_final:
            if status == "approved":
                run_safety = True
                print("[Safety] Running safety checks because manager approved")
            elif iteration == max_rounds:
                # Last iteration - run safety checks regardless
                run_safety = True
                print(f"[Safety] Running safety checks on final iteration ({iteration}/{max_rounds})")

        if run_safety:
            print("\n[Safety] Running comprehensive safety checks...")

            # Defensive handling: catch any unexpected errors from run_safety_checks
            try:
                safety_result = run_safety_checks(str(out_dir), task)

                # Use summary_status if available, fall back to status
                iteration_safety_status = safety_result.get("summary_status") or safety_result.get("status", "failed")

                # STAGE 2.2: Log safety check
                static_issues = safety_result.get("static_issues", [])
                dep_issues = safety_result.get("dependency_issues", [])
                error_count = sum(1 for i in static_issues if i.get("severity") == "error")
                error_count += sum(1 for i in dep_issues if i.get("severity") == "error")
                warning_count = sum(1 for i in static_issues if i.get("severity") == "warning")
                warning_count += sum(1 for i in dep_issues if i.get("severity") == "warning")

                core_logging.log_safety_check(
                    core_run_id,
                    summary_status=iteration_safety_status,
                    error_count=error_count,
                    warning_count=warning_count,
                    safety_run_id=safety_result.get("run_id", ""),
                    iteration=iteration
                )

                if iteration_safety_status == "failed":
                    print("\n[Safety] ❌ Safety checks FAILED")
                    print(f"[Safety] Static issues: {len(safety_result.get('static_issues', []))}")
                    print(f"[Safety] Dependency issues: {len(safety_result.get('dependency_issues', []))}")

                    # Check if this is the final planned iteration
                    is_final_iteration = (iteration == max_rounds)

                    # STAGE 1 AUDIT FIX: Configurable extra iteration policy
                    if is_final_iteration and not extra_iteration_granted and allow_extra_iteration_on_failure:
                        # Grant one extra iteration for fixes
                        print("\n[Safety] ⚠️  Safety failed on final planned iteration")
                        print("[Safety] Granting ONE extra iteration to fix safety issues")
                        print("[Safety] (disable with safety.allow_extra_iteration_on_failure=false)")
                        max_rounds += 1
                        extra_iteration_granted = True
                        safety_failed_on_final = True
                    elif is_final_iteration and not allow_extra_iteration_on_failure:
                        print("\n[Safety] ⚠️  Safety failed on final iteration")
                        print("[Safety] Extra iteration disabled by config (safety.allow_extra_iteration_on_failure=false)")
                        safety_failed_on_final = True

                    # Override status to needs_changes
                    status = "needs_changes"
                    last_status = status

                    # Build safety feedback for the manager
                    safety_feedback = _build_safety_feedback(safety_result)
                    feedback = safety_feedback if feedback is None else list(feedback) + safety_feedback
                    last_feedback = feedback

                    print("[Safety] Overriding status to 'needs_changes'")
                    print("[Safety] Safety issues will be fed back to manager on next iteration")
                else:
                    print("\n[Safety] ✓ Safety checks PASSED")

            except KeyError as e:
                # Handle malformed safety result
                print(f"\n[Safety] ⚠️  Malformed safety result: missing key {e}")
                print("[Safety] Treating as safety failure for safety")
                iteration_safety_status = "failed"
                status = "needs_changes"
                last_status = status
                feedback = ["Safety check returned malformed result - treating as failure"]
                last_feedback = feedback
            except Exception as e:
                # Catch-all for any other unexpected errors
                print(f"\n[Safety] ⚠️  Unexpected error during safety checks: {e}")
                print("[Safety] Treating as safety failure for safety")
                iteration_safety_status = "failed"
                status = "needs_changes"
                last_status = status
                feedback = [f"Safety check crashed: {str(e)}"]
                last_feedback = feedback

        # Git commit
        if git_ready:
            commit_message = (
                f"3loop iteration {iteration}: "
                f"status={status}, all_passed={test_results.get('all_passed')}"
            )
            commit_all(out_dir, commit_message)

        # RUN LOG: record this iteration (legacy dict-based)
        log_iteration_dict(
            run_record,
            {
                "iteration": iteration,
                "status": status,
                "tests": test_results,
                "employee_model": employee_model,
                "screenshot_path": screenshot_path,
                "feedback_size": len(feedback) if isinstance(feedback, list) else None,
            },
        )

        # STAGE 2: Log iteration with new structured API
        if run_summary is not None:
            # Determine iteration status
            iter_status = "ok"
            if iteration_safety_status == "failed":
                iter_status = "safety_failed"
            elif status == "needs_changes":
                iter_status = "needs_changes"
            elif status == "approved":
                iter_status = "approved"

            # Build notes
            notes_parts = [f"Iteration {iteration} completed"]
            notes_parts.append(f"Manager status: {status}")
            if test_results.get("all_passed"):
                notes_parts.append("All tests passed")
            else:
                notes_parts.append("Some tests failed")

            log_iteration_new(
                run_summary,
                index=iteration,
                role="manager",  # Last role in iteration is manager review
                status=iter_status,
                notes="; ".join(notes_parts),
                safety_status=iteration_safety_status,
            )

        # STAGE 2.2: Log iteration end
        core_logging.log_iteration_end(
            core_run_id,
            iteration=iteration,
            status=status,
            tests_all_passed=test_results.get("all_passed", False),
            safety_status=iteration_safety_status
        )

        # ─────────────────────────────────────────────────────────────
        # STAGE 3: Cost Control Enforcement
        # ─────────────────────────────────────────────────────────────
        total_cost = cost_tracker.get_total_cost_usd()
        print(f"\n[Cost] After iteration {iteration}: ~${total_cost:.4f} USD")

        # Show warning once when crossing cost_warning_usd
        if cost_warning_usd and total_cost > cost_warning_usd and not cost_warning_shown:
            print(
                f"\n⚠️  [Cost] WARNING: total cost ~${total_cost:.4f} exceeds warning "
                f"threshold ${cost_warning_usd:.4f}"
            )
            cost_warning_shown = True

        # Hard stop if max_cost_usd exceeded
        if max_cost_usd and total_cost > max_cost_usd:
            print(
                f"\n❌ [Cost] HARD CAP EXCEEDED (~${total_cost:.4f} > ${max_cost_usd:.4f}). "
                "Stopping further iterations."
            )
            last_status = "cost_cap_exceeded"
            break

        if status == "approved":
            print("\n[Manager] Approved – stopping iterations.")
            break
        else:
            print("\n[Manager] Requested changes – will continue if rounds remain.")

    # ─────────────────────────────────────────────────────────────
    # STAGE 1: Final safety failure handling
    # ─────────────────────────────────────────────────────────────
    # If safety failed on the extra iteration we granted, we've exhausted
    # all options. Mark the run as failed with unresolved safety issues.
    final_status = last_status or "completed_no_status"

    if safety_failed_on_final and extra_iteration_granted and last_status == "needs_changes":
        print("\n⚠️  [Safety] Safety checks failed even after extra iteration")
        print("[Safety] Run ended with UNRESOLVED SAFETY ISSUES")
        final_status = "failed_safety_unresolved"

    final_cost_summary = cost_tracker.get_summary()

    print("\n====== DONE (3-loop) ======")
    print(f"Final status: {final_status}")
    print("\n[Cost] Final summary:")
    print(json.dumps(final_cost_summary, indent=2, ensure_ascii=False))

    # Persist cost summary
    agent_dir = Path(__file__).resolve().parent
    cost_log_dir = agent_dir / "cost_logs"
    cost_log_dir.mkdir(parents=True, exist_ok=True)
    cost_log_file = cost_log_dir / f"{cfg['project_subdir']}.jsonl"

    cost_tracker.append_history(
        log_file=cost_log_file,
        project_name=cfg["project_subdir"],
        task=task,
        status=final_status,
        extra={"max_rounds": max_rounds, "mode": "3loop"},
    )

    # RUN LOG: finalize
    finish_run(run_record, final_status, final_cost_summary, out_dir)

    # STAGE 2.2: Log final status
    core_logging.log_final_status(
        core_run_id,
        status=final_status,
        reason=f"Run completed with status: {final_status}",
        iterations=max_rounds,
        total_cost_usd=final_cost_summary.get("total_usd", 0.0)
    )

    print(f"\n[CoreLog] Main run logs written to: run_logs_main/{core_run_id}.jsonl")


if __name__ == "__main__":
    main()
