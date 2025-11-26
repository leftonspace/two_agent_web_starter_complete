"""
JARVIS Dashboard API

FastAPI application providing REST endpoints for the JARVIS dashboard.

Run with:
    uvicorn api.main:app --reload --port 8000

API Documentation available at:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting JARVIS Dashboard API...")

    # Initialize services
    try:
        _initialize_services()
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.warning(f"Some services failed to initialize: {e}")

    yield

    # Shutdown
    logger.info("Shutting down JARVIS Dashboard API...")


def _initialize_services() -> None:
    """Initialize core services."""
    services_status = {}

    # Try to initialize each service
    try:
        from core.routing import get_task_router
        get_task_router()
        services_status["routing"] = "ok"
    except ImportError:
        services_status["routing"] = "not available"

    try:
        from core.benchmark import get_benchmark_loader, get_benchmark_executor
        get_benchmark_loader()
        get_benchmark_executor()
        services_status["benchmark"] = "ok"
    except ImportError:
        services_status["benchmark"] = "not available"

    try:
        from core.evolution import get_evolution_controller
        get_evolution_controller()
        services_status["evolution"] = "ok"
    except ImportError:
        services_status["evolution"] = "not available"

    logger.info(f"Services status: {services_status}")


# ============================================================================
# Application
# ============================================================================


app = FastAPI(
    title="JARVIS Dashboard API",
    description="""
## JARVIS - Self-Evolving Business AI Platform

Dashboard API for monitoring and controlling the JARVIS system.

### Features

- **Dashboard**: System overview, domain status, specialist details
- **Evaluation**: Control Scoring Committee vs AI Council modes
- **Benchmark**: Run and monitor benchmark executions
- **Tasks**: View task history and submit feedback

### Authentication

Currently no authentication required (development mode).
Production deployment should add OAuth2 or API key authentication.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ============================================================================
# CORS Middleware
# ============================================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url),
        },
    )


# ============================================================================
# Include Routers
# ============================================================================


from api.routes.dashboard import router as dashboard_router
from api.routes.evaluation import router as evaluation_router
from api.routes.benchmark import router as benchmark_router
from api.routes.tasks import router as tasks_router

app.include_router(dashboard_router)
app.include_router(evaluation_router)
app.include_router(benchmark_router)
app.include_router(tasks_router)


# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "JARVIS Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health():
    """
    Health check endpoint.

    Returns system health status for monitoring and load balancers.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    # Check core services
    try:
        from core.routing import get_task_router
        get_task_router()
        health_status["services"]["routing"] = "healthy"
    except Exception as e:
        health_status["services"]["routing"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"

    try:
        from core.benchmark import get_benchmark_loader
        loader = get_benchmark_loader()
        discovered = loader.discover()
        health_status["services"]["benchmark"] = f"healthy ({len(discovered)} domains)"
    except Exception as e:
        health_status["services"]["benchmark"] = f"unhealthy: {e}"

    return health_status


@app.get("/version", tags=["root"])
async def version():
    """Get API version information."""
    return {
        "api_version": "1.0.0",
        "jarvis_version": "7.5",
        "python_version": "3.11+",
    }


@app.get("/stats", tags=["root"])
async def stats():
    """Get quick system statistics."""
    stats: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        from core.benchmark import get_benchmark_loader
        loader = get_benchmark_loader()
        discovered = loader.discover()
        stats["benchmarks"] = {
            "domains": len(discovered),
            "total": sum(len(b) for b in discovered.values()),
        }
    except ImportError:
        stats["benchmarks"] = "not available"

    try:
        from core.routing import get_task_router
        router = get_task_router()
        router_stats = router.get_stats()
        stats["routing"] = {
            "total_requests": router_stats.get("total_requests", 0),
        }
    except ImportError:
        stats["routing"] = "not available"

    return stats


# ============================================================================
# Development Server
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
