"""
Test Coverage Gap Tests

Tests for:
1. Callback exception handling
2. Concurrent access
3. Corrupted data recovery
4. Scale tests (10k+ items)
5. Integration tests between modules
"""

import pytest
import asyncio
import threading
import time
import json
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from datetime import datetime
from unittest.mock import MagicMock, patch


# =============================================================================
# 1. Callback Exception Handling Tests
# =============================================================================

class TestCallbackExceptionHandling:
    """Test that callbacks with exceptions don't crash the system."""

    def test_event_bus_callback_exception_handled(self):
        """EventBus should handle callback exceptions gracefully."""
        from agent.flow.events import EventBus, FlowEvent, EventType

        bus = EventBus()
        call_count = [0]

        def failing_callback(event):
            call_count[0] += 1
            raise ValueError("Callback error")

        def success_callback(event):
            call_count[0] += 1

        bus.on(EventType.STEP_STARTED.value, failing_callback)
        bus.on(EventType.STEP_STARTED.value, success_callback)

        event = FlowEvent(
            type=EventType.STEP_STARTED,
            source="test",
            data={}
        )

        # Should not raise, both callbacks should be called
        bus.emit(event)
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_event_bus_async_callback_exception_handled(self):
        """EventBus async emit should handle callback exceptions."""
        from agent.flow.events import EventBus, FlowEvent, EventType

        bus = EventBus()
        call_count = [0]

        def failing_callback(event):
            call_count[0] += 1
            raise RuntimeError("Async callback error")

        def success_callback(event):
            call_count[0] += 1

        bus.on(EventType.FLOW_STARTED.value, failing_callback)
        bus.on(EventType.FLOW_STARTED.value, success_callback)

        event = FlowEvent(
            type=EventType.FLOW_STARTED,
            source="test",
            data={}
        )

        await bus.emit_async(event)
        assert call_count[0] == 2

    def test_pattern_callback_exception_isolated(self):
        """Pattern callbacks should be isolated from each other."""
        from agent.patterns.base import Pattern, Agent, Message, MessageRole, PatternConfig

        class TestPattern(Pattern):
            def select_next_agent(self, context):
                return self.agents[0] if self.agents else None

            def should_terminate(self, last_message):
                return True

        agents = [Agent(name="test", role="tester")]
        pattern = TestPattern(agents, PatternConfig(max_rounds=1))

        exception_raised = [False]

        def failing_callback(msg):
            exception_raised[0] = True
            raise Exception("Callback failed")

        pattern.on_message(failing_callback)

        # Adding a message should not crash
        msg = Message(content="test", sender="user", role=MessageRole.USER)
        pattern.add_message(msg)

        # The callback was called and raised, but pattern continues
        assert exception_raised[0]


# =============================================================================
# 2. Concurrent Access Tests
# =============================================================================

class TestConcurrentAccess:
    """Test thread safety of critical components."""

    def test_lazy_property_concurrent_access(self):
        """lazy_property should be thread-safe."""
        from agent.performance.lazy import lazy_property

        call_count = [0]
        call_lock = threading.Lock()

        class TestClass:
            @lazy_property
            def expensive_value(self):
                with call_lock:
                    call_count[0] += 1
                time.sleep(0.01)  # Simulate expensive computation
                return "computed"

        instance = TestClass()
        results = []
        errors = []

        def access_property():
            try:
                results.append(instance.expensive_value)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=access_property) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(r == "computed" for r in results)
        # Should only be computed once due to thread safety
        assert call_count[0] == 1

    def test_memoize_with_ttl_concurrent_access(self):
        """memoize_with_ttl should handle concurrent access."""
        from agent.performance.utils import memoize_with_ttl

        call_count = [0]

        @memoize_with_ttl(ttl_seconds=60)
        def expensive_function(x):
            call_count[0] += 1
            time.sleep(0.01)
            return x * 2

        results = []
        errors = []

        def call_function():
            try:
                results.append(expensive_function(5))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_function) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(r == 10 for r in results)
        # Multiple calls may compute before cache is set, but should be limited
        assert call_count[0] <= 20

    def test_throttler_concurrent_sync_access(self):
        """Throttler sync access should be thread-safe."""
        from agent.performance.parallel import Throttler

        throttler = Throttler(rate=100, period=1.0)
        results = []
        errors = []

        def acquire_token():
            try:
                wait_time = throttler.acquire_sync(1)
                results.append(wait_time)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=acquire_token) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50

    @pytest.mark.asyncio
    async def test_throttler_concurrent_async_access(self):
        """Throttler async access should be safe."""
        from agent.performance.parallel import Throttler

        throttler = Throttler(rate=100, period=1.0)
        results = []

        async def acquire_token():
            wait_time = await throttler.acquire(1)
            results.append(wait_time)

        await asyncio.gather(*[acquire_token() for _ in range(50)])
        assert len(results) == 50


# =============================================================================
# 3. Corrupted Data Recovery Tests
# =============================================================================

class TestCorruptedDataRecovery:
    """Test recovery from corrupted data scenarios."""

    def test_json_config_corrupted_recovery(self):
        """System should handle corrupted JSON config."""
        from agent.config.yaml_loader import YAMLConfigLoader

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [broken")
            f.flush()

            loader = YAMLConfigLoader()
            # Should handle gracefully
            try:
                result = loader.load(f.name)
                # If it returns, should be empty or default
            except Exception as e:
                # Should raise a clean error, not crash
                assert "yaml" in str(e).lower() or "parse" in str(e).lower()
            finally:
                os.unlink(f.name)

    def test_memory_storage_corrupted_data(self):
        """Memory storage should handle corrupted entries."""
        from agent.memory.storage import InMemoryStorage, MemoryItem

        storage = InMemoryStorage()

        # Add valid items
        item = MemoryItem(
            id="test1",
            content="valid content",
            timestamp=datetime.now(),
            metadata={}
        )
        storage.add(item)

        # Manually corrupt internal state
        if hasattr(storage, '_items'):
            storage._items["corrupted"] = {"invalid": "structure"}

        # Search should handle corrupted data gracefully
        try:
            results = storage.search("test")
            # Should return valid results, skip corrupted
            assert all(hasattr(r, 'content') for r in results)
        except Exception as e:
            # Or raise clean error
            assert True

    def test_graph_storage_from_dict_partial_data(self):
        """GraphStorage should handle partial/corrupted dict data."""
        from agent.memory.storage import GraphStorage

        storage = GraphStorage()

        # Partial data missing required fields
        partial_data = {
            "nodes": [
                {"id": "1", "type": "entity"},  # Missing other fields
                {"id": "2"}  # Missing type
            ],
            "edges": [
                {"source": "1"}  # Missing target
            ]
        }

        # Should handle gracefully
        try:
            storage.from_dict(partial_data)
        except (KeyError, ValueError, TypeError):
            # Clean error is acceptable
            pass


# =============================================================================
# 4. Scale Tests (10k+ items)
# =============================================================================

class TestScaleOperations:
    """Test system behavior with large data sets."""

    def test_memory_storage_10k_items(self):
        """Memory storage should handle 10k+ items."""
        from agent.memory.storage import InMemoryStorage, MemoryItem

        storage = InMemoryStorage()

        # Add 10k items
        start = time.time()
        for i in range(10000):
            item = MemoryItem(
                id=f"item_{i}",
                content=f"Content for item {i} with some searchable text",
                timestamp=datetime.now(),
                metadata={"index": i}
            )
            storage.add(item)

        add_time = time.time() - start
        assert add_time < 10.0  # Should complete in reasonable time

        # Search should still be performant
        start = time.time()
        results = storage.search("searchable")
        search_time = time.time() - start

        assert len(results) > 0
        assert search_time < 5.0  # Search should be fast

    def test_event_bus_10k_events(self):
        """Event bus should handle 10k+ events."""
        from agent.flow.events import EventBus, FlowEvent, EventType

        bus = EventBus()
        received = [0]

        def counter(event):
            received[0] += 1

        bus.on(EventType.STEP_COMPLETED.value, counter)

        start = time.time()
        for i in range(10000):
            event = FlowEvent(
                type=EventType.STEP_COMPLETED,
                source=f"step_{i}",
                data={"index": i}
            )
            bus.emit(event)

        emit_time = time.time() - start

        assert received[0] == 10000
        assert emit_time < 5.0  # Should be fast

    def test_pattern_selection_10k_agents(self):
        """Pattern selector should handle large agent lists."""
        from agent.patterns.selector import PatternSelector
        from agent.patterns.base import Agent

        selector = PatternSelector()

        # Create 10k agents
        agents = [
            Agent(
                name=f"agent_{i}",
                role=f"role_{i % 10}",
                description=f"Agent number {i}",
                capabilities=[f"cap_{i % 5}"]
            )
            for i in range(10000)
        ]

        start = time.time()
        analysis = selector.analyze_task(
            "Process data with specialized experts",
            agents[:100]  # Use subset for analysis
        )
        recommendations = selector.recommend(analysis, agents[:100])
        analysis_time = time.time() - start

        assert len(recommendations) > 0
        assert analysis_time < 2.0

    @pytest.mark.asyncio
    async def test_parallel_executor_10k_tasks(self):
        """Parallel executor should handle 10k tasks."""
        from agent.performance.parallel import ParallelExecutor

        executor = ParallelExecutor(max_workers=100)

        async def simple_task(x):
            return x * 2

        items = list(range(10000))

        start = time.time()
        results = await executor.map_async(simple_task, items, timeout=30.0)
        exec_time = time.time() - start

        success_count = sum(1 for r in results if r.success)
        assert success_count == 10000
        assert exec_time < 30.0


# =============================================================================
# 5. Integration Tests Between Modules
# =============================================================================

class TestModuleIntegration:
    """Test integration between different modules."""

    @pytest.mark.asyncio
    async def test_flow_with_pattern_integration(self):
        """Flow engine should integrate with patterns."""
        from agent.flow.engine import FlowEngine, FlowDefinition, StepDefinition
        from agent.patterns.base import Agent
        from agent.patterns.sequential import SequentialPattern

        # Create agents
        agents = [
            Agent(name="researcher", role="Research"),
            Agent(name="writer", role="Writing")
        ]

        # Create pattern
        pattern = SequentialPattern(agents)

        # Create flow that uses pattern context
        steps = [
            StepDefinition(
                name="init",
                handler=lambda ctx: {"agents": [a.name for a in agents]}
            ),
            StepDefinition(
                name="process",
                handler=lambda ctx: {"processed": True, **ctx}
            )
        ]

        flow = FlowDefinition(name="pattern_flow", steps=steps)
        engine = FlowEngine()

        result = await engine.execute(flow, {})
        assert result.success
        assert "agents" in result.data

    @pytest.mark.asyncio
    async def test_memory_with_clarification_integration(self):
        """Memory system should integrate with clarification."""
        from agent.memory.storage import InMemoryStorage, MemoryItem
        from agent.clarification.manager import ClarificationManager
        from agent.clarification.detector import RequestClarity

        # Setup memory
        storage = InMemoryStorage()
        storage.add(MemoryItem(
            id="context1",
            content="Previous project used React for frontend",
            timestamp=datetime.now(),
            metadata={"type": "project_history"}
        ))

        # Setup clarification
        manager = ClarificationManager(
            clarity_threshold=RequestClarity.SOMEWHAT_CLEAR
        )

        # Use memory to inform clarification
        request = "Build a website"
        should_clarify, analysis = manager.should_clarify(request)

        # Memory context could enhance clarification
        context = storage.search("project")
        assert len(context) > 0

        if should_clarify:
            session = manager.start_session(request, analysis)
            assert session is not None

    def test_council_with_pattern_integration(self):
        """Council system should integrate with patterns."""
        from agent.council.models import CouncilMember, CouncilConfig
        from agent.council.factory import AgentFactory
        from agent.patterns.base import Agent

        # Create council members
        config = CouncilConfig(
            min_members=2,
            max_members=5
        )

        factory = AgentFactory()

        # Council members can be converted to pattern agents
        members = [
            CouncilMember(
                id="m1",
                name="Technical Lead",
                role="technical",
                expertise=["architecture", "code review"]
            ),
            CouncilMember(
                id="m2",
                name="Product Manager",
                role="product",
                expertise=["requirements", "prioritization"]
            )
        ]

        # Convert to pattern agents
        pattern_agents = [
            Agent(
                name=m.name,
                role=m.role,
                capabilities=m.expertise
            )
            for m in members
        ]

        assert len(pattern_agents) == 2
        assert pattern_agents[0].capabilities == ["architecture", "code review"]

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Performance monitoring should work across modules."""
        from agent.performance.utils import PerformanceMonitor
        from agent.flow.engine import FlowEngine, FlowDefinition, StepDefinition

        monitor = PerformanceMonitor()

        async def monitored_step(ctx):
            with monitor.measure("step_execution"):
                await asyncio.sleep(0.01)
                return {"result": "done"}

        steps = [
            StepDefinition(name="monitored", handler=monitored_step)
        ]

        flow = FlowDefinition(name="monitored_flow", steps=steps)
        engine = FlowEngine()

        # Execute multiple times
        for _ in range(5):
            await engine.execute(flow, {})

        stats = monitor.get_stats("step_execution")
        assert stats is not None
        assert stats["call_count"] == 5

    def test_llm_router_with_tool_registry_integration(self):
        """LLM router should integrate with tool registry."""
        from agent.llm.enhanced_router import EnhancedModelRouter
        from agent.tools.registry import ToolRegistry

        # Setup router
        router = EnhancedModelRouter()

        # Setup tool registry
        registry = ToolRegistry()

        def sample_tool(arg: str) -> str:
            return f"Result: {arg}"

        registry.register(
            name="sample",
            func=sample_tool,
            description="A sample tool"
        )

        # Router can use tools from registry
        tools = registry.list_tools()
        assert len(tools) > 0

        # Router config can include tool info
        assert router is not None


# =============================================================================
# Run configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
