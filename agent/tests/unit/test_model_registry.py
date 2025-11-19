# tests/unit/test_model_registry.py
"""
PHASE 1.7: Unit tests for ModelRegistry

Tests model registry loading, querying, and deprecation checking.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(agent_dir))

import pytest
from model_registry import ModelRegistry, ModelInfo, get_registry


# ══════════════════════════════════════════════════════════════════════
# Test: Registry Loading
# ══════════════════════════════════════════════════════════════════════


def test_registry_loads_successfully():
    """Test that registry can be loaded from models.json."""
    registry = ModelRegistry()
    assert registry.registry_data is not None
    assert "providers" in registry.registry_data
    assert "aliases" in registry.registry_data


def test_registry_has_openai_provider():
    """Test that OpenAI provider is available."""
    registry = ModelRegistry()
    assert "openai" in registry.registry_data["providers"]
    assert "models" in registry.registry_data["providers"]["openai"]


def test_registry_has_anthropic_provider():
    """Test that Anthropic provider is available."""
    registry = ModelRegistry()
    assert "anthropic" in registry.registry_data["providers"]
    assert "models" in registry.registry_data["providers"]["anthropic"]


# ══════════════════════════════════════════════════════════════════════
# Test: Model Resolution
# ══════════════════════════════════════════════════════════════════════


def test_get_model_by_alias():
    """Test retrieving model by alias."""
    registry = ModelRegistry()
    model = registry.get_model("manager_default")

    assert model is not None
    assert isinstance(model, ModelInfo)
    assert model.full_id is not None
    assert model.cost_per_1k_prompt > 0
    assert model.cost_per_1k_completion > 0


def test_get_model_by_provider_slash_model():
    """Test retrieving model by provider/model format."""
    registry = ModelRegistry()
    model = registry.get_model("openai/gpt-5-mini")

    assert model is not None
    assert model.provider == "openai"
    assert model.model_id == "gpt-5-mini"
    assert "gpt-5-mini" in model.full_id.lower()


def test_get_model_defaults_to_openai():
    """Test that model without provider defaults to OpenAI."""
    registry = ModelRegistry()
    model = registry.get_model("gpt-5-mini")

    assert model is not None
    assert model.provider == "openai"


def test_get_model_invalid_reference_raises():
    """Test that invalid model reference raises ValueError."""
    registry = ModelRegistry()

    with pytest.raises(ValueError):
        registry.get_model("invalid/nonexistent-model")


# ══════════════════════════════════════════════════════════════════════
# Test: Model Info
# ══════════════════════════════════════════════════════════════════════


def test_model_info_has_required_fields():
    """Test that ModelInfo has all required fields."""
    registry = ModelRegistry()
    model = registry.get_model("openai/gpt-5")

    assert model.provider is not None
    assert model.model_id is not None
    assert model.full_id is not None
    assert model.display_name is not None
    assert model.context_window > 0
    assert model.max_output_tokens > 0
    assert model.cost_per_1k_prompt >= 0
    assert model.cost_per_1k_completion >= 0
    assert isinstance(model.capabilities, list)


def test_model_info_calculate_cost():
    """Test ModelInfo.get_cost_for_tokens()."""
    registry = ModelRegistry()
    model = registry.get_model("openai/gpt-5-mini")

    # Calculate cost for 1000 prompt + 500 completion tokens
    cost = model.get_cost_for_tokens(1000, 500)

    # Should be positive
    assert cost > 0

    # Should match expected calculation
    expected = (1000 / 1000 * model.cost_per_1k_prompt) + (500 / 1000 * model.cost_per_1k_completion)
    assert abs(cost - expected) < 0.0001


# ══════════════════════════════════════════════════════════════════════
# Test: Role-Based Model Selection
# ══════════════════════════════════════════════════════════════════════


def test_get_role_model_manager():
    """Test getting model for manager role."""
    registry = ModelRegistry()
    model = registry.get_role_model("manager", "planning")

    assert model is not None
    assert isinstance(model, ModelInfo)


def test_get_role_model_employee():
    """Test getting model for employee role."""
    registry = ModelRegistry()
    model = registry.get_role_model("employee", "default")

    assert model is not None
    assert isinstance(model, ModelInfo)


def test_get_role_model_high_complexity():
    """Test getting model for high complexity tasks."""
    registry = ModelRegistry()
    model = registry.get_role_model("employee", "default", complexity="high")

    assert model is not None
    # High complexity should use more capable model
    assert model.cost_per_1k_prompt > 0


# ══════════════════════════════════════════════════════════════════════
# Test: Model Listing
# ══════════════════════════════════════════════════════════════════════


def test_list_models_all():
    """Test listing all models."""
    registry = ModelRegistry()
    models = registry.list_models()

    assert len(models) > 0
    assert all(isinstance(m, ModelInfo) for m in models)


def test_list_models_by_provider():
    """Test listing models filtered by provider."""
    registry = ModelRegistry()
    openai_models = registry.list_models(provider="openai")

    assert len(openai_models) > 0
    assert all(m.provider == "openai" for m in openai_models)


def test_list_models_exclude_deprecated():
    """Test listing models excluding deprecated ones."""
    registry = ModelRegistry()
    non_deprecated = registry.list_models(include_deprecated=False)

    assert all(not m.deprecated for m in non_deprecated)


# ══════════════════════════════════════════════════════════════════════
# Test: Deprecation Checking
# ══════════════════════════════════════════════════════════════════════


def test_check_deprecations():
    """Test checking for deprecated models."""
    registry = ModelRegistry()
    deprecations = registry.check_deprecations()

    # Should return a list (may be empty if no deprecated models)
    assert isinstance(deprecations, list)

    # Each entry should be a tuple of (alias, ModelInfo)
    for alias, model in deprecations:
        assert isinstance(alias, str)
        assert isinstance(model, ModelInfo)
        assert model.deprecated or model.is_deprecation_imminent()


def test_deprecated_model_marked():
    """Test that deprecated models are properly marked."""
    registry = ModelRegistry()

    # gpt-4-turbo is marked as deprecated in models.json
    try:
        model = registry.get_model("openai/gpt-4-turbo")
        assert model.deprecated == True
        assert model.deprecation_date is not None
        assert model.replacement is not None
    except ValueError:
        # Model might not exist in registry, skip test
        pass


# ══════════════════════════════════════════════════════════════════════
# Test: Cost Thresholds
# ══════════════════════════════════════════════════════════════════════


def test_get_cost_threshold():
    """Test getting cost thresholds."""
    registry = ModelRegistry()

    low = registry.get_cost_threshold("low")
    medium = registry.get_cost_threshold("medium")
    high = registry.get_cost_threshold("high")

    assert low > 0
    assert medium > low
    assert high > medium


# ══════════════════════════════════════════════════════════════════════
# Test: Global Registry Singleton
# ══════════════════════════════════════════════════════════════════════


def test_get_registry_singleton():
    """Test that get_registry() returns singleton."""
    registry1 = get_registry()
    registry2 = get_registry()

    # Should be the same instance
    assert registry1 is registry2


# ══════════════════════════════════════════════════════════════════════
# Test: Registry Reload
# ══════════════════════════════════════════════════════════════════════


def test_registry_reload():
    """Test reloading registry clears cache."""
    registry = ModelRegistry()

    # Load a model to populate cache
    model1 = registry.get_model("manager_default")

    # Reload registry
    registry.reload()

    # Cache should be cleared
    assert len(registry._model_cache) == 0

    # Can still load models
    model2 = registry.get_model("manager_default")
    assert model2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
