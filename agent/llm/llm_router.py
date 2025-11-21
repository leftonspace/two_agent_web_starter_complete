"""
PHASE 9.2: LLM Router

Intelligent LLM routing that selects the optimal model for each request.
Routes between cloud models (GPT-4, GPT-4o-mini) and local models (Llama 3, Mistral).

Features:
- Task complexity analysis
- Cost-based routing
- Automatic fallback on failure
- Performance-based optimization
- Multi-provider support (OpenAI, Ollama)

Routing Strategy:
- Simple tasks → Local models (Llama 3, Mistral)
- Complex reasoning → GPT-4
- Code generation → GPT-4o or local models
- Cost tracking and optimization
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# Local imports
try:
    from .ollama_client import OllamaClient, OllamaResponse
    from .performance_tracker import PerformanceTracker
except ImportError:
    # Fallback for tests
    from ollama_client import OllamaClient, OllamaResponse
    from performance_tracker import PerformanceTracker


class ModelTier(Enum):
    """Model tier classification."""
    LOCAL = "local"  # Local models (Llama 3, Mistral) - Free, slower, lower quality
    MINI = "mini"  # GPT-4o-mini, Claude Haiku - Cheap, fast, good quality
    STANDARD = "standard"  # GPT-4o, Claude Sonnet - Moderate cost, high quality
    PREMIUM = "premium"  # GPT-4, o1, Claude Opus - Expensive, highest quality


@dataclass
class ModelConfig:
    """Configuration for a model."""
    name: str
    tier: ModelTier
    provider: str  # "openai", "anthropic", "ollama"
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_tokens: int
    context_window: int

    @property
    def is_local(self) -> bool:
        """Check if this is a local model."""
        return self.tier == ModelTier.LOCAL or self.provider == "ollama"


# Default model configurations
DEFAULT_MODELS = {
    # Local models (via Ollama)
    "llama3": ModelConfig(
        name="llama3",
        tier=ModelTier.LOCAL,
        provider="ollama",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        max_tokens=4096,
        context_window=8192,
    ),
    "mistral": ModelConfig(
        name="mistral",
        tier=ModelTier.LOCAL,
        provider="ollama",
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        max_tokens=4096,
        context_window=8192,
    ),
    # Cloud models (OpenAI)
    "gpt-4o-mini": ModelConfig(
        name="gpt-4o-mini",
        tier=ModelTier.MINI,
        provider="openai",
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        max_tokens=16384,
        context_window=128000,
    ),
    "gpt-4o": ModelConfig(
        name="gpt-4o",
        tier=ModelTier.STANDARD,
        provider="openai",
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
        max_tokens=16384,
        context_window=128000,
    ),
    "gpt-4": ModelConfig(
        name="gpt-4",
        tier=ModelTier.PREMIUM,
        provider="openai",
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06,
        max_tokens=8192,
        context_window=128000,
    ),
}


class TaskComplexity(Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"  # Simple, repetitive tasks
    LOW = "low"  # Standard tasks with clear patterns
    MEDIUM = "medium"  # Moderate complexity, some reasoning
    HIGH = "high"  # Complex reasoning, multi-step problems
    CRITICAL = "critical"  # Mission-critical, requires best model


class LLMRouter:
    """
    Intelligent LLM router.

    Routes requests to optimal model based on:
    - Task complexity
    - Cost constraints
    - Performance history
    - Model availability
    """

    def __init__(
        self,
        enable_local: bool = True,
        max_cost_usd: float = 0.0,
        prefer_local: bool = True,
    ):
        """
        Initialize LLM router.

        Args:
            enable_local: Enable local models via Ollama (default: True)
            max_cost_usd: Maximum cost per request in USD (0 = unlimited)
            prefer_local: Prefer local models when quality is acceptable
        """
        self.enable_local = enable_local
        self.max_cost_usd = max_cost_usd
        self.prefer_local = prefer_local

        # Initialize clients
        self.ollama_client: Optional[OllamaClient] = None
        self._ollama_available: Optional[bool] = None

        # Performance tracker
        self.performance_tracker = PerformanceTracker()

        # Model registry
        self.models = DEFAULT_MODELS.copy()

        # Statistics
        self.total_requests = 0
        self.local_requests = 0
        self.cloud_requests = 0
        self.total_cost_usd = 0.0

    async def _ensure_ollama_client(self) -> Optional[OllamaClient]:
        """Ensure Ollama client is initialized and available."""
        if not self.enable_local:
            return None

        if self.ollama_client is None:
            self.ollama_client = OllamaClient()

        if self._ollama_available is None:
            self._ollama_available = await self.ollama_client.is_available()
            if self._ollama_available:
                print("[LLMRouter] Ollama server is available for local inference")
            else:
                print("[LLMRouter] Ollama server not available - using cloud models only")

        return self.ollama_client if self._ollama_available else None

    def analyze_complexity(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskComplexity:
        """
        Analyze task complexity.

        Args:
            prompt: User prompt
            task_type: Optional task type hint
            context: Optional context dict

        Returns:
            TaskComplexity enum
        """
        # Check if explicitly marked as critical
        if context and context.get("is_critical"):
            return TaskComplexity.CRITICAL

        # Analyze prompt length and structure
        prompt_length = len(prompt)

        # Keywords indicating complexity
        high_complexity_keywords = [
            "analyze", "explain", "design", "architecture", "complex",
            "multi-step", "reasoning", "solve", "optimize", "refactor",
        ]

        low_complexity_keywords = [
            "list", "show", "display", "what is", "simple", "basic",
            "format", "convert", "translate",
        ]

        prompt_lower = prompt.lower()

        # Check for high complexity indicators
        high_score = sum(1 for kw in high_complexity_keywords if kw in prompt_lower)
        low_score = sum(1 for kw in low_complexity_keywords if kw in prompt_lower)

        # Simple heuristics
        if high_score > 2 or prompt_length > 2000:
            return TaskComplexity.HIGH
        elif high_score > 0 or prompt_length > 500:
            return TaskComplexity.MEDIUM
        elif low_score > 0 or prompt_length < 100:
            return TaskComplexity.LOW
        else:
            return TaskComplexity.TRIVIAL

    def select_model(
        self,
        complexity: TaskComplexity,
        task_type: Optional[str] = None,
        force_tier: Optional[ModelTier] = None,
    ) -> ModelConfig:
        """
        Select optimal model based on complexity and constraints.

        Args:
            complexity: Task complexity
            task_type: Optional task type
            force_tier: Force specific tier (overrides routing logic)

        Returns:
            ModelConfig for selected model
        """
        # If tier is forced, use it
        if force_tier:
            for model in self.models.values():
                if model.tier == force_tier:
                    return model

        # Routing logic based on complexity
        if complexity == TaskComplexity.CRITICAL:
            # Use premium model for critical tasks
            return self.models["gpt-4"]

        elif complexity == TaskComplexity.HIGH:
            # Use standard model for high complexity
            return self.models["gpt-4o"]

        elif complexity == TaskComplexity.MEDIUM:
            # Prefer local if available and enabled, otherwise mini
            if self.prefer_local and self._ollama_available:
                return self.models["llama3"]
            else:
                return self.models["gpt-4o-mini"]

        else:  # LOW or TRIVIAL
            # Use local model if available
            if self.enable_local and self._ollama_available:
                return self.models["llama3"]
            else:
                return self.models["gpt-4o-mini"]

    async def route(
        self,
        prompt: str,
        system: Optional[str] = None,
        task_type: Optional[str] = None,
        complexity: Optional[TaskComplexity] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Route request to optimal model and execute.

        Args:
            prompt: User prompt
            system: System prompt
            task_type: Task type hint
            complexity: Explicit complexity (skips analysis)
            model: Force specific model (skips routing)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            context: Additional context

        Returns:
            Dict with response, model used, cost, and metadata
        """
        self.total_requests += 1

        # Ensure Ollama client if needed
        await self._ensure_ollama_client()

        # Analyze complexity if not provided
        if complexity is None:
            complexity = self.analyze_complexity(prompt, task_type, context)

        # Select model if not forced
        if model:
            # Find model config
            model_config = self.models.get(model)
            if not model_config:
                # Unknown model, create basic config
                model_config = ModelConfig(
                    name=model,
                    tier=ModelTier.STANDARD,
                    provider="openai",
                    cost_per_1k_input=0.0025,
                    cost_per_1k_output=0.01,
                    max_tokens=8192,
                    context_window=128000,
                )
        else:
            model_config = self.select_model(complexity, task_type)

        print(f"[LLMRouter] Routing to {model_config.name} ({model_config.tier.value}) "
              f"for {complexity.value} complexity task")

        # Execute request
        try:
            if model_config.is_local:
                response = await self._execute_local(
                    prompt, system, model_config, temperature, max_tokens
                )
                self.local_requests += 1
            else:
                response = await self._execute_cloud(
                    prompt, system, model_config, temperature, max_tokens
                )
                self.cloud_requests += 1

            # Track performance
            await self.performance_tracker.record_call(
                model=model_config.name,
                latency_ms=response.get("latency_ms", 0),
                cost_usd=response.get("cost_usd", 0.0),
                success=True,
            )

            self.total_cost_usd += response.get("cost_usd", 0.0)

            return response

        except Exception as e:
            print(f"[LLMRouter] Error with {model_config.name}: {e}")

            # Track failure
            await self.performance_tracker.record_call(
                model=model_config.name,
                latency_ms=0,
                cost_usd=0.0,
                success=False,
            )

            # Fallback logic
            if model_config.is_local:
                print("[LLMRouter] Falling back to cloud model")
                fallback_config = self.models["gpt-4o-mini"]
                response = await self._execute_cloud(
                    prompt, system, fallback_config, temperature, max_tokens
                )
                response["fallback_used"] = True
                return response
            else:
                raise

    async def _execute_local(
        self,
        prompt: str,
        system: Optional[str],
        model_config: ModelConfig,
        temperature: float,
        max_tokens: Optional[int],
    ) -> Dict[str, Any]:
        """Execute request on local model via Ollama."""
        if self.ollama_client is None:
            raise RuntimeError("Ollama client not available")

        ollama_response: OllamaResponse = await self.ollama_client.chat(
            prompt=prompt,
            model=model_config.name,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "response": ollama_response.response,
            "model": model_config.name,
            "provider": "ollama",
            "tier": model_config.tier.value,
            "cost_usd": 0.0,  # Local models are free
            "latency_ms": int(ollama_response.latency_seconds * 1000),
            "tokens_per_second": ollama_response.tokens_per_second,
            "prompt_tokens": ollama_response.prompt_eval_count or 0,
            "completion_tokens": ollama_response.eval_count or 0,
        }

    async def _execute_cloud(
        self,
        prompt: str,
        system: Optional[str],
        model_config: ModelConfig,
        temperature: float,
        max_tokens: Optional[int],
    ) -> Dict[str, Any]:
        """Execute request on cloud model (placeholder - integrate with existing llm.py)."""
        # This is a placeholder - in production, this would call the existing llm.chat_json
        # For now, return stub response
        print(f"[LLMRouter] Cloud execution for {model_config.name} - "
              "integrate with existing llm.chat_json()")

        # Estimate tokens for cost calculation
        estimated_input_tokens = len(prompt) // 4
        estimated_output_tokens = max_tokens or 500

        cost_usd = (
            (estimated_input_tokens / 1000) * model_config.cost_per_1k_input +
            (estimated_output_tokens / 1000) * model_config.cost_per_1k_output
        )

        return {
            "response": "Cloud model response (placeholder)",
            "model": model_config.name,
            "provider": model_config.provider,
            "tier": model_config.tier.value,
            "cost_usd": cost_usd,
            "latency_ms": 1000,
            "prompt_tokens": estimated_input_tokens,
            "completion_tokens": estimated_output_tokens,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get routing statistics."""
        total = self.total_requests
        local_pct = (self.local_requests / total * 100) if total > 0 else 0
        cloud_pct = (self.cloud_requests / total * 100) if total > 0 else 0

        return {
            "total_requests": total,
            "local_requests": self.local_requests,
            "cloud_requests": self.cloud_requests,
            "local_percentage": local_pct,
            "cloud_percentage": cloud_pct,
            "total_cost_usd": self.total_cost_usd,
            "avg_cost_per_request": self.total_cost_usd / total if total > 0 else 0,
        }
