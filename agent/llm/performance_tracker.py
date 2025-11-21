"""
PHASE 9.3: Model Performance Tracking

Tracks performance metrics for all LLM calls:
- Latency per model
- Cost per model
- Success/failure rates
- Quality scores (optional user feedback)
- Performance trends over time

Features:
- Real-time metrics collection
- Persistent storage to disk
- Analytics and reporting
- Performance-based routing optimization
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PerformanceMetric:
    """Single performance metric record."""
    timestamp: float
    model: str
    latency_ms: float
    cost_usd: float
    success: bool
    quality_score: Optional[float] = None  # 0.0-1.0, from user feedback
    prompt_tokens: int = 0
    completion_tokens: int = 0
    task_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PerformanceMetric:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ModelStats:
    """Aggregated statistics for a model."""
    model: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_latency_ms: float
    total_cost_usd: float
    total_tokens: int

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0-1.0)."""
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency in milliseconds."""
        if self.successful_calls == 0:
            return 0.0
        return self.total_latency_ms / self.successful_calls

    @property
    def avg_cost_per_call(self) -> float:
        """Calculate average cost per call."""
        if self.total_calls == 0:
            return 0.0
        return self.total_cost_usd / self.total_calls

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model": self.model,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": self.success_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_cost_per_call": self.avg_cost_per_call,
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
        }


class PerformanceTracker:
    """
    Performance tracker for LLM calls.

    Tracks metrics across all models and provides analytics.
    Persists data to disk for historical analysis.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize performance tracker.

        Args:
            storage_path: Path to store metrics (default: ./llm_performance.jsonl)
        """
        if storage_path is None:
            storage_path = Path("llm_performance.jsonl")

        self.storage_path = storage_path
        self.metrics: List[PerformanceMetric] = []

        # In-memory aggregated stats per model
        self._stats: Dict[str, ModelStats] = {}

        # Load existing metrics if available
        self._load_metrics()

    def _load_metrics(self):
        """Load metrics from disk."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        metric = PerformanceMetric.from_dict(data)
                        self.metrics.append(metric)
                        self._update_stats(metric)

            print(f"[PerformanceTracker] Loaded {len(self.metrics)} historical metrics")

        except Exception as e:
            print(f"[PerformanceTracker] Error loading metrics: {e}")

    def _save_metric(self, metric: PerformanceMetric):
        """Append metric to disk storage."""
        try:
            with open(self.storage_path, "a") as f:
                f.write(json.dumps(metric.to_dict()) + "\n")
        except Exception as e:
            print(f"[PerformanceTracker] Error saving metric: {e}")

    def _update_stats(self, metric: PerformanceMetric):
        """Update aggregated statistics."""
        model = metric.model

        if model not in self._stats:
            self._stats[model] = ModelStats(
                model=model,
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                total_latency_ms=0.0,
                total_cost_usd=0.0,
                total_tokens=0,
            )

        stats = self._stats[model]
        stats.total_calls += 1

        if metric.success:
            stats.successful_calls += 1
            stats.total_latency_ms += metric.latency_ms
        else:
            stats.failed_calls += 1

        stats.total_cost_usd += metric.cost_usd
        stats.total_tokens += metric.prompt_tokens + metric.completion_tokens

    async def record_call(
        self,
        model: str,
        latency_ms: float,
        cost_usd: float,
        success: bool,
        quality_score: Optional[float] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        task_type: Optional[str] = None,
    ):
        """
        Record a single LLM call.

        Args:
            model: Model name
            latency_ms: Latency in milliseconds
            cost_usd: Cost in USD
            success: Whether call succeeded
            quality_score: Optional quality score (0.0-1.0)
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            task_type: Optional task type
        """
        metric = PerformanceMetric(
            timestamp=time.time(),
            model=model,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            success=success,
            quality_score=quality_score,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            task_type=task_type,
        )

        self.metrics.append(metric)
        self._update_stats(metric)
        self._save_metric(metric)

    def get_model_stats(self, model: str) -> Optional[ModelStats]:
        """
        Get statistics for a specific model.

        Args:
            model: Model name

        Returns:
            ModelStats or None if no data
        """
        return self._stats.get(model)

    def get_all_stats(self) -> Dict[str, ModelStats]:
        """Get statistics for all models."""
        return self._stats.copy()

    def get_best_model_for_latency(self) -> Optional[str]:
        """Get model with best (lowest) average latency."""
        if not self._stats:
            return None

        best_model = None
        best_latency = float("inf")

        for model, stats in self._stats.items():
            if stats.successful_calls > 0:
                avg_latency = stats.avg_latency_ms
                if avg_latency < best_latency:
                    best_latency = avg_latency
                    best_model = model

        return best_model

    def get_best_model_for_cost(self) -> Optional[str]:
        """Get model with best (lowest) average cost."""
        if not self._stats:
            return None

        best_model = None
        best_cost = float("inf")

        for model, stats in self._stats.items():
            if stats.total_calls > 0:
                avg_cost = stats.avg_cost_per_call
                if avg_cost < best_cost:
                    best_cost = avg_cost
                    best_model = model

        return best_model

    def get_best_model_for_reliability(self) -> Optional[str]:
        """Get model with highest success rate."""
        if not self._stats:
            return None

        best_model = None
        best_rate = 0.0

        for model, stats in self._stats.items():
            if stats.total_calls >= 5:  # Require minimum 5 calls
                if stats.success_rate > best_rate:
                    best_rate = stats.success_rate
                    best_model = model

        return best_model

    def get_metrics_by_time_range(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[PerformanceMetric]:
        """
        Get metrics within a time range.

        Args:
            start_time: Start timestamp (default: 0)
            end_time: End timestamp (default: now)

        Returns:
            List of metrics in range
        """
        start = start_time or 0
        end = end_time or time.time()

        return [
            m for m in self.metrics
            if start <= m.timestamp <= end
        ]

    def get_recent_metrics(self, count: int = 100) -> List[PerformanceMetric]:
        """
        Get most recent metrics.

        Args:
            count: Number of metrics to return

        Returns:
            List of recent metrics
        """
        return self.metrics[-count:] if self.metrics else []

    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.

        Returns:
            Dict with overall statistics and per-model breakdown
        """
        if not self.metrics:
            return {
                "total_calls": 0,
                "models": {},
                "overall": {},
            }

        # Overall statistics
        total_calls = len(self.metrics)
        successful_calls = sum(1 for m in self.metrics if m.success)
        total_cost = sum(m.cost_usd for m in self.metrics)
        total_tokens = sum(m.prompt_tokens + m.completion_tokens for m in self.metrics)

        # Quality scores (if any)
        quality_scores = [m.quality_score for m in self.metrics if m.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        # Per-model breakdown
        model_breakdown = {
            model: stats.to_dict()
            for model, stats in self._stats.items()
        }

        # Best models
        best_latency = self.get_best_model_for_latency()
        best_cost = self.get_best_model_for_cost()
        best_reliability = self.get_best_model_for_reliability()

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "total_cost_usd": total_cost,
            "total_tokens": total_tokens,
            "avg_quality_score": avg_quality,
            "models": model_breakdown,
            "best_for_latency": best_latency,
            "best_for_cost": best_cost,
            "best_for_reliability": best_reliability,
        }

    def export_to_csv(self, output_path: Path):
        """
        Export metrics to CSV format.

        Args:
            output_path: Output file path
        """
        import csv

        if not self.metrics:
            print("[PerformanceTracker] No metrics to export")
            return

        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "timestamp", "datetime", "model", "latency_ms", "cost_usd",
                "success", "quality_score", "prompt_tokens", "completion_tokens",
                "total_tokens", "task_type"
            ])

            # Data rows
            for metric in self.metrics:
                dt = datetime.fromtimestamp(metric.timestamp).isoformat()
                total_tokens = metric.prompt_tokens + metric.completion_tokens

                writer.writerow([
                    metric.timestamp,
                    dt,
                    metric.model,
                    metric.latency_ms,
                    metric.cost_usd,
                    metric.success,
                    metric.quality_score or "",
                    metric.prompt_tokens,
                    metric.completion_tokens,
                    total_tokens,
                    metric.task_type or "",
                ])

        print(f"[PerformanceTracker] Exported {len(self.metrics)} metrics to {output_path}")
