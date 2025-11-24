"""
Temporal.io Configuration

Configuration for Temporal.io server connection, namespaces, and task queues.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TemporalConfig:
    """
    Temporal.io configuration.

    Attributes:
        host: Temporal server host
        port: Temporal server port
        namespace: Temporal namespace (logical isolation)
        task_queue: Default task queue name
        tls_enabled: Enable TLS for connection
        tls_cert_path: Path to TLS certificate
        tls_key_path: Path to TLS private key
        workflow_execution_timeout: Max workflow execution time (seconds)
        workflow_run_timeout: Max single workflow run time (seconds)
        workflow_task_timeout: Max workflow task processing time (seconds)
        activity_start_to_close_timeout: Max activity execution time (seconds)
        activity_schedule_to_close_timeout: Max time from schedule to complete (seconds)
        activity_heartbeat_timeout: Activity heartbeat interval (seconds)
        max_concurrent_activities: Max concurrent activity executions
        max_concurrent_workflows: Max concurrent workflow executions
    """

    # Connection settings
    host: str = "localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "jarvis-task-queue"

    # TLS settings
    tls_enabled: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None

    # Workflow timeouts
    workflow_execution_timeout: int = 86400 * 30  # 30 days
    workflow_run_timeout: int = 86400  # 1 day
    workflow_task_timeout: int = 10  # 10 seconds

    # Activity timeouts
    activity_start_to_close_timeout: int = 3600  # 1 hour
    activity_schedule_to_close_timeout: int = 7200  # 2 hours
    activity_heartbeat_timeout: int = 30  # 30 seconds

    # Concurrency limits
    max_concurrent_activities: int = 100
    max_concurrent_workflows: int = 50

    # Retry policies
    activity_max_attempts: int = 5
    activity_backoff_coefficient: float = 2.0
    activity_initial_interval: int = 1  # seconds
    activity_maximum_interval: int = 100  # seconds

    # Task queue configuration
    task_queues: dict = field(default_factory=lambda: {
        "default": "jarvis-task-queue",
        "high_priority": "jarvis-high-priority",
        "long_running": "jarvis-long-running",
        "self_improvement": "jarvis-self-improvement",
        "model_training": "jarvis-model-training",
        "data_processing": "jarvis-data-processing",
    })

    @classmethod
    def from_env(cls) -> TemporalConfig:
        """
        Create configuration from environment variables.

        Environment Variables:
            TEMPORAL_HOST: Server host (default: localhost)
            TEMPORAL_PORT: Server port (default: 7233)
            TEMPORAL_NAMESPACE: Namespace (default: default)
            TEMPORAL_TASK_QUEUE: Default task queue (default: jarvis-task-queue)
            TEMPORAL_TLS_ENABLED: Enable TLS (default: false)
            TEMPORAL_TLS_CERT: Path to TLS certificate
            TEMPORAL_TLS_KEY: Path to TLS private key

        Returns:
            TemporalConfig instance with values from environment
        """
        return cls(
            host=os.getenv("TEMPORAL_HOST", "localhost"),
            port=int(os.getenv("TEMPORAL_PORT", "7233")),
            namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
            task_queue=os.getenv("TEMPORAL_TASK_QUEUE", "jarvis-task-queue"),
            tls_enabled=os.getenv("TEMPORAL_TLS_ENABLED", "false").lower() == "true",
            tls_cert_path=os.getenv("TEMPORAL_TLS_CERT"),
            tls_key_path=os.getenv("TEMPORAL_TLS_KEY"),
        )

    def get_connection_url(self) -> str:
        """Get Temporal server connection URL."""
        protocol = "https" if self.tls_enabled else "http"
        return f"{protocol}://{self.host}:{self.port}"

    def get_task_queue(self, queue_type: str = "default") -> str:
        """
        Get task queue name for specific type.

        Args:
            queue_type: Queue type (default, high_priority, long_running, etc.)

        Returns:
            Task queue name
        """
        return self.task_queues.get(queue_type, self.task_queue)


# Global configuration instance
_config: Optional[TemporalConfig] = None


def get_temporal_config() -> TemporalConfig:
    """
    Get global Temporal configuration.

    Returns:
        TemporalConfig instance
    """
    global _config
    if _config is None:
        try:
            _config = TemporalConfig.from_env()
        except Exception:
            _config = TemporalConfig()
    return _config


def set_temporal_config(config: TemporalConfig) -> None:
    """
    Set global Temporal configuration.

    Args:
        config: TemporalConfig instance
    """
    global _config
    _config = config
