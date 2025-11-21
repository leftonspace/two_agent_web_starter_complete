"""
PHASE 10: Business Memory - Long-term Context Storage

This module provides vector-based long-term memory for semantic search:
- Store meeting summaries, decisions, action items
- Semantic search for relevant historical context
- Preference learning across sessions
- Cross-session continuity

Components:
- vector_store: ChromaDB-based vector storage with embeddings
- context_retriever: Smart retrieval with time-weighting and filtering
- preference_learner: Learn and track user preferences
- session_manager: Cross-session continuity and project tracking
"""

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

__all__ = [
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
]
