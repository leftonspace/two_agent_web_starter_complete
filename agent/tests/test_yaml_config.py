"""
Comprehensive Test Suite for YAML Configuration System

Tests for agent configuration, task configuration, and configuration loading.
"""

import pytest
import tempfile
import yaml
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from agent.config_loader import ConfigLoader, load_agents, load_tasks, validate_config, ConfigValidationError
from agent.models.agent_config import AgentConfig, AgentTeam, LLMModel
from agent.models.task_config import TaskConfig, TaskGraph, TaskPriority, TaskStatus


class TestAgentConfig:
    """Test agent configuration models and loading"""

    def test_basic_agent_creation(self):
        """Test creating a basic agent configuration"""
        agent = AgentConfig(
            name="test_agent",
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory"
        )

        assert agent.name == "test_agent"
        assert agent.role == "Test Role"
        assert agent.llm == LLMModel.GPT_4O_MINI  # Default
        assert agent.temperature == 0.7  # Default
        assert agent.max_iterations == 15  # Default
        assert agent.verbose is False  # Default

    def test_agent_with_all_fields(self):
        """Test agent with all optional fields specified"""
        agent = AgentConfig(
            name="advanced_agent",
            role="Advanced Role",
            goal="Complex Goal",
            backstory="Detailed Backstory",
            llm=LLMModel.CLAUDE_35_SONNET,
            temperature=0.9,
            max_iterations=50,
            max_tokens=4000,
            tools=["web_search", "file_read"],
            capabilities=["analysis", "synthesis"],
            verbose=True,
            allow_delegation=False,
            require_approval=True,
            custom_attributes={"level": "expert"}
        )

        assert agent.llm == LLMModel.CLAUDE_35_SONNET
        assert agent.temperature == 0.9
        assert agent.max_iterations == 50
        assert agent.max_tokens == 4000
        assert "web_search" in agent.tools
        assert "analysis" in agent.capabilities
        assert agent.verbose is True
        assert agent.allow_delegation is False
        assert agent.require_approval is True
        assert agent.custom_attributes["level"] == "expert"

    def test_agent_name_validation(self):
        """Test agent name validation rules"""
        # Valid names
        valid_names = ["agent1", "test_agent", "agent-123", "my_agent"]
        for name in valid_names:
            agent = AgentConfig(
                name=name,
                role="Test",
                goal="Test",
                backstory="Test"
            )
            assert agent.name == name.lower()

        # Invalid names
        invalid_names = ["", " ", "agent@123", "agent.test", "agent/test"]
        for name in invalid_names:
            with pytest.raises(ValueError):
                AgentConfig(
                    name=name,
                    role="Test",
                    goal="Test",
                    backstory="Test"
                )

    def test_tool_validation(self):
        """Test tool validation"""
        # Valid tools
        agent = AgentConfig(
            name="test",
            role="Test",
            goal="Test",
            backstory="Test",
            tools=["web_search", "file_read", "code_execute"]
        )
        assert len(agent.tools) == 3

        # Invalid tool
        with pytest.raises(ValueError, match="Unknown tool"):
            AgentConfig(
                name="test",
                role="Test",
                goal="Test",
                backstory="Test",
                tools=["invalid_tool"]
            )

    def test_variable_substitution(self):
        """Test variable substitution in agent fields"""
        agent = AgentConfig(
            name="researcher",
            role="Expert in {domain}",
            goal="Master {domain} and {skill}",
            backstory="Specialized in {domain} for {years} years"
        )

        substituted = agent.substitute_variables({
            "domain": "AI",
            "skill": "machine learning",
            "years": "10"
        })

        assert substituted.role == "Expert in AI"
        assert substituted.goal == "Master AI and machine learning"
        assert substituted.backstory == "Specialized in AI for 10 years"

    def test_variable_substitution_missing(self):
        """Test error on missing variable substitution"""
        agent = AgentConfig(
            name="test",
            role="Expert in {domain}",
            goal="Test",
            backstory="Test"
        )

        with pytest.raises(ValueError, match="Unsubstituted variables"):
            agent.substitute_variables({"other": "value"})

    def test_agent_team(self):
        """Test agent team functionality"""
        agents = [
            AgentConfig(name="agent1", role="Role1", goal="Goal1", backstory="Story1"),
            AgentConfig(name="agent2", role="Role2", goal="Goal2", backstory="Story2")
        ]

        team = AgentTeam(
            name="test_team",
            description="Test team",
            agents=agents
        )

        assert len(team.agents) == 2
        assert team.get_agent("agent1") is not None
        assert team.get_agent("agent1").role == "Role1"
        assert team.get_agent("nonexistent") is None

    def test_team_duplicate_validation(self):
        """Test team validates no duplicate agent names"""
        agents = [
            AgentConfig(name="agent1", role="Role1", goal="Goal1", backstory="Story1"),
            AgentConfig(name="agent1", role="Role2", goal="Goal2", backstory="Story2")  # Duplicate
        ]

        team = AgentTeam(
            name="test_team",
            description="Test team",
            agents=agents
        )

        with pytest.raises(ValueError, match="Duplicate agent names"):
            team.validate_no_duplicates()


class TestTaskConfig:
    """Test task configuration models"""

    def test_basic_task_creation(self):
        """Test creating a basic task"""
        task = TaskConfig(
            id="task1",
            name="Test Task",
            description="Do something",
            expected_output="Result",
            agent="test_agent"
        )

        assert task.id == "task1"
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert task.max_retries == 3
        assert task.output_format == "text"

    def test_task_with_dependencies(self):
        """Test task with dependencies"""
        task = TaskConfig(
            id="task3",
            name="Final Task",
            description="Depends on others",
            expected_output="Final result",
            agent="agent1",
            depends_on=["task1", "task2"],
            blocks=["task4"]
        )

        assert len(task.depends_on) == 2
        assert "task1" in task.depends_on
        assert "task4" in task.blocks

    def test_task_self_dependency_validation(self):
        """Test that task cannot depend on itself"""
        with pytest.raises(ValueError):
            TaskConfig(
                id="task1",
                name="Test",
                description="Test",
                expected_output="Test",
                agent="agent1",
                depends_on=["task1"]  # Self-reference
            )

    def test_task_circular_dependency_validation(self):
        """Test circular dependency detection"""
        with pytest.raises(ValueError, match="Circular dependency"):
            TaskConfig(
                id="task1",
                name="Test",
                description="Test",
                expected_output="Test",
                agent="agent1",
                depends_on=["task2"],
                blocks=["task2"]  # Creates circle
            )

    def test_task_is_ready(self):
        """Test task readiness check"""
        task = TaskConfig(
            id="task3",
            name="Test",
            description="Test",
            expected_output="Test",
            agent="agent1",
            depends_on=["task1", "task2"]
        )

        assert task.is_ready([]) is False
        assert task.is_ready(["task1"]) is False
        assert task.is_ready(["task1", "task2"]) is True
        assert task.is_ready(["task1", "task2", "task3"]) is True

    def test_task_graph(self):
        """Test task graph functionality"""
        tasks = [
            TaskConfig(id="task1", name="First", description="D1", expected_output="E1", agent="a1"),
            TaskConfig(id="task2", name="Second", description="D2", expected_output="E2", agent="a2", depends_on=["task1"]),
            TaskConfig(id="task3", name="Third", description="D3", expected_output="E3", agent="a3", depends_on=["task1", "task2"])
        ]

        graph = TaskGraph(
            name="test_graph",
            description="Test",
            tasks=tasks
        )

        # Test get_task
        assert graph.get_task("task1") is not None
        assert graph.get_task("task1").name == "First"

        # Test get_ready_tasks
        ready = graph.get_ready_tasks([])
        assert len(ready) == 1
        assert ready[0].id == "task1"

        ready = graph.get_ready_tasks(["task1"])
        assert len(ready) == 1
        assert ready[0].id == "task2"

        ready = graph.get_ready_tasks(["task1", "task2"])
        assert len(ready) == 1
        assert ready[0].id == "task3"

    def test_task_graph_execution_order(self):
        """Test getting execution order for parallel execution"""
        tasks = [
            TaskConfig(id="task1", name="T1", description="D", expected_output="E", agent="a"),
            TaskConfig(id="task2", name="T2", description="D", expected_output="E", agent="a"),
            TaskConfig(id="task3", name="T3", description="D", expected_output="E", agent="a", depends_on=["task1"]),
            TaskConfig(id="task4", name="T4", description="D", expected_output="E", agent="a", depends_on=["task2"]),
            TaskConfig(id="task5", name="T5", description="D", expected_output="E", agent="a", depends_on=["task3", "task4"])
        ]

        graph = TaskGraph(name="test", description="test", tasks=tasks)
        levels = graph.get_execution_order()

        assert len(levels) == 3
        assert set(levels[0]) == {"task1", "task2"}  # Can run in parallel
        assert set(levels[1]) == {"task3", "task4"}  # Can run in parallel
        assert set(levels[2]) == {"task5"}


class TestConfigLoader:
    """Test configuration loading from YAML files"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory with config files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "schemas").mkdir()

            # Create agents.yaml
            agents_data = {
                "researcher": {
                    "role": "Research Expert",
                    "goal": "Find information",
                    "backstory": "Expert researcher",
                    "tools": ["web_search"]
                },
                "writer": {
                    "role": "Content Writer",
                    "goal": "Create content",
                    "backstory": "Professional writer",
                    "llm": "claude-3-5-sonnet"
                }
            }

            with open(config_dir / "agents.yaml", 'w') as f:
                yaml.dump(agents_data, f)

            # Create tasks.yaml
            tasks_data = {
                "research_task": {
                    "name": "Research",
                    "description": "Research the topic",
                    "expected_output": "Research report",
                    "agent": "researcher",
                    "priority": "high"
                },
                "write_task": {
                    "name": "Write",
                    "description": "Write content",
                    "expected_output": "Article",
                    "agent": "writer",
                    "depends_on": ["research_task"]
                }
            }

            with open(config_dir / "tasks.yaml", 'w') as f:
                yaml.dump(tasks_data, f)

            yield config_dir

    def test_load_agents_from_yaml(self, temp_config_dir):
        """Test loading agents from YAML file"""
        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents()

        assert len(agents) == 2
        assert any(a.name == "researcher" for a in agents)
        assert any(a.name == "writer" for a in agents)

        researcher = next(a for a in agents if a.name == "researcher")
        assert researcher.role == "Research Expert"
        assert "web_search" in researcher.tools

        writer = next(a for a in agents if a.name == "writer")
        assert writer.llm == LLMModel.CLAUDE_35_SONNET

    def test_load_tasks_from_yaml(self, temp_config_dir):
        """Test loading tasks from YAML file"""
        loader = ConfigLoader(temp_config_dir)
        tasks = loader.load_tasks(validate_agents=False)

        assert len(tasks) == 2

        research = next(t for t in tasks if t.id == "research_task")
        assert research.name == "Research"
        assert research.priority == TaskPriority.HIGH
        assert len(research.depends_on) == 0

        write = next(t for t in tasks if t.id == "write_task")
        assert write.name == "Write"
        assert "research_task" in write.depends_on

    def test_load_with_variables(self, temp_config_dir):
        """Test loading with variable substitution"""
        # Create config with variables
        agents_data = [{
            "name": "expert",
            "role": "Expert in {domain}",
            "goal": "Master {domain}",
            "backstory": "{years} years in {domain}"
        }]

        with open(temp_config_dir / "agents_vars.yaml", 'w') as f:
            yaml.dump(agents_data, f)

        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents(
            path=temp_config_dir / "agents_vars.yaml",
            variables={"domain": "AI", "years": "10"}
        )

        assert agents[0].role == "Expert in AI"
        assert agents[0].goal == "Master AI"
        assert agents[0].backstory == "10 years in AI"

    def test_validate_task_agents(self, temp_config_dir):
        """Test validation of task agent assignments"""
        loader = ConfigLoader(temp_config_dir)

        # Should succeed with valid agents
        tasks = loader.load_tasks(validate_agents=True)
        assert len(tasks) == 2

        # Add task with invalid agent
        tasks_data = {
            "bad_task": {
                "name": "Bad",
                "description": "Bad task",
                "expected_output": "Nothing",
                "agent": "nonexistent_agent"
            }
        }

        with open(temp_config_dir / "bad_tasks.yaml", 'w') as f:
            yaml.dump(tasks_data, f)

        with pytest.raises(ConfigValidationError, match="unknown agent"):
            loader.load_tasks(
                path=temp_config_dir / "bad_tasks.yaml",
                validate_agents=True
            )

    def test_circular_dependency_detection(self, temp_config_dir):
        """Test detection of circular task dependencies"""
        tasks_data = {
            "task1": {
                "name": "Task 1",
                "description": "First",
                "expected_output": "Output",
                "agent": "researcher",
                "depends_on": ["task3"]
            },
            "task2": {
                "name": "Task 2",
                "description": "Second",
                "expected_output": "Output",
                "agent": "writer",
                "depends_on": ["task1"]
            },
            "task3": {
                "name": "Task 3",
                "description": "Third",
                "expected_output": "Output",
                "agent": "researcher",
                "depends_on": ["task2"]  # Creates cycle
            }
        }

        with open(temp_config_dir / "circular_tasks.yaml", 'w') as f:
            yaml.dump(tasks_data, f)

        loader = ConfigLoader(temp_config_dir)
        with pytest.raises(ConfigValidationError, match="Circular dependency"):
            loader.load_tasks(
                path=temp_config_dir / "circular_tasks.yaml",
                validate_agents=False
            )

    def test_load_team(self, temp_config_dir):
        """Test loading complete team configuration"""
        loader = ConfigLoader(temp_config_dir)
        team, graph = loader.load_team()

        assert team.name == "default_team"
        assert len(team.agents) == 2
        assert graph.name == "default_graph"
        assert len(graph.tasks) == 2

    def test_validate_config(self, temp_config_dir):
        """Test complete configuration validation"""
        loader = ConfigLoader(temp_config_dir)

        # Should pass with valid config
        assert loader.validate_config() is True

        # Test with invalid task agent
        tasks_data = {
            "tasks": [{
                "id": "bad_task",
                "name": "Bad",
                "description": "Bad task",
                "expected_output": "Nothing",
                "agent": "nonexistent"
            }]
        }

        with open(temp_config_dir / "tasks.yaml", 'w') as f:
            yaml.dump(tasks_data, f)

        with pytest.raises(ConfigValidationError):
            loader.validate_config()

    def test_multiple_format_support(self, temp_config_dir):
        """Test different YAML format support"""
        # Test list format for agents
        agents_list = [
            {
                "name": "agent1",
                "role": "Role 1",
                "goal": "Goal 1",
                "backstory": "Story 1"
            },
            {
                "name": "agent2",
                "role": "Role 2",
                "goal": "Goal 2",
                "backstory": "Story 2"
            }
        ]

        with open(temp_config_dir / "agents_list.yaml", 'w') as f:
            yaml.dump(agents_list, f)

        loader = ConfigLoader(temp_config_dir)
        agents = loader.load_agents(path=temp_config_dir / "agents_list.yaml")
        assert len(agents) == 2

        # Test team format
        team_format = {
            "agents": agents_list
        }

        with open(temp_config_dir / "agents_team.yaml", 'w') as f:
            yaml.dump(team_format, f)

        agents = loader.load_agents(path=temp_config_dir / "agents_team.yaml")
        assert len(agents) == 2

    def test_convenience_functions(self, temp_config_dir):
        """Test module-level convenience functions"""
        # Test with actual loader
        agents = load_agents(temp_config_dir / "agents.yaml")
        assert len(agents) == 2

        tasks = load_tasks(temp_config_dir / "tasks.yaml")
        assert len(tasks) == 2

        assert validate_config(temp_config_dir) is True


class TestIntegration:
    """Integration tests for complete configuration system"""

    def test_full_workflow(self, tmp_path):
        """Test complete workflow from YAML to execution"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Create comprehensive configuration
        agents_yaml = """
researcher:
  role: Research specialist in {topic}
  goal: Find comprehensive information about {topic}
  backstory: Expert researcher with deep knowledge
  llm: gpt-4o
  tools:
    - web_search
    - file_read
  max_iterations: 20

analyzer:
  role: Data Analyst
  goal: Analyze research findings and extract insights
  backstory: Statistical expert with business acumen
  llm: claude-3-5-sonnet
  tools:
    - file_read
    - file_write

writer:
  role: Content Creator
  goal: Transform analysis into engaging content
  backstory: Professional writer with SEO expertise
  llm: gpt-4o-mini
  temperature: 0.8
  tools:
    - file_write
        """

        tasks_yaml = """
research:
  name: Conduct Research
  description: Research {topic} thoroughly
  expected_output: Comprehensive research document
  agent: researcher
  priority: high
  output_file: research.md

analysis:
  name: Analyze Findings
  description: Extract key insights from research
  expected_output: Analysis report with recommendations
  agent: analyzer
  depends_on:
    - research
  priority: high
  output_file: analysis.json

content:
  name: Create Content
  description: Write blog post based on analysis
  expected_output: SEO-optimized blog post
  agent: writer
  depends_on:
    - analysis
  priority: medium
  output_file: blog.html
  success_criteria:
    - "Contains title and meta tags"
    - "Includes at least 5 sections"
    - "Word count over 1000"
        """

        with open(config_dir / "agents.yaml", 'w') as f:
            f.write(agents_yaml)

        with open(config_dir / "tasks.yaml", 'w') as f:
            f.write(tasks_yaml)

        # Load and validate
        loader = ConfigLoader(config_dir)

        # Load with variables
        agents = loader.load_agents(variables={"topic": "AI Ethics"})
        tasks = loader.load_tasks(variables={"topic": "AI Ethics"})

        # Verify substitution
        researcher = next(a for a in agents if a.name == "researcher")
        assert "AI Ethics" in researcher.role
        assert "AI Ethics" in researcher.goal

        research_task = next(t for t in tasks if t.id == "research")
        assert "AI Ethics" in research_task.description

        # Verify dependencies
        graph = TaskGraph(name="workflow", description="Test workflow", tasks=tasks)

        # Check execution order
        levels = graph.get_execution_order()
        assert len(levels) == 3
        assert levels[0] == ["research"]
        assert levels[1] == ["analysis"]
        assert levels[2] == ["content"]

        # Simulate execution
        completed = []
        for level in levels:
            ready = graph.get_ready_tasks(completed)
            assert len(ready) == len(level)
            for task in ready:
                assert task.id in level
                completed.append(task.id)

        # Validate complete configuration
        assert loader.validate_config() is True


class TestPerformance:
    """Test performance and edge cases"""

    def test_large_configuration(self, tmp_path):
        """Test handling large configurations"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Generate large configuration
        agents_data = {}
        for i in range(100):
            agents_data[f"agent_{i}"] = {
                "role": f"Role {i}",
                "goal": f"Goal {i}",
                "backstory": f"Story {i}",
                "tools": ["web_search"] if i % 2 == 0 else ["file_read"]
            }

        tasks_data = {}
        for i in range(200):
            task = {
                "name": f"Task {i}",
                "description": f"Description {i}",
                "expected_output": f"Output {i}",
                "agent": f"agent_{i % 100}"
            }
            # Add dependencies to create complex graph
            if i > 0:
                task["depends_on"] = [f"task_{j}" for j in range(max(0, i-3), i)]
            tasks_data[f"task_{i}"] = task

        with open(config_dir / "agents.yaml", 'w') as f:
            yaml.dump(agents_data, f)

        with open(config_dir / "tasks.yaml", 'w') as f:
            yaml.dump(tasks_data, f)

        # Load and measure performance
        loader = ConfigLoader(config_dir)

        start = time.time()
        agents = loader.load_agents()
        agents_time = time.time() - start

        start = time.time()
        tasks = loader.load_tasks(validate_agents=False)
        tasks_time = time.time() - start

        assert len(agents) == 100
        assert len(tasks) == 200
        assert agents_time < 1.0  # Should load in under 1 second
        assert tasks_time < 2.0  # Should load in under 2 seconds

    def test_malformed_yaml(self, tmp_path):
        """Test handling of malformed YAML"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Write malformed YAML
        with open(config_dir / "bad.yaml", 'w') as f:
            f.write("""
agent1:
  role: Test
  goal: Test
  backstory: Test
  tools:
    - web_search
    invalid_indent: here
            """)

        loader = ConfigLoader(config_dir)
        with pytest.raises(ConfigValidationError, match="Invalid YAML"):
            loader.load_agents(path=config_dir / "bad.yaml")

    def test_missing_required_fields(self, tmp_path):
        """Test handling of missing required fields"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Missing required fields
        agents_data = {
            "incomplete": {
                "role": "Test Role"
                # Missing goal and backstory
            }
        }

        with open(config_dir / "incomplete.yaml", 'w') as f:
            yaml.dump(agents_data, f)

        loader = ConfigLoader(config_dir)
        with pytest.raises(Exception):  # Pydantic validation error
            loader.load_agents(path=config_dir / "incomplete.yaml")

    def test_empty_configuration(self, tmp_path):
        """Test handling of empty configuration files"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Empty file
        open(config_dir / "empty.yaml", 'w').close()

        loader = ConfigLoader(config_dir)
        with pytest.raises(ConfigValidationError, match="Empty"):
            loader.load_agents(path=config_dir / "empty.yaml")

    def test_deeply_nested_dependencies(self, tmp_path):
        """Test handling of deeply nested task dependencies"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Create agents
        agents_data = {"agent1": {"role": "R", "goal": "G", "backstory": "B"}}
        with open(config_dir / "agents.yaml", 'w') as f:
            yaml.dump(agents_data, f)

        # Create deeply nested dependency chain (50 levels)
        tasks_data = {}
        for i in range(50):
            task = {
                "name": f"Task {i}",
                "description": f"Description {i}",
                "expected_output": f"Output {i}",
                "agent": "agent1"
            }
            if i > 0:
                task["depends_on"] = [f"task_{i-1}"]
            tasks_data[f"task_{i}"] = task

        with open(config_dir / "tasks.yaml", 'w') as f:
            yaml.dump(tasks_data, f)

        loader = ConfigLoader(config_dir)
        tasks = loader.load_tasks(validate_agents=False)

        assert len(tasks) == 50

        # Create graph and verify execution order
        graph = TaskGraph(name="test", description="test", tasks=tasks)
        levels = graph.get_execution_order()

        # Should have 50 levels (each task depends on previous)
        assert len(levels) == 50
        for i, level in enumerate(levels):
            assert level == [f"task_{i}"]

    def test_concurrent_dependency_branches(self, tmp_path):
        """Test handling of concurrent dependency branches"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "schemas").mkdir()

        # Create agents
        agents_data = {"agent1": {"role": "R", "goal": "G", "backstory": "B"}}
        with open(config_dir / "agents.yaml", 'w') as f:
            yaml.dump(agents_data, f)

        # Create diamond dependency pattern
        #       task1
        #      /     \
        #   task2   task3
        #      \     /
        #       task4
        tasks_data = {
            "task1": {
                "name": "Task 1",
                "description": "Root",
                "expected_output": "Output",
                "agent": "agent1"
            },
            "task2": {
                "name": "Task 2",
                "description": "Branch A",
                "expected_output": "Output",
                "agent": "agent1",
                "depends_on": ["task1"]
            },
            "task3": {
                "name": "Task 3",
                "description": "Branch B",
                "expected_output": "Output",
                "agent": "agent1",
                "depends_on": ["task1"]
            },
            "task4": {
                "name": "Task 4",
                "description": "Merge",
                "expected_output": "Output",
                "agent": "agent1",
                "depends_on": ["task2", "task3"]
            }
        }

        with open(config_dir / "tasks.yaml", 'w') as f:
            yaml.dump(tasks_data, f)

        loader = ConfigLoader(config_dir)
        tasks = loader.load_tasks(validate_agents=False)

        graph = TaskGraph(name="test", description="test", tasks=tasks)
        levels = graph.get_execution_order()

        assert len(levels) == 3
        assert levels[0] == ["task1"]
        assert set(levels[1]) == {"task2", "task3"}
        assert levels[2] == ["task4"]
