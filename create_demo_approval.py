import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "agent"))

from approval_engine import ApprovalEngine, create_hr_offer_letter_workflow


async def main():
    print("=" * 60)
    print("Creating demo HR approval (PENDING)")
    print("=" * 60)

    engine = ApprovalEngine()
    engine.register_workflow(create_hr_offer_letter_workflow())

    request = engine.create_approval_request(
        workflow_id="hr_offer_letter_v1",
        mission_id="demo_hr_ui_001",
        payload={
            "candidate_name": "Jane Demo",
            "position": "HR Business Partner",
            "salary": 95000,
            "level": "mid",
            "department": "Human Resources",
            "email": "jane.demo@company.com",
            "start_date": "2025-03-01",
        },
        created_by="recruiter_demo",
    )

    print(f"   ✓ Request ID: {request.request_id}")
    print(f"   Status: {request.status.value}")
    print(f"   Current step(s): {request.current_step_ids}")

    print("\nOpen: http://127.0.0.1:8000/approvals")
    print("You should see Jane Demo as a pending approval.")

    print("\n" + "=" * 60)
    print("✓ Pending approval created for UI demo")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
