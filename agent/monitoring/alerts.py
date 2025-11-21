"""
PHASE 11.2: Alerting System

Alert rules and notification system for monitoring critical conditions.

Features:
- Alert rules with thresholds
- Alert severity levels
- Alert state management (firing, resolved)
- Alert grouping and deduplication
- Notification channels (email, slack, webhook)
- Alert history tracking
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(Enum):
    """Alert states."""
    PENDING = "pending"  # Rule triggered but not firing yet
    FIRING = "firing"  # Alert is firing
    RESOLVED = "resolved"  # Alert condition no longer met


@dataclass
class Alert:
    """An active or resolved alert."""
    id: str
    rule_name: str
    severity: AlertSeverity
    state: AlertState
    message: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    fired_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "state": self.state.value,
            "message": self.message,
            "labels": self.labels,
            "annotations": self.annotations,
            "started_at": self.started_at,
            "resolved_at": self.resolved_at,
            "fired_count": self.fired_count,
            "duration": time.time() - self.started_at if self.state == AlertState.FIRING else None,
        }


@dataclass
class AlertRule:
    """
    Alert rule definition.

    Defines conditions and thresholds for alerting.
    """
    name: str
    description: str
    severity: AlertSeverity
    condition: Callable[[], bool]
    message_template: str
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    for_duration: float = 0  # Seconds condition must be true before firing
    cooldown: float = 300  # Seconds between repeated alerts

    # Internal state
    _condition_met_at: Optional[float] = None
    _last_fired_at: Optional[float] = None

    def evaluate(self) -> bool:
        """
        Evaluate rule condition.

        Returns:
            True if alert should fire
        """
        try:
            condition_met = self.condition()
        except Exception as e:
            print(f"[AlertRule] Error evaluating {self.name}: {e}")
            return False

        current_time = time.time()

        if condition_met:
            # Track when condition first met
            if self._condition_met_at is None:
                self._condition_met_at = current_time

            # Check if condition has been met for required duration
            duration = current_time - self._condition_met_at

            if duration >= self.for_duration:
                # Check cooldown
                if self._last_fired_at is None or (current_time - self._last_fired_at) >= self.cooldown:
                    return True

        else:
            # Condition no longer met, reset
            self._condition_met_at = None

        return False

    def mark_fired(self):
        """Mark rule as fired."""
        self._last_fired_at = time.time()

    def format_message(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Format alert message with context."""
        if context:
            try:
                return self.message_template.format(**context)
            except KeyError:
                pass

        return self.message_template


class AlertManager:
    """
    Manage alerts and notification.

    Evaluates rules, tracks alerts, and sends notifications.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000

        # Statistics
        self.total_fired = 0
        self.total_resolved = 0

    def register_rule(self, rule: AlertRule):
        """
        Register alert rule.

        Args:
            rule: AlertRule to register
        """
        self.rules[rule.name] = rule
        print(f"[AlertManager] Registered rule: {rule.name} ({rule.severity.value})")

    def unregister_rule(self, rule_name: str):
        """Unregister alert rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]

    def evaluate_rules(self):
        """
        Evaluate all rules and update alerts.

        Should be called periodically (e.g., every 30 seconds).
        """
        for rule_name, rule in self.rules.items():
            should_fire = rule.evaluate()

            alert_id = f"{rule_name}_{hash(frozenset(rule.labels.items()))}"

            if should_fire:
                # Check if alert already firing
                if alert_id in self.active_alerts:
                    # Update existing alert
                    alert = self.active_alerts[alert_id]
                    alert.fired_count += 1
                else:
                    # Create new alert
                    alert = Alert(
                        id=alert_id,
                        rule_name=rule_name,
                        severity=rule.severity,
                        state=AlertState.FIRING,
                        message=rule.format_message(),
                        labels=rule.labels.copy(),
                        annotations=rule.annotations.copy(),
                    )

                    self.active_alerts[alert_id] = alert
                    self.total_fired += 1

                    # Send notification
                    self._send_notification(alert)

                # Mark rule as fired
                rule.mark_fired()

            else:
                # Check if we should resolve alert
                if alert_id in self.active_alerts:
                    alert = self.active_alerts[alert_id]

                    if alert.state == AlertState.FIRING:
                        # Resolve alert
                        alert.state = AlertState.RESOLVED
                        alert.resolved_at = time.time()

                        # Move to history
                        self.alert_history.append(alert)
                        del self.active_alerts[alert_id]

                        self.total_resolved += 1

                        # Trim history
                        if len(self.alert_history) > self.max_history:
                            self.alert_history = self.alert_history[-self.max_history:]

    def _send_notification(self, alert: Alert):
        """Send alert notification."""
        print(f"[AlertManager] 🚨 ALERT: {alert.severity.value.upper()} - {alert.message}")
        print(f"  Rule: {alert.rule_name}")
        if alert.labels:
            print(f"  Labels: {alert.labels}")

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
    ) -> List[Alert]:
        """
        Get active alerts.

        Args:
            severity: Filter by severity

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Sort by severity and time
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.ERROR: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3,
        }

        alerts.sort(key=lambda a: (severity_order[a.severity], a.started_at))

        return alerts

    def get_alert_history(
        self,
        limit: int = 100,
    ) -> List[Alert]:
        """Get alert history."""
        return self.alert_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        active_by_severity = {}
        for alert in self.active_alerts.values():
            severity = alert.severity.value
            active_by_severity[severity] = active_by_severity.get(severity, 0) + 1

        return {
            "total_rules": len(self.rules),
            "active_alerts": len(self.active_alerts),
            "active_by_severity": active_by_severity,
            "total_fired": self.total_fired,
            "total_resolved": self.total_resolved,
        }


# Common alert rules
def create_high_error_rate_rule(
    metrics_collector,
    threshold: float = 0.1,  # 10% error rate
) -> AlertRule:
    """
    Create rule for high error rate.

    Args:
        metrics_collector: MetricsCollector instance
        threshold: Error rate threshold (0.0-1.0)

    Returns:
        AlertRule
    """
    def condition():
        success = metrics_collector.tasks_completed.get(labels={"status": "success"})
        failure = metrics_collector.tasks_completed.get(labels={"status": "failure"})
        total = success + failure

        if total < 10:  # Need at least 10 tasks
            return False

        error_rate = failure / total
        return error_rate >= threshold

    return AlertRule(
        name="high_error_rate",
        description="Task error rate is too high",
        severity=AlertSeverity.WARNING,
        condition=condition,
        message_template=f"Error rate exceeded {threshold*100}%",
        for_duration=60,  # Must be high for 1 minute
        cooldown=300,  # Alert every 5 minutes max
    )


def create_high_cost_rule(
    metrics_collector,
    threshold: float = 10.0,  # $10 USD
) -> AlertRule:
    """
    Create rule for high LLM cost.

    Args:
        metrics_collector: MetricsCollector instance
        threshold: Cost threshold in USD

    Returns:
        AlertRule
    """
    def condition():
        # Sum all model costs
        total_cost = sum(
            sample.value
            for sample in metrics_collector.llm_cost.samples()
        )
        return total_cost >= threshold

    return AlertRule(
        name="high_llm_cost",
        description="LLM cost is too high",
        severity=AlertSeverity.WARNING,
        condition=condition,
        message_template=f"LLM cost exceeded ${threshold:.2f}",
        cooldown=600,  # Alert every 10 minutes max
    )


def create_no_active_sessions_rule(
    metrics_collector,
) -> AlertRule:
    """
    Create rule for no active sessions (system idle).

    Args:
        metrics_collector: MetricsCollector instance

    Returns:
        AlertRule
    """
    def condition():
        return metrics_collector.active_sessions.get() == 0

    return AlertRule(
        name="no_active_sessions",
        description="No active user sessions",
        severity=AlertSeverity.INFO,
        condition=condition,
        message_template="System has no active sessions",
        for_duration=300,  # Idle for 5 minutes
        cooldown=3600,  # Alert every hour max
    )
