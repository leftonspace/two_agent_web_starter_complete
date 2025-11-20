"""
PHASE 1.1: Domain Classification System
PHASE 2.5: Role-Based Department Profile Integration

This module provides domain-agnostic routing for the multi-agent orchestrator.
Tasks are classified into domains, and each domain has specialized prompts and tools.

Supported Domains:
- CODING: Software development, web apps, APIs
- FINANCE: Financial analysis, budgeting, forecasting
- LEGAL: Contract review, compliance, documentation
- HR: Human resources, hiring, employee relations
- OPS: Operations, logistics, process optimization
- MARKETING: Content creation, campaigns, copywriting
- RESEARCH: Data analysis, literature review, fact-finding
- GENERIC: Catch-all for tasks that don't fit other domains
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

# ══════════════════════════════════════════════════════════════════════
# Domain Enum
# ══════════════════════════════════════════════════════════════════════


class Domain(str, Enum):
    """Task domain categories."""

    CODING = "coding"
    FINANCE = "finance"
    LEGAL = "legal"
    HR = "hr"
    OPS = "ops"
    MARKETING = "marketing"
    RESEARCH = "research"
    GENERIC = "generic"


# ══════════════════════════════════════════════════════════════════════
# Domain Keywords
# ══════════════════════════════════════════════════════════════════════

# Keywords that strongly indicate a specific domain
DOMAIN_KEYWORDS: Dict[Domain, Set[str]] = {
    Domain.CODING: {
        "code",
        "programming",
        "software",
        "website",
        "app",
        "application",
        "api",
        "backend",
        "frontend",
        "database",
        "script",
        "function",
        "debug",
        "test",
        "deploy",
        "build",
        "refactor",
        "bug",
        "feature",
        "html",
        "css",
        "javascript",
        "python",
        "typescript",
        "react",
        "node",
        "server",
        "endpoint",
        "ui",
        "ux",
    },
    Domain.FINANCE: {
        "financial",
        "budget",
        "forecast",
        "revenue",
        "cost",
        "profit",
        "loss",
        "roi",
        "investment",
        "accounting",
        "bookkeeping",
        "expense",
        "invoice",
        "payroll",
        "tax",
        "spreadsheet",
        "financial model",
        "valuation",
        "cash flow",
        "balance sheet",
        "p&l",
        "income statement",
    },
    Domain.LEGAL: {
        "legal",
        "contract",
        "agreement",
        "terms",
        "compliance",
        "regulation",
        "policy",
        "privacy",
        "gdpr",
        "terms of service",
        "tos",
        "liability",
        "indemnity",
        "warranty",
        "clause",
        "jurisdiction",
        "arbitration",
        "license",
        "copyright",
        "trademark",
    },
    Domain.HR: {
        "hr",
        "human resources",
        "hiring",
        "recruitment",
        "recruiting",
        "candidate",
        "interview",
        "onboarding",
        "employee",
        "compensation",
        "benefits",
        "payroll",
        "performance review",
        "performance management",
        "talent",
        "workforce",
        "job description",
        "offer letter",
        "termination",
        "hris",
        "ats",
        "applicant tracking",
    },
    Domain.OPS: {
        "operations",
        "process",
        "workflow",
        "logistics",
        "supply chain",
        "inventory",
        "scheduling",
        "planning",
        "optimization",
        "efficiency",
        "automation",
        "sop",
        "standard operating procedure",
        "deployment",
        "infrastructure",
        "monitoring",
        "alerting",
        "incident",
        "runbook",
    },
    Domain.MARKETING: {
        "marketing",
        "content",
        "copy",
        "copywriting",
        "campaign",
        "advertising",
        "social media",
        "seo",
        "email",
        "newsletter",
        "landing page",
        "conversion",
        "cta",
        "call to action",
        "branding",
        "messaging",
        "value proposition",
        "target audience",
        "persona",
        "blog",
        "article",
    },
    Domain.RESEARCH: {
        "research",
        "analysis",
        "analyze",
        "study",
        "investigate",
        "data",
        "statistics",
        "survey",
        "report",
        "findings",
        "insights",
        "trends",
        "patterns",
        "literature review",
        "fact-finding",
        "competitive analysis",
        "market research",
        "user research",
    },
}


# ══════════════════════════════════════════════════════════════════════
# Domain Classification
# ══════════════════════════════════════════════════════════════════════


def classify_task(task: str) -> Domain:
    """
    Classify a task description into a domain.

    Uses keyword matching to determine the most likely domain.
    Returns GENERIC if no strong match is found.

    Args:
        task: Task description string

    Returns:
        Classified domain

    Examples:
        >>> classify_task("Build a React website with user authentication")
        Domain.CODING

        >>> classify_task("Create a financial forecast for Q1 2025")
        Domain.FINANCE

        >>> classify_task("Write blog posts about healthy eating")
        Domain.MARKETING
    """
    task_lower = task.lower()

    # Count keyword matches per domain
    domain_scores: Dict[Domain, int] = {domain: 0 for domain in Domain}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in task_lower:
                domain_scores[domain] += 1

    # Find domain with highest score
    max_score = max(domain_scores.values())

    if max_score == 0:
        # No matches - classify as generic
        return Domain.GENERIC

    # Return domain with highest score
    for domain, score in domain_scores.items():
        if score == max_score:
            return domain

    return Domain.GENERIC


# ══════════════════════════════════════════════════════════════════════
# Domain-Specific Prompts
# ══════════════════════════════════════════════════════════════════════


def get_domain_prompts(domain: Domain) -> Dict[str, str]:
    """
    Get domain-specific prompt additions for each role.

    These prompt snippets are appended to the base system prompts
    to specialize agent behavior for the domain.

    Args:
        domain: Task domain

    Returns:
        Dict mapping role -> prompt snippet
    """
    if domain == Domain.CODING:
        return {
            "manager": """
You are planning a software development task.
Focus on:
- Clear technical requirements
- User stories and acceptance criteria
- Testing strategy
- Security considerations
- Performance requirements
""",
            "supervisor": """
Break down the coding task into logical phases:
- Setup/infrastructure
- Core functionality
- UI/UX implementation
- Testing and validation
- Documentation
""",
            "employee": """
Write clean, well-documented code following best practices:
- Use meaningful variable names
- Add comments for complex logic
- Follow language conventions
- Include error handling
- Write testable code
""",
        }

    elif domain == Domain.FINANCE:
        return {
            "manager": """
You are planning a financial analysis task.
Focus on:
- Data sources and accuracy
- Assumptions and constraints
- Key metrics to track
- Visualization needs
- Compliance requirements
""",
            "supervisor": """
Structure the financial work:
- Data collection and validation
- Calculations and formulas
- Analysis and interpretation
- Reporting and visualization
""",
            "employee": """
Create accurate financial deliverables:
- Double-check all calculations
- Document assumptions clearly
- Use standard financial formats
- Include data sources
- Highlight key insights
""",
        }

    elif domain == Domain.LEGAL:
        return {
            "manager": """
You are planning legal documentation work.
Focus on:
- Regulatory requirements
- Risk mitigation
- Clear definitions
- Compliance standards
- Review process
""",
            "supervisor": """
Organize legal work:
- Research and reference gathering
- Drafting key clauses
- Review and validation
- Finalization and formatting
""",
            "employee": """
Create clear, precise legal content:
- Use precise language
- Define all terms
- Reference relevant laws/regulations
- Note any disclaimers
- Maintain professional tone
""",
        }

    elif domain == Domain.OPS:
        return {
            "manager": """
You are planning an operations task.
Focus on:
- Process efficiency
- Resource optimization
- Success metrics
- Stakeholder coordination
- Risk management
""",
            "supervisor": """
Structure operational work:
- Current state analysis
- Process design
- Implementation steps
- Monitoring and optimization
""",
            "employee": """
Create practical operational deliverables:
- Step-by-step procedures
- Clear responsibilities
- Measurable outcomes
- Contingency plans
- Documentation for handoff
""",
        }

    elif domain == Domain.MARKETING:
        return {
            "manager": """
You are planning a marketing task.
Focus on:
- Target audience
- Key messaging
- Brand consistency
- Conversion goals
- Success metrics
""",
            "supervisor": """
Organize marketing work:
- Audience research
- Content strategy
- Creation and design
- Review and optimization
""",
            "employee": """
Create compelling marketing content:
- Clear value propositions
- Engaging headlines
- Benefit-focused copy
- Strong calls-to-action
- Brand-appropriate tone
""",
        }

    elif domain == Domain.RESEARCH:
        return {
            "manager": """
You are planning a research task.
Focus on:
- Research questions
- Data sources and methods
- Analysis approach
- Validation criteria
- Reporting format
""",
            "supervisor": """
Structure research work:
- Question refinement
- Data collection
- Analysis and synthesis
- Reporting and recommendations
""",
            "employee": """
Conduct thorough research:
- Use credible sources
- Document methodology
- Present findings objectively
- Note limitations
- Provide actionable insights
""",
        }

    else:  # Domain.GENERIC
        return {
            "manager": "Focus on clear planning and measurable outcomes.",
            "supervisor": "Break down the work into logical, manageable phases.",
            "employee": "Deliver high-quality work with clear documentation.",
        }


# ══════════════════════════════════════════════════════════════════════
# Domain-Specific Tools
# ══════════════════════════════════════════════════════════════════════


def get_domain_tools(domain: Domain) -> List[str]:
    """
    Get the list of allowed tools for a domain.

    Tools are filtered to prevent inappropriate operations
    (e.g., no file writes for research tasks).

    Args:
        domain: Task domain

    Returns:
        List of tool names allowed for this domain
    """
    # Core tools available to all domains
    core_tools = [
        "read_file",
        "list_directory",
        "search_files",
    ]

    if domain == Domain.CODING:
        return core_tools + [
            "write_file",
            "run_command",
            # PHASE 3.1: Sandbox tools for coding
            "sandbox_run_python",
            "sandbox_run_node",
            "sandbox_run_script",
            "git_commit",
            "git_diff",
            "run_tests",
        ]

    elif domain == Domain.FINANCE:
        return core_tools + [
            "write_file",
            "read_spreadsheet",
            "write_spreadsheet",
            "calculate",
            # PHASE 3.1: Python sandbox for data analysis
            "sandbox_run_python",
        ]

    elif domain == Domain.LEGAL:
        return core_tools + [
            "write_file",
            "search_regulations",
            "format_document",
        ]

    elif domain == Domain.OPS:
        return core_tools + [
            "write_file",
            "run_command",
            "schedule_task",
            "notify",
        ]

    elif domain == Domain.MARKETING:
        return core_tools + [
            "write_file",
            "generate_image",  # Future: DALL-E integration
            "check_seo",
            "analyze_readability",
        ]

    elif domain == Domain.RESEARCH:
        return core_tools + [
            "write_file",
            "web_search",
            "fetch_url",
            "summarize_document",
            # PHASE 3.1: Python sandbox for analysis
            "sandbox_run_python",
        ]

    else:  # Domain.GENERIC
        return core_tools + [
            "write_file",
        ]


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def get_domain_info(task: str) -> Dict[str, any]:
    """
    Get complete domain classification info for a task.

    Convenience function that returns domain, prompts, and tools together.

    Args:
        task: Task description

    Returns:
        Dict with domain, prompts, and tools

    Example:
        >>> info = get_domain_info("Build a React app")
        >>> info['domain']
        Domain.CODING
        >>> 'sandbox_run_python' in info['tools']
        True
    """
    domain = classify_task(task)

    return {
        "domain": domain,
        "domain_name": domain.value,
        "prompts": get_domain_prompts(domain),
        "tools": get_domain_tools(domain),
    }


# ══════════════════════════════════════════════════════════════════════
# PHASE 4.2: Workflow Integration
# ══════════════════════════════════════════════════════════════════════


def get_workflow_for_domain(domain: Domain):
    """
    Get the workflow module for a specific domain.

    PHASE 4.2: Maps domains to their corresponding workflow implementations.

    Args:
        domain: The domain enum

    Returns:
        Workflow instance or None if no workflow defined

    Example:
        >>> workflow = get_workflow_for_domain(Domain.CODING)
        >>> if workflow:
        ...     result = workflow.run(mission_context)
    """
    try:
        from agent.workflows import get_workflow_for_domain as get_workflow
        return get_workflow(domain.value)
    except ImportError:
        # Workflows not available
        return None


# ══════════════════════════════════════════════════════════════════════
# PHASE 2.5: Role Selection Integration
# ══════════════════════════════════════════════════════════════════════


def select_role_for_task(task: str, department: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Select the best role for a task based on domain classification and expertise matching.

    PHASE 2.5: Integrates role system with domain routing. If department is not specified,
    it will be inferred from domain classification.

    Args:
        task: Task description
        department: Optional department name (hr, finance, legal). If None, inferred from domain.

    Returns:
        Tuple of (role_id, department_name). Returns (None, department) if no role found.

    Example:
        >>> role_id, dept = select_role_for_task("Screen candidates for software engineer position")
        >>> print(role_id)  # "hr_recruiter"
        >>> print(dept)     # "hr"

        >>> role_id, dept = select_role_for_task("Review employment contract", department="legal")
        >>> print(role_id)  # "legal_counsel"
    """
    # If department not specified, infer from domain classification
    if department is None:
        domain = classify_task(task)
        # Map domain to department
        domain_to_dept = {
            Domain.HR: "hr",
            Domain.FINANCE: "finance",
            Domain.LEGAL: "legal",
        }
        department = domain_to_dept.get(domain, "generic")

    # Only use role system for departments that have role definitions
    if department not in ["hr", "finance", "legal"]:
        return None, department

    # Import role registry (lazy import to avoid circular dependencies)
    try:
        from agent.roles import get_role_registry

        registry = get_role_registry()
        role_id = registry.select_role_for_task(task, department)

        return role_id, department
    except ImportError:
        # Role system not available
        return None, department
    except Exception as e:
        # Fallback gracefully if role selection fails
        print(f"[RoleSelection] Warning: Failed to select role: {e}")
        return None, department


def get_role_and_domain_info(task: str, department: Optional[str] = None) -> Dict[str, any]:
    """
    Get comprehensive domain and role information for a task.

    PHASE 2.5: Combines domain classification with role selection to provide
    complete routing information.

    Args:
        task: Task description
        department: Optional department override

    Returns:
        Dict with domain, role, prompts, tools, and role profile

    Example:
        >>> info = get_role_and_domain_info("Create offer letter for new hire")
        >>> info['domain']
        Domain.HR
        >>> info['role_id']
        'hr_hiring_manager'
        >>> info['role_profile'].role_name
        'Hiring Manager'
    """
    # Get domain info
    domain_info = get_domain_info(task)

    # Get role selection
    role_id, dept = select_role_for_task(task, department)

    # Get role profile if role selected
    role_profile = None
    if role_id:
        try:
            from agent.roles import get_role_registry
            registry = get_role_registry()
            role_profile = registry.get_role(role_id)
        except ImportError:
            pass

    return {
        **domain_info,
        "department": dept,
        "role_id": role_id,
        "role_profile": role_profile,
    }
