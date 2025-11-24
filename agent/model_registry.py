# model_registry.py
"""
PHASE 1.7: Externalized Model Configuration Registry

Loads model configuration from external JSON file (agent/models.json)
to enable model updates without code changes.

Addresses vulnerability A3: Hard-coded model names requiring code changes
when providers deprecate models.

Usage:
    >>> from model_registry import get_registry
    >>> registry = get_registry()
    >>> model = registry.get_model("manager_default")
    >>> print(model.full_id)  # "gpt-4o-mini-2024-11-20"
    >>> print(model.cost_per_1k_prompt)  # 0.003
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ══════════════════════════════════════════════════════════════════════
# Data Classes
# ══════════════════════════════════════════════════════════════════════


@dataclass
class ModelInfo:
    """
    Information about a specific model.

    Attributes:
        provider: Provider name (e.g., "openai", "anthropic")
        model_id: Short model identifier (e.g., "gpt-4o", "claude-3-5-sonnet-20241022")
        full_id: Complete model ID for API calls (e.g., "gpt-4o-2024-11-20")
        display_name: Human-readable name
        context_window: Maximum context window size in tokens
        max_output_tokens: Maximum output tokens
        cost_per_1k_prompt: Cost per 1000 prompt tokens in USD
        cost_per_1k_completion: Cost per 1000 completion tokens in USD
        capabilities: List of capabilities (e.g., ["chat", "json", "vision"])
        deprecated: Whether model is deprecated
        deprecation_date: Date when model will be deprecated (ISO format)
        replacement: Recommended replacement model ID
        notes: Additional notes about the model
    """

    provider: str
    model_id: str
    full_id: str
    display_name: str
    context_window: int
    max_output_tokens: int
    cost_per_1k_prompt: float
    cost_per_1k_completion: float
    capabilities: List[str]
    deprecated: bool = False
    deprecation_date: Optional[str] = None
    replacement: Optional[str] = None
    notes: str = ""

    def __repr__(self) -> str:
        deprecation_status = " [DEPRECATED]" if self.deprecated else ""
        return (
            f"ModelInfo({self.provider}/{self.model_id} -> {self.full_id}"
            f"{deprecation_status})"
        )

    def get_cost_for_tokens(
        self, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """
        Calculate cost for given token counts.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Total cost in USD
        """
        prompt_cost = (prompt_tokens / 1000) * self.cost_per_1k_prompt
        completion_cost = (completion_tokens / 1000) * self.cost_per_1k_completion
        return prompt_cost + completion_cost

    def is_deprecation_imminent(self, warning_days: int = 90) -> bool:
        """
        Check if deprecation is within warning period.

        Args:
            warning_days: Days before deprecation to start warning

        Returns:
            True if deprecation is imminent
        """
        if not self.deprecated or not self.deprecation_date:
            return False

        try:
            dep_date = datetime.fromisoformat(self.deprecation_date)
            warning_date = dep_date - timedelta(days=warning_days)
            return datetime.now() >= warning_date
        except (ValueError, TypeError):
            return False


# ══════════════════════════════════════════════════════════════════════
# Model Registry
# ══════════════════════════════════════════════════════════════════════


class ModelRegistry:
    """
    Registry for managing model configurations.

    Loads model information from external JSON file (agent/models.json)
    and provides query interface for model resolution.

    Example:
        >>> registry = ModelRegistry()
        >>> model = registry.get_model("manager_default")
        >>> print(model.full_id)
        "gpt-4o-mini-2024-11-20"
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize model registry.

        Args:
            registry_path: Path to models.json. If None, uses default location.
        """
        if registry_path is None:
            registry_path = Path(__file__).parent / "models.json"

        self.registry_path = registry_path
        self.registry_data: Dict = {}
        self._model_cache: Dict[str, ModelInfo] = {}

        # Load registry
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from JSON file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(
                f"Model registry not found at {self.registry_path}. "
                f"Please create agent/models.json with model configuration."
            )

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                self.registry_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in model registry: {e}")

        # Validate basic structure
        if "providers" not in self.registry_data:
            raise ValueError("Model registry missing 'providers' section")
        if "aliases" not in self.registry_data:
            raise ValueError("Model registry missing 'aliases' section")

    def get_model(self, model_ref: str) -> ModelInfo:
        """
        Get model by reference (alias or provider/model format).

        Args:
            model_ref: Model reference in one of these formats:
                       - Alias: "manager_default", "high_complexity"
                       - Provider/model: "openai/gpt-4o", "anthropic/claude-3-5-sonnet-20241022"
                       - Model only: "gpt-4o" (defaults to openai)

        Returns:
            ModelInfo instance with model details

        Raises:
            ValueError: If model reference cannot be resolved

        Examples:
            >>> registry.get_model("manager_default")  # Alias
            >>> registry.get_model("openai/gpt-4o")     # Provider/model
            >>> registry.get_model("gpt-4o")            # Model (defaults to openai)
        """
        # Check cache first
        if model_ref in self._model_cache:
            return self._model_cache[model_ref]

        # Resolve alias
        original_ref = model_ref
        if model_ref in self.registry_data.get("aliases", {}):
            model_ref = self.registry_data["aliases"][model_ref]

        # Parse provider/model
        if "/" in model_ref:
            provider, model_id = model_ref.split("/", 1)
        else:
            # Default to openai if no provider specified
            provider, model_id = "openai", model_ref

        # Look up model
        try:
            providers = self.registry_data["providers"]
            if provider not in providers:
                raise ValueError(f"Unknown provider: {provider}")

            models = providers[provider]["models"]
            if model_id not in models:
                raise ValueError(
                    f"Unknown model: {model_id} for provider {provider}"
                )

            model_data = models[model_id]

            # Create ModelInfo
            model_info = ModelInfo(
                provider=provider,
                model_id=model_id,
                full_id=model_data["id"],
                display_name=model_data.get("display_name", model_id),
                context_window=model_data["context_window"],
                max_output_tokens=model_data["max_output_tokens"],
                cost_per_1k_prompt=model_data["cost_per_1k_prompt"],
                cost_per_1k_completion=model_data["cost_per_1k_completion"],
                capabilities=model_data.get("capabilities", []),
                deprecated=model_data.get("deprecated", False),
                deprecation_date=model_data.get("deprecation_date"),
                replacement=model_data.get("replacement"),
                notes=model_data.get("notes", ""),
            )

            # Cache and return
            self._model_cache[original_ref] = model_info
            return model_info

        except (KeyError, TypeError) as e:
            raise ValueError(
                f"Failed to resolve model reference '{original_ref}': {e}"
            )

    def get_role_model(
        self,
        role: str,
        context: str = "default",
        complexity: Optional[str] = None,
    ) -> ModelInfo:
        """
        Get model for a specific role and context.

        Args:
            role: Agent role ("manager", "supervisor", "employee", "specialist")
            context: Context/phase ("default", "planning", "review", etc.)
            complexity: Optional complexity level ("high", "medium", "low")

        Returns:
            ModelInfo instance

        Example:
            >>> registry.get_role_model("manager", "planning")
            >>> registry.get_role_model("employee", "default", complexity="high")
        """
        role_defaults = self.registry_data.get("role_defaults", {})

        # Check complexity override
        if complexity == "high" and role in role_defaults:
            if "high_complexity" in role_defaults[role]:
                alias = role_defaults[role]["high_complexity"]
                return self.get_model(alias)

        # Check context-specific setting
        if role in role_defaults and context in role_defaults[role]:
            alias = role_defaults[role][context]
            return self.get_model(alias)

        # Fall back to default for role
        if role in role_defaults and "default" in role_defaults[role]:
            alias = role_defaults[role]["default"]
            return self.get_model(alias)

        # Ultimate fallback
        return self.get_model("manager_default")

    def list_models(
        self, provider: Optional[str] = None, include_deprecated: bool = True
    ) -> List[ModelInfo]:
        """
        List all models in registry.

        Args:
            provider: Optional provider filter ("openai", "anthropic", etc.)
            include_deprecated: Whether to include deprecated models

        Returns:
            List of ModelInfo instances
        """
        models = []

        providers = self.registry_data.get("providers", {})
        for prov_name, prov_data in providers.items():
            # Skip if filtering by provider
            if provider and prov_name != provider:
                continue

            # Iterate through models
            for model_id in prov_data.get("models", {}):
                try:
                    model = self.get_model(f"{prov_name}/{model_id}")

                    # Skip deprecated if requested
                    if not include_deprecated and model.deprecated:
                        continue

                    models.append(model)
                except ValueError:
                    # Skip invalid models
                    continue

        return models

    def check_deprecations(self, warning_days: int = 90) -> List[Tuple[str, ModelInfo]]:
        """
        Check for deprecated models or models approaching deprecation.

        Args:
            warning_days: Days before deprecation to start warning

        Returns:
            List of (alias/reference, ModelInfo) tuples for deprecated models
        """
        deprecations = []

        # Check all aliases
        for alias, model_ref in self.registry_data.get("aliases", {}).items():
            try:
                model = self.get_model(alias)
                if model.deprecated or model.is_deprecation_imminent(warning_days):
                    deprecations.append((alias, model))
            except ValueError:
                # Skip invalid references
                continue

        return deprecations

    def warn_if_deprecated(self) -> None:
        """
        Print warnings for deprecated models in registry.

        Should be called at application startup.
        """
        deprecations = self.check_deprecations()

        if not deprecations:
            return

        warnings.warn(
            f"⚠️  Model Registry: {len(deprecations)} model(s) are deprecated or approaching deprecation",
            UserWarning,
        )

        for alias, model in deprecations:
            if model.deprecated:
                msg = f"  - {alias} -> {model.provider}/{model.model_id} is DEPRECATED"
                if model.replacement:
                    msg += f" (use {model.replacement} instead)"
                if model.deprecation_date:
                    msg += f" [Removal: {model.deprecation_date}]"
                print(msg)
            elif model.is_deprecation_imminent():
                msg = f"  - {alias} -> {model.provider}/{model.model_id} will be deprecated on {model.deprecation_date}"
                if model.replacement:
                    msg += f" (migrate to {model.replacement})"
                print(msg)

    def get_cost_threshold(self, level: str) -> float:
        """
        Get cost threshold for given level.

        Args:
            level: "low", "medium", or "high"

        Returns:
            Cost threshold in USD per 1K tokens
        """
        thresholds = self.registry_data.get("cost_thresholds", {})
        return thresholds.get(level, 0.01)

    def reload(self) -> None:
        """
        Reload registry from disk.

        Useful for hot-reloading configuration without restart.
        """
        self._model_cache.clear()
        self._load_registry()


# ══════════════════════════════════════════════════════════════════════
# Global Registry Instance
# ══════════════════════════════════════════════════════════════════════

_global_registry: Optional[ModelRegistry] = None


def get_registry(registry_path: Optional[Path] = None) -> ModelRegistry:
    """
    Get global model registry instance (singleton).

    Args:
        registry_path: Optional custom path to models.json

    Returns:
        ModelRegistry instance

    Example:
        >>> from model_registry import get_registry
        >>> registry = get_registry()
        >>> model = registry.get_model("manager_default")
    """
    global _global_registry

    if _global_registry is None or registry_path is not None:
        _global_registry = ModelRegistry(registry_path)

    return _global_registry


def reload_registry() -> None:
    """
    Reload global registry from disk.

    Useful for hot-reloading configuration.
    """
    registry = get_registry()
    registry.reload()


# ══════════════════════════════════════════════════════════════════════
# Startup Check
# ══════════════════════════════════════════════════════════════════════


def check_deprecations_on_startup() -> None:
    """
    Check for deprecated models on application startup.

    Should be called once at startup to warn about deprecated models.
    """
    try:
        registry = get_registry()
        registry.warn_if_deprecated()
    except Exception as e:
        warnings.warn(f"Failed to check model deprecations: {e}", UserWarning)
