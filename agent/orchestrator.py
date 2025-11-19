# orchestrator.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# PHASE 1.5: Import dependency injection context
from orchestrator_context import OrchestratorContext

# STAGE 2.2: Import core logging for main run events
import core_logging
import cost_tracker

# PHASE 1.3: Import prompt security for injection defense
import prompt_security

# PHASE 1.4: Import artifacts for mission logging
try:
    import artifacts
    ARTIFACTS_AVAILABLE = True
except ImportError:
    ARTIFACTS_AVAILABLE = False

# PHASE 0.3: Import new config and paths modules
try:
    import config as config_module
    import paths as paths_module
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# PHASE 1.1: Import domain router for domain-aware prompting
try:
    import domain_router
    DOMAIN_ROUTER_AVAILABLE = True
except ImportError:
    DOMAIN_ROUTER_AVAILABLE = False

# PHASE 2.2: Import project_stats for risk analysis
try:
    import project_stats
    PROJECT_STATS_AVAILABLE = True
except ImportError:
    PROJECT_STATS_AVAILABLE = False

# PHASE 4: Import specialist system for expert agent routing
try:
    import specialists
    import specialist_market
    import company_ops
    SPECIALISTS_AVAILABLE = True
except ImportError:
    SPECIALISTS_AVAILABLE = False

# PHASE 5: Import overseer system for meta-orchestration
try:
    import overseer
    import self_refinement
    import feedback_analyzer
    OVERSEER_AVAILABLE = True
except ImportError:
    OVERSEER_AVAILABLE = False

# STAGE 3: Import dynamic workflow and memory systems
try:
    import workflow_manager
    import memory_store
    import inter_agent_bus
    STAGE3_AVAILABLE = True
except ImportError:
    STAGE3_AVAILABLE = False
    print("[Stage3] Warning: Stage 3 modules not available - using fixed iteration flow")

# STAGE 4: Import merge manager and multi-repo routing
import merge_manager
from exec_safety import run_safety_checks

# STAGE 2.1: Import tool registry for metadata
from exec_tools import get_tool_metadata
from git_utils import commit_all, ensure_repo
from llm import chat_json

# STAGE 5: Import model router
from model_router import estimate_complexity, is_stage_important
from prompts import load_prompts
from repo_router import resolve_repo_path

# STAGE 2: Import new run logging API
# NOTE: We maintain TWO parallel logging systems:
# 1. Legacy logging (run_logger.py) - writes to agent/run_logs/<project>_<mode>.jsonl
#    - Used for backward compatibility with existing tooling
#    - Appends high-level run summaries
# 2. Core logging (core_logging.py) - writes to agent/run_logs_main/<run_id>.jsonl
#    - New structured event logging system (STAGE 2)
#    - Provides granular event tracking (LLM calls, file writes, etc.)
#
# DEPRECATION PLAN: The legacy logging API should eventually be phased out in favor
# of core_logging once all consumers are migrated. For now, both are maintained to
# avoid breaking existing scripts/dashboards that depend on the legacy format.
from run_logger import RunSummary
from run_logger import (
    finish_run_legacy as finish_run,
)
from run_logger import log_iteration as log_iteration_new
from run_logger import (
    log_iteration_legacy as log_iteration_dict,
)
from run_logger import (
    start_run_legacy as start_run,
)
from site_tools import (
    analyze_site,
    load_existing_files,
    summarize_files_for_manager,
)


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


def main(
    run_summary: Optional[RunSummary] = None,
    mission_id: Optional[str] = None,
    cfg_override: Optional[Dict[str, Any]] = None,
    context: Optional[OrchestratorContext] = None,
) -> Dict[str, Any]:
    """
    Main 3-loop orchestrator function.

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
    use_visual_review: bool = bool(cfg.get("use_visual_review", False))
    prompts_file: str = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd: float = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd: float = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode: str = cfg.get("interactive_cost_mode", "off")
    use_git: bool = bool(cfg.get("use_git", False))

    # PHASE 1.4: Git secret scanning configuration
    git_secret_scanning_enabled: bool = bool(cfg.get("git_secret_scanning_enabled", True))

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
    print(f"git_secret_scanning_enabled: {git_secret_scanning_enabled}")
    print(f"run_safety_before_final: {run_safety_before_final}")
    print(f"allow_extra_iteration_on_failure: {allow_extra_iteration_on_failure}")

    # snapshots
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
    run_record = context.run_logger.start_run(cfg, mode, out_dir)

    # STAGE 2.2: Log run start
    context.logger.log_start(
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
            index=0,  # Planning phase (pre-iteration)
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
        print("[Cost] Max cost exceeded during planning. Aborting run.")
        final_status = "aborted_cost_cap_planning"
        final_cost_summary = context.cost_tracker.get_summary()
        context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)
        return

    # 2) Supervisor phasing
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
        context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)
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

    # STAGE 5.2: Track cumulative file count for complexity estimation
    cumulative_files_written = 0

    # PHASE 2.1a: Track all unique files modified across iterations for knowledge graph
    all_files_modified = set()  # Track unique file paths

    # STAGE 3: Track current stage for workflow integration
    current_stage_idx = 0  # Index into phase_list
    current_stage_obj = None  # Current Stage object from workflow_mgr

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
            mode=mode,
            max_rounds=max_rounds
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
            context.logger.log_llm_call(
                core_run_id,
                role="employee",
                model=employee_model,
                prompt_length=len(employee_sys_phase) + len(json.dumps(phase_payload)),
                iteration=iteration,
                phase_index=phase_index,
                phase_name=phase.get('name', 'Unnamed phase')
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

            files_dict = emp.get("files", {})
            if not isinstance(files_dict, dict):
                raise RuntimeError(
                    f"Employee response 'files' must be an object/dict, got {type(files_dict)}"
                )

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

            # STAGE 2.2: Log file writes
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

        # RUN LOG: record this iteration (legacy dict-based)
        context.run_logger.log_iteration_legacy(
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
            iteration=iteration,
            status=status,
            tests_all_passed=test_results.get("all_passed", False),
            safety_status=iteration_safety_status
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

    # RUN LOG: finalize
    context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)

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
        reason=f"Run completed with status: {final_status}",
        iterations=max_rounds,
        total_cost_usd=final_cost_summary.get("total_usd", 0.0)
    )

    print(f"\n[CoreLog] Main run logs written to: run_logs_main/{core_run_id}.jsonl")

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
