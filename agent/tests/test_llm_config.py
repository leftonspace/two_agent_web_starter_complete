"""
Tests for YAML-based LLM Configuration System

Tests configuration loading, role-based routing, cost optimization,
and integration with the router system.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.config import (
    LLMConfig,
    LLMConfigLoader,
    ConfigurableRouter,
    ProviderConfig,
    RoleConfig,
    ModelAssignment,
    CostOptimizationConfig,
    AgentRole,
    TaskCategory,
    load_config,
    create_router_from_yaml,
    generate_default_config,
    DEFAULT_CONFIG_TEMPLATE,
)


# ============================================================================
# Test YAML Config Loading
# ============================================================================

class TestLLMConfigLoader:
    """Tests for LLMConfigLoader class"""

    def test_load_from_string_basic(self):
        """Test loading config from YAML string"""
        yaml_str = """
routing_strategy: hybrid
providers:
  openai:
    api_key: test-key
    models:
      - gpt-4o
      - gpt-4o-mini
default_model: gpt-4o-mini
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        assert config.routing_strategy == "hybrid"
        assert "openai" in config.providers
        assert config.providers["openai"].api_key == "test-key"
        assert config.providers["openai"].models == ["gpt-4o", "gpt-4o-mini"]
        assert config.default_model == "gpt-4o-mini"

    def test_environment_variable_expansion(self):
        """Test environment variable expansion in config"""
        yaml_str = """
providers:
  openai:
    api_key: ${TEST_API_KEY}
    models:
      - gpt-4o
"""
        with patch.dict(os.environ, {"TEST_API_KEY": "expanded-key-123"}):
            loader = LLMConfigLoader()
            config = loader.load_from_string(yaml_str)

            assert config.providers["openai"].api_key == "expanded-key-123"

    def test_missing_env_var_preserved(self):
        """Test that missing env vars are preserved as-is"""
        yaml_str = """
providers:
  openai:
    api_key: ${NONEXISTENT_KEY}
    models:
      - gpt-4o
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        # Missing env var should be preserved
        assert "${NONEXISTENT_KEY}" in config.providers["openai"].api_key

    def test_load_from_file(self):
        """Test loading config from file"""
        yaml_content = """
routing_strategy: cost
providers:
  anthropic:
    api_key: test-anthropic-key
    models:
      - claude-3-5-sonnet
default_model: claude-3-5-sonnet
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            loader = LLMConfigLoader()
            config = loader.load(f.name)

            assert config.routing_strategy == "cost"
            assert "anthropic" in config.providers

            os.unlink(f.name)

    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises error"""
        loader = LLMConfigLoader()

        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path/config.yaml")


# ============================================================================
# Test Role Assignments
# ============================================================================

class TestRoleAssignments:
    """Tests for role-based model assignments"""

    def test_simple_role_assignment(self):
        """Test simple primary/fallback role assignment"""
        yaml_str = """
role_assignments:
  manager:
    primary: gpt-4o
    fallback: claude-3-5-sonnet
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        assert "manager" in config.role_assignments
        role = config.role_assignments["manager"]
        assert role.default_assignment is not None
        assert role.default_assignment.primary == "gpt-4o"
        assert role.default_assignment.fallback == "claude-3-5-sonnet"

    def test_task_specific_assignment(self):
        """Test task-specific role assignments"""
        yaml_str = """
role_assignments:
  employee:
    coding:
      primary: claude-3-5-sonnet
      fallback: deepseek-chat
    general:
      primary: gpt-4o-mini
      fallback: llama3.1:70b
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        employee = config.role_assignments["employee"]
        assert "coding" in employee.assignments
        assert "general" in employee.assignments

        coding = employee.assignments["coding"]
        assert coding.primary == "claude-3-5-sonnet"
        assert coding.fallback == "deepseek-chat"


# ============================================================================
# Test Cost Optimization
# ============================================================================

class TestCostOptimization:
    """Tests for cost optimization configuration"""

    def test_cost_optimization_loading(self):
        """Test loading cost optimization settings"""
        yaml_str = """
cost_optimization:
  prefer_local_for:
    - simple_queries
    - code_formatting
  use_premium_for:
    - security_reviews
  daily_budget: 50.0
  monthly_budget: 1000.0
  alert_threshold: 0.75
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        co = config.cost_optimization
        assert co is not None
        assert "simple_queries" in co.prefer_local_for
        assert "security_reviews" in co.use_premium_for
        assert co.daily_budget == 50.0
        assert co.monthly_budget == 1000.0
        assert co.alert_threshold == 0.75


# ============================================================================
# Test ConfigurableRouter
# ============================================================================

class TestConfigurableRouter:
    """Tests for ConfigurableRouter class"""

    def test_get_model_for_role(self):
        """Test role-based model selection"""
        yaml_str = """
providers:
  openai:
    api_key: test
    models: [gpt-4o, gpt-4o-mini]
  anthropic:
    api_key: test
    models: [claude-3-5-sonnet]

role_assignments:
  manager:
    primary: gpt-4o
    fallback: claude-3-5-sonnet
  employee:
    coding:
      primary: claude-3-5-sonnet
      fallback: gpt-4o-mini
    general:
      primary: gpt-4o-mini

default_model: gpt-4o-mini
default_provider: openai
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        # Test manager role
        provider, model = router.get_model_for_role("manager")
        assert model == "gpt-4o"
        assert provider == "openai"

        # Test employee coding
        provider, model = router.get_model_for_role("employee", "coding")
        assert model == "claude-3-5-sonnet"
        assert provider == "anthropic"

        # Test employee general
        provider, model = router.get_model_for_role("employee", "general")
        assert model == "gpt-4o-mini"

        # Test unknown role (should return defaults)
        provider, model = router.get_model_for_role("unknown_role")
        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_should_use_local(self):
        """Test local preference checking"""
        yaml_str = """
cost_optimization:
  prefer_local_for:
    - simple_queries
    - test_generation
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        assert router.should_use_local("simple_queries") is True
        assert router.should_use_local("test_generation") is True
        assert router.should_use_local("complex_reasoning") is False

    def test_should_use_premium(self):
        """Test premium preference checking"""
        yaml_str = """
cost_optimization:
  use_premium_for:
    - security_reviews
    - architecture_decisions
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        assert router.should_use_premium("security_reviews") is True
        assert router.should_use_premium("architecture_decisions") is True
        assert router.should_use_premium("simple_query") is False


# ============================================================================
# Test Model String Parsing
# ============================================================================

class TestModelStringParsing:
    """Tests for model string parsing"""

    def test_parse_openai_models(self):
        """Test parsing OpenAI model strings"""
        yaml_str = """
default_provider: openai
default_model: gpt-4o
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        provider, model = router._parse_model_string("gpt-4o")
        assert provider == "openai"
        assert model == "gpt-4o"

        provider, model = router._parse_model_string("gpt-4o-mini")
        assert provider == "openai"
        assert model == "gpt-4o-mini"

    def test_parse_anthropic_models(self):
        """Test parsing Anthropic model strings"""
        yaml_str = """
default_provider: openai
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        provider, model = router._parse_model_string("claude-3-5-sonnet")
        assert provider == "anthropic"

    def test_parse_local_models(self):
        """Test parsing local model strings"""
        yaml_str = """
default_provider: openai
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        provider, model = router._parse_model_string("llama3.1:70b")
        assert provider == "ollama"

    def test_parse_deepseek_models(self):
        """Test parsing DeepSeek model strings"""
        yaml_str = """
default_provider: openai
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)
        router = ConfigurableRouter(config)

        provider, model = router._parse_model_string("deepseek-chat")
        assert provider == "deepseek"


# ============================================================================
# Test Validation
# ============================================================================

class TestValidation:
    """Tests for configuration validation"""

    def test_validate_missing_api_key(self):
        """Test validation catches missing API keys"""
        yaml_str = """
providers:
  openai:
    api_key: ${MISSING_KEY}
    models: [gpt-4o]
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        issues = loader.validate(config)
        assert len(issues) > 0
        assert any("API key" in issue for issue in issues)

    def test_validate_no_models(self):
        """Test validation catches empty models list"""
        yaml_str = """
providers:
  openai:
    api_key: valid-key
    models: []
"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(yaml_str)

        issues = loader.validate(config)
        assert any("no models" in issue for issue in issues)


# ============================================================================
# Test Default Config Generation
# ============================================================================

class TestDefaultConfig:
    """Tests for default configuration generation"""

    def test_generate_default_config(self):
        """Test generating default config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config" / "llm_config.yaml"
            generate_default_config(output_path)

            assert output_path.exists()

            # Verify it can be loaded
            loader = LLMConfigLoader()
            config = loader.load(output_path)

            assert config.routing_strategy == "hybrid"
            assert "openai" in config.providers

    def test_default_template_is_valid(self):
        """Test that DEFAULT_CONFIG_TEMPLATE is valid YAML"""
        loader = LLMConfigLoader()
        config = loader.load_from_string(DEFAULT_CONFIG_TEMPLATE)

        assert config is not None
        assert config.routing_strategy == "hybrid"


# ============================================================================
# Test Enums
# ============================================================================

class TestEnums:
    """Tests for configuration enums"""

    def test_agent_role_enum(self):
        """Test AgentRole enum values"""
        assert AgentRole.MANAGER.value == "manager"
        assert AgentRole.SUPERVISOR.value == "supervisor"
        assert AgentRole.EMPLOYEE.value == "employee"

    def test_task_category_enum(self):
        """Test TaskCategory enum values"""
        assert TaskCategory.CODING.value == "coding"
        assert TaskCategory.GENERAL.value == "general"
        assert TaskCategory.REASONING.value == "reasoning"


# ============================================================================
# Run tests if executed directly
# ============================================================================

if __name__ == "__main__":
    print("Testing LLM Config System...")

    # Test 1: Basic YAML loading
    yaml_str = """
routing_strategy: hybrid
providers:
  openai:
    api_key: test-key
    models: [gpt-4o, gpt-4o-mini]
default_model: gpt-4o-mini
"""
    loader = LLMConfigLoader()
    config = loader.load_from_string(yaml_str)
    assert config.routing_strategy == "hybrid"
    assert config.providers["openai"].api_key == "test-key"
    print("✓ Basic YAML loading works")

    # Test 2: Environment variable expansion
    os.environ["TEST_KEY"] = "expanded-value"
    yaml_str = """
providers:
  openai:
    api_key: ${TEST_KEY}
    models: [gpt-4o]
"""
    config = loader.load_from_string(yaml_str)
    assert config.providers["openai"].api_key == "expanded-value"
    print("✓ Environment variable expansion works")

    # Test 3: Role assignments
    yaml_str = """
role_assignments:
  manager:
    primary: gpt-4o
    fallback: claude-3-5-sonnet
  employee:
    coding:
      primary: claude-3-5-sonnet
      fallback: deepseek-chat
"""
    config = loader.load_from_string(yaml_str)
    assert config.role_assignments["manager"].default_assignment.primary == "gpt-4o"
    assert config.role_assignments["employee"].assignments["coding"].primary == "claude-3-5-sonnet"
    print("✓ Role assignments work")

    # Test 4: Cost optimization
    yaml_str = """
cost_optimization:
  prefer_local_for:
    - simple_queries
  use_premium_for:
    - security_reviews
  daily_budget: 50.0
"""
    config = loader.load_from_string(yaml_str)
    router = ConfigurableRouter(config)
    assert router.should_use_local("simple_queries") is True
    assert router.should_use_premium("security_reviews") is True
    print("✓ Cost optimization works")

    # Test 5: Model for role
    yaml_str = """
providers:
  openai:
    api_key: test
    models: [gpt-4o, gpt-4o-mini]
role_assignments:
  manager:
    primary: gpt-4o
default_model: gpt-4o-mini
default_provider: openai
"""
    config = loader.load_from_string(yaml_str)
    router = ConfigurableRouter(config)
    provider, model = router.get_model_for_role("manager")
    assert model == "gpt-4o"
    assert provider == "openai"
    print("✓ Model for role works")

    # Test 6: Model string parsing
    provider, model = router._parse_model_string("claude-3-5-sonnet")
    assert provider == "anthropic"
    provider, model = router._parse_model_string("deepseek-chat")
    assert provider == "deepseek"
    provider, model = router._parse_model_string("llama3.1:70b")
    assert provider == "ollama"
    print("✓ Model string parsing works")

    # Test 7: Default config template
    config = loader.load_from_string(DEFAULT_CONFIG_TEMPLATE)
    assert config.routing_strategy == "hybrid"
    assert "openai" in config.providers
    print("✓ Default config template is valid")

    print()
    print("All LLM Config System tests passed!")
