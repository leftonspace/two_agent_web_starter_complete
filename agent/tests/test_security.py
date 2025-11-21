"""
PHASE 11.3: Security Tests

Tests for authentication, authorization, rate limiting, and audit logging.
"""

import asyncio
import hashlib
import time
import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.auth import (
    AuthManager,
    User,
    Role,
    Permission,
    APIKey,
    OAuthProvider,
    OAuthCredentials,
    AuthenticationError,
    AuthorizationError,
    ROLE_PERMISSIONS,
)
from security.rate_limit import (
    RateLimiter,
    RateLimitExceeded,
    TokenBucket,
    SlidingWindowRateLimiter,
)
from security.audit_log import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    get_audit_logger,
)


# ============================================================================
# Rate Limiting Tests
# ============================================================================

def test_token_bucket_initialization():
    """Test token bucket initialization."""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)

    assert bucket.capacity == 10
    assert bucket.refill_rate == 1.0
    assert bucket.tokens == 10.0


def test_token_bucket_consume():
    """Test consuming tokens."""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)

    # Consume 3 tokens
    assert bucket.consume(3) is True
    assert bucket.get_remaining() == 7

    # Consume 7 more
    assert bucket.consume(7) is True
    assert bucket.get_remaining() == 0

    # Try to consume when empty
    assert bucket.consume(1) is False


def test_token_bucket_refill():
    """Test token refill."""
    bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/sec

    # Consume all tokens
    bucket.consume(10)
    assert bucket.get_remaining() == 0

    # Wait for refill
    time.sleep(0.5)  # Should refill 5 tokens

    remaining = bucket.get_remaining()
    assert 4 <= remaining <= 6  # Allow some variance


def test_token_bucket_time_until_available():
    """Test calculating time until tokens available."""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)

    # Consume all tokens
    bucket.consume(10)

    # Need 1 token, should take ~1 second
    time_needed = bucket.time_until_available(1)
    assert 0.9 <= time_needed <= 1.1


@pytest.mark.asyncio
async def test_rate_limiter_allow():
    """Test rate limiter allows requests."""
    limiter = RateLimiter(max_requests=10, window=60.0)

    # Should allow first 10 requests
    for i in range(10):
        assert await limiter.allow("user1") is True

    # Should deny 11th request
    assert await limiter.allow("user1") is False


@pytest.mark.asyncio
async def test_rate_limiter_per_identifier():
    """Test rate limiter is per-identifier."""
    limiter = RateLimiter(max_requests=5, window=60.0)

    # User 1 makes 5 requests
    for i in range(5):
        assert await limiter.allow("user1") is True

    # User 1 is rate limited
    assert await limiter.allow("user1") is False

    # User 2 can still make requests
    assert await limiter.allow("user2") is True


@pytest.mark.asyncio
async def test_rate_limiter_raise():
    """Test rate limiter raises exception."""
    limiter = RateLimiter(max_requests=2, window=60.0)

    # First 2 requests succeed
    await limiter.allow_or_raise("user1")
    await limiter.allow_or_raise("user1")

    # 3rd request raises
    with pytest.raises(RateLimitExceeded) as exc_info:
        await limiter.allow_or_raise("user1")

    assert exc_info.value.retry_after > 0


def test_rate_limiter_get_remaining():
    """Test getting remaining requests."""
    limiter = RateLimiter(max_requests=10, window=60.0)

    assert limiter.get_remaining("user1") == 10


def test_rate_limiter_reset():
    """Test resetting rate limits."""
    limiter = RateLimiter(max_requests=5, window=60.0)

    # Consume some tokens
    asyncio.run(limiter.allow("user1"))
    asyncio.run(limiter.allow("user1"))

    assert limiter.get_remaining("user1") < 5

    # Reset
    limiter.reset("user1")

    assert limiter.get_remaining("user1") == 5


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    """Test sliding window rate limiter."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window=1.0)

    # Allow first 3 requests
    assert await limiter.allow("user1") is True
    assert await limiter.allow("user1") is True
    assert await limiter.allow("user1") is True

    # Deny 4th
    assert await limiter.allow("user1") is False

    # Wait for window to pass
    time.sleep(1.1)

    # Should allow again
    assert await limiter.allow("user1") is True


# ============================================================================
# Audit Logging Tests
# ============================================================================

@pytest.mark.asyncio
async def test_audit_event_creation():
    """Test creating audit events."""
    event = AuditEvent(
        event_type=AuditEventType.AUTH_SUCCESS,
        severity=AuditSeverity.INFO,
        message="User logged in",
        user_id="user123",
    )

    assert event.event_type == AuditEventType.AUTH_SUCCESS
    assert event.severity == AuditSeverity.INFO
    assert event.message == "User logged in"
    assert event.user_id == "user123"


@pytest.mark.asyncio
async def test_audit_event_to_dict():
    """Test converting audit event to dict."""
    event = AuditEvent(
        event_type=AuditEventType.AUTH_SUCCESS,
        severity=AuditSeverity.INFO,
        message="Test",
    )

    data = event.to_dict()

    assert data["event_type"] == "auth_success"
    assert data["severity"] == "info"
    assert data["message"] == "Test"
    assert "timestamp_iso" in data


@pytest.mark.asyncio
async def test_audit_logger_log():
    """Test logging audit events."""
    logger = AuditLogger()

    await logger.log(
        AuditEventType.AUTH_SUCCESS,
        "User logged in",
        user_id="user123",
    )

    assert len(logger.events) == 1
    assert logger.total_events == 1


@pytest.mark.asyncio
async def test_audit_logger_search():
    """Test searching audit events."""
    logger = AuditLogger()

    # Log different events
    await logger.log(AuditEventType.AUTH_SUCCESS, "Login 1", user_id="user1")
    await logger.log(AuditEventType.AUTH_FAILURE, "Login failed", user_id="user2")
    await logger.log(AuditEventType.AUTH_SUCCESS, "Login 2", user_id="user1")

    # Search by event type
    successes = logger.search(event_type=AuditEventType.AUTH_SUCCESS)
    assert len(successes) == 2

    # Search by user
    user1_events = logger.search(user_id="user1")
    assert len(user1_events) == 2


@pytest.mark.asyncio
async def test_audit_logger_severity_filtering():
    """Test filtering by severity."""
    logger = AuditLogger()

    await logger.log(
        AuditEventType.AUTH_SUCCESS,
        "Success",
        severity=AuditSeverity.INFO,
    )
    await logger.log(
        AuditEventType.AUTH_FAILURE,
        "Failure",
        severity=AuditSeverity.WARNING,
    )

    warnings = logger.search(severity=AuditSeverity.WARNING)
    assert len(warnings) == 1


@pytest.mark.asyncio
async def test_audit_logger_time_range():
    """Test filtering by time range."""
    logger = AuditLogger()

    start = time.time()

    await logger.log(AuditEventType.AUTH_SUCCESS, "Event 1")
    time.sleep(0.1)
    mid = time.time()
    time.sleep(0.1)
    await logger.log(AuditEventType.AUTH_SUCCESS, "Event 2")

    # Get events after mid
    events = logger.search(start_time=mid)
    assert len(events) == 1


@pytest.mark.asyncio
async def test_audit_logger_get_user_activity():
    """Test getting user activity."""
    logger = AuditLogger()

    await logger.log(AuditEventType.AUTH_SUCCESS, "Login", user_id="user1")
    await logger.log(AuditEventType.DATA_READ, "Read data", user_id="user1")
    await logger.log(AuditEventType.AUTH_SUCCESS, "Login", user_id="user2")

    user1_activity = logger.get_user_activity("user1", hours=24)
    assert len(user1_activity) == 2


@pytest.mark.asyncio
async def test_audit_logger_security_events():
    """Test getting security events."""
    logger = AuditLogger()

    await logger.log(AuditEventType.AUTH_SUCCESS, "Login")
    await logger.log(AuditEventType.AUTH_FAILURE, "Failed login")
    await logger.log(AuditEventType.SUSPICIOUS_ACTIVITY, "Suspicious")
    await logger.log(AuditEventType.DATA_READ, "Normal read")

    security_events = logger.get_security_events(hours=24)
    assert len(security_events) == 2  # failure + suspicious


def test_audit_logger_statistics():
    """Test audit logger statistics."""
    logger = AuditLogger()

    asyncio.run(logger.log(AuditEventType.AUTH_SUCCESS, "Event 1"))
    asyncio.run(logger.log(AuditEventType.AUTH_FAILURE, "Event 2"))

    stats = logger.get_statistics()

    assert stats["total_events"] == 2
    assert stats["events_in_memory"] == 2


@pytest.mark.asyncio
async def test_audit_logger_file_output():
    """Test writing audit logs to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "audit.log"

        logger = AuditLogger(log_file=log_file)

        await logger.log(AuditEventType.AUTH_SUCCESS, "Test event")

        # Check file exists and contains event
        assert log_file.exists()
        content = log_file.read_text()
        assert "auth_success" in content


# ============================================================================
# Authentication Tests
# ============================================================================

def test_role_permissions():
    """Test role to permissions mapping."""
    admin_perms = ROLE_PERMISSIONS[Role.ADMIN]

    assert Permission.SYSTEM_ADMIN in admin_perms
    assert Permission.READ_DATA in admin_perms

    user_perms = ROLE_PERMISSIONS[Role.USER]
    assert Permission.READ_DATA in user_perms
    assert Permission.SYSTEM_ADMIN not in user_perms


def test_user_get_permissions():
    """Test getting user permissions."""
    user = User(
        user_id="user1",
        username="testuser",
        email="test@example.com",
        role=Role.USER,
    )

    perms = user.get_permissions()

    assert Permission.READ_DATA in perms
    assert Permission.WRITE_DATA in perms
    assert Permission.DELETE_DATA not in perms


def test_user_has_permission():
    """Test checking user permissions."""
    user = User(
        user_id="user1",
        username="testuser",
        email="test@example.com",
        role=Role.USER,
    )

    assert user.has_permission(Permission.READ_DATA) is True
    assert user.has_permission(Permission.DELETE_DATA) is False


def test_user_custom_permissions():
    """Test custom permissions."""
    user = User(
        user_id="user1",
        username="testuser",
        email="test@example.com",
        role=Role.USER,
    )

    # Add custom permission
    user.custom_permissions.add(Permission.DELETE_DATA)

    assert user.has_permission(Permission.DELETE_DATA) is True


def test_api_key_expiration():
    """Test API key expiration."""
    key = APIKey(
        key_id="key1",
        user_id="user1",
        name="Test Key",
        key_hash="hash123",
        expires_at=time.time() - 100,  # Expired
    )

    assert key.is_expired() is True
    assert key.is_valid() is False


def test_api_key_valid():
    """Test valid API key."""
    key = APIKey(
        key_id="key1",
        user_id="user1",
        name="Test Key",
        key_hash="hash123",
        expires_at=time.time() + 86400,  # Expires tomorrow
    )

    assert key.is_expired() is False
    assert key.is_valid() is True


def test_auth_manager_create_user():
    """Test creating users."""
    auth = AuthManager()

    user = auth.create_user(
        username="testuser",
        email="test@example.com",
        role=Role.USER,
    )

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.role == Role.USER
    assert user.user_id in auth.users


def test_auth_manager_get_user():
    """Test getting users."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com")

    retrieved = auth.get_user(user.user_id)
    assert retrieved is user


def test_auth_manager_create_api_key():
    """Test creating API keys."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com")

    raw_key, api_key = auth.create_api_key(
        user_id=user.user_id,
        name="Test Key",
        expires_in_days=30,
    )

    assert len(raw_key) > 0
    assert api_key.user_id == user.user_id
    assert api_key.name == "Test Key"
    assert api_key.expires_at is not None


@pytest.mark.asyncio
async def test_auth_manager_verify_api_key():
    """Test verifying API keys."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com")
    raw_key, api_key = auth.create_api_key(user.user_id, "Test Key")

    # Verify with correct key
    verified_user = await auth.verify_api_key(raw_key)
    assert verified_user is not None
    assert verified_user.user_id == user.user_id

    # Verify with wrong key
    wrong_user = await auth.verify_api_key("wrong_key_12345")
    assert wrong_user is None


@pytest.mark.asyncio
async def test_auth_manager_verify_expired_key():
    """Test verifying expired API key."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com")
    raw_key, api_key = auth.create_api_key(
        user.user_id,
        "Test Key",
        expires_in_days=-1,  # Already expired
    )

    verified_user = await auth.verify_api_key(raw_key)
    assert verified_user is None


def test_auth_manager_revoke_api_key():
    """Test revoking API keys."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com")
    raw_key, api_key = auth.create_api_key(user.user_id, "Test Key")

    # Revoke key
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    auth.revoke_api_key(key_hash, user.user_id)

    assert api_key.is_active is False


@pytest.mark.asyncio
async def test_auth_manager_rate_limiting():
    """Test rate limiting."""
    auth = AuthManager(default_rate_limit=3, rate_limit_window=60.0)

    user = auth.create_user("testuser", "test@example.com")

    # First 3 requests should succeed
    assert await auth.check_rate_limit(user.user_id) is True
    assert await auth.check_rate_limit(user.user_id) is True
    assert await auth.check_rate_limit(user.user_id) is True

    # 4th should raise
    with pytest.raises(RateLimitExceeded):
        await auth.check_rate_limit(user.user_id)


def test_auth_manager_check_permission():
    """Test permission checking."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com", role=Role.USER)

    # User has READ_DATA
    assert auth.check_permission(user, Permission.READ_DATA) is True

    # User lacks DELETE_DATA
    with pytest.raises(AuthorizationError):
        auth.check_permission(user, Permission.DELETE_DATA)


def test_auth_manager_assign_role():
    """Test assigning roles."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com", role=Role.USER)
    admin = auth.create_user("admin", "admin@example.com", role=Role.ADMIN)

    # Assign new role
    auth.assign_role(user.user_id, Role.DEVELOPER, assigned_by=admin.user_id)

    assert user.role == Role.DEVELOPER


def test_auth_manager_grant_revoke_permission():
    """Test granting and revoking permissions."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com", role=Role.USER)

    # Grant custom permission
    auth.grant_permission(user.user_id, Permission.DELETE_DATA)
    assert user.has_permission(Permission.DELETE_DATA) is True

    # Revoke permission
    auth.revoke_permission(user.user_id, Permission.DELETE_DATA)
    assert user.has_permission(Permission.DELETE_DATA) is False


def test_auth_manager_oauth_credentials():
    """Test OAuth credential storage."""
    auth = AuthManager()

    user = auth.create_user("testuser", "test@example.com")

    credentials = OAuthCredentials(
        provider=OAuthProvider.GOOGLE,
        access_token="token123",
        refresh_token="refresh123",
    )

    # Store credentials
    auth.store_oauth_credentials(user.user_id, credentials)

    # Retrieve credentials
    retrieved = auth.get_oauth_credentials(user.user_id)
    assert retrieved is not None
    assert retrieved.provider == OAuthProvider.GOOGLE
    assert retrieved.access_token == "token123"


def test_auth_manager_statistics():
    """Test authentication statistics."""
    auth = AuthManager()

    # Create users
    auth.create_user("user1", "user1@example.com", role=Role.USER)
    auth.create_user("admin1", "admin@example.com", role=Role.ADMIN)
    auth.create_user("user2", "user2@example.com", role=Role.USER)

    stats = auth.get_statistics()

    assert stats["total_users"] == 3
    assert stats["active_users"] == 3
    assert stats["users_by_role"][Role.USER.value] == 2
    assert stats["users_by_role"][Role.ADMIN.value] == 1
