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
        DomainPool,
        SelectionMode,
        PoolManager,
        get_pool_manager,
        DomainConfig,
        DomainConfigLoader,
        get_domain_loader,
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

    # Use domain pools
    manager = get_pool_manager()
    pool = manager.get_pool("code_review")
    pool.add(specialist)

    # Select specialist for task
    selected = pool.select(SelectionMode.WEIGHTED)

    # Load domain configs
    loader = get_domain_loader()
    config = loader.load("code_generation")
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

from .pool import (
    # Enums
    SelectionMode,
    # Main class
    DomainPool,
    # Exceptions
    PoolError,
    NoSpecialistsError,
    SpecialistNotFoundError,
    PoolFullError,
)

from .pool_manager import (
    PoolManager,
    get_pool_manager,
    reset_pool_manager,
)

from .domain_config import (
    # Config models
    VerificationRule,
    QualityThresholds,
    EvolutionSettings,
    DefaultSpecialistConfig,
    DomainConfig,
    # Loader
    DomainConfigLoader,
    get_domain_loader,
    reset_domain_loader,
)

from .spawner import (
    # Enums
    MutationType,
    LearningType,
    # Models
    Learning,
    Mutation,
    # Spawner class
    Spawner,
    get_spawner,
    reset_spawner,
)


__all__ = [
    # Specialist enums
    "SpecialistStatus",
    "TrendDirection",
    # Specialist config models
    "SpecialistConfig",
    "PerformanceStats",
    # Specialist model
    "Specialist",
    # Specialist factory functions
    "create_specialist",
    "evolve_specialist",
    # Pool enums
    "SelectionMode",
    # Pool model
    "DomainPool",
    # Pool exceptions
    "PoolError",
    "NoSpecialistsError",
    "SpecialistNotFoundError",
    "PoolFullError",
    # Pool manager
    "PoolManager",
    "get_pool_manager",
    "reset_pool_manager",
    # Domain config models
    "VerificationRule",
    "QualityThresholds",
    "EvolutionSettings",
    "DefaultSpecialistConfig",
    "DomainConfig",
    # Domain config loader
    "DomainConfigLoader",
    "get_domain_loader",
    "reset_domain_loader",
    # Spawner enums
    "MutationType",
    "LearningType",
    # Spawner models
    "Learning",
    "Mutation",
    # Spawner
    "Spawner",
    "get_spawner",
    "reset_spawner",
]
