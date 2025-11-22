# Jarvis 2.0: Complete Roadmap & Competitive Analysis

**Version:** 2.0 Planning Document
**Date:** November 22, 2025
**Status:** Strategic Planning Phase

---

## Executive Summary

This document provides a comprehensive analysis of Jarvis against industry-leading open-source frameworks (CrewAI and AG2/AutoGen), identifies critical gaps, proposes solutions with implementation prompts, and ranks LLMs for optimal Jarvis performance.

**Key Finding:** Jarvis lacks **7 critical features** present in competitors that are essential for market competitiveness. This roadmap addresses each gap with specific implementation plans.

---

# Part 1: Competitive Gap Analysis

## 1.1 Feature Comparison Matrix

| Feature | CrewAI | AG2 (AutoGen) | **Jarvis Current** | Gap Level |
|---------|--------|---------------|-------------------|-----------|
| YAML Agent Config | Yes | No | **No** | Critical |
| Declarative Tasks | Yes | No | **No** | Critical |
| Memory System | 4 types | Hook-based | **Partial** | High |
| Flow/Router System | Yes (advanced) | Patterns | **No** | Critical |
| Tool Registration | Decorator-based | Function-based | **Manual** | High |
| Group Chat | Via Flows | Native | **No** | Critical |
| Observability Events | Yes | Yes | **Partial** | Medium |
| State Management | Pydantic | Dict-based | **Dict** | Low |
| Human-in-Loop | Manual | UserProxyAgent | **No** | High |
| Cost Tracking | No | No | **Yes** | Advantage |
| Git Integration | No | No | **Yes** | Advantage |
| Safety Scanning | No | No | **Yes** | Advantage |

---

## 1.2 CrewAI Features Jarvis Lacks (With Code)

### Gap 1: YAML-Based Agent Configuration

**CrewAI Pattern:**
```yaml
# config/agents.yaml
researcher:
  role: >
    Senior Data Researcher
  goal: >
    Uncover cutting-edge developments in {topic}
  backstory: >
    You're a seasoned researcher with a knack for uncovering
    the latest developments in {topic}.
  tools:
    - search_tool
    - web_scraper
  llm: gpt-4o
  max_iter: 15
  verbose: true
```

**Jarvis Current:** Agents hardcoded in Python

**Impact:** CrewAI users can modify agent behavior without code changes

---

### Gap 2: Declarative Task Definition

**CrewAI Pattern:**
```yaml
# config/tasks.yaml
research_task:
  description: >
    Conduct a thorough research about {topic}.
    Make sure you find any interesting and relevant information.
  expected_output: >
    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher
  output_file: research_output.md
```

**Jarvis Current:** Tasks generated dynamically by Manager LLM

**Impact:** Less predictable outputs, harder to reproduce

---

### Gap 3: Flow Router System

**CrewAI Pattern:**
```python
from crewai.flow.flow import Flow, listen, router, start, or_
from pydantic import BaseModel

class ContentState(BaseModel):
    topic: str = ""
    complexity: str = "medium"
    draft: str = ""
    final: str = ""

class ContentFlow(Flow[ContentState]):
    @start()
    def analyze_topic(self):
        # Analyze and set complexity
        self.state.complexity = self._determine_complexity()
        return self.state.topic

    @router(analyze_topic)
    def route_by_complexity(self):
        if self.state.complexity == "high":
            return "deep_research"
        elif self.state.complexity == "medium":
            return "standard_research"
        else:
            return "quick_summary"

    @listen("deep_research")
    def do_deep_research(self):
        # Complex multi-step research
        pass

    @listen("standard_research")
    def do_standard_research(self):
        # Standard research flow
        pass

    @listen(or_("deep_research", "standard_research", "quick_summary"))
    def generate_output(self):
        # All paths converge here
        pass
```

**Jarvis Current:** Fixed sequential/hierarchical process only

**Impact:** Cannot handle conditional branching or dynamic workflows

---

### Gap 4: Multi-Type Memory System

**CrewAI Pattern:**
```python
from crewai import Crew
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.entity.entity_memory import EntityMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable all memory types

    # Or customize each type:
    short_term_memory=ShortTermMemory(
        storage=ChromaDBStorage(collection_name="stm")
    ),
    long_term_memory=LongTermMemory(
        storage=SQLiteStorage(db_path="ltm.db")
    ),
    entity_memory=EntityMemory(
        storage=QdrantStorage(collection_name="entities")
    ),

    # Memory configuration
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
)
```

**Jarvis Current:** Single session-based memory with limited persistence

**Impact:** No entity tracking, limited context across sessions

---

## 1.3 AG2 (AutoGen) Features Jarvis Lacks (With Code)

### Gap 5: Orchestration Patterns

**AG2 Pattern:**
```python
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import (
    AutoPattern,
    DefaultPattern,
    RoundRobinPattern,
    RandomPattern,
    ManualPattern
)

llm_config = LLMConfig(api_type="openai", model="gpt-4o")

# Define specialized agents
planner = ConversableAgent(
    name="planner",
    system_message="You plan projects into actionable steps.",
    llm_config=llm_config
)

coder = ConversableAgent(
    name="coder",
    system_message="You write clean, efficient code.",
    llm_config=llm_config
)

reviewer = ConversableAgent(
    name="reviewer",
    system_message="You review code for bugs and improvements.",
    llm_config=llm_config
)

# AutoPattern - LLM selects next speaker
pattern = AutoPattern(
    initial_agent=planner,
    agents=[planner, coder, reviewer],
    group_manager_args={"llm_config": llm_config}
)

# Or RoundRobinPattern - Fixed rotation
pattern = RoundRobinPattern(
    initial_agent=planner,
    agents=[planner, coder, reviewer]
)

# Execute group chat
result, context, last_agent = initiate_group_chat(
    pattern=pattern,
    messages="Build a REST API for user management",
    max_rounds=15
)
```

**Jarvis Current:** Fixed Manager → Supervisor → Employee hierarchy

**Impact:** Cannot adapt orchestration strategy to task requirements

---

### Gap 6: Human-in-the-Loop Agent

**AG2 Pattern:**
```python
from autogen import UserProxyAgent, AssistantAgent

# Human proxy that can execute code and get user input
user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="TERMINATE",  # ALWAYS, TERMINATE, or NEVER
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "APPROVED" in x.get("content", ""),
    code_execution_config={
        "work_dir": "workspace",
        "use_docker": False
    }
)

assistant = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="You help users with coding tasks."
)

# Chat with human approval points
user_proxy.initiate_chat(
    assistant,
    message="Create a Python script that processes CSV files"
)
```

**Jarvis Current:** No structured human approval workflow

**Impact:** Cannot pause for user confirmation on critical steps

---

### Gap 7: Hookable Message Pipeline

**AG2 Pattern:**
```python
class CustomAgent(ConversableAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Register hooks at various pipeline stages
        self.register_hook(
            hookable_method="process_message_before_send",
            hook=self.log_outgoing_message
        )
        self.register_hook(
            hookable_method="process_received_message",
            hook=self.validate_incoming_message
        )
        self.register_hook(
            hookable_method="process_all_messages_before_reply",
            hook=self.add_context_to_messages
        )

    def log_outgoing_message(self, message):
        print(f"[SEND] {message[:100]}...")
        return message

    def validate_incoming_message(self, message, sender):
        if "forbidden" in message.lower():
            raise ValueError("Message contains forbidden content")
        return message

    def add_context_to_messages(self, messages):
        # Inject system context before LLM call
        context = {"role": "system", "content": "Current time: ..."}
        return [context] + messages
```

**Jarvis Current:** No message interception/modification hooks

**Impact:** Cannot inject middleware for logging, validation, or context

---

# Part 2: Jarvis 2.0 Architecture

## 2.1 Proposed Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JARVIS 2.0 ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         USER INTERFACE LAYER                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  Web Chat  │  │  REST API  │  │ WebSocket  │  │  CLI Interface │  │  │
│  │  │  (React)   │  │ (FastAPI)  │  │ (Real-time)│  │   (Optional)   │  │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │  │
│  └────────┼───────────────┼───────────────┼─────────────────┼───────────┘  │
│           └───────────────┴───────────────┴─────────────────┘              │
│                                    │                                        │
│  ┌─────────────────────────────────▼────────────────────────────────────┐  │
│  │                      JARVIS GATEWAY (NEW)                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │ Intent Analyzer │  │ Clarification   │  │ Human-in-Loop       │   │  │
│  │  │ (Enhanced)      │  │ Loop Manager    │  │ Controller          │   │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘   │  │
│  └───────────┼────────────────────┼──────────────────────┼──────────────┘  │
│              │                    │                      │                  │
│  ┌───────────▼────────────────────▼──────────────────────▼──────────────┐  │
│  │                        FLOW ENGINE (NEW)                              │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Flow Parser    │  │ Router Engine  │  │ State Manager          │  │  │
│  │  │ (YAML → Graph) │  │ (@router)      │  │ (Pydantic)             │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ @start()       │  │ @listen()      │  │ or_() / and_()         │  │  │
│  │  │ Decorator      │  │ Decorator      │  │ Combinators            │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                    ORCHESTRATION LAYER (ENHANCED)                     │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │                   PATTERN SELECTOR (NEW)                        │  │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │  │  │
│  │  │  │Sequential│ │ Hierarchi│ │AutoSelect│ │RoundRobin│ │ Manual│ │  │  │
│  │  │  │ Pattern  │ │ Pattern  │ │ Pattern  │ │ Pattern  │ │Pattern│ │  │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │ Agent Registry  │  │ Task Registry   │  │ Message Bus         │   │  │
│  │  │ (YAML Config)   │  │ (YAML Config)   │  │ (Enhanced)          │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                        AGENT LAYER (ENHANCED)                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  Manager   │  │ Supervisor │  │  Employee  │  │  UserProxy     │  │  │
│  │  │  Agent     │  │   Agent    │  │   Agent    │  │  Agent (NEW)   │  │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │  │
│  │        └───────────────┴───────────────┴─────────────────┘           │  │
│  │                                │                                      │  │
│  │  ┌─────────────────────────────▼─────────────────────────────────┐   │  │
│  │  │                    HOOK SYSTEM (NEW)                           │   │  │
│  │  │  pre_send │ post_receive │ pre_llm │ post_llm │ on_error      │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                        MEMORY LAYER (ENHANCED)                        │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Short-Term     │  │ Long-Term      │  │ Entity Memory          │  │  │
│  │  │ Memory (STM)   │  │ Memory (LTM)   │  │ (Knowledge Graph)      │  │  │
│  │  │ ChromaDB/RAM   │  │ SQLite/Postgres│  │ Neo4j/SQLite           │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Contextual     │  │ Embedding      │  │ Memory Events          │  │  │
│  │  │ Memory         │  │ Provider       │  │ & Observability        │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                          LLM LAYER (ENHANCED)                         │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    MODEL ROUTER (ENHANCED)                      │  │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │  │  │
│  │  │  │ OpenAI   │ │Anthropic │ │  Ollama  │ │ DeepSeek │ │ Qwen  │ │  │  │
│  │  │  │ GPT-4o   │ │ Claude   │ │ (Local)  │ │   V3     │ │  3    │ │  │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Cost Tracker   │  │ Response Cache │  │ Fallback Chain         │  │  │
│  │  │ (Existing)     │  │ (Existing)     │  │ (Enhanced)             │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                        TOOL & OUTPUT LAYER                            │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Tool Registry  │  │ File Writer    │  │ Git Integration        │  │  │
│  │  │ (@tool)        │  │ (Existing)     │  │ (Existing)             │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Safety Scanner │  │ Test Runner    │  │ Observability          │  │  │
│  │  │ (Existing)     │  │ (NEW)          │  │ Dashboard              │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Part 3: Implementation Roadmap

## Phase 1: Foundation (Weeks 1-2)

### 1.1 YAML Configuration System

**Priority:** P0 (Critical)
**Effort:** 3 days
**Files to Create:** `agent/config/agents.yaml`, `agent/config/tasks.yaml`, `agent/config_loader.py`

#### Implementation Prompt

```
Create a YAML-based configuration system for Jarvis agents and tasks.

Requirements:
1. Create agents.yaml schema supporting:
   - role, goal, backstory fields
   - tools list
   - llm model selection
   - max_iterations
   - verbose flag
   - custom attributes

2. Create tasks.yaml schema supporting:
   - description with variable templates {variable}
   - expected_output
   - agent assignment
   - output_file (optional)
   - dependencies (optional)
   - context (optional)

3. Create config_loader.py with:
   - load_agents(path) -> List[AgentConfig]
   - load_tasks(path) -> List[TaskConfig]
   - validate_config() -> bool
   - Variable substitution support

4. Integrate with existing JarvisChat class

Example usage:
```python
from config_loader import load_agents, load_tasks

agents = load_agents("config/agents.yaml")
tasks = load_tasks("config/tasks.yaml", variables={"topic": "AI agents"})
```

Use Pydantic for validation. Support both YAML and Python dict input.
```

#### Backtest Verification

```python
# tests/test_config_loader.py
import pytest
from config_loader import load_agents, load_tasks, ConfigValidationError

def test_load_agents_from_yaml():
    agents = load_agents("tests/fixtures/agents.yaml")
    assert len(agents) == 3
    assert agents[0].role == "researcher"
    assert "search_tool" in agents[0].tools

def test_load_tasks_with_variables():
    tasks = load_tasks(
        "tests/fixtures/tasks.yaml",
        variables={"topic": "machine learning"}
    )
    assert "machine learning" in tasks[0].description

def test_invalid_config_raises_error():
    with pytest.raises(ConfigValidationError):
        load_agents("tests/fixtures/invalid_agents.yaml")

def test_agent_task_assignment_valid():
    agents = load_agents("tests/fixtures/agents.yaml")
    tasks = load_tasks("tests/fixtures/tasks.yaml")
    for task in tasks:
        assert task.agent in [a.name for a in agents]
```

---

### 1.2 Flow Engine with Router

**Priority:** P0 (Critical)
**Effort:** 5 days
**Files to Create:** `agent/flow_engine.py`, `agent/decorators.py`

#### Implementation Prompt

```
Create a Flow Engine for Jarvis with conditional routing support.

Requirements:

1. Create decorators in decorators.py:
   - @start() - marks entry point method
   - @listen(event_name) - triggers on specific event
   - @router(source_method) - conditional routing based on return value
   - or_(*events) - trigger on any event
   - and_(*events) - trigger when all events complete

2. Create Flow base class in flow_engine.py:
```python
from pydantic import BaseModel
from typing import TypeVar, Generic

StateT = TypeVar('StateT', bound=BaseModel)

class Flow(Generic[StateT]):
    state: StateT

    def __init__(self, state_class: type[StateT]):
        self.state = state_class()
        self._graph = self._build_graph()

    def _build_graph(self) -> Dict[str, List[str]]:
        """Analyze decorated methods and build execution graph"""
        pass

    async def run(self, initial_input: Any = None) -> StateT:
        """Execute the flow from @start() to completion"""
        pass

    def visualize(self) -> str:
        """Return ASCII art of the flow graph"""
        pass
```

3. Support features:
   - Async execution
   - State persistence between methods
   - Error handling with retry
   - Timeout per step
   - Event emission for observability

Example usage:
```python
class WebsiteFlow(Flow[WebsiteState]):
    @start()
    def gather_requirements(self):
        return "analyze"

    @router(gather_requirements)
    def route_complexity(self):
        if self.state.complexity == "high":
            return "detailed_design"
        return "simple_design"

    @listen("detailed_design")
    def create_detailed_design(self):
        pass

    @listen("simple_design")
    def create_simple_design(self):
        pass

    @listen(or_("detailed_design", "simple_design"))
    def generate_code(self):
        pass
```
```

#### Backtest Verification

```python
# tests/test_flow_engine.py
import pytest
from flow_engine import Flow
from decorators import start, listen, router, or_
from pydantic import BaseModel

class TestState(BaseModel):
    value: int = 0
    path: str = ""

class SimpleFlow(Flow[TestState]):
    @start()
    def begin(self):
        self.state.value = 1
        return "next"

    @listen("next")
    def process(self):
        self.state.value += 1
        self.state.path = "completed"

@pytest.mark.asyncio
async def test_simple_flow_execution():
    flow = SimpleFlow(TestState)
    result = await flow.run()
    assert result.value == 2
    assert result.path == "completed"

class RouterFlow(Flow[TestState]):
    @start()
    def begin(self):
        return "route"

    @router(begin)
    def decide(self):
        if self.state.value > 5:
            return "high"
        return "low"

    @listen("high")
    def high_path(self):
        self.state.path = "high"

    @listen("low")
    def low_path(self):
        self.state.path = "low"

@pytest.mark.asyncio
async def test_router_low_path():
    flow = RouterFlow(TestState)
    flow.state.value = 3
    result = await flow.run()
    assert result.path == "low"

@pytest.mark.asyncio
async def test_router_high_path():
    flow = RouterFlow(TestState)
    flow.state.value = 10
    result = await flow.run()
    assert result.path == "high"

def test_flow_visualization():
    flow = RouterFlow(TestState)
    viz = flow.visualize()
    assert "begin" in viz
    assert "decide" in viz
    assert "->" in viz
```

---

### 1.3 Clarification Loop System

**Priority:** P0 (Critical)
**Effort:** 2 days
**Files to Modify:** `agent/jarvis_chat.py`

#### Implementation Prompt

```
Implement a clarification loop system in JarvisChat that asks follow-up questions
before executing complex tasks.

Requirements:

1. Add clarification state tracking:
```python
class ClarificationState:
    pending_task: Optional[str] = None
    questions: List[Dict] = []
    answers: Dict[str, str] = {}
    phase: str = "idle"  # idle, asking, ready
```

2. Modify handle_complex_task to:
   - Detect if task needs clarification (vague requests)
   - Generate 3-5 relevant questions using LLM
   - Store questions and await responses
   - Accumulate answers across multiple messages
   - Proceed to execution when sufficient detail gathered

3. Question generation prompt:
```
Given the user request: "{task}"

This request is vague. Generate 3-5 clarifying questions to understand:
- Specific requirements and features
- Design preferences (style, colors, layout)
- Technical constraints
- Target audience

Return JSON:
{
  "questions": [
    {"id": "q1", "text": "...", "category": "requirements|design|technical|audience"},
    ...
  ],
  "reasoning": "why these questions are important"
}
```

4. Detection criteria for needing clarification:
   - Task description under 50 characters
   - No specific technical details mentioned
   - Ambiguous scope (e.g., "make a website", "build an app")
   - User explicitly asks "help me" or similar

5. Allow user to bypass with phrases like:
   - "just do it"
   - "proceed anyway"
   - "skip questions"
```

#### Backtest Verification

```python
# tests/test_clarification.py
import pytest
from jarvis_chat import JarvisChat

@pytest.mark.asyncio
async def test_vague_request_triggers_clarification():
    jarvis = JarvisChat()
    response = await jarvis.handle_message("make me a website")

    assert response["metadata"]["type"] == "clarification_request"
    assert len(response["metadata"]["questions"]) >= 3

@pytest.mark.asyncio
async def test_detailed_request_skips_clarification():
    jarvis = JarvisChat()
    detailed_request = """
    Create a portfolio website with:
    - Dark theme
    - 5 pages: Home, About, Projects, Blog, Contact
    - React with Tailwind CSS
    - Mobile responsive
    """
    response = await jarvis.handle_message(detailed_request)

    assert response["metadata"]["type"] != "clarification_request"

@pytest.mark.asyncio
async def test_bypass_clarification():
    jarvis = JarvisChat()
    await jarvis.handle_message("make me a website")
    response = await jarvis.handle_message("just do it")

    assert response["metadata"]["type"] != "clarification_request"

@pytest.mark.asyncio
async def test_answer_accumulation():
    jarvis = JarvisChat()
    await jarvis.handle_message("make me a website")
    await jarvis.handle_message("It should be about cats")
    await jarvis.handle_message("Blue and white colors")
    response = await jarvis.handle_message("Modern style")

    # After enough answers, should proceed or ask remaining questions
    assert jarvis.clarification_state.answers
```

---

## Phase 2: Orchestration Patterns (Weeks 3-4)

### 2.1 Pattern-Based Orchestration

**Priority:** P1 (High)
**Effort:** 4 days
**Files to Create:** `agent/patterns/`, `agent/pattern_selector.py`

#### Implementation Prompt

```
Create an orchestration pattern system supporting multiple agent coordination strategies.

Requirements:

1. Create base Pattern class:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class PatternConfig:
    max_rounds: int = 10
    timeout_seconds: int = 300
    allow_parallel: bool = False

class Pattern(ABC):
    def __init__(self, agents: List[Agent], config: PatternConfig):
        self.agents = agents
        self.config = config
        self.current_round = 0
        self.history: List[Message] = []

    @abstractmethod
    def select_next_agent(self, context: Dict) -> Optional[Agent]:
        """Determine which agent speaks next"""
        pass

    @abstractmethod
    def should_terminate(self, last_message: Message) -> bool:
        """Check if conversation should end"""
        pass

    async def run(self, initial_message: str) -> PatternResult:
        """Execute the pattern"""
        pass
```

2. Implement pattern types:

SequentialPattern:
- Agents speak in defined order
- Each agent speaks once per round
- Terminates after all agents complete

HierarchicalPattern (existing behavior):
- Manager → Supervisor → Employee
- Maintains current Jarvis behavior

AutoSelectPattern:
- LLM-based agent selection
- Considers conversation context and agent descriptions
- Most flexible but highest cost

RoundRobinPattern:
- Fixed rotation through agents
- Useful for review/feedback cycles

ManualPattern:
- Always returns to user for next selection
- Maximum human control

3. Create PatternSelector that auto-recommends patterns:
```python
class PatternSelector:
    def recommend(self, task: str, agents: List[Agent]) -> Pattern:
        """Analyze task and recommend best pattern"""
        # Simple tasks -> Sequential
        # Code review -> RoundRobin
        # Complex/ambiguous -> AutoSelect
        # Critical operations -> Manual
```

4. Integrate with existing orchestrator as drop-in enhancement
```

#### Backtest Verification

```python
# tests/test_patterns.py
import pytest
from patterns import (
    SequentialPattern, HierarchicalPattern,
    AutoSelectPattern, RoundRobinPattern
)
from pattern_selector import PatternSelector

def test_sequential_pattern_order():
    agents = [MockAgent("A"), MockAgent("B"), MockAgent("C")]
    pattern = SequentialPattern(agents)

    order = []
    for _ in range(3):
        agent = pattern.select_next_agent({})
        order.append(agent.name)
        pattern.history.append(MockMessage(agent.name))

    assert order == ["A", "B", "C"]

def test_round_robin_cycles():
    agents = [MockAgent("A"), MockAgent("B")]
    pattern = RoundRobinPattern(agents)

    selections = []
    for _ in range(4):
        agent = pattern.select_next_agent({})
        selections.append(agent.name)
        pattern.history.append(MockMessage(agent.name))

    assert selections == ["A", "B", "A", "B"]

@pytest.mark.asyncio
async def test_auto_select_pattern():
    agents = [
        MockAgent("planner", "Plans projects"),
        MockAgent("coder", "Writes code"),
        MockAgent("reviewer", "Reviews code")
    ]
    pattern = AutoSelectPattern(agents, llm_config=mock_llm_config)

    # After planning message, should select coder
    pattern.history.append(MockMessage("planner", "Here's the plan: ..."))
    next_agent = pattern.select_next_agent({})
    assert next_agent.name == "coder"

def test_pattern_selector_simple_task():
    selector = PatternSelector()
    pattern = selector.recommend(
        task="Format this JSON file",
        agents=[MockAgent("formatter")]
    )
    assert isinstance(pattern, SequentialPattern)

def test_pattern_selector_complex_task():
    selector = PatternSelector()
    pattern = selector.recommend(
        task="Build a full-stack e-commerce platform",
        agents=[MockAgent("architect"), MockAgent("backend"), MockAgent("frontend")]
    )
    assert isinstance(pattern, AutoSelectPattern)
```

---

### 2.2 Human-in-the-Loop Controller

**Priority:** P1 (High)
**Effort:** 3 days
**Files to Create:** `agent/human_proxy.py`

#### Implementation Prompt

```
Create a Human-in-the-Loop controller for Jarvis that enables user approval workflows.

Requirements:

1. Create UserProxyAgent class:
```python
class UserProxyAgent:
    """Agent that represents human user in the workflow"""

    def __init__(
        self,
        name: str = "user",
        input_mode: str = "APPROVAL_REQUIRED",  # ALWAYS, APPROVAL_REQUIRED, NEVER
        approval_keywords: List[str] = ["APPROVED", "LGTM", "proceed"],
        rejection_keywords: List[str] = ["REJECTED", "stop", "redo"],
        timeout_seconds: int = 300,
        default_on_timeout: str = "reject"
    ):
        pass

    async def get_human_input(self, context: Dict) -> str:
        """Wait for human input via configured channel"""
        pass

    def check_approval(self, message: str) -> ApprovalStatus:
        """Parse message for approval/rejection signals"""
        pass
```

2. Create approval checkpoints:
```python
class ApprovalCheckpoint:
    """Define points where human approval is required"""

    PLAN_REVIEW = "plan_review"           # After manager creates plan
    CODE_REVIEW = "code_review"           # Before writing files
    DEPLOY_APPROVAL = "deploy_approval"   # Before deployment
    COST_WARNING = "cost_warning"         # When cost exceeds threshold

@dataclass
class CheckpointConfig:
    enabled_checkpoints: List[str]
    auto_approve_after: int = 0  # seconds, 0 = never auto-approve
    notification_channel: str = "websocket"
```

3. Integrate with orchestrator:
```python
class OrchestratorWithApproval:
    async def run_with_approval(self, task: str):
        # ... planning phase ...

        if CheckpointConfig.PLAN_REVIEW in self.checkpoints:
            approval = await self.user_proxy.request_approval(
                checkpoint=CheckpointConfig.PLAN_REVIEW,
                content=plan_summary,
                options=["Approve", "Modify", "Reject"]
            )

            if approval.status == "rejected":
                return {"status": "cancelled", "reason": approval.feedback}
            elif approval.status == "modified":
                task = self._merge_modifications(task, approval.feedback)
```

4. WebSocket integration for real-time approval requests
```

#### Backtest Verification

```python
# tests/test_human_proxy.py
import pytest
from human_proxy import UserProxyAgent, ApprovalCheckpoint

@pytest.mark.asyncio
async def test_approval_detection():
    proxy = UserProxyAgent()

    assert proxy.check_approval("APPROVED").is_approved
    assert proxy.check_approval("LGTM looks good").is_approved
    assert proxy.check_approval("proceed with changes").is_approved

    assert proxy.check_approval("REJECTED").is_rejected
    assert proxy.check_approval("stop this").is_rejected

@pytest.mark.asyncio
async def test_approval_timeout_default_reject():
    proxy = UserProxyAgent(timeout_seconds=1, default_on_timeout="reject")

    # Simulate no input within timeout
    result = await proxy.get_human_input_with_timeout({})
    assert result.is_rejected
    assert "timeout" in result.reason.lower()

@pytest.mark.asyncio
async def test_checkpoint_integration():
    orchestrator = MockOrchestratorWithApproval(
        checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
    )

    # Mock user approval
    orchestrator.user_proxy.queue_response("APPROVED")

    result = await orchestrator.run_with_approval("Build a website")
    assert result["status"] != "cancelled"

@pytest.mark.asyncio
async def test_checkpoint_rejection_stops_execution():
    orchestrator = MockOrchestratorWithApproval(
        checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
    )

    orchestrator.user_proxy.queue_response("REJECTED - too expensive")

    result = await orchestrator.run_with_approval("Build a website")
    assert result["status"] == "cancelled"
    assert "expensive" in result["reason"]
```

---

## Phase 3: Memory & Intelligence (Weeks 5-6)

### 3.1 Multi-Type Memory System

**Priority:** P1 (High)
**Effort:** 5 days
**Files to Create:** `agent/memory/`, multiple files

#### Implementation Prompt

```
Create a comprehensive memory system with four memory types.

Requirements:

1. Short-Term Memory (STM):
```python
class ShortTermMemory:
    """RAG-based memory for current conversation context"""

    def __init__(self, storage: MemoryStorage, max_items: int = 100):
        self.storage = storage  # ChromaDB, Qdrant, or in-memory
        self.max_items = max_items

    def add(self, content: str, metadata: Dict = None):
        """Add item with auto-embedding"""
        pass

    def search(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Semantic search"""
        pass

    def clear(self):
        """Clear for new conversation"""
        pass
```

2. Long-Term Memory (LTM):
```python
class LongTermMemory:
    """Persistent memory across sessions"""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    def store_task_result(self, task_id: str, result: Dict):
        """Store completed task for future reference"""
        pass

    def get_similar_tasks(self, description: str) -> List[TaskResult]:
        """Find similar past tasks"""
        pass

    def get_user_preferences(self, user_id: str) -> Dict:
        """Retrieve learned user preferences"""
        pass
```

3. Entity Memory:
```python
class EntityMemory:
    """Track entities mentioned across conversations"""

    def __init__(self, storage: GraphStorage):
        self.storage = storage  # Neo4j, SQLite graph, or dict

    def extract_entities(self, text: str) -> List[Entity]:
        """NER extraction using LLM or spaCy"""
        pass

    def add_entity(self, entity: Entity, context: str):
        """Add or update entity with context"""
        pass

    def get_entity_context(self, entity_name: str) -> EntityContext:
        """Get all known information about entity"""
        pass

    def get_related_entities(self, entity_name: str) -> List[Entity]:
        """Get entities related to this one"""
        pass
```

4. Contextual Memory:
```python
class ContextualMemory:
    """Situation-aware memory retrieval"""

    def __init__(self, stm: ShortTermMemory, ltm: LongTermMemory, entity: EntityMemory):
        self.stm = stm
        self.ltm = ltm
        self.entity = entity

    def build_context(self, current_input: str, task_type: str) -> Context:
        """Build rich context from all memory sources"""
        # 1. Get relevant STM items
        # 2. Find similar past tasks from LTM
        # 3. Extract and enrich entities
        # 4. Combine into coherent context
        pass
```

5. Unified MemoryManager:
```python
class MemoryManager:
    def __init__(self, config: MemoryConfig):
        self.stm = ShortTermMemory(config.stm_storage)
        self.ltm = LongTermMemory(config.ltm_storage)
        self.entity = EntityMemory(config.entity_storage)
        self.contextual = ContextualMemory(self.stm, self.ltm, self.entity)

    def process_message(self, message: str, role: str):
        """Process incoming message across all memory types"""
        pass

    def get_context_for_llm(self, query: str) -> str:
        """Format memory context for LLM prompt"""
        pass
```
```

#### Backtest Verification

```python
# tests/test_memory_system.py
import pytest
from memory import ShortTermMemory, LongTermMemory, EntityMemory, MemoryManager

def test_stm_add_and_search():
    stm = ShortTermMemory(storage=InMemoryStorage())

    stm.add("The user wants a blue website", {"type": "preference"})
    stm.add("React is the preferred framework", {"type": "technical"})
    stm.add("Contact page should have a form", {"type": "requirement"})

    results = stm.search("what color does user want", top_k=1)
    assert "blue" in results[0].content.lower()

def test_ltm_similar_tasks():
    ltm = LongTermMemory(storage=SQLiteStorage(":memory:"))

    ltm.store_task_result("task_1", {
        "description": "Build portfolio website",
        "result": "success",
        "files": ["index.html", "style.css"]
    })

    similar = ltm.get_similar_tasks("Create a personal website")
    assert len(similar) > 0
    assert "portfolio" in similar[0].description.lower()

def test_entity_extraction_and_retrieval():
    entity = EntityMemory(storage=DictStorage())

    entity.extract_and_add("John from Acme Corp wants a CRM system")

    john = entity.get_entity_context("John")
    assert john is not None
    assert "Acme Corp" in str(john.related_entities)

def test_memory_manager_integration():
    manager = MemoryManager(config=default_memory_config)

    manager.process_message("I'm building a website for my bakery", "user")
    manager.process_message("I'll use Next.js with Tailwind", "assistant")
    manager.process_message("The bakery is called Sweet Dreams", "user")

    context = manager.get_context_for_llm("What framework are we using?")
    assert "Next.js" in context
    assert "Sweet Dreams" in context
```

---

## Phase 4: LLM & Tools (Weeks 7-8)

### 4.1 Enhanced Model Router with Local LLM Support

**Priority:** P1 (High)
**Effort:** 4 days
**Files to Modify:** `agent/llm.py`, `agent/model_router.py`

#### Implementation Prompt

```
Enhance the model router to support multiple LLM providers including local models.

Requirements:

1. Provider abstraction:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass

    @abstractmethod
    def get_cost_per_token(self) -> Tuple[float, float]:
        """Return (input_cost, output_cost) per 1K tokens"""
        pass

class OpenAIProvider(LLMProvider):
    pass

class AnthropicProvider(LLMProvider):
    pass

class OllamaProvider(LLMProvider):
    """Local LLM via Ollama"""
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.1"):
        pass

class DeepSeekProvider(LLMProvider):
    pass

class QwenProvider(LLMProvider):
    pass
```

2. Intelligent routing:
```python
class EnhancedModelRouter:
    def __init__(self, config: RouterConfig):
        self.providers = self._init_providers(config)
        self.routing_strategy = config.strategy  # cost, quality, hybrid, local_first

    def select_model(
        self,
        task_type: str,  # planning, coding, review, simple
        complexity: str,  # low, medium, high
        cost_budget: float = None,
        require_local: bool = False
    ) -> Tuple[LLMProvider, str]:
        """Select best provider and model for task"""

        if require_local or self.routing_strategy == "local_first":
            if self.ollama_available:
                return self.providers["ollama"], "llama3.1:70b"

        if self.routing_strategy == "cost":
            return self._select_cheapest(task_type, complexity)
        elif self.routing_strategy == "quality":
            return self._select_best_quality(task_type, complexity)
        else:  # hybrid
            return self._select_balanced(task_type, complexity, cost_budget)
```

3. Fallback chain:
```python
class FallbackChain:
    def __init__(self, primary: LLMProvider, fallbacks: List[LLMProvider]):
        self.chain = [primary] + fallbacks

    async def chat_with_fallback(self, messages: List[Dict], **kwargs) -> str:
        last_error = None
        for provider in self.chain:
            try:
                return await provider.chat(messages, **kwargs)
            except Exception as e:
                last_error = e
                continue
        raise last_error
```

4. Cost tracking per provider
5. Automatic provider health checks
```

---

### 4.2 Tool Registration System

**Priority:** P2 (Medium)
**Effort:** 3 days
**Files to Create:** `agent/tool_registry.py`

#### Implementation Prompt

```
Create a decorator-based tool registration system.

Requirements:

1. Tool decorator:
```python
def tool(
    name: str = None,
    description: str = None,
    agents: List[str] = None  # Which agents can use this tool
):
    """Decorator to register a function as an agent tool"""
    def decorator(func):
        # Extract parameter info from type hints
        # Generate JSON schema for LLM
        # Register in global tool registry
        return func
    return decorator

# Usage:
@tool(
    name="search_web",
    description="Search the web for information",
    agents=["researcher"]
)
def search_web(
    query: Annotated[str, "The search query"],
    num_results: Annotated[int, "Number of results"] = 5
) -> str:
    # Implementation
    pass
```

2. Tool registry:
```python
class ToolRegistry:
    _tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool_def: ToolDefinition):
        pass

    @classmethod
    def get_tools_for_agent(cls, agent_name: str) -> List[ToolDefinition]:
        pass

    @classmethod
    def get_tool_schemas(cls, agent_name: str) -> List[Dict]:
        """Get OpenAI function calling format schemas"""
        pass

    @classmethod
    def execute_tool(cls, name: str, **kwargs) -> Any:
        pass
```

3. Built-in tools to implement:
   - web_search
   - file_read
   - file_write
   - code_execute (sandboxed)
   - http_request
```

---

# Part 4: LLM Analysis & Ranking

## 4.1 LLM Comparison for Jarvis Agent System

| Model | Provider | Strengths | Weaknesses | Best For | Cost (per 1M tokens) |
|-------|----------|-----------|------------|----------|---------------------|
| **GPT-4o** | OpenAI | Balanced performance, reliable tool use, multimodal | Expensive, rate limits | Manager role, complex reasoning | $2.50 / $10.00 |
| **Claude 3.5 Sonnet** | Anthropic | Excellent coding (49% SWE-bench), long context | Less tool use docs | Employee (coding), reviews | $3.00 / $15.00 |
| **DeepSeek V3** | DeepSeek | Outstanding coding, cost-effective MoE, 671B params | Chinese company concerns | Employee (coding), high-volume | $0.27 / $1.10 |
| **Llama 3.1 70B** | Meta (Local) | Free, private, good quality | Needs GPU hardware | Self-hosted operations | Free (compute only) |
| **Qwen 2.5 72B** | Alibaba (Local) | Competitive benchmarks, MoE efficient | Less English training | Local alternative | Free (compute only) |
| **GPT-4o-mini** | OpenAI | Very cheap, fast, good enough | Limited complex reasoning | Supervisor, simple tasks | $0.15 / $0.60 |

## 4.2 Recommended Jarvis Configuration

### Hybrid Strategy (Recommended)

```yaml
# config/llm_config.yaml
routing_strategy: hybrid

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    models:
      - gpt-4o
      - gpt-4o-mini

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    models:
      - claude-3-5-sonnet-20241022

  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    models:
      - deepseek-chat

  ollama:
    host: http://localhost:11434
    models:
      - llama3.1:70b
      - qwen2.5:72b

role_assignments:
  manager:
    primary: gpt-4o
    fallback: claude-3-5-sonnet

  supervisor:
    primary: gpt-4o-mini
    fallback: deepseek-chat

  employee:
    coding:
      primary: claude-3-5-sonnet
      fallback: deepseek-chat
    general:
      primary: gpt-4o-mini
      fallback: llama3.1:70b

cost_optimization:
  prefer_local_for:
    - simple_queries
    - code_formatting
    - test_generation

  use_premium_for:
    - architecture_decisions
    - security_reviews
    - final_code_review
```

## 4.3 LLM Ranking for Jarvis Roles

### Rank 1: Claude 3.5 Sonnet (Employee - Coding)
- **Score:** 9.2/10
- **Rationale:** 49% SWE-bench score, excellent at generating clean code
- **Best for:** Code generation, code review, debugging
- **Cost efficiency:** High quality per dollar for coding tasks

### Rank 2: GPT-4o (Manager Role)
- **Score:** 9.0/10
- **Rationale:** Best reasoning, reliable JSON output, excellent planning
- **Best for:** Planning, complex decisions, multi-step reasoning
- **Cost efficiency:** Worth premium for critical decisions

### Rank 3: DeepSeek V3 (Cost-Effective Coding)
- **Score:** 8.7/10
- **Rationale:** Near GPT-4 quality at 1/10th the cost
- **Best for:** High-volume coding tasks, bulk operations
- **Cost efficiency:** Best cost/quality ratio

### Rank 4: Llama 3.1 70B (Self-Hosted)
- **Score:** 8.3/10
- **Rationale:** Free, private, good quality for most tasks
- **Best for:** Privacy-sensitive work, offline operation
- **Cost efficiency:** Best for high-volume if you have GPUs

### Rank 5: GPT-4o-mini (Supervisor/Simple Tasks)
- **Score:** 8.0/10
- **Rationale:** Extremely cheap, fast, good for structured tasks
- **Best for:** Classification, formatting, simple generation
- **Cost efficiency:** Best for high-volume simple tasks

---

# Part 5: Implementation Timeline

## 5.1 Complete Roadmap

```
Week 1-2: Foundation
├── Day 1-3: YAML Configuration System
├── Day 4-8: Flow Engine with Router
└── Day 9-10: Clarification Loop System

Week 3-4: Orchestration
├── Day 11-14: Pattern-Based Orchestration
├── Day 15-17: Human-in-the-Loop Controller
└── Day 18-20: Pattern Selection Intelligence

Week 5-6: Memory & Intelligence
├── Day 21-25: Multi-Type Memory System
└── Day 26-30: Memory-Enhanced Prompts

Week 7-8: LLM & Tools
├── Day 31-34: Enhanced Model Router
├── Day 35-37: Tool Registration System
└── Day 38-40: Provider Integrations

Week 9-10: Polish & Testing
├── Day 41-45: Integration Testing
├── Day 46-48: Performance Optimization
└── Day 49-50: Documentation
```

## 5.2 Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Task completion rate | ~60% | 90%+ | Manager approval rate |
| User clarification needed | 0% | 80%+ | Questions before complex tasks |
| Memory retention | 0 sessions | 30+ days | LTM persistence |
| Cost per task | ~$0.10 | ~$0.05 | With local LLM routing |
| Time to first response | N/A | <2s | Clarification question |

---

# Part 6: Risk Analysis

## 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Flow engine complexity | Medium | High | Start with simple patterns, iterate |
| Memory system overhead | Medium | Medium | Lazy loading, async operations |
| Local LLM quality | Low | Medium | Maintain cloud fallback |
| Pattern selection errors | Medium | Medium | Allow manual override |

## 6.2 Competitive Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CrewAI adds cost tracking | High | Medium | Focus on UX differentiators |
| AG2 improves UX | Medium | Medium | Build community, documentation |
| New entrant | Medium | High | Speed to market, unique features |

---

# Appendix A: File Structure for Jarvis 2.0

```
agent/
├── config/
│   ├── agents.yaml              # NEW: Agent definitions
│   ├── tasks.yaml               # NEW: Task definitions
│   └── llm_config.yaml          # NEW: LLM provider config
├── flow/
│   ├── __init__.py
│   ├── decorators.py            # NEW: @start, @listen, @router
│   ├── flow_engine.py           # NEW: Flow execution engine
│   └── state.py                 # NEW: Pydantic state models
├── patterns/
│   ├── __init__.py
│   ├── base.py                  # NEW: Pattern base class
│   ├── sequential.py            # NEW
│   ├── hierarchical.py          # NEW (existing behavior)
│   ├── auto_select.py           # NEW
│   ├── round_robin.py           # NEW
│   └── manual.py                # NEW
├── memory/
│   ├── __init__.py
│   ├── short_term.py            # NEW: STM with RAG
│   ├── long_term.py             # NEW: SQLite persistence
│   ├── entity.py                # NEW: Entity tracking
│   ├── contextual.py            # NEW: Combined retrieval
│   └── storage/
│       ├── chroma.py            # NEW
│       ├── sqlite.py            # NEW
│       └── qdrant.py            # NEW
├── tools/
│   ├── __init__.py
│   ├── registry.py              # NEW: Tool registration
│   ├── web_search.py            # NEW
│   ├── code_executor.py         # NEW
│   └── http_client.py           # NEW
├── providers/
│   ├── __init__.py
│   ├── base.py                  # NEW: Provider ABC
│   ├── openai.py                # ENHANCED
│   ├── anthropic.py             # NEW
│   ├── deepseek.py              # NEW
│   ├── ollama.py                # NEW
│   └── qwen.py                  # NEW
├── human_proxy.py               # NEW: Human-in-the-loop
├── config_loader.py             # NEW: YAML config loader
├── pattern_selector.py          # NEW: Auto pattern selection
├── jarvis_chat.py               # ENHANCED: Clarification loop
├── orchestrator.py              # ENHANCED: Pattern support
└── llm.py                       # ENHANCED: Multi-provider
```

---

*Document Version: 1.0*
*Last Updated: November 22, 2025*
*Author: Claude Code Analysis*
