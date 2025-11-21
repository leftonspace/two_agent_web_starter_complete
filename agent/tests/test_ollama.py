"""
PHASE 9.1: Ollama Client Tests

Tests for Ollama integration including:
- Model management (list, pull, delete)
- Chat completions
- Streaming responses
- Error handling and retries
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.ollama_client import OllamaClient, OllamaModel, OllamaResponse


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx.AsyncClient."""
    with patch("llm.ollama_client.httpx.AsyncClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_ollama_client_initialization():
    """Test OllamaClient initialization."""
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.timeout == 180.0
    assert client.max_retries == 3
    await client.close()

    # Test custom URL
    client = OllamaClient(base_url="http://custom:11434")
    assert client.base_url == "http://custom:11434"
    await client.close()


@pytest.mark.asyncio
async def test_is_available_success(mock_httpx_client):
    """Test server availability check - success."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = OllamaClient()
    available = await client.is_available()

    assert available is True
    mock_httpx_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_is_available_failure(mock_httpx_client):
    """Test server availability check - failure."""
    mock_httpx_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

    client = OllamaClient()
    available = await client.is_available()

    assert available is False


@pytest.mark.asyncio
async def test_list_models(mock_httpx_client):
    """Test listing available models."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {
                "name": "llama3",
                "size": 4661224960,
                "modified_at": "2024-01-01T00:00:00Z",
                "digest": "abc123",
            },
            {
                "name": "mistral",
                "size": 4109865984,
                "modified_at": "2024-01-02T00:00:00Z",
                "digest": "def456",
            }
        ]
    }
    mock_httpx_client.get = AsyncMock(return_value=mock_response)

    client = OllamaClient()
    models = await client.list_models()

    assert len(models) == 2
    assert models[0].name == "llama3"
    assert models[1].name == "mistral"
    assert models[0].size == 4661224960


@pytest.mark.asyncio
async def test_chat_success(mock_httpx_client):
    """Test successful chat completion."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "model": "llama3",
        "response": "Python is a high-level programming language.",
        "done": True,
        "total_duration": 5000000000,  # 5 seconds in nanoseconds
        "load_duration": 1000000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 500000000,
        "eval_count": 20,
        "eval_duration": 3500000000,
    }
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    client = OllamaClient()
    response = await client.chat("What is Python?", model="llama3")

    assert response.model == "llama3"
    assert "Python" in response.response
    assert response.done is True
    assert response.eval_count == 20

    # Test calculated properties
    assert response.latency_seconds == 5.0
    assert response.tokens_per_second > 0


@pytest.mark.asyncio
async def test_chat_with_system_prompt(mock_httpx_client):
    """Test chat with system prompt."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "model": "llama3",
        "response": "Affirmative, Commander.",
        "done": True,
    }
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    client = OllamaClient()
    await client.chat(
        prompt="What is your status?",
        model="llama3",
        system="You are a helpful AI assistant in a sci-fi setting.",
    )

    # Verify system prompt was included in request
    call_args = mock_httpx_client.post.call_args
    request_data = call_args.kwargs["json"]
    assert "system" in request_data
    assert "sci-fi" in request_data["system"]


@pytest.mark.asyncio
async def test_chat_retry_logic(mock_httpx_client):
    """Test chat retry logic on failure."""
    # First two calls fail, third succeeds
    mock_httpx_client.post = AsyncMock(
        side_effect=[
            httpx.TimeoutException("Timeout 1"),
            httpx.TimeoutException("Timeout 2"),
            MagicMock(json=lambda: {"model": "llama3", "response": "Success", "done": True}),
        ]
    )

    client = OllamaClient(max_retries=3)

    # Should succeed on third attempt
    response = await client.chat("Test", model="llama3")
    assert response.response == "Success"
    assert mock_httpx_client.post.call_count == 3


@pytest.mark.asyncio
async def test_chat_all_retries_fail(mock_httpx_client):
    """Test chat when all retries fail."""
    mock_httpx_client.post = AsyncMock(
        side_effect=httpx.TimeoutException("Timeout")
    )

    client = OllamaClient(max_retries=3)

    # Should raise exception after all retries
    with pytest.raises(httpx.TimeoutException):
        await client.chat("Test", model="llama3")

    assert mock_httpx_client.post.call_count == 3


@pytest.mark.asyncio
async def test_chat_stream(mock_httpx_client):
    """Test streaming chat response."""
    # Mock streaming response
    mock_stream_response = AsyncMock()

    async def mock_aiter_lines():
        lines = [
            json.dumps({"response": "Hello", "done": False}),
            json.dumps({"response": " world", "done": False}),
            json.dumps({"response": "!", "done": True}),
        ]
        for line in lines:
            yield line

    mock_stream_response.aiter_lines = mock_aiter_lines
    mock_stream_response.raise_for_status = MagicMock()

    mock_stream_context = AsyncMock()
    mock_stream_context.__aenter__.return_value = mock_stream_response
    mock_stream_context.__aexit__.return_value = None

    mock_httpx_client.stream = MagicMock(return_value=mock_stream_context)

    client = OllamaClient()

    chunks = []
    async for chunk in client.chat_stream("Hello", model="llama3"):
        chunks.append(chunk)

    assert chunks == ["Hello", " world", "!"]


@pytest.mark.asyncio
async def test_embeddings(mock_httpx_client):
    """Test embeddings generation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    mock_httpx_client.post = AsyncMock(return_value=mock_response)

    client = OllamaClient()
    embeddings = await client.embeddings("test text", model="llama3")

    assert embeddings == [0.1, 0.2, 0.3, 0.4, 0.5]
    mock_httpx_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager usage."""
    async with OllamaClient() as client:
        assert client is not None
        assert isinstance(client, OllamaClient)


def test_ollama_model_from_dict():
    """Test OllamaModel creation from dict."""
    data = {
        "name": "llama3",
        "size": 4661224960,
        "modified_at": "2024-01-01T00:00:00Z",
        "digest": "abc123",
    }

    model = OllamaModel.from_dict(data)

    assert model.name == "llama3"
    assert model.size == 4661224960
    assert model.modified_at == "2024-01-01T00:00:00Z"
    assert model.digest == "abc123"


def test_ollama_response_properties():
    """Test OllamaResponse calculated properties."""
    response = OllamaResponse(
        model="llama3",
        response="Test response",
        done=True,
        total_duration=5000000000,  # 5 seconds
        eval_count=100,
        eval_duration=2000000000,  # 2 seconds
    )

    # Test latency
    assert response.latency_seconds == 5.0

    # Test tokens per second: 100 tokens / 2 seconds = 50 tok/s
    assert response.tokens_per_second == 50.0
