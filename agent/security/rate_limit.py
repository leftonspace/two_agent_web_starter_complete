"""
PHASE 11.3: Rate Limiting

Token bucket rate limiting implementation for API protection.

Features:
- Token bucket algorithm
- Sliding window tracking
- Per-user/per-key rate limits
- Configurable limits and windows
- Automatic token refill
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Optional


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.1f} seconds")


@dataclass
class TokenBucket:
    """
    Token bucket for rate limiting.

    Tokens are added at a constant rate (refill_rate).
    Each request consumes one token.
    """

    capacity: int  # Maximum tokens
    refill_rate: float  # Tokens per second
    tokens: float  # Current tokens
    last_refill: float  # Last refill timestamp

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens
            refill_rate: Rate at which tokens are refilled (tokens/second)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        self.refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until requested tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens are available
        """
        self.refill()

        if self.tokens >= tokens:
            return 0.0

        # Calculate tokens needed
        tokens_needed = tokens - self.tokens

        # Calculate time needed to refill
        return tokens_needed / self.refill_rate

    def get_remaining(self) -> int:
        """Get remaining tokens."""
        self.refill()
        return int(self.tokens)


class RateLimiter:
    """
    Rate limiter with per-identifier token buckets.

    Supports multiple rate limiting strategies:
    - Token bucket (default)
    - Sliding window
    - Fixed window
    """

    def __init__(
        self,
        max_requests: int = 100,
        window: float = 60.0,
        burst_size: Optional[int] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window: Time window in seconds
            burst_size: Maximum burst size (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.window = window
        self.burst_size = burst_size or max_requests

        # Calculate refill rate (tokens per second)
        self.refill_rate = max_requests / window

        # Per-identifier buckets
        self.buckets: Dict[str, TokenBucket] = {}

    def _get_bucket(self, identifier: str) -> TokenBucket:
        """Get or create token bucket for identifier."""
        if identifier not in self.buckets:
            self.buckets[identifier] = TokenBucket(
                capacity=self.burst_size,
                refill_rate=self.refill_rate,
            )

        return self.buckets[identifier]

    async def allow(self, identifier: str, cost: int = 1) -> bool:
        """
        Check if request is allowed.

        Args:
            identifier: Unique identifier (user_id, api_key, etc.)
            cost: Cost of this request in tokens

        Returns:
            True if request is allowed, False otherwise
        """
        bucket = self._get_bucket(identifier)
        return bucket.consume(cost)

    async def allow_or_raise(self, identifier: str, cost: int = 1):
        """
        Check if request is allowed, raise exception if not.

        Args:
            identifier: Unique identifier
            cost: Cost of this request in tokens

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        bucket = self._get_bucket(identifier)

        if not bucket.consume(cost):
            retry_after = bucket.time_until_available(cost)
            raise RateLimitExceeded(retry_after)

    def get_remaining(self, identifier: str) -> int:
        """
        Get remaining requests for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Number of remaining requests
        """
        bucket = self._get_bucket(identifier)
        return bucket.get_remaining()

    def get_limit_info(self, identifier: str) -> Dict[str, any]:
        """
        Get rate limit information for identifier.

        Args:
            identifier: Unique identifier

        Returns:
            Dictionary with limit info
        """
        bucket = self._get_bucket(identifier)

        return {
            "limit": self.max_requests,
            "remaining": bucket.get_remaining(),
            "window": self.window,
            "retry_after": bucket.time_until_available(1),
        }

    def reset(self, identifier: str):
        """Reset rate limit for identifier."""
        if identifier in self.buckets:
            del self.buckets[identifier]

    def reset_all(self):
        """Reset all rate limits."""
        self.buckets.clear()


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.

    More accurate than token bucket but uses more memory.
    Tracks individual request timestamps.
    """

    def __init__(self, max_requests: int = 100, window: float = 60.0):
        """
        Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum requests per window
            window: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = window

        # Per-identifier request timestamps
        self.requests: Dict[str, list[float]] = {}

    def _clean_old_requests(self, identifier: str):
        """Remove requests outside the time window."""
        if identifier not in self.requests:
            return

        cutoff = time.time() - self.window
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > cutoff
        ]

    async def allow(self, identifier: str) -> bool:
        """
        Check if request is allowed.

        Args:
            identifier: Unique identifier

        Returns:
            True if request is allowed, False otherwise
        """
        self._clean_old_requests(identifier)

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(time.time())
            return True

        return False

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        self._clean_old_requests(identifier)

        current = len(self.requests.get(identifier, []))
        return max(0, self.max_requests - current)
