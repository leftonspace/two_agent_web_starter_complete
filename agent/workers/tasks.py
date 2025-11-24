"""
Celery Task Definitions

Distributed tasks for JARVIS background processing.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from celery import Task, group, chain, chord
from celery.exceptions import SoftTimeLimitExceeded

from .celery_app import app
from ..queue_config import Priority, QueueNames


# =============================================================================
# Base Task Classes
# =============================================================================

class JAR VISTask(Task):
    """Base task class with common functionality"""

    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    max_retries = 3

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        print(f"[Task] {self.name} failed: {exc}")
        # Could send alerts, update metrics, etc.

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry"""
        print(f"[Task] {self.name} retrying due to: {exc}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        print(f"[Task] {self.name} completed successfully")


# =============================================================================
# Model Inference Tasks
# =============================================================================

@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.run_model_inference",
    queue=QueueNames.MODEL_INFERENCE,
    priority=Priority.NORMAL,
    time_limit=300,  # 5 minutes
)
def run_model_inference(
    model_name: str,
    prompt: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run LLM inference as distributed task.

    Args:
        model_name: Model to use
        prompt: Prompt text
        parameters: Optional model parameters

    Returns:
        Dict with completion, usage, cost, etc.
    """
    try:
        # Import here to avoid circular dependencies
        from ..model_router import ModelRouter

        router = ModelRouter()
        result = router.complete(
            prompt=prompt,
            model=model_name,
            **(parameters or {})
        )

        return {
            "success": True,
            "result": result,
            "model": model_name,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except SoftTimeLimitExceeded:
        return {
            "success": False,
            "error": "Task exceeded time limit",
            "model": model_name,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model": model_name,
        }


@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.batch_inference",
    queue=QueueNames.MODEL_INFERENCE,
    priority=Priority.NORMAL,
)
def batch_inference(
    model_name: str,
    prompts: List[str],
    parameters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Run batch inference with parallel execution.

    Args:
        model_name: Model to use
        prompts: List of prompts
        parameters: Optional model parameters

    Returns:
        List of results
    """
    # Create parallel group of tasks
    job = group(
        run_model_inference.s(model_name, prompt, parameters)
        for prompt in prompts
    )

    result = job.apply_async()
    return result.get(timeout=600)  # 10 minute timeout for batch


# =============================================================================
# Long-Running Tasks
# =============================================================================

@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.execute_long_task",
    queue=QueueNames.LONG_RUNNING,
    priority=Priority.LOW,
    time_limit=7200,  # 2 hours
    soft_time_limit=6900,  # 1h 55m
)
def execute_long_task(
    task_type: str,
    task_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute long-running task (multi-hour operations).

    Args:
        task_type: Type of task to execute
        task_config: Task configuration

    Returns:
        Task result
    """
    start_time = time.time()

    try:
        if task_type == "code_analysis":
            return _execute_code_analysis(task_config)
        elif task_type == "model_training":
            return _execute_model_training(task_config)
        elif task_type == "data_processing":
            return _execute_data_processing(task_config)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}",
            }
    except SoftTimeLimitExceeded:
        return {
            "success": False,
            "error": "Task exceeded time limit",
            "elapsed_time": time.time() - start_time,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "elapsed_time": time.time() - start_time,
        }


def _execute_code_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute comprehensive code analysis"""
    # Placeholder for actual implementation
    return {
        "success": True,
        "analysis_type": "code",
        "files_analyzed": config.get("file_count", 0),
        "issues_found": 0,
    }


def _execute_model_training(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute model training/fine-tuning"""
    # Placeholder for actual implementation
    return {
        "success": True,
        "model": config.get("model_name"),
        "epochs": config.get("epochs", 1),
        "final_loss": 0.1,
    }


def _execute_data_processing(config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute data processing pipeline"""
    # Placeholder for actual implementation
    return {
        "success": True,
        "records_processed": config.get("record_count", 0),
        "output_path": config.get("output_path"),
    }


# =============================================================================
# Self-Improvement Tasks
# =============================================================================

@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.self_improve",
    queue=QueueNames.SELF_IMPROVEMENT,
    priority=Priority.HIGH,
)
def self_improve(
    improvement_type: str,
    target: str,
    confidence: float,
) -> Dict[str, Any]:
    """
    Execute self-improvement task.

    Args:
        improvement_type: Type of improvement (prompt, parameter, routing)
        target: What to improve
        confidence: Confidence score for improvement (0-1)

    Returns:
        Improvement result
    """
    try:
        from ..self_refinement import SelfRefinement

        refinement = SelfRefinement()

        if improvement_type == "prompt":
            result = refinement.optimize_prompt(target)
        elif improvement_type == "parameter":
            result = refinement.optimize_parameters(target)
        elif improvement_type == "routing":
            result = refinement.optimize_routing(target)
        else:
            return {
                "success": False,
                "error": f"Unknown improvement type: {improvement_type}",
            }

        return {
            "success": True,
            "improvement_type": improvement_type,
            "target": target,
            "confidence": confidence,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "improvement_type": improvement_type,
        }


@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.periodic_self_evaluation",
    queue=QueueNames.SELF_IMPROVEMENT,
)
def periodic_self_evaluation() -> Dict[str, Any]:
    """
    Periodic self-evaluation task (runs daily).

    Returns:
        Evaluation results and improvement suggestions
    """
    try:
        from ..self_eval import SelfEval
        from ..self_refinement import SelfRefinement

        # Evaluate recent performance
        evaluator = SelfEval()
        eval_results = evaluator.evaluate_recent_runs(days=1)

        # Generate improvement suggestions
        refinement = SelfRefinement()
        suggestions = refinement.suggest_improvements(eval_results)

        # Queue high-confidence improvements for auto-execution
        high_confidence_improvements = [
            s for s in suggestions if s.get("confidence", 0) >= 0.8
        ]

        for improvement in high_confidence_improvements:
            self_improve.apply_async(
                args=[
                    improvement["type"],
                    improvement["target"],
                    improvement["confidence"],
                ],
                priority=Priority.HIGH,
            )

        return {
            "success": True,
            "eval_results": eval_results,
            "suggestions_count": len(suggestions),
            "auto_queued": len(high_confidence_improvements),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# Analytics Tasks
# =============================================================================

@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.process_analytics",
    queue=QueueNames.ANALYTICS,
    priority=Priority.LOW,
)
def process_analytics(
    analytics_type: str,
    data_source: str,
    time_range: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Process analytics data.

    Args:
        analytics_type: Type of analytics (cost, performance, usage)
        data_source: Data source identifier
        time_range: Optional time range (start, end)

    Returns:
        Analytics results
    """
    try:
        from ..analytics import Analytics

        analytics = Analytics()

        if analytics_type == "cost":
            result = analytics.analyze_cost_trends(data_source, time_range)
        elif analytics_type == "performance":
            result = analytics.analyze_performance(data_source, time_range)
        elif analytics_type == "usage":
            result = analytics.analyze_usage_patterns(data_source, time_range)
        else:
            return {
                "success": False,
                "error": f"Unknown analytics type: {analytics_type}",
            }

        return {
            "success": True,
            "analytics_type": analytics_type,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# Maintenance Tasks
# =============================================================================

@app.task(
    base=JAR VISTask,
    name="agent.workers.tasks.cleanup_old_results",
    queue=QueueNames.DEFAULT,
)
def cleanup_old_results() -> Dict[str, Any]:
    """
    Cleanup old task results from Redis.

    Returns:
        Cleanup statistics
    """
    try:
        from celery.result import AsyncResult

        # Get all task IDs from result backend
        # This is a simplified version - production would use Celery's result backend API
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        cleaned_count = 0
        # Placeholder for actual cleanup logic
        # Would iterate through results and delete old ones

        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "cutoff_date": cutoff_date.isoformat(),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# Task Composition Helpers
# =============================================================================

def chain_tasks(*tasks) -> chain:
    """
    Chain tasks to run sequentially.

    Example:
        result = chain_tasks(
            run_model_inference.s("gpt-4o", "prompt1"),
            process_analytics.s("performance", "source1"),
        ).apply_async()
    """
    return chain(*tasks)


def parallel_tasks(*tasks) -> group:
    """
    Run tasks in parallel.

    Example:
        result = parallel_tasks(
            run_model_inference.s("gpt-4o", "prompt1"),
            run_model_inference.s("gpt-4o", "prompt2"),
        ).apply_async()
    """
    return group(*tasks)


def map_reduce_tasks(map_task, reduce_task, items: List) -> chord:
    """
    Map-reduce pattern for distributed processing.

    Example:
        result = map_reduce_tasks(
            run_model_inference.s("gpt-4o"),
            aggregate_results.s(),
            ["prompt1", "prompt2", "prompt3"]
        ).apply_async()
    """
    return chord(
        group(map_task.clone(args=(item,)) for item in items),
        reduce_task
    )
