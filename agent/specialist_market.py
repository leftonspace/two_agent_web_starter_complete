"""
PHASE 4.2: Specialist Marketplace

Provides a marketplace for discovering and selecting specialist agents:
- Agent discovery based on task requirements
- Performance tracking and recommendations
- Cost estimation and budget checking
- Specialist assignment optimization
- Historical success rate analysis

Usage:
    >>> from agent import specialist_market
    >>> market = specialist_market.SpecialistMarket()
    >>> recommendation = market.recommend_specialist(
    ...     task="Build a React dashboard with authentication",
    ...     budget_usd=10.0
    ... )
    >>> print(f"Best specialist: {recommendation['specialist'].name}")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local imports
try:
    import specialists
    SPECIALISTS_AVAILABLE = True
except ImportError:
    SPECIALISTS_AVAILABLE = False

try:
    import knowledge_graph
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False

try:
    import config as config_module
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Performance Tracking
# ══════════════════════════════════════════════════════════════════════


@dataclass
class SpecialistPerformance:
    """Performance metrics for a specialist."""

    specialist_type: str
    total_missions: int = 0
    successful_missions: int = 0
    failed_missions: int = 0
    total_cost_usd: float = 0.0
    average_duration_seconds: float = 0.0
    success_rate: float = 0.0
    average_cost_usd: float = 0.0
    last_used: Optional[datetime] = None

    def update_from_mission(
        self,
        success: bool,
        cost_usd: float,
        duration_seconds: float
    ) -> None:
        """Update performance metrics from a mission result."""
        self.total_missions += 1
        if success:
            self.successful_missions += 1
        else:
            self.failed_missions += 1

        self.total_cost_usd += cost_usd

        # Update rolling average for duration
        if self.total_missions == 1:
            self.average_duration_seconds = duration_seconds
        else:
            self.average_duration_seconds = (
                (self.average_duration_seconds * (self.total_missions - 1) + duration_seconds)
                / self.total_missions
            )

        # Calculate success rate
        self.success_rate = self.successful_missions / self.total_missions

        # Calculate average cost
        self.average_cost_usd = self.total_cost_usd / self.total_missions

        self.last_used = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "specialist_type": self.specialist_type,
            "total_missions": self.total_missions,
            "successful_missions": self.successful_missions,
            "failed_missions": self.failed_missions,
            "total_cost_usd": self.total_cost_usd,
            "average_duration_seconds": self.average_duration_seconds,
            "success_rate": self.success_rate,
            "average_cost_usd": self.average_cost_usd,
            "last_used": self.last_used.isoformat() + "Z" if self.last_used else None,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> SpecialistPerformance:
        """Create from dictionary."""
        last_used_str = data.get("last_used")
        last_used = None
        if last_used_str:
            last_used = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))

        return SpecialistPerformance(
            specialist_type=data["specialist_type"],
            total_missions=data.get("total_missions", 0),
            successful_missions=data.get("successful_missions", 0),
            failed_missions=data.get("failed_missions", 0),
            total_cost_usd=data.get("total_cost_usd", 0.0),
            average_duration_seconds=data.get("average_duration_seconds", 0.0),
            success_rate=data.get("success_rate", 0.0),
            average_cost_usd=data.get("average_cost_usd", 0.0),
            last_used=last_used,
        )


# ══════════════════════════════════════════════════════════════════════
# Specialist Recommendation
# ══════════════════════════════════════════════════════════════════════


@dataclass
class SpecialistRecommendation:
    """A recommendation for a specialist agent."""

    specialist: Any  # SpecialistProfile from specialists.py
    match_score: float  # 0.0 to 1.0 based on task keywords
    performance_score: float  # 0.0 to 1.0 based on historical performance
    cost_score: float  # 0.0 to 1.0 based on cost efficiency
    overall_score: float  # Weighted combination
    estimated_cost_usd: float  # Estimated mission cost
    estimated_duration_seconds: float  # Estimated duration
    confidence: str  # "high", "medium", "low"
    reasoning: List[str]  # Human-readable explanation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "specialist_type": self.specialist.specialist_type.value,
            "specialist_name": self.specialist.name,
            "match_score": self.match_score,
            "performance_score": self.performance_score,
            "cost_score": self.cost_score,
            "overall_score": self.overall_score,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


# ══════════════════════════════════════════════════════════════════════
# Specialist Market
# ══════════════════════════════════════════════════════════════════════


class SpecialistMarket:
    """Marketplace for discovering and selecting specialist agents."""

    def __init__(
        self,
        performance_cache_path: Optional[Path] = None,
        use_knowledge_graph: bool = True
    ):
        """
        Initialize specialist market.

        Args:
            performance_cache_path: Path to cache performance data (default: data/specialist_performance.json)
            use_knowledge_graph: Whether to use knowledge graph for performance tracking
        """
        if performance_cache_path is None:
            performance_cache_path = Path(__file__).resolve().parent.parent / "data" / "specialist_performance.json"

        self.performance_cache_path = performance_cache_path
        self.use_knowledge_graph = use_knowledge_graph and KG_AVAILABLE

        # Load or initialize performance data
        self.performance: Dict[str, SpecialistPerformance] = {}
        self._load_performance()

    def _load_performance(self) -> None:
        """Load performance data from cache or knowledge graph."""
        # Try loading from cache first
        if self.performance_cache_path.exists():
            try:
                with open(self.performance_cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for spec_type, perf_data in data.items():
                        self.performance[spec_type] = SpecialistPerformance.from_dict(perf_data)
            except Exception as e:
                print(f"[Market] Warning: Could not load performance cache: {e}")

        # Update from knowledge graph if available
        if self.use_knowledge_graph:
            self._update_from_knowledge_graph()

    def _update_from_knowledge_graph(self) -> None:
        """Update performance metrics from knowledge graph."""
        if not KG_AVAILABLE:
            return

        kg = knowledge_graph.KnowledgeGraph()

        # Get all missions from knowledge graph
        missions = kg.get_mission_history(limit=1000)

        # Group by specialist type and calculate metrics
        specialist_missions: Dict[str, List[Dict]] = {}

        for mission in missions:
            metadata = mission.get("metadata", {})
            specialist_type = metadata.get("specialist_type")

            if not specialist_type:
                continue

            if specialist_type not in specialist_missions:
                specialist_missions[specialist_type] = []

            specialist_missions[specialist_type].append(mission)

        # Calculate performance for each specialist
        for spec_type, missions in specialist_missions.items():
            if spec_type not in self.performance:
                self.performance[spec_type] = SpecialistPerformance(specialist_type=spec_type)

            perf = self.performance[spec_type]

            for mission in missions:
                success = mission.get("status") == "success"
                cost_usd = mission.get("cost_usd", 0.0)
                duration_seconds = mission.get("duration_seconds", 0.0)

                perf.update_from_mission(success, cost_usd, duration_seconds)

    def _save_performance(self) -> None:
        """Save performance data to cache."""
        try:
            self.performance_cache_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                spec_type: perf.to_dict()
                for spec_type, perf in self.performance.items()
            }

            with open(self.performance_cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Market] Warning: Could not save performance cache: {e}")

    def recommend_specialist(
        self,
        task: str,
        budget_usd: Optional[float] = None,
        max_duration_seconds: Optional[int] = None,
        prefer_performance: bool = True,
        min_confidence: str = "low"
    ) -> Optional[SpecialistRecommendation]:
        """
        Recommend the best specialist for a task.

        Args:
            task: Task description
            budget_usd: Maximum budget in USD (None = no limit)
            max_duration_seconds: Maximum duration in seconds (None = no limit)
            prefer_performance: Weight performance over cost
            min_confidence: Minimum confidence level ("high", "medium", "low")

        Returns:
            SpecialistRecommendation or None if no suitable specialist found
        """
        if not SPECIALISTS_AVAILABLE:
            print("[Market] Error: specialists module not available")
            return None

        # Get all specialists
        all_specialists = specialists.list_all_specialists()

        # Calculate scores for each specialist
        recommendations: List[SpecialistRecommendation] = []

        for specialist in all_specialists:
            # Skip generic specialist for recommendations
            if specialist.specialist_type == specialists.SpecialistType.GENERIC:
                continue

            # Calculate match score (keyword/expertise matching)
            match_score = specialist.matches_task(task)

            # Get performance data
            spec_type = specialist.specialist_type.value
            perf = self.performance.get(spec_type, SpecialistPerformance(specialist_type=spec_type))

            # Calculate performance score
            if perf.total_missions > 0:
                # Use success rate, with bonus for more missions (more confidence)
                performance_score = perf.success_rate

                # Add confidence bonus (up to +0.1 for 10+ missions)
                confidence_bonus = min(perf.total_missions / 100.0, 0.1)
                performance_score = min(performance_score + confidence_bonus, 1.0)
            else:
                # No history - neutral score
                performance_score = 0.5

            # Calculate cost score (inverse of cost multiplier and average cost)
            if perf.total_missions > 0 and perf.average_cost_usd > 0:
                # Lower cost = higher score
                # Normalize to 0-1 range (assume $100 is max reasonable cost)
                cost_score = max(0.0, 1.0 - (perf.average_cost_usd / 100.0))
            else:
                # Use cost multiplier inverse
                cost_score = max(0.0, 1.0 - (specialist.cost_multiplier - 1.0))

            # Calculate overall score (weighted combination)
            if prefer_performance:
                overall_score = (
                    match_score * 0.4 +
                    performance_score * 0.4 +
                    cost_score * 0.2
                )
            else:
                overall_score = (
                    match_score * 0.4 +
                    performance_score * 0.3 +
                    cost_score * 0.3
                )

            # Estimate cost and duration
            if perf.total_missions > 0:
                estimated_cost_usd = perf.average_cost_usd * specialist.cost_multiplier
                estimated_duration_seconds = perf.average_duration_seconds
            else:
                # Estimate based on typical mission cost
                estimated_cost_usd = 5.0 * specialist.cost_multiplier
                estimated_duration_seconds = 300.0  # 5 minutes default

            # Check budget constraint
            if budget_usd is not None and estimated_cost_usd > budget_usd:
                continue

            # Check duration constraint
            if max_duration_seconds is not None and estimated_duration_seconds > max_duration_seconds:
                continue

            # Determine confidence
            if perf.total_missions >= 10 and perf.success_rate >= 0.8:
                confidence = "high"
            elif perf.total_missions >= 3 and perf.success_rate >= 0.6:
                confidence = "medium"
            else:
                confidence = "low"

            # Skip if below minimum confidence
            confidence_levels = {"low": 0, "medium": 1, "high": 2}
            if confidence_levels[confidence] < confidence_levels[min_confidence]:
                continue

            # Build reasoning
            reasoning = []
            reasoning.append(f"Task match score: {match_score:.2f} (keyword/expertise matching)")

            if perf.total_missions > 0:
                reasoning.append(
                    f"Historical performance: {perf.successful_missions}/{perf.total_missions} "
                    f"successful missions ({perf.success_rate * 100:.1f}%)"
                )
                reasoning.append(f"Average cost: ${perf.average_cost_usd:.2f} per mission")
            else:
                reasoning.append("No historical data available (first-time use)")

            reasoning.append(f"Cost multiplier: {specialist.cost_multiplier}x")
            reasoning.append(f"Estimated cost: ${estimated_cost_usd:.2f}")

            # Create recommendation
            rec = SpecialistRecommendation(
                specialist=specialist,
                match_score=match_score,
                performance_score=performance_score,
                cost_score=cost_score,
                overall_score=overall_score,
                estimated_cost_usd=estimated_cost_usd,
                estimated_duration_seconds=estimated_duration_seconds,
                confidence=confidence,
                reasoning=reasoning,
            )

            recommendations.append(rec)

        # Sort by overall score descending
        recommendations.sort(key=lambda r: r.overall_score, reverse=True)

        # Return best recommendation
        return recommendations[0] if recommendations else None

    def get_all_recommendations(
        self,
        task: str,
        budget_usd: Optional[float] = None,
        max_duration_seconds: Optional[int] = None,
        limit: int = 3
    ) -> List[SpecialistRecommendation]:
        """
        Get multiple specialist recommendations for a task.

        Args:
            task: Task description
            budget_usd: Maximum budget in USD (None = no limit)
            max_duration_seconds: Maximum duration in seconds (None = no limit)
            limit: Maximum number of recommendations to return

        Returns:
            List of SpecialistRecommendation, sorted by overall score
        """
        if not SPECIALISTS_AVAILABLE:
            return []

        # Use recommend_specialist logic but return multiple
        all_specialists = specialists.list_all_specialists()
        recommendations: List[SpecialistRecommendation] = []

        for specialist in all_specialists:
            if specialist.specialist_type == specialists.SpecialistType.GENERIC:
                continue

            # Same logic as recommend_specialist
            match_score = specialist.matches_task(task)
            spec_type = specialist.specialist_type.value
            perf = self.performance.get(spec_type, SpecialistPerformance(specialist_type=spec_type))

            if perf.total_missions > 0:
                performance_score = perf.success_rate
                confidence_bonus = min(perf.total_missions / 100.0, 0.1)
                performance_score = min(performance_score + confidence_bonus, 1.0)
            else:
                performance_score = 0.5

            if perf.total_missions > 0 and perf.average_cost_usd > 0:
                cost_score = max(0.0, 1.0 - (perf.average_cost_usd / 100.0))
            else:
                cost_score = max(0.0, 1.0 - (specialist.cost_multiplier - 1.0))

            overall_score = (
                match_score * 0.4 +
                performance_score * 0.4 +
                cost_score * 0.2
            )

            if perf.total_missions > 0:
                estimated_cost_usd = perf.average_cost_usd * specialist.cost_multiplier
                estimated_duration_seconds = perf.average_duration_seconds
            else:
                estimated_cost_usd = 5.0 * specialist.cost_multiplier
                estimated_duration_seconds = 300.0

            if budget_usd is not None and estimated_cost_usd > budget_usd:
                continue

            if max_duration_seconds is not None and estimated_duration_seconds > max_duration_seconds:
                continue

            if perf.total_missions >= 10 and perf.success_rate >= 0.8:
                confidence = "high"
            elif perf.total_missions >= 3 and perf.success_rate >= 0.6:
                confidence = "medium"
            else:
                confidence = "low"

            reasoning = [
                f"Task match score: {match_score:.2f}",
                f"Performance score: {performance_score:.2f}",
                f"Cost score: {cost_score:.2f}",
            ]

            rec = SpecialistRecommendation(
                specialist=specialist,
                match_score=match_score,
                performance_score=performance_score,
                cost_score=cost_score,
                overall_score=overall_score,
                estimated_cost_usd=estimated_cost_usd,
                estimated_duration_seconds=estimated_duration_seconds,
                confidence=confidence,
                reasoning=reasoning,
            )

            recommendations.append(rec)

        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        return recommendations[:limit]

    def record_mission_result(
        self,
        specialist_type: str,
        success: bool,
        cost_usd: float,
        duration_seconds: float
    ) -> None:
        """
        Record a mission result for a specialist.

        Args:
            specialist_type: Specialist type (e.g., "frontend", "backend")
            success: Whether mission succeeded
            cost_usd: Mission cost in USD
            duration_seconds: Mission duration in seconds
        """
        if specialist_type not in self.performance:
            self.performance[specialist_type] = SpecialistPerformance(specialist_type=specialist_type)

        self.performance[specialist_type].update_from_mission(success, cost_usd, duration_seconds)
        self._save_performance()

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of all specialist performance.

        Returns:
            Dictionary with performance metrics for all specialists
        """
        summary = {
            "total_specialists": len(self.performance),
            "specialists": {},
        }

        for spec_type, perf in self.performance.items():
            summary["specialists"][spec_type] = perf.to_dict()

        return summary

    def get_top_performers(self, limit: int = 3) -> List[Tuple[str, SpecialistPerformance]]:
        """
        Get top performing specialists by success rate.

        Args:
            limit: Maximum number of specialists to return

        Returns:
            List of (specialist_type, performance) tuples
        """
        # Filter specialists with at least 3 missions
        qualified = [
            (spec_type, perf)
            for spec_type, perf in self.performance.items()
            if perf.total_missions >= 3
        ]

        # Sort by success rate descending
        qualified.sort(key=lambda x: x[1].success_rate, reverse=True)

        return qualified[:limit]

    def get_cost_leaders(self, limit: int = 3) -> List[Tuple[str, SpecialistPerformance]]:
        """
        Get most cost-efficient specialists.

        Args:
            limit: Maximum number of specialists to return

        Returns:
            List of (specialist_type, performance) tuples
        """
        # Filter specialists with at least 3 missions
        qualified = [
            (spec_type, perf)
            for spec_type, perf in self.performance.items()
            if perf.total_missions >= 3 and perf.average_cost_usd > 0
        ]

        # Sort by average cost ascending (lower is better)
        qualified.sort(key=lambda x: x[1].average_cost_usd)

        return qualified[:limit]


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for specialist market."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Specialist Marketplace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Recommend command
    recommend_parser = subparsers.add_parser("recommend", help="Get specialist recommendation for task")
    recommend_parser.add_argument("task", type=str, help="Task description")
    recommend_parser.add_argument("--budget", type=float, help="Maximum budget in USD")
    recommend_parser.add_argument("--duration", type=int, help="Maximum duration in seconds")
    recommend_parser.add_argument("--all", action="store_true", help="Show all recommendations")

    # Performance command
    subparsers.add_parser("performance", help="Show performance summary")

    # Top performers command
    top_parser = subparsers.add_parser("top", help="Show top performing specialists")
    top_parser.add_argument("--limit", type=int, default=3, help="Number of specialists to show")

    # Cost leaders command
    cost_parser = subparsers.add_parser("cost-leaders", help="Show most cost-efficient specialists")
    cost_parser.add_argument("--limit", type=int, default=3, help="Number of specialists to show")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    market = SpecialistMarket()

    if args.command == "recommend":
        if args.all:
            recommendations = market.get_all_recommendations(
                task=args.task,
                budget_usd=args.budget,
                max_duration_seconds=args.duration,
                limit=5
            )

            if not recommendations:
                print(f"\nNo specialists found for task: {args.task}")
                return

            print(f"\nAll recommendations for task: '{args.task}'\n")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec.specialist.name}")
                print(f"   Type: {rec.specialist.specialist_type.value}")
                print(f"   Overall Score: {rec.overall_score:.2f}")
                print(f"   Match: {rec.match_score:.2f} | Performance: {rec.performance_score:.2f} | Cost: {rec.cost_score:.2f}")
                print(f"   Estimated Cost: ${rec.estimated_cost_usd:.2f}")
                print(f"   Confidence: {rec.confidence}")
                print()
        else:
            rec = market.recommend_specialist(
                task=args.task,
                budget_usd=args.budget,
                max_duration_seconds=args.duration
            )

            if not rec:
                print(f"\nNo suitable specialist found for task: {args.task}")
                return

            print(f"\nBest specialist for task: '{args.task}'\n")
            print(f"Specialist: {rec.specialist.name}")
            print(f"Type: {rec.specialist.specialist_type.value}")
            print(f"Overall Score: {rec.overall_score:.2f}")
            print(f"  - Match Score: {rec.match_score:.2f}")
            print(f"  - Performance Score: {rec.performance_score:.2f}")
            print(f"  - Cost Score: {rec.cost_score:.2f}")
            print(f"\nEstimates:")
            print(f"  - Cost: ${rec.estimated_cost_usd:.2f}")
            print(f"  - Duration: {rec.estimated_duration_seconds:.0f}s ({rec.estimated_duration_seconds / 60:.1f} min)")
            print(f"  - Confidence: {rec.confidence}")
            print(f"\nReasoning:")
            for reason in rec.reasoning:
                print(f"  - {reason}")

    elif args.command == "performance":
        summary = market.get_performance_summary()

        print(f"\nSpecialist Performance Summary\n")
        print(f"Total specialists tracked: {summary['total_specialists']}\n")

        if not summary["specialists"]:
            print("No performance data available yet.")
            return

        for spec_type, perf in summary["specialists"].items():
            print(f"{spec_type.upper()}:")
            print(f"  Missions: {perf['total_missions']} ({perf['successful_missions']} successful, {perf['failed_missions']} failed)")
            print(f"  Success Rate: {perf['success_rate'] * 100:.1f}%")
            print(f"  Average Cost: ${perf['average_cost_usd']:.2f}")
            print(f"  Average Duration: {perf['average_duration_seconds']:.0f}s")
            if perf['last_used']:
                print(f"  Last Used: {perf['last_used']}")
            print()

    elif args.command == "top":
        top_performers = market.get_top_performers(limit=args.limit)

        if not top_performers:
            print("\nNo performance data available yet (need at least 3 missions per specialist).")
            return

        print(f"\nTop {args.limit} Performing Specialists\n")
        for i, (spec_type, perf) in enumerate(top_performers, 1):
            print(f"{i}. {spec_type.upper()}")
            print(f"   Success Rate: {perf.success_rate * 100:.1f}% ({perf.successful_missions}/{perf.total_missions})")
            print(f"   Average Cost: ${perf.average_cost_usd:.2f}")
            print()

    elif args.command == "cost-leaders":
        cost_leaders = market.get_cost_leaders(limit=args.limit)

        if not cost_leaders:
            print("\nNo performance data available yet (need at least 3 missions per specialist).")
            return

        print(f"\nTop {args.limit} Cost-Efficient Specialists\n")
        for i, (spec_type, perf) in enumerate(cost_leaders, 1):
            print(f"{i}. {spec_type.upper()}")
            print(f"   Average Cost: ${perf.average_cost_usd:.2f}")
            print(f"   Success Rate: {perf.success_rate * 100:.1f}% ({perf.successful_missions}/{perf.total_missions})")
            print()


if __name__ == "__main__":
    main()
