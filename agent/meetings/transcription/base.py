"""
Base classes for speech transcription engines.

PHASE 7A.2: Provides abstraction for multiple transcription providers
(Whisper, Deepgram, Google, Azure) with a uniform API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════


class TranscriptionProvider(Enum):
    """Supported transcription providers"""
    WHISPER = "whisper"  # OpenAI Whisper (best accuracy, batch-based)
    DEEPGRAM = "deepgram"  # Deepgram (best real-time, streaming)
    GOOGLE = "google"  # Google Speech-to-Text
    AZURE = "azure"  # Azure Speech Service


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class TranscriptSegment:
    """
    Single transcription result.

    Represents a segment of transcribed text with metadata.
    Can be interim (partial) or final result.
    """
    text: str
    confidence: float  # 0.0 - 1.0 (quality of transcription)
    start_time: datetime
    end_time: datetime
    speaker_id: Optional[str] = None  # Speaker diarization (if available)
    language: str = "en"  # ISO 639-1 language code
    is_final: bool = False  # False for interim results, True for final

    @property
    def duration_ms(self) -> float:
        """Get duration of segment in milliseconds"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "speaker_id": self.speaker_id,
            "language": self.language,
            "is_final": self.is_final,
        }


# ══════════════════════════════════════════════════════════════════════
# Abstract Base Class
# ══════════════════════════════════════════════════════════════════════


class TranscriptionEngine(ABC):
    """
    Abstract base class for transcription engines.

    Each provider (Whisper, Deepgram, Google) implements this interface.
    This provides a uniform API for:
    - Transcribing audio chunks
    - Streaming transcription
    - Language support
    - Connection lifecycle

    Example:
        engine = WhisperEngine(api_key="...")
        await engine.start_stream()

        segment = await engine.transcribe_chunk(audio_bytes)
        print(f"Transcribed: {segment.text}")

        await engine.end_stream()
    """

    @abstractmethod
    async def transcribe_chunk(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000
    ) -> TranscriptSegment:
        """
        Transcribe single audio chunk.

        Args:
            audio_bytes: Raw PCM audio data
            sample_rate: Sample rate in Hz (default 16kHz)

        Returns:
            TranscriptSegment with text and metadata

        Example:
            audio_bytes = b'\\x00' * 32000  # 1 second at 16kHz
            segment = await engine.transcribe_chunk(audio_bytes)
            print(f"Text: {segment.text}")
            print(f"Confidence: {segment.confidence}")
        """
        pass

    @abstractmethod
    async def start_stream(self):
        """
        Initialize streaming connection.

        Opens connection to transcription service.
        Must be called before transcribe_chunk() or transcribe_stream().

        Example:
            await engine.start_stream()
            # Now ready to transcribe
        """
        pass

    @abstractmethod
    async def end_stream(self):
        """
        Close streaming connection.

        Cleans up resources and closes connection.
        Should always be called when done transcribing.

        Example:
            await engine.end_stream()
        """
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Does this engine support true streaming?

        Returns:
            True if engine supports streaming (Deepgram, Google)
            False if batch-based (Whisper)

        Example:
            if engine.supports_streaming():
                async for segment in engine.transcribe_stream(audio):
                    print(segment.text)
            else:
                # Use chunk-based
                segment = await engine.transcribe_chunk(audio)
        """
        pass

    @abstractmethod
    async def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO 639-1 language codes (e.g., ["en", "es", "fr"])

        Example:
            languages = await engine.get_supported_languages()
            if "es" in languages:
                print("Spanish is supported")
        """
        pass

    # ══════════════════════════════════════════════════════════════════════
    # Optional Methods (can be overridden)
    # ══════════════════════════════════════════════════════════════════════

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptSegment]:
        """
        Stream audio and get continuous transcription.

        This is an optional method that streaming engines can override
        for better performance. Non-streaming engines will use the
        default implementation that calls transcribe_chunk() repeatedly.

        Args:
            audio_stream: Iterator of audio chunks

        Yields:
            TranscriptSegment objects (interim and final)

        Example:
            async for segment in engine.transcribe_stream(audio):
                if segment.is_final:
                    print(f"Final: {segment.text}")
                else:
                    print(f"Interim: {segment.text}")
        """
        # Default implementation for non-streaming engines
        await self.start_stream()

        try:
            async for audio_chunk in audio_stream:
                segment = await self.transcribe_chunk(audio_chunk)

                if segment.text:  # Only yield non-empty
                    yield segment

        finally:
            await self.end_stream()

    def get_provider_name(self) -> str:
        """
        Get human-readable provider name.

        Returns:
            Provider name (e.g., "OpenAI Whisper", "Deepgram")
        """
        # Default implementation - subclasses can override
        return self.__class__.__name__.replace("Engine", "")
