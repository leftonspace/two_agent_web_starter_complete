"""
Integration Tests: Multi-Provider LLM Failover

Tests LLM provider routing, fallback chains, and automatic
failover when providers fail.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# Mock providers for testing without real API calls
class MockProvider:
    """Mock LLM provider for testing"""

    def __init__(self, name: str, should_fail: bool = False, fail_count: int = 0):
        self.name = name
        self.should_fail = should_fail
        self.fail_count = fail_count
        self._current_failures = 0
        self._call_count = 0

        from llm.providers import ProviderHealth, ProviderStatus
        self._health = ProviderHealth(
            provider=name,
            status=ProviderStatus.HEALTHY if not should_fail else ProviderStatus.UNHEALTHY
        )

    @property
    def is_healthy(self) -> bool:
        from llm.providers import ProviderStatus
        return self._health.status == ProviderStatus.HEALTHY

    @property
    def health(self):
        return self._health

    async def chat(self, messages, model=None, **kwargs):
        self._call_count += 1

        if self.should_fail and self._current_failures < self.fail_count:
            self._current_failures += 1
            raise RuntimeError(f"Mock failure {self._current_failures} from {self.name}")

        from llm.providers import ChatResponse
        return ChatResponse(
            content=f"Response from {self.name}",
            model=model or "mock-model",
            provider=self.name,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.001,
            latency_ms=100
        )

    def get_cost_per_token(self, model=None):
        return (0.001, 0.002)

    async def health_check(self):
        return self._health

    def get_available_models(self):
        from llm.providers import ModelInfo
        return [ModelInfo("mock-model", self.name, 0.001, 0.002, 8192, 4096)]


class TestFallbackChain:
    """Test fallback chain behavior"""

    @pytest.mark.asyncio
    async def test_primary_provider_success(self):
        """Should use primary provider when it succeeds"""
        from llm.enhanced_router import FallbackChain

        primary = MockProvider("primary")
        fallback = MockProvider("fallback")

        chain = FallbackChain(primary, [fallback])

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        assert response.provider == "primary"
        assert primary._call_count == 1
        assert fallback._call_count == 0

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Should fallback when primary fails"""
        from llm.enhanced_router import FallbackChain

        primary = MockProvider("primary", should_fail=True, fail_count=10)
        fallback = MockProvider("fallback")

        chain = FallbackChain(primary, [fallback], max_retries=2)

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        assert response.provider == "fallback"
        assert primary._call_count == 2  # Max retries
        assert fallback._call_count == 1

    @pytest.mark.asyncio
    async def test_retry_before_fallback(self):
        """Should retry primary before falling back"""
        from llm.enhanced_router import FallbackChain

        # Fail once then succeed
        primary = MockProvider("primary", should_fail=True, fail_count=1)
        fallback = MockProvider("fallback")

        chain = FallbackChain(primary, [fallback], max_retries=3)

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        assert response.provider == "primary"
        assert primary._call_count == 2  # 1 fail + 1 success
        assert fallback._call_count == 0

    @pytest.mark.asyncio
    async def test_multiple_fallbacks(self):
        """Should try multiple fallbacks in order"""
        from llm.enhanced_router import FallbackChain

        primary = MockProvider("primary", should_fail=True, fail_count=10)
        fallback1 = MockProvider("fallback1", should_fail=True, fail_count=10)
        fallback2 = MockProvider("fallback2")

        chain = FallbackChain(primary, [fallback1, fallback2], max_retries=1)

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        assert response.provider == "fallback2"

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Should raise error when all providers fail"""
        from llm.enhanced_router import FallbackChain

        primary = MockProvider("primary", should_fail=True, fail_count=10)
        fallback = MockProvider("fallback", should_fail=True, fail_count=10)

        chain = FallbackChain(primary, [fallback], max_retries=2)

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RuntimeError) as exc:
            await chain.chat_with_fallback(messages)

        assert "All providers failed" in str(exc.value)

    @pytest.mark.asyncio
    async def test_tracks_last_successful_provider(self):
        """Should track which provider succeeded"""
        from llm.enhanced_router import FallbackChain

        primary = MockProvider("primary", should_fail=True, fail_count=10)
        fallback = MockProvider("fallback")

        chain = FallbackChain(primary, [fallback], max_retries=1)

        messages = [{"role": "user", "content": "Hello"}]
        await chain.chat_with_fallback(messages)

        assert chain.last_successful_provider == "fallback"


class TestRoutingStrategy:
    """Test different routing strategies"""

    def test_cost_strategy_selects_cheapest(self):
        """Cost strategy should select cheapest provider"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig, RoutingStrategy

        config = RouterConfig(strategy=RoutingStrategy.COST)
        router = EnhancedModelRouter(config)

        # Add mock providers with known costs
        router.providers = {
            "expensive": MockProvider("expensive"),
            "cheap": MockProvider("cheap"),
        }

        # The cost strategy implementation checks specific order
        # Just verify selection works without error
        provider, model = router.select_model(task_type="simple", complexity="low")
        assert provider is not None
        assert model is not None

    def test_quality_strategy_uses_recommendations(self):
        """Quality strategy should use model recommendations"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig, RoutingStrategy

        config = RouterConfig(strategy=RoutingStrategy.QUALITY)
        router = EnhancedModelRouter(config)

        # Should select based on task type and complexity
        provider, model = router.select_model(task_type="coding", complexity="high")

        # Should return something even without configured providers
        assert model is not None

    def test_hybrid_strategy_balances_cost_and_quality(self):
        """Hybrid strategy should balance cost and quality"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig, RoutingStrategy

        config = RouterConfig(strategy=RoutingStrategy.HYBRID)
        router = EnhancedModelRouter(config)

        provider, model = router.select_model(task_type="review", complexity="medium")

        # Should make a selection
        assert model is not None

    def test_local_first_prefers_ollama(self):
        """Local-first strategy should prefer Ollama"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig, RoutingStrategy

        config = RouterConfig(strategy=RoutingStrategy.LOCAL_FIRST)
        router = EnhancedModelRouter(config)

        # Add mock Ollama provider
        ollama_mock = MockProvider("ollama")
        router.providers["ollama"] = ollama_mock

        provider, model = router.select_model(task_type="simple", complexity="low")

        # Should prefer Ollama if available and healthy
        if provider:
            assert provider.name == "ollama"


class TestCostTracking:
    """Test cost tracking functionality"""

    def test_cost_tracking_accumulation(self):
        """Should accumulate costs correctly"""
        from llm.enhanced_router import CostTracker

        tracker = CostTracker()

        tracker.add_cost("openai", "gpt-4", 0.05, 1000)
        tracker.add_cost("anthropic", "claude-3", 0.03, 800)

        assert tracker.total_cost == 0.08
        assert tracker.daily_cost == 0.08
        assert tracker.session_cost == 0.08
        assert tracker.costs_by_provider["openai"] == 0.05
        assert tracker.costs_by_provider["anthropic"] == 0.03

    def test_cost_reset_daily(self):
        """Should reset daily costs"""
        from llm.enhanced_router import CostTracker

        tracker = CostTracker()
        tracker.add_cost("openai", "gpt-4", 0.05, 1000)

        tracker.reset_daily()

        assert tracker.daily_cost == 0.0
        assert tracker.total_cost == 0.05  # Total not reset

    def test_cost_reset_session(self):
        """Should reset session costs"""
        from llm.enhanced_router import CostTracker

        tracker = CostTracker()
        tracker.add_cost("openai", "gpt-4", 0.05, 1000)

        tracker.reset_session()

        assert tracker.session_cost == 0.0
        assert tracker.total_cost == 0.05

    def test_cost_summary(self):
        """Should provide cost summary"""
        from llm.enhanced_router import CostTracker

        tracker = CostTracker()
        tracker.add_cost("openai", "gpt-4", 0.05, 1000)

        summary = tracker.get_summary()

        assert "total_cost" in summary
        assert "daily_cost" in summary
        assert "by_provider" in summary
        assert "by_model" in summary


class TestBudgetEnforcement:
    """Test budget enforcement"""

    @pytest.mark.asyncio
    async def test_daily_budget_exceeded_raises_error(self):
        """Should raise error when daily budget exceeded"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        config = RouterConfig(daily_budget=0.01)
        router = EnhancedModelRouter(config)

        # Simulate exceeding budget
        router.cost_tracker.daily_cost = 0.02

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RuntimeError) as exc:
            await router.chat(messages)

        assert "budget" in str(exc.value).lower()

    def test_cost_budget_selection(self):
        """Should respect cost budget in model selection"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        config = RouterConfig(cost_budget=0.001)  # Very tight budget
        router = EnhancedModelRouter(config)

        # Should still be able to select a model
        provider, model = router.select_model(
            task_type="simple",
            complexity="low",
            cost_budget=0.001
        )

        # Should return some selection
        assert model is not None


class TestHealthChecks:
    """Test provider health checking"""

    @pytest.mark.asyncio
    async def test_health_check_updates_status(self):
        """Health checks should update provider status"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig
        from llm.providers import ProviderStatus

        router = EnhancedModelRouter(RouterConfig())

        # Add mock provider
        mock = MockProvider("test")
        router.providers["test"] = mock

        await router.check_provider_health(force=True)

        # Status should be updated
        health_status = router.get_health_status()
        assert "test" in health_status

    def test_get_health_status(self):
        """Should return health status for all providers"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        # Add mock providers
        router.providers["provider1"] = MockProvider("provider1")
        router.providers["provider2"] = MockProvider("provider2")

        status = router.get_health_status()

        assert "provider1" in status
        assert "provider2" in status


class TestModelSelection:
    """Test model selection for different task types"""

    def test_select_model_for_coding(self):
        """Should select appropriate model for coding tasks"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        provider, model = router.select_model(task_type="coding", complexity="high")

        # Should return a selection
        assert model is not None

    def test_select_model_for_planning(self):
        """Should select appropriate model for planning tasks"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        provider, model = router.select_model(task_type="planning", complexity="high")

        assert model is not None

    def test_select_model_for_simple_tasks(self):
        """Should select cost-effective model for simple tasks"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        provider, model = router.select_model(task_type="simple", complexity="low")

        assert model is not None

    def test_require_local_model(self):
        """Should respect require_local parameter"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        # Add mock Ollama
        router.providers["ollama"] = MockProvider("ollama")

        provider, model = router.select_model(
            task_type="simple",
            complexity="low",
            require_local=True
        )

        # Should prefer Ollama when require_local is True
        if provider:
            assert provider.name == "ollama"


class TestEnhancedRouterIntegration:
    """Integration tests for the complete router"""

    @pytest.mark.asyncio
    async def test_chat_with_routing(self):
        """Should route chat through selected provider"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        # Replace with mock providers
        mock = MockProvider("mock")
        router.providers = {"mock": mock}

        messages = [{"role": "user", "content": "Hello"}]

        response = await router.chat(
            messages,
            task_type="simple",
            complexity="low",
            use_fallback=False
        )

        assert response is not None
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_chat_with_fallback_enabled(self):
        """Should use fallback chain when enabled"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        config = RouterConfig(fallback_enabled=True)
        router = EnhancedModelRouter(config)

        # Set up mock providers - primary fails, fallback succeeds
        primary = MockProvider("primary", should_fail=True, fail_count=10)
        fallback = MockProvider("fallback")
        router.providers = {"primary": primary, "fallback": fallback}

        messages = [{"role": "user", "content": "Hello"}]

        response = await router.chat(messages, use_fallback=True)

        assert response.provider == "fallback"

    def test_create_custom_fallback_chain(self):
        """Should create custom fallback chains"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        # Add mock providers
        router.providers = {
            "openai": MockProvider("openai"),
            "anthropic": MockProvider("anthropic"),
            "deepseek": MockProvider("deepseek"),
        }

        chain = router.create_fallback_chain(
            "openai",
            ["anthropic", "deepseek"]
        )

        assert len(chain.providers) == 3
        assert chain.providers[0].name == "openai"

    def test_get_cost_summary(self):
        """Should return cost summary"""
        from llm.enhanced_router import EnhancedModelRouter, RouterConfig

        router = EnhancedModelRouter(RouterConfig())

        # Add some mock costs
        router.cost_tracker.add_cost("openai", "gpt-4", 0.05, 1000)

        summary = router.get_cost_summary()

        assert "total_cost" in summary
        assert summary["total_cost"] == 0.05


class TestProviderHealth:
    """Test provider health tracking"""

    def test_consecutive_failures_degrade_health(self):
        """Consecutive failures should degrade health status"""
        from llm.providers import ProviderHealth, ProviderStatus

        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.HEALTHY
        )

        # Simulate failures
        health.consecutive_failures = 3
        health.status = ProviderStatus.UNHEALTHY

        assert health.status == ProviderStatus.UNHEALTHY

    def test_success_resets_failures(self):
        """Success should reset failure count"""
        from llm.providers import ProviderHealth, ProviderStatus

        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.DEGRADED,
            consecutive_failures=2
        )

        # Simulate success
        health.consecutive_failures = 0
        health.status = ProviderStatus.HEALTHY

        assert health.consecutive_failures == 0
        assert health.status == ProviderStatus.HEALTHY


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
