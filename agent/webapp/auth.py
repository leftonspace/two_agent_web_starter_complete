"""
Authentication and Authorization Module for Web Dashboard

Implements:
- API Key authentication for programmatic access
- Session-based authentication for web UI
- Role-based access control (admin, developer, viewer)
- CSRF protection for web forms

Security Features:
- Bcrypt password hashing
- Secure session management
- Configurable auth bypass for development
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel


# ══════════════════════════════════════════════════════════════════════
# User Roles
# ══════════════════════════════════════════════════════════════════════


class UserRole(str, Enum):
    """User roles with different permission levels."""

    ADMIN = "admin"  # Full access: manage keys, users, system config
    DEVELOPER = "developer"  # Run jobs, view analytics, modify projects
    VIEWER = "viewer"  # Read-only: view jobs, analytics, logs


# ══════════════════════════════════════════════════════════════════════
# Models
# ══════════════════════════════════════════════════════════════════════


class User(BaseModel):
    """User model for authentication."""

    user_id: str
    username: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None


class Session(BaseModel):
    """Session model for web UI authentication."""

    session_id: str
    user_id: str
    username: str
    role: UserRole
    created_at: datetime
    expires_at: datetime
    csrf_token: str


# ══════════════════════════════════════════════════════════════════════
# Session Storage (In-Memory)
# ══════════════════════════════════════════════════════════════════════


class SessionStore:
    """
    In-memory session storage.

    For production, consider using Redis or a database.
    """

    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def create_session(self, user: User, ttl_hours: int = 24) -> Session:
        """Create a new session for a user."""
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        now = datetime.now()

        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
            csrf_token=csrf_token,
        )

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID, returns None if expired."""
        session = self.sessions.get(session_id)
        if session is None:
            return None

        # Check expiration
        if datetime.now() > session.expires_at:
            del self.sessions[session_id]
            return None

        return session

    def delete_session(self, session_id: str) -> bool:
        """Delete a session (logout)."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        now = datetime.now()
        expired = [
            sid for sid, sess in self.sessions.items() if now > sess.expires_at
        ]
        for sid in expired:
            del self.sessions[sid]
        return len(expired)


# Global session store instance
_session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Get the global session store."""
    return _session_store


# ══════════════════════════════════════════════════════════════════════
# Authentication Dependencies
# ══════════════════════════════════════════════════════════════════════


# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_api_key(
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[User]:
    """
    Authenticate user via API key from X-API-Key header.

    Returns User if valid key, None otherwise.
    """
    if not api_key:
        return None

    # Import here to avoid circular dependency
    from agent.webapp.api_keys import get_api_key_manager

    api_key_manager = get_api_key_manager()
    key_data = api_key_manager.verify_key(api_key)

    if key_data is None:
        return None

    # Convert to User object
    return User(
        user_id=key_data["user_id"],
        username=key_data.get("username", key_data["user_id"]),
        role=UserRole(key_data["role"]),
        created_at=datetime.fromisoformat(key_data["created_at"]),
    )


async def get_current_user_from_session(request: Request) -> Optional[User]:
    """
    Authenticate user via session cookie.

    Returns User if valid session, None otherwise.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    session_store = get_session_store()
    session = session_store.get_session(session_id)

    if session is None:
        return None

    # Convert to User object
    return User(
        user_id=session.user_id,
        username=session.username,
        role=session.role,
        created_at=session.created_at,
        last_login=session.created_at,
    )


async def get_current_user(
    request: Request,
    api_user: Optional[User] = Depends(get_current_user_from_api_key),
    session_user: Optional[User] = Depends(get_current_user_from_session),
) -> Optional[User]:
    """
    Get current authenticated user from either API key or session.

    Priority: API key > Session
    Returns None if not authenticated.
    """
    # Check if auth is disabled via config
    from agent.config import get_config

    config = get_config()

    if not config.auth.enabled:
        # Auth disabled - return a default admin user
        return User(
            user_id="dev",
            username="developer",
            role=UserRole.ADMIN,
            created_at=datetime.now(),
        )

    # Try API key first, then session
    return api_user or session_user


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """
    Require authentication. Raises 401 if not authenticated.

    Use this as a dependency on protected routes.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_role(
    required_role: UserRole,
    current_user: User = Depends(require_auth),
) -> User:
    """
    Require specific role or higher.

    Role hierarchy: ADMIN > DEVELOPER > VIEWER
    """
    role_hierarchy = {UserRole.VIEWER: 1, UserRole.DEVELOPER: 2, UserRole.ADMIN: 3}

    user_level = role_hierarchy[current_user.role]
    required_level = role_hierarchy[required_role]

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role.value}",
        )

    return current_user


def require_admin(current_user: User = Depends(require_auth)) -> User:
    """Require admin role. Use as dependency on admin-only routes."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_developer(current_user: User = Depends(require_auth)) -> User:
    """Require developer role or higher. Use as dependency on developer routes."""
    if current_user.role == UserRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer access required",
        )
    return current_user


# ══════════════════════════════════════════════════════════════════════
# CSRF Protection
# ══════════════════════════════════════════════════════════════════════


async def verify_csrf_token(request: Request) -> bool:
    """
    Verify CSRF token for state-changing operations.

    Checks that the csrf_token in the form matches the session's CSRF token.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        return False

    session_store = get_session_store()
    session = session_store.get_session(session_id)
    if session is None:
        return False

    # Get CSRF token from form or header
    form_data = await request.form()
    csrf_token = form_data.get("csrf_token") or request.headers.get("X-CSRF-Token")

    if not csrf_token:
        return False

    return secrets.compare_digest(csrf_token, session.csrf_token)


async def require_csrf(request: Request):
    """
    Require valid CSRF token for POST/PUT/DELETE requests.

    Use as dependency on state-changing routes.
    """
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if not await verify_csrf_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing CSRF token",
            )


# ══════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════


def get_csrf_token_from_request(request: Request) -> Optional[str]:
    """Get CSRF token from current session for including in forms."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    session_store = get_session_store()
    session = session_store.get_session(session_id)
    if session is None:
        return None

    return session.csrf_token


def is_authenticated(request: Request) -> bool:
    """Check if request is authenticated (for templates)."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        return False

    session_store = get_session_store()
    session = session_store.get_session(session_id)
    return session is not None
