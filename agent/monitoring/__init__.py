"""
PHASE 11.2: Monitoring & Observability

Production monitoring infrastructure with metrics, logging, and alerting.

Components:
- metrics: Prometheus-style metrics collection
- logging_config: Structured logging configuration
- alerts: Alert rules and notification system

Features:
- Counter, Gauge, Histogram metrics
- Prometheus export format
- JSON structured logging
- Alert rules with thresholds
- Real-time monitoring
"""

from .metrics import (
    MetricsCollector,
    Counter,
    Gauge,
    Histogram,
    get_global_collector,
)
from .logging_config import (
    setup_logging,
    get_structured_logger,
    LogLevel,
)
from .alerts import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertRule,
)

__all__ = [
    "MetricsCollector",
    "Counter",
    "Gauge",
    "Histogram",
    "get_global_collector",
    "setup_logging",
    "get_structured_logger",
    "LogLevel",
    "AlertManager",
    "Alert",
    "AlertSeverity",
    "AlertRule",
]
