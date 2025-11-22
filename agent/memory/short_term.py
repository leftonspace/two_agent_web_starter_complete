"""
Short-Term Memory (STM)

RAG-based memory for current conversation context.
Provides fast semantic search over recent interactions.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

from .storage import MemoryStorage, InMemoryStorage, MemoryItem


@dataclass
class STMConfig:
    """Configuration for Short-Term Memory"""
    max_items: int = 100
    embedding_dim: int = 384
    auto_embed: bool = True
    dedup_threshold: float = 0.95  # Similarity threshold for deduplication
    metadata_default: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """
    RAG-based memory for current conversation context.

    Provides:
    - Auto-embedding of content
    - Semantic similarity search
    - Conversation history tracking
    - Automatic deduplication

    Usage:
        stm = ShortTermMemory(storage=InMemoryStorage())

        stm.add("The user wants a blue website", {"type": "preference"})
        stm.add("React is the preferred framework", {"type": "technical"})

        results = stm.search("what color does user want", top_k=1)
        # Returns items related to "blue website"
    """

    def __init__(
        self,
        storage: Optional[MemoryStorage] = None,
        config: Optional[STMConfig] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        async_embedding_fn: Optional[Callable[[str], Awaitable[List[float]]]] = None
    ):
        """
        Initialize Short-Term Memory.

        Args:
            storage: Storage backend (default: InMemoryStorage)
            config: STM configuration
            embedding_fn: Sync function to generate embeddings
            async_embedding_fn: Async function to generate embeddings
        """
        self.config = config or STMConfig()
        self.storage = storage or InMemoryStorage(max_items=self.config.max_items)
        self.embedding_fn = embedding_fn
        self.async_embedding_fn = async_embedding_fn

        # Conversation tracking
        self._conversation_id: Optional[str] = None
        self._turn_count: int = 0
        self._content_hashes: set = set()  # For deduplication

    def add(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Add item with auto-embedding.

        Args:
            content: Text content to store
            metadata: Optional metadata dict
            embedding: Pre-computed embedding (optional)

        Returns:
            ID of the stored item
        """
        if not content.strip():
            return ""

        # Check for duplicates
        content_hash = self._hash_content(content)
        if content_hash in self._content_hashes:
            return ""  # Skip duplicate
        self._content_hashes.add(content_hash)

        # Prepare metadata
        item_metadata = {**self.config.metadata_default}
        if metadata:
            item_metadata.update(metadata)
        item_metadata["turn"] = self._turn_count
        item_metadata["conversation_id"] = self._conversation_id

        # Generate embedding if needed
        if embedding is None and self.config.auto_embed and self.embedding_fn:
            embedding = self.embedding_fn(content)

        # Create and store item
        item = MemoryItem(
            content=content,
            embedding=embedding,
            metadata=item_metadata
        )

        return self.storage.add(item)

    async def add_async(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """Async version of add with async embedding"""
        if not content.strip():
            return ""

        # Check for duplicates
        content_hash = self._hash_content(content)
        if content_hash in self._content_hashes:
            return ""
        self._content_hashes.add(content_hash)

        # Prepare metadata
        item_metadata = {**self.config.metadata_default}
        if metadata:
            item_metadata.update(metadata)
        item_metadata["turn"] = self._turn_count
        item_metadata["conversation_id"] = self._conversation_id

        # Generate embedding if needed
        if embedding is None and self.config.auto_embed and self.async_embedding_fn:
            embedding = await self.async_embedding_fn(content)

        # Create and store item
        item = MemoryItem(
            content=content,
            embedding=embedding,
            metadata=item_metadata
        )

        return self.storage.add(item)

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """
        Semantic search over stored items.

        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filter

        Returns:
            List of matching MemoryItems sorted by relevance
        """
        # Get query embedding
        if self.embedding_fn:
            query_embedding = self.embedding_fn(query)
            results = self.storage.search(query_embedding, top_k=top_k * 2)
        else:
            # Fall back to text search
            if hasattr(self.storage, 'search_by_text'):
                results = self.storage.search_by_text(query, top_k=top_k * 2)
            else:
                results = []

        # Apply metadata filter
        if filter_metadata:
            results = [
                r for r in results
                if self._matches_filter(r.metadata, filter_metadata)
            ]

        return results[:top_k]

    async def search_async(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[MemoryItem]:
        """Async version of search"""
        if self.async_embedding_fn:
            query_embedding = await self.async_embedding_fn(query)
            results = self.storage.search(query_embedding, top_k=top_k * 2)
        else:
            return self.search(query, top_k, filter_metadata)

        if filter_metadata:
            results = [
                r for r in results
                if self._matches_filter(r.metadata, filter_metadata)
            ]

        return results[:top_k]

    def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """Get n most recent items"""
        if hasattr(self.storage, 'get_recent'):
            return self.storage.get_recent(n)
        elif hasattr(self.storage, 'get_all'):
            all_items = self.storage.get_all()
            return all_items[-n:] if len(all_items) > n else all_items
        return []

    def get_by_type(self, item_type: str) -> List[MemoryItem]:
        """Get items by type metadata"""
        return self.search("", top_k=100, filter_metadata={"type": item_type})

    def clear(self):
        """Clear all items for new conversation"""
        self.storage.clear()
        self._content_hashes.clear()
        self._turn_count = 0

    def new_conversation(self, conversation_id: Optional[str] = None):
        """Start a new conversation (clears memory)"""
        self.clear()
        self._conversation_id = conversation_id or self._generate_conversation_id()

    def increment_turn(self):
        """Increment the turn counter"""
        self._turn_count += 1

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation"""
        return {
            "conversation_id": self._conversation_id,
            "turn_count": self._turn_count,
            "item_count": self.storage.count(),
            "items": self.get_recent(5)
        }

    # Helper methods

    def _hash_content(self, content: str) -> str:
        """Generate hash for deduplication"""
        return hashlib.md5(content.strip().lower().encode()).hexdigest()

    def _matches_filter(self, metadata: Dict, filter_dict: Dict) -> bool:
        """Check if metadata matches filter"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def _generate_conversation_id(self) -> str:
        """Generate a unique conversation ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    # Properties

    @property
    def count(self) -> int:
        """Number of items in memory"""
        return self.storage.count()

    @property
    def conversation_id(self) -> Optional[str]:
        return self._conversation_id

    @property
    def turn_count(self) -> int:
        return self._turn_count


class ConversationBuffer:
    """
    Simple buffer for maintaining conversation history.

    Stores raw messages without embeddings for quick access.
    """

    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self._messages: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to the buffer"""
        message = {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        self._messages.append(message)

        # Trim if exceeds max
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

    def get_messages(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent messages"""
        if n is None:
            return self._messages.copy()
        return self._messages[-n:]

    def get_formatted_history(self, n: Optional[int] = None) -> str:
        """Get formatted conversation history"""
        messages = self.get_messages(n)
        lines = []
        for msg in messages:
            lines.append(f"{msg['role']}: {msg['content']}")
        return "\n".join(lines)

    def clear(self):
        """Clear the buffer"""
        self._messages.clear()

    @property
    def count(self) -> int:
        return len(self._messages)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'STMConfig',
    'ShortTermMemory',
    'ConversationBuffer',
]
