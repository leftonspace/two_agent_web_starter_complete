# self_eval.py
"""
Self-evaluation module for the multi-agent orchestrator.

Evaluates RunSummary results to compute quality, safety, and cost scores.
Used by auto-pilot mode to decide whether to retry, adjust, or stop.
"""

from __future__ import annotations

from typing import Any, Dict


def evaluate_run(run_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a completed run and compute quality/safety/cost scores.

    Args:
        run_summary: RunSummary as a dict (from asdict() or dict-based API)
            Expected keys:
            - final_status: "completed", "max_rounds_reached", "cost_cap_exceeded", etc.
            - safety_status: "passed", "failed", or None
            - rounds_completed: int
            - max_rounds: int
            - cost_summary: dict with "total_usd"
            - config: dict with "max_cost_usd"

    Returns:
        Dict with structure:
        {
            "score_quality": float (0-1),
            "score_safety": float (0-1),
            "score_cost": float (0-1),
            "overall_score": float (0-1),
            "reasoning": str,
            "recommendation": "continue" | "retry" | "stop"
        }
    """
    # Extract fields with safe defaults
    final_status = run_summary.get("final_status", "unknown")
    safety_status = run_summary.get("safety_status")
    rounds_completed = run_summary.get("rounds_completed", 0)
    max_rounds = run_summary.get("max_rounds", 1)

    cost_summary = run_summary.get("cost_summary", {})
    total_usd = cost_summary.get("total_usd", 0.0)

    config = run_summary.get("config", {})
    max_cost_usd = float(config.get("max_cost_usd", 0.0) or 0.0)

    # ──────────────────────────────────────────────────────────────────────
    # 1. Quality Score (based on final_status and rounds_completed)
    # ──────────────────────────────────────────────────────────────────────
    score_quality = _compute_quality_score(final_status, rounds_completed, max_rounds)

    # ──────────────────────────────────────────────────────────────────────
    # 2. Safety Score (based on safety_status)
    # ──────────────────────────────────────────────────────────────────────
    score_safety = _compute_safety_score(safety_status)

    # ──────────────────────────────────────────────────────────────────────
    # 3. Cost Score (based on total_usd vs max_cost_usd)
    # ──────────────────────────────────────────────────────────────────────
    score_cost = _compute_cost_score(total_usd, max_cost_usd)

    # ──────────────────────────────────────────────────────────────────────
    # 4. Overall Score (weighted average)
    # ──────────────────────────────────────────────────────────────────────
    # Weights: quality=0.5, safety=0.3, cost=0.2
    overall_score = (
        0.5 * score_quality +
        0.3 * score_safety +
        0.2 * score_cost
    )

    # ──────────────────────────────────────────────────────────────────────
    # 5. Reasoning and Recommendation
    # ──────────────────────────────────────────────────────────────────────
    reasoning_parts = []
    reasoning_parts.append(f"Quality: {score_quality:.2f} (status={final_status}, rounds={rounds_completed}/{max_rounds})")
    reasoning_parts.append(f"Safety: {score_safety:.2f} (status={safety_status})")
    reasoning_parts.append(f"Cost: {score_cost:.2f} (${total_usd:.4f} / ${max_cost_usd:.4f})")
    reasoning = "; ".join(reasoning_parts)

    # Recommendation logic
    recommendation = _compute_recommendation(
        overall_score, final_status, safety_status, score_quality, score_safety
    )

    return {
        "score_quality": round(score_quality, 3),
        "score_safety": round(score_safety, 3),
        "score_cost": round(score_cost, 3),
        "overall_score": round(overall_score, 3),
        "reasoning": reasoning,
        "recommendation": recommendation,
    }


def _compute_quality_score(final_status: str, rounds_completed: int, max_rounds: int) -> float:
    """
    Compute quality score based on final_status and round efficiency.

    Returns:
        0.0 to 1.0
    """
    # Base score from status
    status_scores = {
        "completed": 1.0,
        "success": 1.0,
        "approved": 0.9,
        "max_rounds_reached": 0.5,
        "timeout": 0.3,
        "cost_cap_exceeded": 0.4,
        "aborted_by_user": 0.0,
        "exception": 0.2,
        "unknown": 0.5,
    }
    base_score = status_scores.get(final_status, 0.5)

    # Efficiency penalty: if we used all rounds, slightly reduce score
    if max_rounds > 0:
        efficiency = 1.0 - (rounds_completed / max_rounds) * 0.2
        efficiency = max(0.5, min(1.0, efficiency))  # Clamp to [0.5, 1.0]
    else:
        efficiency = 1.0

    return base_score * efficiency


def _compute_safety_score(safety_status: str | None) -> float:
    """
    Compute safety score based on safety_status.

    Returns:
        0.0 to 1.0
    """
    if safety_status == "passed":
        return 1.0
    elif safety_status == "failed":
        return 0.0
    else:
        # None or unknown: neutral
        return 0.7


def _compute_cost_score(total_usd: float, max_cost_usd: float) -> float:
    """
    Compute cost score based on total_usd vs max_cost_usd.

    Returns:
        0.0 to 1.0 (higher is better = lower cost)
    """
    if max_cost_usd <= 0:
        # No cap configured, assume cost is fine
        return 1.0

    if total_usd <= 0:
        return 1.0

    # Linear scale: 0% of cap = 1.0, 100% of cap = 0.5, >100% = 0.0
    ratio = total_usd / max_cost_usd
    if ratio <= 0.5:
        return 1.0
    elif ratio <= 1.0:
        # Scale from 1.0 to 0.5 as we go from 50% to 100%
        return 1.0 - (ratio - 0.5)
    else:
        # Over budget
        return max(0.0, 0.5 - (ratio - 1.0) * 0.5)


def _compute_recommendation(
    overall_score: float,
    final_status: str,
    safety_status: str | None,
    score_quality: float,
    score_safety: float,
) -> str:
    """
    Compute recommendation based on scores and status.

    Returns:
        "continue" - Run was good, continue to next task
        "retry" - Run had issues but might succeed if retried
        "stop" - Critical failure, stop auto-pilot
    """
    # Critical failures -> stop
    if final_status in ("exception", "aborted_by_user"):
        return "stop"

    # Safety failures -> stop (don't continue with unsafe code)
    if safety_status == "failed" or score_safety < 0.3:
        return "stop"

    # Good overall score -> continue
    if overall_score >= 0.7:
        return "continue"

    # Moderate score with specific issues -> retry
    if overall_score >= 0.4:
        # If quality is low but safety is ok, might be worth a retry
        if score_quality < 0.6 and score_safety >= 0.7:
            return "retry"
        # If we hit max rounds, retry might help
        if final_status == "max_rounds_reached":
            return "retry"

    # Low score -> stop
    if overall_score < 0.4:
        return "stop"

    # Default: continue
    return "continue"
