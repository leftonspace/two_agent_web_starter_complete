"""
Action Execution Tools

PHASE 7.4: Tools that interact with external services to perform real-world actions.

Action tools can:
- Execute paid operations (domain purchases, server provisioning)
- Modify external systems (deploy websites, create databases)
- Send notifications (email, SMS, push)

All actions require audit logging and may require user approval.
"""

from agent.tools.actions.base import ActionTool, ActionRisk, ActionApproval

__all__ = [
    "ActionTool",
    "ActionRisk",
    "ActionApproval",
]
