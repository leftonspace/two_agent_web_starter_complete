"""
Connection Pooling for LLM Providers

Provides connection pooling and management for HTTP clients
used by LLM providers to improve performance and reduce latency.
"""

from typing import TypeVar, Generic, Optional, Any, Dict, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager
from collections import deque
import asyncio
import threading
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class PoolConfig:
    """Configuration for connection pools."""
    min_size: int = 2  # Minimum pool size
    max_size: int = 10  # Maximum pool size
    max_idle_time: int = 300  # Max idle time in seconds before connection is closed
    connection_timeout: float = 30.0  # Timeout for acquiring connection
    health_check_interval: int = 60  # Interval for health checks
    retry_on_error: bool = True  # Retry failed connections
    max_retries: int = 3  # Maximum retries for failed connections


@dataclass
class PooledConnection(Generic[T]):
    """Wrapper for a pooled connection with metadata."""
    connection: T
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)
    use_count: int = 0
    is_healthy: bool = True

    def mark_used(self):
        """Mark connection as used."""
        self.last_used_at = time.time()
        self.use_count += 1

    def is_idle_expired(self, max_idle_time: int) -> bool:
        """Check if connection has been idle too long."""
        return time.time() - self.last_used_at > max_idle_time


@dataclass
class PoolStats:
    """Statistics for connection pool."""
    created_connections: int = 0
    closed_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_acquisitions: int = 0
    total_releases: int = 0
    timeouts: int = 0
    errors: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_connections": self.created_connections,
            "closed_connections": self.closed_connections,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "total_acquisitions": self.total_acquisitions,
            "total_releases": self.total_releases,
            "timeouts": self.timeouts,
            "errors": self.errors,
        }


class ConnectionPool(Generic[T]):
    """
    Thread-safe connection pool for synchronous connections.

    Usage:
        def create_client():
            return httpx.Client(timeout=30)

        pool = ConnectionPool(create_client, PoolConfig(max_size=10))

        with pool.acquire() as client:
            response = client.get(url)
    """

    def __init__(
        self,
        factory: Callable[[], T],
        config: Optional[PoolConfig] = None,
        health_check: Optional[Callable[[T], bool]] = None,
        cleanup: Optional[Callable[[T], None]] = None
    ):
        """
        Initialize connection pool.

        Args:
            factory: Function to create new connections
            config: Pool configuration
            health_check: Optional function to check connection health
            cleanup: Optional function to cleanup connection on close
        """
        self.factory = factory
        self.config = config or PoolConfig()
        self.health_check = health_check
        self.cleanup = cleanup

        self._pool: deque[PooledConnection[T]] = deque()
        self._in_use: Dict[int, PooledConnection[T]] = {}
        self._lock = threading.Lock()
        self._available = threading.Semaphore(self.config.max_size)
        self._stats = PoolStats()

        # Initialize minimum connections
        self._initialize_pool()

    def _initialize_pool(self):
        """Create minimum number of connections."""
        for _ in range(self.config.min_size):
            try:
                conn = self._create_connection()
                self._pool.append(conn)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")

    def _create_connection(self) -> PooledConnection[T]:
        """Create a new pooled connection."""
        connection = self.factory()
        self._stats.created_connections += 1
        return PooledConnection(connection=connection)

    def _close_connection(self, pooled: PooledConnection[T]):
        """Close a connection."""
        if self.cleanup:
            try:
                self.cleanup(pooled.connection)
            except Exception as e:
                logger.warning(f"Error during connection cleanup: {e}")
        self._stats.closed_connections += 1

    def _check_health(self, pooled: PooledConnection[T]) -> bool:
        """Check connection health."""
        if self.health_check:
            try:
                return self.health_check(pooled.connection)
            except Exception:
                return False
        return pooled.is_healthy

    def acquire(self, timeout: Optional[float] = None) -> T:
        """
        Acquire a connection from the pool.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            Connection object

        Raises:
            TimeoutError: If acquisition times out
        """
        timeout = timeout or self.config.connection_timeout

        # Wait for available slot
        if not self._available.acquire(timeout=timeout):
            self._stats.timeouts += 1
            raise TimeoutError("Connection pool exhausted")

        self._stats.total_acquisitions += 1

        with self._lock:
            # Try to get existing connection
            while self._pool:
                pooled = self._pool.popleft()

                # Check if expired
                if pooled.is_idle_expired(self.config.max_idle_time):
                    self._close_connection(pooled)
                    continue

                # Check health
                if not self._check_health(pooled):
                    self._close_connection(pooled)
                    continue

                pooled.mark_used()
                self._in_use[id(pooled.connection)] = pooled
                self._update_stats()
                return pooled.connection

            # Create new connection
            try:
                pooled = self._create_connection()
                pooled.mark_used()
                self._in_use[id(pooled.connection)] = pooled
                self._update_stats()
                return pooled.connection
            except Exception as e:
                self._available.release()
                self._stats.errors += 1
                raise

    def release(self, connection: T):
        """
        Release a connection back to the pool.

        Args:
            connection: Connection to release
        """
        conn_id = id(connection)

        with self._lock:
            if conn_id not in self._in_use:
                logger.warning("Releasing unknown connection")
                return

            pooled = self._in_use.pop(conn_id)
            self._stats.total_releases += 1

            # Check if still healthy before returning to pool
            if self._check_health(pooled):
                self._pool.append(pooled)
            else:
                self._close_connection(pooled)

            self._update_stats()

        self._available.release()

    def _update_stats(self):
        """Update pool statistics."""
        self._stats.active_connections = len(self._in_use)
        self._stats.idle_connections = len(self._pool)

    @contextmanager
    def connection(self, timeout: Optional[float] = None):
        """
        Context manager for acquiring/releasing connections.

        Usage:
            with pool.connection() as conn:
                conn.do_something()
        """
        conn = self.acquire(timeout)
        try:
            yield conn
        finally:
            self.release(conn)

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return self._stats.to_dict()

    def close_all(self):
        """Close all connections and shutdown pool."""
        with self._lock:
            # Close idle connections
            while self._pool:
                pooled = self._pool.popleft()
                self._close_connection(pooled)

            # Close in-use connections
            for pooled in self._in_use.values():
                self._close_connection(pooled)
            self._in_use.clear()

            self._update_stats()


class AsyncConnectionPool(Generic[T]):
    """
    Async connection pool for async HTTP clients.

    Usage:
        async def create_client():
            return httpx.AsyncClient(timeout=30)

        pool = AsyncConnectionPool(create_client, PoolConfig(max_size=10))

        async with pool.acquire() as client:
            response = await client.get(url)
    """

    def __init__(
        self,
        factory: Callable[[], T],
        config: Optional[PoolConfig] = None,
        health_check: Optional[Callable[[T], bool]] = None,
        cleanup: Optional[Callable[[T], Any]] = None
    ):
        self.factory = factory
        self.config = config or PoolConfig()
        self.health_check = health_check
        self.cleanup = cleanup

        self._pool: deque[PooledConnection[T]] = deque()
        self._in_use: Dict[int, PooledConnection[T]] = {}
        self._lock: Optional[asyncio.Lock] = None  # Defer creation to avoid event loop issues
        self._semaphore: Optional[asyncio.Semaphore] = None  # Defer creation
        self._stats = PoolStats()
        self._initialized = False

    async def _get_lock(self) -> asyncio.Lock:
        """Get or create the async lock (deferred to avoid event loop issues)."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create the async semaphore (deferred to avoid event loop issues)."""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.config.max_size)
        return self._semaphore

    async def initialize(self):
        """Initialize pool with minimum connections."""
        if self._initialized:
            return

        for _ in range(self.config.min_size):
            try:
                conn = await self._create_connection()
                self._pool.append(conn)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")

        self._initialized = True

    async def _create_connection(self) -> PooledConnection[T]:
        """Create a new pooled connection."""
        if asyncio.iscoroutinefunction(self.factory):
            connection = await self.factory()
        else:
            connection = self.factory()
        self._stats.created_connections += 1
        return PooledConnection(connection=connection)

    async def _close_connection(self, pooled: PooledConnection[T]):
        """Close a connection."""
        if self.cleanup:
            try:
                result = self.cleanup(pooled.connection)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning(f"Error during connection cleanup: {e}")
        self._stats.closed_connections += 1

    def _check_health(self, pooled: PooledConnection[T]) -> bool:
        """Check connection health."""
        if self.health_check:
            try:
                return self.health_check(pooled.connection)
            except Exception:
                return False
        return pooled.is_healthy

    async def acquire(self, timeout: Optional[float] = None) -> T:
        """Acquire a connection from the pool."""
        if not self._initialized:
            await self.initialize()

        timeout = timeout or self.config.connection_timeout

        # Get or create semaphore and lock (deferred creation)
        semaphore = await self._get_semaphore()
        lock = await self._get_lock()

        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=timeout)
        except asyncio.TimeoutError:
            self._stats.timeouts += 1
            raise TimeoutError("Connection pool exhausted")

        self._stats.total_acquisitions += 1

        async with lock:
            while self._pool:
                pooled = self._pool.popleft()

                if pooled.is_idle_expired(self.config.max_idle_time):
                    await self._close_connection(pooled)
                    continue

                if not self._check_health(pooled):
                    await self._close_connection(pooled)
                    continue

                pooled.mark_used()
                self._in_use[id(pooled.connection)] = pooled
                self._update_stats()
                return pooled.connection

            try:
                pooled = await self._create_connection()
                pooled.mark_used()
                self._in_use[id(pooled.connection)] = pooled
                self._update_stats()
                return pooled.connection
            except Exception as e:
                semaphore.release()
                self._stats.errors += 1
                raise

    async def release(self, connection: T):
        """Release a connection back to the pool."""
        conn_id = id(connection)

        # Get or create lock and semaphore (deferred creation)
        lock = await self._get_lock()
        semaphore = await self._get_semaphore()

        async with lock:
            if conn_id not in self._in_use:
                logger.warning("Releasing unknown connection")
                return

            pooled = self._in_use.pop(conn_id)
            self._stats.total_releases += 1

            if self._check_health(pooled):
                self._pool.append(pooled)
            else:
                await self._close_connection(pooled)

            self._update_stats()

        semaphore.release()

    def _update_stats(self):
        """Update pool statistics."""
        self._stats.active_connections = len(self._in_use)
        self._stats.idle_connections = len(self._pool)

    @asynccontextmanager
    async def connection(self, timeout: Optional[float] = None):
        """Context manager for acquiring/releasing connections."""
        conn = await self.acquire(timeout)
        try:
            yield conn
        finally:
            await self.release(conn)

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return self._stats.to_dict()

    async def close_all(self):
        """Close all connections and shutdown pool."""
        lock = await self._get_lock()
        async with lock:
            while self._pool:
                pooled = self._pool.popleft()
                await self._close_connection(pooled)

            for pooled in self._in_use.values():
                await self._close_connection(pooled)
            self._in_use.clear()

            self._update_stats()


# Global HTTP client pool
_http_pool: Optional[AsyncConnectionPool] = None


def get_http_pool(config: Optional[PoolConfig] = None) -> AsyncConnectionPool:
    """
    Get or create the global HTTP client pool.

    Args:
        config: Optional configuration for new pool

    Returns:
        AsyncConnectionPool for HTTP clients
    """
    global _http_pool

    if _http_pool is None:
        try:
            import httpx

            def create_client():
                return httpx.AsyncClient(timeout=60.0)

            async def cleanup_client(client):
                await client.aclose()

            _http_pool = AsyncConnectionPool(
                factory=create_client,
                config=config or PoolConfig(min_size=2, max_size=20),
                cleanup=cleanup_client
            )
        except ImportError:
            logger.warning("httpx not available, HTTP pool disabled")
            return None

    return _http_pool


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'PoolConfig',
    'PooledConnection',
    'PoolStats',
    'ConnectionPool',
    'AsyncConnectionPool',
    'get_http_pool',
]
