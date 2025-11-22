"""
Flow Control Decorators

Decorators for defining flow steps, routing, and event handling.
"""

from typing import Callable, Optional, List, Union, Any, Dict
from functools import wraps
import inspect
import asyncio
from dataclasses import dataclass, field


@dataclass
class StepMetadata:
    """Metadata for a flow step"""
    name: str
    type: str
    description: str = ""
    triggers: List[str] = field(default_factory=list)
    router_source: Optional[str] = None
    timeout: Optional[int] = None
    retries: int = 0
    retry_delay: float = 1.0


# Global registry for decorated methods
_step_registry: Dict[str, Dict[str, StepMetadata]] = {}


def _get_class_name(func: Callable) -> str:
    """Get the class name from a function's qualified name"""
    if '.' in func.__qualname__:
        return func.__qualname__.rsplit('.', 1)[0]
    return ""


def _register_step(func: Callable, metadata: StepMetadata):
    """Register a step in the global registry"""
    class_name = _get_class_name(func)
    if class_name:
        if class_name not in _step_registry:
            _step_registry[class_name] = {}
        _step_registry[class_name][metadata.name] = metadata


def start(description: str = "", timeout: Optional[int] = None):
    """Decorator to mark the flow entry point

    Args:
        description: Description of the start step
        timeout: Optional timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        # Choose wrapper based on function type
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        # Store metadata
        wrapper._flow_metadata = StepMetadata(
            name=func.__name__,
            type="start",
            description=description,
            timeout=timeout
        )

        _register_step(func, wrapper._flow_metadata)

        return wrapper
    return decorator


def listen(*triggers: Union[str, Callable], timeout: Optional[int] = None, retries: int = 0):
    """Decorator to mark a step that listens for specific events

    Args:
        triggers: Event names or step functions to listen for
        timeout: Optional timeout in seconds
        retries: Number of retries on failure
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        # Process triggers
        trigger_names = []
        for trigger in triggers:
            if callable(trigger):
                if hasattr(trigger, '__name__'):
                    trigger_names.append(trigger.__name__)
                elif hasattr(trigger, '_flow_metadata'):
                    trigger_names.append(trigger._flow_metadata.name)
                else:
                    trigger_names.append(str(trigger))
            else:
                trigger_names.append(trigger)

        wrapper._flow_metadata = StepMetadata(
            name=func.__name__,
            type="listener",
            triggers=trigger_names,
            timeout=timeout,
            retries=retries
        )

        _register_step(func, wrapper._flow_metadata)

        return wrapper
    return decorator


def router(source: Union[str, Callable], description: str = ""):
    """Decorator for conditional routing based on return value

    The decorated method should return the name of the next step to execute.

    Args:
        source: Source step name or function
        description: Description of the router
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        source_name = source.__name__ if callable(source) else source

        wrapper._flow_metadata = StepMetadata(
            name=func.__name__,
            type="router",
            description=description,
            router_source=source_name
        )

        _register_step(func, wrapper._flow_metadata)

        return wrapper
    return decorator


def step(name: Optional[str] = None, description: str = "", timeout: Optional[int] = None):
    """Generic step decorator

    Args:
        name: Optional step name (defaults to function name)
        description: Description of the step
        timeout: Optional timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        step_name = name or func.__name__

        wrapper._flow_metadata = StepMetadata(
            name=step_name,
            type="step",
            description=description,
            timeout=timeout
        )

        _register_step(func, wrapper._flow_metadata)

        return wrapper
    return decorator


def parallel(*steps: str):
    """Decorator to mark parallel execution paths

    Args:
        steps: Names of steps to execute in parallel
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return await func(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        wrapper._flow_metadata = StepMetadata(
            name=func.__name__,
            type="parallel",
            triggers=list(steps)
        )

        _register_step(func, wrapper._flow_metadata)

        return wrapper
    return decorator


class EventCombinator:
    """Base class for event combinators"""
    def __init__(self, *events):
        self.events = events

    def __str__(self):
        event_names = []
        for e in self.events:
            if callable(e):
                event_names.append(e.__name__ if hasattr(e, '__name__') else str(e))
            else:
                event_names.append(str(e))
        return f"{self.__class__.__name__}({', '.join(event_names)})"

    def get_event_names(self) -> List[str]:
        """Get list of event names"""
        names = []
        for e in self.events:
            if callable(e):
                names.append(e.__name__ if hasattr(e, '__name__') else str(e))
            else:
                names.append(str(e))
        return names


class OrCombinator(EventCombinator):
    """Combines events with OR logic - triggers on any event"""
    pass


class AndCombinator(EventCombinator):
    """Combines events with AND logic - triggers when all events have occurred"""
    pass


def or_(*events: Union[str, Callable]) -> OrCombinator:
    """Trigger on any of the specified events

    Args:
        events: Event names or step functions

    Returns:
        OrCombinator instance
    """
    return OrCombinator(*events)


def and_(*events: Union[str, Callable]) -> AndCombinator:
    """Trigger when all specified events have occurred

    Args:
        events: Event names or step functions

    Returns:
        AndCombinator instance
    """
    return AndCombinator(*events)


def get_flow_metadata(cls: Any) -> Dict[str, StepMetadata]:
    """Get all flow metadata for a class

    Args:
        cls: Class to get metadata for

    Returns:
        Dictionary of step names to metadata
    """
    metadata = {}
    class_name = cls.__name__

    # Check registry
    if class_name in _step_registry:
        metadata.update(_step_registry[class_name])

    # Also check methods directly
    for name in dir(cls):
        try:
            method = getattr(cls, name)
            if hasattr(method, '_flow_metadata'):
                metadata[method._flow_metadata.name] = method._flow_metadata
        except AttributeError:
            continue

    return metadata


# Utility decorators for common patterns

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry a step on failure with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay between retries
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            raise last_error

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_error = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_error

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def timeout(seconds: int):
    """Add timeout to a step

    Args:
        seconds: Timeout in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Step timed out after {seconds} seconds")

            # Only set signal handler on Unix
            try:
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                return result
            except AttributeError:
                # Windows doesn't support SIGALRM
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def validate_input(**validators: Callable[[Any], bool]):
    """Validate step inputs

    Args:
        validators: Mapping of parameter names to validation functions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"Validation failed for parameter '{param_name}': {value}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


def validate_output(validator: Callable[[Any], bool], error_message: str = "Output validation failed"):
    """Validate step output

    Args:
        validator: Validation function that returns True if output is valid
        error_message: Error message if validation fails
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if not validator(result):
                raise ValueError(f"{error_message}: {result}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if not validator(result):
                raise ValueError(f"{error_message}: {result}")

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_step(logger: Callable[[str], None] = print):
    """Log step execution

    Args:
        logger: Logging function (defaults to print)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger(f"Starting step: {func.__name__}")
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                logger(f"Completed step: {func.__name__}")
                return result
            except Exception as e:
                logger(f"Failed step: {func.__name__} - {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger(f"Starting step: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger(f"Completed step: {func.__name__}")
                return result
            except Exception as e:
                logger(f"Failed step: {func.__name__} - {e}")
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def conditional(condition: Callable[..., bool], skip_value: Any = None):
    """Conditionally execute a step

    Args:
        condition: Function that returns True if step should execute
        skip_value: Value to return if step is skipped
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if condition(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            return skip_value

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if condition(*args, **kwargs):
                return func(*args, **kwargs)
            return skip_value

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
