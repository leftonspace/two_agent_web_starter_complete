"""
Tests for task router.

PHASE 7B.3: Tests for task routing logic with retry and escalation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from agent.execution.task_router import TaskRouter, TaskStatus
from agent.execution.strategy_decider import ExecutionMode, ExecutionStrategy


# ══════════════════════════════════════════════════════════════════════
# Basic Routing Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_simple_task_direct_routing():
    """Test simple task routes to direct executor"""
    llm_mock = Mock()

    # Mock strategy decision
    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Simple task",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)
    router.direct_executor.execute = AsyncMock(return_value={
        "success": True,
        "result": "Task completed"
    })

    result = await router.route_task("Simple task")

    assert result["success"] is True
    assert router.direct_executor.execute.called
    assert result["result"] == "Task completed"


@pytest.mark.asyncio
async def test_task_id_generation():
    """Test automatic task ID generation"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Test",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)
    router.direct_executor.execute = AsyncMock(return_value={
        "success": True,
        "result": "Done"
    })

    # Route without task_id
    await router.route_task("Test task")

    # Should have created a task
    assert len(router.active_tasks) == 1
    task_id = list(router.active_tasks.keys())[0]
    assert task_id.startswith("task_")


@pytest.mark.asyncio
async def test_task_status_tracking():
    """Test task status updates throughout lifecycle"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Test",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)
    router.direct_executor.execute = AsyncMock(return_value={
        "success": True,
        "result": "Done"
    })

    result = await router.route_task("Test", task_id="test123")

    # Check final status
    status = router.get_task_status("test123")
    assert status is not None
    assert status["status"] == TaskStatus.COMPLETED.value
    assert "completed_at" in status


# ══════════════════════════════════════════════════════════════════════
# Retry and Escalation Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_retry_escalation():
    """Test failed task escalates to higher mode on retry"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Simple task",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)

    # First attempt (DIRECT) fails
    router.direct_executor.execute = AsyncMock(return_value={
        "success": False,
        "error": "Direct execution failed"
    })

    # Second attempt (REVIEWED) succeeds
    router._execute_reviewed_mode = AsyncMock(return_value={
        "success": True,
        "result": "Completed in reviewed mode",
        "mode": "reviewed"
    })

    result = await router.route_task("Task that needs escalation")

    assert result["success"] is True
    assert result["mode"] == "reviewed"
    assert router._execute_reviewed_mode.called


@pytest.mark.asyncio
async def test_retry_without_escalation():
    """Test retry without escalation when disabled"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Test",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.retry_escalation = False  # Disable escalation
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)

    # All attempts fail in DIRECT mode
    router.direct_executor.execute = AsyncMock(return_value={
        "success": False,
        "error": "Failed"
    })

    result = await router.route_task("Failing task")

    assert result["success"] is False
    assert "Failed after" in result["error"]
    # Should have tried direct mode multiple times
    assert router.direct_executor.execute.call_count == router.max_retries


@pytest.mark.asyncio
async def test_escalation_levels():
    """Test escalation through all levels"""
    llm_mock = Mock()

    router = TaskRouter(llm_mock)

    # Test escalation path
    assert router._escalate_mode(ExecutionMode.DIRECT) == ExecutionMode.REVIEWED
    assert router._escalate_mode(ExecutionMode.REVIEWED) == ExecutionMode.FULL_LOOP
    assert router._escalate_mode(ExecutionMode.FULL_LOOP) == ExecutionMode.FULL_LOOP  # No higher


# ══════════════════════════════════════════════════════════════════════
# Human Approval Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_human_approval_required():
    """Test high-risk task requires human approval"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.HUMAN_APPROVAL,
        rationale="High risk task",
        estimated_duration_seconds=60,
        estimated_cost_usd=1.0,
        risk_level="high",
        requires_approval=True,
        suggested_timeout_seconds=300
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)

    result = await router.route_task("Deploy to production", task_id="deploy1")

    assert result["success"] is False
    assert result["status"] == "requires_approval"
    assert "approval" in result["message"].lower()
    assert len(router.list_pending_approvals()) == 1


@pytest.mark.asyncio
async def test_approve_and_execute():
    """Test executing task after human approval"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.HUMAN_APPROVAL,
        rationale="High risk",
        estimated_duration_seconds=60,
        estimated_cost_usd=1.0,
        risk_level="high",
        requires_approval=True,
        suggested_timeout_seconds=300
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)
    router._execute_full_loop = AsyncMock(return_value={
        "success": True,
        "result": "Completed",
        "mode": "full_loop"
    })

    # Request approval
    result = await router.route_task("Risky task", task_id="test_task")
    assert result["status"] == "requires_approval"

    # Approve and execute
    result = await router.approve_and_execute("test_task", approved=True)
    assert result["success"] is True
    assert router._execute_full_loop.called


@pytest.mark.asyncio
async def test_reject_task():
    """Test rejecting task requiring approval"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.HUMAN_APPROVAL,
        rationale="High risk",
        estimated_duration_seconds=60,
        estimated_cost_usd=1.0,
        risk_level="high",
        requires_approval=True,
        suggested_timeout_seconds=300
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)

    # Request approval
    result = await router.route_task("Risky task", task_id="reject_test")
    assert result["status"] == "requires_approval"

    # Reject
    result = await router.approve_and_execute("reject_test", approved=False)
    assert result["success"] is False
    assert "rejected" in result["message"].lower()

    # Check task status
    status = router.get_task_status("reject_test")
    assert status["status"] == TaskStatus.FAILED.value


@pytest.mark.asyncio
async def test_approve_unknown_task():
    """Test approving unknown task ID"""
    llm_mock = Mock()
    router = TaskRouter(llm_mock)

    result = await router.approve_and_execute("unknown_id", approved=True)

    assert result["success"] is False
    assert "Unknown task ID" in result["error"]


@pytest.mark.asyncio
async def test_approve_non_pending_task():
    """Test approving task not waiting for approval"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Simple",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)
    router.direct_executor.execute = AsyncMock(return_value={
        "success": True,
        "result": "Done"
    })

    # Execute task normally
    await router.route_task("Simple task", task_id="simple1")

    # Try to approve it
    result = await router.approve_and_execute("simple1", approved=True)

    assert result["success"] is False
    assert "not waiting for approval" in result["error"].lower()


# ══════════════════════════════════════════════════════════════════════
# Task Management Tests
# ══════════════════════════════════════════════════════════════════════


def test_list_pending_approvals():
    """Test listing tasks pending approval"""
    llm_mock = Mock()
    router = TaskRouter(llm_mock)

    # Manually add tasks
    router.active_tasks["task1"] = {
        "description": "Deploy app",
        "status": TaskStatus.REQUIRES_APPROVAL,
        "started_at": datetime.now(),
        "strategy": {"mode": "human_approval"}
    }
    router.active_tasks["task2"] = {
        "description": "Query DB",
        "status": TaskStatus.COMPLETED,
        "started_at": datetime.now()
    }

    pending = router.list_pending_approvals()

    assert len(pending) == 1
    assert pending[0]["task_id"] == "task1"


def test_get_active_tasks():
    """Test getting active tasks"""
    llm_mock = Mock()
    router = TaskRouter(llm_mock)

    # Add various tasks
    router.active_tasks["task1"] = {
        "description": "Task 1",
        "status": TaskStatus.EXECUTING,
        "started_at": datetime.now(),
        "attempts": 1
    }
    router.active_tasks["task2"] = {
        "description": "Task 2",
        "status": TaskStatus.ROUTING,
        "started_at": datetime.now(),
        "attempts": 0
    }
    router.active_tasks["task3"] = {
        "description": "Task 3",
        "status": TaskStatus.COMPLETED,
        "started_at": datetime.now()
    }

    active = router.get_active_tasks()

    assert len(active) == 2
    task_ids = [t["task_id"] for t in active]
    assert "task1" in task_ids
    assert "task2" in task_ids


def test_clear_completed_tasks():
    """Test clearing old completed tasks"""
    llm_mock = Mock()
    router = TaskRouter(llm_mock)

    # Add many completed tasks
    for i in range(20):
        router.active_tasks[f"task{i}"] = {
            "description": f"Task {i}",
            "status": TaskStatus.COMPLETED,
            "started_at": datetime.now(),
            "completed_at": datetime.now()
        }

    router.clear_completed_tasks(keep_recent=5)

    # Should keep only 5 most recent
    assert len(router.active_tasks) == 5


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_strategy_decision_failure():
    """Test handling of strategy decision failure"""
    llm_mock = Mock()
    router = TaskRouter(llm_mock)

    # Strategy decision fails
    router.strategy_decider.decide_strategy = AsyncMock(
        side_effect=Exception("Strategy error")
    )

    result = await router.route_task("Task", task_id="error_test")

    assert result["success"] is False
    assert "error" in result
    assert router.get_task_status("error_test")["status"] == TaskStatus.FAILED.value


@pytest.mark.asyncio
async def test_execution_exception():
    """Test handling of execution exception"""
    llm_mock = Mock()

    strategy = ExecutionStrategy(
        mode=ExecutionMode.DIRECT,
        rationale="Test",
        estimated_duration_seconds=10,
        estimated_cost_usd=0.05,
        risk_level="low",
        requires_approval=False,
        suggested_timeout_seconds=30
    )

    router = TaskRouter(llm_mock)
    router.strategy_decider.decide_strategy = AsyncMock(return_value=strategy)
    router.direct_executor.execute = AsyncMock(
        side_effect=Exception("Execution error")
    )

    result = await router.route_task("Failing task")

    assert result["success"] is False
    assert "Failed after" in result["error"]


def test_get_task_status_unknown():
    """Test getting status of unknown task"""
    llm_mock = Mock()
    router = TaskRouter(llm_mock)

    status = router.get_task_status("unknown_task")

    assert status is None
