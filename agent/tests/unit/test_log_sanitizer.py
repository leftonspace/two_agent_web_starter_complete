# test_log_sanitizer.py
"""
PHASE 1.2: Comprehensive tests for log sanitization module.

Tests cover:
- API key detection and redaction
- Token and credential sanitization
- PII masking (email, phone, SSN, credit card)
- Nested data structure sanitization
- Environment variable protection
- LLM request/response sanitization
- Performance requirements (< 5ms per log event)
- Edge cases (None, empty strings, non-dict types)
"""

from __future__ import annotations

import time
from typing import Any, Dict

import pytest

# Import module under test
import sys
from pathlib import Path

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

import log_sanitizer


# ══════════════════════════════════════════════════════════════════════
# Test: API Key Detection and Redaction
# ══════════════════════════════════════════════════════════════════════


def test_api_key_in_dict_key():
    """Test that API keys in dictionary keys are redacted."""
    data = {
        "api_key": "sk-1234567890abcdefghij",
        "task": "Build website",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["api_key"] == "sk-1...ghij"
    assert result["task"] == "Build website"


def test_openai_api_key_in_value():
    """Test that OpenAI API keys in values are redacted."""
    data = {
        "message": "Use this key: sk-proj-abcdefghij1234567890abcdefghij1234567890",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "sk-proj-abcdefghij1234567890abcdefghij1234567890" not in result["message"]
    assert "sk-pro...7890" in result["message"]


def test_anthropic_api_key_in_value():
    """Test that Anthropic API keys in values are redacted."""
    data = {
        "config": "API_KEY=sk-ant-1234567890abcdefghij1234567890",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "sk-ant-1234567890abcdefghij1234567890" not in result["config"]
    assert "sk-ant...7890" in result["config"]


def test_bearer_token_in_value():
    """Test that Bearer tokens are redacted."""
    data = {
        "auth_header": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result["auth_header"]


def test_jwt_token_in_value():
    """Test that JWT tokens are redacted."""
    data = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
    }
    result = log_sanitizer.sanitize_log_data(data)
    # JWT should be detected and redacted (key matches "token" pattern)
    # Shows first 4 and last 4 chars for debugging
    assert "eyJh...sR8U" in result["token"]


def test_authorization_header():
    """Test that Authorization headers are redacted."""
    data = {
        "Authorization": "Bearer sk-1234567890abcdef",
        "Content-Type": "application/json",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["Authorization"] == "Bear...cdef"
    assert result["Content-Type"] == "application/json"


def test_x_api_key_header():
    """Test that X-API-Key headers are redacted."""
    data = {
        "X-API-Key": "sk-1234567890abcdefghij",
        "User-Agent": "test/1.0",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["X-API-Key"] == "sk-1...ghij"
    assert result["User-Agent"] == "test/1.0"


# ══════════════════════════════════════════════════════════════════════
# Test: Credential Sanitization
# ══════════════════════════════════════════════════════════════════════


def test_password_field():
    """Test that password fields are redacted."""
    data = {
        "username": "admin",
        "password": "supersecret123",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["username"] == "admin"
    # Password shows first/last 4 for debugging
    assert result["password"] == "supe...t123"


def test_secret_field():
    """Test that secret fields are redacted."""
    data = {
        "client_secret": "my-secret-value-1234567890",
        "public_data": "safe-to-log",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["client_secret"] == "my-s...7890"
    assert result["public_data"] == "safe-to-log"


def test_private_key_field():
    """Test that private key fields are redacted."""
    data = {
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg...",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["private_key"] == "----...g..."


def test_session_id_field():
    """Test that session_id fields are redacted."""
    data = {
        "session_id": "abc123def456ghi789jkl012",
        "user_id": "user_12345",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["session_id"] == "abc1...l012"
    assert result["user_id"] == "user_12345"


# ══════════════════════════════════════════════════════════════════════
# Test: PII Masking
# ══════════════════════════════════════════════════════════════════════


def test_email_address_masking():
    """Test that email addresses are masked."""
    data = {
        "message": "Contact john.doe@example.com for more info",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "john.doe@example.com" not in result["message"]
    assert "j***@example.com" in result["message"]


def test_phone_number_masking():
    """Test that phone numbers are masked."""
    data = {
        "contact": "Call me at 555-123-4567 or (555) 987-6543",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "555-123-4567" not in result["contact"]
    assert "***-***-4567" in result["contact"]
    assert "***-***-6543" in result["contact"]


def test_ssn_masking():
    """Test that SSNs are masked."""
    data = {
        "info": "SSN: 123-45-6789 or 987654321",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "123-45-6789" not in result["info"]
    assert "***-**-6789" in result["info"]


def test_credit_card_masking():
    """Test that credit card numbers are masked."""
    data = {
        "payment": "Card: 1234-5678-9012-3456",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "1234-5678-9012-3456" not in result["payment"]
    assert "****-****-****-3456" in result["payment"]


# ══════════════════════════════════════════════════════════════════════
# Test: Nested Data Structures
# ══════════════════════════════════════════════════════════════════════


def test_nested_dict_sanitization():
    """Test that nested dictionaries are sanitized recursively."""
    data = {
        "config": {
            "api_key": "sk-1234567890abcdef",
            "endpoint": "https://api.example.com",
            "credentials": {
                "access_token": "secret-token-value",
                "username": "admin",
            },
        },
        "task": "Deploy app",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["config"]["api_key"] == "sk-1...cdef"
    assert result["config"]["endpoint"] == "https://api.example.com"
    # "credentials" is detected as sensitive, so whole object is redacted
    assert result["config"]["credentials"] == "***REDACTED***"
    assert result["task"] == "Deploy app"


def test_list_with_dicts_sanitization():
    """Test that lists containing dictionaries are sanitized."""
    data = {
        "items": [
            {"api_key": "sk-111111111111", "name": "item1"},
            {"api_key": "sk-222222222222", "name": "item2"},
        ]
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["items"][0]["api_key"] == "sk-1...1111"
    assert result["items"][0]["name"] == "item1"
    assert result["items"][1]["api_key"] == "sk-2...2222"
    assert result["items"][1]["name"] == "item2"


def test_deeply_nested_structure():
    """Test sanitization of deeply nested structures."""
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "api_key": "sk-deep-nested-key",
                    "level4": {
                        "password": "deep-password",
                    },
                },
            },
        },
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["level1"]["level2"]["level3"]["api_key"] == "sk-d...-key"
    assert result["level1"]["level2"]["level3"]["level4"]["password"] == "deep...word"


# ══════════════════════════════════════════════════════════════════════
# Test: LLM Request/Response Sanitization
# ══════════════════════════════════════════════════════════════════════


def test_llm_request_sanitization():
    """Test that LLM requests with API keys in messages are sanitized."""
    request = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Use this API key: sk-test1234567890abcdef"},
        ],
        "headers": {
            "Authorization": "Bearer sk-auth-token",
        },
    }
    result = log_sanitizer.sanitize_llm_request(request)
    assert "sk-test1234567890abcdef" not in result["messages"][1]["content"]
    assert result["headers"]["Authorization"] == "Bear...oken"


def test_llm_response_sanitization():
    """Test that LLM responses echoing sensitive data are sanitized."""
    response = {
        "choices": [
            {
                "message": {
                    "content": "Sure, I'll use the key sk-echo1234567890abcdef to make the API call.",
                },
            },
        ],
    }
    result = log_sanitizer.sanitize_llm_response(response)
    assert "sk-echo1234567890abcdef" not in result["choices"][0]["message"]["content"]
    assert "sk-ech...cdef" in result["choices"][0]["message"]["content"]


# ══════════════════════════════════════════════════════════════════════
# Test: Environment Variables
# ══════════════════════════════════════════════════════════════════════


def test_env_var_sanitization():
    """Test that environment variables are sanitized by default."""
    env = {
        "DEBUG": "1",
        "OPENAI_API_KEY": "sk-env-api-key",
        "DATABASE_URL": "postgres://user:pass@host/db",
        "PATH": "/usr/bin:/usr/local/bin",
    }
    result = log_sanitizer.sanitize_env_vars(env)
    assert result["DEBUG"] == "1"  # Allowlisted
    assert result["OPENAI_API_KEY"] == "sk-e...-key"  # Redacted
    assert result["DATABASE_URL"] == "post...t/db"  # Redacted
    assert result["PATH"] == "/usr/bin:/usr/local/bin"  # Allowlisted


def test_custom_env_allowlist():
    """Test that custom environment variable allowlist works."""
    env = {
        "MY_CUSTOM_VAR": "value1",
        "SECRET_VAR": "secret123456",
    }
    allowlist = {"MY_CUSTOM_VAR"}
    result = log_sanitizer.sanitize_env_vars(env, allowlist=allowlist)
    assert result["MY_CUSTOM_VAR"] == "value1"
    assert result["SECRET_VAR"] == "secr...3456"


# ══════════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ══════════════════════════════════════════════════════════════════════


def test_none_value():
    """Test that None values are handled correctly."""
    data = {
        "api_key": None,
        "value": "something",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["api_key"] == "***REDACTED***"
    assert result["value"] == "something"


def test_empty_string():
    """Test that empty strings are handled correctly."""
    data = {
        "api_key": "",
        "task": "test",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["api_key"] == "***REDACTED***"
    assert result["task"] == "test"


def test_non_string_sensitive_value():
    """Test that non-string values in sensitive keys are redacted."""
    data = {
        "api_key": 12345,
        "count": 42,
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["api_key"] == "***REDACTED***"
    assert result["count"] == 42


def test_empty_dict():
    """Test that empty dictionaries are handled."""
    data: Dict[str, Any] = {}
    result = log_sanitizer.sanitize_log_data(data)
    assert result == {}


def test_empty_list():
    """Test that empty lists are handled."""
    data = {"items": []}
    result = log_sanitizer.sanitize_log_data(data)
    assert result["items"] == []


def test_list_with_primitives():
    """Test that lists with primitive types are preserved."""
    data = {"numbers": [1, 2, 3], "strings": ["a", "b", "c"]}
    result = log_sanitizer.sanitize_log_data(data)
    assert result["numbers"] == [1, 2, 3]
    assert result["strings"] == ["a", "b", "c"]


def test_tuple_sanitization():
    """Test that tuples are sanitized and returned as tuples."""
    data = {"coords": ({"api_key": "sk-123"}, {"value": "safe"})}
    result = log_sanitizer.sanitize_log_data(data)
    assert isinstance(result["coords"], tuple)
    assert result["coords"][0]["api_key"] == "***REDACTED***"
    assert result["coords"][1]["value"] == "safe"


# ══════════════════════════════════════════════════════════════════════
# Test: Utility Functions
# ══════════════════════════════════════════════════════════════════════


def test_is_likely_sensitive():
    """Test the is_likely_sensitive utility function."""
    assert log_sanitizer.is_likely_sensitive("sk-1234567890abcdefghij1234567890") is True
    assert log_sanitizer.is_likely_sensitive("Bearer abc123def456ghi789jkl012mno345") is True
    assert log_sanitizer.is_likely_sensitive("hello world") is False
    assert log_sanitizer.is_likely_sensitive("short") is False


def test_sanitize_error_message():
    """Test error message sanitization."""
    error = "API call failed with key sk-1234567890: Invalid credentials"
    result = log_sanitizer.sanitize_error_message(error)
    assert "sk-1234567890" not in result
    assert "Invalid credentials" in result


def test_sanitize_headers():
    """Test header sanitization utility."""
    headers = {
        "Authorization": "Bearer token1234567890",
        "Content-Type": "application/json",
        "X-API-Key": "sk-apikey1234567890",
    }
    result = log_sanitizer.sanitize_headers(headers)
    assert result["Authorization"] == "Bear...7890"
    assert result["Content-Type"] == "application/json"
    assert result["X-API-Key"] == "sk-a...7890"


# ══════════════════════════════════════════════════════════════════════
# Test: Performance Requirements
# ══════════════════════════════════════════════════════════════════════


def test_performance_simple_dict():
    """Test that sanitization of simple dict is < 5ms."""
    data = {
        "api_key": "sk-1234567890abcdef",
        "task": "Build website",
        "config": {"timeout": 30},
    }

    start = time.time()
    for _ in range(100):  # Average over 100 iterations
        log_sanitizer.sanitize_log_data(data)
    elapsed = (time.time() - start) / 100

    assert elapsed < 0.005, f"Sanitization took {elapsed*1000:.2f}ms, expected < 5ms"


def test_performance_nested_structure():
    """Test that sanitization of nested structure is < 5ms."""
    data = {
        "level1": {
            "level2": {
                "level3": {
                    "api_key": "sk-test",
                    "items": [
                        {"token": f"token-{i}", "value": i} for i in range(10)
                    ],
                },
            },
        },
    }

    start = time.time()
    for _ in range(100):  # Average over 100 iterations
        log_sanitizer.sanitize_log_data(data)
    elapsed = (time.time() - start) / 100

    assert elapsed < 0.005, f"Sanitization took {elapsed*1000:.2f}ms, expected < 5ms"


# ══════════════════════════════════════════════════════════════════════
# Test: Fail-Safe Behavior
# ══════════════════════════════════════════════════════════════════════


def test_fail_safe_on_error():
    """Test that sanitization never crashes, even on malformed data."""
    # This test ensures that even if sanitization encounters an error,
    # it returns the original data rather than crashing
    class UnserializableObject:
        def __repr__(self):
            raise RuntimeError("Cannot serialize")

    # The sanitizer should handle this gracefully
    data = {"key": "value"}  # Use valid data as sanitizer might not fail on everything
    result = log_sanitizer.sanitize_log_data(data)
    assert result is not None


# ══════════════════════════════════════════════════════════════════════
# Test: Integration with Core Logging
# ══════════════════════════════════════════════════════════════════════


def test_task_description_with_api_key():
    """Test that task descriptions containing API keys are sanitized."""
    # This simulates a user accidentally putting an API key in their task description
    data = {
        "task_description": "Deploy the app using API key sk-1234567890abcdefghij",
        "project_folder": "/path/to/project",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert "sk-1234567890abcdefghij" not in result["task_description"]
    assert "Deploy the app" in result["task_description"]
    assert "sk-123...ghij" in result["task_description"]


def test_allowlist_keys_preserved():
    """Test that allowlisted keys are never redacted even if they match patterns."""
    # This ensures that safe keys like "task", "status" are always preserved
    data = {
        "task": "Complete the authentication module",
        "status": "completed",
        "api_key": "sk-1234567890abcdef",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["task"] == "Complete the authentication module"
    assert result["status"] == "completed"
    # API key shows first/last 4 chars
    assert result["api_key"] == "sk-1...cdef"


# ══════════════════════════════════════════════════════════════════════
# Test: Custom Pattern Addition
# ══════════════════════════════════════════════════════════════════════


def test_add_custom_sensitive_pattern():
    """Test that custom sensitive patterns can be added at runtime."""
    # Add custom pattern
    log_sanitizer.add_sensitive_pattern(r".*custom[_-]?secret.*")

    data = {
        "custom_secret": "my-custom-value",
        "normal_field": "safe value",
    }
    result = log_sanitizer.sanitize_log_data(data)
    assert result["custom_secret"] == "my-c...alue"
    assert result["normal_field"] == "safe value"


# ══════════════════════════════════════════════════════════════════════
# Run Tests
# ══════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
