"""
Orchestration Patterns Package

Multi-agent coordination patterns for JARVIS.

This package provides different strategies for coordinating multiple agents:

- SequentialPattern: Agents speak in defined order
- HierarchicalPattern: Manager-supervisor-worker delegation
- AutoSelectPattern: LLM-based intelligent agent selection
- RoundRobinPattern: Fixed rotation through agents
- ManualPattern: User-controlled agent selection
- PatternSelector: Automatic pattern recommendation

Usage:
    from agent.patterns import SequentialPattern, Agent, PatternConfig

    agents = [
        Agent(name="researcher", role="Research"),
        Agent(name="writer", role="Writing"),
    ]

    pattern = SequentialPattern(agents)
    result = await pattern.run("Write an article about AI")

    # Or use PatternSelector to choose automatically
    from agent.patterns import select_pattern

    pattern = select_pattern("Collaborate on project", agents)
    result = await pattern.run("Start collaboration")
"""

# Base classes and data models
from .base import (
    Pattern,
    PatternStatus,
    PatternConfig,
    PatternResult,
    Agent,
    Message,
    MessageRole,
)

# Sequential patterns
from .sequential import (
    SequentialPattern,
    OrderedSequentialPattern,
    PipelinePattern,
)

# Hierarchical pattern
from .hierarchical import (
    HierarchicalPattern,
    HierarchicalAgent,
    HierarchyLevel,
)

# AutoSelect pattern
from .autoselect import (
    AutoSelectPattern,
    AgentSelector,
    KeywordSelector,
    LLMSelector,
    SelectionCriteria,
)

# RoundRobin and Manual patterns
from .roundrobin import (
    RoundRobinPattern,
    WeightedRoundRobinPattern,
    ManualPattern,
    InteractivePattern,
)

# Pattern selector
from .selector import (
    PatternSelector,
    TaskAnalysis,
    TaskComplexity,
    TaskType,
    PatternRecommendation,
    select_pattern,
)


__all__ = [
    # Base classes
    'Pattern',
    'PatternStatus',
    'PatternConfig',
    'PatternResult',
    'Agent',
    'Message',
    'MessageRole',

    # Sequential patterns
    'SequentialPattern',
    'OrderedSequentialPattern',
    'PipelinePattern',

    # Hierarchical pattern
    'HierarchicalPattern',
    'HierarchicalAgent',
    'HierarchyLevel',

    # AutoSelect pattern
    'AutoSelectPattern',
    'AgentSelector',
    'KeywordSelector',
    'LLMSelector',
    'SelectionCriteria',

    # RoundRobin and Manual patterns
    'RoundRobinPattern',
    'WeightedRoundRobinPattern',
    'ManualPattern',
    'InteractivePattern',

    # Pattern selector
    'PatternSelector',
    'TaskAnalysis',
    'TaskComplexity',
    'TaskType',
    'PatternRecommendation',
    'select_pattern',
]


# Version
__version__ = '1.0.0'
