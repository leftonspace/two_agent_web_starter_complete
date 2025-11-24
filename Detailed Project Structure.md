# THE JARVIS BIBLE
## Complete System Reference & Architecture Documentation

> **Version:** 2.1.0
> **Last Updated:** 2025-11-24
> **Total Files:** 400+
> **Total Lines of Code:** 150,000+

---

# PART I: WHAT IS JARVIS?

## 1.1 Overview

**JARVIS** (Just A Rather Very Intelligent System) is an enterprise-grade, multi-agent AI orchestration platform designed to function as an autonomous digital employee. Named after the AI assistant from Iron Man, JARVIS combines multiple AI capabilities into a unified, self-improving system.

JARVIS is NOT just a chatbot. It is a **complete autonomous agent system** that can:
- Execute complex multi-step tasks without human intervention
- Coordinate multiple AI agents working in parallel
- Remember user preferences and business context across sessions
- Join meetings, transcribe, and take action items automatically
- Generate documents, analyze data, and manage workflows
- Self-optimize based on performance data

## 1.2 Core Philosophy

JARVIS operates on these principles:
1. **Proactive, Not Reactive** - Anticipates needs, doesn't just respond
2. **Multi-Agent Collaboration** - Complex tasks are broken into specialized sub-tasks
3. **Persistent Memory** - Learns and remembers across all interactions
4. **Safety First** - Multiple layers of validation before any risky action
5. **Transparent Operations** - All actions are logged and auditable
6. **Self-Improvement** - Continuously optimizes based on performance data

---

# PART II: COMPLETE JARVIS FUNCTIONS

## 2.1 Core AI Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Natural Language Understanding** | Parse and understand user requests | `jarvis_chat.py` |
| **Intent Classification** | Route requests to appropriate handlers | `jarvis_chat.py` |
| **Multi-Step Planning** | Break complex tasks into executable steps | `conversational_agent.py` |
| **Task Orchestration** | Coordinate multiple agents on a task | `orchestrator.py` |
| **Context Retrieval** | Fetch relevant context for any query | `memory/context_retriever.py` |

## 2.2 Agent Management Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Agent Spawning** | Create new specialist agents on demand | `council/factory.py` |
| **Agent Coordination** | Manage parallel agent execution | `council/orchestrator.py` |
| **Weighted Voting** | Democratic decision-making among agents | `council/voting.py` |
| **Happiness Management** | Track and optimize agent morale | `council/happiness.py` |
| **Performance Tracking** | Monitor agent success rates | `council/models.py` |
| **Agent Lifecycle** | Hire, fire, promote agents based on performance | `council/graveyard.py` |

## 2.3 Tool Execution Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **File Reading** | Read any file with line ranges | `jarvis_tools.py` |
| **File Writing** | Create new files safely | `jarvis_tools.py` |
| **File Editing** | Targeted string replacements | `jarvis_tools.py` |
| **Code Search (Grep)** | Regex pattern search across files | `jarvis_tools.py` |
| **File Search (Glob)** | Find files by pattern | `jarvis_tools.py` |
| **Shell Execution** | Run bash commands safely | `jarvis_tools.py` |
| **Web Search** | Search the internet | `jarvis_tools.py` |
| **Web Fetch** | Fetch webpage content | `jarvis_tools.py` |
| **Code Execution** | Run Python/JS in sandbox | `actions/code_executor.py` |
| **API Calls** | Universal HTTP client | `actions/api_client.py` |
| **Database Queries** | Safe SQL execution | `actions/db_client.py` |
| **Git Operations** | Full git repository management | `actions/git_ops.py` |

## 2.4 Memory Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Short-Term Memory** | Current conversation context | `memory/short_term.py` |
| **Long-Term Memory** | Persistent user knowledge | `memory/long_term.py` |
| **Entity Extraction** | Identify people, places, concepts | `memory/entity.py` |
| **Vector Search** | Semantic similarity search | `memory/vector_store.py` |
| **User Profiling** | Learn user preferences | `memory/user_profile.py` |
| **Preference Learning** | Adapt to user patterns | `memory/preference_learner.py` |
| **Session Management** | Per-chat isolation | `memory/session_manager.py` |
| **Business Memory** | Company/project context | `business_memory/manager.py` |

## 2.5 Meeting Intelligence Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Zoom Integration** | Join Zoom meetings as participant | `meetings/zoom_bot.py` |
| **Teams Integration** | Join Microsoft Teams meetings | `meetings/teams_bot.py` |
| **Google Meet Bot** | Join Google Meet sessions | `meetings/google_meet_bot.py` |
| **Live Audio Capture** | Record in-person meetings | `meetings/live_audio_bot.py` |
| **Speech-to-Text** | Real-time transcription | `meetings/transcription/` |
| **Speaker Diarization** | Identify who spoke when | `meetings/diarization/` |
| **Action Item Extraction** | Find tasks from discussion | `meetings/intelligence/meeting_analyzer.py` |
| **Decision Tracking** | Capture decisions made | `meetings/intelligence/meeting_analyzer.py` |
| **Cross-Meeting Context** | Link related meetings | `meetings/cross_meeting_context.py` |

## 2.6 Document Generation Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **PDF Generation** | Create PDF documents | `documents/pdf_generator.py` |
| **Word Generation** | Create .docx files | `documents/word_generator.py` |
| **Excel Generation** | Create spreadsheets | `documents/excel_generator.py` |
| **Email Templates** | Render email HTML | `templates/email_renderer.py` |
| **Financial Templates** | Create financial documents | `finance/financial_templates.py` |

## 2.7 Business Action Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Domain Purchase** | Buy domains via Namecheap | `tools/actions/buy_domain.py` |
| **Website Deployment** | Deploy to Vercel | `tools/actions/deploy_website.py` |
| **SMS Messaging** | Send SMS via Twilio | `tools/actions/send_sms.py` |
| **Payment Processing** | Stripe integration | `tools/actions/make_payment.py` |
| **Email Sending** | Send emails programmatically | `tools/hr/send_email.py` |
| **Calendar Events** | Create calendar entries | `tools/hr/create_calendar_event.py` |
| **HRIS Records** | HR system integration | `tools/hr/create_hris_record.py` |

## 2.8 Security & Safety Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Prompt Injection Defense** | Detect malicious prompts | `prompt_security.py` |
| **Secret Scanning** | Find exposed credentials | `git_secret_scanner.py` |
| **Approval Workflows** | Human approval for risky actions | `approval_engine.py` |
| **Audit Logging** | Complete action trail | `audit_log.py` |
| **Rate Limiting** | Prevent API abuse | `security/rate_limit.py` |
| **Authentication** | User identity verification | `security/auth.py` |
| **Execution Safety** | Validate before execute | `exec_safety.py` |
| **Static Analysis** | Code vulnerability scanning | `static_analysis.py` |

## 2.9 Vision & Voice Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Image Analysis** | Understand images/screenshots | `jarvis_vision.py` |
| **Scene Understanding** | Object and scene detection | `vision_api.py` |
| **OCR** | Extract text from images | `jarvis_vision.py` |
| **Text-to-Speech** | Voice output (ElevenLabs/OpenAI) | `jarvis_voice.py` |
| **Speech-to-Text** | Voice input recognition | `voice_api.py` |
| **Voice Chat** | Full voice conversations | `jarvis_voice_chat.py` |

## 2.10 Administration Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Calendar Intelligence** | Smart scheduling | `admin/calendar_intelligence.py` |
| **Email Integration** | Email automation | `admin/email_integration.py` |
| **Workflow Automation** | Business process automation | `admin/workflow_automation.py` |
| **Monitoring & Alerts** | System health tracking | `monitoring/alerts.py` |
| **Metrics Collection** | Performance metrics | `monitoring/metrics.py` |
| **Cost Tracking** | Token usage & spending | `cost_tracker.py` |
| **Analytics Engine** | Usage analytics | `analytics.py` |
| **Self-Optimization** | Auto-tuning system | `brain.py` |

---

# PART III: COMPLETE FILE REFERENCE

## Directory: `/` (Root)

### Configuration Files

#### `.env.example`
- **Definition:** Template for environment variables
- **Importance:** Guides users on required API keys and configuration
- **Links to:** All modules that read environment variables

#### `.gitignore`
- **Definition:** Specifies files Git should ignore
- **Importance:** Prevents sensitive data and build artifacts from being committed
- **Links to:** Git operations throughout the system

#### `requirements.txt`
- **Definition:** Python package dependencies
- **Importance:** Ensures all required libraries are installed
- **Links to:** Every Python module in the project

#### `make.py`
- **Definition:** Command dispatcher for common operations
- **Importance:** Single entry point for development commands (test, run, docs)
- **Links to:** `dev/` scripts, test runners

### Documentation Files

#### `README.md`
- **Definition:** Main project documentation
- **Importance:** First point of contact for new users/developers
- **Links to:** All major documentation files in `docs/`

#### `DEVELOPER_GUIDE.md`
- **Definition:** Guide for contributors and developers
- **Importance:** Explains coding standards, testing, architecture
- **Links to:** `agent/` modules, `tests/`, `docs/`

#### `JARVIS_ARCHITECTURE.md`
- **Definition:** Complete system architecture documentation
- **Importance:** Technical reference for understanding system design
- **Links to:** All core modules, API endpoints, memory system

#### `CHANGELOG.md`
- **Definition:** Version history and changes
- **Importance:** Track what changed between versions
- **Links to:** All modules that were changed

### Entry Points

#### `orchestrator.py` (Root)
- **Definition:** Root-level orchestrator entry point
- **Importance:** Backward compatibility with older startup methods
- **Links to:** `agent/orchestrator.py`, `agent/run_mode.py`

#### `start_webapp.py`
- **Definition:** Web application launcher
- **Importance:** Single command to start the web server
- **Links to:** `agent/webapp/app.py`

---

## Directory: `/.githooks/`

### `pre-commit`
- **Definition:** Git hook script that runs before each commit
- **Importance:** Ensures code quality by running linters, tests, and validation
- **Links to:** `ruff.toml`, `mypy.ini`, test files

---

## Directory: `/.github/workflows/`

### `tests.yml`
- **Definition:** GitHub Actions CI/CD workflow configuration
- **Importance:** Automated testing on every push/PR
- **Links to:** All test files, `requirements.txt`

---

## Directory: `/.vscode/`

### `launch.json`
- **Definition:** VSCode debug configurations
- **Importance:** One-click debugging for various scenarios
- **Links to:** `run_mode.py`, `webapp/app.py`, test files

### `tasks.json`
- **Definition:** VSCode build tasks
- **Importance:** Quick access to common commands from VSCode
- **Links to:** `make.py`, test runners, linters

---

## Directory: `/agent/`

This is the **core of JARVIS** - containing all orchestration, agent, and business logic.

### Core Orchestration

#### `orchestrator.py`
- **Definition:** The 3-loop multi-agent orchestrator (Manager → Supervisor → Employee)
- **Importance:** Heart of the multi-agent system; coordinates all complex tasks
- **Links to:**
  - `llm.py` - For LLM calls
  - `prompts.py` - For prompt templates
  - `run_logger.py` - For logging
  - `cost_tracker.py` - For cost management
  - `workflow_manager.py` - For workflow management
  - `inter_agent_bus.py` - For agent communication
  - `memory_store.py` - For persistent memory
  - `site_tools.py` - For file operations
  - `git_utils.py` - For Git integration

#### `orchestrator_2loop.py`
- **Definition:** Simplified 2-loop orchestrator (Manager → Employee direct)
- **Importance:** Faster execution for simpler tasks without supervisor
- **Links to:** Same as `orchestrator.py` minus supervisor components

#### `orchestrator_3loop_legacy.py`
- **Definition:** Legacy 3-loop implementation for backward compatibility
- **Importance:** Maintains compatibility with older configurations
- **Links to:** `orchestrator.py`

#### `orchestrator_context.py`
- **Definition:** Context object passed through orchestration pipeline
- **Importance:** Maintains state and configuration throughout task execution
- **Links to:** All orchestrator modules

#### `orchestrator_integration.py`
- **Definition:** Integration layer for external orchestrator connections
- **Importance:** Allows orchestrator to connect with external systems
- **Links to:** `orchestrator.py`, external APIs

#### `orchestrator_phase3.py`
- **Definition:** Phase 3 adaptive orchestrator with dynamic roadmaps
- **Importance:** Advanced orchestration with stage-based execution
- **Links to:** `workflow_manager.py`, `inter_agent_bus.py`, `stage_summaries.py`

### JARVIS Core Identity

#### `jarvis_agent.py`
- **Definition:** The autonomous tool-using agent core
- **Importance:** Enables proactive tool usage similar to Claude Code
- **Links to:**
  - `jarvis_tools.py` - Tool implementations
  - `llm.py` - LLM interface
  - Event streaming system

#### `jarvis_chat.py`
- **Definition:** Main chat router and intent classifier
- **Importance:** Entry point for all user interactions; routes to appropriate handlers
- **Links to:**
  - `jarvis_agent.py` - For tool-using tasks
  - `conversational_agent.py` - For complex planning
  - `orchestrator.py` - For multi-step tasks
  - `memory/` - For context retrieval
  - `jarvis_persona.py` - For personality

#### `jarvis_tools.py`
- **Definition:** Claude Code-like tools (read, write, edit, bash, grep, glob)
- **Importance:** Core capability set for file and system operations
- **Links to:**
  - `actions/file_ops.py` - File system safety
  - `actions/git_ops.py` - Git operations
  - `exec_safety.py` - Execution safety

#### `jarvis_persona.py`
- **Definition:** JARVIS personality definition and system prompt
- **Importance:** Defines JARVIS's British butler personality and behavior
- **Links to:** `jarvis_chat.py`, `jarvis_agent.py`

#### `jarvis_vision.py`
- **Definition:** Image analysis and visual understanding capabilities
- **Importance:** Enables JARVIS to see and understand images/screenshots
- **Links to:** `vision_api.py`, LLM providers with vision

#### `jarvis_voice.py`
- **Definition:** Text-to-speech synthesis (ElevenLabs, OpenAI TTS)
- **Importance:** Gives JARVIS a voice for audio responses
- **Links to:** External TTS APIs

#### `jarvis_voice_chat.py`
- **Definition:** Full voice conversation handler
- **Importance:** Enables hands-free voice interaction
- **Links to:** `jarvis_voice.py`, `voice_api.py`, `jarvis_chat.py`

### Agent Communication

#### `agent_api.py`
- **Definition:** API interface for agent operations
- **Importance:** Exposes agent functionality via API endpoints
- **Links to:** `webapp/agent_api.py`, `jarvis_agent.py`

#### `agent_messaging.py`
- **Definition:** Message bus for agent-to-user communication
- **Importance:** Structured message passing with role information
- **Links to:** All agent modules, `webapp/`

#### `agents_api.py`
- **Definition:** API endpoints for agent management
- **Importance:** RESTful interface for agent operations
- **Links to:** `webapp/app.py`

#### `inter_agent_bus.py`
- **Definition:** Message bus for agent-to-agent communication
- **Importance:** Enables horizontal communication between agents
- **Links to:** `orchestrator.py`, `council/orchestrator.py`

### Conversational AI

#### `conversational_agent.py`
- **Definition:** NLP-based task planning and natural language interface
- **Importance:** Translates natural language into executable plans
- **Links to:** `jarvis_chat.py`, `llm.py`, `tool_registry.py`

#### `cli_chat.py`
- **Definition:** Command-line chat interface
- **Importance:** Enables terminal-based interaction with JARVIS
- **Links to:** `jarvis_chat.py`, `conversational_agent.py`

### LLM Integration

#### `llm.py`
- **Definition:** Main LLM interface and provider abstraction
- **Importance:** Central point for all LLM API calls
- **Links to:**
  - `llm/providers.py` - Provider implementations
  - `llm/llm_router.py` - Model routing
  - `cost_tracker.py` - Usage tracking
  - All modules that need LLM calls

#### `llm_cache.py`
- **Definition:** Response caching for LLM calls
- **Importance:** Reduces costs and latency for repeated queries
- **Links to:** `llm.py`

### Configuration

#### `config.py`
- **Definition:** Configuration management and validation
- **Importance:** Centralized configuration handling
- **Links to:** All modules that use configuration

#### `config_loader.py`
- **Definition:** YAML/JSON configuration file loader
- **Importance:** Loads and validates configuration files
- **Links to:** `config/agents.yaml`, `config/tasks.yaml`

#### `project_config.json`
- **Definition:** Default project configuration
- **Importance:** Defines default settings for new projects
- **Links to:** `run_mode.py`, `runner.py`

### Cost Management

#### `cost_tracker.py`
- **Definition:** Token usage and cost tracking
- **Importance:** Monitors API spending and enforces budgets
- **Links to:** `llm.py`, `run_logger.py`, `analytics.py`

#### `cost_tracker_instance.py`
- **Definition:** Singleton instance of cost tracker
- **Importance:** Ensures consistent cost tracking across modules
- **Links to:** `cost_tracker.py`

#### `cost_estimator.py`
- **Definition:** Pre-execution cost estimation
- **Importance:** Predicts costs before running expensive operations
- **Links to:** `cost_tracker.py`, `run_mode.py`

### Logging & Monitoring

#### `run_logger.py`
- **Definition:** Structured run logging (RunSummary, SessionSummary)
- **Importance:** Creates detailed logs of all orchestrator runs
- **Links to:** `orchestrator.py`, `run_logs/`

#### `core_logging.py`
- **Definition:** Core logging configuration
- **Importance:** Standardized logging across all modules
- **Links to:** All modules

#### `log_sanitizer.py`
- **Definition:** Remove sensitive data from logs
- **Importance:** Security - prevents credentials in logs
- **Links to:** `run_logger.py`, `audit_log.py`

#### `audit_log.py`
- **Definition:** Audit trail for all actions
- **Importance:** Compliance and security tracking
- **Links to:** All action modules, `security/audit_log.py`

### Safety & Security

#### `exec_safety.py`
- **Definition:** Execution safety checks and validation
- **Importance:** Prevents dangerous operations before execution
- **Links to:** `jarvis_tools.py`, `actions/code_executor.py`

#### `exec_analysis.py`
- **Definition:** Static analysis of code before execution
- **Importance:** Detects potentially harmful code patterns
- **Links to:** `exec_safety.py`

#### `exec_deps.py`
- **Definition:** Dependency analysis for execution
- **Importance:** Ensures all dependencies are available
- **Links to:** `exec_safety.py`

#### `exec_tools.py`
- **Definition:** Tool metadata and execution helpers
- **Importance:** Provides tool information for orchestrator
- **Links to:** `orchestrator.py`, `tool_registry.py`

#### `prompt_security.py`
- **Definition:** Prompt injection detection and defense
- **Importance:** Protects against malicious prompt attacks
- **Links to:** `jarvis_chat.py`, `llm.py`

#### `static_analysis.py`
- **Definition:** Static code analysis for vulnerabilities
- **Importance:** Security scanning before code execution
- **Links to:** `exec_safety.py`, `code_analysis/`

#### `git_secret_scanner.py`
- **Definition:** Scans git history for exposed secrets
- **Importance:** Prevents accidental credential exposure
- **Links to:** `git_utils.py`, `security/`

### Git Integration

#### `git_utils.py`
- **Definition:** Git utility functions
- **Importance:** Provides git operations for version control
- **Links to:** `orchestrator.py`, `actions/git_ops.py`

#### `github_integration.py`
- **Definition:** GitHub API integration
- **Importance:** Enables GitHub operations (PRs, issues, etc.)
- **Links to:** `git_utils.py`, external GitHub API

### Workflow Management

#### `workflow_manager.py`
- **Definition:** Dynamic workflow/roadmap management
- **Importance:** Manages stage-based execution flow
- **Links to:** `orchestrator.py`, `workflow_enforcement.py`

#### `workflow_enforcement.py`
- **Definition:** Workflow rule enforcement
- **Importance:** Ensures workflows follow defined patterns
- **Links to:** `workflow_manager.py`, `workflows/`

### Miscellaneous Core

#### `_errors.py`
- **Definition:** Custom exception definitions
- **Importance:** Standardized error handling
- **Links to:** All modules

#### `paths.py`
- **Definition:** Path utilities and constants
- **Importance:** Centralized path management
- **Links to:** All modules dealing with files

#### `status_codes.py`
- **Definition:** Normalized status codes
- **Importance:** Consistent status reporting
- **Links to:** `orchestrator.py`, `webapp/`

#### `safe_io.py`
- **Definition:** Safe I/O operations
- **Importance:** Prevents race conditions and file corruption
- **Links to:** File operation modules

#### `sandbox.py`
- **Definition:** Sandboxed execution environment
- **Importance:** Isolates potentially dangerous operations
- **Links to:** `actions/sandbox.py`, `exec_safety.py`

---

## Directory: `/agent/actions/`

Action execution modules for performing real-world operations.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports action modules
- **Links to:** All action modules

### `api_client.py`
- **Definition:** Universal HTTP client with retry and rate limiting
- **Importance:** All external API calls go through this
- **Links to:**
  - `rate_limiter.py` - Rate limiting
  - External APIs (Stripe, Twilio, etc.)

### `code_executor.py`
- **Definition:** Multi-language code execution (Python, JS, Shell)
- **Importance:** Safe execution of generated code
- **Links to:**
  - `sandbox.py` - Sandboxed execution
  - `exec_safety.py` - Safety validation
  - Whitelist of allowed imports/commands

### `db_client.py`
- **Definition:** Database client with read-only mode
- **Importance:** Safe SQL execution with parameterization
- **Links to:**
  - PostgreSQL, MySQL, SQLite drivers
  - `integrations/database.py`

### `file_ops.py`
- **Definition:** File system operations with safety
- **Importance:** All file operations with path validation
- **Links to:**
  - `jarvis_tools.py` - Tool interface
  - `exec_safety.py` - Path validation
  - Restricted paths configuration

### `git_ops.py`
- **Definition:** Git repository operations
- **Importance:** Full git functionality (init, commit, push, branch)
- **Links to:**
  - `git_utils.py` - Git utilities
  - `github_integration.py` - GitHub API

### `rate_limiter.py`
- **Definition:** Token bucket rate limiter
- **Importance:** Prevents API overload
- **Links to:** `api_client.py`, all external API calls

### `sandbox.py`
- **Definition:** Execution sandbox implementation
- **Importance:** Isolates code execution for security
- **Links to:** `code_executor.py`, `exec_safety.py`

---

## Directory: `/agent/admin/`

Administrative and business automation tools.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports admin modules
- **Links to:** All admin modules

### `calendar_intelligence.py`
- **Definition:** Smart calendar management and scheduling
- **Importance:** Intelligent meeting scheduling and availability
- **Links to:**
  - External calendar APIs (Google, Outlook)
  - `tools/hr/create_calendar_event.py`

### `email_integration.py`
- **Definition:** Email automation and management
- **Importance:** Send, read, and organize emails
- **Links to:**
  - SMTP/IMAP providers
  - `tools/hr/send_email.py`
  - `templates/email/`

### `workflow_automation.py`
- **Definition:** Business process automation
- **Importance:** Automate repetitive business workflows
- **Links to:**
  - `workflows/` - Workflow definitions
  - `approval_engine.py`

---

## Directory: `/agent/business_memory/`

Business context and company knowledge management.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports business memory modules
- **Links to:** All business memory modules

### `extractor.py`
- **Definition:** Extract business information from conversations
- **Importance:** Automatically captures company/project details
- **Links to:**
  - `memory/entity.py` - Entity extraction
  - `manager.py` - Storage

### `manager.py`
- **Definition:** Business memory management
- **Importance:** Store and retrieve business context
- **Links to:**
  - `memory/long_term.py` - Persistence
  - `privacy.py` - Privacy controls
  - `schema.py` - Data structure

### `privacy.py`
- **Definition:** Privacy controls for business data
- **Importance:** Ensures sensitive business data is protected
- **Links to:**
  - `manager.py`
  - `security/` modules

### `schema.py`
- **Definition:** Business memory data schemas
- **Importance:** Defines structure of business information
- **Links to:** `manager.py`, `extractor.py`

---

## Directory: `/agent/clarification/`

Ambiguity detection and clarification question system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports clarification modules
- **Links to:** All clarification modules

### `detector.py`
- **Definition:** Detects ambiguous or unclear requests
- **Importance:** Identifies when clarification is needed
- **Links to:**
  - `jarvis_chat.py` - Main chat handler
  - `generator.py` - Question generation

### `generator.py`
- **Definition:** Generates clarification questions
- **Importance:** Creates helpful questions to resolve ambiguity
- **Links to:**
  - `templates.py` - Question templates
  - `llm.py` - LLM for question generation

### `manager.py`
- **Definition:** Manages clarification workflow
- **Importance:** Orchestrates the clarification process
- **Links to:**
  - `detector.py`
  - `generator.py`
  - `jarvis_chat.py`

### `templates.py`
- **Definition:** Question templates for common clarification types
- **Importance:** Consistent question format
- **Links to:** `generator.py`

---

## Directory: `/agent/code_analysis/`

Code understanding and refactoring tools.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports code analysis modules
- **Links to:** All code analysis modules

### `ast_parser.py`
- **Definition:** Python AST parsing and analysis
- **Importance:** Deep understanding of Python code structure
- **Links to:**
  - `patterns.py` - Pattern detection
  - `refactoring.py` - Code transformation

### `js_parser.py`
- **Definition:** JavaScript parsing and analysis
- **Importance:** Understanding of JavaScript/TypeScript code
- **Links to:** `patterns.py`, `refactoring.py`

### `patterns.py`
- **Definition:** Code pattern detection
- **Importance:** Find common patterns and anti-patterns
- **Links to:**
  - `ast_parser.py`, `js_parser.py`
  - `static_analysis.py`

### `refactoring.py`
- **Definition:** Code refactoring tools
- **Importance:** Automated code improvements
- **Links to:**
  - `ast_parser.py`, `js_parser.py`
  - `jarvis_tools.py` - For file edits

---

## Directory: `/agent/code_review/`

Automated code review system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports code review modules
- **Links to:** All code review modules

### `review_agent.py`
- **Definition:** AI-powered code review agent
- **Importance:** Automated PR and code review
- **Links to:**
  - `code_analysis/` - Code understanding
  - `github_integration.py` - GitHub PR integration
  - `llm.py` - Review generation

---

## Directory: `/agent/config/`

YAML-based configuration system.

### `agents.yaml`
- **Definition:** Agent definitions (role, llm, tools, capabilities)
- **Importance:** Defines all available agent types
- **Links to:**
  - `config_loader.py` - Loading
  - `specialists.py` - Agent creation
  - `council/factory.py` - Agent spawning

### `tasks.yaml`
- **Definition:** Task templates and workflows
- **Importance:** Reusable task definitions
- **Links to:**
  - `config_loader.py` - Loading
  - `orchestrator.py` - Task execution

### `/schemas/agent_schema.json`
- **Definition:** JSON schema for agent configuration
- **Importance:** Validates agent YAML structure
- **Links to:** `validators/config_validator.py`

### `/schemas/task_schema.json`
- **Definition:** JSON schema for task configuration
- **Importance:** Validates task YAML structure
- **Links to:** `validators/config_validator.py`

---

## Directory: `/agent/core/`

Core utilities and patterns.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports core modules
- **Links to:** All core modules

### `circuit_breaker.py`
- **Definition:** Circuit breaker pattern implementation
- **Importance:** Prevents cascade failures in external calls
- **Links to:**
  - `api_client.py`
  - `llm.py`
  - All external service calls

### `error_handler.py`
- **Definition:** Centralized error handling
- **Importance:** Consistent error processing and recovery
- **Links to:** All modules

---

## Directory: `/agent/council/`

Multi-agent council and voting system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports council modules
- **Links to:** All council modules

### `competitive_council.py`
- **Definition:** Competitive analysis among councillors
- **Importance:** Enables head-to-head agent comparison
- **Links to:**
  - `orchestrator.py` - Council orchestrator
  - `voting.py` - Voting system

### `factory.py`
- **Definition:** Councillor creation factory
- **Importance:** Spawns new agent councillors from templates
- **Links to:**
  - `models.py` - Councillor model
  - `config/agents.yaml` - Agent templates
  - `specialists.py`

### `graveyard.py`
- **Definition:** Fired councillor tracking
- **Importance:** Records agent terminations for analysis
- **Links to:**
  - `orchestrator.py` - Council orchestrator
  - `happiness.py` - Happiness tracking

### `happiness.py`
- **Definition:** Agent happiness/morale management
- **Importance:** Tracks and optimizes agent satisfaction
- **Links to:**
  - `models.py` - Happiness model
  - `orchestrator.py` - Happiness updates
  - `voting.py` - Happiness affects vote weight

### `models.py`
- **Definition:** Council data models (Councillor, Vote, Task)
- **Importance:** Defines all council-related data structures
- **Links to:** All council modules

### `orchestrator.py`
- **Definition:** Council leader - coordinates councillors
- **Importance:** Main council coordination logic
- **Links to:**
  - `voting.py` - Voting management
  - `happiness.py` - Happiness management
  - `factory.py` - Councillor creation
  - `inter_agent_bus.py` - Agent communication

### `voting.py`
- **Definition:** Weighted voting system
- **Importance:** Democratic decision-making among agents
- **Links to:**
  - `models.py` - Vote model
  - `happiness.py` - Happiness affects weight
  - `orchestrator.py`

---

## Directory: `/agent/database/`

Database utilities and migrations.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports database modules
- **Links to:** All database modules

### `kg_backends.py`
- **Definition:** Knowledge graph database backends
- **Importance:** Supports different KG storage options
- **Links to:** `knowledge_graph.py`

### `pg_migration.py`
- **Definition:** PostgreSQL migration utilities
- **Importance:** Database schema migrations
- **Links to:** `migrations/`, `integrations/database.py`

---

## Directory: `/agent/deployment/`

Deployment and rollback utilities.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports deployment modules
- **Links to:** All deployment modules

### `rollback.py`
- **Definition:** Deployment rollback management
- **Importance:** Safely rollback failed deployments
- **Links to:**
  - `tools/actions/deploy_website.py`
  - `git_utils.py`

---

## Directory: `/agent/documents/`

Document generation engines.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports document modules
- **Links to:** All document modules

### `excel_generator.py`
- **Definition:** Excel/spreadsheet generation
- **Importance:** Create .xlsx files programmatically
- **Links to:**
  - `tools/documents/generate_excel.py`
  - `finance/spreadsheet_engine.py`

### `pdf_generator.py`
- **Definition:** PDF document generation
- **Importance:** Create PDF files programmatically
- **Links to:** `tools/documents/generate_pdf.py`

### `word_generator.py`
- **Definition:** Word document generation
- **Importance:** Create .docx files programmatically
- **Links to:** `tools/documents/generate_word.py`

---

## Directory: `/agent/execution/`

Task execution and routing.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports execution modules
- **Links to:** All execution modules

### `direct_executor.py`
- **Definition:** Fast-path direct execution (bypasses multi-agent)
- **Importance:** Quick execution for simple, safe tasks
- **Links to:**
  - `strategy_decider.py` - Decides when to use
  - `jarvis_tools.py` - Tool execution

### `employee_pool.py`
- **Definition:** Pool of employee agents for parallel execution
- **Importance:** Enables concurrent task execution
- **Links to:**
  - `task_distributor.py` - Task distribution
  - `orchestrator.py`

### `review_queue.py`
- **Definition:** Supervisor review queue
- **Importance:** Quality gates before task completion
- **Links to:**
  - `task_router.py`
  - `orchestrator.py`

### `strategy_decider.py`
- **Definition:** Decides execution strategy (direct, reviewed, full loop)
- **Importance:** Optimizes execution path based on task complexity
- **Links to:**
  - `task_router.py`
  - `direct_executor.py`
  - `orchestrator.py`

### `task_distributor.py`
- **Definition:** Distributes tasks to workers with priorities
- **Importance:** Load balancing and priority scheduling
- **Links to:**
  - `employee_pool.py`
  - `task_router.py`

### `task_router.py`
- **Definition:** Routes tasks to appropriate execution mode
- **Importance:** Single entry point for all task execution
- **Links to:**
  - `strategy_decider.py`
  - `direct_executor.py`
  - `review_queue.py`
  - `orchestrator.py`

---

## Directory: `/agent/finance/`

Financial tools and document generation.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports finance modules
- **Links to:** All finance modules

### `document_intelligence.py`
- **Definition:** Financial document analysis
- **Importance:** Extract data from financial documents
- **Links to:**
  - `jarvis_vision.py` - Document OCR
  - `memory/` - Store extracted data

### `financial_templates.py`
- **Definition:** Financial document templates
- **Importance:** Standard financial document formats
- **Links to:**
  - `documents/` - Document generation
  - `webapp/finance_api.py`

### `spreadsheet_engine.py`
- **Definition:** Financial spreadsheet calculations
- **Importance:** Complex financial calculations
- **Links to:**
  - `documents/excel_generator.py`
  - `financial_templates.py`

---

## Directory: `/agent/flow/`

State machine and workflow flow engine.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports flow modules
- **Links to:** All flow modules

### `decorators.py`
- **Definition:** Flow step decorators
- **Importance:** Declarative flow definition
- **Links to:** `engine.py`

### `engine.py`
- **Definition:** Flow execution engine
- **Importance:** Executes state machine workflows
- **Links to:**
  - `graph.py` - Flow graph
  - `state.py` - Flow state
  - `events.py` - Flow events

### `events.py`
- **Definition:** Flow event definitions
- **Importance:** Event-driven flow transitions
- **Links to:** `engine.py`

### `graph.py`
- **Definition:** Flow graph data structure
- **Importance:** Defines flow topology
- **Links to:** `engine.py`

### `state.py`
- **Definition:** Flow state management
- **Importance:** Tracks current flow state
- **Links to:** `engine.py`

---

## Directory: `/agent/integrations/`

External system integrations.

### `auth.py`
- **Definition:** Authentication for integrations
- **Importance:** Secure connection to external systems
- **Links to:** All integration modules

### `base.py`
- **Definition:** Base integration class
- **Importance:** Common integration interface
- **Links to:** All integration modules

### `database.py`
- **Definition:** Database integration utilities
- **Importance:** Connect to external databases
- **Links to:** `actions/db_client.py`

### `tools.py`
- **Definition:** Integration tool helpers
- **Importance:** Common utilities for integrations
- **Links to:** All integration modules

### `/hris/__init__.py`
- **Definition:** HRIS package initializer
- **Importance:** Exports HRIS modules
- **Links to:** HRIS modules

### `/hris/bamboohr.py`
- **Definition:** BambooHR integration
- **Importance:** Connect to BambooHR system
- **Links to:**
  - `tools/hr/` - HR tools
  - `api_client.py`

---

## Directory: `/agent/llm/`

LLM provider management and routing.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports LLM modules
- **Links to:** All LLM modules

### `config.py`
- **Definition:** LLM configuration
- **Importance:** Provider settings and defaults
- **Links to:** `config/llm_config.yaml`

### `enhanced_router.py`
- **Definition:** Advanced model routing with fallbacks
- **Importance:** Smart model selection based on task
- **Links to:**
  - `llm_router.py`
  - `hybrid_strategy.py`
  - `performance_tracker.py`

### `hybrid_strategy.py`
- **Definition:** Hybrid LLM strategy (local + cloud)
- **Importance:** Balance cost and capability
- **Links to:**
  - `ollama_client.py` - Local LLM
  - `providers.py` - Cloud providers

### `llm_router.py`
- **Definition:** Route requests to appropriate LLM
- **Importance:** Model selection logic
- **Links to:**
  - `providers.py`
  - `config.py`
  - `model_registry.py`

### `ollama_client.py`
- **Definition:** Ollama local LLM client
- **Importance:** Run LLMs locally for privacy/cost
- **Links to:** `hybrid_strategy.py`

### `performance_tracker.py`
- **Definition:** Track LLM performance metrics
- **Importance:** Monitor latency, quality, costs
- **Links to:**
  - `llm_router.py`
  - `analytics.py`

### `providers.py`
- **Definition:** LLM provider implementations
- **Importance:** OpenAI, Anthropic, DeepSeek clients
- **Links to:**
  - `llm.py` - Main interface
  - `api_client.py` - HTTP client

---

## Directory: `/agent/meetings/`

Meeting platform integration and intelligence.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports meeting modules
- **Links to:** All meeting modules

### `base.py`
- **Definition:** Base meeting bot class
- **Importance:** Common meeting bot interface
- **Links to:** All meeting bots

### `cross_meeting_context.py`
- **Definition:** Link context across related meetings
- **Importance:** Maintain continuity between meetings
- **Links to:**
  - `memory/` - Context storage
  - `intelligence/meeting_analyzer.py`

### `factory.py`
- **Definition:** Meeting bot factory
- **Importance:** Create appropriate bot for platform
- **Links to:** All meeting bots

### `google_meet_bot.py`
- **Definition:** Google Meet integration
- **Importance:** Join and interact with Google Meet
- **Links to:**
  - `base.py`
  - `transcription/`
  - `diarization/`

### `live_audio_bot.py`
- **Definition:** Live microphone audio capture
- **Importance:** Record in-person meetings
- **Links to:**
  - `base.py`
  - `transcription/`
  - PyAudio library

### `sdk_integration.py`
- **Definition:** Meeting SDK integration helpers
- **Importance:** Common SDK utilities
- **Links to:** All meeting bots

### `session_manager.py`
- **Definition:** Meeting session management
- **Importance:** Track active meeting sessions
- **Links to:** All meeting bots

### `teams_bot.py`
- **Definition:** Microsoft Teams integration
- **Importance:** Join and interact with Teams
- **Links to:**
  - `base.py`
  - Microsoft Graph API

### `zoom_bot.py`
- **Definition:** Zoom integration
- **Importance:** Join and interact with Zoom
- **Links to:**
  - `base.py`
  - Zoom SDK

### `/diarization/__init__.py`
- **Definition:** Diarization package initializer
- **Links to:** All diarization modules

### `/diarization/base.py`
- **Definition:** Base diarization engine
- **Importance:** Common speaker identification interface
- **Links to:** All diarization engines

### `/diarization/pyannote_engine.py`
- **Definition:** Pyannote speaker diarization
- **Importance:** State-of-the-art speaker identification
- **Links to:**
  - `speaker_manager.py`
  - Pyannote library

### `/diarization/speaker_manager.py`
- **Definition:** Speaker database and matching
- **Importance:** Map voices to known speakers
- **Links to:**
  - `pyannote_engine.py`
  - `memory/` - Speaker storage

### `/intelligence/__init__.py`
- **Definition:** Intelligence package initializer
- **Links to:** All intelligence modules

### `/intelligence/action_executor.py`
- **Definition:** Execute actions from meetings
- **Importance:** Act on meeting decisions in real-time
- **Links to:**
  - `meeting_analyzer.py`
  - `jarvis_agent.py`

### `/intelligence/action_item_reminders.py`
- **Definition:** Action item follow-up reminders
- **Importance:** Ensure action items are completed
- **Links to:**
  - `meeting_analyzer.py`
  - `admin/email_integration.py`

### `/intelligence/meeting_analyzer.py`
- **Definition:** Extract insights from meeting transcripts
- **Importance:** Action items, decisions, questions
- **Links to:**
  - `transcription/` - Transcript source
  - `llm.py` - Analysis

### `/transcription/__init__.py`
- **Definition:** Transcription package initializer
- **Links to:** All transcription modules

### `/transcription/base.py`
- **Definition:** Base transcription engine
- **Importance:** Common transcription interface
- **Links to:** All transcription engines

### `/transcription/deepgram_engine.py`
- **Definition:** Deepgram streaming transcription
- **Importance:** Real-time transcription (<100ms latency)
- **Links to:**
  - Deepgram WebSocket API
  - `manager.py`

### `/transcription/manager.py`
- **Definition:** Transcription manager with failover
- **Importance:** Coordinates transcription engines
- **Links to:** All transcription engines

### `/transcription/whisper_engine.py`
- **Definition:** OpenAI Whisper transcription
- **Importance:** High-accuracy batch transcription
- **Links to:**
  - OpenAI Whisper API
  - `manager.py`

---

## Directory: `/agent/memory/`

Complete memory system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports memory modules
- **Links to:** All memory modules

### `context_retriever.py`
- **Definition:** Retrieve relevant context for queries
- **Importance:** Find relevant memories for any question
- **Links to:**
  - `vector_store.py` - Semantic search
  - `long_term.py` - Memory storage
  - `jarvis_chat.py` - Context injection

### `contextual.py`
- **Definition:** Contextual memory (current task context)
- **Importance:** Maintain context within a task
- **Links to:**
  - `short_term.py`
  - `orchestrator.py`

### `entity.py`
- **Definition:** Entity extraction and memory
- **Importance:** Remember people, places, concepts
- **Links to:**
  - `long_term.py` - Entity storage
  - `llm.py` - Entity extraction

### `long_term.py`
- **Definition:** Persistent long-term memory
- **Importance:** Information that persists across sessions
- **Links to:**
  - `memory_store.py` - Storage
  - `user_profile.py`

### `manager.py`
- **Definition:** Unified memory manager
- **Importance:** Single interface for all memory operations
- **Links to:** All memory modules

### `preference_learner.py`
- **Definition:** Learn user preferences from interactions
- **Importance:** Adapt to user patterns over time
- **Links to:**
  - `user_profile.py`
  - `long_term.py`

### `session_manager.py`
- **Definition:** Per-session memory isolation
- **Importance:** Each chat has separate context
- **Links to:**
  - `short_term.py`
  - `jarvis_chat.py`

### `short_term.py`
- **Definition:** Working memory (current conversation)
- **Importance:** Immediate context for current task
- **Links to:**
  - `session_manager.py`
  - `jarvis_chat.py`

### `storage.py`
- **Definition:** Memory storage backends
- **Importance:** SQLite, in-memory, graph storage
- **Links to:** All memory modules

### `user_profile.py`
- **Definition:** Persistent user profiles
- **Importance:** Remember user across all sessions
- **Links to:**
  - `preference_learner.py`
  - `long_term.py`

### `vector_store.py`
- **Definition:** Vector embedding storage (ChromaDB)
- **Importance:** Semantic similarity search
- **Links to:**
  - `context_retriever.py`
  - `long_term.py`

---

## Directory: `/agent/models/`

Data model definitions.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All model modules

### `agent_config.py`
- **Definition:** Agent configuration model
- **Importance:** Typed agent configuration
- **Links to:** `config/agents.yaml`

### `task_config.py`
- **Definition:** Task configuration model
- **Importance:** Typed task configuration
- **Links to:** `config/tasks.yaml`

---

## Directory: `/agent/monitoring/`

System monitoring and alerting.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All monitoring modules

### `alerts.py`
- **Definition:** Alert management
- **Importance:** Notify on important events
- **Links to:**
  - `metrics.py`
  - Email/Slack integrations

### `logging_config.py`
- **Definition:** Logging configuration
- **Importance:** Structured logging setup
- **Links to:** `core_logging.py`

### `metrics.py`
- **Definition:** Metrics collection
- **Importance:** Track system performance
- **Links to:**
  - `analytics.py`
  - Prometheus/StatsD

---

## Directory: `/agent/optimization/`

Performance optimization utilities.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All optimization modules

### `batch_processor.py`
- **Definition:** Batch processing for efficiency
- **Importance:** Group similar operations
- **Links to:** `llm.py`, `api_client.py`

### `cache.py`
- **Definition:** General-purpose caching
- **Importance:** Reduce redundant operations
- **Links to:** `llm_cache.py`

### `lazy_loader.py`
- **Definition:** Lazy loading utilities
- **Importance:** Defer expensive initialization
- **Links to:** Heavy modules

---

## Directory: `/agent/patterns/`

Execution pattern implementations.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All pattern modules

### `autoselect.py`
- **Definition:** Automatic pattern selection
- **Importance:** Choose best pattern for task
- **Links to:** `selector.py`

### `base.py`
- **Definition:** Base pattern class
- **Importance:** Common pattern interface
- **Links to:** All pattern modules

### `hierarchical.py`
- **Definition:** Hierarchical execution pattern
- **Importance:** Tree-structured task decomposition
- **Links to:** `orchestrator.py`

### `roundrobin.py`
- **Definition:** Round-robin pattern
- **Importance:** Distribute work evenly
- **Links to:** `employee_pool.py`

### `selector.py`
- **Definition:** Pattern selection logic
- **Importance:** Choose appropriate pattern
- **Links to:** `orchestrator.py`

### `sequential.py`
- **Definition:** Sequential execution pattern
- **Importance:** Step-by-step execution
- **Links to:** `orchestrator.py`

---

## Directory: `/agent/performance/`

Performance utilities.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All performance modules

### `cache.py`
- **Definition:** Performance-focused caching
- **Importance:** Speed optimization
- **Links to:** `optimization/cache.py`

### `lazy.py`
- **Definition:** Lazy evaluation
- **Importance:** Defer computation
- **Links to:** `optimization/lazy_loader.py`

### `parallel.py`
- **Definition:** Parallel execution utilities
- **Importance:** Concurrent processing
- **Links to:** `parallel_executor.py`

### `pool.py`
- **Definition:** Worker pool management
- **Importance:** Thread/process pooling
- **Links to:** `execution/employee_pool.py`

### `utils.py`
- **Definition:** Performance utilities
- **Importance:** Common performance helpers
- **Links to:** All performance modules

---

## Directory: `/agent/scheduler/`

Task scheduling.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All scheduler modules

### `cron.py`
- **Definition:** Cron-style scheduling
- **Importance:** Schedule recurring tasks
- **Links to:**
  - `workers/tasks.py`
  - `orchestrator.py`

---

## Directory: `/agent/security/`

Security modules.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All security modules

### `audit_log.py`
- **Definition:** Security audit logging
- **Importance:** Track all security-relevant events
- **Links to:**
  - `audit_log.py` (root)
  - `webapp/auth.py`

### `auth.py`
- **Definition:** Authentication system
- **Importance:** User identity verification
- **Links to:**
  - `webapp/auth.py`
  - `api_keys.py`

### `rate_limit.py`
- **Definition:** Rate limiting
- **Importance:** Prevent abuse
- **Links to:**
  - `webapp/app.py`
  - `actions/rate_limiter.py`

---

## Directory: `/agent/templates/`

Template files.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All template modules

### `email_renderer.py`
- **Definition:** Email template rendering
- **Importance:** Generate formatted emails
- **Links to:**
  - `email/` - Email templates
  - `admin/email_integration.py`

### `/email/welcome_email.html`
- **Definition:** Welcome email template
- **Importance:** New user welcome email
- **Links to:** `email_renderer.py`

---

## Directory: `/agent/temporal/`

Temporal workflow integration.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All temporal modules

### `activities.py`
- **Definition:** Temporal activity definitions
- **Importance:** Individual workflow steps
- **Links to:** `workflows.py`

### `client.py`
- **Definition:** Temporal client wrapper
- **Importance:** Connect to Temporal service
- **Links to:** Temporal server

### `config.py`
- **Definition:** Temporal configuration
- **Importance:** Temporal settings
- **Links to:** `client.py`

### `worker.py`
- **Definition:** Temporal worker
- **Importance:** Execute workflow activities
- **Links to:** `activities.py`

### `workflows.py`
- **Definition:** Temporal workflow definitions
- **Importance:** Durable workflow orchestration
- **Links to:** `activities.py`, `orchestrator.py`

---

## Directory: `/agent/tests/`

Test suite.

### `/e2e/test_smoke_hello_kevin.py`
- **Definition:** Basic smoke test
- **Importance:** Verify basic functionality
- **Links to:** `jarvis_chat.py`

### `/fixtures/mock_tool.py`
- **Definition:** Mock tool for testing
- **Importance:** Test tool system
- **Links to:** `jarvis_tools.py`

### `/integration/` (9 files)
- **Definition:** Integration tests
- **Importance:** Test module interactions
- **Links to:** Multiple modules

### `/unit/` (18 files)
- **Definition:** Unit tests
- **Importance:** Test individual functions
- **Links to:** Individual modules

### `mocks.py`
- **Definition:** Mock objects for testing
- **Importance:** Test isolation
- **Links to:** All test files

---

## Directory: `/agent/tools/`

Tool implementations.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All tool modules

### `base.py`
- **Definition:** Base tool class
- **Importance:** Common tool interface
- **Links to:** All tools

### `plugin_loader.py`
- **Definition:** Dynamic tool loading
- **Importance:** Load tools at runtime
- **Links to:** `tool_registry.py`

### `/actions/` (5 files)
- **Definition:** Business action tools
- **Importance:** Real-world actions (buy domain, deploy, SMS, payment)
- **Links to:** External APIs

### `/builtin/` (2 files)
- **Definition:** Built-in tools
- **Importance:** Core capabilities (format code, run tests)
- **Links to:** `jarvis_tools.py`

### `/documents/` (3 files)
- **Definition:** Document generation tools
- **Importance:** Create documents via tools
- **Links to:** `documents/` generators

### `/hr/` (3 files)
- **Definition:** HR tools
- **Importance:** HR operations
- **Links to:** `integrations/hris/`

---

## Directory: `/agent/validators/`

Input validation.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All validator modules

### `config_validator.py`
- **Definition:** Configuration validation
- **Importance:** Validate YAML configs against schemas
- **Links to:** `config/schemas/`

---

## Directory: `/agent/webapp/`

Web application.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All webapp modules

### `app.py`
- **Definition:** FastAPI application root
- **Importance:** Main web application
- **Links to:** All API modules, templates

### `admin_api.py`
- **Definition:** Administration API
- **Importance:** System administration endpoints
- **Links to:** Admin functions

### `api_keys.py`
- **Definition:** API key management
- **Importance:** API authentication
- **Links to:** `security/auth.py`

### `auth.py`
- **Definition:** Authentication system
- **Importance:** User login/session management
- **Links to:** `security/auth.py`

### `auth_routes.py`
- **Definition:** Authentication routes
- **Importance:** Login/logout endpoints
- **Links to:** `auth.py`

### `chat_api.py`
- **Definition:** Chat REST endpoints
- **Importance:** Chat functionality
- **Links to:** `jarvis_chat.py`

### `code_api.py`
- **Definition:** Code operations API
- **Importance:** Code execution endpoints
- **Links to:** `actions/code_executor.py`

### `finance_api.py`
- **Definition:** Finance API
- **Importance:** Financial operations
- **Links to:** `finance/`

### `/templates/` (12 HTML files)
- **Definition:** HTML templates
- **Importance:** Web UI
- **Links to:** `app.py`

---

## Directory: `/agent/webhooks/`

Webhook handling.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All webhook modules

### `retry.py`
- **Definition:** Webhook retry logic
- **Importance:** Reliable webhook delivery
- **Links to:** External services

### `security.py`
- **Definition:** Webhook security
- **Importance:** Verify webhook signatures
- **Links to:** External services

---

## Directory: `/agent/workers/`

Background workers.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All worker modules

### `celery_app.py`
- **Definition:** Celery application
- **Importance:** Async task queue
- **Links to:** `tasks.py`

### `tasks.py`
- **Definition:** Celery task definitions
- **Importance:** Background jobs
- **Links to:** `jobs.py`, `orchestrator.py`

---

## Directory: `/agent/workflows/`

Business workflow definitions.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All workflow modules

### `base.py`
- **Definition:** Base workflow class
- **Importance:** Common workflow interface
- **Links to:** All workflows

### `coding.py`
- **Definition:** Coding workflow
- **Importance:** Software development workflow
- **Links to:** `orchestrator.py`

### `finance.py`
- **Definition:** Finance workflow
- **Importance:** Financial operations workflow
- **Links to:** `finance/`

### `hr.py`
- **Definition:** HR workflow
- **Importance:** HR operations workflow
- **Links to:** `tools/hr/`

### `legal.py`
- **Definition:** Legal workflow
- **Importance:** Legal operations workflow
- **Links to:** `documents/`

### `ops.py`
- **Definition:** Operations workflow
- **Importance:** General operations workflow
- **Links to:** `admin/`

---

## Directory: `/config/`

Global configuration.

### `llm_config.yaml`
- **Definition:** LLM provider configuration
- **Importance:** Model settings and API configuration
- **Links to:** `agent/llm/config.py`

---

## Directory: `/deployment/`

Deployment configuration.

### `CLOUD_DEPLOYMENT_GUIDE.md`
- **Definition:** Cloud deployment documentation
- **Importance:** Deploy JARVIS to cloud
- **Links to:** Docker, Kubernetes configs

### `docker-compose.yml`
- **Definition:** Docker Compose configuration
- **Importance:** Local multi-container deployment
- **Links to:** Dockerfiles

### `Dockerfile.app`
- **Definition:** Application Dockerfile
- **Importance:** Build web application container
- **Links to:** `agent/webapp/`

### `Dockerfile.worker`
- **Definition:** Worker Dockerfile
- **Importance:** Build background worker container
- **Links to:** `agent/workers/`

### `/kubernetes/jarvis-deployment.yaml`
- **Definition:** Kubernetes deployment
- **Importance:** K8s orchestration config
- **Links to:** Docker images

---

## Directory: `/dev/`

Developer tools.

### `clean_logs.py`
- **Definition:** Clean/archive run logs
- **Importance:** Maintenance script
- **Links to:** `run_logs/`

### `generate_fixture.py`
- **Definition:** Generate test fixtures
- **Importance:** Create test data
- **Links to:** Test files

### `profile_run.py`
- **Definition:** Performance profiling
- **Importance:** Find bottlenecks
- **Links to:** `orchestrator.py`

### `run_autopilot.py`
- **Definition:** Run auto-pilot mode
- **Importance:** Multi-run automation
- **Links to:** `auto_pilot.py`

### `run_once.py`
- **Definition:** Run single orchestration
- **Importance:** Quick single run
- **Links to:** `run_mode.py`

### `view_logs.py`
- **Definition:** View logs in browser
- **Importance:** Log visualization
- **Links to:** `run_logs/`

---

## Directory: `/docs/`

Documentation (40+ files).

Key documents:
- `STAGE7_WEB_UI.md` - Web dashboard guide
- `STAGE8_JOB_MANAGER.md` - Job manager guide
- `STAGE9_PROJECT_EXPLORER.md` - Project explorer guide
- `STAGE10_QA_PIPELINE.md` - QA pipeline guide
- `STAGE11_ANALYTICS_DASHBOARD.md` - Analytics guide
- `STAGE12_SELF_OPTIMIZATION.md` - Self-optimization guide
- `JARVIS_2_0_API_REFERENCE.md` - API documentation
- `JARVIS_2_0_MEMORY_GUIDE.md` - Memory system guide
- `JARVIS_2_0_COUNCIL_GUIDE.md` - Council system guide

---

## Directory: `/tools/`

External tools and extensions.

### `/cli/jarvis_cli.py`
- **Definition:** JARVIS command-line interface
- **Importance:** Terminal-based JARVIS access
- **Links to:** `agent/cli_chat.py`

### `/gmail-addon/`
- **Definition:** Gmail add-on
- **Importance:** JARVIS in Gmail
- **Links to:** Google Apps Script

### `/outlook-addin/`
- **Definition:** Outlook add-in
- **Importance:** JARVIS in Outlook
- **Links to:** Office.js

### `/vscode-extension/`
- **Definition:** VSCode extension
- **Importance:** JARVIS in VSCode
- **Links to:** VSCode API

---

# PART IV: SYSTEM INTERCONNECTIONS

## 4.1 Data Flow Diagram

```
User Request
     │
     ▼
┌─────────────────┐
│  jarvis_chat.py │ ◄── Intent Classification
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────────┐
    ▼         ▼            ▼              ▼
Direct    jarvis_      orchestrator   conversational_
Response  agent.py        .py          agent.py
             │              │              │
             ▼              ▼              ▼
        jarvis_tools   council/      Task Planning
             │         voting
             ▼              │
        actions/*           ▼
             │         employee_pool
             ▼              │
        External       ────┴────
        Systems        task_router
                           │
                           ▼
                      execution/*
```

## 4.2 Memory Flow

```
User Message
     │
     ▼
┌─────────────────┐
│ session_manager │ ◄── Per-chat isolation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  short_term.py  │ ◄── Current conversation
└────────┬────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│   entity.py     │  │ preference_     │
│  (extraction)   │  │ learner.py      │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └──────────┬─────────┘
                    ▼
           ┌─────────────────┐
           │  long_term.py   │ ◄── Persistent
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ vector_store.py │ ◄── Semantic search
           └─────────────────┘
```

---

# PART V: QUICK REFERENCE

## 5.1 Key Entry Points

| Purpose | File |
|---------|------|
| Start Web Server | `start_webapp.py` |
| CLI Chat | `agent/cli_chat.py` |
| Single Run | `dev/run_once.py` |
| Auto-Pilot | `dev/run_autopilot.py` |

## 5.2 Configuration Files

| Config | Location |
|--------|----------|
| Agents | `agent/config/agents.yaml` |
| Tasks | `agent/config/tasks.yaml` |
| LLM | `config/llm_config.yaml` |
| Project | `agent/project_config.json` |

## 5.3 Main APIs

| API | Endpoint |
|-----|----------|
| Chat | `/api/chat/*` |
| Agent | `/api/agent/*` |
| Vision | `/api/vision/*` |
| Admin | `/api/admin/*` |

---

*This document is the complete reference for the JARVIS system. All modules, functions, and interconnections are documented here.*

**Document Version:** 1.0.0
**Total Entries:** 300+ files documented
**Last Updated:** 2025-11-24
