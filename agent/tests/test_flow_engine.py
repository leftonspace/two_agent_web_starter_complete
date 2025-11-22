"""
Comprehensive Tests for Flow Engine

Tests for state management, events, graph construction,
decorators, and flow execution.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from agent.flow.state import (
    FlowState, FlowContext, FlowStatus, StepStatus, StepResult
)
from agent.flow.events import (
    EventBus, FlowEvent, EventType, EventMatcher, or_, and_, not_
)
from agent.flow.graph import FlowGraph, FlowNode, FlowEdge, NodeType
from agent.flow.decorators import (
    start, listen, router, step, parallel,
    or_ as dec_or, and_ as dec_and,
    retry, timeout, validate_input, validate_output,
    get_flow_metadata
)
from agent.flow.engine import Flow, FlowExecutionError, FlowBuilder, run_flow


class TestFlowState:
    """Tests for flow state management"""

    def test_step_result_creation(self):
        """Test creating a step result"""
        result = StepResult(
            step_name="test_step",
            status=StepStatus.RUNNING,
            started_at=datetime.now()
        )
        assert result.step_name == "test_step"
        assert result.status == StepStatus.RUNNING
        assert result.output is None
        assert result.error is None

    def test_step_result_duration(self):
        """Test step duration calculation"""
        start = datetime.now()
        result = StepResult(
            step_name="test",
            status=StepStatus.COMPLETED,
            started_at=start,
            completed_at=datetime.now()
        )
        result.calculate_duration()
        assert result.duration_seconds is not None
        assert result.duration_seconds >= 0

    def test_flow_context_lifecycle(self):
        """Test flow context state transitions"""
        context = FlowContext()
        assert context.status == FlowStatus.PENDING

        context.start()
        assert context.status == FlowStatus.RUNNING
        assert context.started_at is not None

        context.complete(success=True)
        assert context.status == FlowStatus.COMPLETED
        assert context.completed_at is not None

    def test_flow_context_failure(self):
        """Test flow context failure handling"""
        context = FlowContext()
        context.start()
        context.fail("Test error")

        assert context.status == FlowStatus.FAILED
        assert context.error == "Test error"

    def test_flow_context_step_tracking(self):
        """Test step result tracking in context"""
        context = FlowContext()

        result = StepResult(
            step_name="step1",
            status=StepStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            output="result"
        )
        context.add_step_result(result)

        assert context.is_step_completed("step1")
        assert context.get_step_output("step1") == "result"
        assert not context.is_step_completed("step2")

    def test_flow_context_variables(self):
        """Test context variable management"""
        context = FlowContext()
        context.set_variable("key1", "value1")

        assert context.get_variable("key1") == "value1"
        assert context.get_variable("missing", "default") == "default"

    def test_flow_state_update(self):
        """Test flow state updates"""
        from pydantic import BaseModel

        class TestData(BaseModel):
            counter: int = 0
            name: str = ""

        state = FlowState(data=TestData())
        state.update(counter=5, name="test")

        assert state.data.counter == 5
        assert state.data.name == "test"
        assert len(state.history) == 1

    def test_flow_state_checkpoint(self):
        """Test state checkpointing"""
        from pydantic import BaseModel

        class TestData(BaseModel):
            value: int = 0

        state = FlowState(data=TestData(value=42))
        checkpoint = state.checkpoint()

        assert checkpoint["data"]["value"] == 42
        assert "context" in checkpoint


class TestEventBus:
    """Tests for event bus"""

    def test_emit_and_receive(self):
        """Test basic event emission and reception"""
        bus = EventBus()
        received = []

        def listener(event):
            received.append(event)

        bus.on(EventType.STEP_COMPLETED.value, listener)

        event = FlowEvent(
            type=EventType.STEP_COMPLETED,
            source="test",
            data={"result": "success"}
        )
        bus.emit(event)

        assert len(received) == 1
        assert received[0].type == EventType.STEP_COMPLETED

    @pytest.mark.asyncio
    async def test_async_emit(self):
        """Test async event emission"""
        bus = EventBus()
        received = []

        async def async_listener(event):
            received.append(event)

        bus.on_async(EventType.FLOW_STARTED.value, async_listener)

        event = FlowEvent(
            type=EventType.FLOW_STARTED,
            source="test",
            data={}
        )
        await bus.emit_async(event)

        assert len(received) == 1

    def test_wildcard_listener(self):
        """Test wildcard event listener"""
        bus = EventBus()
        received = []

        def listener(event):
            received.append(event)

        bus.on("*", listener)

        bus.emit(FlowEvent(type=EventType.STEP_STARTED, source="a", data={}))
        bus.emit(FlowEvent(type=EventType.STEP_COMPLETED, source="b", data={}))

        assert len(received) == 2

    def test_once_listener(self):
        """Test one-time event listener"""
        bus = EventBus()
        count = [0]

        def listener(event):
            count[0] += 1

        bus.once(EventType.CUSTOM.value, listener)

        bus.emit(FlowEvent(type=EventType.CUSTOM, source="test", data={}))
        bus.emit(FlowEvent(type=EventType.CUSTOM, source="test", data={}))

        assert count[0] == 1

    def test_event_history(self):
        """Test event history tracking"""
        bus = EventBus()

        bus.emit(FlowEvent(type=EventType.STEP_STARTED, source="a", data={}))
        bus.emit(FlowEvent(type=EventType.STEP_COMPLETED, source="a", data={}))

        history = bus.get_history()
        assert len(history) == 2

        step_history = bus.get_history(EventType.STEP_STARTED.value)
        assert len(step_history) == 1

    def test_remove_listener(self):
        """Test removing event listeners"""
        bus = EventBus()
        received = []

        def listener(event):
            received.append(event)

        bus.on(EventType.CUSTOM.value, listener)
        bus.off(EventType.CUSTOM.value, listener)

        bus.emit(FlowEvent(type=EventType.CUSTOM, source="test", data={}))
        assert len(received) == 0


class TestEventMatcher:
    """Tests for event matching"""

    def test_type_matching(self):
        """Test matching by event type"""
        matcher = EventMatcher().type(EventType.STEP_COMPLETED)

        event1 = FlowEvent(type=EventType.STEP_COMPLETED, source="a", data={})
        event2 = FlowEvent(type=EventType.STEP_FAILED, source="a", data={})

        assert matcher.matches(event1)
        assert not matcher.matches(event2)

    def test_source_matching(self):
        """Test matching by source"""
        matcher = EventMatcher().source("step1")

        event1 = FlowEvent(type=EventType.CUSTOM, source="step1", data={})
        event2 = FlowEvent(type=EventType.CUSTOM, source="step2", data={})

        assert matcher.matches(event1)
        assert not matcher.matches(event2)

    def test_data_matching(self):
        """Test matching by data content"""
        matcher = EventMatcher().data_contains("status", "success")

        event1 = FlowEvent(type=EventType.CUSTOM, source="a", data={"status": "success"})
        event2 = FlowEvent(type=EventType.CUSTOM, source="a", data={"status": "failed"})

        assert matcher.matches(event1)
        assert not matcher.matches(event2)

    def test_combined_matching(self):
        """Test combining multiple conditions"""
        matcher = (EventMatcher()
                   .type(EventType.STEP_COMPLETED)
                   .source("step1")
                   .data_contains("output"))

        event = FlowEvent(
            type=EventType.STEP_COMPLETED,
            source="step1",
            data={"output": "result"}
        )
        assert matcher.matches(event)

    def test_or_combinator(self):
        """Test OR combinator"""
        matcher1 = EventMatcher().source("a")
        matcher2 = EventMatcher().source("b")
        combined = or_(matcher1, matcher2)

        event_a = FlowEvent(type=EventType.CUSTOM, source="a", data={})
        event_b = FlowEvent(type=EventType.CUSTOM, source="b", data={})
        event_c = FlowEvent(type=EventType.CUSTOM, source="c", data={})

        assert combined(event_a)
        assert combined(event_b)
        assert not combined(event_c)

    def test_and_combinator(self):
        """Test AND combinator"""
        matcher1 = EventMatcher().type(EventType.STEP_COMPLETED)
        matcher2 = EventMatcher().data_contains("success", True)
        combined = and_(matcher1, matcher2)

        event1 = FlowEvent(
            type=EventType.STEP_COMPLETED,
            source="a",
            data={"success": True}
        )
        event2 = FlowEvent(
            type=EventType.STEP_COMPLETED,
            source="a",
            data={"success": False}
        )

        assert combined(event1)
        assert not combined(event2)


class TestFlowGraph:
    """Tests for flow graph construction"""

    def test_add_nodes(self):
        """Test adding nodes to graph"""
        graph = FlowGraph("test")

        node1 = FlowNode(name="start", type=NodeType.START)
        node2 = FlowNode(name="step1", type=NodeType.STEP)

        graph.add_node(node1).add_node(node2)

        assert len(graph.nodes) == 2
        assert graph.get_start_node().name == "start"

    def test_add_edges(self):
        """Test adding edges between nodes"""
        graph = FlowGraph("test")

        graph.add_node(FlowNode(name="a", type=NodeType.START))
        graph.add_node(FlowNode(name="b", type=NodeType.STEP))
        graph.add_edge("a", "b")

        assert "b" in graph.nodes["a"].next_nodes
        assert "a" in graph.nodes["b"].previous_nodes

    def test_get_path(self):
        """Test finding path between nodes"""
        graph = FlowGraph("test")

        graph.add_node(FlowNode(name="a", type=NodeType.START))
        graph.add_node(FlowNode(name="b", type=NodeType.STEP))
        graph.add_node(FlowNode(name="c", type=NodeType.END))
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")

        path = graph.get_path("a", "c")
        assert path == ["a", "b", "c"]

    def test_validate_graph(self):
        """Test graph validation"""
        graph = FlowGraph("test")

        # Graph without start node should fail
        graph.add_node(FlowNode(name="orphan", type=NodeType.STEP))
        errors = graph.validate()

        assert len(errors) > 0
        assert any("start" in e.lower() for e in errors)

    def test_cycle_detection(self):
        """Test cycle detection in graph"""
        graph = FlowGraph("test")

        graph.add_node(FlowNode(name="a", type=NodeType.START))
        graph.add_node(FlowNode(name="b", type=NodeType.STEP))
        graph.add_node(FlowNode(name="c", type=NodeType.STEP))
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("c", "b")  # Create cycle

        assert graph._has_cycle()

    def test_topological_order(self):
        """Test topological ordering"""
        graph = FlowGraph("test")

        graph.add_node(FlowNode(name="a", type=NodeType.START))
        graph.add_node(FlowNode(name="b", type=NodeType.STEP))
        graph.add_node(FlowNode(name="c", type=NodeType.STEP))
        graph.add_edge("a", "b")
        graph.add_edge("a", "c")
        graph.add_edge("b", "c")

        order = graph.get_topological_order()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")

    def test_visualization(self):
        """Test graph visualization"""
        graph = FlowGraph("test")

        graph.add_node(FlowNode(name="start", type=NodeType.START))
        graph.add_node(FlowNode(name="step1", type=NodeType.STEP))
        graph.add_edge("start", "step1")

        ascii_viz = graph.visualize("ascii")
        assert "start" in ascii_viz

        mermaid_viz = graph.visualize("mermaid")
        assert "graph TD" in mermaid_viz


class TestDecorators:
    """Tests for flow decorators"""

    def test_start_decorator(self):
        """Test @start decorator"""
        class TestFlow(Flow):
            @start(description="Entry point")
            def begin(self):
                return "started"

        flow = TestFlow()
        metadata = get_flow_metadata(TestFlow)

        assert "begin" in metadata
        assert metadata["begin"].type == "start"

    def test_listen_decorator(self):
        """Test @listen decorator"""
        class TestFlow(Flow):
            @start()
            def begin(self):
                return "data"

            @listen("begin")
            def process(self, data):
                return data.upper()

        flow = TestFlow()
        metadata = get_flow_metadata(TestFlow)

        assert "process" in metadata
        assert metadata["process"].type == "listener"
        assert "begin" in metadata["process"].triggers

    def test_router_decorator(self):
        """Test @router decorator"""
        class TestFlow(Flow):
            @start()
            def begin(self):
                return "data"

            @router("begin")
            def route(self, data):
                return "path_a" if data else "path_b"

        metadata = get_flow_metadata(TestFlow)

        assert "route" in metadata
        assert metadata["route"].type == "router"

    def test_retry_decorator(self):
        """Test @retry decorator"""
        attempts = [0]

        @retry(max_attempts=3, delay=0.01)
        def failing_function():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("Not yet")
            return "success"

        result = failing_function()
        assert result == "success"
        assert attempts[0] == 3

    def test_validate_input_decorator(self):
        """Test @validate_input decorator"""
        @validate_input(x=lambda v: v > 0)
        def positive_only(x):
            return x * 2

        assert positive_only(5) == 10

        with pytest.raises(ValueError):
            positive_only(-1)

    def test_validate_output_decorator(self):
        """Test @validate_output decorator"""
        @validate_output(lambda x: x > 0)
        def must_be_positive(x):
            return x - 10

        assert must_be_positive(15) == 5

        with pytest.raises(ValueError):
            must_be_positive(5)


class TestFlowExecution:
    """Tests for flow execution"""

    @pytest.mark.asyncio
    async def test_simple_flow(self):
        """Test simple linear flow"""
        class SimpleFlow(Flow):
            @start()
            def begin(self):
                return "hello"

            @listen("begin")
            def process(self, data):
                return data.upper()

        flow = SimpleFlow()
        result = await flow.run()

        assert result == "HELLO"
        assert flow.context.status == FlowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_flow_with_input(self):
        """Test flow with initial input"""
        class InputFlow(Flow):
            @start()
            def begin(self, data):
                return f"processed: {data}"

        flow = InputFlow()
        result = await flow.run("test input")

        assert result == "processed: test input"

    @pytest.mark.asyncio
    async def test_multi_step_flow(self):
        """Test multi-step flow execution"""
        class MultiStepFlow(Flow):
            @start()
            def step1(self):
                return 1

            @listen("step1")
            def step2(self, data):
                return data + 1

            @listen("step2")
            def step3(self, data):
                return data + 1

        flow = MultiStepFlow()
        result = await flow.run()

        assert result == 3
        assert len(flow.execution_history) == 3

    @pytest.mark.asyncio
    async def test_router_flow(self):
        """Test flow with router"""
        class RouterFlow(Flow):
            @start()
            def begin(self):
                return 10

            @router("begin")
            def route(self, data):
                if data > 5:
                    return "high_path"
                return "low_path"

            @step()
            def high_path(self, data):
                return "HIGH"

            @step()
            def low_path(self, data):
                return "LOW"

        flow = RouterFlow()
        result = await flow.run()

        assert result == "HIGH"

    @pytest.mark.asyncio
    async def test_flow_error_handling(self):
        """Test flow error handling"""
        class ErrorFlow(Flow):
            @start()
            def begin(self):
                raise ValueError("Test error")

        flow = ErrorFlow()

        with pytest.raises(FlowExecutionError) as exc_info:
            await flow.run()

        assert "Test error" in str(exc_info.value)
        assert flow.context.status == FlowStatus.FAILED

    @pytest.mark.asyncio
    async def test_flow_events(self):
        """Test flow event emission"""
        events = []

        class EventFlow(Flow):
            @start()
            def begin(self):
                return "done"

        flow = EventFlow()
        flow._event_bus = EventBus()
        flow._event_bus.on("*", lambda e: events.append(e))

        await flow.run()

        event_types = [e.type for e in events]
        assert EventType.FLOW_STARTED in event_types
        assert EventType.STEP_STARTED in event_types
        assert EventType.STEP_COMPLETED in event_types
        assert EventType.FLOW_COMPLETED in event_types

    @pytest.mark.asyncio
    async def test_async_steps(self):
        """Test async step handlers"""
        class AsyncFlow(Flow):
            @start()
            async def begin(self):
                await asyncio.sleep(0.01)
                return "async result"

        flow = AsyncFlow()
        result = await flow.run()

        assert result == "async result"

    def test_flow_visualization(self):
        """Test flow visualization"""
        class VizFlow(Flow):
            @start()
            def begin(self):
                return "data"

            @listen("begin")
            def process(self, data):
                return data

        flow = VizFlow()
        viz = flow.visualize("ascii")

        assert "begin" in viz

    def test_flow_validation(self):
        """Test flow validation"""
        class ValidFlow(Flow):
            @start()
            def begin(self):
                return "data"

        flow = ValidFlow()
        errors = flow.validate()

        # Should have no errors for simple valid flow
        # May have "unreachable" warning since no listener
        assert not any("No start node" in e for e in errors)


class TestFlowBuilder:
    """Tests for programmatic flow building"""

    @pytest.mark.asyncio
    async def test_builder_basic(self):
        """Test basic flow building"""
        def step1():
            return "hello"

        def step2(data):
            return data.upper()

        flow = (FlowBuilder("test")
                .add_start("begin", step1)
                .add_step("process", step2, after="begin")
                .build())

        result = await flow.run()
        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_builder_multiple_steps(self):
        """Test building flow with multiple steps"""
        def start():
            return 0

        def add_one(x):
            return x + 1

        def add_two(x):
            return x + 2

        flow = (FlowBuilder()
                .add_start("start", start)
                .add_step("add1", add_one, after="start")
                .add_step("add2", add_two, after="add1")
                .build())

        result = await flow.run()
        assert result == 3


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_complex_flow(self):
        """Test complex flow with multiple features"""
        class ComplexFlow(Flow):
            def __init__(self):
                super().__init__()
                self.log = []

            @start(description="Initialize")
            def initialize(self):
                self.log.append("init")
                return {"count": 0}

            @listen("initialize")
            def process(self, data):
                self.log.append("process")
                data["count"] += 1
                return data

            @listen("process")
            def finalize(self, data):
                self.log.append("finalize")
                return f"Final count: {data['count']}"

        flow = ComplexFlow()
        result = await flow.run()

        assert result == "Final count: 1"
        assert flow.log == ["init", "process", "finalize"]
        assert flow.context.status == FlowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_flow_with_state(self):
        """Test flow with typed state"""
        from pydantic import BaseModel

        class MyState(BaseModel):
            counter: int = 0
            messages: list = []

        class StatefulFlow(Flow):
            @start()
            def begin(self):
                return "start"

            @listen("begin")
            def increment(self, data):
                return data + "_incremented"

        flow = StatefulFlow()
        result = await flow.run()

        assert "_incremented" in result

    @pytest.mark.asyncio
    async def test_event_driven_flow(self):
        """Test event-driven flow patterns"""
        events_received = []

        class EventDrivenFlow(Flow):
            @start()
            def emit_event(self):
                return {"type": "data", "value": 42}

            @listen("emit_event")
            def handle_event(self, event_data):
                return event_data["value"] * 2

        flow = EventDrivenFlow()
        flow._event_bus = EventBus()
        flow._event_bus.on("*", lambda e: events_received.append(e.type))

        result = await flow.run()

        assert result == 84
        assert EventType.STEP_COMPLETED in events_received


class TestPerformance:
    """Performance tests"""

    @pytest.mark.asyncio
    async def test_many_steps(self):
        """Test flow with many steps"""
        class ManyStepsFlow(Flow):
            @start()
            def begin(self):
                return 0

            @listen("begin")
            def step1(self, x): return x + 1

            @listen("step1")
            def step2(self, x): return x + 1

            @listen("step2")
            def step3(self, x): return x + 1

            @listen("step3")
            def step4(self, x): return x + 1

            @listen("step4")
            def step5(self, x): return x + 1

        flow = ManyStepsFlow()
        result = await flow.run()

        assert result == 5
        assert len(flow.execution_history) == 6

    @pytest.mark.asyncio
    async def test_rapid_execution(self):
        """Test rapid flow execution"""
        class QuickFlow(Flow):
            @start()
            def quick(self):
                return "done"

        import time
        start_time = time.time()

        for _ in range(100):
            flow = QuickFlow()
            await flow.run()

        elapsed = time.time() - start_time
        assert elapsed < 5.0  # Should complete 100 runs in under 5 seconds
