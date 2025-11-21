"""
Authentication Routes for Web Dashboard

Provides endpoints for:
- Login/Logout (session-based)
- API key management (admin only)
- User authentication status
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from agent.webapp.auth import (
    User,
    UserRole,
    get_current_user,
    get_session_store,
    require_admin,
    require_auth,
)
from agent.webapp.api_keys import create_default_admin_key, get_api_key_manager


# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create router
auth_router = APIRouter(prefix="/auth", tags=["authentication"])
api_keys_router = APIRouter(prefix="/api/keys", tags=["api_keys"])


# ══════════════════════════════════════════════════════════════════════
# Authentication Endpoints
# ══════════════════════════════════════════════════════════════════════


@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page."""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": request.query_params.get("error"),
        },
    )


@auth_router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    api_key: str = Form(...),
):
    """
    Login with API key to create a session.

    This allows users to use their API key once to get a session cookie
    for web UI access.
    """
    # Verify the API key
    api_key_manager = get_api_key_manager()
    key_data = api_key_manager.verify_key(api_key)

    if key_data is None:
        return RedirectResponse(
            url="/auth/login?error=Invalid+credentials",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # Create session
    from agent.webapp.auth import User, get_session_store
    from datetime import datetime

    user = User(
        user_id=key_data["user_id"],
        username=key_data["username"],
        role=UserRole(key_data["role"]),
        created_at=datetime.fromisoformat(key_data["created_at"]),
    )

    from agent.config import get_config

    config = get_config()
    session_ttl = config.auth.session_ttl_hours

    session_store = get_session_store()
    session = session_store.create_session(user, ttl_hours=session_ttl)

    # Set session cookie
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=config.auth.session_cookie_name,
        value=session.session_id,
        max_age=session_ttl * 3600,  # Convert hours to seconds
        httponly=config.auth.session_cookie_httponly,
        secure=config.auth.session_cookie_secure,
        samesite=config.auth.session_cookie_samesite,
    )

    return response


@auth_router.post("/logout")
async def logout(request: Request):
    """Logout and destroy session."""
    from agent.config import get_config

    config = get_config()

    session_id = request.cookies.get(config.auth.session_cookie_name)
    if session_id:
        session_store = get_session_store()
        session_store.delete_session(session_id)

    # Clear cookie
    response = RedirectResponse(
        url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie(key=config.auth.session_cookie_name)

    return response


@auth_router.get("/status")
async def auth_status(current_user: User = Depends(get_current_user)):
    """Check authentication status (for AJAX requests)."""
    if current_user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"authenticated": False},
        )

    return {
        "authenticated": True,
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role.value,
    }


# ══════════════════════════════════════════════════════════════════════
# API Key Management Endpoints (Admin Only)
# ══════════════════════════════════════════════════════════════════════


@api_keys_router.get("/", response_class=HTMLResponse)
async def api_keys_page(request: Request, current_user: User = Depends(require_admin)):
    """Display API keys management page (admin only)."""
    api_key_manager = get_api_key_manager()
    keys = api_key_manager.list_keys(include_revoked=True)

    return templates.TemplateResponse(
        "api_keys.html",
        {
            "request": request,
            "current_user": current_user,
            "keys": keys,
        },
    )


@api_keys_router.get("/list")
async def list_api_keys(current_user: User = Depends(require_admin)):
    """List all API keys (admin only)."""
    api_key_manager = get_api_key_manager()
    keys = api_key_manager.list_keys(include_revoked=True)
    return {"keys": keys}


@api_keys_router.post("/generate")
async def generate_api_key(
    user_id: str = Form(...),
    username: str = Form(...),
    role: str = Form(...),
    ttl_days: int = Form(90),
    description: str = Form(""),
    current_user: User = Depends(require_admin),
):
    """Generate a new API key (admin only)."""
    # Validate role
    if role not in ["admin", "developer", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be: admin, developer, or viewer",
        )

    api_key_manager = get_api_key_manager()
    key_info = api_key_manager.generate_key(
        user_id=user_id,
        username=username,
        role=role,
        ttl_days=ttl_days,
        description=description,
    )

    return {
        "success": True,
        "key_id": key_info["key_id"],
        "api_key": key_info["api_key"],  # Only shown once!
        "user_id": key_info["user_id"],
        "username": key_info["username"],
        "role": key_info["role"],
        "created_at": key_info["created_at"],
        "expires_at": key_info["expires_at"],
        "description": key_info["description"],
        "warning": "Save this API key now. It will not be shown again!",
    }


@api_keys_router.post("/{key_id}/revoke")
async def revoke_api_key(key_id: str, current_user: User = Depends(require_admin)):
    """Revoke an API key (admin only)."""
    api_key_manager = get_api_key_manager()
    success = api_key_manager.revoke_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"success": True, "message": f"API key {key_id} has been revoked"}


@api_keys_router.delete("/{key_id}")
async def delete_api_key(key_id: str, current_user: User = Depends(require_admin)):
    """Permanently delete an API key (admin only)."""
    api_key_manager = get_api_key_manager()
    success = api_key_manager.delete_key(key_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return {"success": True, "message": f"API key {key_id} has been deleted"}


@api_keys_router.get("/{key_id}")
async def get_api_key_info(key_id: str, current_user: User = Depends(require_admin)):
    """Get information about a specific API key (admin only)."""
    api_key_manager = get_api_key_manager()
    key_info = api_key_manager.get_key_info(key_id)

    if key_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    return key_info


# ══════════════════════════════════════════════════════════════════════
# Initialization
# ══════════════════════════════════════════════════════════════════════


def initialize_auth_system():
    """
    Initialize authentication system.

    Creates default admin key if no keys exist.
    """
    from agent.config import get_config

    config = get_config()

    if config.auth.create_default_admin_key:
        default_key = create_default_admin_key()
        if default_key:
            print("\n" + "=" * 60)
            print("🔐 DEFAULT ADMIN API KEY GENERATED")
            print("=" * 60)
            print(f"API Key: {default_key['api_key']}")
            print(f"User ID: {default_key['user_id']}")
            print(f"Role: {default_key['role']}")
            print("\n⚠️  SAVE THIS KEY NOW - IT WILL NOT BE SHOWN AGAIN!")
            print("=" * 60 + "\n")
