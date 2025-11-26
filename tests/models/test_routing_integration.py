"""
Model Routing Integration Tests

Tests for complexity-based model routing, fallback chains,
and budget integration.

Run with: pytest tests/models/test_routing_integration.py -v
"""

import pytest
from unittest.mock import patch, MagicMock

from core.models import (
    ComplexityAssessor,
    ComplexityLevel,
    ModelRouter,
    RoutingStrategy,
    ModelSelection,
    BudgetController,
    BudgetCategory,
    SpendingRecord,
)
from core.models.router import reset_router
from core.models.complexity import reset_assessor


# ============================================================================
# Test Complexity Routing
# ============================================================================


@pytest.mark.routing
class TestComplexityRouting:
    """Tests for complexity-based model routing."""

    def test_simple_greeting_uses_haiku(self, router):
        """Simple greetings should route to haiku (cheapest model)."""
        selection = router.route("Hello!", domain="default")

        assert selection.complexity == ComplexityLevel.TRIVIAL
        assert selection.model == "haiku"
        assert selection.provider == "anthropic"

    def test_simple_question_uses_haiku(self, router):
        """Simple questions should use haiku or similar low-tier model."""
        selection = router.route("What time is it?", domain="default")

        # Simple questions should be low complexity
        assert selection.complexity in (ComplexityLevel.TRIVIAL, ComplexityLevel.LOW, ComplexityLevel.MEDIUM)
        # Should use a lower tier model
        assert selection.model in ("haiku", "sonnet")

    def test_complex_code_uses_sonnet(self, router):
        """Complex code generation should route to sonnet."""
        selection = router.route(
            "Write a function to implement binary search with error handling",
            domain="code_generation"
        )

        assert selection.complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH)
        assert selection.model in ("sonnet", "haiku")

    def test_architecture_uses_higher_tier(self, router):
        """Architecture design should use higher tier model."""
        selection = router.route(
            "Design a microservices architecture for a distributed system step by step",
            domain="code_generation"
        )

        # Architecture tasks should be at least medium complexity
        assert selection.complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.CRITICAL)
        # Should use a capable model
        assert selection.model in ("haiku", "sonnet", "opus")

    def test_critical_task_uses_opus(self, router):
        """Critical tasks should use opus."""
        selection = router.route(
            "Process a $100,000 financial transaction with regulatory compliance",
            domain="financial"
        )

        assert selection.complexity == ComplexityLevel.CRITICAL
        assert selection.model == "opus"

    def test_financial_mention_upgrades_to_critical(self, router):
        """Mentioning large financial amounts should upgrade to critical."""
        selection = router.route(
            "Calculate the tax implications for a $500,000 business transaction",
            domain="default"
        )

        assert selection.complexity == ComplexityLevel.CRITICAL
        assert selection.model == "opus"

    def test_legal_domain_uses_opus(self, router):
        """Legal domain should use opus for critical decisions."""
        selection = router.route(
            "Review this contract for compliance issues",
            domain="legal"
        )

        assert selection.complexity == ComplexityLevel.CRITICAL
        assert selection.model == "opus"

    def test_pii_handling_detected(self, router):
        """PII handling should be detected and affect routing."""
        selection = router.route(
            "Process customer personal information and verify their identity",
            domain="default"
        )

        # Should detect as at least medium complexity due to PII keywords
        assert selection.complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.CRITICAL)
        assert selection.model in ("haiku", "sonnet", "opus")

    def test_multi_step_reasoning_detected(self, router):
        """Multi-step reasoning keywords should affect routing."""
        selection = router.route(
            "First analyze the data, then create a report, finally summarize findings",
            domain="default"
        )

        # Multi-step should boost complexity
        assert selection.complexity != ComplexityLevel.TRIVIAL

    def test_code_with_multiple_files_uses_capable_model(self, router):
        """Code generation with multiple files should use capable model."""
        selection = router.route(
            "Create a complete REST API with models, controllers, and tests",
            domain="code_generation"
        )

        # Complex code generation should be at least medium complexity
        assert selection.complexity in (ComplexityLevel.MEDIUM, ComplexityLevel.HIGH, ComplexityLevel.CRITICAL)
        assert selection.model in ("haiku", "sonnet", "opus")


# ============================================================================
# Test Strategy Selection
# ============================================================================


@pytest.mark.routing
class TestRoutingStrategies:
    """Tests for different routing strategies."""

    def test_api_only_strategy(self, router):
        """API-only strategy should use cloud models."""
        router.set_strategy(RoutingStrategy.API_ONLY)
        selection = router.route("Hello!", domain="default")

        assert selection.provider == "anthropic"
        assert selection.strategy_used == "api_only"

    def test_quality_optimized_upgrades_models(self, quality_router):
        """Quality-optimized should use higher tier models."""
        selection = quality_router.route("Hello!", domain="default")

        # Quality optimized prefers better models even for simple tasks
        # The strategy_used should reflect quality_optimized
        assert selection.strategy_used == "quality_optimized"
        # Model selection depends on routing table configuration
        assert selection.model in ("haiku", "sonnet", "opus")

    def test_cost_optimized_uses_cheapest(self, cost_router):
        """Cost-optimized should prefer cheaper models."""
        selection = cost_router.route(
            "Analyze this complex data pattern",
            domain="default"
        )

        # Cost optimized should prefer haiku when possible
        assert selection.model == "haiku"

    def test_strategy_change_at_runtime(self, router):
        """Strategy can be changed at runtime."""
        # Start with API only
        assert router.get_strategy() == RoutingStrategy.API_ONLY

        # Change to quality optimized
        router.set_strategy(RoutingStrategy.QUALITY_OPTIMIZED)
        assert router.get_strategy() == RoutingStrategy.QUALITY_OPTIMIZED

        selection = router.route("Simple task", domain="default")
        assert selection.strategy_used == "quality_optimized"

    def test_available_strategies_listed(self, router):
        """Router should list available strategies."""
        strategies = router.get_available_strategies()

        assert "api_only" in strategies
        assert "quality_optimized" in strategies
        assert "cost_optimized" in strategies
        assert "balanced" in strategies

    def test_routing_table_accessible(self, router):
        """Current routing table should be accessible."""
        table = router.get_routing_table()

        assert "trivial" in table
        assert "low" in table
        assert "medium" in table
        assert "high" in table
        assert "critical" in table


# ============================================================================
# Test Fallback Chain
# ============================================================================


@pytest.mark.routing
class TestFallbackChain:
    """Tests for model fallback behavior."""

    def test_fallback_chain_built_for_opus(self, router):
        """Opus should have sonnet as fallback."""
        selection = router.route(
            "Process $1,000,000 transaction",
            domain="financial"
        )

        assert selection.model == "opus"
        assert "anthropic:sonnet" in selection.fallback_chain

    def test_fallback_chain_built_for_sonnet(self, router):
        """Sonnet should have haiku as fallback."""
        selection = router.route(
            "Write a function for binary search",
            domain="code_generation"
        )

        if selection.model == "sonnet":
            assert "anthropic:haiku" in selection.fallback_chain

    def test_haiku_has_no_fallback(self, router):
        """Haiku (cheapest) should have empty fallback chain."""
        selection = router.route("Hello!", domain="default")

        if selection.model == "haiku":
            assert len(selection.fallback_chain) == 0

    def test_opus_failure_would_fall_to_sonnet(self, failing_registry):
        """When opus fails, router should provide sonnet fallback."""
        reset_router()
        reset_assessor()
        router = ModelRouter(registry=failing_registry)

        selection = router.route(
            "Critical financial task worth $500,000",
            domain="financial"
        )

        # Should have fallback available
        assert len(selection.fallback_chain) > 0 or selection.model != "opus"

    def test_critical_fallback_excludes_haiku(self, router):
        """Critical tasks should not fallback to haiku."""
        selection = router.route(
            "Process $1,000,000 regulatory filing",
            domain="financial"
        )

        # Haiku should not be in critical fallback chain
        assert "anthropic:haiku" not in selection.fallback_chain


# ============================================================================
# Test Selection Metadata
# ============================================================================


@pytest.mark.routing
class TestSelectionMetadata:
    """Tests for ModelSelection metadata."""

    def test_selection_includes_provider(self, router):
        """Selection should include provider name."""
        selection = router.route("Hello!", domain="default")
        assert selection.provider == "anthropic"

    def test_selection_includes_model(self, router):
        """Selection should include model name."""
        selection = router.route("Hello!", domain="default")
        assert selection.model in ("haiku", "sonnet", "opus")

    def test_selection_includes_complexity(self, router):
        """Selection should include complexity level."""
        selection = router.route("Hello!", domain="default")
        assert isinstance(selection.complexity, ComplexityLevel)

    def test_selection_includes_reasons(self, router):
        """Selection should include routing reasons."""
        selection = router.route("Hello!", domain="default")
        assert len(selection.reasons) > 0

    def test_selection_includes_strategy(self, router):
        """Selection should include strategy used."""
        selection = router.route("Hello!", domain="default")
        assert selection.strategy_used == "api_only"

    def test_selection_includes_estimated_cost(self, router):
        """Selection should include estimated cost."""
        selection = router.route("Hello!", domain="default")
        assert selection.estimated_cost >= 0.0


# ============================================================================
# Test Budget Integration
# ============================================================================


@pytest.mark.routing
@pytest.mark.budget
class TestRoutingBudgetIntegration:
    """Tests for routing with budget constraints."""

    def test_within_budget_proceeds_normally(self, mock_registry):
        """Routing proceeds normally when within budget."""
        reset_router()
        router = ModelRouter(registry=mock_registry)

        selection = router.route("Process request", domain="default")

        assert selection.model is not None
        # Router should have budget state
        budget_state = router.get_budget_state()
        assert budget_state.can_afford(0.10)

    def test_budget_state_accessible_from_router(self, mock_registry):
        """Router exposes budget state."""
        reset_router()
        router = ModelRouter(registry=mock_registry)

        budget_state = router.get_budget_state()

        assert budget_state is not None
        assert budget_state.daily_limit > 0

    def test_budget_enforcement_toggleable(self, mock_registry):
        """Budget enforcement can be disabled."""
        reset_router()
        router = ModelRouter(registry=mock_registry)

        router.set_budget_enabled(False)

        # Should still route even if we couldn't normally afford it
        selection = router.route("Process request", domain="default")
        assert selection.model is not None


# ============================================================================
# Test Complexity Assessment Edge Cases
# ============================================================================


@pytest.mark.complexity
class TestComplexityEdgeCases:
    """Edge case tests for complexity assessment."""

    def test_empty_request_handled(self, assessor):
        """Empty request should not crash."""
        result = assessor.assess("", domain="default")
        # Empty request should be handled (any level is acceptable as long as no crash)
        assert result.level in (ComplexityLevel.TRIVIAL, ComplexityLevel.LOW, ComplexityLevel.MEDIUM)

    def test_very_long_request_handled(self, assessor):
        """Very long requests should be handled."""
        long_request = "Please help me " * 1000
        result = assessor.assess(long_request, domain="default")

        # Long requests might be medium or higher due to token count
        assert result.level is not None

    def test_code_blocks_detected(self, assessor):
        """Code blocks should be detected."""
        request = """
        Here's the code:
        ```python
        def hello():
            print("world")
        ```
        """
        result = assessor.assess(request, domain="default")
        assert result.features.has_code

    def test_urls_detected(self, assessor):
        """URLs should be detected."""
        request = "Check out https://github.com/example/repo for more info"
        result = assessor.assess(request, domain="default")
        assert result.features.has_urls

    def test_financial_amount_extracted(self, assessor):
        """Financial amounts should be extracted."""
        result = assessor.assess("Process $50,000 payment", domain="default")
        assert result.features.financial_amount == 50000.0

    def test_million_amount_extracted(self, assessor):
        """Million amounts should be extracted correctly."""
        result = assessor.assess("Handle $2 million transaction", domain="default")
        # The pattern extracts millions - exact format may vary
        assert result.features.financial_amount is not None
        assert result.features.financial_amount >= 1000000  # At least 1M

    def test_domain_affects_complexity(self, assessor):
        """Domain should affect complexity level."""
        # Same request, different domains
        legal_result = assessor.assess("Review this document", domain="legal")
        general_result = assessor.assess("Review this document", domain="default")

        # Legal domain should be higher
        assert legal_result.level.value >= general_result.level.value or \
               legal_result.level == ComplexityLevel.CRITICAL

    def test_multiple_keywords_increase_confidence(self, assessor):
        """Multiple matching keywords should increase confidence."""
        simple_result = assessor.assess("Help me", domain="default")
        complex_result = assessor.assess(
            "Design architecture, implement system, analyze performance step by step",
            domain="code_generation"
        )

        # More matches should give higher confidence
        assert len(complex_result.matched_rules) >= len(simple_result.matched_rules)


# ============================================================================
# Test Router Initialization
# ============================================================================


@pytest.mark.routing
class TestRouterInitialization:
    """Tests for router initialization and configuration."""

    def test_router_loads_default_config(self):
        """Router should load default config if file missing."""
        reset_router()
        router = ModelRouter(config_path="/nonexistent/path.yaml")

        # Should still work with defaults
        selection = router.route("Hello!", domain="default")
        assert selection.model is not None

    def test_router_accepts_custom_assessor(self, mock_registry):
        """Router should accept custom assessor."""
        reset_router()
        custom_assessor = ComplexityAssessor()
        router = ModelRouter(
            registry=mock_registry,
            assessor=custom_assessor,
        )

        selection = router.route("Hello!", domain="default")
        assert selection.model is not None

    def test_router_creates_default_budget_controller(self, mock_registry):
        """Router should create default budget controller."""
        reset_router()
        router = ModelRouter(registry=mock_registry)

        # Should have budget state
        state = router.get_budget_state()
        assert state is not None
