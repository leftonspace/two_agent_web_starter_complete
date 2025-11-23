"""
JARVIS Tools System

Claude Code-like capabilities for JARVIS:
- Read: Read files from disk
- Edit: Make targeted string replacements in files
- Write: Create new files
- Bash: Run shell commands
- Grep: Search for patterns in code
- Glob: Find files by pattern
- Todo: Track tasks visibly
- WebSearch/WebFetch: Look up documentation
"""

import asyncio
import fnmatch
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Optional imports for web capabilities
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class ToolType(Enum):
    """Available tool types"""
    READ = "read"
    EDIT = "edit"
    WRITE = "write"
    BASH = "bash"
    GREP = "grep"
    GLOB = "glob"
    TODO = "todo"
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    tool: ToolType
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "tool": self.tool.value,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "execution_time": self.execution_time
        }


@dataclass
class TodoItem:
    """A task item"""
    id: str
    content: str
    status: str  # "pending", "in_progress", "completed"
    created_at: float
    updated_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class JarvisTools:
    """
    JARVIS Tools System - Claude Code-like capabilities

    Provides file operations, code search, shell execution,
    task tracking, and web capabilities.
    """

    def __init__(self, working_directory: Optional[str] = None):
        """Initialize the tools system"""
        self.working_dir = Path(working_directory) if working_directory else Path.cwd()
        self.todos: Dict[str, TodoItem] = {}
        self.command_history: List[Dict] = []
        self.file_cache: Dict[str, Tuple[float, str]] = {}  # path -> (mtime, content)

        # Safety settings
        self.allowed_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
            '.json', '.yaml', '.yml', '.md', '.txt', '.sh', '.bash',
            '.sql', '.env', '.gitignore', '.dockerignore', '.xml', '.csv'
        }
        self.blocked_paths = {'/etc', '/usr', '/bin', '/sbin', '/var', '/root'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

        print(f"[JarvisTools] Initialized with working directory: {self.working_dir}")

    # ═══════════════════════════════════════════════════════════════════════
    # READ TOOL - Read files from disk
    # ═══════════════════════════════════════════════════════════════════════

    async def read(
        self,
        file_path: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        encoding: str = "utf-8"
    ) -> ToolResult:
        """
        Read a file from disk.

        Args:
            file_path: Path to the file (absolute or relative to working_dir)
            line_start: Optional starting line number (1-indexed)
            line_end: Optional ending line number (1-indexed)
            encoding: File encoding (default: utf-8)

        Returns:
            ToolResult with file content
        """
        start_time = time.time()
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    tool=ToolType.READ,
                    output=None,
                    error=f"File not found: {path}",
                    execution_time=time.time() - start_time
                )

            if not path.is_file():
                return ToolResult(
                    success=False,
                    tool=ToolType.READ,
                    output=None,
                    error=f"Not a file: {path}",
                    execution_time=time.time() - start_time
                )

            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                return ToolResult(
                    success=False,
                    tool=ToolType.READ,
                    output=None,
                    error=f"File too large: {file_size / 1024 / 1024:.2f}MB (max: {self.max_file_size / 1024 / 1024}MB)",
                    execution_time=time.time() - start_time
                )

            # Read file
            content = path.read_text(encoding=encoding)
            lines = content.splitlines(keepends=True)
            total_lines = len(lines)

            # Apply line range if specified
            if line_start is not None or line_end is not None:
                start = (line_start or 1) - 1  # Convert to 0-indexed
                end = line_end or total_lines
                lines = lines[start:end]
                content = ''.join(lines)

            # Add line numbers
            numbered_content = ""
            start_num = line_start or 1
            for i, line in enumerate(lines):
                numbered_content += f"{start_num + i:6d}\t{line}"

            return ToolResult(
                success=True,
                tool=ToolType.READ,
                output=numbered_content,
                metadata={
                    "path": str(path),
                    "size": file_size,
                    "total_lines": total_lines,
                    "lines_returned": len(lines),
                    "encoding": encoding
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.READ,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # EDIT TOOL - Make targeted string replacements
    # ═══════════════════════════════════════════════════════════════════════

    async def edit(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False
    ) -> ToolResult:
        """
        Make targeted string replacement in a file.

        Args:
            file_path: Path to the file
            old_string: The exact string to find and replace
            new_string: The replacement string
            replace_all: If True, replace all occurrences; else replace first only

        Returns:
            ToolResult with edit status
        """
        start_time = time.time()
        try:
            path = self._resolve_path(file_path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    tool=ToolType.EDIT,
                    output=None,
                    error=f"File not found: {path}",
                    execution_time=time.time() - start_time
                )

            # Read current content
            content = path.read_text(encoding='utf-8')

            # Check if old_string exists
            if old_string not in content:
                return ToolResult(
                    success=False,
                    tool=ToolType.EDIT,
                    output=None,
                    error=f"String not found in file. Make sure the string matches exactly (including whitespace).",
                    metadata={"searched_for": old_string[:100]},
                    execution_time=time.time() - start_time
                )

            # Count occurrences
            occurrences = content.count(old_string)

            # Check for uniqueness if not replacing all
            if not replace_all and occurrences > 1:
                return ToolResult(
                    success=False,
                    tool=ToolType.EDIT,
                    output=None,
                    error=f"String found {occurrences} times. Use replace_all=True or provide more context to make it unique.",
                    metadata={"occurrences": occurrences},
                    execution_time=time.time() - start_time
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements_made = occurrences
            else:
                new_content = content.replace(old_string, new_string, 1)
                replacements_made = 1

            # Write back
            path.write_text(new_content, encoding='utf-8')

            return ToolResult(
                success=True,
                tool=ToolType.EDIT,
                output=f"Successfully replaced {replacements_made} occurrence(s)",
                metadata={
                    "path": str(path),
                    "replacements": replacements_made,
                    "old_string_preview": old_string[:50],
                    "new_string_preview": new_string[:50]
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.EDIT,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # WRITE TOOL - Create or overwrite files
    # ═══════════════════════════════════════════════════════════════════════

    async def write(
        self,
        file_path: str,
        content: str,
        create_dirs: bool = True
    ) -> ToolResult:
        """
        Write content to a file.

        Args:
            file_path: Path to the file
            content: Content to write
            create_dirs: Create parent directories if they don't exist

        Returns:
            ToolResult with write status
        """
        start_time = time.time()
        try:
            path = self._resolve_path(file_path)

            # Safety check for blocked paths
            for blocked in self.blocked_paths:
                if str(path).startswith(blocked):
                    return ToolResult(
                        success=False,
                        tool=ToolType.WRITE,
                        output=None,
                        error=f"Cannot write to restricted path: {blocked}",
                        execution_time=time.time() - start_time
                    )

            # Create directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            path.write_text(content, encoding='utf-8')

            return ToolResult(
                success=True,
                tool=ToolType.WRITE,
                output=f"Successfully wrote {len(content)} bytes to {path}",
                metadata={
                    "path": str(path),
                    "size": len(content),
                    "lines": content.count('\n') + 1
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.WRITE,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # BASH TOOL - Execute shell commands
    # ═══════════════════════════════════════════════════════════════════════

    async def bash(
        self,
        command: str,
        timeout: int = 60,
        cwd: Optional[str] = None
    ) -> ToolResult:
        """
        Execute a shell command.

        Args:
            command: The command to execute
            timeout: Timeout in seconds (default: 60)
            cwd: Working directory for the command

        Returns:
            ToolResult with command output
        """
        start_time = time.time()

        # Blocked commands for safety
        blocked_commands = ['rm -rf /', 'mkfs', 'dd if=', ':(){', 'fork bomb']
        for blocked in blocked_commands:
            if blocked in command.lower():
                return ToolResult(
                    success=False,
                    tool=ToolType.BASH,
                    output=None,
                    error=f"Command blocked for safety: {blocked}",
                    execution_time=time.time() - start_time
                )

        try:
            work_dir = cwd or str(self.working_dir)

            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(
                    success=False,
                    tool=ToolType.BASH,
                    output=None,
                    error=f"Command timed out after {timeout} seconds",
                    execution_time=time.time() - start_time
                )

            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            # Store in history
            self.command_history.append({
                "command": command,
                "returncode": process.returncode,
                "timestamp": time.time()
            })

            # Truncate very long output
            max_output = 50000
            if len(stdout_str) > max_output:
                stdout_str = stdout_str[:max_output] + f"\n... (truncated, {len(stdout_str)} total chars)"

            output = stdout_str
            if stderr_str:
                output += f"\n--- STDERR ---\n{stderr_str}"

            return ToolResult(
                success=process.returncode == 0,
                tool=ToolType.BASH,
                output=output,
                error=stderr_str if process.returncode != 0 else None,
                metadata={
                    "command": command,
                    "returncode": process.returncode,
                    "cwd": work_dir
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.BASH,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # GREP TOOL - Search for patterns in code
    # ═══════════════════════════════════════════════════════════════════════

    async def grep(
        self,
        pattern: str,
        path: Optional[str] = None,
        file_pattern: str = "*",
        case_insensitive: bool = False,
        context_lines: int = 0,
        max_results: int = 100
    ) -> ToolResult:
        """
        Search for a pattern in files.

        Args:
            pattern: Regex pattern to search for
            path: Directory to search in (default: working_dir)
            file_pattern: Glob pattern for files to search (e.g., "*.py")
            case_insensitive: Case-insensitive search
            context_lines: Number of context lines before/after match
            max_results: Maximum number of results to return

        Returns:
            ToolResult with search results
        """
        start_time = time.time()
        try:
            search_path = self._resolve_path(path) if path else self.working_dir

            if not search_path.exists():
                return ToolResult(
                    success=False,
                    tool=ToolType.GREP,
                    output=None,
                    error=f"Path not found: {search_path}",
                    execution_time=time.time() - start_time
                )

            # Compile regex
            flags = re.IGNORECASE if case_insensitive else 0
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return ToolResult(
                    success=False,
                    tool=ToolType.GREP,
                    output=None,
                    error=f"Invalid regex pattern: {e}",
                    execution_time=time.time() - start_time
                )

            results = []
            files_searched = 0

            # Search files
            if search_path.is_file():
                files_to_search = [search_path]
            else:
                files_to_search = list(search_path.rglob(file_pattern))

            for file_path in files_to_search:
                if not file_path.is_file():
                    continue
                if file_path.suffix not in self.allowed_extensions:
                    continue

                files_searched += 1

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.splitlines()

                    for i, line in enumerate(lines):
                        if regex.search(line):
                            # Get context
                            start = max(0, i - context_lines)
                            end = min(len(lines), i + context_lines + 1)

                            match_info = {
                                "file": str(file_path.relative_to(self.working_dir) if file_path.is_relative_to(self.working_dir) else file_path),
                                "line": i + 1,
                                "content": line.strip(),
                            }

                            if context_lines > 0:
                                match_info["context"] = lines[start:end]

                            results.append(match_info)

                            if len(results) >= max_results:
                                break

                    if len(results) >= max_results:
                        break

                except Exception:
                    continue

            # Format output
            output_lines = []
            for r in results:
                output_lines.append(f"{r['file']}:{r['line']}: {r['content']}")

            return ToolResult(
                success=True,
                tool=ToolType.GREP,
                output="\n".join(output_lines) if output_lines else "No matches found",
                metadata={
                    "pattern": pattern,
                    "matches": len(results),
                    "files_searched": files_searched,
                    "results": results[:20]  # Include detailed results for first 20
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.GREP,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # GLOB TOOL - Find files by pattern
    # ═══════════════════════════════════════════════════════════════════════

    async def glob(
        self,
        pattern: str,
        path: Optional[str] = None,
        include_hidden: bool = False,
        max_results: int = 200
    ) -> ToolResult:
        """
        Find files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py", "src/**/*.js")
            path: Base directory (default: working_dir)
            include_hidden: Include hidden files/directories
            max_results: Maximum number of results

        Returns:
            ToolResult with matching files
        """
        start_time = time.time()
        try:
            search_path = self._resolve_path(path) if path else self.working_dir

            if not search_path.exists():
                return ToolResult(
                    success=False,
                    tool=ToolType.GLOB,
                    output=None,
                    error=f"Path not found: {search_path}",
                    execution_time=time.time() - start_time
                )

            # Find matching files
            matches = []
            for file_path in search_path.rglob(pattern):
                # Skip hidden files unless requested
                if not include_hidden and any(part.startswith('.') for part in file_path.parts):
                    continue

                try:
                    rel_path = file_path.relative_to(self.working_dir) if file_path.is_relative_to(self.working_dir) else file_path
                    stat = file_path.stat()

                    matches.append({
                        "path": str(rel_path),
                        "type": "file" if file_path.is_file() else "directory",
                        "size": stat.st_size if file_path.is_file() else None,
                        "modified": stat.st_mtime
                    })

                    if len(matches) >= max_results:
                        break
                except Exception:
                    continue

            # Sort by modification time (newest first)
            matches.sort(key=lambda x: x.get("modified", 0), reverse=True)

            # Format output
            output_lines = []
            for m in matches:
                size_str = f" ({m['size']:,} bytes)" if m.get('size') else ""
                output_lines.append(f"{m['path']}{size_str}")

            return ToolResult(
                success=True,
                tool=ToolType.GLOB,
                output="\n".join(output_lines) if output_lines else "No matching files found",
                metadata={
                    "pattern": pattern,
                    "matches": len(matches),
                    "files": matches[:50]  # Include details for first 50
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.GLOB,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # TODO TOOL - Track tasks visibly
    # ═══════════════════════════════════════════════════════════════════════

    async def todo_write(
        self,
        todos: List[Dict[str, str]]
    ) -> ToolResult:
        """
        Update the todo list.

        Args:
            todos: List of todo items with content, status, and activeForm
                   status: "pending", "in_progress", "completed"

        Returns:
            ToolResult with updated todo list
        """
        start_time = time.time()
        try:
            # Clear existing todos and add new ones
            self.todos.clear()

            for i, todo in enumerate(todos):
                todo_id = f"todo_{i}_{int(time.time())}"
                self.todos[todo_id] = TodoItem(
                    id=todo_id,
                    content=todo.get("content", ""),
                    status=todo.get("status", "pending"),
                    created_at=time.time(),
                    updated_at=time.time(),
                    metadata={"activeForm": todo.get("activeForm", "")}
                )

            # Format output
            output_lines = ["📋 **Task List Updated**\n"]
            for todo_id, item in self.todos.items():
                status_icon = {
                    "pending": "⬜",
                    "in_progress": "🔄",
                    "completed": "✅"
                }.get(item.status, "⬜")
                output_lines.append(f"{status_icon} {item.content}")

            return ToolResult(
                success=True,
                tool=ToolType.TODO,
                output="\n".join(output_lines),
                metadata={
                    "total": len(self.todos),
                    "pending": sum(1 for t in self.todos.values() if t.status == "pending"),
                    "in_progress": sum(1 for t in self.todos.values() if t.status == "in_progress"),
                    "completed": sum(1 for t in self.todos.values() if t.status == "completed")
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.TODO,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def todo_get(self) -> ToolResult:
        """Get current todo list"""
        start_time = time.time()

        output_lines = ["📋 **Current Tasks**\n"]
        for item in self.todos.values():
            status_icon = {
                "pending": "⬜",
                "in_progress": "🔄",
                "completed": "✅"
            }.get(item.status, "⬜")
            output_lines.append(f"{status_icon} {item.content}")

        if len(self.todos) == 0:
            output_lines.append("No tasks")

        return ToolResult(
            success=True,
            tool=ToolType.TODO,
            output="\n".join(output_lines),
            metadata={"total": len(self.todos)},
            execution_time=time.time() - start_time
        )

    # ═══════════════════════════════════════════════════════════════════════
    # WEB SEARCH TOOL - Search the web
    # ═══════════════════════════════════════════════════════════════════════

    async def web_search(
        self,
        query: str,
        max_results: int = 5
    ) -> ToolResult:
        """
        Search the web (requires external API or fallback to limited search).

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            ToolResult with search results
        """
        start_time = time.time()

        # Check for DuckDuckGo instant answer API (no API key needed)
        if not AIOHTTP_AVAILABLE:
            return ToolResult(
                success=False,
                tool=ToolType.WEB_SEARCH,
                output=None,
                error="Web search requires aiohttp. Install with: pip install aiohttp",
                execution_time=time.time() - start_time
            )

        try:
            async with aiohttp.ClientSession() as session:
                # Use DuckDuckGo instant answer API
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                }

                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            tool=ToolType.WEB_SEARCH,
                            output=None,
                            error=f"Search API returned status {response.status}",
                            execution_time=time.time() - start_time
                        )

                    data = await response.json()

                    results = []

                    # Abstract (main result)
                    if data.get("Abstract"):
                        results.append({
                            "title": data.get("Heading", "Result"),
                            "snippet": data["Abstract"],
                            "url": data.get("AbstractURL", "")
                        })

                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:max_results - 1]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append({
                                "title": topic.get("Text", "")[:50],
                                "snippet": topic.get("Text", ""),
                                "url": topic.get("FirstURL", "")
                            })

                    if not results:
                        return ToolResult(
                            success=True,
                            tool=ToolType.WEB_SEARCH,
                            output="No results found for this query. Try a different search term.",
                            metadata={"query": query, "results": 0},
                            execution_time=time.time() - start_time
                        )

                    # Format output
                    output_lines = [f"🔍 **Search results for:** {query}\n"]
                    for i, r in enumerate(results, 1):
                        output_lines.append(f"{i}. **{r['title']}**")
                        output_lines.append(f"   {r['snippet'][:200]}")
                        if r.get('url'):
                            output_lines.append(f"   🔗 {r['url']}")
                        output_lines.append("")

                    return ToolResult(
                        success=True,
                        tool=ToolType.WEB_SEARCH,
                        output="\n".join(output_lines),
                        metadata={
                            "query": query,
                            "results": len(results),
                            "results_data": results
                        },
                        execution_time=time.time() - start_time
                    )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.WEB_SEARCH,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # WEB FETCH TOOL - Fetch and parse web pages
    # ═══════════════════════════════════════════════════════════════════════

    async def web_fetch(
        self,
        url: str,
        extract_text: bool = True
    ) -> ToolResult:
        """
        Fetch a web page and optionally extract text content.

        Args:
            url: URL to fetch
            extract_text: If True, extract readable text; else return raw HTML

        Returns:
            ToolResult with page content
        """
        start_time = time.time()

        if not AIOHTTP_AVAILABLE:
            return ToolResult(
                success=False,
                tool=ToolType.WEB_FETCH,
                output=None,
                error="Web fetch requires aiohttp. Install with: pip install aiohttp",
                execution_time=time.time() - start_time
            )

        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return ToolResult(
                    success=False,
                    tool=ToolType.WEB_FETCH,
                    output=None,
                    error="Invalid URL format",
                    execution_time=time.time() - start_time
                )

            async with aiohttp.ClientSession() as session:
                headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; JarvisBot/1.0)"
                }

                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            tool=ToolType.WEB_FETCH,
                            output=None,
                            error=f"HTTP {response.status}: {response.reason}",
                            execution_time=time.time() - start_time
                        )

                    content = await response.text()

                    if extract_text and BS4_AVAILABLE:
                        # Parse and extract text
                        soup = BeautifulSoup(content, 'html.parser')

                        # Remove script and style elements
                        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                            element.decompose()

                        # Get title
                        title = soup.title.string if soup.title else "No title"

                        # Get main content
                        text = soup.get_text(separator='\n', strip=True)

                        # Clean up whitespace
                        lines = [line.strip() for line in text.splitlines() if line.strip()]
                        text = '\n'.join(lines)

                        # Truncate if too long
                        if len(text) > 10000:
                            text = text[:10000] + "\n... (content truncated)"

                        output = f"📄 **{title}**\n\n{text}"
                    else:
                        output = content[:10000]
                        if len(content) > 10000:
                            output += "\n... (content truncated)"

                    return ToolResult(
                        success=True,
                        tool=ToolType.WEB_FETCH,
                        output=output,
                        metadata={
                            "url": url,
                            "status": response.status,
                            "content_type": response.headers.get("Content-Type", ""),
                            "content_length": len(content)
                        },
                        execution_time=time.time() - start_time
                    )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.WEB_FETCH,
                output=None,
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ═══════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path string to an absolute Path"""
        path = Path(path_str)
        if not path.is_absolute():
            path = self.working_dir / path
        return path.resolve()

    def get_tool_help(self) -> str:
        """Get help text for all available tools"""
        return """
📚 **JARVIS Tools Reference**

**Read** - Read files from disk
  `read(file_path, line_start=None, line_end=None)`
  Example: "Read the file config.py"

**Edit** - Make targeted string replacements
  `edit(file_path, old_string, new_string, replace_all=False)`
  Example: "Replace 'DEBUG = False' with 'DEBUG = True' in settings.py"

**Write** - Create or overwrite files
  `write(file_path, content)`
  Example: "Create a new file called utils.py with..."

**Bash** - Execute shell commands
  `bash(command, timeout=60)`
  Example: "Run 'git status'"

**Grep** - Search for patterns in code
  `grep(pattern, path=None, file_pattern="*")`
  Example: "Search for 'TODO' in all Python files"

**Glob** - Find files by pattern
  `glob(pattern, path=None)`
  Example: "Find all *.py files in src/"

**Todo** - Track tasks
  `todo_write(todos)` / `todo_get()`
  Example: "Add task: Implement login feature"

**WebSearch** - Search the web
  `web_search(query)`
  Example: "Search for Python async best practices"

**WebFetch** - Fetch web pages
  `web_fetch(url)`
  Example: "Fetch the documentation at https://..."
"""


# Global instance for convenience
_tools_instance: Optional[JarvisTools] = None


def get_jarvis_tools(working_directory: Optional[str] = None) -> JarvisTools:
    """Get or create the global JarvisTools instance"""
    global _tools_instance
    if _tools_instance is None:
        _tools_instance = JarvisTools(working_directory)
    return _tools_instance
