"""
Zoom meeting bot implementation.

PHASE 7A.1: Uses Zoom SDK to join meetings and capture audio.

NOTE: This implementation uses the Zoom Meeting SDK which requires:
- SDK credentials (SDK Key/Secret)
- Marketplace app approval from Zoom
- Zoom Meeting SDK libraries installed

Setup: https://developers.zoom.us/docs/meeting-sdk/
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional

import agent.core_logging as core_logging
from agent.meetings.base import AudioChunk, MeetingBot, MeetingInfo

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class ZoomBot(MeetingBot):
    """
    Zoom meeting bot implementation.

    Joins Zoom meetings, captures audio, and interacts with participants.
    """

    def __init__(self, meeting_info: MeetingInfo):
        super().__init__(meeting_info)

        # Zoom API credentials (for REST API)
        self.api_key = os.getenv("ZOOM_API_KEY", "")
        self.api_secret = os.getenv("ZOOM_API_SECRET", "")

        # Zoom SDK credentials (for Meeting SDK)
        self.sdk_key = os.getenv("ZOOM_SDK_KEY", "")
        self.sdk_secret = os.getenv("ZOOM_SDK_SECRET", "")

        if not all([self.api_key, self.api_secret]):
            core_logging.log_event("zoom_credentials_missing", {
                "note": "Set ZOOM_API_KEY and ZOOM_API_SECRET"
            })

        # SDK session (would be initialized with actual Zoom SDK)
        self.zoom_session = None
        self.joined_meeting = False

    async def connect(self) -> bool:
        """Connect to Zoom SDK"""
        try:
            # In production, this would initialize the Zoom Meeting SDK
            # For now, we simulate the connection
            core_logging.log_event("zoom_bot_connecting", {
                "meeting_id": self.meeting_info.meeting_id
            })

            # Generate JWT token for authentication
            if JWT_AVAILABLE:
                token = self._generate_jwt_token()
                core_logging.log_event("zoom_jwt_generated", {
                    "token_length": len(token)
                })

            # Actual SDK initialization would happen here
            # self.zoom_session = ZoomSDK.initialize(
            #     sdk_key=self.sdk_key,
            #     sdk_secret=self.sdk_secret
            # )

            self.is_connected = True

            core_logging.log_event("zoom_bot_connected", {
                "meeting_id": self.meeting_info.meeting_id,
                "sdk_available": self.zoom_session is not None
            })

            return True

        except Exception as e:
            core_logging.log_event("zoom_bot_connection_failed", {
                "error": str(e),
                "meeting_id": self.meeting_info.meeting_id
            })
            return False

    async def join_meeting(self) -> bool:
        """Join Zoom meeting"""
        if not self.is_connected:
            if not await self.connect():
                return False

        try:
            core_logging.log_event("zoom_bot_joining", {
                "meeting_id": self.meeting_info.meeting_id,
                "meeting_url": self.meeting_info.meeting_url
            })

            # Actual SDK join would look like:
            # join_response = await self.zoom_session.join_meeting(
            #     meeting_number=self.meeting_info.meeting_id,
            #     display_name="JARVIS (AI Assistant)",
            #     meeting_password=self.meeting_info.password
            # )

            self.joined_meeting = True

            core_logging.log_event("zoom_meeting_joined", {
                "meeting_id": self.meeting_info.meeting_id,
                "title": self.meeting_info.title
            })

            return True

        except Exception as e:
            core_logging.log_event("zoom_meeting_join_failed", {
                "error": str(e),
                "meeting_id": self.meeting_info.meeting_id
            })
            return False

    async def start_audio_capture(self) -> bool:
        """Start capturing audio from meeting"""
        if not self.joined_meeting:
            if not await self.join_meeting():
                return False

        try:
            # Actual SDK audio capture:
            # await self.zoom_session.start_audio_stream(
            #     sample_rate=16000,
            #     channels=1,
            #     format='pcm'
            # )

            self.audio_stream_active = True
            self.is_recording = True

            core_logging.log_event("zoom_audio_capture_started", {
                "meeting_id": self.meeting_info.meeting_id,
                "sample_rate": 16000
            })

            return True

        except Exception as e:
            core_logging.log_event("zoom_audio_capture_failed", {
                "error": str(e)
            })
            return False

    async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
        """
        Stream audio chunks from Zoom meeting.

        Yields 1-second audio chunks at 16kHz.
        """
        if not self.audio_stream_active:
            if not await self.start_audio_capture():
                return

        chunk_counter = 0

        while self.audio_stream_active:
            try:
                # Actual SDK would provide:
                # audio_data = await self.zoom_session.read_audio_data(
                #     chunk_size=16000  # 1 second at 16kHz
                # )

                # Simulate audio chunk (in production, this comes from SDK)
                # For now, yield empty chunks to demonstrate the interface
                audio_data = b'\x00' * 32000  # 16000 samples * 2 bytes (16-bit PCM)

                if audio_data:
                    yield AudioChunk(
                        audio_bytes=audio_data,
                        timestamp=datetime.now(),
                        duration_ms=1000,
                        sample_rate=16000,
                        channels=1
                    )

                    chunk_counter += 1

                    if chunk_counter % 60 == 0:  # Log every minute
                        core_logging.log_event("zoom_audio_streaming", {
                            "chunks_processed": chunk_counter
                        })

                # Small delay to prevent tight loop
                await asyncio.sleep(1.0)

            except Exception as e:
                core_logging.log_event("zoom_audio_stream_error", {
                    "error": str(e)
                })
                break

    async def get_participants(self) -> List[Dict[str, Any]]:
        """Get list of current participants"""
        if not self.joined_meeting:
            return []

        try:
            # Actual SDK would provide:
            # participants = await self.zoom_session.get_participants()

            # Return simulated participants (in production, from SDK)
            core_logging.log_event("zoom_get_participants", {
                "meeting_id": self.meeting_info.meeting_id
            })

            # Example structure
            return [
                {
                    "id": "user_123",
                    "name": participant,
                    "email": f"{participant.lower().replace(' ', '.')}@example.com",
                    "is_host": idx == 0,
                    "is_cohost": False,
                    "audio_state": "unmuted",
                    "video_state": "on"
                }
                for idx, participant in enumerate(self.meeting_info.participants)
            ]

        except Exception as e:
            core_logging.log_event("zoom_get_participants_failed", {
                "error": str(e)
            })
            return []

    async def send_chat_message(self, message: str) -> bool:
        """Send message to meeting chat"""
        if not self.joined_meeting:
            return False

        try:
            # Actual SDK would provide:
            # await self.zoom_session.send_chat_message(
            #     message=message,
            #     to_all=True
            # )

            core_logging.log_event("zoom_chat_message_sent", {
                "message_length": len(message),
                "message_preview": message[:50]
            })

            return True

        except Exception as e:
            core_logging.log_event("zoom_chat_message_failed", {
                "error": str(e)
            })
            return False

    async def leave_meeting(self) -> bool:
        """Leave meeting and cleanup"""
        try:
            # Stop audio capture
            self.audio_stream_active = False
            self.is_recording = False

            # Actual SDK would provide:
            # await self.zoom_session.leave_meeting()
            # await self.zoom_session.disconnect()

            self.joined_meeting = False
            self.is_connected = False

            core_logging.log_event("zoom_meeting_left", {
                "meeting_id": self.meeting_info.meeting_id
            })

            return True

        except Exception as e:
            core_logging.log_event("zoom_leave_meeting_failed", {
                "error": str(e)
            })
            return False

    async def get_recording_url(self) -> Optional[str]:
        """
        Get recording URL via Zoom API.

        Recording must be enabled in meeting settings.
        """
        if not AIOHTTP_AVAILABLE:
            return None

        try:
            token = self._generate_jwt_token() if JWT_AVAILABLE else None
            if not token:
                return None

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                url = f"https://api.zoom.us/v2/meetings/{self.meeting_info.meeting_id}/recordings"

                async with session.get(url, headers=headers, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        recordings = data.get("recording_files", [])

                        # Return first MP4 recording
                        for recording in recordings:
                            if recording.get("file_type") == "MP4":
                                return recording.get("download_url")

            return None

        except Exception as e:
            core_logging.log_event("zoom_get_recording_failed", {
                "error": str(e)
            })
            return None

    def _generate_jwt_token(self) -> str:
        """Generate JWT token for Zoom API"""
        if not JWT_AVAILABLE or not self.api_key or not self.api_secret:
            return ""

        payload = {
            "iss": self.api_key,
            "exp": datetime.now() + timedelta(hours=1)
        }

        try:
            return jwt.encode(payload, self.api_secret, algorithm="HS256")
        except Exception as e:
            core_logging.log_event("zoom_jwt_generation_failed", {
                "error": str(e)
            })
            return ""
