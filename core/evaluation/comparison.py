"""
PHASE 7.5: Evaluation Comparison Tracker

Enhanced comparison tracking between Scoring Committee and AI Council.
Includes Pearson correlation, standard deviation, and database persistence.

Usage:
    from core.evaluation.comparison import (
        ComparisonRecord,
        EnhancedComparisonStats,
        EnhancedComparisonTracker,
    )

    tracker = EnhancedComparisonTracker()
    await tracker.record(task_id, sc_result, ac_result)
    stats = tracker.get_stats()
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .base import EvaluationResult


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Comparison Record
# ============================================================================


class ComparisonRecord(BaseModel):
    """
    A single comparison between SC and AC evaluations.

    Stores both scores and component-level details for analysis.
    """

    id: UUID = Field(default_factory=uuid4)
    task_id: UUID

    # Scores
    sc_score: float = Field(..., ge=0.0, le=1.0)
    ac_score: float = Field(..., ge=0.0, le=1.0)
    difference: float = Field(description="ac_score - sc_score (positive = AC more lenient)")

    # Agreement
    agreement: bool = Field(description="Within threshold")
    agreement_threshold: float = 0.1

    # Component details
    sc_components: Dict[str, float] = Field(default_factory=dict)
    ac_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Confidence
    sc_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    ac_confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        task_id: UUID,
        sc_result: EvaluationResult,
        ac_result: EvaluationResult,
        threshold: float = 0.1,
    ) -> "ComparisonRecord":
        """Create comparison from two evaluation results."""
        diff = ac_result.score - sc_result.score  # Positive = AC more lenient

        return cls(
            task_id=task_id,
            sc_score=sc_result.score,
            ac_score=ac_result.score,
            difference=diff,
            agreement=abs(diff) <= threshold,
            agreement_threshold=threshold,
            sc_components=sc_result.components,
            ac_metadata=ac_result.metadata,
            sc_confidence=sc_result.confidence,
            ac_confidence=ac_result.confidence,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "sc_score": round(self.sc_score, 4),
            "ac_score": round(self.ac_score, 4),
            "difference": round(self.difference, 4),
            "agreement": self.agreement,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# Enhanced Comparison Statistics
# ============================================================================


class EnhancedComparisonStats(BaseModel):
    """
    Enhanced statistics on SC vs AC agreement.

    Includes Pearson correlation for measuring linear relationship
    between evaluator scores.
    """

    total_comparisons: int = 0
    agreement_rate: float = Field(
        default=0.0,
        description="Fraction of comparisons within threshold",
    )
    correlation: float = Field(
        default=0.0,
        description="Pearson correlation coefficient (-1 to 1)",
    )
    mean_difference: float = Field(
        default=0.0,
        description="Mean of (AC - SC), positive = AC more lenient",
    )
    std_difference: float = Field(
        default=0.0,
        description="Standard deviation of differences",
    )

    # Additional stats
    agreements: int = 0
    disagreements: int = 0
    max_difference: float = 0.0
    min_difference: float = 0.0
    sc_higher_count: int = Field(default=0, description="Times SC scored higher")
    ac_higher_count: int = Field(default=0, description="Times AC scored higher")
    equal_count: int = Field(default=0, description="Times scores were equal")

    # Score ranges
    sc_mean: float = 0.0
    sc_std: float = 0.0
    ac_mean: float = 0.0
    ac_std: float = 0.0

    def to_summary(self) -> Dict[str, Any]:
        """Get summary for dashboard display."""
        return {
            "total": self.total_comparisons,
            "agreement_rate": f"{self.agreement_rate * 100:.1f}%",
            "correlation": round(self.correlation, 3),
            "mean_diff": f"{self.mean_difference:+.3f}",
            "bias": "AC lenient" if self.mean_difference > 0.02 else
                    "SC lenient" if self.mean_difference < -0.02 else "neutral",
            "sc_higher": self.sc_higher_count,
            "ac_higher": self.ac_higher_count,
        }


# ============================================================================
# Enhanced Comparison Tracker
# ============================================================================


class EnhancedComparisonTracker:
    """
    Track and analyze comparisons between Scoring Committee and AI Council.

    Features:
    - Records individual comparisons
    - Calculates Pearson correlation
    - Tracks bias direction (which evaluator is more lenient)
    - Supports database persistence

    Usage:
        tracker = EnhancedComparisonTracker()
        await tracker.record(task_id, sc_result, ac_result)

        stats = tracker.get_stats()
        print(f"Correlation: {stats.correlation}")
        print(f"AC bias: {stats.mean_difference:+.3f}")
    """

    def __init__(
        self,
        threshold: float = 0.1,
        db_session: Optional[Any] = None,
    ):
        """
        Initialize the tracker.

        Args:
            threshold: Agreement threshold (within this = "agree")
            db_session: Optional database session for persistence
        """
        self._threshold = threshold
        self._db_session = db_session
        self._comparisons: List[ComparisonRecord] = []

        # Running statistics for incremental updates
        self._sc_sum = 0.0
        self._ac_sum = 0.0
        self._sc_sq_sum = 0.0
        self._ac_sq_sum = 0.0
        self._cross_sum = 0.0
        self._diff_sum = 0.0
        self._diff_sq_sum = 0.0

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def threshold(self) -> float:
        """Get agreement threshold."""
        return self._threshold

    @property
    def comparisons(self) -> List[ComparisonRecord]:
        """Get all comparisons (copy)."""
        return self._comparisons.copy()

    @property
    def count(self) -> int:
        """Get number of comparisons recorded."""
        return len(self._comparisons)

    # -------------------------------------------------------------------------
    # Recording
    # -------------------------------------------------------------------------

    async def record(
        self,
        task_id: UUID,
        sc_result: EvaluationResult,
        ac_result: EvaluationResult,
    ) -> ComparisonRecord:
        """
        Record a comparison between evaluators.

        Args:
            task_id: Task that was evaluated
            sc_result: Scoring Committee result
            ac_result: AI Council result

        Returns:
            The comparison record
        """
        comparison = ComparisonRecord.create(
            task_id=task_id,
            sc_result=sc_result,
            ac_result=ac_result,
            threshold=self._threshold,
        )

        # Update running statistics
        sc = sc_result.score
        ac = ac_result.score
        diff = comparison.difference

        self._sc_sum += sc
        self._ac_sum += ac
        self._sc_sq_sum += sc * sc
        self._ac_sq_sum += ac * ac
        self._cross_sum += sc * ac
        self._diff_sum += diff
        self._diff_sq_sum += diff * diff

        # Store comparison
        self._comparisons.append(comparison)

        # Persist to database if session available
        if self._db_session:
            await self._persist_comparison(comparison)

        logger.info(
            f"Recorded comparison for task {task_id}: "
            f"SC={sc:.3f}, AC={ac:.3f}, diff={diff:+.3f}, "
            f"agree={comparison.agreement}"
        )

        return comparison

    async def _persist_comparison(self, comparison: ComparisonRecord) -> None:
        """Persist comparison to database."""
        try:
            from database.models import EvaluationComparisonDB

            db_record = EvaluationComparisonDB(
                id=comparison.id,
                task_id=comparison.task_id,
                sc_score=comparison.sc_score,
                ac_score=comparison.ac_score,
                difference=comparison.difference,
                agreement=comparison.agreement,
                sc_components=comparison.sc_components,
                ac_metadata=comparison.ac_metadata,
                created_at=comparison.created_at,
            )

            self._db_session.add(db_record)
            await self._db_session.commit()

        except ImportError:
            logger.debug("Database models not available for persistence")
        except Exception as e:
            logger.error(f"Failed to persist comparison: {e}")

    # -------------------------------------------------------------------------
    # Statistics Calculation
    # -------------------------------------------------------------------------

    def get_stats(self) -> EnhancedComparisonStats:
        """
        Calculate comprehensive comparison statistics.

        Returns:
            EnhancedComparisonStats with correlation, bias direction, etc.
        """
        n = len(self._comparisons)

        if n == 0:
            return EnhancedComparisonStats()

        # Basic counts
        agreements = sum(1 for c in self._comparisons if c.agreement)
        disagreements = n - agreements

        # Score comparisons
        sc_higher = sum(1 for c in self._comparisons if c.difference < 0)
        ac_higher = sum(1 for c in self._comparisons if c.difference > 0)
        equal = sum(1 for c in self._comparisons if c.difference == 0)

        # Difference statistics
        differences = [c.difference for c in self._comparisons]
        mean_diff = self._diff_sum / n
        var_diff = (self._diff_sq_sum / n) - (mean_diff * mean_diff)
        std_diff = math.sqrt(max(0, var_diff))

        # Score means and stds
        sc_mean = self._sc_sum / n
        ac_mean = self._ac_sum / n
        sc_var = (self._sc_sq_sum / n) - (sc_mean * sc_mean)
        ac_var = (self._ac_sq_sum / n) - (ac_mean * ac_mean)
        sc_std = math.sqrt(max(0, sc_var))
        ac_std = math.sqrt(max(0, ac_var))

        # Pearson correlation
        correlation = self._calculate_pearson_correlation(n)

        return EnhancedComparisonStats(
            total_comparisons=n,
            agreement_rate=agreements / n if n > 0 else 0.0,
            correlation=correlation,
            mean_difference=mean_diff,
            std_difference=std_diff,
            agreements=agreements,
            disagreements=disagreements,
            max_difference=max(differences) if differences else 0.0,
            min_difference=min(differences) if differences else 0.0,
            sc_higher_count=sc_higher,
            ac_higher_count=ac_higher,
            equal_count=equal,
            sc_mean=sc_mean,
            sc_std=sc_std,
            ac_mean=ac_mean,
            ac_std=ac_std,
        )

    def _calculate_pearson_correlation(self, n: int) -> float:
        """
        Calculate Pearson correlation coefficient.

        Formula: r = (n*Σxy - Σx*Σy) / sqrt((n*Σx² - (Σx)²) * (n*Σy² - (Σy)²))

        Returns:
            Correlation coefficient between -1 and 1
        """
        if n < 2:
            return 0.0

        numerator = (n * self._cross_sum) - (self._sc_sum * self._ac_sum)

        sc_term = (n * self._sc_sq_sum) - (self._sc_sum * self._sc_sum)
        ac_term = (n * self._ac_sq_sum) - (self._ac_sum * self._ac_sum)

        denominator = math.sqrt(max(0, sc_term) * max(0, ac_term))

        if denominator == 0:
            return 0.0

        correlation = numerator / denominator

        # Clamp to [-1, 1] to handle floating point errors
        return max(-1.0, min(1.0, correlation))

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_recent(self, count: int = 100) -> List[ComparisonRecord]:
        """Get most recent comparisons."""
        return self._comparisons[-count:]

    def get_disagreements(self) -> List[ComparisonRecord]:
        """Get all disagreements."""
        return [c for c in self._comparisons if not c.agreement]

    def get_largest_disagreements(self, count: int = 10) -> List[ComparisonRecord]:
        """Get comparisons with largest absolute differences."""
        sorted_comps = sorted(
            self._comparisons,
            key=lambda c: abs(c.difference),
            reverse=True,
        )
        return sorted_comps[:count]

    def get_by_task(self, task_id: UUID) -> Optional[ComparisonRecord]:
        """Get comparison for a specific task."""
        for c in self._comparisons:
            if c.task_id == task_id:
                return c
        return None

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all tracked data."""
        self._comparisons.clear()
        self._sc_sum = 0.0
        self._ac_sum = 0.0
        self._sc_sq_sum = 0.0
        self._ac_sq_sum = 0.0
        self._cross_sum = 0.0
        self._diff_sum = 0.0
        self._diff_sq_sum = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Get tracker state as dictionary."""
        stats = self.get_stats()
        return {
            "threshold": self._threshold,
            "comparison_count": len(self._comparisons),
            "stats": stats.model_dump(),
        }


# ============================================================================
# Singleton Instance
# ============================================================================


_comparison_tracker: Optional[EnhancedComparisonTracker] = None


def get_comparison_tracker() -> EnhancedComparisonTracker:
    """Get the global comparison tracker."""
    global _comparison_tracker
    if _comparison_tracker is None:
        _comparison_tracker = EnhancedComparisonTracker()
    return _comparison_tracker


def reset_comparison_tracker() -> None:
    """Reset the global comparison tracker (for testing)."""
    global _comparison_tracker
    _comparison_tracker = None
