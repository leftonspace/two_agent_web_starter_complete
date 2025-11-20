"""
PHASE 4.3: Workflow Enforcement Module (R6)

Provides strict enforcement of workflow step failures to prevent shipping
code that fails linting, tests, or compliance checks.

Enforcement Levels:
- strict: Workflow failures abort iteration and force retry (blocks file writes)
- warn: Log warnings but continue (default behavior)
- off: No enforcement

Usage:
    enforcer = WorkflowEnforcer(enforcement_level="strict")

    # Check if workflow failures should block
    workflow_result = run_workflow(...)
    should_block, reason = enforcer.check_workflow_result(workflow_result)

    if should_block:
        print(f"Blocking: {reason}")
        # Abort iteration, don't write files
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EnforcementLevel(Enum):
    """Workflow enforcement levels."""

    STRICT = "strict"  # Block execution on failures
    WARN = "warn"  # Log warnings but continue
    OFF = "off"  # No enforcement


class WorkflowEnforcer:
    """
    Enforces workflow step completion based on configuration.

    In strict mode, workflow failures block file writes and force iteration retry.
    """

    def __init__(self, enforcement_level: str = "warn"):
        """
        Initialize workflow enforcer.

        Args:
            enforcement_level: "strict", "warn", or "off"
        """
        try:
            self.level = EnforcementLevel(enforcement_level)
        except ValueError:
            print(f"[WorkflowEnforcer] Invalid enforcement level: {enforcement_level}, using 'warn'")
            self.level = EnforcementLevel.WARN

        self.violations: List[Dict[str, Any]] = []

    def check_workflow_result(
        self, workflow_result: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if workflow result should block execution.

        Args:
            workflow_result: Result from workflow.run()

        Returns:
            Tuple of (should_block, reason)
            - should_block: True if execution should be blocked
            - reason: Human-readable explanation
        """
        if self.level == EnforcementLevel.OFF:
            return (False, None)

        has_failures = workflow_result.get("has_failures", False)
        steps_failed = workflow_result.get("steps_failed", [])

        if not has_failures and not steps_failed:
            return (False, None)

        # Build reason message
        workflow_name = workflow_result.get("workflow_name", "Unknown")
        failure_count = len(steps_failed)

        if steps_failed:
            failed_steps = [step.get("step", "unknown") for step in steps_failed]
            reason = (
                f"Workflow '{workflow_name}' has {failure_count} failed step(s): "
                f"{', '.join(failed_steps)}"
            )
        else:
            reason = f"Workflow '{workflow_name}' reported failures"

        # Record violation
        self.violations.append({
            "workflow": workflow_name,
            "failure_count": failure_count,
            "failed_steps": steps_failed,
            "reason": reason,
        })

        # In strict mode, block execution
        if self.level == EnforcementLevel.STRICT:
            return (True, reason)

        # In warn mode, log but don't block
        print(f"[WorkflowEnforcer] WARNING: {reason}")
        return (False, None)

    def check_safety_result(
        self, safety_result: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if safety check result should block execution.

        Args:
            safety_result: Result from run_safety_checks()

        Returns:
            Tuple of (should_block, reason)
        """
        if self.level == EnforcementLevel.OFF:
            return (False, None)

        summary_status = safety_result.get("summary_status") or safety_result.get("status", "passed")

        if summary_status != "failed":
            return (False, None)

        # Count errors
        static_issues = safety_result.get("static_issues", [])
        dep_issues = safety_result.get("dependency_issues", [])
        error_count = sum(1 for i in static_issues if i.get("severity") == "error")
        error_count += sum(1 for i in dep_issues if i.get("severity") == "error")

        reason = f"Safety checks failed with {error_count} error(s)"

        # Record violation
        self.violations.append({
            "type": "safety_check",
            "error_count": error_count,
            "reason": reason,
        })

        # In strict mode, block execution
        if self.level == EnforcementLevel.STRICT:
            return (True, reason)

        # In warn mode, log but don't block
        print(f"[WorkflowEnforcer] WARNING: {reason}")
        return (False, None)

    def reset_violations(self) -> None:
        """Clear violation history."""
        self.violations = []

    def get_violation_summary(self) -> Dict[str, Any]:
        """
        Get summary of workflow violations.

        Returns:
            Dict with violation counts and details
        """
        return {
            "enforcement_level": self.level.value,
            "violation_count": len(self.violations),
            "violations": self.violations,
        }


def should_block_file_writes(
    workflow_results: List[Dict[str, Any]],
    enforcement_level: str = "warn",
) -> Tuple[bool, List[str]]:
    """
    Determine if file writes should be blocked based on workflow results.

    Convenience function for orchestrator integration.

    Args:
        workflow_results: List of workflow results
        enforcement_level: "strict", "warn", or "off"

    Returns:
        Tuple of (should_block, reasons)
        - should_block: True if writes should be blocked
        - reasons: List of blocking reasons
    """
    enforcer = WorkflowEnforcer(enforcement_level)
    reasons = []

    for result in workflow_results:
        should_block, reason = enforcer.check_workflow_result(result)
        if should_block and reason:
            reasons.append(reason)

    return (len(reasons) > 0, reasons)
