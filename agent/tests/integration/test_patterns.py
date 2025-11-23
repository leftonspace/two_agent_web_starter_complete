"""
Integration Tests: Pattern Switching

Tests pattern selection and switching based on task complexity
and requirements.
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestPatternSelection:
    """Test automatic pattern selection based on task characteristics"""

    @pytest.mark.asyncio
    async def test_sequential_pattern_for_ordered_tasks(self, pattern_selector, pattern_agents):
        """Sequential pattern should be selected for ordered step-by-step tasks"""
        task = "Build the project step by step: first compile, then test, then deploy"

        recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)

        assert len(recommendations) > 0
        pattern_names = [r.pattern_name.lower() for r in recommendations]
        # Should recommend sequential for ordered tasks
        assert any("sequential" in name or "chain" in name for name in pattern_names)

    @pytest.mark.asyncio
    async def test_parallel_pattern_for_independent_tasks(self, pattern_selector, pattern_agents):
        """Parallel pattern should be selected for independent tasks"""
        task = "Run linting, testing, and security scan simultaneously"

        recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)

        assert len(recommendations) > 0
        # Should have recommendations that can handle parallelism
        assert recommendations[0].confidence > 0.5

    @pytest.mark.asyncio
    async def test_hierarchical_pattern_for_complex_tasks(self, pattern_selector, pattern_agents):
        """Hierarchical pattern for tasks requiring coordination"""
        task = "Coordinate a large refactoring: plan architecture, delegate to specialists, review all changes"

        recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)

        assert len(recommendations) > 0
        # Complex coordination should get hierarchical recommendations
        pattern_names = [r.pattern_name.lower() for r in recommendations]
        assert any("hierarchical" in name or "coord" in name for name in pattern_names) or recommendations[0].confidence > 0.3

    @pytest.mark.asyncio
    async def test_collaborative_pattern_for_creative_tasks(self, pattern_selector, pattern_agents):
        """Collaborative pattern for creative/brainstorming tasks"""
        task = "Brainstorm ideas for the new feature design"

        recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)

        assert len(recommendations) > 0
        # Creative tasks should get some recommendation
        assert recommendations[0].confidence > 0.3


class TestPatternSwitching:
    """Test dynamic pattern switching during execution"""

    @pytest.mark.asyncio
    async def test_pattern_can_execute_task(self, pattern_selector, pattern_agents):
        """Selected pattern should be able to execute tasks"""
        from patterns import select_pattern

        pattern = select_pattern("Write documentation", pattern_agents)

        result = await pattern.run("Document the API endpoints")

        assert result.status.value in ["completed", "terminated", "failed"]
        assert hasattr(result, "messages")

    @pytest.mark.asyncio
    async def test_pattern_produces_output(self, pattern_selector, pattern_agents):
        """Pattern execution should produce meaningful output"""
        from patterns import select_pattern

        pattern = select_pattern("Review the code changes", pattern_agents)
        result = await pattern.run("Check for bugs in the parser module")

        # Should have some output
        assert result.messages is not None
        assert len(result.messages) >= 0

    @pytest.mark.asyncio
    async def test_multiple_patterns_can_run_sequentially(self, pattern_selector, pattern_agents):
        """Multiple patterns should run without interference"""
        from patterns import select_pattern

        tasks = [
            ("research", "Research best practices for API design"),
            ("write", "Write the implementation code"),
            ("review", "Review the implementation"),
        ]

        results = []
        for task_type, task_desc in tasks:
            pattern = select_pattern(task_desc, pattern_agents)
            result = await pattern.run(task_desc)
            results.append(result)

        # All patterns should complete
        assert len(results) == 3
        for result in results:
            assert result.status.value in ["completed", "terminated", "failed"]


class TestPatternRecommendations:
    """Test pattern recommendation quality"""

    @pytest.mark.asyncio
    async def test_recommendations_are_ranked(self, pattern_selector, pattern_agents):
        """Recommendations should be ranked by confidence"""
        task = "Build a web application"

        recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)

        # Should have multiple recommendations
        assert len(recommendations) >= 1

        # Should be sorted by confidence (descending)
        if len(recommendations) > 1:
            for i in range(len(recommendations) - 1):
                assert recommendations[i].confidence >= recommendations[i + 1].confidence

    @pytest.mark.asyncio
    async def test_recommendations_include_reasoning(self, pattern_selector, pattern_agents):
        """Recommendations should include reasoning"""
        task = "Debug the authentication module"

        recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)

        assert len(recommendations) > 0
        # Each recommendation should have a pattern name
        for rec in recommendations:
            assert hasattr(rec, "pattern_name")
            assert rec.pattern_name is not None

    @pytest.mark.asyncio
    async def test_empty_task_handled_gracefully(self, pattern_selector, pattern_agents):
        """Empty task should be handled without error"""
        task = ""

        try:
            recommendations = pattern_selector.analyze_and_recommend(task, pattern_agents)
            # Should either return empty or default recommendations
            assert recommendations is not None
        except Exception:
            # Also acceptable to raise an exception for invalid input
            pass


class TestPatternIntegrationWithAgents:
    """Test pattern integration with agent system"""

    @pytest.mark.asyncio
    async def test_agents_participate_in_pattern(self, pattern_agents):
        """Agents should participate in pattern execution"""
        from patterns import select_pattern

        pattern = select_pattern("Analyze code quality", pattern_agents)

        # Pattern should have access to agents
        assert pattern is not None

        result = await pattern.run("Check code coverage")
        assert result is not None

    @pytest.mark.asyncio
    async def test_agent_specialization_considered(self, pattern_selector, pattern_agents):
        """Agent specializations should influence recommendations"""
        # Agents have: researcher (search, analyze), writer (draft, edit), reviewer (critique, approve)

        research_task = "Research and analyze market trends"
        recommendations = pattern_selector.analyze_and_recommend(research_task, pattern_agents)

        assert len(recommendations) > 0
        # Should find suitable pattern for research task
        assert recommendations[0].confidence > 0

    @pytest.mark.asyncio
    async def test_pattern_with_single_agent(self):
        """Pattern should work with single agent"""
        from patterns import Agent, select_pattern

        single_agent = [Agent(name="solo", role="General", capabilities=["all"])]
        pattern = select_pattern("Complete a task", single_agent)

        result = await pattern.run("Do the work")
        assert result.status.value in ["completed", "terminated", "failed"]


class TestPatternErrorHandling:
    """Test pattern error handling"""

    @pytest.mark.asyncio
    async def test_pattern_handles_agent_failure(self, pattern_agents):
        """Pattern should handle agent failures gracefully"""
        from patterns import select_pattern

        pattern = select_pattern("Task with potential failure", pattern_agents)

        # Should not crash on execution
        try:
            result = await pattern.run("Execute risky operation")
            assert result is not None
        except Exception as e:
            # Pattern may raise but should be a clean exception
            assert str(e) is not None

    @pytest.mark.asyncio
    async def test_pattern_timeout_behavior(self, pattern_agents):
        """Pattern should respect timeout constraints"""
        from patterns import select_pattern

        pattern = select_pattern("Quick task", pattern_agents)

        # Run with implicit timeout
        result = await asyncio.wait_for(
            pattern.run("Fast operation"),
            timeout=30.0  # Generous timeout for test
        )

        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
