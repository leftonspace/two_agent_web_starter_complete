"""
Tasks API Routes

View recent tasks and submit feedback.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class TaskSummary(BaseModel):
    """Summary of a task execution."""

    id: UUID = Field(..., description="Task ID")
    domain: str = Field(..., description="Task domain")
    specialist_id: Optional[UUID] = Field(default=None)
    specialist_name: Optional[str] = Field(default=None)
    request_preview: str = Field(..., description="First 200 chars of request")
    response_preview: str = Field(..., description="First 200 chars of response")
    score: Optional[float] = Field(default=None)
    model_used: str = Field(default="unknown")
    execution_time_ms: int = Field(default=0)
    cost_cad: float = Field(default=0.0)
    created_at: datetime = Field(...)
    has_feedback: bool = Field(default=False)


class TaskDetail(BaseModel):
    """Detailed task information."""

    id: UUID
    domain: str
    specialist_id: Optional[UUID]
    specialist_name: Optional[str]
    request: str
    response: str
    score: Optional[float]
    evaluation_details: Optional[Dict[str, Any]]
    model_used: str
    execution_time_ms: int
    tokens_used: int
    cost_cad: float
    created_at: datetime
    feedback: Optional[Dict[str, Any]]


class UserFeedbackRequest(BaseModel):
    """Request to submit user feedback."""

    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating 1-5 (1=poor, 5=excellent)",
    )
    feedback_type: Literal["helpful", "accurate", "fast", "creative", "other"] = Field(
        default="other",
        description="Type of feedback",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional text feedback",
    )
    would_use_again: bool = Field(
        default=True,
        description="Whether user would use this specialist again",
    )


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    status: str = Field(default="ok")
    message: str = Field(default="Feedback recorded")
    feedback_id: Optional[UUID] = Field(default=None)
    score_impact: Optional[float] = Field(
        default=None,
        description="How this feedback affected specialist score",
    )


class PendingFeedbackItem(BaseModel):
    """Task awaiting feedback."""

    task_id: UUID
    domain: str
    specialist_name: Optional[str]
    request_preview: str
    response_preview: str
    created_at: datetime
    age_minutes: int


class FeedbackStats(BaseModel):
    """Feedback statistics."""

    total_feedback: int = Field(default=0)
    positive_rate: float = Field(default=0.0, description="Rating >= 4")
    avg_rating: float = Field(default=0.0)
    pending_count: int = Field(default=0)
    feedback_by_domain: Dict[str, int] = Field(default_factory=dict)


# ============================================================================
# Router
# ============================================================================


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/recent", response_model=List[TaskSummary])
async def get_recent_tasks(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    specialist_id: Optional[UUID] = Query(None, description="Filter by specialist"),
):
    """
    Get recent tasks.

    Args:
        limit: Maximum number of tasks to return
        domain: Optional domain filter
        specialist_id: Optional specialist filter
    """
    try:
        tasks = await _get_recent_tasks(limit, domain, specialist_id)
        return tasks
    except Exception as e:
        logger.error(f"Failed to get recent tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskDetail)
async def get_task_detail(task_id: UUID):
    """
    Get detailed information about a task.

    Args:
        task_id: UUID of the task
    """
    try:
        task = await _get_task_detail(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(task_id: UUID, feedback: UserFeedbackRequest):
    """
    Submit feedback for a task.

    Args:
        task_id: UUID of the task
        feedback: User's feedback

    Feedback affects specialist scores and influences evolution.
    """
    try:
        # Verify task exists
        task = await _get_task_detail(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        # Check if feedback already submitted
        if task.feedback:
            raise HTTPException(
                status_code=409,
                detail="Feedback already submitted for this task",
            )

        # Submit feedback
        result = await _submit_feedback(task_id, task.specialist_id, feedback)

        return FeedbackResponse(
            status="ok",
            message="Feedback recorded successfully",
            feedback_id=result.get("feedback_id"),
            score_impact=result.get("score_impact"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending-feedback", response_model=List[PendingFeedbackItem])
async def get_pending_feedback(
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Get tasks awaiting user feedback.

    Returns tasks that completed but haven't received feedback yet.
    """
    try:
        return await _get_pending_feedback(limit)
    except Exception as e:
        logger.error(f"Failed to get pending feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats():
    """Get feedback statistics."""
    try:
        return await _get_feedback_stats()
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-specialist/{specialist_id}", response_model=List[TaskSummary])
async def get_tasks_by_specialist(
    specialist_id: UUID,
    limit: int = Query(20, ge=1, le=100),
):
    """Get tasks handled by a specific specialist."""
    try:
        return await _get_recent_tasks(limit, None, specialist_id)
    except Exception as e:
        logger.error(f"Failed to get specialist tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-domain/{domain}", response_model=List[TaskSummary])
async def get_tasks_by_domain(
    domain: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get tasks for a specific domain."""
    try:
        return await _get_recent_tasks(limit, domain, None)
    except Exception as e:
        logger.error(f"Failed to get domain tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================


# In-memory task storage (populated by real task executions)
_task_history: List[Dict[str, Any]] = []
_feedback_history: Dict[UUID, Dict[str, Any]] = {}


async def _get_recent_tasks(
    limit: int,
    domain: Optional[str],
    specialist_id: Optional[UUID],
) -> List[TaskSummary]:
    """Get recent tasks from storage."""
    try:
        from core.routing import get_task_router
        router = get_task_router()

        # Try to get from router history
        if hasattr(router, 'get_task_history'):
            tasks = router.get_task_history(limit=limit * 2)  # Get extra for filtering
        else:
            tasks = _task_history[-limit * 2:]

    except ImportError:
        tasks = _task_history[-limit * 2:]

    # Filter
    filtered = []
    for task in tasks:
        if domain and task.get("domain") != domain:
            continue
        if specialist_id and task.get("specialist_id") != specialist_id:
            continue
        filtered.append(task)

    # Convert to TaskSummary
    summaries = []
    for task in filtered[-limit:]:
        task_id = task.get("id") or task.get("task_id")
        if isinstance(task_id, str):
            task_id = UUID(task_id)

        summaries.append(TaskSummary(
            id=task_id,
            domain=task.get("domain", "unknown"),
            specialist_id=task.get("specialist_id"),
            specialist_name=task.get("specialist_name"),
            request_preview=task.get("request", "")[:200],
            response_preview=task.get("response", "")[:200],
            score=task.get("score"),
            model_used=task.get("model_used", "unknown"),
            execution_time_ms=task.get("execution_time_ms", 0),
            cost_cad=task.get("cost_cad", 0.0),
            created_at=task.get("created_at", datetime.utcnow()),
            has_feedback=task_id in _feedback_history,
        ))

    return summaries


async def _get_task_detail(task_id: UUID) -> Optional[TaskDetail]:
    """Get detailed task information."""
    try:
        from core.routing import get_task_router
        router = get_task_router()

        if hasattr(router, 'get_task'):
            task = router.get_task(task_id)
        else:
            task = next((t for t in _task_history if t.get("id") == task_id), None)

    except ImportError:
        task = next((t for t in _task_history if t.get("id") == task_id), None)

    if not task:
        return None

    return TaskDetail(
        id=task_id,
        domain=task.get("domain", "unknown"),
        specialist_id=task.get("specialist_id"),
        specialist_name=task.get("specialist_name"),
        request=task.get("request", ""),
        response=task.get("response", ""),
        score=task.get("score"),
        evaluation_details=task.get("evaluation_details"),
        model_used=task.get("model_used", "unknown"),
        execution_time_ms=task.get("execution_time_ms", 0),
        tokens_used=task.get("tokens_used", 0),
        cost_cad=task.get("cost_cad", 0.0),
        created_at=task.get("created_at", datetime.utcnow()),
        feedback=_feedback_history.get(task_id),
    )


async def _submit_feedback(
    task_id: UUID,
    specialist_id: Optional[UUID],
    feedback: UserFeedbackRequest,
) -> Dict[str, Any]:
    """Submit feedback and update specialist score."""
    from uuid import uuid4

    feedback_id = uuid4()
    score_impact = 0.0

    # Store feedback
    feedback_data = {
        "id": feedback_id,
        "task_id": task_id,
        "specialist_id": specialist_id,
        "rating": feedback.rating,
        "feedback_type": feedback.feedback_type,
        "comment": feedback.comment,
        "would_use_again": feedback.would_use_again,
        "created_at": datetime.utcnow(),
    }
    _feedback_history[task_id] = feedback_data

    # Calculate score impact (normalize 1-5 to 0-1)
    normalized_score = (feedback.rating - 1) / 4  # 1->0, 5->1
    score_impact = normalized_score - 0.5  # Center around 0

    # Try to update specialist score
    if specialist_id:
        try:
            from core.specialists import get_pool_manager
            pool_manager = get_pool_manager()
            specialist = pool_manager.get_specialist(specialist_id)
            if specialist and hasattr(specialist, 'record_feedback'):
                specialist.record_feedback(
                    rating=feedback.rating,
                    comment=feedback.comment,
                )
        except ImportError:
            pass

    # Try to save to database
    try:
        from database.models import UserFeedbackDB
        # Would save to database here
    except ImportError:
        pass

    return {
        "feedback_id": feedback_id,
        "score_impact": round(score_impact, 3),
    }


async def _get_pending_feedback(limit: int) -> List[PendingFeedbackItem]:
    """Get tasks awaiting feedback."""
    pending = []

    # Find tasks without feedback
    for task in _task_history[-100:]:  # Check last 100 tasks
        task_id = task.get("id")
        if task_id and task_id not in _feedback_history:
            created_at = task.get("created_at", datetime.utcnow())
            age_minutes = int((datetime.utcnow() - created_at).total_seconds() / 60)

            pending.append(PendingFeedbackItem(
                task_id=task_id,
                domain=task.get("domain", "unknown"),
                specialist_name=task.get("specialist_name"),
                request_preview=task.get("request", "")[:100],
                response_preview=task.get("response", "")[:100],
                created_at=created_at,
                age_minutes=age_minutes,
            ))

            if len(pending) >= limit:
                break

    return pending


async def _get_feedback_stats() -> FeedbackStats:
    """Get feedback statistics."""
    total = len(_feedback_history)

    if total == 0:
        return FeedbackStats()

    ratings = [f["rating"] for f in _feedback_history.values()]
    positive = sum(1 for r in ratings if r >= 4)

    # Count by domain
    domain_counts: Dict[str, int] = {}
    for task_id, feedback in _feedback_history.items():
        task = next((t for t in _task_history if t.get("id") == task_id), None)
        if task:
            domain = task.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # Get pending count
    pending = await _get_pending_feedback(100)

    return FeedbackStats(
        total_feedback=total,
        positive_rate=positive / total if total > 0 else 0.0,
        avg_rating=sum(ratings) / total if total > 0 else 0.0,
        pending_count=len(pending),
        feedback_by_domain=domain_counts,
    )


def record_task(task_data: Dict[str, Any]) -> None:
    """Record a task (called by router)."""
    _task_history.append(task_data)
    # Keep only last 1000 tasks in memory
    if len(_task_history) > 1000:
        _task_history.pop(0)
