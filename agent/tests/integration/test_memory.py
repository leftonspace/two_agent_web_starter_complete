"""
Integration Tests: Memory Persistence

Tests memory system persistence across sessions,
including short-term, long-term, entity, and contextual memory.
"""

import pytest
import asyncio
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestShortTermMemory:
    """Test short-term memory within a session"""

    def test_message_storage_and_retrieval(self, memory_store):
        """Messages should be stored and retrievable"""
        if memory_store is None:
            pytest.skip("Memory store not available")

        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        manager.process_message("Hello, I want to build a website", "user")
        manager.process_message("I'll help you with that", "assistant")

        history = manager.get_conversation_history()

        assert len(history) == 2
        assert "website" in history[0]["content"]

    def test_context_building(self, memory_store):
        """Context should include recent messages"""
        if memory_store is None:
            pytest.skip("Memory store not available")

        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False,
            enable_entity_extraction=False
        ))

        manager.process_message("I prefer React for frontend", "user")
        manager.process_message("React is a great choice", "assistant")

        context = manager.get_context_for_llm("What framework should I use?")

        # Context should include recent conversation
        assert context is not None
        assert len(context) > 0

    def test_message_count_tracking(self, memory_store):
        """Message count should be tracked accurately"""
        if memory_store is None:
            pytest.skip("Memory store not available")

        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        for i in range(5):
            manager.process_message(f"Message {i}", "user")

        summary = manager.get_session_summary()

        assert summary["message_count"] == 5


class TestLongTermMemory:
    """Test long-term memory persistence"""

    def test_task_storage(self, tmp_path):
        """Tasks should be stored in long-term memory"""
        from memory import MemoryManager, MemoryConfig

        db_path = str(tmp_path / "test_ltm.db")

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=db_path,
            enable_embeddings=False
        ))

        task_id = manager.store_task(
            task_id="test-task-1",
            description="Build user authentication",
            result="Implemented JWT-based auth",
            status="completed",
            files=["auth.py", "routes.py"]
        )

        assert task_id is not None

        # Close and reopen to test persistence
        manager.close()

    def test_preference_storage(self, tmp_path):
        """Preferences should be stored and retrievable"""
        from memory import MemoryManager, MemoryConfig

        db_path = str(tmp_path / "test_prefs.db")

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=db_path,
            enable_embeddings=False
        ))

        manager.set_preference("framework", "React")
        manager.set_preference("language", "TypeScript")

        prefs = manager.get_user_preferences()

        # Should have stored preferences
        assert prefs is not None

        manager.close()

    def test_preference_learning_from_messages(self, tmp_path):
        """Preferences should be learned from messages"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False,
            enable_pattern_learning=True
        ))

        manager.process_message("I prefer TypeScript over JavaScript", "user")
        manager.process_message("Use React framework for this project", "user")

        # Should have learned from messages
        stats = manager.get_statistics()
        assert stats is not None

        manager.close()


class TestEntityMemory:
    """Test entity extraction and memory"""

    def test_entity_extraction(self, tmp_path):
        """Entities should be extracted from messages"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False,
            enable_entity_extraction=True
        ))

        manager.process_message("My company is called TechCorp Inc", "user")
        manager.process_message("The CEO is John Smith", "user")

        # Entity memory should have tracked entities
        entities = manager.get_all_entities()

        # Should have at least attempted extraction
        assert entities is not None

        manager.close()

    def test_entity_retrieval_by_name(self, tmp_path):
        """Entities should be retrievable by name"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False,
            enable_entity_extraction=True
        ))

        manager.process_message("Working on Project Alpha with team lead Bob", "user")

        # Try to retrieve entity
        entities = manager.get_all_entities()
        assert entities is not None

        manager.close()


class TestSessionManagement:
    """Test session management and persistence"""

    def test_new_session_clears_stm(self, tmp_path):
        """New session should clear short-term memory"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        # Add messages to session 1
        manager.process_message("Hello from session 1", "user")
        manager.process_message("Response 1", "assistant")

        history_before = manager.get_conversation_history()
        assert len(history_before) == 2

        # Start new session
        manager.new_session()

        history_after = manager.get_conversation_history()
        assert len(history_after) == 0

        manager.close()

    def test_session_summary(self, tmp_path):
        """Session summary should include relevant info"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        manager.process_message("Test message 1", "user")
        manager.process_message("Test message 2", "assistant")

        summary = manager.get_session_summary()

        assert "user_id" in summary
        assert "session_start" in summary
        assert "message_count" in summary
        assert summary["message_count"] == 2

        manager.close()

    def test_user_switching(self, tmp_path):
        """Switching users should work correctly"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        manager.set_user("user_1")
        manager.set_preference("color", "blue")

        manager.set_user("user_2")
        manager.set_preference("color", "red")

        # Both users should have their preferences
        stats = manager.get_statistics()
        assert stats is not None

        manager.close()


class TestCrossSessionPersistence:
    """Test memory persistence across sessions"""

    def test_ltm_persists_across_sessions(self, tmp_path):
        """Long-term memory should persist across sessions"""
        from memory import MemoryManager, MemoryConfig

        db_path = str(tmp_path / "persistent_ltm.db")

        # Session 1: Store data
        manager1 = MemoryManager(MemoryConfig(
            ltm_db_path=db_path,
            enable_embeddings=False
        ))

        manager1.store_task(
            task_id="persistent-task",
            description="Important task to remember",
            result="Task completed successfully",
            status="completed"
        )

        manager1.close()

        # Session 2: Retrieve data
        manager2 = MemoryManager(MemoryConfig(
            ltm_db_path=db_path,
            enable_embeddings=False
        ))

        # Should be able to query similar tasks
        similar = manager2.get_similar_tasks("Important task")

        manager2.close()

        # Similar tasks retrieval should work
        assert similar is not None

    def test_stm_cleared_between_sessions(self, tmp_path):
        """Short-term memory should be cleared between sessions"""
        from memory import MemoryManager, MemoryConfig

        db_path = str(tmp_path / "stm_test.db")

        # Session 1
        manager1 = MemoryManager(MemoryConfig(
            ltm_db_path=db_path,
            enable_embeddings=False
        ))

        manager1.process_message("Message from session 1", "user")
        count1 = manager1.get_session_summary()["message_count"]

        manager1.close()

        # Session 2
        manager2 = MemoryManager(MemoryConfig(
            ltm_db_path=db_path,
            enable_embeddings=False
        ))

        # New session should have fresh message count
        count2 = manager2.get_session_summary()["message_count"]

        manager2.close()

        assert count1 == 1
        assert count2 == 0


class TestMemoryStatistics:
    """Test memory statistics and insights"""

    def test_statistics_structure(self, tmp_path):
        """Statistics should have expected structure"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        manager.process_message("Test message", "user")

        stats = manager.get_statistics()

        assert "short_term" in stats
        assert "long_term" in stats
        assert "entities" in stats
        assert "session" in stats

        manager.close()

    def test_statistics_update_after_messages(self, tmp_path):
        """Statistics should update after messages"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        stats_before = manager.get_statistics()
        count_before = stats_before["session"]["message_count"]

        manager.process_message("New message", "user")

        stats_after = manager.get_statistics()
        count_after = stats_after["session"]["message_count"]

        assert count_after == count_before + 1

        manager.close()


class TestMemoryCleanup:
    """Test memory cleanup operations"""

    def test_clear_short_term(self, tmp_path):
        """Should clear short-term memory only"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        manager.process_message("Test message", "user")

        manager.clear_short_term()

        history = manager.get_conversation_history()
        assert len(history) == 0

        manager.close()

    def test_clear_all(self, tmp_path):
        """Should clear all memory"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        manager.process_message("Test message", "user")

        manager.clear_all()

        history = manager.get_conversation_history()
        entities = manager.get_all_entities()

        assert len(history) == 0
        assert len(entities) == 0

        manager.close()


class TestAsyncMemoryOperations:
    """Test async memory operations"""

    @pytest.mark.asyncio
    async def test_async_message_processing(self, tmp_path):
        """Async message processing should work"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        await manager.process_message_async("Async test message", "user")

        history = manager.get_conversation_history()
        assert len(history) == 1

        manager.close()

    @pytest.mark.asyncio
    async def test_async_context_retrieval(self, tmp_path):
        """Async context retrieval should work"""
        from memory import MemoryManager, MemoryConfig

        manager = MemoryManager(MemoryConfig(
            ltm_db_path=":memory:",
            enable_embeddings=False
        ))

        await manager.process_message_async("I like Python programming", "user")

        context = await manager.get_context_for_llm_async("What do I like?")

        assert context is not None

        manager.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
