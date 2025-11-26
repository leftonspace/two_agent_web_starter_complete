"""
PHASE 7.5: Specialist Graveyard

Manages culled specialists and extracts learnings from their failures.
When a specialist is removed from the pool, they are sent here for
post-mortem analysis.

Usage:
    from core.evolution import Graveyard, get_graveyard

    graveyard = get_graveyard()

    # Send a failed specialist to graveyard
    entry = await graveyard.send_to_graveyard(specialist, reason="Low performance")

    # Get learnings for new specialists
    learnings = graveyard.get_learnings("code_generation")
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.specialists import Specialist


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class FailureCategory(str, Enum):
    """Categories of specialist failures."""

    PROMPT_WEAKNESS = "prompt_weakness"  # System prompt missing instructions
    TOOL_MISUSE = "tool_misuse"  # Wrong tools selected
    DOMAIN_GAP = "domain_gap"  # Missing domain knowledge
    CONSISTENCY = "consistency"  # Inconsistent quality
    EDGE_CASES = "edge_cases"  # Fails on unusual inputs
    COMPLEXITY_MISMATCH = "complexity_mismatch"  # Struggles with complex tasks
    SLOW_RESPONSE = "slow_response"  # Takes too long
    HALLUCINATION = "hallucination"  # Makes things up
    FORMAT_ERRORS = "format_errors"  # Output formatting issues
    UNKNOWN = "unknown"  # Unclassified failures


# ============================================================================
# Failure Pattern Model
# ============================================================================


class FailurePattern(BaseModel):
    """
    A pattern of failures identified in a specialist.

    Used to understand why a specialist underperformed.
    """

    category: FailureCategory
    description: str = Field(..., description="Human-readable description")
    frequency: int = Field(..., ge=0, description="How often this occurred")
    example_tasks: List[UUID] = Field(
        default_factory=list,
        description="Sample task IDs showing this pattern",
    )
    suggested_fix: str = Field(
        default="",
        description="Suggested improvement for future specialists",
    )
    severity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How severe this failure pattern is",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "description": self.description,
            "frequency": self.frequency,
            "example_tasks": [str(t) for t in self.example_tasks],
            "suggested_fix": self.suggested_fix,
            "severity": self.severity,
        }


# ============================================================================
# Learning Model
# ============================================================================


class Learning(BaseModel):
    """
    An actionable learning extracted from failure patterns.

    Types:
    - avoidance: Things to NOT do
    - enhancement: Things to ADD
    - technique: Specific methods that work well
    """

    id: UUID = Field(default_factory=uuid4)
    type: Literal["avoidance", "enhancement", "technique"]
    instruction: str = Field(
        ...,
        min_length=1,
        description="The actual learning/instruction",
    )
    source_patterns: List[str] = Field(
        default_factory=list,
        description="Pattern descriptions this came from",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this learning",
    )
    times_applied: int = Field(
        default=0,
        ge=0,
        description="How many times this was applied to new specialists",
    )
    effectiveness: Optional[float] = Field(
        default=None,
        description="Measured effectiveness (null until measured)",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "type": self.type,
            "instruction": self.instruction,
            "source_patterns": self.source_patterns,
            "confidence": self.confidence,
            "times_applied": self.times_applied,
            "effectiveness": self.effectiveness,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# Graveyard Entry Model
# ============================================================================


class GraveyardEntry(BaseModel):
    """
    A record of a culled specialist.

    Contains the specialist's final state, failure analysis,
    and extracted learnings.
    """

    id: UUID = Field(default_factory=uuid4)
    specialist_id: UUID
    domain: str
    name: str

    # Performance at time of culling
    final_avg_score: float = Field(ge=0.0, le=1.0)
    final_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    total_tasks: int = Field(ge=0)
    best_score: float = Field(default=0.0, ge=0.0, le=1.0)
    worst_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Reason for culling
    cull_reason: str = Field(default="low_performance")

    # Analysis
    failure_patterns: List[FailurePattern] = Field(default_factory=list)
    learnings: List[Learning] = Field(default_factory=list)

    # Config snapshot for future reference
    config_snapshot: Dict[str, Any] = Field(default_factory=dict)

    # Lineage
    parent_id: Optional[UUID] = Field(
        default=None,
        description="ID of specialist this was spawned from",
    )
    generation: int = Field(default=1, ge=1)

    # Timestamps
    spawned_at: Optional[datetime] = None
    graveyarded_at: datetime = Field(default_factory=datetime.utcnow)
    lifespan_hours: float = Field(default=0.0, ge=0.0)

    def __repr__(self) -> str:
        return (
            f"<GraveyardEntry({self.name}, domain={self.domain}, "
            f"score={self.final_avg_score:.2f}, patterns={len(self.failure_patterns)})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "specialist_id": str(self.specialist_id),
            "domain": self.domain,
            "name": self.name,
            "final_avg_score": round(self.final_avg_score, 4),
            "final_confidence": round(self.final_confidence, 4),
            "total_tasks": self.total_tasks,
            "best_score": round(self.best_score, 4),
            "worst_score": round(self.worst_score, 4),
            "cull_reason": self.cull_reason,
            "failure_patterns": [p.to_dict() for p in self.failure_patterns],
            "learnings": [l.to_dict() for l in self.learnings],
            "generation": self.generation,
            "lifespan_hours": round(self.lifespan_hours, 2),
            "graveyarded_at": self.graveyarded_at.isoformat(),
        }

    def to_summary(self) -> Dict[str, Any]:
        """Get brief summary."""
        return {
            "name": self.name,
            "domain": self.domain,
            "score": round(self.final_avg_score, 2),
            "tasks": self.total_tasks,
            "patterns": len(self.failure_patterns),
            "learnings": len(self.learnings),
            "reason": self.cull_reason,
        }


# ============================================================================
# Graveyard Manager
# ============================================================================


class Graveyard:
    """
    Manages culled specialists and their learnings.

    When a specialist is removed from the pool, they are sent here.
    The graveyard analyzes their failures and extracts learnings
    that can be injected into future specialists.

    Usage:
        graveyard = Graveyard()

        # Send failed specialist
        entry = await graveyard.send_to_graveyard(specialist, "Low performance")

        # Get learnings for spawner
        learnings = graveyard.get_learnings("code_generation")
    """

    def __init__(
        self,
        analyzer: Optional[Any] = None,
        extractor: Optional[Any] = None,
        db_session: Optional[Any] = None,
    ):
        """
        Initialize the graveyard.

        Args:
            analyzer: FailureAnalyzer instance
            extractor: LearningsExtractor instance
            db_session: Database session for persistence
        """
        self._analyzer = analyzer
        self._extractor = extractor
        self._db_session = db_session

        # In-memory storage (also persisted to DB)
        self._entries: Dict[UUID, GraveyardEntry] = {}
        self._domain_learnings: Dict[str, List[Learning]] = {}

        # Statistics
        self._total_entries = 0
        self._initialized_at = datetime.utcnow()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def analyzer(self) -> Any:
        """Get failure analyzer (lazy load)."""
        if self._analyzer is None:
            from .failure_analyzer import FailureAnalyzer
            self._analyzer = FailureAnalyzer()
        return self._analyzer

    @property
    def extractor(self) -> Any:
        """Get learnings extractor (lazy load)."""
        if self._extractor is None:
            from .learnings_extractor import LearningsExtractor
            self._extractor = LearningsExtractor()
        return self._extractor

    @property
    def entry_count(self) -> int:
        """Get total number of entries."""
        return len(self._entries)

    # -------------------------------------------------------------------------
    # Main Methods
    # -------------------------------------------------------------------------

    async def send_to_graveyard(
        self,
        specialist: "Specialist",
        reason: str = "low_performance",
    ) -> GraveyardEntry:
        """
        Send a culled specialist to the graveyard.

        Analyzes failures, extracts learnings, and stores entry.

        Args:
            specialist: The specialist being culled
            reason: Reason for culling

        Returns:
            GraveyardEntry with analysis results
        """
        logger.info(
            f"Sending {specialist.name} to graveyard "
            f"(reason={reason}, score={specialist.performance.avg_score:.2f})"
        )

        # Analyze failures
        patterns = await self.analyzer.analyze(specialist)

        # Extract learnings from patterns
        learnings = self.extractor.extract(patterns)

        # Calculate lifespan
        lifespan_hours = 0.0
        spawned_at = None
        if hasattr(specialist, 'spawned_at') and specialist.spawned_at:
            spawned_at = specialist.spawned_at
            lifespan_hours = (datetime.utcnow() - spawned_at).total_seconds() / 3600

        # Create entry
        entry = GraveyardEntry(
            id=uuid4(),
            specialist_id=specialist.id,
            domain=specialist.domain,
            name=specialist.name,
            final_avg_score=specialist.performance.avg_score,
            final_confidence=getattr(specialist.performance, 'confidence', 0.0),
            total_tasks=specialist.performance.task_count,
            best_score=specialist.performance.best_score,
            worst_score=specialist.performance.worst_score,
            cull_reason=reason,
            failure_patterns=patterns,
            learnings=learnings,
            config_snapshot=specialist.config.model_dump() if hasattr(specialist.config, 'model_dump') else {},
            parent_id=getattr(specialist, 'parent_id', None),
            generation=getattr(specialist, 'generation', 1),
            spawned_at=spawned_at,
            graveyarded_at=datetime.utcnow(),
            lifespan_hours=lifespan_hours,
        )

        # Store entry
        self._entries[entry.specialist_id] = entry
        self._total_entries += 1

        # Update domain learnings cache
        await self._update_domain_learnings(specialist.domain, learnings)

        # Persist to database
        await self._save(entry)

        logger.info(
            f"Graveyard entry created: {entry.name}, "
            f"patterns={len(patterns)}, learnings={len(learnings)}"
        )

        return entry

    def get_learnings(
        self,
        domain: str,
        min_confidence: float = 0.5,
        limit: int = 20,
    ) -> List[Learning]:
        """
        Get learnings for a domain.

        Used by the spawner to inject learnings into new specialists.

        Args:
            domain: Domain to get learnings for
            min_confidence: Minimum confidence threshold
            limit: Maximum number of learnings to return

        Returns:
            List of learnings sorted by confidence
        """
        domain_learnings = self._domain_learnings.get(domain, [])

        # Filter by confidence
        filtered = [l for l in domain_learnings if l.confidence >= min_confidence]

        # Sort by confidence (highest first)
        sorted_learnings = sorted(filtered, key=lambda l: l.confidence, reverse=True)

        return sorted_learnings[:limit]

    def get_entries(
        self,
        domain: Optional[str] = None,
        limit: int = 100,
    ) -> List[GraveyardEntry]:
        """
        Get graveyard entries.

        Args:
            domain: Filter by domain (None = all)
            limit: Maximum entries to return

        Returns:
            List of entries sorted by timestamp (newest first)
        """
        entries = list(self._entries.values())

        if domain:
            entries = [e for e in entries if e.domain == domain]

        # Sort by graveyarded_at (newest first)
        sorted_entries = sorted(
            entries,
            key=lambda e: e.graveyarded_at,
            reverse=True,
        )

        return sorted_entries[:limit]

    def get_entry(self, specialist_id: UUID) -> Optional[GraveyardEntry]:
        """Get entry for a specific specialist."""
        return self._entries.get(specialist_id)

    async def cleanup_old(self, days: int = 90) -> int:
        """
        Remove entries older than X days.

        Keeps learnings but removes detailed entries.

        Args:
            days: Remove entries older than this

        Returns:
            Number of entries removed
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        removed = 0

        entries_to_remove = []
        for specialist_id, entry in self._entries.items():
            if entry.graveyarded_at < cutoff:
                entries_to_remove.append(specialist_id)

        for specialist_id in entries_to_remove:
            del self._entries[specialist_id]
            removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old graveyard entries (>{days} days)")

            # Also clean from database
            await self._cleanup_db(cutoff)

        return removed

    # -------------------------------------------------------------------------
    # Learning Management
    # -------------------------------------------------------------------------

    async def _update_domain_learnings(
        self,
        domain: str,
        new_learnings: List[Learning],
    ) -> None:
        """Update the domain learnings cache."""
        if domain not in self._domain_learnings:
            self._domain_learnings[domain] = []

        existing = self._domain_learnings[domain]

        # Add new learnings, avoiding duplicates
        for learning in new_learnings:
            # Check if similar learning exists
            is_duplicate = False
            for existing_learning in existing:
                if self._is_similar_learning(learning, existing_learning):
                    # Boost confidence of existing
                    existing_learning.confidence = min(
                        1.0,
                        existing_learning.confidence + 0.1
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                existing.append(learning)

        # Sort by confidence
        self._domain_learnings[domain] = sorted(
            existing,
            key=lambda l: l.confidence,
            reverse=True,
        )

    def _is_similar_learning(self, a: Learning, b: Learning) -> bool:
        """Check if two learnings are similar."""
        if a.type != b.type:
            return False

        # Simple similarity check (could be enhanced with embeddings)
        a_words = set(a.instruction.lower().split())
        b_words = set(b.instruction.lower().split())

        if not a_words or not b_words:
            return False

        overlap = len(a_words & b_words)
        similarity = overlap / max(len(a_words), len(b_words))

        return similarity > 0.7

    def mark_learning_applied(
        self,
        learning_id: UUID,
        domain: str,
    ) -> None:
        """Mark a learning as applied to a new specialist."""
        for learning in self._domain_learnings.get(domain, []):
            if learning.id == learning_id:
                learning.times_applied += 1
                break

    def update_learning_effectiveness(
        self,
        learning_id: UUID,
        domain: str,
        effectiveness: float,
    ) -> None:
        """Update effectiveness metric for a learning."""
        for learning in self._domain_learnings.get(domain, []):
            if learning.id == learning_id:
                # Running average
                if learning.effectiveness is None:
                    learning.effectiveness = effectiveness
                else:
                    learning.effectiveness = (
                        learning.effectiveness * 0.8 + effectiveness * 0.2
                    )
                break

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    async def _save(self, entry: GraveyardEntry) -> None:
        """Save entry to database."""
        if self._db_session is None:
            return

        try:
            from database.models import GraveyardEntryDB

            db_entry = GraveyardEntryDB.from_graveyard_entry(entry)
            self._db_session.add(db_entry)
            await self._db_session.commit()

        except ImportError:
            logger.debug("Database models not available")
        except Exception as e:
            logger.error(f"Failed to persist graveyard entry: {e}")

    async def _cleanup_db(self, cutoff: datetime) -> None:
        """Clean old entries from database."""
        if self._db_session is None:
            return

        try:
            from database.models import GraveyardEntryDB
            from sqlalchemy import delete

            stmt = delete(GraveyardEntryDB).where(
                GraveyardEntryDB.graveyarded_at < cutoff
            )
            await self._db_session.execute(stmt)
            await self._db_session.commit()

        except Exception as e:
            logger.error(f"Failed to cleanup database: {e}")

    async def load_from_db(self) -> int:
        """Load entries from database."""
        if self._db_session is None:
            return 0

        try:
            from database.models import GraveyardEntryDB
            from sqlalchemy import select

            stmt = select(GraveyardEntryDB)
            result = await self._db_session.execute(stmt)
            rows = result.scalars().all()

            count = 0
            for row in rows:
                entry = row.to_graveyard_entry()
                self._entries[entry.specialist_id] = entry

                # Update domain learnings
                for learning in entry.learnings:
                    if entry.domain not in self._domain_learnings:
                        self._domain_learnings[entry.domain] = []
                    self._domain_learnings[entry.domain].append(learning)

                count += 1

            logger.info(f"Loaded {count} graveyard entries from database")
            return count

        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
            return 0

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get graveyard statistics."""
        entries = list(self._entries.values())

        if not entries:
            return {
                "total_entries": 0,
                "domains": {},
                "avg_score_at_death": 0,
                "total_learnings": 0,
            }

        # Group by domain
        domain_counts: Dict[str, int] = {}
        for entry in entries:
            domain_counts[entry.domain] = domain_counts.get(entry.domain, 0) + 1

        # Calculate averages
        avg_score = sum(e.final_avg_score for e in entries) / len(entries)
        avg_tasks = sum(e.total_tasks for e in entries) / len(entries)
        avg_lifespan = sum(e.lifespan_hours for e in entries) / len(entries)

        # Count learnings
        total_learnings = sum(
            len(learnings)
            for learnings in self._domain_learnings.values()
        )

        # Pattern breakdown
        pattern_counts: Dict[str, int] = {}
        for entry in entries:
            for pattern in entry.failure_patterns:
                cat = pattern.category.value
                pattern_counts[cat] = pattern_counts.get(cat, 0) + 1

        return {
            "total_entries": len(entries),
            "domains": domain_counts,
            "avg_score_at_death": round(avg_score, 3),
            "avg_tasks_completed": round(avg_tasks, 1),
            "avg_lifespan_hours": round(avg_lifespan, 1),
            "total_learnings": total_learnings,
            "pattern_breakdown": pattern_counts,
            "initialized_at": self._initialized_at.isoformat(),
        }


# ============================================================================
# Singleton Instance
# ============================================================================


_graveyard: Optional[Graveyard] = None


def get_graveyard() -> Graveyard:
    """Get the global graveyard instance."""
    global _graveyard
    if _graveyard is None:
        _graveyard = Graveyard()
    return _graveyard


def reset_graveyard() -> None:
    """Reset the global graveyard (for testing)."""
    global _graveyard
    _graveyard = None
