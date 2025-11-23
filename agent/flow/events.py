"""
Flow Event Handling System

Event bus and event handling for flow communication and monitoring.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of flow events"""
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_RETRYING = "step_retrying"
    STEP_SKIPPED = "step_skipped"
    FLOW_STARTED = "flow_started"
    FLOW_COMPLETED = "flow_completed"
    FLOW_FAILED = "flow_failed"
    FLOW_PAUSED = "flow_paused"
    FLOW_RESUMED = "flow_resumed"
    FLOW_CANCELLED = "flow_cancelled"
    STATE_CHANGED = "state_changed"
    CUSTOM = "custom"


@dataclass
class FlowEvent:
    """Event in flow execution"""
    type: EventType
    source: str
    data: Any
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "type": self.type.value,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowEvent':
        """Create event from dictionary"""
        return cls(
            type=EventType(data["type"]),
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


class EventBus:
    """Event bus for flow communication"""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._event_history: List[FlowEvent] = []
        self._async_listeners: Dict[str, List[Callable]] = {}
        self._max_history: int = 1000

    def emit(self, event: FlowEvent):
        """Emit an event to all listeners"""
        self._record_event(event)

        # Notify sync listeners
        for listener in self._listeners.get(event.type.value, []):
            try:
                listener(event)
            except Exception as e:
                logger.exception(f"Error in event listener for {event.type.value}: {e}")

        # Notify wildcard listeners
        for listener in self._listeners.get("*", []):
            try:
                listener(event)
            except Exception as e:
                logger.exception(f"Error in wildcard listener: {e}")

    async def emit_async(self, event: FlowEvent):
        """Emit event asynchronously"""
        self._record_event(event)

        # Gather all async listeners
        tasks = []

        for listener in self._async_listeners.get(event.type.value, []):
            if asyncio.iscoroutinefunction(listener):
                tasks.append(listener(event))
            else:
                listener(event)

        for listener in self._async_listeners.get("*", []):
            if asyncio.iscoroutinefunction(listener):
                tasks.append(listener(event))
            else:
                listener(event)

        # Also notify sync listeners
        for listener in self._listeners.get(event.type.value, []):
            try:
                listener(event)
            except Exception as e:
                logger.exception(f"Error in event listener for {event.type.value}: {e}")

        for listener in self._listeners.get("*", []):
            try:
                listener(event)
            except Exception as e:
                logger.exception(f"Error in wildcard listener: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _record_event(self, event: FlowEvent):
        """Record event in history"""
        self._event_history.append(event)
        # Trim history if needed
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def on(self, event_type: str, listener: Callable):
        """Register an event listener"""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        return self  # For chaining

    def on_async(self, event_type: str, listener: Callable):
        """Register an async event listener"""
        if event_type not in self._async_listeners:
            self._async_listeners[event_type] = []
        self._async_listeners[event_type].append(listener)
        return self  # For chaining

    def off(self, event_type: str, listener: Callable = None):
        """Remove an event listener"""
        if listener is None:
            # Remove all listeners for this event type
            self._listeners.pop(event_type, None)
            self._async_listeners.pop(event_type, None)
        else:
            if event_type in self._listeners and listener in self._listeners[event_type]:
                self._listeners[event_type].remove(listener)
            if event_type in self._async_listeners and listener in self._async_listeners[event_type]:
                self._async_listeners[event_type].remove(listener)

    def once(self, event_type: str, listener: Callable):
        """Register a one-time event listener"""
        def wrapper(event):
            listener(event)
            self.off(event_type, wrapper)
        self.on(event_type, wrapper)
        return self

    def get_history(self, event_type: Optional[str] = None, limit: int = None) -> List[FlowEvent]:
        """Get event history"""
        if event_type:
            events = [e for e in self._event_history if e.type.value == event_type]
        else:
            events = self._event_history.copy()

        if limit:
            events = events[-limit:]

        return events

    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()

    def clear_listeners(self):
        """Clear all listeners"""
        self._listeners.clear()
        self._async_listeners.clear()

    def get_listener_count(self, event_type: str = None) -> int:
        """Get count of listeners"""
        if event_type:
            sync = len(self._listeners.get(event_type, []))
            async_ = len(self._async_listeners.get(event_type, []))
            return sync + async_
        else:
            total = sum(len(v) for v in self._listeners.values())
            total += sum(len(v) for v in self._async_listeners.values())
            return total


class EventMatcher:
    """Match events based on patterns"""

    def __init__(self):
        self.conditions: List[Callable[[FlowEvent], bool]] = []

    def type(self, event_type: EventType) -> 'EventMatcher':
        """Match event type"""
        self.conditions.append(lambda e: e.type == event_type)
        return self

    def source(self, source: str) -> 'EventMatcher':
        """Match event source"""
        self.conditions.append(lambda e: e.source == source)
        return self

    def source_pattern(self, pattern: str) -> 'EventMatcher':
        """Match event source with pattern (supports * wildcard)"""
        import fnmatch
        self.conditions.append(lambda e: fnmatch.fnmatch(e.source, pattern))
        return self

    def data_contains(self, key: str, value: Any = None) -> 'EventMatcher':
        """Match event data content"""
        if value is None:
            self.conditions.append(lambda e: key in e.data if isinstance(e.data, dict) else False)
        else:
            self.conditions.append(
                lambda e: e.data.get(key) == value if isinstance(e.data, dict) else False
            )
        return self

    def data_matches(self, predicate: Callable[[Any], bool]) -> 'EventMatcher':
        """Match event data with custom predicate"""
        self.conditions.append(lambda e: predicate(e.data))
        return self

    def custom(self, condition: Callable[[FlowEvent], bool]) -> 'EventMatcher':
        """Add custom condition"""
        self.conditions.append(condition)
        return self

    def matches(self, event: FlowEvent) -> bool:
        """Check if event matches all conditions"""
        return all(cond(event) for cond in self.conditions)

    def __call__(self, event: FlowEvent) -> bool:
        """Make matcher callable"""
        return self.matches(event)


def or_(*matchers: EventMatcher) -> Callable[[FlowEvent], bool]:
    """Combine matchers with OR logic"""
    def combined(event: FlowEvent) -> bool:
        return any(m.matches(event) if isinstance(m, EventMatcher) else m(event) for m in matchers)
    return combined


def and_(*matchers: EventMatcher) -> Callable[[FlowEvent], bool]:
    """Combine matchers with AND logic"""
    def combined(event: FlowEvent) -> bool:
        return all(m.matches(event) if isinstance(m, EventMatcher) else m(event) for m in matchers)
    return combined


def not_(matcher: EventMatcher) -> Callable[[FlowEvent], bool]:
    """Negate a matcher"""
    def negated(event: FlowEvent) -> bool:
        if isinstance(matcher, EventMatcher):
            return not matcher.matches(event)
        return not matcher(event)
    return negated


class EventAggregator:
    """Aggregate events over time or count"""

    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self._aggregated: Dict[str, List[FlowEvent]] = {}

    def collect(self, event_type: str, key_fn: Callable[[FlowEvent], str] = None):
        """Start collecting events of a type"""
        def collector(event: FlowEvent):
            key = key_fn(event) if key_fn else event_type
            if key not in self._aggregated:
                self._aggregated[key] = []
            self._aggregated[key].append(event)

        self.event_bus.on(event_type, collector)

    def get(self, key: str) -> List[FlowEvent]:
        """Get collected events"""
        return self._aggregated.get(key, [])

    def count(self, key: str) -> int:
        """Get count of collected events"""
        return len(self._aggregated.get(key, []))

    def clear(self, key: str = None):
        """Clear collected events"""
        if key:
            self._aggregated.pop(key, None)
        else:
            self._aggregated.clear()


# Convenience functions for creating events

def step_started(step_name: str, input_data: Any = None, **metadata) -> FlowEvent:
    """Create a step started event"""
    return FlowEvent(
        type=EventType.STEP_STARTED,
        source=step_name,
        data={"input": input_data},
        metadata=metadata
    )


def step_completed(step_name: str, output: Any = None, **metadata) -> FlowEvent:
    """Create a step completed event"""
    return FlowEvent(
        type=EventType.STEP_COMPLETED,
        source=step_name,
        data={"output": output},
        metadata=metadata
    )


def step_failed(step_name: str, error: str, **metadata) -> FlowEvent:
    """Create a step failed event"""
    return FlowEvent(
        type=EventType.STEP_FAILED,
        source=step_name,
        data={"error": error},
        metadata=metadata
    )


def flow_started(flow_name: str, input_data: Any = None, **metadata) -> FlowEvent:
    """Create a flow started event"""
    return FlowEvent(
        type=EventType.FLOW_STARTED,
        source=flow_name,
        data={"input": input_data},
        metadata=metadata
    )


def flow_completed(flow_name: str, result: Any = None, **metadata) -> FlowEvent:
    """Create a flow completed event"""
    return FlowEvent(
        type=EventType.FLOW_COMPLETED,
        source=flow_name,
        data={"result": result},
        metadata=metadata
    )


def flow_failed(flow_name: str, error: str, **metadata) -> FlowEvent:
    """Create a flow failed event"""
    return FlowEvent(
        type=EventType.FLOW_FAILED,
        source=flow_name,
        data={"error": error},
        metadata=metadata
    )
