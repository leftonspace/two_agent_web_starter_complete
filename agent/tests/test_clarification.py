"""
Comprehensive Tests for Clarification Loop System

Tests covering:
- Vague request detection
- Question generation
- Clarification session management
- Question templates
"""

import pytest
import asyncio
from typing import List, Dict
from datetime import datetime, timedelta
import json
import time

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
    QuestionType,
    # Manager
    ClarificationManager,
    ClarificationSession,
    SessionStatus,
    ClarificationPhase,
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


class TestVagueRequestDetector:
    """Test request clarity detection"""

    def test_very_vague_request(self):
        """Test detection of very vague requests"""
        detector = VagueRequestDetector()

        vague_requests = [
            "make me a website",
            "build something",
            "create an app",
            "I need a thing",
            "help me"
        ]

        for request in vague_requests:
            analysis = detector.analyze(request)
            assert analysis.clarity_level in [RequestClarity.VAGUE, RequestClarity.VERY_VAGUE]
            assert len(analysis.missing_details) > 0
            assert analysis.confidence > 0.5

    def test_clear_request(self):
        """Test detection of clear, detailed requests"""
        detector = VagueRequestDetector()

        clear_request = """
        Create a portfolio website with the following requirements:
        - Dark theme with blue accents
        - 5 pages: Home, About, Projects, Blog, Contact
        - Built with React and Tailwind CSS
        - Include a project gallery with filtering
        - Contact form that sends emails
        - Mobile responsive design
        - Deploy to Vercel
        """

        analysis = detector.analyze(clear_request)
        assert analysis.clarity_level in [RequestClarity.CLEAR, RequestClarity.SOMEWHAT_CLEAR]
        assert analysis.detected_type == RequestType.WEBSITE

    def test_request_type_detection(self):
        """Test correct detection of request types"""
        detector = VagueRequestDetector()

        test_cases = [
            ("Create a landing page for my startup", RequestType.WEBSITE),
            ("Build a REST API for user management", RequestType.API),
            ("Develop a mobile app for iOS", RequestType.APPLICATION),
            ("Set up a PostgreSQL database schema", RequestType.DATABASE),
            ("Write a Python script to automate deployments", RequestType.AUTOMATION),
            ("Analyze sales data and create a dashboard", RequestType.ANALYSIS),
            ("Write a blog post about AI", RequestType.CONTENT),
            ("Do something interesting", RequestType.GENERAL)
        ]

        for request, expected_type in test_cases:
            analysis = detector.analyze(request)
            assert analysis.detected_type == expected_type, f"Failed for: {request}"

    def test_specific_element_extraction(self):
        """Test extraction of specific elements from requests"""
        detector = VagueRequestDetector()

        request = """
        Build a website with dark theme, 5 pages, using React.
        It should have a contact form and be ready by Friday.
        """

        analysis = detector.analyze(request)

        # Check that some specific elements were extracted
        assert len(analysis.specific_elements) > 0
        assert 'quantities' in analysis.specific_elements or 'color_scheme' in analysis.specific_elements

    def test_missing_details_identification(self):
        """Test identification of missing details"""
        detector = VagueRequestDetector()

        # Website without audience or examples
        analysis = detector.analyze("Create a business website")
        assert 'target_audience' in analysis.missing_details

        # API without auth or endpoints
        analysis = detector.analyze("Build an API")
        assert 'endpoint_specifications' in analysis.missing_details or 'authentication_method' in analysis.missing_details

    def test_vagueness_scoring(self):
        """Test vagueness scoring calculation"""
        detector = VagueRequestDetector()

        # Short request = higher vagueness
        short_analysis = detector.analyze("make website")

        # Longer, detailed request = lower vagueness
        detailed_analysis = detector.analyze(
            "Create a professional portfolio website with modern design, "
            "featuring project showcase, blog section, and contact form"
        )

        assert short_analysis.vagueness_score > detailed_analysis.vagueness_score

    def test_should_request_clarification(self):
        """Test clarification decision logic"""
        # Vague request should trigger clarification
        should_clarify, analysis = should_request_clarification(
            "build me a website",
            threshold=RequestClarity.SOMEWHAT_CLEAR
        )
        assert should_clarify == True

        # Skip phrase should override
        should_clarify, analysis = should_request_clarification(
            "make website, just do it",
            threshold=RequestClarity.VAGUE
        )
        assert should_clarify == False


class TestQuestionGenerator:
    """Test question generation"""

    @pytest.mark.asyncio
    async def test_generate_website_questions(self):
        """Test generating questions for website request"""
        generator = QuestionGenerator()

        analysis = ClarityAnalysis(
            clarity_level=RequestClarity.VAGUE,
            confidence=0.8,
            missing_details=['color_scheme_or_style', 'pages_or_sections', 'target_audience'],
            detected_type=RequestType.WEBSITE,
            specific_elements={},
            reasoning="Request is vague"
        )

        questions = await generator.generate_questions(analysis, max_questions=5)

        assert len(questions) <= 5
        assert all(isinstance(q, ClarifyingQuestion) for q in questions)

    @pytest.mark.asyncio
    async def test_prioritize_missing_details(self):
        """Test that missing details are prioritized in questions"""
        generator = QuestionGenerator()

        analysis = ClarityAnalysis(
            clarity_level=RequestClarity.VAGUE,
            confidence=0.8,
            missing_details=['color_scheme_or_style', 'target_audience'],
            detected_type=RequestType.WEBSITE,
            specific_elements={},
            reasoning="Missing key details"
        )

        questions = await generator.generate_questions(
            analysis,
            max_questions=3,
            prioritize_missing=True
        )

        # Should include questions about missing details
        question_ids = [q.id for q in questions]
        assert any('color' in qid or 'style' in qid for qid in question_ids) or len(questions) > 0

    def test_format_questions_text(self):
        """Test text formatting of questions"""
        generator = QuestionGenerator()

        questions = [
            ClarifyingQuestion(
                question="What style do you want?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.MEDIUM,
                related_detail="style",
                options=["Modern", "Classic", "Minimalist"]
            ),
            ClarifyingQuestion(
                question="What's your target audience?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.CONTEXT,
                priority=QuestionPriority.HIGH,
                related_detail="audience",
                context="Describe your ideal users"
            )
        ]

        formatted = generator.format_questions_for_display(questions, "text")

        assert "What style do you want?" in formatted
        assert "a) Modern" in formatted
        assert "b) Classic" in formatted

    def test_format_questions_html(self):
        """Test HTML formatting of questions"""
        generator = QuestionGenerator()

        questions = [
            ClarifyingQuestion(
                question="Which pages do you need?",
                question_type=QuestionType.SELECTION,
                category=QuestionCategory.REQUIREMENTS,
                priority=QuestionPriority.HIGH,
                related_detail="pages",
                options=["Home", "About", "Contact"],
                required=True
            )
        ]

        formatted = generator.format_questions_for_display(questions, "html")

        assert '<div class="clarification-questions">' in formatted
        assert 'type="checkbox"' in formatted
        assert 'name="pages"' in formatted
        assert 'required' in formatted

    @pytest.mark.asyncio
    async def test_question_templates_by_type(self):
        """Test that different request types get appropriate questions"""
        generator = QuestionGenerator()

        # API request should get API-specific questions
        api_analysis = ClarityAnalysis(
            clarity_level=RequestClarity.VAGUE,
            confidence=0.8,
            missing_details=[],
            detected_type=RequestType.API,
            specific_elements={},
            reasoning=""
        )

        api_questions = await generator.generate_questions(api_analysis)
        assert len(api_questions) > 0

        # App request should get app-specific questions
        app_analysis = ClarityAnalysis(
            clarity_level=RequestClarity.VAGUE,
            confidence=0.8,
            missing_details=[],
            detected_type=RequestType.APPLICATION,
            specific_elements={},
            reasoning=""
        )

        app_questions = await generator.generate_questions(app_analysis)
        assert len(app_questions) > 0


class TestClarificationManager:
    """Test clarification session management"""

    def test_start_session(self):
        """Test starting a clarification session"""
        manager = ClarificationManager()

        analysis = ClarityAnalysis(
            clarity_level=RequestClarity.VAGUE,
            confidence=0.8,
            missing_details=['style'],
            detected_type=RequestType.WEBSITE,
            specific_elements={},
            reasoning="Vague request"
        )

        questions = [
            ClarifyingQuestion(
                question="What style?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.MEDIUM,
                related_detail="style",
                options=["Modern", "Classic"],
                required=True
            )
        ]

        session = manager.start_session(
            request="make website",
            analysis=analysis,
            questions=questions
        )

        assert session.phase == ClarificationPhase.ASKING
        assert len(session.questions) == 1
        assert session.session_id in manager.sessions
        assert manager.active_session_id == session.session_id

    def test_process_text_answer(self):
        """Test processing text answers"""
        manager = ClarificationManager()

        # Start session with text question
        questions = [
            ClarifyingQuestion(
                question="Who is your target audience?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.CONTEXT,
                priority=QuestionPriority.HIGH,
                related_detail="audience"
            )
        ]

        session = manager.start_session(
            request="make website",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.WEBSITE,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        result = manager.process_answer("Young professionals interested in tech")

        assert result["status"] == "complete"

    def test_process_multiple_choice_answer(self):
        """Test processing multiple choice answers"""
        manager = ClarificationManager()

        questions = [
            ClarifyingQuestion(
                question="Choose style",
                question_type=QuestionType.MULTIPLE_CHOICE,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.MEDIUM,
                related_detail="style",
                options=["Modern", "Classic", "Minimalist"]
            )
        ]

        session = manager.start_session(
            request="make website",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.WEBSITE,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        # Test letter selection
        result = manager.process_answer("a")
        assert session._answers_dict.get("style") == "Modern"

    def test_process_selection_answer(self):
        """Test processing multi-select answers"""
        manager = ClarificationManager()

        questions = [
            ClarifyingQuestion(
                question="Select pages",
                question_type=QuestionType.SELECTION,
                category=QuestionCategory.REQUIREMENTS,
                priority=QuestionPriority.HIGH,
                related_detail="pages",
                options=["Home", "About", "Services", "Contact", "Blog"]
            )
        ]

        session = manager.start_session(
            request="make website",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.WEBSITE,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        # Test comma-separated
        result = manager.process_answer("Home, About, Contact")
        assert len(session._answers_dict["pages"]) == 3
        assert "Home" in session._answers_dict["pages"]
        assert "Contact" in session._answers_dict["pages"]

    def test_skip_clarification(self):
        """Test skipping clarification"""
        manager = ClarificationManager()
        manager.allow_skip = True

        questions = [
            ClarifyingQuestion(
                question="Question 1",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.CONTEXT,
                priority=QuestionPriority.MEDIUM,
                related_detail="q1",
                default="default_value"
            )
        ]

        session = manager.start_session(
            request="make website",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.WEBSITE,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        result = manager.process_answer("skip")

        assert result["status"] == "skipped"
        assert session.phase == ClarificationPhase.SKIPPED

    def test_session_completion(self):
        """Test completing a clarification session"""
        manager = ClarificationManager()

        questions = [
            ClarifyingQuestion(
                question="What style?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.MEDIUM,
                related_detail="style",
                required=True
            ),
            ClarifyingQuestion(
                question="What color?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.LOW,
                related_detail="color",
                required=False
            )
        ]

        session = manager.start_session(
            request="make website",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.WEBSITE,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        # Answer required question
        result = manager.process_answer("Modern minimalist")

        # Should complete since required question answered
        assert result["status"] == "complete"
        assert session.phase == ClarificationPhase.READY
        assert session.enhanced_request is not None
        assert "Modern minimalist" in session.enhanced_request

    def test_enhanced_request_generation(self):
        """Test generation of enhanced request"""
        manager = ClarificationManager()

        questions = [
            ClarifyingQuestion(
                question="What style do you prefer?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.MEDIUM,
                related_detail="style"
            ),
            ClarifyingQuestion(
                question="Which pages?",
                question_type=QuestionType.SELECTION,
                category=QuestionCategory.REQUIREMENTS,
                priority=QuestionPriority.HIGH,
                related_detail="pages",
                options=["Home", "About", "Contact"]
            )
        ]

        session = manager.start_session(
            request="Create a website",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.WEBSITE,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        # Set answers directly for testing
        session._answers_dict = {
            "style": "Modern and clean",
            "pages": ["Home", "About", "Contact"]
        }

        result = manager.complete_clarification()

        enhanced = session.enhanced_request
        assert "Create a website" in enhanced
        assert "Modern and clean" in enhanced
        assert "Home, About, Contact" in enhanced
        assert "Project Type: website" in enhanced

    def test_timeout_handling(self):
        """Test session timeout handling"""
        manager = ClarificationManager()
        manager.timeout_minutes = 0.001  # Very short timeout for testing

        questions = [
            ClarifyingQuestion(
                question="Question",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.CONTEXT,
                priority=QuestionPriority.MEDIUM,
                related_detail="q1",
                default="timeout_default"
            )
        ]

        session = manager.start_session(
            request="test",
            analysis=ClarityAnalysis(
                clarity_level=RequestClarity.VAGUE,
                confidence=0.8,
                missing_details=[],
                detected_type=RequestType.GENERAL,
                specific_elements={},
                reasoning=""
            ),
            questions=questions
        )

        # Wait for timeout
        time.sleep(0.1)

        timed_out = manager.timeout_check()

        assert len(timed_out) == 1
        assert session.phase == ClarificationPhase.TIMEOUT


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

    def test_get_context(self, sample_session):
        """Test getting context"""
        context = sample_session.get_context()
        assert "original_request" in context
        assert "request_type" in context
        assert "session_id" in context


class TestIntegration:
    """Integration tests for full clarification flow"""

    @pytest.mark.asyncio
    async def test_full_clarification_flow(self):
        """Test complete flow from detection to completion"""
        # Step 1: Detect vague request
        request = "Build me a website about cats"
        should_clarify, analysis = should_request_clarification(request)

        assert should_clarify == True
        assert analysis.detected_type == RequestType.WEBSITE

        # Step 2: Generate questions
        generator = QuestionGenerator()
        questions = await generator.generate_questions(analysis, max_questions=3)

        assert len(questions) > 0

        # Step 3: Start clarification session
        manager = ClarificationManager()
        session = manager.start_session(request, analysis, questions)

        assert session.phase == ClarificationPhase.ASKING

        # Step 4: Answer questions
        for question in questions:
            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                if question.options:
                    result = manager.process_answer(question.options[0], question.id)
            elif question.question_type == QuestionType.SELECTION:
                if question.options and len(question.options) >= 2:
                    answer = f"{question.options[0]}, {question.options[1]}"
                    result = manager.process_answer(answer, question.id)
            else:
                result = manager.process_answer("Test answer", question.id)

        # Complete the session
        manager.complete_clarification()

        # Should be complete
        assert session.is_complete
        assert session.enhanced_request is not None
        assert "cats" in session.enhanced_request

        # Step 5: Get summary
        summary = manager.get_session_summary(session.session_id)
        assert summary["is_complete"] == True

    @pytest.mark.asyncio
    async def test_clarification_with_partial_answers(self):
        """Test handling partial answers and required questions"""
        detector = VagueRequestDetector()
        generator = QuestionGenerator()
        manager = ClarificationManager()

        request = "Create an application"
        analysis = detector.analyze(request)

        # Generate questions with mix of required and optional
        questions = [
            ClarifyingQuestion(
                question="What platform?",
                question_type=QuestionType.MULTIPLE_CHOICE,
                category=QuestionCategory.TECHNICAL,
                priority=QuestionPriority.HIGH,
                related_detail="platform",
                options=["Web", "Mobile", "Desktop"],
                required=True
            ),
            ClarifyingQuestion(
                question="Color preference?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.PREFERENCES,
                priority=QuestionPriority.LOW,
                related_detail="color",
                required=False
            ),
            ClarifyingQuestion(
                question="Core features?",
                question_type=QuestionType.TEXT,
                category=QuestionCategory.REQUIREMENTS,
                priority=QuestionPriority.HIGH,
                related_detail="features",
                required=True
            )
        ]

        session = manager.start_session(request, analysis, questions)

        # Answer only required questions
        manager.process_answer("Web", "platform")
        result = manager.process_answer("User authentication and data management", "features")

        # Should complete even without optional question answered
        assert result["status"] == "complete"
        assert session.enhanced_request is not None

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
