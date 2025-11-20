"""
PHASE 4.3: Checkpoint/Resume System for Orchestrator Reliability (R4)

Provides checkpoint persistence to enable orchestrator crash recovery.
After each iteration, the orchestrator saves state to a checkpoint file.
On restart, the orchestrator can resume from the last checkpoint.

Checkpoint Data:
- iteration_index: Current iteration number
- files_written: List of files created/modified
- cost_accumulated: Current cost in USD
- last_status: Last manager review status
- last_feedback: Last manager feedback
- plan: Original plan
- phases: Supervisor phases
- task: Original task
- timestamp: When checkpoint was created

Usage:
    # Save checkpoint after iteration
    checkpoint_mgr = CheckpointManager(run_id="abc123")
    checkpoint_mgr.save_checkpoint(
        iteration=2,
        files_written=["index.html", "styles.css"],
        cost_accumulated=0.45,
        last_status="needs_changes",
        last_feedback=["Fix CSS bug"],
        plan=plan_dict,
        phases=phases_list,
        task="Build landing page"
    )

    # Resume from checkpoint
    checkpoint_data = checkpoint_mgr.load_checkpoint()
    if checkpoint_data:
        # Resume orchestrator from iteration + 1
        start_iteration = checkpoint_data["iteration_index"] + 1
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CheckpointData:
    """
    Orchestrator checkpoint state.

    Contains all necessary data to resume orchestrator execution
    after a crash or interruption.
    """

    # Core state
    run_id: str
    iteration_index: int  # Current iteration (0-indexed internally, but 1-indexed in UI)
    files_written: List[str] = field(default_factory=list)
    cost_accumulated: float = 0.0

    # Manager review state
    last_status: Optional[str] = None  # "approved", "needs_changes", "failed"
    last_feedback: List[str] = field(default_factory=list)
    last_tests: Optional[Dict[str, Any]] = None

    # Plan and phase state
    plan: Optional[Dict[str, Any]] = None
    phases: List[Dict[str, Any]] = field(default_factory=list)
    task: str = ""

    # Stage 3 workflow state (if available)
    current_stage_idx: int = 0
    current_stage_id: Optional[str] = None

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    checkpoint_version: str = "1.0"

    # Retry tracking (for R1 infinite loop prevention)
    consecutive_retry_count: int = 0
    last_retry_feedback_hash: Optional[str] = None


class CheckpointManager:
    """
    Manages checkpoint persistence for orchestrator crash recovery.

    Checkpoints are saved to: run_logs/<run_id>/checkpoint.json
    Uses atomic writes (temp file + rename) to prevent corruption.
    """

    def __init__(self, run_id: str, checkpoint_dir: Optional[Path] = None):
        """
        Initialize checkpoint manager.

        Args:
            run_id: Unique run identifier
            checkpoint_dir: Directory for checkpoints (default: agent/run_logs/<run_id>/)
        """
        self.run_id = run_id

        if checkpoint_dir is None:
            agent_dir = Path(__file__).resolve().parent
            checkpoint_dir = agent_dir / "run_logs" / run_id

        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / "checkpoint.json"

    def save_checkpoint(
        self,
        iteration: int,
        files_written: List[str],
        cost_accumulated: float,
        last_status: Optional[str] = None,
        last_feedback: Optional[List[str]] = None,
        last_tests: Optional[Dict[str, Any]] = None,
        plan: Optional[Dict[str, Any]] = None,
        phases: Optional[List[Dict[str, Any]]] = None,
        task: str = "",
        current_stage_idx: int = 0,
        current_stage_id: Optional[str] = None,
        consecutive_retry_count: int = 0,
        last_retry_feedback_hash: Optional[str] = None,
    ) -> bool:
        """
        Save checkpoint state to disk.

        Uses atomic write (temp file + rename) to prevent corruption.

        Args:
            iteration: Current iteration number (1-indexed)
            files_written: List of files created/modified
            cost_accumulated: Total cost so far in USD
            last_status: Last manager review status
            last_feedback: Last manager feedback
            last_tests: Last test results
            plan: Original manager plan
            phases: Supervisor phases
            task: Original task description
            current_stage_idx: Current workflow stage index
            current_stage_id: Current workflow stage ID
            consecutive_retry_count: Number of consecutive retries (for R1)
            last_retry_feedback_hash: Hash of last retry feedback (for R1)

        Returns:
            True if checkpoint saved successfully, False otherwise
        """
        try:
            checkpoint = CheckpointData(
                run_id=self.run_id,
                iteration_index=iteration,
                files_written=files_written,
                cost_accumulated=cost_accumulated,
                last_status=last_status,
                last_feedback=last_feedback or [],
                last_tests=last_tests,
                plan=plan,
                phases=phases or [],
                task=task,
                current_stage_idx=current_stage_idx,
                current_stage_id=current_stage_id,
                consecutive_retry_count=consecutive_retry_count,
                last_retry_feedback_hash=last_retry_feedback_hash,
            )

            checkpoint_dict = asdict(checkpoint)

            # Atomic write: temp file + rename
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.checkpoint_dir, prefix="checkpoint_", suffix=".tmp"
            )
            try:
                with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                    json.dump(checkpoint_dict, f, indent=2, ensure_ascii=False)

                # Atomic rename
                os.replace(temp_path, self.checkpoint_file)

                print(
                    f"[Checkpoint] Saved checkpoint at iteration {iteration} "
                    f"(cost: ${cost_accumulated:.4f}, files: {len(files_written)})"
                )
                return True

            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e

        except Exception as e:
            print(f"[Checkpoint] Error saving checkpoint: {e}")
            return False

    def load_checkpoint(self) -> Optional[CheckpointData]:
        """
        Load checkpoint from disk.

        Returns:
            CheckpointData if checkpoint exists and is valid, None otherwise
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint_dict = json.load(f)

            # Convert dict back to CheckpointData
            checkpoint = CheckpointData(**checkpoint_dict)

            print(
                f"[Checkpoint] Loaded checkpoint from iteration {checkpoint.iteration_index} "
                f"(cost: ${checkpoint.cost_accumulated:.4f}, files: {len(checkpoint.files_written)})"
            )

            return checkpoint

        except Exception as e:
            print(f"[Checkpoint] Error loading checkpoint: {e}")
            return None

    def checkpoint_exists(self) -> bool:
        """Check if a checkpoint file exists for this run."""
        return self.checkpoint_file.exists()

    def clear_checkpoint(self) -> bool:
        """
        Delete checkpoint file.

        Called when run completes successfully.

        Returns:
            True if deleted, False if file didn't exist or error occurred
        """
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                print(f"[Checkpoint] Cleared checkpoint for run {self.run_id}")
                return True
            return False
        except Exception as e:
            print(f"[Checkpoint] Error clearing checkpoint: {e}")
            return False


def compute_feedback_hash(feedback: List[str]) -> str:
    """
    Compute hash of feedback list for R1 infinite loop detection.

    Args:
        feedback: List of feedback strings

    Returns:
        Hash string (first 16 chars of SHA256)
    """
    import hashlib

    # Sort feedback for consistent hashing
    sorted_feedback = sorted(feedback) if feedback else []
    feedback_str = "|".join(sorted_feedback)
    hash_obj = hashlib.sha256(feedback_str.encode("utf-8"))
    return hash_obj.hexdigest()[:16]
