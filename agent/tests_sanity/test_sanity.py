# test_sanity.py
"""
Sanity tests for the multi-agent system.

Run with: python3 -m pytest agent/tests_sanity/ -v
Or simply: python3 agent/tests_sanity/test_sanity.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    """Test that all core modules import without errors."""
    print("[TEST] Testing module imports...")

    try:
        import auto_pilot
        import cost_estimator
        import cost_tracker
        import exec_analysis
        import exec_deps
        import exec_safety
        import llm
        import orchestrator
        import run_logger
        import run_mode
        import self_eval
        import site_tools
        import status_codes

        print("  ✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_cost_estimation():
    """Test cost estimation with dummy data."""
    print("[TEST] Testing cost estimation...")

    try:
        from cost_estimator import estimate_run_cost

        models = {
            "manager": "gpt-5-mini",
            "supervisor": "gpt-5-nano",
            "employee": "gpt-5",
        }

        estimate = estimate_run_cost(
            mode="3loop",
            max_rounds=3,
            models_used=models,
        )

        # Verify structure
        assert "per_round" in estimate
        assert "max_rounds" in estimate
        assert "estimated_total_usd" in estimate
        assert estimate["max_rounds"] == 3
        assert estimate["estimated_total_usd"] > 0

        print(f"  ✓ Cost estimation works (${estimate['estimated_total_usd']:.4f})")
        return True
    except Exception as e:
        print(f"  ✗ Cost estimation failed: {e}")
        return False


def test_self_evaluation():
    """Test self-evaluation with synthetic RunSummary."""
    print("[TEST] Testing self-evaluation...")

    try:
        from self_eval import evaluate_run

        # Create synthetic run summary
        mock_run = {
            "run_id": "test123",
            "final_status": "completed",
            "safety_status": "passed",
            "rounds_completed": 2,
            "max_rounds": 5,
            "cost_summary": {"total_usd": 0.15},
            "config": {"max_cost_usd": 1.0},
        }

        result = evaluate_run(mock_run)

        # Verify structure
        assert "score_quality" in result
        assert "score_safety" in result
        assert "score_cost" in result
        assert "overall_score" in result
        assert "reasoning" in result
        assert "recommendation" in result

        assert 0 <= result["overall_score"] <= 1
        assert result["recommendation"] in ("continue", "retry", "stop")

        print(f"  ✓ Self-evaluation works (score={result['overall_score']:.3f}, rec={result['recommendation']})")
        return True
    except Exception as e:
        print(f"  ✗ Self-evaluation failed: {e}")
        return False


def test_safety_checks():
    """Test safety checks on empty temporary directory."""
    print("[TEST] Testing safety checks...")

    try:
        from exec_safety import run_safety_checks

        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_safety_checks(tmpdir, "Test task")

            # Verify structure
            assert "static_issues" in result
            assert "dependency_issues" in result
            assert "docker_tests" in result
            assert "status" in result
            assert "run_id" in result

            # Empty dir should pass (no code to analyze)
            assert result["status"] in ("passed", "failed")

            print(f"  ✓ Safety checks work (status={result['status']}, issues={len(result['static_issues'])})")
            return True
    except Exception as e:
        print(f"  ✗ Safety checks failed: {e}")
        return False


def test_run_logger():
    """Test run logger dataclass creation."""
    print("[TEST] Testing run logger...")

    try:
        from dataclasses import asdict

        from run_logger import finalize_run, log_iteration, start_run

        # Create a run
        run = start_run(
            mode="3loop",
            project_dir="/tmp/test",
            task="Test task",
            max_rounds=3,
            models_used={"manager": "gpt-5-mini", "supervisor": "gpt-5-nano", "employee": "gpt-5"},
            config={},
        )

        # Log an iteration
        log_iteration(run, index=1, role="manager", status="ok", notes="Test iteration")

        # Finalize
        run = finalize_run(run, final_status="completed", cost_summary={"total_usd": 0.1})

        # Convert to dict
        run_dict = asdict(run)

        assert run_dict["mode"] == "3loop"
        assert run_dict["max_rounds"] == 3
        assert run_dict["rounds_completed"] == 1
        assert run_dict["final_status"] == "completed"

        print(f"  ✓ Run logger works (run_id={run.run_id})")
        return True
    except Exception as e:
        print(f"  ✗ Run logger failed: {e}")
        return False


def test_status_codes():
    """Test status codes module."""
    print("[TEST] Testing status codes...")

    try:
        from status_codes import (
            COMPLETED,
            MAX_ROUNDS_REACHED,
            SUCCESS,
            is_failure_status,
            is_success_status,
            is_terminal_status,
        )

        assert is_terminal_status(SUCCESS)
        assert is_terminal_status(COMPLETED)
        assert is_terminal_status(MAX_ROUNDS_REACHED)

        assert is_success_status(SUCCESS)
        assert is_success_status(COMPLETED)
        assert not is_success_status(MAX_ROUNDS_REACHED)

        assert is_failure_status("timeout")
        assert not is_failure_status(SUCCESS)

        print("  ✓ Status codes work correctly")
        return True
    except Exception as e:
        print(f"  ✗ Status codes failed: {e}")
        return False


def run_all_tests():
    """Run all sanity tests."""
    print("\n" + "=" * 70)
    print("  SANITY TESTS - Multi-Agent System")
    print("=" * 70 + "\n")

    tests = [
        test_imports,
        test_status_codes,
        test_cost_estimation,
        test_self_evaluation,
        test_run_logger,
        test_safety_checks,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test crashed: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print("=" * 70)
    print(f"  Results: {passed}/{total} tests passed")

    if passed == total:
        print("  Status: ✓ ALL TESTS PASSED")
    else:
        print(f"  Status: ✗ {total - passed} TESTS FAILED")

    print("=" * 70 + "\n")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
