"""
Question Templates

Pre-defined question templates for various request types and scenarios.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from .generator import QuestionCategory, QuestionPriority, ClarifyingQuestion


class TemplateType(Enum):
    """Types of question templates"""
    WEBSITE = "website"
    APPLICATION = "application"
    API = "api"
    DATABASE = "database"
    AUTOMATION = "automation"
    CONTENT = "content"
    ANALYSIS = "analysis"
    GENERAL = "general"


@dataclass
class QuestionTemplate:
    """A reusable question template"""
    id: str
    question: str
    category: QuestionCategory
    priority: QuestionPriority
    options: List[str]
    hint: str = ""
    applicable_types: List[TemplateType] = None
    follow_up_template: str = None
    validation_pattern: str = None

    def __post_init__(self):
        if self.applicable_types is None:
            self.applicable_types = list(TemplateType)

    def to_clarifying_question(self, related_detail: str, **format_kwargs) -> ClarifyingQuestion:
        """Convert to a ClarifyingQuestion instance"""
        return ClarifyingQuestion(
            question=self.question.format(**format_kwargs) if format_kwargs else self.question,
            category=self.category,
            priority=self.priority,
            related_detail=related_detail,
            options=self.options,
            hint=self.hint.format(**format_kwargs) if format_kwargs else self.hint
        )


# Core question templates
CORE_TEMPLATES: Dict[str, QuestionTemplate] = {
    # Scope & Requirements
    "project_scope": QuestionTemplate(
        id="project_scope",
        question="What is the overall scope of this project?",
        category=QuestionCategory.SCOPE,
        priority=QuestionPriority.CRITICAL,
        options=["Small/Simple", "Medium", "Large/Complex", "Enterprise"],
        hint="Helps estimate effort and complexity"
    ),
    "primary_goal": QuestionTemplate(
        id="primary_goal",
        question="What is the primary goal you want to achieve?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.CRITICAL,
        options=[],
        hint="The main objective this should accomplish"
    ),
    "success_criteria": QuestionTemplate(
        id="success_criteria",
        question="How will you measure success?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.HIGH,
        options=[],
        hint="What defines a successful outcome?"
    ),

    # Context
    "existing_system": QuestionTemplate(
        id="existing_system",
        question="Is this a new project or integration with existing systems?",
        category=QuestionCategory.CONTEXT,
        priority=QuestionPriority.HIGH,
        options=["Brand new", "Extending existing", "Replacing legacy", "Integration"],
        hint="Understanding the context helps plan approach"
    ),
    "team_size": QuestionTemplate(
        id="team_size",
        question="Who will be working with or maintaining this?",
        category=QuestionCategory.CONTEXT,
        priority=QuestionPriority.MEDIUM,
        options=["Just me", "Small team (2-5)", "Medium team (6-15)", "Large team (15+)"],
        hint="Affects documentation and complexity choices"
    ),

    # Constraints
    "timeline": QuestionTemplate(
        id="timeline",
        question="Is there a specific deadline or timeline?",
        category=QuestionCategory.CONSTRAINTS,
        priority=QuestionPriority.MEDIUM,
        options=["ASAP", "1-2 weeks", "1 month", "Flexible"],
        hint="Helps prioritize features"
    ),
    "budget": QuestionTemplate(
        id="budget",
        question="Are there any budget constraints for tools/services?",
        category=QuestionCategory.CONSTRAINTS,
        priority=QuestionPriority.LOW,
        options=["Free/open source only", "Limited budget", "Flexible", "Not applicable"],
        hint="Affects technology recommendations"
    ),

    # Technical
    "tech_experience": QuestionTemplate(
        id="tech_experience",
        question="What is your technical experience level?",
        category=QuestionCategory.CONTEXT,
        priority=QuestionPriority.MEDIUM,
        options=["Beginner", "Intermediate", "Advanced", "Expert"],
        hint="Helps tailor the solution complexity"
    ),
    "hosting_preference": QuestionTemplate(
        id="hosting_preference",
        question="Do you have a preferred hosting/deployment platform?",
        category=QuestionCategory.TECHNICAL,
        priority=QuestionPriority.MEDIUM,
        options=["AWS", "Google Cloud", "Azure", "Vercel", "Self-hosted", "No preference"],
        hint="Affects architecture decisions"
    ),

    # Preferences
    "style_preference": QuestionTemplate(
        id="style_preference",
        question="Do you have any style or design preferences?",
        category=QuestionCategory.PREFERENCES,
        priority=QuestionPriority.LOW,
        options=["Modern/Minimal", "Classic/Traditional", "Bold/Creative", "No preference"],
        hint="Visual direction guidance"
    )
}


# Website-specific templates
WEBSITE_TEMPLATES: Dict[str, QuestionTemplate] = {
    "website_type": QuestionTemplate(
        id="website_type",
        question="What type of website is this?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.CRITICAL,
        options=["Landing page", "Portfolio", "Blog", "E-commerce", "SaaS", "Corporate", "Community"],
        hint="Determines core features needed",
        applicable_types=[TemplateType.WEBSITE]
    ),
    "page_count": QuestionTemplate(
        id="page_count",
        question="Approximately how many pages will the site need?",
        category=QuestionCategory.SCOPE,
        priority=QuestionPriority.HIGH,
        options=["1-5 pages", "5-15 pages", "15-50 pages", "50+ pages"],
        hint="Affects navigation and structure",
        applicable_types=[TemplateType.WEBSITE]
    ),
    "content_management": QuestionTemplate(
        id="content_management",
        question="How will content be managed and updated?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.HIGH,
        options=["Static (code changes)", "CMS (WordPress, etc.)", "Headless CMS", "Custom admin"],
        hint="Determines backend requirements",
        applicable_types=[TemplateType.WEBSITE]
    ),
    "seo_requirements": QuestionTemplate(
        id="seo_requirements",
        question="How important is SEO for this website?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.MEDIUM,
        options=["Critical", "Important", "Nice to have", "Not important"],
        hint="Affects technical implementation",
        applicable_types=[TemplateType.WEBSITE]
    ),
    "responsive_design": QuestionTemplate(
        id="responsive_design",
        question="What devices should the website support?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.HIGH,
        options=["Desktop only", "Desktop + Mobile", "Mobile first", "All devices"],
        hint="Determines responsive design approach",
        applicable_types=[TemplateType.WEBSITE]
    )
}


# API-specific templates
API_TEMPLATES: Dict[str, QuestionTemplate] = {
    "api_style": QuestionTemplate(
        id="api_style",
        question="What API style do you prefer?",
        category=QuestionCategory.TECHNICAL,
        priority=QuestionPriority.HIGH,
        options=["REST", "GraphQL", "gRPC", "WebSocket", "No preference"],
        hint="Determines API architecture",
        applicable_types=[TemplateType.API]
    ),
    "versioning_strategy": QuestionTemplate(
        id="versioning_strategy",
        question="How should API versions be handled?",
        category=QuestionCategory.TECHNICAL,
        priority=QuestionPriority.MEDIUM,
        options=["URL path (/v1/)", "Header", "Query param", "Not needed initially"],
        hint="Affects API structure",
        applicable_types=[TemplateType.API]
    ),
    "rate_limiting": QuestionTemplate(
        id="rate_limiting",
        question="Do you need rate limiting?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.MEDIUM,
        options=["Yes, strict", "Yes, basic", "No", "Not sure"],
        hint="For protecting against abuse",
        applicable_types=[TemplateType.API]
    ),
    "documentation_format": QuestionTemplate(
        id="documentation_format",
        question="What API documentation format do you prefer?",
        category=QuestionCategory.PREFERENCES,
        priority=QuestionPriority.LOW,
        options=["OpenAPI/Swagger", "GraphQL schema", "Manual docs", "Auto-generated"],
        hint="For API documentation",
        applicable_types=[TemplateType.API]
    )
}


# Application-specific templates
APPLICATION_TEMPLATES: Dict[str, QuestionTemplate] = {
    "app_type": QuestionTemplate(
        id="app_type",
        question="What type of application is this?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.CRITICAL,
        options=["Web app", "Desktop app", "Mobile app", "CLI tool", "Background service"],
        hint="Determines technology stack",
        applicable_types=[TemplateType.APPLICATION]
    ),
    "user_management": QuestionTemplate(
        id="user_management",
        question="Do you need user accounts and authentication?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.HIGH,
        options=["Yes, full auth", "Yes, simple", "Social login only", "No users"],
        hint="Affects security implementation",
        applicable_types=[TemplateType.APPLICATION]
    ),
    "data_persistence": QuestionTemplate(
        id="data_persistence",
        question="How should data be stored?",
        category=QuestionCategory.TECHNICAL,
        priority=QuestionPriority.HIGH,
        options=["Database", "Files", "Cloud storage", "In-memory only", "Not sure"],
        hint="Determines storage architecture",
        applicable_types=[TemplateType.APPLICATION]
    ),
    "notification_needs": QuestionTemplate(
        id="notification_needs",
        question="Do you need notifications (email, push, etc.)?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.MEDIUM,
        options=["Email", "Push notifications", "SMS", "Multiple", "None"],
        hint="Affects integration requirements",
        applicable_types=[TemplateType.APPLICATION]
    )
}


# Database-specific templates
DATABASE_TEMPLATES: Dict[str, QuestionTemplate] = {
    "db_type": QuestionTemplate(
        id="db_type",
        question="What type of database fits your needs?",
        category=QuestionCategory.TECHNICAL,
        priority=QuestionPriority.CRITICAL,
        options=["Relational (SQL)", "Document (NoSQL)", "Graph", "Time-series", "Not sure"],
        hint="Based on data structure and query patterns",
        applicable_types=[TemplateType.DATABASE]
    ),
    "data_volume": QuestionTemplate(
        id="data_volume",
        question="What is the expected data volume?",
        category=QuestionCategory.CONSTRAINTS,
        priority=QuestionPriority.HIGH,
        options=["< 1GB", "1-10 GB", "10-100 GB", "100GB - 1TB", "> 1TB"],
        hint="Affects database choice and optimization",
        applicable_types=[TemplateType.DATABASE]
    ),
    "query_complexity": QuestionTemplate(
        id="query_complexity",
        question="How complex are your query requirements?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.HIGH,
        options=["Simple CRUD", "Moderate joins", "Complex analytics", "Full-text search"],
        hint="Determines indexing strategy",
        applicable_types=[TemplateType.DATABASE]
    ),
    "backup_requirements": QuestionTemplate(
        id="backup_requirements",
        question="What are your backup and recovery requirements?",
        category=QuestionCategory.CONSTRAINTS,
        priority=QuestionPriority.MEDIUM,
        options=["Basic daily", "Point-in-time", "Real-time replication", "None needed"],
        hint="Affects architecture and costs",
        applicable_types=[TemplateType.DATABASE]
    )
}


# Automation-specific templates
AUTOMATION_TEMPLATES: Dict[str, QuestionTemplate] = {
    "trigger_type": QuestionTemplate(
        id="trigger_type",
        question="What should trigger this automation?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.CRITICAL,
        options=["Schedule", "Event/Webhook", "Manual", "File change", "Multiple"],
        hint="Determines execution model",
        applicable_types=[TemplateType.AUTOMATION]
    ),
    "idempotency": QuestionTemplate(
        id="idempotency",
        question="Should the automation be safe to run multiple times?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.HIGH,
        options=["Yes, must be idempotent", "No, once only", "Not sure"],
        hint="Affects error handling design",
        applicable_types=[TemplateType.AUTOMATION]
    ),
    "monitoring_needs": QuestionTemplate(
        id="monitoring_needs",
        question="How should automation status be monitored?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.MEDIUM,
        options=["Logs only", "Dashboard", "Alerts on failure", "Full observability"],
        hint="Determines monitoring setup",
        applicable_types=[TemplateType.AUTOMATION]
    )
}


# Content-specific templates
CONTENT_TEMPLATES: Dict[str, QuestionTemplate] = {
    "content_type": QuestionTemplate(
        id="content_type",
        question="What type of content is needed?",
        category=QuestionCategory.REQUIREMENTS,
        priority=QuestionPriority.CRITICAL,
        options=["Blog post", "Documentation", "Marketing copy", "Technical guide", "Tutorial"],
        hint="Determines writing style",
        applicable_types=[TemplateType.CONTENT]
    ),
    "target_audience": QuestionTemplate(
        id="target_audience",
        question="Who is the target audience for this content?",
        category=QuestionCategory.CONTEXT,
        priority=QuestionPriority.HIGH,
        options=["General public", "Technical users", "Business decision makers", "Beginners"],
        hint="Affects tone and complexity",
        applicable_types=[TemplateType.CONTENT]
    ),
    "content_length": QuestionTemplate(
        id="content_length",
        question="What is the desired content length?",
        category=QuestionCategory.CONSTRAINTS,
        priority=QuestionPriority.MEDIUM,
        options=["Short (< 500 words)", "Medium (500-1500 words)", "Long (1500-3000 words)", "Comprehensive (3000+)"],
        hint="Affects depth of coverage",
        applicable_types=[TemplateType.CONTENT]
    ),
    "voice_tone": QuestionTemplate(
        id="voice_tone",
        question="What tone should the content have?",
        category=QuestionCategory.PREFERENCES,
        priority=QuestionPriority.MEDIUM,
        options=["Professional", "Casual/Friendly", "Technical", "Authoritative", "Conversational"],
        hint="Determines writing style",
        applicable_types=[TemplateType.CONTENT]
    )
}


class TemplateLibrary:
    """Library of question templates"""

    def __init__(self):
        self.templates: Dict[str, QuestionTemplate] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load all default templates"""
        for templates in [
            CORE_TEMPLATES,
            WEBSITE_TEMPLATES,
            API_TEMPLATES,
            APPLICATION_TEMPLATES,
            DATABASE_TEMPLATES,
            AUTOMATION_TEMPLATES,
            CONTENT_TEMPLATES
        ]:
            self.templates.update(templates)

    def get_template(self, template_id: str) -> QuestionTemplate:
        """Get a specific template by ID"""
        return self.templates.get(template_id)

    def get_templates_for_type(self, template_type: TemplateType) -> List[QuestionTemplate]:
        """Get all templates applicable to a type"""
        return [t for t in self.templates.values()
                if template_type in t.applicable_types]

    def get_templates_by_category(self, category: QuestionCategory) -> List[QuestionTemplate]:
        """Get templates by category"""
        return [t for t in self.templates.values() if t.category == category]

    def get_templates_by_priority(self, priority: QuestionPriority) -> List[QuestionTemplate]:
        """Get templates by priority"""
        return [t for t in self.templates.values() if t.priority == priority]

    def add_template(self, template: QuestionTemplate):
        """Add a custom template"""
        self.templates[template.id] = template

    def remove_template(self, template_id: str) -> bool:
        """Remove a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def generate_questions(
        self,
        template_type: TemplateType,
        max_questions: int = None,
        priorities: List[QuestionPriority] = None
    ) -> List[ClarifyingQuestion]:
        """Generate questions from templates

        Args:
            template_type: Type to generate questions for
            max_questions: Maximum number of questions
            priorities: Filter by priorities

        Returns:
            List of ClarifyingQuestion instances
        """
        templates = self.get_templates_for_type(template_type)

        if priorities:
            templates = [t for t in templates if t.priority in priorities]

        # Sort by priority
        priority_order = {
            QuestionPriority.CRITICAL: 0,
            QuestionPriority.HIGH: 1,
            QuestionPriority.MEDIUM: 2,
            QuestionPriority.LOW: 3
        }
        templates.sort(key=lambda t: priority_order[t.priority])

        if max_questions:
            templates = templates[:max_questions]

        return [t.to_clarifying_question(t.id) for t in templates]


# Global template library instance
template_library = TemplateLibrary()
