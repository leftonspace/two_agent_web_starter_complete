"""
PHASE 4.2: Legal Workflow

Workflow for legal document and compliance missions.
"""

from __future__ import annotations

from .base import Workflow, WorkflowStep


class LegalWorkflow(Workflow):
    """
    Workflow for legal missions.

    Includes:
    - Document structure validation
    - Citation verification
    - Compliance checks
    - Terminology consistency
    """

    def _build_steps(self) -> None:
        """Build legal workflow steps."""
        self.steps = [
            WorkflowStep(
                name="Document Structure",
                action="qa_check",
                config={"check_type": "structure"},
            ),
            WorkflowStep(
                name="Citation Verification",
                action="qa_check",
                config={"check_type": "citations"},
            ),
            WorkflowStep(
                name="Compliance Check",
                action="qa_check",
                config={"check_type": "legal_compliance"},
            ),
        ]
