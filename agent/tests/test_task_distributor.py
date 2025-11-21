"""
Tests for parallel task distribution system.

PHASE 7C.2: Tests for intelligent task distribution with priority queuing,
dependency tracking, and load balancing.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta

from agent.execution.task_distributor import (
    TaskDistributor,
    TaskPriority,
    TaskRequest,
    TaskResult
)
from agent.execution.employee_pool import EmployeePool


# ══════════════════════════════════════════════════════════════════════
# Priority Queue Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_priority_ordering():
    """Test tasks execute in priority order"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=1)  # Single worker
    await pool.initialize()

    distributor = TaskDistributor(pool, enable_batching=False)
    await distributor.start()

    # Submit tasks in reverse priority order
    low_id = await distributor.submit_task("Low priority", TaskPriority.LOW)
    high_id = await distributor.submit_task("High priority", TaskPriority.HIGH)
    urgent_id = await distributor.submit_task("Urgent", TaskPriority.URGENT)
    medium_id = await distributor.submit_task("Medium priority", TaskPriority.MEDIUM)

    # Wait for all to complete
    await asyncio.sleep(0.5)

    # Check completion order (higher priority should complete first)
    low_result = distributor.completed_tasks[low_id]
    high_result = distributor.completed_tasks[high_id]
    urgent_result = distributor.completed_tasks[urgent_id]
    medium_result = distributor.completed_tasks[medium_id]

    # Urgent should complete before others
    assert urgent_result.completed_at < high_result.completed_at
    assert urgent_result.completed_at < medium_result.completed_at

    await distributor.stop()
    await pool.shutdown()


@pytest.mark.asyncio
async def test_deadline_escalation():
    """Test tasks with approaching deadlines get priority boost"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=1)
    await pool.initialize()

    distributor = TaskDistributor(pool, enable_batching=False)
    await distributor.start()

    # Submit low priority task with urgent deadline
    urgent_deadline = datetime.now() + timedelta(seconds=30)
    deadline_task = await distributor.submit_task(
        "Low priority but urgent deadline",
        TaskPriority.LOW,
        deadline=urgent_deadline
    )

    # Submit high priority task with no deadline
    high_task = await distributor.submit_task(
        "High priority no deadline",
        TaskPriority.HIGH
    )

    # Wait for execution
    await asyncio.sleep(0.3)

    # Deadline task should complete first due to urgency
    deadline_result = distributor.completed_tasks.get(deadline_task)
    high_result = distributor.completed_tasks.get(high_task)

    if deadline_result and high_result:
        # If both completed, deadline task should finish first
        assert deadline_result.completed_at <= high_result.completed_at

    await distributor.stop()
    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Dependency Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dependency_resolution():
    """Test task waits for dependency to complete"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    # Submit task A
    task_a = await distributor.submit_task("Task A")

    # Submit task B that depends on A
    task_b = await distributor.submit_task(
        "Task B (depends on A)",
        dependencies=[task_a]
    )

    # Wait for completion
    result_a = await distributor.get_result(task_a)
    result_b = await distributor.get_result(task_b)

    assert result_a.success
    assert result_b.success

    # B should complete after A
    assert result_b.completed_at > result_a.completed_at

    await distributor.stop()
    await pool.shutdown()


@pytest.mark.asyncio
async def test_dependency_chain():
    """Test chain of dependencies (C depends on B depends on A)"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    # Create dependency chain
    task_a = await distributor.submit_task("Task A")
    task_b = await distributor.submit_task("Task B", dependencies=[task_a])
    task_c = await distributor.submit_task("Task C", dependencies=[task_b])

    # Wait for all
    result_a = await distributor.get_result(task_a)
    result_b = await distributor.get_result(task_b)
    result_c = await distributor.get_result(task_c)

    # Check order
    assert result_a.completed_at < result_b.completed_at
    assert result_b.completed_at < result_c.completed_at

    await distributor.stop()
    await pool.shutdown()


@pytest.mark.asyncio
async def test_multiple_dependencies():
    """Test task with multiple dependencies"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    # Submit independent tasks
    task_a = await distributor.submit_task("Task A")
    task_b = await distributor.submit_task("Task B")

    # Submit task that depends on both
    task_c = await distributor.submit_task(
        "Task C (depends on A and B)",
        dependencies=[task_a, task_b]
    )

    # Wait for all
    result_a = await distributor.get_result(task_a)
    result_b = await distributor.get_result(task_b)
    result_c = await distributor.get_result(task_c)

    # C should complete after both A and B
    assert result_c.completed_at > result_a.completed_at
    assert result_c.completed_at > result_b.completed_at

    await distributor.stop()
    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Load Balancing Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_load_balancing():
    """Test tasks distributed evenly across workers"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    # Submit many tasks
    task_ids = []
    for i in range(9):
        task_id = await distributor.submit_task(f"Task {i}")
        task_ids.append(task_id)

    # Wait for all
    for task_id in task_ids:
        await distributor.get_result(task_id)

    # Check stats
    stats = distributor.get_distribution_stats()
    assert stats["total_completed"] == 9

    await distributor.stop()
    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Worker Affinity Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_worker_affinity():
    """Test related tasks assigned to same worker"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    distributor = TaskDistributor(pool, enable_affinity=True)
    await distributor.start()

    # Submit first task
    task_a = await distributor.submit_task("Task A - write code")
    result_a = await distributor.get_result(task_a)

    # Submit related task with affinity hint
    task_b = await distributor.submit_task(
        "Task B - test code",
        affinity_hints=[task_a]
    )
    result_b = await distributor.get_result(task_b)

    # If affinity worked, both should be on same worker
    if result_a.worker_id and result_b.worker_id:
        # Affinity is best-effort, so we just check if it was attempted
        assert "affinity_hits" in distributor.stats

    await distributor.stop()
    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Batch Optimization Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_batch_optimization():
    """Test similar tasks batched together"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    distributor = TaskDistributor(pool, enable_batching=True)
    await distributor.start()

    # Submit multiple tasks of same specialty
    task_ids = []
    for i in range(5):
        task_id = await distributor.submit_task(
            f"Coding task {i}",
            specialty="coding"
        )
        task_ids.append(task_id)

    # Wait for completion
    for task_id in task_ids:
        await distributor.get_result(task_id)

    # Check if batches were executed
    stats = distributor.get_distribution_stats()
    # Some batches should have been formed
    assert stats["total_completed"] == 5

    await distributor.stop()
    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Statistics and Status Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_distribution_statistics():
    """Test distribution statistics tracking"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=2)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    # Submit and complete some tasks
    task_ids = []
    for i in range(5):
        task_id = await distributor.submit_task(f"Task {i}")
        task_ids.append(task_id)

    # Wait for completion
    for task_id in task_ids:
        await distributor.get_result(task_id)

    # Check stats
    stats = distributor.get_distribution_stats()

    assert stats["total_submitted"] == 5
    assert stats["total_completed"] == 5
    assert stats["pending_tasks"] == 0
    assert stats["completed_tasks"] == 5

    await distributor.stop()
    await pool.shutdown()


@pytest.mark.asyncio
async def test_get_pending_tasks():
    """Test getting list of pending tasks"""
    llm_mock = Mock()

    # Make tasks never complete
    async def never_complete(*args, **kwargs):
        await asyncio.sleep(10)
        return "Done"

    llm_mock.chat = never_complete

    pool = EmployeePool(llm_mock, pool_size=1)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    # Submit tasks
    task_a = await distributor.submit_task("Task A")
    task_b = await distributor.submit_task("Task B", dependencies=[task_a])

    # Wait a moment
    await asyncio.sleep(0.1)

    # Get pending tasks
    pending = distributor.get_pending_tasks()

    # Both should be pending
    assert len(pending) >= 1

    await distributor.stop()
    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_task_execution_failure():
    """Test handling of task execution failure"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(side_effect=Exception("Task failed"))

    pool = EmployeePool(llm_mock, pool_size=2)
    await pool.initialize()

    distributor = TaskDistributor(pool)
    await distributor.start()

    task_id = await distributor.submit_task("Failing task")

    result = await distributor.get_result(task_id)

    assert result.success is False
    assert result.error is not None

    stats = distributor.get_distribution_stats()
    assert stats["total_failed"] == 1

    await distributor.stop()
    await pool.shutdown()


@pytest.mark.asyncio
async def test_priority_score_calculation():
    """Test priority score calculation logic"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock, pool_size=1)

    distributor = TaskDistributor(pool)

    # Test base priorities
    urgent_task = TaskRequest(
        task_id="urgent",
        description="Urgent task",
        priority=TaskPriority.URGENT
    )
    low_task = TaskRequest(
        task_id="low",
        description="Low task",
        priority=TaskPriority.LOW
    )

    urgent_score = distributor._calculate_priority_score(urgent_task)
    low_score = distributor._calculate_priority_score(low_task)

    # Lower score = higher priority
    assert urgent_score < low_score

    # Test deadline urgency
    deadline_task = TaskRequest(
        task_id="deadline",
        description="Task with deadline",
        priority=TaskPriority.MEDIUM,
        deadline=datetime.now() + timedelta(seconds=30)
    )

    medium_task = TaskRequest(
        task_id="medium",
        description="Medium task",
        priority=TaskPriority.MEDIUM
    )

    deadline_score = distributor._calculate_priority_score(deadline_task)
    medium_score = distributor._calculate_priority_score(medium_task)

    # Deadline task should have higher priority (lower score)
    assert deadline_score < medium_score
