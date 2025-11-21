"""
Self-optimization and auto-tuning module for the multi-agent orchestrator.

Analyzes historical run data to provide intelligent recommendations and
automatically tune settings for better performance, cost, and quality.

STAGE 12: Self-Optimization & Auto-Tuning Layer ("Brain")
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import analytics

# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class ModeStats:
    """Statistics for a specific orchestration mode (2loop or 3loop)."""

    mode: str  # "2loop" or "3loop"
    runs_count: int = 0
    avg_cost: float = 0.0
    median_cost: float = 0.0
    avg_duration: float = 0.0
    qa_passed: int = 0
    qa_warning: int = 0
    qa_failed: int = 0
    qa_pass_rate: float = 0.0
    avg_rounds_used: float = 0.0


@dataclass
class StrategyStats:
    """Statistics for a specific prompt strategy."""

    strategy: str
    runs_count: int = 0
    avg_cost: float = 0.0
    median_cost: float = 0.0
    avg_duration: float = 0.0
    qa_passed: int = 0
    qa_warning: int = 0
    qa_failed: int = 0
    qa_pass_rate: float = 0.0


@dataclass
class ProjectProfile:
    """
    Complete profile of a project based on historical runs.

    Aggregates performance metrics across different modes, strategies,
    and configurations to enable intelligent recommendations.
    """

    project_id: str
    runs_count: int = 0

    # Mode statistics
    modes: Dict[str, ModeStats] = field(default_factory=dict)
    preferred_mode: Optional[str] = None

    # Cost patterns
    min_cost: float = 0.0
    median_cost: float = 0.0
    max_cost: float = 0.0
    avg_cost: float = 0.0

    # Rounds patterns
    avg_rounds_used: float = 0.0
    max_rounds_completed: int = 0
    rounds_distribution: Dict[int, int] = field(default_factory=dict)  # {rounds: count}

    # Strategy performance
    strategies: Dict[str, StrategyStats] = field(default_factory=dict)
    preferred_strategy: Optional[str] = None

    # Quality metrics
    overall_qa_pass_rate: float = 0.0
    qa_passed: int = 0
    qa_warning: int = 0
    qa_failed: int = 0

    # Model usage
    models_used: Dict[str, int] = field(default_factory=dict)  # {model: count}

    # Metadata
    last_run_time: Optional[str] = None
    sufficient_data: bool = False  # True if enough runs for reliable recommendations


@dataclass
class Recommendation:
    """
    A single tuning recommendation with explanation.

    Represents one suggested change to improve cost, performance, or quality.
    """

    category: str  # "mode", "rounds", "cost", "strategy"
    current_value: Any
    recommended_value: Any
    explanation: str
    confidence: str  # "high", "medium", "low"
    estimated_impact: str  # e.g., "25% cost reduction", "Same QA, 30% faster"


@dataclass
class TuningConfig:
    """Configuration for auto-tuning behavior."""

    enabled: bool = False
    apply_safely: bool = True
    min_runs_for_recommendations: int = 5
    confidence_threshold: str = "medium"  # "high", "medium", "low"


# ══════════════════════════════════════════════════════════════════════
# Project Profiling
# ══════════════════════════════════════════════════════════════════════


def build_project_profile(project_id: str) -> ProjectProfile:
    """
    Build a comprehensive profile for a project based on historical runs.

    Args:
        project_id: Project identifier (subfolder name)

    Returns:
        ProjectProfile with aggregated statistics
    """
    profile = ProjectProfile(project_id=project_id)

    # Load all runs and filter by project
    all_runs = analytics.load_all_runs()
    project_runs = [
        r for r in all_runs
        if Path(r.get("project_dir", "")).name == project_id
    ]

    profile.runs_count = len(project_runs)

    if not project_runs:
        return profile

    # Extract basic metrics
    costs = []
    rounds_used = []
    qa_statuses = {"passed": 0, "warning": 0, "failed": 0}
    modes_data = defaultdict(list)
    strategies_data = defaultdict(list)
    models_count = defaultdict(int)

    for run in project_runs:
        # Cost
        cost = run.get("cost_summary", {}).get("total_cost_usd", 0.0)
        if cost > 0:
            costs.append(cost)

        # Rounds
        rounds = run.get("rounds_completed", 0)
        if rounds > 0:
            rounds_used.append(rounds)
            profile.rounds_distribution[rounds] = profile.rounds_distribution.get(rounds, 0) + 1

        # QA status
        qa_status = run.get("qa_status")
        if qa_status in qa_statuses:
            qa_statuses[qa_status] += 1

        # Mode
        mode = run.get("mode", "").lower()
        if mode in ("2loop", "3loop"):
            modes_data[mode].append(run)

        # Strategy (from config or default to "baseline")
        strategy = run.get("config", {}).get("prompt_strategy", "baseline")
        strategies_data[strategy].append(run)

        # Models
        models_used = run.get("models_used", {})
        for model in models_used.values():
            if model:
                models_count[model] += 1

        # Last run time
        started_at = run.get("started_at")
        if started_at:
            if not profile.last_run_time or started_at > profile.last_run_time:
                profile.last_run_time = started_at

    # Compute cost statistics
    if costs:
        profile.min_cost = min(costs)
        profile.max_cost = max(costs)
        profile.median_cost = statistics.median(costs)
        profile.avg_cost = statistics.mean(costs)

    # Compute rounds statistics
    if rounds_used:
        profile.avg_rounds_used = statistics.mean(rounds_used)
        profile.max_rounds_completed = max(rounds_used)

    # Compute QA statistics
    profile.qa_passed = qa_statuses["passed"]
    profile.qa_warning = qa_statuses["warning"]
    profile.qa_failed = qa_statuses["failed"]
    total_qa_runs = sum(qa_statuses.values())
    if total_qa_runs > 0:
        profile.overall_qa_pass_rate = profile.qa_passed / total_qa_runs

    # Compute per-mode statistics
    for mode, runs in modes_data.items():
        mode_stats = _compute_mode_stats(mode, runs)
        profile.modes[mode] = mode_stats

    # Determine preferred mode
    profile.preferred_mode = _determine_preferred_mode(profile.modes)

    # Compute per-strategy statistics
    for strategy, runs in strategies_data.items():
        strategy_stats = _compute_strategy_stats(strategy, runs)
        profile.strategies[strategy] = strategy_stats

    # Determine preferred strategy
    profile.preferred_strategy = _determine_preferred_strategy(profile.strategies)

    # Models used
    profile.models_used = dict(models_count)

    # Check if we have sufficient data for reliable recommendations
    tuning_config = load_tuning_config()
    profile.sufficient_data = profile.runs_count >= tuning_config.min_runs_for_recommendations

    return profile


def _compute_mode_stats(mode: str, runs: List[Dict[str, Any]]) -> ModeStats:
    """Compute statistics for runs using a specific mode."""
    stats = ModeStats(mode=mode, runs_count=len(runs))

    costs = []
    durations = []
    rounds = []
    qa_counts = {"passed": 0, "warning": 0, "failed": 0}

    for run in runs:
        # Cost
        cost = run.get("cost_summary", {}).get("total_cost_usd", 0.0)
        if cost > 0:
            costs.append(cost)

        # Duration
        started_at = run.get("started_at")
        finished_at = run.get("finished_at")
        if started_at and finished_at:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                duration = (end - start).total_seconds()
                durations.append(duration)
            except Exception:
                pass

        # Rounds
        rounds_used = run.get("rounds_completed", 0)
        if rounds_used > 0:
            rounds.append(rounds_used)

        # QA
        qa_status = run.get("qa_status")
        if qa_status in qa_counts:
            qa_counts[qa_status] += 1

    # Compute aggregates
    if costs:
        stats.avg_cost = statistics.mean(costs)
        stats.median_cost = statistics.median(costs)

    if durations:
        stats.avg_duration = statistics.mean(durations)

    if rounds:
        stats.avg_rounds_used = statistics.mean(rounds)

    # QA statistics
    stats.qa_passed = qa_counts["passed"]
    stats.qa_warning = qa_counts["warning"]
    stats.qa_failed = qa_counts["failed"]
    total_qa = sum(qa_counts.values())
    if total_qa > 0:
        stats.qa_pass_rate = stats.qa_passed / total_qa

    return stats


def _compute_strategy_stats(strategy: str, runs: List[Dict[str, Any]]) -> StrategyStats:
    """Compute statistics for runs using a specific prompt strategy."""
    stats = StrategyStats(strategy=strategy, runs_count=len(runs))

    costs = []
    durations = []
    qa_counts = {"passed": 0, "warning": 0, "failed": 0}

    for run in runs:
        # Cost
        cost = run.get("cost_summary", {}).get("total_cost_usd", 0.0)
        if cost > 0:
            costs.append(cost)

        # Duration
        started_at = run.get("started_at")
        finished_at = run.get("finished_at")
        if started_at and finished_at:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                end = datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
                duration = (end - start).total_seconds()
                durations.append(duration)
            except Exception:
                pass

        # QA
        qa_status = run.get("qa_status")
        if qa_status in qa_counts:
            qa_counts[qa_status] += 1

    # Compute aggregates
    if costs:
        stats.avg_cost = statistics.mean(costs)
        stats.median_cost = statistics.median(costs)

    if durations:
        stats.avg_duration = statistics.mean(durations)

    # QA statistics
    stats.qa_passed = qa_counts["passed"]
    stats.qa_warning = qa_counts["warning"]
    stats.qa_failed = qa_counts["failed"]
    total_qa = sum(qa_counts.values())
    if total_qa > 0:
        stats.qa_pass_rate = stats.qa_passed / total_qa

    return stats


def _determine_preferred_mode(modes: Dict[str, ModeStats]) -> Optional[str]:
    """
    Determine the preferred mode based on QA pass rate and cost.

    Prioritize QA pass rate, then use cost as tie-breaker.
    """
    if not modes:
        return None

    # If only one mode, return it
    if len(modes) == 1:
        return list(modes.keys())[0]

    # Compare modes
    best_mode = None
    best_score = -1

    for mode, stats in modes.items():
        if stats.runs_count < 3:  # Need minimum sample size
            continue

        # Score based on QA pass rate (primary) and cost (secondary)
        # Higher QA pass rate is better, lower cost is better
        qa_score = stats.qa_pass_rate
        cost_score = 1.0 / (stats.median_cost + 0.01) if stats.median_cost > 0 else 0

        # Weight QA more heavily than cost (70% QA, 30% cost)
        score = (qa_score * 0.7) + (cost_score * 0.3)

        if score > best_score:
            best_score = score
            best_mode = mode

    return best_mode


def _determine_preferred_strategy(strategies: Dict[str, StrategyStats]) -> Optional[str]:
    """
    Determine the preferred prompt strategy based on QA and cost.

    Similar logic to mode preference.
    """
    if not strategies:
        return None

    # If only one strategy, return it
    if len(strategies) == 1:
        return list(strategies.keys())[0]

    # Compare strategies
    best_strategy = None
    best_score = -1

    for strategy, stats in strategies.items():
        if stats.runs_count < 3:  # Need minimum sample size
            continue

        # Score based on QA pass rate (primary) and cost (secondary)
        qa_score = stats.qa_pass_rate
        cost_score = 1.0 / (stats.median_cost + 0.01) if stats.median_cost > 0 else 0

        # Weight QA more heavily than cost
        score = (qa_score * 0.7) + (cost_score * 0.3)

        if score > best_score:
            best_score = score
            best_strategy = strategy

    return best_strategy


# ══════════════════════════════════════════════════════════════════════
# Recommendation Engine
# ══════════════════════════════════════════════════════════════════════


def generate_recommendations(
    profile: ProjectProfile,
    current_config: Dict[str, Any]
) -> List[Recommendation]:
    """
    Generate tuning recommendations based on project profile and current config.

    Args:
        profile: Project profile with historical data
        current_config: Current project configuration

    Returns:
        List of Recommendation objects with explanations
    """
    recommendations = []

    if not profile.sufficient_data:
        return recommendations

    # Recommendation 1: Mode optimization
    mode_rec = _recommend_mode(profile, current_config)
    if mode_rec:
        recommendations.append(mode_rec)

    # Recommendation 2: max_rounds optimization
    rounds_rec = _recommend_max_rounds(profile, current_config)
    if rounds_rec:
        recommendations.append(rounds_rec)

    # Recommendation 3: Cost limit optimization
    cost_rec = _recommend_cost_limit(profile, current_config)
    if cost_rec:
        recommendations.append(cost_rec)

    # Recommendation 4: Prompt strategy optimization
    strategy_rec = _recommend_strategy(profile, current_config)
    if strategy_rec:
        recommendations.append(strategy_rec)

    return recommendations


def _recommend_mode(
    profile: ProjectProfile,
    current_config: Dict[str, Any]
) -> Optional[Recommendation]:
    """Recommend mode change if a different mode performs better."""
    current_mode = current_config.get("mode", "3loop")
    preferred_mode = profile.preferred_mode

    if not preferred_mode or preferred_mode == current_mode:
        return None

    # Check if both modes have sufficient data
    if preferred_mode not in profile.modes or current_mode not in profile.modes:
        return None

    preferred_stats = profile.modes[preferred_mode]
    current_stats = profile.modes[current_mode]

    # Need minimum sample size for both
    if preferred_stats.runs_count < 3 or current_stats.runs_count < 3:
        return None

    # Compare QA pass rates
    qa_diff = preferred_stats.qa_pass_rate - current_stats.qa_pass_rate

    # Compare costs
    cost_diff_pct = 0
    if current_stats.median_cost > 0:
        cost_diff_pct = (current_stats.median_cost - preferred_stats.median_cost) / current_stats.median_cost * 100

    # Only recommend if preferred mode has similar or better QA
    if qa_diff < -0.05:  # More than 5% worse QA
        return None

    # Build explanation
    if qa_diff >= 0.05:  # Significantly better QA
        explanation = (
            f"Based on {preferred_stats.runs_count} {preferred_mode} runs vs "
            f"{current_stats.runs_count} {current_mode} runs, {preferred_mode} has "
            f"{preferred_stats.qa_pass_rate:.0%} QA pass rate "
            f"({qa_diff:+.0%} better)"
        )
        confidence = "high"
    else:  # Similar QA, check cost
        if cost_diff_pct > 15:  # Significantly cheaper
            explanation = (
                f"Based on {preferred_stats.runs_count} {preferred_mode} runs vs "
                f"{current_stats.runs_count} {current_mode} runs, {preferred_mode} has "
                f"similar QA ({preferred_stats.qa_pass_rate:.0%} vs {current_stats.qa_pass_rate:.0%}) "
                f"but {cost_diff_pct:.0f}% lower cost"
            )
            confidence = "high"
        elif cost_diff_pct > 5:
            explanation = (
                f"{preferred_mode} has similar QA but {cost_diff_pct:.0f}% lower cost "
                f"based on {preferred_stats.runs_count} runs"
            )
            confidence = "medium"
        else:
            return None  # Not enough difference to recommend

    # Estimate impact
    if qa_diff >= 0.05 and cost_diff_pct > 10:
        impact = f"{qa_diff:+.0%} QA, {cost_diff_pct:.0f}% cost reduction"
    elif qa_diff >= 0.05:
        impact = f"{qa_diff:+.0%} QA improvement"
    else:
        impact = f"{cost_diff_pct:.0f}% cost reduction"

    return Recommendation(
        category="mode",
        current_value=current_mode,
        recommended_value=preferred_mode,
        explanation=explanation,
        confidence=confidence,
        estimated_impact=impact
    )


def _recommend_max_rounds(
    profile: ProjectProfile,
    current_config: Dict[str, Any]
) -> Optional[Recommendation]:
    """Recommend max_rounds adjustment based on actual usage patterns."""
    current_max_rounds = current_config.get("max_rounds", 3)

    if not profile.rounds_distribution:
        return None

    # Calculate what percentage of runs complete by various round counts
    total_runs = sum(profile.rounds_distribution.values())
    cumulative = 0
    rounds_for_90pct = None
    rounds_for_95pct = None

    for rounds in sorted(profile.rounds_distribution.keys()):
        cumulative += profile.rounds_distribution[rounds]
        pct = cumulative / total_runs

        if pct >= 0.90 and rounds_for_90pct is None:
            rounds_for_90pct = rounds
        if pct >= 0.95 and rounds_for_95pct is None:
            rounds_for_95pct = rounds

    # Recommend lower max_rounds if most runs finish early
    if rounds_for_95pct and rounds_for_95pct < current_max_rounds:
        recommended = rounds_for_95pct
        pct_completing = cumulative / total_runs

        explanation = (
            f"Based on {total_runs} runs, {pct_completing:.0%} complete successfully "
            f"by round {recommended}. Current max_rounds={current_max_rounds} is rarely needed."
        )

        # Check if this would affect QA
        qa_concern = ""
        if profile.overall_qa_pass_rate < 0.8:
            confidence = "low"
            qa_concern = " However, overall QA pass rate is below 80%, so verify quality."
        else:
            confidence = "high"

        return Recommendation(
            category="rounds",
            current_value=current_max_rounds,
            recommended_value=recommended,
            explanation=explanation + qa_concern,
            confidence=confidence,
            estimated_impact=f"Faster completion, {(current_max_rounds - recommended) / current_max_rounds * 100:.0f}% fewer potential iterations"
        )

    # Recommend higher max_rounds if many runs hit the limit
    if profile.max_rounds_completed >= current_max_rounds:
        runs_at_limit = profile.rounds_distribution.get(current_max_rounds, 0)
        if runs_at_limit / total_runs > 0.2:  # More than 20% hit the limit
            recommended = current_max_rounds + 1

            explanation = (
                f"Based on {total_runs} runs, {runs_at_limit / total_runs:.0%} reach "
                f"the current max_rounds={current_max_rounds} limit. Consider increasing "
                f"to allow more iterations when needed."
            )

            return Recommendation(
                category="rounds",
                current_value=current_max_rounds,
                recommended_value=recommended,
                explanation=explanation,
                confidence="medium",
                estimated_impact="Better completion rate for complex tasks"
            )

    return None


def _recommend_cost_limit(
    profile: ProjectProfile,
    current_config: Dict[str, Any]
) -> Optional[Recommendation]:
    """Recommend cost limit adjustment based on actual costs."""
    current_max_cost = current_config.get("max_cost_usd", 0.0)

    if not current_max_cost or not profile.median_cost:
        return None

    # Recommend cost limit that covers 95% of runs with some buffer
    # Use max cost from history + 20% buffer
    recommended_cost = profile.max_cost * 1.2

    # Round to 2 decimal places
    recommended_cost = round(recommended_cost, 2)

    # Only recommend if significantly different from current
    diff_pct = abs(recommended_cost - current_max_cost) / current_max_cost * 100

    if diff_pct < 15:  # Less than 15% difference
        return None

    if recommended_cost < current_max_cost:
        explanation = (
            f"Based on {profile.runs_count} runs, median cost is ${profile.median_cost:.2f} "
            f"and max is ${profile.max_cost:.2f}. Current limit of ${current_max_cost:.2f} "
            f"is higher than needed."
        )
        impact = "Tighter cost control"
        confidence = "medium"
    else:
        explanation = (
            f"Based on {profile.runs_count} runs, max cost is ${profile.max_cost:.2f}. "
            f"Current limit of ${current_max_cost:.2f} may be too restrictive. "
            f"Recommended: ${recommended_cost:.2f} (max + 20% buffer)"
        )
        impact = "Avoid hitting cost limits"
        confidence = "low"

    return Recommendation(
        category="cost",
        current_value=current_max_cost,
        recommended_value=recommended_cost,
        explanation=explanation,
        confidence=confidence,
        estimated_impact=impact
    )


def _recommend_strategy(
    profile: ProjectProfile,
    current_config: Dict[str, Any]
) -> Optional[Recommendation]:
    """Recommend prompt strategy change if a different strategy performs better."""
    current_strategy = current_config.get("prompts", {}).get("default_strategy", "baseline")
    preferred_strategy = profile.preferred_strategy

    if not preferred_strategy or preferred_strategy == current_strategy:
        return None

    # Check if both strategies have sufficient data
    if preferred_strategy not in profile.strategies or current_strategy not in profile.strategies:
        return None

    preferred_stats = profile.strategies[preferred_strategy]
    current_stats = profile.strategies[current_strategy]

    # Need minimum sample size for both
    if preferred_stats.runs_count < 3 or current_stats.runs_count < 3:
        return None

    # Compare QA and cost
    qa_diff = preferred_stats.qa_pass_rate - current_stats.qa_pass_rate

    cost_diff_pct = 0
    if current_stats.median_cost > 0:
        cost_diff_pct = (current_stats.median_cost - preferred_stats.median_cost) / current_stats.median_cost * 100

    # Only recommend if preferred strategy has similar or better QA
    if qa_diff < -0.05:
        return None

    # Build explanation
    if qa_diff >= 0.05 and cost_diff_pct > 10:
        explanation = (
            f"Strategy '{preferred_strategy}' has {preferred_stats.qa_pass_rate:.0%} QA pass rate "
            f"({qa_diff:+.0%} better) and {cost_diff_pct:.0f}% lower cost "
            f"based on {preferred_stats.runs_count} runs"
        )
        confidence = "high"
        impact = f"{qa_diff:+.0%} QA, {cost_diff_pct:.0f}% cost reduction"
    elif cost_diff_pct > 20:
        explanation = (
            f"Strategy '{preferred_strategy}' has similar QA but {cost_diff_pct:.0f}% lower cost "
            f"based on {preferred_stats.runs_count} runs"
        )
        confidence = "high"
        impact = f"{cost_diff_pct:.0f}% cost reduction"
    else:
        return None

    return Recommendation(
        category="strategy",
        current_value=current_strategy,
        recommended_value=preferred_strategy,
        explanation=explanation,
        confidence=confidence,
        estimated_impact=impact
    )


def apply_auto_tune(
    config: Dict[str, Any],
    recommendations: List[Recommendation],
    tuning_config: Optional[TuningConfig] = None
) -> Dict[str, Any]:
    """
    Apply recommendations to configuration.

    Args:
        config: Current configuration dict
        recommendations: List of recommendations to apply
        tuning_config: Tuning configuration (for safety settings)

    Returns:
        New configuration dict with recommendations applied
    """
    if tuning_config is None:
        tuning_config = load_tuning_config()

    # Create a copy to avoid mutating original
    tuned_config = config.copy()

    # Track what was tuned for logging
    tuned_fields = []

    for rec in recommendations:
        # Skip low-confidence recommendations in safe mode
        if tuning_config.apply_safely and rec.confidence == "low":
            continue

        # Apply based on category
        if rec.category == "mode":
            tuned_config["mode"] = rec.recommended_value
            tuned_fields.append(f"mode={rec.recommended_value}")

        elif rec.category == "rounds":
            tuned_config["max_rounds"] = rec.recommended_value
            tuned_fields.append(f"max_rounds={rec.recommended_value}")

        elif rec.category == "cost":
            tuned_config["max_cost_usd"] = rec.recommended_value
            tuned_fields.append(f"max_cost_usd={rec.recommended_value}")

        elif rec.category == "strategy":
            if "prompts" not in tuned_config:
                tuned_config["prompts"] = {}
            tuned_config["prompts"]["default_strategy"] = rec.recommended_value
            tuned_fields.append(f"strategy={rec.recommended_value}")

    # Add metadata about tuning
    tuned_config["_auto_tuned"] = True
    tuned_config["_tuned_fields"] = tuned_fields

    return tuned_config


# ══════════════════════════════════════════════════════════════════════
# Configuration Loading
# ══════════════════════════════════════════════════════════════════════


def load_tuning_config() -> TuningConfig:
    """
    Load auto-tune configuration from project_config.json.

    Returns:
        TuningConfig with defaults if not configured
    """
    agent_dir = Path(__file__).resolve().parent
    config_file = agent_dir / "project_config.json"

    defaults = TuningConfig()

    if not config_file.exists():
        return defaults

    try:
        with config_file.open("r", encoding="utf-8") as f:
            config = json.load(f)
            auto_tune_config = config.get("auto_tune", {})

            return TuningConfig(
                enabled=auto_tune_config.get("enabled", defaults.enabled),
                apply_safely=auto_tune_config.get("apply_safely", defaults.apply_safely),
                min_runs_for_recommendations=auto_tune_config.get(
                    "min_runs_for_recommendations",
                    defaults.min_runs_for_recommendations
                ),
                confidence_threshold=auto_tune_config.get(
                    "confidence_threshold",
                    defaults.confidence_threshold
                ),
            )
    except Exception:
        return defaults


def get_available_strategies() -> Dict[str, Dict[str, str]]:
    """
    Get available prompt strategies from configuration.

    Returns:
        Dict mapping strategy names to their configuration
    """
    agent_dir = Path(__file__).resolve().parent
    config_file = agent_dir / "project_config.json"

    defaults = {
        "baseline": {
            "file": "prompts_default.json",
            "description": "Default prompts"
        }
    }

    if not config_file.exists():
        return defaults

    try:
        with config_file.open("r", encoding="utf-8") as f:
            config = json.load(f)
            prompts_config = config.get("prompts", {})
            strategies = prompts_config.get("strategies", defaults)
            return strategies
    except Exception:
        return defaults


# ══════════════════════════════════════════════════════════════════════
# Main API
# ══════════════════════════════════════════════════════════════════════


def get_tuning_analysis(project_id: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get complete tuning analysis for a project.

    This is the main entry point for the self-optimization system.

    Args:
        project_id: Project identifier
        current_config: Current project configuration

    Returns:
        Dict with:
        - profile: ProjectProfile (as dict)
        - recommendations: List[Recommendation] (as dicts)
        - tuning_config: TuningConfig (as dict)
        - available_strategies: Dict of available prompt strategies
    """
    # Build profile
    profile = build_project_profile(project_id)

    # Generate recommendations
    recommendations = generate_recommendations(profile, current_config)

    # Load tuning config
    tuning_config = load_tuning_config()

    # Get available strategies
    strategies = get_available_strategies()

    return {
        "profile": asdict(profile),
        "recommendations": [asdict(r) for r in recommendations],
        "tuning_config": asdict(tuning_config),
        "available_strategies": strategies,
    }
