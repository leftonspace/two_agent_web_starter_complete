"""
PHASE 5.6: Monitoring & Alerting - Alert Management

Alerting system with rules, conditions, and notification channels.

Features:
- Alert rule definition and evaluation
- Cost budget alerts
- Success rate alerts
- Error rate alerts
- Approval timeout alerts
- Email notifications
- Slack webhook notifications
- PagerDuty integration
- Alert history tracking

Usage:
    >>> from agent.alerting import get_alert_manager
    >>> alert_mgr = get_alert_manager()
    >>>
    >>> # Add alert rule
    >>> alert_mgr.add_rule(
    ...     name="Daily Cost Budget",
    ...     condition="daily_cost_exceeds",
    ...     threshold=100.0,
    ...     channels=["email", "slack"]
    ... )
    >>>
    >>> # Check alerts
    >>> alert_mgr.check_all_rules()
"""

from __future__ import annotations

import json
import os
import smtplib
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib import parse, request

# Import monitoring module
try:
    from monitoring import get_metrics_collector, MetricsCollector
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Try to import paths module
try:
    import paths as paths_module
    PATHS_AVAILABLE = True
except ImportError:
    PATHS_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    condition: str  # Condition type (e.g., "daily_cost_exceeds")
    threshold: float
    channels: List[str]
    severity: str = "warning"
    enabled: bool = True
    cooldown_minutes: int = 60  # Don't re-alert within this period
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert instance."""
    rule_name: str
    severity: str
    message: str
    current_value: float
    threshold: float
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════
# Database Schema
# ══════════════════════════════════════════════════════════════════════


ALERTING_SCHEMA = """
-- Alert rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    condition TEXT NOT NULL,
    threshold REAL NOT NULL,
    channels TEXT NOT NULL,  -- JSON array
    severity TEXT NOT NULL DEFAULT 'warning',
    enabled INTEGER NOT NULL DEFAULT 1,
    cooldown_minutes INTEGER NOT NULL DEFAULT 60,
    metadata TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled
    ON alert_rules(enabled);

-- Alert history
CREATE TABLE IF NOT EXISTS alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    current_value REAL NOT NULL,
    threshold REAL NOT NULL,
    timestamp TEXT NOT NULL,
    channels_notified TEXT,  -- JSON array
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_alert_history_timestamp
    ON alert_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_alert_history_rule
    ON alert_history(rule_name);

-- Alert cooldowns (prevent alert spam)
CREATE TABLE IF NOT EXISTS alert_cooldowns (
    rule_name TEXT PRIMARY KEY,
    last_alerted TEXT NOT NULL,
    cooldown_until TEXT NOT NULL
);
"""


# ══════════════════════════════════════════════════════════════════════
# Notification Channels
# ══════════════════════════════════════════════════════════════════════


class EmailNotifier:
    """Email notification channel."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_emails: Optional[List[str]] = None,
    ):
        """
        Initialize email notifier.

        Args:
            smtp_host: SMTP server host (defaults to env var ALERT_SMTP_HOST)
            smtp_port: SMTP server port (defaults to env var ALERT_SMTP_PORT or 587)
            smtp_user: SMTP username (defaults to env var ALERT_SMTP_USER)
            smtp_password: SMTP password (defaults to env var ALERT_SMTP_PASSWORD)
            from_email: From email address (defaults to env var ALERT_FROM_EMAIL)
            to_emails: List of recipient emails (defaults to env var ALERT_TO_EMAILS, comma-separated)
        """
        self.smtp_host = smtp_host or os.getenv("ALERT_SMTP_HOST")
        self.smtp_port = smtp_port or int(os.getenv("ALERT_SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.getenv("ALERT_SMTP_USER")
        self.smtp_password = smtp_password or os.getenv("ALERT_SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("ALERT_FROM_EMAIL", "alerts@example.com")

        if to_emails:
            self.to_emails = to_emails
        else:
            to_emails_str = os.getenv("ALERT_TO_EMAILS", "")
            self.to_emails = [e.strip() for e in to_emails_str.split(",") if e.strip()]

    def send(self, alert: Alert) -> bool:
        """
        Send email notification.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        if not self.smtp_host or not self.to_emails:
            print("[EmailNotifier] Email not configured, skipping notification")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = f"[{alert.severity.upper()}] {alert.rule_name}"

            # Create HTML body
            body = f"""
            <html>
            <body>
                <h2 style="color: {'red' if alert.severity == 'error' else 'orange'}">
                    Alert: {alert.rule_name}
                </h2>
                <p><strong>Severity:</strong> {alert.severity.upper()}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                <p><strong>Current Value:</strong> {alert.current_value:.2f}</p>
                <p><strong>Threshold:</strong> {alert.threshold:.2f}</p>
                <p><strong>Timestamp:</strong> {alert.timestamp}</p>
                {f'<p><strong>Details:</strong> {json.dumps(alert.metadata, indent=2)}</p>' if alert.metadata else ''}
            </body>
            </html>
            """
            msg.attach(MIMEText(body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"[EmailNotifier] Sent alert to {len(self.to_emails)} recipients")
            return True

        except Exception as e:
            print(f"[EmailNotifier] Failed to send email: {e}")
            return False


class SlackNotifier:
    """Slack webhook notification channel."""

    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL (defaults to env var ALERT_SLACK_WEBHOOK)
        """
        self.webhook_url = webhook_url or os.getenv("ALERT_SLACK_WEBHOOK")

    def send(self, alert: Alert) -> bool:
        """
        Send Slack notification.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        if not self.webhook_url:
            print("[SlackNotifier] Slack webhook not configured, skipping notification")
            return False

        try:
            # Map severity to emoji
            severity_emoji = {
                "info": ":information_source:",
                "warning": ":warning:",
                "error": ":x:",
                "critical": ":rotating_light:",
            }
            emoji = severity_emoji.get(alert.severity, ":bell:")

            # Create message payload
            payload = {
                "text": f"{emoji} *{alert.rule_name}*",
                "attachments": [
                    {
                        "color": "danger" if alert.severity in ["error", "critical"] else "warning",
                        "fields": [
                            {"title": "Message", "value": alert.message, "short": False},
                            {"title": "Severity", "value": alert.severity.upper(), "short": True},
                            {"title": "Current Value", "value": f"{alert.current_value:.2f}", "short": True},
                            {"title": "Threshold", "value": f"{alert.threshold:.2f}", "short": True},
                            {"title": "Time", "value": alert.timestamp, "short": True},
                        ],
                    }
                ],
            }

            # Send POST request
            data = json.dumps(payload).encode("utf-8")
            req = request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    print("[SlackNotifier] Sent alert to Slack")
                    return True
                else:
                    print(f"[SlackNotifier] Failed to send: HTTP {response.status}")
                    return False

        except Exception as e:
            print(f"[SlackNotifier] Failed to send to Slack: {e}")
            return False


class PagerDutyNotifier:
    """PagerDuty notification channel."""

    def __init__(self, integration_key: Optional[str] = None):
        """
        Initialize PagerDuty notifier.

        Args:
            integration_key: PagerDuty integration key (defaults to env var ALERT_PAGERDUTY_KEY)
        """
        self.integration_key = integration_key or os.getenv("ALERT_PAGERDUTY_KEY")
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    def send(self, alert: Alert) -> bool:
        """
        Send PagerDuty notification.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully
        """
        if not self.integration_key:
            print("[PagerDutyNotifier] PagerDuty key not configured, skipping notification")
            return False

        try:
            # Map severity to PagerDuty severity
            pd_severity = {
                "info": "info",
                "warning": "warning",
                "error": "error",
                "critical": "critical",
            }.get(alert.severity, "warning")

            # Create event payload
            payload = {
                "routing_key": self.integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"{alert.rule_name}: {alert.message}",
                    "severity": pd_severity,
                    "source": "department-in-a-box",
                    "timestamp": alert.timestamp,
                    "custom_details": {
                        "current_value": alert.current_value,
                        "threshold": alert.threshold,
                        "metadata": alert.metadata,
                    },
                },
            }

            # Send POST request
            data = json.dumps(payload).encode("utf-8")
            req = request.Request(
                self.api_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with request.urlopen(req, timeout=10) as response:
                if response.status == 202:
                    print("[PagerDutyNotifier] Sent alert to PagerDuty")
                    return True
                else:
                    print(f"[PagerDutyNotifier] Failed to send: HTTP {response.status}")
                    return False

        except Exception as e:
            print(f"[PagerDutyNotifier] Failed to send to PagerDuty: {e}")
            return False


# ══════════════════════════════════════════════════════════════════════
# Alert Manager
# ══════════════════════════════════════════════════════════════════════


class AlertManager:
    """
    Alert management system.

    Evaluates alert rules and sends notifications via configured channels.
    """

    def __init__(
        self,
        db_path: Optional[Path] = None,
        metrics_collector: Optional[MetricsCollector] = None,
    ):
        """
        Initialize alert manager.

        Args:
            db_path: Path to SQLite database (None = default location)
            metrics_collector: Metrics collector instance
        """
        if db_path is None:
            if PATHS_AVAILABLE:
                db_path = paths_module.get_data_dir() / "alerting.db"
            else:
                db_path = Path(__file__).parent.parent / "data" / "alerting.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Metrics collector
        if metrics_collector:
            self.metrics = metrics_collector
        elif MONITORING_AVAILABLE:
            self.metrics = get_metrics_collector()
        else:
            self.metrics = None
            print("[AlertManager] Warning: Monitoring module not available")

        # Notification channels
        self.email_notifier = EmailNotifier()
        self.slack_notifier = SlackNotifier()
        self.pagerduty_notifier = PagerDutyNotifier()

        # Built-in alert conditions
        self.conditions: Dict[str, Callable] = {
            "daily_cost_exceeds": self._check_daily_cost_exceeds,
            "success_rate_below": self._check_success_rate_below,
            "error_rate_increases": self._check_error_rate_increases,
            "approval_timeout": self._check_approval_timeout,
            "queue_length_exceeds": self._check_queue_length_exceeds,
        }

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(ALERTING_SCHEMA)
            conn.commit()

    def _now(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    # ──────────────────────────────────────────────────────────────────
    # Rule Management
    # ──────────────────────────────────────────────────────────────────

    def add_rule(
        self,
        name: str,
        condition: str,
        threshold: float,
        channels: List[str],
        severity: str = "warning",
        enabled: bool = True,
        cooldown_minutes: int = 60,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add or update alert rule.

        Args:
            name: Rule name (unique identifier)
            condition: Condition type
            threshold: Threshold value
            channels: List of notification channels
            severity: Alert severity
            enabled: Whether rule is enabled
            cooldown_minutes: Cooldown period between alerts
            metadata: Additional metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            now = self._now()

            conn.execute("""
                INSERT OR REPLACE INTO alert_rules (
                    name, condition, threshold, channels, severity,
                    enabled, cooldown_minutes, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name,
                condition,
                threshold,
                json.dumps(channels),
                severity,
                1 if enabled else 0,
                cooldown_minutes,
                json.dumps(metadata) if metadata else None,
                now,
                now,
            ))
            conn.commit()

    def get_rules(self, enabled_only: bool = True) -> List[AlertRule]:
        """
        Get all alert rules.

        Args:
            enabled_only: Only return enabled rules

        Returns:
            List of alert rules
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM alert_rules"
            if enabled_only:
                query += " WHERE enabled = 1"

            cursor.execute(query)
            rows = cursor.fetchall()

            return [
                AlertRule(
                    name=row["name"],
                    condition=row["condition"],
                    threshold=row["threshold"],
                    channels=json.loads(row["channels"]),
                    severity=row["severity"],
                    enabled=bool(row["enabled"]),
                    cooldown_minutes=row["cooldown_minutes"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]

    def disable_rule(self, name: str) -> None:
        """Disable alert rule."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE alert_rules SET enabled = 0, updated_at = ? WHERE name = ?",
                (self._now(), name),
            )
            conn.commit()

    def enable_rule(self, name: str) -> None:
        """Enable alert rule."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE alert_rules SET enabled = 1, updated_at = ? WHERE name = ?",
                (self._now(), name),
            )
            conn.commit()

    # ──────────────────────────────────────────────────────────────────
    # Alert Conditions
    # ──────────────────────────────────────────────────────────────────

    def _check_daily_cost_exceeds(self, rule: AlertRule) -> Optional[Alert]:
        """Check if daily cost exceeds threshold."""
        if not self.metrics:
            return None

        stats = self.metrics.get_mission_stats(hours=24)
        current_cost = stats["total_cost_usd"]

        if current_cost > rule.threshold:
            return Alert(
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Daily cost ${current_cost:.2f} exceeds threshold ${rule.threshold:.2f}",
                current_value=current_cost,
                threshold=rule.threshold,
                timestamp=self._now(),
                metadata={"stats": stats},
            )
        return None

    def _check_success_rate_below(self, rule: AlertRule) -> Optional[Alert]:
        """Check if success rate drops below threshold."""
        if not self.metrics:
            return None

        stats = self.metrics.get_mission_stats(hours=24)
        success_rate = stats["success_rate"] * 100  # Convert to percentage

        if success_rate < rule.threshold:
            return Alert(
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Success rate {success_rate:.1f}% is below threshold {rule.threshold:.1f}%",
                current_value=success_rate,
                threshold=rule.threshold,
                timestamp=self._now(),
                metadata={"stats": stats},
            )
        return None

    def _check_error_rate_increases(self, rule: AlertRule) -> Optional[Alert]:
        """Check if error rate increased significantly."""
        if not self.metrics:
            return None

        # Compare last hour to previous hour
        recent_stats = self.metrics.get_error_rate(hours=1)
        previous_stats = self.metrics.get_error_rate(hours=2)

        recent_rate = recent_stats["failure_rate"]
        if previous_stats["total_missions"] > 0:
            previous_rate = previous_stats["failure_rate"]
        else:
            previous_rate = 0

        # Check if error rate increased by threshold multiplier
        if previous_rate > 0 and recent_rate > previous_rate * rule.threshold:
            increase_factor = recent_rate / previous_rate if previous_rate > 0 else float('inf')
            return Alert(
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Error rate increased {increase_factor:.1f}x (from {previous_rate:.1%} to {recent_rate:.1%})",
                current_value=increase_factor,
                threshold=rule.threshold,
                timestamp=self._now(),
                metadata={"recent_stats": recent_stats, "previous_stats": previous_stats},
            )
        return None

    def _check_approval_timeout(self, rule: AlertRule) -> Optional[Alert]:
        """Check for approval timeouts (placeholder - needs integration)."""
        # This would require integration with approval workflow system
        # For now, return None
        return None

    def _check_queue_length_exceeds(self, rule: AlertRule) -> Optional[Alert]:
        """Check if queue length exceeds threshold."""
        if not self.metrics:
            return None

        health = self.metrics.get_latest_health()
        if not health:
            return None

        queue_length = health["queue_length"]
        if queue_length > rule.threshold:
            return Alert(
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Queue length {queue_length} exceeds threshold {rule.threshold}",
                current_value=queue_length,
                threshold=rule.threshold,
                timestamp=self._now(),
                metadata={"health": health},
            )
        return None

    # ──────────────────────────────────────────────────────────────────
    # Alert Evaluation
    # ──────────────────────────────────────────────────────────────────

    def check_rule(self, rule: AlertRule) -> Optional[Alert]:
        """
        Check if alert rule condition is met.

        Args:
            rule: Alert rule to check

        Returns:
            Alert if condition is met, None otherwise
        """
        # Check if rule is in cooldown
        if self._is_in_cooldown(rule.name):
            return None

        # Evaluate condition
        condition_func = self.conditions.get(rule.condition)
        if not condition_func:
            print(f"[AlertManager] Unknown condition: {rule.condition}")
            return None

        return condition_func(rule)

    def check_all_rules(self) -> List[Alert]:
        """
        Check all enabled rules.

        Returns:
            List of triggered alerts
        """
        rules = self.get_rules(enabled_only=True)
        alerts = []

        for rule in rules:
            alert = self.check_rule(rule)
            if alert:
                alerts.append(alert)
                # Send notifications
                self._send_alert(alert, rule.channels)
                # Record in history
                self._record_alert(alert, rule.channels)
                # Set cooldown
                self._set_cooldown(rule.name, rule.cooldown_minutes)

        return alerts

    # ──────────────────────────────────────────────────────────────────
    # Cooldown Management
    # ──────────────────────────────────────────────────────────────────

    def _is_in_cooldown(self, rule_name: str) -> bool:
        """Check if rule is in cooldown period."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT cooldown_until FROM alert_cooldowns WHERE rule_name = ?",
                (rule_name,),
            )
            row = cursor.fetchone()
            if row:
                cooldown_until = datetime.fromisoformat(row[0])
                if datetime.utcnow() < cooldown_until:
                    return True
                else:
                    # Cooldown expired, remove it
                    conn.execute("DELETE FROM alert_cooldowns WHERE rule_name = ?", (rule_name,))
                    conn.commit()
        return False

    def _set_cooldown(self, rule_name: str, cooldown_minutes: int) -> None:
        """Set cooldown for rule."""
        now = datetime.utcnow()
        cooldown_until = now + timedelta(minutes=cooldown_minutes)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alert_cooldowns (rule_name, last_alerted, cooldown_until)
                VALUES (?, ?, ?)
            """, (rule_name, now.isoformat(), cooldown_until.isoformat()))
            conn.commit()

    # ──────────────────────────────────────────────────────────────────
    # Notification
    # ──────────────────────────────────────────────────────────────────

    def _send_alert(self, alert: Alert, channels: List[str]) -> None:
        """Send alert via configured channels."""
        for channel in channels:
            if channel == "email":
                self.email_notifier.send(alert)
            elif channel == "slack":
                self.slack_notifier.send(alert)
            elif channel == "pagerduty":
                self.pagerduty_notifier.send(alert)
            else:
                print(f"[AlertManager] Unknown channel: {channel}")

    def _record_alert(self, alert: Alert, channels: List[str]) -> None:
        """Record alert in history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO alert_history (
                    rule_name, severity, message, current_value, threshold,
                    timestamp, channels_notified, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.rule_name,
                alert.severity,
                alert.message,
                alert.current_value,
                alert.threshold,
                alert.timestamp,
                json.dumps(channels),
                json.dumps(alert.metadata),
            ))
            conn.commit()

    # ──────────────────────────────────────────────────────────────────
    # Alert History
    # ──────────────────────────────────────────────────────────────────

    def get_alert_history(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get alert history.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of alerts to return

        Returns:
            List of historical alerts
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    rule_name,
                    severity,
                    message,
                    current_value,
                    threshold,
                    timestamp,
                    channels_notified
                FROM alert_history
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (cutoff, limit))

            return [dict(row) for row in cursor.fetchall()]


# ══════════════════════════════════════════════════════════════════════
# Singleton Instance
# ══════════════════════════════════════════════════════════════════════


_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    Get singleton alert manager instance.

    Returns:
        AlertManager instance
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("Alerting System Demo")
    print("=" * 60)

    alert_mgr = get_alert_manager()

    # Add some sample rules
    print("\nAdding alert rules...")
    alert_mgr.add_rule(
        name="Daily Cost Budget",
        condition="daily_cost_exceeds",
        threshold=100.0,
        channels=["email", "slack"],
        severity="warning",
    )

    alert_mgr.add_rule(
        name="Low Success Rate",
        condition="success_rate_below",
        threshold=80.0,
        channels=["email"],
        severity="error",
    )

    alert_mgr.add_rule(
        name="Error Rate Spike",
        condition="error_rate_increases",
        threshold=2.0,  # 2x increase
        channels=["slack", "pagerduty"],
        severity="critical",
    )

    # Get rules
    rules = alert_mgr.get_rules()
    print(f"\n✓ Added {len(rules)} alert rules")
    for rule in rules:
        print(f"  - {rule.name}: {rule.condition} (threshold: {rule.threshold})")

    print("\n✓ Alerting system initialized")
