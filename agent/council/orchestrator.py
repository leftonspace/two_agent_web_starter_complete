"""
Council System - Main Orchestrator

The Council Leader (JARVIS) that manages the councillor pool,
coordinates voting, and orchestrates task execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import asyncio

from .models import (
    Councillor, CouncillorStatus, Specialization,
    Vote, VotingSession, VoteType,
    CouncilTask, TaskComplexity, BonusPool
)
from .voting import VotingManager, VotingConfig, conduct_vote
from .happiness import HappinessManager, HappinessEvent
from .factory import CouncillorFactory, FactoryConfig


@dataclass
class CouncilConfig:
    """Configuration for the Council"""
    min_councillors: int = 3
    max_councillors: int = 10
    default_templates: List[str] = field(default_factory=lambda: ["coder", "reviewer", "tester"])
    evaluation_interval: int = 10  # Tasks between evaluations
    bonus_on_success: float = 5.0
    bonus_on_excellent: float = 15.0
    user_satisfaction_bonus: float = 10.0


class CouncilOrchestrator:
    """
    The Council Leader - JARVIS

    Coordinates a council of specialist agents through:
    - Weighted voting for decisions
    - Performance-based task assignment
    - Happiness management
    - Fire/spawn lifecycle management

    Example:
        council = CouncilOrchestrator()
        await council.initialize()
        result = await council.process_task("Build a REST API")
    """

    def __init__(self, config: Optional[CouncilConfig] = None):
        self.config = config or CouncilConfig()

        # Core components
        self.councillors: List[Councillor] = []
        self.voting_manager = VotingManager()
        self.happiness_manager = HappinessManager()
        self.factory = CouncillorFactory(FactoryConfig(
            min_councillors=self.config.min_councillors,
            max_councillors=self.config.max_councillors,
            default_templates=self.config.default_templates
        ))

        # State
        self.bonus_pool = BonusPool()
        self.tasks_processed: int = 0
        self.task_history: List[CouncilTask] = []
        self._initialized: bool = False

        # Callbacks
        self._on_task_complete: List[Callable] = []
        self._on_councillor_fired: List[Callable] = []
        self._on_vote_complete: List[Callable] = []

        # LLM function for councillor execution
        self._llm_func: Optional[Callable] = None

    async def initialize(
        self,
        llm_func: Optional[Callable] = None,
        initial_templates: Optional[List[str]] = None
    ):
        """
        Initialize the council with councillors.

        Args:
            llm_func: Optional LLM function for councillor execution
            initial_templates: Optional list of templates for initial team
        """
        self._llm_func = llm_func

        # Set up factory with execution function
        if llm_func:
            self.factory.set_execute_func(self._create_execute_func(llm_func))

        # Spawn initial team
        templates = initial_templates or self.config.default_templates
        self.councillors = self.factory.spawn_team(templates)

        self._initialized = True

    def _create_execute_func(self, llm_func: Callable) -> Callable:
        """Create an execution function for councillors"""
        async def execute(task: str, context: Dict[str, Any]) -> str:
            councillor_name = context.get("councillor_name", "Unknown")
            specializations = context.get("specializations", [])

            prompt = f"""You are {councillor_name}, a specialist in {', '.join(specializations)}.

Task: {task}

Provide a focused response based on your specialization. Be concise and practical."""

            return await llm_func(prompt)

        return execute

    async def process_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a task through the council.

        Flow:
        1. Analysis vote - determine complexity
        2. Assignment - select councillors based on specialization
        3. Execution - councillors work on task
        4. Review vote - evaluate quality
        5. Update metrics and happiness

        Args:
            task_description: The task to process
            context: Optional additional context

        Returns:
            Task result with metadata
        """
        if not self._initialized:
            await self.initialize()

        # Create task record
        task = CouncilTask(
            description=task_description,
            metadata=context or {}
        )

        # Initialize assigned list in case of early exception
        assigned = []

        try:
            # Step 1: Analysis Vote
            task.complexity = await self._conduct_analysis_vote(task)
            print(f"[Council] Task complexity: {task.complexity.value}")

            # Step 2: Assignment
            assigned = await self._assign_councillors(task)
            task.assigned_councillors = [c.id for c in assigned]
            print(f"[Council] Assigned: {[c.name for c in assigned]}")

            # Step 3: Execution
            task.status = "in_progress"
            result = await self._execute_task(task, assigned)
            task.result = result

            # Step 4: Review Vote
            quality = await self._conduct_review_vote(task, assigned)
            task.quality_score = quality
            print(f"[Council] Quality score: {quality:.2f}")

            # Step 5: Update metrics and happiness
            await self._finalize_task(task, assigned, success=True)

            task.status = "completed"
            task.completed_at = datetime.now()

        except Exception as e:
            task.status = "failed"
            task.metadata["error"] = str(e)
            await self._finalize_task(task, assigned, success=False)

        # Record task
        self.task_history.append(task)
        self.tasks_processed += 1

        # Periodic evaluation
        if self.tasks_processed % self.config.evaluation_interval == 0:
            await self._periodic_evaluation()

        return {
            "task_id": task.id,
            "status": task.status,
            "result": task.result,
            "complexity": task.complexity.value if task.complexity else None,
            "quality_score": task.quality_score,
            "assigned_councillors": task.assigned_councillors,
        }

    async def _conduct_analysis_vote(self, task: CouncilTask) -> TaskComplexity:
        """Conduct analysis vote to determine task complexity"""
        active = self._get_active_councillors()

        winner, session = await conduct_vote(
            councillors=active,
            vote_type=VoteType.ANALYSIS,
            question=f"How should we approach: {task.description}",
            options=[c.value for c in TaskComplexity]
        )

        task.analysis_vote = session

        # Update vote results happiness
        for vote in session.votes:
            councillor = self._get_councillor_by_id(vote.councillor_id)
            if councillor:
                won = vote.choice == winner
                councillor.metrics.record_vote_result(won)
                self.happiness_manager.apply_vote_result(councillor, won)

        return TaskComplexity(winner)

    async def _assign_councillors(
        self,
        task: CouncilTask,
        count: int = 2
    ) -> List[Councillor]:
        """
        Assign councillors to a task based on specialization and performance.

        Args:
            task: The task to assign
            count: Number of councillors to assign

        Returns:
            List of assigned councillors
        """
        active = self._get_active_councillors()

        # Score councillors by relevance
        scored = []
        for c in active:
            score = self._calculate_assignment_score(c, task)
            scored.append((c, score))

        # Sort by score descending
        scored.sort(key=lambda x: -x[1])

        # Select top councillors
        assigned = [c for c, _ in scored[:count]]

        return assigned

    def _calculate_assignment_score(
        self,
        councillor: Councillor,
        task: CouncilTask
    ) -> float:
        """Calculate assignment suitability score"""
        score = 0.0

        # Base score from vote weight
        score += councillor.vote_weight * 10

        # Performance bonus
        score += councillor.metrics.overall_performance / 10

        # Specialization matching (simplified)
        task_lower = task.description.lower()
        for spec in councillor.specializations:
            if spec.value in task_lower:
                score += 20

        # Recent success bonus
        if councillor.metrics.consecutive_successes > 0:
            score += councillor.metrics.consecutive_successes * 2

        return score

    async def _execute_task(
        self,
        task: CouncilTask,
        councillors: List[Councillor]
    ) -> str:
        """Execute task with assigned councillors"""
        results = []

        for councillor in councillors:
            context = {
                "councillor_name": councillor.name,
                "specializations": [s.value for s in councillor.specializations],
                "task_complexity": task.complexity.value if task.complexity else "unknown",
            }

            result = await councillor.execute(task.description, context)
            results.append(f"**{councillor.name}:**\n{result}")

        return "\n\n".join(results)

    async def _conduct_review_vote(
        self,
        task: CouncilTask,
        workers: List[Councillor]
    ) -> float:
        """Conduct review vote for task quality"""
        # Get reviewers (councillors not assigned to task)
        active = self._get_active_councillors()
        reviewers = [c for c in active if c not in workers]

        if not reviewers:
            reviewers = active[:2]  # Use any available if no others

        winner, session = await conduct_vote(
            councillors=reviewers,
            vote_type=VoteType.REVIEW,
            question=f"Quality of work on: {task.description}",
            options=["excellent", "good", "acceptable", "needs_revision", "reject"]
        )

        task.review_vote = session

        # Convert to quality score
        quality_map = {
            "excellent": 1.0,
            "good": 0.8,
            "acceptable": 0.6,
            "needs_revision": 0.4,
            "reject": 0.2
        }

        return quality_map.get(winner, 0.5)

    async def _finalize_task(
        self,
        task: CouncilTask,
        councillors: List[Councillor],
        success: bool
    ):
        """Finalize task: update metrics, happiness, bonuses"""
        quality = task.quality_score or 0.5

        for councillor in councillors:
            if success:
                councillor.metrics.record_task_success(quality, 0.8)
                self.happiness_manager.apply_task_result(
                    councillor,
                    success=True,
                    quality_score=quality,
                    was_challenging=(task.complexity == TaskComplexity.COMPLEX)
                )

                # Award bonus for excellent work
                if quality >= 0.9:
                    self.happiness_manager.apply_bonus(
                        councillor,
                        self.bonus_pool,
                        self.config.bonus_on_excellent,
                        "excellent_work"
                    )
                elif quality >= 0.7:
                    self.happiness_manager.apply_bonus(
                        councillor,
                        self.bonus_pool,
                        self.config.bonus_on_success,
                        "task_success"
                    )
            else:
                councillor.metrics.record_task_failure()
                self.happiness_manager.apply_task_result(councillor, success=False)

        # Trigger callbacks
        for callback in self._on_task_complete:
            callback(task, councillors, success)

    async def _periodic_evaluation(self):
        """Periodic team evaluation and maintenance"""
        actions = self.factory.maintain_team(self.councillors)

        # Apply team events for fired councillors
        if actions["fired"]:
            self.happiness_manager.apply_team_event(
                self.councillors,
                HappinessEvent.COLLEAGUE_FIRED
            )

            for decision in actions["fired"]:
                for callback in self._on_councillor_fired:
                    callback(decision)

        # Apply team events for new councillors
        if actions["spawned"]:
            self.happiness_manager.apply_team_event(
                self.councillors,
                HappinessEvent.NEW_COLLEAGUE
            )

        # Add new councillors to the team (fix council shrinkage bug)
        if actions["new_councillors"]:
            self.councillors.extend(actions["new_councillors"])

        # Apply happiness decay
        self.happiness_manager.apply_decay(self.councillors)

        return actions

    def apply_user_satisfaction(self, satisfaction: float):
        """
        Apply user satisfaction feedback.

        Args:
            satisfaction: Satisfaction score (0-1)
        """
        # Replenish bonus pool
        self.bonus_pool.replenish(satisfaction)

        # Team happiness based on satisfaction
        if satisfaction >= 0.8:
            self.happiness_manager.apply_team_event(
                self.councillors,
                HappinessEvent.TEAM_SUCCESS
            )
        elif satisfaction < 0.4:
            self.happiness_manager.apply_team_event(
                self.councillors,
                HappinessEvent.TEAM_FAILURE
            )

    def _get_active_councillors(self) -> List[Councillor]:
        """Get list of active councillors"""
        return [
            c for c in self.councillors
            if c.status in [CouncillorStatus.ACTIVE, CouncillorStatus.PROBATION]
        ]

    def _get_councillor_by_id(self, councillor_id: str) -> Optional[Councillor]:
        """Get councillor by ID"""
        for c in self.councillors:
            if c.id == councillor_id:
                return c
        return None

    def get_council_status(self) -> Dict[str, Any]:
        """Get current council status"""
        active = self._get_active_councillors()

        return {
            "total_councillors": len(self.councillors),
            "active_councillors": len(active),
            "tasks_processed": self.tasks_processed,
            "bonus_pool": self.bonus_pool.balance,
            "team_morale": self.happiness_manager.get_team_morale(active),
            "councillors": [c.to_dict() for c in active],
        }

    def get_councillor_leaderboard(self) -> List[Dict[str, Any]]:
        """Get councillors ranked by performance"""
        active = self._get_active_councillors()
        ranked = sorted(active, key=lambda c: -c.metrics.overall_performance)

        return [
            {
                "rank": i + 1,
                "name": c.name,
                "performance": c.metrics.overall_performance,
                "vote_weight": c.vote_weight,
                "happiness": c.happiness,
                "tasks_completed": c.metrics.tasks_completed,
            }
            for i, c in enumerate(ranked)
        ]

    # Event registration
    def on_task_complete(self, callback: Callable):
        """Register task complete callback"""
        self._on_task_complete.append(callback)

    def on_councillor_fired(self, callback: Callable):
        """Register councillor fired callback"""
        self._on_councillor_fired.append(callback)

    def on_vote_complete(self, callback: Callable):
        """Register vote complete callback"""
        self._on_vote_complete.append(callback)


# Convenience function
async def create_council(
    llm_func: Optional[Callable] = None,
    templates: Optional[List[str]] = None,
    config: Optional[CouncilConfig] = None
) -> CouncilOrchestrator:
    """
    Create and initialize a council.

    Args:
        llm_func: Optional LLM function for councillor execution
        templates: Optional list of councillor templates
        config: Optional council configuration

    Returns:
        Initialized CouncilOrchestrator
    """
    council = CouncilOrchestrator(config)
    await council.initialize(llm_func, templates)
    return council
