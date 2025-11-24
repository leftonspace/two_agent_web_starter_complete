# tests/test_backward_compat.py
"""
PHASE 1.5: Backward compatibility verification tests.

These tests verify that the refactored code maintains backward compatibility
with existing code that doesn't use dependency injection.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))


def test_orchestrator_context_imports():
    """Test that orchestrator_context can be imported."""
    from orchestrator_context import OrchestratorContext

    assert OrchestratorContext is not None


def test_orchestrator_context_create_default():
    """Test that OrchestratorContext.create_default() works."""
    from orchestrator_context import OrchestratorContext

    context = OrchestratorContext.create_default()
    assert context is not None
    assert context.llm is not None
    assert context.cost_tracker is not None
    assert context.logger is not None


def test_orchestrator_context_is_feature_available():
    """Test that is_feature_available() method works."""
    from orchestrator_context import OrchestratorContext

    context = OrchestratorContext.create_default()

    # Core features should be available
    assert context.is_feature_available("llm")
    assert context.is_feature_available("cost_tracker")
    assert context.is_feature_available("logger")
    assert context.is_feature_available("prompts")
    assert context.is_feature_available("site_tools")
    assert context.is_feature_available("git_utils")


def test_mock_context_creation():
    """Test that mock context can be created."""
    from tests.mocks import create_mock_context

    context = create_mock_context()
    assert context is not None
    assert context.llm is not None
    assert context.cost_tracker is not None


def test_mock_llm_provider():
    """Test that mock LLM provider works."""
    from tests.mocks import MockLLMProvider

    mock_llm = MockLLMProvider(responses=[
        {"result": "test response"}
    ])

    response = mock_llm.chat_json("manager", "system prompt", "user content")
    assert response == {"result": "test response"}
    assert mock_llm.call_count == 1


def test_mock_cost_tracker():
    """Test that mock cost tracker works."""
    from tests.mocks import MockCostTracker

    tracker = MockCostTracker()
    tracker.reset()
    assert tracker.get_total_cost_usd() == 0.0

    tracker.register_call("manager", "gpt-4o", 100, 50)
    assert tracker.get_total_cost_usd() > 0.0


def test_orchestrator_main_signature():
    """Test that orchestrator.main() has the correct signature."""
    import inspect
    import orchestrator

    sig = inspect.signature(orchestrator.main)
    params = list(sig.parameters.keys())

    # Verify context parameter exists
    assert "context" in params

    # Verify it's optional (has a default value, even if that default is None)
    assert sig.parameters["context"].default != inspect.Parameter.empty


def test_orchestrator_run_signature():
    """Test that orchestrator.run() has the correct signature."""
    import inspect
    import orchestrator

    sig = inspect.signature(orchestrator.run)
    params = list(sig.parameters.keys())

    # Verify context parameter exists
    assert "context" in params

    # Verify other parameters still exist (backward compat)
    assert "config" in params
    assert "mission_id" in params


def test_orchestrator_2loop_main_signature():
    """Test that orchestrator_2loop.main() has the correct signature."""
    import inspect
    import orchestrator_2loop

    sig = inspect.signature(orchestrator_2loop.main)
    params = list(sig.parameters.keys())

    # Verify context parameter exists
    assert "context" in params


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
