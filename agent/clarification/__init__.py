"""
Clarification Loop System

A system for intelligently asking follow-up questions before executing complex tasks.

Usage:
    from agent.clarification import ClarificationManager, should_request_clarification

    # Quick check if clarification needed
    needs_clarification, analysis = should_request_clarification("build me a website")

    # Full session management
    manager = ClarificationManager()
    if manager.should_clarify(request)[0]:
        session = manager.start_session(request)
        for question in session.question_set.questions:
            print(question.question)
            answer = input("> ")
            manager.answer_question(session.session_id, answer)
"""

from .detector import (
    VagueRequestDetector,
    ClarityAnalysis,
    RequestClarity,
    RequestType,
    should_request_clarification,
)

from .generator import (
    QuestionGenerator,
    ClarifyingQuestion,
    QuestionSet,
    QuestionPriority,
    QuestionCategory,
    QuestionType,
)

from .manager import (
    ClarificationManager,
    ClarificationSession,
    SessionStatus,
    ClarificationPhase,
    Answer,
    clarify_request,
)

from .templates import (
    TemplateLibrary,
    QuestionTemplate,
    TemplateType,
    template_library,
    CORE_TEMPLATES,
    WEBSITE_TEMPLATES,
    API_TEMPLATES,
    APPLICATION_TEMPLATES,
    DATABASE_TEMPLATES,
    AUTOMATION_TEMPLATES,
    CONTENT_TEMPLATES,
)

__all__ = [
    # Detector
    'VagueRequestDetector',
    'ClarityAnalysis',
    'RequestClarity',
    'RequestType',
    'should_request_clarification',

    # Generator
    'QuestionGenerator',
    'ClarifyingQuestion',
    'QuestionSet',
    'QuestionPriority',
    'QuestionCategory',
    'QuestionType',

    # Manager
    'ClarificationManager',
    'ClarificationSession',
    'SessionStatus',
    'ClarificationPhase',
    'Answer',
    'clarify_request',

    # Templates
    'TemplateLibrary',
    'QuestionTemplate',
    'TemplateType',
    'template_library',
    'CORE_TEMPLATES',
    'WEBSITE_TEMPLATES',
    'API_TEMPLATES',
    'APPLICATION_TEMPLATES',
    'DATABASE_TEMPLATES',
    'AUTOMATION_TEMPLATES',
    'CONTENT_TEMPLATES',
]
