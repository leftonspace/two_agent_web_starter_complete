"""
User Feedback Database Models

SQLAlchemy models for persisting user feedback on task results.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    Index,
    ForeignKey,
)

from database.base import Base
from .cost_log import UUID  # Reuse UUID type


# ============================================================================
# User Feedback Model
# ============================================================================


class UserFeedbackDB(Base):
    """
    Database model for user feedback on task results.

    This is the primary quality signal for evaluation,
    especially for the administration (JARVIS) domain.
    """

    __tablename__ = "user_feedback"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, nullable=False, unique=True, index=True)
    specialist_id = Column(UUID, nullable=False, index=True)

    # Core rating
    rating = Column(Integer, nullable=False)  # 1-5

    # Quality indicators
    worked_correctly = Column(Boolean, nullable=False)
    needed_edits = Column(Boolean, nullable=False, default=False)
    edit_severity = Column(String(20), nullable=True)  # minor, moderate, major

    # Calculated score
    score = Column(Float, nullable=False)

    # Detailed feedback
    comments = Column(Text, nullable=True)
    tags = Column(Text, nullable=True, default="[]")  # JSON array

    # Context
    domain = Column(String(100), nullable=True, index=True)
    task_type = Column(String(100), nullable=True)

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_user_feedback_specialist_time", "specialist_id", "submitted_at"),
        Index("ix_user_feedback_domain_time", "domain", "submitted_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserFeedbackDB(task_id={self.task_id}, "
            f"rating={self.rating}, score={self.score:.2f})>"
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def get_tags(self) -> List[str]:
        """Parse tags JSON to list."""
        if isinstance(self.tags, str):
            return json.loads(self.tags)
        return self.tags or []  # type: ignore[return-value]

    def set_tags(self, tags: List[str]) -> None:
        """Set tags from list."""
        self.tags = json.dumps(tags)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "rating": self.rating,
            "worked_correctly": bool(self.worked_correctly),
            "needed_edits": bool(self.needed_edits),
            "edit_severity": self.edit_severity,
            "score": float(self.score) if self.score else 0.0,
            "comments": self.comments,
            "tags": self.get_tags(),
            "domain": self.domain,
            "task_type": self.task_type,
            "submitted_at": self.submitted_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserFeedbackDB":
        """Create from dictionary."""
        feedback = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            task_id=uuid.UUID(data["task_id"]) if isinstance(data.get("task_id"), str) else data.get("task_id"),
            specialist_id=uuid.UUID(data["specialist_id"]) if isinstance(data.get("specialist_id"), str) else data.get("specialist_id"),
            rating=data["rating"],
            worked_correctly=data["worked_correctly"],
            needed_edits=data.get("needed_edits", False),
            edit_severity=data.get("edit_severity"),
            score=data.get("score", 0.0),
            comments=data.get("comments"),
            domain=data.get("domain"),
            task_type=data.get("task_type"),
            submitted_at=data.get("submitted_at", datetime.utcnow()),
        )

        # Handle tags
        tags = data.get("tags", [])
        if isinstance(tags, list):
            feedback.set_tags(tags)
        else:
            feedback.tags = tags or "[]"

        return feedback


# ============================================================================
# Feedback Request Model
# ============================================================================


class FeedbackRequestDB(Base):
    """
    Database model for pending feedback requests.

    Tracks which tasks are awaiting user feedback.
    """

    __tablename__ = "feedback_requests"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, nullable=False, unique=True, index=True)
    specialist_id = Column(UUID, nullable=False, index=True)
    specialist_name = Column(String(100), nullable=True)

    # Context
    domain = Column(String(100), nullable=False, index=True)
    request_summary = Column(String(200), nullable=False)
    response_preview = Column(String(500), nullable=True)

    # Priority and timing
    priority = Column(Integer, nullable=False, default=1)  # 1=low, 2=medium, 3=high
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Status
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_feedback_requests_pending", "completed", "priority", "requested_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<FeedbackRequestDB(task_id={self.task_id}, "
            f"domain={self.domain}, priority={self.priority})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "specialist_name": self.specialist_name,
            "domain": self.domain,
            "request_summary": self.request_summary,
            "response_preview": self.response_preview,
            "priority": self.priority,
            "requested_at": self.requested_at,
            "expires_at": self.expires_at,
            "completed": bool(self.completed),
            "completed_at": self.completed_at,
        }


# ============================================================================
# Feedback Statistics Model
# ============================================================================


class FeedbackStatsDB(Base):
    """
    Aggregated feedback statistics by specialist/domain.

    Updated periodically to avoid expensive aggregation queries.
    """

    __tablename__ = "feedback_stats"

    # Identity (composite key)
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    specialist_id = Column(UUID, nullable=True, index=True)  # NULL = all specialists
    domain = Column(String(100), nullable=True, index=True)  # NULL = all domains

    # Statistics
    total_feedback = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Float, nullable=False, default=0.0)
    avg_score = Column(Float, nullable=False, default=0.0)
    worked_correctly_rate = Column(Float, nullable=False, default=0.0)
    needed_edits_rate = Column(Float, nullable=False, default=0.0)

    # Rating distribution
    rating_1_count = Column(Integer, nullable=False, default=0)
    rating_2_count = Column(Integer, nullable=False, default=0)
    rating_3_count = Column(Integer, nullable=False, default=0)
    rating_4_count = Column(Integer, nullable=False, default=0)
    rating_5_count = Column(Integer, nullable=False, default=0)

    # Time range
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_feedback_stats_specialist_domain", "specialist_id", "domain"),
    )

    def __repr__(self) -> str:
        return (
            f"<FeedbackStatsDB(specialist={self.specialist_id}, "
            f"domain={self.domain}, count={self.total_feedback})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "domain": self.domain,
            "total_feedback": self.total_feedback,
            "avg_rating": round(float(self.avg_rating), 2),
            "avg_score": round(float(self.avg_score), 3),
            "worked_correctly_rate": round(float(self.worked_correctly_rate), 3),
            "needed_edits_rate": round(float(self.needed_edits_rate), 3),
            "rating_distribution": {
                1: self.rating_1_count,
                2: self.rating_2_count,
                3: self.rating_3_count,
                4: self.rating_4_count,
                5: self.rating_5_count,
            },
            "calculated_at": self.calculated_at,
        }
