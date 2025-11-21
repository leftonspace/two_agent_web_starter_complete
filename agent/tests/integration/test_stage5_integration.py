"""
Integration tests for Stage 5.2: Cost Controls and Model Routing.

Tests cost cap enforcement, run summaries, and fallback logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import cost_tracker
import core_logging
from llm import chat_json


def test_cost_cap_blocks_expensive_call() -> None:
    """
    STAGE 5.2 Integration: Verify cost cap blocks call when budget would be exceeded.
    """
    cost_tracker.reset()

    # Simulate previous expensive calls that nearly exhaust budget
    for _ in range(3):
        cost_tracker.register_call("manager", "gpt-5", 10_000, 10_000)

    # Try to make another call with a tiny cap
    # This should return error stub instead of making the call
    with patch("llm._post") as mock_post:
        result = chat_json(
            role="manager",
            system_prompt="Test system",
            user_content="Test content",
            max_cost_usd=0.01,  # Very low cap - already exceeded
        )

        # Should NOT have called _post because cap would be exceeded
        assert mock_post.call_count == 0, "Expected _post to not be called due to cost cap"

        # Result should indicate cost cap hit
        assert result.get("status") == "cost_cap_exceeded"
        assert result.get("cost_cap_hit") is True
        assert "cost cap would be exceeded" in result.get("notes", "").lower()


def test_cost_cap_allows_within_budget() -> None:
    """
    STAGE 5.2 Integration: Verify calls proceed when within budget.
    """
    cost_tracker.reset()

    # Mock _post to return a fake response
    fake_response = {
        "choices": [{"message": {"content": '{"status": "ok"}'}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }

    with patch("llm._post", return_value=fake_response):
        result = chat_json(
            role="manager",
            system_prompt="Test system",
            user_content="Test content",
            max_cost_usd=10.0,  # High cap - plenty of budget
        )

        # Should succeed
        assert result.get("status") != "cost_cap_exceeded"
        assert "cost_cap_hit" not in result


def test_cost_checkpoints_logged() -> None:
    """
    STAGE 5.2 Integration: Verify cost checkpoints are logged correctly.
    """
    cost_tracker.reset()

    # Register some calls
    cost_tracker.register_call("manager", "gpt-5-mini", 1000, 500)
    cost_tracker.register_call("employee", "gpt-5", 2000, 1000)

    run_id = core_logging.new_run_id()
    max_cost = 1.0

    # Log a cost checkpoint
    core_logging.log_cost_checkpoint(
        run_id=run_id,
        checkpoint="test_checkpoint",
        total_cost_usd=cost_tracker.get_total_cost_usd(),
        max_cost_usd=max_cost,
        cost_summary=cost_tracker.get_summary(),
    )

    # Verify log file exists
    log_file = core_logging.LOGS_DIR / f"{run_id}.jsonl"
    assert log_file.exists(), f"Expected log file {log_file} to exist"

    # Read and verify the log entry
    with log_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        # Should have at least one line (the cost checkpoint)
        assert len(lines) >= 1

        # Find the cost_checkpoint event
        cost_checkpoint_found = False
        for line in lines:
            import json

            entry = json.loads(line)
            if entry.get("event_type") == "cost_checkpoint":
                cost_checkpoint_found = True
                payload = entry.get("payload", {})

                # Verify payload structure
                assert payload.get("checkpoint") == "test_checkpoint"
                assert payload.get("total_cost_usd") > 0
                assert payload.get("max_cost_usd") == max_cost
                assert "cost_summary" in payload

                # Verify cost summary structure
                summary = payload["cost_summary"]
                assert "num_calls" in summary
                assert "total_usd" in summary
                assert "by_role" in summary
                assert "by_model" in summary

                break

        assert cost_checkpoint_found, "Expected to find cost_checkpoint event in logs"


def test_llm_timeout_fallback() -> None:
    """
    STAGE 5.2 Integration: Verify timeout returns stub response without crashing.
    """
    # Mock _post to return timeout stub
    timeout_stub = {
        "timeout": True,
        "reason": "Connection timeout",
        "plan": [],
        "files": {},
        "notes": "Step skipped due to upstream API error. Safe stub returned by llm._post.",
        "status": "timeout",
    }

    with patch("llm._post", return_value=timeout_stub):
        result = chat_json(
            role="employee",
            system_prompt="Test system",
            user_content="Test content",
        )

        # Should return graceful stub
        assert result.get("status") == "timeout"
        assert "stub" in result.get("notes", "").lower() or "failure" in result.get("notes", "").lower()
        assert isinstance(result.get("files"), dict)  # Should be dict, not crash


def test_model_routing_enforces_gpt5_gating() -> None:
    """
    STAGE 5.2 Integration: Verify GPT-5 is not used on first interaction.
    """
    from model_router import choose_model

    # First interaction, high complexity, very important
    # Should still NOT use GPT-5
    model = choose_model(
        task_type="code",
        complexity="high",
        role="employee",
        interaction_index=1,  # FIRST iteration
        is_very_important=True,
    )

    # Should not be GPT-5
    assert "gpt-5-2025" not in model, f"Expected no GPT-5 on first iteration, got: {model}"
    assert "gpt-5-mini" in model or "gpt-5-nano" in model, f"Expected cheaper model, got: {model}"


def test_model_routing_allows_gpt5_on_second_iteration() -> None:
    """
    STAGE 5.2 Integration: Verify GPT-5 IS used on 2nd/3rd iterations when appropriate.
    """
    from model_router import choose_model

    # Second interaction, high complexity
    model = choose_model(
        task_type="code",
        complexity="high",
        role="employee",
        interaction_index=2,  # SECOND iteration
        is_very_important=False,
    )

    # Should use GPT-5 now
    assert "gpt-5-2025" in model, f"Expected GPT-5 on 2nd iteration with high complexity, got: {model}"


def test_run_summary_includes_cost_data() -> None:
    """
    STAGE 5.2 Integration: Verify run summaries include cost breakdown.
    """
    cost_tracker.reset()

    # Simulate a run with multiple calls
    cost_tracker.register_call("manager", "gpt-5-mini", 1000, 500)
    cost_tracker.register_call("supervisor", "gpt-5-nano", 800, 400)
    cost_tracker.register_call("employee", "gpt-5", 3000, 2000)

    # Get summary
    summary = cost_tracker.get_summary()

    # Verify structure
    assert "num_calls" in summary
    assert summary["num_calls"] == 3

    assert "total_usd" in summary
    assert summary["total_usd"] > 0

    assert "by_role" in summary
    assert "manager" in summary["by_role"]
    assert "supervisor" in summary["by_role"]
    assert "employee" in summary["by_role"]

    assert "by_model" in summary
    assert "gpt-5-mini" in summary["by_model"]
    assert "gpt-5-nano" in summary["by_model"]
    assert "gpt-5" in summary["by_model"]

    # Verify role breakdown
    manager_stats = summary["by_role"]["manager"]
    assert manager_stats["num_calls"] == 1
    assert manager_stats["prompt_tokens"] == 1000
    assert manager_stats["completion_tokens"] == 500

    # Verify model breakdown
    gpt5_stats = summary["by_model"]["gpt-5"]
    assert gpt5_stats["num_calls"] == 1
    assert gpt5_stats["total_usd"] > 0


def test_config_validation_catches_invalid_cost_caps() -> None:
    """
    STAGE 5.2 Integration: Verify _validate_cost_config catches invalid settings.
    """
    from orchestrator import _validate_cost_config

    # Test invalid max_cost_usd
    try:
        _validate_cost_config({"max_cost_usd": "not_a_number"})
        assert False, "Expected ValueError for invalid max_cost_usd"
    except ValueError as e:
        assert "must be a valid number" in str(e)

    # Test negative max_cost_usd
    try:
        _validate_cost_config({"max_cost_usd": -5.0})
        assert False, "Expected ValueError for negative max_cost_usd"
    except ValueError as e:
        assert "must be >= 0" in str(e)

    # Test invalid llm_very_important_stages type
    try:
        _validate_cost_config({"llm_very_important_stages": "not_a_list"})
        assert False, "Expected ValueError for non-list llm_very_important_stages"
    except ValueError as e:
        assert "must be a list" in str(e)

    # Test valid config
    try:
        _validate_cost_config({
            "max_cost_usd": 10.0,
            "cost_warning_usd": 5.0,
            "llm_very_important_stages": ["stage1", "stage2"],
        })
        # Should succeed without exception
    except ValueError:
        assert False, "Expected valid config to pass validation"
