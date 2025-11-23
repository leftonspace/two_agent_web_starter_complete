"""
Send SMS via Twilio.

PHASE 7.4: Send SMS messages programmatically.

Requires environment variables:
- TWILIO_ACCOUNT_SID: Your Twilio account SID
- TWILIO_AUTH_TOKEN: Your Twilio auth token
- TWILIO_PHONE_NUMBER: Your Twilio phone number (format: +1234567890)

Setup: https://www.twilio.com/docs/usage/api
"""

from __future__ import annotations

import os
from typing import Any, Dict

import agent.core_logging as core_logging
from agent.tools.actions.base import ActionTool, ActionRisk
from agent.tools.base import ToolExecutionContext, ToolManifest, ToolResult

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class SendSMSTool(ActionTool):
    """Send SMS message via Twilio"""

    def __init__(self):
        super().__init__()
        self._api_base = "https://api.twilio.com/2010-04-01"
        self._cost_per_message = 0.0079  # ~$0.008 per SMS in US

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="send_sms",
            version="1.0.0",
            description="Send SMS message via Twilio",
            domains=["communication", "notifications"],
            roles=["admin", "manager", "support"],
            required_permissions=["sms_send"],
            input_schema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "pattern": r"^\+?[1-9]\d{1,14}$",
                        "description": "Recipient phone number (E.164 format, e.g., +14155552671)"
                    },
                    "message": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 1600,
                        "description": "Message text (max 1600 characters)"
                    },
                    "from_number": {
                        "type": "string",
                        "description": "Sender phone number (optional, uses TWILIO_PHONE_NUMBER if not provided)"
                    }
                },
                "required": ["to", "message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "message_sid": {"type": "string"},
                    "status": {"type": "string"},
                    "to": {"type": "string"},
                    "from": {"type": "string"},
                    "cost": {"type": "number"},
                    "sent_at": {"type": "string"}
                }
            },
            cost_estimate=0.0079,
            timeout_seconds=15,
            requires_network=True,
            examples=[
                {
                    "input": {
                        "to": "+14155552671",
                        "message": "Hello from System-1.2!"
                    },
                    "output": {
                        "message_sid": "SM1234567890abcdef",
                        "status": "queued",
                        "to": "+14155552671",
                        "from": "+14155552670",
                        "cost": 0.0079,
                        "sent_at": "2025-11-20T12:00:00Z"
                    }
                }
            ],
            tags=["sms", "messaging", "communication", "twilio"]
        )

    async def estimate_cost(self, params: Dict[str, Any]) -> float:
        """Estimate SMS cost"""
        message = params["message"]

        # SMS messages are charged per segment (160 chars)
        # For messages with Unicode, it's 70 chars per segment
        has_unicode = any(ord(char) > 127 for char in message)
        chars_per_segment = 70 if has_unicode else 160

        segments = (len(message) + chars_per_segment - 1) // chars_per_segment

        return self._cost_per_message * segments

    async def execute_action(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Send SMS via Twilio"""
        if not REQUESTS_AVAILABLE:
            return ToolResult(
                success=False,
                error="requests library not installed. Install with: pip install requests"
            )

        to_number = params["to"]
        message = params["message"]
        from_number = params.get("from_number") or os.getenv("TWILIO_PHONE_NUMBER")

        # Validate credentials
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        if not account_sid or not auth_token:
            return ToolResult(
                success=False,
                error="Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
            )

        if not from_number:
            return ToolResult(
                success=False,
                error="Sender phone number not provided. Set TWILIO_PHONE_NUMBER or pass from_number parameter."
            )

        try:
            # Send SMS via Twilio API
            response = requests.post(
                f"{self._api_base}/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data={
                    "To": to_number,
                    "From": from_number,
                    "Body": message
                },
                timeout=15
            )

            response.raise_for_status()
            result = response.json()

            # Calculate actual cost
            cost = await self.estimate_cost(params)

            core_logging.log_event("sms_sent", {
                "message_sid": result["sid"],
                "to": to_number,
                "status": result["status"],
                "cost": cost
            })

            return ToolResult(
                success=True,
                data={
                    "message_sid": result["sid"],
                    "status": result["status"],
                    "to": result["to"],
                    "from": result["from"],
                    "cost": cost,
                    "sent_at": result["date_created"]
                },
                metadata={
                    "segments": result.get("num_segments", 1),
                    "error_code": result.get("error_code"),
                    "error_message": result.get("error_message")
                }
            )

        except requests.RequestException as e:
            core_logging.log_event("sms_send_failed", {
                "to": to_number,
                "error": str(e)
            })

            error_msg = f"Failed to send SMS: {str(e)}"

            # Extract Twilio error if available
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_data = e.response.json()
                    error_msg = f"Twilio error: {error_data.get('message', str(e))}"
            except (ValueError, KeyError, AttributeError):
                pass

            return ToolResult(
                success=False,
                error=error_msg
            )

    async def rollback(
        self,
        execution_id: str,
        context: ToolExecutionContext
    ) -> bool:
        """
        Cannot rollback SMS (message already sent).

        Twilio does not support message cancellation once sent.
        """
        core_logging.log_event("sms_rollback_attempted", {
            "execution_id": execution_id,
            "note": "SMS messages cannot be rolled back once sent"
        })
        return False

    def _format_action_description(self, params: Dict[str, Any]) -> str:
        """Format action description for approval"""
        to = params["to"]
        message_preview = params["message"][:50]
        if len(params["message"]) > 50:
            message_preview += "..."

        return f"Send SMS to {to}: \"{message_preview}\""

    def _assess_risk(self, params: Dict[str, Any], cost: float) -> ActionRisk:
        """SMS is low risk (cheap, non-destructive)"""
        # SMS is inexpensive and non-destructive
        return ActionRisk.LOW
