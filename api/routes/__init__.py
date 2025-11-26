"""
API Routes Package

All FastAPI routers for the JARVIS Dashboard API.
"""

from .dashboard import router as dashboard_router
from .evaluation import router as evaluation_router
from .benchmark import router as benchmark_router
from .tasks import router as tasks_router

__all__ = [
    "dashboard_router",
    "evaluation_router",
    "benchmark_router",
    "tasks_router",
]
