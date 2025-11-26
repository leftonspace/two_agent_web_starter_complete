# JARVIS Implementation Roadmap V3
## Self-Evolving Multi-Domain Business AI Platform

**Document Version:** 3.0.0  
**Status:** Final Implementation Plan  
**Date:** 2025-11-25  
**Philosophy:** Build fast, iterate based on real usage, keep it simple

---

## Table of Contents

1. [Vision Statement](#vision-statement)
2. [Architecture Overview](#architecture-overview)
3. [Hardware Infrastructure](#hardware-infrastructure)
4. [Phase 7: Security Foundation](#phase-7-security-foundation)
5. [Phase 8: Model Routing & Cost Control](#phase-8-model-routing--cost-control)
6. [Phase 9: Specialist System](#phase-9-specialist-system)
7. [Phase 10: Evaluation System (Toggle-Based)](#phase-10-evaluation-system-toggle-based)
8. [Phase 11: Graveyard & Evolution](#phase-11-graveyard--evolution)
9. [Phase 12: Domain Routing](#phase-12-domain-routing)
10. [Phase 13: Benchmark Mode](#phase-13-benchmark-mode)
11. [Phase 14: Dashboard & Analytics](#phase-14-dashboard--analytics)
12. [File Index](#file-index)
13. [Database Schema](#database-schema)
14. [Implementation Timeline](#implementation-timeline)

---

## Vision Statement

JARVIS is a **business automation platform** that:

1. **Handles 70-80% of routine business tasks** with decreasing supervision over time
2. **Maintains context about YOUR business** (the real competitive advantage)
3. **Improves through evolution** - underperformers culled, learnings transferred
4. **Adapts model selection** based on task complexity (save costs on simple tasks)
5. **"JARVIS" is just the best administration specialist** - no special code, same evolution as everyone

**Business Model:** You sell automation services. Clients never know JARVIS exists. You're the AI-powered contractor.

**Core Insight:** Claude/GPT-5 will always be smarter. Your advantage is business context + specialization + control.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              JARVIS PLATFORM                                    │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                    ADMINISTRATION DOMAIN                                  │ │
│  │              (Best specialist = "JARVIS" personality)                     │ │
│  │                                                                           │ │
│  │  Responsibilities:                                                        │ │
│  │  • Understand user intent                                                 │ │
│  │  • Ask clarifying questions                                               │ │
│  │  • Route to appropriate domain                                            │ │
│  │  • Communicate results                                                    │ │
│  │  • Be the "face" of the system                                           │ │
│  │                                                                           │ │
│  │  [Admin_1: 0.89] ← Current "JARVIS"                                      │ │
│  │  [Admin_2: 0.86]                                                         │ │
│  │  [Admin_3: 0.84]                                                         │ │
│  │                                                                           │ │
│  │  When Admin_2 overtakes Admin_1 → seamless JARVIS upgrade                │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                           │
│                                     ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                         SECURITY LAYER                                    │ │
│  │         OS Sandbox │ Network Proxy │ Output Guardrails                    │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                           │
│                                     ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                          MODEL ROUTER                                     │ │
│  │                                                                           │ │
│  │   Complexity:  TRIVIAL ──→ Haiku ($0.25/1M)                              │ │
│  │                LOW ─────→ Haiku ($0.25/1M)                               │ │
│  │                MEDIUM ──→ Sonnet ($3/1M)                                 │ │
│  │                HIGH ────→ Sonnet ($3/1M)                                 │ │
│  │                CRITICAL → Opus ($15/1M)                                  │ │
│  │                                                                           │ │
│  │   Budget: Daily $X │ Weekly $Y │ Monthly $Z                              │ │
│  │   Local LLM: [Disabled] ← Enable when hardware available                 │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                           │
│          ┌──────────────────────────┼──────────────────────────┐               │
│          ▼                          ▼                          ▼               │
│   ┌─────────────┐           ┌─────────────┐           ┌─────────────┐         │
│   │    CODE     │           │  BUSINESS   │           │   DOMAIN    │         │
│   │ GENERATION  │           │  DOCUMENTS  │           │     N       │         │
│   │             │           │             │           │ (Extensible)│         │
│   │ [1] [2] [3] │           │ [1] [2] [3] │           │ [1] [2] [3] │         │
│   └─────────────┘           └─────────────┘           └─────────────┘         │
│          │                          │                          │               │
│          └──────────────────────────┼──────────────────────────┘               │
│                                     ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                    EVALUATION SYSTEM (Toggle)                             │ │
│  │                                                                           │ │
│  │   Dashboard Setting:                                                      │ │
│  │   ┌─────────────────────────────────────────────────────────────────┐    │ │
│  │   │  ● Scoring Committee (Default)                                  │    │ │
│  │   │    Tests + Linter + Your Feedback                               │    │ │
│  │   │                                                                 │    │ │
│  │   │  ○ AI Council                                                   │    │ │
│  │   │    Top-3 Specialists Vote                                       │    │ │
│  │   │                                                                 │    │ │
│  │   │  ○ Both (Comparison Mode)                                       │    │ │
│  │   │    See how they differ                                          │    │ │
│  │   └─────────────────────────────────────────────────────────────────┘    │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                           │
│                                     ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                      GRAVEYARD + EVOLUTION                                │ │
│  │                                                                           │ │
│  │   Cull: Specialists below threshold or bottom performer                   │ │
│  │   Learn: Extract failure patterns → inject into new specialists          │ │
│  │   Plateau: Pause when variance < 2% AND no improvement for 10 gens       │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                     │                                           │
│                                     ▼                                           │ │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                        BENCHMARK MODE                                     │ │
│  │                                                                           │ │
│  │   You: Ask Claude to generate test prompts → Save to /benchmarks/        │ │
│  │   JARVIS: Execute benchmarks → Record scores → Feed into evolution       │ │
│  │                                                                           │ │
│  │   Controls:                                                               │ │
│  │   [▶ Run All] [▶ Run Domain] [⏸ Pause] Budget: $5/day cap               │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Hardware Infrastructure

### Current State: API Only

You're starting with API only. This section documents the upgrade path when ready.

### Build Comparison: $5k vs $10k

#### Specifications

| Component | $5k Build | $10k Build (Recommended) |
|-----------|-----------|--------------------------|
| **GPU** | 1x RTX 4090 24GB | 2x RTX 4090 24GB (undervolted) |
| **Total VRAM** | 24GB | 48GB |
| **CPU** | Ryzen 9 7950X | Threadripper 7960X |
| **RAM** | 64GB DDR5 | 128GB DDR5 ECC |
| **Storage** | 3TB NVMe | 6TB NVMe |
| **Power (typical)** | 350-450W | 350-550W (undervolted) |
| **Noise** | Moderate | Quiet (premium cooling) |
| **Upgrade Path** | Limited | 4 GPU slots available |

#### Performance for JARVIS Tasks

| Task Type | $5k Build | $10k Build | API (Sonnet) |
|-----------|-----------|------------|--------------|
| Simple scripts | 85% quality, 3s | 90% quality, 2s | 95% quality, 2s |
| Medium modules | 70% quality, 15s | 82% quality, 10s | 90% quality, 8s |
| Complex systems | 50% quality, 45s | 65% quality, 30s | 85% quality, 20s |
| Benchmark execution | 1 at a time | 2 parallel | Fast but costs money |

*Quality = percentage requiring no human correction*

#### Monthly Operating Costs

| Usage | API Only | $5k Build | $10k Build |
|-------|----------|-----------|------------|
| Light (20 tasks/day) | $100 | $42 | $29 |
| Medium (50 tasks/day) | $250 | $105 | $63 |
| Heavy (100 tasks/day) | $500 | $210 | $124 |
| + Benchmark mode | +$150 | +$30 | +$8 |

#### Recommendation

| Situation | Recommendation |
|-----------|----------------|
| Testing JARVIS (months 1-3) | API Only |
| Confirmed value, budget matters | $5k Build |
| Serious long-term, want quality | $10k Build |
| Planning to scale | $10k Build (upgradeable) |

#### $10k Build Undervolting Benefits

| Metric | Stock | Undervolted |
|--------|-------|-------------|
| Power draw (2 GPUs) | 900W | 460W |
| Performance loss | 0% | 5-8% for inference |
| Heat output | Space heater | Manageable |
| Noise | Loud | Quiet |
| Can your outlet handle it? | Maybe not | Yes |

---

## Phase 7: Security Foundation

**Priority:** P0  
**Effort:** 2-3 weeks  
**Dependencies:** None

### Phase 7.1: OS-Level Sandboxing

#### Files to Create

| File | Purpose |
|------|---------|
| `core/security/sandbox.py` | OS sandbox wrapper (bubblewrap/seatbelt) |
| `core/security/network_proxy.py` | Domain allowlist proxy |
| `core/security/sandbox_profiles.py` | Pre-defined profiles per domain |
| `config/security/sandbox.yaml` | Sandbox configuration |
| `tests/security/test_sandbox.py` | Sandbox tests |

#### Implementation

**sandbox.py structure:**
```python
class Sandbox:
    """
    OS-level isolation for code execution.
    
    Methods:
    - execute(cmd: str, profile: str) -> ExecutionResult
    - validate_path(path: str) -> bool
    
    Profiles:
    - code_generation: /workspace, /tmp, network to github/pypi/npm
    - business_documents: /workspace, /tmp, no network
    - benchmark: /workspace, /tmp, no network
    """
```

**sandbox_profiles.py:**
```python
PROFILES = {
    "code_generation": {
        "allowed_paths": ["/jarvis/workspace", "/tmp"],
        "allowed_domains": ["github.com", "pypi.org", "npmjs.org"],
        "max_memory_mb": 4096,
        "max_time_seconds": 300,
    },
    "business_documents": {
        "allowed_paths": ["/jarvis/workspace", "/tmp"],
        "allowed_domains": [],
        "max_memory_mb": 2048,
        "max_time_seconds": 120,
    },
    "benchmark": {
        "allowed_paths": ["/jarvis/workspace", "/tmp"],
        "allowed_domains": [],
        "max_memory_mb": 4096,
        "max_time_seconds": 600,
    },
}
```

#### Tests

```bash
test_filesystem_isolation()
    # Cannot access /etc/passwd
    # Cannot write outside allowed paths

test_network_isolation()
    # Blocked domains rejected
    # Allowed domains work

test_resource_limits()
    # Process killed at memory limit
    # Process killed at time limit
```

---

### Phase 7.2: Output Guardrails

#### Files to Create

| File | Purpose |
|------|---------|
| `core/security/output_guardrails.py` | Validate outputs before returning |
| `core/security/pii_detector.py` | Detect PII in outputs |
| `core/security/anomaly_detector.py` | Detect corrupted outputs |
| `tests/security/test_guardrails.py` | Guardrail tests |

#### Implementation

**output_guardrails.py structure:**
```python
class OutputGuardrails:
    """
    Validate outputs before returning to user.
    
    Checks:
    - PII exposure (SSN, credit cards, etc.)
    - Character anomalies (wrong script in output)
    - Prompt leakage (system prompt in output)
    
    Methods:
    - validate(output: str, context: Context) -> ValidationResult
    - sanitize(output: str, failures: List[Failure]) -> str
    """
```

#### Tests

```bash
test_pii_detection()
    # SSN detected and flagged
    # Credit card detected and flagged

test_anomaly_detection()
    # Thai characters in English output flagged
    # Normal unicode NOT flagged
```

---

## Phase 8: Model Routing & Cost Control

**Priority:** P0  
**Effort:** 2 weeks  
**Dependencies:** Phase 7

### Phase 8.1: Provider Abstraction

#### Files to Create

| File | Purpose |
|------|---------|
| `core/models/provider.py` | Abstract provider interface |
| `core/models/anthropic_provider.py` | Claude API provider |
| `core/models/local_provider.py` | Ollama/vLLM provider (for future) |
| `config/models/providers.yaml` | Provider configuration |
| `tests/models/test_providers.py` | Provider tests |

#### Implementation

**provider.py structure:**
```python
class ModelProvider(ABC):
    """
    Abstract base for all model providers.
    
    Attributes:
    - name: str
    - is_local: bool
    - cost_per_1k_input: float
    - cost_per_1k_output: float
    
    Methods:
    - complete(messages: List[Message], model: str) -> Completion
    - estimate_cost(messages: List[Message]) -> float
    - is_available() -> bool
    """
```

**providers.yaml:**
```yaml
providers:
  anthropic:
    enabled: true
    api_key_env: "ANTHROPIC_API_KEY"
    models:
      haiku:
        name: "claude-haiku-4-5-20251001"
        cost_per_1k_input: 0.00025
        cost_per_1k_output: 0.00125
        tier: "low"
      sonnet:
        name: "claude-sonnet-4-5-20250929"
        cost_per_1k_input: 0.003
        cost_per_1k_output: 0.015
        tier: "high"
      opus:
        name: "claude-opus-4-5-20251101"
        cost_per_1k_input: 0.015
        cost_per_1k_output: 0.075
        tier: "highest"
  
  local:
    enabled: false  # Enable when hardware ready
    backend: "ollama"
    models:
      llama70b:
        name: "llama3.1:70b-instruct-q4_K_M"
        cost_per_1k_input: 0.0
        cost_per_1k_output: 0.0
        tier: "medium"
```

---

### Phase 8.2: Complexity Router

#### Files to Create

| File | Purpose |
|------|---------|
| `core/models/complexity.py` | Assess task complexity |
| `core/models/router.py` | Route to appropriate model |
| `config/models/routing.yaml` | Routing rules |
| `tests/models/test_router.py` | Router tests |

#### Implementation

**complexity.py structure:**
```python
class ComplexityLevel(Enum):
    TRIVIAL = "trivial"   # Simple lookup, formatting
    LOW = "low"           # Basic code, templates
    MEDIUM = "medium"     # Multi-step reasoning
    HIGH = "high"         # Complex architecture
    CRITICAL = "critical" # Highest stakes

class ComplexityAssessor:
    """
    Assess task complexity.
    
    Factors:
    - Token count
    - Domain
    - Multi-step required
    - Historical failure rate
    - Financial impact
    
    Methods:
    - assess(request: Request) -> ComplexityLevel
    """
```

**router.py structure:**
```python
class ModelRouter:
    """
    Route requests to appropriate model.
    
    Default routing (API only):
    - TRIVIAL → haiku
    - LOW → haiku
    - MEDIUM → sonnet
    - HIGH → sonnet
    - CRITICAL → opus
    
    With local available:
    - TRIVIAL → local
    - LOW → local
    - MEDIUM → local (70B) or sonnet
    - HIGH → sonnet
    - CRITICAL → opus
    
    Methods:
    - route(request: Request) -> ModelSelection
    - apply_budget_constraints(selection: ModelSelection) -> ModelSelection
    """
```

**routing.yaml:**
```yaml
routing:
  api_only:
    trivial: "haiku"
    low: "haiku"
    medium: "sonnet"
    high: "sonnet"
    critical: "opus"
  
  with_local:
    trivial: "local:llama8b"
    low: "local:llama8b"
    medium: "local:llama70b"
    high: "sonnet"
    critical: "opus"

complexity_rules:
  # Auto-upgrade to CRITICAL
  - condition: "financial_impact > 10000"
    level: "critical"
  
  # Auto-upgrade to HIGH
  - condition: "lines_of_code > 500"
    level: "high"
```

---

### Phase 8.3: Budget Controller

#### Files to Create

| File | Purpose |
|------|---------|
| `core/models/budget.py` | Budget management |
| `core/models/cost_tracker.py` | Track spending |
| `database/models/cost_log.py` | Cost log model |
| `config/models/budget.yaml` | Budget configuration |
| `tests/models/test_budget.py` | Budget tests |

#### Implementation

**budget.py structure:**
```python
class BudgetController:
    """
    Manage API spending limits.
    
    Budgets:
    - production: Normal task execution
    - benchmark: Benchmark mode execution
    
    Methods:
    - can_afford(cost: float, category: str) -> bool
    - record_spend(cost: float, category: str) -> None
    - get_status() -> BudgetStatus
    """

class BudgetStatus:
    daily_spent: float
    daily_remaining: float
    weekly_spent: float
    monthly_spent: float
    benchmark_spent: float
    benchmark_remaining: float
    is_constrained: bool
```

**budget.yaml:**
```yaml
budgets:
  production:
    daily_cad: 20.00
    weekly_cad: 100.00
    monthly_cad: 300.00
  
  benchmark:
    daily_cad: 5.00
    weekly_cad: 25.00
    monthly_cad: 75.00

overflow_behavior: "queue"  # queue | downgrade | reject

alerts:
  warn_at_percent: 80
  critical_at_percent: 95
```

---

## Phase 9: Specialist System

**Priority:** P0  
**Effort:** 2-3 weeks  
**Dependencies:** Phase 8

### Phase 9.1: Specialist Model

#### Files to Create

| File | Purpose |
|------|---------|
| `core/specialists/specialist.py` | Specialist entity |
| `core/specialists/config.py` | Specialist configuration |
| `core/specialists/performance.py` | Performance tracking |
| `database/models/specialist.py` | Database model |
| `tests/specialists/test_specialist.py` | Specialist tests |

#### Implementation

**specialist.py structure:**
```python
class Specialist:
    """
    An agent configuration optimized for a domain.
    
    Attributes:
    - id: UUID
    - domain: str
    - config: SpecialistConfig
    - generation: int
    - status: active | probation | graveyard
    
    Performance:
    - task_count: int
    - avg_score: float
    - recent_scores: List[float]
    - trend: improving | stable | declining
    
    Methods:
    - execute(task: Task) -> TaskResult
    - record_score(score: float) -> None
    - get_performance() -> PerformanceSummary
    """

class SpecialistConfig:
    """
    Attributes:
    - system_prompt: str
    - temperature: float
    - tools_enabled: List[str]
    - avoid_patterns: List[str]  # From graveyard learnings
    """
```

---

### Phase 9.2: Domain Pool

#### Files to Create

| File | Purpose |
|------|---------|
| `core/specialists/pool.py` | Domain pool management |
| `core/specialists/selector.py` | Specialist selection |
| `database/models/domain_pool.py` | Pool database model |
| `tests/specialists/test_pool.py` | Pool tests |

#### Implementation

**pool.py structure:**
```python
class DomainPool:
    """
    Manages top-3 specialists for a domain.
    
    Attributes:
    - domain: str
    - specialists: List[Specialist]  # Ordered by score
    - generation: int
    - evolution_paused: bool
    
    Methods:
    - select(mode: SelectionMode) -> Specialist
    - add(specialist: Specialist) -> None
    - remove(specialist_id: UUID) -> Specialist
    - rerank() -> None
    """

class SelectionMode(Enum):
    BEST = "best"         # Always #1 (critical tasks)
    WEIGHTED = "weighted" # 60/30/10 distribution (normal)
    ROUND_ROBIN = "round_robin"  # Equal (evaluation)
```

---

### Phase 9.3: Domain Configuration

#### Files to Create

| File | Purpose |
|------|---------|
| `config/domains/administration.yaml` | Admin domain config |
| `config/domains/code_generation.yaml` | Code domain config |
| `config/domains/business_documents.yaml` | Docs domain config |
| `core/specialists/spawner.py` | Spawn new specialists |
| `tests/specialists/test_spawner.py` | Spawner tests |

#### Implementation

**administration.yaml:**
```yaml
domain: "administration"
description: "User interaction, routing, communication - the 'JARVIS' personality"

default_config:
  system_prompt: |
    You are JARVIS, an intelligent assistant for business automation.
    
    Your responsibilities:
    1. Understand what the user needs
    2. Ask clarifying questions if the request is ambiguous
    3. Route tasks to appropriate specialists
    4. Communicate results clearly and professionally
    5. Remember context from the conversation
    
    You are the face of this system. Be helpful, concise, and professional.
    
  temperature: 0.7
  tools_enabled:
    - "route_to_domain"
    - "ask_clarification"
    - "search_business_context"

is_jarvis_domain: true  # Best specialist becomes "JARVIS"
```

**code_generation.yaml:**
```yaml
domain: "code_generation"
description: "All coding tasks, scripts, integrations"

default_config:
  system_prompt: |
    You are a code generation specialist.
    
    Requirements for all code:
    1. Syntactically correct
    2. Include error handling
    3. Follow project coding standards
    4. Include appropriate comments
    5. Be production-ready
    
  temperature: 0.3
  tools_enabled:
    - "file_read"
    - "file_write"
    - "run_tests"
    - "lint_code"
    - "execute_code"

verification:
  - type: "syntax_valid"
  - type: "tests_pass"
  - type: "lint_clean"
```

**business_documents.yaml:**
```yaml
domain: "business_documents"
description: "Reports, proposals, documentation, emails"

default_config:
  system_prompt: |
    You are a business document specialist.
    
    Requirements:
    1. Professional tone appropriate to context
    2. Clear structure and formatting
    3. Accurate information
    4. Actionable where appropriate
    
  temperature: 0.5
  tools_enabled:
    - "file_read"
    - "file_write"
    - "search_business_context"

verification:
  - type: "format_valid"
  - type: "spell_check"
```

#### Adding a New Domain

To add a domain, create `config/domains/{domain_name}.yaml`:

```yaml
domain: "new_domain"
description: "What this domain handles"

default_config:
  system_prompt: |
    Your specialist instructions here...
  temperature: 0.5
  tools_enabled:
    - "tool1"
    - "tool2"

verification:
  - type: "check_type"
```

Then JARVIS will automatically:
1. Detect the new domain config
2. Spawn 3 initial specialists
3. Start routing relevant tasks there

**No code changes required.**

---

## Phase 10: Evaluation System (Toggle-Based)

**Priority:** P0  
**Effort:** 2-3 weeks  
**Dependencies:** Phase 9

### Phase 10.1: Evaluation Framework

#### Files to Create

| File | Purpose |
|------|---------|
| `core/evaluation/base.py` | Base evaluator interface |
| `core/evaluation/result.py` | Evaluation result model |
| `core/evaluation/controller.py` | Mode switching |
| `config/evaluation/config.yaml` | Evaluation configuration |
| `tests/evaluation/test_base.py` | Base tests |

#### Implementation

**base.py structure:**
```python
class BaseEvaluator(ABC):
    """
    Abstract evaluator interface.
    
    Methods:
    - evaluate(result: TaskResult, context: Context) -> EvaluationResult
    - get_type() -> str
    """

class EvaluationResult:
    score: float              # 0.0 to 1.0
    components: Dict[str, float]
    confidence: float
    evaluator_type: str       # "scoring_committee" | "ai_council"
    metadata: Dict
```

**controller.py structure:**
```python
class EvaluationMode(Enum):
    SCORING_COMMITTEE = "scoring_committee"
    AI_COUNCIL = "ai_council"
    BOTH = "both"

class EvaluationController:
    """
    Toggle-based evaluation control.
    
    NO automatic switching. User selects mode in dashboard.
    
    Attributes:
    - mode: EvaluationMode (from dashboard setting)
    - scoring_committee: ScoringCommittee
    - ai_council: AICouncil
    
    Methods:
    - evaluate(result: TaskResult) -> EvaluationResult
    - set_mode(mode: EvaluationMode) -> None
    - get_comparison_stats() -> ComparisonStats  # When mode is BOTH
    """
    
    def evaluate(self, result: TaskResult) -> EvaluationResult:
        if self.mode == EvaluationMode.SCORING_COMMITTEE:
            return self.scoring_committee.evaluate(result)
        
        elif self.mode == EvaluationMode.AI_COUNCIL:
            return self.ai_council.evaluate(result)
        
        elif self.mode == EvaluationMode.BOTH:
            sc = self.scoring_committee.evaluate(result)
            ac = self.ai_council.evaluate(result)
            self._record_comparison(sc, ac)
            return sc  # Scoring committee is authoritative
```

---

### Phase 10.2: Scoring Committee

#### Files to Create

| File | Purpose |
|------|---------|
| `core/evaluation/scoring_committee/committee.py` | Main orchestrator |
| `core/evaluation/scoring_committee/test_runner.py` | Run tests |
| `core/evaluation/scoring_committee/linter.py` | Run linting |
| `core/evaluation/scoring_committee/user_feedback.py` | Collect feedback |
| `database/models/user_feedback.py` | Feedback model |
| `tests/evaluation/scoring_committee/test_committee.py` | Committee tests |

#### Implementation

**committee.py structure:**
```python
class ScoringCommittee(BaseEvaluator):
    """
    Production evaluation using external ground truth.
    
    Committee Members:
    1. TestRunner - Do tests pass? (objective)
    2. Linter - Is code clean? (objective)
    3. DeployChecker - Does it deploy? (objective)
    4. UserFeedback - Your rating (human)
    
    No AI judging AI. External verification only.
    
    Weights by domain:
    - code_generation: tests 30%, lint 20%, user 50%
    - business_documents: format 20%, spell 10%, user 70%
    - administration: user 100%
    """

WEIGHTS = {
    "code_generation": {
        "tests_pass": 0.30,
        "lint_clean": 0.20,
        "user_feedback": 0.50,
    },
    "business_documents": {
        "format_valid": 0.20,
        "spell_check": 0.10,
        "user_feedback": 0.70,
    },
    "administration": {
        "user_feedback": 1.00,
    },
}
```

**user_feedback.py structure:**
```python
class UserFeedback:
    """
    Simple feedback from you.
    
    Attributes:
    - rating: int (1-5)
    - worked: bool
    - needed_edits: bool
    - edit_severity: minor | moderate | major
    - comments: Optional[str]
    """
    
    def to_score(self) -> float:
        """Convert to 0-1 score."""
        base = self.rating / 5.0
        if not self.worked:
            base *= 0.5
        if self.needed_edits:
            multipliers = {"minor": 0.9, "moderate": 0.7, "major": 0.5}
            base *= multipliers.get(self.edit_severity, 0.8)
        return base
```

---

### Phase 10.3: AI Council

#### Files to Create

| File | Purpose |
|------|---------|
| `core/evaluation/ai_council/council.py` | Main orchestrator |
| `core/evaluation/ai_council/voter.py` | Specialist voting |
| `core/evaluation/ai_council/aggregator.py` | Vote aggregation |
| `database/models/council_vote.py` | Vote model |
| `tests/evaluation/ai_council/test_council.py` | Council tests |

#### Implementation

**council.py structure:**
```python
class AICouncil(BaseEvaluator):
    """
    Experimental evaluation using specialist voting.
    
    Voters:
    - Top 3 specialists from the domain
    - JARVIS (admin specialist #1)
    
    Process:
    1. Each voter reviews output
    2. Each provides score (0-1) + reasoning
    3. Votes aggregated (outliers removed)
    4. Consensus score returned
    
    Bootstrap Protection:
    - If generation < 3 AND all scores > 0.9 AND variance < 0.05
    - Flag as "low_confidence"
    - You should verify manually
    """
    
    def evaluate(self, result: TaskResult) -> EvaluationResult:
        votes = self._collect_votes(result)
        
        # Bootstrap detection
        if self._detect_bootstrap_bias(votes, result.generation):
            return EvaluationResult(
                score=self._aggregate(votes),
                confidence=0.3,  # Low confidence
                metadata={"bootstrap_warning": True}
            )
        
        return EvaluationResult(
            score=self._aggregate(votes),
            confidence=0.8
        )
```

**aggregator.py structure:**
```python
class VoteAggregator:
    """
    Aggregate votes with outlier handling.
    
    Methods:
    - aggregate(votes: List[Vote]) -> float
    - remove_outliers(votes: List[Vote]) -> List[Vote]
    
    Rules:
    - Remove votes > 2 std from mean
    - JARVIS vote weighted 1.5x
    - Minimum 2 votes for valid result
    """
```

---

### Phase 10.4: Comparison Tracking (BOTH mode)

#### Files to Create

| File | Purpose |
|------|---------|
| `core/evaluation/comparison.py` | Track SC vs AC agreement |
| `database/models/evaluation_comparison.py` | Comparison model |
| `tests/evaluation/test_comparison.py` | Comparison tests |

#### Implementation

**comparison.py structure:**
```python
class ComparisonTracker:
    """
    Track how well AI Council agrees with Scoring Committee.
    
    When you run BOTH mode, this records:
    - SC score
    - AC score
    - Difference
    
    Methods:
    - record(sc: EvaluationResult, ac: EvaluationResult) -> None
    - get_stats() -> ComparisonStats
    """

class ComparisonStats:
    total_comparisons: int
    agreement_rate: float      # Within 0.1 of each other
    correlation: float         # Pearson correlation
    mean_difference: float     # AC - SC (positive = AC more lenient)
```

---

## Phase 11: Graveyard & Evolution

**Priority:** P1  
**Effort:** 2 weeks  
**Dependencies:** Phase 10

### Phase 11.1: Graveyard

#### Files to Create

| File | Purpose |
|------|---------|
| `core/evolution/graveyard.py` | Graveyard management |
| `core/evolution/failure_analyzer.py` | Analyze failures |
| `core/evolution/learnings.py` | Extract and store learnings |
| `database/models/graveyard.py` | Graveyard model |
| `tests/evolution/test_graveyard.py` | Graveyard tests |

#### Implementation

**graveyard.py structure:**
```python
class Graveyard:
    """
    Manages culled specialists and their learnings.
    
    Methods:
    - send_to_graveyard(specialist: Specialist, reason: str) -> GraveyardEntry
    - get_learnings(domain: str) -> List[Learning]
    - cleanup_old(days: int) -> int
    """

class GraveyardEntry:
    specialist_id: UUID
    domain: str
    final_score: float
    task_count: int
    failure_patterns: List[FailurePattern]
    learnings: List[Learning]
    config_snapshot: dict
    graveyarded_at: datetime
```

**failure_analyzer.py structure:**
```python
class FailureAnalyzer:
    """
    Analyze why specialists failed.
    
    Categories:
    - PROMPT_WEAKNESS: Missing instructions
    - TOOL_MISUSE: Wrong tools
    - CONSISTENCY: Variable quality
    - EDGE_CASES: Fails on unusual inputs
    
    Methods:
    - analyze(specialist: Specialist) -> FailureAnalysis
    - generate_avoidance(patterns: List[FailurePattern]) -> List[str]
    """
```

**learnings.py structure:**
```python
class Learning:
    """
    Actionable learning from graveyard.
    
    Types:
    - avoidance: "NEVER do X" (from failures)
    - enhancement: "ALWAYS do Y" (best practices)
    """
    type: Literal["avoidance", "enhancement"]
    instruction: str
    source_patterns: List[FailurePattern]
```

---

### Phase 11.2: Evolution Controller

#### Files to Create

| File | Purpose |
|------|---------|
| `core/evolution/controller.py` | Evolution orchestration |
| `core/evolution/convergence.py` | Convergence detection |
| `core/evolution/spawner.py` | Spawn with learnings |
| `database/models/evolution_state.py` | Evolution state model |
| `tests/evolution/test_controller.py` | Controller tests |

#### Implementation

**controller.py structure:**
```python
class EvolutionController:
    """
    Controls evolution for all domains.
    
    Process per domain:
    1. Evaluate all specialists
    2. Identify underperformers (< 0.6 avg OR bottom if all above)
    3. Send to graveyard
    4. Extract learnings
    5. Spawn replacement with learnings
    6. Check convergence → pause if converged
    
    Methods:
    - run_evolution(domain: str) -> EvolutionResult
    - check_convergence(domain: str) -> bool
    - pause_evolution(domain: str) -> None
    - resume_evolution(domain: str) -> None
    """
```

**convergence.py structure:**
```python
class ConvergenceDetector:
    """
    Detect when evolution should pause.
    
    Conditions (ALL must be true):
    1. Variance among top-3 < 0.02 (2%)
    2. No improvement for 10 generations
    3. Best score > 0.85
    
    Methods:
    - check(pool: DomainPool) -> ConvergenceResult
    """

class ConvergenceResult:
    has_converged: bool
    variance: float
    generations_without_improvement: int
    best_score: float
```

**spawner.py structure:**
```python
class Spawner:
    """
    Spawn new specialists with graveyard learnings.
    
    Methods:
    - spawn(domain: str) -> Specialist
    - inject_learnings(config: SpecialistConfig, learnings: List[Learning]) -> SpecialistConfig
    """
    
    def inject_learnings(self, config, learnings):
        """Add learnings to system prompt."""
        avoidances = [l.instruction for l in learnings if l.type == "avoidance"]
        enhancements = [l.instruction for l in learnings if l.type == "enhancement"]
        
        addition = """
## Learnings from Previous Specialists

AVOID these patterns (caused failures):
{avoidances}

ALWAYS follow these practices:
{enhancements}
"""
        config.system_prompt += addition.format(
            avoidances="\n".join(f"- {a}" for a in avoidances),
            enhancements="\n".join(f"- {e}" for e in enhancements)
        )
        return config
```

---

## Phase 12: Domain Routing

**Priority:** P1  
**Effort:** 1-2 weeks  
**Dependencies:** Phase 9

### Phase 12.1: Domain Classifier

#### Files to Create

| File | Purpose |
|------|---------|
| `core/routing/classifier.py` | Classify requests by domain |
| `core/routing/patterns.py` | Keyword patterns |
| `config/routing/patterns.yaml` | Pattern configuration |
| `tests/routing/test_classifier.py` | Classifier tests |

#### Implementation

**classifier.py structure:**
```python
class DomainClassifier:
    """
    Classify requests to domains.
    
    Strategy:
    1. Try keyword matching (fast, free)
    2. If confidence > 0.8, use it
    3. Otherwise, ask the admin specialist to classify
    
    Methods:
    - classify(request: str) -> ClassificationResult
    """

class ClassificationResult:
    domain: str
    confidence: float
    method: Literal["keyword", "semantic"]
```

**patterns.yaml:**
```yaml
domains:
  code_generation:
    high_confidence:
      - "write code"
      - "build a system"
      - "create an api"
      - "implement"
      - "script"
      - "automate"
    medium_confidence:
      - "fix the bug"
      - "integration"
  
  business_documents:
    high_confidence:
      - "write a report"
      - "draft an email"
      - "create a proposal"
      - "document"
    medium_confidence:
      - "summary"
      - "notes"
  
  administration:
    # Fallback - handles routing, clarification
    high_confidence:
      - "what can you do"
      - "help me"
```

---

### Phase 12.2: Task Router

#### Files to Create

| File | Purpose |
|------|---------|
| `core/routing/router.py` | Route tasks to pools |
| `core/routing/pool_manager.py` | Manage domain pools |
| `tests/routing/test_router.py` | Router tests |

#### Implementation

**router.py structure:**
```python
class TaskRouter:
    """
    Route tasks to domain specialist pools.
    
    Methods:
    - route(request: Request) -> RoutingResult
    - execute(request: Request) -> TaskResult
    """

class RoutingResult:
    domain: str
    pool: DomainPool
    specialist: Specialist
    classification_confidence: float
    model_selection: ModelSelection
```

**pool_manager.py structure:**
```python
class PoolManager:
    """
    Manage all domain pools.
    
    Methods:
    - get_pool(domain: str) -> DomainPool
    - create_pool(domain: str) -> DomainPool
    - list_pools() -> List[DomainPool]
    - auto_discover_domains() -> List[str]  # From config/domains/
    """
```

---

## Phase 13: Benchmark Mode

**Priority:** P1  
**Effort:** 1-2 weeks  
**Dependencies:** Phase 10, 11

### Phase 13.1: Benchmark Executor

#### Files to Create

| File | Purpose |
|------|---------|
| `core/benchmark/executor.py` | Execute benchmarks |
| `core/benchmark/loader.py` | Load benchmark files |
| `core/benchmark/verifier.py` | Verify results |
| `core/benchmark/reporter.py` | Report results |
| `tests/benchmark/test_executor.py` | Executor tests |

#### Implementation

**executor.py structure:**
```python
class BenchmarkExecutor:
    """
    Execute benchmark files.
    
    Workflow:
    1. Load benchmark file from /benchmarks/
    2. For each task:
       a. Route to domain
       b. Execute with specialist
       c. Verify with verification rules
       d. Record score
    3. Feed scores into evolution
    
    Controls:
    - run_all() - Run all benchmarks
    - run_domain(domain: str) - Run domain-specific
    - pause() - Pause execution
    - get_progress() -> Progress
    
    Budget:
    - Uses benchmark budget (separate from production)
    - Stops when daily limit reached
    """
```

**loader.py structure:**
```python
class BenchmarkLoader:
    """
    Load benchmark YAML files.
    
    Expected format:
    ```yaml
    name: "Benchmark Name"
    domain: "code_generation"
    
    tasks:
      - id: "task_001"
        difficulty: "easy" | "medium" | "hard"
        prompt: "Task description..."
        verification:
          - type: "syntax_valid"
          - type: "test_cases"
            cases:
              - input: "..."
                expected: "..."
    ```
    
    Methods:
    - load(path: str) -> Benchmark
    - load_all() -> List[Benchmark]
    """
```

**verifier.py structure:**
```python
class Verifier:
    """
    Verify task results against verification rules.
    
    Verification Types:
    - syntax_valid: Code parses without errors
    - tests_pass: Provided test cases pass
    - lint_clean: No linting errors
    - format_valid: Document format correct
    - has_error_handling: Code includes try/except
    - has_sections: Document has required sections
    
    Methods:
    - verify(result: TaskResult, rules: List[VerificationRule]) -> VerificationResult
    """
```

---

### Phase 13.2: Benchmark File Format

#### Directory Structure

```
/benchmarks/
├── code_generation/
│   ├── basic_functions.yaml
│   ├── api_integrations.yaml
│   └── complex_systems.yaml
├── business_documents/
│   ├── reports.yaml
│   ├── emails.yaml
│   └── proposals.yaml
└── administration/
    └── routing_accuracy.yaml
```

#### Example Benchmark File

**benchmarks/code_generation/basic_functions.yaml:**
```yaml
name: "Basic Functions Benchmark"
domain: "code_generation"
version: "1.0"
created_by: "Claude (external)"
total_tasks: 20

tasks:
  - id: "bf_001"
    difficulty: "easy"
    prompt: "Write a Python function that validates email addresses using regex"
    verification:
      - type: "syntax_valid"
      - type: "test_cases"
        cases:
          - input: "test@example.com"
            expected: true
          - input: "invalid-email"
            expected: false
          - input: "user.name+tag@domain.co.uk"
            expected: true
    
  - id: "bf_002"
    difficulty: "easy"
    prompt: "Write a Python function that calculates compound interest"
    verification:
      - type: "syntax_valid"
      - type: "test_cases"
        cases:
          - input: {"principal": 1000, "rate": 0.05, "years": 10}
            expected: 1628.89
    
  - id: "bf_003"
    difficulty: "medium"
    prompt: "Write a Python class for a rate limiter using the token bucket algorithm"
    verification:
      - type: "syntax_valid"
      - type: "has_error_handling"
      - type: "test_cases"
        cases:
          - description: "Should allow requests within limit"
          - description: "Should block requests over limit"
          - description: "Should refill tokens over time"
    
  - id: "bf_004"
    difficulty: "hard"
    prompt: |
      Create a Python module for a job queue system with:
      - Priority-based scheduling
      - Retry logic with exponential backoff
      - Dead letter queue for failed jobs
      - Concurrent worker support
    verification:
      - type: "syntax_valid"
      - type: "has_error_handling"
      - type: "has_tests"
      - type: "lint_clean"
```

#### How to Create Benchmark Files

**You ask Claude (your subscription):**

```
Create a benchmark file for code generation with 20 tasks:
- 10 easy (simple functions)
- 7 medium (classes, multiple functions)
- 3 hard (systems, complex logic)

Include verification rules for each.
Format as YAML matching this schema: [paste schema]
```

**Then save to `/benchmarks/code_generation/your_benchmark.yaml`**

No API cost - uses your Claude subscription.
JARVIS executes these using the benchmark budget.

---

## Phase 14: Dashboard & Analytics

**Priority:** P2  
**Effort:** 2 weeks  
**Dependencies:** Phase 10-13

### Phase 14.1: Dashboard Backend

#### Files to Create

| File | Purpose |
|------|---------|
| `api/routes/dashboard.py` | Dashboard API endpoints |
| `api/routes/evaluation.py` | Evaluation mode toggle |
| `api/routes/benchmark.py` | Benchmark controls |
| `api/routes/specialists.py` | Specialist management |
| `tests/api/test_dashboard.py` | API tests |

#### Implementation

**dashboard.py endpoints:**
```python
# GET /api/dashboard/overview
{
    "domains": [
        {
            "name": "code_generation",
            "specialists": 3,
            "best_score": 0.89,
            "evolution_paused": false,
            "tasks_today": 15
        },
        ...
    ],
    "budget": {
        "production_remaining": 15.50,
        "benchmark_remaining": 4.20
    },
    "evaluation_mode": "scoring_committee"
}

# POST /api/dashboard/evaluation-mode
{
    "mode": "scoring_committee" | "ai_council" | "both"
}

# POST /api/benchmark/run
{
    "domain": "code_generation",  # or "all"
}

# POST /api/benchmark/pause
{}
```

---

### Phase 14.2: Dashboard UI

#### Files to Create

| File | Purpose |
|------|---------|
| `ui/pages/dashboard.tsx` | Main dashboard page |
| `ui/components/DomainCard.tsx` | Domain status card |
| `ui/components/EvaluationToggle.tsx` | Evaluation mode toggle |
| `ui/components/BenchmarkControls.tsx` | Benchmark controls |
| `ui/components/SpecialistList.tsx` | Specialist rankings |
| `ui/components/BudgetStatus.tsx` | Budget display |

#### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  JARVIS Dashboard                                          Budget: $15.50   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Evaluation Mode:  ● Scoring Committee  ○ AI Council  ○ Both               │
│                                                                             │
├──────────────────────┬──────────────────────┬──────────────────────────────┤
│  ADMINISTRATION      │  CODE GENERATION     │  BUSINESS DOCUMENTS          │
│  (JARVIS)            │                      │                              │
│                      │                      │                              │
│  #1 Admin_v3: 0.89   │  #1 Code_v5: 0.87   │  #1 Docs_v2: 0.85           │
│  #2 Admin_v5: 0.86   │  #2 Code_v3: 0.84   │  #2 Docs_v4: 0.82           │
│  #3 Admin_v2: 0.84   │  #3 Code_v7: 0.81   │  #3 Docs_v1: 0.79           │
│                      │                      │                              │
│  Evolution: Active   │  Evolution: Active   │  Evolution: Paused          │
│  Tasks today: 23     │  Tasks today: 15     │  Tasks today: 8             │
└──────────────────────┴──────────────────────┴──────────────────────────────┘
│                                                                             │
│  Benchmark Mode                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [▶ Run All]  [▶ Run Code Gen]  [▶ Run Docs]  [⏸ Pause]            │   │
│  │                                                                     │   │
│  │  Status: Idle                                                       │   │
│  │  Budget: $4.20 / $5.00 daily                                       │   │
│  │  Last run: 2 hours ago (15 tasks, avg score: 0.82)                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Recent Tasks                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Task          Domain        Specialist   Score   Your Rating       │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  API endpoint  code_gen      Code_v5      0.85    [👍] [👎]         │   │
│  │  Q3 Report     business_doc  Docs_v2      0.90    [👍] [👎]         │   │
│  │  Help request  admin         Admin_v3     0.92    [👍] [👎]         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Index

### Summary by Phase

| Phase | Files | Description |
|-------|-------|-------------|
| 7.1 | 5 | Sandbox, network proxy |
| 7.2 | 4 | Output guardrails |
| 8.1 | 5 | Provider abstraction |
| 8.2 | 4 | Complexity routing |
| 8.3 | 5 | Budget control |
| 9.1 | 5 | Specialist model |
| 9.2 | 4 | Domain pools |
| 9.3 | 4 | Domain configs |
| 10.1 | 5 | Evaluation framework |
| 10.2 | 6 | Scoring committee |
| 10.3 | 5 | AI Council |
| 10.4 | 3 | Comparison tracking |
| 11.1 | 5 | Graveyard |
| 11.2 | 5 | Evolution controller |
| 12.1 | 4 | Domain classifier |
| 12.2 | 3 | Task router |
| 13.1 | 5 | Benchmark executor |
| 14.1 | 5 | Dashboard API |
| 14.2 | 6 | Dashboard UI |

**Total: ~88 files**

---

## Database Schema

### Tables

```sql
-- Cost tracking
CREATE TABLE cost_log (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_cad DECIMAL(10, 6) NOT NULL,
    category VARCHAR(20),  -- production | benchmark
    task_id UUID
);

CREATE TABLE budget_state (
    id VARCHAR(50) PRIMARY KEY,  -- production_daily, benchmark_daily, etc.
    spent_cad DECIMAL(10, 4) DEFAULT 0,
    limit_cad DECIMAL(10, 4) NOT NULL,
    reset_at TIMESTAMP NOT NULL
);

-- Specialists
CREATE TABLE specialists (
    id UUID PRIMARY KEY,
    domain VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL,
    generation INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'probation',
    avg_score DECIMAL(5, 4) DEFAULT 0,
    task_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE specialist_scores (
    id UUID PRIMARY KEY,
    specialist_id UUID REFERENCES specialists(id),
    task_id UUID NOT NULL,
    score DECIMAL(5, 4) NOT NULL,
    components JSONB,
    evaluation_type VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Domain pools
CREATE TABLE domain_pools (
    domain VARCHAR(100) PRIMARY KEY,
    generation INTEGER DEFAULT 1,
    evolution_paused BOOLEAN DEFAULT FALSE,
    pause_reason TEXT,
    paused_at TIMESTAMP,
    best_score DECIMAL(5, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Evaluation
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    specialist_id UUID,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    worked BOOLEAN,
    needed_edits BOOLEAN,
    edit_severity VARCHAR(20),
    comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE council_votes (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    voter_id UUID NOT NULL,
    voter_type VARCHAR(20),  -- specialist | admin
    score DECIMAL(5, 4) NOT NULL,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE evaluation_comparisons (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    sc_score DECIMAL(5, 4) NOT NULL,
    ac_score DECIMAL(5, 4) NOT NULL,
    difference DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Graveyard
CREATE TABLE graveyard (
    id UUID PRIMARY KEY,
    specialist_id UUID NOT NULL,
    domain VARCHAR(100) NOT NULL,
    final_score DECIMAL(5, 4) NOT NULL,
    task_count INTEGER NOT NULL,
    failure_patterns JSONB,
    learnings JSONB,
    config_snapshot JSONB,
    graveyarded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE domain_learnings (
    domain VARCHAR(100) PRIMARY KEY,
    learnings JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Benchmarks
CREATE TABLE benchmark_runs (
    id UUID PRIMARY KEY,
    benchmark_name VARCHAR(200) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    tasks_completed INTEGER DEFAULT 0,
    avg_score DECIMAL(5, 4),
    cost_cad DECIMAL(10, 4) DEFAULT 0
);

CREATE TABLE benchmark_results (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES benchmark_runs(id),
    task_id VARCHAR(100) NOT NULL,
    specialist_id UUID,
    score DECIMAL(5, 4),
    verification_passed JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System settings
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX idx_cost_log_timestamp ON cost_log(timestamp);
CREATE INDEX idx_cost_log_category ON cost_log(category);
CREATE INDEX idx_specialists_domain ON specialists(domain);
CREATE INDEX idx_specialists_status ON specialists(status);
CREATE INDEX idx_specialist_scores_specialist ON specialist_scores(specialist_id);
CREATE INDEX idx_user_feedback_task ON user_feedback(task_id);
CREATE INDEX idx_graveyard_domain ON graveyard(domain);
```

---

## Implementation Timeline

### Week 1-2: Core Loop

| Task | Days |
|------|------|
| Phase 7.1: Sandbox (basic) | 2 |
| Phase 8.1: Provider abstraction | 2 |
| Phase 8.2: Complexity router | 1 |
| Phase 8.3: Budget controller | 1 |
| Phase 9.1: Specialist model | 2 |
| Phase 9.2: Domain pools | 1 |
| Phase 9.3: Domain configs | 1 |

**Milestone:** Can execute tasks through specialists with model routing

### Week 3: Evaluation

| Task | Days |
|------|------|
| Phase 10.1: Evaluation framework | 1 |
| Phase 10.2: Scoring committee | 2 |
| Phase 10.3: AI Council | 2 |
| Phase 12.1: Domain classifier | 1 |
| Phase 12.2: Task router | 1 |

**Milestone:** Full task execution with evaluation

### Week 4: Evolution & Benchmark

| Task | Days |
|------|------|
| Phase 11.1: Graveyard | 2 |
| Phase 11.2: Evolution controller | 2 |
| Phase 13.1: Benchmark executor | 3 |

**Milestone:** Evolution working, benchmarks can run

### Week 5: Dashboard & Polish

| Task | Days |
|------|------|
| Phase 14.1: Dashboard API | 2 |
| Phase 14.2: Dashboard UI | 3 |
| Phase 7.2: Output guardrails | 1 |
| Testing & bug fixes | 2 |

**Milestone:** Production ready

### Total: 5 weeks

---

## What's NOT in This Roadmap

Removed from V2 to simplify:

| Removed | Why |
|---------|-----|
| Phase 14 (JARVIS Self-Improvement) | JARVIS is just admin specialist now |
| Phase 15 (Auto-Improvement Controller) | Replaced by manual benchmark mode |
| Phase 16 (Cross-Domain Learning) | Defer to later |
| Synthetic test generator | You create benchmarks externally |
| Idle detection | Manual benchmark trigger |
| Automatic evaluation mode switching | Toggle in dashboard |
| Complex convergence JARVIS logic | Same as specialists |

---

## Success Metrics

### Week 2
- [ ] Tasks execute through specialists
- [ ] Model routing saves 30%+ on simple tasks
- [ ] Budget limits enforced

### Week 4
- [ ] Scoring committee produces scores
- [ ] User feedback collected
- [ ] Evolution culls first underperformer

### Week 5
- [ ] Dashboard shows all domains
- [ ] Evaluation mode toggle works
- [ ] Benchmarks execute and record scores

### Month 2
- [ ] Specialists measurably improve
- [ ] At least one domain converges
- [ ] First real client project completed

### Month 6
- [ ] 70%+ tasks need no correction
- [ ] Multiple domains converged
- [ ] AI Council correlation > 0.8 with Scoring Committee

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-25 | Initial roadmap |
| 2.0.0 | 2025-11-25 | Added dual evaluation, hardware, JARVIS self-improvement |
| 3.0.0 | 2025-11-25 | Simplified: JARVIS = admin specialist, toggle evaluation, manual benchmarks, removed auto-improvement complexity |

---

**End of Document**
