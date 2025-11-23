"""
Tool Registration System for JARVIS AI Agent

Provides decorator-based tool registration with automatic schema generation,
agent-based access control, and built-in tool implementations.
"""

import asyncio
import inspect
import json
import os
import subprocess
import tempfile
import functools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    get_type_hints,
    get_origin,
    get_args,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
)

# Python 3.9+ has Annotated in typing, earlier versions need typing_extensions
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    httpx = None


class ToolCategory(Enum):
    """Categories for organizing tools"""
    WEB = "web"
    FILE = "file"
    CODE = "code"
    DATA = "data"
    SYSTEM = "system"
    CUSTOM = "custom"


class ToolPermission(Enum):
    """Permission levels for tool access"""
    PUBLIC = "public"  # Any agent can use
    RESTRICTED = "restricted"  # Only specified agents
    ADMIN = "admin"  # Only admin agents


@dataclass
class ParameterInfo:
    """Information about a tool parameter"""
    name: str
    type_hint: Type
    description: str = ""
    default: Any = inspect.Parameter.empty
    required: bool = True

    def to_json_schema(self) -> Dict[str, Any]:
        """Convert parameter to JSON schema format"""
        schema = self._type_to_schema(self.type_hint)
        if self.description:
            schema["description"] = self.description
        return schema

    def _type_to_schema(self, type_hint: Type) -> Dict[str, Any]:
        """Convert Python type hint to JSON schema"""
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # Handle Optional types
        if origin is Union:
            # Check if it's Optional (Union with None)
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return self._type_to_schema(non_none_args[0])
            # General Union
            return {"oneOf": [self._type_to_schema(a) for a in non_none_args]}

        # Handle List types
        if origin is list:
            item_type = args[0] if args else Any
            return {
                "type": "array",
                "items": self._type_to_schema(item_type)
            }

        # Handle Dict types
        if origin is dict:
            return {"type": "object"}

        # Handle basic types
        type_map = {
            str: {"type": "string"},
            int: {"type": "integer"},
            float: {"type": "number"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
            Any: {},
        }

        return type_map.get(type_hint, {"type": "string"})


@dataclass
class ToolDefinition:
    """Complete definition of a registered tool"""
    name: str
    description: str
    func: Callable
    parameters: List[ParameterInfo]
    category: ToolCategory = ToolCategory.CUSTOM
    permission: ToolPermission = ToolPermission.PUBLIC
    agents: Optional[List[str]] = None  # None means all agents
    is_async: bool = False
    timeout: float = 30.0  # Default timeout in seconds
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)

    def get_openai_schema(self) -> Dict[str, Any]:
        """Generate OpenAI function calling format schema"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

    def get_anthropic_schema(self) -> Dict[str, Any]:
        """Generate Anthropic tool use format schema"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_name": self.tool_name
        }


class ToolRegistry:
    """
    Central registry for all agent tools.

    Supports:
    - Tool registration via decorator or direct registration
    - Agent-based access control
    - Schema generation for different LLM formats
    - Async and sync tool execution
    """

    _tools: Dict[str, ToolDefinition] = {}
    _categories: Dict[ToolCategory, Set[str]] = {cat: set() for cat in ToolCategory}
    _agent_tools: Dict[str, Set[str]] = {}  # agent_name -> set of tool names

    @classmethod
    def register(cls, tool_def: ToolDefinition) -> None:
        """Register a tool definition"""
        cls._tools[tool_def.name] = tool_def
        cls._categories[tool_def.category].add(tool_def.name)

        # Update agent-tool mapping
        if tool_def.agents:
            for agent in tool_def.agents:
                if agent not in cls._agent_tools:
                    cls._agent_tools[agent] = set()
                cls._agent_tools[agent].add(tool_def.name)

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister a tool by name"""
        if name not in cls._tools:
            return False

        tool_def = cls._tools[name]
        cls._categories[tool_def.category].discard(name)

        # Remove from agent mappings
        for agent_tools in cls._agent_tools.values():
            agent_tools.discard(name)

        del cls._tools[name]
        return True

    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name"""
        return cls._tools.get(name)

    @classmethod
    def get_all_tools(cls) -> List[ToolDefinition]:
        """Get all registered tools"""
        return list(cls._tools.values())

    @classmethod
    def get_tools_for_agent(cls, agent_name: str) -> List[ToolDefinition]:
        """
        Get tools available for a specific agent.

        Returns tools that either:
        - Have no agent restriction (agents=None)
        - Explicitly include this agent in their agents list
        """
        available = []
        for tool in cls._tools.values():
            if tool.agents is None or agent_name in tool.agents:
                available.append(tool)
        return available

    @classmethod
    def get_tools_by_category(cls, category: ToolCategory) -> List[ToolDefinition]:
        """Get all tools in a specific category"""
        tool_names = cls._categories.get(category, set())
        return [cls._tools[name] for name in tool_names if name in cls._tools]

    @classmethod
    def get_tool_schemas(
        cls,
        agent_name: str,
        format: str = "openai"
    ) -> List[Dict[str, Any]]:
        """
        Get tool schemas for a specific agent.

        Args:
            agent_name: Name of the agent
            format: Schema format - "openai" or "anthropic"

        Returns:
            List of tool schemas in the specified format
        """
        tools = cls.get_tools_for_agent(agent_name)

        if format == "openai":
            return [tool.get_openai_schema() for tool in tools]
        elif format == "anthropic":
            return [tool.get_anthropic_schema() for tool in tools]
        else:
            raise ValueError(f"Unknown schema format: {format}")

    @classmethod
    async def execute_tool(
        cls,
        name: str,
        agent_name: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            name: Tool name
            agent_name: Optional agent name for permission checking
            **kwargs: Tool arguments

        Returns:
            ToolResult with execution outcome
        """
        import time
        start_time = time.time()

        tool = cls._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' not found",
                tool_name=name
            )

        # Check agent permission
        if agent_name and tool.agents and agent_name not in tool.agents:
            return ToolResult(
                success=False,
                error=f"Agent '{agent_name}' not authorized to use tool '{name}'",
                tool_name=name
            )

        try:
            # Execute with timeout
            if tool.is_async:
                result = await asyncio.wait_for(
                    tool.func(**kwargs),
                    timeout=tool.timeout
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: tool.func(**kwargs)),
                    timeout=tool.timeout
                )

            execution_time = time.time() - start_time
            return ToolResult(
                success=True,
                result=result,
                execution_time=execution_time,
                tool_name=name
            )

        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' timed out after {tool.timeout}s",
                execution_time=tool.timeout,
                tool_name=name
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return ToolResult(
                success=False,
                error=f"Tool '{name}' failed: {str(e)}",
                execution_time=execution_time,
                tool_name=name
            )

    @classmethod
    def execute_tool_sync(cls, name: str, agent_name: Optional[str] = None, **kwargs) -> ToolResult:
        """Synchronous version of execute_tool"""
        return asyncio.run(cls.execute_tool(name, agent_name, **kwargs))

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (useful for testing)"""
        cls._tools.clear()
        cls._categories = {cat: set() for cat in ToolCategory}
        cls._agent_tools.clear()

    @classmethod
    def list_tools(cls) -> List[str]:
        """List all registered tool names"""
        return list(cls._tools.keys())

    @classmethod
    def tool_exists(cls, name: str) -> bool:
        """Check if a tool exists"""
        return name in cls._tools


def _extract_parameter_info(func: Callable) -> List[ParameterInfo]:
    """Extract parameter information from function signature and type hints"""
    sig = inspect.signature(func)
    hints = get_type_hints(func, include_extras=True)

    params = []
    for name, param in sig.parameters.items():
        if name in ('self', 'cls'):
            continue

        type_hint = hints.get(name, Any)
        description = ""

        # Check if type hint is Annotated
        if get_origin(type_hint) is Annotated:
            args = get_args(type_hint)
            type_hint = args[0]
            # Look for string annotation as description
            for arg in args[1:]:
                if isinstance(arg, str):
                    description = arg
                    break

        has_default = param.default is not inspect.Parameter.empty

        params.append(ParameterInfo(
            name=name,
            type_hint=type_hint,
            description=description,
            default=param.default if has_default else inspect.Parameter.empty,
            required=not has_default
        ))

    return params


def tool(
    name: str = None,
    description: str = None,
    agents: List[str] = None,
    category: ToolCategory = ToolCategory.CUSTOM,
    permission: ToolPermission = ToolPermission.PUBLIC,
    timeout: float = 30.0,
    tags: List[str] = None,
    version: str = "1.0.0"
):
    """
    Decorator to register a function as an agent tool.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        agents: List of agents that can use this tool (None = all)
        category: Tool category for organization
        permission: Permission level
        timeout: Execution timeout in seconds
        tags: Optional tags for searching/filtering
        version: Tool version string

    Usage:
        @tool(
            name="search_web",
            description="Search the web for information",
            agents=["researcher"]
        )
        def search_web(
            query: Annotated[str, "The search query"],
            num_results: Annotated[int, "Number of results"] = 5
        ) -> str:
            # Implementation
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Extract metadata
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or "").strip()

        # Check if function is async
        is_async = asyncio.iscoroutinefunction(func)

        # Extract parameter info
        parameters = _extract_parameter_info(func)

        # Create tool definition
        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_description,
            func=func,
            parameters=parameters,
            category=category,
            permission=permission,
            agents=agents,
            is_async=is_async,
            timeout=timeout,
            tags=tags or [],
            version=version
        )

        # Register the tool
        ToolRegistry.register(tool_def)

        # Preserve original function
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return async_wrapper if is_async else wrapper

    return decorator


# ============================================================================
# Built-in Tools
# ============================================================================

@tool(
    name="web_search",
    description="Search the web for information using a search query",
    category=ToolCategory.WEB,
    agents=["researcher", "assistant", "web_agent"],
    tags=["search", "web", "information"]
)
async def web_search(
    query: Annotated[str, "The search query to execute"],
    num_results: Annotated[int, "Maximum number of results to return"] = 5,
    search_type: Annotated[str, "Type of search: 'general', 'news', 'images'"] = "general"
) -> Dict[str, Any]:
    """
    Search the web for information.

    This is a placeholder implementation. In production, integrate with
    actual search APIs (Google, Bing, DuckDuckGo, etc.)
    """
    # Placeholder - would integrate with actual search API
    return {
        "query": query,
        "num_results": num_results,
        "search_type": search_type,
        "results": [
            {
                "title": f"Result {i+1} for: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a placeholder result for '{query}'"
            }
            for i in range(min(num_results, 5))
        ],
        "status": "placeholder",
        "message": "Integrate with actual search API for real results"
    }


@tool(
    name="file_read",
    description="Read the contents of a file from the filesystem",
    category=ToolCategory.FILE,
    agents=["coder", "assistant", "file_agent"],
    tags=["file", "read", "filesystem"],
    timeout=10.0
)
def file_read(
    path: Annotated[str, "Path to the file to read"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
    max_size: Annotated[int, "Maximum file size in bytes to read"] = 1_000_000
) -> Dict[str, Any]:
    """
    Read contents of a file.

    Includes safety checks for file size and restricted paths.
    """
    import os

    # Security: Normalize and validate path
    path = os.path.abspath(os.path.expanduser(path))

    # Check for restricted paths (customize as needed)
    restricted_prefixes = ['/etc/shadow', '/etc/passwd', '/root']
    for restricted in restricted_prefixes:
        if path.startswith(restricted):
            return {
                "success": False,
                "error": f"Access to '{restricted}' is restricted",
                "path": path
            }

    if not os.path.exists(path):
        return {
            "success": False,
            "error": f"File not found: {path}",
            "path": path
        }

    if not os.path.isfile(path):
        return {
            "success": False,
            "error": f"Path is not a file: {path}",
            "path": path
        }

    # Check file size
    file_size = os.path.getsize(path)
    if file_size > max_size:
        return {
            "success": False,
            "error": f"File too large: {file_size} bytes (max: {max_size})",
            "path": path,
            "file_size": file_size
        }

    try:
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()

        return {
            "success": True,
            "path": path,
            "content": content,
            "size": len(content),
            "encoding": encoding
        }
    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"Could not decode file with encoding '{encoding}'",
            "path": path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": path
        }


@tool(
    name="file_write",
    description="Write content to a file on the filesystem",
    category=ToolCategory.FILE,
    agents=["coder", "assistant", "file_agent"],
    permission=ToolPermission.RESTRICTED,
    tags=["file", "write", "filesystem"],
    timeout=10.0
)
def file_write(
    path: Annotated[str, "Path to the file to write"],
    content: Annotated[str, "Content to write to the file"],
    encoding: Annotated[str, "File encoding"] = "utf-8",
    mode: Annotated[str, "Write mode: 'overwrite' or 'append'"] = "overwrite",
    create_dirs: Annotated[bool, "Create parent directories if they don't exist"] = False
) -> Dict[str, Any]:
    """
    Write content to a file.

    Supports both overwrite and append modes with optional directory creation.
    """
    import os

    # Security: Normalize and validate path
    path = os.path.abspath(os.path.expanduser(path))

    # Check for restricted paths
    restricted_prefixes = ['/etc', '/bin', '/sbin', '/usr/bin', '/usr/sbin', '/root']
    for restricted in restricted_prefixes:
        if path.startswith(restricted):
            return {
                "success": False,
                "error": f"Writing to '{restricted}' is restricted",
                "path": path
            }

    # Create parent directories if requested
    parent_dir = os.path.dirname(path)
    if create_dirs and parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not create directories: {e}",
                "path": path
            }

    try:
        write_mode = 'a' if mode == 'append' else 'w'
        with open(path, write_mode, encoding=encoding) as f:
            f.write(content)

        return {
            "success": True,
            "path": path,
            "bytes_written": len(content.encode(encoding)),
            "mode": mode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": path
        }


@tool(
    name="code_execute",
    description="Execute code in a sandboxed environment",
    category=ToolCategory.CODE,
    agents=["coder", "executor"],
    permission=ToolPermission.ADMIN,
    tags=["code", "execute", "sandbox"],
    timeout=60.0
)
def code_execute(
    code: Annotated[str, "The code to execute"],
    language: Annotated[str, "Programming language: 'python', 'javascript', 'bash'"] = "python",
    timeout: Annotated[int, "Execution timeout in seconds"] = 30,
    capture_output: Annotated[bool, "Capture stdout/stderr"] = True
) -> Dict[str, Any]:
    """
    Execute code in a sandboxed environment.

    Currently supports Python, JavaScript (Node.js), and Bash.
    Uses subprocess with resource limits for safety.
    """
    import resource
    import signal

    supported_languages = {
        "python": ["python3", "-c"],
        "javascript": ["node", "-e"],
        "bash": ["bash", "-c"]
    }

    if language not in supported_languages:
        return {
            "success": False,
            "error": f"Unsupported language: {language}. Supported: {list(supported_languages.keys())}",
            "language": language
        }

    # Create command
    cmd = supported_languages[language] + [code]

    try:
        # Create subprocess with resource limits
        def set_limits():
            # Limit CPU time
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
            # Limit memory (100MB)
            resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))
            # Limit file creation
            resource.setrlimit(resource.RLIMIT_FSIZE, (10 * 1024 * 1024, 10 * 1024 * 1024))

        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            timeout=timeout,
            text=True,
            preexec_fn=set_limits if os.name != 'nt' else None  # Resource limits on Unix only
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout if capture_output else None,
            "stderr": result.stderr if capture_output else None,
            "language": language
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution timed out after {timeout} seconds",
            "language": language
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Interpreter for '{language}' not found",
            "language": language
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "language": language
        }


@tool(
    name="http_request",
    description="Make an HTTP request to a URL",
    category=ToolCategory.WEB,
    agents=["researcher", "assistant", "web_agent", "api_agent"],
    tags=["http", "api", "web", "request"],
    timeout=30.0
)
async def http_request(
    url: Annotated[str, "The URL to request"],
    method: Annotated[str, "HTTP method: GET, POST, PUT, DELETE, PATCH"] = "GET",
    headers: Annotated[Optional[Dict[str, str]], "Request headers"] = None,
    body: Annotated[Optional[str], "Request body (for POST/PUT/PATCH)"] = None,
    timeout: Annotated[int, "Request timeout in seconds"] = 30
) -> Dict[str, Any]:
    """
    Make an HTTP request to a URL.

    Supports common HTTP methods and custom headers.
    Requires httpx library for async requests.
    """
    if not HAS_HTTPX:
        return {
            "success": False,
            "error": "httpx library not installed. Install with: pip install httpx",
            "url": url
        }

    method = method.upper()
    valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

    if method not in valid_methods:
        return {
            "success": False,
            "error": f"Invalid HTTP method: {method}. Valid: {valid_methods}",
            "url": url
        }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body
            )

            # Try to parse JSON response
            try:
                response_body = response.json()
            except json.JSONDecodeError:
                response_body = response.text

            return {
                "success": True,
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body
            }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": f"Request timed out after {timeout} seconds",
            "url": url
        }
    except httpx.RequestError as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


# ============================================================================
# Additional Utility Tools
# ============================================================================

@tool(
    name="list_directory",
    description="List contents of a directory",
    category=ToolCategory.FILE,
    agents=["coder", "assistant", "file_agent"],
    tags=["file", "directory", "list"]
)
def list_directory(
    path: Annotated[str, "Path to the directory"] = ".",
    pattern: Annotated[str, "Glob pattern to filter files"] = "*",
    include_hidden: Annotated[bool, "Include hidden files"] = False,
    recursive: Annotated[bool, "List recursively"] = False
) -> Dict[str, Any]:
    """
    List contents of a directory with optional filtering.
    """
    import os
    import glob

    path = os.path.abspath(os.path.expanduser(path))

    if not os.path.exists(path):
        return {
            "success": False,
            "error": f"Directory not found: {path}",
            "path": path
        }

    if not os.path.isdir(path):
        return {
            "success": False,
            "error": f"Path is not a directory: {path}",
            "path": path
        }

    try:
        if recursive:
            search_pattern = os.path.join(path, "**", pattern)
            entries = glob.glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(path, pattern)
            entries = glob.glob(search_pattern)

        # Filter hidden files if requested
        if not include_hidden:
            entries = [e for e in entries if not os.path.basename(e).startswith('.')]

        # Get file info
        items = []
        for entry in sorted(entries):
            stat = os.stat(entry)
            items.append({
                "name": os.path.basename(entry),
                "path": entry,
                "type": "directory" if os.path.isdir(entry) else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return {
            "success": True,
            "path": path,
            "pattern": pattern,
            "count": len(items),
            "items": items
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "path": path
        }


@tool(
    name="json_parse",
    description="Parse and extract data from JSON",
    category=ToolCategory.DATA,
    agents=None,  # Available to all agents
    tags=["json", "parse", "data"]
)
def json_parse(
    data: Annotated[str, "JSON string to parse"],
    path: Annotated[str, "JSONPath-like expression to extract (e.g., 'key.subkey.0')"] = None
) -> Dict[str, Any]:
    """
    Parse JSON and optionally extract nested data.
    """
    try:
        parsed = json.loads(data)

        if path:
            # Simple path navigation (not full JSONPath)
            current = parsed
            for key in path.split('.'):
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list) and key.isdigit():
                    idx = int(key)
                    if 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return {
                            "success": False,
                            "error": f"Index {idx} out of range"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"Key '{key}' not found"
                    }
            return {
                "success": True,
                "result": current,
                "path": path
            }

        return {
            "success": True,
            "result": parsed
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}"
        }


@tool(
    name="shell_command",
    description="Execute a shell command (restricted)",
    category=ToolCategory.SYSTEM,
    permission=ToolPermission.ADMIN,
    agents=["admin", "system_agent"],
    tags=["shell", "command", "system"],
    timeout=60.0
)
def shell_command(
    command: Annotated[str, "The shell command to execute"],
    working_dir: Annotated[str, "Working directory for command execution"] = None,
    timeout: Annotated[int, "Command timeout in seconds"] = 30
) -> Dict[str, Any]:
    """
    Execute a shell command with safety restrictions.

    Uses argument list execution (shell=False) to prevent command injection.
    Dangerous commands are blocked.
    """
    import shlex

    # List of blocked commands/patterns
    blocked_patterns = [
        'rm -rf /',
        'rm -rf /*',
        'dd if=',
        ':(){:|:&};:',  # Fork bomb
        'mkfs',
        'chmod 777 /',
        '> /dev/sda',
        '$(', '`',  # Command substitution
        '; ', ' && ', ' || ',  # Command chaining (with spaces)
        '| ', ' |',  # Pipe operators
    ]

    command_lower = command.lower()
    for pattern in blocked_patterns:
        if pattern in command_lower:
            return {
                "success": False,
                "error": f"Blocked dangerous command pattern: {pattern}",
                "command": command
            }

    try:
        # Parse command into safe argument list to prevent shell injection
        try:
            args = shlex.split(command)
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid command syntax: {e}",
                "command": command
            }

        if not args:
            return {
                "success": False,
                "error": "Empty command",
                "command": command
            }

        # Execute with shell=False for security
        result = subprocess.run(
            args,
            shell=False,  # SECURITY: Prevent shell injection
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": command
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"Command not found: {args[0] if args else command}",
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": command
        }


# ============================================================================
# Tool Discovery and Documentation
# ============================================================================

def get_tool_documentation() -> str:
    """Generate documentation for all registered tools"""
    docs = ["# Available Tools\n"]

    for category in ToolCategory:
        tools = ToolRegistry.get_tools_by_category(category)
        if tools:
            docs.append(f"\n## {category.value.title()} Tools\n")
            for tool_def in tools:
                docs.append(f"\n### {tool_def.name}\n")
                docs.append(f"**Description:** {tool_def.description}\n")
                docs.append(f"**Permission:** {tool_def.permission.value}\n")
                if tool_def.agents:
                    docs.append(f"**Agents:** {', '.join(tool_def.agents)}\n")
                else:
                    docs.append("**Agents:** All\n")

                if tool_def.parameters:
                    docs.append("\n**Parameters:**\n")
                    for param in tool_def.parameters:
                        required = "required" if param.required else "optional"
                        default = f" (default: {param.default})" if not param.required else ""
                        docs.append(f"- `{param.name}` ({required}): {param.description}{default}\n")

    return "".join(docs)


def discover_tools(module_path: str) -> int:
    """
    Discover and load tools from a Python module.

    Args:
        module_path: Python module path (e.g., 'myapp.tools')

    Returns:
        Number of tools loaded
    """
    import importlib

    initial_count = len(ToolRegistry.list_tools())

    try:
        importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_path}': {e}")

    return len(ToolRegistry.list_tools()) - initial_count


# ============================================================================
# Convenience Functions
# ============================================================================

def create_tool_from_function(
    func: Callable,
    name: str = None,
    description: str = None,
    agents: List[str] = None,
    **kwargs
) -> ToolDefinition:
    """
    Programmatically create and register a tool from a function.

    Useful when you can't use decorators.
    """
    tool_name = name or func.__name__
    tool_description = description or (func.__doc__ or "").strip()
    is_async = asyncio.iscoroutinefunction(func)
    parameters = _extract_parameter_info(func)

    tool_def = ToolDefinition(
        name=tool_name,
        description=tool_description,
        func=func,
        parameters=parameters,
        agents=agents,
        is_async=is_async,
        **kwargs
    )

    ToolRegistry.register(tool_def)
    return tool_def


async def batch_execute_tools(
    tool_calls: List[Dict[str, Any]],
    agent_name: Optional[str] = None,
    parallel: bool = True
) -> List[ToolResult]:
    """
    Execute multiple tools, optionally in parallel.

    Args:
        tool_calls: List of {"name": str, "arguments": dict}
        agent_name: Optional agent name for permission checking
        parallel: Whether to execute in parallel

    Returns:
        List of ToolResults
    """
    async def execute_single(call: Dict[str, Any]) -> ToolResult:
        return await ToolRegistry.execute_tool(
            call["name"],
            agent_name=agent_name,
            **call.get("arguments", {})
        )

    if parallel:
        results = await asyncio.gather(
            *[execute_single(call) for call in tool_calls]
        )
    else:
        results = []
        for call in tool_calls:
            result = await execute_single(call)
            results.append(result)

    return results
