"""
Knowledge Graph Backend Abstraction

Database backend abstraction for KG with support for:
- SQLite (default, single-machine, file-based)
- PostgreSQL (production, horizontal scaling, connection pooling)

The backend layer provides a unified interface for both databases,
enabling seamless switching and horizontal scaling.
"""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    import psycopg2.pool
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


# =============================================================================
# Backend Interface
# =============================================================================

class KGBackend(ABC):
    """
    Abstract base class for KG database backends.

    Provides unified interface for SQLite and PostgreSQL.
    """

    @abstractmethod
    def connect(self) -> None:
        """Initialize database connection"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    def init_schema(self) -> None:
        """Create database tables"""
        pass

    @abstractmethod
    def execute(self, query: str, params: Tuple = ()) -> Any:
        """Execute a query"""
        pass

    @abstractmethod
    def executemany(self, query: str, params_list: List[Tuple]) -> None:
        """Execute query with multiple parameter sets"""
        pass

    @abstractmethod
    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        pass

    @abstractmethod
    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit transaction"""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback transaction"""
        pass

    @abstractmethod
    def lastrowid(self) -> int:
        """Get last inserted row ID"""
        pass


# =============================================================================
# SQLite Backend
# =============================================================================

class SQLiteBackend(KGBackend):
    """
    SQLite backend for KG.

    File-based, single-writer, good for development and single-machine deployment.
    """

    def __init__(self, db_path: Path):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._last_row_id: int = 0

    def connect(self) -> None:
        """Initialize database connection"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self) -> None:
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def init_schema(self) -> None:
        """Create database tables"""
        schema_sql = """
        -- Entities table
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(type, name)
        );

        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

        -- Relationships table
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (from_id) REFERENCES entities(id) ON DELETE CASCADE,
            FOREIGN KEY (to_id) REFERENCES entities(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type);

        -- Mission history table
        CREATE TABLE IF NOT EXISTS mission_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mission_id TEXT NOT NULL,
            status TEXT NOT NULL,
            domain TEXT,
            cost_usd REAL,
            iterations INTEGER,
            duration_seconds REAL,
            files_modified INTEGER,
            metadata TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(mission_id)
        );

        CREATE INDEX IF NOT EXISTS idx_mission_history_status ON mission_history(status);
        CREATE INDEX IF NOT EXISTS idx_mission_history_domain ON mission_history(domain);
        CREATE INDEX IF NOT EXISTS idx_mission_history_created ON mission_history(created_at);

        -- File snapshots table
        CREATE TABLE IF NOT EXISTS file_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            mission_id TEXT,
            size_bytes INTEGER,
            lines_of_code INTEGER,
            hash TEXT,
            created_at TEXT NOT NULL,
            metadata TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_file_snapshots_path ON file_snapshots(file_path);
        CREATE INDEX IF NOT EXISTS idx_file_snapshots_mission ON file_snapshots(mission_id);
        CREATE INDEX IF NOT EXISTS idx_file_snapshots_created ON file_snapshots(created_at);
        """

        self.conn.executescript(schema_sql)
        self.conn.commit()

    def execute(self, query: str, params: Tuple = ()) -> Any:
        """Execute a query"""
        self.cursor.execute(query, params)
        self._last_row_id = self.cursor.lastrowid
        return self.cursor

    def executemany(self, query: str, params_list: List[Tuple]) -> None:
        """Execute query with multiple parameter sets"""
        self.cursor.executemany(query, params_list)

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self) -> None:
        """Commit transaction"""
        self.conn.commit()

    def rollback(self) -> None:
        """Rollback transaction"""
        self.conn.rollback()

    def lastrowid(self) -> int:
        """Get last inserted row ID"""
        return self._last_row_id


# =============================================================================
# PostgreSQL Backend
# =============================================================================

class PostgreSQLBackend(KGBackend):
    """
    PostgreSQL backend for KG.

    Production-ready with:
    - Connection pooling
    - Horizontal scaling support
    - Multi-writer capability
    - Better performance for large datasets
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "jarvis_kg",
        user: str = "jarvis",
        password: str = "",
        pool_size: int = 10,
        max_overflow: int = 20,
    ):
        """
        Initialize PostgreSQL backend.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            pool_size: Connection pool size
            max_overflow: Max overflow connections
        """
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")

        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow

        self.pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self.conn: Optional[Any] = None
        self.cursor: Optional[Any] = None
        self._last_row_id: int = 0

    def connect(self) -> None:
        """Initialize connection pool"""
        # Create connection pool
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=self.pool_size + self.max_overflow,
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

        # Get initial connection
        self.conn = self.pool.getconn()
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

    def close(self) -> None:
        """Close all connections"""
        if self.cursor:
            self.cursor.close()
        if self.conn and self.pool:
            self.pool.putconn(self.conn)
        if self.pool:
            self.pool.closeall()

    def init_schema(self) -> None:
        """Create database tables"""
        schema_sql = """
        -- Entities table
        CREATE TABLE IF NOT EXISTS entities (
            id SERIAL PRIMARY KEY,
            type VARCHAR(50) NOT NULL,
            name TEXT NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE(type, name)
        );

        CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
        CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
        CREATE INDEX IF NOT EXISTS idx_entities_metadata ON entities USING GIN(metadata);

        -- Relationships table
        CREATE TABLE IF NOT EXISTS relationships (
            id SERIAL PRIMARY KEY,
            from_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            to_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
            type VARCHAR(50) NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_id);
        CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type);
        CREATE INDEX IF NOT EXISTS idx_relationships_from_type ON relationships(from_id, type);
        CREATE INDEX IF NOT EXISTS idx_relationships_to_type ON relationships(to_id, type);

        -- Mission history table
        CREATE TABLE IF NOT EXISTS mission_history (
            id SERIAL PRIMARY KEY,
            mission_id VARCHAR(255) NOT NULL UNIQUE,
            status VARCHAR(50) NOT NULL,
            domain VARCHAR(100),
            cost_usd DECIMAL(10, 4),
            iterations INTEGER,
            duration_seconds DECIMAL(10, 2),
            files_modified INTEGER,
            metadata JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_mission_history_status ON mission_history(status);
        CREATE INDEX IF NOT EXISTS idx_mission_history_domain ON mission_history(domain);
        CREATE INDEX IF NOT EXISTS idx_mission_history_created ON mission_history(created_at);

        -- File snapshots table
        CREATE TABLE IF NOT EXISTS file_snapshots (
            id SERIAL PRIMARY KEY,
            file_path TEXT NOT NULL,
            mission_id VARCHAR(255),
            size_bytes INTEGER,
            lines_of_code INTEGER,
            hash VARCHAR(64),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            metadata JSONB
        );

        CREATE INDEX IF NOT EXISTS idx_file_snapshots_path ON file_snapshots(file_path);
        CREATE INDEX IF NOT EXISTS idx_file_snapshots_mission ON file_snapshots(mission_id);
        CREATE INDEX IF NOT EXISTS idx_file_snapshots_created ON file_snapshots(created_at);
        """

        self.cursor.execute(schema_sql)
        self.conn.commit()

    def execute(self, query: str, params: Tuple = ()) -> Any:
        """Execute a query"""
        self.cursor.execute(query, params)
        # Try to get lastrowid from RETURNING clause or currval
        try:
            if self.cursor.description:
                row = self.cursor.fetchone()
                if row and 'id' in row:
                    self._last_row_id = row['id']
        except:
            pass
        return self.cursor

    def executemany(self, query: str, params_list: List[Tuple]) -> None:
        """Execute query with multiple parameter sets"""
        self.cursor.executemany(query, params_list)

    def fetchone(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        self.cursor.execute(query, params)
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self) -> None:
        """Commit transaction"""
        self.conn.commit()

    def rollback(self) -> None:
        """Rollback transaction"""
        self.conn.rollback()

    def lastrowid(self) -> int:
        """Get last inserted row ID"""
        return self._last_row_id


# =============================================================================
# Backend Factory
# =============================================================================

def get_backend(backend_type: str = "sqlite", **kwargs) -> KGBackend:
    """
    Get database backend instance.

    Args:
        backend_type: "sqlite" or "postgres"
        **kwargs: Backend-specific configuration

    Returns:
        KGBackend instance

    Examples:
        # SQLite
        backend = get_backend("sqlite", db_path=Path("data/kg.db"))

        # PostgreSQL
        backend = get_backend(
            "postgres",
            host="localhost",
            database="jarvis_kg",
            user="jarvis",
            password="secret"
        )
    """
    if backend_type == "sqlite":
        db_path = kwargs.get("db_path")
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "knowledge_graph.db"
        return SQLiteBackend(db_path)

    elif backend_type == "postgres" or backend_type == "postgresql":
        if not POSTGRES_AVAILABLE:
            raise ImportError(
                "PostgreSQL support requires psycopg2. "
                "Install with: pip install psycopg2-binary"
            )

        return PostgreSQLBackend(
            host=kwargs.get("host", "localhost"),
            port=kwargs.get("port", 5432),
            database=kwargs.get("database", "jarvis_kg"),
            user=kwargs.get("user", "jarvis"),
            password=kwargs.get("password", ""),
            pool_size=kwargs.get("pool_size", 10),
            max_overflow=kwargs.get("max_overflow", 20),
        )

    else:
        raise ValueError(f"Unknown backend type: {backend_type}")
