# model_router.py
"""
STAGE 5.1: Central Model Router & Cost Intelligence

This module provides intelligent model selection based on:
- Task type (planning, code, docs, analysis)
- Complexity (low, high)
- Role (manager, employee, supervisor, etc.)
- Interaction index (iteration number)
- Importance flags

PHASE 3.2: Extended to support multiple providers (OpenAI, Anthropic, Local)
with ModelConfig dataclass for flexible routing.

PHASE 1.7: Integrated with ModelRegistry for externalized model configuration.
Model names now resolved from agent/models.json instead of hard-coded.

KEY CONSTRAINT:
High-end models (gpt-5, etc.) are ONLY allowed on 2nd or 3rd interactions AND only when:
- Complexity is "high" OR
- is_very_important is True

First interactions ALWAYS use cheaper models (gpt-5-mini or similar).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Union

# PHASE 1.7: Import model registry for externalized configuration
from model_registry import get_registry, ModelInfo


# ══════════════════════════════════════════════════════════════════════
# PHASE 3.2: Provider and Model Configuration
# ══════════════════════════════════════════════════════════════════════


class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """
    Configuration for model selection including provider and parameters.

    Attributes:
        provider: Model provider (OpenAI, Anthropic, Local)
        model_name: Model identifier (e.g., "gpt-5-2025-08-07", "claude-3-5-sonnet-20241022")
        max_tokens: Maximum tokens for response (default: 4096)
        temperature: Sampling temperature (default: 0.0 for deterministic)
        cost_per_1k_tokens: Estimated cost per 1K tokens for budgeting
    """
    provider: ModelProvider
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.0
    cost_per_1k_tokens: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "provider": self.provider.value,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "cost_per_1k_tokens": self.cost_per_1k_tokens,
        }


def get_provider_for_model(model_name: str) -> ModelProvider:
    """
    Determine provider based on model name.

    Args:
        model_name: Model identifier

    Returns:
        ModelProvider enum
    """
    model_lower = model_name.lower()

    if "gpt" in model_lower or "o1" in model_lower:
        return ModelProvider.OPENAI
    elif "claude" in model_lower:
        return ModelProvider.ANTHROPIC
    elif "local" in model_lower or "llama" in model_lower:
        return ModelProvider.LOCAL
    else:
        # Default to OpenAI
        return ModelProvider.OPENAI

# ══════════════════════════════════════════════════════════════════════
# PHASE 1.7: Model Routing Rules (Registry-Based)
# ══════════════════════════════════════════════════════════════════════

# Initialize registry (singleton)
_registry = None


def _get_registry():
    """Get or initialize model registry."""
    global _registry
    if _registry is None:
        _registry = get_registry()
    return _registry


# Task type -> Complexity -> Model alias mapping
# These reference aliases in models.json instead of hard-coded IDs
ROUTING_RULES: Dict[str, Dict[str, str]] = {
    # Planning (Manager, Supervisor)
    "planning": {
        "low": "manager_default",
        "high": "high_complexity",  # Subject to interaction index constraint
    },
    # Code generation/editing (Employee)
    "code": {
        "low": "employee_default",
        "high": "high_complexity",  # Subject to interaction index constraint
    },
    # Documentation, commit messages, summaries
    "docs": {
        "low": "employee_default",
        "high": "employee_default",  # Docs rarely need high-end models
    },
    # Analysis (QA, diff summaries, etc.)
    "analysis": {
        "low": "cost_optimized",
        "high": "employee_default",
    },
    # Supervisor reviews
    "review": {
        "low": "cost_optimized",
        "high": "employee_default",
    },
}

# Fallback model alias if task type is unknown
DEFAULT_MODEL_ALIAS = "employee_default"

# High-end model constraint: Only allowed on these interaction indices
HIGH_END_ALLOWED_INTERACTIONS = [2, 3]


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

    PHASE 1.7: Now uses ModelRegistry to resolve model aliases from models.json.

    Args:
        task_type: Type of task ("planning", "code", "docs", "analysis", "review")
        complexity: Task complexity ("low" or "high")
        role: Agent role (for logging/debugging)
        interaction_index: Current interaction/iteration number (1-indexed)
        is_very_important: Flag indicating critical task (overrides complexity)
        config: Optional project config for very_important_stages lookup

    Returns:
        Model identifier string (e.g., "gpt-5-2025-08-07")

    High-End Model Constraint Rules:
    1. High-end models (gpt-5, etc.) are ONLY allowed on interaction indices 2 or 3
    2. Even on those interactions, high-end models are only used if:
       - complexity == "high" OR is_very_important == True
    3. First iteration (index=1) ALWAYS uses cheaper models
    4. Iterations beyond 3 fall back to cheaper models
    """
    # Normalize inputs
    task_type = task_type.lower().strip()
    complexity = complexity.lower().strip()

    # Get registry
    registry = _get_registry()

    # Get base model alias from routing rules
    task_rules = ROUTING_RULES.get(
        task_type, {"low": DEFAULT_MODEL_ALIAS, "high": DEFAULT_MODEL_ALIAS}
    )

    # Determine effective complexity
    effective_complexity = "high" if (complexity == "high" or is_very_important) else "low"

    # Get candidate model alias
    candidate_alias = task_rules.get(effective_complexity, DEFAULT_MODEL_ALIAS)

    # Resolve to ModelInfo
    try:
        candidate_model_info = registry.get_model(candidate_alias)
    except ValueError as e:
        print(f"[ModelRouter] Warning: Failed to resolve alias '{candidate_alias}': {e}")
        # Fallback to default
        candidate_model_info = registry.get_model(DEFAULT_MODEL_ALIAS)

    # Apply high-end model constraint
    # Check if this is a high-complexity alias (which maps to expensive models)
    is_high_end_alias = candidate_alias in ["high_complexity", "reasoning", "premium"]

    if is_high_end_alias:
        # Check interaction index constraint
        if interaction_index not in HIGH_END_ALLOWED_INTERACTIONS:
            # Not allowed - downgrade to default
            print(
                f"[ModelRouter] High-end model requested but interaction_index={interaction_index} "
                f"(allowed: {HIGH_END_ALLOWED_INTERACTIONS}). Downgrading to default."
            )
            candidate_model_info = registry.get_model(DEFAULT_MODEL_ALIAS)
        elif effective_complexity == "low" and not is_very_important:
            # Allowed interaction but not important enough
            print(
                "[ModelRouter] High-end model requested but complexity=low and not important. "
                "Downgrading to default."
            )
            candidate_model_info = registry.get_model(DEFAULT_MODEL_ALIAS)

    # Get final model ID
    final_model_id = candidate_model_info.full_id

    # Log routing decision
    print(
        f"[ModelRouter] role={role}, task={task_type}, complexity={effective_complexity}, "
        f"iteration={interaction_index}, important={is_very_important} -> "
        f"{candidate_alias} ({final_model_id}) [${candidate_model_info.cost_per_1k_prompt:.4f}/1k]"
    )

    return final_model_id


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


# ══════════════════════════════════════════════════════════════════════
# PHASE 1.7: Startup Check for Deprecated Models
# ══════════════════════════════════════════════════════════════════════


def check_model_deprecations() -> None:
    """
    Check for deprecated models at startup.

    Should be called once at application startup to warn about deprecated models.
    Uses ModelRegistry to check all configured aliases.
    """
    try:
        registry = _get_registry()
        registry.warn_if_deprecated()
    except Exception as e:
        print(f"[ModelRouter] Warning: Failed to check model deprecations: {e}")
