# JARVIS 2.0 Configuration Quick Reference

**Version:** 2.0.0
**Date:** November 23, 2025

Quick reference for all configuration options with copy-paste examples.

---

## Configuration Files Overview

```
config/
├── agents.yaml       # Agent definitions
├── tasks.yaml        # Task templates
├── llm_config.yaml   # LLM providers and routing
├── flows.yaml        # Workflow definitions
├── memory.yaml       # Memory system settings
├── council.yaml      # Council/voting system
└── patterns.yaml     # Orchestration patterns
```

---

## Environment Variables (.env)

```bash
# =============================================================================
# REQUIRED: API Keys
# =============================================================================
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# =============================================================================
# OPTIONAL: Additional Providers
# =============================================================================
DEEPSEEK_API_KEY=sk-...
QWEN_API_KEY=...
ELEVENLABS_API_KEY=...

# =============================================================================
# Database
# =============================================================================
DATABASE_URL=sqlite:///data/jarvis.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/jarvis

# =============================================================================
# Security
# =============================================================================
SECRET_KEY=your-32-character-secret-key-here
JWT_EXPIRATION_HOURS=24

# =============================================================================
# Features (true/false)
# =============================================================================
ENABLE_COUNCIL=true
ENABLE_MEMORY=true
ENABLE_FLOWS=true
ENABLE_VOICE=false
ENABLE_VISION=true

# =============================================================================
# Logging
# =============================================================================
LOG_LEVEL=INFO                # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json               # json or text
LOG_FILE=logs/jarvis.log

# =============================================================================
# Performance
# =============================================================================
MAX_CONCURRENT_TASKS=10
CACHE_TTL_SECONDS=3600
CONNECTION_POOL_SIZE=10

# =============================================================================
# Voice System (optional)
# =============================================================================
VOICE_ID=your-elevenlabs-voice-id
VOICE_STABILITY=0.5
VOICE_SIMILARITY=0.75

# =============================================================================
# Development
# =============================================================================
DEBUG=false
PYTHONASYNCIODEBUG=0
```

---

## agents.yaml - Complete Example

```yaml
version: "2.0"
metadata:
  author: "your-name"
  description: "Team agent configuration"
  created: "2025-11-23"

agents:
  # Senior Developer Agent
  - id: senior_dev
    name: "Alex"
    role: "Senior Developer"
    goal: "Write clean, efficient, well-tested code"
    backstory: |
      Alex is a senior developer with 10+ years of experience in Python,
      JavaScript, and cloud architecture. They prioritize code quality,
      maintainability, and security best practices.
    specialization: coding
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
      - "Always write unit tests"
      - "Follow PEP 8 style guidelines"
      - "Document all public functions"
    permissions:
      can_execute_code: true
      can_access_web: false
      can_modify_files: true

  # Code Reviewer Agent
  - id: reviewer
    name: "Jordan"
    role: "Code Reviewer"
    goal: "Ensure code quality and catch potential issues"
    backstory: |
      Jordan specializes in code review with expertise in security,
      performance optimization, and design patterns.
    specialization: review
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

  # QA Engineer Agent
  - id: qa_engineer
    name: "Sam"
    role: "QA Engineer"
    goal: "Comprehensive testing and quality assurance"
    specialization: testing
    tools:
      - test_runner
      - load_tester
    llm_config:
      provider: openai
      model: gpt-4-turbo
      temperature: 0.1

  # Documentation Writer Agent
  - id: doc_writer
    name: "Morgan"
    role: "Technical Writer"
    goal: "Create clear, helpful documentation"
    specialization: documentation
    tools:
      - file_manager
      - markdown_formatter
    llm_config:
      provider: anthropic
      model: claude-3-haiku
      temperature: 0.5
```

### Agent Specializations

| Value | Description |
|-------|-------------|
| `coding` | Software development |
| `review` | Code review |
| `testing` | QA and testing |
| `design` | UI/UX design |
| `architecture` | System design |
| `documentation` | Technical writing |
| `devops` | Infrastructure |
| `research` | Investigation |

---

## tasks.yaml - Complete Example

```yaml
version: "2.0"

tasks:
  # Requirements Analysis Task
  - id: analyze_requirements
    name: "Analyze Requirements"
    description: |
      Analyze project requirements and create a detailed
      specification with user stories and acceptance criteria.
    agent_id: senior_dev
    expected_output: |
      Structured requirements document with:
      - User stories (Given/When/Then)
      - Acceptance criteria
      - Technical constraints
    priority: high
    timeout_seconds: 300

  # Implementation Task
  - id: implement_feature
    name: "Implement Feature"
    description: |
      Implement the feature based on requirements.
      Include unit tests and documentation.
    agent_id: senior_dev
    expected_output: |
      - Working code
      - Unit tests (>80% coverage)
      - Updated docs
    tools:
      - code_executor
      - test_runner
    context:
      - analyze_requirements
    dependencies:
      - analyze_requirements
    priority: high
    human_input: false

  # Code Review Task
  - id: review_code
    name: "Code Review"
    description: "Review implementation for quality and security"
    agent_id: reviewer
    expected_output: |
      Review report with:
      - Issues found
      - Suggestions
      - Security assessment
      - Approval/rejection
    dependencies:
      - implement_feature
    human_input: true
    priority: high

  # Testing Task
  - id: run_tests
    name: "Run Tests"
    description: "Execute test suite and generate coverage"
    agent_id: qa_engineer
    expected_output: |
      - Test results
      - Coverage report
      - Performance metrics
    dependencies:
      - implement_feature
    async_execution: true
    retry_config:
      max_retries: 3
      backoff_multiplier: 2.0

# Task Chains
task_chains:
  - id: feature_pipeline
    name: "Feature Development Pipeline"
    tasks:
      - analyze_requirements
      - implement_feature
      - review_code
      - run_tests
    on_failure: rollback
```

### Task Priority Values

| Value | Description |
|-------|-------------|
| `low` | Background task |
| `medium` | Normal priority (default) |
| `high` | Expedited processing |
| `critical` | Immediate attention |

---

## llm_config.yaml - Complete Example

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

  ollama:
    enabled: false  # Enable for local models
    base_url: http://localhost:11434
    models:
      llama2:
        max_tokens: 4096
        cost_per_1k_input: 0
        cost_per_1k_output: 0
      codellama:
        max_tokens: 16384
        cost_per_1k_input: 0
        cost_per_1k_output: 0

# Intelligent routing rules
routing:
  cost_optimization: true
  failover_enabled: true
  rules:
    # Simple tasks use cheaper models
    - condition: "task.complexity == 'simple'"
      provider: anthropic
      model: claude-3-haiku

    # Complex reasoning uses best models
    - condition: "task.complexity == 'complex'"
      provider: anthropic
      model: claude-3-opus

    # Coding tasks use specialized model
    - condition: "task.type == 'coding'"
      provider: deepseek
      model: deepseek-coder

    # Development uses local models
    - condition: "environment == 'development'"
      provider: ollama
      model: codellama

    # Failover chain
    - condition: "provider.anthropic.unavailable"
      provider: openai
      model: gpt-4-turbo
```

---

## memory.yaml - Complete Example

```yaml
version: "2.0"

memory:
  # Short-term memory (RAG-based)
  short_term:
    enabled: true
    max_tokens: 8000
    relevance_threshold: 0.65
    compression_enabled: true
    embedding_model: text-embedding-3-small

  # Long-term memory (persistent)
  long_term:
    enabled: true
    storage_type: sqlite
    storage_path: ./data/memory.db
    embedding_model: text-embedding-3-small
    chunk_size: 500
    retention_days: 90

  # Entity memory (knowledge graph)
  entity:
    enabled: true
    storage_type: networkx  # or neo4j
    max_entities: 10000
    relationship_types:
      - works_on
      - depends_on
      - created_by
      - modified_by
      - related_to
      - part_of

  # Context window
  context:
    enabled: true
    window_size: 10
    include_system_context: true
```

---

## council.yaml - Complete Example

```yaml
version: "2.0"

council:
  enabled: true
  min_councillors: 3
  max_councillors: 10

  # Voting configuration
  voting:
    quorum_percentage: 0.6
    decision_threshold: 0.5
    timeout_seconds: 30

  # Happiness system
  happiness:
    initial_value: 70
    min_value: 0
    max_value: 100
    decay_rate: 0.02
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

  # Performance evaluation
  performance:
    evaluation_interval: 86400
    fire_threshold: 0.4
    promote_threshold: 0.8
    consecutive_failures_limit: 5
    probation_tasks: 10

  # Specialization weights
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

## patterns.yaml - Complete Example

```yaml
version: "2.0"

patterns:
  default: auto_select

  definitions:
    # Linear execution
    sequential:
      enabled: true
      config:
        max_rounds: 3
        allow_repeat: false

    # Manager → Supervisor → Worker
    hierarchical:
      enabled: true
      config:
        max_rounds: 5
        hierarchy_levels:
          - manager
          - supervisor
          - worker
        escalation_enabled: true

    # LLM-driven selection
    auto_select:
      enabled: true
      config:
        max_rounds: 10
        selection_model: claude-3-haiku
        confidence_threshold: 0.7

    # Rotating through agents
    round_robin:
      enabled: true
      config:
        max_rounds: 5
        skip_on_no_contribution: true

    # Human selects agent
    manual:
      enabled: true
      config:
        prompt_timeout_seconds: 300
        default_on_timeout: sequential

  # Auto-select pattern based on task
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

## flows.yaml - Complete Example

```yaml
version: "2.0"

flows:
  # Feature development flow
  - id: feature_development
    name: "Feature Development Flow"
    description: "End-to-end feature development"
    initial_state:
      feature_name: ""
      requirements: []
      status: pending

    steps:
      - id: start
        type: start
        next: check_complexity

      - id: check_complexity
        type: router
        condition: |
          if len(state.requirements) > 5:
            return "complex"
          return "simple"
        next:
          complex: clarify_requirements
          simple: implement

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
            return "human"
          return "auto"
        next:
          human: human_review
          auto: auto_review

      - id: human_review
        type: task
        task_id: human_review_task
        human_input: true
        next: check_approval

      - id: auto_review
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

  # Quick fix flow
  - id: quick_fix
    name: "Quick Fix Flow"
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

    timeout_seconds: 900
```

---

## Validation Commands

```bash
# Validate all configuration
python -m agent.config validate

# Validate specific file
python -m agent.config validate --file config/agents.yaml

# Show schema for a component
python -m agent.config schema --component agents

# Export current config
python -m agent.config export > backup.yaml

# Test LLM configuration
python -m agent.llm test
```

---

## Minimal Startup Configuration

Fastest way to get started:

**.env**
```bash
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=your-secret-key
```

**config/agents.yaml**
```yaml
version: "2.0"
agents:
  - id: assistant
    name: "Assistant"
    role: "General Assistant"
    goal: "Help users with tasks"
```

**config/llm_config.yaml**
```yaml
version: "2.0"
defaults:
  provider: anthropic
  model: claude-3-sonnet
```

Then run:
```bash
python -m agent.webapp.app
```

---

*Configuration Quick Reference - JARVIS 2.0*
