"""
Council System - Gamified Meta-Orchestration

A unique multi-agent coordination system where specialist councillors
vote on decisions with weighted influence based on performance and happiness.

Features:
- Weighted voting based on performance and happiness
- Councillor happiness system with event-based impacts
- Fire/spawn mechanics to maintain team quality
- Bonus pool for rewarding excellent work
- Automatic pattern selection based on task analysis

Usage:
    from agent.council import CouncilOrchestrator, create_council

    # Create and initialize council
    council = await create_council(
        llm_func=my_llm_function,
        templates=["coder", "reviewer", "tester"]
    )

    # Process a task
    result = await council.process_task("Build a REST API")

    # Get council status
    status = council.get_council_status()
    print(f"Team morale: {status['team_morale']['mood']}")
"""

# Core models
from .models import (
    Councillor,
    CouncillorStatus,
    Specialization,
    PerformanceMetrics,
    Vote,
    VotingSession,
    VoteType,
    CouncilTask,
    TaskComplexity,
    BonusPool,
)

# Voting system
from .voting import (
    VotingManager,
    VotingConfig,
    conduct_vote,
)

# Happiness system
from .happiness import (
    HappinessManager,
    HappinessEvent,
    HappinessRecord,
    HAPPINESS_IMPACTS,
)

# Factory system
from .factory import (
    CouncillorFactory,
    FactoryConfig,
    FiringDecision,
    SpawnDecision,
    SPECIALIZATION_TEMPLATES,
)

# Orchestrator
from .orchestrator import (
    CouncilOrchestrator,
    CouncilConfig,
    create_council,
)


__all__ = [
    # Models
    'Councillor',
    'CouncillorStatus',
    'Specialization',
    'PerformanceMetrics',
    'Vote',
    'VotingSession',
    'VoteType',
    'CouncilTask',
    'TaskComplexity',
    'BonusPool',

    # Voting
    'VotingManager',
    'VotingConfig',
    'conduct_vote',

    # Happiness
    'HappinessManager',
    'HappinessEvent',
    'HappinessRecord',
    'HAPPINESS_IMPACTS',

    # Factory
    'CouncillorFactory',
    'FactoryConfig',
    'FiringDecision',
    'SpawnDecision',
    'SPECIALIZATION_TEMPLATES',

    # Orchestrator
    'CouncilOrchestrator',
    'CouncilConfig',
    'create_council',
]

__version__ = '1.0.0'
