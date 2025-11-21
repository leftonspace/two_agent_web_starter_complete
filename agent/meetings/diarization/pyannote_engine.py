"""
Pyannote.audio speaker diarization engine.

PHASE 7A.3: State-of-the-art open-source speaker diarization.

Pyannote.audio is a research-grade speaker diarization toolkit with:
- 95%+ accuracy for speaker segmentation
- Robust voice embedding models
- Support for unlimited speakers
- Pre-trained models from HuggingFace

Requires: pip install pyannote.audio torch torchaudio
"""

from __future__ import annotations

import io
from typing import List, Optional

import agent.core_logging as core_logging
from agent.meetings.diarization.base import (
    DiarizationEngine,
    Speaker,
    SpeakerSegment,
)

try:
    import numpy as np
    import torch
    from scipy.io import wavfile

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from pyannote.audio import Model, Pipeline

    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False


class PyannoteEngine(DiarizationEngine):
    """
    Pyannote.audio speaker diarization engine.

    Uses state-of-the-art deep learning models for:
    - Speaker diarization (who spoke when)
    - Voice embedding (speaker fingerprints)
    - Speaker verification (is this the same person?)

    Typical accuracy: 95%+ for known speakers
    """

    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize Pyannote engine.

        Args:
            auth_token: HuggingFace token for model access
                       Get from: https://huggingface.co/settings/tokens
                       Required to download pretrained models

        Raises:
            ImportError: If pyannote.audio or dependencies not installed
        """
        if not PYANNOTE_AVAILABLE:
            raise ImportError(
                "pyannote.audio not installed. Run: pip install pyannote.audio torch torchaudio"
            )

        if not NUMPY_AVAILABLE:
            raise ImportError(
                "numpy/scipy not installed. Run: pip install numpy scipy"
            )

        self.auth_token = auth_token
        self.pipeline: Optional[Pipeline] = None
        self.embedding_model: Optional[Model] = None

        self._init_models()

    def _init_models(self):
        """
        Initialize Pyannote models.

        Downloads pretrained models from HuggingFace if not cached.
        Uses GPU if available for faster inference.
        """
        try:
            core_logging.log_event("pyannote_initializing")

            # Load speaker diarization pipeline
            # This is the main model for "who spoke when"
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.auth_token
            )

            # Load embedding model for speaker identification
            # This creates voice fingerprints
            self.embedding_model = Model.from_pretrained(
                "pyannote/embedding",
                use_auth_token=self.auth_token
            )

            # Use GPU if available (10x faster)
            if torch.cuda.is_available():
                device = torch.device("cuda")
                self.pipeline.to(device)
                self.embedding_model.to(device)
                core_logging.log_event("pyannote_using_gpu")
            else:
                core_logging.log_event("pyannote_using_cpu", {
                    "note": "GPU not available, using CPU (slower)"
                })

            core_logging.log_event("pyannote_models_loaded", {
                "gpu_available": torch.cuda.is_available()
            })

        except Exception as e:
            core_logging.log_event("pyannote_init_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise

    async def diarize_audio(
        self,
        audio_bytes: bytes,
        num_speakers: Optional[int] = None
    ) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on audio.

        Identifies speaker change points and assigns speaker labels.

        Args:
            audio_bytes: Raw WAV audio data (16-bit PCM, mono)
            num_speakers: Expected number of speakers (helps accuracy)

        Returns:
            List of speaker segments with timestamps

        Example:
            audio = load_wav_file("meeting.wav")
            segments = await engine.diarize_audio(audio, num_speakers=3)

            for seg in segments:
                print(f"{seg.speaker_id} spoke from {seg.start_time}s to {seg.end_time}s")
        """
        try:
            core_logging.log_event("pyannote_diarization_start", {
                "audio_size_bytes": len(audio_bytes),
                "num_speakers_hint": num_speakers
            })

            # Convert bytes to format Pyannote expects
            audio_io = io.BytesIO(audio_bytes)
            sample_rate, audio_data = wavfile.read(audio_io)

            # Convert to tensor
            waveform = torch.from_numpy(audio_data).float()

            # Normalize to [-1, 1] if needed
            if waveform.abs().max() > 1.0:
                waveform = waveform / 32768.0  # 16-bit PCM

            # Add batch dimension if needed
            if waveform.dim() == 1:
                waveform = waveform.unsqueeze(0)

            # Prepare audio dict for Pyannote
            audio_dict = {
                "waveform": waveform,
                "sample_rate": sample_rate
            }

            # Run diarization pipeline
            if num_speakers:
                diarization = self.pipeline(
                    audio_dict,
                    num_speakers=num_speakers
                )
            else:
                diarization = self.pipeline(audio_dict)

            # Convert Pyannote output to SpeakerSegment objects
            segments = []

            for turn, _, speaker_label in diarization.itertracks(yield_label=True):
                segment = SpeakerSegment(
                    speaker_id=speaker_label,
                    start_time=turn.start,
                    end_time=turn.end,
                    confidence=1.0  # Pyannote doesn't provide per-segment confidence
                )
                segments.append(segment)

            num_speakers_found = len(set(s.speaker_id for s in segments))

            core_logging.log_event("pyannote_diarization_complete", {
                "num_segments": len(segments),
                "num_speakers_found": num_speakers_found,
                "total_speech_time": sum(s.duration for s in segments)
            })

            return segments

        except Exception as e:
            core_logging.log_event("pyannote_diarization_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return []

    async def create_voice_embedding(
        self,
        audio_bytes: bytes
    ) -> List[float]:
        """
        Create voice embedding for speaker identification.

        Converts audio into a 512-dimensional vector that captures
        unique voice characteristics.

        Args:
            audio_bytes: Audio sample (3-10 seconds recommended)

        Returns:
            512-dimensional vector representing voice characteristics

        Example:
            sample = record_speaker_audio(duration=5)  # 5 seconds
            embedding = await engine.create_voice_embedding(sample)
            # embedding = [0.123, -0.456, ...]  # 512 floats
        """
        try:
            core_logging.log_event("pyannote_embedding_start", {
                "audio_size_bytes": len(audio_bytes)
            })

            # Convert audio bytes to tensor
            audio_io = io.BytesIO(audio_bytes)
            sample_rate, audio_data = wavfile.read(audio_io)

            waveform = torch.from_numpy(audio_data).float()

            # Normalize
            if waveform.abs().max() > 1.0:
                waveform = waveform / 32768.0

            # Add batch dimension
            if waveform.dim() == 1:
                waveform = waveform.unsqueeze(0)

            # Prepare audio dict
            audio_dict = {
                "waveform": waveform,
                "sample_rate": sample_rate
            }

            # Generate embedding
            with torch.no_grad():
                embedding = self.embedding_model(audio_dict)

            # Convert to list
            embedding_list = embedding.squeeze().cpu().numpy().tolist()

            core_logging.log_event("pyannote_embedding_complete", {
                "embedding_dim": len(embedding_list)
            })

            return embedding_list

        except Exception as e:
            core_logging.log_event("pyannote_embedding_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return []

    async def identify_speaker(
        self,
        audio_segment: bytes,
        known_speakers: List[Speaker]
    ) -> Optional[str]:
        """
        Identify speaker from known speakers using voice embedding.

        Uses cosine similarity to match voice embeddings.

        Args:
            audio_segment: Audio to identify
            known_speakers: List of speakers with voice embeddings

        Returns:
            speaker_id if identified (similarity > 0.75), None otherwise

        Example:
            known_speakers = [
                Speaker("SPEAKER_001", name="Alice", voice_embedding=[...]),
                Speaker("SPEAKER_002", name="Bob", voice_embedding=[...]),
            ]

            # Unknown audio
            unknown_audio = get_meeting_segment(120.0, 125.0)

            speaker_id = await engine.identify_speaker(unknown_audio, known_speakers)
            # Returns: "SPEAKER_001" if voice matches Alice
        """
        if not known_speakers:
            return None

        try:
            core_logging.log_event("pyannote_identification_start", {
                "num_known_speakers": len(known_speakers)
            })

            # Get embedding for unknown speaker
            unknown_embedding = await self.create_voice_embedding(audio_segment)

            if not unknown_embedding:
                return None

            # Compare with known speakers using cosine similarity
            best_match = None
            best_similarity = -1.0

            unknown_vec = np.array(unknown_embedding)

            for speaker in known_speakers:
                if not speaker.voice_embedding:
                    continue

                known_vec = np.array(speaker.voice_embedding)

                # Cosine similarity: dot product / (norm1 * norm2)
                similarity = np.dot(unknown_vec, known_vec) / (
                    np.linalg.norm(unknown_vec) * np.linalg.norm(known_vec)
                )

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = speaker.speaker_id

            # Threshold for positive identification
            # 0.75 = reasonably confident match
            # Higher threshold = fewer false positives but may miss some matches
            SIMILARITY_THRESHOLD = 0.75

            if best_similarity > SIMILARITY_THRESHOLD:
                core_logging.log_event("pyannote_speaker_identified", {
                    "speaker_id": best_match,
                    "similarity": best_similarity
                })
                return best_match

            core_logging.log_event("pyannote_speaker_not_identified", {
                "best_similarity": best_similarity,
                "threshold": SIMILARITY_THRESHOLD
            })

            return None

        except Exception as e:
            core_logging.log_event("pyannote_identification_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return None

    def get_engine_name(self) -> str:
        """Get engine name"""
        return "Pyannote.audio"
