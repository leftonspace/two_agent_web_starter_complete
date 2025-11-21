"""
Transcription manager with multi-provider support and failover.

PHASE 7A.2: Automatically falls back to alternative providers if primary fails.
Provides high reliability for critical meeting transcription.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional

import agent.core_logging as core_logging
from agent.meetings.transcription.base import (
    TranscriptionEngine,
    TranscriptSegment,
    TranscriptionProvider,
)


class TranscriptionManager:
    """
    Manages transcription with automatic failover.

    Tries providers in order: Primary → Fallback1 → Fallback2 → ...
    Switches to a working provider and stays with it until it fails.

    Example:
        manager = TranscriptionManager(
            primary_provider=TranscriptionProvider.DEEPGRAM,
            fallback_providers=[TranscriptionProvider.WHISPER]
        )

        async for segment in manager.start_transcription(audio_stream):
            print(f"[{segment.confidence:.2f}] {segment.text}")
    """

    def __init__(
        self,
        primary_provider: TranscriptionProvider = TranscriptionProvider.DEEPGRAM,
        fallback_providers: Optional[List[TranscriptionProvider]] = None
    ):
        """
        Initialize transcription manager.

        Args:
            primary_provider: Preferred transcription provider
            fallback_providers: List of backup providers (in order)
        """
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or [
            TranscriptionProvider.WHISPER
        ]

        # Initialize engines
        self.engines: Dict[TranscriptionProvider, TranscriptionEngine] = {}
        self._init_engines()

        # Current active engine
        self.active_engine: Optional[TranscriptionEngine] = None
        self.active_provider: Optional[TranscriptionProvider] = None

    def _init_engines(self):
        """Initialize all configured transcription engines"""
        # Import engines here to avoid circular imports
        from agent.meetings.transcription.whisper_engine import WhisperEngine
        from agent.meetings.transcription.deepgram_engine import DeepgramEngine

        # Deepgram (streaming)
        deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        if deepgram_key:
            try:
                self.engines[TranscriptionProvider.DEEPGRAM] = DeepgramEngine(
                    api_key=deepgram_key,
                    model="nova-2",
                    language="en",
                    punctuate=True,
                    diarize=True
                )
                core_logging.log_event("deepgram_engine_initialized")
            except ImportError as e:
                core_logging.log_event("deepgram_engine_init_failed", {
                    "error": str(e)
                })

        # OpenAI Whisper (batch)
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                self.engines[TranscriptionProvider.WHISPER] = WhisperEngine(
                    api_key=openai_key,
                    model="whisper-1"
                )
                core_logging.log_event("whisper_engine_initialized")
            except ImportError as e:
                core_logging.log_event("whisper_engine_init_failed", {
                    "error": str(e)
                })

        # Log available engines
        available = list(self.engines.keys())
        core_logging.log_event("transcription_engines_initialized", {
            "available_providers": [p.value for p in available],
            "count": len(available)
        })

    async def start_transcription(
        self,
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[TranscriptSegment]:
        """
        Start transcribing audio stream with automatic failover.

        Args:
            audio_stream: Iterator of audio chunks (PCM 16-bit, 16kHz, mono)

        Yields:
            TranscriptSegment objects as transcription completes

        Raises:
            Exception: If all providers fail

        Example:
            async for segment in manager.start_transcription(audio):
                if segment.is_final:
                    print(f"Final: {segment.text}")
                else:
                    print(f"Interim: {segment.text}")
        """
        # Try providers in order
        providers_to_try = [self.primary_provider] + self.fallback_providers

        for provider in providers_to_try:
            engine = self.engines.get(provider)

            if not engine:
                core_logging.log_event("transcription_provider_unavailable", {
                    "provider": provider.value,
                    "reason": "Not configured or API key missing"
                })
                continue

            try:
                self.active_engine = engine
                self.active_provider = provider

                core_logging.log_event("transcription_started", {
                    "provider": provider.value,
                    "streaming": engine.supports_streaming()
                })

                # Use streaming or chunk-based depending on engine
                if engine.supports_streaming():
                    # Streaming transcription (Deepgram, Google)
                    core_logging.log_event("using_streaming_transcription", {
                        "provider": provider.value
                    })

                    async for segment in engine.transcribe_stream(audio_stream):
                        yield segment

                else:
                    # Chunk-based transcription (Whisper)
                    core_logging.log_event("using_chunk_transcription", {
                        "provider": provider.value
                    })

                    await engine.start_stream()

                    try:
                        async for audio_chunk in audio_stream:
                            segment = await engine.transcribe_chunk(audio_chunk)

                            if segment.text:  # Only yield non-empty
                                yield segment

                    finally:
                        await engine.end_stream()

                # Success - no need to try fallbacks
                core_logging.log_event("transcription_completed", {
                    "provider": provider.value
                })
                break

            except Exception as e:
                core_logging.log_event("transcription_provider_failed", {
                    "provider": provider.value,
                    "error": str(e),
                    "error_type": type(e).__name__
                })

                # Try next provider
                self.active_engine = None
                self.active_provider = None
                continue

        # All providers failed
        if self.active_engine is None:
            error_msg = "All transcription providers failed"
            core_logging.log_event("transcription_all_providers_failed", {
                "tried_providers": [p.value for p in providers_to_try]
            })
            raise Exception(error_msg)

    async def transcribe_chunk(
        self,
        audio_bytes: bytes,
        sample_rate: int = 16000
    ) -> TranscriptSegment:
        """
        Transcribe single audio chunk.

        Uses active engine or initializes primary provider.
        Automatically fails over if transcription fails.

        Args:
            audio_bytes: Raw PCM audio data
            sample_rate: Sample rate in Hz (default 16kHz)

        Returns:
            TranscriptSegment with transcribed text

        Example:
            audio = b'\\x00' * 32000  # 1 second at 16kHz
            segment = await manager.transcribe_chunk(audio)
            print(segment.text)
        """
        # Initialize active engine if needed
        if not self.active_engine:
            await self._init_active_engine()

        try:
            return await self.active_engine.transcribe_chunk(
                audio_bytes,
                sample_rate
            )

        except Exception as e:
            core_logging.log_event("transcription_chunk_failed", {
                "provider": self.active_provider.value if self.active_provider else None,
                "error": str(e),
                "error_type": type(e).__name__
            })

            # Try failover
            return await self._failover_transcribe_chunk(audio_bytes, sample_rate)

    async def _init_active_engine(self):
        """Initialize primary provider as active engine"""
        self.active_provider = self.primary_provider
        self.active_engine = self.engines.get(self.primary_provider)

        if not self.active_engine:
            # Primary not available, try fallbacks
            for provider in self.fallback_providers:
                engine = self.engines.get(provider)
                if engine:
                    self.active_provider = provider
                    self.active_engine = engine
                    break

        if not self.active_engine:
            raise Exception("No transcription providers available")

        await self.active_engine.start_stream()

        core_logging.log_event("active_transcription_engine_initialized", {
            "provider": self.active_provider.value
        })

    async def _failover_transcribe_chunk(
        self,
        audio_bytes: bytes,
        sample_rate: int
    ) -> TranscriptSegment:
        """
        Try fallback providers for chunk transcription.

        Args:
            audio_bytes: Raw PCM audio data
            sample_rate: Sample rate in Hz

        Returns:
            TranscriptSegment (empty if all fail)
        """
        for provider in self.fallback_providers:
            if provider == self.active_provider:
                # Skip current (failed) provider
                continue

            engine = self.engines.get(provider)

            if not engine:
                continue

            try:
                core_logging.log_event("attempting_transcription_failover", {
                    "from_provider": self.active_provider.value if self.active_provider else None,
                    "to_provider": provider.value
                })

                await engine.start_stream()
                segment = await engine.transcribe_chunk(audio_bytes, sample_rate)

                # Success - switch to this provider
                if self.active_engine:
                    await self.active_engine.end_stream()

                self.active_engine = engine
                self.active_provider = provider

                core_logging.log_event("transcription_failover_success", {
                    "new_provider": provider.value
                })

                return segment

            except Exception as e:
                core_logging.log_event("transcription_failover_attempt_failed", {
                    "provider": provider.value,
                    "error": str(e)
                })
                continue

        # All failed - return empty segment
        core_logging.log_event("transcription_failover_exhausted")

        return TranscriptSegment(
            text="",
            confidence=0.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            is_final=True
        )

    async def stop_transcription(self):
        """
        Stop active transcription and clean up resources.

        Example:
            await manager.stop_transcription()
        """
        if self.active_engine:
            try:
                await self.active_engine.end_stream()
                core_logging.log_event("transcription_stopped", {
                    "provider": self.active_provider.value if self.active_provider else None
                })
            except Exception as e:
                core_logging.log_event("transcription_stop_failed", {
                    "error": str(e)
                })

            self.active_engine = None
            self.active_provider = None

    def get_active_provider(self) -> Optional[TranscriptionProvider]:
        """
        Get currently active transcription provider.

        Returns:
            TranscriptionProvider or None if no active provider

        Example:
            provider = manager.get_active_provider()
            if provider == TranscriptionProvider.DEEPGRAM:
                print("Using Deepgram (streaming)")
        """
        return self.active_provider

    def is_active(self) -> bool:
        """
        Check if transcription is currently active.

        Returns:
            True if actively transcribing, False otherwise
        """
        return self.active_engine is not None and self.active_provider is not None

    def get_available_providers(self) -> List[TranscriptionProvider]:
        """
        Get list of available (configured) providers.

        Returns:
            List of providers with valid API keys

        Example:
            providers = manager.get_available_providers()
            print(f"Available: {[p.value for p in providers]}")
        """
        return list(self.engines.keys())
