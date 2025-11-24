"""
Temporal.io Integration for JARVIS

Provides durable, long-running workflow orchestration with advanced features:
- Workflow versioning and evolution
- Long-running sagas (days, months, years)
- Deterministic execution with replay
- External signals and queries
- Automatic state management and recovery
- Distributed workflow execution

This complements Celery by providing workflow-level orchestration
for complex, multi-step, long-running processes.
"""

from .config import TemporalConfig, get_temporal_config
from .client import TemporalClient, start_workflow, query_workflow, signal_workflow
from .workflows import (
    SelfImprovementWorkflow,
    CodeAnalysisWorkflow,
    DataProcessingWorkflow,
    ModelTrainingWorkflow,
    LongRunningTaskWorkflow,
)
from .activities import (
    run_code_analysis,
    execute_tests,
    generate_improvement,
    apply_changes,
    validate_changes,
    process_data_batch,
    train_model_step,
    evaluate_model,
)

__all__ = [
    # Config
    "TemporalConfig",
    "get_temporal_config",
    # Client
    "TemporalClient",
    "start_workflow",
    "query_workflow",
    "signal_workflow",
    # Workflows
    "SelfImprovementWorkflow",
    "CodeAnalysisWorkflow",
    "DataProcessingWorkflow",
    "ModelTrainingWorkflow",
    "LongRunningTaskWorkflow",
    # Activities
    "run_code_analysis",
    "execute_tests",
    "generate_improvement",
    "apply_changes",
    "validate_changes",
    "process_data_batch",
    "train_model_step",
    "evaluate_model",
]
