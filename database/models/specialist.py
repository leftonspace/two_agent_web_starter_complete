"""
Specialist Database Models

SQLAlchemy models for persisting specialist configurations
and performance data.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Text,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from database.base import Base
from .cost_log import UUID  # Reuse UUID type from cost_log


# ============================================================================
# Specialist Model
# ============================================================================


class SpecialistDB(Base):
    """
    Database model for specialist agents.

    Stores the configuration, performance stats, and lineage
    of each specialist.
    """

    __tablename__ = "specialists"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    domain = Column(String(100), nullable=False, index=True)
    name = Column(String(100), nullable=False)

    # Configuration (stored as JSON)
    config = Column(Text, nullable=False)

    # Lineage
    generation = Column(Integer, nullable=False, default=1)
    parent_id = Column(UUID, ForeignKey("specialists.id"), nullable=True)

    # Status (active, probation, graveyard, retired)
    status = Column(String(20), nullable=False, default="probation", index=True)

    # Performance (stored as JSON for flexibility)
    performance = Column(Text, nullable=False, default="{}")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    promoted_at = Column(DateTime, nullable=True)
    culled_at = Column(DateTime, nullable=True)

    # Metadata
    tags = Column(Text, default="[]")  # JSON array
    notes = Column(Text, default="")

    # Relationships
    children = relationship(
        "SpecialistDB",
        backref="parent",
        remote_side=[id],
        foreign_keys=[parent_id],
    )

    # Indexes
    __table_args__ = (
        Index("ix_specialists_domain_status", "domain", "status"),
        Index("ix_specialists_domain_generation", "domain", "generation"),
    )

    def __repr__(self) -> str:
        return (
            f"<SpecialistDB(id={self.id}, domain={self.domain}, "
            f"name={self.name}, status={self.status})>"
        )

    # -------------------------------------------------------------------------
    # Serialization Helpers
    # -------------------------------------------------------------------------

    def get_config_dict(self) -> Dict[str, Any]:
        """Parse config JSON to dict."""
        config_val = self.config
        if isinstance(config_val, str):
            return json.loads(config_val)
        return config_val or {}  # type: ignore[return-value]

    def set_config_dict(self, config: Dict[str, Any]) -> None:
        """Set config from dict."""
        object.__setattr__(self, 'config', json.dumps(config))

    def get_performance_dict(self) -> Dict[str, Any]:
        """Parse performance JSON to dict."""
        perf_val = self.performance
        if isinstance(perf_val, str):
            return json.loads(perf_val)
        return perf_val or {}  # type: ignore[return-value]

    def set_performance_dict(self, performance: Dict[str, Any]) -> None:
        """Set performance from dict."""
        object.__setattr__(self, 'performance', json.dumps(performance))

    def get_tags_list(self) -> List[str]:
        """Parse tags JSON to list."""
        tags_val = self.tags
        if isinstance(tags_val, str):
            return json.loads(tags_val)
        return tags_val or []  # type: ignore[return-value]

    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from list."""
        object.__setattr__(self, 'tags', json.dumps(tags))

    # -------------------------------------------------------------------------
    # Conversion to/from Pydantic Model
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Pydantic model."""
        return {
            "id": str(self.id) if self.id else None,
            "domain": self.domain,
            "name": self.name,
            "config": self.get_config_dict(),
            "generation": self.generation,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "status": self.status,
            "performance": self.get_performance_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "promoted_at": self.promoted_at,
            "culled_at": self.culled_at,
            "tags": self.get_tags_list(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpecialistDB":
        """Create from dictionary."""
        specialist = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            domain=data["domain"],
            name=data["name"],
            generation=data.get("generation", 1),
            parent_id=uuid.UUID(data["parent_id"]) if data.get("parent_id") else None,
            status=data.get("status", "probation"),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
            promoted_at=data.get("promoted_at"),
            culled_at=data.get("culled_at"),
            notes=data.get("notes", ""),
        )

        # Handle JSON fields
        if isinstance(data.get("config"), dict):
            specialist.set_config_dict(data["config"])
        else:
            specialist.config = data.get("config", "{}")

        if isinstance(data.get("performance"), dict):
            specialist.set_performance_dict(data["performance"])
        else:
            specialist.performance = data.get("performance", "{}")

        if isinstance(data.get("tags"), list):
            specialist.set_tags_list(data["tags"])
        else:
            specialist.tags = data.get("tags", "[]")

        return specialist

    # -------------------------------------------------------------------------
    # Query Helpers
    # -------------------------------------------------------------------------

    @property
    def avg_score(self) -> float:
        """Get average score from performance stats."""
        perf = self.get_performance_dict()
        return perf.get("avg_score", 0.0)

    @property
    def task_count(self) -> int:
        """Get task count from performance stats."""
        perf = self.get_performance_dict()
        return perf.get("task_count", 0)

    @property
    def trend(self) -> str:
        """Get trend from performance stats."""
        perf = self.get_performance_dict()
        return perf.get("trend", "stable")

    def is_active(self) -> bool:
        """Check if specialist is active or on probation."""
        return self.status in ("active", "probation")


# ============================================================================
# Specialist Task Log
# ============================================================================


class SpecialistTaskLog(Base):
    """
    Log of tasks handled by specialists.

    Used for performance tracking and analysis.
    """

    __tablename__ = "specialist_task_log"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    # Foreign keys
    specialist_id = Column(UUID, ForeignKey("specialists.id"), nullable=False, index=True)
    task_id = Column(UUID, nullable=True)

    # Task info
    domain = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=True)
    task_summary = Column(Text, nullable=True)

    # Performance
    score = Column(Float, nullable=False)
    success = Column(Integer, default=1)  # 1 = success, 0 = failure
    response_time_ms = Column(Float, default=0.0)
    cost_cad = Column(Float, default=0.0)

    # Model used
    model = Column(String(100), nullable=True)
    model_tier = Column(String(20), nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)

    # Error info (if failed)
    error_type = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_specialist_task_log_specialist_completed", "specialist_id", "completed_at"),
        Index("ix_specialist_task_log_domain_score", "domain", "score"),
    )

    def __repr__(self) -> str:
        return (
            f"<SpecialistTaskLog(specialist_id={self.specialist_id}, "
            f"score={self.score:.2f}, success={bool(self.success)})>"
        )

    @classmethod
    def create(
        cls,
        specialist_id: uuid.UUID,
        domain: str,
        score: float,
        started_at: datetime,
        success: bool = True,
        task_id: Optional[uuid.UUID] = None,
        task_type: Optional[str] = None,
        task_summary: Optional[str] = None,
        response_time_ms: float = 0.0,
        cost_cad: float = 0.0,
        model: Optional[str] = None,
        model_tier: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> "SpecialistTaskLog":
        """Create a new task log entry."""
        return cls(
            id=uuid.uuid4(),
            specialist_id=specialist_id,
            task_id=task_id,
            domain=domain,
            task_type=task_type,
            task_summary=task_summary,
            score=score,
            success=1 if success else 0,
            response_time_ms=response_time_ms,
            cost_cad=cost_cad,
            model=model,
            model_tier=model_tier,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            error_type=error_type,
            error_message=error_message,
        )


# ============================================================================
# Graveyard Learnings
# ============================================================================


class GraveyardLearning(Base):
    """
    Learnings extracted from culled specialists.

    When a specialist is culled, we analyze what went wrong
    and store learnings for future specialists to avoid.
    """

    __tablename__ = "graveyard_learnings"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    # Source
    specialist_id = Column(UUID, ForeignKey("specialists.id"), nullable=False)
    domain = Column(String(100), nullable=False, index=True)

    # Learning type (avoid_pattern, failed_approach, etc.)
    learning_type = Column(String(50), nullable=False)

    # The actual learning
    pattern = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # Context
    culled_at = Column(DateTime, nullable=False)
    avg_score_at_cull = Column(Float, nullable=True)
    task_count_at_cull = Column(Integer, nullable=True)

    # Whether this learning is still active
    active = Column(Integer, default=1)  # 1 = active, 0 = deprecated

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_graveyard_learnings_domain_active", "domain", "active"),
    )

    def __repr__(self) -> str:
        return (
            f"<GraveyardLearning(domain={self.domain}, "
            f"type={self.learning_type}, pattern={self.pattern[:50]}...)>"
        )

    @classmethod
    def create(
        cls,
        specialist_id: uuid.UUID,
        domain: str,
        learning_type: str,
        pattern: str,
        description: Optional[str] = None,
        avg_score: Optional[float] = None,
        task_count: Optional[int] = None,
    ) -> "GraveyardLearning":
        """Create a new graveyard learning."""
        return cls(
            id=uuid.uuid4(),
            specialist_id=specialist_id,
            domain=domain,
            learning_type=learning_type,
            pattern=pattern,
            description=description,
            culled_at=datetime.utcnow(),
            avg_score_at_cull=avg_score,
            task_count_at_cull=task_count,
            active=1,
            created_at=datetime.utcnow(),
        )
