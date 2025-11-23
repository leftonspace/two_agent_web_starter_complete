"""
Performance Optimization Module

Provides performance enhancements for the JARVIS 2.0 system:
- Lazy loading for memory and heavy components
- Response caching with TTL and LRU eviction
- Connection pooling for LLM providers
- Parallel execution utilities
- Async batching and throttling
"""

from .lazy import LazyLoader, lazy_property, LazyModule
from .cache import (
    ResponseCache,
    CacheConfig,
    cached,
    async_cached,
    cache_key,
)
from .pool import (
    ConnectionPool,
    PoolConfig,
    AsyncConnectionPool,
)
from .parallel import (
    ParallelExecutor,
    BatchProcessor,
    Throttler,
    run_parallel,
    run_with_timeout,
)

__all__ = [
    # Lazy loading
    'LazyLoader',
    'lazy_property',
    'LazyModule',

    # Caching
    'ResponseCache',
    'CacheConfig',
    'cached',
    'async_cached',
    'cache_key',

    # Connection pooling
    'ConnectionPool',
    'PoolConfig',
    'AsyncConnectionPool',

    # Parallel execution
    'ParallelExecutor',
    'BatchProcessor',
    'Throttler',
    'run_parallel',
    'run_with_timeout',
]

__version__ = '1.0.0'
