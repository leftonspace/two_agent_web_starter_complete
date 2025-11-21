"""
PHASE 7A.1: Tests for meeting bot integration.

Tests the meeting bot abstraction, factory, and concrete implementations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

import pytest

from agent.meetings import (
    AudioChunk,
    MeetingBot,
    MeetingInfo,
    MeetingPlatform,
    create_meeting_bot,
)
from agent.meetings.google_meet_bot import GoogleMeetBot
from agent.meetings.live_audio_bot import LiveAudioBot
from agent.meetings.teams_bot import TeamsBot
from agent.meetings.zoom_bot import ZoomBot


# ══════════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def zoom_meeting_info() -> MeetingInfo:
    """Create a sample Zoom meeting"""
    return MeetingInfo(
        platform=MeetingPlatform.ZOOM,
        meeting_id="123456789",
        title="Weekly Standup",
        participants=["Alice", "Bob", "Charlie"],
        start_time=datetime.now(),
        scheduled_duration_minutes=30,
        meeting_url="https://zoom.us/j/123456789",
        password="test123"
    )


@pytest.fixture
def teams_meeting_info() -> MeetingInfo:
    """Create a sample Teams meeting"""
    return MeetingInfo(
        platform=MeetingPlatform.TEAMS,
        meeting_id="19:meeting_abc123",
        title="Sprint Planning",
        participants=["Dave", "Eve"],
        start_time=datetime.now() + timedelta(hours=1),
        scheduled_duration_minutes=60,
        meeting_url="https://teams.microsoft.com/l/meetup-join/...",
    )


@pytest.fixture
def live_audio_meeting_info() -> MeetingInfo:
    """Create a sample live audio meeting"""
    return MeetingInfo(
        platform=MeetingPlatform.LIVE_AUDIO,
        meeting_id="live_001",
        title="In-Person Meeting",
        participants=["Frank"],
        start_time=datetime.now(),
        scheduled_duration_minutes=45,
    )


@pytest.fixture
def google_meet_meeting_info() -> MeetingInfo:
    """Create a sample Google Meet meeting"""
    return MeetingInfo(
        platform=MeetingPlatform.GOOGLE_MEET,
        meeting_id="abc-defg-hij",
        title="Q4 Review",
        participants=["Grace", "Henry"],
        start_time=datetime.now(),
        scheduled_duration_minutes=90,
        meeting_url="https://meet.google.com/abc-defg-hij",
    )


# ══════════════════════════════════════════════════════════════════════
# Test Data Models
# ══════════════════════════════════════════════════════════════════════


def test_meeting_info_creation(zoom_meeting_info: MeetingInfo):
    """Test MeetingInfo dataclass creation"""
    assert zoom_meeting_info.platform == MeetingPlatform.ZOOM
    assert zoom_meeting_info.meeting_id == "123456789"
    assert zoom_meeting_info.title == "Weekly Standup"
    assert len(zoom_meeting_info.participants) == 3
    assert zoom_meeting_info.scheduled_duration_minutes == 30


def test_meeting_info_to_dict(zoom_meeting_info: MeetingInfo):
    """Test MeetingInfo serialization"""
    data = zoom_meeting_info.to_dict()

    assert data["platform"] == "zoom"
    assert data["meeting_id"] == "123456789"
    assert data["title"] == "Weekly Standup"
    assert isinstance(data["start_time"], str)  # ISO format
    assert isinstance(data["participants"], list)


def test_audio_chunk_creation():
    """Test AudioChunk dataclass"""
    audio_bytes = b'\x00' * 32000  # 1 second at 16kHz mono
    chunk = AudioChunk(
        audio_bytes=audio_bytes,
        timestamp=datetime.now(),
        duration_ms=1000,
        sample_rate=16000,
        channels=1
    )

    assert len(chunk) == 32000
    assert chunk.duration_seconds == 1.0
    assert chunk.sample_rate == 16000
    assert chunk.channels == 1


# ══════════════════════════════════════════════════════════════════════
# Test Factory
# ══════════════════════════════════════════════════════════════════════


def test_factory_creates_zoom_bot(zoom_meeting_info: MeetingInfo):
    """Test factory creates ZoomBot for Zoom meetings"""
    bot = create_meeting_bot(zoom_meeting_info)

    assert bot is not None
    assert isinstance(bot, ZoomBot)
    assert bot.meeting_info.platform == MeetingPlatform.ZOOM


def test_factory_creates_teams_bot(teams_meeting_info: MeetingInfo):
    """Test factory creates TeamsBot for Teams meetings"""
    bot = create_meeting_bot(teams_meeting_info)

    assert bot is not None
    assert isinstance(bot, TeamsBot)
    assert bot.meeting_info.platform == MeetingPlatform.TEAMS


def test_factory_creates_live_audio_bot(live_audio_meeting_info: MeetingInfo):
    """Test factory creates LiveAudioBot for live audio"""
    bot = create_meeting_bot(live_audio_meeting_info)

    assert bot is not None
    assert isinstance(bot, LiveAudioBot)
    assert bot.meeting_info.platform == MeetingPlatform.LIVE_AUDIO


def test_factory_creates_google_meet_bot(google_meet_meeting_info: MeetingInfo):
    """Test factory creates GoogleMeetBot (stub)"""
    bot = create_meeting_bot(google_meet_meeting_info)

    assert bot is not None
    assert isinstance(bot, GoogleMeetBot)
    assert bot.meeting_info.platform == MeetingPlatform.GOOGLE_MEET


# ══════════════════════════════════════════════════════════════════════
# Test ZoomBot
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_zoom_bot_initialization(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot initialization"""
    bot = ZoomBot(zoom_meeting_info)

    assert bot.meeting_info == zoom_meeting_info
    assert not bot.is_connected
    assert not bot.is_recording
    assert not bot.audio_stream_active


@pytest.mark.asyncio
async def test_zoom_bot_connect(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot connection (simulation mode)"""
    bot = ZoomBot(zoom_meeting_info)

    result = await bot.connect()

    assert result is True
    assert bot.is_connected


@pytest.mark.asyncio
async def test_zoom_bot_join_meeting(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot joining meeting"""
    bot = ZoomBot(zoom_meeting_info)

    # Join should auto-connect if needed
    result = await bot.join_meeting()

    assert result is True
    assert bot.is_connected
    assert bot.joined_meeting


@pytest.mark.asyncio
async def test_zoom_bot_audio_stream(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot audio streaming"""
    bot = ZoomBot(zoom_meeting_info)
    await bot.join_meeting()
    await bot.start_audio_capture()

    chunks: List[AudioChunk] = []

    # Collect 3 audio chunks
    async def collect_chunks():
        async for chunk in bot.get_audio_stream():
            chunks.append(chunk)
            if len(chunks) >= 3:
                bot.audio_stream_active = False
                break

    # Run with timeout
    try:
        await asyncio.wait_for(collect_chunks(), timeout=5.0)
    except asyncio.TimeoutError:
        pass

    assert len(chunks) >= 1  # At least one chunk
    assert all(isinstance(c, AudioChunk) for c in chunks)
    assert all(c.sample_rate == 16000 for c in chunks)


@pytest.mark.asyncio
async def test_zoom_bot_get_participants(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot participant retrieval"""
    bot = ZoomBot(zoom_meeting_info)
    await bot.join_meeting()

    participants = await bot.get_participants()

    assert isinstance(participants, list)
    assert len(participants) == 3  # Alice, Bob, Charlie
    assert all("name" in p for p in participants)
    assert all("id" in p for p in participants)


@pytest.mark.asyncio
async def test_zoom_bot_send_chat(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot sending chat messages"""
    bot = ZoomBot(zoom_meeting_info)
    await bot.join_meeting()

    result = await bot.send_chat_message("Hello from JARVIS!")

    assert result is True


@pytest.mark.asyncio
async def test_zoom_bot_leave_meeting(zoom_meeting_info: MeetingInfo):
    """Test ZoomBot leaving meeting"""
    bot = ZoomBot(zoom_meeting_info)
    await bot.join_meeting()

    result = await bot.leave_meeting()

    assert result is True
    assert not bot.is_connected
    assert not bot.joined_meeting


# ══════════════════════════════════════════════════════════════════════
# Test TeamsBot
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_teams_bot_connect(teams_meeting_info: MeetingInfo):
    """Test TeamsBot connection"""
    bot = TeamsBot(teams_meeting_info)

    result = await bot.connect()

    assert result is True
    assert bot.is_connected


@pytest.mark.asyncio
async def test_teams_bot_join_meeting(teams_meeting_info: MeetingInfo):
    """Test TeamsBot joining meeting"""
    bot = TeamsBot(teams_meeting_info)

    result = await bot.join_meeting()

    assert result is True
    assert bot.joined_meeting


@pytest.mark.asyncio
async def test_teams_bot_get_participants(teams_meeting_info: MeetingInfo):
    """Test TeamsBot participant retrieval"""
    bot = TeamsBot(teams_meeting_info)
    await bot.join_meeting()

    participants = await bot.get_participants()

    assert isinstance(participants, list)
    assert len(participants) == 2  # Dave, Eve


# ══════════════════════════════════════════════════════════════════════
# Test LiveAudioBot
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_live_audio_bot_connect(live_audio_meeting_info: MeetingInfo):
    """Test LiveAudioBot connection (checks for microphone)"""
    bot = LiveAudioBot(live_audio_meeting_info)

    # May fail if pyaudio not installed or no microphone
    result = await bot.connect()

    # Result depends on environment, just check it's a boolean
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_live_audio_bot_no_participants(live_audio_meeting_info: MeetingInfo):
    """Test LiveAudioBot cannot detect participants"""
    bot = LiveAudioBot(live_audio_meeting_info)

    participants = await bot.get_participants()

    assert participants == []


@pytest.mark.asyncio
async def test_live_audio_bot_no_chat(live_audio_meeting_info: MeetingInfo):
    """Test LiveAudioBot cannot send chat"""
    bot = LiveAudioBot(live_audio_meeting_info)

    result = await bot.send_chat_message("Test")

    assert result is False


# ══════════════════════════════════════════════════════════════════════
# Test GoogleMeetBot (Stub)
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_google_meet_bot_not_implemented(google_meet_meeting_info: MeetingInfo):
    """Test GoogleMeetBot returns not implemented"""
    bot = GoogleMeetBot(google_meet_meeting_info)

    # All methods should return False/empty/None
    assert await bot.connect() is False
    assert await bot.join_meeting() is False
    assert await bot.start_audio_capture() is False
    assert await bot.get_participants() == []
    assert await bot.send_chat_message("Test") is False
    assert await bot.get_recording_url() is None


# ══════════════════════════════════════════════════════════════════════
# Test Base MeetingBot Utilities
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_ensure_connected(zoom_meeting_info: MeetingInfo):
    """Test ensure_connected utility method"""
    bot = ZoomBot(zoom_meeting_info)

    assert not bot.is_connected

    result = await bot.ensure_connected()

    assert result is True
    assert bot.is_connected

    # Calling again should still return True without reconnecting
    result = await bot.ensure_connected()
    assert result is True


def test_get_meeting_duration(zoom_meeting_info: MeetingInfo):
    """Test get_meeting_duration_minutes utility"""
    bot = ZoomBot(zoom_meeting_info)

    duration = bot.get_meeting_duration_minutes()

    assert duration == 30


def test_get_platform_name(zoom_meeting_info: MeetingInfo):
    """Test get_platform_name utility"""
    bot = ZoomBot(zoom_meeting_info)

    name = bot.get_platform_name()

    assert name == "Zoom"


# ══════════════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_full_meeting_lifecycle(zoom_meeting_info: MeetingInfo):
    """Test complete meeting lifecycle: connect → join → capture → leave"""
    bot = ZoomBot(zoom_meeting_info)

    # Connect
    assert await bot.connect()
    assert bot.is_connected

    # Join
    assert await bot.join_meeting()
    assert bot.joined_meeting

    # Start audio
    assert await bot.start_audio_capture()
    assert bot.is_recording
    assert bot.audio_stream_active

    # Get participants
    participants = await bot.get_participants()
    assert len(participants) > 0

    # Send message
    assert await bot.send_chat_message("JARVIS has joined")

    # Leave
    assert await bot.leave_meeting()
    assert not bot.is_connected
    assert not bot.joined_meeting


@pytest.mark.asyncio
async def test_meeting_platform_enum():
    """Test MeetingPlatform enum values"""
    assert MeetingPlatform.ZOOM.value == "zoom"
    assert MeetingPlatform.TEAMS.value == "teams"
    assert MeetingPlatform.GOOGLE_MEET.value == "google_meet"
    assert MeetingPlatform.LIVE_AUDIO.value == "live"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
