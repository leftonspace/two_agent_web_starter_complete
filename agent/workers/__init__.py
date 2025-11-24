"""
JARVIS Distributed Workers

Celery-based distributed task queue for horizontal scaling and background processing.

Usage:
    # Start worker
    celery -A agent.workers.celery_app worker --loglevel=info

    # Start beat scheduler (for periodic tasks)
    celery -A agent.workers.celery_app beat --loglevel=info

    # Monitor tasks
    celery -A agent.workers.celery_app flower
"""

from .celery_app import app as celery_app
from .tasks import (
    run_model_inference,
    execute_long_task,
    self_improve,
    process_analytics,
)

__all__ = [
    "celery_app",
    "run_model_inference",
    "execute_long_task",
    "self_improve",
    "process_analytics",
]
