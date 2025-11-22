"""
Contextual Memory

Situation-aware memory retrieval that combines all memory types
to build rich context for LLM interactions.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime

from .storage import MemoryItem, Entity, TaskResult
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from .entity import EntityMemory


@dataclass
class Context:
    """Rich context built from all memory sources"""
    # Short-term memories
    recent_messages: List[MemoryItem] = field(default_factory=list)
    relevant_memories: List[MemoryItem] = field(default_factory=list)

    # Long-term context
    similar_tasks: List[TaskResult] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)

    # Entity context
    mentioned_entities: List[Entity] = field(default_factory=list)
    entity_details: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    task_type: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0

    def to_prompt_text(self, max_length: int = 2000) -> str:
        """Format context for LLM prompt"""
        sections = []

        # Recent conversation
        if self.recent_messages:
            messages = []
            for msg in self.recent_messages[-5:]:
                role = msg.metadata.get("role", "unknown")
                messages.append(f"  {role}: {msg.content[:200]}")
            sections.append("Recent Conversation:\n" + "\n".join(messages))

        # Relevant memories
        if self.relevant_memories:
            memories = []
            for mem in self.relevant_memories[:3]:
                memories.append(f"  - {mem.content[:150]}")
            sections.append("Relevant Context:\n" + "\n".join(memories))

        # Similar past tasks
        if self.similar_tasks:
            tasks = []
            for task in self.similar_tasks[:2]:
                tasks.append(f"  - {task.description[:100]} ({task.status})")
            sections.append("Similar Past Tasks:\n" + "\n".join(tasks))

        # User preferences
        if self.user_preferences:
            prefs = []
            for key, value in list(self.user_preferences.items())[:5]:
                prefs.append(f"  - {key}: {value}")
            sections.append("User Preferences:\n" + "\n".join(prefs))

        # Entities
        if self.mentioned_entities:
            entities = []
            for entity in self.mentioned_entities[:5]:
                entities.append(f"  - {entity.name} ({entity.entity_type})")
            sections.append("Known Entities:\n" + "\n".join(entities))

        result = "\n\n".join(sections)

        # Truncate if needed
        if len(result) > max_length:
            result = result[:max_length - 3] + "..."

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "recent_messages": [m.to_dict() for m in self.recent_messages],
            "relevant_memories": [m.to_dict() for m in self.relevant_memories],
            "similar_tasks": [t.to_dict() for t in self.similar_tasks],
            "user_preferences": self.user_preferences,
            "mentioned_entities": [e.to_dict() for e in self.mentioned_entities],
            "entity_details": self.entity_details,
            "task_type": self.task_type,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence
        }


@dataclass
class ContextConfig:
    """Configuration for context building"""
    max_recent_messages: int = 10
    max_relevant_memories: int = 5
    max_similar_tasks: int = 3
    max_entities: int = 10
    include_user_preferences: bool = True
    include_similar_tasks: bool = True
    include_entities: bool = True
    relevance_threshold: float = 0.3


class ContextualMemory:
    """
    Situation-aware memory retrieval.

    Combines Short-Term, Long-Term, and Entity memories to build
    rich context for LLM interactions.

    Usage:
        contextual = ContextualMemory(
            stm=short_term_memory,
            ltm=long_term_memory,
            entity=entity_memory
        )

        context = contextual.build_context(
            current_input="Build a React dashboard",
            task_type="development"
        )

        # Use context in LLM prompt
        prompt_context = context.to_prompt_text()
    """

    def __init__(
        self,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        entity: EntityMemory,
        config: Optional[ContextConfig] = None,
        user_id: Optional[str] = None
    ):
        """
        Initialize Contextual Memory.

        Args:
            stm: Short-Term Memory instance
            ltm: Long-Term Memory instance
            entity: Entity Memory instance
            config: Context building configuration
            user_id: Current user ID for preferences
        """
        self.stm = stm
        self.ltm = ltm
        self.entity = entity
        self.config = config or ContextConfig()
        self.user_id = user_id or "default"

    def build_context(
        self,
        current_input: str,
        task_type: str = "",
        include_all: bool = True
    ) -> Context:
        """
        Build rich context from all memory sources.

        Args:
            current_input: Current user input/query
            task_type: Type of task being performed
            include_all: Whether to include all context types

        Returns:
            Context object with all relevant information
        """
        context = Context(task_type=task_type)

        # 1. Get relevant STM items
        context.recent_messages = self.stm.get_recent(
            self.config.max_recent_messages
        )

        relevant = self.stm.search(
            current_input,
            top_k=self.config.max_relevant_memories
        )
        context.relevant_memories = [
            m for m in relevant
            if m.score >= self.config.relevance_threshold
        ]

        # 2. Find similar past tasks from LTM
        if include_all and self.config.include_similar_tasks:
            context.similar_tasks = self.ltm.get_similar_tasks(
                current_input,
                top_k=self.config.max_similar_tasks
            )

        # 3. Get user preferences
        if include_all and self.config.include_user_preferences:
            context.user_preferences = self.ltm.get_user_preferences(
                self.user_id
            )

        # 4. Extract and enrich entities
        if include_all and self.config.include_entities:
            # Extract entities from current input
            extracted = self.entity.extract_entities(current_input)

            # Get stored entities with context
            for entity in extracted:
                existing = self.entity.get_entity_by_name(entity.name)
                if existing:
                    context.mentioned_entities.append(existing)
                    entity_ctx = self.entity.get_entity_context(entity.name)
                    if entity_ctx:
                        context.entity_details[entity.name] = {
                            "type": existing.entity_type,
                            "related": [e.name for e in entity_ctx.related_entities],
                            "mentions": len(existing.mentions)
                        }
                else:
                    context.mentioned_entities.append(entity)

        # Calculate confidence based on context richness
        context.confidence = self._calculate_confidence(context)

        return context

    async def build_context_async(
        self,
        current_input: str,
        task_type: str = "",
        include_all: bool = True
    ) -> Context:
        """Async version of build_context"""
        context = Context(task_type=task_type)

        # Get STM items
        context.recent_messages = self.stm.get_recent(
            self.config.max_recent_messages
        )

        relevant = await self.stm.search_async(
            current_input,
            top_k=self.config.max_relevant_memories
        )
        context.relevant_memories = [
            m for m in relevant
            if m.score >= self.config.relevance_threshold
        ]

        # Get similar tasks
        if include_all and self.config.include_similar_tasks:
            context.similar_tasks = await self.ltm.get_similar_tasks_async(
                current_input,
                top_k=self.config.max_similar_tasks
            )

        # Get preferences
        if include_all and self.config.include_user_preferences:
            context.user_preferences = self.ltm.get_user_preferences(
                self.user_id
            )

        # Extract entities
        if include_all and self.config.include_entities:
            extracted = await self.entity.extract_and_add_async(current_input)
            for entity in extracted[:self.config.max_entities]:
                entity_ctx = self.entity.get_entity_context(entity.name)
                if entity_ctx:
                    context.mentioned_entities.append(entity_ctx.entity)
                    context.entity_details[entity.name] = {
                        "type": entity_ctx.entity.entity_type,
                        "related": [e.name for e in entity_ctx.related_entities],
                        "summary": entity_ctx.summary
                    }

        context.confidence = self._calculate_confidence(context)
        return context

    def _calculate_confidence(self, context: Context) -> float:
        """Calculate confidence score based on context richness"""
        score = 0.0
        max_score = 0.0

        # Recent messages contribute
        if context.recent_messages:
            score += min(len(context.recent_messages) / 5, 0.2)
        max_score += 0.2

        # Relevant memories contribute
        if context.relevant_memories:
            avg_relevance = sum(m.score for m in context.relevant_memories) / len(context.relevant_memories)
            score += avg_relevance * 0.3
        max_score += 0.3

        # Similar tasks contribute
        if context.similar_tasks:
            score += min(len(context.similar_tasks) / 3, 0.2)
        max_score += 0.2

        # User preferences contribute
        if context.user_preferences:
            score += min(len(context.user_preferences) / 5, 0.15)
        max_score += 0.15

        # Entities contribute
        if context.mentioned_entities:
            score += min(len(context.mentioned_entities) / 5, 0.15)
        max_score += 0.15

        return score / max_score if max_score > 0 else 0.0

    def get_quick_context(self, current_input: str) -> str:
        """
        Get a quick context string without full processing.

        Useful for simple queries that don't need full context.
        """
        recent = self.stm.get_recent(3)

        lines = ["Recent context:"]
        for msg in recent:
            lines.append(f"  - {msg.content[:100]}")

        return "\n".join(lines)

    def update_user(self, user_id: str):
        """Update the current user ID"""
        self.user_id = user_id


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'Context',
    'ContextConfig',
    'ContextualMemory',
]
