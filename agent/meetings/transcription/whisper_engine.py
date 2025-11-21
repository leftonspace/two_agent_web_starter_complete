"""
OpenAI Whisper transcription engine.

PHASE 7A.2: Best accuracy transcription, but batch-based (not true streaming).
Good for high-quality transcription when <2 second latency is acceptable.

API: https://platform.openai.com/docs/guides/speech-to-text
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from io import BytesIO
from typing import List

import agent.core_logging as core_logging
from agent.meetings.transcription.base import TranscriptionEngine, TranscriptSegment

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class WhisperEngine(TranscriptionEngine):
    """
    OpenAI Whisper transcription.

    Provides best-in-class accuracy for speech recognition.
    Not true streaming - each chunk is transcribed independently.

    Typical latency: 500ms - 2 seconds per chunk.
    """

    def __init__(self, api_key: str, model: str = "whisper-1"):
        """
        Initialize Whisper engine.

        Args:
            api_key: OpenAI API key
            model: Whisper model name (default: whisper-1)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. Run: pip install openai"
            )

        self.api_key = api_key
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.is_streaming = False

    async def transcribe_chunk(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000
    ) -> TranscriptSegment:
        """
        Transcribe audio chunk with Whisper.

        Note: Whisper is batch-based, not streaming.
        Each chunk is transcribed independently.

        Args:
            audio_bytes: Raw PCM audio data
            sample_rate: Sample rate in Hz (default 16kHz)

        Returns:
            TranscriptSegment with transcribed text
        """
        try:
            start_time = datetime.now()

            # Convert bytes to WAV file-like object
            # Whisper API expects a file, so we create BytesIO
            audio_file = self._create_audio_file(audio_bytes, sample_rate)

            core_logging.log_event("whisper_transcription_start", {
                "audio_size_bytes": len(audio_bytes),
                "sample_rate": sample_rate
            })

            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

            end_time = datetime.now()

            # Extract text and metadata
            text = response.text.strip()

            # Whisper doesn't provide confidence directly
            # Estimate based on no_speech_prob (if available)
            no_speech_prob = getattr(response, "no_speech_prob", 0.0)
            confidence = 1.0 - no_speech_prob

            # Get language
            language = getattr(response, "language", "en")

            segment = TranscriptSegment(
                text=text,
                confidence=confidence,
                start_time=start_time,
                end_time=end_time,
                language=language,
                is_final=True  # Whisper always returns final results
            )

            latency_ms = (end_time - start_time).total_seconds() * 1000

            core_logging.log_event("whisper_transcription_complete", {
                "text_length": len(text),
                "text_preview": text[:50] if text else "",
                "confidence": confidence,
                "language": language,
                "latency_ms": latency_ms
            })

            return segment

        except Exception as e:
            core_logging.log_event("whisper_transcription_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })

            # Return empty segment on error
            return TranscriptSegment(
                text="",
                confidence=0.0,
                start_time=datetime.now(),
                end_time=datetime.now(),
                is_final=True
            )

    def _create_audio_file(self, audio_bytes: bytes, sample_rate: int) -> BytesIO:
        """
        Create WAV file from raw PCM audio bytes.

        Whisper API expects a file, so we create a BytesIO object
        with WAV headers.

        Args:
            audio_bytes: Raw PCM audio (16-bit signed)
            sample_rate: Sample rate in Hz

        Returns:
            BytesIO object with WAV file data
        """
        import wave
        import struct

        # Create BytesIO for WAV file
        wav_file = BytesIO()

        # Write WAV file
        with wave.open(wav_file, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            wav.writeframes(audio_bytes)

        # Reset to beginning
        wav_file.seek(0)
        wav_file.name = "audio.wav"  # Whisper API needs a filename

        return wav_file

    async def start_stream(self):
        """
        Start Whisper pseudo-stream.

        Whisper doesn't support true streaming, but we mark as streaming
        to indicate readiness to transcribe chunks.
        """
        self.is_streaming = True

        core_logging.log_event("whisper_stream_started", {
            "model": self.model
        })

    async def end_stream(self):
        """End Whisper pseudo-stream"""
        self.is_streaming = False

        core_logging.log_event("whisper_stream_ended")

    def supports_streaming(self) -> bool:
        """
        Whisper is batch-based, not true streaming.

        Returns:
            False (Whisper processes each chunk independently)
        """
        return False

    async def get_supported_languages(self) -> List[str]:
        """
        Get Whisper's supported languages.

        Whisper supports 99 languages with varying accuracy.

        Returns:
            List of ISO 639-1 language codes
        """
        # Whisper supports 99 languages
        # Full list: https://github.com/openai/whisper/blob/main/whisper/tokenizer.py
        return [
            "en",  # English
            "zh",  # Chinese
            "de",  # German
            "es",  # Spanish
            "ru",  # Russian
            "ko",  # Korean
            "fr",  # French
            "ja",  # Japanese
            "pt",  # Portuguese
            "tr",  # Turkish
            "pl",  # Polish
            "ca",  # Catalan
            "nl",  # Dutch
            "ar",  # Arabic
            "sv",  # Swedish
            "it",  # Italian
            "id",  # Indonesian
            "hi",  # Hindi
            "fi",  # Finnish
            "vi",  # Vietnamese
            "he",  # Hebrew
            "uk",  # Ukrainian
            "el",  # Greek
            "ms",  # Malay
            "cs",  # Czech
            "ro",  # Romanian
            "da",  # Danish
            "hu",  # Hungarian
            "ta",  # Tamil
            "no",  # Norwegian
            "th",  # Thai
            "ur",  # Urdu
            "hr",  # Croatian
            "bg",  # Bulgarian
            "lt",  # Lithuanian
            "la",  # Latin
            "mi",  # Maori
            "ml",  # Malayalam
            "cy",  # Welsh
            "sk",  # Slovak
            "te",  # Telugu
            "fa",  # Persian
            "lv",  # Latvian
            "bn",  # Bengali
            "sr",  # Serbian
            "az",  # Azerbaijani
            "sl",  # Slovenian
            "kn",  # Kannada
            "et",  # Estonian
            "mk",  # Macedonian
            "br",  # Breton
            "eu",  # Basque
            "is",  # Icelandic
            "hy",  # Armenian
            "ne",  # Nepali
            "mn",  # Mongolian
            "bs",  # Bosnian
            "kk",  # Kazakh
            "sq",  # Albanian
            "sw",  # Swahili
            "gl",  # Galician
            "mr",  # Marathi
            "pa",  # Punjabi
            "si",  # Sinhala
            "km",  # Khmer
            "sn",  # Shona
            "yo",  # Yoruba
            "so",  # Somali
            "af",  # Afrikaans
            "oc",  # Occitan
            "ka",  # Georgian
            "be",  # Belarusian
            "tg",  # Tajik
            "sd",  # Sindhi
            "gu",  # Gujarati
            "am",  # Amharic
            "yi",  # Yiddish
            "lo",  # Lao
            "uz",  # Uzbek
            "fo",  # Faroese
            "ht",  # Haitian Creole
            "ps",  # Pashto
            "tk",  # Turkmen
            "nn",  # Nynorsk
            "mt",  # Maltese
            "sa",  # Sanskrit
            "lb",  # Luxembourgish
            "my",  # Myanmar
            "bo",  # Tibetan
            "tl",  # Tagalog
            "mg",  # Malagasy
            "as",  # Assamese
            "tt",  # Tatar
            "haw",  # Hawaiian
            "ln",  # Lingala
            "ha",  # Hausa
            "ba",  # Bashkir
            "jw",  # Javanese
            "su",  # Sundanese
        ]

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "OpenAI Whisper"
