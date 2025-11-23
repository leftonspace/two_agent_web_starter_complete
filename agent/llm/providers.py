"""
LLM Provider Abstractions

Multi-provider support for various LLM backends:
- OpenAI (GPT-4, GPT-4o, etc.)
- Anthropic (Claude 3 Opus, Sonnet, Haiku)
- Ollama (Local models - Llama 3, Mistral, etc.)
- DeepSeek
- Qwen

Each provider implements the LLMProvider interface for consistent usage.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
import os

# Try to import httpx, fall back to aiohttp or provide mock
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None  # type: ignore

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    aiohttp = None  # type: ignore


# =============================================================================
# Data Models
# =============================================================================

class ProviderStatus(Enum):
    """Provider health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    provider: str
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    context_window: int = 8192
    max_output_tokens: int = 4096
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """Response from a chat completion"""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata
        }


@dataclass
class ProviderHealth:
    """Health status of a provider"""
    provider: str
    status: ProviderStatus
    latency_ms: float = 0.0
    error_rate: float = 0.0
    last_check: datetime = field(default_factory=datetime.now)
    last_error: Optional[str] = None
    consecutive_failures: int = 0


# =============================================================================
# Abstract Provider
# =============================================================================

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement:
    - chat(): Send messages and get response
    - get_cost_per_token(): Return pricing info
    - health_check(): Check provider availability
    """

    def __init__(self, name: str):
        self.name = name
        self._health = ProviderHealth(
            provider=name,
            status=ProviderStatus.UNKNOWN
        )

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Send messages and get a response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (provider-specific default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            **kwargs: Additional provider-specific parameters

        Returns:
            ChatResponse with content and metadata
        """
        pass

    @abstractmethod
    def get_cost_per_token(self, model: Optional[str] = None) -> Tuple[float, float]:
        """
        Return (input_cost, output_cost) per 1K tokens.

        Args:
            model: Model name (uses default if None)

        Returns:
            Tuple of (input_cost_per_1k, output_cost_per_1k)
        """
        pass

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """
        Check provider availability and update health status.

        Returns:
            ProviderHealth with current status
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """
        Get list of available models.

        Returns:
            List of ModelInfo objects
        """
        pass

    @property
    def health(self) -> ProviderHealth:
        """Get current health status"""
        return self._health

    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        return self._health.status == ProviderStatus.HEALTHY

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None
    ) -> float:
        """Calculate cost for token usage"""
        input_cost, output_cost = self.get_cost_per_token(model)
        return (input_tokens * input_cost / 1000) + (output_tokens * output_cost / 1000)


# =============================================================================
# OpenAI Provider
# =============================================================================

class OpenAIProvider(LLMProvider):
    """
    OpenAI API provider.

    Supports GPT-4, GPT-4o, GPT-4o-mini, etc.
    """

    # Model pricing (per 1K tokens)
    MODEL_COSTS = {
        "gpt-4o": (0.005, 0.015),  # $5/$15 per 1M tokens
        "gpt-4o-mini": (0.00015, 0.0006),  # $0.15/$0.60 per 1M tokens
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4": (0.03, 0.06),
        "gpt-3.5-turbo": (0.0005, 0.0015),
        "o1-preview": (0.015, 0.060),
        "o1-mini": (0.003, 0.012),
    }

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o-mini",
        timeout: float = 60.0
    ):
        super().__init__("openai")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        if not HAS_HTTPX:
            raise RuntimeError(
                "httpx is required for OpenAI provider. Install with: pip install httpx"
            )

        model = model or self.default_model
        start_time = datetime.now()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in payload:
                payload[key] = value

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency = (datetime.now() - start_time).total_seconds() * 1000

            # Extract usage
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # Update health
            self._health.status = ProviderStatus.HEALTHY
            self._health.latency_ms = latency
            self._health.consecutive_failures = 0

            return ChatResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=usage.get("total_tokens", input_tokens + output_tokens),
                cost=self.calculate_cost(input_tokens, output_tokens, model),
                latency_ms=latency,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                metadata={"id": data.get("id")}
            )

        except Exception as e:
            self._health.consecutive_failures += 1
            self._health.last_error = str(e)
            if self._health.consecutive_failures >= 3:
                self._health.status = ProviderStatus.UNHEALTHY
            raise

    def get_cost_per_token(self, model: Optional[str] = None) -> Tuple[float, float]:
        model = model or self.default_model
        return self.MODEL_COSTS.get(model, (0.01, 0.03))

    async def health_check(self) -> ProviderHealth:
        if not HAS_HTTPX:
            self._health.status = ProviderStatus.UNHEALTHY
            self._health.last_error = "httpx not installed"
            return self._health

        if not self.api_key:
            self._health.status = ProviderStatus.UNHEALTHY
            self._health.last_error = "API key not configured"
            return self._health

        try:
            # Test actual API connectivity with a lightweight request
            start_time = datetime.now()
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()

            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._health.status = ProviderStatus.HEALTHY
            self._health.last_check = datetime.now()
            self._health.latency_ms = latency
            self._health.consecutive_failures = 0

        except Exception as e:
            self._health.status = ProviderStatus.UNHEALTHY
            self._health.last_error = str(e)
            self._health.consecutive_failures += 1

        return self._health

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("gpt-4o", "openai", 0.005, 0.015, 128000, 4096, True, True, True),
            ModelInfo("gpt-4o-mini", "openai", 0.00015, 0.0006, 128000, 16384, True, True, True),
            ModelInfo("gpt-4-turbo", "openai", 0.01, 0.03, 128000, 4096, True, True, True),
            ModelInfo("gpt-4", "openai", 0.03, 0.06, 8192, 4096, True, True, False),
            ModelInfo("gpt-3.5-turbo", "openai", 0.0005, 0.0015, 16384, 4096, True, True, False),
            ModelInfo("o1-preview", "openai", 0.015, 0.060, 128000, 32768, False, False, False),
            ModelInfo("o1-mini", "openai", 0.003, 0.012, 128000, 65536, False, False, False),
        ]


# =============================================================================
# Anthropic Provider
# =============================================================================

class AnthropicProvider(LLMProvider):
    """
    Anthropic API provider.

    Supports Claude 3 Opus, Sonnet, Haiku.
    """

    MODEL_COSTS = {
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-sonnet-20240229": (0.003, 0.015),
        "claude-3-5-sonnet-20241022": (0.003, 0.015),
        "claude-3-haiku-20240307": (0.00025, 0.00125),
        "claude-3-5-haiku-20241022": (0.001, 0.005),
    }

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.anthropic.com/v1",
        default_model: str = "claude-3-5-sonnet-20241022",
        timeout: float = 60.0
    ):
        super().__init__("anthropic")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        if not HAS_HTTPX:
            raise RuntimeError(
                "httpx is required for Anthropic provider. Install with: pip install httpx"
            )

        model = model or self.default_model
        start_time = datetime.now()

        # Extract system message if present
        system_message = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature
        }
        if system_message:
            payload["system"] = system_message

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency = (datetime.now() - start_time).total_seconds() * 1000

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            self._health.status = ProviderStatus.HEALTHY
            self._health.latency_ms = latency
            self._health.consecutive_failures = 0

            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            return ChatResponse(
                content=content,
                model=model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=self.calculate_cost(input_tokens, output_tokens, model),
                latency_ms=latency,
                finish_reason=data.get("stop_reason", "end_turn"),
                metadata={"id": data.get("id")}
            )

        except Exception as e:
            self._health.consecutive_failures += 1
            self._health.last_error = str(e)
            if self._health.consecutive_failures >= 3:
                self._health.status = ProviderStatus.UNHEALTHY
            raise

    def get_cost_per_token(self, model: Optional[str] = None) -> Tuple[float, float]:
        model = model or self.default_model
        return self.MODEL_COSTS.get(model, (0.003, 0.015))

    async def health_check(self) -> ProviderHealth:
        # Anthropic doesn't have a simple health endpoint, so we try a minimal request
        self._health.last_check = datetime.now()
        self._health.status = ProviderStatus.HEALTHY if self.api_key else ProviderStatus.UNHEALTHY
        return self._health

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("claude-3-opus-20240229", "anthropic", 0.015, 0.075, 200000, 4096),
            ModelInfo("claude-3-5-sonnet-20241022", "anthropic", 0.003, 0.015, 200000, 8192),
            ModelInfo("claude-3-sonnet-20240229", "anthropic", 0.003, 0.015, 200000, 4096),
            ModelInfo("claude-3-haiku-20240307", "anthropic", 0.00025, 0.00125, 200000, 4096),
            ModelInfo("claude-3-5-haiku-20241022", "anthropic", 0.001, 0.005, 200000, 8192),
        ]


# =============================================================================
# Ollama Provider (Local)
# =============================================================================

class OllamaProvider(LLMProvider):
    """
    Ollama provider for local LLMs.

    Supports Llama 3, Mistral, CodeLlama, and other local models.
    Free (no API costs) but requires Ollama running locally.
    """

    DEFAULT_MODEL = "llama3.1"

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3.1",
        timeout: float = 120.0
    ):
        super().__init__("ollama")
        self.host = host
        self.default_model = model
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        model = model or self.default_model
        start_time = datetime.now()

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency = (datetime.now() - start_time).total_seconds() * 1000

            # Estimate tokens (Ollama may not always report)
            content = data.get("message", {}).get("content", "")
            input_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)

            self._health.status = ProviderStatus.HEALTHY
            self._health.latency_ms = latency
            self._health.consecutive_failures = 0

            return ChatResponse(
                content=content,
                model=model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=0.0,  # Local is free
                latency_ms=latency,
                finish_reason=data.get("done_reason", "stop"),
                metadata={"model": data.get("model")}
            )

        except Exception as e:
            self._health.consecutive_failures += 1
            self._health.last_error = str(e)
            if self._health.consecutive_failures >= 3:
                self._health.status = ProviderStatus.UNHEALTHY
            raise

    def get_cost_per_token(self, model: Optional[str] = None) -> Tuple[float, float]:
        return (0.0, 0.0)  # Local models are free

    async def health_check(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()

            self._health.status = ProviderStatus.HEALTHY
            self._health.last_check = datetime.now()
            self._health.consecutive_failures = 0

        except Exception as e:
            self._health.status = ProviderStatus.UNHEALTHY
            self._health.last_error = str(e)
            self._health.consecutive_failures += 1

        return self._health

    async def list_local_models(self) -> List[str]:
        """Get list of models available locally"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.host}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def get_available_models(self) -> List[ModelInfo]:
        # Common Ollama models
        return [
            ModelInfo("llama3.1", "ollama", 0.0, 0.0, 128000, 4096),
            ModelInfo("llama3.1:70b", "ollama", 0.0, 0.0, 128000, 4096),
            ModelInfo("llama3.2", "ollama", 0.0, 0.0, 128000, 4096),
            ModelInfo("mistral", "ollama", 0.0, 0.0, 32000, 4096),
            ModelInfo("mixtral", "ollama", 0.0, 0.0, 32000, 4096),
            ModelInfo("codellama", "ollama", 0.0, 0.0, 16000, 4096),
            ModelInfo("qwen2.5:72b", "ollama", 0.0, 0.0, 128000, 4096),
            ModelInfo("deepseek-coder:33b", "ollama", 0.0, 0.0, 16000, 4096),
        ]


# =============================================================================
# DeepSeek Provider
# =============================================================================

class DeepSeekProvider(LLMProvider):
    """
    DeepSeek API provider.

    Cost-effective alternative for coding tasks.
    """

    MODEL_COSTS = {
        "deepseek-chat": (0.00014, 0.00028),  # Very cheap
        "deepseek-coder": (0.00014, 0.00028),
    }

    DEFAULT_MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.deepseek.com/v1",
        default_model: str = "deepseek-chat",
        timeout: float = 60.0
    ):
        super().__init__("deepseek")
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        model = model or self.default_model
        start_time = datetime.now()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency = (datetime.now() - start_time).total_seconds() * 1000

            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            self._health.status = ProviderStatus.HEALTHY
            self._health.latency_ms = latency
            self._health.consecutive_failures = 0

            return ChatResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=usage.get("total_tokens", input_tokens + output_tokens),
                cost=self.calculate_cost(input_tokens, output_tokens, model),
                latency_ms=latency,
                finish_reason=data["choices"][0].get("finish_reason", "stop")
            )

        except Exception as e:
            self._health.consecutive_failures += 1
            self._health.last_error = str(e)
            if self._health.consecutive_failures >= 3:
                self._health.status = ProviderStatus.UNHEALTHY
            raise

    def get_cost_per_token(self, model: Optional[str] = None) -> Tuple[float, float]:
        model = model or self.default_model
        return self.MODEL_COSTS.get(model, (0.00014, 0.00028))

    async def health_check(self) -> ProviderHealth:
        self._health.last_check = datetime.now()
        self._health.status = ProviderStatus.HEALTHY if self.api_key else ProviderStatus.UNHEALTHY
        return self._health

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("deepseek-chat", "deepseek", 0.00014, 0.00028, 64000, 4096),
            ModelInfo("deepseek-coder", "deepseek", 0.00014, 0.00028, 64000, 4096),
        ]


# =============================================================================
# Qwen Provider
# =============================================================================

class QwenProvider(LLMProvider):
    """
    Qwen (Alibaba) API provider.

    Available via DashScope API or local deployment.
    """

    MODEL_COSTS = {
        "qwen-turbo": (0.0008, 0.002),
        "qwen-plus": (0.002, 0.006),
        "qwen-max": (0.004, 0.012),
    }

    DEFAULT_MODEL = "qwen-turbo"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://dashscope.aliyuncs.com/api/v1",
        default_model: str = "qwen-turbo",
        timeout: float = 60.0
    ):
        super().__init__("qwen")
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ChatResponse:
        model = model or self.default_model
        start_time = datetime.now()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # DashScope uses a different format
        payload = {
            "model": model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["parameters"]["max_tokens"] = max_tokens

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/services/aigc/text-generation/generation",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

            latency = (datetime.now() - start_time).total_seconds() * 1000

            output = data.get("output", {})
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            self._health.status = ProviderStatus.HEALTHY
            self._health.latency_ms = latency
            self._health.consecutive_failures = 0

            return ChatResponse(
                content=output.get("text", ""),
                model=model,
                provider=self.name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost=self.calculate_cost(input_tokens, output_tokens, model),
                latency_ms=latency,
                finish_reason=output.get("finish_reason", "stop")
            )

        except Exception as e:
            self._health.consecutive_failures += 1
            self._health.last_error = str(e)
            if self._health.consecutive_failures >= 3:
                self._health.status = ProviderStatus.UNHEALTHY
            raise

    def get_cost_per_token(self, model: Optional[str] = None) -> Tuple[float, float]:
        model = model or self.default_model
        return self.MODEL_COSTS.get(model, (0.0008, 0.002))

    async def health_check(self) -> ProviderHealth:
        self._health.last_check = datetime.now()
        self._health.status = ProviderStatus.HEALTHY if self.api_key else ProviderStatus.UNHEALTHY
        return self._health

    def get_available_models(self) -> List[ModelInfo]:
        return [
            ModelInfo("qwen-turbo", "qwen", 0.0008, 0.002, 8000, 1500),
            ModelInfo("qwen-plus", "qwen", 0.002, 0.006, 32000, 2000),
            ModelInfo("qwen-max", "qwen", 0.004, 0.012, 32000, 2000),
        ]


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    'ProviderStatus',

    # Data classes
    'ModelInfo',
    'ChatResponse',
    'ProviderHealth',

    # Base class
    'LLMProvider',

    # Providers
    'OpenAIProvider',
    'AnthropicProvider',
    'OllamaProvider',
    'DeepSeekProvider',
    'QwenProvider',
]
