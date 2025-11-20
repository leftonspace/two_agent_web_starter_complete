"""
PHASE 4.3: Infinite Loop Prevention (R1)

Detects consecutive identical retry feedback to prevent infinite loops
where Manager always returns "retry" with same feedback.

Circuit Breaker Logic:
- Track last N retry feedback messages
- If Manager returns "retry" with identical feedback 2+ times consecutively,
  force escalation to Overseer or abort with detailed error

Integration with Checkpoint System:
- Retry count and feedback hash stored in checkpoint
- Persists across orchestrator restarts

Usage:
    detector = RetryLoopDetector(max_consecutive_retries=2)

    # Check if we should continue iteration
    should_abort, reason = detector.check_retry_loop(
        status="needs_changes",
        feedback=["Fix the CSS bug in styles.css"],
        iteration=3
    )

    if should_abort:
        print(f"Aborting: {reason}")
        # Escalate to Overseer or abort run
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class RetryHistory:
    """
    History of retry attempts.

    Tracks consecutive retries with same feedback to detect infinite loops.
    """

    consecutive_retry_count: int = 0
    last_retry_feedback_hash: Optional[str] = None
    retry_history: List[str] = field(default_factory=list)  # Hash history


class RetryLoopDetector:
    """
    Detects infinite retry loops in Manager review cycles.

    PHASE 4.3 (R1): Prevents orchestrator from getting stuck in infinite loop
    when Manager repeatedly requests same changes without progress.
    """

    def __init__(self, max_consecutive_retries: int = 2):
        """
        Initialize retry loop detector.

        Args:
            max_consecutive_retries: Max number of consecutive retries with
                identical feedback before forcing escalation (default: 2)
        """
        self.max_consecutive_retries = max_consecutive_retries
        self.history = RetryHistory()

    def check_retry_loop(
        self,
        status: str,
        feedback: List[str],
        iteration: int,
        max_rounds: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if we're in an infinite retry loop.

        Args:
            status: Manager status ("approved", "needs_changes", "failed")
            feedback: Manager feedback messages
            iteration: Current iteration number
            max_rounds: Maximum allowed rounds (optional, for additional checks)

        Returns:
            Tuple of (should_abort, reason)
            - should_abort: True if loop detected and should abort
            - reason: Human-readable explanation of why we're aborting
        """
        # Only track retries for needs_changes status
        if status != "needs_changes":
            # Reset on success or different status
            if status == "approved":
                self._reset()
            return (False, None)

        # Compute feedback hash
        current_hash = self._compute_feedback_hash(feedback)

        # Check if this is identical to last retry
        if current_hash == self.history.last_retry_feedback_hash:
            self.history.consecutive_retry_count += 1
            self.history.retry_history.append(current_hash)

            print(
                f"[RetryLoop] Consecutive retry #{self.history.consecutive_retry_count} "
                f"with identical feedback (hash: {current_hash[:8]}...)"
            )

            # Check if we've exceeded threshold
            if self.history.consecutive_retry_count >= self.max_consecutive_retries:
                reason = (
                    f"Infinite retry loop detected: Manager requested identical changes "
                    f"{self.history.consecutive_retry_count} times consecutively. "
                    f"Feedback: {self._format_feedback(feedback)}. "
                    f"This indicates ambiguous requirements or a stuck workflow. "
                    f"Aborting to prevent infinite loop."
                )
                return (True, reason)

        else:
            # Different feedback - reset counter but track new feedback
            if self.history.consecutive_retry_count > 0:
                print(
                    f"[RetryLoop] Feedback changed from previous retry - resetting counter "
                    f"(was {self.history.consecutive_retry_count})"
                )

            self.history.consecutive_retry_count = 1
            self.history.last_retry_feedback_hash = current_hash
            self.history.retry_history.append(current_hash)

        # Additional check: If we're at max_rounds with retry, that's also problematic
        if max_rounds and iteration >= max_rounds:
            if status == "needs_changes":
                reason = (
                    f"Reached maximum rounds ({max_rounds}) with Manager still requesting changes. "
                    f"Latest feedback: {self._format_feedback(feedback)}. "
                    f"This run has exhausted all retry attempts."
                )
                return (True, reason)

        return (False, None)

    def _compute_feedback_hash(self, feedback: List[str]) -> str:
        """
        Compute hash of feedback list for comparison.

        Args:
            feedback: List of feedback strings

        Returns:
            SHA256 hash (first 16 chars)
        """
        # Sort for consistent hashing (order shouldn't matter)
        sorted_feedback = sorted(feedback) if feedback else []
        feedback_str = "|".join(sorted_feedback)
        hash_obj = hashlib.sha256(feedback_str.encode("utf-8"))
        return hash_obj.hexdigest()[:16]

    def _format_feedback(self, feedback: List[str], max_items: int = 3) -> str:
        """
        Format feedback list for display.

        Args:
            feedback: List of feedback strings
            max_items: Maximum number of items to show

        Returns:
            Formatted string
        """
        if not feedback:
            return "(no feedback provided)"

        if len(feedback) <= max_items:
            return "; ".join(feedback)

        shown = feedback[:max_items]
        remaining = len(feedback) - max_items
        return "; ".join(shown) + f" (and {remaining} more)"

    def _reset(self) -> None:
        """Reset retry tracking (called on successful approval)."""
        if self.history.consecutive_retry_count > 0:
            print(f"[RetryLoop] Resetting tracker (was at {self.history.consecutive_retry_count} retries)")
        self.history = RetryHistory()

    def get_state(self) -> dict:
        """
        Get current detector state for checkpoint persistence.

        Returns:
            Dict with consecutive_retry_count and last_retry_feedback_hash
        """
        return {
            "consecutive_retry_count": self.history.consecutive_retry_count,
            "last_retry_feedback_hash": self.history.last_retry_feedback_hash,
        }

    def restore_state(self, state: dict) -> None:
        """
        Restore detector state from checkpoint.

        Args:
            state: State dict from get_state()
        """
        self.history.consecutive_retry_count = state.get("consecutive_retry_count", 0)
        self.history.last_retry_feedback_hash = state.get("last_retry_feedback_hash")

        if self.history.consecutive_retry_count > 0:
            print(
                f"[RetryLoop] Restored state: {self.history.consecutive_retry_count} "
                f"consecutive retries (hash: {self.history.last_retry_feedback_hash or 'none'})"
            )


def check_for_retry_loop(
    status: str,
    feedback: List[str],
    iteration: int,
    last_retry_count: int = 0,
    last_retry_hash: Optional[str] = None,
    max_consecutive_retries: int = 2,
) -> Tuple[bool, Optional[str], int, Optional[str]]:
    """
    Convenience function for one-off retry loop checks.

    Useful for orchestrator integration without maintaining detector instance.

    Args:
        status: Manager status
        feedback: Manager feedback
        iteration: Current iteration
        last_retry_count: Previous consecutive retry count (from checkpoint)
        last_retry_hash: Previous feedback hash (from checkpoint)
        max_consecutive_retries: Max allowed consecutive retries

    Returns:
        Tuple of (should_abort, reason, new_retry_count, new_hash)
    """
    detector = RetryLoopDetector(max_consecutive_retries)

    # Restore state if provided
    if last_retry_count > 0 or last_retry_hash:
        detector.restore_state({
            "consecutive_retry_count": last_retry_count,
            "last_retry_feedback_hash": last_retry_hash,
        })

    # Check for loop
    should_abort, reason = detector.check_retry_loop(status, feedback, iteration)

    # Get updated state
    state = detector.get_state()

    return (
        should_abort,
        reason,
        state["consecutive_retry_count"],
        state["last_retry_feedback_hash"],
    )
