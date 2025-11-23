"""
YAML-based LLM Configuration System for JARVIS AI Agent

Provides configuration loading, role-based model assignment,
cost optimization routing, and integration with EnhancedModelRouter.
"""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

try:
    from .providers import (
        LLMProvider,
        OpenAIProvider,
        AnthropicProvider,
        OllamaProvider,
        DeepSeekProvider,
        QwenProvider,
        ModelInfo,
    )
    from .enhanced_router import (
        EnhancedModelRouter,
        RouterConfig,
        RoutingStrategy,
        FallbackChain,
        CostTracker,
    )
except ImportError:
    from providers import (
        LLMProvider,
        OpenAIProvider,
        AnthropicProvider,
        OllamaProvider,
        DeepSeekProvider,
        QwenProvider,
        ModelInfo,
    )
    from enhanced_router import (
        EnhancedModelRouter,
        RouterConfig,
        RoutingStrategy,
        FallbackChain,
        CostTracker,
    )


class AgentRole(Enum):
    """Standard agent roles in the Jarvis system"""
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    EMPLOYEE = "employee"
    REVIEWER = "reviewer"
    PLANNER = "planner"
    EXECUTOR = "executor"


class TaskCategory(Enum):
    """Categories for task-based routing"""
    CODING = "coding"
    GENERAL = "general"
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    REVIEW = "review"
    PLANNING = "planning"
    SIMPLE = "simple"
    COMPLEX = "complex"


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider"""
    name: str
    api_key: Optional[str] = None
    host: Optional[str] = None
    models: List[str] = field(default_factory=list)
    enabled: bool = True
    max_retries: int = 3
    timeout: float = 30.0
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelAssignment:
    """Assignment of primary and fallback models"""
    primary: str
    fallback: Optional[str] = None
    fallback_chain: List[str] = field(default_factory=list)


@dataclass
class RoleConfig:
    """Configuration for a specific agent role"""
    role: str
    assignments: Dict[str, ModelAssignment] = field(default_factory=dict)
    default_assignment: Optional[ModelAssignment] = None


@dataclass
class CostOptimizationConfig:
    """Cost optimization rules"""
    prefer_local_for: List[str] = field(default_factory=list)
    use_premium_for: List[str] = field(default_factory=list)
    daily_budget: Optional[float] = None
    monthly_budget: Optional[float] = None
    alert_threshold: float = 0.8  # Alert when 80% of budget used


@dataclass
class LLMConfig:
    """Complete LLM configuration"""
    routing_strategy: str = "hybrid"
    providers: Dict[str, ProviderConfig] = field(default_factory=dict)
    role_assignments: Dict[str, RoleConfig] = field(default_factory=dict)
    cost_optimization: Optional[CostOptimizationConfig] = None
    default_model: str = "gpt-4o-mini"
    default_provider: str = "openai"
    environment: str = "development"


class LLMConfigLoader:
    """
    Loads and validates LLM configuration from YAML files.

    Supports:
    - Environment variable expansion (${VAR_NAME})
    - Multiple config file formats
    - Validation of provider and model settings
    - Default value handling
    """

    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self):
        if not HAS_YAML:
            raise ImportError("PyYAML is required. Install with: pip install pyyaml")

    def load(self, config_path: Union[str, Path]) -> LLMConfig:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            LLMConfig object with all settings
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)

        # Expand environment variables
        expanded_config = self._expand_env_vars(raw_config)

        # Parse and validate
        return self._parse_config(expanded_config)

    def load_from_string(self, yaml_string: str) -> LLMConfig:
        """Load configuration from a YAML string"""
        raw_config = yaml.safe_load(yaml_string)
        expanded_config = self._expand_env_vars(raw_config)
        return self._parse_config(expanded_config)

    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in config"""
        if isinstance(obj, str):
            def replace_var(match):
                var_name = match.group(1)
                return os.environ.get(var_name, f"${{{var_name}}}")
            return self.ENV_VAR_PATTERN.sub(replace_var, obj)
        elif isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        return obj

    def _parse_config(self, config: Dict[str, Any]) -> LLMConfig:
        """Parse raw config dict into LLMConfig object"""
        # Parse providers
        providers = {}
        for name, pconfig in config.get('providers', {}).items():
            providers[name] = ProviderConfig(
                name=name,
                api_key=pconfig.get('api_key'),
                host=pconfig.get('host'),
                models=pconfig.get('models', []),
                enabled=pconfig.get('enabled', True),
                max_retries=pconfig.get('max_retries', 3),
                timeout=pconfig.get('timeout', 30.0),
                extra=pconfig.get('extra', {})
            )

        # Parse role assignments
        role_assignments = {}
        for role_name, rconfig in config.get('role_assignments', {}).items():
            assignments = {}

            if isinstance(rconfig, dict):
                for task_or_key, assignment in rconfig.items():
                    if task_or_key in ('primary', 'fallback'):
                        # Direct role assignment without task category
                        assignments['default'] = ModelAssignment(
                            primary=rconfig.get('primary', ''),
                            fallback=rconfig.get('fallback'),
                            fallback_chain=rconfig.get('fallback_chain', [])
                        )
                        break
                    elif isinstance(assignment, dict):
                        # Task-specific assignment
                        assignments[task_or_key] = ModelAssignment(
                            primary=assignment.get('primary', ''),
                            fallback=assignment.get('fallback'),
                            fallback_chain=assignment.get('fallback_chain', [])
                        )

            role_assignments[role_name] = RoleConfig(
                role=role_name,
                assignments=assignments,
                default_assignment=assignments.get('default')
            )

        # Parse cost optimization
        cost_opt = None
        if 'cost_optimization' in config:
            co = config['cost_optimization']
            cost_opt = CostOptimizationConfig(
                prefer_local_for=co.get('prefer_local_for', []),
                use_premium_for=co.get('use_premium_for', []),
                daily_budget=co.get('daily_budget'),
                monthly_budget=co.get('monthly_budget'),
                alert_threshold=co.get('alert_threshold', 0.8)
            )

        return LLMConfig(
            routing_strategy=config.get('routing_strategy', 'hybrid'),
            providers=providers,
            role_assignments=role_assignments,
            cost_optimization=cost_opt,
            default_model=config.get('default_model', 'gpt-4o-mini'),
            default_provider=config.get('default_provider', 'openai'),
            environment=config.get('environment', 'development')
        )

    def validate(self, config: LLMConfig) -> List[str]:
        """
        Validate configuration and return list of issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check providers have required fields
        for name, provider in config.providers.items():
            if name in ('openai', 'anthropic', 'deepseek', 'qwen'):
                if not provider.api_key or provider.api_key.startswith('${'):
                    issues.append(
                        f"Provider '{name}' missing API key (check environment variable)"
                    )
            elif name == 'ollama':
                if not provider.host:
                    issues.append(
                        f"Provider 'ollama' missing host URL"
                    )

            if not provider.models:
                issues.append(f"Provider '{name}' has no models configured")

        # Check role assignments reference valid providers/models
        all_models = set()
        for provider in config.providers.values():
            all_models.update(provider.models)

        for role_name, role_config in config.role_assignments.items():
            for task, assignment in role_config.assignments.items():
                # Note: We don't strictly validate model names since
                # they might be provider-specific (e.g., "claude-3-5-sonnet")
                pass

        return issues


class ConfigurableRouter:
    """
    LLM Router configured from YAML config file.

    Integrates LLMConfig with EnhancedModelRouter to provide:
    - Role-based model selection
    - Task-category routing
    - Cost optimization
    - Automatic fallback handling
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.router: Optional[EnhancedModelRouter] = None
        self.cost_tracker = CostTracker()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize providers and router from config"""
        # Create provider instances
        for name, pconfig in self.config.providers.items():
            if not pconfig.enabled:
                continue

            provider = self._create_provider(name, pconfig)
            if provider:
                self.providers[name] = provider

        # Create router with configured strategy
        strategy = RoutingStrategy(self.config.routing_strategy)
        router_config = RouterConfig(
            default_strategy=strategy,
            enable_fallback=True,
            max_retries=3,
            enable_cost_tracking=True
        )

        self.router = EnhancedModelRouter(config=router_config)

        # Register all providers with router
        for name, provider in self.providers.items():
            self.router.register_provider(name, provider)

        self._initialized = True

    def _create_provider(
        self,
        name: str,
        config: ProviderConfig
    ) -> Optional[LLMProvider]:
        """Create a provider instance from config"""
        try:
            if name == 'openai':
                return OpenAIProvider(
                    api_key=config.api_key or os.environ.get('OPENAI_API_KEY', ''),
                    default_model=config.models[0] if config.models else 'gpt-4o-mini'
                )
            elif name == 'anthropic':
                return AnthropicProvider(
                    api_key=config.api_key or os.environ.get('ANTHROPIC_API_KEY', ''),
                    default_model=config.models[0] if config.models else 'claude-3-5-sonnet-20241022'
                )
            elif name == 'deepseek':
                return DeepSeekProvider(
                    api_key=config.api_key or os.environ.get('DEEPSEEK_API_KEY', ''),
                    default_model=config.models[0] if config.models else 'deepseek-chat'
                )
            elif name == 'qwen':
                return QwenProvider(
                    api_key=config.api_key or os.environ.get('QWEN_API_KEY', ''),
                    default_model=config.models[0] if config.models else 'qwen-turbo'
                )
            elif name == 'ollama':
                return OllamaProvider(
                    host=config.host or 'http://localhost:11434',
                    default_model=config.models[0] if config.models else 'llama3.1:70b'
                )
            else:
                # Unknown provider - could extend with custom providers
                return None
        except Exception as e:
            print(f"Warning: Could not create provider '{name}': {e}")
            return None

    def get_model_for_role(
        self,
        role: str,
        task_category: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Get the appropriate model for a role and task.

        Args:
            role: Agent role (manager, supervisor, employee, etc.)
            task_category: Optional task category (coding, general, etc.)

        Returns:
            Tuple of (provider_name, model_name)
        """
        role_config = self.config.role_assignments.get(role)

        if not role_config:
            return self.config.default_provider, self.config.default_model

        # Look for task-specific assignment
        assignment = None
        if task_category and task_category in role_config.assignments:
            assignment = role_config.assignments[task_category]
        elif role_config.default_assignment:
            assignment = role_config.default_assignment
        elif 'default' in role_config.assignments:
            assignment = role_config.assignments['default']

        if not assignment:
            return self.config.default_provider, self.config.default_model

        # Parse model string (format: "model-name" or "provider:model-name")
        model_str = assignment.primary
        return self._parse_model_string(model_str)

    def _parse_model_string(self, model_str: str) -> Tuple[str, str]:
        """Parse a model string into provider and model name"""
        # Map common model prefixes to providers
        model_provider_map = {
            'gpt-': 'openai',
            'claude-': 'anthropic',
            'deepseek-': 'deepseek',
            'qwen-': 'qwen',
            'llama': 'ollama',
        }

        for prefix, provider in model_provider_map.items():
            if model_str.startswith(prefix) or model_str.startswith(prefix.rstrip('-')):
                return provider, model_str

        # Default to configured default provider
        return self.config.default_provider, model_str

    def should_use_local(self, task_type: str) -> bool:
        """Check if task should prefer local models"""
        if not self.config.cost_optimization:
            return False
        return task_type in self.config.cost_optimization.prefer_local_for

    def should_use_premium(self, task_type: str) -> bool:
        """Check if task requires premium models"""
        if not self.config.cost_optimization:
            return False
        return task_type in self.config.cost_optimization.use_premium_for

    async def chat(
        self,
        messages: List[Dict[str, str]],
        role: str = "employee",
        task_category: str = "general",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat request with role-based routing.

        Args:
            messages: Chat messages
            role: Agent role for model selection
            task_category: Task category for specialized routing
            **kwargs: Additional arguments for the provider

        Returns:
            Chat response from the selected model
        """
        if not self._initialized:
            self.initialize()

        # Determine model based on role and task
        provider_name, model_name = self.get_model_for_role(role, task_category)

        # Apply cost optimization overrides
        if self.should_use_local(task_category):
            if 'ollama' in self.providers:
                provider_name = 'ollama'
        elif self.should_use_premium(task_category):
            # Prefer premium models for critical tasks
            if 'openai' in self.providers:
                provider_name = 'openai'
                model_name = 'gpt-4o'
            elif 'anthropic' in self.providers:
                provider_name = 'anthropic'
                model_name = 'claude-3-5-sonnet-20241022'

        # Get provider
        provider = self.providers.get(provider_name)
        if not provider:
            # Fallback to first available provider
            provider_name = next(iter(self.providers.keys()))
            provider = self.providers[provider_name]

        # Make the request
        response = await provider.chat(messages, model=model_name, **kwargs)

        # Track cost
        self.cost_tracker.track(
            provider_name,
            model_name,
            response.input_tokens,
            response.output_tokens
        )

        return {
            "content": response.content,
            "model": response.model,
            "provider": provider_name,
            "tokens": {
                "input": response.input_tokens,
                "output": response.output_tokens,
                "total": response.total_tokens
            },
            "cost": self.cost_tracker.get_provider_cost(provider_name)
        }

    def get_fallback_chain(
        self,
        role: str,
        task_category: Optional[str] = None
    ) -> FallbackChain:
        """
        Create a fallback chain for a role/task.

        Returns:
            FallbackChain with configured fallback order
        """
        role_config = self.config.role_assignments.get(role)
        providers_list = []

        if role_config:
            assignment = None
            if task_category and task_category in role_config.assignments:
                assignment = role_config.assignments[task_category]
            elif role_config.default_assignment:
                assignment = role_config.default_assignment

            if assignment:
                # Add primary
                primary_provider, _ = self._parse_model_string(assignment.primary)
                if primary_provider in self.providers:
                    providers_list.append(self.providers[primary_provider])

                # Add fallback
                if assignment.fallback:
                    fallback_provider, _ = self._parse_model_string(assignment.fallback)
                    if fallback_provider in self.providers:
                        providers_list.append(self.providers[fallback_provider])

                # Add chain
                for model in assignment.fallback_chain:
                    chain_provider, _ = self._parse_model_string(model)
                    if chain_provider in self.providers:
                        providers_list.append(self.providers[chain_provider])

        # Add remaining providers as final fallbacks
        for name, provider in self.providers.items():
            if provider not in providers_list:
                providers_list.append(provider)

        return FallbackChain(providers_list)

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        summary = self.cost_tracker.get_summary()

        # Add budget info if configured
        if self.config.cost_optimization:
            co = self.config.cost_optimization
            summary['budget'] = {
                'daily': co.daily_budget,
                'monthly': co.monthly_budget,
                'alert_threshold': co.alert_threshold
            }

            # Check budget alerts
            total_cost = summary.get('total_cost', 0)
            if co.daily_budget and total_cost >= co.daily_budget * co.alert_threshold:
                summary['alerts'] = summary.get('alerts', [])
                summary['alerts'].append(
                    f"Daily budget {co.alert_threshold*100:.0f}% threshold reached"
                )

        return summary


def load_config(config_path: Union[str, Path]) -> LLMConfig:
    """Convenience function to load config from file"""
    loader = LLMConfigLoader()
    return loader.load(config_path)


def create_router_from_config(config_path: Union[str, Path]) -> ConfigurableRouter:
    """Create a fully configured router from a config file"""
    config = load_config(config_path)
    router = ConfigurableRouter(config)
    router.initialize()
    return router


def create_router_from_yaml(yaml_string: str) -> ConfigurableRouter:
    """Create a router from a YAML string"""
    loader = LLMConfigLoader()
    config = loader.load_from_string(yaml_string)
    router = ConfigurableRouter(config)
    router.initialize()
    return router


# Default configuration template
DEFAULT_CONFIG_TEMPLATE = """
# JARVIS LLM Configuration
routing_strategy: hybrid

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    models:
      - gpt-4o
      - gpt-4o-mini
    enabled: true

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    models:
      - claude-3-5-sonnet-20241022
    enabled: true

  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    models:
      - deepseek-chat
    enabled: true

  ollama:
    host: http://localhost:11434
    models:
      - llama3.1:70b
      - qwen2.5:72b
    enabled: false  # Enable if running locally

role_assignments:
  manager:
    primary: gpt-4o
    fallback: claude-3-5-sonnet-20241022

  supervisor:
    primary: gpt-4o-mini
    fallback: deepseek-chat

  employee:
    coding:
      primary: claude-3-5-sonnet-20241022
      fallback: deepseek-chat
    general:
      primary: gpt-4o-mini
      fallback: llama3.1:70b
    review:
      primary: claude-3-5-sonnet-20241022
      fallback: gpt-4o

  planner:
    primary: gpt-4o
    fallback: claude-3-5-sonnet-20241022

cost_optimization:
  prefer_local_for:
    - simple_queries
    - code_formatting
    - test_generation
    - documentation

  use_premium_for:
    - architecture_decisions
    - security_reviews
    - final_code_review
    - complex_reasoning

  daily_budget: 50.0
  monthly_budget: 1000.0
  alert_threshold: 0.8

default_model: gpt-4o-mini
default_provider: openai
environment: development
"""


def generate_default_config(output_path: Union[str, Path]) -> None:
    """Generate a default configuration file"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(DEFAULT_CONFIG_TEMPLATE.strip())

    print(f"Generated default config at: {output_path}")
