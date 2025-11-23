# JARVIS 2.0 Developer Guide

**Version:** 2.0.0
**Date:** November 23, 2025

Complete developer reference for building with and extending JARVIS 2.0.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Adding New Agents](#adding-new-agents)
5. [Creating Custom Tools](#creating-custom-tools)
6. [Flow Engine Development](#flow-engine-development)
7. [Council System Integration](#council-system-integration)
8. [Memory System](#memory-system)
9. [Voice System Development](#voice-system-development)
10. [Vision System Development](#vision-system-development)
11. [API Development](#api-development)
12. [Testing](#testing)
13. [Best Practices](#best-practices)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        JARVIS 2.0                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Voice   │  │  Vision  │  │   Chat   │  │Dashboard │        │
│  │   API    │  │   API    │  │   API    │  │   API    │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│  ┌────┴─────────────┴─────────────┴─────────────┴────┐         │
│  │              JARVIS (Master Orchestrator)          │         │
│  └────┬─────────────┬─────────────┬─────────────┬────┘         │
│       │             │             │             │               │
│  ┌────┴────┐  ┌─────┴────┐  ┌─────┴────┐  ┌─────┴────┐        │
│  │ Council │  │   Flow   │  │  Pattern │  │  Memory  │        │
│  │ System  │  │  Engine  │  │ Selector │  │  System  │        │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │             │             │               │
│  ┌────┴─────────────┴─────────────┴─────────────┴────┐         │
│  │                   Agent Pool                       │         │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │         │
│  │  │ Manager │ │Supervisor│ │  Code   │ │  Test   │ │         │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ │         │
│  └───────────────────────────────────────────────────┘         │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────┐         │
│  │              LLM Router (Multi-Provider)           │         │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │         │
│  │  │Anthropic│ │ OpenAI  │ │DeepSeek │ │ Ollama  │ │         │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ │         │
│  └───────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
agent/
├── __init__.py
├── config_loader.py          # YAML configuration loader
├── jarvis_chat.py            # Main JARVIS chat interface
├── jarvis_voice.py           # Voice system (TTS/STT)
├── jarvis_vision.py          # Vision system (image analysis)
│
├── council/                  # Council voting system
│   ├── __init__.py
│   ├── models.py             # Councillor, Vote models
│   ├── voting.py             # Voting sessions
│   ├── happiness.py          # Happiness tracking
│   ├── factory.py            # Councillor spawning/firing
│   └── orchestrator.py       # Council orchestration
│
├── flow/                     # Flow engine
│   ├── __init__.py
│   ├── decorators.py         # @start, @listen, @router
│   ├── engine.py             # Flow execution engine
│   ├── graph.py              # Flow graph construction
│   ├── state.py              # Pydantic state models
│   └── events.py             # Event bus
│
├── patterns/                 # Orchestration patterns
│   ├── __init__.py
│   ├── base.py               # Pattern base class
│   ├── sequential.py         # Sequential pattern
│   ├── hierarchical.py       # Manager → Supervisor → Employee
│   ├── auto_select.py        # LLM-driven selection
│   ├── round_robin.py        # Rotating agents
│   └── manual.py             # Human selection
│
├── memory/                   # Memory system
│   ├── __init__.py
│   ├── short_term.py         # RAG-based short-term
│   ├── long_term.py          # Persistent storage
│   ├── entity.py             # Knowledge graph
│   └── manager.py            # Unified interface
│
├── llm/                      # LLM providers
│   ├── __init__.py
│   ├── providers.py          # Provider implementations
│   ├── enhanced_router.py    # Intelligent routing
│   └── config.py             # LLM configuration
│
├── performance/              # Performance optimization
│   ├── __init__.py
│   ├── lazy.py               # Lazy loading
│   ├── cache.py              # Response caching
│   ├── pool.py               # Connection pooling
│   ├── parallel.py           # Parallel execution
│   └── utils.py              # Timing, retry utilities
│
├── webapp/                   # Web application
│   ├── app.py                # FastAPI application
│   ├── templates/            # Jinja2 templates
│   │   ├── jarvis.html       # JARVIS chat interface
│   │   └── ...
│   └── static/               # Static assets
│
├── voice_api.py              # Voice REST endpoints
├── vision_api.py             # Vision REST endpoints
├── agents_api.py             # Agent status endpoints
│
├── tool_registry.py          # Tool registration system
├── human_proxy.py            # Human-in-the-loop controller
├── approval_engine.py        # Approval workflow engine
│
└── tests/
    ├── unit/
    └── integration/
```

---

## Core Components

### Config Loader

```python
from agent.config_loader import load_agents, load_tasks, load_llm_config

# Load agent definitions from YAML
agents = load_agents()  # Returns dict of Agent objects

# Load task templates
tasks = load_tasks()  # Returns dict of Task objects

# Load LLM configuration
llm_config = load_llm_config()  # Returns LLMConfig object
```

### LLM Router

```python
from agent.llm import get_router

router = get_router()

# Simple completion
response = await router.complete(
    messages=[{"role": "user", "content": "Hello"}],
    task_type="general"  # Enables intelligent routing
)

# With specific model
response = await router.complete(
    messages=[...],
    provider="anthropic",
    model="claude-3-opus"
)

# Health check
health = await router.health_check()
```

### Pattern Selector

```python
from agent.patterns import get_pattern
from agent.pattern_selector import select_pattern

# Auto-select best pattern
pattern_name = select_pattern(task)  # Returns "sequential", "hierarchical", etc.

# Get pattern instance
pattern = get_pattern(pattern_name)

# Execute with pattern
result = await pattern.execute(task, agents)
```

---

## Adding New Agents

### Method 1: YAML Configuration (Recommended)

```yaml
# config/agents.yaml
agents:
  - id: my_custom_agent
    name: "Custom Agent"
    role: "Specialist"
    goal: "Perform specialized tasks"
    backstory: |
      This agent specializes in a specific domain...
    specialization: custom
    tools:
      - my_tool_1
      - my_tool_2
    llm_config:
      provider: anthropic
      model: claude-3-sonnet
      temperature: 0.5
    constraints:
      - "Always verify inputs"
      - "Follow security best practices"
    permissions:
      can_execute_code: true
      can_access_web: false
```

### Method 2: Python Code

```python
from agent.models import Agent, LLMConfig

custom_agent = Agent(
    id="my_custom_agent",
    name="Custom Agent",
    role="Specialist",
    goal="Perform specialized tasks",
    backstory="This agent specializes in...",
    specialization="custom",
    tools=["my_tool_1", "my_tool_2"],
    llm_config=LLMConfig(
        provider="anthropic",
        model="claude-3-sonnet",
        temperature=0.5
    )
)

# Register with agent pool
from agent.pool import register_agent
register_agent(custom_agent)
```

---

## Creating Custom Tools

### Tool Registry

```python
from agent.tool_registry import register_tool, Tool

@register_tool(
    name="web_scraper",
    description="Scrapes content from a web page",
    parameters={
        "url": {"type": "string", "description": "URL to scrape"},
        "selector": {"type": "string", "description": "CSS selector", "optional": True}
    }
)
async def web_scraper(url: str, selector: str = None) -> dict:
    """Scrape content from a web page."""
    import aiohttp
    from bs4 import BeautifulSoup

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()

    soup = BeautifulSoup(html, 'html.parser')

    if selector:
        elements = soup.select(selector)
        return {"content": [el.get_text() for el in elements]}

    return {"content": soup.get_text()}
```

### Tool with Validation

```python
from pydantic import BaseModel, HttpUrl
from agent.tool_registry import register_tool

class WebScraperInput(BaseModel):
    url: HttpUrl
    selector: str = None
    timeout: int = 30

@register_tool(
    name="validated_scraper",
    description="Scrapes with validation",
    input_model=WebScraperInput
)
async def validated_scraper(input: WebScraperInput) -> dict:
    # Input is already validated
    ...
```

---

## Flow Engine Development

### Creating a Flow

```python
from agent.flow import start, listen, router, FlowEngine, FlowState

class FeatureFlowState(FlowState):
    feature_name: str = ""
    requirements: list = []
    code_path: str = ""
    status: str = "pending"

@start()
async def begin_feature(state: FeatureFlowState):
    """Entry point for feature development."""
    state.status = "analyzing"
    return await analyze_requirements(state)

@router(begin_feature)
def route_complexity(result):
    """Route based on complexity."""
    if len(result.requirements) > 5:
        return "complex_handler"
    return "simple_handler"

@listen("complex_handler")
async def handle_complex(state: FeatureFlowState):
    """Handle complex features."""
    # Break down into sub-tasks
    state.status = "planning"
    return await create_detailed_plan(state)

@listen("simple_handler")
async def handle_simple(state: FeatureFlowState):
    """Handle simple features."""
    state.status = "implementing"
    return await implement_directly(state)

# Execute flow
engine = FlowEngine()
result = await engine.execute(FeatureFlowState(
    feature_name="user_auth",
    requirements=["login", "logout", "signup"]
))
```

### Flow Events

```python
from agent.flow.events import EventBus, on_event

bus = EventBus()

@on_event("flow_started")
async def handle_start(event):
    print(f"Flow {event.flow_id} started")

@on_event("step_completed")
async def handle_step(event):
    print(f"Step {event.step_name} completed")

@on_event("flow_completed")
async def handle_complete(event):
    print(f"Flow completed with result: {event.result}")
```

---

## Council System Integration

### Creating a Vote

```python
from agent.council import CouncilOrchestrator, VoteOption

council = CouncilOrchestrator()

# Create voting session
session = await council.create_vote(
    question="Which database should we use?",
    options=[
        VoteOption("postgresql", "PostgreSQL - robust, scalable"),
        VoteOption("mongodb", "MongoDB - flexible schema"),
        VoteOption("sqlite", "SQLite - simple, embedded")
    ],
    context={
        "project_type": "web_application",
        "expected_scale": "medium"
    }
)

# Get result
result = await council.execute_vote(session)
print(f"Winner: {result.winner}")  # postgresql
print(f"Weighted score: {result.weighted_score}")
```

### Custom Councillor

```python
from agent.council.models import Councillor, PerformanceMetrics

new_councillor = Councillor(
    id="database_expert",
    name="Dana",
    specialization="database",
    performance=PerformanceMetrics(
        quality_score=0.85,
        speed_score=0.90,
        success_rate=0.88
    ),
    happiness=75
)

# Add to council
council.add_councillor(new_councillor)
```

---

## Memory System

### Short-Term Memory (RAG)

```python
from agent.memory import MemoryManager

memory = MemoryManager()

# Store context
await memory.short_term.store(
    content="User prefers dark mode interfaces",
    metadata={"type": "preference", "user_id": "user_123"}
)

# Retrieve relevant context
results = await memory.short_term.search(
    query="What UI preferences does the user have?",
    k=5,
    threshold=0.7
)
```

### Long-Term Memory

```python
# Store persistent memory
await memory.long_term.store(
    content="Project X uses React with TypeScript",
    metadata={
        "project": "project_x",
        "category": "tech_stack"
    },
    expires_days=90
)

# Retrieve by metadata
memories = await memory.long_term.search_by_metadata(
    project="project_x"
)
```

### Entity Memory (Knowledge Graph)

```python
# Add entity
await memory.entity.add_entity(
    entity_type="project",
    name="Project X",
    attributes={
        "language": "TypeScript",
        "framework": "React"
    }
)

# Add relationship
await memory.entity.add_relationship(
    source="Project X",
    target="React",
    relationship_type="uses"
)

# Query relationships
related = await memory.entity.get_related("Project X")
```

---

## Voice System Development

### Text-to-Speech

```python
from agent.jarvis_voice import JarvisVoice, VoiceConfig

voice = JarvisVoice(config=VoiceConfig(
    tts_provider="elevenlabs",
    voice_id="your_voice_id",
    stability=0.5,
    similarity_boost=0.75
))

# Generate speech
audio_data = await voice.speak("Good morning, sir.")

# Save to file
await voice.speak_to_file("Hello", "output.mp3")
```

### Speech-to-Text

```python
# Transcribe audio
text = await voice.listen(audio_data)
print(f"Transcribed: {text}")

# Real-time transcription
async for partial in voice.listen_stream(audio_stream):
    print(f"Partial: {partial}")
```

### Voice Conversation

```python
from agent.jarvis_voice_chat import JarvisVoiceChat

voice_chat = JarvisVoiceChat()

# Start conversation
session = await voice_chat.start_session()

# Process voice input
response = await voice_chat.process_audio(
    session_id=session.id,
    audio_data=recorded_audio
)

# Response includes both text and audio
print(response.text)
await play_audio(response.audio)
```

---

## Vision System Development

### Image Analysis

```python
from agent.jarvis_vision import JarvisVision

vision = JarvisVision()

# Analyze image from file
result = await vision.analyze_image(
    image_path="/path/to/image.png",
    prompt="Describe what you see in detail"
)

# Analyze from bytes
result = await vision.analyze_image(
    image_data=image_bytes,
    prompt="What objects are in this image?"
)

# Analyze from URL
result = await vision.analyze_image(
    image_url="https://example.com/image.jpg",
    prompt="Describe the scene"
)
```

### OCR

```python
# Extract text from image
text = await vision.read_text(image_data)
print(f"Extracted: {text}")
```

### Document Analysis

```python
# Analyze document
analysis = await vision.analyze_document(
    image_data=document_image,
    document_type="invoice"
)
print(f"Vendor: {analysis.vendor}")
print(f"Amount: {analysis.total}")
```

### Code Analysis

```python
# Analyze code screenshot
analysis = await vision.analyze_code(
    image_data=code_screenshot,
    language_hint="python"
)
print(f"Language: {analysis.language}")
print(f"Issues: {analysis.potential_issues}")
```

---

## API Development

### Creating New Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/custom", tags=["custom"])

class CustomRequest(BaseModel):
    input: str
    options: dict = {}

class CustomResponse(BaseModel):
    result: str
    metadata: dict

@router.post("/process", response_model=CustomResponse)
async def process_custom(request: CustomRequest):
    """Process custom request."""
    try:
        result = await process(request.input, request.options)
        return CustomResponse(result=result, metadata={})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Register in app.py
from custom_api import router as custom_router
app.include_router(custom_router)
```

### WebSocket Endpoint

```python
from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            result = await process(data)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
```

---

## Testing

### Unit Tests

```python
import pytest
from agent.config_loader import load_agents

def test_load_agents():
    agents = load_agents()
    assert "jarvis" in agents
    assert agents["jarvis"].role == "Master Orchestrator"

@pytest.mark.asyncio
async def test_llm_router():
    from agent.llm import get_router
    router = get_router()
    health = await router.health_check()
    assert health["status"] == "ok"
```

### Integration Tests

```python
import pytest
from httpx import AsyncClient
from agent.webapp.app import app

@pytest.mark.asyncio
async def test_jarvis_chat():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/chat", json={
            "message": "Hello JARVIS"
        })
        assert response.status_code == 200
        assert "Good" in response.json()["response"]
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=agent --cov-report=html
```

---

## Best Practices

### 1. Async-First Design

```python
# GOOD: Use async functions
async def process_task(task):
    result = await llm.complete(...)
    return result

# AVOID: Blocking calls in async context
def process_task(task):
    result = requests.post(...)  # Blocks event loop!
```

### 2. Configuration Over Code

```python
# GOOD: Load from YAML
agents = load_agents()  # config/agents.yaml

# AVOID: Hardcoded values
agents = {
    "developer": Agent(name="Dev", model="gpt-4", ...)
}
```

### 3. Error Handling

```python
# GOOD: Specific exceptions
try:
    result = await llm.complete(...)
except RateLimitError:
    await asyncio.sleep(60)
    result = await llm.complete(...)
except ProviderError as e:
    logger.error(f"LLM error: {e}")
    raise

# AVOID: Bare except
try:
    result = await llm.complete(...)
except:  # Catches everything!
    pass
```

### 4. Logging

```python
import core_logging

logger = core_logging.get_logger(__name__)

# GOOD: Structured logging
logger.info(
    "Task completed",
    extra={
        "task_id": task.id,
        "duration_ms": duration,
        "agent": agent.id
    }
)

# AVOID: String formatting
logger.info(f"Task {task.id} completed in {duration}ms by {agent.id}")
```

### 5. Type Hints

```python
# GOOD: Full type hints
async def process(
    message: str,
    context: list[dict[str, str]] = None,
    temperature: float = 0.7
) -> dict[str, Any]:
    ...

# AVOID: No type hints
async def process(message, context=None, temperature=0.7):
    ...
```

---

## Additional Resources

- [JARVIS_2_0_API_REFERENCE.md](./JARVIS_2_0_API_REFERENCE.md) - Complete API documentation
- [JARVIS_2_0_CONFIGURATION_GUIDE.md](./JARVIS_2_0_CONFIGURATION_GUIDE.md) - Configuration options
- [JARVIS_2_0_PATTERN_GUIDE.md](./JARVIS_2_0_PATTERN_GUIDE.md) - Orchestration patterns
- [JARVIS_2_0_MEMORY_GUIDE.md](./JARVIS_2_0_MEMORY_GUIDE.md) - Memory system
- [JARVIS_2_0_COUNCIL_GUIDE.md](./JARVIS_2_0_COUNCIL_GUIDE.md) - Council system
- [THREADING_AND_CONCURRENCY.md](./THREADING_AND_CONCURRENCY.md) - Async patterns
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues

---

*Developer Guide - JARVIS 2.0*
