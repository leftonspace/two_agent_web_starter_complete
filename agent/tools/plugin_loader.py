"""
PHASE 2.1: Tool Plugin Loader and Registry

This module provides the core plugin discovery, registration, and execution engine:
- ToolRegistry: Central registry for managing tool plugins
- Dynamic plugin discovery from directories
- Permission checking and access control
- Tool execution with timeout and error handling
- Global registry singleton

Features:
- Zero-code plugin registration (automatic discovery)
- Domain and role-based tool filtering
- Permission enforcement
- Timeout management
- Comprehensive error handling

Usage:
    from agent.tools.plugin_loader import get_global_registry

    # Get global registry (singleton)
    registry = get_global_registry()

    # Discover available tools for a domain/role
    tools = registry.get_tools_for_domain("hr", "recruiter")

    # Execute a tool
    context = ToolExecutionContext(
        mission_id="mission_123",
        project_path=Path("/path/to/project"),
        permissions=["email_send", "hris_read"]
    )
    result = await registry.execute_tool("send_email", {...}, context)
"""

from __future__ import annotations

import asyncio
import importlib.util
import inspect
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

from .base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
    create_error_result,
)

# Setup logging
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# Tool Registry
# ══════════════════════════════════════════════════════════════════════


class ToolRegistry:
    """
    Central registry for discovering, loading, and managing tool plugins.

    The registry:
    1. Scans specified directories for Python files
    2. Dynamically imports files and finds ToolPlugin subclasses
    3. Instantiates and registers tools
    4. Provides query interface for tool discovery
    5. Executes tools with validation and permission checking

    Example:
        registry = ToolRegistry()
        tools = registry.get_tools_for_domain("hr", "recruiter")
        result = await registry.execute_tool("send_email", {...}, context)
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """
        Initialize the tool registry.

        Args:
            plugin_dirs: List of directories to scan for plugins.
                        If None, uses default directories under agent/tools/
        """
        self.tools: Dict[str, ToolPlugin] = {}
        self.manifests: Dict[str, ToolManifest] = {}
        self._loaded_modules: Set[str] = set()

        # Default plugin directories
        if plugin_dirs is None:
            base_dir = Path(__file__).parent
            plugin_dirs = [
                base_dir / "builtin",   # Built-in development tools
                base_dir / "hr",        # HR department tools
                base_dir / "finance",   # Finance department tools
                base_dir / "legal",     # Legal department tools
                base_dir / "custom",    # User-defined custom tools
            ]

        self.plugin_dirs = plugin_dirs

        # Discover and load plugins
        discovered = self.discover_plugins(self.plugin_dirs)
        logger.info(f"ToolRegistry initialized: {discovered} tools discovered from {len(self.plugin_dirs)} directories")

    def discover_plugins(self, plugin_dirs: List[Path]) -> int:
        """
        Scan directories for tool plugins.

        Looks for Python files containing ToolPlugin subclasses. Each file
        can contain multiple plugin classes - all will be discovered and registered.

        Args:
            plugin_dirs: Directories to scan

        Returns:
            Count of discovered tools

        Example:
            count = registry.discover_plugins([Path("agent/tools/hr")])
            print(f"Found {count} HR tools")
        """
        count = 0

        for dir_path in plugin_dirs:
            if not dir_path.exists():
                logger.debug(f"Plugin directory not found (skipping): {dir_path}")
                continue

            if not dir_path.is_dir():
                logger.warning(f"Plugin path is not a directory (skipping): {dir_path}")
                continue

            logger.debug(f"Scanning for plugins in: {dir_path}")

            # Find all Python files (excluding __init__.py and files starting with _)
            for py_file in dir_path.glob("*.py"):
                if py_file.name.startswith("_"):
                    logger.debug(f"Skipping private file: {py_file.name}")
                    continue

                try:
                    loaded = self._load_plugin_file(py_file)
                    count += loaded
                    logger.debug(f"Loaded {loaded} plugin(s) from: {py_file.name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin file {py_file}: {e}", exc_info=True)

        return count

    def _load_plugin_file(self, file_path: Path) -> int:
        """
        Load a single plugin file using dynamic import.

        Finds all ToolPlugin subclasses in the file, instantiates them,
        and registers them.

        Args:
            file_path: Path to Python file

        Returns:
            Number of tools loaded from this file

        Raises:
            Exception: If import or instantiation fails
        """
        # Create a unique module name
        module_name = f"agent.tools.dynamic.{file_path.stem}"

        # Skip if already loaded
        if module_name in self._loaded_modules:
            logger.debug(f"Module already loaded: {module_name}")
            return 0

        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        self._loaded_modules.add(module_name)

        # Find all ToolPlugin subclasses in the module
        count = 0
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a ToolPlugin subclass (but not ToolPlugin itself)
            if issubclass(obj, ToolPlugin) and obj is not ToolPlugin:
                # Check if the class is defined in this module (not imported)
                if obj.__module__ == module_name:
                    try:
                        # Instantiate and register
                        tool_instance = obj()
                        self.register(tool_instance)
                        count += 1
                        logger.debug(f"Registered tool: {name}")
                    except Exception as e:
                        logger.error(f"Failed to instantiate tool {name}: {e}", exc_info=True)

        return count

    def register(self, tool: ToolPlugin) -> None:
        """
        Manually register a tool instance.

        Args:
            tool: ToolPlugin instance to register

        Raises:
            ValueError: If a tool with the same name is already registered

        Example:
            tool = MySendEmailTool()
            registry.register(tool)
        """
        manifest = tool.get_manifest()

        # Check for duplicate names
        if manifest.name in self.tools:
            existing_version = self.manifests[manifest.name].version
            logger.warning(
                f"Tool '{manifest.name}' already registered "
                f"(version {existing_version}). Replacing with version {manifest.version}"
            )

        self.tools[manifest.name] = tool
        self.manifests[manifest.name] = manifest
        logger.info(f"Registered tool: {manifest.name} v{manifest.version}")

    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool by name.

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if tool was unregistered, False if not found

        Example:
            if registry.unregister("deprecated_tool"):
                print("Tool removed")
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            del self.manifests[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        return False

    def get_tool(self, name: str) -> Optional[ToolPlugin]:
        """
        Get tool instance by name.

        Args:
            name: Tool name

        Returns:
            ToolPlugin instance or None if not found

        Example:
            tool = registry.get_tool("send_email")
            if tool:
                manifest = tool.get_manifest()
        """
        return self.tools.get(name)

    def get_manifest(self, name: str) -> Optional[ToolManifest]:
        """
        Get tool manifest by name.

        Args:
            name: Tool name

        Returns:
            ToolManifest or None if not found
        """
        return self.manifests.get(name)

    def get_tools_for_domain(
        self,
        domain: str,
        role: Optional[str] = None
    ) -> List[str]:
        """
        Get list of tool names available for a domain/role.

        Args:
            domain: Domain to filter by (e.g., "hr", "finance", "coding")
            role: Optional role to filter by (e.g., "manager", "employee")

        Returns:
            List of tool names available for the domain/role

        Example:
            # Get all HR tools for recruiters
            tools = registry.get_tools_for_domain("hr", "recruiter")
            for tool_name in tools:
                print(f"Available: {tool_name}")
        """
        tools = []

        for name, manifest in self.manifests.items():
            # Check domain
            if domain not in manifest.domains:
                continue

            # Check role if specified
            if role is not None and role not in manifest.roles:
                continue

            tools.append(name)

        return sorted(tools)  # Return sorted for consistency

    def check_permissions(
        self,
        tool_name: str,
        user_permissions: List[str]
    ) -> tuple[bool, Optional[str]]:
        """
        Verify user has required permissions for a tool.

        Args:
            tool_name: Name of tool to check
            user_permissions: List of permissions user has

        Returns:
            (has_permission, error_message) tuple
            - has_permission: True if user has all required permissions
            - error_message: None if authorized, error description otherwise

        Example:
            can_use, error = registry.check_permissions(
                "send_email",
                ["email_send", "hris_read"]
            )
            if not can_use:
                print(f"Access denied: {error}")
        """
        manifest = self.manifests.get(tool_name)
        if not manifest:
            return False, f"Tool '{tool_name}' not found"

        required = set(manifest.required_permissions)
        available = set(user_permissions)
        missing = required - available

        if missing:
            return False, f"Missing required permissions: {', '.join(sorted(missing))}"

        return True, None

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute a tool with validation and error handling.

        This is the main entry point for tool execution. It:
        1. Looks up the tool
        2. Checks permissions
        3. Validates input parameters
        4. Executes with timeout
        5. Validates output
        6. Returns ToolResult

        Args:
            tool_name: Name of tool to execute
            params: Input parameters (will be validated against schema)
            context: Execution context with permissions, project_path, etc.

        Returns:
            ToolResult with success status, data, and optional error

        Example:
            result = await registry.execute_tool(
                "send_email",
                {
                    "to": "candidate@example.com",
                    "subject": "Interview Invitation",
                    "body": "We'd like to invite you..."
                },
                context
            )

            if result.success:
                print(f"Email sent: {result.data['message_id']}")
            else:
                print(f"Failed: {result.error}")
        """
        # Get tool
        tool = self.get_tool(tool_name)
        if not tool:
            return create_error_result(
                f"Tool '{tool_name}' not found",
                available_tools=list(self.tools.keys())
            )

        manifest = tool.get_manifest()

        # Check permissions
        has_permission, permission_error = self.check_permissions(
            tool_name,
            context.permissions
        )
        if not has_permission:
            return create_error_result(
                f"Insufficient permissions: {permission_error}",
                required_permissions=manifest.required_permissions,
                user_permissions=context.permissions
            )

        # Validate input parameters
        is_valid, validation_error = tool.validate_params(params)
        if not is_valid:
            return create_error_result(
                f"Invalid parameters: {validation_error}",
                params=params,
                expected_schema=manifest.input_schema
            )

        # Execute with timeout
        try:
            logger.info(
                f"Executing tool '{tool_name}' for mission {context.mission_id}"
            )

            result = await asyncio.wait_for(
                tool.execute(params, context),
                timeout=manifest.timeout_seconds
            )

            # Validate output if successful
            if result.success and result.data is not None:
                output_valid, output_error = tool.validate_output(result.data)
                if not output_valid:
                    logger.warning(
                        f"Tool '{tool_name}' returned invalid output: {output_error}"
                    )
                    # Don't fail the execution, just log the warning
                    result.metadata["output_validation_warning"] = output_error

            logger.info(
                f"Tool '{tool_name}' completed: success={result.success}"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(
                f"Tool '{tool_name}' timed out after {manifest.timeout_seconds}s"
            )
            return create_error_result(
                f"Tool execution timed out after {manifest.timeout_seconds} seconds",
                timeout_seconds=manifest.timeout_seconds,
                tool_name=tool_name
            )

        except Exception as e:
            logger.error(
                f"Tool '{tool_name}' raised exception: {e}",
                exc_info=True
            )
            return create_error_result(
                f"Tool execution failed: {str(e)}",
                exception_type=type(e).__name__,
                tool_name=tool_name
            )

    def list_all_tools(self) -> List[ToolManifest]:
        """
        Get manifests for all registered tools.

        Returns:
            List of ToolManifest objects for all registered tools

        Example:
            for manifest in registry.list_all_tools():
                print(f"{manifest.name}: {manifest.description}")
        """
        return list(self.manifests.values())

    def get_tool_count(self) -> int:
        """Get total number of registered tools"""
        return len(self.tools)

    def get_domains(self) -> Set[str]:
        """Get set of all domains with registered tools"""
        domains = set()
        for manifest in self.manifests.values():
            domains.update(manifest.domains)
        return domains

    def get_statistics(self) -> Dict[str, any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with tool counts by domain, total tools, etc.

        Example:
            stats = registry.get_statistics()
            print(f"Total tools: {stats['total_tools']}")
            print(f"Domains: {stats['domains']}")
            print(f"Tools by domain: {stats['tools_by_domain']}")
        """
        tools_by_domain = {}
        for manifest in self.manifests.values():
            for domain in manifest.domains:
                if domain not in tools_by_domain:
                    tools_by_domain[domain] = []
                tools_by_domain[domain].append(manifest.name)

        return {
            "total_tools": len(self.tools),
            "domains": sorted(self.get_domains()),
            "tools_by_domain": tools_by_domain,
            "loaded_modules": len(self._loaded_modules),
        }


# ══════════════════════════════════════════════════════════════════════
# Global Registry Singleton
# ══════════════════════════════════════════════════════════════════════


_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """
    Get the global tool registry singleton.

    The global registry is initialized once and reused throughout the
    application lifecycle. It automatically discovers plugins from
    standard directories.

    Returns:
        Global ToolRegistry instance

    Example:
        from agent.tools.plugin_loader import get_global_registry

        registry = get_global_registry()
        tools = registry.get_tools_for_domain("hr")
    """
    global _global_registry

    if _global_registry is None:
        logger.info("Initializing global tool registry")
        _global_registry = ToolRegistry()

    return _global_registry


def reset_global_registry() -> None:
    """
    Reset the global registry (useful for testing).

    Example:
        # In tests
        reset_global_registry()
        registry = get_global_registry()  # Fresh registry
    """
    global _global_registry
    _global_registry = None
    logger.info("Global tool registry reset")


# ══════════════════════════════════════════════════════════════════════
# Tool Discovery for LLMs
# ══════════════════════════════════════════════════════════════════════


def generate_tool_documentation(
    domain: str,
    role: str,
    registry: Optional[ToolRegistry] = None,
    format: str = "markdown"
) -> str:
    """
    Generate documentation of available tools for LLM agents.

    This creates a formatted description of all tools available to a specific
    domain/role combination. The output is designed to be included in agent
    system prompts.

    Args:
        domain: Domain to filter tools by (e.g., "hr", "finance")
        role: Role to filter tools by (e.g., "manager", "recruiter")
        registry: Tool registry (uses global registry if None)
        format: Output format ("markdown" or "json")

    Returns:
        Formatted tool documentation string

    Example:
        # For inclusion in manager prompt
        tools_doc = generate_tool_documentation("hr", "recruiter")
        manager_prompt = f"{base_prompt}\\n\\n{tools_doc}"
    """
    if registry is None:
        registry = get_global_registry()

    tools = registry.get_tools_for_domain(domain, role)

    if format == "json":
        import json
        tool_data = []
        for tool_name in tools:
            manifest = registry.manifests[tool_name]
            tool_data.append({
                "name": manifest.name,
                "description": manifest.description,
                "input_schema": manifest.input_schema,
                "output_schema": manifest.output_schema,
                "examples": manifest.examples,
            })
        return json.dumps(tool_data, indent=2)

    # Markdown format
    docs = f"# Available Tools for {domain.title()} {role.title()}\n\n"
    docs += f"You have access to {len(tools)} tool(s):\n\n"

    for tool_name in tools:
        manifest = registry.manifests[tool_name]

        docs += f"## {manifest.name}\n\n"
        docs += f"{manifest.description}\n\n"

        docs += "**Parameters:**\n```json\n"
        import json
        docs += json.dumps(manifest.input_schema, indent=2)
        docs += "\n```\n\n"

        if manifest.examples:
            docs += "**Example:**\n```json\n"
            docs += json.dumps(manifest.examples[0], indent=2)
            docs += "\n```\n\n"

        if manifest.required_permissions:
            docs += f"**Required Permissions:** {', '.join(manifest.required_permissions)}\n\n"

        docs += f"**Cost Estimate:** ${manifest.cost_estimate:.4f}\n\n"
        docs += f"**Timeout:** {manifest.timeout_seconds}s\n\n"

        docs += "---\n\n"

    return docs
