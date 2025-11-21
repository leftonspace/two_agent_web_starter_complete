"""
Employee AI Pool Management.

PHASE 7C.1: Manages multiple concurrent Employee agents for parallel task execution.

Features:
- Multiple worker pool with specialty-based assignment
- Load balancing and task queueing
- Parallel batch execution
- Worker health monitoring and statistics
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from agent.llm_client import LLMClient
from agent.core_logging import log_event


class EmployeeSpecialty(Enum):
    """Employee worker specialties"""
    CODING = "coding"
    DOCUMENTS = "documents"
    DATA_ANALYSIS = "data_analysis"
    COMMUNICATIONS = "communications"
    GENERAL = "general"


class EmployeeStatus(Enum):
    """Worker status"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class EmployeeWorker:
    """Represents a single Employee worker in the pool"""
    worker_id: str
    specialty: EmployeeSpecialty
    status: EmployeeStatus = EmployeeStatus.IDLE
    current_task: Optional[str] = None
    tasks_completed: int = 0
    total_execution_time: float = 0.0
    error_count: int = 0
    last_active: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


class EmployeePool:
    """
    Manages pool of Employee AI agents for parallel execution.

    Features:
    - Specialty-based task assignment
    - Load balancing across workers
    - Task queueing when all busy
    - Batch parallel execution
    - Worker statistics and health monitoring

    Example:
        pool = EmployeePool(llm_client, pool_size=5)
        await pool.initialize()

        result = await pool.assign_task("Write a report", specialty="documents")

        results = await pool.execute_batch([
            {"description": "Task 1", "specialty": "coding"},
            {"description": "Task 2", "specialty": "documents"}
        ])
    """

    def __init__(
        self,
        llm_client: LLMClient,
        pool_size: int = 5,
        max_queue_size: int = 50
    ):
        """
        Initialize Employee pool.

        Args:
            llm_client: LLM client for worker agents
            pool_size: Number of concurrent workers
            max_queue_size: Maximum queued tasks before rejection
        """
        self.llm = llm_client
        self.pool_size = pool_size
        self.max_queue_size = max_queue_size

        # Worker pool
        self.workers: Dict[str, EmployeeWorker] = {}

        # Task queue
        self.task_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)

        # Tracking
        self.total_tasks_processed = 0
        self.total_errors = 0

        # Queue processor
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self):
        """Initialize worker pool"""
        log_event("employee_pool_initializing", {
            "pool_size": self.pool_size
        })

        await self._initialize_pool()

        # Start queue processor
        self._running = True
        self._queue_processor_task = asyncio.create_task(self._process_queue())

        log_event("employee_pool_initialized", {
            "workers": len(self.workers),
            "specialties": self._get_specialty_distribution()
        })

    async def _initialize_pool(self):
        """Create worker pool with balanced specialties"""
        specialties = [
            EmployeeSpecialty.CODING,
            EmployeeSpecialty.DOCUMENTS,
            EmployeeSpecialty.DATA_ANALYSIS,
            EmployeeSpecialty.COMMUNICATIONS,
            EmployeeSpecialty.GENERAL
        ]

        # Distribute specialties evenly
        for i in range(self.pool_size):
            specialty = specialties[i % len(specialties)]
            worker_id = f"employee_{i+1}_{specialty.value}"

            worker = EmployeeWorker(
                worker_id=worker_id,
                specialty=specialty,
                status=EmployeeStatus.IDLE
            )

            self.workers[worker_id] = worker

        log_event("pool_workers_created", {
            "count": len(self.workers)
        })

    async def assign_task(
        self,
        task_description: str,
        specialty: Optional[str] = None,
        context: Optional[Dict] = None,
        priority: int = 5
    ) -> Dict[str, Any]:
        """
        Assign task to appropriate worker.

        Args:
            task_description: Task to execute
            specialty: Preferred specialty (auto-detected if None)
            context: Additional context
            priority: Task priority (1-10, higher = more urgent)

        Returns:
            Execution result
        """
        # Determine specialty if not provided
        if specialty:
            try:
                specialty_enum = EmployeeSpecialty(specialty)
            except ValueError:
                specialty_enum = await self._determine_specialty(task_description)
        else:
            specialty_enum = await self._determine_specialty(task_description)

        log_event("task_assignment_requested", {
            "task": task_description[:100],
            "specialty": specialty_enum.value,
            "priority": priority
        })

        # Find best worker
        worker = self._find_best_worker(specialty_enum)

        if worker:
            # Assign immediately
            return await self._assign_to_worker(
                worker,
                task_description,
                context
            )
        else:
            # Queue for later
            log_event("task_queued", {
                "task": task_description[:100],
                "queue_size": self.task_queue.qsize()
            })

            if self.task_queue.full():
                return {
                    "success": False,
                    "error": "Task queue full. Pool overloaded.",
                    "queue_size": self.task_queue.qsize()
                }

            # Add to queue
            task_item = {
                "description": task_description,
                "specialty": specialty_enum,
                "context": context,
                "priority": priority,
                "queued_at": datetime.now()
            }

            # Create future for result
            result_future = asyncio.Future()
            task_item["result_future"] = result_future

            await self.task_queue.put(task_item)

            # Wait for result
            return await result_future

    def _find_best_worker(
        self,
        specialty: EmployeeSpecialty
    ) -> Optional[EmployeeWorker]:
        """
        Find best available worker for task.

        Preference:
        1. Idle worker with matching specialty
        2. Idle worker with general specialty
        3. Idle worker with any specialty
        4. None (all busy)
        """
        idle_workers = [
            w for w in self.workers.values()
            if w.status == EmployeeStatus.IDLE
        ]

        if not idle_workers:
            return None

        # 1. Match specialty
        matching = [w for w in idle_workers if w.specialty == specialty]
        if matching:
            # Choose least loaded
            return min(matching, key=lambda w: w.tasks_completed)

        # 2. General workers
        general = [w for w in idle_workers if w.specialty == EmployeeSpecialty.GENERAL]
        if general:
            return min(general, key=lambda w: w.tasks_completed)

        # 3. Any idle worker
        return min(idle_workers, key=lambda w: w.tasks_completed)

    async def _assign_to_worker(
        self,
        worker: EmployeeWorker,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Assign and execute task on worker"""
        worker.status = EmployeeStatus.BUSY
        worker.current_task = task_description
        worker.last_active = datetime.now()

        start_time = datetime.now()

        try:
            result = await self._execute_task_on_worker(
                worker,
                task_description,
                context
            )

            # Update stats
            execution_time = (datetime.now() - start_time).total_seconds()
            worker.tasks_completed += 1
            worker.total_execution_time += execution_time
            self.total_tasks_processed += 1

            log_event("task_completed_on_worker", {
                "worker_id": worker.worker_id,
                "specialty": worker.specialty.value,
                "execution_time": execution_time,
                "success": result.get("success", False)
            })

            return result

        except Exception as e:
            worker.error_count += 1
            worker.status = EmployeeStatus.ERROR
            self.total_errors += 1

            log_event("worker_task_failed", {
                "worker_id": worker.worker_id,
                "error": str(e)
            })

            return {
                "success": False,
                "error": str(e),
                "worker_id": worker.worker_id
            }

        finally:
            # Reset worker status
            worker.status = EmployeeStatus.IDLE
            worker.current_task = None

    async def _execute_task_on_worker(
        self,
        worker: EmployeeWorker,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Execute task using Employee agent.

        This is a simplified implementation.
        In production, this would:
        1. Create Employee agent instance
        2. Execute task with full agent capabilities
        3. Handle multi-step execution
        4. Return comprehensive result
        """
        # Build execution prompt
        prompt = f"""You are an Employee AI agent specializing in {worker.specialty.value}.

TASK: {task_description}

CONTEXT: {context or 'None'}

Execute this task to the best of your ability. Be thorough and accurate.
"""

        try:
            # Use LLM to execute task
            # In full implementation, this would use the Employee agent class
            result_text = await self.llm.chat(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.3
            )

            return {
                "success": True,
                "result": result_text,
                "worker_id": worker.worker_id,
                "specialty": worker.specialty.value
            }

        except Exception as e:
            raise ValueError(f"Task execution failed: {str(e)}")

    async def _process_queue(self):
        """Background task processor for queued tasks"""
        log_event("queue_processor_started", {})

        while self._running:
            try:
                # Check for queued tasks
                if not self.task_queue.empty():
                    # Find idle worker
                    idle_workers = [
                        w for w in self.workers.values()
                        if w.status == EmployeeStatus.IDLE
                    ]

                    if idle_workers:
                        # Get next task
                        task_item = await self.task_queue.get()

                        # Find best worker for this task
                        worker = self._find_best_worker(task_item["specialty"])

                        if worker:
                            # Execute task
                            result = await self._assign_to_worker(
                                worker,
                                task_item["description"],
                                task_item["context"]
                            )

                            # Set result on future
                            task_item["result_future"].set_result(result)

                            log_event("queued_task_processed", {
                                "worker_id": worker.worker_id,
                                "wait_time": (datetime.now() - task_item["queued_at"]).total_seconds()
                            })

                # Sleep briefly
                await asyncio.sleep(0.1)

            except Exception as e:
                log_event("queue_processor_error", {
                    "error": str(e)
                })
                await asyncio.sleep(1)

    async def execute_batch(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks in parallel.

        Args:
            tasks: List of task dicts with:
                - description: Task to execute
                - specialty: Optional specialty
                - context: Optional context

        Returns:
            List of results in same order as input
        """
        log_event("batch_execution_started", {
            "task_count": len(tasks)
        })

        start_time = datetime.now()

        # Create coroutines for all tasks
        task_coros = [
            self.assign_task(
                task_description=task["description"],
                specialty=task.get("specialty"),
                context=task.get("context")
            )
            for task in tasks
        ]

        # Execute all in parallel
        results = await asyncio.gather(*task_coros, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "task_index": i
                })
            else:
                processed_results.append(result)

        execution_time = (datetime.now() - start_time).total_seconds()

        log_event("batch_execution_completed", {
            "task_count": len(tasks),
            "execution_time": execution_time,
            "successful": sum(1 for r in processed_results if r.get("success")),
            "failed": sum(1 for r in processed_results if not r.get("success"))
        })

        return processed_results

    async def _determine_specialty(
        self,
        task_description: str
    ) -> EmployeeSpecialty:
        """
        Automatically determine best specialty for task.

        Uses keyword matching and LLM analysis.
        """
        task_lower = task_description.lower()

        # Keyword matching
        if any(kw in task_lower for kw in ["code", "program", "implement", "debug", "fix", "function"]):
            return EmployeeSpecialty.CODING

        if any(kw in task_lower for kw in ["write", "document", "report", "memo", "letter", "article"]):
            return EmployeeSpecialty.DOCUMENTS

        if any(kw in task_lower for kw in ["analyze", "data", "statistics", "chart", "graph", "calculate"]):
            return EmployeeSpecialty.DATA_ANALYSIS

        if any(kw in task_lower for kw in ["email", "message", "communicate", "send", "contact"]):
            return EmployeeSpecialty.COMMUNICATIONS

        # Default to general
        return EmployeeSpecialty.GENERAL

    def get_pool_status(self) -> Dict[str, Any]:
        """
        Get current pool status and statistics.

        Returns comprehensive status including:
        - Worker states
        - Queue status
        - Performance metrics
        """
        workers_by_status = {
            "idle": 0,
            "busy": 0,
            "error": 0
        }

        workers_by_specialty = {}

        worker_details = []

        for worker in self.workers.values():
            # Count by status
            workers_by_status[worker.status.value] += 1

            # Count by specialty
            specialty_key = worker.specialty.value
            if specialty_key not in workers_by_specialty:
                workers_by_specialty[specialty_key] = 0
            workers_by_specialty[specialty_key] += 1

            # Worker details
            worker_details.append({
                "worker_id": worker.worker_id,
                "specialty": worker.specialty.value,
                "status": worker.status.value,
                "current_task": worker.current_task,
                "tasks_completed": worker.tasks_completed,
                "total_execution_time": worker.total_execution_time,
                "error_count": worker.error_count,
                "avg_execution_time": (
                    worker.total_execution_time / worker.tasks_completed
                    if worker.tasks_completed > 0
                    else 0
                )
            })

        return {
            "pool_size": self.pool_size,
            "workers_by_status": workers_by_status,
            "workers_by_specialty": workers_by_specialty,
            "queue_size": self.task_queue.qsize(),
            "queue_capacity": self.max_queue_size,
            "total_tasks_processed": self.total_tasks_processed,
            "total_errors": self.total_errors,
            "success_rate": (
                (self.total_tasks_processed - self.total_errors) / self.total_tasks_processed
                if self.total_tasks_processed > 0
                else 0
            ),
            "workers": worker_details
        }

    def _get_specialty_distribution(self) -> Dict[str, int]:
        """Get count of workers by specialty"""
        distribution = {}
        for worker in self.workers.values():
            specialty = worker.specialty.value
            distribution[specialty] = distribution.get(specialty, 0) + 1
        return distribution

    async def shutdown(self):
        """Shutdown pool gracefully"""
        log_event("employee_pool_shutting_down", {
            "tasks_processed": self.total_tasks_processed
        })

        self._running = False

        if self._queue_processor_task:
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass

        log_event("employee_pool_shutdown_complete", {})
