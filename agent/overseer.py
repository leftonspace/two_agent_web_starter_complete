"""
PHASE 5.1: Overseer - Meta-Orchestration System

Provides high-level coordination and strategic guidance for orchestrator:
- Mission monitoring and intervention
- Multi-mission coordination
- Resource allocation optimization
- Strategic planning and goal decomposition
- Performance trend analysis

Usage:
    >>> from agent import overseer
    >>> os = overseer.Overseer()
    >>> intervention = os.analyze_mission_progress(
    ...     mission_data={"status": "in_progress", "cost_usd": 15.0, "iterations": 5}
    ... )
    >>> if intervention["should_intervene"]:
    ...     print(f"Intervention: {intervention['recommendation']}")
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

try:
    import specialist_market
    MARKET_AVAILABLE = True
except ImportError:
    MARKET_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Mission Health
# ══════════════════════════════════════════════════════════════════════


class MissionHealth(str, Enum):
    """Mission health status."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class MissionDiagnostics:
    """Diagnostic information for a mission."""

    mission_id: str
    health: MissionHealth
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mission_id": self.mission_id,
            "health": self.health.value,
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "metrics": self.metrics,
        }


# ══════════════════════════════════════════════════════════════════════
# Intervention Strategy
# ══════════════════════════════════════════════════════════════════════


class InterventionType(str, Enum):
    """Types of overseer interventions."""
    NONE = "none"
    ADJUST_PARAMETERS = "adjust_parameters"
    CHANGE_STRATEGY = "change_strategy"
    ABORT_MISSION = "abort_mission"
    REQUEST_SPECIALIST = "request_specialist"
    INCREASE_BUDGET = "increase_budget"
    REDUCE_SCOPE = "reduce_scope"


@dataclass
class Intervention:
    """An intervention recommendation from the overseer."""

    intervention_type: InterventionType
    should_intervene: bool
    urgency: str  # "low", "medium", "high"
    recommendation: str
    reasoning: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intervention_type": self.intervention_type.value,
            "should_intervene": self.should_intervene,
            "urgency": self.urgency,
            "recommendation": self.recommendation,
            "reasoning": self.reasoning,
            "parameters": self.parameters,
        }


# ══════════════════════════════════════════════════════════════════════
# Overseer System
# ══════════════════════════════════════════════════════════════════════


class Overseer:
    """Meta-orchestration system for high-level mission management."""

    def __init__(
        self,
        use_knowledge_graph: bool = True,
        intervention_threshold: float = 0.7
    ):
        """
        Initialize overseer.

        Args:
            use_knowledge_graph: Whether to use knowledge graph for historical analysis
            intervention_threshold: Confidence threshold for interventions (0.0-1.0)
        """
        self.use_knowledge_graph = use_knowledge_graph and KG_AVAILABLE
        self.intervention_threshold = intervention_threshold

        # Historical mission data
        self.mission_history: List[Dict[str, Any]] = []

        # Load historical data if available
        if self.use_knowledge_graph:
            self._load_history()

    def _load_history(self) -> None:
        """Load mission history from knowledge graph."""
        if not KG_AVAILABLE:
            return

        try:
            kg = knowledge_graph.KnowledgeGraph()
            self.mission_history = kg.get_mission_history(limit=100)
        except Exception as e:
            print(f"[Overseer] Warning: Failed to load mission history: {e}")

    def analyze_mission_progress(
        self,
        mission_data: Dict[str, Any]
    ) -> Intervention:
        """
        Analyze current mission progress and recommend interventions.

        Args:
            mission_data: Current mission data with keys:
                - status: "in_progress", "completed", "failed"
                - cost_usd: Current cost
                - iterations: Number of iterations
                - max_iterations: Maximum allowed iterations
                - budget_usd: Total budget (optional)

        Returns:
            Intervention recommendation
        """
        reasoning: List[str] = []
        issues: List[str] = []

        # Extract mission metrics
        status = mission_data.get("status", "unknown")
        cost_usd = mission_data.get("cost_usd", 0.0)
        iterations = mission_data.get("iterations", 0)
        max_iterations = mission_data.get("max_iterations", 10)
        budget_usd = mission_data.get("budget_usd")

        # Analyze cost
        if budget_usd and cost_usd > budget_usd * 0.9:
            issues.append(f"Cost ${cost_usd:.2f} approaching budget ${budget_usd:.2f}")
            reasoning.append("Mission is near budget limit")

        # Analyze iterations
        iteration_ratio = iterations / max_iterations if max_iterations > 0 else 0
        if iteration_ratio > 0.8:
            issues.append(f"Iterations {iterations}/{max_iterations} near limit")
            reasoning.append("Mission using most available iterations")

        # Determine intervention
        if budget_usd and cost_usd >= budget_usd:
            # Budget exceeded - abort or request more budget
            return Intervention(
                intervention_type=InterventionType.ABORT_MISSION,
                should_intervene=True,
                urgency="high",
                recommendation="Mission has exceeded budget. Consider aborting or requesting budget increase.",
                reasoning=reasoning + ["Budget limit reached"],
            )

        if iteration_ratio >= 1.0:
            # Max iterations reached
            return Intervention(
                intervention_type=InterventionType.ABORT_MISSION,
                should_intervene=True,
                urgency="high",
                recommendation="Mission reached maximum iterations without completion.",
                reasoning=reasoning + ["Iteration limit reached"],
            )

        if iteration_ratio > 0.7 and status != "completed":
            # Approaching iteration limit
            return Intervention(
                intervention_type=InterventionType.REDUCE_SCOPE,
                should_intervene=True,
                urgency="medium",
                recommendation="Mission approaching iteration limit. Consider reducing scope or adjusting strategy.",
                reasoning=reasoning + ["High iteration usage without completion"],
            )

        if cost_usd > 0 and iterations > 0:
            # Check cost per iteration
            cost_per_iteration = cost_usd / iterations
            if cost_per_iteration > 5.0:  # $5 per iteration is expensive
                return Intervention(
                    intervention_type=InterventionType.CHANGE_STRATEGY,
                    should_intervene=True,
                    urgency="medium",
                    recommendation=f"High cost per iteration (${cost_per_iteration:.2f}). Consider using cheaper models or specialists.",
                    reasoning=reasoning + [f"Average ${cost_per_iteration:.2f} per iteration"],
                )

        # No intervention needed
        return Intervention(
            intervention_type=InterventionType.NONE,
            should_intervene=False,
            urgency="low",
            recommendation="Mission progressing normally. No intervention needed.",
            reasoning=["Mission metrics within acceptable ranges"],
        )

    def diagnose_mission(
        self,
        mission_id: str,
        mission_data: Optional[Dict[str, Any]] = None
    ) -> MissionDiagnostics:
        """
        Diagnose mission health and identify issues.

        Args:
            mission_id: Mission identifier
            mission_data: Current mission data (if not provided, loads from KG)

        Returns:
            MissionDiagnostics with health status and recommendations
        """
        issues: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []
        metrics: Dict[str, Any] = {}

        # Load mission data if not provided
        if mission_data is None and self.use_knowledge_graph:
            try:
                kg = knowledge_graph.KnowledgeGraph()
                entity = kg.find_entity("mission", mission_id)
                if entity:
                    mission_data = entity.get("metadata", {})
            except Exception:
                pass

        if mission_data is None:
            return MissionDiagnostics(
                mission_id=mission_id,
                health=MissionHealth.WARNING,
                issues=["No mission data available"],
                recommendations=["Ensure mission is properly logged"],
            )

        # Analyze metrics
        status = mission_data.get("status", "unknown")
        cost_usd = mission_data.get("cost_usd", 0.0)
        iterations = mission_data.get("iterations", 0)
        duration_seconds = mission_data.get("duration_seconds", 0)

        metrics["status"] = status
        metrics["cost_usd"] = cost_usd
        metrics["iterations"] = iterations
        metrics["duration_seconds"] = duration_seconds

        # Determine health
        if status == "failed":
            health = MissionHealth.FAILED
            issues.append("Mission failed")
            recommendations.append("Review mission logs to identify failure cause")

        elif status == "success":
            # Check if cost was reasonable
            if cost_usd > 20.0:
                health = MissionHealth.WARNING
                warnings.append(f"High cost: ${cost_usd:.2f}")
                recommendations.append("Consider optimization for similar future missions")
            else:
                health = MissionHealth.EXCELLENT

        elif status == "in_progress":
            # Analyze in-progress mission
            if iterations > 10:
                health = MissionHealth.WARNING
                warnings.append(f"High iteration count: {iterations}")
                recommendations.append("Mission may be stuck - consider intervention")
            elif cost_usd > 15.0:
                health = MissionHealth.WARNING
                warnings.append(f"Cost accumulating: ${cost_usd:.2f}")
                recommendations.append("Monitor cost closely")
            else:
                health = MissionHealth.GOOD

        else:
            health = MissionHealth.WARNING
            warnings.append(f"Unknown status: {status}")

        return MissionDiagnostics(
            mission_id=mission_id,
            health=health,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            metrics=metrics,
        )

    def get_strategic_insights(self) -> Dict[str, Any]:
        """
        Analyze historical patterns and provide strategic insights.

        Returns:
            Dict with strategic insights and recommendations
        """
        insights = {
            "total_missions": len(self.mission_history),
            "patterns": [],
            "recommendations": [],
            "top_domains": [],
            "cost_trends": {},
        }

        if not self.mission_history:
            insights["recommendations"].append("No historical data available yet")
            return insights

        # Analyze by domain
        domain_stats: Dict[str, Dict[str, Any]] = {}
        for mission in self.mission_history:
            domain = mission.get("domain", "unknown")
            if domain not in domain_stats:
                domain_stats[domain] = {
                    "count": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_cost": 0.0,
                }

            domain_stats[domain]["count"] += 1
            if mission.get("status") == "success":
                domain_stats[domain]["successes"] += 1
            else:
                domain_stats[domain]["failures"] += 1
            domain_stats[domain]["total_cost"] += mission.get("cost_usd", 0.0)

        # Calculate success rates
        for domain, stats in domain_stats.items():
            if stats["count"] > 0:
                success_rate = stats["successes"] / stats["count"]
                avg_cost = stats["total_cost"] / stats["count"]

                if success_rate < 0.7:
                    insights["patterns"].append(
                        f"Low success rate in {domain} domain: {success_rate * 100:.1f}%"
                    )
                    insights["recommendations"].append(
                        f"Improve {domain} domain performance through specialist training or better prompts"
                    )

                if avg_cost > 15.0:
                    insights["recommendations"].append(
                        f"Optimize costs for {domain} domain (avg ${avg_cost:.2f} per mission)"
                    )

        # Top domains by volume
        sorted_domains = sorted(
            domain_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        insights["top_domains"] = [
            {
                "domain": domain,
                "count": stats["count"],
                "success_rate": stats["successes"] / stats["count"] if stats["count"] > 0 else 0,
                "avg_cost": stats["total_cost"] / stats["count"] if stats["count"] > 0 else 0,
            }
            for domain, stats in sorted_domains[:5]
        ]

        return insights

    def recommend_mission_strategy(
        self,
        task: str,
        budget_usd: Optional[float] = None,
        max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Recommend strategy for a new mission based on historical data.

        Args:
            task: Mission task description
            budget_usd: Available budget (None = unlimited)
            max_iterations: Maximum iterations (None = default)

        Returns:
            Dict with strategy recommendations
        """
        recommendations: List[str] = []
        estimated_cost = 5.0  # Default estimate
        estimated_iterations = 3  # Default estimate
        confidence = "low"

        # Find similar missions in history
        if self.mission_history:
            similar_missions = self._find_similar_missions(task, limit=5)

            if similar_missions:
                # Calculate averages from similar missions
                total_cost = sum(m.get("cost_usd", 0.0) for m in similar_missions)
                total_iterations = sum(m.get("iterations", 0) for m in similar_missions)
                success_count = sum(1 for m in similar_missions if m.get("status") == "success")

                estimated_cost = total_cost / len(similar_missions)
                estimated_iterations = int(total_iterations / len(similar_missions))
                success_rate = success_count / len(similar_missions)

                confidence = "high" if len(similar_missions) >= 3 else "medium"

                recommendations.append(
                    f"Based on {len(similar_missions)} similar missions: "
                    f"avg cost ${estimated_cost:.2f}, "
                    f"avg {estimated_iterations} iterations, "
                    f"{success_rate * 100:.1f}% success rate"
                )

                if success_rate < 0.7:
                    recommendations.append(
                        "Warning: Similar missions have low success rate. "
                        "Consider using specialists or adjusting approach."
                    )

        # Budget check
        if budget_usd and estimated_cost > budget_usd:
            recommendations.append(
                f"Warning: Estimated cost ${estimated_cost:.2f} exceeds budget ${budget_usd:.2f}. "
                "Consider increasing budget or reducing scope."
            )

        # Specialist recommendation
        if MARKET_AVAILABLE:
            market = specialist_market.SpecialistMarket()
            specialist_rec = market.recommend_specialist(task, budget_usd=budget_usd)
            if specialist_rec:
                recommendations.append(
                    f"Recommended specialist: {specialist_rec.specialist.name} "
                    f"(match: {specialist_rec.match_score:.2f})"
                )

        return {
            "estimated_cost_usd": estimated_cost,
            "estimated_iterations": estimated_iterations,
            "confidence": confidence,
            "recommendations": recommendations,
        }

    def _find_similar_missions(
        self,
        task: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find historically similar missions.

        Args:
            task: Task description
            limit: Maximum number of similar missions to return

        Returns:
            List of similar mission data
        """
        if not self.mission_history:
            return []

        # Simple keyword-based similarity
        task_words = set(task.lower().split())

        scored_missions: List[Tuple[float, Dict[str, Any]]] = []

        for mission in self.mission_history:
            mission_task = mission.get("metadata", {}).get("task", "")
            mission_words = set(mission_task.lower().split())

            # Calculate similarity as overlap coefficient
            overlap = len(task_words & mission_words)
            similarity = overlap / min(len(task_words), len(mission_words)) if task_words and mission_words else 0

            if similarity > 0.2:  # Minimum threshold
                scored_missions.append((similarity, mission))

        # Sort by similarity descending
        scored_missions.sort(key=lambda x: x[0], reverse=True)

        return [mission for _, mission in scored_missions[:limit]]


    # ══════════════════════════════════════════════════════════════════
    # PHASE 5.1: Persistence and Mission Generation
    # ══════════════════════════════════════════════════════════════════

    def persist_suggestions(
        self,
        suggestions: Dict[str, Any],
        mission_id: Optional[str] = None
    ) -> Path:
        """
        Persist overseer suggestions to artifacts.

        Args:
            suggestions: Suggestions dict (from analyze_mission_progress or get_strategic_insights)
            mission_id: Optional mission ID for mission-specific suggestions

        Returns:
            Path to written suggestions file
        """
        # Determine output directory
        if mission_id:
            # Mission-specific suggestions in artifacts/<mission_id>/
            try:
                import paths as paths_module
                artifacts_dir = paths_module.get_root() / "artifacts" / mission_id
            except ImportError:
                artifacts_dir = Path(__file__).parent.parent / "artifacts" / mission_id

            artifacts_dir.mkdir(parents=True, exist_ok=True)
            output_path = artifacts_dir / "overseer_suggestions.jsonl"
        else:
            # General suggestions in artifacts/overseer/
            try:
                import paths as paths_module
                overseer_dir = paths_module.get_root() / "artifacts" / "overseer"
            except ImportError:
                overseer_dir = Path(__file__).parent.parent / "artifacts" / "overseer"

            overseer_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_path = overseer_dir / f"suggestions_{timestamp}.jsonl"

        # Write as JSONL (one line per suggestion)
        with output_path.open("a", encoding="utf-8") as f:
            suggestion_entry = {
                "timestamp": datetime.now().isoformat(),
                "mission_id": mission_id,
                "suggestions": suggestions,
            }
            f.write(json.dumps(suggestion_entry) + "\n")

        return output_path

    def generate_suggested_missions(self) -> List[Dict[str, Any]]:
        """
        Generate suggested missions based on project history and patterns.

        Returns:
            List of suggested mission dicts ready to be written as mission files
        """
        insights = self.get_strategic_insights()
        suggested_missions = []

        # Suggest missions based on patterns and history
        if insights.get("patterns"):
            for pattern in insights["patterns"]:
                if "high failure rate" in pattern:
                    # Suggest a refactoring or stabilization mission
                    suggested_missions.append({
                        "mission_id": f"stabilize_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "task": "Review and stabilize components with high failure rates",
                        "domain": "coding",
                        "max_rounds": 3,
                        "cost_cap_usd": 5.0,
                        "tags": ["stability", "auto-generated", "overseer"],
                        "priority": "high",
                        "reason": pattern,
                    })

        # Suggest missions based on domain performance
        if insights.get("top_domains"):
            for domain_info in insights["top_domains"]:
                if domain_info["success_rate"] < 0.7:  # Less than 70% success
                    suggested_missions.append({
                        "mission_id": f"improve_{domain_info['domain']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "task": f"Improve {domain_info['domain']} workflow and quality checks",
                        "domain": domain_info["domain"],
                        "max_rounds": 2,
                        "cost_cap_usd": 3.0,
                        "tags": ["improvement", "auto-generated", "overseer"],
                        "priority": "medium",
                        "reason": f"Low success rate: {domain_info['success_rate'] * 100:.1f}%",
                    })

        return suggested_missions

    def write_suggested_missions_to_disk(self) -> List[Path]:
        """
        Write suggested missions to missions/ directory as JSON files.

        Returns:
            List of paths to written mission files
        """
        suggested_missions = self.generate_suggested_missions()
        written_paths = []

        if not suggested_missions:
            return written_paths

        # Get missions directory
        try:
            import paths as paths_module
            missions_dir = paths_module.get_missions_dir()
        except ImportError:
            missions_dir = Path(__file__).parent.parent / "missions"

        missions_dir.mkdir(parents=True, exist_ok=True)

        # Write each suggested mission
        for mission in suggested_missions:
            mission_file = missions_dir / f"{mission['mission_id']}.json"

            with mission_file.open("w", encoding="utf-8") as f:
                json.dump(mission, f, indent=2)

            written_paths.append(mission_file)

        return written_paths

    def should_decompose(self, goal_description: str) -> bool:
        """
        Determine if a goal should be decomposed into sub-goals.

        Uses complexity heuristics and historical data to decide.

        Args:
            goal_description: Description of the goal

        Returns:
            True if goal should be decomposed
        """
        description = goal_description.lower()

        # Complexity indicators
        complexity_score = 0

        # Length-based complexity
        if len(description) > 100:
            complexity_score += 2
        elif len(description) > 50:
            complexity_score += 1

        # Multi-step indicators
        if " and " in description:
            complexity_score += description.count(" and ")
        if ", then " in description:
            complexity_score += description.count(", then ") * 2
        if any(f"{i}." in description for i in range(1, 10)):
            complexity_score += 3

        # Multiple action verbs (implement, write, test, deploy, etc.)
        action_verbs = ["implement", "write", "test", "deploy", "create", "build", "update", "refactor"]
        verb_count = sum(1 for verb in action_verbs if verb in description)
        if verb_count >= 2:
            complexity_score += verb_count

        # Threshold for decomposition
        should_decompose = complexity_score >= 3

        return should_decompose

    def decompose_goal(self, goal_description: str) -> List[str]:
        """
        Decompose a complex goal into sub-goals.

        Uses linguistic analysis and pattern matching to break down goals.

        Args:
            goal_description: Complex goal to decompose

        Returns:
            List of sub-goal descriptions
        """
        description = goal_description.strip()
        sub_goals = []

        # Strategy 1: Split on "and"
        if " and " in description.lower():
            parts = description.split(" and ")
            # Clean up parts
            for part in parts:
                part = part.strip()
                if part:
                    # Capitalize first letter if needed
                    if part[0].islower():
                        part = part[0].upper() + part[1:]
                    sub_goals.append(part)

        # Strategy 2: Split on ", then"
        elif ", then " in description.lower():
            parts = description.split(", then ")
            for part in parts:
                part = part.strip()
                if part:
                    if part[0].islower():
                        part = part[0].upper() + part[1:]
                    sub_goals.append(part)

        # Strategy 3: Numbered steps (1. Step one 2. Step two)
        elif any(f"{i}." in description for i in range(1, 10)):
            import re
            # Split on number + dot pattern
            parts = re.split(r'\d+\.', description)
            for part in parts:
                part = part.strip()
                if part and len(part) > 5:  # Skip very short fragments
                    if part[0].islower():
                        part = part[0].upper() + part[1:]
                    sub_goals.append(part)

        # Strategy 4: Sentence-based decomposition for long goals
        elif len(description) > 150:
            # Split on sentence boundaries
            sentences = description.split('. ')
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 20:  # Meaningful sentences only
                    if not sentence.endswith('.'):
                        sentence += '.'
                    sub_goals.append(sentence)

        # Strategy 5: Verb-based decomposition
        else:
            # Look for multiple action verbs and create goals around them
            import re
            verbs = ["implement", "write", "test", "deploy", "create", "build", "update", "refactor", "add", "remove"]

            # Find all verb positions
            verb_positions = []
            for verb in verbs:
                pattern = r'\b' + verb + r'\b'
                for match in re.finditer(pattern, description.lower()):
                    verb_positions.append((match.start(), verb))

            # Sort by position
            verb_positions.sort(key=lambda x: x[0])

            if len(verb_positions) >= 2:
                # Create sub-goals based on verb phrases
                for i, (pos, verb) in enumerate(verb_positions):
                    # Extract context around verb
                    start = pos
                    # Find end (next verb or end of string)
                    if i < len(verb_positions) - 1:
                        end = verb_positions[i + 1][0]
                    else:
                        end = len(description)

                    phrase = description[start:end].strip()
                    if phrase and len(phrase) > 10:
                        # Capitalize first letter
                        phrase = phrase[0].upper() + phrase[1:]
                        sub_goals.append(phrase)

        # Fallback: if no decomposition worked, return original as single goal
        if not sub_goals:
            sub_goals = [description]

        # Limit to reasonable number of sub-goals
        sub_goals = sub_goals[:5]

        return sub_goals


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for overseer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Overseer - Meta-Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Insights command
    subparsers.add_parser("insights", help="Get strategic insights from mission history")

    # Strategy command
    strategy_parser = subparsers.add_parser("strategy", help="Recommend strategy for a mission")
    strategy_parser.add_argument("task", type=str, help="Mission task description")
    strategy_parser.add_argument("--budget", type=float, help="Available budget in USD")
    strategy_parser.add_argument("--iterations", type=int, help="Maximum iterations")

    # Diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Diagnose mission health")
    diagnose_parser.add_argument("mission_id", type=str, help="Mission ID")

    # PHASE 5.1: Review command - prints overview and writes suggested missions
    review_parser = subparsers.add_parser("review", help="Review mission history and generate suggested missions")
    review_parser.add_argument("--limit", type=int, default=10, help="Number of recent missions to review (default: 10)")
    review_parser.add_argument("--write-missions", action="store_true", help="Write suggested missions to missions/ directory")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    overseer_instance = Overseer()

    if args.command == "insights":
        insights = overseer_instance.get_strategic_insights()

        print("\nStrategic Insights\n")
        print(f"Total Missions Analyzed: {insights['total_missions']}\n")

        if insights["top_domains"]:
            print("Top Domains:")
            for domain_info in insights["top_domains"]:
                print(f"  - {domain_info['domain'].upper()}: "
                      f"{domain_info['count']} missions, "
                      f"{domain_info['success_rate'] * 100:.1f}% success rate, "
                      f"${domain_info['avg_cost']:.2f} avg cost")
            print()

        if insights["patterns"]:
            print("Patterns Detected:")
            for pattern in insights["patterns"]:
                print(f"  - {pattern}")
            print()

        if insights["recommendations"]:
            print("Strategic Recommendations:")
            for rec in insights["recommendations"]:
                print(f"  - {rec}")

    elif args.command == "strategy":
        strategy = overseer_instance.recommend_mission_strategy(
            task=args.task,
            budget_usd=args.budget,
            max_iterations=args.iterations
        )

        print(f"\nMission Strategy Recommendation\n")
        print(f"Task: {args.task}\n")
        print(f"Estimated Cost: ${strategy['estimated_cost_usd']:.2f}")
        print(f"Estimated Iterations: {strategy['estimated_iterations']}")
        print(f"Confidence: {strategy['confidence']}\n")

        if strategy["recommendations"]:
            print("Recommendations:")
            for rec in strategy["recommendations"]:
                print(f"  - {rec}")

    elif args.command == "diagnose":
        diagnostics = overseer_instance.diagnose_mission(args.mission_id)

        print(f"\nMission Diagnostics: {args.mission_id}\n")
        print(f"Health: {diagnostics.health.value.upper()}\n")

        if diagnostics.metrics:
            print("Metrics:")
            for key, value in diagnostics.metrics.items():
                print(f"  {key}: {value}")
            print()

        if diagnostics.issues:
            print("Issues:")
            for issue in diagnostics.issues:
                print(f"  - {issue}")
            print()

        if diagnostics.warnings:
            print("Warnings:")
            for warning in diagnostics.warnings:
                print(f"  - {warning}")
            print()

        if diagnostics.recommendations:
            print("Recommendations:")
            for rec in diagnostics.recommendations:
                print(f"  - {rec}")

    elif args.command == "review":
        # PHASE 5.1: Review mission history and generate suggestions
        print(f"\n=== OVERSEER REVIEW (last {args.limit} missions) ===\n")

        insights = overseer_instance.get_strategic_insights()

        # Print overview
        print(f"Total Missions: {insights['total_missions']}")
        print(f"Success Rate: {insights.get('overall_success_rate', 0) * 100:.1f}%\n")

        if insights.get("top_domains"):
            print("Domain Performance:")
            for domain_info in insights["top_domains"][:5]:
                print(f"  {domain_info['domain']:12s}: {domain_info['count']:3d} missions, "
                      f"{domain_info['success_rate'] * 100:5.1f}% success, "
                      f"${domain_info['avg_cost']:6.2f} avg cost")
            print()

        if insights.get("patterns"):
            print("Detected Patterns:")
            for pattern in insights["patterns"]:
                print(f"  - {pattern}")
            print()

        if insights.get("recommendations"):
            print("Strategic Recommendations:")
            for rec in insights["recommendations"]:
                print(f"  - {rec}")
            print()

        # Generate and optionally write suggested missions
        suggested_missions = overseer_instance.generate_suggested_missions()

        if suggested_missions:
            print(f"Generated {len(suggested_missions)} Suggested Missions:")
            for mission in suggested_missions:
                print(f"  - {mission['mission_id']}: {mission['task'][:60]}...")
                print(f"    Priority: {mission['priority']}, Domain: {mission['domain']}")
                print(f"    Reason: {mission['reason']}")
            print()

            if args.write_missions:
                written_paths = overseer_instance.write_suggested_missions_to_disk()
                print(f"✅ Wrote {len(written_paths)} suggested mission files:")
                for path in written_paths:
                    print(f"   {path}")
            else:
                print("💡 Use --write-missions to write these suggestions to missions/ directory")
        else:
            print("No mission suggestions generated at this time.")

        # Persist insights
        suggestions_path = overseer_instance.persist_suggestions(insights)
        print(f"\n📁 Insights saved to: {suggestions_path}")

    elif args.command == "diagnose":
        diagnostics = overseer_instance.diagnose_mission(args.mission_id)

        print(f"\nMission Diagnostics: {args.mission_id}\n")
        print(f"Health: {diagnostics.health.value.upper()}\n")

        if diagnostics.metrics:
            print("Metrics:")
            for key, value in diagnostics.metrics.items():
                print(f"  {key}: {value}")
            print()

        if diagnostics.issues:
            print("Issues:")
            for issue in diagnostics.issues:
                print(f"  - {issue}")
            print()

        if diagnostics.warnings:
            print("Warnings:")
            for warning in diagnostics.warnings:
                print(f"  - {warning}")
            print()

        if diagnostics.recommendations:
            print("Recommendations:")
            for rec in diagnostics.recommendations:
                print(f"  - {rec}")


if __name__ == "__main__":
    main()
