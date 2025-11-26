"""
Evaluation API Routes

Control and monitor the evaluation system (Scoring Committee vs AI Council).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================


class EvaluationModeRequest(BaseModel):
    """Request to change evaluation mode."""

    mode: Literal["scoring_committee", "ai_council", "both"] = Field(
        ...,
        description="Evaluation mode to set",
    )


class EvaluationModeResponse(BaseModel):
    """Current evaluation mode."""

    mode: str = Field(..., description="Current mode")
    scoring_committee_enabled: bool = Field(default=True)
    ai_council_enabled: bool = Field(default=False)
    comparison_tracking: bool = Field(default=False)
    changed_at: Optional[datetime] = Field(default=None)


class ScoringCommitteeStats(BaseModel):
    """Statistics for Scoring Committee."""

    total_evaluations: int = Field(default=0)
    avg_score: float = Field(default=0.0)
    avg_confidence: float = Field(default=0.0)
    checkers_active: List[str] = Field(default_factory=list)
    recent_scores: List[float] = Field(default_factory=list)


class AICouncilStats(BaseModel):
    """Statistics for AI Council."""

    total_sessions: int = Field(default=0)
    total_votes: int = Field(default=0)
    outliers_removed: int = Field(default=0)
    avg_score: float = Field(default=0.0)
    avg_confidence: float = Field(default=0.0)
    bootstrap_warnings: int = Field(default=0)
    voter_count: int = Field(default=0)


class ComparisonStats(BaseModel):
    """Statistics comparing SC and AC."""

    comparisons_count: int = Field(default=0)
    agreement_rate: float = Field(default=0.0, description="Rate within threshold")
    correlation: float = Field(default=0.0, description="Pearson correlation")
    mean_difference: float = Field(
        default=0.0,
        description="AC - SC (positive = AC more lenient)",
    )
    std_difference: float = Field(default=0.0)
    recent_comparisons: List[Dict[str, Any]] = Field(default_factory=list)


class EvaluationStats(BaseModel):
    """Combined evaluation statistics."""

    mode: str = Field(..., description="Current mode")
    scoring_committee: ScoringCommitteeStats = Field(
        default_factory=ScoringCommitteeStats,
    )
    ai_council: AICouncilStats = Field(
        default_factory=AICouncilStats,
    )
    comparison: Optional[ComparisonStats] = Field(default=None)


# ============================================================================
# Router
# ============================================================================


router = APIRouter(prefix="/api/evaluation", tags=["evaluation"])


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/mode", response_model=EvaluationModeResponse)
async def get_mode():
    """
    Get current evaluation mode.

    Returns the active evaluation configuration.
    """
    try:
        config = _get_evaluation_config()
        return EvaluationModeResponse(
            mode=config.get("mode", "scoring_committee"),
            scoring_committee_enabled=config.get("scoring_committee_enabled", True),
            ai_council_enabled=config.get("ai_council_enabled", False),
            comparison_tracking=config.get("comparison_tracking", False),
            changed_at=config.get("changed_at"),
        )
    except Exception as e:
        logger.error(f"Failed to get evaluation mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode", response_model=EvaluationModeResponse)
async def set_mode(request: EvaluationModeRequest):
    """
    Set evaluation mode.

    Args:
        request: The new evaluation mode to set

    Modes:
    - scoring_committee: Use only Scoring Committee (deterministic, fast)
    - ai_council: Use only AI Council (LLM voting, expensive)
    - both: Run both and track comparisons for analysis
    """
    try:
        new_config = _set_evaluation_mode(request.mode)

        logger.info(f"Evaluation mode changed to: {request.mode}")

        return EvaluationModeResponse(
            mode=new_config.get("mode", request.mode),
            scoring_committee_enabled=new_config.get("scoring_committee_enabled", True),
            ai_council_enabled=new_config.get("ai_council_enabled", False),
            comparison_tracking=new_config.get("comparison_tracking", False),
            changed_at=datetime.utcnow(),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set evaluation mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=EvaluationStats)
async def get_stats():
    """
    Get comprehensive evaluation statistics.

    Returns stats for both evaluators and comparison data if in BOTH mode.
    """
    try:
        mode = _get_evaluation_config().get("mode", "scoring_committee")
        sc_stats = await _get_scoring_committee_stats()
        ac_stats = await _get_ai_council_stats()
        comparison = await _get_comparison_stats() if mode == "both" else None

        return EvaluationStats(
            mode=mode,
            scoring_committee=sc_stats,
            ai_council=ac_stats,
            comparison=comparison,
        )

    except Exception as e:
        logger.error(f"Failed to get evaluation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scoring-committee/stats", response_model=ScoringCommitteeStats)
async def get_scoring_committee_stats():
    """Get Scoring Committee statistics."""
    try:
        return await _get_scoring_committee_stats()
    except Exception as e:
        logger.error(f"Failed to get SC stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-council/stats", response_model=AICouncilStats)
async def get_ai_council_stats():
    """Get AI Council statistics."""
    try:
        return await _get_ai_council_stats()
    except Exception as e:
        logger.error(f"Failed to get AC stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison-stats", response_model=ComparisonStats)
async def get_comparison_stats():
    """
    Get SC vs AC comparison statistics.

    Only available when running in BOTH mode or when historical
    comparison data exists.
    """
    try:
        stats = await _get_comparison_stats()
        if not stats:
            return ComparisonStats(
                comparisons_count=0,
                agreement_rate=0.0,
                correlation=0.0,
                mean_difference=0.0,
                std_difference=0.0,
                recent_comparisons=[],
            )
        return stats

    except Exception as e:
        logger.error(f"Failed to get comparison stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-stats")
async def reset_stats():
    """
    Reset evaluation statistics.

    This clears accumulated statistics but preserves configuration.
    """
    try:
        _reset_evaluation_stats()
        return {"status": "ok", "message": "Statistics reset successfully"}
    except Exception as e:
        logger.error(f"Failed to reset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================


# In-memory config storage (would be persisted in production)
_evaluation_config: Dict[str, Any] = {
    "mode": "scoring_committee",
    "scoring_committee_enabled": True,
    "ai_council_enabled": False,
    "comparison_tracking": False,
    "changed_at": None,
}


def _get_evaluation_config() -> Dict[str, Any]:
    """Get current evaluation configuration."""
    try:
        from core.evaluation import get_evaluation_controller
        controller = get_evaluation_controller()
        mode = controller.mode.value if hasattr(controller.mode, 'value') else str(controller.mode)
        return {
            "mode": mode,
            "scoring_committee_enabled": mode in ("scoring_committee", "both"),
            "ai_council_enabled": mode in ("ai_council", "both"),
            "comparison_tracking": mode == "both",
            "changed_at": getattr(controller, 'changed_at', None),
        }
    except ImportError:
        return _evaluation_config


def _set_evaluation_mode(mode: str) -> Dict[str, Any]:
    """Set evaluation mode."""
    global _evaluation_config

    valid_modes = {"scoring_committee", "ai_council", "both"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode: {mode}. Must be one of {valid_modes}")

    try:
        from core.evaluation import set_evaluation_mode
        set_evaluation_mode(mode)
    except ImportError:
        pass

    # Update local config
    _evaluation_config = {
        "mode": mode,
        "scoring_committee_enabled": mode in ("scoring_committee", "both"),
        "ai_council_enabled": mode in ("ai_council", "both"),
        "comparison_tracking": mode == "both",
        "changed_at": datetime.utcnow(),
    }

    return _evaluation_config


async def _get_scoring_committee_stats() -> ScoringCommitteeStats:
    """Get Scoring Committee statistics."""
    try:
        from core.evaluation import get_scoring_committee
        sc = get_scoring_committee()
        stats = sc.get_stats()

        return ScoringCommitteeStats(
            total_evaluations=stats.get("total_evaluations", 0),
            avg_score=stats.get("avg_score", 0.0),
            avg_confidence=stats.get("avg_confidence", 0.0),
            checkers_active=stats.get("active_checkers", []),
            recent_scores=stats.get("recent_scores", [])[-10:],
        )
    except ImportError:
        return ScoringCommitteeStats()


async def _get_ai_council_stats() -> AICouncilStats:
    """Get AI Council statistics."""
    try:
        from core.evaluation import get_ai_council
        ac = get_ai_council()
        stats = ac.get_stats()

        return AICouncilStats(
            total_sessions=stats.get("total_sessions", 0),
            total_votes=stats.get("total_votes", 0),
            outliers_removed=stats.get("outliers_removed", 0),
            avg_score=stats.get("avg_score", 0.0),
            avg_confidence=stats.get("avg_confidence", 0.0),
            bootstrap_warnings=stats.get("bootstrap_warnings", 0),
            voter_count=stats.get("voter_count", 0),
        )
    except ImportError:
        return AICouncilStats()


async def _get_comparison_stats() -> Optional[ComparisonStats]:
    """Get SC vs AC comparison statistics."""
    try:
        from core.evaluation import get_comparison_tracker
        tracker = get_comparison_tracker()
        stats = tracker.get_stats()

        return ComparisonStats(
            comparisons_count=stats.get("total_comparisons", 0),
            agreement_rate=stats.get("agreement_rate", 0.0),
            correlation=stats.get("correlation", 0.0),
            mean_difference=stats.get("mean_difference", 0.0),
            std_difference=stats.get("std_difference", 0.0),
            recent_comparisons=stats.get("recent_comparisons", [])[-5:],
        )
    except ImportError:
        return None


def _reset_evaluation_stats() -> None:
    """Reset evaluation statistics."""
    try:
        from core.evaluation import (
            get_scoring_committee,
            get_ai_council,
            get_comparison_tracker,
        )

        get_scoring_committee().reset_stats()
        get_ai_council().reset_stats()

        tracker = get_comparison_tracker()
        if tracker:
            tracker.reset_stats()
    except ImportError:
        pass
