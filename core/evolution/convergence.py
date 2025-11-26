"""
PHASE 7.5: Convergence Detection

Detects when evolution should pause because the domain has reached
a stable, high-quality state.

Usage:
    from core.evolution import ConvergenceDetector, ConvergenceResult

    detector = ConvergenceDetector()
    result = detector.check(pool)

    if result.has_converged:
        print(f"Evolution converged: {result.reasons}")
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.specialists.pool import DomainPool


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Convergence Result Model
# ============================================================================


class ConvergenceResult(BaseModel):
    """
    Result of convergence check.

    Convergence means evolution can pause - the domain is "good enough".
    """

    has_converged: bool = Field(
        default=False,
        description="Whether all convergence conditions are met",
    )
    variance: float = Field(
        default=1.0,
        ge=0.0,
        description="Score variance among specialists",
    )
    generations_without_improvement: int = Field(
        default=0,
        ge=0,
        description="How many generations without score improvement",
    )
    best_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Current best score in pool",
    )
    mean_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Mean score across specialists",
    )
    reasons: List[str] = Field(
        default_factory=list,
        description="Conditions that are currently met",
    )
    conditions_met: int = Field(
        default=0,
        ge=0,
        description="Number of convergence conditions met",
    )
    conditions_total: int = Field(
        default=3,
        ge=1,
        description="Total conditions required for convergence",
    )
    checked_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "has_converged": self.has_converged,
            "variance": round(self.variance, 4),
            "generations_stagnant": self.generations_without_improvement,
            "best_score": round(self.best_score, 3),
            "mean_score": round(self.mean_score, 3),
            "conditions_met": f"{self.conditions_met}/{self.conditions_total}",
            "reasons": self.reasons,
        }


# ============================================================================
# Convergence Progress Model
# ============================================================================


class ConvergenceProgress(BaseModel):
    """
    Progress toward convergence.

    Shows how close the domain is to converging.
    """

    domain: str
    generation: int = 0

    # Variance progress
    current_variance: float = 1.0
    target_variance: float = 0.02
    variance_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="0-1 progress toward variance target",
    )

    # Stagnation progress
    stagnant_generations: int = 0
    target_stagnation: int = 10
    stagnation_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    # Quality progress
    current_best_score: float = 0.0
    target_score: float = 0.85
    quality_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    # Overall
    overall_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average of all progress metrics",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "generation": self.generation,
            "overall_progress": f"{self.overall_progress * 100:.1f}%",
            "variance": {
                "current": round(self.current_variance, 4),
                "target": self.target_variance,
                "progress": f"{self.variance_progress * 100:.1f}%",
            },
            "stagnation": {
                "current": self.stagnant_generations,
                "target": self.target_stagnation,
                "progress": f"{self.stagnation_progress * 100:.1f}%",
            },
            "quality": {
                "current": round(self.current_best_score, 3),
                "target": self.target_score,
                "progress": f"{self.quality_progress * 100:.1f}%",
            },
        }


# ============================================================================
# Convergence Configuration
# ============================================================================


class ConvergenceConfig(BaseModel):
    """Configuration for convergence detection."""

    # Variance threshold - how similar specialists must be
    variance_threshold: float = Field(
        default=0.02,
        gt=0.0,
        le=1.0,
        description="Max variance for convergence",
    )

    # Stagnation threshold - generations without improvement
    stagnation_threshold: int = Field(
        default=10,
        ge=1,
        description="Generations without improvement to consider stagnant",
    )

    # Quality threshold - minimum best score
    quality_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Minimum best score for convergence",
    )

    # Improvement threshold - what counts as "improvement"
    improvement_threshold: float = Field(
        default=0.01,
        gt=0.0,
        description="Score increase to count as improvement",
    )


# ============================================================================
# Convergence Detector
# ============================================================================


class ConvergenceDetector:
    """
    Detect when evolution should pause.

    Convergence conditions (ALL must be true):
    1. Variance among specialists < threshold (specialists very similar)
    2. No improvement for N generations (stagnation)
    3. Best score > threshold (actually good)

    Usage:
        detector = ConvergenceDetector()
        result = detector.check(pool)

        if result.has_converged:
            pause_evolution(pool.domain)
    """

    def __init__(self, config: Optional[ConvergenceConfig] = None):
        """
        Initialize the detector.

        Args:
            config: Convergence configuration
        """
        self._config = config or ConvergenceConfig()

        # History for tracking improvements
        self._score_history: Dict[str, List[float]] = {}

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> ConvergenceConfig:
        """Get configuration."""
        return self._config

    # -------------------------------------------------------------------------
    # Main Check
    # -------------------------------------------------------------------------

    def check(self, pool: "DomainPool") -> ConvergenceResult:
        """
        Check if a domain pool has converged.

        Args:
            pool: The domain pool to check

        Returns:
            ConvergenceResult with details
        """
        specialists = pool.specialists

        # Need at least 3 specialists
        if len(specialists) < 3:
            return ConvergenceResult(
                has_converged=False,
                variance=1.0,
                generations_without_improvement=0,
                best_score=0.0,
                reasons=["Not enough specialists (need 3)"],
                conditions_met=0,
            )

        # Get scores
        scores = [s.performance.avg_score for s in specialists]

        # Calculate metrics
        variance = self._calculate_variance(scores)
        best_score = max(scores)
        mean_score = sum(scores) / len(scores)
        stagnant_gens = self._count_stagnant_generations(pool)

        # Check each condition
        reasons = []
        conditions_met = 0

        # Condition 1: Low variance
        if variance < self._config.variance_threshold:
            conditions_met += 1
            reasons.append(
                f"Low variance: {variance:.4f} < {self._config.variance_threshold}"
            )

        # Condition 2: Stagnation
        if stagnant_gens >= self._config.stagnation_threshold:
            conditions_met += 1
            reasons.append(
                f"Stagnant: {stagnant_gens} generations without improvement"
            )

        # Condition 3: High quality
        if best_score >= self._config.quality_threshold:
            conditions_met += 1
            reasons.append(
                f"High quality: best score {best_score:.3f} >= {self._config.quality_threshold}"
            )

        has_converged = conditions_met == 3

        if has_converged:
            logger.info(
                f"Domain {pool.domain} has CONVERGED at generation {pool.generation}"
            )

        return ConvergenceResult(
            has_converged=has_converged,
            variance=variance,
            generations_without_improvement=stagnant_gens,
            best_score=best_score,
            mean_score=mean_score,
            reasons=reasons,
            conditions_met=conditions_met,
            conditions_total=3,
        )

    # -------------------------------------------------------------------------
    # Progress Tracking
    # -------------------------------------------------------------------------

    def get_progress(self, pool: "DomainPool") -> ConvergenceProgress:
        """
        Get progress toward convergence.

        Args:
            pool: The domain pool to check

        Returns:
            ConvergenceProgress with detailed metrics
        """
        specialists = pool.specialists

        if len(specialists) < 3:
            return ConvergenceProgress(
                domain=pool.domain,
                generation=pool.generation,
            )

        scores = [s.performance.avg_score for s in specialists]
        variance = self._calculate_variance(scores)
        best_score = max(scores)
        stagnant_gens = self._count_stagnant_generations(pool)

        # Calculate progress percentages
        variance_progress = max(
            0.0,
            1.0 - (variance / self._config.variance_threshold)
        ) if variance > 0 else 1.0

        stagnation_progress = min(
            1.0,
            stagnant_gens / self._config.stagnation_threshold
        )

        quality_progress = min(
            1.0,
            best_score / self._config.quality_threshold
        )

        overall = (variance_progress + stagnation_progress + quality_progress) / 3

        return ConvergenceProgress(
            domain=pool.domain,
            generation=pool.generation,
            current_variance=variance,
            target_variance=self._config.variance_threshold,
            variance_progress=min(1.0, variance_progress),
            stagnant_generations=stagnant_gens,
            target_stagnation=self._config.stagnation_threshold,
            stagnation_progress=stagnation_progress,
            current_best_score=best_score,
            target_score=self._config.quality_threshold,
            quality_progress=quality_progress,
            overall_progress=overall,
        )

    # -------------------------------------------------------------------------
    # History Management
    # -------------------------------------------------------------------------

    def record_generation(self, domain: str, best_score: float) -> None:
        """
        Record the best score for a generation.

        Called after each evolution cycle to track improvements.

        Args:
            domain: The domain
            best_score: Best score this generation
        """
        if domain not in self._score_history:
            self._score_history[domain] = []

        self._score_history[domain].append(best_score)

        # Keep last 50 generations
        if len(self._score_history[domain]) > 50:
            self._score_history[domain] = self._score_history[domain][-50:]

    def clear_history(self, domain: str) -> None:
        """Clear score history for a domain."""
        self._score_history.pop(domain, None)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores."""
        if not scores:
            return 0.0

        n = len(scores)
        if n < 2:
            return 0.0

        mean = sum(scores) / n
        variance = sum((s - mean) ** 2 for s in scores) / n

        return variance

    def _count_stagnant_generations(self, pool: "DomainPool") -> int:
        """
        Count generations without meaningful improvement.

        Returns:
            Number of generations since last improvement
        """
        history = self._score_history.get(pool.domain, [])

        if len(history) < 2:
            return 0

        # Find the last improvement
        threshold = self._config.improvement_threshold
        stagnant = 0

        for i in range(len(history) - 1, 0, -1):
            if history[i] - history[i - 1] >= threshold:
                break
            stagnant += 1

        return stagnant


# ============================================================================
# Singleton Instance
# ============================================================================


_convergence_detector: Optional[ConvergenceDetector] = None


def get_convergence_detector() -> ConvergenceDetector:
    """Get the global convergence detector."""
    global _convergence_detector
    if _convergence_detector is None:
        _convergence_detector = ConvergenceDetector()
    return _convergence_detector


def reset_convergence_detector() -> None:
    """Reset the global convergence detector (for testing)."""
    global _convergence_detector
    _convergence_detector = None
