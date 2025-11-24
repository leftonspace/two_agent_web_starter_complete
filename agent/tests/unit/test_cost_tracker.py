from pathlib import Path

import cost_tracker


def test_register_and_summary_basic() -> None:
    # reset global state
    cost_tracker.reset()

    # simulate a few calls
    cost_tracker.register_call("manager", "gpt-4o-mini", 1_000, 2_000)
    cost_tracker.register_call("employee", "gpt-4o", 500, 500)

    summary = cost_tracker.get_summary()

    # total number of calls
    assert summary["num_calls"] == 2

    # token counts add up
    assert summary["total_input_tokens"] == 1_500
    assert summary["total_output_tokens"] == 2_500

    # role breakdown present
    assert "manager" in summary["by_role"]
    assert "employee" in summary["by_role"]

    # model breakdown present
    assert "gpt-4o-mini" in summary["by_model"]
    assert "gpt-4o" in summary["by_model"]

    # total cost is > 0
    assert summary["total_usd"] > 0.0


def test_get_total_cost_usd_matches_summary() -> None:
    cost_tracker.reset()
    cost_tracker.register_call("manager", "gpt-4o-mini", 10_000, 0)

    summary = cost_tracker.get_summary()
    total_from_summary = summary["total_usd"]
    total_from_helper = cost_tracker.get_total_cost_usd()

    # they should match to within a tiny epsilon
    assert abs(total_from_summary - total_from_helper) < 1e-9


def test_append_history_creates_file(tmp_path: Path) -> None:
    cost_tracker.reset()
    cost_tracker.register_call("manager", "gpt-4o-mini", 1_000, 1_000)

    log_file = tmp_path / "history.jsonl"
    cost_tracker.append_history(
        log_file=log_file,
        project_name="unit-test-project",
        task="dummy task",
        status="completed",
        extra={"test": True},
    )

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8").strip()
    # one JSON line
    assert content.startswith("{") and content.endswith("}")
    assert '"project": "unit-test-project"' in content


def test_check_cost_cap_no_cap() -> None:
    """STAGE 5.2: Test cost cap check with no cap set."""
    cost_tracker.reset()

    would_exceed, current, message = cost_tracker.check_cost_cap(
        max_cost_usd=0.0,  # No cap
        estimated_tokens=5000,
        model="gpt-4o-mini",
    )

    assert would_exceed is False
    assert "No cost cap" in message


def test_check_cost_cap_within_budget() -> None:
    """STAGE 5.2: Test cost cap check when within budget."""
    cost_tracker.reset()
    # Add a small call
    cost_tracker.register_call("manager", "gpt-4o-mini", 100, 100)

    would_exceed, current, message = cost_tracker.check_cost_cap(
        max_cost_usd=1.0,  # High cap
        estimated_tokens=1000,
        model="gpt-4o-mini",
    )

    assert would_exceed is False
    assert "Within budget" in message
    assert current > 0.0


def test_check_cost_cap_would_exceed() -> None:
    """STAGE 5.2: Test cost cap check when next call would exceed cap."""
    cost_tracker.reset()
    # Add enough calls to get close to a small cap
    for _ in range(5):
        cost_tracker.register_call("manager", "gpt-4o", 10_000, 10_000)

    would_exceed, current, message = cost_tracker.check_cost_cap(
        max_cost_usd=0.01,  # Very small cap - already exceeded
        estimated_tokens=5000,
        model="gpt-4o",
    )

    assert would_exceed is True
    assert "would be exceeded" in message
    assert current > 0.0
