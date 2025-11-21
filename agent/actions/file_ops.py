"""
Safe file system operations.

PHASE 8.3: File system operations with workspace restrictions and security validation.
"""

import aiofiles
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from agent.core_logging import log_event


class FileOperations:
    """
    Safe file system operations with workspace restrictions.

    Features:
    - Read/write files within workspace only
    - Path validation prevents directory traversal
    - System file protection
    - Directory operations
    - File metadata
    - Async file I/O

    Example:
        ops = FileOperations(workspace_root="/path/to/workspace")

        # Read file
        content = await ops.read_file("project/README.md")

        # Write file
        await ops.write_file("output.txt", "Hello World")

        # Create directory
        await ops.create_directory("new_folder")

        # List files
        files = await ops.list_files(".")
    """

    def __init__(
        self,
        workspace_root: str,
        max_file_size: int = 10 * 1024 * 1024  # 10MB default
    ):
        """
        Initialize file operations.

        Args:
            workspace_root: Root directory for all operations
            max_file_size: Maximum file size in bytes
        """
        self.workspace = Path(workspace_root).resolve()
        self.max_file_size = max_file_size

        # Forbidden paths (system directories)
        self.forbidden_paths = [
            "/etc",
            "/sys",
            "/proc",
            "/dev",
            "/boot",
            "/root",
            "C:\\Windows",
            "C:\\System32",
            "C:\\Program Files"
        ]

        # Ensure workspace exists
        self.workspace.mkdir(parents=True, exist_ok=True)

        log_event("file_operations_initialized", {
            "workspace": str(self.workspace)
        })

    def _validate_path(self, path: str) -> Path:
        """
        Validate path is safe and within workspace.

        Args:
            path: Relative path from workspace root

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path is unsafe
        """
        # Convert to Path and resolve
        if os.path.isabs(path):
            # If absolute, check if within workspace
            full_path = Path(path).resolve()
        else:
            # If relative, join with workspace
            full_path = (self.workspace / path).resolve()

        # Check if path is within workspace
        try:
            full_path.relative_to(self.workspace)
        except ValueError:
            raise ValueError(f"Path outside workspace: {path}")

        # Check against forbidden paths
        full_path_str = str(full_path)
        for forbidden in self.forbidden_paths:
            if full_path_str.startswith(forbidden):
                raise ValueError(f"Access to system files denied: {path}")

        return full_path

    async def read_file(self, path: str) -> str:
        """
        Read file contents.

        Args:
            path: Path to file (relative to workspace)

        Returns:
            File contents as string

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If file doesn't exist
        """
        safe_path = self._validate_path(path)

        # Check file exists
        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not safe_path.is_file():
            raise ValueError(f"Not a file: {path}")

        # Check file size
        size = safe_path.stat().st_size
        if size > self.max_file_size:
            raise ValueError(f"File too large: {size} bytes (max {self.max_file_size})")

        # Read file
        async with aiofiles.open(safe_path, 'r', encoding='utf-8') as f:
            content = await f.read()

        log_event("file_read", {
            "path": path,
            "size": size
        })

        return content

    async def write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True
    ):
        """
        Write content to file.

        Args:
            path: Path to file (relative to workspace)
            content: Content to write
            create_dirs: Create parent directories if needed

        Raises:
            ValueError: If path is invalid or content too large
        """
        safe_path = self._validate_path(path)

        # Check content size
        content_bytes = content.encode('utf-8')
        if len(content_bytes) > self.max_file_size:
            raise ValueError(
                f"Content too large: {len(content_bytes)} bytes "
                f"(max {self.max_file_size})"
            )

        # Create parent directories if needed
        if create_dirs:
            safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        async with aiofiles.open(safe_path, 'w', encoding='utf-8') as f:
            await f.write(content)

        log_event("file_written", {
            "path": path,
            "size": len(content_bytes)
        })

    async def append_file(self, path: str, content: str):
        """
        Append content to file.

        Args:
            path: Path to file
            content: Content to append

        Raises:
            ValueError: If path is invalid
        """
        safe_path = self._validate_path(path)

        # Create parent directories if needed
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to file
        async with aiofiles.open(safe_path, 'a', encoding='utf-8') as f:
            await f.write(content)

        log_event("file_appended", {
            "path": path,
            "size": len(content.encode('utf-8'))
        })

    async def delete_file(self, path: str):
        """
        Delete file.

        Args:
            path: Path to file

        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If file doesn't exist
        """
        safe_path = self._validate_path(path)

        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not safe_path.is_file():
            raise ValueError(f"Not a file: {path}")

        safe_path.unlink()

        log_event("file_deleted", {
            "path": path
        })

    async def create_directory(self, path: str):
        """
        Create directory.

        Args:
            path: Path to directory

        Raises:
            ValueError: If path is invalid
        """
        safe_path = self._validate_path(path)

        safe_path.mkdir(parents=True, exist_ok=True)

        log_event("directory_created", {
            "path": path
        })

    async def delete_directory(self, path: str, recursive: bool = False):
        """
        Delete directory.

        Args:
            path: Path to directory
            recursive: Delete recursively

        Raises:
            ValueError: If path is invalid or not empty (without recursive)
        """
        safe_path = self._validate_path(path)

        if not safe_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not safe_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        if recursive:
            shutil.rmtree(safe_path)
        else:
            # Non-recursive - will fail if not empty
            safe_path.rmdir()

        log_event("directory_deleted", {
            "path": path,
            "recursive": recursive
        })

    async def list_files(
        self,
        path: str = ".",
        pattern: Optional[str] = None,
        recursive: bool = False
    ) -> List[str]:
        """
        List files in directory.

        Args:
            path: Directory path
            pattern: Glob pattern (e.g., "*.py")
            recursive: List recursively

        Returns:
            List of file paths (relative to workspace)

        Raises:
            ValueError: If path is invalid
        """
        safe_path = self._validate_path(path)

        if not safe_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not safe_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        # List files
        files = []

        if pattern:
            # Use glob pattern
            if recursive:
                matches = safe_path.rglob(pattern)
            else:
                matches = safe_path.glob(pattern)

            for file_path in matches:
                if file_path.is_file():
                    # Get relative path from workspace
                    rel_path = file_path.relative_to(self.workspace)
                    files.append(str(rel_path))
        else:
            # List all files
            if recursive:
                for root, _, filenames in os.walk(safe_path):
                    for filename in filenames:
                        file_path = Path(root) / filename
                        rel_path = file_path.relative_to(self.workspace)
                        files.append(str(rel_path))
            else:
                for item in safe_path.iterdir():
                    if item.is_file():
                        rel_path = item.relative_to(self.workspace)
                        files.append(str(rel_path))

        return sorted(files)

    async def list_directories(
        self,
        path: str = ".",
        recursive: bool = False
    ) -> List[str]:
        """
        List directories.

        Args:
            path: Directory path
            recursive: List recursively

        Returns:
            List of directory paths (relative to workspace)
        """
        safe_path = self._validate_path(path)

        if not safe_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")

        if not safe_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        directories = []

        if recursive:
            for root, dirnames, _ in os.walk(safe_path):
                for dirname in dirnames:
                    dir_path = Path(root) / dirname
                    rel_path = dir_path.relative_to(self.workspace)
                    directories.append(str(rel_path))
        else:
            for item in safe_path.iterdir():
                if item.is_dir():
                    rel_path = item.relative_to(self.workspace)
                    directories.append(str(rel_path))

        return sorted(directories)

    def file_exists(self, path: str) -> bool:
        """Check if file exists"""
        try:
            safe_path = self._validate_path(path)
            return safe_path.exists() and safe_path.is_file()
        except (ValueError, FileNotFoundError):
            return False

    def directory_exists(self, path: str) -> bool:
        """Check if directory exists"""
        try:
            safe_path = self._validate_path(path)
            return safe_path.exists() and safe_path.is_dir()
        except (ValueError, FileNotFoundError):
            return False

    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Get file metadata.

        Args:
            path: Path to file

        Returns:
            Dict with file metadata
        """
        safe_path = self._validate_path(path)

        if not safe_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        stat = safe_path.stat()

        return {
            "path": path,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": safe_path.is_file(),
            "is_dir": safe_path.is_dir()
        }

    async def copy_file(self, source: str, destination: str):
        """
        Copy file.

        Args:
            source: Source path
            destination: Destination path
        """
        safe_source = self._validate_path(source)
        safe_dest = self._validate_path(destination)

        if not safe_source.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        if not safe_source.is_file():
            raise ValueError(f"Source is not a file: {source}")

        # Create parent directories
        safe_dest.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        shutil.copy2(safe_source, safe_dest)

        log_event("file_copied", {
            "source": source,
            "destination": destination
        })

    async def move_file(self, source: str, destination: str):
        """
        Move/rename file.

        Args:
            source: Source path
            destination: Destination path
        """
        safe_source = self._validate_path(source)
        safe_dest = self._validate_path(destination)

        if not safe_source.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        # Create parent directories
        safe_dest.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        shutil.move(str(safe_source), str(safe_dest))

        log_event("file_moved", {
            "source": source,
            "destination": destination
        })
