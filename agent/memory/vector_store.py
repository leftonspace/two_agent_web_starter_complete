"""
PHASE 10.1: Long-term Context Storage

Vector-based memory storage for semantic search of historical context.
Stores meeting summaries, decisions, action items, and preferences.

Features:
- ChromaDB for vector storage
- OpenAI embeddings for semantic search
- Metadata filtering (user, project, date)
- Memory type classification
- Relevance scoring
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
    """

    def __init__(
        self,
        collection_name: str = "business_memory",
        persist_directory: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize vector memory store.

        Args:
            collection_name: Name of ChromaDB collection
            persist_directory: Directory to persist data (default: ./chroma_db)
            embedding_model: OpenAI embedding model to use
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB not available. Install with: pip install chromadb")

        self.collection_name = collection_name
        self.embedding_model = embedding_model

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

        # Simple embedding cache
        self._embedding_cache: Dict[str, List[float]] = {}

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
        if cache_key in self._embedding_cache:
            self.cache_hits += 1
            return self._embedding_cache[cache_key]

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

            # Cache it
            self._embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            print(f"[VectorStore] Error creating embedding: {e}")
            # Return dummy embedding as fallback
            import random
            random.seed(hash(text))
            return [random.random() for _ in range(1536)]

    async def store_memory(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[Dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> str:
        """
        Store memory with embedding.

        Args:
            content: Memory content text
            memory_type: Type of memory
            metadata: Additional metadata (user, project, etc.)
            memory_id: Optional custom ID (auto-generated if not provided)

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

        metadata["memory_type"] = memory_type.value
        metadata["timestamp"] = time.time()
        metadata["created_at"] = datetime.now().isoformat()

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

            print(f"[VectorStore] Stored memory {memory_id} ({memory_type.value})")
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
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant memories.

        Args:
            query: Search query text
            n_results: Number of results to return
            memory_type: Filter by memory type
            filters: Additional metadata filters

        Returns:
            List of matching memories with relevance scores
        """
        self.total_searches += 1

        # Create query embedding
        query_embedding = await self._create_embedding(query)

        # Build where clause for filtering
        where_clause = {}
        if memory_type:
            where_clause["memory_type"] = memory_type.value

        if filters:
            where_clause.update(filters)

        # Query ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None,
            )

            # Format results
            memories = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    memory = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None,
                        "relevance_score": 1.0 - results["distances"][0][i] if "distances" in results else 1.0,
                    }
                    memories.append(memory)

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
        """Get usage statistics."""
        return {
            "collection_name": self.collection_name,
            "total_memories": self.collection.count(),
            "total_stores": self.total_stores,
            "total_searches": self.total_searches,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.total_stores, 1),
        }
