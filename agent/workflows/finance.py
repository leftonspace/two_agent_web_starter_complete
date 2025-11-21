"""
PHASE 4.2: Finance Workflow

Workflow for financial analysis and reporting missions.
"""

from __future__ import annotations

from .base import Workflow, WorkflowStep


class FinanceWorkflow(Workflow):
    """
    Workflow for finance missions.

    Includes:
    - Data validation
    - Calculation verification
    - Compliance checks
    - Report formatting
    - Data specialist review
    """

    def _build_steps(self) -> None:
        """Build finance workflow steps."""
        self.steps = [
            WorkflowStep(
                name="Data Validation",
                action="qa_check",
                config={"check_type": "data_integrity"},
            ),
            WorkflowStep(
                name="Calculation Verification",
                action="qa_check",
                config={"check_type": "calculations"},
            ),
            WorkflowStep(
                name="Compliance Check",
                action="qa_check",
                config={"check_type": "compliance", "standards": ["GAAP", "IFRS"]},
            ),
            WorkflowStep(
                name="Data Specialist Review",
                action="specialist_pass",
                config={"specialist_type": "data"},
            ),
        ]
