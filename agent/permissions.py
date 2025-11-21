"""
PHASE 2.2: Role-Based Access Control (RBAC) for Tools

This module implements a comprehensive permission system for tool access control.
Addresses vulnerability A7: Manager and Employee have same tool access.

Key Components:
- Permission: Enum of all system permissions
- Role: Dataclass defining roles with permissions
- PermissionChecker: Central permission validation logic

Design Principles:
- Principle of Least Privilege: Grant minimum permissions needed
- Role-Based: Permissions tied to roles, not individual users
- Domain-Aware: Different permissions in different domains (hr, finance, etc.)
- Auditable: All permission checks logged
- Extensible: Easy to add new permissions and roles

Usage:
    from agent.permissions import PermissionChecker, Permission

    checker = PermissionChecker()

    # Check single permission
    has_perm = checker.check_permission("hr_recruiter", Permission.HRIS_WRITE, "hr")

    # Check tool access
    allowed, reason = checker.check_tool_access("hr_recruiter", "send_email", "hr")
    if not allowed:
        print(f"Access denied: {reason}")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# Permission Definitions
# ══════════════════════════════════════════════════════════════════════


class Permission(str, Enum):
    """
    System-wide permissions for tool access control.

    Organized by category:
    - Filesystem operations
    - Git operations
    - Code execution
    - HR department
    - Finance department
    - Legal department
    - Administrative
    """

    # Filesystem
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    FILESYSTEM_DELETE = "filesystem_delete"

    # Git operations
    GIT_READ = "git_read"          # status, diff, log
    GIT_WRITE = "git_write"        # commit, push
    GIT_BRANCH = "git_branch"      # create/delete branches
    GIT_MERGE = "git_merge"        # merge branches

    # Code execution
    SANDBOX_EXECUTE = "sandbox_execute"     # Execute code in sandbox
    SHELL_EXECUTE = "shell_execute"         # Execute shell commands
    CODE_EXECUTE = "code_execute"           # Generic code execution

    # HR tools
    EMAIL_SEND = "email_send"
    CALENDAR_READ = "calendar_read"
    CALENDAR_WRITE = "calendar_write"
    HRIS_READ = "hris_read"
    HRIS_WRITE = "hris_write"
    HRIS_DELETE = "hris_delete"
    CANDIDATE_READ = "candidate_read"
    CANDIDATE_WRITE = "candidate_write"
    OFFER_CREATE = "offer_create"
    OFFER_APPROVE = "offer_approve"

    # Finance tools
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    ACCOUNTING_READ = "accounting_read"
    ACCOUNTING_WRITE = "accounting_write"
    INVOICE_CREATE = "invoice_create"
    INVOICE_APPROVE = "invoice_approve"
    PAYMENT_CREATE = "payment_create"
    PAYMENT_APPROVE = "payment_approve"

    # Legal tools
    DOCUMENT_READ = "document_read"
    DOCUMENT_WRITE = "document_write"
    LEGAL_DB_ACCESS = "legal_db_access"
    CONTRACT_CREATE = "contract_create"
    CONTRACT_REVIEW = "contract_review"
    CONTRACT_SIGN = "contract_sign"

    # Administrative
    CONFIG_READ = "config_read"
    CONFIG_WRITE = "config_write"
    USER_MANAGE = "user_manage"
    TOOL_INSTALL = "tool_install"
    AUDIT_VIEW = "audit_view"
    PERMISSION_GRANT = "permission_grant"


# ══════════════════════════════════════════════════════════════════════
# Role Definitions
# ══════════════════════════════════════════════════════════════════════


@dataclass
class Role:
    """
    Role definition with associated permissions and capabilities.

    Attributes:
        role_id: Unique role identifier (e.g., "hr_recruiter")
        role_name: Human-readable name (e.g., "HR Recruiter")
        level: Organizational level (1=IC, 2=Manager, 3=Director, etc.)
        base_permissions: Core permissions granted to this role
        can_delegate: Whether role can delegate tasks
        can_approve: Whether role can approve workflows
        description: Description of the role's responsibilities
    """
    role_id: str
    role_name: str
    level: int
    base_permissions: Set[Permission] = field(default_factory=set)
    can_delegate: bool = False
    can_approve: bool = False
    description: str = ""

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission"""
        return permission in self.base_permissions


# ══════════════════════════════════════════════════════════════════════
# Standard System Roles
# ══════════════════════════════════════════════════════════════════════


SYSTEM_ROLES: Dict[str, Role] = {
    # ─────────────────────────────────────────────────────────────────
    # Generic System Roles
    # ─────────────────────────────────────────────────────────────────

    "manager": Role(
        role_id="manager",
        role_name="Manager",
        level=2,
        base_permissions={
            Permission.FILESYSTEM_READ,
            Permission.GIT_READ,
            Permission.SANDBOX_EXECUTE,
            Permission.CONFIG_READ,
            Permission.AUDIT_VIEW,
        },
        can_approve=True,
        description="Orchestrator manager - plans and delegates tasks"
    ),

    "supervisor": Role(
        role_id="supervisor",
        role_name="Supervisor",
        level=2,
        base_permissions={
            Permission.FILESYSTEM_READ,
            Permission.FILESYSTEM_WRITE,
            Permission.GIT_READ,
            Permission.SANDBOX_EXECUTE,
            Permission.CONFIG_READ,
        },
        can_delegate=True,
        description="Orchestrator supervisor - evaluates and provides feedback"
    ),

    "employee": Role(
        role_id="employee",
        role_name="Employee",
        level=1,
        base_permissions={
            Permission.FILESYSTEM_READ,
            Permission.FILESYSTEM_WRITE,
            Permission.GIT_READ,
            Permission.GIT_WRITE,
            Permission.SANDBOX_EXECUTE,
            Permission.CODE_EXECUTE,
        },
        description="Orchestrator employee - executes tasks and commits code"
    ),

    # ─────────────────────────────────────────────────────────────────
    # HR Department Roles
    # ─────────────────────────────────────────────────────────────────

    "hr_manager": Role(
        role_id="hr_manager",
        role_name="HR Manager",
        level=2,
        base_permissions={
            Permission.FILESYSTEM_READ,
            Permission.FILESYSTEM_WRITE,
            Permission.EMAIL_SEND,
            Permission.CALENDAR_READ,
            Permission.CALENDAR_WRITE,
            Permission.HRIS_READ,
            Permission.HRIS_WRITE,
            Permission.HRIS_DELETE,
            Permission.CANDIDATE_READ,
            Permission.CANDIDATE_WRITE,
            Permission.OFFER_CREATE,
            Permission.OFFER_APPROVE,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
        },
        can_approve=True,
        can_delegate=True,
        description="HR Manager - full HR system access, can approve offers"
    ),

    "hr_recruiter": Role(
        role_id="hr_recruiter",
        role_name="HR Recruiter",
        level=1,
        base_permissions={
            Permission.FILESYSTEM_READ,
            Permission.EMAIL_SEND,
            Permission.CALENDAR_READ,
            Permission.CALENDAR_WRITE,
            Permission.HRIS_READ,
            Permission.CANDIDATE_READ,
            Permission.CANDIDATE_WRITE,
            Permission.OFFER_CREATE,  # Can create but not approve
            Permission.DOCUMENT_READ,
        },
        description="HR Recruiter - candidate management, cannot approve offers"
    ),

    "hr_business_partner": Role(
        role_id="hr_business_partner",
        role_name="HR Business Partner",
        level=2,
        base_permissions={
            Permission.FILESYSTEM_READ,
            Permission.FILESYSTEM_WRITE,
            Permission.EMAIL_SEND,
            Permission.CALENDAR_READ,
            Permission.HRIS_READ,
            Permission.HRIS_WRITE,
            Permission.CANDIDATE_READ,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
        },
        can_delegate=True,
        description="HR Business Partner - employee relations and development"
    ),

    # ─────────────────────────────────────────────────────────────────
    # Finance Department Roles
    # ─────────────────────────────────────────────────────────────────

    "finance_controller": Role(
        role_id="finance_controller",
        role_name="Finance Controller",
        level=3,
        base_permissions={
            Permission.DATABASE_READ,
            Permission.DATABASE_WRITE,
            Permission.ACCOUNTING_READ,
            Permission.ACCOUNTING_WRITE,
            Permission.INVOICE_CREATE,
            Permission.INVOICE_APPROVE,
            Permission.PAYMENT_CREATE,
            Permission.PAYMENT_APPROVE,
            Permission.DOCUMENT_WRITE,
        },
        can_approve=True,
        description="Finance Controller - full financial system access"
    ),

    "finance_analyst": Role(
        role_id="finance_analyst",
        role_name="Finance Analyst",
        level=1,
        base_permissions={
            Permission.DATABASE_READ,
            Permission.ACCOUNTING_READ,
            Permission.DOCUMENT_READ,
            Permission.INVOICE_CREATE,  # Can create but not approve
        },
        description="Finance Analyst - financial reporting and analysis"
    ),

    # ─────────────────────────────────────────────────────────────────
    # Legal Department Roles
    # ─────────────────────────────────────────────────────────────────

    "legal_counsel": Role(
        role_id="legal_counsel",
        role_name="Legal Counsel",
        level=3,
        base_permissions={
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_WRITE,
            Permission.LEGAL_DB_ACCESS,
            Permission.CONTRACT_CREATE,
            Permission.CONTRACT_REVIEW,
            Permission.CONTRACT_SIGN,
        },
        can_approve=True,
        description="Legal Counsel - contract review and legal advisory"
    ),

    "legal_assistant": Role(
        role_id="legal_assistant",
        role_name="Legal Assistant",
        level=1,
        base_permissions={
            Permission.DOCUMENT_READ,
            Permission.LEGAL_DB_ACCESS,
            Permission.CONTRACT_CREATE,  # Can draft but not sign
        },
        description="Legal Assistant - contract drafting and administrative support"
    ),
}


# ══════════════════════════════════════════════════════════════════════
# Permission Checker
# ══════════════════════════════════════════════════════════════════════


class PermissionChecker:
    """
    Central permission validation and checking logic.

    Handles:
    - Base role permissions
    - Domain-specific permission augmentation
    - Tool access validation
    - Permission matrix loading
    """

    def __init__(
        self,
        roles: Optional[Dict[str, Role]] = None,
        matrix_path: Optional[Path] = None
    ):
        """
        Initialize permission checker.

        Args:
            roles: Custom role definitions (defaults to SYSTEM_ROLES)
            matrix_path: Path to permissions matrix JSON file
        """
        self.roles = roles if roles is not None else SYSTEM_ROLES
        self.matrix_path = matrix_path or (
            Path(__file__).parent / "permissions_matrix.json"
        )

        # Load permission matrix
        self.domain_role_permissions: Dict[str, Dict[str, List[str]]] = {}
        self.tool_overrides: Dict[str, Dict] = {}
        self.escalation_paths: Dict[str, Dict] = {}
        self._load_permission_matrix()

    def _load_permission_matrix(self) -> None:
        """Load permission matrix from JSON file"""
        if not self.matrix_path.exists():
            logger.warning(
                f"Permission matrix not found: {self.matrix_path}. "
                "Using base role permissions only."
            )
            return

        try:
            with open(self.matrix_path, 'r') as f:
                matrix = json.load(f)

            self.domain_role_permissions = matrix.get("domain_role_permissions", {})
            self.tool_overrides = matrix.get("tool_overrides", {})
            self.escalation_paths = matrix.get("escalation_paths", {})

            logger.info(
                f"Loaded permission matrix: "
                f"{len(self.domain_role_permissions)} domains, "
                f"{len(self.tool_overrides)} tool overrides, "
                f"{len(self.escalation_paths)} escalation paths"
            )
        except Exception as e:
            logger.error(f"Failed to load permission matrix: {e}", exc_info=True)

    def get_role(self, role_id: str) -> Optional[Role]:
        """Get role definition by ID"""
        return self.roles.get(role_id)

    def get_permissions(
        self,
        role_id: str,
        domain: Optional[str] = None
    ) -> Set[Permission]:
        """
        Get effective permissions for a role in a domain.

        Combines:
        1. Base role permissions
        2. Domain-specific permissions from matrix

        Args:
            role_id: Role identifier
            domain: Optional domain for domain-specific permissions

        Returns:
            Set of effective permissions

        Example:
            perms = checker.get_permissions("hr_recruiter", "hr")
            if Permission.HRIS_WRITE in perms:
                print("Can write to HRIS")
        """
        role = self.roles.get(role_id)
        if not role:
            logger.warning(f"Unknown role: {role_id}")
            return set()

        # Start with base permissions
        permissions = role.base_permissions.copy()

        # Add domain-specific permissions
        if domain:
            domain_perms = self._get_domain_permissions(role_id, domain)
            permissions.update(domain_perms)

        return permissions

    def _get_domain_permissions(
        self,
        role_id: str,
        domain: str
    ) -> Set[Permission]:
        """
        Get additional permissions granted by domain.

        Loads from permissions_matrix.json.

        Args:
            role_id: Role identifier
            domain: Domain name

        Returns:
            Set of domain-specific permissions
        """
        if domain not in self.domain_role_permissions:
            return set()

        role_perms = self.domain_role_permissions[domain].get(role_id, [])

        # Convert string permissions to Permission enum
        permissions = set()
        for perm_str in role_perms:
            try:
                # Handle both "email_send" and "EMAIL_SEND" formats
                perm_str_upper = perm_str.upper()
                perm = Permission[perm_str_upper]
                permissions.add(perm)
            except KeyError:
                logger.warning(
                    f"Unknown permission in matrix: {perm_str} "
                    f"for role {role_id} in domain {domain}"
                )

        return permissions

    def check_permission(
        self,
        role_id: str,
        required_permission: Permission,
        domain: Optional[str] = None
    ) -> bool:
        """
        Check if role has required permission.

        Args:
            role_id: Role identifier
            required_permission: Permission to check
            domain: Optional domain context

        Returns:
            True if role has permission, False otherwise

        Example:
            if checker.check_permission("hr_recruiter", Permission.OFFER_APPROVE, "hr"):
                approve_offer()
            else:
                print("Permission denied")
        """
        permissions = self.get_permissions(role_id, domain)
        return required_permission in permissions

    def check_tool_access(
        self,
        role_id: str,
        tool_name: str,
        domain: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if role can access tool in domain.

        Validates:
        1. Role is in tool's allowed roles
        2. Domain matches tool's domains
        3. Role has all required permissions
        4. Tool override rules (from matrix)

        Args:
            role_id: Role identifier
            tool_name: Tool name
            domain: Optional domain context

        Returns:
            (allowed: bool, reason: Optional[str])
            - allowed: True if access granted
            - reason: Error message if denied, None if allowed

        Example:
            allowed, reason = checker.check_tool_access(
                "hr_recruiter",
                "approve_offer",
                "hr"
            )
            if not allowed:
                log_security_event(f"Access denied: {reason}")
        """
        # Check tool overrides first
        if tool_name in self.tool_overrides:
            override = self.tool_overrides[tool_name]

            # Check if role is blocked
            blocked_roles = override.get("blocked_roles", [])
            if role_id in blocked_roles:
                reason = override.get("reason", "Role blocked by override")
                return False, f"Access denied: {reason}"

            # Check if role is explicitly allowed
            allowed_roles = override.get("allowed_roles", [])
            if allowed_roles and role_id not in allowed_roles:
                reason = override.get("reason", "Role not in allowed list")
                return False, f"Access denied: {reason}"

        # Get tool from registry
        try:
            from agent.tools.plugin_loader import get_global_registry
            registry = get_global_registry()
        except Exception as e:
            logger.error(f"Failed to get tool registry: {e}")
            return False, "Tool registry unavailable"

        tool = registry.get_tool(tool_name)
        if not tool:
            return False, f"Tool '{tool_name}' not found"

        manifest = tool.get_manifest()

        # Check if role is allowed
        if role_id not in manifest.roles and "*" not in manifest.roles and "any" not in manifest.roles:
            return False, f"Role '{role_id}' not authorized for this tool"

        # Check domain
        if domain and domain not in manifest.domains:
            return False, f"Tool not available in domain '{domain}'"

        # Check permissions
        role_permissions = self.get_permissions(role_id, domain)
        required_perms_str = set(manifest.required_permissions)

        # Convert string permissions to Permission enum for comparison
        required_perms = set()
        for perm_str in required_perms_str:
            try:
                perm_str_upper = perm_str.upper()
                perm = Permission[perm_str_upper]
                required_perms.add(perm)
            except KeyError:
                # If permission not in enum, treat as string comparison
                logger.warning(f"Unknown permission: {perm_str}")
                continue

        # Check if role has all required permissions
        if not required_perms.issubset(role_permissions):
            missing = required_perms - role_permissions
            missing_strs = [p.value for p in missing]
            return False, f"Missing permissions: {', '.join(missing_strs)}"

        return True, None

    def get_escalation_path(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        Get escalation path for a role (for privilege elevation).

        Args:
            role_id: Role identifier

        Returns:
            Dict with escalation info or None if no escalation path exists

        Example:
            escalation = checker.get_escalation_path("hr_recruiter")
            if escalation:
                print(f"Escalate to: {escalation['escalate_to']}")
                print(f"Allowed permissions: {escalation['allowed_permissions']}")
        """
        return self.escalation_paths.get(role_id)

    def list_accessible_tools(
        self,
        role_id: str,
        domain: Optional[str] = None
    ) -> List[str]:
        """
        Get list of tools accessible to a role in a domain.

        Args:
            role_id: Role identifier
            domain: Optional domain filter

        Returns:
            List of tool names the role can access

        Example:
            tools = checker.list_accessible_tools("hr_recruiter", "hr")
            print(f"Available tools: {tools}")
        """
        try:
            from agent.tools.plugin_loader import get_global_registry
            registry = get_global_registry()
        except Exception:
            return []

        accessible = []

        # Get all tools in domain
        if domain:
            tool_names = registry.get_tools_for_domain(domain)
        else:
            tool_names = list(registry.tools.keys())

        # Filter by access
        for tool_name in tool_names:
            allowed, _ = self.check_tool_access(role_id, tool_name, domain)
            if allowed:
                accessible.append(tool_name)

        return accessible


# ══════════════════════════════════════════════════════════════════════
# Global Permission Checker Singleton
# ══════════════════════════════════════════════════════════════════════


_global_permission_checker: Optional[PermissionChecker] = None


def get_permission_checker() -> PermissionChecker:
    """
    Get global permission checker singleton.

    Returns:
        Global PermissionChecker instance

    Example:
        from agent.permissions import get_permission_checker

        checker = get_permission_checker()
        if checker.check_permission("manager", Permission.GIT_WRITE):
            execute_git_commit()
    """
    global _global_permission_checker

    if _global_permission_checker is None:
        _global_permission_checker = PermissionChecker()

    return _global_permission_checker


def reset_permission_checker() -> None:
    """
    Reset global permission checker (useful for testing).

    Example:
        # In tests
        reset_permission_checker()
        checker = get_permission_checker()  # Fresh instance
    """
    global _global_permission_checker
    _global_permission_checker = None
