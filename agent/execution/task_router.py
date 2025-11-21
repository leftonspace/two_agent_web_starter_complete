"""
Task routing system.

Routes tasks to appropriate execution mode based on strategy.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from agent.execution.strategy_decider import StrategyDecider, ExecutionMode
from agent.execution.direct_executor import DirectExecutor
from agent.llm_client import LLMClient
from agent.core_logging import log_event


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"


class TaskRouter:
    """
    Routes tasks to appropriate execution mode.

    Lifecycle:
    1. Receive task
    2. Decide strategy
    3. Route to executor
    4. Monitor execution
    5. Handle failures/retries
    6. Return result
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

        # Components
        self.strategy_decider = StrategyDecider(llm_client)
        self.direct_executor = DirectExecutor(llm_client)
        self.orchestrator = None  # Initialized when needed

        # Task tracking
        self.active_tasks: Dict[str, Dict] = {}

        # Retry settings
        self.max_retries = 2
        self.retry_escalation = True  # Escalate to higher mode on retry

    async def route_task(
        self,
        task_description: str,
        context: Optional[Dict] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route task to appropriate executor.

        Args:
            task_description: What needs to be done
            context: Additional context
            task_id: Optional task ID for tracking

        Returns:
            Execution result with status and data
        """
        # Generate task ID if not provided
        if not task_id:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Initialize task tracking
        self.active_tasks[task_id] = {
            "description": task_description,
            "context": context,
            "status": TaskStatus.PENDING,
            "started_at": datetime.now(),
            "attempts": 0
        }

        try:
            # 1. Decide strategy
            strategy = await self._decide_strategy_with_tracking(
                task_id, task_description, context
            )

            # 2. Check if human approval needed
            if strategy.mode == ExecutionMode.HUMAN_APPROVAL:
                return await self._request_human_approval(
                    task_id, task_description, strategy
                )

            # 3. Execute with retries
            result = await self._execute_with_retry(
                task_id, task_description, context, strategy
            )

            # 4. Mark completed
            self.active_tasks[task_id]["status"] = TaskStatus.COMPLETED
            self.active_tasks[task_id]["completed_at"] = datetime.now()
            self.active_tasks[task_id]["result"] = result

            return result

        except Exception as e:
            self.active_tasks[task_id]["status"] = TaskStatus.FAILED
            self.active_tasks[task_id]["error"] = str(e)

            log_event("task_routing_failed", {
                "task_id": task_id,
                "error": str(e)
            })

            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }

    async def _decide_strategy_with_tracking(
        self,
        task_id: str,
        task_description: str,
        context: Optional[Dict]
    ):
        """Decide strategy and update tracking"""
        self.active_tasks[task_id]["status"] = TaskStatus.ROUTING

        strategy = await self.strategy_decider.decide_strategy(
            task_description, context
        )

        self.active_tasks[task_id]["strategy"] = {
            "mode": strategy.mode.value,
            "rationale": strategy.rationale,
            "estimated_duration": strategy.estimated_duration_seconds,
            "risk_level": strategy.risk_level
        }

        log_event("task_strategy_decided", {
            "task_id": task_id,
            "mode": strategy.mode.value,
            "risk": strategy.risk_level
        })

        return strategy

    async def _execute_with_retry(
        self,
        task_id: str,
        task_description: str,
        context: Optional[Dict],
        strategy
    ) -> Dict[str, Any]:
        """
        Execute task with retry logic.

        On failure, optionally escalates to higher execution mode.
        """
        current_mode = strategy.mode
        attempts = 0
        last_error = None

        while attempts < self.max_retries:
            attempts += 1
            self.active_tasks[task_id]["attempts"] = attempts
            self.active_tasks[task_id]["status"] = TaskStatus.EXECUTING

            try:
                # Route to appropriate executor
                if current_mode == ExecutionMode.DIRECT:
                    result = await self.direct_executor.execute(
                        task_description, context
                    )

                elif current_mode == ExecutionMode.REVIEWED:
                    result = await self._execute_reviewed_mode(
                        task_description, context
                    )

                elif current_mode == ExecutionMode.FULL_LOOP:
                    result = await self._execute_full_loop(
                        task_description, context
                    )

                else:
                    raise ValueError(f"Unknown execution mode: {current_mode}")

                # Check if successful
                if result.get("success"):
                    log_event("task_execution_success", {
                        "task_id": task_id,
                        "mode": current_mode.value,
                        "attempts": attempts
                    })
                    return result
                else:
                    last_error = result.get("error", "Unknown error")

            except Exception as e:
                last_error = str(e)
                log_event("task_execution_attempt_failed", {
                    "task_id": task_id,
                    "attempt": attempts,
                    "error": last_error
                })

            # Retry with escalation if enabled
            if attempts < self.max_retries and self.retry_escalation:
                current_mode = self._escalate_mode(current_mode)
                log_event("task_execution_escalated", {
                    "task_id": task_id,
                    "new_mode": current_mode.value
                })

        # All retries failed
        return {
            "success": False,
            "task_id": task_id,
            "error": f"Failed after {attempts} attempts. Last error: {last_error}",
            "attempts": attempts
        }

    def _escalate_mode(self, current_mode: ExecutionMode) -> ExecutionMode:
        """Escalate to higher execution mode"""
        if current_mode == ExecutionMode.DIRECT:
            return ExecutionMode.REVIEWED
        elif current_mode == ExecutionMode.REVIEWED:
            return ExecutionMode.FULL_LOOP
        else:
            return current_mode  # Already at highest

    async def _execute_reviewed_mode(
        self,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Execute in reviewed mode (Employee + Supervisor).

        Simplified 2-agent process.
        """
        # Initialize orchestrator if needed
        if not self.orchestrator:
            self.orchestrator = self._init_orchestrator()

        # Use orchestrator with simplified flow (skip Manager planning)
        # For now, this is a placeholder - would integrate with actual orchestrator
        log_event("reviewed_mode_execution", {
            "task": task_description
        })

        # Placeholder: Use direct executor as fallback for reviewed mode
        # In production, this would call Employee + Supervisor agents
        result = await self.direct_executor.execute(task_description, context)

        if result.get("success"):
            result["mode"] = "reviewed"

        return result

    async def _execute_full_loop(
        self,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Execute in full loop mode (Manager + Employee + Supervisor)"""
        if not self.orchestrator:
            self.orchestrator = self._init_orchestrator()

        # Placeholder: Full orchestrator integration
        log_event("full_loop_execution", {
            "task": task_description
        })

        # For now, use direct executor as fallback
        # In production, this would call full Manager + Employee + Supervisor flow
        result = await self.direct_executor.execute(task_description, context)

        if result.get("success"):
            result["mode"] = "full_loop"

        return result

    def _init_orchestrator(self):
        """Initialize orchestrator (placeholder)"""
        # Try to import orchestrator, use mock if not available
        try:
            from agent.orchestrator import StrategicOrchestrator
            return StrategicOrchestrator(self.llm)
        except ImportError:
            log_event("orchestrator_not_available", {
                "message": "StrategicOrchestrator not found, using fallback"
            })
            return None

    async def _request_human_approval(
        self,
        task_id: str,
        task_description: str,
        strategy
    ) -> Dict[str, Any]:
        """
        Request human approval for high-risk task.

        Returns immediately with status, human must approve separately.
        """
        self.active_tasks[task_id]["status"] = TaskStatus.REQUIRES_APPROVAL

        log_event("human_approval_requested", {
            "task_id": task_id,
            "task": task_description,
            "risk_level": strategy.risk_level
        })

        return {
            "success": False,
            "task_id": task_id,
            "status": "requires_approval",
            "message": "This task requires human approval before execution",
            "risk_level": strategy.risk_level,
            "rationale": strategy.rationale
        }

    async def approve_and_execute(
        self,
        task_id: str,
        approved: bool
    ) -> Dict[str, Any]:
        """
        Execute task after human approval/rejection.

        Args:
            task_id: Task to approve
            approved: True to execute, False to cancel
        """
        if task_id not in self.active_tasks:
            return {
                "success": False,
                "error": f"Unknown task ID: {task_id}"
            }

        task = self.active_tasks[task_id]

        if task["status"] != TaskStatus.REQUIRES_APPROVAL:
            return {
                "success": False,
                "error": f"Task not waiting for approval: {task['status'].value}"
            }

        if not approved:
            task["status"] = TaskStatus.FAILED
            task["error"] = "Rejected by human"

            log_event("task_rejected_by_human", {
                "task_id": task_id
            })

            return {
                "success": False,
                "task_id": task_id,
                "message": "Task rejected"
            }

        # Approved - execute in full loop mode
        log_event("task_approved_by_human", {
            "task_id": task_id
        })

        return await self._execute_full_loop(
            task["description"],
            task["context"]
        )

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None

        # Convert enum to string for serialization
        return {
            **task,
            "status": task["status"].value if isinstance(task["status"], TaskStatus) else task["status"]
        }

    def list_pending_approvals(self) -> List[Dict]:
        """Get all tasks awaiting human approval"""
        return [
            {
                "task_id": task_id,
                "description": task["description"],
                "strategy": task.get("strategy", {}),
                "requested_at": task["started_at"].isoformat()
            }
            for task_id, task in self.active_tasks.items()
            if task["status"] == TaskStatus.REQUIRES_APPROVAL
        ]

    def get_active_tasks(self) -> List[Dict]:
        """Get all currently active (executing) tasks"""
        return [
            {
                "task_id": task_id,
                "description": task["description"],
                "status": task["status"].value,
                "started_at": task["started_at"].isoformat(),
                "attempts": task.get("attempts", 0)
            }
            for task_id, task in self.active_tasks.items()
            if task["status"] in [TaskStatus.ROUTING, TaskStatus.EXECUTING]
        ]

    def clear_completed_tasks(self, keep_recent: int = 10):
        """
        Clear old completed/failed tasks to prevent memory bloat.

        Args:
            keep_recent: Number of recent tasks to keep
        """
        completed_tasks = [
            (task_id, task)
            for task_id, task in self.active_tasks.items()
            if task["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]

        # Sort by completion time
        completed_tasks.sort(
            key=lambda x: x[1].get("completed_at", x[1]["started_at"]),
            reverse=True
        )

        # Remove old tasks
        for task_id, _ in completed_tasks[keep_recent:]:
            del self.active_tasks[task_id]
