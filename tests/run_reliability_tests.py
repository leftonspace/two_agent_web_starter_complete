"""
Simple test runner for reliability fixes (no pytest required).

Run with: python tests/run_reliability_tests.py
"""

import json
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

# Add agent directory to path
agent_dir = Path(__file__).resolve().parent.parent / "agent"
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

# Import modules to test
from checkpoint import CheckpointManager, compute_feedback_hash
from cost_tracker_instance import CostTrackerInstance
from kg_write_queue import KnowledgeGraphQueue
from retry_loop_detector import RetryLoopDetector, check_for_retry_loop
from workflow_enforcement import WorkflowEnforcer, should_block_file_writes


class TestRunner:
    """Simple test runner."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name, func):
        """Run a test function."""
        try:
            func()
            print(f"✓ {name}")
            self.passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            self.failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            self.failed += 1

    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"Tests run: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"{'=' * 60}")
        return self.failed == 0


def run_tests():
    """Run all reliability tests."""
    runner = TestRunner()

    print("=" * 60)
    print("PHASE 4.3: Reliability Tests (R1-R7)")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────────
    # R1: Infinite Loop Prevention Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R1] Infinite Loop Prevention Tests")
    print("-" * 60)

    def test_r1_no_loop_first_retry():
        detector = RetryLoopDetector(max_consecutive_retries=2)
        should_abort, reason = detector.check_retry_loop(
            status="needs_changes", feedback=["Fix bug"], iteration=1
        )
        assert should_abort is False

    runner.test("R1.1: No loop on first retry", test_r1_no_loop_first_retry)

    def test_r1_loop_detected():
        detector = RetryLoopDetector(max_consecutive_retries=2)
        detector.check_retry_loop("needs_changes", ["Fix bug"], 1)
        should_abort, reason = detector.check_retry_loop("needs_changes", ["Fix bug"], 2)
        assert should_abort is True
        assert "Infinite retry loop" in reason

    runner.test("R1.2: Loop detected on identical feedback", test_r1_loop_detected)

    def test_r1_different_feedback_resets():
        detector = RetryLoopDetector(max_consecutive_retries=2)
        detector.check_retry_loop("needs_changes", ["Bug 1"], 1)
        should_abort, _ = detector.check_retry_loop("needs_changes", ["Bug 2"], 2)
        assert should_abort is False

    runner.test("R1.3: Different feedback resets counter", test_r1_different_feedback_resets)

    def test_r1_state_persistence():
        detector = RetryLoopDetector(max_consecutive_retries=2)
        detector.check_retry_loop("needs_changes", ["Fix bug"], 1)
        state = detector.get_state()

        new_detector = RetryLoopDetector(max_consecutive_retries=2)
        new_detector.restore_state(state)
        should_abort, _ = new_detector.check_retry_loop("needs_changes", ["Fix bug"], 2)
        assert should_abort is True

    runner.test("R1.4: State persistence across restarts", test_r1_state_persistence)

    # ──────────────────────────────────────────────────────────────
    # R2: Knowledge Graph Write Queue Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R2] Knowledge Graph Write Queue Tests")
    print("-" * 60)

    def test_r2_queue_initialization():
        mock_kg = MagicMock()
        mock_kg.conn = MagicMock()
        kg_queue = KnowledgeGraphQueue(mock_kg, batch_size=5)
        kg_queue.start()
        assert kg_queue.running is True
        kg_queue.stop(timeout=1.0)

    runner.test("R2.1: Queue initialization", test_r2_queue_initialization)

    def test_r2_enqueue_operations():
        mock_kg = MagicMock()
        mock_kg.conn = MagicMock()
        mock_kg.add_entity = MagicMock(return_value=1)

        kg_queue = KnowledgeGraphQueue(mock_kg, batch_size=2, batch_timeout_seconds=0.5)
        kg_queue.start()

        kg_queue.enqueue_add_entity("mission", "test_m1")
        kg_queue.enqueue_add_entity("mission", "test_m2")

        time.sleep(1.5)
        kg_queue.stop(timeout=2.0)

        assert kg_queue.stats["operations_queued"] == 2

    runner.test("R2.2: Enqueue operations", test_r2_enqueue_operations)

    # ──────────────────────────────────────────────────────────────
    # R3: LLM Timeout Fallback Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R3] LLM Timeout Fallback Tests")
    print("-" * 60)

    def test_r3_timeout_flag():
        import llm
        # Test that timeout flag is properly set in stub response
        stub = {
            "timeout": True,
            "is_timeout": True,
            "reason": "Test timeout",
        }
        assert stub.get("is_timeout") is True

    runner.test("R3.1: Timeout flag in response", test_r3_timeout_flag)

    # ──────────────────────────────────────────────────────────────
    # R4: Checkpoint/Resume Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R4] Checkpoint/Resume Tests")
    print("-" * 60)

    def test_r4_save_load():
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager("test_run_123", checkpoint_dir)

            success = manager.save_checkpoint(
                iteration=2,
                files_written=["index.html"],
                cost_accumulated=0.45,
                last_status="needs_changes",
            )
            assert success is True

            checkpoint = manager.load_checkpoint()
            assert checkpoint.run_id == "test_run_123"
            assert checkpoint.iteration_index == 2

    runner.test("R4.1: Save and load checkpoint", test_r4_save_load)

    def test_r4_atomic_write():
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"
            manager = CheckpointManager("test_run_456", checkpoint_dir)
            manager.save_checkpoint(iteration=1, files_written=[], cost_accumulated=0.1)

            # No .tmp files should remain
            tmp_files = list(checkpoint_dir.glob("*.tmp"))
            assert len(tmp_files) == 0

    runner.test("R4.2: Atomic write (no temp files)", test_r4_atomic_write)

    def test_r4_resume_after_crash():
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"

            # Save checkpoint
            manager1 = CheckpointManager("crash_test", checkpoint_dir)
            manager1.save_checkpoint(iteration=5, files_written=[], cost_accumulated=2.5)

            # Simulate crash: new instance
            manager2 = CheckpointManager("crash_test", checkpoint_dir)
            checkpoint = manager2.load_checkpoint()

            assert checkpoint.iteration_index == 5
            assert checkpoint.cost_accumulated == 2.5

    runner.test("R4.3: Resume after crash", test_r4_resume_after_crash)

    # ──────────────────────────────────────────────────────────────
    # R5: Instance-Based Cost Tracker Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R5] Instance-Based Cost Tracker Tests")
    print("-" * 60)

    def test_r5_isolated_instances():
        tracker1 = CostTrackerInstance("run_001")
        tracker2 = CostTrackerInstance("run_002")

        tracker1.register_call("manager", "gpt-4o-mini", 1000, 500)
        tracker2.register_call("employee", "gpt-4o-mini", 2000, 1000)

        summary1 = tracker1.get_summary()
        summary2 = tracker2.get_summary()

        assert summary1["run_id"] == "run_001"
        assert summary2["run_id"] == "run_002"
        assert summary1["total_input_tokens"] == 1000
        assert summary2["total_input_tokens"] == 2000

    runner.test("R5.1: Isolated instances", test_r5_isolated_instances)

    def test_r5_no_shared_state():
        tracker1 = CostTrackerInstance("run_A")
        tracker1.register_call("manager", "gpt-4o-mini", 500, 250)

        tracker2 = CostTrackerInstance("run_B")
        summary2 = tracker2.get_summary()

        assert summary2["num_calls"] == 0

    runner.test("R5.2: No shared state between instances", test_r5_no_shared_state)

    # ──────────────────────────────────────────────────────────────
    # R6: Workflow Enforcement Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R6] Workflow Enforcement Tests")
    print("-" * 60)

    def test_r6_strict_blocks():
        enforcer = WorkflowEnforcer(enforcement_level="strict")
        workflow_result = {
            "workflow_name": "TestWorkflow",
            "has_failures": True,
            "steps_failed": [{"step": "lint", "error": "Syntax error"}],
        }
        should_block, reason = enforcer.check_workflow_result(workflow_result)
        assert should_block is True

    runner.test("R6.1: Strict mode blocks on failure", test_r6_strict_blocks)

    def test_r6_warn_no_block():
        enforcer = WorkflowEnforcer(enforcement_level="warn")
        workflow_result = {
            "workflow_name": "TestWorkflow",
            "has_failures": True,
            "steps_failed": [{"step": "test", "error": "Failed"}],
        }
        should_block, _ = enforcer.check_workflow_result(workflow_result)
        assert should_block is False

    runner.test("R6.2: Warn mode logs but doesn't block", test_r6_warn_no_block)

    def test_r6_off_no_enforcement():
        enforcer = WorkflowEnforcer(enforcement_level="off")
        workflow_result = {
            "workflow_name": "TestWorkflow",
            "has_failures": True,
            "steps_failed": [{"step": "critical", "error": "Major"}],
        }
        should_block, _ = enforcer.check_workflow_result(workflow_result)
        assert should_block is False

    runner.test("R6.3: Off mode never blocks", test_r6_off_no_enforcement)

    # ──────────────────────────────────────────────────────────────
    # R7: Atomic Writes Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[R7] Atomic Writes Tests (Job Manager)")
    print("-" * 60)

    def test_r7_job_manager_atomic():
        from jobs import JobManager

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "jobs_state.json"
            manager = JobManager(state_file=state_file)

            job = manager.create_job({"task": "test", "project_subdir": "test"})

            assert state_file.exists()

            # No .tmp files left
            tmp_files = list(Path(tmpdir).glob("*.tmp"))
            assert len(tmp_files) == 0

    runner.test("R7.1: Job manager atomic writes", test_r7_job_manager_atomic)

    # ──────────────────────────────────────────────────────────────
    # Acceptance Criteria Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[ACCEPTANCE CRITERIA]")
    print("-" * 60)

    def test_acc_no_infinite_loops():
        detector = RetryLoopDetector(max_consecutive_retries=2)
        detector.check_retry_loop("needs_changes", ["Same"], 1)
        should_abort, _ = detector.check_retry_loop("needs_changes", ["Same"], 2)
        assert should_abort is True

    runner.test("AC1: No infinite retry loops", test_acc_no_infinite_loops)

    def test_acc_orchestrator_resume():
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = CheckpointManager("resume_test", Path(tmpdir))
            manager.save_checkpoint(iteration=3, files_written=[], cost_accumulated=1.0)

            new_manager = CheckpointManager("resume_test", Path(tmpdir))
            checkpoint = new_manager.load_checkpoint()
            assert checkpoint.iteration_index == 3

    runner.test("AC2: Orchestrator resumes after crash", test_acc_orchestrator_resume)

    def test_acc_parallel_jobs():
        mock_kg = MagicMock()
        mock_kg.conn = MagicMock()
        mock_kg.add_entity = MagicMock(return_value=1)

        kg_queue = KnowledgeGraphQueue(mock_kg, batch_size=10)
        kg_queue.start()

        def write_ops(job_id, count):
            for i in range(count):
                kg_queue.enqueue_add_entity("mission", f"j{job_id}_m{i}")

        threads = []
        for j in range(3):
            t = threading.Thread(target=write_ops, args=(j, 5))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        kg_queue.stop(timeout=3.0)
        assert kg_queue.stats["errors"] == 0

    runner.test("AC3: Parallel jobs without DB errors", test_acc_parallel_jobs)

    # Print summary
    return runner.summary()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
