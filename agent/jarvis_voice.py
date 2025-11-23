"""
JARVIS Voice System

Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities for JARVIS.
Enables verbal communication with the butler AI.

================================================================================
VOICE SETUP GUIDE - Getting the JARVIS Voice from Iron Man
================================================================================

The JARVIS character from Iron Man is voiced by Paul Bettany. To get an authentic
JARVIS voice, you have several options:

OPTION 1: ElevenLabs Voice Cloning (Best Quality)
-------------------------------------------------
ElevenLabs offers professional-grade voice cloning. You can either:

A) Use a pre-made JARVIS-like voice:
   1. Sign up at https://elevenlabs.io
   2. Browse the Voice Library for "British Butler" or "JARVIS" voices
   3. Copy the voice_id and set: ELEVENLABS_JARVIS_VOICE_ID=<voice_id>

B) Clone your own voice (requires audio samples):
   1. Get ElevenLabs Professional plan ($22/month) for voice cloning
   2. Collect clean audio samples (1-5 minutes total):
      - Search for "JARVIS Iron Man voice clips" on YouTube
      - Use audio extraction tools (ensure you have rights for personal use)
   3. Use ElevenLabs Voice Lab to create a cloned voice
   4. Set the voice_id in your environment

   Code example:
   ```python
   from jarvis_voice import setup_jarvis_voice

   voice = await setup_jarvis_voice(
       elevenlabs_api_key="your_key",
       voice_samples=["sample1.mp3", "sample2.mp3"]
   )
   ```

OPTION 2: OpenAI TTS (Good Fallback)
------------------------------------
OpenAI's TTS has a British-sounding "onyx" voice that works well:

   1. Set OPENAI_API_KEY in your environment
   2. The system will automatically use "onyx" voice
   3. This is the default if ElevenLabs is not configured

OPTION 3: Local TTS (Future)
----------------------------
For fully local/offline operation, Coqui TTS can be integrated.
This is planned for future releases.


ENVIRONMENT VARIABLES
---------------------
Required:
    OPENAI_API_KEY          - For Whisper STT and OpenAI TTS fallback

Optional (for premium JARVIS voice):
    ELEVENLABS_API_KEY      - ElevenLabs API key
    ELEVENLABS_JARVIS_VOICE_ID - Custom voice ID for cloned JARVIS voice

Optional configuration:
    JARVIS_TTS_PROVIDER     - "elevenlabs" or "openai" (default: auto-detect)


DEPENDENCIES
------------
Required:
    pip install openai httpx

For audio playback/recording:
    pip install pyaudio pydub

For MP3 conversion (if pydub not available):
    - Install ffmpeg: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)


API ENDPOINTS
-------------
Once configured, JARVIS voice is available via:

    POST /api/voice/speak     - Text-to-speech
    POST /api/voice/listen    - Speech-to-text
    POST /api/voice/chat      - Full voice conversation turn
    WS   /api/voice/stream    - Real-time voice WebSocket

Example API usage:
    curl -X POST http://localhost:8000/api/voice/speak \\
         -H "Content-Type: application/json" \\
         -d '{"text": "Good morning, sir."}'


PYTHON USAGE
------------
    from jarvis_voice import JarvisVoice

    voice = JarvisVoice()

    # JARVIS speaks
    await voice.speak("Good morning, sir. How may I be of service?")

    # Listen for user
    user_text = await voice.listen()

    # Save to file
    await voice.synthesize_to_file("Hello sir", "greeting.mp3")

================================================================================

TTS Providers:
- ElevenLabs: Best quality, supports voice cloning (for JARVIS voice replica)
- OpenAI TTS: Good quality fallback with British-sounding voices

STT Provider:
- OpenAI Whisper: Best-in-class speech recognition

Usage:
    voice = JarvisVoice()
    await voice.speak("Good morning, sir.")

    # Listen for user input
    text = await voice.listen()
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import os
import tempfile
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union

import core_logging

# =============================================================================
# TTS Provider Imports
# =============================================================================

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

class TTSProvider(Enum):
    """Available TTS providers"""
    ELEVENLABS = "elevenlabs"
    OPENAI = "openai"
    LOCAL = "local"  # For future local TTS support


@dataclass
class VoiceConfig:
    """Voice configuration for JARVIS"""
    # TTS Settings
    tts_provider: TTSProvider = TTSProvider.OPENAI

    # ElevenLabs settings
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: Optional[str] = None  # Custom voice ID for JARVIS
    elevenlabs_model: str = "eleven_monolingual_v1"
    elevenlabs_stability: float = 0.5
    elevenlabs_similarity_boost: float = 0.75

    # OpenAI TTS settings (fallback)
    openai_api_key: Optional[str] = None
    openai_voice: str = "onyx"  # British-sounding, deep voice
    openai_model: str = "tts-1-hd"  # High quality
    openai_speed: float = 1.0

    # STT Settings (Whisper)
    whisper_api_key: Optional[str] = None  # Uses openai_api_key if not set
    whisper_model: str = "whisper-1"

    # Audio settings
    sample_rate: int = 24000  # ElevenLabs default
    channels: int = 1
    audio_format: str = "mp3"

    # Caching
    cache_enabled: bool = True
    cache_dir: str = "data/voice_cache"

    @classmethod
    def from_env(cls) -> "VoiceConfig":
        """Create config from environment variables"""
        return cls(
            tts_provider=TTSProvider(os.getenv("JARVIS_TTS_PROVIDER", "openai")),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
            elevenlabs_voice_id=os.getenv("ELEVENLABS_JARVIS_VOICE_ID"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            whisper_api_key=os.getenv("OPENAI_API_KEY"),
        )


# =============================================================================
# TTS Engine Base Class
# =============================================================================

class TTSEngine(ABC):
    """Abstract base class for TTS engines"""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech audio.

        Args:
            text: Text to synthesize

        Returns:
            Audio bytes (MP3 or WAV format)
        """
        pass

    @abstractmethod
    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        """
        Stream audio synthesis for real-time playback.

        Args:
            text: Text to synthesize

        Yields:
            Audio chunks
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name"""
        pass


# =============================================================================
# ElevenLabs TTS Engine
# =============================================================================

class ElevenLabsTTS(TTSEngine):
    """
    ElevenLabs TTS Engine - Premium quality voice synthesis.

    Supports voice cloning for authentic JARVIS voice replica.
    Requires ElevenLabs API key and optionally a custom voice ID.

    To clone JARVIS voice:
    1. Get audio samples of Paul Bettany as JARVIS (from Iron Man)
    2. Use ElevenLabs voice cloning: https://elevenlabs.io/voice-cloning
    3. Set the voice_id in config
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    # Pre-made British voices (if no custom voice)
    BRITISH_VOICES = {
        "daniel": "onwK4e9ZLuTAKqWW03F9",  # Deep British male
        "adam": "pNInz6obpgDQGcFmaJgB",     # Deep male
        "arnold": "VR6AewLTigWG4xSOukaG",   # Crisp British
    }

    def __init__(self, config: VoiceConfig):
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx not installed. Run: pip install httpx")

        self.config = config
        self.api_key = config.elevenlabs_api_key

        if not self.api_key:
            raise ValueError("ElevenLabs API key required")

        # Use custom voice or fall back to British voice
        self.voice_id = config.elevenlabs_voice_id or self.BRITISH_VOICES["daniel"]

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0
        )

        core_logging.log_event("elevenlabs_tts_initialized", {
            "voice_id": self.voice_id,
            "model": config.elevenlabs_model
        })

    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech with ElevenLabs"""
        try:
            response = await self.client.post(
                f"/text-to-speech/{self.voice_id}",
                json={
                    "text": text,
                    "model_id": self.config.elevenlabs_model,
                    "voice_settings": {
                        "stability": self.config.elevenlabs_stability,
                        "similarity_boost": self.config.elevenlabs_similarity_boost,
                    }
                }
            )

            if response.status_code != 200:
                error_text = response.text
                core_logging.log_event("elevenlabs_error", {
                    "status": response.status_code,
                    "error": error_text[:200]
                })
                raise RuntimeError(f"ElevenLabs API error: {response.status_code}")

            audio_bytes = response.content

            core_logging.log_event("elevenlabs_synthesized", {
                "text_length": len(text),
                "audio_size": len(audio_bytes)
            })

            return audio_bytes

        except httpx.TimeoutException:
            core_logging.log_event("elevenlabs_timeout", {"text_preview": text[:50]})
            raise

    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Stream audio synthesis for real-time playback"""
        try:
            async with self.client.stream(
                "POST",
                f"/text-to-speech/{self.voice_id}/stream",
                json={
                    "text": text,
                    "model_id": self.config.elevenlabs_model,
                    "voice_settings": {
                        "stability": self.config.elevenlabs_stability,
                        "similarity_boost": self.config.elevenlabs_similarity_boost,
                    }
                }
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"ElevenLabs stream error: {response.status_code}")

                async for chunk in response.aiter_bytes(chunk_size=1024):
                    yield chunk

        except Exception as e:
            core_logging.log_event("elevenlabs_stream_error", {"error": str(e)})
            raise

    async def list_voices(self) -> List[Dict[str, Any]]:
        """List available voices"""
        response = await self.client.get("/voices")
        if response.status_code == 200:
            return response.json().get("voices", [])
        return []

    async def clone_voice(
        self,
        name: str,
        audio_files: List[bytes],
        description: str = "JARVIS voice clone"
    ) -> str:
        """
        Clone a voice from audio samples.

        Args:
            name: Name for the cloned voice
            audio_files: List of audio file bytes (MP3/WAV)
            description: Voice description

        Returns:
            Voice ID of the cloned voice
        """
        # Prepare multipart form data
        files = []
        for i, audio in enumerate(audio_files):
            files.append(("files", (f"sample_{i}.mp3", audio, "audio/mpeg")))

        response = await self.client.post(
            "/voices/add",
            data={
                "name": name,
                "description": description,
            },
            files=files
        )

        if response.status_code != 200:
            raise RuntimeError(f"Voice cloning failed: {response.text}")

        voice_id = response.json().get("voice_id")

        core_logging.log_event("voice_cloned", {
            "name": name,
            "voice_id": voice_id
        })

        return voice_id

    def get_provider_name(self) -> str:
        return "ElevenLabs"

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# =============================================================================
# OpenAI TTS Engine
# =============================================================================

class OpenAITTS(TTSEngine):
    """
    OpenAI TTS Engine - Good quality fallback.

    Uses OpenAI's TTS API with British-sounding voices.
    Voice options: alloy, echo, fable, onyx, nova, shimmer

    Recommended for JARVIS: "onyx" (deep, British-sounding)
    """

    def __init__(self, config: VoiceConfig):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not installed. Run: pip install openai")

        self.config = config
        self.api_key = config.openai_api_key

        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.client = openai.AsyncOpenAI(api_key=self.api_key)

        core_logging.log_event("openai_tts_initialized", {
            "voice": config.openai_voice,
            "model": config.openai_model
        })

    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech with OpenAI TTS"""
        try:
            response = await self.client.audio.speech.create(
                model=self.config.openai_model,
                voice=self.config.openai_voice,
                input=text,
                speed=self.config.openai_speed,
                response_format="mp3"
            )

            # Response is a streaming response, read all bytes
            audio_bytes = response.content

            core_logging.log_event("openai_tts_synthesized", {
                "text_length": len(text),
                "audio_size": len(audio_bytes)
            })

            return audio_bytes

        except Exception as e:
            core_logging.log_event("openai_tts_error", {"error": str(e)})
            raise

    async def stream_synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Stream audio synthesis"""
        try:
            response = await self.client.audio.speech.create(
                model=self.config.openai_model,
                voice=self.config.openai_voice,
                input=text,
                speed=self.config.openai_speed,
                response_format="mp3"
            )

            # OpenAI returns the full response, simulate streaming
            audio_bytes = response.content
            chunk_size = 4096

            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i:i + chunk_size]

        except Exception as e:
            core_logging.log_event("openai_tts_stream_error", {"error": str(e)})
            raise

    def get_provider_name(self) -> str:
        return "OpenAI TTS"


# =============================================================================
# Speech-to-Text (STT) Engine
# =============================================================================

class WhisperSTT:
    """
    OpenAI Whisper STT Engine.

    Provides speech-to-text transcription for voice input.
    """

    def __init__(self, config: VoiceConfig):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not installed. Run: pip install openai")

        self.config = config
        api_key = config.whisper_api_key or config.openai_api_key

        if not api_key:
            raise ValueError("OpenAI API key required for Whisper")

        self.client = openai.AsyncOpenAI(api_key=api_key)

        core_logging.log_event("whisper_stt_initialized", {
            "model": config.whisper_model
        })

    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe audio to text.

        Args:
            audio_bytes: Audio data (WAV or MP3)
            language: Language code (default: en)

        Returns:
            Transcribed text
        """
        try:
            # Create file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            response = await self.client.audio.transcriptions.create(
                model=self.config.whisper_model,
                file=audio_file,
                language=language
            )

            text = response.text.strip()

            core_logging.log_event("whisper_transcribed", {
                "audio_size": len(audio_bytes),
                "text_length": len(text),
                "text_preview": text[:50] if text else ""
            })

            return text

        except Exception as e:
            core_logging.log_event("whisper_error", {"error": str(e)})
            raise


# =============================================================================
# Audio Player
# =============================================================================

class AudioPlayer:
    """
    Cross-platform audio player for JARVIS voice output.

    Uses PyAudio for real-time playback.
    """

    def __init__(self, sample_rate: int = 24000):
        if not PYAUDIO_AVAILABLE:
            raise ImportError("pyaudio not installed. Run: pip install pyaudio")

        self.sample_rate = sample_rate
        self.pyaudio = pyaudio.PyAudio()
        self._stream = None

    async def play_audio(self, audio_bytes: bytes, format: str = "mp3"):
        """
        Play audio bytes.

        Args:
            audio_bytes: Audio data
            format: Audio format (mp3 or wav)
        """
        # Convert MP3 to WAV for PyAudio if needed
        if format == "mp3":
            audio_bytes = await self._mp3_to_pcm(audio_bytes)

        # Play audio in thread to not block
        await asyncio.to_thread(self._play_pcm, audio_bytes)

    def _play_pcm(self, pcm_data: bytes):
        """Play PCM audio data"""
        try:
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                output=True
            )

            stream.write(pcm_data)
            stream.stop_stream()
            stream.close()

        except Exception as e:
            core_logging.log_event("audio_playback_error", {"error": str(e)})

    async def _mp3_to_pcm(self, mp3_bytes: bytes) -> bytes:
        """Convert MP3 to PCM for playback"""
        try:
            # Use pydub if available
            from pydub import AudioSegment

            audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
            audio = audio.set_frame_rate(self.sample_rate)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit

            return audio.raw_data

        except ImportError:
            # Fallback: save to temp file and use subprocess
            import subprocess

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(mp3_bytes)
                mp3_path = f.name

            wav_path = mp3_path.replace(".mp3", ".wav")

            try:
                # Use ffmpeg to convert
                subprocess.run([
                    "ffmpeg", "-i", mp3_path,
                    "-ar", str(self.sample_rate),
                    "-ac", "1",
                    "-f", "s16le",
                    wav_path
                ], check=True, capture_output=True)

                with open(wav_path, "rb") as f:
                    return f.read()

            finally:
                # Cleanup temp files
                Path(mp3_path).unlink(missing_ok=True)
                Path(wav_path).unlink(missing_ok=True)

    def close(self):
        """Close PyAudio"""
        if self.pyaudio:
            self.pyaudio.terminate()


# =============================================================================
# Microphone Input
# =============================================================================

class MicrophoneInput:
    """
    Capture audio from microphone for voice input.
    """

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        if not PYAUDIO_AVAILABLE:
            raise ImportError("pyaudio not installed. Run: pip install pyaudio")

        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._recording = False

    async def record_until_silence(
        self,
        silence_threshold: float = 500,
        silence_duration: float = 1.5,
        max_duration: float = 30.0
    ) -> bytes:
        """
        Record audio until silence is detected.

        Args:
            silence_threshold: RMS threshold for silence detection
            silence_duration: Seconds of silence to stop recording
            max_duration: Maximum recording duration

        Returns:
            WAV audio bytes
        """
        import struct
        import math

        frames = []
        silent_chunks = 0
        silence_chunks_needed = int(silence_duration * self.sample_rate / self.chunk_size)
        max_chunks = int(max_duration * self.sample_rate / self.chunk_size)

        self._stream = self.pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        self._recording = True

        try:
            core_logging.log_event("microphone_recording_started")

            for _ in range(max_chunks):
                if not self._recording:
                    break

                data = self._stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

                # Calculate RMS for silence detection
                count = len(data) // 2
                shorts = struct.unpack(f"{count}h", data)
                rms = math.sqrt(sum(s ** 2 for s in shorts) / count) if count else 0

                if rms < silence_threshold:
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed:
                        break
                else:
                    silent_chunks = 0

            # Convert to WAV
            audio_bytes = b''.join(frames)
            wav_bytes = self._create_wav(audio_bytes)

            core_logging.log_event("microphone_recording_stopped", {
                "duration_seconds": len(frames) * self.chunk_size / self.sample_rate,
                "audio_size": len(wav_bytes)
            })

            return wav_bytes

        finally:
            self._stream.stop_stream()
            self._stream.close()
            self._recording = False

    def _create_wav(self, pcm_data: bytes) -> bytes:
        """Create WAV file from PCM data"""
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm_data)

        wav_buffer.seek(0)
        return wav_buffer.read()

    def stop_recording(self):
        """Stop current recording"""
        self._recording = False

    def close(self):
        """Close PyAudio"""
        if self.pyaudio:
            self.pyaudio.terminate()


# =============================================================================
# Voice Cache
# =============================================================================

class VoiceCache:
    """
    Cache synthesized audio to avoid repeated API calls.
    """

    def __init__(self, cache_dir: str = "data/voice_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        """Generate cache key from text and voice"""
        content = f"{voice_id}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, text: str, voice_id: str) -> Optional[bytes]:
        """Get cached audio if exists"""
        cache_key = self._get_cache_key(text, voice_id)
        cache_path = self.cache_dir / f"{cache_key}.mp3"

        if cache_path.exists():
            return cache_path.read_bytes()
        return None

    def set(self, text: str, voice_id: str, audio_bytes: bytes):
        """Cache audio"""
        cache_key = self._get_cache_key(text, voice_id)
        cache_path = self.cache_dir / f"{cache_key}.mp3"
        cache_path.write_bytes(audio_bytes)

    def clear(self):
        """Clear all cached audio"""
        for file in self.cache_dir.glob("*.mp3"):
            file.unlink()


# =============================================================================
# Main JARVIS Voice Class
# =============================================================================

class JarvisVoice:
    """
    Main JARVIS voice interface.

    Combines TTS (speaking) and STT (listening) for voice interaction.

    Usage:
        voice = JarvisVoice()

        # JARVIS speaks
        await voice.speak("Good morning, sir.")

        # Listen for user input
        text = await voice.listen()

        # Full voice conversation
        async for response in voice.converse(chat_handler):
            print(f"User said: {response['user']}")
            print(f"JARVIS said: {response['jarvis']}")
    """

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or VoiceConfig.from_env()

        # Initialize TTS engine based on provider
        self.tts_engine: Optional[TTSEngine] = None
        self._init_tts_engine()

        # Initialize STT engine
        self.stt_engine: Optional[WhisperSTT] = None
        self._init_stt_engine()

        # Initialize audio components
        self.player: Optional[AudioPlayer] = None
        self.microphone: Optional[MicrophoneInput] = None

        # Voice cache
        self.cache = VoiceCache(self.config.cache_dir) if self.config.cache_enabled else None

        # State
        self.is_speaking = False
        self.is_listening = False

        core_logging.log_event("jarvis_voice_initialized", {
            "tts_provider": self.config.tts_provider.value,
            "cache_enabled": self.config.cache_enabled
        })

    def _init_tts_engine(self):
        """Initialize TTS engine based on config"""
        try:
            if self.config.tts_provider == TTSProvider.ELEVENLABS:
                if self.config.elevenlabs_api_key:
                    self.tts_engine = ElevenLabsTTS(self.config)
                else:
                    core_logging.log_event("elevenlabs_no_api_key", {
                        "fallback": "openai"
                    })
                    self.tts_engine = OpenAITTS(self.config)
            else:
                self.tts_engine = OpenAITTS(self.config)

        except Exception as e:
            core_logging.log_event("tts_init_error", {"error": str(e)})

    def _init_stt_engine(self):
        """Initialize STT engine"""
        try:
            self.stt_engine = WhisperSTT(self.config)
        except Exception as e:
            core_logging.log_event("stt_init_error", {"error": str(e)})

    def _get_player(self) -> AudioPlayer:
        """Get or create audio player"""
        if not self.player:
            self.player = AudioPlayer(self.config.sample_rate)
        return self.player

    def _get_microphone(self) -> MicrophoneInput:
        """Get or create microphone input"""
        if not self.microphone:
            self.microphone = MicrophoneInput()
        return self.microphone

    async def speak(self, text: str, stream: bool = False) -> Optional[bytes]:
        """
        Have JARVIS speak the given text.

        Args:
            text: Text for JARVIS to speak
            stream: If True, stream audio for real-time playback

        Returns:
            Audio bytes if not streaming
        """
        if not self.tts_engine:
            core_logging.log_event("tts_unavailable")
            return None

        self.is_speaking = True

        try:
            # Check cache first
            voice_id = getattr(self.tts_engine, 'voice_id', 'default')

            if self.cache:
                cached = self.cache.get(text, voice_id)
                if cached:
                    core_logging.log_event("voice_cache_hit", {
                        "text_preview": text[:50]
                    })

                    # Play cached audio
                    try:
                        player = self._get_player()
                        await player.play_audio(cached, "mp3")
                    except Exception as e:
                        core_logging.log_event("playback_error", {"error": str(e)})

                    return cached

            if stream:
                # Stream audio for real-time playback
                audio_chunks = []
                async for chunk in self.tts_engine.stream_synthesize(text):
                    audio_chunks.append(chunk)
                    # Could play chunks here for real streaming

                audio_bytes = b''.join(audio_chunks)
            else:
                # Get full audio
                audio_bytes = await self.tts_engine.synthesize(text)

            # Cache the audio
            if self.cache and audio_bytes:
                self.cache.set(text, voice_id, audio_bytes)

            # Play audio
            try:
                player = self._get_player()
                await player.play_audio(audio_bytes, "mp3")
            except Exception as e:
                core_logging.log_event("playback_error", {"error": str(e)})

            return audio_bytes

        finally:
            self.is_speaking = False

    async def listen(self, timeout: float = 30.0) -> Optional[str]:
        """
        Listen for user voice input.

        Args:
            timeout: Maximum time to wait for input

        Returns:
            Transcribed text or None if failed
        """
        if not self.stt_engine:
            core_logging.log_event("stt_unavailable")
            return None

        self.is_listening = True

        try:
            # Record from microphone
            mic = self._get_microphone()
            audio_bytes = await mic.record_until_silence(max_duration=timeout)

            # Transcribe
            text = await self.stt_engine.transcribe(audio_bytes)

            return text

        except Exception as e:
            core_logging.log_event("listen_error", {"error": str(e)})
            return None

        finally:
            self.is_listening = False

    async def synthesize_to_file(self, text: str, output_path: str) -> bool:
        """
        Synthesize speech to a file.

        Args:
            text: Text to synthesize
            output_path: Path for output audio file

        Returns:
            True if successful
        """
        if not self.tts_engine:
            return False

        try:
            audio_bytes = await self.tts_engine.synthesize(text)

            Path(output_path).write_bytes(audio_bytes)

            core_logging.log_event("audio_saved", {
                "path": output_path,
                "size": len(audio_bytes)
            })

            return True

        except Exception as e:
            core_logging.log_event("synthesize_to_file_error", {"error": str(e)})
            return False

    async def get_audio_base64(self, text: str) -> Optional[str]:
        """
        Get synthesized audio as base64 string.

        Useful for web API responses.

        Args:
            text: Text to synthesize

        Returns:
            Base64 encoded audio string
        """
        if not self.tts_engine:
            return None

        try:
            # Check cache
            voice_id = getattr(self.tts_engine, 'voice_id', 'default')

            if self.cache:
                cached = self.cache.get(text, voice_id)
                if cached:
                    return base64.b64encode(cached).decode('utf-8')

            audio_bytes = await self.tts_engine.synthesize(text)

            # Cache it
            if self.cache:
                self.cache.set(text, voice_id, audio_bytes)

            return base64.b64encode(audio_bytes).decode('utf-8')

        except Exception as e:
            core_logging.log_event("get_audio_base64_error", {"error": str(e)})
            return None

    async def converse(
        self,
        chat_handler: Callable[[str], str],
        greeting: Optional[str] = None,
        exit_phrases: Optional[List[str]] = None
    ) -> AsyncIterator[Dict[str, str]]:
        """
        Run a voice conversation loop.

        Args:
            chat_handler: Function that takes user text and returns JARVIS response
            greeting: Optional greeting to start with
            exit_phrases: Phrases that end the conversation

        Yields:
            Dict with 'user' and 'jarvis' keys
        """
        exit_phrases = exit_phrases or ["goodbye", "exit", "quit", "stop"]

        # Speak greeting if provided
        if greeting:
            await self.speak(greeting)
            yield {"user": "", "jarvis": greeting}

        while True:
            # Listen for user input
            user_text = await self.listen()

            if not user_text:
                continue

            # Check for exit
            if any(phrase in user_text.lower() for phrase in exit_phrases):
                farewell = "Very good, sir. I shall be here when you need me."
                await self.speak(farewell)
                yield {"user": user_text, "jarvis": farewell}
                break

            # Get JARVIS response
            jarvis_response = chat_handler(user_text)

            # Speak response
            await self.speak(jarvis_response)

            yield {"user": user_text, "jarvis": jarvis_response}

    def close(self):
        """Clean up resources"""
        if self.player:
            self.player.close()
        if self.microphone:
            self.microphone.close()
        if isinstance(self.tts_engine, ElevenLabsTTS):
            asyncio.create_task(self.tts_engine.close())


# =============================================================================
# Voice Setup Helper
# =============================================================================

async def setup_jarvis_voice(
    elevenlabs_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    voice_samples: Optional[List[str]] = None
) -> JarvisVoice:
    """
    Helper to set up JARVIS voice with optional voice cloning.

    Args:
        elevenlabs_api_key: ElevenLabs API key (for premium voice)
        openai_api_key: OpenAI API key (for fallback)
        voice_samples: List of paths to audio samples for voice cloning

    Returns:
        Configured JarvisVoice instance
    """
    config = VoiceConfig(
        elevenlabs_api_key=elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY"),
        openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY"),
        tts_provider=TTSProvider.ELEVENLABS if elevenlabs_api_key else TTSProvider.OPENAI
    )

    voice = JarvisVoice(config)

    # Clone voice if samples provided
    if voice_samples and config.elevenlabs_api_key:
        if isinstance(voice.tts_engine, ElevenLabsTTS):
            audio_files = []
            for path in voice_samples:
                audio_files.append(Path(path).read_bytes())

            voice_id = await voice.tts_engine.clone_voice(
                name="JARVIS",
                audio_files=audio_files,
                description="JARVIS AI Butler Voice"
            )

            voice.tts_engine.voice_id = voice_id

            core_logging.log_event("jarvis_voice_cloned", {
                "voice_id": voice_id
            })

    return voice


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'JarvisVoice',
    'VoiceConfig',
    'TTSProvider',
    'ElevenLabsTTS',
    'OpenAITTS',
    'WhisperSTT',
    'AudioPlayer',
    'MicrophoneInput',
    'setup_jarvis_voice',
]
