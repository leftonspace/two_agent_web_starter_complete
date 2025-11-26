"""
PHASE 7.5: AI Council

Experimental evaluator using specialist voting.
Specialists vote on each other's work with structured feedback.

WARNING: This is experimental - AI judging AI.
Use Scoring Committee for production evaluation.

Usage:
    from core.evaluation.ai_council import (
        AICouncil,
        AICouncilConfig,
        Vote,
        VoteAggregator,
        AggregationResult,
    )

    # Create council
    council = AICouncil()

    # Evaluate
    result = await council.evaluate(task_result)
"""

from .voter import (
    # Models
    Vote,
    VoteCriteria,
    # Exceptions
    VoteParseError,
    # Functions
    parse_vote_response,
    # Constants
    VOTING_INSTRUCTIONS,
    JARVIS_VOTING_ADDENDUM,
)

from .aggregator import (
    # Result
    AggregationResult,
    # Aggregator
    VoteAggregator,
    # Exceptions
    AggregationError,
    NoVotesError,
    InsufficientVotesError,
)

from .council import (
    # Config
    AICouncilConfig,
    # Council
    AICouncil,
    # Factory
    create_ai_council,
)


__all__ = [
    # Voter
    "Vote",
    "VoteCriteria",
    "VoteParseError",
    "parse_vote_response",
    "VOTING_INSTRUCTIONS",
    "JARVIS_VOTING_ADDENDUM",
    # Aggregator
    "AggregationResult",
    "VoteAggregator",
    "AggregationError",
    "NoVotesError",
    "InsufficientVotesError",
    # Council
    "AICouncilConfig",
    "AICouncil",
    "create_ai_council",
]
