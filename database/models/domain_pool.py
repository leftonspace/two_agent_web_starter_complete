"""
Domain Pool Database Models

SQLAlchemy models for persisting domain pool state.
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
    DateTime,
    Text,
    Index,
    Boolean,
)

from database.base import Base
from .cost_log import UUID  # Reuse UUID type


# ============================================================================
# Domain Pool Model
# ============================================================================


class DomainPoolDB(Base):
    """
    Database model for domain pools.

    Stores pool configuration and state. Specialists are stored
    separately in the specialists table and linked by domain.
    """

    __tablename__ = "domain_pools"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    domain = Column(String(100), nullable=False, unique=True, index=True)

    # Configuration
    max_size = Column(Integer, nullable=False, default=3)

    # Evolution state
    generation = Column(Integer, nullable=False, default=1)
    evolution_paused = Column(Boolean, nullable=False, default=False)
    pause_reason = Column(Text, nullable=True)

    # Tracking
    selection_count = Column(Integer, nullable=False, default=0)

    # Specialist IDs (stored as JSON array of UUID strings)
    specialist_ids = Column(Text, nullable=False, default="[]")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_domain_pools_generation", "domain", "generation"),
    )

    def __repr__(self) -> str:
        return (
            f"<DomainPoolDB(domain={self.domain}, "
            f"generation={self.generation}, specialists={self.get_specialist_count()})>"
        )

    # -------------------------------------------------------------------------
    # Serialization Helpers
    # -------------------------------------------------------------------------

    def get_specialist_ids(self) -> List[str]:
        """Parse specialist_ids JSON to list."""
        ids_val = self.specialist_ids
        if isinstance(ids_val, str):
            return json.loads(ids_val)
        return ids_val or []  # type: ignore[return-value]

    def set_specialist_ids(self, ids: List[str]) -> None:
        """Set specialist_ids from list."""
        object.__setattr__(self, 'specialist_ids', json.dumps(ids))

    def get_specialist_count(self) -> int:
        """Get number of specialists in pool."""
        return len(self.get_specialist_ids())

    # -------------------------------------------------------------------------
    # Conversion to/from Dict
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "domain": self.domain,
            "max_size": self.max_size,
            "generation": self.generation,
            "evolution_paused": bool(self.evolution_paused),
            "pause_reason": self.pause_reason,
            "selection_count": self.selection_count,
            "specialist_ids": self.get_specialist_ids(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainPoolDB":
        """Create from dictionary."""
        pool = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            domain=data["domain"],
            max_size=data.get("max_size", 3),
            generation=data.get("generation", 1),
            evolution_paused=data.get("evolution_paused", False),
            pause_reason=data.get("pause_reason"),
            selection_count=data.get("selection_count", 0),
            created_at=data.get("created_at", datetime.utcnow()),
            updated_at=data.get("updated_at", datetime.utcnow()),
        )

        # Handle specialist_ids
        ids = data.get("specialist_ids", [])
        if isinstance(ids, list):
            pool.set_specialist_ids(ids)
        else:
            pool.specialist_ids = ids or "[]"

        return pool

    # -------------------------------------------------------------------------
    # Query Helpers
    # -------------------------------------------------------------------------

    def is_jarvis_domain(self) -> bool:
        """Check if this is the JARVIS domain."""
        return self.domain.lower() == "administration"

    def is_empty(self) -> bool:
        """Check if pool has no specialists."""
        return self.get_specialist_count() == 0

    def is_full(self) -> bool:
        """Check if pool is at capacity."""
        return self.get_specialist_count() >= self.max_size


# ============================================================================
# Pool Selection Log
# ============================================================================


class PoolSelectionLog(Base):
    """
    Log of specialist selections from pools.

    Used for:
    - Analyzing selection patterns
    - Validating weighted distribution
    - Debugging selection issues
    """

    __tablename__ = "pool_selection_log"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    # Selection context
    domain = Column(String(100), nullable=False, index=True)
    specialist_id = Column(UUID, nullable=False, index=True)
    specialist_name = Column(String(100), nullable=True)

    # Selection details
    selection_mode = Column(String(20), nullable=False)  # best, weighted, round_robin, specific
    specialist_rank = Column(Integer, nullable=False)  # 1-based rank at selection time

    # Pool state at selection
    pool_size = Column(Integer, nullable=False)
    pool_generation = Column(Integer, nullable=False)

    # Task info (optional)
    task_id = Column(UUID, nullable=True)
    task_type = Column(String(50), nullable=True)

    # Timestamp
    selected_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_pool_selection_log_domain_time", "domain", "selected_at"),
        Index("ix_pool_selection_log_specialist_time", "specialist_id", "selected_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<PoolSelectionLog(domain={self.domain}, "
            f"specialist={self.specialist_name}, mode={self.selection_mode})>"
        )

    @classmethod
    def create(
        cls,
        domain: str,
        specialist_id: uuid.UUID,
        selection_mode: str,
        specialist_rank: int,
        pool_size: int,
        pool_generation: int,
        specialist_name: Optional[str] = None,
        task_id: Optional[uuid.UUID] = None,
        task_type: Optional[str] = None,
    ) -> "PoolSelectionLog":
        """Create a new selection log entry."""
        return cls(
            id=uuid.uuid4(),
            domain=domain,
            specialist_id=specialist_id,
            specialist_name=specialist_name,
            selection_mode=selection_mode,
            specialist_rank=specialist_rank,
            pool_size=pool_size,
            pool_generation=pool_generation,
            task_id=task_id,
            task_type=task_type,
            selected_at=datetime.utcnow(),
        )
