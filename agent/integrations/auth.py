"""
OAuth2 Authentication and Credential Management

This module handles:
- OAuth2 flow (authorization code, client credentials, refresh token)
- Credential encryption and storage
- Token refresh and expiration
- Secure credential management

Author: AI Agent System
Created: Phase 3.2 - Integration Framework
"""

import base64
import hashlib
import json
import os
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
from urllib.parse import urlencode, parse_qs, urlparse
import aiohttp
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CREDENTIAL ENCRYPTION
# ============================================================================

class CredentialEncryption:
    """
    Handles encryption/decryption of credentials using Fernet (AES-128).

    Uses a master key derived from environment variable or generated key file.
    """

    def __init__(self, master_key: Optional[str] = None):
        if master_key:
            # Use provided master key
            key_bytes = master_key.encode()
        else:
            # Get from environment or generate
            key_bytes = self._get_or_create_master_key()

        # Derive Fernet key from master key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'integration_salt',  # In production, use unique salt per installation
            iterations=100000
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
        self.cipher = Fernet(derived_key)

    def _get_or_create_master_key(self) -> bytes:
        """Get master key from environment or create one"""
        # Check environment variable
        env_key = os.environ.get('INTEGRATION_MASTER_KEY')
        if env_key:
            return env_key.encode()

        # Check key file
        key_file = Path('data/.integration_key')
        if key_file.exists():
            return key_file.read_bytes()

        # Generate new key
        logger.warning("No master key found, generating new one")
        new_key = Fernet.generate_key()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_bytes(new_key)
        key_file.chmod(0o600)  # Read/write for owner only
        logger.info(f"Master key saved to {key_file}")
        return new_key

    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()


# Global encryption instance
_encryption = None


def get_encryption() -> CredentialEncryption:
    """Get the global encryption instance"""
    global _encryption
    if _encryption is None:
        _encryption = CredentialEncryption()
    return _encryption


# ============================================================================
# CREDENTIAL STORAGE
# ============================================================================

@dataclass
class Credential:
    """Stored credential"""
    connector_id: str
    auth_type: str  # api_key, oauth2, basic, token
    credentials: Dict[str, str]  # Encrypted credential data
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class CredentialStore:
    """
    Manages secure storage of credentials.

    Credentials are encrypted and stored in data/integrations.json
    """

    def __init__(self, storage_path: str = "data/integrations.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption = get_encryption()
        self._ensure_file()

    def _ensure_file(self):
        """Ensure storage file exists"""
        if not self.storage_path.exists():
            self._save_data({})

    def _load_data(self) -> Dict:
        """Load data from file"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_data(self, data: Dict):
        """Save data to file"""
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
        self.storage_path.chmod(0o600)  # Secure permissions

    def store(self, credential: Credential):
        """Store a credential (encrypted)"""
        data = self._load_data()

        # Encrypt sensitive fields
        encrypted_creds = {}
        for key, value in credential.credentials.items():
            encrypted_creds[key] = self.encryption.encrypt(value)

        credential.credentials = encrypted_creds
        credential.updated_at = datetime.utcnow().isoformat()

        data[credential.connector_id] = credential.to_dict()
        self._save_data(data)
        logger.info(f"Stored credentials for connector: {credential.connector_id}")

    def get(self, connector_id: str) -> Optional[Credential]:
        """Get and decrypt a credential"""
        data = self._load_data()

        if connector_id not in data:
            return None

        cred_data = data[connector_id]

        # Decrypt credentials
        decrypted_creds = {}
        for key, encrypted_value in cred_data['credentials'].items():
            try:
                decrypted_creds[key] = self.encryption.decrypt(encrypted_value)
            except Exception as e:
                logger.error(f"Failed to decrypt credential {key}: {e}")
                decrypted_creds[key] = None

        cred_data['credentials'] = decrypted_creds
        return Credential(**cred_data)

    def delete(self, connector_id: str) -> bool:
        """Delete a credential"""
        data = self._load_data()

        if connector_id in data:
            del data[connector_id]
            self._save_data(data)
            logger.info(f"Deleted credentials for connector: {connector_id}")
            return True

        return False

    def list_all(self) -> Dict[str, Dict]:
        """List all stored credentials (without decrypting)"""
        data = self._load_data()
        return {
            k: {
                'connector_id': v['connector_id'],
                'auth_type': v['auth_type'],
                'created_at': v['created_at'],
                'updated_at': v['updated_at']
            }
            for k, v in data.items()
        }


# ============================================================================
# OAUTH2 CLIENT
# ============================================================================

@dataclass
class OAuth2Config:
    """OAuth2 configuration"""
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None


@dataclass
class OAuth2Token:
    """OAuth2 token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.expires_in and not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(seconds=self.expires_in)

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'access_token': self.access_token,
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'refresh_token': self.refresh_token,
            'scope': self.scope,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class OAuth2Client:
    """
    OAuth2 client for handling authorization flows.

    Supports:
    - Authorization Code Flow
    - Client Credentials Flow
    - Refresh Token Flow
    """

    def __init__(self, config: OAuth2Config):
        self.config = config
        self.token: Optional[OAuth2Token] = None

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get authorization URL for user consent.

        Args:
            state: CSRF token (generated if not provided)

        Returns:
            Authorization URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
            self.config.state = state

        params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'response_type': 'code',
            'state': state
        }

        if self.config.scope:
            params['scope'] = self.config.scope

        return f"{self.config.authorization_url}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuth2Token:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from callback

        Returns:
            OAuth2 token
        """
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.config.redirect_uri,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }

            async with session.post(self.config.token_url, data=data) as resp:
                resp.raise_for_status()
                token_data = await resp.json()

                self.token = OAuth2Token(**token_data)
                logger.info("OAuth2 token obtained successfully")
                return self.token

    async def client_credentials(self) -> OAuth2Token:
        """
        Obtain token using client credentials flow.

        Returns:
            OAuth2 token
        """
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }

            if self.config.scope:
                data['scope'] = self.config.scope

            async with session.post(self.config.token_url, data=data) as resp:
                resp.raise_for_status()
                token_data = await resp.json()

                self.token = OAuth2Token(**token_data)
                logger.info("OAuth2 client credentials token obtained")
                return self.token

    async def refresh_token(self, refresh_token: Optional[str] = None) -> OAuth2Token:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token (uses stored token if not provided)

        Returns:
            New OAuth2 token
        """
        if not refresh_token:
            if not self.token or not self.token.refresh_token:
                raise ValueError("No refresh token available")
            refresh_token = self.token.refresh_token

        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }

            async with session.post(self.config.token_url, data=data) as resp:
                resp.raise_for_status()
                token_data = await resp.json()

                self.token = OAuth2Token(**token_data)
                logger.info("OAuth2 token refreshed successfully")
                return self.token

    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token, refreshing if needed.

        Returns:
            Valid access token
        """
        if not self.token:
            raise ValueError("No token available. Please authenticate first.")

        if self.token.is_expired():
            if self.token.refresh_token:
                await self.refresh_token()
            else:
                raise ValueError("Token expired and no refresh token available")

        return self.token.access_token

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header"""
        if not self.token:
            raise ValueError("No token available")

        return {
            'Authorization': f"{self.token.token_type} {self.token.access_token}"
        }


# ============================================================================
# API KEY MANAGER
# ============================================================================

class APIKeyManager:
    """
    Simple API key management.

    For services that use API keys instead of OAuth2.
    """

    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header"""
        return {self.header_name: self.api_key}


# ============================================================================
# BASIC AUTH MANAGER
# ============================================================================

class BasicAuthManager:
    """
    HTTP Basic Authentication manager.
    """

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def get_auth_header(self) -> Dict[str, str]:
        """Get authorization header"""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {encoded}'}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_credential(
    connector_id: str,
    auth_type: str,
    credentials: Dict[str, str],
    metadata: Optional[Dict] = None
) -> Credential:
    """
    Create a new credential.

    Args:
        connector_id: ID of the connector
        auth_type: Type of authentication
        credentials: Credential data (will be encrypted)
        metadata: Optional metadata

    Returns:
        Credential object
    """
    now = datetime.utcnow().isoformat()
    return Credential(
        connector_id=connector_id,
        auth_type=auth_type,
        credentials=credentials,
        created_at=now,
        updated_at=now,
        metadata=metadata
    )


# Global credential store
_store = None


def get_credential_store() -> CredentialStore:
    """Get the global credential store"""
    global _store
    if _store is None:
        _store = CredentialStore()
    return _store
