# JARVIS Dashboard Fix Plan

## Overview
The current dashboard contains outdated Phase 1 architecture mixed with newer JARVIS 2.0 components. This plan provides step-by-step prompts to audit, clean up, and fix the dashboard.

---

## Phase 1: Backend Audit

### Prompt 1.1 - Discover Existing API Endpoints
```
Scan the webapp folder and list ALL existing API endpoints. For each endpoint provide:
1. Route path (e.g., /api/dashboard/overview)
2. HTTP method (GET, POST, etc.)
3. What data it returns/accepts
4. Whether it's currently functional or a stub

Create a table mapping: Endpoint → Status → Description
```

### Prompt 1.2 - Identify Database Schema
```
Find and document the database schema being used:
1. What ORM/database is configured (SQLite, PostgreSQL, etc.)?
2. List all tables/models and their fields
3. Identify which tables are for JARVIS 2.0 (specialists, domains, benchmarks, tasks)
4. Identify any legacy tables from Phase 1 that should be removed
```

### Prompt 1.3 - Map Backend to Frontend Requirements
```
Compare the backend API endpoints against what the React UI expects.
The UI expects these endpoints (from ui/src/api/client.ts):

Dashboard API:
- GET /api/dashboard/overview
- GET /api/dashboard/domains
- GET /api/dashboard/domains/{domain}
- GET /api/dashboard/specialists
- GET /api/dashboard/specialists/{id}
- GET /api/dashboard/budget

Evaluation API:
- GET /api/evaluation/mode
- POST /api/evaluation/mode
- GET /api/evaluation/stats

Benchmark API:
- GET /api/benchmark/status
- POST /api/benchmark/run
- POST /api/benchmark/pause
- GET /api/benchmark/history

Tasks API:
- GET /api/tasks/recent
- GET /api/tasks/{taskId}
- POST /api/tasks/{taskId}/feedback

Health API:
- GET /health
- GET /version

Create a gap analysis: Which endpoints exist? Which are missing? Which return wrong data?
```

---

## Phase 2: Remove Legacy Code

### Prompt 2.1 - Identify Phase 1 Remnants
```
Search the codebase for these Phase 1 patterns that need removal:

1. "3-loop" or "three-loop" orchestration references
2. "Manager → Supervisor → Employee" hierarchy
3. "Start New Run" functionality (old execution model)
4. /cost-log routes or components
5. Any "orchestration" or "orchestrator" code not related to JARVIS 2.0
6. Legacy templates in webapp/templates/ that conflict with React UI

List all files containing these patterns with line numbers.
```

### Prompt 2.2 - Clean Up Legacy Templates
```
The webapp likely has Jinja2 templates that conflict with React:

1. Find all .html template files in webapp/templates/
2. Identify which serve the OLD dashboard vs which are still needed
3. The React app should be served from a single index.html entry point
4. Remove or archive any legacy dashboard templates

DO NOT remove templates needed for:
- API documentation
- Health check pages
- Admin utilities (if any)
```

### Prompt 2.3 - Remove Dead Routes
```
In the webapp's main app file (likely app.py or main.py):

1. Find routes that serve legacy dashboard pages
2. Find routes like /cost-log that don't have implementations
3. Remove or comment out these dead routes
4. Ensure the root route "/" serves the React app's index.html
5. Ensure /api/* routes are properly prefixed and don't conflict
```

---

## Phase 3: Fix Backend API Implementation

### Prompt 3.1 - Implement Missing Dashboard Endpoints
```
For each missing endpoint from the gap analysis, implement it:

GET /api/dashboard/overview should return:
{
  "system_health": "healthy|degraded|unhealthy",
  "total_specialists": number,
  "total_tasks_today": number,
  "domains": [DomainSummary],
  "budget": BudgetStatus,
  "evaluation": EvaluationStatus
}

GET /api/dashboard/domains should return:
[{
  "name": string,
  "specialists": [SpecialistSummary],
  "avg_score": number,
  "best_score": number,
  "tasks_today": number,
  "convergence_progress": number,
  "evolution_paused": boolean
}]

Implement each endpoint with proper error handling.
If no real data exists, return realistic mock data for now.
```

### Prompt 3.2 - Implement Benchmark API
```
The benchmark endpoints need to support:

GET /api/benchmark/status:
{
  "running": boolean,
  "progress": number (0-1),
  "current_task": string | null,
  "results": [BenchmarkResult]
}

POST /api/benchmark/run:
- Accept optional { domain?: string, benchmark_name?: string }
- Start benchmark execution (or mock it)
- Return { status: "started", run_id: string }

POST /api/benchmark/pause:
- Pause running benchmark
- Return { status: "paused" }

Implement state management for benchmark runs.
```

### Prompt 3.3 - Implement Evaluation Mode API
```
GET /api/evaluation/mode should return:
{
  "mode": "scoring_committee" | "ai_council" | "both",
  "scoring_committee_enabled": boolean,
  "ai_council_enabled": boolean
}

POST /api/evaluation/mode should:
- Accept { mode: string }
- Update the evaluation mode in config/database
- Return the new mode state

This controls how specialists are evaluated during evolution.
```

### Prompt 3.4 - Implement Budget API
```
GET /api/dashboard/budget should return:
{
  "daily_limit": number,
  "used": number,
  "remaining": number,
  "reset_time": string (ISO timestamp),
  "trend": number (percentage vs average)
}

This tracks API costs for running specialists.
If no real tracking exists, create a simple budget tracker.
```

---

## Phase 4: Wire Up Frontend Actions

### Prompt 4.1 - Fix Button Click Handlers
```
In ui/src/pages/Dashboard.tsx, ensure all buttons call real API endpoints:

1. "Run Benchmark" button → POST /api/benchmark/run
2. "Force Evolution" button → POST /api/evolution/trigger (need to implement)
3. "New Task" button → Opens modal, submit → POST /api/tasks/create
4. "Refresh" button → Refetch all dashboard data
5. Settings button → Opens settings modal
6. Budget badge click → Opens budget detail modal

Each action should:
- Show loading state
- Call the API
- Handle success (show notification, refresh data)
- Handle error (show error notification)
```

### Prompt 4.2 - Fix Domain Card Interactions
```
DomainCard components should:

1. Be expandable to show specialist list
2. Click on specialist → Open SpecialistDetailModal
3. Show real domain data from /api/dashboard/domains
4. Update when data refreshes

Verify the data flow:
useDomains() hook → API call → DomainCard props → Display
```

### Prompt 4.3 - Fix Task Table Actions
```
TasksTable should support:

1. Click row → Open TaskDetailModal with task details
2. "Retry" action on failed tasks → POST /api/tasks/{id}/retry
3. "View Details" in dropdown → Open modal
4. "Delete" action → DELETE /api/tasks/{id} (if supported)

Implement missing API endpoints as needed.
```

---

## Phase 5: Fix Routing & Navigation

### Prompt 5.1 - Configure Frontend Routing
```
In ui/src/App.tsx, ensure routes are properly configured:

/ → Dashboard (main view)
/dashboard → Dashboard
/domain/:name → Domain detail view (if needed)
/specialist/:id → Specialist detail view (if needed)
/* → Redirect to /

The React Router should handle all client-side navigation.
```

### Prompt 5.2 - Configure Backend to Serve React App
```
In the webapp backend:

1. Serve static files from ui/dist/ after build
2. All non-API routes should serve index.html (for SPA routing)
3. API routes should be under /api/* prefix
4. Avoid route conflicts between Flask/FastAPI and React Router

Example Flask setup:
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        abort(404)
    return send_from_directory('ui/dist', 'index.html')
```

---

## Phase 6: Testing & Validation

### Prompt 6.1 - Test All API Endpoints
```
Create a test script or use curl to verify each endpoint:

curl http://localhost:5000/api/dashboard/overview
curl http://localhost:5000/api/dashboard/domains
curl http://localhost:5000/api/dashboard/budget
curl http://localhost:5000/api/evaluation/mode
curl http://localhost:5000/api/benchmark/status
curl http://localhost:5000/api/tasks/recent
curl http://localhost:5000/health

Each should return valid JSON with expected structure.
Document any that fail or return unexpected data.
```

### Prompt 6.2 - Test Frontend Integration
```
Start the development server and verify:

1. Dashboard loads without errors
2. Stats cards show real or mock data
3. Domain cards display and expand
4. All buttons trigger their actions
5. Modals open and close properly
6. Auto-refresh works (data updates every 30s)
7. No console errors in browser dev tools

Document any issues found.
```

### Prompt 6.3 - Final Cleanup
```
After all fixes:

1. Remove any commented-out legacy code
2. Remove unused imports and files
3. Run linter/formatter on all changed files
4. Update any outdated comments or documentation
5. Commit with clear message describing what was fixed
```

---

## File Locations Reference

### Frontend (React UI)
- `ui/src/App.tsx` - Main app with routing
- `ui/src/pages/Dashboard.tsx` - Dashboard page component
- `ui/src/api/client.ts` - API client functions
- `ui/src/hooks/useDashboard.ts` - Data fetching hooks
- `ui/src/components/` - All UI components

### Backend (Webapp) - Need to verify locations
- `webapp/app.py` or `webapp/main.py` - Main application
- `webapp/routes/` or inline - API route definitions
- `webapp/models/` - Database models
- `webapp/templates/` - Jinja2 templates (legacy?)

---

## Summary Checklist

- [ ] Audit existing backend API endpoints
- [ ] Document database schema
- [ ] Identify and remove Phase 1 legacy code
- [ ] Clean up conflicting templates
- [ ] Implement missing API endpoints
- [ ] Wire frontend buttons to API calls
- [ ] Fix routing (frontend and backend)
- [ ] Test all endpoints
- [ ] Test frontend integration
- [ ] Final cleanup and commit
