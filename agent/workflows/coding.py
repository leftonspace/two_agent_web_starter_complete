"""
PHASE 4.2: Coding Workflow

Workflow for coding/software development missions.
"""

from __future__ import annotations

from .base import Workflow, WorkflowStep


class CodingWorkflow(Workflow):
    """
    Workflow for coding missions.

    Includes:
    - Syntax validation
    - Linting (ruff/eslint)
    - Unit tests
    - Security checks
    - Code formatting
    - Specialist reviews (frontend, backend, security)
    """

    def _build_steps(self) -> None:
        """Build coding workflow steps."""
        self.steps = [
            WorkflowStep(
                name="Syntax Check",
                action="qa_check",
                config={"check_type": "syntax"},
            ),
            WorkflowStep(
                name="Run Linter",
                action="tool_call",
                config={"tool_name": "format_code", "formatter": "ruff"},
            ),
            WorkflowStep(
                name="Run Unit Tests",
                action="tool_call",
                config={"tool_name": "run_unit_tests"},
            ),
            WorkflowStep(
                name="Security Audit",
                action="specialist_pass",
                config={"specialist_type": "security"},
            ),
            WorkflowStep(
                name="Code Review",
                action="specialist_pass",
                config={"specialist_type": "qa"},
            ),
        ]
