"""
PHASE 7.5: Evolution System

Manages the lifecycle of specialists including:
- Graveyard for culled specialists
- Learning extraction from failures
- Convergence detection
- Evolution control with pause/resume

Usage:
    from core.evolution import (
        # Controller
        EvolutionController,
        get_evolution_controller,
        EvolutionResult,
        EvolutionStatus,

        # Convergence
        ConvergenceDetector,
        ConvergenceResult,

        # Resume
        ResumeChecker,
        ResumeTrigger,

        # Graveyard
        Graveyard,
        get_graveyard,
        FailureAnalyzer,
        LearningsExtractor,
    )

    # Run evolution
    controller = get_evolution_controller()
    result = await controller.run_evolution("code_generation")

    # Check convergence
    convergence = controller.check_convergence("code_generation")
"""

from .graveyard import (
    # Enums
    FailureCategory,
    # Models
    FailurePattern,
    Learning,
    GraveyardEntry,
    # Manager
    Graveyard,
    get_graveyard,
    reset_graveyard,
)

from .failure_analyzer import (
    FailureAnalyzer,
    TaskAnalysisResult,
)

from .learnings_extractor import (
    LearningsExtractor,
    LEARNING_TEMPLATES,
)

from .convergence import (
    # Models
    ConvergenceResult,
    ConvergenceProgress,
    ConvergenceConfig,
    # Detector
    ConvergenceDetector,
    get_convergence_detector,
    reset_convergence_detector,
)

from .resume_triggers import (
    # Enums
    ResumeTrigger,
    # Models
    ResumeCheckResult,
    ResumeConfig,
    # Checker
    ResumeChecker,
    get_resume_checker,
    reset_resume_checker,
)

from .controller import (
    # Enums
    EvolutionState,
    # Models
    EvolutionStatus,
    EvolutionResult,
    EvolutionConfig,
    # Controller
    EvolutionController,
    get_evolution_controller,
    reset_evolution_controller,
)


__all__ = [
    # Graveyard enums
    "FailureCategory",
    # Graveyard models
    "FailurePattern",
    "Learning",
    "GraveyardEntry",
    # Graveyard
    "Graveyard",
    "get_graveyard",
    "reset_graveyard",
    # Analyzer
    "FailureAnalyzer",
    "TaskAnalysisResult",
    # Extractor
    "LearningsExtractor",
    "LEARNING_TEMPLATES",
    # Convergence
    "ConvergenceResult",
    "ConvergenceProgress",
    "ConvergenceConfig",
    "ConvergenceDetector",
    "get_convergence_detector",
    "reset_convergence_detector",
    # Resume
    "ResumeTrigger",
    "ResumeCheckResult",
    "ResumeConfig",
    "ResumeChecker",
    "get_resume_checker",
    "reset_resume_checker",
    # Controller
    "EvolutionState",
    "EvolutionStatus",
    "EvolutionResult",
    "EvolutionConfig",
    "EvolutionController",
    "get_evolution_controller",
    "reset_evolution_controller",
]
