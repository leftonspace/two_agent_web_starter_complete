"""
Response Caching System

Provides caching for LLM responses and expensive computations
with TTL (time-to-live), LRU eviction, and async support.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict, Tuple, Hashable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from collections import OrderedDict
import asyncio
import hashlib
import json
import threading
import time

T = TypeVar('T')


@dataclass
class CacheConfig:
    """Configuration for the response cache."""
    max_size: int = 1000  # Maximum number of cached items
    ttl_seconds: int = 3600  # Time-to-live in seconds (1 hour default)
    enable_stats: bool = True  # Track hit/miss statistics
    hash_function: str = "md5"  # Hash function for keys


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    value: Any
    created_at: float
    expires_at: float
    hits: int = 0
    size_bytes: int = 0


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    total_size_bytes: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": round(self.hit_rate, 4),
            "total_size_bytes": self.total_size_bytes,
        }


class ResponseCache:
    """
    LRU cache with TTL support for caching expensive operations.

    Features:
    - Thread-safe operations
    - TTL-based expiration
    - LRU eviction when max size reached
    - Hit/miss statistics
    - Key generation from function arguments

    Usage:
        cache = ResponseCache(CacheConfig(max_size=100, ttl_seconds=600))

        # Manual caching
        cache.set("key", expensive_result)
        result = cache.get("key")

        # Or use as decorator
        @cache.memoize
        def expensive_function(arg):
            return compute(arg)
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize the response cache.

        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats() if self.config.enable_stats else None

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if self._stats:
                self._stats.total_requests += 1

            if key not in self._cache:
                if self._stats:
                    self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if time.time() > entry.expires_at:
                del self._cache[key]
                if self._stats:
                    self._stats.misses += 1
                return None

            # Update LRU order and hit count
            self._cache.move_to_end(key)
            entry.hits += 1

            if self._stats:
                self._stats.hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses config default if not specified)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds
        now = time.time()

        # Estimate size
        try:
            size_bytes = len(json.dumps(value).encode())
        except (TypeError, ValueError):
            size_bytes = 0

        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=now + ttl,
            size_bytes=size_bytes
        )

        with self._lock:
            # Evict if at capacity
            while len(self._cache) >= self.config.max_size:
                oldest_key = next(iter(self._cache))
                oldest_entry = self._cache.pop(oldest_key)
                if self._stats:
                    self._stats.evictions += 1
                    self._stats.total_size_bytes -= oldest_entry.size_bytes

            self._cache[key] = entry
            if self._stats:
                self._stats.total_size_bytes += size_bytes

    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted
        """
        with self._lock:
            if key in self._cache:
                entry = self._cache.pop(key)
                if self._stats:
                    self._stats.total_size_bytes -= entry.size_bytes
                return True
            return False

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            if self._stats:
                self._stats.total_size_bytes = 0

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        now = time.time()
        removed = 0

        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if now > v.expires_at
            ]

            for key in expired_keys:
                entry = self._cache.pop(key)
                if self._stats:
                    self._stats.total_size_bytes -= entry.size_bytes
                removed += 1

        return removed

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self._stats:
            return self._stats.to_dict()
        return None

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def memoize(self, func: Callable) -> Callable:
        """
        Decorator for memoizing function results.

        Args:
            func: Function to memoize

        Returns:
            Wrapped function with caching
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = cache_key(func.__name__, args, kwargs)
            result = self.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            self.set(key, result)
            return result
        return wrapper

    def memoize_async(self, func: Callable) -> Callable:
        """
        Decorator for memoizing async function results.

        Args:
            func: Async function to memoize

        Returns:
            Wrapped async function with caching
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = cache_key(func.__name__, args, kwargs)
            result = self.get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            self.set(key, result)
            return result
        return wrapper


class AsyncResponseCache:
    """
    Async-safe response cache with the same features as ResponseCache.

    Uses asyncio.Lock for async operations.
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = CacheStats() if self.config.enable_stats else None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache asynchronously."""
        async with self._lock:
            if self._stats:
                self._stats.total_requests += 1

            if key not in self._cache:
                if self._stats:
                    self._stats.misses += 1
                return None

            entry = self._cache[key]

            if time.time() > entry.expires_at:
                del self._cache[key]
                if self._stats:
                    self._stats.misses += 1
                return None

            self._cache.move_to_end(key)
            entry.hits += 1

            if self._stats:
                self._stats.hits += 1

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache asynchronously."""
        ttl = ttl_seconds if ttl_seconds is not None else self.config.ttl_seconds
        now = time.time()

        try:
            size_bytes = len(json.dumps(value).encode())
        except (TypeError, ValueError):
            size_bytes = 0

        entry = CacheEntry(
            value=value,
            created_at=now,
            expires_at=now + ttl,
            size_bytes=size_bytes
        )

        async with self._lock:
            while len(self._cache) >= self.config.max_size:
                oldest_key = next(iter(self._cache))
                oldest_entry = self._cache.pop(oldest_key)
                if self._stats:
                    self._stats.evictions += 1
                    self._stats.total_size_bytes -= oldest_entry.size_bytes

            self._cache[key] = entry
            if self._stats:
                self._stats.total_size_bytes += size_bytes


def cache_key(
    func_name: str,
    args: Tuple,
    kwargs: Dict,
    hash_function: str = "md5"
) -> str:
    """
    Generate a cache key from function name and arguments.

    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments
        hash_function: Hash algorithm to use

    Returns:
        Hash string suitable for cache key
    """
    # Convert args and kwargs to a hashable representation
    key_parts = [func_name]

    for arg in args:
        if isinstance(arg, (str, int, float, bool, type(None))):
            key_parts.append(str(arg))
        elif isinstance(arg, (list, tuple)):
            key_parts.append(json.dumps(arg, sort_keys=True))
        elif isinstance(arg, dict):
            key_parts.append(json.dumps(arg, sort_keys=True))
        else:
            key_parts.append(str(id(arg)))

    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool, type(None))):
            key_parts.append(f"{k}={v}")
        elif isinstance(v, (list, tuple, dict)):
            key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
        else:
            key_parts.append(f"{k}={id(v)}")

    key_string = "|".join(key_parts)

    if hash_function == "md5":
        return hashlib.md5(key_string.encode()).hexdigest()
    elif hash_function == "sha256":
        return hashlib.sha256(key_string.encode()).hexdigest()
    else:
        return key_string


def cached(
    cache: ResponseCache,
    ttl_seconds: Optional[int] = None,
    key_fn: Optional[Callable[..., str]] = None
) -> Callable:
    """
    Decorator for caching function results.

    Args:
        cache: ResponseCache instance
        ttl_seconds: Optional custom TTL
        key_fn: Optional custom key generation function

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = cache_key(func.__name__, args, kwargs)

            result = cache.get(key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator


def async_cached(
    cache: ResponseCache,
    ttl_seconds: Optional[int] = None,
    key_fn: Optional[Callable[..., str]] = None
) -> Callable:
    """
    Decorator for caching async function results.

    Args:
        cache: ResponseCache instance
        ttl_seconds: Optional custom TTL
        key_fn: Optional custom key generation function

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = cache_key(func.__name__, args, kwargs)

            result = cache.get(key)
            if result is not None:
                return result

            result = await func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator


# Global cache for LLM responses
_llm_cache: Optional[ResponseCache] = None


def get_llm_cache(config: Optional[CacheConfig] = None) -> ResponseCache:
    """
    Get or create the global LLM response cache.

    Args:
        config: Optional configuration for new cache

    Returns:
        ResponseCache instance
    """
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = ResponseCache(config or CacheConfig(
            max_size=500,
            ttl_seconds=1800,  # 30 minutes for LLM responses
        ))
    return _llm_cache


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'CacheConfig',
    'CacheEntry',
    'CacheStats',
    'ResponseCache',
    'AsyncResponseCache',
    'cache_key',
    'cached',
    'async_cached',
    'get_llm_cache',
]
