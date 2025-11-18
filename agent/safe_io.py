# safe_io.py
"""
Safe I/O utilities for the multi-agent system.

Provides error-resilient wrappers for common file and network operations
to prevent crashes from I/O failures, malformed JSON, network issues, etc.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def safe_json_read(path: Path) -> Optional[Dict[str, Any]]:
    """
    Safely read and parse a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON dict, or None if reading/parsing fails
    """
    try:
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except (IOError, OSError, json.JSONDecodeError) as e:
        print(f"[SYS] Failed to read JSON from {path}: {e}")
        return None


def safe_json_write(path: Path, data: Dict[str, Any], *, indent: int = 2) -> bool:
    """
    Safely write data to a JSON file.

    Args:
        path: Path to write to
        data: Data to serialize
        indent: JSON indentation (default: 2)

    Returns:
        True if successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=indent, ensure_ascii=False)
        path.write_text(text, encoding="utf-8")
        return True
    except (IOError, OSError, TypeError) as e:
        print(f"[SYS] Failed to write JSON to {path}: {e}")
        return False


def safe_timestamp() -> str:
    """
    Generate a safe ISO timestamp.

    Returns:
        ISO formatted timestamp string, or fallback if datetime fails
    """
    try:
        return datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    except Exception:
        # Fallback to basic format if isoformat fails
        try:
            return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        except Exception:
            return "1970-01-01T00:00:00.000Z"


def safe_file_read(path: Path, *, encoding: str = "utf-8") -> Optional[str]:
    """
    Safely read a text file.

    Args:
        path: Path to file
        encoding: Text encoding (default: utf-8)

    Returns:
        File contents, or None if reading fails
    """
    try:
        if not path.exists():
            return None
        return path.read_text(encoding=encoding, errors="ignore")
    except (IOError, OSError) as e:
        print(f"[SYS] Failed to read file {path}: {e}")
        return None


def safe_file_write(path: Path, content: str, *, encoding: str = "utf-8") -> bool:
    """
    Safely write content to a text file.

    Args:
        path: Path to write to
        content: Content to write
        encoding: Text encoding (default: utf-8)

    Returns:
        True if successful, False otherwise
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return True
    except (IOError, OSError) as e:
        print(f"[SYS] Failed to write file {path}: {e}")
        return False


def safe_mkdir(path: Path) -> bool:
    """
    Safely create a directory (and parents).

    Args:
        path: Directory path to create

    Returns:
        True if successful or already exists, False on error
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (IOError, OSError) as e:
        print(f"[SYS] Failed to create directory {path}: {e}")
        return False


def safe_path_resolve(path_str: str) -> Optional[Path]:
    """
    Safely resolve a path string to an absolute Path.

    Args:
        path_str: Path string

    Returns:
        Resolved Path object, or None if resolution fails
    """
    try:
        return Path(path_str).resolve()
    except (ValueError, OSError) as e:
        print(f"[SYS] Failed to resolve path '{path_str}': {e}")
        return None


def safe_get_config_value(
    config: Dict[str, Any],
    key: str,
    default: Any = None,
    *,
    cast: Optional[type] = None,
) -> Any:
    """
    Safely get a configuration value with optional type casting.

    Args:
        config: Configuration dictionary
        key: Key to retrieve
        default: Default value if key missing or cast fails
        cast: Optional type to cast to (int, float, str, bool)

    Returns:
        Configuration value or default
    """
    try:
        value = config.get(key, default)
        if cast is not None and value is not None:
            if cast is bool and isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return cast(value)
        return value
    except (ValueError, TypeError):
        return default
