"""
Lazy Loading Utilities

Provides lazy initialization for heavy components to improve startup time
and reduce memory usage until components are actually needed.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict
from functools import wraps
import importlib
import threading

T = TypeVar('T')


class LazyLoader(Generic[T]):
    """
    Lazy loader that defers object creation until first access.

    Usage:
        # Defer heavy initialization
        memory_manager = LazyLoader(lambda: MemoryManager(config))

        # Access triggers creation
        memory_manager.get().process_message(...)

        # Or use as context manager
        with LazyLoader(lambda: HeavyResource()) as resource:
            resource.do_work()
    """

    def __init__(
        self,
        factory: Callable[[], T],
        thread_safe: bool = True
    ):
        """
        Initialize lazy loader.

        Args:
            factory: Callable that creates the object
            thread_safe: Whether to use thread locking
        """
        self._factory = factory
        self._instance: Optional[T] = None
        self._initialized = False
        self._lock = threading.Lock() if thread_safe else None

    def get(self) -> T:
        """Get or create the instance."""
        if self._initialized:
            return self._instance

        if self._lock:
            with self._lock:
                if not self._initialized:
                    self._instance = self._factory()
                    self._initialized = True
        else:
            self._instance = self._factory()
            self._initialized = True

        return self._instance

    def is_initialized(self) -> bool:
        """Check if instance has been created."""
        return self._initialized

    def reset(self):
        """Reset to uninitialized state."""
        if self._lock:
            with self._lock:
                self._instance = None
                self._initialized = False
        else:
            self._instance = None
            self._initialized = False

    def __enter__(self) -> T:
        return self.get()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the lazy instance."""
        return getattr(self.get(), name)


def lazy_property(func: Callable[[Any], T]) -> property:
    """
    Decorator for lazy property initialization.

    The property value is computed once on first access and cached.
    Thread-safe: uses a lock to prevent race conditions.

    Usage:
        class MyClass:
            @lazy_property
            def heavy_resource(self):
                return load_heavy_resource()
    """
    attr_name = f'_lazy_{func.__name__}'
    lock_name = f'_lazy_lock_{func.__name__}'

    @wraps(func)
    def wrapper(self):
        # Fast path: already initialized
        if hasattr(self, attr_name):
            return getattr(self, attr_name)

        # Get or create lock for this property
        if not hasattr(self, lock_name):
            # Use a class-level lock for initializing instance locks
            cls_lock_name = f'_lazy_cls_lock_{func.__name__}'
            cls = type(self)
            if not hasattr(cls, cls_lock_name):
                setattr(cls, cls_lock_name, threading.Lock())
            with getattr(cls, cls_lock_name):
                if not hasattr(self, lock_name):
                    setattr(self, lock_name, threading.Lock())

        # Thread-safe initialization
        with getattr(self, lock_name):
            if not hasattr(self, attr_name):
                setattr(self, attr_name, func(self))
            return getattr(self, attr_name)

    return property(wrapper)


class LazyModule:
    """
    Lazy module loader that defers import until first attribute access.

    Usage:
        # Instead of: import numpy as np
        np = LazyModule('numpy')

        # numpy is only imported when first used
        arr = np.array([1, 2, 3])
    """

    def __init__(self, module_name: str):
        """
        Initialize lazy module.

        Args:
            module_name: Name of module to import
        """
        self._module_name = module_name
        self._module = None
        self._lock = threading.Lock()

    def _load(self):
        """Load the module if not already loaded."""
        if self._module is None:
            with self._lock:
                if self._module is None:
                    self._module = importlib.import_module(self._module_name)

    def __getattr__(self, name: str) -> Any:
        self._load()
        return getattr(self._module, name)

    def __dir__(self):
        self._load()
        return dir(self._module)


class LazyDict(dict):
    """
    Dictionary with lazy value initialization.

    Values are computed on first access using provided factory functions.

    Usage:
        config = LazyDict({
            'db': lambda: connect_database(),
            'cache': lambda: init_cache(),
        })

        # Database connection made only when accessed
        db = config['db']
    """

    def __init__(self, factories: Dict[str, Callable[[], Any]] = None):
        super().__init__()
        self._factories = factories or {}
        self._computed = set()

    def __getitem__(self, key: str) -> Any:
        if key not in self._computed and key in self._factories:
            super().__setitem__(key, self._factories[key]())
            self._computed.add(key)
        return super().__getitem__(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def register(self, key: str, factory: Callable[[], Any]):
        """Register a lazy factory for a key."""
        self._factories[key] = factory

    def is_computed(self, key: str) -> bool:
        """Check if a key has been computed."""
        return key in self._computed


class LazyMemoryLoader:
    """
    Specialized lazy loader for memory system components.

    Defers initialization of heavy memory components until needed.

    Usage:
        loader = LazyMemoryLoader(config)

        # STM created on first access
        stm = loader.short_term

        # LTM created on first access
        ltm = loader.long_term
    """

    def __init__(self, config: Any = None):
        """
        Initialize memory loader.

        Args:
            config: Memory configuration
        """
        self._config = config
        self._stm = None
        self._ltm = None
        self._entity = None
        self._lock = threading.Lock()

    @lazy_property
    def short_term(self):
        """Lazy short-term memory."""
        from memory import ShortTermMemory, STMConfig
        return ShortTermMemory(config=self._config.stm_config if self._config else STMConfig())

    @lazy_property
    def long_term(self):
        """Lazy long-term memory."""
        from memory import LongTermMemory, LTMConfig
        return LongTermMemory(config=self._config.ltm_config if self._config else LTMConfig())

    @lazy_property
    def entity(self):
        """Lazy entity memory."""
        from memory import EntityMemory, EntityConfig
        return EntityMemory(config=self._config.entity_config if self._config else EntityConfig())

    def initialize_all(self):
        """Force initialization of all components."""
        _ = self.short_term
        _ = self.long_term
        _ = self.entity


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'LazyLoader',
    'lazy_property',
    'LazyModule',
    'LazyDict',
    'LazyMemoryLoader',
]
