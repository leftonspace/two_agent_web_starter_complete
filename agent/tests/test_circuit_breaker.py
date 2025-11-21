"""
PHASE 11.1: Circuit Breaker Tests

Tests for circuit breaker pattern implementation.
"""

import asyncio
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    CircuitStats,
    CircuitBreakerRegistry,
    get_registry,
)


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker instance."""
    return CircuitBreaker(
        name="test_circuit",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0,
    )


def test_circuit_breaker_initialization(circuit_breaker):
    """Test circuit breaker initialization."""
    assert circuit_breaker.name == "test_circuit"
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.failure_threshold == 3
    assert circuit_breaker.success_threshold == 2
    assert circuit_breaker.stats.total_requests == 0


def test_circuit_stats_success_rate():
    """Test circuit stats success rate calculation."""
    stats = CircuitStats(
        total_requests=10,
        successful_requests=8,
        failed_requests=2,
    )

    assert stats.success_rate == 0.8
    assert stats.failure_rate == 0.2


def test_circuit_stats_no_requests():
    """Test stats with no requests."""
    stats = CircuitStats()

    assert stats.success_rate == 1.0
    assert stats.failure_rate == 0.0


@pytest.mark.asyncio
async def test_circuit_closed_success(circuit_breaker):
    """Test successful request in closed state."""
    async def success_func():
        return "success"

    result = await circuit_breaker.call(success_func)

    assert result == "success"
    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.stats.successful_requests == 1
    assert circuit_breaker.stats.failed_requests == 0


@pytest.mark.asyncio
async def test_circuit_opens_after_failures(circuit_breaker):
    """Test circuit opens after threshold failures."""
    async def fail_func():
        raise Exception("Failure")

    # First 3 failures should open circuit
    for i in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(fail_func)

    # Circuit should now be open
    assert circuit_breaker.state == CircuitState.OPEN
    assert circuit_breaker.stats.failed_requests == 3


@pytest.mark.asyncio
async def test_circuit_rejects_when_open(circuit_breaker):
    """Test circuit rejects requests when open."""
    # Cause failures to open circuit
    async def fail_func():
        raise Exception("Failure")

    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(fail_func)

    assert circuit_breaker.state == CircuitState.OPEN

    # Now requests should be rejected immediately
    async def success_func():
        return "success"

    with pytest.raises(CircuitBreakerOpenError):
        await circuit_breaker.call(success_func)

    assert circuit_breaker.stats.rejected_requests == 1


@pytest.mark.asyncio
async def test_circuit_half_open_after_timeout(circuit_breaker):
    """Test circuit transitions to half-open after timeout."""
    # Open the circuit
    async def fail_func():
        raise Exception("Failure")

    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(fail_func)

    assert circuit_breaker.state == CircuitState.OPEN

    # Wait for timeout
    await asyncio.sleep(circuit_breaker.timeout + 0.1)

    # Next request should transition to half-open
    async def success_func():
        return "success"

    result = await circuit_breaker.call(success_func)

    assert result == "success"
    assert circuit_breaker.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_circuit_closes_from_half_open(circuit_breaker):
    """Test circuit closes after successes in half-open."""
    # Open the circuit
    async def fail_func():
        raise Exception("Failure")

    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(fail_func)

    # Wait and transition to half-open
    await asyncio.sleep(circuit_breaker.timeout + 0.1)

    async def success_func():
        return "success"

    # First success transitions to half-open
    await circuit_breaker.call(success_func)
    assert circuit_breaker.state == CircuitState.HALF_OPEN

    # Second success should close circuit
    await circuit_breaker.call(success_func)
    assert circuit_breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_reopens_from_half_open(circuit_breaker):
    """Test circuit reopens on failure in half-open."""
    # Open the circuit
    async def fail_func():
        raise Exception("Failure")

    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(fail_func)

    # Wait and transition to half-open
    await asyncio.sleep(circuit_breaker.timeout + 0.1)

    # First request succeeds -> half-open
    async def success_func():
        return "success"

    await circuit_breaker.call(success_func)
    assert circuit_breaker.state == CircuitState.HALF_OPEN

    # Next request fails -> immediately reopens
    with pytest.raises(Exception):
        await circuit_breaker.call(fail_func)

    assert circuit_breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_sync_function_support(circuit_breaker):
    """Test circuit breaker with sync functions."""
    def sync_func():
        return "success"

    result = await circuit_breaker.call(sync_func)

    assert result == "success"


def test_get_statistics(circuit_breaker):
    """Test getting statistics."""
    stats = circuit_breaker.get_statistics()

    assert stats["name"] == "test_circuit"
    assert stats["state"] == "closed"
    assert stats["total_requests"] == 0
    assert "success_rate" in stats
    assert "failure_rate" in stats


def test_reset_circuit(circuit_breaker):
    """Test resetting circuit breaker."""
    # Set some state
    circuit_breaker.state = CircuitState.OPEN
    circuit_breaker.consecutive_failures = 5

    # Reset
    circuit_breaker.reset()

    assert circuit_breaker.state == CircuitState.CLOSED
    assert circuit_breaker.consecutive_failures == 0


def test_failure_rate_threshold():
    """Test opening based on failure rate."""
    cb = CircuitBreaker(
        name="rate_test",
        failure_threshold=100,  # High threshold
        failure_rate_threshold=0.5,  # 50% failure rate
        min_requests=10,
    )

    # Need at least min_requests before checking rate
    # So first 9 failures won't open circuit
    for _ in range(9):
        cb._record_failure()

    assert cb.state == CircuitState.CLOSED

    # 10th failure makes 10 total requests with 100% failure rate
    # Should open circuit
    cb._record_failure()

    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_registry():
    """Test circuit breaker registry."""
    registry = CircuitBreakerRegistry()

    # Create circuit breakers
    cb1 = registry.get_or_create("service1", failure_threshold=5)
    cb2 = registry.get_or_create("service2", failure_threshold=3)

    assert cb1.name == "service1"
    assert cb2.name == "service2"

    # Get existing
    cb1_again = registry.get_or_create("service1")
    assert cb1 is cb1_again

    # Get by name
    assert registry.get("service1") is cb1
    assert registry.get("nonexistent") is None


def test_registry_statistics():
    """Test getting all statistics from registry."""
    registry = CircuitBreakerRegistry()

    cb1 = registry.get_or_create("service1")
    cb2 = registry.get_or_create("service2")

    all_stats = registry.get_all_statistics()

    assert "service1" in all_stats
    assert "service2" in all_stats
    assert all_stats["service1"]["name"] == "service1"


def test_registry_reset_all():
    """Test resetting all circuit breakers."""
    registry = CircuitBreakerRegistry()

    cb1 = registry.get_or_create("service1")
    cb2 = registry.get_or_create("service2")

    # Set some state
    cb1.state = CircuitState.OPEN
    cb2.state = CircuitState.HALF_OPEN

    # Reset all
    registry.reset_all()

    assert cb1.state == CircuitState.CLOSED
    assert cb2.state == CircuitState.CLOSED


def test_global_registry():
    """Test global registry singleton."""
    registry1 = get_registry()
    registry2 = get_registry()

    # Should be same instance
    assert registry1 is registry2


@pytest.mark.asyncio
async def test_consecutive_counter_reset():
    """Test consecutive counters reset on state change."""
    cb = CircuitBreaker(
        name="counter_test",
        failure_threshold=3,
    )

    # Build up failures
    async def fail_func():
        raise Exception("Fail")

    for _ in range(3):
        with pytest.raises(Exception):
            await cb.call(fail_func)

    assert cb.state == CircuitState.OPEN
    assert cb.consecutive_failures == 0  # Reset on state change

    # Wait for timeout
    await asyncio.sleep(cb.timeout + 0.1)

    # Success transitions to half-open, resets counters
    async def success_func():
        return "ok"

    await cb.call(success_func)

    assert cb.state == CircuitState.HALF_OPEN
    assert cb.consecutive_successes == 1
    assert cb.consecutive_failures == 0


@pytest.mark.asyncio
async def test_state_change_tracking(circuit_breaker):
    """Test state changes are tracked."""
    initial_changes = circuit_breaker.stats.state_changes

    # Open circuit
    async def fail_func():
        raise Exception("Fail")

    for _ in range(3):
        with pytest.raises(Exception):
            await circuit_breaker.call(fail_func)

    # Should have one state change (CLOSED -> OPEN)
    assert circuit_breaker.stats.state_changes == initial_changes + 1


@pytest.mark.asyncio
async def test_timing_tracking(circuit_breaker):
    """Test last success/failure time tracking."""
    # Success
    async def success_func():
        return "ok"

    await circuit_breaker.call(success_func)

    assert circuit_breaker.stats.last_success_time is not None
    last_success = circuit_breaker.stats.last_success_time

    # Failure
    async def fail_func():
        raise Exception("Fail")

    with pytest.raises(Exception):
        await circuit_breaker.call(fail_func)

    assert circuit_breaker.stats.last_failure_time is not None
    assert circuit_breaker.stats.last_success_time == last_success
