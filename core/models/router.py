"""
PHASE 7.3: Model Router

Routes requests to appropriate models based on complexity, availability,
and budget constraints.

Usage:
    from core.models.router import ModelRouter, RoutingStrategy

    router = ModelRouter()

    # Route a request
    selection = router.route(
        request="Design a microservices architecture",
        domain="code_generation"
    )
    print(f"Selected: {selection.provider}:{selection.model}")

    # Change strategy
    router.set_strategy(RoutingStrategy.QUALITY_OPTIMIZED)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel

from .complexity import ComplexityAssessor, ComplexityLevel, ComplexityResult
from .provider import ModelInfo, ModelTier
from .registry import ProviderRegistry, get_registry


# Configure logging
logger = logging.getLogger(__name__)


# Default routing config path
DEFAULT_ROUTING_PATH = "config/models/routing.yaml"


# ============================================================================
# Enums
# ============================================================================


class RoutingStrategy(str, Enum):
    """Routing strategies for model selection."""
    COST_OPTIMIZED = "cost_optimized"       # Prefer cheapest that can handle
    QUALITY_OPTIMIZED = "quality_optimized"  # Prefer best quality
    BALANCED = "balanced"                    # Balance cost and quality
    LOCAL_ONLY = "local_only"               # Only use local models
    API_ONLY = "api_only"                   # Only use API models
    WITH_LOCAL = "with_local"               # Use local when appropriate


class BudgetAction(str, Enum):
    """Action to take when budget is exceeded."""
    DOWNGRADE = "downgrade"  # Try cheaper model
    BLOCK = "block"          # Reject request
    WARN = "warn"            # Allow but warn


# ============================================================================
# Data Models
# ============================================================================


class ModelSelection(BaseModel):
    """Result of model routing."""
    provider: str
    model: str
    model_info: Optional[ModelInfo] = None
    complexity: ComplexityLevel
    complexity_result: Optional[ComplexityResult] = None
    estimated_cost: float = 0.0
    fallback_chain: List[str] = []
    strategy_used: str = ""
    reasons: List[str] = []

    class Config:
        arbitrary_types_allowed = True


@dataclass
class BudgetState:
    """Current budget state for routing decisions."""
    daily_spent: float = 0.0
    daily_limit: float = 50.0
    request_limit: float = 1.0
    enabled: bool = True

    def can_afford(self, estimated_cost: float) -> bool:
        """Check if budget allows this cost."""
        if not self.enabled:
            return True

        if estimated_cost > self.request_limit:
            return False

        if self.daily_spent + estimated_cost > self.daily_limit:
            return False

        return True

    def remaining_daily(self) -> float:
        """Get remaining daily budget."""
        return max(0.0, self.daily_limit - self.daily_spent)

    def record_spend(self, amount: float) -> None:
        """Record spending."""
        self.daily_spent += amount


class RoutingConfig:
    """Configuration loaded from routing.yaml."""

    def __init__(self, config_data: Dict[str, Any]):
        """Initialize from config data."""
        self.routing_tables = config_data.get("routing_tables", {})
        self.fallback_chains = config_data.get("fallback_chains", {})
        self.critical_overrides = config_data.get("critical_overrides", {})
        self.budget_config = config_data.get("budget", {})
        self.current_strategy = config_data.get("current_strategy", "api_only")
        self.strategy_settings = config_data.get("strategy_settings", {})

    def get_routing_table(self, strategy: str) -> Dict[str, str]:
        """Get routing table for strategy."""
        return self.routing_tables.get(strategy, self.routing_tables.get("api_only", {}))

    def get_fallbacks(self, model_key: str) -> List[str]:
        """Get fallback chain for a model."""
        return self.fallback_chains.get(model_key, [])

    def is_critical_blocked(self, model_key: str) -> bool:
        """Check if model is blocked for critical tasks."""
        blocked = self.critical_overrides.get("blocked_models", [])
        return model_key in blocked


# ============================================================================
# Budget Controller
# ============================================================================


class BudgetController:
    """
    Controls budget enforcement for routing decisions.

    Tracks spending and determines if models are affordable.
    """

    def __init__(
        self,
        daily_limit: float = 50.0,
        request_limit: float = 1.0,
        enabled: bool = True,
    ):
        """
        Initialize budget controller.

        Args:
            daily_limit: Maximum daily spend in USD
            request_limit: Maximum per-request spend in USD
            enabled: Whether budget enforcement is active
        """
        self._state = BudgetState(
            daily_limit=daily_limit,
            request_limit=request_limit,
            enabled=enabled,
        )
        self._minimum_tier = ModelTier.LOW

    @property
    def enabled(self) -> bool:
        """Check if budget enforcement is enabled."""
        return self._state.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable budget enforcement."""
        self._state.enabled = value

    def can_afford(self, model_info: ModelInfo, estimated_tokens: int = 4000) -> bool:
        """
        Check if model is affordable.

        Args:
            model_info: Model to check
            estimated_tokens: Estimated tokens for request

        Returns:
            True if model is within budget
        """
        cost = self.estimate_cost(model_info, estimated_tokens)
        return self._state.can_afford(cost)

    def estimate_cost(
        self,
        model_info: ModelInfo,
        estimated_tokens: int = 4000,
        input_ratio: float = 0.7,
    ) -> float:
        """
        Estimate cost for a model call.

        Args:
            model_info: Model to estimate for
            estimated_tokens: Total estimated tokens
            input_ratio: Ratio of input to total tokens

        Returns:
            Estimated cost in USD
        """
        input_tokens = int(estimated_tokens * input_ratio)
        output_tokens = estimated_tokens - input_tokens

        return model_info.estimate_cost(input_tokens, output_tokens)

    def record_usage(self, model_info: ModelInfo, input_tokens: int, output_tokens: int) -> None:
        """Record actual usage."""
        cost = model_info.estimate_cost(input_tokens, output_tokens)
        self._state.record_spend(cost)

    def get_state(self) -> BudgetState:
        """Get current budget state."""
        return self._state

    def reset_daily(self) -> None:
        """Reset daily spending (called at midnight)."""
        self._state.daily_spent = 0.0

    def set_minimum_tier(self, tier: ModelTier) -> None:
        """Set minimum tier for downgrade protection."""
        self._minimum_tier = tier


# ============================================================================
# Model Router
# ============================================================================


class ModelRouter:
    """
    Route requests to appropriate models.

    Uses complexity assessment, budget constraints, and strategy
    to select the best model for each request.
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        assessor: Optional[ComplexityAssessor] = None,
        budget_controller: Optional[BudgetController] = None,
        config_path: Optional[str] = None,
    ):
        """
        Initialize router.

        Args:
            registry: Provider registry (uses global if not specified)
            assessor: Complexity assessor (creates new if not specified)
            budget_controller: Budget controller (creates new if not specified)
            config_path: Path to routing config YAML
        """
        self._registry = registry
        self._assessor = assessor or ComplexityAssessor()
        self._budget = budget_controller or BudgetController()
        self._config = self._load_config(config_path)
        self._strategy = RoutingStrategy(self._config.current_strategy)

    @property
    def registry(self) -> ProviderRegistry:
        """Get provider registry (lazy load)."""
        if self._registry is None:
            self._registry = get_registry()
        return self._registry

    def _load_config(self, path: Optional[str] = None) -> RoutingConfig:
        """Load routing configuration."""
        if path is None:
            path = self._find_config_path()

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return RoutingConfig(data)
        except FileNotFoundError:
            logger.warning(f"Routing config not found: {path}, using defaults")
            return self._default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing routing config: {e}")
            return self._default_config()

    def _find_config_path(self) -> str:
        """Find config file path."""
        candidates = [
            DEFAULT_ROUTING_PATH,
            f"../{DEFAULT_ROUTING_PATH}",
            str(Path(__file__).parent.parent.parent / DEFAULT_ROUTING_PATH),
        ]

        for candidate in candidates:
            if Path(candidate).exists():
                return candidate

        return DEFAULT_ROUTING_PATH

    def _default_config(self) -> RoutingConfig:
        """Create default configuration."""
        return RoutingConfig({
            "routing_tables": {
                "api_only": {
                    "trivial": "anthropic:haiku",
                    "low": "anthropic:haiku",
                    "medium": "anthropic:sonnet",
                    "high": "anthropic:sonnet",
                    "critical": "anthropic:opus",
                },
            },
            "fallback_chains": {
                "anthropic:opus": ["anthropic:sonnet"],
                "anthropic:sonnet": ["anthropic:haiku"],
            },
            "current_strategy": "api_only",
        })

    def route(
        self,
        request: str,
        domain: str = "default",
        context: Optional[Dict[str, Any]] = None,
        estimated_tokens: int = 4000,
    ) -> ModelSelection:
        """
        Route a request to the appropriate model.

        Args:
            request: The request text
            domain: Task domain
            context: Additional context
            estimated_tokens: Estimated tokens for budget calculation

        Returns:
            ModelSelection with chosen model and metadata
        """
        # 1. Assess complexity
        complexity_result = self._assessor.assess(request, domain, context)
        complexity_level = complexity_result.level

        reasons = [f"Complexity: {complexity_level.value}"]

        # 2. Get base model from routing table
        model_key = self._get_model_for_complexity(complexity_level)
        reasons.append(f"Strategy {self._strategy.value} → {model_key}")

        # 3. Check critical override
        if complexity_level == ComplexityLevel.CRITICAL:
            if self._config.is_critical_blocked(model_key):
                # Upgrade to preferred critical model
                preferred = self._config.critical_overrides.get("preferred_models", [])
                if preferred:
                    model_key = preferred[0]
                    reasons.append(f"Critical override → {model_key}")

        # 4. Parse provider and model
        provider, model = self._parse_model_key(model_key)

        # 5. Check availability and get model info
        model_info = self._get_model_info(provider, model)

        if model_info is None:
            # Model not available, try fallbacks
            fallbacks = self._config.get_fallbacks(model_key)
            for fb in fallbacks:
                fb_provider, fb_model = self._parse_model_key(fb)
                model_info = self._get_model_info(fb_provider, fb_model)
                if model_info:
                    provider, model = fb_provider, fb_model
                    model_key = fb
                    reasons.append(f"Fallback to {fb} (original unavailable)")
                    break

        # 6. Check budget constraints
        estimated_cost = 0.0
        if model_info:
            estimated_cost = self._budget.estimate_cost(model_info, estimated_tokens)

            if not self._budget.can_afford(model_info, estimated_tokens):
                # Try to downgrade
                downgraded = self._downgrade_model(model_key, complexity_level, estimated_tokens)
                if downgraded:
                    provider, model = self._parse_model_key(downgraded)
                    model_info = self._get_model_info(provider, model)
                    if model_info:
                        estimated_cost = self._budget.estimate_cost(model_info, estimated_tokens)
                    model_key = downgraded
                    reasons.append(f"Budget downgrade → {downgraded}")

        # 7. Build fallback chain
        fallback_chain = self._build_fallback_chain(model_key, complexity_level)

        return ModelSelection(
            provider=provider,
            model=model,
            model_info=model_info,
            complexity=complexity_level,
            complexity_result=complexity_result,
            estimated_cost=estimated_cost,
            fallback_chain=fallback_chain,
            strategy_used=self._strategy.value,
            reasons=reasons,
        )

    def _get_model_for_complexity(self, level: ComplexityLevel) -> str:
        """Get model key for complexity level based on current strategy."""
        table = self._config.get_routing_table(self._strategy.value)
        return table.get(level.value, "anthropic:sonnet")

    def _parse_model_key(self, model_key: str) -> Tuple[str, str]:
        """Parse 'provider:model' format."""
        if ":" in model_key:
            parts = model_key.split(":", 1)
            return parts[0], parts[1]
        return "anthropic", model_key

    def _get_model_info(self, provider: str, model: str) -> Optional[ModelInfo]:
        """Get model info from registry."""
        try:
            prov = self.registry.get(provider)
            if prov and prov.is_available():
                return prov.get_model_info(model)
        except Exception as e:
            logger.debug(f"Could not get model info for {provider}:{model}: {e}")
        return None

    def _downgrade_model(
        self,
        model_key: str,
        complexity: ComplexityLevel,
        estimated_tokens: int,
    ) -> Optional[str]:
        """Try to find a cheaper model that's still acceptable."""
        fallbacks = self._config.get_fallbacks(model_key)

        for fb in fallbacks:
            provider, model = self._parse_model_key(fb)
            model_info = self._get_model_info(provider, model)

            if model_info and self._budget.can_afford(model_info, estimated_tokens):
                # Check if this model is acceptable for the complexity
                if self._is_acceptable_for_complexity(model_info, complexity):
                    return fb

        return None

    def _is_acceptable_for_complexity(
        self,
        model_info: ModelInfo,
        complexity: ComplexityLevel,
    ) -> bool:
        """Check if model tier is acceptable for complexity level."""
        # Critical requires high tier
        if complexity == ComplexityLevel.CRITICAL:
            return model_info.tier in (ModelTier.HIGH, ModelTier.HIGHEST)

        # High prefers high tier but can use medium
        if complexity == ComplexityLevel.HIGH:
            return model_info.tier in (ModelTier.MEDIUM, ModelTier.HIGH, ModelTier.HIGHEST)

        # Medium and below can use any tier
        return True

    def _build_fallback_chain(
        self,
        model_key: str,
        complexity: ComplexityLevel,
    ) -> List[str]:
        """Build list of fallback models."""
        fallbacks = self._config.get_fallbacks(model_key)

        # Filter out models that are blocked for critical
        if complexity == ComplexityLevel.CRITICAL:
            fallbacks = [
                fb for fb in fallbacks
                if not self._config.is_critical_blocked(fb)
            ]

        return fallbacks

    def set_strategy(self, strategy: RoutingStrategy) -> None:
        """
        Change routing strategy.

        Args:
            strategy: New strategy to use
        """
        self._strategy = strategy
        logger.info(f"Routing strategy changed to: {strategy.value}")

    def get_strategy(self) -> RoutingStrategy:
        """Get current routing strategy."""
        return self._strategy

    def get_routing_table(self) -> Dict[str, str]:
        """Get current routing table."""
        return self._config.get_routing_table(self._strategy.value)

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies."""
        return list(self._config.routing_tables.keys())

    def set_budget_enabled(self, enabled: bool) -> None:
        """Enable or disable budget enforcement."""
        self._budget.enabled = enabled

    def get_budget_state(self) -> BudgetState:
        """Get current budget state."""
        return self._budget.get_state()


# ============================================================================
# Convenience Functions
# ============================================================================


# Module-level cache
_router_cache: Optional[ModelRouter] = None


def get_router(config_path: Optional[str] = None) -> ModelRouter:
    """
    Get model router (cached).

    Args:
        config_path: Optional path to routing config

    Returns:
        ModelRouter instance
    """
    global _router_cache

    if _router_cache is None:
        _router_cache = ModelRouter(config_path=config_path)

    return _router_cache


def reset_router() -> None:
    """Reset cached router."""
    global _router_cache
    _router_cache = None


def route_request(
    request: str,
    domain: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> ModelSelection:
    """
    Quick route a request.

    Args:
        request: Request text
        domain: Task domain
        context: Optional context

    Returns:
        ModelSelection
    """
    return get_router().route(request, domain, context)
