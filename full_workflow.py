import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "agent"))

from approval_engine import ApprovalEngine, DecisionType, create_hr_offer_letter_workflow
from integrations.database import DatabaseConnector


async def main():
    print("=" * 60)
    print("Full HR Workflow: Approval → Database Integration")
    print("=" * 60)

    engine = ApprovalEngine()
    db_path = ROOT / "data" / "test_hr.db"

    # DB connector (auth_type must be valid for the enum)
    db = DatabaseConnector(
        connector_id="hr_db",
        engine="sqlite",
        config={
            "database": str(db_path),
            "auth_type": "api_key",  # not really used for SQLite
            "api_key": "",
        },
    )
    await db.connect()

    # Step 1: Create approval request
    print("\n1. Creating approval request...")
    engine.register_workflow(create_hr_offer_letter_workflow())

    request = engine.create_approval_request(
        workflow_id="hr_offer_letter_v1",
        mission_id="workflow_demo_001",
        payload={
            "candidate_name": "David Martinez",
            "position": "Staff Engineer",
            "salary": 165000,
            "level": "staff",
            "department": "Engineering",
            "email": "david.martinez@company.com",
            "start_date": "2025-02-15",
        },
        created_by="recruiter_001",
    )
    print(f"   ✓ Approval request: {request.request_id[:8]}...")
    print(f"   Status: {request.status.value}")

    # Step 2: Process multi-step approvals
    print("\n2. Processing multi-step approvals...")

    print("   - Hiring Manager approving...")
    request = engine.process_decision(
        request.request_id,
        "mgr_001",
        DecisionType.APPROVE,
        "Excellent technical skills",
        "hr_hiring_manager",
    )
    print(f"     ✓ Current step: {request.current_step_ids}")

    print("   - Director approving (high salary triggered this step)...")
    request = engine.process_decision(
        request.request_id,
        "dir_001",
        DecisionType.APPROVE,
        "Approved for staff level",
        "hr_director",
    )
    print(f"     ✓ Current step: {request.current_step_ids}")

    print("   - HR Head final approval...")
    request = engine.process_decision(
        request.request_id,
        "head_001",
        DecisionType.APPROVE,
        "Welcome to the team!",
        "hr_head",
    )
    print(f"     ✓ Status: {request.status.value}")

    # Step 3: Insert into database if approved (idempotent)
    if request.status.value == "approved":
        print("\n3. Creating employee record in database...")

        parts = request.payload["candidate_name"].split()
        first_name = parts[0]
        last_name = " ".join(parts[1:])

        # Check if this email already exists
        existing = await db.query(
            "SELECT * FROM employees WHERE email = :email",
            {"email": request.payload["email"]},
        )

        if existing:
            emp = existing[0]
            print("   ⚠ Employee already exists in database, skipping insert.")
            print(
                f"   Existing record: {emp['first_name']} {emp['last_name']} "
                f"({emp['email']}) status={emp['status']}"
            )
        else:
            await db.execute(
                """
                INSERT INTO employees
                    (first_name, last_name, email, department, hire_date, status)
                VALUES
                    (:first_name, :last_name, :email, :department, :hire_date, :status)
                """,
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": request.payload["email"],
                    "department": request.payload["department"],
                    "hire_date": request.payload["start_date"],
                    "status": "pending_start",
                },
            )
            print("   ✓ Employee created in database")

        print("\n4. Verifying employee in database...")
        employees = await db.query(
            "SELECT * FROM employees WHERE email = :email",
            {"email": request.payload["email"]},
        )

        if employees:
            emp = employees[0]
            print(f"   ✓ Found: {emp['first_name']} {emp['last_name']}")
            print(f"     Email: {emp['email']}")
            print(f"     Department: {emp['department']}")
            print(f"     Hire Date: {emp['hire_date']}")
            print(f"     Status: {emp['status']}")

    print("\n5. All employees in database:")
    all_employees = await db.query("SELECT * FROM employees ORDER BY id")
    for emp in all_employees:
        print(
            f"   {emp['id']}. {emp['first_name']} {emp['last_name']} - "
            f"{emp['department']} ({emp['status']})"
        )

    print("\n6. Approval workflow statistics:")
    stats = engine.get_statistics(domain="hr")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Approved: {stats['approved']}")
    print(f"   Rejected: {stats['rejected']}")
    print(f"   Pending: {stats['pending']}")

    await db.disconnect()

    print("\n" + "=" * 60)
    print("✓ Complete workflow executed successfully!")
    print("  Approval Request → Multi-Step Approval → Database Integration")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
