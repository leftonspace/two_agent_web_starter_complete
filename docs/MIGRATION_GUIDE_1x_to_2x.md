# JARVIS Migration Guide: 1.x to 2.0

**Version:** 2.0.0
**Date:** November 23, 2025

This guide helps you migrate your JARVIS installation from version 1.x to 2.0, covering breaking changes, new features, and step-by-step migration instructions.

---

## Table of Contents

1. [Overview of Changes](#overview-of-changes)
2. [Breaking Changes](#breaking-changes)
3. [New Features](#new-features)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [Configuration Migration](#configuration-migration)
6. [Code Migration](#code-migration)
7. [Database Migration](#database-migration)
8. [Testing Your Migration](#testing-your-migration)
9. [Rollback Procedures](#rollback-procedures)
10. [FAQ](#faq)

---

## Overview of Changes

JARVIS 2.0 represents a major architectural evolution:

| Aspect | 1.x | 2.0 |
|--------|-----|-----|
| Configuration | Python code | YAML files |
| Agent Definition | Hardcoded | Declarative YAML |
| Orchestration | Fixed hierarchical | Pattern-based (5 patterns) |
| Memory | Session-only | Multi-type persistent |
| LLM Support | Single provider | Multi-provider with routing |
| Task Planning | Implicit | Flow Engine with visual graphs |
| Human Approval | Manual | Integrated checkpoints |
| Performance | Synchronous | Async with caching/pooling |

---

## Breaking Changes

### 1. Agent Configuration Format

**1.x (Python):**
```python
# agent/config.py
AGENTS = {
    "developer": {
        "name": "Developer",
        "model": "gpt-4",
        "system_prompt": "You are a developer..."
    }
}
```

**2.0 (YAML):**
```yaml
# config/agents.yaml
version: "2.0"
agents:
  - id: developer
    name: "Developer"
    role: "Software Developer"
    goal: "Write clean, efficient code"
    backstory: "You are a developer..."
    llm_config:
      provider: openai
      model: gpt-4
```

### 2. Task Execution API

**1.x:**
```python
from agent.executor import execute_task

result = execute_task(
    task="Write a function",
    agent="developer"
)
```

**2.0:**
```python
from agent.flow import FlowEngine
from agent.config_loader import load_tasks

engine = FlowEngine()
task = load_tasks()["write_function"]
result = await engine.execute(task)
```

### 3. LLM Client Interface

**1.x:**
```python
from agent.llm import get_completion

response = get_completion(prompt, model="gpt-4")
```

**2.0:**
```python
from agent.llm import get_router

router = get_router()
response = await router.complete(
    messages=[{"role": "user", "content": prompt}],
    task_type="coding"  # Enables intelligent routing
)
```

### 4. Memory Access

**1.x:**
```python
# Memory was session-scoped, no persistence
context = session.get_context()
```

**2.0:**
```python
from agent.memory import MemoryManager

memory = MemoryManager()

# Short-term (RAG-based)
relevant = await memory.short_term.search(query, k=5)

# Long-term (persistent)
await memory.long_term.store(content, metadata)

# Entity (knowledge graph)
entities = await memory.entity.get_related("user_project")
```

### 5. Authentication Required

**1.x:** Many endpoints had no authentication
**2.0:** All API endpoints require authentication by default

```python
# 1.x - No auth
@app.get("/api/status")
async def get_status():
    return {"status": "ok"}

# 2.0 - Auth required
@app.get("/api/status")
async def get_status(user: User = Depends(require_auth)):
    return {"status": "ok", "user": user.username}
```

### 6. Logging System

**1.x:**
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

**2.0:**
```python
import core_logging
logger = core_logging.get_logger(__name__)
logger.info("Message", extra={"component": "agent"})
```

### 7. Exception Handling

**1.x:** Bare except clauses allowed
**2.0:** Specific exception types required

```python
# 1.x - Allowed
try:
    do_something()
except:
    pass

# 2.0 - Required
try:
    do_something()
except Exception as e:
    logger.error(f"Error: {e}")
```

---

## New Features

### 1. YAML-Based Configuration

Define agents, tasks, and flows without writing Python:

```yaml
# config/agents.yaml
agents:
  - id: code_reviewer
    name: "Jordan"
    role: "Code Reviewer"
    goal: "Ensure code quality"
    tools: [code_analyzer, security_scanner]
```

### 2. Flow Engine

Create complex workflows with conditional routing:

```python
from agent.flow import start, listen, router

@start()
def begin_task(state):
    return analyze_input(state)

@router(begin_task)
def route_complexity(result):
    if result.complexity > 7:
        return "complex_handler"
    return "simple_handler"

@listen("complex_handler")
def handle_complex(state):
    # Multi-step processing
    ...
```

### 3. Council System

Gamified meta-orchestration with voting:

```python
from agent.council import CouncilOrchestrator

council = CouncilOrchestrator()
decision = await council.vote(
    question="How should we approach this task?",
    options=["simple", "standard", "complex"]
)
```

### 4. Pattern-Based Orchestration

Choose from 5 coordination patterns:

- **Sequential** - Linear agent execution
- **Hierarchical** - Manager → Supervisor → Employee
- **AutoSelect** - LLM-driven agent selection
- **RoundRobin** - Rotating through agents
- **Manual** - Human-selected agent

### 5. Multi-Provider LLM Routing

```yaml
# config/llm_config.yaml
routing:
  rules:
    - condition: "task.type == 'coding'"
      provider: deepseek
      model: deepseek-coder
    - condition: "task.complexity == 'complex'"
      provider: anthropic
      model: claude-3-opus
```

### 6. Voice and Vision Capabilities

```python
from agent.jarvis_voice import JarvisVoice
from agent.jarvis_vision import JarvisVision

voice = JarvisVoice()
await voice.speak("How may I assist you?")

vision = JarvisVision()
analysis = await vision.analyze_image(image_data)
```

### 7. Real-time Agent Dashboard

WebSocket-based monitoring of all agents:

```javascript
const ws = new WebSocket('/api/agents/stream');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateAgentStatus(data.agent);
};
```

---

## Step-by-Step Migration

### Step 1: Backup Your Installation

```bash
# Backup current installation
cp -r /path/to/jarvis /path/to/jarvis-1.x-backup

# Backup database
cp data/jarvis.db data/jarvis-1.x.db

# Export current configuration
python -m agent.export_config > config-1.x-export.json
```

### Step 2: Update Dependencies

```bash
# Update requirements
pip install -r requirements.txt --upgrade

# Install new dependencies
pip install aiosqlite pyyaml pydantic[email]
```

### Step 3: Create Configuration Directory

```bash
mkdir -p config
```

### Step 4: Migrate Agent Configuration

Run the migration script:

```bash
python -m agent.migrate.agents_to_yaml
```

Or manually create `config/agents.yaml`:

```yaml
version: "2.0"
metadata:
  author: "your-name"
  migrated_from: "1.x"
  migration_date: "2025-11-23"

agents:
  # Copy your agent definitions here
  - id: your_agent_id
    name: "Your Agent Name"
    role: "Agent Role"
    goal: "Agent's primary goal"
    # ... additional fields
```

### Step 5: Migrate Task Definitions

Create `config/tasks.yaml`:

```yaml
version: "2.0"

tasks:
  - id: your_task_id
    name: "Task Name"
    description: "What the task does"
    expected_output: "Expected result"
    # ... additional fields
```

### Step 6: Update Environment Variables

Add new required variables to `.env`:

```bash
# New in 2.0
ENABLE_COUNCIL=true
ENABLE_MEMORY=true
ENABLE_FLOWS=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Voice (optional)
ELEVENLABS_API_KEY=...
VOICE_ID=...

# Vision (optional)
OPENAI_API_KEY=...  # For GPT-4 Vision
```

### Step 7: Run Database Migrations

```bash
# Apply schema updates
python -m agent.migrate.database

# Verify migration
python -m agent.migrate.verify
```

### Step 8: Update Code References

Search and replace deprecated imports:

```bash
# Find deprecated imports
grep -r "from agent.executor import" .
grep -r "from agent.llm import get_completion" .

# Update to new imports
# See Code Migration section below
```

### Step 9: Test the Migration

```bash
# Run validation
python -m agent.config validate

# Run integration tests
pytest tests/integration/ -v

# Start in development mode
python -m agent.webapp.app --debug
```

---

## Configuration Migration

### Agent Configuration Mapping

| 1.x Field | 2.0 Field | Notes |
|-----------|-----------|-------|
| `name` | `name` | No change |
| `model` | `llm_config.model` | Nested under llm_config |
| `system_prompt` | `backstory` | Renamed |
| `max_tokens` | `llm_config.max_tokens` | Nested |
| `temperature` | `llm_config.temperature` | Nested |
| N/A | `role` | New required field |
| N/A | `goal` | New required field |
| N/A | `tools` | New optional field |
| N/A | `constraints` | New optional field |
| N/A | `permissions` | New optional field |

### LLM Configuration Mapping

| 1.x | 2.0 |
|-----|-----|
| `OPENAI_MODEL=gpt-4` | `defaults.model: gpt-4` in `llm_config.yaml` |
| `OPENAI_API_KEY` | `providers.openai.api_key_env: OPENAI_API_KEY` |
| `MAX_TOKENS=4096` | `defaults.max_tokens: 4096` |
| N/A | `routing.rules` for intelligent routing |

---

## Code Migration

### Async/Await Updates

Many functions are now async:

```python
# 1.x - Synchronous
def process_message(message: str) -> str:
    result = llm.complete(message)
    return result

# 2.0 - Asynchronous
async def process_message(message: str) -> str:
    result = await llm.complete(message)
    return result
```

### Import Updates

```python
# 1.x imports → 2.0 imports

# Agent execution
# from agent.executor import execute_task
from agent.flow import FlowEngine

# LLM calls
# from agent.llm import get_completion
from agent.llm import get_router

# Memory
# from agent.context import get_context
from agent.memory import MemoryManager

# Logging
# import logging
import core_logging

# Configuration
# from agent.config import AGENTS
from agent.config_loader import load_agents
```

### Pattern Usage

```python
# 1.x - Fixed hierarchical
from agent.orchestrator import run_hierarchical
result = run_hierarchical(task)

# 2.0 - Pattern-based
from agent.patterns import get_pattern
from agent.pattern_selector import select_pattern

# Auto-select best pattern
pattern_name = select_pattern(task)
pattern = get_pattern(pattern_name)
result = await pattern.execute(task, agents)

# Or specify pattern
from agent.patterns import SequentialPattern
pattern = SequentialPattern()
result = await pattern.execute(task, agents)
```

### Error Handling

```python
# 1.x
try:
    result = do_something()
except:
    result = None

# 2.0
from agent.exceptions import TaskExecutionError

try:
    result = await do_something()
except TaskExecutionError as e:
    logger.error(f"Task failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    result = None
```

---

## Database Migration

### Schema Changes

JARVIS 2.0 adds several new tables:

```sql
-- New tables in 2.0
CREATE TABLE memory_long_term (
    id TEXT PRIMARY KEY,
    content TEXT,
    embedding BLOB,
    metadata JSON,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE TABLE memory_entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT,
    name TEXT,
    attributes JSON,
    created_at TIMESTAMP
);

CREATE TABLE memory_relationships (
    source_id TEXT,
    target_id TEXT,
    relationship_type TEXT,
    weight REAL,
    created_at TIMESTAMP
);

CREATE TABLE council_councillors (
    id TEXT PRIMARY KEY,
    name TEXT,
    specialization TEXT,
    performance_score REAL,
    happiness INT,
    vote_weight REAL,
    created_at TIMESTAMP
);

CREATE TABLE council_votes (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    councillor_id TEXT,
    vote TEXT,
    confidence REAL,
    timestamp TIMESTAMP
);
```

### Running Migrations

```bash
# Automatic migration
python -m agent.migrate.database --auto

# Manual migration with backup
python -m agent.migrate.database --backup --verbose

# Verify schema
python -m agent.migrate.verify_schema
```

---

## Testing Your Migration

### Validation Checklist

```bash
# 1. Validate configuration files
python -m agent.config validate

# 2. Check agent loading
python -c "from agent.config_loader import load_agents; print(load_agents())"

# 3. Verify LLM connectivity
python -c "from agent.llm import get_router; import asyncio; asyncio.run(get_router().health_check())"

# 4. Test memory system
python -c "from agent.memory import MemoryManager; m = MemoryManager(); print('Memory OK')"

# 5. Run unit tests
pytest tests/unit/ -v

# 6. Run integration tests
pytest tests/integration/ -v

# 7. Start web server
python -m agent.webapp.app --debug
```

### Common Issues After Migration

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: agent.executor` | Update import to `agent.flow` |
| `AttributeError: 'coroutine' object` | Add `await` to async function calls |
| `ValidationError: field required` | Add missing required fields to YAML |
| `DatabaseError: no such table` | Run database migrations |
| `AuthenticationError` | Update API calls to include auth |

---

## Rollback Procedures

### Quick Rollback

```bash
# Stop current server
pkill -f "python -m agent"

# Restore backup
rm -rf /path/to/jarvis
cp -r /path/to/jarvis-1.x-backup /path/to/jarvis

# Restore database
cp data/jarvis-1.x.db data/jarvis.db

# Restart
python -m agent.webapp.app
```

### Partial Rollback (Keep Data)

```bash
# Revert code only, keep database
git checkout v1.x -- agent/

# Or restore specific files
cp jarvis-1.x-backup/agent/executor.py agent/
cp jarvis-1.x-backup/agent/llm.py agent/
```

---

## FAQ

### Q: Can I run 1.x and 2.0 side by side?

Yes, using different ports:
```bash
# 1.x on port 8000
cd jarvis-1.x && python -m agent.webapp.app --port 8000

# 2.0 on port 8001
cd jarvis-2.0 && python -m agent.webapp.app --port 8001
```

### Q: Is my 1.x data preserved?

Yes. Database migrations preserve existing data. New tables are added without modifying existing ones.

### Q: Do I need to recreate my agents?

No. Use the migration script to convert Python configs to YAML:
```bash
python -m agent.migrate.agents_to_yaml
```

### Q: Can I disable new features?

Yes. In `.env`:
```bash
ENABLE_COUNCIL=false
ENABLE_MEMORY=false
ENABLE_FLOWS=false
```

### Q: What if migration fails?

1. Check logs: `tail -f logs/migration.log`
2. Restore from backup
3. Report issue with logs at GitHub

### Q: How do I migrate custom tools?

Register them with the new tool registry:
```python
from agent.tool_registry import register_tool

@register_tool(
    name="my_custom_tool",
    description="What it does",
    parameters={"param1": {"type": "string"}}
)
async def my_custom_tool(param1: str) -> str:
    return f"Result: {param1}"
```

### Q: Is the API backwards compatible?

Most endpoints maintain compatibility with deprecation warnings. Check:
```bash
grep -r "@deprecated" agent/
```

---

## Support

- **Documentation:** `docs/` directory
- **Issues:** https://github.com/your-org/jarvis/issues
- **Migration Help:** Tag issues with `migration`

---

*Migration Guide - JARVIS 2.0*
