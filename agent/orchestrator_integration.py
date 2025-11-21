"""
Orchestrator Integration for Approval Workflows

This module provides integration between the orchestrator and the approval workflow engine,
enabling human-in-the-loop pauses during mission execution.

Usage:
    from orchestrator_integration import request_approval, wait_for_approval

    # Request approval during mission
    approval_request = request_approval(
        mission_id="mission_123",
        workflow_type=("hr", "offer_letter"),
        payload={"candidate_name": "Jane Doe", "salary": 150000}
    )

    # Wait for approval (blocks until approved/rejected)
    is_approved = wait_for_approval(approval_request.request_id)

Author: AI Agent System
Created: Phase 3.1 - Approval Workflows
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
from approval_engine import (
    ApprovalEngine,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalWorkflow
)

logger = logging.getLogger(__name__)


class ApprovalRequiredException(Exception):
    """Raised when an approval is required but not granted"""
    pass


class OrchestrationPauseManager:
    """
    Manages orchestrator pause/resume for approval workflows.

    This class provides utilities for:
    - Requesting approvals during mission execution
    - Pausing orchestrator until approval granted
    - Resuming orchestrator after approval
    - Handling approval timeouts and rejections
    """

    def __init__(self, approval_engine: Optional[ApprovalEngine] = None):
        self.engine = approval_engine or ApprovalEngine()
        logger.info("OrchestrationPauseManager initialized")

    def request_approval(
        self,
        mission_id: str,
        workflow_type: Tuple[str, str],  # (domain, task_type)
        payload: Dict[str, Any],
        created_by: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Request approval for a mission task.

        This creates an approval request and returns it. The calling code
        should then call wait_for_approval() to pause until approved.

        Args:
            mission_id: ID of the orchestrator mission
            workflow_type: Tuple of (domain, task_type) to identify workflow
            payload: Data to be approved
            created_by: User ID who created the request

        Returns:
            ApprovalRequest object

        Raises:
            ValueError: If workflow not found
        """
        domain, task_type = workflow_type

        # Get workflow
        workflow = self.engine.get_workflow_by_type(domain, task_type)
        if not workflow:
            raise ValueError(f"No workflow found for {domain}/{task_type}")

        # Create approval request
        request = self.engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id=mission_id,
            payload=payload,
            created_by=created_by
        )

        logger.info(f"Approval requested for mission {mission_id}: {request.request_id}")
        logger.info(f"  Workflow: {workflow.workflow_name}")
        logger.info(f"  Status: {request.status.value}")

        return request

    def wait_for_approval(
        self,
        request_id: str,
        poll_interval: int = 5,
        timeout: Optional[int] = None
    ) -> bool:
        """
        Wait for an approval request to be approved or rejected.

        This blocks the orchestrator until the approval is granted or denied.

        Args:
            request_id: ID of the approval request
            poll_interval: Seconds between status checks (default: 5)
            timeout: Maximum seconds to wait (default: None = wait forever)

        Returns:
            True if approved, False if rejected

        Raises:
            ApprovalRequiredException: If approval rejected or timed out
            ValueError: If request not found
        """
        logger.info(f"Waiting for approval: {request_id}")

        start_time = time.time()
        elapsed = 0

        while True:
            # Get current request status
            request = self.engine.get_request(request_id)

            if not request:
                raise ValueError(f"Approval request {request_id} not found")

            # Check status
            if request.status == ApprovalStatus.APPROVED:
                logger.info(f"Approval {request_id} APPROVED after {elapsed:.1f}s")
                return True

            elif request.status == ApprovalStatus.REJECTED:
                logger.warning(f"Approval {request_id} REJECTED after {elapsed:.1f}s")
                raise ApprovalRequiredException(f"Approval {request_id} was rejected")

            elif request.status == ApprovalStatus.TIMEOUT:
                logger.error(f"Approval {request_id} TIMED OUT after {elapsed:.1f}s")
                raise ApprovalRequiredException(f"Approval {request_id} timed out")

            elif request.status == ApprovalStatus.CANCELLED:
                logger.warning(f"Approval {request_id} CANCELLED after {elapsed:.1f}s")
                raise ApprovalRequiredException(f"Approval {request_id} was cancelled")

            # Check timeout
            if timeout and elapsed >= timeout:
                logger.error(f"Wait timeout exceeded for approval {request_id}")
                raise ApprovalRequiredException(f"Approval {request_id} wait timeout exceeded")

            # Still pending, wait and check again
            logger.debug(f"Approval {request_id} still pending... ({elapsed:.1f}s)")
            time.sleep(poll_interval)
            elapsed = time.time() - start_time

    def check_approval_status(self, request_id: str) -> ApprovalStatus:
        """
        Check the status of an approval request without blocking.

        Args:
            request_id: ID of the approval request

        Returns:
            ApprovalStatus enum

        Raises:
            ValueError: If request not found
        """
        request = self.engine.get_request(request_id)

        if not request:
            raise ValueError(f"Approval request {request_id} not found")

        return request.status

    def cancel_approval(self, request_id: str) -> bool:
        """
        Cancel a pending approval request.

        Args:
            request_id: ID of the approval request

        Returns:
            True if cancelled successfully
        """
        try:
            request = self.engine.get_request(request_id)

            if not request:
                logger.error(f"Cannot cancel: request {request_id} not found")
                return False

            if request.status != ApprovalStatus.PENDING:
                logger.warning(f"Cannot cancel: request {request_id} is not pending (status: {request.status.value})")
                return False

            # Update status
            request.status = ApprovalStatus.CANCELLED
            request.updated_at = time.time()
            self.engine._save_request(request)

            logger.info(f"Approval {request_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel approval {request_id}: {e}")
            return False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global pause manager instance
_pause_manager = None


def get_pause_manager() -> OrchestrationPauseManager:
    """Get the global pause manager instance"""
    global _pause_manager
    if _pause_manager is None:
        _pause_manager = OrchestrationPauseManager()
    return _pause_manager


def request_approval(
    mission_id: str,
    workflow_type: Tuple[str, str],
    payload: Dict[str, Any],
    created_by: Optional[str] = None
) -> ApprovalRequest:
    """
    Convenience function to request approval.

    See OrchestrationPauseManager.request_approval() for details.
    """
    manager = get_pause_manager()
    return manager.request_approval(mission_id, workflow_type, payload, created_by)


def wait_for_approval(
    request_id: str,
    poll_interval: int = 5,
    timeout: Optional[int] = None
) -> bool:
    """
    Convenience function to wait for approval.

    See OrchestrationPauseManager.wait_for_approval() for details.
    """
    manager = get_pause_manager()
    return manager.wait_for_approval(request_id, poll_interval, timeout)


def check_approval_status(request_id: str) -> ApprovalStatus:
    """
    Convenience function to check approval status.

    See OrchestrationPauseManager.check_approval_status() for details.
    """
    manager = get_pause_manager()
    return manager.check_approval_status(request_id)


# ============================================================================
# ORCHESTRATOR HOOKS
# ============================================================================

def approval_checkpoint(
    mission_id: str,
    checkpoint_name: str,
    approval_type: Tuple[str, str],
    payload: Dict[str, Any],
    auto_approve: bool = False,
    created_by: Optional[str] = None
) -> bool:
    """
    Orchestrator checkpoint that requires approval before proceeding.

    This is designed to be called from within the orchestrator's execution loop
    to pause for human approval.

    Args:
        mission_id: ID of the current mission
        checkpoint_name: Human-readable name for this checkpoint
        approval_type: Tuple of (domain, task_type)
        payload: Data to be approved
        auto_approve: If True, skip approval for testing (default: False)
        created_by: User ID who initiated the mission

    Returns:
        True if approved, False if should abort mission

    Example:
        # In orchestrator code:
        if not approval_checkpoint(
            mission_id=run_id,
            checkpoint_name="Offer Letter Approval",
            approval_type=("hr", "offer_letter"),
            payload={"candidate_name": "Jane Doe", "salary": 150000}
        ):
            logger.error("Approval rejected, aborting mission")
            return False
    """
    logger.info(f"Checkpoint: {checkpoint_name} for mission {mission_id}")

    if auto_approve:
        logger.warning(f"Auto-approving checkpoint: {checkpoint_name}")
        return True

    try:
        # Request approval
        request = request_approval(
            mission_id=mission_id,
            workflow_type=approval_type,
            payload=payload,
            created_by=created_by
        )

        logger.info(f"Orchestrator paused at checkpoint: {checkpoint_name}")
        logger.info(f"Approval request: {request.request_id}")
        logger.info(f"View approvals at: http://localhost:8000/approvals")

        # Wait for approval
        approved = wait_for_approval(request.request_id)

        if approved:
            logger.info(f"Checkpoint {checkpoint_name} approved, resuming...")
            return True
        else:
            logger.warning(f"Checkpoint {checkpoint_name} rejected, aborting...")
            return False

    except ApprovalRequiredException as e:
        logger.error(f"Approval checkpoint failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error at approval checkpoint: {e}", exc_info=True)
        return False


# ============================================================================
# TESTING UTILITIES
# ============================================================================

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("Testing Orchestrator Integration")
    print("=" * 80)

    # Create test approval
    print("\n1. Creating test approval request...")
    request = request_approval(
        mission_id="test_mission_456",
        workflow_type=("hr", "offer_letter"),
        payload={
            "candidate_name": "John Smith",
            "position": "Senior Engineer",
            "salary": 120000,
            "level": "senior"
        },
        created_by="orchestrator_test"
    )

    print(f"   Created: {request.request_id}")
    print(f"   Status: {request.status.value}")
    print(f"   Current steps: {request.current_step_ids}")

    # Check status (non-blocking)
    print("\n2. Checking status (non-blocking)...")
    status = check_approval_status(request.request_id)
    print(f"   Status: {status.value}")

    print("\n3. To approve this request:")
    print(f"   - Visit http://localhost:8000/approvals")
    print(f"   - Or use the API: POST /api/approvals/{request.request_id}/approve")

    print("\n4. Waiting for approval (blocking)...")
    print("   This will wait until approved/rejected")
    print("   Press Ctrl+C to cancel")

    try:
        approved = wait_for_approval(request.request_id, poll_interval=2, timeout=60)
        print(f"\n   Result: {'APPROVED' if approved else 'REJECTED'}")
    except KeyboardInterrupt:
        print("\n   Cancelled by user")
    except ApprovalRequiredException as e:
        print(f"\n   Approval failed: {e}")
    except Exception as e:
        print(f"\n   Error: {e}")
