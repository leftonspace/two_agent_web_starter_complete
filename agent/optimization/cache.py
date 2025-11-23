"""
PHASE 11.4: Caching System

Multi-tier caching with memory and Redis for production performance.

Features:
- LRU memory cache with TTL
- Redis distributed cache
- Query result caching
- LLM response caching
- Cache warming and invalidation
- Statistics and monitoring
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps

T = TypeVar('T')


@dataclass
class CacheKey:
    """Cache key with namespace and identifier."""

    namespace: str
    identifier: str

    def to_string(self) -> str:
        """Convert to string key."""
        return f"{self.namespace}:{identifier}"

    @staticmethod
    def from_function(func: Callable, *args, **kwargs) -> str:
        """Generate cache key from function and arguments."""
        # Create deterministic key from function name and arguments
        key_parts = [func.__name__]

        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))

        # Add keyword arguments (sorted for consistency)
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        # Hash the key for consistent length
        key_str = ":".join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return f"func:{func.__name__}:{key_hash}"


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
        }


class LRUCache:
    """
    LRU (Least Recently Used) cache with TTL support.

    Evicts least recently used items when capacity is reached.
    """

    def __init__(self, capacity: int = 1000, default_ttl: float = 3600):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items
            default_ttl: Default TTL in seconds
        """
        self.capacity = capacity
        self.default_ttl = default_ttl

        # Ordered dict maintains insertion/access order
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

        # Statistics
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            self.stats.misses += 1
            return None

        value, expiry = self.cache[key]

        # Check expiration
        if expiry > 0 and time.time() > expiry:
            # Expired - remove
            del self.cache[key]
            self.stats.misses += 1
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)

        self.stats.hits += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None = default)
        """
        # Calculate expiry
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl if ttl > 0 else 0

        # Check if we need to evict
        if key not in self.cache and len(self.cache) >= self.capacity:
            # Evict least recently used (first item)
            self.cache.popitem(last=False)
            self.stats.evictions += 1

        # Set value
        self.cache[key] = (value, expiry)

        # Move to end
        self.cache.move_to_end(key)

        self.stats.sets += 1

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            self.stats.deletes += 1
            return True

        return False

    def clear(self):
        """Clear all cached items."""
        self.cache.clear()

    def cleanup_expired(self):
        """Remove expired items."""
        now = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if expiry > 0 and now > expiry
        ]

        for key in expired_keys:
            del self.cache[key]

    def get_size(self) -> int:
        """Get current cache size."""
        return len(self.cache)

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.stats


class CacheManager:
    """
    Multi-tier caching system.

    Tier 1: In-memory LRU cache (fast, limited capacity)
    Tier 2: Redis cache (distributed, larger capacity)

    Features:
    - Automatic tier promotion/demotion
    - Cache warming
    - Batch operations
    - Statistics
    """

    def __init__(
        self,
        memory_capacity: int = 1000,
        default_ttl: float = 3600,
        use_redis: bool = False,
        redis_host: str = "localhost",
        redis_port: int = 6379,
    ):
        """
        Initialize cache manager.

        Args:
            memory_capacity: Memory cache capacity
            default_ttl: Default TTL in seconds
            use_redis: Whether to use Redis
            redis_host: Redis host
            redis_port: Redis port
        """
        # Memory cache (Tier 1)
        self.memory_cache = LRUCache(
            capacity=memory_capacity,
            default_ttl=default_ttl,
        )

        self.default_ttl = default_ttl

        # Redis cache (Tier 2) - optional
        self.use_redis = use_redis
        self.redis_client = None

        if use_redis:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=False,
                )
            except ImportError:
                print("Warning: redis not installed, falling back to memory-only cache")
                self.use_redis = False

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with tier fallback.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try memory cache first (Tier 1)
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Try Redis (Tier 2) if enabled
        if self.use_redis and self.redis_client:
            try:
                redis_value = await self.redis_client.get(key)
                if redis_value:
                    # SECURITY: Use JSON instead of pickle to prevent code execution
                    value = json.loads(redis_value)

                    # Promote to memory cache
                    self.memory_cache.set(key, value)

                    return value

            except json.JSONDecodeError as e:
                print(f"Redis JSON decode error (possibly old pickle data): {e}")
            except Exception as e:
                print(f"Redis get error: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ):
        """
        Set value in all cache tiers.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        ttl = ttl if ttl is not None else self.default_ttl

        # Set in memory cache
        self.memory_cache.set(key, value, ttl)

        # Set in Redis if enabled
        if self.use_redis and self.redis_client:
            try:
                # SECURITY: Use JSON instead of pickle to prevent code execution
                serialized = json.dumps(value)

                # Set with expiration
                if ttl > 0:
                    await self.redis_client.setex(key, int(ttl), serialized)
                else:
                    await self.redis_client.set(key, serialized)

            except TypeError as e:
                print(f"Redis serialization error (non-JSON-serializable value): {e}")
            except Exception as e:
                print(f"Redis set error: {e}")

    async def delete(self, key: str):
        """
        Delete key from all cache tiers.

        Args:
            key: Cache key
        """
        # Delete from memory
        self.memory_cache.delete(key)

        # Delete from Redis
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                print(f"Redis delete error: {e}")

    async def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: Optional[float] = None,
    ) -> Any:
        """
        Get from cache or compute and cache.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = await self.get(key)

        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(compute_fn):
            value = await compute_fn()
        else:
            value = compute_fn()

        # Cache the result
        await self.set(key, value, ttl)

        return value

    async def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:*")
        """
        # Invalidate memory cache
        keys_to_delete = [
            key for key in self.memory_cache.cache.keys()
            if self._matches_pattern(key, pattern)
        ]

        for key in keys_to_delete:
            self.memory_cache.delete(key)

        # Invalidate Redis
        if self.use_redis and self.redis_client:
            try:
                # Scan for matching keys
                cursor = 0
                while True:
                    cursor, keys = await self.redis_client.scan(
                        cursor,
                        match=pattern,
                        count=100,
                    )

                    if keys:
                        await self.redis_client.delete(*keys)

                    if cursor == 0:
                        break

            except Exception as e:
                print(f"Redis invalidate error: {e}")

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern (simple * wildcard)."""
        if "*" not in pattern:
            return key == pattern

        # Split on *
        parts = pattern.split("*")

        # Check prefix
        if parts[0] and not key.startswith(parts[0]):
            return False

        # Check suffix
        if parts[-1] and not key.endswith(parts[-1]):
            return False

        return True

    def clear_memory_cache(self):
        """Clear memory cache."""
        self.memory_cache.clear()

    async def warm_cache(
        self,
        keys_and_compute: list[tuple[str, Callable]],
    ):
        """
        Warm cache with computed values.

        Args:
            keys_and_compute: List of (key, compute_fn) tuples
        """
        for key, compute_fn in keys_and_compute:
            await self.get_or_compute(key, compute_fn)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory": self.memory_cache.get_stats().to_dict(),
            "memory_size": self.memory_cache.get_size(),
            "memory_capacity": self.memory_cache.capacity,
            "redis_enabled": self.use_redis,
        }

        return stats


def cached(
    ttl: float = 3600,
    key_prefix: Optional[str] = None,
):
    """
    Decorator for caching function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Optional key prefix

    Usage:
        @cached(ttl=300)
        async def expensive_function(arg1, arg2):
            # Expensive computation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get global cache
            cache = get_global_cache()

            # Generate cache key
            prefix = key_prefix or func.__name__
            key = CacheKey.from_function(func, *args, **kwargs)
            full_key = f"{prefix}:{key}"

            # Try to get from cache
            result = await cache.get(full_key)

            if result is not None:
                return result

            # Compute result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Cache result
            await cache.set(full_key, result, ttl)

            return result

        return wrapper

    return decorator


# Global cache singleton
_global_cache: Optional[CacheManager] = None


def get_global_cache() -> CacheManager:
    """Get global cache manager."""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache
