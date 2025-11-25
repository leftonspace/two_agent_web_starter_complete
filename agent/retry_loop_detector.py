"""
PHASE 4.3: Infinite Loop Prevention (R1)
PHASE 2.2 HARDENING: Hallucination Spiral Detection

Detects consecutive identical retry feedback to prevent infinite loops
where Manager always returns "retry" with same feedback.

Circuit Breaker Logic:
- Track last N retry feedback messages
- If Manager returns "retry" with identical feedback 2+ times consecutively,
  force escalation to Overseer or abort with detailed error

Hallucination Spiral Detection (Phase 2.2):
- Detects patterns like "I apologize...", "Let me try again...", etc.
- Triggers when agent produces apologetic/retry messages 4+ times sequentially
- Indicates LLM is stuck and unable to make progress

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

    # Check for hallucination spiral
    spiral_detector = HallucinationSpiralDetector()
    is_spiral, reason = spiral_detector.check_response("I apologize, let me try again...")
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from agent.core_logging import log_event


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


# ============================================================================
# PHASE 2.2: Hallucination Spiral Detection
# ============================================================================

# Patterns that indicate the LLM is in a hallucination spiral
HALLUCINATION_PATTERNS: List[str] = [
    # Apology patterns
    r"(?i)i\s+apologize",
    r"(?i)i'm\s+sorry",
    r"(?i)my\s+apologies",
    r"(?i)sorry\s+for\s+the\s+confusion",
    r"(?i)sorry\s+about\s+that",

    # Retry patterns
    r"(?i)let\s+me\s+try\s+again",
    r"(?i)i'll\s+try\s+again",
    r"(?i)let\s+me\s+attempt",
    r"(?i)i'll\s+attempt\s+again",
    r"(?i)let\s+me\s+redo",
    r"(?i)i'll\s+redo",

    # Confusion/stuck patterns
    r"(?i)i\s+seem\s+to\s+be\s+having\s+trouble",
    r"(?i)i'm\s+having\s+difficulty",
    r"(?i)i'm\s+unable\s+to",
    r"(?i)i\s+cannot\s+seem\s+to",
    r"(?i)this\s+is\s+proving\s+difficult",

    # Acknowledgment of failure patterns
    r"(?i)that\s+didn't\s+work",
    r"(?i)that\s+approach\s+failed",
    r"(?i)my\s+previous\s+attempt",
    r"(?i)the\s+previous\s+solution",

    # Repetitive uncertainty
    r"(?i)i'm\s+not\s+sure\s+(?:why|what|how)",
    r"(?i)i\s+don't\s+understand\s+why",
]


@dataclass
class SpiralHistory:
    """History of potential hallucination spiral messages."""
    consecutive_spiral_count: int = 0
    recent_messages: List[str] = field(default_factory=list)
    pattern_matches: List[str] = field(default_factory=list)


class HallucinationSpiralDetector:
    """
    Detects when an LLM is in a hallucination spiral.

    PHASE 2.2: A hallucination spiral occurs when the LLM repeatedly produces
    apologetic or retry messages without making actual progress. This is a sign
    that the LLM is stuck and the task should be aborted or escalated.

    Patterns detected:
    - "I apologize...", "I'm sorry...", "My apologies..."
    - "Let me try again...", "I'll attempt again..."
    - "I seem to be having trouble...", "I'm unable to..."
    - "That didn't work...", "My previous attempt..."

    Trigger: 4+ consecutive messages matching these patterns.
    """

    def __init__(
        self,
        max_consecutive_spirals: int = 4,
        custom_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize hallucination spiral detector.

        Args:
            max_consecutive_spirals: Max consecutive spiral messages before abort (default: 4)
            custom_patterns: Additional regex patterns to detect
        """
        self.max_consecutive_spirals = max_consecutive_spirals
        self.history = SpiralHistory()

        # Compile patterns for efficiency
        self._patterns = HALLUCINATION_PATTERNS.copy()
        if custom_patterns:
            self._patterns.extend(custom_patterns)

        self._compiled_patterns = [re.compile(p) for p in self._patterns]

    def check_response(self, response: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a response indicates a hallucination spiral.

        Args:
            response: The LLM response text to check

        Returns:
            Tuple of (is_spiral, reason)
            - is_spiral: True if spiral detected and should abort
            - reason: Human-readable explanation if spiral detected
        """
        if not response:
            return (False, None)

        # Check first 500 chars (spiral indicators are usually at the start)
        check_text = response[:500]

        # Find matching patterns
        matches = []
        for pattern in self._compiled_patterns:
            if pattern.search(check_text):
                matches.append(pattern.pattern)

        if matches:
            # This response matches spiral patterns
            self.history.consecutive_spiral_count += 1
            self.history.recent_messages.append(check_text[:100])
            self.history.pattern_matches.extend(matches)

            log_event("hallucination_spiral_match", {
                "consecutive_count": self.history.consecutive_spiral_count,
                "patterns_matched": matches[:3],  # Limit logged patterns
                "response_preview": check_text[:100],
            })

            print(
                f"[SpiralDetector] Spiral pattern detected "
                f"(count: {self.history.consecutive_spiral_count}/{self.max_consecutive_spirals})"
            )

            # Check if we've hit the threshold
            if self.history.consecutive_spiral_count >= self.max_consecutive_spirals:
                reason = (
                    f"Hallucination spiral detected: LLM produced {self.history.consecutive_spiral_count} "
                    f"consecutive apologetic/retry messages. "
                    f"Patterns: {', '.join(set(self.history.pattern_matches[-5:]))}. "
                    f"This indicates the LLM is stuck and unable to make progress. "
                    f"Aborting to prevent infinite loop and wasted tokens."
                )

                log_event("hallucination_spiral_abort", {
                    "consecutive_count": self.history.consecutive_spiral_count,
                    "unique_patterns": list(set(self.history.pattern_matches)),
                    "recent_messages": self.history.recent_messages[-3:],
                })

                return (True, reason)

        else:
            # Response doesn't match patterns - reset counter
            if self.history.consecutive_spiral_count > 0:
                print(
                    f"[SpiralDetector] Non-spiral response - resetting counter "
                    f"(was {self.history.consecutive_spiral_count})"
                )
            self._reset()

        return (False, None)

    def _reset(self) -> None:
        """Reset spiral tracking."""
        self.history = SpiralHistory()

    def get_state(self) -> dict:
        """Get current detector state for persistence."""
        return {
            "consecutive_spiral_count": self.history.consecutive_spiral_count,
            "pattern_matches": self.history.pattern_matches[-10:],  # Keep last 10
        }

    def restore_state(self, state: dict) -> None:
        """Restore detector state from checkpoint."""
        self.history.consecutive_spiral_count = state.get("consecutive_spiral_count", 0)
        self.history.pattern_matches = state.get("pattern_matches", [])

        if self.history.consecutive_spiral_count > 0:
            print(
                f"[SpiralDetector] Restored state: {self.history.consecutive_spiral_count} "
                f"consecutive spiral messages"
            )

    def get_statistics(self) -> dict:
        """Get detector statistics."""
        return {
            "consecutive_count": self.history.consecutive_spiral_count,
            "threshold": self.max_consecutive_spirals,
            "total_patterns_matched": len(self.history.pattern_matches),
            "unique_patterns": list(set(self.history.pattern_matches)),
        }


class CombinedLoopDetector:
    """
    Combined detector for both retry loops and hallucination spirals.

    Convenience class that wraps both detectors for easy integration.
    """

    def __init__(
        self,
        max_consecutive_retries: int = 2,
        max_consecutive_spirals: int = 4,
    ):
        """
        Initialize combined detector.

        Args:
            max_consecutive_retries: Max retries with identical feedback
            max_consecutive_spirals: Max spiral messages before abort
        """
        self.retry_detector = RetryLoopDetector(max_consecutive_retries)
        self.spiral_detector = HallucinationSpiralDetector(max_consecutive_spirals)

    def check_all(
        self,
        status: str,
        feedback: List[str],
        response: str,
        iteration: int,
        max_rounds: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for both retry loops and hallucination spirals.

        Args:
            status: Manager status
            feedback: Manager feedback
            response: LLM response text
            iteration: Current iteration
            max_rounds: Maximum allowed rounds

        Returns:
            Tuple of (should_abort, reason)
        """
        # Check retry loop first
        should_abort, reason = self.retry_detector.check_retry_loop(
            status, feedback, iteration, max_rounds
        )
        if should_abort:
            return (True, reason)

        # Check hallucination spiral
        should_abort, reason = self.spiral_detector.check_response(response)
        if should_abort:
            return (True, reason)

        return (False, None)

    def get_state(self) -> dict:
        """Get combined state for persistence."""
        return {
            "retry": self.retry_detector.get_state(),
            "spiral": self.spiral_detector.get_state(),
        }

    def restore_state(self, state: dict) -> None:
        """Restore combined state from checkpoint."""
        if "retry" in state:
            self.retry_detector.restore_state(state["retry"])
        if "spiral" in state:
            self.spiral_detector.restore_state(state["spiral"])
