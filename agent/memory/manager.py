"""
Memory Manager

Unified interface for all memory types.
Provides centralized memory processing and context management.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from .storage import (
    InMemoryStorage,
    SQLiteStorage,
    TaskStorage,
    GraphStorage,
    MemoryItem,
    Entity,
    TaskResult
)
from .short_term import ShortTermMemory, STMConfig, ConversationBuffer
from .long_term import LongTermMemory, LTMConfig
from .entity import EntityMemory, EntityConfig
from .contextual import ContextualMemory, Context, ContextConfig


@dataclass
class MemoryConfig:
    """Configuration for the Memory Manager"""
    # Storage paths
    stm_max_items: int = 100
    ltm_db_path: str = ":memory:"
    entity_max_items: int = 1000

    # Feature flags
    enable_embeddings: bool = True
    enable_entity_extraction: bool = True
    enable_pattern_learning: bool = True

    # User settings
    default_user_id: str = "default"

    # Storage configs
    stm_config: Optional[STMConfig] = None
    ltm_config: Optional[LTMConfig] = None
    entity_config: Optional[EntityConfig] = None
    context_config: Optional[ContextConfig] = None


def default_memory_config() -> MemoryConfig:
    """Get default memory configuration"""
    return MemoryConfig(
        stm_max_items=100,
        ltm_db_path=":memory:",
        stm_config=STMConfig(),
        ltm_config=LTMConfig(),
        entity_config=EntityConfig(),
        context_config=ContextConfig()
    )


class MemoryManager:
    """
    Unified memory management for all memory types.

    Provides:
    - Centralized message processing
    - Automatic context building
    - Memory persistence management
    - LLM context formatting

    Usage:
        manager = MemoryManager(config=default_memory_config())

        manager.process_message("I'm building a website for my bakery", "user")
        manager.process_message("I'll use Next.js with Tailwind", "assistant")
        manager.process_message("The bakery is called Sweet Dreams", "user")

        context = manager.get_context_for_llm("What framework are we using?")
        # Returns formatted context including "Next.js" and "Sweet Dreams"
    """

    def __init__(
        self,
        config: Optional[MemoryConfig] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        async_embedding_fn: Optional[Callable[[str], Awaitable[List[float]]]] = None,
        llm_extract_fn: Optional[Callable[[str], Awaitable[List[Dict]]]] = None
    ):
        """
        Initialize Memory Manager.

        Args:
            config: Memory configuration
            embedding_fn: Sync function to generate embeddings
            async_embedding_fn: Async function to generate embeddings
            llm_extract_fn: Async function for LLM-based entity extraction
        """
        self.config = config or default_memory_config()

        # Initialize storage backends
        stm_storage = InMemoryStorage(max_items=self.config.stm_max_items)
        ltm_storage = TaskStorage(db_path=self.config.ltm_db_path)
        entity_storage = GraphStorage()

        # Initialize memory components
        self.stm = ShortTermMemory(
            storage=stm_storage,
            config=self.config.stm_config,
            embedding_fn=embedding_fn if self.config.enable_embeddings else None,
            async_embedding_fn=async_embedding_fn if self.config.enable_embeddings else None
        )

        self.ltm = LongTermMemory(
            storage=ltm_storage,
            config=self.config.ltm_config,
            embedding_fn=embedding_fn if self.config.enable_embeddings else None,
            async_embedding_fn=async_embedding_fn if self.config.enable_embeddings else None
        )

        self.entity = EntityMemory(
            storage=entity_storage,
            config=self.config.entity_config,
            llm_extract_fn=llm_extract_fn if self.config.enable_entity_extraction else None
        )

        self.contextual = ContextualMemory(
            stm=self.stm,
            ltm=self.ltm,
            entity=self.entity,
            config=self.config.context_config,
            user_id=self.config.default_user_id
        )

        # Conversation buffer for raw messages
        self._buffer = ConversationBuffer()

        # Current session info
        self._current_user_id = self.config.default_user_id
        self._session_start = datetime.now()
        self._message_count = 0

    def process_message(
        self,
        message: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Process incoming message across all memory types.

        Args:
            message: Message content
            role: Message role ("user", "assistant", "system")
            metadata: Optional metadata
        """
        if not message.strip():
            return

        self._message_count += 1
        metadata = metadata or {}
        metadata["role"] = role
        metadata["message_number"] = self._message_count

        # Add to conversation buffer
        self._buffer.add_message(role, message, metadata)

        # Add to short-term memory
        self.stm.add(message, metadata)
        self.stm.increment_turn()

        # Extract entities if enabled
        if self.config.enable_entity_extraction:
            self.entity.extract_and_add(message)

        # Learn preferences from user messages
        if role == "user" and self.config.enable_pattern_learning:
            self._learn_from_message(message)

    async def process_message_async(
        self,
        message: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Async version of process_message"""
        if not message.strip():
            return

        self._message_count += 1
        metadata = metadata or {}
        metadata["role"] = role
        metadata["message_number"] = self._message_count

        self._buffer.add_message(role, message, metadata)

        await self.stm.add_async(message, metadata)
        self.stm.increment_turn()

        if self.config.enable_entity_extraction:
            await self.entity.extract_and_add_async(message)

        if role == "user" and self.config.enable_pattern_learning:
            self._learn_from_message(message)

    def _learn_from_message(self, message: str):
        """Learn preferences and patterns from user message"""
        message_lower = message.lower()

        # Simple preference detection patterns
        preference_patterns = [
            (r"i prefer (\w+)", "preference"),
            (r"i like (\w+)", "preference"),
            (r"use (\w+) framework", "framework_preference"),
            (r"(\w+) is better", "preference"),
            (r"i want it in (\w+)", "style_preference"),
        ]

        import re
        for pattern, pref_type in preference_patterns:
            match = re.search(pattern, message_lower)
            if match:
                value = match.group(1)
                self.ltm.learn_pattern(
                    pref_type,
                    f"User prefers {value}",
                    {"source": message, "value": value}
                )

    def get_context_for_llm(
        self,
        query: str,
        max_length: int = 2000,
        include_all: bool = True
    ) -> str:
        """
        Format memory context for LLM prompt.

        Args:
            query: Current query/input
            max_length: Maximum context length
            include_all: Whether to include all context types

        Returns:
            Formatted context string for LLM
        """
        context = self.contextual.build_context(
            current_input=query,
            include_all=include_all
        )

        return context.to_prompt_text(max_length=max_length)

    async def get_context_for_llm_async(
        self,
        query: str,
        max_length: int = 2000,
        include_all: bool = True
    ) -> str:
        """Async version of get_context_for_llm"""
        context = await self.contextual.build_context_async(
            current_input=query,
            include_all=include_all
        )

        return context.to_prompt_text(max_length=max_length)

    def get_context(self, query: str) -> Context:
        """Get full context object"""
        return self.contextual.build_context(query)

    async def get_context_async(self, query: str) -> Context:
        """Async version of get_context"""
        return await self.contextual.build_context_async(query)

    # Task management

    def store_task(
        self,
        task_id: str,
        description: str,
        result: str,
        status: str = "completed",
        files: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a completed task"""
        return self.ltm.store_task_result(task_id, {
            "description": description,
            "result": result,
            "status": status,
            "files": files or [],
            "metadata": metadata or {}
        })

    def get_similar_tasks(
        self,
        description: str,
        top_k: int = 5
    ) -> List[TaskResult]:
        """Find similar past tasks"""
        return self.ltm.get_similar_tasks(description, top_k=top_k)

    # User preferences

    def set_user(self, user_id: str):
        """Set current user"""
        self._current_user_id = user_id
        self.contextual.update_user(user_id)

    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user's preferences"""
        return self.ltm.get_user_preferences(self._current_user_id)

    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        self.ltm.store_user_preference(self._current_user_id, key, value)

    # Entity management

    def get_entity(self, name: str) -> Optional[Entity]:
        """Get entity by name"""
        return self.entity.get_entity_by_name(name)

    def get_all_entities(self) -> List[Entity]:
        """Get all known entities"""
        return self.entity.storage.get_all_entities()

    # Session management

    def new_session(self, user_id: Optional[str] = None):
        """Start a new session (clears short-term memory)"""
        self.stm.new_conversation()
        self._buffer.clear()
        self._session_start = datetime.now()
        self._message_count = 0

        if user_id:
            self.set_user(user_id)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "user_id": self._current_user_id,
            "session_start": self._session_start.isoformat(),
            "message_count": self._message_count,
            "stm_items": self.stm.count,
            "entities_mentioned": self.entity.count,
            "conversation": self._buffer.get_formatted_history(10)
        }

    def get_conversation_history(self, n: Optional[int] = None) -> List[Dict]:
        """Get conversation history"""
        return self._buffer.get_messages(n)

    # Statistics and insights

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return {
            "short_term": {
                "item_count": self.stm.count,
                "turn_count": self.stm.turn_count,
                "conversation_id": self.stm.conversation_id
            },
            "long_term": self.ltm.get_insights(self._current_user_id),
            "entities": self.entity.get_statistics(),
            "session": {
                "user_id": self._current_user_id,
                "message_count": self._message_count,
                "duration_seconds": (datetime.now() - self._session_start).total_seconds()
            }
        }

    # Cleanup

    def clear_short_term(self):
        """Clear short-term memory only"""
        self.stm.clear()
        self._buffer.clear()

    def clear_all(self):
        """Clear all memory"""
        self.stm.clear()
        self.entity.clear()
        self._buffer.clear()
        # Note: LTM is typically not cleared

    def close(self):
        """Close all storage connections"""
        self.ltm.close()


# =============================================================================
# Convenience Functions
# =============================================================================

def create_memory_manager(
    db_path: str = ":memory:",
    embedding_fn: Optional[Callable[[str], List[float]]] = None
) -> MemoryManager:
    """
    Create a memory manager with default settings.

    Args:
        db_path: Path for SQLite storage
        embedding_fn: Optional embedding function

    Returns:
        Configured MemoryManager
    """
    config = MemoryConfig(ltm_db_path=db_path)
    return MemoryManager(config=config, embedding_fn=embedding_fn)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'MemoryConfig',
    'MemoryManager',
    'default_memory_config',
    'create_memory_manager',
]
