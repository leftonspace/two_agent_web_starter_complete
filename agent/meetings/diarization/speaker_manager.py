"""
Speaker manager for tracking and identifying meeting participants.

PHASE 7A.3: Combines voice diarization with platform participant data
to create a complete picture of WHO is speaking in meetings.

This manager:
- Tracks known speakers (from previous meetings)
- Registers new speakers with voice samples
- Maps anonymous speaker IDs to real people
- Combines transcripts with speaker information
- Integrates with meeting platform participant lists
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import agent.core_logging as core_logging
from agent.meetings.diarization.base import (
    DiarizationEngine,
    Speaker,
    SpeakerSegment,
)


class SpeakerManager:
    """
    Manages speaker identification in meetings.

    Tracks:
    - Known speakers (from previous meetings)
    - Current meeting participants (from Zoom/Teams)
    - Voice-to-person mapping
    - Speaker segments from diarization

    Example:
        manager = SpeakerManager()

        # Register known speaker
        speaker = await manager.register_speaker(
            name="Alice",
            email="alice@example.com",
            voice_sample=audio_sample
        )

        # Set meeting participants
        manager.set_meeting_participants([
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"}
        ])

        # Diarize meeting
        segments = await manager.diarize_meeting_audio(meeting_audio)

        # Identify speakers
        for seg in segments:
            audio = extract_audio(seg.start_time, seg.end_time)
            name = await manager.identify_speaker_in_segment(audio, seg.speaker_id)
            print(f"{name} spoke from {seg.start_time}s to {seg.end_time}s")
    """

    def __init__(self, diarization_engine: Optional[DiarizationEngine] = None):
        """
        Initialize speaker manager.

        Args:
            diarization_engine: Custom diarization engine
                              (defaults to PyannoteEngine if None)
        """
        # Initialize diarization engine
        if diarization_engine is None:
            try:
                from agent.meetings.diarization.pyannote_engine import PyannoteEngine
                self.engine = PyannoteEngine()
            except ImportError:
                core_logging.log_event("pyannote_not_available", {
                    "note": "Install with: pip install pyannote.audio torch"
                })
                self.engine = None
        else:
            self.engine = diarization_engine

        # Known speakers database
        self.known_speakers: Dict[str, Speaker] = {}

        # Current meeting participants (from platform)
        self.current_participants: List[Dict[str, Any]] = []

        # Mapping of anonymous speaker IDs to actual people
        # e.g., {"SPEAKER_00": "SPEAKER_001"}  # SPEAKER_00 (Pyannote) → Alice
        self.speaker_mapping: Dict[str, str] = {}

    async def register_speaker(
        self,
        name: str,
        email: str,
        voice_sample: bytes
    ) -> Speaker:
        """
        Register a new speaker with voice sample.

        Creates voice embedding for future identification.

        Args:
            name: Speaker's full name
            email: Speaker's email address
            voice_sample: Audio sample (3-10 seconds recommended)

        Returns:
            Speaker object with voice embedding

        Example:
            # Record Alice's voice for 5 seconds
            voice_sample = record_audio(duration=5)

            speaker = await manager.register_speaker(
                name="Alice Smith",
                email="alice@example.com",
                voice_sample=voice_sample
            )

            # Now Alice can be identified in future meetings
        """
        if not self.engine:
            raise RuntimeError("No diarization engine available")

        speaker_id = f"SPEAKER_{len(self.known_speakers):03d}"

        core_logging.log_event("registering_speaker", {
            "speaker_id": speaker_id,
            "name": name
        })

        # Create voice embedding
        embedding = await self.engine.create_voice_embedding(voice_sample)

        speaker = Speaker(
            speaker_id=speaker_id,
            name=name,
            email=email,
            voice_embedding=embedding
        )

        self.known_speakers[speaker_id] = speaker

        core_logging.log_event("speaker_registered", {
            "speaker_id": speaker_id,
            "name": name,
            "embedding_dim": len(embedding) if embedding else 0
        })

        return speaker

    def set_meeting_participants(self, participants: List[Dict[str, Any]]):
        """
        Set participants from meeting platform.

        Args:
            participants: List of participant dicts with keys:
                         - name: str (required)
                         - email: str (optional)
                         - participant_id: str (optional, platform ID)

        Example:
            # Get participants from Zoom
            zoom_participants = await bot.get_participants()

            manager.set_meeting_participants(zoom_participants)
        """
        self.current_participants = participants

        core_logging.log_event("meeting_participants_set", {
            "num_participants": len(participants),
            "participants": [p.get("name") for p in participants]
        })

    async def identify_speaker_in_segment(
        self,
        audio_segment: bytes,
        diarization_id: str
    ) -> Optional[str]:
        """
        Identify actual person from audio segment.

        Args:
            audio_segment: Audio data to identify
            diarization_id: Anonymous speaker ID from diarization
                           (e.g., "SPEAKER_00" from Pyannote)

        Returns:
            Speaker name if identified, None otherwise

        Example:
            # After diarization
            for seg in segments:
                audio = extract_audio(seg.start_time, seg.end_time)
                name = await manager.identify_speaker_in_segment(
                    audio,
                    seg.speaker_id
                )
                print(f"{name or 'Unknown'} spoke")
        """
        if not self.engine:
            return None

        # Check if we already mapped this diarization ID
        if diarization_id in self.speaker_mapping:
            mapped_id = self.speaker_mapping[diarization_id]
            speaker = self.known_speakers.get(mapped_id)
            return speaker.name if speaker else None

        # Try to identify from voice
        speaker_id = await self.engine.identify_speaker(
            audio_segment,
            list(self.known_speakers.values())
        )

        if speaker_id:
            # Create mapping
            self.speaker_mapping[diarization_id] = speaker_id
            speaker = self.known_speakers[speaker_id]

            core_logging.log_event("speaker_mapped", {
                "diarization_id": diarization_id,
                "speaker_id": speaker_id,
                "speaker_name": speaker.name
            })

            return speaker.name

        # Not identified - try to match by name from participants
        # This is a fallback if voice matching fails
        return None

    async def diarize_meeting_audio(
        self,
        audio_bytes: bytes,
        num_expected_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        Perform diarization on meeting audio.

        Args:
            audio_bytes: Full meeting audio
            num_expected_speakers: Number of participants
                                  (auto-detected from participant list if None)

        Returns:
            List of speaker segments with timestamps

        Example:
            # Record full meeting
            meeting_audio = record_meeting()

            # Diarize (automatically uses participant count)
            segments = await manager.diarize_meeting_audio(meeting_audio)

            for seg in segments:
                print(f"{seg.speaker_id}: {seg.start_time}s - {seg.end_time}s")
        """
        if not self.engine:
            raise RuntimeError("No diarization engine available")

        # Use participant count if available
        if num_expected_speakers is None and self.current_participants:
            num_expected_speakers = len(self.current_participants)

        core_logging.log_event("diarizing_meeting_audio", {
            "audio_size_bytes": len(audio_bytes),
            "num_expected_speakers": num_expected_speakers
        })

        # Run diarization
        segments = await self.engine.diarize_audio(
            audio_bytes,
            num_speakers=num_expected_speakers
        )

        return segments

    def get_speaker_by_name(self, name: str) -> Optional[Speaker]:
        """
        Get speaker by name.

        Args:
            name: Speaker name (case-insensitive)

        Returns:
            Speaker object if found, None otherwise

        Example:
            speaker = manager.get_speaker_by_name("Alice")
            if speaker:
                print(f"Found: {speaker.email}")
        """
        for speaker in self.known_speakers.values():
            if speaker.name and speaker.name.lower() == name.lower():
                return speaker
        return None

    def get_speaker_by_email(self, email: str) -> Optional[Speaker]:
        """
        Get speaker by email.

        Args:
            email: Speaker email (case-insensitive)

        Returns:
            Speaker object if found, None otherwise
        """
        for speaker in self.known_speakers.values():
            if speaker.email and speaker.email.lower() == email.lower():
                return speaker
        return None

    def get_transcript_with_speakers(
        self,
        transcript_segments: List[Dict[str, Any]],
        diarization_segments: List[SpeakerSegment]
    ) -> List[Dict[str, Any]]:
        """
        Combine transcription with diarization.

        Maps transcribed text to speakers based on timestamp overlap.

        Args:
            transcript_segments: List of {text, start_time, end_time}
            diarization_segments: List of SpeakerSegment

        Returns:
            List of {text, speaker, start_time, end_time}

        Example:
            # Transcribe audio
            transcript = [
                {"text": "Hello everyone", "start_time": 0.0, "end_time": 2.0},
                {"text": "Hi Alice", "start_time": 2.1, "end_time": 3.5},
            ]

            # Diarize audio
            diarization = [
                SpeakerSegment("SPEAKER_00", 0.0, 2.0, 0.95),
                SpeakerSegment("SPEAKER_01", 2.1, 3.5, 0.92),
            ]

            # Combine
            result = manager.get_transcript_with_speakers(transcript, diarization)
            # result = [
            #     {"text": "Hello everyone", "speaker": "Alice", "start_time": 0.0, ...},
            #     {"text": "Hi Alice", "speaker": "Bob", "start_time": 2.1, ...},
            # ]
        """
        result = []

        for trans_seg in transcript_segments:
            trans_start = trans_seg["start_time"]
            trans_end = trans_seg["end_time"]

            # Find overlapping speaker
            speaker_name = "Unknown"

            for diar_seg in diarization_segments:
                # Check if segments overlap
                if (diar_seg.start_time <= trans_start <= diar_seg.end_time or
                        diar_seg.start_time <= trans_end <= diar_seg.end_time or
                        (trans_start <= diar_seg.start_time and trans_end >= diar_seg.end_time)):

                    # Get speaker name from mapping
                    if diar_seg.speaker_id in self.speaker_mapping:
                        mapped_id = self.speaker_mapping[diar_seg.speaker_id]
                        speaker = self.known_speakers.get(mapped_id)
                        if speaker and speaker.name:
                            speaker_name = speaker.name
                    else:
                        # Use anonymous speaker ID if not mapped
                        speaker_name = diar_seg.speaker_id

                    break

            result.append({
                "text": trans_seg["text"],
                "speaker": speaker_name,
                "start_time": trans_start,
                "end_time": trans_end,
                "confidence": trans_seg.get("confidence", 1.0)
            })

        core_logging.log_event("transcript_speakers_combined", {
            "num_segments": len(result),
            "num_unique_speakers": len(set(s["speaker"] for s in result))
        })

        return result

    def get_speaker_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about speakers in the meeting.

        Returns:
            Dict with speaker statistics

        Example:
            stats = manager.get_speaker_statistics()
            print(f"Known speakers: {stats['num_known_speakers']}")
            print(f"Meeting participants: {stats['num_participants']}")
        """
        return {
            "num_known_speakers": len(self.known_speakers),
            "num_participants": len(self.current_participants),
            "num_mapped_speakers": len(self.speaker_mapping),
            "known_speaker_names": [s.name for s in self.known_speakers.values() if s.name],
            "participant_names": [p.get("name") for p in self.current_participants],
        }
