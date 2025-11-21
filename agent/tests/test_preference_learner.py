"""
PHASE 10.3: Preference Learner Tests

Tests for personal preference learning and tracking.
"""

import asyncio
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.vector_store import VectorMemoryStore, MemoryType
from memory.preference_learner import PreferenceLearner, PreferenceCategory, Preference


@pytest.fixture
def temp_chroma_dir():
    """Create temporary ChromaDB directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def vector_store(temp_chroma_dir):
    """Create vector store instance."""
    return VectorMemoryStore(
        collection_name="test_preferences",
        persist_directory=temp_chroma_dir,
    )


@pytest.fixture
def learner(vector_store):
    """Create preference learner instance."""
    return PreferenceLearner(vector_store, user_id="test_user")


@pytest.mark.asyncio
async def test_learner_initialization(learner):
    """Test preference learner initialization."""
    assert learner.user_id == "test_user"
    assert len(learner.preferences) == 0
    assert learner.total_learned == 0


@pytest.mark.asyncio
async def test_learn_communication_preference(learner):
    """Test learning communication preferences from text."""
    text = "I prefer email over Slack for important notifications"

    prefs = await learner.learn_from_text(text)

    assert len(prefs) > 0
    assert learner.total_observations == 1


@pytest.mark.asyncio
async def test_learn_tool_preference(learner):
    """Test learning tool preferences."""
    text = "I prefer VSCode for all my development work"

    prefs = await learner.learn_from_text(text)

    # Check if preference was learned
    tool_prefs = learner.get_all_preferences(category=PreferenceCategory.TOOLS)
    assert len(tool_prefs) > 0


@pytest.mark.asyncio
async def test_learn_working_hours(learner):
    """Test learning working hours preferences."""
    text = "I work from 9 to 5"

    prefs = await learner.learn_from_text(text)

    # Check working hours
    working_hours = learner.get_working_hours()
    assert working_hours is not None


@pytest.mark.asyncio
async def test_record_explicit_preference(learner):
    """Test recording explicit preferences."""
    await learner.record_explicit_preference(
        category=PreferenceCategory.NOTIFICATION,
        key="channel",
        value="email",
    )

    pref = learner.get_preference(PreferenceCategory.NOTIFICATION, "channel")

    assert pref is not None
    assert pref.value == "email"
    assert pref.confidence == 1.0
    assert pref.source == "explicit"


@pytest.mark.asyncio
async def test_infer_preference(learner):
    """Test inferring preferences with lower confidence."""
    await learner.infer_preference(
        category=PreferenceCategory.TASK_STYLE,
        key="approach",
        value="incremental",
        confidence=0.6,
    )

    pref = learner.get_preference(PreferenceCategory.TASK_STYLE, "approach")

    assert pref is not None
    assert pref.value == "incremental"
    assert pref.confidence == 0.6
    assert pref.source == "inferred"


@pytest.mark.asyncio
async def test_preference_confidence_update(learner):
    """Test confidence increase with repeated observations."""
    # First observation
    await learner.infer_preference(
        category=PreferenceCategory.TOOLS,
        key="editor",
        value="vim",
        confidence=0.5,
    )

    initial_pref = learner.get_preference(PreferenceCategory.TOOLS, "editor")
    initial_confidence = initial_pref.confidence

    # Second observation (same preference)
    await learner.infer_preference(
        category=PreferenceCategory.TOOLS,
        key="editor",
        value="vim",
        confidence=0.5,
    )

    updated_pref = learner.get_preference(PreferenceCategory.TOOLS, "editor")

    # Confidence should increase
    assert updated_pref.confidence > initial_confidence
    assert updated_pref.observation_count == 2


@pytest.mark.asyncio
async def test_preference_conflict_resolution(learner):
    """Test handling of conflicting preferences."""
    # First preference
    await learner.record_explicit_preference(
        category=PreferenceCategory.TOOLS,
        key="database",
        value="PostgreSQL",
    )

    # Conflicting preference
    await learner.record_explicit_preference(
        category=PreferenceCategory.TOOLS,
        key="database",
        value="MySQL",
    )

    pref = learner.get_preference(PreferenceCategory.TOOLS, "database")

    # Should keep most recent preference
    assert pref.value == "MySQL"


@pytest.mark.asyncio
async def test_get_all_preferences(learner):
    """Test getting all preferences with filtering."""
    # Add preferences in different categories
    await learner.record_explicit_preference(
        PreferenceCategory.TOOLS, "editor", "VSCode"
    )
    await learner.record_explicit_preference(
        PreferenceCategory.NOTIFICATION, "channel", "email"
    )
    await learner.infer_preference(
        PreferenceCategory.COMMUNICATION, "style", "concise", confidence=0.4
    )

    # Get all preferences
    all_prefs = learner.get_all_preferences()
    assert len(all_prefs) >= 2  # At least 2 with default min_confidence=0.5

    # Get only tool preferences
    tool_prefs = learner.get_all_preferences(category=PreferenceCategory.TOOLS)
    assert len(tool_prefs) == 1
    assert tool_prefs[0].key == "editor"

    # Get high confidence preferences
    high_conf = learner.get_all_preferences(min_confidence=0.9)
    assert all(p.confidence >= 0.9 for p in high_conf)


@pytest.mark.asyncio
async def test_get_working_hours(learner):
    """Test getting working hours preference."""
    # Initially None
    assert learner.get_working_hours() is None

    # Set working hours
    await learner.record_explicit_preference(
        PreferenceCategory.WORKING_HOURS,
        "work_hours",
        "9:00-17:00",
    )

    working_hours = learner.get_working_hours()

    assert working_hours is not None
    assert working_hours["start"] == "9:00"
    assert working_hours["end"] == "17:00"


@pytest.mark.asyncio
async def test_is_working_hours(learner):
    """Test checking if time is within working hours."""
    # Set working hours (9 AM - 5 PM)
    await learner.record_explicit_preference(
        PreferenceCategory.WORKING_HOURS,
        "work_hours",
        "9:00-17:00",
    )

    # Test during working hours (noon)
    noon = datetime.now().replace(hour=12, minute=0)
    assert learner.is_working_hours(noon) is True

    # Test outside working hours (8 PM)
    evening = datetime.now().replace(hour=20, minute=0)
    assert learner.is_working_hours(evening) is False

    # Test early morning (6 AM)
    morning = datetime.now().replace(hour=6, minute=0)
    assert learner.is_working_hours(morning) is False


@pytest.mark.asyncio
async def test_is_working_hours_no_preference(learner):
    """Test working hours check with no preference set."""
    # Should default to always available
    assert learner.is_working_hours() is True


@pytest.mark.asyncio
async def test_get_summary(learner):
    """Test getting preference summary."""
    # Add various preferences
    await learner.record_explicit_preference(
        PreferenceCategory.TOOLS, "editor", "VSCode"
    )
    await learner.record_explicit_preference(
        PreferenceCategory.NOTIFICATION, "channel", "email"
    )
    await learner.infer_preference(
        PreferenceCategory.COMMUNICATION, "style", "formal", confidence=0.6
    )

    summary = learner.get_summary()

    assert summary["user_id"] == "test_user"
    assert summary["total_preferences"] >= 3
    assert summary["total_learned"] >= 3
    assert "by_category" in summary
    assert "high_confidence" in summary
    assert "medium_confidence" in summary
    assert "low_confidence" in summary


@pytest.mark.asyncio
async def test_multiple_text_patterns(learner):
    """Test learning from text with multiple patterns."""
    texts = [
        "I prefer email over Slack",
        "I always use vim for editing",
        "I work from 9 to 5",
        "My favorite editor is VSCode",
    ]

    for text in texts:
        await learner.learn_from_text(text)

    # Should have learned multiple preferences
    assert len(learner.preferences) > 0
    assert learner.total_observations == len(texts)


def test_preference_dataclass():
    """Test Preference dataclass."""
    pref = Preference(
        category=PreferenceCategory.TOOLS,
        key="editor",
        value="vim",
        confidence=0.8,
        source="explicit",
        first_seen=time.time(),
        last_updated=time.time(),
    )

    # Test to_dict
    data = pref.to_dict()
    assert data["category"] == "tools"
    assert data["key"] == "editor"
    assert data["value"] == "vim"

    # Test from_dict
    pref2 = Preference.from_dict(data)
    assert pref2.category == pref.category
    assert pref2.key == pref.key
    assert pref2.value == pref.value


def test_preference_category_enum():
    """Test PreferenceCategory enum."""
    assert PreferenceCategory.COMMUNICATION.value == "communication"
    assert PreferenceCategory.TOOLS.value == "tools"
    assert PreferenceCategory.WORKING_HOURS.value == "working_hours"
    assert PreferenceCategory.TASK_STYLE.value == "task_style"


@pytest.mark.asyncio
async def test_preference_persistence(learner, vector_store):
    """Test that preferences are persisted to vector store."""
    await learner.record_explicit_preference(
        PreferenceCategory.TOOLS,
        key="language",
        value="Python",
    )

    # Check vector store
    count = vector_store.count_memories(MemoryType.PREFERENCE)
    assert count > 0


@pytest.mark.asyncio
async def test_confidence_sorting(learner):
    """Test that preferences are sorted by confidence."""
    # Add preferences with different confidence levels
    await learner.record_explicit_preference(
        PreferenceCategory.TOOLS, "tool1", "value1"  # confidence=1.0
    )
    await learner.infer_preference(
        PreferenceCategory.TOOLS, "tool2", "value2", confidence=0.5
    )
    await learner.infer_preference(
        PreferenceCategory.TOOLS, "tool3", "value3", confidence=0.8
    )

    prefs = learner.get_all_preferences(category=PreferenceCategory.TOOLS)

    # Should be sorted by confidence (descending)
    assert prefs[0].confidence >= prefs[1].confidence
    assert prefs[1].confidence >= prefs[2].confidence
