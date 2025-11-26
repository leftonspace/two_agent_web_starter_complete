"""
PHASE 7.5: Evaluation Framework Base Classes

Defines the core abstractions for evaluating specialist task outputs.
Two evaluator types are supported:
- Scoring Committee (default): Deterministic, component-weighted scoring
- AI Council (experimental): Multi-agent deliberation with voting

Usage:
    from core.evaluation import (
        EvaluatorType,
        EvaluationResult,
        TaskResult,
        BaseEvaluator,
    )

    class MyEvaluator(BaseEvaluator):
        async def evaluate(self, result: TaskResult, context: Dict = None) -> EvaluationResult:
            # Evaluation logic
            return EvaluationResult(...)

        def get_type(self) -> EvaluatorType:
            return EvaluatorType.SCORING_COMMITTEE
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class EvaluatorType(str, Enum):
    """Types of evaluators available."""
    SCORING_COMMITTEE = "scoring_committee"
    AI_COUNCIL = "ai_council"


class EvaluationStatus(str, Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN = "requires_human"


# ============================================================================
# Task Result Model
# ============================================================================


class TaskResult(BaseModel):
    """
    The output from a specialist task to be evaluated.

    Contains all information needed for evaluation:
    - The original request and response
    - Artifacts created (files, etc.)
    - Execution metadata
    """

    # Identity
    task_id: UUID = Field(default_factory=uuid4)
    specialist_id: UUID
    specialist_name: Optional[str] = None

    # Domain context
    domain: str
    task_type: Optional[str] = None  # e.g., "code_review", "report_generation"

    # Content
    request: str = Field(
        ...,
        min_length=1,
        description="The original user request",
    )
    response: str = Field(
        ...,
        description="The specialist's response",
    )

    # Artifacts
    artifacts: List[str] = Field(
        default_factory=list,
        description="File paths created/modified",
    )

    # Execution metadata
    execution_time_ms: int = Field(
        default=0,
        ge=0,
        description="Time taken in milliseconds",
    )
    model_used: str = Field(
        default="unknown",
        description="LLM model used",
    )
    tokens_used: int = Field(
        default=0,
        ge=0,
        description="Total tokens (input + output)",
    )
    cost_cad: float = Field(
        default=0.0,
        ge=0.0,
        description="Cost in CAD",
    )

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Additional context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for evaluation",
    )


# ============================================================================
# Evaluation Result Model
# ============================================================================


class ComponentScore(BaseModel):
    """Score for a single evaluation component."""

    name: str = Field(..., description="Component name (e.g., 'tests_pass')")
    score: float = Field(..., ge=0.0, le=1.0, description="Component score")
    weight: float = Field(default=1.0, ge=0.0, description="Weight in final score")
    details: str = Field(default="", description="Explanation of score")
    passed: Optional[bool] = Field(
        default=None,
        description="For pass/fail components",
    )


class EvaluationResult(BaseModel):
    """
    Result from any evaluator.

    Provides a unified structure for evaluation results regardless
    of which evaluator produced them.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    specialist_id: UUID

    # Scores
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall score (0-1)",
    )
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="Score breakdown by component",
    )
    component_details: List[ComponentScore] = Field(
        default_factory=list,
        description="Detailed component scores",
    )

    # Confidence
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the evaluation (1.0 = fully confident)",
    )

    # Evaluator info
    evaluator_type: EvaluatorType
    evaluator_version: str = Field(default="1.0")

    # Status
    status: EvaluationStatus = Field(default=EvaluationStatus.COMPLETED)
    requires_human_feedback: bool = Field(
        default=False,
        description="Whether human review is recommended",
    )
    human_feedback_reason: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Evaluator-specific metadata",
    )

    # Timestamps
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    evaluation_duration_ms: int = Field(default=0, ge=0)

    # Error handling
    error: Optional[str] = None

    def is_passing(self, threshold: float = 0.7) -> bool:
        """Check if score meets passing threshold."""
        return self.score >= threshold

    def to_summary(self) -> Dict[str, Any]:
        """Get a summary of the evaluation."""
        return {
            "task_id": str(self.task_id),
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "evaluator": self.evaluator_type.value,
            "status": self.status.value,
            "requires_human": self.requires_human_feedback,
            "components": {k: round(v, 3) for k, v in self.components.items()},
        }


# ============================================================================
# Base Evaluator
# ============================================================================


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.

    Subclasses must implement:
    - evaluate(): Perform evaluation and return result
    - get_type(): Return the evaluator type

    Usage:
        class ScoringCommittee(BaseEvaluator):
            async def evaluate(self, result, context=None):
                # ... evaluation logic ...
                return EvaluationResult(...)

            def get_type(self):
                return EvaluatorType.SCORING_COMMITTEE
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the evaluator.

        Args:
            config: Evaluator-specific configuration
        """
        self._config = config or {}
        self._evaluation_count = 0

    @property
    def config(self) -> Dict[str, Any]:
        """Get evaluator configuration."""
        return self._config

    @property
    def evaluation_count(self) -> int:
        """Get number of evaluations performed."""
        return self._evaluation_count

    @abstractmethod
    async def evaluate(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a task result.

        Args:
            result: The task result to evaluate
            context: Additional context for evaluation

        Returns:
            EvaluationResult with score and details
        """
        pass

    @abstractmethod
    def get_type(self) -> EvaluatorType:
        """
        Get the type of this evaluator.

        Returns:
            EvaluatorType enum value
        """
        pass

    async def evaluate_batch(
        self,
        results: List[TaskResult],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[EvaluationResult]:
        """
        Evaluate multiple task results.

        Default implementation evaluates sequentially.
        Subclasses may override for parallel evaluation.

        Args:
            results: List of task results to evaluate
            context: Shared context for all evaluations

        Returns:
            List of evaluation results
        """
        evaluations = []
        for result in results:
            evaluation = await self.evaluate(result, context)
            evaluations.append(evaluation)
        return evaluations

    def validate_result(self, result: TaskResult) -> bool:
        """
        Validate that a task result can be evaluated.

        Args:
            result: Task result to validate

        Returns:
            True if result is valid for evaluation
        """
        # Basic validation
        if not result.request:
            return False
        if result.response is None:
            return False
        return True

    def _increment_count(self) -> None:
        """Increment evaluation count."""
        self._evaluation_count += 1

    def _create_error_result(
        self,
        result: TaskResult,
        error: str,
    ) -> EvaluationResult:
        """Create an error evaluation result."""
        return EvaluationResult(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            score=0.0,
            evaluator_type=self.get_type(),
            status=EvaluationStatus.FAILED,
            error=error,
        )


# ============================================================================
# Comparison Models (for BOTH mode)
# ============================================================================


class EvaluationComparison(BaseModel):
    """Comparison between two evaluator results."""

    task_id: UUID
    scoring_committee_score: float
    ai_council_score: float
    difference: float = Field(description="SC score - AC score")
    agreement: bool = Field(description="Whether evaluators agree within threshold")
    compared_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        task_id: UUID,
        sc_result: EvaluationResult,
        ac_result: EvaluationResult,
        threshold: float = 0.1,
    ) -> "EvaluationComparison":
        """Create comparison from two results."""
        diff = sc_result.score - ac_result.score
        return cls(
            task_id=task_id,
            scoring_committee_score=sc_result.score,
            ai_council_score=ac_result.score,
            difference=diff,
            agreement=abs(diff) <= threshold,
        )


class ComparisonStats(BaseModel):
    """Statistics from comparing evaluators."""

    total_comparisons: int = 0
    agreements: int = 0
    disagreements: int = 0
    agreement_rate: float = 0.0
    avg_difference: float = 0.0
    max_difference: float = 0.0
    sc_higher_count: int = 0  # Times SC scored higher
    ac_higher_count: int = 0  # Times AC scored higher

    def update(self, comparison: EvaluationComparison) -> None:
        """Update stats with new comparison."""
        self.total_comparisons += 1

        if comparison.agreement:
            self.agreements += 1
        else:
            self.disagreements += 1

        self.agreement_rate = self.agreements / self.total_comparisons

        # Update difference stats
        abs_diff = abs(comparison.difference)
        self.avg_difference = (
            (self.avg_difference * (self.total_comparisons - 1) + abs_diff)
            / self.total_comparisons
        )
        self.max_difference = max(self.max_difference, abs_diff)

        # Track which evaluator scored higher
        if comparison.difference > 0:
            self.sc_higher_count += 1
        elif comparison.difference < 0:
            self.ac_higher_count += 1
