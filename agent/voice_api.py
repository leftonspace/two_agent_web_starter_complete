"""
JARVIS Voice API

FastAPI router for voice interaction endpoints.

Provides:
- POST /api/voice/speak - Text-to-speech
- POST /api/voice/listen - Speech-to-text
- POST /api/voice/chat - Full voice conversation turn
- WebSocket /api/voice/stream - Real-time voice streaming

Usage:
    from voice_api import router as voice_router
    app.include_router(voice_router)
"""

from __future__ import annotations

import asyncio
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel

import core_logging

# Import auth if available
try:
    from webapp.auth import User, require_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    User = None
    def require_auth():
        return None

# Import voice components
try:
    from jarvis_voice import JarvisVoice, VoiceConfig, TTSProvider
    from jarvis_voice_chat import JarvisVoiceChat, VoiceWebSocketHandler
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    print(f"[Voice API] Voice components not available: {e}")


# =============================================================================
# API Models
# =============================================================================

class SpeakRequest(BaseModel):
    """Request to synthesize speech"""
    text: str
    return_format: str = "base64"  # base64 or binary
    stream: bool = False


class SpeakResponse(BaseModel):
    """Response with synthesized audio"""
    audio_base64: Optional[str] = None
    format: str = "mp3"
    text_length: int
    processing_time_ms: float


class ListenRequest(BaseModel):
    """Request with audio for transcription"""
    audio_base64: str
    language: str = "en"


class ListenResponse(BaseModel):
    """Response with transcribed text"""
    text: str
    confidence: float = 1.0
    processing_time_ms: float


class VoiceChatRequest(BaseModel):
    """Request for voice chat turn"""
    audio_base64: str
    return_audio: bool = True
    language: str = "en"


class VoiceChatResponse(BaseModel):
    """Response for voice chat turn"""
    user_text: str
    jarvis_text: str
    jarvis_audio_base64: Optional[str] = None
    processing_time_ms: float
    session_ended: bool = False


class VoiceStatusResponse(BaseModel):
    """Voice system status"""
    voice_available: bool
    tts_provider: Optional[str] = None
    stt_available: bool
    session_active: bool = False
    is_speaking: bool = False
    is_listening: bool = False


class VoiceConfigUpdate(BaseModel):
    """Update voice configuration"""
    tts_provider: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None
    openai_voice: Optional[str] = None
    speech_speed: Optional[float] = None


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Global voice chat instance
_voice_chat: Optional[JarvisVoiceChat] = None


def get_voice_chat() -> JarvisVoiceChat:
    """Get or create voice chat instance"""
    global _voice_chat

    if not VOICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Voice system not available. Check dependencies."
        )

    if _voice_chat is None:
        _voice_chat = JarvisVoiceChat()

    return _voice_chat


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status", response_model=VoiceStatusResponse)
async def voice_status():
    """
    Get voice system status.

    Returns information about TTS/STT availability and current state.
    """
    if not VOICE_AVAILABLE:
        return VoiceStatusResponse(
            voice_available=False,
            stt_available=False
        )

    try:
        voice_chat = get_voice_chat()
        session_stats = voice_chat.get_session_stats()

        return VoiceStatusResponse(
            voice_available=True,
            tts_provider=voice_chat.voice.tts_engine.get_provider_name() if voice_chat.voice.tts_engine else None,
            stt_available=voice_chat.voice.stt_engine is not None,
            session_active=session_stats is not None and session_stats.get("is_active", False),
            is_speaking=session_stats.get("is_speaking", False) if session_stats else False,
            is_listening=session_stats.get("is_listening", False) if session_stats else False
        )
    except Exception as e:
        return VoiceStatusResponse(
            voice_available=False,
            stt_available=False
        )


@router.post("/speak", response_model=SpeakResponse)
async def speak(
    request: SpeakRequest,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """
    Convert text to speech (JARVIS voice).

    Args:
        request: SpeakRequest with text to synthesize

    Returns:
        SpeakResponse with base64 encoded audio
    """
    start_time = datetime.now()

    try:
        voice_chat = get_voice_chat()

        # Get audio as base64
        audio_base64 = await voice_chat.voice.get_audio_base64(request.text)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return SpeakResponse(
            audio_base64=audio_base64,
            format="mp3",
            text_length=len(request.text),
            processing_time_ms=processing_time
        )

    except Exception as e:
        core_logging.log_event("voice_speak_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/speak/audio")
async def speak_audio(
    request: SpeakRequest,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """
    Convert text to speech and return raw audio.

    Returns MP3 audio file directly for streaming playback.
    """
    try:
        voice_chat = get_voice_chat()

        # Get raw audio bytes
        audio_bytes = await voice_chat.voice.tts_engine.synthesize(request.text)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=jarvis_speech.mp3"
            }
        )

    except Exception as e:
        core_logging.log_event("voice_speak_audio_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listen", response_model=ListenResponse)
async def listen(
    request: ListenRequest,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """
    Transcribe speech to text.

    Args:
        request: ListenRequest with base64 encoded audio

    Returns:
        ListenResponse with transcribed text
    """
    start_time = datetime.now()

    try:
        voice_chat = get_voice_chat()

        # Decode audio
        audio_bytes = base64.b64decode(request.audio_base64)

        # Transcribe
        text = await voice_chat.voice.stt_engine.transcribe(
            audio_bytes,
            language=request.language
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ListenResponse(
            text=text or "",
            confidence=1.0,
            processing_time_ms=processing_time
        )

    except Exception as e:
        core_logging.log_event("voice_listen_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat_turn(
    request: VoiceChatRequest,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """
    Process a voice conversation turn.

    Transcribes user audio, processes with JARVIS, returns response audio.

    Args:
        request: VoiceChatRequest with user audio

    Returns:
        VoiceChatResponse with transcription and JARVIS response
    """
    try:
        voice_chat = get_voice_chat()

        # Start session if not active
        if not voice_chat.session:
            await voice_chat.start_voice_session()

        # Decode audio
        audio_bytes = base64.b64decode(request.audio_base64)

        # Process voice input
        result = await voice_chat.process_voice_input(
            audio_bytes,
            return_audio=request.return_audio
        )

        return VoiceChatResponse(
            user_text=result.get("user_text", ""),
            jarvis_text=result.get("jarvis_text", ""),
            jarvis_audio_base64=result.get("jarvis_audio_base64"),
            processing_time_ms=result.get("processing_time_ms", 0),
            session_ended=result.get("session_ended", False)
        )

    except Exception as e:
        core_logging.log_event("voice_chat_error", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/start")
async def start_session(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Start a new voice session"""
    try:
        voice_chat = get_voice_chat()
        session_id = await voice_chat.start_voice_session()

        return {
            "session_id": session_id,
            "status": "active"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/end")
async def end_session(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """End the current voice session"""
    try:
        voice_chat = get_voice_chat()
        await voice_chat.end_voice_session()

        return {"status": "ended"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/stats")
async def session_stats(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get current session statistics"""
    try:
        voice_chat = get_voice_chat()
        stats = voice_chat.get_session_stats()

        if not stats:
            return {"status": "no_active_session"}

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WebSocket for Real-time Voice
# =============================================================================

@router.websocket("/stream")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice streaming.

    Protocol:
    - Client connects and receives session info
    - Client sends: {"type": "audio", "data": "<base64 audio>"}
    - Server sends: {"type": "transcription", "text": "..."}
    - Server sends: {"type": "response", "text": "...", "audio": "<base64>"}

    Enables low-latency voice conversation.
    """
    await websocket.accept()

    if not VOICE_AVAILABLE:
        await websocket.send_json({
            "type": "error",
            "message": "Voice system not available"
        })
        await websocket.close()
        return

    try:
        voice_chat = get_voice_chat()
        handler = VoiceWebSocketHandler(voice_chat)

        # Generate connection ID
        import uuid
        connection_id = f"ws_{uuid.uuid4().hex[:8]}"

        await handler.handle_connection(websocket, connection_id)

    except WebSocketDisconnect:
        core_logging.log_event("voice_websocket_disconnected")

    except Exception as e:
        core_logging.log_event("voice_websocket_error", {"error": str(e)})
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except RuntimeError:
            pass


# =============================================================================
# Voice Configuration
# =============================================================================

@router.get("/config")
async def get_voice_config(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get current voice configuration"""
    if not VOICE_AVAILABLE:
        return {"error": "Voice system not available"}

    try:
        voice_chat = get_voice_chat()
        config = voice_chat.voice.config

        return {
            "tts_provider": config.tts_provider.value,
            "openai_voice": config.openai_voice,
            "openai_model": config.openai_model,
            "speech_speed": config.openai_speed,
            "elevenlabs_voice_id": config.elevenlabs_voice_id,
            "cache_enabled": config.cache_enabled
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_voice_config(
    update: VoiceConfigUpdate,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """
    Update voice configuration.

    Note: Changes take effect for new synthesis requests.
    """
    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice system not available")

    try:
        voice_chat = get_voice_chat()
        config = voice_chat.voice.config

        if update.tts_provider:
            config.tts_provider = TTSProvider(update.tts_provider)
            # Reinitialize TTS engine
            voice_chat.voice._init_tts_engine()

        if update.elevenlabs_voice_id:
            config.elevenlabs_voice_id = update.elevenlabs_voice_id
            if hasattr(voice_chat.voice.tts_engine, 'voice_id'):
                voice_chat.voice.tts_engine.voice_id = update.elevenlabs_voice_id

        if update.openai_voice:
            config.openai_voice = update.openai_voice

        if update.speech_speed is not None:
            config.openai_speed = update.speech_speed

        core_logging.log_event("voice_config_updated", {
            "tts_provider": config.tts_provider.value
        })

        return {"status": "updated"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Voice Cache Management
# =============================================================================

@router.post("/cache/clear")
async def clear_voice_cache(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Clear the voice synthesis cache"""
    if not VOICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Voice system not available")

    try:
        voice_chat = get_voice_chat()

        if voice_chat.voice.cache:
            voice_chat.voice.cache.clear()
            return {"status": "cache_cleared"}
        else:
            return {"status": "cache_disabled"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Exports
# =============================================================================

__all__ = ['router']
