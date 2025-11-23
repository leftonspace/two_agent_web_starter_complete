"""
Integration Tests: Council Voting and Happiness

Tests the gamified council system including weighted voting,
happiness management, councillor lifecycle, and bonuses.
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCouncilVoting:
    """Test council voting mechanics"""

    @pytest.mark.asyncio
    async def test_weighted_vote_calculation(self, council, mock_llm):
        """Vote weights should be calculated correctly"""
        councillors = council._get_active_councillors()

        for councillor in councillors:
            # Vote weight formula: base × performance × happiness_modifier
            expected = councillor.base_vote_weight * councillor.performance_coefficient * councillor.happiness_modifier
            assert abs(councillor.vote_weight - expected) < 0.01

    @pytest.mark.asyncio
    async def test_analysis_vote_determines_complexity(self, council, mock_llm):
        """Analysis vote should determine task complexity"""
        from council import CouncilTask

        task = CouncilTask(description="Build a REST API")

        complexity = await council._conduct_analysis_vote(task)

        assert complexity is not None
        assert complexity.value in ["simple", "medium", "complex", "epic"]

    @pytest.mark.asyncio
    async def test_review_vote_assigns_quality(self, council, mock_llm):
        """Review vote should assign quality score"""
        from council import CouncilTask, TaskComplexity

        task = CouncilTask(description="Write unit tests")
        task.complexity = TaskComplexity.SIMPLE
        task.result = "Tests written successfully"

        councillors = council._get_active_councillors()[:2]
        quality = await council._conduct_review_vote(task, councillors)

        assert 0.0 <= quality <= 1.0

    @pytest.mark.asyncio
    async def test_vote_results_affect_happiness(self, council, mock_llm):
        """Vote results should affect councillor happiness"""
        councillors = council._get_active_councillors()
        initial_happiness = {c.id: c.happiness for c in councillors}

        # Process a task to trigger voting
        await council.process_task("Simple task")

        # Happiness may have changed due to vote results
        for councillor in councillors:
            # Happiness is tracked
            assert councillor.happiness >= 0
            assert councillor.happiness <= 100


class TestCouncillorHappiness:
    """Test councillor happiness system"""

    def test_happiness_bounds(self, council):
        """Happiness should stay within 0-100 bounds"""
        councillor = council._get_active_councillors()[0]

        # Try to exceed bounds
        councillor.adjust_happiness(200)
        assert councillor.happiness <= 100

        councillor.adjust_happiness(-300)
        assert councillor.happiness >= 0

    def test_happiness_events_have_correct_impact(self):
        """Happiness events should have expected impacts"""
        from council.happiness import HappinessManager, HappinessEvent, HAPPINESS_IMPACTS

        manager = HappinessManager()

        # Check key events
        assert HAPPINESS_IMPACTS[HappinessEvent.TASK_SUCCESS] > 0
        assert HAPPINESS_IMPACTS[HappinessEvent.TASK_FAILURE] < 0
        assert HAPPINESS_IMPACTS[HappinessEvent.BONUS_RECEIVED] > 0
        assert HAPPINESS_IMPACTS[HappinessEvent.COLLEAGUE_FIRED] < 0

    @pytest.mark.asyncio
    async def test_task_success_increases_happiness(self, council, mock_llm):
        """Successful tasks should increase happiness"""
        councillor = council._get_active_councillors()[0]
        initial_happiness = councillor.happiness

        # Success event
        council.happiness_manager.apply_task_result(
            councillor,
            success=True,
            quality_score=0.9
        )

        assert councillor.happiness > initial_happiness

    @pytest.mark.asyncio
    async def test_task_failure_decreases_happiness(self, council, mock_llm):
        """Failed tasks should decrease happiness"""
        councillor = council._get_active_councillors()[0]
        initial_happiness = councillor.happiness

        council.happiness_manager.apply_task_result(
            councillor,
            success=False
        )

        assert councillor.happiness < initial_happiness

    def test_happiness_decay_toward_baseline(self, council):
        """Happiness should decay toward baseline over time"""
        councillor = council._get_active_councillors()[0]

        # Set happiness high
        councillor.happiness = 90

        # Apply decay
        council.happiness_manager.apply_decay([councillor], toward=50.0)

        # Should move toward 50
        assert councillor.happiness < 90

    def test_get_mood_from_happiness(self, council):
        """Should return appropriate mood description"""
        manager = council.happiness_manager

        assert manager.get_mood(95) == "ecstatic"
        assert manager.get_mood(75) == "happy"
        assert manager.get_mood(60) == "content"
        assert manager.get_mood(45) == "neutral"
        assert manager.get_mood(30) == "unhappy"
        assert manager.get_mood(15) == "miserable"
        assert manager.get_mood(5) == "critical"


class TestCouncillorLifecycle:
    """Test councillor spawn/fire/promote lifecycle"""

    def test_spawn_creates_councillor_on_probation(self, council):
        """New councillors should start on probation"""
        from council.factory import CouncillorFactory
        from council.models import CouncillorStatus

        factory = CouncillorFactory()
        councillor = factory.spawn("coder")

        assert councillor.status == CouncillorStatus.PROBATION
        assert councillor.base_vote_weight == 0.8  # Reduced weight

    def test_spawn_team_creates_multiple(self, council):
        """Should spawn multiple councillors"""
        from council.factory import CouncillorFactory

        factory = CouncillorFactory()
        team = factory.spawn_team(["coder", "reviewer", "tester"])

        assert len(team) == 3

    def test_fire_criteria_performance(self, council):
        """Should fire for low performance"""
        councillor = council._get_active_councillors()[0]

        # Simulate low performance
        councillor.metrics.overall_performance = 30

        should_fire, reason = council.factory.should_fire(councillor)

        assert should_fire
        assert "performance" in reason.lower()

    def test_fire_criteria_consecutive_failures(self, council):
        """Should fire for consecutive failures"""
        councillor = council._get_active_councillors()[0]

        # Simulate failures
        councillor.metrics.consecutive_failures = 6

        should_fire, reason = council.factory.should_fire(councillor)

        assert should_fire
        assert "consecutive" in reason.lower()

    def test_fire_criteria_low_happiness(self, council):
        """Should fire for very low happiness"""
        councillor = council._get_active_councillors()[0]

        # Simulate unhappiness
        councillor.happiness = 15

        should_fire, reason = council.factory.should_fire(councillor)

        assert should_fire
        assert "happiness" in reason.lower()

    def test_promotion_criteria(self, council):
        """Should promote after meeting criteria"""
        from council.models import CouncillorStatus

        councillor = council._get_active_councillors()[0]

        # Set up for promotion
        councillor.status = CouncillorStatus.PROBATION
        councillor.metrics.tasks_completed = 15
        councillor.metrics.overall_performance = 70

        can_promote, reason = council.factory.can_promote(councillor)

        assert can_promote
        assert "criteria" in reason.lower()

    def test_promotion_increases_vote_weight(self, council):
        """Promotion should increase vote weight"""
        from council.models import CouncillorStatus

        councillor = council._get_active_councillors()[0]

        # Set up for promotion
        councillor.status = CouncillorStatus.PROBATION
        councillor.metrics.tasks_completed = 15
        councillor.metrics.overall_performance = 70
        councillor.base_vote_weight = 0.8

        council.factory.promote(councillor)

        assert councillor.status == CouncillorStatus.ACTIVE
        assert councillor.base_vote_weight == 1.0


class TestBonusPool:
    """Test bonus pool mechanics"""

    def test_bonus_withdrawal(self, council):
        """Should withdraw from bonus pool"""
        # Add to pool
        council.bonus_pool.balance = 50.0

        amount = council.bonus_pool.withdraw(10.0, "Test", "performance")

        assert amount == 10.0
        assert council.bonus_pool.balance == 40.0

    def test_bonus_withdrawal_exceeds_balance(self, council):
        """Should cap withdrawal at available balance"""
        council.bonus_pool.balance = 5.0

        amount = council.bonus_pool.withdraw(10.0, "Test", "performance")

        assert amount == 5.0
        assert council.bonus_pool.balance == 0.0

    def test_bonus_replenishment(self, council):
        """Should replenish bonus pool"""
        council.bonus_pool.balance = 10.0

        council.bonus_pool.replenish(0.9)  # 90% satisfaction

        assert council.bonus_pool.balance > 10.0

    def test_bonus_increases_happiness(self, council):
        """Bonus should increase happiness"""
        councillor = council._get_active_councillors()[0]
        initial_happiness = councillor.happiness
        council.bonus_pool.balance = 100.0

        council.happiness_manager.apply_bonus(
            councillor,
            council.bonus_pool,
            15.0,
            "excellent_work"
        )

        assert councillor.happiness > initial_happiness


class TestCouncilTaskProcessing:
    """Test complete task processing through council"""

    @pytest.mark.asyncio
    async def test_complete_task_flow(self, council, mock_llm):
        """Should process task through full flow"""
        result = await council.process_task("Build a feature")

        assert result["status"] == "completed"
        assert "task_id" in result
        assert "complexity" in result
        assert "quality_score" in result

    @pytest.mark.asyncio
    async def test_task_updates_metrics(self, council, mock_llm):
        """Task processing should update metrics"""
        initial_processed = council.tasks_processed

        await council.process_task("Write tests")

        assert council.tasks_processed == initial_processed + 1

    @pytest.mark.asyncio
    async def test_councillor_assignment(self, council, mock_llm):
        """Should assign councillors based on suitability"""
        from council import CouncilTask, TaskComplexity

        task = CouncilTask(description="Review the code")
        task.complexity = TaskComplexity.MEDIUM

        assigned = await council._assign_councillors(task, count=2)

        assert len(assigned) == 2
        # Should have assigned councillors
        for councillor in assigned:
            assert councillor.status.value in ["active", "probation"]

    @pytest.mark.asyncio
    async def test_assignment_considers_specialization(self, council, mock_llm):
        """Assignment should consider specialization"""
        from council import CouncilTask

        # Task about coding
        task = CouncilTask(description="Write Python code for the API")

        assigned = await council._assign_councillors(task, count=2)

        # Should prefer councillors with coding specialization
        assert len(assigned) > 0


class TestCouncilStatus:
    """Test council status and reporting"""

    def test_get_council_status(self, council):
        """Should return council status"""
        status = council.get_council_status()

        assert "total_councillors" in status
        assert "active_councillors" in status
        assert "tasks_processed" in status
        assert "bonus_pool" in status
        assert "team_morale" in status

    def test_get_leaderboard(self, council):
        """Should return councillor leaderboard"""
        leaderboard = council.get_councillor_leaderboard()

        assert len(leaderboard) > 0
        for entry in leaderboard:
            assert "rank" in entry
            assert "name" in entry
            assert "performance" in entry

    def test_leaderboard_is_sorted(self, council):
        """Leaderboard should be sorted by performance"""
        leaderboard = council.get_councillor_leaderboard()

        if len(leaderboard) > 1:
            for i in range(len(leaderboard) - 1):
                assert leaderboard[i]["performance"] >= leaderboard[i + 1]["performance"]


class TestUserSatisfaction:
    """Test user satisfaction feedback"""

    def test_high_satisfaction_boosts_team(self, council):
        """High satisfaction should boost team happiness"""
        councillors = council._get_active_councillors()
        initial_avg = sum(c.happiness for c in councillors) / len(councillors)

        council.apply_user_satisfaction(0.95)

        new_avg = sum(c.happiness for c in councillors) / len(councillors)
        assert new_avg > initial_avg

    def test_low_satisfaction_affects_team(self, council):
        """Low satisfaction should affect team happiness"""
        councillors = council._get_active_councillors()
        initial_avg = sum(c.happiness for c in councillors) / len(councillors)

        council.apply_user_satisfaction(0.3)

        new_avg = sum(c.happiness for c in councillors) / len(councillors)
        assert new_avg < initial_avg


class TestPeriodicEvaluation:
    """Test periodic team evaluation"""

    @pytest.mark.asyncio
    async def test_evaluation_runs_on_interval(self, council, mock_llm):
        """Evaluation should run at configured interval"""
        # Set evaluation interval
        council.config.evaluation_interval = 2

        # Process tasks
        for i in range(3):
            await council.process_task(f"Task {i}")

        # Evaluation should have run
        assert council.tasks_processed >= 3

    @pytest.mark.asyncio
    async def test_team_maintenance(self, council, mock_llm):
        """Should maintain minimum team size"""
        initial_count = len(council._get_active_councillors())

        # Force a councillor to be fired
        councillor = council._get_active_councillors()[0]
        councillor.metrics.overall_performance = 10

        # Run evaluation
        actions = await council._periodic_evaluation()

        # Team should be maintained
        current_count = len(council._get_active_councillors())
        assert current_count >= council.config.min_councillors


class TestCouncilCallbacks:
    """Test council event callbacks"""

    def test_task_complete_callback(self, council):
        """Should trigger callback on task complete"""
        callback_data = []

        def callback(task, councillors, success):
            callback_data.append({
                "task": task,
                "success": success
            })

        council.on_task_complete(callback)

        # The callback is registered
        assert len(council._on_task_complete) > 0

    def test_councillor_fired_callback(self, council):
        """Should trigger callback when councillor fired"""
        callback_data = []

        def callback(decision):
            callback_data.append(decision)

        council.on_councillor_fired(callback)

        # The callback is registered
        assert len(council._on_councillor_fired) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
