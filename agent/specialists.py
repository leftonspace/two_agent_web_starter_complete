"""
PHASE 4.1: Specialist Agent System

Defines specialist agents with specific expertise:
- Frontend Specialist (React, Vue, CSS, UX)
- Backend Specialist (APIs, databases, services)
- Data Specialist (Analytics, ML, data pipelines)
- Security Specialist (Auth, encryption, vulnerabilities)
- DevOps Specialist (CI/CD, deployment, infrastructure)
- QA Specialist (Testing, quality assurance, automation)

Each specialist has:
- Expertise domains
- Specialized prompts
- Tool preferences
- Cost multiplier (specialists may cost more)

Usage:
    >>> from agent import specialists
    >>> spec = specialists.get_specialist("frontend")
    >>> spec.get_system_prompt(task="Build a React dashboard")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# PHASE 1.3: Import prompt security for injection defense (V3)
import prompt_security


# ══════════════════════════════════════════════════════════════════════
# Specialist Types
# ══════════════════════════════════════════════════════════════════════


class SpecialistType(str, Enum):
    """Types of specialist agents."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    DATA = "data"
    SECURITY = "security"
    DEVOPS = "devops"
    QA = "qa"
    FULLSTACK = "fullstack"
    GENERIC = "generic"
    # PHASE 4.1: Additional specialist types
    CONTENT_WRITER = "content_writer"
    RESEARCHER = "researcher"


# ══════════════════════════════════════════════════════════════════════
# Specialist Definitions
# ══════════════════════════════════════════════════════════════════════


@dataclass
class SpecialistProfile:
    """Profile for a specialist agent."""

    name: str
    specialist_type: SpecialistType
    expertise: List[str]  # Areas of expertise
    tools: List[str]  # Preferred tools
    keywords: List[str]  # Keywords for task matching
    cost_multiplier: float = 1.0  # Cost adjustment (1.0 = normal, 1.5 = 50% more expensive)
    complexity_threshold: str = "low"  # Minimum complexity to use this specialist
    system_prompt_additions: str = ""  # Additional system prompt content

    def matches_task(self, task: str) -> float:
        """
        Calculate how well this specialist matches a task.

        Args:
            task: Task description

        Returns:
            Match score (0.0 to 1.0, higher is better)
        """
        task_lower = task.lower()
        score = 0.0

        # Check keyword matches
        keyword_matches = sum(1 for kw in self.keywords if kw.lower() in task_lower)
        if keyword_matches > 0:
            score += min(keyword_matches * 0.2, 0.6)  # Max 0.6 from keywords

        # Check expertise matches
        expertise_matches = sum(1 for exp in self.expertise if exp.lower() in task_lower)
        if expertise_matches > 0:
            score += min(expertise_matches * 0.15, 0.4)  # Max 0.4 from expertise

        return min(score, 1.0)

    def get_system_prompt(self, task: str) -> str:
        """
        Get the system prompt for this specialist.

        PHASE 1.3: Sanitize task and system_prompt_additions to prevent injection (V3)

        Args:
            task: Task description

        Returns:
            System prompt string
        """
        # PHASE 1.3: Sanitize task input to prevent prompt injection (V3)
        sanitized_task = prompt_security.sanitize_user_input(
            task,
            context="specialist_task"
        )

        # PHASE 1.3: Sanitize system_prompt_additions as defense-in-depth
        # (Currently hardcoded, but protects if made user-configurable in future)
        sanitized_additions = prompt_security.sanitize_user_input(
            self.system_prompt_additions,
            context="specialist_system_prompt_additions"
        )

        # Build structured prompt with sanitized inputs
        base = f"""You are a {self.name} with deep expertise in {', '.join(self.expertise[:3])}.

Your specialized knowledge includes:
{chr(10).join(f'- {exp}' for exp in self.expertise)}

You have access to these preferred tools:
{chr(10).join(f'- {tool}' for tool in self.tools)}

When approaching tasks, you:
1. Apply best practices from your domain
2. Consider performance, security, and maintainability
3. Leverage your specialized tools effectively
4. Provide expert-level solutions

<task_description>
{sanitized_task}
</task_description>

{sanitized_additions}"""

        return base


# ══════════════════════════════════════════════════════════════════════
# Specialist Registry
# ══════════════════════════════════════════════════════════════════════


SPECIALIST_REGISTRY: Dict[SpecialistType, SpecialistProfile] = {
    SpecialistType.FRONTEND: SpecialistProfile(
        name="Frontend Specialist",
        specialist_type=SpecialistType.FRONTEND,
        expertise=[
            "React, Vue, Angular frameworks",
            "Modern CSS (Flexbox, Grid, Tailwind)",
            "JavaScript/TypeScript",
            "Component architecture",
            "State management (Redux, Zustand)",
            "Responsive design",
            "Accessibility (a11y)",
            "Performance optimization",
            "Browser compatibility",
        ],
        tools=[
            "npm",
            "webpack",
            "vite",
            "eslint",
            "prettier",
            "chrome devtools",
        ],
        keywords=[
            "react", "vue", "angular", "frontend", "ui", "ux",
            "css", "tailwind", "bootstrap", "component", "dashboard",
            "form", "navigation", "responsive", "mobile",
        ],
        cost_multiplier=1.2,
        complexity_threshold="medium",
        system_prompt_additions="""
Focus on:
- Clean, reusable component structure
- Semantic HTML and accessibility
- Responsive design patterns
- User experience best practices
- Modern CSS methodologies
""",
    ),

    SpecialistType.BACKEND: SpecialistProfile(
        name="Backend Specialist",
        specialist_type=SpecialistType.BACKEND,
        expertise=[
            "RESTful API design",
            "GraphQL",
            "Database design (SQL, NoSQL)",
            "Authentication & authorization",
            "Caching strategies",
            "Message queues",
            "Microservices architecture",
            "API security",
            "Performance optimization",
        ],
        tools=[
            "fastapi",
            "flask",
            "django",
            "postgresql",
            "redis",
            "docker",
        ],
        keywords=[
            "api", "backend", "server", "database", "endpoint",
            "rest", "graphql", "auth", "authentication", "jwt",
            "sql", "postgres", "mongo", "redis", "cache",
        ],
        cost_multiplier=1.2,
        complexity_threshold="medium",
        system_prompt_additions="""
Focus on:
- Scalable API design
- Proper error handling and validation
- Security best practices (OWASP)
- Database optimization
- Efficient data structures
""",
    ),

    SpecialistType.DATA: SpecialistProfile(
        name="Data Specialist",
        specialist_type=SpecialistType.DATA,
        expertise=[
            "Data analysis and visualization",
            "Machine learning pipelines",
            "ETL processes",
            "Statistical modeling",
            "Data cleaning and preprocessing",
            "Feature engineering",
            "Model evaluation",
            "Big data processing",
        ],
        tools=[
            "pandas",
            "numpy",
            "scikit-learn",
            "matplotlib",
            "jupyter",
            "sql",
        ],
        keywords=[
            "data", "analytics", "ml", "machine learning", "model",
            "prediction", "analysis", "visualization", "dashboard",
            "etl", "pipeline", "dataset", "feature", "training",
        ],
        cost_multiplier=1.3,
        complexity_threshold="high",
        system_prompt_additions="""
Focus on:
- Data quality and validation
- Reproducible analysis
- Clear visualizations
- Statistical rigor
- Model interpretability
""",
    ),

    SpecialistType.SECURITY: SpecialistProfile(
        name="Security Specialist",
        specialist_type=SpecialistType.SECURITY,
        expertise=[
            "OWASP Top 10 vulnerabilities",
            "Authentication mechanisms",
            "Encryption (at rest, in transit)",
            "Input validation and sanitization",
            "CSRF, XSS, SQL injection prevention",
            "Security headers",
            "Secrets management",
            "Penetration testing",
            "Compliance (GDPR, HIPAA)",
        ],
        tools=[
            "bandit",
            "safety",
            "owasp zap",
            "ssl labs",
        ],
        keywords=[
            "security", "auth", "encryption", "vulnerability",
            "xss", "csrf", "sql injection", "sanitize", "validate",
            "oauth", "jwt", "secret", "https", "ssl", "tls",
        ],
        cost_multiplier=1.4,
        complexity_threshold="medium",
        system_prompt_additions="""
Focus on:
- Defense in depth
- Principle of least privilege
- Secure by default
- Input validation everywhere
- Regular security audits
""",
    ),

    SpecialistType.DEVOPS: SpecialistProfile(
        name="DevOps Specialist",
        specialist_type=SpecialistType.DEVOPS,
        expertise=[
            "CI/CD pipelines",
            "Container orchestration (Docker, Kubernetes)",
            "Infrastructure as Code (Terraform, Ansible)",
            "Monitoring and logging",
            "Cloud platforms (AWS, GCP, Azure)",
            "Auto-scaling",
            "Deployment strategies",
            "Performance monitoring",
        ],
        tools=[
            "docker",
            "kubernetes",
            "terraform",
            "ansible",
            "github actions",
            "prometheus",
        ],
        keywords=[
            "devops", "ci/cd", "deployment", "docker", "kubernetes",
            "pipeline", "terraform", "ansible", "cloud", "aws",
            "monitoring", "logging", "infrastructure", "scale",
        ],
        cost_multiplier=1.3,
        complexity_threshold="high",
        system_prompt_additions="""
Focus on:
- Automation and repeatability
- Infrastructure as Code
- Observability (metrics, logs, traces)
- Scalability and resilience
- Cost optimization
""",
    ),

    SpecialistType.QA: SpecialistProfile(
        name="QA Specialist",
        specialist_type=SpecialistType.QA,
        expertise=[
            "Test strategy and planning",
            "Unit testing",
            "Integration testing",
            "End-to-end testing",
            "Performance testing",
            "Test automation",
            "Bug tracking and reporting",
            "Test coverage analysis",
        ],
        tools=[
            "pytest",
            "jest",
            "cypress",
            "selenium",
            "postman",
        ],
        keywords=[
            "test", "testing", "qa", "quality", "coverage",
            "unit test", "integration test", "e2e", "automation",
            "bug", "assertion", "mock", "fixture",
        ],
        cost_multiplier=1.1,
        complexity_threshold="low",
        system_prompt_additions="""
Focus on:
- Comprehensive test coverage
- Clear test documentation
- Fast, reliable tests
- Edge case handling
- Continuous testing
""",
    ),

    SpecialistType.FULLSTACK: SpecialistProfile(
        name="Full-Stack Specialist",
        specialist_type=SpecialistType.FULLSTACK,
        expertise=[
            "Frontend and backend development",
            "Database design",
            "API development",
            "User interface design",
            "System architecture",
            "End-to-end feature development",
        ],
        tools=[
            "react",
            "fastapi",
            "postgresql",
            "docker",
            "git",
        ],
        keywords=[
            "fullstack", "full stack", "full-stack", "end-to-end",
            "application", "web app", "complete", "entire",
        ],
        cost_multiplier=1.25,
        complexity_threshold="medium",
        system_prompt_additions="""
Focus on:
- End-to-end architecture
- Frontend-backend integration
- Consistent user experience
- Full-stack best practices
""",
    ),

    # PHASE 4.1: Additional specialists
    SpecialistType.CONTENT_WRITER: SpecialistProfile(
        name="Content Writer Specialist",
        specialist_type=SpecialistType.CONTENT_WRITER,
        expertise=[
            "Technical writing",
            "Documentation",
            "User guides and tutorials",
            "Marketing copy",
            "SEO optimization",
            "Content strategy",
            "Style guide compliance",
            "Accessibility in writing",
        ],
        tools=[
            "markdown",
            "grammarly",
            "hemingway editor",
            "google docs",
        ],
        keywords=[
            "content", "writing", "documentation", "docs", "readme",
            "tutorial", "guide", "copy", "blog", "article",
            "technical writing", "user guide", "manual",
        ],
        cost_multiplier=1.2,
        complexity_threshold="low",
        system_prompt_additions="""
Focus on:
- Clear, concise communication
- Audience-appropriate language
- Consistent tone and style
- Accessibility (plain language, readability)
- SEO best practices where applicable
""",
    ),

    SpecialistType.RESEARCHER: SpecialistProfile(
        name="Research Specialist",
        specialist_type=SpecialistType.RESEARCHER,
        expertise=[
            "Information gathering and synthesis",
            "Data analysis and interpretation",
            "Literature review",
            "Competitive analysis",
            "Market research",
            "Academic research methods",
            "Statistical analysis",
            "Report writing",
        ],
        tools=[
            "jupyter",
            "pandas",
            "matplotlib",
            "google scholar",
            "arxiv",
        ],
        keywords=[
            "research", "analysis", "study", "investigation",
            "survey", "data analysis", "literature review",
            "competitive analysis", "market research",
            "report", "findings", "insights",
        ],
        cost_multiplier=1.3,
        complexity_threshold="medium",
        system_prompt_additions="""
Focus on:
- Thorough information gathering
- Critical evaluation of sources
- Data-driven insights
- Clear presentation of findings
- Proper citation and attribution
- Objective analysis
""",
    ),

    SpecialistType.GENERIC: SpecialistProfile(
        name="Generic Specialist",
        specialist_type=SpecialistType.GENERIC,
        expertise=[
            "General software development",
            "Problem solving",
            "Code organization",
            "Documentation",
        ],
        tools=[
            "git",
            "editor",
        ],
        keywords=[],  # Matches nothing specifically
        cost_multiplier=1.0,
        complexity_threshold="low",
        system_prompt_additions="",
    ),
}


# ══════════════════════════════════════════════════════════════════════
# Specialist Selection
# ══════════════════════════════════════════════════════════════════════


def get_specialist(specialist_type: str) -> SpecialistProfile:
    """
    Get a specialist by type.

    Args:
        specialist_type: Specialist type string

    Returns:
        SpecialistProfile instance

    Raises:
        ValueError: If specialist type not found
    """
    try:
        spec_enum = SpecialistType(specialist_type)
        return SPECIALIST_REGISTRY[spec_enum]
    except (ValueError, KeyError):
        raise ValueError(f"Unknown specialist type: {specialist_type}")


def select_specialist_for_task(
    task: str,
    min_score: float = 0.3,
    max_specialists: int = 3
) -> List[tuple[SpecialistProfile, float]]:
    """
    Select the best specialist(s) for a task.

    Args:
        task: Task description
        min_score: Minimum match score (0.0 to 1.0)
        max_specialists: Maximum number of specialists to return

    Returns:
        List of (specialist, score) tuples, sorted by score descending
    """
    # Calculate match scores for all specialists
    scored = []
    for specialist in SPECIALIST_REGISTRY.values():
        if specialist.specialist_type == SpecialistType.GENERIC:
            continue  # Skip generic

        score = specialist.matches_task(task)
        if score >= min_score:
            scored.append((specialist, score))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Return top N
    return scored[:max_specialists]


def list_all_specialists() -> List[SpecialistProfile]:
    """
    Get all specialist profiles.

    Returns:
        List of all specialist profiles
    """
    return list(SPECIALIST_REGISTRY.values())


def get_specialists_for_domain(domain: str) -> List[SpecialistProfile]:
    """
    Get applicable specialists for a specific domain.

    PHASE 4.1: Returns specialists that are relevant for the given domain.

    Args:
        domain: Domain string (e.g., "coding", "finance", "research", "legal", "hr", "ops")

    Returns:
        List of SpecialistProfile instances applicable to the domain
    """
    domain_lower = domain.lower()

    # Map domains to relevant specialists
    domain_specialists = {
        "coding": [
            SpecialistType.FRONTEND,
            SpecialistType.BACKEND,
            SpecialistType.FULLSTACK,
            SpecialistType.SECURITY,
            SpecialistType.DEVOPS,
            SpecialistType.QA,
        ],
        "web": [
            SpecialistType.FRONTEND,
            SpecialistType.BACKEND,
            SpecialistType.FULLSTACK,
            SpecialistType.QA,
        ],
        "data": [
            SpecialistType.DATA,
            SpecialistType.BACKEND,
            SpecialistType.RESEARCHER,
        ],
        "security": [
            SpecialistType.SECURITY,
            SpecialistType.BACKEND,
        ],
        "devops": [
            SpecialistType.DEVOPS,
            SpecialistType.BACKEND,
        ],
        "testing": [
            SpecialistType.QA,
        ],
        # PHASE 4.1: Extended domain mappings
        "finance": [SpecialistType.DATA, SpecialistType.RESEARCHER],
        "research": [SpecialistType.RESEARCHER, SpecialistType.DATA],
        "legal": [SpecialistType.RESEARCHER, SpecialistType.SECURITY, SpecialistType.CONTENT_WRITER],
        "hr": [SpecialistType.CONTENT_WRITER],
        "ops": [SpecialistType.DEVOPS],
        "documentation": [SpecialistType.CONTENT_WRITER],
        "content": [SpecialistType.CONTENT_WRITER],
    }

    # Get specialists for this domain
    specialist_types = domain_specialists.get(domain_lower, [SpecialistType.GENERIC])

    return [
        SPECIALIST_REGISTRY[spec_type]
        for spec_type in specialist_types
        if spec_type in SPECIALIST_REGISTRY
    ]


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for specialist management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Specialist Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    subparsers.add_parser("list", help="List all specialists")

    # Match command
    match_parser = subparsers.add_parser("match", help="Find specialists for a task")
    match_parser.add_argument(
        "task",
        type=str,
        help="Task description",
    )
    match_parser.add_argument(
        "--min-score",
        type=float,
        default=0.3,
        help="Minimum match score (default: 0.3)",
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Show specialist info")
    info_parser.add_argument(
        "specialist_type",
        type=str,
        help="Specialist type (frontend, backend, etc.)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "list":
        print("\nAvailable Specialists:\n")
        for spec in list_all_specialists():
            print(f"  {spec.specialist_type.value.upper()}: {spec.name}")
            print(f"    Cost multiplier: {spec.cost_multiplier}x")
            print(f"    Expertise: {', '.join(spec.expertise[:3])}...")
            print()

    elif args.command == "match":
        matches = select_specialist_for_task(args.task, min_score=args.min_score)
        if not matches:
            print(f"\nNo specialists found matching: {args.task}")
            print("Try lowering --min-score or using a more specific task description.")
            return

        print(f"\nBest specialists for task: '{args.task}'\n")
        for i, (spec, score) in enumerate(matches, 1):
            print(f"{i}. {spec.name} (score: {score:.2f})")
            print(f"   Type: {spec.specialist_type.value}")
            print(f"   Cost: {spec.cost_multiplier}x")
            print(f"   Expertise: {', '.join(spec.expertise[:3])}")
            print()

    elif args.command == "info":
        try:
            spec = get_specialist(args.specialist_type)
            print(f"\n{spec.name.upper()}")
            print("=" * 60)
            print(f"\nType: {spec.specialist_type.value}")
            print(f"Cost Multiplier: {spec.cost_multiplier}x")
            print(f"Complexity Threshold: {spec.complexity_threshold}")
            print(f"\nExpertise:")
            for exp in spec.expertise:
                print(f"  - {exp}")
            print(f"\nPreferred Tools:")
            for tool in spec.tools:
                print(f"  - {tool}")
            print(f"\nKeywords:")
            print(f"  {', '.join(spec.keywords[:10])}...")
            print()
        except ValueError as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
