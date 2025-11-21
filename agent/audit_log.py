"""
PHASE 5.1: Audit & Compliance Logging (WORM - Write-Once-Read-Many)

Provides immutable audit trail for compliance with cryptographic signatures.
Logs all sensitive actions with user attribution (who/what/when/why).

Key Features:
- Append-only JSONL log (WORM)
- Cryptographic signatures (HMAC-SHA256)
- Tamper detection via signature verification
- User-centric attribution (not agent-centric)
- Comprehensive action tracking

Logged Actions:
- Tool executions
- File writes/deletes
- Approval decisions
- Configuration changes
- Permission changes
- Database queries
- API calls

Usage:
    audit = AuditLogger()

    # Log action
    audit.log_action(
        user_id="john.doe@company.com",
        action="file_write",
        entity_type="file",
        entity_id="/sites/project/index.html",
        changes={"content": "...", "size_bytes": 1024},
        reason="Manager approved design changes",
        metadata={"mission_id": "abc123", "iteration": 2}
    )

    # Verify log integrity
    is_valid, issues = audit.verify_log_integrity()

    # Query logs
    entries = audit.query_logs(
        user_id="john.doe@company.com",
        start_date="2025-01-01",
        end_date="2025-01-31"
    )
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class AuditEntry:
    """
    Single audit log entry.

    Fields:
        entry_id: Unique entry ID (monotonic counter)
        user_id: User identifier (email, username, employee_id)
        action: Action type (file_write, tool_exec, approval_decision, etc.)
        entity_type: Type of entity affected (file, tool, approval, config, etc.)
        entity_id: Unique identifier for the entity
        timestamp: ISO 8601 timestamp with timezone
        changes: Dict of changes made (before/after, new values, etc.)
        reason: Human-readable reason for the action
        metadata: Additional context (mission_id, iteration, etc.)
        signature: HMAC-SHA256 signature for tamper detection
        prev_signature: Signature of previous entry (blockchain-style chaining)
    """

    entry_id: int
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    timestamp: str
    changes: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    prev_signature: str = ""


# ══════════════════════════════════════════════════════════════════════
# Audit Logger
# ══════════════════════════════════════════════════════════════════════


class AuditLogger:
    """
    WORM (Write-Once-Read-Many) audit logger with cryptographic signatures.

    Provides immutable audit trail for compliance and forensic analysis.
    """

    def __init__(self, log_file: Optional[Path] = None, secret_key: Optional[str] = None):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file (default: data/audit_log.jsonl)
            secret_key: Secret key for HMAC signatures (default: from env or generated)
        """
        if log_file is None:
            agent_dir = Path(__file__).resolve().parent
            data_dir = agent_dir.parent / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            log_file = data_dir / "audit_log.jsonl"

        self.log_file = log_file

        # Get or generate secret key for signatures
        if secret_key is None:
            secret_key = os.getenv("AUDIT_LOG_SECRET_KEY")
            if not secret_key:
                # Generate and save secret key
                secret_key = self._generate_secret_key()
                print(
                    f"[AuditLog] Generated new secret key. Set AUDIT_LOG_SECRET_KEY "
                    f"environment variable to persist across restarts."
                )

        self.secret_key = secret_key.encode("utf-8")

        # Cache last signature for chaining
        self._last_signature = self._get_last_signature()
        self._entry_counter = self._get_last_entry_id() + 1

    def _generate_secret_key(self) -> str:
        """Generate a random secret key for HMAC signatures."""
        import secrets

        return secrets.token_hex(32)

    def _get_last_signature(self) -> str:
        """Get signature of last log entry for blockchain-style chaining."""
        if not self.log_file.exists():
            return "GENESIS"  # First entry

        try:
            # Read last line
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry.get("signature", "GENESIS")
        except Exception:
            pass

        return "GENESIS"

    def _get_last_entry_id(self) -> int:
        """Get ID of last log entry for monotonic counter."""
        if not self.log_file.exists():
            return 0

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry.get("entry_id", 0)
        except Exception:
            pass

        return 0

    def _compute_signature(self, entry: AuditEntry) -> str:
        """
        Compute HMAC-SHA256 signature for audit entry.

        Signature includes:
        - All entry fields except signature itself
        - Previous entry signature (blockchain chaining)

        Args:
            entry: Audit entry to sign

        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        # Create canonical representation (sorted keys for deterministic hash)
        entry_dict = asdict(entry)
        entry_dict.pop("signature", None)  # Don't include signature in signature

        canonical = json.dumps(entry_dict, sort_keys=True, ensure_ascii=False)
        signature = hmac.new(self.secret_key, canonical.encode("utf-8"), hashlib.sha256)
        return signature.hexdigest()

    def log_action(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        changes: Optional[Dict[str, Any]] = None,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """
        Log an action to the audit log (append-only).

        Args:
            user_id: User identifier (email, username, employee_id)
            action: Action type (file_write, tool_exec, approval_decision, etc.)
            entity_type: Type of entity (file, tool, approval, config, etc.)
            entity_id: Unique identifier for the entity
            changes: Dict of changes made (optional)
            reason: Human-readable reason for the action
            metadata: Additional context (mission_id, iteration, etc.)

        Returns:
            AuditEntry that was logged
        """
        # Create entry
        entry = AuditEntry(
            entry_id=self._entry_counter,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            changes=changes or {},
            reason=reason,
            metadata=metadata or {},
            prev_signature=self._last_signature,
        )

        # Compute signature
        entry.signature = self._compute_signature(entry)

        # Append to log file (WORM - Write-Once-Read-Many)
        self._append_entry(entry)

        # Update cache
        self._last_signature = entry.signature
        self._entry_counter += 1

        return entry

    def _append_entry(self, entry: AuditEntry) -> None:
        """
        Append entry to log file (append-only, immutable).

        Args:
            entry: Audit entry to append
        """
        try:
            # Ensure parent directory exists
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            # Append to JSONL file
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

        except Exception as e:
            print(f"[AuditLog] ERROR: Failed to write audit log: {e}")
            # Don't raise - audit logging should never crash the main application
            # But log to stderr for alerting
            import sys

            print(f"[AuditLog] CRITICAL: Audit log write failure: {e}", file=sys.stderr)

    def query_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AuditEntry]:
        """
        Query audit logs with filters.

        Args:
            user_id: Filter by user ID
            action: Filter by action type
            entity_type: Filter by entity type
            start_date: Filter by start date (ISO 8601)
            end_date: Filter by end date (ISO 8601)
            limit: Maximum number of entries to return

        Returns:
            List of matching audit entries (newest first)
        """
        if not self.log_file.exists():
            return []

        entries = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    entry_dict = json.loads(line)
                    entry = AuditEntry(**entry_dict)

                    # Apply filters
                    if user_id and entry.user_id != user_id:
                        continue
                    if action and entry.action != action:
                        continue
                    if entity_type and entry.entity_type != entity_type:
                        continue
                    if start_date and entry.timestamp < start_date:
                        continue
                    if end_date and entry.timestamp > end_date:
                        continue

                    entries.append(entry)

        except Exception as e:
            print(f"[AuditLog] Error querying logs: {e}")

        # Sort by timestamp (newest first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply limit
        if limit:
            entries = entries[:limit]

        return entries

    def verify_log_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify integrity of audit log (tamper detection).

        Checks:
        1. All signatures are valid (HMAC verification)
        2. Signature chain is unbroken (prev_signature matches)
        3. Entry IDs are monotonic (no gaps or duplicates)

        Returns:
            Tuple of (is_valid, list_of_issues)
            - is_valid: True if log is intact, False if tampered
            - list_of_issues: List of integrity issues found
        """
        if not self.log_file.exists():
            return (True, [])  # Empty log is valid

        issues = []
        prev_signature = "GENESIS"
        prev_entry_id = 0

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    if not line.strip():
                        continue

                    entry_dict = json.loads(line)
                    entry = AuditEntry(**entry_dict)

                    # Check 1: Verify signature
                    expected_signature = self._compute_signature(entry)
                    if entry.signature != expected_signature:
                        issues.append(
                            f"Line {line_num}: Signature mismatch for entry {entry.entry_id}. "
                            f"Expected: {expected_signature[:16]}..., "
                            f"Got: {entry.signature[:16]}..."
                        )

                    # Check 2: Verify signature chain
                    if entry.prev_signature != prev_signature:
                        issues.append(
                            f"Line {line_num}: Broken signature chain at entry {entry.entry_id}. "
                            f"Expected prev_signature: {prev_signature[:16]}..., "
                            f"Got: {entry.prev_signature[:16]}..."
                        )

                    # Check 3: Verify monotonic entry IDs
                    if entry.entry_id != prev_entry_id + 1:
                        issues.append(
                            f"Line {line_num}: Non-monotonic entry ID. "
                            f"Expected: {prev_entry_id + 1}, Got: {entry.entry_id}"
                        )

                    prev_signature = entry.signature
                    prev_entry_id = entry.entry_id

        except Exception as e:
            issues.append(f"Error reading log file: {e}")

        is_valid = len(issues) == 0
        return (is_valid, issues)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Returns:
            Dict with stats: total_entries, users, actions, date_range
        """
        if not self.log_file.exists():
            return {
                "total_entries": 0,
                "unique_users": 0,
                "unique_actions": 0,
                "date_range": None,
            }

        entries = self.query_logs()
        users = set(e.user_id for e in entries)
        actions = set(e.action for e in entries)

        date_range = None
        if entries:
            timestamps = sorted(e.timestamp for e in entries)
            date_range = {"start": timestamps[0], "end": timestamps[-1]}

        return {
            "total_entries": len(entries),
            "unique_users": len(users),
            "unique_actions": len(actions),
            "date_range": date_range,
            "actions_by_type": {action: sum(1 for e in entries if e.action == action) for action in actions},
        }


# ══════════════════════════════════════════════════════════════════════
# Global Audit Logger Instance
# ══════════════════════════════════════════════════════════════════════

_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance."""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def log_file_write(
    user_id: str,
    file_path: str,
    size_bytes: int,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log file write action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="file_write",
        entity_type="file",
        entity_id=file_path,
        changes={"size_bytes": size_bytes},
        reason=reason,
        metadata=metadata,
    )


def log_file_delete(
    user_id: str,
    file_path: str,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log file delete action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="file_delete",
        entity_type="file",
        entity_id=file_path,
        reason=reason,
        metadata=metadata,
    )


def log_tool_execution(
    user_id: str,
    tool_name: str,
    tool_args: Dict[str, Any],
    result_summary: str,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log tool execution action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="tool_execution",
        entity_type="tool",
        entity_id=tool_name,
        changes={"args": tool_args, "result": result_summary},
        reason=reason,
        metadata=metadata,
    )


def log_approval_decision(
    user_id: str,
    approval_id: str,
    decision: str,
    comments: str = "",
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log approval decision action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="approval_decision",
        entity_type="approval",
        entity_id=approval_id,
        changes={"decision": decision, "comments": comments},
        reason=reason,
        metadata=metadata,
    )


def log_config_change(
    user_id: str,
    config_key: str,
    old_value: Any,
    new_value: Any,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log configuration change action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="config_change",
        entity_type="config",
        entity_id=config_key,
        changes={"old_value": old_value, "new_value": new_value},
        reason=reason,
        metadata=metadata,
    )


def log_permission_change(
    user_id: str,
    target_user: str,
    permission: str,
    granted: bool,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log permission change action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="permission_change",
        entity_type="permission",
        entity_id=f"{target_user}:{permission}",
        changes={"granted": granted},
        reason=reason,
        metadata=metadata,
    )


def log_database_query(
    user_id: str,
    query: str,
    database: str,
    rows_affected: int,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log database query action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="database_query",
        entity_type="database",
        entity_id=database,
        changes={"query": query, "rows_affected": rows_affected},
        reason=reason,
        metadata=metadata,
    )


def log_api_call(
    user_id: str,
    api_endpoint: str,
    method: str,
    status_code: int,
    reason: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> AuditEntry:
    """Log API call action."""
    audit = get_audit_logger()
    return audit.log_action(
        user_id=user_id,
        action="api_call",
        entity_type="api",
        entity_id=api_endpoint,
        changes={"method": method, "status_code": status_code},
        reason=reason,
        metadata=metadata,
    )
