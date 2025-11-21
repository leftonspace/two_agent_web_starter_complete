"""
PHASE 7A.2: Tests for real-time speech transcription.

Tests the transcription engine abstraction, Whisper implementation,
Deepgram implementation, and failover manager.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from agent.meetings.transcription.base import (
    TranscriptSegment,
    TranscriptionEngine,
    TranscriptionProvider,
)
from agent.meetings.transcription.manager import TranscriptionManager


# ══════════════════════════════════════════════════════════════════════
# Test Data Models
# ══════════════════════════════════════════════════════════════════════


def test_transcript_segment_creation():
    """Test TranscriptSegment dataclass creation"""
    start = datetime.now()
    end = datetime.now()

    segment = TranscriptSegment(
        text="Hello world",
        confidence=0.95,
        start_time=start,
        end_time=end,
        speaker_id="speaker_1",
        language="en",
        is_final=True
    )

    assert segment.text == "Hello world"
    assert segment.confidence == 0.95
    assert segment.speaker_id == "speaker_1"
    assert segment.language == "en"
    assert segment.is_final is True


def test_transcript_segment_duration():
    """Test TranscriptSegment duration calculation"""
    import time

    start = datetime.now()
    time.sleep(0.1)  # 100ms
    end = datetime.now()

    segment = TranscriptSegment(
        text="Test",
        confidence=0.9,
        start_time=start,
        end_time=end
    )

    # Should be approximately 100ms
    assert 90 <= segment.duration_ms <= 150


def test_transcript_segment_to_dict():
    """Test TranscriptSegment serialization"""
    start = datetime.now()
    end = datetime.now()

    segment = TranscriptSegment(
        text="Test",
        confidence=0.8,
        start_time=start,
        end_time=end,
        speaker_id="speaker_2"
    )

    data = segment.to_dict()

    assert data["text"] == "Test"
    assert data["confidence"] == 0.8
    assert data["speaker_id"] == "speaker_2"
    assert isinstance(data["start_time"], str)  # ISO format
    assert isinstance(data["duration_ms"], float)


# ══════════════════════════════════════════════════════════════════════
# Test Whisper Engine
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_whisper_engine_initialization():
    """Test WhisperEngine can be initialized"""
    try:
        from agent.meetings.transcription.whisper_engine import WhisperEngine

        engine = WhisperEngine(api_key="test_key")

        assert engine.api_key == "test_key"
        assert engine.model == "whisper-1"
        assert not engine.is_streaming
        assert not engine.supports_streaming()

    except ImportError:
        pytest.skip("OpenAI library not installed")


@pytest.mark.asyncio
async def test_whisper_transcription():
    """Test Whisper transcribes audio correctly"""
    try:
        from agent.meetings.transcription.whisper_engine import WhisperEngine

        engine = WhisperEngine(api_key="test_key")

        # Mock OpenAI API response
        mock_response = Mock()
        mock_response.text = "Hello world"
        mock_response.language = "en"
        mock_response.no_speech_prob = 0.1

        with patch.object(
            engine.client.audio.transcriptions,
            'create',
            return_value=mock_response
        ):
            audio_bytes = b'\x00' * 32000  # 1 second at 16kHz
            segment = await engine.transcribe_chunk(audio_bytes)

            assert segment.text == "Hello world"
            assert segment.language == "en"
            assert segment.confidence == 0.9  # 1.0 - 0.1
            assert segment.is_final is True

    except ImportError:
        pytest.skip("OpenAI library not installed")


@pytest.mark.asyncio
async def test_whisper_error_handling():
    """Test Whisper handles API errors gracefully"""
    try:
        from agent.meetings.transcription.whisper_engine import WhisperEngine

        engine = WhisperEngine(api_key="test_key")

        # Mock API to raise exception
        with patch.object(
            engine.client.audio.transcriptions,
            'create',
            side_effect=Exception("API error")
        ):
            audio_bytes = b'\x00' * 32000
            segment = await engine.transcribe_chunk(audio_bytes)

            # Should return empty segment on error
            assert segment.text == ""
            assert segment.confidence == 0.0
            assert segment.is_final is True

    except ImportError:
        pytest.skip("OpenAI library not installed")


@pytest.mark.asyncio
async def test_whisper_supported_languages():
    """Test Whisper reports supported languages"""
    try:
        from agent.meetings.transcription.whisper_engine import WhisperEngine

        engine = WhisperEngine(api_key="test_key")

        languages = await engine.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) >= 50  # Whisper supports 99 languages
        assert "en" in languages
        assert "es" in languages
        assert "fr" in languages

    except ImportError:
        pytest.skip("OpenAI library not installed")


# ══════════════════════════════════════════════════════════════════════
# Test Deepgram Engine
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_deepgram_engine_initialization():
    """Test DeepgramEngine can be initialized"""
    try:
        from agent.meetings.transcription.deepgram_engine import DeepgramEngine

        engine = DeepgramEngine(
            api_key="test_key",
            model="nova-2",
            language="en"
        )

        assert engine.api_key == "test_key"
        assert engine.model == "nova-2"
        assert engine.language == "en"
        assert not engine.is_streaming
        assert engine.supports_streaming()  # Deepgram supports streaming

    except ImportError:
        pytest.skip("websockets library not installed")


@pytest.mark.asyncio
async def test_deepgram_streaming_transcription():
    """Test Deepgram streaming transcription"""
    try:
        from agent.meetings.transcription.deepgram_engine import DeepgramEngine

        engine = DeepgramEngine(api_key="test_key")

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(return_value='''
        {
            "type": "Results",
            "is_final": true,
            "channel": {
                "alternatives": [{
                    "transcript": "Test transcription",
                    "confidence": 0.95
                }]
            }
        }
        ''')

        with patch('websockets.connect', return_value=mock_ws):
            await engine.start_stream()

            assert engine.is_streaming
            assert engine.websocket == mock_ws

            audio_bytes = b'\x00' * 32000
            segment = await engine.transcribe_chunk(audio_bytes)

            assert segment.text == "Test transcription"
            assert segment.confidence == 0.95
            assert segment.is_final is True

            await engine.end_stream()
            assert not engine.is_streaming

    except ImportError:
        pytest.skip("websockets library not installed")


@pytest.mark.asyncio
async def test_deepgram_error_response():
    """Test Deepgram handles error responses"""
    try:
        from agent.meetings.transcription.deepgram_engine import DeepgramEngine

        engine = DeepgramEngine(api_key="test_key")

        # Mock WebSocket with error response
        mock_ws = AsyncMock()
        mock_ws.recv = AsyncMock(return_value='''
        {
            "type": "Error",
            "message": "Invalid audio format"
        }
        ''')

        with patch('websockets.connect', return_value=mock_ws):
            await engine.start_stream()

            audio_bytes = b'\x00' * 32000
            segment = await engine.transcribe_chunk(audio_bytes)

            # Should return empty segment on error
            assert segment.text == ""
            assert segment.confidence == 0.0

    except ImportError:
        pytest.skip("websockets library not installed")


@pytest.mark.asyncio
async def test_deepgram_supported_languages():
    """Test Deepgram reports supported languages"""
    try:
        from agent.meetings.transcription.deepgram_engine import DeepgramEngine

        engine = DeepgramEngine(api_key="test_key")

        languages = await engine.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) >= 20  # Deepgram supports 36+ languages
        assert "en" in languages
        assert "es" in languages
        assert "fr" in languages

    except ImportError:
        pytest.skip("websockets library not installed")


# ══════════════════════════════════════════════════════════════════════
# Test Transcription Manager
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_manager_initialization():
    """Test TranscriptionManager initializes correctly"""
    manager = TranscriptionManager(
        primary_provider=TranscriptionProvider.DEEPGRAM,
        fallback_providers=[TranscriptionProvider.WHISPER]
    )

    assert manager.primary_provider == TranscriptionProvider.DEEPGRAM
    assert manager.fallback_providers == [TranscriptionProvider.WHISPER]
    assert manager.active_engine is None


@pytest.mark.asyncio
async def test_manager_failover():
    """Test manager fails over to backup provider"""
    manager = TranscriptionManager(
        primary_provider=TranscriptionProvider.DEEPGRAM,
        fallback_providers=[TranscriptionProvider.WHISPER]
    )

    # Mock primary to fail
    deepgram_engine = Mock(spec=TranscriptionEngine)
    deepgram_engine.transcribe_chunk = AsyncMock(
        side_effect=Exception("Primary failed")
    )
    deepgram_engine.start_stream = AsyncMock()
    manager.engines[TranscriptionProvider.DEEPGRAM] = deepgram_engine

    # Mock fallback to succeed
    whisper_engine = Mock(spec=TranscriptionEngine)
    whisper_segment = TranscriptSegment(
        text="Fallback success",
        confidence=0.9,
        start_time=datetime.now(),
        end_time=datetime.now(),
        is_final=True
    )
    whisper_engine.transcribe_chunk = AsyncMock(return_value=whisper_segment)
    whisper_engine.start_stream = AsyncMock()
    whisper_engine.end_stream = AsyncMock()
    manager.engines[TranscriptionProvider.WHISPER] = whisper_engine

    # Should use fallback
    audio = b'\x00' * 32000
    segment = await manager.transcribe_chunk(audio)

    assert segment.text == "Fallback success"
    assert manager.get_active_provider() == TranscriptionProvider.WHISPER


@pytest.mark.asyncio
async def test_manager_no_providers():
    """Test manager raises error when no providers available"""
    manager = TranscriptionManager(
        primary_provider=TranscriptionProvider.DEEPGRAM,
        fallback_providers=[]
    )

    # No engines configured
    manager.engines = {}

    with pytest.raises(Exception, match="No transcription providers available"):
        await manager._init_active_engine()


@pytest.mark.asyncio
async def test_manager_stop_transcription():
    """Test manager stops transcription cleanly"""
    manager = TranscriptionManager()

    # Mock active engine
    mock_engine = Mock(spec=TranscriptionEngine)
    mock_engine.end_stream = AsyncMock()

    manager.active_engine = mock_engine
    manager.active_provider = TranscriptionProvider.DEEPGRAM

    await manager.stop_transcription()

    # Should call end_stream
    mock_engine.end_stream.assert_called_once()

    # Should clear active state
    assert manager.active_engine is None
    assert manager.active_provider is None


@pytest.mark.asyncio
async def test_manager_is_active():
    """Test manager reports active state correctly"""
    manager = TranscriptionManager()

    # Initially not active
    assert not manager.is_active()

    # Set active
    manager.active_engine = Mock()
    manager.active_provider = TranscriptionProvider.WHISPER

    assert manager.is_active()

    # Clear active
    manager.active_engine = None
    manager.active_provider = None

    assert not manager.is_active()


@pytest.mark.asyncio
async def test_manager_get_available_providers():
    """Test manager returns available providers"""
    manager = TranscriptionManager()

    # Mock some engines as available
    manager.engines = {
        TranscriptionProvider.DEEPGRAM: Mock(),
        TranscriptionProvider.WHISPER: Mock(),
    }

    providers = manager.get_available_providers()

    assert len(providers) == 2
    assert TranscriptionProvider.DEEPGRAM in providers
    assert TranscriptionProvider.WHISPER in providers


# ══════════════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_transcription_provider_enum():
    """Test TranscriptionProvider enum values"""
    assert TranscriptionProvider.WHISPER.value == "whisper"
    assert TranscriptionProvider.DEEPGRAM.value == "deepgram"
    assert TranscriptionProvider.GOOGLE.value == "google"
    assert TranscriptionProvider.AZURE.value == "azure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
