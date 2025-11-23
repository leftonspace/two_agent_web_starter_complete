"""
RoundRobin and Manual Pattern Implementations

RoundRobin: Fixed rotation through agents
Manual: User selects next agent
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
import logging

from .base import Pattern, Agent, Message, PatternConfig, PatternResult, PatternStatus, MessageRole

logger = logging.getLogger(__name__)


class RoundRobinPattern(Pattern):
    """
    Round-robin orchestration pattern.

    Agents speak in a fixed rotation, cycling through all agents
    repeatedly until termination.

    Example:
        agents = [Agent("agent1"), Agent("agent2"), Agent("agent3")]
        pattern = RoundRobinPattern(agents)
        result = await pattern.run("Discuss topic X")
        # agent1 -> agent2 -> agent3 -> agent1 -> agent2 -> ...
    """

    def __init__(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None,
        skip_on_empty: bool = False,
        reverse: bool = False
    ):
        """
        Initialize round-robin pattern.

        Args:
            agents: List of agents to rotate through
            config: Pattern configuration
            skip_on_empty: Whether to skip agents that return empty responses
            reverse: Whether to rotate in reverse order
        """
        super().__init__(agents, config)
        self.skip_on_empty = skip_on_empty
        self.reverse = reverse

        self._current_index = 0
        self._direction = -1 if reverse else 1
        self._rounds_per_agent: Dict[str, int] = {a.name: 0 for a in agents}

    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Select the next agent in rotation.

        Returns the next agent in the cycle.
        """
        if not self.agents:
            return None

        agent = self.agents[self._current_index]

        # Move to next position for next call
        self._current_index = (self._current_index + self._direction) % len(self.agents)

        # Track rounds per agent
        self._rounds_per_agent[agent.name] = self._rounds_per_agent.get(agent.name, 0) + 1

        return agent

    def should_terminate(self, last_message: Message) -> bool:
        """
        Check if pattern should terminate.

        Terminates when:
        - Termination keywords found
        - Max rounds reached (handled by base class)
        """
        content_upper = last_message.content.upper()
        for keyword in self.config.termination_keywords:
            if keyword.upper() in content_upper:
                return True

        return False

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._current_index = 0
        self._rounds_per_agent = {a.name: 0 for a in self.agents}

    def get_rotation_stats(self) -> Dict[str, Any]:
        """Get rotation statistics"""
        return {
            "current_index": self._current_index,
            "direction": "reverse" if self.reverse else "forward",
            "rounds_per_agent": self._rounds_per_agent.copy(),
            "total_rotations": sum(self._rounds_per_agent.values())
        }


class WeightedRoundRobinPattern(RoundRobinPattern):
    """
    Weighted round-robin pattern.

    Agents are selected based on weights, with higher-weighted agents
    being selected more frequently.
    """

    def __init__(
        self,
        agents: List[Agent],
        weights: Optional[Dict[str, int]] = None,
        config: Optional[PatternConfig] = None
    ):
        """
        Initialize weighted round-robin pattern.

        Args:
            agents: List of agents
            weights: Dict mapping agent names to weights (default: all equal)
            config: Pattern configuration
        """
        super().__init__(agents, config)
        self.weights = weights or {a.name: 1 for a in agents}

        # Build weighted rotation list
        self._rotation_list = self._build_rotation_list()
        self._rotation_index = 0

    def _build_rotation_list(self) -> List[Agent]:
        """Build the weighted rotation list"""
        rotation = []
        for agent in self.agents:
            weight = self.weights.get(agent.name, 1)
            rotation.extend([agent] * weight)
        return rotation

    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """Select next agent from weighted rotation"""
        if not self._rotation_list:
            return None

        agent = self._rotation_list[self._rotation_index]
        self._rotation_index = (self._rotation_index + 1) % len(self._rotation_list)

        self._rounds_per_agent[agent.name] = self._rounds_per_agent.get(agent.name, 0) + 1

        return agent

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._rotation_index = 0


class ManualPattern(Pattern):
    """
    Manual orchestration pattern.

    The user (or external system) explicitly selects which agent
    speaks next. The pattern prompts for selection after each turn.

    Example:
        pattern = ManualPattern(agents)
        pattern.set_next_agent("researcher")
        result = await pattern.run("Start discussion")
    """

    def __init__(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None,
        selection_callback: Optional[Callable[[List[Agent], Dict], Optional[str]]] = None,
        default_agent: Optional[str] = None
    ):
        """
        Initialize manual pattern.

        Args:
            agents: List of available agents
            config: Pattern configuration
            selection_callback: Optional callback to request agent selection
                               Takes (agents, context) and returns agent name or None
            default_agent: Default agent to use if no selection made
        """
        super().__init__(agents, config)
        self.selection_callback = selection_callback
        self.default_agent = default_agent

        self._next_agent_name: Optional[str] = None
        self._selection_pending = False
        self._selection_history: List[Dict[str, Any]] = []

    def set_next_agent(self, agent_name: str) -> bool:
        """
        Set the next agent to speak.

        Args:
            agent_name: Name of the agent to speak next

        Returns:
            True if agent exists and was set, False otherwise
        """
        if agent_name in self._agent_map:
            self._next_agent_name = agent_name
            self._selection_pending = False
            return True
        return False

    def get_available_agents(self) -> List[str]:
        """Get list of available agent names"""
        return self.agent_names

    def is_selection_pending(self) -> bool:
        """Check if a selection is needed"""
        return self._selection_pending

    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Select the next agent based on manual selection.

        If no selection has been made:
        - Calls selection_callback if provided
        - Uses default_agent if set
        - Falls back to first agent with warning (prevents indefinite halt)
        """
        # If explicit selection was made
        if self._next_agent_name:
            agent = self._agent_map.get(self._next_agent_name)
            self._record_selection(self._next_agent_name, "explicit")
            self._next_agent_name = None
            return agent

        # Try callback
        if self.selection_callback:
            selected = self.selection_callback(self.agents, context)
            if selected and selected in self._agent_map:
                self._record_selection(selected, "callback")
                return self._agent_map[selected]

        # Use default
        if self.default_agent and self.default_agent in self._agent_map:
            self._record_selection(self.default_agent, "default")
            return self._agent_map[self.default_agent]

        # Mark as pending but fall back to first agent to prevent indefinite halt
        self._selection_pending = True
        if self.agents:
            logger.warning(
                f"ManualPattern: No agent selected, falling back to first agent '{self.agents[0].name}'. "
                "Set default_agent or provide selection_callback to avoid this."
            )
            self._record_selection(self.agents[0].name, "fallback")
            return self.agents[0]

        return None

    def _record_selection(self, agent_name: str, method: str):
        """Record a selection in history"""
        self._selection_history.append({
            "agent": agent_name,
            "method": method,
            "round": self.current_round
        })

    def should_terminate(self, last_message: Message) -> bool:
        """Check if pattern should terminate"""
        content_upper = last_message.content.upper()
        for keyword in self.config.termination_keywords:
            if keyword.upper() in content_upper:
                return True

        return False

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._next_agent_name = None
        self._selection_pending = False
        self._selection_history.clear()

    def get_selection_history(self) -> List[Dict[str, Any]]:
        """Get the history of agent selections"""
        return self._selection_history.copy()


class InteractivePattern(ManualPattern):
    """
    Interactive pattern with user prompts.

    Extends ManualPattern with built-in prompting for agent selection.
    Useful for CLI or interactive applications.
    """

    def __init__(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None,
        prompt_message: str = "Select next agent",
        show_descriptions: bool = True
    ):
        """
        Initialize interactive pattern.

        Args:
            agents: List of available agents
            config: Pattern configuration
            prompt_message: Message to show when prompting for selection
            show_descriptions: Whether to show agent descriptions in prompt
        """
        super().__init__(agents, config)
        self.prompt_message = prompt_message
        self.show_descriptions = show_descriptions

    def get_selection_prompt(self) -> str:
        """Generate the selection prompt text"""
        lines = [self.prompt_message, ""]

        for i, agent in enumerate(self.agents, 1):
            line = f"  {i}. {agent.name}"
            if self.show_descriptions and agent.description:
                line += f" - {agent.description}"
            lines.append(line)

        lines.append("")
        lines.append("Enter agent name or number: ")

        return "\n".join(lines)

    def parse_selection(self, input_text: str) -> Optional[str]:
        """
        Parse user input to get agent name.

        Accepts:
        - Agent name (case-insensitive)
        - Agent number (1-indexed)
        """
        input_text = input_text.strip()

        # Try as number
        try:
            index = int(input_text) - 1
            if 0 <= index < len(self.agents):
                return self.agents[index].name
        except ValueError:
            pass

        # Try as name
        for agent in self.agents:
            if agent.name.lower() == input_text.lower():
                return agent.name

        return None
