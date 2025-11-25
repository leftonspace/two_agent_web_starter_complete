"""
PHASE 4.1 HARDENING: Secrets Management

Provides secure secrets retrieval with support for multiple backends:
- Environment variables (development)
- HashiCorp Vault (production recommended)
- AWS Secrets Manager
- Azure Key Vault
- File-based encrypted secrets

Features:
- Backend abstraction for easy switching
- Automatic secret rotation support
- Caching with configurable TTL
- Audit logging of secret access
- Fallback chain (try Vault -> AWS -> env vars)

Usage:
    from agent.security.secrets import get_secret, SecretsManager

    # Simple usage (auto-selects backend)
    api_key = get_secret("OPENAI_API_KEY")

    # With specific backend
    manager = SecretsManager(backend="vault")
    api_key = manager.get("openai/api_key")

    # With fallback chain
    manager = SecretsManager(fallback_chain=["vault", "aws", "env"])
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agent.core_logging import log_event


class SecretBackend(Enum):
    """Available secret storage backends."""
    ENV = "env"                     # Environment variables (development)
    VAULT = "vault"                 # HashiCorp Vault
    AWS = "aws"                     # AWS Secrets Manager
    AZURE = "azure"                 # Azure Key Vault
    FILE = "file"                   # Encrypted file (for testing)


@dataclass
class SecretMetadata:
    """Metadata about a secret."""
    key: str
    backend: SecretBackend
    retrieved_at: float
    expires_at: Optional[float] = None
    version: Optional[str] = None
    rotation_due: Optional[float] = None


@dataclass
class CachedSecret:
    """Cached secret with TTL."""
    value: str
    metadata: SecretMetadata
    cached_at: float


# ============================================================================
# Secret Backend Implementations
# ============================================================================

class BaseSecretBackend(ABC):
    """Abstract base class for secret backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Get secret value by key."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available/configured."""
        pass

    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret (optional)."""
        return None


class EnvSecretBackend(BaseSecretBackend):
    """
    Environment variable backend (development).

    Simply reads from os.environ. No encryption, caching, or rotation.
    Suitable for development and testing only.
    """

    def get(self, key: str) -> Optional[str]:
        """Get secret from environment variable."""
        # Normalize key: OPENAI_API_KEY or openai/api_key -> OPENAI_API_KEY
        normalized_key = key.upper().replace("/", "_").replace("-", "_")
        return os.environ.get(normalized_key)

    def is_available(self) -> bool:
        """Environment backend is always available."""
        return True

    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        value = self.get(key)
        if value:
            return SecretMetadata(
                key=key,
                backend=SecretBackend.ENV,
                retrieved_at=time.time(),
            )
        return None


class VaultSecretBackend(BaseSecretBackend):
    """
    HashiCorp Vault backend (production recommended).

    Supports:
    - Token and AppRole authentication
    - KV v2 secrets engine
    - Secret rotation and leases
    - Namespace support

    Environment variables:
    - VAULT_ADDR: Vault server address
    - VAULT_TOKEN: Auth token (or use AppRole)
    - VAULT_ROLE_ID: AppRole role ID
    - VAULT_SECRET_ID: AppRole secret ID
    - VAULT_NAMESPACE: Optional namespace
    """

    def __init__(
        self,
        addr: Optional[str] = None,
        token: Optional[str] = None,
        role_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        namespace: Optional[str] = None,
        mount_path: str = "secret",
    ):
        self.addr = addr or os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.role_id = role_id or os.getenv("VAULT_ROLE_ID")
        self.secret_id = secret_id or os.getenv("VAULT_SECRET_ID")
        self.namespace = namespace or os.getenv("VAULT_NAMESPACE")
        self.mount_path = mount_path

        self._client = None
        self._authenticated = False

    def _get_client(self):
        """Get or create Vault client."""
        if self._client is None:
            try:
                import hvac
                self._client = hvac.Client(
                    url=self.addr,
                    token=self.token,
                    namespace=self.namespace,
                )

                # Authenticate with AppRole if token not provided
                if not self.token and self.role_id and self.secret_id:
                    auth_response = self._client.auth.approle.login(
                        role_id=self.role_id,
                        secret_id=self.secret_id,
                    )
                    self._client.token = auth_response["auth"]["client_token"]

                self._authenticated = self._client.is_authenticated()

            except ImportError:
                print("[Secrets] hvac not installed. Install with: pip install hvac")
                return None
            except Exception as e:
                print(f"[Secrets] Vault connection error: {e}")
                return None

        return self._client

    def get(self, key: str) -> Optional[str]:
        """Get secret from Vault KV v2."""
        client = self._get_client()
        if not client:
            return None

        try:
            # Parse key: can be "path/to/secret:field" or just "path/to/secret"
            if ":" in key:
                path, field = key.rsplit(":", 1)
            else:
                path = key
                field = "value"

            # Read from KV v2
            response = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_path,
            )

            data = response.get("data", {}).get("data", {})
            return data.get(field)

        except Exception as e:
            log_event("vault_secret_error", {"key": key, "error": str(e)})
            return None

    def is_available(self) -> bool:
        """Check if Vault is configured and reachable."""
        client = self._get_client()
        return client is not None and self._authenticated

    def get_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get Vault secret metadata including version."""
        client = self._get_client()
        if not client:
            return None

        try:
            if ":" in key:
                path, _ = key.rsplit(":", 1)
            else:
                path = key

            response = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_path,
            )

            metadata = response.get("data", {}).get("metadata", {})

            return SecretMetadata(
                key=key,
                backend=SecretBackend.VAULT,
                retrieved_at=time.time(),
                version=str(metadata.get("version", "unknown")),
            )

        except Exception:
            return None


class AWSSecretsBackend(BaseSecretBackend):
    """
    AWS Secrets Manager backend.

    Supports:
    - Automatic credential discovery (IAM roles, env vars, etc.)
    - Secret versioning
    - Automatic rotation

    Environment variables:
    - AWS_REGION: AWS region (default: us-east-1)
    - AWS_ACCESS_KEY_ID: Optional (prefer IAM roles)
    - AWS_SECRET_ACCESS_KEY: Optional (prefer IAM roles)
    """

    def __init__(
        self,
        region: Optional[str] = None,
        prefix: str = "jarvis/",
    ):
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.prefix = prefix
        self._client = None

    def _get_client(self):
        """Get or create AWS Secrets Manager client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "secretsmanager",
                    region_name=self.region,
                )
            except ImportError:
                print("[Secrets] boto3 not installed. Install with: pip install boto3")
                return None
            except Exception as e:
                print(f"[Secrets] AWS connection error: {e}")
                return None

        return self._client

    def get(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        client = self._get_client()
        if not client:
            return None

        try:
            # Normalize key and add prefix
            secret_name = self.prefix + key.replace("_", "/").lower()

            response = client.get_secret_value(SecretId=secret_name)

            # Handle string or JSON secrets
            if "SecretString" in response:
                secret = response["SecretString"]
                try:
                    # Try to parse as JSON
                    data = json.loads(secret)
                    # Return first value or 'value' key
                    return data.get("value", list(data.values())[0] if data else None)
                except json.JSONDecodeError:
                    return secret

            return None

        except Exception as e:
            log_event("aws_secret_error", {"key": key, "error": str(e)})
            return None

    def is_available(self) -> bool:
        """Check if AWS Secrets Manager is available."""
        client = self._get_client()
        if not client:
            return False

        try:
            # Try a simple list operation to verify credentials
            client.list_secrets(MaxResults=1)
            return True
        except Exception:
            return False


class AzureKeyVaultBackend(BaseSecretBackend):
    """
    Azure Key Vault backend.

    Supports:
    - DefaultAzureCredential (managed identity, CLI, env vars)
    - Secret versioning

    Environment variables:
    - AZURE_KEY_VAULT_URL: Key Vault URL (https://<vault>.vault.azure.net/)
    - AZURE_TENANT_ID: Azure AD tenant
    - AZURE_CLIENT_ID: App registration client ID
    - AZURE_CLIENT_SECRET: App registration secret
    """

    def __init__(
        self,
        vault_url: Optional[str] = None,
    ):
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        self._client = None

    def _get_client(self):
        """Get or create Azure Key Vault client."""
        if self._client is None and self.vault_url:
            try:
                from azure.identity import DefaultAzureCredential
                from azure.keyvault.secrets import SecretClient

                credential = DefaultAzureCredential()
                self._client = SecretClient(
                    vault_url=self.vault_url,
                    credential=credential,
                )
            except ImportError:
                print("[Secrets] Azure SDK not installed. Install with: pip install azure-keyvault-secrets azure-identity")
                return None
            except Exception as e:
                print(f"[Secrets] Azure connection error: {e}")
                return None

        return self._client

    def get(self, key: str) -> Optional[str]:
        """Get secret from Azure Key Vault."""
        client = self._get_client()
        if not client:
            return None

        try:
            # Normalize key: OPENAI_API_KEY -> openai-api-key (Azure naming convention)
            secret_name = key.lower().replace("_", "-").replace("/", "-")

            secret = client.get_secret(secret_name)
            return secret.value

        except Exception as e:
            log_event("azure_secret_error", {"key": key, "error": str(e)})
            return None

    def is_available(self) -> bool:
        """Check if Azure Key Vault is available."""
        return self._get_client() is not None


class FileSecretBackend(BaseSecretBackend):
    """
    File-based secrets backend (for testing/development).

    Reads secrets from an encrypted JSON file.
    Uses simple Fernet encryption for the file.

    NOT recommended for production - use Vault or cloud provider.
    """

    def __init__(
        self,
        secrets_file: Optional[str] = None,
        encryption_key: Optional[str] = None,
    ):
        self.secrets_file = Path(secrets_file or os.getenv(
            "JARVIS_SECRETS_FILE",
            str(Path.home() / ".jarvis" / "secrets.json.enc")
        ))
        self.encryption_key = encryption_key or os.getenv("JARVIS_SECRETS_KEY")
        self._secrets: Optional[Dict[str, str]] = None

    def _load_secrets(self) -> Dict[str, str]:
        """Load and decrypt secrets file."""
        if self._secrets is not None:
            return self._secrets

        if not self.secrets_file.exists():
            return {}

        try:
            encrypted_data = self.secrets_file.read_bytes()

            if self.encryption_key:
                from cryptography.fernet import Fernet
                fernet = Fernet(self.encryption_key.encode())
                decrypted = fernet.decrypt(encrypted_data)
                self._secrets = json.loads(decrypted)
            else:
                # Unencrypted fallback (not recommended)
                self._secrets = json.loads(encrypted_data)

            return self._secrets

        except Exception as e:
            print(f"[Secrets] Error loading secrets file: {e}")
            return {}

    def get(self, key: str) -> Optional[str]:
        """Get secret from file."""
        secrets = self._load_secrets()
        normalized_key = key.upper().replace("/", "_").replace("-", "_")
        return secrets.get(normalized_key)

    def is_available(self) -> bool:
        """Check if secrets file exists."""
        return self.secrets_file.exists()


# ============================================================================
# Secrets Manager
# ============================================================================

# Backend registry
BACKEND_CLASSES: Dict[SecretBackend, type] = {
    SecretBackend.ENV: EnvSecretBackend,
    SecretBackend.VAULT: VaultSecretBackend,
    SecretBackend.AWS: AWSSecretsBackend,
    SecretBackend.AZURE: AzureKeyVaultBackend,
    SecretBackend.FILE: FileSecretBackend,
}


class SecretsManager:
    """
    Unified secrets management with backend abstraction.

    Supports:
    - Multiple backend types (Vault, AWS, Azure, env)
    - Fallback chains (try Vault, then AWS, then env)
    - Local caching with TTL
    - Audit logging
    - Secret rotation monitoring
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        fallback_chain: Optional[List[str]] = None,
        cache_ttl_seconds: int = 300,
        audit_logging: bool = True,
    ):
        """
        Initialize secrets manager.

        Args:
            backend: Primary backend ("vault", "aws", "azure", "env", "file")
            fallback_chain: List of backends to try in order
            cache_ttl_seconds: How long to cache secrets (default 5 minutes)
            audit_logging: Whether to log secret access
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self.audit_logging = audit_logging

        # Setup fallback chain
        if fallback_chain:
            self.backend_chain = [SecretBackend(b) for b in fallback_chain]
        elif backend:
            self.backend_chain = [SecretBackend(backend)]
        else:
            # Default chain: vault -> aws -> azure -> env
            self.backend_chain = self._detect_available_backends()

        # Initialize backends
        self._backends: Dict[SecretBackend, BaseSecretBackend] = {}
        for backend_type in self.backend_chain:
            self._backends[backend_type] = BACKEND_CLASSES[backend_type]()

        # Cache
        self._cache: Dict[str, CachedSecret] = {}
        self._cache_lock = threading.Lock()

        # Statistics
        self.total_requests = 0
        self.cache_hits = 0
        self.backend_hits: Dict[SecretBackend, int] = {b: 0 for b in SecretBackend}

    def _detect_available_backends(self) -> List[SecretBackend]:
        """Detect available backends based on configuration."""
        chain = []

        # Check Vault
        if os.getenv("VAULT_ADDR"):
            chain.append(SecretBackend.VAULT)

        # Check AWS
        if os.getenv("AWS_REGION") or os.getenv("AWS_ACCESS_KEY_ID"):
            chain.append(SecretBackend.AWS)

        # Check Azure
        if os.getenv("AZURE_KEY_VAULT_URL"):
            chain.append(SecretBackend.AZURE)

        # Check file
        secrets_file = Path(os.getenv(
            "JARVIS_SECRETS_FILE",
            str(Path.home() / ".jarvis" / "secrets.json.enc")
        ))
        if secrets_file.exists():
            chain.append(SecretBackend.FILE)

        # Always fall back to env
        chain.append(SecretBackend.ENV)

        return chain

    def get(
        self,
        key: str,
        default: Optional[str] = None,
        bypass_cache: bool = False,
    ) -> Optional[str]:
        """
        Get secret value.

        Tries backends in order until one succeeds.

        Args:
            key: Secret key (e.g., "OPENAI_API_KEY" or "openai/api_key")
            default: Default value if not found
            bypass_cache: Skip cache lookup

        Returns:
            Secret value or default
        """
        self.total_requests += 1

        # Check cache first
        if not bypass_cache:
            cached = self._get_from_cache(key)
            if cached is not None:
                self.cache_hits += 1
                return cached

        # Try backends in order
        for backend_type in self.backend_chain:
            backend = self._backends.get(backend_type)
            if not backend or not backend.is_available():
                continue

            value = backend.get(key)
            if value is not None:
                self.backend_hits[backend_type] += 1

                # Cache the result
                metadata = backend.get_metadata(key) or SecretMetadata(
                    key=key,
                    backend=backend_type,
                    retrieved_at=time.time(),
                )
                self._cache_secret(key, value, metadata)

                # Audit log
                if self.audit_logging:
                    log_event("secret_accessed", {
                        "key": key,
                        "backend": backend_type.value,
                        "cached": False,
                    })

                return value

        # Not found in any backend
        if self.audit_logging:
            log_event("secret_not_found", {"key": key})

        return default

    def _get_from_cache(self, key: str) -> Optional[str]:
        """Get secret from cache if not expired."""
        with self._cache_lock:
            cached = self._cache.get(key)
            if cached is None:
                return None

            # Check TTL
            age = time.time() - cached.cached_at
            if age > self.cache_ttl_seconds:
                del self._cache[key]
                return None

            return cached.value

    def _cache_secret(
        self,
        key: str,
        value: str,
        metadata: SecretMetadata,
    ) -> None:
        """Add secret to cache."""
        with self._cache_lock:
            self._cache[key] = CachedSecret(
                value=value,
                metadata=metadata,
                cached_at=time.time(),
            )

    def clear_cache(self, key: Optional[str] = None) -> None:
        """Clear cache (all or specific key)."""
        with self._cache_lock:
            if key:
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / max(self.total_requests, 1),
            "backend_hits": {k.value: v for k, v in self.backend_hits.items()},
            "active_backends": [b.value for b in self.backend_chain],
            "cache_size": len(self._cache),
        }


# ============================================================================
# Global Instance and Convenience Functions
# ============================================================================

_default_manager: Optional[SecretsManager] = None
_manager_lock = threading.Lock()


def get_secrets_manager() -> SecretsManager:
    """Get or create the default secrets manager."""
    global _default_manager

    with _manager_lock:
        if _default_manager is None:
            _default_manager = SecretsManager()

    return _default_manager


def configure_secrets(
    backend: Optional[str] = None,
    fallback_chain: Optional[List[str]] = None,
    cache_ttl_seconds: int = 300,
) -> SecretsManager:
    """
    Configure the default secrets manager.

    Args:
        backend: Primary backend
        fallback_chain: Fallback chain
        cache_ttl_seconds: Cache TTL

    Returns:
        Configured SecretsManager
    """
    global _default_manager

    with _manager_lock:
        _default_manager = SecretsManager(
            backend=backend,
            fallback_chain=fallback_chain,
            cache_ttl_seconds=cache_ttl_seconds,
        )

    return _default_manager


def get_secret(
    key: str,
    default: Optional[str] = None,
    bypass_cache: bool = False,
) -> Optional[str]:
    """
    Get a secret value.

    Convenience function using the default secrets manager.

    Args:
        key: Secret key
        default: Default value if not found
        bypass_cache: Skip cache lookup

    Returns:
        Secret value or default

    Example:
        api_key = get_secret("OPENAI_API_KEY")
        db_url = get_secret("DATABASE_URL", "sqlite:///default.db")
    """
    return get_secrets_manager().get(key, default, bypass_cache)


def require_secret(key: str) -> str:
    """
    Get a required secret (raises if not found).

    Args:
        key: Secret key

    Returns:
        Secret value

    Raises:
        ValueError: If secret not found
    """
    value = get_secret(key)
    if value is None:
        raise ValueError(f"Required secret not found: {key}")
    return value
