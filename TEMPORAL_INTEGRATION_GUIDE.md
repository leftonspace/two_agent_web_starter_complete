# Temporal.io Integration Guide

## Overview

JARVIS integrates with [Temporal.io](https://temporal.io/) to provide enterprise-grade workflow orchestration for long-running, durable processes. This complements Celery by adding workflow-level features like versioning, deterministic execution, and saga patterns.

## Why Temporal.io?

**Celery** provides:
- ✅ Distributed task execution
- ✅ Task queues and routing
- ✅ Retry logic
- ✅ Periodic tasks

**Temporal.io** adds:
- ✅ **Workflow Versioning** - Update workflows without breaking running instances
- ✅ **Durable Execution** - Workflows survive failures and restarts
- ✅ **Long-Running Sagas** - Run for days, weeks, months, or years
- ✅ **Deterministic Replay** - Debug and replay workflows from history
- ✅ **Signals & Queries** - External interaction with running workflows
- ✅ **Automatic State Management** - No manual checkpointing needed
- ✅ **Child Workflows** - Compose complex workflows from simpler ones

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        JARVIS Application                        │
│                                                                  │
│  ┌────────────────┐    ┌────────────────┐    ┌──────────────┐  │
│  │  Temporal      │    │   Workflows    │    │  Activities  │  │
│  │  Client        │───▶│   - Self       │───▶│  - Analysis  │  │
│  │                │    │     Improvement│    │  - Testing   │  │
│  │  - Start       │    │   - Code       │    │  - Training  │  │
│  │  - Signal      │    │     Analysis   │    │  - Data      │  │
│  │  - Query       │    │   - Model      │    │    Processing│  │
│  │  - Cancel      │    │     Training   │    │              │  │
│  └────────────────┘    └────────────────┘    └──────────────┘  │
└──────────────┬───────────────────────────────────────┬──────────┘
               │                                        │
               │                                        │
               ▼                                        ▼
        ┌─────────────────────────────────────────────────┐
        │           Temporal Server (Cluster)            │
        │                                                 │
        │  ┌──────────────┐  ┌──────────────────────┐   │
        │  │   Frontend   │  │   History Service    │   │
        │  │   (gRPC)     │  │   (Workflow State)   │   │
        │  └──────────────┘  └──────────────────────┘   │
        │                                                 │
        │  ┌──────────────┐  ┌──────────────────────┐   │
        │  │   Matching   │  │   Database           │   │
        │  │   (Routing)  │  │   (PostgreSQL/       │   │
        │  │              │  │    Cassandra)        │   │
        │  └──────────────┘  └──────────────────────┘   │
        └─────────────────────────────────────────────────┘
               ▲                                        ▲
               │                                        │
               │                                        │
┌──────────────┴────────┐            ┌─────────────────┴──────────┐
│   Temporal Worker 1   │            │   Temporal Worker 2        │
│                       │            │                            │
│  - Executes           │            │  - Executes                │
│    Workflows          │            │    Workflows               │
│  - Executes           │            │  - Executes                │
│    Activities         │            │    Activities              │
│  - Handles Signals    │            │  - Handles Signals         │
└───────────────────────┘            └────────────────────────────┘
```

## Installation

### 1. Install Temporal Server

**Option A: Docker (Recommended for Development)**

```bash
# Start Temporal server with all dependencies
docker-compose -f docker-compose-temporal.yml up -d

# Or use Temporal's official Docker Compose
curl -L https://github.com/temporalio/temporal/releases/latest/download/docker-compose.yml -o temporal-docker-compose.yml
docker-compose -f temporal-docker-compose.yml up -d
```

**Option B: Temporal Cloud (Recommended for Production)**

Sign up at [cloud.temporal.io](https://cloud.temporal.io/)

**Option C: Local Installation**

```bash
# Install Temporal CLI
brew install temporal  # macOS
# or
curl -sSf https://temporal.download/cli.sh | sh  # Linux

# Start local server
temporal server start-dev
```

### 2. Install Python SDK

```bash
pip install temporalio
```

## Configuration

### Environment Variables

```bash
# Temporal server connection
export TEMPORAL_HOST=localhost
export TEMPORAL_PORT=7233
export TEMPORAL_NAMESPACE=default

# Task queue
export TEMPORAL_TASK_QUEUE=jarvis-task-queue

# TLS (for production)
export TEMPORAL_TLS_ENABLED=false
export TEMPORAL_TLS_CERT=/path/to/cert.pem
export TEMPORAL_TLS_KEY=/path/to/key.pem
```

### Configuration File

```python
from agent.temporal.config import TemporalConfig, set_temporal_config

# Custom configuration
config = TemporalConfig(
    host="temporal.example.com",
    port=7233,
    namespace="jarvis-prod",
    task_queue="jarvis-prod-queue",
    workflow_execution_timeout=86400 * 30,  # 30 days
    activity_start_to_close_timeout=3600,    # 1 hour
)

set_temporal_config(config)
```

## Usage

### Starting the Worker

The worker executes workflows and activities:

```bash
# Start worker (runs in foreground)
python -m agent.temporal.worker

# Or run as background service
nohup python -m agent.temporal.worker > temporal-worker.log 2>&1 &
```

**Multiple Workers for Horizontal Scaling**:

```bash
# Start multiple workers for high availability
python -m agent.temporal.worker &  # Worker 1
python -m agent.temporal.worker &  # Worker 2
python -m agent.temporal.worker &  # Worker 3
```

### Starting Workflows

#### Self-Improvement Workflow

```python
import asyncio
from agent.temporal.client import TemporalClient
from agent.temporal.workflows import SelfImprovementWorkflow

async def run_self_improvement():
    client = TemporalClient()

    # Start workflow
    handle = await client.start_workflow(
        SelfImprovementWorkflow,
        workflow_id="self-improvement-repo-xyz",
        repo_path="/path/to/repo",
        auto_apply=True,
        confidence_threshold=0.8,
    )

    print(f"Workflow started: {handle.id}")

    # Query progress
    progress = await client.query_workflow(handle.id, "get_progress")
    print(f"Progress: {progress}")

    # Wait for result
    result = await handle.result()
    print(f"Result: {result}")

asyncio.run(run_self_improvement())
```

#### Code Analysis Workflow

```python
from agent.temporal.workflows import CodeAnalysisWorkflow

async def run_analysis():
    client = TemporalClient()

    handle = await client.start_workflow(
        CodeAnalysisWorkflow,
        workflow_id="analysis-repo-xyz",
        repo_path="/path/to/repo",
        analysis_types=["static", "security", "complexity"],
    )

    # This can run for hours analyzing millions of lines
    result = await handle.result()
    print(f"Analysis complete: {result}")

asyncio.run(run_analysis())
```

#### Model Training Workflow

```python
from agent.temporal.workflows import ModelTrainingWorkflow

async def train_model():
    client = TemporalClient()

    handle = await client.start_workflow(
        ModelTrainingWorkflow,
        workflow_id="training-model-v2",
        model_id="jarvis-model-v2",
        training_config={
            "num_steps": 1000,
            "learning_rate": 0.001,
            "batch_size": 32,
            "target_accuracy": 0.95,
        },
    )

    # Query progress while training
    for i in range(10):
        await asyncio.sleep(60)  # Check every minute
        progress = await client.query_workflow(
            handle.id,
            "get_training_progress"
        )
        print(f"Training progress: {progress}")

    # Pause training if needed
    await client.send_signal(handle.id, "pause_training")
    print("Training paused")

    # Resume later
    await client.send_signal(handle.id, "resume_training")
    print("Training resumed")

    # Wait for completion (can take days/weeks)
    result = await handle.result()
    print(f"Training complete: {result}")

asyncio.run(train_model())
```

#### Long-Running Task with Control

```python
from agent.temporal.workflows import LongRunningTaskWorkflow

async def run_long_task():
    client = TemporalClient()

    handle = await client.start_workflow(
        LongRunningTaskWorkflow,
        workflow_id="long-task-001",
        task_id="data-migration-001",
        task_type="data_migration",
        parameters={"source": "db1", "target": "db2", "steps": 10000},
    )

    # Check status
    status = await client.get_workflow_status(handle.id)
    print(f"Status: {status}")

    # Pause if needed
    await client.send_signal(handle.id, "pause")

    # Resume later
    await client.send_signal(handle.id, "resume")

    # Cancel if needed
    # await client.cancel_workflow(handle.id)

    result = await handle.result()
    print(f"Task complete: {result}")

asyncio.run(run_long_task())
```

### Signals and Queries

**Signals** modify workflow state (async, no return value):

```python
# Pause workflow
await client.send_signal(workflow_id, "pause")

# Resume workflow
await client.send_signal(workflow_id, "resume")

# Cancel workflow
await client.send_signal(workflow_id, "cancel")

# Approve changes
await client.send_signal(workflow_id, "approve_changes", ["change1", "change2"])
```

**Queries** read workflow state (synchronous, returns value):

```python
# Get current progress
progress = await client.query_workflow(workflow_id, "get_progress")

# Get training metrics
metrics = await client.query_workflow(workflow_id, "get_training_progress")

# Get task status
status = await client.query_workflow(workflow_id, "get_status")
```

## Creating Custom Workflows

### Define Activities

```python
# agent/temporal/activities.py

from temporalio import activity

@activity.defn
async def my_custom_activity(
    param1: str,
    param2: int,
) -> dict:
    """
    Custom activity that does something.

    Activities should be:
    - Idempotent (safe to retry)
    - Heartbeating (for long operations)
    - Error handling (raise exceptions on failure)
    """
    activity.logger.info(f"Running custom activity: {param1}")

    # Heartbeat to show progress
    activity.heartbeat("Starting work")

    try:
        # Do work here
        result = {"status": "success", "value": param2 * 2}

        activity.heartbeat("Work complete")
        return result

    except Exception as e:
        activity.logger.error(f"Activity failed: {e}")
        raise
```

### Define Workflows

```python
# agent/temporal/workflows.py

from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyCustomWorkflow:
    """Custom workflow for specific use case."""

    @workflow.run
    async def run(
        self,
        input_param: str,
    ) -> dict:
        """Execute workflow."""
        workflow.logger.info(f"Starting custom workflow: {input_param}")

        # Execute activity
        result = await workflow.execute_activity(
            my_custom_activity,
            input_param,
            42,
            start_to_close_timeout=timedelta(minutes=30),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=100),
                backoff_coefficient=2.0,
            ),
        )

        workflow.logger.info(f"Workflow complete: {result}")
        return result

    @workflow.signal
    async def custom_signal(self, data: dict) -> None:
        """Handle custom signal."""
        workflow.logger.info(f"Received signal: {data}")
        # Update workflow state

    @workflow.query
    def get_custom_status(self) -> dict:
        """Query workflow status."""
        return {"status": "running", "progress": 0.5}
```

### Register with Worker

```python
# In worker.py or custom worker script

from agent.temporal.worker import create_worker
from agent.temporal.client import Client
from my_workflows import MyCustomWorkflow
from my_activities import my_custom_activity

async def run_custom_worker():
    client = await Client.connect("localhost:7233")

    worker = await create_worker(
        client,
        task_queue="custom-queue",
        workflows_list=[MyCustomWorkflow],
        activities_list=[my_custom_activity],
    )

    await worker.run()
```

## Best Practices

### 1. Workflow Determinism

**Workflows MUST be deterministic** - same input = same execution path:

✅ **DO**:
```python
@workflow.run
async def run(self):
    # Use workflow.now() for timestamps
    current_time = workflow.now()

    # Use workflow.sleep() for delays
    await workflow.sleep(3600)

    # Execute activities for non-deterministic operations
    result = await workflow.execute_activity(...)
```

❌ **DON'T**:
```python
@workflow.run
async def run(self):
    # DON'T use datetime.now() - not deterministic
    current_time = datetime.now()

    # DON'T use asyncio.sleep() - use workflow.sleep()
    await asyncio.sleep(3600)

    # DON'T do I/O in workflow - use activities
    data = open("file.txt").read()
```

### 2. Activity Idempotency

**Activities should be idempotent** - safe to retry:

```python
@activity.defn
async def process_record(record_id: str):
    # Check if already processed (idempotency)
    if is_already_processed(record_id):
        return get_cached_result(record_id)

    # Process and cache result
    result = do_processing(record_id)
    cache_result(record_id, result)
    return result
```

### 3. Heartbeating

**Use heartbeats for long activities**:

```python
@activity.defn
async def long_running_activity():
    for i in range(1000):
        # Heartbeat every 10 iterations
        if i % 10 == 0:
            activity.heartbeat(f"Processed {i}/1000")

        # Do work
        await process_item(i)
```

### 4. Error Handling

**Let activities fail and retry**:

```python
@activity.defn
async def risky_activity():
    try:
        result = external_api_call()
        return result
    except TemporaryError as e:
        # Let Temporal retry
        activity.logger.warning(f"Temporary error: {e}")
        raise
    except PermanentError as e:
        # Don't retry permanent errors
        activity.logger.error(f"Permanent error: {e}")
        raise ApplicationError("Permanent failure", non_retryable=True)
```

### 5. Versioning

**Use versioning for workflow changes**:

```python
@workflow.defn
class EvolvingWorkflow:
    @workflow.run
    async def run(self):
        # V1: Original logic
        if workflow.get_version("feature-x", 1, 2) == 1:
            result = await old_activity()
        else:
            # V2: New logic
            result = await new_activity()

        return result
```

## Monitoring

### Temporal Web UI

Access at `http://localhost:8080` (default Docker setup)

Features:
- View running workflows
- See workflow history
- Query workflow state
- Retry failed workflows
- View activity execution

### Prometheus Metrics

Temporal exposes metrics for monitoring:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'temporal'
    static_configs:
      - targets: ['localhost:9090']
```

### Logging

All workflows and activities log via Python's logging:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# In workflows/activities
workflow.logger.info("Workflow event")
activity.logger.info("Activity event")
```

## Comparison: Celery vs Temporal.io

| Feature | Celery | Temporal.io |
|---------|--------|-------------|
| **Task Execution** | ✅ Excellent | ✅ Excellent |
| **Distributed Queue** | ✅ Yes | ✅ Yes |
| **Retry Logic** | ✅ Good | ✅ Excellent |
| **Workflow Orchestration** | ⚠️ Limited | ✅ Excellent |
| **Long-Running (months/years)** | ❌ No | ✅ Yes |
| **Versioning** | ❌ No | ✅ Yes |
| **Deterministic Replay** | ❌ No | ✅ Yes |
| **Signals & Queries** | ❌ No | ✅ Yes |
| **State Management** | ⚠️ Manual | ✅ Automatic |
| **Child Workflows** | ❌ No | ✅ Yes |
| **Saga Patterns** | ⚠️ Manual | ✅ Built-in |
| **Learning Curve** | ✅ Easy | ⚠️ Moderate |
| **Setup Complexity** | ✅ Simple | ⚠️ More complex |

**Use Celery for**:
- Short-lived tasks (seconds to hours)
- Simple task queues
- Periodic tasks
- Quick setup

**Use Temporal.io for**:
- Long-running workflows (days to years)
- Complex multi-step processes
- Workflows requiring versioning
- Critical processes needing guaranteed execution
- Workflows with external interaction (signals/queries)

**Use Both**:
- Temporal for workflow orchestration
- Celery for individual task execution
- Best of both worlds!

## Troubleshooting

### Worker Not Picking Up Tasks

Check:
1. Worker is running: `ps aux | grep temporal.worker`
2. Correct task queue: Verify `TEMPORAL_TASK_QUEUE`
3. Worker is connected: Check worker logs

### Workflow Stuck

```python
# Query workflow status
status = await client.get_workflow_status(workflow_id)

# View in Temporal Web UI
# http://localhost:8080/namespaces/default/workflows/{workflow_id}

# Terminate if needed
await client.terminate_workflow(workflow_id, "Stuck workflow")
```

### Activity Timeout

Increase timeouts in workflow:

```python
result = await workflow.execute_activity(
    my_activity,
    start_to_close_timeout=timedelta(hours=2),  # Increase from 1 hour
    heartbeat_timeout=timedelta(seconds=60),     # More lenient
)
```

## Production Deployment

### High Availability Setup

```bash
# Deploy multiple workers
kubectl apply -f k8s/temporal-worker-deployment.yaml

# Scale workers
kubectl scale deployment temporal-worker --replicas=10
```

### Temporal Cloud

1. Sign up at [cloud.temporal.io](https://cloud.temporal.io/)
2. Get connection details
3. Configure TLS:

```python
config = TemporalConfig(
    host="your-namespace.tmprl.cloud",
    port=7233,
    namespace="your-namespace.accounting",
    tls_enabled=True,
    tls_cert_path="/path/to/client-cert.pem",
    tls_key_path="/path/to/client-key.pem",
)
```

## Resources

- **Temporal Documentation**: https://docs.temporal.io/
- **Python SDK**: https://github.com/temporalio/sdk-python
- **Temporal Cloud**: https://cloud.temporal.io/
- **Community**: https://community.temporal.io/

## Summary

Temporal.io provides **enterprise-grade workflow orchestration** that complements JARVIS's Celery-based task execution:

✅ **Phase 2 (Async & Background Tasks) is now 100% complete**

- Celery + Redis for distributed tasks ✅
- Temporal.io for long-running workflows ✅
- Complete solution for async execution at any scale ✅
