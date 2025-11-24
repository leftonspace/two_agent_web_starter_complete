# test_model_router.py
"""
Unit tests for model_router module (Stage 5).
"""

from __future__ import annotations

import pytest

# Import the module we're testing
import model_router


def test_choose_model_gpt5_constraint_first_iteration():
    """Test that GPT-5 is NOT allowed on first iteration."""
    model = model_router.choose_model(
        task_type="planning",
        complexity="high",
        role="manager",
        interaction_index=1,
        is_very_important=True,
    )

    # Should NOT be GPT-4o on first iteration
    assert "gpt-4o-mini" in model
    assert "gpt-4o-2024" not in model


def test_choose_model_gpt5_allowed_second_iteration_high_complexity():
    """Test that GPT-5 IS allowed on 2nd iteration with high complexity."""
    model = model_router.choose_model(
        task_type="planning",
        complexity="high",
        role="manager",
        interaction_index=2,
        is_very_important=False,
    )

    # Should be GPT-4o on 2nd iteration with high complexity
    assert "gpt-4o-2024" in model


def test_choose_model_gpt5_allowed_third_iteration_important():
    """Test that GPT-5 IS allowed on 3rd iteration when important."""
    model = model_router.choose_model(
        task_type="code",
        complexity="low",
        role="employee",
        interaction_index=3,
        is_very_important=True,
    )

    # Should be GPT-4o on 3rd iteration when very important
    assert "gpt-4o-2024" in model


def test_choose_model_gpt5_not_allowed_second_iteration_low_complexity():
    """Test that GPT-5 is NOT allowed on 2nd iteration with low complexity and not important."""
    model = model_router.choose_model(
        task_type="planning",
        complexity="low",
        role="manager",
        interaction_index=2,
        is_very_important=False,
    )

    # Should NOT be GPT-4o with low complexity and not important
    assert "gpt-4o-mini" in model


def test_choose_model_gpt5_not_allowed_fourth_iteration():
    """Test that GPT-5 is NOT allowed beyond 3rd iteration."""
    model = model_router.choose_model(
        task_type="planning",
        complexity="high",
        role="manager",
        interaction_index=4,
        is_very_important=True,
    )

    # Should NOT be GPT-4o beyond 3rd iteration
    assert "gpt-4o-mini" in model


def test_choose_model_docs_task_type():
    """Test that docs task type uses cheaper models."""
    model = model_router.choose_model(
        task_type="docs",
        complexity="high",
        role="manager",
        interaction_index=2,
    )

    # Docs should always use mini, even with high complexity
    assert "gpt-4o-mini" in model


def test_choose_model_analysis_task_type():
    """Test that analysis task type uses appropriate models."""
    model_low = model_router.choose_model(
        task_type="analysis",
        complexity="low",
        role="qa",
        interaction_index=1,
    )

    model_high = model_router.choose_model(
        task_type="analysis",
        complexity="high",
        role="qa",
        interaction_index=1,
    )

    # Analysis with low complexity should use mini
    assert "gpt-4o-mini" in model_low

    # Analysis with high complexity should use mini
    assert "gpt-4o-mini" in model_high


def test_estimate_complexity_previous_failures():
    """Test that previous failures increase complexity."""
    complexity = model_router.estimate_complexity(
        previous_failures=2,
    )

    assert complexity == "high"


def test_estimate_complexity_many_files():
    """Test that many files increase complexity."""
    complexity = model_router.estimate_complexity(
        files_count=10,
    )

    assert complexity == "high"


def test_estimate_complexity_keywords():
    """Test that certain keywords increase complexity."""
    stage = {
        "name": "Refactor authentication system",
        "description": "Major architecture changes",
    }

    complexity = model_router.estimate_complexity(stage=stage)

    assert complexity == "high"


def test_estimate_complexity_low():
    """Test that simple cases result in low complexity."""
    stage = {
        "name": "Update button color",
        "description": "Simple CSS change",
    }

    complexity = model_router.estimate_complexity(
        stage=stage,
        previous_failures=0,
        files_count=1,
    )

    assert complexity == "low"


def test_is_stage_important_in_list():
    """Test that stages in very_important list are marked as important."""
    stage = {
        "id": "stage-123",
        "name": "Critical Feature",
    }

    config = {
        "llm_very_important_stages": ["stage-123"],
    }

    result = model_router.is_stage_important(stage, config)

    assert result is True


def test_is_stage_important_by_name():
    """Test that stages can be marked important by name."""
    stage = {
        "id": "stage-456",
        "name": "Security Update",
    }

    config = {
        "llm_very_important_stages": ["Security Update"],
    }

    result = model_router.is_stage_important(stage, config)

    assert result is True


def test_is_stage_important_not_in_list():
    """Test that stages not in list are not important."""
    stage = {
        "id": "stage-789",
        "name": "Minor Fix",
    }

    config = {
        "llm_very_important_stages": ["stage-123"],
    }

    result = model_router.is_stage_important(stage, config)

    assert result is False
