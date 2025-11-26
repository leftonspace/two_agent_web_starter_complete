"""
JARVIS Dashboard API Package

FastAPI application for the JARVIS dashboard.

Usage:
    uvicorn api.main:app --reload --port 8000

Or programmatically:
    from api.main import app
"""

from .main import app

__all__ = ["app"]
