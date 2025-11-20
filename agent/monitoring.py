"""
PHASE 5.6: Monitoring & Alerting - Metrics Collection

Comprehensive monitoring system for tracking mission metrics, tool usage,
error rates, and system health.

Features:
- Mission success/failure rate tracking
- Cost per mission tracking
- Execution time tracking
- Tool usage statistics
- Error rate tracking by type
- Time series data storage
- Real-time and historical queries
- Health check monitoring

Usage:
    >>> from agent.monitoring import get_metrics_collector
    >>> metrics = get_metrics_collector()
    >>>
    >>> # Record mission completion
    >>> metrics.record_mission(
    ...     mission_id="mission_123",
    ...     status="success",
    ...     cost_usd=1.25,
    ...     duration_seconds=120,
    ...     iterations=3
    ... )
    >>>
    >>> # Get metrics
    >>> stats = metrics.get_mission_stats(hours=24)
    >>> print(f"Success rate: {stats['success_rate']:.1%}")
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import paths module
try:
    import paths as paths_module
    PATHS_AVAILABLE = True
except ImportError:
    PATHS_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


class MetricType(Enum):
    """Types of metrics tracked."""
    MISSION = "mission"
    TOOL = "tool"
    ERROR = "error"
    HEALTH = "health"


class MissionStatus(Enum):
    """Mission completion status."""
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"
    TIMEOUT = "timeout"


@dataclass
class MissionMetric:
    """Mission execution metrics."""
    mission_id: str
    status: str
    cost_usd: float
    duration_seconds: float
    iterations: int
    timestamp: str
    domain: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolMetric:
    """Tool execution metrics."""
    tool_name: str
    execution_count: int
    success_count: int
    failure_count: int
    avg_duration_seconds: float
    total_cost_usd: float
    last_used: str


@dataclass
class ErrorMetric:
    """Error tracking metrics."""
    error_type: str
    error_message: str
    count: int
    first_seen: str
    last_seen: str
    mission_ids: List[str] = field(default_factory=list)


@dataclass
class HealthMetric:
    """System health metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_missions: int
    queue_length: int
    status: str  # healthy, degraded, unhealthy


# ══════════════════════════════════════════════════════════════════════
# Database Schema
# ══════════════════════════════════════════════════════════════════════


MONITORING_SCHEMA = """
-- Mission metrics (time series)
CREATE TABLE IF NOT EXISTS mission_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    status TEXT NOT NULL,
    cost_usd REAL NOT NULL,
    duration_seconds REAL NOT NULL,
    iterations INTEGER NOT NULL,
    domain TEXT,
    error_type TEXT,
    error_message TEXT,
    metadata TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mission_metrics_timestamp
    ON mission_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_mission_metrics_status
    ON mission_metrics(status);
CREATE INDEX IF NOT EXISTS idx_mission_metrics_domain
    ON mission_metrics(domain);

-- Tool usage metrics (aggregated)
CREATE TABLE IF NOT EXISTS tool_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL UNIQUE,
    execution_count INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    avg_duration_seconds REAL NOT NULL DEFAULT 0,
    total_cost_usd REAL NOT NULL DEFAULT 0,
    last_used TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tool_metrics_name
    ON tool_metrics(tool_name);

-- Error metrics (aggregated)
CREATE TABLE IF NOT EXISTS error_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    mission_ids TEXT,  -- JSON array
    UNIQUE(error_type, error_message)
);

CREATE INDEX IF NOT EXISTS idx_error_metrics_type
    ON error_metrics(error_type);
CREATE INDEX IF NOT EXISTS idx_error_metrics_last_seen
    ON error_metrics(last_seen);

-- Health check metrics (time series)
CREATE TABLE IF NOT EXISTS health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_percent REAL,
    memory_percent REAL,
    disk_percent REAL,
    active_missions INTEGER NOT NULL DEFAULT 0,
    queue_length INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_health_metrics_timestamp
    ON health_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_health_metrics_status
    ON health_metrics(status);
"""


# ══════════════════════════════════════════════════════════════════════
# Metrics Collector
# ══════════════════════════════════════════════════════════════════════


class MetricsCollector:
    """
    Metrics collection and storage system.

    Tracks mission metrics, tool usage, errors, and health checks.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize metrics collector.

        Args:
            db_path: Path to SQLite database (None = default location)
        """
        if db_path is None:
            if PATHS_AVAILABLE:
                db_path = paths_module.get_data_dir() / "monitoring.db"
            else:
                db_path = Path(__file__).parent.parent / "data" / "monitoring.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(MONITORING_SCHEMA)
            conn.commit()

    def _now(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    # ──────────────────────────────────────────────────────────────────
    # Mission Metrics
    # ──────────────────────────────────────────────────────────────────

    def record_mission(
        self,
        mission_id: str,
        status: str,
        cost_usd: float,
        duration_seconds: float,
        iterations: int,
        domain: Optional[str] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record mission completion metrics.

        Args:
            mission_id: Mission identifier
            status: Mission status (success, failed, aborted, timeout)
            cost_usd: Total cost in USD
            duration_seconds: Execution duration
            iterations: Number of iterations completed
            domain: Mission domain (coding, finance, etc.)
            error_type: Error type if failed
            error_message: Error message if failed
            metadata: Additional metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO mission_metrics (
                    mission_id, status, cost_usd, duration_seconds, iterations,
                    domain, error_type, error_message, metadata, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mission_id,
                status,
                cost_usd,
                duration_seconds,
                iterations,
                domain,
                error_type,
                error_message,
                json.dumps(metadata) if metadata else None,
                self._now(),
            ))
            conn.commit()

        # Also record error if failed
        if error_type and error_message:
            self.record_error(error_type, error_message, mission_id)

    def get_mission_stats(
        self,
        hours: int = 24,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get mission statistics for time period.

        Args:
            hours: Number of hours to look back
            domain: Optional domain filter

        Returns:
            Dict with mission statistics
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT
                    COUNT(*) as total_missions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'aborted' THEN 1 ELSE 0 END) as aborted,
                    AVG(cost_usd) as avg_cost,
                    SUM(cost_usd) as total_cost,
                    AVG(duration_seconds) as avg_duration,
                    AVG(iterations) as avg_iterations
                FROM mission_metrics
                WHERE timestamp >= ?
            """
            params = [cutoff]

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            cursor.execute(query, params)
            row = cursor.fetchone()

            total = row["total_missions"] or 0
            successful = row["successful"] or 0

            return {
                "total_missions": total,
                "successful_missions": successful,
                "failed_missions": row["failed"] or 0,
                "aborted_missions": row["aborted"] or 0,
                "success_rate": successful / total if total > 0 else 0,
                "avg_cost_usd": row["avg_cost"] or 0,
                "total_cost_usd": row["total_cost"] or 0,
                "avg_duration_seconds": row["avg_duration"] or 0,
                "avg_iterations": row["avg_iterations"] or 0,
                "period_hours": hours,
                "domain": domain,
            }

    def get_mission_trend(
        self,
        hours: int = 24,
        bucket_hours: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get mission metrics trend over time.

        Args:
            hours: Number of hours to look back
            bucket_hours: Bucket size for aggregation

        Returns:
            List of time-bucketed metrics
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # SQLite doesn't have great time bucketing, so we'll do it in Python
            cursor.execute("""
                SELECT
                    timestamp,
                    status,
                    cost_usd,
                    duration_seconds
                FROM mission_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff,))

            rows = cursor.fetchall()

            # Bucket by hour
            buckets = {}
            for row in rows:
                ts = datetime.fromisoformat(row["timestamp"])
                bucket_key = ts.replace(minute=0, second=0, microsecond=0).isoformat()

                if bucket_key not in buckets:
                    buckets[bucket_key] = {
                        "timestamp": bucket_key,
                        "total": 0,
                        "successful": 0,
                        "failed": 0,
                        "total_cost": 0,
                        "avg_duration": 0,
                    }

                buckets[bucket_key]["total"] += 1
                if row["status"] == "success":
                    buckets[bucket_key]["successful"] += 1
                elif row["status"] == "failed":
                    buckets[bucket_key]["failed"] += 1
                buckets[bucket_key]["total_cost"] += row["cost_usd"]
                buckets[bucket_key]["avg_duration"] += row["duration_seconds"]

            # Calculate averages
            result = []
            for bucket in sorted(buckets.values(), key=lambda x: x["timestamp"]):
                if bucket["total"] > 0:
                    bucket["success_rate"] = bucket["successful"] / bucket["total"]
                    bucket["avg_duration"] = bucket["avg_duration"] / bucket["total"]
                result.append(bucket)

            return result

    # ──────────────────────────────────────────────────────────────────
    # Tool Metrics
    # ──────────────────────────────────────────────────────────────────

    def record_tool_execution(
        self,
        tool_name: str,
        success: bool,
        duration_seconds: float,
        cost_usd: float = 0,
    ) -> None:
        """
        Record tool execution.

        Args:
            tool_name: Name of tool
            success: Whether execution succeeded
            duration_seconds: Execution duration
            cost_usd: Cost of execution
        """
        with sqlite3.connect(self.db_path) as conn:
            # Try to update existing row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    execution_count,
                    success_count,
                    failure_count,
                    avg_duration_seconds,
                    total_cost_usd
                FROM tool_metrics
                WHERE tool_name = ?
            """, (tool_name,))

            row = cursor.fetchone()
            now = self._now()

            if row:
                # Update existing
                exec_count = row[0] + 1
                succ_count = row[1] + (1 if success else 0)
                fail_count = row[2] + (0 if success else 1)
                old_avg_duration = row[3]
                old_total_cost = row[4]

                # Calculate new average duration
                new_avg_duration = (old_avg_duration * row[0] + duration_seconds) / exec_count
                new_total_cost = old_total_cost + cost_usd

                cursor.execute("""
                    UPDATE tool_metrics
                    SET
                        execution_count = ?,
                        success_count = ?,
                        failure_count = ?,
                        avg_duration_seconds = ?,
                        total_cost_usd = ?,
                        last_used = ?,
                        updated_at = ?
                    WHERE tool_name = ?
                """, (
                    exec_count,
                    succ_count,
                    fail_count,
                    new_avg_duration,
                    new_total_cost,
                    now,
                    now,
                    tool_name,
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO tool_metrics (
                        tool_name,
                        execution_count,
                        success_count,
                        failure_count,
                        avg_duration_seconds,
                        total_cost_usd,
                        last_used,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tool_name,
                    1,
                    1 if success else 0,
                    0 if success else 1,
                    duration_seconds,
                    cost_usd,
                    now,
                    now,
                ))

            conn.commit()

    def get_tool_stats(
        self,
        limit: int = 20,
        order_by: str = "execution_count",
    ) -> List[Dict[str, Any]]:
        """
        Get tool usage statistics.

        Args:
            limit: Maximum number of tools to return
            order_by: Sort field (execution_count, total_cost_usd, avg_duration_seconds)

        Returns:
            List of tool statistics
        """
        valid_order_by = {
            "execution_count",
            "total_cost_usd",
            "avg_duration_seconds",
            "success_count",
            "failure_count",
        }
        if order_by not in valid_order_by:
            order_by = "execution_count"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT
                    tool_name,
                    execution_count,
                    success_count,
                    failure_count,
                    avg_duration_seconds,
                    total_cost_usd,
                    last_used
                FROM tool_metrics
                ORDER BY {order_by} DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [
                {
                    "tool_name": row["tool_name"],
                    "execution_count": row["execution_count"],
                    "success_count": row["success_count"],
                    "failure_count": row["failure_count"],
                    "success_rate": row["success_count"] / row["execution_count"] if row["execution_count"] > 0 else 0,
                    "avg_duration_seconds": row["avg_duration_seconds"],
                    "total_cost_usd": row["total_cost_usd"],
                    "last_used": row["last_used"],
                }
                for row in rows
            ]

    # ──────────────────────────────────────────────────────────────────
    # Error Metrics
    # ──────────────────────────────────────────────────────────────────

    def record_error(
        self,
        error_type: str,
        error_message: str,
        mission_id: Optional[str] = None,
    ) -> None:
        """
        Record error occurrence.

        Args:
            error_type: Type of error (e.g., "ValueError", "APIError")
            error_message: Error message
            mission_id: Optional mission ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = self._now()

            # Try to update existing
            cursor.execute("""
                SELECT count, mission_ids
                FROM error_metrics
                WHERE error_type = ? AND error_message = ?
            """, (error_type, error_message))

            row = cursor.fetchone()

            if row:
                # Update existing
                new_count = row[0] + 1
                mission_ids = json.loads(row[1]) if row[1] else []
                if mission_id and mission_id not in mission_ids:
                    mission_ids.append(mission_id)
                    # Keep only last 10 mission IDs
                    mission_ids = mission_ids[-10:]

                cursor.execute("""
                    UPDATE error_metrics
                    SET
                        count = ?,
                        last_seen = ?,
                        mission_ids = ?
                    WHERE error_type = ? AND error_message = ?
                """, (
                    new_count,
                    now,
                    json.dumps(mission_ids),
                    error_type,
                    error_message,
                ))
            else:
                # Insert new
                mission_ids = [mission_id] if mission_id else []
                cursor.execute("""
                    INSERT INTO error_metrics (
                        error_type,
                        error_message,
                        count,
                        first_seen,
                        last_seen,
                        mission_ids
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    error_type,
                    error_message,
                    1,
                    now,
                    now,
                    json.dumps(mission_ids),
                ))

            conn.commit()

    def get_error_stats(
        self,
        hours: int = 24,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Get error statistics.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of errors to return

        Returns:
            List of error statistics
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    error_type,
                    error_message,
                    count,
                    first_seen,
                    last_seen,
                    mission_ids
                FROM error_metrics
                WHERE last_seen >= ?
                ORDER BY count DESC
                LIMIT ?
            """, (cutoff, limit))

            rows = cursor.fetchall()
            return [
                {
                    "error_type": row["error_type"],
                    "error_message": row["error_message"],
                    "count": row["count"],
                    "first_seen": row["first_seen"],
                    "last_seen": row["last_seen"],
                    "mission_ids": json.loads(row["mission_ids"]) if row["mission_ids"] else [],
                }
                for row in rows
            ]

    def get_error_rate(self, hours: int = 24) -> Dict[str, Any]:
        """
        Calculate error rate.

        Args:
            hours: Number of hours to look back

        Returns:
            Dict with error rate statistics
        """
        mission_stats = self.get_mission_stats(hours=hours)
        error_stats = self.get_error_stats(hours=hours)

        total_missions = mission_stats["total_missions"]
        failed_missions = mission_stats["failed_missions"]
        total_errors = sum(e["count"] for e in error_stats)

        return {
            "total_missions": total_missions,
            "failed_missions": failed_missions,
            "failure_rate": failed_missions / total_missions if total_missions > 0 else 0,
            "total_errors": total_errors,
            "unique_errors": len(error_stats),
            "period_hours": hours,
        }

    # ──────────────────────────────────────────────────────────────────
    # Health Metrics
    # ──────────────────────────────────────────────────────────────────

    def record_health_check(
        self,
        cpu_percent: Optional[float] = None,
        memory_percent: Optional[float] = None,
        disk_percent: Optional[float] = None,
        active_missions: int = 0,
        queue_length: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record health check metrics.

        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            disk_percent: Disk usage percentage
            active_missions: Number of active missions
            queue_length: Number of queued missions
            metadata: Additional metadata

        Returns:
            Health status (healthy, degraded, unhealthy)
        """
        # Determine health status
        status = "healthy"
        if cpu_percent and cpu_percent > 80:
            status = "degraded"
        if memory_percent and memory_percent > 85:
            status = "degraded"
        if disk_percent and disk_percent > 90:
            status = "unhealthy"
        if queue_length > 100:
            status = "degraded"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO health_metrics (
                    timestamp,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    active_missions,
                    queue_length,
                    status,
                    metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self._now(),
                cpu_percent,
                memory_percent,
                disk_percent,
                active_missions,
                queue_length,
                status,
                json.dumps(metadata) if metadata else None,
            ))
            conn.commit()

        return status

    def get_latest_health(self) -> Optional[Dict[str, Any]]:
        """
        Get latest health check.

        Returns:
            Latest health metrics or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    timestamp,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    active_missions,
                    queue_length,
                    status
                FROM health_metrics
                ORDER BY timestamp DESC
                LIMIT 1
            """)

            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_health_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health metrics trend.

        Args:
            hours: Number of hours to look back

        Returns:
            List of health metrics
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    timestamp,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    active_missions,
                    queue_length,
                    status
                FROM health_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff,))

            return [dict(row) for row in cursor.fetchall()]


# ══════════════════════════════════════════════════════════════════════
# Singleton Instance
# ══════════════════════════════════════════════════════════════════════


_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get singleton metrics collector instance.

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def record_mission(mission_id: str, status: str, cost_usd: float, duration_seconds: float, iterations: int, **kwargs) -> None:
    """Record mission metrics."""
    metrics = get_metrics_collector()
    metrics.record_mission(mission_id, status, cost_usd, duration_seconds, iterations, **kwargs)


def record_tool_execution(tool_name: str, success: bool, duration_seconds: float, cost_usd: float = 0) -> None:
    """Record tool execution metrics."""
    metrics = get_metrics_collector()
    metrics.record_tool_execution(tool_name, success, duration_seconds, cost_usd)


def record_error(error_type: str, error_message: str, mission_id: Optional[str] = None) -> None:
    """Record error occurrence."""
    metrics = get_metrics_collector()
    metrics.record_error(error_type, error_message, mission_id)


def record_health_check(**kwargs) -> str:
    """Record health check metrics."""
    metrics = get_metrics_collector()
    return metrics.record_health_check(**kwargs)


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("Monitoring System Demo")
    print("=" * 60)

    metrics = get_metrics_collector()

    # Record some sample missions
    print("\nRecording sample missions...")
    metrics.record_mission("mission_1", "success", 1.25, 120, 3, domain="coding")
    metrics.record_mission("mission_2", "success", 0.85, 90, 2, domain="finance")
    metrics.record_mission("mission_3", "failed", 2.10, 180, 5, domain="coding", error_type="ValueError", error_message="Invalid input")

    # Get statistics
    print("\nMission Statistics (24h):")
    stats = metrics.get_mission_stats(hours=24)
    print(f"  Total missions: {stats['total_missions']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Avg cost: ${stats['avg_cost_usd']:.2f}")
    print(f"  Avg duration: {stats['avg_duration_seconds']:.1f}s")

    print("\n✓ Monitoring system initialized")
