"""
PHASE 7.5: AI Council Vote Aggregator

Aggregates votes from multiple specialists with outlier handling.
JARVIS votes are weighted 1.5x.

Usage:
    from core.evaluation.ai_council import VoteAggregator

    aggregator = VoteAggregator()

    # Remove outliers
    filtered = aggregator.remove_outliers(votes)

    # Aggregate to final score
    score = aggregator.aggregate(filtered)
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .voter import Vote


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class AggregationError(Exception):
    """Base error for aggregation issues."""
    pass


class NoVotesError(AggregationError):
    """No votes available to aggregate."""
    pass


class InsufficientVotesError(AggregationError):
    """Not enough votes for reliable aggregation."""
    pass


# ============================================================================
# Aggregation Result
# ============================================================================


class AggregationResult(BaseModel):
    """Result of vote aggregation."""

    final_score: float = Field(ge=0.0, le=1.0)
    total_votes: int
    included_votes: int
    excluded_outliers: int

    # Statistics
    mean_score: float
    median_score: float
    std_deviation: float
    min_score: float
    max_score: float

    # Weights
    total_weight: float
    jarvis_weight_applied: bool

    # Confidence
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the aggregation",
    )

    def to_summary(self) -> Dict[str, Any]:
        """Get summary of aggregation."""
        return {
            "score": round(self.final_score, 3),
            "votes": f"{self.included_votes}/{self.total_votes}",
            "outliers_removed": self.excluded_outliers,
            "confidence": round(self.confidence, 2),
            "std": round(self.std_deviation, 3),
        }


# ============================================================================
# Vote Aggregator
# ============================================================================


class VoteAggregator:
    """
    Aggregate votes with outlier handling.

    Features:
    - JARVIS vote weighted 1.5x
    - Outlier removal (> N std from mean)
    - Confidence calculation based on vote consistency

    Usage:
        aggregator = VoteAggregator(
            jarvis_weight=1.5,
            outlier_threshold_std=2.0,
        )

        filtered_votes = aggregator.remove_outliers(votes)
        result = aggregator.aggregate(filtered_votes)
    """

    def __init__(
        self,
        jarvis_weight: float = 1.5,
        specialist_weight: float = 1.0,
        outlier_threshold_std: float = 2.0,
        min_votes_for_outlier_detection: int = 3,
    ):
        """
        Initialize the aggregator.

        Args:
            jarvis_weight: Weight for JARVIS votes
            specialist_weight: Weight for specialist votes
            outlier_threshold_std: Std deviations for outlier threshold
            min_votes_for_outlier_detection: Min votes needed for outlier detection
        """
        self._jarvis_weight = jarvis_weight
        self._specialist_weight = specialist_weight
        self._outlier_threshold = outlier_threshold_std
        self._min_votes_outlier = min_votes_for_outlier_detection

    # -------------------------------------------------------------------------
    # Main Methods
    # -------------------------------------------------------------------------

    def aggregate(
        self,
        votes: List[Vote],
        include_outliers: bool = False,
    ) -> AggregationResult:
        """
        Aggregate votes to a final score.

        Args:
            votes: List of votes to aggregate
            include_outliers: Whether to include votes marked as outliers

        Returns:
            AggregationResult with final score and statistics

        Raises:
            NoVotesError: If no votes provided
        """
        if not votes:
            raise NoVotesError("No votes to aggregate")

        # Filter outliers if requested
        if not include_outliers:
            included = [v for v in votes if not v.is_outlier]
        else:
            included = votes

        if not included:
            raise NoVotesError("No non-outlier votes to aggregate")

        # Calculate weighted score
        total_weight = 0.0
        weighted_sum = 0.0
        jarvis_weight_applied = False

        for vote in included:
            weight = self._get_vote_weight(vote)
            weighted_sum += vote.score * weight
            total_weight += weight

            if vote.voter_type == "jarvis":
                jarvis_weight_applied = True

        final_score = weighted_sum / total_weight

        # Calculate statistics
        scores = [v.score for v in included]
        stats = self._calculate_statistics(scores)

        # Calculate confidence
        confidence = self._calculate_confidence(
            votes=included,
            std_deviation=stats["std"],
            total_votes=len(votes),
        )

        return AggregationResult(
            final_score=final_score,
            total_votes=len(votes),
            included_votes=len(included),
            excluded_outliers=len(votes) - len(included),
            mean_score=stats["mean"],
            median_score=stats["median"],
            std_deviation=stats["std"],
            min_score=stats["min"],
            max_score=stats["max"],
            total_weight=total_weight,
            jarvis_weight_applied=jarvis_weight_applied,
            confidence=confidence,
        )

    def remove_outliers(
        self,
        votes: List[Vote],
        threshold_std: Optional[float] = None,
    ) -> List[Vote]:
        """
        Remove outlier votes based on standard deviation.

        Args:
            votes: List of votes
            threshold_std: Std deviation threshold (uses default if not provided)

        Returns:
            List of votes with outliers marked (is_outlier=True)
        """
        if len(votes) < self._min_votes_outlier:
            logger.debug(
                f"Not enough votes ({len(votes)}) for outlier detection "
                f"(min: {self._min_votes_outlier})"
            )
            return votes

        threshold = threshold_std or self._outlier_threshold

        # Calculate mean and std
        scores = [v.score for v in votes]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std = math.sqrt(variance)

        if std == 0:
            # All same score - no outliers
            return votes

        # Mark outliers
        result = []
        for vote in votes:
            deviation = abs(vote.score - mean)
            if deviation > threshold * std:
                # Create new vote with outlier flag
                vote_dict = vote.model_dump()
                vote_dict["is_outlier"] = True
                vote_dict["outlier_reason"] = (
                    f"Score {vote.score:.2f} is {deviation/std:.1f} std "
                    f"from mean {mean:.2f}"
                )
                result.append(Vote(**vote_dict))
                logger.info(
                    f"Marked vote from {vote.voter_name or vote.voter_id} as outlier: "
                    f"score={vote.score:.2f}, mean={mean:.2f}, std={std:.2f}"
                )
            else:
                result.append(vote)

        return result

    def get_simple_average(self, votes: List[Vote]) -> float:
        """Get simple unweighted average (for comparison)."""
        if not votes:
            return 0.0
        scores = [v.score for v in votes if not v.is_outlier]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_vote_weight(self, vote: Vote) -> float:
        """Get weight for a vote based on voter type."""
        if vote.voter_type == "jarvis":
            return self._jarvis_weight
        return self._specialist_weight

    def _calculate_statistics(self, scores: List[float]) -> Dict[str, float]:
        """Calculate statistical measures for scores."""
        if not scores:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

        n = len(scores)
        mean = sum(scores) / n

        # Median
        sorted_scores = sorted(scores)
        if n % 2 == 0:
            median = (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
        else:
            median = sorted_scores[n // 2]

        # Standard deviation
        variance = sum((s - mean) ** 2 for s in scores) / n
        std = math.sqrt(variance)

        return {
            "mean": mean,
            "median": median,
            "std": std,
            "min": min(scores),
            "max": max(scores),
        }

    def _calculate_confidence(
        self,
        votes: List[Vote],
        std_deviation: float,
        total_votes: int,
    ) -> float:
        """
        Calculate confidence in the aggregation.

        Higher confidence when:
        - More votes
        - Lower variance (agreement)
        - JARVIS included
        """
        confidence = 0.5  # Base confidence

        # More votes = more confidence (up to +0.2)
        vote_bonus = min(0.2, len(votes) * 0.05)
        confidence += vote_bonus

        # Lower std = more agreement = more confidence (up to +0.2)
        if std_deviation < 0.05:
            agreement_bonus = 0.2
        elif std_deviation < 0.1:
            agreement_bonus = 0.15
        elif std_deviation < 0.15:
            agreement_bonus = 0.1
        else:
            agreement_bonus = 0.0
        confidence += agreement_bonus

        # JARVIS included = more confidence (+0.1)
        if any(v.voter_type == "jarvis" for v in votes):
            confidence += 0.1

        return min(1.0, confidence)
