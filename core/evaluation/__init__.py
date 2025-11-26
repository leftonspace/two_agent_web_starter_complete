"""
PHASE 7.5: Evaluation System

Two-mode evaluation framework:
- Scoring Committee (default): Deterministic component-weighted scoring
- AI Council (experimental): Multi-agent deliberation with voting

User toggles between modes in dashboard - NO automatic switching.

Usage:
    from core.evaluation import (
        EvaluationController,
        EvaluationMode,
        EvaluationResult,
        TaskResult,
        get_evaluation_controller,
        ScoringCommittee,
        UserFeedback,
    )

    # Get controller
    controller = get_evaluation_controller()

    # Register scoring committee
    committee = ScoringCommittee()
    controller.register_scoring_committee(committee)

    # Evaluate
    result = await controller.evaluate(task_result)

    # Change mode (user-initiated only)
    controller.set_mode(EvaluationMode.AI_COUNCIL)
"""

from .base import (
    # Enums
    EvaluatorType,
    EvaluationStatus,
    # Models
    TaskResult,
    ComponentScore,
    EvaluationResult,
    EvaluationComparison,
    ComparisonStats,
    # Base class
    BaseEvaluator,
)

from .controller import (
    # Enums
    EvaluationMode,
    # Config
    EvaluationConfig,
    # Tracker
    ComparisonTracker,
    # Controller
    EvaluationController,
    get_evaluation_controller,
    reset_evaluation_controller,
)

from .scoring_committee import (
    # Committee
    ScoringCommittee,
    ScoringCommitteeConfig,
    create_scoring_committee,
    # Components
    TestRunner,
    Linter,
    FormatChecker,
    SpellChecker,
    # User feedback
    UserFeedback,
    FeedbackRequest,
    UserFeedbackCollector,
    get_feedback_collector,
    reset_feedback_collector,
)


__all__ = [
    # Base enums
    "EvaluatorType",
    "EvaluationStatus",
    # Base models
    "TaskResult",
    "ComponentScore",
    "EvaluationResult",
    "EvaluationComparison",
    "ComparisonStats",
    # Base class
    "BaseEvaluator",
    # Controller enums
    "EvaluationMode",
    # Controller config
    "EvaluationConfig",
    # Controller tracker
    "ComparisonTracker",
    # Controller
    "EvaluationController",
    "get_evaluation_controller",
    "reset_evaluation_controller",
    # Scoring Committee
    "ScoringCommittee",
    "ScoringCommitteeConfig",
    "create_scoring_committee",
    # Scoring Committee components
    "TestRunner",
    "Linter",
    "FormatChecker",
    "SpellChecker",
    # User feedback
    "UserFeedback",
    "FeedbackRequest",
    "UserFeedbackCollector",
    "get_feedback_collector",
    "reset_feedback_collector",
]
