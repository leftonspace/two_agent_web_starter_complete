"""
Integration Tests: Human Approval Workflows

Tests the approval workflow engine including multi-step approvals,
conditional branching, timeouts, and escalations.
"""

import pytest
import asyncio
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def approval_engine(tmp_path):
    """Create approval engine with temp database"""
    from approval_engine import ApprovalEngine

    db_path = str(tmp_path / "test_approvals.db")
    return ApprovalEngine(db_path=db_path)


@pytest.fixture
def sample_workflow():
    """Create a sample approval workflow"""
    from approval_engine import ApprovalWorkflow, ApprovalStep

    return ApprovalWorkflow(
        workflow_id="test_workflow_v1",
        domain="test",
        task_type="sample_approval",
        workflow_name="Test Approval Workflow",
        steps=[
            ApprovalStep(
                step_id="manager_approval",
                approver_role="manager",
                timeout_hours=24,
                step_name="Manager Approval"
            ),
            ApprovalStep(
                step_id="director_approval",
                approver_role="director",
                timeout_hours=48,
                step_name="Director Approval"
            )
        ]
    )


class TestWorkflowRegistration:
    """Test workflow registration and retrieval"""

    def test_register_workflow(self, approval_engine, sample_workflow):
        """Should register a workflow successfully"""
        result = approval_engine.register_workflow(sample_workflow)

        assert result is True

    def test_get_workflow_by_id(self, approval_engine, sample_workflow):
        """Should retrieve workflow by ID"""
        approval_engine.register_workflow(sample_workflow)

        workflow = approval_engine.get_workflow(sample_workflow.workflow_id)

        assert workflow is not None
        assert workflow.workflow_id == sample_workflow.workflow_id
        assert len(workflow.steps) == 2

    def test_get_workflow_by_type(self, approval_engine, sample_workflow):
        """Should retrieve workflow by domain and task type"""
        approval_engine.register_workflow(sample_workflow)

        workflow = approval_engine.get_workflow_by_type(
            domain="test",
            task_type="sample_approval"
        )

        assert workflow is not None
        assert workflow.workflow_id == sample_workflow.workflow_id

    def test_duplicate_step_ids_rejected(self, approval_engine):
        """Should reject workflows with duplicate step IDs"""
        from approval_engine import ApprovalWorkflow, ApprovalStep

        with pytest.raises(ValueError) as exc:
            ApprovalWorkflow(
                workflow_id="invalid",
                domain="test",
                task_type="invalid",
                steps=[
                    ApprovalStep(step_id="same", approver_role="role1"),
                    ApprovalStep(step_id="same", approver_role="role2"),
                ]
            )

        assert "Duplicate" in str(exc.value)


class TestApprovalRequests:
    """Test approval request creation and processing"""

    def test_create_approval_request(self, approval_engine, sample_workflow):
        """Should create approval request"""
        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"},
            created_by="user_1"
        )

        assert request is not None
        assert request.request_id is not None
        assert request.status.value == "pending"
        assert len(request.current_step_ids) > 0

    def test_request_starts_at_first_step(self, approval_engine, sample_workflow):
        """New request should start at first step"""
        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"}
        )

        assert request.current_step_index == 0
        assert "manager_approval" in request.current_step_ids

    def test_get_request_by_id(self, approval_engine, sample_workflow):
        """Should retrieve request by ID"""
        approval_engine.register_workflow(sample_workflow)

        created = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"test": "data"}
        )

        retrieved = approval_engine.get_request(created.request_id)

        assert retrieved is not None
        assert retrieved.request_id == created.request_id
        assert retrieved.payload == {"test": "data"}


class TestApprovalDecisions:
    """Test approval decision processing"""

    def test_approve_advances_to_next_step(self, approval_engine, sample_workflow):
        """Approval should advance to next step"""
        from approval_engine import DecisionType

        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"}
        )

        # Process first approval
        updated = approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_1",
            decision=DecisionType.APPROVE,
            approver_role="manager"
        )

        assert "director_approval" in updated.current_step_ids

    def test_final_approval_completes_request(self, approval_engine, sample_workflow):
        """Final approval should complete the request"""
        from approval_engine import DecisionType, ApprovalStatus

        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"}
        )

        # First approval
        approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_1",
            decision=DecisionType.APPROVE,
            approver_role="manager"
        )

        # Second (final) approval
        final = approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="director_1",
            decision=DecisionType.APPROVE,
            approver_role="director"
        )

        assert final.status == ApprovalStatus.APPROVED
        assert final.completed_at is not None

    def test_rejection_terminates_request(self, approval_engine, sample_workflow):
        """Rejection should terminate the request"""
        from approval_engine import DecisionType, ApprovalStatus

        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"}
        )

        updated = approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_1",
            decision=DecisionType.REJECT,
            comments="Not approved",
            approver_role="manager"
        )

        assert updated.status == ApprovalStatus.REJECTED

    def test_escalation_changes_status(self, approval_engine, sample_workflow):
        """Escalation should change status"""
        from approval_engine import DecisionType, ApprovalStatus

        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"}
        )

        updated = approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_1",
            decision=DecisionType.ESCALATE,
            comments="Need higher approval",
            approver_role="manager"
        )

        assert updated.status == ApprovalStatus.ESCALATED

    def test_decisions_are_recorded(self, approval_engine, sample_workflow):
        """Decisions should be recorded in history"""
        from approval_engine import DecisionType

        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_123",
            payload={"item": "test"}
        )

        approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_1",
            decision=DecisionType.APPROVE,
            comments="Looks good",
            approver_role="manager"
        )

        retrieved = approval_engine.get_request(request.request_id)

        assert len(retrieved.decisions) == 1
        assert retrieved.decisions[0].comments == "Looks good"


class TestConditionalSteps:
    """Test conditional step execution"""

    def test_conditional_step_executed_when_true(self, approval_engine):
        """Should execute step when condition is true"""
        from approval_engine import ApprovalWorkflow, ApprovalStep

        workflow = ApprovalWorkflow(
            workflow_id="conditional_test",
            domain="test",
            task_type="conditional",
            steps=[
                ApprovalStep(
                    step_id="high_value",
                    approver_role="executive",
                    condition="payload.get('amount', 0) > 10000"
                )
            ]
        )

        approval_engine.register_workflow(workflow)

        # High value request
        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="mission_high",
            payload={"amount": 50000}
        )

        assert "high_value" in request.current_step_ids

    def test_conditional_step_skipped_when_false(self, approval_engine):
        """Should skip step when condition is false"""
        from approval_engine import ApprovalWorkflow, ApprovalStep, ApprovalStatus

        workflow = ApprovalWorkflow(
            workflow_id="conditional_skip",
            domain="test",
            task_type="conditional_skip",
            steps=[
                ApprovalStep(
                    step_id="high_value",
                    approver_role="executive",
                    condition="payload.get('amount', 0) > 10000"
                )
            ]
        )

        approval_engine.register_workflow(workflow)

        # Low value request - step should be skipped
        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="mission_low",
            payload={"amount": 5000}
        )

        # No steps active means auto-approved (all conditional steps skipped)
        assert len(request.current_step_ids) == 0 or request.status == ApprovalStatus.APPROVED


class TestAutoApproval:
    """Test automatic approval conditions"""

    def test_auto_approve_when_condition_met(self, approval_engine):
        """Should auto-approve when conditions are met"""
        from approval_engine import ApprovalWorkflow, ApprovalStep, ApprovalStatus

        workflow = ApprovalWorkflow(
            workflow_id="auto_approve_test",
            domain="test",
            task_type="auto_approve",
            steps=[
                ApprovalStep(
                    step_id="manager",
                    approver_role="manager"
                )
            ],
            auto_approve_conditions="payload.get('amount', 0) < 100"
        )

        approval_engine.register_workflow(workflow)

        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="mission_small",
            payload={"amount": 50}
        )

        assert request.status == ApprovalStatus.APPROVED
        assert len(request.decisions) > 0
        assert request.decisions[0].approver_user_id == "system"

    def test_no_auto_approve_when_condition_not_met(self, approval_engine):
        """Should not auto-approve when conditions not met"""
        from approval_engine import ApprovalWorkflow, ApprovalStep, ApprovalStatus

        workflow = ApprovalWorkflow(
            workflow_id="no_auto_approve",
            domain="test",
            task_type="no_auto",
            steps=[
                ApprovalStep(
                    step_id="manager",
                    approver_role="manager"
                )
            ],
            auto_approve_conditions="payload.get('amount', 0) < 100"
        )

        approval_engine.register_workflow(workflow)

        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="mission_large",
            payload={"amount": 500}
        )

        assert request.status == ApprovalStatus.PENDING


class TestPendingApprovals:
    """Test pending approval queries"""

    def test_get_pending_by_role(self, approval_engine, sample_workflow):
        """Should get pending approvals by role"""
        approval_engine.register_workflow(sample_workflow)

        approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_1",
            payload={"item": "test1"}
        )

        pending = approval_engine.get_pending_approvals(role="manager")

        assert len(pending) > 0
        assert pending[0]["domain"] == "test"

    def test_get_pending_by_domain(self, approval_engine, sample_workflow):
        """Should filter pending by domain"""
        approval_engine.register_workflow(sample_workflow)

        approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_1",
            payload={"item": "test1"}
        )

        pending = approval_engine.get_pending_approvals(domain="test")

        assert len(pending) > 0
        for item in pending:
            assert item["domain"] == "test"

    def test_pending_includes_timeout_info(self, approval_engine, sample_workflow):
        """Pending approvals should include timeout info"""
        approval_engine.register_workflow(sample_workflow)

        approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_1",
            payload={"item": "test1"}
        )

        pending = approval_engine.get_pending_approvals(role="manager")

        assert len(pending) > 0
        assert "hours_remaining" in pending[0]
        assert "is_overdue" in pending[0]


class TestStatistics:
    """Test approval statistics"""

    def test_get_statistics(self, approval_engine, sample_workflow):
        """Should return statistics"""
        from approval_engine import DecisionType

        approval_engine.register_workflow(sample_workflow)

        # Create multiple requests
        for i in range(3):
            request = approval_engine.create_approval_request(
                workflow_id=sample_workflow.workflow_id,
                mission_id=f"mission_{i}",
                payload={"item": f"test{i}"}
            )

            # Approve first one
            if i == 0:
                approval_engine.process_decision(
                    request_id=request.request_id,
                    approver_user_id="manager",
                    decision=DecisionType.APPROVE,
                    approver_role="manager"
                )
                approval_engine.process_decision(
                    request_id=request.request_id,
                    approver_user_id="director",
                    decision=DecisionType.APPROVE,
                    approver_role="director"
                )

        stats = approval_engine.get_statistics(domain="test")

        assert stats["total_requests"] >= 3
        assert stats["approved"] >= 1
        assert stats["pending"] >= 2


class TestRealWorldWorkflows:
    """Test real-world workflow scenarios"""

    def test_hr_offer_letter_workflow(self, approval_engine):
        """Test HR offer letter approval flow"""
        from approval_engine import create_hr_offer_letter_workflow, DecisionType

        workflow = create_hr_offer_letter_workflow()
        approval_engine.register_workflow(workflow)

        # Create offer request
        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="offer_001",
            payload={
                "candidate_name": "John Doe",
                "position": "Engineer",
                "salary": 120000,
                "level": "senior"
            }
        )

        # Should start with hiring manager
        assert "hiring_manager" in request.current_step_ids

        # Hiring manager approves
        request = approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="hm_1",
            decision=DecisionType.APPROVE,
            approver_role="hr_hiring_manager"
        )

        # Since salary > 100k, director step should be active
        assert "director" in request.current_step_ids

    def test_finance_expense_workflow(self, approval_engine):
        """Test finance expense approval flow"""
        from approval_engine import create_finance_expense_workflow, DecisionType, ApprovalStatus

        workflow = create_finance_expense_workflow()
        approval_engine.register_workflow(workflow)

        # Small expense - should auto-approve
        small_request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="expense_small",
            payload={"amount": 50, "description": "Coffee"}
        )

        assert small_request.status == ApprovalStatus.APPROVED

    def test_legal_contract_workflow(self, approval_engine):
        """Test legal contract review flow"""
        from approval_engine import create_legal_contract_workflow, DecisionType

        workflow = create_legal_contract_workflow()
        approval_engine.register_workflow(workflow)

        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="contract_001",
            payload={
                "contract_name": "Vendor Agreement",
                "contract_value": 75000
            }
        )

        # Should start with contract manager
        assert "contract_manager" in request.current_step_ids


class TestParallelApprovals:
    """Test parallel approval steps"""

    def test_parallel_steps_all_active(self, approval_engine):
        """Parallel steps should all be active together"""
        from approval_engine import ApprovalWorkflow, ApprovalStep

        workflow = ApprovalWorkflow(
            workflow_id="parallel_test",
            domain="test",
            task_type="parallel",
            steps=[
                ApprovalStep(
                    step_id="legal",
                    approver_role="legal",
                    parallel=True
                ),
                ApprovalStep(
                    step_id="finance",
                    approver_role="finance",
                    parallel=True
                ),
                ApprovalStep(
                    step_id="final",
                    approver_role="executive",
                    parallel=False
                )
            ]
        )

        approval_engine.register_workflow(workflow)

        request = approval_engine.create_approval_request(
            workflow_id=workflow.workflow_id,
            mission_id="mission_parallel",
            payload={"item": "test"}
        )

        # Both parallel steps should be active
        assert "legal" in request.current_step_ids
        assert "finance" in request.current_step_ids


class TestApprovalValidation:
    """Test approval validation"""

    def test_cannot_approve_completed_request(self, approval_engine, sample_workflow):
        """Cannot approve already completed request"""
        from approval_engine import DecisionType, ApprovalStatus

        approval_engine.register_workflow(sample_workflow)

        request = approval_engine.create_approval_request(
            workflow_id=sample_workflow.workflow_id,
            mission_id="mission_1",
            payload={"item": "test"}
        )

        # Complete the request
        approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_1",
            decision=DecisionType.APPROVE,
            approver_role="manager"
        )
        approval_engine.process_decision(
            request_id=request.request_id,
            approver_user_id="director_1",
            decision=DecisionType.APPROVE,
            approver_role="director"
        )

        # Try to approve again
        with pytest.raises(ValueError) as exc:
            approval_engine.process_decision(
                request_id=request.request_id,
                approver_user_id="other",
                decision=DecisionType.APPROVE,
                approver_role="manager"
            )

        assert "not pending" in str(exc.value)

    def test_request_not_found_raises_error(self, approval_engine):
        """Should raise error for non-existent request"""
        from approval_engine import DecisionType

        with pytest.raises(ValueError) as exc:
            approval_engine.process_decision(
                request_id="non_existent",
                approver_user_id="user",
                decision=DecisionType.APPROVE
            )

        assert "not found" in str(exc.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
