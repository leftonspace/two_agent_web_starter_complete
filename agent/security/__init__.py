"""
PHASE 11.3: Security & Authentication

Production-grade security controls with authentication, authorization, and auditing.

Components:
- auth: API key management, OAuth 2.0, RBAC
- rate_limit: Token bucket rate limiting
- audit_log: Security event logging

Features:
- API key authentication with secure hashing
- Role-based access control (RBAC)
- Per-user rate limiting
- Comprehensive audit logging
- Secret rotation support
- OAuth 2.0 integration
"""

from .auth import (
    AuthManager,
    User,
    Role,
    Permission,
    APIKey,
    OAuthProvider,
)
from .rate_limit import (
    RateLimiter,
    RateLimitExceeded,
    TokenBucket,
)
from .audit_log import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
)

__all__ = [
    "AuthManager",
    "User",
    "Role",
    "Permission",
    "APIKey",
    "OAuthProvider",
    "RateLimiter",
    "RateLimitExceeded",
    "TokenBucket",
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
]
