"""
PHASE 7A.3: Tests for speaker diarization.

Tests the diarization engine abstraction, Pyannote implementation,
and speaker manager functionality.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from agent.meetings.diarization.base import Speaker, SpeakerSegment
from agent.meetings.diarization.speaker_manager import SpeakerManager


# ══════════════════════════════════════════════════════════════════════
# Test Data Models
# ══════════════════════════════════════════════════════════════════════


def test_speaker_segment_creation():
    """Test SpeakerSegment dataclass creation"""
    segment = SpeakerSegment(
        speaker_id="SPEAKER_00",
        start_time=0.0,
        end_time=5.2,
        confidence=0.95
    )

    assert segment.speaker_id == "SPEAKER_00"
    assert segment.start_time == 0.0
    assert segment.end_time == 5.2
    assert segment.confidence == 0.95
    assert segment.duration == 5.2


def test_speaker_segment_overlap():
    """Test SpeakerSegment overlap detection"""
    seg1 = SpeakerSegment("SPEAKER_00", 0.0, 5.0, 1.0)
    seg2 = SpeakerSegment("SPEAKER_01", 4.0, 8.0, 1.0)
    seg3 = SpeakerSegment("SPEAKER_02", 10.0, 15.0, 1.0)

    assert seg1.overlaps_with(seg2)  # Overlapping
    assert seg2.overlaps_with(seg1)  # Symmetric
    assert not seg1.overlaps_with(seg3)  # No overlap


def test_speaker_segment_to_dict():
    """Test SpeakerSegment serialization"""
    segment = SpeakerSegment(
        speaker_id="SPEAKER_01",
        start_time=2.5,
        end_time=7.8,
        confidence=0.88
    )

    data = segment.to_dict()

    assert data["speaker_id"] == "SPEAKER_01"
    assert data["start_time"] == 2.5
    assert data["end_time"] == 7.8
    assert data["duration"] == 5.3
    assert data["confidence"] == 0.88


def test_speaker_creation():
    """Test Speaker dataclass creation"""
    speaker = Speaker(
        speaker_id="SPEAKER_001",
        name="Alice Smith",
        email="alice@example.com",
        voice_embedding=[0.1, 0.2, 0.3],
        participant_id="zoom_123"
    )

    assert speaker.speaker_id == "SPEAKER_001"
    assert speaker.name == "Alice Smith"
    assert speaker.email == "alice@example.com"
    assert speaker.has_voice_profile()


def test_speaker_without_embedding():
    """Test Speaker without voice embedding"""
    speaker = Speaker(
        speaker_id="SPEAKER_002",
        name="Bob"
    )

    assert not speaker.has_voice_profile()


def test_speaker_to_dict():
    """Test Speaker serialization"""
    speaker = Speaker(
        speaker_id="SPEAKER_003",
        name="Charlie",
        email="charlie@example.com",
        voice_embedding=[0.5] * 512
    )

    data = speaker.to_dict()

    assert data["speaker_id"] == "SPEAKER_003"
    assert data["name"] == "Charlie"
    assert data["has_voice_profile"] is True


# ══════════════════════════════════════════════════════════════════════
# Test SpeakerManager
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_speaker_manager_initialization():
    """Test SpeakerManager initializes correctly"""
    # Create with mock engine to avoid pyannote dependency
    mock_engine = Mock()
    manager = SpeakerManager(diarization_engine=mock_engine)

    assert manager.engine == mock_engine
    assert len(manager.known_speakers) == 0
    assert len(manager.current_participants) == 0
    assert len(manager.speaker_mapping) == 0


@pytest.mark.asyncio
async def test_speaker_registration():
    """Test registering new speaker"""
    mock_engine = Mock()
    mock_engine.create_voice_embedding = AsyncMock(
        return_value=[0.1, 0.2, 0.3]
    )

    manager = SpeakerManager(diarization_engine=mock_engine)

    speaker = await manager.register_speaker(
        name="John Doe",
        email="john@example.com",
        voice_sample=b"fake_audio"
    )

    assert speaker.name == "John Doe"
    assert speaker.email == "john@example.com"
    assert speaker.voice_embedding == [0.1, 0.2, 0.3]
    assert speaker.speaker_id == "SPEAKER_000"
    assert speaker.speaker_id in manager.known_speakers


@pytest.mark.asyncio
async def test_multiple_speaker_registration():
    """Test registering multiple speakers"""
    mock_engine = Mock()
    mock_engine.create_voice_embedding = AsyncMock(
        return_value=[0.5] * 512
    )

    manager = SpeakerManager(diarization_engine=mock_engine)

    speaker1 = await manager.register_speaker("Alice", "alice@example.com", b"audio1")
    speaker2 = await manager.register_speaker("Bob", "bob@example.com", b"audio2")

    assert len(manager.known_speakers) == 2
    assert speaker1.speaker_id == "SPEAKER_000"
    assert speaker2.speaker_id == "SPEAKER_001"


@pytest.mark.asyncio
async def test_speaker_identification():
    """Test identifying speaker from voice"""
    mock_engine = Mock()

    manager = SpeakerManager(diarization_engine=mock_engine)

    # Register known speaker
    manager.known_speakers["SPEAKER_001"] = Speaker(
        speaker_id="SPEAKER_001",
        name="Alice",
        email="alice@example.com",
        voice_embedding=[0.5, 0.5, 0.5]
    )

    # Mock engine to return matching speaker
    mock_engine.identify_speaker = AsyncMock(
        return_value="SPEAKER_001"
    )

    name = await manager.identify_speaker_in_segment(
        audio_segment=b"audio",
        diarization_id="SPEAKER_00"
    )

    assert name == "Alice"
    assert manager.speaker_mapping["SPEAKER_00"] == "SPEAKER_001"


@pytest.mark.asyncio
async def test_speaker_identification_caching():
    """Test speaker identification uses cached mapping"""
    mock_engine = Mock()
    mock_engine.identify_speaker = AsyncMock()

    manager = SpeakerManager(diarization_engine=mock_engine)

    # Setup pre-existing mapping
    manager.speaker_mapping["SPEAKER_00"] = "SPEAKER_001"
    manager.known_speakers["SPEAKER_001"] = Speaker(
        speaker_id="SPEAKER_001",
        name="Alice"
    )

    # Should use cached mapping, not call engine
    name = await manager.identify_speaker_in_segment(
        audio_segment=b"audio",
        diarization_id="SPEAKER_00"
    )

    assert name == "Alice"
    mock_engine.identify_speaker.assert_not_called()


def test_set_meeting_participants():
    """Test setting participants from meeting platform"""
    manager = SpeakerManager(diarization_engine=Mock())

    participants = [
        {"name": "Alice", "email": "alice@example.com", "participant_id": "123"},
        {"name": "Bob", "email": "bob@example.com", "participant_id": "456"}
    ]

    manager.set_meeting_participants(participants)

    assert len(manager.current_participants) == 2
    assert manager.current_participants[0]["name"] == "Alice"
    assert manager.current_participants[1]["name"] == "Bob"


@pytest.mark.asyncio
async def test_diarize_meeting_audio():
    """Test diarizing meeting audio"""
    mock_engine = Mock()
    mock_segments = [
        SpeakerSegment("SPEAKER_00", 0.0, 5.0, 0.95),
        SpeakerSegment("SPEAKER_01", 5.0, 10.0, 0.92)
    ]
    mock_engine.diarize_audio = AsyncMock(return_value=mock_segments)

    manager = SpeakerManager(diarization_engine=mock_engine)

    # Set participants (should use count as hint)
    manager.set_meeting_participants([
        {"name": "Alice"}, {"name": "Bob"}
    ])

    segments = await manager.diarize_meeting_audio(b"audio_bytes")

    assert len(segments) == 2
    assert segments[0].speaker_id == "SPEAKER_00"

    # Verify it passed participant count to engine
    mock_engine.diarize_audio.assert_called_once()
    call_args = mock_engine.diarize_audio.call_args
    assert call_args[1]["num_speakers"] == 2


def test_get_speaker_by_name():
    """Test getting speaker by name"""
    manager = SpeakerManager(diarization_engine=Mock())

    manager.known_speakers["SPEAKER_001"] = Speaker(
        speaker_id="SPEAKER_001",
        name="Alice Smith"
    )

    speaker = manager.get_speaker_by_name("Alice Smith")
    assert speaker is not None
    assert speaker.speaker_id == "SPEAKER_001"

    # Case-insensitive
    speaker = manager.get_speaker_by_name("alice smith")
    assert speaker is not None

    # Not found
    speaker = manager.get_speaker_by_name("Bob")
    assert speaker is None


def test_get_speaker_by_email():
    """Test getting speaker by email"""
    manager = SpeakerManager(diarization_engine=Mock())

    manager.known_speakers["SPEAKER_002"] = Speaker(
        speaker_id="SPEAKER_002",
        name="Bob",
        email="bob@example.com"
    )

    speaker = manager.get_speaker_by_email("bob@example.com")
    assert speaker is not None
    assert speaker.name == "Bob"

    # Case-insensitive
    speaker = manager.get_speaker_by_email("BOB@EXAMPLE.COM")
    assert speaker is not None


def test_transcript_speaker_combination():
    """Test combining transcript with speaker info"""
    manager = SpeakerManager(diarization_engine=Mock())

    # Setup speaker mapping
    manager.speaker_mapping["SPEAKER_00"] = "SPEAKER_001"
    manager.speaker_mapping["SPEAKER_01"] = "SPEAKER_002"

    manager.known_speakers["SPEAKER_001"] = Speaker(
        speaker_id="SPEAKER_001",
        name="Alice"
    )
    manager.known_speakers["SPEAKER_002"] = Speaker(
        speaker_id="SPEAKER_002",
        name="Bob"
    )

    transcript = [
        {"text": "Hello world", "start_time": 0.0, "end_time": 2.0, "confidence": 0.95},
        {"text": "Hi Alice", "start_time": 2.1, "end_time": 3.5, "confidence": 0.92}
    ]

    diarization = [
        SpeakerSegment("SPEAKER_00", 0.0, 2.0, 0.95),
        SpeakerSegment("SPEAKER_01", 2.1, 3.5, 0.92)
    ]

    result = manager.get_transcript_with_speakers(transcript, diarization)

    assert len(result) == 2
    assert result[0]["speaker"] == "Alice"
    assert result[0]["text"] == "Hello world"
    assert result[1]["speaker"] == "Bob"
    assert result[1]["text"] == "Hi Alice"


def test_transcript_unknown_speaker():
    """Test combining transcript with unknown speaker"""
    manager = SpeakerManager(diarization_engine=Mock())

    # No speaker mapping - should use anonymous ID
    transcript = [
        {"text": "Mystery speaker", "start_time": 0.0, "end_time": 2.0}
    ]

    diarization = [
        SpeakerSegment("SPEAKER_00", 0.0, 2.0, 0.95)
    ]

    result = manager.get_transcript_with_speakers(transcript, diarization)

    assert len(result) == 1
    assert result[0]["speaker"] == "SPEAKER_00"  # Anonymous ID
    assert result[0]["text"] == "Mystery speaker"


def test_get_speaker_statistics():
    """Test getting speaker statistics"""
    manager = SpeakerManager(diarization_engine=Mock())

    manager.known_speakers["SPEAKER_001"] = Speaker(
        speaker_id="SPEAKER_001",
        name="Alice"
    )
    manager.known_speakers["SPEAKER_002"] = Speaker(
        speaker_id="SPEAKER_002",
        name="Bob"
    )

    manager.set_meeting_participants([
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"}
    ])

    manager.speaker_mapping["SPEAKER_00"] = "SPEAKER_001"

    stats = manager.get_speaker_statistics()

    assert stats["num_known_speakers"] == 2
    assert stats["num_participants"] == 3
    assert stats["num_mapped_speakers"] == 1
    assert "Alice" in stats["known_speaker_names"]
    assert "Charlie" in stats["participant_names"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
