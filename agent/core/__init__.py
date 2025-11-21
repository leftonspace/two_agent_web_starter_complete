"""
PHASE 11.1: Error Handling & Recovery

Production-grade error handling and recovery system.

Components:
- error_handler: Global error handling with retry and degradation
- circuit_breaker: Circuit breaker pattern for fault isolation

Features:
- Categorized errors (retryable, fatal, user)
- Retry logic with exponential backoff
- Circuit breaker pattern
- Graceful degradation
- Error aggregation and reporting
"""

from .error_handler import (
    ErrorHandler,
    ErrorCategory,
    RetryableError,
    FatalError,
    UserError,
    ErrorContext,
)
from .circuit_breaker import CircuitBreaker, CircuitState

__all__ = [
    "ErrorHandler",
    "ErrorCategory",
    "RetryableError",
    "FatalError",
    "UserError",
    "ErrorContext",
    "CircuitBreaker",
    "CircuitState",
]
