"""
Execute payment via Stripe.

PHASE 7.4: Process payments programmatically.

⚠️ CRITICAL: Always requires approval, even for small amounts.

Requires environment variables:
- STRIPE_API_KEY: Your Stripe secret API key

Setup: https://stripe.com/docs/api
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


class MakePaymentTool(ActionTool):
    """Process payment via Stripe"""

    def __init__(self):
        super().__init__()
        self._api_base = "https://api.stripe.com/v1"

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="make_payment",
            version="1.0.0",
            description="Process payment via Stripe (requires approval)",
            domains=["finance", "billing"],
            roles=["admin", "finance"],
            required_permissions=["payment_process"],
            input_schema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "minimum": 0.50,
                        "description": "Amount in USD (minimum $0.50)"
                    },
                    "currency": {
                        "type": "string",
                        "default": "usd",
                        "enum": ["usd", "eur", "gbp", "cad", "aud"],
                        "description": "Currency code"
                    },
                    "payment_method_id": {
                        "type": "string",
                        "description": "Stripe payment method ID"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Stripe customer ID (optional)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Payment description"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata (optional)"
                    }
                },
                "required": ["amount", "payment_method_id", "description"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "payment_intent_id": {"type": "string"},
                    "status": {"type": "string"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "created_at": {"type": "string"}
                }
            },
            cost_estimate=0.0,  # The cost is the payment amount itself
            timeout_seconds=30,
            requires_network=True,
            examples=[
                {
                    "input": {
                        "amount": 99.99,
                        "payment_method_id": "pm_1234567890",
                        "description": "Invoice #12345 payment"
                    },
                    "output": {
                        "payment_intent_id": "pi_1234567890abcdef",
                        "status": "succeeded",
                        "amount": 99.99,
                        "currency": "usd",
                        "created_at": "2025-11-20T12:00:00Z"
                    }
                }
            ],
            tags=["payment", "stripe", "finance", "billing"]
        )

    async def estimate_cost(self, params: Dict[str, Any]) -> float:
        """Payment cost is the amount itself"""
        # The "cost" for a payment is the payment amount
        return params["amount"]

    async def execute_action(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Process payment via Stripe"""
        if not REQUESTS_AVAILABLE:
            return ToolResult(
                success=False,
                error="requests library not installed. Install with: pip install requests"
            )

        amount = params["amount"]
        currency = params.get("currency", "usd")
        payment_method_id = params["payment_method_id"]
        customer_id = params.get("customer_id")
        description = params["description"]
        metadata = params.get("metadata", {})

        # Validate API key
        stripe_key = os.getenv("STRIPE_API_KEY")
        if not stripe_key:
            return ToolResult(
                success=False,
                error="Stripe API key not configured. Set STRIPE_API_KEY environment variable."
            )

        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)

            # Create payment intent
            payment_data = {
                "amount": amount_cents,
                "currency": currency,
                "payment_method": payment_method_id,
                "description": description,
                "confirm": True,  # Automatically confirm the payment
                "metadata": metadata
            }

            if customer_id:
                payment_data["customer"] = customer_id

            response = requests.post(
                f"{self._api_base}/payment_intents",
                auth=(stripe_key, ""),
                data=payment_data,
                timeout=30
            )

            response.raise_for_status()
            payment_intent = response.json()

            status = payment_intent["status"]
            success = status in ["succeeded", "processing"]

            core_logging.log_event("payment_processed", {
                "payment_intent_id": payment_intent["id"],
                "amount": amount,
                "currency": currency,
                "status": status,
                "description": description,
                "customer_id": customer_id
            })

            if success:
                return ToolResult(
                    success=True,
                    data={
                        "payment_intent_id": payment_intent["id"],
                        "status": status,
                        "amount": amount,
                        "currency": currency,
                        "created_at": payment_intent["created"],
                        "charges": payment_intent.get("charges", {}).get("data", [])
                    },
                    metadata={
                        "payment_method": payment_method_id,
                        "customer_id": customer_id,
                        "description": description
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    error=f"Payment failed with status: {status}",
                    metadata={"payment_intent_id": payment_intent["id"], "status": status}
                )

        except requests.RequestException as e:
            core_logging.log_event("payment_failed", {
                "amount": amount,
                "error": str(e)
            })

            error_msg = f"Payment processing failed: {str(e)}"

            # Extract Stripe error if available
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_data = e.response.json()
                    if "error" in error_data:
                        stripe_error = error_data["error"]
                        error_msg = f"Stripe error: {stripe_error.get('message', str(e))}"
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
        """Attempt refund via Stripe"""
        execution = self.get_execution_history(execution_id)

        if not execution or "result" not in execution:
            core_logging.log_event("refund_failed", {
                "execution_id": execution_id,
                "reason": "execution not found"
            })
            return False

        payment_intent_id = execution["result"].get("payment_intent_id")

        if not payment_intent_id:
            return False

        stripe_key = os.getenv("STRIPE_API_KEY")
        if not stripe_key:
            return False

        try:
            # Get payment intent to find charge ID
            pi_response = requests.get(
                f"{self._api_base}/payment_intents/{payment_intent_id}",
                auth=(stripe_key, ""),
                timeout=30
            )
            pi_response.raise_for_status()
            payment_intent = pi_response.json()

            # Get the charge ID
            charges = payment_intent.get("charges", {}).get("data", [])
            if not charges:
                return False

            charge_id = charges[0]["id"]

            # Create refund
            refund_response = requests.post(
                f"{self._api_base}/refunds",
                auth=(stripe_key, ""),
                data={"charge": charge_id},
                timeout=30
            )

            refund_response.raise_for_status()
            refund = refund_response.json()

            success = refund["status"] in ["succeeded", "pending"]

            core_logging.log_event("payment_refunded", {
                "execution_id": execution_id,
                "payment_intent_id": payment_intent_id,
                "refund_id": refund["id"],
                "status": refund["status"],
                "amount": refund["amount"] / 100.0
            })

            return success

        except Exception as e:
            core_logging.log_event("refund_failed", {
                "execution_id": execution_id,
                "payment_intent_id": payment_intent_id,
                "error": str(e)
            })
            return False

    def _format_action_description(self, params: Dict[str, Any]) -> str:
        """Format action description for approval"""
        amount = params["amount"]
        currency = params.get("currency", "USD").upper()
        description = params["description"]

        return f"Process payment of ${amount:.2f} {currency} for: {description}"

    def _assess_risk(self, params: Dict[str, Any], cost: float) -> ActionRisk:
        """Payments always require approval - assess risk based on amount"""
        amount = params["amount"]

        # Payments always HIGH or CRITICAL risk
        if amount > 100:
            return ActionRisk.CRITICAL  # Requires 2FA
        elif amount > 10:
            return ActionRisk.HIGH
        else:
            return ActionRisk.MEDIUM  # Even small payments need approval
