"""
Clarifying Question Generator

Generate intelligent follow-up questions based on detected vagueness.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from .detector import ClarityAnalysis, RequestType, RequestClarity

logger = logging.getLogger(__name__)


class QuestionPriority(Enum):
    """Priority level for clarifying questions"""
    CRITICAL = "critical"  # Must be answered
    HIGH = "high"          # Should be answered
    MEDIUM = "medium"      # Nice to have
    LOW = "low"           # Optional


class QuestionCategory(Enum):
    """Category of clarifying question"""
    SCOPE = "scope"
    REQUIREMENTS = "requirements"
    PREFERENCES = "preferences"
    CONSTRAINTS = "constraints"
    CONTEXT = "context"
    TECHNICAL = "technical"


class QuestionType(Enum):
    """Type of question input"""
    TEXT = "text"                      # Free-form text input
    MULTIPLE_CHOICE = "multiple_choice"  # Single selection from options
    SELECTION = "selection"            # Multiple selection from options
    BOOLEAN = "boolean"                # Yes/No question
    NUMBER = "number"                  # Numeric input
    SCALE = "scale"                    # Rating scale (1-5, 1-10)


@dataclass
class ClarifyingQuestion:
    """A clarifying question to ask the user"""
    question: str
    category: QuestionCategory
    priority: QuestionPriority
    related_detail: str
    options: List[str] = field(default_factory=list)
    default: Optional[str] = None
    hint: str = ""
    follow_up: Optional[str] = None
    question_type: QuestionType = QuestionType.TEXT
    required: bool = True
    context: str = ""

    # Alias for compatibility
    @property
    def id(self) -> str:
        """Alias for related_detail"""
        return self.related_detail

    @property
    def text(self) -> str:
        """Alias for question"""
        return self.question

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question": self.question,
            "text": self.text,
            "category": self.category.value if isinstance(self.category, QuestionCategory) else self.category,
            "priority": self.priority.value if isinstance(self.priority, QuestionPriority) else self.priority,
            "question_type": self.question_type.value if isinstance(self.question_type, QuestionType) else self.question_type,
            "related_detail": self.related_detail,
            "options": self.options,
            "default": self.default,
            "hint": self.hint,
            "follow_up": self.follow_up,
            "required": self.required,
            "context": self.context
        }


@dataclass
class QuestionSet:
    """A set of clarifying questions"""
    questions: List[ClarifyingQuestion]
    request_type: RequestType
    clarity_level: RequestClarity
    summary: str

    def get_critical_questions(self) -> List[ClarifyingQuestion]:
        """Get only critical priority questions"""
        return [q for q in self.questions if q.priority == QuestionPriority.CRITICAL]

    def get_by_category(self, category: QuestionCategory) -> List[ClarifyingQuestion]:
        """Get questions by category"""
        return [q for q in self.questions if q.category == category]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "questions": [q.to_dict() for q in self.questions],
            "request_type": self.request_type.value,
            "clarity_level": self.clarity_level.value,
            "summary": self.summary,
            "question_count": len(self.questions),
            "critical_count": len(self.get_critical_questions())
        }


class QuestionGenerator:
    """Generate clarifying questions based on analysis"""

    def __init__(self):
        # Question templates by detail type
        self.question_templates = {
            "target_audience": {
                "question": "Who is the target audience for this {type}?",
                "category": QuestionCategory.CONTEXT,
                "priority": QuestionPriority.HIGH,
                "options": ["General public", "Business professionals", "Developers", "Students", "Specific industry"],
                "hint": "Understanding your audience helps us tailor the solution"
            },
            "pages_or_sections": {
                "question": "What pages or sections should be included?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": ["Home", "About", "Services", "Contact", "Blog", "Portfolio"],
                "hint": "List the main pages you need"
            },
            "specific_features": {
                "question": "What specific features or functionality do you need?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": [],
                "hint": "Be as specific as possible about what the {type} should do"
            },
            "color_scheme_or_style": {
                "question": "Do you have any preferences for colors or visual style?",
                "category": QuestionCategory.PREFERENCES,
                "priority": QuestionPriority.MEDIUM,
                "options": ["Modern/minimal", "Corporate/professional", "Colorful/vibrant", "Dark theme", "Light theme"],
                "hint": "Share any brand colors or style preferences"
            },
            "reference_examples": {
                "question": "Are there any examples or references you'd like us to consider?",
                "category": QuestionCategory.PREFERENCES,
                "priority": QuestionPriority.LOW,
                "options": [],
                "hint": "Links to similar projects or designs you like"
            },
            "technology_stack": {
                "question": "Do you have any technology preferences or requirements?",
                "category": QuestionCategory.TECHNICAL,
                "priority": QuestionPriority.HIGH,
                "options": ["Python", "JavaScript/TypeScript", "React", "Vue", "No preference"],
                "hint": "Specify frameworks, languages, or platforms"
            },
            "core_functionality": {
                "question": "What are the core functions this application must perform?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": [],
                "hint": "List the essential features"
            },
            "target_platform": {
                "question": "What platform(s) should this run on?",
                "category": QuestionCategory.TECHNICAL,
                "priority": QuestionPriority.HIGH,
                "options": ["Web", "Desktop", "Mobile (iOS)", "Mobile (Android)", "Cross-platform"],
                "hint": "Specify where users will access this"
            },
            "endpoint_specifications": {
                "question": "What endpoints or operations does the API need to support?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": [],
                "hint": "List the main API operations"
            },
            "data_models": {
                "question": "What data models or entities will the API handle?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.HIGH,
                "options": [],
                "hint": "Describe the main data structures"
            },
            "authentication_method": {
                "question": "What authentication method should be used?",
                "category": QuestionCategory.TECHNICAL,
                "priority": QuestionPriority.HIGH,
                "options": ["API Key", "JWT", "OAuth 2.0", "Basic Auth", "None"],
                "hint": "How should API access be secured?"
            },
            "schema_design": {
                "question": "What tables or collections are needed?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": [],
                "hint": "List the main data entities"
            },
            "data_relationships": {
                "question": "What relationships exist between your data entities?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.HIGH,
                "options": [],
                "hint": "Describe how entities relate to each other"
            },
            "writing_tone": {
                "question": "What tone or style should the content have?",
                "category": QuestionCategory.PREFERENCES,
                "priority": QuestionPriority.HIGH,
                "options": ["Professional", "Casual/friendly", "Technical", "Persuasive", "Informative"],
                "hint": "How should the content sound?"
            },
            "content_length": {
                "question": "What is the desired length of the content?",
                "category": QuestionCategory.CONSTRAINTS,
                "priority": QuestionPriority.MEDIUM,
                "options": ["Short (< 500 words)", "Medium (500-1500 words)", "Long (1500+ words)"],
                "hint": "Approximate word count"
            },
            "main_topic": {
                "question": "What is the main topic or subject matter?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": [],
                "hint": "The central theme of the content"
            },
            "trigger_condition": {
                "question": "What should trigger this automation?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": ["Schedule/time-based", "Event-based", "Manual trigger", "Webhook"],
                "hint": "When should the automation run?"
            },
            "actions_to_perform": {
                "question": "What actions should the automation perform?",
                "category": QuestionCategory.REQUIREMENTS,
                "priority": QuestionPriority.CRITICAL,
                "options": [],
                "hint": "List the steps in the automation"
            }
        }

        # Type-specific additional questions
        self.type_questions = {
            RequestType.WEBSITE: [
                ClarifyingQuestion(
                    question="Do you need a content management system (CMS)?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="cms",
                    options=["Yes", "No", "Maybe"],
                    hint="For updating content without coding"
                ),
                ClarifyingQuestion(
                    question="Will you need user authentication/accounts?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="authentication",
                    options=["Yes", "No", "Optional"],
                    hint="For user-specific features"
                )
            ],
            RequestType.APPLICATION: [
                ClarifyingQuestion(
                    question="Should data be stored locally or in the cloud?",
                    category=QuestionCategory.TECHNICAL,
                    priority=QuestionPriority.HIGH,
                    related_detail="storage",
                    options=["Local", "Cloud", "Both", "Not sure"],
                    hint="Where should user data be saved?"
                ),
                ClarifyingQuestion(
                    question="Do you need offline functionality?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="offline",
                    options=["Yes", "No", "Nice to have"],
                    hint="Should the app work without internet?"
                )
            ],
            RequestType.API: [
                ClarifyingQuestion(
                    question="What is the expected request volume?",
                    category=QuestionCategory.CONSTRAINTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="scale",
                    options=["Low (< 1k/day)", "Medium (1k-100k/day)", "High (100k+/day)"],
                    hint="Helps determine infrastructure needs"
                ),
                ClarifyingQuestion(
                    question="Should the API support real-time updates?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="realtime",
                    options=["Yes (WebSocket)", "No (REST only)", "Maybe"],
                    hint="For live data updates"
                )
            ],
            RequestType.DATABASE: [
                ClarifyingQuestion(
                    question="What type of database do you prefer?",
                    category=QuestionCategory.TECHNICAL,
                    priority=QuestionPriority.HIGH,
                    related_detail="db_type",
                    options=["SQL (PostgreSQL, MySQL)", "NoSQL (MongoDB)", "Graph (Neo4j)", "No preference"],
                    hint="Based on your data structure needs"
                ),
                ClarifyingQuestion(
                    question="What is the expected data volume?",
                    category=QuestionCategory.CONSTRAINTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="data_volume",
                    options=["Small (< 1GB)", "Medium (1-100GB)", "Large (100GB+)"],
                    hint="Affects database choice and optimization"
                )
            ],
            RequestType.AUTOMATION: [
                ClarifyingQuestion(
                    question="How often should this automation run?",
                    category=QuestionCategory.CONSTRAINTS,
                    priority=QuestionPriority.HIGH,
                    related_detail="frequency",
                    options=["Real-time", "Every minute", "Hourly", "Daily", "Weekly", "On-demand"],
                    hint="Execution frequency"
                ),
                ClarifyingQuestion(
                    question="What should happen if the automation fails?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="error_handling",
                    options=["Retry", "Notify", "Log and continue", "Stop"],
                    hint="Error handling behavior"
                )
            ],
            RequestType.CONTENT: [
                ClarifyingQuestion(
                    question="What format should the content be in?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.MEDIUM,
                    related_detail="format",
                    options=["Markdown", "HTML", "Plain text", "PDF"],
                    hint="Output format"
                ),
                ClarifyingQuestion(
                    question="Should SEO be a consideration?",
                    category=QuestionCategory.REQUIREMENTS,
                    priority=QuestionPriority.LOW,
                    related_detail="seo",
                    options=["Yes", "No", "If applicable"],
                    hint="Search engine optimization"
                )
            ]
        }

    def generate(self, analysis: ClarityAnalysis) -> QuestionSet:
        """Generate clarifying questions based on analysis

        Args:
            analysis: ClarityAnalysis from detector

        Returns:
            QuestionSet with relevant questions
        """
        questions = []
        type_name = analysis.detected_type.value

        # Generate questions for missing details
        for detail in analysis.missing_details:
            if detail in self.question_templates:
                template = self.question_templates[detail]
                question = ClarifyingQuestion(
                    question=template["question"].format(type=type_name),
                    category=template["category"],
                    priority=template["priority"],
                    related_detail=detail,
                    options=template.get("options", []),
                    hint=template.get("hint", "").format(type=type_name),
                    question_type=QuestionType.MULTIPLE_CHOICE if template.get("options") else QuestionType.TEXT
                )
                questions.append(question)
            else:
                # Log warning for missing template to provide feedback
                logger.warning(
                    f"No question template found for detail '{detail}' "
                    f"(request type: {type_name}). Consider adding a template."
                )

        # Add type-specific questions
        if analysis.detected_type in self.type_questions:
            for question in self.type_questions[analysis.detected_type]:
                # Avoid duplicates
                if question.related_detail not in analysis.specific_elements:
                    questions.append(question)

        # Sort by priority
        priority_order = {
            QuestionPriority.CRITICAL: 0,
            QuestionPriority.HIGH: 1,
            QuestionPriority.MEDIUM: 2,
            QuestionPriority.LOW: 3
        }
        questions.sort(key=lambda q: priority_order[q.priority])

        # Generate summary
        summary = self._generate_summary(analysis, questions)

        return QuestionSet(
            questions=questions,
            request_type=analysis.detected_type,
            clarity_level=analysis.clarity_level,
            summary=summary
        )

    async def generate_questions(
        self,
        analysis: ClarityAnalysis,
        max_questions: int = 10,
        prioritize_missing: bool = True
    ) -> List[ClarifyingQuestion]:
        """Async method to generate clarifying questions

        Args:
            analysis: ClarityAnalysis from detector
            max_questions: Maximum number of questions
            prioritize_missing: Whether to prioritize missing details

        Returns:
            List of ClarifyingQuestion
        """
        question_set = self.generate(analysis)
        questions = question_set.questions

        if prioritize_missing and analysis.missing_details:
            # Ensure questions about missing details come first
            missing_questions = [q for q in questions if q.related_detail in analysis.missing_details]
            other_questions = [q for q in questions if q.related_detail not in analysis.missing_details]
            questions = missing_questions + other_questions

        return questions[:max_questions]

    def format_questions_for_display(
        self,
        questions: List[ClarifyingQuestion],
        format_type: str = "text"
    ) -> str:
        """Format questions for display with various formats

        Args:
            questions: List of questions to format
            format_type: Output format ('text', 'html', 'markdown')

        Returns:
            Formatted string
        """
        if format_type == "html":
            lines = ['<div class="clarification-questions">']
            for q in questions:
                lines.append(f'<div class="question" data-id="{q.id}">')
                lines.append(f'<label>{q.question}</label>')
                if q.context:
                    lines.append(f'<p class="context">{q.context}</p>')
                if q.question_type == QuestionType.MULTIPLE_CHOICE:
                    for opt in q.options:
                        required = 'required' if q.required else ''
                        lines.append(f'<input type="radio" name="{q.id}" value="{opt}" {required}> {opt}<br>')
                elif q.question_type == QuestionType.SELECTION:
                    for opt in q.options:
                        required = 'required' if q.required else ''
                        lines.append(f'<input type="checkbox" name="{q.id}" value="{opt}" {required}> {opt}<br>')
                else:
                    required = 'required' if q.required else ''
                    lines.append(f'<input type="text" name="{q.id}" {required}>')
                lines.append('</div>')
            lines.append('</div>')
            return "\n".join(lines)

        elif format_type == "markdown":
            return self.format_questions(questions, "markdown")

        else:  # text
            lines = []
            for i, q in enumerate(questions, 1):
                lines.append(f"{i}. {q.question}")
                if q.context:
                    lines.append(f"   {q.context}")
                if q.options:
                    for j, opt in enumerate(q.options):
                        letter = chr(ord('a') + j)
                        lines.append(f"   {letter}) {opt}")
            return "\n".join(lines)

    def _generate_summary(self, analysis: ClarityAnalysis, questions: List[ClarifyingQuestion]) -> str:
        """Generate a summary of needed clarifications"""
        parts = []

        if analysis.clarity_level == RequestClarity.VERY_VAGUE:
            parts.append("Your request needs significant clarification.")
        elif analysis.clarity_level == RequestClarity.VAGUE:
            parts.append("I need a few more details to proceed.")
        else:
            parts.append("Just a few quick questions to ensure I understand correctly.")

        critical_count = len([q for q in questions if q.priority == QuestionPriority.CRITICAL])
        if critical_count > 0:
            parts.append(f"There {'is' if critical_count == 1 else 'are'} {critical_count} critical question{'s' if critical_count > 1 else ''} to address.")

        return " ".join(parts)

    def generate_quick_questions(
        self,
        analysis: ClarityAnalysis,
        max_questions: int = 3
    ) -> List[ClarifyingQuestion]:
        """Generate a minimal set of the most important questions

        Args:
            analysis: ClarityAnalysis from detector
            max_questions: Maximum number of questions to return

        Returns:
            List of most critical questions
        """
        question_set = self.generate(analysis)

        # Get critical first, then high priority
        critical = [q for q in question_set.questions if q.priority == QuestionPriority.CRITICAL]
        high = [q for q in question_set.questions if q.priority == QuestionPriority.HIGH]

        result = critical[:max_questions]
        remaining = max_questions - len(result)

        if remaining > 0:
            result.extend(high[:remaining])

        return result

    def format_questions(
        self,
        questions: List[ClarifyingQuestion],
        format_type: str = "text"
    ) -> str:
        """Format questions for display

        Args:
            questions: List of questions to format
            format_type: Output format ('text', 'markdown', 'numbered')

        Returns:
            Formatted string
        """
        if format_type == "markdown":
            lines = []
            for i, q in enumerate(questions, 1):
                lines.append(f"### Question {i}: {q.question}")
                if q.hint:
                    lines.append(f"*{q.hint}*")
                if q.options:
                    lines.append("\nOptions:")
                    for opt in q.options:
                        lines.append(f"- {opt}")
                lines.append("")
            return "\n".join(lines)

        elif format_type == "numbered":
            lines = []
            for i, q in enumerate(questions, 1):
                lines.append(f"{i}. {q.question}")
                if q.options:
                    lines.append(f"   Options: {', '.join(q.options)}")
            return "\n".join(lines)

        else:  # text
            lines = []
            for q in questions:
                lines.append(f"- {q.question}")
                if q.hint:
                    lines.append(f"  Hint: {q.hint}")
            return "\n".join(lines)

    def get_follow_up_questions(
        self,
        previous_answer: str,
        previous_question: ClarifyingQuestion,
        analysis: ClarityAnalysis
    ) -> List[ClarifyingQuestion]:
        """Generate follow-up questions based on answer

        Args:
            previous_answer: User's answer to previous question
            previous_question: The question that was answered
            analysis: Original analysis

        Returns:
            List of follow-up questions
        """
        follow_ups = []

        # Check for answers that need more detail
        vague_answers = ["not sure", "maybe", "depends", "other", "custom"]
        if any(va in previous_answer.lower() for va in vague_answers):
            follow_ups.append(ClarifyingQuestion(
                question=f"Could you elaborate on your answer about {previous_question.related_detail.replace('_', ' ')}?",
                category=previous_question.category,
                priority=QuestionPriority.HIGH,
                related_detail=f"{previous_question.related_detail}_detail",
                hint="More specifics would help"
            ))

        return follow_ups
