#!/usr/bin/env python3
"""
Smoke tests for Stage 8 - Job Manager.

Can be run without pytest for quick validation.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))


def test_jobs_imports():
    """Test that jobs module imports successfully."""
    try:
        from jobs import Job, JobManager, get_job_manager  # noqa: F401


        print("✓ jobs.py imports successfully")
        return True
    except ImportError as e:
        print(f"✗ jobs.py import failed: {e}")
        return False


def test_job_creation():
    """Test creating a job."""
    try:
        from jobs import JobManager

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_state = Path(tmpdir) / "jobs_state.json"
            manager = JobManager(state_file=temp_state)

            config = {
                "mode": "3loop",
                "project_subdir": "test",
                "task": "Test task",
                "max_rounds": 1,
            }

            job = manager.create_job(config)
            assert job.id is not None, "Job should have an ID"
            assert job.status == "queued", "Job should be queued"
            assert len(job.id) == 12, "Job ID should be 12 characters"

            print("✓ Job creation works")
            return True
    except Exception as e:
        print(f"✗ Job creation failed: {e}")
        return False


def test_job_list():
    """Test listing jobs."""
    try:
        from jobs import JobManager

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_state = Path(tmpdir) / "jobs_state.json"
            manager = JobManager(state_file=temp_state)

            config = {
                "mode": "3loop",
                "project_subdir": "test",
                "task": "Test task",
                "max_rounds": 1,
            }

            _job1 = manager.create_job(config)
            job2 = manager.create_job(config)


            jobs = manager.list_jobs()
            assert len(jobs) == 2, "Should have 2 jobs"
            assert jobs[0].id == job2.id, "Jobs should be sorted newest first"

            print("✓ Job listing works")
            return True
    except Exception as e:
        print(f"✗ Job listing failed: {e}")
        return False


def test_job_update():
    """Test updating a job."""
    try:
        from jobs import JobManager

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_state = Path(tmpdir) / "jobs_state.json"
            manager = JobManager(state_file=temp_state)

            config = {
                "mode": "3loop",
                "project_subdir": "test",
                "task": "Test task",
                "max_rounds": 1,
            }

            job = manager.create_job(config)
            assert job.status == "queued"

            updated = manager.update_job(job.id, status="running")
            assert updated is not None, "Update should return job"
            assert updated.status == "running", "Status should be updated"

            print("✓ Job updates work")
            return True
    except Exception as e:
        print(f"✗ Job updates failed: {e}")
        return False


def test_job_cancellation():
    """Test cancelling a job."""
    try:
        from jobs import JobManager

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_state = Path(tmpdir) / "jobs_state.json"
            manager = JobManager(state_file=temp_state)

            config = {
                "mode": "3loop",
                "project_subdir": "test",
                "task": "Test task",
                "max_rounds": 1,
            }

            job = manager.create_job(config)
            success = manager.cancel_job(job.id)
            assert success, "Cancellation should succeed"

            updated = manager.get_job(job.id)
            assert updated.cancelled, "Job should be marked as cancelled"

            print("✓ Job cancellation works")
            return True
    except Exception as e:
        print(f"✗ Job cancellation failed: {e}")
        return False


def test_webapp_imports():
    """Test that webapp imports successfully with job support."""
    try:
        # Check if FastAPI is installed
        import fastapi  # noqa: F401

        from webapp.app import app

        assert app is not None, "FastAPI app should not be None"
        print("✓ webapp/app.py imports successfully with job support")
        return True
    except ImportError as e:
        if "fastapi" in str(e).lower():
            print("⚠️  webapp/app.py requires FastAPI (expected - install with pip)")
            return True  # Not a failure, just missing dependency
        else:
            print(f"✗ webapp/app.py import failed: {e}")
            return False
    except Exception as e:
        print(f"✗ webapp/app.py failed: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("  STAGE 8 SMOKE TESTS - Job Manager")
    print("=" * 60)
    print()

    tests = [
        ("Module Imports (jobs.py)", test_jobs_imports),
        ("Job Creation", test_job_creation),
        ("Job Listing", test_job_list),
        ("Job Updates", test_job_update),
        ("Job Cancellation", test_job_cancellation),
        ("Webapp Integration", test_webapp_imports),
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
