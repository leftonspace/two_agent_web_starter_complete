"""
PHASE 7.5: Resume Triggers

Detects when evolution should resume for paused domains.

Usage:
    from core.evolution import ResumeChecker, ResumeTrigger

    checker = ResumeChecker()
    trigger = checker.check(pool)

    if trigger:
        resume_evolution(pool.domain, trigger)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.specialists.pool import DomainPool


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Resume Trigger Enum
# ============================================================================


class ResumeTrigger(str, Enum):
    """Reasons to resume evolution after pause."""

    PERFORMANCE_DROP = "performance_drop"  # Best score dropped >5%
    NEW_TASK_TYPES = "new_task_types"  # New patterns detected
    TIME_ELAPSED = "time_elapsed"  # 30 days since pause
    USER_REQUEST = "user_request"  # Manual resume
    COMPARISON_DRIFT = "comparison_drift"  # SC vs AC diverging
    TASK_FAILURE_SPIKE = "task_failure_spike"  # Sudden increase in failures
    DOMAIN_CONFIG_CHANGE = "domain_config_change"  # Config was updated


# ============================================================================
# Resume Check Result
# ============================================================================


class ResumeCheckResult(BaseModel):
    """Result of checking if evolution should resume."""

    should_resume: bool = False
    trigger: Optional[ResumeTrigger] = None
    reason: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "should_resume": self.should_resume,
            "trigger": self.trigger.value if self.trigger else None,
            "reason": self.reason,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
        }


# ============================================================================
# Resume Configuration
# ============================================================================


class ResumeConfig(BaseModel):
    """Configuration for resume checks."""

    # Performance drop threshold
    performance_drop_threshold: float = Field(
        default=0.05,
        gt=0.0,
        le=1.0,
        description="Score drop to trigger resume (5% default)",
    )

    # Time elapsed before auto-resume
    max_pause_days: int = Field(
        default=30,
        ge=1,
        description="Days before auto-resume",
    )

    # Failure spike threshold
    failure_spike_threshold: float = Field(
        default=0.2,
        gt=0.0,
        le=1.0,
        description="Increase in failure rate to trigger resume",
    )

    # Comparison drift threshold
    comparison_drift_threshold: float = Field(
        default=0.15,
        gt=0.0,
        le=1.0,
        description="SC vs AC divergence to trigger resume",
    )

    # Minimum tasks for statistical significance
    min_tasks_for_check: int = Field(
        default=10,
        ge=1,
        description="Minimum tasks before checking triggers",
    )


# ============================================================================
# Resume Checker
# ============================================================================


class ResumeChecker:
    """
    Check if evolution should resume for paused domains.

    Triggers:
    1. Performance drop - best score dropped significantly
    2. New task types - unseen patterns detected
    3. Time elapsed - been paused too long
    4. User request - manual intervention
    5. Comparison drift - SC and AC disagree too much
    6. Task failure spike - sudden increase in failures

    Usage:
        checker = ResumeChecker()

        # Check single pool
        result = checker.check(pool)
        if result.should_resume:
            resume_evolution(pool.domain, result.trigger)

        # Check all pools
        triggers = checker.check_all(pools)
    """

    def __init__(self, config: Optional[ResumeConfig] = None):
        """
        Initialize the checker.

        Args:
            config: Resume configuration
        """
        self._config = config or ResumeConfig()

        # Tracking state
        self._pause_times: Dict[str, datetime] = {}
        self._baseline_scores: Dict[str, float] = {}
        self._baseline_failure_rates: Dict[str, float] = {}
        self._seen_task_types: Dict[str, set] = {}

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> ResumeConfig:
        """Get configuration."""
        return self._config

    # -------------------------------------------------------------------------
    # Main Check
    # -------------------------------------------------------------------------

    def check(self, pool: "DomainPool") -> ResumeCheckResult:
        """
        Check if evolution should resume for a pool.

        Args:
            pool: The paused domain pool

        Returns:
            ResumeCheckResult with trigger if resume needed
        """
        domain = pool.domain

        # Check each trigger in priority order
        checks = [
            self._check_user_request,
            self._check_performance_drop,
            self._check_task_failure_spike,
            self._check_comparison_drift,
            self._check_time_elapsed,
            self._check_new_task_types,
        ]

        for check_fn in checks:
            result = check_fn(pool)
            if result.should_resume:
                logger.info(
                    f"Resume trigger for {domain}: {result.trigger.value} - {result.reason}"
                )
                return result

        return ResumeCheckResult(
            should_resume=False,
            reason="No resume conditions met",
        )

    def check_all(
        self,
        pools: List["DomainPool"],
    ) -> Dict[str, ResumeCheckResult]:
        """
        Check all pools for resume triggers.

        Args:
            pools: List of domain pools to check

        Returns:
            Dict mapping domain to result (only includes those needing resume)
        """
        results = {}

        for pool in pools:
            if not getattr(pool, 'evolution_paused', False):
                continue

            result = self.check(pool)
            if result.should_resume:
                results[pool.domain] = result

        return results

    # -------------------------------------------------------------------------
    # Baseline Management
    # -------------------------------------------------------------------------

    def record_pause(
        self,
        domain: str,
        best_score: float,
        failure_rate: float = 0.0,
    ) -> None:
        """
        Record baseline when evolution is paused.

        Args:
            domain: The domain being paused
            best_score: Current best score
            failure_rate: Current failure rate
        """
        self._pause_times[domain] = datetime.utcnow()
        self._baseline_scores[domain] = best_score
        self._baseline_failure_rates[domain] = failure_rate
        self._seen_task_types[domain] = set()

        logger.info(
            f"Recorded pause baseline for {domain}: "
            f"score={best_score:.3f}, failure_rate={failure_rate:.3f}"
        )

    def record_resume(self, domain: str) -> None:
        """Clear baseline when evolution resumes."""
        self._pause_times.pop(domain, None)
        self._baseline_scores.pop(domain, None)
        self._baseline_failure_rates.pop(domain, None)
        self._seen_task_types.pop(domain, None)

    def record_task_type(self, domain: str, task_type: str) -> None:
        """Record a task type seen for the domain."""
        if domain in self._seen_task_types:
            self._seen_task_types[domain].add(task_type)

    # -------------------------------------------------------------------------
    # Individual Checks
    # -------------------------------------------------------------------------

    def _check_performance_drop(self, pool: "DomainPool") -> ResumeCheckResult:
        """Check if performance has dropped."""
        domain = pool.domain
        baseline = self._baseline_scores.get(domain)

        if baseline is None:
            return ResumeCheckResult(should_resume=False)

        specialists = pool.specialists
        if not specialists:
            return ResumeCheckResult(should_resume=False)

        current_best = max(s.performance.avg_score for s in specialists)
        drop = baseline - current_best

        if drop >= self._config.performance_drop_threshold:
            return ResumeCheckResult(
                should_resume=True,
                trigger=ResumeTrigger.PERFORMANCE_DROP,
                reason=f"Best score dropped {drop:.1%} (from {baseline:.3f} to {current_best:.3f})",
                details={
                    "baseline": baseline,
                    "current": current_best,
                    "drop": drop,
                },
            )

        return ResumeCheckResult(should_resume=False)

    def _check_task_failure_spike(self, pool: "DomainPool") -> ResumeCheckResult:
        """Check if failure rate has spiked."""
        domain = pool.domain
        baseline = self._baseline_failure_rates.get(domain)

        if baseline is None:
            return ResumeCheckResult(should_resume=False)

        # Get current failure rate from specialists
        specialists = pool.specialists
        if not specialists:
            return ResumeCheckResult(should_resume=False)

        # Calculate current failure rate
        total_tasks = sum(s.performance.task_count for s in specialists)
        if total_tasks < self._config.min_tasks_for_check:
            return ResumeCheckResult(should_resume=False)

        # Estimate failures (tasks with score < 0.5)
        failures = sum(
            s.performance.task_count * (1 - s.performance.avg_score)
            for s in specialists
        )
        current_failure_rate = failures / total_tasks if total_tasks > 0 else 0

        spike = current_failure_rate - baseline

        if spike >= self._config.failure_spike_threshold:
            return ResumeCheckResult(
                should_resume=True,
                trigger=ResumeTrigger.TASK_FAILURE_SPIKE,
                reason=f"Failure rate spiked by {spike:.1%}",
                details={
                    "baseline": baseline,
                    "current": current_failure_rate,
                    "spike": spike,
                },
            )

        return ResumeCheckResult(should_resume=False)

    def _check_comparison_drift(self, pool: "DomainPool") -> ResumeCheckResult:
        """Check if SC and AC are diverging too much."""
        domain = pool.domain

        # Get comparison stats (would need integration with comparison tracker)
        # For now, check if metadata indicates drift
        if hasattr(pool, 'comparison_stats'):
            stats = pool.comparison_stats
            if stats and hasattr(stats, 'mean_difference'):
                drift = abs(stats.mean_difference)

                if drift >= self._config.comparison_drift_threshold:
                    return ResumeCheckResult(
                        should_resume=True,
                        trigger=ResumeTrigger.COMPARISON_DRIFT,
                        reason=f"SC vs AC drift: {drift:.3f}",
                        details={
                            "drift": drift,
                            "threshold": self._config.comparison_drift_threshold,
                        },
                    )

        return ResumeCheckResult(should_resume=False)

    def _check_time_elapsed(self, pool: "DomainPool") -> ResumeCheckResult:
        """Check if evolution has been paused too long."""
        domain = pool.domain
        pause_time = self._pause_times.get(domain)

        if pause_time is None:
            return ResumeCheckResult(should_resume=False)

        elapsed = datetime.utcnow() - pause_time
        max_pause = timedelta(days=self._config.max_pause_days)

        if elapsed >= max_pause:
            return ResumeCheckResult(
                should_resume=True,
                trigger=ResumeTrigger.TIME_ELAPSED,
                reason=f"Paused for {elapsed.days} days (max: {self._config.max_pause_days})",
                details={
                    "paused_at": pause_time.isoformat(),
                    "elapsed_days": elapsed.days,
                    "max_days": self._config.max_pause_days,
                },
            )

        return ResumeCheckResult(should_resume=False)

    def _check_new_task_types(self, pool: "DomainPool") -> ResumeCheckResult:
        """Check if new task types have been seen."""
        domain = pool.domain
        seen_types = self._seen_task_types.get(domain, set())

        # Get known task types from pool configuration
        known_types = getattr(pool, 'known_task_types', set())

        if not known_types or not seen_types:
            return ResumeCheckResult(should_resume=False)

        new_types = seen_types - known_types

        if new_types:
            return ResumeCheckResult(
                should_resume=True,
                trigger=ResumeTrigger.NEW_TASK_TYPES,
                reason=f"New task types detected: {', '.join(new_types)}",
                details={
                    "new_types": list(new_types),
                    "known_types": list(known_types),
                },
            )

        return ResumeCheckResult(should_resume=False)

    def _check_user_request(self, pool: "DomainPool") -> ResumeCheckResult:
        """Check if user has requested resume."""
        # Check pool metadata for user resume request
        if hasattr(pool, 'resume_requested') and pool.resume_requested:
            return ResumeCheckResult(
                should_resume=True,
                trigger=ResumeTrigger.USER_REQUEST,
                reason="User requested resume",
                details={},
            )

        return ResumeCheckResult(should_resume=False)

    # -------------------------------------------------------------------------
    # Manual Triggers
    # -------------------------------------------------------------------------

    def trigger_resume(
        self,
        domain: str,
        trigger: ResumeTrigger = ResumeTrigger.USER_REQUEST,
        reason: str = "",
    ) -> ResumeCheckResult:
        """
        Manually trigger a resume.

        Args:
            domain: Domain to resume
            trigger: Trigger type
            reason: Reason for resume

        Returns:
            ResumeCheckResult
        """
        return ResumeCheckResult(
            should_resume=True,
            trigger=trigger,
            reason=reason or f"Manual {trigger.value}",
            details={"manual": True},
        )


# ============================================================================
# Singleton Instance
# ============================================================================


_resume_checker: Optional[ResumeChecker] = None


def get_resume_checker() -> ResumeChecker:
    """Get the global resume checker."""
    global _resume_checker
    if _resume_checker is None:
        _resume_checker = ResumeChecker()
    return _resume_checker


def reset_resume_checker() -> None:
    """Reset the global resume checker (for testing)."""
    global _resume_checker
    _resume_checker = None
