"""
Configuration Loader

Main configuration loader for YAML-based agent and task definitions.
Supports schema validation, variable substitution, and cross-validation.
"""

import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from collections import defaultdict

try:
    from jsonschema import validate, ValidationError as JSONSchemaError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    JSONSchemaError = Exception

from agent.models.agent_config import AgentConfig, AgentTeam
from agent.models.task_config import TaskConfig, TaskGraph


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigLoader:
    """Load and validate YAML configurations

    This class provides methods to load agent and task configurations
    from YAML files, with support for:
    - JSON schema validation
    - Variable substitution
    - Cross-validation between agents and tasks
    - Dependency validation

    Attributes:
        config_dir: Base directory for configuration files
        schema_dir: Directory containing JSON schemas
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration loader

        Args:
            config_dir: Base directory for configurations (default: agent/config)
        """
        self.config_dir = config_dir or Path("agent/config")
        self.schema_dir = self.config_dir / "schemas"

        # Cache for loaded configurations
        self._agents_cache: Optional[List[AgentConfig]] = None
        self._tasks_cache: Optional[List[TaskConfig]] = None

    def load_agents(
        self,
        path: Optional[Union[str, Path]] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> List[AgentConfig]:
        """Load agents from YAML file

        Args:
            path: Path to agents.yaml (default: config/agents.yaml)
            variables: Variables for substitution

        Returns:
            List of AgentConfig objects

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if path is None:
            path = self.config_dir / "agents.yaml"
        else:
            path = Path(path)

        if not path.exists():
            raise ConfigValidationError(f"Agents file not found: {path}")

        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML in {path}: {e}")

        # Handle empty file
        if data is None:
            raise ConfigValidationError(f"Empty agents file: {path}")

        # Validate against schema if available
        if self.schema_dir.exists() and HAS_JSONSCHEMA:
            self._validate_against_schema(data, "agent_schema.json")

        # Parse agents
        agents = []
        variables = variables or {}

        if isinstance(data, dict):
            # Handle both single team and multiple teams
            if 'agents' in data:
                # Single team format
                for agent_data in data['agents']:
                    agent = AgentConfig(**agent_data)
                    if variables:
                        agent = agent.substitute_variables(variables)
                    agents.append(agent)
            else:
                # Multiple agents as top-level keys
                for name, agent_data in data.items():
                    if agent_data is None:
                        agent_data = {}
                    agent_data['name'] = name
                    agent = AgentConfig(**agent_data)
                    if variables:
                        agent = agent.substitute_variables(variables)
                    agents.append(agent)
        elif isinstance(data, list):
            # Direct list of agents
            for agent_data in data:
                agent = AgentConfig(**agent_data)
                if variables:
                    agent = agent.substitute_variables(variables)
                agents.append(agent)
        else:
            raise ConfigValidationError("Invalid agents format")

        # Validate no duplicates
        self._validate_unique_names(agents, "agent")

        self._agents_cache = agents
        return agents

    def load_tasks(
        self,
        path: Optional[Union[str, Path]] = None,
        variables: Optional[Dict[str, str]] = None,
        validate_agents: bool = True
    ) -> List[TaskConfig]:
        """Load tasks from YAML file

        Args:
            path: Path to tasks.yaml (default: config/tasks.yaml)
            variables: Variables for substitution
            validate_agents: Validate agent assignments

        Returns:
            List of TaskConfig objects

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        if path is None:
            path = self.config_dir / "tasks.yaml"
        else:
            path = Path(path)

        if not path.exists():
            raise ConfigValidationError(f"Tasks file not found: {path}")

        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML in {path}: {e}")

        # Handle empty file
        if data is None:
            raise ConfigValidationError(f"Empty tasks file: {path}")

        # Validate against schema if available
        if self.schema_dir.exists() and HAS_JSONSCHEMA:
            self._validate_against_schema(data, "task_schema.json")

        # Parse tasks
        tasks = []
        variables = variables or {}

        if isinstance(data, dict):
            if 'tasks' in data:
                # TaskGraph format
                for task_data in data['tasks']:
                    task = TaskConfig(**task_data)
                    if variables:
                        task = task.substitute_variables(variables)
                    tasks.append(task)
            else:
                # Tasks as top-level keys
                for task_id, task_data in data.items():
                    if task_data is None:
                        task_data = {}
                    task_data['id'] = task_id
                    task = TaskConfig(**task_data)
                    if variables:
                        task = task.substitute_variables(variables)
                    tasks.append(task)
        elif isinstance(data, list):
            # Direct list of tasks
            for i, task_data in enumerate(data):
                if 'id' not in task_data:
                    task_data['id'] = f"task_{i+1}"
                task = TaskConfig(**task_data)
                if variables:
                    task = task.substitute_variables(variables)
                tasks.append(task)
        else:
            raise ConfigValidationError("Invalid tasks format")

        # Validate
        self._validate_unique_ids(tasks, "task")
        self._validate_task_dependencies(tasks)

        if validate_agents:
            self._validate_task_agents(tasks)

        self._tasks_cache = tasks
        return tasks

    def load_team(
        self,
        agents_path: Optional[Union[str, Path]] = None,
        tasks_path: Optional[Union[str, Path]] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> Tuple[AgentTeam, TaskGraph]:
        """Load complete team configuration

        Args:
            agents_path: Path to agents.yaml
            tasks_path: Path to tasks.yaml
            variables: Variables for substitution

        Returns:
            Tuple of (AgentTeam, TaskGraph)
        """
        agents = self.load_agents(agents_path, variables)
        tasks = self.load_tasks(tasks_path, variables, validate_agents=True)

        # Create team
        team = AgentTeam(
            name="default_team",
            description="Loaded from configuration",
            agents=agents
        )

        # Create task graph
        graph = TaskGraph(
            name="default_graph",
            description="Loaded from configuration",
            tasks=tasks
        )

        return team, graph

    def validate_config(self) -> bool:
        """Validate complete configuration

        Returns:
            True if valid, raises ConfigValidationError otherwise
        """
        try:
            # Load and validate agents
            agents = self.load_agents()

            # Load and validate tasks
            tasks = self.load_tasks(validate_agents=True)

            # Cross-validate
            agent_names = {agent.name for agent in agents}
            for task in tasks:
                if task.agent not in agent_names:
                    raise ConfigValidationError(
                        f"Task '{task.id}' assigned to unknown agent '{task.agent}'"
                    )

                for backup in task.backup_agents:
                    if backup not in agent_names:
                        raise ConfigValidationError(
                            f"Task '{task.id}' has unknown backup agent '{backup}'"
                        )

            return True

        except ConfigValidationError:
            raise
        except Exception as e:
            raise ConfigValidationError(f"Configuration validation failed: {e}")

    def reload(self) -> None:
        """Clear cache and force reload on next access"""
        self._agents_cache = None
        self._tasks_cache = None

    def get_cached_agents(self) -> Optional[List[AgentConfig]]:
        """Get cached agents if available"""
        return self._agents_cache

    def get_cached_tasks(self) -> Optional[List[TaskConfig]]:
        """Get cached tasks if available"""
        return self._tasks_cache

    def _validate_against_schema(self, data: Any, schema_file: str) -> None:
        """Validate data against JSON schema

        Args:
            data: Data to validate
            schema_file: Schema filename

        Raises:
            ConfigValidationError: If validation fails
        """
        if not HAS_JSONSCHEMA:
            return

        schema_path = self.schema_dir / schema_file
        if not schema_path.exists():
            return  # Skip if schema not available

        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            validate(data, schema)
        except JSONSchemaError as e:
            raise ConfigValidationError(f"Schema validation failed: {e.message}")
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON schema {schema_file}: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Schema validation error: {e}")

    def _validate_unique_names(self, items: List[AgentConfig], item_type: str) -> None:
        """Validate unique agent names

        Args:
            items: List of agents
            item_type: Type name for error messages

        Raises:
            ConfigValidationError: If duplicates found
        """
        names = [item.name for item in items]
        if len(names) != len(set(names)):
            duplicates = list(set(n for n in names if names.count(n) > 1))
            raise ConfigValidationError(f"Duplicate {item_type} names: {duplicates}")

    def _validate_unique_ids(self, items: List[TaskConfig], item_type: str) -> None:
        """Validate unique task IDs

        Args:
            items: List of tasks
            item_type: Type name for error messages

        Raises:
            ConfigValidationError: If duplicates found
        """
        ids = [item.id for item in items]
        if len(ids) != len(set(ids)):
            duplicates = list(set(i for i in ids if ids.count(i) > 1))
            raise ConfigValidationError(f"Duplicate {item_type} IDs: {duplicates}")

    def _validate_task_dependencies(self, tasks: List[TaskConfig]) -> None:
        """Validate task dependencies

        Args:
            tasks: List of tasks to validate

        Raises:
            ConfigValidationError: If invalid dependencies found
        """
        task_ids = {task.id for task in tasks}

        for task in tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    raise ConfigValidationError(
                        f"Task '{task.id}' depends on unknown task '{dep}'"
                    )

            for blocked in task.blocks:
                if blocked not in task_ids:
                    raise ConfigValidationError(
                        f"Task '{task.id}' blocks unknown task '{blocked}'"
                    )

        # Check for circular dependencies
        self._check_circular_dependencies(tasks)

    def _validate_task_agents(self, tasks: List[TaskConfig]) -> None:
        """Validate task agent assignments

        Args:
            tasks: List of tasks to validate

        Raises:
            ConfigValidationError: If unknown agent assigned
        """
        if not self._agents_cache:
            try:
                self._agents_cache = self.load_agents()
            except ConfigValidationError:
                # Can't validate agents if agents file doesn't exist
                return

        agent_names = {agent.name for agent in self._agents_cache}

        for task in tasks:
            if task.agent not in agent_names:
                raise ConfigValidationError(
                    f"Task '{task.id}' assigned to unknown agent '{task.agent}'"
                )

    def _check_circular_dependencies(self, tasks: List[TaskConfig]) -> None:
        """Check for circular dependencies using DFS

        Args:
            tasks: List of tasks to check

        Raises:
            ConfigValidationError: If circular dependency detected
        """
        # Build adjacency list
        graph = defaultdict(list)
        for task in tasks:
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

        for task in tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    raise ConfigValidationError(
                        f"Circular dependency detected involving task '{task.id}'"
                    )


# Convenience functions
def load_agents(
    path: Optional[Union[str, Path]] = None,
    variables: Optional[Dict[str, str]] = None
) -> List[AgentConfig]:
    """Load agents from YAML file

    Args:
        path: Path to agents.yaml
        variables: Variables for substitution

    Returns:
        List of AgentConfig objects
    """
    loader = ConfigLoader()
    return loader.load_agents(path, variables)


def load_tasks(
    path: Optional[Union[str, Path]] = None,
    variables: Optional[Dict[str, str]] = None
) -> List[TaskConfig]:
    """Load tasks from YAML file

    Args:
        path: Path to tasks.yaml
        variables: Variables for substitution

    Returns:
        List of TaskConfig objects
    """
    loader = ConfigLoader()
    return loader.load_tasks(path, variables)


def validate_config(config_dir: Optional[Path] = None) -> bool:
    """Validate complete configuration

    Args:
        config_dir: Configuration directory

    Returns:
        True if valid
    """
    loader = ConfigLoader(config_dir)
    return loader.validate_config()


def load_team(
    agents_path: Optional[Union[str, Path]] = None,
    tasks_path: Optional[Union[str, Path]] = None,
    variables: Optional[Dict[str, str]] = None
) -> Tuple[AgentTeam, TaskGraph]:
    """Load complete team configuration

    Args:
        agents_path: Path to agents.yaml
        tasks_path: Path to tasks.yaml
        variables: Variables for substitution

    Returns:
        Tuple of (AgentTeam, TaskGraph)
    """
    loader = ConfigLoader()
    return loader.load_team(agents_path, tasks_path, variables)
