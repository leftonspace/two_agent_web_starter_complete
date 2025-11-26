# orchestrator.py
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

NOTE (2025-11-25): Header corrected from "orchestrator_phase3.py" per Phase 8 audit.
"""

from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import core_logging
import cost_tracker
from exec_tools import get_tool_metadata
from git_utils import ensure_repo
from inter_agent_bus import get_bus, reset_bus
from llm import chat_json
from memory_store import create_memory_store
from prompts import load_prompts
from run_logger import (
    RunSummary,
)
from run_logger import (
    finish_run_legacy as finish_run,
)
from run_logger import (
    log_iteration as log_iteration_new,
)
from run_logger import (
    start_run_legacy as start_run,
)
from site_tools import (
    load_existing_files,
)
from stage_summaries import create_tracker

# PHASE 3: Import new systems
from orchestrator_context import OrchestratorContext
from workflow_manager import create_workflow

# =============================================================================
# OPTIONAL MODULE IMPORTS (with availability flags)
# =============================================================================

# Config module (PHASE 0.3)
try:
    import config as config_module
    import paths as paths_module
    CONFIG_AVAILABLE = True
except ImportError:
    config_module = None
    paths_module = None
    CONFIG_AVAILABLE = False

# Domain router (PHASE 1.1)
try:
    import domain_router
    DOMAIN_ROUTER_AVAILABLE = True
except ImportError:
    domain_router = None
    DOMAIN_ROUTER_AVAILABLE = False

# Project stats (PHASE 2.2)
try:
    import project_stats
    PROJECT_STATS_AVAILABLE = True
except ImportError:
    project_stats = None
    PROJECT_STATS_AVAILABLE = False

# Specialist market (PHASE 4)
try:
    import specialist_market
    SPECIALISTS_AVAILABLE = True
except ImportError:
    specialist_market = None
    SPECIALISTS_AVAILABLE = False

# Overseer and self-refinement (PHASE 5)
try:
    import overseer
    import self_refinement
    OVERSEER_AVAILABLE = True
except ImportError:
    overseer = None
    self_refinement = None
    OVERSEER_AVAILABLE = False

# Artifacts logging (PHASE 1.4)
try:
    import artifacts
    ARTIFACTS_AVAILABLE = True
except ImportError:
    artifacts = None
    ARTIFACTS_AVAILABLE = False

# Stage 3 workflow systems
try:
    import workflow_manager
    import memory_store as memory_store_module
    import inter_agent_bus
    STAGE3_AVAILABLE = True
except ImportError:
    workflow_manager = None
    memory_store_module = None
    inter_agent_bus = None
    STAGE3_AVAILABLE = False

# Prompt security (PHASE 1.3)
try:
    import prompt_security
    PROMPT_SECURITY_AVAILABLE = True
except ImportError:
    prompt_security = None
    PROMPT_SECURITY_AVAILABLE = False

# Model router utilities
try:
    from model_router import estimate_complexity, is_stage_important
except ImportError:
    def estimate_complexity(**kwargs):
        return "medium"
    def is_stage_important(**kwargs):
        return False

# Repo router (STAGE 4.3)
try:
    from repo_router import resolve_repo_path
except ImportError:
    def resolve_repo_path(cfg, stage=None):
        from pathlib import Path
        return Path(cfg.get("project_subdir", "default_project"))


def _load_config() -> Dict[str, Any]:
    """
    Load configuration.

    PHASE 0.3: Uses config.get_config() if available, falls back to project_config.json.

    Returns:
        Configuration dictionary
    """
    if CONFIG_AVAILABLE:
        # PHASE 0.3: Use new centralized config module
        cfg_obj = config_module.get_config()
        cfg_dict = cfg_obj.to_dict()
        print("[Config] Loaded configuration from config.py")
        return cfg_dict
    else:
        # Legacy: Load from project_config.json
        cfg_path = Path(__file__).resolve().parent / "project_config.json"
        if not cfg_path.exists():
            raise FileNotFoundError(f"project_config.json not found at {cfg_path}")
        print("[Config] Loaded configuration from project_config.json (legacy)")
        return json.loads(cfg_path.read_text(encoding="utf-8"))


def _validate_cost_config(cfg: Dict[str, Any]) -> None:
    """
    STAGE 5.2: Validate cost-related configuration settings.

    Checks:
    - max_cost_usd and cost_warning_usd are valid floats
    - cost_warning_usd <= max_cost_usd
    - llm_very_important_stages is a list
    - Model names in environment variables are recognized

    Args:
        cfg: Project configuration dict

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate cost caps
    max_cost = cfg.get("max_cost_usd")
    if max_cost is not None:
        try:
            max_cost_float = float(max_cost)
        except (TypeError, ValueError) as e:
            raise ValueError(f"max_cost_usd must be a valid number, got: {max_cost}") from e

        if max_cost_float < 0:
            raise ValueError("max_cost_usd must be >= 0")

    cost_warning = cfg.get("cost_warning_usd")
    if cost_warning is not None:
        try:
            cost_warning_float = float(cost_warning)
        except (TypeError, ValueError) as e:
            raise ValueError(f"cost_warning_usd must be a valid number, got: {cost_warning}") from e

        if cost_warning_float < 0:
            raise ValueError("cost_warning_usd must be >= 0")

        # Check warning <= max if both are set
        if max_cost is not None:
            max_cost_float = float(max_cost)
            if cost_warning_float > max_cost_float:
                print(
                    f"[Config Warning] cost_warning_usd ({cost_warning_float}) > "
                    f"max_cost_usd ({max_cost_float}). "
                    "Warning will trigger before cost cap."
                )

    # Validate llm_very_important_stages
    very_important = cfg.get("llm_very_important_stages")
    if very_important is not None and not isinstance(very_important, list):
        raise ValueError(
            f"llm_very_important_stages must be a list, got: {type(very_important).__name__}"
        )

    # Validate interactive_cost_mode
    cost_mode = cfg.get("interactive_cost_mode", "off")
    valid_modes = ["off", "once", "always"]
    if cost_mode not in valid_modes:
        print(
            f"[Config Warning] interactive_cost_mode='{cost_mode}' not recognized. "
            f"Valid values: {valid_modes}. Defaulting to 'off'."
        )

    print("[Config] Cost configuration validated successfully.")


def _ensure_out_dir(cfg: Dict[str, Any]) -> Path:
    """
    Determine output directory for the project.

    PHASE 0.3: Uses paths.resolve_project_path() if available.
    STAGE 4.3: For multi-repo projects, returns the first repo's path.
    For single-repo projects, uses project_subdir.

    Args:
        cfg: Project configuration

    Returns:
        Path to output directory
    """
    # STAGE 4.3: Check for multi-repo mode
    repos = cfg.get("repos", [])
    if repos and isinstance(repos, list) and len(repos) > 0:
        # Multi-repo mode: use first repo as default
        first_repo_path = repos[0].get("path")
        if first_repo_path:
            out_dir = Path(first_repo_path).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            return out_dir

    # Single-repo mode
    if CONFIG_AVAILABLE and paths_module:
        # PHASE 0.3: Use paths module for directory resolution
        project_subdir = cfg.get("project_subdir", "default_project")
        out_dir = paths_module.resolve_project_path(project_subdir)
        paths_module.ensure_dir(out_dir)
        print(f"[Paths] Using paths.resolve_project_path(): {out_dir}")
        return out_dir
    else:
        # Legacy: Construct path manually
        root = Path(__file__).resolve().parent.parent  # .. from agent to root
        sites_dir = root / "sites"
        out_dir = sites_dir / cfg["project_subdir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Paths] Using legacy path resolution: {out_dir}")
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


def _choose_model_for_agent(
    role: str,
    task_type: str,
    iteration: int,
    last_status: Optional[str] = None,
    last_tests: Optional[Dict[str, Any]] = None,
    stage: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    files_count: int = 0,
) -> str:
    """
    STAGE 5: Choose model using central model router with GPT-5 constraints.

    Uses model_router.choose_model() to enforce:
    - GPT-5 only on 2nd or 3rd iterations
    - GPT-5 only when complexity is high or task is very important
    - Cost-aware model selection

    Args:
        role: Agent role (manager, employee, supervisor)
        task_type: Type of task (planning, code, review)
        iteration: Current iteration number (1-indexed)
        last_status: Previous iteration status
        last_tests: Previous test results
        stage: Current stage metadata
        config: Project configuration
        run_id: Current run ID for logging
        files_count: Number of files modified so far (STAGE 5.2)

    Returns:
        Model identifier string
    """
    # Estimate complexity based on previous failures and stage metadata
    previous_failures = 0
    if last_status == "needs_changes":
        previous_failures += 1
    if last_tests and not last_tests.get("all_passed"):
        previous_failures += 1

    # STAGE 5.2: Use actual file counts for complexity estimation
    complexity = estimate_complexity(
        stage=stage,
        previous_failures=previous_failures,
        files_count=files_count,
        config=config,
    )

    # Check if stage is marked as very important
    is_important = is_stage_important(stage=stage, config=config) if stage else False

    # Use model router to select model
    from model_router import choose_model

    return choose_model(
        task_type=task_type,
        complexity=complexity,
        role=role,
        interaction_index=iteration,
        is_very_important=is_important,
        config=config,
    )


def _maybe_confirm_cost(cfg: Dict[str, Any], stage_label: str) -> bool:
    """
    Ask the user once whether they accept the current cost and want to continue.

    Uses cfg['interactive_cost_mode'] == 'off' or 'once'.
    """
    mode = str(cfg.get("interactive_cost_mode", "off")).lower().strip()
    if mode != "once":
        return True

    total_cost = cost_tracker.get_total_cost_usd()
    warning_threshold = float(cfg.get("cost_warning_usd", 0) or 0)

    if mode == "once" and stage_label != "after_planning_and_supervisor":
        return True

    if total_cost < warning_threshold:
        return True

    print(f"\n[Cost] Current cost: ~${total_cost:.4f} USD")
    print(f"[Cost] Checkpoint: {stage_label}")
    response = input("[Cost] Continue? (y/n): ").strip().lower()
    return response == "y"


def _present_plan_for_confirmation(
    plan: Dict[str, Any],
    phases: List[Dict[str, Any]],
    cfg: Dict[str, Any],
) -> bool:
    """
    PHASE 6.1: Present the execution plan and wait for user confirmation.

    Human UX Hardening: Before executing complex tasks, JARVIS presents
    a structured plan and waits for explicit user approval.

    Args:
        plan: Manager's plan from initial planning phase
        phases: Supervisor's phased breakdown
        cfg: Project configuration

    Returns:
        True if user confirms, False to abort
    """
    require_confirmation = cfg.get("require_plan_confirmation", True)

    if not require_confirmation:
        print("[PlanConfirm] Plan confirmation disabled (require_plan_confirmation=false)")
        return True

    # Build structured plan summary
    print("\n" + "=" * 70)
    print("  📋 EXECUTION PLAN - AWAITING YOUR CONFIRMATION")
    print("=" * 70)

    # Show acceptance criteria
    criteria = plan.get("acceptance_criteria", [])
    if criteria:
        print("\n🎯 Acceptance Criteria:")
        for i, c in enumerate(criteria, 1):
            print(f"   {i}. {c}")

    # Show planned steps
    steps = plan.get("plan", [])
    if steps:
        print("\n📝 Planned Steps:")
        for i, step in enumerate(steps, 1):
            if isinstance(step, dict):
                print(f"   {i}. {step.get('description', step.get('name', str(step)))}")
            else:
                print(f"   {i}. {step}")

    # Show execution phases
    if phases:
        print("\n🔄 Execution Phases:")
        for i, phase in enumerate(phases, 1):
            phase_name = phase.get("name", f"Phase {i}")
            categories = phase.get("categories", [])
            cat_str = ", ".join(categories[:3]) if categories else "General"
            if len(categories) > 3:
                cat_str += f" +{len(categories) - 3} more"
            print(f"   {i}. {phase_name}")
            print(f"      Categories: {cat_str}")

    # Show cost estimate if available
    max_cost = cfg.get("max_cost_usd", 0)
    if max_cost:
        print(f"\n💰 Budget Cap: ${max_cost:.2f} USD")

    max_rounds = cfg.get("max_rounds", 1)
    print(f"🔁 Max Iterations: {max_rounds}")

    print("\n" + "-" * 70)
    print("  ⚠️  Employee agents will begin execution after confirmation.")
    print("-" * 70)

    # Wait for confirmation
    try:
        response = input("\n[Proceed] Execute this plan? (y/n/details): ").strip().lower()

        if response == "details":
            # Show full JSON plan
            print("\n📄 Full Plan JSON:")
            print(json.dumps(plan, indent=2, ensure_ascii=False))
            print("\n📄 Full Phases JSON:")
            print(json.dumps(phases, indent=2, ensure_ascii=False))
            # Ask again after showing details
            response = input("\n[Proceed] Execute this plan? (y/n): ").strip().lower()

        if response == "y":
            print("\n[PlanConfirm] ✅ Plan confirmed - proceeding with execution...")
            return True
        else:
            print("\n[PlanConfirm] ❌ Plan rejected by user - aborting run.")
            return False

    except (EOFError, KeyboardInterrupt):
        # Non-interactive mode or interrupted - check for auto-approve setting
        auto_approve = cfg.get("auto_approve_plan", False)
        if auto_approve:
            print("\n[PlanConfirm] Auto-approving plan (auto_approve_plan=true)")
            return True
        print("\n[PlanConfirm] Non-interactive mode without auto_approve_plan - aborting.")
        return False


def main(
    run_summary: Optional[RunSummary] = None,
    mission_id: Optional[str] = None,
    cfg_override: Optional[Dict[str, Any]] = None,
    context: Optional[OrchestratorContext] = None,
) -> Dict[str, Any]:
    """
    PHASE 3: Main adaptive multi-agent orchestrator.

    PHASE 1.5: Now supports dependency injection for easier testing.

    Args:
        run_summary: Optional RunSummary for STAGE 2 logging.
                     If provided, iterations will be logged automatically.
        mission_id: Optional mission ID for PHASE 1.4 artifact logging.
                    If provided, artifacts will be logged to artifacts/<mission_id>/.
        cfg_override: Optional config dict override. If provided, uses this instead of loading from file.
        context: Optional OrchestratorContext for dependency injection.
                 If None, creates default context with real implementations.

    Returns:
        Dict with run results (status, rounds_completed, cost_summary, etc.)
    """
    # PHASE 1.5: Initialize dependency injection context
    if context is None:
        context = OrchestratorContext.create_default(cfg_override)
        print("[DI] Using default production context")
    else:
        print("[DI] Using provided context (likely test context)")

    # STAGE 2.2: Create run ID for core logging
    core_run_id = context.logger.new_run_id()

    cfg = cfg_override if cfg_override is not None else _load_config()
    # STAGE 5.2: Validate cost configuration
    _validate_cost_config(cfg)
    out_dir = _ensure_out_dir(cfg)

    task: str = cfg["task"]

    # PHASE 1.3: Sanitize and validate task input to prevent prompt injection (V1)
    original_task = task
    detected_patterns = []
    was_blocked = False

    if PROMPT_SECURITY_AVAILABLE and prompt_security is not None:
        task, detected_patterns, was_blocked = prompt_security.check_and_sanitize_task(
            task,
            context="orchestrator_main",
            session_id=core_run_id,
            strict_mode=False,  # Allow with sanitization rather than blocking
        )

    if detected_patterns:
        print(f"[Security] Detected injection patterns: {', '.join(detected_patterns)}")
        if was_blocked:
            print("[Security] CRITICAL: Task blocked due to high-severity injection attempt")
            print(f"[Security] Original task: {original_task[:200]}...")
            # Log security event
            context.logger.log_event(core_run_id, "security_task_blocked", {
                "original_task": original_task,
                "detected_patterns": detected_patterns,
            })
            return {
                "status": "blocked_security",
                "reason": "Task blocked due to prompt injection attempt",
                "detected_patterns": detected_patterns,
            }
        else:
            print(f"[Security] Task sanitized (patterns detected but not blocked)")
            context.logger.log_event(core_run_id, "security_task_sanitized", {
                "detected_patterns": detected_patterns,
                "original_length": len(original_task),
                "sanitized_length": len(task),
            })

    max_rounds: int = int(cfg.get("max_rounds", 1))
    max_audits_per_stage: int = int(cfg.get("max_audits_per_stage", 3))
    use_visual_review: bool = bool(cfg.get("use_visual_review", False))
    prompts_file: str = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd: float = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd: float = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    _interactive_cost_mode: str = cfg.get("interactive_cost_mode", "off")
    use_git: bool = bool(cfg.get("use_git", False))

    # PHASE 1.4: Git secret scanning configuration
    git_secret_scanning_enabled: bool = bool(cfg.get("git_secret_scanning_enabled", True))

    # STAGE 1: Safety configuration
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
    print(f"git_secret_scanning_enabled: {git_secret_scanning_enabled}")
    print(f"run_safety_before_final: {run_safety_before_final}")

    # STAGE 3.3: Validate API connectivity before starting work
    print("\n[API] Validating OpenAI API connectivity...")
    # Load llm.py explicitly to bypass llm/ package shadowing (Phase 9)
    llm_file = Path(__file__).parent / "llm.py"
    spec = importlib.util.spec_from_file_location("llm_module", llm_file)
    llm_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(llm_module)
    validate_api_connectivity = llm_module.validate_api_connectivity
    is_valid, error_message = validate_api_connectivity()

    if not is_valid:
        print(f"\n❌ API VALIDATION FAILED: {error_message}")
        print("\nPossible solutions:")
        print("  1. Check your OPENAI_API_KEY environment variable")
        print("  2. Verify network connectivity to api.openai.com")
        print("  3. Check OpenAI service status at status.openai.com")
        print("  4. Try using mode='3loop_legacy' for offline testing")
        print("\nAborting run due to API connectivity issues.")
        raise RuntimeError(f"API validation failed: {error_message}")

    print("[API] ✅ OpenAI API is accessible\n")

    # Snapshots
    snapshots_root = out_dir / ".history"
    snapshots_root.mkdir(parents=True, exist_ok=True)

    # Git
    git_ready = False
    if use_git:
        git_ready = context.git_utils.ensure_repo(out_dir)

    # Cost tracker
    context.cost_tracker.reset()

    # Load prompts
    prompts = context.prompts.load_prompts(prompts_file)
    manager_plan_sys = prompts["manager_plan_sys"]
    manager_review_sys = prompts["manager_review_sys"]
    employee_sys_base = prompts["employee_sys"]
    supervisor_sys = _build_supervisor_sys(manager_plan_sys)

    # PHASE 1.1: Domain classification and domain-specific prompting
    domain = None
    domain_allowed_tools = None
    if DOMAIN_ROUTER_AVAILABLE:
        try:
            # Classify task into domain
            domain = domain_router.classify_task(task)
            print(f"\n[Domain] Task classified as: {domain.value}")

            # Get domain-specific prompt additions
            domain_prompts = domain_router.get_domain_prompts(domain)
            domain_allowed_tools = domain_router.get_domain_tools(domain)

            print(f"[Domain] Using domain-specific prompts for {domain.value}")
            print(f"[Domain] Allowed tools for {domain.value}: {len(domain_allowed_tools)} tools")

            # Append domain-specific prompt additions to each role
            if domain_prompts.get("manager"):
                manager_plan_sys = manager_plan_sys + "\n\n" + domain_prompts["manager"]
                manager_review_sys = manager_review_sys + "\n\n" + domain_prompts["manager"]
            if domain_prompts.get("supervisor"):
                supervisor_sys = supervisor_sys + "\n\n" + domain_prompts["supervisor"]
            if domain_prompts.get("employee"):
                employee_sys_base = employee_sys_base + "\n\n" + domain_prompts["employee"]

        except Exception as e:
            print(f"[Domain] Warning: Failed to classify domain: {e}")
            print("[Domain] Falling back to generic prompts")
    else:
        print("[Domain] Domain router not available - using generic prompts")

    # PHASE 2.2: Risk analysis integration - inject risky files into manager prompts
    if PROJECT_STATS_AVAILABLE:
        try:
            risky_files = project_stats.get_risky_files(project_path=Path(out_dir), limit=5)
            if risky_files:
                risk_summary = project_stats.format_risk_summary(risky_files)
                # Inject risk insights into both planning and review prompts
                risk_prompt_addition = f"\n\n## Historical Risk Analysis\n\n{risk_summary}"
                manager_plan_sys = manager_plan_sys + risk_prompt_addition
                manager_review_sys = manager_review_sys + risk_prompt_addition
                print(f"[Risk] Identified {len(risky_files)} high-risk files for manager awareness")
        except Exception as e:
            print(f"[Risk] Warning: Failed to get risk insights: {e}")

    # PHASE 4: Specialist system integration
    specialist_recommendation = None
    specialist_info = None
    use_specialist = False

    if SPECIALISTS_AVAILABLE:
        try:
            # Initialize specialist market
            market = specialist_market.SpecialistMarket()

            # Get budget for specialist recommendation
            specialist_budget = max_cost_usd if max_cost_usd > 0 else None

            # Get specialist recommendation
            specialist_recommendation = market.recommend_specialist(
                task=task,
                budget_usd=specialist_budget,
                prefer_performance=True,
                min_confidence="low"
            )

            if specialist_recommendation:
                specialist_profile = specialist_recommendation.specialist
                use_specialist = True

                print(f"\n[Specialist] Recommended: {specialist_profile.name}")
                print(f"[Specialist] Type: {specialist_profile.specialist_type.value}")
                print(f"[Specialist] Match Score: {specialist_recommendation.match_score:.2f}")
                print(f"[Specialist] Performance Score: {specialist_recommendation.performance_score:.2f}")
                print(f"[Specialist] Estimated Cost: ${specialist_recommendation.estimated_cost_usd:.2f}")
                print(f"[Specialist] Confidence: {specialist_recommendation.confidence}")

                # Get specialist-specific system prompt additions
                specialist_prompt = specialist_profile.get_system_prompt(task)

                # Append specialist expertise to agent prompts
                specialist_section = f"\n\n=== SPECIALIST EXPERTISE ===\n{specialist_prompt}\n======================\n"
                employee_sys_base = employee_sys_base + specialist_section

                # Store specialist info for later logging
                specialist_info = {
                    "type": specialist_profile.specialist_type.value,
                    "name": specialist_profile.name,
                    "match_score": specialist_recommendation.match_score,
                    "performance_score": specialist_recommendation.performance_score,
                    "cost_multiplier": specialist_profile.cost_multiplier,
                    "estimated_cost_usd": specialist_recommendation.estimated_cost_usd,
                }
            else:
                print("[Specialist] No specialist recommendation available - using generic agent")

        except Exception as e:
            print(f"[Specialist] Warning: Failed to get specialist recommendation: {e}")
            print("[Specialist] Falling back to generic agent")
    else:
        print("[Specialist] Specialist system not available - using generic agent")

    # PHASE 5: Overseer strategic planning
    overseer_strategy = None
    if OVERSEER_AVAILABLE:
        try:
            overseer_instance = overseer.Overseer()

            # Get strategic recommendations for this mission
            overseer_strategy = overseer_instance.recommend_mission_strategy(
                task=task,
                budget_usd=max_cost_usd if max_cost_usd > 0 else None,
                max_iterations=max_rounds
            )

            print(f"\n[Overseer] Strategic Analysis:")
            print(f"[Overseer] Estimated Cost: ${overseer_strategy['estimated_cost_usd']:.2f}")
            print(f"[Overseer] Estimated Iterations: {overseer_strategy['estimated_iterations']}")
            print(f"[Overseer] Confidence: {overseer_strategy['confidence']}")

            if overseer_strategy["recommendations"]:
                print(f"[Overseer] Recommendations:")
                for rec in overseer_strategy["recommendations"]:
                    print(f"[Overseer]   - {rec}")

        except Exception as e:
            print(f"[Overseer] Warning: Failed to get strategic recommendations: {e}")
    else:
        print("[Overseer] Overseer system not available")

    # STAGE 2.1: Get tool metadata for injection into prompts
    tool_metadata_str = context.exec_tools.get_tool_metadata()
    tool_metadata = json.loads(tool_metadata_str) if isinstance(tool_metadata_str, str) else tool_metadata_str

    # PHASE 1.1: Filter tools by domain if domain routing is active
    if domain_allowed_tools is not None:
        # Filter to only allowed tools for this domain
        filtered_tools = [
            tool for tool in tool_metadata
            if tool.get("name") in domain_allowed_tools
        ]
        if filtered_tools:
            tool_metadata = filtered_tools
            print(f"[Domain] Filtered tools: {len(tool_metadata)} tools available")
        else:
            print(f"[Domain] Warning: No matching tools found, using all tools")

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

    # Run log
    mode = "3loop"
    # PHASE 1.6: Removed run_logger.start_run() - now using core_logging only
    # run_record = context.run_logger.start_run(cfg, mode, out_dir)

    # STAGE 2.2: Log run start
    context.logger.log_start(
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

    # STAGE 5: Use model router for manager planning
    manager_model = _choose_model_for_agent(
        role="manager",
        task_type="planning",
        iteration=1,  # Planning is pre-iteration
        config=cfg,
        run_id=core_run_id,
    )
    print(f"[ModelRouter] Manager planning will use: {manager_model}")

    # STAGE 2.2: Log LLM call
    context.logger.log_llm_call(
        core_run_id,
        role="manager",
        model=manager_model,
        prompt_length=len(manager_plan_sys) + len(task),
        phase="planning"
    )

    plan = context.llm.chat_json(
        "manager",
        manager_plan_sys,
        task,
        model=manager_model,
        task_type="planning",
        complexity="low",
        interaction_index=1,
        run_id=core_run_id,
        config=cfg,
        max_cost_usd=max_cost_usd,
    )
    print("\n-- Manager Plan --")
    print(json.dumps(plan, indent=2, ensure_ascii=False))

    # PHASE 1.4: Log plan artifact if mission_id provided
    if mission_id and ARTIFACTS_AVAILABLE:
        try:
            plan_content = json.dumps(plan, indent=2, ensure_ascii=False)
            artifacts.log_plan(
                mission_id=mission_id,
                role="manager",
                plan_content=plan_content,
                stages=plan.get("plan", []),
            )
        except Exception as e:
            print(f"[Mission] Warning: Failed to log plan artifact: {e}")

    # STAGE 2: Log manager planning phase
    if run_summary is not None:
        context.run_logger.log_iteration(
            run_summary,
            index=0,
            role="manager",
            status="ok",
            notes="Manager created initial plan and acceptance criteria",
        )

    total_cost = context.cost_tracker.get_total_cost_usd()
    print(f"\n[Cost] After planning: ~${total_cost:.4f} USD")

    # STAGE 5.2: Log cost checkpoint after planning
    context.logger.log_cost_checkpoint(
        core_run_id,
        checkpoint="after_planning",
        total_cost_usd=total_cost,
        max_cost_usd=max_cost_usd,
        cost_summary=context.cost_tracker.get_summary(),
    )

    if max_cost_usd and total_cost > max_cost_usd:
        print("[Cost] Max cost exceeded during planning. Aborting.")
        final_status = "aborted_cost_cap_planning"
        final_cost_summary = context.cost_tracker.get_summary()
        # PHASE 1.6: core_logging.log_final_status() handles this now
        # context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)
        context.logger.log_final_status(
            core_run_id,
            status=final_status,
            reason="Cost cap exceeded during planning phase",
            iterations=0,
            total_cost_usd=total_cost
        )
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

    # STAGE 5: Use model router for supervisor
    supervisor_model = _choose_model_for_agent(
        role="supervisor",
        task_type="planning",
        iteration=1,  # Phasing is pre-iteration
        config=cfg,
        run_id=core_run_id,
    )
    print(f"[ModelRouter] Supervisor phasing will use: {supervisor_model}")

    # STAGE 2.2: Log LLM call
    context.logger.log_llm_call(
        core_run_id,
        role="supervisor",
        model=supervisor_model,
        prompt_length=len(supervisor_sys) + len(json.dumps(sup_payload)),
        phase="supervisor_phasing"
    )

    phases = context.llm.chat_json(
        "supervisor",
        supervisor_sys,
        json.dumps(sup_payload, ensure_ascii=False),
        model=supervisor_model,
        task_type="planning",
        complexity="low",
        interaction_index=1,
        run_id=core_run_id,
        config=cfg,
        max_cost_usd=max_cost_usd,
    )

    # STAGE 3.3: Check for LLM failure during phasing
    if phases.get("llm_failure") or phases.get("status") == "llm_failure":
        reason = phases.get("reason", "Unknown LLM error")
        print(f"\n❌ SUPERVISOR PHASING FAILED: {reason}")
        print("Cannot proceed without supervisor phases.")
        raise RuntimeError(f"Supervisor LLM call failed during phasing: {reason}")

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

    # STAGE 3: Initialize workflow manager, memory store, and inter-agent bus
    workflow_mgr = None
    mem_store = None
    agent_bus = None

    if STAGE3_AVAILABLE:
        try:
            # Initialize workflow manager with run ID
            workflow_mgr = workflow_manager.WorkflowManager(run_id=core_run_id)

            # Create initial roadmap from supervisor phases
            workflow_mgr.initialize(
                plan_steps=plan.get("plan", []),
                supervisor_phases=phase_list,
                task=task
            )

            print(f"\n[Stage3] Initialized workflow with {len(phase_list)} stages")
            roadmap_summary = workflow_mgr.get_roadmap_summary()
            print(f"[Stage3] Roadmap: {roadmap_summary['total_stages']} stages ({roadmap_summary['pending_count']} pending)")

            # Initialize memory store
            mem_store = memory_store.MemoryStore(run_id=core_run_id)
            print("[Stage3] Initialized memory store")

            # Initialize inter-agent bus
            agent_bus = inter_agent_bus.InterAgentBus()

            # Set up logging callback for bus messages
            def log_bus_message(msg: inter_agent_bus.Message):
                try:
                    context.logger.log_event(
                        core_run_id,
                        event_type="agent_message",
                        data={
                            "from": msg.from_agent,
                            "to": msg.to_agent,
                            "type": msg.message_type.value,
                            "subject": msg.subject,
                        }
                    )
                except Exception:
                    pass  # Best effort

            agent_bus.set_log_callback(log_bus_message)
            print("[Stage3] Initialized inter-agent bus")

        except Exception as e:
            print(f"[Stage3] Warning: Failed to initialize Stage 3 systems: {e}")
            workflow_mgr = None
            mem_store = None
            agent_bus = None

    # Optional interactive cost check after planning+phasing
    if not _maybe_confirm_cost(cfg, "after_planning_and_supervisor"):
        print("[User] Aborted run after planning & supervisor phasing.")
        final_status = "aborted_by_user_after_planning"
        final_cost_summary = context.cost_tracker.get_summary()
        # PHASE 1.6: core_logging.log_final_status() handles this now
        # context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)
        context.logger.log_final_status(
            core_run_id,
            status=final_status,
            reason="Run aborted by user after planning and supervisor phasing",
            iterations=0,
            total_cost_usd=context.cost_tracker.get_total_cost_usd()
        )
        return

    # ══════════════════════════════════════════════════════════════
    # PHASE 6.1: PLAN CONFIRMATION (Human UX Hardening)
    # ══════════════════════════════════════════════════════════════
    # Before executing complex tasks, present the plan and wait for
    # explicit user confirmation. This prevents unintended execution
    # and gives users visibility into what will be done.
    if not _present_plan_for_confirmation(plan, phase_list, cfg):
        print("[User] Plan rejected - aborting execution.")
        final_status = "aborted_plan_rejected"
        final_cost_summary = context.cost_tracker.get_summary()
        context.logger.log_final_status(
            core_run_id,
            status=final_status,
            reason="User rejected the execution plan",
            iterations=0,
            total_cost_usd=context.cost_tracker.get_total_cost_usd()
        )
        # Log the rejection event
        context.logger.log_event(core_run_id, "plan_rejected", {
            "plan_steps": len(plan.get("plan", [])),
            "phases": len(phase_list),
        })
        return {
            "status": "aborted",
            "reason": "Plan rejected by user",
            "core_run_id": core_run_id,
        }

    # Log plan confirmation
    context.logger.log_event(core_run_id, "plan_confirmed", {
        "plan_steps": len(plan.get("plan", [])),
        "phases": len(phase_list),
    })

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

    # STAGE 5.2: Track cumulative file count for complexity estimation
    cumulative_files_written = 0

    # PHASE 2.1a: Track all unique files modified across iterations for knowledge graph
    all_files_modified = set()  # Track unique file paths

    # STAGE 3: Track current stage for workflow integration
    current_stage_idx = 0  # Index into phase_list
    current_stage_obj = None  # Current Stage object from workflow_mgr

    # Initialize iteration tracking variables
    last_status: Optional[str] = None
    last_tests: Optional[Dict[str, Any]] = None
    last_feedback: Optional[List[str]] = None
    extra_iteration_granted = False
    safety_failed_on_final = False
    cost_warning_shown = False
    final_status = "unknown"
    stages_processed = 0
    all_completed = False

    # Initialize next_stage for iteration loop
    next_stage = None

    # Start first stage if workflow manager available
    if workflow_mgr is not None and phase_list:
        try:
            next_stage = workflow_mgr.get_next_pending_stage()
            if next_stage:
                current_stage_obj = workflow_mgr.start_stage(next_stage.id)
                print(f"\n[Stage3] Started stage: {current_stage_obj.name}")

                # Initialize stage memory
                if mem_store is not None:
                    mem_store.get_or_create_memory(
                        stage_id=current_stage_obj.id,
                        stage_name=current_stage_obj.name
                    )
        except Exception as e:
            print(f"[Stage3] Warning: Failed to start first stage: {e}")

    # 3) Iterations: Supervisor → Employee (per phase) → Manager review
    for iteration in range(1, max_rounds + 1):
        print(f"\n====== ITERATION {iteration} / {max_rounds} ======")


        # PHASE 1.4: Log iteration start artifact
        if mission_id and ARTIFACTS_AVAILABLE:
            try:
                artifacts.log_iteration_start(
                    mission_id=mission_id,
                    iteration_num=iteration,
                )
            except Exception as e:
                print(f"[Mission] Warning: Failed to log iteration start: {e}")

        # STAGE 2.2: Log iteration begin
        context.logger.log_iteration_begin(
            core_run_id,
            iteration=iteration,
            mode=mode,  # "3loop" for Phase 3 orchestrator
            stage_name=phase_list[current_stage_idx].get("name", f"Stage {current_stage_idx}") if current_stage_idx < len(phase_list) else "Unknown"
        )

        # STAGE 5: Use model router for employee
        # STAGE 5.2: Pass cumulative file count for complexity estimation
        employee_model = _choose_model_for_agent(
            role="employee",
            task_type="code",
            iteration=iteration,
            last_status=last_status,
            last_tests=last_tests,
            config=cfg,
            run_id=core_run_id,
            files_count=cumulative_files_written,
        )
        print(f"[ModelRouter] Employee will use model: {employee_model}")

        existing_files = context.site_tools.load_existing_files(out_dir)
        if existing_files:
            print(f"[Files] Loaded {len(existing_files)} existing files from {out_dir}")
        else:
            print("[Files] No existing files loaded; starting from scratch.")


        # Get current phase info
        phase_index = current_stage_idx
        phase = phase_list[phase_index] if phase_index < len(phase_list) else {"name": "Unknown"}

        # Log stage start - only if next_stage is available
        if next_stage is not None:
            core_logging.log_stage_started(
                core_run_id,
                next_stage.id,
                next_stage.name,
                stage_number=stages_processed,
                total_stages=len(workflow.state.current_roadmap.stages) if hasattr(workflow, 'state') and hasattr(workflow.state, 'current_roadmap') else len(phase_list)
            )
        else:
            # Fallback logging when next_stage is not available
            core_logging.log_stage_started(
                core_run_id,
                f"stage_{phase_index}",
                phase.get("name", f"Stage {phase_index}"),
                stage_number=stages_processed,
                total_stages=len(phase_list)
            )

        # Build context from previous stages
        stage_id = next_stage.id if next_stage is not None else f"stage_{phase_index}"
        stage_name = next_stage.name if next_stage is not None else phase.get("name", f"Stage {phase_index}")
        stage_categories = next_stage.categories if next_stage is not None else phase.get("categories", [])
        stage_plan_steps = next_stage.plan_steps if next_stage is not None else phase.get("plan_steps", [])

        prev_stage_summary = memory.get_previous_stage_summary(stage_id)
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

            print(f"\n--- Audit Cycle {audit_cycle}/{max_audits_per_stage} ---")

            # Start fix cycle tracking
            tracker.start_fix_cycle(stage_id, audit_cycle, employee_model="gpt-4o")
            memory.increment_iterations(stage_id)

            # ────────────────────────────────────────────────────
            # EMPLOYEE: Build stage
            # ────────────────────────────────────────────────────

            existing_files = load_existing_files(out_dir)

            employee_payload = {
                "task": task,
                "plan": plan,
                "phase": {
                    "name": stage_name,
                    "categories": stage_categories,
                    "plan_steps": stage_plan_steps,
                },
                "previous_files": existing_files,
                "feedback": last_feedback,
                "context_notes": context_notes,
                "iteration": audit_cycle,
            }
            phase_payload = employee_payload  # Alias for backward compatibility

            employee_sys_phase = employee_sys_base

            print(
                f"\n[Employee] Running phase {phase_index}: "
                f"{phase.get('name', 'Unnamed phase')}"
            )

            # STAGE 2.2: Log LLM call
            context.logger.log_llm_call(
                core_run_id,
                role="employee",
                model="gpt-4o",
                prompt_length=len(employee_sys_base) + len(json.dumps(employee_payload)),
                iteration=audit_cycle,
                phase_index=stages_processed,
                phase_name=stage_name
            )

            emp = context.llm.chat_json(
                "employee",
                employee_sys_phase,
                json.dumps(phase_payload, ensure_ascii=False),
                model=employee_model,
                task_type="code",
                interaction_index=iteration,
                run_id=core_run_id,
                config=cfg,
                max_cost_usd=max_cost_usd,
            )

            # STAGE 3.3: Check for LLM failure
            if emp.get("llm_failure") or emp.get("status") == "llm_failure":
                reason = emp.get("reason", "Unknown LLM error")
                original_model = emp.get("original_model", "unknown")
                print(f"\n❌ EMPLOYEE LLM CALL FAILED: {reason}")
                print(f"[Stage3] Model: {original_model}")

                # Check if fallback was used
                fallback_used = emp.get("_fallback_used", False)
                if fallback_used:
                    fallback_model = emp.get("_fallback_model", "unknown")
                    print(f"[Stage3] ⚠️  Even fallback model ({fallback_model}) failed")
                    # Log model fallback event
                    core_logging.log_model_fallback(
                        core_run_id,
                        stage_id,
                        "employee",
                        original_model,
                        fallback_model,
                        "Primary model failed, fallback also failed"
                    )

                # STAGE 3.3 FIX: Use log_llm_failure helper (proper payload dict)
                core_logging.log_llm_failure(
                    core_run_id,
                    stage_id=stage_id,
                    stage_name=stage_name,
                    role="employee",
                    reason=reason,
                    retry_count=5,  # From llm.MAX_RETRIES
                    model=original_model
                )

                # STAGE 3.3: Mark as pending_retry instead of hard failure
                print("[Stage3] Marking stage as pending_retry for later revisit")
                memory.set_final_status(stage_id, "pending_retry")
                tracker.complete_stage(stage_id, "pending_retry", reason)

                # Log pending retry
                core_logging.log_stage_pending_retry(
                    core_run_id,
                    stage_id,
                    stage_name,
                    reason=f"Employee LLM failure: {reason}"
                )

                # Don't complete or reopen - just move to next stage
                # The retry pass will revisit this stage
                break  # Exit audit loop

            files_dict = emp.get("files", {})
            if not isinstance(files_dict, dict):
                raise RuntimeError(f"Employee response 'files' must be dict, got {type(files_dict)}")

            # STAGE 4.3: Determine target repo for this phase
            phase_repo_path = resolve_repo_path(cfg, stage=phase)
            print(f"\n[MultiRepo] Target repo: {phase_repo_path}")

            # PHASE 3.4: Check simulation mode - skip writes if enabled
            simulation_mode = False
            if CONFIG_AVAILABLE:
                cfg_obj = config_module.get_config()
                simulation_mode = (cfg_obj.simulation.value != "off")

            if simulation_mode:
                print("\n[Simulation] Simulation mode enabled - skipping file writes")
                written_files = list(files_dict.keys())
                for rel_path in written_files:
                    print(f"  [simulated] {rel_path}")
            else:
                print("\n[Orchestrator] Writing files to disk...")
                written_files = []
                for rel_path, content in files_dict.items():
                    dest = phase_repo_path / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content, encoding="utf-8")
                    print(f"  wrote {dest}")
                    written_files.append(rel_path)

            # STAGE 5.2: Update cumulative file count
            cumulative_files_written += len(written_files)

            # PHASE 2.1a: Track unique files for knowledge graph
            all_files_modified.update(written_files)

            # Log file writes
            if written_files:
                context.logger.log_file_write(
                    core_run_id,
                    files=written_files,
                    summary=f"Employee phase {phase_index} wrote {len(written_files)} files (total: {cumulative_files_written})",
                    iteration=iteration,
                    phase_index=phase_index
                )

            # PHASE 1.4: Log code artifact if mission_id provided (only on last phase of iteration)
            if mission_id and ARTIFACTS_AVAILABLE and phase_index == len(phase_list):
                try:
                    code_summary = emp.get("summary", f"Phase {phase_index} completed - {len(written_files)} files written")
                    artifacts.log_code(
                        mission_id=mission_id,
                        role="employee",
                        code_summary=code_summary,
                        files_modified=written_files,
                    )
                except Exception as e:
                    print(f"[Mission] Warning: Failed to log code artifact: {e}")

            # refresh for next phase
            existing_files = context.site_tools.load_existing_files(out_dir)

        # Snapshot for this iteration
        snap_dir = snapshots_root / f"iteration_{iteration}"
        snap_dir.mkdir(parents=True, exist_ok=True)
        final_files = context.site_tools.load_existing_files(out_dir)
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
                analysis = context.site_tools.analyze_site(index_path)
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
            "files_summary": context.site_tools.summarize_files_for_manager(final_files),
            "tests": test_results,
            "browser_summary": browser_summary,
            "screenshot_path": screenshot_path,
            "iteration": iteration,
        }

        # STAGE 5: Use model router for manager review
        manager_review_model = _choose_model_for_agent(
            role="manager",
            task_type="review",
            iteration=iteration,
            last_status=last_status,
            last_tests=last_tests,
            config=cfg,
            run_id=core_run_id,
        )
        print(f"[ModelRouter] Manager review will use: {manager_review_model}")

        # STAGE 2.2: Log LLM call
        context.logger.log_llm_call(
            core_run_id,
            role="manager",
            model=manager_review_model,
            prompt_length=len(manager_review_sys) + len(json.dumps(mgr_payload)),
            iteration=iteration,
            phase="review"
        )

        review = context.llm.chat_json(
            "manager",
            manager_review_sys,
            json.dumps(mgr_payload, ensure_ascii=False),
            model=manager_review_model,
            task_type="review",
            interaction_index=iteration,
            run_id=core_run_id,
            config=cfg,
            max_cost_usd=max_cost_usd,
        )
        print("\n-- Manager Review --")
        print(json.dumps(review, indent=2, ensure_ascii=False))

        status = review.get("status", "needs_changes")
        feedback = review.get("feedback")

        # PHASE 1.4: Log review artifact if mission_id provided
        if mission_id and ARTIFACTS_AVAILABLE:
            try:
                review_content = json.dumps(review, indent=2, ensure_ascii=False)
                approved = (status == "approved")
                artifacts.log_review(
                    mission_id=mission_id,
                    role="manager",
                    review_content=review_content,
                    approved=approved,
                    feedback=str(feedback) if feedback else None,
                )
            except Exception as e:
                print(f"[Mission] Warning: Failed to log review artifact: {e}")

        last_status = status
        last_tests = test_results
        last_feedback = feedback

        # STAGE 3: Use InterAgentBus to send review message
        if agent_bus is not None:
            try:
                if status == "approved":
                    agent_bus.send_message(
                        from_agent="manager",
                        to_agent="supervisor",
                        message_type=inter_agent_bus.MessageType.INFO,
                        subject="Work Approved",
                        body={"status": "approved", "iteration": iteration},
                        requires_response=False
                    )
                else:
                    agent_bus.send_message(
                        from_agent="manager",
                        to_agent="employee",
                        message_type=inter_agent_bus.MessageType.TARGETED_FIX_REQUEST,
                        subject="Changes Requested",
                        body={"feedback": feedback, "iteration": iteration},
                        requires_response=True
                    )
            except Exception as e:
                print(f"[Stage3] Warning: Failed to send bus message: {e}")

        # STAGE 3: Store manager review findings in memory
        if mem_store is not None and current_stage_obj is not None:
            try:
                # Store review as a finding
                if status != "approved" and feedback:
                    # Parse feedback to extract findings
                    # feedback can be a string or a list
                    if isinstance(feedback, list):
                        for idx, item in enumerate(feedback):
                            severity = "error" if "error" in str(item).lower() or "bug" in str(item).lower() else "warning"
                            mem_store.add_finding(
                                stage_id=current_stage_obj.id,
                                severity=severity,
                                category="manager_review",
                                description=str(item),
                            )
                    elif isinstance(feedback, str) and feedback:
                        severity = "warning" if status == "needs_changes" else "info"
                        mem_store.add_finding(
                            stage_id=current_stage_obj.id,
                            severity=severity,
                            category="manager_review",
                            description=feedback,
                        )

                # Increment audit count
                audit_count = workflow_mgr.increment_audit_count(current_stage_obj.id)
                print(f"[Stage3] Audit #{audit_count} for stage: {current_stage_obj.name}")

                # Check for unresolved findings
                unresolved = mem_store.get_unresolved_findings(current_stage_obj.id)
                print(f"[Stage3] Unresolved findings: {len(unresolved)}")

                # If approved and no unresolved findings, stage can be completed
                if status == "approved" and len(unresolved) == 0:
                    print(f"[Stage3] Stage ready for completion (approved, no unresolved findings)")

            except Exception as e:
                print(f"[Stage3] Warning: Failed to store findings in memory: {e}")

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
                safety_result = context.exec_safety.run_safety_checks(str(out_dir), task)

                # Use summary_status if available, fall back to status
                iteration_safety_status = safety_result.get("summary_status") or safety_result.get("status", "failed")

                # STAGE 2.2: Log safety check
                static_issues = safety_result.get("static_issues", [])
                dep_issues = safety_result.get("dependency_issues", [])
                error_count = sum(1 for i in static_issues if i.get("severity") == "error")
                error_count += sum(1 for i in dep_issues if i.get("severity") == "error")
                warning_count = sum(1 for i in static_issues if i.get("severity") == "warning")
                warning_count += sum(1 for i in dep_issues if i.get("severity") == "warning")

                context.logger.log_safety_check(
                    core_run_id,
                    status=iteration_safety_status,
                    error_count=error_count,
                    warning_count=warning_count,
                    iteration=iteration
                )

                # Process safety results
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

        # STAGE 4: Merge manager diff summary (after successful iteration)
        if status == "approved" or (status != "needs_changes" and iteration_safety_status != "failed"):
            try:
                # STAGE 4.3: Summarize diffs for all repos
                from repo_router import get_all_repo_paths

                repo_paths = get_all_repo_paths(cfg)
                if not repo_paths:
                    repo_paths = [out_dir]  # Fallback to default

                for repo_path in repo_paths:
                    # Summarize git diff with LLM
                    # STAGE 5.2: Pass cost cap to merge_manager
                    diff_summary = context.merge_manager.summarize_diff_with_llm(
                        run_id=core_run_id,
                        repo_path=repo_path,
                        context={
                            "iteration": iteration,
                            "status": status,
                            "safety_status": iteration_safety_status,
                            "repo_path": str(repo_path),
                        },
                        max_cost_usd=max_cost_usd,
                    )
                    if diff_summary.get("summary") != "No changes detected":
                        print(f"\n[MergeManager] Diff summary for {repo_path.name}: {diff_summary.get('summary', 'N/A')}")
                        if diff_summary.get("risks"):
                            print(f"[MergeManager] Risks identified: {', '.join(diff_summary['risks'])}")
            except Exception as e:
                print(f"[MergeManager] Failed to summarize diff: {e}")

        # Git commit
        if git_ready:
            commit_message = (
                f"3loop iteration {iteration}: "
                f"status={status}, all_passed={test_results.get('all_passed')}"
            )
            # PHASE 1.4: Pass secret scanning configuration
            commit_success = context.git_utils.commit_all(out_dir, commit_message, git_secret_scanning_enabled)
            if not commit_success:
                print(f"[Git] Warning: Commit failed for iteration {iteration}")

        # PHASE 1.6: Removed run_logger.log_iteration_legacy() - now using core_logging only
        # Already using: context.logger.log_iteration_begin() (line ~1042)
        # Already using: context.logger.log_iteration_end() (line ~1537)
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

            context.run_logger.log_iteration(
                run_summary,
                index=iteration,
                role="manager",  # Last role in iteration is manager review
                status=iter_status,
                notes="; ".join(notes_parts),
                safety_status=iteration_safety_status,
            )

        # STAGE 2.2: Log iteration end
        context.logger.log_iteration_end(
            core_run_id,
            iteration,  # iteration number (int)
            "completed",  # status
            stage_id=stage_id,
            stage_name=stage_name,
            iterations=audit_cycle,
            audit_count=audit_cycle,
            duration_seconds=0  # TODO: Track actual duration
        )

        # PHASE 1.4: Log iteration end artifact
        if mission_id and ARTIFACTS_AVAILABLE:
            try:
                approved = (status == "approved")
                artifacts.log_iteration_end(
                    mission_id=mission_id,
                    iteration_num=iteration,
                    approved=approved,
                    feedback=str(feedback) if feedback else None,
                )
            except Exception as e:
                print(f"[Mission] Warning: Failed to log iteration end: {e}")

        # ─────────────────────────────────────────────────────────────
        # STAGE 3: Cost Control Enforcement
        # ─────────────────────────────────────────────────────────────
        total_cost = context.cost_tracker.get_total_cost_usd()
        print(f"\n[Cost] After iteration {iteration}: ~${total_cost:.4f} USD")

        # STAGE 5.2: Log cost checkpoint after each iteration
        context.logger.log_cost_checkpoint(
            core_run_id,
            checkpoint=f"iteration_{iteration}",
            total_cost_usd=total_cost,
            max_cost_usd=max_cost_usd,
            cost_summary=context.cost_tracker.get_summary(),
            iteration=iteration,
            status=status,
        )

        # PHASE 1.4: Log cost checkpoint artifact
        if mission_id and ARTIFACTS_AVAILABLE:
            try:
                artifacts.log_cost_summary(
                    mission_id=mission_id,
                    checkpoint=f"iteration_{iteration}",
                    cost_summary=context.cost_tracker.get_summary(),
                )
            except Exception as e:
                print(f"[Mission] Warning: Failed to log cost checkpoint: {e}")

        # Show warning once when crossing cost_warning_usd
        if cost_warning_usd and total_cost > cost_warning_usd and not cost_warning_shown:
            print(f"\n⚠️  [Cost] Warning threshold exceeded: ${total_cost:.4f} > ${cost_warning_usd:.4f}")
            cost_warning_shown = True

        if max_cost_usd and total_cost > max_cost_usd:
            print(f"\n[Cost] ❌ Max cost cap exceeded: ${total_cost:.4f} > ${max_cost_usd:.4f}")
            print("[Cost] Aborting run.")
            break

        if status == "approved":
            print("\n[Manager] Approved – stopping iterations.")

            # STAGE 3: Complete the current stage when approved
            if workflow_mgr is not None and current_stage_obj is not None:
                try:
                    workflow_mgr.complete_stage(current_stage_obj.id)
                    print(f"[Stage3] ✓ Completed stage: {current_stage_obj.name}")

                    # Move to next stage if available
                    next_stage = workflow_mgr.get_next_pending_stage()
                    if next_stage:
                        current_stage_obj = workflow_mgr.start_stage(next_stage.id)
                        print(f"[Stage3] → Started next stage: {current_stage_obj.name}")

                        # Initialize memory for new stage
                        if mem_store is not None:
                            mem_store.get_or_create_memory(
                                stage_id=current_stage_obj.id,
                                stage_name=current_stage_obj.name
                            )

                        # Continue iterations for next stage (don't break)
                        continue
                    else:
                        print("[Stage3] ✓ All stages completed!")

                except Exception as e:
                    print(f"[Stage3] Warning: Failed to complete/advance stage: {e}")

            break

        # If not approved, continue to next iteration (needs_changes)
        print(f"\n[Iteration] Status: {status} - continuing to next iteration...")

    final_cost_summary = context.cost_tracker.get_summary()

    print("\n====== DONE (3-loop) ======")
    print(f"Final status: {final_status}")
    print("\n[Cost] Final summary:")
    print(json.dumps(final_cost_summary, indent=2, ensure_ascii=False))

    # Persist cost summary
    agent_dir = Path(__file__).resolve().parent
    cost_log_dir = agent_dir / "cost_logs"
    cost_log_dir.mkdir(parents=True, exist_ok=True)
    cost_log_file = cost_log_dir / f"{cfg['project_subdir']}.jsonl"

    context.cost_tracker.append_history(
        log_file=cost_log_file,
        project_name=cfg["project_subdir"],
        task=task,
        status=final_status,
        extra={"max_rounds": max_rounds, "mode": "3loop"},
    )

    # STAGE 5.2: Final cost checkpoint
    final_total_cost = context.cost_tracker.get_total_cost_usd()
    context.logger.log_cost_checkpoint(
        core_run_id,
        checkpoint="final",
        total_cost_usd=final_total_cost,
        max_cost_usd=max_cost_usd,
        cost_summary=final_cost_summary,
        final_status=final_status,
    )

    # PHASE 1.6: Removed run_logger.finish_run_legacy() - now using core_logging only
    # Already using: context.logger.log_final_status() (line ~1761)
    # context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)

    # STAGE 4.2: Semantic git commit (if enabled and not already committed by individual iterations)
    auto_git_commit = cfg.get("auto_git_commit", False)
    if auto_git_commit and git_ready:
        try:
            print("\n[SemanticCommit] Generating semantic commit messages for all repos...")

            # STAGE 4.3: Get all repos to commit
            from repo_router import get_all_repo_paths

            repo_paths = get_all_repo_paths(cfg)
            if not repo_paths:
                repo_paths = [out_dir]  # Fallback to default

            auto_commit_repos = cfg.get("auto_git_commit_repos", ["default"])

            for repo_path in repo_paths:
                # Check if this repo should be auto-committed
                repo_name = repo_path.name
                if "default" not in auto_commit_repos and repo_name not in auto_commit_repos:
                    print(f"[SemanticCommit] Skipping {repo_name} (not in auto_git_commit_repos)")
                    continue

                print(f"\n[SemanticCommit] Processing {repo_name}...")

                context.logger.log_event(core_run_id, "git_commit_attempt", {
                    "mode": "semantic",
                    "final_status": final_status,
                    "repo_path": str(repo_path),
                })

                # STAGE 5.2: Pass cost cap to merge_manager
                commit_info = context.merge_manager.summarize_session(
                    run_id=core_run_id,
                    repo_path=repo_path,
                    task=task,
                    max_cost_usd=max_cost_usd,
                )

                title = commit_info.get("title", f"Auto-commit: {core_run_id[:8]}")
                body = commit_info.get("body", "Changes made during orchestrator run.")

                print(f"[SemanticCommit] {repo_name} - Title: {title}")
                print(f"[SemanticCommit] {repo_name} - Body preview: {body[:100]}...")

                # Create commit
                commit_success = context.merge_manager.make_commit(
                    repo_path=repo_path,
                    title=title,
                    body=body,
                )

                if commit_success:
                    context.logger.log_event(core_run_id, "git_commit_success", {
                        "title": title,
                        "mode": "semantic",
                        "repo_path": str(repo_path),
                    })
                    print(f"[SemanticCommit] ✅ {repo_name} - Commit created successfully")
                else:
                    context.logger.log_event(core_run_id, "git_commit_skipped", {
                        "reason": "No changes or commit failed",
                        "repo_path": str(repo_path),
                    })
                    print(f"[SemanticCommit] ⚠️  {repo_name} - No commit created (no changes or failed)")

        except Exception as e:
            context.logger.log_event(core_run_id, "git_commit_failed", {
                "error": str(e),
            })
            print(f"[SemanticCommit] ❌ Failed to create semantic commit: {e}")
    elif auto_git_commit and not git_ready:
        context.logger.log_event(core_run_id, "git_commit_skipped", {
            "reason": "Git not initialized",
        })
        print("[SemanticCommit] Skipped - git not initialized")

    # STAGE 2.2: Log final status
    context.logger.log_final_status(
        core_run_id,
        status=final_status,
        reason="All stages completed" if all_completed else "Partial completion",
        iterations=stages_processed
    )

    # PHASE 1.4: Log final result artifact if mission_id provided
    if mission_id and ARTIFACTS_AVAILABLE:
        try:
            artifacts.log_final_result(
                mission_id=mission_id,
                status="success" if final_status == "approved" else "failed",
                summary=f"Run completed with status: {final_status}",
                total_iterations=max_rounds,
                total_cost_usd=final_cost_summary.get("total_usd", 0.0),
            )

            # Generate HTML report
            report_path = artifacts.generate_report(mission_id)
            print(f"\n[Mission] Artifact report generated: {report_path}")
        except Exception as e:
            print(f"[Mission] Warning: Failed to generate artifact report: {e}")

    # PHASE 4: Record specialist performance
    if SPECIALISTS_AVAILABLE and specialist_info and use_specialist:
        try:
            # Calculate actual mission duration (estimate for now)
            actual_duration = 300.0  # 5 minutes default

            # Record mission result in specialist market
            market = specialist_market.SpecialistMarket()
            market.record_mission_result(
                specialist_type=specialist_info["type"],
                success=(final_status == "approved"),
                cost_usd=final_cost_summary.get("total_usd", 0.0),
                duration_seconds=actual_duration
            )

            print(f"\n[Specialist] Performance recorded for {specialist_info['type']}")
        except Exception as e:
            print(f"[Specialist] Warning: Failed to record specialist performance: {e}")

    # PHASE 5: Overseer post-mission analysis
    if OVERSEER_AVAILABLE:
        try:
            overseer_instance = overseer.Overseer()

            # Analyze mission outcome
            mission_data = {
                "status": "completed" if final_status == "approved" else "failed",
                "cost_usd": final_cost_summary.get("total_usd", 0.0),
                "iterations": max_rounds,
                "max_iterations": max_rounds,
                "budget_usd": max_cost_usd if max_cost_usd > 0 else None,
            }

            intervention = overseer_instance.analyze_mission_progress(mission_data)

            if intervention.should_intervene:
                print(f"\n[Overseer] Post-Mission Analysis:")
                print(f"[Overseer] {intervention.recommendation}")

            # Generate improvement suggestions
            if OVERSEER_AVAILABLE:
                refiner = self_refinement.SelfRefiner()
                improvements = refiner.suggest_improvements()

                if improvements and len(improvements) > 0:
                    print(f"\n[Refinement] Suggested Improvements:")
                    for imp in improvements[:3]:  # Show top 3
                        print(f"[Refinement]   [{imp.priority.upper()}] {imp.area.value}: {imp.suggestion}")

        except Exception as e:
            print(f"[Overseer] Warning: Failed to perform post-mission analysis: {e}")

    # PHASE 1.5: Return result dict for programmatic access
    return {
        "status": "success" if final_status == "approved" else "failed",
        "final_status": final_status,
        "rounds_completed": max_rounds,
        "cost_summary": final_cost_summary,
        "core_run_id": core_run_id,
        "output_dir": str(out_dir),
        "files_modified": list(all_files_modified),  # PHASE 2.1a: Return modified files for knowledge graph
    }


def run(
    config: Dict[str, Any],
    mission_id: Optional[str] = None,
    context: Optional[OrchestratorContext] = None,
) -> Dict[str, Any]:
    """
    PHASE 1.5: Public entry point for running orchestrator with mission support and DI.

    This function provides a clean API for running the orchestrator programmatically,
    with optional mission artifact logging and dependency injection.

    Args:
        config: Configuration dictionary (same structure as project_config.json)
        mission_id: Optional mission ID for artifact logging
        context: Optional OrchestratorContext for dependency injection (for testing)

    Returns:
        Dict with run results (status, rounds_completed, cost_summary, etc.)

    Example:
        >>> from agent import orchestrator
        >>> config = {
        ...     "task": "Build a landing page",
        ...     "project_subdir": "my_project",
        ...     "max_rounds": 2,
        ...     "max_cost_usd": 1.0,
        ... }
        >>> result = orchestrator.run(config, mission_id="my_mission")
        >>> print(result["status"])  # "success" or "failed"
    """
    return main(
        run_summary=None,
        mission_id=mission_id,
        cfg_override=config,
        context=context,
    )


if __name__ == "__main__":
    main()
