"""
PHASE 11.2: Metrics Collection

Prometheus-style metrics collection for monitoring system health and performance.

Features:
- Counter: Monotonically increasing values
- Gauge: Values that can go up or down
- Histogram: Distribution of values with buckets
- Summary statistics
- Label support for dimensional metrics
- Prometheus export format
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Sample:
    """A metric sample with labels."""
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class Counter:
    """
    Counter metric - monotonically increasing value.

    Used for: request counts, error counts, task completions, etc.
    """

    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        """
        Initialize counter.

        Args:
            name: Metric name
            description: Metric description
            labels: Label names for dimensional metrics
        """
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[Tuple, float] = defaultdict(float)

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Increment counter.

        Args:
            amount: Amount to increment (default: 1)
            labels: Label values
        """
        label_key = self._make_label_key(labels)
        self._values[label_key] += amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value."""
        label_key = self._make_label_key(labels)
        return self._values[label_key]

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> Tuple:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def samples(self) -> List[Sample]:
        """Get all samples."""
        return [
            Sample(value=value, labels=dict(label_key))
            for label_key, value in self._values.items()
        ]


class Gauge:
    """
    Gauge metric - value that can go up or down.

    Used for: current memory usage, active connections, queue size, etc.
    """

    def __init__(self, name: str, description: str = "", labels: Optional[List[str]] = None):
        """Initialize gauge."""
        self.name = name
        self.description = description
        self.label_names = labels or []
        self._values: Dict[Tuple, float] = defaultdict(float)

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Set gauge value."""
        label_key = self._make_label_key(labels)
        self._values[label_key] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment gauge."""
        label_key = self._make_label_key(labels)
        self._values[label_key] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Decrement gauge."""
        label_key = self._make_label_key(labels)
        self._values[label_key] -= amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value."""
        label_key = self._make_label_key(labels)
        return self._values[label_key]

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> Tuple:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def samples(self) -> List[Sample]:
        """Get all samples."""
        return [
            Sample(value=value, labels=dict(label_key))
            for label_key, value in self._values.items()
        ]


class Histogram:
    """
    Histogram metric - distribution of values.

    Used for: request durations, response sizes, etc.
    Provides: count, sum, and buckets.
    """

    DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]

    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: Optional[List[float]] = None,
        labels: Optional[List[str]] = None,
    ):
        """
        Initialize histogram.

        Args:
            name: Metric name
            description: Metric description
            buckets: Bucket boundaries (default: [0.005, 0.01, ..., 10.0])
            labels: Label names
        """
        self.name = name
        self.description = description
        self.label_names = labels or []
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)

        # Storage: {label_key: {"count": N, "sum": S, "buckets": {le: count}}}
        self._data: Dict[Tuple, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "sum": 0.0,
                "buckets": defaultdict(int),
            }
        )

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe a value.

        Args:
            value: Value to observe
            labels: Label values
        """
        label_key = self._make_label_key(labels)
        data = self._data[label_key]

        # Update count and sum
        data["count"] += 1
        data["sum"] += value

        # Update buckets
        for bucket in self.buckets:
            if value <= bucket:
                data["buckets"][bucket] += 1

        # Add infinity bucket
        data["buckets"][float("inf")] += 1

    def get_stats(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get histogram statistics."""
        label_key = self._make_label_key(labels)
        data = self._data[label_key]

        count = data["count"]
        total = data["sum"]

        return {
            "count": count,
            "sum": total,
            "avg": total / count if count > 0 else 0,
            "buckets": dict(data["buckets"]),
        }

    def _make_label_key(self, labels: Optional[Dict[str, str]]) -> Tuple:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def samples(self) -> List[Sample]:
        """Get all samples."""
        samples = []

        for label_key, data in self._data.items():
            labels_dict = dict(label_key)

            # Add bucket samples
            for bucket, count in data["buckets"].items():
                bucket_labels = labels_dict.copy()
                bucket_labels["le"] = str(bucket)
                samples.append(Sample(value=count, labels=bucket_labels))

            # Add sum and count
            samples.append(Sample(value=data["sum"], labels=labels_dict))
            samples.append(Sample(value=data["count"], labels=labels_dict))

        return samples


class MetricsCollector:
    """
    Central metrics collector.

    Collects and exports metrics for monitoring.
    """

    def __init__(self):
        """Initialize metrics collector."""
        # Standard metrics
        self.tasks_completed = Counter(
            "tasks_completed_total",
            "Total number of tasks completed",
            labels=["status"],
        )

        self.execution_time = Histogram(
            "task_execution_seconds",
            "Task execution time in seconds",
            labels=["task_type"],
        )

        self.errors = Counter(
            "errors_total",
            "Total number of errors",
            labels=["category", "operation"],
        )

        self.llm_calls = Counter(
            "llm_calls_total",
            "Total number of LLM API calls",
            labels=["model", "status"],
        )

        self.llm_cost = Gauge(
            "llm_cost_usd",
            "Current LLM cost in USD",
            labels=["model"],
        )

        self.active_sessions = Gauge(
            "active_sessions",
            "Number of active user sessions",
        )

        self.memory_usage = Gauge(
            "memory_usage_bytes",
            "Memory usage in bytes",
            labels=["type"],
        )

        # Registry of all metrics
        self._metrics: Dict[str, Any] = {
            "tasks_completed": self.tasks_completed,
            "execution_time": self.execution_time,
            "errors": self.errors,
            "llm_calls": self.llm_calls,
            "llm_cost": self.llm_cost,
            "active_sessions": self.active_sessions,
            "memory_usage": self.memory_usage,
        }

    def record_task_completion(
        self,
        duration: float,
        success: bool,
        task_type: str = "general",
    ):
        """
        Record task completion metrics.

        Args:
            duration: Task duration in seconds
            success: Whether task succeeded
            task_type: Type of task
        """
        status = "success" if success else "failure"

        self.tasks_completed.inc(labels={"status": status})
        self.execution_time.observe(duration, labels={"task_type": task_type})

        if not success:
            self.errors.inc(labels={"category": "task_failure", "operation": task_type})

    def record_llm_call(
        self,
        model: str,
        success: bool,
        cost_usd: float = 0.0,
    ):
        """
        Record LLM API call.

        Args:
            model: Model name
            success: Whether call succeeded
            cost_usd: Cost in USD
        """
        status = "success" if success else "failure"

        self.llm_calls.inc(labels={"model": model, "status": status})

        if cost_usd > 0:
            # Add to cumulative cost
            current = self.llm_cost.get(labels={"model": model})
            self.llm_cost.set(current + cost_usd, labels={"model": model})

    def record_error(self, category: str, operation: str):
        """Record error occurrence."""
        self.errors.inc(labels={"category": category, "operation": operation})

    def set_active_sessions(self, count: int):
        """Set number of active sessions."""
        self.active_sessions.set(count)

    def set_memory_usage(self, bytes_used: int, memory_type: str = "total"):
        """Set memory usage."""
        self.memory_usage.set(bytes_used, labels={"type": memory_type})

    def register_metric(self, name: str, metric: Any):
        """Register custom metric."""
        self._metrics[name] = metric

    def get_metric(self, name: str) -> Optional[Any]:
        """Get metric by name."""
        return self._metrics.get(name)

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        for name, metric in self._metrics.items():
            # Add HELP and TYPE
            if hasattr(metric, "description") and metric.description:
                lines.append(f"# HELP {metric.name} {metric.description}")

            metric_type = self._get_metric_type(metric)
            lines.append(f"# TYPE {metric.name} {metric_type}")

            # Add samples
            if isinstance(metric, Histogram):
                lines.extend(self._format_histogram_samples(metric))
            else:
                lines.extend(self._format_samples(metric))

        return "\n".join(lines) + "\n"

    def _get_metric_type(self, metric: Any) -> str:
        """Get Prometheus metric type."""
        if isinstance(metric, Counter):
            return "counter"
        elif isinstance(metric, Gauge):
            return "gauge"
        elif isinstance(metric, Histogram):
            return "histogram"
        else:
            return "untyped"

    def _format_samples(self, metric: Any) -> List[str]:
        """Format metric samples for Prometheus."""
        lines = []

        for sample in metric.samples():
            if sample.labels:
                labels_str = ",".join(f'{k}="{v}"' for k, v in sample.labels.items())
                line = f'{metric.name}{{{labels_str}}} {sample.value}'
            else:
                line = f'{metric.name} {sample.value}'

            lines.append(line)

        return lines

    def _format_histogram_samples(self, histogram: Histogram) -> List[str]:
        """Format histogram samples for Prometheus."""
        lines = []

        for label_key, data in histogram._data.items():
            labels_dict = dict(label_key)

            # Bucket samples
            for bucket, count in sorted(data["buckets"].items()):
                bucket_labels = labels_dict.copy()
                bucket_labels["le"] = str(bucket)
                labels_str = ",".join(f'{k}="{v}"' for k, v in bucket_labels.items())
                lines.append(f'{histogram.name}_bucket{{{labels_str}}} {count}')

            # Sum
            if labels_dict:
                labels_str = ",".join(f'{k}="{v}"' for k, v in labels_dict.items())
                lines.append(f'{histogram.name}_sum{{{labels_str}}} {data["sum"]}')
                lines.append(f'{histogram.name}_count{{{labels_str}}} {data["count"]}')
            else:
                lines.append(f'{histogram.name}_sum {data["sum"]}')
                lines.append(f'{histogram.name}_count {data["count"]}')

        return lines

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            "tasks_completed": {
                "success": self.tasks_completed.get(labels={"status": "success"}),
                "failure": self.tasks_completed.get(labels={"status": "failure"}),
            },
            "errors_total": sum(
                sample.value for sample in self.errors.samples()
            ),
            "llm_calls_total": sum(
                sample.value for sample in self.llm_calls.samples()
            ),
            "active_sessions": self.active_sessions.get(),
        }


# Global metrics collector
_global_collector: Optional[MetricsCollector] = None


def get_global_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector
