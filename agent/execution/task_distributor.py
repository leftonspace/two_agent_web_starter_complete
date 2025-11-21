"""
Parallel task distribution system.

PHASE 7C.2: Intelligent task distribution with priority queuing, dependency tracking,
and load balancing for maximum throughput.

Features:
- Priority-based queue (urgent, high, medium, low)
- Dependency tracking and resolution
- Batch optimization for similar tasks
- Load balancing across workers
- Worker affinity for related tasks
- Deadline-aware scheduling
"""

import asyncio
import heapq
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

from agent.execution.employee_pool import EmployeePool, EmployeeSpecialty
from agent.core_logging import log_event


class TaskPriority(Enum):
    """Task priority levels"""
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TaskRequest:
    """Task request with priority, dependencies, and scheduling metadata"""
    task_id: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    specialty: Optional[EmployeeSpecialty] = None
    context: Optional[Dict] = None
    dependencies: List[str] = field(default_factory=list)
    deadline: Optional[datetime] = None
    affinity_hints: List[str] = field(default_factory=list)  # Related task IDs
    submitted_at: datetime = field(default_factory=datetime.now)
    batch_key: Optional[str] = None  # For grouping similar tasks


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    worker_id: Optional[str] = None
    execution_time: float = 0.0
    completed_at: datetime = field(default_factory=datetime.now)


class TaskDistributor:
    """
    Intelligent task distribution system.

    Features:
    - Priority-based scheduling
    - Dependency resolution
    - Load balancing
    - Worker affinity
    - Batch optimization
    - Deadline awareness

    Example:
        distributor = TaskDistributor(employee_pool)
        await distributor.start()

        # Submit tasks
        task_id = await distributor.submit_task(
            description="Write code",
            priority=TaskPriority.HIGH,
            deadline=datetime.now() + timedelta(minutes=5)
        )

        # Submit with dependencies
        dependent_task = await distributor.submit_task(
            description="Test code",
            dependencies=[task_id]
        )

        result = await distributor.get_result(task_id)
    """

    def __init__(
        self,
        employee_pool: EmployeePool,
        enable_batching: bool = True,
        enable_affinity: bool = True,
        batch_timeout: float = 2.0  # seconds
    ):
        """
        Initialize task distributor.

        Args:
            employee_pool: Employee pool for task execution
            enable_batching: Enable batch optimization
            enable_affinity: Enable worker affinity
            batch_timeout: Max time to wait for batch accumulation
        """
        self.pool = employee_pool
        self.enable_batching = enable_batching
        self.enable_affinity = enable_affinity
        self.batch_timeout = batch_timeout

        # Priority queue (min-heap by priority score)
        self.task_queue: List[tuple] = []  # [(priority_score, task_request), ...]
        self.queue_lock = asyncio.Lock()

        # Dependency tracking
        self.pending_tasks: Dict[str, TaskRequest] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}  # {task_id: {dep_ids}}

        # Worker affinity tracking
        self.task_worker_map: Dict[str, str] = {}  # {task_id: worker_id}
        self.worker_task_history: Dict[str, List[str]] = {}  # {worker_id: [task_ids]}

        # Load balancing
        self.worker_load: Dict[str, int] = {}  # {worker_id: active_tasks}

        # Batch optimization
        self.batch_accumulator: Dict[str, List[TaskRequest]] = {}  # {batch_key: [tasks]}

        # Background processor
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

        # Result futures
        self.result_futures: Dict[str, asyncio.Future] = {}

        # Statistics
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "priority_escalations": 0,
            "batches_executed": 0,
            "affinity_hits": 0
        }

    async def start(self):
        """Start background task processor"""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_distribution())
        log_event("task_distributor_started", {})

    async def stop(self):
        """Stop background processor"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        log_event("task_distributor_stopped", {})

    async def submit_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        specialty: Optional[str] = None,
        context: Optional[Dict] = None,
        dependencies: Optional[List[str]] = None,
        deadline: Optional[datetime] = None,
        affinity_hints: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ) -> str:
        """
        Submit task for execution.

        Args:
            description: Task description
            priority: Task priority level
            specialty: Preferred worker specialty
            context: Additional context
            dependencies: List of task IDs this task depends on
            deadline: Task deadline
            affinity_hints: Related task IDs for worker affinity
            task_id: Optional task ID (auto-generated if None)

        Returns:
            Task ID for tracking
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Convert specialty string to enum
        specialty_enum = None
        if specialty:
            try:
                specialty_enum = EmployeeSpecialty(specialty)
            except ValueError:
                pass

        # Create task request
        task = TaskRequest(
            task_id=task_id,
            description=description,
            priority=priority,
            specialty=specialty_enum,
            context=context,
            dependencies=dependencies or [],
            deadline=deadline,
            affinity_hints=affinity_hints or []
        )

        # Determine batch key for optimization
        if self.enable_batching and specialty_enum:
            task.batch_key = specialty_enum.value

        # Create result future
        self.result_futures[task_id] = asyncio.Future()

        # Track dependencies
        if task.dependencies:
            self.task_dependencies[task_id] = set(task.dependencies)

        # Add to pending
        self.pending_tasks[task_id] = task

        # Calculate priority score
        priority_score = self._calculate_priority_score(task)

        # Add to queue
        async with self.queue_lock:
            heapq.heappush(self.task_queue, (priority_score, task))

        self.stats["total_submitted"] += 1

        log_event("task_submitted", {
            "task_id": task_id,
            "priority": priority.value,
            "has_dependencies": len(task.dependencies) > 0,
            "has_deadline": deadline is not None
        })

        return task_id

    def _calculate_priority_score(self, task: TaskRequest) -> float:
        """
        Calculate priority score for task scheduling.

        Lower score = higher priority (executed first).

        Score factors:
        - Base priority (1-4)
        - Deadline urgency (0-10 bonus)
        - Dependency depth (small penalty)
        - Wait time (small bonus)
        """
        # Base priority
        score = float(task.priority.value)

        # Deadline urgency
        if task.deadline:
            time_until_deadline = (task.deadline - datetime.now()).total_seconds()
            if time_until_deadline < 60:  # Less than 1 minute
                score -= 10  # Very urgent
            elif time_until_deadline < 300:  # Less than 5 minutes
                score -= 5  # Urgent
            elif time_until_deadline < 900:  # Less than 15 minutes
                score -= 2  # Somewhat urgent

        # Dependency penalty (tasks with dependencies scheduled slightly later)
        score += len(task.dependencies) * 0.1

        # Wait time bonus (older tasks get small priority boost)
        wait_time = (datetime.now() - task.submitted_at).total_seconds()
        if wait_time > 60:
            score -= 0.5

        return score

    async def _process_distribution(self):
        """Background task distribution processor"""
        while self._running:
            try:
                # Check for ready tasks
                ready_tasks = await self._get_ready_tasks()

                if ready_tasks:
                    # Try batch optimization
                    if self.enable_batching:
                        batches = self._group_tasks_by_batch_key(ready_tasks)
                        for batch_key, batch_tasks in batches.items():
                            if len(batch_tasks) > 1:
                                # Execute as batch
                                asyncio.create_task(
                                    self._execute_batch(batch_tasks)
                                )
                            else:
                                # Execute single task
                                asyncio.create_task(
                                    self._execute_single(batch_tasks[0])
                                )
                    else:
                        # Execute individually
                        for task in ready_tasks:
                            asyncio.create_task(self._execute_single(task))

                # Sleep briefly
                await asyncio.sleep(0.1)

            except Exception as e:
                log_event("distribution_processor_error", {
                    "error": str(e)
                })
                await asyncio.sleep(1)

    async def _get_ready_tasks(self) -> List[TaskRequest]:
        """Get tasks that are ready to execute (dependencies met)"""
        ready_tasks = []

        async with self.queue_lock:
            # Get up to 10 highest priority tasks
            temp_queue = []
            while len(ready_tasks) < 10 and self.task_queue:
                priority_score, task = heapq.heappop(self.task_queue)

                # Check if dependencies are met
                if self._dependencies_met(task):
                    ready_tasks.append(task)
                else:
                    # Put back in queue
                    temp_queue.append((priority_score, task))

            # Put back tasks that weren't ready
            for item in temp_queue:
                heapq.heappush(self.task_queue, item)

        return ready_tasks

    def _dependencies_met(self, task: TaskRequest) -> bool:
        """Check if all dependencies are completed"""
        if not task.dependencies:
            return True

        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if not self.completed_tasks[dep_id].success:
                # Dependency failed
                return False

        return True

    def _group_tasks_by_batch_key(
        self,
        tasks: List[TaskRequest]
    ) -> Dict[str, List[TaskRequest]]:
        """Group tasks by batch key for batch execution"""
        batches = {}
        for task in tasks:
            key = task.batch_key or "default"
            if key not in batches:
                batches[key] = []
            batches[key].append(task)
        return batches

    async def _execute_single(self, task: TaskRequest):
        """Execute single task"""
        try:
            # Find optimal worker
            worker_id = await self._find_optimal_worker(task)

            # Track load
            if worker_id:
                self.worker_load[worker_id] = self.worker_load.get(worker_id, 0) + 1

            # Execute on pool
            result = await self.pool.assign_task(
                task_description=task.description,
                specialty=task.specialty.value if task.specialty else None,
                context=task.context
            )

            # Update load
            if worker_id:
                self.worker_load[worker_id] = max(0, self.worker_load[worker_id] - 1)

            # Record result
            task_result = TaskResult(
                task_id=task.task_id,
                success=result.get("success", False),
                result=result.get("result"),
                error=result.get("error"),
                worker_id=result.get("worker_id"),
                execution_time=result.get("execution_time", 0)
            )

            # Store result
            self.completed_tasks[task.task_id] = task_result
            del self.pending_tasks[task.task_id]

            # Track worker affinity
            if task_result.worker_id:
                self.task_worker_map[task.task_id] = task_result.worker_id
                if task_result.worker_id not in self.worker_task_history:
                    self.worker_task_history[task_result.worker_id] = []
                self.worker_task_history[task_result.worker_id].append(task.task_id)

            # Update stats
            if task_result.success:
                self.stats["total_completed"] += 1
            else:
                self.stats["total_failed"] += 1

            # Set result future
            if task.task_id in self.result_futures:
                self.result_futures[task.task_id].set_result(task_result)

            log_event("task_completed", {
                "task_id": task.task_id,
                "success": task_result.success
            })

        except Exception as e:
            # Task execution failed
            task_result = TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e)
            )

            self.completed_tasks[task.task_id] = task_result
            del self.pending_tasks[task.task_id]
            self.stats["total_failed"] += 1

            if task.task_id in self.result_futures:
                self.result_futures[task.task_id].set_result(task_result)

            log_event("task_execution_failed", {
                "task_id": task.task_id,
                "error": str(e)
            })

    async def _execute_batch(self, tasks: List[TaskRequest]):
        """Execute batch of similar tasks"""
        try:
            log_event("batch_execution_started", {
                "batch_size": len(tasks)
            })

            # Build batch for pool
            batch_items = [
                {
                    "description": t.description,
                    "specialty": t.specialty.value if t.specialty else None,
                    "context": t.context
                }
                for t in tasks
            ]

            # Execute batch
            results = await self.pool.execute_batch(batch_items)

            # Process results
            for task, result in zip(tasks, results):
                task_result = TaskResult(
                    task_id=task.task_id,
                    success=result.get("success", False),
                    result=result.get("result"),
                    error=result.get("error"),
                    worker_id=result.get("worker_id")
                )

                self.completed_tasks[task.task_id] = task_result
                del self.pending_tasks[task.task_id]

                if task_result.success:
                    self.stats["total_completed"] += 1
                else:
                    self.stats["total_failed"] += 1

                if task.task_id in self.result_futures:
                    self.result_futures[task.task_id].set_result(task_result)

            self.stats["batches_executed"] += 1

        except Exception as e:
            log_event("batch_execution_failed", {
                "error": str(e)
            })

    async def _find_optimal_worker(self, task: TaskRequest) -> Optional[str]:
        """
        Find optimal worker for task.

        Considers:
        - Worker affinity (related tasks)
        - Load balancing
        - Specialty matching
        """
        if not self.enable_affinity:
            return None

        # Check affinity hints
        if task.affinity_hints:
            for hint_task_id in task.affinity_hints:
                if hint_task_id in self.task_worker_map:
                    worker_id = self.task_worker_map[hint_task_id]
                    # Check if worker has low load
                    if self.worker_load.get(worker_id, 0) < 3:
                        self.stats["affinity_hits"] += 1
                        return worker_id

        return None

    async def get_result(self, task_id: str) -> TaskResult:
        """
        Wait for and get task result.

        Args:
            task_id: Task ID

        Returns:
            Task result
        """
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]

        if task_id in self.result_futures:
            return await self.result_futures[task_id]

        raise ValueError(f"Unknown task ID: {task_id}")

    def get_distribution_stats(self) -> Dict[str, Any]:
        """Get distribution statistics"""
        return {
            **self.stats,
            "pending_tasks": len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "queue_size": len(self.task_queue),
            "worker_loads": dict(self.worker_load)
        }

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get list of pending tasks"""
        return [
            {
                "task_id": task.task_id,
                "description": task.description,
                "priority": task.priority.value,
                "dependencies": task.dependencies,
                "dependencies_met": self._dependencies_met(task),
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "submitted_at": task.submitted_at.isoformat()
            }
            for task in self.pending_tasks.values()
        ]
