"""
PHASE 11.1: Circuit Breaker Pattern

Implements circuit breaker pattern for fault isolation and system stability.

Features:
- Three states: CLOSED, OPEN, HALF_OPEN
- Automatic state transitions based on failure rate
- Configurable thresholds and timeouts
- Failure tracking and statistics
- Support for async operations
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failing, reject requests immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitStats:
    """Circuit breaker statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successful_requests + self.failed_requests
        if total == 0:
            return 1.0
        return self.successful_requests / total

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker for fault isolation.

    Protects against cascading failures by failing fast when
    a service is unhealthy.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        failure_rate_threshold: float = 0.5,
        min_requests: int = 10,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures to open circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds to wait before transitioning to half-open
            failure_rate_threshold: Failure rate to open circuit (0.0-1.0)
            min_requests: Minimum requests before checking failure rate
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.failure_rate_threshold = failure_rate_threshold
        self.min_requests = min_requests

        # State
        self.state = CircuitState.CLOSED
        self.state_changed_at = time.time()

        # Statistics
        self.stats = CircuitStats()

        # Consecutive counters (reset on state change)
        self.consecutive_failures = 0
        self.consecutive_successes = 0

    def _should_open(self) -> bool:
        """Check if circuit should open."""
        # Check consecutive failures
        if self.consecutive_failures >= self.failure_threshold:
            return True

        # Check failure rate (only if we have enough requests)
        if self.stats.total_requests >= self.min_requests:
            if self.stats.failure_rate >= self.failure_rate_threshold:
                return True

        return False

    def _should_close(self) -> bool:
        """Check if circuit should close from half-open."""
        return self.consecutive_successes >= self.success_threshold

    def _can_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.state != CircuitState.OPEN:
            return False

        elapsed = time.time() - self.state_changed_at
        return elapsed >= self.timeout

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        self.state_changed_at = time.time()
        self.stats.state_changes += 1

        # Reset consecutive counters on state change
        self.consecutive_failures = 0
        self.consecutive_successes = 0

        print(f"[CircuitBreaker] {self.name}: {old_state.value} -> {new_state.value}")

    def _record_success(self):
        """Record successful request."""
        self.stats.total_requests += 1
        self.stats.successful_requests += 1
        self.stats.last_success_time = time.time()

        self.consecutive_successes += 1
        self.consecutive_failures = 0

        # Check state transitions
        if self.state == CircuitState.HALF_OPEN:
            if self._should_close():
                self._transition_to(CircuitState.CLOSED)

    def _record_failure(self):
        """Record failed request."""
        self.stats.total_requests += 1
        self.stats.failed_requests += 1
        self.stats.last_failure_time = time.time()

        self.consecutive_failures += 1
        self.consecutive_successes = 0

        # Check state transitions
        if self.state == CircuitState.CLOSED:
            if self._should_open():
                self._transition_to(CircuitState.OPEN)

        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            self._transition_to(CircuitState.OPEN)

    async def call(
        self,
        func: Callable[..., T],
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function raises
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if we can attempt reset
            if self._can_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                # Circuit still open, reject request
                self.stats.rejected_requests += 1
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        # Execute function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            self._record_success()

            return result

        except Exception as e:
            # Record failure
            self._record_failure()
            raise

    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "rejected_requests": self.stats.rejected_requests,
            "success_rate": self.stats.success_rate,
            "failure_rate": self.stats.failure_rate,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "state_changes": self.stats.state_changes,
            "state_duration": time.time() - self.state_changed_at,
        }

    def reset(self):
        """Reset circuit breaker to closed state."""
        self._transition_to(CircuitState.CLOSED)
        self.consecutive_failures = 0
        self.consecutive_successes = 0


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.

    Allows centralized management and monitoring of all circuit breakers.
    """

    def __init__(self):
        """Initialize registry."""
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        **kwargs,
    ) -> CircuitBreaker:
        """
        Get existing circuit breaker or create new one.

        Args:
            name: Circuit breaker name
            **kwargs: CircuitBreaker initialization arguments

        Returns:
            CircuitBreaker instance
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name=name, **kwargs)

        return self.breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self.breakers.get(name)

    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {
            name: breaker.get_statistics()
            for name, breaker in self.breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()


# Global registry singleton
_global_registry: Optional[CircuitBreakerRegistry] = None


def get_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CircuitBreakerRegistry()
    return _global_registry
