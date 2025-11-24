"""
JARVIS Voice Chat Interface

Combines the JARVIS chat system with voice capabilities for
full verbal interaction with the butler AI.

Usage:
    # Terminal voice chat
    voice_chat = JarvisVoiceChat()
    await voice_chat.start_voice_session()

    # Or with web integration
    audio_response = await voice_chat.process_voice_input(audio_bytes)
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

try:
    import core_logging
except ImportError:
    import logging as core_logging
from jarvis_voice import (
    JarvisVoice,
    VoiceConfig,
    TTSProvider,
    WhisperSTT,
)
from jarvis_persona import (
    JARVIS_GREETINGS,
    JARVIS_FAREWELLS,
)

# Try to import the main chat interfaces
try:
    from jarvis_chat import JarvisChat
    JARVIS_CHAT_AVAILABLE = True
except ImportError:
    JarvisChat = None
    JARVIS_CHAT_AVAILABLE = False

try:
    from conversational_agent import ConversationalAgent
    CONVERSATIONAL_AGENT_AVAILABLE = True
except ImportError:
    ConversationalAgent = None
    CONVERSATIONAL_AGENT_AVAILABLE = False


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class VoiceInteraction:
    """Single voice interaction"""
    user_audio: Optional[bytes]
    user_text: str
    jarvis_text: str
    jarvis_audio: Optional[bytes]
    timestamp: datetime
    processing_time_ms: float


@dataclass
class VoiceSessionState:
    """State for a voice session"""
    session_id: str
    is_active: bool
    is_listening: bool
    is_speaking: bool
    interactions: List[VoiceInteraction]
    started_at: datetime
    last_activity: datetime


# =============================================================================
# JARVIS Voice Chat
# =============================================================================

class JarvisVoiceChat:
    """
    Voice-enabled JARVIS chat interface.

    Provides full voice interaction with JARVIS, combining:
    - Speech-to-Text (user voice input)
    - Text chat processing (JARVIS logic)
    - Text-to-Speech (JARVIS voice output)

    Maintains JARVIS as master orchestrator while adding voice capabilities.
    """

    # Exit phrases to end voice session
    EXIT_PHRASES = [
        "goodbye", "bye", "exit", "quit", "stop listening",
        "end session", "that will be all", "dismissed"
    ]

    # Wake words to start listening (optional push-to-talk alternative)
    WAKE_WORDS = ["jarvis", "hey jarvis", "okay jarvis"]

    def __init__(
        self,
        voice_config: Optional[VoiceConfig] = None,
        enable_wake_word: bool = False,
        auto_listen: bool = True
    ):
        """
        Initialize voice chat.

        Args:
            voice_config: Voice configuration (uses env vars if not provided)
            enable_wake_word: If True, wait for wake word before processing
            auto_listen: If True, automatically listen after speaking
        """
        # Voice system
        self.voice = JarvisVoice(voice_config)
        self.enable_wake_word = enable_wake_word
        self.auto_listen = auto_listen

        # Chat backend
        self.chat: Optional[Any] = None
        self._init_chat_backend()

        # Session state
        self.session: Optional[VoiceSessionState] = None

        # Callbacks
        self.on_listening_start: Optional[Callable] = None
        self.on_listening_stop: Optional[Callable] = None
        self.on_speaking_start: Optional[Callable] = None
        self.on_speaking_stop: Optional[Callable] = None
        self.on_transcription: Optional[Callable[[str], None]] = None

        core_logging.log_event("jarvis_voice_chat_initialized", {
            "wake_word_enabled": enable_wake_word,
            "auto_listen": auto_listen
        })

    def _init_chat_backend(self):
        """Initialize the chat backend"""
        if JARVIS_CHAT_AVAILABLE and JarvisChat:
            self.chat = JarvisChat(memory_enabled=True)
            core_logging.log_event("chat_backend", {"type": "JarvisChat"})
        elif CONVERSATIONAL_AGENT_AVAILABLE and ConversationalAgent:
            self.chat = ConversationalAgent()
            core_logging.log_event("chat_backend", {"type": "ConversationalAgent"})
        else:
            core_logging.log_event("chat_backend_unavailable")

    async def start_voice_session(self) -> str:
        """
        Start a voice interaction session.

        Returns:
            Session ID
        """
        import uuid

        session_id = f"voice_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        self.session = VoiceSessionState(
            session_id=session_id,
            is_active=True,
            is_listening=False,
            is_speaking=False,
            interactions=[],
            started_at=now,
            last_activity=now
        )

        # Start chat session if available
        if self.chat and hasattr(self.chat, 'start_session'):
            await self.chat.start_session()

        core_logging.log_event("voice_session_started", {
            "session_id": session_id
        })

        return session_id

    async def end_voice_session(self):
        """End the current voice session"""
        if self.session:
            self.session.is_active = False

            core_logging.log_event("voice_session_ended", {
                "session_id": self.session.session_id,
                "interactions": len(self.session.interactions),
                "duration_seconds": (datetime.now() - self.session.started_at).total_seconds()
            })

        self.session = None

    async def process_voice_input(
        self,
        audio_bytes: bytes,
        return_audio: bool = True
    ) -> Dict[str, Any]:
        """
        Process voice input and return response.

        This is the main entry point for web/API integration.

        Args:
            audio_bytes: User's audio input (WAV format)
            return_audio: If True, include audio in response

        Returns:
            Dict with:
            - user_text: Transcribed user input
            - jarvis_text: JARVIS text response
            - jarvis_audio_base64: Base64 encoded audio (if return_audio)
            - processing_time_ms: Total processing time
        """
        start_time = datetime.now()

        try:
            # Transcribe user audio
            if self.voice.stt_engine is None:
                return {
                    "user_text": "",
                    "jarvis_text": "Speech recognition is not available.",
                    "jarvis_audio_base64": None,
                    "processing_time_ms": 0
                }
            user_text = await self.voice.stt_engine.transcribe(audio_bytes)

            if not user_text or user_text.strip() == "":
                return {
                    "user_text": "",
                    "jarvis_text": "I didn't catch that, sir. Could you repeat?",
                    "jarvis_audio_base64": None,
                    "processing_time_ms": 0
                }

            # Notify transcription callback
            if self.on_transcription:
                self.on_transcription(user_text)

            # Check for exit phrases
            if any(phrase in user_text.lower() for phrase in self.EXIT_PHRASES):
                import random
                farewell = random.choice(JARVIS_FAREWELLS)

                response = {
                    "user_text": user_text,
                    "jarvis_text": farewell,
                    "session_ended": True
                }

                if return_audio:
                    response["jarvis_audio_base64"] = await self.voice.get_audio_base64(farewell)

                return response

            # Get JARVIS response
            jarvis_text = await self._get_chat_response(user_text)

            # Generate audio response
            jarvis_audio_base64 = None
            if return_audio:
                jarvis_audio_base64 = await self.voice.get_audio_base64(jarvis_text)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Store interaction
            if self.session:
                interaction = VoiceInteraction(
                    user_audio=audio_bytes,
                    user_text=user_text,
                    jarvis_text=jarvis_text,
                    jarvis_audio=base64.b64decode(jarvis_audio_base64) if jarvis_audio_base64 else None,
                    timestamp=datetime.now(),
                    processing_time_ms=processing_time
                )
                self.session.interactions.append(interaction)
                self.session.last_activity = datetime.now()

            return {
                "user_text": user_text,
                "jarvis_text": jarvis_text,
                "jarvis_audio_base64": jarvis_audio_base64,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            core_logging.log_event("voice_input_error", {"error": str(e)})

            error_response = "I'm afraid I encountered a technical difficulty, sir. My apologies."
            return {
                "user_text": "",
                "jarvis_text": error_response,
                "jarvis_audio_base64": await self.voice.get_audio_base64(error_response) if return_audio else None,
                "error": str(e)
            }

    async def _get_chat_response(self, user_text: str) -> str:
        """Get response from chat backend"""
        if not self.chat:
            return "I'm afraid my conversational systems are offline, sir."

        try:
            if hasattr(self.chat, 'handle_message'):
                # JarvisChat
                response = await self.chat.handle_message(user_text)
                return response.get("content", "")
            elif hasattr(self.chat, 'chat'):
                # ConversationalAgent
                return await self.chat.chat(user_text)
            else:
                return "At your service, sir."

        except Exception as e:
            core_logging.log_event("chat_response_error", {"error": str(e)})
            return f"I encountered an issue processing your request, sir: {str(e)}"

    async def run_voice_loop(self, greeting: Optional[str] = None):
        """
        Run interactive voice conversation loop.

        For terminal/CLI use. Listens for user voice input,
        processes with JARVIS, and speaks the response.

        Args:
            greeting: Optional greeting to start with
        """
        import random

        # Start session
        await self.start_voice_session()

        # Greeting
        if greeting is None:
            greeting = random.choice(JARVIS_GREETINGS)

        print(f"\n[JARVIS]: {greeting}")
        await self.voice.speak(greeting)

        try:
            while self.session and self.session.is_active:
                # Listen for input
                print("\n[Listening...]")

                if self.on_listening_start:
                    self.on_listening_start()

                self.session.is_listening = True
                user_text = await self.voice.listen()
                self.session.is_listening = False

                if self.on_listening_stop:
                    self.on_listening_stop()

                if not user_text:
                    print("[No input detected]")
                    continue

                print(f"\n[You]: {user_text}")

                # Check for exit
                if any(phrase in user_text.lower() for phrase in self.EXIT_PHRASES):
                    farewell = random.choice(JARVIS_FAREWELLS)
                    print(f"\n[JARVIS]: {farewell}")
                    await self.voice.speak(farewell)
                    break

                # Get response
                jarvis_text = await self._get_chat_response(user_text)

                # Speak response
                print(f"\n[JARVIS]: {jarvis_text}")

                if self.on_speaking_start:
                    self.on_speaking_start()

                self.session.is_speaking = True
                await self.voice.speak(jarvis_text)
                self.session.is_speaking = False

                if self.on_speaking_stop:
                    self.on_speaking_stop()

                # Store interaction
                self.session.interactions.append(VoiceInteraction(
                    user_audio=None,
                    user_text=user_text,
                    jarvis_text=jarvis_text,
                    jarvis_audio=None,
                    timestamp=datetime.now(),
                    processing_time_ms=0
                ))

        except KeyboardInterrupt:
            print("\n[Session interrupted]")

        finally:
            await self.end_voice_session()

    async def speak(self, text: str) -> Optional[bytes]:
        """
        Have JARVIS speak text.

        Args:
            text: Text to speak

        Returns:
            Audio bytes
        """
        if self.session:
            self.session.is_speaking = True

        if self.on_speaking_start:
            self.on_speaking_start()

        try:
            return await self.voice.speak(text)
        finally:
            if self.session:
                self.session.is_speaking = False
            if self.on_speaking_stop:
                self.on_speaking_stop()

    async def listen(self) -> Optional[str]:
        """
        Listen for user voice input.

        Returns:
            Transcribed text
        """
        if self.session:
            self.session.is_listening = True

        if self.on_listening_start:
            self.on_listening_start()

        try:
            return await self.voice.listen()
        finally:
            if self.session:
                self.session.is_listening = False
            if self.on_listening_stop:
                self.on_listening_stop()

    def get_session_stats(self) -> Optional[Dict[str, Any]]:
        """Get current session statistics"""
        if not self.session:
            return None

        return {
            "session_id": self.session.session_id,
            "is_active": self.session.is_active,
            "is_listening": self.session.is_listening,
            "is_speaking": self.session.is_speaking,
            "interaction_count": len(self.session.interactions),
            "started_at": self.session.started_at.isoformat(),
            "last_activity": self.session.last_activity.isoformat(),
            "duration_seconds": (datetime.now() - self.session.started_at).total_seconds()
        }

    def close(self):
        """Clean up resources"""
        self.voice.close()


# =============================================================================
# WebSocket Voice Handler (for real-time web integration)
# =============================================================================

class VoiceWebSocketHandler:
    """
    WebSocket handler for real-time voice streaming.

    Enables low-latency voice interaction over WebSocket connection.

    Protocol:
    - Client sends: {"type": "audio", "data": "<base64 audio>"}
    - Server sends: {"type": "transcription", "text": "..."}
    - Server sends: {"type": "response", "text": "...", "audio": "<base64>"}
    """

    def __init__(self, voice_chat: JarvisVoiceChat):
        self.voice_chat = voice_chat
        self.active_connections: Dict[str, Any] = {}

    async def handle_connection(
        self,
        websocket: Any,
        connection_id: str
    ):
        """
        Handle a WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
        """
        self.active_connections[connection_id] = websocket

        # Start voice session
        session_id = await self.voice_chat.start_voice_session()

        try:
            # Send session info
            await websocket.send_json({
                "type": "session_started",
                "session_id": session_id
            })

            # Process messages
            async for message in websocket.iter_json():
                if message.get("type") == "audio":
                    # Process voice input
                    audio_base64 = message.get("data", "")
                    audio_bytes = base64.b64decode(audio_base64)

                    response = await self.voice_chat.process_voice_input(
                        audio_bytes,
                        return_audio=True
                    )

                    # Send transcription
                    await websocket.send_json({
                        "type": "transcription",
                        "text": response["user_text"]
                    })

                    # Send response
                    await websocket.send_json({
                        "type": "response",
                        "text": response["jarvis_text"],
                        "audio": response.get("jarvis_audio_base64")
                    })

                    # Check if session ended
                    if response.get("session_ended"):
                        break

                elif message.get("type") == "text":
                    # Process text input (no STT needed)
                    user_text = message.get("text", "")
                    jarvis_text = await self.voice_chat._get_chat_response(user_text)

                    response = {
                        "type": "response",
                        "text": jarvis_text,
                        "audio": await self.voice_chat.voice.get_audio_base64(jarvis_text)
                    }

                    await websocket.send_json(response)

        except Exception as e:
            core_logging.log_event("websocket_error", {
                "connection_id": connection_id,
                "error": str(e)
            })

        finally:
            await self.voice_chat.end_voice_session()
            del self.active_connections[connection_id]


# =============================================================================
# CLI Entry Point
# =============================================================================

async def main():
    """Run JARVIS voice chat from command line"""
    print("\n" + "=" * 60)
    print("  JARVIS Voice Interface")
    print("  Say 'goodbye' to exit")
    print("=" * 60)

    voice_chat = JarvisVoiceChat()

    try:
        await voice_chat.run_voice_loop()
    finally:
        voice_chat.close()


if __name__ == "__main__":
    asyncio.run(main())


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'JarvisVoiceChat',
    'VoiceInteraction',
    'VoiceSessionState',
    'VoiceWebSocketHandler',
]
