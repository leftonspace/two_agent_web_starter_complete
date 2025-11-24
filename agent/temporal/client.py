"""
Temporal.io Client

Client for starting workflows, sending signals, and executing queries.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Type, TypeVar

from temporalio.client import Client, WorkflowHandle
from temporalio.exceptions import WorkflowAlreadyStartedError

from .config import get_temporal_config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Type variable for workflow types
WorkflowType = TypeVar("WorkflowType")


class TemporalClient:
    """
    High-level Temporal client for JARVIS.

    Provides easy-to-use interface for starting workflows, sending signals,
    and executing queries.
    """

    def __init__(self, client: Optional[Client] = None):
        """
        Initialize Temporal client.

        Args:
            client: Optional Temporal client instance (will create if not provided)
        """
        self._client = client
        self._config = get_temporal_config()

    async def _ensure_client(self) -> Client:
        """Ensure client is connected."""
        if self._client is None:
            logger.info(f"Connecting to Temporal server at {self._config.get_connection_url()}")
            self._client = await Client.connect(
                f"{self._config.host}:{self._config.port}",
                namespace=self._config.namespace,
            )
            logger.info(f"Connected to namespace: {self._config.namespace}")
        return self._client

    async def start_workflow(
        self,
        workflow_class: Type[WorkflowType],
        workflow_id: str,
        *args: Any,
        task_queue: Optional[str] = None,
        **kwargs: Any,
    ) -> WorkflowHandle:
        """
        Start a new workflow.

        Args:
            workflow_class: Workflow class to start
            workflow_id: Unique workflow identifier
            *args: Positional arguments for workflow
            task_queue: Task queue (defaults to config)
            **kwargs: Keyword arguments for workflow

        Returns:
            WorkflowHandle for interacting with workflow

        Raises:
            WorkflowAlreadyStartedError: If workflow with this ID already exists
        """
        client = await self._ensure_client()

        if task_queue is None:
            task_queue = self._config.task_queue

        logger.info(f"Starting workflow {workflow_class.__name__} with ID: {workflow_id}")

        try:
            handle = await client.start_workflow(
                workflow_class.run,
                *args,
                id=workflow_id,
                task_queue=task_queue,
                **kwargs,
            )

            logger.info(f"Workflow started: {workflow_id}")
            return handle

        except WorkflowAlreadyStartedError:
            logger.warning(f"Workflow already exists: {workflow_id}")
            # Return handle to existing workflow
            return client.get_workflow_handle(workflow_id)

    async def get_workflow_result(
        self,
        workflow_id: str,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Wait for workflow to complete and get result.

        Args:
            workflow_id: Workflow identifier
            timeout: Optional timeout in seconds

        Returns:
            Workflow result
        """
        client = await self._ensure_client()
        handle = client.get_workflow_handle(workflow_id)

        logger.info(f"Waiting for workflow result: {workflow_id}")

        if timeout:
            result = await asyncio.wait_for(handle.result(), timeout=timeout)
        else:
            result = await handle.result()

        logger.info(f"Workflow completed: {workflow_id}")
        return result

    async def send_signal(
        self,
        workflow_id: str,
        signal_name: str,
        *args: Any,
    ) -> None:
        """
        Send signal to running workflow.

        Args:
            workflow_id: Workflow identifier
            signal_name: Signal name
            *args: Signal arguments
        """
        client = await self._ensure_client()
        handle = client.get_workflow_handle(workflow_id)

        logger.info(f"Sending signal {signal_name} to workflow: {workflow_id}")
        await handle.signal(signal_name, *args)
        logger.info(f"Signal sent: {signal_name}")

    async def query_workflow(
        self,
        workflow_id: str,
        query_name: str,
        *args: Any,
    ) -> Any:
        """
        Execute query on running workflow.

        Args:
            workflow_id: Workflow identifier
            query_name: Query name
            *args: Query arguments

        Returns:
            Query result
        """
        client = await self._ensure_client()
        handle = client.get_workflow_handle(workflow_id)

        logger.info(f"Querying workflow {workflow_id}: {query_name}")
        result = await handle.query(query_name, *args)
        logger.info(f"Query result received")
        return result

    async def cancel_workflow(
        self,
        workflow_id: str,
    ) -> None:
        """
        Cancel running workflow.

        Args:
            workflow_id: Workflow identifier
        """
        client = await self._ensure_client()
        handle = client.get_workflow_handle(workflow_id)

        logger.info(f"Cancelling workflow: {workflow_id}")
        await handle.cancel()
        logger.info(f"Workflow cancelled: {workflow_id}")

    async def terminate_workflow(
        self,
        workflow_id: str,
        reason: str = "Terminated by client",
    ) -> None:
        """
        Terminate running workflow (immediate stop, no cleanup).

        Args:
            workflow_id: Workflow identifier
            reason: Termination reason
        """
        client = await self._ensure_client()
        handle = client.get_workflow_handle(workflow_id)

        logger.info(f"Terminating workflow: {workflow_id} - Reason: {reason}")
        await handle.terminate(reason)
        logger.info(f"Workflow terminated: {workflow_id}")

    async def get_workflow_status(
        self,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Get workflow status.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Status information
        """
        client = await self._ensure_client()
        handle = client.get_workflow_handle(workflow_id)

        # Try to query workflow for status
        try:
            status = await handle.query("get_status")
            return status
        except Exception:
            # If no status query, return basic info
            return {
                "workflow_id": workflow_id,
                "status": "unknown",
            }

    async def close(self) -> None:
        """Close client connection."""
        if self._client:
            logger.info("Closing Temporal client")
            # Temporal client doesn't have explicit close, but we can clean up
            self._client = None


# =============================================================================
# Convenience Functions
# =============================================================================


async def start_workflow(
    workflow_class: Type[WorkflowType],
    workflow_id: str,
    *args: Any,
    task_queue: Optional[str] = None,
    **kwargs: Any,
) -> WorkflowHandle:
    """
    Start a workflow (convenience function).

    Args:
        workflow_class: Workflow class to start
        workflow_id: Unique workflow identifier
        *args: Positional arguments for workflow
        task_queue: Task queue (defaults to config)
        **kwargs: Keyword arguments for workflow

    Returns:
        WorkflowHandle for interacting with workflow
    """
    client = TemporalClient()
    return await client.start_workflow(
        workflow_class,
        workflow_id,
        *args,
        task_queue=task_queue,
        **kwargs,
    )


async def query_workflow(
    workflow_id: str,
    query_name: str,
    *args: Any,
) -> Any:
    """
    Query a workflow (convenience function).

    Args:
        workflow_id: Workflow identifier
        query_name: Query name
        *args: Query arguments

    Returns:
        Query result
    """
    client = TemporalClient()
    return await client.query_workflow(workflow_id, query_name, *args)


async def signal_workflow(
    workflow_id: str,
    signal_name: str,
    *args: Any,
) -> None:
    """
    Send signal to workflow (convenience function).

    Args:
        workflow_id: Workflow identifier
        signal_name: Signal name
        *args: Signal arguments
    """
    client = TemporalClient()
    await client.send_signal(workflow_id, signal_name, *args)


# =============================================================================
# Example Usage
# =============================================================================


async def example_self_improvement():
    """Example: Start self-improvement workflow."""
    from .workflows import SelfImprovementWorkflow

    client = TemporalClient()

    # Start workflow
    handle = await client.start_workflow(
        SelfImprovementWorkflow,
        workflow_id="self-improvement-001",
        repo_path="/path/to/repo",
        auto_apply=True,
        confidence_threshold=0.8,
    )

    logger.info(f"Started workflow: {handle.id}")

    # Query progress
    progress = await client.query_workflow(
        handle.id,
        "get_progress",
    )
    logger.info(f"Progress: {progress}")

    # Wait for result (or timeout)
    try:
        result = await asyncio.wait_for(handle.result(), timeout=3600)
        logger.info(f"Workflow completed: {result}")
    except asyncio.TimeoutError:
        logger.info("Workflow still running after 1 hour")

    await client.close()


async def example_long_running_task():
    """Example: Start long-running task with pause/resume."""
    from .workflows import LongRunningTaskWorkflow

    client = TemporalClient()

    # Start workflow
    handle = await client.start_workflow(
        LongRunningTaskWorkflow,
        workflow_id="long-task-001",
        task_id="task-001",
        task_type="data_processing",
        parameters={"steps": 100},
    )

    logger.info(f"Started workflow: {handle.id}")

    # Wait a bit then pause
    await asyncio.sleep(5)
    await client.send_signal(handle.id, "pause")
    logger.info("Paused workflow")

    # Check status
    status = await client.get_workflow_status(handle.id)
    logger.info(f"Status: {status}")

    # Resume
    await client.send_signal(handle.id, "resume")
    logger.info("Resumed workflow")

    # Wait for completion
    result = await handle.result()
    logger.info(f"Workflow completed: {result}")

    await client.close()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_self_improvement())
