"""
Hierarchical Pattern Implementation

Manager delegates to supervisors who delegate to workers.
Supports multi-level hierarchies with delegation and reporting.
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from .base import Pattern, Agent, Message, PatternConfig, PatternResult, PatternStatus, MessageRole


class HierarchyLevel(Enum):
    """Agent hierarchy levels"""
    EXECUTIVE = "executive"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    WORKER = "worker"


@dataclass
class HierarchicalAgent(Agent):
    """Agent with hierarchy information"""
    level: HierarchyLevel = HierarchyLevel.WORKER
    reports_to: Optional[str] = None
    subordinates: List[str] = field(default_factory=list)

    @classmethod
    def from_agent(
        cls,
        agent: Agent,
        level: HierarchyLevel = HierarchyLevel.WORKER,
        reports_to: Optional[str] = None,
        subordinates: Optional[List[str]] = None
    ) -> "HierarchicalAgent":
        """Create HierarchicalAgent from regular Agent"""
        return cls(
            name=agent.name,
            role=agent.role,
            description=agent.description,
            capabilities=agent.capabilities,
            priority=agent.priority,
            metadata=agent.metadata,
            level=level,
            reports_to=reports_to,
            subordinates=subordinates or []
        )


class HierarchicalPattern(Pattern):
    """
    Hierarchical orchestration pattern.

    Implements a manager-supervisor-worker hierarchy where:
    - Managers delegate tasks to supervisors
    - Supervisors delegate to workers
    - Workers report back up the chain

    Example:
        manager = HierarchicalAgent("manager", level=HierarchyLevel.MANAGER)
        supervisor = HierarchicalAgent("supervisor", level=HierarchyLevel.SUPERVISOR, reports_to="manager")
        worker1 = HierarchicalAgent("worker1", level=HierarchyLevel.WORKER, reports_to="supervisor")

        pattern = HierarchicalPattern([manager, supervisor, worker1])
        result = await pattern.run("Complete project X")
    """

    def __init__(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None,
        hierarchy: Optional[Dict[str, Dict]] = None
    ):
        """
        Initialize hierarchical pattern.

        Args:
            agents: List of agents (can be HierarchicalAgent or regular Agent)
            config: Pattern configuration
            hierarchy: Optional hierarchy definition mapping agent names to
                      {level: str, reports_to: str, subordinates: [str]}
        """
        super().__init__(agents, config)

        # Convert agents to hierarchical agents if needed
        self._hierarchy: Dict[str, HierarchicalAgent] = {}
        self._build_hierarchy(agents, hierarchy)

        # Validate hierarchy for circular dependencies
        self._validate_hierarchy()

        # Track delegation state
        self._delegation_stack: List[str] = []
        self._pending_reports: Dict[str, List[str]] = {}
        self._phase: str = "delegation"  # delegation, execution, reporting

    def _build_hierarchy(
        self,
        agents: List[Agent],
        hierarchy: Optional[Dict[str, Dict]] = None
    ):
        """Build the hierarchy structure"""
        hierarchy = hierarchy or {}

        for agent in agents:
            if isinstance(agent, HierarchicalAgent):
                self._hierarchy[agent.name] = agent
            else:
                # Get hierarchy info or infer from position
                info = hierarchy.get(agent.name, {})
                level = HierarchyLevel(info.get("level", "worker"))
                reports_to = info.get("reports_to")
                subordinates = info.get("subordinates", [])

                self._hierarchy[agent.name] = HierarchicalAgent.from_agent(
                    agent,
                    level=level,
                    reports_to=reports_to,
                    subordinates=subordinates
                )

        # If no explicit hierarchy, infer from agent order
        if not hierarchy and len(agents) > 0:
            self._infer_hierarchy()

    def _infer_hierarchy(self):
        """Infer hierarchy from agent order (first is manager, etc.)"""
        agents_list = list(self._hierarchy.values())
        if len(agents_list) == 0:
            return

        # First agent is manager
        if len(agents_list) >= 1:
            agents_list[0].level = HierarchyLevel.MANAGER
            agents_list[0].subordinates = [a.name for a in agents_list[1:]]

        # Middle agents are supervisors (if > 2 agents)
        if len(agents_list) > 2:
            for agent in agents_list[1:-1]:
                agent.level = HierarchyLevel.SUPERVISOR
                agent.reports_to = agents_list[0].name
                agent.subordinates = [agents_list[-1].name]

        # Last agent is worker (if > 1 agent)
        if len(agents_list) >= 2:
            agents_list[-1].level = HierarchyLevel.WORKER
            if len(agents_list) > 2:
                agents_list[-1].reports_to = agents_list[-2].name
            else:
                agents_list[-1].reports_to = agents_list[0].name

    def _validate_hierarchy(self):
        """
        Validate hierarchy structure for circular dependencies.

        Raises:
            ValueError: If circular dependency is detected
        """
        def detect_cycle_from_reports_to(agent_name: str, visited: Set[str], path: Set[str]) -> None:
            """Check for cycles following reports_to chain"""
            if agent_name in path:
                raise ValueError(
                    f"Circular dependency detected in reports_to chain at '{agent_name}'"
                )
            if agent_name in visited:
                return

            visited.add(agent_name)
            path.add(agent_name)

            agent = self._hierarchy.get(agent_name)
            if agent and agent.reports_to:
                detect_cycle_from_reports_to(agent.reports_to, visited, path)

            path.remove(agent_name)

        def detect_cycle_from_subordinates(agent_name: str, visited: Set[str], path: Set[str]) -> None:
            """Check for cycles following subordinates chain"""
            if agent_name in path:
                raise ValueError(
                    f"Circular dependency detected in subordinates chain at '{agent_name}'"
                )
            if agent_name in visited:
                return

            visited.add(agent_name)
            path.add(agent_name)

            agent = self._hierarchy.get(agent_name)
            if agent:
                for sub_name in agent.subordinates:
                    if sub_name in self._hierarchy:
                        detect_cycle_from_subordinates(sub_name, visited, path)

            path.remove(agent_name)

        # Check all agents for cycles
        visited_reports = set()
        visited_subs = set()

        for agent_name in self._hierarchy:
            detect_cycle_from_reports_to(agent_name, visited_reports, set())
            detect_cycle_from_subordinates(agent_name, visited_subs, set())

    def _get_top_level_agents(self) -> List[HierarchicalAgent]:
        """Get agents at the top of the hierarchy"""
        return [
            a for a in self._hierarchy.values()
            if a.reports_to is None or a.level == HierarchyLevel.MANAGER
        ]

    def _get_subordinates(self, agent_name: str) -> List[HierarchicalAgent]:
        """Get direct subordinates of an agent"""
        agent = self._hierarchy.get(agent_name)
        if not agent:
            return []

        return [
            self._hierarchy[name]
            for name in agent.subordinates
            if name in self._hierarchy
        ]

    def _get_manager(self, agent_name: str) -> Optional[HierarchicalAgent]:
        """Get the manager of an agent"""
        agent = self._hierarchy.get(agent_name)
        if not agent or not agent.reports_to:
            return None
        return self._hierarchy.get(agent.reports_to)

    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Select next agent based on hierarchy and current phase.

        Delegation phase: Top-down (manager -> supervisor -> worker)
        Execution phase: Workers execute tasks
        Reporting phase: Bottom-up (worker -> supervisor -> manager)
        """
        if not self._hierarchy:
            return None

        last_message = context.get("last_message")
        last_agent_name = context.get("last_agent_name")

        # First message - start with top-level manager
        if not last_agent_name or last_agent_name == "user":
            top_agents = self._get_top_level_agents()
            if top_agents:
                agent = top_agents[0]
                self._delegation_stack.append(agent.name)
                return agent
            return None

        current_agent = self._hierarchy.get(last_agent_name)
        if not current_agent:
            return None

        # Check for delegation keywords
        if last_message and self._is_delegation(last_message.content):
            # Delegate to subordinates
            subordinates = self._get_subordinates(current_agent.name)
            if subordinates:
                next_agent = subordinates[0]
                self._delegation_stack.append(next_agent.name)
                return next_agent

        # Check for report keywords
        if last_message and self._is_report(last_message.content):
            # Report back to manager
            manager = self._get_manager(current_agent.name)
            if manager:
                if self._delegation_stack and self._delegation_stack[-1] == current_agent.name:
                    self._delegation_stack.pop()
                return manager

        # If worker, report back
        if current_agent.level == HierarchyLevel.WORKER:
            manager = self._get_manager(current_agent.name)
            if manager:
                return manager

        # If no subordinates left to delegate to, report back
        manager = self._get_manager(current_agent.name)
        if manager:
            return manager

        return None

    def _is_delegation(self, content: str) -> bool:
        """Check if message contains delegation keywords"""
        delegation_keywords = [
            "delegate", "assign", "task", "handle",
            "please", "need you to", "your job"
        ]
        content_lower = content.lower()
        return any(kw in content_lower for kw in delegation_keywords)

    def _is_report(self, content: str) -> bool:
        """Check if message contains report keywords"""
        report_keywords = [
            "report", "completed", "finished", "done",
            "results", "findings", "status"
        ]
        content_lower = content.lower()
        return any(kw in content_lower for kw in report_keywords)

    def should_terminate(self, last_message: Message) -> bool:
        """
        Check if pattern should terminate.

        Terminates when:
        - Top-level manager provides final report
        - Termination keywords found
        - Delegation stack is empty and last speaker is manager
        """
        # Check termination keywords
        content_upper = last_message.content.upper()
        for keyword in self.config.termination_keywords:
            if keyword.upper() in content_upper:
                return True

        # Check if back at top level with report
        agent = self._hierarchy.get(last_message.sender)
        if agent and agent.level == HierarchyLevel.MANAGER:
            if self._is_report(last_message.content):
                return True
            # Also terminate if delegation stack is empty
            if not self._delegation_stack:
                return True

        return False

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._delegation_stack.clear()
        self._pending_reports.clear()
        self._phase = "delegation"

    def get_hierarchy_visualization(self) -> str:
        """Get a text visualization of the hierarchy"""
        lines = ["Hierarchy Structure:"]

        def add_agent(agent: HierarchicalAgent, indent: int = 0):
            prefix = "  " * indent
            lines.append(f"{prefix}- {agent.name} ({agent.level.value})")
            for sub_name in agent.subordinates:
                if sub_name in self._hierarchy:
                    add_agent(self._hierarchy[sub_name], indent + 1)

        for top_agent in self._get_top_level_agents():
            add_agent(top_agent)

        return "\n".join(lines)
