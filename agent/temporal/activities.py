"""
Temporal.io Activity Definitions

Activities are units of work that can be retried, have timeouts, and can be
executed by any worker. They should be deterministic or idempotent.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from temporalio import activity

# =============================================================================
# Code Analysis Activities
# =============================================================================


@activity.defn
async def run_code_analysis(
    repo_path: str,
    file_patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run static code analysis on repository.

    Args:
        repo_path: Path to repository
        file_patterns: Optional file patterns to analyze

    Returns:
        Analysis results with issues, metrics, suggestions
    """
    activity.logger.info(f"Running code analysis on {repo_path}")

    # Heartbeat to show we're alive
    activity.heartbeat("Starting analysis")

    try:
        # Import here to avoid circular dependencies
        from ..tools.builtin.format_code import analyze_code

        results = {
            "repo_path": repo_path,
            "analyzed_at": datetime.utcnow().isoformat(),
            "issues": [],
            "metrics": {},
            "suggestions": [],
        }

        # Simulate analysis (replace with actual implementation)
        activity.heartbeat("Analyzing files")
        await asyncio.sleep(2)  # Placeholder for actual analysis

        results["issues"] = [
            {"file": "example.py", "line": 42, "severity": "warning", "message": "Unused variable"}
        ]
        results["metrics"] = {"lines": 1000, "complexity": 15}
        results["suggestions"] = ["Consider refactoring function X"]

        activity.logger.info(f"Analysis complete: {len(results['issues'])} issues found")
        return results

    except Exception as e:
        activity.logger.error(f"Code analysis failed: {e}")
        raise


@activity.defn
async def execute_tests(
    test_path: str,
    test_pattern: str = "test_*.py",
) -> Dict[str, Any]:
    """
    Execute test suite.

    Args:
        test_path: Path to tests
        test_pattern: Test file pattern

    Returns:
        Test results with pass/fail counts
    """
    activity.logger.info(f"Executing tests in {test_path}")
    activity.heartbeat("Running tests")

    try:
        # Import here to avoid circular dependencies
        from ..tools.builtin.run_tests import run_pytest

        results = {
            "test_path": test_path,
            "executed_at": datetime.utcnow().isoformat(),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "total": 0,
            "failures": [],
        }

        # Simulate test execution
        await asyncio.sleep(3)
        results["passed"] = 45
        results["failed"] = 2
        results["total"] = 47

        activity.logger.info(f"Tests complete: {results['passed']}/{results['total']} passed")
        return results

    except Exception as e:
        activity.logger.error(f"Test execution failed: {e}")
        raise


# =============================================================================
# Self-Improvement Activities
# =============================================================================


@activity.defn
async def generate_improvement(
    analysis_results: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate improvement suggestions based on analysis.

    Args:
        analysis_results: Results from code analysis
        context: Additional context (metrics, history, etc.)

    Returns:
        Improvement plan with changes to make
    """
    activity.logger.info("Generating improvement suggestions")
    activity.heartbeat("Analyzing issues")

    try:
        # Import here to avoid circular dependencies
        from ..auto_improver import AutoImprover

        improvement = {
            "generated_at": datetime.utcnow().isoformat(),
            "confidence": 0.85,
            "changes": [],
            "rationale": "Based on analysis findings",
        }

        # Simulate LLM-based improvement generation
        await asyncio.sleep(5)
        improvement["changes"] = [
            {"file": "example.py", "type": "refactor", "description": "Extract method"}
        ]

        activity.logger.info(f"Generated {len(improvement['changes'])} improvements")
        return improvement

    except Exception as e:
        activity.logger.error(f"Improvement generation failed: {e}")
        raise


@activity.defn
async def apply_changes(
    changes: List[Dict[str, Any]],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Apply code changes.

    Args:
        changes: List of changes to apply
        dry_run: If True, simulate changes without applying

    Returns:
        Results of applying changes
    """
    activity.logger.info(f"Applying {len(changes)} changes (dry_run={dry_run})")

    results = {
        "applied_at": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
        "successful": [],
        "failed": [],
    }

    for i, change in enumerate(changes):
        activity.heartbeat(f"Applying change {i+1}/{len(changes)}")

        try:
            # Simulate applying change
            await asyncio.sleep(1)
            results["successful"].append(change)

        except Exception as e:
            activity.logger.warning(f"Failed to apply change: {e}")
            results["failed"].append({"change": change, "error": str(e)})

    activity.logger.info(f"Changes applied: {len(results['successful'])} successful, {len(results['failed'])} failed")
    return results


@activity.defn
async def validate_changes(
    changes: List[Dict[str, Any]],
    validation_strategy: str = "full",
) -> Dict[str, Any]:
    """
    Validate applied changes.

    Args:
        changes: Changes that were applied
        validation_strategy: Validation approach (quick, full, etc.)

    Returns:
        Validation results
    """
    activity.logger.info(f"Validating {len(changes)} changes with strategy={validation_strategy}")
    activity.heartbeat("Running validation")

    try:
        # Run tests
        test_results = await execute_tests("tests/")

        # Check if changes broke anything
        validation = {
            "validated_at": datetime.utcnow().isoformat(),
            "strategy": validation_strategy,
            "tests_passed": test_results["passed"] == test_results["total"],
            "issues_found": [],
            "approved": True,
        }

        if not validation["tests_passed"]:
            validation["approved"] = False
            validation["issues_found"].append("Test failures detected")

        activity.logger.info(f"Validation complete: approved={validation['approved']}")
        return validation

    except Exception as e:
        activity.logger.error(f"Validation failed: {e}")
        raise


# =============================================================================
# Data Processing Activities
# =============================================================================


@activity.defn
async def process_data_batch(
    batch_id: int,
    data_source: str,
    batch_size: int = 1000,
) -> Dict[str, Any]:
    """
    Process a batch of data.

    Args:
        batch_id: Batch identifier
        data_source: Data source path/URL
        batch_size: Number of records per batch

    Returns:
        Processing results
    """
    activity.logger.info(f"Processing batch {batch_id} from {data_source}")

    results = {
        "batch_id": batch_id,
        "processed_at": datetime.utcnow().isoformat(),
        "records_processed": 0,
        "records_failed": 0,
        "errors": [],
    }

    try:
        # Simulate batch processing with heartbeats
        for i in range(batch_size):
            if i % 100 == 0:
                activity.heartbeat(f"Processed {i}/{batch_size} records")
                await asyncio.sleep(0.1)

            results["records_processed"] += 1

        activity.logger.info(f"Batch {batch_id} complete: {results['records_processed']} records")
        return results

    except Exception as e:
        activity.logger.error(f"Batch {batch_id} failed: {e}")
        raise


# =============================================================================
# Model Training Activities
# =============================================================================


@activity.defn
async def train_model_step(
    model_id: str,
    step: int,
    training_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute one step of model training.

    Args:
        model_id: Model identifier
        step: Training step number
        training_data: Training data configuration

    Returns:
        Training step results
    """
    activity.logger.info(f"Training model {model_id}, step {step}")
    activity.heartbeat(f"Training step {step}")

    try:
        # Simulate training step
        await asyncio.sleep(10)

        results = {
            "model_id": model_id,
            "step": step,
            "trained_at": datetime.utcnow().isoformat(),
            "loss": 0.5 / (step + 1),  # Simulated decreasing loss
            "accuracy": min(0.99, 0.5 + (step * 0.05)),
            "metrics": {},
        }

        activity.logger.info(f"Step {step} complete: loss={results['loss']:.4f}, accuracy={results['accuracy']:.4f}")
        return results

    except Exception as e:
        activity.logger.error(f"Training step {step} failed: {e}")
        raise


@activity.defn
async def evaluate_model(
    model_id: str,
    test_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate trained model.

    Args:
        model_id: Model identifier
        test_data: Test data configuration

    Returns:
        Evaluation results
    """
    activity.logger.info(f"Evaluating model {model_id}")
    activity.heartbeat("Running evaluation")

    try:
        # Simulate evaluation
        await asyncio.sleep(5)

        results = {
            "model_id": model_id,
            "evaluated_at": datetime.utcnow().isoformat(),
            "accuracy": 0.92,
            "precision": 0.90,
            "recall": 0.94,
            "f1_score": 0.92,
            "confusion_matrix": [[100, 5], [3, 92]],
        }

        activity.logger.info(f"Evaluation complete: accuracy={results['accuracy']:.4f}")
        return results

    except Exception as e:
        activity.logger.error(f"Model evaluation failed: {e}")
        raise


# =============================================================================
# Generic Long-Running Activities
# =============================================================================


@activity.defn
async def execute_long_running_task(
    task_id: str,
    task_type: str,
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a long-running task with heartbeats.

    Args:
        task_id: Task identifier
        task_type: Type of task
        parameters: Task parameters

    Returns:
        Task execution results
    """
    activity.logger.info(f"Executing long-running task {task_id} of type {task_type}")

    results = {
        "task_id": task_id,
        "task_type": task_type,
        "started_at": datetime.utcnow().isoformat(),
        "status": "running",
        "progress": 0.0,
        "result": None,
    }

    try:
        # Simulate long-running task with progress updates
        total_steps = parameters.get("steps", 100)

        for step in range(total_steps):
            # Heartbeat every 10 steps
            if step % 10 == 0:
                progress = (step + 1) / total_steps
                results["progress"] = progress
                activity.heartbeat(f"Progress: {progress:.1%}")

            # Simulate work
            await asyncio.sleep(0.5)

        results["status"] = "completed"
        results["progress"] = 1.0
        results["completed_at"] = datetime.utcnow().isoformat()
        results["result"] = {"success": True, "output": "Task completed successfully"}

        activity.logger.info(f"Task {task_id} completed successfully")
        return results

    except Exception as e:
        activity.logger.error(f"Task {task_id} failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        raise
