"""
PHASE 7.4: Domain Pool System

Manages the top-3 specialists per domain with intelligent selection.
Selection modes allow different strategies based on task criticality.

Usage:
    from core.specialists import DomainPool, SelectionMode

    pool = DomainPool(domain="code_review")
    pool.add(specialist1)
    pool.add(specialist2)
    pool.add(specialist3)

    # Different selection strategies
    best = pool.select(SelectionMode.BEST)      # Always #1
    weighted = pool.select()                     # 60/30/10 distribution
    round_robin = pool.select(SelectionMode.ROUND_ROBIN)  # Equal
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .specialist import Specialist, SpecialistStatus


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class PoolError(Exception):
    """Base exception for pool operations."""
    pass


class NoSpecialistsError(PoolError):
    """Raised when selecting from empty pool."""
    def __init__(self, domain: str):
        self.domain = domain
        super().__init__(f"No specialists available in {domain} pool")


class SpecialistNotFoundError(PoolError):
    """Raised when specific specialist not found."""
    def __init__(self, specialist_id: UUID):
        self.specialist_id = specialist_id
        super().__init__(f"Specialist {specialist_id} not found in pool")


class PoolFullError(PoolError):
    """Raised when trying to add to full pool."""
    def __init__(self, domain: str, max_size: int = 3):
        self.domain = domain
        self.max_size = max_size
        super().__init__(f"Pool {domain} is full (max {max_size} specialists)")


# ============================================================================
# Selection Mode
# ============================================================================


class SelectionMode(str, Enum):
    """
    Strategy for selecting a specialist from the pool.

    - BEST: Always select #1 ranked (for critical tasks)
    - WEIGHTED: 60/30/10 probability distribution (default)
    - ROUND_ROBIN: Equal distribution (for evaluation/benchmarking)
    - SPECIFIC: Select specific specialist by ID
    """
    BEST = "best"
    WEIGHTED = "weighted"
    ROUND_ROBIN = "round_robin"
    SPECIFIC = "specific"


# ============================================================================
# Domain Pool
# ============================================================================


class DomainPool(BaseModel):
    """
    Manages top-3 specialists for a domain.

    Specialists are ranked by average score, with the best performer
    at index 0. Selection modes allow different strategies for
    choosing which specialist handles a task.

    For the "administration" domain, the #1 specialist is JARVIS -
    the user-facing personality of the system.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4)
    domain: str = Field(
        ...,
        min_length=1,
        description="Domain this pool manages",
    )

    # Pool contents (ordered by score, best first)
    specialists: List[Specialist] = Field(
        default_factory=list,
        description="Specialists in this pool (max 3, ordered by score)",
    )

    # Pool configuration
    max_size: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum specialists in pool",
    )

    # Evolution control
    generation: int = Field(
        default=1,
        ge=1,
        description="Current pool generation",
    )
    evolution_paused: bool = Field(
        default=False,
        description="Whether evolution is temporarily paused",
    )
    pause_reason: Optional[str] = Field(
        default=None,
        description="Reason for pausing evolution",
    )

    # Selection tracking
    _round_robin_index: int = -1
    selection_count: int = Field(default=0, description="Total selections made")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}

    def __init__(self, **data):
        super().__init__(**data)
        self._round_robin_index = -1

    # -------------------------------------------------------------------------
    # Selection
    # -------------------------------------------------------------------------

    def select(
        self,
        mode: SelectionMode = SelectionMode.WEIGHTED,
        specialist_id: Optional[UUID] = None,
    ) -> Specialist:
        """
        Select a specialist from the pool.

        Args:
            mode: Selection strategy to use
            specialist_id: Required if mode is SPECIFIC

        Returns:
            Selected Specialist

        Raises:
            NoSpecialistsError: If pool is empty
            SpecialistNotFoundError: If specific specialist not found
        """
        eligible = [s for s in self.specialists if s.is_eligible_for_tasks()]

        if not eligible:
            raise NoSpecialistsError(self.domain)

        selected: Specialist

        if mode == SelectionMode.BEST:
            selected = eligible[0]

        elif mode == SelectionMode.WEIGHTED:
            # 60/30/10 distribution
            weights = [0.6, 0.3, 0.1][:len(eligible)]
            # Normalize if fewer than 3
            total = sum(weights)
            weights = [w / total for w in weights]
            selected = random.choices(eligible, weights=weights)[0]

        elif mode == SelectionMode.ROUND_ROBIN:
            self._round_robin_index = (self._round_robin_index + 1) % len(eligible)
            selected = eligible[self._round_robin_index]

        elif mode == SelectionMode.SPECIFIC:
            if specialist_id is None:
                raise ValueError("specialist_id required for SPECIFIC mode")
            found = None
            for s in eligible:
                if s.id == specialist_id:
                    found = s
                    break
            if found is None:
                raise SpecialistNotFoundError(specialist_id)
            selected = found

        else:
            raise ValueError(f"Unknown selection mode: {mode}")

        self.selection_count += 1
        self.updated_at = datetime.utcnow()

        logger.debug(
            f"Selected {selected.name} from {self.domain} pool "
            f"(mode={mode.value}, rank={eligible.index(selected) + 1})"
        )

        return selected

    # -------------------------------------------------------------------------
    # Pool Management
    # -------------------------------------------------------------------------

    def add(self, specialist: Specialist) -> None:
        """
        Add a specialist to the pool.

        Args:
            specialist: Specialist to add

        Raises:
            PoolFullError: If pool already at max capacity
            ValueError: If specialist domain doesn't match pool domain
        """
        if specialist.domain != self.domain:
            raise ValueError(
                f"Specialist domain '{specialist.domain}' doesn't match "
                f"pool domain '{self.domain}'"
            )

        # Check if already in pool
        for existing in self.specialists:
            if existing.id == specialist.id:
                logger.warning(f"Specialist {specialist.id} already in pool")
                return

        if len(self.specialists) >= self.max_size:
            raise PoolFullError(self.domain, self.max_size)

        self.specialists.append(specialist)
        self.rerank()
        self.updated_at = datetime.utcnow()

        logger.info(
            f"Added {specialist.name} to {self.domain} pool "
            f"(rank={self._get_rank(specialist.id)})"
        )

    def remove(self, specialist_id: UUID) -> Specialist:
        """
        Remove a specialist from the pool.

        Args:
            specialist_id: ID of specialist to remove

        Returns:
            Removed specialist

        Raises:
            SpecialistNotFoundError: If specialist not in pool
        """
        for i, s in enumerate(self.specialists):
            if s.id == specialist_id:
                removed = self.specialists.pop(i)
                self.updated_at = datetime.utcnow()
                logger.info(f"Removed {removed.name} from {self.domain} pool")
                return removed

        raise SpecialistNotFoundError(specialist_id)

    def replace(self, old_id: UUID, new_specialist: Specialist) -> Specialist:
        """
        Replace a specialist with a new one.

        Args:
            old_id: ID of specialist to replace
            new_specialist: New specialist to add

        Returns:
            Removed specialist
        """
        removed = self.remove(old_id)
        self.add(new_specialist)
        return removed

    def rerank(self) -> None:
        """Re-sort specialists by average score (best first)."""
        self.specialists.sort(
            key=lambda s: s.performance.avg_score,
            reverse=True,
        )
        self.updated_at = datetime.utcnow()

    def _get_rank(self, specialist_id: UUID) -> int:
        """Get 1-based rank of specialist in pool."""
        for i, s in enumerate(self.specialists):
            if s.id == specialist_id:
                return i + 1
        return -1

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def get_rankings(self) -> List[Tuple[int, Specialist]]:
        """
        Get specialists with their rankings.

        Returns:
            List of (rank, specialist) tuples, 1-indexed
        """
        return [(i + 1, s) for i, s in enumerate(self.specialists)]

    def get_specialist(self, specialist_id: UUID) -> Optional[Specialist]:
        """Get specialist by ID if in pool."""
        for s in self.specialists:
            if s.id == specialist_id:
                return s
        return None

    def get_best(self) -> Optional[Specialist]:
        """Get best specialist (rank 1) if pool not empty."""
        if self.specialists:
            return self.specialists[0]
        return None

    def is_jarvis_domain(self) -> bool:
        """Check if this is the JARVIS domain (administration)."""
        return self.domain.lower() == "administration"

    def is_empty(self) -> bool:
        """Check if pool has no specialists."""
        return len(self.specialists) == 0

    def is_full(self) -> bool:
        """Check if pool is at capacity."""
        return len(self.specialists) >= self.max_size

    @property
    def size(self) -> int:
        """Current number of specialists in pool."""
        return len(self.specialists)

    # -------------------------------------------------------------------------
    # Evolution Control
    # -------------------------------------------------------------------------

    def pause_evolution(self, reason: str) -> None:
        """Pause automatic evolution."""
        self.evolution_paused = True
        self.pause_reason = reason
        self.updated_at = datetime.utcnow()
        logger.info(f"Paused evolution for {self.domain}: {reason}")

    def resume_evolution(self) -> None:
        """Resume automatic evolution."""
        self.evolution_paused = False
        self.pause_reason = None
        self.updated_at = datetime.utcnow()
        logger.info(f"Resumed evolution for {self.domain}")

    def increment_generation(self) -> int:
        """Increment and return new generation number."""
        self.generation += 1
        self.updated_at = datetime.utcnow()
        return self.generation

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "id": str(self.id),
            "domain": self.domain,
            "specialist_ids": [str(s.id) for s in self.specialists],
            "max_size": self.max_size,
            "generation": self.generation,
            "evolution_paused": self.evolution_paused,
            "pause_reason": self.pause_reason,
            "selection_count": self.selection_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_db_row(
        cls,
        row: Dict[str, Any],
        specialists: Optional[List[Specialist]] = None,
    ) -> "DomainPool":
        """
        Create from database row.

        Args:
            row: Database row dictionary
            specialists: Pre-loaded specialists (optional)
        """
        pool = cls(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            domain=row["domain"],
            max_size=row.get("max_size", 3),
            generation=row.get("generation", 1),
            evolution_paused=row.get("evolution_paused", False),
            pause_reason=row.get("pause_reason"),
            selection_count=row.get("selection_count", 0),
            created_at=row.get("created_at", datetime.utcnow()),
            updated_at=row.get("updated_at", datetime.utcnow()),
        )

        # Add specialists if provided
        if specialists:
            for s in specialists:
                pool.specialists.append(s)
            pool.rerank()

        return pool

    def to_summary(self) -> Dict[str, Any]:
        """Get a summary of pool state."""
        return {
            "domain": self.domain,
            "size": self.size,
            "max_size": self.max_size,
            "generation": self.generation,
            "is_jarvis_domain": self.is_jarvis_domain(),
            "evolution_paused": self.evolution_paused,
            "selection_count": self.selection_count,
            "rankings": [
                {
                    "rank": rank,
                    "name": s.name,
                    "avg_score": round(s.performance.avg_score, 3),
                    "task_count": s.performance.task_count,
                    "status": s.status.value,
                }
                for rank, s in self.get_rankings()
            ],
        }
