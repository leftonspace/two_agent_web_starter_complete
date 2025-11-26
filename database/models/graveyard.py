"""
Graveyard Database Models

SQLAlchemy models for persisting culled specialists and their learnings.
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
    Index,
)

from database.base import Base
from .cost_log import UUID  # Reuse UUID type


# ============================================================================
# Graveyard Entry Model
# ============================================================================


class GraveyardEntryDB(Base):
    """
    Database model for culled specialist entries.

    Stores the specialist's final state, failure patterns, and learnings.
    """

    __tablename__ = "graveyard_entries"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    specialist_id = Column(UUID, nullable=False, unique=True, index=True)
    domain = Column(String(100), nullable=False, index=True)
    name = Column(String(200), nullable=False)

    # Performance at culling
    final_avg_score = Column(Float, nullable=False)
    final_confidence = Column(Float, nullable=True, default=0.0)
    total_tasks = Column(Integer, nullable=False, default=0)
    best_score = Column(Float, nullable=True)
    worst_score = Column(Float, nullable=True)

    # Culling info
    cull_reason = Column(String(100), nullable=False, default="low_performance")

    # Analysis (JSON)
    failure_patterns = Column(Text, nullable=True)  # JSON
    learnings = Column(Text, nullable=True)  # JSON

    # Config snapshot (JSON)
    config_snapshot = Column(Text, nullable=True)  # JSON

    # Lineage
    parent_id = Column(UUID, nullable=True)
    generation = Column(Integer, nullable=False, default=1)

    # Timestamps
    spawned_at = Column(DateTime, nullable=True)
    graveyarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    lifespan_hours = Column(Float, nullable=True, default=0.0)

    # Indexes
    __table_args__ = (
        Index("ix_graveyard_domain_time", "domain", "graveyarded_at"),
        Index("ix_graveyard_score", "final_avg_score"),
    )

    def __repr__(self) -> str:
        return (
            f"<GraveyardEntryDB({self.name}, domain={self.domain}, "
            f"score={self.final_avg_score:.2f})>"
        )

    # -------------------------------------------------------------------------
    # JSON Serialization
    # -------------------------------------------------------------------------

    def get_failure_patterns(self) -> List[Dict[str, Any]]:
        """Parse failure patterns JSON."""
        if self.failure_patterns:
            return json.loads(self.failure_patterns)
        return []

    def set_failure_patterns(self, patterns: List[Dict[str, Any]]) -> None:
        """Set failure patterns from list."""
        self.failure_patterns = json.dumps(patterns)

    def get_learnings(self) -> List[Dict[str, Any]]:
        """Parse learnings JSON."""
        if self.learnings:
            return json.loads(self.learnings)
        return []

    def set_learnings(self, learnings: List[Dict[str, Any]]) -> None:
        """Set learnings from list."""
        self.learnings = json.dumps(learnings)

    def get_config_snapshot(self) -> Optional[Dict[str, Any]]:
        """Parse config snapshot JSON."""
        if self.config_snapshot:
            return json.loads(self.config_snapshot)
        return None

    def set_config_snapshot(self, config: Dict[str, Any]) -> None:
        """Set config snapshot from dict."""
        self.config_snapshot = json.dumps(config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "domain": self.domain,
            "name": self.name,
            "final_avg_score": float(self.final_avg_score or 0),
            "final_confidence": float(self.final_confidence or 0),
            "total_tasks": self.total_tasks,
            "best_score": float(self.best_score) if self.best_score else None,
            "worst_score": float(self.worst_score) if self.worst_score else None,
            "cull_reason": self.cull_reason,
            "failure_patterns": self.get_failure_patterns(),
            "learnings": self.get_learnings(),
            "config_snapshot": self.get_config_snapshot(),
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "generation": self.generation,
            "spawned_at": self.spawned_at,
            "graveyarded_at": self.graveyarded_at,
            "lifespan_hours": float(self.lifespan_hours or 0),
        }

    @classmethod
    def from_graveyard_entry(cls, entry: Any) -> "GraveyardEntryDB":
        """Create from GraveyardEntry model."""
        db_entry = cls(
            id=entry.id,
            specialist_id=entry.specialist_id,
            domain=entry.domain,
            name=entry.name,
            final_avg_score=entry.final_avg_score,
            final_confidence=entry.final_confidence,
            total_tasks=entry.total_tasks,
            best_score=entry.best_score,
            worst_score=entry.worst_score,
            cull_reason=entry.cull_reason,
            parent_id=entry.parent_id,
            generation=entry.generation,
            spawned_at=entry.spawned_at,
            graveyarded_at=entry.graveyarded_at,
            lifespan_hours=entry.lifespan_hours,
        )

        # Serialize nested objects
        if entry.failure_patterns:
            db_entry.set_failure_patterns([p.to_dict() for p in entry.failure_patterns])
        if entry.learnings:
            db_entry.set_learnings([l.to_dict() for l in entry.learnings])
        if entry.config_snapshot:
            db_entry.set_config_snapshot(entry.config_snapshot)

        return db_entry

    def to_graveyard_entry(self) -> Any:
        """Convert to GraveyardEntry model."""
        from core.evolution.graveyard import (
            GraveyardEntry,
            FailurePattern,
            Learning,
            FailureCategory,
        )

        # Parse patterns
        patterns = []
        for p_dict in self.get_failure_patterns():
            patterns.append(FailurePattern(
                category=FailureCategory(p_dict.get("category", "unknown")),
                description=p_dict.get("description", ""),
                frequency=p_dict.get("frequency", 0),
                example_tasks=[uuid.UUID(t) for t in p_dict.get("example_tasks", [])],
                suggested_fix=p_dict.get("suggested_fix", ""),
                severity=p_dict.get("severity", 0.5),
            ))

        # Parse learnings
        learnings = []
        for l_dict in self.get_learnings():
            learnings.append(Learning(
                id=uuid.UUID(l_dict["id"]) if l_dict.get("id") else uuid.uuid4(),
                type=l_dict.get("type", "enhancement"),
                instruction=l_dict.get("instruction", ""),
                source_patterns=l_dict.get("source_patterns", []),
                confidence=l_dict.get("confidence", 0.5),
                times_applied=l_dict.get("times_applied", 0),
                effectiveness=l_dict.get("effectiveness"),
            ))

        return GraveyardEntry(
            id=self.id,
            specialist_id=self.specialist_id,
            domain=self.domain,
            name=self.name,
            final_avg_score=self.final_avg_score,
            final_confidence=self.final_confidence or 0.0,
            total_tasks=self.total_tasks,
            best_score=self.best_score or 0.0,
            worst_score=self.worst_score or 0.0,
            cull_reason=self.cull_reason,
            failure_patterns=patterns,
            learnings=learnings,
            config_snapshot=self.get_config_snapshot() or {},
            parent_id=self.parent_id,
            generation=self.generation,
            spawned_at=self.spawned_at,
            graveyarded_at=self.graveyarded_at,
            lifespan_hours=self.lifespan_hours or 0.0,
        )


# ============================================================================
# Domain Learnings Model
# ============================================================================


class DomainLearningDB(Base):
    """
    Aggregated learnings by domain.

    These are the distilled learnings that get injected into
    new specialists for each domain.
    """

    __tablename__ = "domain_learnings"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    domain = Column(String(100), nullable=False, index=True)

    # Learning
    learning_type = Column(String(20), nullable=False)  # avoidance, enhancement, technique
    instruction = Column(Text, nullable=False)
    source_patterns = Column(Text, nullable=True)  # JSON array

    # Metrics
    confidence = Column(Float, nullable=False, default=0.5)
    times_applied = Column(Integer, nullable=False, default=0)
    effectiveness = Column(Float, nullable=True)  # NULL until measured

    # Source
    source_specialist_id = Column(UUID, nullable=True)
    source_specialist_name = Column(String(200), nullable=True)

    # Status
    is_active = Column(Integer, nullable=False, default=1)  # 1=active, 0=disabled

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_domain_learnings_domain_type", "domain", "learning_type"),
        Index("ix_domain_learnings_confidence", "confidence"),
        Index("ix_domain_learnings_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<DomainLearningDB(domain={self.domain}, "
            f"type={self.learning_type}, conf={self.confidence:.2f})>"
        )

    def get_source_patterns(self) -> List[str]:
        """Parse source patterns JSON."""
        if self.source_patterns:
            return json.loads(self.source_patterns)
        return []

    def set_source_patterns(self, patterns: List[str]) -> None:
        """Set source patterns from list."""
        self.source_patterns = json.dumps(patterns)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "domain": self.domain,
            "type": self.learning_type,
            "instruction": self.instruction,
            "source_patterns": self.get_source_patterns(),
            "confidence": round(float(self.confidence), 3),
            "times_applied": self.times_applied,
            "effectiveness": round(float(self.effectiveness), 3) if self.effectiveness else None,
            "is_active": bool(self.is_active),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ============================================================================
# Graveyard Statistics Model
# ============================================================================


class GraveyardStatsDB(Base):
    """
    Aggregated statistics for the graveyard.

    Updated periodically for dashboard display.
    """

    __tablename__ = "graveyard_stats"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    domain = Column(String(100), nullable=True, index=True)  # NULL = all domains

    # Counts
    total_entries = Column(Integer, nullable=False, default=0)
    total_learnings = Column(Integer, nullable=False, default=0)

    # Averages
    avg_score_at_death = Column(Float, nullable=True)
    avg_tasks_completed = Column(Float, nullable=True)
    avg_lifespan_hours = Column(Float, nullable=True)

    # Pattern breakdown (JSON)
    pattern_counts = Column(Text, nullable=True)  # JSON: {category: count}

    # Time range
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<GraveyardStatsDB(domain={self.domain}, "
            f"entries={self.total_entries})>"
        )

    def get_pattern_counts(self) -> Dict[str, int]:
        """Parse pattern counts JSON."""
        if self.pattern_counts:
            return json.loads(self.pattern_counts)
        return {}

    def set_pattern_counts(self, counts: Dict[str, int]) -> None:
        """Set pattern counts from dict."""
        self.pattern_counts = json.dumps(counts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "total_entries": self.total_entries,
            "total_learnings": self.total_learnings,
            "avg_score_at_death": round(float(self.avg_score_at_death or 0), 3),
            "avg_tasks_completed": round(float(self.avg_tasks_completed or 0), 1),
            "avg_lifespan_hours": round(float(self.avg_lifespan_hours or 0), 1),
            "pattern_counts": self.get_pattern_counts(),
            "calculated_at": self.calculated_at,
        }
