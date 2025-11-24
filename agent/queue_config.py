"""
Distributed Task Queue Configuration

Provides Celery + Redis configuration for distributed task execution.
Enables horizontal scaling and background task processing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class QueueConfig:
    """Distributed queue configuration"""

    # Redis connection
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Celery settings
    broker_url: Optional[str] = None
    result_backend: Optional[str] = None
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = None
    timezone: str = "UTC"
    enable_utc: bool = True

    # Task routing
    task_routes: Optional[Dict[str, str]] = None
    task_default_queue: str = "default"
    task_default_priority: int = 5

    # Worker settings
    worker_prefetch_multiplier: int = 4
    worker_max_tasks_per_child: int = 1000
    worker_pool: str = "prefork"  # prefork, solo, threads, gevent
    worker_concurrency: Optional[int] = None  # None = number of CPUs

    # Task execution
    task_time_limit: int = 3600  # 1 hour hard limit
    task_soft_time_limit: int = 3000  # 50 minutes soft limit
    task_acks_late: bool = True  # Acknowledge after task completion
    task_reject_on_worker_lost: bool = True

    # Result backend settings
    result_expires: int = 86400  # 24 hours
    result_compression: str = "gzip"

    # Rate limiting
    task_annotations: Optional[Dict] = None

    def __post_init__(self):
        if self.accept_content is None:
            self.accept_content = ["json", "msgpack"]

        # Build broker URL if not provided
        if self.broker_url is None:
            if self.redis_password:
                self.broker_url = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            else:
                self.broker_url = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

        # Build result backend URL if not provided
        if self.result_backend is None:
            if self.redis_password:
                self.result_backend = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db + 1}"
            else:
                self.result_backend = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db + 1}"

    @classmethod
    def from_env(cls) -> QueueConfig:
        """Load configuration from environment variables"""
        return cls(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_db=int(os.getenv("REDIS_DB", "0")),
            redis_password=os.getenv("REDIS_PASSWORD"),
            broker_url=os.getenv("CELERY_BROKER_URL"),
            result_backend=os.getenv("CELERY_RESULT_BACKEND"),
            timezone=os.getenv("TIMEZONE", "UTC"),
            worker_pool=os.getenv("CELERY_WORKER_POOL", "prefork"),
            worker_concurrency=int(os.getenv("CELERY_WORKER_CONCURRENCY"))
            if os.getenv("CELERY_WORKER_CONCURRENCY")
            else None,
        )

    def to_celery_config(self) -> Dict[str, any]:
        """Convert to Celery configuration dictionary"""
        return {
            # Broker settings
            "broker_url": self.broker_url,
            "result_backend": self.result_backend,

            # Serialization
            "task_serializer": self.task_serializer,
            "result_serializer": self.result_serializer,
            "accept_content": self.accept_content,

            # Timezone
            "timezone": self.timezone,
            "enable_utc": self.enable_utc,

            # Task routing
            "task_routes": self.task_routes or {},
            "task_default_queue": self.task_default_queue,
            "task_default_priority": self.task_default_priority,

            # Worker settings
            "worker_prefetch_multiplier": self.worker_prefetch_multiplier,
            "worker_max_tasks_per_child": self.worker_max_tasks_per_child,
            "worker_pool": self.worker_pool,
            "worker_concurrency": self.worker_concurrency,

            # Task execution
            "task_time_limit": self.task_time_limit,
            "task_soft_time_limit": self.task_soft_time_limit,
            "task_acks_late": self.task_acks_late,
            "task_reject_on_worker_lost": self.task_reject_on_worker_lost,

            # Result backend
            "result_expires": self.result_expires,
            "result_compression": self.result_compression,

            # Rate limiting
            "task_annotations": self.task_annotations or {},
        }


# =============================================================================
# Priority Levels
# =============================================================================

class Priority:
    """Task priority constants (0-10, higher = more urgent)"""
    CRITICAL = 10
    HIGH = 7
    NORMAL = 5
    LOW = 3
    BACKGROUND = 0


# =============================================================================
# Queue Names
# =============================================================================

class QueueNames:
    """Standard queue names for task routing"""
    DEFAULT = "default"
    HIGH_PRIORITY = "high_priority"
    MODEL_INFERENCE = "model_inference"  # LLM calls
    LONG_RUNNING = "long_running"  # Multi-hour tasks
    SCHEDULED = "scheduled"  # Cron/scheduled tasks
    SELF_IMPROVEMENT = "self_improvement"  # Self-modification tasks
    ANALYTICS = "analytics"  # Data processing


# =============================================================================
# Default Configuration
# =============================================================================

DEFAULT_CONFIG = QueueConfig(
    task_routes={
        "agent.workers.tasks.run_model_inference": QueueNames.MODEL_INFERENCE,
        "agent.workers.tasks.execute_long_task": QueueNames.LONG_RUNNING,
        "agent.workers.tasks.self_improve": QueueNames.SELF_IMPROVEMENT,
        "agent.workers.tasks.process_analytics": QueueNames.ANALYTICS,
    },
    task_annotations={
        # Rate limit model inference to prevent API abuse
        "agent.workers.tasks.run_model_inference": {"rate_limit": "100/m"},

        # Long-running tasks get extended time limits
        "agent.workers.tasks.execute_long_task": {
            "time_limit": 7200,  # 2 hours
            "soft_time_limit": 6900,  # 1h 55m
        },
    },
)
