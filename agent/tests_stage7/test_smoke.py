#!/usr/bin/env python3
"""
Smoke tests for Stage 7 - Web Dashboard.

Can be run without pytest for quick validation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))


def test_runner_imports():
    """Test that runner module imports successfully."""
    try:
        from runner import (
            get_run_details,  # noqa: F401
            list_projects,  # noqa: F401
            list_run_history,  # noqa: F401
            run_project,  # noqa: F401
        )


        print("✓ runner.py imports successfully")
        return True
    except ImportError as e:
        print(f"✗ runner.py import failed: {e}")
        return False


def test_list_projects():
    """Test list_projects function."""
    try:
        from runner import list_projects

        projects = list_projects()
        assert isinstance(projects, list), "list_projects() should return a list"
        print(f"✓ list_projects() works: {len(projects)} projects found")
        return True
    except Exception as e:
        print(f"✗ list_projects() failed: {e}")
        return False


def test_list_run_history():
    """Test list_run_history function."""
    try:
        from runner import list_run_history

        history = list_run_history()
        assert isinstance(history, list), "list_run_history() should return a list"
        print(f"✓ list_run_history() works: {len(history)} runs found")
        return True
    except Exception as e:
        print(f"✗ list_run_history() failed: {e}")
        return False


def test_webapp_imports():
    """Test that webapp imports successfully."""
    try:
        from webapp.app import app

        assert app is not None, "FastAPI app should not be None"
        print("✓ webapp/app.py imports successfully")
        return True
    except ImportError as e:
        print(f"✗ webapp/app.py import failed (FastAPI not installed?): {e}")
        return False
    except Exception as e:
        print(f"✗ webapp/app.py failed: {e}")
        return False


def test_run_project_validation():
    """Test run_project input validation."""
    try:
        from runner import run_project

        # Test missing required field
        try:
            run_project({"mode": "3loop"})
            print("✗ run_project() should raise ValueError for missing fields")
            return False
        except ValueError as e:
            if "Missing required config field" in str(e):
                print("✓ run_project() validates required fields")
            else:
                print(f"✗ Unexpected ValueError: {e}")
                return False

        # Test invalid mode
        try:
            run_project({
                "mode": "invalid",
                "project_subdir": "test",
                "task": "test",
            })
            print("✗ run_project() should raise ValueError for invalid mode")
            return False
        except ValueError as e:
            if "Invalid mode" in str(e):
                print("✓ run_project() validates mode")
            else:
                print(f"✗ Unexpected ValueError: {e}")
                return False

        return True
    except Exception as e:
        print(f"✗ run_project() validation failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("  STAGE 7 SMOKE TESTS - Web Dashboard")
    print("=" * 60)
    print()

    tests = [
        ("Module Imports (runner.py)", test_runner_imports),
        ("list_projects() function", test_list_projects),
        ("list_run_history() function", test_list_run_history),
        ("Module Imports (webapp)", test_webapp_imports),
        ("run_project() validation", test_run_project_validation),
    ]

    results = []
    for name, test_func in tests:
        print(f"[TEST] {name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test crashed: {e}")
            results.append(False)
        print()

    # Summary
    passed = sum(results)
    total = len(results)
    print("=" * 60)
    print(f"  Results: {passed}/{total} tests passed")
    if passed == total:
        print("  Status: ✓ ALL TESTS PASSED")
    else:
        print(f"  Status: ✗ {total - passed} TESTS FAILED")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
