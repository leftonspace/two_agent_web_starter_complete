"""
Role-Based Department Profiles System

This module provides a comprehensive role definition system with department-specific roles,
each having specialized knowledge, tools, and permissions.

Features:
- Role definitions with domain expertise and knowledge
- Tool and workflow access control
- Permission-based security
- System prompt generation for LLM agents
- Decision authority management
- Role selection based on task matching
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
import json
import logging

from agent.permissions import Permission

logger = logging.getLogger(__name__)


class RoleLevel(Enum):
    """Hierarchical role levels in the organization"""
    INDIVIDUAL_CONTRIBUTOR = 1
    MANAGER = 2
    DIRECTOR = 3
    VP = 4
    C_LEVEL = 5


@dataclass
class RoleProfile:
    """
    Comprehensive role definition with expertise, permissions, and behavior.

    A RoleProfile defines everything needed for an AI agent to act as a specific
    role within a department, including their knowledge, tools, permissions, and
    decision-making authority.
    """
    role_id: str
    role_name: str
    department: str
    level: RoleLevel

    # Expertise and knowledge
    expertise_areas: List[str]
    domain_knowledge: str  # Long-form description for LLM prompt

    # Access control
    allowed_tools: List[str]
    allowed_workflows: List[str]
    base_permissions: Set[Permission]

    # Behavior and prompting
    system_prompt_template: str
    decision_authority: Dict[str, Any]
    escalation_role: Optional[str] = None

    # Performance tracking
    performance_kpis: List[str] = field(default_factory=list)

    def build_system_prompt(self, task: str, context: Optional[Dict] = None) -> str:
        """
        Build agent system prompt for this role.

        Args:
            task: The task to be performed
            context: Additional context variables for prompt rendering

        Returns:
            Rendered system prompt string
        """
        from jinja2 import Template

        template = Template(self.system_prompt_template)

        # Build rendering context
        render_context = {
            "role_name": self.role_name,
            "expertise": ", ".join(self.expertise_areas),
            "domain_knowledge": self.domain_knowledge,
            "task": task,
            "escalation_role": self.escalation_role or "your supervisor"
        }

        # Add any additional context
        if context:
            render_context.update(context)

        return template.render(**render_context)

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission"""
        return permission in self.base_permissions

    def can_use_tool(self, tool_name: str) -> bool:
        """Check if role can use a specific tool"""
        return tool_name in self.allowed_tools

    def can_execute_workflow(self, workflow_name: str) -> bool:
        """Check if role can execute a specific workflow"""
        return workflow_name in self.allowed_workflows

    def check_decision_authority(self, decision_type: str, **params) -> bool:
        """
        Check if role has authority to make a specific decision.

        Args:
            decision_type: Type of decision (e.g., "approve_expense")
            **params: Decision parameters (e.g., amount=5000)

        Returns:
            True if role has authority, False otherwise
        """
        if decision_type not in self.decision_authority:
            return False

        authority = self.decision_authority[decision_type]

        # Simple boolean check
        if isinstance(authority, bool):
            return authority

        # Numeric threshold check (e.g., can_approve_offers_up_to: 100000)
        if isinstance(authority, (int, float)) and "amount" in params:
            return params["amount"] <= authority

        # List of conditions that require approval
        if isinstance(authority, list):
            # If it's a "requires_approval_for" list, return False (needs approval)
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert role profile to dictionary"""
        return {
            "role_id": self.role_id,
            "role_name": self.role_name,
            "department": self.department,
            "level": self.level.name,
            "expertise_areas": self.expertise_areas,
            "domain_knowledge": self.domain_knowledge,
            "allowed_tools": self.allowed_tools,
            "allowed_workflows": self.allowed_workflows,
            "base_permissions": [p.name for p in self.base_permissions],
            "system_prompt_template": self.system_prompt_template,
            "decision_authority": self.decision_authority,
            "escalation_role": self.escalation_role,
            "performance_kpis": self.performance_kpis
        }


class RoleRegistry:
    """
    Registry for loading and managing role definitions.

    Loads role definitions from JSON files in the role_definitions directory
    and provides methods for role lookup and task-based role selection.
    """

    def __init__(self, role_definitions_dir: Optional[Path] = None):
        """
        Initialize role registry.

        Args:
            role_definitions_dir: Directory containing role definition JSON files.
                                 Defaults to agent/role_definitions/
        """
        if role_definitions_dir is None:
            role_definitions_dir = Path(__file__).parent / "role_definitions"

        self.definitions_dir = role_definitions_dir
        self.roles: Dict[str, RoleProfile] = {}

        # Load roles if directory exists
        if self.definitions_dir.exists():
            self._load_roles(self.definitions_dir)
        else:
            logger.warning(f"Role definitions directory not found: {self.definitions_dir}")

    def _load_roles(self, definitions_dir: Path):
        """
        Load role definitions from JSON files.

        Args:
            definitions_dir: Directory containing *.json role definition files
        """
        json_files = list(definitions_dir.glob("**/*.json"))

        if not json_files:
            logger.warning(f"No JSON role definitions found in {definitions_dir}")
            return

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    roles_data = json.load(f)

                department = roles_data.get("department", "unknown")
                roles_list = roles_data.get("roles", [])

                logger.info(f"Loading {len(roles_list)} roles from {json_file.name}")

                for role_data in roles_list:
                    try:
                        role = self._parse_role(role_data)
                        self.roles[role.role_id] = role
                        logger.debug(f"Loaded role: {role.role_id} ({role.role_name})")
                    except Exception as e:
                        logger.error(f"Failed to parse role in {json_file}: {e}")

            except Exception as e:
                logger.error(f"Failed to load role definitions from {json_file}: {e}")

    def _parse_role(self, data: Dict) -> RoleProfile:
        """
        Parse JSON role definition into RoleProfile object.

        Args:
            data: Dictionary containing role definition

        Returns:
            RoleProfile instance
        """
        return RoleProfile(
            role_id=data["role_id"],
            role_name=data["role_name"],
            department=data["department"],
            level=RoleLevel[data["level"]],
            expertise_areas=data["expertise_areas"],
            domain_knowledge=data["domain_knowledge"],
            allowed_tools=data["allowed_tools"],
            allowed_workflows=data["allowed_workflows"],
            base_permissions=set(Permission[p] for p in data.get("base_permissions", [])),
            system_prompt_template=data["system_prompt_template"],
            decision_authority=data.get("decision_authority", {}),
            escalation_role=data.get("escalation_role"),
            performance_kpis=data.get("performance_kpis", [])
        )

    def get_role(self, role_id: str) -> Optional[RoleProfile]:
        """
        Get role by ID.

        Args:
            role_id: Unique role identifier

        Returns:
            RoleProfile if found, None otherwise
        """
        return self.roles.get(role_id)

    def get_roles_for_department(self, department: str) -> List[RoleProfile]:
        """
        Get all roles for a specific department.

        Args:
            department: Department name (e.g., "hr", "finance", "legal")

        Returns:
            List of RoleProfile objects for the department
        """
        return [r for r in self.roles.values() if r.department.lower() == department.lower()]

    def get_roles_by_level(self, level: RoleLevel) -> List[RoleProfile]:
        """
        Get all roles at a specific organizational level.

        Args:
            level: RoleLevel enum value

        Returns:
            List of RoleProfile objects at that level
        """
        return [r for r in self.roles.values() if r.level == level]

    def list_all_roles(self) -> List[RoleProfile]:
        """Get all loaded roles"""
        return list(self.roles.values())

    def select_role_for_task(self, task: str, department: str) -> Optional[str]:
        """
        Select best role for a task based on expertise matching.

        Uses keyword matching between task description and role expertise areas
        to find the most suitable role.

        Args:
            task: Task description
            department: Department name

        Returns:
            role_id of best matching role, or None if no roles found
        """
        roles = self.get_roles_for_department(department)

        if not roles:
            logger.warning(f"No roles found for department: {department}")
            return None

        best_role = None
        best_score = 0

        task_lower = task.lower()

        for role in roles:
            # Count keyword matches in expertise areas
            score = sum(
                1 for keyword in role.expertise_areas
                if keyword.lower() in task_lower
            )

            # Also check if role name is mentioned in task
            if role.role_name.lower() in task_lower:
                score += 2  # Bonus for explicit role mention

            if score > best_score:
                best_score = score
                best_role = role

        # If no expertise match, default to most junior role (IC level)
        if best_role is None:
            ic_roles = [r for r in roles if r.level == RoleLevel.INDIVIDUAL_CONTRIBUTOR]
            if ic_roles:
                best_role = ic_roles[0]
            else:
                best_role = roles[0]  # Fallback to first role

        logger.info(f"Selected role {best_role.role_id} for task in {department} (score: {best_score})")
        return best_role.role_id

    def reload_roles(self):
        """Reload all role definitions from disk"""
        self.roles.clear()
        if self.definitions_dir.exists():
            self._load_roles(self.definitions_dir)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded roles"""
        if not self.roles:
            return {"total_roles": 0, "departments": [], "levels": {}}

        departments = {}
        levels = {}

        for role in self.roles.values():
            # Count by department
            departments[role.department] = departments.get(role.department, 0) + 1

            # Count by level
            level_name = role.level.name
            levels[level_name] = levels.get(level_name, 0) + 1

        return {
            "total_roles": len(self.roles),
            "departments": departments,
            "levels": levels,
            "role_ids": list(self.roles.keys())
        }


# Global registry instance (lazy loaded)
_global_registry: Optional[RoleRegistry] = None


def get_role_registry() -> RoleRegistry:
    """
    Get the global role registry instance.

    Returns:
        Global RoleRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = RoleRegistry()
    return _global_registry
