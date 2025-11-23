"""
Universal API client with authentication and retry logic.

PHASE 8.2: Robust HTTP client for external API integration with auth,
rate limiting, and exponential backoff retry.

Features connection pooling for improved performance:
- Shared connection pool reduces connection overhead
- Configurable connection limits prevent resource exhaustion
- Keep-alive connections for repeated requests to same host
"""

import asyncio
import httpx
from typing import Dict, Any, Optional, Union, List
from enum import Enum
from datetime import datetime
import base64
import threading

from agent.actions.rate_limiter import RateLimiter
from agent.core_logging import log_event


# Global shared HTTP client pool for connection reuse
_shared_client: Optional[httpx.AsyncClient] = None
_shared_client_lock = threading.Lock()


def get_shared_http_client(timeout: float = 60.0) -> httpx.AsyncClient:
    """
    Get or create a shared HTTP client with connection pooling.

    Uses httpx's built-in connection pooling with configured limits.
    Sharing a client across multiple APIClient instances reduces
    connection overhead and improves performance.

    Args:
        timeout: Default request timeout

    Returns:
        Shared AsyncClient instance
    """
    global _shared_client

    if _shared_client is None:
        with _shared_client_lock:
            if _shared_client is None:
                # Configure connection limits for pooling
                limits = httpx.Limits(
                    max_keepalive_connections=20,  # Max idle connections
                    max_connections=100,  # Max total connections
                    keepalive_expiry=30.0,  # Keep connections alive for 30s
                )
                _shared_client = httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=True,
                    limits=limits,
                )

    return _shared_client


async def close_shared_http_client():
    """Close the shared HTTP client (call on application shutdown)."""
    global _shared_client

    if _shared_client is not None:
        with _shared_client_lock:
            if _shared_client is not None:
                await _shared_client.aclose()
                _shared_client = None


class AuthType(Enum):
    """Authentication types"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"
    JWT = "jwt"


class APIClient:
    """
    Universal API client with authentication, retry, and rate limiting.

    Features:
    - Multiple auth methods (API key, OAuth, JWT, Basic)
    - Exponential backoff retry
    - Rate limiting
    - All HTTP methods (GET, POST, PUT, PATCH, DELETE)
    - Automatic JSON handling
    - Request/response logging

    Example:
        # API Key authentication
        client = APIClient(
            base_url="https://api.example.com",
            auth_config={
                "type": "api_key",
                "key": "your-api-key",
                "header": "X-API-Key"
            }
        )

        # Make request
        result = await client.get("/users/123")

        # POST with data
        result = await client.post("/users", data={"name": "John"})
    """

    def __init__(
        self,
        base_url: str,
        auth_config: Optional[Dict[str, Any]] = None,
        rate_limit: float = 10.0,
        max_retries: int = 3,
        timeout: float = 30.0,
        use_shared_pool: bool = True
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (e.g., "https://api.example.com")
            auth_config: Authentication configuration dict
            rate_limit: Requests per second (default 10)
            max_retries: Maximum retry attempts (default 3)
            timeout: Request timeout in seconds (default 30)
            use_shared_pool: Use shared connection pool (default True, recommended)
        """
        self.base_url = base_url.rstrip("/")
        self.auth_config = auth_config or {"type": "none"}
        self.max_retries = max_retries
        self.timeout = timeout
        self.use_shared_pool = use_shared_pool

        # Setup HTTP client - use shared pool for connection reuse
        if use_shared_pool:
            self.session = get_shared_http_client(timeout)
            self._owns_session = False  # Don't close shared client
        else:
            # Create dedicated client with connection pooling
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=20,
            )
            self.session = httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=True,
                limits=limits,
            )
            self._owns_session = True

        # Setup rate limiter
        self.rate_limiter = RateLimiter(rate=rate_limit)

        # Setup authentication
        self.auth_type = AuthType(self.auth_config.get("type", "none"))
        self._auth_headers = self._setup_auth()

        # Request counter
        self.request_count = 0
        self.error_count = 0

    def _setup_auth(self) -> Dict[str, str]:
        """Setup authentication headers based on config"""
        headers = {}

        if self.auth_type == AuthType.API_KEY:
            # API Key in header
            key = self.auth_config.get("key")
            header_name = self.auth_config.get("header", "X-API-Key")
            if key:
                headers[header_name] = key

        elif self.auth_type == AuthType.BEARER:
            # Bearer token
            token = self.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif self.auth_type == AuthType.JWT:
            # JWT token (same as bearer)
            token = self.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif self.auth_type == AuthType.BASIC:
            # Basic authentication
            username = self.auth_config.get("username")
            password = self.auth_config.get("password")
            if username and password:
                credentials = f"{username}:{password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"

        elif self.auth_type == AuthType.OAUTH2:
            # OAuth 2.0 access token
            access_token = self.auth_config.get("access_token")
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

        return headers

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send GET request.

        Args:
            endpoint: API endpoint (e.g., "/users/123")
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional httpx request arguments

        Returns:
            Response data as dict
        """
        return await self._request(
            "GET",
            endpoint,
            params=params,
            headers=headers,
            **kwargs
        )

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send POST request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data (preferred)
            headers: Additional headers
            **kwargs: Additional httpx request arguments

        Returns:
            Response data as dict
        """
        return await self._request(
            "POST",
            endpoint,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send PUT request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data (preferred)
            headers: Additional headers
            **kwargs: Additional httpx request arguments

        Returns:
            Response data as dict
        """
        return await self._request(
            "PUT",
            endpoint,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )

    async def patch(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send PATCH request.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data (preferred)
            headers: Additional headers
            **kwargs: Additional httpx request arguments

        Returns:
            Response data as dict
        """
        return await self._request(
            "PATCH",
            endpoint,
            data=data,
            json=json,
            headers=headers,
            **kwargs
        )

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send DELETE request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            **kwargs: Additional httpx request arguments

        Returns:
            Response data as dict
        """
        return await self._request(
            "DELETE",
            endpoint,
            params=params,
            headers=headers,
            **kwargs
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with retry and rate limiting.

        Implements exponential backoff for retryable errors.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request arguments

        Returns:
            Response data as dict

        Raises:
            httpx.HTTPStatusError: For non-retryable errors
        """
        # Build full URL
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Merge headers
        headers = {**self._auth_headers}
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
        kwargs["headers"] = headers

        # Retry loop with exponential backoff
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                await self.rate_limiter.acquire()

                # Make request
                start_time = datetime.now()

                response = await self.session.request(
                    method,
                    url,
                    **kwargs
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                # Log successful request
                self.request_count += 1
                log_event("api_request_success", {
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "execution_time": execution_time,
                    "attempt": attempt + 1
                })

                # Check for HTTP errors
                response.raise_for_status()

                # Parse response
                try:
                    result = response.json()
                except (ValueError, TypeError):
                    # Not JSON, return text
                    result = {"text": response.text}

                return result

            except httpx.HTTPStatusError as e:
                # HTTP error occurred
                status_code = e.response.status_code
                self.error_count += 1

                log_event("api_request_http_error", {
                    "method": method,
                    "url": url,
                    "status_code": status_code,
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries
                })

                # Retry on specific status codes
                if status_code in [429, 503, 504] and attempt < self.max_retries - 1:
                    # Rate limited or service unavailable - retry with backoff
                    wait_time = 2 ** attempt  # Exponential: 1s, 2s, 4s
                    log_event("api_request_retry", {
                        "wait_time": wait_time,
                        "attempt": attempt + 1
                    })
                    await asyncio.sleep(wait_time)
                    continue

                # Don't retry other errors
                raise

            except httpx.RequestError as e:
                # Network/connection error
                self.error_count += 1
                last_exception = e

                log_event("api_request_network_error", {
                    "method": method,
                    "url": url,
                    "error": str(e),
                    "attempt": attempt + 1
                })

                # Retry network errors
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue

                raise

        # All retries exhausted
        if last_exception:
            raise last_exception

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / self.request_count
                if self.request_count > 0 else 0
            )
        }

    async def close(self):
        """Close HTTP session (only if client owns it, not shared pool)"""
        if self._owns_session:
            await self.session.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
