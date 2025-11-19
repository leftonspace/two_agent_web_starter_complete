"""
PHASE 2.1: Mock Tool for Testing

Provides a simple mock tool for testing the plugin system.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
    create_success_result,
    create_error_result,
)


class MockTool(ToolPlugin):
    """
    Simple mock tool for testing plugin system.

    Always succeeds and echoes back the input parameters.
    """

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="mock_tool",
            version="1.0.0",
            description="Mock tool for testing - echoes input back",
            domains=["testing"],
            roles=["test_user"],
            required_permissions=["test_permission"],
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "echo": {"type": "string"}
                }
            },
            cost_estimate=0.0,
            timeout_seconds=5,
            tags=["mock", "test"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Echo the message back"""
        message = params.get("message", "")

        # Simulate some work
        await asyncio.sleep(0.1)

        return create_success_result(
            {"echo": f"Echoed: {message}"},
            simulated=True
        )


class SlowMockTool(ToolPlugin):
    """
    Mock tool that takes a long time to execute (for timeout testing).
    """

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="slow_mock_tool",
            version="1.0.0",
            description="Slow mock tool for timeout testing",
            domains=["testing"],
            roles=["test_user"],
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {
                    "sleep_seconds": {"type": "number", "default": 10}
                }
            },
            output_schema={},
            cost_estimate=0.0,
            timeout_seconds=2,  # Intentionally short timeout
            tags=["mock", "test", "slow"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Sleep for specified duration"""
        sleep_seconds = params.get("sleep_seconds", 10)
        await asyncio.sleep(sleep_seconds)
        return create_success_result({"slept": sleep_seconds})


class FailingMockTool(ToolPlugin):
    """
    Mock tool that always fails (for error handling testing).
    """

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="failing_mock_tool",
            version="1.0.0",
            description="Mock tool that always fails",
            domains=["testing"],
            roles=["test_user"],
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {}
            },
            output_schema={},
            cost_estimate=0.0,
            timeout_seconds=5,
            tags=["mock", "test", "failing"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Always fail"""
        return create_error_result(
            "This tool always fails",
            reason="intentional_failure"
        )


class PermissionMockTool(ToolPlugin):
    """
    Mock tool with specific permission requirements (for permission testing).
    """

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="permission_mock_tool",
            version="1.0.0",
            description="Mock tool requiring specific permissions",
            domains=["testing"],
            roles=["test_user"],
            required_permissions=["special_permission", "another_permission"],
            input_schema={
                "type": "object",
                "properties": {}
            },
            output_schema={},
            cost_estimate=0.0,
            timeout_seconds=5,
            tags=["mock", "test", "permissions"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute with permission check"""
        return create_success_result(
            {"message": "Permission check passed"},
            permissions=context.permissions
        )
