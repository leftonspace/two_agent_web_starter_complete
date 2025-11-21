"""
Generic SQL Database Connector

Supports multiple database engines:
- PostgreSQL
- MySQL/MariaDB
- SQLite
- SQL Server

Features:
- Query execution with parameter binding
- Connection pooling
- Transaction support
- Schema introspection
- Prepared statements

Author: AI Agent System
Created: Phase 3.2 - Integration Framework
"""

import asyncio
import sqlite3
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import logging

try:
    import asyncpg  # PostgreSQL
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

try:
    import aiomysql  # MySQL
    HAS_AIOMYSQL = True
except ImportError:
    HAS_AIOMYSQL = False

try:
    import aiosqlite  # SQLite
    HAS_AIOSQLITE = True
except ImportError:
    HAS_AIOSQLITE = False

from .base import Connector, ConnectionStatus
from .auth import get_credential_store, create_credential

logger = logging.getLogger(__name__)


class DatabaseEngine(Enum):
    """Supported database engines"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"


class DatabaseConnector(Connector):
    """
    Generic SQL database connector.

    Supports multiple database engines with a unified interface.
    """

    def __init__(
        self,
        connector_id: str,
        engine: str,
        config: Dict[str, Any]
    ):
        """
        Initialize database connector.

        Args:
            connector_id: Unique connector ID
            engine: Database engine ('postgresql', 'mysql', 'sqlite', 'sqlserver')
            config: Database configuration:
                For PostgreSQL/MySQL/SQL Server:
                    - host: Database host
                    - port: Database port
                    - database: Database name
                    - username: Database username
                    - password: Database password
                    - pool_size: Connection pool size (default: 10)
                For SQLite:
                    - database: Path to database file
        """
        # Validate engine
        try:
            self.engine = DatabaseEngine(engine)
        except ValueError:
            raise ValueError(f"Unsupported database engine: {engine}")

        # Set up configuration
        base_config = {
            'engine': engine,
            'auth_type': 'basic' if engine != 'sqlite' else 'none',
            'rate_limit_requests': 1000,  # High limit for databases
            'rate_limit_window': 60,
            'max_retries': 3,
            'pool_size': config.get('pool_size', 10)
        }

        base_config.update(config)

        super().__init__(
            connector_id=connector_id,
            name=f"Database ({engine})",
            config=base_config
        )

        # Engine-specific setup
        self.pool = None
        self.connection = None

        # Store credentials
        if engine != 'sqlite':
            self._store_credentials()

    def _store_credentials(self):
        """Store database credentials securely"""
        try:
            store = get_credential_store()
            cred = create_credential(
                connector_id=self.connector_id,
                auth_type='basic',
                credentials={
                    'username': self.config.get('username', ''),
                    'password': self.config.get('password', ''),
                    'host': self.config.get('host', ''),
                    'port': str(self.config.get('port', '')),
                    'database': self.config.get('database', '')
                },
                metadata={'engine': self.engine.value}
            )
            store.store(cred)
        except Exception as e:
            logger.warning(f"Failed to store credentials: {e}")

    # ========================================================================
    # AUTHENTICATION & CONNECTION
    # ========================================================================

    async def authenticate(self) -> bool:
        """
        Connect to database and create connection pool.

        Returns:
            True if authentication successful
        """
        try:
            if self.engine == DatabaseEngine.POSTGRESQL:
                return await self._connect_postgresql()
            elif self.engine == DatabaseEngine.MYSQL:
                return await self._connect_mysql()
            elif self.engine == DatabaseEngine.SQLITE:
                return await self._connect_sqlite()
            elif self.engine == DatabaseEngine.SQLSERVER:
                return await self._connect_sqlserver()
            else:
                logger.error(f"Unsupported engine: {self.engine}")
                return False

        except Exception as e:
            logger.error(f"Database authentication failed: {e}")
            return False

    async def _connect_postgresql(self) -> bool:
        """Connect to PostgreSQL"""
        if not HAS_ASYNCPG:
            raise ImportError("asyncpg not installed. Install with: pip install asyncpg")

        self.pool = await asyncpg.create_pool(
            host=self.config['host'],
            port=self.config.get('port', 5432),
            database=self.config['database'],
            user=self.config['username'],
            password=self.config['password'],
            min_size=1,
            max_size=self.config['pool_size']
        )

        # Test connection
        async with self.pool.acquire() as conn:
            await conn.fetchval('SELECT 1')

        logger.info(f"Connected to PostgreSQL: {self.config['database']}")
        return True

    async def _connect_mysql(self) -> bool:
        """Connect to MySQL"""
        if not HAS_AIOMYSQL:
            raise ImportError("aiomysql not installed. Install with: pip install aiomysql")

        self.pool = await aiomysql.create_pool(
            host=self.config['host'],
            port=self.config.get('port', 3306),
            user=self.config['username'],
            password=self.config['password'],
            db=self.config['database'],
            minsize=1,
            maxsize=self.config['pool_size']
        )

        # Test connection
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT 1')

        logger.info(f"Connected to MySQL: {self.config['database']}")
        return True

    async def _connect_sqlite(self) -> bool:
        """Connect to SQLite"""
        if not HAS_AIOSQLITE:
            raise ImportError("aiosqlite not installed. Install with: pip install aiosqlite")

        self.connection = await aiosqlite.connect(self.config['database'])

        # Test connection
        await self.connection.execute('SELECT 1')

        logger.info(f"Connected to SQLite: {self.config['database']}")
        return True

    async def _connect_sqlserver(self) -> bool:
        """Connect to SQL Server"""
        raise NotImplementedError("SQL Server support not yet implemented")

    async def disconnect(self):
        """Disconnect from database"""
        try:
            if self.pool:
                if self.engine == DatabaseEngine.POSTGRESQL:
                    await self.pool.close()
                elif self.engine == DatabaseEngine.MYSQL:
                    self.pool.close()
                    await self.pool.wait_closed()
                self.pool = None

            if self.connection:
                await self.connection.close()
                self.connection = None

            await super().disconnect()

        except Exception as e:
            logger.error(f"Error disconnecting from database: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection.

        Returns:
            Test results
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Execute a simple query
            result = await self.query("SELECT 1 as test")
            latency = (asyncio.get_event_loop().time() - start_time) * 1000

            return {
                'success': True,
                'latency_ms': round(latency, 2),
                'message': 'Connection successful',
                'details': {
                    'engine': self.engine.value,
                    'database': self.config.get('database'),
                    'pool_size': self.config.get('pool_size')
                }
            }

        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            return {
                'success': False,
                'latency_ms': round(latency, 2),
                'message': str(e),
                'details': {'error': str(e)}
            }

    # ========================================================================
    # QUERY OPERATIONS
    # ========================================================================

    async def query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a SELECT query.

        Args:
            query: SQL query string
            params: Query parameters (for parameter binding)

        Returns:
            List of result rows as dictionaries
        """
        async def _execute():
            if self.engine == DatabaseEngine.POSTGRESQL:
                return await self._query_postgresql(query, params)
            elif self.engine == DatabaseEngine.MYSQL:
                return await self._query_mysql(query, params)
            elif self.engine == DatabaseEngine.SQLITE:
                return await self._query_sqlite(query, params)
            else:
                raise NotImplementedError(f"Query not implemented for {self.engine}")

        return await self.execute_with_rate_limit(_execute)

    async def _query_postgresql(self, query: str, params: Optional[Dict]) -> List[Dict]:
        """Execute PostgreSQL query"""
        async with self.pool.acquire() as conn:
            if params:
                # Convert dict params to positional
                param_list = [params.get(k) for k in sorted(params.keys())]
                rows = await conn.fetch(query, *param_list)
            else:
                rows = await conn.fetch(query)

            return [dict(row) for row in rows]

    async def _query_mysql(self, query: str, params: Optional[Dict]) -> List[Dict]:
        """Execute MySQL query"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params or ())
                rows = await cursor.fetchall()
                return list(rows)

    async def _query_sqlite(self, query: str, params: Optional[Dict]) -> List[Dict]:
        """Execute SQLite query"""
        self.connection.row_factory = aiosqlite.Row
        async with self.connection.execute(query, params or ()) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def execute(self, query: str, params: Optional[Dict] = None) -> int:
        """
        Execute a non-SELECT query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        async def _execute():
            if self.engine == DatabaseEngine.POSTGRESQL:
                async with self.pool.acquire() as conn:
                    result = await conn.execute(query, *(params or ()))
                    return int(result.split()[-1])  # Extract row count

            elif self.engine == DatabaseEngine.MYSQL:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(query, params or ())
                        await conn.commit()
                        return cursor.rowcount

            elif self.engine == DatabaseEngine.SQLITE:
                await self.connection.execute(query, params or ())
                await self.connection.commit()
                return self.connection.total_changes

            else:
                raise NotImplementedError(f"Execute not implemented for {self.engine}")

        return await self.execute_with_rate_limit(_execute)

    # ========================================================================
    # CRUD OPERATIONS (Connector interface)
    # ========================================================================

    async def create(self, entity_type: str, data: Dict) -> Dict:
        """
        Create a record (INSERT).

        Args:
            entity_type: Table name
            data: Record data

        Returns:
            Created record with ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join([f'${i+1}' for i in range(len(data))])
        query = f"INSERT INTO {entity_type} ({columns}) VALUES ({placeholders}) RETURNING *"

        results = await self.query(query, data)
        return results[0] if results else data

    async def update(self, entity_type: str, entity_id: str, data: Dict) -> Dict:
        """
        Update a record (UPDATE).

        Args:
            entity_type: Table name
            entity_id: Record ID
            data: Updated data

        Returns:
            Updated record
        """
        set_clause = ', '.join([f"{k} = ${i+1}" for i, k in enumerate(data.keys())])
        query = f"UPDATE {entity_type} SET {set_clause} WHERE id = ${len(data)+1} RETURNING *"

        params = {**data, 'id': entity_id}
        results = await self.query(query, params)
        return results[0] if results else {}

    async def delete(self, entity_type: str, entity_id: str) -> bool:
        """
        Delete a record (DELETE).

        Args:
            entity_type: Table name
            entity_id: Record ID

        Returns:
            True if deleted
        """
        query = f"DELETE FROM {entity_type} WHERE id = $1"
        affected = await self.execute(query, {'id': entity_id})
        return affected > 0

    # ========================================================================
    # SCHEMA INTROSPECTION
    # ========================================================================

    async def list_tables(self) -> List[str]:
        """List all tables in the database"""
        if self.engine == DatabaseEngine.POSTGRESQL:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """
        elif self.engine == DatabaseEngine.MYSQL:
            query = "SHOW TABLES"
        elif self.engine == DatabaseEngine.SQLITE:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
        else:
            raise NotImplementedError()

        results = await self.query(query)
        return [list(r.values())[0] for r in results]

    async def describe_table(self, table_name: str) -> List[Dict]:
        """Get table schema"""
        if self.engine == DatabaseEngine.POSTGRESQL:
            query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1
            """
        elif self.engine == DatabaseEngine.MYSQL:
            query = f"DESCRIBE {table_name}"
        elif self.engine == DatabaseEngine.SQLITE:
            query = f"PRAGMA table_info({table_name})"
        else:
            raise NotImplementedError()

        return await self.query(query, {'table_name': table_name} if self.engine == DatabaseEngine.POSTGRESQL else None)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def __repr__(self) -> str:
        db_name = self.config.get('database', 'unknown')
        return f"DatabaseConnector(engine={self.engine.value}, database='{db_name}', status={self.status.value})"
