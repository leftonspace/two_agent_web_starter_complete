"""
PHASE 11.3: Security & Authentication
PHASE 1 HARDENING: Security & Sandboxing
PHASE 4.1 HARDENING: Secrets Management

Production-grade security controls with authentication, authorization, and auditing.

Components:
- auth: API key management, OAuth 2.0, RBAC
- rate_limit: Token bucket rate limiting
- audit_log: Security event logging
- network: SSRF protection and egress filtering (Phase 1.2)
- approval: Human-in-the-loop approval system (Phase 1.3)
- sandbox_docker: Docker-based isolated execution (Phase 1.1)
- secrets: Multi-backend secrets management (Phase 4.1)

Features:
- API key authentication with secure hashing
- Role-based access control (RBAC)
- Per-user rate limiting
- Comprehensive audit logging
- Secret rotation support
- OAuth 2.0 integration
- SSRF protection with blocked IP ranges
- HITL approval for dangerous operations
- Docker-based sandboxed code execution
- Multi-backend secrets (Vault, AWS, Azure, env)
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

# Phase 1 Hardening imports
from .network import (
    NetworkSecurityValidator,
    SSRFError,
    is_url_safe,
    is_ip_blocked,
    validate_url_or_raise,
    BLOCKED_IP_RANGES,
)
from .approval import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalResult,
    ApprovalRequired,
    ApprovalStatus,
    RiskLevel,
    require_approval,
    get_default_manager as get_approval_manager,
)
from .sandbox_docker import (
    DockerSandbox,
    SandboxResult,
    SandboxLanguage,
    run_in_sandbox,
    is_sandbox_available,
)

# Phase 4.1: Secrets Management
from .secrets import (
    SecretsManager,
    SecretBackend,
    get_secret,
    require_secret,
    configure_secrets,
    get_secrets_manager,
)

__all__ = [
    # Auth
    "AuthManager",
    "User",
    "Role",
    "Permission",
    "APIKey",
    "OAuthProvider",
    # Rate limiting
    "RateLimiter",
    "RateLimitExceeded",
    "TokenBucket",
    # Audit logging
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    # Network security (Phase 1.2)
    "NetworkSecurityValidator",
    "SSRFError",
    "is_url_safe",
    "is_ip_blocked",
    "validate_url_or_raise",
    "BLOCKED_IP_RANGES",
    # Approval system (Phase 1.3)
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalResult",
    "ApprovalRequired",
    "ApprovalStatus",
    "RiskLevel",
    "require_approval",
    "get_approval_manager",
    # Docker sandbox (Phase 1.1)
    "DockerSandbox",
    "SandboxResult",
    "SandboxLanguage",
    "run_in_sandbox",
    "is_sandbox_available",
    # Secrets management (Phase 4.1)
    "SecretsManager",
    "SecretBackend",
    "get_secret",
    "require_secret",
    "configure_secrets",
    "get_secrets_manager",
]
