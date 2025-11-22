"""
Flow Execution Engine

Main flow execution engine with support for conditional routing,
parallel execution, and dynamic workflows.
"""

import asyncio
import inspect
import traceback
from typing import Any, Dict, List, Optional, Type, TypeVar, Callable
from datetime import datetime

from pydantic import BaseModel

from .state import FlowState, FlowContext, FlowStatus, StepStatus, StepResult
from .events import EventBus, FlowEvent, EventType
from .graph import FlowGraph, FlowNode, NodeType
from .decorators import get_flow_metadata, StepMetadata, OrCombinator, AndCombinator

StateT = TypeVar('StateT', bound=BaseModel)


class FlowExecutionError(Exception):
    """Error during flow execution"""

    def __init__(self, message: str, step_name: str = None, cause: Exception = None):
        super().__init__(message)
        self.step_name = step_name
        self.cause = cause


class Flow(BaseModel):
    """Base class for flows with dynamic routing

    Subclass this and use decorators to define flow steps:

    ```python
    class MyFlow(Flow):
        @start()
        def begin(self):
            return "Hello"

        @listen("begin")
        def process(self, data):
            return data.upper()
    ```
    """

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._graph: Optional[FlowGraph] = None
        self._metadata: Optional[Dict[str, StepMetadata]] = None
        self._event_bus: Optional[EventBus] = None
        self._state: Optional[FlowState] = None
        self._execution_history: List[str] = []

    def _build_graph(self) -> FlowGraph:
        """Build execution graph from decorated methods"""
        graph = FlowGraph(name=self.__class__.__name__)

        # Get metadata from decorators
        metadata = get_flow_metadata(self.__class__)

        # Also check instance methods directly
        for name in dir(self):
            try:
                method = getattr(self, name)
                if hasattr(method, '_flow_metadata'):
                    metadata[method._flow_metadata.name] = method._flow_metadata
            except AttributeError:
                continue

        if not metadata:
            raise ValueError("No flow steps defined. Use @start(), @listen(), etc.")

        self._metadata = metadata

        # Find start node
        start_nodes = [m for m in metadata.values() if m.type == "start"]
        if not start_nodes:
            raise ValueError("No @start() decorated method found")
        if len(start_nodes) > 1:
            raise ValueError("Multiple @start() decorated methods found")

        start_meta = start_nodes[0]

        # Add start node
        start_handler = getattr(self, start_meta.name, None)
        start_node = FlowNode(
            name=start_meta.name,
            type=NodeType.START,
            handler=start_handler,
            description=start_meta.description,
            timeout=start_meta.timeout
        )
        graph.add_node(start_node)

        # Process other nodes
        for meta in metadata.values():
            if meta.type == "start":
                continue

            handler = getattr(self, meta.name, None)

            if meta.type == "listener":
                node = FlowNode(
                    name=meta.name,
                    type=NodeType.STEP,
                    handler=handler,
                    description=meta.description,
                    timeout=meta.timeout,
                    retries=meta.retries
                )
                graph.add_node(node)

                # Connect based on triggers
                for trigger in meta.triggers:
                    trigger_name = trigger
                    if isinstance(trigger, OrCombinator):
                        for event in trigger.get_event_names():
                            if event in graph.nodes:
                                graph.add_edge(event, meta.name)
                    elif isinstance(trigger, AndCombinator):
                        for event in trigger.get_event_names():
                            if event in graph.nodes:
                                graph.add_edge(event, meta.name)
                    elif trigger_name in graph.nodes:
                        graph.add_edge(trigger_name, meta.name)

            elif meta.type == "router":
                node = FlowNode(
                    name=meta.name,
                    type=NodeType.ROUTER,
                    handler=handler,
                    description=meta.description
                )
                graph.add_node(node)

                if meta.router_source and meta.router_source in graph.nodes:
                    graph.add_edge(meta.router_source, meta.name)

            elif meta.type == "parallel":
                node = FlowNode(
                    name=meta.name,
                    type=NodeType.PARALLEL,
                    handler=handler,
                    parallel_nodes=meta.triggers
                )
                graph.add_node(node)

            else:
                node = FlowNode(
                    name=meta.name,
                    type=NodeType.STEP,
                    handler=handler,
                    description=meta.description,
                    timeout=meta.timeout,
                    retries=meta.retries
                )
                graph.add_node(node)

        return graph

    async def run(self, initial_input: Any = None) -> Any:
        """Execute the flow

        Args:
            initial_input: Initial input data for the flow

        Returns:
            Final output from the flow
        """
        # Build graph if not already built
        if self._graph is None:
            self._graph = self._build_graph()

        # Initialize state
        state_class = self._get_state_class()
        if state_class:
            state_data = state_class()
        else:
            state_data = BaseModel()

        self._state = FlowState(data=state_data)
        self._event_bus = EventBus()
        self._execution_history = []

        # Start execution
        context = self._state.context
        context.start()

        await self._emit_event(EventType.FLOW_STARTED, {
            "input": initial_input,
            "flow_id": context.flow_id
        })

        try:
            # Execute from start node
            start_node = self._graph.get_start_node()
            if not start_node:
                raise FlowExecutionError("No start node found in graph")

            result = await self._execute_node(start_node, initial_input)

            # Mark flow as completed
            context.complete(success=True)

            await self._emit_event(EventType.FLOW_COMPLETED, {
                "result": result,
                "duration": context.get_duration()
            })

            return result

        except Exception as e:
            # Mark flow as failed
            context.fail(str(e))

            await self._emit_event(EventType.FLOW_FAILED, {
                "error": str(e),
                "traceback": traceback.format_exc()
            })

            raise FlowExecutionError(
                f"Flow execution failed: {e}",
                step_name=context.current_step,
                cause=e
            )

    async def _execute_node(self, node: FlowNode, input_data: Any = None) -> Any:
        """Execute a single node"""
        context = self._state.context
        context.current_step = node.name
        self._execution_history.append(node.name)

        # Create step result
        step_result = StepResult(
            step_name=node.name,
            status=StepStatus.RUNNING,
            started_at=datetime.now()
        )

        await self._emit_event(EventType.STEP_STARTED, {
            "step": node.name,
            "input": input_data
        }, source=node.name)

        try:
            # Execute handler with retries
            result = await self._execute_with_retry(node, input_data)

            # Update step result
            step_result.status = StepStatus.COMPLETED
            step_result.completed_at = datetime.now()
            step_result.output = result
            step_result.calculate_duration()

            context.add_step_result(step_result)

            await self._emit_event(EventType.STEP_COMPLETED, {
                "step": node.name,
                "output": result,
                "duration": step_result.duration_seconds
            }, source=node.name)

            # Handle different node types
            return await self._handle_node_result(node, result, input_data)

        except Exception as e:
            # Update step result
            step_result.status = StepStatus.FAILED
            step_result.completed_at = datetime.now()
            step_result.error = str(e)
            step_result.calculate_duration()

            context.add_step_result(step_result)

            await self._emit_event(EventType.STEP_FAILED, {
                "step": node.name,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, source=node.name)

            raise

    async def _execute_with_retry(self, node: FlowNode, input_data: Any) -> Any:
        """Execute node handler with retry logic"""
        handler = node.handler
        if not handler:
            return input_data

        max_retries = node.retries
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if inspect.iscoroutinefunction(handler):
                    if input_data is not None:
                        result = await handler(input_data)
                    else:
                        result = await handler()
                else:
                    if input_data is not None:
                        result = handler(input_data)
                    else:
                        result = handler()
                return result

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await self._emit_event(EventType.STEP_RETRYING, {
                        "step": node.name,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "error": str(e)
                    }, source=node.name)
                    await asyncio.sleep(1.0 * (attempt + 1))  # Simple backoff

        raise last_error

    async def _handle_node_result(self, node: FlowNode, result: Any, original_input: Any) -> Any:
        """Handle node result based on node type"""
        if node.type == NodeType.ROUTER:
            # Router node - route based on result
            next_step = result
            if isinstance(next_step, str) and next_step in self._graph.nodes:
                next_node = self._graph.nodes[next_step]
                return await self._execute_node(next_node, original_input)
            else:
                raise FlowExecutionError(
                    f"Router returned invalid next step: {next_step}",
                    step_name=node.name
                )

        elif node.type == NodeType.PARALLEL:
            # Execute parallel nodes
            parallel_names = node.parallel_nodes
            if parallel_names:
                tasks = []
                for parallel_node_name in parallel_names:
                    if parallel_node_name in self._graph.nodes:
                        parallel_node = self._graph.nodes[parallel_node_name]
                        tasks.append(self._execute_node(parallel_node, result))

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    # Check for errors
                    for r in results:
                        if isinstance(r, Exception):
                            raise r
                    return results

            return result

        else:
            # Regular step - continue to next nodes
            next_nodes = self._graph.get_next_nodes(node.name)

            if len(next_nodes) == 0:
                # No next nodes - end of flow
                return result
            elif len(next_nodes) == 1:
                # Single next node
                return await self._execute_node(next_nodes[0], result)
            else:
                # Multiple next nodes (parallel execution)
                tasks = [self._execute_node(n, result) for n in next_nodes]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if isinstance(r, Exception):
                        raise r
                return results

    async def _emit_event(self, event_type: EventType, data: Any, source: str = None):
        """Emit a flow event"""
        if self._event_bus:
            event = FlowEvent(
                type=event_type,
                source=source or self.__class__.__name__,
                data=data
            )
            await self._event_bus.emit_async(event)

    def _get_state_class(self) -> Optional[Type[BaseModel]]:
        """Get the state class from type hints"""
        if hasattr(self.__class__, '__orig_bases__'):
            for base in self.__class__.__orig_bases__:
                if hasattr(base, '__args__'):
                    args = base.__args__
                    if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                        return args[0]
        return None

    def visualize(self, format: str = "ascii") -> str:
        """Visualize the flow graph

        Args:
            format: Output format ('ascii', 'dot', or 'mermaid')

        Returns:
            String representation of the flow
        """
        if self._graph is None:
            self._graph = self._build_graph()

        return self._graph.visualize(format)

    def validate(self) -> List[str]:
        """Validate the flow structure

        Returns:
            List of validation errors (empty if valid)
        """
        if self._graph is None:
            self._graph = self._build_graph()

        return self._graph.validate()

    @property
    def state(self) -> Optional[FlowState]:
        """Get current flow state"""
        return self._state

    @property
    def context(self) -> Optional[FlowContext]:
        """Get current flow context"""
        return self._state.context if self._state else None

    @property
    def event_bus(self) -> Optional[EventBus]:
        """Get event bus"""
        return self._event_bus

    @property
    def graph(self) -> Optional[FlowGraph]:
        """Get flow graph"""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    @property
    def execution_history(self) -> List[str]:
        """Get list of executed step names"""
        return self._execution_history.copy()

    def get_metadata(self) -> Dict[str, StepMetadata]:
        """Get all step metadata"""
        if self._metadata is None:
            self._metadata = get_flow_metadata(self.__class__)
        return self._metadata

    def on_event(self, event_type: str, listener: Callable):
        """Register an event listener

        Args:
            event_type: Event type to listen for
            listener: Callback function
        """
        if self._event_bus is None:
            self._event_bus = EventBus()
        self._event_bus.on(event_type, listener)

    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """Get result of a specific step

        Args:
            step_name: Name of the step

        Returns:
            StepResult if step was executed
        """
        if self._state and self._state.context:
            return self._state.context.step_results.get(step_name)
        return None


# Convenience functions

def create_flow(state_class: Type[StateT] = None) -> Type[Flow]:
    """Create a flow class with optional typed state

    Args:
        state_class: Optional Pydantic model for state

    Returns:
        Flow subclass
    """
    class TypedFlow(Flow):
        def __init__(self, **data):
            super().__init__(**data)
            self._state_class = state_class

        def _get_state_class(self) -> Optional[Type[BaseModel]]:
            return self._state_class

    return TypedFlow


async def run_flow(flow: Flow, initial_input: Any = None) -> Any:
    """Run a flow instance

    Args:
        flow: Flow instance to run
        initial_input: Initial input data

    Returns:
        Flow result
    """
    return await flow.run(initial_input)


def run_flow_sync(flow: Flow, initial_input: Any = None) -> Any:
    """Run a flow synchronously

    Args:
        flow: Flow instance to run
        initial_input: Initial input data

    Returns:
        Flow result
    """
    return asyncio.run(flow.run(initial_input))


class FlowBuilder:
    """Builder for programmatically creating flows"""

    def __init__(self, name: str = "flow"):
        self.name = name
        self._steps: Dict[str, Callable] = {}
        self._edges: List[tuple] = []
        self._start_step: Optional[str] = None

    def add_start(self, name: str, handler: Callable) -> 'FlowBuilder':
        """Add start step"""
        self._steps[name] = handler
        self._start_step = name
        return self

    def add_step(self, name: str, handler: Callable, after: str = None) -> 'FlowBuilder':
        """Add a step"""
        self._steps[name] = handler
        if after:
            self._edges.append((after, name))
        return self

    def add_edge(self, source: str, target: str) -> 'FlowBuilder':
        """Add an edge between steps"""
        self._edges.append((source, target))
        return self

    def build(self) -> Flow:
        """Build the flow"""
        if not self._start_step:
            raise ValueError("No start step defined")

        # Create dynamic flow class
        steps = self._steps
        edges = self._edges
        start_step = self._start_step

        class DynamicFlow(Flow):
            def __init__(self):
                super().__init__()
                self._dynamic_steps = steps
                self._dynamic_edges = edges
                self._dynamic_start = start_step

            def _build_graph(self) -> FlowGraph:
                graph = FlowGraph(name=self.__class__.__name__)

                # Add start node
                start_handler = self._dynamic_steps.get(self._dynamic_start)
                graph.add_node(FlowNode(
                    name=self._dynamic_start,
                    type=NodeType.START,
                    handler=start_handler
                ))

                # Add other nodes
                for name, handler in self._dynamic_steps.items():
                    if name != self._dynamic_start:
                        graph.add_node(FlowNode(
                            name=name,
                            type=NodeType.STEP,
                            handler=handler
                        ))

                # Add edges
                for source, target in self._dynamic_edges:
                    if source in graph.nodes and target in graph.nodes:
                        graph.add_edge(source, target)

                return graph

        return DynamicFlow()
