"""
API Key Management Module

Handles:
- API key generation and storage
- Key verification with bcrypt
- Key rotation and revocation
- SQLite database for persistence

Database Schema:
- api_keys table: key_id, key_hash, user_id, username, role, created_at, expires_at, last_used

Security:
- Keys are hashed with bcrypt before storage (never store plain text)
- Generated keys use cryptographically secure random tokens
- Keys can have expiration dates
- Last used timestamp tracked for auditing
"""

from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import bcrypt


# ══════════════════════════════════════════════════════════════════════
# API Key Manager
# ══════════════════════════════════════════════════════════════════════


class APIKeyManager:
    """
    Manages API keys with SQLite persistence.

    Keys are stored as bcrypt hashes for security.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize API key manager.

        Args:
            db_path: Path to SQLite database. Defaults to data/api_keys.db
        """
        if db_path is None:
            # Default to data/api_keys.db relative to this file
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "api_keys.db"

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                key_hash TEXT NOT NULL,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                last_used TEXT,
                revoked INTEGER DEFAULT 0,
                description TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def generate_key(
        self,
        user_id: str,
        username: str,
        role: str,
        ttl_days: int = 90,
        description: str = "",
    ) -> Dict[str, str]:
        """
        Generate a new API key.

        Args:
            user_id: Unique user identifier
            username: Human-readable username
            role: User role (admin, developer, viewer)
            ttl_days: Time-to-live in days (0 = no expiration)
            description: Optional key description

        Returns:
            Dict with 'key_id', 'api_key' (plain text - shown only once), and metadata
        """
        # Generate key components
        key_id = f"key_{secrets.token_urlsafe(16)}"
        api_key = f"sk_{secrets.token_urlsafe(32)}"  # Similar to OpenAI format

        # Hash the key with bcrypt
        key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

        # Calculate expiration
        now = datetime.now()
        expires_at = None if ttl_days == 0 else now + timedelta(days=ttl_days)

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO api_keys (
                key_id, key_hash, user_id, username, role,
                created_at, expires_at, description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                key_id,
                key_hash,
                user_id,
                username,
                role,
                now.isoformat(),
                expires_at.isoformat() if expires_at else None,
                description,
            ),
        )

        conn.commit()
        conn.close()

        return {
            "key_id": key_id,
            "api_key": api_key,  # Plain text - only returned once!
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
            "description": description,
        }

    def verify_key(self, api_key: str) -> Optional[Dict]:
        """
        Verify an API key and return user information if valid.

        Args:
            api_key: The API key to verify

        Returns:
            Dict with user info if valid, None if invalid/expired/revoked
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all non-revoked keys
        cursor.execute(
            """
            SELECT key_id, key_hash, user_id, username, role,
                   created_at, expires_at, last_used
            FROM api_keys
            WHERE revoked = 0
        """
        )

        rows = cursor.fetchall()

        for row in rows:
            (
                key_id,
                key_hash,
                user_id,
                username,
                role,
                created_at,
                expires_at,
                last_used,
            ) = row

            # Check if key matches hash
            if bcrypt.checkpw(api_key.encode(), key_hash.encode()):
                # Check expiration
                if expires_at:
                    if datetime.now() > datetime.fromisoformat(expires_at):
                        conn.close()
                        return None  # Expired

                # Update last_used timestamp
                now = datetime.now()
                cursor.execute(
                    "UPDATE api_keys SET last_used = ? WHERE key_id = ?",
                    (now.isoformat(), key_id),
                )
                conn.commit()
                conn.close()

                return {
                    "key_id": key_id,
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "last_used": now.isoformat(),
                }

        conn.close()
        return None  # No matching key found

    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: The key_id to revoke

        Returns:
            True if key was revoked, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE api_keys SET revoked = 1 WHERE key_id = ?", (key_id,)
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def list_keys(
        self, user_id: Optional[str] = None, include_revoked: bool = False
    ) -> List[Dict]:
        """
        List API keys.

        Args:
            user_id: Filter by user_id (None = all users)
            include_revoked: Include revoked keys

        Returns:
            List of key metadata (without hashes)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT key_id, user_id, username, role, created_at,
                   expires_at, last_used, revoked, description
            FROM api_keys
        """

        conditions = []
        params = []

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        if not include_revoked:
            conditions.append("revoked = 0")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        keys = []
        for row in rows:
            (
                key_id,
                user_id,
                username,
                role,
                created_at,
                expires_at,
                last_used,
                revoked,
                description,
            ) = row

            # Check if expired
            is_expired = False
            if expires_at:
                is_expired = datetime.now() > datetime.fromisoformat(expires_at)

            keys.append(
                {
                    "key_id": key_id,
                    "user_id": user_id,
                    "username": username,
                    "role": role,
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "last_used": last_used,
                    "revoked": bool(revoked),
                    "is_expired": is_expired,
                    "status": "revoked"
                    if revoked
                    else ("expired" if is_expired else "active"),
                    "description": description or "",
                }
            )

        return keys

    def get_key_info(self, key_id: str) -> Optional[Dict]:
        """Get information about a specific key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT key_id, user_id, username, role, created_at,
                   expires_at, last_used, revoked, description
            FROM api_keys
            WHERE key_id = ?
        """,
            (key_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None

        (
            key_id,
            user_id,
            username,
            role,
            created_at,
            expires_at,
            last_used,
            revoked,
            description,
        ) = row

        # Check if expired
        is_expired = False
        if expires_at:
            is_expired = datetime.now() > datetime.fromisoformat(expires_at)

        return {
            "key_id": key_id,
            "user_id": user_id,
            "username": username,
            "role": role,
            "created_at": created_at,
            "expires_at": expires_at,
            "last_used": last_used,
            "revoked": bool(revoked),
            "is_expired": is_expired,
            "status": "revoked"
            if revoked
            else ("expired" if is_expired else "active"),
            "description": description or "",
        }

    def delete_key(self, key_id: str) -> bool:
        """
        Permanently delete an API key from database.

        Args:
            key_id: The key_id to delete

        Returns:
            True if key was deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM api_keys WHERE key_id = ?", (key_id,))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def cleanup_expired(self) -> int:
        """
        Delete expired keys from database.

        Returns:
            Number of keys deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        cursor.execute(
            """
            DELETE FROM api_keys
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """,
            (now,),
        )

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected


# ══════════════════════════════════════════════════════════════════════
# Global Instance
# ══════════════════════════════════════════════════════════════════════


_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def set_api_key_manager(manager: APIKeyManager) -> None:
    """
    Set the global API key manager instance.

    This is primarily for testing purposes to inject a test database.
    """
    global _api_key_manager
    _api_key_manager = manager


# ══════════════════════════════════════════════════════════════════════
# Initialization Helper
# ══════════════════════════════════════════════════════════════════════


def create_default_admin_key() -> Optional[Dict]:
    """
    Create a default admin key if no keys exist.

    This is useful for initial setup.
    Returns the key info if created, None if keys already exist.
    """
    manager = get_api_key_manager()
    existing_keys = manager.list_keys()

    if existing_keys:
        return None  # Keys already exist

    # Create default admin key
    key_info = manager.generate_key(
        user_id="admin",
        username="admin",
        role="admin",
        ttl_days=0,  # No expiration
        description="Default admin key (created on first run)",
    )

    return key_info
