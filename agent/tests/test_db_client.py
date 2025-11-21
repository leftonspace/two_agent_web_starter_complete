"""
Tests for database client.

PHASE 8.4: Tests for database operations with connection pooling,
read-only mode, and transaction management.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncConnection

from agent.actions.db_client import DatabaseClient, DatabaseType


# ══════════════════════════════════════════════════════════════════════
# Database Type Detection Tests
# ══════════════════════════════════════════════════════════════════════


def test_detect_postgresql():
    """Test PostgreSQL detection"""
    client = DatabaseClient(
        "postgresql+asyncpg://user:pass@localhost/db",
        read_only=True
    )
    assert client.db_type == DatabaseType.POSTGRESQL


def test_detect_mysql():
    """Test MySQL detection"""
    client = DatabaseClient(
        "mysql+aiomysql://user:pass@localhost/db",
        read_only=True
    )
    assert client.db_type == DatabaseType.MYSQL


def test_detect_sqlite():
    """Test SQLite detection"""
    client = DatabaseClient(
        "sqlite+aiosqlite:///./test.db",
        read_only=True
    )
    assert client.db_type == DatabaseType.SQLITE


def test_unsupported_database():
    """Test unsupported database type raises error"""
    with pytest.raises(ValueError, match="Unsupported database type"):
        DatabaseClient("mongodb://localhost/db")


# ══════════════════════════════════════════════════════════════════════
# Read-Only Query Validation Tests
# ══════════════════════════════════════════════════════════════════════


def test_is_read_only_select():
    """Test SELECT query is read-only"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    assert client._is_read_only_query("SELECT * FROM users") is True


def test_is_read_only_with():
    """Test WITH query is read-only"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    sql = "WITH temp AS (SELECT * FROM users) SELECT * FROM temp"
    assert client._is_read_only_query(sql) is True


def test_is_not_read_only_insert():
    """Test INSERT is not read-only"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    assert client._is_read_only_query("INSERT INTO users VALUES (1)") is False


def test_is_not_read_only_update():
    """Test UPDATE is not read-only"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    assert client._is_read_only_query("UPDATE users SET name='test'") is False


def test_is_not_read_only_delete():
    """Test DELETE is not read-only"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    assert client._is_read_only_query("DELETE FROM users") is False


def test_read_only_with_comments():
    """Test read-only detection ignores comments"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    sql = """
    -- This is a comment
    /* Multi-line
       comment */
    SELECT * FROM users
    """
    assert client._is_read_only_query(sql) is True


# ══════════════════════════════════════════════════════════════════════
# Query Validation Tests
# ══════════════════════════════════════════════════════════════════════


def test_validate_empty_query():
    """Test empty query raises error"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")
    with pytest.raises(ValueError, match="Empty SQL query"):
        client._validate_query("")


def test_validate_read_only_mode_blocks_write():
    """Test read-only mode blocks write operations"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db", read_only=True)
    with pytest.raises(ValueError, match="Write operations not allowed"):
        client._validate_query("INSERT INTO users VALUES (1)")


def test_validate_read_only_mode_allows_select():
    """Test read-only mode allows SELECT"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db", read_only=True)
    # Should not raise
    client._validate_query("SELECT * FROM users")


def test_validate_write_mode_allows_insert():
    """Test write mode allows INSERT"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db", read_only=False)
    # Should not raise
    client._validate_query("INSERT INTO users VALUES (1)")


# ══════════════════════════════════════════════════════════════════════
# Query Execution Tests (Mocked)
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_query_basic():
    """Test basic query execution"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    # Mock the engine and connection
    mock_result = Mock()
    mock_row1 = Mock()
    mock_row1._mapping = {"id": 1, "name": "Alice"}
    mock_row2 = Mock()
    mock_row2._mapping = {"id": 2, "name": "Bob"}
    mock_result.fetchall.return_value = [mock_row1, mock_row2]

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    # Patch the engine.begin context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        results = await client.query("SELECT * FROM users")

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
        assert client.query_count == 1


@pytest.mark.asyncio
async def test_query_with_params():
    """Test query with parameter binding"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    mock_result = Mock()
    mock_row = Mock()
    mock_row._mapping = {"id": 1, "name": "Alice"}
    mock_result.fetchall.return_value = [mock_row]

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        results = await client.query(
            "SELECT * FROM users WHERE id = :id",
            params={"id": 1}
        )

        assert len(results) == 1
        assert results[0]["id"] == 1


@pytest.mark.asyncio
async def test_query_with_limit():
    """Test query with LIMIT"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    mock_result = Mock()
    mock_row = Mock()
    mock_row._mapping = {"id": 1, "name": "Alice"}
    mock_result.fetchall.return_value = [mock_row]

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        results = await client.query("SELECT * FROM users", limit=10)

        # Verify LIMIT was added to query
        call_args = mock_conn.execute.call_args
        assert "LIMIT" in str(call_args)


@pytest.mark.asyncio
async def test_query_with_offset():
    """Test query with OFFSET"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    mock_result = Mock()
    mock_result.fetchall.return_value = []

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        await client.query("SELECT * FROM users", limit=10, offset=20)

        # Verify OFFSET was added
        call_args = mock_conn.execute.call_args
        assert "OFFSET" in str(call_args)


@pytest.mark.asyncio
async def test_query_one():
    """Test query_one returns single result"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    mock_result = Mock()
    mock_row = Mock()
    mock_row._mapping = {"id": 1, "name": "Alice"}
    mock_result.fetchall.return_value = [mock_row]

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        result = await client.query_one("SELECT * FROM users WHERE id = 1")

        assert result is not None
        assert result["id"] == 1


@pytest.mark.asyncio
async def test_query_value():
    """Test query_value returns single value"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    mock_result = Mock()
    mock_row = Mock()
    mock_row._mapping = {"count": 42}
    mock_result.fetchall.return_value = [mock_row]

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        value = await client.query_value("SELECT COUNT(*) as count FROM users")

        assert value == 42


# ══════════════════════════════════════════════════════════════════════
# Execute Statement Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_execute_in_write_mode():
    """Test execute in write mode"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db", read_only=False)

    mock_result = Mock()
    mock_result.rowcount = 1

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        rows_affected = await client.execute(
            "INSERT INTO users (name) VALUES (:name)",
            params={"name": "Charlie"}
        )

        assert rows_affected == 1


@pytest.mark.asyncio
async def test_execute_blocked_in_read_only():
    """Test execute blocked in read-only mode"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db", read_only=True)

    with pytest.raises(ValueError, match="Write operations not allowed"):
        await client.execute("INSERT INTO users VALUES (1)")


# ══════════════════════════════════════════════════════════════════════
# Transaction Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_transaction_context():
    """Test transaction context manager"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db", read_only=False)

    mock_result = Mock()
    mock_result.rowcount = 1

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        async with client.transaction() as conn:
            assert conn is not None
            # Transaction should commit on successful exit


# ══════════════════════════════════════════════════════════════════════
# Pagination Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_query_paginated():
    """Test paginated query"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    # Mock page results
    mock_page_result = Mock()
    mock_row1 = Mock()
    mock_row1._mapping = {"id": 1}
    mock_row2 = Mock()
    mock_row2._mapping = {"id": 2}
    mock_page_result.fetchall.return_value = [mock_row1, mock_row2]

    # Mock count result
    mock_count_result = Mock()
    mock_count_row = Mock()
    mock_count_row._mapping = {"total": 25}
    mock_count_result.fetchall.return_value = [mock_count_row]

    call_count = [0]

    async def mock_execute(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return mock_page_result
        else:
            return mock_count_result

    mock_conn = AsyncMock()
    mock_conn.execute = mock_execute

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        result = await client.query_paginated(
            "SELECT * FROM users",
            page=2,
            page_size=10
        )

        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["total_results"] == 25
        assert result["total_pages"] == 3
        assert result["has_next"] is True
        assert result["has_prev"] is True
        assert len(result["results"]) == 2


# ══════════════════════════════════════════════════════════════════════
# Statistics Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_stats():
    """Test statistics tracking"""
    client = DatabaseClient("sqlite+aiosqlite:///./test.db")

    mock_result = Mock()
    mock_result.fetchall.return_value = []

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=mock_result)

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_conn
    mock_context.__aexit__.return_value = None

    with patch.object(client.engine, 'begin', return_value=mock_context):
        await client.query("SELECT * FROM users")
        await client.query("SELECT * FROM posts")

        stats = client.get_stats()

        assert stats["query_count"] == 2
        assert stats["error_count"] == 0
        assert stats["success_count"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["read_only"] is True
        assert stats["db_type"] == "sqlite"


# ══════════════════════════════════════════════════════════════════════
# Context Manager Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager"""
    async with DatabaseClient("sqlite+aiosqlite:///./test.db") as client:
        assert client is not None
        assert client.engine is not None

    # Engine should be disposed after exit
