"""
Job manager for background orchestrator runs.

STAGE 8: Background execution, job tracking, and cancellation support.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add agent/ to path for imports
agent_dir = Path(__file__).resolve().parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from runner import run_project
from safe_io import safe_json_write, safe_timestamp
from status_codes import COMPLETED, EXCEPTION, USER_ABORT


# Job statuses
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"


@dataclass
class Job:
    """
    A background orchestrator job.

    Tracks configuration, status, logs, and results for a single run.
    """

    id: str  # UUID
    status: str  # queued, running, completed, failed, cancelled
    config: Dict[str, Any]  # Run configuration
    created_at: str  # ISO timestamp
    updated_at: str  # ISO timestamp
    started_at: Optional[str] = None  # When execution actually started
    finished_at: Optional[str] = None  # When execution completed
    logs_path: Optional[str] = None  # Path to log file
    result_summary: Optional[Dict[str, Any]] = None  # RunSummary as dict
    error: Optional[str] = None  # Error message if failed
    cancelled: bool = False  # Cancellation flag
    # STAGE 10: Quality assurance
    qa_status: Optional[str] = None  # "passed"/"warning"/"failed"/"error"
    qa_summary: Optional[str] = None  # Human-readable QA summary
    qa_report: Optional[Dict[str, Any]] = None  # Complete QA report


class JobManager:
    """
    Manages background orchestrator jobs.

    Handles job lifecycle:
    - Create and queue jobs
    - Execute in background threads
    - Track status and logs
    - Cancel running jobs
    - Persist job state to disk
    """

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize the job manager.

        Args:
            state_file: Path to jobs state JSON file (default: agent/jobs_state.json)
        """
        if state_file is None:
            agent_dir = Path(__file__).resolve().parent
            state_file = agent_dir / "jobs_state.json"

        self.state_file = state_file
        self.lock = threading.Lock()  # Protect jobs dict and state file writes
        self.jobs: Dict[str, Job] = {}  # In-memory job cache
        self.threads: Dict[str, threading.Thread] = {}  # Running job threads

        # Load existing jobs from disk
        self._load_jobs()

    def _load_jobs(self) -> None:
        """Load jobs from state file."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for job_data in data.get("jobs", []):
                    job = Job(**job_data)
                    self.jobs[job.id] = job
        except Exception as e:
            logging.warning(f"[Jobs] Failed to load jobs state: {e}")

    def _save_jobs(self) -> None:
        """Save jobs to state file (atomic write)."""
        data = {"jobs": [asdict(job) for job in self.jobs.values()]}

        # Atomic write: write to temp file, then rename
        temp_file = self.state_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.state_file)
        except Exception as e:
            logging.error(f"[Jobs] Failed to save jobs state: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def create_job(self, config: Dict[str, Any]) -> Job:
        """
        Create a new job with the given configuration.

        Args:
            config: Run configuration (same as run_project config)

        Returns:
            Job object with status=queued
        """
        job_id = uuid.uuid4().hex[:12]  # 12-char ID
        now = safe_timestamp()

        # Create log directory
        agent_dir = Path(__file__).resolve().parent
        project_root = agent_dir.parent
        log_dir = project_root / "run_logs" / job_id
        log_dir.mkdir(parents=True, exist_ok=True)
        logs_path = str(log_dir / "job.log")

        job = Job(
            id=job_id,
            status=STATUS_QUEUED,
            config=config,
            created_at=now,
            updated_at=now,
            logs_path=logs_path,
        )

        with self.lock:
            self.jobs[job_id] = job
            self._save_jobs()

        logging.info(f"[Jobs] Created job {job_id}")
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job object or None if not found
        """
        return self.jobs.get(job_id)

    def list_jobs(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[Job]:
        """
        List all jobs, optionally filtered by status.

        Args:
            limit: Maximum number of jobs to return
            status: Filter by status (queued, running, completed, etc.)

        Returns:
            List of Job objects, sorted by created_at (newest first)
        """
        jobs = list(self.jobs.values())

        # Filter by status
        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created_at (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        # Limit
        if limit:
            jobs = jobs[:limit]

        return jobs

    def update_job(self, job_id: str, **updates) -> Optional[Job]:
        """
        Update a job's fields.

        Args:
            job_id: Job identifier
            **updates: Fields to update (status, logs_path, result_summary, etc.)

        Returns:
            Updated Job object or None if not found
        """
        job = self.jobs.get(job_id)
        if not job:
            return None

        with self.lock:
            # Update fields
            for key, value in updates.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            job.updated_at = safe_timestamp()
            self._save_jobs()

        return job

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running or queued job.

        Sets the cancelled flag. The background thread must check this flag
        and stop execution gracefully.

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False if job not found or already finished
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        # Only cancel if queued or running
        if job.status not in (STATUS_QUEUED, STATUS_RUNNING):
            return False

        with self.lock:
            job.cancelled = True
            job.updated_at = safe_timestamp()
            self._save_jobs()

        logging.info(f"[Jobs] Cancelled job {job_id}")
        return True

    def start_job(self, job_id: str) -> bool:
        """
        Start executing a job in a background thread.

        Args:
            job_id: Job identifier

        Returns:
            True if started, False if job not found or already running
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        # Only start if queued
        if job.status != STATUS_QUEUED:
            return False

        # Create and start background thread
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        self.threads[job_id] = thread
        thread.start()

        logging.info(f"[Jobs] Started job {job_id} in background thread")
        return True

    def _run_job(self, job_id: str) -> None:
        """
        Background thread function to execute a job.

        This wraps run_project() and handles:
        - Status updates
        - Log capture
        - Result storage
        - Cancellation checking
        - Error handling

        Args:
            job_id: Job identifier
        """
        job = self.jobs.get(job_id)
        if not job:
            return

        # Update status to running
        self.update_job(
            job_id,
            status=STATUS_RUNNING,
            started_at=safe_timestamp(),
        )

        # Setup logging to job log file
        log_file = Path(job.logs_path) if job.logs_path else None
        log_handler = None

        if log_file:
            log_handler = logging.FileHandler(log_file, encoding="utf-8")
            log_handler.setLevel(logging.INFO)
            log_handler.setFormatter(
                logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            )
            logging.getLogger().addHandler(log_handler)

        try:
            # Log job start
            logging.info(f"[Jobs] Starting job {job_id}")
            logging.info(f"[Jobs] Config: {json.dumps(job.config, indent=2)}")

            # Check cancellation before starting
            if job.cancelled:
                logging.info("[Jobs] Job was cancelled before execution")
                self.update_job(
                    job_id,
                    status=STATUS_CANCELLED,
                    finished_at=safe_timestamp(),
                )
                return

            # Run the orchestrator
            # Note: run_project() is blocking. For better cancellation,
            # we'd need to modify the orchestrator to check cancellation flags
            # between iterations. For now, this is a coarse-grained check.
            run_summary = run_project(job.config)

            # Check cancellation after run (in case it was cancelled during execution)
            if job.cancelled:
                logging.info("[Jobs] Job was cancelled during execution")
                self.update_job(
                    job_id,
                    status=STATUS_CANCELLED,
                    finished_at=safe_timestamp(),
                    result_summary=asdict(run_summary),
                )
                return

            # Job completed successfully
            logging.info(f"[Jobs] Job {job_id} completed successfully")
            self.update_job(
                job_id,
                status=STATUS_COMPLETED,
                finished_at=safe_timestamp(),
                result_summary=asdict(run_summary),
            )

        except Exception as e:
            # Job failed with exception
            logging.error(f"[Jobs] Job {job_id} failed: {e}", exc_info=True)
            self.update_job(
                job_id,
                status=STATUS_FAILED,
                finished_at=safe_timestamp(),
                error=str(e),
            )

        finally:
            # Cleanup log handler
            if log_handler:
                logging.getLogger().removeHandler(log_handler)
                log_handler.close()

            # Remove from threads dict
            if job_id in self.threads:
                del self.threads[job_id]

    def get_job_logs(self, job_id: str, tail_lines: Optional[int] = None) -> str:
        """
        Get logs for a job.

        Args:
            job_id: Job identifier
            tail_lines: If specified, return only last N lines

        Returns:
            Log content as string, or empty string if no logs
        """
        job = self.jobs.get(job_id)
        if not job or not job.logs_path:
            return ""

        log_file = Path(job.logs_path)
        if not log_file.exists():
            return ""

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                if tail_lines:
                    # Read all lines and return last N
                    lines = f.readlines()
                    return "".join(lines[-tail_lines:])
                else:
                    return f.read()
        except Exception as e:
            logging.error(f"[Jobs] Failed to read logs for {job_id}: {e}")
            return f"Error reading logs: {e}\n"


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """
    Get the global JobManager instance.

    Creates one if it doesn't exist.

    Returns:
        JobManager singleton
    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
