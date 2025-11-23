"""
Tests for Council System

Tests the gamified meta-orchestration council system including:
- Councillor models and metrics
- Weighted voting
- Happiness management
- Fire/spawn mechanics
- Council orchestration
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from council import (
    # Models
    Councillor, CouncillorStatus, Specialization, PerformanceMetrics,
    Vote, VotingSession, VoteType, TaskComplexity, BonusPool,
    # Voting
    VotingManager, VotingConfig, conduct_vote,
    # Happiness
    HappinessManager, HappinessEvent, HAPPINESS_IMPACTS,
    # Factory
    CouncillorFactory, FactoryConfig, SPECIALIZATION_TEMPLATES,
    # Orchestrator
    CouncilOrchestrator, CouncilConfig, create_council,
)


class TestCouncillorModel:
    """Tests for Councillor model"""

    def test_councillor_creation(self):
        """Test creating a councillor"""
        c = Councillor(
            name="Ada",
            specializations=[Specialization.CODING, Specialization.ARCHITECTURE]
        )
        assert c.name == "Ada"
        assert len(c.specializations) == 2
        assert c.status == CouncillorStatus.PROBATION
        assert c.happiness == 70.0

    def test_vote_weight_calculation(self):
        """Test vote weight calculation"""
        c = Councillor(name="Test")

        # Default should be around 1.25 (50% perf, 70% happiness)
        assert 1.0 <= c.vote_weight <= 1.5

        # High performance increases weight
        c.metrics.tasks_completed = 10
        c.metrics.total_quality_score = 9.0
        c.happiness = 90

        assert c.vote_weight > 1.5

    def test_performance_coefficient(self):
        """Test performance coefficient calculation"""
        c = Councillor(name="Test")

        # 50% performance = 1.0x coefficient
        assert 0.9 <= c.performance_coefficient <= 1.1

        # Record high performance
        for _ in range(10):
            c.metrics.record_task_success(0.9, 0.9)

        # Should be higher
        assert c.performance_coefficient > 1.5

    def test_happiness_modifier(self):
        """Test happiness modifier calculation"""
        c = Councillor(name="Test")

        # 70 happiness = 1.0x modifier
        c.happiness = 70
        assert 0.95 <= c.happiness_modifier <= 1.05

        # High happiness = higher modifier
        c.happiness = 100
        assert c.happiness_modifier > 1.2

        # Low happiness = lower modifier
        c.happiness = 20
        assert c.happiness_modifier < 0.8

    def test_fireable_criteria(self):
        """Test firing criteria"""
        c = Councillor(name="Test")

        # New councillor shouldn't be fireable
        assert not c.is_fireable

        # Low performance makes fireable
        c.metrics.tasks_failed = 10
        assert c.is_fireable

        # Reset
        c.metrics = PerformanceMetrics()

        # Consecutive failures make fireable
        for _ in range(5):
            c.metrics.record_task_failure()
        assert c.is_fireable

        # Reset
        c.metrics = PerformanceMetrics()

        # Low happiness makes fireable
        c.happiness = 15
        assert c.is_fireable


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics"""

    def test_success_rate(self):
        """Test success rate calculation"""
        m = PerformanceMetrics()

        # Default
        assert m.success_rate == 0.5

        m.record_task_success()
        m.record_task_success()
        m.record_task_failure()

        assert m.success_rate == pytest.approx(0.667, 0.01)

    def test_consecutive_tracking(self):
        """Test consecutive success/failure tracking"""
        m = PerformanceMetrics()

        m.record_task_success()
        m.record_task_success()
        assert m.consecutive_successes == 2
        assert m.consecutive_failures == 0

        m.record_task_failure()
        assert m.consecutive_successes == 0
        assert m.consecutive_failures == 1

    def test_overall_performance(self):
        """Test overall performance calculation"""
        m = PerformanceMetrics()

        # Record some successes
        for _ in range(5):
            m.record_task_success(0.8, 0.9)

        # Performance should be reasonable
        assert 40 <= m.overall_performance <= 100


class TestVotingSystem:
    """Tests for voting system"""

    def test_create_session(self):
        """Test creating a voting session"""
        vm = VotingManager()
        session = vm.create_session(
            VoteType.ANALYSIS,
            "How complex?",
            ["simple", "standard", "complex"]
        )

        assert session.vote_type == VoteType.ANALYSIS
        assert len(session.options) == 3
        assert session.is_open

    def test_cast_vote(self):
        """Test casting a vote"""
        vm = VotingManager()
        session = vm.create_session(
            VoteType.DECISION,
            "Choose one",
            ["A", "B", "C"]
        )

        c = Councillor(name="Voter")
        vote = vm.cast_vote(session.id, c, "B", confidence=0.8)

        assert vote is not None
        assert vote.choice == "B"
        assert vote.weight == c.vote_weight

    def test_weighted_results(self):
        """Test weighted vote tallying"""
        vm = VotingManager()
        session = vm.create_session(
            VoteType.DECISION,
            "Choose",
            ["A", "B"]
        )

        c1 = Councillor(name="C1")
        c1.happiness = 90  # High happiness = higher weight

        c2 = Councillor(name="C2")
        c2.happiness = 30  # Low happiness = lower weight

        vm.cast_vote(session.id, c1, "A", 0.9)
        vm.cast_vote(session.id, c2, "B", 0.9)

        results = vm.tally_votes(session.id)

        # C1's vote for A should have more weight
        assert results["A"] > results["B"]

    @pytest.mark.asyncio
    async def test_conduct_vote(self):
        """Test conducting a complete vote"""
        councillors = [
            Councillor(name="A"),
            Councillor(name="B"),
            Councillor(name="C"),
        ]

        winner, session = await conduct_vote(
            councillors,
            VoteType.ANALYSIS,
            "Complexity?",
            ["simple", "standard", "complex"]
        )

        assert winner in ["simple", "standard", "complex"]
        assert len(session.votes) == 3
        assert not session.is_open


class TestHappinessSystem:
    """Tests for happiness system"""

    def test_happiness_impacts(self):
        """Test that all impacts are defined"""
        assert HappinessEvent.TASK_SUCCESS in HAPPINESS_IMPACTS
        assert HappinessEvent.TASK_FAILURE in HAPPINESS_IMPACTS
        assert HAPPINESS_IMPACTS[HappinessEvent.TASK_SUCCESS] > 0
        assert HAPPINESS_IMPACTS[HappinessEvent.TASK_FAILURE] < 0

    def test_apply_event(self):
        """Test applying happiness events"""
        hm = HappinessManager()
        c = Councillor(name="Test", happiness=50)

        record = hm.apply_event(c, HappinessEvent.TASK_SUCCESS)

        assert c.happiness > 50
        assert record.impact > 0

    def test_happiness_clamp(self):
        """Test happiness stays in bounds"""
        hm = HappinessManager()
        c = Councillor(name="Test", happiness=95)

        # Try to go over 100
        for _ in range(10):
            hm.apply_event(c, HappinessEvent.BONUS_RECEIVED)

        assert c.happiness <= 100

        # Try to go below 0
        c.happiness = 10
        for _ in range(10):
            hm.apply_event(c, HappinessEvent.TASK_FAILURE)

        assert c.happiness >= 0

    def test_mood_levels(self):
        """Test mood descriptions"""
        hm = HappinessManager()

        assert hm.get_mood(95) == "ecstatic"
        assert hm.get_mood(75) == "happy"
        assert hm.get_mood(45) == "neutral"
        assert hm.get_mood(25) == "unhappy"
        assert hm.get_mood(10) == "critical"

    def test_team_morale(self):
        """Test team morale calculation"""
        hm = HappinessManager()
        team = [
            Councillor(name="A", happiness=80),
            Councillor(name="B", happiness=60),
            Councillor(name="C", happiness=70),
        ]

        morale = hm.get_team_morale(team)

        assert morale["average"] == pytest.approx(70, 0.1)
        assert morale["at_risk"] == 0


class TestFactory:
    """Tests for councillor factory"""

    def test_spawn_councillor(self):
        """Test spawning a councillor"""
        factory = CouncillorFactory()
        c = factory.spawn("coder")

        assert c.status == CouncillorStatus.PROBATION
        assert Specialization.CODING in c.specializations

    def test_spawn_team(self):
        """Test spawning a team"""
        factory = CouncillorFactory()
        team = factory.spawn_team(["coder", "reviewer", "tester"])

        assert len(team) == 3

        # Check each has different name
        names = [c.name for c in team]
        assert len(set(names)) == 3

    def test_unique_names(self):
        """Test that spawned councillors get unique names"""
        factory = CouncillorFactory()
        names = set()

        for _ in range(20):
            c = factory.spawn("generalist")
            assert c.name not in names
            names.add(c.name)

    def test_should_fire(self):
        """Test firing criteria evaluation"""
        factory = CouncillorFactory()

        # Good performer
        good = Councillor(name="Good")
        for _ in range(5):
            good.metrics.record_task_success()

        should, reason = factory.should_fire(good)
        assert not should

        # Poor performer
        poor = Councillor(name="Poor")
        for _ in range(6):
            poor.metrics.record_task_failure()

        should, reason = factory.should_fire(poor)
        assert should

    def test_promotion_criteria(self):
        """Test promotion criteria"""
        factory = CouncillorFactory()
        c = Councillor(name="Test", status=CouncillorStatus.PROBATION)

        # Not enough tasks
        can, reason = factory.can_promote(c)
        assert not can

        # Add enough successful tasks
        for _ in range(12):
            c.metrics.record_task_success(0.8, 0.8)

        can, reason = factory.can_promote(c)
        assert can

    def test_maintain_team(self):
        """Test team maintenance"""
        factory = CouncillorFactory(FactoryConfig(min_councillors=3))
        team = factory.spawn_team(["coder", "reviewer"])  # Only 2

        actions = factory.maintain_team(team)

        # Should have spawned 1 to reach minimum
        assert len(actions["spawned"]) >= 1
        assert len(team) >= 3


class TestBonusPool:
    """Tests for bonus pool"""

    def test_add_to_pool(self):
        """Test adding to bonus pool"""
        pool = BonusPool(balance=100)
        pool.add(50, "test")

        assert pool.balance == 150

    def test_withdraw_from_pool(self):
        """Test withdrawing from pool"""
        pool = BonusPool(balance=100)
        amount = pool.withdraw(30, "recipient", "bonus")

        assert amount == 30
        assert pool.balance == 70

    def test_withdraw_exceeds_balance(self):
        """Test withdrawing more than balance"""
        pool = BonusPool(balance=50)
        amount = pool.withdraw(100, "recipient", "bonus")

        assert amount == 50  # Only got what was available
        assert pool.balance == 0

    def test_max_balance(self):
        """Test max balance cap"""
        pool = BonusPool(balance=400, max_balance=500)
        pool.add(200, "test")

        assert pool.balance == 500  # Capped


class TestCouncilOrchestrator:
    """Tests for the main orchestrator"""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test council initialization"""
        council = await create_council(templates=["coder", "reviewer"])

        assert len(council.councillors) == 2
        assert council._initialized

    @pytest.mark.asyncio
    async def test_get_council_status(self):
        """Test getting council status"""
        council = await create_council()
        status = council.get_council_status()

        assert "total_councillors" in status
        assert "bonus_pool" in status
        assert "team_morale" in status

    @pytest.mark.asyncio
    async def test_leaderboard(self):
        """Test councillor leaderboard"""
        council = await create_council(templates=["coder", "reviewer", "tester"])

        leaderboard = council.get_councillor_leaderboard()

        assert len(leaderboard) == 3
        assert "rank" in leaderboard[0]
        assert "performance" in leaderboard[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
