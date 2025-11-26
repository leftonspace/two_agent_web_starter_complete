"""
Benchmark Database Models

SQLAlchemy models for persisting benchmark runs and results.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    Index,
    ForeignKey,
)

from database.base import Base
from .cost_log import UUID  # Reuse UUID type


# ============================================================================
# Benchmark Run Model
# ============================================================================


class BenchmarkRunDB(Base):
    """
    Database model for benchmark runs.

    Stores information about a complete benchmark execution.
    """

    __tablename__ = "benchmark_runs"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    benchmark_name = Column(String(200), nullable=False, index=True)
    benchmark_version = Column(String(20), nullable=True)
    domain = Column(String(100), nullable=False, index=True)

    # Status
    status = Column(
        String(20),
        nullable=False,
        default="running",
        index=True,
    )  # running, paused, completed, failed, cancelled

    # Task counts
    tasks_total = Column(Integer, nullable=False, default=0)
    tasks_completed = Column(Integer, nullable=False, default=0)
    tasks_failed = Column(Integer, nullable=False, default=0)
    tasks_skipped = Column(Integer, nullable=False, default=0)

    # Score statistics
    avg_score = Column(Float, nullable=False, default=0.0)
    min_score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    pass_rate = Column(Float, nullable=False, default=0.0)  # Score > 0.5

    # Cost
    total_cost = Column(Float, nullable=False, default=0.0)
    budget_category = Column(String(50), nullable=True, default="benchmark")

    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Configuration (JSON)
    config = Column(Text, nullable=True)  # JSON: executor config used

    # Error information
    error = Column(Text, nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_benchmark_runs_domain_status", "domain", "status"),
        Index("ix_benchmark_runs_name_time", "benchmark_name", "started_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<BenchmarkRunDB(benchmark={self.benchmark_name}, "
            f"status={self.status}, score={self.avg_score:.2f})>"
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def get_config(self) -> Optional[Dict[str, Any]]:
        """Parse config JSON."""
        if self.config:
            return json.loads(self.config)
        return None

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set config from dict."""
        self.config = json.dumps(config)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "benchmark_name": self.benchmark_name,
            "benchmark_version": self.benchmark_version,
            "domain": self.domain,
            "status": self.status,
            "tasks": {
                "total": self.tasks_total,
                "completed": self.tasks_completed,
                "failed": self.tasks_failed,
                "skipped": self.tasks_skipped,
            },
            "scores": {
                "average": round(float(self.avg_score or 0), 3),
                "min": round(float(self.min_score or 0), 3) if self.min_score else None,
                "max": round(float(self.max_score or 0), 3) if self.max_score else None,
                "pass_rate": round(float(self.pass_rate or 0), 3),
            },
            "total_cost": round(float(self.total_cost or 0), 4),
            "budget_category": self.budget_category,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": round(self.duration_seconds, 2) if self.duration_seconds else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkRunDB":
        """Create from dictionary."""
        run = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            benchmark_name=data.get("benchmark_name", ""),
            benchmark_version=data.get("benchmark_version"),
            domain=data.get("domain", ""),
            status=data.get("status", "running"),
            tasks_total=data.get("tasks_total", 0),
            tasks_completed=data.get("tasks_completed", 0),
            tasks_failed=data.get("tasks_failed", 0),
            tasks_skipped=data.get("tasks_skipped", 0),
            avg_score=data.get("avg_score", 0.0),
            min_score=data.get("min_score"),
            max_score=data.get("max_score"),
            pass_rate=data.get("pass_rate", 0.0),
            total_cost=data.get("total_cost", 0.0),
            budget_category=data.get("budget_category", "benchmark"),
            started_at=data.get("started_at", datetime.utcnow()),
            ended_at=data.get("ended_at"),
            duration_seconds=data.get("duration_seconds"),
            error=data.get("error"),
        )

        if data.get("config"):
            run.set_config(data["config"])

        return run


# ============================================================================
# Benchmark Task Result Model
# ============================================================================


class BenchmarkTaskResultDB(Base):
    """
    Database model for individual benchmark task results.

    Stores the result of each task execution within a benchmark run.
    """

    __tablename__ = "benchmark_task_results"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    run_id = Column(
        UUID,
        ForeignKey("benchmark_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id = Column(String(200), nullable=False)  # ID from benchmark file

    # Status
    status = Column(
        String(20),
        nullable=False,
        index=True,
    )  # completed, failed, skipped

    # Score
    score = Column(Float, nullable=True)

    # Execution details
    specialist_id = Column(UUID, nullable=True, index=True)
    specialist_name = Column(String(200), nullable=True)
    model_used = Column(String(100), nullable=True)

    # Cost and timing
    cost = Column(Float, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    # Task metadata
    difficulty = Column(String(20), nullable=True)  # easy, medium, hard
    expected_domain = Column(String(100), nullable=True)
    actual_domain = Column(String(100), nullable=True)

    # Verification details (JSON)
    verification_results = Column(Text, nullable=True)  # JSON array of check results

    # Error information
    error = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)  # For skipped tasks

    # Timestamps
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_benchmark_task_results_run_task", "run_id", "task_id"),
        Index("ix_benchmark_task_results_specialist", "specialist_id", "executed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<BenchmarkTaskResultDB(task={self.task_id}, "
            f"status={self.status}, score={self.score})>"
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def get_verification_results(self) -> List[Dict[str, Any]]:
        """Parse verification results JSON."""
        if self.verification_results:
            return json.loads(self.verification_results)
        return []

    def set_verification_results(self, results: List[Dict[str, Any]]) -> None:
        """Set verification results from list."""
        self.verification_results = json.dumps(results)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "run_id": str(self.run_id) if self.run_id else None,
            "task_id": self.task_id,
            "status": self.status,
            "score": round(float(self.score), 3) if self.score is not None else None,
            "specialist_id": str(self.specialist_id) if self.specialist_id else None,
            "specialist_name": self.specialist_name,
            "model_used": self.model_used,
            "cost": round(float(self.cost), 4) if self.cost else None,
            "execution_time_ms": self.execution_time_ms,
            "difficulty": self.difficulty,
            "expected_domain": self.expected_domain,
            "actual_domain": self.actual_domain,
            "verification": self.get_verification_results(),
            "error": self.error,
            "reason": self.reason,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkTaskResultDB":
        """Create from dictionary."""
        result = cls(
            id=uuid.UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id"),
            run_id=uuid.UUID(data["run_id"]) if isinstance(data.get("run_id"), str) else data.get("run_id"),
            task_id=data.get("task_id", ""),
            status=data.get("status", "completed"),
            score=data.get("score"),
            specialist_id=uuid.UUID(data["specialist_id"]) if isinstance(data.get("specialist_id"), str) else data.get("specialist_id"),
            specialist_name=data.get("specialist_name"),
            model_used=data.get("model_used"),
            cost=data.get("cost"),
            execution_time_ms=data.get("execution_time_ms"),
            difficulty=data.get("difficulty"),
            expected_domain=data.get("expected_domain"),
            actual_domain=data.get("actual_domain"),
            error=data.get("error"),
            reason=data.get("reason"),
            executed_at=data.get("executed_at", datetime.utcnow()),
        )

        if data.get("verification"):
            result.set_verification_results(data["verification"])

        return result


# ============================================================================
# Benchmark Statistics Model
# ============================================================================


class BenchmarkStatsDB(Base):
    """
    Aggregated statistics for benchmark executions.

    Tracks overall benchmark performance across runs.
    """

    __tablename__ = "benchmark_stats"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    benchmark_name = Column(String(200), nullable=True, index=True)  # NULL = all benchmarks
    domain = Column(String(100), nullable=True, index=True)  # NULL = all domains

    # Run counts
    total_runs = Column(Integer, nullable=False, default=0)
    completed_runs = Column(Integer, nullable=False, default=0)
    failed_runs = Column(Integer, nullable=False, default=0)

    # Task counts
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)

    # Score statistics
    avg_score = Column(Float, nullable=False, default=0.0)
    best_score = Column(Float, nullable=True)
    worst_score = Column(Float, nullable=True)
    score_std = Column(Float, nullable=True)

    # Pass rate
    avg_pass_rate = Column(Float, nullable=False, default=0.0)

    # Cost statistics
    total_cost = Column(Float, nullable=False, default=0.0)
    avg_cost_per_run = Column(Float, nullable=False, default=0.0)
    avg_cost_per_task = Column(Float, nullable=False, default=0.0)

    # Time statistics
    avg_duration_seconds = Column(Float, nullable=True)
    avg_task_time_ms = Column(Float, nullable=True)

    # Time range
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_benchmark_stats_domain_name", "domain", "benchmark_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<BenchmarkStatsDB(benchmark={self.benchmark_name}, "
            f"domain={self.domain}, runs={self.total_runs})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_name": self.benchmark_name,
            "domain": self.domain,
            "runs": {
                "total": self.total_runs,
                "completed": self.completed_runs,
                "failed": self.failed_runs,
            },
            "tasks": {
                "total": self.total_tasks,
                "completed": self.completed_tasks,
                "failed": self.failed_tasks,
            },
            "scores": {
                "average": round(float(self.avg_score or 0), 3),
                "best": round(float(self.best_score or 0), 3) if self.best_score else None,
                "worst": round(float(self.worst_score or 0), 3) if self.worst_score else None,
                "std": round(float(self.score_std or 0), 3) if self.score_std else None,
                "avg_pass_rate": round(float(self.avg_pass_rate or 0), 3),
            },
            "costs": {
                "total": round(float(self.total_cost or 0), 4),
                "avg_per_run": round(float(self.avg_cost_per_run or 0), 4),
                "avg_per_task": round(float(self.avg_cost_per_task or 0), 6),
            },
            "timing": {
                "avg_duration_seconds": round(self.avg_duration_seconds, 2) if self.avg_duration_seconds else None,
                "avg_task_time_ms": round(self.avg_task_time_ms, 2) if self.avg_task_time_ms else None,
            },
            "period": {
                "start": self.period_start.isoformat() if self.period_start else None,
                "end": self.period_end.isoformat() if self.period_end else None,
            },
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }


# ============================================================================
# Benchmark Definition Model (Optional - for storing benchmark metadata)
# ============================================================================


class BenchmarkDefinitionDB(Base):
    """
    Database model for benchmark definitions.

    Stores metadata about registered benchmarks (optional - benchmarks
    can also be loaded directly from YAML files).
    """

    __tablename__ = "benchmark_definitions"

    # Identity
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True, index=True)
    domain = Column(String(100), nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1.0")

    # Description
    description = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=True)

    # Task information
    task_count = Column(Integer, nullable=False, default=0)
    easy_count = Column(Integer, nullable=False, default=0)
    medium_count = Column(Integer, nullable=False, default=0)
    hard_count = Column(Integer, nullable=False, default=0)

    # File location
    file_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 of file content

    # Status
    is_active = Column(Boolean, nullable=False, default=True)

    # Run statistics (denormalized for quick access)
    last_run_at = Column(DateTime, nullable=True)
    last_avg_score = Column(Float, nullable=True)
    run_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<BenchmarkDefinitionDB(name={self.name}, "
            f"domain={self.domain}, tasks={self.task_count})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "domain": self.domain,
            "version": self.version,
            "description": self.description,
            "created_by": self.created_by,
            "tasks": {
                "total": self.task_count,
                "easy": self.easy_count,
                "medium": self.medium_count,
                "hard": self.hard_count,
            },
            "file_path": self.file_path,
            "is_active": bool(self.is_active),
            "last_run": {
                "at": self.last_run_at.isoformat() if self.last_run_at else None,
                "avg_score": round(float(self.last_avg_score or 0), 3) if self.last_avg_score else None,
            },
            "run_count": self.run_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
