# JARVIS 2.0 Troubleshooting Guide

**Version:** 2.0.0
**Date:** November 23, 2025

This guide covers common errors, their causes, and solutions for JARVIS 2.0.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Startup Errors](#startup-errors)
3. [Configuration Errors](#configuration-errors)
4. [LLM Provider Errors](#llm-provider-errors)
5. [Memory System Errors](#memory-system-errors)
6. [Authentication Errors](#authentication-errors)
7. [WebSocket Errors](#websocket-errors)
8. [Performance Issues](#performance-issues)
9. [Database Errors](#database-errors)
10. [Voice System Errors](#voice-system-errors)
11. [Vision System Errors](#vision-system-errors)
12. [Agent Coordination Errors](#agent-coordination-errors)
13. [Flow Engine Errors](#flow-engine-errors)
14. [Council System Errors](#council-system-errors)
15. [Debug Mode](#debug-mode)
16. [Getting Help](#getting-help)

---

## Quick Diagnostics

Run these commands to diagnose common issues:

```bash
# Check system health
python -m agent.diagnostics health

# Validate all configurations
python -m agent.config validate

# Test LLM connectivity
python -m agent.llm test

# Check memory system
python -m agent.memory test

# View recent logs
tail -f logs/jarvis.log

# Check Python environment
python -c "import sys; print(sys.version)"
pip list | grep -E "fastapi|pydantic|anthropic|openai"
```

---

## Startup Errors

### Error: `ModuleNotFoundError: No module named 'xyz'`

**Cause:** Missing dependency

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific module
pip install xyz
```

### Error: `ImportError: cannot import name 'X' from 'Y'`

**Cause:** Version mismatch or circular import

**Solution:**
```bash
# Check installed version
pip show Y

# Upgrade to compatible version
pip install Y --upgrade

# If circular import, check import order in your code
```

### Error: `Address already in use (port 8000)`

**Cause:** Another process is using the port

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
python -m agent.webapp.app --port 8001
```

### Error: `PermissionError: [Errno 13] Permission denied`

**Cause:** Insufficient file permissions

**Solution:**
```bash
# Fix directory permissions
chmod -R 755 /path/to/jarvis
chown -R $USER:$USER /path/to/jarvis

# Fix data directory
mkdir -p data logs
chmod 755 data logs
```

### Error: `FileNotFoundError: config/agents.yaml`

**Cause:** Configuration files not created

**Solution:**
```bash
# Create config directory
mkdir -p config

# Copy example configs
cp config.example/*.yaml config/

# Or run setup
python -m agent.setup init
```

---

## Configuration Errors

### Error: `ValidationError: field required`

**Cause:** Missing required field in YAML

**Example:**
```
ValidationError: 1 validation error for AgentConfig
role
  field required (type=value_error.missing)
```

**Solution:**
Add the missing field to your YAML:
```yaml
agents:
  - id: my_agent
    name: "Agent Name"
    role: "Agent Role"  # Add this required field
    goal: "Agent Goal"  # Add this required field
```

### Error: `yaml.scanner.ScannerError: mapping values are not allowed`

**Cause:** YAML syntax error (usually indentation)

**Solution:**
```yaml
# WRONG - inconsistent indentation
agents:
  - id: agent1
   name: "Name"  # Wrong indent

# CORRECT
agents:
  - id: agent1
    name: "Name"  # Consistent 4-space indent
```

### Error: `UnknownAgent: agent 'xyz' not found`

**Cause:** Task references non-existent agent

**Solution:**
1. Check agent ID spelling in tasks.yaml
2. Ensure agent is defined in agents.yaml
3. Agent IDs are case-sensitive

```yaml
# agents.yaml
agents:
  - id: developer  # Note: lowercase

# tasks.yaml
tasks:
  - id: code_task
    agent_id: developer  # Must match exactly
```

### Error: `CircularDependency: tasks form a cycle`

**Cause:** Task A depends on B, B depends on A

**Solution:**
```yaml
# WRONG - circular
tasks:
  - id: task_a
    dependencies: [task_b]
  - id: task_b
    dependencies: [task_a]

# CORRECT - linear
tasks:
  - id: task_a
    dependencies: []
  - id: task_b
    dependencies: [task_a]
```

### Error: `InvalidProvider: provider 'xyz' not configured`

**Cause:** LLM provider not enabled in config

**Solution:**
```yaml
# config/llm_config.yaml
providers:
  xyz:
    enabled: true  # Enable the provider
    api_key_env: XYZ_API_KEY
```

---

## LLM Provider Errors

### Error: `AuthenticationError: Invalid API key`

**Cause:** API key missing or incorrect

**Solution:**
```bash
# Check environment variable
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Set in .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Verify key format
# OpenAI: starts with "sk-"
# Anthropic: starts with "sk-ant-"
```

### Error: `RateLimitError: Rate limit exceeded`

**Cause:** Too many API requests

**Solution:**
1. Wait and retry (automatic with exponential backoff)
2. Reduce concurrent requests in config:
```yaml
# config/llm_config.yaml
providers:
  openai:
    rate_limits:
      requests_per_minute: 30  # Reduce from 60
```
3. Use caching for repeated queries
4. Switch to different provider temporarily

### Error: `APIConnectionError: Connection failed`

**Cause:** Network issue or provider down

**Solution:**
```bash
# Test connectivity
curl https://api.openai.com/v1/models
curl https://api.anthropic.com/v1/messages

# Check DNS
nslookup api.openai.com

# If using proxy
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

### Error: `ModelNotFound: Model 'xyz' does not exist`

**Cause:** Invalid model name or no access

**Solution:**
```yaml
# Use correct model names
providers:
  openai:
    models:
      # Correct names
      gpt-4-turbo: ...
      gpt-4: ...
      gpt-3.5-turbo: ...

  anthropic:
    models:
      # Correct names
      claude-3-opus-20240229: ...
      claude-3-sonnet-20240229: ...
      claude-3-haiku-20240307: ...
```

### Error: `ContextLengthExceeded: Maximum context length exceeded`

**Cause:** Input too long for model

**Solution:**
1. Truncate input:
```python
max_chars = 100000  # ~25k tokens
truncated = text[:max_chars]
```
2. Use model with larger context:
```yaml
defaults:
  model: gpt-4-turbo  # 128k context
```
3. Enable automatic chunking:
```yaml
memory:
  short_term:
    compression_enabled: true
```

---

## Memory System Errors

### Error: `EmbeddingError: Failed to generate embedding`

**Cause:** Embedding API issue

**Solution:**
```bash
# Check embedding model availability
python -c "from agent.memory import test_embedding; test_embedding()"

# Use local embeddings if API unavailable
# config/memory.yaml
memory:
  long_term:
    embedding_model: local  # Use local model
```

### Error: `DatabaseError: database is locked`

**Cause:** SQLite concurrent access

**Solution:**
```python
# Use aiosqlite for async access
import aiosqlite

async with aiosqlite.connect("data/memory.db") as db:
    await db.execute(...)

# Or use WAL mode
import sqlite3
conn = sqlite3.connect("data/memory.db")
conn.execute("PRAGMA journal_mode=WAL")
```

### Error: `MemoryNotFound: No memories matching query`

**Cause:** Empty memory or low relevance threshold

**Solution:**
```yaml
# Lower threshold in config/memory.yaml
memory:
  short_term:
    relevance_threshold: 0.5  # Lower from 0.65
```

### Error: `EntityGraphError: Failed to connect to Neo4j`

**Cause:** Neo4j not running or wrong credentials

**Solution:**
```bash
# Start Neo4j
docker run -p 7474:7474 -p 7687:7687 neo4j

# Or use in-memory graph
# config/memory.yaml
memory:
  entity:
    storage_type: networkx  # In-memory, no Neo4j needed
```

---

## Authentication Errors

### Error: `401 Unauthorized`

**Cause:** Missing or invalid auth token

**Solution:**
```python
# Include auth header in requests
headers = {
    "Authorization": f"Bearer {token}"
}
response = requests.get("/api/status", headers=headers)
```

### Error: `403 Forbidden`

**Cause:** User lacks permission

**Solution:**
1. Check user role in database
2. Update permissions:
```python
from webapp.auth import update_user_role
update_user_role(user_id, "admin")
```

### Error: `TokenExpired: JWT token has expired`

**Cause:** Token lifetime exceeded

**Solution:**
```python
# Refresh token before expiry
from webapp.auth import refresh_token
new_token = refresh_token(old_token)

# Or increase token lifetime in .env
JWT_EXPIRATION_HOURS=24
```

---

## WebSocket Errors

### Error: `WebSocketDisconnect: Connection closed`

**Cause:** Client disconnected or timeout

**Solution:**
```javascript
// Implement reconnection logic
const ws = new WebSocket('/api/agents/stream');

ws.onclose = () => {
    console.log('Disconnected, reconnecting...');
    setTimeout(() => connectWebSocket(), 1000);
};

// Send periodic pings to prevent timeout
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({type: 'ping'}));
    }
}, 30000);
```

### Error: `WebSocketException: Invalid state`

**Cause:** Sending on closed connection

**Solution:**
```python
async def safe_send(websocket, message):
    try:
        await websocket.send_json(message)
    except WebSocketDisconnect:
        # Connection already closed
        pass
    except RuntimeError as e:
        if "websocket.close" not in str(e):
            raise
```

---

## Performance Issues

### Issue: Slow response times

**Diagnosis:**
```bash
# Check which component is slow
python -m agent.diagnostics profile

# View timing logs
grep "took" logs/jarvis.log
```

**Solutions:**

1. **Enable caching:**
```yaml
# config/llm_config.yaml
providers:
  openai:
    cache_enabled: true
    cache_ttl: 3600
```

2. **Use connection pooling:**
```python
from agent.performance import get_http_pool
pool = get_http_pool()
```

3. **Enable lazy loading:**
```python
from agent.performance import LazyLoader
memory = LazyLoader(lambda: MemoryManager())
```

4. **Reduce memory search scope:**
```yaml
memory:
  short_term:
    max_tokens: 4000  # Reduce from 8000
```

### Issue: High memory usage

**Diagnosis:**
```bash
# Monitor memory
watch -n 1 "ps aux | grep python"

# Profile memory
python -m memory_profiler agent/webapp/app.py
```

**Solutions:**

1. **Limit cache size:**
```python
from agent.performance import ResponseCache
cache = ResponseCache(max_size=100)  # Limit entries
```

2. **Enable memory compression:**
```yaml
memory:
  short_term:
    compression_enabled: true
```

3. **Reduce entity graph size:**
```yaml
memory:
  entity:
    max_entities: 5000  # Limit nodes
```

### Issue: High CPU usage

**Cause:** Blocking operations in async context

**Solution:**
```python
# Move CPU-heavy work to thread pool
import asyncio

async def process_heavy(data):
    # WRONG: Blocks event loop
    # result = heavy_computation(data)

    # CORRECT: Run in thread
    result = await asyncio.to_thread(heavy_computation, data)
    return result
```

---

## Database Errors

### Error: `OperationalError: no such table`

**Cause:** Database not initialized

**Solution:**
```bash
# Initialize database
python -m agent.migrate.database --init

# Or create tables manually
python -c "from agent.database import init_db; init_db()"
```

### Error: `IntegrityError: UNIQUE constraint failed`

**Cause:** Duplicate primary key

**Solution:**
```python
# Use upsert pattern
async def save_or_update(item):
    try:
        await db.insert(item)
    except IntegrityError:
        await db.update(item)
```

### Error: `DatabaseCorruption: malformed database`

**Cause:** Unexpected shutdown or disk issue

**Solution:**
```bash
# Check integrity
sqlite3 data/jarvis.db "PRAGMA integrity_check"

# If corrupted, restore from backup
cp data/jarvis.db.backup data/jarvis.db

# Or rebuild
sqlite3 data/jarvis.db ".dump" | sqlite3 data/jarvis_new.db
mv data/jarvis_new.db data/jarvis.db
```

---

## Voice System Errors

### Error: `ElevenLabsError: Invalid voice ID`

**Cause:** Voice ID doesn't exist or no access

**Solution:**
```bash
# List available voices
python -c "from jarvis_voice import list_voices; print(list_voices())"

# Update voice ID in config
VOICE_ID=your_voice_id
```

### Error: `AudioDeviceError: No input device`

**Cause:** Microphone not available

**Solution:**
```bash
# List audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"

# Specify device in config
AUDIO_INPUT_DEVICE=1
```

### Error: `TranscriptionError: Audio too short`

**Cause:** Recording too brief

**Solution:**
```python
# Increase minimum recording duration
voice_config = VoiceConfig(
    min_recording_seconds=1.0  # At least 1 second
)
```

---

## Vision System Errors

### Error: `VisionError: Image too large`

**Cause:** Image exceeds API limits

**Solution:**
```python
from jarvis_vision import JarvisVision

vision = JarvisVision()
# Automatic resize
result = await vision.analyze_image(
    image_data,
    max_size=(1024, 1024)  # Resize before sending
)
```

### Error: `UnsupportedFormat: Cannot process file type`

**Cause:** Unsupported image format

**Solution:**
```python
# Supported formats: PNG, JPEG, GIF, WebP
from PIL import Image
import io

# Convert to supported format
img = Image.open(file_path)
buffer = io.BytesIO()
img.save(buffer, format='PNG')
png_data = buffer.getvalue()
```

### Error: `CameraPermissionDenied`

**Cause:** Browser blocked camera access

**Solution:**
```javascript
// Request permission explicitly
async function requestCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });
        return stream;
    } catch (err) {
        if (err.name === 'NotAllowedError') {
            alert('Camera permission denied. Please enable in browser settings.');
        }
        throw err;
    }
}
```

---

## Agent Coordination Errors

### Error: `AgentTimeoutError: Agent did not respond`

**Cause:** Agent task took too long

**Solution:**
```yaml
# Increase timeout in tasks.yaml
tasks:
  - id: slow_task
    timeout_seconds: 600  # 10 minutes
    retry_config:
      max_retries: 3
```

### Error: `NoAvailableAgent: No agent can handle task`

**Cause:** No agent with required skills/tools

**Solution:**
1. Add required tool to an agent:
```yaml
agents:
  - id: developer
    tools:
      - code_executor
      - file_manager
      - required_tool  # Add missing tool
```

2. Or remove tool requirement from task:
```yaml
tasks:
  - id: my_task
    tools: []  # Don't require specific tools
```

### Error: `AgentConflict: Multiple agents claimed task`

**Cause:** Race condition in task assignment

**Solution:**
```python
# Use locking for task assignment
from agent.coordination import TaskLock

async with TaskLock(task_id):
    agent = await assign_task(task)
```

---

## Flow Engine Errors

### Error: `FlowStateError: Invalid state transition`

**Cause:** Flow tried invalid transition

**Solution:**
```python
# Check flow definition
@router(previous_step)
def route_decision(result):
    # Ensure all return values are valid step names
    if result.success:
        return "success_step"  # Must exist
    return "failure_step"  # Must exist
```

### Error: `FlowDeadlock: Flow stuck in cycle`

**Cause:** Infinite loop in flow routing

**Solution:**
```yaml
flows:
  - id: my_flow
    steps:
      - id: check_condition
        type: router
        # Add max_iterations limit
        max_iterations: 5
        next:
          continue: check_condition  # Loops back
          done: complete
```

### Error: `FlowNotFound: Flow 'xyz' not registered`

**Cause:** Flow not loaded

**Solution:**
```python
from agent.flow import FlowEngine

engine = FlowEngine()
engine.load_flow("config/flows.yaml")  # Load flows
# Or
engine.register_flow(MyFlowClass)
```

---

## Council System Errors

### Error: `QuorumNotMet: Not enough councillors voted`

**Cause:** Insufficient participation

**Solution:**
```yaml
# Lower quorum requirement
council:
  voting:
    quorum_percentage: 0.5  # 50% instead of 60%
    timeout_seconds: 60  # More time to vote
```

### Error: `NoCouncillorsAvailable: All councillors are busy`

**Cause:** All councillors assigned to tasks

**Solution:**
```yaml
council:
  min_councillors: 5  # Ensure minimum pool
  max_councillors: 15  # Allow more to spawn
```

### Error: `VoteWeightError: Vote weight calculation failed`

**Cause:** Missing performance data

**Solution:**
```python
# Initialize councillor metrics
from agent.council import Councillor

councillor = Councillor(
    id="new_councillor",
    performance=PerformanceMetrics(
        quality_score=0.7,
        speed_score=0.7,
        success_rate=0.7
    )
)
```

---

## Debug Mode

Enable detailed debugging:

```bash
# Environment variable
export JARVIS_DEBUG=true
export LOG_LEVEL=DEBUG
export PYTHONASYNCIODEBUG=1

# Start with debug flag
python -m agent.webapp.app --debug

# Or in .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Debug Logging

```python
import core_logging

logger = core_logging.get_logger(__name__)
logger.setLevel("DEBUG")

# Add context to logs
logger.debug(
    "Processing request",
    extra={
        "request_id": request_id,
        "user": user.id,
        "component": "chat"
    }
)
```

### Profile Specific Components

```bash
# Profile LLM calls
python -m agent.diagnostics profile --component llm

# Profile memory operations
python -m agent.diagnostics profile --component memory

# Profile flows
python -m agent.diagnostics profile --component flow
```

---

## Document Processing Errors

### Error: `Document not processed: No attached files`

**Cause:** User requested document processing without attaching files

**Solution:**
Ensure files are attached before requesting document operations:
```
1. Click the attachment button (📎) in the chat interface
2. Select your document (PDF, TXT, DOCX supported)
3. Wait for upload confirmation
4. Then type your request: "Make me a resume from this document"
```

### Error: `File content not displaying (white box)`

**Cause:** CSS text color conflict with file display elements

**Solution:**
This was fixed in version 2.0.1. If you still see this issue:
```bash
# Pull latest changes
git pull origin main

# Clear browser cache
# Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

### Error: `Document processed as code instead of content`

**Cause:** Intent classification incorrectly routed to code generation

**Solution:**
Be specific about wanting document analysis:
```
# Instead of:
"Make me a website resume"  # May trigger code generation

# Use:
"Create a resume from my attached document"  # Triggers document processing
"Analyze this file and make a professional resume"
```

### Error: `Format export not available`

**Cause:** Format generation requires additional processing

**Solution:**
After receiving the generated content, specify your format:
```
You: I want it in PDF format
JARVIS: I'll generate a PDF file for you...
```

---

## Administration Tools Errors

### Error: `Email integration not configured`

**Cause:** Missing email provider credentials

**Solution:**
```bash
# Add to .env file:
OUTLOOK_CLIENT_ID=your_client_id
OUTLOOK_CLIENT_SECRET=your_secret
# Or for Gmail:
GMAIL_CREDENTIALS_PATH=path/to/credentials.json
```

### Error: `Calendar sync failed`

**Cause:** Calendar API permissions not granted

**Solution:**
1. Re-authenticate with your calendar provider
2. Ensure JARVIS has read/write calendar permissions
3. Check API quota limits

### Error: `Workflow execution timeout`

**Cause:** Workflow action took too long

**Solution:**
```yaml
# Increase timeout in workflow config
workflows:
  - name: my_workflow
    timeout_seconds: 300  # Increase from default 60
```

---

## Finance Tools Errors

### Error: `Spreadsheet processing failed`

**Cause:** Unsupported file format or corrupted file

**Solution:**
```
Supported formats: .xlsx, .xls, .csv
Maximum file size: 10MB

# Convert older formats:
# .xls → Save as .xlsx in Excel
# Numbers → Export as .xlsx
```

### Error: `Invoice OCR inaccurate`

**Cause:** Poor image quality or unusual layout

**Solution:**
1. Use high-resolution images (300 DPI minimum)
2. Ensure good lighting and contrast
3. Avoid skewed or rotated documents
4. Try manual field correction if needed

---

## Engineering Tools Errors

### Error: `VS Code extension not connecting`

**Cause:** Extension not installed or port conflict

**Solution:**
```bash
# Check if extension is installed
code --list-extensions | grep jarvis

# Restart VS Code
# Or manually specify port:
VSCODE_JARVIS_PORT=3001
```

### Error: `Code review timeout`

**Cause:** Large codebase or complex PR

**Solution:**
```python
# Review specific files instead of entire PR
review = await reviewer.review_file("src/main.py")

# Or limit scope:
review = await reviewer.review_pr(
    pr_number=123,
    max_files=10,
    focus=["security"]  # Focus on specific aspects
)
```

---

## Getting Help

### 1. Check Logs

```bash
# Application logs
tail -f logs/jarvis.log

# Error logs only
grep ERROR logs/jarvis.log

# Specific component
grep "council" logs/jarvis.log
```

### 2. Run Diagnostics

```bash
python -m agent.diagnostics --full-report > diagnostics.txt
```

### 3. Search Documentation

```bash
grep -r "your error" docs/
```

### 4. Common Solutions Summary

| Error Type | First Step |
|------------|------------|
| Import/Module | `pip install -r requirements.txt` |
| Configuration | `python -m agent.config validate` |
| LLM/API | Check API keys in `.env` |
| Database | Run migrations |
| Performance | Enable caching |
| WebSocket | Check connection/reconnect logic |
| Auth | Verify token/permissions |

### 5. Report Issues

Include in bug reports:
1. Full error message and stack trace
2. Output of `python -m agent.diagnostics`
3. Relevant config files (redact API keys)
4. Steps to reproduce
5. Python version (`python --version`)
6. OS and version

---

*Troubleshooting Guide - JARVIS 2.0*
