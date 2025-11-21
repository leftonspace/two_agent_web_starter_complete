"""
Execution strategy module.

PHASE 7B.1: Intelligent execution strategy selection.
PHASE 7B.2: Direct execution mode for simple tasks.
PHASE 7B.3: Task routing logic with retry and escalation.
PHASE 7C.1: Employee AI pool management for parallel execution.

Decides HOW to execute tasks based on complexity, risk, and cost.
Executes simple tasks directly without multi-agent review.
Routes tasks to appropriate executors with automatic retry and escalation.
Manages multiple concurrent Employee agents for parallel task execution.
"""

from agent.execution.strategy_decider import (
    StrategyDecider,
    ExecutionMode,
    ExecutionStrategy,
    StrategyOverrides
)
from agent.execution.direct_executor import (
    DirectExecutor,
    DirectActionType
)
from agent.execution.task_router import (
    TaskRouter,
    TaskStatus
)
from agent.execution.employee_pool import (
    EmployeePool,
    EmployeeSpecialty,
    EmployeeStatus,
    EmployeeWorker
)

__all__ = [
    "StrategyDecider",
    "ExecutionMode",
    "ExecutionStrategy",
    "StrategyOverrides",
    "DirectExecutor",
    "DirectActionType",
    "TaskRouter",
    "TaskStatus",
    "EmployeePool",
    "EmployeeSpecialty",
    "EmployeeStatus",
    "EmployeeWorker"
]
