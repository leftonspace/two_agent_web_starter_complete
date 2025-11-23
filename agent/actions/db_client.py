"""
Database operations with connection pooling and safety controls.

PHASE 8.4: Database client for SQL databases with read-only mode,
transaction management, and query timeout.
"""

import re
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from enum import Enum

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncConnection,
    AsyncSession
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool, QueuePool

from agent.core_logging import log_event


# Pre-compiled regex patterns for SQL validation (performance optimization)
_SQL_LINE_COMMENT_PATTERN = re.compile(r'--.*$', re.MULTILINE)
_SQL_BLOCK_COMMENT_PATTERN = re.compile(r'/\*.*?\*/', re.DOTALL)
_READ_ONLY_PATTERNS = [
    re.compile(r'^SELECT\s', re.IGNORECASE),
    re.compile(r'^WITH\s', re.IGNORECASE),
    re.compile(r'^EXPLAIN\s', re.IGNORECASE),
    re.compile(r'^SHOW\s', re.IGNORECASE),
    re.compile(r'^DESCRIBE\s', re.IGNORECASE),
    re.compile(r'^DESC\s', re.IGNORECASE),
]


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


class DatabaseClient:
    """
    Database operations with safety controls.

    Features:
    - Connection pooling with SQLAlchemy
    - Read-only mode by default
    - Transaction management
    - Query timeout protection
    - Result pagination
    - Parameter binding for SQL injection prevention
    - Support for PostgreSQL, MySQL, SQLite

    Example:
        client = DatabaseClient(
            connection_string="postgresql+asyncpg://user:pass@localhost/db",
            read_only=True
        )

        # Query with parameters
        results = await client.query(
            "SELECT * FROM users WHERE id = :id",
            params={"id": 123}
        )

        # Transaction
        async with client.transaction() as conn:
            await client.execute(
                "UPDATE users SET status = :status WHERE id = :id",
                params={"status": "active", "id": 123},
                connection=conn
            )

        # Pagination
        results = await client.query(
            "SELECT * FROM users ORDER BY created_at",
            limit=10,
            offset=20
        )
    """

    def __init__(
        self,
        connection_string: str,
        read_only: bool = True,
        pool_size: int = 5,
        max_overflow: int = 10,
        query_timeout: float = 30.0,
        echo: bool = False
    ):
        """
        Initialize database client.

        Args:
            connection_string: SQLAlchemy connection string
            read_only: Enable read-only mode (blocks write operations)
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            query_timeout: Query timeout in seconds
            echo: Echo SQL statements (for debugging)
        """
        self.connection_string = connection_string
        self.read_only = read_only
        self.query_timeout = query_timeout

        # Determine database type
        self.db_type = self._detect_database_type(connection_string)

        # Create async engine with connection pooling
        if self.db_type == DatabaseType.SQLITE:
            # SQLite doesn't support pooling in the same way
            self.engine: AsyncEngine = create_async_engine(
                connection_string,
                echo=echo,
                poolclass=NullPool  # SQLite uses NullPool
            )
        else:
            self.engine: AsyncEngine = create_async_engine(
                connection_string,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Verify connections before using
                poolclass=QueuePool
            )

        # Create session factory
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Statistics
        self.query_count = 0
        self.error_count = 0

        log_event("database_client_initialized", {
            "db_type": self.db_type.value,
            "read_only": read_only,
            "pool_size": pool_size
        })

    def _detect_database_type(self, connection_string: str) -> DatabaseType:
        """
        Detect database type from connection string.

        Args:
            connection_string: SQLAlchemy connection string

        Returns:
            DatabaseType enum
        """
        if connection_string.startswith("postgresql"):
            return DatabaseType.POSTGRESQL
        elif connection_string.startswith("mysql"):
            return DatabaseType.MYSQL
        elif connection_string.startswith("sqlite"):
            return DatabaseType.SQLITE
        else:
            raise ValueError(f"Unsupported database type: {connection_string}")

    def _is_read_only_query(self, sql: str) -> bool:
        """
        Check if SQL query is read-only.

        Uses pre-compiled regex patterns for better performance.

        Args:
            sql: SQL query string

        Returns:
            True if query is read-only (SELECT, WITH)
        """
        # Normalize SQL (remove comments, extra whitespace) using cached patterns
        normalized = _SQL_LINE_COMMENT_PATTERN.sub('', sql)
        normalized = _SQL_BLOCK_COMMENT_PATTERN.sub('', normalized)
        normalized = normalized.strip().upper()

        # Check for read-only statements using cached patterns
        for pattern in _READ_ONLY_PATTERNS:
            if pattern.match(normalized):
                return True

        return False

    def _validate_query(self, sql: str):
        """
        Validate SQL query for safety.

        Args:
            sql: SQL query string

        Raises:
            ValueError: If query is invalid or violates read-only mode
        """
        if not sql or not sql.strip():
            raise ValueError("Empty SQL query")

        if self.read_only and not self._is_read_only_query(sql):
            raise ValueError(
                "Write operations not allowed in read-only mode. "
                f"Query: {sql[:100]}"
            )

    async def query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        connection: Optional[AsyncConnection] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results.

        Args:
            sql: SQL query string
            params: Query parameters (for parameter binding)
            limit: Result limit (pagination)
            offset: Result offset (pagination)
            connection: Optional connection (for transactions)

        Returns:
            List of result rows as dictionaries

        Raises:
            ValueError: If query is invalid
            asyncio.TimeoutError: If query times out
        """
        self._validate_query(sql)

        # Add pagination if specified
        if limit is not None:
            sql = f"{sql} LIMIT :limit_value"
            params = params or {}
            params["limit_value"] = limit

        if offset is not None:
            sql = f"{sql} OFFSET :offset_value"
            params = params or {}
            params["offset_value"] = offset

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_query(sql, params, connection),
                timeout=self.query_timeout
            )

            self.query_count += 1

            log_event("database_query_executed", {
                "sql": sql[:100],
                "params": str(params)[:100] if params else None,
                "result_count": len(result)
            })

            return result

        except asyncio.TimeoutError:
            self.error_count += 1
            log_event("database_query_timeout", {
                "sql": sql[:100],
                "timeout": self.query_timeout
            })
            raise

        except Exception as e:
            self.error_count += 1
            log_event("database_query_error", {
                "sql": sql[:100],
                "error": str(e)
            })
            raise

    async def _execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]],
        connection: Optional[AsyncConnection]
    ) -> List[Dict[str, Any]]:
        """
        Internal query execution.

        Args:
            sql: SQL query
            params: Query parameters
            connection: Optional connection

        Returns:
            List of result dictionaries
        """
        if connection:
            # Use provided connection (transaction)
            result = await connection.execute(text(sql), params or {})
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        else:
            # Use connection from pool
            async with self.engine.begin() as conn:
                result = await conn.execute(text(sql), params or {})
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]

    async def execute(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        connection: Optional[AsyncConnection] = None
    ) -> int:
        """
        Execute SQL statement (INSERT, UPDATE, DELETE).

        Args:
            sql: SQL statement
            params: Statement parameters
            connection: Optional connection (for transactions)

        Returns:
            Number of rows affected

        Raises:
            ValueError: If in read-only mode or invalid statement
        """
        self._validate_query(sql)

        try:
            result = await asyncio.wait_for(
                self._execute_statement(sql, params, connection),
                timeout=self.query_timeout
            )

            self.query_count += 1

            log_event("database_execute", {
                "sql": sql[:100],
                "rows_affected": result
            })

            return result

        except asyncio.TimeoutError:
            self.error_count += 1
            raise

        except Exception as e:
            self.error_count += 1
            log_event("database_execute_error", {
                "sql": sql[:100],
                "error": str(e)
            })
            raise

    async def _execute_statement(
        self,
        sql: str,
        params: Optional[Dict[str, Any]],
        connection: Optional[AsyncConnection]
    ) -> int:
        """
        Internal statement execution.

        Args:
            sql: SQL statement
            params: Statement parameters
            connection: Optional connection

        Returns:
            Rows affected
        """
        if connection:
            result = await connection.execute(text(sql), params or {})
            return result.rowcount
        else:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(sql), params or {})
                return result.rowcount

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncConnection, None]:
        """
        Create transaction context manager.

        Yields:
            AsyncConnection for transaction

        Example:
            async with client.transaction() as conn:
                await client.execute("UPDATE ...", connection=conn)
                await client.execute("INSERT ...", connection=conn)
                # Commits on successful exit, rolls back on exception
        """
        async with self.engine.begin() as conn:
            try:
                log_event("database_transaction_begin", {})
                yield conn
                log_event("database_transaction_commit", {})
            except Exception as e:
                log_event("database_transaction_rollback", {
                    "error": str(e)
                })
                raise

    async def query_one(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single result.

        Args:
            sql: SQL query
            params: Query parameters

        Returns:
            Single result row or None
        """
        results = await self.query(sql, params, limit=1)
        return results[0] if results else None

    async def query_value(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute query and return single value.

        Args:
            sql: SQL query (should return single column)
            params: Query parameters

        Returns:
            Single value or None
        """
        row = await self.query_one(sql, params)
        if row:
            # Return first column value
            return next(iter(row.values()))
        return None

    async def query_paginated(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Execute paginated query.

        Args:
            sql: SQL query
            params: Query parameters
            page: Page number (1-indexed)
            page_size: Results per page

        Returns:
            Dict with results, page info, and total count
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Get results for page
        results = await self.query(
            sql,
            params,
            limit=page_size,
            offset=offset
        )

        # Get total count (modify query to COUNT)
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as subquery"
        total = await self.query_value(count_sql, params) or 0

        total_pages = (total + page_size - 1) // page_size

        return {
            "results": results,
            "page": page,
            "page_size": page_size,
            "total_results": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    async def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful
        """
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            log_event("database_connection_test_failed", {
                "error": str(e)
            })
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.

        Returns:
            Dict with statistics
        """
        success_count = self.query_count - self.error_count
        success_rate = (
            success_count / self.query_count
            if self.query_count > 0
            else 0.0
        )

        return {
            "query_count": self.query_count,
            "error_count": self.error_count,
            "success_count": success_count,
            "success_rate": success_rate,
            "read_only": self.read_only,
            "db_type": self.db_type.value
        }

    async def close(self):
        """Close database connection pool"""
        await self.engine.dispose()

        log_event("database_client_closed", {
            "stats": self.get_stats()
        })

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
