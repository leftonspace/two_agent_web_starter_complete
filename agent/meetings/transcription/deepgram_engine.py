"""
Deepgram transcription engine.

PHASE 7A.2: True real-time streaming with <100ms latency.
Best for live transcription during meetings where low latency is critical.

API: https://developers.deepgram.com/
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import agent.core_logging as core_logging
from agent.meetings.transcription.base import TranscriptionEngine, TranscriptSegment

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class DeepgramEngine(TranscriptionEngine):
    """
    Deepgram streaming transcription.

    Provides true real-time streaming with WebSocket connection.
    Yields interim and final results with very low latency (<100ms).

    Typical latency: 50-100ms per result.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "nova-2",
        language: str = "en",
        punctuate: bool = True,
        diarize: bool = True
    ):
        """
        Initialize Deepgram engine.

        Args:
            api_key: Deepgram API key
            model: Model name (nova-2, nova, base, enhanced)
            language: Language code (en, es, fr, etc.)
            punctuate: Add punctuation to transcripts
            diarize: Enable speaker diarization
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library not installed. Run: pip install websockets"
            )

        self.api_key = api_key
        self.model = model
        self.language = language
        self.punctuate = punctuate
        self.diarize = diarize

        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_streaming = False

        # Streaming state
        self._send_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None

    async def start_stream(self):
        """
        Open WebSocket connection to Deepgram.

        Establishes streaming connection for real-time transcription.
        """
        try:
            # Build WebSocket URL with parameters
            params = [
                f"model={self.model}",
                f"language={self.language}",
                f"punctuate={'true' if self.punctuate else 'false'}",
                f"diarize={'true' if self.diarize else 'false'}",
                "encoding=linear16",
                "sample_rate=16000",
                "channels=1"
            ]

            url = f"wss://api.deepgram.com/v1/listen?{'&'.join(params)}"

            # Connect with API key
            headers = {
                "Authorization": f"Token {self.api_key}"
            }

            core_logging.log_event("deepgram_connecting", {
                "model": self.model,
                "language": self.language
            })

            self.websocket = await websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=5,  # Keep connection alive
                ping_timeout=10
            )

            self.is_streaming = True

            core_logging.log_event("deepgram_stream_started", {
                "model": self.model,
                "language": self.language,
                "punctuate": self.punctuate,
                "diarize": self.diarize
            })

        except Exception as e:
            core_logging.log_event("deepgram_stream_start_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise

    async def transcribe_chunk(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000
    ) -> TranscriptSegment:
        """
        Send audio chunk and get transcription.

        For streaming, prefer using transcribe_stream() instead.
        This method is for single-chunk transcription.

        Args:
            audio_bytes: Raw PCM audio data
            sample_rate: Sample rate in Hz (must be 16000)

        Returns:
            TranscriptSegment with transcribed text
        """
        if not self.is_streaming:
            await self.start_stream()

        try:
            start_time = datetime.now()

            # Send audio to Deepgram
            await self.websocket.send(audio_bytes)

            # Receive response (may get multiple interim results)
            final_segment = None

            while True:
                response_json = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=2.0  # 2 second timeout
                )

                response = json.loads(response_json)

                if response.get("type") == "Results":
                    segment = self._parse_response(response, start_time)

                    if segment.is_final:
                        final_segment = segment
                        break
                    elif not final_segment:
                        # Save interim result in case we don't get final
                        final_segment = segment

                elif response.get("type") == "Metadata":
                    # Connection metadata (ignore)
                    pass

                elif response.get("type") == "Error":
                    error_msg = response.get("message", "Unknown error")
                    core_logging.log_event("deepgram_error_response", {
                        "error": error_msg
                    })
                    break

            return final_segment or TranscriptSegment(
                text="",
                confidence=0.0,
                start_time=start_time,
                end_time=datetime.now(),
                is_final=True
            )

        except asyncio.TimeoutError:
            core_logging.log_event("deepgram_transcription_timeout")

            return TranscriptSegment(
                text="",
                confidence=0.0,
                start_time=datetime.now(),
                end_time=datetime.now(),
                is_final=True
            )

        except Exception as e:
            core_logging.log_event("deepgram_transcription_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })

            return TranscriptSegment(
                text="",
                confidence=0.0,
                start_time=datetime.now(),
                end_time=datetime.now(),
                is_final=True
            )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptSegment]:
        """
        Stream audio and get continuous transcription.

        Yields interim and final results as they arrive.
        This is the recommended way to use Deepgram for real-time.

        Args:
            audio_stream: Iterator of audio chunks

        Yields:
            TranscriptSegment objects (interim and final)
        """
        if not self.is_streaming:
            await self.start_stream()

        # Create tasks for sending and receiving
        send_queue = asyncio.Queue()

        async def send_audio():
            """Send audio chunks to Deepgram"""
            try:
                async for audio_chunk in audio_stream:
                    if self.websocket and self.is_streaming:
                        await self.websocket.send(audio_chunk)
                    else:
                        break

                # Send close message
                if self.websocket:
                    close_msg = json.dumps({"type": "CloseStream"})
                    await self.websocket.send(close_msg)

            except Exception as e:
                core_logging.log_event("deepgram_send_audio_failed", {
                    "error": str(e)
                })

        async def receive_transcripts():
            """Receive transcription results from Deepgram"""
            try:
                while self.is_streaming and self.websocket:
                    response_json = await self.websocket.recv()
                    response = json.loads(response_json)

                    if response.get("type") == "Results":
                        segment = self._parse_response(response, datetime.now())

                        if segment.text:  # Only yield non-empty
                            yield segment

                    elif response.get("type") == "Metadata":
                        # Connection metadata
                        core_logging.log_event("deepgram_metadata", {
                            "request_id": response.get("request_id")
                        })

                    elif response.get("type") == "Error":
                        error_msg = response.get("message", "Unknown error")
                        core_logging.log_event("deepgram_error_response", {
                            "error": error_msg
                        })

            except websockets.exceptions.ConnectionClosed:
                core_logging.log_event("deepgram_connection_closed")
            except Exception as e:
                core_logging.log_event("deepgram_receive_failed", {
                    "error": str(e)
                })

        # Run send and receive concurrently
        send_task = asyncio.create_task(send_audio())

        async for segment in receive_transcripts():
            yield segment

        # Wait for send task to complete
        await send_task

    def _parse_response(
        self,
        response: Dict[str, Any],
        start_time: datetime
    ) -> TranscriptSegment:
        """
        Parse Deepgram response into TranscriptSegment.

        Args:
            response: JSON response from Deepgram
            start_time: When audio was sent

        Returns:
            TranscriptSegment
        """
        try:
            channel = response["channel"]["alternatives"][0]

            text = channel["transcript"]
            confidence = channel["confidence"]
            is_final = response.get("is_final", False)

            # Speaker diarization (if enabled)
            speaker_id = None
            if "words" in channel and len(channel["words"]) > 0:
                # Use speaker from first word
                speaker_id = channel["words"][0].get("speaker")

            segment = TranscriptSegment(
                text=text,
                confidence=confidence,
                start_time=start_time,
                end_time=datetime.now(),
                speaker_id=str(speaker_id) if speaker_id is not None else None,
                language=self.language,
                is_final=is_final
            )

            if text:  # Log non-empty transcripts
                core_logging.log_event("deepgram_transcript_received", {
                    "text_length": len(text),
                    "text_preview": text[:50],
                    "confidence": confidence,
                    "is_final": is_final,
                    "speaker_id": speaker_id
                })

            return segment

        except (KeyError, IndexError) as e:
            core_logging.log_event("deepgram_parse_error", {
                "error": str(e),
                "response": response
            })

            return TranscriptSegment(
                text="",
                confidence=0.0,
                start_time=start_time,
                end_time=datetime.now(),
                is_final=False
            )

    async def end_stream(self):
        """Close Deepgram WebSocket connection"""
        try:
            self.is_streaming = False

            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            core_logging.log_event("deepgram_stream_ended")

        except Exception as e:
            core_logging.log_event("deepgram_stream_end_failed", {
                "error": str(e)
            })

    def supports_streaming(self) -> bool:
        """
        Deepgram supports true streaming.

        Returns:
            True (Deepgram is a streaming transcription service)
        """
        return True

    async def get_supported_languages(self) -> List[str]:
        """
        Get Deepgram's supported languages.

        Deepgram supports 36+ languages.

        Returns:
            List of ISO 639-1 language codes
        """
        # Deepgram supports 36+ languages
        # Full list: https://developers.deepgram.com/docs/models-languages
        return [
            "en",  # English
            "en-US",  # English (US)
            "en-GB",  # English (UK)
            "en-AU",  # English (Australia)
            "en-NZ",  # English (New Zealand)
            "en-IN",  # English (India)
            "zh",  # Chinese
            "zh-CN",  # Chinese (Simplified)
            "zh-TW",  # Chinese (Traditional)
            "nl",  # Dutch
            "fr",  # French
            "fr-CA",  # French (Canadian)
            "de",  # German
            "hi",  # Hindi
            "hi-Latn",  # Hindi (Latin script)
            "id",  # Indonesian
            "it",  # Italian
            "ja",  # Japanese
            "ko",  # Korean
            "pt",  # Portuguese
            "pt-BR",  # Portuguese (Brazilian)
            "ru",  # Russian
            "es",  # Spanish
            "es-419",  # Spanish (Latin America)
            "sv",  # Swedish
            "tr",  # Turkish
            "uk",  # Ukrainian
        ]

    def get_provider_name(self) -> str:
        """Get provider name"""
        return "Deepgram"
