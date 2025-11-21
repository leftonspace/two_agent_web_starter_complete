"""
PHASE 2.1: Tool Plugin Base Classes and Data Models

This module defines the core abstractions for the universal tool plugin system:
- ToolManifest: Metadata describing a tool's capabilities
- ToolExecutionContext: Runtime context provided during execution
- ToolResult: Standardized execution result
- ToolPlugin: Abstract base class all plugins must implement

Design Principles:
- Schema-driven: Tools declare JSON Schema for validation
- Permission-based: Tools declare required permissions
- Cost-aware: Tools report estimated cost/latency
- Async-first: All tool execution is async for IO-bound operations
- Type-safe: Full type hints with Pydantic models
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


class ToolManifest(BaseModel):
    """
    Metadata describing a tool's capabilities and requirements.

    This is the "contract" between a tool and the system. It declares:
    - What the tool does (description)
    - Who can use it (domains, roles, permissions)
    - How to call it (input/output schemas)
    - Resource usage (cost, timeout, network/filesystem access)
    - Documentation (examples, tags)

    Example:
        ToolManifest(
            name="send_email",
            version="1.0.0",
            description="Send email via SMTP",
            domains=["hr", "finance"],
            roles=["manager", "employee"],
            required_permissions=["email_send"],
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "format": "email"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"}
                },
                "required": ["to", "subject", "body"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "sent_at": {"type": "string", "format": "date-time"}
                }
            },
            cost_estimate=0.01,
            timeout_seconds=30,
            requires_network=True,
            examples=[...],
            tags=["email", "communication"]
        )
    """

    # Identity
    name: str = Field(
        ...,
        description="Unique tool identifier (e.g., 'send_email', 'format_code')",
        pattern=r"^[a-z][a-z0-9_]*$"
    )
    version: str = Field(
        ...,
        description="Semantic version (e.g., '1.0.0')",
        pattern=r"^\d+\.\d+\.\d+$"
    )
    description: str = Field(
        ...,
        description="Human-readable description for LLM context",
        min_length=10,
        max_length=500
    )

    # Access Control
    domains: List[str] = Field(
        default_factory=list,
        description="Which domains can use this tool (e.g., ['hr', 'finance', 'coding'])"
    )
    roles: List[str] = Field(
        default_factory=lambda: ["manager", "supervisor", "employee"],
        description="Which roles can use this tool"
    )
    required_permissions: List[str] = Field(
        default_factory=list,
        description="Required permissions (e.g., ['email_send', 'hris_write'])"
    )

    # Schema Validation
    input_schema: Dict[str, Any] = Field(
        ...,
        description="JSON Schema for validating input parameters"
    )
    output_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for validating output (optional)"
    )

    # Resource Usage
    cost_estimate: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated cost in USD (0.0 for free tools)"
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Maximum execution time in seconds"
    )
    requires_network: bool = Field(
        default=False,
        description="Whether tool requires network access"
    )
    requires_filesystem: bool = Field(
        default=False,
        description="Whether tool requires filesystem access"
    )

    # Documentation
    examples: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Example usage with input/output pairs"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for discovery (e.g., ['email', 'communication'])"
    )

    # Metadata
    author: Optional[str] = Field(
        default=None,
        description="Tool author/maintainer"
    )
    documentation_url: Optional[str] = Field(
        default=None,
        description="Link to detailed documentation"
    )

    @validator("domains", "roles", "tags", pre=True, always=True)
    def lowercase_lists(cls, v):
        """Ensure list values are lowercase for consistency"""
        if isinstance(v, list):
            return [item.lower() if isinstance(item, str) else item for item in v]
        return v

    class Config:
        extra = "forbid"  # Reject unknown fields


@dataclass
class ToolExecutionContext:
    """
    Runtime context provided to a tool during execution.

    This provides tools with all the information they need to execute safely
    and correctly within the orchestrator environment.

    Attributes:
        user_id: Optional user identifier for audit logging
        mission_id: Unique identifier for the current mission/run
        project_path: Root directory of the project being worked on
        config: Configuration dictionary from orchestrator
        permissions: List of permissions granted to current user/role
        role_id: PHASE 2.2: Current role for RBAC (e.g., "hr_recruiter")
        domain: PHASE 2.2: Current domain context (e.g., "hr", "finance")
        dry_run: If True, tool should simulate execution without side effects
        max_cost_usd: Maximum cost allowed for this execution (0 = no limit)
        metadata: Additional context-specific metadata
    """

    mission_id: str
    project_path: Path
    config: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)

    # PHASE 2.2: Role-based access control
    role_id: Optional[str] = None
    domain: Optional[str] = None

    # Optional fields
    user_id: Optional[str] = None
    dry_run: bool = False
    max_cost_usd: float = 0.0

    # Extensibility
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission"""
        return permission in self.permissions

    def validate_path(self, path: Path) -> bool:
        """Validate that a path is within project directory"""
        try:
            path.resolve().relative_to(self.project_path.resolve())
            return True
        except ValueError:
            return False


class ToolResult(BaseModel):
    """
    Standardized result returned by tool execution.

    All tools must return this structure for consistent error handling
    and result processing.

    Attributes:
        success: Whether tool execution succeeded
        data: Tool-specific output data (validated against output_schema)
        error: Error message if success=False
        metadata: Additional execution metadata (logs, timing, cost, etc.)

    Example:
        # Success case
        ToolResult(
            success=True,
            data={"formatted": True, "changes_made": True},
            metadata={"duration_seconds": 1.2, "files_changed": 5}
        )

        # Error case
        ToolResult(
            success=False,
            error="File not found: main.py",
            metadata={"attempted_path": "/invalid/path/main.py"}
        )
    """

    success: bool = Field(
        ...,
        description="Whether the tool execution succeeded"
    )
    data: Any = Field(
        default=None,
        description="Tool-specific output data (if success=True)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message (if success=False)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata (logs, timing, cost)"
    )

    class Config:
        extra = "allow"  # Allow additional fields for extensibility


# ══════════════════════════════════════════════════════════════════════
# Abstract Base Class
# ══════════════════════════════════════════════════════════════════════


class ToolPlugin(ABC):
    """
    Abstract base class for all tool plugins.

    To create a new tool plugin:
    1. Subclass ToolPlugin
    2. Implement get_manifest() to declare capabilities
    3. Implement execute() with the tool logic
    4. Drop the .py file in agent/tools/{domain}/ directory

    The plugin system will automatically discover and register your tool.

    Example:
        class SendEmailTool(ToolPlugin):
            def get_manifest(self) -> ToolManifest:
                return ToolManifest(
                    name="send_email",
                    version="1.0.0",
                    description="Send email via SMTP",
                    domains=["hr", "finance"],
                    required_permissions=["email_send"],
                    input_schema={...},
                    ...
                )

            async def execute(
                self,
                params: Dict[str, Any],
                context: ToolExecutionContext
            ) -> ToolResult:
                # Send email using params["to"], params["subject"], params["body"]
                # Return ToolResult with success=True and data={...}
                pass
    """

    @abstractmethod
    def get_manifest(self) -> ToolManifest:
        """
        Return tool metadata and capabilities.

        This is called once during plugin discovery to register the tool.

        Returns:
            ToolManifest describing the tool's interface and requirements
        """
        pass

    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute the tool with given parameters and context.

        This is the main entry point for tool execution. It must:
        - Be async (for IO-bound operations)
        - Validate parameters (or trust validate_params() was called)
        - Respect context.dry_run (simulate without side effects)
        - Handle errors gracefully (return ToolResult with success=False)
        - Include useful metadata in the result

        Args:
            params: Input parameters (validated against input_schema)
            context: Execution context with mission_id, project_path, permissions, etc.

        Returns:
            ToolResult with success status, data, and optional error message

        Example:
            async def execute(self, params, context):
                if context.dry_run:
                    return ToolResult(
                        success=True,
                        data={"simulated": True},
                        metadata={"dry_run": True}
                    )

                try:
                    # Actual tool logic here
                    result_data = await self._do_work(params)
                    return ToolResult(
                        success=True,
                        data=result_data,
                        metadata={"duration_seconds": 1.5}
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=str(e),
                        metadata={"exception_type": type(e).__name__}
                    )
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters against input_schema.

        Args:
            params: Parameters to validate

        Returns:
            (is_valid, error_message) tuple
            - is_valid: True if params match schema, False otherwise
            - error_message: None if valid, error description if invalid

        Example:
            is_valid, error = tool.validate_params({"to": "invalid-email"})
            if not is_valid:
                print(f"Invalid params: {error}")
        """
        if not JSONSCHEMA_AVAILABLE:
            # Fallback: basic type checking without jsonschema
            return self._basic_validation(params)

        manifest = self.get_manifest()
        try:
            jsonschema.validate(instance=params, schema=manifest.input_schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, f"Parameter validation failed: {e.message}"
        except jsonschema.SchemaError as e:
            return False, f"Invalid schema: {e.message}"

    def validate_output(self, output: Any) -> tuple[bool, Optional[str]]:
        """
        Validate output against output_schema.

        Args:
            output: Output to validate

        Returns:
            (is_valid, error_message) tuple
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, None  # Skip validation if jsonschema not available

        manifest = self.get_manifest()
        if not manifest.output_schema:
            return True, None  # No schema defined, skip validation

        try:
            jsonschema.validate(instance=output, schema=manifest.output_schema)
            return True, None
        except jsonschema.ValidationError as e:
            return False, f"Output validation failed: {e.message}"

    def _basic_validation(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Fallback validation when jsonschema is not available.

        Checks:
        - Required properties are present
        - Basic type checking

        Args:
            params: Parameters to validate

        Returns:
            (is_valid, error_message) tuple
        """
        manifest = self.get_manifest()
        schema = manifest.input_schema

        # Check required properties
        required = schema.get("required", [])
        for prop in required:
            if prop not in params:
                return False, f"Missing required parameter: {prop}"

        # Basic type checking for properties
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name not in params:
                continue

            value = params[prop_name]
            expected_type = prop_schema.get("type")

            if expected_type == "string" and not isinstance(value, str):
                return False, f"Parameter '{prop_name}' must be a string"
            elif expected_type == "integer" and not isinstance(value, int):
                return False, f"Parameter '{prop_name}' must be an integer"
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False, f"Parameter '{prop_name}' must be a number"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False, f"Parameter '{prop_name}' must be a boolean"
            elif expected_type == "array" and not isinstance(value, list):
                return False, f"Parameter '{prop_name}' must be an array"
            elif expected_type == "object" and not isinstance(value, dict):
                return False, f"Parameter '{prop_name}' must be an object"

        return True, None

    def __str__(self) -> str:
        """String representation of the tool"""
        manifest = self.get_manifest()
        return f"<{self.__class__.__name__} name={manifest.name} version={manifest.version}>"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return self.__str__()


# ══════════════════════════════════════════════════════════════════════
# Utility Functions
# ══════════════════════════════════════════════════════════════════════


def create_error_result(error_message: str, **metadata) -> ToolResult:
    """
    Convenience function to create an error ToolResult.

    Args:
        error_message: Error description
        **metadata: Additional metadata to include

    Returns:
        ToolResult with success=False

    Example:
        return create_error_result("File not found", path="/invalid/path")
    """
    return ToolResult(
        success=False,
        error=error_message,
        metadata=metadata
    )


def create_success_result(data: Any, **metadata) -> ToolResult:
    """
    Convenience function to create a success ToolResult.

    Args:
        data: Result data
        **metadata: Additional metadata to include

    Returns:
        ToolResult with success=True

    Example:
        return create_success_result({"formatted": True}, duration_seconds=1.2)
    """
    return ToolResult(
        success=True,
        data=data,
        metadata=metadata
    )
