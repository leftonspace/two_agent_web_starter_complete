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
- **Competitive Council**: Parallel execution with "best answer" voting
- **Graveyard System**: Permanent deletion of underperformers

Usage (Standard Council):
    from agent.council import CouncilOrchestrator, create_council

    council = await create_council(
        llm_func=my_llm_function,
        templates=["coder", "reviewer", "tester"]
    )
    result = await council.process_task("Build a REST API")

Usage (Competitive Council):
    from agent.council import CompetitiveCouncil, create_competitive_council

    # 3 supervisor+employee sets work on SAME task in parallel
    # All vote on whose answer is BEST
    # Every 10 rounds: 3 lowest performers → Graveyard (deleted)
    council = await create_competitive_council(llm_func=my_llm_function)
    result = await council.process_task("Build a unicorn website")
    print(f"Winner: {result.winner_set_id}")
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

# Competitive Council (Parallel Execution)
from .competitive_council import (
    CompetitiveCouncil,
    CompetitiveConfig,
    CompetitiveResult,
    AgentSet,
    create_competitive_council,
)

# Graveyard (Permanent Deletion)
from .graveyard import (
    Graveyard,
    GraveyardRecord,
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

    # Competitive Council
    'CompetitiveCouncil',
    'CompetitiveConfig',
    'CompetitiveResult',
    'AgentSet',
    'create_competitive_council',

    # Graveyard
    'Graveyard',
    'GraveyardRecord',
]

__version__ = '1.1.0'  # Added competitive council + graveyard
