"""
PHASE 7.5: Scoring Committee

Production evaluator using external ground truth verification.
NO AI judging AI - only external tools and user feedback.

Committee Members by Domain:
- code_generation: TestRunner (30%), Linter (20%), UserFeedback (50%)
- business_documents: FormatChecker (20%), SpellChecker (10%), UserFeedback (70%)
- administration: UserFeedback (100%)

Usage:
    from core.evaluation.scoring_committee import ScoringCommittee

    committee = ScoringCommittee()
    result = await committee.evaluate(task_result)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from ..base import (
    BaseEvaluator,
    ComponentScore,
    EvaluationResult,
    EvaluationStatus,
    EvaluatorType,
    TaskResult,
)
from .test_runner import TestRunner
from .linter import Linter
from .format_checker import FormatChecker
from .spell_checker import SpellChecker
from .user_feedback import UserFeedbackCollector, get_feedback_collector


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


class ScoringCommitteeConfig(BaseModel):
    """Configuration for the Scoring Committee."""

    # Component weights by domain
    weights: Dict[str, Dict[str, float]] = Field(
        default_factory=lambda: {
            "code_generation": {
                "tests_pass": 0.30,
                "lint_clean": 0.20,
                "user_feedback": 0.50,
            },
            "code_review": {
                "issues_found": 0.25,
                "false_positives": 0.15,
                "user_feedback": 0.60,
            },
            "business_documents": {
                "format_valid": 0.20,
                "spell_check": 0.10,
                "user_feedback": 0.70,
            },
            "administration": {
                "user_feedback": 1.00,
            },
            "research": {
                "accuracy": 0.30,
                "completeness": 0.20,
                "user_feedback": 0.50,
            },
            "default": {
                "automated_checks": 0.30,
                "user_feedback": 0.70,
            },
        }
    )

    # Confidence settings
    confidence_no_automated: float = 0.6
    confidence_no_feedback: float = 0.7
    confidence_full: float = 1.0

    @classmethod
    def load(cls, path: str = "config/evaluation/config.yaml") -> "ScoringCommitteeConfig":
        """Load configuration from YAML file."""
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            sc_config = data.get("scoring_committee", {})
            return cls(
                weights=sc_config.get("weights", cls().weights),
                confidence_no_automated=sc_config.get("confidence", {}).get("no_automated_checks", 0.6),
                confidence_no_feedback=sc_config.get("confidence", {}).get("no_user_feedback", 0.7),
                confidence_full=sc_config.get("confidence", {}).get("full_validation", 1.0),
            )
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return cls()


# ============================================================================
# Scoring Committee
# ============================================================================


class ScoringCommittee(BaseEvaluator):
    """
    Production evaluator using external ground truth.

    NO AI judging AI here - only:
    - External verification tools (pytest, ruff, spell checkers)
    - User feedback (ratings, corrections)

    Committee Members:
    - TestRunner: Run tests, calculate pass rate
    - Linter: Run linting, count errors
    - FormatChecker: Validate document structure
    - SpellChecker: Check spelling/grammar
    - UserFeedback: User ratings and corrections

    Usage:
        committee = ScoringCommittee()
        result = await committee.evaluate(task_result)
    """

    def __init__(
        self,
        config: Optional[ScoringCommitteeConfig] = None,
        test_runner: Optional[TestRunner] = None,
        linter: Optional[Linter] = None,
        format_checker: Optional[FormatChecker] = None,
        spell_checker: Optional[SpellChecker] = None,
        feedback_collector: Optional[UserFeedbackCollector] = None,
    ):
        """
        Initialize the Scoring Committee.

        Args:
            config: Committee configuration
            test_runner: TestRunner instance
            linter: Linter instance
            format_checker: FormatChecker instance
            spell_checker: SpellChecker instance
            feedback_collector: UserFeedbackCollector instance
        """
        super().__init__(config.model_dump() if config else None)

        self._sc_config = config or ScoringCommitteeConfig.load()

        # Initialize committee members
        self._test_runner = test_runner or TestRunner()
        self._linter = linter or Linter()
        self._format_checker = format_checker or FormatChecker()
        self._spell_checker = spell_checker or SpellChecker()
        self._feedback_collector = feedback_collector or get_feedback_collector()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def test_runner(self) -> TestRunner:
        """Get the test runner."""
        return self._test_runner

    @property
    def linter(self) -> Linter:
        """Get the linter."""
        return self._linter

    @property
    def format_checker(self) -> FormatChecker:
        """Get the format checker."""
        return self._format_checker

    @property
    def spell_checker(self) -> SpellChecker:
        """Get the spell checker."""
        return self._spell_checker

    @property
    def feedback_collector(self) -> UserFeedbackCollector:
        """Get the feedback collector."""
        return self._feedback_collector

    # -------------------------------------------------------------------------
    # BaseEvaluator Implementation
    # -------------------------------------------------------------------------

    def get_type(self) -> EvaluatorType:
        """Get evaluator type."""
        return EvaluatorType.SCORING_COMMITTEE

    async def evaluate(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a task result using the scoring committee.

        Args:
            result: Task result to evaluate
            context: Additional context

        Returns:
            EvaluationResult with weighted score
        """
        start_time = time.time()
        self._increment_count()

        # Get weights for this domain
        domain = result.domain
        weights = self._get_weights(domain)

        # Run applicable checks
        components: Dict[str, float] = {}
        component_details: List[ComponentScore] = []

        # Code checks
        if "tests_pass" in weights:
            score = await self._test_runner.run(result, context)
            components["tests_pass"] = score
            component_details.append(ComponentScore(
                name="tests_pass",
                score=score,
                weight=weights["tests_pass"],
                details="Test pass rate",
                passed=score >= 0.95,
            ))

        if "lint_clean" in weights:
            score = await self._linter.run(result, context)
            components["lint_clean"] = score
            component_details.append(ComponentScore(
                name="lint_clean",
                score=score,
                weight=weights["lint_clean"],
                details="Lint score",
                passed=score >= 0.8,
            ))

        # Document checks
        if "format_valid" in weights:
            score = await self._format_checker.run(result, context)
            components["format_valid"] = score
            component_details.append(ComponentScore(
                name="format_valid",
                score=score,
                weight=weights["format_valid"],
                details="Format validity score",
                passed=score >= 0.8,
            ))

        if "spell_check" in weights:
            score = await self._spell_checker.run(result, context)
            components["spell_check"] = score
            component_details.append(ComponentScore(
                name="spell_check",
                score=score,
                weight=weights["spell_check"],
                details="Spelling score",
                passed=score >= 0.9,
            ))

        # User feedback - special handling
        if "user_feedback" in weights:
            feedback = await self._feedback_collector.get(result.task_id)

            if feedback:
                score = feedback.to_score()
                components["user_feedback"] = score
                component_details.append(ComponentScore(
                    name="user_feedback",
                    score=score,
                    weight=weights["user_feedback"],
                    details=f"User rating: {feedback.rating}/5",
                    passed=score >= 0.7,
                ))
            else:
                # No feedback yet - return partial result
                return await self._create_partial_result(
                    result,
                    components,
                    component_details,
                    weights,
                    start_time,
                )

        # Calculate weighted score
        final_score = self._calculate_weighted_score(components, weights)

        # Determine confidence
        confidence = self._calculate_confidence(components, weights)

        duration_ms = int((time.time() - start_time) * 1000)

        return EvaluationResult(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            score=final_score,
            components=components,
            component_details=component_details,
            confidence=confidence,
            evaluator_type=EvaluatorType.SCORING_COMMITTEE,
            status=EvaluationStatus.COMPLETED,
            evaluation_duration_ms=duration_ms,
            metadata={
                "domain": domain,
                "weights_used": weights,
            },
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_weights(self, domain: str) -> Dict[str, float]:
        """Get weights for a domain."""
        weights = self._sc_config.weights.get(domain)
        if weights is None:
            weights = self._sc_config.weights.get("default", {})
            logger.debug(f"Using default weights for domain: {domain}")
        return weights

    def _calculate_weighted_score(
        self,
        components: Dict[str, float],
        weights: Dict[str, float],
    ) -> float:
        """Calculate weighted score from components."""
        if not components:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for name, weight in weights.items():
            if name in components:
                weighted_sum += components[name] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _calculate_confidence(
        self,
        components: Dict[str, float],
        weights: Dict[str, float],
    ) -> float:
        """Calculate confidence in the evaluation."""
        has_automated = any(
            k in components
            for k in ["tests_pass", "lint_clean", "format_valid", "spell_check"]
        )
        has_feedback = "user_feedback" in components

        if has_automated and has_feedback:
            return self._sc_config.confidence_full
        elif has_automated:
            return self._sc_config.confidence_no_feedback
        elif has_feedback:
            return self._sc_config.confidence_no_automated
        else:
            return 0.3  # Very low confidence without any validation

    async def _create_partial_result(
        self,
        result: TaskResult,
        components: Dict[str, float],
        component_details: List[ComponentScore],
        weights: Dict[str, float],
        start_time: float,
    ) -> EvaluationResult:
        """Create partial result when user feedback is pending."""
        # Calculate partial score from available components
        partial_score = self._calculate_weighted_score(components, weights)

        # Request feedback
        await self._feedback_collector.request_feedback(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            domain=result.domain,
            request_summary=result.request[:200],
            response_preview=result.response[:500],
        )

        duration_ms = int((time.time() - start_time) * 1000)

        return EvaluationResult(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            score=partial_score,
            components=components,
            component_details=component_details,
            confidence=0.5,  # Lower confidence without user feedback
            evaluator_type=EvaluatorType.SCORING_COMMITTEE,
            status=EvaluationStatus.COMPLETED,
            requires_human_feedback=True,
            human_feedback_reason="User feedback pending",
            evaluation_duration_ms=duration_ms,
            metadata={
                "domain": result.domain,
                "weights_used": weights,
                "partial": True,
            },
        )


# ============================================================================
# Factory Function
# ============================================================================


def create_scoring_committee(
    config_path: str = "config/evaluation/config.yaml",
) -> ScoringCommittee:
    """Create a configured ScoringCommittee instance."""
    config = ScoringCommitteeConfig.load(config_path)
    return ScoringCommittee(config=config)
