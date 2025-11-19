"""
PHASE 4.2: HR Workflow

Workflow for human resources and people operations missions.
"""

from __future__ import annotations

from .base import Workflow, WorkflowStep


class HRWorkflow(Workflow):
    """
    Workflow for HR missions.

    Includes:
    - Policy compliance
    - Data privacy checks
    - Document formatting
    - Sensitivity review
    """

    def _build_steps(self) -> None:
        """Build HR workflow steps."""
        self.steps = [
            WorkflowStep(
                name="Policy Compliance",
                action="qa_check",
                config={"check_type": "hr_policy"},
            ),
            WorkflowStep(
                name="Data Privacy",
                action="qa_check",
                config={"check_type": "privacy", "standards": ["GDPR", "CCPA"]},
            ),
            WorkflowStep(
                name="Sensitivity Review",
                action="qa_check",
                config={"check_type": "sensitivity"},
            ),
        ]
