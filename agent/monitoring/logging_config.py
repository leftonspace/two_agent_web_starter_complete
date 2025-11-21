"""
PHASE 11.2: Structured Logging Configuration

JSON-structured logging for production observability.

Features:
- JSON output format
- Context fields (request_id, user_id, etc.)
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Automatic field enrichment
- Performance tracking
- Integration with monitoring
"""

from __future__ import annotations

import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogRecord:
    """Structured log record."""
    timestamp: str
    level: str
    message: str
    logger_name: str
    module: str
    function: str
    line_number: int
    thread_name: str
    process_id: int
    context: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter.

    Outputs logs as JSON for structured logging systems.
    """

    def __init__(self, default_context: Optional[Dict[str, Any]] = None):
        """
        Initialize formatter.

        Args:
            default_context: Default context fields to include
        """
        super().__init__()
        self.default_context = default_context or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Extract exception info
        exception_info = None
        if record.exc_info:
            exception_info = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": "".join(traceback.format_exception(*record.exc_info)),
            }

        # Build context from extra fields
        context = self.default_context.copy()

        # Add fields from record
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info"
            ]:
                context[key] = value

        # Create structured log record
        log_record = LogRecord(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_name=record.threadName,
            process_id=record.process,
            context=context,
            exception=exception_info,
        )

        return log_record.to_json()


class StructuredLogger:
    """
    Structured logger wrapper.

    Provides convenient methods for logging with context.
    """

    def __init__(self, name: str, default_context: Optional[Dict[str, Any]] = None):
        """
        Initialize structured logger.

        Args:
            name: Logger name
            default_context: Default context fields
        """
        self.logger = logging.getLogger(name)
        self.default_context = default_context or {}

    def _log(
        self,
        level: int,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """Internal log method."""
        # Merge contexts
        merged_context = self.default_context.copy()
        if context:
            merged_context.update(context)

        # Log with extra fields
        self.logger.log(level, message, extra=merged_context, exc_info=exc_info)

    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self._log(logging.DEBUG, message, context)

    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self._log(logging.INFO, message, context)

    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self._log(logging.WARNING, message, context)

    def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """Log error message."""
        self._log(logging.ERROR, message, context, exc_info=exc_info)

    def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """Log critical message."""
        self._log(logging.CRITICAL, message, context, exc_info=exc_info)

    def with_context(self, **kwargs) -> StructuredLogger:
        """Create new logger with additional context."""
        new_context = self.default_context.copy()
        new_context.update(kwargs)
        return StructuredLogger(self.logger.name, new_context)


def setup_logging(
    level: LogLevel = LogLevel.INFO,
    output_file: Optional[Path] = None,
    json_format: bool = True,
    default_context: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        level: Log level
        output_file: Optional file output path
        json_format: Use JSON formatting (default: True)
        default_context: Default context fields

    Returns:
        Root logger
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers.clear()

    # Set level
    log_level = getattr(logging, level.value)
    root_logger.setLevel(log_level)

    # Create formatter
    if json_format:
        formatter = JSONFormatter(default_context=default_context)
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(output_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_structured_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None,
) -> StructuredLogger:
    """
    Get structured logger instance.

    Args:
        name: Logger name
        context: Default context

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, context)
