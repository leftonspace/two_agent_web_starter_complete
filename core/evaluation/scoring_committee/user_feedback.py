"""
PHASE 7.5: User Feedback Component

Collects and manages user feedback on task results.
Feedback is the most important signal for JARVIS (administration domain).

Usage:
    from core.evaluation.scoring_committee import UserFeedback, UserFeedbackCollector

    collector = get_feedback_collector()

    # Submit feedback
    feedback = UserFeedback(
        task_id=task_id,
        specialist_id=specialist_id,
        rating=4,
        worked_correctly=True,
        needed_edits=False,
    )
    await collector.submit(feedback)

    # Get feedback for scoring
    feedback = await collector.get(task_id)
    score = feedback.to_score()
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Feedback Models
# ============================================================================


class UserFeedback(BaseModel):
    """
    Feedback provided by user on task results.

    This is the primary quality signal for most domains,
    especially administration (JARVIS).
    """

    # Identity
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    specialist_id: UUID

    # Core rating (1-5 stars)
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Star rating (1=poor, 5=excellent)",
    )

    # Quality indicators
    worked_correctly: bool = Field(
        ...,
        description="Did the output work as expected?",
    )
    needed_edits: bool = Field(
        default=False,
        description="Did you need to edit the output?",
    )
    edit_severity: Optional[Literal["minor", "moderate", "major"]] = Field(
        default=None,
        description="How significant were the edits?",
    )

    # Detailed feedback
    comments: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Free-form comments",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags like 'slow', 'verbose', 'missed_requirement'",
    )

    # Context
    domain: Optional[str] = None
    task_type: Optional[str] = None

    # Timestamps
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    def to_score(self) -> float:
        """
        Convert feedback to 0-1 score.

        Scoring logic:
        1. Base score from rating (1-5 → 0.2-1.0)
        2. Penalty if didn't work correctly (-50%)
        3. Penalty for edits (minor=-10%, moderate=-30%, major=-50%)

        Returns:
            Score from 0.0 to 1.0
        """
        # Base score from rating
        base = self.rating / 5.0

        # Penalty for not working correctly
        if not self.worked_correctly:
            base *= 0.5

        # Penalty for needed edits
        if self.needed_edits:
            multipliers = {
                "minor": 0.9,
                "moderate": 0.7,
                "major": 0.5,
            }
            base *= multipliers.get(self.edit_severity, 0.8)

        return max(0.0, min(1.0, base))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "specialist_id": str(self.specialist_id),
            "rating": self.rating,
            "worked_correctly": self.worked_correctly,
            "needed_edits": self.needed_edits,
            "edit_severity": self.edit_severity,
            "comments": self.comments,
            "tags": self.tags,
            "domain": self.domain,
            "task_type": self.task_type,
            "submitted_at": self.submitted_at.isoformat(),
            "score": self.to_score(),
        }


class FeedbackRequest(BaseModel):
    """Request for user feedback on a task."""

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    specialist_id: UUID
    specialist_name: Optional[str] = None
    domain: str
    request_summary: str = Field(
        ...,
        max_length=200,
        description="Brief summary of the task",
    )
    response_preview: str = Field(
        default="",
        max_length=500,
        description="Preview of the response",
    )
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    priority: int = Field(
        default=1,
        ge=1,
        le=3,
        description="1=low, 2=medium, 3=high",
    )


# ============================================================================
# Feedback Collector
# ============================================================================


class UserFeedbackCollector:
    """
    Collect and store user feedback.

    In-memory storage with optional database persistence.
    Tracks pending feedback requests.

    Usage:
        collector = UserFeedbackCollector()

        # Submit feedback
        await collector.submit(feedback)

        # Get feedback
        feedback = await collector.get(task_id)

        # Get pending requests
        pending = await collector.get_pending()
    """

    def __init__(self, use_database: bool = False):
        """
        Initialize the collector.

        Args:
            use_database: Whether to persist to database
        """
        self._feedback: Dict[UUID, UserFeedback] = {}
        self._requests: Dict[UUID, FeedbackRequest] = {}
        self._use_database = use_database

    async def submit(self, feedback: UserFeedback) -> None:
        """
        Submit user feedback.

        Args:
            feedback: The feedback to submit
        """
        self._feedback[feedback.task_id] = feedback

        # Remove from pending requests if exists
        if feedback.task_id in self._requests:
            del self._requests[feedback.task_id]

        # Persist to database if enabled
        if self._use_database:
            await self._save_to_database(feedback)

        logger.info(
            f"Received feedback for task {feedback.task_id}: "
            f"rating={feedback.rating}, score={feedback.to_score():.2f}"
        )

    async def get(self, task_id: UUID) -> Optional[UserFeedback]:
        """
        Get feedback for a task.

        Args:
            task_id: Task ID to get feedback for

        Returns:
            UserFeedback if available, None otherwise
        """
        # Check in-memory cache
        if task_id in self._feedback:
            return self._feedback[task_id]

        # Try database if enabled
        if self._use_database:
            feedback = await self._load_from_database(task_id)
            if feedback:
                self._feedback[task_id] = feedback
                return feedback

        return None

    async def request_feedback(
        self,
        task_id: UUID,
        specialist_id: UUID,
        domain: str,
        request_summary: str,
        response_preview: str = "",
        specialist_name: Optional[str] = None,
        priority: int = 1,
    ) -> FeedbackRequest:
        """
        Request feedback for a task.

        Args:
            task_id: Task to request feedback for
            specialist_id: Specialist that handled the task
            domain: Task domain
            request_summary: Summary of the task
            response_preview: Preview of the response
            specialist_name: Name of the specialist
            priority: Request priority (1-3)

        Returns:
            The feedback request
        """
        request = FeedbackRequest(
            task_id=task_id,
            specialist_id=specialist_id,
            specialist_name=specialist_name,
            domain=domain,
            request_summary=request_summary,
            response_preview=response_preview[:500],
            priority=priority,
        )

        self._requests[task_id] = request

        logger.info(f"Requested feedback for task {task_id} (priority={priority})")

        return request

    async def get_pending(self) -> List[FeedbackRequest]:
        """
        Get pending feedback requests.

        Returns:
            List of pending requests, sorted by priority
        """
        pending = list(self._requests.values())
        # Sort by priority (high first) then by time (oldest first)
        pending.sort(key=lambda r: (-r.priority, r.requested_at))
        return pending

    async def get_pending_count(self) -> int:
        """Get count of pending feedback requests."""
        return len(self._requests)

    async def has_feedback(self, task_id: UUID) -> bool:
        """Check if feedback exists for a task."""
        if task_id in self._feedback:
            return True
        if self._use_database:
            return await self._exists_in_database(task_id)
        return False

    async def get_recent(self, limit: int = 10) -> List[UserFeedback]:
        """Get most recent feedback."""
        feedbacks = list(self._feedback.values())
        feedbacks.sort(key=lambda f: f.submitted_at, reverse=True)
        return feedbacks[:limit]

    async def get_by_specialist(
        self,
        specialist_id: UUID,
        limit: int = 50,
    ) -> List[UserFeedback]:
        """Get feedback for a specific specialist."""
        feedbacks = [
            f for f in self._feedback.values()
            if f.specialist_id == specialist_id
        ]
        feedbacks.sort(key=lambda f: f.submitted_at, reverse=True)
        return feedbacks[:limit]

    async def get_statistics(
        self,
        specialist_id: Optional[UUID] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Args:
            specialist_id: Filter by specialist (optional)
            domain: Filter by domain (optional)

        Returns:
            Statistics dictionary
        """
        feedbacks = list(self._feedback.values())

        # Apply filters
        if specialist_id:
            feedbacks = [f for f in feedbacks if f.specialist_id == specialist_id]
        if domain:
            feedbacks = [f for f in feedbacks if f.domain == domain]

        if not feedbacks:
            return {
                "count": 0,
                "avg_rating": 0,
                "avg_score": 0,
                "worked_correctly_rate": 0,
                "needed_edits_rate": 0,
            }

        return {
            "count": len(feedbacks),
            "avg_rating": sum(f.rating for f in feedbacks) / len(feedbacks),
            "avg_score": sum(f.to_score() for f in feedbacks) / len(feedbacks),
            "worked_correctly_rate": (
                sum(1 for f in feedbacks if f.worked_correctly) / len(feedbacks)
            ),
            "needed_edits_rate": (
                sum(1 for f in feedbacks if f.needed_edits) / len(feedbacks)
            ),
        }

    async def load_recent_from_database(self, limit: int = 100) -> int:
        """
        Load recent feedback from database into memory cache.

        Call this on startup to restore feedback history.

        Args:
            limit: Maximum number of feedback entries to load

        Returns:
            Number of feedback entries loaded
        """
        if not self._use_database:
            return 0

        try:
            from database import get_session
            from database.models.user_feedback import UserFeedbackDB

            loaded = 0
            with get_session() as session:
                db_feedbacks = (
                    session.query(UserFeedbackDB)
                    .order_by(UserFeedbackDB.submitted_at.desc())
                    .limit(limit)
                    .all()
                )

                for db_feedback in db_feedbacks:
                    feedback = UserFeedback(
                        id=db_feedback.id,
                        task_id=db_feedback.task_id,
                        specialist_id=db_feedback.specialist_id,
                        rating=db_feedback.rating,
                        worked_correctly=db_feedback.worked_correctly,
                        needed_edits=db_feedback.needed_edits,
                        edit_severity=db_feedback.edit_severity,
                        comments=db_feedback.comments,
                        tags=db_feedback.get_tags(),
                        domain=db_feedback.domain,
                        task_type=db_feedback.task_type,
                        submitted_at=db_feedback.submitted_at,
                    )
                    self._feedback[feedback.task_id] = feedback
                    loaded += 1

            logger.info(f"Loaded {loaded} feedback entries from database")
            return loaded

        except ImportError:
            logger.warning("Database module not available")
        except Exception as e:
            logger.error(f"Failed to load feedback from database: {e}")

        return 0

    # -------------------------------------------------------------------------
    # Database Methods
    # -------------------------------------------------------------------------

    async def _save_to_database(self, feedback: UserFeedback) -> None:
        """Save feedback to database."""
        try:
            from database import get_session
            from database.models.user_feedback import UserFeedbackDB

            with get_session() as session:
                # Check if feedback already exists
                existing = session.query(UserFeedbackDB).filter(
                    UserFeedbackDB.task_id == feedback.task_id
                ).first()

                if existing:
                    # Update existing
                    existing.rating = feedback.rating
                    existing.worked_correctly = feedback.worked_correctly
                    existing.needed_edits = feedback.needed_edits
                    existing.edit_severity = feedback.edit_severity
                    existing.score = feedback.to_score()
                    existing.comments = feedback.comments
                    existing.set_tags(feedback.tags)
                    existing.domain = feedback.domain
                    existing.task_type = feedback.task_type
                    existing.submitted_at = feedback.submitted_at
                else:
                    # Create new
                    db_feedback = UserFeedbackDB(
                        id=feedback.id,
                        task_id=feedback.task_id,
                        specialist_id=feedback.specialist_id,
                        rating=feedback.rating,
                        worked_correctly=feedback.worked_correctly,
                        needed_edits=feedback.needed_edits,
                        edit_severity=feedback.edit_severity,
                        score=feedback.to_score(),
                        comments=feedback.comments,
                        domain=feedback.domain,
                        task_type=feedback.task_type,
                        submitted_at=feedback.submitted_at,
                    )
                    db_feedback.set_tags(feedback.tags)
                    session.add(db_feedback)

                session.commit()
                logger.debug(f"Saved feedback to database for task {feedback.task_id}")

        except ImportError:
            logger.warning("Database module not available, feedback not persisted")
        except Exception as e:
            logger.error(f"Failed to save feedback to database: {e}")

    async def _load_from_database(self, task_id: UUID) -> Optional[UserFeedback]:
        """Load feedback from database."""
        try:
            from database import get_session
            from database.models.user_feedback import UserFeedbackDB

            with get_session() as session:
                db_feedback = session.query(UserFeedbackDB).filter(
                    UserFeedbackDB.task_id == task_id
                ).first()

                if db_feedback:
                    return UserFeedback(
                        id=db_feedback.id,
                        task_id=db_feedback.task_id,
                        specialist_id=db_feedback.specialist_id,
                        rating=db_feedback.rating,
                        worked_correctly=db_feedback.worked_correctly,
                        needed_edits=db_feedback.needed_edits,
                        edit_severity=db_feedback.edit_severity,
                        comments=db_feedback.comments,
                        tags=db_feedback.get_tags(),
                        domain=db_feedback.domain,
                        task_type=db_feedback.task_type,
                        submitted_at=db_feedback.submitted_at,
                    )

        except ImportError:
            logger.warning("Database module not available")
        except Exception as e:
            logger.error(f"Failed to load feedback from database: {e}")

        return None

    async def _exists_in_database(self, task_id: UUID) -> bool:
        """Check if feedback exists in database."""
        try:
            from database import get_session
            from database.models.user_feedback import UserFeedbackDB

            with get_session() as session:
                exists = session.query(UserFeedbackDB).filter(
                    UserFeedbackDB.task_id == task_id
                ).first() is not None
                return exists

        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Failed to check feedback in database: {e}")

        return False


# ============================================================================
# Singleton Instance
# ============================================================================


_feedback_collector: Optional[UserFeedbackCollector] = None


def get_feedback_collector(use_database: bool = True) -> UserFeedbackCollector:
    """
    Get the global feedback collector.

    Args:
        use_database: Whether to persist feedback to database (default True)

    Returns:
        The feedback collector instance
    """
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = UserFeedbackCollector(use_database=use_database)
    return _feedback_collector


def reset_feedback_collector() -> None:
    """Reset the global feedback collector (for testing)."""
    global _feedback_collector
    _feedback_collector = None
