"""
JARVIS Database Backends

Database backend abstraction and implementations for:
- SQLite (default, single-machine)
- PostgreSQL (production, horizontal scaling)
- Connection pooling
- Migration tools
"""

from .kg_backends import (
    KGBackend,
    SQLiteBackend,
    PostgreSQLBackend,
    get_backend,
)

__all__ = [
    "KGBackend",
    "SQLiteBackend",
    "PostgreSQLBackend",
    "get_backend",
]
