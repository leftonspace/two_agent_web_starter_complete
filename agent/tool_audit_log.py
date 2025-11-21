"""
PHASE 2.2: Tool Access Audit Logging

Comprehensive audit logging for all tool access attempts (successful and denied).
Provides immutable audit trail for security and compliance.

Features:
- JSONL format for easy parsing
- Structured logging with timestamps
- Success and failure tracking
- Query and reporting capabilities

Usage:
    from agent.tool_audit_log import log_tool_access, get_audit_logs

    # Log access attempt
    log_tool_access(
        mission_id="mission_123",
        role_id="hr_recruiter",
        tool_name="send_email",
        domain="hr",
        allowed=True,
        reason=None
    )

    # Query logs
    logs = get_audit_logs(role_id="hr_recruiter", days=30)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════


# Default audit log location
DEFAULT_AUDIT_LOG_PATH = Path(__file__).parent.parent / "data" / "tool_access_log.jsonl"


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class ToolAccessEvent:
    """
    Record of a tool access attempt.

    Attributes:
        timestamp: ISO 8601 timestamp
        mission_id: Mission/run identifier
        role_id: Role attempting access
        tool_name: Tool being accessed
        domain: Domain context
        allowed: Whether access was granted
        reason: Denial reason (if allowed=False)
        user_id: Optional user identifier
        permissions_checked: Permissions that were checked
        metadata: Additional event metadata
    """
    timestamp: str
    mission_id: str
    role_id: str
    tool_name: str
    domain: Optional[str]
    allowed: bool
    reason: Optional[str] = None
    user_id: Optional[str] = None
    permissions_checked: List[str] = None
    metadata: Dict[str, Any] = None


# ══════════════════════════════════════════════════════════════════════
# Audit Logging Functions
# ══════════════════════════════════════════════════════════════════════


def log_tool_access(
    mission_id: str,
    role_id: str,
    tool_name: str,
    domain: Optional[str],
    allowed: bool,
    reason: Optional[str] = None,
    user_id: Optional[str] = None,
    permissions_checked: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    log_path: Optional[Path] = None
) -> None:
    """
    Log a tool access attempt to audit log.

    Args:
        mission_id: Mission/run identifier
        role_id: Role attempting access
        tool_name: Tool being accessed
        domain: Domain context
        allowed: Whether access was granted
        reason: Denial reason (if allowed=False)
        user_id: Optional user identifier
        permissions_checked: Permissions that were checked
        metadata: Additional event metadata
        log_path: Custom log path (defaults to data/tool_access_log.jsonl)

    Example:
        log_tool_access(
            mission_id="mission_123",
            role_id="hr_recruiter",
            tool_name="approve_offer",
            domain="hr",
            allowed=False,
            reason="Missing permission: offer_approve"
        )
    """
    if log_path is None:
        log_path = DEFAULT_AUDIT_LOG_PATH

    # Create event
    event = ToolAccessEvent(
        timestamp=datetime.utcnow().isoformat() + "Z",
        mission_id=mission_id,
        role_id=role_id,
        tool_name=tool_name,
        domain=domain,
        allowed=allowed,
        reason=reason,
        user_id=user_id,
        permissions_checked=permissions_checked or [],
        metadata=metadata or {}
    )

    # Ensure directory exists
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create audit log directory: {e}")
        return

    # Append to log file
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

        # Log to application logger as well
        if allowed:
            logger.info(
                f"Tool access granted: role={role_id} tool={tool_name} domain={domain}"
            )
        else:
            logger.warning(
                f"Tool access denied: role={role_id} tool={tool_name} "
                f"domain={domain} reason={reason}"
            )

    except Exception as e:
        logger.error(f"Failed to write audit log: {e}", exc_info=True)


def get_audit_logs(
    role_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    domain: Optional[str] = None,
    allowed: Optional[bool] = None,
    days: int = 30,
    log_path: Optional[Path] = None
) -> List[ToolAccessEvent]:
    """
    Query audit logs with filters.

    Args:
        role_id: Filter by role
        tool_name: Filter by tool
        domain: Filter by domain
        allowed: Filter by access result (True=granted, False=denied, None=all)
        days: Number of days to look back
        log_path: Custom log path

    Returns:
        List of matching audit events

    Example:
        # Get all denied access attempts for hr_recruiter in last 7 days
        denied = get_audit_logs(
            role_id="hr_recruiter",
            allowed=False,
            days=7
        )
        for event in denied:
            print(f"{event.timestamp}: {event.tool_name} - {event.reason}")
    """
    if log_path is None:
        log_path = DEFAULT_AUDIT_LOG_PATH

    if not log_path.exists():
        return []

    cutoff_time = datetime.utcnow() - timedelta(days=days)
    results = []

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event_dict = json.loads(line)
                    event = ToolAccessEvent(**event_dict)

                    # Parse timestamp
                    event_time = datetime.fromisoformat(event.timestamp.rstrip("Z"))
                    if event_time < cutoff_time:
                        continue

                    # Apply filters
                    if role_id and event.role_id != role_id:
                        continue
                    if tool_name and event.tool_name != tool_name:
                        continue
                    if domain and event.domain != domain:
                        continue
                    if allowed is not None and event.allowed != allowed:
                        continue

                    results.append(event)

                except Exception as e:
                    logger.warning(f"Failed to parse audit log line: {e}")
                    continue

    except Exception as e:
        logger.error(f"Failed to read audit log: {e}")
        return []

    return results


def get_access_statistics(
    days: int = 30,
    log_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Get statistics on tool access patterns.

    Args:
        days: Number of days to analyze
        log_path: Custom log path

    Returns:
        Dictionary with access statistics

    Example:
        stats = get_access_statistics(days=7)
        print(f"Total accesses: {stats['total']}")
        print(f"Denied: {stats['denied']}")
        print(f"Top tools: {stats['top_tools']}")
    """
    logs = get_audit_logs(days=days, log_path=log_path)

    total = len(logs)
    granted = sum(1 for log in logs if log.allowed)
    denied = sum(1 for log in logs if not log.allowed)

    # Count by tool
    tool_counts = {}
    for log in logs:
        tool_counts[log.tool_name] = tool_counts.get(log.tool_name, 0) + 1

    # Count by role
    role_counts = {}
    for log in logs:
        role_counts[log.role_id] = role_counts.get(log.role_id, 0) + 1

    # Count by domain
    domain_counts = {}
    for log in logs:
        if log.domain:
            domain_counts[log.domain] = domain_counts.get(log.domain, 0) + 1

    # Top denied tools
    denied_logs = [log for log in logs if not log.allowed]
    denied_tool_counts = {}
    for log in denied_logs:
        denied_tool_counts[log.tool_name] = denied_tool_counts.get(log.tool_name, 0) + 1

    return {
        "total": total,
        "granted": granted,
        "denied": denied,
        "grant_rate": round(granted / total * 100, 2) if total > 0 else 0,
        "top_tools": sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_roles": sorted(role_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_domains": sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        "top_denied_tools": sorted(denied_tool_counts.items(), key=lambda x: x[1], reverse=True)[:10],
    }


def clear_old_logs(days: int = 90, log_path: Optional[Path] = None) -> int:
    """
    Remove audit logs older than specified days.

    Args:
        days: Remove logs older than this many days
        log_path: Custom log path

    Returns:
        Number of logs removed

    Example:
        removed = clear_old_logs(days=90)
        print(f"Removed {removed} old audit logs")
    """
    if log_path is None:
        log_path = DEFAULT_AUDIT_LOG_PATH

    if not log_path.exists():
        return 0

    cutoff_time = datetime.utcnow() - timedelta(days=days)
    kept_logs = []
    removed = 0

    try:
        # Read all logs
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event_dict = json.loads(line)
                    event_time = datetime.fromisoformat(event_dict["timestamp"].rstrip("Z"))

                    if event_time >= cutoff_time:
                        kept_logs.append(line)
                    else:
                        removed += 1

                except Exception:
                    # Keep malformed lines
                    kept_logs.append(line)

        # Write back kept logs
        with open(log_path, "w", encoding="utf-8") as f:
            f.writelines(kept_logs)

        logger.info(f"Cleared {removed} audit logs older than {days} days")
        return removed

    except Exception as e:
        logger.error(f"Failed to clear old logs: {e}")
        return 0
