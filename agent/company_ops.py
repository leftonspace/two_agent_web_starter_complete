"""
PHASE 4.3: CompanyOps - Multi-Agent Coordination

Coordinates multiple specialist agents working together:
- Task decomposition into subtasks
- Agent assignment based on expertise
- Parallel execution coordination
- Result aggregation and conflict resolution
- Communication protocols between agents

Usage:
    >>> from agent import company_ops
    >>> company = company_ops.CompanyOps()
    >>> result = company.execute_collaborative_task(
    ...     task="Build a full-stack web application with authentication",
    ...     budget_usd=50.0
    ... )
    >>> print(f"Completed in {result['agents_used']} agents")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Local imports
try:
    import specialists
    SPECIALISTS_AVAILABLE = True
except ImportError:
    SPECIALISTS_AVAILABLE = False

try:
    import specialist_market
    MARKET_AVAILABLE = True
except ImportError:
    MARKET_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Task Decomposition
# ══════════════════════════════════════════════════════════════════════


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class SubTask:
    """A subtask that can be assigned to a specialist."""

    id: str
    description: str
    specialist_type: Optional[str] = None  # Recommended specialist type
    dependencies: List[str] = field(default_factory=list)  # IDs of tasks that must complete first
    estimated_cost_usd: float = 0.0
    estimated_duration_seconds: float = 0.0
    priority: int = 1  # 1 = highest, 5 = lowest
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    assigned_to: Optional[str] = None  # Specialist type assigned to this task
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "specialist_type": self.specialist_type,
            "dependencies": self.dependencies,
            "estimated_cost_usd": self.estimated_cost_usd,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "priority": self.priority,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class TaskDecomposition:
    """Result of decomposing a complex task."""

    subtasks: List[SubTask]
    complexity: TaskComplexity
    total_estimated_cost_usd: float
    total_estimated_duration_seconds: float
    requires_coordination: bool  # True if subtasks need to be integrated
    reasoning: List[str]  # Explanation of decomposition strategy

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subtasks": [st.to_dict() for st in self.subtasks],
            "complexity": self.complexity.value,
            "total_estimated_cost_usd": self.total_estimated_cost_usd,
            "total_estimated_duration_seconds": self.total_estimated_duration_seconds,
            "requires_coordination": self.requires_coordination,
            "reasoning": self.reasoning,
        }


# ══════════════════════════════════════════════════════════════════════
# Agent Communication
# ══════════════════════════════════════════════════════════════════════


@dataclass
class AgentMessage:
    """Message passed between agents."""

    from_agent: str  # Specialist type sending message
    to_agent: str  # Specialist type receiving message
    message_type: str  # request, response, notification, question
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat() + "Z",
            "context": self.context,
        }


# ══════════════════════════════════════════════════════════════════════
# CompanyOps System
# ══════════════════════════════════════════════════════════════════════


class CompanyOps:
    """Multi-agent coordination system."""

    def __init__(
        self,
        use_market: bool = True,
        max_parallel_agents: int = 3,
        enable_agent_communication: bool = True
    ):
        """
        Initialize CompanyOps.

        Args:
            use_market: Whether to use specialist market for recommendations
            max_parallel_agents: Maximum number of agents to run in parallel
            enable_agent_communication: Allow agents to communicate with each other
        """
        self.use_market = use_market and MARKET_AVAILABLE
        self.max_parallel_agents = max_parallel_agents
        self.enable_agent_communication = enable_agent_communication

        # Initialize market if available
        self.market = None
        if self.use_market:
            self.market = specialist_market.SpecialistMarket()

        # Message queue for agent communication
        self.message_queue: List[AgentMessage] = []

    def decompose_task(
        self,
        task: str,
        budget_usd: Optional[float] = None
    ) -> TaskDecomposition:
        """
        Decompose a complex task into subtasks.

        Args:
            task: Task description
            budget_usd: Total budget available (None = unlimited)

        Returns:
            TaskDecomposition with subtasks and estimates
        """
        # Simple rule-based decomposition
        # In a real system, this would use an LLM to intelligently decompose tasks

        task_lower = task.lower()
        subtasks: List[SubTask] = []
        reasoning: List[str] = []

        # Detect full-stack application patterns
        if any(kw in task_lower for kw in ["full-stack", "full stack", "web app", "application"]):
            reasoning.append("Detected full-stack application - decomposing into frontend and backend")

            # Backend subtask
            if any(kw in task_lower for kw in ["api", "backend", "server", "database"]):
                subtasks.append(SubTask(
                    id="backend",
                    description=f"Backend development: {task}",
                    specialist_type="backend",
                    priority=1,
                    estimated_cost_usd=10.0,
                    estimated_duration_seconds=600,
                ))

            # Frontend subtask (depends on backend)
            if any(kw in task_lower for kw in ["frontend", "ui", "dashboard", "interface"]):
                subtasks.append(SubTask(
                    id="frontend",
                    description=f"Frontend development: {task}",
                    specialist_type="frontend",
                    dependencies=["backend"] if any(st.id == "backend" for st in subtasks) else [],
                    priority=2,
                    estimated_cost_usd=10.0,
                    estimated_duration_seconds=600,
                ))

            # Authentication/Security
            if any(kw in task_lower for kw in ["auth", "authentication", "login", "security"]):
                subtasks.append(SubTask(
                    id="security",
                    description=f"Security implementation: {task}",
                    specialist_type="security",
                    priority=1,
                    estimated_cost_usd=8.0,
                    estimated_duration_seconds=450,
                ))

            # Testing
            subtasks.append(SubTask(
                id="qa",
                description=f"Quality assurance and testing: {task}",
                specialist_type="qa",
                dependencies=[st.id for st in subtasks],  # Depends on all previous
                priority=3,
                estimated_cost_usd=5.0,
                estimated_duration_seconds=300,
            ))

            # Deployment
            if any(kw in task_lower for kw in ["deploy", "production", "ci/cd", "pipeline"]):
                subtasks.append(SubTask(
                    id="devops",
                    description=f"Deployment and DevOps: {task}",
                    specialist_type="devops",
                    dependencies=["qa"],
                    priority=4,
                    estimated_cost_usd=7.0,
                    estimated_duration_seconds=400,
                ))

        # Detect data/ML patterns
        elif any(kw in task_lower for kw in ["data", "analytics", "ml", "machine learning", "model"]):
            reasoning.append("Detected data/ML task - decomposing into data and backend components")

            subtasks.append(SubTask(
                id="data",
                description=f"Data analysis and ML: {task}",
                specialist_type="data",
                priority=1,
                estimated_cost_usd=12.0,
                estimated_duration_seconds=700,
            ))

            if "dashboard" in task_lower or "visualization" in task_lower:
                subtasks.append(SubTask(
                    id="frontend",
                    description=f"Data visualization dashboard: {task}",
                    specialist_type="frontend",
                    dependencies=["data"],
                    priority=2,
                    estimated_cost_usd=8.0,
                    estimated_duration_seconds=500,
                ))

        # Single-domain task (no decomposition needed)
        else:
            reasoning.append("Task is single-domain - no decomposition needed")

            # Try to match to a specialist
            if SPECIALISTS_AVAILABLE:
                matches = specialists.select_specialist_for_task(task, min_score=0.3, max_specialists=1)
                specialist_type = matches[0][0].specialist_type.value if matches else "generic"
            else:
                specialist_type = "generic"

            subtasks.append(SubTask(
                id="main",
                description=task,
                specialist_type=specialist_type,
                priority=1,
                estimated_cost_usd=5.0,
                estimated_duration_seconds=300,
            ))

        # Calculate totals
        total_cost = sum(st.estimated_cost_usd for st in subtasks)
        total_duration = sum(st.estimated_duration_seconds for st in subtasks)

        # Determine complexity
        if len(subtasks) == 1:
            complexity = TaskComplexity.SIMPLE
        elif len(subtasks) == 2:
            complexity = TaskComplexity.MODERATE
        elif len(subtasks) <= 4:
            complexity = TaskComplexity.COMPLEX
        else:
            complexity = TaskComplexity.VERY_COMPLEX

        requires_coordination = len(subtasks) > 1

        # Check budget constraint
        if budget_usd is not None and total_cost > budget_usd:
            reasoning.append(f"Warning: Estimated cost ${total_cost:.2f} exceeds budget ${budget_usd:.2f}")

        return TaskDecomposition(
            subtasks=subtasks,
            complexity=complexity,
            total_estimated_cost_usd=total_cost,
            total_estimated_duration_seconds=total_duration,
            requires_coordination=requires_coordination,
            reasoning=reasoning,
        )

    def assign_agents(
        self,
        decomposition: TaskDecomposition,
        budget_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Assign specialists to subtasks.

        Args:
            decomposition: Task decomposition
            budget_usd: Available budget (None = unlimited)

        Returns:
            Dict with assignment details
        """
        assignments: Dict[str, str] = {}  # subtask_id -> specialist_type
        reasoning: List[str] = []

        for subtask in decomposition.subtasks:
            # Use recommended specialist if available
            if subtask.specialist_type:
                assignments[subtask.id] = subtask.specialist_type
                subtask.assigned_to = subtask.specialist_type
                reasoning.append(f"Assigned {subtask.id} to {subtask.specialist_type} (recommended)")
            else:
                # Try to find best specialist using market
                if self.use_market and self.market:
                    rec = self.market.recommend_specialist(
                        task=subtask.description,
                        budget_usd=budget_usd
                    )
                    if rec:
                        specialist_type = rec.specialist.specialist_type.value
                        assignments[subtask.id] = specialist_type
                        subtask.assigned_to = specialist_type
                        reasoning.append(f"Assigned {subtask.id} to {specialist_type} (market recommendation)")
                    else:
                        assignments[subtask.id] = "generic"
                        subtask.assigned_to = "generic"
                        reasoning.append(f"Assigned {subtask.id} to generic (no recommendation)")
                else:
                    assignments[subtask.id] = "generic"
                    subtask.assigned_to = "generic"
                    reasoning.append(f"Assigned {subtask.id} to generic (market unavailable)")

        return {
            "assignments": assignments,
            "reasoning": reasoning,
        }

    def execute_collaborative_task(
        self,
        task: str,
        budget_usd: Optional[float] = None,
        simulate: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a task using multiple coordinated agents.

        Args:
            task: Task description
            budget_usd: Maximum budget (None = unlimited)
            simulate: If True, simulate execution without running agents

        Returns:
            Dict with execution results
        """
        start_time = datetime.utcnow()

        # Step 1: Decompose task
        decomposition = self.decompose_task(task, budget_usd=budget_usd)

        # Step 2: Assign agents
        assignment_result = self.assign_agents(decomposition, budget_usd=budget_usd)

        # Step 3: Execute subtasks (simulated or real)
        execution_order = self._calculate_execution_order(decomposition.subtasks)

        results: Dict[str, Any] = {}
        total_cost = 0.0
        total_duration = 0.0
        agents_used: Set[str] = set()

        if simulate:
            # Simulate execution
            for subtask_id in execution_order:
                subtask = next(st for st in decomposition.subtasks if st.id == subtask_id)
                subtask.status = "completed"
                subtask.result = {
                    "simulated": True,
                    "message": f"Simulated execution of {subtask.description}"
                }
                results[subtask_id] = subtask.result
                total_cost += subtask.estimated_cost_usd
                total_duration += subtask.estimated_duration_seconds

                if subtask.assigned_to:
                    agents_used.add(subtask.assigned_to)
        else:
            # Real execution would happen here
            # For now, we just simulate
            for subtask_id in execution_order:
                subtask = next(st for st in decomposition.subtasks if st.id == subtask_id)
                subtask.status = "completed"
                subtask.result = {
                    "placeholder": True,
                    "message": f"Placeholder execution of {subtask.description}"
                }
                results[subtask_id] = subtask.result
                total_cost += subtask.estimated_cost_usd
                total_duration += subtask.estimated_duration_seconds

                if subtask.assigned_to:
                    agents_used.add(subtask.assigned_to)

        # Step 4: Aggregate results
        aggregated_result = self._aggregate_results(decomposition.subtasks, results)

        end_time = datetime.utcnow()
        actual_duration = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "task": task,
            "decomposition": decomposition.to_dict(),
            "assignments": assignment_result["assignments"],
            "execution_order": execution_order,
            "agents_used": list(agents_used),
            "results": results,
            "aggregated_result": aggregated_result,
            "total_cost_usd": total_cost,
            "estimated_duration_seconds": total_duration,
            "actual_duration_seconds": actual_duration,
            "simulated": simulate,
        }

    def _calculate_execution_order(self, subtasks: List[SubTask]) -> List[str]:
        """
        Calculate optimal execution order based on dependencies and priorities.

        Args:
            subtasks: List of subtasks

        Returns:
            List of subtask IDs in execution order
        """
        # Topological sort with priority
        order: List[str] = []
        completed: Set[str] = set()
        pending = {st.id: st for st in subtasks}

        while pending:
            # Find subtasks with no unmet dependencies
            ready = [
                st for st in pending.values()
                if all(dep in completed for dep in st.dependencies)
            ]

            if not ready:
                # Circular dependency or error - just take first pending
                ready = [next(iter(pending.values()))]

            # Sort by priority (lower number = higher priority)
            ready.sort(key=lambda st: st.priority)

            # Take highest priority task
            next_task = ready[0]
            order.append(next_task.id)
            completed.add(next_task.id)
            del pending[next_task.id]

        return order

    def _aggregate_results(
        self,
        subtasks: List[SubTask],
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple subtasks.

        Args:
            subtasks: List of subtasks
            results: Dict of subtask_id -> result

        Returns:
            Aggregated result
        """
        # Simple aggregation - combine all results
        aggregated = {
            "subtask_count": len(subtasks),
            "completed_count": sum(1 for st in subtasks if st.status == "completed"),
            "failed_count": sum(1 for st in subtasks if st.status == "failed"),
            "subtask_results": results,
        }

        # Check for conflicts or errors
        errors = [st.error for st in subtasks if st.error]
        if errors:
            aggregated["errors"] = errors

        return aggregated

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a message from one agent to another.

        Args:
            from_agent: Sending agent specialist type
            to_agent: Receiving agent specialist type
            message_type: Type of message (request, response, notification, question)
            content: Message content
            context: Optional context information
        """
        if not self.enable_agent_communication:
            return

        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            context=context,
        )

        self.message_queue.append(message)

    def get_messages_for_agent(self, agent_type: str) -> List[AgentMessage]:
        """
        Get all messages for a specific agent.

        Args:
            agent_type: Specialist type

        Returns:
            List of messages for this agent
        """
        return [msg for msg in self.message_queue if msg.to_agent == agent_type]

    def clear_messages(self) -> None:
        """Clear all messages from queue."""
        self.message_queue.clear()


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for CompanyOps."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CompanyOps - Multi-Agent Coordination",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Decompose command
    decompose_parser = subparsers.add_parser("decompose", help="Decompose a task into subtasks")
    decompose_parser.add_argument("task", type=str, help="Task description")
    decompose_parser.add_argument("--budget", type=float, help="Maximum budget in USD")

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute a collaborative task")
    execute_parser.add_argument("task", type=str, help="Task description")
    execute_parser.add_argument("--budget", type=float, help="Maximum budget in USD")
    execute_parser.add_argument("--simulate", action="store_true", help="Simulate execution")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    company = CompanyOps()

    if args.command == "decompose":
        decomposition = company.decompose_task(args.task, budget_usd=args.budget)

        print(f"\nTask Decomposition\n")
        print(f"Task: {args.task}")
        print(f"Complexity: {decomposition.complexity.value}")
        print(f"Total Estimated Cost: ${decomposition.total_estimated_cost_usd:.2f}")
        print(f"Total Estimated Duration: {decomposition.total_estimated_duration_seconds:.0f}s ({decomposition.total_estimated_duration_seconds / 60:.1f} min)")
        print(f"Requires Coordination: {decomposition.requires_coordination}")
        print(f"\nReasoning:")
        for reason in decomposition.reasoning:
            print(f"  - {reason}")
        print(f"\nSubtasks ({len(decomposition.subtasks)}):")
        for i, st in enumerate(decomposition.subtasks, 1):
            print(f"\n  {i}. {st.id.upper()}")
            print(f"     Description: {st.description}")
            print(f"     Specialist: {st.specialist_type or 'unassigned'}")
            print(f"     Priority: {st.priority}")
            print(f"     Estimated Cost: ${st.estimated_cost_usd:.2f}")
            print(f"     Estimated Duration: {st.estimated_duration_seconds:.0f}s")
            if st.dependencies:
                print(f"     Dependencies: {', '.join(st.dependencies)}")

    elif args.command == "execute":
        result = company.execute_collaborative_task(
            task=args.task,
            budget_usd=args.budget,
            simulate=args.simulate
        )

        print(f"\nCollaborative Task Execution\n")
        print(f"Task: {result['task']}")
        print(f"Success: {result['success']}")
        print(f"Simulated: {result['simulated']}")
        print(f"\nAgents Used: {', '.join(result['agents_used'])}")
        print(f"Total Cost: ${result['total_cost_usd']:.2f}")
        print(f"Duration: {result['actual_duration_seconds']:.2f}s")
        print(f"\nExecution Order: {' -> '.join(result['execution_order'])}")
        print(f"\nAggregated Result:")
        print(f"  Subtasks: {result['aggregated_result']['subtask_count']}")
        print(f"  Completed: {result['aggregated_result']['completed_count']}")
        print(f"  Failed: {result['aggregated_result']['failed_count']}")


if __name__ == "__main__":
    main()
