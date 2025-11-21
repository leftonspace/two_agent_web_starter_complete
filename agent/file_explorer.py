"""
File explorer for projects and snapshots.

STAGE 9: Browse project files, snapshots, and compare versions.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# File size limit for viewing (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".ico",
    ".svg",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}


@dataclass
class FileNode:
    """Represents a file or directory in the file tree."""

    name: str
    path: str  # Relative path from project root
    is_dir: bool
    size: Optional[int] = None  # File size in bytes
    children: Optional[List["FileNode"]] = None  # For directories


@dataclass
class Snapshot:
    """Represents a project snapshot."""

    id: str  # e.g., "iteration_1"
    iteration: int  # Iteration number
    path: str  # Full path to snapshot directory
    created_at: Optional[str] = None  # Timestamp if available


def is_safe_path(base_path: Path, requested_path: Path) -> bool:
    """
    Check if requested_path is safely within base_path.

    Args:
        base_path: Root directory that access is limited to
        requested_path: Path to check

    Returns:
        True if safe, False otherwise
    """
    try:
        base_resolved = base_path.resolve()
        requested_resolved = requested_path.resolve()
        return requested_resolved.is_relative_to(base_resolved)
    except (ValueError, OSError):
        return False


def is_text_file(file_path: Path) -> bool:
    """
    Check if a file is likely a text file.

    Args:
        file_path: Path to the file

    Returns:
        True if likely text, False if likely binary
    """
    # Check extension
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return False

    # Check for common text extensions
    text_extensions = {
        ".txt",
        ".md",
        ".html",
        ".htm",
        ".css",
        ".js",
        ".json",
        ".py",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".xml",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".cfg",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ts",
        ".tsx",
        ".jsx",
        ".vue",
        ".svelte",
        ".sql",
        ".go",
        ".rs",
        ".rb",
        ".php",
    }
    if file_path.suffix.lower() in text_extensions:
        return True

    # For files without extension or unknown extensions, try reading a sample
    try:
        with open(file_path, "rb") as f:
            sample = f.read(1024)
            # Check if sample contains null bytes (strong indicator of binary)
            if b"\x00" in sample:
                return False
            # Try to decode as UTF-8
            sample.decode("utf-8")
            return True
    except (OSError, UnicodeDecodeError):
        return False


def get_project_tree(project_path: Path, relative_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Generate a file tree for a project directory.

    Args:
        project_path: Root directory of the project
        relative_root: Optional subdirectory to start from (relative to project_path)

    Returns:
        List of file/directory nodes as dicts
    """
    if not project_path.exists() or not project_path.is_dir():
        return []

    root = project_path / relative_root if relative_root else project_path

    if not is_safe_path(project_path, root):
        return []

    nodes: List[Dict[str, Any]] = []

    try:
        items = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

        for item in items:
            # Skip hidden/internal files and directories like .history, .git, etc.
            if item.name.startswith(".") or item.name in {"__pycache__", "node_modules"}:
                continue

            # Get relative path from project root
            rel_path = item.relative_to(project_path)

            if item.is_dir():
                nodes.append(
                    {
                        "name": item.name,
                        "path": str(rel_path),
                        "is_dir": True,
                        "children": None,  # Lazy load on expand
                    }
                )
            else:
                size = item.stat().st_size if item.exists() else None
                nodes.append(
                    {
                        "name": item.name,
                        "path": str(rel_path),
                        "is_dir": False,
                        "size": size,
                    }
                )

    except (OSError, PermissionError):
        pass

    return nodes


def get_file_content(project_path: Path, file_path: str) -> Dict[str, Any]:
    """
    Read file content safely.

    Args:
        project_path: Project root directory
        file_path: Relative path to file within project

    Returns:
        Dict with keys:
        - content: File content as string
        - error: Error message if any
        - is_binary: True if file is binary
        - is_too_large: True if file exceeds size limit
    """
    full_path = project_path / file_path

    # Safety check
    if not is_safe_path(project_path, full_path):
        return {
            "content": None,
            "error": "Access denied: Path outside project directory",
            "is_binary": False,
            "is_too_large": False,
        }

    if not full_path.exists() or not full_path.is_file():
        return {
            "content": None,
            "error": "File not found",
            "is_binary": False,
            "is_too_large": False,
        }

    # Check file size
    try:
        size = full_path.stat().st_size
        if size > MAX_FILE_SIZE:
            return {
                "content": None,
                "error": f"File too large to display ({size / 1024 / 1024:.1f} MB > 5 MB limit)",
                "is_binary": False,
                "is_too_large": True,
            }
    except OSError as e:
        return {
            "content": None,
            "error": f"Error reading file: {e}",
            "is_binary": False,
            "is_too_large": False,
        }

    # Check if binary
    if not is_text_file(full_path):
        return {
            "content": None,
            "error": "Binary file (cannot display)",
            "is_binary": True,
            "is_too_large": False,
        }

    # Read file content
    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "content": content,
            "error": None,
            "is_binary": False,
            "is_too_large": False,
        }
    except Exception as e:  # noqa: BLE001
        return {
            "content": None,
            "error": f"Error reading file: {e}",
            "is_binary": False,
            "is_too_large": False,
        }


def list_snapshots(project_path: Path) -> List[Snapshot]:
    """
    List all snapshots for a project.

    Args:
        project_path: Project root directory

    Returns:
        List of Snapshot objects, sorted by iteration number
    """
    history_dir = project_path / ".history"

    if not history_dir.exists() or not history_dir.is_dir():
        return []

    snapshots: List[Snapshot] = []

    try:
        for item in history_dir.iterdir():
            if item.is_dir() and item.name.startswith("iteration_"):
                try:
                    # Extract iteration number from name
                    iteration = int(item.name.split("_")[1])

                    # Get creation time if available
                    created_at = None
                    try:
                        stat = item.stat()
                        created_at = str(stat.st_mtime)  # Unix timestamp
                    except OSError:
                        pass

                    snapshots.append(
                        Snapshot(
                            id=item.name,
                            iteration=iteration,
                            path=str(item),
                            created_at=created_at,
                        )
                    )
                except (ValueError, IndexError):
                    # Skip malformed directory names
                    continue

        # Sort by iteration number
        snapshots.sort(key=lambda s: s.iteration)

    except (OSError, PermissionError):
        pass

    return snapshots


def compute_diff(
    file1_path: Path,
    file2_path: Path,
    file1_label: str = "before",
    file2_label: str = "after",
) -> Dict[str, Any]:
    """
    Compute unified diff between two files.

    Args:
        file1_path: Path to first file
        file2_path: Path to second file
        file1_label: Label for first file in diff output
        file2_label: Label for second file in diff output

    Returns:
        Dict with keys:
        - diff: Unified diff as string
        - error: Error message if any
        - is_binary: True if files are binary
        - file1_missing: True if file1 doesn't exist
        - file2_missing: True if file2 doesn't exist
    """
    file1_exists = file1_path.exists() and file1_path.is_file()
    file2_exists = file2_path.exists() and file2_path.is_file()

    # Handle missing files
    if not file1_exists and not file2_exists:
        return {
            "diff": "Both files are missing",
            "error": None,
            "is_binary": False,
            "file1_missing": True,
            "file2_missing": True,
        }

    if not file1_exists:
        # File added
        try:
            if not is_text_file(file2_path):
                return {
                    "diff": f"Binary file added: {file2_label}",
                    "error": None,
                    "is_binary": True,
                    "file1_missing": True,
                    "file2_missing": False,
                }

            with open(file2_path, "r", encoding="utf-8", errors="replace") as f:
                lines2 = f.readlines()

            diff = difflib.unified_diff(
                [],
                lines2,
                fromfile=file1_label,
                tofile=file2_label,
                lineterm="",
            )

            return {
                "diff": "\n".join(diff),
                "error": None,
                "is_binary": False,
                "file1_missing": True,
                "file2_missing": False,
            }
        except Exception as e:  # noqa: BLE001
            return {
                "diff": None,
                "error": f"Error reading file: {e}",
                "is_binary": False,
                "file1_missing": True,
                "file2_missing": False,
            }

    if not file2_exists:
        # File deleted
        try:
            if not is_text_file(file1_path):
                return {
                    "diff": f"Binary file deleted: {file1_label}",
                    "error": None,
                    "is_binary": True,
                    "file1_missing": False,
                    "file2_missing": True,
                }

            with open(file1_path, "r", encoding="utf-8", errors="replace") as f:
                lines1 = f.readlines()

            diff = difflib.unified_diff(
                lines1,
                [],
                fromfile=file1_label,
                tofile=file2_label,
                lineterm="",
            )

            return {
                "diff": "\n".join(diff),
                "error": None,
                "is_binary": False,
                "file1_missing": False,
                "file2_missing": True,
            }
        except Exception as e:  # noqa: BLE001
            return {
                "diff": None,
                "error": f"Error reading file: {e}",
                "is_binary": False,
                "file1_missing": False,
                "file2_missing": True,
            }

    # Both files exist - check if binary
    if not is_text_file(file1_path) or not is_text_file(file2_path):
        return {
            "diff": f"Binary files differ: {file1_label} and {file2_label}",
            "error": None,
            "is_binary": True,
            "file1_missing": False,
            "file2_missing": False,
        }

    # Read both files and compute diff
    try:
        with open(file1_path, "r", encoding="utf-8", errors="replace") as f:
            lines1 = f.readlines()
        with open(file2_path, "r", encoding="utf-8", errors="replace") as f:
            lines2 = f.readlines()

        diff = difflib.unified_diff(
            lines1,
            lines2,
            fromfile=file1_label,
            tofile=file2_label,
            lineterm="",
        )

        diff_text = "\n".join(diff)

        if not diff_text:
            diff_text = "Files are identical"

        return {
            "diff": diff_text,
            "error": None,
            "is_binary": False,
            "file1_missing": False,
            "file2_missing": False,
        }

    except Exception as e:  # noqa: BLE001
        return {
            "diff": None,
            "error": f"Error computing diff: {e}",
            "is_binary": False,
            "file1_missing": False,
            "file2_missing": False,
        }
