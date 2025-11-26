"""
Database Base Configuration

SQLAlchemy declarative base and session management.
Supports SQLite for development and PostgreSQL for production.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session


# Create declarative base
Base = declarative_base()


# Default database URL (SQLite for development)
DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./jarvis_data.db"
)


# Engine cache
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine(database_url: Optional[str] = None) -> Engine:
    """
    Get or create database engine.

    Args:
        database_url: Database connection URL (uses default if not specified)

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if _engine is None:
        url = database_url or DEFAULT_DATABASE_URL

        # Configure engine based on database type
        if url.startswith("sqlite"):
            _engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                echo=False,
            )
            # Enable foreign keys for SQLite
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            # PostgreSQL or other databases
            _engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
            )

    return _engine


def get_session_factory(database_url: Optional[str] = None) -> sessionmaker:
    """
    Get or create session factory.

    Args:
        database_url: Database connection URL

    Returns:
        SQLAlchemy sessionmaker
    """
    global _session_factory

    if _session_factory is None:
        engine = get_engine(database_url)
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
        )

    return _session_factory


@contextmanager
def get_session(database_url: Optional[str] = None) -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with get_session() as session:
            session.query(Model).all()

    Args:
        database_url: Database connection URL

    Yields:
        SQLAlchemy Session
    """
    factory = get_session_factory(database_url)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables(database_url: Optional[str] = None) -> None:
    """
    Create all database tables.

    Args:
        database_url: Database connection URL
    """
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)


def drop_all_tables(database_url: Optional[str] = None) -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!

    Args:
        database_url: Database connection URL
    """
    engine = get_engine(database_url)
    Base.metadata.drop_all(bind=engine)


def reset_engine() -> None:
    """Reset engine and session factory (for testing)."""
    global _engine, _session_factory
    if _engine:
        _engine.dispose()
    _engine = None
    _session_factory = None
