"""
Enhanced Model Router

Intelligent LLM routing with multi-provider support, fallback chains,
cost tracking, and automatic health checks.

Features:
- Multiple routing strategies (cost, quality, hybrid, local_first)
- Automatic fallback on provider failures
- Cost tracking and budget enforcement
- Provider health monitoring
- Task-based model selection
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio

# Handle both relative and absolute imports
try:
    from .providers import (
        LLMProvider,
        OpenAIProvider,
        AnthropicProvider,
        OllamaProvider,
        DeepSeekProvider,
        QwenProvider,
        ChatResponse,
        ProviderStatus,
        ProviderHealth,
        ModelInfo,
    )
except ImportError:
    from providers import (
        LLMProvider,
        OpenAIProvider,
        AnthropicProvider,
        OllamaProvider,
        DeepSeekProvider,
        QwenProvider,
        ChatResponse,
        ProviderStatus,
        ProviderHealth,
    ModelInfo,
)


# =============================================================================
# Enums and Configuration
# =============================================================================

class RoutingStrategy(Enum):
    """Routing strategy for model selection"""
    COST = "cost"  # Always choose cheapest option
    QUALITY = "quality"  # Always choose best quality
    HYBRID = "hybrid"  # Balance cost and quality
    LOCAL_FIRST = "local_first"  # Prefer local models
    ROUND_ROBIN = "round_robin"  # Distribute load


class TaskType(Enum):
    """Types of tasks for routing decisions"""
    PLANNING = "planning"  # Strategic planning, high-level reasoning
    CODING = "coding"  # Code generation and debugging
    REVIEW = "review"  # Code/content review
    SIMPLE = "simple"  # Simple queries, Q&A
    CREATIVE = "creative"  # Creative writing
    ANALYSIS = "analysis"  # Data analysis, complex reasoning


class Complexity(Enum):
    """Task complexity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RouterConfig:
    """Configuration for the Enhanced Model Router"""
    strategy: RoutingStrategy = RoutingStrategy.HYBRID
    cost_budget: Optional[float] = None  # Max cost per request
    daily_budget: Optional[float] = None  # Max daily cost
    prefer_local: bool = False  # Prefer local models when possible
    health_check_interval: int = 300  # Seconds between health checks
    max_retries: int = 3  # Max retries on failure
    fallback_enabled: bool = True  # Enable automatic fallback
    timeout: float = 60.0  # Default timeout

    # Provider API keys (if not in environment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"


@dataclass
class CostTracker:
    """Tracks costs across providers"""
    total_cost: float = 0.0
    daily_cost: float = 0.0
    session_cost: float = 0.0
    costs_by_provider: Dict[str, float] = field(default_factory=dict)
    costs_by_model: Dict[str, float] = field(default_factory=dict)
    requests_by_provider: Dict[str, int] = field(default_factory=dict)
    tokens_by_provider: Dict[str, int] = field(default_factory=dict)
    last_reset: datetime = field(default_factory=datetime.now)

    def add_cost(self, provider: str, model: str, cost: float, tokens: int):
        """Record a cost"""
        self.total_cost += cost
        self.daily_cost += cost
        self.session_cost += cost

        self.costs_by_provider[provider] = self.costs_by_provider.get(provider, 0) + cost
        self.costs_by_model[model] = self.costs_by_model.get(model, 0) + cost
        self.requests_by_provider[provider] = self.requests_by_provider.get(provider, 0) + 1
        self.tokens_by_provider[provider] = self.tokens_by_provider.get(provider, 0) + tokens

    def track(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        input_cost_per_1k: float = 0.01,
        output_cost_per_1k: float = 0.03
    ):
        """Track cost from token usage (convenience method matching config.py interface).

        Args:
            provider: Provider name
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            input_cost_per_1k: Cost per 1K input tokens (default: $0.01)
            output_cost_per_1k: Cost per 1K output tokens (default: $0.03)
        """
        cost = (input_tokens * input_cost_per_1k / 1000) + (output_tokens * output_cost_per_1k / 1000)
        total_tokens = input_tokens + output_tokens
        self.add_cost(provider, model, cost, total_tokens)

    def get_provider_cost(self, provider: str) -> float:
        """Get total cost for a specific provider."""
        return round(self.costs_by_provider.get(provider, 0.0), 6)

    def reset_daily(self):
        """Reset daily costs"""
        self.daily_cost = 0.0
        self.last_reset = datetime.now()

    def reset_session(self):
        """Reset session costs"""
        self.session_cost = 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary"""
        return {
            "total_cost": round(self.total_cost, 6),
            "daily_cost": round(self.daily_cost, 6),
            "session_cost": round(self.session_cost, 6),
            "by_provider": {k: round(v, 6) for k, v in self.costs_by_provider.items()},
            "by_model": {k: round(v, 6) for k, v in self.costs_by_model.items()},
            "requests_by_provider": self.requests_by_provider,
            "tokens_by_provider": self.tokens_by_provider
        }


# =============================================================================
# Fallback Chain
# =============================================================================

class FallbackChain:
    """
    Chain of providers with automatic fallback on failure.

    Tries providers in order until one succeeds.
    """

    def __init__(
        self,
        primary: LLMProvider,
        fallbacks: List[LLMProvider],
        max_retries: int = 2
    ):
        """
        Initialize fallback chain.

        Args:
            primary: Primary provider to try first
            fallbacks: List of fallback providers
            max_retries: Max retries per provider
        """
        self.chain = [primary] + fallbacks
        self.max_retries = max_retries
        self._last_successful: Optional[str] = None

    async def chat_with_fallback(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """
        Send chat with automatic fallback.

        Tries each provider in the chain until one succeeds.

        Args:
            messages: Chat messages
            model: Model to use (provider default if None)
            **kwargs: Additional parameters

        Returns:
            ChatResponse from first successful provider

        Raises:
            Exception: If all providers fail
        """
        last_error = None
        errors = []

        for provider in self.chain:
            for attempt in range(self.max_retries):
                try:
                    response = await provider.chat(messages, model, **kwargs)
                    self._last_successful = provider.name
                    return response
                except Exception as e:
                    last_error = e
                    errors.append(f"{provider.name} (attempt {attempt + 1}): {str(e)}")

                    # Wait briefly before retry
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(0.5 * (attempt + 1))

        # All providers failed
        error_summary = "\n".join(errors)
        raise RuntimeError(f"All providers failed:\n{error_summary}") from last_error

    @property
    def providers(self) -> List[LLMProvider]:
        """Get all providers in chain"""
        return self.chain

    @property
    def last_successful_provider(self) -> Optional[str]:
        """Get name of last successful provider"""
        return self._last_successful


# =============================================================================
# Enhanced Model Router
# =============================================================================

class EnhancedModelRouter:
    """
    Intelligent LLM router with multi-provider support.

    Features:
    - Multiple routing strategies
    - Automatic provider health checks
    - Cost tracking and budget enforcement
    - Fallback chains for reliability
    - Task-based model selection

    Usage:
        router = EnhancedModelRouter(config=RouterConfig(
            strategy=RoutingStrategy.HYBRID,
            daily_budget=10.0
        ))

        # Select best model for task
        provider, model = router.select_model(
            task_type="coding",
            complexity="high"
        )

        # Chat with automatic routing
        response = await router.chat(
            messages=[{"role": "user", "content": "Write a Python function"}],
            task_type="coding"
        )
    """

    # Model recommendations by task type and complexity
    MODEL_RECOMMENDATIONS = {
        TaskType.PLANNING: {
            Complexity.HIGH: [("anthropic", "claude-3-opus-20240229"), ("openai", "gpt-4")],
            Complexity.MEDIUM: [("anthropic", "claude-3-5-sonnet-20241022"), ("openai", "gpt-4o")],
            Complexity.LOW: [("openai", "gpt-4o-mini"), ("ollama", "llama3.1")],
        },
        TaskType.CODING: {
            Complexity.HIGH: [("anthropic", "claude-3-5-sonnet-20241022"), ("openai", "gpt-4o")],
            Complexity.MEDIUM: [("deepseek", "deepseek-coder"), ("openai", "gpt-4o-mini")],
            Complexity.LOW: [("ollama", "codellama"), ("deepseek", "deepseek-coder")],
        },
        TaskType.REVIEW: {
            Complexity.HIGH: [("anthropic", "claude-3-5-sonnet-20241022"), ("openai", "gpt-4o")],
            Complexity.MEDIUM: [("openai", "gpt-4o-mini"), ("deepseek", "deepseek-chat")],
            Complexity.LOW: [("ollama", "llama3.1"), ("openai", "gpt-3.5-turbo")],
        },
        TaskType.SIMPLE: {
            Complexity.HIGH: [("openai", "gpt-4o-mini"), ("anthropic", "claude-3-haiku-20240307")],
            Complexity.MEDIUM: [("ollama", "llama3.1"), ("deepseek", "deepseek-chat")],
            Complexity.LOW: [("ollama", "mistral"), ("openai", "gpt-3.5-turbo")],
        },
        TaskType.CREATIVE: {
            Complexity.HIGH: [("anthropic", "claude-3-opus-20240229"), ("openai", "gpt-4")],
            Complexity.MEDIUM: [("anthropic", "claude-3-5-sonnet-20241022"), ("openai", "gpt-4o")],
            Complexity.LOW: [("openai", "gpt-4o-mini"), ("ollama", "llama3.1")],
        },
        TaskType.ANALYSIS: {
            Complexity.HIGH: [("openai", "o1-preview"), ("anthropic", "claude-3-opus-20240229")],
            Complexity.MEDIUM: [("openai", "gpt-4o"), ("anthropic", "claude-3-5-sonnet-20241022")],
            Complexity.LOW: [("deepseek", "deepseek-chat"), ("openai", "gpt-4o-mini")],
        },
    }

    def __init__(self, config: Optional[RouterConfig] = None):
        """
        Initialize the Enhanced Model Router.

        Args:
            config: Router configuration
        """
        self.config = config or RouterConfig()
        self.providers: Dict[str, LLMProvider] = {}
        self.cost_tracker = CostTracker()
        self._last_health_check = datetime.min
        self._round_robin_index = 0

        self._init_providers()

    def _init_providers(self):
        """Initialize all configured providers"""
        # OpenAI
        try:
            self.providers["openai"] = OpenAIProvider(
                api_key=self.config.openai_api_key,
                timeout=self.config.timeout
            )
        except Exception:
            pass

        # Anthropic
        try:
            self.providers["anthropic"] = AnthropicProvider(
                api_key=self.config.anthropic_api_key,
                timeout=self.config.timeout
            )
        except Exception:
            pass

        # DeepSeek
        try:
            self.providers["deepseek"] = DeepSeekProvider(
                api_key=self.config.deepseek_api_key,
                timeout=self.config.timeout
            )
        except Exception:
            pass

        # Qwen
        try:
            self.providers["qwen"] = QwenProvider(
                api_key=self.config.qwen_api_key,
                timeout=self.config.timeout
            )
        except Exception:
            pass

        # Ollama (local)
        try:
            self.providers["ollama"] = OllamaProvider(
                host=self.config.ollama_host,
                timeout=self.config.timeout
            )
        except Exception:
            pass

    @property
    def ollama_available(self) -> bool:
        """Check if Ollama is available"""
        ollama = self.providers.get("ollama")
        return ollama is not None and ollama.is_healthy

    async def check_provider_health(self, force: bool = False):
        """
        Check health of all providers.

        Args:
            force: Force check even if interval hasn't elapsed
        """
        now = datetime.now()
        if not force and (now - self._last_health_check).total_seconds() < self.config.health_check_interval:
            return

        self._last_health_check = now

        # Check all providers in parallel
        checks = []
        for provider in self.providers.values():
            checks.append(provider.health_check())

        await asyncio.gather(*checks, return_exceptions=True)

    def select_model(
        self,
        task_type: str = "simple",
        complexity: str = "medium",
        cost_budget: Optional[float] = None,
        require_local: bool = False
    ) -> Tuple[LLMProvider, str]:
        """
        Select best provider and model for task.

        Args:
            task_type: Type of task (planning, coding, review, simple, etc.)
            complexity: Task complexity (low, medium, high)
            cost_budget: Max cost for this request
            require_local: Whether to require a local model

        Returns:
            Tuple of (LLMProvider, model_name)
        """
        # Convert string to enums
        try:
            task = TaskType(task_type)
        except ValueError:
            task = TaskType.SIMPLE

        try:
            comp = Complexity(complexity)
        except ValueError:
            comp = Complexity.MEDIUM

        # Check local requirement
        if require_local or self.config.strategy == RoutingStrategy.LOCAL_FIRST:
            if "ollama" in self.providers and self.providers["ollama"].is_healthy:
                ollama = self.providers["ollama"]
                model = "llama3.1" if comp in [Complexity.HIGH, Complexity.MEDIUM] else "mistral"
                return ollama, model

        # Apply routing strategy
        if self.config.strategy == RoutingStrategy.COST:
            return self._select_cheapest(task, comp, cost_budget)
        elif self.config.strategy == RoutingStrategy.QUALITY:
            return self._select_best_quality(task, comp)
        elif self.config.strategy == RoutingStrategy.ROUND_ROBIN:
            return self._select_round_robin(task, comp)
        else:  # HYBRID
            return self._select_balanced(task, comp, cost_budget)

    def _select_cheapest(
        self,
        task: TaskType,
        complexity: Complexity,
        budget: Optional[float]
    ) -> Tuple[LLMProvider, str]:
        """Select cheapest available model"""
        # Priority: ollama > deepseek > qwen > openai mini > others
        cheap_order = [
            ("ollama", "llama3.1"),
            ("deepseek", "deepseek-chat"),
            ("qwen", "qwen-turbo"),
            ("openai", "gpt-3.5-turbo"),
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-haiku-20240307"),
        ]

        for provider_name, model in cheap_order:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if provider.is_healthy or provider._health.status == ProviderStatus.UNKNOWN:
                    # Check budget
                    if budget:
                        input_cost, output_cost = provider.get_cost_per_token(model)
                        # Estimate: 1000 input + 500 output tokens
                        est_cost = (1000 * input_cost + 500 * output_cost) / 1000
                        if est_cost > budget:
                            continue
                    return provider, model

        # Fallback to first available
        for provider in self.providers.values():
            return provider, provider.get_available_models()[0].name

        raise RuntimeError("No providers available")

    def _select_best_quality(
        self,
        task: TaskType,
        complexity: Complexity
    ) -> Tuple[LLMProvider, str]:
        """Select highest quality model for task"""
        recommendations = self.MODEL_RECOMMENDATIONS.get(task, {}).get(
            complexity,
            [("openai", "gpt-4o")]
        )

        for provider_name, model in recommendations:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if provider.is_healthy or provider._health.status == ProviderStatus.UNKNOWN:
                    return provider, model

        # Fallback
        return self._select_cheapest(task, complexity, None)

    def _select_balanced(
        self,
        task: TaskType,
        complexity: Complexity,
        budget: Optional[float]
    ) -> Tuple[LLMProvider, str]:
        """Select balanced model considering cost and quality"""
        recommendations = self.MODEL_RECOMMENDATIONS.get(task, {}).get(
            complexity,
            [("openai", "gpt-4o-mini")]
        )

        # Try recommended models in order
        for provider_name, model in recommendations:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if not (provider.is_healthy or provider._health.status == ProviderStatus.UNKNOWN):
                    continue

                # Check budget
                if budget:
                    input_cost, output_cost = provider.get_cost_per_token(model)
                    est_cost = (1000 * input_cost + 500 * output_cost) / 1000
                    if est_cost > budget:
                        continue

                return provider, model

        # Fallback to cheapest
        return self._select_cheapest(task, complexity, budget)

    def _select_round_robin(
        self,
        task: TaskType,
        complexity: Complexity
    ) -> Tuple[LLMProvider, str]:
        """Select provider in round-robin fashion"""
        healthy_providers = [
            (name, p) for name, p in self.providers.items()
            if p.is_healthy or p._health.status == ProviderStatus.UNKNOWN
        ]

        if not healthy_providers:
            raise RuntimeError("No healthy providers available")

        # Get next provider
        idx = self._round_robin_index % len(healthy_providers)
        self._round_robin_index += 1

        name, provider = healthy_providers[idx]
        model = provider.get_available_models()[0].name

        return provider, model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "simple",
        complexity: str = "medium",
        model: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs
    ) -> ChatResponse:
        """
        Send chat with intelligent routing.

        Args:
            messages: Chat messages
            task_type: Type of task
            complexity: Task complexity
            model: Specific model to use (overrides routing)
            use_fallback: Whether to use fallback chain
            **kwargs: Additional parameters

        Returns:
            ChatResponse
        """
        # Check daily budget
        if self.config.daily_budget and self.cost_tracker.daily_cost >= self.config.daily_budget:
            raise RuntimeError(f"Daily budget of ${self.config.daily_budget} exceeded")

        # Select provider and model
        provider, selected_model = self.select_model(
            task_type=task_type,
            complexity=complexity,
            cost_budget=self.config.cost_budget
        )

        model = model or selected_model

        if use_fallback and self.config.fallback_enabled:
            # Build fallback chain
            fallbacks = [
                p for name, p in self.providers.items()
                if name != provider.name and (p.is_healthy or p._health.status == ProviderStatus.UNKNOWN)
            ]
            chain = FallbackChain(provider, fallbacks, self.config.max_retries)

            response = await chain.chat_with_fallback(messages, model, **kwargs)
        else:
            response = await provider.chat(messages, model, **kwargs)

        # Track cost
        self.cost_tracker.add_cost(
            response.provider,
            response.model,
            response.cost,
            response.total_tokens
        )

        return response

    def create_fallback_chain(
        self,
        primary_provider: str,
        fallback_providers: Optional[List[str]] = None
    ) -> FallbackChain:
        """
        Create a custom fallback chain.

        Args:
            primary_provider: Name of primary provider
            fallback_providers: List of fallback provider names

        Returns:
            FallbackChain instance
        """
        primary = self.providers.get(primary_provider)
        if not primary:
            raise ValueError(f"Unknown provider: {primary_provider}")

        if fallback_providers:
            fallbacks = [
                self.providers[name]
                for name in fallback_providers
                if name in self.providers
            ]
        else:
            fallbacks = [
                p for name, p in self.providers.items()
                if name != primary_provider
            ]

        return FallbackChain(primary, fallbacks, self.config.max_retries)

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a specific provider by name"""
        return self.providers.get(name)

    def get_all_providers(self) -> Dict[str, LLMProvider]:
        """Get all providers"""
        return self.providers

    def get_health_status(self) -> Dict[str, ProviderHealth]:
        """Get health status of all providers"""
        return {
            name: provider.health
            for name, provider in self.providers.items()
        }

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        return self.cost_tracker.get_summary()

    def reset_session_costs(self):
        """Reset session cost tracking"""
        self.cost_tracker.reset_session()

    def reset_daily_costs(self):
        """Reset daily cost tracking"""
        self.cost_tracker.reset_daily()


# =============================================================================
# Convenience Functions
# =============================================================================

def create_router(
    strategy: str = "hybrid",
    prefer_local: bool = False,
    daily_budget: Optional[float] = None
) -> EnhancedModelRouter:
    """
    Create a configured router.

    Args:
        strategy: Routing strategy (cost, quality, hybrid, local_first)
        prefer_local: Prefer local models
        daily_budget: Daily cost budget

    Returns:
        Configured EnhancedModelRouter
    """
    config = RouterConfig(
        strategy=RoutingStrategy(strategy),
        prefer_local=prefer_local,
        daily_budget=daily_budget
    )
    return EnhancedModelRouter(config)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    'RoutingStrategy',
    'TaskType',
    'Complexity',

    # Config
    'RouterConfig',
    'CostTracker',

    # Main classes
    'FallbackChain',
    'EnhancedModelRouter',

    # Convenience
    'create_router',
]
