"""
Tests for Configuration Loader

Comprehensive tests for ConfigLoader class and convenience functions.
"""

import pytest
import tempfile
import os
from pathlib import Path

from agent.config_loader import (
    ConfigLoader,
    ConfigValidationError,
    load_agents,
    load_tasks,
    validate_config,
    load_team
)
from agent.models.agent_config import AgentConfig, LLMModel
from agent.models.task_config import TaskConfig, TaskPriority


class TestConfigLoader:
    """Tests for ConfigLoader class"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "schemas").mkdir()
            yield config_dir

    @pytest.fixture
    def valid_agents_yaml(self, temp_config_dir):
        """Create a valid agents.yaml file"""
        content = """
researcher:
  role: Research Analyst
  goal: Conduct research
  backstory: Experienced researcher
  llm: gpt-4o
  tools:
    - web_search
    - file_read

writer:
  role: Content Writer
  goal: Create content
  backstory: Professional writer
  llm: claude-3-5-sonnet
"""
        agents_file = temp_config_dir / "agents.yaml"
        agents_file.write_text(content)
        return agents_file

    @pytest.fixture
    def valid_tasks_yaml(self, temp_config_dir):
        """Create a valid tasks.yaml file"""
        content = """
research_task:
  name: Research Task
  description: Do research
  expected_output: Research report
  agent: researcher
  priority: high

write_task:
  name: Write Task
  description: Write content
  expected_output: Written content
  agent: writer
  depends_on:
    - research_task
"""
        tasks_file = temp_config_dir / "tasks.yaml"
        tasks_file.write_text(content)
        return tasks_file

    def test_load_agents_basic(self, temp_config_dir, valid_agents_yaml):
        """Test loading agents from YAML"""
        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents()

        assert len(agents) == 2
        agent_names = [a.name for a in agents]
        assert "researcher" in agent_names
        assert "writer" in agent_names

    def test_load_agents_with_variables(self, temp_config_dir):
        """Test loading agents with variable substitution"""
        content = """
researcher:
  role: Research Analyst for {topic}
  goal: Research {topic}
  backstory: Expert in {topic}
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents(variables={"topic": "AI"})

        assert len(agents) == 1
        assert "AI" in agents[0].role
        assert "AI" in agents[0].goal

    def test_load_agents_list_format(self, temp_config_dir):
        """Test loading agents in list format"""
        content = """
- name: agent1
  role: Role 1
  goal: Goal 1
  backstory: Backstory 1
- name: agent2
  role: Role 2
  goal: Goal 2
  backstory: Backstory 2
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents()

        assert len(agents) == 2

    def test_load_agents_team_format(self, temp_config_dir):
        """Test loading agents in team format"""
        content = """
agents:
  - name: agent1
    role: Role 1
    goal: Goal 1
    backstory: Backstory 1
  - name: agent2
    role: Role 2
    goal: Goal 2
    backstory: Backstory 2
"""
        (temp_config_dir / "agents.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents()

        assert len(agents) == 2

    def test_load_agents_file_not_found(self, temp_config_dir):
        """Test error when agents file not found"""
        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_agents()
        assert "not found" in str(exc_info.value)

    def test_load_agents_invalid_yaml(self, temp_config_dir):
        """Test error with invalid YAML"""
        content = "invalid: yaml: content: ["
        (temp_config_dir / "agents.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_agents()
        assert "Invalid YAML" in str(exc_info.value)

    def test_load_agents_empty_file(self, temp_config_dir):
        """Test error with empty file"""
        (temp_config_dir / "agents.yaml").write_text("")

        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_agents()
        assert "Empty" in str(exc_info.value)

    def test_load_agents_duplicate_names(self, temp_config_dir):
        """Test error with duplicate agent names"""
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

        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_agents()
        assert "Duplicate" in str(exc_info.value)

    def test_load_tasks_basic(self, temp_config_dir, valid_agents_yaml, valid_tasks_yaml):
        """Test loading tasks from YAML"""
        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()  # Load agents first for validation
        tasks = loader.load_tasks()

        assert len(tasks) == 2
        task_ids = [t.id for t in tasks]
        assert "research_task" in task_ids
        assert "write_task" in task_ids

    def test_load_tasks_with_variables(self, temp_config_dir, valid_agents_yaml):
        """Test loading tasks with variable substitution"""
        content = """
task1:
  name: Research {topic}
  description: Research {topic} thoroughly
  expected_output: Report on {topic}
  agent: researcher
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()
        tasks = loader.load_tasks(variables={"topic": "AI"})

        assert len(tasks) == 1
        assert "AI" in tasks[0].description

    def test_load_tasks_list_format(self, temp_config_dir, valid_agents_yaml):
        """Test loading tasks in list format"""
        content = """
- id: task1
  name: Task 1
  description: Desc 1
  expected_output: Output 1
  agent: researcher
- id: task2
  name: Task 2
  description: Desc 2
  expected_output: Output 2
  agent: writer
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()
        tasks = loader.load_tasks()

        assert len(tasks) == 2

    def test_load_tasks_auto_generate_ids(self, temp_config_dir, valid_agents_yaml):
        """Test auto-generating task IDs"""
        content = """
- name: Task 1
  description: Desc 1
  expected_output: Output 1
  agent: researcher
- name: Task 2
  description: Desc 2
  expected_output: Output 2
  agent: writer
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()
        tasks = loader.load_tasks()

        assert tasks[0].id == "task_1"
        assert tasks[1].id == "task_2"

    def test_load_tasks_invalid_dependency(self, temp_config_dir, valid_agents_yaml):
        """Test error with invalid dependency"""
        content = """
task1:
  name: Task 1
  description: Desc
  expected_output: Output
  agent: researcher
  depends_on:
    - nonexistent_task
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_tasks()
        assert "unknown task" in str(exc_info.value).lower()

    def test_load_tasks_invalid_agent(self, temp_config_dir, valid_agents_yaml):
        """Test error with invalid agent assignment"""
        content = """
task1:
  name: Task 1
  description: Desc
  expected_output: Output
  agent: nonexistent_agent
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_tasks()
        assert "unknown agent" in str(exc_info.value).lower()

    def test_load_tasks_skip_agent_validation(self, temp_config_dir):
        """Test loading tasks without agent validation"""
        content = """
task1:
  name: Task 1
  description: Desc
  expected_output: Output
  agent: any_agent
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        tasks = loader.load_tasks(validate_agents=False)

        assert len(tasks) == 1

    def test_load_team(self, temp_config_dir, valid_agents_yaml, valid_tasks_yaml):
        """Test loading complete team configuration"""
        loader = ConfigLoader(temp_config_dir)
        team, graph = loader.load_team()

        assert team.name == "default_team"
        assert len(team.agents) == 2

        assert graph.name == "default_graph"
        assert len(graph.tasks) == 2

    def test_validate_config(self, temp_config_dir, valid_agents_yaml, valid_tasks_yaml):
        """Test complete configuration validation"""
        loader = ConfigLoader(temp_config_dir)
        result = loader.validate_config()

        assert result is True

    def test_validate_config_missing_backup_agent(self, temp_config_dir, valid_agents_yaml):
        """Test validation catches missing backup agents"""
        content = """
task1:
  name: Task 1
  description: Desc
  expected_output: Output
  agent: researcher
  backup_agents:
    - nonexistent_backup
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.validate_config()
        assert "unknown" in str(exc_info.value).lower()

    def test_reload_clears_cache(self, temp_config_dir, valid_agents_yaml):
        """Test reload clears cache"""
        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()

        assert loader.get_cached_agents() is not None

        loader.reload()

        assert loader.get_cached_agents() is None

    def test_caching(self, temp_config_dir, valid_agents_yaml, valid_tasks_yaml):
        """Test that loaded configs are cached"""
        loader = ConfigLoader(temp_config_dir)

        # First load
        agents1 = loader.load_agents()
        tasks1 = loader.load_tasks()

        # Get from cache
        cached_agents = loader.get_cached_agents()
        cached_tasks = loader.get_cached_tasks()

        assert cached_agents == agents1
        assert cached_tasks == tasks1

    def test_custom_path(self, temp_config_dir, valid_agents_yaml):
        """Test loading from custom path"""
        # Create a custom agents file
        custom_file = temp_config_dir / "custom_agents.yaml"
        content = """
custom_agent:
  role: Custom Role
  goal: Custom Goal
  backstory: Custom Backstory
"""
        custom_file.write_text(content)

        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents(path=custom_file)

        assert len(agents) == 1
        assert agents[0].name == "custom_agent"


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set up as default config dir
            config_dir = Path(tmpdir) / "agent" / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "schemas").mkdir()

            # Save original cwd
            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            yield config_dir

            os.chdir(original_cwd)

    @pytest.fixture
    def setup_valid_configs(self, temp_config_dir):
        """Set up valid config files"""
        agents_content = """
agent1:
  role: Role 1
  goal: Goal 1
  backstory: Backstory 1
"""
        (temp_config_dir / "agents.yaml").write_text(agents_content)

        tasks_content = """
task1:
  name: Task 1
  description: Desc 1
  expected_output: Output 1
  agent: agent1
"""
        (temp_config_dir / "tasks.yaml").write_text(tasks_content)

    def test_load_agents_function(self, temp_config_dir, setup_valid_configs):
        """Test load_agents convenience function"""
        agents = load_agents(temp_config_dir / "agents.yaml")
        assert len(agents) == 1

    def test_load_tasks_function(self, temp_config_dir, setup_valid_configs):
        """Test load_tasks convenience function"""
        tasks = load_tasks(temp_config_dir / "tasks.yaml")
        assert len(tasks) == 1

    def test_validate_config_function(self, temp_config_dir, setup_valid_configs):
        """Test validate_config convenience function"""
        result = validate_config(temp_config_dir)
        assert result is True

    def test_load_team_function(self, temp_config_dir, setup_valid_configs):
        """Test load_team convenience function"""
        team, graph = load_team(
            temp_config_dir / "agents.yaml",
            temp_config_dir / "tasks.yaml"
        )
        assert len(team.agents) == 1
        assert len(graph.tasks) == 1


class TestCircularDependencies:
    """Tests for circular dependency detection"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "schemas").mkdir()

            # Create agents file
            agents_content = """
agent1:
  role: Role
  goal: Goal
  backstory: Backstory
"""
            (config_dir / "agents.yaml").write_text(agents_content)

            yield config_dir

    def test_circular_dependency_simple(self, temp_config_dir):
        """Test simple circular dependency A -> B -> A"""
        content = """
task_a:
  name: Task A
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_b

task_b:
  name: Task B
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_a
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_tasks()
        assert "Circular" in str(exc_info.value)

    def test_circular_dependency_chain(self, temp_config_dir):
        """Test circular dependency A -> B -> C -> A"""
        content = """
task_a:
  name: Task A
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_c

task_b:
  name: Task B
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_a

task_c:
  name: Task C
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_b
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()

        with pytest.raises(ConfigValidationError) as exc_info:
            loader.load_tasks()
        assert "Circular" in str(exc_info.value)

    def test_no_circular_dependency(self, temp_config_dir):
        """Test valid dependency chain"""
        content = """
task_a:
  name: Task A
  description: Desc
  expected_output: Output
  agent: agent1

task_b:
  name: Task B
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_a

task_c:
  name: Task C
  description: Desc
  expected_output: Output
  agent: agent1
  depends_on:
    - task_a
    - task_b
"""
        (temp_config_dir / "tasks.yaml").write_text(content)

        loader = ConfigLoader(temp_config_dir)
        loader.load_agents()
        tasks = loader.load_tasks()

        assert len(tasks) == 3
