"""
Benchmark API Routes

Control and monitor benchmark execution.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================


class BenchmarkInfo(BaseModel):
    """Information about a benchmark file."""

    name: str = Field(..., description="Benchmark name")
    domain: str = Field(..., description="Target domain")
    version: str = Field(default="1.0", description="Benchmark version")
    description: str = Field(default="", description="Benchmark description")
    task_count: int = Field(..., description="Total tasks")
    easy_count: int = Field(default=0)
    medium_count: int = Field(default=0)
    hard_count: int = Field(default=0)


class BenchmarkRunSummary(BaseModel):
    """Summary of a benchmark run."""

    id: UUID = Field(..., description="Run ID")
    benchmark_name: str = Field(..., description="Benchmark name")
    domain: str = Field(..., description="Domain")
    status: str = Field(..., description="Run status")
    tasks_completed: int = Field(default=0)
    tasks_total: int = Field(default=0)
    avg_score: float = Field(default=0.0)
    pass_rate: float = Field(default=0.0)
    cost_spent: float = Field(default=0.0)
    started_at: datetime = Field(...)
    ended_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)


class BenchmarkStatus(BaseModel):
    """Current benchmark execution status."""

    is_running: bool = Field(default=False)
    is_paused: bool = Field(default=False)
    current_run: Optional[BenchmarkRunSummary] = Field(default=None)
    progress_percent: float = Field(default=0.0)
    current_task: Optional[str] = Field(default=None)
    estimated_completion: Optional[datetime] = Field(default=None)


class BenchmarkDiscovery(BaseModel):
    """Available benchmarks."""

    domains: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Map of domain -> benchmark names",
    )
    total_benchmarks: int = Field(default=0)


class RunBenchmarkRequest(BaseModel):
    """Request to run a benchmark."""

    domain: Optional[str] = Field(
        default=None,
        description="Domain to run (None = all)",
    )
    benchmark_name: Optional[str] = Field(
        default=None,
        description="Specific benchmark (None = all in domain)",
    )


class RunBenchmarkResponse(BaseModel):
    """Response after starting benchmark."""

    status: str = Field(default="started")
    message: str = Field(default="")
    run_id: Optional[UUID] = Field(default=None)


# ============================================================================
# Router
# ============================================================================


router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


# Background task handle
_benchmark_task: Optional[asyncio.Task] = None


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/status", response_model=BenchmarkStatus)
async def get_status():
    """
    Get current benchmark execution status.

    Returns whether a benchmark is running, progress, and current task.
    """
    try:
        return await _get_benchmark_status()
    except Exception as e:
        logger.error(f"Failed to get benchmark status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover", response_model=BenchmarkDiscovery)
async def discover_benchmarks():
    """
    Discover available benchmark files.

    Scans the /benchmarks/ directory for YAML files.
    """
    try:
        from core.benchmark import get_benchmark_loader
        loader = get_benchmark_loader()
        discovered = loader.discover()

        return BenchmarkDiscovery(
            domains=discovered,
            total_benchmarks=sum(len(b) for b in discovered.values()),
        )
    except Exception as e:
        logger.error(f"Failed to discover benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=List[BenchmarkInfo])
async def list_benchmarks(
    domain: Optional[str] = Query(None, description="Filter by domain"),
):
    """
    List all available benchmarks with details.

    Args:
        domain: Optional domain filter
    """
    try:
        from core.benchmark import get_benchmark_loader
        loader = get_benchmark_loader()

        benchmarks = []

        if domain:
            loaded = loader.load_domain(domain)
        else:
            loaded = loader.load_all()

        for b in loaded:
            benchmarks.append(BenchmarkInfo(
                name=b.name,
                domain=b.domain,
                version=b.version,
                description=b.description,
                task_count=b.total_tasks,
                easy_count=b.easy_count,
                medium_count=b.medium_count,
                hard_count=b.hard_count,
            ))

        return benchmarks

    except Exception as e:
        logger.error(f"Failed to list benchmarks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=RunBenchmarkResponse)
async def run_benchmark(
    request: RunBenchmarkRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start benchmark execution.

    Args:
        request: Specifies which benchmark(s) to run

    This starts execution in the background and returns immediately.
    Use /status to monitor progress.
    """
    global _benchmark_task

    try:
        from core.benchmark import get_benchmark_executor, get_benchmark_loader
        executor = get_benchmark_executor()
        loader = get_benchmark_loader()

        # Check if already running
        if executor.is_running():
            raise HTTPException(
                status_code=409,
                detail="A benchmark is already running. Pause or wait for completion.",
            )

        # Validate benchmark exists
        if request.benchmark_name and request.domain:
            path = f"benchmarks/{request.domain}/{request.benchmark_name}.yaml"
            try:
                benchmark = loader.load(path)
            except FileNotFoundError:
                raise HTTPException(
                    status_code=404,
                    detail=f"Benchmark not found: {request.benchmark_name} in {request.domain}",
                )

            # Run specific benchmark in background
            background_tasks.add_task(_run_benchmark_async, benchmark)

            return RunBenchmarkResponse(
                status="started",
                message=f"Running benchmark: {benchmark.name}",
            )

        elif request.domain:
            # Run all benchmarks for domain
            benchmarks = loader.load_domain(request.domain)
            if not benchmarks:
                raise HTTPException(
                    status_code=404,
                    detail=f"No benchmarks found for domain: {request.domain}",
                )

            background_tasks.add_task(_run_domain_async, request.domain)

            return RunBenchmarkResponse(
                status="started",
                message=f"Running {len(benchmarks)} benchmarks for domain: {request.domain}",
            )

        else:
            # Run all benchmarks
            benchmarks = loader.load_all()
            if not benchmarks:
                raise HTTPException(
                    status_code=404,
                    detail="No benchmarks found",
                )

            background_tasks.add_task(_run_all_async)

            return RunBenchmarkResponse(
                status="started",
                message=f"Running all {len(benchmarks)} benchmarks",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_benchmark():
    """
    Pause benchmark execution.

    The current task will complete before pausing.
    """
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()

        if not executor.is_running():
            return {"status": "ok", "message": "No benchmark is running"}

        executor.pause()

        return {"status": "ok", "message": "Benchmark paused"}

    except Exception as e:
        logger.error(f"Failed to pause benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
async def resume_benchmark():
    """
    Resume paused benchmark execution.
    """
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()

        if not executor.is_paused():
            return {"status": "ok", "message": "No benchmark is paused"}

        executor.resume()

        return {"status": "ok", "message": "Benchmark resumed"}

    except Exception as e:
        logger.error(f"Failed to resume benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel")
async def cancel_benchmark():
    """
    Cancel benchmark execution.

    The current task will complete but no further tasks will run.
    """
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()

        if not executor.is_running() and not executor.is_paused():
            return {"status": "ok", "message": "No benchmark is running"}

        executor.cancel()

        return {"status": "ok", "message": "Benchmark cancelled"}

    except Exception as e:
        logger.error(f"Failed to cancel benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[BenchmarkRunSummary])
async def get_history(
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
):
    """
    Get recent benchmark runs.

    Args:
        limit: Maximum number of results
        domain: Optional domain filter
    """
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()

        runs = executor.get_runs(limit=limit)

        # Filter by domain if specified
        if domain:
            runs = [r for r in runs if r.domain == domain]

        return [
            BenchmarkRunSummary(
                id=r.id,
                benchmark_name=r.benchmark_name,
                domain=r.domain,
                status=r.status,
                tasks_completed=r.tasks_completed,
                tasks_total=r.tasks_total,
                avg_score=r.avg_score,
                pass_rate=r.pass_rate,
                cost_spent=r.cost_spent,
                started_at=r.started_at,
                ended_at=r.ended_at,
                duration_seconds=r.duration_seconds,
            )
            for r in runs
        ]

    except Exception as e:
        logger.error(f"Failed to get benchmark history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{run_id}", response_model=Dict[str, Any])
async def get_run_detail(run_id: UUID):
    """
    Get detailed information about a benchmark run.

    Args:
        run_id: The run ID to retrieve
    """
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()

        run = executor.get_run(run_id)
        if not run:
            raise HTTPException(
                status_code=404,
                detail=f"Run not found: {run_id}",
            )

        return run.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get run detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get benchmark execution statistics."""
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()
        return executor.get_stats()
    except Exception as e:
        logger.error(f"Failed to get benchmark stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================


async def _get_benchmark_status() -> BenchmarkStatus:
    """Get current benchmark status."""
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()

        progress = executor.get_progress()

        if progress:
            return BenchmarkStatus(
                is_running=executor.is_running(),
                is_paused=executor.is_paused(),
                current_run=BenchmarkRunSummary(
                    id=progress.run_id,
                    benchmark_name=progress.benchmark_name,
                    domain="",  # Would need to get from run
                    status="running" if not progress.is_paused else "paused",
                    tasks_completed=progress.completed_tasks,
                    tasks_total=progress.total_tasks,
                    avg_score=progress.avg_score,
                    pass_rate=0.0,
                    cost_spent=progress.cost_spent,
                    started_at=progress.started_at,
                ),
                progress_percent=progress.progress_percent,
                current_task=progress.current_task,
                estimated_completion=progress.estimated_completion,
            )

        return BenchmarkStatus(
            is_running=False,
            is_paused=False,
            current_run=None,
            progress_percent=0.0,
            current_task=None,
            estimated_completion=None,
        )

    except ImportError:
        return BenchmarkStatus()


async def _run_benchmark_async(benchmark) -> None:
    """Run a single benchmark asynchronously."""
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()
        await executor.run(benchmark)
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")


async def _run_domain_async(domain: str) -> None:
    """Run all benchmarks for a domain asynchronously."""
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()
        await executor.run_domain(domain)
    except Exception as e:
        logger.error(f"Domain benchmark execution failed: {e}")


async def _run_all_async() -> None:
    """Run all benchmarks asynchronously."""
    try:
        from core.benchmark import get_benchmark_executor
        executor = get_benchmark_executor()
        await executor.run_all()
    except Exception as e:
        logger.error(f"Full benchmark execution failed: {e}")
