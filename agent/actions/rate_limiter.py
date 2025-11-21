"""
Rate limiter for API requests.

PHASE 8.2: Token bucket rate limiter to prevent API overload.
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter for API requests.

    Features:
    - Token bucket algorithm
    - Configurable rate and burst capacity
    - Async-safe with locks
    - Automatic token refill

    Example:
        # Allow 10 requests per second, burst of 20
        limiter = RateLimiter(rate=10.0, capacity=20)

        async def make_request():
            await limiter.acquire()
            # Make API request
    """

    def __init__(
        self,
        rate: float = 10.0,
        capacity: Optional[int] = None
    ):
        """
        Initialize rate limiter.

        Args:
            rate: Requests per second (e.g., 10.0 = 10 req/s)
            capacity: Max burst capacity (defaults to rate * 2)
        """
        self.rate = rate
        self.capacity = capacity or int(rate * 2)
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire (default 1)
        """
        async with self.lock:
            while self.tokens < tokens:
                # Calculate time to wait for enough tokens
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.rate

                # Wait and refill
                await asyncio.sleep(wait_time)
                self._refill()

            # Consume tokens
            self.tokens -= tokens

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)

        self.last_refill = now

    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens acquired, False otherwise
        """
        async with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_available_tokens(self) -> float:
        """Get current number of available tokens"""
        return self.tokens

    def reset(self):
        """Reset limiter to full capacity"""
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
