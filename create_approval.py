import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "agent"))

from approval_engine import ApprovalEngine, create_hr_offer_letter_workflow


async def main():
    print("=" * 60)
    print("Creating HR Offer Letter Approval Request")
    print("=" * 60)

    engine = ApprovalEngine()

    # Register workflow
    print("\n1. Registering HR offer letter workflow...")
    workflow = create_hr_offer_letter_workflow()
    engine.register_workflow(workflow)
    print(f"   ✓ Workflow registered: {workflow.workflow_name}")
    print(f"   Steps: {len(workflow.steps)}")
    for i, step in enumerate(workflow.steps, 1):
        print(f"   {i}. {step.step_name} ({step.approver_role})")
        if step.condition:
            print(f"      Condition: {step.condition}")

    # Create approval request
    print("\n2. Creating approval request for Senior Engineer...")
    request = engine.create_approval_request(
        workflow_id="hr_offer_letter_v1",
        mission_id="demo_mission_001",
        payload={
            "candidate_name": "Jane Developer",
            "position": "Senior Software Engineer",
            "salary": 145000,
            "level": "senior",
            "department": "Engineering",
            "start_date": "2025-02-01",
        },
        created_by="demo_user",
    )

    print(f"   ✓ Request created: {request.request_id}")
    print(f"   Status: {request.status.value}")
    print(
        f"   Current step: "
        f"{request.current_step_ids[0] if request.current_step_ids else 'none'}"
    )

    print("\n3. Checking pending approvals for hiring manager...")
    pending = engine.get_pending_approvals(role="hr_hiring_manager")
    print(f"   Pending approvals: {len(pending)}")
    if pending:
        for approval in pending:
            print(f"   - {approval['workflow_name']}")
            print(f"     Candidate: {approval['payload'].get('candidate_name')}")
            print(f"     Salary: ${approval['payload'].get('salary'):,}")
            print(f"     Time remaining: {approval['hours_remaining']:.1f} hours")

    print("\n4. View in browser:")
    print("   http://127.0.0.1:8000/approvals")
    print(f"\n   Request ID: {request.request_id}")

    print("\n" + "=" * 60)
    print("✓ Approval request created!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
