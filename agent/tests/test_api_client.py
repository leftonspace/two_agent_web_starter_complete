"""
Tests for API client and rate limiter.

PHASE 8.2: Tests for HTTP client with authentication, retry logic,
and rate limiting.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import httpx

from agent.actions.api_client import APIClient, AuthType
from agent.actions.rate_limiter import RateLimiter


# ══════════════════════════════════════════════════════════════════════
# Rate Limiter Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_rate_limiter_basic():
    """Test basic rate limiting"""
    limiter = RateLimiter(rate=10.0, capacity=10)

    # Should allow immediate acquisition
    await limiter.acquire()
    assert limiter.get_available_tokens() < 10


@pytest.mark.asyncio
async def test_rate_limiter_multiple_tokens():
    """Test acquiring multiple tokens"""
    limiter = RateLimiter(rate=10.0, capacity=10)

    # Acquire 5 tokens
    await limiter.acquire(tokens=5)
    remaining = limiter.get_available_tokens()

    assert remaining <= 5


@pytest.mark.asyncio
async def test_rate_limiter_try_acquire():
    """Test try_acquire without waiting"""
    limiter = RateLimiter(rate=10.0, capacity=10)

    # Should succeed
    success = await limiter.try_acquire()
    assert success is True

    # Exhaust tokens
    await limiter.acquire(tokens=9)

    # Should fail (no tokens left)
    success = await limiter.try_acquire()
    assert success is False


@pytest.mark.asyncio
async def test_rate_limiter_reset():
    """Test rate limiter reset"""
    limiter = RateLimiter(rate=10.0, capacity=10)

    # Consume tokens
    await limiter.acquire(tokens=8)
    assert limiter.get_available_tokens() < 10

    # Reset
    limiter.reset()
    assert limiter.get_available_tokens() == 10


# ══════════════════════════════════════════════════════════════════════
# API Client - Basic HTTP Methods Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_api_client_get():
    """Test GET request"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Test"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = await client.get("/users/1")

        assert result == {"id": 1, "name": "Test"}
        mock_request.assert_called_once()
        assert mock_request.call_args[0][0] == "GET"

    await client.close()


@pytest.mark.asyncio
async def test_api_client_post():
    """Test POST request"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 2, "name": "Created"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = await client.post("/users", json={"name": "New User"})

        assert result == {"id": 2, "name": "Created"}
        assert mock_request.call_args[0][0] == "POST"

    await client.close()


@pytest.mark.asyncio
async def test_api_client_put():
    """Test PUT request"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "name": "Updated"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = await client.put("/users/1", json={"name": "Updated"})

        assert result == {"id": 1, "name": "Updated"}
        assert mock_request.call_args[0][0] == "PUT"

    await client.close()


@pytest.mark.asyncio
async def test_api_client_patch():
    """Test PATCH request"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "email": "new@example.com"}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = await client.patch("/users/1", json={"email": "new@example.com"})

        assert result["email"] == "new@example.com"
        assert mock_request.call_args[0][0] == "PATCH"

    await client.close()


@pytest.mark.asyncio
async def test_api_client_delete():
    """Test DELETE request"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.json.side_effect = ValueError()  # No JSON body
        mock_response.text = ""
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = await client.delete("/users/1")

        assert "text" in result
        assert mock_request.call_args[0][0] == "DELETE"

    await client.close()


# ══════════════════════════════════════════════════════════════════════
# Authentication Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_api_key_auth():
    """Test API key authentication"""
    client = APIClient(
        base_url="https://api.example.com",
        auth_config={
            "type": "api_key",
            "key": "test-api-key-123",
            "header": "X-API-Key"
        }
    )

    assert "X-API-Key" in client._auth_headers
    assert client._auth_headers["X-API-Key"] == "test-api-key-123"

    await client.close()


@pytest.mark.asyncio
async def test_bearer_auth():
    """Test Bearer token authentication"""
    client = APIClient(
        base_url="https://api.example.com",
        auth_config={
            "type": "bearer",
            "token": "bearer-token-xyz"
        }
    )

    assert "Authorization" in client._auth_headers
    assert client._auth_headers["Authorization"] == "Bearer bearer-token-xyz"

    await client.close()


@pytest.mark.asyncio
async def test_basic_auth():
    """Test Basic authentication"""
    client = APIClient(
        base_url="https://api.example.com",
        auth_config={
            "type": "basic",
            "username": "user",
            "password": "pass"
        }
    )

    assert "Authorization" in client._auth_headers
    assert client._auth_headers["Authorization"].startswith("Basic ")

    await client.close()


@pytest.mark.asyncio
async def test_jwt_auth():
    """Test JWT authentication"""
    client = APIClient(
        base_url="https://api.example.com",
        auth_config={
            "type": "jwt",
            "token": "jwt-token-123"
        }
    )

    assert "Authorization" in client._auth_headers
    assert client._auth_headers["Authorization"] == "Bearer jwt-token-123"

    await client.close()


@pytest.mark.asyncio
async def test_oauth2_auth():
    """Test OAuth2 authentication"""
    client = APIClient(
        base_url="https://api.example.com",
        auth_config={
            "type": "oauth2",
            "access_token": "oauth-access-token"
        }
    )

    assert "Authorization" in client._auth_headers
    assert client._auth_headers["Authorization"] == "Bearer oauth-access-token"

    await client.close()


# ══════════════════════════════════════════════════════════════════════
# Retry Logic Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_retry_on_rate_limit():
    """Test retry on 429 rate limit"""
    client = APIClient(base_url="https://api.example.com", max_retries=3)

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        mock_response = Mock()
        if call_count < 3:
            # First 2 calls: rate limited
            mock_response.status_code = 429
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Rate limited",
                request=Mock(),
                response=mock_response
            )
        else:
            # 3rd call: success
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            mock_response.raise_for_status = Mock()

        return mock_response

    with patch.object(client.session, 'request', side_effect=mock_request):
        result = await client.get("/test")

        assert result == {"success": True}
        assert call_count == 3  # Should have retried twice

    await client.close()


@pytest.mark.asyncio
async def test_retry_on_503():
    """Test retry on 503 service unavailable"""
    client = APIClient(base_url="https://api.example.com", max_retries=2)

    call_count = 0

    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        mock_response = Mock()
        if call_count < 2:
            mock_response.status_code = 503
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Service unavailable",
                request=Mock(),
                response=mock_response
            )
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = {"recovered": True}
            mock_response.raise_for_status = Mock()

        return mock_response

    with patch.object(client.session, 'request', side_effect=mock_request):
        result = await client.get("/test")

        assert result == {"recovered": True}
        assert call_count == 2

    await client.close()


@pytest.mark.asyncio
async def test_no_retry_on_400():
    """Test no retry on 400 bad request"""
    client = APIClient(base_url="https://api.example.com", max_retries=3)

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request",
            request=Mock(),
            response=mock_response
        )
        mock_request.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await client.get("/test")

        # Should not retry on 400
        assert mock_request.call_count == 1

    await client.close()


# ══════════════════════════════════════════════════════════════════════
# Statistics Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_stats():
    """Test client statistics"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        # Make some requests
        await client.get("/test1")
        await client.get("/test2")

        stats = client.get_stats()

        assert stats["request_count"] == 2
        assert stats["error_count"] == 0
        assert stats["success_rate"] == 1.0

    await client.close()


# ══════════════════════════════════════════════════════════════════════
# Context Manager Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_context_manager():
    """Test async context manager"""
    async with APIClient(base_url="https://api.example.com") as client:
        assert client.session is not None

    # Session should be closed after context exit
    # (We can't easily test this without accessing internals)


# ══════════════════════════════════════════════════════════════════════
# Edge Cases Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_non_json_response():
    """Test handling of non-JSON response"""
    client = APIClient(base_url="https://api.example.com")

    with patch.object(client.session, 'request', new_callable=AsyncMock) as mock_request:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Plain text response"
        mock_response.raise_for_status = Mock()
        mock_request.return_value = mock_response

        result = await client.get("/test")

        assert result == {"text": "Plain text response"}

    await client.close()
