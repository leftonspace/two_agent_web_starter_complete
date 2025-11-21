"""
Tests for direct executor.

PHASE 7B.2: Tests for direct execution mode with safety checks.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from agent.execution.direct_executor import DirectExecutor, DirectActionType


# ══════════════════════════════════════════════════════════════════════
# Successful Execution Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_direct_execution_success():
    """Test successful direct execution"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "search_info",
        "parameters": {
            "query": "What is Python?"
        },
        "expected_output": "Information about Python"
    })
    llm_mock.chat = AsyncMock(return_value="Python is a programming language")

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("What is Python?")

    assert result["success"] is True
    assert "result" in result
    assert result["result"]["result"] == "Python is a programming language"
    assert result["mode"] == "direct"


@pytest.mark.asyncio
async def test_search_info_execution():
    """Test search info action"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "search_info",
        "parameters": {"query": "Claude AI"}
    })
    llm_mock.chat = AsyncMock(return_value="Claude is an AI assistant")

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Search for Claude AI")

    assert result["success"] is True
    assert "Claude is an AI assistant" in result["result"]["result"]


@pytest.mark.asyncio
async def test_create_document_execution():
    """Test document creation action"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "create_document",
        "parameters": {
            "title": "Test Document",
            "type": "notes",
            "content": "Test content"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Create a test document")

    assert result["success"] is True
    assert result["result"]["title"] == "Test Document"
    assert result["result"]["created"] is True


@pytest.mark.asyncio
async def test_calculate_execution():
    """Test calculation action"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "calculate",
        "parameters": {"expression": "2 + 2"}
    })
    llm_mock.chat = AsyncMock(return_value="4")

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Calculate 2 + 2")

    assert result["success"] is True
    assert result["result"]["expression"] == "2 + 2"
    assert result["result"]["result"] == "4"


# ══════════════════════════════════════════════════════════════════════
# Safety Check Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_unsafe_query_blocked_delete():
    """Test unsafe database DELETE query is blocked"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "query_database",
        "parameters": {
            "query": "DELETE FROM users WHERE id = 1"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Delete user 1")

    assert result["success"] is False
    assert "not allowed" in result["error"]


@pytest.mark.asyncio
async def test_unsafe_query_blocked_update():
    """Test unsafe database UPDATE query is blocked"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "query_database",
        "parameters": {
            "query": "UPDATE users SET role='admin' WHERE id=1"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Update user role")

    assert result["success"] is False
    assert "not allowed" in result["error"]


@pytest.mark.asyncio
async def test_unsafe_query_blocked_drop():
    """Test unsafe database DROP query is blocked"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "query_database",
        "parameters": {
            "query": "DROP TABLE users"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Drop users table")

    assert result["success"] is False


@pytest.mark.asyncio
async def test_safe_query_allowed():
    """Test safe database SELECT query is allowed"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "query_database",
        "parameters": {
            "query": "SELECT * FROM users WHERE id = 1"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Get user 1")

    assert result["success"] is True
    assert result["result"]["query"] == "SELECT * FROM users WHERE id = 1"


@pytest.mark.asyncio
async def test_unsafe_api_method_blocked_post():
    """Test POST API method is blocked"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "api_call",
        "parameters": {
            "url": "https://api.example.com/data",
            "method": "POST"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Post data to API")

    assert result["success"] is False
    assert "not allowed" in result["error"]


@pytest.mark.asyncio
async def test_unsafe_api_method_blocked_put():
    """Test PUT API method is blocked"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "api_call",
        "parameters": {
            "url": "https://api.example.com/data",
            "method": "PUT"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Update data via API")

    assert result["success"] is False


@pytest.mark.asyncio
async def test_safe_api_method_allowed_get():
    """Test GET API method is allowed"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "api_call",
        "parameters": {
            "url": "https://api.example.com/data",
            "method": "GET"
        }
    })

    executor = DirectExecutor(llm_mock)

    # Mock httpx to avoid actual network call
    with patch('agent.execution.direct_executor.httpx') as mock_httpx:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "test data"
        mock_response.headers = {"content-type": "text/plain"}

        mock_client = Mock()
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_httpx.AsyncClient.return_value.__aenter__.return_value = mock_client

        result = await executor.execute("Get data from API")

        assert result["success"] is True


@pytest.mark.asyncio
async def test_system_file_access_blocked():
    """Test access to system files is blocked"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "file_read",
        "parameters": {
            "path": "/etc/passwd"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Read /etc/passwd")

    assert result["success"] is False
    assert "system files" in result["error"].lower()


# ══════════════════════════════════════════════════════════════════════
# Timeout and Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_execution_timeout():
    """Test execution timeout protection"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "search_info",
        "parameters": {"query": "test"}
    })

    # Simulate slow execution
    async def slow_chat(*args, **kwargs):
        await asyncio.sleep(5)  # Exceeds test timeout
        return "result"

    llm_mock.chat = slow_chat

    executor = DirectExecutor(llm_mock)
    executor.max_execution_time = 1  # 1 second for test

    result = await executor.execute("Slow task")

    assert result["success"] is False
    assert "timeout" in result["error"].lower()


@pytest.mark.asyncio
async def test_unsupported_action():
    """Test unsupported action type"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "unsupported",
        "reason": "Task requires deployment"
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Deploy to production")

    assert result["success"] is False
    assert "not allowed" in result["error"]


@pytest.mark.asyncio
async def test_action_planning_failure():
    """Test handling of action planning failure"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(side_effect=Exception("LLM error"))

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Some task")

    assert result["success"] is False
    assert "not allowed" in result["error"]


@pytest.mark.asyncio
async def test_execution_error_handling():
    """Test handling of execution errors"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_type": "file_read",
        "parameters": {
            "path": "/nonexistent/file.txt"
        }
    })

    executor = DirectExecutor(llm_mock)
    result = await executor.execute("Read nonexistent file")

    assert result["success"] is False
    assert "error" in result


# ══════════════════════════════════════════════════════════════════════
# Result Validation Tests
# ══════════════════════════════════════════════════════════════════════


def test_validate_result_success():
    """Test result validation with valid result"""
    executor = DirectExecutor(Mock())

    # Valid dict result
    assert executor._validate_result({"data": "test"}) is True

    # Valid string result
    assert executor._validate_result("result") is True


def test_validate_result_failure():
    """Test result validation with invalid result"""
    executor = DirectExecutor(Mock())

    # None result
    assert executor._validate_result(None) is False

    # Result with error
    assert executor._validate_result({"error": "Something failed"}) is False


# ══════════════════════════════════════════════════════════════════════
# Safety Check Unit Tests
# ══════════════════════════════════════════════════════════════════════


def test_is_safe_action_query_checks():
    """Test safety checks for database queries"""
    executor = DirectExecutor(Mock())

    # Safe SELECT
    plan = {
        "action_type": "query_database",
        "parameters": {"query": "SELECT * FROM users"}
    }
    assert executor._is_safe_action(plan) is True

    # Unsafe DELETE
    plan = {
        "action_type": "query_database",
        "parameters": {"query": "DELETE FROM users"}
    }
    assert executor._is_safe_action(plan) is False

    # Unsafe INSERT
    plan = {
        "action_type": "query_database",
        "parameters": {"query": "INSERT INTO users VALUES (1)"}
    }
    assert executor._is_safe_action(plan) is False


def test_is_safe_action_api_checks():
    """Test safety checks for API calls"""
    executor = DirectExecutor(Mock())

    # Safe GET
    plan = {
        "action_type": "api_call",
        "parameters": {"method": "GET"}
    }
    assert executor._is_safe_action(plan) is True

    # Safe HEAD
    plan = {
        "action_type": "api_call",
        "parameters": {"method": "HEAD"}
    }
    assert executor._is_safe_action(plan) is True

    # Unsafe POST
    plan = {
        "action_type": "api_call",
        "parameters": {"method": "POST"}
    }
    assert executor._is_safe_action(plan) is False

    # Unsafe DELETE
    plan = {
        "action_type": "api_call",
        "parameters": {"method": "DELETE"}
    }
    assert executor._is_safe_action(plan) is False


def test_is_safe_action_invalid_type():
    """Test safety check with invalid action type"""
    executor = DirectExecutor(Mock())

    # Invalid action type
    plan = {
        "action_type": "invalid_action",
        "parameters": {}
    }
    assert executor._is_safe_action(plan) is False

    # Unsupported action
    plan = {
        "action_type": "unsupported",
        "reason": "Too complex"
    }
    assert executor._is_safe_action(plan) is False
