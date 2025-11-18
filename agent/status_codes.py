# status_codes.py
"""
Normalized status codes for the multi-agent system.

All modules must use these constants instead of raw strings to ensure
consistency across run summaries, session summaries, and status reporting.
"""

from __future__ import annotations

# ══════════════════════════════════════════════════════════════════════
# Run-Level Status Codes
# ══════════════════════════════════════════════════════════════════════

# Success states
SUCCESS = "success"
COMPLETED = "completed"
APPROVED = "approved"

# Limit-based termination
MAX_ROUNDS_REACHED = "max_rounds_reached"
COST_CAP_EXCEEDED = "cost_cap_exceeded"

# Failure states
TIMEOUT = "timeout"
SAFETY_FAILED = "safety_failed"
EXCEPTION = "exception"

# User actions
USER_ABORT = "aborted_by_user"

# Unknown/default
UNKNOWN = "unknown"

# Intermediate states
NEEDS_CHANGES = "needs_changes"
IN_PROGRESS = "in_progress"

# ══════════════════════════════════════════════════════════════════════
# Session-Level Status Codes (Auto-Pilot)
# ══════════════════════════════════════════════════════════════════════

SESSION_SUCCESS = "success"
SESSION_MAX_RUNS_REACHED = "max_runs_reached"
SESSION_STOPPED_BY_EVAL = "stopped_by_evaluation"
SESSION_USER_ABORT = "aborted_by_user"
SESSION_UNKNOWN = "unknown"
SESSION_UNKNOWN_RECOMMENDATION = "unknown_recommendation"

# ══════════════════════════════════════════════════════════════════════
# Safety Status Codes
# ══════════════════════════════════════════════════════════════════════

SAFETY_PASSED = "passed"
SAFETY_FAILED_STATUS = "failed"
SAFETY_NONE = None  # No safety check performed

# ══════════════════════════════════════════════════════════════════════
# Iteration/Action Status Codes
# ══════════════════════════════════════════════════════════════════════

ITER_OK = "ok"
ITER_TIMEOUT = "timeout"
ITER_SAFETY_FAILED = "safety_failed"
ITER_INTERRUPTED = "interrupted"
ITER_EXCEPTION = "exception"

# ══════════════════════════════════════════════════════════════════════
# Self-Evaluation Recommendation Codes
# ══════════════════════════════════════════════════════════════════════

EVAL_CONTINUE = "continue"
EVAL_RETRY = "retry"
EVAL_STOP = "stop"

# ══════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════


def is_terminal_status(status: str) -> bool:
    """
    Check if a run status is terminal (no further processing needed).

    Args:
        status: Run status code

    Returns:
        True if status indicates run is finished
    """
    terminal_states = {
        SUCCESS,
        COMPLETED,
        APPROVED,
        MAX_ROUNDS_REACHED,
        COST_CAP_EXCEEDED,
        TIMEOUT,
        SAFETY_FAILED,
        EXCEPTION,
        USER_ABORT,
    }
    return status in terminal_states


def is_success_status(status: str) -> bool:
    """
    Check if a run status indicates successful completion.

    Args:
        status: Run status code

    Returns:
        True if status indicates success
    """
    success_states = {SUCCESS, COMPLETED, APPROVED}
    return status in success_states


def is_failure_status(status: str) -> bool:
    """
    Check if a run status indicates failure.

    Args:
        status: Run status code

    Returns:
        True if status indicates failure
    """
    failure_states = {
        TIMEOUT,
        SAFETY_FAILED,
        EXCEPTION,
        COST_CAP_EXCEEDED,
    }
    return status in failure_states
