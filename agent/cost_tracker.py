# cost_tracker.py
"""
PHASE 1.7: Integrated with ModelRegistry for dynamic pricing.

Cost tracking now queries models.json for up-to-date pricing information
instead of relying on hard-coded prices.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    "gpt-5": {
        "input": 1.250 / 1_000_000,
        "output": 10.000 / 1_000_000,
    },
    "gpt-5-mini": {
        "input": 0.250 / 1_000_000,
        "output": 2.000 / 1_000_000,
    },
    "gpt-5-nano": {
        "input": 0.050 / 1_000_000,
        "output": 0.400 / 1_000_000,
    },
    "gpt-5-pro": {
        "input": 15.00 / 1_000_000,
        "output": 120.00 / 1_000_000,
    },
}

FALLBACK_MODEL = "gpt-5-mini"  # if we don't know a model name, use this as a safe-ish default


def _get_pricing_from_registry(model_id: str) -> Optional[Dict[str, float]]:
    """
    Get pricing from ModelRegistry for a given model ID.

    Args:
        model_id: Full model ID (e.g., "gpt-5-2025-08-07")

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

    # Try partial match (e.g., "gpt-5-2025-08-07" -> "gpt-5")
    for key_prefix in ["gpt-5-pro", "gpt-5-mini", "gpt-5-nano", "gpt-5"]:
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
    model: str = "gpt-5-mini",
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
