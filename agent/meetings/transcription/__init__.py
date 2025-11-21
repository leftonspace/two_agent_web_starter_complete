"""
Real-time speech transcription for meeting audio.

PHASE 7A.2: Converts audio streams to text using multiple providers
with automatic failover for reliability.

Supported providers:
- OpenAI Whisper (best accuracy, batch-based)
- Deepgram (best real-time, streaming)
- Google Speech-to-Text (planned)
- Azure Speech Service (planned)
"""

from agent.meetings.transcription.base import (
    TranscriptionEngine,
    TranscriptSegment,
    TranscriptionProvider,
)
from agent.meetings.transcription.manager import TranscriptionManager

# Import engines with graceful fallback if dependencies not installed
try:
    from agent.meetings.transcription.whisper_engine import WhisperEngine
except ImportError:
    WhisperEngine = None  # OpenAI not installed

try:
    from agent.meetings.transcription.deepgram_engine import DeepgramEngine
except ImportError:
    DeepgramEngine = None  # websockets not installed

__all__ = [
    # Core abstractions
    "TranscriptionEngine",
    "TranscriptSegment",
    "TranscriptionProvider",
    # Manager
    "TranscriptionManager",
    # Engines (may be None if dependencies not installed)
    "WhisperEngine",
    "DeepgramEngine",
]
