# cost_tracker.py
"""
PHASE 1.7: Integrated with ModelRegistry for dynamic pricing.
PHASE 2.1 HARDENING: Kill Switch Middleware with hard budget enforcement.

Cost tracking now queries models.json for up-to-date pricing information
instead of relying on hard-coded prices.

Kill Switch Features:
- BudgetExceededException raised when budget is exceeded
- enforce_budget() function for mandatory budget checks
- @budget_guard decorator for wrapping LLM calls
- Configurable hard limits per task/session
"""

from __future__ import annotations

import functools
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar

from agent.core_logging import log_event

# PHASE 1.7: Import model registry for dynamic pricing
try:
    from model_registry import get_registry
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

# Where to store the default runtime history when log_file is None
HISTORY_FILE = Path("cost_history.json")

# DEPRECATED: Hard-coded pricing (Phase 1.7)
# These are kept as fallback only. ModelRegistry provides current pricing.
# USD per token (prices are per 1M tokens, so we divide by 1_000_000)
PRICES_USD_PER_TOKEN: Dict[str, Dict[str, float]] = {
    "gpt-4o": {
        "input": 1.250 / 1_000_000,
        "output": 10.000 / 1_000_000,
    },
    "gpt-4o-mini": {
        "input": 0.250 / 1_000_000,
        "output": 2.000 / 1_000_000,
    },
}

FALLBACK_MODEL = "gpt-4o-mini"  # if we don't know a model name, use this as a safe-ish default


def _get_pricing_from_registry(model_id: str) -> Optional[Dict[str, float]]:
    """
    Get pricing from ModelRegistry for a given model ID.

    Args:
        model_id: Full model ID (e.g., "gpt-4o-2024-11-20")

    Returns:
        Dict with 'input' and 'output' keys (cost per token), or None if not found
    """
    if not REGISTRY_AVAILABLE:
        return None

    try:
        registry = get_registry()

        # Try to find model in registry by full ID
        for model_info in registry.list_models():
            if model_info.full_id == model_id or model_info.model_id in model_id:
                # Convert per-1k pricing to per-token pricing
                return {
                    "input": model_info.cost_per_1k_prompt / 1000,
                    "output": model_info.cost_per_1k_completion / 1000,
                }

        return None
    except Exception:
        # If registry fails, return None and fall back to hard-coded prices
        return None


def _get_pricing_fallback(model_key: str) -> Dict[str, float]:
    """
    Get pricing with fallback logic.

    Tries registry first, then hard-coded prices, then fallback model.

    Args:
        model_key: Model identifier

    Returns:
        Dict with 'input' and 'output' pricing (per token)
    """
    # Try registry first
    registry_pricing = _get_pricing_from_registry(model_key)
    if registry_pricing:
        return registry_pricing

    # Fall back to hard-coded prices
    # Try exact match first
    if model_key in PRICES_USD_PER_TOKEN:
        return PRICES_USD_PER_TOKEN[model_key]

    # Try partial match (e.g., "gpt-4o-2024-11-20" -> "gpt-4o")
    for key_prefix in ["gpt-4o-mini", "gpt-4o"]:
        if key_prefix in model_key:
            return PRICES_USD_PER_TOKEN.get(key_prefix, PRICES_USD_PER_TOKEN[FALLBACK_MODEL])

    # Ultimate fallback
    return PRICES_USD_PER_TOKEN[FALLBACK_MODEL]


@dataclass
class CallRecord:
    role: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float


@dataclass
class CostState:
    calls: List[CallRecord] = field(default_factory=list)

    def add_call(self, role: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
        model_key = model or FALLBACK_MODEL

        # PHASE 1.7: Use registry-based pricing with fallback
        price_cfg = _get_pricing_fallback(model_key)

        input_cost = prompt_tokens * price_cfg["input"]
        output_cost = completion_tokens * price_cfg["output"]
        total_cost = input_cost + output_cost

        self.calls.append(
            CallRecord(
                role=role,
                model=model_key,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                input_cost_usd=input_cost,
                output_cost_usd=output_cost,
                total_cost_usd=total_cost,
            )
        )

    def summary(self) -> Dict[str, Any]:
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0

        by_role: Dict[str, Dict[str, Any]] = {}
        by_model: Dict[str, Dict[str, Any]] = {}

        for c in self.calls:
            total_input_tokens += c.prompt_tokens
            total_output_tokens += c.completion_tokens
            total_cost += c.total_cost_usd

            # by_role
            r = by_role.setdefault(
                c.role,
                {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_usd": 0.0,
                    "num_calls": 0,
                },
            )
            r["prompt_tokens"] += c.prompt_tokens
            r["completion_tokens"] += c.completion_tokens
            r["total_usd"] += c.total_cost_usd
            r["num_calls"] += 1

            # by_model
            m = by_model.setdefault(
                c.model,
                {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_usd": 0.0,
                    "num_calls": 0,
                },
            )
            m["prompt_tokens"] += c.prompt_tokens
            m["completion_tokens"] += c.completion_tokens
            m["total_usd"] += c.total_cost_usd
            m["num_calls"] += 1

        return {
            "num_calls": len(self.calls),
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_usd": round(total_cost, 6),
            "by_role": {
                role: {
                    **vals,
                    "total_usd": round(vals["total_usd"], 6),
                }
                for role, vals in by_role.items()
            },
            "by_model": {
                model: {
                    **vals,
                    "total_usd": round(vals["total_usd"], 6),
                }
                for model, vals in by_model.items()
            },
        }


_GLOBAL_STATE = CostState()


def reset() -> None:
    """Reset the global cost tracking state for a new run."""
    _GLOBAL_STATE.calls.clear()


def register_call(role: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Register a single API call for cost accounting."""
    try:
        _GLOBAL_STATE.add_call(role, model, prompt_tokens, completion_tokens)
    except Exception as e:  # noqa: BLE001
        # We don't want cost-tracking errors to kill the main flow
        print(f"[CostTracker] Failed to register call: {e}")


def get_summary() -> Dict[str, Any]:
    """Get a structured summary of costs and tokens for the current run."""
    return _GLOBAL_STATE.summary()


def get_total_cost_usd() -> float:
    """Return the estimated total cost in USD for the current run."""
    try:
        return _GLOBAL_STATE.summary()["total_usd"]
    except Exception:
        return 0.0


def check_cost_cap(
    max_cost_usd: float,
    estimated_tokens: int = 5000,
    model: str = "gpt-4o-mini",
) -> tuple[bool, float, str]:
    """
    STAGE 5.2: Check if making another LLM call would exceed the cost cap.

    Args:
        max_cost_usd: Maximum allowed cost in USD
        estimated_tokens: Rough estimate of tokens for next call (input + output)
        model: Model that will be used for the call

    Returns:
        Tuple of (would_exceed, current_cost, message)
        - would_exceed: True if the call would likely exceed the cap
        - current_cost: Current total cost in USD
        - message: Human-readable explanation
    """
    if max_cost_usd <= 0:
        # No cap set
        return (False, 0.0, "No cost cap configured")

    current_cost = get_total_cost_usd()

    # Estimate cost of next call
    # Use a conservative estimate: assume all tokens are output tokens (more expensive)
    # PHASE 1.7: Use registry-based pricing with fallback
    price_cfg = _get_pricing_fallback(model or FALLBACK_MODEL)
    # Conservative: assume all tokens are output (more expensive)
    estimated_call_cost = estimated_tokens * price_cfg["output"]

    projected_cost = current_cost + estimated_call_cost

    if projected_cost > max_cost_usd:
        message = (
            f"Cost cap would be exceeded: current=${current_cost:.4f}, "
            f"estimated next call=${estimated_call_cost:.4f}, "
            f"projected total=${projected_cost:.4f}, "
            f"cap=${max_cost_usd:.4f}"
        )
        return (True, current_cost, message)

    remaining = max_cost_usd - current_cost
    message = (
        f"Within budget: current=${current_cost:.4f}, "
        f"remaining=${remaining:.4f}, "
        f"cap=${max_cost_usd:.4f}"
    )
    return (False, current_cost, message)


def load_history() -> list[dict[str, Any]]:
    """Load the shared history from HISTORY_FILE. Best-effort and safe on errors."""
    if not HISTORY_FILE.exists():
        return []
    try:
        text = HISTORY_FILE.read_text(encoding="utf-8")
        return json.loads(text)
    except json.JSONDecodeError:
        return []


def save_history(history: list[dict[str, Any]]) -> None:
    """Persist the shared history to HISTORY_FILE."""
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def append_history(
    log_file: Path | None = None,
    project_name: str | None = None,
    task: str | None = None,
    status: str | None = None,
    extra: Dict[str, Any] | None = None,
    *,
    total_usd: float | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    model: str | None = None,
) -> None:
    """
    Append a history record.

    Two usage modes:

    1) Tests call this with an explicit `log_file` and metadata fields
       (project_name, task, status, extra). We append one JSON line to
       that file. The field is named "project" to match test expectations.

    2) Runtime usage logging from llm.chat_json() passes cost-related
       fields (total_usd, prompt_tokens, completion_tokens, model) with
       log_file=None. We append to the default history file via
       load_history/save_history.
    """

    record: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        # NOTE: tests expect the key to be "project"
        "project": project_name,
        "task": task,
        "status": status,
        "total_usd": total_usd,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "model": model,
    }

    if extra:
        record.update(extra)

    if log_file is not None:
        # Test / ad-hoc mode: write JSONL to the provided file
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    else:
        # Default runtime mode: use the shared cost history file
        history = load_history()
        history.append(record)
        save_history(history)


# ============================================================================
# PHASE 2.1: Kill Switch Middleware - Hard Budget Enforcement
# ============================================================================

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])

# Default budget limits (can be overridden via environment variables)
DEFAULT_TASK_BUDGET_USD = float(os.getenv("JARVIS_TASK_BUDGET_USD", "5.00"))
DEFAULT_SESSION_BUDGET_USD = float(os.getenv("JARVIS_SESSION_BUDGET_USD", "50.00"))


class BudgetExceededException(Exception):
    """
    Raised when a budget limit is exceeded.

    This is a hard stop - execution must halt to prevent runaway costs.
    """

    def __init__(
        self,
        current_cost: float,
        budget_limit: float,
        budget_type: str = "task",
        message: Optional[str] = None,
    ):
        self.current_cost = current_cost
        self.budget_limit = budget_limit
        self.budget_type = budget_type

        if message is None:
            message = (
                f"BUDGET EXCEEDED: {budget_type} budget of ${budget_limit:.4f} exceeded. "
                f"Current cost: ${current_cost:.4f}. "
                f"JARVIS has been severed from the API. Manual override required."
            )

        super().__init__(message)

        # Log the budget breach
        log_event("budget_exceeded", {
            "current_cost": current_cost,
            "budget_limit": budget_limit,
            "budget_type": budget_type,
            "overage": current_cost - budget_limit,
        })


@dataclass
class BudgetConfig:
    """Configuration for budget enforcement."""
    task_budget_usd: float = DEFAULT_TASK_BUDGET_USD
    session_budget_usd: float = DEFAULT_SESSION_BUDGET_USD
    warn_at_percent: float = 80.0  # Warn when 80% of budget used
    enabled: bool = True


# Global budget configuration
_budget_config = BudgetConfig()


def configure_budget(
    task_budget_usd: Optional[float] = None,
    session_budget_usd: Optional[float] = None,
    warn_at_percent: Optional[float] = None,
    enabled: Optional[bool] = None,
) -> None:
    """
    Configure budget limits.

    Args:
        task_budget_usd: Maximum cost per task (default $5.00)
        session_budget_usd: Maximum cost per session (default $50.00)
        warn_at_percent: Percentage at which to warn (default 80%)
        enabled: Enable/disable budget enforcement
    """
    global _budget_config

    if task_budget_usd is not None:
        _budget_config.task_budget_usd = task_budget_usd
    if session_budget_usd is not None:
        _budget_config.session_budget_usd = session_budget_usd
    if warn_at_percent is not None:
        _budget_config.warn_at_percent = warn_at_percent
    if enabled is not None:
        _budget_config.enabled = enabled

    log_event("budget_configured", {
        "task_budget_usd": _budget_config.task_budget_usd,
        "session_budget_usd": _budget_config.session_budget_usd,
        "warn_at_percent": _budget_config.warn_at_percent,
        "enabled": _budget_config.enabled,
    })


def get_budget_config() -> BudgetConfig:
    """Get current budget configuration."""
    return _budget_config


def enforce_budget(
    budget_limit: Optional[float] = None,
    budget_type: str = "task",
    estimated_next_cost: float = 0.0,
) -> None:
    """
    Enforce budget limit - raises BudgetExceededException if exceeded.

    This is the HARD STOP middleware. Call this before every LLM request.

    Args:
        budget_limit: Budget limit in USD (default from config)
        budget_type: Type of budget ("task" or "session")
        estimated_next_cost: Estimated cost of next call (for proactive blocking)

    Raises:
        BudgetExceededException: If budget would be exceeded
    """
    if not _budget_config.enabled:
        return

    # Get appropriate budget limit
    if budget_limit is None:
        if budget_type == "session":
            budget_limit = _budget_config.session_budget_usd
        else:
            budget_limit = _budget_config.task_budget_usd

    # Skip if no limit configured
    if budget_limit <= 0:
        return

    current_cost = get_total_cost_usd()
    projected_cost = current_cost + estimated_next_cost

    # Check if we've already exceeded
    if current_cost >= budget_limit:
        raise BudgetExceededException(
            current_cost=current_cost,
            budget_limit=budget_limit,
            budget_type=budget_type,
        )

    # Check if next call would exceed (proactive blocking)
    if projected_cost > budget_limit:
        raise BudgetExceededException(
            current_cost=current_cost,
            budget_limit=budget_limit,
            budget_type=budget_type,
            message=(
                f"BUDGET WOULD BE EXCEEDED: Next call (est. ${estimated_next_cost:.4f}) "
                f"would push {budget_type} cost to ${projected_cost:.4f}, "
                f"exceeding limit of ${budget_limit:.4f}. "
                f"Current cost: ${current_cost:.4f}. Blocking preemptively."
            ),
        )

    # Warn if approaching limit
    usage_percent = (current_cost / budget_limit) * 100
    if usage_percent >= _budget_config.warn_at_percent:
        remaining = budget_limit - current_cost
        log_event("budget_warning", {
            "current_cost": current_cost,
            "budget_limit": budget_limit,
            "budget_type": budget_type,
            "usage_percent": usage_percent,
            "remaining": remaining,
        })
        print(
            f"[CostTracker] WARNING: {usage_percent:.1f}% of {budget_type} budget used. "
            f"Remaining: ${remaining:.4f}"
        )


def budget_guard(
    budget_limit: Optional[float] = None,
    budget_type: str = "task",
    estimated_tokens: int = 5000,
    model: str = "gpt-4o-mini",
) -> Callable[[F], F]:
    """
    Decorator to enforce budget before executing a function.

    Use this to wrap LLM call functions to automatically enforce budget.

    Args:
        budget_limit: Budget limit in USD (default from config)
        budget_type: Type of budget ("task" or "session")
        estimated_tokens: Estimated tokens for cost calculation
        model: Model for cost estimation

    Returns:
        Decorated function

    Example:
        @budget_guard(budget_limit=5.00)
        async def call_llm(prompt: str) -> str:
            ...

        @budget_guard(budget_type="session")
        def expensive_operation():
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Estimate cost of this call
            price_cfg = _get_pricing_fallback(model)
            estimated_cost = estimated_tokens * price_cfg["output"]

            # Enforce budget (will raise if exceeded)
            enforce_budget(
                budget_limit=budget_limit,
                budget_type=budget_type,
                estimated_next_cost=estimated_cost,
            )

            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Estimate cost of this call
            price_cfg = _get_pricing_fallback(model)
            estimated_cost = estimated_tokens * price_cfg["output"]

            # Enforce budget (will raise if exceeded)
            enforce_budget(
                budget_limit=budget_limit,
                budget_type=budget_type,
                estimated_next_cost=estimated_cost,
            )

            return await func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def get_budget_status() -> Dict[str, Any]:
    """
    Get current budget status.

    Returns:
        Dict with current cost, limits, and usage percentages
    """
    current_cost = get_total_cost_usd()
    task_limit = _budget_config.task_budget_usd
    session_limit = _budget_config.session_budget_usd

    return {
        "current_cost_usd": current_cost,
        "task_budget": {
            "limit_usd": task_limit,
            "remaining_usd": max(0, task_limit - current_cost),
            "usage_percent": (current_cost / task_limit * 100) if task_limit > 0 else 0,
            "exceeded": current_cost >= task_limit if task_limit > 0 else False,
        },
        "session_budget": {
            "limit_usd": session_limit,
            "remaining_usd": max(0, session_limit - current_cost),
            "usage_percent": (current_cost / session_limit * 100) if session_limit > 0 else 0,
            "exceeded": current_cost >= session_limit if session_limit > 0 else False,
        },
        "enforcement_enabled": _budget_config.enabled,
    }
