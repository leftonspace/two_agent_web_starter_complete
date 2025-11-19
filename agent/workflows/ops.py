"""
PHASE 4.2: Operations Workflow

Workflow for operations and infrastructure missions.
"""

from __future__ import annotations

from .base import Workflow, WorkflowStep


class OpsWorkflow(Workflow):
    """
    Workflow for operations missions.

    Includes:
    - Configuration validation
    - Infrastructure checks
    - Security audit
    - DevOps specialist review
    """

    def _build_steps(self) -> None:
        """Build ops workflow steps."""
        self.steps = [
            WorkflowStep(
                name="Configuration Validation",
                action="qa_check",
                config={"check_type": "config"},
            ),
            WorkflowStep(
                name="Infrastructure Check",
                action="qa_check",
                config={"check_type": "infrastructure"},
            ),
            WorkflowStep(
                name="Security Audit",
                action="specialist_pass",
                config={"specialist_type": "security"},
            ),
            WorkflowStep(
                name="DevOps Review",
                action="specialist_pass",
                config={"specialist_type": "devops"},
            ),
        ]
