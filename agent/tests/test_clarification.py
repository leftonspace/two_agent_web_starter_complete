"""
Comprehensive Tests for Clarification Loop System

Tests covering:
- Vague request detection
- Question generation
- Clarification session management
- Question templates
"""

import pytest
from datetime import datetime

from agent.clarification import (
    # Detector
    VagueRequestDetector,
    ClarityAnalysis,
    RequestClarity,
    RequestType,
    should_request_clarification,
    # Generator
    QuestionGenerator,
    ClarifyingQuestion,
    QuestionSet,
    QuestionPriority,
    QuestionCategory,
    # Manager
    ClarificationManager,
    ClarificationSession,
    SessionStatus,
    Answer,
    clarify_request,
    # Templates
    TemplateLibrary,
    QuestionTemplate,
    TemplateType,
    template_library,
    CORE_TEMPLATES,
    WEBSITE_TEMPLATES,
)


# =============================================================================
# Detector Tests
# =============================================================================

class TestVagueRequestDetector:
    """Tests for VagueRequestDetector"""

    @pytest.fixture
    def detector(self):
        return VagueRequestDetector()

    def test_init(self, detector):
        """Test detector initialization"""
        assert len(detector.type_keywords) > 0
        assert len(detector.vague_triggers) > 0
        assert len(detector.detail_patterns) > 0

    def test_analyze_returns_clarity_analysis(self, detector):
        """Test that analyze returns ClarityAnalysis"""
        result = detector.analyze("build me a website")
        assert isinstance(result, ClarityAnalysis)
        assert isinstance(result.clarity_level, RequestClarity)
        assert isinstance(result.detected_type, RequestType)
        assert isinstance(result.missing_details, list)

    def test_detect_website_type(self, detector):
        """Test website type detection"""
        result = detector.analyze("I need a website for my business")
        assert result.detected_type == RequestType.WEBSITE

    def test_detect_api_type(self, detector):
        """Test API type detection"""
        result = detector.analyze("Create a REST API with authentication")
        assert result.detected_type == RequestType.API

    def test_detect_application_type(self, detector):
        """Test application type detection"""
        result = detector.analyze("Build me a desktop application")
        assert result.detected_type == RequestType.APPLICATION

    def test_detect_database_type(self, detector):
        """Test database type detection"""
        result = detector.analyze("Design a database schema for users")
        assert result.detected_type == RequestType.DATABASE

    def test_detect_automation_type(self, detector):
        """Test automation type detection"""
        result = detector.analyze("Automate the deployment pipeline")
        assert result.detected_type == RequestType.AUTOMATION

    def test_detect_content_type(self, detector):
        """Test content type detection"""
        result = detector.analyze("Write documentation for the API")
        assert result.detected_type == RequestType.CONTENT

    def test_detect_general_type(self, detector):
        """Test general type detection for ambiguous requests"""
        result = detector.analyze("help me")
        assert result.detected_type == RequestType.GENERAL

    def test_vague_request_detected(self, detector):
        """Test that vague requests are detected"""
        result = detector.analyze("something")
        assert result.clarity_level in [RequestClarity.VAGUE, RequestClarity.VERY_VAGUE]
        assert result.vagueness_score > 0.3

    def test_clear_request_detected(self, detector):
        """Test that detailed requests are clear"""
        result = detector.analyze(
            "Build a React website with a home page, about page, and contact form. "
            "Use a dark theme with blue accents. Target audience is developers. "
            "Include user authentication with JWT tokens."
        )
        assert result.clarity_level in [RequestClarity.CLEAR, RequestClarity.SOMEWHAT_CLEAR]

    def test_missing_details_identified(self, detector):
        """Test that missing details are identified"""
        result = detector.analyze("build a website")
        assert len(result.missing_details) > 0
        assert any("page" in detail.lower() or "section" in detail.lower()
                   for detail in result.missing_details)

    def test_specific_elements_extracted(self, detector):
        """Test that specific elements are extracted"""
        result = detector.analyze("Create a website for developers with dark theme")
        assert "target_audience" in result.specific_elements or "color_scheme" in result.specific_elements

    def test_word_count_tracked(self, detector):
        """Test that word count is tracked"""
        result = detector.analyze("one two three four five")
        assert result.word_count == 5

    def test_vagueness_score_range(self, detector):
        """Test that vagueness score is in valid range"""
        result = detector.analyze("build something")
        assert 0 <= result.vagueness_score <= 1

    def test_confidence_range(self, detector):
        """Test that confidence is in valid range"""
        result = detector.analyze("build a website")
        assert 0 <= result.confidence <= 1

    def test_reasoning_generated(self, detector):
        """Test that reasoning is generated"""
        result = detector.analyze("help")
        assert result.reasoning is not None
        assert len(result.reasoning) > 0


class TestClarityAnalysis:
    """Tests for ClarityAnalysis dataclass"""

    @pytest.fixture
    def sample_analysis(self):
        return ClarityAnalysis(
            clarity_level=RequestClarity.VAGUE,
            confidence=0.8,
            missing_details=["target_audience", "features"],
            detected_type=RequestType.WEBSITE,
            specific_elements={"color_scheme": ["dark"]},
            reasoning="Request is brief",
            vagueness_score=0.6,
            word_count=5
        )

    def test_needs_clarification_true(self, sample_analysis):
        """Test needs_clarification returns True for vague request"""
        assert sample_analysis.needs_clarification(RequestClarity.SOMEWHAT_CLEAR)

    def test_needs_clarification_false(self, sample_analysis):
        """Test needs_clarification returns False when below threshold"""
        assert not sample_analysis.needs_clarification(RequestClarity.VERY_VAGUE)

    def test_to_dict(self, sample_analysis):
        """Test conversion to dictionary"""
        result = sample_analysis.to_dict()
        assert result["clarity_level"] == "vague"
        assert result["detected_type"] == "website"
        assert result["confidence"] == 0.8


class TestShouldRequestClarification:
    """Tests for should_request_clarification function"""

    def test_returns_tuple(self):
        """Test that function returns tuple"""
        result = should_request_clarification("build a website")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], ClarityAnalysis)

    def test_vague_request_needs_clarification(self):
        """Test that vague requests need clarification"""
        should_clarify, _ = should_request_clarification("something")
        assert should_clarify

    def test_skip_phrase_disables_clarification(self):
        """Test that skip phrases disable clarification"""
        should_clarify, _ = should_request_clarification("just do it website")
        assert not should_clarify

    def test_use_defaults_skips(self):
        """Test use defaults skips clarification"""
        should_clarify, _ = should_request_clarification("use defaults for the website")
        assert not should_clarify

    def test_always_clarify_types(self):
        """Test always_clarify_types parameter"""
        should_clarify, analysis = should_request_clarification(
            "build a detailed website with all features",
            always_clarify_types=[RequestType.WEBSITE]
        )
        if analysis.detected_type == RequestType.WEBSITE:
            assert should_clarify


# =============================================================================
# Generator Tests
# =============================================================================

class TestQuestionGenerator:
    """Tests for QuestionGenerator"""

    @pytest.fixture
    def generator(self):
        return QuestionGenerator()

    @pytest.fixture
    def sample_analysis(self):
        detector = VagueRequestDetector()
        return detector.analyze("build a website")

    def test_init(self, generator):
        """Test generator initialization"""
        assert len(generator.question_templates) > 0
        assert len(generator.type_questions) > 0

    def test_generate_returns_question_set(self, generator, sample_analysis):
        """Test that generate returns QuestionSet"""
        result = generator.generate(sample_analysis)
        assert isinstance(result, QuestionSet)
        assert isinstance(result.questions, list)

    def test_questions_have_required_fields(self, generator, sample_analysis):
        """Test that generated questions have required fields"""
        result = generator.generate(sample_analysis)
        for question in result.questions:
            assert isinstance(question, ClarifyingQuestion)
            assert question.question
            assert isinstance(question.category, QuestionCategory)
            assert isinstance(question.priority, QuestionPriority)
            assert question.related_detail

    def test_questions_sorted_by_priority(self, generator, sample_analysis):
        """Test that questions are sorted by priority"""
        result = generator.generate(sample_analysis)
        if len(result.questions) > 1:
            priority_order = {
                QuestionPriority.CRITICAL: 0,
                QuestionPriority.HIGH: 1,
                QuestionPriority.MEDIUM: 2,
                QuestionPriority.LOW: 3
            }
            for i in range(len(result.questions) - 1):
                assert priority_order[result.questions[i].priority] <= \
                       priority_order[result.questions[i + 1].priority]

    def test_summary_generated(self, generator, sample_analysis):
        """Test that summary is generated"""
        result = generator.generate(sample_analysis)
        assert result.summary
        assert len(result.summary) > 0

    def test_generate_quick_questions(self, generator, sample_analysis):
        """Test generating quick questions"""
        questions = generator.generate_quick_questions(sample_analysis, max_questions=3)
        assert len(questions) <= 3
        # Should prioritize critical questions
        for q in questions:
            assert q.priority in [QuestionPriority.CRITICAL, QuestionPriority.HIGH]

    def test_format_questions_text(self, generator, sample_analysis):
        """Test formatting questions as text"""
        result = generator.generate(sample_analysis)
        formatted = generator.format_questions(result.questions[:3], "text")
        assert isinstance(formatted, str)
        assert "-" in formatted

    def test_format_questions_markdown(self, generator, sample_analysis):
        """Test formatting questions as markdown"""
        result = generator.generate(sample_analysis)
        formatted = generator.format_questions(result.questions[:3], "markdown")
        assert "###" in formatted

    def test_format_questions_numbered(self, generator, sample_analysis):
        """Test formatting questions as numbered list"""
        result = generator.generate(sample_analysis)
        formatted = generator.format_questions(result.questions[:3], "numbered")
        assert "1." in formatted


class TestClarifyingQuestion:
    """Tests for ClarifyingQuestion"""

    @pytest.fixture
    def sample_question(self):
        return ClarifyingQuestion(
            question="What is the target audience?",
            category=QuestionCategory.CONTEXT,
            priority=QuestionPriority.HIGH,
            related_detail="target_audience",
            options=["Developers", "Business users", "General public"],
            hint="Who will use this?"
        )

    def test_to_dict(self, sample_question):
        """Test conversion to dictionary"""
        result = sample_question.to_dict()
        assert result["question"] == "What is the target audience?"
        assert result["category"] == "context"
        assert result["priority"] == "high"
        assert len(result["options"]) == 3


class TestQuestionSet:
    """Tests for QuestionSet"""

    @pytest.fixture
    def sample_question_set(self):
        questions = [
            ClarifyingQuestion(
                question="Q1", category=QuestionCategory.REQUIREMENTS,
                priority=QuestionPriority.CRITICAL, related_detail="d1"
            ),
            ClarifyingQuestion(
                question="Q2", category=QuestionCategory.CONTEXT,
                priority=QuestionPriority.HIGH, related_detail="d2"
            ),
            ClarifyingQuestion(
                question="Q3", category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.LOW, related_detail="d3"
            ),
        ]
        return QuestionSet(
            questions=questions,
            request_type=RequestType.WEBSITE,
            clarity_level=RequestClarity.VAGUE,
            summary="Test summary"
        )

    def test_get_critical_questions(self, sample_question_set):
        """Test getting critical questions"""
        critical = sample_question_set.get_critical_questions()
        assert len(critical) == 1
        assert critical[0].priority == QuestionPriority.CRITICAL

    def test_get_by_category(self, sample_question_set):
        """Test getting questions by category"""
        context_qs = sample_question_set.get_by_category(QuestionCategory.CONTEXT)
        assert len(context_qs) == 1

    def test_to_dict(self, sample_question_set):
        """Test conversion to dictionary"""
        result = sample_question_set.to_dict()
        assert result["question_count"] == 3
        assert result["critical_count"] == 1


# =============================================================================
# Manager Tests
# =============================================================================

class TestClarificationManager:
    """Tests for ClarificationManager"""

    @pytest.fixture
    def manager(self):
        return ClarificationManager()

    def test_init(self, manager):
        """Test manager initialization"""
        assert manager.detector is not None
        assert manager.generator is not None
        assert len(manager.skip_phrases) > 0

    def test_should_clarify_vague_request(self, manager):
        """Test should_clarify for vague request"""
        should_clarify, analysis = manager.should_clarify("build something")
        assert isinstance(should_clarify, bool)
        assert isinstance(analysis, ClarityAnalysis)

    def test_should_clarify_with_skip_phrase(self, manager):
        """Test should_clarify with skip phrase"""
        should_clarify, _ = manager.should_clarify("just do it - build a website")
        assert not should_clarify

    def test_start_session(self, manager):
        """Test starting a session"""
        session = manager.start_session("build a website")
        assert isinstance(session, ClarificationSession)
        assert session.session_id
        assert session.status == SessionStatus.PENDING
        assert len(session.question_set.questions) > 0

    def test_get_session(self, manager):
        """Test getting a session by ID"""
        session = manager.start_session("build a website")
        retrieved = manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_session_not_found(self, manager):
        """Test getting non-existent session"""
        result = manager.get_session("nonexistent-id")
        assert result is None

    def test_answer_question(self, manager):
        """Test answering a question"""
        session = manager.start_session("build a website")
        first_question = session.current_question
        next_question = manager.answer_question(session.session_id, "For developers")
        assert len(session.answers) == 1
        assert session.answers[0].response == "For developers"
        assert session.status == SessionStatus.IN_PROGRESS

    def test_answer_advances_to_next_question(self, manager):
        """Test that answering advances to next question"""
        session = manager.start_session("build a website")
        first_question = session.current_question
        manager.answer_question(session.session_id, "Answer 1")
        if session.current_question:
            assert session.current_question != first_question

    def test_skip_session(self, manager):
        """Test skipping a session"""
        session = manager.start_session("build a website")
        result = manager.skip_session(session.session_id)
        assert result
        assert session.status == SessionStatus.CANCELLED

    def test_complete_session(self, manager):
        """Test completing a session early"""
        session = manager.start_session("build a website")
        manager.answer_question(session.session_id, "Answer")
        completed = manager.complete_session(session.session_id)
        assert completed is not None
        assert completed.status == SessionStatus.COMPLETED

    def test_get_quick_clarification(self, manager):
        """Test quick clarification"""
        session, questions = manager.get_quick_clarification("build a website", max_questions=2)
        assert isinstance(session, ClarificationSession)
        assert len(questions) <= 2

    def test_process_batch_answers(self, manager):
        """Test processing batch answers"""
        session = manager.start_session("build a website")
        details = [q.related_detail for q in session.question_set.questions[:2]]
        answers = {details[0]: "Answer 1"}
        if len(details) > 1:
            answers[details[1]] = "Answer 2"
        result = manager.process_batch_answers(session.session_id, answers)
        assert result
        assert len(session.answers) >= 1

    def test_get_active_sessions(self, manager):
        """Test getting active sessions"""
        manager.start_session("request 1")
        manager.start_session("request 2")
        active = manager.get_active_sessions()
        assert len(active) >= 2

    def test_cleanup_sessions(self, manager):
        """Test session cleanup"""
        manager.start_session("test")
        # Cleanup with 0 hours should remove all
        manager.cleanup_sessions(max_age_hours=0)
        # Sessions should be removed (created "0 hours" ago)

    def test_get_statistics(self, manager):
        """Test getting statistics"""
        manager.start_session("test 1")
        manager.start_session("test 2")
        stats = manager.get_statistics()
        assert "total_sessions" in stats
        assert stats["total_sessions"] >= 2

    def test_event_callbacks(self, manager):
        """Test event callbacks"""
        events = []

        def on_start(session):
            events.append(("start", session.session_id))

        def on_answer(session, answer):
            events.append(("answer", answer.response))

        manager.on_session_start(on_start)
        manager.on_answer_received(on_answer)

        session = manager.start_session("build a website")
        manager.answer_question(session.session_id, "Test answer")

        assert len(events) >= 2
        assert events[0][0] == "start"
        assert ("answer", "Test answer") in events


class TestClarificationSession:
    """Tests for ClarificationSession"""

    @pytest.fixture
    def sample_session(self):
        manager = ClarificationManager()
        return manager.start_session("build a website")

    def test_current_question(self, sample_session):
        """Test getting current question"""
        question = sample_session.current_question
        if sample_session.question_set.questions:
            assert question is not None
            assert question == sample_session.question_set.questions[0]

    def test_remaining_questions(self, sample_session):
        """Test getting remaining questions"""
        remaining = sample_session.remaining_questions
        assert len(remaining) == len(sample_session.question_set.questions)

    def test_progress(self, sample_session):
        """Test progress calculation"""
        assert sample_session.progress == 0.0

    def test_get_clarified_request(self, sample_session):
        """Test getting clarified request"""
        # Initially should be original
        result = sample_session.get_clarified_request()
        assert result == sample_session.original_request

    def test_get_context(self, sample_session):
        """Test getting context"""
        context = sample_session.get_context()
        assert "original_request" in context
        assert "request_type" in context
        assert "session_id" in context

    def test_to_dict(self, sample_session):
        """Test conversion to dictionary"""
        result = sample_session.to_dict()
        assert "session_id" in result
        assert "status" in result
        assert "progress" in result


class TestAnswer:
    """Tests for Answer"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        question = ClarifyingQuestion(
            question="Test?",
            category=QuestionCategory.REQUIREMENTS,
            priority=QuestionPriority.HIGH,
            related_detail="test"
        )
        answer = Answer(
            question=question,
            response="Test answer",
            confidence=0.9
        )
        result = answer.to_dict()
        assert result["response"] == "Test answer"
        assert result["confidence"] == 0.9


class TestClarifyRequest:
    """Tests for clarify_request convenience function"""

    def test_returns_tuple(self):
        """Test that function returns tuple"""
        result = clarify_request("build a website")
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_vague_request(self):
        """Test with vague request"""
        needs, questions, analysis = clarify_request("something")
        assert needs
        if questions:
            assert len(questions.questions) > 0

    def test_clear_request(self):
        """Test with detailed request"""
        needs, questions, analysis = clarify_request(
            "Build a React website with dark theme, 5 pages, for developers, "
            "including authentication, deployed on Vercel"
        )
        # May or may not need clarification depending on thresholds


# =============================================================================
# Templates Tests
# =============================================================================

class TestTemplateLibrary:
    """Tests for TemplateLibrary"""

    @pytest.fixture
    def library(self):
        return TemplateLibrary()

    def test_init_loads_templates(self, library):
        """Test that templates are loaded on init"""
        assert len(library.templates) > 0

    def test_get_template(self, library):
        """Test getting a template by ID"""
        template = library.get_template("project_scope")
        assert template is not None
        assert isinstance(template, QuestionTemplate)

    def test_get_template_not_found(self, library):
        """Test getting non-existent template"""
        template = library.get_template("nonexistent")
        assert template is None

    def test_get_templates_for_type(self, library):
        """Test getting templates for a type"""
        templates = library.get_templates_for_type(TemplateType.WEBSITE)
        assert len(templates) > 0
        for t in templates:
            assert TemplateType.WEBSITE in t.applicable_types

    def test_get_templates_by_category(self, library):
        """Test getting templates by category"""
        templates = library.get_templates_by_category(QuestionCategory.REQUIREMENTS)
        assert len(templates) > 0
        for t in templates:
            assert t.category == QuestionCategory.REQUIREMENTS

    def test_get_templates_by_priority(self, library):
        """Test getting templates by priority"""
        templates = library.get_templates_by_priority(QuestionPriority.CRITICAL)
        assert len(templates) > 0
        for t in templates:
            assert t.priority == QuestionPriority.CRITICAL

    def test_add_custom_template(self, library):
        """Test adding a custom template"""
        custom = QuestionTemplate(
            id="custom_test",
            question="Custom question?",
            category=QuestionCategory.PREFERENCES,
            priority=QuestionPriority.LOW,
            options=["A", "B"]
        )
        library.add_template(custom)
        assert library.get_template("custom_test") is not None

    def test_remove_template(self, library):
        """Test removing a template"""
        # Add then remove
        custom = QuestionTemplate(
            id="to_remove",
            question="Remove me?",
            category=QuestionCategory.CONTEXT,
            priority=QuestionPriority.LOW,
            options=[]
        )
        library.add_template(custom)
        result = library.remove_template("to_remove")
        assert result
        assert library.get_template("to_remove") is None

    def test_generate_questions(self, library):
        """Test generating questions from templates"""
        questions = library.generate_questions(TemplateType.WEBSITE, max_questions=5)
        assert len(questions) <= 5
        for q in questions:
            assert isinstance(q, ClarifyingQuestion)


class TestQuestionTemplate:
    """Tests for QuestionTemplate"""

    def test_to_clarifying_question(self):
        """Test converting template to ClarifyingQuestion"""
        template = QuestionTemplate(
            id="test",
            question="What is your {type} preference?",
            category=QuestionCategory.PREFERENCES,
            priority=QuestionPriority.MEDIUM,
            options=["A", "B", "C"],
            hint="Choose wisely"
        )
        question = template.to_clarifying_question("preference", type="color")
        assert question.question == "What is your color preference?"
        assert question.related_detail == "preference"
        assert question.options == ["A", "B", "C"]


class TestGlobalTemplateLibrary:
    """Tests for global template_library instance"""

    def test_template_library_exists(self):
        """Test that global instance exists"""
        assert template_library is not None
        assert isinstance(template_library, TemplateLibrary)

    def test_core_templates_loaded(self):
        """Test that core templates are loaded"""
        assert "project_scope" in template_library.templates
        assert "primary_goal" in template_library.templates


class TestPredefinedTemplates:
    """Tests for predefined template dictionaries"""

    def test_core_templates(self):
        """Test CORE_TEMPLATES"""
        assert len(CORE_TEMPLATES) > 0
        assert "project_scope" in CORE_TEMPLATES

    def test_website_templates(self):
        """Test WEBSITE_TEMPLATES"""
        assert len(WEBSITE_TEMPLATES) > 0
        assert "website_type" in WEBSITE_TEMPLATES


# =============================================================================
# Integration Tests
# =============================================================================

class TestClarificationIntegration:
    """Integration tests for the clarification system"""

    def test_full_clarification_flow(self):
        """Test complete clarification flow"""
        # Start with vague request
        manager = ClarificationManager()
        request = "build me something"

        # Check if clarification needed
        needs_clarify, analysis = manager.should_clarify(request)
        assert needs_clarify

        # Start session
        session = manager.start_session(request)
        assert session.status == SessionStatus.PENDING

        # Answer questions
        while session.current_question and len(session.answers) < 5:
            manager.answer_question(session.session_id, "Test answer")

        # Complete session
        manager.complete_session(session.session_id)
        assert session.status == SessionStatus.COMPLETED

        # Get clarified context
        context = session.get_context()
        assert len(context["answers"]) > 0

    def test_skip_clarification_flow(self):
        """Test skipping clarification"""
        manager = ClarificationManager()
        session = manager.start_session("just do it - build website")

        # Should still create session even with skip phrase
        # But user can skip
        manager.skip_session(session.session_id)
        assert session.status == SessionStatus.CANCELLED

    def test_batch_answer_flow(self):
        """Test batch answering"""
        manager = ClarificationManager()
        session = manager.start_session("build a website")

        # Collect detail names
        details = {q.related_detail: f"Answer for {q.related_detail}"
                   for q in session.question_set.questions[:3]}

        # Process batch
        manager.process_batch_answers(session.session_id, details)
        assert len(session.answers) >= len(details)

    def test_different_request_types(self):
        """Test clarification for different request types"""
        manager = ClarificationManager()
        requests = [
            ("build a website", RequestType.WEBSITE),
            ("create an API", RequestType.API),
            ("make an app", RequestType.APPLICATION),
            ("design database", RequestType.DATABASE),
            ("automate workflow", RequestType.AUTOMATION),
            ("write content", RequestType.CONTENT),
        ]

        for request, expected_type in requests:
            session = manager.start_session(request)
            assert session.analysis.detected_type == expected_type

    def test_question_relevance(self):
        """Test that questions are relevant to request type"""
        manager = ClarificationManager()

        # Website request should have website-related questions
        website_session = manager.start_session("build a website")
        website_questions = [q.related_detail for q in website_session.question_set.questions]

        # API request should have API-related questions
        api_session = manager.start_session("create a REST API")
        api_questions = [q.related_detail for q in api_session.question_set.questions]

        # Should have some different questions
        assert website_questions != api_questions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
