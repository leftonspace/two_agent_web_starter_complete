"""
Evaluation Comparison Database Models

SQLAlchemy models for persisting SC vs AC comparison data.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    Index,
)

from database.base import Base
from .cost_log import UUID  # Reuse UUID type


# ============================================================================
# Evaluation Comparison Model
# ============================================================================


class EvaluationComparisonDB(Base):
    """
    Database model for SC vs AC evaluation comparisons.

    Stores individual comparisons for analysis of evaluator agreement.
    """

    __tablename__ = "evaluation_comparisons"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID, nullable=False, index=True)

    # Scores
    sc_score = Column(Float, nullable=False)
    ac_score = Column(Float, nullable=False)
    difference = Column(Float, nullable=False)  # ac_score - sc_score

    # Agreement
    agreement = Column(Boolean, nullable=False, default=False)
    agreement_threshold = Column(Float, nullable=False, default=0.1)

    # Component details (JSON)
    sc_components = Column(Text, nullable=True)  # JSON
    ac_metadata = Column(Text, nullable=True)  # JSON

    # Confidence
    sc_confidence = Column(Float, nullable=True)
    ac_confidence = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_eval_comp_task", "task_id"),
        Index("ix_eval_comp_agreement", "agreement"),
        Index("ix_eval_comp_diff", "difference"),
        Index("ix_eval_comp_time", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EvaluationComparisonDB(task_id={self.task_id}, "
            f"SC={self.sc_score:.3f}, AC={self.ac_score:.3f}, "
            f"agree={self.agreement})>"
        )

    # -------------------------------------------------------------------------
    # JSON Serialization
    # -------------------------------------------------------------------------

    def get_sc_components(self) -> Optional[Dict[str, float]]:
        """Parse SC components JSON."""
        if self.sc_components:
            return json.loads(self.sc_components)
        return None

    def set_sc_components(self, components: Dict[str, float]) -> None:
        """Set SC components from dict."""
        self.sc_components = json.dumps(components)

    def get_ac_metadata(self) -> Optional[Dict[str, Any]]:
        """Parse AC metadata JSON."""
        if self.ac_metadata:
            return json.loads(self.ac_metadata)
        return None

    def set_ac_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set AC metadata from dict."""
        self.ac_metadata = json.dumps(metadata)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "sc_score": float(self.sc_score) if self.sc_score else 0.0,
            "ac_score": float(self.ac_score) if self.ac_score else 0.0,
            "difference": float(self.difference) if self.difference else 0.0,
            "agreement": bool(self.agreement),
            "agreement_threshold": float(self.agreement_threshold or 0.1),
            "sc_components": self.get_sc_components(),
            "ac_metadata": self.get_ac_metadata(),
            "sc_confidence": float(self.sc_confidence) if self.sc_confidence else None,
            "ac_confidence": float(self.ac_confidence) if self.ac_confidence else None,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationComparisonDB":
        """Create from dictionary."""
        record = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            task_id=uuid.UUID(data["task_id"]) if isinstance(data.get("task_id"), str) else data.get("task_id"),
            sc_score=data.get("sc_score", 0.0),
            ac_score=data.get("ac_score", 0.0),
            difference=data.get("difference", 0.0),
            agreement=data.get("agreement", False),
            agreement_threshold=data.get("agreement_threshold", 0.1),
            sc_confidence=data.get("sc_confidence"),
            ac_confidence=data.get("ac_confidence"),
            created_at=data.get("created_at", datetime.utcnow()),
        )

        # Handle nested JSON fields
        if data.get("sc_components"):
            record.set_sc_components(data["sc_components"])
        if data.get("ac_metadata"):
            record.set_ac_metadata(data["ac_metadata"])

        return record


# ============================================================================
# Comparison Statistics Model
# ============================================================================


class ComparisonStatsDB(Base):
    """
    Aggregated comparison statistics.

    Updated periodically for dashboard display.
    """

    __tablename__ = "comparison_stats"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    # Counts
    total_comparisons = Column(Float, nullable=False, default=0)
    agreements = Column(Float, nullable=False, default=0)
    disagreements = Column(Float, nullable=False, default=0)

    # Rates
    agreement_rate = Column(Float, nullable=False, default=0.0)

    # Correlation
    correlation = Column(Float, nullable=False, default=0.0)

    # Difference statistics
    mean_difference = Column(Float, nullable=False, default=0.0)
    std_difference = Column(Float, nullable=False, default=0.0)
    max_difference = Column(Float, nullable=False, default=0.0)
    min_difference = Column(Float, nullable=False, default=0.0)

    # Higher counts
    sc_higher_count = Column(Float, nullable=False, default=0)
    ac_higher_count = Column(Float, nullable=False, default=0)
    equal_count = Column(Float, nullable=False, default=0)

    # Score statistics
    sc_mean = Column(Float, nullable=True)
    sc_std = Column(Float, nullable=True)
    ac_mean = Column(Float, nullable=True)
    ac_std = Column(Float, nullable=True)

    # Time range
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ComparisonStatsDB(comparisons={self.total_comparisons}, "
            f"agreement={self.agreement_rate:.2%}, corr={self.correlation:.3f})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_comparisons": int(self.total_comparisons or 0),
            "agreement_rate": round(float(self.agreement_rate or 0), 4),
            "correlation": round(float(self.correlation or 0), 4),
            "mean_difference": round(float(self.mean_difference or 0), 4),
            "std_difference": round(float(self.std_difference or 0), 4),
            "bias": {
                "direction": "AC lenient" if (self.mean_difference or 0) > 0.02 else
                            "SC lenient" if (self.mean_difference or 0) < -0.02 else "neutral",
                "magnitude": abs(float(self.mean_difference or 0)),
            },
            "counts": {
                "sc_higher": int(self.sc_higher_count or 0),
                "ac_higher": int(self.ac_higher_count or 0),
                "equal": int(self.equal_count or 0),
            },
            "score_stats": {
                "sc_mean": round(float(self.sc_mean or 0), 4),
                "sc_std": round(float(self.sc_std or 0), 4),
                "ac_mean": round(float(self.ac_mean or 0), 4),
                "ac_std": round(float(self.ac_std or 0), 4),
            },
            "calculated_at": self.calculated_at,
        }
