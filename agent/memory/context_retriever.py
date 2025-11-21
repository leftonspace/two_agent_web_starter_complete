"""
PHASE 10.2: Contextual Recall

Smart retrieval system for finding relevant past information.
Provides time-weighted relevance, filtering, and context summarization.

Features:
- Semantic similarity search
- Time decay weighting (recent memories more relevant)
- User/project/type filtering
- Context summarization
- Relevance scoring
"""

from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    from .vector_store import VectorMemoryStore, MemoryType
except ImportError:
    from vector_store import VectorMemoryStore, MemoryType


@dataclass
class RetrievalContext:
    """Context for retrieval operations."""
    user: Optional[str] = None
    project: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    time_window_days: Optional[int] = None  # Only retrieve memories from last N days
    max_results: int = 10
    min_relevance_score: float = 0.5


@dataclass
class RetrievedMemory:
    """Memory with relevance scoring."""
    id: str
    content: str
    memory_type: str
    metadata: Dict[str, Any]
    timestamp: float
    semantic_score: float  # Raw similarity score
    time_score: float  # Time decay score
    final_score: float  # Combined score
    age_days: float

    @classmethod
    def from_search_result(
        cls,
        result: Dict[str, Any],
        time_decay_factor: float = 0.1,
    ) -> RetrievedMemory:
        """
        Create from search result with time weighting.

        Args:
            result: Search result from vector store
            time_decay_factor: How much to weight recent memories (0-1)

        Returns:
            RetrievedMemory with calculated scores
        """
        timestamp = result["metadata"].get("timestamp", time.time())
        age_seconds = time.time() - timestamp
        age_days = age_seconds / 86400  # Convert to days

        # Semantic similarity score (from vector search)
        semantic_score = result.get("relevance_score", 0.5)

        # Time decay: exponential decay based on age
        # More recent = higher score
        time_score = math.exp(-time_decay_factor * age_days)

        # Combined score (weighted average)
        final_score = 0.7 * semantic_score + 0.3 * time_score

        return cls(
            id=result["id"],
            content=result["content"],
            memory_type=result["metadata"].get("memory_type", "unknown"),
            metadata=result["metadata"],
            timestamp=timestamp,
            semantic_score=semantic_score,
            time_score=time_score,
            final_score=final_score,
            age_days=age_days,
        )


class ContextRetriever:
    """
    Smart context retrieval system.

    Retrieves relevant historical context with:
    - Time-weighted relevance
    - User/project filtering
    - Context summarization
    """

    def __init__(
        self,
        vector_store: VectorMemoryStore,
        time_decay_factor: float = 0.1,
    ):
        """
        Initialize context retriever.

        Args:
            vector_store: Vector memory store instance
            time_decay_factor: Time decay weighting (higher = favor recent more)
        """
        self.vector_store = vector_store
        self.time_decay_factor = time_decay_factor

        # Statistics
        self.total_retrievals = 0
        self.cache_hits = 0

    async def retrieve_context(
        self,
        query: str,
        context: Optional[RetrievalContext] = None,
    ) -> List[RetrievedMemory]:
        """
        Retrieve relevant context for a query.

        Args:
            query: Search query
            context: Retrieval context with filters

        Returns:
            List of relevant memories sorted by final score
        """
        self.total_retrievals += 1

        if context is None:
            context = RetrievalContext()

        # Build filters
        filters = {}
        if context.user:
            filters["user"] = context.user
        if context.project:
            filters["project"] = context.project

        # Search each memory type if specified
        all_results = []

        if context.memory_types:
            # Search each type separately
            for memory_type in context.memory_types:
                results = await self.vector_store.search_similar(
                    query=query,
                    n_results=context.max_results,
                    memory_type=memory_type,
                    filters=filters if filters else None,
                )
                all_results.extend(results)
        else:
            # Search all types
            all_results = await self.vector_store.search_similar(
                query=query,
                n_results=context.max_results,
                filters=filters if filters else None,
            )

        # Convert to RetrievedMemory with time weighting
        memories = [
            RetrievedMemory.from_search_result(result, self.time_decay_factor)
            for result in all_results
        ]

        # Filter by time window
        if context.time_window_days:
            max_age_days = context.time_window_days
            memories = [m for m in memories if m.age_days <= max_age_days]

        # Filter by minimum relevance
        memories = [m for m in memories if m.final_score >= context.min_relevance_score]

        # Sort by final score (descending)
        memories.sort(key=lambda m: m.final_score, reverse=True)

        # Limit results
        memories = memories[:context.max_results]

        print(f"[ContextRetriever] Retrieved {len(memories)} relevant memories")

        return memories

    async def retrieve_recent(
        self,
        memory_type: Optional[MemoryType] = None,
        days: int = 7,
        max_results: int = 10,
        user: Optional[str] = None,
        project: Optional[str] = None,
    ) -> List[RetrievedMemory]:
        """
        Retrieve recent memories (chronologically).

        Args:
            memory_type: Filter by type
            days: Number of days to look back
            max_results: Maximum results
            user: Filter by user
            project: Filter by project

        Returns:
            List of recent memories
        """
        # Use a generic query to get all memories
        context = RetrievalContext(
            user=user,
            project=project,
            memory_types=[memory_type] if memory_type else None,
            time_window_days=days,
            max_results=max_results,
            min_relevance_score=0.0,  # No relevance filtering for recency query
        )

        memories = await self.retrieve_context("", context)

        # Sort by timestamp (most recent first)
        memories.sort(key=lambda m: m.timestamp, reverse=True)

        return memories

    async def summarize_context(
        self,
        memories: List[RetrievedMemory],
        max_length: int = 500,
    ) -> str:
        """
        Summarize retrieved context into a concise text.

        Args:
            memories: Retrieved memories
            max_length: Maximum summary length

        Returns:
            Summary text
        """
        if not memories:
            return "No relevant context found."

        # Group by memory type
        by_type: Dict[str, List[RetrievedMemory]] = {}
        for memory in memories:
            mem_type = memory.memory_type
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(memory)

        # Build summary
        summary_parts = []

        # Add type summaries
        for mem_type, mems in sorted(by_type.items()):
            if mem_type == "meeting_summary":
                summary_parts.append(f"Recent meetings ({len(mems)}):")
                for mem in mems[:3]:  # Top 3
                    age = self._format_age(mem.age_days)
                    snippet = mem.content[:100] + "..." if len(mem.content) > 100 else mem.content
                    summary_parts.append(f"  - {age}: {snippet}")

            elif mem_type == "decision":
                summary_parts.append(f"Key decisions ({len(mems)}):")
                for mem in mems[:3]:
                    age = self._format_age(mem.age_days)
                    snippet = mem.content[:100] + "..." if len(mem.content) > 100 else mem.content
                    summary_parts.append(f"  - {age}: {snippet}")

            elif mem_type == "action_item":
                summary_parts.append(f"Action items ({len(mems)}):")
                for mem in mems[:3]:
                    snippet = mem.content[:100] + "..." if len(mem.content) > 100 else mem.content
                    summary_parts.append(f"  - {snippet}")

            elif mem_type == "preference":
                summary_parts.append(f"Preferences ({len(mems)}):")
                for mem in mems[:3]:
                    summary_parts.append(f"  - {mem.content}")

        summary = "\n".join(summary_parts)

        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."

        return summary

    def _format_age(self, age_days: float) -> str:
        """Format age in human-readable form."""
        if age_days < 1:
            hours = int(age_days * 24)
            return f"{hours}h ago"
        elif age_days < 7:
            return f"{int(age_days)}d ago"
        elif age_days < 30:
            weeks = int(age_days / 7)
            return f"{weeks}w ago"
        else:
            months = int(age_days / 30)
            return f"{months}mo ago"

    async def find_related_decisions(
        self,
        topic: str,
        project: Optional[str] = None,
        days: int = 90,
    ) -> List[RetrievedMemory]:
        """
        Find decisions related to a topic.

        Args:
            topic: Topic to search for
            project: Filter by project
            days: Look back days

        Returns:
            List of related decisions
        """
        context = RetrievalContext(
            project=project,
            memory_types=[MemoryType.DECISION],
            time_window_days=days,
            max_results=10,
        )

        return await self.retrieve_context(topic, context)

    async def find_action_items(
        self,
        user: Optional[str] = None,
        project: Optional[str] = None,
        days: int = 30,
    ) -> List[RetrievedMemory]:
        """
        Find action items (recent).

        Args:
            user: Filter by assigned user
            project: Filter by project
            days: Look back days

        Returns:
            List of action items
        """
        context = RetrievalContext(
            user=user,
            project=project,
            memory_types=[MemoryType.ACTION_ITEM],
            time_window_days=days,
            max_results=20,
            min_relevance_score=0.0,  # Return all action items
        )

        return await self.retrieve_context("", context)

    async def find_user_preferences(
        self,
        user: str,
        category: Optional[str] = None,
    ) -> List[RetrievedMemory]:
        """
        Find user preferences.

        Args:
            user: User identifier
            category: Optional category filter

        Returns:
            List of preferences
        """
        query = category if category else ""

        context = RetrievalContext(
            user=user,
            memory_types=[MemoryType.PREFERENCE],
            max_results=20,
            min_relevance_score=0.0,
        )

        return await self.retrieve_context(query, context)

    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            "total_retrievals": self.total_retrievals,
            "cache_hits": self.cache_hits,
            "time_decay_factor": self.time_decay_factor,
            "vector_store_stats": self.vector_store.get_statistics(),
        }
