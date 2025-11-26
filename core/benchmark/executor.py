"""
PHASE 7.5: Benchmark Executor

Execute benchmark files against specialists.
Supports pause/resume, budget limits, and score recording.

Usage:
    from core.benchmark import BenchmarkExecutor, get_benchmark_executor

    executor = get_benchmark_executor()

    # Run a single benchmark
    run = await executor.run(benchmark)

    # Run all benchmarks for a domain
    runs = await executor.run_domain("code_generation")

    # Pause/resume
    executor.pause()
    executor.resume()
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Literal, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .loader import Benchmark, BenchmarkLoader, BenchmarkTask, get_benchmark_loader
from .verifier import Verifier, VerificationSummary, get_verifier

if TYPE_CHECKING:
    from core.routing import TaskRouter


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Benchmark Task Result
# ============================================================================


class BenchmarkTaskResult(BaseModel):
    """Result of a single benchmark task."""

    task_id: str = Field(..., description="Task ID from benchmark")
    status: Literal["completed", "failed", "skipped"] = Field(
        ...,
        description="Task execution status",
    )
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Verification score",
    )
    specialist_id: Optional[UUID] = Field(
        default=None,
        description="Specialist that handled the task",
    )
    model_used: Optional[str] = Field(
        default=None,
        description="Model used for execution",
    )
    cost: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Cost in CAD",
    )
    execution_time_ms: Optional[int] = Field(
        default=None,
        ge=0,
        description="Execution time in milliseconds",
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason if skipped/failed",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
    )
    verification: Optional[VerificationSummary] = Field(
        default=None,
        description="Detailed verification results",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "score": round(self.score, 3) if self.score else None,
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "model_used": self.model_used,
            "cost": round(self.cost, 4) if self.cost else None,
            "execution_time_ms": self.execution_time_ms,
            "reason": self.reason,
            "error": self.error,
        }


# ============================================================================
# Benchmark Run
# ============================================================================


class BenchmarkRun(BaseModel):
    """Complete benchmark run with all results."""

    id: UUID = Field(default_factory=uuid4, description="Run ID")
    benchmark_name: str = Field(..., description="Benchmark name")
    domain: str = Field(..., description="Benchmark domain")
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Start time",
    )
    ended_at: Optional[datetime] = Field(
        default=None,
        description="End time",
    )
    status: Literal["running", "paused", "completed", "failed", "cancelled"] = Field(
        default="running",
        description="Run status",
    )
    tasks_completed: int = Field(default=0, description="Tasks completed")
    tasks_total: int = Field(default=0, description="Total tasks")
    avg_score: float = Field(default=0.0, description="Average score")
    cost_spent: float = Field(default=0.0, description="Total cost")
    results: List[BenchmarkTaskResult] = Field(
        default_factory=list,
        description="Task results",
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get run duration in seconds."""
        if self.ended_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    @property
    def pass_rate(self) -> float:
        """Get pass rate (score > 0.5)."""
        passed = sum(1 for r in self.results if r.score and r.score > 0.5)
        return passed / max(len(self.results), 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "benchmark_name": self.benchmark_name,
            "domain": self.domain,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "status": self.status,
            "tasks_completed": self.tasks_completed,
            "tasks_total": self.tasks_total,
            "avg_score": round(self.avg_score, 3),
            "pass_rate": round(self.pass_rate, 3),
            "cost_spent": round(self.cost_spent, 4),
            "duration_seconds": round(self.duration_seconds, 2) if self.duration_seconds else None,
        }


# ============================================================================
# Benchmark Progress
# ============================================================================


class BenchmarkProgress(BaseModel):
    """Current progress of a benchmark run."""

    benchmark_name: str = Field(..., description="Benchmark name")
    run_id: UUID = Field(..., description="Run ID")
    total_tasks: int = Field(default=0, description="Total tasks")
    completed_tasks: int = Field(default=0, description="Completed tasks")
    current_task: Optional[str] = Field(
        default=None,
        description="Current task ID",
    )
    avg_score: float = Field(default=0.0, description="Average score so far")
    cost_spent: float = Field(default=0.0, description="Cost spent so far")
    started_at: datetime = Field(..., description="Start time")
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time",
    )
    is_paused: bool = Field(default=False, description="Whether run is paused")

    @property
    def progress_percent(self) -> float:
        """Get progress percentage."""
        return (self.completed_tasks / max(self.total_tasks, 1)) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_name": self.benchmark_name,
            "run_id": str(self.run_id),
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "progress_percent": round(self.progress_percent, 1),
            "current_task": self.current_task,
            "avg_score": round(self.avg_score, 3),
            "cost_spent": round(self.cost_spent, 4),
            "is_paused": self.is_paused,
        }


# ============================================================================
# Executor Configuration
# ============================================================================


class ExecutorConfig(BaseModel):
    """Configuration for benchmark executor."""

    # Budget
    budget_category: str = Field(
        default="benchmark",
        description="Budget category to use",
    )
    max_cost_per_run: float = Field(
        default=5.0,
        gt=0,
        description="Maximum cost per benchmark run (CAD)",
    )
    cost_check_threshold: float = Field(
        default=0.01,
        ge=0,
        description="Minimum cost to check budget for",
    )

    # Execution
    task_timeout_seconds: int = Field(
        default=120,
        gt=0,
        description="Default task timeout",
    )
    retry_on_failure: bool = Field(
        default=False,
        description="Retry failed tasks once",
    )

    # Scoring
    record_scores: bool = Field(
        default=True,
        description="Record scores to specialist performance",
    )
    score_weight: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Weight of benchmark scores vs production",
    )


# ============================================================================
# Benchmark Executor
# ============================================================================


class BenchmarkExecutor:
    """
    Execute benchmark files.

    Features:
    - Runs tasks sequentially
    - Uses BENCHMARK budget (separate from production)
    - Can be paused/resumed
    - Feeds scores into specialist evaluation
    - Stops if budget exceeded

    Usage:
        executor = BenchmarkExecutor()
        run = await executor.run(benchmark)
    """

    def __init__(
        self,
        config: Optional[ExecutorConfig] = None,
        loader: Optional[BenchmarkLoader] = None,
        verifier: Optional[Verifier] = None,
        router: Optional[Any] = None,
    ):
        """
        Initialize the executor.

        Args:
            config: Executor configuration
            loader: Benchmark loader
            verifier: Result verifier
            router: Task router for execution
        """
        self._config = config or ExecutorConfig()
        self._loader = loader
        self._verifier = verifier
        self._router = router

        # State
        self._paused = False
        self._cancelled = False
        self._current_run: Optional[BenchmarkRun] = None
        self._current_task: Optional[str] = None

        # Run history
        self._runs: List[BenchmarkRun] = []

        # Callbacks
        self._on_task_complete: Optional[Callable] = None
        self._on_run_complete: Optional[Callable] = None

        # Statistics
        self._total_runs = 0
        self._total_tasks_executed = 0
        self._total_cost = 0.0

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> ExecutorConfig:
        """Get executor configuration."""
        return self._config

    @property
    def loader(self) -> BenchmarkLoader:
        """Get benchmark loader (lazy load)."""
        if self._loader is None:
            self._loader = get_benchmark_loader()
        return self._loader

    @property
    def verifier(self) -> Verifier:
        """Get verifier (lazy load)."""
        if self._verifier is None:
            self._verifier = get_verifier()
        return self._verifier

    @property
    def router(self) -> Any:
        """Get task router (lazy load)."""
        if self._router is None:
            try:
                from core.routing import get_task_router
                self._router = get_task_router()
            except ImportError:
                logger.warning("Task router not available")
        return self._router

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    async def run(self, benchmark: Benchmark) -> BenchmarkRun:
        """
        Run a benchmark.

        Args:
            benchmark: Benchmark to execute

        Returns:
            BenchmarkRun with all results
        """
        self._total_runs += 1
        self._paused = False
        self._cancelled = False

        run = BenchmarkRun(
            benchmark_name=benchmark.name,
            domain=benchmark.domain,
            started_at=datetime.utcnow(),
            status="running",
            tasks_total=benchmark.total_tasks,
        )
        self._current_run = run
        self._runs.append(run)

        logger.info(f"Starting benchmark: {benchmark.name} ({benchmark.total_tasks} tasks)")

        results = []
        total_cost = 0.0
        total_score = 0.0
        scored_count = 0

        for task in benchmark.tasks:
            # Check if cancelled
            if self._cancelled:
                run.status = "cancelled"
                logger.info(f"Benchmark cancelled: {benchmark.name}")
                break

            # Check if paused
            if self._paused:
                run.status = "paused"
                logger.info(f"Benchmark paused: {benchmark.name}")
                break

            # Check budget
            if total_cost >= self._config.max_cost_per_run:
                run.status = "paused"
                results.append(BenchmarkTaskResult(
                    task_id=task.id,
                    status="skipped",
                    reason="Budget limit reached",
                ))
                logger.warning(f"Budget limit reached for benchmark: {benchmark.name}")
                break

            # Execute task
            self._current_task = task.id
            task_result = await self._execute_task(task, benchmark.domain)
            results.append(task_result)

            # Update totals
            if task_result.cost:
                total_cost += task_result.cost
            if task_result.score is not None:
                total_score += task_result.score
                scored_count += 1

            run.tasks_completed += 1
            self._total_tasks_executed += 1

            # Callback
            if self._on_task_complete:
                try:
                    self._on_task_complete(task_result, run)
                except Exception as e:
                    logger.error(f"Task complete callback failed: {e}")

            # Small delay between tasks
            await asyncio.sleep(0.1)

        # Finalize
        run.ended_at = datetime.utcnow()
        run.results = results
        run.cost_spent = total_cost
        run.avg_score = total_score / max(scored_count, 1)
        self._total_cost += total_cost

        if run.status == "running":
            run.status = "completed" if run.tasks_completed == benchmark.total_tasks else "failed"

        self._current_run = None
        self._current_task = None

        logger.info(
            f"Benchmark completed: {benchmark.name} - "
            f"Score: {run.avg_score:.2f}, Cost: ${run.cost_spent:.4f}"
        )

        # Callback
        if self._on_run_complete:
            try:
                self._on_run_complete(run)
            except Exception as e:
                logger.error(f"Run complete callback failed: {e}")

        return run

    async def _execute_task(
        self,
        task: BenchmarkTask,
        domain: str,
    ) -> BenchmarkTaskResult:
        """Execute a single benchmark task."""
        start_time = datetime.utcnow()

        try:
            # Use router if available
            if self.router:
                routing, result = await self.router.route_and_execute(
                    request=task.prompt,
                    context={"benchmark": True, "domain": domain},
                )

                # Verify result
                verification = await self.verifier.verify_detailed(
                    result,
                    task.verification,
                )

                # Record score to specialist if configured
                if self._config.record_scores and routing.specialist_id:
                    await self._record_score(
                        specialist_id=routing.specialist_id,
                        score=verification.final_score,
                        task_id=task.id,
                    )

                execution_time = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                return BenchmarkTaskResult(
                    task_id=task.id,
                    status="completed",
                    score=verification.final_score,
                    specialist_id=routing.specialist_id,
                    model_used=routing.model_selection.model if routing.model_selection else None,
                    cost=result.cost_cad if hasattr(result, "cost_cad") else 0.0,
                    execution_time_ms=execution_time,
                    verification=verification,
                )

            else:
                # Mock execution for testing
                return await self._mock_execute(task, start_time)

        except asyncio.TimeoutError:
            return BenchmarkTaskResult(
                task_id=task.id,
                status="failed",
                error="Task timeout exceeded",
            )
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return BenchmarkTaskResult(
                task_id=task.id,
                status="failed",
                error=str(e),
            )

    async def _mock_execute(
        self,
        task: BenchmarkTask,
        start_time: datetime,
    ) -> BenchmarkTaskResult:
        """Mock execution for testing without full infrastructure."""
        # Simulate execution time
        await asyncio.sleep(0.05)

        # Generate mock response based on task
        mock_response = self._generate_mock_response(task)

        # Verify mock response
        verification = await self.verifier.verify_detailed(
            mock_response,
            task.verification,
        )

        execution_time = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )

        return BenchmarkTaskResult(
            task_id=task.id,
            status="completed",
            score=verification.final_score,
            specialist_id=None,
            model_used="mock",
            cost=0.001,  # Nominal cost for mock
            execution_time_ms=execution_time,
            verification=verification,
        )

    def _generate_mock_response(self, task: BenchmarkTask) -> str:
        """Generate a mock response for testing."""
        if task.expected_domain == "code_generation" or "code" in task.prompt.lower():
            return '''```python
def example_function(data: str) -> str:
    """Process the input data.

    Args:
        data: Input string to process

    Returns:
        Processed string
    """
    try:
        result = data.strip().upper()
        return result
    except Exception as e:
        raise ValueError(f"Processing failed: {e}")
```'''
        elif task.expected_domain == "business_documents" or "report" in task.prompt.lower():
            return '''# Report

## Executive Summary

This report provides an overview of the requested analysis.

## Key Findings

- Finding 1: Important insight
- Finding 2: Critical observation
- Finding 3: Notable trend

## Recommendations

1. First recommendation
2. Second recommendation

Best regards,
The Analysis Team'''
        else:
            return f"Response to: {task.prompt[:100]}"

    async def _record_score(
        self,
        specialist_id: UUID,
        score: float,
        task_id: str,
    ) -> None:
        """Record benchmark score to specialist."""
        try:
            # Try to get pool manager and record score
            from core.domain import get_pool_manager
            pool_manager = get_pool_manager()
            specialist = pool_manager.get_specialist(specialist_id)
            if specialist:
                specialist.record_score(
                    score,
                    source="benchmark",
                    task_id=task_id,
                )
        except Exception as e:
            logger.debug(f"Could not record score to specialist: {e}")

    # -------------------------------------------------------------------------
    # Domain and Batch Execution
    # -------------------------------------------------------------------------

    async def run_domain(self, domain: str) -> List[BenchmarkRun]:
        """
        Run all benchmarks for a domain.

        Args:
            domain: Domain name

        Returns:
            List of BenchmarkRuns
        """
        benchmarks = self.loader.load_domain(domain)
        runs = []

        for benchmark in benchmarks:
            if self._cancelled:
                break
            run = await self.run(benchmark)
            runs.append(run)

        return runs

    async def run_all(self) -> List[BenchmarkRun]:
        """
        Run all available benchmarks.

        Returns:
            List of all BenchmarkRuns
        """
        benchmarks = self.loader.load_all()
        runs = []

        for benchmark in benchmarks:
            if self._cancelled:
                break
            run = await self.run(benchmark)
            runs.append(run)

        return runs

    # -------------------------------------------------------------------------
    # Control
    # -------------------------------------------------------------------------

    def pause(self) -> None:
        """Pause the current benchmark run."""
        self._paused = True
        logger.info("Benchmark execution paused")

    def resume(self) -> None:
        """Resume benchmark execution."""
        self._paused = False
        logger.info("Benchmark execution resumed")

    def cancel(self) -> None:
        """Cancel the current benchmark run."""
        self._cancelled = True
        logger.info("Benchmark execution cancelled")

    def is_running(self) -> bool:
        """Check if a benchmark is currently running."""
        return self._current_run is not None and not self._paused

    def is_paused(self) -> bool:
        """Check if execution is paused."""
        return self._paused

    # -------------------------------------------------------------------------
    # Progress
    # -------------------------------------------------------------------------

    def get_progress(self) -> Optional[BenchmarkProgress]:
        """Get current execution progress."""
        if not self._current_run:
            return None

        run = self._current_run

        # Estimate completion
        estimated_completion = None
        if run.tasks_completed > 0:
            elapsed = (datetime.utcnow() - run.started_at).total_seconds()
            avg_time_per_task = elapsed / run.tasks_completed
            remaining_tasks = run.tasks_total - run.tasks_completed
            remaining_seconds = avg_time_per_task * remaining_tasks
            estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_seconds)

        # Calculate current average score
        scored_results = [r for r in run.results if r.score is not None]
        avg_score = (
            sum(r.score for r in scored_results) / len(scored_results)
            if scored_results
            else 0.0
        )

        return BenchmarkProgress(
            benchmark_name=run.benchmark_name,
            run_id=run.id,
            total_tasks=run.tasks_total,
            completed_tasks=run.tasks_completed,
            current_task=self._current_task,
            avg_score=avg_score,
            cost_spent=run.cost_spent,
            started_at=run.started_at,
            estimated_completion=estimated_completion,
            is_paused=self._paused,
        )

    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------

    def on_task_complete(self, callback: Callable) -> None:
        """Set callback for task completion."""
        self._on_task_complete = callback

    def on_run_complete(self, callback: Callable) -> None:
        """Set callback for run completion."""
        self._on_run_complete = callback

    # -------------------------------------------------------------------------
    # History
    # -------------------------------------------------------------------------

    def get_runs(self, limit: int = 10) -> List[BenchmarkRun]:
        """Get recent benchmark runs."""
        return self._runs[-limit:]

    def get_run(self, run_id: UUID) -> Optional[BenchmarkRun]:
        """Get a specific run by ID."""
        for run in self._runs:
            if run.id == run_id:
                return run
        return None

    def clear_history(self) -> int:
        """Clear run history. Returns items cleared."""
        count = len(self._runs)
        self._runs.clear()
        return count

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "total_runs": self._total_runs,
            "total_tasks_executed": self._total_tasks_executed,
            "total_cost": round(self._total_cost, 4),
            "runs_in_history": len(self._runs),
            "is_running": self.is_running(),
            "is_paused": self.is_paused(),
        }

    def reset_stats(self) -> None:
        """Reset executor statistics."""
        self._total_runs = 0
        self._total_tasks_executed = 0
        self._total_cost = 0.0


# ============================================================================
# Singleton Instance
# ============================================================================


_benchmark_executor: Optional[BenchmarkExecutor] = None


def get_benchmark_executor() -> BenchmarkExecutor:
    """Get the global benchmark executor."""
    global _benchmark_executor
    if _benchmark_executor is None:
        _benchmark_executor = BenchmarkExecutor()
    return _benchmark_executor


def reset_benchmark_executor() -> None:
    """Reset the global benchmark executor (for testing)."""
    global _benchmark_executor
    _benchmark_executor = None
