"""
Autonomous Agent Coordinator

Connects self-reflection, goal decomposition, and auto-execution for full autonomy.

Features:
- Automatic self-improvement: self_refinement → auto_improver → execution
- Recursive goal decomposition: overseer → sub-goals → execution
- Safety bounds: max iterations, timeout limits, resource caps
- Autonomous learning loops with safety controls

Usage:
    coordinator = AutonomousCoordinator()

    # Run autonomous improvement cycle
    await coordinator.run_improvement_cycle()

    # Decompose and execute complex goals
    result = await coordinator.execute_goal_with_decomposition("Build new feature")
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .self_refinement import SelfRefiner
except ImportError:
    SelfRefiner = None

try:
    from .auto_improver import AutoImprover, create_auto_improver
except ImportError:
    AutoImprover = None
    create_auto_improver = None

try:
    from .overseer import Overseer
except ImportError:
    Overseer = None


# =============================================================================
# Safety Configuration
# =============================================================================

@dataclass
class SafetyBounds:
    """Safety limits for autonomous operations"""

    # Iteration limits
    max_iterations: int = 100  # Maximum iterations per goal
    max_depth: int = 5  # Maximum recursion depth for goal decomposition
    max_concurrent_goals: int = 3  # Maximum parallel goals

    # Time limits
    max_execution_time_minutes: int = 60  # Maximum execution time per goal
    timeout_between_iterations_seconds: int = 5  # Cooldown between iterations

    # Resource limits
    max_cost_per_goal_usd: float = 10.0  # Maximum cost per goal
    max_total_cost_usd: float = 100.0  # Maximum total cost

    # Safety checks
    require_human_approval_for_destructive: bool = True
    enable_rollback: bool = True
    stop_on_repeated_failures: bool = True
    max_consecutive_failures: int = 3

    # Improvement limits
    max_improvements_per_cycle: int = 5
    min_confidence_for_auto_execute: float = 0.8


@dataclass
class AutonomousState:
    """State tracking for autonomous agent"""

    iteration_count: int = 0
    depth: int = 0
    total_cost_usd: float = 0.0
    consecutive_failures: int = 0
    started_at: Optional[datetime] = None
    goals_completed: int = 0
    improvements_applied: int = 0
    last_iteration_time: Optional[datetime] = None


# =============================================================================
# Goal Decomposition
# =============================================================================

class GoalStatus(Enum):
    """Status of goal execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class Goal:
    """A goal to be executed"""

    id: str
    description: str
    parent_id: Optional[str] = None
    status: GoalStatus = GoalStatus.PENDING
    depth: int = 0

    # Sub-goals (for decomposition)
    sub_goals: List[Goal] = field(default_factory=list)

    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cost_usd: float = 0.0
    iterations: int = 0

    # Result
    result: Optional[Any] = None
    error: Optional[str] = None


# =============================================================================
# Autonomous Coordinator
# =============================================================================

class AutonomousCoordinator:
    """
    Autonomous Agent Coordinator

    Connects all autonomous capabilities:
    - Self-reflection → auto-execution
    - Goal decomposition → execution
    - Safety bounds and monitoring

    Example:
        coordinator = AutonomousCoordinator()

        # Run self-improvement cycle
        stats = await coordinator.run_improvement_cycle()
        print(f"Applied {stats['improvements_applied']} improvements")

        # Execute complex goal with decomposition
        result = await coordinator.execute_goal_with_decomposition(
            goal_description="Implement new API endpoint",
            max_depth=3
        )
    """

    def __init__(
        self,
        safety_bounds: Optional[SafetyBounds] = None,
        self_refiner: Optional[SelfRefiner] = None,
        auto_improver: Optional[AutoImprover] = None,
        overseer: Optional[Overseer] = None,
    ):
        """
        Initialize autonomous coordinator.

        Args:
            safety_bounds: Safety configuration
            self_refiner: Self-refinement system
            auto_improver: Auto-improvement system
            overseer: Meta-orchestration system
        """
        self.safety_bounds = safety_bounds or SafetyBounds()
        self.state = AutonomousState()

        # Initialize subsystems
        self.self_refiner = self_refiner or (SelfRefiner() if SelfRefiner else None)
        self.auto_improver = auto_improver or (create_auto_improver() if create_auto_improver else None)
        self.overseer = overseer or (Overseer() if Overseer else None)

        # Goal tracking
        self.goals: Dict[str, Goal] = {}
        self.active_goals: List[str] = []

        print(f"[AutonomousCoordinator] Initialized with safety bounds:")
        print(f"  Max iterations: {self.safety_bounds.max_iterations}")
        print(f"  Max depth: {self.safety_bounds.max_depth}")
        print(f"  Max cost: ${self.safety_bounds.max_total_cost_usd}")

    # =========================================================================
    # Self-Improvement Cycle
    # =========================================================================

    async def run_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run autonomous self-improvement cycle.

        Process:
        1. Analyze past performance (self_refinement)
        2. Generate improvement suggestions
        3. Evaluate suggestions (confidence-based)
        4. Execute high-confidence improvements automatically
        5. A/B test medium-confidence improvements
        6. Reject low-confidence improvements

        Returns:
            Dict with cycle statistics
        """
        if self.self_refiner is None or self.auto_improver is None:
            print("[AutonomousCoordinator] Self-improvement systems not available")
            return {"error": "Systems not available"}

        print("\n[AutonomousCoordinator] Starting self-improvement cycle...")
        cycle_start = datetime.now()

        # Step 1: Generate improvement suggestions
        print("[AutonomousCoordinator] Step 1: Analyzing performance...")
        try:
            improvements = self.self_refiner.suggest_improvements()
            print(f"[AutonomousCoordinator] Generated {len(improvements)} suggestions")
        except Exception as e:
            print(f"[AutonomousCoordinator] Error generating suggestions: {e}")
            return {"error": str(e)}

        # Step 2: Process suggestions through auto-improver
        print("[AutonomousCoordinator] Step 2: Processing suggestions...")

        # Convert improvements to format expected by auto_improver
        suggestions_dict = [
            {
                "area": imp.area.value if hasattr(imp.area, 'value') else imp.area,
                "priority": imp.priority,
                "suggestion": imp.suggestion,
                "confidence": self._calculate_confidence(imp),
                "changes": self._extract_changes(imp),
            }
            for imp in improvements[:self.safety_bounds.max_improvements_per_cycle]
        ]

        # Execute improvements
        stats = self.auto_improver.process_suggestions(suggestions_dict)

        # Update state
        self.state.improvements_applied += stats["auto_executed"]

        cycle_duration = (datetime.now() - cycle_start).total_seconds()

        print(f"\n[AutonomousCoordinator] Improvement cycle complete:")
        print(f"  Auto-executed: {stats['auto_executed']}")
        print(f"  A/B testing: {stats['ab_testing']}")
        print(f"  Rejected: {stats['rejected']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Duration: {cycle_duration:.1f}s")

        return {
            "success": True,
            "suggestions_generated": len(improvements),
            "suggestions_processed": len(suggestions_dict),
            **stats,
            "duration_seconds": cycle_duration,
        }

    def _calculate_confidence(self, improvement) -> float:
        """Calculate confidence score for improvement"""
        # Map priority and expected impact to confidence
        priority_scores = {"high": 0.9, "medium": 0.7, "low": 0.5}
        impact_scores = {"high": 0.9, "medium": 0.7, "low": 0.5}

        priority_score = priority_scores.get(improvement.priority, 0.5)
        impact_score = impact_scores.get(improvement.expected_impact, 0.5)

        # Average of priority and impact
        return (priority_score + impact_score) / 2

    def _extract_changes(self, improvement) -> Dict[str, Any]:
        """Extract config/prompt changes from improvement"""
        # Parse the suggestion text to extract concrete changes
        # This is a simplified version - production would be more sophisticated
        return {
            "area": improvement.area.value if hasattr(improvement.area, 'value') else improvement.area,
            "suggestion": improvement.suggestion,
        }

    # =========================================================================
    # Goal Decomposition and Execution
    # =========================================================================

    async def execute_goal_with_decomposition(
        self,
        goal_description: str,
        max_depth: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute goal with automatic decomposition.

        Process:
        1. Analyze goal complexity
        2. If complex, decompose into sub-goals recursively
        3. Execute sub-goals with iteration limits
        4. Aggregate results
        5. Monitor safety bounds

        Args:
            goal_description: High-level goal description
            max_depth: Maximum decomposition depth (overrides safety_bounds)

        Returns:
            Execution result with status and metrics
        """
        max_depth = max_depth or self.safety_bounds.max_depth

        print(f"\n[AutonomousCoordinator] Executing goal: {goal_description}")
        print(f"  Max depth: {max_depth}")
        print(f"  Max iterations: {self.safety_bounds.max_iterations}")

        # Create root goal
        goal = Goal(
            id=f"goal_{len(self.goals)}",
            description=goal_description,
            depth=0,
        )

        self.goals[goal.id] = goal
        self.state.started_at = datetime.now()

        # Execute goal (with decomposition if needed)
        try:
            result = await self._execute_goal_recursive(goal, max_depth)

            print(f"\n[AutonomousCoordinator] Goal completed: {goal.description}")
            print(f"  Status: {goal.status.value}")
            print(f"  Iterations: {goal.iterations}")
            print(f"  Cost: ${goal.cost_usd:.4f}")

            return {
                "success": goal.status == GoalStatus.COMPLETED,
                "goal_id": goal.id,
                "status": goal.status.value,
                "result": goal.result,
                "iterations": goal.iterations,
                "cost_usd": goal.cost_usd,
                "sub_goals_count": len(goal.sub_goals),
                "error": goal.error,
            }

        except Exception as e:
            print(f"[AutonomousCoordinator] Error executing goal: {e}")
            goal.status = GoalStatus.FAILED
            goal.error = str(e)

            return {
                "success": False,
                "error": str(e),
                "goal_id": goal.id,
            }

    async def _execute_goal_recursive(
        self,
        goal: Goal,
        remaining_depth: int,
    ) -> Any:
        """
        Execute goal recursively with decomposition.

        Args:
            goal: Goal to execute
            remaining_depth: Remaining decomposition depth

        Returns:
            Goal result
        """
        goal.status = GoalStatus.IN_PROGRESS
        goal.started_at = datetime.now()

        # Check if goal should be decomposed
        should_decompose = (
            remaining_depth > 0
            and self._should_decompose_goal(goal)
        )

        if should_decompose:
            print(f"[AutonomousCoordinator] Decomposing goal: {goal.description}")

            # Decompose goal into sub-goals
            sub_goals = await self._decompose_goal(goal)
            goal.sub_goals = sub_goals

            print(f"[AutonomousCoordinator] Decomposed into {len(sub_goals)} sub-goals")

            # Execute sub-goals
            sub_results = []
            for sub_goal in sub_goals:
                # Check safety bounds
                if not self._check_safety_bounds():
                    print("[AutonomousCoordinator] Safety bounds exceeded, stopping")
                    goal.status = GoalStatus.BLOCKED
                    goal.error = "Safety bounds exceeded"
                    return None

                sub_result = await self._execute_goal_recursive(
                    sub_goal,
                    remaining_depth - 1
                )
                sub_results.append(sub_result)

                # Aggregate cost
                goal.cost_usd += sub_goal.cost_usd

            # Aggregate results
            goal.result = sub_results
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.now()

            return sub_results

        else:
            # Execute goal directly (with iteration limits)
            result = await self._execute_goal_with_iterations(goal)

            goal.result = result
            goal.completed_at = datetime.now()

            return result

    def _should_decompose_goal(self, goal: Goal) -> bool:
        """
        Determine if goal should be decomposed.

        Heuristics:
        - Goal description is long (complex)
        - Contains multiple steps or "and" clauses
        - Overseer suggests decomposition
        """
        description = goal.description.lower()

        # Simple heuristics
        is_complex = (
            len(description) > 100
            or " and " in description
            or ", then " in description
            or description.count('.') > 2
        )

        # Could use overseer for more sophisticated analysis
        if self.overseer and hasattr(self.overseer, 'should_decompose'):
            return self.overseer.should_decompose(goal.description)

        return is_complex

    async def _decompose_goal(self, goal: Goal) -> List[Goal]:
        """
        Decompose goal into sub-goals.

        Uses overseer for intelligent decomposition if available,
        otherwise uses simple rule-based decomposition.
        """
        if self.overseer and hasattr(self.overseer, 'decompose_goal'):
            # Use overseer for intelligent decomposition
            sub_goal_descriptions = self.overseer.decompose_goal(goal.description)
        else:
            # Simple rule-based decomposition
            sub_goal_descriptions = self._simple_decompose(goal.description)

        # Create Goal objects
        sub_goals = []
        for i, desc in enumerate(sub_goal_descriptions):
            sub_goal = Goal(
                id=f"{goal.id}_sub_{i}",
                description=desc,
                parent_id=goal.id,
                depth=goal.depth + 1,
            )
            sub_goals.append(sub_goal)
            self.goals[sub_goal.id] = sub_goal

        return sub_goals

    def _simple_decompose(self, description: str) -> List[str]:
        """Simple rule-based goal decomposition"""
        # Split on common conjunctions
        parts = []

        # Split on "and"
        if " and " in description.lower():
            parts = [p.strip() for p in description.lower().split(" and ")]
        # Split on ", then"
        elif ", then " in description.lower():
            parts = [p.strip() for p in description.lower().split(", then ")]
        # Split on numbered steps
        elif any(f"{i}." in description for i in range(1, 10)):
            import re
            parts = re.split(r'\d+\.', description)[1:]  # Skip first empty element
            parts = [p.strip() for p in parts if p.strip()]
        else:
            # Can't decompose, return as single goal
            parts = [description]

        return parts[:5]  # Max 5 sub-goals

    async def _execute_goal_with_iterations(self, goal: Goal) -> Any:
        """
        Execute goal with iteration limits and safety checks.

        Args:
            goal: Goal to execute

        Returns:
            Execution result
        """
        print(f"[AutonomousCoordinator] Executing: {goal.description}")

        for iteration in range(self.safety_bounds.max_iterations):
            # Check safety bounds
            if not self._check_safety_bounds():
                print("[AutonomousCoordinator] Safety bounds exceeded")
                goal.status = GoalStatus.BLOCKED
                return None

            # Execute one iteration
            try:
                # In production, this would call actual execution logic
                # For now, simulate execution
                await asyncio.sleep(0.1)  # Simulate work

                goal.iterations += 1
                self.state.iteration_count += 1

                # Simulate success after a few iterations
                if iteration >= 2:
                    goal.status = GoalStatus.COMPLETED
                    return f"Completed: {goal.description}"

            except Exception as e:
                self.state.consecutive_failures += 1

                if self.state.consecutive_failures >= self.safety_bounds.max_consecutive_failures:
                    print(f"[AutonomousCoordinator] Max consecutive failures reached")
                    goal.status = GoalStatus.FAILED
                    goal.error = f"Max failures: {str(e)}"
                    return None

            # Cooldown between iterations
            await asyncio.sleep(self.safety_bounds.timeout_between_iterations_seconds)

        # Max iterations reached
        print(f"[AutonomousCoordinator] Max iterations reached for: {goal.description}")
        goal.status = GoalStatus.FAILED
        goal.error = "Max iterations exceeded"
        return None

    def _check_safety_bounds(self) -> bool:
        """Check if safety bounds are exceeded"""

        # Check iteration limit
        if self.state.iteration_count >= self.safety_bounds.max_iterations:
            return False

        # Check cost limit
        if self.state.total_cost_usd >= self.safety_bounds.max_total_cost_usd:
            return False

        # Check execution time
        if self.state.started_at:
            elapsed = datetime.now() - self.state.started_at
            max_time = timedelta(minutes=self.safety_bounds.max_execution_time_minutes)
            if elapsed >= max_time:
                return False

        # Check consecutive failures
        if self.state.consecutive_failures >= self.safety_bounds.max_consecutive_failures:
            return False

        return True

    # =========================================================================
    # Monitoring and Reporting
    # =========================================================================

    def get_state(self) -> Dict[str, Any]:
        """Get current autonomous agent state"""
        return {
            "iteration_count": self.state.iteration_count,
            "depth": self.state.depth,
            "total_cost_usd": self.state.total_cost_usd,
            "consecutive_failures": self.state.consecutive_failures,
            "goals_completed": self.state.goals_completed,
            "improvements_applied": self.state.improvements_applied,
            "active_goals": len(self.active_goals),
            "total_goals": len(self.goals),
        }

    def reset(self):
        """Reset autonomous agent state"""
        self.state = AutonomousState()
        self.goals = {}
        self.active_goals = []
        print("[AutonomousCoordinator] State reset")


# =============================================================================
# Convenience Functions
# =============================================================================

def create_autonomous_coordinator(
    safety_bounds: Optional[SafetyBounds] = None,
) -> AutonomousCoordinator:
    """
    Create autonomous coordinator with default configuration.

    Args:
        safety_bounds: Optional custom safety bounds

    Returns:
        Configured AutonomousCoordinator
    """
    return AutonomousCoordinator(safety_bounds=safety_bounds)


# =============================================================================
# CLI for Testing
# =============================================================================

async def test_autonomous_coordinator():
    """Test autonomous coordinator"""
    print("\n" + "="*60)
    print("Autonomous Coordinator - Test Mode")
    print("="*60 + "\n")

    # Create coordinator
    coordinator = create_autonomous_coordinator()

    # Test 1: Self-improvement cycle
    print("\nTest 1: Self-Improvement Cycle")
    print("-" * 60)
    if coordinator.self_refiner and coordinator.auto_improver:
        result = await coordinator.run_improvement_cycle()
        print(f"Result: {result}")
    else:
        print("Self-improvement systems not available (expected in test mode)")

    # Test 2: Goal decomposition
    print("\nTest 2: Goal Decomposition and Execution")
    print("-" * 60)
    result = await coordinator.execute_goal_with_decomposition(
        goal_description="Implement new API endpoint, write tests, and update documentation",
        max_depth=2
    )
    print(f"Result: {result}")

    # Test 3: Check state
    print("\nTest 3: Agent State")
    print("-" * 60)
    state = coordinator.get_state()
    for key, value in state.items():
        print(f"  {key}: {value}")

    print("\nTests complete!")


if __name__ == "__main__":
    asyncio.run(test_autonomous_coordinator())
