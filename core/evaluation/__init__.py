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
    )

    # Get controller
    controller = get_evaluation_controller()

    # Check mode
    print(f"Mode: {controller.get_mode()}")

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
]
