"""
Dashboard API Routes

Provides system overview, domain status, and specialist details.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Response Models
# ============================================================================


class SpecialistSummary(BaseModel):
    """Summary of a specialist for listing."""

    id: UUID
    name: str
    generation: int
    score: float
    task_count: int
    is_active: bool


class DomainStatus(BaseModel):
    """Status of a single domain."""

    name: str = Field(..., description="Domain name")
    specialists: int = Field(..., description="Number of specialists")
    best_score: float = Field(..., description="Best specialist score")
    avg_score: float = Field(..., description="Average score")
    evolution_paused: bool = Field(..., description="Whether evolution is paused")
    convergence_progress: float = Field(
        default=0.0,
        description="Progress toward convergence (0-100%)",
    )
    tasks_today: int = Field(..., description="Tasks completed today")
    current_jarvis: Optional[str] = Field(
        default=None,
        description="Current JARVIS specialist (administration only)",
    )


class BudgetStatus(BaseModel):
    """Current budget status."""

    production_spent_today: float = Field(..., description="Production spend today (CAD)")
    production_remaining: float = Field(..., description="Production budget remaining")
    production_limit: float = Field(..., description="Daily production limit")
    benchmark_spent_today: float = Field(..., description="Benchmark spend today (CAD)")
    benchmark_remaining: float = Field(..., description="Benchmark budget remaining")
    benchmark_limit: float = Field(..., description="Daily benchmark limit")
    is_warning: bool = Field(..., description="Whether budget warning triggered")
    warning_threshold: float = Field(default=0.8, description="Warning threshold (0-1)")


class EvaluationStatus(BaseModel):
    """Current evaluation configuration."""

    mode: str = Field(..., description="Current mode: scoring_committee, ai_council, or both")
    scoring_committee_enabled: bool = Field(default=True)
    ai_council_enabled: bool = Field(default=False)
    comparison_tracking: bool = Field(default=False)


class DashboardOverview(BaseModel):
    """Complete dashboard overview."""

    domains: List[DomainStatus] = Field(..., description="Status of all domains")
    budget: BudgetStatus = Field(..., description="Budget status")
    evaluation: EvaluationStatus = Field(..., description="Evaluation configuration")
    total_tasks_today: int = Field(..., description="Total tasks completed today")
    total_specialists: int = Field(..., description="Total specialists across domains")
    system_health: str = Field(default="healthy", description="Overall system health")
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of this data",
    )


class SpecialistDetail(BaseModel):
    """Detailed information about a specialist."""

    id: UUID
    name: str
    domain: str
    generation: int
    created_at: datetime
    is_active: bool

    # Performance
    total_tasks: int
    successful_tasks: int
    success_rate: float
    avg_score: float
    recent_scores: List[float]

    # Configuration
    system_prompt_preview: str
    model_preference: Optional[str]
    temperature: float

    # Evolution info
    parent_id: Optional[UUID]
    mutation_summary: Optional[str]
    learnings_applied: int


class DomainDetail(BaseModel):
    """Detailed information about a domain."""

    name: str
    description: str

    # Specialists
    specialists: List[SpecialistSummary]
    pool_size: int
    min_pool_size: int
    max_pool_size: int

    # Evolution
    evolution_paused: bool
    pause_reason: Optional[str]
    generations_completed: int
    convergence_status: Dict[str, Any]

    # Performance
    tasks_today: int
    tasks_total: int
    avg_score: float
    best_score: float
    score_trend: str  # improving, stable, declining

    # Recent activity
    recent_tasks: List[Dict[str, Any]]
    last_evolution_at: Optional[datetime]


# ============================================================================
# Router
# ============================================================================


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/overview", response_model=DashboardOverview)
async def get_overview():
    """
    Get complete dashboard overview.

    Returns status of all domains, budget, and evaluation configuration.
    """
    try:
        domains = await _get_all_domain_statuses()
        budget = await _get_budget_status()
        evaluation = await _get_evaluation_status()

        total_specialists = sum(d.specialists for d in domains)
        total_tasks = sum(d.tasks_today for d in domains)

        return DashboardOverview(
            domains=domains,
            budget=budget,
            evaluation=evaluation,
            total_tasks_today=total_tasks,
            total_specialists=total_specialists,
            system_health="healthy",
            last_updated=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains", response_model=List[DomainStatus])
async def list_domains():
    """Get status of all domains."""
    try:
        return await _get_all_domain_statuses()
    except Exception as e:
        logger.error(f"Failed to list domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains/{domain}", response_model=DomainDetail)
async def get_domain_detail(domain: str):
    """
    Get detailed information about a domain.

    Args:
        domain: Domain name (e.g., code_generation, business_documents)
    """
    try:
        detail = await _get_domain_detail(domain)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get domain detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/specialists", response_model=List[SpecialistSummary])
async def list_specialists(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    active_only: bool = Query(True, description="Only show active specialists"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
):
    """List specialists with optional filtering."""
    try:
        return await _get_specialists_list(domain, active_only, limit)
    except Exception as e:
        logger.error(f"Failed to list specialists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/specialists/{specialist_id}", response_model=SpecialistDetail)
async def get_specialist_detail(specialist_id: UUID):
    """
    Get detailed information about a specialist.

    Args:
        specialist_id: UUID of the specialist
    """
    try:
        detail = await _get_specialist_detail(specialist_id)
        if not detail:
            raise HTTPException(
                status_code=404,
                detail=f"Specialist '{specialist_id}' not found",
            )
        return detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get specialist detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget", response_model=BudgetStatus)
async def get_budget():
    """Get current budget status."""
    try:
        return await _get_budget_status()
    except Exception as e:
        logger.error(f"Failed to get budget status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get system-wide statistics."""
    try:
        return await _get_system_stats()
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================


async def _get_all_domain_statuses() -> List[DomainStatus]:
    """Get status of all domains."""
    domains = []

    # Define known domains with mock data for development
    domain_configs = {
        "code_generation": {
            "specialists": 5, "best_score": 0.92, "avg_score": 0.85,
            "tasks_today": 47, "convergence_progress": 78.5, "evolution_paused": False
        },
        "code_review": {
            "specialists": 4, "best_score": 0.88, "avg_score": 0.82,
            "tasks_today": 23, "convergence_progress": 65.0, "evolution_paused": False
        },
        "business_documents": {
            "specialists": 3, "best_score": 0.85, "avg_score": 0.79,
            "tasks_today": 15, "convergence_progress": 45.0, "evolution_paused": False
        },
        "research": {
            "specialists": 4, "best_score": 0.90, "avg_score": 0.84,
            "tasks_today": 31, "convergence_progress": 72.0, "evolution_paused": False
        },
        "planning": {
            "specialists": 3, "best_score": 0.87, "avg_score": 0.81,
            "tasks_today": 12, "convergence_progress": 55.0, "evolution_paused": True
        },
        "administration": {
            "specialists": 2, "best_score": 0.94, "avg_score": 0.91,
            "tasks_today": 8, "convergence_progress": 92.0, "evolution_paused": True,
            "current_jarvis": "JARVIS-v7.2"
        },
    }

    try:
        from core.domain import get_pool_manager
        pool_manager = get_pool_manager()
    except ImportError:
        pool_manager = None

    try:
        from core.evolution import get_evolution_controller
        evolution_controller = get_evolution_controller()
    except ImportError:
        evolution_controller = None

    for domain_name, mock_config in domain_configs.items():
        # Get pool info - try real data first, fall back to mock
        specialists = mock_config["specialists"]
        best_score = mock_config["best_score"]
        avg_score = mock_config["avg_score"]
        tasks_today = mock_config["tasks_today"]
        current_jarvis = mock_config.get("current_jarvis")
        evolution_paused = mock_config["evolution_paused"]
        convergence_progress = mock_config["convergence_progress"]

        if pool_manager:
            try:
                pool = pool_manager.get_pool(domain_name)
                if pool:
                    specialists = len(pool.specialists)
                    if pool.specialists:
                        scores = [s.score for s in pool.specialists if hasattr(s, 'score')]
                        if scores:
                            best_score = max(scores)
                            avg_score = sum(scores) / len(scores)

                    # For administration, get current JARVIS
                    if domain_name == "administration" and pool.specialists:
                        best = max(pool.specialists, key=lambda s: getattr(s, 'score', 0))
                        current_jarvis = best.name if hasattr(best, 'name') else current_jarvis
            except Exception:
                pass

        # Check evolution status from controller if available
        if evolution_controller:
            try:
                status = evolution_controller.get_domain_status(domain_name)
                if status:
                    evolution_paused = status.get("paused", evolution_paused)
                    convergence_progress = status.get("convergence_progress", convergence_progress)
            except Exception:
                pass

        domains.append(DomainStatus(
            name=domain_name,
            specialists=specialists,
            best_score=best_score,
            avg_score=avg_score,
            evolution_paused=evolution_paused,
            convergence_progress=convergence_progress,
            tasks_today=tasks_today,
            current_jarvis=current_jarvis,
        ))

    return domains


async def _get_budget_status() -> BudgetStatus:
    """Get current budget status."""
    # Mock data for development/demo
    mock_budget = BudgetStatus(
        production_spent_today=23.47,
        production_remaining=26.53,
        production_limit=50.0,
        benchmark_spent_today=3.12,
        benchmark_remaining=6.88,
        benchmark_limit=10.0,
        is_warning=False,
        warning_threshold=0.8,
    )

    try:
        from core.cost import get_budget_controller
        budget = get_budget_controller()

        production_status = budget.get_category_status("production")
        benchmark_status = budget.get_category_status("benchmark")

        prod_spent = production_status.get("spent_today", mock_budget.production_spent_today)
        prod_limit = production_status.get("daily_limit", mock_budget.production_limit)
        bench_spent = benchmark_status.get("spent_today", mock_budget.benchmark_spent_today)
        bench_limit = benchmark_status.get("daily_limit", mock_budget.benchmark_limit)

        warning_threshold = 0.8
        is_warning = (prod_spent / prod_limit) >= warning_threshold if prod_limit > 0 else False

        return BudgetStatus(
            production_spent_today=prod_spent,
            production_remaining=max(0, prod_limit - prod_spent),
            production_limit=prod_limit,
            benchmark_spent_today=bench_spent,
            benchmark_remaining=max(0, bench_limit - bench_spent),
            benchmark_limit=bench_limit,
            is_warning=is_warning,
            warning_threshold=warning_threshold,
        )
    except ImportError:
        return mock_budget


async def _get_evaluation_status() -> EvaluationStatus:
    """Get current evaluation configuration."""
    try:
        from core.evaluation import get_evaluation_config
        config = get_evaluation_config()

        return EvaluationStatus(
            mode=config.mode,
            scoring_committee_enabled=config.mode in ("scoring_committee", "both"),
            ai_council_enabled=config.mode in ("ai_council", "both"),
            comparison_tracking=config.mode == "both",
        )
    except ImportError:
        return EvaluationStatus(
            mode="scoring_committee",
            scoring_committee_enabled=True,
            ai_council_enabled=False,
            comparison_tracking=False,
        )


async def _get_domain_detail(domain: str) -> Optional[DomainDetail]:
    """Get detailed information about a domain."""
    try:
        from core.domain import get_pool_manager, get_domain_config
        pool_manager = get_pool_manager()
        domain_config = get_domain_config(domain)
    except ImportError:
        pool_manager = None
        domain_config = None

    if not domain_config:
        return None

    specialists = []
    pool_size = 0
    best_score = 0.0
    avg_score = 0.0

    if pool_manager:
        pool = pool_manager.get_pool(domain)
        if pool:
            pool_size = len(pool.specialists)
            for spec in pool.specialists:
                specialists.append(SpecialistSummary(
                    id=spec.id,
                    name=spec.name,
                    generation=getattr(spec, 'generation', 1),
                    score=getattr(spec, 'score', 0.0),
                    task_count=getattr(spec, 'task_count', 0),
                    is_active=getattr(spec, 'is_active', True),
                ))
            if specialists:
                scores = [s.score for s in specialists]
                best_score = max(scores)
                avg_score = sum(scores) / len(scores)

    # Get evolution status
    evolution_paused = False
    pause_reason = None
    generations = 0
    convergence_status = {}

    try:
        from core.evolution import get_evolution_controller
        controller = get_evolution_controller()
        status = controller.get_domain_status(domain)
        if status:
            evolution_paused = status.get("paused", False)
            pause_reason = status.get("pause_reason")
            generations = status.get("generations", 0)
            convergence_status = status.get("convergence", {})
    except ImportError:
        pass

    return DomainDetail(
        name=domain,
        description=domain_config.description if domain_config else "",
        specialists=specialists,
        pool_size=pool_size,
        min_pool_size=domain_config.min_pool_size if domain_config else 3,
        max_pool_size=domain_config.max_pool_size if domain_config else 10,
        evolution_paused=evolution_paused,
        pause_reason=pause_reason,
        generations_completed=generations,
        convergence_status=convergence_status,
        tasks_today=0,
        tasks_total=0,
        avg_score=avg_score,
        best_score=best_score,
        score_trend="stable",
        recent_tasks=[],
        last_evolution_at=None,
    )


async def _get_specialists_list(
    domain: Optional[str],
    active_only: bool,
    limit: int,
) -> List[SpecialistSummary]:
    """Get list of specialists."""
    specialists = []

    try:
        from core.domain import get_pool_manager
        pool_manager = get_pool_manager()

        domains_to_check = [domain] if domain else pool_manager.get_domains()

        for d in domains_to_check:
            pool = pool_manager.get_pool(d)
            if pool:
                for spec in pool.specialists:
                    is_active = getattr(spec, 'is_active', True)
                    if active_only and not is_active:
                        continue

                    specialists.append(SpecialistSummary(
                        id=spec.id,
                        name=spec.name,
                        generation=getattr(spec, 'generation', 1),
                        score=getattr(spec, 'score', 0.0),
                        task_count=getattr(spec, 'task_count', 0),
                        is_active=is_active,
                    ))

                    if len(specialists) >= limit:
                        break

            if len(specialists) >= limit:
                break

    except ImportError:
        # Return mock specialists for development/demo
        from uuid import uuid4
        mock_specialists = [
            ("CodeGen-Alpha-v5", "code_generation", 5, 0.92, 156, True),
            ("CodeGen-Beta-v4", "code_generation", 4, 0.88, 134, True),
            ("CodeGen-Gamma-v5", "code_generation", 5, 0.85, 98, True),
            ("Review-Prime-v3", "code_review", 3, 0.88, 89, True),
            ("Review-Expert-v4", "code_review", 4, 0.85, 67, True),
            ("DocWriter-Pro-v2", "business_documents", 2, 0.85, 45, True),
            ("Research-Deep-v4", "research", 4, 0.90, 78, True),
            ("Planner-Strategic-v3", "planning", 3, 0.87, 34, True),
            ("JARVIS-v7.2", "administration", 7, 0.94, 256, True),
        ]

        for name, dom, gen, score, tasks, active in mock_specialists:
            if domain and dom != domain:
                continue
            if active_only and not active:
                continue

            specialists.append(SpecialistSummary(
                id=uuid4(),
                name=name,
                generation=gen,
                score=score,
                task_count=tasks,
                is_active=active,
            ))

            if len(specialists) >= limit:
                break

    return specialists[:limit]


async def _get_specialist_detail(specialist_id: UUID) -> Optional[SpecialistDetail]:
    """Get detailed information about a specialist."""
    try:
        from core.domain import get_pool_manager
        pool_manager = get_pool_manager()

        spec = pool_manager.get_specialist(specialist_id)
        if not spec:
            return None

        return SpecialistDetail(
            id=spec.id,
            name=spec.name,
            domain=getattr(spec, 'domain', 'unknown'),
            generation=getattr(spec, 'generation', 1),
            created_at=getattr(spec, 'created_at', datetime.utcnow()),
            is_active=getattr(spec, 'is_active', True),
            total_tasks=getattr(spec, 'task_count', 0),
            successful_tasks=getattr(spec, 'successful_tasks', 0),
            success_rate=getattr(spec, 'success_rate', 0.0),
            avg_score=getattr(spec, 'score', 0.0),
            recent_scores=getattr(spec, 'recent_scores', []),
            system_prompt_preview=getattr(spec, 'system_prompt', '')[:500],
            model_preference=getattr(spec, 'model_preference', None),
            temperature=getattr(spec, 'temperature', 0.7),
            parent_id=getattr(spec, 'parent_id', None),
            mutation_summary=getattr(spec, 'mutation_summary', None),
            learnings_applied=getattr(spec, 'learnings_count', 0),
        )

    except ImportError:
        return None


async def _get_system_stats() -> Dict[str, Any]:
    """Get system-wide statistics."""
    stats = {
        "uptime_seconds": 0,
        "total_requests": 0,
        "total_specialists": 0,
        "total_evolutions": 0,
        "graveyard_size": 0,
    }

    try:
        from core.domain import get_pool_manager
        pool_manager = get_pool_manager()
        stats["total_specialists"] = pool_manager.get_total_specialists()
    except ImportError:
        pass

    try:
        from core.evolution import get_graveyard
        graveyard = get_graveyard()
        stats["graveyard_size"] = graveyard.get_count()
    except ImportError:
        pass

    try:
        from core.routing import get_task_router
        router = get_task_router()
        router_stats = router.get_stats()
        stats["total_requests"] = router_stats.get("total_requests", 0)
    except ImportError:
        pass

    return stats
