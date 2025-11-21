"""
PHASE 5.3: Feedback Analyzer - Pattern Detection

Analyzes mission feedback and outcomes to detect patterns:
- Success/failure pattern identification
- Common error detection
- Feedback trend analysis
- Optimization opportunity discovery
- Root cause analysis

Usage:
    >>> from agent import feedback_analyzer
    >>> analyzer = feedback_analyzer.FeedbackAnalyzer()
    >>> patterns = analyzer.detect_patterns()
    >>> for pattern in patterns:
    ...     print(f"{pattern['type']}: {pattern['description']}")
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Local imports
try:
    import knowledge_graph
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Pattern Types
# ══════════════════════════════════════════════════════════════════════


class PatternType(str, Enum):
    """Types of patterns that can be detected."""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    ERROR_PATTERN = "error_pattern"
    COST_ANOMALY = "cost_anomaly"
    ITERATION_PATTERN = "iteration_pattern"
    DOMAIN_CORRELATION = "domain_correlation"


@dataclass
class Pattern:
    """A detected pattern in mission feedback."""

    pattern_type: PatternType
    description: str
    occurrences: int
    confidence: float  # 0.0 to 1.0
    examples: List[str] = field(default_factory=list)
    impact: str = "medium"  # "high", "medium", "low"
    actionable: bool = True
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_type": self.pattern_type.value,
            "description": self.description,
            "occurrences": self.occurrences,
            "confidence": self.confidence,
            "examples": self.examples[:5],  # Limit examples
            "impact": self.impact,
            "actionable": self.actionable,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }


# ══════════════════════════════════════════════════════════════════════
# Feedback Analyzer
# ══════════════════════════════════════════════════════════════════════


class FeedbackAnalyzer:
    """Analyzes mission feedback to detect patterns and trends."""

    def __init__(
        self,
        lookback_days: int = 30,
        min_occurrences: int = 3,
        min_confidence: float = 0.6
    ):
        """
        Initialize feedback analyzer.

        Args:
            lookback_days: Number of days to analyze
            min_occurrences: Minimum occurrences to consider a pattern
            min_confidence: Minimum confidence to report a pattern
        """
        self.lookback_days = lookback_days
        self.min_occurrences = min_occurrences
        self.min_confidence = min_confidence

        # Historical data
        self.mission_history: List[Dict[str, Any]] = []
        self.error_messages: List[str] = []
        self.success_messages: List[str] = []

        # Load historical data
        if KG_AVAILABLE:
            self._load_history()

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

            # Filter by date and extract feedback
            for mission in all_missions:
                created_at = mission.get("created_at")
                if created_at:
                    try:
                        timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        if timestamp >= cutoff:
                            self.mission_history.append(mission)

                            # Extract error/success messages
                            metadata = mission.get("metadata", {})
                            if mission.get("status") == "failed":
                                error = metadata.get("error", "")
                                if error:
                                    self.error_messages.append(error)
                            elif mission.get("status") == "success":
                                feedback = metadata.get("feedback", "")
                                if feedback:
                                    self.success_messages.append(feedback)
                    except Exception:
                        continue

        except Exception as e:
            print(f"[Analyzer] Warning: Failed to load mission history: {e}")

    def detect_patterns(self) -> List[Pattern]:
        """
        Detect patterns in mission feedback.

        Returns:
            List of detected patterns
        """
        patterns: List[Pattern] = []

        if not self.mission_history:
            return patterns

        # Detect various pattern types
        patterns.extend(self._detect_error_patterns())
        patterns.extend(self._detect_success_patterns())
        patterns.extend(self._detect_cost_anomalies())
        patterns.extend(self._detect_iteration_patterns())
        patterns.extend(self._detect_domain_correlations())

        # Filter by confidence
        patterns = [p for p in patterns if p.confidence >= self.min_confidence]

        # Sort by confidence descending
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        return patterns

    def _detect_error_patterns(self) -> List[Pattern]:
        """Detect common error patterns."""
        patterns: List[Pattern] = []

        if not self.error_messages:
            return patterns

        # Count error types using simple keyword matching
        error_keywords = {
            "timeout": ["timeout", "time out", "exceeded time"],
            "memory": ["memory", "out of memory", "oom"],
            "api_error": ["api error", "api failed", "connection error"],
            "validation": ["validation", "invalid", "not found"],
            "budget": ["budget", "cost limit", "exceeded budget"],
        }

        error_counts: Dict[str, List[str]] = defaultdict(list)

        for error_msg in self.error_messages:
            error_lower = error_msg.lower()
            for error_type, keywords in error_keywords.items():
                if any(kw in error_lower for kw in keywords):
                    error_counts[error_type].append(error_msg)

        # Create patterns for frequent errors
        for error_type, examples in error_counts.items():
            if len(examples) >= self.min_occurrences:
                confidence = min(len(examples) / len(self.error_messages), 1.0)

                # Generate recommendations
                recommendations = []
                if error_type == "timeout":
                    recommendations.append("Increase timeout limits or optimize for faster execution")
                elif error_type == "memory":
                    recommendations.append("Reduce memory usage or increase memory limits")
                elif error_type == "api_error":
                    recommendations.append("Implement retry logic or check API connectivity")
                elif error_type == "validation":
                    recommendations.append("Improve input validation or error handling")
                elif error_type == "budget":
                    recommendations.append("Optimize costs or increase budget allocation")

                patterns.append(
                    Pattern(
                        pattern_type=PatternType.ERROR_PATTERN,
                        description=f"Recurring {error_type} errors",
                        occurrences=len(examples),
                        confidence=confidence,
                        examples=examples[:3],
                        impact="high",
                        recommendations=recommendations,
                        metadata={"error_type": error_type},
                    )
                )

        return patterns

    def _detect_success_patterns(self) -> List[Pattern]:
        """Detect patterns in successful missions."""
        patterns: List[Pattern] = []

        if len(self.mission_history) < self.min_occurrences:
            return patterns

        # Analyze successful missions
        successful_missions = [
            m for m in self.mission_history
            if m.get("status") == "success"
        ]

        if not successful_missions:
            return patterns

        # Find common characteristics
        low_cost_successes = [
            m for m in successful_missions
            if m.get("cost_usd", 0.0) < 5.0
        ]

        if len(low_cost_successes) >= self.min_occurrences:
            confidence = len(low_cost_successes) / len(successful_missions)
            if confidence > 0.5:
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.SUCCESS_PATTERN,
                        description="Low-cost missions have high success rate",
                        occurrences=len(low_cost_successes),
                        confidence=confidence,
                        impact="medium",
                        recommendations=[
                            "Prioritize cost optimization strategies",
                            "Use simpler models or fewer iterations when possible"
                        ],
                        metadata={"threshold_usd": 5.0},
                    )
                )

        # Analyze by iteration count
        quick_successes = [
            m for m in successful_missions
            if m.get("iterations", 0) <= 3
        ]

        if len(quick_successes) >= self.min_occurrences:
            confidence = len(quick_successes) / len(successful_missions)
            if confidence > 0.5:
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.SUCCESS_PATTERN,
                        description="Missions completing in ≤3 iterations succeed more often",
                        occurrences=len(quick_successes),
                        confidence=confidence,
                        impact="medium",
                        recommendations=[
                            "Improve initial planning to reduce iterations",
                            "Consider early stopping for simple tasks"
                        ],
                        metadata={"max_iterations": 3},
                    )
                )

        return patterns

    def _detect_cost_anomalies(self) -> List[Pattern]:
        """Detect cost-related patterns and anomalies."""
        patterns: List[Pattern] = []

        if len(self.mission_history) < self.min_occurrences:
            return patterns

        # Calculate cost statistics
        costs = [m.get("cost_usd", 0.0) for m in self.mission_history if m.get("cost_usd", 0.0) > 0]

        if not costs:
            return patterns

        avg_cost = sum(costs) / len(costs)
        max_cost = max(costs)

        # Detect expensive outliers
        expensive_missions = [
            m for m in self.mission_history
            if m.get("cost_usd", 0.0) > avg_cost * 2
        ]

        if len(expensive_missions) >= self.min_occurrences:
            confidence = min(len(expensive_missions) / len(self.mission_history), 1.0)

            patterns.append(
                Pattern(
                    pattern_type=PatternType.COST_ANOMALY,
                    description=f"Some missions cost >2x average (${avg_cost * 2:.2f} vs ${avg_cost:.2f})",
                    occurrences=len(expensive_missions),
                    confidence=confidence,
                    impact="high",
                    recommendations=[
                        "Investigate high-cost missions for inefficiencies",
                        "Consider cost caps or budget alerts",
                        "Use cheaper models for expensive missions"
                    ],
                    metadata={
                        "average_cost_usd": avg_cost,
                        "threshold_usd": avg_cost * 2,
                    },
                )
            )

        return patterns

    def _detect_iteration_patterns(self) -> List[Pattern]:
        """Detect iteration-related patterns."""
        patterns: List[Pattern] = []

        if len(self.mission_history) < self.min_occurrences:
            return patterns

        # Analyze iteration counts
        iterations = [m.get("iterations", 0) for m in self.mission_history if m.get("iterations", 0) > 0]

        if not iterations:
            return patterns

        avg_iterations = sum(iterations) / len(iterations)

        # Detect high-iteration missions
        high_iteration_missions = [
            m for m in self.mission_history
            if m.get("iterations", 0) > avg_iterations * 1.5
        ]

        if len(high_iteration_missions) >= self.min_occurrences:
            confidence = min(len(high_iteration_missions) / len(self.mission_history), 1.0)

            # Check if high iterations correlate with failure
            failed_high_iter = [
                m for m in high_iteration_missions
                if m.get("status") == "failed"
            ]

            if len(failed_high_iter) > len(high_iteration_missions) * 0.5:
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.ITERATION_PATTERN,
                        description=f"High iteration count (>{avg_iterations * 1.5:.0f}) correlates with failure",
                        occurrences=len(high_iteration_missions),
                        confidence=confidence,
                        impact="high",
                        recommendations=[
                            "Implement iteration limits to prevent runaway missions",
                            "Improve convergence detection",
                            "Consider aborting missions that exceed expected iterations"
                        ],
                        metadata={
                            "average_iterations": avg_iterations,
                            "threshold": avg_iterations * 1.5,
                        },
                    )
                )

        return patterns

    def _detect_domain_correlations(self) -> List[Pattern]:
        """Detect domain-specific patterns."""
        patterns: List[Pattern] = []

        if len(self.mission_history) < self.min_occurrences:
            return patterns

        # Group by domain
        domain_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total": 0,
            "successes": 0,
            "total_cost": 0.0,
        })

        for mission in self.mission_history:
            domain = mission.get("domain", "unknown")
            domain_stats[domain]["total"] += 1

            if mission.get("status") == "success":
                domain_stats[domain]["successes"] += 1

            domain_stats[domain]["total_cost"] += mission.get("cost_usd", 0.0)

        # Analyze each domain
        for domain, stats in domain_stats.items():
            if stats["total"] < self.min_occurrences:
                continue

            success_rate = stats["successes"] / stats["total"]
            avg_cost = stats["total_cost"] / stats["total"]

            # Detect low-performing domains
            if success_rate < 0.6:
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.DOMAIN_CORRELATION,
                        description=f"{domain} domain has low success rate ({success_rate * 100:.1f}%)",
                        occurrences=stats["total"],
                        confidence=min(stats["total"] / 10.0, 1.0),  # More missions = higher confidence
                        impact="high",
                        recommendations=[
                            f"Review {domain} domain prompts and specialist selection",
                            f"Collect more training data for {domain} tasks",
                            f"Consider specialized tools for {domain} domain"
                        ],
                        metadata={
                            "domain": domain,
                            "success_rate": success_rate,
                            "average_cost_usd": avg_cost,
                        },
                    )
                )

        return patterns

    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """
        Analyze trends in mission feedback over time.

        Returns:
            Dict with trend analysis
        """
        trends = {
            "total_missions": len(self.mission_history),
            "success_rate": 0.0,
            "failure_rate": 0.0,
            "common_errors": [],
            "recommendations": [],
        }

        if not self.mission_history:
            return trends

        # Calculate basic rates
        successes = sum(1 for m in self.mission_history if m.get("status") == "success")
        failures = len(self.mission_history) - successes

        trends["success_rate"] = successes / len(self.mission_history)
        trends["failure_rate"] = failures / len(self.mission_history)

        # Extract common error keywords
        if self.error_messages:
            # Simple word frequency analysis
            all_words = []
            for msg in self.error_messages:
                words = re.findall(r'\b\w{4,}\b', msg.lower())  # Words with 4+ chars
                all_words.extend(words)

            word_counts = Counter(all_words)
            trends["common_errors"] = [
                {"word": word, "count": count}
                for word, count in word_counts.most_common(10)
            ]

        # Generate recommendations based on trends
        if trends["failure_rate"] > 0.3:
            trends["recommendations"].append(
                "High failure rate detected. Review error patterns and improve error handling."
            )

        return trends

    def generate_analysis_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive feedback analysis report.

        Returns:
            Dict with patterns, trends, and recommendations
        """
        patterns = self.detect_patterns()
        trends = self.analyze_feedback_trends()

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "lookback_days": self.lookback_days,
            "missions_analyzed": len(self.mission_history),
            "patterns_detected": len(patterns),
            "patterns": [p.to_dict() for p in patterns],
            "trends": trends,
            "high_impact_patterns": [
                p.to_dict() for p in patterns if p.impact == "high"
            ],
        }


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for feedback analyzer."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Feedback Analyzer - Pattern Detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Detect command
    detect_parser = subparsers.add_parser("detect", help="Detect patterns in feedback")
    detect_parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    detect_parser.add_argument("--min-occurrences", type=int, default=3, help="Minimum occurrences (default: 3)")

    # Trends command
    trends_parser = subparsers.add_parser("trends", help="Analyze feedback trends")
    trends_parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate analysis report")
    report_parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    report_parser.add_argument("--output", type=str, help="Output file path (JSON)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "detect":
        analyzer = FeedbackAnalyzer(
            lookback_days=args.days,
            min_occurrences=args.min_occurrences
        )
        patterns = analyzer.detect_patterns()

        if not patterns:
            print(f"\nNo patterns detected in last {args.days} days")
            return

        print(f"\nDetected Patterns (last {args.days} days)\n")
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. [{pattern.pattern_type.value.upper()}] {pattern.description}")
            print(f"   Occurrences: {pattern.occurrences}")
            print(f"   Confidence: {pattern.confidence * 100:.1f}%")
            print(f"   Impact: {pattern.impact}")
            if pattern.recommendations:
                print(f"   Recommendations:")
                for rec in pattern.recommendations:
                    print(f"     - {rec}")
            print()

    elif args.command == "trends":
        analyzer = FeedbackAnalyzer(lookback_days=args.days)
        trends = analyzer.analyze_feedback_trends()

        print(f"\nFeedback Trends (last {args.days} days)\n")
        print(f"Total Missions: {trends['total_missions']}")
        print(f"Success Rate: {trends['success_rate'] * 100:.1f}%")
        print(f"Failure Rate: {trends['failure_rate'] * 100:.1f}%")

        if trends["common_errors"]:
            print(f"\nCommon Error Keywords:")
            for error in trends["common_errors"]:
                print(f"  - {error['word']}: {error['count']} occurrences")

        if trends["recommendations"]:
            print(f"\nRecommendations:")
            for rec in trends["recommendations"]:
                print(f"  - {rec}")

    elif args.command == "report":
        analyzer = FeedbackAnalyzer(lookback_days=args.days)
        report = analyzer.generate_analysis_report()

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"\nAnalysis report saved to: {output_path}")
        else:
            print("\nFeedback Analysis Report\n")
            print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
