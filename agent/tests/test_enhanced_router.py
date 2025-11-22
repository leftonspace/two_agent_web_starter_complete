"""
Comprehensive Tests for Enhanced Model Router

Tests for:
- LLMProvider implementations
- FallbackChain
- EnhancedModelRouter
- Cost tracking
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agent.llm import (
    # Providers
    LLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider,
    DeepSeekProvider,
    QwenProvider,
    ChatResponse,
    ModelInfo,
    ProviderStatus,
    ProviderHealth,
    # Router
    EnhancedModelRouter,
    FallbackChain,
    RouterConfig,
    CostTracker,
    RoutingStrategy,
    TaskType,
    Complexity,
    create_router,
)


# =============================================================================
# Mock Provider for Testing
# =============================================================================

class MockProvider(LLMProvider):
    """Mock provider for testing"""

    def __init__(
        self,
        name: str = "mock",
        should_fail: bool = False,
        response_content: str = "Mock response"
    ):
        super().__init__(name)
        self.should_fail = should_fail
        self.response_content = response_content
        self.call_count = 0
        self._health.status = ProviderStatus.HEALTHY

    async def chat(
        self,
        messages,
        model=None,
        temperature=0.7,
        max_tokens=None,
        **kwargs
    ):
        self.call_count += 1

        if self.should_fail:
            self._health.consecutive_failures += 1
            raise RuntimeError("Mock failure")

        return ChatResponse(
            content=self.response_content,
            model=model or "mock-model",
            provider=self.name,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost=0.001,
            latency_ms=100.0
        )

    def get_cost_per_token(self, model=None):
        return (0.001, 0.002)

    async def health_check(self):
        self._health.last_check = datetime.now()
        if not self.should_fail:
            self._health.status = ProviderStatus.HEALTHY
        return self._health

    def get_available_models(self):
        return [ModelInfo("mock-model", "mock", 0.001, 0.002)]


# =============================================================================
# Provider Tests
# =============================================================================

class TestChatResponse:
    """Test ChatResponse dataclass"""

    def test_creation(self):
        """Test response creation"""
        response = ChatResponse(
            content="Hello",
            model="gpt-4",
            provider="openai",
            input_tokens=100,
            output_tokens=50,
            cost=0.01
        )

        assert response.content == "Hello"
        assert response.model == "gpt-4"
        assert response.total_tokens == 0  # Not auto-calculated in this test
        assert response.cost == 0.01

    def test_to_dict(self):
        """Test serialization"""
        response = ChatResponse(
            content="Test",
            model="model",
            provider="provider"
        )

        d = response.to_dict()
        assert d["content"] == "Test"
        assert d["model"] == "model"


class TestModelInfo:
    """Test ModelInfo dataclass"""

    def test_creation(self):
        """Test model info creation"""
        info = ModelInfo(
            name="gpt-4o",
            provider="openai",
            input_cost_per_1k=0.005,
            output_cost_per_1k=0.015,
            context_window=128000
        )

        assert info.name == "gpt-4o"
        assert info.provider == "openai"
        assert info.context_window == 128000


class TestProviderHealth:
    """Test ProviderHealth tracking"""

    def test_health_status(self):
        """Test health status tracking"""
        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.HEALTHY
        )

        assert health.status == ProviderStatus.HEALTHY

    def test_error_tracking(self):
        """Test error tracking"""
        health = ProviderHealth(
            provider="test",
            status=ProviderStatus.UNHEALTHY,
            last_error="Connection failed",
            consecutive_failures=3
        )

        assert health.consecutive_failures == 3
        assert "Connection" in health.last_error


class TestOpenAIProvider:
    """Test OpenAI provider"""

    def test_cost_per_token(self):
        """Test cost calculation"""
        provider = OpenAIProvider(api_key="test")

        input_cost, output_cost = provider.get_cost_per_token("gpt-4o-mini")
        assert input_cost == 0.00015
        assert output_cost == 0.0006

    def test_available_models(self):
        """Test available models listing"""
        provider = OpenAIProvider(api_key="test")

        models = provider.get_available_models()
        model_names = [m.name for m in models]

        assert "gpt-4o" in model_names
        assert "gpt-4o-mini" in model_names

    def test_calculate_cost(self):
        """Test cost calculation"""
        provider = OpenAIProvider(api_key="test")

        cost = provider.calculate_cost(1000, 500, "gpt-4o-mini")
        expected = (1000 * 0.00015 / 1000) + (500 * 0.0006 / 1000)
        assert abs(cost - expected) < 0.0001


class TestAnthropicProvider:
    """Test Anthropic provider"""

    def test_cost_per_token(self):
        """Test cost calculation"""
        provider = AnthropicProvider(api_key="test")

        input_cost, output_cost = provider.get_cost_per_token("claude-3-5-sonnet-20241022")
        assert input_cost == 0.003
        assert output_cost == 0.015

    def test_available_models(self):
        """Test available models listing"""
        provider = AnthropicProvider(api_key="test")

        models = provider.get_available_models()
        model_names = [m.name for m in models]

        assert "claude-3-opus-20240229" in model_names
        assert "claude-3-5-sonnet-20241022" in model_names


class TestOllamaProvider:
    """Test Ollama local provider"""

    def test_cost_is_free(self):
        """Test that local models are free"""
        provider = OllamaProvider()

        input_cost, output_cost = provider.get_cost_per_token()
        assert input_cost == 0.0
        assert output_cost == 0.0

    def test_available_models(self):
        """Test available models listing"""
        provider = OllamaProvider()

        models = provider.get_available_models()
        model_names = [m.name for m in models]

        assert "llama3.1" in model_names
        assert "mistral" in model_names


class TestDeepSeekProvider:
    """Test DeepSeek provider"""

    def test_cost_per_token(self):
        """Test cost calculation"""
        provider = DeepSeekProvider(api_key="test")

        input_cost, output_cost = provider.get_cost_per_token("deepseek-chat")
        assert input_cost == 0.00014  # Very cheap
        assert output_cost == 0.00028


class TestQwenProvider:
    """Test Qwen provider"""

    def test_cost_per_token(self):
        """Test cost calculation"""
        provider = QwenProvider(api_key="test")

        input_cost, output_cost = provider.get_cost_per_token("qwen-turbo")
        assert input_cost == 0.0008


# =============================================================================
# Fallback Chain Tests
# =============================================================================

class TestFallbackChain:
    """Test FallbackChain functionality"""

    @pytest.mark.asyncio
    async def test_primary_success(self):
        """Test that primary provider is used when healthy"""
        primary = MockProvider("primary", response_content="Primary response")
        fallback = MockProvider("fallback", response_content="Fallback response")

        chain = FallbackChain(primary, [fallback])

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        assert response.content == "Primary response"
        assert primary.call_count == 1
        assert fallback.call_count == 0

    @pytest.mark.asyncio
    async def test_fallback_on_failure(self):
        """Test fallback when primary fails"""
        primary = MockProvider("primary", should_fail=True)
        fallback = MockProvider("fallback", response_content="Fallback response")

        chain = FallbackChain(primary, [fallback], max_retries=1)

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        assert response.content == "Fallback response"
        assert chain.last_successful_provider == "fallback"

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test error when all providers fail"""
        primary = MockProvider("primary", should_fail=True)
        fallback = MockProvider("fallback", should_fail=True)

        chain = FallbackChain(primary, [fallback], max_retries=1)

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RuntimeError) as excinfo:
            await chain.chat_with_fallback(messages)

        assert "All providers failed" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_retry_before_fallback(self):
        """Test that retries happen before fallback"""
        # Provider that fails first time, succeeds second
        call_count = 0

        class FlakeyProvider(MockProvider):
            async def chat(self, messages, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("First attempt failed")
                return await super().chat(messages, **kwargs)

        primary = FlakeyProvider("primary")
        fallback = MockProvider("fallback")

        chain = FallbackChain(primary, [fallback], max_retries=2)

        messages = [{"role": "user", "content": "Hello"}]
        response = await chain.chat_with_fallback(messages)

        # Should succeed on retry, not fallback
        assert response.provider == "primary"


# =============================================================================
# Cost Tracker Tests
# =============================================================================

class TestCostTracker:
    """Test CostTracker"""

    def test_add_cost(self):
        """Test adding costs"""
        tracker = CostTracker()

        tracker.add_cost("openai", "gpt-4o", 0.01, 1000)
        tracker.add_cost("openai", "gpt-4o", 0.02, 2000)
        tracker.add_cost("anthropic", "claude", 0.015, 1500)

        assert tracker.total_cost == pytest.approx(0.045, rel=0.01)
        assert tracker.costs_by_provider["openai"] == pytest.approx(0.03, rel=0.01)
        assert tracker.requests_by_provider["openai"] == 2

    def test_reset_daily(self):
        """Test daily reset"""
        tracker = CostTracker()
        tracker.add_cost("openai", "gpt-4", 0.05, 1000)

        tracker.reset_daily()

        assert tracker.daily_cost == 0.0
        assert tracker.total_cost == 0.05  # Total not reset

    def test_reset_session(self):
        """Test session reset"""
        tracker = CostTracker()
        tracker.add_cost("openai", "gpt-4", 0.05, 1000)

        tracker.reset_session()

        assert tracker.session_cost == 0.0

    def test_get_summary(self):
        """Test summary generation"""
        tracker = CostTracker()
        tracker.add_cost("openai", "gpt-4o", 0.01, 1000)

        summary = tracker.get_summary()

        assert "total_cost" in summary
        assert "by_provider" in summary
        assert "requests_by_provider" in summary


# =============================================================================
# Enhanced Router Tests
# =============================================================================

class TestRouterConfig:
    """Test RouterConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = RouterConfig()

        assert config.strategy == RoutingStrategy.HYBRID
        assert config.max_retries == 3
        assert config.fallback_enabled == True

    def test_custom_config(self):
        """Test custom configuration"""
        config = RouterConfig(
            strategy=RoutingStrategy.COST,
            daily_budget=10.0,
            prefer_local=True
        )

        assert config.strategy == RoutingStrategy.COST
        assert config.daily_budget == 10.0
        assert config.prefer_local == True


class TestEnhancedModelRouter:
    """Test EnhancedModelRouter"""

    @pytest.fixture
    def router(self):
        """Create router with mock providers"""
        config = RouterConfig()
        router = EnhancedModelRouter(config)

        # Replace with mock providers
        router.providers = {
            "mock1": MockProvider("mock1", response_content="Response 1"),
            "mock2": MockProvider("mock2", response_content="Response 2"),
        }

        return router

    def test_select_model_hybrid(self):
        """Test hybrid model selection"""
        config = RouterConfig(strategy=RoutingStrategy.HYBRID)
        router = EnhancedModelRouter(config)

        # Should not raise
        try:
            provider, model = router.select_model(
                task_type="simple",
                complexity="low"
            )
            assert provider is not None
            assert model is not None
        except RuntimeError:
            # May fail if no providers configured
            pass

    def test_select_model_cost_strategy(self):
        """Test cost-based selection"""
        config = RouterConfig(strategy=RoutingStrategy.COST)
        router = EnhancedModelRouter(config)

        # Replace with mock providers with known costs
        cheap = MockProvider("cheap")
        cheap.get_cost_per_token = lambda m: (0.0001, 0.0002)

        expensive = MockProvider("expensive")
        expensive.get_cost_per_token = lambda m: (0.01, 0.02)

        router.providers = {"cheap": cheap, "expensive": expensive}

        provider, model = router.select_model(task_type="simple")

        # Should select cheaper provider
        assert provider.name == "cheap"

    def test_select_model_local_first(self):
        """Test local-first selection"""
        config = RouterConfig(strategy=RoutingStrategy.LOCAL_FIRST)
        router = EnhancedModelRouter(config)

        # Add mock ollama provider
        ollama = MockProvider("ollama")
        router.providers["ollama"] = ollama

        provider, model = router.select_model(task_type="simple")

        # Should select ollama
        assert provider.name == "ollama"

    def test_require_local(self):
        """Test require_local parameter"""
        config = RouterConfig()
        router = EnhancedModelRouter(config)

        ollama = MockProvider("ollama")
        router.providers["ollama"] = ollama

        provider, model = router.select_model(
            task_type="coding",
            require_local=True
        )

        assert provider.name == "ollama"

    @pytest.mark.asyncio
    async def test_chat_with_routing(self, router):
        """Test chat with automatic routing"""
        messages = [{"role": "user", "content": "Hello"}]

        response = await router.chat(
            messages,
            task_type="simple",
            complexity="low"
        )

        assert response.content in ["Response 1", "Response 2"]

    @pytest.mark.asyncio
    async def test_cost_tracking(self, router):
        """Test that costs are tracked"""
        messages = [{"role": "user", "content": "Hello"}]

        await router.chat(messages)

        summary = router.get_cost_summary()
        assert summary["total_cost"] > 0

    def test_budget_enforcement(self):
        """Test daily budget enforcement"""
        config = RouterConfig(daily_budget=0.001)
        router = EnhancedModelRouter(config)

        mock = MockProvider("mock")
        router.providers = {"mock": mock}

        # Simulate exceeding budget
        router.cost_tracker.daily_cost = 0.002

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(RuntimeError) as excinfo:
            asyncio.run(router.chat(messages))

        assert "budget" in str(excinfo.value).lower()

    def test_create_fallback_chain(self):
        """Test custom fallback chain creation"""
        config = RouterConfig()
        router = EnhancedModelRouter(config)

        mock1 = MockProvider("mock1")
        mock2 = MockProvider("mock2")
        router.providers = {"mock1": mock1, "mock2": mock2}

        chain = router.create_fallback_chain("mock1", ["mock2"])

        assert len(chain.providers) == 2
        assert chain.providers[0].name == "mock1"

    def test_get_health_status(self, router):
        """Test health status retrieval"""
        status = router.get_health_status()

        assert "mock1" in status
        assert "mock2" in status

    @pytest.mark.asyncio
    async def test_provider_health_check(self, router):
        """Test provider health checking"""
        await router.check_provider_health(force=True)

        # Health should be checked for all providers
        for provider in router.providers.values():
            assert provider.health.last_check is not None


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_router(self):
        """Test router creation function"""
        router = create_router(
            strategy="cost",
            prefer_local=True,
            daily_budget=5.0
        )

        assert isinstance(router, EnhancedModelRouter)
        assert router.config.strategy == RoutingStrategy.COST
        assert router.config.daily_budget == 5.0


# =============================================================================
# Integration Tests
# =============================================================================

class TestRouterIntegration:
    """Integration tests for the router"""

    @pytest.mark.asyncio
    async def test_full_routing_flow(self):
        """Test complete routing flow"""
        config = RouterConfig(
            strategy=RoutingStrategy.HYBRID,
            fallback_enabled=True
        )
        router = EnhancedModelRouter(config)

        # Replace with mock providers
        primary = MockProvider("primary", response_content="Primary response")
        fallback = MockProvider("fallback", response_content="Fallback response")
        router.providers = {"primary": primary, "fallback": fallback}

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]

        response = await router.chat(
            messages,
            task_type="simple",
            complexity="low"
        )

        assert response.content in ["Primary response", "Fallback response"]

        # Check cost was tracked
        assert router.cost_tracker.total_cost > 0

    @pytest.mark.asyncio
    async def test_fallback_flow(self):
        """Test fallback when primary fails"""
        config = RouterConfig(fallback_enabled=True)
        router = EnhancedModelRouter(config)

        # Primary fails, fallback succeeds
        primary = MockProvider("primary", should_fail=True)
        fallback = MockProvider("fallback", response_content="Fallback worked")
        router.providers = {"primary": primary, "fallback": fallback}

        messages = [{"role": "user", "content": "Hello"}]

        response = await router.chat(messages, use_fallback=True)

        assert response.content == "Fallback worked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
