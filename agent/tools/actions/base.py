"""
Base class for action tools that interact with external services.

PHASE 7.4: Action tools can:
- Execute paid operations (domain purchases, server provisioning)
- Modify external systems (deploy websites, create databases)
- Send notifications (email, SMS, push)

All actions require audit logging and may require user approval.
"""

from __future__ import annotations

import uuid
from abc import abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import agent.core_logging as core_logging
from agent.tools.base import ToolExecutionContext, ToolPlugin, ToolResult


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


class ActionRisk(Enum):
    """Risk level of action"""
    LOW = "low"          # Read-only, no cost (<$1)
    MEDIUM = "medium"    # Modifies data, low cost ($1-$10)
    HIGH = "high"        # High cost ($10-$100) or significant changes
    CRITICAL = "critical"  # Very expensive (>$100) or irreversible


@dataclass
class ActionApproval:
    """Approval request for action"""
    action_name: str
    description: str
    cost_usd: Optional[float]
    risk_level: ActionRisk
    details: Dict[str, Any]
    requires_2fa: bool = False
    approval_id: str = ""

    def __post_init__(self):
        if not self.approval_id:
            self.approval_id = f"approval_{uuid.uuid4().hex[:12]}"


# ══════════════════════════════════════════════════════════════════════
# ActionTool Base Class
# ══════════════════════════════════════════════════════════════════════


class ActionTool(ToolPlugin):
    """
    Base class for action execution tools.

    Provides:
    - Cost estimation before execution
    - User approval workflow
    - Rollback support
    - Audit logging
    - Dry-run support

    Example:
        class BuyDomainTool(ActionTool):
            async def estimate_cost(self, params):
                return 12.98  # $12.98 per domain

            async def execute_action(self, params, context):
                # Purchase domain via API
                return ToolResult(success=True, data={...})

            async def rollback(self, execution_id, context):
                # Attempt refund
                return True
    """

    def __init__(self):
        super().__init__()
        self._execution_history: Dict[str, Dict[str, Any]] = {}

    @abstractmethod
    async def estimate_cost(self, params: Dict[str, Any]) -> float:
        """
        Estimate cost in USD before execution.

        Returns 0.0 for free actions.

        Args:
            params: Tool parameters

        Returns:
            Estimated cost in USD

        Example:
            async def estimate_cost(self, params):
                domain = params["domain"]
                years = params.get("years", 1)
                return 12.98 * years
        """
        pass

    @abstractmethod
    async def execute_action(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute the actual action.

        Called only after approval granted (if required).

        Args:
            params: Tool parameters (validated)
            context: Execution context

        Returns:
            ToolResult with success status and data

        Example:
            async def execute_action(self, params, context):
                domain = params["domain"]
                # Purchase domain via API
                response = await self._api_call(...)
                return ToolResult(
                    success=True,
                    data={"domain": domain, "cost": 12.98}
                )
        """
        pass

    @abstractmethod
    async def rollback(
        self,
        execution_id: str,
        context: ToolExecutionContext
    ) -> bool:
        """
        Attempt to rollback/undo action.

        Not all actions are reversible. Return False if rollback not possible.

        Args:
            execution_id: ID of execution to rollback
            context: Execution context

        Returns:
            True if rollback successful, False otherwise

        Example:
            async def rollback(self, execution_id, context):
                # Check if within refund window
                execution = self._execution_history.get(execution_id)
                if not execution:
                    return False

                # Attempt refund via API
                try:
                    await self._api_refund(execution["order_id"])
                    return True
                except:
                    return False
        """
        pass

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Main execution with approval workflow.

        Orchestrates: validation → cost estimation → approval → execution → audit log

        This method is called by the plugin system. It handles the entire
        approval workflow before calling execute_action().

        Args:
            params: Tool parameters
            context: Execution context

        Returns:
            ToolResult with execution outcome
        """
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        # Step 1: Validate parameters
        is_valid, error = self.validate_params(params)
        if not is_valid:
            core_logging.log_event("action_validation_failed", {
                "action": self.get_manifest().name,
                "error": error
            })
            return ToolResult(
                success=False,
                error=f"Parameter validation failed: {error}"
            )

        # Step 2: Estimate cost
        try:
            cost = await self.estimate_cost(params)
        except Exception as e:
            core_logging.log_event("action_cost_estimation_failed", {
                "action": self.get_manifest().name,
                "error": str(e)
            })
            return ToolResult(
                success=False,
                error=f"Cost estimation failed: {str(e)}"
            )

        # Step 3: Check cost limits
        if context.max_cost_usd > 0 and cost > context.max_cost_usd:
            core_logging.log_event("action_cost_exceeded", {
                "action": self.get_manifest().name,
                "cost": cost,
                "limit": context.max_cost_usd
            })
            return ToolResult(
                success=False,
                error=f"Cost ${cost:.2f} exceeds limit ${context.max_cost_usd:.2f}"
            )

        # Step 4: Determine risk level
        risk = self._assess_risk(params, cost)

        # Step 5: Get approval if needed (and not dry run)
        if not context.dry_run and risk in [ActionRisk.MEDIUM, ActionRisk.HIGH, ActionRisk.CRITICAL]:
            approval_request = ActionApproval(
                action_name=self.get_manifest().name,
                description=self._format_action_description(params),
                cost_usd=cost,
                risk_level=risk,
                details=params,
                requires_2fa=(risk == ActionRisk.CRITICAL)
            )

            approved = await self._request_approval(approval_request, context)

            if not approved:
                core_logging.log_event("action_declined", {
                    "action": self.get_manifest().name,
                    "cost": cost,
                    "risk": risk.value,
                    "approval_id": approval_request.approval_id
                })
                return ToolResult(
                    success=False,
                    error="Action declined by user",
                    metadata={
                        "approval_id": approval_request.approval_id,
                        "cost": cost,
                        "risk": risk.value
                    }
                )

        # Step 6: Handle dry run
        if context.dry_run:
            core_logging.log_event("action_dry_run", {
                "action": self.get_manifest().name,
                "cost": cost,
                "risk": risk.value
            })
            return ToolResult(
                success=True,
                data={"simulated": True, "estimated_cost": cost},
                metadata={
                    "dry_run": True,
                    "risk": risk.value,
                    "would_require_approval": risk in [ActionRisk.MEDIUM, ActionRisk.HIGH, ActionRisk.CRITICAL]
                }
            )

        # Step 7: Execute action
        try:
            result = await self.execute_action(params, context)

            # Store execution history for rollback
            self._execution_history[execution_id] = {
                "params": params,
                "result": result.data,
                "cost": cost,
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "user_id": context.user_id,
                    "mission_id": context.mission_id
                }
            }

            # Step 8: Audit log
            await self._audit_log(execution_id, params, result, cost, context)

            # Add execution_id to result metadata
            if result.success:
                result.metadata["execution_id"] = execution_id
                result.metadata["cost"] = cost
                result.metadata["risk"] = risk.value

            return result

        except Exception as e:
            core_logging.log_event("action_failed", {
                "action": self.get_manifest().name,
                "error": str(e),
                "execution_id": execution_id
            })
            return ToolResult(
                success=False,
                error=f"Action execution failed: {str(e)}",
                metadata={"execution_id": execution_id, "exception_type": type(e).__name__}
            )

    async def _request_approval(
        self,
        approval: ActionApproval,
        context: ToolExecutionContext
    ) -> bool:
        """
        Request user approval via agent messaging system.

        Returns True if approved, False if declined.

        Args:
            approval: Approval request details
            context: Execution context

        Returns:
            True if approved, False otherwise
        """
        try:
            from agent.agent_messaging import AgentRole, get_message_bus

            message_bus = get_message_bus()

            # Format approval message
            message = self._format_approval_message(approval)

            # Request via message bus
            response = await message_bus.post_message(
                role=AgentRole.MANAGER,
                content=message,
                metadata={
                    "type": "approval_request",
                    "approval_id": approval.approval_id,
                    "action": approval.action_name,
                    "cost": approval.cost_usd,
                    "risk": approval.risk_level.value,
                    "requires_2fa": approval.requires_2fa
                },
                requires_response=True,
                response_timeout=300  # 5 minutes
            )

            # Parse response
            if response:
                response_lower = response.lower().strip()
                approved = response_lower in ["yes", "approve", "y", "approved", "ok"]

                core_logging.log_event("approval_response_received", {
                    "approval_id": approval.approval_id,
                    "approved": approved,
                    "response": response
                })

                return approved

            # Timeout or no response = declined
            return False

        except Exception as e:
            core_logging.log_event("approval_request_failed", {
                "approval_id": approval.approval_id,
                "error": str(e)
            })
            # On error, default to declining for safety
            return False

    def _format_approval_message(self, approval: ActionApproval) -> str:
        """
        Format user-friendly approval message.

        Args:
            approval: Approval request

        Returns:
            Formatted message string
        """
        msg = f"⚠️ Action Approval Required\n\n"
        msg += f"Action: {approval.action_name}\n"
        msg += f"Description: {approval.description}\n"

        if approval.cost_usd is not None and approval.cost_usd > 0:
            msg += f"Cost: ${approval.cost_usd:.2f}\n"

        msg += f"Risk Level: {approval.risk_level.value.upper()}\n"

        if approval.requires_2fa:
            msg += f"⚠️ Requires 2FA: Yes\n"

        msg += "\n"
        msg += "Details:\n"
        for key, value in approval.details.items():
            msg += f"  {key}: {value}\n"

        msg += "\nApprove this action? [yes/no]"

        return msg

    def _format_action_description(self, params: Dict[str, Any]) -> str:
        """
        Format human-readable action description.

        Override this for better descriptions.

        Args:
            params: Tool parameters

        Returns:
            Human-readable description
        """
        manifest = self.get_manifest()
        return f"{manifest.description} with params: {params}"

    async def _audit_log(
        self,
        execution_id: str,
        params: Dict[str, Any],
        result: ToolResult,
        cost: float,
        context: ToolExecutionContext
    ):
        """
        Log action execution to audit trail.

        Args:
            execution_id: Unique execution identifier
            params: Tool parameters
            result: Execution result
            cost: Actual or estimated cost
            context: Execution context
        """
        core_logging.log_event("action_executed", {
            "execution_id": execution_id,
            "action": self.get_manifest().name,
            "params": params,
            "success": result.success,
            "cost": cost,
            "user_id": context.user_id,
            "mission_id": context.mission_id,
            "timestamp": datetime.now().isoformat(),
            "error": result.error if not result.success else None
        })

    def _assess_risk(self, params: Dict[str, Any], cost: float) -> ActionRisk:
        """
        Assess risk level of action.

        Override this method for custom risk assessment.

        Default logic:
        - CRITICAL: cost > $100
        - HIGH: cost > $10
        - MEDIUM: cost > $1
        - LOW: cost <= $1

        Args:
            params: Tool parameters
            cost: Estimated cost

        Returns:
            ActionRisk level
        """
        if cost > 100:
            return ActionRisk.CRITICAL
        elif cost > 10:
            return ActionRisk.HIGH
        elif cost > 1:
            return ActionRisk.MEDIUM
        else:
            return ActionRisk.LOW

    def get_execution_history(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution history for rollback.

        Args:
            execution_id: Execution identifier

        Returns:
            Execution data if found, None otherwise
        """
        return self._execution_history.get(execution_id)
