"""
PHASE 7.4: Specialist Model

Specialists are agent configurations optimized for specific domains.
Each domain has multiple specialists competing, with the best performers
handling tasks and poor performers being culled to the graveyard.

The best specialist for the "administration" domain becomes JARVIS
(the user-facing personality).

Usage:
    from core.specialists import Specialist, SpecialistConfig, SpecialistStatus

    # Create a new specialist
    config = SpecialistConfig(
        system_prompt="You are an expert code reviewer...",
        temperature=0.3,
        tools_enabled=["code_search", "file_read"],
    )

    specialist = Specialist(
        domain="code_review",
        name="CodeReview_v1",
        config=config,
    )

    # Record task performance
    specialist.record_score(0.85)
    specialist.record_score(0.92)

    print(f"Avg score: {specialist.get_avg_score()}")
    print(f"Trend: {specialist.performance.trend}")
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class SpecialistStatus(str, Enum):
    """Status of a specialist in the system."""
    ACTIVE = "active"         # In the pool, receiving tasks
    PROBATION = "probation"   # New, being evaluated (limited task allocation)
    GRAVEYARD = "graveyard"   # Culled due to poor performance
    RETIRED = "retired"       # Manually retired (not culled)


class TrendDirection(str, Enum):
    """Performance trend direction."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


# ============================================================================
# Configuration Models
# ============================================================================


class SpecialistConfig(BaseModel):
    """
    Configuration that defines a specialist's behavior.

    This is the "DNA" of the specialist - what makes it unique
    and how it approaches tasks.
    """

    # Core behavior
    system_prompt: str = Field(
        ...,
        min_length=10,
        description="The system prompt that defines this specialist's personality and approach",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0=deterministic, 1=creative)",
    )

    # Tool configuration
    tools_enabled: List[str] = Field(
        default_factory=list,
        description="List of tool names this specialist can use",
    )
    tools_required: List[str] = Field(
        default_factory=list,
        description="Tools that must be available for this specialist to work",
    )

    # Learning from failures
    avoid_patterns: List[str] = Field(
        default_factory=list,
        description="Patterns/approaches to avoid (injected from graveyard learnings)",
    )
    learned_techniques: List[str] = Field(
        default_factory=list,
        description="Successful techniques learned from high-scoring tasks",
    )

    # Model preferences (hints, not requirements)
    preferred_model_tier: str = Field(
        default="high",
        description="Preferred model tier (low/medium/high)",
    )
    min_model_tier: str = Field(
        default="low",
        description="Minimum acceptable model tier",
    )

    # Retry behavior
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on failure",
    )
    retry_temperature_bump: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Temperature increase on each retry",
    )

    # Response constraints
    max_response_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens in response (None = no limit)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpecialistConfig":
        """Create from dictionary."""
        return cls(**data)


# ============================================================================
# Performance Tracking
# ============================================================================


class PerformanceStats(BaseModel):
    """
    Tracked performance metrics for a specialist.

    Metrics are used to determine which specialists receive tasks
    and which get culled to the graveyard.
    """

    # Counts
    task_count: int = Field(default=0, ge=0)
    success_count: int = Field(default=0, ge=0)
    failure_count: int = Field(default=0, ge=0)

    # Scores
    total_score: float = Field(default=0.0, ge=0.0)
    avg_score: float = Field(default=0.0, ge=0.0, le=1.0)
    recent_scores: List[float] = Field(
        default_factory=list,
        description="Last 20 scores for trend calculation",
    )

    # Extremes
    best_score: float = Field(default=0.0, ge=0.0, le=1.0)
    worst_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # Trend
    trend: TrendDirection = Field(default=TrendDirection.STABLE)

    # Timing
    last_task_at: Optional[datetime] = None
    avg_response_time_ms: float = Field(default=0.0, ge=0.0)

    # Cost tracking
    total_cost_cad: float = Field(default=0.0, ge=0.0)
    avg_cost_per_task_cad: float = Field(default=0.0, ge=0.0)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.task_count == 0:
            return 0.0
        return self.success_count / self.task_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = self.model_dump()
        if data.get("last_task_at"):
            data["last_task_at"] = data["last_task_at"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceStats":
        """Create from dictionary."""
        if data.get("last_task_at") and isinstance(data["last_task_at"], str):
            data["last_task_at"] = datetime.fromisoformat(data["last_task_at"])
        # Handle old trend format
        if isinstance(data.get("trend"), str):
            data["trend"] = TrendDirection(data["trend"])
        return cls(**data)


# ============================================================================
# Specialist Model
# ============================================================================


class Specialist(BaseModel):
    """
    An agent configuration optimized for a specific domain.

    Specialists compete within their domain - the best performers
    get more tasks, while poor performers are culled to the graveyard.

    The graveyard isn't just storage - it's a learning repository.
    New specialists inherit "avoid_patterns" from culled predecessors,
    learning from their failures.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4)
    domain: str = Field(
        ...,
        min_length=1,
        description="Domain this specialist is optimized for",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Unique name within domain (e.g., 'Code_v3')",
    )

    # Configuration
    config: SpecialistConfig

    # Lineage
    generation: int = Field(
        default=1,
        ge=1,
        description="Generation number (increments with evolution)",
    )
    parent_id: Optional[UUID] = Field(
        default=None,
        description="ID of parent specialist (if evolved from another)",
    )

    # Status
    status: SpecialistStatus = Field(default=SpecialistStatus.PROBATION)

    # Performance
    performance: PerformanceStats = Field(default_factory=PerformanceStats)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    promoted_at: Optional[datetime] = Field(
        default=None,
        description="When promoted from probation to active",
    )
    culled_at: Optional[datetime] = Field(
        default=None,
        description="When moved to graveyard",
    )

    # Metadata
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization",
    )
    notes: str = Field(
        default="",
        description="Free-form notes about this specialist",
    )

    class Config:
        use_enum_values = False  # Keep enums as enum objects

    # -------------------------------------------------------------------------
    # Score Recording
    # -------------------------------------------------------------------------

    def record_score(
        self,
        score: float,
        success: bool = True,
        response_time_ms: float = 0.0,
        cost_cad: float = 0.0,
    ) -> None:
        """
        Record a new task score and update all statistics.

        Args:
            score: Task score (0.0 to 1.0)
            success: Whether the task completed successfully
            response_time_ms: Response time in milliseconds
            cost_cad: Cost of this task in CAD
        """
        # Clamp score to valid range
        score = max(0.0, min(1.0, score))

        perf = self.performance

        # Update counts
        perf.task_count += 1
        if success:
            perf.success_count += 1
        else:
            perf.failure_count += 1

        # Update scores
        perf.total_score += score
        perf.avg_score = perf.total_score / perf.task_count

        # Keep last 20 scores for trend
        perf.recent_scores.append(score)
        if len(perf.recent_scores) > 20:
            perf.recent_scores.pop(0)

        # Update best/worst
        perf.best_score = max(perf.best_score, score)
        perf.worst_score = min(perf.worst_score, score)

        # Update timing
        perf.last_task_at = datetime.utcnow()
        if response_time_ms > 0:
            # Running average
            old_total = perf.avg_response_time_ms * (perf.task_count - 1)
            perf.avg_response_time_ms = (old_total + response_time_ms) / perf.task_count

        # Update cost
        perf.total_cost_cad += cost_cad
        perf.avg_cost_per_task_cad = perf.total_cost_cad / perf.task_count

        # Calculate trend
        perf.trend = self._calculate_trend()

        # Update timestamp
        self.updated_at = datetime.utcnow()

    def _calculate_trend(self) -> TrendDirection:
        """
        Calculate performance trend based on recent scores.

        Compares the average of the last 5 scores to the previous 5.
        """
        scores = self.performance.recent_scores

        if len(scores) < 10:
            return TrendDirection.STABLE

        # Compare recent 5 vs previous 5
        recent_5 = scores[-5:]
        previous_5 = scores[-10:-5]

        recent_avg = sum(recent_5) / len(recent_5)
        previous_avg = sum(previous_5) / len(previous_5)

        diff = recent_avg - previous_avg

        # Threshold for change detection
        threshold = 0.05

        if diff > threshold:
            return TrendDirection.IMPROVING
        elif diff < -threshold:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE

    # -------------------------------------------------------------------------
    # Status Transitions
    # -------------------------------------------------------------------------

    def promote(self) -> None:
        """Promote from probation to active status."""
        if self.status == SpecialistStatus.PROBATION:
            self.status = SpecialistStatus.ACTIVE
            self.promoted_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            logger.info(f"Promoted specialist {self.name} to active")

    def cull(self, reason: str = "") -> None:
        """Move to graveyard due to poor performance."""
        if self.status in (SpecialistStatus.ACTIVE, SpecialistStatus.PROBATION):
            self.status = SpecialistStatus.GRAVEYARD
            self.culled_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            if reason:
                self.notes = f"{self.notes}\nCulled: {reason}".strip()
            logger.info(f"Culled specialist {self.name}: {reason}")

    def retire(self, reason: str = "") -> None:
        """Manually retire (not due to poor performance)."""
        if self.status != SpecialistStatus.GRAVEYARD:
            self.status = SpecialistStatus.RETIRED
            self.updated_at = datetime.utcnow()
            if reason:
                self.notes = f"{self.notes}\nRetired: {reason}".strip()
            logger.info(f"Retired specialist {self.name}: {reason}")

    def reactivate(self) -> None:
        """Reactivate a retired or graveyard specialist (rare)."""
        if self.status in (SpecialistStatus.GRAVEYARD, SpecialistStatus.RETIRED):
            self.status = SpecialistStatus.PROBATION
            self.culled_at = None
            self.updated_at = datetime.utcnow()
            logger.info(f"Reactivated specialist {self.name}")

    # -------------------------------------------------------------------------
    # Queries
    # -------------------------------------------------------------------------

    def get_avg_score(self) -> float:
        """Get average score across all tasks."""
        return self.performance.avg_score

    def get_recent_avg_score(self, n: int = 5) -> float:
        """Get average of last N scores."""
        scores = self.performance.recent_scores
        if not scores:
            return 0.0
        recent = scores[-n:] if len(scores) >= n else scores
        return sum(recent) / len(recent)

    def is_eligible_for_tasks(self) -> bool:
        """Check if specialist can receive new tasks."""
        return self.status in (SpecialistStatus.ACTIVE, SpecialistStatus.PROBATION)

    def should_be_culled(
        self,
        min_score: float = 0.4,
        min_tasks: int = 5,
    ) -> bool:
        """
        Check if specialist should be culled based on performance.

        Args:
            min_score: Minimum acceptable average score
            min_tasks: Minimum tasks before culling can occur

        Returns:
            True if specialist should be culled
        """
        perf = self.performance

        # Need minimum tasks before culling
        if perf.task_count < min_tasks:
            return False

        # Check average score
        if perf.avg_score < min_score:
            return True

        # Check declining trend with poor recent performance
        if perf.trend == TrendDirection.DECLINING:
            recent_avg = self.get_recent_avg_score(5)
            if recent_avg < min_score:
                return True

        return False

    def should_be_promoted(
        self,
        min_score: float = 0.7,
        min_tasks: int = 3,
    ) -> bool:
        """
        Check if specialist should be promoted from probation.

        Args:
            min_score: Minimum average score for promotion
            min_tasks: Minimum tasks before promotion can occur

        Returns:
            True if specialist should be promoted
        """
        if self.status != SpecialistStatus.PROBATION:
            return False

        perf = self.performance

        # Need minimum tasks
        if perf.task_count < min_tasks:
            return False

        # Check average score
        return perf.avg_score >= min_score

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "id": str(self.id),
            "domain": self.domain,
            "name": self.name,
            "config": json.dumps(self.config.to_dict()),
            "generation": self.generation,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "status": self.status.value,
            "performance": json.dumps(self.performance.to_dict()),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "promoted_at": self.promoted_at,
            "culled_at": self.culled_at,
            "tags": json.dumps(self.tags),
            "notes": self.notes,
        }

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> "Specialist":
        """Create from database row."""
        return cls(
            id=UUID(row["id"]) if isinstance(row["id"], str) else row["id"],
            domain=row["domain"],
            name=row["name"],
            config=SpecialistConfig.from_dict(
                json.loads(row["config"]) if isinstance(row["config"], str) else row["config"]
            ),
            generation=row["generation"],
            parent_id=UUID(row["parent_id"]) if row.get("parent_id") else None,
            status=SpecialistStatus(row["status"]),
            performance=PerformanceStats.from_dict(
                json.loads(row["performance"]) if isinstance(row["performance"], str) else row["performance"]
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            promoted_at=row.get("promoted_at"),
            culled_at=row.get("culled_at"),
            tags=json.loads(row["tags"]) if isinstance(row.get("tags"), str) else (row.get("tags") or []),
            notes=row.get("notes", ""),
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "Specialist":
        """Create from JSON string."""
        return cls.model_validate_json(json_str)


# ============================================================================
# Factory Functions
# ============================================================================


def create_specialist(
    domain: str,
    system_prompt: str,
    name: Optional[str] = None,
    generation: int = 1,
    temperature: float = 0.7,
    tools: Optional[List[str]] = None,
    avoid_patterns: Optional[List[str]] = None,
    parent_id: Optional[UUID] = None,
    **kwargs,
) -> Specialist:
    """
    Factory function to create a new specialist.

    Args:
        domain: Domain this specialist handles
        system_prompt: The specialist's system prompt
        name: Optional name (auto-generated if not provided)
        generation: Generation number
        temperature: Sampling temperature
        tools: List of enabled tools
        avoid_patterns: Patterns to avoid (from graveyard)
        parent_id: Parent specialist ID (if evolved)
        **kwargs: Additional config options

    Returns:
        New Specialist instance
    """
    # Auto-generate name if not provided
    if name is None:
        name = f"{domain.title().replace(' ', '')}_v{generation}"

    config = SpecialistConfig(
        system_prompt=system_prompt,
        temperature=temperature,
        tools_enabled=tools or [],
        avoid_patterns=avoid_patterns or [],
        **kwargs,
    )

    return Specialist(
        domain=domain,
        name=name,
        config=config,
        generation=generation,
        parent_id=parent_id,
    )


def evolve_specialist(
    parent: Specialist,
    system_prompt: Optional[str] = None,
    temperature_delta: float = 0.0,
    additional_patterns: Optional[List[str]] = None,
    additional_techniques: Optional[List[str]] = None,
) -> Specialist:
    """
    Create a new specialist evolved from a parent.

    Args:
        parent: Parent specialist to evolve from
        system_prompt: New system prompt (or inherit from parent)
        temperature_delta: Change in temperature
        additional_patterns: New patterns to avoid
        additional_techniques: New techniques learned

    Returns:
        New evolved Specialist instance
    """
    # Build new config based on parent
    new_config = SpecialistConfig(
        system_prompt=system_prompt or parent.config.system_prompt,
        temperature=max(0.0, min(2.0, parent.config.temperature + temperature_delta)),
        tools_enabled=parent.config.tools_enabled.copy(),
        tools_required=parent.config.tools_required.copy(),
        avoid_patterns=parent.config.avoid_patterns + (additional_patterns or []),
        learned_techniques=parent.config.learned_techniques + (additional_techniques or []),
        preferred_model_tier=parent.config.preferred_model_tier,
        min_model_tier=parent.config.min_model_tier,
        max_retries=parent.config.max_retries,
    )

    new_generation = parent.generation + 1
    new_name = f"{parent.domain.title().replace(' ', '')}_v{new_generation}"

    return Specialist(
        domain=parent.domain,
        name=new_name,
        config=new_config,
        generation=new_generation,
        parent_id=parent.id,
        tags=parent.tags.copy(),
    )
