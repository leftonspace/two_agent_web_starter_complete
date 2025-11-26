"""
AI Council Vote Database Models

SQLAlchemy models for persisting AI Council votes.
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
# Council Vote Model
# ============================================================================


class CouncilVoteDB(Base):
    """
    Database model for AI Council votes.

    Stores individual votes from specialists on task results.
    """

    __tablename__ = "council_votes"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, nullable=False, index=True)
    voter_id = Column(UUID, nullable=False, index=True)
    voter_name = Column(String(100), nullable=True)
    voter_type = Column(String(20), nullable=False)  # specialist, jarvis

    # Score
    score = Column(Float, nullable=False)
    weight = Column(Float, nullable=False, default=1.0)

    # Criteria breakdown (JSON)
    criteria = Column(Text, nullable=True)  # JSON: {correctness, completeness, etc.}

    # Reasoning
    reasoning = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True, default="[]")  # JSON array
    weaknesses = Column(Text, nullable=True, default="[]")  # JSON array

    # Outlier status
    is_outlier = Column(Boolean, nullable=False, default=False)
    outlier_reason = Column(Text, nullable=True)

    # Metadata
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    voting_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_council_votes_task_voter", "task_id", "voter_id"),
        Index("ix_council_votes_voter_time", "voter_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CouncilVoteDB(task_id={self.task_id}, "
            f"voter={self.voter_name}, score={self.score:.2f})>"
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def get_criteria(self) -> Optional[Dict[str, int]]:
        """Parse criteria JSON."""
        if self.criteria:
            return json.loads(self.criteria)
        return None

    def set_criteria(self, criteria: Dict[str, int]) -> None:
        """Set criteria from dict."""
        self.criteria = json.dumps(criteria)

    def get_strengths(self) -> List[str]:
        """Parse strengths JSON."""
        if self.strengths:
            return json.loads(self.strengths)
        return []

    def set_strengths(self, strengths: List[str]) -> None:
        """Set strengths from list."""
        self.strengths = json.dumps(strengths)

    def get_weaknesses(self) -> List[str]:
        """Parse weaknesses JSON."""
        if self.weaknesses:
            return json.loads(self.weaknesses)
        return []

    def set_weaknesses(self, weaknesses: List[str]) -> None:
        """Set weaknesses from list."""
        self.weaknesses = json.dumps(weaknesses)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "voter_id": str(self.voter_id) if self.voter_id else None,
            "voter_name": self.voter_name,
            "voter_type": self.voter_type,
            "score": float(self.score) if self.score else 0.0,
            "weight": float(self.weight) if self.weight else 1.0,
            "criteria": self.get_criteria(),
            "reasoning": self.reasoning,
            "strengths": self.get_strengths(),
            "weaknesses": self.get_weaknesses(),
            "is_outlier": bool(self.is_outlier),
            "outlier_reason": self.outlier_reason,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "voting_time_ms": self.voting_time_ms,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CouncilVoteDB":
        """Create from dictionary."""
        vote = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            task_id=uuid.UUID(data["task_id"]) if isinstance(data.get("task_id"), str) else data.get("task_id"),
            voter_id=uuid.UUID(data["voter_id"]) if isinstance(data.get("voter_id"), str) else data.get("voter_id"),
            voter_name=data.get("voter_name"),
            voter_type=data.get("voter_type", "specialist"),
            score=data.get("score", 0.0),
            weight=data.get("weight", 1.0),
            reasoning=data.get("reasoning"),
            is_outlier=data.get("is_outlier", False),
            outlier_reason=data.get("outlier_reason"),
            model_used=data.get("model_used"),
            tokens_used=data.get("tokens_used"),
            voting_time_ms=data.get("voting_time_ms"),
            created_at=data.get("created_at", datetime.utcnow()),
        )

        # Handle nested fields
        if data.get("criteria"):
            vote.set_criteria(data["criteria"])
        if data.get("strengths"):
            vote.set_strengths(data["strengths"])
        if data.get("weaknesses"):
            vote.set_weaknesses(data["weaknesses"])

        return vote


# ============================================================================
# Council Session Model
# ============================================================================


class CouncilSessionDB(Base):
    """
    Database model for AI Council evaluation sessions.

    Stores aggregated results of a council evaluation.
    """

    __tablename__ = "council_sessions"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, nullable=False, unique=True, index=True)
    specialist_id = Column(UUID, nullable=False, index=True)
    domain = Column(String(100), nullable=False, index=True)

    # Aggregation results
    final_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    total_votes = Column(Integer, nullable=False)
    included_votes = Column(Integer, nullable=False)
    excluded_outliers = Column(Integer, nullable=False, default=0)

    # Statistics
    mean_score = Column(Float, nullable=True)
    median_score = Column(Float, nullable=True)
    std_deviation = Column(Float, nullable=True)
    min_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)

    # Bootstrap detection
    generation = Column(Integer, nullable=False, default=1)
    bootstrap_warning = Column(Boolean, nullable=False, default=False)

    # Status
    status = Column(String(20), nullable=False, default="completed")
    error = Column(Text, nullable=True)

    # Timing
    evaluation_time_ms = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_council_sessions_domain_time", "domain", "created_at"),
        Index("ix_council_sessions_specialist_time", "specialist_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CouncilSessionDB(task_id={self.task_id}, "
            f"score={self.final_score:.2f}, votes={self.included_votes})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "domain": self.domain,
            "final_score": float(self.final_score) if self.final_score else 0.0,
            "confidence": float(self.confidence) if self.confidence else 0.0,
            "total_votes": self.total_votes,
            "included_votes": self.included_votes,
            "excluded_outliers": self.excluded_outliers,
            "statistics": {
                "mean": self.mean_score,
                "median": self.median_score,
                "std": self.std_deviation,
                "min": self.min_score,
                "max": self.max_score,
            },
            "generation": self.generation,
            "bootstrap_warning": bool(self.bootstrap_warning),
            "status": self.status,
            "error": self.error,
            "evaluation_time_ms": self.evaluation_time_ms,
            "created_at": self.created_at,
        }


# ============================================================================
# Council Statistics Model
# ============================================================================


class CouncilStatsDB(Base):
    """
    Aggregated statistics for AI Council evaluations.

    Updated periodically for dashboard display.
    """

    __tablename__ = "council_stats"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    domain = Column(String(100), nullable=True, index=True)  # NULL = all domains

    # Counts
    total_sessions = Column(Integer, nullable=False, default=0)
    total_votes = Column(Integer, nullable=False, default=0)
    outliers_removed = Column(Integer, nullable=False, default=0)

    # Score statistics
    avg_final_score = Column(Float, nullable=False, default=0.0)
    avg_confidence = Column(Float, nullable=False, default=0.0)
    avg_vote_spread = Column(Float, nullable=False, default=0.0)

    # Bootstrap warnings
    bootstrap_warnings = Column(Integer, nullable=False, default=0)
    bootstrap_rate = Column(Float, nullable=False, default=0.0)

    # Agreement with Scoring Committee (when both run)
    comparison_count = Column(Integer, nullable=False, default=0)
    avg_sc_difference = Column(Float, nullable=False, default=0.0)
    agreement_rate = Column(Float, nullable=False, default=0.0)

    # Time range
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<CouncilStatsDB(domain={self.domain}, "
            f"sessions={self.total_sessions})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "total_sessions": self.total_sessions,
            "total_votes": self.total_votes,
            "outliers_removed": self.outliers_removed,
            "avg_final_score": round(float(self.avg_final_score or 0), 3),
            "avg_confidence": round(float(self.avg_confidence or 0), 3),
            "avg_vote_spread": round(float(self.avg_vote_spread or 0), 3),
            "bootstrap_warnings": self.bootstrap_warnings,
            "bootstrap_rate": round(float(self.bootstrap_rate or 0), 3),
            "comparison": {
                "count": self.comparison_count,
                "avg_difference": round(float(self.avg_sc_difference or 0), 3),
                "agreement_rate": round(float(self.agreement_rate or 0), 3),
            },
            "calculated_at": self.calculated_at,
        }
