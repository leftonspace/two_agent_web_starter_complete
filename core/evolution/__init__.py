"""
PHASE 7.5: Evolution System

Manages the lifecycle of specialists including the graveyard
for culled specialists and learning extraction.

Usage:
    from core.evolution import (
        Graveyard,
        get_graveyard,
        FailureAnalyzer,
        LearningsExtractor,
        FailureCategory,
        FailurePattern,
        Learning,
        GraveyardEntry,
    )

    # Get graveyard
    graveyard = get_graveyard()

    # Send failed specialist
    entry = await graveyard.send_to_graveyard(specialist, "low_performance")

    # Get learnings for spawner
    learnings = graveyard.get_learnings("code_generation")
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


__all__ = [
    # Enums
    "FailureCategory",
    # Models
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
]
