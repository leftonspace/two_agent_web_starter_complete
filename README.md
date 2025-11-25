# Two-Agent Web Starter (Complete)

A multi-agent AI orchestrator system for building web projects autonomously. This system uses multiple AI agents (Manager, Supervisor, Employee) working together to plan, build, and iterate on web projects.

## Features

### Core Orchestration (Stages 0-3)
- **2-loop mode**: Manager ↔ Employee direct collaboration
- **3-loop mode**: Manager ↔ Supervisor ↔ Employee with task phasing
- **Git integration**: Automatic commits after each iteration
- **Visual review**: DOM analysis and screenshot capture
- **Cost control**: Token tracking, warnings, and hard caps
- **Interactive gating**: Approve costs before execution

### Advanced Features (Stages 4-6)
- **Auto-pilot mode**: Multiple sub-runs with self-evaluation
- **Safety checks**: Static analysis, dependency scanning, execution safety
- **Run logging**: Structured JSON logs for all runs and sessions
- **Developer tools**: Helper scripts for common tasks
- **VSCode integration**: Debug configs and build tasks
- **Documentation**: Auto-generated API reference

### Web Dashboard (Stage 7-11) 🆕
- **Visual interface**: Clean web UI for project management
- **Background jobs**: Non-blocking execution with live progress ✨
- **Job management**: List, view, cancel, and rerun jobs ✨
- **Live log streaming**: Watch logs update in real-time ✨
- **Project explorer**: Browse files, view snapshots, compare versions ✨
- **Diff viewer**: Interactive comparison between iterations ✨
- **Quality assurance**: Automated quality checks with configurable gates ✨
- **QA dashboard**: View quality status, issues, and metrics ✨
- **Analytics dashboard**: Comprehensive metrics, trends, and insights ✨
- **Cost analytics**: Track spending, budgets, and model costs ✨
- **Performance metrics**: Duration, token usage, and efficiency trends ✨
- **Data export**: Download analytics as JSON or CSV ✨
- **Run history**: Browse past runs with detailed logs
- **Cost tracking**: View token usage and cost breakdowns
- **RESTful API**: Programmatic access to all features

### Conversational Agent (Phase 7.1) 🚀
- **Natural language interface**: Chat with the system instead of writing mission files ✨
- **Intent understanding**: Automatically parses requests and selects appropriate tools ✨
- **Multi-step planning**: Breaks complex tasks into executable steps ✨
- **Background execution**: Long-running tasks execute asynchronously ✨
- **Web chat UI**: Interactive chat interface at `/chat` ✨
- **CLI chat mode**: Command-line chat with `/status`, `/task`, `/help` commands ✨
- **Task tracking**: Monitor active tasks and their progress in real-time ✨
- **Context awareness**: Maintains conversation history for better understanding ✨

### Action Execution Tools (Phase 7.4) 🎯
- **Domain purchase**: Buy domains via Namecheap API with approval workflow ✨
- **Website deployment**: Deploy to Vercel (auto-creates GitHub repo, pushes code, deploys) ✨
- **SMS messaging**: Send SMS via Twilio for notifications and alerts ✨
- **Payment processing**: Accept payments via Stripe with refund support ✨
- **Approval workflows**: User approval required for paid or risky actions ✨
- **Cost estimation**: Know the cost before executing any action ✨
- **Rollback support**: Undo actions when possible (refunds, deletions) ✨
- **Risk assessment**: LOW/MEDIUM/HIGH/CRITICAL risk levels with 2FA for critical actions ✨
- **Audit logging**: Complete trail of all action attempts and approvals ✨
- **Dry-run mode**: Test actions without actually executing them ✨

### Meeting Platform Integration (Phase 7A.1) 🎤
- **Zoom integration**: Join Zoom meetings as a participant, capture audio streams ✨
- **Microsoft Teams**: Join Teams meetings via Graph API with audio capture ✨
- **Live audio capture**: Record in-person meetings using microphone (PyAudio) ✨
- **Participant management**: List meeting participants and their status ✨
- **Chat integration**: Send messages to meeting chat automatically ✨
- **Platform abstraction**: Uniform API across Zoom, Teams, and live audio ✨
- **Privacy compliance**: Configurable recording announcements and consent handling ✨
- **Meeting lifecycle**: Connect → Join → Capture → Transcribe → Leave workflow ✨

### Real-Time Speech Transcription (Phase 7A.2) 🎙️
- **Multi-provider support**: Deepgram (streaming), OpenAI Whisper (batch), Google, Azure ✨
- **Automatic failover**: Switches to backup provider if primary fails ✨
- **True streaming**: <100ms latency with Deepgram WebSocket streaming ✨
- **High accuracy**: Best-in-class accuracy with OpenAI Whisper ✨
- **Punctuation**: Automatic punctuation and capitalization ✨
- **Multi-language**: Supports 99+ languages (Whisper), 36+ languages (Deepgram) ✨
- **Interim results**: Real-time interim transcripts before final results ✨
- **Confidence scores**: Quality metrics for each transcript segment ✨
- **Latency optimization**: <2s for Whisper, <100ms for Deepgram ✨

### Speaker Diarization (Phase 7A.3) 👥
- **Speaker segmentation**: Identifies who spoke when in meetings (95%+ accuracy) ✨
- **Voice fingerprinting**: Creates 512-dimensional voice embeddings for recognition ✨
- **Speaker identification**: Matches voices to known speakers across meetings ✨
- **Platform integration**: Combines voice data with Zoom/Teams participant lists ✨
- **Speaker mapping**: Maps anonymous speaker IDs to actual people ✨
- **Transcript attribution**: Combines transcripts with speaker information ✨
- **Known speaker database**: Registers speakers with voice samples for future meetings ✨
- **Pyannote.audio**: State-of-the-art deep learning models for diarization ✨
- **Automatic speaker count**: Detects number of speakers from meeting participants ✨
- **Speaker statistics**: Tracks who spoke, when, and for how long ✨

### Meeting Intelligence & Real-Time Action (Phase 7A.4) 🧠
- **Action item extraction**: Automatically identifies tasks from meeting discussion ✨
- **Decision tracking**: Captures decisions with rationale and alternatives considered ✨
- **Question identification**: Tracks questions needing answers (answered/unanswered) ✨
- **Real-time analysis**: Analyzes transcripts every 30 seconds during meetings ✨
- **Smart execution**: Executes simple, safe tasks immediately during meetings ✨
- **Meeting context**: Accumulates topics, decisions, and action items throughout session ✨
- **Action types**: Query data, search info, create documents, send messages, schedule meetings ✨
- **Chat integration**: Announces actions in meeting chat for transparency ✨
- **Meeting summaries**: Generates comprehensive summaries with action items, decisions, questions ✨
- **Safety controls**: Configurable limits on actions per meeting and confirmation requirements ✨

### Execution Strategy Decider (Phase 7B.1) 🎯
- **Intelligent strategy selection**: Analyzes tasks to choose optimal execution approach ✨
- **4 execution modes**: Direct (JARVIS solo), Reviewed (Employee+Supervisor), Full Loop (Manager+Employee+Supervisor), Human Approval ✨
- **Complexity analysis**: Scores tasks 0-10 based on code generation, APIs, file changes, steps ✨
- **Risk assessment**: Evaluates production impact, reversibility, security, downtime risk ✨
- **Cost estimation**: Predicts LLM API costs before execution ✨
- **Manual overrides**: Predefined patterns for known tasks (deploy→approval, query→direct) ✨
- **Urgency handling**: Immediate tasks skip review (unless high risk) ✨
- **Conservative by default**: Overestimates complexity/risk for safety ✨
- **Decision rationale**: Explains why each strategy was chosen ✨
- **Timeout suggestions**: Recommends appropriate timeouts per complexity level ✨

### Direct Execution Mode (Phase 7B.2) ⚡
- **Fast path execution**: JARVIS executes simple tasks immediately without multi-agent review ✨
- **7 action types**: query_database, search_info, create_document, send_message, calculate, api_call, read ✨
- **Safety-first design**: Only whitelisted actions, read-only by default ✨
- **Database safety**: Blocks UPDATE, DELETE, INSERT, DROP, ALTER, CREATE - allows SELECT only ✨
- **API safety**: Blocks POST, PUT, PATCH, DELETE - allows GET and HEAD only ✨
- **File safety**: Blocks access to system directories (/etc, /sys, /proc, C:\Windows) ✨
- **Timeout protection**: 30-second max execution time prevents hung tasks ✨
- **Automatic validation**: Validates results before returning ✨
- **LLM-powered planning**: Uses GPT-4o-mini for fast action planning ✨
- **Error handling**: Graceful failures with detailed error messages ✨

### Task Routing Logic (Phase 7B.3) 🚦
- **Unified entry point**: Single TaskRouter handles all task execution ✨
- **6 task statuses**: PENDING, ROUTING, EXECUTING, COMPLETED, FAILED, REQUIRES_APPROVAL ✨
- **Automatic routing**: Routes to Direct, Reviewed, or Full Loop based on strategy ✨
- **Retry with escalation**: Failed tasks automatically retry at higher execution mode ✨
- **Smart escalation**: Direct → Reviewed → Full Loop on failure ✨
- **Human approval workflow**: High-risk tasks pause for approval before execution ✨
- **Task tracking**: Monitors all active tasks with real-time status updates ✨
- **Pending approvals**: Lists all tasks awaiting human approval ✨
- **Task lifecycle management**: Complete lifecycle from routing to completion ✨
- **Memory management**: Automatically clears old completed tasks to prevent bloat ✨

### Employee AI Pool Management (Phase 7C.1) 🔄
- **Multi-agent parallelism**: Pool of Employee agents executing tasks concurrently ✨
- **5 specialties**: Coding, Documents, Data Analysis, Communications, General ✨
- **Specialty-based assignment**: Matches tasks to workers with appropriate expertise ✨
- **Load balancing**: Distributes tasks evenly across available workers ✨
- **Task queueing**: Queues tasks when all workers busy, processes when idle ✨
- **Parallel batch execution**: Execute multiple tasks simultaneously for speed ✨
- **Worker health monitoring**: Tracks status (idle, busy, error) for each worker ✨
- **Performance statistics**: Tasks completed, execution time, error count per worker ✨
- **Auto-specialty detection**: Analyzes task description to determine best specialty ✨
- **Background queue processor**: Continuously monitors queue and assigns to idle workers ✨
- **Configurable pool size**: Scale from 1 to 50+ workers based on workload ✨
- **Graceful degradation**: Handles worker errors without disrupting pool operations ✨

### Parallel Task Distribution (Phase 7C.2) 📊
- **Priority-based queue**: 4 priority levels (URGENT, HIGH, MEDIUM, LOW) with intelligent scheduling ✨
- **Dependency tracking**: Tasks wait for dependencies to complete before execution ✨
- **Dependency chains**: Support for complex dependency graphs (C→B→A) ✨
- **Load balancing**: Optimal distribution across workers based on current load ✨
- **Worker affinity**: Related tasks assigned to same worker for better context ✨
- **Batch optimization**: Groups similar tasks for efficient parallel execution ✨
- **Deadline-aware scheduling**: Tasks approaching deadline get priority boost ✨
- **Priority inheritance**: Tasks inherit priority from dependent tasks ✨
- **Async distribution**: Non-blocking task submission and result retrieval ✨
- **Queue statistics**: Real-time metrics on pending, completed, and failed tasks ✨
- **Configurable batching**: Toggle batch optimization and set batch timeouts ✨
- **Graceful error handling**: Failed tasks don't block queue or dependent tasks ✨

### Supervisor Review Queue (Phase 7C.3) ✅
- **Automated quality gates**: 4-gate validation (correctness, safety, performance, code quality) ✨
- **Auto-approval for low-risk work**: Safe work passing all gates approved automatically ✨
- **Risk-based processing**: 4 risk levels (LOW, MEDIUM, HIGH, CRITICAL) with different handling ✨
- **Batch review processing**: Similar work types reviewed together for efficiency ✨
- **Smart escalation**: CRITICAL risk or quality failures escalated to Manager ✨
- **Work type classification**: 8 work types (code, documents, data, API, database, files, communications, other) ✨
- **Comprehensive metrics**: Approval rate, rejection rate, escalation rate, avg review time ✨
- **Safety validation**: Blocks dangerous operations (DROP TABLE, system file access) ✨
- **Performance checks**: Flags slow operations (>30s execution time) ✨
- **Code quality analysis**: Validates code structure and completeness ✨
- **Async review processing**: Non-blocking submission and result retrieval ✨
- **Configurable thresholds**: Set auto-approval risk threshold and batch timeouts ✨

### Code Execution Engine (Phase 8.1) 🚀
- **Multi-language support**: Python, JavaScript (Node.js), and shell command execution ✨
- **Sandboxed execution**: Isolated subprocess execution for security ✨
- **Import validation**: Whitelist of safe Python modules, dangerous modules blocked ✨
- **Shell command whitelist**: Only safe read-only commands allowed (ls, cat, grep, etc.) ✨
- **Timeout protection**: Configurable execution timeout (default 30s, max 5min) ✨
- **Output capture**: Captures stdout, stderr, and return codes ✨
- **Security validation**: Pre-execution checks for dangerous patterns ✨
- **Resource limits**: Memory and CPU limits (max 1GB memory) ✨
- **Dangerous pattern blocking**: Blocks eval(), exec(), subprocess, file operations ✨
- **Network isolation**: Network access disabled by default ✨
- **Automatic cleanup**: Temp files automatically deleted after execution ✨
- **Comprehensive logging**: All execution attempts logged with violations ✨

### API Integration System (Phase 8.2) 🌐
- **Universal HTTP client**: Support for all REST APIs with httpx ✨
- **All HTTP methods**: GET, POST, PUT, PATCH, DELETE with clean async API ✨
- **5 authentication types**: API Key, Bearer, Basic, OAuth 2.0, JWT ✨
- **Exponential backoff retry**: Automatic retry on 429, 503, 504 errors ✨
- **Configurable retries**: Max retry attempts (default 3) with backoff (1s, 2s, 4s) ✨
- **Token bucket rate limiting**: Prevents API overload with configurable rates ✨
- **Automatic JSON handling**: Parse JSON responses, fallback to text ✨
- **Request statistics**: Track request count, error count, success rate ✨
- **Timeout protection**: Configurable request timeout (default 30s) ✨
- **Context manager support**: Clean resource management with async context ✨
- **Flexible authentication**: Per-request header override support ✨
- **Comprehensive logging**: All requests logged with timing and status ✨

### File System Operations (Phase 8.3) 📁
- **Workspace restrictions**: All operations confined to workspace directory ✨
- **Path validation**: Prevents directory traversal attacks (../, absolute paths) ✨
- **System file protection**: Blocks access to /etc, /sys, /proc, Windows system dirs ✨
- **Async file I/O**: Non-blocking read/write operations with aiofiles ✨
- **Directory operations**: Create, delete, list directories with recursion support ✨
- **File management**: Read, write, append, copy, move, delete files ✨
- **Glob patterns**: List files with wildcard patterns (*.py, **/*.txt) ✨
- **File metadata**: Get size, timestamps, type information ✨
- **Size limits**: Configurable max file size (default 10MB) ✨
- **Git integration**: Full repository management (init, commit, push, branches) ✨
- **Git operations**: Add, commit, push, pull, branch management, status, diff, log ✨
- **Safe git commands**: All git operations through validated async subprocess calls ✨

### Database Operations (Phase 8.4) 🗄️
- **Connection pooling**: SQLAlchemy async engine with configurable pool size ✨
- **Read-only mode**: Default read-only mode blocks write operations (UPDATE, INSERT, DELETE) ✨
- **Multiple databases**: Support for PostgreSQL, MySQL, and SQLite ✨
- **Query validation**: Automatic detection of read-only vs write queries ✨
- **Parameter binding**: Prevents SQL injection through parameter substitution ✨
- **Transaction support**: Async context manager for transaction management ✨
- **Query timeout**: Configurable timeout protection (default 30s) ✨
- **Result pagination**: Built-in LIMIT/OFFSET support with metadata ✨
- **Connection management**: Async context manager for automatic cleanup ✨
- **Query helpers**: query(), query_one(), query_value(), query_paginated() ✨
- **Statistics tracking**: Request count, error tracking, success rate ✨
- **Comprehensive logging**: All queries logged with parameters and results ✨

### Self-Optimization (Stage 12) 🆕
- **Project profiling**: Historical behavior analysis per project ✨
- **Intelligent recommendations**: Data-driven optimization suggestions ✨
- **Prompt strategies**: A/B testing for different prompt sets ✨
- **Auto-tuning**: Automatic application of recommendations ✨
- **Confidence scoring**: High/medium/low confidence levels ✨
- **Safety mechanisms**: Minimum data requirements and graceful fallbacks ✨
- **Tuning dashboard**: View recommendations and control auto-tune ✨
- **Quality-first optimization**: 70/30 QA vs cost weighting ✨

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd two_agent_web_starter_complete

# Install dependencies
pip install -r requirements.txt

# Install web dashboard dependencies
pip install fastapi jinja2 uvicorn
```

### 2. Choose Your Interface

#### Option A: Web Dashboard (Recommended)

```bash
# Start the web server
python -m agent.webapp.app

# Open your browser to:
# http://127.0.0.1:8000
```

Then:
1. Select a project from the dropdown
2. Configure mode (2loop or 3loop), rounds, and costs
3. Enter your task description
4. Click "Start Run"
5. View results and history

#### Option B: Conversational Chat (New! 🚀)

Chat naturally with the system without writing mission files:

**Web Chat:**
```bash
# Start web server
python -m agent.webapp.app

# Navigate to http://127.0.0.1:8000/chat
```

Then chat naturally:
```
You: Format the code in src/
Agent: ✓ Code formatted successfully

You: Run the test suite
Agent: ✓ 47 tests passed

You: Create a portfolio website
Agent: I'll build that! Working on 5 steps...
```

**CLI Chat:**
```bash
python -m agent.cli_chat
```

See [docs/CONVERSATIONAL_AGENT.md](docs/CONVERSATIONAL_AGENT.md) for full guide.

#### Option C: Command Line

```bash
cd agent
python run_mode.py
```

Configure your run in `agent/project_config.json`:

```json
{
  "project_name": "My Website",
  "project_subdir": "my_project",
  "task": "Build a modern landing page with hero section",
  "max_rounds": 3,
  "mode": "3loop",
  "use_visual_review": true,
  "use_git": true,
  "max_cost_usd": 1.5,
  "cost_warning_usd": 0.8
}
```

### 3. View Results

**Web UI:**
- Browse to http://127.0.0.1:8000
- Click on a run ID to see details

**Command Line:**
```bash
# View logs in browser
python dev/view_logs.py --latest

# Or check JSON directly
cat run_logs/<run_id>/run_summary.json
```

## Project Structure

```
two_agent_web_starter_complete/
├── .env.example                           # Environment variables template
├── .githooks/                             # Git hooks
│   └── pre-commit                         # Pre-commit validation hook
├── .github/                               # GitHub configuration
│   └── workflows/
│       └── tests.yml                      # CI/CD test workflow
├── .gitignore                             # Git ignore rules
├── .vscode/                               # VSCode configuration
│   ├── launch.json                        # Debug configurations
│   └── tasks.json                         # Build tasks
├── agent/                                 # Core orchestrator code
│   ├── _errors.py                         # Error definitions
│   ├── actions/                           # Action execution modules
│   │   ├── __init__.py
│   │   ├── api_client.py                  # Universal HTTP client
│   │   ├── code_executor.py               # Multi-language code execution
│   │   ├── db_client.py                   # Database operations
│   │   ├── file_ops.py                    # File system operations
│   │   ├── git_ops.py                     # Git repository operations
│   │   ├── rate_limiter.py                # API rate limiting
│   │   └── sandbox.py                     # Sandboxed execution
│   ├── admin/                             # Administrative tools
│   │   ├── __init__.py
│   │   ├── calendar_intelligence.py       # Calendar management
│   │   ├── email_integration.py           # Email automation
│   │   └── workflow_automation.py         # Workflow automation
│   ├── agent_api.py                       # Agent API interface
│   ├── agent_messaging.py                 # Inter-agent messaging
│   ├── agents_api.py                      # Agents API endpoints
│   ├── alerting.py                        # Alert system
│   ├── analytics.py                       # Analytics engine (Stage 11)
│   ├── approval_engine.py                 # Approval workflow engine
│   ├── artifacts.py                       # Artifact management
│   ├── audit_log.py                       # Audit logging
│   ├── auto_improver.py                   # Auto-improvement system
│   ├── auto_pilot.py                      # Auto-pilot mode
│   ├── autonomous_coordinator.py          # Autonomous coordination
│   ├── brain.py                           # Self-optimization engine (Stage 12)
│   ├── business_memory/                   # Business context memory
│   │   ├── __init__.py
│   │   ├── extractor.py                   # Information extraction
│   │   ├── manager.py                     # Memory management
│   │   ├── privacy.py                     # Privacy controls
│   │   └── schema.py                      # Data schemas
│   ├── checkpoint.py                      # Checkpoint management
│   ├── clarification/                     # Clarification system
│   │   ├── __init__.py
│   │   ├── detector.py                    # Ambiguity detection
│   │   ├── generator.py                   # Question generation
│   │   ├── manager.py                     # Clarification management
│   │   └── templates.py                   # Question templates
│   ├── cli_chat.py                        # CLI chat interface
│   ├── code_analysis/                     # Code analysis tools
│   │   ├── __init__.py
│   │   ├── ast_parser.py                  # AST parsing
│   │   ├── js_parser.py                   # JavaScript parser
│   │   ├── patterns.py                    # Pattern detection
│   │   └── refactoring.py                 # Refactoring tools
│   ├── code_review/                       # Code review system
│   │   ├── __init__.py
│   │   └── review_agent.py                # Review agent
│   ├── code_review_bot.py                 # Code review bot
│   ├── company_ops.py                     # Company operations
│   ├── config/                            # Configuration files
│   │   ├── agents.yaml                    # Agent configurations
│   │   ├── schemas/                       # JSON schemas
│   │   │   ├── agent_schema.json          # Agent config schema
│   │   │   └── task_schema.json           # Task config schema
│   │   └── tasks.yaml                     # Task configurations
│   ├── config.py                          # Configuration module
│   ├── config_loader.py                   # Config file loader
│   ├── conversational_agent.py            # Conversational AI agent
│   ├── core/                              # Core utilities
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py             # Circuit breaker pattern
│   │   └── error_handler.py               # Error handling
│   ├── core_logging.py                    # Logging configuration
│   ├── cost_estimator.py                  # Cost estimation
│   ├── cost_logs/                         # Cost tracking logs
│   │   └── multi_section_landing_full_test.jsonl
│   ├── cost_tracker.py                    # Token and cost tracking
│   ├── cost_tracker_instance.py           # Cost tracker singleton
│   ├── council/                           # Council decision system
│   │   ├── __init__.py
│   │   ├── competitive_council.py         # Competitive analysis
│   │   ├── factory.py                     # Council factory
│   │   ├── graveyard.py                   # Deprecated decisions
│   │   ├── happiness.py                   # Team happiness metrics
│   │   ├── models.py                      # Council models
│   │   ├── orchestrator.py                # Council orchestration
│   │   └── voting.py                      # Voting mechanisms
│   ├── database/                          # Database modules
│   │   ├── __init__.py
│   │   ├── kg_backends.py                 # Knowledge graph backends
│   │   └── pg_migration.py                # PostgreSQL migration
│   ├── deployment/                        # Deployment utilities
│   │   ├── __init__.py
│   │   └── rollback.py                    # Rollback management
│   ├── documents/                         # Document generation
│   │   ├── __init__.py
│   │   ├── excel_generator.py             # Excel generation
│   │   ├── pdf_generator.py               # PDF generation
│   │   └── word_generator.py              # Word generation
│   ├── domain_router.py                   # Domain routing
│   ├── exec_analysis.py                   # Execution analysis
│   ├── exec_deps.py                       # Execution dependencies
│   ├── exec_safety.py                     # Safety checks
│   ├── exec_tools.py                      # Execution tools
│   ├── execution/                         # Task execution
│   │   ├── __init__.py
│   │   ├── direct_executor.py             # Direct execution mode
│   │   ├── employee_pool.py               # Worker pool management
│   │   ├── review_queue.py                # Review queue
│   │   ├── strategy_decider.py            # Execution strategy
│   │   ├── task_distributor.py            # Task distribution
│   │   └── task_router.py                 # Task routing
│   ├── feedback_analyzer.py               # Feedback analysis
│   ├── file_context.py                    # File context management
│   ├── file_explorer.py                   # File & snapshot explorer (Stage 9)
│   ├── file_operations.py                 # File operations
│   ├── finance/                           # Finance tools
│   │   ├── __init__.py
│   │   ├── document_intelligence.py       # Financial document analysis
│   │   ├── financial_templates.py         # Financial templates
│   │   └── spreadsheet_engine.py          # Spreadsheet engine
│   ├── flow/                              # Flow engine
│   │   ├── __init__.py
│   │   ├── decorators.py                  # Flow decorators
│   │   ├── engine.py                      # Flow execution engine
│   │   ├── events.py                      # Flow events
│   │   ├── graph.py                       # Flow graph
│   │   └── state.py                       # Flow state
│   ├── git_secret_scanner.py              # Git secret scanning
│   ├── git_utils.py                       # Git utilities
│   ├── github_integration.py              # GitHub integration
│   ├── human_proxy.py                     # Human-in-the-loop proxy
│   ├── integrations/                      # External integrations
│   │   ├── auth.py                        # Authentication
│   │   ├── base.py                        # Base integration
│   │   ├── database.py                    # Database integration
│   │   ├── hris/                          # HR systems
│   │   │   ├── __init__.py
│   │   │   └── bamboohr.py                # BambooHR integration
│   │   └── tools.py                       # Integration tools
│   ├── inter_agent_bus.py                 # Inter-agent message bus
│   ├── jarvis_agent.py                    # JARVIS agent core
│   ├── jarvis_chat.py                     # JARVIS chat interface
│   ├── jarvis_persona.py                  # JARVIS personality
│   ├── jarvis_tools.py                    # JARVIS tools
│   ├── jarvis_vision.py                   # JARVIS vision capabilities
│   ├── jarvis_voice.py                    # JARVIS voice synthesis
│   ├── jarvis_voice_chat.py               # JARVIS voice chat
│   ├── jobs.py                            # Job manager (Stage 8)
│   ├── kg_optimizer.py                    # Knowledge graph optimizer
│   ├── kg_write_queue.py                  # KG write queue
│   ├── knowledge_graph.py                 # Knowledge graph
│   ├── knowledge_query.py                 # Knowledge queries
│   ├── llm/                               # LLM management
│   │   ├── __init__.py
│   │   ├── config.py                      # LLM configuration
│   │   ├── enhanced_router.py             # Enhanced routing
│   │   ├── hybrid_strategy.py             # Hybrid LLM strategy
│   │   ├── llm_router.py                  # LLM routing
│   │   ├── ollama_client.py               # Ollama integration
│   │   ├── performance_tracker.py         # Performance tracking
│   │   └── providers.py                   # LLM providers
│   ├── llm.py                             # LLM interface
│   ├── llm_cache.py                       # LLM response cache
│   ├── log_sanitizer.py                   # Log sanitization
│   ├── meetings/                          # Meeting integration
│   │   ├── __init__.py
│   │   ├── base.py                        # Base meeting bot
│   │   ├── cross_meeting_context.py       # Cross-meeting context
│   │   ├── diarization/                   # Speaker diarization
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Base diarization
│   │   │   ├── pyannote_engine.py         # Pyannote engine
│   │   │   └── speaker_manager.py         # Speaker management
│   │   ├── factory.py                     # Meeting bot factory
│   │   ├── google_meet_bot.py             # Google Meet bot
│   │   ├── intelligence/                  # Meeting intelligence
│   │   │   ├── __init__.py
│   │   │   ├── action_executor.py         # Action execution
│   │   │   ├── action_item_reminders.py   # Action item reminders
│   │   │   └── meeting_analyzer.py        # Meeting analysis
│   │   ├── live_audio_bot.py              # Live audio capture
│   │   ├── sdk_integration.py             # SDK integration
│   │   ├── session_manager.py             # Session management
│   │   ├── teams_bot.py                   # Microsoft Teams bot
│   │   ├── transcription/                 # Transcription engines
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Base transcription
│   │   │   ├── deepgram_engine.py         # Deepgram engine
│   │   │   ├── manager.py                 # Transcription manager
│   │   │   └── whisper_engine.py          # Whisper engine
│   │   └── zoom_bot.py                    # Zoom bot
│   ├── memory/                            # Memory system
│   │   ├── __init__.py
│   │   ├── context_retriever.py           # Context retrieval
│   │   ├── contextual.py                  # Contextual memory
│   │   ├── entity.py                      # Entity memory
│   │   ├── long_term.py                   # Long-term memory
│   │   ├── manager.py                     # Memory manager
│   │   ├── preference_learner.py          # Preference learning
│   │   ├── session_manager.py             # Session management
│   │   ├── short_term.py                  # Short-term memory
│   │   ├── storage.py                     # Memory storage
│   │   ├── user_profile.py                # User profiles
│   │   └── vector_store.py                # Vector storage
│   ├── memory_store/                      # Memory storage data
│   │   └── test_run_002/
│   │       └── stage1.json
│   ├── memory_store.py                    # Memory store module
│   ├── merge_manager.py                   # Merge management
│   ├── migrations/                        # Database migrations
│   │   └── 001_approval_workflows.py      # Approval workflow migration
│   ├── mission_runner.py                  # Mission execution
│   ├── model_registry.py                  # Model registry
│   ├── model_router.py                    # Model routing
│   ├── models/                            # Data models
│   │   ├── __init__.py
│   │   ├── agent_config.py                # Agent configuration model
│   │   └── task_config.py                 # Task configuration model
│   ├── models.json                        # Model definitions
│   ├── monitoring/                        # Monitoring system
│   │   ├── __init__.py
│   │   ├── alerts.py                      # Alert management
│   │   ├── logging_config.py              # Logging configuration
│   │   └── metrics.py                     # Metrics collection
│   ├── monitoring.py                      # Monitoring module
│   ├── mypy.ini                           # MyPy configuration
│   ├── optimization/                      # Performance optimization
│   │   ├── __init__.py
│   │   ├── batch_processor.py             # Batch processing
│   │   ├── cache.py                       # Caching
│   │   └── lazy_loader.py                 # Lazy loading
│   ├── orchestrator.py                    # 3-loop orchestrator
│   ├── orchestrator_2loop.py              # 2-loop orchestrator
│   ├── orchestrator_3loop_legacy.py       # Legacy 3-loop
│   ├── orchestrator_context.py            # Orchestrator context
│   ├── orchestrator_integration.py        # Orchestrator integration
│   ├── orchestrator_phase3.py             # Phase 3 orchestrator
│   ├── overseer.py                        # System overseer
│   ├── parallel_executor.py               # Parallel execution
│   ├── paths.py                           # Path utilities
│   ├── patterns/                          # Execution patterns
│   │   ├── __init__.py
│   │   ├── autoselect.py                  # Auto-selection
│   │   ├── base.py                        # Base pattern
│   │   ├── hierarchical.py                # Hierarchical pattern
│   │   ├── roundrobin.py                  # Round-robin pattern
│   │   ├── selector.py                    # Pattern selector
│   │   └── sequential.py                  # Sequential pattern
│   ├── performance/                       # Performance utilities
│   │   ├── __init__.py
│   │   ├── cache.py                       # Performance cache
│   │   ├── lazy.py                        # Lazy evaluation
│   │   ├── parallel.py                    # Parallel processing
│   │   ├── pool.py                        # Worker pools
│   │   └── utils.py                       # Performance utilities
│   ├── permissions.py                     # Permission management
│   ├── permissions_matrix.json            # Permission definitions
│   ├── proactive_executor.py              # Proactive execution
│   ├── project_config.json                # Project configuration
│   ├── project_stats.py                   # Project statistics
│   ├── prompt_security.py                 # Prompt injection protection
│   ├── prompts/                           # Prompt templates
│   │   └── prompts_default.json           # Default prompts
│   ├── prompts.py                         # Prompts module
│   ├── py.typed                           # PEP 561 marker
│   ├── qa.py                              # Quality assurance
│   ├── queue_config.py                    # Queue configuration
│   ├── repo_router.py                     # Repository routing
│   ├── retry_loop_detector.py             # Retry loop detection
│   ├── role_definitions/                  # Role definitions
│   │   ├── finance_roles.json             # Finance roles
│   │   ├── hr_roles.json                  # HR roles
│   │   └── legal_roles.json               # Legal roles
│   ├── roles.py                           # Role management
│   ├── ruff.toml                          # Ruff linter config
│   ├── run_logger.py                      # Structured run logging
│   ├── run_logs/                          # Run log storage
│   │   └── multi_section_landing_full_test_3loop.jsonl
│   ├── run_mode.py                        # Main CLI entry point
│   ├── run_workflows/                     # Workflow definitions
│   │   └── test_run_001_workflow.json
│   ├── runner.py                          # Programmatic API (Stage 7)
│   ├── safe_io.py                         # Safe I/O helpers
│   ├── sandbox.py                         # Sandbox execution
│   ├── scheduler/                         # Task scheduling
│   │   ├── __init__.py
│   │   └── cron.py                        # Cron scheduler
│   ├── security/                          # Security modules
│   │   ├── __init__.py
│   │   ├── audit_log.py                   # Security audit log
│   │   ├── auth.py                        # Authentication
│   │   └── rate_limit.py                  # Rate limiting
│   ├── self_eval.py                       # Self-evaluation
│   ├── self_refinement.py                 # Self-refinement
│   ├── site_tools.py                      # Site management tools
│   ├── specialist_market.py               # Specialist marketplace
│   ├── specialists.py                     # Specialist agents
│   ├── STAGE_3.3_LLM_RESILIENCE.md        # LLM resilience docs
│   ├── stage_summaries/                   # Stage summary storage
│   │   └── test_run_003/
│   │       └── stage1.json
│   ├── stage_summaries.py                 # Stage summaries module
│   ├── static_analysis.py                 # Static code analysis
│   ├── status_codes.py                    # Normalized status codes
│   ├── templates/                         # Template files
│   │   ├── __init__.py
│   │   ├── email/
│   │   │   └── welcome_email.html         # Email template
│   │   └── email_renderer.py              # Email rendering
│   ├── temporal/                          # Temporal workflow
│   │   ├── __init__.py
│   │   ├── activities.py                  # Temporal activities
│   │   ├── client.py                      # Temporal client
│   │   ├── config.py                      # Temporal config
│   │   ├── worker.py                      # Temporal worker
│   │   └── workflows.py                   # Temporal workflows
│   ├── test_generation.py                 # Test generation
│   ├── tests/                             # Test suite
│   │   ├── e2e/                           # End-to-end tests
│   │   │   └── test_smoke_hello_kevin.py
│   │   ├── fixtures/                      # Test fixtures
│   │   │   └── mock_tool.py
│   │   ├── integration/                   # Integration tests
│   │   │   ├── conftest.py
│   │   │   ├── test_council.py
│   │   │   ├── test_full_flow.py
│   │   │   ├── test_human_approval.py
│   │   │   ├── test_llm_failover.py
│   │   │   ├── test_memory.py
│   │   │   ├── test_patterns.py
│   │   │   ├── test_snapshots_and_files.py
│   │   │   └── test_stage5_integration.py
│   │   ├── mocks.py
│   │   ├── test_action_tools.py
│   │   ├── test_agent_messaging.py
│   │   ├── test_api_client.py
│   │   ├── test_backward_compat.py
│   │   ├── test_business_memory.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_clarification.py
│   │   ├── test_code_executor.py
│   │   ├── test_context_retriever.py
│   │   ├── test_conversational_agent.py
│   │   ├── test_council.py
│   │   ├── test_coverage_gaps.py
│   │   ├── test_db_client.py
│   │   ├── test_diarization.py
│   │   ├── test_direct_executor.py
│   │   ├── test_employee_pool.py
│   │   ├── test_enhanced_router.py
│   │   ├── test_error_handler.py
│   │   ├── test_file_ops.py
│   │   ├── test_flow_engine.py
│   │   ├── test_human_proxy.py
│   │   ├── test_hybrid_strategy.py
│   │   ├── test_llm_config.py
│   │   ├── test_llm_router.py
│   │   ├── test_meeting_bots.py
│   │   ├── test_meeting_intelligence.py
│   │   ├── test_memory_system.py
│   │   ├── test_monitoring.py
│   │   ├── test_ollama.py
│   │   ├── test_optimization.py
│   │   ├── test_patterns.py
│   │   ├── test_performance_tracker.py
│   │   ├── test_phase1_integration.py
│   │   ├── test_preference_learner.py
│   │   ├── test_review_queue.py
│   │   ├── test_security.py
│   │   ├── test_session_manager.py
│   │   ├── test_strategy_decider.py
│   │   ├── test_task_distributor.py
│   │   ├── test_task_router.py
│   │   ├── test_tool_registry.py
│   │   ├── test_transcription.py
│   │   ├── test_vector_store.py
│   │   ├── test_yaml_config.py
│   │   └── unit/                          # Unit tests
│   │       ├── test_cost_tracker.py
│   │       ├── test_document_generation.py
│   │       ├── test_exec_tools.py
│   │       ├── test_git_secret_scanner.py
│   │       ├── test_hr_tools.py
│   │       ├── test_log_sanitizer.py
│   │       ├── test_merge_manager.py
│   │       ├── test_model_registry.py
│   │       ├── test_model_router.py
│   │       ├── test_orchestrator.py
│   │       ├── test_permissions.py
│   │       ├── test_phase3_basic.py
│   │       ├── test_prompt_security.py
│   │       ├── test_repo_router.py
│   │       ├── test_roles.py
│   │       ├── test_tool_plugins.py
│   │       └── test_view_run.py
│   ├── tests_config/                      # Config tests
│   │   ├── __init__.py
│   │   ├── test_agent_config.py
│   │   ├── test_config_loader.py
│   │   ├── test_config_validator.py
│   │   └── test_task_config.py
│   ├── tests_e2e/                         # E2E tests
│   │   ├── __init__.py
│   │   └── test_full_pipeline.py
│   ├── tests_sanity/                      # Sanity tests
│   │   ├── __init__.py
│   │   └── test_sanity.py
│   ├── tests_shared/                      # Shared test utilities
│   │   ├── __init__.py
│   │   └── fixtures.py
│   ├── tests_stage10/                     # QA pipeline tests
│   │   ├── __init__.py
│   │   ├── test_qa.py
│   │   ├── test_qa_edge_cases.py
│   │   ├── test_runner_qa_integration.py
│   │   └── test_webapp_qa_endpoints.py
│   ├── tests_stage11/                     # Analytics tests
│   │   ├── __init__.py
│   │   └── test_analytics.py
│   ├── tests_stage12/                     # Self-optimization tests
│   │   ├── __init__.py
│   │   └── test_brain.py
│   ├── tests_stage7/                      # Web dashboard tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_runner.py
│   │   ├── test_smoke.py
│   │   └── test_webapp.py
│   ├── tests_stage8/                      # Job manager tests
│   │   ├── __init__.py
│   │   ├── test_jobs.py
│   │   └── test_smoke.py
│   ├── tests_stage9/                      # Project explorer tests
│   │   ├── __init__.py
│   │   ├── test_file_explorer.py
│   │   └── test_webapp_routes.py
│   ├── tool_audit_log.py                  # Tool audit logging
│   ├── tool_registry.py                   # Tool registry
│   ├── tools/                             # Tool implementations
│   │   ├── __init__.py
│   │   ├── actions/                       # Action tools
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Base action
│   │   │   ├── buy_domain.py              # Domain purchase
│   │   │   ├── deploy_website.py          # Website deployment
│   │   │   ├── make_payment.py            # Payment processing
│   │   │   └── send_sms.py                # SMS messaging
│   │   ├── audit_report.py                # Audit reports
│   │   ├── base.py                        # Base tool
│   │   ├── builtin/                       # Built-in tools
│   │   │   ├── __init__.py
│   │   │   ├── format_code.py             # Code formatting
│   │   │   └── run_tests.py               # Test execution
│   │   ├── compliance_audit_report.py     # Compliance audits
│   │   ├── documents/                     # Document tools
│   │   │   ├── __init__.py
│   │   │   ├── generate_excel.py          # Excel generation
│   │   │   ├── generate_pdf.py            # PDF generation
│   │   │   └── generate_word.py           # Word generation
│   │   ├── hr/                            # HR tools
│   │   │   ├── __init__.py
│   │   │   ├── create_calendar_event.py   # Calendar events
│   │   │   ├── create_hris_record.py      # HRIS records
│   │   │   └── send_email.py              # Email sending
│   │   ├── plugin_loader.py               # Plugin loading
│   │   └── update_models.py               # Model updates
│   ├── validators/                        # Input validators
│   │   ├── __init__.py
│   │   └── config_validator.py            # Config validation
│   ├── verify_phase1.py                   # Phase 1 verification
│   ├── view_run.py                        # Run viewer
│   ├── view_runs.py                       # Runs list viewer
│   ├── vision_api.py                      # Vision API
│   ├── voice_api.py                       # Voice API
│   ├── webapp/                            # Web dashboard (Stage 7-12)
│   │   ├── __init__.py
│   │   ├── admin_api.py                   # Admin API
│   │   ├── api_keys.py                    # API key management
│   │   ├── app.py                         # FastAPI application
│   │   ├── auth.py                        # Authentication
│   │   ├── auth_routes.py                 # Auth routes
│   │   ├── chat_api.py                    # Chat API
│   │   ├── code_api.py                    # Code API
│   │   ├── finance_api.py                 # Finance API
│   │   └── templates/                     # HTML templates
│   │       ├── analytics.html             # Analytics dashboard
│   │       ├── approvals.html             # Approvals page
│   │       ├── base.html                  # Base template
│   │       ├── chat.html                  # Chat interface
│   │       ├── index.html                 # Home page
│   │       ├── integrations.html          # Integrations page
│   │       ├── jarvis.html                # JARVIS interface
│   │       ├── job_detail.html            # Job detail page
│   │       ├── jobs.html                  # Jobs list
│   │       ├── project_detail.html        # Project detail
│   │       ├── projects.html              # Projects list
│   │       ├── run_detail.html            # Run detail page
│   │       └── tuning.html                # Tuning dashboard
│   ├── webhooks/                          # Webhook handling
│   │   ├── __init__.py
│   │   ├── retry.py                       # Webhook retry
│   │   └── security.py                    # Webhook security
│   ├── workers/                           # Background workers
│   │   ├── __init__.py
│   │   ├── celery_app.py                  # Celery application
│   │   └── tasks.py                       # Celery tasks
│   ├── workflow_enforcement.py            # Workflow enforcement
│   ├── workflow_manager.py                # Workflow management
│   └── workflows/                         # Workflow definitions
│       ├── __init__.py
│       ├── base.py                        # Base workflow
│       ├── coding.py                      # Coding workflow
│       ├── finance.py                     # Finance workflow
│       ├── hr.py                          # HR workflow
│       ├── legal.py                       # Legal workflow
│       └── ops.py                         # Operations workflow
├── artifacts/                             # Generated artifacts
│   └── .gitkeep
├── config/                                # Global configuration
│   └── llm_config.yaml                    # LLM configuration
├── data/                                  # Data storage
│   └── .gitkeep
├── deployment/                            # Deployment configuration
│   ├── CLOUD_DEPLOYMENT_GUIDE.md          # Cloud deployment guide
│   ├── docker-compose.yml                 # Docker Compose config
│   ├── Dockerfile.app                     # App Dockerfile
│   ├── Dockerfile.worker                  # Worker Dockerfile
│   └── kubernetes/                        # Kubernetes configs
│       └── jarvis-deployment.yaml         # K8s deployment
├── dev/                                   # Developer tools
│   ├── clean_logs.py                      # Clean/archive logs
│   ├── generate_fixture.py                # Generate test fixture
│   ├── profile_run.py                     # Performance profiling
│   ├── run_autopilot.py                   # Run auto-pilot mode
│   ├── run_once.py                        # Run single orchestrator
│   ├── templates/
│   │   └── log_viewer.html                # Log viewer template
│   └── view_logs.py                       # View logs in browser
├── docs/                                  # Documentation
│   ├── ACTION_TOOLS_SETUP.md              # Action tools setup
│   ├── ADMIN_TOOLS.md                     # Admin tools guide
│   ├── Audit_Phase_1.md                   # Phase 1 audit
│   ├── COMPETITIVE_ANALYSIS_2025.md       # Competitive analysis
│   ├── CONFIGURATION_QUICK_REFERENCE.md   # Quick reference
│   ├── CONVERSATIONAL_AGENT.md            # Conversational agent guide
│   ├── DEMO_GUIDE.md                      # Demo guide
│   ├── DEPENDENCY_INJECTION.md            # DI documentation
│   ├── DEVELOPER_GUIDE.md                 # Developer guide
│   ├── ENGINEERING_TOOLS.md               # Engineering tools
│   ├── ENTERPRISE_ROADMAP.md              # Enterprise roadmap
│   ├── FINANCE_TOOLS.md                   # Finance tools guide
│   ├── generate_docs.py                   # Doc generator
│   ├── HR_TOOLS_SETUP.md                  # HR tools setup
│   ├── IMPLEMENTATION_PROMPTS_PHASES_1_5.md
│   ├── IMPLEMENTATION_PROMPTS_PHASES_6_11 (1).md
│   ├── INSTALLATION.md                    # Installation guide
│   ├── JARVIS_2_0_API_REFERENCE.md        # API reference
│   ├── JARVIS_2_0_AUDIT_REPORT.md         # Audit report
│   ├── JARVIS_2_0_CONFIGURATION_GUIDE.md  # Configuration guide
│   ├── JARVIS_2_0_COUNCIL_GUIDE.md        # Council guide
│   ├── JARVIS_2_0_MEMORY_GUIDE.md         # Memory guide
│   ├── JARVIS_2_0_PATTERN_GUIDE.md        # Pattern guide
│   ├── JARVIS_2_0_REMAINING_WORK.md       # Remaining work
│   ├── JARVIS_PRE_DEMO_CHECKLIST.md       # Pre-demo checklist
│   ├── LOGGING_BEST_PRACTICES.md          # Logging guide
│   ├── MEETING_INTEGRATION_SETUP.md       # Meeting integration
│   ├── MIGRATION_GUIDE_1x_to_2x.md        # Migration guide
│   ├── MIGRATION_LOGGING.md               # Logging migration
│   ├── MODEL_ROUTING.md                   # Model routing guide
│   ├── PHASE_3_1_APPROVAL_WORKFLOWS.md    # Phase 3.1 docs
│   ├── PHASE_3_2_INTEGRATION_FRAMEWORK.md # Phase 3.2 docs
│   ├── PHASE_4_3_RELIABILITY_FIXES.md     # Phase 4.3 docs
│   ├── PHASE_5_1_AUDIT_COMPLIANCE_LOGGING.md
│   ├── PHASE_5_2_PARALLEL_EXECUTION.md
│   ├── PHASE_5_2_PERFORMANCE_OPTIMIZATION.md
│   ├── PHASE_5_6_MONITORING_ALERTING.md
│   ├── REFERENCE.md                       # API reference
│   ├── SECURITY_GIT_SECRET_SCANNING.md    # Secret scanning
│   ├── SECURITY_PROMPT_INJECTION.md       # Prompt injection
│   ├── stage5.2_plan.md                   # Stage 5.2 plan
│   ├── STAGE7_WEB_UI.md                   # Web dashboard guide
│   ├── STAGE8_JOB_MANAGER.md              # Job manager guide
│   ├── STAGE9_PROJECT_EXPLORER.md         # Project explorer guide
│   ├── STAGE10_QA_PIPELINE.md             # QA pipeline guide
│   ├── STAGE11_ANALYTICS_DASHBOARD.md     # Analytics guide
│   ├── STAGE12_SELF_OPTIMIZATION.md       # Self-optimization guide
│   ├── SYSTEM_1.2_COMPLETE_ROADMAP.md     # Complete roadmap
│   ├── SYSTEM_1_2_MANUAL.md               # System manual
│   ├── SYSTEM_1_2_MANUAL_PHASES_9_11_ADDENDUM.md
│   ├── SYSTEM_ANALYSIS_DEPARTMENT_IN_A_BOX.md
│   ├── THREADING_AND_CONCURRENCY.md       # Threading guide
│   ├── TOOL_PLUGIN_GUIDE.md               # Plugin guide
│   ├── TROUBLESHOOTING.md                 # Troubleshooting
│   └── WINDOWS_SETUP_GUIDE.md             # Windows setup
├── missions/                              # Mission definitions
│   ├── example_coding_mission.json        # Example mission
│   └── logs/
│       └── .gitkeep
├── run_logs/                              # Run history and logs
│   └── .gitkeep
├── run_logs_exec/                         # Execution logs
│   └── .gitkeep
├── sites/                                 # Generated web projects
│   └── contafuel_marketing/               # Example project
├── tests/                                 # Root-level tests
│   ├── run_reliability_tests.py           # Reliability tests
│   ├── run_stage3_tests.py                # Stage 3 tests
│   ├── test_approval_workflows.py         # Approval tests
│   ├── test_audit_log.py                  # Audit log tests
│   ├── test_inter_agent_bus.py            # Inter-agent bus tests
│   ├── test_kg_optimizer.py               # KG optimizer tests
│   ├── test_memory_store.py               # Memory store tests
│   ├── test_monitoring_alerting.py        # Monitoring tests
│   ├── test_parallel_executor.py          # Parallel executor tests
│   ├── test_reliability_fixes.py          # Reliability tests
│   ├── test_specialists.py                # Specialists tests
│   └── test_workflow_manager.py           # Workflow tests
├── tools/                                 # External tools
│   ├── cli/                               # CLI tool
│   │   ├── jarvis_cli.py                  # JARVIS CLI
│   │   └── setup.py                       # CLI setup
│   ├── gmail-addon/                       # Gmail add-on
│   │   ├── appsscript.json                # Apps Script config
│   │   └── Code.gs                        # Gmail add-on code
│   ├── outlook-addin/                     # Outlook add-in
│   │   ├── manifest.xml                   # Add-in manifest
│   │   └── src/
│   │       └── taskpane.ts                # Taskpane code
│   └── vscode-extension/                  # VSCode extension
│       ├── package.json                   # Extension config
│       ├── src/
│       │   └── extension.ts               # Extension code
│       └── tsconfig.json                  # TypeScript config
├── add_sqlite_integration.py              # SQLite integration script
├── AST_CODE_TRANSFORMATION.md             # AST transformation docs
├── AUDIT_PROMPT.md                        # Audit prompt template
├── AUDIT_REPORT.md                        # Audit report
├── CHANGELOG.md                           # Change log
├── check_hr_db.py                         # HR database checker
├── CLEAN_BRANCH_GUIDE.md                  # Branch cleaning guide
├── COMPETITIVE_ANALYSIS_REPORT.md         # Competitive analysis
├── COMPETITIVE_ANALYSIS_REPORT_ES.md      # Competitive analysis (Spanish)
├── cost_tracker.py                        # Cost tracker (root)
├── create_approval.py                     # Create approval script
├── create_demo_approval.py                # Demo approval script
├── create_test_hr_db.py                   # Test HR database
├── DEVELOPER_GUIDE.md                     # Developer guide
├── full_workflow.py                       # Full workflow script
├── JARVIS_2_0_ROADMAP.md                  # JARVIS 2.0 roadmap
├── JARVIS_2_0_ROADMAP_ES.md               # Roadmap (Spanish)
├── JARVIS_AGI_ROADMAP_EVALUATION.md       # AGI roadmap evaluation
├── JARVIS_ARCHITECTURE.md                 # Architecture documentation
├── JARVIS_COMPREHENSIVE_AUDIT_REPORT.md   # Comprehensive audit
├── JARVIS_TRIAL_REPORT.md                 # Trial report
├── make.py                                # Command dispatcher
├── MEETING_SDK_ACTIVATION_GUIDE.md        # Meeting SDK guide
├── orchestrator.py                        # Root orchestrator
├── ORCHESTRATOR_CONSOLIDATION_PLAN.md     # Consolidation plan
├── PHASE_3_IMPLEMENTATION_GUIDE.md        # Phase 3 guide
├── POSTGRESQL_MIGRATION_GUIDE.md          # PostgreSQL migration
├── README.md                              # This file
├── README.txt                             # Text readme
├── requirements.txt                       # Python dependencies
├── site_tools.py                          # Site tools (root)
├── start_webapp.py                        # Webapp starter
├── TEMPORAL_INTEGRATION_GUIDE.md          # Temporal integration
├── test_integration.py                    # Integration test
├── TOOL_MIGRATION_REFERENCE.md            # Tool migration ref
└── ZOOM_MEET_SDK_INTEGRATION.md           # Zoom/Meet SDK guide
```

## Usage

### Web Dashboard

**Start the server:**
```bash
python -m agent.webapp.app
```

**Access the dashboard:**
- Home: http://127.0.0.1:8000
- Run detail: http://127.0.0.1:8000/run/<run_id>
- API: http://127.0.0.1:8000/api/projects

**Features:**
- 📋 Project selection from sites/ directory
- ⚙️ Visual configuration forms
- 🚀 One-click run execution
- 📊 Run history with filtering
- 💰 Cost breakdown per run
- 📝 Detailed iteration logs
- 📁 Project file explorer (Stage 9)
- 📸 Snapshot browsing (Stage 9)
- 🔄 Version comparison & diff viewer (Stage 9)

See [docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md) for complete dashboard documentation.

**Project Explorer (Stage 9):**

Browse and explore your generated projects:

```bash
# Navigate to Projects in the web dashboard
# http://127.0.0.1:8000/projects
```

Features:
- 🗂️ **File Tree Browser**: Navigate project files with expand/collapse
- 📄 **File Viewer**: View file contents with syntax highlighting
- 📸 **Snapshot Browser**: Explore iteration history
- 🔄 **Diff Viewer**: Compare versions with unified diff
- 🔗 **Job Integration**: Direct links from job pages to project files

See [docs/STAGE9_PROJECT_EXPLORER.md](docs/STAGE9_PROJECT_EXPLORER.md) for complete explorer documentation.

### Command Line

**Single run:**
```bash
python dev/run_once.py
```

**Auto-pilot mode:**
```bash
python dev/run_autopilot.py
```

**Using make.py:**
```bash
python make.py run        # Run single orchestrator
python make.py auto       # Run auto-pilot mode
python make.py test       # Run sanity tests
python make.py docs       # Generate documentation
python make.py fixture    # Generate test fixture
python make.py view       # View logs in browser
python make.py clean      # Clean run logs
python make.py profile    # Profile a run
```

### Programmatic API

```python
from agent.runner import run_project, list_projects, list_run_history

# List available projects
projects = list_projects()

# Run a project
config = {
    "mode": "3loop",
    "project_subdir": "my_project",
    "task": "Build a landing page",
    "max_rounds": 3,
    "max_cost_usd": 1.5,
    "use_git": True,
}
run_summary = run_project(config)

# View history
history = list_run_history(limit=10)
```

## Configuration

### Project Configuration (project_config.json)

```json
{
  "project_name": "My Project",
  "project_subdir": "my_project",
  "task": "Build a modern website...",
  "max_rounds": 3,
  "mode": "3loop",
  "use_visual_review": true,
  "use_git": true,
  "prompts_file": "prompts_default.json",
  "max_cost_usd": 1.5,
  "cost_warning_usd": 0.8,
  "interactive_cost_mode": "once"
}
```

### Auto-Pilot Configuration

Add to project_config.json:

```json
{
  "auto_pilot": {
    "enabled": true,
    "max_sub_runs": 3,
    "acceptance_threshold": 0.8
  }
}
```

### Environment Variables

```bash
# Override default models
export MANAGER_MODEL=gpt-4o
export SUPERVISOR_MODEL=gpt-4o-mini
export EMPLOYEE_MODEL=gpt-4o

# Set API keys
export OPENAI_API_KEY=your-key-here
```

## Testing

### Test Organization

The project includes comprehensive test coverage across all stages:

```
agent/
├── tests_sanity/          # Smoke tests for core functionality
├── tests_stage7/          # Web dashboard tests
├── tests_stage8/          # Job manager tests
├── tests_stage9/          # Project explorer tests
├── tests_stage10/         # QA pipeline tests
├── tests_stage11/         # Analytics tests
├── tests_stage12/         # Self-optimization tests
├── tests_shared/          # Reusable fixtures and helpers
└── tests_e2e/             # End-to-end integration tests
```

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run tests by stage:**
```bash
# Stage 7: Web dashboard
pytest agent/tests_stage7/ -v

# Stage 8: Job manager
pytest agent/tests_stage8/ -v

# Stage 9: Project explorer
pytest agent/tests_stage9/ -v

# Stage 10: QA pipeline
pytest agent/tests_stage10/ -v

# Stage 11: Analytics
pytest agent/tests_stage11/ -v

# Stage 12: Self-optimization
pytest agent/tests_stage12/ -v
```

**Run specific test files:**
```bash
# Web API endpoints
pytest agent/tests_stage7/test_webapp.py -v

# QA edge cases
pytest agent/tests_stage10/test_qa_edge_cases.py -v

# E2E pipeline test
pytest agent/tests_e2e/test_full_pipeline.py -v
```

**Run with coverage:**
```bash
pytest --cov=agent --cov-report=html
open htmlcov/index.html  # View coverage report
```

**Run E2E tests (marked with @pytest.mark.e2e):**
```bash
pytest -m e2e -v
```

**Using make.py:**
```bash
python make.py test        # Run sanity tests
```

### Test Coverage by Stage

**Stage 7 - Web Dashboard:**
- `test_webapp.py`: FastAPI routes, job creation, error handling
- `test_runner.py`: Programmatic API, integration tests

**Stage 8 - Job Manager:**
- `test_job_manager.py`: Job CRUD, state persistence, background execution
- `test_job_endpoints.py`: Job API endpoints, cancellation, log streaming

**Stage 9 - Project Explorer:**
- `test_webapp_routes.py`: File tree, snapshots, diff viewer, path traversal protection
- `test_file_explorer.py`: File system operations, snapshot management

**Stage 10 - QA Pipeline:**
- `test_webapp_qa_endpoints.py`: QA API endpoints (9 tests)
- `test_runner_qa_integration.py`: QA integration with runner (7 tests)
- `test_qa_edge_cases.py`: Edge cases and error conditions (20+ tests)
  - Missing HTML tags (title, meta, lang, h1)
  - Accessibility issues (images without alt, empty buttons)
  - Code quality (large files, excessive console.logs)
  - Smoke test failures and timeouts
  - Malformed HTML and empty projects
  - Config handling and report serialization

**Stage 11 - Analytics:**
- `test_analytics.py`: Metrics aggregation, cost tracking, trends
- `test_analytics_endpoints.py`: Analytics API, data export

**Stage 12 - Self-Optimization:**
- `test_brain.py`: Recommendations, profiling, auto-tuning
- `test_brain_endpoints.py`: Tuning API, confidence scoring

**End-to-End Tests:**
- `test_full_pipeline.py`: Complete workflow testing
  - Job creation and polling
  - QA execution and reporting
  - Analytics integration
  - Tuning endpoint verification
  - Failure handling scenarios
  - Concurrent job management

### Shared Test Fixtures

The `tests_shared/fixtures.py` module provides reusable test fixtures:

```python
from agent.tests_shared.fixtures import (
    temp_agent_dir,              # Temporary directory structure
    sample_project_dir,           # Sample HTML/CSS/JS project
    sample_project_with_snapshots, # Project with iteration history
    sample_run_summary,           # Mock run data
    sample_job,                   # Mock Job object
    sample_qa_config,             # QA configuration
    sample_qa_report,             # QA report data
    create_minimal_html_project,  # Helper function
)
```

### Writing New Tests

**Example test structure:**

```python
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from webapp.app import app
    return TestClient(app)

def test_example_endpoint(client):
    """Test description."""
    response = client.get("/api/example")
    assert response.status_code == 200
    assert "expected_key" in response.json()
```

**Best practices:**
- Use descriptive test names: `test_<what>_<condition>`
- Mock heavy operations (LLM calls, file I/O)
- Use temporary directories (`tmp_path` fixture)
- Test both success and error cases
- Verify status codes, data structure, and error messages
- Use shared fixtures to reduce duplication

### Continuous Integration

GitHub Actions CI workflow runs on every push:

```yaml
# .github/workflows/tests.yml
- Python 3.9+ compatibility
- All unit tests
- E2E tests (optional)
- Coverage reporting
```

To run the same checks locally:
```bash
pytest --cov=agent --cov-report=term
```

## Development

### VSCode Integration

Launch configurations and tasks are provided in `.vscode/`:

**Debug Configurations:**
- Run Single Orchestrator Run
- Run Auto-Pilot Mode
- Debug Orchestrator (3-loop)
- Profile Run
- Run Sanity Tests
- Generate Documentation

**Build Tasks:**
- Run: Single Orchestrator Run
- Run: Auto-Pilot Mode
- Test: Sanity Tests
- Test: MyPy
- Test: Ruff
- Clean: Delete Logs
- Docs: Generate Reference

### Git Hooks

Install the pre-commit hook:

```bash
git config core.hooksPath .githooks
```

The hook runs:
- Import validation
- Sanity tests
- Ruff linting
- MyPy type checking

All checks are graceful - missing tools won't fail the commit.

### Documentation

**Generate API reference:**
```bash
python docs/generate_docs.py
```

**View developer guide:**
```bash
cat DEVELOPER_GUIDE.md
```

**View Stage 7 docs:**
```bash
cat docs/STAGE7_WEB_UI.md
```

## Documentation

- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Complete developer documentation
- **[docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md)** - Web dashboard guide
- **[docs/STAGE8_JOB_MANAGER.md](docs/STAGE8_JOB_MANAGER.md)** - Job manager guide
- **[docs/STAGE9_PROJECT_EXPLORER.md](docs/STAGE9_PROJECT_EXPLORER.md)** - Project explorer guide
- **[docs/STAGE10_QA_PIPELINE.md](docs/STAGE10_QA_PIPELINE.md)** - Quality assurance guide
- **[docs/STAGE11_ANALYTICS_DASHBOARD.md](docs/STAGE11_ANALYTICS_DASHBOARD.md)** - Analytics & insights guide 🆕
- **[docs/REFERENCE.md](docs/REFERENCE.md)** - Auto-generated API reference

## Architecture

### Orchestration Flow

**3-loop mode:**
```
User → Manager (planning)
     → Supervisor (phasing)
     → Employee (implementation per phase)
     → Manager (review)
     → [iterate or approve]
```

**2-loop mode:**
```
User → Manager (planning)
     → Employee (implementation)
     → Manager (review)
     → [iterate or approve]
```

### Web Dashboard Flow (Stage 7-8)

**Stage 7 (Blocking):**
```
User → Web UI (form)
     → FastAPI app (validation)
     → runner.run_project() (API)
     → Orchestrator (execution)
     → run_logger (save results)
     → Web UI (display)
```

**Stage 8 (Background Jobs):**
```
User → Web UI (form)
     → FastAPI app (create job)
     → JobManager (background thread)
     → runner.run_project() (API)
     → Orchestrator (execution)
     → run_logger (save results)
     → Job state updated
User polls → Job detail page
          → API (get logs)
          → Live updates
```

### Key Components

- **orchestrator.py**: 3-loop orchestration logic
- **run_mode.py**: CLI entry point with cost estimation
- **runner.py**: Programmatic API for web dashboard
- **jobs.py**: Job manager for background execution (Stage 8)
- **analytics.py**: Analytics engine with aggregations (Stage 11)
- **webapp/app.py**: FastAPI web application
- **run_logger.py**: Structured logging (RunSummary, SessionSummary)
- **cost_tracker.py**: Token usage and cost tracking
- **auto_pilot.py**: Multi-run self-evaluation
- **exec_safety.py**: Safety checks and analysis

## Stages

- **Stage 0**: Baseline 2-loop orchestrator
- **Stage 1**: Safety pack (execution safety, analysis, dependency scanning)
- **Stage 2**: Run logging and evaluation layer
- **Stage 3**: Cost control and quality-of-life features
- **Stage 4**: Auto-pilot mode with self-evaluation
- **Stage 5**: Production hardening (status codes, safe I/O, tests)
- **Stage 6**: Developer experience (dev tools, VSCode, docs)
- **Stage 7**: Web dashboard with forms and history
- **Stage 8**: Job manager with background execution
- **Stage 9**: Project explorer with snapshots and diff viewer
- **Stage 10**: Quality assurance pipeline with automated checks
- **Stage 11**: Analytics & insights dashboard
- **Stage 12**: Self-optimization & auto-tuning layer ("brain") 🆕

## Contributing

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for:
- Coding standards
- Testing guidelines
- How to extend the system
- Architecture details

## License

[Your license here]

## Support

For issues or questions:
- Check [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- Check [docs/STAGE7_WEB_UI.md](docs/STAGE7_WEB_UI.md)
- Review existing run logs for debugging
- Check sanity tests: `python make.py test`
