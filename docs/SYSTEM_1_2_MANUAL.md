# System-1.2 — Complete Technical Manual & File Guide

**Version:** System-1.2 (Branch: claude/integrate-knowledge-graph-015uwZS1UYRuWiU9Yt99QqrX)
**Last Updated:** November 2025

---

## Table of Contents

1. [Repository Overview & File Roles](#1-repository-overview--file-roles)
   - [1.1 Top-Level Structure](#11-top-level-structure)
   - [1.2 Core Agent Modules](#12-core-agent-modules)
   - [1.3 Supporting Infrastructure](#13-supporting-infrastructure)
   - [1.4 Web Dashboard & APIs](#14-web-dashboard--apis)
   - [1.5 Testing & Quality](#15-testing--quality)
   - [1.6 Documentation & Developer Tools](#16-documentation--developer-tools)

2. [Complete How-To Manual (End-to-End)](#2-complete-how-to-manual-end-to-end)
   - [2.1 Introduction & High-Level Overview](#21-introduction--high-level-overview)
   - [2.2 Prerequisites & Requirements](#22-prerequisites--requirements)
   - [2.3 Installation & Setup](#23-installation--setup)
   - [2.4 Configuration & Customization](#24-configuration--customization)
   - [2.5 Core Usage Scenarios](#25-core-usage-scenarios)
   - [2.6 Advanced Features & Internals](#26-advanced-features--internals)
   - [2.7 Troubleshooting & FAQ](#27-troubleshooting--faq)

3. [Main Modules & Key Functions](#3-main-modules--key-functions)
   - [3.1 Orchestration & Execution](#31-orchestration--execution)
   - [3.2 LLM & Model Management](#32-llm--model-management)
   - [3.3 Knowledge Graph & Analytics](#33-knowledge-graph--analytics)
   - [3.4 Specialist & Workflow Systems](#34-specialist--workflow-systems)
   - [3.5 Quality Assurance & Safety](#35-quality-assurance--safety)
   - [3.6 Web Interface & Job Management](#36-web-interface--job-management)

4. [Full Dependency & Install Checklist](#4-full-dependency--install-checklist)
   - [4.1 Core Runtimes](#41-core-runtimes)
   - [4.2 Python Libraries](#42-python-libraries)
   - [4.3 External Tools & CLIs](#43-external-tools--clis)
   - [4.4 Environment Variables & Secrets](#44-environment-variables--secrets)
   - [4.5 Optional Dependencies](#45-optional-dependencies)

---

## 1. Repository Overview & File Roles

### 1.1 Top-Level Structure

System-1.2 is a multi-agent AI orchestration platform for autonomous software development and project management. The repository is organized into functional areas:

```
two_agent_web_starter_complete/
├── agent/              # Core orchestration system (50+ modules)
├── sites/              # Generated/managed projects (output directory)
├── tests/              # Top-level test suite
├── docs/               # Documentation files
├── dev/                # Developer utilities
├── missions/           # Mission definition files (JSON/YAML)
├── artifacts/          # Runtime artifacts (logs, snapshots, reports)
├── data/               # Knowledge graph databases and persistent data
├── run_logs/           # Legacy run logging (deprecated path)
├── requirements.txt    # Python dependencies
├── README.md           # Project overview
└── DEVELOPER_GUIDE.md  # Developer documentation
```

**Key Directories:**

- **`agent/`** — The heart of the system. Contains all orchestration logic, LLM interfaces, tool execution, quality assurance, web dashboard, and advanced features like knowledge graphs, workflows, and self-optimization.

- **`sites/`** — Output directory for generated web projects. Each subdirectory represents a managed project with its own history, snapshots, and metadata.

- **`tests/`** — Comprehensive test suite with unit tests, integration tests, and end-to-end tests organized by feature stage.

- **`missions/`** — Mission definition files that specify tasks, configurations, and constraints for the orchestrator to execute.

- **`artifacts/`** — Runtime artifacts including mission logs, overseer suggestions, self-refinement proposals, and QA reports.

- **`data/`** — Persistent data storage for knowledge graphs, analytics, and system learning.

### 1.2 Core Agent Modules

Located in `agent/`, these are the foundational modules:

#### **Orchestration & Execution**

- **`orchestrator.py`** (2,047 lines)
  The 3-loop orchestration engine. Manages Manager ↔ Supervisor ↔ Employee agent interactions. Handles iteration loops, cost tracking, file management, knowledge graph integration, specialist routing, and workflow execution. Entry point for full multi-agent runs.

  *Key Functions:* `run(task, project_path, config)`, `_run_iteration()`, `_build_manager_prompt()`, `_execute_employee_tasks()`

  *Integrates with:* llm.py, cost_tracker.py, model_router.py, knowledge_graph.py, specialists.py, workflows/

- **`orchestrator_2loop.py`** (350 lines)
  Simplified 2-loop orchestrator (Manager ↔ Employee). Faster and cheaper for simpler tasks that don't require task phasing.

  *Key Functions:* `run_2loop(task, project_path, config)`

- **`mission_runner.py`** (570 lines)
  CLI interface for running missions from JSON/YAML files. Loads mission definitions, executes them via orchestrator, logs results to knowledge graph, and generates mission reports.

  *Key Functions:* `load_mission_file()`, `run_mission()`, `list_missions()`, `get_mission_status()`

  *Integrates with:* orchestrator.py, knowledge_graph.py, artifacts.py

- **`runner.py`** (421 lines)
  Programmatic API for web dashboard and external integrations. Provides clean interfaces for running projects without CLI dependencies.

  *Key Functions:* `run_project(config)`, `list_projects()`, `list_run_history()`, `get_run_details(run_id)`

- **`auto_pilot.py`** (287 lines)
  Autonomous multi-run mode with self-evaluation. Executes multiple sub-runs, analyzes outcomes, and refines approach iteratively.

  *Key Functions:* `run_autopilot(config, max_sub_runs=3)`

#### **LLM & Intelligence**

- **`llm.py`** (326 lines)
  LLM abstraction layer. Handles OpenAI API calls, token counting, cost tracking, retries, and simulation mode. All LLM interactions flow through this module.

  *Key Functions:* `chat_json(messages, model, temperature, max_tokens)`, `count_tokens(text, model)`, `_post(payload)`

  *Features:* Automatic retries, timeout handling, cost tracking integration, simulation mode support

- **`model_router.py`** (271 lines)
  Intelligent model selection based on task type, complexity, role, and iteration count. Enforces cost controls (GPT-5 only on iterations 2-3 when complexity is high). Supports multi-provider configuration (OpenAI, Anthropic, local models).

  *Key Functions:* `choose_model(task_type, complexity, role, interaction_index)`, `estimate_complexity(stage, previous_failures, files_count)`, `ModelConfig` dataclass

  *Key Constraint:* GPT-5 restricted to specific iterations and high-complexity tasks to control costs

- **`domain_router.py`** (445 lines)
  Classifies tasks into domains (CODING, FINANCE, LEGAL, OPS, MARKETING, RESEARCH) and provides domain-specific prompts, tools, and workflows.

  *Key Functions:* `classify_task(task)`, `get_domain_prompts(domain)`, `get_domain_tools(domain)`, `get_workflow_for_domain(domain)`

  *Domains:* 7 predefined domains with keyword matching and tool restrictions

#### **Knowledge & Learning**

- **`knowledge_graph.py`** (903 lines)
  SQLite-backed knowledge graph for tracking missions, files, bugs, fixes, and relationships. Enables historical learning and risk analysis.

  *Key Functions:*
  - `add_entity(type, name, metadata)`
  - `add_relationship(from_id, to_id, relationship_type, metadata)`
  - `log_mission(mission_id, status, domain, cost, iterations, files_modified)`
  - `get_files_for_mission(mission_id)` — Get all files worked on by a mission
  - `get_missions_for_file(file_path)` — Get all missions that touched a file
  - `get_risky_files(limit=10)` — Risk analysis based on bug counts and failure rates
  - `get_bug_relationships(mission_id)` — Query CAUSED_BUG/FIXED_BUG edges

  *Database Schema:* 4 tables (entities, relationships, mission_history, file_snapshots)

- **`project_stats.py`** (604 lines)
  Analytics and statistical analysis of missions. Computes trends, success rates, cost patterns, and risk insights from knowledge graph data.

  *Key Functions:* `get_risky_files(project_path, limit=5)`, `format_risk_summary(risky_files)`, `compute_growth_rate()`, `get_project_metrics()`

- **`analytics.py`** (641 lines)
  Comprehensive analytics engine. Aggregates metrics across runs, tracks costs, identifies trends, and exports data for dashboards.

  *Key Functions:* `get_analytics_summary(project, timeframe)`, `get_cost_breakdown()`, `get_performance_trends()`, `export_analytics(format='json')`

- **`brain.py`** (851 lines)
  Self-optimization engine. Profiles project behavior, generates recommendations, and auto-tunes parameters based on historical performance.

  *Key Functions:* `generate_recommendations(project)`, `apply_recommendation(rec_id)`, `profile_project(project_path)`, `auto_tune(confidence_threshold='medium')`

#### **Memory & Communication**

- **`memory_store.py`** (675 lines)
  Persistent agent memory system. Stores decisions, findings, and context across iterations and runs.

  *Key Functions:* `store_memory(stage, key, value)`, `retrieve_memory(stage, key)`, `clear_stage_memory(stage_id)`

- **`inter_agent_bus.py`** (531 lines)
  Message bus for agent-to-agent communication. Enables horizontal information sharing between Manager, Supervisor, and Employee.

  *Key Functions:* `publish(topic, message, sender)`, `subscribe(topic, callback)`, `get_messages(topic, since_timestamp)`

- **`workflow_manager.py`** (703 lines)
  Dynamic workflow orchestration. Manages stage progression, mutations, and conditional branching in complex multi-stage workflows.

  *Key Functions:* `create_workflow(roadmap)`, `execute_stage(stage_id)`, `mutate_stage(stage_id, new_definition)`

### 1.3 Supporting Infrastructure

#### **Execution & Tools**

- **`exec_tools.py`** (850 lines)
  Tool registry and execution framework. Provides code formatting, linting, testing, git operations, and sandbox execution to agents.

  *Key Tools:* `format_code`, `run_unit_tests`, `run_integration_tests`, `git_diff`, `git_status`, `sandbox_run_python`, `sandbox_run_node`, `sandbox_run_script`

  *Key Functions:* `call_tool(tool_name, **kwargs)`, `get_tool_metadata()`

  *Security:* Domain-based tool restrictions, no shell execution in tool registry

- **`sandbox.py`** (583 lines)
  Safe code execution environment. Runs Python, Node.js, and shell scripts in resource-limited subprocesses with timeouts and memory constraints.

  *Key Functions:* `run_python_snippet(code, timeout=30)`, `run_node_snippet(code, timeout=30)`, `run_script(script_path, args, interpreter)`

  *Safety Features:* CPU time limits (5 min), memory limits (512MB for tests), no network access option, automatic cleanup

- **`exec_safety.py`** (296 lines)
  Safety analysis system. Performs static analysis, dependency scanning, and code quality checks before execution.

  *Key Functions:* `run_safety_checks(project_path)`, `analyze_static_issues()`, `scan_dependencies()`

- **`exec_analysis.py`** (219 lines)
  Code analysis utilities. Extracts statistics, detects patterns, and generates insights from codebases.

  *Key Functions:* `analyze_codebase(project_path)`, `count_lines_by_type()`, `detect_code_smells()`

- **`exec_deps.py`** (248 lines)
  Dependency management and scanning. Identifies package requirements, checks for vulnerabilities, and validates dependency trees.

  *Key Functions:* `scan_dependencies(project_path)`, `check_security_vulnerabilities()`, `resolve_dependency_conflicts()`

#### **Cost & Tracking**

- **`cost_tracker.py`** (257 lines)
  Global token and cost tracking. Monitors LLM usage, enforces cost caps, and provides warnings.

  *Key Functions:* `track(model, prompt_tokens, completion_tokens)`, `get_cost_summary()`, `check_limit(max_cost)`, `reset()`

  *State:* Singleton pattern, thread-safe, persistent across function calls

- **`cost_estimator.py`** (141 lines)
  Pre-flight cost estimation. Predicts costs based on task complexity and historical data.

  *Key Functions:* `estimate_run_cost(task, mode, max_rounds)`, `estimate_tokens(text_length)`

#### **Configuration & Paths**

- **`config.py`** (476 lines)
  Centralized configuration system. Manages defaults, environment variables, and runtime settings.

  *Key Classes:* `ModelDefaults`, `CostLimits`, `SafetyConfig`, `GitConfig`, `QAConfig`, `RuntimeConfig`

  *Key Functions:* `get_config()`, `load_project_config(project_path)`, `merge_configs(default, project, env)`

- **`paths.py`** (342 lines)
  Path resolution and management. Provides safe, consistent file system access across the system.

  *Key Functions:* `get_root()`, `get_sites_dir()`, `get_run_logs_dir()`, `get_missions_dir()`, `is_safe_path(path)`, `resolve_project_path(project_subdir)`

#### **Logging & Artifacts**

- **`run_logger.py`** (436 lines)
  Structured run logging. Records sessions, iterations, and summaries in JSON format.

  *Key Classes:* `RunSummary`, `SessionSummary`, `IterationLog`

  *Key Functions:* `start_run(config)`, `log_iteration(iteration_data)`, `finish_run(status, cost_summary)`

  *Note:* Legacy system, being phased out in favor of core_logging

- **`core_logging.py`** (748 lines)
  Modern event-driven logging system. Granular tracking of LLM calls, tool executions, file writes, and errors.

  *Key Functions:* `log_event(event_type, data)`, `start_session()`, `end_session()`, `query_events(filters)`

- **`artifacts.py`** (722 lines)
  Artifact management system. Organizes and stores mission outputs, reports, snapshots, and metadata.

  *Key Functions:* `save_artifact(mission_id, artifact_type, content)`, `load_artifact(mission_id, artifact_type)`, `list_artifacts(mission_id)`

### 1.4 Web Dashboard & APIs

#### **Web Application**

- **`webapp/app.py`** (973 lines)
  FastAPI web application. Provides REST API and web UI for managing projects, jobs, analytics, and system tuning.

  *Key Routes:*
  - `GET /` — Dashboard home
  - `POST /api/run` — Start new run
  - `GET /api/projects` — List projects
  - `GET /api/runs` — Run history
  - `GET /api/runs/{run_id}` — Run details
  - `POST /api/jobs` — Create background job
  - `GET /api/jobs/{job_id}` — Job status
  - `GET /api/analytics` — Analytics data
  - `GET /api/tuning/recommendations` — Get optimization recommendations
  - `POST /api/tuning/apply` — Apply tuning recommendation

  *Features:* CORS support, static file serving, Jinja2 templates, background job management

- **`jobs.py`** (354 lines)
  Background job manager. Executes long-running tasks asynchronously with state persistence and progress tracking.

  *Key Classes:* `Job`, `JobManager`

  *Key Functions:* `create_job(config)`, `get_job(job_id)`, `cancel_job(job_id)`, `list_jobs(filters)`, `stream_logs(job_id)`

  *Features:* Thread-safe, state persistence to disk, automatic cleanup, live log streaming

- **`file_explorer.py`** (363 lines)
  Project file browser and snapshot viewer. Enables navigation of project files, iteration history, and diff comparison.

  *Key Functions:* `get_file_tree(project_path)`, `read_file(project_path, file_path)`, `list_snapshots(project_path)`, `get_snapshot_diff(project_path, iteration1, iteration2)`

  *Security:* Path traversal prevention, safe file access

### 1.5 Testing & Quality

#### **Quality Assurance**

- **`qa.py`** (795 lines)
  Automated quality assurance system. Validates HTML/CSS/JS projects against configurable rules and best practices.

  *Key Functions:* `run_qa_checks(project_path, config)`, `validate_html_quality()`, `check_accessibility()`, `run_smoke_tests()`, `generate_qa_report()`

  *Checks:* Title/meta tags, H1 presence, image alt text, duplicate IDs, console.logs, large files, link validity

#### **Specialists & Workflows**

- **`specialists.py`** (716 lines)
  Specialist agent definitions. Defines 10 specialist types with expertise, tools, keywords, and domain mappings.

  *Specialist Types:* FRONTEND, BACKEND, DATA, SECURITY, DEVOPS, QA, FULLSTACK, GENERIC, CONTENT_WRITER, RESEARCHER

  *Key Functions:* `get_specialist(specialist_type)`, `select_specialist_for_task(task)`, `get_specialists_for_domain(domain)`

  *Features:* Task matching scoring, cost multipliers, complexity thresholds

- **`specialist_market.py`** (735 lines)
  Marketplace for specialist discovery and performance tracking. Rates specialists based on mission outcomes.

  *Key Functions:* `recommend_specialist(task, budget)`, `track_specialist_performance(specialist, mission_outcome)`, `get_specialist_leaderboard()`

- **`workflows/`** (7 modules)
  Domain-specific QA pipelines and workflow definitions.

  *Modules:*
  - `base.py` — Abstract Workflow class with step execution framework
  - `coding.py` — Software development workflow (Syntax → Lint → Test → Security → QA)
  - `finance.py` — Financial analysis workflow (Data validation → Calculations → Compliance)
  - `legal.py` — Legal document workflow (Structure → Citations → Compliance)
  - `hr.py` — HR workflow (Policy → Privacy → Sensitivity)
  - `ops.py` — Operations workflow (Config → Infrastructure → Security)

  *Key Classes:* `Workflow`, `WorkflowStep`, domain-specific workflow classes

  *Key Functions:* `run(mission_context)`, `_execute_step(step, context)`, `get_workflow_for_domain(domain)`

#### **Oversight & Refinement**

- **`overseer.py`** (930 lines)
  Meta-orchestration system. Monitors mission progress, provides strategic interventions, and generates optimization suggestions.

  *Key Functions:*
  - `analyze_mission_progress(mission_data)` — Real-time mission health analysis
  - `recommend_mission_strategy(task, budget, max_iterations)` — Strategic planning
  - `generate_suggested_missions()` — Auto-generate missions from patterns
  - `persist_suggestions(suggestions, mission_id)` — Save recommendations to artifacts
  - `write_suggested_missions_to_disk()` — Create mission JSON files

  *CLI Commands:* `python -m agent.overseer review --write-missions`

- **`self_refinement.py`** (733 lines)
  Autonomous improvement system. Analyzes historical performance and proposes system optimizations.

  *Key Functions:*
  - `suggest_improvements()` — Generate improvement proposals
  - `generate_refinement_report()` — Comprehensive analysis report
  - `persist_proposals(improvements)` — Write to proposals/YYYY-MM-DD_self_refine.md
  - `apply_approved_proposals(proposal_file)` — Apply approved changes

  *Improvement Areas:* Prompts, parameters, specialists, cost optimization, iteration efficiency, domain routing, tool usage

- **`feedback_analyzer.py`** (663 lines)
  Feedback analysis engine. Processes user feedback, supervisor notes, and QA findings to identify improvement opportunities.

  *Key Functions:* `analyze_feedback(feedback_data)`, `extract_insights()`, `generate_actionable_recommendations()`

#### **Company Operations**

- **`company_ops.py`** (700 lines)
  Enterprise workflow management for non-coding domains (finance, legal, HR, ops).

  *Key Functions:* `execute_finance_workflow(task)`, `execute_legal_workflow(task)`, `execute_hr_workflow(task)`, `execute_ops_workflow(task)`

  *Features:* Domain-specific QA gates, specialist routing, compliance checking

### 1.6 Documentation & Developer Tools

#### **Documentation**

- **`README.md`** — Project overview, quick start, features, architecture
- **`DEVELOPER_GUIDE.md`** — Comprehensive developer documentation
- **`docs/STAGE7_WEB_UI.md`** — Web dashboard guide
- **`docs/STAGE8_JOB_MANAGER.md`** — Job management guide
- **`docs/STAGE9_PROJECT_EXPLORER.md`** — File explorer guide
- **`docs/STAGE10_QA_PIPELINE.md`** — Quality assurance guide
- **`docs/STAGE11_ANALYTICS_DASHBOARD.md`** — Analytics guide
- **`docs/STAGE12_SELF_OPTIMIZATION.md`** — Brain/tuning guide
- **`docs/MODEL_ROUTING.md`** — Model selection strategies
- **`docs/REFERENCE.md`** — Auto-generated API reference

#### **Developer Utilities**

- **`dev/run_once.py`** — Execute single orchestrator run with logging
- **`dev/run_autopilot.py`** — Launch auto-pilot mode
- **`dev/view_logs.py`** — Open logs in browser with interactive viewer
- **`dev/clean_logs.py`** — Archive/delete old run logs
- **`dev/profile_run.py`** — Performance profiling with cProfile
- **`dev/generate_fixture.py`** — Create test fixtures from real runs

- **`make.py`** — Command dispatcher for common development tasks
  - `python make.py run` — Run orchestrator
  - `python make.py test` — Run tests
  - `python make.py docs` — Generate documentation
  - `python make.py clean` — Clean artifacts
  - `python make.py profile` — Profile execution

#### **Testing Infrastructure**

- **`tests/test_specialists.py`** — Specialist system tests (4 test cases, all passing)
- **`tests/test_memory_store.py`** — Memory persistence tests
- **`tests/test_inter_agent_bus.py`** — Message bus tests
- **`tests/test_workflow_manager.py`** — Workflow execution tests

- **`agent/tests/`** — Unit tests for core modules
  - `unit/test_cost_tracker.py`
  - `unit/test_exec_tools.py`
  - `unit/test_merge_manager.py`
  - `unit/test_model_router.py`

- **`agent/tests_stage7/`** — Web dashboard tests
- **`agent/tests_stage8/`** — Job manager tests
- **`agent/tests_stage9/`** — Project explorer tests
- **`agent/tests_stage10/`** — QA pipeline tests (30+ test cases)
- **`agent/tests_stage11/`** — Analytics tests
- **`agent/tests_stage12/`** — Brain/tuning tests
- **`agent/tests_e2e/`** — End-to-end integration tests

---

## 2. Complete How-To Manual (End-to-End)

### 2.1 Introduction & High-Level Overview

**What is System-1.2?**

System-1.2 is an advanced multi-agent AI orchestration platform designed for autonomous software development, project management, and knowledge work. It uses multiple specialized AI agents (Manager, Supervisor, Employee, and domain-specific Specialists) working collaboratively to plan, build, iterate on, and optimize complex projects.

**Core Capabilities:**

- **Autonomous Development**: Generate complete web applications, landing pages, tools, and documentation from natural language task descriptions
- **Multi-Agent Orchestration**: Manager plans, Supervisor phases work, Employee implements, Specialists provide domain expertise
- **Knowledge Graph Learning**: Tracks mission history, file relationships, bugs/fixes, and learns from past executions to improve risk assessment
- **Intelligent Model Routing**: Automatically selects optimal LLM models based on task complexity, iteration count, and budget constraints
- **Domain-Aware Processing**: Classifies tasks into domains (coding, finance, legal, ops, etc.) and applies domain-specific workflows and tools
- **Sandbox Execution**: Safely runs Python, Node.js, and scripts in resource-limited environments
- **Quality Assurance**: Automated HTML/CSS/JS validation, accessibility checks, and smoke testing
- **Cost Control**: Token tracking, warnings, hard caps, and cost estimation before execution
- **Web Dashboard**: Visual interface for project management, job execution, analytics, and system tuning
- **Self-Optimization**: Analyzes historical performance and auto-tunes system parameters for better outcomes

**Typical Usage Scenarios:**

1. **Web Development**: "Build a modern landing page with hero section, features, pricing, and testimonials"
2. **Code Refactoring**: "Refactor the authentication module to use JWT tokens instead of sessions"
3. **Documentation**: "Generate comprehensive API documentation for all endpoints"
4. **Data Analysis**: "Create a dashboard to visualize sales trends by region"
5. **Process Automation**: "Build a workflow to automatically process incoming customer support tickets"

**Architecture:**

System-1.2 uses a hierarchical multi-agent architecture:

```
┌──────────────────────────────────────────────────┐
│                    MANAGER                       │
│  (Strategic planning, task decomposition)        │
└─────────────────┬────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────┐
│                  SUPERVISOR                      │
│  (Task phasing, quality gates)                   │
└─────────────────┬────────────────────────────────┘
                  │
                  ▼
┌──────────────────────────────────────────────────┐
│                  EMPLOYEE                        │
│  (Code generation, implementation)               │
└─────────────────┬────────────────────────────────┘
                  │
                  ├─> Specialists (Frontend, Backend, Security, etc.)
                  ├─> Tools (Linting, Testing, Git, Sandbox)
                  ├─> Workflows (Domain-specific QA pipelines)
                  └─> Knowledge Graph (Historical learning)
```

The system also includes meta-orchestration layers (Overseer, Self-Refinement) that monitor and optimize the core orchestration process.

### 2.2 Prerequisites & Requirements

#### **Operating Systems**

- **Linux** (Ubuntu 20.04+, Debian 11+, or equivalent) — Primary development platform
- **macOS** (11.0+) — Fully supported
- **Windows 10/11** — Supported via WSL2 or native Python

#### **Core Runtimes**

**Python 3.9 or higher** (Required)

*Why needed:* System-1.2 is written entirely in Python. Type hints and modern syntax require 3.9+.

*Check if installed:*
```bash
python --version
# or
python3 --version
```

*Install:*
- **Ubuntu/Debian:** `sudo apt update && sudo apt install python3 python3-pip python3-venv`
- **macOS:** `brew install python@3.11` (Homebrew recommended)
- **Windows:** Download from [python.org](https://www.python.org/downloads/) or use Microsoft Store

**Git** (Required)

*Why needed:* Auto-commit features, repository management, version control integration

*Check if installed:*
```bash
git --version
```

*Install:*
- **Ubuntu/Debian:** `sudo apt install git`
- **macOS:** `brew install git` (or use Xcode Command Line Tools)
- **Windows:** Download from [git-scm.com](https://git-scm.com/) or use GitHub Desktop

**Node.js and npm** (Optional, for sandbox execution and project testing)

*Why needed:* Sandbox execution of JavaScript code, running Node.js projects, npm package management

*Check if installed:*
```bash
node --version
npm --version
```

*Install:*
- **Ubuntu/Debian:** `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs`
- **macOS:** `brew install node`
- **Windows:** Download from [nodejs.org](https://nodejs.org/)

#### **Web Browser**

**Modern Web Browser** (Required for web dashboard)

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

*Why needed:* Access web dashboard, view analytics, interact with project explorer

### 2.3 Installation & Setup

Follow these steps to set up System-1.2 from scratch:

#### **Step 1: Clone the Repository**

```bash
# Clone from GitHub (replace with actual URL)
git clone https://github.com/your-org/two_agent_web_starter_complete.git
cd two_agent_web_starter_complete

# Checkout the System-1.2 branch
git checkout claude/integrate-knowledge-graph-015uwZS1UYRuWiU9Yt99QqrX
```

#### **Step 2: Create Virtual Environment** (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Linux/macOS:
source venv/bin/activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On Windows (CMD):
.\venv\Scripts\activate.bat
```

#### **Step 3: Install Python Dependencies**

```bash
# Install required packages
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- fastapi (≥0.104.0) — Web framework
- jinja2 (≥3.1.0) — Template engine
- uvicorn (≥0.24.0) — ASGI server
- python-multipart (≥0.0.6) — Form handling
- pytest (≥7.4.0) — Testing framework
- pytest-cov (≥4.1.0) — Coverage reporting

#### **Step 4: Configure Environment Variables**

Create a `.env` file in the project root:

```bash
# Copy example (if exists) or create new
touch .env
```

Edit `.env` with required API keys and settings:

```bash
# REQUIRED: OpenAI API key for LLM access
OPENAI_API_KEY=sk-your-openai-api-key-here

# OPTIONAL: Alternative/additional providers
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# OPTIONAL: Model overrides (defaults to config.py settings)
# DEFAULT_MANAGER_MODEL=gpt-4o-mini
# DEFAULT_SUPERVISOR_MODEL=gpt-4o-mini
# DEFAULT_EMPLOYEE_MODEL=gpt-4o

# OPTIONAL: Cost controls
# MAX_COST_USD=10.0
# COST_WARNING_USD=5.0
```

**Critical Environment Variables:**

1. **`OPENAI_API_KEY`** (REQUIRED)
   Your OpenAI API key. Get one from [platform.openai.com](https://platform.openai.com/api-keys)

   Without this, the system cannot make LLM calls and will fail immediately.

2. **`ANTHROPIC_API_KEY`** (Optional)
   If using Claude models (future feature), provide Anthropic API key.

3. **Model Override Variables** (Optional)
   Override default model selection per role:
   - `DEFAULT_MANAGER_MODEL`
   - `DEFAULT_SUPERVISOR_MODEL`
   - `DEFAULT_EMPLOYEE_MODEL`

#### **Step 5: Verify Installation**

```bash
# Run sanity tests
python make.py test

# Or directly with pytest
pytest agent/tests_sanity/ -v

# Expected output: All tests pass
```

#### **Step 6: Initialize Data Directories**

System-1.2 creates these automatically on first run, but you can pre-create them:

```bash
mkdir -p sites artifacts run_logs data missions
```

- **`sites/`** — Generated projects will be stored here
- **`artifacts/`** — Mission logs, snapshots, reports
- **`run_logs/`** — Execution logs and summaries
- **`data/`** — Knowledge graph database (`knowledge_graph.db`)
- **`missions/`** — Mission definition files

### 2.4 Configuration & Customization

System-1.2 uses a multi-layer configuration system:

1. **Built-in defaults** (in `agent/config.py`)
2. **Project config** (`agent/project_config.json`)
3. **Environment variables** (`.env` file)
4. **Runtime parameters** (command-line flags or API calls)

Higher layers override lower layers.

#### **Project Configuration File**

Edit `agent/project_config.json` to customize defaults:

```json
{
  "project_name": "My Project",
  "project_subdir": "my_project",
  "task": "Build a modern landing page with hero section...",
  "max_rounds": 3,
  "mode": "3loop",
  "use_visual_review": true,
  "use_snapshots": true,
  "use_git": true,
  "prompts_file": "prompts_default.json",
  "cost_warning_usd": 0.8,
  "max_cost_usd": 1.5,
  "interactive_cost_mode": "once",
  "qa": {
    "enabled": true,
    "require_title": true,
    "require_meta_description": true,
    "require_h1": true,
    "max_images_missing_alt": 0
  },
  "analytics": {
    "enabled": true,
    "monthly_budget": 50.0
  },
  "auto_tune": {
    "enabled": false,
    "apply_safely": true
  }
}
```

**Key Configuration Fields:**

- **`project_subdir`**: Directory name under `sites/` where project files are stored
- **`mode`**: Orchestration mode (`"2loop"` or `"3loop"`)
  - `2loop`: Manager ↔ Employee (faster, cheaper)
  - `3loop`: Manager ↔ Supervisor ↔ Employee (more thorough, task phasing)
- **`max_rounds`**: Maximum iteration count (typically 1-5)
- **`use_git`**: Enable automatic Git commits after each iteration
- **`use_snapshots`**: Save iteration snapshots for diff comparison
- **`max_cost_usd`**: Hard cost cap (run aborts if exceeded)
- **`cost_warning_usd`**: Warning threshold (prompt before continuing)
- **`interactive_cost_mode`**: `"off"`, `"once"`, or `"always"`

#### **Customizing Model Selection**

Edit model routing in `agent/config.py` or override via environment variables:

```python
# config.py
class ModelDefaults:
    manager: str = "gpt-4o-mini"                # Planning and review
    supervisor: str = "gpt-4o-mini"             # Task phasing
    employee: str = "gpt-4o"                    # Code generation
    merge_manager: str = "gpt-4o-mini"          # Conflict resolution
    qa_reviewer: str = "gpt-4o-mini"            # Quality checks
```

Or via `.env`:

```bash
DEFAULT_MANAGER_MODEL=gpt-4o-mini
DEFAULT_EMPLOYEE_MODEL=gpt-4o
```

**Model Routing Constraints:**

The system enforces intelligent model routing to control costs:

- **GPT-4o** is ONLY used on iterations 2-3 when complexity is "high" or task is flagged as important
- First iteration ALWAYS uses cheaper models (gpt-4o-mini)
- Simple tasks use nano/mini models throughout

#### **Customizing QA Rules**

Edit the `qa` section in `project_config.json`:

```json
{
  "qa": {
    "enabled": true,
    "require_title": true,              // <title> must exist
    "require_meta_description": true,   // <meta name="description"> required
    "require_lang_attribute": true,     // <html lang="..."> required
    "require_h1": true,                 // At least one <h1> required
    "max_empty_links": 10,              // Max <a href="#"> allowed
    "max_images_missing_alt": 0,        // All images must have alt text
    "max_duplicate_ids": 0,             // No duplicate id attributes
    "max_console_logs": 5,              // Max console.log() statements
    "allow_large_files": true,
    "max_large_files": 5,
    "large_file_threshold": 5000        // Lines
  }
}
```

#### **Domain-Specific Tool Access**

Sandbox tools are restricted by domain for security. To modify permissions, edit `agent/domain_router.py`:

```python
def get_domain_tools(domain: Domain) -> List[str]:
    if domain == Domain.CODING:
        return core_tools + [
            "sandbox_run_python",
            "sandbox_run_node",
            "sandbox_run_script",  # All sandbox tools allowed
        ]
    elif domain == Domain.FINANCE:
        return core_tools + [
            "sandbox_run_python",  # Only Python for data analysis
        ]
    # ... other domains
```

### 2.5 Core Usage Scenarios

#### **Scenario 1: Run the Orchestrator (Web Dashboard)**

**What it does:** Provides a visual interface for managing projects and runs.

**When to use:** Recommended for most users. Easiest way to start runs, monitor progress, and view results.

**How to use:**

```bash
# 1. Start the web server
python -m agent.webapp.app

# 2. Open browser to http://127.0.0.1:8000

# 3. In the web UI:
#    - Select a project from dropdown (or create new)
#    - Choose mode (2loop or 3loop)
#    - Set max rounds and cost limits
#    - Enter task description
#    - Click "Start Run"

# 4. Monitor progress:
#    - View live job status
#    - Stream logs in real-time
#    - Check cost accumulation

# 5. View results:
#    - Browse generated files
#    - Compare iteration snapshots
#    - Review QA reports
#    - Check analytics
```

**Expected output:**
- Web server starts on port 8000
- Dashboard shows project list, run history, and forms
- Background jobs execute asynchronously
- Results saved to `sites/<project_subdir>/`

**Key endpoints:**
- `/` — Dashboard home
- `/projects` — Project explorer
- `/jobs/<job_id>` — Job details
- `/analytics` — Analytics dashboard
- `/tuning` — Self-optimization controls

#### **Scenario 2: Run the Orchestrator (Command Line)**

**What it does:** Executes a run directly from the terminal using config file.

**When to use:** For scripting, CI/CD integration, or when you prefer CLI over web UI.

**How to use:**

```bash
# 1. Navigate to agent directory
cd agent

# 2. Edit project_config.json with your task and settings

# 3. Run the orchestrator
python run_mode.py

# Or using the make.py dispatcher
cd ..
python make.py run
```

**Expected output:**
```
🚀 Starting orchestration run...
📋 Project: My Project
🎯 Task: Build a modern landing page...
⚙️  Mode: 3loop, Max Rounds: 3
💰 Cost Cap: $1.50, Warning: $0.80

[Domain] Task classified as: coding
[Risk] Identified 2 high-risk files for manager awareness
[Specialist] Recommended: Frontend Specialist (match: 0.85)

=== Iteration 1 ===
[Manager] Planning...
[Supervisor] Creating phases...
[Employee] Implementing...
[Files] Written: index.html, styles.css, script.js
[Cost] $0.23 (15% of cap)

=== Iteration 2 ===
...

✅ Run completed successfully!
📁 Output: sites/my_project/
💰 Total cost: $0.67
📊 Files modified: 5
```

Results saved to:
- `sites/<project_subdir>/` — Generated files
- `run_logs/<run_id>/` — Execution logs and summary

#### **Scenario 3: Run a Mission**

**What it does:** Executes predefined missions from JSON/YAML files.

**When to use:** For reproducible workflows, batch processing, or scheduled tasks.

**How to use:**

```bash
# 1. Create a mission file
cat > missions/my_mission.json << 'EOF'
{
  "mission_id": "landing_page_v1",
  "task": "Build a landing page with hero, features, pricing",
  "project_path": "sites/landing_page",
  "mode": "3loop",
  "max_rounds": 3,
  "cost_cap_usd": 2.0,
  "tags": ["web", "marketing"],
  "domain": "coding"
}
EOF

# 2. Run the mission
python -m agent.mission_runner run missions/my_mission.json

# 3. Check mission status
python -m agent.mission_runner status landing_page_v1

# 4. List all missions
python -m agent.mission_runner list
```

**Expected output:**
```
🎯 Running mission: landing_page_v1
📄 Task: Build a landing page with hero, features, pricing
🏷️  Tags: web, marketing
🌐 Domain: coding

[Mission] Starting orchestration...
[Mission] Iteration 1/3 completed
[Mission] Iteration 2/3 completed
[Mission] Iteration 3/3 completed

✅ Mission completed successfully!
📊 Mission logged to knowledge graph
📄 Tracked 7 modified files
💾 Results: sites/landing_page/
📝 Mission log: artifacts/landing_page_v1/mission_log.json
```

**Mission results:**
- Knowledge graph updated with mission → file relationships
- Artifacts saved to `artifacts/<mission_id>/`
- Mission summary in `artifacts/<mission_id>/mission_log.json`

#### **Scenario 4: Use Sandbox Execution**

**What it does:** Safely executes Python, Node.js, or shell scripts in isolated environments.

**When to use:** Testing code snippets, running untrusted code, data analysis scripts.

**How to use:**

```python
# From Python code
from agent import sandbox

# Run Python snippet
result = sandbox.run_python_snippet("""
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
print(df.describe())
""")

print(result['stdout'])  # Output from script
print(result['success'])  # True/False
print(result['exit_code'])  # 0 if successful

# Run Node.js snippet
result = sandbox.run_node_snippet("""
const data = [1, 2, 3, 4, 5];
console.log('Average:', data.reduce((a,b) => a+b) / data.length);
""")

# Run a script file
result = sandbox.run_script(
    script_path=Path('scripts/analyze.py'),
    interpreter='python3',
    timeout_seconds=60
)
```

**Available through agent tools:**
- `sandbox_run_python` — Python code execution
- `sandbox_run_node` — Node.js code execution
- `sandbox_run_script` — Generic script execution

**Security features:**
- CPU time limit: 5 minutes
- Memory limit: 512 MB (tests), 256 MB (snippets)
- Network isolation (optional)
- Automatic cleanup of temporary files
- Timeout enforcement

**Domain restrictions:**
- CODING: All sandbox tools available
- FINANCE/RESEARCH: Python only
- Other domains: No sandbox access (security)

#### **Scenario 5: Query the Knowledge Graph**

**What it does:** Retrieves historical mission data, file relationships, and risk insights.

**When to use:** Understanding project history, identifying risky files, analyzing patterns.

**How to use:**

```python
from agent import knowledge_graph, project_stats

# Initialize knowledge graph
kg = knowledge_graph.KnowledgeGraph()

# Get all files touched by a mission
files = kg.get_files_for_mission("landing_page_v1")
for file_info in files:
    print(f"File: {file_info['file']['name']}")
    print(f"Status: {file_info['relationship']['metadata'].get('status')}")

# Get all missions that modified a file
missions = kg.get_missions_for_file("sites/my_project/index.html")
for mission_info in missions:
    print(f"Mission: {mission_info['mission']['name']}")

# Get bug relationships for a mission
bugs = kg.get_bug_relationships("landing_page_v1")
print(f"Caused bugs: {len(bugs['caused_bugs'])}")
print(f"Fixed bugs: {len(bugs['fixed_bugs'])}")

# Get high-risk files
risky_files = project_stats.get_risky_files(limit=5)
for file_path, risk_score in risky_files:
    print(f"⚠️  {file_path}: risk score {risk_score}")

# Format risk summary for prompts
summary = project_stats.format_risk_summary(risky_files)
print(summary)
```

**Expected output:**
```
⚠️ High-Risk Files (based on historical bugs and failures):
  • sites/auth/login.py (risk score: 45)
  • sites/api/routes.py (risk score: 30)
  • sites/utils/validation.js (risk score: 25)

ℹ️ Exercise extra caution when modifying these files.
```

**Knowledge graph queries:**
- Mission → Files mapping
- File → Missions mapping
- Bug/Fix relationship tracking
- Risk scoring and analysis

#### **Scenario 6: Review Overseer Suggestions**

**What it does:** Analyzes mission history and generates optimization suggestions.

**When to use:** After multiple runs, to identify improvements and auto-generate missions.

**How to use:**

```bash
# Run overseer review
python -m agent.overseer review --write-missions

# Or via Python
from agent import overseer

os = overseer.Overseer()

# Get strategic insights
insights = os.get_strategic_insights()
print(f"Total missions: {insights['total_missions']}")
print(f"Top domains: {insights['top_domains']}")

# Generate suggested missions
suggested = os.generate_suggested_missions()
for mission in suggested:
    print(f"Mission: {mission['task']}")
    print(f"Priority: {mission['priority']}")
    print(f"Reason: {mission['reason']}")

# Persist suggestions
os.persist_suggestions(insights)

# Write suggested missions to disk
paths = os.write_suggested_missions_to_disk()
print(f"Created {len(paths)} mission files in missions/")
```

**Expected output:**
```
=== OVERSEER REVIEW (last 10 missions) ===

Total Missions: 47
Success Rate: 87.2%

Domain Performance:
  coding      :  32 missions,  90.6% success, $ 0.85 avg cost
  finance     :  10 missions,  70.0% success, $ 1.20 avg cost
  research    :   5 missions, 100.0% success, $ 0.45 avg cost

Detected Patterns:
  - High failure rate in finance domain (30%)
  - Cost increasing trend for coding domain (+12% month-over-month)

Strategic Recommendations:
  - Improve finance domain workflow and quality checks
  - Review coding domain prompts for efficiency

Generated 2 Suggested Missions:
  - improve_finance_20251119_143022: Improve finance workflow and quality checks
    Priority: medium, Domain: finance
    Reason: Low success rate: 70.0%

💡 Use --write-missions to write these suggestions to missions/ directory

📁 Insights saved to: artifacts/overseer/suggestions_2025-11-19_143022.jsonl
```

#### **Scenario 7: Self-Refinement Proposals**

**What it does:** Generates improvement proposals based on performance analysis.

**When to use:** Periodically (weekly/monthly) to optimize system parameters.

**How to use:**

```python
from agent import self_refinement

# Initialize refiner
refiner = self_refinement.SelfRefiner(lookback_days=30)

# Generate improvement suggestions
improvements = refiner.suggest_improvements()
for imp in improvements:
    print(f"Area: {imp.area.value}")
    print(f"Priority: {imp.priority}")
    print(f"Suggestion: {imp.suggestion}")
    print(f"Impact: {imp.expected_impact}")

# Persist proposals to markdown
proposal_file = refiner.persist_proposals(improvements)
print(f"Proposals written to: {proposal_file}")

# Review and apply (manual process)
# 1. Review proposals/<date>_self_refine.md
# 2. Test changes in temporary branch
# 3. Approve and merge if tests pass
```

**Generated proposal file** (`proposals/2025-11-19_self_refine.md`):

```markdown
# Self-Refinement Proposals - 2025-11-19

Generated: 2025-11-19 14:35:12
Lookback Period: 30 days

## Performance Overview

- Total Missions: 47
- Success Rate: 87.2%
- Average Cost: $0.85
- Average Iterations: 2.3
- Cost Trend: increasing
- Success Trend: stable

## High Priority Improvements

### 1. Prompts

**Suggestion:** Optimize employee prompts to reduce iteration count

**Reasoning:**
- Average iterations per mission: 2.3 (target: < 2.0)
- 34% of missions require 3+ iterations
- Prompt clarity could reduce back-and-forth

**Expected Impact:** high
**Implementation Effort:** medium

## Review Process

1. Review each proposal carefully
2. Verify metrics and reasoning
3. Test changes in a temporary branch
4. Approve for implementation if tests pass
5. Document changes in change log

## Application Status

- [ ] Reviewed by maintainer
- [ ] Tests passed
- [ ] Approved for implementation
- [ ] Applied to production
```

### 2.6 Advanced Features & Internals

#### **Model Routing Strategy**

System-1.2 uses intelligent model routing to balance quality and cost:

**Cost Control Algorithm:**
1. First iteration: Always use cheap models (gpt-4o-mini)
2. Subsequent iterations:
   - If complexity is LOW and not important: Use gpt-4o-mini
   - If complexity is HIGH or important: Use gpt-4o (only on iterations 2-3)
   - Beyond iteration 3: Fall back to gpt-4o-mini

**Complexity Estimation:**
- High if previous failures > 1
- High if files count > 5
- High if task keywords match (refactor, architecture, migration, etc.)
- High if marked as `very_important` in config

**Cost Per Model** (approximate):
- gpt-4o: $0.05-0.15 per request
- gpt-4o-mini: $0.01-0.03 per request

#### **Knowledge Graph Schema**

The knowledge graph uses SQLite with 4 tables:

**1. entities**
- `id` (integer, primary key)
- `type` (text): "mission", "file", "bug", "domain"
- `name` (text): Identifier (mission_id, file_path, etc.)
- `metadata` (JSON): Additional properties
- `created_at` (timestamp)

**2. relationships**
- `id` (integer, primary key)
- `from_id` (integer, foreign key → entities)
- `to_id` (integer, foreign key → entities)
- `type` (text): "worked_on", "caused_bug", "fixed_bug", "has_domain"
- `metadata` (JSON): Relationship properties
- `created_at` (timestamp)

**3. mission_history**
- `id` (integer, primary key)
- `mission_id` (text, unique)
- `status` (text): "success", "failed", "in_progress"
- `domain` (text): Task domain
- `cost_usd` (real): Total cost
- `iterations` (integer): Iteration count
- `duration_seconds` (real): Runtime
- `files_modified` (integer): File count
- `metadata` (JSON): Additional data
- `created_at` (timestamp)

**4. file_snapshots**
- `id` (integer, primary key)
- `mission_id` (text)
- `file_path` (text)
- `content_hash` (text): SHA256 of content
- `size_bytes` (integer)
- `created_at` (timestamp)

**Example Queries:**

```python
# Find all files with >5 bug associations
kg = knowledge_graph.KnowledgeGraph()
risky = kg.get_risky_files(limit=10)

# Trace file history across missions
missions = kg.get_missions_for_file("sites/app/auth.py")
for m in missions:
    print(f"{m['mission']['name']}: {m['relationship']['metadata'].get('status')}")
```

#### **Workflow Execution**

Domain-specific workflows run after the main orchestration loop:

```python
from agent.workflows import get_workflow_for_domain
from agent.domain_router import Domain

# Get workflow for domain
workflow = get_workflow_for_domain(Domain.CODING)

# Execute workflow steps
result = workflow.run({
    "mission_id": "my_mission",
    "task": "Build API",
    "domain": "coding",
    "files": ["api.py", "routes.py"]
})

# Result structure:
{
    "workflow_name": "CodingWorkflow",
    "steps_completed": [
        {"step": "Syntax Check", "action": "qa_check", "result": {...}},
        {"step": "Run Linter", "action": "tool_call", "result": {...}},
        {"step": "Run Unit Tests", "action": "tool_call", "result": {...}},
    ],
    "steps_failed": [],
    "qa_findings": [...],
    "specialist_feedback": [...]
}
```

**Available Workflows:**
- **CodingWorkflow**: Syntax → Lint → Test → Security → QA
- **FinanceWorkflow**: Data validation → Calculations → Compliance → Specialist
- **LegalWorkflow**: Structure → Citations → Compliance
- **HRWorkflow**: Policy → Privacy → Sensitivity
- **OpsWorkflow**: Config → Infrastructure → Security → DevOps

#### **Specialist Selection Algorithm**

Specialists are matched to tasks using keyword/expertise scoring:

```python
from agent.specialists import select_specialist_for_task

# Match specialists to task
specialists = select_specialist_for_task(
    "Build a React dashboard with responsive design",
    min_score=0.3,
    max_specialists=3
)

# Returns: [(SpecialistProfile, score), ...]
# Frontend Specialist: score 0.85 (keywords: react, dashboard, responsive)
# Fullstack Specialist: score 0.45 (keywords: dashboard)
```

**Scoring Algorithm:**
- Keyword matches: +0.2 per match (max 0.6)
- Expertise matches: +0.15 per match (max 0.4)
- Total score capped at 1.0

**Cost Multipliers:**
- Generic: 1.0x
- QA: 1.1x
- Content Writer: 1.2x
- Fullstack: 1.25x
- Researcher: 1.3x
- DevOps: 1.3x
- Data: 1.3x
- Security: 1.4x

#### **Job Management & Background Execution**

The job manager enables async execution:

```python
from agent.jobs import JobManager

job_mgr = JobManager()

# Create background job
job = job_mgr.create_job({
    "mode": "3loop",
    "task": "Build a landing page",
    "max_rounds": 3
})

print(f"Job ID: {job.job_id}")
print(f"Status: {job.status}")  # "pending"

# Job executes in background thread
# Poll for updates
while job_mgr.get_job(job.job_id).status == "running":
    time.sleep(5)
    print("Still running...")

# Get final result
final_job = job_mgr.get_job(job.job_id)
print(f"Status: {final_job.status}")  # "completed" or "failed"
print(f"Result: {final_job.result}")
```

**Job States:**
- `pending` → `running` → `completed`
- `pending` → `running` → `failed`
- `pending` → `running` → `cancelled`

**Job Storage:**
Jobs are persisted to `data/jobs/<job_id>.json` for recovery after server restarts.

### 2.7 Troubleshooting & FAQ

#### **Installation Errors**

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# Re-install dependencies
pip install -r requirements.txt
```

---

**Problem:** `ImportError: No module named 'agent'`

**Solution:**
```bash
# Ensure you're in the correct directory
cd agent
python run_mode.py

# Or run from project root
cd /path/to/two_agent_web_starter_complete
python -m agent.run_mode
```

---

**Problem:** Python version too old

**Solution:**
```bash
# Check version
python --version

# If < 3.9, install newer Python
# Ubuntu/Debian:
sudo apt install python3.11 python3.11-venv

# Update symbolic links
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

#### **Runtime Errors**

**Problem:** `RuntimeError: OPENAI_API_KEY environment variable is not set`

**Solution:**
```bash
# Set in .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> .env

# Or export directly
export OPENAI_API_KEY=sk-your-key-here
```

---

**Problem:** HTTP 401 Unauthorized (OpenAI API)

**Solution:**
- Verify API key is correct
- Check key has not expired
- Ensure account has credits
- Try regenerating key at platform.openai.com

---

**Problem:** HTTP 429 Rate Limit Exceeded

**Solution:**
```bash
# The system will automatically retry (up to 3 attempts)
# If persistent:
# 1. Wait a few minutes
# 2. Reduce max_rounds to decrease API call frequency
# 3. Upgrade OpenAI account tier
# 4. Use cheaper models (gpt-4o-mini instead of gpt-4o)
```

---

**Problem:** Run gets stuck at "Nothing happens"

**Solution:**
1. Check logs: `tail -f run_logs/<run_id>/log.txt`
2. Verify OPENAI_API_KEY is set
3. Check network connectivity
4. Look for timeout errors in logs
5. Try reducing `max_rounds` or task complexity

---

**Problem:** Cost cap exceeded immediately

**Solution:**
```json
// Edit project_config.json
{
  "max_cost_usd": 5.0,  // Increase limit
  "cost_warning_usd": 3.0,
  "interactive_cost_mode": "once"  // Get prompted before major costs
}
```

---

**Problem:** Web dashboard won't start

**Solution:**
```bash
# Check if port 8000 is already in use
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill existing process or use different port
uvicorn agent.webapp.app:app --port 8001

# Check for import errors
python -c "from agent.webapp.app import app; print('OK')"
```

#### **Frequently Asked Questions**

**Q: How much does a typical run cost?**

A: Depends on task complexity and model selection:
- Simple task (2 rounds, gpt-4o-mini): $0.10 - $0.50
- Medium task (3 rounds, mixed models): $0.50 - $2.00
- Complex task (3 rounds, gpt-4o): $2.00 - $10.00

Use `cost_estimator.estimate_run_cost(task, mode, max_rounds)` for pre-flight estimates.

---

**Q: Can I use models other than OpenAI?**

A: Partial support. The infrastructure is ready (ModelProvider enum, ModelConfig), but provider-specific API adapters (e.g., `_post_anthropic()`) need implementation in `llm.py`. This is a future enhancement.

---

**Q: How do I add a new specialist?**

A: Edit `agent/specialists.py`:

```python
SpecialistType.MY_SPECIALIST: SpecialistProfile(
    name="My Specialist",
    specialist_type=SpecialistType.MY_SPECIALIST,
    expertise=["Area 1", "Area 2"],
    tools=["tool1", "tool2"],
    keywords=["keyword1", "keyword2"],
    cost_multiplier=1.2,
    complexity_threshold="medium",
    system_prompt_additions="Focus on..."
)
```

Then add to domain mappings in `get_specialists_for_domain()`.

---

**Q: How do I create a custom workflow?**

A: Create a new file in `agent/workflows/`:

```python
from .base import Workflow, WorkflowStep

class MyWorkflow(Workflow):
    def _build_steps(self) -> None:
        self.steps = [
            WorkflowStep(
                name="My QA Check",
                action="qa_check",
                config={"check_type": "my_check"},
            ),
            WorkflowStep(
                name="Run My Tool",
                action="tool_call",
                config={"tool_name": "my_tool"},
            ),
        ]
```

Register in `agent/workflows/__init__.py` and `domain_router.py`.

---

**Q: Where are logs stored?**

A:
- **Run logs**: `run_logs/<run_id>/`
- **Core event logs**: `run_logs_main/<run_id>.jsonl`
- **Mission logs**: `artifacts/<mission_id>/`
- **Overseer suggestions**: `artifacts/overseer/`
- **Self-refinement proposals**: `proposals/`
- **Knowledge graph DB**: `data/knowledge_graph.db`

---

**Q: How do I reset the knowledge graph?**

A:
```bash
# Backup first
cp data/knowledge_graph.db data/knowledge_graph.db.backup

# Delete database
rm data/knowledge_graph.db

# Will be recreated on next run
python -m agent.mission_runner run missions/example.json
```

---

**Q: Can I run multiple jobs in parallel?**

A: Yes, via the web dashboard. Each background job runs in its own thread. Recommended limit: 3-5 concurrent jobs (depends on system resources and API rate limits).

---

**Q: How do I export analytics data?**

A:
```bash
# Via web dashboard
# Navigate to http://127.0.0.1:8000/analytics
# Click "Export JSON" or "Export CSV"

# Or via Python
from agent import analytics

data = analytics.get_analytics_summary("my_project", timeframe="30d")
with open("analytics_export.json", "w") as f:
    json.dump(data, f, indent=2)
```

---

## 3. Main Modules & Key Functions

### 3.1 Orchestration & Execution

#### **Module: `agent/orchestrator.py`**

**Responsibility:** Core 3-loop orchestration engine. Coordinates Manager, Supervisor, and Employee agents through iterative planning, implementation, and review cycles. Integrates with knowledge graph, specialists, workflows, and all advanced features.

**Architecture:** Hierarchical agent loop with knowledge graph integration, specialist routing, workflow execution, and cost tracking.

**Key Functions:**

- **`run(task: str, project_path: Path, config: Dict) -> Dict`**
  Main entry point for 3-loop orchestration.

  *Parameters:*
  - `task`: Natural language task description
  - `project_path`: Path to project directory (under sites/)
  - `config`: Runtime configuration (max_rounds, cost caps, etc.)

  *Returns:* Dict with status, cost_summary, files_modified, rounds_completed

  *Side effects:* Writes files to project_path, logs to knowledge graph, creates artifacts

- **`_run_iteration(iteration_index: int, context: Dict) -> Dict`**
  Executes a single Manager → Supervisor → Employee iteration.

  *Process:*
  1. Manager creates plan
  2. Supervisor phases tasks
  3. Employee implements each phase
  4. Files are written to disk
  5. Manager reviews output
  6. Iteration logged

  *Returns:* Iteration result with status ("approved", "retry", "failed")

- **`_build_manager_prompt(task: str, iteration: int, history: List) -> str`**
  Constructs context-aware prompts for the Manager agent.

  *Includes:*
  - Original task description
  - Risk insights from knowledge graph (high-risk files)
  - Domain-specific guidance
  - Iteration history and feedback
  - Cost warnings if approaching limit

  *Returns:* Formatted prompt string

- **`_execute_employee_tasks(tasks: List[Dict], project_path: Path) -> List[str]`**
  Runs Employee agent on each phased task and collects written files.

  *Features:*
  - Parallel task execution (if safe)
  - Tool calls (linting, testing, Git operations)
  - Sandbox execution for untrusted code
  - File tracking for knowledge graph

  *Returns:* List of file paths written during execution

**Integration Points:**
- Calls `llm.chat_json()` for LLM interactions
- Uses `model_router.choose_model()` for intelligent model selection
- Queries `knowledge_graph` for risk insights
- Invokes `specialists.select_specialist_for_task()` for expert routing
- Executes `workflows.get_workflow_for_domain()` for QA pipelines
- Tracks costs via `cost_tracker`
- Logs events via `run_logger` and `core_logging`

---

#### **Module: `agent/mission_runner.py`**

**Responsibility:** CLI and programmatic interface for running missions defined in JSON/YAML files. Manages mission lifecycle, knowledge graph logging, and artifact generation.

**Architecture:** Mission file parser → Orchestrator invocation → Knowledge graph logging → Artifact generation

**Key Functions:**

- **`load_mission_file(mission_file_path: Path) -> Dict`**
  Loads and validates mission definition from JSON or YAML.

  *Supports:* JSON and YAML formats

  *Returns:* Mission configuration dict

  *Raises:* FileNotFoundError, ValueError for invalid missions

- **`run_mission(mission_file_path: Path, override_config: Optional[Dict] = None) -> Dict`**
  Executes a complete mission from start to finish.

  *Process:*
  1. Load mission file
  2. Classify domain (if not specified)
  3. Execute via orchestrator
  4. Log to knowledge graph (mission, files, relationships)
  5. Generate mission report
  6. Save artifacts

  *Returns:* Mission result with status, cost, files_modified, mission_id

  *Side effects:* Creates knowledge graph entities/relationships, writes artifacts

- **`list_missions(missions_dir: Path = "missions/") -> List[Dict]`**
  Lists all mission files in the missions directory.

  *Returns:* List of mission metadata (id, task, status, tags)

- **`get_mission_status(mission_id: str) -> Dict`**
  Retrieves mission status from knowledge graph.

  *Returns:* Mission metadata, status, cost, iterations, files_modified

**CLI Commands:**
```bash
python -m agent.mission_runner run missions/my_mission.json
python -m agent.mission_runner list
python -m agent.mission_runner status <mission_id>
```

**Knowledge Graph Integration:**
After mission completion, creates:
- MISSION entity
- FILE entities (one per modified file)
- WORKED_ON relationships (mission → file)
- Domain relationship (mission → domain)
- Logs to mission_history table

---

### 3.2 LLM & Model Management

#### **Module: `agent/llm.py`**

**Responsibility:** Unified LLM interface. Handles OpenAI API calls, token counting, cost tracking, retries, simulation mode, and error handling.

**Architecture:** Thin abstraction layer over OpenAI API with automatic retries, cost tracking integration, and simulation support.

**Key Functions:**

- **`chat_json(messages: List[Dict], model: str = "gpt-4o-mini", temperature: float = 0.0, max_tokens: int = 4096) -> Dict`**
  Sends chat completion request and expects JSON response.

  *Parameters:*
  - `messages`: List of message dicts ({"role": "user"|"system"|"assistant", "content": "..."})
  - `model`: Model identifier (routed through model_router)
  - `temperature`: Sampling temperature (0.0 = deterministic, 1.0 = creative)
  - `max_tokens`: Maximum response length

  *Returns:* Parsed JSON response from model

  *Features:*
  - Automatic JSON parsing
  - Token counting and cost tracking
  - 3 retry attempts on failure
  - Simulation mode support (returns stub if enabled)
  - Timeout handling

  *Side effects:* Calls `cost_tracker.track(model, prompt_tokens, completion_tokens)`

- **`count_tokens(text: str, model: str = "gpt-4o-mini") -> int`**
  Counts tokens in text using tiktoken encoding.

  *Used for:* Cost estimation, prompt length validation

  *Returns:* Token count

- **`_post(payload: Dict) -> Dict`**
  Low-level HTTP POST to OpenAI API with retries.

  *Retries:* 3 attempts with exponential backoff

  *Error handling:* Returns stub dict with `timeout=True` on failure instead of raising

  *Simulation mode:* Checks `config.SIMULATION_MODE` and returns deterministic stub

**Error Handling:**
- HTTP errors: Retry 3 times, then return timeout stub
- JSON parse errors: Log and return empty dict
- Rate limits: Automatic retry with backoff
- Network errors: Retry 3 times

**Simulation Mode:**
When `config.simulation.value != "off"`:
```python
return {
    "choices": [{
        "message": {
            "content": json.dumps({
                "plan": ["Simulated plan step 1", "Simulated plan step 2"],
                "status": "approved",
                # ... deterministic stub data
            })
        }
    }],
    "usage": {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
    },
    "simulated": True,
}
```

---

#### **Module: `agent/model_router.py`**

**Responsibility:** Intelligent model selection based on task characteristics, iteration count, and cost constraints. Enforces GPT-5 usage restrictions to control costs.

**Architecture:** Rule-based routing with complexity estimation and cost gating.

**Key Functions:**

- **`choose_model(task_type: str, complexity: str = "low", role: str = "unknown", interaction_index: int = 1, is_very_important: bool = False, config: Optional[Dict] = None) -> str`**
  Selects optimal model for a given task.

  *Parameters:*
  - `task_type`: "planning", "code", "docs", "analysis", "review"
  - `complexity`: "low" or "high"
  - `role`: Agent role (for logging)
  - `interaction_index`: Current iteration (1-indexed)
  - `is_very_important`: Override flag for critical tasks
  - `config`: Project config for very_important_stages lookup

  *Returns:* Model identifier (e.g., "gpt-4o", "gpt-4o-mini")

  *Key Constraint:* gpt-4o ONLY allowed on iterations 2-3 when complexity is high OR is_very_important is True

  *Cost Control Logic:*
  ```
  if candidate_model == "gpt-4o":
      if interaction_index not in [2, 3]:
          downgrade to gpt-4o-mini
      elif complexity == "low" and not is_very_important:
          downgrade to gpt-4o-mini
  ```

- **`estimate_complexity(stage: Optional[Dict] = None, previous_failures: int = 0, files_count: int = 0, config: Optional[Dict] = None) -> str`**
  Estimates task complexity using heuristics.

  *Returns:* "low" or "high"

  *Heuristics:*
  - High if previous_failures > 1
  - High if files_count > 5
  - High if stage name/description contains keywords (refactor, architecture, migration, etc.)
  - High if stage in config.llm_very_important_stages
  - Otherwise: low

- **`ModelConfig` (dataclass)**
  Configuration for model + provider.

  *Fields:*
  - `provider`: ModelProvider enum (OPENAI, ANTHROPIC, LOCAL)
  - `model_name`: Model identifier
  - `max_tokens`: Response length limit (default: 4096)
  - `temperature`: Sampling temperature (default: 0.0)
  - `cost_per_1k_tokens`: Estimated cost for budgeting

- **`get_provider_for_model(model_name: str) -> ModelProvider`**
  Determines provider from model name.

  *Logic:*
  - "gpt" or "o1" in name → OPENAI
  - "claude" in name → ANTHROPIC
  - "local" or "llama" in name → LOCAL
  - Default: OPENAI

**Routing Rules Table:**
| Task Type | Complexity | Model Selected |
|-----------|-----------|----------------|
| planning | low | gpt-4o-mini |
| planning | high | gpt-4o (if iteration 2-3) |
| code | low | gpt-4o-mini |
| code | high | gpt-4o (if iteration 2-3) |
| docs | low | gpt-4o-mini |
| docs | high | gpt-4o-mini (docs rarely need gpt-4o) |
| analysis | low | gpt-4o-mini |
| analysis | high | gpt-4o-mini |
| review | low | gpt-4o-mini |
| review | high | gpt-4o-mini |

---

### 3.3 Knowledge Graph & Analytics

#### **Module: `agent/knowledge_graph.py`**

**Responsibility:** SQLite-backed knowledge graph for tracking missions, files, bugs, fixes, and relationships. Enables historical learning, risk analysis, and mission traceability.

**Architecture:** Entity-relationship graph stored in SQLite with 4 tables (entities, relationships, mission_history, file_snapshots).

**Key Classes:**

- **`KnowledgeGraph`**
  Main interface for graph operations.

**Key Functions:**

- **`add_entity(type: str, name: str, metadata: Dict) -> int`**
  Creates or updates an entity in the graph.

  *Parameters:*
  - `type`: Entity type ("mission", "file", "bug", "domain")
  - `name`: Unique identifier
  - `metadata`: Additional properties as JSON

  *Returns:* Entity ID

  *Idempotent:* If entity exists, updates metadata instead of creating duplicate

- **`add_relationship(from_id: int, to_id: int, relationship_type: str, metadata: Dict) -> int`**
  Creates a relationship between two entities.

  *Common relationship types:*
  - "worked_on": mission → file
  - "caused_bug": mission → bug
  - "fixed_bug": mission → bug
  - "has_domain": mission → domain

  *Returns:* Relationship ID

- **`log_mission(mission_id: str, status: str, domain: str, cost_usd: float, iterations: int, duration_seconds: float, files_modified: int, metadata: Dict) -> None`**
  Logs mission execution to history table.

  *Used by:* mission_runner after orchestrator completion

  *Side effects:* Inserts row into mission_history table

- **`get_files_for_mission(mission_id: str) -> List[Dict]`**
  Retrieves all files worked on by a mission.

  *Returns:* List of file entities with relationship metadata

  *Example:*
  ```python
  [
      {
          "file": {"id": 42, "type": "file", "name": "index.html", ...},
          "relationship": {"type": "worked_on", "metadata": {...}}
      },
      ...
  ]
  ```

- **`get_missions_for_file(file_path: str) -> List[Dict]`**
  Retrieves all missions that modified a file.

  *Returns:* List of mission entities with relationship metadata

  *Use case:* Understanding file history, identifying frequent changes

- **`get_bug_relationships(mission_id: str) -> Dict[str, List[Dict]]`**
  Queries all bug/fix relationships for a mission.

  *Returns:* Dict with "caused_bugs" and "fixed_bugs" lists

  *Used for:* Quality metrics, defect tracking

- **`get_risky_files(limit: int = 10) -> List[Dict]`**
  Identifies files with highest bug counts or failure associations.

  *SQL Query:* Joins entities → relationships → mission_history to count bugs and failed missions per file

  *Returns:* List of file dicts with:
  - `file_path`: File path
  - `bug_count`: Number of bugs associated
  - `mission_count`: Total missions touching file
  - `failed_mission_count`: Missions that failed while touching this file
  - `risk_score`: Computed as (bug_count * 10 + failed_mission_count * 5)

  *Sort order:* Descending by risk_score

- **`find_related(entity_id: int, relationship_type: Optional[str] = None, direction: str = "outgoing") -> List[Tuple[Dict, Dict]]`**
  General-purpose relationship traversal.

  *Parameters:*
  - `entity_id`: Starting entity
  - `relationship_type`: Filter by type (optional)
  - `direction`: "outgoing", "incoming", or "both"

  *Returns:* List of (related_entity, relationship_metadata) tuples

**Database Schema:**

```sql
CREATE TABLE entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(type, name)
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER NOT NULL,
    to_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(from_id) REFERENCES entities(id),
    FOREIGN KEY(to_id) REFERENCES entities(id)
);

CREATE TABLE mission_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    domain TEXT,
    cost_usd REAL,
    iterations INTEGER,
    duration_seconds REAL,
    files_modified INTEGER,
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE file_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    size_bytes INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

#### **Module: `agent/project_stats.py`**

**Responsibility:** Analytics and statistical analysis of missions. Computes trends, success rates, cost patterns, and risk insights from knowledge graph data.

**Key Functions:**

- **`get_risky_files(project_path: Optional[Path] = None, limit: int = 5) -> List[Tuple[str, float]]`**
  Convenience wrapper around knowledge_graph.get_risky_files().

  *Returns:* List of (file_path, risk_score) tuples

  *Used by:* orchestrator to inject risk warnings into manager prompts

- **`format_risk_summary(risky_files: List[Tuple[str, float]]) -> str`**
  Formats risky files into human-readable summary for prompts.

  *Example output:*
  ```
  ⚠️ High-Risk Files (based on historical bugs and failures):
    • sites/auth/login.py (risk score: 45)
    • sites/api/routes.py (risk score: 30)

  ℹ️ Exercise extra caution when modifying these files.
  ```

- **`compute_growth_rate(history: List[Dict], metric_path: str) -> float`**
  Calculates growth rate of a metric over time.

  *Parameters:*
  - `history`: List of historical data points
  - `metric_path`: JSON path to metric (e.g., "cost_usd", "iterations")

  *Returns:* Growth rate as percentage (e.g., 0.15 = 15% growth)

- **`get_project_metrics(project_path: Path) -> Dict`**
  Aggregates metrics for a specific project.

  *Returns:* Dict with:
  - Total missions
  - Success rate
  - Average cost
  - Average iterations
  - Total cost
  - Cost trend
  - Success trend

---

### 3.4 Specialist & Workflow Systems

#### **Module: `agent/specialists.py`**

**Responsibility:** Defines specialist agent types with expertise, tools, keywords, and domain mappings. Provides task-based specialist selection and matching.

**Architecture:** Registry of 10 specialist types with keyword/expertise scoring algorithm for task matching.

**Specialist Types:**
1. **FRONTEND** — React, Vue, CSS, UX (keywords: react, vue, css, ui, responsive)
2. **BACKEND** — APIs, databases, services (keywords: api, database, server, backend)
3. **DATA** — Analytics, ML, data pipelines (keywords: data, analytics, ml, pipeline)
4. **SECURITY** — Auth, encryption, vulnerabilities (keywords: security, auth, encryption, xss)
5. **DEVOPS** — CI/CD, Docker, infrastructure (keywords: devops, docker, kubernetes, deploy)
6. **QA** — Testing, quality assurance (keywords: test, testing, qa, quality)
7. **FULLSTACK** — End-to-end development (keywords: fullstack, full-stack, e2e)
8. **GENERIC** — General development (no specific keywords)
9. **CONTENT_WRITER** — Documentation, technical writing (keywords: writing, documentation, docs, tutorial)
10. **RESEARCHER** — Data analysis, literature review (keywords: research, analysis, study, investigation)

**Key Classes:**

- **`SpecialistProfile` (dataclass)**
  Profile for a specialist agent.

  *Fields:*
  - `name`: Display name
  - `specialist_type`: SpecialistType enum
  - `expertise`: List of expertise areas
  - `tools`: Preferred tools
  - `keywords`: Keywords for task matching
  - `cost_multiplier`: Cost adjustment (1.0 = normal, 1.5 = 50% more)
  - `complexity_threshold`: "low", "medium", or "high"
  - `system_prompt_additions`: Additional prompt text

**Key Functions:**

- **`get_specialist(specialist_type: str) -> SpecialistProfile`**
  Retrieves specialist by type.

  *Returns:* SpecialistProfile instance

  *Raises:* ValueError if type not found

- **`select_specialist_for_task(task: str, min_score: float = 0.3, max_specialists: int = 3) -> List[Tuple[SpecialistProfile, float]]`**
  Matches specialists to a task using scoring algorithm.

  *Scoring:*
  - Keyword matches: +0.2 per match (max 0.6)
  - Expertise matches: +0.15 per match (max 0.4)
  - Total score capped at 1.0

  *Returns:* List of (specialist, score) tuples sorted descending by score

  *Example:*
  ```python
  specialists = select_specialist_for_task(
      "Build a React dashboard with responsive design"
  )
  # Returns: [(FrontendSpecialist, 0.85), (FullstackSpecialist, 0.45), ...]
  ```

- **`get_specialists_for_domain(domain: str) -> List[SpecialistProfile]`**
  Returns specialists applicable to a domain.

  *Domain mappings:*
  - coding → FRONTEND, BACKEND, FULLSTACK, SECURITY, DEVOPS, QA
  - finance → DATA, RESEARCHER
  - legal → RESEARCHER, SECURITY, CONTENT_WRITER
  - hr → CONTENT_WRITER
  - research → RESEARCHER, DATA
  - documentation → CONTENT_WRITER

  *Returns:* List of relevant SpecialistProfile instances

- **`list_all_specialists() -> List[SpecialistProfile]`**
  Returns all specialist profiles.

**Cost Multipliers:**
- Generic: 1.0x
- QA: 1.1x
- Content Writer: 1.2x
- Fullstack: 1.25x
- Researcher: 1.3x
- DevOps: 1.3x
- Data: 1.3x
- Security: 1.4x

---

#### **Module: `agent/workflows/` (package)**

**Responsibility:** Domain-specific QA pipelines and workflow definitions. Each workflow defines a sequence of quality checks, tool invocations, and specialist passes.

**Modules:**

**1. `base.py`** — Abstract base class

**Key Classes:**

- **`WorkflowStep` (dataclass)**
  Represents a single workflow step.

  *Fields:*
  - `name`: Step name
  - `action`: "qa_check", "tool_call", or "specialist_pass"
  - `config`: Step-specific configuration dict

- **`Workflow` (ABC)**
  Base class for domain workflows.

  *Abstract Methods:*
  - `_build_steps()`: Define workflow steps (must be implemented by subclasses)

  *Key Methods:*
  - `run(mission_context: Dict) -> Dict`: Execute workflow
  - `_execute_step(step, context) -> Dict`: Execute single step
  - `_run_qa_check(config, context) -> Dict`: Run QA check
  - `_run_tool(config, context) -> Dict`: Run tool
  - `_run_specialist(config, context) -> Dict`: Run specialist pass

**2. `coding.py`** — Software development workflow

**Steps:**
1. Syntax Check (qa_check)
2. Run Linter (tool_call: format_code with ruff)
3. Run Unit Tests (tool_call: run_unit_tests)
4. Security Audit (specialist_pass: security)
5. Code Review (specialist_pass: qa)

**3. `finance.py`** — Financial analysis workflow

**Steps:**
1. Data Validation (qa_check: data_integrity)
2. Calculation Verification (qa_check: calculations)
3. Compliance Check (qa_check: compliance, standards: GAAP/IFRS)
4. Data Specialist Review (specialist_pass: data)

**4. `legal.py`** — Legal document workflow

**Steps:**
1. Document Structure (qa_check: structure)
2. Citation Verification (qa_check: citations)
3. Compliance Check (qa_check: legal_compliance)

**5. `hr.py`** — HR workflow

**Steps:**
1. Policy Compliance (qa_check: hr_policy)
2. Data Privacy (qa_check: privacy, standards: GDPR/CCPA)
3. Sensitivity Review (qa_check: sensitivity)

**6. `ops.py`** — Operations workflow

**Steps:**
1. Configuration Validation (qa_check: config)
2. Infrastructure Check (qa_check: infrastructure)
3. Security Audit (specialist_pass: security)
4. DevOps Review (specialist_pass: devops)

**Integration:**

```python
from agent.workflows import get_workflow_for_domain
from agent.domain_router import Domain

# Get workflow for domain
workflow = get_workflow_for_domain(Domain.CODING)

# Execute workflow
result = workflow.run({
    "mission_id": "my_mission",
    "task": "Build API",
    "domain": "coding",
    "files": ["api.py", "routes.py"]
})

# Result structure:
{
    "workflow_name": "CodingWorkflow",
    "steps_completed": [...],
    "steps_failed": [],
    "qa_findings": [],
    "specialist_feedback": []
}
```

---

### 3.5 Quality Assurance & Safety

#### **Module: `agent/qa.py`**

**Responsibility:** Automated quality assurance for HTML/CSS/JS projects. Validates structure, accessibility, code quality, and runs smoke tests.

**Key Functions:**

- **`run_qa_checks(project_path: Path, config: Dict) -> Dict`**
  Runs all configured QA checks on a project.

  *Checks performed:*
  - HTML validation (title, meta, lang, H1)
  - Accessibility (image alt text, empty links, button labels)
  - Code quality (large files, console.logs, duplicate IDs)
  - Smoke tests (optional, via external command)

  *Returns:* QA report dict with:
  ```python
  {
      "passed": True/False,
      "issues": [
          {"severity": "error", "message": "Missing <title>"},
          ...
      ],
      "checks_run": 10,
      "checks_passed": 8,
      "checks_failed": 2
  }
  ```

- **`validate_html_quality(html_path: Path, config: Dict) -> List[Dict]`**
  Validates HTML structure and content.

  *Checks:*
  - `<title>` presence
  - `<meta name="description">` presence
  - `<html lang="...">` attribute
  - At least one `<h1>` tag
  - Empty links (`<a href="#">`)
  - Images missing alt text
  - Duplicate ID attributes

  *Returns:* List of issue dicts

- **`check_accessibility(project_path: Path, config: Dict) -> List[Dict]`**
  Runs accessibility checks.

  *Checks:*
  - All images have alt attributes
  - Empty button labels
  - Missing ARIA labels
  - Color contrast (if configured)

  *Returns:* List of accessibility issues

- **`run_smoke_tests(project_path: Path, test_command: str, timeout: int = 60) -> Dict`**
  Executes smoke tests via external command.

  *Example test_command:* `"pytest tests/smoke --tb=short"`

  *Returns:* Test result with success status and output

- **`generate_qa_report(project_path: Path, qa_results: Dict) -> Path`**
  Generates HTML/JSON QA report.

  *Saves to:* `artifacts/<mission_id>/qa_report.json`

  *Returns:* Path to report file

**Configuration (in project_config.json):**
```json
{
  "qa": {
    "enabled": true,
    "require_title": true,
    "require_meta_description": true,
    "require_lang_attribute": true,
    "require_h1": true,
    "max_empty_links": 10,
    "max_images_missing_alt": 0,
    "max_duplicate_ids": 0,
    "max_console_logs": 5,
    "allow_large_files": true,
    "max_large_files": 5,
    "large_file_threshold": 5000,
    "require_smoke_tests_pass": false,
    "smoke_test_command": null
  }
}
```

---

#### **Module: `agent/sandbox.py`**

**Responsibility:** Safe code execution in resource-limited subprocesses. Runs Python, Node.js, and shell scripts with timeouts and memory constraints.

**Key Functions:**

- **`run_python_snippet(code: str, working_dir: Optional[Path] = None, timeout_seconds: int = 30) -> Dict`**
  Executes Python code snippet in sandbox.

  *Process:*
  1. Write code to temporary file
  2. Execute with `python3` in subprocess
  3. Apply resource limits (CPU, memory)
  4. Capture stdout/stderr
  5. Clean up temporary file

  *Returns:* Dict with:
  ```python
  {
      "success": True/False,
      "stdout": "output...",
      "stderr": "errors...",
      "exit_code": 0,
      "timeout": False,
      "error": None
  }
  ```

  *Limits:*
  - Timeout: 30 seconds
  - Memory: 256 MB
  - CPU time: 5 minutes

- **`run_node_snippet(code: str, working_dir: Optional[Path] = None, timeout_seconds: int = 30) -> Dict`**
  Executes Node.js code snippet in sandbox.

  *Same interface as run_python_snippet*

- **`run_script(script_path: Path, args: Optional[List[str]] = None, working_dir: Optional[Path] = None, timeout_seconds: int = 60, interpreter: Optional[str] = None) -> Dict`**
  Executes a script file in sandbox.

  *Parameters:*
  - `script_path`: Path to script file
  - `args`: Command-line arguments
  - `interpreter`: Explicit interpreter (e.g., "python3", "node", "bash")

  *Returns:* Same dict structure as snippet functions

- **`run_in_sandbox(command: List[str], working_dir: Optional[Path] = None, timeout_seconds: int = 120, memory_limit_mb: Optional[int] = None, env: Optional[Dict] = None, network_isolation: bool = False) -> Dict`**
  Low-level sandbox execution.

  *Features:*
  - Resource limits (CPU, memory)
  - Timeout enforcement
  - Network isolation (Linux only, requires unshare)
  - Environment variable control
  - Automatic cleanup

  *Used by:* snippet and script functions

**Security Features:**
- `shell=False` in subprocess calls (prevents shell injection)
- Explicit command arguments (no shell parsing)
- Resource limits via `resource` module (Unix)
- Timeout enforcement
- Working directory isolation
- Optional network isolation

**Tool Registration:**

Tools registered in `exec_tools.TOOL_REGISTRY`:
- `sandbox_run_python` — Available in CODING, FINANCE, RESEARCH domains
- `sandbox_run_node` — Available in CODING domain only
- `sandbox_run_script` — Available in CODING domain only

**Domain Restrictions:**
- CODING: All 3 sandbox tools
- FINANCE/RESEARCH: Python only (for data analysis)
- Other domains: No sandbox access (security)

---

### 3.6 Web Interface & Job Management

#### **Module: `agent/webapp/app.py`**

**Responsibility:** FastAPI web application providing REST API and web UI for project management, job execution, analytics, and system tuning.

**Architecture:** FastAPI + Jinja2 templates + background job execution.

**Key Routes:**

**Dashboard & UI:**
- `GET /` — Dashboard home page
- `GET /projects` — Project explorer page
- `GET /jobs/{job_id}` — Job detail page
- `GET /analytics` — Analytics dashboard
- `GET /tuning` — Self-optimization dashboard

**API Endpoints:**

**Projects:**
- `GET /api/projects` — List all projects in sites/

  *Returns:* `[{"name": "my_project", "path": "sites/my_project", ...}, ...]`

- `GET /api/projects/{project_name}/files` — List project files

  *Returns:* File tree structure

**Runs:**
- `POST /api/run` — Start synchronous run (blocking)

  *Body:* `{mode, task, project_subdir, max_rounds, max_cost_usd, ...}`

  *Returns:* Run summary after completion

- `GET /api/runs` — List run history

  *Query params:* `limit`, `offset`, `project_filter`

  *Returns:* `[{run_id, status, cost, timestamp, ...}, ...]`

- `GET /api/runs/{run_id}` — Get run details

  *Returns:* Complete run summary with iterations, costs, files

**Jobs (Background Execution):**
- `POST /api/jobs` — Create background job

  *Body:* Same as `/api/run`

  *Returns:* `{job_id, status: "pending"}`

- `GET /api/jobs` — List all jobs

  *Returns:* `[{job_id, status, created_at, ...}, ...]`

- `GET /api/jobs/{job_id}` — Get job status

  *Returns:* `{job_id, status, progress, result, ...}`

- `POST /api/jobs/{job_id}/cancel` — Cancel running job

- `GET /api/jobs/{job_id}/logs` — Stream job logs

  *Returns:* Server-sent events (SSE) stream of log lines

**Analytics:**
- `GET /api/analytics` — Get analytics summary

  *Query params:* `project`, `timeframe` (7d, 30d, 90d)

  *Returns:* Aggregated metrics, trends, costs

- `GET /api/analytics/export` — Export analytics data

  *Query params:* `format` (json, csv)

  *Returns:* Downloaded file

**Tuning:**
- `GET /api/tuning/recommendations` — Get optimization recommendations

  *Returns:* List of recommendation dicts

- `POST /api/tuning/apply` — Apply recommendation

  *Body:* `{recommendation_id}`

  *Returns:* Application result

**File Explorer:**
- `GET /api/projects/{project}/snapshots` — List iteration snapshots
- `GET /api/projects/{project}/snapshots/{iteration}` — Get snapshot files
- `GET /api/projects/{project}/diff?iter1=X&iter2=Y` — Get diff between iterations

**Server Configuration:**
```python
# Start server
uvicorn agent.webapp.app:app --host 127.0.0.1 --port 8000 --reload

# Access at http://127.0.0.1:8000
```

**Features:**
- CORS enabled for API access
- Static file serving (/static/)
- Jinja2 template rendering
- Background job management via JobManager
- Live log streaming via Server-Sent Events
- Error handling and validation

---

#### **Module: `agent/jobs.py`**

**Responsibility:** Background job manager for async execution. Runs orchestrator tasks in separate threads with state persistence and progress tracking.

**Architecture:** Thread-based job execution with JSON state persistence.

**Key Classes:**

- **`Job` (dataclass)**
  Represents a background job.

  *Fields:*
  - `job_id`: Unique identifier (UUID)
  - `config`: Job configuration (mode, task, max_rounds, etc.)
  - `status`: "pending", "running", "completed", "failed", "cancelled"
  - `result`: Execution result (None while running)
  - `error`: Error message if failed
  - `created_at`: Timestamp
  - `started_at`: Timestamp
  - `completed_at`: Timestamp
  - `progress`: Progress percentage (0-100)
  - `log_lines`: List of log messages

- **`JobManager`**
  Manages job lifecycle and persistence.

**Key Functions:**

- **`create_job(config: Dict) -> Job`**
  Creates and starts a new background job.

  *Process:*
  1. Generate unique job_id
  2. Create Job object with status="pending"
  3. Persist to disk
  4. Start execution thread
  5. Update status to "running"

  *Returns:* Job object

  *Side effects:* Writes `data/jobs/{job_id}.json`

- **`get_job(job_id: str) -> Optional[Job]`**
  Retrieves job by ID.

  *Returns:* Job object or None if not found

  *Source:* In-memory cache or disk

- **`list_jobs(status_filter: Optional[str] = None, limit: int = 50) -> List[Job]`**
  Lists jobs with optional filtering.

  *Parameters:*
  - `status_filter`: Filter by status (optional)
  - `limit`: Maximum jobs to return

  *Returns:* List of Job objects sorted by created_at descending

- **`cancel_job(job_id: str) -> bool`**
  Attempts to cancel a running job.

  *Returns:* True if cancelled, False if job not found or already completed

  *Implementation:* Sets cancellation flag; job thread checks flag periodically

- **`stream_logs(job_id: str) -> Generator[str, None, None]`**
  Yields log lines as they're generated.

  *Returns:* Generator of log line strings

  *Used by:* SSE endpoint for live log streaming

- **`_execute_job(job: Job) -> None`**
  Background thread execution function.

  *Process:*
  1. Update status to "running"
  2. Call `runner.run_project(job.config)`
  3. Capture result and logs
  4. Update job with result and status="completed"
  5. Persist final state

  *Error handling:* Catches exceptions, sets status="failed", stores error message

**State Persistence:**

Jobs are persisted to `data/jobs/{job_id}.json`:
```json
{
  "job_id": "uuid-here",
  "config": {...},
  "status": "completed",
  "result": {...},
  "error": null,
  "created_at": "2025-11-19T14:30:00Z",
  "started_at": "2025-11-19T14:30:01Z",
  "completed_at": "2025-11-19T14:32:45Z",
  "progress": 100,
  "log_lines": [...]
}
```

**Concurrency:**
- Thread-safe: Uses locks for job list access
- Multiple jobs can run concurrently (each in its own thread)
- Recommended limit: 3-5 concurrent jobs (depends on system resources and API rate limits)

**Cleanup:**
- Completed jobs persist indefinitely
- Can be manually deleted via `rm data/jobs/{job_id}.json`
- Future enhancement: Automatic cleanup after N days

---

## 4. Full Dependency & Install Checklist

### 4.1 Core Runtimes

**Python 3.9+** (Required)
- **Purpose:** Primary language for entire system
- **Check:** `python --version` or `python3 --version`
- **Install:**
  - Ubuntu/Debian: `sudo apt update && sudo apt install python3 python3-pip python3-venv`
  - macOS: `brew install python@3.11`
  - Windows: Download from python.org or Microsoft Store
- **Recommended version:** 3.11 or 3.12 (for best performance and type hint support)

**Git** (Required)
- **Purpose:** Version control, auto-commit features, repository management
- **Check:** `git --version`
- **Install:**
  - Ubuntu/Debian: `sudo apt install git`
  - macOS: `brew install git` or Xcode Command Line Tools
  - Windows: Download from git-scm.com

**Node.js 16+** (Optional)
- **Purpose:** Sandbox execution of JavaScript code, running Node.js projects
- **Check:** `node --version && npm --version`
- **Install:**
  - Ubuntu/Debian: `curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs`
  - macOS: `brew install node`
  - Windows: Download from nodejs.org
- **Recommended version:** 18 LTS or 20 LTS

### 4.2 Python Libraries

**From requirements.txt** (install via `pip install -r requirements.txt`):

**Web Framework & Server:**
- **fastapi** (≥0.104.0) — Web framework for REST API and dashboard
- **uvicorn[standard]** (≥0.24.0) — ASGI server for FastAPI
- **jinja2** (≥3.1.0) — Template engine for HTML rendering
- **python-multipart** (≥0.0.6) — Form data handling in FastAPI

**Testing:**
- **pytest** (≥7.4.0) — Test framework
- **pytest-cov** (≥4.1.0) — Coverage reporting

**Implicit Dependencies** (installed automatically as dependencies of above):
- **pydantic** — Data validation (via FastAPI)
- **starlette** — ASGI toolkit (via FastAPI)
- **anyio** — Async support (via Starlette)
- **idna** — Internationalized domain names (via anyio)
- **sniffio** — Async library detection (via anyio)
- **typing-extensions** — Backported type hints (for Python < 3.10)

**Not in requirements.txt but used in code** (implicit/optional):
- **requests** — HTTP client (for OpenAI API calls) — Usually included with Python
- **tiktoken** — OpenAI token counter — Install via `pip install tiktoken`
- **sqlite3** — Database (included with Python standard library)
- **json**, **pathlib**, **subprocess**, **os**, **sys** — Standard library modules

**Optional Development Tools** (mentioned in requirements.txt comments):
- **ruff** — Fast Python linter — `pip install ruff`
- **mypy** — Static type checker — `pip install mypy`
- **psutil** — Memory profiling — `pip install psutil`

### 4.3 External Tools & CLIs

**OpenAI Python SDK** (Implicit, install if needed):
```bash
pip install openai
```
- **Purpose:** OpenAI API client library
- **Used by:** llm.py for chat completions

**Requests Library** (Usually included, install if missing):
```bash
pip install requests
```
- **Purpose:** HTTP requests to OpenAI API
- **Used by:** llm.py

**Tiktoken** (OpenAI tokenizer, install if needed):
```bash
pip install tiktoken
```
- **Purpose:** Accurate token counting for cost tracking
- **Used by:** llm.py, cost_tracker.py

**PyYAML** (Optional, for YAML mission files):
```bash
pip install pyyaml
```
- **Purpose:** Parse YAML mission definitions
- **Used by:** mission_runner.py

**Browser** (Required for web dashboard):
- Chrome, Firefox, Safari, or Edge (modern versions)
- **Purpose:** Access web UI at http://127.0.0.1:8000

**Code Formatters** (Optional, for development):
- **Ruff:** `pip install ruff` — Fast Python linter/formatter
- **Black:** `pip install black` — Opinionated Python formatter

**Type Checker** (Optional, for development):
- **MyPy:** `pip install mypy` — Static type checking

### 4.4 Environment Variables & Secrets

**Required:**

**`OPENAI_API_KEY`**
- **Purpose:** Authenticate with OpenAI API
- **Format:** `sk-...` (starts with "sk-")
- **Get it:** https://platform.openai.com/api-keys
- **Set it:**
  ```bash
  export OPENAI_API_KEY=sk-your-key-here
  # Or add to .env file
  echo "OPENAI_API_KEY=sk-your-key-here" >> .env
  ```
- **Critical:** System will not start without this

**Optional:**

**`ANTHROPIC_API_KEY`**
- **Purpose:** Authenticate with Anthropic API (for Claude models, future feature)
- **Format:** `sk-ant-...`
- **Get it:** https://console.anthropic.com/
- **Set it:** `export ANTHROPIC_API_KEY=sk-ant-your-key-here`

**Model Override Variables:**
- **`DEFAULT_MANAGER_MODEL`** — Override manager model (default: gpt-4o-mini)
- **`DEFAULT_SUPERVISOR_MODEL`** — Override supervisor model (default: gpt-4o-mini)
- **`DEFAULT_EMPLOYEE_MODEL`** — Override employee model (default: gpt-4o)

**Example:**
```bash
export DEFAULT_MANAGER_MODEL=gpt-4o-mini
export DEFAULT_EMPLOYEE_MODEL=gpt-4o
```

**Cost Control Variables:**
- **`MAX_COST_USD`** — Global cost cap
- **`COST_WARNING_USD`** — Warning threshold

**Example .env file:**
```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here

# Optional
# ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Model overrides (optional)
# DEFAULT_MANAGER_MODEL=gpt-4o-mini
# DEFAULT_SUPERVISOR_MODEL=gpt-4o-mini
# DEFAULT_EMPLOYEE_MODEL=gpt-4o

# Cost controls (optional)
# MAX_COST_USD=10.0
# COST_WARNING_USD=5.0
```

### 4.5 Optional Dependencies

**For YAML Mission Files:**
```bash
pip install pyyaml
```

**For Enhanced Profiling:**
```bash
pip install psutil memory_profiler
```

**For Jupyter Notebook Support:**
```bash
pip install jupyter notebook
```
- **Purpose:** Interactive exploration of knowledge graph and analytics

**For Advanced Plotting:**
```bash
pip install matplotlib pandas
```
- **Purpose:** Visualize analytics data

**For Docker Sandbox** (future feature):
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
- **Purpose:** Maximum isolation for sandbox execution

**For GitHub CLI** (for CI/CD integration):
```bash
# Ubuntu/Debian
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# macOS
brew install gh
```

---

## Complete Installation Checklist

Use this checklist to ensure all dependencies are installed:

### Core Setup
- [ ] Python 3.9+ installed (`python --version`)
- [ ] Git installed (`git --version`)
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API key set (`echo $OPENAI_API_KEY`)
- [ ] .env file created with OPENAI_API_KEY

### Optional but Recommended
- [ ] Node.js installed (`node --version`)
- [ ] tiktoken installed (`pip install tiktoken`)
- [ ] ruff installed for linting (`pip install ruff`)
- [ ] pytest working (`pytest agent/tests_sanity/ -v`)

### Verify Installation
- [ ] Sanity tests pass (`python make.py test`)
- [ ] Web server starts (`python -m agent.webapp.app`)
- [ ] Dashboard accessible (http://127.0.0.1:8000)
- [ ] Knowledge graph DB created (`ls data/knowledge_graph.db`)

### First Run
- [ ] Create test mission file in missions/
- [ ] Run mission successfully (`python -m agent.mission_runner run missions/test.json`)
- [ ] Check generated files in sites/
- [ ] View run logs in run_logs/
- [ ] Query knowledge graph (Python REPL: `from agent import knowledge_graph`)

---

**End of Manual**

This manual covers the complete System-1.2 platform. For questions, issues, or contributions, refer to:
- DEVELOPER_GUIDE.md — Development practices
- docs/STAGE*.md — Feature-specific documentation
- GitHub Issues — Bug reports and feature requests

