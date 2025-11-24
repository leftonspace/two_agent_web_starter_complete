"""
Webhook Security

OAuth2 and HMAC signature verification for webhooks.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

class SignatureAlgorithm(Enum):
    """Supported signature algorithms"""
    HMAC_SHA256 = "hmac-sha256"
    HMAC_SHA512 = "hmac-sha512"
    JWT_HS256 = "jwt-hs256"
    JWT_RS256 = "jwt-rs256"


@dataclass
class SecurityConfig:
    """Security configuration for webhooks"""
    algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256
    secret: Optional[str] = None
    public_key: Optional[str] = None  # For JWT RS256
    tolerance_seconds: int = 300  # 5 minutes
    require_timestamp: bool = True


# =============================================================================
# Base Verifier
# =============================================================================

class SignatureVerifier(ABC):
    """Base class for signature verifiers"""

    @abstractmethod
    def verify(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Signature to verify
            timestamp: Optional timestamp for replay protection

        Returns:
            True if signature is valid
        """
        pass


# =============================================================================
# HMAC Verifier
# =============================================================================

class HMACVerifier(SignatureVerifier):
    """
    HMAC signature verifier.

    Supports:
    - HMAC-SHA256
    - HMAC-SHA512
    - Timestamp-based replay protection

    Usage:
        verifier = HMACVerifier(secret="your-secret-key")

        is_valid = verifier.verify(
            payload=request.body,
            signature=request.headers["X-Webhook-Signature"],
            timestamp=request.headers["X-Webhook-Timestamp"]
        )
    """

    def __init__(
        self,
        secret: str,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.HMAC_SHA256,
        tolerance_seconds: int = 300,
    ):
        """
        Initialize HMAC verifier.

        Args:
            secret: Shared secret key
            algorithm: HMAC algorithm to use
            tolerance_seconds: Maximum age of timestamp
        """
        self.secret = secret.encode() if isinstance(secret, str) else secret
        self.algorithm = algorithm
        self.tolerance_seconds = tolerance_seconds

        # Select hash function
        if algorithm == SignatureAlgorithm.HMAC_SHA256:
            self.hash_func = hashlib.sha256
        elif algorithm == SignatureAlgorithm.HMAC_SHA512:
            self.hash_func = hashlib.sha512
        else:
            raise ValueError(f"Unsupported HMAC algorithm: {algorithm}")

    def compute_signature(
        self,
        payload: bytes,
        timestamp: Optional[str] = None,
    ) -> str:
        """
        Compute HMAC signature.

        Args:
            payload: Raw payload bytes
            timestamp: Optional timestamp

        Returns:
            Hex-encoded signature
        """
        # Include timestamp in signature if provided
        if timestamp:
            message = timestamp.encode() + b"." + payload
        else:
            message = payload

        signature = hmac.new(
            self.secret,
            message,
            self.hash_func
        ).hexdigest()

        return signature

    def verify(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify HMAC signature.

        Args:
            payload: Raw webhook payload
            signature: Signature to verify
            timestamp: Optional timestamp for replay protection

        Returns:
            True if signature is valid
        """
        # Verify timestamp if provided
        if timestamp:
            try:
                ts = int(timestamp)
                now = int(time.time())

                if abs(now - ts) > self.tolerance_seconds:
                    print(f"[WebhookSecurity] Timestamp outside tolerance: {abs(now - ts)}s")
                    return False
            except ValueError:
                print(f"[WebhookSecurity] Invalid timestamp format: {timestamp}")
                return False

        # Compute expected signature
        expected = self.compute_signature(payload, timestamp)

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected)


# =============================================================================
# OAuth2/JWT Verifier
# =============================================================================

class OAuth2Verifier(SignatureVerifier):
    """
    OAuth2 JWT token verifier.

    Supports:
    - JWT with HS256 (symmetric key)
    - JWT with RS256 (public key)
    - Standard OAuth2 claims validation

    Usage:
        verifier = OAuth2Verifier(
            secret="your-secret",
            audience="https://api.jarvis.ai"
        )

        is_valid = verifier.verify(
            payload=request.body,
            signature=request.headers["Authorization"],
        )
    """

    def __init__(
        self,
        secret: Optional[str] = None,
        public_key: Optional[str] = None,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.JWT_HS256,
        audience: Optional[str] = None,
        issuer: Optional[str] = None,
        tolerance_seconds: int = 300,
    ):
        """
        Initialize OAuth2 verifier.

        Args:
            secret: Shared secret (for HS256)
            public_key: Public key (for RS256)
            algorithm: JWT algorithm
            audience: Expected audience claim
            issuer: Expected issuer claim
            tolerance_seconds: Clock skew tolerance
        """
        if not JWT_AVAILABLE:
            raise ImportError(
                "PyJWT is required for OAuth2 verification. "
                "Install with: pip install pyjwt"
            )

        self.secret = secret
        self.public_key = public_key
        self.algorithm = algorithm
        self.audience = audience
        self.issuer = issuer
        self.tolerance_seconds = tolerance_seconds

        # Determine JWT algorithm
        if algorithm == SignatureAlgorithm.JWT_HS256:
            self.jwt_algorithm = "HS256"
            if not secret:
                raise ValueError("Secret required for HS256")
        elif algorithm == SignatureAlgorithm.JWT_RS256:
            self.jwt_algorithm = "RS256"
            if not public_key:
                raise ValueError("Public key required for RS256")
        else:
            raise ValueError(f"Unsupported JWT algorithm: {algorithm}")

    def verify(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify OAuth2 JWT token.

        Args:
            payload: Raw webhook payload (not used for JWT)
            signature: JWT token (from Authorization header)
            timestamp: Not used for JWT

        Returns:
            True if token is valid
        """
        # Extract token from "Bearer <token>" format
        token = signature
        if token.startswith("Bearer "):
            token = token[7:]

        try:
            # Select key for verification
            key = self.secret if self.jwt_algorithm == "HS256" else self.public_key

            # Decode and verify token
            claims = jwt.decode(
                token,
                key,
                algorithms=[self.jwt_algorithm],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": self.audience is not None,
                    "verify_iss": self.issuer is not None,
                },
                leeway=self.tolerance_seconds,
            )

            print(f"[WebhookSecurity] Valid JWT token: {claims.get('sub', 'unknown')}")
            return True

        except jwt.ExpiredSignatureError:
            print(f"[WebhookSecurity] JWT token expired")
            return False
        except jwt.InvalidAudienceError:
            print(f"[WebhookSecurity] JWT audience mismatch")
            return False
        except jwt.InvalidIssuerError:
            print(f"[WebhookSecurity] JWT issuer mismatch")
            return False
        except jwt.InvalidTokenError as e:
            print(f"[WebhookSecurity] Invalid JWT token: {e}")
            return False
        except Exception as e:
            print(f"[WebhookSecurity] JWT verification error: {e}")
            return False


# =============================================================================
# Webhook Security Manager
# =============================================================================

class WebhookSecurity:
    """
    Webhook security manager.

    Handles signature verification with multiple algorithms.

    Usage:
        security = WebhookSecurity.from_config({
            "algorithm": "hmac-sha256",
            "secret": "your-secret-key",
        })

        if security.verify_request(request):
            process_webhook(request)
        else:
            return 401
    """

    def __init__(self, verifier: SignatureVerifier):
        """
        Initialize security manager.

        Args:
            verifier: Signature verifier to use
        """
        self.verifier = verifier

    @classmethod
    def from_config(cls, config: Dict) -> WebhookSecurity:
        """
        Create security manager from configuration.

        Args:
            config: Security configuration dict

        Returns:
            Configured WebhookSecurity
        """
        algorithm = SignatureAlgorithm(config.get("algorithm", "hmac-sha256"))

        if algorithm in [SignatureAlgorithm.HMAC_SHA256, SignatureAlgorithm.HMAC_SHA512]:
            verifier = HMACVerifier(
                secret=config["secret"],
                algorithm=algorithm,
                tolerance_seconds=config.get("tolerance_seconds", 300),
            )
        elif algorithm in [SignatureAlgorithm.JWT_HS256, SignatureAlgorithm.JWT_RS256]:
            verifier = OAuth2Verifier(
                secret=config.get("secret"),
                public_key=config.get("public_key"),
                algorithm=algorithm,
                audience=config.get("audience"),
                issuer=config.get("issuer"),
                tolerance_seconds=config.get("tolerance_seconds", 300),
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        return cls(verifier)

    def verify_request(
        self,
        payload: bytes,
        signature: str,
        timestamp: Optional[str] = None,
    ) -> bool:
        """
        Verify webhook request.

        Args:
            payload: Raw request body
            signature: Signature from header
            timestamp: Optional timestamp from header

        Returns:
            True if request is authentic
        """
        return self.verifier.verify(payload, signature, timestamp)


# =============================================================================
# Utility Functions
# =============================================================================

def generate_webhook_secret(length: int = 32) -> str:
    """Generate a random webhook secret"""
    import secrets
    return secrets.token_urlsafe(length)


def create_hmac_verifier(secret: str) -> HMACVerifier:
    """Quick helper to create HMAC verifier"""
    return HMACVerifier(secret=secret)


def create_oauth2_verifier(
    secret: Optional[str] = None,
    public_key: Optional[str] = None,
) -> OAuth2Verifier:
    """Quick helper to create OAuth2 verifier"""
    if secret:
        return OAuth2Verifier(secret=secret, algorithm=SignatureAlgorithm.JWT_HS256)
    elif public_key:
        return OAuth2Verifier(public_key=public_key, algorithm=SignatureAlgorithm.JWT_RS256)
    else:
        raise ValueError("Either secret or public_key required")
