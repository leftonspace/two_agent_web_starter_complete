# orchestrator.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import cost_tracker
from git_utils import commit_all, ensure_repo
from llm import chat_json
from prompts import load_prompts
from run_logger import finish_run, log_iteration, start_run
from site_tools import (
    analyze_site,
    load_existing_files,
    summarize_files_for_manager,
)


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


def main() -> None:
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

    # Run log
    mode = "3loop"
    run_record = start_run(cfg, mode, out_dir)

    # 1) Manager planning
    print("\n====== MANAGER PLANNING ======")
    plan = chat_json("manager", manager_plan_sys, task)
    print("\n-- Manager Plan --")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

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

    # 3) Iterations: Supervisor → Employee (per phase) → Manager review
    for iteration in range(1, max_rounds + 1):
        print(f"\n====== ITERATION {iteration} / {max_rounds} ======")

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
            for rel_path, content in files_dict.items():
                dest = out_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"  wrote {dest}")

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

        # Git commit
        if git_ready:
            commit_message = (
                f"3loop iteration {iteration}: "
                f"status={status}, all_passed={test_results.get('all_passed')}"
            )
            commit_all(out_dir, commit_message)

        # RUN LOG: record this iteration
        log_iteration(
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

        # Cost checks
        total_cost = cost_tracker.get_total_cost_usd()
        print(f"\n[Cost] After iteration {iteration}: ~${total_cost:.4f} USD")

        if cost_warning_usd and total_cost > cost_warning_usd:
            print(
                f"[Cost] Warning: total cost ~${total_cost:.4f} exceeds warning "
                f"threshold ${cost_warning_usd:.4f}"
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

    final_status = last_status or "completed_no_status"
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


if __name__ == "__main__":
    main()
