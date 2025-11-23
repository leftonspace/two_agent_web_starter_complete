"""
Integration Tests: Complete Task Flow

Tests the full journey from clarification through task completion,
verifying all components work together correctly.
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestClarificationToCompletion:
    """Test complete flow from vague request to task completion"""

    @pytest.mark.asyncio
    async def test_vague_request_triggers_clarification(self, clarification_manager):
        """Vague requests should trigger clarification questions"""
        vague_request = "make me a website"

        needs_clarification, analysis = clarification_manager.should_clarify(vague_request)

        assert needs_clarification is True
        assert analysis.clarity_level.value in ["vague", "very_vague"]

    @pytest.mark.asyncio
    async def test_detailed_request_skips_clarification(self, clarification_manager):
        """Detailed requests should skip clarification"""
        detailed_request = """
        Build a React website with Tailwind CSS that includes:
        - A hero section with gradient background
        - Navigation with responsive hamburger menu
        - Contact form with email validation
        - Dark mode toggle using context API
        The design should be modern and minimal with blue/purple color scheme.
        """

        needs_clarification, analysis = clarification_manager.should_clarify(detailed_request)

        assert needs_clarification is False

    @pytest.mark.asyncio
    async def test_clarification_session_flow(self, clarification_manager):
        """Test complete clarification session with answers"""
        request = "build me an app"

        # Start session
        needs, analysis = clarification_manager.should_clarify(request)
        assert needs

        session = clarification_manager.start_session(request, analysis)
        assert session.phase.value == "asking"
        assert len(session.questions) > 0

        # Answer questions
        for i, question in enumerate(session.questions[:3]):
            result = clarification_manager.process_answer(
                f"Answer {i+1} for {question.related_detail}",
                question.id
            )

        # Session should progress
        assert len(session.answers) >= 3

    @pytest.mark.asyncio
    async def test_skip_clarification_phrase(self, clarification_manager):
        """Test that skip phrases bypass clarification"""
        request = "make website, just do it"

        needs, analysis = clarification_manager.should_clarify(request)

        # "just do it" should trigger skip
        assert needs is False


class TestTaskExecutionFlow:
    """Test task execution through the council system"""

    @pytest.mark.asyncio
    async def test_council_processes_simple_task(self, council, mock_llm):
        """Council should successfully process a simple task"""
        mock_llm.set_response("complexity", "simple")
        mock_llm.set_response("quality", "good")

        result = await council.process_task("Fix a typo in the README")

        assert result["status"] == "completed"
        assert "task_id" in result
        assert result["complexity"] is not None

    @pytest.mark.asyncio
    async def test_council_tracks_metrics_after_task(self, council, mock_llm):
        """Council should update metrics after task completion"""
        initial_tasks = council.tasks_processed

        await council.process_task("Write a unit test")

        assert council.tasks_processed == initial_tasks + 1

    @pytest.mark.asyncio
    async def test_councillors_updated_after_task(self, council, mock_llm):
        """Councillors should have updated stats after task"""
        # Get initial state
        councillors = council._get_active_councillors()
        initial_tasks = sum(c.metrics.tasks_completed for c in councillors)

        await council.process_task("Implement a feature")

        # At least one councillor should have more tasks
        final_tasks = sum(c.metrics.tasks_completed for c in councillors)
        assert final_tasks > initial_tasks


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios"""

    @pytest.mark.asyncio
    async def test_website_project_flow(self, council, clarification_manager, mock_llm):
        """Test building a website from vague request to completion"""
        # Step 1: Vague request
        request = "I need a website for my business"

        # Step 2: Clarification
        needs, analysis = clarification_manager.should_clarify(request)
        assert needs

        session = clarification_manager.start_session(request, analysis)

        # Step 3: Simulate answers
        enhanced_request = f"""
        {request}

        Additional details:
        - Type: E-commerce website
        - Style: Modern, minimalist
        - Pages: Home, Products, About, Contact
        - Tech: React with Tailwind CSS
        """

        # Step 4: Process through council
        mock_llm.set_response("website", "Created e-commerce website structure")

        result = await council.process_task(enhanced_request)

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_code_review_flow(self, council, mock_llm):
        """Test code review workflow"""
        mock_llm.set_response("review", "Code looks good with minor suggestions")

        result = await council.process_task(
            "Review this Python function for bugs and improvements"
        )

        assert result["status"] == "completed"
        assert result["quality_score"] is not None

    @pytest.mark.asyncio
    async def test_multiple_tasks_sequential(self, council, mock_llm):
        """Test processing multiple tasks in sequence"""
        tasks = [
            "Write a function to parse JSON",
            "Add error handling to the parser",
            "Write tests for the parser",
        ]

        results = []
        for task in tasks:
            result = await council.process_task(task)
            results.append(result)

        # All should complete
        assert all(r["status"] == "completed" for r in results)

        # Tasks processed should increase
        assert council.tasks_processed >= 3


class TestErrorHandling:
    """Test error handling in the flow"""

    @pytest.mark.asyncio
    async def test_handles_empty_task(self, council):
        """Should handle empty task gracefully"""
        result = await council.process_task("")

        # Should either complete with default or fail gracefully
        assert result["status"] in ["completed", "failed"]

    @pytest.mark.asyncio
    async def test_handles_llm_failure(self, council, mock_llm):
        """Should handle LLM failures"""
        mock_llm.set_failure_mode(max_failures=1)

        # Task should still attempt to complete
        result = await council.process_task("Simple task")

        # Result should exist even if status varies
        assert "status" in result

    @pytest.mark.asyncio
    async def test_council_recovers_from_errors(self, council, mock_llm):
        """Council should recover and continue after errors"""
        # First task fails
        mock_llm.set_failure_mode(max_failures=1)
        result1 = await council.process_task("Task 1")

        # Reset mock
        mock_llm.reset()

        # Second task should work
        result2 = await council.process_task("Task 2")

        assert result2["status"] == "completed"


class TestFlowIntegrationWithPatterns:
    """Test flow integration with pattern selection"""

    @pytest.mark.asyncio
    async def test_pattern_selected_for_task(self, pattern_selector, pattern_agents):
        """Pattern should be selected based on task"""
        recommendations = pattern_selector.analyze_and_recommend(
            "Build a website step by step",
            pattern_agents
        )

        assert len(recommendations) > 0
        # Sequential pattern should score well for "step by step"
        pattern_names = [r.pattern_name for r in recommendations]
        assert any("sequential" in name for name in pattern_names)

    @pytest.mark.asyncio
    async def test_pattern_executes_task(self, pattern_selector, pattern_agents):
        """Selected pattern should execute task"""
        from patterns import select_pattern

        pattern = select_pattern(
            "Collaborate on writing documentation",
            pattern_agents
        )

        result = await pattern.run("Write API documentation")

        assert result.status.value in ["completed", "terminated"]
        assert len(result.messages) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
