"""
Parallel Execution Utilities

Provides utilities for parallel agent execution, batch processing,
throttling, and async coordination.
"""

from typing import TypeVar, Generic, Callable, Optional, Any, Dict, List, Tuple, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import asyncio
import threading
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class ExecutionResult(Generic[T]):
    """Result of a parallel execution."""
    success: bool
    result: Optional[T] = None
    error: Optional[Exception] = None
    duration_ms: float = 0.0
    task_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result if self.success else None,
            "error": str(self.error) if self.error else None,
            "duration_ms": round(self.duration_ms, 2),
            "task_id": self.task_id,
        }


@dataclass
class BatchResult(Generic[T]):
    """Result of a batch execution."""
    results: List[ExecutionResult[T]]
    total_duration_ms: float
    success_count: int
    failure_count: int

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_duration_ms": round(self.total_duration_ms, 2),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": round(self.success_rate, 4),
            "results": [r.to_dict() for r in self.results],
        }


class ParallelExecutor:
    """
    Executes tasks in parallel with configurable concurrency.

    Supports both thread-based and process-based parallelism.

    Usage:
        executor = ParallelExecutor(max_workers=4)

        # Execute multiple tasks
        results = executor.map(process_item, items)

        # Or with async
        results = await executor.map_async(process_item_async, items)
    """

    def __init__(
        self,
        max_workers: int = 4,
        use_processes: bool = False,
        timeout: Optional[float] = None
    ):
        """
        Initialize parallel executor.

        Args:
            max_workers: Maximum concurrent workers
            use_processes: Use processes instead of threads
            timeout: Default timeout for tasks
        """
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.timeout = timeout

    def map(
        self,
        func: Callable[[T], R],
        items: List[T],
        timeout: Optional[float] = None
    ) -> List[ExecutionResult[R]]:
        """
        Execute function on items in parallel.

        Args:
            func: Function to execute
            items: Items to process
            timeout: Optional timeout per item

        Returns:
            List of ExecutionResults
        """
        timeout = timeout or self.timeout
        results = []

        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            futures = {}

            for i, item in enumerate(items):
                future = executor.submit(self._execute_with_timing, func, item)
                futures[future] = i

            for future in as_completed(futures, timeout=timeout):
                idx = futures[future]
                try:
                    result = future.result(timeout=timeout)
                    results.append(result)
                except Exception as e:
                    results.append(ExecutionResult(
                        success=False,
                        error=e,
                        task_id=str(idx)
                    ))

        return results

    def _execute_with_timing(
        self,
        func: Callable[[T], R],
        item: T
    ) -> ExecutionResult[R]:
        """Execute function with timing."""
        start = time.time()
        try:
            result = func(item)
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=True,
                result=result,
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=False,
                error=e,
                duration_ms=duration
            )

    async def map_async(
        self,
        func: Callable[[T], Awaitable[R]],
        items: List[T],
        timeout: Optional[float] = None,
        return_exceptions: bool = True
    ) -> List[ExecutionResult[R]]:
        """
        Execute async function on items in parallel.

        Args:
            func: Async function to execute
            items: Items to process
            timeout: Optional timeout per item
            return_exceptions: Whether to catch and return exceptions

        Returns:
            List of ExecutionResults
        """
        timeout = timeout or self.timeout

        async def execute_one(item: T, idx: int) -> ExecutionResult[R]:
            start = time.time()
            try:
                if timeout:
                    result = await asyncio.wait_for(func(item), timeout=timeout)
                else:
                    result = await func(item)
                duration = (time.time() - start) * 1000
                return ExecutionResult(
                    success=True,
                    result=result,
                    duration_ms=duration,
                    task_id=str(idx)
                )
            except Exception as e:
                duration = (time.time() - start) * 1000
                if not return_exceptions:
                    raise
                return ExecutionResult(
                    success=False,
                    error=e,
                    duration_ms=duration,
                    task_id=str(idx)
                )

        # Create semaphore for concurrency limiting
        semaphore = asyncio.Semaphore(self.max_workers)

        async def bounded_execute(item: T, idx: int) -> ExecutionResult[R]:
            async with semaphore:
                return await execute_one(item, idx)

        tasks = [bounded_execute(item, i) for i, item in enumerate(items)]
        return await asyncio.gather(*tasks)


class BatchProcessor(Generic[T, R]):
    """
    Processes items in batches with configurable batch size and delay.

    Useful for rate-limited APIs and bulk operations.

    Usage:
        processor = BatchProcessor(
            process_fn=call_api,
            batch_size=10,
            delay_between_batches=1.0
        )

        results = await processor.process(items)
    """

    def __init__(
        self,
        process_fn: Callable[[List[T]], Awaitable[List[R]]],
        batch_size: int = 10,
        delay_between_batches: float = 0.0,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize batch processor.

        Args:
            process_fn: Function to process a batch
            batch_size: Number of items per batch
            delay_between_batches: Delay in seconds between batches
            max_retries: Maximum retries on failure
            retry_delay: Delay between retries
        """
        self.process_fn = process_fn
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def process(self, items: List[T]) -> BatchResult[R]:
        """
        Process all items in batches.

        Args:
            items: Items to process

        Returns:
            BatchResult with all results
        """
        start_time = time.time()
        all_results: List[ExecutionResult[R]] = []
        success_count = 0
        failure_count = 0

        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]

        for batch_idx, batch in enumerate(batches):
            batch_results = await self._process_batch_with_retry(batch, batch_idx)
            all_results.extend(batch_results)

            for result in batch_results:
                if result.success:
                    success_count += 1
                else:
                    failure_count += 1

            # Delay between batches (except last)
            if batch_idx < len(batches) - 1 and self.delay_between_batches > 0:
                await asyncio.sleep(self.delay_between_batches)

        total_duration = (time.time() - start_time) * 1000

        return BatchResult(
            results=all_results,
            total_duration_ms=total_duration,
            success_count=success_count,
            failure_count=failure_count
        )

    async def _process_batch_with_retry(
        self,
        batch: List[T],
        batch_idx: int
    ) -> List[ExecutionResult[R]]:
        """Process a batch with retries."""
        for attempt in range(self.max_retries):
            try:
                start = time.time()
                results = await self.process_fn(batch)
                duration = (time.time() - start) * 1000

                return [
                    ExecutionResult(
                        success=True,
                        result=r,
                        duration_ms=duration / len(results),
                        task_id=f"{batch_idx}_{i}"
                    )
                    for i, r in enumerate(results)
                ]
            except Exception as e:
                logger.warning(f"Batch {batch_idx} failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        # All retries failed
        return [
            ExecutionResult(
                success=False,
                error=Exception(f"Batch {batch_idx} failed after {self.max_retries} retries"),
                task_id=f"{batch_idx}_{i}"
            )
            for i in range(len(batch))
        ]


class Throttler:
    """
    Rate limiter for controlling request frequency.

    Supports both sync and async operations.

    Usage:
        throttler = Throttler(rate=10, period=1.0)  # 10 requests per second

        async def make_request():
            await throttler.acquire()
            response = await api.call()
            return response
    """

    def __init__(
        self,
        rate: int = 10,
        period: float = 1.0,
        burst: int = 0
    ):
        """
        Initialize throttler.

        Args:
            rate: Number of allowed requests per period
            period: Time period in seconds
            burst: Additional burst capacity
        """
        self.rate = rate
        self.period = period
        self.burst = burst

        self._tokens = rate + burst
        self._last_refill = time.time()
        self._lock: Optional[asyncio.Lock] = None  # Deferred to avoid event loop issues
        self._sync_lock = threading.Lock()  # Initialize immediately to avoid race condition
        self._async_lock_init = threading.Lock()  # Lock for initializing async lock

    def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        new_tokens = elapsed * (self.rate / self.period)

        self._tokens = min(self.rate + self.burst, self._tokens + new_tokens)
        self._last_refill = now

    async def _get_async_lock(self) -> asyncio.Lock:
        """Get or create the async lock (deferred initialization)."""
        if self._lock is None:
            with self._async_lock_init:
                if self._lock is None:
                    self._lock = asyncio.Lock()
        return self._lock

    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Wait time in seconds
        """
        lock = await self._get_async_lock()
        async with lock:
            self._refill_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0

            # Calculate wait time
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed * (self.period / self.rate)

            await asyncio.sleep(wait_time)

            self._refill_tokens()
            self._tokens -= tokens
            return wait_time

    def acquire_sync(self, tokens: int = 1) -> float:
        """Synchronous version of acquire."""
        with self._sync_lock:
            self._refill_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0

            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed * (self.period / self.rate)

            time.sleep(wait_time)

            self._refill_tokens()
            self._tokens -= tokens
            return wait_time

    @property
    def available_tokens(self) -> float:
        """Get current available tokens."""
        self._refill_tokens()
        return self._tokens


async def run_parallel(
    tasks: List[Callable[[], Awaitable[T]]],
    max_concurrency: int = 10,
    timeout: Optional[float] = None
) -> List[ExecutionResult[T]]:
    """
    Run multiple async tasks in parallel with concurrency limit.

    Args:
        tasks: List of async callables
        max_concurrency: Maximum concurrent tasks
        timeout: Optional timeout per task

    Returns:
        List of ExecutionResults
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def run_one(task: Callable[[], Awaitable[T]], idx: int) -> ExecutionResult[T]:
        async with semaphore:
            start = time.time()
            try:
                if timeout:
                    result = await asyncio.wait_for(task(), timeout=timeout)
                else:
                    result = await task()
                duration = (time.time() - start) * 1000
                return ExecutionResult(
                    success=True,
                    result=result,
                    duration_ms=duration,
                    task_id=str(idx)
                )
            except Exception as e:
                duration = (time.time() - start) * 1000
                return ExecutionResult(
                    success=False,
                    error=e,
                    duration_ms=duration,
                    task_id=str(idx)
                )

    coroutines = [run_one(task, i) for i, task in enumerate(tasks)]
    return await asyncio.gather(*coroutines)


async def run_with_timeout(
    coro: Awaitable[T],
    timeout: float,
    default: Optional[T] = None
) -> T:
    """
    Run coroutine with timeout, returning default on timeout.

    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        default: Default value on timeout

    Returns:
        Result or default
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return default


def run_in_executor(
    func: Callable[..., T],
    *args,
    executor: Optional[ThreadPoolExecutor] = None,
    **kwargs
) -> asyncio.Future:
    """
    Run a synchronous function in a thread executor.

    Args:
        func: Function to run
        *args: Positional arguments
        executor: Optional executor
        **kwargs: Keyword arguments

    Returns:
        Future with result
    """
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(
        executor,
        lambda: func(*args, **kwargs)
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'ExecutionResult',
    'BatchResult',
    'ParallelExecutor',
    'BatchProcessor',
    'Throttler',
    'run_parallel',
    'run_with_timeout',
    'run_in_executor',
]
