"""
PHASE 11.2: Monitoring Tests

Tests for metrics, logging, and alerting.
"""

import json
import logging
import tempfile
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_global_collector,
)
from monitoring.logging_config import (
    setup_logging,
    get_structured_logger,
    LogLevel,
    JSONFormatter,
)
from monitoring.alerts import (
    AlertManager,
    AlertRule,
    Alert,
    AlertSeverity,
    AlertState,
    create_high_error_rate_rule,
)


# ============================================================================
# Metrics Tests
# ============================================================================

def test_counter_increment():
    """Test counter increment."""
    counter = Counter("test_counter", "Test counter")

    counter.inc()
    assert counter.get() == 1.0

    counter.inc(5)
    assert counter.get() == 6.0


def test_counter_with_labels():
    """Test counter with labels."""
    counter = Counter("http_requests", "HTTP requests", labels=["method", "status"])

    counter.inc(labels={"method": "GET", "status": "200"})
    counter.inc(labels={"method": "GET", "status": "200"})
    counter.inc(labels={"method": "POST", "status": "201"})

    assert counter.get(labels={"method": "GET", "status": "200"}) == 2.0
    assert counter.get(labels={"method": "POST", "status": "201"}) == 1.0


def test_gauge_set():
    """Test gauge set."""
    gauge = Gauge("memory_usage", "Memory usage")

    gauge.set(100.0)
    assert gauge.get() == 100.0

    gauge.set(200.0)
    assert gauge.get() == 200.0


def test_gauge_inc_dec():
    """Test gauge increment and decrement."""
    gauge = Gauge("queue_size", "Queue size")

    gauge.inc(5)
    assert gauge.get() == 5.0

    gauge.dec(2)
    assert gauge.get() == 3.0


def test_histogram_observe():
    """Test histogram observations."""
    histogram = Histogram("response_time", "Response time")

    histogram.observe(0.5)
    histogram.observe(1.0)
    histogram.observe(2.5)

    stats = histogram.get_stats()

    assert stats["count"] == 3
    assert stats["sum"] == 4.0
    assert stats["avg"] == pytest.approx(1.333, abs=0.01)


def test_histogram_buckets():
    """Test histogram buckets."""
    histogram = Histogram(
        "request_duration",
        "Request duration",
        buckets=[0.1, 0.5, 1.0, 5.0],
    )

    # Observations
    histogram.observe(0.05)  # < 0.1
    histogram.observe(0.3)   # < 0.5
    histogram.observe(0.8)   # < 1.0
    histogram.observe(3.0)   # < 5.0
    histogram.observe(10.0)  # > 5.0

    stats = histogram.get_stats()
    buckets = stats["buckets"]

    assert buckets[0.1] == 1  # 1 observation <= 0.1
    assert buckets[0.5] == 2  # 2 observations <= 0.5
    assert buckets[1.0] == 3  # 3 observations <= 1.0
    assert buckets[5.0] == 4  # 4 observations <= 5.0
    assert buckets[float("inf")] == 5  # All observations


def test_metrics_collector_task_completion():
    """Test recording task completion."""
    collector = MetricsCollector()

    collector.record_task_completion(duration=1.5, success=True, task_type="test")
    collector.record_task_completion(duration=2.0, success=False, task_type="test")

    assert collector.tasks_completed.get(labels={"status": "success"}) == 1.0
    assert collector.tasks_completed.get(labels={"status": "failure"}) == 1.0


def test_metrics_collector_llm_call():
    """Test recording LLM calls."""
    collector = MetricsCollector()

    collector.record_llm_call("gpt-4", success=True, cost_usd=0.05)
    collector.record_llm_call("gpt-4", success=True, cost_usd=0.03)

    assert collector.llm_calls.get(labels={"model": "gpt-4", "status": "success"}) == 2.0
    assert collector.llm_cost.get(labels={"model": "gpt-4"}) == 0.08


def test_metrics_collector_error():
    """Test recording errors."""
    collector = MetricsCollector()

    collector.record_error("network", "api_call")
    collector.record_error("network", "api_call")
    collector.record_error("timeout", "database")

    assert collector.errors.get(labels={"category": "network", "operation": "api_call"}) == 2.0
    assert collector.errors.get(labels={"category": "timeout", "operation": "database"}) == 1.0


def test_prometheus_export():
    """Test Prometheus format export."""
    collector = MetricsCollector()

    # Add some metrics
    collector.tasks_completed.inc(labels={"status": "success"})
    collector.execution_time.observe(1.5, labels={"task_type": "test"})

    # Export
    output = collector.export_prometheus()

    # Check format
    assert "# HELP" in output
    assert "# TYPE" in output
    assert "tasks_completed_total" in output
    assert "task_execution_seconds" in output


def test_global_collector_singleton():
    """Test global collector is singleton."""
    collector1 = get_global_collector()
    collector2 = get_global_collector()

    assert collector1 is collector2


# ============================================================================
# Logging Tests
# ============================================================================

def test_json_formatter():
    """Test JSON log formatting."""
    formatter = JSONFormatter()

    # Create log record
    logger = logging.getLogger("test")
    record = logger.makeRecord(
        "test", logging.INFO, "test.py", 10,
        "Test message", (), None
    )

    # Format
    output = formatter.format(record)

    # Parse JSON
    data = json.loads(output)

    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["logger_name"] == "test"


def test_structured_logger():
    """Test structured logger."""
    logger = get_structured_logger("test_logger")

    # Should not raise
    logger.info("Test info")
    logger.warning("Test warning")
    logger.error("Test error")


def test_structured_logger_with_context():
    """Test structured logger with context."""
    logger = get_structured_logger("test", context={"request_id": "123"})

    # Create logger with additional context
    request_logger = logger.with_context(user_id="user456")

    # Both contexts should be present
    assert request_logger.default_context["request_id"] == "123"
    assert request_logger.default_context["user_id"] == "user456"


def test_setup_logging():
    """Test logging setup."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"

        setup_logging(
            level=LogLevel.INFO,
            output_file=log_file,
            json_format=True,
        )

        # Log something
        logger = logging.getLogger("test")
        logger.info("Test message")

        # Check file exists
        assert log_file.exists()


# ============================================================================
# Alerts Tests
# ============================================================================

def test_alert_rule_evaluation():
    """Test alert rule evaluation."""
    triggered = [False]

    def condition():
        return triggered[0]

    rule = AlertRule(
        name="test_rule",
        description="Test",
        severity=AlertSeverity.WARNING,
        condition=condition,
        message_template="Test alert",
    )

    # Initially false
    assert rule.evaluate() is False

    # Trigger
    triggered[0] = True
    assert rule.evaluate() is True

    # Should not fire again (cooldown)
    assert rule.evaluate() is False


def test_alert_rule_for_duration():
    """Test alert rule for_duration."""
    triggered = [False]

    def condition():
        return triggered[0]

    rule = AlertRule(
        name="test_rule",
        description="Test",
        severity=AlertSeverity.WARNING,
        condition=condition,
        message_template="Test alert",
        for_duration=1.0,  # 1 second
    )

    # Trigger but too early
    triggered[0] = True
    assert rule.evaluate() is False

    # Wait for duration
    time.sleep(1.1)
    assert rule.evaluate() is True


def test_alert_manager_register_rule():
    """Test registering alert rules."""
    manager = AlertManager()

    rule = AlertRule(
        name="test_rule",
        description="Test",
        severity=AlertSeverity.INFO,
        condition=lambda: False,
        message_template="Test",
    )

    manager.register_rule(rule)

    assert "test_rule" in manager.rules


def test_alert_manager_evaluate_firing():
    """Test alert manager evaluation - firing."""
    manager = AlertManager()

    triggered = [True]

    rule = AlertRule(
        name="test_alert",
        description="Test",
        severity=AlertSeverity.WARNING,
        condition=lambda: triggered[0],
        message_template="Test alert firing",
    )

    manager.register_rule(rule)
    manager.evaluate_rules()

    # Should have one active alert
    assert len(manager.active_alerts) == 1
    assert manager.total_fired == 1


def test_alert_manager_evaluate_resolved():
    """Test alert manager evaluation - resolved."""
    manager = AlertManager()

    triggered = [True]

    rule = AlertRule(
        name="test_alert",
        description="Test",
        severity=AlertSeverity.WARNING,
        condition=lambda: triggered[0],
        message_template="Test alert",
    )

    manager.register_rule(rule)

    # Fire alert
    manager.evaluate_rules()
    assert len(manager.active_alerts) == 1

    # Resolve
    triggered[0] = False
    manager.evaluate_rules()

    # Should be resolved
    assert len(manager.active_alerts) == 0
    assert len(manager.alert_history) == 1
    assert manager.total_resolved == 1


def test_alert_get_active_alerts():
    """Test getting active alerts."""
    manager = AlertManager()

    # Create alerts of different severities
    for severity in [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.CRITICAL]:
        alert = Alert(
            id=f"alert_{severity.value}",
            rule_name=f"rule_{severity.value}",
            severity=severity,
            state=AlertState.FIRING,
            message="Test",
        )
        manager.active_alerts[alert.id] = alert

    # Get all
    all_alerts = manager.get_active_alerts()
    assert len(all_alerts) == 3

    # Filter by severity
    warnings = manager.get_active_alerts(severity=AlertSeverity.WARNING)
    assert len(warnings) == 1
    assert warnings[0].severity == AlertSeverity.WARNING


def test_alert_statistics():
    """Test alert statistics."""
    manager = AlertManager()

    # Register some rules
    for i in range(3):
        rule = AlertRule(
            name=f"rule_{i}",
            description="Test",
            severity=AlertSeverity.INFO,
            condition=lambda: False,
            message_template="Test",
        )
        manager.register_rule(rule)

    # Add some active alerts
    manager.total_fired = 10
    manager.total_resolved = 5

    stats = manager.get_statistics()

    assert stats["total_rules"] == 3
    assert stats["total_fired"] == 10
    assert stats["total_resolved"] == 5


def test_create_high_error_rate_rule():
    """Test high error rate rule creation."""
    collector = MetricsCollector()

    # Add tasks
    for _ in range(5):
        collector.record_task_completion(1.0, success=True)

    for _ in range(5):
        collector.record_task_completion(1.0, success=False)

    rule = create_high_error_rate_rule(collector, threshold=0.3)

    # 50% error rate > 30% threshold
    assert rule.evaluate() is True


def test_alert_to_dict():
    """Test alert serialization."""
    alert = Alert(
        id="test_id",
        rule_name="test_rule",
        severity=AlertSeverity.WARNING,
        state=AlertState.FIRING,
        message="Test alert",
        labels={"env": "prod"},
    )

    data = alert.to_dict()

    assert data["id"] == "test_id"
    assert data["severity"] == "warning"
    assert data["state"] == "firing"
    assert data["labels"]["env"] == "prod"
