"""
PHASE 4.2: Base Workflow Class

Defines the base class for domain-specific workflows.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.

    Attributes:
        name: Step name
        action: Action type (e.g., "qa_check", "tool_call", "specialist_pass")
        config: Step-specific configuration
    """
    name: str
    action: str
    config: Dict[str, Any]


class Workflow(ABC):
    """
    Base class for domain-specific workflows.

    Each workflow defines a sequence of QA checks, tool invocations,
    and specialist passes appropriate for its domain.
    """

    def __init__(self):
        """Initialize workflow."""
        self.steps: List[WorkflowStep] = []
        self._build_steps()

    @abstractmethod
    def _build_steps(self) -> None:
        """
        Build the workflow steps.

        Subclasses must implement this to define their specific pipeline.
        """
        pass

    def run(self, mission_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.

        Args:
            mission_context: Context including mission_id, task, domain, files, etc.

        Returns:
            Workflow result with QA findings, tool outputs, specialist feedback

        PHASE 4.3 (R6): Workflow failures are tracked and can block execution
        based on workflow_enforcement config setting.
        """
        results = {
            "workflow_name": self.__class__.__name__,
            "steps_completed": [],
            "steps_failed": [],
            "qa_findings": [],
            "specialist_feedback": [],
            "has_failures": False,  # PHASE 4.3 (R6): Track if any steps failed
            "enforcement_level": "warn",  # Default to warn mode
        }

        for step in self.steps:
            try:
                step_result = self._execute_step(step, mission_context)
                results["steps_completed"].append({
                    "step": step.name,
                    "action": step.action,
                    "result": step_result,
                })

                # PHASE 4.3 (R6): Track step failures
                if step_result.get("status") in ["failed", "error"]:
                    results["has_failures"] = True

            except Exception as e:
                results["steps_failed"].append({
                    "step": step.name,
                    "error": str(e),
                })
                results["has_failures"] = True  # PHASE 4.3 (R6)

        return results

    def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: Step to execute
            context: Mission context

        Returns:
            Step execution result
        """
        if step.action == "qa_check":
            return self._run_qa_check(step.config, context)
        elif step.action == "tool_call":
            return self._run_tool(step.config, context)
        elif step.action == "specialist_pass":
            return self._run_specialist(step.config, context)
        else:
            return {"status": "skipped", "reason": f"Unknown action: {step.action}"}

    def _run_qa_check(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a QA check."""
        return {"status": "passed", "checks": []}

    def _run_tool(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a tool."""
        return {"status": "completed", "tool": config.get("tool_name")}

    def _run_specialist(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specialist pass."""
        return {"status": "completed", "specialist": config.get("specialist_type")}
