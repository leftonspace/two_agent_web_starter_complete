# Stage 8: Job Manager with Background Execution

**Stage 8** transforms the web dashboard from a simple form-based interface into a full job management system. Jobs run in the background, logs stream in real-time, and you can cancel or rerun jobs at any time.

## Overview

Stage 8 adds:
- **Background execution** - Jobs don't block the UI
- **Live log streaming** - Watch logs update in real-time
- **Job list page** - Browse all jobs with status filtering
- **Job detail page** - See config, logs, costs, and results
- **Cancel support** - Stop running jobs gracefully
- **Rerun capability** - Restart jobs with same configuration

## Architecture

### Components

1. **`agent/jobs.py`** - Job manager and lifecycle
   - `Job` dataclass with ID, status, config, logs, results
   - `JobManager` class for CRUD operations
   - Background execution using Python threads
   - Atomic file-based persistence

2. **Updated `agent/webapp/app.py`** - New job routes
   - `GET /jobs` - Job list page
   - `GET /jobs/{job_id}` - Job detail with live logs
   - `POST /jobs/{job_id}/cancel` - Cancel running job
   - `POST /jobs/{job_id}/rerun` - Rerun with same config
   - `GET /api/jobs/{job_id}/logs` - Polling endpoint for logs

3. **New Templates**
   - `jobs.html` - Job list table with filters
   - `job_detail.html` - Job details with live log viewer

4. **Job Storage**
   - State file: `agent/jobs_state.json` (all job metadata)
   - Log files: `run_logs/{job_id}/job.log` (per-job logs)

### Job Lifecycle

```
Created (queued) → Started (running) → Finished (completed/failed/cancelled)
```

**Job Statuses:**
- `queued` - Job created, waiting to start
- `running` - Job executing in background thread
- `completed` - Job finished successfully
- `failed` - Job encountered an error
- `cancelled` - Job was stopped by user

### Background Execution

Jobs run in Python threads:
1. User submits form → POST /run
2. JobManager creates job with status=queued
3. Background thread starts, calls `run_project(config)`
4. Thread updates job status and logs continuously
5. On completion, stores RunSummary in job.result_summary

### Log Streaming

Logs are streamed via polling:
1. Job writes to `run_logs/{job_id}/job.log`
2. JavaScript polls `GET /api/jobs/{job_id}/logs` every 2 seconds
3. New log lines are appended to the UI
4. Auto-scrolls to bottom if user is near bottom

### Cancellation

Cancellation is graceful:
1. User clicks "Cancel" → POST /api/jobs/{job_id}/cancel
2. JobManager sets `job.cancelled = True`
3. Background thread checks flag periodically
4. Thread exits cleanly and sets status=cancelled

**Note:** Cancellation is coarse-grained (checks between operations, not mid-operation). For finer control, the orchestrator would need to check the flag more frequently.

## Usage

### Starting the Web Dashboard

Same as Stage 7:

```bash
python start_webapp.py
# or
python -m agent.webapp.app
```

Access at: **http://127.0.0.1:8000**

### Creating a Job

1. Go to home page: http://127.0.0.1:8000
2. Fill out the project configuration form
3. Click "Start Run"
4. You'll be redirected to the job detail page
5. **The UI remains responsive** - job runs in background

### Viewing Jobs

**Job List Page:** http://127.0.0.1:8000/jobs

- Shows all jobs with status, timestamps, and actions
- Filter by status (running, completed, failed, cancelled)
- Auto-refreshes every 5 seconds if there are active jobs
- Actions: View, Cancel (if running), Rerun (if finished)

**Job Detail Page:** http://127.0.0.1:8000/jobs/{job_id}

- Shows complete job configuration
- Live log viewer (updates every 2 seconds)
- Cost breakdown if job completed
- Cancel button if running
- Rerun button for any job
- Auto-checks job status (reloads if status changes)

### Live Logs

The job detail page shows logs in real-time:
- Logs automatically refresh every 2 seconds
- Auto-scrolls to bottom (if you're near bottom)
- "Copy Logs" button to copy all logs to clipboard
- No need to manually refresh

### Cancelling a Job

**From Job List:**
1. Click "Cancel" button next to a running job
2. Confirm the cancellation
3. Job will stop gracefully
4. Status changes to "cancelled"

**From Job Detail:**
1. Click "Cancel Job" button
2. Confirm the cancellation
3. Watch logs for cancellation message
4. Page reloads when status changes

**Note:** Cancellation takes effect between iterations/operations. A job in the middle of an LLM call will finish that call before stopping.

### Rerunning a Job

**From Job List:**
1. Click "Rerun" button next to a completed/failed job
2. New job created with same configuration
3. Redirected to new job detail page

**From Job Detail:**
1. Click "Rerun Job" button
2. New job created with same configuration
3. Redirected to new job detail page

The new job gets a fresh ID and logs. Original job is preserved.

## API Reference

### Job Management Endpoints

#### `GET /jobs`
Job list page with optional status filtering.

**Query Parameters:**
- `status` (optional) - Filter by status (queued, running, completed, failed, cancelled)

**Returns:** HTML page with job list table

---

#### `GET /jobs/{job_id}`
Job detail page with live log viewer.

**Path Parameters:**
- `job_id` - Job identifier

**Returns:** HTML page with job details and live logs

**Raises:**
- 404 if job not found

---

#### `POST /jobs/{job_id}/rerun`
Rerun a job with the same configuration.

**Path Parameters:**
- `job_id` - Job identifier to rerun

**Returns:** Redirect to new job detail page (303)

**Raises:**
- 404 if job not found

---

### API Endpoints (JSON)

#### `GET /api/jobs`
List all jobs (JSON).

**Query Parameters:**
- `status` (optional) - Filter by status
- `limit` (optional) - Maximum number of jobs to return

**Returns:**
```json
[
  {
    "id": "abc123def456",
    "status": "running",
    "config": { ... },
    "created_at": "2024-01-01T10:00:00.000Z",
    "updated_at": "2024-01-01T10:01:00.000Z",
    "started_at": "2024-01-01T10:00:05.000Z",
    "finished_at": null,
    "logs_path": "/path/to/job.log",
    "result_summary": null,
    "error": null,
    "cancelled": false
  }
]
```

---

#### `GET /api/jobs/{job_id}`
Get job details (JSON).

**Path Parameters:**
- `job_id` - Job identifier

**Returns:** Job object (same structure as above)

**Raises:**
- 404 if job not found

---

#### `GET /api/jobs/{job_id}/logs`
Get job logs for polling.

**Path Parameters:**
- `job_id` - Job identifier

**Query Parameters:**
- `tail` (optional) - Return only last N lines

**Returns:**
```json
{
  "logs": "Log line 1\nLog line 2\n..."
}
```

**Raises:**
- 404 if job not found

---

#### `POST /api/jobs/{job_id}/cancel`
Cancel a running or queued job.

**Path Parameters:**
- `job_id` - Job identifier

**Returns:**
```json
{
  "success": true,
  "message": "Job abc123 cancellation requested"
}
```

**Raises:**
- 404 if job not found
- 400 if job cannot be cancelled (already finished)

---

### Python API

```python
from jobs import get_job_manager

# Get the global job manager
manager = get_job_manager()

# Create a job
config = {
    "mode": "3loop",
    "project_subdir": "my_project",
    "task": "Build a website",
    "max_rounds": 3,
}
job = manager.create_job(config)

# Start the job in background
manager.start_job(job.id)

# List all jobs
jobs = manager.list_jobs()

# Filter by status
running_jobs = manager.list_jobs(status="running")

# Get a specific job
job = manager.get_job(job_id)

# Update a job
manager.update_job(job_id, status="running")

# Cancel a job
manager.cancel_job(job_id)

# Get logs
logs = manager.get_job_logs(job_id)
logs_tail = manager.get_job_logs(job_id, tail_lines=100)
```

## File Structure

```
agent/
├── jobs.py                     # NEW: Job manager
├── webapp/
│   ├── app.py                 # UPDATED: Job routes
│   └── templates/
│       ├── jobs.html          # NEW: Job list page
│       └── job_detail.html    # NEW: Job detail page
└── tests_stage8/               # NEW: Tests
    ├── test_jobs.py
    └── test_smoke.py

run_logs/
├── {job_id}/
│   ├── job.log                # Job-specific logs
│   └── run_summary.json       # RunSummary (if completed)
└── ...

agent/
└── jobs_state.json             # All job metadata (persisted)
```

## Testing

Run Stage 8 tests:

```bash
# Smoke tests (no pytest required)
python agent/tests_stage8/test_smoke.py

# Full test suite (requires pytest)
pytest agent/tests_stage8/

# Specific test file
pytest agent/tests_stage8/test_jobs.py -v
```

## Backward Compatibility

Stage 8 is fully backward compatible with Stage 7:

- **CLI still works:** `python run_mode.py` unchanged
- **Old run history:** Still accessible at `/run/{run_id}`
- **Direct runs:** Old `run_project()` API still works
- **Existing routes:** All Stage 7 routes still functional

The only change: POST /run now creates a background job instead of blocking.

## Design Decisions

### Why Threading Instead of AsyncIO?

**Threading** was chosen for simplicity:
- Easier integration with existing synchronous code
- No need to refactor `run_project()` to be async
- Python GIL is not a concern (orchestrator is I/O-bound)
- Simple thread-per-job model is sufficient for MVP

Future enhancement could use `asyncio` or a proper job queue (Celery, RQ).

### Why Polling Instead of WebSockets?

**Polling** was chosen for simplicity:
- No need for persistent connections
- Works with standard HTTP (no special server config)
- Easier to implement and debug
- 2-second polling is fast enough for MVP

Future enhancement could use WebSockets or Server-Sent Events for true real-time streaming.

### Why File-Based Storage?

**File storage** was chosen for simplicity:
- No database setup required
- Easy to inspect and debug (JSON files)
- Atomic writes prevent corruption
- Sufficient for single-machine deployment

Future enhancement could use SQLite or PostgreSQL for multi-user scenarios.

### Why Coarse-Grained Cancellation?

**Coarse cancellation** (checks between operations) was chosen because:
- Orchestrator code doesn't check cancellation flags mid-operation
- Fine-grained cancellation would require modifying `run_project()`
- Most runs complete within minutes (not worth complex cancellation)

Future enhancement could add cancellation checkpoints throughout the orchestrator.

## Limitations & Future Enhancements

### Current Limitations

1. **No concurrent limit** - Can run unlimited jobs simultaneously
2. **Coarse cancellation** - Can't stop mid-LLM-call
3. **No job queue** - Jobs start immediately (no priority/scheduling)
4. **No progress tracking** - Can't see % complete or ETA
5. **No job dependencies** - Can't chain jobs or trigger on completion
6. **Single-machine only** - No distributed execution

### Planned Enhancements

1. **Job Queue** - Add queuing, priorities, and concurrent limits
2. **Progress Tracking** - Show current iteration, % complete, ETA
3. **WebSocket Streaming** - Replace polling with true real-time logs
4. **Fine-Grained Cancellation** - Add checkpoints throughout orchestrator
5. **Job Dependencies** - Chain jobs, trigger on completion
6. **Distributed Execution** - Run jobs across multiple machines
7. **Job Analytics** - Charts, trends, success rates
8. **Job Templates** - Save and reuse common configurations

## Troubleshooting

### Jobs stuck in "queued" status

**Cause:** Background thread failed to start

**Fix:**
1. Check server logs for errors
2. Restart the web server
3. Manually mark job as failed if needed

---

### Logs not updating

**Cause:** Polling stopped or log file not writable

**Fix:**
1. Check browser console for JavaScript errors
2. Verify `run_logs/{job_id}/job.log` exists and is writable
3. Refresh the page to restart polling

---

### Job won't cancel

**Cause:** Job is in the middle of an operation

**Fix:**
1. Wait for current operation to complete (check logs)
2. Job will stop at next checkpoint
3. If stuck, restart the server (job will mark as "cancelled" on restart)

---

### "Job not found" error

**Cause:** Job state file corrupted or job was deleted

**Fix:**
1. Check `agent/jobs_state.json` exists and is valid JSON
2. Restore from backup if available
3. Jobs are recoverable from `run_logs/` directory

---

### Memory usage growing

**Cause:** Too many completed jobs in memory

**Fix:**
1. Restart the server periodically
2. Implement job archival (move old jobs to archive file)
3. Add job retention policy (auto-delete after N days)

## Migration from Stage 7

No migration needed! Stage 8 is fully backward compatible.

**What changed:**
- POST /run now creates background jobs instead of blocking
- New /jobs routes added
- New job_state.json file created

**What stayed the same:**
- All CLI functionality
- Old /run/{run_id} routes
- Existing run_logs/ structure
- project_config.json format

## Summary

Stage 8 transforms the web dashboard into a robust job manager:

✅ **Background execution** - UI stays responsive
✅ **Live log streaming** - Watch progress in real-time
✅ **Job list/detail pages** - Browse and monitor all jobs
✅ **Cancel support** - Stop jobs gracefully
✅ **Rerun capability** - Restart jobs easily
✅ **Full backward compatibility** - CLI and old routes still work

The system is now ready for production use with proper job tracking, monitoring, and control!
