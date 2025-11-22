"""
Entity Memory

Track entities mentioned across conversations.
Provides NER extraction and relationship tracking.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import json

from .storage import GraphStorage, Entity, EntityContext


@dataclass
class EntityConfig:
    """Configuration for Entity Memory"""
    enable_auto_extraction: bool = True
    max_entities: int = 1000
    merge_similar: bool = True
    similarity_threshold: float = 0.85
    track_relationships: bool = True


# Common entity patterns for basic NER
ENTITY_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
    "money": r'\$[\d,]+(?:\.\d{2})?',
    "percentage": r'\b\d+(?:\.\d+)?%',
    "version": r'\bv?\d+\.\d+(?:\.\d+)?\b',
}

# Keywords that often indicate entity types
ENTITY_TYPE_INDICATORS = {
    "person": ["CEO", "CTO", "manager", "developer", "engineer", "designer", "Mr.", "Mrs.", "Dr."],
    "organization": ["Inc.", "Corp.", "LLC", "Ltd.", "Company", "Team", "Department"],
    "technology": ["React", "Python", "JavaScript", "API", "database", "server", "framework"],
    "product": ["app", "website", "platform", "system", "tool", "service"],
    "location": ["city", "country", "office", "headquarters", "building"],
}


class EntityMemory:
    """
    Track entities mentioned across conversations.

    Provides:
    - Named Entity Recognition (NER) extraction
    - Entity relationship tracking
    - Context accumulation for entities
    - Entity search and retrieval

    Usage:
        entity = EntityMemory(storage=GraphStorage())

        entity.extract_and_add("John from Acme Corp wants a CRM system")

        john = entity.get_entity_context("John")
        # Returns EntityContext with related entities ["Acme Corp"]
    """

    def __init__(
        self,
        storage: Optional[GraphStorage] = None,
        config: Optional[EntityConfig] = None,
        llm_extract_fn: Optional[Callable[[str], Awaitable[List[Dict]]]] = None
    ):
        """
        Initialize Entity Memory.

        Args:
            storage: GraphStorage backend
            config: Entity memory configuration
            llm_extract_fn: Optional async LLM function for NER
        """
        self.config = config or EntityConfig()
        self.storage = storage or GraphStorage()
        self.llm_extract_fn = llm_extract_fn

    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text using pattern matching.

        For production use, integrate with spaCy or LLM-based NER.

        Args:
            text: Text to extract entities from

        Returns:
            List of extracted Entity objects
        """
        entities = []

        # Extract pattern-based entities
        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            for match in matches:
                entity = Entity(
                    name=match,
                    entity_type=entity_type,
                    attributes={"source": "pattern"}
                )
                entities.append(entity)

        # Extract potential named entities (capitalized sequences)
        # Simple heuristic: sequences of 1-3 capitalized words
        cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
        matches = re.findall(cap_pattern, text)

        # Filter out common words and determine type
        common_words = {"The", "This", "That", "What", "When", "Where", "How", "Why",
                        "Yes", "No", "Please", "Thanks", "Hello", "Hi", "Sure"}

        for match in matches:
            if match not in common_words:
                entity_type = self._infer_entity_type(match, text)
                entity = Entity(
                    name=match,
                    entity_type=entity_type,
                    attributes={"source": "capitalization"}
                )
                entities.append(entity)

        return entities

    async def extract_entities_async(self, text: str) -> List[Entity]:
        """
        Extract entities using LLM if available, otherwise pattern matching.
        """
        if self.llm_extract_fn:
            try:
                llm_entities = await self.llm_extract_fn(text)
                return [
                    Entity(
                        name=e.get("name", ""),
                        entity_type=e.get("type", "unknown"),
                        attributes=e.get("attributes", {})
                    )
                    for e in llm_entities
                    if e.get("name")
                ]
            except Exception:
                pass

        return self.extract_entities(text)

    def _infer_entity_type(self, name: str, context: str) -> str:
        """Infer entity type from name and context"""
        context_lower = context.lower()
        name_lower = name.lower()

        for entity_type, indicators in ENTITY_TYPE_INDICATORS.items():
            for indicator in indicators:
                if indicator.lower() in context_lower:
                    # Check if indicator is near the entity
                    if self._words_near(name, indicator, context):
                        return entity_type

        # Default guesses based on patterns
        if any(word in name for word in ["Inc", "Corp", "LLC", "Ltd"]):
            return "organization"
        if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', name):
            return "person"  # Two capitalized words often a name

        return "unknown"

    def _words_near(self, word1: str, word2: str, text: str, distance: int = 50) -> bool:
        """Check if two words are near each other in text"""
        pos1 = text.lower().find(word1.lower())
        pos2 = text.lower().find(word2.lower())
        if pos1 == -1 or pos2 == -1:
            return False
        return abs(pos1 - pos2) < distance

    def add_entity(self, entity: Entity, context: str = ""):
        """
        Add or update entity with context.

        Args:
            entity: Entity to add
            context: Context where entity was mentioned
        """
        if context:
            entity.add_mention(context)

        self.storage.add_entity(entity)

    def extract_and_add(self, text: str) -> List[Entity]:
        """
        Extract entities from text and add them to storage.

        Also detects and stores relationships between entities.

        Args:
            text: Text to process

        Returns:
            List of extracted entities
        """
        entities = self.extract_entities(text)

        for entity in entities:
            entity.add_mention(text)
            self.storage.add_entity(entity)

        # Detect relationships if multiple entities found
        if self.config.track_relationships and len(entities) > 1:
            self._detect_relationships(entities, text)

        return entities

    async def extract_and_add_async(self, text: str) -> List[Entity]:
        """Async version of extract_and_add"""
        entities = await self.extract_entities_async(text)

        for entity in entities:
            entity.add_mention(text)
            self.storage.add_entity(entity)

        if self.config.track_relationships and len(entities) > 1:
            self._detect_relationships(entities, text)

        return entities

    def _detect_relationships(self, entities: List[Entity], context: str):
        """Detect relationships between entities in the same context"""
        # Simple heuristic: entities in same sentence are related
        relationship_keywords = {
            "works at": "employment",
            "works for": "employment",
            "from": "affiliation",
            "at": "affiliation",
            "of": "membership",
            "with": "association",
            "and": "association",
            "owns": "ownership",
            "manages": "management",
            "leads": "leadership",
        }

        context_lower = context.lower()

        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Check for relationship keywords between entities
                for keyword, relation_type in relationship_keywords.items():
                    pattern = rf'{re.escape(entity1.name.lower())}.*{keyword}.*{re.escape(entity2.name.lower())}'
                    if re.search(pattern, context_lower):
                        self.storage.add_relationship(
                            entity1.id,
                            entity2.id,
                            relation_type,
                            {"context": context, "keyword": keyword}
                        )
                        break

                    # Also check reverse
                    pattern = rf'{re.escape(entity2.name.lower())}.*{keyword}.*{re.escape(entity1.name.lower())}'
                    if re.search(pattern, context_lower):
                        self.storage.add_relationship(
                            entity2.id,
                            entity1.id,
                            relation_type,
                            {"context": context, "keyword": keyword}
                        )
                        break

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.storage.get_entity(entity_id)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get entity by name"""
        return self.storage.get_entity_by_name(name)

    def get_entity_context(self, entity_name: str) -> Optional[EntityContext]:
        """
        Get all known information about entity.

        Args:
            entity_name: Name of the entity

        Returns:
            EntityContext with entity, related entities, and mentions
        """
        entity = self.storage.get_entity_by_name(entity_name)
        if not entity:
            return None

        # Get related entities
        related_tuples = self.storage.get_related_entities(entity.id)
        related_entities = [e for e, _, _ in related_tuples]

        # Get recent mentions
        recent_mentions = entity.mentions[-10:] if entity.mentions else []

        # Generate summary
        summary = self._generate_entity_summary(entity, related_entities)

        return EntityContext(
            entity=entity,
            related_entities=related_entities,
            recent_mentions=recent_mentions,
            summary=summary
        )

    def get_related_entities(self, entity_name: str) -> List[Entity]:
        """Get entities related to this one"""
        entity = self.storage.get_entity_by_name(entity_name)
        if not entity:
            return []

        related_tuples = self.storage.get_related_entities(entity.id)
        return [e for e, _, _ in related_tuples]

    def _generate_entity_summary(
        self,
        entity: Entity,
        related: List[Entity]
    ) -> str:
        """Generate a text summary of entity knowledge"""
        parts = [f"{entity.name} ({entity.entity_type})"]

        if entity.attributes:
            attrs = ", ".join(f"{k}: {v}" for k, v in entity.attributes.items()
                            if k != "source")
            if attrs:
                parts.append(f"Attributes: {attrs}")

        if related:
            related_names = [e.name for e in related[:5]]
            parts.append(f"Related to: {', '.join(related_names)}")

        if entity.mentions:
            parts.append(f"Mentioned {len(entity.mentions)} time(s)")

        return ". ".join(parts)

    def search_entities(
        self,
        query: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Entity]:
        """
        Search entities by name or type.

        Args:
            query: Name search query
            entity_type: Filter by entity type
            limit: Maximum results

        Returns:
            List of matching entities
        """
        return self.storage.search_entities(
            query=query,
            entity_type=entity_type,
            limit=limit
        )

    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type"""
        return self.search_entities(entity_type=entity_type, limit=100)

    def merge_entities(self, entity_ids: List[str], primary_id: str):
        """
        Merge multiple entities into one.

        Args:
            entity_ids: IDs of entities to merge
            primary_id: ID of the entity to keep
        """
        primary = self.storage.get_entity(primary_id)
        if not primary:
            return

        for entity_id in entity_ids:
            if entity_id == primary_id:
                continue

            entity = self.storage.get_entity(entity_id)
            if entity:
                # Merge mentions
                primary.mentions.extend(entity.mentions)

                # Merge attributes
                for key, value in entity.attributes.items():
                    if key not in primary.attributes:
                        primary.attributes[key] = value

                # Delete merged entity
                self.storage.delete_entity(entity_id)

        # Update primary
        self.storage.add_entity(primary)

    def clear(self):
        """Clear all entities"""
        self.storage.clear()

    @property
    def count(self) -> int:
        """Number of entities in memory"""
        return self.storage.count()

    def get_statistics(self) -> Dict[str, Any]:
        """Get entity memory statistics"""
        all_entities = self.storage.get_all_entities()

        type_counts = {}
        for entity in all_entities:
            t = entity.entity_type
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "total_entities": len(all_entities),
            "by_type": type_counts,
            "most_mentioned": sorted(
                all_entities,
                key=lambda e: len(e.mentions),
                reverse=True
            )[:5]
        }


# Convenience class for simple entity tracking
class DictStorage(GraphStorage):
    """Alias for GraphStorage for backwards compatibility"""
    pass


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'EntityConfig',
    'EntityMemory',
    'DictStorage',
    'ENTITY_PATTERNS',
    'ENTITY_TYPE_INDICATORS',
]
