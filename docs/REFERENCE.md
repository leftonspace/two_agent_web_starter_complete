# JARVIS 2.0 API Reference

**Version:** 2.0.0
**Date:** November 23, 2025

Complete API reference for JARVIS 2.0 - all endpoints, modules, and interfaces.

---

## Table of Contents

1. [REST API Endpoints](#rest-api-endpoints)
2. [WebSocket Endpoints](#websocket-endpoints)
3. [Core Modules](#core-modules)
4. [Voice System API](#voice-system-api)
5. [Vision System API](#vision-system-api)
6. [Agents API](#agents-api)
7. [Council System API](#council-system-api)
8. [Flow Engine API](#flow-engine-api)
9. [Memory System API](#memory-system-api)
10. [LLM Router API](#llm-router-api)
11. [Approval Workflow API](#approval-workflow-api)
12. [Integration API](#integration-api)

---

## REST API Endpoints

### Health & Status

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/api/status` | Detailed system status |
| GET | `/api/version` | Version information |

### JARVIS Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to JARVIS |
| GET | `/api/chat/history` | Get conversation history |
| DELETE | `/api/chat/history` | Clear conversation |
| POST | `/api/chat/clarify` | Submit clarification answers |

### Voice System

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/voice/speak` | Text-to-speech |
| POST | `/api/voice/listen` | Speech-to-text |
| POST | `/api/voice/chat` | Voice conversation turn |
| GET | `/api/voice/config` | Voice configuration |
| GET | `/api/voice/audio/{id}` | Get audio file |

### Vision System

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/vision/analyze` | Analyze image |
| POST | `/api/vision/camera` | Process camera capture |
| POST | `/api/vision/ocr` | Extract text from image |
| POST | `/api/vision/document` | Analyze document |
| POST | `/api/vision/chat` | Vision chat with context |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/agents/status` | All agents status |
| GET | `/api/agents/{id}` | Single agent details |
| GET | `/api/agents/activity` | Recent activity log |
| POST | `/api/agents/{id}/task` | Assign task to agent |

### Council System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/council/status` | Council status |
| GET | `/api/council/councillors` | List councillors |
| POST | `/api/council/vote` | Initiate vote |
| GET | `/api/council/history` | Vote history |
| GET | `/api/council/{id}/happiness` | Councillor happiness |

### Flow Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flows` | List available flows |
| GET | `/api/flows/{id}` | Flow details |
| POST | `/api/flows/{id}/execute` | Execute flow |
| GET | `/api/flows/executions/{id}` | Execution status |
| DELETE | `/api/flows/executions/{id}` | Cancel execution |

### Memory System

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/memory/store` | Store memory |
| POST | `/api/memory/search` | Search memories |
| GET | `/api/memory/entities` | List entities |
| DELETE | `/api/memory/{id}` | Delete memory |

### Approvals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/approvals` | List approvals |
| POST | `/api/approvals` | Create approval request |
| GET | `/api/approvals/{id}` | Approval details |
| POST | `/api/approvals/{id}/approve` | Approve request |
| POST | `/api/approvals/{id}/reject` | Reject request |
| POST | `/api/approvals/{id}/escalate` | Escalate request |

### Integrations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/integrations` | List integrations |
| POST | `/api/integrations` | Add integration |
| GET | `/api/integrations/{id}` | Integration details |
| GET | `/api/integrations/{id}/test` | Test connection |
| POST | `/api/integrations/{id}/query` | Execute query |
| DELETE | `/api/integrations/{id}` | Remove integration |

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workflows` | List workflows |
| GET | `/api/workflows/{id}` | Workflow details |
| POST | `/api/workflows` | Create workflow |

---

## WebSocket Endpoints

### Agent Stream

```
WS /api/agents/stream
```

Real-time agent status updates.

**Message Format:**
```json
{
  "type": "agent_update",
  "agent_id": "developer",
  "status": "active",
  "current_task": "Writing tests",
  "timestamp": "2025-11-23T10:30:00Z"
}
```

### Voice Stream

```
WS /api/voice/stream
```

Real-time voice conversation.

**Client → Server:**
```json
{
  "type": "audio_chunk",
  "data": "<base64_audio>",
  "format": "webm"
}
```

**Server → Client:**
```json
{
  "type": "transcription",
  "text": "Hello JARVIS",
  "final": true
}
```

### Chat Stream

```
WS /api/chat/stream
```

Streaming chat responses.

**Client → Server:**
```json
{
  "message": "Create a Python function",
  "context": {}
}
```

**Server → Client:**
```json
{
  "type": "chunk",
  "content": "Certainly, sir.",
  "done": false
}
```

---

## Core Modules

### config_loader

```python
from agent.config_loader import (
    load_agents,
    load_tasks,
    load_llm_config,
    load_flows,
    load_memory_config,
    load_council_config,
    load_patterns_config,
    validate_config
)

# Load agent definitions
agents: dict[str, Agent] = load_agents()

# Load task templates
tasks: dict[str, Task] = load_tasks()

# Load LLM configuration
llm_config: LLMConfig = load_llm_config()

# Validate all configs
errors: list[str] = validate_config()
```

### jarvis_chat

```python
from agent.jarvis_chat import JarvisChat, ClarificationState

class JarvisChat:
    async def process_message(
        self,
        message: str,
        context: dict = None,
        session_id: str = None
    ) -> ChatResponse:
        """Process user message and return response."""

    async def process_with_clarification(
        self,
        message: str,
        answers: dict = None
    ) -> ChatResponse | ClarificationRequest:
        """Process with clarification loop."""

    async def get_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> list[Message]:
        """Get conversation history."""
```

### orchestrator

```python
from agent.orchestrator import (
    run_hierarchical,
    run_with_pattern,
    start_run,
    log_iteration,
    finalize_run
)

# Run with pattern
result = await run_with_pattern(
    task=task,
    pattern="auto_select",
    agents=agents,
    config=config
)

# Start logging
run = start_run(
    mode="hierarchical",
    project_dir="/path/to/project",
    task="Build feature",
    max_rounds=10,
    models_used={"manager": "claude-3-sonnet"}
)
```

---

## Voice System API

### JarvisVoice

```python
from agent.jarvis_voice import JarvisVoice, VoiceConfig

class VoiceConfig:
    tts_provider: str = "elevenlabs"  # or "openai"
    stt_provider: str = "whisper"
    voice_id: str = None
    stability: float = 0.5
    similarity_boost: float = 0.75
    language: str = "en"

class JarvisVoice:
    def __init__(self, config: VoiceConfig = None): ...

    async def speak(
        self,
        text: str,
        voice_id: str = None
    ) -> bytes:
        """Convert text to speech, return audio bytes."""

    async def speak_to_file(
        self,
        text: str,
        output_path: str
    ) -> str:
        """Save speech to file."""

    async def listen(
        self,
        audio_data: bytes,
        language: str = None
    ) -> str:
        """Transcribe audio to text."""

    async def listen_stream(
        self,
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        """Real-time transcription."""
```

### Voice API Endpoints

```python
# POST /api/voice/speak
class SpeakRequest(BaseModel):
    text: str
    voice_id: str = None

class SpeakResponse(BaseModel):
    success: bool
    audio_url: str
    duration_seconds: float

# POST /api/voice/listen
class ListenRequest(BaseModel):
    audio: str  # base64 encoded
    format: str = "webm"

class ListenResponse(BaseModel):
    success: bool
    text: str
    confidence: float
```

---

## Vision System API

### JarvisVision

```python
from agent.jarvis_vision import JarvisVision, VisionConfig

class VisionConfig:
    provider: str = "openai"  # or "anthropic"
    model: str = "gpt-4-vision-preview"
    max_tokens: int = 1024

class JarvisVision:
    def __init__(self, config: VisionConfig = None): ...

    async def analyze_image(
        self,
        image_data: bytes = None,
        image_path: str = None,
        image_url: str = None,
        prompt: str = "Describe this image"
    ) -> ImageAnalysis:
        """Analyze image with custom prompt."""

    async def read_text(
        self,
        image_data: bytes
    ) -> str:
        """OCR - extract text from image."""

    async def analyze_document(
        self,
        image_data: bytes,
        document_type: str = "general"
    ) -> DocumentAnalysis:
        """Analyze document (invoice, receipt, form)."""

    async def analyze_code(
        self,
        image_data: bytes,
        language_hint: str = None
    ) -> CodeAnalysis:
        """Analyze code screenshot."""

    async def compare_images(
        self,
        image1: bytes,
        image2: bytes,
        comparison_type: str = "difference"
    ) -> ComparisonResult:
        """Compare two images."""
```

### Vision API Endpoints

```python
# POST /api/vision/analyze
class AnalyzeRequest(BaseModel):
    image_data: str = None  # base64
    image_url: str = None
    prompt: str = "Describe this image"

class AnalyzeResponse(BaseModel):
    success: bool
    analysis: str
    objects_detected: list[str]
    confidence: float
```

---

## Agents API

### AgentRegistry

```python
from agent.agents_api import AgentRegistry, AgentStatus

class AgentStatus:
    id: str
    name: str
    role: str
    status: str  # "active", "idle", "error"
    current_task: str = None
    tasks_completed: int
    uptime_seconds: int

class AgentRegistry:
    def get_all_agents(self) -> list[AgentStatus]: ...
    def get_agent(self, agent_id: str) -> AgentStatus: ...
    def update_status(self, agent_id: str, status: str): ...
    def assign_task(self, agent_id: str, task: str): ...
    def get_activity_log(self, limit: int = 50) -> list[Activity]: ...
```

### Agent Status Endpoint

```python
# GET /api/agents/status
class AgentsStatusResponse(BaseModel):
    agents: list[AgentStatus]
    total_active: int
    total_idle: int
    timestamp: str
```

---

## Council System API

### Council Models

```python
from agent.council import (
    Councillor,
    PerformanceMetrics,
    Vote,
    VotingSession,
    VoteResult,
    CouncilOrchestrator
)

class PerformanceMetrics:
    quality_score: float  # 0-1
    speed_score: float  # 0-1
    feedback_score: float  # 0-1
    success_rate: float  # 0-1

class Councillor:
    id: str
    name: str
    specialization: str
    performance: PerformanceMetrics
    happiness: int  # 0-100
    vote_weight: float  # Calculated

class Vote:
    councillor_id: str
    option: str
    confidence: float
    reasoning: str

class VotingSession:
    session_id: str
    question: str
    options: list[str]
    votes: list[Vote]
    status: str  # "open", "closed"

class VoteResult:
    winner: str
    weighted_score: float
    vote_breakdown: dict
```

### CouncilOrchestrator

```python
class CouncilOrchestrator:
    async def create_vote(
        self,
        question: str,
        options: list[str],
        context: dict = None
    ) -> VotingSession: ...

    async def execute_vote(
        self,
        session: VotingSession
    ) -> VoteResult: ...

    def add_councillor(self, councillor: Councillor): ...
    def remove_councillor(self, councillor_id: str): ...
    def update_happiness(self, councillor_id: str, event: str): ...
    def evaluate_performance(self): ...  # Fire/promote logic
```

---

## Flow Engine API

### Flow Decorators

```python
from agent.flow import start, listen, router, or_, and_

@start()
async def entry_point(state: FlowState):
    """Mark function as flow entry point."""

@listen("step_name")
async def step_handler(state: FlowState):
    """Listen for specific step completion."""

@router(previous_step)
def route_logic(result) -> str:
    """Route to next step based on result."""

@listen(or_("step_a", "step_b"))
async def handle_either(state: FlowState):
    """Listen for either step."""

@listen(and_("step_a", "step_b"))
async def handle_both(state: FlowState):
    """Listen for both steps to complete."""
```

### FlowEngine

```python
from agent.flow import FlowEngine, FlowState

class FlowEngine:
    def register_flow(self, flow_class): ...
    def load_flow(self, yaml_path: str): ...

    async def execute(
        self,
        initial_state: FlowState,
        timeout_seconds: int = 3600
    ) -> FlowResult: ...

    async def get_execution_status(
        self,
        execution_id: str
    ) -> ExecutionStatus: ...

    async def cancel_execution(self, execution_id: str): ...
```

---

## Memory System API

### MemoryManager

```python
from agent.memory import MemoryManager

class MemoryManager:
    short_term: ShortTermMemory
    long_term: LongTermMemory
    entity: EntityMemory

    async def store(
        self,
        content: str,
        memory_type: str = "short_term",
        metadata: dict = None
    ): ...

    async def search(
        self,
        query: str,
        memory_types: list[str] = None,
        k: int = 5
    ) -> list[Memory]: ...

    async def clear(self, memory_type: str = None): ...
```

### ShortTermMemory

```python
class ShortTermMemory:
    async def store(
        self,
        content: str,
        metadata: dict = None
    ): ...

    async def search(
        self,
        query: str,
        k: int = 5,
        threshold: float = 0.65
    ) -> list[Memory]: ...
```

### LongTermMemory

```python
class LongTermMemory:
    async def store(
        self,
        content: str,
        metadata: dict = None,
        expires_days: int = None
    ): ...

    async def search(
        self,
        query: str,
        k: int = 5
    ) -> list[Memory]: ...

    async def search_by_metadata(
        self,
        **filters
    ) -> list[Memory]: ...
```

### EntityMemory

```python
class EntityMemory:
    async def add_entity(
        self,
        entity_type: str,
        name: str,
        attributes: dict = None
    ): ...

    async def add_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str,
        weight: float = 1.0
    ): ...

    async def get_related(
        self,
        entity_name: str,
        relationship_type: str = None,
        depth: int = 1
    ) -> list[Entity]: ...
```

---

## LLM Router API

### EnhancedRouter

```python
from agent.llm import get_router, EnhancedRouter

class EnhancedRouter:
    async def complete(
        self,
        messages: list[dict],
        provider: str = None,
        model: str = None,
        task_type: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> CompletionResponse: ...

    async def complete_with_vision(
        self,
        messages: list[dict],
        images: list[bytes],
        **kwargs
    ) -> CompletionResponse: ...

    async def health_check(self) -> dict: ...

    def get_available_providers(self) -> list[str]: ...
    def get_available_models(self, provider: str) -> list[str]: ...
```

### Routing Rules

```python
# Automatic routing based on task_type
router = get_router()

# Simple task → cheap model
response = await router.complete(
    messages=[...],
    task_type="simple"  # Routes to haiku/3.5-turbo
)

# Complex task → powerful model
response = await router.complete(
    messages=[...],
    task_type="complex"  # Routes to opus/gpt-4
)

# Code task → specialized model
response = await router.complete(
    messages=[...],
    task_type="coding"  # Routes to deepseek-coder
)
```

---

## Approval Workflow API

### ApprovalEngine

```python
from agent.approval_engine import (
    ApprovalEngine,
    ApprovalWorkflow,
    ApprovalRequest,
    DecisionType
)

class ApprovalEngine:
    def register_workflow(self, workflow: ApprovalWorkflow): ...

    def create_approval_request(
        self,
        workflow_id: str,
        mission_id: str,
        payload: dict,
        created_by: str
    ) -> ApprovalRequest: ...

    def process_decision(
        self,
        request_id: str,
        approver_id: str,
        decision: DecisionType,
        comments: str,
        approver_role: str
    ) -> ApprovalRequest: ...

    def get_pending_approvals(
        self,
        role: str = None,
        department: str = None
    ) -> list[ApprovalRequest]: ...

    def get_statistics(
        self,
        domain: str = None
    ) -> dict: ...
```

---

## Integration API

### DatabaseConnector

```python
from agent.integrations.database import DatabaseConnector

class DatabaseConnector:
    def __init__(
        self,
        connector_id: str,
        engine: str,  # "postgresql", "mysql", "sqlite"
        config: dict
    ): ...

    async def connect(self) -> bool: ...
    async def disconnect(self): ...

    async def query(
        self,
        sql: str,
        params: dict = None
    ) -> list[dict]: ...

    async def execute(
        self,
        sql: str,
        params: dict = None
    ) -> int: ...

    async def list_tables(self) -> list[str]: ...
    async def describe_table(self, table: str) -> list[dict]: ...
    def get_health(self) -> dict: ...
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing/invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource state conflict |
| 422 | Validation Error - Invalid data |
| 429 | Rate Limited - Too many requests |
| 500 | Internal Error - Server error |
| 503 | Service Unavailable - Dependency down |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/chat` | 60/minute |
| `/api/voice/*` | 30/minute |
| `/api/vision/*` | 20/minute |
| `/api/council/vote` | 10/minute |
| `/api/flows/*/execute` | 5/minute |

---

*API Reference - JARVIS 2.0*
