"""
Webhook Retry Logic

Exponential backoff retry with failure notifications.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

class RetryStatus(Enum):
    """Retry attempt status"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    EXHAUSTED = "exhausted"


@dataclass
class RetryPolicy:
    """
    Retry policy configuration.

    Implements exponential backoff with jitter.
    """
    max_attempts: int = 5
    initial_delay: float = 1.0  # seconds
    max_delay: float = 300.0  # 5 minutes
    exponential_base: float = 2.0
    jitter: bool = True
    timeout: float = 30.0  # per-attempt timeout


@dataclass
class RetryAttempt:
    """Record of a retry attempt"""
    attempt_number: int
    timestamp: datetime
    status: RetryStatus
    delay: float
    error: Optional[str] = None
    response_code: Optional[int] = None


@dataclass
class WebhookDelivery:
    """
    Webhook delivery tracking.

    Tracks all retry attempts and final outcome.
    """
    webhook_id: str
    url: str
    payload: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    attempts: List[RetryAttempt] = field(default_factory=list)
    status: RetryStatus = RetryStatus.PENDING
    final_error: Optional[str] = None

    @property
    def attempt_count(self) -> int:
        """Get number of attempts"""
        return len(self.attempts)

    @property
    def last_attempt(self) -> Optional[RetryAttempt]:
        """Get last attempt"""
        return self.attempts[-1] if self.attempts else None


# =============================================================================
# Retry Manager
# =============================================================================

class WebhookRetryManager:
    """
    Manages webhook retry logic with exponential backoff.

    Features:
    - Exponential backoff with jitter
    - Configurable retry policy
    - Failure notifications
    - Delivery tracking

    Usage:
        retry_manager = WebhookRetryManager(
            policy=RetryPolicy(max_attempts=5),
            on_failure=send_alert
        )

        delivery = await retry_manager.deliver_webhook(
            url="https://example.com/webhook",
            payload={"event": "task.completed"}
        )
    """

    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        on_failure: Optional[Callable[[WebhookDelivery], None]] = None,
        on_final_failure: Optional[Callable[[WebhookDelivery], None]] = None,
    ):
        """
        Initialize retry manager.

        Args:
            policy: Retry policy configuration
            on_failure: Callback for each failed attempt
            on_final_failure: Callback when all attempts exhausted
        """
        self.policy = policy or RetryPolicy()
        self.on_failure = on_failure
        self.on_final_failure = on_final_failure

        # Track active deliveries
        self.deliveries: Dict[str, WebhookDelivery] = {}

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.policy.initial_delay * (self.policy.exponential_base ** attempt)

        # Cap at max delay
        delay = min(delay, self.policy.max_delay)

        # Add jitter
        if self.policy.jitter:
            import random
            jitter = random.uniform(0, delay * 0.1)  # ±10% jitter
            delay += jitter

        return delay

    async def deliver_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        webhook_id: Optional[str] = None,
    ) -> WebhookDelivery:
        """
        Deliver webhook with automatic retry.

        Args:
            url: Webhook URL
            payload: Payload to send
            headers: Optional headers
            webhook_id: Optional webhook ID

        Returns:
            WebhookDelivery with delivery status
        """
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx required for webhook delivery")

        # Create delivery tracking
        if not webhook_id:
            webhook_id = f"wh_{int(time.time() * 1000)}"

        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            url=url,
            payload=payload,
            headers=headers or {},
        )

        self.deliveries[webhook_id] = delivery

        # Attempt delivery with retries
        async with httpx.AsyncClient() as client:
            for attempt in range(self.policy.max_attempts):
                # Calculate delay (skip for first attempt)
                if attempt > 0:
                    delay = self.calculate_delay(attempt - 1)
                    print(f"[WebhookRetry] Waiting {delay:.2f}s before attempt {attempt + 1}")
                    await asyncio.sleep(delay)
                else:
                    delay = 0.0

                # Attempt delivery
                print(f"[WebhookRetry] Attempt {attempt + 1}/{self.policy.max_attempts} for {webhook_id}")

                try:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=headers or {},
                        timeout=self.policy.timeout,
                    )

                    # Record attempt
                    attempt_record = RetryAttempt(
                        attempt_number=attempt + 1,
                        timestamp=datetime.now(),
                        status=RetryStatus.SUCCESS if response.status_code < 400 else RetryStatus.FAILED,
                        delay=delay,
                        response_code=response.status_code,
                    )

                    delivery.attempts.append(attempt_record)

                    # Check if successful
                    if response.status_code < 400:
                        delivery.status = RetryStatus.SUCCESS
                        print(f"[WebhookRetry] ✅ Webhook delivered successfully: {webhook_id}")
                        return delivery

                    # Non-retryable status codes
                    if response.status_code in [400, 401, 403, 404, 410]:
                        delivery.status = RetryStatus.EXHAUSTED
                        delivery.final_error = f"Non-retryable status: {response.status_code}"
                        print(f"[WebhookRetry] ❌ Non-retryable error: {response.status_code}")

                        if self.on_final_failure:
                            self.on_final_failure(delivery)

                        return delivery

                    # Retryable error
                    attempt_record.error = f"HTTP {response.status_code}"

                    if self.on_failure:
                        self.on_failure(delivery)

                except httpx.TimeoutException:
                    print(f"[WebhookRetry] ⏱️ Timeout on attempt {attempt + 1}")
                    delivery.attempts.append(RetryAttempt(
                        attempt_number=attempt + 1,
                        timestamp=datetime.now(),
                        status=RetryStatus.FAILED,
                        delay=delay,
                        error="Timeout",
                    ))

                    if self.on_failure:
                        self.on_failure(delivery)

                except httpx.RequestError as e:
                    print(f"[WebhookRetry] 🔌 Connection error on attempt {attempt + 1}: {e}")
                    delivery.attempts.append(RetryAttempt(
                        attempt_number=attempt + 1,
                        timestamp=datetime.now(),
                        status=RetryStatus.FAILED,
                        delay=delay,
                        error=str(e),
                    ))

                    if self.on_failure:
                        self.on_failure(delivery)

                except Exception as e:
                    print(f"[WebhookRetry] ❌ Unexpected error on attempt {attempt + 1}: {e}")
                    delivery.attempts.append(RetryAttempt(
                        attempt_number=attempt + 1,
                        timestamp=datetime.now(),
                        status=RetryStatus.FAILED,
                        delay=delay,
                        error=str(e),
                    ))

                    if self.on_failure:
                        self.on_failure(delivery)

            # All attempts exhausted
            delivery.status = RetryStatus.EXHAUSTED
            delivery.final_error = f"All {self.policy.max_attempts} attempts failed"
            print(f"[WebhookRetry] ❌ All retry attempts exhausted for {webhook_id}")

            if self.on_final_failure:
                self.on_final_failure(delivery)

            return delivery

    def get_delivery(self, webhook_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID"""
        return self.deliveries.get(webhook_id)

    def get_failed_deliveries(self) -> List[WebhookDelivery]:
        """Get all failed deliveries"""
        return [
            d for d in self.deliveries.values()
            if d.status in [RetryStatus.FAILED, RetryStatus.EXHAUSTED]
        ]


# =============================================================================
# Failure Notification
# =============================================================================

class FailureNotifier:
    """
    Sends notifications for webhook failures.

    Supports:
    - Email notifications
    - Slack notifications
    - Custom callbacks
    """

    def __init__(
        self,
        email_to: Optional[str] = None,
        slack_webhook: Optional[str] = None,
        custom_callback: Optional[Callable[[WebhookDelivery], None]] = None,
    ):
        """
        Initialize failure notifier.

        Args:
            email_to: Email address for notifications
            slack_webhook: Slack webhook URL
            custom_callback: Custom notification function
        """
        self.email_to = email_to
        self.slack_webhook = slack_webhook
        self.custom_callback = custom_callback

    async def notify_failure(self, delivery: WebhookDelivery):
        """
        Send failure notification.

        Args:
            delivery: Failed webhook delivery
        """
        message = self._format_failure_message(delivery)

        # Send to all configured channels
        tasks = []

        if self.email_to:
            tasks.append(self._send_email(message))

        if self.slack_webhook:
            tasks.append(self._send_slack(message))

        if self.custom_callback:
            tasks.append(self._call_custom(delivery))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _format_failure_message(self, delivery: WebhookDelivery) -> str:
        """Format failure notification message"""
        lines = [
            f"🚨 Webhook Delivery Failed",
            f"",
            f"Webhook ID: {delivery.webhook_id}",
            f"URL: {delivery.url}",
            f"Attempts: {delivery.attempt_count}/{delivery.attempt_count}",
            f"Status: {delivery.status.value}",
            f"",
            f"Final Error: {delivery.final_error or 'Unknown'}",
            f"",
            f"Attempt History:",
        ]

        for attempt in delivery.attempts:
            lines.append(
                f"  {attempt.attempt_number}. {attempt.timestamp.isoformat()} - "
                f"{attempt.status.value} "
                f"(delay: {attempt.delay:.1f}s, error: {attempt.error or 'N/A'})"
            )

        return "\n".join(lines)

    async def _send_email(self, message: str):
        """Send email notification"""
        # Placeholder - implement with your email provider
        print(f"[FailureNotifier] Would send email to {self.email_to}:")
        print(message)

    async def _send_slack(self, message: str):
        """Send Slack notification"""
        if not HTTPX_AVAILABLE:
            return

        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.slack_webhook,
                    json={"text": message},
                    timeout=10.0,
                )
            print(f"[FailureNotifier] Sent Slack notification")
        except Exception as e:
            print(f"[FailureNotifier] Error sending Slack notification: {e}")

    async def _call_custom(self, delivery: WebhookDelivery):
        """Call custom notification callback"""
        try:
            if asyncio.iscoroutinefunction(self.custom_callback):
                await self.custom_callback(delivery)
            else:
                self.custom_callback(delivery)
        except Exception as e:
            print(f"[FailureNotifier] Error in custom callback: {e}")


# =============================================================================
# Utility Functions
# =============================================================================

def create_retry_manager(
    max_attempts: int = 5,
    on_failure: Optional[Callable] = None,
) -> WebhookRetryManager:
    """Quick helper to create retry manager"""
    return WebhookRetryManager(
        policy=RetryPolicy(max_attempts=max_attempts),
        on_failure=on_failure,
    )
