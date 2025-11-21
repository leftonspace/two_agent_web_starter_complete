"""
Live audio capture from microphone.

PHASE 7A.1: For in-person meetings or when screen-sharing.
Uses PyAudio to capture from default microphone.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import agent.core_logging as core_logging
from agent.meetings.base import AudioChunk, MeetingBot, MeetingInfo

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


class LiveAudioBot(MeetingBot):
    """Capture live audio from microphone"""

    def __init__(self, meeting_info: MeetingInfo):
        super().__init__(meeting_info)
        
        if PYAUDIO_AVAILABLE:
            self.pyaudio = pyaudio.PyAudio()
        else:
            self.pyaudio = None
        
        self.stream = None

    async def connect(self) -> bool:
        """Check microphone availability"""
        if not PYAUDIO_AVAILABLE:
            core_logging.log_event("pyaudio_not_available", {
                "note": "Install with: pip install pyaudio"
            })
            return False
        
        try:
            device_count = self.pyaudio.get_device_count()
            
            if device_count == 0:
                raise ValueError("No audio devices found")
            
            self.is_connected = True
            
            core_logging.log_event("live_audio_connected", {
                "devices": device_count
            })
            
            return True
            
        except Exception as e:
            core_logging.log_event("live_audio_connection_failed", {
                "error": str(e)
            })
            return False

    async def join_meeting(self) -> bool:
        """'Join' by starting to listen"""
        if not self.is_connected:
            if not await self.connect():
                return False
        
        core_logging.log_event("live_audio_started", {
            "meeting_id": self.meeting_info.meeting_id
        })
        
        return True

    async def start_audio_capture(self) -> bool:
        """Open microphone stream"""
        if not self.is_connected:
            return False
        
        try:
            if PYAUDIO_AVAILABLE:
                self.stream = self.pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024
                )
            
            self.audio_stream_active = True
            self.is_recording = True
            
            core_logging.log_event("live_audio_capture_started")
            
            return True
            
        except Exception as e:
            core_logging.log_event("live_audio_capture_failed", {
                "error": str(e)
            })
            return False

    async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
        """Stream microphone audio"""
        if not self.audio_stream_active:
            if not await self.start_audio_capture():
                return
        
        while self.audio_stream_active:
            try:
                if not self.stream:
                    break
                
                # Read 1 second of audio (16 chunks of 1024 samples)
                frames = []
                for _ in range(16):
                    data = self.stream.read(1024, exception_on_overflow=False)
                    frames.append(data)
                
                audio_bytes = b''.join(frames)
                
                yield AudioChunk(
                    audio_bytes=audio_bytes,
                    timestamp=datetime.now(),
                    duration_ms=1000,
                    sample_rate=16000,
                    channels=1
                )
                
            except Exception as e:
                core_logging.log_event("live_audio_stream_error", {
                    "error": str(e)
                })
                break

    async def get_participants(self) -> List[Dict[str, Any]]:
        """Cannot detect participants from microphone"""
        return []

    async def send_chat_message(self, message: str) -> bool:
        """Cannot send chat in live audio"""
        return False

    async def leave_meeting(self) -> bool:
        """Stop microphone capture"""
        try:
            self.audio_stream_active = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            if self.pyaudio:
                self.pyaudio.terminate()
            
            self.is_connected = False
            
            core_logging.log_event("live_audio_stopped")
            
            return True
            
        except Exception as e:
            core_logging.log_event("live_audio_stop_failed", {
                "error": str(e)
            })
            return False

    async def get_recording_url(self) -> Optional[str]:
        """No recording for live audio"""
        return None
