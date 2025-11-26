"""
PHASE 7.4: Specialist System

Specialists are agent configurations optimized for specific domains.
Each domain has multiple specialists competing for tasks based on
performance metrics.

Usage:
    from core.specialists import (
        Specialist,
        SpecialistConfig,
        SpecialistStatus,
        create_specialist,
        evolve_specialist,
    )

    # Create a new specialist
    specialist = create_specialist(
        domain="code_review",
        system_prompt="You are an expert code reviewer...",
        tools=["code_search", "file_read"],
    )

    # Record performance
    specialist.record_score(0.85)

    # Evolve from high performer
    child = evolve_specialist(
        parent=specialist,
        additional_techniques=["Always check for edge cases"],
    )
"""

from .specialist import (
    # Enums
    SpecialistStatus,
    TrendDirection,
    # Config models
    SpecialistConfig,
    PerformanceStats,
    # Main model
    Specialist,
    # Factory functions
    create_specialist,
    evolve_specialist,
)


__all__ = [
    # Enums
    "SpecialistStatus",
    "TrendDirection",
    # Config models
    "SpecialistConfig",
    "PerformanceStats",
    # Main model
    "Specialist",
    # Factory functions
    "create_specialist",
    "evolve_specialist",
]
