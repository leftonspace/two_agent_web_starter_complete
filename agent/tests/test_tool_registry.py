"""
Tests for Tool Registration System

Tests the decorator-based tool registration, schema generation,
agent-based access control, and tool execution.
"""

import asyncio
import pytest
import sys
import os
from typing import Optional, List, Dict, Any
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Python 3.9+ has Annotated in typing
try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated

from tool_registry import (
    ToolRegistry,
    ToolDefinition,
    ToolResult,
    ParameterInfo,
    ToolCategory,
    ToolPermission,
    tool,
    create_tool_from_function,
    batch_execute_tools,
    get_tool_documentation,
    _extract_parameter_info,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def clear_registry():
    """Clear the registry before each test"""
    ToolRegistry.clear()
    yield
    ToolRegistry.clear()


# ============================================================================
# Test ParameterInfo
# ============================================================================

class TestParameterInfo:
    """Tests for ParameterInfo class"""

    def test_string_type_to_schema(self):
        """Test string type conversion"""
        param = ParameterInfo(
            name="test",
            type_hint=str,
            description="Test parameter"
        )
        schema = param.to_json_schema()
        assert schema["type"] == "string"
        assert schema["description"] == "Test parameter"

    def test_int_type_to_schema(self):
        """Test integer type conversion"""
        param = ParameterInfo(name="count", type_hint=int)
        schema = param.to_json_schema()
        assert schema["type"] == "integer"

    def test_float_type_to_schema(self):
        """Test float type conversion"""
        param = ParameterInfo(name="value", type_hint=float)
        schema = param.to_json_schema()
        assert schema["type"] == "number"

    def test_bool_type_to_schema(self):
        """Test boolean type conversion"""
        param = ParameterInfo(name="flag", type_hint=bool)
        schema = param.to_json_schema()
        assert schema["type"] == "boolean"

    def test_list_type_to_schema(self):
        """Test list type conversion"""
        param = ParameterInfo(name="items", type_hint=List[str])
        schema = param.to_json_schema()
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "string"

    def test_dict_type_to_schema(self):
        """Test dict type conversion"""
        param = ParameterInfo(name="data", type_hint=Dict[str, Any])
        schema = param.to_json_schema()
        assert schema["type"] == "object"

    def test_optional_type_to_schema(self):
        """Test Optional type conversion"""
        param = ParameterInfo(name="maybe", type_hint=Optional[str])
        schema = param.to_json_schema()
        assert schema["type"] == "string"


# ============================================================================
# Test Tool Decorator
# ============================================================================

class TestToolDecorator:
    """Tests for @tool decorator"""

    def test_basic_tool_registration(self):
        """Test basic tool registration with decorator"""
        @tool(name="test_tool", description="A test tool")
        def test_func(arg1: str) -> str:
            return f"Hello {arg1}"

        assert ToolRegistry.tool_exists("test_tool")
        tool_def = ToolRegistry.get("test_tool")
        assert tool_def.name == "test_tool"
        assert tool_def.description == "A test tool"

    def test_tool_with_annotated_params(self):
        """Test tool with Annotated parameters"""
        @tool(name="annotated_tool")
        def annotated_func(
            query: Annotated[str, "The search query"],
            limit: Annotated[int, "Max results"] = 10
        ) -> str:
            return f"Searching for {query}, limit {limit}"

        tool_def = ToolRegistry.get("annotated_tool")
        assert len(tool_def.parameters) == 2

        query_param = tool_def.parameters[0]
        assert query_param.name == "query"
        assert query_param.description == "The search query"
        assert query_param.required is True

        limit_param = tool_def.parameters[1]
        assert limit_param.name == "limit"
        assert limit_param.description == "Max results"
        assert limit_param.required is False
        assert limit_param.default == 10

    def test_tool_with_agent_restriction(self):
        """Test tool with agent restrictions"""
        @tool(
            name="restricted_tool",
            agents=["agent1", "agent2"]
        )
        def restricted_func() -> str:
            return "restricted"

        tool_def = ToolRegistry.get("restricted_tool")
        assert tool_def.agents == ["agent1", "agent2"]

    def test_tool_category_and_permission(self):
        """Test tool category and permission settings"""
        @tool(
            name="admin_tool",
            category=ToolCategory.SYSTEM,
            permission=ToolPermission.ADMIN
        )
        def admin_func() -> str:
            return "admin"

        tool_def = ToolRegistry.get("admin_tool")
        assert tool_def.category == ToolCategory.SYSTEM
        assert tool_def.permission == ToolPermission.ADMIN

    def test_async_tool_registration(self):
        """Test async tool registration"""
        @tool(name="async_tool")
        async def async_func(data: str) -> str:
            return f"async {data}"

        tool_def = ToolRegistry.get("async_tool")
        assert tool_def.is_async is True

    def test_tool_default_name_from_function(self):
        """Test tool name defaults to function name"""
        @tool(description="Uses function name")
        def my_custom_tool():
            pass

        assert ToolRegistry.tool_exists("my_custom_tool")

    def test_tool_with_tags(self):
        """Test tool with tags"""
        @tool(
            name="tagged_tool",
            tags=["tag1", "tag2", "search"]
        )
        def tagged_func():
            pass

        tool_def = ToolRegistry.get("tagged_tool")
        assert tool_def.tags == ["tag1", "tag2", "search"]


# ============================================================================
# Test ToolRegistry
# ============================================================================

class TestToolRegistry:
    """Tests for ToolRegistry class"""

    def test_register_and_get(self):
        """Test registering and retrieving tools"""
        @tool(name="reg_test")
        def reg_func():
            pass

        assert ToolRegistry.get("reg_test") is not None
        assert ToolRegistry.get("nonexistent") is None

    def test_unregister(self):
        """Test unregistering tools"""
        @tool(name="to_remove")
        def remove_func():
            pass

        assert ToolRegistry.tool_exists("to_remove")
        result = ToolRegistry.unregister("to_remove")
        assert result is True
        assert not ToolRegistry.tool_exists("to_remove")

        # Try to unregister non-existent tool
        result = ToolRegistry.unregister("nonexistent")
        assert result is False

    def test_get_all_tools(self):
        """Test getting all registered tools"""
        @tool(name="tool1")
        def func1():
            pass

        @tool(name="tool2")
        def func2():
            pass

        all_tools = ToolRegistry.get_all_tools()
        names = [t.name for t in all_tools]
        assert "tool1" in names
        assert "tool2" in names

    def test_get_tools_for_agent(self):
        """Test agent-based tool filtering"""
        @tool(name="public_tool", agents=None)
        def public_func():
            pass

        @tool(name="agent1_tool", agents=["agent1"])
        def agent1_func():
            pass

        @tool(name="agent2_tool", agents=["agent2"])
        def agent2_func():
            pass

        @tool(name="shared_tool", agents=["agent1", "agent2"])
        def shared_func():
            pass

        # Agent1 tools
        agent1_tools = ToolRegistry.get_tools_for_agent("agent1")
        agent1_names = [t.name for t in agent1_tools]
        assert "public_tool" in agent1_names
        assert "agent1_tool" in agent1_names
        assert "shared_tool" in agent1_names
        assert "agent2_tool" not in agent1_names

        # Agent2 tools
        agent2_tools = ToolRegistry.get_tools_for_agent("agent2")
        agent2_names = [t.name for t in agent2_tools]
        assert "public_tool" in agent2_names
        assert "agent2_tool" in agent2_names
        assert "shared_tool" in agent2_names
        assert "agent1_tool" not in agent2_names

    def test_get_tools_by_category(self):
        """Test category-based tool filtering"""
        @tool(name="web_tool", category=ToolCategory.WEB)
        def web_func():
            pass

        @tool(name="file_tool", category=ToolCategory.FILE)
        def file_func():
            pass

        web_tools = ToolRegistry.get_tools_by_category(ToolCategory.WEB)
        web_names = [t.name for t in web_tools]
        assert "web_tool" in web_names
        assert "file_tool" not in web_names

    def test_list_tools(self):
        """Test listing tool names"""
        @tool(name="list_test1")
        def func1():
            pass

        @tool(name="list_test2")
        def func2():
            pass

        names = ToolRegistry.list_tools()
        assert "list_test1" in names
        assert "list_test2" in names


# ============================================================================
# Test Schema Generation
# ============================================================================

class TestSchemaGeneration:
    """Tests for tool schema generation"""

    def test_openai_schema_generation(self):
        """Test OpenAI function calling schema generation"""
        @tool(name="schema_test", description="Test tool for schema")
        def schema_func(
            query: Annotated[str, "Search query"],
            count: Annotated[int, "Number of results"] = 5
        ) -> str:
            pass

        schemas = ToolRegistry.get_tool_schemas("any_agent", format="openai")
        assert len(schemas) == 1

        schema = schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "schema_test"
        assert schema["function"]["description"] == "Test tool for schema"

        params = schema["function"]["parameters"]
        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "count" in params["properties"]
        assert "query" in params["required"]
        assert "count" not in params["required"]

    def test_anthropic_schema_generation(self):
        """Test Anthropic tool use schema generation"""
        @tool(name="anthropic_test", description="Test for Anthropic")
        def anthropic_func(
            text: Annotated[str, "Input text"]
        ) -> str:
            pass

        schemas = ToolRegistry.get_tool_schemas("any_agent", format="anthropic")
        assert len(schemas) == 1

        schema = schemas[0]
        assert schema["name"] == "anthropic_test"
        assert schema["description"] == "Test for Anthropic"
        assert "input_schema" in schema
        assert schema["input_schema"]["type"] == "object"

    def test_invalid_schema_format(self):
        """Test invalid schema format raises error"""
        @tool(name="format_test")
        def format_func():
            pass

        with pytest.raises(ValueError, match="Unknown schema format"):
            ToolRegistry.get_tool_schemas("agent", format="invalid")


# ============================================================================
# Test Tool Execution
# ============================================================================

class TestToolExecution:
    """Tests for tool execution"""

    @pytest.mark.asyncio
    async def test_sync_tool_execution(self):
        """Test executing synchronous tool"""
        @tool(name="sync_exec")
        def sync_func(x: int, y: int) -> int:
            return x + y

        result = await ToolRegistry.execute_tool("sync_exec", x=5, y=3)
        assert result.success is True
        assert result.result == 8
        assert result.tool_name == "sync_exec"

    @pytest.mark.asyncio
    async def test_async_tool_execution(self):
        """Test executing asynchronous tool"""
        @tool(name="async_exec")
        async def async_func(message: str) -> str:
            await asyncio.sleep(0.01)
            return f"Processed: {message}"

        result = await ToolRegistry.execute_tool("async_exec", message="hello")
        assert result.success is True
        assert result.result == "Processed: hello"

    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test executing non-existent tool"""
        result = await ToolRegistry.execute_tool("nonexistent_tool")
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_tool_agent_authorization(self):
        """Test agent authorization for tool execution"""
        @tool(name="authorized_tool", agents=["authorized_agent"])
        def auth_func() -> str:
            return "success"

        # Authorized agent
        result = await ToolRegistry.execute_tool(
            "authorized_tool",
            agent_name="authorized_agent"
        )
        assert result.success is True

        # Unauthorized agent
        result = await ToolRegistry.execute_tool(
            "authorized_tool",
            agent_name="unauthorized_agent"
        )
        assert result.success is False
        assert "not authorized" in result.error

    @pytest.mark.asyncio
    async def test_tool_execution_error(self):
        """Test tool execution with error"""
        @tool(name="error_tool")
        def error_func() -> str:
            raise ValueError("Intentional error")

        result = await ToolRegistry.execute_tool("error_tool")
        assert result.success is False
        assert "Intentional error" in result.error

    @pytest.mark.asyncio
    async def test_tool_timeout(self):
        """Test tool execution timeout"""
        @tool(name="slow_tool", timeout=0.1)
        async def slow_func() -> str:
            await asyncio.sleep(10)
            return "done"

        result = await ToolRegistry.execute_tool("slow_tool")
        assert result.success is False
        assert "timed out" in result.error

    def test_sync_execution_method(self):
        """Test synchronous execute_tool_sync method"""
        @tool(name="sync_method_test")
        def sync_test() -> str:
            return "sync result"

        result = ToolRegistry.execute_tool_sync("sync_method_test")
        assert result.success is True
        assert result.result == "sync result"


# ============================================================================
# Test Batch Execution
# ============================================================================

class TestBatchExecution:
    """Tests for batch tool execution"""

    @pytest.mark.asyncio
    async def test_parallel_batch_execution(self):
        """Test parallel batch execution"""
        @tool(name="batch_tool1")
        def batch_func1(x: int) -> int:
            return x * 2

        @tool(name="batch_tool2")
        def batch_func2(y: int) -> int:
            return y + 10

        calls = [
            {"name": "batch_tool1", "arguments": {"x": 5}},
            {"name": "batch_tool2", "arguments": {"y": 3}},
        ]

        results = await batch_execute_tools(calls, parallel=True)
        assert len(results) == 2
        assert results[0].result == 10
        assert results[1].result == 13

    @pytest.mark.asyncio
    async def test_sequential_batch_execution(self):
        """Test sequential batch execution"""
        @tool(name="seq_tool")
        def seq_func(n: int) -> int:
            return n * n

        calls = [
            {"name": "seq_tool", "arguments": {"n": 2}},
            {"name": "seq_tool", "arguments": {"n": 3}},
            {"name": "seq_tool", "arguments": {"n": 4}},
        ]

        results = await batch_execute_tools(calls, parallel=False)
        assert len(results) == 3
        assert [r.result for r in results] == [4, 9, 16]


# ============================================================================
# Test Tool Creation from Function
# ============================================================================

class TestCreateToolFromFunction:
    """Tests for programmatic tool creation"""

    def test_create_from_function(self):
        """Test creating tool from existing function"""
        def existing_function(a: int, b: int) -> int:
            """Add two numbers"""
            return a + b

        tool_def = create_tool_from_function(
            existing_function,
            name="add_numbers",
            description="Adds two integers",
            agents=["math_agent"]
        )

        assert tool_def.name == "add_numbers"
        assert tool_def.description == "Adds two integers"
        assert tool_def.agents == ["math_agent"]
        assert ToolRegistry.tool_exists("add_numbers")


# ============================================================================
# Test Built-in Tools
# ============================================================================

class TestBuiltInTools:
    """Tests for built-in tools"""

    def test_builtin_tools_registered(self):
        """Test that built-in tools are registered on import"""
        # Re-import to trigger registration
        from tool_registry import (
            web_search,
            file_read,
            file_write,
            code_execute,
            http_request,
        )

        # Check tools exist
        assert ToolRegistry.tool_exists("web_search")
        assert ToolRegistry.tool_exists("file_read")
        assert ToolRegistry.tool_exists("file_write")
        assert ToolRegistry.tool_exists("code_execute")
        assert ToolRegistry.tool_exists("http_request")

    @pytest.mark.asyncio
    async def test_web_search_placeholder(self):
        """Test web_search placeholder implementation"""
        result = await ToolRegistry.execute_tool(
            "web_search",
            agent_name="researcher",
            query="test query",
            num_results=3
        )
        assert result.success is True
        assert "results" in result.result
        assert len(result.result["results"]) == 3

    def test_file_read_nonexistent(self):
        """Test file_read with non-existent file"""
        result = ToolRegistry.execute_tool_sync(
            "file_read",
            agent_name="coder",
            path="/nonexistent/file.txt"
        )
        assert result.success is True  # Tool executes successfully
        assert result.result["success"] is False  # But operation fails
        assert "not found" in result.result["error"]

    def test_file_read_restricted_path(self):
        """Test file_read with restricted path"""
        result = ToolRegistry.execute_tool_sync(
            "file_read",
            agent_name="coder",
            path="/etc/shadow"
        )
        assert result.success is True
        assert result.result["success"] is False
        assert "restricted" in result.result["error"]

    def test_json_parse_tool(self):
        """Test json_parse tool"""
        result = ToolRegistry.execute_tool_sync(
            "json_parse",
            data='{"name": "test", "value": 42}'
        )
        assert result.success is True
        assert result.result["result"]["name"] == "test"
        assert result.result["result"]["value"] == 42

    def test_json_parse_with_path(self):
        """Test json_parse with path extraction"""
        result = ToolRegistry.execute_tool_sync(
            "json_parse",
            data='{"outer": {"inner": {"value": 123}}}',
            path="outer.inner.value"
        )
        assert result.success is True
        assert result.result["result"] == 123

    def test_json_parse_invalid(self):
        """Test json_parse with invalid JSON"""
        result = ToolRegistry.execute_tool_sync(
            "json_parse",
            data="not valid json"
        )
        assert result.success is True
        assert result.result["success"] is False
        assert "Invalid JSON" in result.result["error"]


# ============================================================================
# Test Documentation Generation
# ============================================================================

class TestDocumentation:
    """Tests for documentation generation"""

    def test_generate_documentation(self):
        """Test documentation generation"""
        @tool(
            name="doc_test",
            description="A tool for testing documentation",
            category=ToolCategory.DATA,
            agents=["tester"]
        )
        def doc_func(
            param1: Annotated[str, "First parameter"],
            param2: Annotated[int, "Second parameter"] = 10
        ) -> str:
            pass

        docs = get_tool_documentation()
        assert "# Available Tools" in docs
        assert "doc_test" in docs
        assert "A tool for testing documentation" in docs
        assert "First parameter" in docs
        assert "Second parameter" in docs


# ============================================================================
# Test Parameter Extraction
# ============================================================================

class TestParameterExtraction:
    """Tests for parameter extraction from functions"""

    def test_extract_simple_params(self):
        """Test extracting simple parameters"""
        def simple_func(a: str, b: int, c: float = 1.0):
            pass

        params = _extract_parameter_info(simple_func)
        assert len(params) == 3
        assert params[0].name == "a"
        assert params[0].required is True
        assert params[2].name == "c"
        assert params[2].required is False
        assert params[2].default == 1.0

    def test_extract_annotated_params(self):
        """Test extracting Annotated parameters"""
        def annotated_func(
            query: Annotated[str, "The query string"],
            limit: Annotated[int, "Maximum items"] = 100
        ):
            pass

        params = _extract_parameter_info(annotated_func)
        assert params[0].description == "The query string"
        assert params[1].description == "Maximum items"


# ============================================================================
# Test ToolResult
# ============================================================================

class TestToolResult:
    """Tests for ToolResult class"""

    def test_tool_result_to_dict(self):
        """Test ToolResult serialization"""
        result = ToolResult(
            success=True,
            result={"data": "test"},
            error=None,
            execution_time=0.5,
            tool_name="test_tool"
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["result"] == {"data": "test"}
        assert d["error"] is None
        assert d["execution_time"] == 0.5
        assert d["tool_name"] == "test_tool"


# ============================================================================
# Run tests if executed directly
# ============================================================================

if __name__ == "__main__":
    # Run without pytest for quick verification
    print("Testing Tool Registry...")

    # Clear registry
    ToolRegistry.clear()

    # Test 1: Basic decorator
    @tool(name="test_add", description="Add two numbers")
    def add(a: Annotated[int, "First number"], b: Annotated[int, "Second number"]) -> int:
        return a + b

    assert ToolRegistry.tool_exists("test_add"), "Tool registration failed"
    print("✓ Tool decorator works")

    # Test 2: Schema generation
    schemas = ToolRegistry.get_tool_schemas("any_agent", format="openai")
    assert len(schemas) > 0, "Schema generation failed"
    print("✓ Schema generation works")

    # Test 3: Tool execution
    result = ToolRegistry.execute_tool_sync("test_add", a=5, b=3)
    assert result.success and result.result == 8, "Tool execution failed"
    print("✓ Tool execution works")

    # Test 4: Agent filtering
    @tool(name="agent_tool", agents=["special_agent"])
    def special() -> str:
        return "special"

    agent_tools = ToolRegistry.get_tools_for_agent("special_agent")
    tool_names = [t.name for t in agent_tools]
    assert "agent_tool" in tool_names, "Agent filtering failed"
    print("✓ Agent filtering works")

    # Test 5: Built-in tools exist
    from tool_registry import web_search, file_read
    assert ToolRegistry.tool_exists("web_search"), "Built-in web_search not found"
    assert ToolRegistry.tool_exists("file_read"), "Built-in file_read not found"
    print("✓ Built-in tools registered")

    print("\nAll Tool Registry components verified!")
