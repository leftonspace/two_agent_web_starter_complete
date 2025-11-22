"""
Tests for Configuration Validator

Comprehensive tests for ConfigValidator class and validation functions.
"""

import pytest
import tempfile
from pathlib import Path

from agent.validators.config_validator import (
    ConfigValidator,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    validate_agents_config,
    validate_tasks_config,
    validate_full_config
)


class TestValidationResult:
    """Tests for ValidationResult class"""

    def test_initial_state(self):
        """Test initial validation result state"""
        result = ValidationResult()
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.info) == 0

    def test_add_error(self):
        """Test adding an error"""
        result = ValidationResult()
        result.add_error("Test error", path="test.path", suggestion="Fix it")

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "Test error"
        assert result.errors[0].path == "test.path"
        assert result.errors[0].suggestion == "Fix it"

    def test_add_warning(self):
        """Test adding a warning"""
        result = ValidationResult()
        result.add_warning("Test warning", path="test.path")

        assert result.is_valid is True  # Warnings don't invalidate
        assert len(result.warnings) == 1
        assert result.warnings[0].message == "Test warning"

    def test_add_info(self):
        """Test adding info message"""
        result = ValidationResult()
        result.add_info("Test info", path="test.path")

        assert result.is_valid is True
        assert len(result.info) == 1

    def test_merge_results(self):
        """Test merging validation results"""
        result1 = ValidationResult()
        result1.add_error("Error 1")

        result2 = ValidationResult()
        result2.add_warning("Warning 1")
        result2.stats['count'] = 5

        result1.merge(result2)

        assert result1.is_valid is False
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 1
        assert result1.stats.get('count') == 5

    def test_to_dict(self):
        """Test converting result to dictionary"""
        result = ValidationResult()
        result.add_error("Error 1")
        result.add_warning("Warning 1")
        result.stats['test'] = 'value'

        d = result.to_dict()

        assert d['is_valid'] is False
        assert d['error_count'] == 1
        assert d['warning_count'] == 1
        assert 'test' in d['stats']

    def test_string_representation(self):
        """Test string representation"""
        result = ValidationResult()
        result.add_error("Test error")

        s = str(result)

        assert "FAILED" in s
        assert "Test error" in s


class TestValidationError:
    """Tests for ValidationError class"""

    def test_error_creation(self):
        """Test creating validation error"""
        error = ValidationError(
            message="Test message",
            severity=ValidationSeverity.ERROR,
            path="test.path",
            suggestion="Fix it"
        )

        assert error.message == "Test message"
        assert error.severity == ValidationSeverity.ERROR
        assert error.path == "test.path"
        assert error.suggestion == "Fix it"

    def test_string_representation(self):
        """Test string representation of error"""
        error = ValidationError(
            message="Test message",
            severity=ValidationSeverity.ERROR,
            path="test.path",
            suggestion="Fix it"
        )

        s = str(error)

        assert "ERROR" in s
        assert "test.path" in s
        assert "Test message" in s
        assert "Fix it" in s


class TestConfigValidator:
    """Tests for ConfigValidator class"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "schemas").mkdir()
            yield config_dir

    @pytest.fixture
    def valid_agents(self, temp_config_dir):
        """Create valid agents.yaml"""
        content = """
researcher:
  role: Research Analyst
  goal: Conduct research
  backstory: Experienced researcher
  llm: gpt-4o
  temperature: 0.7
  tools:
    - web_search
    - file_read

writer:
  role: Content Writer
  goal: Create content
  backstory: Professional writer
"""
        (temp_config_dir / "agents.yaml").write_text(content)

    @pytest.fixture
    def valid_tasks(self, temp_config_dir):
        """Create valid tasks.yaml"""
        content = """
task1:
  name: Research Task
  description: Do research
  expected_output: Research report
  agent: researcher
  priority: high

task2:
  name: Write Task
  description: Write content
  expected_output: Written content
  agent: writer
  depends_on:
    - task1
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

    def test_validate_agents_valid(self, temp_config_dir, valid_agents):
        """Test validating valid agents"""
        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is True
        assert result.stats.get('agent_count') == 2

    def test_validate_agents_missing_file(self, temp_config_dir):
        """Test validation with missing file"""
        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("not found" in str(e) for e in result.errors)

    def test_validate_agents_invalid_yaml(self, temp_config_dir):
        """Test validation with invalid YAML"""
        (temp_config_dir / "agents.yaml").write_text("invalid: yaml: [")

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("Invalid YAML" in str(e) for e in result.errors)

    def test_validate_agents_empty_file(self, temp_config_dir):
        """Test validation with empty file"""
        (temp_config_dir / "agents.yaml").write_text("")

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("Empty" in str(e) for e in result.errors)

    def test_validate_agents_missing_required_fields(self, temp_config_dir):
        """Test validation with missing required fields"""
        content = """
agent1:
  role: Only role provided
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("goal" in str(e).lower() for e in result.errors)

    def test_validate_agents_invalid_llm(self, temp_config_dir):
        """Test validation with invalid LLM model"""
        content = """
agent1:
  role: Role
  goal: Goal
  backstory: Backstory
  llm: invalid-model
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("invalid" in str(e).lower() and "llm" in str(e).lower() for e in result.errors)

    def test_validate_agents_invalid_temperature(self, temp_config_dir):
        """Test validation with invalid temperature"""
        content = """
agent1:
  role: Role
  goal: Goal
  backstory: Backstory
  temperature: 3.0
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("temperature" in str(e).lower() for e in result.errors)

    def test_validate_agents_invalid_tools(self, temp_config_dir):
        """Test validation with invalid tools"""
        content = """
agent1:
  role: Role
  goal: Goal
  backstory: Backstory
  tools:
    - invalid_tool
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("tool" in str(e).lower() for e in result.errors)

    def test_validate_agents_duplicate_names(self, temp_config_dir):
        """Test validation with duplicate agent names"""
        content = """
- name: agent1
  role: Role 1
  goal: Goal 1
  backstory: Backstory 1
- name: agent1
  role: Role 2
  goal: Goal 2
  backstory: Backstory 2
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        assert result.is_valid is False
        assert any("duplicate" in str(e).lower() for e in result.errors)

    def test_validate_agents_with_variables(self, temp_config_dir):
        """Test validation detects unsubstituted variables"""
        content = """
agent1:
  role: Expert in {topic}
  goal: Research {topic}
  backstory: Background in {topic}
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_agents()

        # Should pass but have info messages about variables
        assert result.is_valid is True
        assert any("variable" in str(i).lower() for i in result.info)

    def test_validate_tasks_valid(self, temp_config_dir, valid_agents, valid_tasks):
        """Test validating valid tasks"""
        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks(agents={"researcher", "writer"})

        assert result.is_valid is True
        assert result.stats.get('task_count') == 2

    def test_validate_tasks_missing_file(self, temp_config_dir):
        """Test validation with missing tasks file"""
        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("not found" in str(e) for e in result.errors)

    def test_validate_tasks_missing_required_fields(self, temp_config_dir):
        """Test validation with missing required fields"""
        content = """
task1:
  name: Only name
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("description" in str(e).lower() or "agent" in str(e).lower() for e in result.errors)

    def test_validate_tasks_unknown_agent(self, temp_config_dir):
        """Test validation with unknown agent"""
        content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: unknown_agent
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks(agents={"agent1", "agent2"})

        assert result.is_valid is False
        assert any("unknown" in str(e).lower() and "agent" in str(e).lower() for e in result.errors)

    def test_validate_tasks_unknown_dependency(self, temp_config_dir):
        """Test validation with unknown dependency"""
        content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: agent1
  depends_on:
    - nonexistent_task
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("unknown" in str(e).lower() and "depend" in str(e).lower() for e in result.errors)

    def test_validate_tasks_self_dependency(self, temp_config_dir):
        """Test validation with self dependency"""
        content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: agent1
  depends_on:
    - task1
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("itself" in str(e).lower() for e in result.errors)

    def test_validate_tasks_invalid_priority(self, temp_config_dir):
        """Test validation with invalid priority"""
        content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: agent1
  priority: invalid
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("priority" in str(e).lower() for e in result.errors)

    def test_validate_tasks_invalid_output_format(self, temp_config_dir):
        """Test validation with invalid output format"""
        content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: agent1
  output_format: invalid
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("output_format" in str(e).lower() for e in result.errors)

    def test_validate_tasks_circular_dependency(self, temp_config_dir):
        """Test validation detects circular dependencies"""
        content = """
task_a:
  name: Task A
  description: Description
  expected_output: Output
  agent: agent1
  depends_on:
    - task_b

task_b:
  name: Task B
  description: Description
  expected_output: Output
  agent: agent1
  depends_on:
    - task_a
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_tasks()

        assert result.is_valid is False
        assert any("circular" in str(e).lower() for e in result.errors)

    def test_validate_full_valid(self, temp_config_dir, valid_agents, valid_tasks):
        """Test full validation with valid config"""
        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_full()

        assert result.is_valid is True

    def test_validate_full_cross_validation(self, temp_config_dir, valid_agents):
        """Test full validation catches cross-validation errors"""
        # Task references agent not in agents.yaml
        content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: nonexistent
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        validator = ConfigValidator(temp_config_dir)
        result = validator.validate_full()

        assert result.is_valid is False


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "schemas").mkdir()

            # Create valid configs
            agents_content = """
agent1:
  role: Role
  goal: Goal
  backstory: Backstory
"""
            (config_dir / "agents.yaml").write_text(agents_content)

            tasks_content = """
task1:
  name: Task 1
  description: Description
  expected_output: Output
  agent: agent1
"""
            (config_dir / "tasks.yaml").write_text(tasks_content)

            yield config_dir

    def test_validate_agents_config(self, temp_config_dir):
        """Test validate_agents_config function"""
        result = validate_agents_config(temp_config_dir / "agents.yaml")
        assert result.is_valid is True

    def test_validate_tasks_config(self, temp_config_dir):
        """Test validate_tasks_config function"""
        result = validate_tasks_config(temp_config_dir / "tasks.yaml")
        assert result.is_valid is True

    def test_validate_full_config(self, temp_config_dir):
        """Test validate_full_config function"""
        result = validate_full_config(temp_config_dir)
        assert result.is_valid is True
