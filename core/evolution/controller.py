"""
PHASE 7.5: Evolution Controller

Orchestrates the full evolution cycle for specialist pools.
Manages culling, spawning, learning extraction, and convergence.

Usage:
    from core.evolution import EvolutionController, get_evolution_controller

    controller = get_evolution_controller()

    # Run evolution for one domain
    result = await controller.run_evolution("code_generation")

    # Run for all domains
    results = await controller.run_all()

    # Check status
    status = controller.get_status("code_generation")
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, Field

from .graveyard import Graveyard, Learning, get_graveyard
from .convergence import (
    ConvergenceDetector,
    ConvergenceResult,
    get_convergence_detector,
)
from .resume_triggers import (
    ResumeChecker,
    ResumeTrigger,
    ResumeCheckResult,
    get_resume_checker,
)

if TYPE_CHECKING:
    from core.specialists.pool import DomainPool
    from core.specialists.pool_manager import PoolManager
    from core.specialists.spawner import Spawner
    from core.specialists import Specialist


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Evolution Status
# ============================================================================


class EvolutionState(str, Enum):
    """Current state of evolution for a domain."""

    ACTIVE = "active"  # Evolution running normally
    PAUSED = "paused"  # Converged, evolution paused
    PENDING_RESUME = "pending_resume"  # Resume trigger detected
    DISABLED = "disabled"  # Manually disabled


class EvolutionStatus(BaseModel):
    """Status of evolution for a domain."""

    domain: str
    state: EvolutionState = EvolutionState.ACTIVE
    generation: int = 1
    last_evolution: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    pause_reason: Optional[str] = None
    resume_trigger: Optional[ResumeTrigger] = None

    # Convergence info
    convergence_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress toward convergence (0-1)",
    )

    # Pool stats
    specialist_count: int = 0
    best_score: float = 0.0
    mean_score: float = 0.0

    # Evolution stats
    total_evolutions: int = 0
    total_culled: int = 0
    total_spawned: int = 0
    total_learnings: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "state": self.state.value,
            "generation": self.generation,
            "last_evolution": self.last_evolution.isoformat() if self.last_evolution else None,
            "convergence_progress": f"{self.convergence_progress * 100:.1f}%",
            "specialist_count": self.specialist_count,
            "best_score": round(self.best_score, 3),
            "mean_score": round(self.mean_score, 3),
            "stats": {
                "evolutions": self.total_evolutions,
                "culled": self.total_culled,
                "spawned": self.total_spawned,
                "learnings": self.total_learnings,
            },
            "paused": {
                "at": self.paused_at.isoformat() if self.paused_at else None,
                "reason": self.pause_reason,
            } if self.state == EvolutionState.PAUSED else None,
        }


# ============================================================================
# Evolution Result
# ============================================================================


class EvolutionResult(BaseModel):
    """Result of running evolution for a domain."""

    domain: str
    success: bool = True

    # Changes
    culled: List[str] = Field(
        default_factory=list,
        description="Names of culled specialists",
    )
    spawned: List[str] = Field(
        default_factory=list,
        description="Names of new specialists",
    )
    learnings_applied: int = Field(
        default=0,
        ge=0,
        description="Number of learnings injected",
    )

    # State
    converged: bool = False
    new_generation: int = 1

    # Metrics
    previous_best_score: float = 0.0
    new_best_score: float = 0.0
    improvement: float = Field(
        default=0.0,
        description="Score improvement this evolution",
    )

    # Errors
    error: Optional[str] = None

    # Timing
    duration_ms: int = 0
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "success": self.success,
            "culled": self.culled,
            "spawned": self.spawned,
            "learnings_applied": self.learnings_applied,
            "converged": self.converged,
            "generation": self.new_generation,
            "scores": {
                "previous_best": round(self.previous_best_score, 3),
                "new_best": round(self.new_best_score, 3),
                "improvement": f"{self.improvement:+.3f}",
            },
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


# ============================================================================
# Evolution Configuration
# ============================================================================


class EvolutionConfig(BaseModel):
    """Configuration for evolution controller."""

    # Quality thresholds per domain
    quality_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "code_generation": 0.65,
            "code_review": 0.60,
            "administration": 0.70,
            "research": 0.55,
            "planning": 0.60,
        }
    )

    # Default threshold
    default_min_score: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
    )

    # Pool constraints
    min_pool_size: int = Field(default=3, ge=1)
    max_cull_per_cycle: int = Field(default=1, ge=1)

    # Learning limits
    max_learnings_per_spawn: int = Field(default=5, ge=1)
    min_learning_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Auto-run settings
    auto_check_resume: bool = Field(default=True)
    evolution_cooldown_minutes: int = Field(default=60, ge=1)


# ============================================================================
# Evolution Controller
# ============================================================================


class EvolutionController:
    """
    Controls evolution for all domain pools.

    Evolution cycle for a domain:
    1. Get all specialists and their scores
    2. Identify underperformers
    3. Send underperformers to graveyard
    4. Extract learnings
    5. Spawn replacements with learnings injected
    6. Check for convergence
    7. If converged, pause evolution

    Usage:
        controller = EvolutionController()

        # Run evolution
        result = await controller.run_evolution("code_generation")

        # Check status
        status = controller.get_status("code_generation")

        # Pause/resume
        controller.pause_evolution("code_generation", "Manual pause")
        controller.resume_evolution("code_generation")
    """

    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        pool_manager: Optional["PoolManager"] = None,
        spawner: Optional["Spawner"] = None,
        graveyard: Optional[Graveyard] = None,
        convergence_detector: Optional[ConvergenceDetector] = None,
        resume_checker: Optional[ResumeChecker] = None,
    ):
        """
        Initialize the controller.

        Args:
            config: Evolution configuration
            pool_manager: Pool manager instance
            spawner: Specialist spawner
            graveyard: Graveyard for culled specialists
            convergence_detector: Convergence detector
            resume_checker: Resume checker
        """
        self._config = config or EvolutionConfig()

        # Dependencies (lazy loaded)
        self._pool_manager = pool_manager
        self._spawner = spawner
        self._graveyard = graveyard or get_graveyard()
        self._convergence_detector = convergence_detector or get_convergence_detector()
        self._resume_checker = resume_checker or get_resume_checker()

        # Status tracking
        self._status: Dict[str, EvolutionStatus] = {}
        self._last_evolution: Dict[str, datetime] = {}

        # Statistics
        self._total_evolutions = 0
        self._initialized_at = datetime.utcnow()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> EvolutionConfig:
        """Get configuration."""
        return self._config

    @property
    def pool_manager(self) -> "PoolManager":
        """Get pool manager (lazy load)."""
        if self._pool_manager is None:
            from core.specialists.pool_manager import get_pool_manager
            self._pool_manager = get_pool_manager()
        return self._pool_manager

    @property
    def spawner(self) -> "Spawner":
        """Get spawner (lazy load)."""
        if self._spawner is None:
            from core.specialists.spawner import get_spawner
            self._spawner = get_spawner()
        return self._spawner

    @property
    def graveyard(self) -> Graveyard:
        """Get graveyard."""
        return self._graveyard

    # -------------------------------------------------------------------------
    # Main Evolution
    # -------------------------------------------------------------------------

    async def run_evolution(self, domain: str) -> EvolutionResult:
        """
        Run one evolution cycle for a domain.

        Args:
            domain: Domain to evolve

        Returns:
            EvolutionResult with changes made
        """
        start_time = datetime.utcnow()

        try:
            # Get pool
            pool = self.pool_manager.get_pool(domain)

            if pool is None:
                return EvolutionResult(
                    domain=domain,
                    success=False,
                    error=f"Pool not found for domain: {domain}",
                )

            # Check if paused
            status = self._get_or_create_status(domain, pool)

            if status.state == EvolutionState.PAUSED:
                logger.info(f"Evolution paused for {domain}, skipping")
                return EvolutionResult(
                    domain=domain,
                    success=True,
                    converged=True,
                    new_generation=pool.generation,
                )

            if status.state == EvolutionState.DISABLED:
                return EvolutionResult(
                    domain=domain,
                    success=False,
                    error="Evolution disabled for this domain",
                )

            # Get specialists sorted by score (worst first)
            specialists = sorted(
                pool.specialists,
                key=lambda s: s.performance.avg_score,
            )

            if not specialists:
                return EvolutionResult(
                    domain=domain,
                    success=False,
                    error="No specialists in pool",
                )

            previous_best = max(s.performance.avg_score for s in specialists)

            # Identify underperformers
            min_threshold = self._config.quality_thresholds.get(
                domain,
                self._config.default_min_score,
            )

            underperformers = [
                s for s in specialists
                if s.performance.avg_score < min_threshold
            ]

            # If none below threshold but pool is full, cull worst
            if not underperformers and len(specialists) >= self._config.min_pool_size:
                underperformers = [specialists[0]]  # Worst performer

            # Limit culling
            underperformers = underperformers[:self._config.max_cull_per_cycle]

            # Send to graveyard
            culled_names = []
            all_learnings: List[Learning] = []

            for specialist in underperformers:
                reason = f"Score {specialist.performance.avg_score:.2f} below threshold {min_threshold}"
                entry = await self._graveyard.send_to_graveyard(specialist, reason)
                culled_names.append(specialist.name)
                all_learnings.extend(entry.learnings)
                pool.remove(specialist.id)

            # Spawn replacements
            spawned_names = []
            domain_learnings = self._graveyard.get_learnings(
                domain,
                min_confidence=self._config.min_learning_confidence,
                limit=self._config.max_learnings_per_spawn,
            )

            for _ in underperformers:
                if hasattr(self.spawner, 'spawn_with_learnings'):
                    new_specialist = self.spawner.spawn_with_learnings(
                        domain,
                        domain_learnings,
                    )
                else:
                    new_specialist = self.spawner.spawn_initial(domain)

                pool.add(new_specialist)
                spawned_names.append(new_specialist.name)

            # Increment generation
            pool.generation += 1

            # Record for convergence tracking
            new_best = max(
                s.performance.avg_score for s in pool.specialists
            ) if pool.specialists else 0.0

            self._convergence_detector.record_generation(domain, new_best)

            # Check convergence
            convergence = self._convergence_detector.check(pool)

            if convergence.has_converged:
                self.pause_evolution(domain, "Convergence detected")

            # Update status
            self._update_status(domain, pool, convergence)

            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Update counters
            status.total_evolutions += 1
            status.total_culled += len(culled_names)
            status.total_spawned += len(spawned_names)
            status.total_learnings += len(domain_learnings)
            status.last_evolution = datetime.utcnow()

            self._total_evolutions += 1
            self._last_evolution[domain] = datetime.utcnow()

            logger.info(
                f"Evolution complete for {domain}: "
                f"culled={len(culled_names)}, spawned={len(spawned_names)}, "
                f"gen={pool.generation}, converged={convergence.has_converged}"
            )

            return EvolutionResult(
                domain=domain,
                success=True,
                culled=culled_names,
                spawned=spawned_names,
                learnings_applied=len(domain_learnings),
                converged=convergence.has_converged,
                new_generation=pool.generation,
                previous_best_score=previous_best,
                new_best_score=new_best,
                improvement=new_best - previous_best,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Evolution failed for {domain}: {e}")
            return EvolutionResult(
                domain=domain,
                success=False,
                error=str(e),
            )

    async def run_all(self) -> List[EvolutionResult]:
        """
        Run evolution for all domains.

        Returns:
            List of results for each domain
        """
        results = []

        for domain in self.pool_manager.domains:
            # Check resume triggers first
            if self._config.auto_check_resume:
                pool = self.pool_manager.get_pool(domain)
                if pool and getattr(pool, 'evolution_paused', False):
                    resume_result = self._resume_checker.check(pool)
                    if resume_result.should_resume:
                        self.resume_evolution(domain, str(resume_result.trigger))

            result = await self.run_evolution(domain)
            results.append(result)

        return results

    # -------------------------------------------------------------------------
    # Pause/Resume
    # -------------------------------------------------------------------------

    def pause_evolution(self, domain: str, reason: str = "") -> None:
        """
        Pause evolution for a domain.

        Args:
            domain: Domain to pause
            reason: Reason for pausing
        """
        pool = self.pool_manager.get_pool(domain)
        if pool:
            pool.evolution_paused = True

        status = self._get_or_create_status(domain, pool)
        status.state = EvolutionState.PAUSED
        status.paused_at = datetime.utcnow()
        status.pause_reason = reason

        # Record baseline for resume checking
        if pool and pool.specialists:
            best_score = max(s.performance.avg_score for s in pool.specialists)
            self._resume_checker.record_pause(domain, best_score)

        logger.info(f"Paused evolution for {domain}: {reason}")

    def resume_evolution(self, domain: str, trigger: str = "") -> None:
        """
        Resume evolution for a domain.

        Args:
            domain: Domain to resume
            trigger: What triggered the resume
        """
        pool = self.pool_manager.get_pool(domain)
        if pool:
            pool.evolution_paused = False

        status = self._get_or_create_status(domain, pool)
        status.state = EvolutionState.ACTIVE
        status.paused_at = None
        status.pause_reason = None
        status.resume_trigger = ResumeTrigger(trigger) if trigger else None

        # Clear resume baseline
        self._resume_checker.record_resume(domain)

        # Clear convergence history to start fresh
        self._convergence_detector.clear_history(domain)

        logger.info(f"Resumed evolution for {domain}: {trigger}")

    def disable_evolution(self, domain: str) -> None:
        """Disable evolution for a domain (manual override)."""
        status = self._get_or_create_status(domain, None)
        status.state = EvolutionState.DISABLED
        logger.info(f"Disabled evolution for {domain}")

    def enable_evolution(self, domain: str) -> None:
        """Enable evolution for a domain."""
        status = self._get_or_create_status(domain, None)
        if status.state == EvolutionState.DISABLED:
            status.state = EvolutionState.ACTIVE
        logger.info(f"Enabled evolution for {domain}")

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    def get_status(self, domain: str) -> EvolutionStatus:
        """Get evolution status for a domain."""
        pool = self.pool_manager.get_pool(domain)
        return self._get_or_create_status(domain, pool)

    def get_all_status(self) -> Dict[str, EvolutionStatus]:
        """Get status for all domains."""
        return {
            domain: self.get_status(domain)
            for domain in self.pool_manager.domains
        }

    def check_convergence(self, domain: str) -> ConvergenceResult:
        """Check convergence for a domain."""
        pool = self.pool_manager.get_pool(domain)
        if not pool:
            return ConvergenceResult(
                has_converged=False,
                reasons=["Pool not found"],
            )
        return self._convergence_detector.check(pool)

    def check_resume(self, domain: str) -> ResumeCheckResult:
        """Check if evolution should resume for a domain."""
        pool = self.pool_manager.get_pool(domain)
        if not pool:
            return ResumeCheckResult(
                should_resume=False,
                reason="Pool not found",
            )
        return self._resume_checker.check(pool)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _get_or_create_status(
        self,
        domain: str,
        pool: Optional["DomainPool"],
    ) -> EvolutionStatus:
        """Get or create status for a domain."""
        if domain not in self._status:
            self._status[domain] = EvolutionStatus(domain=domain)

        status = self._status[domain]

        # Update from pool if available
        if pool:
            status.generation = pool.generation
            status.specialist_count = len(pool.specialists)

            if pool.specialists:
                scores = [s.performance.avg_score for s in pool.specialists]
                status.best_score = max(scores)
                status.mean_score = sum(scores) / len(scores)

            # Update convergence progress
            progress = self._convergence_detector.get_progress(pool)
            status.convergence_progress = progress.overall_progress

        return status

    def _update_status(
        self,
        domain: str,
        pool: "DomainPool",
        convergence: ConvergenceResult,
    ) -> None:
        """Update status after evolution."""
        status = self._get_or_create_status(domain, pool)
        status.generation = pool.generation

        if pool.specialists:
            scores = [s.performance.avg_score for s in pool.specialists]
            status.best_score = max(scores)
            status.mean_score = sum(scores) / len(scores)

        # Update convergence progress
        progress = self._convergence_detector.get_progress(pool)
        status.convergence_progress = progress.overall_progress

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get controller statistics."""
        return {
            "total_evolutions": self._total_evolutions,
            "domains": {
                domain: status.to_dict()
                for domain, status in self._status.items()
            },
            "graveyard": self._graveyard.get_stats(),
            "initialized_at": self._initialized_at.isoformat(),
        }


# ============================================================================
# Singleton Instance
# ============================================================================


_evolution_controller: Optional[EvolutionController] = None


def get_evolution_controller() -> EvolutionController:
    """Get the global evolution controller."""
    global _evolution_controller
    if _evolution_controller is None:
        _evolution_controller = EvolutionController()
    return _evolution_controller


def reset_evolution_controller() -> None:
    """Reset the global evolution controller (for testing)."""
    global _evolution_controller
    _evolution_controller = None
