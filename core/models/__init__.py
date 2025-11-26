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

    # Create provider
    provider = AnthropicProvider()

    # Check availability
    if provider.is_available():
        # List models
        for model in provider.get_models():
            print(f"{model.name}: {model.tier.value}")

        # Make completion
        result = await provider.complete(
            messages=[Message(role="user", content="Hello!")],
            model="sonnet"
        )
        print(result.content)
        print(f"Cost: ${result.cost:.4f}")

    # Stream completion
    async for token in provider.stream(
        messages=[Message(role="user", content="Tell me a story")],
        model="haiku"
    ):
        print(token, end="", flush=True)

    # Use provider registry for multi-provider support
    from core.models import ProviderRegistry

    registry = ProviderRegistry()
    registry.register(AnthropicProvider())
    # registry.register(OpenAIProvider())  # Future

    result = await registry.complete(
        messages=[Message(role="user", content="Hello!")],
        model="sonnet"  # Registry finds appropriate provider
    )
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
    # Registry
    "ProviderRegistry",
    # Anthropic
    "AnthropicProvider",
    "ANTHROPIC_MODELS",
    "RateLimiter",
    "get_anthropic_provider",
    "quick_complete",
]
