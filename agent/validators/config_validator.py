"""
Configuration Validator

Comprehensive validation logic for JARVIS agent and task configurations.
Provides detailed error messages and validation reports.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from enum import Enum
import yaml
import json
import re

try:
    from jsonschema import validate, Draft7Validator
    from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    JSONSchemaValidationError = Exception


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Represents a validation error or warning

    Attributes:
        message: Error message
        severity: Error severity
        path: Location in config (e.g., "agents.researcher.tools")
        suggestion: Suggested fix
    """
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    path: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        parts = [f"[{self.severity.value.upper()}]"]
        if self.path:
            parts.append(f"at '{self.path}':")
        parts.append(self.message)
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
        return " ".join(parts)


@dataclass
class ValidationResult:
    """Result of configuration validation

    Attributes:
        is_valid: Whether configuration is valid
        errors: List of errors found
        warnings: List of warnings found
        info: List of informational messages
        stats: Validation statistics
    """
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    info: List[ValidationError] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str, path: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        """Add an error to the result"""
        self.errors.append(ValidationError(
            message=message,
            severity=ValidationSeverity.ERROR,
            path=path,
            suggestion=suggestion
        ))
        self.is_valid = False

    def add_warning(self, message: str, path: Optional[str] = None, suggestion: Optional[str] = None) -> None:
        """Add a warning to the result"""
        self.warnings.append(ValidationError(
            message=message,
            severity=ValidationSeverity.WARNING,
            path=path,
            suggestion=suggestion
        ))

    def add_info(self, message: str, path: Optional[str] = None) -> None:
        """Add an informational message"""
        self.info.append(ValidationError(
            message=message,
            severity=ValidationSeverity.INFO,
            path=path
        ))

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)
        self.stats.update(other.stats)
        if not other.is_valid:
            self.is_valid = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': [str(e) for e in self.errors],
            'warnings': [str(w) for w in self.warnings],
            'info': [str(i) for i in self.info],
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'stats': self.stats
        }

    def __str__(self) -> str:
        lines = [f"Validation {'PASSED' if self.is_valid else 'FAILED'}"]
        lines.append(f"  Errors: {len(self.errors)}, Warnings: {len(self.warnings)}")

        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  - {err}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warn in self.warnings:
                lines.append(f"  - {warn}")

        return "\n".join(lines)


class ConfigValidator:
    """Comprehensive configuration validator

    Validates agent and task configurations with:
    - Schema validation
    - Semantic validation
    - Cross-reference validation
    - Best practice checks

    Attributes:
        config_dir: Base directory for configurations
        schema_dir: Directory containing JSON schemas
    """

    VALID_TOOLS = {
        'web_search', 'file_read', 'file_write', 'code_execute',
        'database_query', 'api_call', 'git_operations', 'image_generation'
    }

    VALID_LLM_MODELS = {
        'gpt-4o', 'gpt-4o-mini', 'claude-3-5-sonnet',
        'deepseek-chat', 'llama-3.1:70b'
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize validator

        Args:
            config_dir: Base directory for configurations
        """
        self.config_dir = config_dir or Path("agent/config")
        self.schema_dir = self.config_dir / "schemas"

    def validate_agents(self, path: Optional[Path] = None) -> ValidationResult:
        """Validate agents configuration

        Args:
            path: Path to agents.yaml

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        path = path or self.config_dir / "agents.yaml"

        # Check file exists
        if not path.exists():
            result.add_error(f"Agents file not found: {path}")
            return result

        # Load YAML
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            result.add_error(f"Invalid YAML syntax: {e}", path=str(path))
            return result

        if data is None:
            result.add_error("Empty agents file", path=str(path))
            return result

        # Schema validation
        if HAS_JSONSCHEMA and self.schema_dir.exists():
            schema_result = self._validate_schema(data, "agent_schema.json")
            result.merge(schema_result)

        # Semantic validation
        agents = self._extract_agents(data)
        result.stats['agent_count'] = len(agents)

        seen_names: Set[str] = set()
        for agent_name, agent_data in agents.items():
            agent_result = self._validate_agent(agent_name, agent_data)
            result.merge(agent_result)

            # Check for duplicates
            name_lower = agent_name.lower()
            if name_lower in seen_names:
                result.add_error(f"Duplicate agent name: {agent_name}", path=f"agents.{agent_name}")
            seen_names.add(name_lower)

        return result

    def validate_tasks(
        self,
        path: Optional[Path] = None,
        agents: Optional[Set[str]] = None
    ) -> ValidationResult:
        """Validate tasks configuration

        Args:
            path: Path to tasks.yaml
            agents: Set of valid agent names (for cross-validation)

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        path = path or self.config_dir / "tasks.yaml"

        # Check file exists
        if not path.exists():
            result.add_error(f"Tasks file not found: {path}")
            return result

        # Load YAML
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            result.add_error(f"Invalid YAML syntax: {e}", path=str(path))
            return result

        if data is None:
            result.add_error("Empty tasks file", path=str(path))
            return result

        # Schema validation
        if HAS_JSONSCHEMA and self.schema_dir.exists():
            schema_result = self._validate_schema(data, "task_schema.json")
            result.merge(schema_result)

        # Semantic validation
        tasks = self._extract_tasks(data)
        result.stats['task_count'] = len(tasks)

        task_ids: Set[str] = set()
        for task_id, task_data in tasks.items():
            task_result = self._validate_task(task_id, task_data, agents)
            result.merge(task_result)
            task_ids.add(task_id)

        # Validate dependencies
        dep_result = self._validate_dependencies(tasks, task_ids)
        result.merge(dep_result)

        return result

    def validate_full(self) -> ValidationResult:
        """Validate complete configuration

        Returns:
            ValidationResult with all errors and warnings
        """
        result = ValidationResult()

        # Validate agents first
        agents_result = self.validate_agents()
        result.merge(agents_result)

        # Get agent names for cross-validation
        agent_names: Set[str] = set()
        if agents_result.is_valid or agents_result.stats.get('agent_count', 0) > 0:
            try:
                with open(self.config_dir / "agents.yaml", 'r') as f:
                    data = yaml.safe_load(f)
                agents = self._extract_agents(data or {})
                agent_names = set(name.lower() for name in agents.keys())
            except Exception:
                pass

        # Validate tasks with agent cross-validation
        tasks_result = self.validate_tasks(agents=agent_names)
        result.merge(tasks_result)

        return result

    def _validate_schema(self, data: Any, schema_file: str) -> ValidationResult:
        """Validate data against JSON schema"""
        result = ValidationResult()
        schema_path = self.schema_dir / schema_file

        if not schema_path.exists():
            result.add_info(f"Schema file not found, skipping schema validation: {schema_file}")
            return result

        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)

            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(data))

            for error in errors:
                path = ".".join(str(p) for p in error.absolute_path)
                result.add_error(
                    error.message,
                    path=path or "root",
                    suggestion=f"Check schema at {schema_file}"
                )

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON schema: {e}", path=schema_file)
        except Exception as e:
            result.add_warning(f"Schema validation failed: {e}")

        return result

    def _extract_agents(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract agents from various formats"""
        agents = {}

        if isinstance(data, dict):
            if 'agents' in data:
                # List format under 'agents' key
                for agent in data['agents']:
                    if isinstance(agent, dict) and 'name' in agent:
                        agents[agent['name']] = agent
            else:
                # Top-level keys are agent names
                for name, agent_data in data.items():
                    if isinstance(agent_data, dict):
                        agents[name] = agent_data

        elif isinstance(data, list):
            for agent in data:
                if isinstance(agent, dict) and 'name' in agent:
                    agents[agent['name']] = agent

        return agents

    def _extract_tasks(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract tasks from various formats"""
        tasks = {}

        if isinstance(data, dict):
            if 'tasks' in data:
                # List format under 'tasks' key
                for task in data['tasks']:
                    if isinstance(task, dict) and 'id' in task:
                        tasks[task['id']] = task
            else:
                # Top-level keys are task IDs
                for task_id, task_data in data.items():
                    if isinstance(task_data, dict):
                        tasks[task_id] = task_data

        elif isinstance(data, list):
            for i, task in enumerate(data):
                if isinstance(task, dict):
                    task_id = task.get('id', f'task_{i+1}')
                    tasks[task_id] = task

        return tasks

    def _validate_agent(self, name: str, data: Dict[str, Any]) -> ValidationResult:
        """Validate a single agent"""
        result = ValidationResult()
        path_prefix = f"agents.{name}"

        # Required fields
        for field in ['role', 'goal', 'backstory']:
            if field not in data or not data.get(field):
                result.add_error(
                    f"Missing required field: {field}",
                    path=f"{path_prefix}.{field}"
                )

        # Validate LLM model
        llm = data.get('llm')
        if llm and llm not in self.VALID_LLM_MODELS:
            result.add_error(
                f"Invalid LLM model: {llm}",
                path=f"{path_prefix}.llm",
                suggestion=f"Valid models: {', '.join(self.VALID_LLM_MODELS)}"
            )

        # Validate temperature
        temp = data.get('temperature')
        if temp is not None:
            if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                result.add_error(
                    f"Temperature must be between 0 and 2, got: {temp}",
                    path=f"{path_prefix}.temperature"
                )

        # Validate tools
        tools = data.get('tools', [])
        for tool in tools:
            if tool not in self.VALID_TOOLS:
                result.add_error(
                    f"Unknown tool: {tool}",
                    path=f"{path_prefix}.tools",
                    suggestion=f"Valid tools: {', '.join(self.VALID_TOOLS)}"
                )

        # Validate max_iterations
        max_iter = data.get('max_iterations')
        if max_iter is not None:
            if not isinstance(max_iter, int) or max_iter < 1 or max_iter > 100:
                result.add_error(
                    f"max_iterations must be between 1 and 100, got: {max_iter}",
                    path=f"{path_prefix}.max_iterations"
                )

        # Check for unsubstituted variables (warning)
        for field in ['role', 'goal', 'backstory']:
            value = data.get(field, '')
            if value:
                unsubstituted = re.findall(r'\{([^}]+)\}', str(value))
                if unsubstituted:
                    result.add_info(
                        f"Contains variables that need substitution: {unsubstituted}",
                        path=f"{path_prefix}.{field}"
                    )

        return result

    def _validate_task(
        self,
        task_id: str,
        data: Dict[str, Any],
        agents: Optional[Set[str]] = None
    ) -> ValidationResult:
        """Validate a single task"""
        result = ValidationResult()
        path_prefix = f"tasks.{task_id}"

        # Required fields
        for field in ['name', 'description', 'expected_output', 'agent']:
            if field not in data or not data.get(field):
                result.add_error(
                    f"Missing required field: {field}",
                    path=f"{path_prefix}.{field}"
                )

        # Validate agent assignment
        agent = data.get('agent')
        if agent and agents:
            if agent.lower() not in agents:
                result.add_error(
                    f"Unknown agent: {agent}",
                    path=f"{path_prefix}.agent",
                    suggestion=f"Valid agents: {', '.join(agents)}"
                )

        # Validate backup agents
        for backup in data.get('backup_agents', []):
            if agents and backup.lower() not in agents:
                result.add_error(
                    f"Unknown backup agent: {backup}",
                    path=f"{path_prefix}.backup_agents"
                )

        # Validate priority
        priority = data.get('priority')
        if priority and priority not in ['critical', 'high', 'medium', 'low']:
            result.add_error(
                f"Invalid priority: {priority}",
                path=f"{path_prefix}.priority",
                suggestion="Valid: critical, high, medium, low"
            )

        # Validate output_format
        output_format = data.get('output_format')
        if output_format and output_format not in ['text', 'json', 'markdown', 'html', 'file']:
            result.add_error(
                f"Invalid output_format: {output_format}",
                path=f"{path_prefix}.output_format"
            )

        # Validate timeout
        timeout = data.get('timeout_seconds')
        if timeout is not None:
            if not isinstance(timeout, int) or timeout < 1 or timeout > 3600:
                result.add_error(
                    f"timeout_seconds must be between 1 and 3600, got: {timeout}",
                    path=f"{path_prefix}.timeout_seconds"
                )

        # Self-reference check
        depends_on = data.get('depends_on', [])
        if task_id in depends_on:
            result.add_error(
                "Task cannot depend on itself",
                path=f"{path_prefix}.depends_on"
            )

        blocks = data.get('blocks', [])
        if task_id in blocks:
            result.add_error(
                "Task cannot block itself",
                path=f"{path_prefix}.blocks"
            )

        return result

    def _validate_dependencies(
        self,
        tasks: Dict[str, Dict[str, Any]],
        task_ids: Set[str]
    ) -> ValidationResult:
        """Validate task dependencies"""
        result = ValidationResult()

        # Check all dependencies exist
        for task_id, task_data in tasks.items():
            for dep in task_data.get('depends_on', []):
                if dep not in task_ids:
                    result.add_error(
                        f"Unknown dependency: {dep}",
                        path=f"tasks.{task_id}.depends_on"
                    )

            for blocked in task_data.get('blocks', []):
                if blocked not in task_ids:
                    result.add_error(
                        f"Unknown blocked task: {blocked}",
                        path=f"tasks.{task_id}.blocks"
                    )

        # Check for circular dependencies
        circular = self._detect_circular_dependencies(tasks)
        if circular:
            result.add_error(
                f"Circular dependency detected: {' -> '.join(circular)}",
                path="tasks"
            )

        return result

    def _detect_circular_dependencies(self, tasks: Dict[str, Dict[str, Any]]) -> Optional[List[str]]:
        """Detect circular dependencies using DFS"""
        from collections import defaultdict

        graph = defaultdict(list)
        for task_id, task_data in tasks.items():
            for dep in task_data.get('depends_on', []):
                graph[dep].append(task_id)

        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    path.append(neighbor)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for task_id in tasks:
            if task_id not in visited:
                if dfs(task_id):
                    # Find the cycle in path
                    cycle_start = path[-1]
                    cycle_idx = path.index(cycle_start)
                    return path[cycle_idx:]

        return None


# Convenience functions
def validate_agents_config(path: Optional[Path] = None) -> ValidationResult:
    """Validate agents configuration file"""
    validator = ConfigValidator()
    return validator.validate_agents(path)


def validate_tasks_config(
    path: Optional[Path] = None,
    agents: Optional[Set[str]] = None
) -> ValidationResult:
    """Validate tasks configuration file"""
    validator = ConfigValidator()
    return validator.validate_tasks(path, agents)


def validate_full_config(config_dir: Optional[Path] = None) -> ValidationResult:
    """Validate complete configuration"""
    validator = ConfigValidator(config_dir)
    return validator.validate_full()
