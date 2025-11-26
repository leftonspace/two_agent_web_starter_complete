"""
PHASE 7.3: Anthropic Model Provider

Implementation of ModelProvider for Anthropic's Claude models.
Uses the official Anthropic Python SDK with rate limiting and retry logic.

Models:
- claude-haiku-4-5-20251001 (alias: haiku) - Fast, low cost
- claude-sonnet-4-5-20250929 (alias: sonnet) - Balanced
- claude-opus-4-5-20251101 (alias: opus) - Most capable

Usage:
    from core.models import AnthropicProvider, Message

    provider = AnthropicProvider()
    result = await provider.complete(
        messages=[Message(role="user", content="Hello!")],
        model="sonnet"  # or full name
    )
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from .provider import (
    Completion,
    Message,
    ModelInfo,
    ModelProvider,
    ModelTier,
    StopReason,
    ToolCall,
    ToolDefinition,
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Model Definitions
# ============================================================================

# Current Anthropic models with pricing (as of late 2024)
ANTHROPIC_MODELS: Dict[str, ModelInfo] = {
    "claude-haiku-4-5-20251001": ModelInfo(
        name="claude-haiku-4-5-20251001",
        provider="anthropic",
        tier=ModelTier.LOW,
        cost_per_1k_input=0.001,    # $1/M input
        cost_per_1k_output=0.005,   # $5/M output
        max_context=200000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        aliases=["haiku", "claude-haiku", "fast"],
    ),
    "claude-sonnet-4-5-20250929": ModelInfo(
        name="claude-sonnet-4-5-20250929",
        provider="anthropic",
        tier=ModelTier.MEDIUM,
        cost_per_1k_input=0.003,    # $3/M input
        cost_per_1k_output=0.015,   # $15/M output
        max_context=200000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        aliases=["sonnet", "claude-sonnet", "balanced"],
    ),
    "claude-opus-4-5-20251101": ModelInfo(
        name="claude-opus-4-5-20251101",
        provider="anthropic",
        tier=ModelTier.HIGH,
        cost_per_1k_input=0.015,    # $15/M input
        cost_per_1k_output=0.075,   # $75/M output
        max_context=200000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        aliases=["opus", "claude-opus", "capable"],
    ),
}


# ============================================================================
# Rate Limiter
# ============================================================================


class RateLimiter:
    """
    Token bucket rate limiter with exponential backoff.

    Handles both request rate limits and token limits.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            tokens_per_minute: Maximum tokens per minute
        """
        self.rpm = requests_per_minute
        self.tpm = tokens_per_minute

        # Token buckets
        self._request_tokens = float(requests_per_minute)
        self._token_bucket = float(tokens_per_minute)

        # Refill rates (per second)
        self._request_refill = requests_per_minute / 60.0
        self._token_refill = tokens_per_minute / 60.0

        # Last refill time
        self._last_refill = time.monotonic()

        # Lock for thread safety
        self._lock = asyncio.Lock()

        # Backoff state
        self._consecutive_failures = 0
        self._base_delay = 1.0

    async def acquire(self, estimated_tokens: int = 1000) -> None:
        """
        Acquire permission to make a request.

        Waits if rate limit would be exceeded.

        Args:
            estimated_tokens: Estimated tokens for this request
        """
        async with self._lock:
            self._refill()

            # Wait for request bucket
            while self._request_tokens < 1:
                wait_time = (1 - self._request_tokens) / self._request_refill
                await asyncio.sleep(min(wait_time, 1.0))
                self._refill()

            # Wait for token bucket
            while self._token_bucket < estimated_tokens:
                wait_time = (estimated_tokens - self._token_bucket) / self._token_refill
                await asyncio.sleep(min(wait_time, 1.0))
                self._refill()

            # Consume tokens
            self._request_tokens -= 1
            self._token_bucket -= estimated_tokens

    def _refill(self) -> None:
        """Refill token buckets based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now

        self._request_tokens = min(
            self.rpm,
            self._request_tokens + elapsed * self._request_refill
        )
        self._token_bucket = min(
            self.tpm,
            self._token_bucket + elapsed * self._token_refill
        )

    def record_success(self) -> None:
        """Record successful request (reset backoff)."""
        self._consecutive_failures = 0

    def record_failure(self) -> None:
        """Record failed request (increase backoff)."""
        self._consecutive_failures += 1

    def get_backoff_delay(self) -> float:
        """
        Get exponential backoff delay.

        Returns:
            Delay in seconds (0 if no failures)
        """
        if self._consecutive_failures == 0:
            return 0.0

        # Exponential backoff with jitter
        import random
        delay = self._base_delay * (2 ** (self._consecutive_failures - 1))
        jitter = random.uniform(0, delay * 0.1)
        return min(delay + jitter, 60.0)  # Cap at 60 seconds


# ============================================================================
# Anthropic Provider
# ============================================================================


class AnthropicProvider(ModelProvider):
    """
    Model provider for Anthropic's Claude models.

    Uses the official Anthropic Python SDK with:
    - Automatic rate limiting
    - Exponential backoff on errors
    - Streaming support
    - Tool use support
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100000,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            base_url: Custom API base URL (for proxies)
            max_retries: Maximum retry attempts
            requests_per_minute: Rate limit for requests
            tokens_per_minute: Rate limit for tokens
        """
        super().__init__("anthropic")

        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._base_url = base_url
        self._max_retries = max_retries
        self._rate_limiter = RateLimiter(requests_per_minute, tokens_per_minute)

        # Lazy-loaded client
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                kwargs: Dict[str, Any] = {}
                if self._api_key:
                    kwargs["api_key"] = self._api_key
                if self._base_url:
                    kwargs["base_url"] = self._base_url

                self._client = anthropic.AsyncAnthropic(**kwargs)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if provider is available (has API key)."""
        return bool(self._api_key or os.getenv("ANTHROPIC_API_KEY"))

    def get_models(self) -> List[ModelInfo]:
        """Get list of available Anthropic models."""
        return list(ANTHROPIC_MODELS.values())

    def resolve_model(self, model: str) -> str:
        """
        Resolve model alias to full model name.

        Args:
            model: Model name or alias (e.g., "sonnet", "claude-sonnet")

        Returns:
            Full model name (e.g., "claude-sonnet-4-5-20250929")
        """
        model_lower = model.lower()

        # Check each model's aliases
        for name, info in ANTHROPIC_MODELS.items():
            if model_lower == name.lower():
                return name
            if model_lower in [a.lower() for a in info.aliases]:
                return name

        # Return as-is if no match (might be a custom/new model)
        return model

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
        Generate a completion using Claude.

        Args:
            messages: Conversation messages
            model: Model name or alias
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            tools: Optional tools for the model to use
            tool_choice: How to choose tools
            system: System prompt
            stop_sequences: Sequences that stop generation

        Returns:
            Completion with response and metadata
        """
        resolved_model = self.resolve_model(model)
        client = self._get_client()

        # Prepare messages for Anthropic format
        formatted_messages = self._format_messages(messages)

        # Estimate tokens for rate limiting (rough estimate)
        estimated_tokens = sum(len(m.content) // 4 for m in messages) + max_tokens

        # Build request kwargs
        request_kwargs: Dict[str, Any] = {
            "model": resolved_model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            request_kwargs["system"] = system
        if stop_sequences:
            request_kwargs["stop_sequences"] = stop_sequences

        # Add tools if provided
        if tools:
            request_kwargs["tools"] = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.input_schema,
                }
                for t in tools
            ]
            if tool_choice:
                if tool_choice == "any":
                    request_kwargs["tool_choice"] = {"type": "any"}
                elif tool_choice == "none":
                    request_kwargs["tool_choice"] = {"type": "none"}
                elif tool_choice == "auto":
                    request_kwargs["tool_choice"] = {"type": "auto"}
                else:
                    # Specific tool name
                    request_kwargs["tool_choice"] = {
                        "type": "tool",
                        "name": tool_choice
                    }

        # Execute with retries
        last_error: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                # Wait for rate limit
                await self._rate_limiter.acquire(estimated_tokens)

                # Add backoff delay if needed
                backoff = self._rate_limiter.get_backoff_delay()
                if backoff > 0:
                    logger.debug(f"Backing off for {backoff:.2f}s (attempt {attempt + 1})")
                    await asyncio.sleep(backoff)

                # Make request
                start_time = time.perf_counter()
                response = await client.messages.create(**request_kwargs)
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                self._rate_limiter.record_success()

                # Parse response
                return self._parse_response(response, resolved_model, latency_ms)

            except Exception as e:
                last_error = e
                self._rate_limiter.record_failure()

                # Check if we should retry
                if attempt < self._max_retries and self._is_retryable(e):
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self._max_retries + 1}): {e}"
                    )
                    continue
                else:
                    break

        # All retries exhausted
        raise last_error or Exception("Unknown error")

    async def stream(
        self,
        messages: List[Message],
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream completion tokens from Claude.

        Args:
            messages: Conversation messages
            model: Model name or alias
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt
            **kwargs: Additional parameters

        Yields:
            String tokens as they are generated
        """
        resolved_model = self.resolve_model(model)
        client = self._get_client()

        # Prepare messages
        formatted_messages = self._format_messages(messages)

        # Estimate tokens for rate limiting
        estimated_tokens = sum(len(m.content) // 4 for m in messages) + max_tokens

        # Build request kwargs
        request_kwargs: Dict[str, Any] = {
            "model": resolved_model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            request_kwargs["system"] = system

        # Wait for rate limit
        await self._rate_limiter.acquire(estimated_tokens)

        # Add backoff delay if needed
        backoff = self._rate_limiter.get_backoff_delay()
        if backoff > 0:
            await asyncio.sleep(backoff)

        try:
            async with client.messages.stream(**request_kwargs) as stream:
                async for text in stream.text_stream:
                    yield text

            self._rate_limiter.record_success()

        except Exception as e:
            self._rate_limiter.record_failure()
            raise

    def _format_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Format messages for Anthropic API.

        Args:
            messages: List of Message objects

        Returns:
            List of dicts in Anthropic format
        """
        formatted = []

        for msg in messages:
            # Skip system messages (handled separately in Anthropic)
            if msg.role == "system":
                continue

            formatted.append({
                "role": msg.role,
                "content": msg.content,
            })

        return formatted

    def _parse_response(
        self,
        response: Any,
        model: str,
        latency_ms: int
    ) -> Completion:
        """
        Parse Anthropic response into Completion.

        Args:
            response: Raw Anthropic response
            model: Model used
            latency_ms: Request latency

        Returns:
            Completion object
        """
        # Extract content
        content = ""
        tool_calls: List[ToolCall] = []

        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
            elif hasattr(block, "type") and block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    input=block.input,
                ))

        # Map stop reason
        stop_reason = self._map_stop_reason(response.stop_reason)

        # Get token counts
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Calculate cost
        model_info = self.get_model_info(model)
        cost = 0.0
        if model_info:
            cost = model_info.estimate_cost(input_tokens, output_tokens)

        return Completion(
            content=content,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=stop_reason,
            latency_ms=latency_ms,
            tool_calls=tool_calls,
            cost=cost,
        )

    def _map_stop_reason(self, reason: str) -> str:
        """Map Anthropic stop reason to our enum."""
        mapping = {
            "end_turn": StopReason.END_TURN.value,
            "max_tokens": StopReason.MAX_TOKENS.value,
            "stop_sequence": StopReason.STOP_SEQUENCE.value,
            "tool_use": StopReason.TOOL_USE.value,
        }
        return mapping.get(reason, reason)

    def _is_retryable(self, error: Exception) -> bool:
        """
        Check if an error is retryable.

        Args:
            error: Exception that occurred

        Returns:
            True if request should be retried
        """
        error_str = str(error).lower()

        # Rate limit errors - always retry
        if "rate" in error_str and "limit" in error_str:
            return True

        # Server errors (5xx) - retry
        if "500" in error_str or "502" in error_str or "503" in error_str:
            return True

        # Timeout errors - retry
        if "timeout" in error_str:
            return True

        # Overloaded - retry
        if "overloaded" in error_str:
            return True

        # Connection errors - retry
        if "connection" in error_str:
            return True

        return False


# ============================================================================
# Convenience Functions
# ============================================================================


def get_anthropic_provider(
    api_key: Optional[str] = None,
    **kwargs: Any
) -> AnthropicProvider:
    """
    Get a configured Anthropic provider.

    Args:
        api_key: Optional API key (defaults to env var)
        **kwargs: Additional configuration

    Returns:
        Configured AnthropicProvider
    """
    return AnthropicProvider(api_key=api_key, **kwargs)


async def quick_complete(
    prompt: str,
    model: str = "sonnet",
    **kwargs: Any
) -> str:
    """
    Quick single-turn completion.

    Args:
        prompt: User prompt
        model: Model to use (default: sonnet)
        **kwargs: Additional parameters

    Returns:
        Response content string
    """
    provider = AnthropicProvider()
    result = await provider.complete(
        messages=[Message(role="user", content=prompt)],
        model=model,
        **kwargs
    )
    return result.content
