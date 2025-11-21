"""
Execution strategy module.

PHASE 7B.1: Intelligent execution strategy selection.
PHASE 7B.2: Direct execution mode for simple tasks.
PHASE 7B.3: Task routing logic with retry and escalation.
PHASE 7C.1: Employee AI pool management for parallel execution.
PHASE 7C.2: Parallel task distribution with priority queuing.
PHASE 7C.3: Supervisor review queue with quality gates.

Decides HOW to execute tasks based on complexity, risk, and cost.
Executes simple tasks directly without multi-agent review.
Routes tasks to appropriate executors with automatic retry and escalation.
Manages multiple concurrent Employee agents for parallel task execution.
Distributes tasks intelligently with priority, dependencies, and load balancing.
Reviews Employee work with quality gates and automated approval.
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
from agent.execution.task_distributor import (
    TaskDistributor,
    TaskPriority,
    TaskRequest,
    TaskResult
)
from agent.execution.review_queue import (
    ReviewQueueManager,
    RiskLevel,
    WorkType,
    ReviewStatus,
    ReviewItem,
    ReviewResult,
    QualityGateResult
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
    "EmployeeWorker",
    "TaskDistributor",
    "TaskPriority",
    "TaskRequest",
    "TaskResult",
    "ReviewQueueManager",
    "RiskLevel",
    "WorkType",
    "ReviewStatus",
    "ReviewItem",
    "ReviewResult",
    "QualityGateResult"
]
