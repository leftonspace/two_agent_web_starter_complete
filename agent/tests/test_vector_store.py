"""
PHASE 10.1: Vector Store Tests

Tests for vector-based long-term memory storage.
"""

import asyncio
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.vector_store import VectorMemoryStore, MemoryType, Memory


@pytest.fixture
def temp_chroma_dir():
    """Create temporary ChromaDB directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def vector_store(temp_chroma_dir):
    """Create vector store instance with temporary storage."""
    return VectorMemoryStore(
        collection_name="test_memory",
        persist_directory=temp_chroma_dir,
    )


@pytest.mark.asyncio
async def test_vector_store_initialization(temp_chroma_dir):
    """Test vector store initialization."""
    store = VectorMemoryStore(
        collection_name="test",
        persist_directory=temp_chroma_dir,
    )

    assert store.collection_name == "test"
    assert store.total_stores == 0
    assert store.total_searches == 0


@pytest.mark.asyncio
async def test_store_memory(vector_store):
    """Test storing a memory."""
    memory_id = await vector_store.store_memory(
        content="Team meeting on 2024-01-15. Discussed Q1 roadmap.",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={
            "user": "john@example.com",
            "project": "product_launch",
        }
    )

    assert memory_id is not None
    assert vector_store.total_stores == 1

    # Verify memory was stored
    count = vector_store.count_memories()
    assert count == 1


@pytest.mark.asyncio
async def test_store_memory_with_custom_id(vector_store):
    """Test storing memory with custom ID."""
    custom_id = "meeting-2024-01-15"

    memory_id = await vector_store.store_memory(
        content="Custom ID test",
        memory_type=MemoryType.NOTE,
        memory_id=custom_id,
    )

    assert memory_id == custom_id


@pytest.mark.asyncio
async def test_get_memory(vector_store):
    """Test retrieving specific memory by ID."""
    # Store a memory
    memory_id = await vector_store.store_memory(
        content="Test memory content",
        memory_type=MemoryType.NOTE,
        metadata={"test": "value"}
    )

    # Retrieve it
    memory = await vector_store.get_memory(memory_id)

    assert memory is not None
    assert memory["id"] == memory_id
    assert memory["content"] == "Test memory content"
    assert memory["metadata"]["test"] == "value"


@pytest.mark.asyncio
async def test_get_nonexistent_memory(vector_store):
    """Test retrieving non-existent memory."""
    memory = await vector_store.get_memory("nonexistent-id")
    assert memory is None


@pytest.mark.asyncio
async def test_search_similar(vector_store):
    """Test semantic search for similar memories."""
    # Store multiple memories
    await vector_store.store_memory(
        content="Meeting about product launch timeline",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"project": "product_launch"}
    )

    await vector_store.store_memory(
        content="Decision to postpone feature X to Q2",
        memory_type=MemoryType.DECISION,
        metadata={"project": "product_launch"}
    )

    await vector_store.store_memory(
        content="User prefers email notifications over Slack",
        memory_type=MemoryType.PREFERENCE,
        metadata={"user": "john@example.com"}
    )

    # Search for product-related memories
    results = await vector_store.search_similar(
        query="product launch plans",
        n_results=3
    )

    assert len(results) > 0
    assert vector_store.total_searches == 1

    # Check result structure
    result = results[0]
    assert "id" in result
    assert "content" in result
    assert "metadata" in result
    assert "relevance_score" in result


@pytest.mark.asyncio
async def test_search_with_type_filter(vector_store):
    """Test search with memory type filter."""
    # Store memories of different types
    await vector_store.store_memory(
        content="Meeting summary text",
        memory_type=MemoryType.MEETING_SUMMARY,
    )

    await vector_store.store_memory(
        content="Decision text",
        memory_type=MemoryType.DECISION,
    )

    # Search only for decisions
    results = await vector_store.search_similar(
        query="decision",
        memory_type=MemoryType.DECISION,
        n_results=5
    )

    # Should only return decisions
    for result in results:
        assert result["metadata"]["memory_type"] == MemoryType.DECISION.value


@pytest.mark.asyncio
async def test_search_with_metadata_filter(vector_store):
    """Test search with metadata filters."""
    # Store memories for different projects
    await vector_store.store_memory(
        content="Project A meeting",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"project": "project_a"}
    )

    await vector_store.store_memory(
        content="Project B meeting",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"project": "project_b"}
    )

    # Search only project A
    results = await vector_store.search_similar(
        query="meeting",
        filters={"project": "project_a"},
        n_results=5
    )

    # Should only return project A memories
    for result in results:
        assert result["metadata"]["project"] == "project_a"


@pytest.mark.asyncio
async def test_update_memory(vector_store):
    """Test updating existing memory."""
    # Store initial memory
    memory_id = await vector_store.store_memory(
        content="Original content",
        memory_type=MemoryType.NOTE,
        metadata={"version": "1"}
    )

    # Update content and metadata
    success = await vector_store.update_memory(
        memory_id=memory_id,
        content="Updated content",
        metadata={"version": "2"}
    )

    assert success is True

    # Verify update
    memory = await vector_store.get_memory(memory_id)
    assert memory["content"] == "Updated content"
    assert memory["metadata"]["version"] == "2"
    assert "updated_at" in memory["metadata"]


@pytest.mark.asyncio
async def test_update_nonexistent_memory(vector_store):
    """Test updating non-existent memory."""
    success = await vector_store.update_memory(
        memory_id="nonexistent",
        content="New content"
    )

    assert success is False


@pytest.mark.asyncio
async def test_delete_memory(vector_store):
    """Test deleting memory."""
    # Store memory
    memory_id = await vector_store.store_memory(
        content="To be deleted",
        memory_type=MemoryType.NOTE,
    )

    # Delete it
    success = await vector_store.delete_memory(memory_id)
    assert success is True

    # Verify deletion
    memory = await vector_store.get_memory(memory_id)
    assert memory is None


@pytest.mark.asyncio
async def test_count_memories(vector_store):
    """Test counting memories."""
    # Initially empty
    assert vector_store.count_memories() == 0

    # Add some memories
    await vector_store.store_memory("Memory 1", MemoryType.NOTE)
    await vector_store.store_memory("Memory 2", MemoryType.DECISION)
    await vector_store.store_memory("Memory 3", MemoryType.NOTE)

    # Count all
    assert vector_store.count_memories() == 3

    # Count by type
    assert vector_store.count_memories(MemoryType.NOTE) == 2
    assert vector_store.count_memories(MemoryType.DECISION) == 1


@pytest.mark.asyncio
async def test_embedding_cache(vector_store):
    """Test embedding cache for performance."""
    text = "Test content for caching"

    # First call - not cached
    embedding1 = await vector_store._create_embedding(text)

    # Second call - should be cached
    embedding2 = await vector_store._create_embedding(text)

    # Should be same embedding
    assert embedding1 == embedding2

    # Cache hit should be recorded
    assert vector_store.cache_hits > 0


@pytest.mark.asyncio
async def test_get_statistics(vector_store):
    """Test statistics retrieval."""
    # Perform some operations
    await vector_store.store_memory("Memory 1", MemoryType.NOTE)
    await vector_store.store_memory("Memory 2", MemoryType.DECISION)
    await vector_store.search_similar("test query", n_results=2)

    stats = vector_store.get_statistics()

    assert stats["collection_name"] == "test_memory"
    assert stats["total_memories"] == 2
    assert stats["total_stores"] == 2
    assert stats["total_searches"] == 1
    assert "cache_hit_rate" in stats


@pytest.mark.asyncio
async def test_multiple_memory_types(vector_store):
    """Test storing different memory types."""
    memory_types = [
        (MemoryType.MEETING_SUMMARY, "Meeting summary"),
        (MemoryType.DECISION, "Decision made"),
        (MemoryType.ACTION_ITEM, "Action item assigned"),
        (MemoryType.PREFERENCE, "User preference"),
        (MemoryType.FEEDBACK, "User feedback"),
        (MemoryType.NOTE, "Note taken"),
        (MemoryType.INSIGHT, "Insight discovered"),
    ]

    for mem_type, content in memory_types:
        memory_id = await vector_store.store_memory(content, mem_type)
        assert memory_id is not None

    # Verify all stored
    assert vector_store.count_memories() == len(memory_types)


def test_memory_dataclass():
    """Test Memory dataclass."""
    memory = Memory(
        id="test-id",
        content="Test content",
        memory_type=MemoryType.NOTE,
        metadata={"key": "value"},
        timestamp=time.time(),
    )

    # Test to_dict
    data = memory.to_dict()
    assert data["id"] == "test-id"
    assert data["content"] == "Test content"
    assert data["memory_type"] == "note"

    # Test from_dict
    memory2 = Memory.from_dict(data)
    assert memory2.id == memory.id
    assert memory2.content == memory.content
    assert memory2.memory_type == memory.memory_type


def test_memory_type_enum():
    """Test MemoryType enum values."""
    assert MemoryType.MEETING_SUMMARY.value == "meeting_summary"
    assert MemoryType.DECISION.value == "decision"
    assert MemoryType.ACTION_ITEM.value == "action_item"
    assert MemoryType.PREFERENCE.value == "preference"
