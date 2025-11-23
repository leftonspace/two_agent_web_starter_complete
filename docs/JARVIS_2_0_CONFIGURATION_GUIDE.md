# JARVIS 2.0 Configuration Guide

**Version:** 2.0.0
**Date:** November 23, 2025

This guide covers all YAML-based configuration options for JARVIS 2.0, enabling non-technical users to define agents, tasks, flows, and LLM routing without writing Python code.

---

## Table of Contents

1. [Configuration File Locations](#configuration-file-locations)
2. [Agent Configuration](#agent-configuration)
3. [Task Configuration](#task-configuration)
4. [LLM Configuration](#llm-configuration)
5. [Flow Configuration](#flow-configuration)
6. [Memory Configuration](#memory-configuration)
7. [Council Configuration](#council-configuration)
8. [Pattern Configuration](#pattern-configuration)
9. [Environment Variables](#environment-variables)
10. [Configuration Validation](#configuration-validation)

---

## Configuration File Locations

```
project/
├── config/
│   ├── agents.yaml          # Agent definitions
│   ├── tasks.yaml           # Task templates
│   ├── llm_config.yaml      # LLM provider settings
│   ├── flows.yaml           # Flow definitions
│   ├── memory.yaml          # Memory system settings
│   ├── council.yaml         # Council system settings
│   └── patterns.yaml        # Orchestration patterns
└── .env                     # Environment variables (API keys)
```

---

## Agent Configuration

**File:** `config/agents.yaml`

### Schema

```yaml
# Version and metadata
version: "2.0"
metadata:
  author: "your-name"
  description: "Agent configuration for project X"
  created: "2025-11-23"

# Agent definitions
agents:
  - id: string              # Unique identifier (required)
    name: string            # Display name (required)
    role: string            # Agent role/title (required)
    goal: string            # Primary objective (required)
    backstory: string       # Context and personality (optional)
    specialization: string  # Domain expertise (optional)
    tools: list[string]     # Available tools (optional)
    llm_config:             # LLM settings (optional)
      provider: string
      model: string
      temperature: float
      max_tokens: int
    constraints:            # Behavioral constraints (optional)
      - string
    permissions:            # Access permissions (optional)
      can_execute_code: bool
      can_access_web: bool
      can_modify_files: bool
```

### Example

```yaml
version: "2.0"
metadata:
  author: "team-lead"
  description: "Development team agents"

agents:
  - id: senior_developer
    name: "Alex"
    role: "Senior Developer"
    goal: "Write clean, efficient, and well-tested code"
    backstory: |
      Alex is a senior developer with 10+ years of experience in Python,
      JavaScript, and cloud architecture. They prioritize code quality,
      maintainability, and security best practices.
    specialization: "backend"
    tools:
      - code_executor
      - file_manager
      - git_operations
      - test_runner
    llm_config:
      provider: anthropic
      model: claude-3-sonnet
      temperature: 0.3
      max_tokens: 4000
    constraints:
      - "Always write unit tests for new code"
      - "Follow PEP 8 style guidelines"
      - "Document all public functions"
    permissions:
      can_execute_code: true
      can_access_web: false
      can_modify_files: true

  - id: code_reviewer
    name: "Jordan"
    role: "Code Reviewer"
    goal: "Ensure code quality and catch potential issues"
    backstory: |
      Jordan specializes in code review with expertise in security,
      performance optimization, and design patterns.
    specialization: "review"
    tools:
      - code_analyzer
      - security_scanner
    llm_config:
      provider: anthropic
      model: claude-3-opus
      temperature: 0.2
    constraints:
      - "Provide constructive feedback"
      - "Check for security vulnerabilities"
      - "Verify test coverage"

  - id: qa_engineer
    name: "Sam"
    role: "QA Engineer"
    goal: "Ensure software quality through comprehensive testing"
    specialization: "testing"
    tools:
      - test_runner
      - load_tester
      - bug_tracker
    llm_config:
      provider: openai
      model: gpt-4-turbo
      temperature: 0.1
```

### Agent Specializations

| Specialization | Description | Typical Tasks |
|---------------|-------------|---------------|
| `coding` | Software development | Writing code, debugging |
| `review` | Code review | PR reviews, quality checks |
| `testing` | QA and testing | Writing tests, validation |
| `design` | UI/UX design | Interface design, mockups |
| `architecture` | System design | Architecture decisions |
| `documentation` | Technical writing | Docs, guides, comments |
| `devops` | Infrastructure | CI/CD, deployment |
| `research` | Investigation | Research, analysis |

---

## Task Configuration

**File:** `config/tasks.yaml`

### Schema

```yaml
version: "2.0"

tasks:
  - id: string              # Unique identifier (required)
    name: string            # Display name (required)
    description: string     # What the task does (required)
    agent_id: string        # Assigned agent (optional, can be auto-selected)
    expected_output: string # Description of expected result (required)
    tools: list[string]     # Required tools (optional)
    context: list[string]   # Task IDs for context (optional)
    dependencies: list[string]  # Tasks that must complete first (optional)
    async_execution: bool   # Run asynchronously (default: false)
    human_input: bool       # Requires human approval (default: false)
    priority: string        # low, medium, high, critical (default: medium)
    timeout_seconds: int    # Task timeout (optional)
    retry_config:           # Retry settings (optional)
      max_retries: int
      backoff_multiplier: float
```

### Example

```yaml
version: "2.0"

tasks:
  - id: analyze_requirements
    name: "Analyze Requirements"
    description: |
      Analyze the project requirements and create a detailed
      specification document with user stories and acceptance criteria.
    agent_id: senior_developer
    expected_output: |
      A structured requirements document including:
      - User stories in Given/When/Then format
      - Acceptance criteria for each story
      - Technical constraints and dependencies
    priority: high
    timeout_seconds: 300

  - id: implement_feature
    name: "Implement Feature"
    description: |
      Implement the feature based on the requirements analysis.
      Follow coding standards and include unit tests.
    agent_id: senior_developer
    expected_output: |
      - Working code implementation
      - Unit tests with >80% coverage
      - Updated documentation
    tools:
      - code_executor
      - test_runner
      - file_manager
    context:
      - analyze_requirements
    dependencies:
      - analyze_requirements
    human_input: false
    priority: high

  - id: review_code
    name: "Review Implementation"
    description: |
      Review the implemented code for quality, security,
      and adherence to best practices.
    agent_id: code_reviewer
    expected_output: |
      Code review report with:
      - Issues found (if any)
      - Suggestions for improvement
      - Security assessment
      - Approval or rejection recommendation
    context:
      - implement_feature
    dependencies:
      - implement_feature
    human_input: true  # Human reviews before deployment
    priority: high

  - id: run_tests
    name: "Execute Test Suite"
    description: "Run all tests and generate coverage report"
    agent_id: qa_engineer
    expected_output: |
      - Test execution results
      - Coverage report
      - Performance benchmarks
    dependencies:
      - implement_feature
    async_execution: true  # Can run in parallel with review
    retry_config:
      max_retries: 3
      backoff_multiplier: 2.0
```

### Task Chains and Dependencies

```yaml
# Define task chains for complex workflows
task_chains:
  - id: feature_development
    name: "Feature Development Pipeline"
    tasks:
      - analyze_requirements
      - implement_feature
      - review_code
      - run_tests
    on_failure: rollback
    notification:
      on_complete: slack
      on_failure: email

  - id: hotfix_pipeline
    name: "Hotfix Pipeline"
    tasks:
      - implement_fix
      - quick_review
      - deploy_staging
    priority: critical
    timeout_seconds: 1800  # 30 minutes total
```

---

## LLM Configuration

**File:** `config/llm_config.yaml`

### Schema

```yaml
version: "2.0"

# Default settings
defaults:
  provider: string
  model: string
  temperature: float
  max_tokens: int
  timeout_seconds: int

# Provider configurations
providers:
  provider_name:
    enabled: bool
    api_key_env: string     # Environment variable name
    base_url: string        # Optional custom endpoint
    models:
      model_name:
        max_tokens: int
        cost_per_1k_input: float
        cost_per_1k_output: float
        supports_vision: bool
        supports_functions: bool
    rate_limits:
      requests_per_minute: int
      tokens_per_minute: int
    retry_config:
      max_retries: int
      base_delay: float
      max_delay: float

# Routing rules
routing:
  cost_optimization: bool
  failover_enabled: bool
  rules:
    - condition: string
      provider: string
      model: string
```

### Example

```yaml
version: "2.0"

defaults:
  provider: anthropic
  model: claude-3-sonnet
  temperature: 0.7
  max_tokens: 4096
  timeout_seconds: 60

providers:
  anthropic:
    enabled: true
    api_key_env: ANTHROPIC_API_KEY
    models:
      claude-3-opus:
        max_tokens: 4096
        cost_per_1k_input: 0.015
        cost_per_1k_output: 0.075
        supports_vision: true
        supports_functions: true
      claude-3-sonnet:
        max_tokens: 4096
        cost_per_1k_input: 0.003
        cost_per_1k_output: 0.015
        supports_vision: true
        supports_functions: true
      claude-3-haiku:
        max_tokens: 4096
        cost_per_1k_input: 0.00025
        cost_per_1k_output: 0.00125
        supports_vision: true
        supports_functions: true
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 100000
    retry_config:
      max_retries: 3
      base_delay: 1.0
      max_delay: 60.0

  openai:
    enabled: true
    api_key_env: OPENAI_API_KEY
    models:
      gpt-4-turbo:
        max_tokens: 128000
        cost_per_1k_input: 0.01
        cost_per_1k_output: 0.03
        supports_vision: true
        supports_functions: true
      gpt-4:
        max_tokens: 8192
        cost_per_1k_input: 0.03
        cost_per_1k_output: 0.06
      gpt-3.5-turbo:
        max_tokens: 16385
        cost_per_1k_input: 0.0005
        cost_per_1k_output: 0.0015
    rate_limits:
      requests_per_minute: 60
      tokens_per_minute: 90000

  deepseek:
    enabled: true
    api_key_env: DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/v1
    models:
      deepseek-coder:
        max_tokens: 16384
        cost_per_1k_input: 0.0002
        cost_per_1k_output: 0.0002
      deepseek-chat:
        max_tokens: 32768
        cost_per_1k_input: 0.0001
        cost_per_1k_output: 0.0002
    rate_limits:
      requests_per_minute: 60

  ollama:
    enabled: true
    base_url: http://localhost:11434
    models:
      llama2:
        max_tokens: 4096
        cost_per_1k_input: 0  # Local, no cost
        cost_per_1k_output: 0
      codellama:
        max_tokens: 16384
        cost_per_1k_input: 0
        cost_per_1k_output: 0
      mistral:
        max_tokens: 8192
        cost_per_1k_input: 0
        cost_per_1k_output: 0

  qwen:
    enabled: false  # Enable when needed
    api_key_env: QWEN_API_KEY
    base_url: https://dashscope.aliyuncs.com/api/v1
    models:
      qwen-turbo:
        max_tokens: 8000
        cost_per_1k_input: 0.001
        cost_per_1k_output: 0.002

# Intelligent routing
routing:
  cost_optimization: true
  failover_enabled: true
  rules:
    # Use cheaper models for simple tasks
    - condition: "task.complexity == 'simple'"
      provider: anthropic
      model: claude-3-haiku

    # Use powerful models for complex reasoning
    - condition: "task.complexity == 'complex'"
      provider: anthropic
      model: claude-3-opus

    # Use local models for development
    - condition: "environment == 'development'"
      provider: ollama
      model: codellama

    # Use specialized coding model for code tasks
    - condition: "task.type == 'coding'"
      provider: deepseek
      model: deepseek-coder

    # Failover chain
    - condition: "provider.anthropic.unavailable"
      provider: openai
      model: gpt-4-turbo
```

---

## Flow Configuration

**File:** `config/flows.yaml`

### Schema

```yaml
version: "2.0"

flows:
  - id: string
    name: string
    description: string
    initial_state:
      key: value
    steps:
      - id: string
        type: start | task | router | end
        task_id: string         # For task steps
        condition: string       # For router steps
        next: string | object   # Next step or routing map
    on_error: retry | skip | abort
    timeout_seconds: int
```

### Example

```yaml
version: "2.0"

flows:
  - id: feature_development
    name: "Feature Development Flow"
    description: "Complete flow for developing a new feature"
    initial_state:
      feature_name: ""
      requirements: []
      code_path: ""
      status: "pending"

    steps:
      - id: start
        type: start
        next: check_complexity

      - id: check_complexity
        type: router
        condition: |
          if len(state.requirements) > 5:
            return "complex_path"
          return "simple_path"
        next:
          complex_path: clarify_requirements
          simple_path: implement

      - id: clarify_requirements
        type: task
        task_id: analyze_requirements
        next: implement

      - id: implement
        type: task
        task_id: implement_feature
        next: review_decision

      - id: review_decision
        type: router
        condition: |
          if state.priority == "critical":
            return "human_review"
          return "auto_review"
        next:
          human_review: human_approval
          auto_review: automated_review

      - id: human_approval
        type: task
        task_id: human_review_task
        human_input: true
        next: check_approval

      - id: automated_review
        type: task
        task_id: review_code
        next: check_approval

      - id: check_approval
        type: router
        condition: |
          if state.review_result == "approved":
            return "deploy"
          return "revise"
        next:
          deploy: run_tests
          revise: implement

      - id: run_tests
        type: task
        task_id: run_tests
        next: complete

      - id: complete
        type: end

    on_error: retry
    timeout_seconds: 3600

  - id: quick_fix
    name: "Quick Fix Flow"
    description: "Streamlined flow for small fixes"
    steps:
      - id: start
        type: start
        next: fix

      - id: fix
        type: task
        task_id: implement_fix
        next: test

      - id: test
        type: task
        task_id: quick_test
        next: complete

      - id: complete
        type: end

    timeout_seconds: 900  # 15 minutes
```

---

## Memory Configuration

**File:** `config/memory.yaml`

### Schema

```yaml
version: "2.0"

memory:
  short_term:
    enabled: bool
    max_tokens: int
    relevance_threshold: float
    compression_enabled: bool
    embedding_model: string

  long_term:
    enabled: bool
    storage_type: sqlite | postgresql | redis
    storage_path: string
    connection_string: string
    embedding_model: string
    chunk_size: int
    retention_days: int

  entity:
    enabled: bool
    storage_type: neo4j | networkx | sqlite
    connection_string: string
    max_entities: int
    relationship_types: list[string]

  context:
    enabled: bool
    window_size: int
    include_system_context: bool
```

### Example

```yaml
version: "2.0"

memory:
  short_term:
    enabled: true
    max_tokens: 8000
    relevance_threshold: 0.65
    compression_enabled: true
    embedding_model: text-embedding-3-small

  long_term:
    enabled: true
    storage_type: sqlite
    storage_path: ./data/memory.db
    embedding_model: text-embedding-3-small
    chunk_size: 500
    retention_days: 90  # Keep memories for 90 days

  entity:
    enabled: true
    storage_type: networkx  # In-memory graph
    max_entities: 10000
    relationship_types:
      - works_on
      - depends_on
      - created_by
      - modified_by
      - related_to
      - part_of

  context:
    enabled: true
    window_size: 10  # Last 10 messages
    include_system_context: true
```

---

## Council Configuration

**File:** `config/council.yaml`

### Schema

```yaml
version: "2.0"

council:
  enabled: bool
  min_councillors: int
  max_councillors: int

  voting:
    quorum_percentage: float
    decision_threshold: float
    timeout_seconds: int

  happiness:
    initial_value: int
    min_value: int
    max_value: int
    decay_rate: float
    events:
      event_name: int  # Impact value

  performance:
    evaluation_interval: int
    fire_threshold: float
    promote_threshold: float
    consecutive_failures_limit: int

  specializations:
    - name: string
      weight: float
      required_count: int
```

### Example

```yaml
version: "2.0"

council:
  enabled: true
  min_councillors: 3
  max_councillors: 10

  voting:
    quorum_percentage: 0.6    # 60% must vote
    decision_threshold: 0.5   # Simple majority
    timeout_seconds: 30

  happiness:
    initial_value: 70
    min_value: 0
    max_value: 100
    decay_rate: 0.02  # 2% daily decay
    events:
      task_success: 5
      task_failure: -8
      bonus_received: 15
      criticism: -10
      praise: 8
      overworked: -12
      vote_won: 3
      vote_ignored: -5
      colleague_fired: -8
      new_colleague: 2
      vacation: 20

  performance:
    evaluation_interval: 86400  # Daily
    fire_threshold: 0.4         # Fire if < 40%
    promote_threshold: 0.8      # Promote if > 80%
    consecutive_failures_limit: 5
    probation_tasks: 10         # Tasks before full status

  specializations:
    - name: coding
      weight: 1.5
      required_count: 2
    - name: review
      weight: 1.2
      required_count: 1
    - name: testing
      weight: 1.0
      required_count: 1
    - name: architecture
      weight: 1.3
      required_count: 1
    - name: documentation
      weight: 0.8
      required_count: 1
```

---

## Pattern Configuration

**File:** `config/patterns.yaml`

### Schema

```yaml
version: "2.0"

patterns:
  default: string  # Default pattern to use

  definitions:
    pattern_name:
      enabled: bool
      config:
        max_rounds: int
        allow_repeat: bool
        # Pattern-specific config

  auto_selection:
    enabled: bool
    rules:
      - condition: string
        pattern: string
```

### Example

```yaml
version: "2.0"

patterns:
  default: auto_select

  definitions:
    sequential:
      enabled: true
      config:
        max_rounds: 3
        allow_repeat: false

    hierarchical:
      enabled: true
      config:
        max_rounds: 5
        hierarchy_levels:
          - manager
          - supervisor
          - worker
        escalation_enabled: true

    auto_select:
      enabled: true
      config:
        max_rounds: 10
        selection_model: claude-3-haiku
        confidence_threshold: 0.7

    round_robin:
      enabled: true
      config:
        max_rounds: 5
        skip_on_no_contribution: true

    manual:
      enabled: true
      config:
        prompt_timeout_seconds: 300
        default_on_timeout: sequential

  auto_selection:
    enabled: true
    rules:
      - condition: "task.type == 'review'"
        pattern: round_robin
      - condition: "task.complexity == 'simple'"
        pattern: sequential
      - condition: "task.complexity == 'complex'"
        pattern: hierarchical
      - condition: "task.priority == 'critical'"
        pattern: manual
      - condition: "default"
        pattern: auto_select
```

---

## Environment Variables

**File:** `.env`

```bash
# LLM Provider API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=...
QWEN_API_KEY=...

# Database connections
DATABASE_URL=postgresql://user:pass@localhost:5432/jarvis
REDIS_URL=redis://localhost:6379/0
NEO4J_URL=bolt://localhost:7687

# Memory storage
MEMORY_STORAGE_PATH=./data/memory
EMBEDDING_CACHE_PATH=./data/embeddings

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key

# Feature flags
ENABLE_COUNCIL=true
ENABLE_MEMORY=true
ENABLE_FLOWS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance
MAX_CONCURRENT_TASKS=10
CACHE_TTL_SECONDS=3600
```

---

## Configuration Validation

JARVIS 2.0 validates all configuration files on startup. Use the CLI to validate:

```bash
# Validate all configs
python -m agent.config validate

# Validate specific file
python -m agent.config validate --file config/agents.yaml

# Show config schema
python -m agent.config schema --component agents
```

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `MissingRequiredField` | Required field not provided | Add the missing field |
| `InvalidType` | Wrong data type | Check schema for correct type |
| `UnknownAgent` | Referenced agent doesn't exist | Define agent first |
| `CircularDependency` | Tasks depend on each other | Fix dependency chain |
| `InvalidProvider` | LLM provider not configured | Enable provider in config |

---

*Configuration Guide - JARVIS 2.0*
