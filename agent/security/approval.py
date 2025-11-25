"""
PHASE 1.3: Human-in-the-Loop (HITL) Approval System

Requires human approval for dangerous operations before execution.

Features:
- Action classification by risk level
- Approval queue management
- Timeout handling
- Audit logging of all approvals/rejections
- Configurable auto-approve for low-risk operations

Usage:
    from agent.security.approval import ApprovalManager, require_approval

    manager = ApprovalManager()

    # Check if action requires approval
    if manager.requires_approval("bash", {"command": "rm -rf /tmp/test"}):
        approval = await manager.request_approval(
            action_type="bash",
            action_params={"command": "rm -rf /tmp/test"},
            description="Delete temporary test directory",
            requester="agent_123"
        )

        if approval.approved:
            # Execute action
            pass
        else:
            # Action was rejected
            print(f"Action rejected: {approval.reason}")

    # Or use the decorator
    @require_approval(risk_level="high")
    async def dangerous_operation():
        pass
"""

from __future__ import annotations

import asyncio
import functools
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from agent.core_logging import log_event


class RiskLevel(Enum):
    """Risk levels for actions."""
    LOW = "low"           # Auto-approve
    MEDIUM = "medium"     # Log but auto-approve
    HIGH = "high"         # Requires approval
    CRITICAL = "critical" # Requires approval + confirmation


class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """Represents an approval request."""
    id: str
    action_type: str
    action_params: Dict[str, Any]
    description: str
    risk_level: RiskLevel
    requester: str
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "action_params": self.action_params,
            "description": self.description,
            "risk_level": self.risk_level.value,
            "requester": self.requester,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reason": self.reason,
        }


@dataclass
class ApprovalResult:
    """Result of an approval request."""
    request_id: str
    approved: bool
    status: ApprovalStatus
    reason: Optional[str] = None
    reviewed_by: Optional[str] = None


class ApprovalRequired(Exception):
    """Raised when an action requires approval but none was provided."""

    def __init__(self, request: ApprovalRequest):
        self.request = request
        super().__init__(f"Approval required for {request.action_type}: {request.description}")


# ============================================================================
# Action Risk Classification
# ============================================================================

# Actions that require approval
HIGH_RISK_ACTIONS: Dict[str, RiskLevel] = {
    # Shell commands
    "bash": RiskLevel.HIGH,
    "shell": RiskLevel.HIGH,
    "execute_shell": RiskLevel.HIGH,

    # Financial actions
    "make_payment": RiskLevel.CRITICAL,
    "buy_domain": RiskLevel.HIGH,
    "stripe_charge": RiskLevel.CRITICAL,

    # Data operations
    "delete_file": RiskLevel.HIGH,
    "delete_directory": RiskLevel.HIGH,
    "truncate_table": RiskLevel.CRITICAL,
    "drop_database": RiskLevel.CRITICAL,

    # External communications
    "send_email": RiskLevel.MEDIUM,
    "send_sms": RiskLevel.MEDIUM,

    # Deployment
    "deploy_website": RiskLevel.HIGH,
    "deploy_production": RiskLevel.CRITICAL,

    # Git operations
    "git_push_force": RiskLevel.CRITICAL,
    "git_reset_hard": RiskLevel.HIGH,
}

# Dangerous command patterns (for shell/bash)
DANGEROUS_COMMAND_PATTERNS: List[str] = [
    r"rm\s+-rf",
    r"rm\s+-r",
    r"rm\s+/",
    r"dd\s+if=",
    r"mkfs\.",
    r"format\s",
    r">\s*/dev/",
    r"curl.*\|\s*sh",
    r"wget.*\|\s*sh",
    r"chmod\s+777",
    r"chmod\s+-R",
    r"chown\s+-R",
    r"sudo\s",
    r"su\s+-",
    r"DROP\s+TABLE",
    r"DROP\s+DATABASE",
    r"TRUNCATE\s+TABLE",
    r"DELETE\s+FROM.*WHERE\s+1",
]


class ApprovalManager:
    """
    Manages approval requests for dangerous operations.

    Provides a queue-based system for human review of high-risk actions.
    """

    def __init__(
        self,
        auto_approve_low_risk: bool = True,
        auto_approve_medium_risk: bool = False,
        default_timeout_seconds: int = 300,
        approval_callback: Optional[Callable[[ApprovalRequest], asyncio.Future]] = None,
    ):
        """
        Initialize approval manager.

        Args:
            auto_approve_low_risk: Auto-approve low risk actions
            auto_approve_medium_risk: Auto-approve medium risk actions
            default_timeout_seconds: Default timeout for approval requests
            approval_callback: Async callback to handle approval requests (e.g., send to UI)
        """
        self.auto_approve_low_risk = auto_approve_low_risk
        self.auto_approve_medium_risk = auto_approve_medium_risk
        self.default_timeout_seconds = default_timeout_seconds
        self.approval_callback = approval_callback

        # Pending requests
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._request_events: Dict[str, asyncio.Event] = {}

        # History
        self._history: List[ApprovalRequest] = []
        self._max_history = 1000

        # Statistics
        self.total_requests = 0
        self.approved_count = 0
        self.rejected_count = 0
        self.timeout_count = 0

    def classify_risk(
        self,
        action_type: str,
        action_params: Optional[Dict[str, Any]] = None
    ) -> RiskLevel:
        """
        Classify the risk level of an action.

        Args:
            action_type: Type of action
            action_params: Parameters of the action

        Returns:
            RiskLevel for the action
        """
        # Check predefined risk levels
        if action_type in HIGH_RISK_ACTIONS:
            base_risk = HIGH_RISK_ACTIONS[action_type]
        else:
            base_risk = RiskLevel.LOW

        # Elevate risk for dangerous command patterns
        if action_params and action_type in ("bash", "shell", "execute_shell"):
            command = action_params.get("command", "")
            import re
            for pattern in DANGEROUS_COMMAND_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    return RiskLevel.CRITICAL

        return base_risk

    def requires_approval(
        self,
        action_type: str,
        action_params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if an action requires approval.

        Args:
            action_type: Type of action
            action_params: Parameters of the action

        Returns:
            True if approval is required
        """
        risk = self.classify_risk(action_type, action_params)

        if risk == RiskLevel.LOW and self.auto_approve_low_risk:
            return False
        if risk == RiskLevel.MEDIUM and self.auto_approve_medium_risk:
            return False

        return risk in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    async def request_approval(
        self,
        action_type: str,
        action_params: Dict[str, Any],
        description: str,
        requester: str,
        timeout_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApprovalResult:
        """
        Request approval for an action.

        Args:
            action_type: Type of action
            action_params: Parameters of the action
            description: Human-readable description
            requester: ID of the requester (agent/user)
            timeout_seconds: Timeout for approval (default from config)
            metadata: Additional metadata

        Returns:
            ApprovalResult with approval status
        """
        self.total_requests += 1
        timeout = timeout_seconds or self.default_timeout_seconds

        # Classify risk
        risk_level = self.classify_risk(action_type, action_params)

        # Auto-approve if configured
        if risk_level == RiskLevel.LOW and self.auto_approve_low_risk:
            log_event("approval_auto_approved", {
                "action_type": action_type,
                "risk_level": risk_level.value,
                "reason": "auto_approve_low_risk",
            })
            self.approved_count += 1
            return ApprovalResult(
                request_id="auto",
                approved=True,
                status=ApprovalStatus.APPROVED,
                reason="Auto-approved (low risk)",
            )

        if risk_level == RiskLevel.MEDIUM and self.auto_approve_medium_risk:
            log_event("approval_auto_approved", {
                "action_type": action_type,
                "risk_level": risk_level.value,
                "reason": "auto_approve_medium_risk",
            })
            self.approved_count += 1
            return ApprovalResult(
                request_id="auto",
                approved=True,
                status=ApprovalStatus.APPROVED,
                reason="Auto-approved (medium risk)",
            )

        # Create approval request
        request = ApprovalRequest(
            id=str(uuid.uuid4()),
            action_type=action_type,
            action_params=action_params,
            description=description,
            risk_level=risk_level,
            requester=requester,
            created_at=datetime.now(),
            metadata=metadata or {},
        )

        # Store request
        self._pending_requests[request.id] = request
        self._request_events[request.id] = asyncio.Event()

        # Log request
        log_event("approval_requested", {
            "request_id": request.id,
            "action_type": action_type,
            "risk_level": risk_level.value,
            "requester": requester,
            "description": description[:200],
        })

        # Notify via callback if configured
        if self.approval_callback:
            try:
                await self.approval_callback(request)
            except Exception as e:
                log_event("approval_callback_error", {
                    "request_id": request.id,
                    "error": str(e),
                })

        # Wait for approval with timeout
        try:
            await asyncio.wait_for(
                self._request_events[request.id].wait(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            # Timeout - reject request
            request.status = ApprovalStatus.TIMEOUT
            request.reason = f"Approval timed out after {timeout} seconds"
            self.timeout_count += 1

            log_event("approval_timeout", {
                "request_id": request.id,
                "action_type": action_type,
                "timeout_seconds": timeout,
            })

        # Get final status
        final_request = self._pending_requests.pop(request.id, request)
        self._request_events.pop(request.id, None)

        # Add to history
        self._add_to_history(final_request)

        return ApprovalResult(
            request_id=final_request.id,
            approved=final_request.status == ApprovalStatus.APPROVED,
            status=final_request.status,
            reason=final_request.reason,
            reviewed_by=final_request.reviewed_by,
        )

    def approve(
        self,
        request_id: str,
        reviewer: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Approve a pending request.

        Args:
            request_id: ID of the request
            reviewer: ID of the reviewer
            reason: Optional reason for approval

        Returns:
            True if successful
        """
        if request_id not in self._pending_requests:
            return False

        request = self._pending_requests[request_id]
        request.status = ApprovalStatus.APPROVED
        request.reviewed_by = reviewer
        request.reviewed_at = datetime.now()
        request.reason = reason

        self.approved_count += 1

        log_event("approval_granted", {
            "request_id": request_id,
            "action_type": request.action_type,
            "reviewer": reviewer,
            "reason": reason,
        })

        # Signal waiting coroutine
        if request_id in self._request_events:
            self._request_events[request_id].set()

        return True

    def reject(
        self,
        request_id: str,
        reviewer: str,
        reason: str
    ) -> bool:
        """
        Reject a pending request.

        Args:
            request_id: ID of the request
            reviewer: ID of the reviewer
            reason: Reason for rejection

        Returns:
            True if successful
        """
        if request_id not in self._pending_requests:
            return False

        request = self._pending_requests[request_id]
        request.status = ApprovalStatus.REJECTED
        request.reviewed_by = reviewer
        request.reviewed_at = datetime.now()
        request.reason = reason

        self.rejected_count += 1

        log_event("approval_rejected", {
            "request_id": request_id,
            "action_type": request.action_type,
            "reviewer": reviewer,
            "reason": reason,
        })

        # Signal waiting coroutine
        if request_id in self._request_events:
            self._request_events[request_id].set()

        return True

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests."""
        return list(self._pending_requests.values())

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific request by ID."""
        return self._pending_requests.get(request_id)

    def _add_to_history(self, request: ApprovalRequest) -> None:
        """Add request to history with bounded size."""
        self._history.append(request)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_history(self, limit: int = 100) -> List[ApprovalRequest]:
        """Get recent approval history."""
        return self._history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get approval statistics."""
        return {
            "total_requests": self.total_requests,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "timeout_count": self.timeout_count,
            "pending_count": len(self._pending_requests),
            "approval_rate": self.approved_count / max(self.total_requests, 1),
        }


# ============================================================================
# Decorator for requiring approval
# ============================================================================

# Global approval manager
_default_manager: Optional[ApprovalManager] = None


def get_default_manager() -> ApprovalManager:
    """Get or create the default approval manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ApprovalManager()
    return _default_manager


def set_default_manager(manager: ApprovalManager) -> None:
    """Set the default approval manager."""
    global _default_manager
    _default_manager = manager


def require_approval(
    risk_level: str = "high",
    action_type: Optional[str] = None,
    description: Optional[str] = None,
):
    """
    Decorator to require approval before executing a function.

    Args:
        risk_level: Risk level ("low", "medium", "high", "critical")
        action_type: Override action type (defaults to function name)
        description: Description template (can use {arg} placeholders)

    Usage:
        @require_approval(risk_level="high")
        async def delete_user(user_id: str):
            pass

        @require_approval(
            risk_level="critical",
            description="Delete all records for user {user_id}"
        )
        async def purge_user_data(user_id: str):
            pass
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_default_manager()

            # Determine action type
            func_action_type = action_type or func.__name__

            # Build description
            if description:
                try:
                    func_description = description.format(**kwargs)
                except KeyError:
                    func_description = description
            else:
                func_description = f"Execute {func_action_type}"

            # Check if approval required
            if manager.requires_approval(func_action_type, kwargs):
                result = await manager.request_approval(
                    action_type=func_action_type,
                    action_params=kwargs,
                    description=func_description,
                    requester="decorator",
                )

                if not result.approved:
                    raise ApprovalRequired(
                        ApprovalRequest(
                            id=result.request_id,
                            action_type=func_action_type,
                            action_params=kwargs,
                            description=func_description,
                            risk_level=RiskLevel(risk_level),
                            requester="decorator",
                            created_at=datetime.now(),
                            status=result.status,
                            reason=result.reason,
                        )
                    )

            return await func(*args, **kwargs)

        return wrapper
    return decorator
