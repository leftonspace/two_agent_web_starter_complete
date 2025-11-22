"""
Flow Engine Package

A flow execution engine for JARVIS with support for conditional routing,
parallel execution, and dynamic workflows.

Usage:
    from agent.flow import Flow, start, listen, router

    class MyFlow(Flow):
        @start()
        def begin(self):
            return "Hello"

        @listen("begin")
        def process(self, data):
            return data.upper()

    # Run the flow
    flow = MyFlow()
    result = await flow.run()
"""

from .state import (
    FlowState,
    FlowContext,
    FlowStatus,
    StepStatus,
    StepResult,
)

from .events import (
    EventBus,
    FlowEvent,
    EventType,
    EventMatcher,
    EventAggregator,
    or_ as event_or,
    and_ as event_and,
    not_ as event_not,
    step_started,
    step_completed,
    step_failed,
    flow_started,
    flow_completed,
    flow_failed,
)

from .graph import (
    FlowGraph,
    FlowNode,
    FlowEdge,
    NodeType,
)

from .decorators import (
    start,
    listen,
    router,
    step,
    parallel,
    or_,
    and_,
    OrCombinator,
    AndCombinator,
    StepMetadata,
    get_flow_metadata,
    retry,
    timeout,
    validate_input,
    validate_output,
    log_step,
    conditional,
)

from .engine import (
    Flow,
    FlowExecutionError,
    FlowBuilder,
    create_flow,
    run_flow,
    run_flow_sync,
)

__all__ = [
    # State management
    'FlowState',
    'FlowContext',
    'FlowStatus',
    'StepStatus',
    'StepResult',

    # Events
    'EventBus',
    'FlowEvent',
    'EventType',
    'EventMatcher',
    'EventAggregator',
    'event_or',
    'event_and',
    'event_not',
    'step_started',
    'step_completed',
    'step_failed',
    'flow_started',
    'flow_completed',
    'flow_failed',

    # Graph
    'FlowGraph',
    'FlowNode',
    'FlowEdge',
    'NodeType',

    # Decorators
    'start',
    'listen',
    'router',
    'step',
    'parallel',
    'or_',
    'and_',
    'OrCombinator',
    'AndCombinator',
    'StepMetadata',
    'get_flow_metadata',
    'retry',
    'timeout',
    'validate_input',
    'validate_output',
    'log_step',
    'conditional',

    # Engine
    'Flow',
    'FlowExecutionError',
    'FlowBuilder',
    'create_flow',
    'run_flow',
    'run_flow_sync',
]
