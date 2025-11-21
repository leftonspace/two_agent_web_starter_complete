"""
PHASE 11.4: Batch Processing

Efficient batch processing for high-throughput operations.

Features:
- Automatic batching with windowing
- Configurable batch size and timeout
- Parallel processing
- Error handling per batch
- Retry logic
- Progress tracking
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar
from enum import Enum

T = TypeVar('T')
R = TypeVar('R')


class BatchStatus(Enum):
    """Batch processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    # Batch size
    max_batch_size: int = 100
    min_batch_size: int = 1

    # Timing
    max_wait_time: float = 1.0  # Seconds to wait before processing partial batch

    # Concurrency
    max_concurrent_batches: int = 5

    # Retry
    max_retries: int = 3
    retry_delay: float = 1.0

    # Processing
    continue_on_error: bool = True  # Continue processing remaining items if one fails


@dataclass
class BatchResult:
    """Result of batch processing."""

    total_items: int
    successful_items: int
    failed_items: int
    results: List[Any]
    errors: List[tuple[int, Exception]]  # (index, error)
    duration: float
    batches_processed: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_items == 0:
            return 1.0
        return self.successful_items / self.total_items


class BatchProcessor:
    """
    Efficient batch processor.

    Accumulates items and processes them in batches for efficiency.
    Supports automatic windowing, parallel processing, and error handling.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        """
        Initialize batch processor.

        Args:
            config: Batch configuration
        """
        self.config = config or BatchConfig()

        # Pending items
        self.pending_items: List[Any] = []
        self.pending_lock = asyncio.Lock()

        # Statistics
        self.total_processed = 0
        self.total_batches = 0
        self.total_errors = 0

    async def add_item(self, item: Any):
        """
        Add item to batch queue.

        Args:
            item: Item to process
        """
        async with self.pending_lock:
            self.pending_items.append(item)

    async def process_batch(
        self,
        items: List[T],
        processor: Callable[[List[T]], List[R]],
    ) -> BatchResult:
        """
        Process a batch of items.

        Args:
            items: Items to process
            processor: Function to process batch

        Returns:
            Batch processing result
        """
        start_time = time.time()

        results = []
        errors = []
        successful = 0
        failed = 0

        # Split into chunks if needed
        batches = self._split_into_batches(items)

        for batch in batches:
            try:
                # Process batch
                if asyncio.iscoroutinefunction(processor):
                    batch_results = await processor(batch)
                else:
                    batch_results = processor(batch)

                results.extend(batch_results)
                successful += len(batch)

            except Exception as e:
                # Handle batch-level error
                if self.config.continue_on_error:
                    # Try processing items individually
                    for i, item in enumerate(batch):
                        try:
                            if asyncio.iscoroutinefunction(processor):
                                result = await processor([item])
                            else:
                                result = processor([item])

                            results.extend(result)
                            successful += 1

                        except Exception as item_error:
                            errors.append((len(results) + i, item_error))
                            failed += 1
                            results.append(None)
                else:
                    # Fail entire batch
                    errors.append((len(results), e))
                    failed += len(batch)
                    results.extend([None] * len(batch))

        duration = time.time() - start_time

        return BatchResult(
            total_items=len(items),
            successful_items=successful,
            failed_items=failed,
            results=results,
            errors=errors,
            duration=duration,
            batches_processed=len(batches),
        )

    async def process_all(
        self,
        items: List[T],
        processor: Callable[[T], R],
        parallel: bool = True,
    ) -> BatchResult:
        """
        Process all items with automatic batching.

        Args:
            items: Items to process
            processor: Function to process single item
            parallel: Whether to process batches in parallel

        Returns:
            Batch processing result
        """
        if not items:
            return BatchResult(
                total_items=0,
                successful_items=0,
                failed_items=0,
                results=[],
                errors=[],
                duration=0.0,
                batches_processed=0,
            )

        start_time = time.time()

        # Split into batches
        batches = self._split_into_batches(items)

        # Process batches
        if parallel:
            # Process batches in parallel with concurrency limit
            results = await self._process_batches_parallel(batches, processor)
        else:
            # Process batches sequentially
            results = await self._process_batches_sequential(batches, processor)

        # Aggregate results
        all_results = []
        all_errors = []
        successful = 0
        failed = 0

        for batch_result in results:
            all_results.extend(batch_result.results)
            all_errors.extend(batch_result.errors)
            successful += batch_result.successful_items
            failed += batch_result.failed_items

        duration = time.time() - start_time

        return BatchResult(
            total_items=len(items),
            successful_items=successful,
            failed_items=failed,
            results=all_results,
            errors=all_errors,
            duration=duration,
            batches_processed=len(batches),
        )

    async def _process_batches_parallel(
        self,
        batches: List[List[T]],
        processor: Callable[[T], R],
    ) -> List[BatchResult]:
        """Process batches in parallel with concurrency limit."""
        semaphore = asyncio.Semaphore(self.config.max_concurrent_batches)

        async def process_with_semaphore(batch):
            async with semaphore:
                return await self._process_single_batch(batch, processor)

        tasks = [process_with_semaphore(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        batch_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result
                batch_results.append(
                    BatchResult(
                        total_items=len(batches[i]),
                        successful_items=0,
                        failed_items=len(batches[i]),
                        results=[None] * len(batches[i]),
                        errors=[(0, result)],
                        duration=0.0,
                        batches_processed=1,
                    )
                )
            else:
                batch_results.append(result)

        return batch_results

    async def _process_batches_sequential(
        self,
        batches: List[List[T]],
        processor: Callable[[T], R],
    ) -> List[BatchResult]:
        """Process batches sequentially."""
        results = []

        for batch in batches:
            result = await self._process_single_batch(batch, processor)
            results.append(result)

        return results

    async def _process_single_batch(
        self,
        batch: List[T],
        processor: Callable[[T], R],
    ) -> BatchResult:
        """Process a single batch."""
        start_time = time.time()

        results = []
        errors = []
        successful = 0
        failed = 0

        for i, item in enumerate(batch):
            try:
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(item)
                else:
                    result = processor(item)

                results.append(result)
                successful += 1

            except Exception as e:
                errors.append((i, e))
                failed += 1
                results.append(None)

                if not self.config.continue_on_error:
                    break

        duration = time.time() - start_time

        return BatchResult(
            total_items=len(batch),
            successful_items=successful,
            failed_items=failed,
            results=results,
            errors=errors,
            duration=duration,
            batches_processed=1,
        )

    def _split_into_batches(self, items: List[T]) -> List[List[T]]:
        """Split items into batches."""
        batches = []
        batch_size = self.config.max_batch_size

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            if len(batch) >= self.config.min_batch_size:
                batches.append(batch)

        return batches

    async def flush(
        self,
        processor: Callable[[List[Any]], List[Any]],
    ) -> Optional[BatchResult]:
        """
        Process all pending items.

        Args:
            processor: Function to process batch

        Returns:
            Batch result if items were processed, None otherwise
        """
        async with self.pending_lock:
            if not self.pending_items:
                return None

            items = self.pending_items.copy()
            self.pending_items.clear()

        result = await self.process_batch(items, processor)

        # Update statistics
        self.total_processed += result.total_items
        self.total_batches += result.batches_processed
        self.total_errors += result.failed_items

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_processed": self.total_processed,
            "total_batches": self.total_batches,
            "total_errors": self.total_errors,
            "pending_items": len(self.pending_items),
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_concurrent_batches": self.config.max_concurrent_batches,
            },
        }


class StreamingBatchProcessor:
    """
    Streaming batch processor.

    Processes items as they arrive with automatic windowing.
    Useful for real-time processing pipelines.
    """

    def __init__(
        self,
        processor: Callable[[List[Any]], List[Any]],
        config: Optional[BatchConfig] = None,
    ):
        """
        Initialize streaming batch processor.

        Args:
            processor: Function to process batches
            config: Batch configuration
        """
        self.processor = processor
        self.config = config or BatchConfig()

        self.batch_processor = BatchProcessor(config)
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start streaming processor."""
        if self.running:
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        """Stop streaming processor."""
        self.running = False

        if self.worker_task:
            # Wait for worker to finish
            await self.worker_task

    async def add(self, item: Any):
        """Add item to processing queue."""
        await self.batch_processor.add_item(item)

    async def _worker(self):
        """Background worker that processes batches."""
        while self.running:
            # Wait for batch window
            await asyncio.sleep(self.config.max_wait_time)

            # Process pending items
            await self.batch_processor.flush(self.processor)

        # Final flush on stop
        await self.batch_processor.flush(self.processor)
