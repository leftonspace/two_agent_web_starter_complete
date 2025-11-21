"""
Tests for Employee AI Pool Management.

PHASE 7C.1: Tests for multi-agent parallelism with employee pool.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from agent.execution.employee_pool import (
    EmployeePool,
    EmployeeSpecialty,
    EmployeeStatus,
    EmployeeWorker
)


# ══════════════════════════════════════════════════════════════════════
# Pool Initialization Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_pool_initialization():
    """Test pool initializes with correct number of workers"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock, pool_size=5)

    await pool.initialize()

    assert len(pool.workers) == 5
    assert pool.pool_size == 5
    assert pool._running is True

    # Check specialty distribution
    specialties = [w.specialty for w in pool.workers.values()]
    assert EmployeeSpecialty.CODING in specialties
    assert EmployeeSpecialty.DOCUMENTS in specialties
    assert EmployeeSpecialty.DATA_ANALYSIS in specialties

    # All workers should be idle
    for worker in pool.workers.values():
        assert worker.status == EmployeeStatus.IDLE

    await pool.shutdown()


@pytest.mark.asyncio
async def test_pool_custom_size():
    """Test pool with custom size"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock, pool_size=3)

    await pool.initialize()

    assert len(pool.workers) == 3

    await pool.shutdown()


@pytest.mark.asyncio
async def test_worker_specialty_distribution():
    """Test workers distributed evenly across specialties"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock, pool_size=10)

    await pool.initialize()

    distribution = pool._get_specialty_distribution()

    # Each specialty should have 2 workers (10 workers / 5 specialties)
    assert distribution[EmployeeSpecialty.CODING.value] == 2
    assert distribution[EmployeeSpecialty.DOCUMENTS.value] == 2
    assert distribution[EmployeeSpecialty.DATA_ANALYSIS.value] == 2
    assert distribution[EmployeeSpecialty.COMMUNICATIONS.value] == 2
    assert distribution[EmployeeSpecialty.GENERAL.value] == 2

    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Task Assignment Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_task_assignment_to_idle_worker():
    """Test task assigned to idle worker"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Task completed successfully")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    result = await pool.assign_task(
        "Write a simple function",
        specialty="coding"
    )

    assert result["success"] is True
    assert "result" in result
    assert result["specialty"] == "coding"

    await pool.shutdown()


@pytest.mark.asyncio
async def test_specialty_matching():
    """Test task assigned to worker with matching specialty"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Document created")

    pool = EmployeePool(llm_mock, pool_size=5)
    await pool.initialize()

    # Find the documents worker
    docs_worker = None
    for worker in pool.workers.values():
        if worker.specialty == EmployeeSpecialty.DOCUMENTS:
            docs_worker = worker
            break

    result = await pool.assign_task(
        "Write a report about sales",
        specialty="documents"
    )

    assert result["success"] is True
    assert result["specialty"] == "documents"
    # Worker should have completed one task
    assert docs_worker.tasks_completed == 1

    await pool.shutdown()


@pytest.mark.asyncio
async def test_auto_specialty_detection():
    """Test automatic specialty detection from task description"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Code written")

    pool = EmployeePool(llm_mock, pool_size=5)
    await pool.initialize()

    # Coding task
    result = await pool.assign_task("Write a Python function to calculate factorial")
    assert result["success"] is True
    assert result["specialty"] == "coding"

    # Document task
    result = await pool.assign_task("Write a memo about the meeting")
    assert result["success"] is True
    assert result["specialty"] == "documents"

    # Data analysis task
    result = await pool.assign_task("Analyze sales data and create a chart")
    assert result["success"] is True
    assert result["specialty"] == "data_analysis"

    await pool.shutdown()


@pytest.mark.asyncio
async def test_find_best_worker():
    """Test worker selection logic"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock, pool_size=5)
    await pool.initialize()

    # Should find coding worker
    worker = pool._find_best_worker(EmployeeSpecialty.CODING)
    assert worker is not None
    assert worker.specialty == EmployeeSpecialty.CODING

    # Mark all coding workers busy
    for w in pool.workers.values():
        if w.specialty == EmployeeSpecialty.CODING:
            w.status = EmployeeStatus.BUSY

    # Should find general worker as fallback
    worker = pool._find_best_worker(EmployeeSpecialty.CODING)
    assert worker is not None
    # Should be either GENERAL or another specialty
    assert worker.status == EmployeeStatus.IDLE

    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Parallel Execution Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_batch_execution():
    """Test parallel batch execution"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Task completed")

    pool = EmployeePool(llm_mock, pool_size=5)
    await pool.initialize()

    tasks = [
        {"description": "Task 1", "specialty": "coding"},
        {"description": "Task 2", "specialty": "documents"},
        {"description": "Task 3", "specialty": "data_analysis"},
        {"description": "Task 4", "specialty": "communications"},
        {"description": "Task 5", "specialty": "general"}
    ]

    results = await pool.execute_batch(tasks)

    assert len(results) == 5
    assert all(r["success"] for r in results)
    assert pool.total_tasks_processed == 5

    await pool.shutdown()


@pytest.mark.asyncio
async def test_concurrent_task_execution():
    """Test multiple tasks execute concurrently"""
    llm_mock = Mock()

    # Simulate slow execution
    async def slow_chat(*args, **kwargs):
        await asyncio.sleep(0.1)
        return "Result"

    llm_mock.chat = slow_chat

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    start_time = datetime.now()

    # Execute 3 tasks in parallel
    results = await pool.execute_batch([
        {"description": "Task 1"},
        {"description": "Task 2"},
        {"description": "Task 3"}
    ])

    execution_time = (datetime.now() - start_time).total_seconds()

    # Should complete in ~0.1s (parallel) not 0.3s (sequential)
    assert execution_time < 0.25  # Allow some overhead
    assert len(results) == 3
    assert all(r["success"] for r in results)

    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Queueing Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_task_queueing_when_all_busy():
    """Test tasks queue when all workers busy"""
    llm_mock = Mock()

    # Create a slow task to keep workers busy
    async def slow_chat(*args, **kwargs):
        await asyncio.sleep(0.3)
        return "Result"

    llm_mock.chat = slow_chat

    pool = EmployeePool(llm_mock, pool_size=2)
    await pool.initialize()

    # Start 2 tasks to fill pool
    task1 = asyncio.create_task(pool.assign_task("Task 1"))
    task2 = asyncio.create_task(pool.assign_task("Task 2"))

    # Wait a moment for workers to be assigned
    await asyncio.sleep(0.05)

    # This task should be queued
    task3 = asyncio.create_task(pool.assign_task("Task 3"))

    # Wait a moment for task to be queued
    await asyncio.sleep(0.05)

    # Queue should have 1 task
    assert pool.task_queue.qsize() == 1

    # Wait for all to complete
    results = await asyncio.gather(task1, task2, task3)

    assert all(r["success"] for r in results)
    assert pool.total_tasks_processed == 3

    await pool.shutdown()


@pytest.mark.asyncio
async def test_queue_full_rejection():
    """Test task rejected when queue is full"""
    llm_mock = Mock()

    async def never_complete(*args, **kwargs):
        await asyncio.sleep(100)  # Never completes
        return "Result"

    llm_mock.chat = never_complete

    pool = EmployeePool(llm_mock, pool_size=1, max_queue_size=2)
    await pool.initialize()

    # Fill the worker
    task1 = asyncio.create_task(pool.assign_task("Task 1"))
    await asyncio.sleep(0.05)

    # Fill the queue
    task2 = asyncio.create_task(pool.assign_task("Task 2"))
    task3 = asyncio.create_task(pool.assign_task("Task 3"))
    await asyncio.sleep(0.05)

    # This should be rejected (queue full)
    result = await pool.assign_task("Task 4")

    assert result["success"] is False
    assert "queue full" in result["error"].lower()

    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Statistics and Status Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_worker_statistics():
    """Test worker statistics tracking"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    # Execute some tasks
    await pool.assign_task("Task 1", specialty="coding")
    await pool.assign_task("Task 2", specialty="coding")

    # Check worker stats
    coding_worker = None
    for worker in pool.workers.values():
        if worker.specialty == EmployeeSpecialty.CODING:
            coding_worker = worker
            break

    assert coding_worker.tasks_completed == 2
    assert coding_worker.total_execution_time > 0
    assert coding_worker.error_count == 0

    await pool.shutdown()


@pytest.mark.asyncio
async def test_pool_status():
    """Test get_pool_status returns comprehensive info"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="Done")

    pool = EmployeePool(llm_mock, pool_size=5)
    await pool.initialize()

    # Execute some tasks
    await pool.execute_batch([
        {"description": "Task 1"},
        {"description": "Task 2"},
        {"description": "Task 3"}
    ])

    status = pool.get_pool_status()

    assert status["pool_size"] == 5
    assert status["total_tasks_processed"] == 3
    assert status["total_errors"] == 0
    assert status["workers_by_status"]["idle"] == 5
    assert status["workers_by_status"]["busy"] == 0
    assert len(status["workers"]) == 5
    assert "success_rate" in status

    await pool.shutdown()


@pytest.mark.asyncio
async def test_error_tracking():
    """Test error tracking in workers"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(side_effect=Exception("Task failed"))

    pool = EmployeePool(llm_mock, pool_size=3)
    await pool.initialize()

    result = await pool.assign_task("Failing task")

    assert result["success"] is False
    assert "error" in result
    assert pool.total_errors == 1

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

    # Execute 9 tasks (should distribute 3 per worker)
    tasks = [{"description": f"Task {i}"} for i in range(9)]
    await pool.execute_batch(tasks)

    # Check distribution
    completion_counts = [w.tasks_completed for w in pool.workers.values()]

    # All workers should have completed tasks
    assert all(count > 0 for count in completion_counts)

    # Distribution should be relatively even (within 2 tasks)
    assert max(completion_counts) - min(completion_counts) <= 2

    await pool.shutdown()


# ══════════════════════════════════════════════════════════════════════
# Specialty Detection Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_specialty_detection_coding():
    """Test coding tasks detected correctly"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock)

    specialty = await pool._determine_specialty("Write code to implement a function")
    assert specialty == EmployeeSpecialty.CODING

    specialty = await pool._determine_specialty("Debug the program")
    assert specialty == EmployeeSpecialty.CODING


@pytest.mark.asyncio
async def test_specialty_detection_documents():
    """Test document tasks detected correctly"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock)

    specialty = await pool._determine_specialty("Write a report about quarterly results")
    assert specialty == EmployeeSpecialty.DOCUMENTS

    specialty = await pool._determine_specialty("Create a memo for the team")
    assert specialty == EmployeeSpecialty.DOCUMENTS


@pytest.mark.asyncio
async def test_specialty_detection_data():
    """Test data analysis tasks detected correctly"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock)

    specialty = await pool._determine_specialty("Analyze sales data")
    assert specialty == EmployeeSpecialty.DATA_ANALYSIS

    specialty = await pool._determine_specialty("Calculate statistics for survey")
    assert specialty == EmployeeSpecialty.DATA_ANALYSIS


@pytest.mark.asyncio
async def test_specialty_detection_general():
    """Test general tasks default correctly"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock)

    specialty = await pool._determine_specialty("Just do something")
    assert specialty == EmployeeSpecialty.GENERAL


# ══════════════════════════════════════════════════════════════════════
# Shutdown Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_pool_shutdown():
    """Test pool shuts down gracefully"""
    llm_mock = Mock()
    pool = EmployeePool(llm_mock, pool_size=3)

    await pool.initialize()
    assert pool._running is True

    await pool.shutdown()
    assert pool._running is False


@pytest.mark.asyncio
async def test_shutdown_with_active_tasks():
    """Test shutdown handles active tasks"""
    llm_mock = Mock()

    async def slow_chat(*args, **kwargs):
        await asyncio.sleep(0.2)
        return "Done"

    llm_mock.chat = slow_chat

    pool = EmployeePool(llm_mock, pool_size=2)
    await pool.initialize()

    # Start task
    task = asyncio.create_task(pool.assign_task("Long task"))

    # Wait a moment
    await asyncio.sleep(0.05)

    # Shutdown (should not crash)
    await pool.shutdown()

    # Task should still complete or fail gracefully
    try:
        result = await task
        # Either succeeds or fails, but shouldn't hang
    except:
        pass  # Acceptable to fail during shutdown
