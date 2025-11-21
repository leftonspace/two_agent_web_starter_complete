"""
Factory for creating meeting bots.

PHASE 7A.1: Provides simple factory pattern for instantiating the correct bot type.
"""

from __future__ import annotations

from typing import Optional

import agent.core_logging as core_logging
from agent.meetings.base import MeetingBot, MeetingInfo, MeetingPlatform
from agent.meetings.google_meet_bot import GoogleMeetBot
from agent.meetings.live_audio_bot import LiveAudioBot
from agent.meetings.teams_bot import TeamsBot
from agent.meetings.zoom_bot import ZoomBot


def create_meeting_bot(meeting_info: MeetingInfo) -> Optional[MeetingBot]:
    """
    Create appropriate bot for meeting platform.

    Args:
        meeting_info: Meeting details including platform type

    Returns:
        MeetingBot instance for the specified platform, or None if unsupported

    Example:
        meeting_info = MeetingInfo(
            platform=MeetingPlatform.ZOOM,
            meeting_id="123456789",
            title="Weekly Standup",
            participants=["Alice", "Bob"],
            start_time=datetime.now(),
            scheduled_duration_minutes=30,
            meeting_url="https://zoom.us/j/123456789"
        )

        bot = create_meeting_bot(meeting_info)
        if bot:
            await bot.connect()
            await bot.join_meeting()
    """
    core_logging.log_event("creating_meeting_bot", {
        "platform": meeting_info.platform.value,
        "meeting_id": meeting_info.meeting_id
    })

    if meeting_info.platform == MeetingPlatform.ZOOM:
        return ZoomBot(meeting_info)

    elif meeting_info.platform == MeetingPlatform.TEAMS:
        return TeamsBot(meeting_info)

    elif meeting_info.platform == MeetingPlatform.LIVE_AUDIO:
        return LiveAudioBot(meeting_info)

    elif meeting_info.platform == MeetingPlatform.GOOGLE_MEET:
        return GoogleMeetBot(meeting_info)

    else:
        core_logging.log_event("unsupported_meeting_platform", {
            "platform": str(meeting_info.platform)
        })
        return None
