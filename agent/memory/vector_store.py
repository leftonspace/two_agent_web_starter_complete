"""
PHASE 10.1: Long-term Context Storage
PHASE 4.2 HARDENING: Memory TTL and Expiration

Vector-based memory storage for semantic search of historical context.
Stores meeting summaries, decisions, action items, and preferences.

Features:
- ChromaDB for vector storage
- OpenAI embeddings for semantic search
- Metadata filtering (user, project, date)
- Memory type classification
- Relevance scoring
- TTL (Time-To-Live) for automatic memory expiration (Phase 4.2)
- Automatic cleanup of expired memories
- Configurable default TTL per memory type
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[VectorStore] ChromaDB not available - install with: pip install chromadb")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[VectorStore] OpenAI not available - install with: pip install openai")


class MemoryType(Enum):
    """Types of memories that can be stored."""
    MEETING_SUMMARY = "meeting_summary"
    DECISION = "decision"
    ACTION_ITEM = "action_item"
    PREFERENCE = "preference"
    FEEDBACK = "feedback"
    NOTE = "note"
    INSIGHT = "insight"
    OBSERVATION = "observation"  # For storing conversation interactions


# ============================================================================
# PHASE 4.2: Default TTL Configuration (in seconds)
# ============================================================================

# Default TTL values per memory type - customize based on business needs
DEFAULT_TTL_BY_TYPE: Dict[MemoryType, Optional[int]] = {
    MemoryType.MEETING_SUMMARY: 90 * 24 * 60 * 60,  # 90 days
    MemoryType.DECISION: 180 * 24 * 60 * 60,        # 180 days (6 months)
    MemoryType.ACTION_ITEM: 30 * 24 * 60 * 60,      # 30 days
    MemoryType.PREFERENCE: None,                     # No expiration (permanent)
    MemoryType.FEEDBACK: 60 * 24 * 60 * 60,         # 60 days
    MemoryType.NOTE: 30 * 24 * 60 * 60,             # 30 days
    MemoryType.INSIGHT: 90 * 24 * 60 * 60,          # 90 days
    MemoryType.OBSERVATION: 7 * 24 * 60 * 60,       # 7 days (short-term)
}

# Global default TTL if not specified per type (30 days)
DEFAULT_MEMORY_TTL_SECONDS: int = 30 * 24 * 60 * 60

# How often to run automatic cleanup (in searches)
CLEANUP_EVERY_N_SEARCHES: int = 100


@dataclass
class Memory:
    """Represents a stored memory."""
    id: str
    content: str
    memory_type: MemoryType
    metadata: Dict[str, Any]
    timestamp: float
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Memory:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            metadata=data.get("metadata", {}),
            timestamp=data["timestamp"],
            embedding=data.get("embedding"),
        )


class VectorMemoryStore:
    """
    Long-term memory with vector search.

    Uses ChromaDB for vector storage and OpenAI for embeddings.
    Supports semantic search, filtering, and metadata queries.

    PHASE 4.2: Supports TTL-based memory expiration:
    - Each memory can have an optional expires_at timestamp
    - Automatic cleanup of expired memories during searches
    - Configurable default TTL per memory type
    """

    def __init__(
        self,
        collection_name: str = "business_memory",
        persist_directory: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        default_ttl_seconds: Optional[int] = None,
        auto_cleanup: bool = True,
    ):
        """
        Initialize vector memory store.

        Args:
            collection_name: Name of ChromaDB collection
            persist_directory: Directory to persist data (default: ./chroma_db)
            embedding_model: OpenAI embedding model to use
            default_ttl_seconds: Default TTL for memories (None = use per-type defaults)
            auto_cleanup: Whether to automatically clean up expired memories
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")

        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.default_ttl_seconds = default_ttl_seconds
        self.auto_cleanup = auto_cleanup

        # Setup persistence directory
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent.parent / "chroma_db")

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False,
        ))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )

        # Statistics
        self.total_stores = 0
        self.total_searches = 0
        self.cache_hits = 0
        self.total_expired_cleaned = 0  # Phase 4.2: Track expired memory cleanup

        # Bounded embedding cache with LRU eviction to prevent memory leaks
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_access_order: List[str] = []  # Track access order for LRU
        self._max_cache_size: int = 1000  # Maximum cached embeddings

        # Phase 4.2: Track last cleanup time
        self._last_cleanup_search_count: int = 0

    def _cache_put(self, key: str, embedding: List[float]):
        """Add embedding to cache with LRU eviction."""
        # If key already exists, update access order
        if key in self._embedding_cache:
            self._cache_access_order.remove(key)
            self._cache_access_order.append(key)
            self._embedding_cache[key] = embedding
            return

        # Evict oldest entries if cache is full
        while len(self._embedding_cache) >= self._max_cache_size:
            oldest_key = self._cache_access_order.pop(0)
            del self._embedding_cache[oldest_key]

        # Add new entry
        self._embedding_cache[key] = embedding
        self._cache_access_order.append(key)

    def _cache_get(self, key: str) -> Optional[List[float]]:
        """Get embedding from cache, updating access order."""
        if key in self._embedding_cache:
            # Update access order (move to end)
            self._cache_access_order.remove(key)
            self._cache_access_order.append(key)
            self.cache_hits += 1
            return self._embedding_cache[key]
        return None

    async def _create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            List of embedding values
        """
        # Check cache first
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        if not OPENAI_AVAILABLE:
            # Fallback: generate dummy embedding for testing
            print("[VectorStore] OpenAI not available - using dummy embeddings")
            import random
            random.seed(hash(text))
            embedding = [random.random() for _ in range(1536)]
            return embedding

        try:
            # Get API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")

            # Create embedding
            import openai
            client = openai.OpenAI(api_key=api_key)

            response = client.embeddings.create(
                model=self.embedding_model,
                input=text
            )

            embedding = response.data[0].embedding

            # Cache it with LRU eviction
            self._cache_put(cache_key, embedding)

            return embedding

        except Exception as e:
            print(f"[VectorStore] Error creating embedding: {e}")
            # Return dummy embedding as fallback
            import random
            random.seed(hash(text))
            return [random.random() for _ in range(1536)]

    def _get_ttl_for_type(self, memory_type: MemoryType) -> Optional[int]:
        """
        Get default TTL for a memory type.

        Phase 4.2: Returns the appropriate TTL based on:
        1. Instance default (if set)
        2. Per-type default from DEFAULT_TTL_BY_TYPE
        3. Global DEFAULT_MEMORY_TTL_SECONDS

        Args:
            memory_type: Type of memory

        Returns:
            TTL in seconds, or None for no expiration
        """
        # Instance-level override
        if self.default_ttl_seconds is not None:
            return self.default_ttl_seconds

        # Per-type default
        type_ttl = DEFAULT_TTL_BY_TYPE.get(memory_type)
        if type_ttl is not None:
            return type_ttl

        # If type not in dict (new type), use global default
        if memory_type not in DEFAULT_TTL_BY_TYPE:
            return DEFAULT_MEMORY_TTL_SECONDS

        # Type explicitly set to None (no expiration)
        return None

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
        ttl_seconds: Optional[int] = -1,  # -1 = use default, None = no expiration
    ) -> str:
        """
        Store memory with embedding.

        Phase 4.2: Supports TTL-based expiration.

        Args:
            content: Memory content text
            memory_type: Type of memory
            metadata: Additional metadata (user, project, etc.)
            memory_id: Optional custom ID (auto-generated if not provided)
            ttl_seconds: Time-to-live in seconds:
                         -1 = use default TTL for memory type
                         None = no expiration (permanent)
                         >0 = custom TTL

        Returns:
            Memory ID
        """
        self.total_stores += 1

        # Generate ID if not provided
        if memory_id is None:
            memory_id = str(uuid.uuid4())

        # Prepare metadata
        if metadata is None:
            metadata = {}

        current_time = time.time()
        metadata["memory_type"] = memory_type.value
        metadata["timestamp"] = current_time
        metadata["created_at"] = datetime.now().isoformat()

        # Phase 4.2: Calculate expiration timestamp
        if ttl_seconds == -1:
            # Use default TTL for this memory type
            effective_ttl = self._get_ttl_for_type(memory_type)
        else:
            effective_ttl = ttl_seconds

        if effective_ttl is not None and effective_ttl > 0:
            expires_at = current_time + effective_ttl
            metadata["expires_at"] = expires_at
            metadata["ttl_seconds"] = effective_ttl
        else:
            # No expiration - mark as permanent
            metadata["expires_at"] = None
            metadata["ttl_seconds"] = None

        # Create embedding
        embedding = await self._create_embedding(content)

        # Store in ChromaDB
        try:
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )

            ttl_info = f", TTL={effective_ttl}s" if effective_ttl else ", permanent"
            print(f"[VectorStore] Stored memory {memory_id} ({memory_type.value}{ttl_info})")
            return memory_id

        except Exception as e:
            print(f"[VectorStore] Error storing memory: {e}")
            raise

    async def search_similar(
        self,
        query: str,
        n_results: int = 5,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_expired: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant memories.

        Phase 4.2: Filters out expired memories by default.

        Args:
            query: Search query text
            n_results: Number of results to return
            memory_type: Filter by memory type
            filters: Additional metadata filters
            include_expired: If True, include expired memories in results

        Returns:
            List of matching memories with relevance scores
        """
        self.total_searches += 1

        # Phase 4.2: Trigger periodic cleanup
        self._maybe_cleanup()

        # Create query embedding
        query_embedding = await self._create_embedding(query)

        # Build where clause for filtering
        where_clause = {}
        if memory_type:
            where_clause["memory_type"] = memory_type.value

        if filters:
            where_clause.update(filters)

        # Query ChromaDB - request extra results to account for expired filtering
        extra_results = n_results * 2 if not include_expired else n_results

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=extra_results,
                where=where_clause if where_clause else None,
            )

            # Format results, filtering expired memories
            memories = []
            expired_count = 0

            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    metadata = results["metadatas"][0][i]

                    # Phase 4.2: Filter out expired memories
                    if not include_expired and self.is_memory_expired(metadata):
                        expired_count += 1
                        continue

                    memory = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": metadata,
                        "distance": results["distances"][0][i] if "distances" in results else None,
                        "relevance_score": 1.0 - results["distances"][0][i] if "distances" in results else 1.0,
                    }

                    # Add expiration info to result
                    expires_at = metadata.get("expires_at")
                    if expires_at:
                        memory["expires_in_seconds"] = max(0, expires_at - time.time())
                        memory["is_expired"] = memory["expires_in_seconds"] == 0

                    memories.append(memory)

                    # Stop once we have enough results
                    if len(memories) >= n_results:
                        break

            if expired_count > 0:
                print(f"[VectorStore] Filtered {expired_count} expired memories from results")

            print(f"[VectorStore] Found {len(memories)} similar memories")
            return memories

        except Exception as e:
            print(f"[VectorStore] Error searching memories: {e}")
            return []

    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory dict or None if not found
        """
        try:
            result = self.collection.get(ids=[memory_id])

            if result["ids"] and len(result["ids"]) > 0:
                return {
                    "id": result["ids"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0],
                }

            return None

        except Exception as e:
            print(f"[VectorStore] Error getting memory: {e}")
            return None

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update existing memory.

        Args:
            memory_id: Memory ID
            content: New content (if updating)
            metadata: New metadata (merged with existing)

        Returns:
            True if successful
        """
        try:
            # Get existing memory
            existing = await self.get_memory(memory_id)
            if not existing:
                print(f"[VectorStore] Memory {memory_id} not found")
                return False

            # Update content and embedding if provided
            if content:
                embedding = await self._create_embedding(content)
            else:
                content = existing["content"]
                embedding = None

            # Merge metadata
            updated_metadata = existing["metadata"].copy()
            if metadata:
                updated_metadata.update(metadata)
            updated_metadata["updated_at"] = datetime.now().isoformat()

            # Update in ChromaDB
            update_data: Dict[str, Any] = {
                "ids": [memory_id],
                "documents": [content],
                "metadatas": [updated_metadata],
            }

            if embedding:
                update_data["embeddings"] = [embedding]

            self.collection.update(**update_data)

            print(f"[VectorStore] Updated memory {memory_id}")
            return True

        except Exception as e:
            print(f"[VectorStore] Error updating memory: {e}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[memory_id])
            print(f"[VectorStore] Deleted memory {memory_id}")
            return True

        except Exception as e:
            print(f"[VectorStore] Error deleting memory: {e}")
            return False

    # ========================================================================
    # PHASE 4.2: TTL and Expiration Methods
    # ========================================================================

    def is_memory_expired(self, metadata: Dict[str, Any]) -> bool:
        """
        Check if a memory has expired based on its metadata.

        Args:
            metadata: Memory metadata dict

        Returns:
            True if expired, False otherwise
        """
        expires_at = metadata.get("expires_at")

        # No expiration set = not expired
        if expires_at is None:
            return False

        # Check against current time
        return time.time() > expires_at

    async def cleanup_expired_memories(self, batch_size: int = 100) -> int:
        """
        Remove all expired memories from the store.

        Phase 4.2: Scans all memories and deletes those past their expires_at.

        Args:
            batch_size: Number of memories to check per batch

        Returns:
            Number of memories deleted
        """
        deleted_count = 0
        current_time = time.time()

        try:
            # Get all memories with expiration set
            # Note: ChromaDB doesn't support complex queries, so we fetch all
            # and filter in Python
            all_memories = self.collection.get()

            if not all_memories["ids"]:
                return 0

            # Find expired IDs
            expired_ids = []
            for i, memory_id in enumerate(all_memories["ids"]):
                metadata = all_memories["metadatas"][i]
                expires_at = metadata.get("expires_at")

                if expires_at is not None and current_time > expires_at:
                    expired_ids.append(memory_id)

            # Delete in batches
            if expired_ids:
                for i in range(0, len(expired_ids), batch_size):
                    batch = expired_ids[i:i + batch_size]
                    self.collection.delete(ids=batch)
                    deleted_count += len(batch)

                self.total_expired_cleaned += deleted_count
                print(f"[VectorStore] Cleaned up {deleted_count} expired memories")

            return deleted_count

        except Exception as e:
            print(f"[VectorStore] Error cleaning up expired memories: {e}")
            return deleted_count

    def _maybe_cleanup(self) -> None:
        """
        Trigger cleanup if enough searches have occurred.

        Phase 4.2: Called during search operations to periodically clean up.
        """
        if not self.auto_cleanup:
            return

        if self.total_searches - self._last_cleanup_search_count >= CLEANUP_EVERY_N_SEARCHES:
            self._last_cleanup_search_count = self.total_searches
            # Run cleanup asynchronously without blocking
            try:
                asyncio.create_task(self.cleanup_expired_memories())
            except RuntimeError:
                # No event loop running - skip async cleanup
                pass

    async def get_expiring_soon(
        self,
        within_seconds: int = 86400,  # 24 hours
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get memories that will expire soon.

        Useful for notifications or proactive renewal.

        Args:
            within_seconds: Time window in seconds
            limit: Maximum number of results

        Returns:
            List of memories expiring within the time window
        """
        current_time = time.time()
        expiring_threshold = current_time + within_seconds

        try:
            all_memories = self.collection.get()

            if not all_memories["ids"]:
                return []

            expiring = []
            for i, memory_id in enumerate(all_memories["ids"]):
                metadata = all_memories["metadatas"][i]
                expires_at = metadata.get("expires_at")

                if expires_at is not None:
                    if current_time < expires_at <= expiring_threshold:
                        expiring.append({
                            "id": memory_id,
                            "content": all_memories["documents"][i],
                            "metadata": metadata,
                            "expires_in_seconds": expires_at - current_time,
                        })

            # Sort by expiration time (soonest first)
            expiring.sort(key=lambda x: x["expires_in_seconds"])

            return expiring[:limit]

        except Exception as e:
            print(f"[VectorStore] Error getting expiring memories: {e}")
            return []

    async def extend_ttl(
        self,
        memory_id: str,
        additional_seconds: int,
    ) -> bool:
        """
        Extend the TTL of an existing memory.

        Args:
            memory_id: Memory ID
            additional_seconds: Seconds to add to current expiration

        Returns:
            True if successful
        """
        try:
            memory = await self.get_memory(memory_id)
            if not memory:
                return False

            metadata = memory["metadata"]
            current_expires = metadata.get("expires_at")

            if current_expires is None:
                # Memory doesn't expire - nothing to extend
                return True

            # Extend expiration
            new_expires = max(current_expires, time.time()) + additional_seconds
            metadata["expires_at"] = new_expires
            metadata["ttl_extended_at"] = datetime.now().isoformat()

            # Update metadata
            self.collection.update(
                ids=[memory_id],
                metadatas=[metadata],
            )

            print(f"[VectorStore] Extended TTL for {memory_id} to {new_expires}")
            return True

        except Exception as e:
            print(f"[VectorStore] Error extending TTL: {e}")
            return False

    def count_memories(self, memory_type: Optional[MemoryType] = None) -> int:
        """
        Count total memories.

        Args:
            memory_type: Filter by type

        Returns:
            Number of memories
        """
        try:
            if memory_type:
                result = self.collection.get(
                    where={"memory_type": memory_type.value}
                )
                return len(result["ids"]) if result["ids"] else 0
            else:
                return self.collection.count()

        except Exception as e:
            print(f"[VectorStore] Error counting memories: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Phase 4.2: Includes TTL and expiration statistics.
        """
        # Count expired memories
        expired_count = 0
        expiring_soon_count = 0
        permanent_count = 0
        current_time = time.time()
        soon_threshold = current_time + 86400  # 24 hours

        try:
            all_memories = self.collection.get()
            if all_memories["ids"]:
                for metadata in all_memories["metadatas"]:
                    expires_at = metadata.get("expires_at")
                    if expires_at is None:
                        permanent_count += 1
                    elif current_time > expires_at:
                        expired_count += 1
                    elif expires_at <= soon_threshold:
                        expiring_soon_count += 1
        except Exception:
            pass

        return {
            "collection_name": self.collection_name,
            "total_memories": self.collection.count(),
            "total_stores": self.total_stores,
            "total_searches": self.total_searches,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.total_stores, 1),
            # Phase 4.2: TTL statistics
            "ttl_stats": {
                "expired_count": expired_count,
                "expiring_soon_count": expiring_soon_count,
                "permanent_count": permanent_count,
                "total_cleaned": self.total_expired_cleaned,
                "auto_cleanup_enabled": self.auto_cleanup,
            },
        }
