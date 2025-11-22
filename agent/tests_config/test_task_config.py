"""
Tests for Task Configuration Models

Comprehensive tests for TaskConfig and TaskGraph models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from agent.models.task_config import (
    TaskConfig, TaskGraph, TaskPriority, TaskStatus, OutputFormat
)


class TestTaskConfig:
    """Tests for TaskConfig model"""

    def test_minimal_valid_config(self):
        """Test creating task with minimal required fields"""
        task = TaskConfig(
            id="task_1",
            name="Test Task",
            description="Test description",
            expected_output="Test output",
            agent="test_agent"
        )
        assert task.id == "task_1"
        assert task.name == "Test Task"
        assert task.description == "Test description"
        assert task.expected_output == "Test output"
        assert task.agent == "test_agent"

    def test_full_config(self):
        """Test creating task with all fields"""
        task = TaskConfig(
            id="full_task",
            name="Full Task",
            description="Full description",
            expected_output="Full output",
            agent="main_agent",
            backup_agents=["backup1", "backup2"],
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING,
            max_retries=5,
            timeout_seconds=300,
            output_format=OutputFormat.JSON,
            output_file="output.json",
            output_validation={"required_fields": ["id", "name"]},
            depends_on=["task_0"],
            blocks=["task_2"],
            context={"key": "value"},
            variables={"var1": "value1"},
            success_criteria=["Criteria 1", "Criteria 2"],
            quality_threshold=0.9
        )
        assert task.id == "full_task"
        assert task.priority == TaskPriority.HIGH
        assert task.max_retries == 5
        assert task.timeout_seconds == 300
        assert task.output_format == OutputFormat.JSON
        assert len(task.backup_agents) == 2
        assert len(task.success_criteria) == 2
        assert task.quality_threshold == 0.9

    def test_default_values(self):
        """Test default values are applied correctly"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Desc",
            expected_output="Output",
            agent="agent"
        )
        assert task.priority == TaskPriority.MEDIUM
        assert task.status == TaskStatus.PENDING
        assert task.max_retries == 3
        assert task.timeout_seconds is None
        assert task.output_format == OutputFormat.TEXT
        assert task.output_file is None
        assert task.depends_on == []
        assert task.blocks == []
        assert task.quality_threshold == 0.8

    def test_empty_id_validation(self):
        """Test that empty ID raises error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskConfig(
                id="",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent"
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_empty_name_validation(self):
        """Test that empty name raises error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskConfig(
                id="task_1",
                name="",
                description="Desc",
                expected_output="Output",
                agent="agent"
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_self_dependency_validation(self):
        """Test that self-dependency raises error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            )
        assert "cannot depend on" in str(exc_info.value).lower() or "itself" in str(exc_info.value).lower()

    def test_self_blocking_validation(self):
        """Test that self-blocking raises error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                blocks=["task_1"]
            )
        assert "cannot" in str(exc_info.value).lower() or "itself" in str(exc_info.value).lower()

    def test_direct_circular_dependency(self):
        """Test direct circular dependency detection"""
        with pytest.raises(ValidationError) as exc_info:
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_2"],
                blocks=["task_2"]
            )
        assert "Circular" in str(exc_info.value)

    def test_max_retries_range(self):
        """Test max_retries validation"""
        with pytest.raises(ValidationError):
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                max_retries=-1
            )

        with pytest.raises(ValidationError):
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                max_retries=11
            )

    def test_timeout_range(self):
        """Test timeout_seconds validation"""
        with pytest.raises(ValidationError):
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                timeout_seconds=0
            )

        with pytest.raises(ValidationError):
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                timeout_seconds=3601
            )

    def test_quality_threshold_range(self):
        """Test quality_threshold validation"""
        with pytest.raises(ValidationError):
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                quality_threshold=-0.1
            )

        with pytest.raises(ValidationError):
            TaskConfig(
                id="task_1",
                name="Test",
                description="Desc",
                expected_output="Output",
                agent="agent",
                quality_threshold=1.1
            )

    def test_variable_substitution(self):
        """Test variable substitution in text fields"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Research {topic} thoroughly",
            expected_output="Report on {topic}",
            agent="agent"
        )

        substituted = task.substitute_variables({"topic": "AI"})

        assert substituted.description == "Research AI thoroughly"
        assert substituted.expected_output == "Report on AI"

    def test_variable_substitution_merges(self):
        """Test that variable substitution merges variables"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Desc",
            expected_output="Output",
            agent="agent",
            variables={"existing": "value"}
        )

        substituted = task.substitute_variables({"new": "value2"})

        assert "existing" in substituted.variables
        assert "new" in substituted.variables

    def test_is_ready_no_dependencies(self):
        """Test is_ready with no dependencies"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Desc",
            expected_output="Output",
            agent="agent"
        )

        assert task.is_ready([]) is True
        assert task.is_ready(["other_task"]) is True

    def test_is_ready_with_dependencies(self):
        """Test is_ready with dependencies"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Desc",
            expected_output="Output",
            agent="agent",
            depends_on=["dep1", "dep2"]
        )

        assert task.is_ready([]) is False
        assert task.is_ready(["dep1"]) is False
        assert task.is_ready(["dep1", "dep2"]) is True
        assert task.is_ready(["dep1", "dep2", "dep3"]) is True

    def test_status_transitions(self):
        """Test status transition methods"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Desc",
            expected_output="Output",
            agent="agent"
        )

        assert task.status == TaskStatus.PENDING

        in_progress = task.mark_in_progress()
        assert in_progress.status == TaskStatus.IN_PROGRESS

        completed = task.mark_completed()
        assert completed.status == TaskStatus.COMPLETED

        failed = task.mark_failed()
        assert failed.status == TaskStatus.FAILED

    def test_to_crew_task_kwargs(self):
        """Test conversion to CrewAI kwargs"""
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Test Description",
            expected_output="Test Output",
            agent="agent"
        )

        kwargs = task.to_crew_task_kwargs()

        assert kwargs['description'] == "Test Description"
        assert kwargs['expected_output'] == "Test Output"

    def test_created_at_default(self):
        """Test created_at default value"""
        before = datetime.now()
        task = TaskConfig(
            id="task_1",
            name="Test",
            description="Desc",
            expected_output="Output",
            agent="agent"
        )
        after = datetime.now()

        assert before <= task.created_at <= after


class TestTaskGraph:
    """Tests for TaskGraph model"""

    def test_create_graph(self):
        """Test creating a task graph"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc 1",
                expected_output="Output 1",
                agent="agent1"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc 2",
                expected_output="Output 2",
                agent="agent2",
                depends_on=["task_1"]
            )
        ]

        graph = TaskGraph(
            name="Test Graph",
            description="A test graph",
            tasks=tasks
        )

        assert graph.name == "Test Graph"
        assert len(graph.tasks) == 2

    def test_default_values(self):
        """Test graph default values"""
        task = TaskConfig(
            id="task_1",
            name="Task",
            description="Desc",
            expected_output="Output",
            agent="agent"
        )

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=[task]
        )

        assert graph.allow_parallel is True
        assert graph.max_parallel_tasks == 5
        assert graph.stop_on_failure is False

    def test_get_task_by_id(self):
        """Test getting task by ID"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent"
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        found = graph.get_task("task_1")
        assert found is not None
        assert found.id == "task_1"

        not_found = graph.get_task("nonexistent")
        assert not_found is None

    def test_get_ready_tasks(self):
        """Test getting ready tasks"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            ),
            TaskConfig(
                id="task_3",
                name="Task 3",
                description="Desc",
                expected_output="Output",
                agent="agent"
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        # Initially, tasks without dependencies are ready
        ready = graph.get_ready_tasks([])
        assert len(ready) == 2
        ready_ids = [t.id for t in ready]
        assert "task_1" in ready_ids
        assert "task_3" in ready_ids

        # After task_1 completes, task_2 becomes ready
        ready = graph.get_ready_tasks(["task_1"])
        ready_ids = [t.id for t in ready]
        assert "task_2" in ready_ids

    def test_get_tasks_by_status(self):
        """Test filtering tasks by status"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent",
                status=TaskStatus.PENDING
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                status=TaskStatus.COMPLETED
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        pending = graph.get_tasks_by_status(TaskStatus.PENDING)
        assert len(pending) == 1
        assert pending[0].id == "task_1"

    def test_get_tasks_by_priority(self):
        """Test filtering tasks by priority"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent",
                priority=TaskPriority.HIGH
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                priority=TaskPriority.LOW
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        high_priority = graph.get_tasks_by_priority(TaskPriority.HIGH)
        assert len(high_priority) == 1
        assert high_priority[0].id == "task_1"

    def test_validate_dependencies_valid(self):
        """Test dependency validation with valid dependencies"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        errors = graph.validate_dependencies()
        assert len(errors) == 0

    def test_validate_dependencies_invalid(self):
        """Test dependency validation with invalid dependencies"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["nonexistent"]
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        errors = graph.validate_dependencies()
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_check_circular_dependencies_none(self):
        """Test circular dependency check with no cycles"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            ),
            TaskConfig(
                id="task_3",
                name="Task 3",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_2"]
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        result = graph.check_circular_dependencies()
        assert result is None

    def test_get_execution_order(self):
        """Test getting execution order"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            ),
            TaskConfig(
                id="task_3",
                name="Task 3",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_4",
                name="Task 4",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_2", "task_3"]
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        order = graph.get_execution_order()

        # First level: tasks without dependencies
        assert "task_1" in order[0]
        assert "task_3" in order[0]

        # task_2 depends on task_1
        task_2_level = None
        for i, level in enumerate(order):
            if "task_2" in level:
                task_2_level = i
                break
        assert task_2_level is not None
        assert task_2_level > order[0].index("task_1") if "task_1" in order[0] else True

        # task_4 depends on task_2 and task_3
        task_4_level = None
        for i, level in enumerate(order):
            if "task_4" in level:
                task_4_level = i
                break
        assert task_4_level is not None

    def test_get_critical_path(self):
        """Test getting critical path"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent"
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            ),
            TaskConfig(
                id="task_3",
                name="Task 3",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_2"]
            ),
            TaskConfig(
                id="task_4",
                name="Task 4",
                description="Desc",
                expected_output="Output",
                agent="agent"
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        critical_path = graph.get_critical_path()

        # Longest path is task_1 -> task_2 -> task_3
        assert len(critical_path) == 3
        assert critical_path == ["task_1", "task_2", "task_3"]

    def test_to_mermaid_diagram(self):
        """Test Mermaid diagram generation"""
        tasks = [
            TaskConfig(
                id="task_1",
                name="Task 1",
                description="Desc",
                expected_output="Output",
                agent="agent",
                priority=TaskPriority.HIGH
            ),
            TaskConfig(
                id="task_2",
                name="Task 2",
                description="Desc",
                expected_output="Output",
                agent="agent",
                depends_on=["task_1"]
            )
        ]

        graph = TaskGraph(
            name="Test",
            description="Test",
            tasks=tasks
        )

        mermaid = graph.to_mermaid_diagram()

        assert "graph TD" in mermaid
        assert "task_1" in mermaid
        assert "task_2" in mermaid
        assert "task_1 --> task_2" in mermaid

    def test_empty_graph_validation(self):
        """Test that empty graph raises error"""
        with pytest.raises(ValidationError) as exc_info:
            TaskGraph(
                name="Test",
                description="Test",
                tasks=[]
            )
        assert "at least one task" in str(exc_info.value)


class TestEnums:
    """Tests for enum types"""

    def test_task_priority_values(self):
        """Test TaskPriority enum values"""
        assert TaskPriority.CRITICAL.value == "critical"
        assert TaskPriority.HIGH.value == "high"
        assert TaskPriority.MEDIUM.value == "medium"
        assert TaskPriority.LOW.value == "low"

    def test_task_status_values(self):
        """Test TaskStatus enum values"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"

    def test_output_format_values(self):
        """Test OutputFormat enum values"""
        assert OutputFormat.TEXT.value == "text"
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.MARKDOWN.value == "markdown"
        assert OutputFormat.HTML.value == "html"
        assert OutputFormat.FILE.value == "file"
