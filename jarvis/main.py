"""
JARVIS - Self-Evolving Business AI Platform

Main startup script that initializes all components and starts the server.

Usage:
    # Start the server
    python -m jarvis.main

    # Or with uvicorn directly
    uvicorn jarvis.main:app --host 0.0.0.0 --port 8000 --reload
"""

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


# ============================================================================
# JARVIS Main Orchestrator
# ============================================================================


class JARVIS:
    """
    Main JARVIS orchestrator.

    Initializes and manages all system components:
    - Provider registry and model routing
    - Budget controller
    - Specialist pools and spawner
    - Evaluation system (Scoring Committee + AI Council)
    - Evolution controller
    - Task router
    - Benchmark executor
    """

    def __init__(self):
        """Initialize JARVIS with no components loaded."""
        # Core infrastructure
        self.registry = None
        self.model_router = None
        self.budget_controller = None

        # Specialists
        self.pool_manager = None
        self.spawner = None

        # Evaluation
        self.evaluation_controller = None

        # Evolution
        self.evolution_controller = None

        # Routing
        self.task_router = None
        self.domain_classifier = None

        # Benchmarks
        self.benchmark_executor = None
        self.benchmark_loader = None

        # State
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize all JARVIS components.

        Order matters - components are initialized in dependency order.
        """
        if self._initialized:
            logger.warning("JARVIS already initialized")
            return

        logger.info("=" * 60)
        logger.info("Initializing JARVIS...")
        logger.info("=" * 60)

        try:
            # 1. Database (if configured)
            await self._init_database()

            # 2. Budget Controller
            await self._init_budget()

            # 3. Provider Registry & Model Router
            await self._init_providers()

            # 4. Specialist Pools
            await self._init_specialists()

            # 5. Evaluation System
            await self._init_evaluation()

            # 6. Evolution Controller
            await self._init_evolution()

            # 7. Task Router
            await self._init_routing()

            # 8. Benchmark System
            await self._init_benchmarks()

            # 9. Ensure domains have specialists
            await self._ensure_domains_initialized()

            self._initialized = True
            logger.info("=" * 60)
            logger.info("JARVIS initialized successfully!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Failed to initialize JARVIS: {e}")
            raise

    async def _init_database(self) -> None:
        """Initialize database connection."""
        logger.info("Initializing database...")
        try:
            from database.connection import init_database
            await init_database()
            logger.info("  Database initialized")
        except ImportError:
            logger.warning("  Database module not available, using in-memory storage")
        except Exception as e:
            logger.warning(f"  Database init failed: {e}, using in-memory storage")

    async def _init_budget(self) -> None:
        """Initialize budget controller."""
        logger.info("Initializing budget controller...")
        from core.models.budget import BudgetController, get_budget_controller

        self.budget_controller = get_budget_controller()
        logger.info("  Budget controller ready")

    async def _init_providers(self) -> None:
        """Initialize provider registry and model router."""
        logger.info("Initializing provider registry...")

        try:
            from core.models.registry import ProviderRegistry, get_registry

            self.registry = get_registry()
            logger.info(f"  Registry loaded with {len(self.registry.providers)} providers")

        except ImportError:
            logger.warning("  Provider registry not available")
            self.registry = None

        try:
            from core.models.router import ModelRouter, get_model_router

            self.model_router = get_model_router()
            logger.info("  Model router ready")

        except ImportError:
            logger.warning("  Model router not available")
            self.model_router = None

    async def _init_specialists(self) -> None:
        """Initialize specialist pool manager and spawner."""
        logger.info("Initializing specialist system...")

        from core.specialists.pool_manager import PoolManager, get_pool_manager
        from core.specialists.spawner import Spawner, get_spawner

        self.pool_manager = get_pool_manager()
        self.spawner = get_spawner()

        logger.info(f"  Pool manager ready with {len(self.pool_manager.list_domains())} domains")
        logger.info("  Spawner ready")

    async def _init_evaluation(self) -> None:
        """Initialize evaluation system."""
        logger.info("Initializing evaluation system...")

        from core.evaluation.controller import (
            EvaluationController,
            get_evaluation_controller,
        )

        self.evaluation_controller = get_evaluation_controller()

        # Try to register evaluators
        try:
            from core.evaluation.scoring_committee import ScoringCommittee

            sc = ScoringCommittee()
            self.evaluation_controller.register_scoring_committee(sc)
            logger.info("  Scoring Committee registered")
        except ImportError:
            logger.warning("  Scoring Committee not available")

        try:
            from core.evaluation.ai_council import AICouncil

            ac = AICouncil()
            self.evaluation_controller.register_ai_council(ac)
            logger.info("  AI Council registered")
        except ImportError:
            logger.warning("  AI Council not available")

        logger.info(f"  Evaluation mode: {self.evaluation_controller.get_mode().value}")

    async def _init_evolution(self) -> None:
        """Initialize evolution controller."""
        logger.info("Initializing evolution controller...")

        from core.evolution.controller import (
            EvolutionController,
            get_evolution_controller,
        )

        self.evolution_controller = get_evolution_controller()
        logger.info("  Evolution controller ready")

    async def _init_routing(self) -> None:
        """Initialize task router and domain classifier."""
        logger.info("Initializing routing system...")

        from core.routing.classifier import DomainClassifier, get_domain_classifier
        from core.routing.router import TaskRouter, get_task_router

        self.domain_classifier = get_domain_classifier()
        self.task_router = get_task_router()

        logger.info(f"  Domain classifier ready ({len(self.domain_classifier.domains)} domains)")
        logger.info("  Task router ready")

    async def _init_benchmarks(self) -> None:
        """Initialize benchmark system."""
        logger.info("Initializing benchmark system...")

        from core.benchmark.loader import BenchmarkLoader, get_benchmark_loader
        from core.benchmark.executor import BenchmarkExecutor, get_benchmark_executor

        self.benchmark_loader = get_benchmark_loader()
        self.benchmark_executor = get_benchmark_executor()

        # Discover available benchmarks
        available = self.benchmark_loader.discover()
        total = sum(len(v) for v in available.values())
        logger.info(f"  Benchmark loader ready ({total} benchmarks in {len(available)} domains)")
        logger.info("  Benchmark executor ready")

    async def _ensure_domains_initialized(self) -> None:
        """Ensure all core domains have specialists."""
        core_domains = [
            "administration",
            "code_generation",
            "code_review",
            "business_documents",
            "research",
            "planning",
        ]

        logger.info("Checking domain pools...")

        for domain in core_domains:
            pool = self.pool_manager.get_pool(domain)

            if len(pool.specialists) == 0:
                logger.info(f"  Initializing {domain} pool with 3 specialists...")
                for i in range(3):
                    specialist = self.spawner.spawn_initial(domain)
                    pool.add(specialist)
                logger.info(f"    Created: {[s.name for s in pool.specialists]}")
            else:
                logger.info(f"  {domain}: {len(pool.specialists)} specialists")

    # -------------------------------------------------------------------------
    # Main API
    # -------------------------------------------------------------------------

    async def execute(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Any, Any]:
        """
        Main entry point for executing requests.

        Args:
            request: User request to process
            context: Additional context

        Returns:
            Tuple of (RoutingResult, TaskResult)
        """
        if not self._initialized:
            raise RuntimeError("JARVIS not initialized. Call initialize() first.")

        return await self.task_router.route_and_execute(request, context)

    async def get_jarvis_specialist(self):
        """Get the current JARVIS specialist (best administration)."""
        return self.pool_manager.get_jarvis()

    def get_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "initialized": self._initialized,
            "pools": self.pool_manager.get_stats() if self.pool_manager else None,
            "budget": {
                cat.value: self.budget_controller.get_status(cat).model_dump()
                for cat in ["production", "benchmark", "development"]
            } if self.budget_controller else None,
            "evaluation_mode": (
                self.evaluation_controller.get_mode().value
                if self.evaluation_controller
                else None
            ),
            "router_stats": (
                self.task_router.get_stats() if self.task_router else None
            ),
        }

    async def shutdown(self) -> None:
        """Clean shutdown of all components."""
        logger.info("Shutting down JARVIS...")

        try:
            # Save budget state
            if self.budget_controller:
                logger.info("  Saving budget state...")
                # Budget controller auto-saves

            # Save pool state
            if self.pool_manager:
                logger.info("  Saving pool state...")
                self.pool_manager.save_to_database()

            logger.info("JARVIS shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# ============================================================================
# Global Instance
# ============================================================================


# Singleton JARVIS instance
jarvis = JARVIS()


def get_jarvis() -> JARVIS:
    """Get the global JARVIS instance."""
    return jarvis


# ============================================================================
# FastAPI Integration
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    # Startup
    await jarvis.initialize()
    yield
    # Shutdown
    await jarvis.shutdown()


def create_app() -> FastAPI:
    """Create the FastAPI application with JARVIS integration."""
    from api.main import app as api_app

    # The API app already has CORS and routes configured
    # We just need to add the lifespan

    # Create a new app with lifespan
    app = FastAPI(
        title="JARVIS - Self-Evolving Business AI",
        description="AI platform with specialist pools, evolution, and benchmarking",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Mount the API routes
    app.mount("/api", api_app)

    # Add root endpoint
    @app.get("/")
    async def root():
        return {
            "name": "JARVIS",
            "version": "1.0.0",
            "status": "running",
            "api_docs": "/api/docs",
        }

    @app.get("/status")
    async def status():
        return jarvis.get_status()

    return app


# Create the app
app = create_app()


# ============================================================================
# CLI Entry Point
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    # Load environment
    host = os.getenv("JARVIS_HOST", "0.0.0.0")
    port = int(os.getenv("JARVIS_PORT", "8000"))
    reload = os.getenv("JARVIS_RELOAD", "false").lower() == "true"
    log_level = os.getenv("JARVIS_LOG_LEVEL", "info").lower()

    logger.info(f"Starting JARVIS on {host}:{port}")

    uvicorn.run(
        "jarvis.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
