"""
Programmatic API for running the orchestrator.

Provides a clean Python interface for running projects without CLI.
Used by the web dashboard and can be used by other automation tools.

STAGE 7: Created for web dashboard integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

# STAGE 12: Import brain module
import brain
import cost_tracker

# STAGE 10: Import QA module
import qa
from cost_estimator import estimate_run_cost
from run_logger import RunSummary, finalize_run, log_iteration, save_run_summary, start_run
from status_codes import (
    COMPLETED,
    EXCEPTION,
    ITER_EXCEPTION,
    ITER_INTERRUPTED,
    UNKNOWN,
    USER_ABORT,
)


def run_project(config: Dict[str, Any]) -> RunSummary:
    """
    Run the orchestrator with the given configuration.

    This is the main programmatic API for running projects. It:
    - Validates the configuration
    - Initializes run logging
    - Executes the appropriate orchestrator (2loop or 3loop)
    - Returns a complete RunSummary with results

    The CLI behavior remains intact - this function is an alternative
    entry point for programmatic/web-based execution.

    Args:
        config: Project configuration dict with keys:
            - mode: "2loop" or "3loop"
            - project_subdir: Folder name under sites/
            - task: Task description
            - max_rounds: Maximum iterations
            - use_visual_review: bool
            - use_git: bool
            - max_cost_usd: float
            - cost_warning_usd: float
            - interactive_cost_mode: "off", "once", or "always"
            - prompts_file: Prompts JSON file name

    Returns:
        RunSummary with complete run results including:
        - run_id: Unique identifier
        - final_status: Status code from status_codes
        - iterations: List of iteration logs
        - cost_summary: Token usage and costs
        - All metadata about the run

    Raises:
        FileNotFoundError: If project directory doesn't exist
        ValueError: If configuration is invalid
        Exception: If orchestrator encounters an error
    """
    # Validate required fields
    required_fields = ["mode", "project_subdir", "task"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")

    # STAGE 12: Apply auto-tuning if enabled
    original_config = config.copy()
    project_subdir = config.get("project_subdir")

    try:
        tuning_config = brain.load_tuning_config()
        if tuning_config.enabled and not config.get("_skip_auto_tune", False):
            # Build project profile
            profile = brain.build_project_profile(project_subdir)

            # Generate recommendations
            recommendations = brain.generate_recommendations(profile, config)

            # Apply recommendations if sufficient data
            if recommendations:
                config = brain.apply_auto_tune(config, recommendations, tuning_config)
                print(f"[BRAIN] Auto-tune applied {len(recommendations)} recommendations")
                for rec in recommendations:
                    print(f"  - {rec.category}: {rec.current_value} → {rec.recommended_value}")
    except Exception as e:
        # Auto-tune failures should not block runs
        print(f"[BRAIN] Auto-tune failed (continuing with original config): {e}")
        config = original_config

    # Extract configuration
    mode = config.get("mode", "3loop").lower().strip()
    task = config.get("task", "")
    max_rounds = int(config.get("max_rounds", 1))

    # Validate mode
    if mode not in ("2loop", "3loop"):
        raise ValueError(f"Invalid mode: {mode}. Must be '2loop' or '3loop'")

    # Determine project directory
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    project_dir = project_root / "sites" / project_subdir

    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Model configuration (use defaults from llm.py)
    try:
        from llm import (
            DEFAULT_EMPLOYEE_MODEL,
            DEFAULT_MANAGER_MODEL,
            DEFAULT_SUPERVISOR_MODEL,
        )
    except ImportError:
        DEFAULT_MANAGER_MODEL = "gpt-5-mini"
        DEFAULT_SUPERVISOR_MODEL = "gpt-5-nano"
        DEFAULT_EMPLOYEE_MODEL = "gpt-5"

    models_used = {
        "manager": DEFAULT_MANAGER_MODEL,
        "supervisor": DEFAULT_SUPERVISOR_MODEL,
        "employee": DEFAULT_EMPLOYEE_MODEL,
    }

    # Create RunSummary
    run_config = {
        "use_visual_review": config.get("use_visual_review", False),
        "use_git": config.get("use_git", False),
        "max_cost_usd": config.get("max_cost_usd", 0.0),
        "cost_warning_usd": config.get("cost_warning_usd", 0.0),
        "interactive_cost_mode": config.get("interactive_cost_mode", "off"),
        "prompts_file": config.get("prompts_file", "prompts_default.json"),
    }

    # STAGE 12: Add prompt strategy and auto-tune metadata
    prompt_strategy = config.get("prompts", {}).get("default_strategy", "baseline")
    run_config["prompt_strategy"] = prompt_strategy
    run_config["auto_tuned"] = config.get("_auto_tuned", False)
    if config.get("_tuned_fields"):
        run_config["tuned_fields"] = config.get("_tuned_fields")

    run_summary = start_run(
        mode=mode,
        project_dir=str(project_dir),
        task=task,
        max_rounds=max_rounds,
        models_used=models_used,
        config=run_config,
    )

    # Compute cost estimate
    cost_estimate = estimate_run_cost(
        mode=mode,
        max_rounds=max_rounds,
        models_used=models_used,
    )
    run_summary.estimated_cost_usd = cost_estimate["estimated_total_usd"]

    # Reset cost tracking
    cost_tracker.reset()

    # Run orchestrator
    final_status = UNKNOWN
    safety_status = None

    try:
        if mode == "2loop":
            from orchestrator_2loop import main as main_2loop

            # 2loop doesn't support run_summary yet, so we run it standalone
            # We'll need to temporarily write config to project_config.json
            _run_with_temp_config(config, main_2loop)
            final_status = COMPLETED

        else:
            # 3-loop supports run_summary
            from orchestrator import main as main_3loop

            # Temporarily write config to project_config.json
            _run_with_temp_config(config, lambda: main_3loop(run_summary=run_summary))
            final_status = COMPLETED

    except KeyboardInterrupt:
        final_status = USER_ABORT
        log_iteration(
            run_summary,
            index=run_summary.rounds_completed + 1,
            role="system",
            status=ITER_INTERRUPTED,
            notes="Run interrupted by user (Ctrl+C)",
        )

    except Exception as e:
        final_status = EXCEPTION
        log_iteration(
            run_summary,
            index=run_summary.rounds_completed + 1,
            role="system",
            status=ITER_EXCEPTION,
            notes=f"Exception: {type(e).__name__}: {str(e)}",
        )
        # Don't re-raise - return the summary with error status

    finally:
        # Finalize and save
        cost_summary = cost_tracker.get_summary()
        run_summary = finalize_run(
            run_summary,
            final_status=final_status,
            safety_status=safety_status,
            cost_summary=cost_summary,
        )

        # STAGE 10: Run QA checks if enabled and run completed successfully
        qa_config_dict = config.get("qa", {})
        if qa_config_dict.get("enabled", False) and final_status == COMPLETED:
            try:
                qa_report = run_qa_only(project_dir, qa_config_dict)
                run_summary.qa_status = qa_report.status
                run_summary.qa_summary = qa_report.summary
                run_summary.qa_report = qa_report.to_dict()
            except Exception as e:
                # Don't fail the run if QA fails
                run_summary.qa_status = "error"
                run_summary.qa_summary = f"QA execution failed: {str(e)}"
                run_summary.qa_report = None

        save_run_summary(run_summary)

    return run_summary


def _run_with_temp_config(config: Dict[str, Any], run_func: callable) -> None:
    """
    Temporarily write config to project_config.json and run the function.

    The orchestrators currently read from project_config.json, so we need
    to temporarily write the config there. This preserves backward compatibility
    while allowing programmatic execution.

    Args:
        config: Configuration dict
        run_func: Function to call (orchestrator main)
    """
    agent_dir = Path(__file__).resolve().parent
    config_path = agent_dir / "project_config.json"

    # Backup original config
    original_config = None
    if config_path.exists():
        original_config = config_path.read_text(encoding="utf-8")

    try:
        # Write temporary config
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

        # Run orchestrator
        run_func()

    finally:
        # Restore original config
        if original_config is not None:
            config_path.write_text(original_config, encoding="utf-8")


def list_projects() -> list[Dict[str, Any]]:
    """
    List all available projects in the sites/ directory.

    Returns:
        List of dicts with keys:
        - name: Project folder name
        - path: Full path to project directory
        - exists: True if directory exists
        - file_count: Number of files in the directory (0 if empty/new)
    """
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    sites_dir = project_root / "sites"

    if not sites_dir.exists():
        return []

    projects = []
    for item in sorted(sites_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            # Skip fixtures (generated test content)
            if item.name == "fixtures":
                continue

            file_count = sum(1 for _ in item.rglob("*") if _.is_file())
            projects.append({
                "name": item.name,
                "path": str(item),
                "exists": True,
                "file_count": file_count,
            })

    return projects


def list_run_history(limit: int = 50) -> list[Dict[str, Any]]:
    """
    List recent runs from the run_logs/ directory.

    Args:
        limit: Maximum number of runs to return (default 50)

    Returns:
        List of run summary dicts, sorted by start time (newest first).
        Each dict contains the full RunSummary data plus run_id for linking.
    """
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    run_logs_dir = project_root / "run_logs"

    if not run_logs_dir.exists():
        return []

    runs = []

    # Iterate through run directories
    for run_dir in run_logs_dir.iterdir():
        if not run_dir.is_dir():
            continue

        summary_file = run_dir / "run_summary.json"
        if not summary_file.exists():
            continue

        try:
            with summary_file.open("r", encoding="utf-8") as f:
                run_data = json.load(f)
                runs.append(run_data)
        except Exception:
            # Skip invalid/corrupted run logs
            continue

    # Sort by started_at (newest first)
    runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)

    return runs[:limit]


def get_run_details(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific run.

    Args:
        run_id: Run identifier

    Returns:
        Run summary dict, or None if run not found
    """
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent
    run_logs_dir = project_root / "run_logs"
    run_dir = run_logs_dir / run_id
    summary_file = run_dir / "run_summary.json"

    if not summary_file.exists():
        return None

    try:
        with summary_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def run_qa_only(project_path: Path, qa_config_dict: Optional[Dict[str, Any]] = None) -> qa.QAReport:
    """
    Run QA checks on an existing project without re-running the orchestrator.

    This allows on-demand quality checking of any project in the sites/ directory.

    Args:
        project_path: Path to the project directory
        qa_config_dict: Optional QA configuration dict. If None, uses defaults from project_config.json

    Returns:
        QAReport with quality check results

    Raises:
        FileNotFoundError: If project directory doesn't exist
        Exception: If QA execution fails
    """
    if not project_path.exists() or not project_path.is_dir():
        raise FileNotFoundError(f"Project directory not found: {project_path}")

    # Load QA config
    if qa_config_dict is None:
        # Try to load from project_config.json
        agent_dir = Path(__file__).resolve().parent
        config_file = agent_dir / "project_config.json"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                full_config = json.load(f)
                qa_config_dict = full_config.get("qa", {})
        else:
            qa_config_dict = {}

    # Create QA config object
    qa_config = qa.QAConfig.from_dict(qa_config_dict)

    # Run QA checks
    qa_report = qa.run_qa_for_project(project_path, qa_config)

    return qa_report
