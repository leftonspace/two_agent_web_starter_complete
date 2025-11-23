"""
Standardized Error Classes and Messages

Provides consistent error formatting across all JARVIS 2.0 modules.
"""

from typing import Any, Dict, Optional


class JarvisError(Exception):
    """Base exception for all JARVIS errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format error message consistently."""
        base = f"[{self.code}] {self.message}"
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            base += f" ({detail_str})"
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(JarvisError):
    """Error in configuration loading or validation."""
    pass


class InvalidConfigError(ConfigurationError):
    """Configuration values are invalid."""
    pass


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""
    pass


# =============================================================================
# Flow Errors
# =============================================================================

class FlowError(JarvisError):
    """Error during flow execution."""
    pass


class FlowValidationError(FlowError):
    """Flow definition validation failed."""
    pass


class FlowTimeoutError(FlowError):
    """Flow execution timed out."""
    pass


class StepExecutionError(FlowError):
    """Step execution failed."""
    pass


# =============================================================================
# Pattern Errors
# =============================================================================

class PatternError(JarvisError):
    """Error in pattern execution."""
    pass


class NoAgentsError(PatternError):
    """No agents available for pattern."""
    pass


class PatternTimeoutError(PatternError):
    """Pattern execution timed out."""
    pass


# =============================================================================
# Council Errors
# =============================================================================

class CouncilError(JarvisError):
    """Error in council system."""
    pass


class InsufficientQuorumError(CouncilError):
    """Not enough votes for quorum."""
    pass


class VotingError(CouncilError):
    """Error during voting process."""
    pass


# =============================================================================
# Memory Errors
# =============================================================================

class MemoryError(JarvisError):
    """Error in memory system."""
    pass


class StorageError(MemoryError):
    """Error in storage operations."""
    pass


class RetrievalError(MemoryError):
    """Error retrieving from memory."""
    pass


# =============================================================================
# LLM Errors
# =============================================================================

class LLMError(JarvisError):
    """Error in LLM operations."""
    pass


class ProviderError(LLMError):
    """Error with LLM provider."""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class ModelNotFoundError(LLMError):
    """Requested model not found."""
    pass


# =============================================================================
# Tool Errors
# =============================================================================

class ToolError(JarvisError):
    """Error in tool execution."""
    pass


class ToolNotFoundError(ToolError):
    """Tool not found in registry."""
    pass


class ToolExecutionError(ToolError):
    """Tool execution failed."""
    pass


# =============================================================================
# Validation Errors
# =============================================================================

class ValidationError(JarvisError):
    """Input validation error."""
    pass


class EmptyInputError(ValidationError):
    """Input is empty or whitespace."""
    pass


class InvalidTypeError(ValidationError):
    """Input has invalid type."""
    pass


# =============================================================================
# Helper Functions
# =============================================================================

def format_error(
    error_type: str,
    message: str,
    **details: Any
) -> str:
    """
    Format an error message consistently.

    Args:
        error_type: Type/category of error
        message: Human-readable message
        **details: Additional context

    Returns:
        Formatted error string: "[ERROR_TYPE] message (key=value, ...)"
    """
    base = f"[{error_type}] {message}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        base += f" ({detail_str})"
    return base


__all__ = [
    # Base
    'JarvisError',
    'format_error',

    # Configuration
    'ConfigurationError',
    'InvalidConfigError',
    'MissingConfigError',

    # Flow
    'FlowError',
    'FlowValidationError',
    'FlowTimeoutError',
    'StepExecutionError',

    # Pattern
    'PatternError',
    'NoAgentsError',
    'PatternTimeoutError',

    # Council
    'CouncilError',
    'InsufficientQuorumError',
    'VotingError',

    # Memory
    'MemoryError',
    'StorageError',
    'RetrievalError',

    # LLM
    'LLMError',
    'ProviderError',
    'RateLimitError',
    'ModelNotFoundError',

    # Tool
    'ToolError',
    'ToolNotFoundError',
    'ToolExecutionError',

    # Validation
    'ValidationError',
    'EmptyInputError',
    'InvalidTypeError',
]
