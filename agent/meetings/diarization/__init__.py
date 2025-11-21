"""
Speaker diarization for meeting audio.

PHASE 7A.3: Identifies WHO is speaking at each moment in meetings.
Combines voice-based identification with platform participant data.

Key features:
- Speaker segmentation (who spoke when)
- Voice embedding for speaker recognition
- Integration with meeting participant lists
- Speaker-to-person mapping
"""

from agent.meetings.diarization.base import (
    DiarizationEngine,
    Speaker,
    SpeakerSegment,
)
from agent.meetings.diarization.speaker_manager import SpeakerManager

# Import Pyannote engine with graceful fallback
try:
    from agent.meetings.diarization.pyannote_engine import PyannoteEngine
except ImportError:
    PyannoteEngine = None  # pyannote.audio not installed

__all__ = [
    # Core abstractions
    "DiarizationEngine",
    "Speaker",
    "SpeakerSegment",
    # Manager
    "SpeakerManager",
    # Engines (may be None if dependencies not installed)
    "PyannoteEngine",
]
