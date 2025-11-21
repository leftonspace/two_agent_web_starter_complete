"""
PHASE 11.4: Performance Optimization

Production-scale performance optimizations for caching, batch processing, and lazy loading.

Components:
- cache: Multi-tier caching system (memory + Redis)
- batch_processor: Efficient batch processing
- lazy_loader: Deferred computation and lazy loading

Features:
- LRU memory cache with TTL
- Redis distributed cache
- Query and LLM response caching
- Automatic cache warming
- Batch processing with windowing
- Lazy evaluation and loading
- Connection pooling
"""

from .cache import (
    CacheManager,
    CacheKey,
    CacheStats,
    LRUCache,
    get_global_cache,
)
from .batch_processor import (
    BatchProcessor,
    BatchConfig,
    BatchResult,
)
from .lazy_loader import (
    LazyLoader,
    LazyValue,
    lazy_property,
)

__all__ = [
    "CacheManager",
    "CacheKey",
    "CacheStats",
    "LRUCache",
    "get_global_cache",
    "BatchProcessor",
    "BatchConfig",
    "BatchResult",
    "LazyLoader",
    "LazyValue",
    "lazy_property",
]
