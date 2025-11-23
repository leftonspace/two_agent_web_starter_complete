"""
Performance Utilities

High-level utilities and helpers for performance optimization.
Provides profiling, monitoring, and optimization helpers.
"""

from typing import TypeVar, Callable, Optional, Any, Dict, List, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from contextlib import contextmanager, asynccontextmanager
import asyncio
import threading
import time
import logging
import statistics

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class TimingStats:
    """Statistics from timing measurements."""
    name: str
    call_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    times: List[float] = field(default_factory=list)

    @property
    def avg_time_ms(self) -> float:
        return self.total_time_ms / self.call_count if self.call_count > 0 else 0.0

    @property
    def p50_ms(self) -> float:
        if not self.times:
            return 0.0
        return statistics.median(self.times)

    @property
    def p95_ms(self) -> float:
        if len(self.times) < 2:
            return self.avg_time_ms
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx]

    @property
    def p99_ms(self) -> float:
        if len(self.times) < 2:
            return self.avg_time_ms
        sorted_times = sorted(self.times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[idx]

    def record(self, time_ms: float):
        """Record a timing measurement."""
        self.call_count += 1
        self.total_time_ms += time_ms
        self.min_time_ms = min(self.min_time_ms, time_ms)
        self.max_time_ms = max(self.max_time_ms, time_ms)
        self.times.append(time_ms)

        # Keep only last 1000 measurements
        if len(self.times) > 1000:
            self.times = self.times[-1000:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "call_count": self.call_count,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_time_ms": round(self.avg_time_ms, 2),
            "min_time_ms": round(self.min_time_ms, 2) if self.min_time_ms != float('inf') else 0,
            "max_time_ms": round(self.max_time_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
        }


class PerformanceMonitor:
    """
    Monitors and collects performance metrics.

    Usage:
        monitor = PerformanceMonitor()

        @monitor.timed("my_function")
        def my_function():
            ...

        # Or use context manager
        with monitor.measure("operation"):
            do_something()

        # Get stats
        print(monitor.get_stats("my_function"))
    """

    def __init__(self):
        self._stats: Dict[str, TimingStats] = {}
        self._enabled = True

    def enable(self):
        """Enable monitoring."""
        self._enabled = True

    def disable(self):
        """Disable monitoring."""
        self._enabled = False

    def _get_or_create_stats(self, name: str) -> TimingStats:
        """Get or create stats for a metric."""
        if name not in self._stats:
            self._stats[name] = TimingStats(name=name)
        return self._stats[name]

    @contextmanager
    def measure(self, name: str):
        """
        Context manager for timing a code block.

        Args:
            name: Name for this measurement
        """
        if not self._enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            stats = self._get_or_create_stats(name)
            stats.record(duration_ms)

    @asynccontextmanager
    async def measure_async(self, name: str):
        """
        Async context manager for timing.

        Args:
            name: Name for this measurement
        """
        if not self._enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            duration_ms = (time.time() - start) * 1000
            stats = self._get_or_create_stats(name)
            stats.record(duration_ms)

    def timed(self, name: Optional[str] = None) -> Callable:
        """
        Decorator for timing function calls.

        Args:
            name: Optional metric name (uses function name if not provided)

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            metric_name = name or func.__name__

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.measure(metric_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def timed_async(self, name: Optional[str] = None) -> Callable:
        """
        Decorator for timing async function calls.

        Args:
            name: Optional metric name

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            metric_name = name or func.__name__

            @wraps(func)
            async def wrapper(*args, **kwargs):
                async with self.measure_async(metric_name):
                    return await func(*args, **kwargs)
            return wrapper
        return decorator

    def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get stats for a metric."""
        if name in self._stats:
            return self._stats[name].to_dict()
        return None

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get all stats."""
        return {name: stats.to_dict() for name, stats in self._stats.items()}

    def reset(self, name: Optional[str] = None):
        """Reset stats (all or specific metric)."""
        if name:
            if name in self._stats:
                del self._stats[name]
        else:
            self._stats.clear()


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def timed(name: Optional[str] = None) -> Callable:
    """
    Decorator for timing function calls using global monitor.

    Args:
        name: Optional metric name

    Returns:
        Decorator function
    """
    return get_monitor().timed(name)


def timed_async(name: Optional[str] = None) -> Callable:
    """
    Decorator for timing async function calls using global monitor.

    Args:
        name: Optional metric name

    Returns:
        Decorator function
    """
    return get_monitor().timed_async(name)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying with exponential backoff.

    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential: Use exponential backoff
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt if exponential else 1)
                        delay = min(delay, max_delay)
                        logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def async_retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retrying async functions with exponential backoff.

    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential: Use exponential backoff
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt if exponential else 1)
                        delay = min(delay, max_delay)
                        logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
                        await asyncio.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def debounce(wait: float) -> Callable:
    """
    Decorator that debounces a function call.

    Only executes after `wait` seconds of no calls.

    Args:
        wait: Wait time in seconds

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        timer = [None]
        lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            def call_func():
                with lock:
                    timer[0] = None
                func(*args, **kwargs)

            with lock:
                # Cancel previous timer if running
                if timer[0] is not None:
                    timer[0].cancel()

                # Create and start new timer
                timer[0] = threading.Timer(wait, call_func)
                timer[0].start()

        return wrapper
    return decorator


def throttle(rate: float) -> Callable:
    """
    Decorator that throttles a function to max `rate` calls per second.

    Args:
        rate: Maximum calls per second

    Returns:
        Decorator function
    """
    min_interval = 1.0 / rate
    last_called = [0.0]

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def async_throttle(rate: float) -> Callable:
    """
    Decorator that throttles an async function.

    Args:
        rate: Maximum calls per second

    Returns:
        Decorator function
    """
    min_interval = 1.0 / rate
    last_called = [0.0]
    lock = asyncio.Lock()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with lock:
                elapsed = time.time() - last_called[0]
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
                last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def memoize_with_ttl(ttl_seconds: int = 300) -> Callable:
    """
    Simple memoization decorator with TTL.

    Args:
        ttl_seconds: Cache TTL in seconds

    Returns:
        Decorator function
    """
    cache: Dict[str, tuple] = {}

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = str((args, tuple(sorted(kwargs.items()))))

            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    return result

            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        return wrapper
    return decorator


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'TimingStats',
    'PerformanceMonitor',
    'get_monitor',
    'timed',
    'timed_async',
    'RateLimitExceeded',
    'retry_with_backoff',
    'async_retry_with_backoff',
    'debounce',
    'throttle',
    'async_throttle',
    'memoize_with_ttl',
]
