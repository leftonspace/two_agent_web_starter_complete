"""
Temporal.io Workflow Definitions

Workflows are durable, versioned, long-running processes that coordinate activities.
They are deterministic and can be replayed from history.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities
with workflow.unsafe.imports_passed_through():
    from . import activities


# =============================================================================
# Self-Improvement Workflow
# =============================================================================


@workflow.defn
class SelfImprovementWorkflow:
    """
    Long-running workflow for continuous self-improvement.

    This workflow can run for days/weeks, continuously analyzing code,
    generating improvements, and applying changes with validation.
    """

    @workflow.run
    async def run(
        self,
        repo_path: str,
        auto_apply: bool = False,
        confidence_threshold: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Execute self-improvement workflow.

        Args:
            repo_path: Path to repository
            auto_apply: Auto-apply high-confidence changes
            confidence_threshold: Minimum confidence for auto-apply

        Returns:
            Workflow results with improvements made
        """
        workflow.logger.info(f"Starting self-improvement workflow for {repo_path}")

        results = {
            "repo_path": repo_path,
            "iterations": [],
            "total_improvements": 0,
            "total_changes_applied": 0,
        }

        # Iteration 1: Analysis
        workflow.logger.info("Phase 1: Code Analysis")
        analysis = await workflow.execute_activity(
            activities.run_code_analysis,
            repo_path,
            start_to_close_timeout=timedelta(hours=1),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=100),
                backoff_coefficient=2.0,
            ),
        )

        # Iteration 2: Test Execution
        workflow.logger.info("Phase 2: Test Execution")
        test_results = await workflow.execute_activity(
            activities.execute_tests,
            "tests/",
            start_to_close_timeout=timedelta(minutes=30),
        )

        # Check if tests pass
        if test_results["failed"] > 0:
            workflow.logger.warning(f"Tests failing: {test_results['failed']} failures")

        # Iteration 3: Generate Improvements
        workflow.logger.info("Phase 3: Generate Improvements")
        improvement = await workflow.execute_activity(
            activities.generate_improvement,
            analysis,
            {"test_results": test_results},
            start_to_close_timeout=timedelta(minutes=30),
        )

        results["total_improvements"] = len(improvement["changes"])

        # Iteration 4: Apply Changes (if confidence high enough)
        if auto_apply and improvement["confidence"] >= confidence_threshold:
            workflow.logger.info(f"Phase 4: Applying {len(improvement['changes'])} changes (confidence={improvement['confidence']:.2f})")

            # Apply changes
            apply_results = await workflow.execute_activity(
                activities.apply_changes,
                improvement["changes"],
                False,  # dry_run=False
                start_to_close_timeout=timedelta(minutes=20),
            )

            results["total_changes_applied"] = len(apply_results["successful"])

            # Iteration 5: Validate Changes
            if apply_results["successful"]:
                workflow.logger.info("Phase 5: Validating Changes")
                validation = await workflow.execute_activity(
                    activities.validate_changes,
                    apply_results["successful"],
                    "full",
                    start_to_close_timeout=timedelta(hours=1),
                )

                if not validation["approved"]:
                    workflow.logger.error("Validation failed - changes may need rollback")
                    results["validation_failed"] = True
                else:
                    workflow.logger.info("Validation passed - changes approved")

        else:
            workflow.logger.info(f"Skipping auto-apply (confidence={improvement['confidence']:.2f} < {confidence_threshold})")
            results["changes_pending_approval"] = improvement["changes"]

        results["iterations"].append({
            "analysis": analysis,
            "tests": test_results,
            "improvement": improvement,
        })

        workflow.logger.info(f"Self-improvement workflow complete: {results['total_improvements']} improvements, {results['total_changes_applied']} applied")
        return results

    @workflow.signal
    async def approve_changes(self, change_ids: List[str]) -> None:
        """Signal to approve pending changes."""
        workflow.logger.info(f"Received approval for changes: {change_ids}")
        # Implementation would apply approved changes

    @workflow.query
    def get_progress(self) -> Dict[str, Any]:
        """Query current workflow progress."""
        return {
            "status": "running",
            "current_phase": "analysis",
            "progress": 0.5,
        }


# =============================================================================
# Code Analysis Workflow
# =============================================================================


@workflow.defn
class CodeAnalysisWorkflow:
    """
    Workflow for comprehensive code analysis across large repositories.

    Can run for hours analyzing millions of lines of code.
    """

    @workflow.run
    async def run(
        self,
        repo_path: str,
        analysis_types: List[str],
    ) -> Dict[str, Any]:
        """
        Execute code analysis workflow.

        Args:
            repo_path: Path to repository
            analysis_types: Types of analysis to run (static, security, complexity, etc.)

        Returns:
            Comprehensive analysis results
        """
        workflow.logger.info(f"Starting code analysis workflow for {repo_path}")

        results = {
            "repo_path": repo_path,
            "analysis_types": analysis_types,
            "analyses": {},
        }

        # Run each analysis type
        for analysis_type in analysis_types:
            workflow.logger.info(f"Running {analysis_type} analysis")

            analysis = await workflow.execute_activity(
                activities.run_code_analysis,
                repo_path,
                None,  # file_patterns
                start_to_close_timeout=timedelta(hours=2),
                heartbeat_timeout=timedelta(seconds=30),
            )

            results["analyses"][analysis_type] = analysis

            # Allow workflow to continue even if one analysis fails
            workflow.logger.info(f"{analysis_type} analysis complete")

        workflow.logger.info(f"Code analysis workflow complete: {len(results['analyses'])} analyses")
        return results


# =============================================================================
# Data Processing Workflow
# =============================================================================


@workflow.defn
class DataProcessingWorkflow:
    """
    Workflow for processing large datasets in batches.

    Can process millions of records over days/weeks.
    """

    @workflow.run
    async def run(
        self,
        data_source: str,
        total_records: int,
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        """
        Execute data processing workflow.

        Args:
            data_source: Data source path/URL
            total_records: Total number of records to process
            batch_size: Records per batch

        Returns:
            Processing results
        """
        workflow.logger.info(f"Starting data processing workflow: {total_records} records in batches of {batch_size}")

        num_batches = (total_records + batch_size - 1) // batch_size
        results = {
            "data_source": data_source,
            "total_records": total_records,
            "batch_size": batch_size,
            "num_batches": num_batches,
            "batches_completed": 0,
            "records_processed": 0,
            "records_failed": 0,
        }

        # Process batches in parallel (with limited concurrency)
        for batch_id in range(num_batches):
            workflow.logger.info(f"Processing batch {batch_id + 1}/{num_batches}")

            batch_results = await workflow.execute_activity(
                activities.process_data_batch,
                batch_id,
                data_source,
                batch_size,
                start_to_close_timeout=timedelta(hours=1),
                heartbeat_timeout=timedelta(seconds=30),
            )

            results["batches_completed"] += 1
            results["records_processed"] += batch_results["records_processed"]
            results["records_failed"] += batch_results["records_failed"]

            # Sleep between batches to avoid overwhelming system
            await workflow.sleep(1)

        workflow.logger.info(f"Data processing complete: {results['records_processed']} records processed")
        return results


# =============================================================================
# Model Training Workflow
# =============================================================================


@workflow.defn
class ModelTrainingWorkflow:
    """
    Workflow for training machine learning models.

    Can run for days/weeks training complex models with checkpointing.
    """

    @workflow.run
    async def run(
        self,
        model_id: str,
        training_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute model training workflow.

        Args:
            model_id: Model identifier
            training_config: Training configuration

        Returns:
            Training results
        """
        workflow.logger.info(f"Starting model training workflow for {model_id}")

        num_steps = training_config.get("num_steps", 100)
        results = {
            "model_id": model_id,
            "num_steps": num_steps,
            "steps_completed": 0,
            "training_history": [],
        }

        # Training loop
        for step in range(num_steps):
            workflow.logger.info(f"Training step {step + 1}/{num_steps}")

            step_results = await workflow.execute_activity(
                activities.train_model_step,
                model_id,
                step,
                training_config,
                start_to_close_timeout=timedelta(hours=2),
                heartbeat_timeout=timedelta(seconds=30),
            )

            results["steps_completed"] += 1
            results["training_history"].append(step_results)

            # Check if training should stop early
            if step_results["accuracy"] >= training_config.get("target_accuracy", 0.95):
                workflow.logger.info(f"Target accuracy reached at step {step + 1}")
                break

            # Sleep between steps
            await workflow.sleep(0.1)

        # Final evaluation
        workflow.logger.info("Running final evaluation")
        evaluation = await workflow.execute_activity(
            activities.evaluate_model,
            model_id,
            training_config.get("test_data", {}),
            start_to_close_timeout=timedelta(minutes=30),
        )

        results["final_evaluation"] = evaluation

        workflow.logger.info(f"Model training complete: {results['steps_completed']} steps, accuracy={evaluation['accuracy']:.4f}")
        return results

    @workflow.signal
    async def pause_training(self) -> None:
        """Signal to pause training."""
        workflow.logger.info("Received pause signal")
        # Implementation would pause training

    @workflow.signal
    async def resume_training(self) -> None:
        """Signal to resume training."""
        workflow.logger.info("Received resume signal")
        # Implementation would resume training

    @workflow.query
    def get_training_progress(self) -> Dict[str, Any]:
        """Query current training progress."""
        return {
            "status": "training",
            "steps_completed": 0,
            "current_loss": 0.5,
            "current_accuracy": 0.8,
        }


# =============================================================================
# Generic Long-Running Task Workflow
# =============================================================================


@workflow.defn
class LongRunningTaskWorkflow:
    """
    Generic workflow for long-running tasks with monitoring and control.

    Provides signals for pause/resume/cancel and queries for progress.
    """

    def __init__(self) -> None:
        self._paused = False
        self._cancelled = False
        self._progress = 0.0

    @workflow.run
    async def run(
        self,
        task_id: str,
        task_type: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute long-running task workflow.

        Args:
            task_id: Task identifier
            task_type: Type of task
            parameters: Task parameters

        Returns:
            Task results
        """
        workflow.logger.info(f"Starting long-running task workflow: {task_id}")

        results = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "running",
        }

        # Execute task with support for pause/cancel
        try:
            # Check if cancelled
            if self._cancelled:
                workflow.logger.info("Task cancelled before execution")
                results["status"] = "cancelled"
                return results

            # Wait if paused
            await workflow.wait_condition(lambda: not self._paused)

            # Execute activity
            task_results = await workflow.execute_activity(
                activities.execute_long_running_task,
                task_id,
                task_type,
                parameters,
                start_to_close_timeout=timedelta(hours=24),
                heartbeat_timeout=timedelta(seconds=30),
            )

            results.update(task_results)
            results["status"] = "completed"

        except Exception as e:
            workflow.logger.error(f"Task failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            raise

        workflow.logger.info(f"Long-running task workflow complete: {task_id}")
        return results

    @workflow.signal
    async def pause(self) -> None:
        """Signal to pause task."""
        workflow.logger.info("Pausing task")
        self._paused = True

    @workflow.signal
    async def resume(self) -> None:
        """Signal to resume task."""
        workflow.logger.info("Resuming task")
        self._paused = False

    @workflow.signal
    async def cancel(self) -> None:
        """Signal to cancel task."""
        workflow.logger.info("Cancelling task")
        self._cancelled = True

    @workflow.query
    def get_status(self) -> Dict[str, Any]:
        """Query current task status."""
        return {
            "paused": self._paused,
            "cancelled": self._cancelled,
            "progress": self._progress,
        }
