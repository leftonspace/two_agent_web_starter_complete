import asyncio
import sys
from pathlib import Path

# Make sure Python can see the "agent" package
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "agent"))

from integrations.database import DatabaseConnector


async def main() -> None:
    print("=" * 60)
    print("Testing Database Integration (SQLite)")
    print("=" * 60)

    db_path = ROOT / "data" / "test_hr.db"
    print(f"\nUsing DB: {db_path}")
    if not db_path.exists():
        print("ERROR: Database file does not exist.")
        return

    # NOTE: auth_type must be a valid AuthType enum value
    connector = DatabaseConnector(
        connector_id="test_db",
        engine="sqlite",
        config={
            "database": str(db_path),
            "auth_type": "api_key",  # fake API key style, but accepted by the enum
            "api_key": "",           # not actually used for local SQLite
        },
    )

    print("\n1. Connecting to database...")
    success = await connector.connect()
    print(f"   Connection: {'✓ SUCCESS' if success else '✗ FAILED'}")
    if not success:
        return

    print("\n2. Querying employees...")
    employees = await connector.query(
        "SELECT * FROM employees WHERE status = 'active'"
    )
    print(f"   Found {len(employees)} active employees:")
    for emp in employees:
        print(f"   - {emp['first_name']} {emp['last_name']} ({emp['department']})")

    print("\n3. Listing tables...")
    tables = await connector.list_tables()
    print(f"   Tables: {', '.join(tables)}")

    print("\n4. Describing 'employees' table...")
    schema = await connector.describe_table("employees")
    print(f"   Columns: {len(schema)}")
    for col in schema[:3]:
        print(f"   - {dict(col)}")

    print("\n5. Checking connector health...")
    health = connector.get_health()
    print(f"   Status: {health['status']}")
    print(
        f"   Metrics: {health['metrics']['total_requests']} requests, "
        f"{health['metrics']['success_rate']*100:.1f}% success rate"
    )

    print("\n6. Disconnecting...")
    await connector.disconnect()
    print("   ✓ Disconnected")

    print("\n" + "=" * 60)
    print("✓ Integration test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
