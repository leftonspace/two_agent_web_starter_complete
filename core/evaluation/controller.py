"""
PHASE 7.5: Evaluation Controller

Toggle-based control for switching between evaluation modes.
User selects mode in dashboard - NO automatic switching.

Modes:
- SCORING_COMMITTEE (default): Deterministic component-weighted scoring
- AI_COUNCIL: Multi-agent deliberation with voting
- BOTH: Run both evaluators, compare results, use SC as authoritative

Usage:
    from core.evaluation import EvaluationController, EvaluationMode

    controller = get_evaluation_controller()

    # Check current mode
    print(f"Current mode: {controller.get_mode()}")

    # Evaluate a task result
    evaluation = await controller.evaluate(task_result)

    # Change mode (user-initiated only)
    controller.set_mode(EvaluationMode.AI_COUNCIL)

    # Get comparison stats (when running in BOTH mode)
    stats = controller.get_comparison_stats()
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

import yaml
from pydantic import BaseModel, Field

from .base import (
    BaseEvaluator,
    EvaluationResult,
    EvaluatorType,
    TaskResult,
    EvaluationComparison,
    ComparisonStats,
    EvaluationStatus,
)

if TYPE_CHECKING:
    pass  # Future evaluator imports

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Evaluation Mode
# ============================================================================


class EvaluationMode(str, Enum):
    """Available evaluation modes."""
    SCORING_COMMITTEE = "scoring_committee"  # Default, production
    AI_COUNCIL = "ai_council"                # Experimental
    BOTH = "both"                            # Run both, compare


# ============================================================================
# Comparison Tracker
# ============================================================================


class ComparisonTracker:
    """
    Track comparisons between Scoring Committee and AI Council.

    Stores comparison results and calculates statistics.
    Used when running in BOTH mode.
    """

    def __init__(self, threshold: float = 0.1):
        """
        Initialize the tracker.

        Args:
            threshold: Agreement threshold (within this = "agree")
        """
        self._threshold = threshold
        self._comparisons: List[EvaluationComparison] = []
        self._stats = ComparisonStats()

    @property
    def threshold(self) -> float:
        """Get agreement threshold."""
        return self._threshold

    @property
    def stats(self) -> ComparisonStats:
        """Get current statistics."""
        return self._stats

    @property
    def comparisons(self) -> List[EvaluationComparison]:
        """Get all comparisons."""
        return self._comparisons.copy()

    async def record(
        self,
        task_id: UUID,
        sc_result: EvaluationResult,
        ac_result: EvaluationResult,
    ) -> EvaluationComparison:
        """
        Record a comparison between evaluators.

        Args:
            task_id: Task that was evaluated
            sc_result: Scoring Committee result
            ac_result: AI Council result

        Returns:
            The comparison record
        """
        comparison = EvaluationComparison.create(
            task_id=task_id,
            sc_result=sc_result,
            ac_result=ac_result,
            threshold=self._threshold,
        )

        self._comparisons.append(comparison)
        self._stats.update(comparison)

        logger.info(
            f"Recorded comparison for task {task_id}: "
            f"SC={sc_result.score:.3f}, AC={ac_result.score:.3f}, "
            f"diff={comparison.difference:+.3f}, agree={comparison.agreement}"
        )

        return comparison

    def get_recent_comparisons(self, count: int = 10) -> List[EvaluationComparison]:
        """Get most recent comparisons."""
        return self._comparisons[-count:]

    def get_disagreements(self) -> List[EvaluationComparison]:
        """Get all disagreements."""
        return [c for c in self._comparisons if not c.agreement]

    def reset(self) -> None:
        """Reset all tracked data."""
        self._comparisons.clear()
        self._stats = ComparisonStats()


# ============================================================================
# Evaluation Configuration
# ============================================================================


class EvaluationConfig(BaseModel):
    """Configuration for the evaluation system."""

    default_mode: EvaluationMode = EvaluationMode.SCORING_COMMITTEE

    # Scoring Committee config
    scoring_committee: Dict[str, Any] = Field(default_factory=dict)

    # AI Council config
    ai_council: Dict[str, Any] = Field(default_factory=dict)

    # Comparison config
    comparison: Dict[str, Any] = Field(
        default_factory=lambda: {"agreement_threshold": 0.1}
    )

    @classmethod
    def load(cls, path: Optional[str] = None) -> "EvaluationConfig":
        """Load configuration from YAML file."""
        if path is None:
            path = "config/evaluation/config.yaml"

        config_path = Path(path)
        if not config_path.exists():
            logger.warning(f"Config not found at {path}, using defaults")
            return cls()

        try:
            with open(config_path, "r") as f:
                raw = yaml.safe_load(f)

            # Convert mode string to enum
            if "default_mode" in raw:
                raw["default_mode"] = EvaluationMode(raw["default_mode"])

            return cls(**raw)
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            return cls()


# ============================================================================
# Evaluation Controller
# ============================================================================


class EvaluationController:
    """
    Toggle-based evaluation control.

    Manages switching between evaluation modes:
    - SCORING_COMMITTEE: Default, deterministic scoring
    - AI_COUNCIL: Experimental multi-agent deliberation
    - BOTH: Run both evaluators, compare results

    NO automatic switching between modes.
    User selects mode in dashboard.

    Usage:
        controller = EvaluationController()

        # Evaluate
        result = await controller.evaluate(task_result)

        # Change mode (user-initiated)
        controller.set_mode(EvaluationMode.AI_COUNCIL)
    """

    # State file for persistence
    STATE_FILE = "config/evaluation/state.json"

    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
        scoring_committee: Optional[BaseEvaluator] = None,
        ai_council: Optional[BaseEvaluator] = None,
    ):
        """
        Initialize the controller.

        Args:
            config: Evaluation configuration
            scoring_committee: Scoring Committee evaluator instance
            ai_council: AI Council evaluator instance
        """
        self._config = config or EvaluationConfig.load()
        self._mode = self._load_mode() or self._config.default_mode

        # Evaluator instances (lazy-loaded if not provided)
        self._scoring_committee = scoring_committee
        self._ai_council = ai_council

        # Comparison tracking
        threshold = self._config.comparison.get("agreement_threshold", 0.1)
        self._comparison_tracker = ComparisonTracker(threshold=threshold)

        # Stats
        self._evaluation_count = 0
        self._initialized_at = datetime.utcnow()

        logger.info(f"EvaluationController initialized with mode: {self._mode.value}")

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def mode(self) -> EvaluationMode:
        """Get current evaluation mode."""
        return self._mode

    @property
    def config(self) -> EvaluationConfig:
        """Get evaluation configuration."""
        return self._config

    @property
    def scoring_committee(self) -> Optional[BaseEvaluator]:
        """Get Scoring Committee evaluator."""
        return self._scoring_committee

    @property
    def ai_council(self) -> Optional[BaseEvaluator]:
        """Get AI Council evaluator."""
        return self._ai_council

    @property
    def comparison_tracker(self) -> ComparisonTracker:
        """Get comparison tracker."""
        return self._comparison_tracker

    # -------------------------------------------------------------------------
    # Evaluator Registration
    # -------------------------------------------------------------------------

    def register_scoring_committee(self, evaluator: BaseEvaluator) -> None:
        """Register the Scoring Committee evaluator."""
        if evaluator.get_type() != EvaluatorType.SCORING_COMMITTEE:
            raise ValueError("Expected SCORING_COMMITTEE evaluator")
        self._scoring_committee = evaluator
        logger.info("Registered Scoring Committee evaluator")

    def register_ai_council(self, evaluator: BaseEvaluator) -> None:
        """Register the AI Council evaluator."""
        if evaluator.get_type() != EvaluatorType.AI_COUNCIL:
            raise ValueError("Expected AI_COUNCIL evaluator")
        self._ai_council = evaluator
        logger.info("Registered AI Council evaluator")

    # -------------------------------------------------------------------------
    # Mode Management
    # -------------------------------------------------------------------------

    def get_mode(self) -> EvaluationMode:
        """Get current evaluation mode."""
        return self._mode

    def set_mode(self, mode: EvaluationMode) -> None:
        """
        Set evaluation mode.

        This should only be called from user-initiated actions
        (e.g., dashboard toggle). NO automatic switching.

        Args:
            mode: New evaluation mode
        """
        old_mode = self._mode
        self._mode = mode
        self._save_mode(mode)

        logger.info(f"Evaluation mode changed: {old_mode.value} -> {mode.value}")

    def _load_mode(self) -> Optional[EvaluationMode]:
        """Load persisted mode from state file."""
        try:
            state_path = Path(self.STATE_FILE)
            if state_path.exists():
                with open(state_path, "r") as f:
                    state = json.load(f)
                mode_str = state.get("mode")
                if mode_str:
                    return EvaluationMode(mode_str)
        except Exception as e:
            logger.warning(f"Failed to load evaluation mode: {e}")
        return None

    def _save_mode(self, mode: EvaluationMode) -> None:
        """Save mode to state file for persistence."""
        try:
            state_path = Path(self.STATE_FILE)
            state_path.parent.mkdir(parents=True, exist_ok=True)

            state = {
                "mode": mode.value,
                "updated_at": datetime.utcnow().isoformat(),
            }

            with open(state_path, "w") as f:
                json.dump(state, f, indent=2)

            logger.debug(f"Saved evaluation mode: {mode.value}")
        except Exception as e:
            logger.error(f"Failed to save evaluation mode: {e}")

    # -------------------------------------------------------------------------
    # Evaluation
    # -------------------------------------------------------------------------

    async def evaluate(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a task result using the current mode.

        Args:
            result: Task result to evaluate
            context: Additional context for evaluation

        Returns:
            EvaluationResult from the selected evaluator
        """
        self._evaluation_count += 1

        if self._mode == EvaluationMode.SCORING_COMMITTEE:
            return await self._evaluate_scoring_committee(result, context)

        elif self._mode == EvaluationMode.AI_COUNCIL:
            return await self._evaluate_ai_council(result, context)

        elif self._mode == EvaluationMode.BOTH:
            return await self._evaluate_both(result, context)

        else:
            raise ValueError(f"Unknown evaluation mode: {self._mode}")

    async def _evaluate_scoring_committee(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Evaluate using Scoring Committee."""
        if self._scoring_committee is None:
            logger.error("Scoring Committee not registered")
            return self._create_fallback_result(
                result, "Scoring Committee not available"
            )

        try:
            return await self._scoring_committee.evaluate(result, context)
        except Exception as e:
            logger.error(f"Scoring Committee evaluation failed: {e}")
            return self._create_fallback_result(result, str(e))

    async def _evaluate_ai_council(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """Evaluate using AI Council."""
        if self._ai_council is None:
            logger.error("AI Council not registered")
            return self._create_fallback_result(
                result, "AI Council not available"
            )

        try:
            return await self._ai_council.evaluate(result, context)
        except Exception as e:
            logger.error(f"AI Council evaluation failed: {e}")
            return self._create_fallback_result(result, str(e))

    async def _evaluate_both(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate using both evaluators, compare, return SC result.

        Runs both evaluators, records comparison for analysis,
        but returns Scoring Committee result as authoritative.
        """
        # Run Scoring Committee
        sc_result = await self._evaluate_scoring_committee(result, context)

        # Run AI Council
        ac_result = await self._evaluate_ai_council(result, context)

        # Record comparison (if both succeeded)
        if sc_result.status == EvaluationStatus.COMPLETED and \
           ac_result.status == EvaluationStatus.COMPLETED:
            await self._comparison_tracker.record(
                task_id=result.task_id,
                sc_result=sc_result,
                ac_result=ac_result,
            )

        # Add comparison metadata to SC result
        sc_result.metadata["comparison"] = {
            "ai_council_score": ac_result.score,
            "difference": sc_result.score - ac_result.score,
        }

        # Scoring Committee is authoritative
        return sc_result

    def _create_fallback_result(
        self,
        result: TaskResult,
        error: str,
    ) -> EvaluationResult:
        """Create fallback result when evaluation fails."""
        return EvaluationResult(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            score=0.5,  # Neutral score on failure
            confidence=0.0,
            evaluator_type=EvaluatorType.SCORING_COMMITTEE,
            status=EvaluationStatus.FAILED,
            requires_human_feedback=True,
            human_feedback_reason=f"Automatic evaluation failed: {error}",
            error=error,
        )

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_comparison_stats(self) -> ComparisonStats:
        """Get comparison statistics from BOTH mode."""
        return self._comparison_tracker.stats

    def get_stats(self) -> Dict[str, Any]:
        """Get controller statistics."""
        return {
            "mode": self._mode.value,
            "evaluation_count": self._evaluation_count,
            "initialized_at": self._initialized_at.isoformat(),
            "scoring_committee_available": self._scoring_committee is not None,
            "ai_council_available": self._ai_council is not None,
            "comparison_stats": self._comparison_tracker.stats.model_dump(),
        }


# ============================================================================
# Singleton Instance
# ============================================================================


_evaluation_controller: Optional[EvaluationController] = None


def get_evaluation_controller() -> EvaluationController:
    """Get the global evaluation controller."""
    global _evaluation_controller
    if _evaluation_controller is None:
        _evaluation_controller = EvaluationController()
    return _evaluation_controller


def reset_evaluation_controller() -> None:
    """Reset the global evaluation controller (for testing)."""
    global _evaluation_controller
    _evaluation_controller = None
