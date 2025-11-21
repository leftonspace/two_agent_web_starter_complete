"""
File Context Manager

Manages file attachments and context in conversations.
Allows users to:
- Attach files to conversation
- Search for files by name
- Maintain file context across messages
"""

import os
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class AttachedFile:
    """Represents a file attached to conversation"""
    path: str
    name: str
    content: str
    mime_type: str
    size: int
    timestamp: float

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "name": self.name,
            "content": self.content,
            "mime_type": self.mime_type,
            "size": self.size,
            "timestamp": self.timestamp
        }


class FileContextManager:
    """
    Manages file context in conversations.

    Features:
    - Attach files to chat
    - Search for files
    - Read file content
    - Track active file context
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        """
        Initialize file context manager.

        Args:
            workspace_root: Root directory for file operations
        """
        self.workspace_root = workspace_root or Path("sites")
        self.attached_files: Dict[str, AttachedFile] = {}

    async def attach_file(
        self,
        file_path: str,
        session_id: str
    ) -> AttachedFile:
        """
        Attach a file to the conversation.

        Args:
            file_path: Path to file (relative or absolute)
            session_id: Session identifier

        Returns:
            AttachedFile object
        """
        # Resolve path
        resolved_path = self._resolve_path(file_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read content
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary file
            content = f"[Binary file: {resolved_path.name}]"

        # Get mime type
        mime_type, _ = mimetypes.guess_type(str(resolved_path))

        # Create attached file
        attached = AttachedFile(
            path=str(resolved_path),
            name=resolved_path.name,
            content=content,
            mime_type=mime_type or "text/plain",
            size=resolved_path.stat().st_size,
            timestamp=os.path.getmtime(resolved_path)
        )

        # Store in context
        context_key = f"{session_id}:{resolved_path.name}"
        self.attached_files[context_key] = attached

        return attached

    def find_files(
        self,
        filename: str,
        search_path: Optional[Path] = None
    ) -> List[Path]:
        """
        Find files by name.

        Args:
            filename: Filename or pattern to search
            search_path: Directory to search in

        Returns:
            List of matching file paths
        """
        search_root = search_path or self.workspace_root

        if not search_root.exists():
            return []

        matches = []

        # Search recursively
        for file in search_root.rglob(filename):
            if file.is_file():
                matches.append(file)

        return matches

    def find_files_by_pattern(
        self,
        pattern: str,
        search_path: Optional[Path] = None
    ) -> List[Path]:
        """
        Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "*.py")
            search_path: Directory to search in

        Returns:
            List of matching file paths
        """
        search_root = search_path or self.workspace_root

        if not search_root.exists():
            return []

        matches = list(search_root.rglob(pattern))
        return [m for m in matches if m.is_file()]

    def get_attached_files(self, session_id: str) -> List[AttachedFile]:
        """Get all files attached to a session"""
        return [
            file for key, file in self.attached_files.items()
            if key.startswith(f"{session_id}:")
        ]

    def read_file(self, file_path: str) -> str:
        """Read file content"""
        resolved_path = self._resolve_path(file_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return f"[Binary file: {resolved_path.name}]"

    def write_file(self, file_path: str, content: str):
        """Write content to file"""
        resolved_path = self._resolve_path(file_path)

        # Create parent directories
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

        with open(resolved_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def list_files(
        self,
        directory: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict]:
        """
        List files in directory.

        Returns:
            List of file info dicts
        """
        dir_path = self._resolve_path(directory) if directory else self.workspace_root

        if not dir_path.exists() or not dir_path.is_dir():
            return []

        files = []

        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for file in dir_path.glob(pattern):
            if file.is_file():
                files.append({
                    "name": file.name,
                    "path": str(file.relative_to(self.workspace_root)),
                    "size": file.stat().st_size,
                    "modified": file.stat().st_mtime,
                    "extension": file.suffix
                })

        return files

    def get_file_info(self, file_path: str) -> Dict:
        """Get file information"""
        resolved_path = self._resolve_path(file_path)

        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = resolved_path.stat()

        return {
            "name": resolved_path.name,
            "path": str(resolved_path),
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "extension": resolved_path.suffix,
            "mime_type": mimetypes.guess_type(str(resolved_path))[0]
        }

    def search_in_files(
        self,
        query: str,
        file_pattern: str = "*",
        search_path: Optional[Path] = None
    ) -> List[Dict]:
        """
        Search for text within files.

        Args:
            query: Text to search for
            file_pattern: File pattern to search in
            search_path: Directory to search

        Returns:
            List of matches with file path and line numbers
        """
        search_root = search_path or self.workspace_root
        matches = []

        files = self.find_files_by_pattern(file_pattern, search_root)

        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    if query.lower() in line.lower():
                        matches.append({
                            "file": str(file.relative_to(self.workspace_root)),
                            "line_number": line_num,
                            "line_content": line.strip(),
                            "context": self._get_line_context(lines, line_num - 1, 2)
                        })
            except (UnicodeDecodeError, PermissionError):
                continue

        return matches

    def _resolve_path(self, file_path: Optional[str]) -> Path:
        """Resolve file path relative to workspace"""
        if not file_path:
            return self.workspace_root

        path = Path(file_path)

        if path.is_absolute():
            return path

        # Try relative to workspace
        workspace_path = self.workspace_root / path
        if workspace_path.exists():
            return workspace_path

        # Try as-is
        if path.exists():
            return path

        # Return workspace relative path (may not exist)
        return workspace_path

    def _get_line_context(
        self,
        lines: List[str],
        line_index: int,
        context_lines: int = 2
    ) -> Dict:
        """Get context around a line"""
        start = max(0, line_index - context_lines)
        end = min(len(lines), line_index + context_lines + 1)

        return {
            "before": [line.strip() for line in lines[start:line_index]],
            "after": [line.strip() for line in lines[line_index + 1:end]]
        }

    def clear_session_context(self, session_id: str):
        """Clear all attached files for a session"""
        keys_to_remove = [
            key for key in self.attached_files.keys()
            if key.startswith(f"{session_id}:")
        ]

        for key in keys_to_remove:
            del self.attached_files[key]
