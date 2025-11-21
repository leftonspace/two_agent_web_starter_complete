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
"""

from .vector_store import VectorMemoryStore, MemoryType
from .context_retriever import ContextRetriever, RetrievalContext

__all__ = [
    "VectorMemoryStore",
    "MemoryType",
    "ContextRetriever",
    "RetrievalContext",
]
