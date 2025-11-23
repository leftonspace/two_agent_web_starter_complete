# JARVIS 2.0 API Reference

**Version:** 2.0.0
**Date:** November 23, 2025

---

## Table of Contents

1. [Flow Engine](#flow-engine)
2. [Clarification System](#clarification-system)
3. [Pattern-Based Orchestration](#pattern-based-orchestration)
4. [Council System](#council-system)
5. [Memory System](#memory-system)
6. [LLM Router](#llm-router)
7. [Performance Utilities](#performance-utilities)
8. [Human-in-the-Loop](#human-in-the-loop)

---

## Flow Engine

Located in `agent/flow/`

### Decorators (`flow/decorators.py`)

#### `@start()`
Marks a method as the entry point for a flow.

```python
from agent.flow import start, Flow

class MyFlow(Flow):
    @start()
    def begin(self):
        return "Starting flow"
```

#### `@listen(event_or_method)`
Subscribes a method to events or other method completions.

```python
@listen("user_input")
def handle_input(self, data):
    return process(data)

@listen(begin)  # Listen to method completion
def after_begin(self, result):
    return f"Begin returned: {result}"
```

#### `@router()`
Defines a conditional router that returns the next step name.

```python
@router()
def decide_path(self, state):
    if state.needs_clarification:
        return "clarify"
    return "execute"
```

#### `or_(*conditions)` / `and_(*conditions)`
Logical combinators for complex event listening.

```python
@listen(or_("event_a", "event_b"))
def handle_either(self, data):
    pass

@listen(and_("ready", "validated"))
def handle_both(self, data):
    pass
```

### Flow Engine (`flow/engine.py`)

#### `class FlowEngine`

```python
engine = FlowEngine()

# Register a flow
engine.register_flow("my_flow", MyFlow)

# Execute a flow
result = await engine.execute("my_flow", initial_state={"input": "hello"})

# Get flow status
status = engine.get_status("my_flow")
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `register_flow` | `name: str, flow_class: Type[Flow]` | `None` | Register a flow class |
| `execute` | `name: str, initial_state: dict` | `FlowResult` | Execute a flow |
| `get_status` | `name: str` | `FlowStatus` | Get current flow status |
| `cancel` | `name: str` | `bool` | Cancel a running flow |

### State Management (`flow/state.py`)

#### `class FlowState`
Base class for flow state using Pydantic.

```python
from agent.flow import FlowState

class TaskState(FlowState):
    task_description: str
    status: str = "pending"
    results: List[str] = []

    class Config:
        validate_assignment = True
```

**Properties:**
- `created_at: datetime` - When state was created
- `updated_at: datetime` - Last update time
- `version: int` - State version for optimistic locking

### Event Bus (`flow/events.py`)

#### `class EventBus`

```python
bus = EventBus()

# Subscribe to events
bus.subscribe("task_complete", callback)

# Publish events
await bus.publish("task_complete", {"result": "success"})

# Unsubscribe
bus.unsubscribe("task_complete", callback)
```

---

## Clarification System

Located in `agent/clarification/`

### ClarificationDetector (`clarification/detector.py`)

Detects when tasks need clarification before execution.

```python
from agent.clarification import ClarificationDetector, DetectorConfig

detector = ClarificationDetector(config=DetectorConfig(
    min_description_length=50,
    technical_keywords_threshold=2,
    ambiguity_patterns=["make a", "build an", "create"]
))

needs_clarification = detector.should_clarify("make me a website")
# Returns: True
```

**DetectorConfig Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_description_length` | `int` | `50` | Minimum chars for clear task |
| `technical_keywords_threshold` | `int` | `2` | Required technical terms |
| `ambiguity_patterns` | `List[str]` | `[...]` | Patterns indicating vagueness |
| `bypass_phrases` | `List[str]` | `["just do it", ...]` | Phrases to skip clarification |

### QuestionGenerator (`clarification/generator.py`)

Generates contextual clarifying questions.

```python
from agent.clarification import QuestionGenerator

generator = QuestionGenerator(llm_client=client)
questions = await generator.generate(
    task="make me a website",
    context={"domain": "bakery"}
)
# Returns: ["What is the primary purpose?", "What pages needed?", ...]
```

### ClarificationLoop (`clarification/loop.py`)

Manages the full clarification workflow.

```python
from agent.clarification import ClarificationLoop, ClarificationState

loop = ClarificationLoop(detector=detector, generator=generator)

# Start clarification
state = await loop.start("build an app")

# Process user answer
state = await loop.process_answer(state, "It's for inventory tracking")

# Check if ready
if state.phase == "ready":
    enhanced_task = loop.get_enhanced_task(state)
```

**ClarificationState:**

```python
@dataclass
class ClarificationState:
    pending_task: Optional[str] = None
    questions: List[Dict] = field(default_factory=list)
    answers: Dict[str, str] = field(default_factory=dict)
    phase: str = "idle"  # idle, asking, ready
    round: int = 0
    max_rounds: int = 3
```

---

## Pattern-Based Orchestration

Located in `agent/patterns/`

### Base Pattern (`patterns/base.py`)

```python
from agent.patterns import OrchestrationPattern, PatternConfig

class CustomPattern(OrchestrationPattern):
    async def select_next_speaker(
        self,
        agents: List[Agent],
        context: OrchestrationContext
    ) -> Optional[Agent]:
        # Custom selection logic
        return agents[0]
```

### Available Patterns

#### SequentialPattern (`patterns/sequential.py`)

Agents execute in defined order, one turn each per round.

```python
from agent.patterns import SequentialPattern

pattern = SequentialPattern(config=PatternConfig(
    max_rounds=3,
    allow_repeat=False
))
```

#### HierarchicalPattern (`patterns/hierarchical.py`)

Manager delegates to supervisors who delegate to workers.

```python
from agent.patterns import HierarchicalPattern

pattern = HierarchicalPattern(config=PatternConfig(
    hierarchy_levels=["manager", "supervisor", "worker"],
    escalation_enabled=True
))
```

#### AutoSelectPattern (`patterns/auto_select.py`)

LLM dynamically selects the best next speaker.

```python
from agent.patterns import AutoSelectPattern

pattern = AutoSelectPattern(
    llm_client=client,
    config=PatternConfig(selection_prompt_template="...")
)
```

#### RoundRobinPattern (`patterns/round_robin.py`)

Fixed rotation through all agents.

```python
from agent.patterns import RoundRobinPattern

pattern = RoundRobinPattern(config=PatternConfig(
    max_rounds=5,
    skip_on_no_contribution=True
))
```

#### ManualPattern (`patterns/manual.py`)

Returns control to user for agent selection.

```python
from agent.patterns import ManualPattern

pattern = ManualPattern(
    user_prompt_callback=get_user_selection
)
```

### Pattern Selector (`agent/pattern_selector.py`)

Auto-recommends patterns based on task analysis.

```python
from agent.pattern_selector import PatternSelector

selector = PatternSelector()
recommended = selector.recommend(
    task="Review this pull request",
    agents=["reviewer", "author", "qa"]
)
# Returns: PatternRecommendation(pattern="round_robin", confidence=0.85)
```

**Recommendation Logic:**

| Task Type | Recommended Pattern |
|-----------|-------------------|
| Simple, linear | Sequential |
| Code review, feedback | RoundRobin |
| Complex, ambiguous | AutoSelect |
| Critical operations | Manual |
| Multi-level tasks | Hierarchical |

---

## Council System

Located in `agent/council/`

### Councillor Model (`council/models.py`)

```python
from agent.council import Councillor, PerformanceMetrics, Specialization

councillor = Councillor(
    id="ada_001",
    name="Ada",
    specialization=Specialization.CODING,
    performance=PerformanceMetrics(
        quality_score=0.92,
        speed_score=0.85,
        feedback_score=0.88,
        success_rate=0.90
    ),
    happiness=75,
    vote_weight=1.84
)
```

**Specializations:**

```python
class Specialization(Enum):
    CODING = "coding"
    DESIGN = "design"
    TESTING = "testing"
    REVIEW = "review"
    ARCHITECTURE = "architecture"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
```

### Voting System (`council/voting.py`)

```python
from agent.council import VotingSession, Vote, VoteOption

session = VotingSession(
    question="How should we approach this task?",
    options=[
        VoteOption("simple", "Simple approach"),
        VoteOption("standard", "Standard approach"),
        VoteOption("complex", "Complex approach"),
    ]
)

# Councillors vote
session.cast_vote(Vote(
    councillor_id="ada_001",
    option="complex",
    confidence=0.9,
    weight=1.84,
    reasoning="Task requires multiple integrations"
))

# Get result
result = session.tally()
# Returns: VoteResult(winner="complex", weighted_score=1.656, ...)
```

### Happiness Manager (`council/happiness.py`)

```python
from agent.council import HappinessManager, HappinessEvent

manager = HappinessManager()

# Apply happiness event
new_happiness = manager.apply_event(
    councillor=councillor,
    event=HappinessEvent.TASK_SUCCESS
)

# Check happiness effects
effects = manager.get_effects(happiness=45)
# Returns: {"work_quality": 0.85, "vote_modifier": 0.9, "burnout_risk": True}
```

**Happiness Events:**

| Event | Impact |
|-------|--------|
| `TASK_SUCCESS` | +5 |
| `TASK_FAILURE` | -8 |
| `BONUS_RECEIVED` | +15 |
| `CRITICISM` | -10 |
| `PRAISE` | +8 |
| `OVERWORKED` | -12 |
| `VOTE_WON` | +3 |
| `VOTE_IGNORED` | -5 |
| `COLLEAGUE_FIRED` | -8 |

### Council Factory (`council/factory.py`)

```python
from agent.council import CouncillorFactory

factory = CouncillorFactory()

# Spawn new councillor
new_councillor = factory.spawn(
    specialization=Specialization.TESTING,
    probation=True
)

# Check for firing conditions
should_fire = factory.should_fire(councillor)
# Returns: True if performance < 40% OR 5+ consecutive failures OR happiness < 20%
```

### Council Orchestrator (`council/orchestrator.py`)

```python
from agent.council import CouncilOrchestrator

orchestrator = CouncilOrchestrator(
    councillors=councillors,
    leader=leader,
    factory=factory
)

# Execute task with council
result = await orchestrator.execute_task(
    task="Implement user authentication",
    context={"priority": "high"}
)

# Get council status
status = orchestrator.get_status()
# Returns: {"active": 5, "on_probation": 1, "avg_happiness": 72, ...}
```

---

## Memory System

Located in `agent/memory/`

### Short-Term Memory (`memory/short_term.py`)

```python
from agent.memory import ShortTermMemory, STMConfig

stm = ShortTermMemory(config=STMConfig(
    max_tokens=4000,
    relevance_threshold=0.7,
    embedding_model="text-embedding-3-small"
))

# Add message
await stm.add_message(role="user", content="Hello")

# Get relevant context
context = await stm.get_relevant_context(
    query="What did the user say?",
    max_tokens=1000
)

# Compress if needed
await stm.compress()
```

### Long-Term Memory (`memory/long_term.py`)

```python
from agent.memory import LongTermMemory, LTMConfig

ltm = LongTermMemory(config=LTMConfig(
    storage_path="./memory_store",
    embedding_model="text-embedding-3-small",
    chunk_size=500
))

# Store memory
await ltm.store(
    content="User prefers dark mode",
    metadata={"category": "preference", "user_id": "123"}
)

# Retrieve memories
memories = await ltm.retrieve(
    query="What are user preferences?",
    limit=5,
    filters={"user_id": "123"}
)
```

### Entity Memory (`memory/entity.py`)

```python
from agent.memory import EntityMemory, Entity, Relationship

entity_mem = EntityMemory()

# Add entity
await entity_mem.add_entity(Entity(
    id="user_123",
    type="person",
    name="John",
    attributes={"role": "developer", "team": "backend"}
))

# Add relationship
await entity_mem.add_relationship(Relationship(
    source="user_123",
    target="project_456",
    type="works_on",
    properties={"since": "2024-01"}
))

# Query graph
related = await entity_mem.get_related(
    entity_id="user_123",
    relationship_type="works_on",
    depth=2
)
```

### Memory Manager (`memory/manager.py`)

Unified interface for all memory types.

```python
from agent.memory import MemoryManager, MemoryConfig

manager = MemoryManager(config=MemoryConfig(
    stm_config=STMConfig(...),
    ltm_config=LTMConfig(...),
    entity_config=EntityConfig(...)
))

# Process message (auto-routes to appropriate memory)
await manager.process_message(message)

# Get unified context
context = await manager.get_context(
    query="user preferences",
    include_stm=True,
    include_ltm=True,
    include_entities=True
)
```

---

## LLM Router

Located in `agent/llm/`

### Enhanced Router (`llm/enhanced_router.py`)

```python
from agent.llm import EnhancedRouter, RouterConfig

router = EnhancedRouter(config=RouterConfig(
    providers=["anthropic", "openai", "deepseek", "ollama"],
    default_provider="anthropic",
    cost_optimization=True,
    failover_enabled=True
))

# Route request
response = await router.complete(
    messages=[{"role": "user", "content": "Hello"}],
    model_preference="claude-3-sonnet",
    max_tokens=1000
)

# Get cost estimate
cost = router.estimate_cost(
    provider="anthropic",
    model="claude-3-sonnet",
    input_tokens=100,
    output_tokens=500
)
```

### Provider Configuration (`llm/providers.py`)

```python
from agent.llm import ProviderConfig, Provider

providers = {
    "anthropic": ProviderConfig(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        rate_limit=60,  # requests per minute
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015
    ),
    "openai": ProviderConfig(
        api_key=os.getenv("OPENAI_API_KEY"),
        models=["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        rate_limit=60
    ),
    "ollama": ProviderConfig(
        base_url="http://localhost:11434",
        models=["llama2", "mistral", "codellama"],
        is_local=True
    )
}
```

---

## Performance Utilities

Located in `agent/performance/`

### Lazy Loading (`performance/lazy.py`)

```python
from agent.performance import LazyLoader, lazy_property, LazyModule

# Lazy object initialization
heavy_resource = LazyLoader(lambda: load_heavy_resource())
resource = heavy_resource.get()  # Initialized on first access

# Lazy property
class MyClass:
    @lazy_property
    def expensive_data(self):
        return compute_expensive_data()

# Lazy module import
np = LazyModule('numpy')  # numpy imported on first use
```

### Response Cache (`performance/cache.py`)

```python
from agent.performance import ResponseCache, CacheConfig, cached

cache = ResponseCache(config=CacheConfig(
    max_size=1000,
    ttl_seconds=3600
))

# Manual caching
cache.set("key", value, ttl_seconds=600)
result = cache.get("key")

# Decorator
@cached(cache, ttl_seconds=300)
def expensive_function(arg):
    return compute(arg)

# Get stats
stats = cache.get_stats()
# Returns: {"hits": 150, "misses": 50, "hit_rate": 0.75, ...}
```

### Connection Pool (`performance/pool.py`)

```python
from agent.performance import AsyncConnectionPool, PoolConfig

pool = AsyncConnectionPool(
    factory=lambda: httpx.AsyncClient(),
    config=PoolConfig(
        min_size=2,
        max_size=20,
        max_idle_time=300
    ),
    cleanup=lambda c: c.aclose()
)

# Use connection
async with pool.connection() as client:
    response = await client.get(url)

# Get stats
stats = pool.get_stats()
```

### Parallel Execution (`performance/parallel.py`)

```python
from agent.performance import ParallelExecutor, run_parallel, Throttler

# Parallel map
executor = ParallelExecutor(max_workers=4)
results = await executor.map_async(process_item, items)

# Run parallel tasks
results = await run_parallel(
    tasks=[task1, task2, task3],
    max_concurrency=10,
    timeout=30.0
)

# Rate limiting
throttler = Throttler(rate=10, period=1.0)  # 10 req/sec
await throttler.acquire()
await make_request()
```

### Performance Monitor (`performance/utils.py`)

```python
from agent.performance import PerformanceMonitor, timed, timed_async

monitor = PerformanceMonitor()

# Context manager
with monitor.measure("operation"):
    do_something()

# Decorator
@timed("my_function")
def my_function():
    pass

@timed_async("async_op")
async def async_operation():
    pass

# Get stats
stats = monitor.get_all_stats()
# Returns: {"my_function": {"avg_time_ms": 150, "p95_ms": 200, ...}}
```

---

## Human-in-the-Loop

Located in `agent/human_proxy.py`

### HumanProxy Controller

```python
from agent.human_proxy import HumanProxy, ApprovalConfig

proxy = HumanProxy(config=ApprovalConfig(
    require_approval_for=["deploy", "delete", "billing"],
    auto_approve_timeout=300,  # 5 minutes
    escalation_contacts=["admin@example.com"]
))

# Request approval
approval = await proxy.request_approval(
    action="deploy",
    description="Deploy to production",
    context={"version": "1.2.0", "changes": [...]}
)

if approval.approved:
    await deploy()
else:
    logger.info(f"Rejected: {approval.reason}")
```

**ApprovalResult:**

```python
@dataclass
class ApprovalResult:
    approved: bool
    approver: Optional[str]
    reason: Optional[str]
    timestamp: datetime
    conditions: List[str] = field(default_factory=list)
```

---

## Error Handling

All JARVIS 2.0 components use consistent exception hierarchy:

```python
from agent.exceptions import (
    JarvisError,           # Base exception
    ConfigurationError,    # Invalid configuration
    FlowExecutionError,    # Flow engine errors
    MemoryError,           # Memory system errors
    LLMError,              # LLM provider errors
    RateLimitError,        # Rate limiting exceeded
    TimeoutError,          # Operation timeout
    ValidationError,       # Input validation failed
)
```

---

## Type Hints

All APIs are fully typed. Common types:

```python
from agent.types import (
    AgentID,           # str alias for agent identifiers
    TaskID,            # str alias for task identifiers
    Message,           # TypedDict for messages
    Context,           # Dict[str, Any] for context
    Callback,          # Callable[[Any], Awaitable[None]]
)
```

---

*API Reference - JARVIS 2.0*
