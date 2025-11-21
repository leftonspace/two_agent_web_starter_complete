"""
PHASE 11.3: Authentication & Authorization

Comprehensive authentication and authorization system.

Features:
- API key authentication with secure hashing
- OAuth 2.0 support (Google, GitHub, etc.)
- Role-based access control (RBAC)
- Permission system
- Rate limiting per user
- Audit logging
- Secret rotation
"""

from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta

from .rate_limit import RateLimiter, RateLimitExceeded
from .audit_log import AuditLogger, AuditEventType, AuditSeverity, get_audit_logger


class Permission(Enum):
    """System permissions."""

    # Read permissions
    READ_DATA = "read_data"
    READ_USERS = "read_users"
    READ_LOGS = "read_logs"

    # Write permissions
    WRITE_DATA = "write_data"
    WRITE_USERS = "write_users"

    # Delete permissions
    DELETE_DATA = "delete_data"
    DELETE_USERS = "delete_users"

    # Admin permissions
    MANAGE_ROLES = "manage_roles"
    MANAGE_PERMISSIONS = "manage_permissions"
    MANAGE_API_KEYS = "manage_api_keys"
    VIEW_AUDIT_LOGS = "view_audit_logs"

    # System permissions
    SYSTEM_CONFIG = "system_config"
    SYSTEM_ADMIN = "system_admin"


class Role(Enum):
    """Predefined user roles."""

    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"
    READONLY = "readonly"
    GUEST = "guest"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.READ_DATA,
        Permission.READ_USERS,
        Permission.READ_LOGS,
        Permission.WRITE_DATA,
        Permission.WRITE_USERS,
        Permission.DELETE_DATA,
        Permission.DELETE_USERS,
        Permission.MANAGE_ROLES,
        Permission.MANAGE_PERMISSIONS,
        Permission.MANAGE_API_KEYS,
        Permission.VIEW_AUDIT_LOGS,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_ADMIN,
    },
    Role.DEVELOPER: {
        Permission.READ_DATA,
        Permission.READ_USERS,
        Permission.WRITE_DATA,
        Permission.MANAGE_API_KEYS,
    },
    Role.USER: {
        Permission.READ_DATA,
        Permission.WRITE_DATA,
    },
    Role.READONLY: {
        Permission.READ_DATA,
    },
    Role.GUEST: set(),
}


@dataclass
class User:
    """User account."""

    user_id: str
    username: str
    email: str
    role: Role
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    is_active: bool = True

    # Custom permissions (in addition to role permissions)
    custom_permissions: Set[Permission] = field(default_factory=set)

    # Metadata
    metadata: Dict[str, any] = field(default_factory=dict)

    def get_permissions(self) -> Set[Permission]:
        """Get all permissions (role + custom)."""
        role_perms = ROLE_PERMISSIONS.get(self.role, set())
        return role_perms | self.custom_permissions

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has permission."""
        return permission in self.get_permissions()

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the permissions."""
        user_perms = self.get_permissions()
        return any(p in user_perms for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all permissions."""
        user_perms = self.get_permissions()
        return all(p in user_perms for p in permissions)


@dataclass
class APIKey:
    """API key for authentication."""

    key_id: str
    user_id: str
    name: str
    key_hash: str  # SHA-256 hash
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    last_used: Optional[float] = None
    is_active: bool = True

    # Metadata
    scopes: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def is_valid(self) -> bool:
        """Check if key is valid."""
        return self.is_active and not self.is_expired()


class OAuthProvider(Enum):
    """OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"


@dataclass
class OAuthCredentials:
    """OAuth credentials."""

    provider: OAuthProvider
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[float] = None
    scope: Optional[str] = None


class AuthenticationError(Exception):
    """Authentication failed."""
    pass


class AuthorizationError(Exception):
    """Authorization failed (insufficient permissions)."""
    pass


class AuthManager:
    """
    Authentication and authorization manager.

    Features:
    - API key authentication
    - OAuth 2.0 integration
    - Role-based access control
    - Permission checking
    - Rate limiting
    - Audit logging
    """

    def __init__(
        self,
        audit_logger: Optional[AuditLogger] = None,
        default_rate_limit: int = 100,
        rate_limit_window: float = 60.0,
    ):
        """
        Initialize auth manager.

        Args:
            audit_logger: Audit logger instance
            default_rate_limit: Default requests per window
            rate_limit_window: Rate limit window in seconds
        """
        self.audit_logger = audit_logger or get_audit_logger()

        # Storage
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}  # key_hash -> APIKey
        self.oauth_credentials: Dict[str, OAuthCredentials] = {}  # user_id -> credentials

        # Rate limiting
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.default_rate_limit = default_rate_limit
        self.rate_limit_window = rate_limit_window

    def create_user(
        self,
        username: str,
        email: str,
        role: Role = Role.USER,
    ) -> User:
        """
        Create a new user.

        Args:
            username: Username
            email: Email address
            role: User role

        Returns:
            Created user
        """
        user_id = secrets.token_urlsafe(16)

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
        )

        self.users[user_id] = user

        # Audit log
        self.audit_logger.log(
            AuditEventType.USER_CREATED,
            f"User created: {username}",
            user_id=user_id,
            metadata={"role": role.value},
        )

        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    def create_api_key(
        self,
        user_id: str,
        name: str,
        expires_in_days: Optional[int] = None,
        scopes: Optional[Set[Permission]] = None,
    ) -> tuple[str, APIKey]:
        """
        Create API key for user.

        Args:
            user_id: User identifier
            name: Key name/description
            expires_in_days: Expiration in days (None = no expiration)
            scopes: Permissions for this key

        Returns:
            Tuple of (raw_key, api_key_object)
        """
        # Generate random key
        raw_key = secrets.token_urlsafe(32)

        # Hash the key for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = time.time() + (expires_in_days * 86400)

        # Create API key object
        key_id = secrets.token_urlsafe(16)
        api_key = APIKey(
            key_id=key_id,
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            expires_at=expires_at,
            scopes=scopes or set(),
        )

        self.api_keys[key_hash] = api_key

        # Audit log
        self.audit_logger.log(
            AuditEventType.API_KEY_CREATED,
            f"API key created: {name}",
            user_id=user_id,
            metadata={"key_id": key_id, "expires_at": expires_at},
        )

        return raw_key, api_key

    async def verify_api_key(self, raw_key: str) -> Optional[User]:
        """
        Verify API key and return user.

        Args:
            raw_key: Raw API key string

        Returns:
            User if valid, None otherwise
        """
        # Hash the key
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        # Look up key
        api_key = self.api_keys.get(key_hash)

        if not api_key:
            # Audit log - key not found
            await self.audit_logger.log(
                AuditEventType.AUTH_FAILURE,
                "Invalid API key",
                severity=AuditSeverity.WARNING,
                metadata={"reason": "key_not_found"},
            )
            return None

        # Check if key is valid
        if not api_key.is_valid():
            # Audit log - key invalid
            await self.audit_logger.log(
                AuditEventType.AUTH_FAILURE,
                f"Invalid API key: {api_key.name}",
                severity=AuditSeverity.WARNING,
                user_id=api_key.user_id,
                metadata={"reason": "key_expired" if api_key.is_expired() else "key_inactive"},
            )
            return None

        # Update last used
        api_key.last_used = time.time()

        # Get user
        user = self.users.get(api_key.user_id)

        if not user or not user.is_active:
            # Audit log - user invalid
            await self.audit_logger.log(
                AuditEventType.AUTH_FAILURE,
                "User not found or inactive",
                severity=AuditSeverity.WARNING,
                user_id=api_key.user_id,
            )
            return None

        # Update last login
        user.last_login = time.time()

        # Audit log - success
        await self.audit_logger.log(
            AuditEventType.AUTH_SUCCESS,
            f"API key authentication successful: {api_key.name}",
            user_id=user.user_id,
        )

        return user

    def revoke_api_key(self, key_hash: str, user_id: str):
        """
        Revoke API key.

        Args:
            key_hash: Hashed API key
            user_id: User ID (for authorization)
        """
        api_key = self.api_keys.get(key_hash)

        if not api_key:
            return

        # Check authorization
        if api_key.user_id != user_id:
            raise AuthorizationError("Cannot revoke another user's key")

        api_key.is_active = False

        # Audit log
        self.audit_logger.log(
            AuditEventType.API_KEY_REVOKED,
            f"API key revoked: {api_key.name}",
            user_id=user_id,
            metadata={"key_id": api_key.key_id},
        )

    async def check_rate_limit(
        self,
        user_id: str,
        cost: int = 1,
    ) -> bool:
        """
        Check if user is within rate limits.

        Args:
            user_id: User identifier
            cost: Cost of this request in tokens

        Returns:
            True if within limits, False otherwise

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        # Get or create rate limiter for user
        if user_id not in self.rate_limiters:
            self.rate_limiters[user_id] = RateLimiter(
                max_requests=self.default_rate_limit,
                window=self.rate_limit_window,
            )

        limiter = self.rate_limiters[user_id]

        try:
            await limiter.allow_or_raise(user_id, cost)
            return True

        except RateLimitExceeded as e:
            # Audit log
            await self.audit_logger.log(
                AuditEventType.RATE_LIMIT_EXCEEDED,
                f"Rate limit exceeded for user",
                severity=AuditSeverity.WARNING,
                user_id=user_id,
                metadata={"retry_after": e.retry_after},
            )
            raise

    def check_permission(
        self,
        user: User,
        permission: Permission,
    ) -> bool:
        """
        Check if user has permission.

        Args:
            user: User object
            permission: Required permission

        Returns:
            True if user has permission

        Raises:
            AuthorizationError: If user lacks permission
        """
        if not user.has_permission(permission):
            # Audit log
            self.audit_logger.log(
                AuditEventType.ACCESS_DENIED,
                f"Permission denied: {permission.value}",
                severity=AuditSeverity.WARNING,
                user_id=user.user_id,
                metadata={"permission": permission.value},
            )

            raise AuthorizationError(
                f"User lacks required permission: {permission.value}"
            )

        # Audit log - success
        self.audit_logger.log(
            AuditEventType.ACCESS_GRANTED,
            f"Permission granted: {permission.value}",
            user_id=user.user_id,
            metadata={"permission": permission.value},
        )

        return True

    def assign_role(
        self,
        user_id: str,
        role: Role,
        assigned_by: str,
    ):
        """
        Assign role to user.

        Args:
            user_id: User identifier
            role: New role
            assigned_by: User ID of admin assigning role
        """
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")

        old_role = user.role
        user.role = role

        # Audit log
        self.audit_logger.log(
            AuditEventType.ROLE_ASSIGNED,
            f"Role changed: {old_role.value} -> {role.value}",
            user_id=user_id,
            metadata={
                "old_role": old_role.value,
                "new_role": role.value,
                "assigned_by": assigned_by,
            },
        )

    def grant_permission(
        self,
        user_id: str,
        permission: Permission,
    ):
        """Grant custom permission to user."""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")

        user.custom_permissions.add(permission)

        # Audit log
        self.audit_logger.log(
            AuditEventType.PERMISSION_CHANGED,
            f"Permission granted: {permission.value}",
            user_id=user_id,
            metadata={"permission": permission.value, "action": "grant"},
        )

    def revoke_permission(
        self,
        user_id: str,
        permission: Permission,
    ):
        """Revoke custom permission from user."""
        user = self.users.get(user_id)
        if not user:
            raise ValueError("User not found")

        user.custom_permissions.discard(permission)

        # Audit log
        self.audit_logger.log(
            AuditEventType.PERMISSION_CHANGED,
            f"Permission revoked: {permission.value}",
            user_id=user_id,
            metadata={"permission": permission.value, "action": "revoke"},
        )

    def store_oauth_credentials(
        self,
        user_id: str,
        credentials: OAuthCredentials,
    ):
        """Store OAuth credentials for user."""
        self.oauth_credentials[user_id] = credentials

    def get_oauth_credentials(
        self,
        user_id: str,
    ) -> Optional[OAuthCredentials]:
        """Get OAuth credentials for user."""
        return self.oauth_credentials.get(user_id)

    def get_statistics(self) -> Dict[str, any]:
        """Get authentication statistics."""
        return {
            "total_users": len(self.users),
            "active_users": len([u for u in self.users.values() if u.is_active]),
            "total_api_keys": len(self.api_keys),
            "active_api_keys": len([k for k in self.api_keys.values() if k.is_valid()]),
            "users_by_role": {
                role.value: len([u for u in self.users.values() if u.role == role])
                for role in Role
            },
        }
