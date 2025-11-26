"""
PHASE 7.3: Model Provider Layer

Unified interface for interacting with LLM providers.
Enables intelligent routing between models based on task complexity.

Providers:
- AnthropicProvider: Claude models (Haiku, Sonnet, Opus)
- (Future) OpenAIProvider: GPT models
- (Future) OllamaProvider: Local models

Usage:
    from core.models import AnthropicProvider, Message, Completion

    # Create provider directly
    provider = AnthropicProvider()
    result = await provider.complete(
        messages=[Message(role="user", content="Hello!")],
        model="sonnet"
    )

    # Or use the global registry (recommended)
    from core.models import get_registry, complete

    # Registry auto-loads config and finds providers
    registry = get_registry()

    # Get provider for any model
    provider = registry.get_by_model("sonnet")

    # Or complete directly through registry
    result = await registry.complete(
        messages=[Message(role="user", content="Hello!")],
        model="sonnet"
    )

    # Quick completion helper
    result = await complete(
        messages=[Message(role="user", content="Hello!")],
        model="haiku"
    )

    # List available models
    for model in registry.list_available_models():
        print(f"{model.name}: {model.tier.value} - ${model.cost_per_1k_input}/1K")
"""

from .provider import (
    # Enums
    ModelTier,
    StopReason,
    # Data models
    Message,
    ToolDefinition,
    ToolCall,
    ToolResult,
    Completion,
    ModelInfo,
    ProviderStatus,
    # Base class
    ModelProvider,
    # Registry
    ProviderRegistry,
)

from .anthropic_provider import (
    # Provider implementation
    AnthropicProvider,
    # Model definitions
    ANTHROPIC_MODELS,
    # Rate limiter (for advanced use)
    RateLimiter,
    # Convenience functions
    get_anthropic_provider,
    quick_complete,
)

from .config import (
    # Configuration models
    ModelsConfig,
    ProviderConfig,
    ModelConfig,
    RateLimitsConfig,
    CostControlsConfig,
    # Convenience functions
    load_config,
    get_provider_config,
    get_model_info as get_model_info_from_config,
    list_available_models as list_available_models_from_config,
)

from .registry import (
    # Registry class
    ProviderRegistry as ConfigurableRegistry,
    # Exceptions
    ProviderNotFoundError,
    ModelNotFoundError,
    ProviderNotAvailableError,
    # Global registry
    get_registry,
    reset_registry,
    # Convenience functions
    complete,
    get_model_info,
    list_models,
)

from .complexity import (
    # Enums and data classes
    ComplexityLevel,
    ComplexityFeatures,
    ComplexityResult,
    # Main class
    ComplexityAssessor,
    # Convenience functions
    get_assessor,
    assess_complexity,
    reset_assessor,
)

from .router import (
    # Enums
    RoutingStrategy,
    BudgetAction,
    # Data classes
    ModelSelection,
    BudgetState,
    # Main classes
    BudgetController,
    ModelRouter,
    # Convenience functions
    get_router,
    reset_router,
    route_request,
)


__all__ = [
    # Enums
    "ModelTier",
    "StopReason",
    # Data models
    "Message",
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    "Completion",
    "ModelInfo",
    "ProviderStatus",
    # Base class
    "ModelProvider",
    # Simple registry (from provider.py)
    "ProviderRegistry",
    # Anthropic
    "AnthropicProvider",
    "ANTHROPIC_MODELS",
    "RateLimiter",
    "get_anthropic_provider",
    "quick_complete",
    # Configuration
    "ModelsConfig",
    "ProviderConfig",
    "ModelConfig",
    "RateLimitsConfig",
    "CostControlsConfig",
    "load_config",
    "get_provider_config",
    # Configurable registry
    "ConfigurableRegistry",
    "ProviderNotFoundError",
    "ModelNotFoundError",
    "ProviderNotAvailableError",
    "get_registry",
    "reset_registry",
    # Convenience functions
    "complete",
    "get_model_info",
    "list_models",
    # Complexity assessment
    "ComplexityLevel",
    "ComplexityFeatures",
    "ComplexityResult",
    "ComplexityAssessor",
    "get_assessor",
    "assess_complexity",
    "reset_assessor",
    # Model routing
    "RoutingStrategy",
    "BudgetAction",
    "ModelSelection",
    "BudgetState",
    "BudgetController",
    "ModelRouter",
    "get_router",
    "reset_router",
    "route_request",
]
