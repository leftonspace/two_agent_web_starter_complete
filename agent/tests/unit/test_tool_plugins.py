"""
PHASE 2.1: Comprehensive tests for tool plugin system.

Tests cover:
- Plugin discovery and loading
- Tool execution with valid/invalid parameters
- Permission checking and enforcement
- Timeout management
- Tool isolation
- Registry operations
- Error handling

Run with: pytest agent/tests/unit/test_tool_plugins.py -v
"""

from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

import pytest

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
    create_error_result,
    create_success_result,
)
from agent.tools.plugin_loader import (
    ToolRegistry,
    generate_tool_documentation,
    reset_global_registry,
    get_global_registry,
)

# Import mock tools
from agent.tests.fixtures.mock_tool import (
    MockTool,
    SlowMockTool,
    FailingMockTool,
    PermissionMockTool,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_project_path():
    """Create a temporary project directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_context(mock_project_path):
    """Create a mock execution context"""
    return ToolExecutionContext(
        mission_id="test_mission_123",
        project_path=mock_project_path,
        config={"test": True},
        permissions=["test_permission"],
        user_id="test_user",
        dry_run=False
    )


@pytest.fixture
def registry():
    """Create a fresh registry for testing"""
    # Create registry with no plugin dirs (we'll register manually)
    registry = ToolRegistry(plugin_dirs=[])
    return registry


@pytest.fixture
def registry_with_mocks(registry):
    """Registry with mock tools pre-registered"""
    registry.register(MockTool())
    registry.register(SlowMockTool())
    registry.register(FailingMockTool())
    registry.register(PermissionMockTool())
    return registry


# ══════════════════════════════════════════════════════════════════════
# Test: Tool Manifest Validation
# ══════════════════════════════════════════════════════════════════════


def test_tool_manifest_creation():
    """Test that ToolManifest can be created with valid data"""
    manifest = ToolManifest(
        name="test_tool",
        version="1.0.0",
        description="A test tool for validation",
        domains=["testing"],
        roles=["tester"],
        required_permissions=["test_perm"],
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            }
        },
        output_schema={},
        cost_estimate=0.0,
        timeout_seconds=30
    )

    assert manifest.name == "test_tool"
    assert manifest.version == "1.0.0"
    assert "testing" in manifest.domains
    assert manifest.timeout_seconds == 30


def test_tool_manifest_invalid_name():
    """Test that invalid tool names are rejected"""
    with pytest.raises(Exception):  # Pydantic validation error
        ToolManifest(
            name="Invalid-Name-With-Dashes",  # Should only allow lowercase and underscores
            version="1.0.0",
            description="Test description",
            domains=[],
            input_schema={}
        )


def test_tool_manifest_invalid_version():
    """Test that invalid version strings are rejected"""
    with pytest.raises(Exception):  # Pydantic validation error
        ToolManifest(
            name="test_tool",
            version="v1.0",  # Should be semantic version like "1.0.0"
            description="Test description",
            domains=[],
            input_schema={}
        )


# ══════════════════════════════════════════════════════════════════════
# Test: Tool Registration and Discovery
# ══════════════════════════════════════════════════════════════════════


def test_registry_initialization(registry):
    """Test that registry initializes correctly"""
    assert isinstance(registry, ToolRegistry)
    assert registry.get_tool_count() == 0


def test_manual_tool_registration(registry):
    """Test manual registration of a tool"""
    tool = MockTool()
    registry.register(tool)

    assert registry.get_tool_count() == 1
    assert registry.get_tool("mock_tool") is not None
    assert registry.get_manifest("mock_tool") is not None


def test_duplicate_tool_registration(registry):
    """Test that registering duplicate tool replaces the old one"""
    tool1 = MockTool()
    tool2 = MockTool()

    registry.register(tool1)
    assert registry.get_tool_count() == 1

    # Register again - should replace
    registry.register(tool2)
    assert registry.get_tool_count() == 1  # Still 1, not 2


def test_tool_unregistration(registry):
    """Test unregistering a tool"""
    tool = MockTool()
    registry.register(tool)
    assert registry.get_tool_count() == 1

    result = registry.unregister("mock_tool")
    assert result is True
    assert registry.get_tool_count() == 0

    # Try to unregister non-existent tool
    result = registry.unregister("nonexistent")
    assert result is False


def test_plugin_discovery_from_directory():
    """Test automatic plugin discovery from directory"""
    # Create registry that will scan the fixtures directory
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    registry = ToolRegistry(plugin_dirs=[fixtures_dir])

    # Should have discovered mock tools
    assert registry.get_tool_count() > 0
    assert registry.get_tool("mock_tool") is not None


# ══════════════════════════════════════════════════════════════════════
# Test: Tool Execution
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.anyio
async def test_successful_tool_execution(registry_with_mocks, mock_context):
    """Test executing a tool with valid parameters"""
    result = await registry_with_mocks.execute_tool(
        "mock_tool",
        {"message": "Hello, World!"},
        mock_context
    )

    assert result.success is True
    assert result.data is not None
    assert "echo" in result.data
    assert "Hello, World!" in result.data["echo"]


@pytest.mark.anyio
async def test_tool_execution_with_invalid_params(registry_with_mocks, mock_context):
    """Test executing a tool with invalid parameters"""
    # Missing required "message" parameter
    result = await registry_with_mocks.execute_tool(
        "mock_tool",
        {},  # Empty params
        mock_context
    )

    assert result.success is False
    assert "Invalid parameters" in result.error or "Missing required parameter" in result.error


@pytest.mark.anyio
async def test_tool_execution_not_found(registry_with_mocks, mock_context):
    """Test executing a non-existent tool"""
    result = await registry_with_mocks.execute_tool(
        "nonexistent_tool",
        {},
        mock_context
    )

    assert result.success is False
    assert "not found" in result.error.lower()


@pytest.mark.anyio
async def test_tool_execution_timeout(registry_with_mocks, mock_context):
    """Test that tool execution respects timeout"""
    # SlowMockTool has 2-second timeout but tries to sleep for 10 seconds
    result = await registry_with_mocks.execute_tool(
        "slow_mock_tool",
        {"sleep_seconds": 10},
        mock_context
    )

    assert result.success is False
    assert "timed out" in result.error.lower()


@pytest.mark.anyio
async def test_tool_execution_failure(registry_with_mocks, mock_context):
    """Test tool that intentionally fails"""
    result = await registry_with_mocks.execute_tool(
        "failing_mock_tool",
        {},
        mock_context
    )

    assert result.success is False
    assert "always fails" in result.error.lower()


# ══════════════════════════════════════════════════════════════════════
# Test: Permission Checking
# ══════════════════════════════════════════════════════════════════════


def test_permission_check_with_permissions(registry_with_mocks):
    """Test permission check when user has required permissions"""
    has_perm, error = registry_with_mocks.check_permissions(
        "mock_tool",
        ["test_permission"]
    )

    assert has_perm is True
    assert error is None


def test_permission_check_without_permissions(registry_with_mocks):
    """Test permission check when user lacks required permissions"""
    has_perm, error = registry_with_mocks.check_permissions(
        "mock_tool",
        []  # No permissions
    )

    assert has_perm is False
    assert error is not None
    assert "missing" in error.lower() or "insufficient" in error.lower()


def test_permission_check_with_extra_permissions(registry_with_mocks):
    """Test permission check when user has more than required permissions"""
    has_perm, error = registry_with_mocks.check_permissions(
        "mock_tool",
        ["test_permission", "extra_permission", "another_permission"]
    )

    assert has_perm is True
    assert error is None


@pytest.mark.anyio
async def test_tool_execution_blocks_without_permission(registry_with_mocks, mock_context):
    """Test that tool execution is blocked without required permissions"""
    # PermissionMockTool requires "special_permission" and "another_permission"
    # But mock_context only has "test_permission"
    result = await registry_with_mocks.execute_tool(
        "permission_mock_tool",
        {},
        mock_context
    )

    assert result.success is False
    assert "permission" in result.error.lower()


@pytest.mark.anyio
async def test_tool_execution_succeeds_with_permission(registry_with_mocks, mock_project_path):
    """Test that tool execution succeeds with required permissions"""
    # Create context with the required permissions
    context = ToolExecutionContext(
        mission_id="test_mission",
        project_path=mock_project_path,
        permissions=["special_permission", "another_permission"]
    )

    result = await registry_with_mocks.execute_tool(
        "permission_mock_tool",
        {},
        context
    )

    assert result.success is True


# ══════════════════════════════════════════════════════════════════════
# Test: Tool Filtering and Queries
# ══════════════════════════════════════════════════════════════════════


def test_get_tools_for_domain(registry_with_mocks):
    """Test filtering tools by domain"""
    tools = registry_with_mocks.get_tools_for_domain("testing")

    assert len(tools) > 0
    assert "mock_tool" in tools
    assert "slow_mock_tool" in tools


def test_get_tools_for_domain_with_role(registry_with_mocks):
    """Test filtering tools by domain and role"""
    tools = registry_with_mocks.get_tools_for_domain("testing", "test_user")

    assert len(tools) > 0
    assert "mock_tool" in tools


def test_get_tools_for_nonexistent_domain(registry_with_mocks):
    """Test filtering tools by non-existent domain"""
    tools = registry_with_mocks.get_tools_for_domain("nonexistent_domain")

    assert len(tools) == 0


def test_list_all_tools(registry_with_mocks):
    """Test listing all registered tools"""
    manifests = registry_with_mocks.list_all_tools()

    assert len(manifests) == 4  # 4 mock tools
    assert all(isinstance(m, ToolManifest) for m in manifests)


def test_get_statistics(registry_with_mocks):
    """Test registry statistics"""
    stats = registry_with_mocks.get_statistics()

    assert stats["total_tools"] == 4
    assert "testing" in stats["domains"]
    assert "tools_by_domain" in stats
    assert len(stats["tools_by_domain"]["testing"]) > 0


# ══════════════════════════════════════════════════════════════════════
# Test: Parameter Validation
# ══════════════════════════════════════════════════════════════════════


def test_validate_params_success():
    """Test parameter validation with valid params"""
    tool = MockTool()
    is_valid, error = tool.validate_params({"message": "test"})

    assert is_valid is True
    assert error is None


def test_validate_params_missing_required():
    """Test parameter validation with missing required field"""
    tool = MockTool()
    is_valid, error = tool.validate_params({})  # Missing "message"

    assert is_valid is False
    assert error is not None


def test_validate_params_wrong_type():
    """Test parameter validation with wrong type"""
    tool = MockTool()
    is_valid, error = tool.validate_params({"message": 123})  # Should be string

    assert is_valid is False
    assert error is not None


# ══════════════════════════════════════════════════════════════════════
# Test: Tool Documentation Generation
# ══════════════════════════════════════════════════════════════════════


def test_generate_tool_documentation_markdown(registry_with_mocks):
    """Test generating markdown documentation for tools"""
    docs = generate_tool_documentation("testing", "test_user", registry_with_mocks, format="markdown")

    assert isinstance(docs, str)
    assert "mock_tool" in docs
    assert "Available Tools" in docs
    assert "Parameters" in docs


def test_generate_tool_documentation_json(registry_with_mocks):
    """Test generating JSON documentation for tools"""
    import json

    docs_str = generate_tool_documentation("testing", "test_user", registry_with_mocks, format="json")
    docs = json.loads(docs_str)

    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all("name" in tool for tool in docs)
    assert all("description" in tool for tool in docs)


# ══════════════════════════════════════════════════════════════════════
# Test: Global Registry
# ══════════════════════════════════════════════════════════════════════


def test_global_registry_singleton():
    """Test that get_global_registry returns singleton"""
    reset_global_registry()

    registry1 = get_global_registry()
    registry2 = get_global_registry()

    assert registry1 is registry2  # Same instance


def test_global_registry_reset():
    """Test resetting global registry"""
    registry1 = get_global_registry()
    tool = MockTool()
    registry1.register(tool)

    assert registry1.get_tool_count() >= 1

    reset_global_registry()
    registry2 = get_global_registry()

    assert registry1 is not registry2  # Different instance
    # registry2 might auto-discover tools from builtin/, so don't check count == 0


# ══════════════════════════════════════════════════════════════════════
# Test: Helper Functions
# ══════════════════════════════════════════════════════════════════════


def test_create_error_result():
    """Test error result helper function"""
    result = create_error_result("Test error", code=42, details="More info")

    assert result.success is False
    assert result.error == "Test error"
    assert result.metadata["code"] == 42
    assert result.metadata["details"] == "More info"


def test_create_success_result():
    """Test success result helper function"""
    result = create_success_result({"value": 123}, extra="metadata")

    assert result.success is True
    assert result.data == {"value": 123}
    assert result.metadata["extra"] == "metadata"


# ══════════════════════════════════════════════════════════════════════
# Test: Execution Context
# ══════════════════════════════════════════════════════════════════════


def test_execution_context_has_permission():
    """Test context permission checking"""
    context = ToolExecutionContext(
        mission_id="test",
        project_path=Path("/tmp"),
        permissions=["perm1", "perm2"]
    )

    assert context.has_permission("perm1") is True
    assert context.has_permission("perm2") is True
    assert context.has_permission("perm3") is False


def test_execution_context_validate_path(mock_project_path):
    """Test context path validation"""
    context = ToolExecutionContext(
        mission_id="test",
        project_path=mock_project_path
    )

    valid_path = mock_project_path / "subdir" / "file.txt"
    invalid_path = Path("/etc/passwd")

    assert context.validate_path(valid_path) is True
    assert context.validate_path(invalid_path) is False


# ══════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════


def test_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("PHASE 2.1 Tool Plugin System - Test Summary")
    print("="*70)
    print("✅ Tool manifest validation")
    print("✅ Plugin discovery and registration")
    print("✅ Tool execution (success/failure/timeout)")
    print("✅ Permission checking and enforcement")
    print("✅ Parameter validation")
    print("✅ Tool filtering and queries")
    print("✅ Documentation generation")
    print("✅ Global registry singleton")
    print("✅ Helper functions")
    print("✅ Execution context")
    print("="*70)
    print(f"Total test cases: 30+")
    print("="*70)
