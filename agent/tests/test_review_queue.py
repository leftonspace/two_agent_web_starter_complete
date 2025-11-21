"""
Tests for Supervisor review queue system.

PHASE 7C.3: Tests for review queue with batching, quality gates, and auto-approval.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agent.execution.review_queue import (
    ReviewQueueManager,
    RiskLevel,
    WorkType,
    ReviewStatus,
    ReviewItem,
    QualityGateResult
)


# ══════════════════════════════════════════════════════════════════════
# Basic Queue Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_submit_for_review():
    """Test submitting work for review"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Write function",
        result={"code": "def foo(): pass"},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.CODE
    )

    assert work_id.startswith("work_")
    assert queue.metrics["total_submitted"] == 1

    await queue.stop()


@pytest.mark.asyncio
async def test_queue_processing():
    """Test queue processes submitted work"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "approved": True,
        "feedback": "Good work"
    })

    queue = ReviewQueueManager(llm_mock, enable_auto_approval=False)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Task",
        result={"data": "result"},
        risk_level=RiskLevel.MEDIUM,
        work_type=WorkType.DATA_ANALYSIS
    )

    # Wait for processing
    result = await queue.get_review_result(work_id)

    assert result.work_id == work_id
    assert result.status in [ReviewStatus.APPROVED, ReviewStatus.AUTO_APPROVED]

    await queue.stop()


# ══════════════════════════════════════════════════════════════════════
# Quality Gate Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_quality_gates_correctness():
    """Test correctness quality gate"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)

    # Correct result
    item = ReviewItem(
        work_id="test1",
        employee_id="emp1",
        task_description="Task",
        result={"success": True, "data": "result"},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.OTHER
    )

    gates = await queue._run_quality_gates(item)
    assert gates.correctness_passed is True

    # Failed result
    item2 = ReviewItem(
        work_id="test2",
        employee_id="emp1",
        task_description="Task",
        result={"error": "Failed"},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.OTHER
    )

    gates2 = await queue._run_quality_gates(item2)
    assert gates2.correctness_passed is False


@pytest.mark.asyncio
async def test_quality_gates_safety():
    """Test safety quality gate"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)

    # Unsafe database operation
    unsafe_item = ReviewItem(
        work_id="test1",
        employee_id="emp1",
        task_description="Query database",
        result={"query": "DROP TABLE users"},
        risk_level=RiskLevel.MEDIUM,
        work_type=WorkType.DATABASE_QUERY
    )

    gates = await queue._run_quality_gates(unsafe_item)
    assert gates.safety_passed is False

    # Safe database operation
    safe_item = ReviewItem(
        work_id="test2",
        employee_id="emp1",
        task_description="Query database",
        result={"query": "SELECT * FROM users"},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.DATABASE_QUERY
    )

    gates2 = await queue._run_quality_gates(safe_item)
    assert gates2.safety_passed is True


@pytest.mark.asyncio
async def test_quality_gates_performance():
    """Test performance quality gate"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)

    # Slow execution
    slow_item = ReviewItem(
        work_id="test1",
        employee_id="emp1",
        task_description="Process data",
        result={"execution_time": 35.0},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.DATA_ANALYSIS
    )

    gates = await queue._run_quality_gates(slow_item)
    assert gates.performance_passed is False

    # Fast execution
    fast_item = ReviewItem(
        work_id="test2",
        employee_id="emp1",
        task_description="Process data",
        result={"execution_time": 2.0},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.DATA_ANALYSIS
    )

    gates2 = await queue._run_quality_gates(fast_item)
    assert gates2.performance_passed is True


# ══════════════════════════════════════════════════════════════════════
# Auto-Approval Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_auto_approval_low_risk():
    """Test auto-approval for low-risk work"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock, enable_auto_approval=True)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Simple task",
        result={"success": True, "data": "result"},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.OTHER
    )

    # Wait for processing
    result = await queue.get_review_result(work_id)

    assert result.status == ReviewStatus.AUTO_APPROVED
    assert result.approved is True
    assert queue.metrics["auto_approved"] == 1

    await queue.stop()


@pytest.mark.asyncio
async def test_no_auto_approval_high_risk():
    """Test high-risk work not auto-approved"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "approved": True,
        "feedback": "Reviewed"
    })

    queue = ReviewQueueManager(llm_mock, enable_auto_approval=True)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Risky task",
        result={"success": True, "data": "result"},
        risk_level=RiskLevel.HIGH,
        work_type=WorkType.OTHER
    )

    # Wait for processing
    result = await queue.get_review_result(work_id)

    # Should NOT be auto-approved
    assert result.status != ReviewStatus.AUTO_APPROVED
    assert queue.metrics["auto_approved"] == 0

    await queue.stop()


@pytest.mark.asyncio
async def test_auto_approval_disabled():
    """Test auto-approval when disabled"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "approved": True,
        "feedback": "Good"
    })

    queue = ReviewQueueManager(llm_mock, enable_auto_approval=False)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Task",
        result={"success": True},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.OTHER
    )

    result = await queue.get_review_result(work_id)

    # Should be manually reviewed even if low risk
    assert result.status == ReviewStatus.APPROVED
    assert queue.metrics["auto_approved"] == 0
    assert queue.metrics["manual_approved"] == 1

    await queue.stop()


# ══════════════════════════════════════════════════════════════════════
# Escalation Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_escalation_critical_risk():
    """Test critical risk work escalated to Manager"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Critical operation",
        result={"data": "result"},
        risk_level=RiskLevel.CRITICAL,
        work_type=WorkType.OTHER
    )

    result = await queue.get_review_result(work_id)

    assert result.status == ReviewStatus.ESCALATED
    assert result.reviewer == "manager"
    assert queue.metrics["escalated"] == 1

    await queue.stop()


@pytest.mark.asyncio
async def test_escalation_quality_failures():
    """Test work with quality failures escalated"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)
    await queue.start()

    # Submit work that will fail quality gates
    work_id = await queue.submit_for_review(
        employee_id="employee_1",
        task_description="Query",
        result={"query": "DROP TABLE users", "error": "Failed"},
        risk_level=RiskLevel.MEDIUM,
        work_type=WorkType.DATABASE_QUERY
    )

    result = await queue.get_review_result(work_id)

    # Should be escalated due to multiple quality failures
    assert result.status == ReviewStatus.ESCALATED

    await queue.stop()


# ══════════════════════════════════════════════════════════════════════
# Batch Processing Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_batch_processing():
    """Test similar work batched together"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "approved": True,
        "feedback": "Good"
    })

    queue = ReviewQueueManager(llm_mock, enable_batching=True, enable_auto_approval=False)
    await queue.start()

    # Submit multiple CODE items
    work_ids = []
    for i in range(3):
        work_id = await queue.submit_for_review(
            employee_id=f"employee_{i}",
            task_description=f"Code task {i}",
            result={"code": f"code{i}"},
            risk_level=RiskLevel.MEDIUM,
            work_type=WorkType.CODE
        )
        work_ids.append(work_id)

    # Wait for all
    for work_id in work_ids:
        await queue.get_review_result(work_id)

    # Should have processed as batch
    assert queue.metrics["total_reviewed"] == 3

    await queue.stop()


# ══════════════════════════════════════════════════════════════════════
# Metrics Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_review_metrics():
    """Test review metrics tracking"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "approved": True,
        "feedback": "Good"
    })

    queue = ReviewQueueManager(llm_mock)
    await queue.start()

    # Submit various work items
    await queue.submit_for_review(
        employee_id="emp1",
        task_description="Task 1",
        result={"success": True},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.OTHER
    )

    await queue.submit_for_review(
        employee_id="emp2",
        task_description="Task 2",
        result={"data": "result"},
        risk_level=RiskLevel.CRITICAL,
        work_type=WorkType.OTHER
    )

    # Wait a moment for processing
    await asyncio.sleep(0.3)

    metrics = queue.get_review_metrics()

    assert metrics["total_submitted"] >= 2
    assert metrics["total_reviewed"] >= 1
    assert "approval_rate" in metrics
    assert "avg_review_time" in metrics

    await queue.stop()


@pytest.mark.asyncio
async def test_queue_status():
    """Test queue status reporting"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)
    await queue.start()

    # Submit work
    await queue.submit_for_review(
        employee_id="emp1",
        task_description="Task",
        result={"data": "result"},
        risk_level=RiskLevel.LOW,
        work_type=WorkType.OTHER
    )

    status = queue.get_queue_status()

    assert "queue_length" in status
    assert "completed_reviews" in status
    assert "pending_reviews" in status

    await queue.stop()


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_review_error_handling():
    """Test handling of review errors"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(side_effect=Exception("Review failed"))

    queue = ReviewQueueManager(llm_mock, enable_auto_approval=False)
    await queue.start()

    work_id = await queue.submit_for_review(
        employee_id="emp1",
        task_description="Task",
        result={"data": "result"},
        risk_level=RiskLevel.MEDIUM,
        work_type=WorkType.OTHER
    )

    result = await queue.get_review_result(work_id)

    # Should be rejected due to error
    assert result.status == ReviewStatus.REJECTED
    assert result.approved is False
    assert queue.metrics["rejected"] >= 1

    await queue.stop()


@pytest.mark.asyncio
async def test_unknown_work_id():
    """Test getting result for unknown work ID"""
    llm_mock = Mock()
    queue = ReviewQueueManager(llm_mock)

    with pytest.raises(ValueError, match="Unknown work ID"):
        await queue.get_review_result("nonexistent_id")
