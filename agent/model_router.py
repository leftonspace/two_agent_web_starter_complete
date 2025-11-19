# model_router.py
"""
STAGE 5.1: Central Model Router & Cost Intelligence

This module provides intelligent model selection based on:
- Task type (planning, code, docs, analysis)
- Complexity (low, high)
- Role (manager, employee, supervisor, etc.)
- Interaction index (iteration number)
- Importance flags

KEY CONSTRAINT:
GPT-5 is ONLY allowed on 2nd or 3rd interactions AND only when:
- Complexity is "high" OR
- is_very_important is True

First interactions ALWAYS use cheaper models (gpt-5-mini or gpt-5-nano).
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ══════════════════════════════════════════════════════════════════════
# Model Routing Rules
# ══════════════════════════════════════════════════════════════════════

# Task type -> Complexity -> Model mapping
# This is the base routing table before applying GPT-5 constraints
ROUTING_RULES: Dict[str, Dict[str, str]] = {
    # Planning (Manager, Supervisor)
    "planning": {
        "low": "gpt-5-mini-2025-08-07",
        "high": "gpt-5-2025-08-07",  # Subject to interaction index constraint
    },
    # Code generation/editing (Employee)
    "code": {
        "low": "gpt-5-mini-2025-08-07",
        "high": "gpt-5-2025-08-07",  # Subject to interaction index constraint
    },
    # Documentation, commit messages, summaries
    "docs": {
        "low": "gpt-5-mini-2025-08-07",
        "high": "gpt-5-mini-2025-08-07",  # Docs rarely need GPT-5
    },
    # Analysis (QA, diff summaries, etc.)
    "analysis": {
        "low": "gpt-5-nano",
        "high": "gpt-5-mini-2025-08-07",
    },
    # Supervisor reviews
    "review": {
        "low": "gpt-5-nano",
        "high": "gpt-5-mini-2025-08-07",
    },
}

# Fallback model if task type is unknown
DEFAULT_MODEL = "gpt-5-mini-2025-08-07"

# GPT-5 constraint: Only allowed on these interaction indices
GPT5_ALLOWED_INTERACTIONS = [2, 3]


def choose_model(
    task_type: str,
    complexity: str = "low",
    role: str = "unknown",
    interaction_index: int = 1,
    is_very_important: bool = False,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Choose the appropriate model based on task characteristics.

    Args:
        task_type: Type of task ("planning", "code", "docs", "analysis", "review")
        complexity: Task complexity ("low" or "high")
        role: Agent role (for logging/debugging)
        interaction_index: Current interaction/iteration number (1-indexed)
        is_very_important: Flag indicating critical task (overrides complexity)
        config: Optional project config for very_important_stages lookup

    Returns:
        Model identifier string (e.g., "gpt-5-2025-08-07")

    GPT-5 Constraint Rules:
    1. GPT-5 is ONLY allowed on interaction indices 2 or 3
    2. Even on those interactions, GPT-5 is only used if:
       - complexity == "high" OR is_very_important == True
    3. First iteration (index=1) ALWAYS uses cheaper model
    4. Iterations beyond 3 fall back to cheaper models
    """
    # Normalize inputs
    task_type = task_type.lower().strip()
    complexity = complexity.lower().strip()

    # Get base model from routing rules
    task_rules = ROUTING_RULES.get(task_type, {"low": DEFAULT_MODEL, "high": DEFAULT_MODEL})

    # Determine effective complexity
    effective_complexity = "high" if (complexity == "high" or is_very_important) else "low"

    # Get candidate model
    candidate_model = task_rules.get(effective_complexity, DEFAULT_MODEL)

    # Apply GPT-5 constraint
    # If the candidate model is GPT-5, check if we're allowed to use it
    if "gpt-5-2025-08-07" in candidate_model:
        # Check interaction index constraint
        if interaction_index not in GPT5_ALLOWED_INTERACTIONS:
            # Not allowed - downgrade to gpt-5-mini
            print(
                f"[ModelRouter] GPT-5 requested but interaction_index={interaction_index} "
                f"(allowed: {GPT5_ALLOWED_INTERACTIONS}). Downgrading to gpt-5-mini."
            )
            candidate_model = "gpt-5-mini-2025-08-07"
        elif effective_complexity == "low" and not is_very_important:
            # Allowed interaction but not important enough
            print(
                f"[ModelRouter] GPT-5 requested but complexity=low and not important. "
                f"Downgrading to gpt-5-mini."
            )
            candidate_model = "gpt-5-mini-2025-08-07"

    # Log routing decision
    print(
        f"[ModelRouter] role={role}, task={task_type}, complexity={effective_complexity}, "
        f"iteration={interaction_index}, important={is_very_important} -> {candidate_model}"
    )

    return candidate_model


def estimate_complexity(
    stage: Optional[Dict[str, Any]] = None,
    previous_failures: int = 0,
    files_count: int = 0,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Estimate task complexity based on heuristics.

    Args:
        stage: Optional stage dict with metadata
        previous_failures: Number of previous iteration failures
        files_count: Number of files being touched
        config: Optional project config

    Returns:
        "low" or "high"

    Heuristics:
    - High if: previous failures > 1
    - High if: stage name/description contains keywords (refactor, architecture, migration)
    - High if: files_count > 5
    - High if: stage is marked as very_important in config
    - Otherwise: low
    """
    # Check previous failures
    if previous_failures > 1:
        return "high"

    # Check files count
    if files_count > 5:
        return "high"

    # Check stage metadata
    if stage:
        stage_name = stage.get("name", "").lower()
        stage_desc = stage.get("description", "").lower()

        # High-complexity keywords
        high_keywords = [
            "refactor",
            "architecture",
            "migration",
            "redesign",
            "overhaul",
            "rewrite",
            "complex",
            "critical",
        ]

        search_text = f"{stage_name} {stage_desc}"
        if any(keyword in search_text for keyword in high_keywords):
            return "high"

        # Check if stage is marked as very important in config
        if config:
            very_important_stages = config.get("llm_very_important_stages", [])
            stage_id = stage.get("id", "")
            if stage_id in very_important_stages or stage_name in very_important_stages:
                return "high"

    return "low"


def is_stage_important(
    stage: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Check if a stage is marked as very important.

    Args:
        stage: Stage dict
        config: Project config

    Returns:
        True if stage is important, False otherwise
    """
    if not stage or not config:
        return False

    very_important_stages = config.get("llm_very_important_stages", [])

    stage_id = stage.get("id", "")
    stage_name = stage.get("name", "")

    return stage_id in very_important_stages or stage_name in very_important_stages
