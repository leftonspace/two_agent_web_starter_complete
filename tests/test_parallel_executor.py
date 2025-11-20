"""
PHASE 5.2: Tests for Parallel Tool Execution

Tests parallel tool execution with asyncio, dependency resolution,
error handling, and performance improvements.

Run with: python tests/test_parallel_executor.py
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent / "agent"
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from parallel_executor import (
    ParallelExecutor,
    TaskStatus,
    ToolTask,
    git_diff_async,
    git_status_async,
    run_subprocess_async,
)


class TestRunner:
    """Simple test runner for async tests."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test(self, name, func):
        """Run a test function (supports both sync and async)."""
        try:
            if asyncio.iscoroutinefunction(func):
                asyncio.run(func())
            else:
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


# ══════════════════════════════════════════════════════════════════════
# Test Helpers
# ══════════════════════════════════════════════════════════════════════


async def mock_success_task(**kwargs) -> Dict[str, Any]:
    """Mock task that always succeeds."""
    await asyncio.sleep(0.05)
    return {"status": "success", "output": "Task completed", "exit_code": 0}


async def mock_failure_task(**kwargs) -> Dict[str, Any]:
    """Mock task that always fails."""
    await asyncio.sleep(0.05)
    return {"status": "failed", "error": "Task failed", "exit_code": 1}


async def mock_slow_task(delay: float = 0.5, **kwargs) -> Dict[str, Any]:
    """Mock task that takes a specified time."""
    await asyncio.sleep(delay)
    return {"status": "success", "output": f"Completed after {delay}s", "exit_code": 0}


async def mock_exception_task(**kwargs) -> Dict[str, Any]:
    """Mock task that raises an exception."""
    await asyncio.sleep(0.02)
    raise RuntimeError("Intentional test exception")


def create_test_git_repo(project_dir: Path):
    """Create a test git repository."""
    try:
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True, timeout=5)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            timeout=5,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            timeout=5,
        )

        # Create initial file
        (project_dir / "test.txt").write_text("initial content")
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True, timeout=5)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit", "--no-gpg-sign"],
            cwd=project_dir,
            check=True,
            capture_output=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"Failed to create test git repo: {e}")


# ══════════════════════════════════════════════════════════════════════
# Test Suite
# ══════════════════════════════════════════════════════════════════════


def run_tests():
    """Run all parallel executor tests."""
    runner = TestRunner()

    print("=" * 60)
    print("PHASE 5.2: Parallel Tool Execution Tests")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────────
    # Basic Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[BASIC] Basic Execution Tests")
    print("-" * 60)

    async def test_parallel_executor_initialization():
        """Test ParallelExecutor initialization."""
        executor = ParallelExecutor(max_concurrency=3, default_timeout=60, verbose=False)
        assert executor.max_concurrency == 3
        assert executor.default_timeout == 60
        assert executor.verbose is False

    runner.test("Initialize ParallelExecutor", test_parallel_executor_initialization)

    async def test_single_task_execution():
        """Test executing a single task."""
        executor = ParallelExecutor(verbose=False)
        tasks = [ToolTask(name="test1", func=mock_success_task, kwargs={})]
        results = await executor.execute_parallel(tasks)

        assert len(results) == 1
        assert "test1" in results
        assert results["test1"]["status"] == "success"

    runner.test("Single task execution", test_single_task_execution)

    async def test_multiple_parallel_tasks():
        """Test executing multiple tasks in parallel."""
        executor = ParallelExecutor(max_concurrency=5, verbose=False)
        tasks = [
            ToolTask(name=f"task{i}", func=mock_success_task, kwargs={})
            for i in range(5)
        ]

        start_time = time.time()
        results = await executor.execute_parallel(tasks)
        elapsed = time.time() - start_time

        assert len(results) == 5
        for i in range(5):
            assert results[f"task{i}"]["status"] == "success"

        # Parallel should be faster than 250ms (5 * 50ms sequential)
        assert elapsed < 0.2, f"Not parallel enough: {elapsed}s"

    runner.test("Multiple parallel tasks", test_multiple_parallel_tasks)

    async def test_concurrency_limit():
        """Test that concurrency limit is respected."""
        executor = ParallelExecutor(max_concurrency=2, verbose=False)
        tasks = [
            ToolTask(name=f"task{i}", func=mock_slow_task, kwargs={"delay": 0.15})
            for i in range(4)
        ]

        start_time = time.time()
        results = await executor.execute_parallel(tasks)
        elapsed = time.time() - start_time

        assert len(results) == 4
        # With max_concurrency=2, should take at least 300ms (2 batches of 150ms)
        assert elapsed >= 0.25, f"Concurrency limit not working: {elapsed}s"

    runner.test("Concurrency limit respected", test_concurrency_limit)

    async def test_task_failure_handling():
        """Test that task failures are handled gracefully."""
        executor = ParallelExecutor(verbose=False)
        tasks = [
            ToolTask(name="success", func=mock_success_task, kwargs={}),
            ToolTask(name="failure", func=mock_failure_task, kwargs={}),
        ]

        results = await executor.execute_parallel(tasks, fail_fast=False)

        assert len(results) == 2
        assert results["success"]["status"] == "success"
        assert results["failure"]["status"] == "failed"

    runner.test("Task failure handling", test_task_failure_handling)

    async def test_task_exception_handling():
        """Test that exceptions in tasks are caught."""
        executor = ParallelExecutor(verbose=False)
        tasks = [ToolTask(name="exception", func=mock_exception_task, kwargs={})]

        results = await executor.execute_parallel(tasks)

        assert "exception" in results
        assert results["exception"]["status"] == "failed"
        assert "Intentional test exception" in results["exception"]["error"]

    runner.test("Task exception handling", test_task_exception_handling)

    async def test_task_timeout():
        """Test that tasks respect timeout."""
        executor = ParallelExecutor(verbose=False)
        tasks = [
            ToolTask(
                name="timeout_task",
                func=mock_slow_task,
                kwargs={"delay": 5.0},
                timeout=0.15,
            )
        ]

        start_time = time.time()
        results = await executor.execute_parallel(tasks)
        elapsed = time.time() - start_time

        assert results["timeout_task"]["status"] == "failed"
        assert "timed out" in results["timeout_task"]["error"].lower()
        assert results["timeout_task"]["exit_code"] == 124
        assert elapsed < 1.0, f"Timeout took too long: {elapsed}s"

    runner.test("Task timeout enforcement", test_task_timeout)

    # ──────────────────────────────────────────────────────────────
    # Dependency Resolution Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[DEPS] Dependency Resolution Tests")
    print("-" * 60)

    async def test_execution_plan_no_dependencies():
        """Test execution plan with no dependencies."""
        executor = ParallelExecutor(verbose=False)
        tasks = [
            ToolTask(name=f"task{i}", func=mock_success_task, kwargs={})
            for i in range(3)
        ]

        plan = executor._build_execution_plan(tasks)

        assert len(plan.batches) == 1
        assert len(plan.batches[0]) == 3
        assert plan.total_tasks == 3
        assert not plan.has_dependencies

    runner.test("Execution plan without dependencies", test_execution_plan_no_dependencies)

    async def test_execution_plan_with_dependencies():
        """Test execution plan with dependencies."""
        executor = ParallelExecutor(verbose=False)
        tasks = [
            ToolTask(name="task1", func=mock_success_task, kwargs={}, depends_on=[]),
            ToolTask(name="task2", func=mock_success_task, kwargs={}, depends_on=["task1"]),
            ToolTask(name="task3", func=mock_success_task, kwargs={}, depends_on=["task1"]),
            ToolTask(name="task4", func=mock_success_task, kwargs={}, depends_on=["task2", "task3"]),
        ]

        plan = executor._build_execution_plan(tasks)

        assert len(plan.batches) == 3
        assert len(plan.batches[0]) == 1  # task1
        assert len(plan.batches[1]) == 2  # task2, task3
        assert len(plan.batches[2]) == 1  # task4
        assert plan.has_dependencies

    runner.test("Execution plan with dependencies", test_execution_plan_with_dependencies)

    async def test_execute_with_dependencies():
        """Test executing tasks with dependencies."""
        executor = ParallelExecutor(max_concurrency=5, verbose=False)
        execution_order = []

        async def track_task(task_name: str, **kwargs):
            execution_order.append(task_name)
            await asyncio.sleep(0.03)
            return {"status": "success", "output": f"{task_name} completed", "exit_code": 0}

        tasks = [
            ToolTask(name="task1", func=lambda **kw: track_task("task1", **kw), kwargs={}, depends_on=[]),
            ToolTask(name="task2", func=lambda **kw: track_task("task2", **kw), kwargs={}, depends_on=["task1"]),
            ToolTask(name="task3", func=lambda **kw: track_task("task3", **kw), kwargs={}, depends_on=["task1"]),
            ToolTask(name="task4", func=lambda **kw: track_task("task4", **kw), kwargs={}, depends_on=["task2", "task3"]),
        ]

        results = await executor.execute_with_dependencies(tasks)

        assert len(results) == 4
        for task_name in ["task1", "task2", "task3", "task4"]:
            assert results[task_name]["status"] == "success"

        # Verify execution order respects dependencies
        assert execution_order[0] == "task1"
        assert execution_order[-1] == "task4"

    runner.test("Execute tasks with dependencies", test_execute_with_dependencies)

    async def test_circular_dependency_detection():
        """Test that circular dependencies are detected."""
        executor = ParallelExecutor(verbose=False)
        tasks = [
            ToolTask(name="task1", func=mock_success_task, kwargs={}, depends_on=["task2"]),
            ToolTask(name="task2", func=mock_success_task, kwargs={}, depends_on=["task1"]),
        ]

        try:
            executor._build_execution_plan(tasks)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Circular dependency" in str(e)

    runner.test("Circular dependency detection", test_circular_dependency_detection)

    # ──────────────────────────────────────────────────────────────
    # Subprocess Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[SUBPROCESS] Async Subprocess Tests")
    print("-" * 60)

    async def test_run_subprocess_async_success():
        """Test successful subprocess execution."""
        result = await run_subprocess_async(["echo", "hello"])
        assert result["status"] == "success"
        assert result["exit_code"] == 0
        assert "hello" in result["output"]

    runner.test("Subprocess success", test_run_subprocess_async_success)

    async def test_run_subprocess_async_timeout():
        """Test subprocess timeout."""
        result = await run_subprocess_async(["sleep", "10"], timeout=0.15)
        assert result["status"] == "failed"
        assert result["exit_code"] == 124
        assert "timed out" in result["error"].lower()

    runner.test("Subprocess timeout", test_run_subprocess_async_timeout)

    # ──────────────────────────────────────────────────────────────
    # Git Operations Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[GIT] Git Operations Tests")
    print("-" * 60)

    async def test_git_status_async():
        """Test async git status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()
            create_test_git_repo(project_dir)

            # Create a new file
            (project_dir / "new_file.txt").write_text("new content")

            result = await git_status_async(str(project_dir))
            assert result["status"] == "success"
            assert result["exit_code"] == 0
            assert "new_file.txt" in result["output"]

    runner.test("Git status async", test_git_status_async)

    async def test_git_diff_async():
        """Test async git diff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()
            create_test_git_repo(project_dir)

            # Modify existing file
            (project_dir / "test.txt").write_text("modified content")

            result = await git_diff_async(str(project_dir))
            assert result["status"] == "success"
            assert result["exit_code"] == 0

    runner.test("Git diff async", test_git_diff_async)

    async def test_parallel_git_operations():
        """Test running git operations in parallel."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "test_project"
            project_dir.mkdir()
            create_test_git_repo(project_dir)

            # Modify file
            (project_dir / "test.txt").write_text("modified")

            executor = ParallelExecutor(max_concurrency=2, verbose=False)
            tasks = [
                ToolTask(name="git_status", func=git_status_async, kwargs={"project_dir": str(project_dir)}),
                ToolTask(name="git_diff", func=git_diff_async, kwargs={"project_dir": str(project_dir)}),
            ]

            results = await executor.execute_parallel(tasks)
            assert "git_status" in results
            assert "git_diff" in results
            assert results["git_status"]["status"] == "success"
            assert results["git_diff"]["status"] == "success"

    runner.test("Parallel git operations", test_parallel_git_operations)

    # ──────────────────────────────────────────────────────────────
    # Performance Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[PERF] Performance Tests")
    print("-" * 60)

    async def test_parallel_performance_improvement():
        """Test that parallel execution is faster than sequential."""
        executor = ParallelExecutor(max_concurrency=10, verbose=False)

        num_tasks = 10
        task_duration = 0.05

        tasks = [
            ToolTask(name=f"task{i}", func=mock_slow_task, kwargs={"delay": task_duration})
            for i in range(num_tasks)
        ]

        start_time = time.time()
        results = await executor.execute_parallel(tasks)
        elapsed = time.time() - start_time

        assert len(results) == num_tasks

        sequential_time = num_tasks * task_duration  # 0.5s
        # Parallel should be much faster
        assert elapsed < sequential_time * 0.4, f"Not fast enough: {elapsed}s vs {sequential_time}s"

    runner.test("Parallel performance improvement", test_parallel_performance_improvement)

    # ──────────────────────────────────────────────────────────────
    # Acceptance Criteria Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[AC] Acceptance Criteria Tests")
    print("-" * 60)

    async def test_ac_independent_tools_concurrent():
        """AC: Independent tools execute concurrently."""
        executor = ParallelExecutor(max_concurrency=5, verbose=False)
        tasks = [
            ToolTask(name=f"task{i}", func=mock_slow_task, kwargs={"delay": 0.12})
            for i in range(5)
        ]

        start_time = time.time()
        results = await executor.execute_parallel(tasks)
        elapsed = time.time() - start_time

        assert len(results) == 5
        for i in range(5):
            assert results[f"task{i}"]["status"] == "success"

        # Should complete in parallel (~0.12s), not sequential (0.6s)
        assert elapsed < 0.25, f"Not parallel: {elapsed}s"

    runner.test("AC: Independent tools execute concurrently", test_ac_independent_tools_concurrent)

    async def test_ac_error_isolation():
        """AC: One tool failure doesn't affect others."""
        executor = ParallelExecutor(verbose=False)
        tasks = [
            ToolTask(name="success1", func=mock_success_task, kwargs={}),
            ToolTask(name="failure", func=mock_failure_task, kwargs={}),
            ToolTask(name="success2", func=mock_success_task, kwargs={}),
            ToolTask(name="exception", func=mock_exception_task, kwargs={}),
        ]

        results = await executor.execute_parallel(tasks, fail_fast=False)

        assert len(results) == 4
        assert results["success1"]["status"] == "success"
        assert results["success2"]["status"] == "success"
        assert results["failure"]["status"] == "failed"
        assert results["exception"]["status"] == "failed"

    runner.test("AC: Error isolation works", test_ac_error_isolation)

    async def test_ac_50_percent_speedup():
        """AC: 50% faster execution (2x speedup)."""
        num_operations = 6
        operation_time = 0.08

        sequential_time = num_operations * operation_time  # 0.48s

        executor = ParallelExecutor(max_concurrency=num_operations, verbose=False)
        tasks = [
            ToolTask(name=f"op{i}", func=mock_slow_task, kwargs={"delay": operation_time})
            for i in range(num_operations)
        ]

        start_time = time.time()
        results = await executor.execute_parallel(tasks)
        parallel_time = time.time() - start_time

        assert len(results) == num_operations

        speedup = sequential_time / parallel_time
        print(f"  → Speedup: {speedup:.2f}x (seq: {sequential_time:.2f}s, par: {parallel_time:.2f}s)")

        # Should be at least 2x faster (50% reduction = 2x speedup)
        assert speedup >= 2.0, f"Speedup too low: {speedup:.2f}x (need 2.0x+)"

    runner.test("AC: 50%+ faster execution", test_ac_50_percent_speedup)

    return runner.summary()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
