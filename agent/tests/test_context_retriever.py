"""
PHASE 10.2: Context Retriever Tests

Tests for smart context retrieval with time-weighting and filtering.
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.vector_store import VectorMemoryStore, MemoryType
from memory.context_retriever import ContextRetriever, RetrievalContext, RetrievedMemory


@pytest.fixture
def temp_chroma_dir():
    """Create temporary ChromaDB directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def vector_store(temp_chroma_dir):
    """Create vector store instance."""
    return VectorMemoryStore(
        collection_name="test_retrieval",
        persist_directory=temp_chroma_dir,
    )


@pytest.fixture
def retriever(vector_store):
    """Create context retriever instance."""
    return ContextRetriever(vector_store, time_decay_factor=0.1)


@pytest.mark.asyncio
async def test_retriever_initialization(retriever):
    """Test retriever initialization."""
    assert retriever.vector_store is not None
    assert retriever.time_decay_factor == 0.1
    assert retriever.total_retrievals == 0


@pytest.mark.asyncio
async def test_retrieve_context_basic(retriever, vector_store):
    """Test basic context retrieval."""
    # Store some memories
    await vector_store.store_memory(
        content="Meeting about Q1 product launch timeline",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"project": "product_launch"}
    )

    await vector_store.store_memory(
        content="Decision to use React for frontend",
        memory_type=MemoryType.DECISION,
        metadata={"project": "product_launch"}
    )

    # Retrieve context
    memories = await retriever.retrieve_context("product launch plans")

    assert len(memories) > 0
    assert retriever.total_retrievals == 1

    # Check memory structure
    memory = memories[0]
    assert hasattr(memory, "id")
    assert hasattr(memory, "content")
    assert hasattr(memory, "semantic_score")
    assert hasattr(memory, "time_score")
    assert hasattr(memory, "final_score")


@pytest.mark.asyncio
async def test_retrieve_with_user_filter(retriever, vector_store):
    """Test retrieval with user filtering."""
    # Store memories for different users
    await vector_store.store_memory(
        content="User A preference",
        memory_type=MemoryType.PREFERENCE,
        metadata={"user": "user_a@example.com"}
    )

    await vector_store.store_memory(
        content="User B preference",
        memory_type=MemoryType.PREFERENCE,
        metadata={"user": "user_b@example.com"}
    )

    # Retrieve only user A memories
    context = RetrievalContext(user="user_a@example.com")
    memories = await retriever.retrieve_context("preference", context)

    # Should only return user A memories
    for memory in memories:
        assert memory.metadata.get("user") == "user_a@example.com"


@pytest.mark.asyncio
async def test_retrieve_with_project_filter(retriever, vector_store):
    """Test retrieval with project filtering."""
    # Store memories for different projects
    await vector_store.store_memory(
        content="Project X meeting",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"project": "project_x"}
    )

    await vector_store.store_memory(
        content="Project Y meeting",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"project": "project_y"}
    )

    # Retrieve only project X
    context = RetrievalContext(project="project_x")
    memories = await retriever.retrieve_context("meeting", context)

    for memory in memories:
        assert memory.metadata.get("project") == "project_x"


@pytest.mark.asyncio
async def test_retrieve_with_type_filter(retriever, vector_store):
    """Test retrieval with memory type filtering."""
    # Store different types
    await vector_store.store_memory(
        content="Meeting summary",
        memory_type=MemoryType.MEETING_SUMMARY,
    )

    await vector_store.store_memory(
        content="Decision made",
        memory_type=MemoryType.DECISION,
    )

    # Retrieve only decisions
    context = RetrievalContext(memory_types=[MemoryType.DECISION])
    memories = await retriever.retrieve_context("decision", context)

    for memory in memories:
        assert memory.memory_type == MemoryType.DECISION.value


@pytest.mark.asyncio
async def test_retrieve_with_time_window(retriever, vector_store):
    """Test retrieval with time window filtering."""
    current_time = time.time()

    # Store old memory (10 days ago)
    await vector_store.store_memory(
        content="Old meeting",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"timestamp": current_time - (10 * 86400)}
    )

    # Store recent memory (1 day ago)
    await vector_store.store_memory(
        content="Recent meeting",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"timestamp": current_time - 86400}
    )

    # Retrieve only last 7 days
    context = RetrievalContext(time_window_days=7)
    memories = await retriever.retrieve_context("meeting", context)

    # Should only return recent memory
    for memory in memories:
        assert memory.age_days <= 7


@pytest.mark.asyncio
async def test_retrieve_with_min_relevance(retriever, vector_store):
    """Test minimum relevance score filtering."""
    await vector_store.store_memory(
        content="Highly relevant content about product launch",
        memory_type=MemoryType.NOTE,
    )

    # High minimum relevance
    context = RetrievalContext(min_relevance_score=0.8)
    memories = await retriever.retrieve_context("product launch", context)

    # All returned memories should meet threshold
    for memory in memories:
        assert memory.final_score >= 0.8


@pytest.mark.asyncio
async def test_time_decay_scoring(retriever):
    """Test time decay scoring calculation."""
    # Create mock search results with different ages
    old_result = {
        "id": "old",
        "content": "Old memory",
        "metadata": {"timestamp": time.time() - (30 * 86400), "memory_type": "note"},
        "relevance_score": 0.9,
    }

    recent_result = {
        "id": "recent",
        "content": "Recent memory",
        "metadata": {"timestamp": time.time() - 86400, "memory_type": "note"},
        "relevance_score": 0.9,
    }

    old_memory = RetrievedMemory.from_search_result(old_result, time_decay_factor=0.1)
    recent_memory = RetrievedMemory.from_search_result(recent_result, time_decay_factor=0.1)

    # Recent should have higher time score
    assert recent_memory.time_score > old_memory.time_score

    # Recent should have higher final score
    assert recent_memory.final_score > old_memory.final_score


@pytest.mark.asyncio
async def test_retrieve_recent(retriever, vector_store):
    """Test retrieving recent memories chronologically."""
    current_time = time.time()

    # Store memories at different times
    await vector_store.store_memory(
        content="Meeting 1",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"timestamp": current_time - (5 * 86400)}
    )

    await vector_store.store_memory(
        content="Meeting 2",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"timestamp": current_time - (2 * 86400)}
    )

    await vector_store.store_memory(
        content="Meeting 3",
        memory_type=MemoryType.MEETING_SUMMARY,
        metadata={"timestamp": current_time - 86400}
    )

    # Retrieve recent meetings
    memories = await retriever.retrieve_recent(
        memory_type=MemoryType.MEETING_SUMMARY,
        days=7,
        max_results=10
    )

    # Should be sorted by timestamp (most recent first)
    assert len(memories) == 3
    assert memories[0].content == "Meeting 3"  # Most recent
    assert memories[1].content == "Meeting 2"
    assert memories[2].content == "Meeting 1"


@pytest.mark.asyncio
async def test_summarize_context(retriever, vector_store):
    """Test context summarization."""
    # Store diverse memories
    await vector_store.store_memory(
        content="Q1 planning meeting with team leads",
        memory_type=MemoryType.MEETING_SUMMARY,
    )

    await vector_store.store_memory(
        content="Decided to use microservices architecture",
        memory_type=MemoryType.DECISION,
    )

    await vector_store.store_memory(
        content="Complete API documentation by Friday",
        memory_type=MemoryType.ACTION_ITEM,
    )

    # Retrieve and summarize
    memories = await retriever.retrieve_context("project planning")
    summary = await retriever.summarize_context(memories)

    assert len(summary) > 0
    assert isinstance(summary, str)


@pytest.mark.asyncio
async def test_summarize_empty_context(retriever):
    """Test summarizing empty context."""
    summary = await retriever.summarize_context([])
    assert summary == "No relevant context found."


@pytest.mark.asyncio
async def test_find_related_decisions(retriever, vector_store):
    """Test finding related decisions."""
    await vector_store.store_memory(
        content="Decision to use PostgreSQL database",
        memory_type=MemoryType.DECISION,
        metadata={"project": "backend"}
    )

    await vector_store.store_memory(
        content="Decision to implement caching layer",
        memory_type=MemoryType.DECISION,
        metadata={"project": "backend"}
    )

    decisions = await retriever.find_related_decisions(
        topic="database",
        project="backend",
        days=90
    )

    assert len(decisions) > 0
    for decision in decisions:
        assert decision.memory_type == MemoryType.DECISION.value


@pytest.mark.asyncio
async def test_find_action_items(retriever, vector_store):
    """Test finding action items."""
    await vector_store.store_memory(
        content="Review pull request #123",
        memory_type=MemoryType.ACTION_ITEM,
        metadata={"user": "john@example.com"}
    )

    await vector_store.store_memory(
        content="Update deployment documentation",
        memory_type=MemoryType.ACTION_ITEM,
        metadata={"user": "john@example.com"}
    )

    action_items = await retriever.find_action_items(
        user="john@example.com",
        days=30
    )

    assert len(action_items) > 0
    for item in action_items:
        assert item.memory_type == MemoryType.ACTION_ITEM.value


@pytest.mark.asyncio
async def test_find_user_preferences(retriever, vector_store):
    """Test finding user preferences."""
    await vector_store.store_memory(
        content="Prefers email notifications over Slack",
        memory_type=MemoryType.PREFERENCE,
        metadata={"user": "alice@example.com", "category": "notifications"}
    )

    await vector_store.store_memory(
        content="Uses dark mode for all applications",
        memory_type=MemoryType.PREFERENCE,
        metadata={"user": "alice@example.com", "category": "ui"}
    )

    preferences = await retriever.find_user_preferences(
        user="alice@example.com",
        category="notifications"
    )

    assert len(preferences) > 0
    for pref in preferences:
        assert pref.memory_type == MemoryType.PREFERENCE.value


def test_format_age(retriever):
    """Test age formatting."""
    assert retriever._format_age(0.5) == "12h ago"  # 12 hours
    assert retriever._format_age(3.0) == "3d ago"  # 3 days
    assert retriever._format_age(14.0) == "2w ago"  # 2 weeks
    assert retriever._format_age(60.0) == "2mo ago"  # 2 months


def test_retrieved_memory_from_search_result():
    """Test RetrievedMemory creation from search result."""
    result = {
        "id": "test-id",
        "content": "Test content",
        "metadata": {
            "timestamp": time.time() - 86400,  # 1 day ago
            "memory_type": "note",
        },
        "relevance_score": 0.8,
    }

    memory = RetrievedMemory.from_search_result(result, time_decay_factor=0.1)

    assert memory.id == "test-id"
    assert memory.content == "Test content"
    assert memory.semantic_score == 0.8
    assert 0 < memory.time_score < 1
    assert 0 < memory.final_score < 1
    assert memory.age_days > 0


@pytest.mark.asyncio
async def test_get_statistics(retriever, vector_store):
    """Test statistics retrieval."""
    # Perform some retrievals
    await vector_store.store_memory("Test", MemoryType.NOTE)
    await retriever.retrieve_context("test")

    stats = retriever.get_statistics()

    assert stats["total_retrievals"] == 1
    assert "vector_store_stats" in stats
    assert stats["time_decay_factor"] == 0.1
