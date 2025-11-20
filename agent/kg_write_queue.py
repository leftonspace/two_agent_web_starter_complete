"""
PHASE 4.3: Knowledge Graph Write Queue for SQLite Contention (R2)

Implements async write queue to prevent database lock contention when
multiple jobs try to write to the knowledge graph simultaneously.

SQLite has single-writer limitation - concurrent writes cause SQLITE_BUSY errors.
This queue serializes writes and batches commits to reduce lock contention.

Architecture:
- WriteQueue: Async queue for write operations
- QueueWorker: Background thread that processes queue
- Batching: Groups multiple writes into single transaction

Usage:
    # Initialize queue (do this once at startup)
    kg_queue = KnowledgeGraphQueue(kg_instance)
    kg_queue.start()

    # Enqueue writes (non-blocking)
    kg_queue.enqueue_add_entity("mission", "build_site", {"domain": "coding"})
    kg_queue.enqueue_add_relationship(mission_id, file_id, "created")

    # Shutdown (wait for queue to drain)
    kg_queue.stop()
"""

from __future__ import annotations

import queue
import sqlite3
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


class WriteOpType(Enum):
    """Types of write operations."""

    ADD_ENTITY = "add_entity"
    ADD_RELATIONSHIP = "add_relationship"
    LOG_MISSION = "log_mission"
    ADD_FILE_SNAPSHOT = "add_file_snapshot"
    EXECUTE_RAW = "execute_raw"  # For custom SQL


@dataclass
class WriteOperation:
    """
    A pending write operation.

    Attributes:
        op_type: Type of operation
        args: Positional arguments for the operation
        kwargs: Keyword arguments for the operation
        callback: Optional callback function to call with result
    """

    op_type: WriteOpType
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    callback: Optional[Callable[[Any], None]] = None


class KnowledgeGraphQueue:
    """
    Async write queue for knowledge graph operations.

    Serializes writes to prevent SQLite lock contention in parallel job scenarios.
    """

    def __init__(
        self,
        kg_instance: Any,
        batch_size: int = 10,
        batch_timeout_seconds: float = 1.0,
        max_queue_size: int = 10000,
    ):
        """
        Initialize write queue.

        Args:
            kg_instance: KnowledgeGraph instance to wrap
            batch_size: Number of operations to batch per transaction
            batch_timeout_seconds: Max seconds to wait before flushing batch
            max_queue_size: Maximum queue size (blocks enqueue if full)
        """
        self.kg = kg_instance
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds

        self.write_queue: queue.Queue[Optional[WriteOperation]] = queue.Queue(
            maxsize=max_queue_size
        )
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        self.stats = {
            "operations_queued": 0,
            "operations_processed": 0,
            "batches_committed": 0,
            "errors": 0,
        }

    def start(self) -> None:
        """Start the background worker thread."""
        if self.running:
            print("[KGQueue] Warning: Queue already running")
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print(f"[KGQueue] Started write queue worker (batch_size={self.batch_size})")

    def stop(self, timeout: float = 30.0) -> None:
        """
        Stop the worker thread and wait for queue to drain.

        Args:
            timeout: Max seconds to wait for queue to drain
        """
        if not self.running:
            return

        print(f"[KGQueue] Stopping queue (pending: {self.write_queue.qsize()})...")

        # Send stop signal
        self.write_queue.put(None)
        self.running = False

        # Wait for worker to finish
        if self.worker_thread:
            self.worker_thread.join(timeout=timeout)

            if self.worker_thread.is_alive():
                print("[KGQueue] Warning: Worker thread did not stop within timeout")
            else:
                print("[KGQueue] Stopped queue worker")

        print(f"[KGQueue] Final stats: {self.stats}")

    def _worker_loop(self) -> None:
        """
        Background worker that processes write queue.

        Batches operations and commits them in transactions.
        """
        batch: List[WriteOperation] = []
        last_commit_time = time.time()

        while self.running:
            try:
                # Check if we should flush the batch
                should_flush = False
                if batch:
                    elapsed = time.time() - last_commit_time
                    if len(batch) >= self.batch_size or elapsed >= self.batch_timeout_seconds:
                        should_flush = True

                if should_flush:
                    self._commit_batch(batch)
                    batch = []
                    last_commit_time = time.time()

                # Get next operation (with timeout to check flush condition)
                try:
                    op = self.write_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Check for stop signal
                if op is None:
                    # Flush remaining batch before stopping
                    if batch:
                        self._commit_batch(batch)
                    break

                # Add to batch
                batch.append(op)

            except Exception as e:
                print(f"[KGQueue] Error in worker loop: {e}")
                self.stats["errors"] += 1

        print("[KGQueue] Worker loop exited")

    def _commit_batch(self, batch: List[WriteOperation]) -> None:
        """
        Commit a batch of write operations in a single transaction.

        Args:
            batch: List of write operations to commit
        """
        if not batch:
            return

        try:
            # Begin transaction
            conn = self.kg.conn
            conn.execute("BEGIN TRANSACTION")

            results = []
            for op in batch:
                try:
                    result = self._execute_operation(op)
                    results.append(result)

                    # Call callback if provided
                    if op.callback:
                        op.callback(result)

                except Exception as e:
                    print(f"[KGQueue] Error executing operation {op.op_type}: {e}")
                    self.stats["errors"] += 1
                    results.append(None)

            # Commit transaction
            conn.commit()

            self.stats["operations_processed"] += len(batch)
            self.stats["batches_committed"] += 1

            print(
                f"[KGQueue] Committed batch of {len(batch)} operations "
                f"(total: {self.stats['operations_processed']})"
            )

        except sqlite3.OperationalError as e:
            # Database locked - rollback and retry
            print(f"[KGQueue] Database locked during commit, rolling back: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
            self.stats["errors"] += 1

        except Exception as e:
            print(f"[KGQueue] Error committing batch: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
            self.stats["errors"] += 1

    def _execute_operation(self, op: WriteOperation) -> Any:
        """
        Execute a single write operation.

        Args:
            op: Write operation to execute

        Returns:
            Operation result
        """
        if op.op_type == WriteOpType.ADD_ENTITY:
            return self.kg.add_entity(*op.args, **op.kwargs)

        elif op.op_type == WriteOpType.ADD_RELATIONSHIP:
            return self.kg.add_relationship(*op.args, **op.kwargs)

        elif op.op_type == WriteOpType.LOG_MISSION:
            return self.kg.log_mission_run(*op.args, **op.kwargs)

        elif op.op_type == WriteOpType.ADD_FILE_SNAPSHOT:
            return self.kg.add_file_snapshot(*op.args, **op.kwargs)

        elif op.op_type == WriteOpType.EXECUTE_RAW:
            # Execute raw SQL
            sql = op.args[0]
            params = op.args[1] if len(op.args) > 1 else ()
            return self.kg.conn.execute(sql, params)

        else:
            raise ValueError(f"Unknown operation type: {op.op_type}")

    # ──────────────────────────────────────────────────────────────
    # Public enqueue methods
    # ──────────────────────────────────────────────────────────────

    def enqueue_add_entity(
        self,
        entity_type: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """
        Enqueue add_entity operation.

        Args:
            entity_type: Type of entity (mission, file, concept, etc.)
            name: Entity name
            metadata: Optional metadata dict
            callback: Optional callback function to call with entity_id
        """
        op = WriteOperation(
            op_type=WriteOpType.ADD_ENTITY,
            args=(entity_type, name),
            kwargs={"metadata": metadata},
            callback=callback,
        )
        self.write_queue.put(op)
        self.stats["operations_queued"] += 1

    def enqueue_add_relationship(
        self,
        from_id: int,
        to_id: int,
        rel_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """
        Enqueue add_relationship operation.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            rel_type: Relationship type
            metadata: Optional metadata dict
            callback: Optional callback function to call with relationship_id
        """
        op = WriteOperation(
            op_type=WriteOpType.ADD_RELATIONSHIP,
            args=(from_id, to_id, rel_type),
            kwargs={"metadata": metadata},
            callback=callback,
        )
        self.write_queue.put(op)
        self.stats["operations_queued"] += 1

    def enqueue_log_mission(
        self,
        mission_id: str,
        status: str,
        domain: Optional[str] = None,
        cost_usd: Optional[float] = None,
        iterations: Optional[int] = None,
        duration_seconds: Optional[float] = None,
        files_modified: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """
        Enqueue log_mission_run operation.

        Args:
            mission_id: Unique mission identifier
            status: Mission status (success, failed, aborted)
            domain: Domain (coding, finance, etc.)
            cost_usd: Total cost in USD
            iterations: Number of iterations completed
            duration_seconds: Execution duration
            files_modified: Number of files changed
            metadata: Optional metadata dict
            callback: Optional callback function
        """
        op = WriteOperation(
            op_type=WriteOpType.LOG_MISSION,
            args=(mission_id, status),
            kwargs={
                "domain": domain,
                "cost_usd": cost_usd,
                "iterations": iterations,
                "duration_seconds": duration_seconds,
                "files_modified": files_modified,
                "metadata": metadata,
            },
            callback=callback,
        )
        self.write_queue.put(op)
        self.stats["operations_queued"] += 1

    def enqueue_add_file_snapshot(
        self,
        file_path: str,
        mission_id: Optional[str] = None,
        size_bytes: Optional[int] = None,
        lines_of_code: Optional[int] = None,
        hash_str: Optional[str] = None,
        callback: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """
        Enqueue add_file_snapshot operation.

        Args:
            file_path: Path to file
            mission_id: Associated mission ID
            size_bytes: File size in bytes
            lines_of_code: LOC count
            hash_str: Content hash
            callback: Optional callback function
        """
        op = WriteOperation(
            op_type=WriteOpType.ADD_FILE_SNAPSHOT,
            args=(file_path,),
            kwargs={
                "mission_id": mission_id,
                "size_bytes": size_bytes,
                "lines_of_code": lines_of_code,
                "hash": hash_str,
            },
            callback=callback,
        )
        self.write_queue.put(op)
        self.stats["operations_queued"] += 1

    def get_stats(self) -> Dict[str, int]:
        """Get queue statistics."""
        return {
            **self.stats,
            "queue_size": self.write_queue.qsize(),
        }
