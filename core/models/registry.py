"""
PHASE 7.3: Model Provider Registry

Central registry for managing model providers with configuration support.

Usage:
    from core.models.registry import get_registry, ProviderRegistry

    # Get global registry (auto-loads from config)
    registry = get_registry()

    # Get provider for a model
    provider = registry.get_by_model("sonnet")
    result = await provider.complete(messages, "sonnet")

    # Or use registry directly
    result = await registry.complete(messages, "sonnet")

    # List available models
    for model in registry.list_available_models():
        print(f"{model.name}: {model.tier.value}")
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Type

from .provider import (
    Completion,
    Message,
    ModelInfo,
    ModelProvider,
    ProviderStatus,
)
from .config import (
    ModelsConfig,
    ProviderConfig,
    load_config,
)


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class ProviderNotFoundError(Exception):
    """Raised when a requested provider is not found."""
    pass


class ModelNotFoundError(Exception):
    """Raised when a requested model is not found."""
    pass


class ProviderNotAvailableError(Exception):
    """Raised when a provider is not available (missing API key, etc.)."""
    pass


# ============================================================================
# Provider Registry
# ============================================================================


class ProviderRegistry:
    """
    Central registry for all model providers.

    Manages provider instances and provides model routing.
    Can load configuration from YAML.
    """

    def __init__(self, config: Optional[ModelsConfig] = None):
        """
        Initialize registry.

        Args:
            config: Optional configuration (loads from file if not provided)
        """
        self._providers: Dict[str, ModelProvider] = {}
        self._provider_configs: Dict[str, ProviderConfig] = {}
        self._config = config or load_config()
        self._model_lookup: Dict[str, str] = {}  # model name -> provider name

        # Auto-register providers from config
        self._register_from_config()

    def _register_from_config(self) -> None:
        """Register providers from configuration."""
        for provider_name in self._config.list_enabled_providers():
            provider_config = self._config.get_provider_config(provider_name)
            if provider_config:
                self._provider_configs[provider_name] = provider_config

                # Build model lookup
                for alias, model_config in provider_config.models.items():
                    self._model_lookup[alias] = provider_name
                    self._model_lookup[model_config.name] = provider_name

    # -------------------------------------------------------------------------
    # Provider Registration
    # -------------------------------------------------------------------------

    def register(self, name: str, provider: ModelProvider) -> None:
        """
        Register a provider instance.

        Args:
            name: Provider name
            provider: Provider instance
        """
        self._providers[name] = provider
        logger.debug(f"Registered provider: {name}")

        # Update model lookup
        for model in provider.get_models():
            self._model_lookup[model.name] = name
            for alias in model.aliases:
                self._model_lookup[alias] = name

    def unregister(self, name: str) -> None:
        """
        Unregister a provider.

        Args:
            name: Provider name to remove
        """
        if name in self._providers:
            del self._providers[name]
            logger.debug(f"Unregistered provider: {name}")

    def _get_or_create_provider(self, name: str) -> ModelProvider:
        """
        Get or lazily create a provider instance.

        Args:
            name: Provider name

        Returns:
            ModelProvider instance

        Raises:
            ProviderNotFoundError: If provider not in config
            ProviderNotAvailableError: If provider not available
        """
        # Return existing instance
        if name in self._providers:
            return self._providers[name]

        # Get config
        provider_config = self._provider_configs.get(name)
        if not provider_config:
            raise ProviderNotFoundError(f"Provider not found: {name}")

        # Check availability
        if not provider_config.is_available():
            api_key_env = provider_config.api_key_env or "API_KEY"
            raise ProviderNotAvailableError(
                f"Provider '{name}' not available. "
                f"Set {api_key_env} environment variable."
            )

        # Create provider instance
        provider = self._create_provider(name, provider_config)
        self._providers[name] = provider

        return provider

    def _create_provider(
        self,
        name: str,
        config: ProviderConfig
    ) -> ModelProvider:
        """
        Create a provider instance from configuration.

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            ModelProvider instance
        """
        # Import provider classes here to avoid circular imports
        if name == "anthropic":
            from .anthropic_provider import AnthropicProvider
            return AnthropicProvider(
                api_key=config.get_api_key(),
                base_url=config.base_url,
                max_retries=config.retry_attempts,
                requests_per_minute=config.rate_limits.requests_per_minute,
                tokens_per_minute=config.rate_limits.tokens_per_minute,
            )
        elif name == "openai":
            # Future: OpenAI provider
            raise ProviderNotFoundError(f"OpenAI provider not yet implemented")
        elif name == "local":
            # Future: Ollama/local provider
            raise ProviderNotFoundError(f"Local provider not yet implemented")
        else:
            raise ProviderNotFoundError(f"Unknown provider: {name}")

    # -------------------------------------------------------------------------
    # Provider Access
    # -------------------------------------------------------------------------

    def get(self, name: str) -> ModelProvider:
        """
        Get provider by name.

        Args:
            name: Provider name

        Returns:
            ModelProvider instance

        Raises:
            ProviderNotFoundError: If provider not found
            ProviderNotAvailableError: If provider not available
        """
        return self._get_or_create_provider(name)

    def get_by_model(self, model: str) -> ModelProvider:
        """
        Get provider that supports a model.

        Args:
            model: Model name or alias

        Returns:
            ModelProvider instance

        Raises:
            ModelNotFoundError: If model not found
            ProviderNotAvailableError: If provider not available
        """
        provider_name = self._model_lookup.get(model)
        if not provider_name:
            raise ModelNotFoundError(
                f"Model not found: {model}. "
                f"Available models: {', '.join(self._model_lookup.keys())}"
            )

        return self._get_or_create_provider(provider_name)

    def list_providers(self) -> List[str]:
        """Get list of configured provider names."""
        return list(self._provider_configs.keys())

    def list_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [
            name for name, config in self._provider_configs.items()
            if config.is_available()
        ]

    # -------------------------------------------------------------------------
    # Model Access
    # -------------------------------------------------------------------------

    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """
        Get information about a model.

        Args:
            model: Model name or alias

        Returns:
            ModelInfo if found
        """
        provider_name = self._model_lookup.get(model)
        if not provider_name:
            return None

        # Find model in config
        result = self._config.find_model(model)
        if result:
            provider_name, alias = result
            return self._config.get_model_info(provider_name, alias)

        return None

    def list_all_models(self) -> List[ModelInfo]:
        """Get list of all configured models."""
        return self._config.list_all_models()

    def list_available_models(self) -> List[ModelInfo]:
        """Get list of models from available providers."""
        return self._config.list_available_models()

    def resolve_model(self, model: str) -> str:
        """
        Resolve model alias to full model name.

        Args:
            model: Model name or alias

        Returns:
            Full model name
        """
        info = self.get_model_info(model)
        if info:
            return info.name
        return model

    # -------------------------------------------------------------------------
    # Completion Methods
    # -------------------------------------------------------------------------

    async def complete(
        self,
        messages: List[Message],
        model: str,
        **kwargs: Any,
    ) -> Completion:
        """
        Generate completion using appropriate provider.

        Args:
            messages: Conversation messages
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            Completion result

        Raises:
            ModelNotFoundError: If model not found
            ProviderNotAvailableError: If provider not available
        """
        provider = self.get_by_model(model)
        return await provider.complete(messages, model, **kwargs)

    async def stream(
        self,
        messages: List[Message],
        model: str,
        **kwargs: Any,
    ):
        """
        Stream completion using appropriate provider.

        Args:
            messages: Conversation messages
            model: Model to use
            **kwargs: Additional parameters

        Yields:
            String tokens
        """
        provider = self.get_by_model(model)
        async for token in provider.stream(messages, model, **kwargs):
            yield token

    # -------------------------------------------------------------------------
    # Health Checks
    # -------------------------------------------------------------------------

    async def health_check(self, provider_name: Optional[str] = None) -> Dict[str, ProviderStatus]:
        """
        Check health of providers.

        Args:
            provider_name: Specific provider to check (all if None)

        Returns:
            Dictionary of provider name to status
        """
        results = {}

        providers_to_check = (
            [provider_name] if provider_name
            else self.list_available_providers()
        )

        for name in providers_to_check:
            try:
                provider = self._get_or_create_provider(name)
                status = await provider.health_check()
                results[name] = status
            except Exception as e:
                results[name] = ProviderStatus(
                    provider=name,
                    is_available=False,
                    error_message=str(e)
                )

        return results

    # -------------------------------------------------------------------------
    # Cost Estimation
    # -------------------------------------------------------------------------

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> float:
        """
        Estimate cost for a completion.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model to use

        Returns:
            Estimated cost in USD
        """
        info = self.get_model_info(model)
        if info:
            return info.estimate_cost(input_tokens, output_tokens)
        return 0.0

    # -------------------------------------------------------------------------
    # Configuration Access
    # -------------------------------------------------------------------------

    @property
    def config(self) -> ModelsConfig:
        """Get underlying configuration."""
        return self._config

    @property
    def default_provider(self) -> str:
        """Get default provider name."""
        return self._config.default_provider

    def get_default_model(self, provider: Optional[str] = None) -> str:
        """
        Get default model for a provider.

        Args:
            provider: Provider name (uses default provider if None)

        Returns:
            Default model alias
        """
        provider = provider or self.default_provider
        return self._config.get_default_model(provider) or "sonnet"


# ============================================================================
# Global Registry
# ============================================================================


# Module-level registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry(force_reload: bool = False) -> ProviderRegistry:
    """
    Get global provider registry (singleton).

    Args:
        force_reload: Force reload from configuration

    Returns:
        ProviderRegistry instance
    """
    global _registry

    if _registry is None or force_reload:
        _registry = ProviderRegistry()

    return _registry


def reset_registry() -> None:
    """Reset global registry (for testing)."""
    global _registry
    _registry = None


# ============================================================================
# Convenience Functions
# ============================================================================


async def complete(
    messages: List[Message],
    model: str = "sonnet",
    **kwargs: Any,
) -> Completion:
    """
    Quick completion using global registry.

    Args:
        messages: Conversation messages
        model: Model to use (default: sonnet)
        **kwargs: Additional parameters

    Returns:
        Completion result
    """
    return await get_registry().complete(messages, model, **kwargs)


def get_model_info(model: str) -> Optional[ModelInfo]:
    """Get model information from global registry."""
    return get_registry().get_model_info(model)


def list_models() -> List[ModelInfo]:
    """List all available models from global registry."""
    return get_registry().list_available_models()
