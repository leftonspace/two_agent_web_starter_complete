"""
PHASE 4.2: Domain-Specific Workflow Modules

This package contains domain-specific QA pipelines and specialist workflows.
Each domain (coding, finance, legal, HR, ops) has its own workflow module
that defines quality checks, tool invocations, and specialist passes.

Usage:
    >>> from agent.workflows import get_workflow_for_domain
    >>> workflow = get_workflow_for_domain("coding")
    >>> result = workflow.run(mission_context)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type

from .base import Workflow
from .coding import CodingWorkflow
from .finance import FinanceWorkflow
from .hr import HRWorkflow
from .legal import LegalWorkflow
from .ops import OpsWorkflow


# Workflow registry mapping domains to workflow classes
WORKFLOW_REGISTRY: Dict[str, Type[Workflow]] = {
    "coding": CodingWorkflow,
    "web": CodingWorkflow,  # Alias for coding
    "finance": FinanceWorkflow,
    "legal": LegalWorkflow,
    "hr": HRWorkflow,
    "ops": OpsWorkflow,
}


def get_workflow_for_domain(domain: str) -> Optional[Workflow]:
    """
    Get the workflow instance for a specific domain.

    Args:
        domain: Domain string (e.g., "coding", "finance", "legal")

    Returns:
        Workflow instance or None if no workflow defined for domain
    """
    domain_lower = domain.lower()
    workflow_class = WORKFLOW_REGISTRY.get(domain_lower)

    if workflow_class:
        return workflow_class()

    return None


__all__ = [
    "Workflow",
    "CodingWorkflow",
    "FinanceWorkflow",
    "LegalWorkflow",
    "HRWorkflow",
    "OpsWorkflow",
    "get_workflow_for_domain",
]
