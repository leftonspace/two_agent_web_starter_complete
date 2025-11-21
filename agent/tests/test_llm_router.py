"""
PHASE 9.2: LLM Router Tests

Tests for intelligent LLM routing between cloud and local models.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.llm_router import LLMRouter, ModelTier, TaskComplexity, ModelConfig


@pytest.fixture
def router():
    """Create LLM router instance."""
    return LLMRouter(enable_local=True, prefer_local=True)


@pytest.fixture
def router_no_local():
    """Create LLM router with local models disabled."""
    return LLMRouter(enable_local=False)


def test_router_initialization(router):
    """Test router initialization."""
    assert router.enable_local is True
    assert router.prefer_local is True
    assert router.total_requests == 0
    assert router.total_cost_usd == 0.0


def test_analyze_complexity_trivial(router):
    """Test complexity analysis - trivial."""
    complexity = router.analyze_complexity("What is Python?")
    assert complexity == TaskComplexity.TRIVIAL


def test_analyze_complexity_low(router):
    """Test complexity analysis - low."""
    complexity = router.analyze_complexity("List the files in the current directory")
    assert complexity == TaskComplexity.LOW


def test_analyze_complexity_medium(router):
    """Test complexity analysis - medium."""
    complexity = router.analyze_complexity(
        "Explain how the authentication system works in this application"
    )
    assert complexity == TaskComplexity.MEDIUM


def test_analyze_complexity_high(router):
    """Test complexity analysis - high."""
    complexity = router.analyze_complexity(
        "Analyze the architecture of this system and design a comprehensive "
        "refactoring plan to optimize performance and maintainability"
    )
    assert complexity == TaskComplexity.HIGH


def test_analyze_complexity_critical(router):
    """Test complexity analysis - critical (explicit)."""
    complexity = router.analyze_complexity(
        "Simple task",
        context={"is_critical": True}
    )
    assert complexity == TaskComplexity.CRITICAL


def test_select_model_local_trivial(router):
    """Test model selection - local for trivial task."""
    router._ollama_available = True
    model = router.select_model(TaskComplexity.TRIVIAL)

    assert model.tier == ModelTier.LOCAL
    assert model.is_local is True


def test_select_model_local_medium(router):
    """Test model selection - local for medium task with prefer_local."""
    router._ollama_available = True
    model = router.select_model(TaskComplexity.MEDIUM)

    assert model.tier == ModelTier.LOCAL or model.tier == ModelTier.MINI


def test_select_model_cloud_high(router):
    """Test model selection - cloud for high complexity."""
    model = router.select_model(TaskComplexity.HIGH)

    assert model.tier == ModelTier.STANDARD
    assert model.name == "gpt-4o"


def test_select_model_cloud_critical(router):
    """Test model selection - premium for critical."""
    model = router.select_model(TaskComplexity.CRITICAL)

    assert model.tier == ModelTier.PREMIUM
    assert model.name == "gpt-4"


def test_select_model_force_tier(router):
    """Test model selection - forced tier."""
    model = router.select_model(
        TaskComplexity.TRIVIAL,
        force_tier=ModelTier.PREMIUM
    )

    assert model.tier == ModelTier.PREMIUM


def test_select_model_no_local(router_no_local):
    """Test model selection when local models disabled."""
    router_no_local._ollama_available = False
    model = router_no_local.select_model(TaskComplexity.TRIVIAL)

    # Should fall back to mini tier
    assert model.tier == ModelTier.MINI
    assert model.is_local is False


@pytest.mark.asyncio
async def test_route_local_model(router):
    """Test routing to local model."""
    # Mock Ollama client
    mock_ollama = AsyncMock()
    mock_response = MagicMock()
    mock_response.response = "Local model response"
    mock_response.latency_seconds = 2.5
    mock_response.tokens_per_second = 25.0
    mock_response.prompt_eval_count = 10
    mock_response.eval_count = 50
    mock_ollama.chat = AsyncMock(return_value=mock_response)
    mock_ollama.is_available = AsyncMock(return_value=True)

    router.ollama_client = mock_ollama
    router._ollama_available = True

    result = await router.route(
        prompt="What is Python?",
        complexity=TaskComplexity.TRIVIAL
    )

    assert result["model"] == "llama3"
    assert result["provider"] == "ollama"
    assert result["cost_usd"] == 0.0
    assert result["response"] == "Local model response"
    assert router.local_requests == 1
    assert router.total_requests == 1


@pytest.mark.asyncio
async def test_route_cloud_model(router):
    """Test routing to cloud model."""
    router._ollama_available = False

    result = await router.route(
        prompt="Analyze this complex system",
        complexity=TaskComplexity.HIGH
    )

    assert result["tier"] == ModelTier.STANDARD.value
    assert result["provider"] == "openai"
    assert result["cost_usd"] > 0
    assert router.cloud_requests == 1


@pytest.mark.asyncio
async def test_route_fallback_on_local_failure(router):
    """Test fallback to cloud when local model fails."""
    # Mock Ollama client that fails
    mock_ollama = AsyncMock()
    mock_ollama.chat = AsyncMock(side_effect=Exception("Ollama error"))
    mock_ollama.is_available = AsyncMock(return_value=True)

    router.ollama_client = mock_ollama
    router._ollama_available = True

    # Should fall back to cloud
    result = await router.route(
        prompt="Test",
        complexity=TaskComplexity.TRIVIAL
    )

    assert result["provider"] == "openai"
    assert result.get("fallback_used") is True


@pytest.mark.asyncio
async def test_route_forced_model(router):
    """Test routing with forced model."""
    router._ollama_available = True

    result = await router.route(
        prompt="Test",
        model="gpt-4",
        complexity=TaskComplexity.TRIVIAL
    )

    # Should use forced model despite trivial complexity
    assert "gpt-4" in result["model"] or result["tier"] == "premium"


def test_get_statistics(router):
    """Test statistics retrieval."""
    router.total_requests = 100
    router.local_requests = 80
    router.cloud_requests = 20
    router.total_cost_usd = 5.50

    stats = router.get_statistics()

    assert stats["total_requests"] == 100
    assert stats["local_requests"] == 80
    assert stats["cloud_requests"] == 20
    assert stats["local_percentage"] == 80.0
    assert stats["cloud_percentage"] == 20.0
    assert stats["total_cost_usd"] == 5.50
    assert stats["avg_cost_per_request"] == 0.055


def test_get_statistics_empty(router):
    """Test statistics with no requests."""
    stats = router.get_statistics()

    assert stats["total_requests"] == 0
    assert stats["avg_cost_per_request"] == 0


def test_model_config_is_local():
    """Test ModelConfig.is_local property."""
    local_model = ModelConfig(
        name="llama3",
        tier=ModelTier.LOCAL,
        provider="ollama",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        max_tokens=4096,
        context_window=8192,
    )

    cloud_model = ModelConfig(
        name="gpt-4o",
        tier=ModelTier.STANDARD,
        provider="openai",
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
        max_tokens=16384,
        context_window=128000,
    )

    assert local_model.is_local is True
    assert cloud_model.is_local is False
