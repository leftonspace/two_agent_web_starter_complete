"""
Celery Application Configuration

Main Celery application for JARVIS distributed task processing.
"""

from __future__ import annotations

import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure

# Import configuration
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.queue_config import QueueConfig, DEFAULT_CONFIG


# =============================================================================
# Celery Application
# =============================================================================

# Load configuration from environment or use defaults
try:
    config = QueueConfig.from_env()
except Exception:
    config = DEFAULT_CONFIG

# Create Celery application
app = Celery(
    "jarvis",
    broker=config.broker_url,
    backend=config.result_backend,
    include=["agent.workers.tasks"],  # Auto-discover tasks
)

# Apply configuration
app.conf.update(config.to_celery_config())

# Optional: Beat schedule for periodic tasks
app.conf.beat_schedule = {
    "cleanup-old-results": {
        "task": "agent.workers.tasks.cleanup_old_results",
        "schedule": 3600.0,  # Every hour
    },
    "self-evaluation": {
        "task": "agent.workers.tasks.periodic_self_evaluation",
        "schedule": 86400.0,  # Every 24 hours
    },
}


# =============================================================================
# Signal Handlers
# =============================================================================

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log task start"""
    print(f"[Celery] Starting task: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **extra):
    """Log task completion"""
    print(f"[Celery] Completed task: {task.name} (ID: {task_id}, State: {state})")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """Log task failure"""
    print(f"[Celery] Task failed: {sender.name} (ID: {task_id})")
    print(f"[Celery] Exception: {exception}")


# =============================================================================
# Health Check
# =============================================================================

@app.task(name="health_check")
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "message": "JARVIS worker is operational"}


if __name__ == "__main__":
    app.start()
