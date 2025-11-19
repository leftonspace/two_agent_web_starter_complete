"""
PHASE 5.2: Self-Refinement - Autonomous Improvement Loop

Enables the system to learn from mission outcomes and continuously improve:
- Performance tracking and trend analysis
- Automatic parameter tuning
- Prompt refinement suggestions
- Cost optimization recommendations
- Success pattern identification

Usage:
    >>> from agent import self_refinement
    >>> refiner = self_refinement.SelfRefiner()
    >>> improvements = refiner.suggest_improvements()
    >>> for imp in improvements:
    ...     print(f"{imp['area']}: {imp['suggestion']}")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local imports
try:
    import knowledge_graph
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False

try:
    import project_stats
    STATS_AVAILABLE = True
except ImportError:
    STATS_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Improvement Areas
# ══════════════════════════════════════════════════════════════════════


class ImprovementArea(str, Enum):
    """Areas where improvements can be made."""
    PROMPTS = "prompts"
    PARAMETERS = "parameters"
    SPECIALISTS = "specialists"
    COST_OPTIMIZATION = "cost_optimization"
    ITERATION_EFFICIENCY = "iteration_efficiency"
    DOMAIN_ROUTING = "domain_routing"
    TOOL_USAGE = "tool_usage"


@dataclass
class Improvement:
    """A suggested improvement."""

    area: ImprovementArea
    priority: str  # "high", "medium", "low"
    suggestion: str
    reasoning: List[str]
    expected_impact: str  # "high", "medium", "low"
    implementation_effort: str  # "high", "medium", "low"
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "area": self.area.value,
            "priority": self.priority,
            "suggestion": self.suggestion,
            "reasoning": self.reasoning,
            "expected_impact": self.expected_impact,
            "implementation_effort": self.implementation_effort,
            "metrics": self.metrics,
        }


# ══════════════════════════════════════════════════════════════════════
# Performance Metrics
# ══════════════════════════════════════════════════════════════════════


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""

    total_missions: int = 0
    successful_missions: int = 0
    failed_missions: int = 0
    success_rate: float = 0.0
    average_cost_usd: float = 0.0
    average_iterations: float = 0.0
    total_cost_usd: float = 0.0
    cost_trend: str = "stable"  # "increasing", "decreasing", "stable"
    success_trend: str = "stable"  # "improving", "declining", "stable"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_missions": self.total_missions,
            "successful_missions": self.successful_missions,
            "failed_missions": self.failed_missions,
            "success_rate": self.success_rate,
            "average_cost_usd": self.average_cost_usd,
            "average_iterations": self.average_iterations,
            "total_cost_usd": self.total_cost_usd,
            "cost_trend": self.cost_trend,
            "success_trend": self.success_trend,
        }


# ══════════════════════════════════════════════════════════════════════
# Self-Refinement System
# ══════════════════════════════════════════════════════════════════════


class SelfRefiner:
    """Autonomous improvement system."""

    def __init__(
        self,
        lookback_days: int = 30,
        min_missions_for_analysis: int = 5
    ):
        """
        Initialize self-refiner.

        Args:
            lookback_days: Number of days to analyze for trends
            min_missions_for_analysis: Minimum missions needed for meaningful analysis
        """
        self.lookback_days = lookback_days
        self.min_missions_for_analysis = min_missions_for_analysis

        # Historical data
        self.mission_history: List[Dict[str, Any]] = []
        self.performance_metrics: Optional[PerformanceMetrics] = None

        # Load historical data
        if KG_AVAILABLE:
            self._load_history()
            self._calculate_metrics()

    def _load_history(self) -> None:
        """Load mission history from knowledge graph."""
        if not KG_AVAILABLE:
            return

        try:
            kg = knowledge_graph.KnowledgeGraph()

            # Calculate cutoff date
            cutoff = datetime.utcnow() - timedelta(days=self.lookback_days)

            # Get recent missions
            all_missions = kg.get_mission_history(limit=1000)

            # Filter by date
            self.mission_history = [
                m for m in all_missions
                if self._parse_timestamp(m.get("created_at")) >= cutoff
            ]

        except Exception as e:
            print(f"[Refiner] Warning: Failed to load mission history: {e}")

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse ISO timestamp string."""
        if not timestamp_str:
            return datetime.min

        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    def _calculate_metrics(self) -> None:
        """Calculate performance metrics from history."""
        if not self.mission_history:
            self.performance_metrics = PerformanceMetrics()
            return

        total = len(self.mission_history)
        successes = sum(1 for m in self.mission_history if m.get("status") == "success")
        failures = total - successes

        total_cost = sum(m.get("cost_usd", 0.0) for m in self.mission_history)
        total_iterations = sum(m.get("iterations", 0) for m in self.mission_history)

        success_rate = successes / total if total > 0 else 0.0
        avg_cost = total_cost / total if total > 0 else 0.0
        avg_iterations = total_iterations / total if total > 0 else 0.0

        # Calculate trends (compare first half vs second half)
        mid_point = len(self.mission_history) // 2
        if mid_point > 0:
            first_half = self.mission_history[:mid_point]
            second_half = self.mission_history[mid_point:]

            first_success_rate = sum(1 for m in first_half if m.get("status") == "success") / len(first_half)
            second_success_rate = sum(1 for m in second_half if m.get("status") == "success") / len(second_half)

            first_avg_cost = sum(m.get("cost_usd", 0.0) for m in first_half) / len(first_half)
            second_avg_cost = sum(m.get("cost_usd", 0.0) for m in second_half) / len(second_half)

            # Determine trends
            if second_success_rate > first_success_rate * 1.1:
                success_trend = "improving"
            elif second_success_rate < first_success_rate * 0.9:
                success_trend = "declining"
            else:
                success_trend = "stable"

            if second_avg_cost > first_avg_cost * 1.1:
                cost_trend = "increasing"
            elif second_avg_cost < first_avg_cost * 0.9:
                cost_trend = "decreasing"
            else:
                cost_trend = "stable"
        else:
            success_trend = "stable"
            cost_trend = "stable"

        self.performance_metrics = PerformanceMetrics(
            total_missions=total,
            successful_missions=successes,
            failed_missions=failures,
            success_rate=success_rate,
            average_cost_usd=avg_cost,
            average_iterations=avg_iterations,
            total_cost_usd=total_cost,
            cost_trend=cost_trend,
            success_trend=success_trend,
        )

    def suggest_improvements(self) -> List[Improvement]:
        """
        Analyze performance and suggest improvements.

        Returns:
            List of Improvement suggestions
        """
        improvements: List[Improvement] = []

        if not self.performance_metrics:
            return improvements

        if self.performance_metrics.total_missions < self.min_missions_for_analysis:
            return [
                Improvement(
                    area=ImprovementArea.PARAMETERS,
                    priority="low",
                    suggestion="Collect more mission data before making improvement recommendations.",
                    reasoning=[
                        f"Only {self.performance_metrics.total_missions} missions analyzed, "
                        f"need at least {self.min_missions_for_analysis} for meaningful insights"
                    ],
                    expected_impact="low",
                    implementation_effort="low",
                )
            ]

        # Analyze success rate
        if self.performance_metrics.success_rate < 0.7:
            improvements.append(
                Improvement(
                    area=ImprovementArea.PROMPTS,
                    priority="high",
                    suggestion="Improve system prompts to increase success rate.",
                    reasoning=[
                        f"Current success rate: {self.performance_metrics.success_rate * 100:.1f}%",
                        "Target: 70%+",
                        "Consider refining prompts for clearer instructions and better error handling"
                    ],
                    expected_impact="high",
                    implementation_effort="medium",
                    metrics={"current_success_rate": self.performance_metrics.success_rate},
                )
            )

        # Analyze cost
        if self.performance_metrics.average_cost_usd > 10.0:
            improvements.append(
                Improvement(
                    area=ImprovementArea.COST_OPTIMIZATION,
                    priority="high",
                    suggestion="Optimize costs by using cheaper models or reducing iterations.",
                    reasoning=[
                        f"Average cost per mission: ${self.performance_metrics.average_cost_usd:.2f}",
                        "Target: <$10.00",
                        "Consider using smaller models for simple tasks or implementing better early stopping"
                    ],
                    expected_impact="high",
                    implementation_effort="medium",
                    metrics={"average_cost_usd": self.performance_metrics.average_cost_usd},
                )
            )

        # Analyze cost trend
        if self.performance_metrics.cost_trend == "increasing":
            improvements.append(
                Improvement(
                    area=ImprovementArea.COST_OPTIMIZATION,
                    priority="high",
                    suggestion="Costs are trending upward - investigate and address root cause.",
                    reasoning=[
                        "Cost per mission is increasing over time",
                        "Possible causes: more complex tasks, inefficient iterations, or model selection issues"
                    ],
                    expected_impact="high",
                    implementation_effort="low",
                    metrics={"cost_trend": self.performance_metrics.cost_trend},
                )
            )

        # Analyze success trend
        if self.performance_metrics.success_trend == "declining":
            improvements.append(
                Improvement(
                    area=ImprovementArea.PROMPTS,
                    priority="high",
                    suggestion="Success rate is declining - review recent changes and mission patterns.",
                    reasoning=[
                        "Success rate decreasing over time",
                        "Review recent prompt changes, model updates, or task complexity increases"
                    ],
                    expected_impact="high",
                    implementation_effort="low",
                    metrics={"success_trend": self.performance_metrics.success_trend},
                )
            )

        # Analyze iterations
        if self.performance_metrics.average_iterations > 5.0:
            improvements.append(
                Improvement(
                    area=ImprovementArea.ITERATION_EFFICIENCY,
                    priority="medium",
                    suggestion="Reduce average iterations through better initial planning or convergence criteria.",
                    reasoning=[
                        f"Average iterations: {self.performance_metrics.average_iterations:.1f}",
                        "Target: <5 iterations",
                        "High iteration counts suggest planning or execution inefficiencies"
                    ],
                    expected_impact="medium",
                    implementation_effort="medium",
                    metrics={"average_iterations": self.performance_metrics.average_iterations},
                )
            )

        # Domain-specific analysis
        domain_improvements = self._analyze_by_domain()
        improvements.extend(domain_improvements)

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        improvements.sort(key=lambda x: priority_order.get(x.priority, 3))

        return improvements

    def _analyze_by_domain(self) -> List[Improvement]:
        """Analyze performance by domain and suggest domain-specific improvements."""
        improvements: List[Improvement] = []

        if not self.mission_history:
            return improvements

        # Group missions by domain
        domain_stats: Dict[str, Dict[str, Any]] = {}

        for mission in self.mission_history:
            domain = mission.get("domain", "unknown")
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "total": 0,
                    "successes": 0,
                    "total_cost": 0.0,
                }

            domain_stats[domain]["total"] += 1
            if mission.get("status") == "success":
                domain_stats[domain]["successes"] += 1
            domain_stats[domain]["total_cost"] += mission.get("cost_usd", 0.0)

        # Analyze each domain
        for domain, stats in domain_stats.items():
            if stats["total"] < 3:  # Need at least 3 missions
                continue

            success_rate = stats["successes"] / stats["total"]
            avg_cost = stats["total_cost"] / stats["total"]

            if success_rate < 0.6:
                improvements.append(
                    Improvement(
                        area=ImprovementArea.DOMAIN_ROUTING,
                        priority="medium",
                        suggestion=f"Improve {domain} domain performance through specialized prompts or specialists.",
                        reasoning=[
                            f"{domain} domain success rate: {success_rate * 100:.1f}%",
                            f"Based on {stats['total']} missions",
                            "Consider domain-specific prompt tuning or specialist selection"
                        ],
                        expected_impact="medium",
                        implementation_effort="medium",
                        metrics={"domain": domain, "success_rate": success_rate},
                    )
                )

        return improvements

    def generate_refinement_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive refinement report.

        Returns:
            Dict with metrics, trends, and improvement suggestions
        """
        improvements = self.suggest_improvements()

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lookback_days": self.lookback_days,
            "performance_metrics": self.performance_metrics.to_dict() if self.performance_metrics else {},
            "total_improvements": len(improvements),
            "high_priority_improvements": sum(1 for i in improvements if i.priority == "high"),
            "improvements": [i.to_dict() for i in improvements],
        }

    def track_improvement_impact(
        self,
        improvement: Improvement,
        before_metrics: PerformanceMetrics,
        after_metrics: PerformanceMetrics
    ) -> Dict[str, Any]:
        """
        Track the impact of an implemented improvement.

        Args:
            improvement: The improvement that was implemented
            before_metrics: Metrics before implementation
            after_metrics: Metrics after implementation

        Returns:
            Dict with impact analysis
        """
        impact = {
            "improvement": improvement.to_dict(),
            "before": before_metrics.to_dict(),
            "after": after_metrics.to_dict(),
            "changes": {},
        }

        # Calculate changes
        if before_metrics.total_missions > 0:
            impact["changes"]["success_rate_change"] = (
                after_metrics.success_rate - before_metrics.success_rate
            )
            impact["changes"]["cost_change_pct"] = (
                (after_metrics.average_cost_usd - before_metrics.average_cost_usd)
                / before_metrics.average_cost_usd * 100
                if before_metrics.average_cost_usd > 0 else 0
            )
            impact["changes"]["iteration_change"] = (
                after_metrics.average_iterations - before_metrics.average_iterations
            )

        # Assess effectiveness
        if improvement.area == ImprovementArea.COST_OPTIMIZATION:
            if after_metrics.average_cost_usd < before_metrics.average_cost_usd:
                impact["effectiveness"] = "positive"
            else:
                impact["effectiveness"] = "negative"
        elif improvement.area == ImprovementArea.PROMPTS:
            if after_metrics.success_rate > before_metrics.success_rate:
                impact["effectiveness"] = "positive"
            else:
                impact["effectiveness"] = "negative"
        else:
            impact["effectiveness"] = "unknown"

        return impact


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for self-refinement."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Self-Refinement - Autonomous Improvement Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest improvements")
    suggest_parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate refinement report")
    report_parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    report_parser.add_argument("--output", type=str, help="Output file path (JSON)")

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show performance metrics")
    metrics_parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "suggest":
        refiner = SelfRefiner(lookback_days=args.days)
        improvements = refiner.suggest_improvements()

        if not improvements:
            print("\nNo improvements suggested. System performing well!")
            return

        print(f"\nSuggested Improvements (last {args.days} days)\n")
        for i, imp in enumerate(improvements, 1):
            print(f"{i}. [{imp.priority.upper()}] {imp.area.value.upper()}")
            print(f"   Suggestion: {imp.suggestion}")
            print(f"   Expected Impact: {imp.expected_impact}")
            print(f"   Implementation Effort: {imp.implementation_effort}")
            print(f"   Reasoning:")
            for reason in imp.reasoning:
                print(f"     - {reason}")
            print()

    elif args.command == "report":
        refiner = SelfRefiner(lookback_days=args.days)
        report = refiner.generate_refinement_report()

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"\nRefinement report saved to: {output_path}")
        else:
            print("\nRefinement Report\n")
            print(json.dumps(report, indent=2))

    elif args.command == "metrics":
        refiner = SelfRefiner(lookback_days=args.days)

        if not refiner.performance_metrics:
            print("\nNo performance metrics available")
            return

        metrics = refiner.performance_metrics

        print(f"\nPerformance Metrics (last {args.days} days)\n")
        print(f"Total Missions: {metrics.total_missions}")
        print(f"Successful: {metrics.successful_missions}")
        print(f"Failed: {metrics.failed_missions}")
        print(f"Success Rate: {metrics.success_rate * 100:.1f}%")
        print(f"Average Cost: ${metrics.average_cost_usd:.2f}")
        print(f"Average Iterations: {metrics.average_iterations:.1f}")
        print(f"Total Cost: ${metrics.total_cost_usd:.2f}")
        print(f"\nTrends:")
        print(f"  Success: {metrics.success_trend}")
        print(f"  Cost: {metrics.cost_trend}")


if __name__ == "__main__":
    main()
