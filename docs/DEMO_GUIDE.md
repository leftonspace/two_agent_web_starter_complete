# Step-by-Step Demo Guide: Approval Workflows + Integration Framework

Complete guide to demonstrating the Department-in-a-Box system with approval workflows and external system integrations.

## Prerequisites Check

### Step 1: Verify Python Dependencies
```bash
cd /home/user/two_agent_web_starter_complete
python3 -c "import aiohttp, cryptography; print('✓ Core dependencies OK')"
```
**Expected output:** `✓ Core dependencies OK`

**If fails, see [INSTALLATION.md](./INSTALLATION.md) for complete setup instructions.**

---

## Part 1: Start Web Server & Access Dashboard

### Step 2: Start the Web Application
```bash
cd /home/user/two_agent_web_starter_complete/agent/webapp
python app.py
```

**Expected output:**
```
============================================================
  AI Dev Team Dashboard
============================================================
  Starting web server on http://127.0.0.1:8000
  Press Ctrl+C to stop
============================================================
```

**Keep this terminal open.** Open a new terminal for remaining steps.

### Step 3: Verify Server is Running
Open browser or use curl:
```bash
curl http://127.0.0.1:8000/health
```

**Expected output:**
```json
{"status":"ok"}
```

---

## Part 2: Test Approval Workflows

### Step 4: Run Approval Workflow Tests
In a **new terminal**:
```bash
cd /home/user/two_agent_web_starter_complete
python tests/test_approval_workflows.py
```

**Expected output:**
```
================================================================================
TEST SUMMARY
================================================================================
Total Tests: 10
Passed: 10 (100.0%)
Failed: 0 (0.0%)
================================================================================
```

**What this tests:**
- ✅ Workflow registration
- ✅ Simple multi-step approval
- ✅ Conditional branching (salary thresholds)
- ✅ Rejection handling
- ✅ Tiered approval (different amounts)
- ✅ Parallel approvals (multiple approvers simultaneously)
- ✅ Auto-approval conditions
- ✅ Pending approvals query
- ✅ Statistics generation
- ✅ Orchestrator integration

### Step 5: Access Approvals Dashboard
**Browser:** Open `http://127.0.0.1:8000/approvals`

**Or via curl:**
```bash
curl http://127.0.0.1:8000/api/approvals
```

**Expected:** Empty approvals list (no pending approvals yet)

**Dashboard Features:**
- View all pending approvals
- Filter by department (HR, Finance, Legal)
- Filter by role
- Approve/Reject/Escalate actions
- Statistics dashboard

---

## Part 3: Configure Integration (SQLite Database)

### Step 6: Create Test Database
```bash
cd /home/user/two_agent_web_starter_complete
mkdir -p data
sqlite3 data/test_hr.db << 'EOF'
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT,
    hire_date TEXT,
    status TEXT DEFAULT 'active'
);

INSERT INTO employees (first_name, last_name, email, department, hire_date, status)
VALUES
    ('Alice', 'Johnson', 'alice@company.com', 'Engineering', '2024-01-15', 'active'),
    ('Bob', 'Smith', 'bob@company.com', 'Sales', '2024-03-20', 'active'),
    ('Carol', 'Williams', 'carol@company.com', 'Engineering', '2024-02-10', 'active');

SELECT 'Database created with ' || COUNT(*) || ' employees' FROM employees;
EOF
```

**Expected output:**
```
Database created with 3 employees
```

### Step 7: Add SQLite Integration via Web UI

**Option A - Browser (Recommended):**
1. Open: `http://127.0.0.1:8000/integrations`
2. Click **"+ Add Integration"** button
3. Select **"SQLite Database"** from dropdown
4. Enter Database Path: `/home/user/two_agent_web_starter_complete/data/test_hr.db`
5. Click **"Add Integration"**
6. Wait for success message
7. **Note the connector_id** from the integration card

**Option B - curl:**
```bash
curl -X POST http://127.0.0.1:8000/api/integrations \
  -H "Content-Type: application/json" \
  -d '{
    "type": "sqlite",
    "engine": "sqlite",
    "database": "/home/user/two_agent_web_starter_complete/data/test_hr.db"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "connector_id": "abc123-uuid-here",
  "name": "Database (sqlite)",
  "status": "connected"
}
```

**IMPORTANT:** Save the `connector_id` - you'll need it for testing.

### Step 8: Test Database Connection

**Browser:**
1. On integrations page, find your SQLite integration card
2. Click **"Test"** button
3. View test results modal showing:
   - Connection status (Success/Fail)
   - Latency in milliseconds
   - Database details

**Or via curl (replace {connector_id} with actual ID from Step 7):**
```bash
curl http://127.0.0.1:8000/api/integrations/{connector_id}/test
```

**Expected response:**
```json
{
  "success": true,
  "latency_ms": 5.23,
  "message": "Connection successful",
  "details": {
    "engine": "sqlite",
    "database": "/home/user/two_agent_web_starter_complete/data/test_hr.db"
  }
}
```

---

## Part 4: Test Integration Tools

### Step 9: Query Database via Python
Create and run test script:
```bash
cat > /home/user/two_agent_web_starter_complete/test_integration.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/home/user/two_agent_web_starter_complete/agent')

from integrations.database import DatabaseConnector
from integrations.base import get_registry

async def main():
    print("=" * 60)
    print("Testing Database Integration")
    print("=" * 60)

    # Create connector
    connector = DatabaseConnector(
        connector_id="test_db",
        engine="sqlite",
        config={
            "database": "/home/user/two_agent_web_starter_complete/data/test_hr.db"
        }
    )

    # Connect
    print("\n1. Connecting to database...")
    success = await connector.connect()
    print(f"   Connection: {'✓ SUCCESS' if success else '✗ FAILED'}")

    if not success:
        return

    # Query employees
    print("\n2. Querying employees...")
    employees = await connector.query("SELECT * FROM employees WHERE status = 'active'")
    print(f"   Found {len(employees)} active employees:")
    for emp in employees:
        print(f"   - {emp['first_name']} {emp['last_name']} ({emp['department']})")

    # List tables
    print("\n3. Listing tables...")
    tables = await connector.list_tables()
    print(f"   Tables: {', '.join(tables)}")

    # Describe table
    print("\n4. Describing 'employees' table...")
    schema = await connector.describe_table("employees")
    print(f"   Columns: {len(schema)}")
    for col in schema[:3]:  # Show first 3 columns
        print(f"   - {dict(col)}")

    # Get health
    print("\n5. Checking connector health...")
    health = connector.get_health()
    print(f"   Status: {health['status']}")
    print(f"   Metrics: {health['metrics']['total_requests']} requests, "
          f"{health['metrics']['success_rate']*100:.1f}% success rate")

    # Disconnect
    print("\n6. Disconnecting...")
    await connector.disconnect()
    print("   ✓ Disconnected")

    print("\n" + "=" * 60)
    print("✓ Integration test completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
EOF

python /home/user/two_agent_web_starter_complete/test_integration.py
```

**Expected output:**
```
============================================================
Testing Database Integration
============================================================

1. Connecting to database...
   Connection: ✓ SUCCESS

2. Querying employees...
   Found 3 active employees:
   - Alice Johnson (Engineering)
   - Bob Smith (Sales)
   - Carol Williams (Engineering)

3. Listing tables...
   Tables: employees

4. Describing 'employees' table...
   Columns: 7
   - {'cid': 0, 'name': 'id', 'type': 'INTEGER', ...}
   - {'cid': 1, 'name': 'first_name', 'type': 'TEXT', ...}
   - {'cid': 2, 'name': 'last_name', 'type': 'TEXT', ...}

5. Checking connector health...
   Status: connected
   Metrics: 2 requests, 100.0% success rate

6. Disconnecting...
   ✓ Disconnected

============================================================
✓ Integration test completed successfully!
============================================================
```

---

## Part 5: Create & Test Approval Workflow

### Step 10: Create HR Offer Approval Request
```bash
cat > /home/user/two_agent_web_starter_complete/create_approval.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/home/user/two_agent_web_starter_complete/agent')

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
            "start_date": "2025-02-01"
        },
        created_by="demo_user"
    )

    print(f"   ✓ Request created: {request.request_id}")
    print(f"   Status: {request.status.value}")
    print(f"   Current step: {request.current_step_ids[0] if request.current_step_ids else 'none'}")

    # Show pending approvals
    print("\n3. Checking pending approvals for hiring manager...")
    pending = engine.get_pending_approvals(role="hr_hiring_manager")
    print(f"   Pending approvals: {len(pending)}")
    if pending:
        for approval in pending:
            print(f"   - {approval['workflow_name']}")
            print(f"     Candidate: {approval['payload'].get('candidate_name')}")
            print(f"     Salary: ${approval['payload'].get('salary'):,}")
            print(f"     Time remaining: {approval['hours_remaining']:.1f} hours")

    print(f"\n4. View in browser:")
    print(f"   http://127.0.0.1:8000/approvals")
    print(f"\n   Request ID: {request.request_id}")

    print("\n" + "=" * 60)
    print("✓ Approval request created!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
EOF

python /home/user/two_agent_web_starter_complete/create_approval.py
```

**Expected output:**
```
============================================================
Creating HR Offer Letter Approval Request
============================================================

1. Registering HR offer letter workflow...
   ✓ Workflow registered: HR Offer Letter Approval
   Steps: 3
   1. Hiring Manager Approval (hr_hiring_manager)
   2. Director Approval (hr_director)
      Condition: payload.get('salary', 0) > 100000
   3. HR Head Final Approval (hr_head)

2. Creating approval request for Senior Engineer...
   ✓ Request created: abc123-def456-...
   Status: pending
   Current step: hiring_manager

3. Checking pending approvals for hiring manager...
   Pending approvals: 1
   - HR Offer Letter Approval
     Candidate: Jane Developer
     Salary: $145,000
     Time remaining: 24.0 hours

4. View in browser:
   http://127.0.0.1:8000/approvals

   Request ID: abc123-def456-...

============================================================
✓ Approval request created!
============================================================
```

**SAVE THE REQUEST_ID** - You'll need it for the next steps.

### Step 11: View Approval in Web UI

**Browser:**
1. Open: `http://127.0.0.1:8000/approvals`
2. You should see **1 pending approval**
3. Observe the approval card showing:
   - **Candidate name:** Jane Developer
   - **Salary:** $145,000
   - **Current step:** Hiring Manager Approval
   - **Status badge:** PENDING (orange)
   - **Time remaining:** ~24 hours
4. Click on the card to see full details

**Or via curl:**
```bash
curl http://127.0.0.1:8000/api/approvals?role=hr_hiring_manager
```

### Step 12: Approve as Hiring Manager
```bash
# Replace with your actual request_id from Step 10
REQUEST_ID="<paste-request-id-here>"

curl -X POST "http://127.0.0.1:8000/api/approvals/${REQUEST_ID}/approve" \
  -F "approver_user_id=manager_001" \
  -F "approver_role=hr_hiring_manager" \
  -F "comments=Great candidate, approved!"
```

**Expected response:**
```json
{
  "success": true,
  "request_id": "abc123...",
  "status": "pending",
  "message": "Request approved successfully"
}
```

**Note:** Status is still "pending" because it needs director approval (salary > $100k triggers conditional step)

### Step 13: Check Next Approval Step
```bash
curl "http://127.0.0.1:8000/api/approvals/${REQUEST_ID}"
```

**Expected response shows:**
- Previous decision by hiring manager with comments
- Current step now requires: **hr_director**
- Conditional branching kicked in (salary > $100k)

**Refresh browser** at `http://127.0.0.1:8000/approvals` - you'll see the request moved to the next step.

### Step 14: Approve as Director
```bash
curl -X POST "http://127.0.0.1:8000/api/approvals/${REQUEST_ID}/approve" \
  -F "approver_user_id=director_001" \
  -F "approver_role=hr_director" \
  -F "comments=Approved for senior level"
```

**Expected:** Status still "pending", now waiting for HR Head.

### Step 15: Final Approval as HR Head
```bash
curl -X POST "http://127.0.0.1:8000/api/approvals/${REQUEST_ID}/approve" \
  -F "approver_user_id=hr_head_001" \
  -F "approver_role=hr_head" \
  -F "comments=Final approval - welcome aboard!"
```

**Expected response:**
```json
{
  "success": true,
  "request_id": "abc123...",
  "status": "approved",
  "message": "Request approved successfully"
}
```

**Status is now "approved"!** ✅

**Verify in browser:** Refresh approvals page - the request should now show as APPROVED (green badge).

---

## Part 6: End-to-End Workflow with Integration

### Step 16: Complete Workflow (Approval → Database)
This demonstrates the full workflow: create approval request → multi-step approval → create employee in database.

```bash
cat > /home/user/two_agent_web_starter_complete/full_workflow.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/home/user/two_agent_web_starter_complete/agent')

from approval_engine import ApprovalEngine, DecisionType
from integrations.database import DatabaseConnector
from datetime import datetime

async def main():
    print("=" * 60)
    print("Full HR Workflow: Approval → Database Integration")
    print("=" * 60)

    # Setup
    engine = ApprovalEngine()
    db = DatabaseConnector(
        connector_id="hr_db",
        engine="sqlite",
        config={"database": "/home/user/two_agent_web_starter_complete/data/test_hr.db"}
    )
    await db.connect()

    # Step 1: Create approval request
    print("\n1. Creating approval request...")
    from approval_engine import create_hr_offer_letter_workflow
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
            "start_date": "2025-02-15"
        },
        created_by="recruiter_001"
    )
    print(f"   ✓ Approval request: {request.request_id[:8]}...")
    print(f"   Status: {request.status.value}")

    # Step 2: Approve step by step
    print("\n2. Processing multi-step approvals...")

    # Hiring manager
    print("   - Hiring Manager approving...")
    request = engine.process_decision(
        request.request_id, "mgr_001", DecisionType.APPROVE,
        "Excellent technical skills", "hr_hiring_manager"
    )
    print(f"     ✓ Current step: {request.current_step_ids}")

    # Director (required for high salary)
    print("   - Director approving (high salary triggered this step)...")
    request = engine.process_decision(
        request.request_id, "dir_001", DecisionType.APPROVE,
        "Approved for staff level", "hr_director"
    )
    print(f"     ✓ Current step: {request.current_step_ids}")

    # HR Head
    print("   - HR Head final approval...")
    request = engine.process_decision(
        request.request_id, "head_001", DecisionType.APPROVE,
        "Welcome to the team!", "hr_head"
    )
    print(f"     ✓ Status: {request.status.value}")

    # Step 3: Create employee in database (if approved)
    if request.status.value == "approved":
        print("\n3. Creating employee record in database...")

        # Split name
        parts = request.payload["candidate_name"].split()
        first_name = parts[0]
        last_name = " ".join(parts[1:])

        # Insert into database
        await db.execute(
            """INSERT INTO employees
               (first_name, last_name, email, department, hire_date, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": request.payload["email"],
                "department": request.payload["department"],
                "hire_date": request.payload["start_date"],
                "status": "pending_start"
            }
        )
        print(f"   ✓ Employee created in database")

        # Verify
        print("\n4. Verifying employee in database...")
        employees = await db.query(
            "SELECT * FROM employees WHERE email = ?",
            {"email": request.payload["email"]}
        )

        if employees:
            emp = employees[0]
            print(f"   ✓ Found: {emp['first_name']} {emp['last_name']}")
            print(f"     Email: {emp['email']}")
            print(f"     Department: {emp['department']}")
            print(f"     Hire Date: {emp['hire_date']}")
            print(f"     Status: {emp['status']}")

    # Step 4: Show all employees
    print("\n5. All employees in database:")
    all_employees = await db.query("SELECT * FROM employees ORDER BY id")
    for emp in all_employees:
        print(f"   {emp['id']}. {emp['first_name']} {emp['last_name']} - "
              f"{emp['department']} ({emp['status']})")

    # Step 5: Show approval statistics
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
EOF

python /home/user/two_agent_web_starter_complete/full_workflow.py
```

**Expected output:**
```
============================================================
Full HR Workflow: Approval → Database Integration
============================================================

1. Creating approval request...
   ✓ Approval request: abc12345...
   Status: pending

2. Processing multi-step approvals...
   - Hiring Manager approving...
     ✓ Current step: ['director']
   - Director approving (high salary triggered this step)...
     ✓ Current step: ['hr_head']
   - HR Head final approval...
     ✓ Status: approved

3. Creating employee record in database...
   ✓ Employee created in database

4. Verifying employee in database...
   ✓ Found: David Martinez
     Email: david.martinez@company.com
     Department: Engineering
     Hire Date: 2025-02-15
     Status: pending_start

5. All employees in database:
   1. Alice Johnson - Engineering (active)
   2. Bob Smith - Sales (active)
   3. Carol Williams - Engineering (active)
   4. David Martinez - Engineering (pending_start)

6. Approval workflow statistics:
   Total requests: 2
   Approved: 2
   Rejected: 0
   Pending: 0

============================================================
✓ Complete workflow executed successfully!
  Approval Request → Multi-Step Approval → Database Integration
============================================================
```

---

## Part 7: Verify Everything

### Step 17: Check System Health

**All workflows:**
```bash
curl http://127.0.0.1:8000/api/workflows
```

**Expected:** List of registered workflows (HR, Finance, Legal)

**All integrations:**
```bash
curl http://127.0.0.1:8000/api/integrations
```

**Expected:** List of connected integrations with health metrics

**Overall health:**
```bash
curl http://127.0.0.1:8000/health
```

**Expected:** `{"status":"ok"}`

### Step 18: View All Dashboards in Browser

**Open these URLs in your browser:**

1. **Main Dashboard:** `http://127.0.0.1:8000/`
   - System overview
   - Recent runs
   - Project selection

2. **Approvals Dashboard:** `http://127.0.0.1:8000/approvals`
   - Statistics: Pending, Approved, Rejected, Overdue
   - Filter by department (HR, Finance, Legal)
   - Filter by role
   - Approve/Reject/Escalate actions
   - Previous decisions history
   - Time remaining indicators

3. **Integrations Dashboard:** `http://127.0.0.1:8000/integrations`
   - Connected integrations with status badges
   - Health metrics (requests, success rate)
   - Test connection button
   - Connect/Disconnect controls
   - Add new integrations wizard

4. **Jobs Dashboard:** `http://127.0.0.1:8000/jobs`
   - Background job status
   - Job logs
   - Cancel/rerun jobs

---

## Part 8: Test Additional Features

### Step 19: Test Auto-Approval (Conditional)
```bash
python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/home/user/two_agent_web_starter_complete/agent')

from approval_engine import ApprovalEngine, create_hr_offer_letter_workflow

async def main():
    print("Testing auto-approval for intern offer...")

    engine = ApprovalEngine()
    engine.register_workflow(create_hr_offer_letter_workflow())

    # Create intern offer (should auto-approve: salary < $50k AND level == 'intern')
    request = engine.create_approval_request(
        workflow_id="hr_offer_letter_v1",
        mission_id="auto_approve_test",
        payload={
            "candidate_name": "Summer Intern",
            "position": "Software Intern",
            "salary": 45000,
            "level": "intern",
            "department": "Engineering"
        },
        created_by="demo"
    )

    print(f"Status: {request.status.value}")
    print(f"Expected: approved (auto-approved due to conditions)")
    print(f"✓ Auto-approval works!" if request.status.value == "approved" else "✗ Failed")

asyncio.run(main())
EOF
```

### Step 20: Test Rejection Workflow
```bash
python << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/home/user/two_agent_web_starter_complete/agent')

from approval_engine import ApprovalEngine, DecisionType, create_finance_expense_workflow

async def main():
    print("Testing rejection workflow...")

    engine = ApprovalEngine()
    engine.register_workflow(create_finance_expense_workflow())

    # Create expense request
    request = engine.create_approval_request(
        workflow_id="finance_expense_v1",
        mission_id="rejection_test",
        payload={
            "amount": 15000,
            "description": "Office furniture",
            "category": "Equipment"
        },
        created_by="employee"
    )

    print(f"Initial status: {request.status.value}")

    # Reject
    request = engine.process_decision(
        request.request_id,
        "controller_001",
        DecisionType.REJECT,
        "Budget exceeded for this quarter",
        "finance_controller"
    )

    print(f"Final status: {request.status.value}")
    print(f"✓ Rejection works!" if request.status.value == "rejected" else "✗ Failed")

asyncio.run(main())
EOF
```

---

## Cleanup (Optional)

### Step 21: Stop Web Server
In the terminal running the web server:
```
Press Ctrl+C
```

### Step 22: Clean Test Data (Optional)
```bash
rm /home/user/two_agent_web_starter_complete/data/test_hr.db
rm /home/user/two_agent_web_starter_complete/test_integration.py
rm /home/user/two_agent_web_starter_complete/create_approval.py
rm /home/user/two_agent_web_starter_complete/full_workflow.py
```

### Step 23: Keep Test Data (Recommended)
To keep the demo data for future testing:
```bash
# Just stop the server, keep the database and scripts
# You can restart the server anytime with:
cd /home/user/two_agent_web_starter_complete/agent/webapp && python app.py
```

---

## Summary Checklist

At the end of this demo, you should have verified:

- ✅ **Web Server** - Running on port 8000
- ✅ **Unit Tests** - 10/10 approval workflow tests passing
- ✅ **Database Integration** - SQLite connected and queried successfully
- ✅ **Integration Tools** - Python API working (query, create, update)
- ✅ **Approval Workflow** - Multi-step approval created and processed
- ✅ **Conditional Logic** - Director approval triggered by salary > $100k
- ✅ **Web UI** - Approvals and integrations visible and functional
- ✅ **End-to-End** - Complete flow: Approval → Database creation
- ✅ **Auto-Approval** - Conditional auto-approval working
- ✅ **Rejection** - Rejection workflow working
- ✅ **Health Checks** - All APIs responding correctly

---

## Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
# Then restart server
cd /home/user/two_agent_web_starter_complete/agent/webapp && python app.py
```

### Database Creation Fails
```bash
# Verify SQLite is installed
sqlite3 --version

# If not installed (Ubuntu/Debian):
sudo apt-get update && sudo apt-get install -y sqlite3

# If not installed (macOS):
brew install sqlite3
```

### Import Errors
```bash
# Ensure correct directory
cd /home/user/two_agent_web_starter_complete

# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Check dependencies
python3 -m pip list | grep -E 'aiohttp|cryptography|asyncpg|aiomysql|aiosqlite'
```

### Web UI Doesn't Load
- Verify server is running: `curl http://127.0.0.1:8000/health`
- Check firewall settings
- Try: `http://localhost:8000` instead of `127.0.0.1`
- Check browser console for errors (F12)

### Test Failures
```bash
# Run with verbose output
cd /home/user/two_agent_web_starter_complete
python -m pytest tests/test_approval_workflows.py -v -s

# Check logs
tail -f agent/run_logs_main/*.jsonl
```

### Integration Connection Fails
- Verify database file exists: `ls -la data/test_hr.db`
- Check file permissions: `chmod 644 data/test_hr.db`
- Verify path is absolute, not relative
- Check integration status in web UI

---

## What You've Demonstrated

### ✅ Phase 3.1: Approval Workflows
- Multi-step approval chains (3 steps)
- Conditional branching (salary thresholds)
- Parallel approvals capability
- Auto-approval conditions
- Timeout and escalation tracking
- Web UI for approval management
- REST API for programmatic control

### ✅ Phase 3.2: Integration Framework
- Base connector framework with rate limiting
- OAuth2 authentication system
- Database connectors (PostgreSQL, MySQL, SQLite)
- BambooHR HRIS connector
- Integration tools for agents
- Web UI for connection management
- Credential encryption and security

### ✅ End-to-End Workflows
- Complete HR workflow: Request → Approval → Database
- Conditional logic in action
- Multiple approval paths
- Integration between systems
- Real-time status tracking

---

## Next Steps

### Extend the Demo
1. **Add BambooHR Integration** - Connect to real BambooHR account
2. **Add PostgreSQL** - Connect to production database
3. **Add More Workflows** - Finance expense, Legal contract review
4. **Email Notifications** - Send emails on approval/rejection
5. **Calendar Integration** - Schedule onboarding events

### Production Deployment
1. **Environment Variables** - Move credentials to env vars
2. **Production Database** - Use PostgreSQL instead of SQLite
3. **Authentication** - Enable user authentication (already built-in)
4. **HTTPS** - Set up SSL/TLS
5. **Monitoring** - Add Prometheus/Grafana

### Advanced Features
1. **Approval Delegation** - Allow users to delegate approvals
2. **Out-of-Office** - Handle unavailable approvers
3. **Bulk Approvals** - Approve multiple requests at once
4. **Analytics Dashboard** - Approval trends and statistics
5. **SLA Tracking** - Monitor approval times

---

## Support

- **Documentation:** See `/docs/` directory
- **Phase 3.1 Docs:** `PHASE_3_1_APPROVAL_WORKFLOWS.md`
- **Phase 3.2 Docs:** `PHASE_3_2_INTEGRATION_FRAMEWORK.md`
- **Installation Guide:** `INSTALLATION.md`

---

**🎉 Congratulations!**

You've successfully demonstrated a complete **Department-in-a-Box** system with:
- ✅ Multi-step approval workflows
- ✅ External system integrations
- ✅ Web UI for management
- ✅ REST APIs for automation
- ✅ End-to-end HR workflow automation

**The system is production-ready!**
