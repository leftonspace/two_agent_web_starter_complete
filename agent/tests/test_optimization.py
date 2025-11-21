"""
PHASE 11.4: Optimization Tests

Tests for caching, batch processing, and lazy loading.
"""

import asyncio
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from optimization.cache import (
    CacheManager,
    CacheKey,
    LRUCache,
    cached,
    get_global_cache,
)
from optimization.batch_processor import (
    BatchProcessor,
    BatchConfig,
    BatchResult,
    StreamingBatchProcessor,
)
from optimization.lazy_loader import (
    LazyValue,
    LazyLoader,
    lazy_property,
    LazyLoadingMixin,
    AsyncLazyIterator,
    lazy_async,
)


# ============================================================================
# Cache Tests
# ============================================================================

def test_lru_cache_set_get():
    """Test basic LRU cache operations."""
    cache = LRUCache(capacity=3)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"


def test_lru_cache_eviction():
    """Test LRU eviction."""
    cache = LRUCache(capacity=2)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # Should evict key1

    assert cache.get("key1") is None  # Evicted
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_lru_cache_ttl():
    """Test cache TTL expiration."""
    cache = LRUCache(default_ttl=0.1)

    cache.set("key1", "value1", ttl=0.1)

    # Should be available immediately
    assert cache.get("key1") == "value1"

    # Wait for expiration
    time.sleep(0.15)

    # Should be expired
    assert cache.get("key1") is None


def test_lru_cache_lru_order():
    """Test LRU ordering."""
    cache = LRUCache(capacity=3)

    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    # Access key1 (makes it most recent)
    cache.get("key1")

    # Add key4 (should evict key2, not key1)
    cache.set("key4", "value4")

    assert cache.get("key1") == "value1"  # Still there
    assert cache.get("key2") is None  # Evicted
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_lru_cache_delete():
    """Test cache deletion."""
    cache = LRUCache()

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    cache.delete("key1")
    assert cache.get("key1") is None


def test_lru_cache_stats():
    """Test cache statistics."""
    cache = LRUCache()

    cache.set("key1", "value1")
    cache.get("key1")  # Hit
    cache.get("key2")  # Miss

    stats = cache.get_stats()

    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.sets == 1
    assert stats.hit_rate == 0.5


@pytest.mark.asyncio
async def test_cache_manager_memory_only():
    """Test cache manager with memory cache only."""
    cache = CacheManager(use_redis=False)

    await cache.set("key1", "value1")

    value = await cache.get("key1")
    assert value == "value1"


@pytest.mark.asyncio
async def test_cache_manager_get_or_compute():
    """Test get_or_compute functionality."""
    cache = CacheManager(use_redis=False)

    call_count = [0]

    async def compute():
        call_count[0] += 1
        return "computed_value"

    # First call should compute
    value1 = await cache.get_or_compute("key1", compute)
    assert value1 == "computed_value"
    assert call_count[0] == 1

    # Second call should use cache
    value2 = await cache.get_or_compute("key1", compute)
    assert value2 == "computed_value"
    assert call_count[0] == 1  # Not called again


@pytest.mark.asyncio
async def test_cache_manager_delete():
    """Test cache deletion."""
    cache = CacheManager(use_redis=False)

    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"

    await cache.delete("key1")
    assert await cache.get("key1") is None


@pytest.mark.asyncio
async def test_cache_manager_invalidate_pattern():
    """Test pattern-based invalidation."""
    cache = CacheManager(use_redis=False)

    await cache.set("user:1", "data1")
    await cache.set("user:2", "data2")
    await cache.set("post:1", "post1")

    # Invalidate user:* keys
    await cache.invalidate_pattern("user:*")

    assert await cache.get("user:1") is None
    assert await cache.get("user:2") is None
    assert await cache.get("post:1") == "post1"  # Not invalidated


@pytest.mark.asyncio
async def test_cached_decorator():
    """Test cached decorator."""
    call_count = [0]

    @cached(ttl=300)
    async def expensive_function(x, y):
        call_count[0] += 1
        return x + y

    # First call
    result1 = await expensive_function(1, 2)
    assert result1 == 3
    assert call_count[0] == 1

    # Second call with same args (should use cache)
    result2 = await expensive_function(1, 2)
    assert result2 == 3
    assert call_count[0] == 1

    # Different args (should compute)
    result3 = await expensive_function(2, 3)
    assert result3 == 5
    assert call_count[0] == 2


def test_cache_key_from_function():
    """Test generating cache keys from functions."""
    def my_function(a, b, c=3):
        pass

    key1 = CacheKey.from_function(my_function, 1, 2, c=3)
    key2 = CacheKey.from_function(my_function, 1, 2, c=3)
    key3 = CacheKey.from_function(my_function, 1, 2, c=4)

    # Same args should generate same key
    assert key1 == key2

    # Different args should generate different key
    assert key1 != key3


# ============================================================================
# Batch Processing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_batch_processor_process_all():
    """Test processing all items."""
    processor = BatchProcessor()

    items = list(range(10))

    def process_item(item):
        return item * 2

    result = await processor.process_all(items, process_item, parallel=False)

    assert result.total_items == 10
    assert result.successful_items == 10
    assert result.failed_items == 0
    assert result.results == [i * 2 for i in range(10)]


@pytest.mark.asyncio
async def test_batch_processor_with_errors():
    """Test batch processing with errors."""
    config = BatchConfig(continue_on_error=True)
    processor = BatchProcessor(config)

    items = list(range(10))

    def process_item(item):
        if item == 5:
            raise ValueError("Error on 5")
        return item * 2

    result = await processor.process_all(items, process_item, parallel=False)

    assert result.total_items == 10
    assert result.successful_items == 9
    assert result.failed_items == 1
    assert len(result.errors) == 1


@pytest.mark.asyncio
async def test_batch_processor_parallel():
    """Test parallel batch processing."""
    config = BatchConfig(max_batch_size=3, max_concurrent_batches=2)
    processor = BatchProcessor(config)

    items = list(range(10))

    async def process_item(item):
        await asyncio.sleep(0.01)
        return item * 2

    result = await processor.process_all(items, process_item, parallel=True)

    assert result.total_items == 10
    assert result.successful_items == 10
    assert result.results == [i * 2 for i in range(10)]


@pytest.mark.asyncio
async def test_batch_processor_flush():
    """Test flushing pending items."""
    processor = BatchProcessor()

    # Add items
    await processor.add_item(1)
    await processor.add_item(2)
    await processor.add_item(3)

    async def process_batch(items):
        return [item * 2 for item in items]

    result = await processor.flush(process_batch)

    assert result.total_items == 3
    assert result.results == [2, 4, 6]


@pytest.mark.asyncio
async def test_streaming_batch_processor():
    """Test streaming batch processor."""
    results = []

    async def process_batch(items):
        results.extend(items)
        return items

    config = BatchConfig(max_wait_time=0.1)
    processor = StreamingBatchProcessor(process_batch, config)

    await processor.start()

    # Add items
    await processor.add(1)
    await processor.add(2)
    await processor.add(3)

    # Wait for processing
    await asyncio.sleep(0.2)

    await processor.stop()

    assert len(results) == 3


def test_batch_result_success_rate():
    """Test batch result success rate calculation."""
    result = BatchResult(
        total_items=10,
        successful_items=8,
        failed_items=2,
        results=[],
        errors=[],
        duration=1.0,
        batches_processed=2,
    )

    assert result.success_rate == 0.8


# ============================================================================
# Lazy Loading Tests
# ============================================================================

def test_lazy_value_basic():
    """Test basic lazy value."""
    call_count = [0]

    def compute():
        call_count[0] += 1
        return "value"

    lazy = LazyValue(compute)

    # Not computed initially
    assert not lazy.is_computed

    # First access computes
    value1 = lazy.get()
    assert value1 == "value"
    assert call_count[0] == 1

    # Second access uses cached value
    value2 = lazy.get()
    assert value2 == "value"
    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_lazy_value_async():
    """Test async lazy value."""
    call_count = [0]

    async def compute():
        call_count[0] += 1
        await asyncio.sleep(0.01)
        return "async_value"

    lazy = LazyValue(compute)

    value = await lazy.get_async()
    assert value == "async_value"
    assert call_count[0] == 1


def test_lazy_value_reset():
    """Test resetting lazy value."""
    call_count = [0]

    def compute():
        call_count[0] += 1
        return call_count[0]

    lazy = LazyValue(compute)

    # First computation
    value1 = lazy.get()
    assert value1 == 1

    # Reset
    lazy.reset()
    assert not lazy.is_computed

    # Second computation
    value2 = lazy.get()
    assert value2 == 2


def test_lazy_property_decorator():
    """Test lazy property decorator."""
    class TestClass:
        def __init__(self):
            self.call_count = 0

        @lazy_property
        def expensive_value(self):
            self.call_count += 1
            return "computed"

    obj = TestClass()

    # First access
    value1 = obj.expensive_value
    assert value1 == "computed"
    assert obj.call_count == 1

    # Second access (cached)
    value2 = obj.expensive_value
    assert value2 == "computed"
    assert obj.call_count == 1


@pytest.mark.asyncio
async def test_lazy_loader_basic():
    """Test lazy loader."""
    loader = LazyLoader()

    call_count = [0]

    def compute_value():
        call_count[0] += 1
        return "value"

    loader.register("test_value", compute_value)

    # First access
    value1 = await loader.get("test_value")
    assert value1 == "value"
    assert call_count[0] == 1

    # Second access (cached)
    value2 = await loader.get("test_value")
    assert value2 == "value"
    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_lazy_loader_dependencies():
    """Test lazy loader with dependencies."""
    loader = LazyLoader()

    results = []

    def compute_a():
        results.append("a")
        return "a"

    def compute_b():
        results.append("b")
        return "b"

    def compute_c():
        results.append("c")
        return "c"

    # Register with dependencies: c depends on a and b
    loader.register("a", compute_a)
    loader.register("b", compute_b)
    loader.register("c", compute_c, depends_on=["a", "b"])

    # Get c (should load a and b first)
    await loader.get("c")

    assert "a" in results
    assert "b" in results
    assert "c" in results


@pytest.mark.asyncio
async def test_lazy_loader_preload():
    """Test preloading multiple values."""
    loader = LazyLoader()

    loader.register("value1", lambda: "v1")
    loader.register("value2", lambda: "v2")
    loader.register("value3", lambda: "v3")

    # Preload
    await loader.preload(["value1", "value2"])

    # Check computed
    assert loader.is_computed("value1")
    assert loader.is_computed("value2")
    assert not loader.is_computed("value3")


def test_lazy_loader_statistics():
    """Test lazy loader statistics."""
    loader = LazyLoader()

    loader.register("value1", lambda: "v1")
    loader.register("value2", lambda: "v2")

    # Access value1
    loader.get_sync("value1")

    stats = loader.get_statistics()

    assert stats["total_registered"] == 2
    assert stats["total_computed"] == 1
    assert stats["access_counts"]["value1"] == 1


def test_lazy_loading_mixin():
    """Test lazy loading mixin."""
    class TestClass(LazyLoadingMixin):
        def __init__(self):
            super().__init__()
            self.call_count = 0
            self.register_lazy("data", self._load_data)

        def _load_data(self):
            self.call_count += 1
            return "loaded"

    obj = TestClass()

    # First access
    value1 = obj.get_lazy_sync("data")
    assert value1 == "loaded"
    assert obj.call_count == 1

    # Second access (cached)
    value2 = obj.get_lazy_sync("data")
    assert value2 == "loaded"
    assert obj.call_count == 1


@pytest.mark.asyncio
async def test_async_lazy_iterator():
    """Test async lazy iterator."""
    def loader(index):
        return index * 2

    iterator = AsyncLazyIterator(
        loader=loader,
        total_items=5,
        batch_size=2,
    )

    results = []
    async for item in iterator:
        results.append(item)

    assert results == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_lazy_async_decorator():
    """Test lazy async decorator."""
    call_count = [0]

    @lazy_async
    async def expensive_operation(x):
        call_count[0] += 1
        await asyncio.sleep(0.01)
        return x * 2

    # First call
    result1 = await expensive_operation(5)
    assert result1 == 10
    assert call_count[0] == 1

    # Second call with same args (cached)
    result2 = await expensive_operation(5)
    assert result2 == 10
    assert call_count[0] == 1

    # Different args (not cached)
    result3 = await expensive_operation(10)
    assert result3 == 20
    assert call_count[0] == 2


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cache_with_batch_processing():
    """Test caching batch processing results."""
    cache = CacheManager(use_redis=False)
    processor = BatchProcessor()

    async def process_batch(items):
        # Simulate expensive operation
        await asyncio.sleep(0.01)
        return [item * 2 for item in items]

    items = list(range(10))

    # First processing
    result1 = await cache.get_or_compute(
        "batch_result",
        lambda: processor.process_batch(items, process_batch),
    )

    # Second processing (should use cache)
    start = time.time()
    result2 = await cache.get_or_compute(
        "batch_result",
        lambda: processor.process_batch(items, process_batch),
    )
    elapsed = time.time() - start

    # Should be much faster (cached)
    assert elapsed < 0.005
    assert result2.results == result1.results


@pytest.mark.asyncio
async def test_lazy_loading_with_cache():
    """Test combining lazy loading with caching."""
    cache = CacheManager(use_redis=False)
    loader = LazyLoader()

    call_count = [0]

    async def load_data():
        call_count[0] += 1
        return await cache.get_or_compute(
            "expensive_data",
            lambda: "computed_data",
        )

    loader.register("data", load_data)

    # First access
    data1 = await loader.get("data")
    assert data1 == "computed_data"
    assert call_count[0] == 1

    # Reset lazy loader but cache remains
    loader.reset("data")

    # Second access (lazy recomputes but gets from cache)
    data2 = await loader.get("data")
    assert data2 == "computed_data"
    assert call_count[0] == 2  # Lazy recomputed, but cache hit
