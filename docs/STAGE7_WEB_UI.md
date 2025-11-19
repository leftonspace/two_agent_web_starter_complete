# Stage 7: Web Dashboard

**Stage 7** adds a local web interface for controlling and monitoring the multi-agent orchestrator. This provides a user-friendly alternative to the command-line interface while maintaining all existing functionality.

## Overview

The web dashboard provides:
- **Project selection** with visual configuration forms
- **Run control** to start orchestrator runs with custom parameters
- **Run history** with detailed logs and cost breakdowns
- **Live feedback** showing run results and iteration logs
- **RESTful API** for programmatic access

## Architecture

### Components

1. **`agent/runner.py`** - Programmatic API
   - `run_project(config)` - Run orchestrator with given configuration
   - `list_projects()` - List available projects in sites/
   - `list_run_history()` - List recent runs
   - `get_run_details(run_id)` - Get detailed run information

2. **`agent/webapp/`** - Web dashboard
   - `app.py` - FastAPI application with routes
   - `templates/` - Jinja2 HTML templates
   - `static/` - CSS, JavaScript (if needed)

3. **Routes**
   - `GET /` - Home page with form and history
   - `POST /run` - Start a new orchestrator run
   - `GET /run/{run_id}` - View run details
   - `GET /api/projects` - List projects (JSON)
   - `GET /api/history` - List run history (JSON)
   - `GET /api/run/{run_id}` - Get run details (JSON)
   - `GET /health` - Health check

### Design Principles

- **Backward compatibility** - CLI still works exactly as before
- **No breaking changes** - Existing orchestrator code unchanged
- **Minimal dependencies** - FastAPI, Jinja2, Uvicorn only
- **Production-safe** - All web features are optional
- **Clean separation** - Web layer doesn't modify core logic

## Installation

Install the required dependencies:

```bash
pip install fastapi jinja2 uvicorn
```

Or if you have a requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Starting the Web Dashboard

**Method 1: Direct execution**
```bash
cd agent/webapp
python app.py
```

**Method 2: Using uvicorn**
```bash
uvicorn agent.webapp.app:app --reload --host 127.0.0.1 --port 8000
```

**Method 3: Using Python module syntax**
```bash
python -m agent.webapp.app
```

The dashboard will be available at: **http://127.0.0.1:8000**

### Using the Web Interface

#### 1. Home Page

The home page displays:
- **Project selector** - Choose from available projects in `sites/`
- **Configuration form** - Set mode, rounds, costs, options
- **Run history** - Recent runs with status and costs

#### 2. Starting a Run

Fill out the form with:
- **Project** - Select from dropdown (auto-populated from sites/)
- **Mode** - Choose 2-loop or 3-loop
- **Task** - Describe what to build
- **Max Rounds** - Number of iteration cycles (typically 1-5)
- **Cost Limit** - Hard stop if exceeded (USD)
- **Cost Warning** - Show warning threshold (USD)
- **Visual Review** - Enable DOM analysis and screenshots
- **Git Integration** - Commit changes after each iteration

Click "Start Run" to execute. The page will block until the run completes, then redirect to the run detail page.

#### 3. Viewing Run Details

The run detail page shows:
- **Run metadata** - ID, project, mode, timestamps
- **Configuration** - All settings used for the run
- **Cost breakdown** - Estimated vs actual, per-model usage
- **Iteration log** - Detailed timeline with status and notes
- **Raw JSON** - Complete run data for debugging

#### 4. Run History

The home page lists recent runs with:
- Run ID (clickable link)
- Project name
- Mode (2loop/3loop)
- Status (color-coded badge)
- Rounds completed
- Total cost
- Start time

### Using the Programmatic API

You can also use the runner API directly in Python code:

```python
from agent.runner import run_project, list_projects, list_run_history

# List available projects
projects = list_projects()
print(f"Found {len(projects)} projects")

# Configure and run a project
config = {
    "mode": "3loop",
    "project_subdir": "my_project",
    "task": "Build a landing page with hero section and contact form",
    "max_rounds": 3,
    "max_cost_usd": 1.5,
    "cost_warning_usd": 0.8,
    "use_visual_review": True,
    "use_git": True,
    "interactive_cost_mode": "off",
    "prompts_file": "prompts_default.json",
}

# Run the orchestrator
run_summary = run_project(config)

print(f"Run completed: {run_summary.run_id}")
print(f"Final status: {run_summary.final_status}")
print(f"Total cost: ${run_summary.cost_summary['total_usd']:.4f}")

# List run history
history = list_run_history(limit=10)
for run in history:
    print(f"{run['run_id']}: {run['final_status']} (${run['cost_summary']['total_usd']:.4f})")
```

## Configuration

### Project Structure

Projects must exist under `sites/` directory:

```
sites/
├── my_project/         # Your project
│   ├── index.html
│   └── style.css
├── another_project/    # Another project
└── fixtures/          # (Auto-generated test content, ignored)
```

### Run Logs

Run logs are stored in `run_logs/<run_id>/`:

```
run_logs/
├── abc123/
│   └── run_summary.json    # Complete run data
├── def456/
│   └── run_summary.json
└── ...
```

Each `run_summary.json` contains:
- Run metadata (ID, timestamps, mode, project)
- Configuration used
- Iteration logs with status and notes
- Cost breakdown (estimated and actual)
- Final status and results

## API Reference

### `run_project(config: dict) -> RunSummary`

Run the orchestrator with the given configuration.

**Args:**
- `config` (dict): Configuration with keys:
  - `mode` (str): "2loop" or "3loop"
  - `project_subdir` (str): Folder name under sites/
  - `task` (str): Task description
  - `max_rounds` (int): Maximum iterations
  - `use_visual_review` (bool): Enable DOM analysis
  - `use_git` (bool): Enable git commits
  - `max_cost_usd` (float): Cost limit
  - `cost_warning_usd` (float): Warning threshold
  - `interactive_cost_mode` (str): "off", "once", or "always"
  - `prompts_file` (str): Prompts JSON file name

**Returns:**
- `RunSummary`: Complete run results

**Raises:**
- `ValueError`: Invalid configuration
- `FileNotFoundError`: Project directory not found
- `Exception`: Orchestrator error

### `list_projects() -> list[dict]`

List all available projects in the sites/ directory.

**Returns:**
- List of dicts with keys:
  - `name` (str): Project folder name
  - `path` (str): Full path to project
  - `exists` (bool): True if directory exists
  - `file_count` (int): Number of files in project

### `list_run_history(limit: int = 50) -> list[dict]`

List recent runs from the run_logs/ directory.

**Args:**
- `limit` (int): Maximum number of runs to return (default 50)

**Returns:**
- List of run summary dicts, sorted by start time (newest first)

### `get_run_details(run_id: str) -> dict | None`

Get detailed information about a specific run.

**Args:**
- `run_id` (str): Run identifier

**Returns:**
- Run summary dict, or None if run not found

## Testing

Run the Stage 7 tests:

```bash
# Run all Stage 7 tests
pytest agent/tests_stage7/

# Run specific test file
pytest agent/tests_stage7/test_runner.py
pytest agent/tests_stage7/test_webapp.py

# Run with verbose output
pytest agent/tests_stage7/ -v
```

Tests cover:
- Runner API functions (list_projects, list_history, get_run_details)
- Web routes (home, start run, view run details)
- API endpoints (JSON responses)
- Error handling (missing fields, invalid config, not found)

## Limitations & Future Enhancements

### Current Limitations

1. **Blocking execution** - The web UI blocks until the run completes
2. **No live progress** - Can't see iterations in real-time
3. **No run cancellation** - Can't stop a running orchestrator
4. **No authentication** - Web dashboard is unprotected (local only)
5. **Single instance** - Can't run multiple orchestrators concurrently

### Planned Enhancements

1. **Background execution** - Run orchestrator in background task
2. **WebSocket support** - Stream live progress updates
3. **Run control** - Pause/resume/cancel running orchestrators
4. **Multi-user support** - Authentication and user sessions
5. **Run comparison** - Compare results across multiple runs
6. **Cost analytics** - Charts and trends for token usage
7. **Project templates** - Quick-start templates for common tasks

## Troubleshooting

### Port already in use

If port 8000 is already taken:

```bash
uvicorn agent.webapp.app:app --reload --port 8001
```

### Module import errors

Ensure you're running from the project root:

```bash
cd /path/to/two_agent_web_starter_complete
python -m agent.webapp.app
```

### Templates not found

The webapp looks for templates relative to `agent/webapp/templates/`. Ensure:
- You're running from the project root, OR
- The `templates_dir` path in `app.py` is correct

### Run logs missing

Run logs are stored in `run_logs/` at the project root. If missing:
- Check that `run_mode.py` or `runner.py` completed successfully
- Verify write permissions on the `run_logs/` directory

## Integration with Existing Workflows

### CLI still works

The existing CLI entry point is unchanged:

```bash
# Original CLI usage
cd agent
python run_mode.py
```

### Dev tools integration

The web dashboard complements existing dev tools:

```bash
# Generate fixture for testing
python make.py fixture

# Run via web UI
python -m agent.webapp.app

# View logs (command-line)
python dev/view_logs.py --latest

# View logs (web UI)
# Visit http://127.0.0.1:8000
```

### Auto-pilot mode

Auto-pilot mode (STAGE 4) still works from CLI. Future enhancement will add web UI support for auto-pilot sessions.

## Design Decisions

### Why FastAPI?

- **Modern Python** - Async support, type hints, automatic docs
- **Minimal** - Lightweight, no heavy framework overhead
- **Well-documented** - Easy to extend and maintain
- **Fast** - Good performance for local dashboard

### Why not Flask?

Flask would also work well. FastAPI was chosen for:
- Built-in Pydantic validation
- Automatic OpenAPI/Swagger docs
- Modern async/await support
- Better type safety

### Why blocking execution?

The current implementation blocks during run execution for simplicity. This is acceptable for Stage 7 MVP because:
- Runs typically complete in minutes
- Local-only usage (no concurrent users)
- Easier to implement and test
- Future enhancement can add background tasks

### Why no database?

Run logs are stored as JSON files instead of a database because:
- Simple file-based storage is sufficient for MVP
- No additional dependencies required
- Easy to inspect and debug
- Compatible with existing run_logger.py
- Can migrate to database later if needed

## Summary

Stage 7 adds a clean, functional web dashboard while preserving all existing CLI and scripting workflows. The programmatic `run_project()` API enables future automation and integration possibilities. The web UI makes the orchestrator more accessible to non-technical users and provides better visibility into run history and costs.

**Key takeaways:**
- 🌐 Web dashboard at http://127.0.0.1:8000
- 🐍 Programmatic API via `runner.py`
- 🔄 Full backward compatibility with CLI
- 📊 Run history and detailed logs
- 💰 Cost tracking and breakdowns
- ✅ Comprehensive test coverage

---

## Phase 1.1: Authentication & Security

**Added:** November 2025  
**Status:** Implemented

The web dashboard now includes comprehensive authentication and authorization to secure access to the orchestrator system.

### Overview

Authentication provides:
- **API Key authentication** for programmatic access
- **Session-based authentication** for web UI users
- **Role-based access control** (admin, developer, viewer)
- **API key management** (generation, rotation, revocation)
- **CSRF protection** for state-changing operations

### User Roles

Three user roles with different permission levels:

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: manage API keys, users, system configuration, start jobs, view analytics |
| **Developer** | Start jobs, cancel jobs, run QA, view analytics, modify projects |
| **Viewer** | Read-only: view jobs, analytics, logs (cannot start or modify) |

Role hierarchy: **Admin > Developer > Viewer**

### Authentication Methods

#### 1. API Key Authentication

For programmatic access (scripts, CI/CD, external tools):

```bash
# Use X-API-Key header
curl -H "X-API-Key: sk_your_api_key_here" http://localhost:8000/api/jobs

# Example: Start a run via API
curl -X POST http://localhost:8000/run \
  -H "X-API-Key: sk_your_api_key_here" \
  -F "project_subdir=my_project" \
  -F "mode=3loop" \
  -F "task=Build landing page" \
  -F "max_rounds=3"
```

#### 2. Session-Based Authentication

For web UI access:

1. Navigate to `http://localhost:8000/auth/login`
2. Enter your username and API key
3. Get a session cookie (expires after 24 hours by default)
4. Use the web UI normally

### Configuration

Add auth configuration to `project_config.json`:

```json
{
  "auth": {
    "enabled": true,
    "session_ttl_hours": 24,
    "api_key_ttl_days": 90,
    "require_https": true,
    "allow_registration": false,
    "create_default_admin_key": true
  }
}
```

**Configuration Options:**

- `enabled` (bool): Enable/disable authentication (default: true)
- `session_ttl_hours` (int): Session expiration time in hours (default: 24)
- `api_key_ttl_days` (int): Default API key expiration in days (default: 90, 0 = no expiration)
- `require_https` (bool): Enforce HTTPS for cookies in production (default: true)
- `allow_registration` (bool): Allow self-registration (default: false)
- `create_default_admin_key` (bool): Generate admin key on first run (default: true)

**Development Mode:**

To disable authentication for development:

```json
{
  "auth": {
    "enabled": false
  }
}
```

⚠️ **Warning:** Only disable auth in development environments!

### First-Time Setup

When you first start the web dashboard with authentication enabled:

1. **Default admin key is generated automatically:**

```bash
python -m uvicorn agent.webapp.app:app --reload
```

Output:
```
============================================================
🔐 DEFAULT ADMIN API KEY GENERATED
============================================================
API Key: sk_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890
User ID: admin
Role: admin

⚠️  SAVE THIS KEY NOW - IT WILL NOT BE SHOWN AGAIN!
============================================================
```

2. **Save this API key securely** (password manager, secrets vault)
3. **Use it to log in** or make API requests

### API Key Management

#### Generate New Keys (Admin Only)

**Via Web UI:**
1. Navigate to `http://localhost:8000/api/keys/`
2. Fill out the form:
   - User ID: `john_doe`
   - Username: `John Doe`
   - Role: `developer`
   - TTL Days: `90`
   - Description: `John's API key`
3. Click "Generate Key"
4. **Copy the key immediately** (shown only once!)

**Via API:**

```bash
curl -X POST http://localhost:8000/api/keys/generate \
  -H "X-API-Key: sk_your_admin_key" \
  -F "user_id=john_doe" \
  -F "username=John Doe" \
  -F "role=developer" \
  -F "ttl_days=90" \
  -F "description=John's API key"
```

#### List Keys

```bash
curl -H "X-API-Key: sk_your_admin_key" \
  http://localhost:8000/api/keys/list
```

#### Revoke Key

```bash
curl -X POST http://localhost:8000/api/keys/{key_id}/revoke \
  -H "X-API-Key: sk_your_admin_key"
```

#### Delete Key

```bash
curl -X DELETE http://localhost:8000/api/keys/{key_id} \
  -H "X-API-Key: sk_your_admin_key"
```

### Protected Endpoints

Routes requiring authentication:

| Endpoint | Required Role | Description |
|----------|--------------|-------------|
| `POST /run` | Developer | Start orchestrator run |
| `POST /jobs/{id}/rerun` | Developer | Rerun a job |
| `POST /api/jobs/{id}/cancel` | Developer | Cancel running job |
| `POST /api/jobs/{id}/qa` | Developer | Run QA checks |
| `POST /api/auto-tune/toggle` | Admin | Toggle auto-tune |
| `GET /api/keys/` | Admin | View API keys management |
| `POST /api/keys/generate` | Admin | Generate new API key |
| `POST /api/keys/{id}/revoke` | Admin | Revoke API key |
| `DELETE /api/keys/{id}` | Admin | Delete API key |

Public endpoints (no auth required):
- `GET /` - Home page
- `GET /auth/login` - Login page
- `POST /auth/login` - Login action
- `GET /health` - Health check

### Security Features

#### 1. Bcrypt Password Hashing

- API keys are hashed with bcrypt before storage
- Never stored in plain text
- Secure work factor: 12 rounds (configurable)

#### 2. CSRF Protection

- All state-changing operations (POST/PUT/DELETE) require CSRF token
- CSRF tokens are session-specific
- Tokens automatically included in forms

#### 3. Session Security

- Secure cookies (HTTPS-only in production)
- HttpOnly cookies (JavaScript cannot access)
- SameSite=lax (CSRF protection)
- Configurable expiration (default: 24 hours)

#### 4. API Key Best Practices

- Keys use `sk_` prefix (similar to OpenAI format)
- Cryptographically secure random generation
- Expiration dates enforced
- Last-used timestamp tracked for auditing

### Database

API keys are stored in SQLite database: `data/api_keys.db`

**Schema:**

```sql
CREATE TABLE api_keys (
    key_id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL,
    user_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    last_used TEXT,
    revoked INTEGER DEFAULT 0,
    description TEXT
)
```

**Backup:**

```bash
# Backup API keys database
cp data/api_keys.db data/api_keys.backup.db

# Restore from backup
cp data/api_keys.backup.db data/api_keys.db
```

### Testing

Run authentication tests:

```bash
# Run all auth tests
pytest agent/tests_stage7/test_auth.py -v

# Run specific test
pytest agent/tests_stage7/test_auth.py::test_api_key_authentication -v

# Run with coverage
pytest agent/tests_stage7/test_auth.py --cov=agent.webapp.auth --cov-report=html
```

**Test Coverage:**
- API key generation and verification
- Session creation and expiration
- Role-based access control
- Login/logout flow
- API key management endpoints
- 25+ test cases

### Troubleshooting

#### "Authentication required" error

**Cause:** No API key provided or invalid key

**Solution:**
```bash
# Check if auth is enabled in config
cat project_config.json | grep -A 5 '"auth"'

# Verify your API key works
curl -H "X-API-Key: sk_your_key" http://localhost:8000/auth/status
```

#### Default admin key not shown

**Cause:** Key already exists from previous run

**Solution:**
```bash
# List existing keys
python -c "
from agent.webapp.api_keys import get_api_key_manager
manager = get_api_key_manager()
keys = manager.list_keys()
for key in keys:
    print(f'{key[\"key_id\"]}: {key[\"username\"]} ({key[\"role\"]})')
"
```

#### Cannot access /api/keys

**Cause:** Not using admin API key

**Solution:** Only admin role can manage API keys. Use admin key or have an admin generate a key for you.

#### Session expired

**Cause:** Session TTL exceeded (default: 24 hours)

**Solution:** Log in again at `/auth/login`

### Migration from Unauthenticated

If upgrading from a version without authentication:

1. **Backup your data:**
   ```bash
   cp -r data/ data.backup/
   ```

2. **Start the server** - default admin key will be generated

3. **Save the admin key** displayed in console

4. **Update automation/scripts** to include API key header:
   ```bash
   # Old (no auth)
   curl http://localhost:8000/api/jobs

   # New (with auth)
   curl -H "X-API-Key: sk_your_key" http://localhost:8000/api/jobs
   ```

5. **Generate keys for team members:**
   - Admins get `admin` role
   - Developers get `developer` role
   - Viewers get `viewer` role

### Security Checklist

Before deploying to production:

- [ ] Change default admin key
- [ ] Enable `require_https: true`
- [ ] Set `allow_registration: false`
- [ ] Use environment variables for sensitive config
- [ ] Regularly rotate API keys
- [ ] Monitor `last_used` timestamps
- [ ] Review and revoke unused keys
- [ ] Enable HTTPS on your server
- [ ] Set appropriate session TTL for your security requirements
- [ ] Backup `data/api_keys.db` regularly

### Best Practices

1. **Key Management:**
   - Rotate keys every 90 days
   - Use different keys for different services
   - Revoke keys immediately when team members leave
   - Never commit keys to version control

2. **Role Assignment:**
   - Follow principle of least privilege
   - Start with viewer role, escalate as needed
   - Admin role only for key managers

3. **Session Management:**
   - Logout when using shared computers
   - Clear browser cache on public computers
   - Use shorter TTL for sensitive environments

4. **Monitoring:**
   - Review `last_used` timestamps regularly
   - Alert on admin key usage
   - Log authentication failures

### API Reference

#### Authentication Status

```bash
GET /auth/status
```

**Response:**
```json
{
  "authenticated": true,
  "user_id": "john_doe",
  "username": "John Doe",
  "role": "developer"
}
```

#### Login

```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=john_doe&api_key=sk_your_key_here
```

**Response:** Redirect to `/` with session cookie

#### Logout

```bash
POST /auth/logout
```

**Response:** Redirect to `/auth/login` with cookie cleared

---

## Summary

Phase 1.1 adds enterprise-grade authentication to the web dashboard, enabling secure multi-user access with role-based permissions. The system is backward-compatible and can be disabled for development environments.

**Key Features:**
- ✅ API key authentication
- ✅ Session-based web UI auth
- ✅ Role-based access control (admin/developer/viewer)
- ✅ CSRF protection
- ✅ Bcrypt password hashing
- ✅ Secure session management
- ✅ API key lifecycle management
- ✅ Comprehensive test coverage (25+ tests)

**Next Steps:** See `docs/IMPLEMENTATION_PROMPTS_PHASES_1_5.md` for remaining Phase 1 security improvements.
