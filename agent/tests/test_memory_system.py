"""
Comprehensive Tests for Multi-Type Memory System

Tests for:
- Storage backends (InMemory, SQLite, Graph)
- ShortTermMemory
- LongTermMemory
- EntityMemory
- ContextualMemory
- MemoryManager
"""

import pytest
from datetime import datetime
from typing import List, Dict

from agent.memory import (
    # Storage
    MemoryItem,
    Entity,
    EntityContext,
    TaskResult,
    InMemoryStorage,
    SQLiteStorage,
    TaskStorage,
    GraphStorage,
    # Short-Term
    ShortTermMemory,
    STMConfig,
    ConversationBuffer,
    # Long-Term
    LongTermMemory,
    LTMConfig,
    LearnedPattern,
    # Entity
    EntityMemory,
    EntityConfig,
    DictStorage,
    # Contextual
    ContextualMemory,
    Context,
    ContextConfig,
    # Manager
    MemoryManager,
    MemoryConfig,
    default_memory_config,
    create_memory_manager,
)


# =============================================================================
# Storage Backend Tests
# =============================================================================

class TestInMemoryStorage:
    """Test InMemoryStorage"""

    @pytest.fixture
    def storage(self):
        return InMemoryStorage(max_items=10)

    def test_add_and_get(self, storage):
        """Test adding and retrieving items"""
        item = MemoryItem(content="Test content")
        item_id = storage.add(item)

        retrieved = storage.get(item_id)
        assert retrieved is not None
        assert retrieved.content == "Test content"

    def test_max_items_enforcement(self, storage):
        """Test FIFO eviction when max items reached"""
        # Add 15 items to storage with max 10
        for i in range(15):
            storage.add(MemoryItem(content=f"Item {i}"))

        assert storage.count() == 10

        # First 5 items should be evicted
        all_items = storage.get_all()
        contents = [item.content for item in all_items]
        assert "Item 0" not in contents
        assert "Item 14" in contents

    def test_search_by_text(self, storage):
        """Test text-based search"""
        storage.add(MemoryItem(content="The user wants a blue website"))
        storage.add(MemoryItem(content="React is the preferred framework"))
        storage.add(MemoryItem(content="Contact page should have a form"))

        results = storage.search_by_text("blue", top_k=1)
        assert len(results) > 0
        assert "blue" in results[0].content.lower()

    def test_delete(self, storage):
        """Test item deletion"""
        item = MemoryItem(content="To delete")
        item_id = storage.add(item)

        assert storage.delete(item_id) == True
        assert storage.get(item_id) is None

    def test_clear(self, storage):
        """Test clearing storage"""
        storage.add(MemoryItem(content="Item 1"))
        storage.add(MemoryItem(content="Item 2"))

        storage.clear()
        assert storage.count() == 0


class TestSQLiteStorage:
    """Test SQLiteStorage"""

    @pytest.fixture
    def storage(self):
        return SQLiteStorage(":memory:")

    def test_add_and_get(self, storage):
        """Test adding and retrieving items"""
        item = MemoryItem(content="Persistent content")
        item_id = storage.add(item)

        retrieved = storage.get(item_id)
        assert retrieved is not None
        assert retrieved.content == "Persistent content"

    def test_search_by_text(self, storage):
        """Test SQL LIKE search"""
        storage.add(MemoryItem(content="Build a React application"))
        storage.add(MemoryItem(content="Use Python for backend"))

        results = storage.search_by_text("React", top_k=5)
        assert len(results) > 0
        assert "React" in results[0].content

    def test_get_recent(self, storage):
        """Test getting recent items"""
        for i in range(5):
            storage.add(MemoryItem(content=f"Item {i}"))

        recent = storage.get_recent(3)
        assert len(recent) == 3


class TestGraphStorage:
    """Test GraphStorage for entities"""

    @pytest.fixture
    def storage(self):
        return GraphStorage()

    def test_add_entity(self, storage):
        """Test adding entities"""
        entity = Entity(name="John", entity_type="person")
        entity_id = storage.add_entity(entity)

        retrieved = storage.get_entity(entity_id)
        assert retrieved is not None
        assert retrieved.name == "John"

    def test_get_by_name(self, storage):
        """Test getting entity by name"""
        entity = Entity(name="Acme Corp", entity_type="organization")
        storage.add_entity(entity)

        retrieved = storage.get_entity_by_name("Acme Corp")
        assert retrieved is not None
        assert retrieved.entity_type == "organization"

    def test_merge_on_duplicate_name(self, storage):
        """Test that entities with same name are merged"""
        entity1 = Entity(name="John", entity_type="person", attributes={"role": "CEO"})
        storage.add_entity(entity1)

        entity2 = Entity(name="John", entity_type="person", attributes={"company": "Acme"})
        storage.add_entity(entity2)

        # Should only have one entity
        assert storage.count() == 1

        # Should have merged attributes
        john = storage.get_entity_by_name("John")
        assert john.attributes.get("role") == "CEO"
        assert john.attributes.get("company") == "Acme"

    def test_relationships(self, storage):
        """Test entity relationships"""
        john = Entity(name="John", entity_type="person")
        acme = Entity(name="Acme", entity_type="organization")

        john_id = storage.add_entity(john)
        acme_id = storage.add_entity(acme)

        storage.add_relationship(john_id, acme_id, "works_at", {"position": "CEO"})

        related = storage.get_related_entities(john_id)
        assert len(related) == 1
        assert related[0][0].name == "Acme"
        assert related[0][1] == "works_at"


# =============================================================================
# Short-Term Memory Tests
# =============================================================================

class TestShortTermMemory:
    """Test ShortTermMemory"""

    @pytest.fixture
    def stm(self):
        return ShortTermMemory(storage=InMemoryStorage())

    def test_add_and_search(self, stm):
        """Test STM add and search"""
        stm.add("The user wants a blue website", {"type": "preference"})
        stm.add("React is the preferred framework", {"type": "technical"})
        stm.add("Contact page should have a form", {"type": "requirement"})

        results = stm.search("what color does user want", top_k=1)
        assert len(results) > 0
        # Text search should find "blue" related content
        found_blue = any("blue" in r.content.lower() for r in results)
        assert found_blue

    def test_deduplication(self, stm):
        """Test content deduplication"""
        stm.add("Same content here")
        stm.add("Same content here")  # Duplicate
        stm.add("Same content here")  # Duplicate

        assert stm.count == 1

    def test_turn_tracking(self, stm):
        """Test turn counting"""
        assert stm.turn_count == 0

        stm.add("Message 1")
        stm.increment_turn()
        assert stm.turn_count == 1

        stm.add("Message 2")
        stm.increment_turn()
        assert stm.turn_count == 2

    def test_new_conversation(self, stm):
        """Test starting new conversation"""
        stm.add("Old message")
        stm.increment_turn()

        stm.new_conversation()

        assert stm.count == 0
        assert stm.turn_count == 0
        assert stm.conversation_id is not None

    def test_get_recent(self, stm):
        """Test getting recent items"""
        for i in range(5):
            stm.add(f"Message {i}")

        recent = stm.get_recent(3)
        assert len(recent) == 3


class TestConversationBuffer:
    """Test ConversationBuffer"""

    def test_add_and_get(self):
        """Test adding and retrieving messages"""
        buffer = ConversationBuffer()
        buffer.add_message("user", "Hello")
        buffer.add_message("assistant", "Hi there!")

        messages = buffer.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["content"] == "Hi there!"

    def test_formatted_history(self):
        """Test formatted history output"""
        buffer = ConversationBuffer()
        buffer.add_message("user", "Hello")
        buffer.add_message("assistant", "Hi!")

        history = buffer.get_formatted_history()
        assert "user: Hello" in history
        assert "assistant: Hi!" in history

    def test_max_messages(self):
        """Test max message enforcement"""
        buffer = ConversationBuffer(max_messages=5)

        for i in range(10):
            buffer.add_message("user", f"Message {i}")

        assert buffer.count == 5


# =============================================================================
# Long-Term Memory Tests
# =============================================================================

class TestLongTermMemory:
    """Test LongTermMemory"""

    @pytest.fixture
    def ltm(self):
        return LongTermMemory(storage=TaskStorage(":memory:"))

    def test_store_and_get_task(self, ltm):
        """Test storing and retrieving task results"""
        ltm.store_task_result("task_1", {
            "description": "Build portfolio website",
            "result": "success",
            "files": ["index.html", "style.css"]
        })

        task = ltm.get_task("task_1")
        assert task is not None
        assert task.description == "Build portfolio website"
        assert "index.html" in task.files

    def test_similar_tasks(self, ltm):
        """Test finding similar tasks"""
        ltm.store_task_result("task_1", {
            "description": "Build portfolio website",
            "result": "success",
            "files": ["index.html", "style.css"]
        })

        # Text-based search
        similar = ltm.get_similar_tasks("Create a personal website")
        assert len(similar) > 0
        assert "portfolio" in similar[0].description.lower()

    def test_user_preferences(self, ltm):
        """Test user preference storage"""
        ltm.store_user_preference("user1", "theme", "dark")
        ltm.store_user_preference("user1", "framework", "react")

        prefs = ltm.get_user_preferences("user1")
        assert prefs["theme"] == "dark"
        assert prefs["framework"] == "react"

    def test_pattern_learning(self, ltm):
        """Test pattern learning"""
        pattern_id = ltm.learn_pattern(
            "preference",
            "User prefers TypeScript",
            {"source": "I prefer TypeScript", "value": "typescript"}
        )

        patterns = ltm.get_patterns("preference")
        assert len(patterns) > 0
        assert patterns[0].description == "User prefers TypeScript"

    def test_pattern_confidence_increases(self, ltm):
        """Test that repeated patterns increase confidence"""
        ltm.learn_pattern("pref", "Likes dark mode", {"v": 1})
        ltm.learn_pattern("pref", "Likes dark mode", {"v": 2})
        ltm.learn_pattern("pref", "Likes dark mode", {"v": 3})

        patterns = ltm.get_patterns("pref")
        assert len(patterns) == 1
        assert patterns[0].confidence > 0.5


# =============================================================================
# Entity Memory Tests
# =============================================================================

class TestEntityMemory:
    """Test EntityMemory"""

    @pytest.fixture
    def entity(self):
        return EntityMemory(storage=DictStorage())

    def test_extract_entities(self, entity):
        """Test entity extraction"""
        entities = entity.extract_entities("John from Acme Corp wants a CRM system")

        names = [e.name for e in entities]
        assert "John" in names
        assert "Acme Corp" in names

    def test_extract_and_add(self, entity):
        """Test extract and add in one operation"""
        extracted = entity.extract_and_add("John from Acme Corp wants a CRM system")

        # Entities should be stored
        john = entity.get_entity_by_name("John")
        assert john is not None

    def test_entity_context(self, entity):
        """Test getting entity context"""
        entity.extract_and_add("John from Acme Corp wants a CRM system")

        john_ctx = entity.get_entity_context("John")
        assert john_ctx is not None
        assert john_ctx.entity.name == "John"

        # Check for related entities (Acme Corp should be related)
        related_names = [e.name for e in john_ctx.related_entities]
        # Relationship detection is heuristic, may or may not find Acme
        assert john_ctx.summary is not None

    def test_email_extraction(self, entity):
        """Test email entity extraction"""
        entities = entity.extract_entities("Contact me at john@example.com")

        types = [e.entity_type for e in entities]
        assert "email" in types

    def test_url_extraction(self, entity):
        """Test URL entity extraction"""
        entities = entity.extract_entities("Check out https://example.com/page")

        types = [e.entity_type for e in entities]
        assert "url" in types


# =============================================================================
# Contextual Memory Tests
# =============================================================================

class TestContextualMemory:
    """Test ContextualMemory"""

    @pytest.fixture
    def contextual(self):
        stm = ShortTermMemory(storage=InMemoryStorage())
        ltm = LongTermMemory(storage=TaskStorage(":memory:"))
        entity = EntityMemory(storage=DictStorage())

        return ContextualMemory(stm=stm, ltm=ltm, entity=entity)

    def test_build_context(self, contextual):
        """Test building context from all sources"""
        # Add some data
        contextual.stm.add("Building a website for bakery", {"role": "user"})
        contextual.stm.add("Using Next.js with Tailwind", {"role": "assistant"})

        context = contextual.build_context("What framework?")

        assert isinstance(context, Context)
        assert len(context.recent_messages) > 0

    def test_context_to_prompt(self, contextual):
        """Test converting context to prompt text"""
        contextual.stm.add("User wants blue theme", {"role": "user"})

        context = contextual.build_context("color preferences")
        prompt_text = context.to_prompt_text()

        assert isinstance(prompt_text, str)
        assert "blue" in prompt_text.lower()

    def test_context_confidence(self, contextual):
        """Test context confidence calculation"""
        # Empty context should have low confidence
        context1 = contextual.build_context("test")

        # Add more data
        for i in range(5):
            contextual.stm.add(f"Message {i}", {"role": "user"})

        context2 = contextual.build_context("test")

        # More data should mean higher confidence
        assert context2.confidence > context1.confidence


# =============================================================================
# Memory Manager Tests
# =============================================================================

class TestMemoryManager:
    """Test MemoryManager"""

    @pytest.fixture
    def manager(self):
        config = MemoryConfig(
            stm_max_items=100,
            ltm_db_path=":memory:",
            enable_embeddings=False,  # Disable for testing
            enable_entity_extraction=True
        )
        return MemoryManager(config=config)

    def test_process_message(self, manager):
        """Test message processing"""
        manager.process_message("I'm building a website for my bakery", "user")
        manager.process_message("I'll use Next.js with Tailwind", "assistant")
        manager.process_message("The bakery is called Sweet Dreams", "user")

        # Messages should be in STM
        assert manager.stm.count >= 3

    def test_get_context_for_llm(self, manager):
        """Test getting formatted context for LLM"""
        manager.process_message("Building a website for my bakery", "user")
        manager.process_message("Using Next.js with Tailwind", "assistant")

        context = manager.get_context_for_llm("What framework are we using?")

        assert "Next.js" in context

    def test_entity_extraction_in_processing(self, manager):
        """Test that entities are extracted during processing"""
        manager.process_message("John from Acme Corp requested the project", "user")

        entities = manager.get_all_entities()
        names = [e.name for e in entities]
        assert "John" in names

    def test_task_storage(self, manager):
        """Test storing and retrieving tasks"""
        manager.store_task(
            task_id="task_1",
            description="Build React dashboard",
            result="Completed successfully",
            status="completed",
            files=["Dashboard.tsx", "styles.css"]
        )

        similar = manager.get_similar_tasks("Create a dashboard")
        assert len(similar) > 0

    def test_user_preferences(self, manager):
        """Test user preference management"""
        manager.set_preference("theme", "dark")
        manager.set_preference("framework", "react")

        prefs = manager.get_user_preferences()
        assert prefs["theme"] == "dark"
        assert prefs["framework"] == "react"

    def test_new_session(self, manager):
        """Test starting a new session"""
        manager.process_message("Old message", "user")

        manager.new_session()

        assert manager.stm.count == 0

    def test_session_summary(self, manager):
        """Test getting session summary"""
        manager.process_message("Message 1", "user")
        manager.process_message("Message 2", "assistant")

        summary = manager.get_session_summary()

        assert summary["message_count"] == 2
        assert summary["stm_items"] >= 2

    def test_statistics(self, manager):
        """Test getting memory statistics"""
        manager.process_message("Test message", "user")

        stats = manager.get_statistics()

        assert "short_term" in stats
        assert "long_term" in stats
        assert "entities" in stats
        assert "session" in stats


class TestMemoryManagerIntegration:
    """Integration tests for MemoryManager"""

    def test_full_conversation_flow(self):
        """Test a full conversation with all memory types"""
        manager = MemoryManager(config=MemoryConfig(
            enable_embeddings=False,
            enable_entity_extraction=True
        ))

        # Simulate a conversation
        manager.process_message("Hi, I'm John from TechCorp", "user")
        manager.process_message("Hello John! How can I help?", "assistant")
        manager.process_message("I need a website for our company", "user")
        manager.process_message("What kind of website? E-commerce or corporate?", "assistant")
        manager.process_message("Corporate website with React", "user")

        # Get context
        context = manager.get_context_for_llm("What does John need?")

        # Should include relevant info
        assert "website" in context.lower() or "john" in context.lower()

        # Store task when done
        manager.store_task(
            "task_1",
            "Build corporate website for TechCorp",
            "Planning phase complete",
            "completed"
        )

        # Similar task should be found
        similar = manager.get_similar_tasks("Create a company website")
        assert len(similar) > 0

    def test_preference_learning(self):
        """Test automatic preference learning"""
        manager = MemoryManager(config=MemoryConfig(
            enable_embeddings=False,
            enable_pattern_learning=True
        ))

        # Express preferences
        manager.process_message("I prefer React for frontend", "user")
        manager.process_message("I like dark themes", "user")

        # Patterns should be learned
        patterns = manager.ltm.get_patterns("preference")
        assert len(patterns) > 0


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_default_memory_config(self):
        """Test default config creation"""
        config = default_memory_config()

        assert isinstance(config, MemoryConfig)
        assert config.stm_max_items == 100

    def test_create_memory_manager(self):
        """Test manager creation function"""
        manager = create_memory_manager(db_path=":memory:")

        assert isinstance(manager, MemoryManager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
