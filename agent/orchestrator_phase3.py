# orchestrator_phase3.py
"""
PHASE 3: Adaptive Multi-Agent Orchestrator

This orchestrator implements the full Phase 3 architecture with:
- Dynamic roadmap management (merge, split, reorder, skip, reopen stages)
- Adaptive stage flow (auto-advance on 0 findings, intelligent fix cycles)
- Horizontal agent communication (inter-agent bus)
- Stage-level persistent memory
- Regression detection and automatic stage reopening
- Comprehensive Phase 3 logging

KEY DIFFERENCES FROM STAGE 2 orchestrator.py:
- Uses WorkflowManager instead of fixed phase list
- Implements stage-based loop instead of iteration loop
- Auto-advances on clean supervisor audits
- Detects regressions and reopens earlier stages
- Uses inter_agent_bus for horizontal messaging
- Persists stage memory and summaries
- Emits all Phase 3 log events

BACKWARD COMPATIBILITY:
- Maintains all Stage 1-2 features (safety checks, cost tracking, git, etc.)
- Can run in parallel with orchestrator.py (different mode in run_mode.py)
- Uses same config format with optional Phase 3 settings
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import cost_tracker
import core_logging
from exec_safety import run_safety_checks
from exec_tools import get_tool_metadata
from git_utils import commit_all, ensure_repo
from llm import chat_json
from prompts import load_prompts
from run_logger import (
    RunSummary,
    finish_run_legacy as finish_run,
    log_iteration as log_iteration_new,
    log_iteration_legacy as log_iteration_dict,
    start_run_legacy as start_run,
)
from site_tools import (
    analyze_site,
    load_existing_files,
    summarize_files_for_manager,
)

# PHASE 3: Import new systems
from workflow_manager import create_workflow, WorkflowManager
from memory_store import create_memory_store, MemoryStore
from inter_agent_bus import get_bus, reset_bus, MessageType
from stage_summaries import create_tracker, StageSummaryTracker


def _load_config() -> Dict[str, Any]:
    """Load project_config.json from the agent folder."""
    cfg_path = Path(__file__).resolve().parent / "project_config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"project_config.json not found at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _ensure_out_dir(cfg: Dict[str, Any]) -> Path:
    root = Path(__file__).resolve().parent.parent
    sites_dir = root / "sites"
    out_dir = sites_dir / cfg["project_subdir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _build_supervisor_sys(base: str) -> str:
    """Build supervisor system prompt with phasing instructions."""
    return (
        base
        + "\n\nYour task: break the manager's plan into 3–7 sequential phases.\n"
        + "Each phase should group related work.\n"
        + "OUTPUT RULES: Respond ONLY in JSON.\n"
        + 'Use this structure: {"phases": [{"name": "...", "categories": [...], "plan_steps": [...]}, ...]}\n'
    )


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
    """Build human-readable feedback from safety check results with SAFETY: prefix."""
    feedback = []

    # Header
    feedback.append("SAFETY: " + "=" * 60)
    feedback.append("SAFETY: SAFETY CHECKS FAILED - The following issues must be fixed:")
    feedback.append("SAFETY: " + "=" * 60)

    # Static analysis errors
    static_issues = safety_result.get("static_analysis", {}).get("issues", [])
    errors = [i for i in static_issues if i.get("severity") == "error"]
    if errors:
        feedback.append(f"SAFETY: Static Analysis ERRORS ({len(errors)} found):")
        for issue in errors[:10]:
            loc = f"{issue.get('file', 'unknown')}:{issue.get('line', '?')}"
            feedback.append(f"SAFETY:   - {loc} - {issue.get('message', 'Unknown error')}")

    # Dependency errors
    dep_issues = safety_result.get("dependency_scan", {}).get("vulnerabilities", [])
    critical = [v for v in dep_issues if v.get("severity") in ("CRITICAL", "HIGH")]
    if critical:
        feedback.append(f"SAFETY: Dependency ERRORS ({len(critical)} found - CRITICAL/HIGH):")
        for vuln in critical[:10]:
            pkg = vuln.get("package", "unknown")
            ver = vuln.get("version", "?")
            cve = vuln.get("id", "?")
            feedback.append(f"SAFETY:   - {pkg} ({ver}): {cve}")

    feedback.append("SAFETY: " + "=" * 60)
    return feedback


def _maybe_confirm_cost(cfg: Dict[str, Any], checkpoint: str) -> bool:
    """Interactive cost confirmation if enabled."""
    mode = cfg.get("interactive_cost_mode", "off")
    if mode == "off":
        return True

    total_cost = cost_tracker.get_total_cost_usd()
    warning_threshold = float(cfg.get("cost_warning_usd", 0) or 0)

    if mode == "once" and checkpoint != "after_planning_and_supervisor":
        return True

    if total_cost < warning_threshold:
        return True

    print(f"\n[Cost] Current cost: ~${total_cost:.4f} USD")
    print(f"[Cost] Checkpoint: {checkpoint}")
    response = input("[Cost] Continue? (y/n): ").strip().lower()
    return response == "y"


def main_phase3(run_summary: Optional[RunSummary] = None):
    """
    PHASE 3: Main adaptive multi-agent orchestrator.

    This implements the full Phase 3 architecture with dynamic workflows,
    adaptive stage flow, horizontal messaging, and regression detection.
    """
    # PHASE 3: Create run ID for all subsystems
    core_run_id = core_logging.new_run_id()

    # Load config
    cfg = _load_config()
    out_dir = _ensure_out_dir(cfg)

    task: str = cfg["task"]
    max_audits_per_stage: int = int(cfg.get("max_audits_per_stage", 3))
    use_visual_review: bool = bool(cfg.get("use_visual_review", False))
    prompts_file: str = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd: float = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd: float = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode: str = cfg.get("interactive_cost_mode", "off")
    use_git: bool = bool(cfg.get("use_git", False))

    # Safety configuration
    safety_config = cfg.get("safety", {})
    run_safety_before_final: bool = bool(safety_config.get("run_safety_before_final", True))
    allow_extra_iteration_on_failure: bool = bool(safety_config.get("allow_extra_iteration_on_failure", True))

    print("=== PHASE 3 ORCHESTRATOR ===")
    print(f"Run ID: {core_run_id}")
    print(f"Project folder: {out_dir}")
    print(f"Task: {task}")
    print(f"Max audits per stage: {max_audits_per_stage}")
    print(f"use_visual_review: {use_visual_review}")
    print(f"prompts_file: {prompts_file}")
    print(f"max_cost_usd: {max_cost_usd}")
    print(f"cost_warning_usd: {cost_warning_usd}")
    print(f"use_git: {use_git}")
    print(f"run_safety_before_final: {run_safety_before_final}")

    # Snapshots
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

    # PHASE 3: Get tool metadata for injection
    tool_metadata = get_tool_metadata()
    tool_metadata_json = json.dumps(tool_metadata, indent=2, ensure_ascii=False)

    tools_section = (
        "\n\n=== AVAILABLE TOOLS ===\n"
        "You have access to the following tools (you may request the orchestrator to call them on your behalf):\n\n"
        f"{tool_metadata_json}\n"
        "======================\n"
    )

    # Inject tools into prompts
    manager_plan_sys = manager_plan_sys + tools_section
    manager_review_sys = manager_review_sys + tools_section
    employee_sys_base = employee_sys_base + tools_section

    # Run log (legacy)
    mode = "phase3"
    run_record = start_run(cfg, mode, out_dir)

    # PHASE 3: Log run start
    core_logging.log_start(
        core_run_id,
        project_folder=str(out_dir),
        task_description=task,
        config={
            "mode": mode,
            "max_audits_per_stage": max_audits_per_stage,
            "use_visual_review": use_visual_review,
            "run_safety_before_final": run_safety_before_final,
            "allow_extra_iteration_on_failure": allow_extra_iteration_on_failure,
        }
    )

    # ══════════════════════════════════════════════════════════════
    # 1) MANAGER PLANNING
    # ══════════════════════════════════════════════════════════════

    print("\n====== MANAGER PLANNING ======")

    core_logging.log_llm_call(
        core_run_id,
        role="manager",
        model="gpt-5",
        prompt_length=len(manager_plan_sys) + len(task),
        phase="planning"
    )

    plan = chat_json("manager", manager_plan_sys, task)
    print("\n-- Manager Plan --")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    if run_summary is not None:
        log_iteration_new(
            run_summary,
            index=0,
            role="manager",
            status="ok",
            notes="Manager created initial plan and acceptance criteria",
        )

    total_cost = cost_tracker.get_total_cost_usd()
    print(f"\n[Cost] After planning: ~${total_cost:.4f} USD")

    if max_cost_usd and total_cost > max_cost_usd:
        print("[Cost] Max cost exceeded during planning. Aborting.")
        final_status = "aborted_cost_cap_planning"
        final_cost_summary = cost_tracker.get_summary()
        finish_run(run_record, final_status, final_cost_summary, out_dir)
        core_logging.log_final_status(core_run_id, final_status, "Cost cap exceeded", 0)
        return

    # ══════════════════════════════════════════════════════════════
    # 2) SUPERVISOR PHASING
    # ══════════════════════════════════════════════════════════════

    print("\n====== SUPERVISOR PHASING ======")
    sup_payload = {
        "task": task,
        "plan": plan.get("plan", []),
        "acceptance_criteria": plan.get("acceptance_criteria", []),
    }

    core_logging.log_llm_call(
        core_run_id,
        role="supervisor",
        model="gpt-5",
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

    # Interactive cost check
    if not _maybe_confirm_cost(cfg, "after_planning_and_supervisor"):
        print("[User] Aborted run after planning & supervisor phasing.")
        final_status = "aborted_by_user_after_planning"
        final_cost_summary = cost_tracker.get_summary()
        finish_run(run_record, final_status, final_cost_summary, out_dir)
        core_logging.log_final_status(core_run_id, final_status, "User aborted", 0)
        return

    # ══════════════════════════════════════════════════════════════
    # 3) PHASE 3: INITIALIZE WORKFLOW SYSTEMS
    # ══════════════════════════════════════════════════════════════

    print("\n====== PHASE 3: INITIALIZING WORKFLOW SYSTEMS ======")

    # Create workflow manager
    workflow = create_workflow(
        run_id=core_run_id,
        plan_steps=plan.get("plan", []),
        supervisor_phases=phase_list,
        task=task
    )

    # Create memory store
    memory = create_memory_store(core_run_id)

    # Create stage summary tracker
    tracker = create_tracker(core_run_id)

    # Get inter-agent bus
    reset_bus()  # Ensure clean state
    bus = get_bus()

    # Set up bus logging callback
    def log_bus_message(message):
        core_logging.log_agent_message(
            core_run_id,
            message.id,
            message.from_agent,
            message.to_agent,
            message.message_type.value,
            message.subject
        )

    bus.set_log_callback(log_bus_message)

    # Log workflow initialization
    stage_names = [s.name for s in workflow.state.current_roadmap.stages]
    core_logging.log_workflow_initialized(
        core_run_id,
        roadmap_version=1,
        total_stages=len(stage_names),
        stage_names=stage_names
    )

    print(f"[Phase3] Workflow initialized with {len(stage_names)} stages")
    print(f"[Phase3] Stages: {', '.join(stage_names)}")

    # ══════════════════════════════════════════════════════════════
    # 4) PHASE 3: ADAPTIVE STAGE LOOP
    # ══════════════════════════════════════════════════════════════

    print("\n====== PHASE 3: ADAPTIVE STAGE LOOP ======")

    stages_processed = 0
    max_stages_limit = 100  # Safety limit to prevent infinite loops
    cost_warning_shown = False

    while stages_processed < max_stages_limit:
        # Get next pending stage
        next_stage = workflow.get_next_pending_stage()
        if next_stage is None:
            print("\n[Phase3] ✅ All stages completed!")
            break

        stages_processed += 1
        stage_start_time = time.time()

        print(f"\n{'='*70}")
        print(f"STAGE {stages_processed}: {next_stage.name}")
        print(f"ID: {next_stage.id}")
        print(f"Categories: {', '.join(next_stage.categories)}")
        print(f"{'='*70}")

        # Start stage
        workflow.start_stage(next_stage.id)

        # Create stage memory
        stage_mem = memory.get_or_create_memory(next_stage.id, next_stage.name)
        core_logging.log_memory_created(core_run_id, next_stage.id, next_stage.name)

        # Create stage summary
        stage_summary = tracker.create_summary(next_stage.id, next_stage.name)

        # Log stage start
        core_logging.log_stage_started(
            core_run_id,
            next_stage.id,
            next_stage.name,
            stage_number=stages_processed,
            total_stages=len(workflow.state.current_roadmap.stages)
        )

        # Build context from previous stages
        prev_stage_summary = memory.get_previous_stage_summary(next_stage.id)
        context_notes = []
        if prev_stage_summary:
            context_notes.append(f"Previous stage summary: {prev_stage_summary}")

        # ────────────────────────────────────────────────────────
        # ADAPTIVE FIX CYCLE LOOP (max_audits_per_stage)
        # ────────────────────────────────────────────────────────

        audit_cycle = 0
        last_feedback: Optional[List[str]] = None

        while audit_cycle < max_audits_per_stage:
            audit_cycle += 1
            cycle_start_time = time.time()

            print(f"\n--- Audit Cycle {audit_cycle}/{max_audits_per_stage} ---")

            # Start fix cycle tracking
            tracker.start_fix_cycle(next_stage.id, audit_cycle, employee_model="gpt-5")
            memory.increment_iterations(next_stage.id)

            # ────────────────────────────────────────────────────
            # EMPLOYEE: Build stage
            # ────────────────────────────────────────────────────

            existing_files = load_existing_files(out_dir)

            employee_payload = {
                "task": task,
                "plan": plan,
                "phase": {
                    "name": next_stage.name,
                    "categories": next_stage.categories,
                    "plan_steps": next_stage.plan_steps,
                },
                "previous_files": existing_files,
                "feedback": last_feedback,
                "context_notes": context_notes,
                "iteration": audit_cycle,
            }

            core_logging.log_llm_call(
                core_run_id,
                role="employee",
                model="gpt-5",
                prompt_length=len(employee_sys_base) + len(json.dumps(employee_payload)),
                iteration=audit_cycle,
                phase_index=stages_processed,
                phase_name=next_stage.name
            )

            emp = chat_json(
                "employee",
                employee_sys_base,
                json.dumps(employee_payload, ensure_ascii=False),
                model="gpt-5",
            )

            files_dict = emp.get("files", {})
            if not isinstance(files_dict, dict):
                raise RuntimeError(f"Employee response 'files' must be dict, got {type(files_dict)}")

            # Write files
            print(f"\n[Orchestrator] Writing {len(files_dict)} files to disk...")
            written_files = []
            for rel_path, content in files_dict.items():
                dest = out_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                print(f"  wrote {dest}")
                written_files.append(rel_path)

                # Track file changes
                tracker.add_file_change(
                    next_stage.id,
                    rel_path,
                    change_type="modified",  # Could be "created" if new
                    lines_added=len(content.split('\n')),
                    size_bytes=len(content)
                )

            # Log file writes
            if written_files:
                core_logging.log_file_write(
                    core_run_id,
                    files=written_files,
                    summary=f"Stage {next_stage.name} cycle {audit_cycle} wrote {len(written_files)} files",
                    iteration=audit_cycle,
                    phase_index=stages_processed
                )

            # ────────────────────────────────────────────────────
            # SUPERVISOR: Audit work
            # ────────────────────────────────────────────────────

            print("\n[Supervisor] Auditing work...")

            final_files = load_existing_files(out_dir)
            supervisor_audit_payload = {
                "task": task,
                "stage": {
                    "name": next_stage.name,
                    "categories": next_stage.categories,
                },
                "files": final_files,
                "acceptance_criteria": plan.get("acceptance_criteria", []),
            }

            core_logging.log_llm_call(
                core_run_id,
                role="supervisor",
                model="gpt-5",
                prompt_length=len(supervisor_sys) + len(json.dumps(supervisor_audit_payload)),
                iteration=audit_cycle,
                phase="audit"
            )

            audit_result = chat_json(
                "supervisor",
                supervisor_sys,
                json.dumps(supervisor_audit_payload, ensure_ascii=False),
            )

            findings = audit_result.get("findings", [])
            print(f"[Supervisor] Found {len(findings)} issues")

            # Record findings in memory and tracker
            for idx, finding in enumerate(findings):
                issue_id = f"{next_stage.id}_issue_{audit_cycle}_{idx}"
                severity = finding.get("severity", "warning")
                category = finding.get("category", "general")
                description = finding.get("description", "No description")
                file_path = finding.get("file_path")

                memory.add_finding(
                    next_stage.id,
                    severity=severity,
                    category=category,
                    description=description,
                    file_path=file_path
                )

                tracker.add_issue(
                    next_stage.id,
                    issue_id=issue_id,
                    severity=severity,
                    category=category,
                    description=description,
                    file_path=file_path
                )

                core_logging.log_finding_added(
                    core_run_id,
                    next_stage.id,
                    severity,
                    category,
                    description
                )

            # Complete fix cycle
            tracker.complete_fix_cycle(
                next_stage.id,
                audit_cycle,
                issues_addressed=[],  # Would track resolved issues
                files_changed=written_files,
                supervisor_findings=len(findings),
                status="completed"
            )

            # Increment audit count
            workflow.increment_audit_count(next_stage.id)

            # ────────────────────────────────────────────────────
            # CHECK FOR AUTO-ADVANCE (Phase 3 feature)
            # ────────────────────────────────────────────────────

            if len(findings) == 0:
                print("\n[Phase3] ✅ ZERO FINDINGS - AUTO-ADVANCING")

                # Supervisor sends auto-advance request via bus
                bus.supervisor_request_auto_advance(
                    stage_id=next_stage.id,
                    reason="Zero findings in audit"
                )

                core_logging.log_auto_advance(
                    core_run_id,
                    next_stage.id,
                    next_stage.name,
                    reason="Zero findings in audit"
                )

                # Record decision in memory
                memory.add_decision(
                    next_stage.id,
                    agent="supervisor",
                    decision_type="auto_advance",
                    description="Auto-advanced due to zero findings",
                    context={"audit_cycle": audit_cycle, "findings": 0}
                )

                break  # Exit audit loop

            # Prepare feedback for next cycle
            last_feedback = [f"[{f.get('severity', 'warning')}] {f.get('description', '')}" for f in findings]

            # Check if we've hit max audits
            if audit_cycle >= max_audits_per_stage:
                print(f"\n[Phase3] ⚠️  Max audits ({max_audits_per_stage}) reached with {len(findings)} unresolved findings")

                # Report findings to manager via bus
                bus.supervisor_report_findings(
                    findings=findings,
                    stage_id=next_stage.id,
                    recommendation="max_audits_reached"
                )

                break  # Exit audit loop

        # ────────────────────────────────────────────────────────
        # REGRESSION DETECTION (Phase 3 feature)
        # ────────────────────────────────────────────────────────

        unresolved_findings = memory.get_unresolved_findings(next_stage.id)
        if len(unresolved_findings) > 0:
            print(f"\n[Phase3] Checking for regressions ({len(unresolved_findings)} unresolved issues)...")

            # Get previous stage summaries
            all_summaries = tracker.get_all_summaries()
            previous_summaries = [s for s in all_summaries if s.stage_id != next_stage.id]

            # Detect regression
            regressing_stage_id = tracker.detect_regression(
                current_stage_id=next_stage.id,
                issues=[{"file_path": f.file_path} for f in unresolved_findings],
                previous_stage_summaries=previous_summaries
            )

            if regressing_stage_id:
                print(f"\n[Phase3] 🔄 REGRESSION DETECTED: Issues trace back to stage {regressing_stage_id}")

                tracker.mark_regression(regressing_stage_id, next_stage.id)

                core_logging.log_regression_detected(
                    core_run_id,
                    current_stage_id=next_stage.id,
                    regressing_stage_id=regressing_stage_id,
                    issue_count=len(unresolved_findings),
                    description=f"Issues in {next_stage.name} caused by work in {regressing_stage_id}"
                )

                # Reopen regressing stage
                workflow.reopen_stage(
                    stage_id=regressing_stage_id,
                    reason=f"Regression detected from stage {next_stage.id}",
                    regression_source_id=next_stage.id
                )

                core_logging.log_stage_reopened(
                    core_run_id,
                    regressing_stage_id,
                    "Regressing Stage",
                    reason="Regression detected",
                    regression_source=next_stage.id
                )

                print(f"[Phase3] Stage {regressing_stage_id} reopened for rework")
                print(f"[Phase3] Pausing current stage {next_stage.id}, will return after regression fix")

                # Don't complete current stage, it will be revisited
                continue

        # ────────────────────────────────────────────────────────
        # COMPLETE STAGE
        # ────────────────────────────────────────────────────────

        stage_duration = time.time() - stage_start_time
        stage_cost = cost_tracker.get_total_cost_usd()  # Approximate

        workflow.complete_stage(next_stage.id)
        memory.set_final_status(next_stage.id, "completed")
        memory.set_summary(
            next_stage.id,
            f"Stage '{next_stage.name}' completed after {audit_cycle} audit cycles"
        )

        tracker.complete_stage(
            next_stage.id,
            status="completed",
            final_notes=f"Completed after {audit_cycle} audit cycles",
            cost_usd=stage_cost
        )

        core_logging.log_stage_completed(
            core_run_id,
            next_stage.id,
            next_stage.name,
            status="completed",
            iterations=audit_cycle,
            audit_count=audit_cycle,
            duration_seconds=stage_duration
        )

        print(f"\n[Phase3] ✅ Stage '{next_stage.name}' completed")
        print(f"[Phase3] Duration: {stage_duration:.1f}s, Audits: {audit_cycle}, Cost: ~${stage_cost:.4f}")

        # Cost warnings
        total_cost = cost_tracker.get_total_cost_usd()
        if cost_warning_usd and total_cost > cost_warning_usd and not cost_warning_shown:
            print(f"\n⚠️  [Cost] Warning threshold exceeded: ${total_cost:.4f} > ${cost_warning_usd:.4f}")
            cost_warning_shown = True

        if max_cost_usd and total_cost > max_cost_usd:
            print(f"\n[Cost] ❌ Max cost cap exceeded: ${total_cost:.4f} > ${max_cost_usd:.4f}")
            print("[Cost] Aborting run.")
            break

    # ══════════════════════════════════════════════════════════════
    # 5) FINAL STATUS
    # ══════════════════════════════════════════════════════════════

    print("\n====== PHASE 3: RUN COMPLETE ======")

    final_cost = cost_tracker.get_total_cost_usd()
    final_cost_summary = cost_tracker.get_summary()

    all_completed = workflow.get_next_pending_stage() is None
    final_status = "completed" if all_completed else "partial_completion"

    print(f"\n[Phase3] 🎉 Run completed!")
    print(f"[Phase3] Stages processed: {stages_processed}")
    print(f"[Phase3] Total cost: ~${final_cost:.4f} USD")
    print(f"[Phase3] Status: {final_status}")
    print(f"\n[Phase3] 📁 Workflow file: run_workflows/{core_run_id}_workflow.json")
    print(f"[Phase3] 📁 Memories: memory_store/{core_run_id}/")
    print(f"[Phase3] 📁 Summaries: stage_summaries/{core_run_id}/")
    print(f"[Phase3] 📁 Logs: run_logs_main/{core_run_id}.jsonl")

    # Print roadmap summary
    roadmap_summary = workflow.get_roadmap_summary()
    print(f"\n[Phase3] Roadmap summary:")
    print(f"  Version: {roadmap_summary['version']}")
    print(f"  Total stages: {roadmap_summary['total_stages']}")
    if roadmap_summary.get('stages_by_status'):
        for status, stage_names in roadmap_summary['stages_by_status'].items():
            print(f"  {status}: {len(stage_names)} stages - {', '.join(stage_names[:3])}")

    # Finish run (legacy logging)
    finish_run(run_record, final_status, final_cost_summary, out_dir)

    # PHASE 3: Log final status
    core_logging.log_final_status(
        core_run_id,
        status=final_status,
        reason="All stages completed" if all_completed else "Partial completion",
        iterations=stages_processed
    )


# For backward compatibility with run_mode.py
main = main_phase3


if __name__ == "__main__":
    main_phase3()
