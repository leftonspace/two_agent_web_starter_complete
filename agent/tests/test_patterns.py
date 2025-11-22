"""
Comprehensive Tests for Orchestration Patterns

Tests for all pattern implementations:
- Base Pattern classes
- SequentialPattern
- HierarchicalPattern
- AutoSelectPattern
- RoundRobinPattern
- ManualPattern
- PatternSelector
"""

import pytest
import asyncio
from typing import Dict, Any, Optional, List

from agent.patterns import (
    # Base classes
    Pattern,
    PatternStatus,
    PatternConfig,
    PatternResult,
    Agent,
    Message,
    MessageRole,
    # Pattern implementations
    SequentialPattern,
    OrderedSequentialPattern,
    PipelinePattern,
    HierarchicalPattern,
    HierarchicalAgent,
    HierarchyLevel,
    AutoSelectPattern,
    KeywordSelector,
    LLMSelector,
    SelectionCriteria,
    RoundRobinPattern,
    WeightedRoundRobinPattern,
    ManualPattern,
    InteractivePattern,
    # Selector
    PatternSelector,
    TaskAnalysis,
    TaskComplexity,
    TaskType,
    PatternRecommendation,
    select_pattern,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def simple_agents():
    """Create simple test agents"""
    return [
        Agent(name="agent1", role="Researcher", description="Research expert"),
        Agent(name="agent2", role="Writer", description="Content writer"),
        Agent(name="agent3", role="Editor", description="Content editor"),
    ]


@pytest.fixture
def capable_agents():
    """Create agents with capabilities"""
    return [
        Agent(
            name="researcher",
            role="Researcher",
            description="Research specialist",
            capabilities=["web_search", "data_analysis", "research"]
        ),
        Agent(
            name="developer",
            role="Developer",
            description="Software developer",
            capabilities=["coding", "debugging", "testing"]
        ),
        Agent(
            name="reviewer",
            role="Reviewer",
            description="Code reviewer",
            capabilities=["code_review", "quality_assurance"]
        ),
    ]


@pytest.fixture
def hierarchical_agents():
    """Create hierarchical agents"""
    manager = HierarchicalAgent(
        name="manager",
        role="Project Manager",
        level=HierarchyLevel.MANAGER,
        subordinates=["supervisor"]
    )
    supervisor = HierarchicalAgent(
        name="supervisor",
        role="Team Lead",
        level=HierarchyLevel.SUPERVISOR,
        reports_to="manager",
        subordinates=["worker1", "worker2"]
    )
    worker1 = HierarchicalAgent(
        name="worker1",
        role="Developer",
        level=HierarchyLevel.WORKER,
        reports_to="supervisor"
    )
    worker2 = HierarchicalAgent(
        name="worker2",
        role="Tester",
        level=HierarchyLevel.WORKER,
        reports_to="supervisor"
    )
    return [manager, supervisor, worker1, worker2]


class MockAgent(Agent):
    """Agent that tracks execution and returns configurable responses"""

    def __init__(self, name: str, responses: Optional[List[str]] = None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.responses = responses or [f"Response from {name}"]
        self.execution_count = 0
        self.received_messages: List[str] = []

    async def execute(self, message: str, context: Dict[str, Any] = None) -> str:
        self.received_messages.append(message)
        response = self.responses[min(self.execution_count, len(self.responses) - 1)]
        self.execution_count += 1
        return response


# =============================================================================
# Base Classes Tests
# =============================================================================

class TestBaseClasses:
    """Test base classes and data models"""

    def test_agent_creation(self):
        """Test Agent dataclass creation"""
        agent = Agent(
            name="test",
            role="Test Role",
            description="Test Description",
            capabilities=["cap1", "cap2"]
        )
        assert agent.name == "test"
        assert agent.role == "Test Role"
        assert len(agent.capabilities) == 2

    def test_agent_matches_task(self):
        """Test agent task matching"""
        agent = Agent(
            name="researcher",
            role="Research Specialist",
            description="Expert in data analysis",
            capabilities=["research", "analysis"]
        )

        score = agent.matches_task(["research", "data"])
        assert score > 0

        score = agent.matches_task(["cooking", "baking"])
        assert score == 0

    def test_message_creation(self):
        """Test Message dataclass creation"""
        msg = Message(
            content="Hello",
            sender="agent1",
            role=MessageRole.AGENT
        )
        assert msg.content == "Hello"
        assert msg.sender == "agent1"
        assert msg.role == MessageRole.AGENT

    def test_message_to_dict(self):
        """Test Message serialization"""
        msg = Message(content="Test", sender="user", role=MessageRole.USER)
        d = msg.to_dict()
        assert d["content"] == "Test"
        assert d["sender"] == "user"
        assert d["role"] == "user"

    def test_pattern_config_defaults(self):
        """Test PatternConfig default values"""
        config = PatternConfig()
        assert config.max_rounds == 10
        assert config.timeout_seconds == 300
        assert config.allow_parallel == False
        assert "DONE" in config.termination_keywords

    def test_pattern_result_to_dict(self):
        """Test PatternResult serialization"""
        result = PatternResult(
            status=PatternStatus.COMPLETED,
            messages=[],
            rounds_completed=5,
            agents_used=["agent1", "agent2"]
        )
        d = result.to_dict()
        assert d["status"] == "completed"
        assert d["rounds_completed"] == 5


# =============================================================================
# Sequential Pattern Tests
# =============================================================================

class TestSequentialPattern:
    """Test SequentialPattern implementation"""

    @pytest.mark.asyncio
    async def test_basic_sequence(self, simple_agents):
        """Test basic sequential execution"""
        pattern = SequentialPattern(simple_agents)

        # First selection
        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)
        assert agent.name == "agent1"

        # Second selection
        pattern.add_message(Message("msg1", "agent1"))
        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)
        assert agent.name == "agent2"

        # Third selection
        pattern.add_message(Message("msg2", "agent2"))
        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)
        assert agent.name == "agent3"

    @pytest.mark.asyncio
    async def test_full_run(self):
        """Test full pattern execution"""
        agents = [
            MockAgent("agent1", responses=["First response"]),
            MockAgent("agent2", responses=["Second response"]),
            MockAgent("agent3", responses=["DONE"]),
        ]
        pattern = SequentialPattern(agents)

        result = await pattern.run("Start task")

        assert result.status == PatternStatus.COMPLETED
        assert len(result.agents_used) == 3
        assert "agent1" in result.agents_used
        assert "agent2" in result.agents_used
        assert "agent3" in result.agents_used

    @pytest.mark.asyncio
    async def test_termination_keyword(self):
        """Test termination on keyword"""
        agents = [
            MockAgent("agent1", responses=["Processing"]),
            MockAgent("agent2", responses=["COMPLETE"]),
            MockAgent("agent3", responses=["Should not run"]),
        ]
        pattern = SequentialPattern(agents)

        result = await pattern.run("Start task")

        assert result.status == PatternStatus.COMPLETED
        assert agents[2].execution_count == 0

    def test_reset(self, simple_agents):
        """Test pattern reset"""
        pattern = SequentialPattern(simple_agents)
        pattern.current_round = 5
        pattern.add_message(Message("test", "agent1"))

        pattern.reset()

        assert pattern.current_round == 0
        assert len(pattern.history) == 0


class TestOrderedSequentialPattern:
    """Test OrderedSequentialPattern"""

    def test_custom_order(self, simple_agents):
        """Test custom agent ordering"""
        pattern = OrderedSequentialPattern(
            simple_agents,
            order=["agent3", "agent1", "agent2"]
        )

        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)
        assert agent.name == "agent3"

        pattern.add_message(Message("msg", "agent3"))
        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)
        assert agent.name == "agent1"


class TestPipelinePattern:
    """Test PipelinePattern"""

    @pytest.mark.asyncio
    async def test_pipeline_data_collection(self):
        """Test pipeline data collection"""
        agents = [
            MockAgent("step1", responses=["Data from step 1"]),
            MockAgent("step2", responses=["Processed: step 1 data"]),
            MockAgent("step3", responses=["Final: DONE"]),
        ]
        pattern = PipelinePattern(agents)

        result = await pattern.run("Start pipeline")

        data = pattern.get_pipeline_data()
        assert "step1" in data
        assert "step2" in data
        assert "step3" in data


# =============================================================================
# Hierarchical Pattern Tests
# =============================================================================

class TestHierarchicalPattern:
    """Test HierarchicalPattern implementation"""

    def test_hierarchy_creation(self, hierarchical_agents):
        """Test hierarchical agent setup"""
        pattern = HierarchicalPattern(hierarchical_agents)

        manager = pattern._hierarchy.get("manager")
        assert manager is not None
        assert manager.level == HierarchyLevel.MANAGER

    def test_starts_with_manager(self, hierarchical_agents):
        """Test that pattern starts with top-level manager"""
        pattern = HierarchicalPattern(hierarchical_agents)

        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)

        assert agent.name == "manager"

    def test_hierarchy_visualization(self, hierarchical_agents):
        """Test hierarchy visualization"""
        pattern = HierarchicalPattern(hierarchical_agents)

        viz = pattern.get_hierarchy_visualization()

        assert "manager" in viz
        assert "supervisor" in viz
        assert "worker1" in viz

    def test_inferred_hierarchy(self, simple_agents):
        """Test hierarchy inference from agent order"""
        pattern = HierarchicalPattern(simple_agents)

        # First agent should be manager
        first = pattern._hierarchy.get("agent1")
        assert first.level == HierarchyLevel.MANAGER

        # Last agent should be worker
        last = pattern._hierarchy.get("agent3")
        assert last.level == HierarchyLevel.WORKER


class TestHierarchicalAgent:
    """Test HierarchicalAgent creation"""

    def test_from_agent(self):
        """Test creating HierarchicalAgent from Agent"""
        base = Agent(name="test", role="Test Role")
        hierarchical = HierarchicalAgent.from_agent(
            base,
            level=HierarchyLevel.SUPERVISOR,
            reports_to="manager"
        )

        assert hierarchical.name == "test"
        assert hierarchical.level == HierarchyLevel.SUPERVISOR
        assert hierarchical.reports_to == "manager"


# =============================================================================
# AutoSelect Pattern Tests
# =============================================================================

class TestAutoSelectPattern:
    """Test AutoSelectPattern implementation"""

    @pytest.mark.asyncio
    async def test_keyword_selection(self, capable_agents):
        """Test keyword-based agent selection"""
        pattern = AutoSelectPattern(capable_agents)

        # Add message about research
        pattern.add_message(Message(
            "I need help with research and data analysis",
            "user",
            MessageRole.USER
        ))

        ctx = pattern.get_context()
        agent = await pattern._select_next_agent_async(ctx)

        assert agent.name == "researcher"

    @pytest.mark.asyncio
    async def test_avoid_repeat(self, capable_agents):
        """Test avoiding repeated selection"""
        pattern = AutoSelectPattern(
            capable_agents,
            avoid_repeat=True,
            max_same_agent=1
        )

        # Select same agent multiple times
        pattern._selection_history = ["researcher", "researcher"]

        available = pattern._get_available_agents()

        # Researcher should not be available
        names = [a.name for a in available]
        assert "researcher" not in names

    @pytest.mark.asyncio
    async def test_selection_stats(self, capable_agents):
        """Test selection statistics"""
        pattern = AutoSelectPattern(capable_agents)
        pattern._selection_history = ["a1", "a2", "a1", "a1"]

        stats = pattern.get_selection_stats()

        assert stats["total_selections"] == 4
        assert stats["selection_counts"]["a1"] == 3
        assert stats["most_selected"][0] == "a1"


class TestKeywordSelector:
    """Test KeywordSelector"""

    @pytest.mark.asyncio
    async def test_select_by_capability(self, capable_agents):
        """Test selection by capability matching"""
        selector = KeywordSelector()

        ctx = {
            "last_message": Message("need help with coding", "user")
        }

        agent = await selector.select(capable_agents, ctx)

        assert agent.name == "developer"

    @pytest.mark.asyncio
    async def test_fallback_to_first(self, capable_agents):
        """Test fallback when no good match"""
        selector = KeywordSelector()

        ctx = {
            "last_message": Message("xyz abc random text", "user")
        }
        criteria = SelectionCriteria(min_relevance_score=0.9)

        agent = await selector.select(capable_agents, ctx, criteria)

        # Should fall back to first agent
        assert agent == capable_agents[0]


class TestLLMSelector:
    """Test LLMSelector"""

    @pytest.mark.asyncio
    async def test_without_callback_falls_back(self, capable_agents):
        """Test fallback when no LLM callback"""
        selector = LLMSelector()  # No callback

        ctx = {
            "last_message": Message("help with coding", "user")
        }

        agent = await selector.select(capable_agents, ctx)

        # Should fall back to keyword selection
        assert agent is not None

    @pytest.mark.asyncio
    async def test_with_mock_callback(self, capable_agents):
        """Test with mock LLM callback"""
        async def mock_llm(prompt: str) -> str:
            return "developer"

        selector = LLMSelector(llm_callback=mock_llm)

        ctx = {
            "last_message": Message("help me", "user")
        }

        agent = await selector.select(capable_agents, ctx)

        assert agent.name == "developer"


# =============================================================================
# RoundRobin Pattern Tests
# =============================================================================

class TestRoundRobinPattern:
    """Test RoundRobinPattern implementation"""

    def test_rotation(self, simple_agents):
        """Test basic rotation"""
        pattern = RoundRobinPattern(simple_agents)

        agents_selected = []
        for _ in range(6):  # Two full rotations
            ctx = pattern.get_context()
            agent = pattern.select_next_agent(ctx)
            agents_selected.append(agent.name)
            pattern.add_message(Message("msg", agent.name))

        assert agents_selected == [
            "agent1", "agent2", "agent3",
            "agent1", "agent2", "agent3"
        ]

    def test_reverse_rotation(self, simple_agents):
        """Test reverse rotation"""
        pattern = RoundRobinPattern(simple_agents, reverse=True)

        agents_selected = []
        for _ in range(3):
            ctx = pattern.get_context()
            agent = pattern.select_next_agent(ctx)
            agents_selected.append(agent.name)

        # Should go in reverse
        assert agents_selected[0] == "agent1"  # Starts at 0
        assert agents_selected[1] == "agent3"  # Then wraps to end

    def test_rotation_stats(self, simple_agents):
        """Test rotation statistics"""
        pattern = RoundRobinPattern(simple_agents)

        for _ in range(6):
            ctx = pattern.get_context()
            pattern.select_next_agent(ctx)

        stats = pattern.get_rotation_stats()

        assert stats["total_rotations"] == 6
        assert all(count == 2 for count in stats["rounds_per_agent"].values())


class TestWeightedRoundRobinPattern:
    """Test WeightedRoundRobinPattern"""

    def test_weighted_rotation(self, simple_agents):
        """Test weighted rotation"""
        weights = {"agent1": 2, "agent2": 1, "agent3": 1}
        pattern = WeightedRoundRobinPattern(simple_agents, weights=weights)

        selections = []
        for _ in range(4):
            ctx = pattern.get_context()
            agent = pattern.select_next_agent(ctx)
            selections.append(agent.name)

        # agent1 should appear twice as often
        assert selections.count("agent1") == 2


# =============================================================================
# Manual Pattern Tests
# =============================================================================

class TestManualPattern:
    """Test ManualPattern implementation"""

    def test_explicit_selection(self, simple_agents):
        """Test explicit agent selection"""
        pattern = ManualPattern(simple_agents)

        pattern.set_next_agent("agent2")

        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)

        assert agent.name == "agent2"

    def test_selection_with_callback(self, simple_agents):
        """Test selection with callback"""
        def selector(agents, ctx):
            return "agent3"

        pattern = ManualPattern(simple_agents, selection_callback=selector)

        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)

        assert agent.name == "agent3"

    def test_default_agent(self, simple_agents):
        """Test default agent fallback"""
        pattern = ManualPattern(simple_agents, default_agent="agent2")

        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)

        assert agent.name == "agent2"

    def test_selection_pending(self, simple_agents):
        """Test pending selection state"""
        pattern = ManualPattern(simple_agents)

        ctx = pattern.get_context()
        agent = pattern.select_next_agent(ctx)

        assert agent is None
        assert pattern.is_selection_pending()

    def test_selection_history(self, simple_agents):
        """Test selection history tracking"""
        pattern = ManualPattern(simple_agents)

        pattern.set_next_agent("agent1")
        pattern.select_next_agent({})

        pattern.set_next_agent("agent2")
        pattern.select_next_agent({})

        history = pattern.get_selection_history()

        assert len(history) == 2
        assert history[0]["agent"] == "agent1"
        assert history[0]["method"] == "explicit"


class TestInteractivePattern:
    """Test InteractivePattern"""

    def test_selection_prompt(self, simple_agents):
        """Test selection prompt generation"""
        pattern = InteractivePattern(simple_agents)

        prompt = pattern.get_selection_prompt()

        assert "agent1" in prompt
        assert "agent2" in prompt
        assert "agent3" in prompt

    def test_parse_selection_by_name(self, simple_agents):
        """Test parsing selection by name"""
        pattern = InteractivePattern(simple_agents)

        result = pattern.parse_selection("agent2")
        assert result == "agent2"

        result = pattern.parse_selection("AGENT1")  # Case insensitive
        assert result == "agent1"

    def test_parse_selection_by_number(self, simple_agents):
        """Test parsing selection by number"""
        pattern = InteractivePattern(simple_agents)

        result = pattern.parse_selection("2")
        assert result == "agent2"


# =============================================================================
# Pattern Selector Tests
# =============================================================================

class TestPatternSelector:
    """Test PatternSelector implementation"""

    def test_analyze_task(self, simple_agents):
        """Test task analysis"""
        selector = PatternSelector()

        analysis = selector.analyze_task(
            "First research the topic, then write an article, finally edit it",
            simple_agents
        )

        assert analysis.task_type == TaskType.LINEAR
        assert analysis.requires_order == True
        assert analysis.agent_count == 3

    def test_detect_hierarchical(self):
        """Test hierarchical task detection"""
        selector = PatternSelector()

        analysis = selector.analyze_task(
            "Manager should delegate tasks to team and approve final results"
        )

        assert analysis.requires_hierarchy == True

    def test_recommend_patterns(self, simple_agents):
        """Test pattern recommendations"""
        selector = PatternSelector()

        recommendations = selector.analyze_and_recommend(
            "Take turns discussing the topic until consensus",
            simple_agents
        )

        assert len(recommendations) > 0
        # Round-robin should be recommended for "take turns"
        names = [r.pattern_name for r in recommendations]
        assert "roundrobin" in names or "weighted_roundrobin" in names

    def test_get_best_pattern(self, simple_agents):
        """Test getting best pattern"""
        selector = PatternSelector()

        pattern = selector.get_best_pattern(
            "Process data step by step",
            simple_agents
        )

        assert isinstance(pattern, Pattern)

    def test_select_pattern_function(self, simple_agents):
        """Test convenience function"""
        pattern = select_pattern(
            "Collaborate on project",
            simple_agents
        )

        assert isinstance(pattern, Pattern)

    def test_register_custom_pattern(self):
        """Test registering custom pattern"""
        selector = PatternSelector()

        class CustomPattern(SequentialPattern):
            pass

        selector.register_pattern(
            "custom",
            CustomPattern,
            keywords=["custom", "special"]
        )

        assert "custom" in selector._pattern_registry


class TestTaskAnalysis:
    """Test TaskAnalysis dataclass"""

    def test_complexity_levels(self):
        """Test complexity detection"""
        selector = PatternSelector()

        simple = selector.analyze_task("Simple quick task")
        assert simple.complexity == TaskComplexity.SIMPLE

        complex_task = selector.analyze_task(
            "Very complex enterprise-level intricate system"
        )
        assert complex_task.complexity in [
            TaskComplexity.COMPLEX,
            TaskComplexity.VERY_COMPLEX
        ]


class TestPatternRecommendation:
    """Test PatternRecommendation"""

    def test_create_instance(self, simple_agents):
        """Test creating pattern from recommendation"""
        rec = PatternRecommendation(
            pattern_class=SequentialPattern,
            pattern_name="sequential",
            score=0.9,
            reasoning="Good for ordered tasks",
            config_suggestions={"max_rounds": 5}
        )

        pattern = rec.create_instance(simple_agents)

        assert isinstance(pattern, SequentialPattern)
        assert pattern.config.max_rounds == 5


# =============================================================================
# Integration Tests
# =============================================================================

class TestPatternIntegration:
    """Integration tests for patterns"""

    @pytest.mark.asyncio
    async def test_sequential_with_mock_agents(self):
        """Test full sequential workflow"""
        researcher = MockAgent(
            "researcher",
            responses=["Research findings: AI is evolving"]
        )
        writer = MockAgent(
            "writer",
            responses=["Article draft: AI Evolution Today"]
        )
        editor = MockAgent(
            "editor",
            responses=["Final article: DONE"]
        )

        pattern = SequentialPattern([researcher, writer, editor])
        result = await pattern.run("Write about AI")

        assert result.status == PatternStatus.COMPLETED
        assert researcher.execution_count == 1
        assert writer.execution_count == 1
        assert editor.execution_count == 1

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test pattern timeout"""
        class SlowAgent(Agent):
            async def execute(self, message: str, context: Dict = None) -> str:
                await asyncio.sleep(10)
                return "Done"

        config = PatternConfig(timeout_seconds=1)
        pattern = SequentialPattern([SlowAgent(name="slow")], config)

        result = await pattern.run("Start")

        assert result.status == PatternStatus.TIMEOUT
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_pattern_callbacks(self):
        """Test pattern event callbacks"""
        agents = [
            MockAgent("agent1", responses=["Response 1"]),
            MockAgent("agent2", responses=["DONE"]),
        ]

        messages_received = []
        rounds_completed = []
        agents_selected = []

        pattern = SequentialPattern(agents)
        pattern.on_message(lambda m: messages_received.append(m))
        pattern.on_round_complete(lambda r: rounds_completed.append(r))
        pattern.on_agent_selected(lambda a: agents_selected.append(a))

        await pattern.run("Start")

        assert len(messages_received) > 0
        assert len(agents_selected) > 0

    @pytest.mark.asyncio
    async def test_autoselect_full_workflow(self, capable_agents):
        """Test AutoSelectPattern full workflow"""
        # Create mock agents with specific capabilities
        research_agent = MockAgent(
            "researcher",
            role="Researcher",
            capabilities=["research", "analysis"],
            responses=["Research complete"]
        )
        dev_agent = MockAgent(
            "developer",
            role="Developer",
            capabilities=["coding", "implementation"],
            responses=["Code written DONE"]
        )

        pattern = AutoSelectPattern([research_agent, dev_agent])

        result = await pattern.run("Research and implement new feature")

        assert result.status == PatternStatus.COMPLETED


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling in patterns"""

    @pytest.mark.asyncio
    async def test_empty_agents_list(self):
        """Test handling empty agents list"""
        pattern = SequentialPattern([])

        result = await pattern.run("Start")

        # Should complete without agents
        assert result.status == PatternStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_agent_exception(self):
        """Test handling agent exceptions"""
        class FailingAgent(Agent):
            async def execute(self, message: str, context: Dict = None) -> str:
                raise ValueError("Agent failed")

        pattern = SequentialPattern([FailingAgent(name="failer")])

        result = await pattern.run("Start")

        assert result.status == PatternStatus.FAILED
        assert "Agent failed" in result.error

    def test_invalid_agent_reference(self, simple_agents):
        """Test handling invalid agent reference"""
        pattern = ManualPattern(simple_agents)

        success = pattern.set_next_agent("nonexistent")

        assert success == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
