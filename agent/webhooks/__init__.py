"""
JARVIS Webhook System

Production-grade webhook receiver with:
- OAuth2 and HMAC signature verification
- Automatic retry logic with exponential backoff
- Failure notifications
- Webhook routing and transformation
- Idempotency handling
"""

from .server import (
    WebhookServer,
    WebhookConfig,
    create_webhook_server,
)

from .handler import (
    WebhookHandler,
    WebhookEvent,
    WebhookResponse,
)

from .security import (
    WebhookSecurity,
    SignatureVerifier,
    OAuth2Verifier,
)

from .retry import (
    WebhookRetryManager,
    RetryPolicy,
)

__all__ = [
    "WebhookServer",
    "WebhookConfig",
    "create_webhook_server",
    "WebhookHandler",
    "WebhookEvent",
    "WebhookResponse",
    "WebhookSecurity",
    "SignatureVerifier",
    "OAuth2Verifier",
    "WebhookRetryManager",
    "RetryPolicy",
]

__version__ = "1.0.0"
