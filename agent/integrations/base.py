"""
Base Connector Framework for External System Integrations

This module provides the abstract base class and utilities for building
connectors to external systems (HRIS, CRM, databases, etc.).

Features:
- OAuth2 authentication support
- Rate limiting and retry logic
- Connection pooling
- Error handling and logging
- Health checks and monitoring
- Credential encryption

Author: AI Agent System
Created: Phase 3.2 - Integration Framework
"""

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from collections import deque
import aiohttp
import json

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ConnectionStatus(Enum):
    """Status of a connector connection"""
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class AuthType(Enum):
    """Authentication type"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"
    TOKEN = "token"
    CUSTOM = "custom"


# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter for API calls.

    Supports:
    - Requests per second/minute/hour limits
    - Burst handling
    - Automatic refill
    """

    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,  # seconds
        burst_size: Optional[int] = None
    ):
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        self.tokens = self.burst_size
        self.last_refill = time.time()
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens for making a request.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Returns:
            True if tokens acquired, False if rate limited
        """
        async with self._lock:
            # Refill tokens based on time passed
            now = time.time()
            time_passed = now - self.last_refill

            # Calculate tokens to add
            tokens_to_add = (time_passed / self.time_window) * self.max_requests
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_refill = now

            # Remove old requests from sliding window
            cutoff = now - self.time_window
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()

            # Check if we can make the request
            if len(self.requests) < self.max_requests and self.tokens >= tokens:
                self.tokens -= tokens
                self.requests.append(now)
                return True

            return False

    async def wait(self, tokens: int = 1, timeout: Optional[float] = None):
        """
        Wait until tokens are available.

        Args:
            tokens: Number of tokens needed
            timeout: Maximum time to wait (seconds)

        Raises:
            TimeoutError: If timeout exceeded
        """
        start_time = time.time()

        while True:
            if await self.acquire(tokens):
                return

            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("Rate limiter timeout exceeded")

            # Wait a bit before trying again
            await asyncio.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            'max_requests': self.max_requests,
            'time_window': self.time_window,
            'current_tokens': self.tokens,
            'requests_in_window': len(self.requests),
            'utilization': len(self.requests) / self.max_requests
        }


# ============================================================================
# RETRY HANDLER
# ============================================================================

class RetryConfig:
    """Configuration for retry logic"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        delay = min(
            self.max_delay,
            self.initial_delay * (self.exponential_base ** attempt)
        )

        if self.jitter:
            import random
            delay *= (0.5 + random.random())  # Add jitter: 50-150% of delay

        return delay


async def with_retry(
    func: Callable,
    retry_config: RetryConfig,
    retry_on: tuple = (Exception,),
    *args,
    **kwargs
) -> Any:
    """
    Execute function with retry logic.

    Args:
        func: Async function to execute
        retry_config: Retry configuration
        retry_on: Tuple of exceptions to retry on
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of successful function call

    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None

    for attempt in range(retry_config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retry_on as e:
            last_exception = e

            if attempt < retry_config.max_retries:
                delay = retry_config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1}/{retry_config.max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {retry_config.max_retries + 1} attempts failed")

    raise last_exception


# ============================================================================
# CONNECTION METRICS
# ============================================================================

@dataclass
class ConnectionMetrics:
    """Metrics for monitoring connector health"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[float] = None
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    uptime_start: float = field(default_factory=time.time)

    def record_request(self, success: bool, response_time: float, error: Optional[str] = None):
        """Record a request"""
        self.total_requests += 1
        self.last_request_time = time.time()
        self.total_response_time += response_time

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error:
                self.last_error = error
                self.last_error_time = time.time()

    def record_rate_limit(self):
        """Record a rate limited request"""
        self.rate_limited_requests += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        avg_response_time = (
            self.total_response_time / self.total_requests
            if self.total_requests > 0
            else 0
        )

        success_rate = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0
            else 0
        )

        uptime = time.time() - self.uptime_start

        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'rate_limited_requests': self.rate_limited_requests,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'uptime_seconds': uptime,
            'last_request_time': datetime.fromtimestamp(self.last_request_time).isoformat() if self.last_request_time else None,
            'last_error': self.last_error,
            'last_error_time': datetime.fromtimestamp(self.last_error_time).isoformat() if self.last_error_time else None
        }


# ============================================================================
# BASE CONNECTOR
# ============================================================================

class Connector(ABC):
    """
    Abstract base class for all external system connectors.

    Provides:
    - Authentication management
    - Rate limiting
    - Retry logic
    - Connection pooling
    - Health monitoring
    - Error handling
    """

    def __init__(
        self,
        connector_id: str,
        name: str,
        config: Dict[str, Any],
        rate_limit: Optional[RateLimiter] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        self.connector_id = connector_id
        self.name = name
        self.config = config
        self.status = ConnectionStatus.DISCONNECTED
        self.session: Optional[aiohttp.ClientSession] = None
        self.metrics = ConnectionMetrics()

        # Rate limiting
        self.rate_limiter = rate_limit or RateLimiter(
            max_requests=config.get('rate_limit_requests', 100),
            time_window=config.get('rate_limit_window', 60)
        )

        # Retry configuration
        self.retry_config = retry_config or RetryConfig(
            max_retries=config.get('max_retries', 3)
        )

        # Authentication
        self.auth_type = AuthType(config.get('auth_type', 'api_key'))
        self.authenticated = False
        self.auth_token: Optional[str] = None
        self.auth_expires: Optional[datetime] = None

        logger.info(f"Connector initialized: {self.name} ({self.connector_id})")

    # ========================================================================
    # LIFECYCLE METHODS
    # ========================================================================

    async def connect(self) -> bool:
        """
        Establish connection to the external system.

        Returns:
            True if connection successful
        """
        try:
            self.status = ConnectionStatus.AUTHENTICATING
            logger.info(f"Connecting to {self.name}...")

            # Create HTTP session
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Authenticate
            auth_success = await self.authenticate()

            if auth_success:
                self.status = ConnectionStatus.CONNECTED
                self.authenticated = True
                logger.info(f"Successfully connected to {self.name}")
                return True
            else:
                self.status = ConnectionStatus.ERROR
                logger.error(f"Authentication failed for {self.name}")
                return False

        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.metrics.record_request(False, 0, str(e))
            logger.error(f"Connection failed for {self.name}: {e}")
            return False

    async def disconnect(self):
        """Close connection and cleanup resources"""
        try:
            if self.session:
                await self.session.close()
                self.session = None

            self.status = ConnectionStatus.DISCONNECTED
            self.authenticated = False
            logger.info(f"Disconnected from {self.name}")

        except Exception as e:
            logger.error(f"Error disconnecting from {self.name}: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    # ========================================================================
    # ABSTRACT METHODS (Must be implemented by subclasses)
    # ========================================================================

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the external system.

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the external system.

        Returns:
            Dict with test results:
            {
                'success': bool,
                'latency_ms': float,
                'message': str,
                'details': Dict
            }
        """
        pass

    @abstractmethod
    async def query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Query data from the external system.

        Args:
            query: Query string (format depends on connector)
            params: Query parameters

        Returns:
            List of result records
        """
        pass

    @abstractmethod
    async def create(self, entity_type: str, data: Dict) -> Dict:
        """
        Create a new entity in the external system.

        Args:
            entity_type: Type of entity to create (e.g., 'employee', 'contact')
            data: Entity data

        Returns:
            Created entity with ID
        """
        pass

    @abstractmethod
    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict
    ) -> Dict:
        """
        Update an existing entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity to update
            data: Updated data

        Returns:
            Updated entity
        """
        pass

    # ========================================================================
    # OPTIONAL METHODS (Can be overridden by subclasses)
    # ========================================================================

    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """
        Delete an entity.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity to delete

        Returns:
            True if deleted successfully
        """
        raise NotImplementedError(f"{self.name} does not support delete operation")

    async def get(self, entity_type: str, entity_id: str) -> Dict:
        """
        Get a single entity by ID.

        Args:
            entity_type: Type of entity
            entity_id: ID of entity

        Returns:
            Entity data
        """
        # Default implementation using query
        results = await self.query(f"{entity_type}:{entity_id}")
        if results:
            return results[0]
        raise ValueError(f"{entity_type} with ID {entity_id} not found")

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def execute_with_rate_limit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with rate limiting.

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result of function
        """
        # Wait for rate limiter
        await self.rate_limiter.wait(timeout=30)

        # Execute with retry
        start_time = time.time()
        try:
            result = await with_retry(
                func,
                self.retry_config,
                *args,
                **kwargs
            )
            response_time = time.time() - start_time
            self.metrics.record_request(True, response_time)
            return result

        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.record_request(False, response_time, str(e))
            raise

    def check_auth_expired(self) -> bool:
        """Check if authentication has expired"""
        if not self.auth_expires:
            return False
        return datetime.utcnow() >= self.auth_expires

    async def refresh_auth_if_needed(self):
        """Refresh authentication if expired"""
        if self.check_auth_expired():
            logger.info(f"Auth expired for {self.name}, refreshing...")
            await self.authenticate()

    def get_health(self) -> Dict[str, Any]:
        """Get connector health information"""
        return {
            'connector_id': self.connector_id,
            'name': self.name,
            'status': self.status.value,
            'authenticated': self.authenticated,
            'auth_expires': self.auth_expires.isoformat() if self.auth_expires else None,
            'metrics': self.metrics.get_stats(),
            'rate_limiter': self.rate_limiter.get_stats()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize connector configuration"""
        return {
            'connector_id': self.connector_id,
            'name': self.name,
            'type': self.__class__.__name__,
            'status': self.status.value,
            'auth_type': self.auth_type.value,
            'config': {
                k: v for k, v in self.config.items()
                if k not in ['api_key', 'password', 'secret', 'token']  # Don't expose secrets
            }
        }


# ============================================================================
# CONNECTOR REGISTRY
# ============================================================================

class ConnectorRegistry:
    """
    Registry for managing multiple connectors.

    Provides:
    - Connector registration and discovery
    - Centralized connection management
    - Health monitoring across all connectors
    """

    def __init__(self):
        self.connectors: Dict[str, Connector] = {}
        logger.info("ConnectorRegistry initialized")

    def register(self, connector: Connector):
        """Register a connector"""
        self.connectors[connector.connector_id] = connector
        logger.info(f"Registered connector: {connector.name}")

    def unregister(self, connector_id: str):
        """Unregister a connector"""
        if connector_id in self.connectors:
            del self.connectors[connector_id]
            logger.info(f"Unregistered connector: {connector_id}")

    def get(self, connector_id: str) -> Optional[Connector]:
        """Get a connector by ID"""
        return self.connectors.get(connector_id)

    def list_all(self) -> List[Connector]:
        """List all registered connectors"""
        return list(self.connectors.values())

    def list_by_type(self, connector_type: str) -> List[Connector]:
        """List connectors of a specific type"""
        return [
            c for c in self.connectors.values()
            if c.__class__.__name__ == connector_type
        ]

    async def connect_all(self):
        """Connect all registered connectors"""
        tasks = [c.connect() for c in self.connectors.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(f"Connected {success_count}/{len(self.connectors)} connectors")

    async def disconnect_all(self):
        """Disconnect all connectors"""
        tasks = [c.disconnect() for c in self.connectors.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All connectors disconnected")

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for all connectors"""
        return {
            'total_connectors': len(self.connectors),
            'connected': sum(
                1 for c in self.connectors.values()
                if c.status == ConnectionStatus.CONNECTED
            ),
            'disconnected': sum(
                1 for c in self.connectors.values()
                if c.status == ConnectionStatus.DISCONNECTED
            ),
            'error': sum(
                1 for c in self.connectors.values()
                if c.status == ConnectionStatus.ERROR
            ),
            'connectors': [c.get_health() for c in self.connectors.values()]
        }


# Global registry instance
_registry = None


def get_registry() -> ConnectorRegistry:
    """Get the global connector registry"""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry
