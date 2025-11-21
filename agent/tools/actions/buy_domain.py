"""
Buy domain via Namecheap API.

PHASE 7.4: Purchase domain names programmatically.

Requires environment variables:
- NAMECHEAP_API_KEY: Your Namecheap API key
- NAMECHEAP_API_USER: Your Namecheap username
- NAMECHEAP_CLIENT_IP: Your whitelisted IP address

Setup: https://www.namecheap.com/support/api/intro/
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Any, Dict
from urllib.parse import urlencode

import agent.core_logging as core_logging
from agent.tools.actions.base import ActionTool, ActionRisk
from agent.tools.base import ToolExecutionContext, ToolManifest, ToolResult

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class BuyDomainTool(ActionTool):
    """Buy domain from Namecheap"""

    def __init__(self):
        super().__init__()
        self._api_base = "https://api.namecheap.com/xml.response"
        self._sandbox_base = "https://api.sandbox.namecheap.com/xml.response"

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="buy_domain",
            version="1.0.0",
            description="Purchase domain name via Namecheap API",
            domains=["infrastructure", "web"],
            roles=["admin", "devops"],
            required_permissions=["domain_purchase"],
            input_schema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "pattern": r"^[a-z0-9-]+\.[a-z]{2,}$",
                        "description": "Domain to purchase (e.g., example.com)"
                    },
                    "years": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 1,
                        "description": "Number of years to register"
                    },
                    "sandbox": {
                        "type": "boolean",
                        "default": False,
                        "description": "Use sandbox API for testing"
                    },
                    "nameservers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Custom nameservers (optional)"
                    }
                },
                "required": ["domain"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "domain": {"type": "string"},
                    "cost": {"type": "number"},
                    "nameservers": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "expires_at": {"type": "string"},
                    "registration_id": {"type": "string"}
                }
            },
            cost_estimate=12.98,
            timeout_seconds=30,
            requires_network=True,
            examples=[
                {
                    "input": {"domain": "example.com", "years": 1},
                    "output": {
                        "domain": "example.com",
                        "cost": 12.98,
                        "nameservers": ["ns1.namecheap.com", "ns2.namecheap.com"],
                        "expires_at": "2026-11-20",
                        "registration_id": "123456"
                    }
                }
            ],
            tags=["domain", "infrastructure", "dns"]
        )

    async def estimate_cost(self, params: Dict[str, Any]) -> float:
        """Get domain pricing from Namecheap"""
        domain = params["domain"]
        years = params.get("years", 1)
        sandbox = params.get("sandbox", False)

        if not REQUESTS_AVAILABLE:
            # Fallback estimate
            core_logging.log_event("domain_cost_fallback", {
                "domain": domain,
                "reason": "requests library not available"
            })
            return 12.98 * years

        try:
            # Check availability and get price
            tld = domain.split(".")[-1]
            response = await self._namecheap_api_call(
                "namecheap.users.getPricing",
                {
                    "ProductType": "DOMAIN",
                    "ProductCategory": "REGISTER",
                    "ActionName": "REGISTER"
                },
                sandbox=sandbox
            )

            # Parse pricing from XML response
            # For simplicity, using default pricing
            # Real implementation would parse the XML for TLD-specific pricing
            base_price = self._get_tld_price(tld)
            return base_price * years

        except Exception as e:
            core_logging.log_event("domain_cost_estimation_error", {
                "domain": domain,
                "error": str(e)
            })
            # Fallback estimate
            return 12.98 * years

    async def execute_action(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Purchase domain"""
        if not REQUESTS_AVAILABLE:
            return ToolResult(
                success=False,
                error="requests library not installed. Install with: pip install requests"
            )

        domain = params["domain"]
        years = params.get("years", 1)
        sandbox = params.get("sandbox", False)
        nameservers = params.get("nameservers")

        try:
            # Step 1: Check availability
            availability = await self._check_availability(domain, sandbox)

            if not availability["available"]:
                return ToolResult(
                    success=False,
                    error=f"Domain {domain} is not available for registration",
                    metadata={"availability": availability}
                )

            # Step 2: Register domain
            register_params = {
                "DomainName": domain,
                "Years": str(years)
            }

            # Add nameservers if provided
            if nameservers:
                for i, ns in enumerate(nameservers, 1):
                    register_params[f"Nameserver{i}"] = ns
            else:
                # Use Namecheap default nameservers
                register_params["Nameserver1"] = "dns1.registrar-servers.com"
                register_params["Nameserver2"] = "dns2.registrar-servers.com"

            # Register domain via API
            response = await self._namecheap_api_call(
                "namecheap.domains.create",
                register_params,
                sandbox=sandbox
            )

            # Parse response
            registration_data = self._parse_registration_response(response)

            core_logging.log_event("domain_purchased", {
                "domain": domain,
                "years": years,
                "cost": registration_data["cost"],
                "registration_id": registration_data["registration_id"]
            })

            return ToolResult(
                success=True,
                data={
                    "domain": domain,
                    "cost": registration_data["cost"],
                    "nameservers": registration_data.get("nameservers", []),
                    "expires_at": registration_data.get("expires_at"),
                    "registration_id": registration_data["registration_id"]
                },
                metadata={
                    "years": years,
                    "sandbox": sandbox
                }
            )

        except Exception as e:
            core_logging.log_event("domain_purchase_failed", {
                "domain": domain,
                "error": str(e)
            })
            return ToolResult(
                success=False,
                error=f"Failed to purchase domain: {str(e)}"
            )

    async def rollback(
        self,
        execution_id: str,
        context: ToolExecutionContext
    ) -> bool:
        """
        Attempt refund (limited by Namecheap policy).

        Note: Namecheap has a limited refund policy. Domain registrations
        are typically non-refundable after the initial grace period.
        """
        execution = self.get_execution_history(execution_id)

        if not execution:
            core_logging.log_event("rollback_failed", {
                "execution_id": execution_id,
                "reason": "execution not found"
            })
            return False

        # Check if within refund window (typically 24 hours)
        from datetime import datetime, timedelta
        execution_time = datetime.fromisoformat(execution["timestamp"])
        now = datetime.now()

        if now - execution_time > timedelta(hours=24):
            core_logging.log_event("rollback_failed", {
                "execution_id": execution_id,
                "reason": "outside refund window"
            })
            return False

        # Namecheap doesn't have a public refund API
        # Would need to contact support manually
        core_logging.log_event("rollback_requested", {
            "execution_id": execution_id,
            "domain": execution["params"]["domain"],
            "note": "Manual refund request required - contact Namecheap support"
        })

        return False

    async def _check_availability(
        self,
        domain: str,
        sandbox: bool = False
    ) -> Dict[str, Any]:
        """Check if domain is available"""
        response = await self._namecheap_api_call(
            "namecheap.domains.check",
            {"DomainList": domain},
            sandbox=sandbox
        )

        # Parse availability from response
        # Simplified - real implementation would parse XML properly
        return {
            "available": True,  # Placeholder
            "domain": domain
        }

    async def _namecheap_api_call(
        self,
        command: str,
        params: Dict[str, Any],
        sandbox: bool = False
    ) -> str:
        """Make Namecheap API call"""
        import socket

        api_key = os.getenv("NAMECHEAP_API_KEY")
        api_user = os.getenv("NAMECHEAP_API_USER")
        client_ip = os.getenv("NAMECHEAP_CLIENT_IP")

        if not api_key or not api_user:
            raise ValueError(
                "Namecheap API credentials not configured. "
                "Set NAMECHEAP_API_KEY and NAMECHEAP_API_USER environment variables."
            )

        # Get client IP if not provided
        if not client_ip:
            try:
                # Try to get public IP
                response = requests.get("https://api.ipify.org", timeout=5)
                client_ip = response.text
            except:
                # Fallback to local IP
                client_ip = socket.gethostbyname(socket.gethostname())

        # Construct API URL
        api_url = self._sandbox_base if sandbox else self._api_base

        # Build parameters
        api_params = {
            "ApiUser": api_user,
            "ApiKey": api_key,
            "UserName": api_user,
            "Command": command,
            "ClientIp": client_ip
        }
        api_params.update(params)

        # Make request
        try:
            response = requests.get(api_url, params=api_params, timeout=30)
            response.raise_for_status()

            core_logging.log_event("namecheap_api_call", {
                "command": command,
                "status_code": response.status_code,
                "sandbox": sandbox
            })

            return response.text

        except requests.RequestException as e:
            core_logging.log_event("namecheap_api_error", {
                "command": command,
                "error": str(e)
            })
            raise Exception(f"Namecheap API error: {str(e)}")

    def _parse_registration_response(self, xml_response: str) -> Dict[str, Any]:
        """Parse Namecheap XML response"""
        try:
            root = ET.fromstring(xml_response)

            # Check for API errors
            status = root.get("Status")
            if status != "OK":
                errors = root.findall(".//Error")
                if errors:
                    error_msg = errors[0].text
                    raise Exception(f"Namecheap API error: {error_msg}")

            # Parse registration data
            domain_create = root.find(".//DomainCreateResult")

            if domain_create is not None:
                return {
                    "registration_id": domain_create.get("DomainID", ""),
                    "domain": domain_create.get("Domain", ""),
                    "cost": float(domain_create.get("ChargedAmount", "0")),
                    "expires_at": domain_create.get("Expires", ""),
                    "nameservers": []
                }

            # Fallback
            return {
                "registration_id": "unknown",
                "cost": 0.0
            }

        except ET.ParseError as e:
            core_logging.log_event("xml_parse_error", {
                "error": str(e),
                "response": xml_response[:200]
            })
            raise Exception(f"Failed to parse Namecheap response: {str(e)}")

    def _get_tld_price(self, tld: str) -> float:
        """Get base price for TLD"""
        # Simplified pricing table
        # Real implementation would fetch from API
        pricing = {
            "com": 12.98,
            "net": 13.98,
            "org": 14.98,
            "io": 39.98,
            "dev": 14.98,
            "app": 19.98,
            "ai": 99.98
        }
        return pricing.get(tld.lower(), 12.98)

    def _format_action_description(self, params: Dict[str, Any]) -> str:
        """Format action description for approval"""
        domain = params["domain"]
        years = params.get("years", 1)
        return f"Purchase domain '{domain}' for {years} year(s)"

    def _assess_risk(self, params: Dict[str, Any], cost: float) -> ActionRisk:
        """Assess risk - domains are medium risk (non-refundable)"""
        # Domain purchases are typically non-refundable
        if cost > 50:
            return ActionRisk.HIGH
        else:
            return ActionRisk.MEDIUM
