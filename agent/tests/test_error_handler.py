"""
PHASE 11.1: Error Handler Tests

Tests for production-grade error handling and recovery.
"""

import asyncio
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.error_handler import (
    ErrorHandler,
    ErrorCategory,
    RetryableError,
    FatalError,
    UserError,
    NetworkError,
    TimeoutError as CustomTimeoutError,
    RateLimitError,
    ErrorContext,
    with_retry,
)


@pytest.fixture
def error_handler():
    """Create error handler instance."""
    return ErrorHandler(max_retries=3, base_delay=0.1, max_delay=1.0)


def test_error_handler_initialization(error_handler):
    """Test error handler initialization."""
    assert error_handler.max_retries == 3
    assert error_handler.base_delay == 0.1
    assert error_handler.max_delay == 1.0
    assert len(error_handler.error_history) == 0


def test_categorize_retryable_error(error_handler):
    """Test categorizing retryable errors."""
    error = RetryableError("Temporary failure")
    category = error_handler.categorize_error(error)
    assert category == ErrorCategory.RETRYABLE


def test_categorize_fatal_error(error_handler):
    """Test categorizing fatal errors."""
    error = FatalError("Permanent failure")
    category = error_handler.categorize_error(error)
    assert category == ErrorCategory.FATAL


def test_categorize_user_error(error_handler):
    """Test categorizing user errors."""
    error = UserError("Invalid input")
    category = error_handler.categorize_error(error)
    assert category == ErrorCategory.USER


def test_categorize_network_error(error_handler):
    """Test categorizing network errors."""
    error = NetworkError("Connection failed")
    category = error_handler.categorize_error(error)
    assert category == ErrorCategory.NETWORK


def test_categorize_timeout_error(error_handler):
    """Test categorizing timeout errors."""
    error = CustomTimeoutError("Request timed out")
    category = error_handler.categorize_error(error)
    assert category == ErrorCategory.TIMEOUT


def test_categorize_rate_limit_error(error_handler):
    """Test categorizing rate limit errors."""
    error = RateLimitError("Too many requests")
    category = error_handler.categorize_error(error)
    assert category == ErrorCategory.RATE_LIMIT


def test_should_retry_retryable_error(error_handler):
    """Test retry decision for retryable errors."""
    error = RetryableError("Temporary")

    # Should retry on first attempts
    assert error_handler.should_retry(error, 0) is True
    assert error_handler.should_retry(error, 1) is True
    assert error_handler.should_retry(error, 2) is True

    # Should not retry after max retries
    assert error_handler.should_retry(error, 3) is False


def test_should_not_retry_fatal_error(error_handler):
    """Test retry decision for fatal errors."""
    error = FatalError("Permanent")

    # Should never retry fatal errors
    assert error_handler.should_retry(error, 0) is False


def test_should_not_retry_user_error(error_handler):
    """Test retry decision for user errors."""
    error = UserError("Invalid input")

    # Should never retry user errors
    assert error_handler.should_retry(error, 0) is False


def test_calculate_delay(error_handler):
    """Test delay calculation with exponential backoff."""
    # First attempt: base_delay * 2^0 = 0.1
    delay0 = error_handler.calculate_delay(0)
    assert 0.05 <= delay0 <= 0.15  # With jitter

    # Second attempt: base_delay * 2^1 = 0.2
    delay1 = error_handler.calculate_delay(1)
    assert 0.15 <= delay1 <= 0.25

    # Third attempt: base_delay * 2^2 = 0.4
    delay2 = error_handler.calculate_delay(2)
    assert 0.3 <= delay2 <= 0.5


def test_calculate_delay_no_jitter():
    """Test delay calculation without jitter."""
    handler = ErrorHandler(base_delay=1.0, jitter=False)

    assert handler.calculate_delay(0) == 1.0
    assert handler.calculate_delay(1) == 2.0
    assert handler.calculate_delay(2) == 4.0


def test_calculate_delay_max_cap(error_handler):
    """Test delay is capped at max_delay."""
    # With exponential growth, should eventually hit max
    delay = error_handler.calculate_delay(10)
    assert delay <= error_handler.max_delay


@pytest.mark.asyncio
async def test_with_retry_success(error_handler):
    """Test retry with successful function."""
    call_count = [0]

    async def success_func():
        call_count[0] += 1
        return "success"

    result = await error_handler.with_retry(success_func, "test_op")

    assert result == "success"
    assert call_count[0] == 1  # Called once


@pytest.mark.asyncio
async def test_with_retry_eventual_success(error_handler):
    """Test retry with eventually successful function."""
    call_count = [0]

    async def flaky_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise RetryableError("Temporary failure")
        return "success"

    result = await error_handler.with_retry(flaky_func, "test_op")

    assert result == "success"
    assert call_count[0] == 3  # Called 3 times


@pytest.mark.asyncio
async def test_with_retry_all_failures(error_handler):
    """Test retry with all attempts failing."""
    call_count = [0]

    async def always_fail():
        call_count[0] += 1
        raise RetryableError("Always fails")

    with pytest.raises(RetryableError):
        await error_handler.with_retry(always_fail, "test_op")

    assert call_count[0] == 4  # Initial + 3 retries


@pytest.mark.asyncio
async def test_with_retry_fatal_error(error_handler):
    """Test retry with fatal error (no retry)."""
    call_count = [0]

    async def fatal_func():
        call_count[0] += 1
        raise FatalError("Fatal error")

    with pytest.raises(FatalError):
        await error_handler.with_retry(fatal_func, "test_op")

    assert call_count[0] == 1  # Only called once, no retry


@pytest.mark.asyncio
async def test_graceful_degradation_primary_success(error_handler):
    """Test graceful degradation with primary success."""
    primary_called = [False]
    fallback_called = [False]

    async def primary():
        primary_called[0] = True
        return "primary"

    async def fallback():
        fallback_called[0] = True
        return "fallback"

    result = await error_handler.graceful_degradation(primary, fallback, "test_op")

    assert result == "primary"
    assert primary_called[0] is True
    assert fallback_called[0] is False


@pytest.mark.asyncio
async def test_graceful_degradation_fallback(error_handler):
    """Test graceful degradation with fallback."""
    primary_called = [False]
    fallback_called = [False]

    async def primary():
        primary_called[0] = True
        raise NetworkError("Primary failed")

    async def fallback():
        fallback_called[0] = True
        return "fallback"

    result = await error_handler.graceful_degradation(primary, fallback, "test_op")

    assert result == "fallback"
    assert primary_called[0] is True
    assert fallback_called[0] is True


@pytest.mark.asyncio
async def test_graceful_degradation_both_fail(error_handler):
    """Test graceful degradation when both fail."""
    async def primary():
        raise NetworkError("Primary failed")

    async def fallback():
        raise Exception("Fallback also failed")

    with pytest.raises(Exception):
        await error_handler.graceful_degradation(primary, fallback, "test_op")


def test_error_tracking(error_handler):
    """Test error tracking and statistics."""
    # Create some errors
    error1 = RetryableError("Error 1")
    error2 = FatalError("Error 2")

    ctx1 = ErrorContext(
        error=error1,
        category=ErrorCategory.RETRYABLE,
        operation="op1",
        attempt=0,
        timestamp=time.time(),
        stack_trace="",
    )

    ctx2 = ErrorContext(
        error=error2,
        category=ErrorCategory.FATAL,
        operation="op2",
        attempt=0,
        timestamp=time.time(),
        stack_trace="",
    )

    error_handler._track_error(ctx1)
    error_handler._track_error(ctx2)

    # Check statistics
    stats = error_handler.get_error_statistics()

    assert stats["total_errors"] == 2
    assert stats["by_category"]["retryable"] == 1
    assert stats["by_category"]["fatal"] == 1


def test_error_history_limit(error_handler):
    """Test error history is limited."""
    error_handler.max_history = 10

    # Add more than max
    for i in range(15):
        error = RetryableError(f"Error {i}")
        ctx = ErrorContext(
            error=error,
            category=ErrorCategory.RETRYABLE,
            operation=f"op{i}",
            attempt=0,
            timestamp=time.time(),
            stack_trace="",
        )
        error_handler._track_error(ctx)

    # Should be limited to max_history
    assert len(error_handler.error_history) == 10


@pytest.mark.asyncio
async def test_with_retry_decorator():
    """Test with_retry decorator."""
    call_count = [0]

    @with_retry(max_retries=2)
    async def decorated_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise RetryableError("Fail once")
        return "success"

    result = await decorated_func()

    assert result == "success"
    assert call_count[0] == 2


def test_error_context_to_dict():
    """Test ErrorContext serialization."""
    error = ValueError("Test error")
    ctx = ErrorContext(
        error=error,
        category=ErrorCategory.USER,
        operation="test_op",
        attempt=1,
        timestamp=time.time(),
        stack_trace="trace",
        metadata={"key": "value"},
    )

    data = ctx.to_dict()

    assert data["error_type"] == "ValueError"
    assert data["error_message"] == "Test error"
    assert data["category"] == "user"
    assert data["operation"] == "test_op"
    assert data["attempt"] == 1
    assert data["metadata"]["key"] == "value"


@pytest.mark.asyncio
async def test_sync_function_support(error_handler):
    """Test error handler with sync functions."""
    call_count = [0]

    def sync_func():
        call_count[0] += 1
        if call_count[0] < 2:
            raise RetryableError("Fail once")
        return "success"

    result = await error_handler.with_retry(sync_func, "sync_op")

    assert result == "success"
    assert call_count[0] == 2
