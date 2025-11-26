"""
PHASE 7.3: Model Provider Configuration

Loads and validates model provider configuration from YAML.

Usage:
    from core.models.config import ModelsConfig, load_config

    config = load_config()  # Loads from default path
    anthropic_config = config.get_provider_config("anthropic")
    model_info = config.get_model_info("anthropic", "sonnet")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from .provider import ModelInfo, ModelTier


# Configure logging
logger = logging.getLogger(__name__)


# Default config path relative to project root
DEFAULT_CONFIG_PATH = "config/models/providers.yaml"


# ============================================================================
# Configuration Models
# ============================================================================


class RateLimitsConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    tokens_per_minute: int = 100000


class ModelRequirements(BaseModel):
    """Hardware requirements for a model."""
    min_vram_gb: Optional[int] = None
    min_ram_gb: Optional[int] = None


class ModelConfig(BaseModel):
    """Configuration for a single model."""
    name: str
    tier: Literal["low", "medium", "high", "highest"]
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    max_context: int = 128000
    max_output_tokens: int = 4096
    supports_vision: bool = False
    supports_tools: bool = True
    description: str = ""
    requirements: Optional[ModelRequirements] = None

    @field_validator("cost_per_1k_input", "cost_per_1k_output")
    @classmethod
    def validate_cost(cls, v: float) -> float:
        """Ensure costs are non-negative."""
        if v < 0:
            raise ValueError("Cost cannot be negative")
        return v

    def to_model_info(self, alias: str, provider: str) -> ModelInfo:
        """Convert to ModelInfo object."""
        return ModelInfo(
            name=self.name,
            provider=provider,
            tier=ModelTier(self.tier),
            cost_per_1k_input=self.cost_per_1k_input,
            cost_per_1k_output=self.cost_per_1k_output,
            max_context=self.max_context,
            max_output_tokens=self.max_output_tokens,
            supports_vision=self.supports_vision,
            supports_tools=self.supports_tools,
            aliases=[alias],
        )


class ProviderConfig(BaseModel):
    """Configuration for a model provider."""
    enabled: bool = True
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    backend: Optional[str] = None  # For local providers (e.g., "ollama")
    default_max_tokens: int = 4096
    default_temperature: float = 0.7
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: int = 120
    rate_limits: RateLimitsConfig = Field(default_factory=RateLimitsConfig)
    models: Dict[str, ModelConfig] = Field(default_factory=dict)

    def get_api_key(self) -> Optional[str]:
        """Get API key from environment variable."""
        if self.api_key_env:
            return os.getenv(self.api_key_env)
        return None

    def is_available(self) -> bool:
        """Check if provider is available (enabled and has API key if needed)."""
        if not self.enabled:
            return False

        # For local providers, check if URL is accessible (simplified check)
        if self.backend:
            return True  # Assume local is available if enabled

        # For cloud providers, check API key
        if self.api_key_env:
            return bool(os.getenv(self.api_key_env))

        return True

    def get_model_config(self, alias: str) -> Optional[ModelConfig]:
        """Get model configuration by alias."""
        return self.models.get(alias)

    def list_models(self) -> List[str]:
        """List all model aliases."""
        return list(self.models.keys())


class DefaultsConfig(BaseModel):
    """Default settings configuration."""
    provider: str = "anthropic"
    default_models: Dict[str, str] = Field(default_factory=dict)
    task_routing: Dict[str, Dict[str, str]] = Field(default_factory=dict)


class CostControlsConfig(BaseModel):
    """Cost control settings."""
    max_cost_per_request: float = 1.0
    daily_budget: float = 50.0
    warning_threshold: float = 0.8
    hard_limit: float = 100.0


# ============================================================================
# Main Configuration Class
# ============================================================================


class ModelsConfig:
    """
    Main configuration manager for model providers.

    Loads configuration from YAML and provides access to provider
    and model settings.
    """

    def __init__(
        self,
        providers: Dict[str, ProviderConfig],
        defaults: DefaultsConfig,
        cost_controls: CostControlsConfig,
    ):
        """
        Initialize configuration.

        Args:
            providers: Provider configurations
            defaults: Default settings
            cost_controls: Cost control settings
        """
        self._providers = providers
        self._defaults = defaults
        self._cost_controls = cost_controls

        # Build model lookup cache
        self._model_lookup: Dict[str, tuple[str, str]] = {}
        self._build_model_lookup()

    def _build_model_lookup(self) -> None:
        """Build lookup table for model names to (provider, alias)."""
        for provider_name, provider_config in self._providers.items():
            for alias, model_config in provider_config.models.items():
                # Add alias lookup
                self._model_lookup[alias] = (provider_name, alias)
                # Add full name lookup
                self._model_lookup[model_config.name] = (provider_name, alias)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "ModelsConfig":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML config file (uses default if not specified)

        Returns:
            Loaded ModelsConfig instance

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        if path is None:
            # Try to find config relative to project root
            path = cls._find_config_path()

        logger.debug(f"Loading models config from: {path}")

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {path}, using defaults")
            return cls._create_default_config()
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

        return cls._parse_config(data)

    @classmethod
    def _find_config_path(cls) -> str:
        """Find config file path relative to project root."""
        # Try common locations
        candidates: List[str] = [
            DEFAULT_CONFIG_PATH,
            f"../{DEFAULT_CONFIG_PATH}",
            f"../../{DEFAULT_CONFIG_PATH}",
            str(Path(__file__).parent.parent.parent / DEFAULT_CONFIG_PATH),
        ]

        for candidate in candidates:
            path = Path(candidate)
            if path.exists():
                return str(path)

        # Return default path even if not found
        return DEFAULT_CONFIG_PATH

    @classmethod
    def _parse_config(cls, data: Dict[str, Any]) -> "ModelsConfig":
        """Parse configuration dictionary into ModelsConfig."""
        # Parse providers
        providers: Dict[str, ProviderConfig] = {}
        for name, provider_data in data.get("providers", {}).items():
            try:
                # Parse models
                models = {}
                for alias, model_data in provider_data.get("models", {}).items():
                    if isinstance(model_data.get("requirements"), dict):
                        model_data["requirements"] = ModelRequirements(
                            **model_data["requirements"]
                        )
                    models[alias] = ModelConfig(**model_data)

                # Create provider config
                provider_data["models"] = models
                if "rate_limits" in provider_data:
                    provider_data["rate_limits"] = RateLimitsConfig(
                        **provider_data["rate_limits"]
                    )
                providers[name] = ProviderConfig(**provider_data)

            except Exception as e:
                logger.error(f"Error parsing provider '{name}': {e}")
                raise ValueError(f"Invalid provider config for '{name}': {e}")

        # Parse defaults
        defaults_data = data.get("defaults", {})
        defaults = DefaultsConfig(**defaults_data)

        # Parse cost controls
        cost_data = data.get("cost_controls", {})
        cost_controls = CostControlsConfig(**cost_data)

        return cls(providers, defaults, cost_controls)

    @classmethod
    def _create_default_config(cls) -> "ModelsConfig":
        """Create default configuration when no config file exists."""
        # Minimal default with Anthropic
        anthropic_config = ProviderConfig(
            enabled=True,
            api_key_env="ANTHROPIC_API_KEY",
            models={
                "haiku": ModelConfig(
                    name="claude-haiku-4-5-20251001",
                    tier="low",
                    cost_per_1k_input=0.001,
                    cost_per_1k_output=0.005,
                    max_context=200000,
                ),
                "sonnet": ModelConfig(
                    name="claude-sonnet-4-5-20250929",
                    tier="medium",
                    cost_per_1k_input=0.003,
                    cost_per_1k_output=0.015,
                    max_context=200000,
                ),
                "opus": ModelConfig(
                    name="claude-opus-4-5-20251101",
                    tier="high",
                    cost_per_1k_input=0.015,
                    cost_per_1k_output=0.075,
                    max_context=200000,
                ),
            }
        )

        return cls(
            providers={"anthropic": anthropic_config},
            defaults=DefaultsConfig(provider="anthropic"),
            cost_controls=CostControlsConfig(),
        )

    # -------------------------------------------------------------------------
    # Provider Access
    # -------------------------------------------------------------------------

    def get_provider_config(self, name: str) -> Optional[ProviderConfig]:
        """
        Get configuration for a provider.

        Args:
            name: Provider name (e.g., "anthropic", "openai")

        Returns:
            ProviderConfig if found, None otherwise
        """
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        """Get list of all provider names."""
        return list(self._providers.keys())

    def list_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names."""
        return [
            name for name, config in self._providers.items()
            if config.enabled
        ]

    def list_available_providers(self) -> List[str]:
        """Get list of available (enabled + has credentials) provider names."""
        return [
            name for name, config in self._providers.items()
            if config.is_available()
        ]

    # -------------------------------------------------------------------------
    # Model Access
    # -------------------------------------------------------------------------

    def get_model_config(
        self,
        provider: str,
        alias: str
    ) -> Optional[ModelConfig]:
        """
        Get model configuration.

        Args:
            provider: Provider name
            alias: Model alias

        Returns:
            ModelConfig if found
        """
        provider_config = self._providers.get(provider)
        if provider_config:
            return provider_config.get_model_config(alias)
        return None

    def get_model_info(
        self,
        provider: str,
        alias: str
    ) -> Optional[ModelInfo]:
        """
        Get ModelInfo object for a model.

        Args:
            provider: Provider name
            alias: Model alias

        Returns:
            ModelInfo if found
        """
        model_config = self.get_model_config(provider, alias)
        if model_config:
            return model_config.to_model_info(alias, provider)
        return None

    def find_model(self, model: str) -> Optional[tuple[str, str]]:
        """
        Find provider and alias for a model name.

        Args:
            model: Model name or alias

        Returns:
            Tuple of (provider_name, alias) if found
        """
        return self._model_lookup.get(model)

    def list_all_models(self) -> List[ModelInfo]:
        """
        Get list of all models from all enabled providers.

        Returns:
            List of ModelInfo objects
        """
        models = []
        for provider_name, provider_config in self._providers.items():
            if provider_config.enabled:
                for alias, model_config in provider_config.models.items():
                    models.append(model_config.to_model_info(alias, provider_name))
        return models

    def list_available_models(self) -> List[ModelInfo]:
        """
        Get list of models from available providers.

        Returns:
            List of ModelInfo objects
        """
        models = []
        for provider_name, provider_config in self._providers.items():
            if provider_config.is_available():
                for alias, model_config in provider_config.models.items():
                    models.append(model_config.to_model_info(alias, provider_name))
        return models

    # -------------------------------------------------------------------------
    # Defaults Access
    # -------------------------------------------------------------------------

    @property
    def default_provider(self) -> str:
        """Get default provider name."""
        return self._defaults.provider

    def get_default_model(self, provider: str) -> Optional[str]:
        """Get default model alias for a provider."""
        return self._defaults.default_models.get(provider)

    def get_task_routing(self, task_type: str) -> Dict[str, str]:
        """Get routing configuration for a task type."""
        return self._defaults.task_routing.get(task_type, {})

    # -------------------------------------------------------------------------
    # Cost Controls Access
    # -------------------------------------------------------------------------

    @property
    def cost_controls(self) -> CostControlsConfig:
        """Get cost control settings."""
        return self._cost_controls


# ============================================================================
# Convenience Functions
# ============================================================================


# Module-level cache for config
_config_cache: Optional[ModelsConfig] = None


def load_config(path: Optional[str] = None, force_reload: bool = False) -> ModelsConfig:
    """
    Load models configuration (cached).

    Args:
        path: Path to config file (optional)
        force_reload: Force reload from file

    Returns:
        ModelsConfig instance
    """
    global _config_cache

    if _config_cache is None or force_reload:
        _config_cache = ModelsConfig.load(path)

    return _config_cache


def get_provider_config(provider: str) -> Optional[ProviderConfig]:
    """Get configuration for a provider."""
    return load_config().get_provider_config(provider)


def get_model_info(provider: str, alias: str) -> Optional[ModelInfo]:
    """Get ModelInfo for a model."""
    return load_config().get_model_info(provider, alias)


def list_available_models() -> List[ModelInfo]:
    """Get list of all available models."""
    return load_config().list_available_models()
