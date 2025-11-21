"""
PHASE 9.4: Hybrid Execution Strategy

Optimizes costs by using local models for 80% of tasks and reserving
expensive cloud models for complex work.

Features:
- Automatic task complexity analysis
- Intelligent model tier selection
- Quality threshold enforcement
- Cost tracking and optimization
- Adaptive routing based on performance

Strategy:
1. Analyze task complexity
2. Route simple/medium tasks to local models
3. Route complex/critical tasks to cloud models
4. Track quality and adjust routing dynamically
5. Maintain quality standards while minimizing costs
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# Local imports
try:
    from .llm_router import LLMRouter, ModelTier, TaskComplexity
    from .performance_tracker import PerformanceTracker
except ImportError:
    # Fallback for tests
    from llm_router import LLMRouter, ModelTier, TaskComplexity
    from performance_tracker import PerformanceTracker


@dataclass
class QualityThresholds:
    """Quality thresholds for different task types."""
    critical: float = 0.95  # Critical tasks require 95% quality
    high: float = 0.85  # High complexity requires 85% quality
    medium: float = 0.75  # Medium complexity requires 75% quality
    low: float = 0.60  # Low complexity requires 60% quality


@dataclass
class CostBudget:
    """Cost budget configuration."""
    daily_limit_usd: float = 10.0
    per_request_limit_usd: float = 0.10
    warn_threshold_pct: float = 0.80  # Warn at 80% of budget


@dataclass
class HybridStats:
    """Statistics for hybrid execution."""
    total_requests: int = 0
    local_requests: int = 0
    cloud_requests: int = 0
    total_cost_usd: float = 0.0
    cost_saved_usd: float = 0.0
    quality_degradations: int = 0  # Times quality fell below threshold


class HybridStrategy:
    """
    Hybrid execution strategy for cost-optimized LLM usage.

    Automatically routes tasks to local or cloud models based on:
    - Task complexity
    - Quality requirements
    - Cost constraints
    - Historical performance

    Target: 80% local, 20% cloud for optimal cost/quality balance.
    """

    def __init__(
        self,
        quality_thresholds: Optional[QualityThresholds] = None,
        cost_budget: Optional[CostBudget] = None,
        target_local_percentage: float = 80.0,
    ):
        """
        Initialize hybrid strategy.

        Args:
            quality_thresholds: Quality thresholds for routing
            cost_budget: Cost budget constraints
            target_local_percentage: Target percentage for local model usage (default: 80%)
        """
        self.quality_thresholds = quality_thresholds or QualityThresholds()
        self.cost_budget = cost_budget or CostBudget()
        self.target_local_percentage = target_local_percentage

        # Initialize router and tracker
        self.router = LLMRouter(enable_local=True, prefer_local=True)
        self.performance_tracker = PerformanceTracker()

        # Statistics
        self.stats = HybridStats()

        # Adaptive parameters
        self._current_local_percentage = 0.0
        self._quality_history: list[float] = []

    def analyze_task_complexity(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskComplexity:
        """
        Analyze task complexity.

        Args:
            prompt: User prompt
            context: Optional context dict

        Returns:
            TaskComplexity enum
        """
        return self.router.analyze_complexity(prompt, context=context)

    def get_quality_threshold(self, complexity: TaskComplexity) -> float:
        """
        Get quality threshold for complexity level.

        Args:
            complexity: Task complexity

        Returns:
            Quality threshold (0.0-1.0)
        """
        threshold_map = {
            TaskComplexity.CRITICAL: self.quality_thresholds.critical,
            TaskComplexity.HIGH: self.quality_thresholds.high,
            TaskComplexity.MEDIUM: self.quality_thresholds.medium,
            TaskComplexity.LOW: self.quality_thresholds.low,
            TaskComplexity.TRIVIAL: self.quality_thresholds.low,
        }
        return threshold_map.get(complexity, self.quality_thresholds.medium)

    def should_use_local(
        self,
        complexity: TaskComplexity,
        force_cloud: bool = False,
    ) -> bool:
        """
        Determine if local model should be used.

        Args:
            complexity: Task complexity
            force_cloud: Force cloud model usage

        Returns:
            True if local model should be used
        """
        # Always use cloud if forced
        if force_cloud:
            return False

        # Critical tasks always use cloud
        if complexity == TaskComplexity.CRITICAL:
            return False

        # High complexity tasks use cloud
        if complexity == TaskComplexity.HIGH:
            return False

        # Check if we're over budget - force local
        if self._is_over_budget():
            print("[HybridStrategy] Over budget - forcing local model")
            return True

        # Check if we're meeting local percentage target
        if self._current_local_percentage < self.target_local_percentage:
            # Below target, prefer local for medium/low tasks
            return complexity in [TaskComplexity.MEDIUM, TaskComplexity.LOW, TaskComplexity.TRIVIAL]
        else:
            # Above target, can use cloud more liberally
            return complexity in [TaskComplexity.LOW, TaskComplexity.TRIVIAL]

    def _is_over_budget(self) -> bool:
        """Check if over cost budget."""
        # Simple check - in production would check daily budget
        return self.stats.total_cost_usd >= self.cost_budget.per_request_limit_usd * 100

    def _estimate_cloud_cost(self, complexity: TaskComplexity) -> float:
        """
        Estimate cost if using cloud model.

        Args:
            complexity: Task complexity

        Returns:
            Estimated cost in USD
        """
        # Rough estimates based on complexity
        cost_map = {
            TaskComplexity.CRITICAL: 0.10,  # GPT-4
            TaskComplexity.HIGH: 0.05,  # GPT-4o
            TaskComplexity.MEDIUM: 0.01,  # GPT-4o-mini
            TaskComplexity.LOW: 0.005,  # GPT-4o-mini
            TaskComplexity.TRIVIAL: 0.002,  # GPT-4o-mini
        }
        return cost_map.get(complexity, 0.01)

    async def execute(
        self,
        prompt: str,
        system: Optional[str] = None,
        complexity: Optional[TaskComplexity] = None,
        force_cloud: bool = False,
        force_local: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute request with hybrid strategy.

        Args:
            prompt: User prompt
            system: System prompt
            complexity: Explicit complexity (skips analysis)
            force_cloud: Force cloud model usage
            force_local: Force local model usage
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            context: Additional context

        Returns:
            Dict with response and metadata
        """
        self.stats.total_requests += 1

        # Analyze complexity if not provided
        if complexity is None:
            complexity = self.analyze_task_complexity(prompt, context)

        # Determine routing
        use_local = self.should_use_local(complexity, force_cloud)

        if force_local:
            use_local = True
        elif force_cloud:
            use_local = False

        # Select tier
        if use_local:
            tier = ModelTier.LOCAL
            self.stats.local_requests += 1
        else:
            # Select cloud tier based on complexity
            if complexity == TaskComplexity.CRITICAL:
                tier = ModelTier.PREMIUM
            elif complexity == TaskComplexity.HIGH:
                tier = ModelTier.STANDARD
            else:
                tier = ModelTier.MINI

            self.stats.cloud_requests += 1

        # Estimate cost savings
        if use_local:
            estimated_cloud_cost = self._estimate_cloud_cost(complexity)
            self.stats.cost_saved_usd += estimated_cloud_cost

        # Execute request
        print(f"[HybridStrategy] Routing {complexity.value} task to "
              f"{'local' if use_local else 'cloud'} ({tier.value})")

        response = await self.router.route(
            prompt=prompt,
            system=system,
            complexity=complexity,
            temperature=temperature,
            max_tokens=max_tokens,
            context=context,
        )

        # Track cost
        cost = response.get("cost_usd", 0.0)
        self.stats.total_cost_usd += cost

        # Update local percentage
        total = self.stats.total_requests
        self._current_local_percentage = (self.stats.local_requests / total * 100) if total > 0 else 0

        # Add strategy metadata
        response["hybrid_strategy"] = {
            "complexity": complexity.value,
            "tier": tier.value,
            "use_local": use_local,
            "cost_saved_usd": self.stats.cost_saved_usd,
            "local_percentage": self._current_local_percentage,
        }

        return response

    async def execute_with_quality_check(
        self,
        prompt: str,
        system: Optional[str] = None,
        complexity: Optional[TaskComplexity] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute with automatic quality checking and fallback.

        If local model produces low-quality output, automatically retry with cloud.

        Args:
            prompt: User prompt
            system: System prompt
            complexity: Task complexity
            temperature: Sampling temperature
            max_tokens: Max tokens
            context: Additional context

        Returns:
            Dict with response and metadata
        """
        # First attempt
        response = await self.execute(
            prompt=prompt,
            system=system,
            complexity=complexity,
            temperature=temperature,
            max_tokens=max_tokens,
            context=context,
        )

        # Get quality threshold
        if complexity is None:
            complexity = self.analyze_task_complexity(prompt, context)

        threshold = self.get_quality_threshold(complexity)

        # Check if quality assessment is available
        quality_score = response.get("quality_score")

        if quality_score is not None and quality_score < threshold:
            print(f"[HybridStrategy] Quality {quality_score:.2f} below threshold {threshold:.2f}")

            # If local model was used, retry with cloud
            if response["hybrid_strategy"]["use_local"]:
                print("[HybridStrategy] Retrying with cloud model for better quality")

                self.stats.quality_degradations += 1

                # Retry with cloud
                response = await self.execute(
                    prompt=prompt,
                    system=system,
                    complexity=complexity,
                    force_cloud=True,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    context=context,
                )

                response["quality_fallback_used"] = True

        return response

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        total = self.stats.total_requests
        local_pct = (self.stats.local_requests / total * 100) if total > 0 else 0
        cloud_pct = (self.stats.cloud_requests / total * 100) if total > 0 else 0

        # Get router stats
        router_stats = self.router.get_statistics()

        return {
            "total_requests": total,
            "local_requests": self.stats.local_requests,
            "cloud_requests": self.stats.cloud_requests,
            "local_percentage": local_pct,
            "cloud_percentage": cloud_pct,
            "target_local_percentage": self.target_local_percentage,
            "total_cost_usd": self.stats.total_cost_usd,
            "cost_saved_usd": self.stats.cost_saved_usd,
            "quality_degradations": self.stats.quality_degradations,
            "avg_cost_per_request": self.stats.total_cost_usd / total if total > 0 else 0,
            "cost_efficiency": (
                (self.stats.cost_saved_usd / (self.stats.total_cost_usd + self.stats.cost_saved_usd) * 100)
                if (self.stats.total_cost_usd + self.stats.cost_saved_usd) > 0 else 0
            ),
            "router_stats": router_stats,
        }

    def get_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for optimization.

        Returns:
            Dict with recommendations
        """
        stats = self.get_statistics()
        recommendations = []

        # Check local percentage
        local_pct = stats["local_percentage"]
        if local_pct < self.target_local_percentage - 10:
            recommendations.append({
                "type": "increase_local",
                "message": f"Local usage at {local_pct:.1f}%, below target {self.target_local_percentage:.1f}%. "
                          "Consider routing more tasks to local models.",
            })
        elif local_pct > self.target_local_percentage + 10:
            recommendations.append({
                "type": "decrease_local",
                "message": f"Local usage at {local_pct:.1f}%, above target {self.target_local_percentage:.1f}%. "
                          "May be sacrificing quality - consider using cloud models for complex tasks.",
            })

        # Check quality degradations
        if self.stats.quality_degradations > self.stats.total_requests * 0.1:
            recommendations.append({
                "type": "quality_issues",
                "message": f"High quality degradation rate ({self.stats.quality_degradations} out of {self.stats.total_requests}). "
                          "Consider adjusting quality thresholds or using cloud models more often.",
            })

        # Check cost efficiency
        cost_efficiency = stats["cost_efficiency"]
        if cost_efficiency < 50:
            recommendations.append({
                "type": "low_efficiency",
                "message": f"Cost efficiency at {cost_efficiency:.1f}%. "
                          "Consider using local models more to reduce costs.",
            })

        # Check budget
        if self.stats.total_cost_usd > self.cost_budget.daily_limit_usd * 0.8:
            recommendations.append({
                "type": "budget_warning",
                "message": f"Cost at ${self.stats.total_cost_usd:.2f}, approaching daily limit ${self.cost_budget.daily_limit_usd:.2f}. "
                          "Consider using local models exclusively.",
            })

        return {
            "recommendations": recommendations,
            "summary": f"{len(recommendations)} recommendation(s)",
        }
