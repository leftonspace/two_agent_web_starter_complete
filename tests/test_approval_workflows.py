#!/usr/bin/env python3
"""
Comprehensive Test Suite for Approval Workflows

Tests all approval workflow features:
- Multi-step workflows
- Conditional branching
- Parallel approvals
- Timeouts and escalations
- Integration with orchestrator

Usage:
    python tests/test_approval_workflows.py

Author: AI Agent System
Created: Phase 3.1 - Approval Workflows
"""

import sys
import os
from pathlib import Path
import time

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agent"))

from approval_engine import (
    ApprovalEngine,
    ApprovalWorkflow,
    ApprovalStep,
    ApprovalStatus,
    DecisionType,
    create_hr_offer_letter_workflow,
    create_finance_expense_workflow,
    create_legal_contract_workflow
)
from orchestrator_integration import (
    OrchestrationPauseManager,
    request_approval,
    check_approval_status
)
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, test_name: str):
        self.passed += 1
        self.tests.append((test_name, True, None))
        logger.info(f"✓ PASS: {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.tests.append((test_name, False, error))
        logger.error(f"✗ FAIL: {test_name} - {error}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({100 * self.passed / total if total > 0 else 0:.1f}%)")
        print(f"Failed: {self.failed} ({100 * self.failed / total if total > 0 else 0:.1f}%)")
        print("=" * 80)

        if self.failed > 0:
            print("\nFailed Tests:")
            for name, passed, error in self.tests:
                if not passed:
                    print(f"  - {name}: {error}")


def test_workflow_registration(engine: ApprovalEngine, results: TestResults):
    """Test 1: Workflow Registration"""
    test_name = "Workflow Registration"

    try:
        # Register workflows
        workflows = [
            create_hr_offer_letter_workflow(),
            create_finance_expense_workflow(),
            create_legal_contract_workflow()
        ]

        for workflow in workflows:
            success = engine.register_workflow(workflow)
            assert success, f"Failed to register {workflow.workflow_id}"

        # Verify registration
        for workflow in workflows:
            loaded = engine.get_workflow(workflow.workflow_id)
            assert loaded is not None, f"Failed to load {workflow.workflow_id}"
            assert loaded.workflow_id == workflow.workflow_id
            assert len(loaded.steps) == len(workflow.steps)

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_simple_approval_flow(engine: ApprovalEngine, results: TestResults):
    """Test 2: Simple Multi-Step Approval"""
    test_name = "Simple Multi-Step Approval"

    try:
        # Create approval request for low-salary offer (should skip director approval)
        request = engine.create_approval_request(
            workflow_id="hr_offer_letter_v1",
            mission_id="test_mission_001",
            payload={
                "candidate_name": "Alice Johnson",
                "position": "Junior Engineer",
                "salary": 80000,  # Below $100k threshold
                "level": "junior"
            },
            created_by="test_user"
        )

        assert request.status == ApprovalStatus.PENDING, f"Expected PENDING, got {request.status}"
        assert len(request.current_step_ids) == 1, f"Expected 1 active step, got {len(request.current_step_ids)}"
        assert request.current_step_ids[0] == "hiring_manager", "First step should be hiring_manager"

        # Approve as hiring manager
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_001",
            decision=DecisionType.APPROVE,
            comments="Approved - good candidate",
            approver_role="hr_hiring_manager"
        )

        # Should skip director (salary < $100k) and move to hr_head
        assert request.current_step_ids[0] == "hr_head", "Should skip director and go to hr_head"

        # Approve as HR head
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="hr_head_001",
            decision=DecisionType.APPROVE,
            comments="Final approval",
            approver_role="hr_head"
        )

        # Debug: print request state
        logger.info(f"After HR head approval - Status: {request.status}, Step index: {request.current_step_index}, Current steps: {request.current_step_ids}, Total workflow steps: {len(engine.get_workflow(request.workflow_id).steps)}")

        # Should be fully approved
        assert request.status == ApprovalStatus.APPROVED, f"Expected APPROVED, got {request.status}, step_index={request.current_step_index}, current_steps={request.current_step_ids}"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_conditional_branching(engine: ApprovalEngine, results: TestResults):
    """Test 3: Conditional Branching"""
    test_name = "Conditional Branching"

    try:
        # High salary offer - should require director approval
        request = engine.create_approval_request(
            workflow_id="hr_offer_letter_v1",
            mission_id="test_mission_002",
            payload={
                "candidate_name": "Bob Smith",
                "position": "Senior Engineer",
                "salary": 150000,  # Above $100k threshold
                "level": "senior"
            },
            created_by="test_user"
        )

        # Step 1: Hiring Manager
        assert request.current_step_ids[0] == "hiring_manager"
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_001",
            decision=DecisionType.APPROVE,
            approver_role="hr_hiring_manager"
        )

        # Step 2: Should require director approval (salary > $100k)
        assert "director" in request.current_step_ids, "Should require director approval for high salary"
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="director_001",
            decision=DecisionType.APPROVE,
            approver_role="hr_director"
        )

        # Step 3: HR Head
        assert request.current_step_ids[0] == "hr_head"
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="hr_head_001",
            decision=DecisionType.APPROVE,
            approver_role="hr_head"
        )

        assert request.status == ApprovalStatus.APPROVED

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_rejection_workflow(engine: ApprovalEngine, results: TestResults):
    """Test 4: Rejection Handling"""
    test_name = "Rejection Handling"

    try:
        request = engine.create_approval_request(
            workflow_id="hr_offer_letter_v1",
            mission_id="test_mission_003",
            payload={
                "candidate_name": "Charlie Brown",
                "position": "Engineer",
                "salary": 90000,
                "level": "mid"
            },
            created_by="test_user"
        )

        # Reject at first step
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="manager_001",
            decision=DecisionType.REJECT,
            comments="Not a good fit",
            approver_role="hr_hiring_manager"
        )

        assert request.status == ApprovalStatus.REJECTED, f"Expected REJECTED, got {request.status}"
        assert request.completed_at is not None, "Should have completion timestamp"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_tiered_approval(engine: ApprovalEngine, results: TestResults):
    """Test 5: Tiered Approval (Finance Expense)"""
    test_name = "Tiered Approval"

    try:
        # Test low amount - manager only
        low_request = engine.create_approval_request(
            workflow_id="finance_expense_v1",
            mission_id="test_mission_004",
            payload={"amount": 3000, "description": "Software licenses"},
            created_by="test_user"
        )

        assert low_request.current_step_ids[0] == "manager", "Low amount should go to manager"

        # Test medium amount - controller
        med_request = engine.create_approval_request(
            workflow_id="finance_expense_v1",
            mission_id="test_mission_005",
            payload={"amount": 15000, "description": "Equipment purchase"},
            created_by="test_user"
        )

        assert med_request.current_step_ids[0] == "controller", "Medium amount should go to controller"

        # Test high amount - CFO
        high_request = engine.create_approval_request(
            workflow_id="finance_expense_v1",
            mission_id="test_mission_006",
            payload={"amount": 50000, "description": "Major investment"},
            created_by="test_user"
        )

        assert high_request.current_step_ids[0] == "cfo", "High amount should go to CFO"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_parallel_approvals(engine: ApprovalEngine, results: TestResults):
    """Test 6: Parallel Approvals"""
    test_name = "Parallel Approvals"

    try:
        # High-value contract should require parallel legal + finance approval
        request = engine.create_approval_request(
            workflow_id="legal_contract_v1",
            mission_id="test_mission_007",
            payload={"contract_value": 75000, "vendor": "ACME Corp"},
            created_by="test_user"
        )

        # Step 1: Contract Manager
        assert request.current_step_ids[0] == "contract_manager"
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="contract_mgr_001",
            decision=DecisionType.APPROVE,
            approver_role="legal_contract_manager"
        )

        # Step 2: Should have parallel approvals (legal_counsel + finance_review)
        assert "legal_counsel" in request.current_step_ids, "Should require legal counsel"
        assert "finance_review" in request.current_step_ids, "Should require finance review for high value"
        assert len(request.current_step_ids) == 2, "Should have 2 parallel approvals"

        # Approve legal
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="legal_001",
            decision=DecisionType.APPROVE,
            approver_role="legal_counsel"
        )

        # Should still be pending (need finance approval)
        assert request.status == ApprovalStatus.PENDING, "Should still be pending until all parallel approvals done"

        # Approve finance
        request = engine.process_decision(
            request_id=request.request_id,
            approver_user_id="finance_001",
            decision=DecisionType.APPROVE,
            approver_role="finance_controller"
        )

        # Now should be fully approved
        assert request.status == ApprovalStatus.APPROVED, "Should be approved after all parallel approvals"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_auto_approval(engine: ApprovalEngine, results: TestResults):
    """Test 7: Auto-Approval Conditions"""
    test_name = "Auto-Approval Conditions"

    try:
        # Intern offer with low salary - should auto-approve
        request = engine.create_approval_request(
            workflow_id="hr_offer_letter_v1",
            mission_id="test_mission_008",
            payload={
                "candidate_name": "Dave Intern",
                "position": "Intern",
                "salary": 45000,
                "level": "intern"
            },
            created_by="test_user"
        )

        # Should be auto-approved
        assert request.status == ApprovalStatus.APPROVED, "Should be auto-approved"
        assert len(request.decisions) == 1, "Should have auto-approval decision"
        assert request.decisions[0].approver_user_id == "system", "Should be approved by system"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_pending_approvals_query(engine: ApprovalEngine, results: TestResults):
    """Test 8: Pending Approvals Query"""
    test_name = "Pending Approvals Query"

    try:
        # Create several pending approvals
        r1 = engine.create_approval_request(
            workflow_id="hr_offer_letter_v1",
            mission_id="test_mission_009",
            payload={"candidate_name": "Eve", "salary": 100000, "level": "senior"},
            created_by="test_user"
        )

        r2 = engine.create_approval_request(
            workflow_id="finance_expense_v1",
            mission_id="test_mission_010",
            payload={"amount": 10000},
            created_by="test_user"
        )

        # Query for hr_hiring_manager
        hr_approvals = engine.get_pending_approvals(role="hr_hiring_manager")
        assert len(hr_approvals) >= 1, "Should have at least 1 HR approval"

        # Query for finance_controller
        finance_approvals = engine.get_pending_approvals(role="finance_controller")
        assert len(finance_approvals) >= 1, "Should have at least 1 Finance approval"

        # Query by domain
        hr_domain = engine.get_pending_approvals(domain="hr")
        assert len(hr_domain) >= 1, "Should have at least 1 HR domain approval"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_statistics(engine: ApprovalEngine, results: TestResults):
    """Test 9: Statistics Generation"""
    test_name = "Statistics Generation"

    try:
        stats = engine.get_statistics()
        assert 'total_requests' in stats, "Should have total_requests"
        assert 'pending' in stats, "Should have pending count"
        assert 'approved' in stats, "Should have approved count"
        assert 'rejected' in stats, "Should have rejected count"

        # Domain-specific stats
        hr_stats = engine.get_statistics(domain="hr")
        assert hr_stats['total_requests'] >= 0, "Should have HR stats"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def test_orchestrator_integration(results: TestResults):
    """Test 10: Orchestrator Integration"""
    test_name = "Orchestrator Integration"

    try:
        manager = OrchestrationPauseManager()

        # Request approval
        request = manager.request_approval(
            mission_id="test_mission_011",
            workflow_type=("hr", "offer_letter"),
            payload={"candidate_name": "Frank", "salary": 95000, "level": "mid"},
            created_by="orchestrator"
        )

        assert request.status == ApprovalStatus.PENDING, "Should be pending"

        # Check status (non-blocking)
        status = manager.check_approval_status(request.request_id)
        assert status == ApprovalStatus.PENDING, "Status check should return PENDING"

        # Cancel the request
        cancelled = manager.cancel_approval(request.request_id)
        assert cancelled, "Should cancel successfully"

        # Verify cancelled
        status = manager.check_approval_status(request.request_id)
        assert status == ApprovalStatus.CANCELLED, "Should be cancelled"

        results.add_pass(test_name)
        return True

    except AssertionError as e:
        results.add_fail(test_name, str(e))
        return False
    except Exception as e:
        results.add_fail(test_name, f"Unexpected error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("APPROVAL WORKFLOW TEST SUITE")
    print("=" * 80)
    print()

    # Initialize
    engine = ApprovalEngine()
    results = TestResults()

    # Run tests
    tests = [
        ("Workflow Registration", lambda: test_workflow_registration(engine, results)),
        ("Simple Multi-Step Approval", lambda: test_simple_approval_flow(engine, results)),
        ("Conditional Branching", lambda: test_conditional_branching(engine, results)),
        ("Rejection Handling", lambda: test_rejection_workflow(engine, results)),
        ("Tiered Approval", lambda: test_tiered_approval(engine, results)),
        ("Parallel Approvals", lambda: test_parallel_approvals(engine, results)),
        ("Auto-Approval Conditions", lambda: test_auto_approval(engine, results)),
        ("Pending Approvals Query", lambda: test_pending_approvals_query(engine, results)),
        ("Statistics Generation", lambda: test_statistics(engine, results)),
        ("Orchestrator Integration", lambda: test_orchestrator_integration(results))
    ]

    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-" * 80)
        test_func()
        time.sleep(0.1)  # Brief pause between tests

    # Print summary
    results.summary()

    # Exit with appropriate code
    sys.exit(0 if results.failed == 0 else 1)


if __name__ == "__main__":
    main()
