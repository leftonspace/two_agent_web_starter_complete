"""
Task Configuration Models

Pydantic models for task configuration in the JARVIS system.
Supports YAML-based declarative task definitions with dependencies.
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
from collections import defaultdict, deque
import re


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(str, Enum):
    """Supported output formats"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    FILE = "file"


class TaskConfig(BaseModel):
    """Configuration for a single task

    Attributes:
        id: Unique task identifier
        name: Task name
        description: What needs to be done
        expected_output: Expected result description
        agent: Assigned agent name
        backup_agents: Fallback agents
        priority: Task priority level
        status: Current execution status
        max_retries: Maximum retry attempts
        timeout_seconds: Execution timeout
        output_format: Output format type
        output_file: Save output to file
        output_validation: Output validation rules
        depends_on: Task IDs this depends on
        blocks: Task IDs this blocks
        context: Additional context
        variables: Variable substitutions
        created_at: Creation timestamp
        updated_at: Last update timestamp
        success_criteria: Success conditions
        quality_threshold: Quality threshold (0.0 to 1.0)
    """

    # Core fields
    id: str = Field(..., description="Unique task identifier")
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="What needs to be done")
    expected_output: str = Field(..., description="Expected result description")

    # Assignment
    agent: str = Field(..., description="Assigned agent name")
    backup_agents: List[str] = Field(default_factory=list, description="Fallback agents")

    # Configuration
    priority: TaskPriority = Field(TaskPriority.MEDIUM)
    status: TaskStatus = Field(TaskStatus.PENDING)
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, ge=1, le=3600)

    # Output
    output_format: OutputFormat = Field(OutputFormat.TEXT)
    output_file: Optional[str] = Field(None, description="Save output to file")
    output_validation: Optional[Dict[str, Any]] = Field(None, description="Output validation rules")

    # Dependencies
    depends_on: List[str] = Field(default_factory=list, description="Task IDs this depends on")
    blocks: List[str] = Field(default_factory=list, description="Task IDs this blocks")

    # Context
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    variables: Dict[str, str] = Field(default_factory=dict, description="Variable substitutions")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Quality gates
    success_criteria: List[str] = Field(default_factory=list, description="Success conditions")
    quality_threshold: float = Field(0.8, ge=0.0, le=1.0)

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True
        extra = "allow"

    @validator('id', 'name')
    def validate_identifiers(cls, v):
        """Validate ID and name are not empty"""
        if not v or not v.strip():
            raise ValueError("ID and name cannot be empty")
        return v.strip()

    @validator('description', 'expected_output')
    def validate_not_empty(cls, v, field):
        """Validate text fields are not empty"""
        if not v or not v.strip():
            raise ValueError(f"{field.name} cannot be empty")
        return v.strip()

    @validator('depends_on', 'blocks')
    def validate_no_self_reference(cls, v, values):
        """Validate task doesn't reference itself"""
        if 'id' in values and values['id'] in v:
            raise ValueError("Task cannot depend on or block itself")
        return v

    @root_validator
    def validate_circular_dependency(cls, values):
        """Check for direct circular dependency"""
        depends_on = values.get('depends_on', [])
        blocks = values.get('blocks', [])

        # Check for direct circular dependency
        overlap = set(depends_on) & set(blocks)
        if overlap:
            raise ValueError(f"Circular dependency detected: {overlap}")

        return values

    def substitute_variables(self, variables: Dict[str, str]) -> 'TaskConfig':
        """Replace {variable} placeholders

        Args:
            variables: Dictionary of variable names to values

        Returns:
            New TaskConfig with substituted values
        """
        def substitute(text: str) -> str:
            if not text:
                return text
            for key, value in variables.items():
                text = text.replace(f"{{{key}}}", value)
            return text

        config_dict = self.dict()
        config_dict['description'] = substitute(self.description)
        config_dict['expected_output'] = substitute(self.expected_output)

        # Merge variables
        config_dict['variables'] = {**self.variables, **variables}

        return TaskConfig(**config_dict)

    def is_ready(self, completed_tasks: List[str]) -> bool:
        """Check if task is ready to execute

        Args:
            completed_tasks: List of completed task IDs

        Returns:
            True if all dependencies are satisfied
        """
        return all(dep in completed_tasks for dep in self.depends_on)

    def mark_in_progress(self) -> 'TaskConfig':
        """Mark task as in progress"""
        config_dict = self.dict()
        config_dict['status'] = TaskStatus.IN_PROGRESS
        config_dict['updated_at'] = datetime.now()
        return TaskConfig(**config_dict)

    def mark_completed(self) -> 'TaskConfig':
        """Mark task as completed"""
        config_dict = self.dict()
        config_dict['status'] = TaskStatus.COMPLETED
        config_dict['updated_at'] = datetime.now()
        return TaskConfig(**config_dict)

    def mark_failed(self) -> 'TaskConfig':
        """Mark task as failed"""
        config_dict = self.dict()
        config_dict['status'] = TaskStatus.FAILED
        config_dict['updated_at'] = datetime.now()
        return TaskConfig(**config_dict)

    def to_crew_task_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs suitable for CrewAI Task

        Returns:
            Dictionary of kwargs for CrewAI Task constructor
        """
        return {
            'description': self.description,
            'expected_output': self.expected_output,
        }


class TaskGraph(BaseModel):
    """Collection of tasks with dependency management

    Attributes:
        name: Task graph name
        description: Overall objective
        tasks: All tasks in the graph
        allow_parallel: Allow parallel execution
        max_parallel_tasks: Maximum concurrent tasks
        stop_on_failure: Stop all tasks if one fails
    """

    name: str = Field(..., description="Task graph name")
    description: str = Field(..., description="Overall objective")
    tasks: List[TaskConfig] = Field(..., description="All tasks")

    # Execution settings
    allow_parallel: bool = Field(True, description="Allow parallel execution")
    max_parallel_tasks: int = Field(5, ge=1, le=20)
    stop_on_failure: bool = Field(False, description="Stop all tasks if one fails")

    class Config:
        """Pydantic model configuration"""
        extra = "allow"

    @validator('name')
    def validate_name(cls, v):
        """Validate graph name"""
        if not v or not v.strip():
            raise ValueError("Task graph name cannot be empty")
        return v.strip()

    @validator('tasks')
    def validate_tasks(cls, v):
        """Validate tasks list is not empty"""
        if not v:
            raise ValueError("Task graph must have at least one task")
        return v

    def get_task(self, task_id: str) -> Optional[TaskConfig]:
        """Get task by ID

        Args:
            task_id: Task ID to find

        Returns:
            TaskConfig if found, None otherwise
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_ready_tasks(self, completed_tasks: List[str]) -> List[TaskConfig]:
        """Get tasks ready for execution

        Args:
            completed_tasks: List of completed task IDs

        Returns:
            List of tasks ready to execute
        """
        ready = []
        for task in self.tasks:
            if task.status == TaskStatus.PENDING and task.is_ready(completed_tasks):
                ready.append(task)
        return ready

    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskConfig]:
        """Get tasks by status

        Args:
            status: Status to filter by

        Returns:
            List of tasks with the given status
        """
        return [task for task in self.tasks if task.status == status]

    def get_tasks_by_priority(self, priority: TaskPriority) -> List[TaskConfig]:
        """Get tasks by priority

        Args:
            priority: Priority to filter by

        Returns:
            List of tasks with the given priority
        """
        return [task for task in self.tasks if task.priority == priority]

    def validate_dependencies(self) -> List[str]:
        """Validate all dependencies exist

        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        task_ids = {task.id for task in self.tasks}

        for task in self.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    errors.append(f"Task {task.id} depends on unknown task {dep}")
            for blocked in task.blocks:
                if blocked not in task_ids:
                    errors.append(f"Task {task.id} blocks unknown task {blocked}")

        return errors

    def check_circular_dependencies(self) -> Optional[str]:
        """Check for circular dependencies using DFS

        Returns:
            Error message if circular dependency found, None otherwise
        """
        # Build adjacency list
        graph = defaultdict(list)
        for task in self.tasks:
            for dep in task.depends_on:
                graph[dep].append(task.id)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            for neighbor in graph[task_id]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(task_id)
            return False

        for task in self.tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    return f"Circular dependency detected involving task '{task.id}'"

        return None

    def get_execution_order(self) -> List[List[str]]:
        """Get tasks in execution order (batches for parallel execution)

        Returns:
            List of task ID batches, where each batch can run in parallel
        """
        # Build dependency graph
        in_degree = defaultdict(int)
        graph = defaultdict(list)

        for task in self.tasks:
            in_degree[task.id] = len(task.depends_on)
            for dep in task.depends_on:
                graph[dep].append(task.id)

        # Topological sort with levels
        queue = deque([task.id for task in self.tasks if not task.depends_on])
        levels = []

        while queue:
            current_level = []
            level_size = len(queue)

            for _ in range(level_size):
                task_id = queue.popleft()
                current_level.append(task_id)

                for dependent in graph[task_id]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

            levels.append(current_level)

        return levels

    def get_critical_path(self) -> List[str]:
        """Get the critical path (longest dependency chain)

        Returns:
            List of task IDs forming the critical path
        """
        # Build reverse graph for backtracking
        predecessors = defaultdict(list)
        for task in self.tasks:
            for dep in task.depends_on:
                predecessors[task.id].append(dep)

        # Calculate longest path to each task
        longest_path = {}
        path_predecessor = {}

        def get_longest_path(task_id: str) -> int:
            if task_id in longest_path:
                return longest_path[task_id]

            if not predecessors[task_id]:
                longest_path[task_id] = 1
                path_predecessor[task_id] = None
                return 1

            max_length = 0
            best_pred = None
            for pred in predecessors[task_id]:
                pred_length = get_longest_path(pred)
                if pred_length > max_length:
                    max_length = pred_length
                    best_pred = pred

            longest_path[task_id] = max_length + 1
            path_predecessor[task_id] = best_pred
            return longest_path[task_id]

        # Find task with longest path
        max_task = None
        max_length = 0
        for task in self.tasks:
            length = get_longest_path(task.id)
            if length > max_length:
                max_length = length
                max_task = task.id

        # Reconstruct path
        if max_task is None:
            return []

        path = []
        current = max_task
        while current is not None:
            path.append(current)
            current = path_predecessor.get(current)

        return list(reversed(path))

    def to_mermaid_diagram(self) -> str:
        """Generate Mermaid diagram representation

        Returns:
            Mermaid diagram string
        """
        lines = ["graph TD"]

        for task in self.tasks:
            # Node definition with styling based on priority
            style_class = task.priority.value
            lines.append(f"    {task.id}[{task.name}]:::{style_class}")

        for task in self.tasks:
            for dep in task.depends_on:
                lines.append(f"    {dep} --> {task.id}")

        # Add styling
        lines.append("")
        lines.append("    classDef critical fill:#ff6b6b,stroke:#333,stroke-width:2px")
        lines.append("    classDef high fill:#ffd93d,stroke:#333,stroke-width:2px")
        lines.append("    classDef medium fill:#6bcb77,stroke:#333,stroke-width:2px")
        lines.append("    classDef low fill:#4d96ff,stroke:#333,stroke-width:2px")

        return "\n".join(lines)
