"""
JARVIS Memory System

Comprehensive multi-type memory system:

- Short-Term Memory (STM): RAG-based memory for current conversation
- Long-Term Memory (LTM): Persistent memory across sessions
- Entity Memory: Track entities mentioned across conversations
- Contextual Memory: Situation-aware memory retrieval
- Memory Manager: Unified interface for all memory types

Legacy components (Phase 10):
- vector_store: ChromaDB-based vector storage with embeddings
- context_retriever: Smart retrieval with time-weighting and filtering
- preference_learner: Learn and track user preferences
- session_manager: Cross-session continuity and project tracking

Usage:
    from agent.memory import MemoryManager, MemoryConfig

    # Create manager with default config
    manager = MemoryManager()

    # Process messages
    manager.process_message("Build a website for my bakery", "user")
    manager.process_message("I'll use React with Tailwind", "assistant")

    # Get context for LLM
    context = manager.get_context_for_llm("What framework?")
"""

# Legacy exports (Phase 10)
from .vector_store import VectorMemoryStore, MemoryType
from .context_retriever import ContextRetriever, RetrievalContext
from .preference_learner import PreferenceLearner, PreferenceCategory, Preference
from .session_manager import (
    SessionManager,
    Session,
    Project,
    Task,
    ProjectStatus,
    TaskStatus,
)

# New Storage backends
from .storage import (
    MemoryItem,
    Entity,
    EntityContext,
    TaskResult,
    MemoryStorage,
    InMemoryStorage,
    SQLiteStorage,
    TaskStorage,
    GraphStorage,
)

# Short-Term Memory
from .short_term import (
    STMConfig,
    ShortTermMemory,
    ConversationBuffer,
)

# Long-Term Memory
from .long_term import (
    LTMConfig,
    LongTermMemory,
    LearnedPattern,
)

# Entity Memory
from .entity import (
    EntityConfig,
    EntityMemory,
    DictStorage,
)

# Contextual Memory
from .contextual import (
    Context,
    ContextConfig,
    ContextualMemory,
)

# Memory Manager
from .manager import (
    MemoryConfig,
    MemoryManager,
    default_memory_config,
    create_memory_manager,
)


__all__ = [
    # Legacy (Phase 10)
    "VectorMemoryStore",
    "MemoryType",
    "ContextRetriever",
    "RetrievalContext",
    "PreferenceLearner",
    "PreferenceCategory",
    "Preference",
    "SessionManager",
    "Session",
    "Project",
    "Task",
    "ProjectStatus",
    "TaskStatus",

    # Storage
    'MemoryItem',
    'Entity',
    'EntityContext',
    'TaskResult',
    'MemoryStorage',
    'InMemoryStorage',
    'SQLiteStorage',
    'TaskStorage',
    'GraphStorage',

    # Short-Term Memory
    'STMConfig',
    'ShortTermMemory',
    'ConversationBuffer',

    # Long-Term Memory
    'LTMConfig',
    'LongTermMemory',
    'LearnedPattern',

    # Entity Memory
    'EntityConfig',
    'EntityMemory',
    'DictStorage',

    # Contextual Memory
    'Context',
    'ContextConfig',
    'ContextualMemory',

    # Memory Manager
    'MemoryConfig',
    'MemoryManager',
    'default_memory_config',
    'create_memory_manager',
]

__version__ = '1.0.0'
