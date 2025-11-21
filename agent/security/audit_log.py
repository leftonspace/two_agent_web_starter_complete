"""
PHASE 11.3: Audit Logging

Comprehensive audit logging for security events and compliance.

Features:
- Structured audit events
- Multiple severity levels
- Event type categorization
- Searchable audit trail
- Compliance reporting
- Retention policies
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class AuditEventType(Enum):
    """Types of audit events."""

    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"

    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"

    # API events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_ROTATED = "api_key_rotated"

    # Data access events
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"

    # Security events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_ALERT = "security_alert"

    # System events
    CONFIG_CHANGED = "config_changed"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Structured audit event.

    Contains all information needed for compliance and security analysis.
    """

    # Core fields
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    timestamp: float = field(default_factory=time.time)

    # Actor information
    user_id: Optional[str] = None
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None

    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    # Action details
    action: Optional[str] = None
    outcome: Optional[str] = None

    # Context
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Tracing
    request_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        data["timestamp_iso"] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Audit logger for security events.

    Features:
    - Structured event logging
    - Multiple output formats (JSON, text)
    - Event filtering and search
    - Retention policies
    - Compliance reporting
    """

    def __init__(
        self,
        log_file: Optional[Path] = None,
        retention_days: int = 90,
        max_events: int = 10000,
    ):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file (optional)
            retention_days: Days to retain audit logs
            max_events: Maximum events to keep in memory
        """
        self.log_file = log_file
        self.retention_days = retention_days
        self.max_events = max_events

        # In-memory event store
        self.events: List[AuditEvent] = []

        # Statistics
        self.total_events = 0
        self.events_by_type: Dict[AuditEventType, int] = {}
        self.events_by_severity: Dict[AuditSeverity, int] = {}

    async def log(
        self,
        event_type: AuditEventType,
        message: str,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Log an audit event.

        Args:
            event_type: Type of audit event
            message: Human-readable message
            severity: Event severity
            user_id: User identifier
            **kwargs: Additional event fields
        """
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            user_id=user_id,
            **kwargs,
        )

        # Add to memory store
        self.events.append(event)

        # Update statistics
        self.total_events += 1
        self.events_by_type[event_type] = self.events_by_type.get(event_type, 0) + 1
        self.events_by_severity[severity] = self.events_by_severity.get(severity, 0) + 1

        # Enforce max events limit
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

        # Write to file if configured
        if self.log_file:
            await self._write_to_file(event)

        # Print to console for critical events
        if severity == AuditSeverity.CRITICAL:
            print(f"[AUDIT-CRITICAL] {event.message}")

    async def _write_to_file(self, event: AuditEvent):
        """Write event to log file."""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.log_file, "a") as f:
                f.write(event.to_json() + "\n")

        except Exception as e:
            print(f"Failed to write audit log: {e}")

    def search(
        self,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[AuditSeverity] = None,
        user_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Search audit events.

        Args:
            event_type: Filter by event type
            severity: Filter by severity
            user_id: Filter by user ID
            start_time: Filter by start timestamp
            end_time: Filter by end timestamp
            limit: Maximum results

        Returns:
            List of matching audit events
        """
        results = []

        for event in reversed(self.events):  # Most recent first
            # Apply filters
            if event_type and event.event_type != event_type:
                continue

            if severity and event.severity != severity:
                continue

            if user_id and event.user_id != user_id:
                continue

            if start_time and event.timestamp < start_time:
                continue

            if end_time and event.timestamp > end_time:
                continue

            results.append(event)

            if len(results) >= limit:
                break

        return results

    def get_user_activity(
        self,
        user_id: str,
        hours: int = 24,
    ) -> List[AuditEvent]:
        """
        Get recent activity for a user.

        Args:
            user_id: User identifier
            hours: Hours of history

        Returns:
            List of user's audit events
        """
        start_time = time.time() - (hours * 3600)
        return self.search(user_id=user_id, start_time=start_time)

    def get_security_events(
        self,
        hours: int = 24,
    ) -> List[AuditEvent]:
        """
        Get recent security events.

        Args:
            hours: Hours of history

        Returns:
            List of security-related events
        """
        start_time = time.time() - (hours * 3600)

        security_types = [
            AuditEventType.AUTH_FAILURE,
            AuditEventType.ACCESS_DENIED,
            AuditEventType.RATE_LIMIT_EXCEEDED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.SECURITY_ALERT,
        ]

        results = []
        for event_type in security_types:
            results.extend(
                self.search(event_type=event_type, start_time=start_time)
            )

        # Sort by timestamp (most recent first)
        results.sort(key=lambda e: e.timestamp, reverse=True)

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        return {
            "total_events": self.total_events,
            "events_in_memory": len(self.events),
            "events_by_type": {
                k.value: v for k, v in self.events_by_type.items()
            },
            "events_by_severity": {
                k.value: v for k, v in self.events_by_severity.items()
            },
            "retention_days": self.retention_days,
        }

    def cleanup_old_events(self):
        """Remove events older than retention period."""
        if self.retention_days <= 0:
            return

        cutoff = time.time() - (self.retention_days * 86400)
        self.events = [e for e in self.events if e.timestamp > cutoff]

    def export_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Generate compliance report for date range.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report data
        """
        start_time = start_date.timestamp()
        end_time = end_date.timestamp()

        events = self.search(start_time=start_time, end_time=end_time, limit=999999)

        # Group by event type
        by_type = {}
        for event in events:
            event_type = event.event_type.value
            by_type[event_type] = by_type.get(event_type, 0) + 1

        # Security events summary
        security_events = [
            e for e in events
            if e.event_type in [
                AuditEventType.AUTH_FAILURE,
                AuditEventType.ACCESS_DENIED,
                AuditEventType.SUSPICIOUS_ACTIVITY,
            ]
        ]

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_events": len(events),
            "events_by_type": by_type,
            "security_events_count": len(security_events),
            "critical_events_count": len([
                e for e in events
                if e.severity == AuditSeverity.CRITICAL
            ]),
            "unique_users": len(set(e.user_id for e in events if e.user_id)),
        }


# Global audit logger singleton
_global_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AuditLogger()
    return _global_logger
