"""
PHASE 11.4: Lazy Loading

Deferred computation and lazy loading for performance optimization.

Features:
- Lazy value evaluation
- Lazy property decorator
- Async lazy loading
- Dependency tracking
- Memoization
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Generic, Optional, TypeVar
from functools import wraps

T = TypeVar('T')


class LazyValue(Generic[T]):
    """
    Lazy value that is computed on first access.

    The value is computed only once and cached for subsequent accesses.
    """

    def __init__(self, compute_fn: Callable[[], T]):
        """
        Initialize lazy value.

        Args:
            compute_fn: Function to compute value
        """
        self._compute_fn = compute_fn
        self._value: Optional[T] = None
        self._computed = False
        self._lock = asyncio.Lock()

    def get(self) -> T:
        """
        Get value, computing if necessary.

        Returns:
            Computed value
        """
        if not self._computed:
            self._value = self._compute_fn()
            self._computed = True

        return self._value

    async def get_async(self) -> T:
        """
        Get value asynchronously, computing if necessary.

        Returns:
            Computed value
        """
        if not self._computed:
            async with self._lock:
                # Double-check after acquiring lock
                if not self._computed:
                    if asyncio.iscoroutinefunction(self._compute_fn):
                        self._value = await self._compute_fn()
                    else:
                        self._value = self._compute_fn()

                    self._computed = True

        return self._value

    @property
    def is_computed(self) -> bool:
        """Check if value has been computed."""
        return self._computed

    def reset(self):
        """Reset lazy value to uncomputed state."""
        self._value = None
        self._computed = False

    def __repr__(self) -> str:
        if self._computed:
            return f"LazyValue(computed={self._value})"
        else:
            return "LazyValue(not computed)"


def lazy_property(func: Callable) -> property:
    """
    Decorator for lazy properties.

    The property is computed once and cached on the instance.

    Usage:
        class MyClass:
            @lazy_property
            def expensive_value(self):
                # Expensive computation
                return result
    """
    attr_name = f"_lazy_{func.__name__}"

    @wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            value = func(self)
            setattr(self, attr_name, value)

        return getattr(self, attr_name)

    return property(wrapper)


class LazyLoader:
    """
    Lazy loader for managing multiple lazy values.

    Features:
    - Named lazy values
    - Dependency tracking
    - Batch loading
    - Statistics
    """

    def __init__(self):
        """Initialize lazy loader."""
        self.lazy_values: Dict[str, LazyValue] = {}
        self.dependencies: Dict[str, list[str]] = {}

        # Statistics
        self.access_count: Dict[str, int] = {}
        self.compute_count: Dict[str, int] = {}

    def register(
        self,
        name: str,
        compute_fn: Callable[[], Any],
        depends_on: Optional[list[str]] = None,
    ):
        """
        Register a lazy value.

        Args:
            name: Value name
            compute_fn: Function to compute value
            depends_on: List of dependency names
        """
        self.lazy_values[name] = LazyValue(compute_fn)

        if depends_on:
            self.dependencies[name] = depends_on

        self.access_count[name] = 0
        self.compute_count[name] = 0

    async def get(self, name: str) -> Any:
        """
        Get lazy value by name.

        Args:
            name: Value name

        Returns:
            Computed value

        Raises:
            KeyError: If name not registered
        """
        if name not in self.lazy_values:
            raise KeyError(f"Lazy value '{name}' not registered")

        lazy_value = self.lazy_values[name]

        # Track access
        self.access_count[name] += 1

        # Load dependencies first
        if name in self.dependencies:
            for dep_name in self.dependencies[name]:
                await self.get(dep_name)

        # Track computation
        was_computed = lazy_value.is_computed

        # Get value
        value = await lazy_value.get_async()

        if not was_computed:
            self.compute_count[name] += 1

        return value

    def get_sync(self, name: str) -> Any:
        """
        Get lazy value synchronously.

        Args:
            name: Value name

        Returns:
            Computed value
        """
        if name not in self.lazy_values:
            raise KeyError(f"Lazy value '{name}' not registered")

        lazy_value = self.lazy_values[name]

        # Track access
        self.access_count[name] += 1

        # Track computation
        was_computed = lazy_value.is_computed

        # Get value
        value = lazy_value.get()

        if not was_computed:
            self.compute_count[name] += 1

        return value

    async def preload(self, names: list[str]):
        """
        Preload multiple values.

        Args:
            names: List of value names to preload
        """
        tasks = [self.get(name) for name in names]
        await asyncio.gather(*tasks)

    def reset(self, name: Optional[str] = None):
        """
        Reset lazy value(s) to uncomputed state.

        Args:
            name: Value name (None = reset all)
        """
        if name:
            if name in self.lazy_values:
                self.lazy_values[name].reset()
        else:
            for lazy_value in self.lazy_values.values():
                lazy_value.reset()

    def is_computed(self, name: str) -> bool:
        """
        Check if value has been computed.

        Args:
            name: Value name

        Returns:
            True if computed
        """
        if name not in self.lazy_values:
            return False

        return self.lazy_values[name].is_computed

    def get_statistics(self) -> Dict[str, Any]:
        """Get lazy loading statistics."""
        total_registered = len(self.lazy_values)
        total_computed = sum(
            1 for lv in self.lazy_values.values()
            if lv.is_computed
        )

        return {
            "total_registered": total_registered,
            "total_computed": total_computed,
            "compute_rate": total_computed / total_registered if total_registered > 0 else 0,
            "access_counts": self.access_count.copy(),
            "compute_counts": self.compute_count.copy(),
        }


class LazyLoadingMixin:
    """
    Mixin for adding lazy loading capabilities to classes.

    Usage:
        class MyClass(LazyLoadingMixin):
            def __init__(self):
                super().__init__()
                self.register_lazy("data", self._load_data)

            def _load_data(self):
                # Load data
                return data
    """

    def __init__(self):
        """Initialize lazy loading mixin."""
        self._lazy_loader = LazyLoader()

    def register_lazy(
        self,
        name: str,
        compute_fn: Callable[[], Any],
        depends_on: Optional[list[str]] = None,
    ):
        """Register a lazy value."""
        self._lazy_loader.register(name, compute_fn, depends_on)

    async def get_lazy(self, name: str) -> Any:
        """Get lazy value."""
        return await self._lazy_loader.get(name)

    def get_lazy_sync(self, name: str) -> Any:
        """Get lazy value synchronously."""
        return self._lazy_loader.get_sync(name)

    def reset_lazy(self, name: Optional[str] = None):
        """Reset lazy value(s)."""
        self._lazy_loader.reset(name)


class AsyncLazyIterator:
    """
    Async iterator that loads items lazily.

    Useful for large datasets that don't fit in memory.
    """

    def __init__(
        self,
        loader: Callable[[int], Any],
        total_items: int,
        batch_size: int = 10,
    ):
        """
        Initialize async lazy iterator.

        Args:
            loader: Function to load item by index
            total_items: Total number of items
            batch_size: Number of items to load at once
        """
        self.loader = loader
        self.total_items = total_items
        self.batch_size = batch_size

        self.current_index = 0
        self.current_batch = []
        self.batch_index = 0

    def __aiter__(self):
        """Return iterator."""
        return self

    async def __anext__(self):
        """Get next item."""
        # Load next batch if needed
        if self.batch_index >= len(self.current_batch):
            if self.current_index >= self.total_items:
                raise StopAsyncIteration

            # Load batch
            batch_end = min(
                self.current_index + self.batch_size,
                self.total_items,
            )

            if asyncio.iscoroutinefunction(self.loader):
                self.current_batch = [
                    await self.loader(i)
                    for i in range(self.current_index, batch_end)
                ]
            else:
                self.current_batch = [
                    self.loader(i)
                    for i in range(self.current_index, batch_end)
                ]

            self.current_index = batch_end
            self.batch_index = 0

        # Get item from batch
        item = self.current_batch[self.batch_index]
        self.batch_index += 1

        return item


def lazy_async(func: Callable) -> Callable:
    """
    Decorator for lazy async functions.

    The function result is computed once and cached.

    Usage:
        @lazy_async
        async def expensive_operation():
            # Expensive async operation
            return result
    """
    cache = {}
    lock = asyncio.Lock()

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Create cache key
        key = (args, tuple(sorted(kwargs.items())))

        if key not in cache:
            async with lock:
                # Double-check after acquiring lock
                if key not in cache:
                    cache[key] = await func(*args, **kwargs)

        return cache[key]

    return wrapper
