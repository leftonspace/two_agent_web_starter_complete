"""
Model Routing and Budget Test Configuration

Shared fixtures for testing model routing, complexity assessment,
and budget management.

Run tests with: pytest tests/models/ -v
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set test database URL before imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

# Import models modules
from core.models import (
    # Provider classes
    ModelProvider,
    ModelInfo,
    ModelTier,
    Message,
    Completion,
    StopReason,
    # Complexity
    ComplexityAssessor,
    ComplexityLevel,
    # Router
    ModelRouter,
    RoutingStrategy,
    ModelSelection,
    # Budget
    BudgetController,
    BudgetCategory,
    BudgetPeriod,
    BudgetStatus,
    SpendingRecord,
    AlertLevel,
    get_budget_controller,
    reset_budget_controller,
)
from core.models.router import reset_router
from core.models.complexity import reset_assessor


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure custom markers for model tests."""
    config.addinivalue_line(
        "markers", "routing: marks tests related to model routing"
    )
    config.addinivalue_line(
        "markers", "budget: marks tests related to budget management"
    )
    config.addinivalue_line(
        "markers", "complexity: marks tests related to complexity assessment"
    )
    config.addinivalue_line(
        "markers", "integration: marks integration tests"
    )


# ============================================================================
# Mock Provider Implementation
# ============================================================================


class MockModelProvider(ModelProvider):
    """Mock provider for testing without real API calls."""

    def __init__(
        self,
        name: str = "mock",
        available: bool = True,
        models: Optional[List[ModelInfo]] = None,
        fail_on: Optional[List[str]] = None,
    ):
        self.name = name
        self._available = available
        self._fail_on = fail_on or []
        self._call_count = 0
        self._last_request: Optional[Dict[str, Any]] = None

        # Default models if not specified
        self._models = models or [
            ModelInfo(
                name="haiku",
                provider="mock",
                tier=ModelTier.LOW,
                max_context=100000,
                max_output_tokens=4096,
                cost_per_1k_input=0.00025,
                cost_per_1k_output=0.00125,
            ),
            ModelInfo(
                name="sonnet",
                provider="mock",
                tier=ModelTier.MEDIUM,
                max_context=200000,
                max_output_tokens=8192,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
            ),
            ModelInfo(
                name="opus",
                provider="mock",
                tier=ModelTier.HIGH,
                max_context=200000,
                max_output_tokens=8192,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
            ),
        ]

    async def complete(
        self,
        messages: List[Message],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        tools: Optional[List[Any]] = None,
        **kwargs,
    ) -> Completion:
        """Mock completion that returns test response."""
        self._call_count += 1
        self._last_request = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
        }

        # Simulate failures for specific models
        if model in self._fail_on:
            raise Exception(f"Mock failure for {model}")

        # Return mock completion
        return Completion(
            content=f"Mock response from {model}",
            model=model,
            stop_reason=StopReason.END_TURN,
            input_tokens=100,
            output_tokens=50,
        )

    def stream(
        self,
        messages: List[Message],
        model: str,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Mock streaming that yields test chunks."""

        async def _stream():
            yield f"Mock "
            yield f"stream "
            yield f"from {model}"

        return _stream()

    def get_models(self) -> List[ModelInfo]:
        """Return list of available models."""
        return self._models

    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """Get info for a specific model."""
        for m in self._models:
            if m.name == model or m.full_name == model:
                return m
        return None

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._available

    def get_call_count(self) -> int:
        """Get number of API calls made."""
        return self._call_count

    def get_last_request(self) -> Optional[Dict[str, Any]]:
        """Get the last request made."""
        return self._last_request

    def reset_stats(self) -> None:
        """Reset call statistics."""
        self._call_count = 0
        self._last_request = None


# ============================================================================
# Mock Registry
# ============================================================================


class MockProviderRegistry:
    """Mock registry for testing."""

    def __init__(self, providers: Optional[Dict[str, MockModelProvider]] = None):
        self._providers = providers or {
            "anthropic": MockModelProvider("anthropic"),
            "local": MockModelProvider("local", available=False),
        }

    def get(self, name: str) -> Optional[MockModelProvider]:
        """Get provider by name."""
        return self._providers.get(name)

    def get_by_model(self, model: str) -> Optional[MockModelProvider]:
        """Get provider that supports the model."""
        for provider in self._providers.values():
            if provider.get_model_info(model):
                return provider
        return None

    def list_providers(self) -> List[str]:
        """List available provider names."""
        return list(self._providers.keys())

    def list_available_models(self) -> List[ModelInfo]:
        """List all available models."""
        models = []
        for provider in self._providers.values():
            if provider.is_available():
                models.extend(provider.get_models())
        return models

    def set_provider_available(self, name: str, available: bool) -> None:
        """Set provider availability for testing."""
        if name in self._providers:
            self._providers[name]._available = available

    def set_provider_failure(self, name: str, fail_models: List[str]) -> None:
        """Set which models should fail for a provider."""
        if name in self._providers:
            self._providers[name]._fail_on = fail_models


# ============================================================================
# Provider Fixtures
# ============================================================================


@pytest.fixture
def mock_provider() -> MockModelProvider:
    """Create a basic mock provider."""
    return MockModelProvider("test")


@pytest.fixture
def mock_anthropic_provider() -> MockModelProvider:
    """Create a mock Anthropic provider."""
    return MockModelProvider(
        name="anthropic",
        available=True,
        models=[
            ModelInfo(
                name="haiku",
                provider="anthropic",
                tier=ModelTier.LOW,
                max_context=200000,
                max_output_tokens=8192,
                cost_per_1k_input=0.0008,
                cost_per_1k_output=0.004,
            ),
            ModelInfo(
                name="sonnet",
                provider="anthropic",
                tier=ModelTier.MEDIUM,
                max_context=200000,
                max_output_tokens=8192,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
            ),
            ModelInfo(
                name="opus",
                provider="anthropic",
                tier=ModelTier.HIGH,
                max_context=200000,
                max_output_tokens=8192,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
            ),
        ],
    )


@pytest.fixture
def mock_registry(mock_anthropic_provider) -> MockProviderRegistry:
    """Create a mock registry with default providers."""
    return MockProviderRegistry({
        "anthropic": mock_anthropic_provider,
        "local": MockModelProvider("local", available=False),
    })


@pytest.fixture
def failing_registry() -> MockProviderRegistry:
    """Create a registry where opus fails."""
    anthropic = MockModelProvider("anthropic", fail_on=["opus"])
    return MockProviderRegistry({"anthropic": anthropic})


# ============================================================================
# Complexity Fixtures
# ============================================================================


@pytest.fixture
def assessor() -> ComplexityAssessor:
    """Create a complexity assessor."""
    reset_assessor()
    return ComplexityAssessor()


@pytest.fixture
def simple_requests() -> List[str]:
    """List of simple requests that should be trivial/low complexity."""
    return [
        "Hello!",
        "Hi there, how are you?",
        "What time is it?",
        "Thanks!",
        "Good morning",
    ]


@pytest.fixture
def complex_requests() -> List[str]:
    """List of complex requests that should be high complexity."""
    return [
        "Design a microservices architecture for a distributed payment system",
        "Write a comprehensive test suite for a React application step by step",
        "Analyze this codebase and propose refactoring strategies",
        "Create a machine learning pipeline for sentiment analysis",
    ]


@pytest.fixture
def critical_requests() -> List[str]:
    """List of critical requests that should use opus."""
    return [
        "Process a $50,000 financial transaction",
        "Review this legal contract for compliance issues",
        "Handle customer PII data for account verification",
        "Execute regulatory compliance audit",
    ]


# ============================================================================
# Router Fixtures
# ============================================================================


@pytest.fixture
def router(mock_registry) -> ModelRouter:
    """Create a model router with mock registry."""
    reset_router()
    reset_assessor()
    return ModelRouter(registry=mock_registry)


@pytest.fixture
def quality_router(mock_registry) -> ModelRouter:
    """Create a quality-optimized router."""
    reset_router()
    router = ModelRouter(registry=mock_registry)
    router.set_strategy(RoutingStrategy.QUALITY_OPTIMIZED)
    return router


@pytest.fixture
def cost_router(mock_registry) -> ModelRouter:
    """Create a cost-optimized router."""
    reset_router()
    router = ModelRouter(registry=mock_registry)
    router.set_strategy(RoutingStrategy.COST_OPTIMIZED)
    return router


# ============================================================================
# Budget Fixtures
# ============================================================================


@pytest.fixture
def budget_controller() -> BudgetController:
    """Create a fresh budget controller."""
    reset_budget_controller()
    return BudgetController()


@pytest.fixture
def exhausted_budget_controller() -> BudgetController:
    """Create a budget controller with exhausted daily budget."""
    reset_budget_controller()
    controller = BudgetController()

    # Exhaust production daily budget
    for _ in range(25):
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model="opus",
            input_tokens=5000,
            output_tokens=2000,
            cost_cad=1.00,
        )
        controller.record_spend(record)

    return controller


@pytest.fixture
def warning_budget_controller() -> BudgetController:
    """Create a budget controller at warning threshold (80%)."""
    reset_budget_controller()
    controller = BudgetController()

    # Spend 80% of daily budget ($16 of $20)
    for _ in range(16):
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model="sonnet",
            input_tokens=2000,
            output_tokens=1000,
            cost_cad=1.00,
        )
        controller.record_spend(record)

    return controller


@pytest.fixture
def spending_record() -> SpendingRecord:
    """Create a sample spending record."""
    return SpendingRecord.create(
        category=BudgetCategory.PRODUCTION,
        provider="anthropic",
        model="sonnet",
        input_tokens=1000,
        output_tokens=500,
        cost_cad=0.0525,
    )


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
def test_database():
    """Set up in-memory test database."""
    from database import create_all_tables, drop_all_tables, reset_engine
    # Import models to ensure they're registered with Base
    from database.models import CostLog, BudgetState, CostAggregate

    reset_engine()
    create_all_tables()

    yield

    drop_all_tables()
    reset_engine()


@pytest.fixture
def db_budget_controller(test_database) -> BudgetController:
    """Create a budget controller with database persistence."""
    reset_budget_controller()
    return BudgetController(use_database=True)


# ============================================================================
# Test Helpers
# ============================================================================


@pytest.fixture
def make_spending_record():
    """Factory fixture for creating spending records."""

    def _make(
        category: BudgetCategory = BudgetCategory.PRODUCTION,
        provider: str = "anthropic",
        model: str = "sonnet",
        cost_cad: float = 0.05,
        input_tokens: int = 1000,
        output_tokens: int = 500,
    ) -> SpendingRecord:
        return SpendingRecord.create(
            category=category,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cad=cost_cad,
        )

    return _make


@pytest.fixture
def assert_complexity_level():
    """Helper to assert complexity levels."""

    def _assert(assessor: ComplexityAssessor, request: str, expected_level: ComplexityLevel):
        result = assessor.assess(request)
        assert result.level == expected_level, (
            f"Expected {expected_level.value} but got {result.level.value} "
            f"for request: {request[:50]}..."
        )

    return _assert
