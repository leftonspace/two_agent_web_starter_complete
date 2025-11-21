"""
Base classes for speaker diarization.

PHASE 7A.3: Diarization = determining "who spoke when" in audio.

This module provides abstractions for identifying speakers in meetings,
creating voice embeddings, and mapping anonymous speakers to real people.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class SpeakerSegment:
    """
    Segment of audio attributed to a specific speaker.

    Represents a continuous period where one person was speaking.
    """
    speaker_id: str  # Anonymous ID like "SPEAKER_00", "SPEAKER_01"
    start_time: float  # Seconds from start of audio
    end_time: float  # Seconds from start of audio
    confidence: float = 1.0  # 0.0 - 1.0 (quality of diarization)

    @property
    def duration(self) -> float:
        """Get duration of segment in seconds"""
        return self.end_time - self.start_time

    def overlaps_with(self, other: SpeakerSegment) -> bool:
        """Check if this segment overlaps with another"""
        return not (self.end_time <= other.start_time or
                    self.start_time >= other.end_time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "speaker_id": self.speaker_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "confidence": self.confidence,
        }


@dataclass
class Speaker:
    """
    Identified speaker in meeting.

    Represents a person with their voice characteristics and metadata.
    """
    speaker_id: str  # Unique identifier (e.g., "SPEAKER_001")
    name: Optional[str] = None  # Actual name if known
    email: Optional[str] = None  # Email address
    voice_embedding: Optional[List[float]] = None  # Voice fingerprint (512-dim vector)
    participant_id: Optional[str] = None  # Platform participant ID (Zoom, Teams)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info

    def has_voice_profile(self) -> bool:
        """Check if speaker has a voice embedding"""
        return self.voice_embedding is not None and len(self.voice_embedding) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "speaker_id": self.speaker_id,
            "name": self.name,
            "email": self.email,
            "has_voice_profile": self.has_voice_profile(),
            "participant_id": self.participant_id,
            "metadata": self.metadata,
        }


# ══════════════════════════════════════════════════════════════════════
# Abstract Base Class
# ══════════════════════════════════════════════════════════════════════


class DiarizationEngine(ABC):
    """
    Abstract base class for speaker diarization engines.

    Diarization engines identify "who spoke when" in audio by:
    1. Segmenting audio by speaker (speaker segmentation)
    2. Creating voice fingerprints (embeddings)
    3. Identifying speakers from voice characteristics

    Example:
        engine = PyannoteEngine()

        # Diarize audio
        segments = await engine.diarize_audio(audio_bytes)
        for seg in segments:
            print(f"{seg.speaker_id}: {seg.start_time}-{seg.end_time}")

        # Create voice profile
        embedding = await engine.create_voice_embedding(sample)

        # Identify speaker
        speaker_id = await engine.identify_speaker(audio, known_speakers)
    """

    @abstractmethod
    async def diarize_audio(
        self,
        audio_bytes: bytes,
        num_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        Identify speakers in audio and segment by speaker.

        This is the core diarization function that answers "who spoke when".

        Args:
            audio_bytes: Raw PCM audio data
            num_speakers: Expected number of speakers (optional hint)

        Returns:
            List of segments with speaker IDs and timestamps

        Example:
            segments = await engine.diarize_audio(audio_bytes, num_speakers=3)
            # Returns: [
            #     SpeakerSegment("SPEAKER_00", 0.0, 5.2, 0.95),
            #     SpeakerSegment("SPEAKER_01", 5.2, 8.1, 0.92),
            #     SpeakerSegment("SPEAKER_00", 8.1, 12.0, 0.97),
            # ]
        """
        pass

    @abstractmethod
    async def create_voice_embedding(
        self,
        audio_bytes: bytes
    ) -> List[float]:
        """
        Create voice fingerprint for speaker identification.

        Converts audio into a high-dimensional vector that captures
        unique voice characteristics (pitch, timbre, accent, etc.).

        Args:
            audio_bytes: Audio sample of speaker (3-10 seconds recommended)

        Returns:
            Vector embedding (typically 128-512 dimensions)

        Example:
            embedding = await engine.create_voice_embedding(audio_sample)
            # Returns: [0.123, -0.456, 0.789, ...]  # 512 floats
        """
        pass

    @abstractmethod
    async def identify_speaker(
        self,
        audio_segment: bytes,
        known_speakers: List[Speaker]
    ) -> Optional[str]:
        """
        Identify which known speaker is speaking.

        Compares voice characteristics of unknown audio against
        known speakers' voice embeddings.

        Args:
            audio_segment: Audio to identify
            known_speakers: List of speakers with voice embeddings

        Returns:
            speaker_id of matching speaker, or None if no match

        Example:
            known_speakers = [
                Speaker("SPEAKER_001", name="Alice", voice_embedding=[...]),
                Speaker("SPEAKER_002", name="Bob", voice_embedding=[...]),
            ]

            speaker_id = await engine.identify_speaker(audio, known_speakers)
            # Returns: "SPEAKER_001" if voice matches Alice
        """
        pass

    # ══════════════════════════════════════════════════════════════════════
    # Utility Methods
    # ══════════════════════════════════════════════════════════════════════

    def get_engine_name(self) -> str:
        """
        Get human-readable engine name.

        Returns:
            Engine name (e.g., "Pyannote.audio")
        """
        return self.__class__.__name__.replace("Engine", "")
