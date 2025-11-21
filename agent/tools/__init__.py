"""
PHASE 2.1: Universal Tool Plugin System

This package provides a flexible, plugin-based architecture for tools that can be
used by any department (HR, Finance, Legal, Engineering, etc.).

Core Components:
- base.py: Abstract base classes and data models for tool plugins
- plugin_loader.py: Plugin discovery, registration, and execution
- builtin/: Built-in tools for software development
- hr/: HR department-specific tools
- finance/: Finance department-specific tools
- custom/: User-defined custom tools

Key Features:
- Zero-code plugin registration (drop files in tools/ subdirectories)
- Schema-driven validation (JSON Schema for inputs/outputs)
- Permission-based access control
- Sandboxed execution with timeouts
- Cost-aware for model routing decisions
- Dynamic discovery at runtime

Usage:
    from agent.tools.plugin_loader import get_global_registry

    registry = get_global_registry()
    tools = registry.get_tools_for_domain("hr", "recruiter")
    result = await registry.execute_tool("send_email", {...}, context)
"""

from .base import (
    ToolManifest,
    ToolExecutionContext,
    ToolResult,
    ToolPlugin,
)

from .plugin_loader import (
    ToolRegistry,
    get_global_registry,
)

__all__ = [
    "ToolManifest",
    "ToolExecutionContext",
    "ToolResult",
    "ToolPlugin",
    "ToolRegistry",
    "get_global_registry",
]

__version__ = "2.1.0"
