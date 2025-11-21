"""
Base classes for meeting platform integration.

PHASE 7A.1: Provides abstraction for Zoom, Teams, Google Meet, and live audio.

This module defines the contract that all meeting bots must implement,
allowing the system to work with different platforms uniformly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════


class MeetingPlatform(Enum):
    """Supported meeting platforms"""
    ZOOM = "zoom"
    TEAMS = "teams"
    GOOGLE_MEET = "google_meet"
    LIVE_AUDIO = "live"


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class MeetingInfo:
    """
    Meeting metadata.

    Contains all information needed to join and manage a meeting.
    """
    platform: MeetingPlatform
    meeting_id: str
    title: str
    participants: List[str]
    start_time: datetime
    scheduled_duration_minutes: int
    meeting_url: Optional[str] = None
    password: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "platform": self.platform.value,
            "meeting_id": self.meeting_id,
            "title": self.title,
            "participants": self.participants,
            "start_time": self.start_time.isoformat(),
            "scheduled_duration_minutes": self.scheduled_duration_minutes,
            "meeting_url": self.meeting_url,
            "metadata": self.metadata
        }


@dataclass
class AudioChunk:
    """
    Audio data chunk from meeting.

    Represents a segment of audio (typically 1 second) captured from the meeting.
    Audio is in PCM format at 16kHz mono.
    """
    audio_bytes: bytes
    timestamp: datetime
    duration_ms: int
    sample_rate: int = 16000
    channels: int = 1

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds"""
        return self.duration_ms / 1000.0

    def __len__(self) -> int:
        """Get size of audio data in bytes"""
        return len(self.audio_bytes)


# ══════════════════════════════════════════════════════════════════════
# Abstract Base Class
# ══════════════════════════════════════════════════════════════════════


class MeetingBot(ABC):
    """
    Abstract base class for meeting bots.

    Each platform (Zoom, Teams, Google Meet) implements this interface.
    This provides a uniform API for:
    - Connecting to platform
    - Joining meetings
    - Capturing audio streams
    - Getting participant lists
    - Sending chat messages
    - Leaving meetings

    Example:
        bot = ZoomBot(meeting_info)
        await bot.connect()
        await bot.join_meeting()
        await bot.start_audio_capture()

        async for audio_chunk in bot.get_audio_stream():
            # Process audio (transcribe, analyze, etc.)
            print(f"Got {len(audio_chunk)} bytes")

        await bot.leave_meeting()
    """

    def __init__(self, meeting_info: MeetingInfo):
        """
        Initialize meeting bot.

        Args:
            meeting_info: Meeting details (platform, ID, URL, etc.)
        """
        self.meeting_info = meeting_info
        self.is_connected = False
        self.is_recording = False
        self.audio_stream_active = False

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to meeting platform.

        Establishes connection to the platform's API/SDK.
        Must be called before join_meeting().

        Returns:
            True if connection successful, False otherwise

        Example:
            if await bot.connect():
                print("Connected to Zoom")
        """
        pass

    @abstractmethod
    async def join_meeting(self) -> bool:
        """
        Join the specific meeting.

        Bot appears as a participant in the meeting.
        Requires successful connect() first.

        Returns:
            True if join successful, False otherwise

        Example:
            if await bot.join_meeting():
                print("Joined meeting")
                print(f"Participants: {await bot.get_participants()}")
        """
        pass

    @abstractmethod
    async def start_audio_capture(self) -> bool:
        """
        Start capturing audio stream from meeting.

        Begins recording audio that can be retrieved via get_audio_stream().
        Some platforms may start recording automatically on join.

        Returns:
            True if capture started successfully, False otherwise

        Example:
            if await bot.start_audio_capture():
                async for chunk in bot.get_audio_stream():
                    # Process audio
                    pass
        """
        pass

    @abstractmethod
    async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
        """
        Stream audio chunks as they arrive.

        Yields AudioChunk objects continuously while recording is active.
        Typical chunk size is 1 second at 16kHz mono (16000 samples).

        Yields:
            AudioChunk objects containing PCM audio data

        Example:
            async for chunk in bot.get_audio_stream():
                print(f"Got {chunk.duration_seconds}s of audio")
                # chunk.audio_bytes contains raw PCM data
                # Can be sent to speech-to-text API
        """
        pass

    @abstractmethod
    async def get_participants(self) -> List[Dict[str, Any]]:
        """
        Get current meeting participants.

        Returns information about all participants currently in the meeting.

        Returns:
            List of participant info dictionaries with keys:
            - id: Unique participant identifier
            - name: Display name
            - email: Email address (if available)
            - is_host: Whether participant is host
            - is_muted: Whether audio is muted
            - etc. (platform-specific fields)

        Example:
            participants = await bot.get_participants()
            for p in participants:
                print(f"{p['name']} - muted: {p['is_muted']}")
        """
        pass

    @abstractmethod
    async def send_chat_message(self, message: str) -> bool:
        """
        Send message to meeting chat.

        Posts a message in the meeting chat that all participants can see.

        Args:
            message: Text message to send

        Returns:
            True if message sent successfully, False otherwise

        Example:
            await bot.send_chat_message("JARVIS has joined the meeting")
            await bot.send_chat_message("Action item: Update Q4 roadmap")
        """
        pass

    @abstractmethod
    async def leave_meeting(self) -> bool:
        """
        Leave meeting and disconnect.

        Stops audio capture, leaves the meeting, and disconnects from platform.
        Should clean up all resources.

        Returns:
            True if left successfully, False otherwise

        Example:
            await bot.leave_meeting()
            # Bot is no longer in meeting
        """
        pass

    @abstractmethod
    async def get_recording_url(self) -> Optional[str]:
        """
        Get URL of meeting recording (if available).

        Some platforms automatically record meetings. This retrieves the
        recording URL if one exists.

        Returns:
            Recording URL if available, None otherwise

        Example:
            url = await bot.get_recording_url()
            if url:
                print(f"Recording available at: {url}")
        """
        pass

    # ══════════════════════════════════════════════════════════════════════
    # Utility Methods
    # ══════════════════════════════════════════════════════════════════════

    async def ensure_connected(self) -> bool:
        """
        Ensure bot is connected, connecting if necessary.

        Returns:
            True if connected (or successfully connected), False otherwise
        """
        if not self.is_connected:
            return await self.connect()
        return True

    async def ensure_joined(self) -> bool:
        """
        Ensure bot has joined meeting, joining if necessary.

        Returns:
            True if in meeting (or successfully joined), False otherwise
        """
        if not await self.ensure_connected():
            return False

        # Check if we need to join
        # Subclasses should track their join state
        return await self.join_meeting()

    def get_meeting_duration_minutes(self) -> int:
        """Get scheduled meeting duration in minutes"""
        return self.meeting_info.scheduled_duration_minutes

    def get_platform_name(self) -> str:
        """Get human-readable platform name"""
        return self.meeting_info.platform.value.title()
