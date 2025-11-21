"""
Meeting Platform Integration

PHASE 7A.1: Allows JARVIS to join video meetings, listen to audio, and participate
in real-time conversations.

Supported platforms:
- Zoom (via Zoom SDK)
- Microsoft Teams (via Graph API)
- Google Meet (stub - planned for future)
- Live audio (via PyAudio for in-person meetings)
"""

from agent.meetings.base import (
    MeetingBot,
    MeetingInfo,
    MeetingPlatform,
    AudioChunk,
)
from agent.meetings.factory import create_meeting_bot
from agent.meetings.google_meet_bot import GoogleMeetBot
from agent.meetings.live_audio_bot import LiveAudioBot
from agent.meetings.teams_bot import TeamsBot
from agent.meetings.zoom_bot import ZoomBot

__all__ = [
    # Core abstractions
    "MeetingBot",
    "MeetingInfo",
    "MeetingPlatform",
    "AudioChunk",
    # Factory
    "create_meeting_bot",
    # Concrete implementations
    "ZoomBot",
    "TeamsBot",
    "GoogleMeetBot",
    "LiveAudioBot",
]
