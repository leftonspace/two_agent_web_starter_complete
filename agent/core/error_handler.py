"""
PHASE 11.1: Error Handling & Recovery

Production-grade error handling with categorization, retry logic,
and graceful degradation.

Features:
- Error categorization (retryable, fatal, user)
- Exponential backoff retry with jitter
- Graceful degradation with fallbacks
- Error aggregation and reporting
- Context preservation across retries
"""

from __future__ import annotations

import asyncio
import functools
import random
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Type variable for generic functions
T = TypeVar('T')


class ErrorCategory(Enum):
    """Error categories for handling strategy."""
    RETRYABLE = "retryable"  # Transient errors, retry possible
    FATAL = "fatal"  # Permanent errors, don't retry
    USER = "user"  # User input errors, inform user
    NETWORK = "network"  # Network-related errors
    TIMEOUT = "timeout"  # Timeout errors
    RATE_LIMIT = "rate_limit"  # Rate limiting errors
    RESOURCE = "resource"  # Resource exhaustion errors


@dataclass
class ErrorContext:
    """Context information for error tracking."""
    error: Exception
    category: ErrorCategory
    operation: str
    attempt: int
    timestamp: float
    stack_trace: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": type(self.error).__name__,
            "error_message": str(self.error),
            "category": self.category.value,
            "operation": self.operation,
            "attempt": self.attempt,
            "timestamp": self.timestamp,
            "stack_trace": self.stack_trace,
            "metadata": self.metadata,
        }


# Custom exception classes
class RetryableError(Exception):
    """Error that can be retried."""
    pass


class FatalError(Exception):
    """Fatal error that should not be retried."""
    pass


class UserError(Exception):
    """User input error."""
    pass


class NetworkError(RetryableError):
    """Network-related error."""
    pass


class TimeoutError(RetryableError):
    """Timeout error."""
    pass


class RateLimitError(RetryableError):
    """Rate limiting error."""
    pass


class ResourceExhaustedError(RetryableError):
    """Resource exhaustion error."""
    pass


class ErrorHandler:
    """
    Global error handling and recovery system.

    Provides retry logic, graceful degradation, and error tracking.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """
        Initialize error handler.

        Args:
            max_retries: Maximum retry attempts
            base_delay: Base delay between retries (seconds)
            max_delay: Maximum delay between retries
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delays
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_history: List[ErrorContext] = []
        self.max_history = 1000  # Keep last 1000 errors

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize error for handling strategy.

        Args:
            error: Exception to categorize

        Returns:
            ErrorCategory
        """
        # Check custom error types first
        if isinstance(error, UserError):
            return ErrorCategory.USER
        elif isinstance(error, FatalError):
            return ErrorCategory.FATAL
        elif isinstance(error, NetworkError):
            return ErrorCategory.NETWORK
        elif isinstance(error, TimeoutError):
            return ErrorCategory.TIMEOUT
        elif isinstance(error, RateLimitError):
            return ErrorCategory.RATE_LIMIT
        elif isinstance(error, ResourceExhaustedError):
            return ErrorCategory.RESOURCE
        elif isinstance(error, RetryableError):
            return ErrorCategory.RETRYABLE

        # Categorize by error type name
        error_name = type(error).__name__.lower()

        if any(keyword in error_name for keyword in ["timeout", "timedout"]):
            return ErrorCategory.TIMEOUT
        elif any(keyword in error_name for keyword in ["network", "connection", "socket"]):
            return ErrorCategory.NETWORK
        elif any(keyword in error_name for keyword in ["rate", "limit", "throttle"]):
            return ErrorCategory.RATE_LIMIT
        elif any(keyword in error_name for keyword in ["memory", "resource"]):
            return ErrorCategory.RESOURCE
        elif any(keyword in error_name for keyword in ["value", "type", "attribute"]):
            return ErrorCategory.USER

        # Default to retryable
        return ErrorCategory.RETRYABLE

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if error should be retried.

        Args:
            error: Exception that occurred
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry
        """
        if attempt >= self.max_retries:
            return False

        category = self.categorize_error(error)

        # Never retry fatal or user errors
        if category in [ErrorCategory.FATAL, ErrorCategory.USER]:
            return False

        # Retry other categories
        return True

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay before next retry.

        Uses exponential backoff with optional jitter.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            # Add random jitter: ±25% of delay
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0.1, delay)  # Minimum 0.1 seconds

    async def with_retry(
        self,
        func: Callable[..., T],
        operation_name: str = "operation",
        *args,
        **kwargs,
    ) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            operation_name: Name for logging
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception if all retries exhausted
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - log if this was a retry
                if attempt > 0:
                    print(f"[ErrorHandler] {operation_name} succeeded on attempt {attempt + 1}")

                return result

            except Exception as e:
                last_error = e
                category = self.categorize_error(e)

                # Log error
                error_ctx = ErrorContext(
                    error=e,
                    category=category,
                    operation=operation_name,
                    attempt=attempt,
                    timestamp=time.time(),
                    stack_trace=traceback.format_exc(),
                )

                self._track_error(error_ctx)

                # Check if should retry
                if not self.should_retry(e, attempt):
                    print(f"[ErrorHandler] {operation_name} failed with {category.value} error: {e}")
                    if category == ErrorCategory.FATAL:
                        await self.log_fatal_error(error_ctx)
                    raise

                # Calculate delay
                delay = self.calculate_delay(attempt)

                print(f"[ErrorHandler] {operation_name} attempt {attempt + 1} failed: {e}")
                print(f"[ErrorHandler] Retrying in {delay:.2f}s...")

                # Wait before retry
                await asyncio.sleep(delay)

        # All retries exhausted
        print(f"[ErrorHandler] {operation_name} failed after {self.max_retries + 1} attempts")
        raise last_error

    async def graceful_degradation(
        self,
        primary_func: Callable[..., T],
        fallback_func: Callable[..., T],
        operation_name: str = "operation",
        *args,
        **kwargs,
    ) -> T:
        """
        Try primary function, fall back to degraded service on failure.

        Args:
            primary_func: Primary function to try
            fallback_func: Fallback function if primary fails
            operation_name: Name for logging
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Result from primary or fallback function
        """
        try:
            # Try primary function
            if asyncio.iscoroutinefunction(primary_func):
                return await primary_func(*args, **kwargs)
            else:
                return primary_func(*args, **kwargs)

        except Exception as e:
            category = self.categorize_error(e)

            print(f"[ErrorHandler] {operation_name} primary failed: {e}")
            print(f"[ErrorHandler] Falling back to degraded mode")

            # Log degradation event
            error_ctx = ErrorContext(
                error=e,
                category=category,
                operation=f"{operation_name}_primary",
                attempt=1,
                timestamp=time.time(),
                stack_trace=traceback.format_exc(),
                metadata={"degraded": True},
            )

            self._track_error(error_ctx)

            # Try fallback
            try:
                if asyncio.iscoroutinefunction(fallback_func):
                    result = await fallback_func(*args, **kwargs)
                else:
                    result = fallback_func(*args, **kwargs)

                print(f"[ErrorHandler] {operation_name} fallback succeeded")
                return result

            except Exception as fallback_error:
                print(f"[ErrorHandler] {operation_name} fallback also failed: {fallback_error}")
                raise

    def _track_error(self, error_ctx: ErrorContext):
        """Track error for analytics."""
        # Increment error count
        error_key = f"{error_ctx.category.value}:{type(error_ctx.error).__name__}"
        self.error_counts[error_key] += 1

        # Add to history
        self.error_history.append(error_ctx)

        # Trim history if too long
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

    async def log_fatal_error(self, error_ctx: ErrorContext):
        """Log fatal error for investigation."""
        print(f"[ErrorHandler] FATAL ERROR in {error_ctx.operation}:")
        print(f"  Type: {type(error_ctx.error).__name__}")
        print(f"  Message: {error_ctx.error}")
        print(f"  Stack trace:\n{error_ctx.stack_trace}")

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        total_errors = len(self.error_history)

        # Count by category
        by_category = defaultdict(int)
        for error_ctx in self.error_history:
            by_category[error_ctx.category.value] += 1

        # Recent errors (last 10)
        recent_errors = [
            {
                "operation": ctx.operation,
                "error": type(ctx.error).__name__,
                "category": ctx.category.value,
                "timestamp": ctx.timestamp,
            }
            for ctx in self.error_history[-10:]
        ]

        return {
            "total_errors": total_errors,
            "by_category": dict(by_category),
            "error_counts": dict(self.error_counts),
            "recent_errors": recent_errors,
        }

    def clear_history(self):
        """Clear error history."""
        self.error_history.clear()
        self.error_counts.clear()


# Decorator for automatic retry
def with_retry(
    max_retries: int = 3,
    operation_name: Optional[str] = None,
):
    """
    Decorator for automatic retry on errors.

    Args:
        max_retries: Maximum retry attempts
        operation_name: Operation name for logging

    Example:
        @with_retry(max_retries=3)
        async def fetch_data():
            return await api_call()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            handler = ErrorHandler(max_retries=max_retries)
            op_name = operation_name or func.__name__

            return await handler.with_retry(func, op_name, *args, **kwargs)

        return wrapper

    return decorator
