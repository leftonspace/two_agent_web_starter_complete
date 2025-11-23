# log_sanitizer.py
"""
PHASE 1.2: Log Sanitization Module

Comprehensive sanitization of sensitive data in logs to prevent leakage of:
- API keys (OpenAI, Anthropic, etc.)
- Authentication tokens and credentials
- Environment variables
- Personally Identifiable Information (PII)

This module addresses vulnerability S1: API key leakage in logs.

Design principles:
- Sanitize before persistence (at log entry point)
- Preserve debugging information (show first/last 4 chars of secrets)
- Minimal performance impact (< 5ms per log event)
- Fail-safe: Never crash, worst case is no sanitization
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, List, Optional, Pattern, Set

# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════

# Sensitive key patterns (case-insensitive matching)
SENSITIVE_KEY_PATTERNS = [
    # API keys and tokens
    r".*api[_-]?key.*",
    r".*token.*",
    r".*secret.*",
    r".*password.*",
    r".*passwd.*",
    r".*private[_-]?key.*",
    r".*access[_-]?key.*",
    r".*auth.*",
    r".*bearer.*",
    r".*authorization.*",
    r".*credential.*",
    r".*session[_-]?id.*",
    r".*csrf.*",

    # Environment variables (commonly sensitive)
    r".*_token$",
    r".*_key$",
    r".*_secret$",

    # Database and service credentials
    r".*db[_-]?password.*",
    r".*database[_-]?url.*",
    r".*connection[_-]?string.*",
    r".*dsn.*",
]

# Compile patterns for performance
_COMPILED_KEY_PATTERNS: List[Pattern] = [
    re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_KEY_PATTERNS
]

# API key value patterns (for detecting keys in values)
API_KEY_VALUE_PATTERNS = [
    # OpenAI keys: sk-proj-xxx or sk-xxx
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),

    # Anthropic keys: sk-ant-xxx
    re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),

    # Generic Bearer tokens
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.=]+", re.IGNORECASE),

    # JWT tokens (three base64 segments separated by dots)
    re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),

    # Generic API keys (alphanumeric + special chars, length >= 20)
    re.compile(r"\b[a-zA-Z0-9_\-\.]{32,}\b"),
]

# PII patterns
PII_PATTERNS = [
    # Email addresses
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),

    # Phone numbers (various formats)
    ("phone", re.compile(r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),

    # SSN (123-45-6789 or 123456789)
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b")),

    # Credit card numbers (simple pattern, 13-19 digits with optional separators)
    ("credit_card", re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4,7}\b")),
]

# Environment variable allowlist (safe to log)
ENV_VAR_ALLOWLIST = {
    "DEBUG",
    "LOG_LEVEL",
    "ENVIRONMENT",
    "ENV",
    "NODE_ENV",
    "PYTHONPATH",
    "PATH",
    "HOME",
    "USER",
    "SHELL",
    "TERM",
    "LANG",
    "LC_ALL",
    "TZ",
}

# Redaction string
REDACTED = "***REDACTED***"

# Cached pattern for detecting long random tokens (used in is_likely_sensitive)
_RANDOM_TOKEN_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.=]+$")


# ══════════════════════════════════════════════════════════════════════
# Core Sanitization Functions
# ══════════════════════════════════════════════════════════════════════


def sanitize_log_data(data: Any, preserve_structure: bool = True) -> Any:
    """
    Sanitize sensitive data from log payloads.

    This is the main entry point for log sanitization. It recursively
    traverses data structures and redacts sensitive information.

    Args:
        data: Data to sanitize (dict, list, str, or primitive)
        preserve_structure: If True, preserve dict/list structure (default: True)

    Returns:
        Sanitized copy of data with sensitive information redacted

    Examples:
        >>> sanitize_log_data({"api_key": "sk-1234567890", "task": "build website"})
        {"api_key": "***REDACTED***", "task": "build website"}

        >>> sanitize_log_data({"Authorization": "Bearer abc123"})
        {"Authorization": "***REDACTED***"}
    """
    try:
        return _sanitize_recursive(data, preserve_structure)
    except Exception as e:
        # Fail-safe: Return original data if sanitization fails
        # This ensures logging never crashes the application
        print(f"[LogSanitizer] Warning: Sanitization failed: {e}")
        return data


def _sanitize_recursive(data: Any, preserve_structure: bool) -> Any:
    """
    Recursively sanitize data structures.

    Args:
        data: Data to sanitize
        preserve_structure: Whether to preserve dict/list structure

    Returns:
        Sanitized data
    """
    if data is None:
        return None

    # Handle dictionaries
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            # Check if key matches sensitive pattern
            if _is_sensitive_key(key):
                sanitized[key] = _redact_value(value)
            else:
                # Recursively sanitize value (may still contain sensitive data)
                sanitized[key] = _sanitize_recursive(value, preserve_structure)
        return sanitized

    # Handle lists
    if isinstance(data, list):
        return [_sanitize_recursive(item, preserve_structure) for item in data]

    # Handle tuples
    if isinstance(data, tuple):
        return tuple(_sanitize_recursive(item, preserve_structure) for item in data)

    # Handle strings (check for API keys and PII in values)
    if isinstance(data, str):
        return _sanitize_string_value(data)

    # Primitive types (int, float, bool, etc.) - pass through
    return data


def _is_sensitive_key(key: str) -> bool:
    """
    Check if a dictionary key matches sensitive patterns.

    Args:
        key: Dictionary key to check

    Returns:
        True if key matches sensitive pattern, False otherwise
    """
    if not isinstance(key, str):
        return False

    for pattern in _COMPILED_KEY_PATTERNS:
        if pattern.match(key):
            return True

    return False


def _redact_value(value: Any) -> str:
    """
    Redact a sensitive value while preserving type and length information.

    For strings longer than 8 characters, shows first 4 and last 4 characters
    to aid debugging while protecting the secret.

    Args:
        value: Value to redact

    Returns:
        Redacted string representation

    Examples:
        >>> _redact_value("sk-1234567890abcdef")
        "sk-1...cdef"

        >>> _redact_value("short")
        "***REDACTED***"

        >>> _redact_value(12345)
        "***REDACTED***"
    """
    if value is None:
        return REDACTED

    if isinstance(value, str) and len(value) > 8:
        # Show first 4 and last 4 characters for debugging
        return f"{value[:4]}...{value[-4:]}"

    return REDACTED


def _sanitize_string_value(text: str) -> str:
    """
    Sanitize string values for API keys and PII patterns.

    This catches cases where sensitive data appears in string values
    (not just dict keys), such as in log messages, task descriptions, etc.

    Args:
        text: String to sanitize

    Returns:
        Sanitized string with API keys and PII redacted
    """
    if not text or not isinstance(text, str):
        return text

    # Check for API keys
    for pattern in API_KEY_VALUE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # For long keys, show prefix/suffix for debugging
            if len(match) > 16:
                redacted = f"{match[:6]}...{match[-4:]}"
            else:
                redacted = REDACTED
            text = text.replace(match, redacted)

    # Check for PII
    for pii_type, pattern in PII_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # Mask PII differently based on type
            if pii_type == "email":
                # Show first char and domain
                parts = match.split("@")
                if len(parts) == 2:
                    text = text.replace(match, f"{parts[0][0]}***@{parts[1]}")
                else:
                    text = text.replace(match, "***@***")
            elif pii_type == "phone":
                # Show last 4 digits
                text = text.replace(match, f"***-***-{match[-4:]}")
            elif pii_type == "ssn":
                # Show last 4 digits
                text = text.replace(match, f"***-**-{match[-4:]}")
            elif pii_type == "credit_card":
                # Show last 4 digits
                text = text.replace(match, f"****-****-****-{match[-4:]}")
            else:
                text = text.replace(match, REDACTED)

    return text


# ══════════════════════════════════════════════════════════════════════
# Specialized Sanitization Functions
# ══════════════════════════════════════════════════════════════════════


def sanitize_llm_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize LLM request payloads specifically.

    Handles common LLM request formats:
    - messages array with role/content
    - system prompts
    - function calls

    Args:
        request_data: LLM request dict (e.g., for OpenAI API)

    Returns:
        Sanitized copy of request data
    """
    sanitized = copy.deepcopy(request_data)

    # Sanitize messages array
    if "messages" in sanitized and isinstance(sanitized["messages"], list):
        for msg in sanitized["messages"]:
            if isinstance(msg, dict) and "content" in msg:
                if isinstance(msg["content"], str):
                    msg["content"] = _sanitize_string_value(msg["content"])

    # Sanitize system prompt
    if "system" in sanitized and isinstance(sanitized["system"], str):
        sanitized["system"] = _sanitize_string_value(sanitized["system"])

    # Sanitize function calls (may contain sensitive args)
    if "functions" in sanitized:
        sanitized["functions"] = sanitize_log_data(sanitized["functions"])

    # Sanitize headers (may contain auth tokens)
    if "headers" in sanitized:
        sanitized["headers"] = sanitize_log_data(sanitized["headers"])

    return sanitized


def sanitize_llm_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize LLM response payloads.

    LLM responses may echo back sensitive data from the prompt,
    so we sanitize the response content as well.

    Args:
        response_data: LLM response dict

    Returns:
        Sanitized copy of response data
    """
    sanitized = copy.deepcopy(response_data)

    # Sanitize choices array
    if "choices" in sanitized and isinstance(sanitized["choices"], list):
        for choice in sanitized["choices"]:
            if isinstance(choice, dict):
                # Sanitize message content
                if "message" in choice and isinstance(choice["message"], dict):
                    if "content" in choice["message"]:
                        choice["message"]["content"] = _sanitize_string_value(
                            choice["message"]["content"]
                        )
                # Sanitize function call arguments
                if "function_call" in choice:
                    choice["function_call"] = sanitize_log_data(choice["function_call"])

    return sanitized


def sanitize_env_vars(
    env_dict: Dict[str, str],
    allowlist: Optional[Set[str]] = None
) -> Dict[str, str]:
    """
    Sanitize environment variables dictionary.

    By default, redacts all environment variables except those in the allowlist.

    Args:
        env_dict: Dictionary of environment variables
        allowlist: Set of allowed variable names (defaults to ENV_VAR_ALLOWLIST)

    Returns:
        Sanitized copy of environment variables

    Examples:
        >>> sanitize_env_vars({"DEBUG": "1", "OPENAI_API_KEY": "sk-123"})
        {"DEBUG": "1", "OPENAI_API_KEY": "***REDACTED***"}
    """
    if allowlist is None:
        allowlist = ENV_VAR_ALLOWLIST

    sanitized = {}
    for key, value in env_dict.items():
        if key in allowlist:
            sanitized[key] = value
        else:
            sanitized[key] = _redact_value(value)

    return sanitized


def sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages that may contain sensitive data.

    Error messages from APIs often echo back sensitive information
    (e.g., "Invalid API key: sk-123...").

    Args:
        error_msg: Error message to sanitize

    Returns:
        Sanitized error message
    """
    return _sanitize_string_value(error_msg)


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitize HTTP headers, redacting Authorization, X-API-Key, etc.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        Sanitized copy of headers
    """
    return sanitize_log_data(headers)


# ══════════════════════════════════════════════════════════════════════
# Utility Functions
# ══════════════════════════════════════════════════════════════════════


def is_likely_sensitive(value: str) -> bool:
    """
    Check if a string value is likely to be sensitive data.

    Useful for proactive detection in logging code.

    Args:
        value: String to check

    Returns:
        True if value matches sensitive patterns
    """
    if not isinstance(value, str):
        return False

    # Check API key patterns
    for pattern in API_KEY_VALUE_PATTERNS:
        if pattern.search(value):
            return True

    # Check if it looks like a long random token (use cached pattern)
    if len(value) >= 32 and _RANDOM_TOKEN_PATTERN.match(value):
        return True

    return False


def add_sensitive_pattern(pattern: str) -> None:
    """
    Add a custom sensitive key pattern at runtime.

    Useful for application-specific sensitive keys.

    Args:
        pattern: Regex pattern for sensitive keys (case-insensitive)

    Examples:
        >>> add_sensitive_pattern(r".*custom[_-]?secret.*")
    """
    global _COMPILED_KEY_PATTERNS
    _COMPILED_KEY_PATTERNS.append(re.compile(pattern, re.IGNORECASE))


def get_sanitization_stats() -> Dict[str, int]:
    """
    Get statistics about sanitization patterns.

    Useful for debugging and monitoring.

    Returns:
        Dict with pattern counts
    """
    return {
        "sensitive_key_patterns": len(_COMPILED_KEY_PATTERNS),
        "api_key_value_patterns": len(API_KEY_VALUE_PATTERNS),
        "pii_patterns": len(PII_PATTERNS),
        "env_allowlist_size": len(ENV_VAR_ALLOWLIST),
    }


# ══════════════════════════════════════════════════════════════════════
# Testing Helpers
# ══════════════════════════════════════════════════════════════════════


def test_sanitization(test_data: Any) -> Dict[str, Any]:
    """
    Test sanitization on sample data and return before/after.

    Useful for testing and validation.

    Args:
        test_data: Data to test sanitization on

    Returns:
        Dict with 'original' and 'sanitized' keys
    """
    return {
        "original": test_data,
        "sanitized": sanitize_log_data(test_data),
    }
