"""
Temporal.io Worker

Worker process that executes workflows and activities.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from .config import get_temporal_config
from . import activities, workflows as wf


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_worker(
    client: Client,
    task_queue: Optional[str] = None,
    workflows_list: Optional[List] = None,
    activities_list: Optional[List] = None,
    max_concurrent_activities: Optional[int] = None,
    max_concurrent_workflows: Optional[int] = None,
) -> Worker:
    """
    Create Temporal worker.

    Args:
        client: Temporal client instance
        task_queue: Task queue name (defaults to config)
        workflows_list: List of workflow classes to register
        activities_list: List of activity functions to register
        max_concurrent_activities: Max concurrent activity executions
        max_concurrent_workflows: Max concurrent workflow executions

    Returns:
        Worker instance
    """
    config = get_temporal_config()

    # Default task queue
    if task_queue is None:
        task_queue = config.task_queue

    # Default workflows
    if workflows_list is None:
        workflows_list = [
            wf.SelfImprovementWorkflow,
            wf.CodeAnalysisWorkflow,
            wf.DataProcessingWorkflow,
            wf.ModelTrainingWorkflow,
            wf.LongRunningTaskWorkflow,
        ]

    # Default activities
    if activities_list is None:
        activities_list = [
            activities.run_code_analysis,
            activities.execute_tests,
            activities.generate_improvement,
            activities.apply_changes,
            activities.validate_changes,
            activities.process_data_batch,
            activities.train_model_step,
            activities.evaluate_model,
            activities.execute_long_running_task,
        ]

    # Concurrency limits
    if max_concurrent_activities is None:
        max_concurrent_activities = config.max_concurrent_activities
    if max_concurrent_workflows is None:
        max_concurrent_workflows = config.max_concurrent_workflows

    # Create worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=workflows_list,
        activities=activities_list,
        max_concurrent_activities=max_concurrent_activities,
        max_concurrent_workflow_tasks=max_concurrent_workflows,
    )

    logger.info(f"Worker created for task queue: {task_queue}")
    logger.info(f"Registered {len(workflows_list)} workflows")
    logger.info(f"Registered {len(activities_list)} activities")
    logger.info(f"Max concurrent activities: {max_concurrent_activities}")
    logger.info(f"Max concurrent workflows: {max_concurrent_workflows}")

    return worker


async def run_worker(
    task_queue: Optional[str] = None,
    workflows_list: Optional[List] = None,
    activities_list: Optional[List] = None,
) -> None:
    """
    Run Temporal worker (blocking).

    Args:
        task_queue: Task queue name (defaults to config)
        workflows_list: List of workflow classes to register
        activities_list: List of activity functions to register
    """
    config = get_temporal_config()

    logger.info("Starting Temporal worker")
    logger.info(f"Connecting to Temporal server at {config.get_connection_url()}")

    # Connect to Temporal server
    client = await Client.connect(
        f"{config.host}:{config.port}",
        namespace=config.namespace,
    )

    logger.info(f"Connected to namespace: {config.namespace}")

    # Create and run worker
    worker = await create_worker(
        client,
        task_queue=task_queue,
        workflows_list=workflows_list,
        activities_list=activities_list,
    )

    logger.info("Worker started - waiting for tasks...")

    try:
        # Run worker (blocks until interrupted)
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Worker interrupted - shutting down")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        logger.info("Worker stopped")


def main():
    """
    Main entry point for worker process.

    Usage:
        python -m agent.temporal.worker
    """
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise


if __name__ == "__main__":
    main()
