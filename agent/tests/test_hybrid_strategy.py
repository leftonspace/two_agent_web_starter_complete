"""
PHASE 9.4: Hybrid Strategy Tests

Tests for cost-optimized hybrid execution strategy.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.hybrid_strategy import (
    HybridStrategy,
    QualityThresholds,
    CostBudget,
    HybridStats,
)
from llm.llm_router import TaskComplexity, ModelTier


@pytest.fixture
def strategy():
    """Create hybrid strategy instance."""
    return HybridStrategy(
        quality_thresholds=QualityThresholds(),
        cost_budget=CostBudget(daily_limit_usd=10.0),
        target_local_percentage=80.0,
    )


def test_strategy_initialization(strategy):
    """Test hybrid strategy initialization."""
    assert strategy.target_local_percentage == 80.0
    assert strategy.quality_thresholds.critical == 0.95
    assert strategy.cost_budget.daily_limit_usd == 10.0
    assert strategy.stats.total_requests == 0


def test_analyze_task_complexity_trivial(strategy):
    """Test complexity analysis - trivial."""
    complexity = strategy.analyze_task_complexity("What is 2+2?")
    assert complexity == TaskComplexity.TRIVIAL


def test_analyze_task_complexity_high(strategy):
    """Test complexity analysis - high."""
    complexity = strategy.analyze_task_complexity(
        "Design a comprehensive architecture for a distributed system"
    )
    assert complexity == TaskComplexity.HIGH


def test_get_quality_threshold(strategy):
    """Test quality threshold retrieval."""
    assert strategy.get_quality_threshold(TaskComplexity.CRITICAL) == 0.95
    assert strategy.get_quality_threshold(TaskComplexity.HIGH) == 0.85
    assert strategy.get_quality_threshold(TaskComplexity.MEDIUM) == 0.75
    assert strategy.get_quality_threshold(TaskComplexity.LOW) == 0.60


def test_should_use_local_trivial(strategy):
    """Test local routing for trivial tasks."""
    should_use = strategy.should_use_local(TaskComplexity.TRIVIAL)
    assert should_use is True


def test_should_use_local_critical(strategy):
    """Test cloud routing for critical tasks."""
    should_use = strategy.should_use_local(TaskComplexity.CRITICAL)
    assert should_use is False


def test_should_use_local_force_cloud(strategy):
    """Test forced cloud routing."""
    should_use = strategy.should_use_local(TaskComplexity.TRIVIAL, force_cloud=True)
    assert should_use is False


def test_should_use_local_high_complexity(strategy):
    """Test cloud routing for high complexity."""
    should_use = strategy.should_use_local(TaskComplexity.HIGH)
    assert should_use is False


@pytest.mark.asyncio
async def test_execute_local_task(strategy):
    """Test execution of local task."""
    # Mock router
    mock_response = {
        "response": "Test response",
        "model": "llama3",
        "provider": "ollama",
        "tier": "local",
        "cost_usd": 0.0,
    }

    strategy.router.route = AsyncMock(return_value=mock_response)

    result = await strategy.execute(
        prompt="Simple task",
        complexity=TaskComplexity.TRIVIAL
    )

    assert result["model"] == "llama3"
    assert result["hybrid_strategy"]["use_local"] is True
    assert strategy.stats.local_requests == 1
    assert strategy.stats.total_requests == 1


@pytest.mark.asyncio
async def test_execute_cloud_task(strategy):
    """Test execution of cloud task."""
    # Mock router
    mock_response = {
        "response": "Test response",
        "model": "gpt-4",
        "provider": "openai",
        "tier": "premium",
        "cost_usd": 0.10,
    }

    strategy.router.route = AsyncMock(return_value=mock_response)

    result = await strategy.execute(
        prompt="Complex task",
        complexity=TaskComplexity.CRITICAL
    )

    assert result["tier"] == "premium"
    assert result["hybrid_strategy"]["use_local"] is False
    assert strategy.stats.cloud_requests == 1
    assert strategy.stats.total_cost_usd == 0.10


@pytest.mark.asyncio
async def test_execute_force_local(strategy):
    """Test forced local execution."""
    mock_response = {
        "response": "Test",
        "model": "llama3",
        "tier": "local",
        "cost_usd": 0.0,
    }

    strategy.router.route = AsyncMock(return_value=mock_response)

    result = await strategy.execute(
        prompt="Test",
        complexity=TaskComplexity.HIGH,
        force_local=True
    )

    assert result["hybrid_strategy"]["use_local"] is True


@pytest.mark.asyncio
async def test_execute_force_cloud(strategy):
    """Test forced cloud execution."""
    mock_response = {
        "response": "Test",
        "model": "gpt-4o",
        "tier": "standard",
        "cost_usd": 0.05,
    }

    strategy.router.route = AsyncMock(return_value=mock_response)

    result = await strategy.execute(
        prompt="Test",
        complexity=TaskComplexity.TRIVIAL,
        force_cloud=True
    )

    assert result["hybrid_strategy"]["use_local"] is False
    assert strategy.stats.cloud_requests == 1


@pytest.mark.asyncio
async def test_execute_with_quality_check_pass(strategy):
    """Test quality check - passing."""
    mock_response = {
        "response": "High quality response",
        "model": "llama3",
        "tier": "local",
        "cost_usd": 0.0,
        "quality_score": 0.85,
        "hybrid_strategy": {"use_local": True},
    }

    strategy.router.route = AsyncMock(return_value=mock_response)

    result = await strategy.execute_with_quality_check(
        prompt="Test",
        complexity=TaskComplexity.MEDIUM
    )

    # Quality 0.85 >= threshold 0.75 for medium complexity
    assert "quality_fallback_used" not in result
    assert strategy.router.route.call_count == 1


@pytest.mark.asyncio
async def test_execute_with_quality_check_fail_and_retry(strategy):
    """Test quality check - failing and retrying with cloud."""
    # First call (local) - low quality
    local_response = {
        "response": "Low quality",
        "model": "llama3",
        "tier": "local",
        "cost_usd": 0.0,
        "quality_score": 0.5,  # Below threshold
        "hybrid_strategy": {"use_local": True},
    }

    # Second call (cloud) - high quality
    cloud_response = {
        "response": "High quality",
        "model": "gpt-4o",
        "tier": "standard",
        "cost_usd": 0.05,
        "quality_score": 0.9,
        "hybrid_strategy": {"use_local": False},
        "quality_fallback_used": True,
    }

    strategy.router.route = AsyncMock(side_effect=[local_response, cloud_response])

    result = await strategy.execute_with_quality_check(
        prompt="Test",
        complexity=TaskComplexity.MEDIUM
    )

    # Should have retried with cloud
    assert result["quality_fallback_used"] is True
    assert strategy.stats.quality_degradations == 1
    assert strategy.router.route.call_count == 2


def test_get_statistics(strategy):
    """Test statistics retrieval."""
    strategy.stats.total_requests = 100
    strategy.stats.local_requests = 80
    strategy.stats.cloud_requests = 20
    strategy.stats.total_cost_usd = 5.0
    strategy.stats.cost_saved_usd = 20.0

    stats = strategy.get_statistics()

    assert stats["total_requests"] == 100
    assert stats["local_requests"] == 80
    assert stats["cloud_requests"] == 20
    assert stats["local_percentage"] == 80.0
    assert stats["cloud_percentage"] == 20.0
    assert stats["total_cost_usd"] == 5.0
    assert stats["cost_saved_usd"] == 20.0
    assert stats["avg_cost_per_request"] == 0.05
    assert stats["cost_efficiency"] == 80.0  # 20/(5+20) * 100


def test_get_recommendations_low_local_usage(strategy):
    """Test recommendations - low local usage."""
    strategy.stats.total_requests = 100
    strategy.stats.local_requests = 50  # 50% < 80% target
    strategy.stats.cloud_requests = 50

    recommendations = strategy.get_recommendations()

    assert len(recommendations["recommendations"]) > 0
    assert any(r["type"] == "increase_local" for r in recommendations["recommendations"])


def test_get_recommendations_high_local_usage(strategy):
    """Test recommendations - high local usage."""
    strategy.stats.total_requests = 100
    strategy.stats.local_requests = 95  # 95% > 80% target
    strategy.stats.cloud_requests = 5

    recommendations = strategy.get_recommendations()

    assert any(r["type"] == "decrease_local" for r in recommendations["recommendations"])


def test_get_recommendations_quality_issues(strategy):
    """Test recommendations - quality issues."""
    strategy.stats.total_requests = 100
    strategy.stats.quality_degradations = 15  # 15% degradation rate

    recommendations = strategy.get_recommendations()

    assert any(r["type"] == "quality_issues" for r in recommendations["recommendations"])


def test_get_recommendations_budget_warning(strategy):
    """Test recommendations - budget warning."""
    strategy.stats.total_cost_usd = 9.0  # Near $10 daily limit
    strategy.cost_budget.daily_limit_usd = 10.0

    recommendations = strategy.get_recommendations()

    assert any(r["type"] == "budget_warning" for r in recommendations["recommendations"])


def test_estimate_cloud_cost(strategy):
    """Test cloud cost estimation."""
    assert strategy._estimate_cloud_cost(TaskComplexity.TRIVIAL) < 0.01
    assert strategy._estimate_cloud_cost(TaskComplexity.LOW) < 0.01
    assert strategy._estimate_cloud_cost(TaskComplexity.MEDIUM) == 0.01
    assert strategy._estimate_cloud_cost(TaskComplexity.HIGH) == 0.05
    assert strategy._estimate_cloud_cost(TaskComplexity.CRITICAL) == 0.10


@pytest.mark.asyncio
async def test_cost_tracking(strategy):
    """Test cost tracking and savings."""
    # Mock local execution
    local_response = {
        "response": "Test",
        "model": "llama3",
        "tier": "local",
        "cost_usd": 0.0,
    }

    strategy.router.route = AsyncMock(return_value=local_response)

    # Execute trivial task (should use local)
    await strategy.execute(prompt="Test", complexity=TaskComplexity.TRIVIAL)

    # Should have saved money by using local
    assert strategy.stats.cost_saved_usd > 0
    assert strategy.stats.total_cost_usd == 0.0


@pytest.mark.asyncio
async def test_local_percentage_tracking(strategy):
    """Test local percentage tracking."""
    # Execute multiple tasks
    local_response = {"response": "Test", "model": "llama3", "tier": "local", "cost_usd": 0.0}
    cloud_response = {"response": "Test", "model": "gpt-4o", "tier": "standard", "cost_usd": 0.05}

    # 8 local, 2 cloud = 80% local
    for _ in range(8):
        strategy.router.route = AsyncMock(return_value=local_response)
        await strategy.execute(prompt="Test", complexity=TaskComplexity.TRIVIAL)

    for _ in range(2):
        strategy.router.route = AsyncMock(return_value=cloud_response)
        await strategy.execute(prompt="Test", complexity=TaskComplexity.HIGH)

    stats = strategy.get_statistics()
    assert stats["local_percentage"] == 80.0
    assert stats["cloud_percentage"] == 20.0


def test_quality_thresholds_custom():
    """Test custom quality thresholds."""
    custom_thresholds = QualityThresholds(
        critical=0.99,
        high=0.90,
        medium=0.80,
        low=0.70,
    )

    strategy = HybridStrategy(quality_thresholds=custom_thresholds)

    assert strategy.get_quality_threshold(TaskComplexity.CRITICAL) == 0.99
    assert strategy.get_quality_threshold(TaskComplexity.HIGH) == 0.90


def test_cost_budget_custom():
    """Test custom cost budget."""
    custom_budget = CostBudget(
        daily_limit_usd=50.0,
        per_request_limit_usd=1.0,
    )

    strategy = HybridStrategy(cost_budget=custom_budget)

    assert strategy.cost_budget.daily_limit_usd == 50.0
    assert strategy.cost_budget.per_request_limit_usd == 1.0
