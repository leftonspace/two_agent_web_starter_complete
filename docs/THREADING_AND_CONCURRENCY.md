# JARVIS Threading and Concurrency Guide

## Overview

JARVIS uses an **async-first architecture** built on Python's `asyncio`. Understanding the threading model is critical for proper integration and avoiding common pitfalls.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Main Event Loop                       │
│                    (asyncio)                             │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  FastAPI    │  │  WebSocket  │  │   Chat      │     │
│  │  Endpoints  │  │  Handlers   │  │   Sessions  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │            Agent Orchestration Layer             │   │
│  │  (Manager → Supervisor → Employee)               │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │ LLM Calls │  │ Tool Exec │  │ I/O Ops   │          │
│  │ (async)   │  │ (thread)  │  │ (async)   │          │
│  └───────────┘  └───────────┘  └───────────┘          │
└─────────────────────────────────────────────────────────┘
```

## Key Threading Limitations

### 1. Single Event Loop Constraint

**JARVIS runs on a single asyncio event loop.** All async operations must use `await`.

```python
# CORRECT: Use async/await
async def process_request(message: str):
    result = await llm_client.generate(message)
    return result

# WRONG: Blocking the event loop
def process_request_blocking(message: str):
    result = llm_client.generate_sync(message)  # BLOCKS EVERYTHING
    return result
```

### 2. CPU-Bound Operations

**Problem:** CPU-intensive tasks block the event loop.

```python
# WRONG: This blocks the entire server
async def analyze_large_file(data: bytes):
    result = heavy_computation(data)  # Blocks event loop!
    return result

# CORRECT: Run in thread pool
async def analyze_large_file(data: bytes):
    result = await asyncio.to_thread(heavy_computation, data)
    return result
```

### 3. Thread-Safe Operations

The following components are NOT thread-safe and must only be accessed from the main event loop:

| Component | Thread-Safe | Notes |
|-----------|-------------|-------|
| `AgentMessageBus` | No | Use from main loop only |
| `AgentRegistry` | No | Status updates are async |
| `SessionManager` | No | Session state is not locked |
| `VoiceCache` | Yes | Uses file-based locking |
| `VisionAnalysis` | Yes | Stateless operations |

### 4. Database Operations

SQLite has threading limitations:

```python
# WRONG: Sharing connection across threads
connection = sqlite3.connect("db.sqlite")  # In main thread

async def worker():
    # This may fail or corrupt data!
    connection.execute("INSERT ...")

# CORRECT: Connection per operation or use aiosqlite
import aiosqlite

async def worker():
    async with aiosqlite.connect("db.sqlite") as db:
        await db.execute("INSERT ...")
```

## Recommended Patterns

### Pattern 1: Async Task Execution

```python
from agent.execution.employee_pool import EmployeePool

# Use the built-in employee pool for parallel task execution
pool = EmployeePool(max_workers=4)

async def process_tasks(tasks: List[Task]):
    results = await pool.execute_parallel(tasks)
    return results
```

### Pattern 2: Background Jobs

```python
from agent.jobs import get_job_manager

# Submit long-running work to background
job_manager = get_job_manager()

async def start_long_task(config: dict):
    job_id = await job_manager.submit_job(
        "long_task",
        config,
        timeout=3600  # 1 hour timeout
    )
    return job_id
```

### Pattern 3: WebSocket Message Broadcasting

```python
# Use the built-in message bus for real-time updates
from agent.agent_messaging import get_message_bus

bus = get_message_bus()

async def broadcast_status(message: str):
    await bus.post_message(
        role=AgentRole.SYSTEM,
        content=message
    )
```

### Pattern 4: Blocking Library Integration

Some libraries don't support async. Use `asyncio.to_thread()`:

```python
import asyncio
from some_blocking_lib import BlockingClient

client = BlockingClient()

async def call_blocking_service(data):
    # Run blocking call in thread pool
    result = await asyncio.to_thread(client.process, data)
    return result
```

## Performance Considerations

### Concurrent LLM Calls

```python
# Parallel LLM calls (efficient)
async def analyze_multiple(items: List[str]):
    tasks = [llm_client.generate(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

### Rate Limiting

Use the built-in rate limiter:

```python
from agent.actions.rate_limiter import RateLimiter

limiter = RateLimiter(requests_per_minute=60)

async def make_api_call():
    async with limiter:
        return await external_api.call()
```

### Circuit Breaker

Prevent cascading failures:

```python
from agent.core.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30
)

async def call_external_service():
    async with breaker:
        return await external_service.call()
```

## Common Pitfalls

### 1. Nested Event Loops

```python
# WRONG: Creates nested loop
async def handler():
    asyncio.run(some_async_function())  # RuntimeError!

# CORRECT: Just await
async def handler():
    await some_async_function()
```

### 2. Forgetting to Await

```python
# WRONG: Returns coroutine, not result
async def get_data():
    return fetch_data()  # Missing await!

# CORRECT
async def get_data():
    return await fetch_data()
```

### 3. Blocking in Async Context

```python
# WRONG: time.sleep blocks event loop
async def wait_and_process():
    time.sleep(5)  # Blocks everything!
    await process()

# CORRECT: Use async sleep
async def wait_and_process():
    await asyncio.sleep(5)  # Non-blocking
    await process()
```

### 4. Shared Mutable State

```python
# WRONG: Race condition
results = []

async def worker(item):
    result = await process(item)
    results.append(result)  # Race condition!

# CORRECT: Use asyncio.Queue or locks
queue = asyncio.Queue()

async def worker(item):
    result = await process(item)
    await queue.put(result)
```

## Monitoring and Debugging

### Check Event Loop Status

```python
import asyncio

loop = asyncio.get_event_loop()
print(f"Running: {loop.is_running()}")
print(f"Closed: {loop.is_closed()}")
```

### Profile Async Code

```python
import asyncio
import time

async def timed_operation():
    start = time.monotonic()
    await some_operation()
    elapsed = time.monotonic() - start
    print(f"Operation took {elapsed:.2f}s")
```

### Debug Slow Operations

Enable asyncio debug mode:

```python
import asyncio

asyncio.get_event_loop().set_debug(True)
```

Or via environment:
```bash
PYTHONASYNCIODEBUG=1 python app.py
```

## Summary

| Scenario | Solution |
|----------|----------|
| LLM API calls | Use async client, `await` calls |
| CPU-heavy work | `asyncio.to_thread()` |
| Database access | Use `aiosqlite` or connection pooling |
| External blocking libs | `asyncio.to_thread()` |
| Parallel I/O | `asyncio.gather()` |
| Real-time updates | WebSocket + MessageBus |
| Long-running jobs | Background job manager |
