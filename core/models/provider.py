"""
PHASE 7.3: Model Provider Abstraction Layer

Unified interface for all model providers (Anthropic, OpenAI, local).
Enables intelligent routing between models based on task complexity.

Usage:
    from core.models import ModelProvider, Message, Completion

    # Use concrete provider
    from core.models import AnthropicProvider

    provider = AnthropicProvider()
    result = await provider.complete(
        messages=[Message(role="user", content="Hello!")],
        model="sonnet"
    )
    print(result.content)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class ModelTier(str, Enum):
    """Model capability/cost tiers."""
    LOW = "low"           # Fast, cheap (Haiku)
    MEDIUM = "medium"     # Balanced (Sonnet)
    HIGH = "high"         # Capable (Opus)
    HIGHEST = "highest"   # Most capable


class StopReason(str, Enum):
    """Reasons for completion ending."""
    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens"
    STOP_SEQUENCE = "stop_sequence"
    TOOL_USE = "tool_use"
    ERROR = "error"


# ============================================================================
# Data Models
# ============================================================================


class Message(BaseModel):
    """A message in a conversation."""
    role: Literal["user", "assistant", "system"]
    content: str

    class Config:
        frozen = True


class ToolDefinition(BaseModel):
    """Definition of a tool that can be called by the model."""
    name: str
    description: str
    input_schema: Dict[str, Any]

    class Config:
        frozen = True


class ToolCall(BaseModel):
    """A tool call made by the model."""
    id: str
    name: str
    input: Dict[str, Any]


class ToolResult(BaseModel):
    """Result of a tool call to send back to the model."""
    tool_use_id: str
    content: str
    is_error: bool = False


class Completion(BaseModel):
    """Result of a model completion."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    latency_ms: int
    tool_calls: List[ToolCall] = Field(default_factory=list)
    cost: float = 0.0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens


class ModelInfo(BaseModel):
    """Information about a model."""
    name: str
    provider: str
    tier: ModelTier
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_context: int
    max_output_tokens: int = 4096
    supports_vision: bool = False
    supports_tools: bool = True
    supports_streaming: bool = True
    aliases: List[str] = Field(default_factory=list)

    @field_validator("cost_per_1k_input", "cost_per_1k_output")
    @classmethod
    def validate_cost(cls, v: float) -> float:
        """Ensure costs are non-negative."""
        if v < 0:
            raise ValueError("Cost cannot be negative")
        return v

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for given token counts."""
        return (
            input_tokens / 1000 * self.cost_per_1k_input +
            output_tokens / 1000 * self.cost_per_1k_output
        )


class ProviderStatus(BaseModel):
    """Health status of a provider."""
    provider: str
    is_available: bool
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    models_available: List[str] = Field(default_factory=list)


# ============================================================================
# Abstract Base Provider
# ============================================================================


class ModelProvider(ABC):
    """
    Abstract base class for model providers.

    All providers must implement:
    - complete(): Send messages and get response
    - stream(): Stream response tokens
    - get_models(): List available models
    - is_available(): Check provider availability
    """

    def __init__(self, name: str):
        """
        Initialize provider.

        Args:
            name: Provider name (e.g., "anthropic", "openai")
        """
        self.name = name
        self._model_cache: Dict[str, ModelInfo] = {}

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: Optional[List[ToolDefinition]] = None,
        tool_choice: Optional[str] = None,
        system: Optional[str] = None,
        stop_sequences: Optional[List[str]] = None,
    ) -> Completion:
        """
        Generate a completion for the given messages.

        Args:
            messages: List of conversation messages
            model: Model identifier or alias
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            tools: Optional list of tools the model can call
            tool_choice: How to choose tools ("auto", "any", "none", or specific name)
            system: System prompt (if not included in messages)
            stop_sequences: Sequences that stop generation

        Returns:
            Completion with response and metadata
        """
        pass

    @abstractmethod
    def stream(
        self,
        messages: List[Message],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens.

        Args:
            messages: List of conversation messages
            model: Model identifier or alias
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt
            **kwargs: Additional provider-specific parameters

        Yields:
            String tokens as they are generated

        Note:
            Implementations should be async generators (async def with yield).
        """
        # This is an abstract method - implementations should use async def
        raise NotImplementedError

    @abstractmethod
    def get_models(self) -> List[ModelInfo]:
        """
        Get list of available models.

        Returns:
            List of ModelInfo for each available model
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available (has API key, etc.).

        Returns:
            True if provider can be used
        """
        pass

    def get_model_info(self, model: str) -> Optional[ModelInfo]:
        """
        Get info for a specific model.

        Args:
            model: Model name or alias

        Returns:
            ModelInfo if found, None otherwise
        """
        # Check cache first
        if model in self._model_cache:
            return self._model_cache[model]

        # Search by name or alias
        for info in self.get_models():
            if info.name == model or model in info.aliases:
                self._model_cache[model] = info
                return info

        return None

    def resolve_model(self, model: str) -> str:
        """
        Resolve model alias to actual model name.

        Args:
            model: Model name or alias

        Returns:
            Actual model name
        """
        info = self.get_model_info(model)
        if info:
            return info.name
        return model

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
            model: Model used

        Returns:
            Estimated cost in USD
        """
        info = self.get_model_info(model)
        if info:
            return info.estimate_cost(input_tokens, output_tokens)
        return 0.0

    async def health_check(self) -> ProviderStatus:
        """
        Check provider health.

        Returns:
            ProviderStatus with availability info
        """
        import time

        if not self.is_available():
            return ProviderStatus(
                provider=self.name,
                is_available=False,
                error_message="Provider not configured (missing API key)"
            )

        try:
            start = time.perf_counter()
            # Try a minimal completion
            await self.complete(
                messages=[Message(role="user", content="Hi")],
                model=self.get_models()[0].name if self.get_models() else "unknown",
                max_tokens=5,
            )
            latency = (time.perf_counter() - start) * 1000

            return ProviderStatus(
                provider=self.name,
                is_available=True,
                latency_ms=latency,
                models_available=[m.name for m in self.get_models()]
            )
        except Exception as e:
            return ProviderStatus(
                provider=self.name,
                is_available=False,
                error_message=str(e)
            )


# ============================================================================
# Provider Registry
# ============================================================================


class ProviderRegistry:
    """
    Registry for managing multiple model providers.

    Allows selecting providers by name or finding the best provider
    for a given model.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._providers: Dict[str, ModelProvider] = {}

    def register(self, provider: ModelProvider) -> None:
        """
        Register a provider.

        Args:
            provider: Provider instance to register
        """
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[ModelProvider]:
        """
        Get provider by name.

        Args:
            name: Provider name

        Returns:
            Provider if found
        """
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())

    def list_all_models(self) -> List[ModelInfo]:
        """Get all models from all providers."""
        models = []
        for provider in self._providers.values():
            if provider.is_available():
                models.extend(provider.get_models())
        return models

    def find_provider_for_model(self, model: str) -> Optional[ModelProvider]:
        """
        Find provider that supports a given model.

        Args:
            model: Model name or alias

        Returns:
            Provider if found
        """
        for provider in self._providers.values():
            if provider.is_available() and provider.get_model_info(model):
                return provider
        return None

    async def complete(
        self,
        messages: List[Message],
        model: str,
        **kwargs: Any,
    ) -> Completion:
        """
        Complete using the appropriate provider for the model.

        Args:
            messages: Conversation messages
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            Completion result

        Raises:
            ValueError: If no provider found for model
        """
        provider = self.find_provider_for_model(model)
        if not provider:
            raise ValueError(f"No provider found for model: {model}")
        return await provider.complete(messages, model, **kwargs)
