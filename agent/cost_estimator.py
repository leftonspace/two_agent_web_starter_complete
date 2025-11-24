# cost_estimator.py
"""
Cost estimation module for the multi-agent orchestrator.

Provides rough cost estimates before starting a run based on:
- Mode (2loop vs 3loop)
- Max rounds
- Models used per role
- Token budgets per round
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from cost_tracker import FALLBACK_MODEL, PRICES_USD_PER_TOKEN


def estimate_run_cost(
    mode: str,
    max_rounds: int,
    models_used: Dict[str, str],
    *,
    tokens_per_round_prompt: int = 8_000,
    tokens_per_round_completion: int = 8_000,
) -> Dict[str, Any]:
    """
    Estimate the rough upper-bound cost for a multi-agent run.

    Args:
        mode: "2loop" or "3loop"
        max_rounds: Maximum number of iterations
        models_used: Dict mapping role -> model name
            e.g., {"manager": "gpt-4o-mini", "supervisor": "gpt-4o-mini", "employee": "gpt-4o"}
        tokens_per_round_prompt: Estimated prompt tokens per round per role
        tokens_per_round_completion: Estimated completion tokens per round per role

    Returns:
        Dict with structure:
        {
            "per_round": {
                "manager": {"model": "...", "prompt_tokens": ..., "completion_tokens": ..., "usd": ...},
                "supervisor": {...} or None,
                "employee": {...},
            },
            "max_rounds": max_rounds,
            "estimated_total_usd": ...,
        }
    """
    # Determine which roles are active based on mode
    active_roles = ["manager", "employee"]
    if mode == "3loop":
        active_roles.append("supervisor")

    per_round_costs: Dict[str, Optional[Dict[str, Any]]] = {
        "manager": None,
        "supervisor": None,
        "employee": None,
    }

    total_usd_per_round = 0.0

    # Calculate cost for each active role
    for role in active_roles:
        model = models_used.get(role, FALLBACK_MODEL)

        # Get pricing for this model
        if model not in PRICES_USD_PER_TOKEN:
            # Fall back to default model pricing if unknown
            model_key = FALLBACK_MODEL
        else:
            model_key = model

        prices = PRICES_USD_PER_TOKEN[model_key]

        # Calculate cost for this role per round
        input_cost = tokens_per_round_prompt * prices["input"]
        output_cost = tokens_per_round_completion * prices["output"]
        total_cost = input_cost + output_cost

        per_round_costs[role] = {
            "model": model,
            "prompt_tokens": tokens_per_round_prompt,
            "completion_tokens": tokens_per_round_completion,
            "usd": round(total_cost, 6),
        }

        total_usd_per_round += total_cost

    # Calculate total estimated cost
    # For planning phase, we add one extra manager call (index=0)
    # Then multiply by max_rounds for iterations
    estimated_total = total_usd_per_round * max_rounds

    # Add planning phase cost (manager only, roughly same tokens)
    if "manager" in active_roles and per_round_costs["manager"]:
        estimated_total += per_round_costs["manager"]["usd"]

    return {
        "per_round": per_round_costs,
        "max_rounds": max_rounds,
        "per_round_total_usd": round(total_usd_per_round, 6),
        "estimated_total_usd": round(estimated_total, 6),
    }


def format_cost_estimate(
    estimate: Dict[str, Any],
    max_cost_usd: float = 0.0,
    cost_warning_usd: float = 0.0,
) -> str:
    """
    Format a cost estimate as a human-readable string.

    Args:
        estimate: Result from estimate_run_cost()
        max_cost_usd: Maximum cost cap (if set)
        cost_warning_usd: Warning threshold (if set)

    Returns:
        Formatted multi-line string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("  COST ESTIMATE (Upper Bound)")
    lines.append("=" * 60)

    # Per-round breakdown
    per_round = estimate["per_round"]
    lines.append("\nPer-round costs:")
    for role in ["manager", "supervisor", "employee"]:
        role_data = per_round.get(role)
        if role_data:
            lines.append(
                f"  {role.capitalize():12} ({role_data['model']:25}): ${role_data['usd']:.6f}"
            )

    lines.append(f"\nPer-round total: ${estimate['per_round_total_usd']:.6f}")
    lines.append(f"Max rounds:      {estimate['max_rounds']}")
    lines.append(f"\nEstimated total: ${estimate['estimated_total_usd']:.4f} USD")

    # Show caps/warnings if configured
    if cost_warning_usd > 0:
        lines.append(f"Warning threshold: ${cost_warning_usd:.4f} USD")
    if max_cost_usd > 0:
        lines.append(f"Hard cost cap:     ${max_cost_usd:.4f} USD")

    # Warning if estimate exceeds cap
    if max_cost_usd > 0 and estimate["estimated_total_usd"] > max_cost_usd:
        lines.append("")
        lines.append("⚠️  WARNING: Estimated cost exceeds configured max_cost_usd!")
        lines.append(f"    Estimate: ${estimate['estimated_total_usd']:.4f}")
        lines.append(f"    Max cap:  ${max_cost_usd:.4f}")

    lines.append("=" * 60)

    return "\n".join(lines)
