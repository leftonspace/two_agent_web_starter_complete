"""
Sequential Pattern Implementation

Agents speak in a defined order, each agent speaks once per round.
"""

from typing import List, Dict, Optional, Any
from .base import Pattern, Agent, Message, PatternConfig, PatternResult, PatternStatus


class SequentialPattern(Pattern):
    """
    Sequential orchestration pattern.

    Agents speak in a defined order. Each agent speaks once per round.
    The pattern terminates when all agents have spoken or a termination
    condition is met.

    Example:
        agents = [Agent("researcher"), Agent("writer"), Agent("editor")]
        pattern = SequentialPattern(agents)
        result = await pattern.run("Write an article about AI")
        # researcher -> writer -> editor -> done
    """

    def __init__(self, agents: List[Agent], config: Optional[PatternConfig] = None):
        super().__init__(agents, config)
        self._current_index = 0
        self._agents_spoken_this_round: set = set()

    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Select the next agent in sequence.

        Returns None when all agents have spoken in the current round.
        """
        if not self.agents:
            return None

        # Check if all agents have spoken this round
        if len(self._agents_spoken_this_round) >= len(self.agents):
            if self.config.require_all_agents:
                # Start a new round
                self._agents_spoken_this_round.clear()
                self._current_index = 0
            else:
                return None

        # Get next agent that hasn't spoken
        attempts = 0
        while attempts < len(self.agents):
            agent = self.agents[self._current_index]
            self._current_index = (self._current_index + 1) % len(self.agents)

            if agent.name not in self._agents_spoken_this_round:
                self._agents_spoken_this_round.add(agent.name)
                return agent
            attempts += 1

        return None

    def should_terminate(self, last_message: Message) -> bool:
        """
        Check if pattern should terminate.

        Terminates when:
        - A termination keyword is found in the message
        - All agents have spoken (if not requiring multiple rounds)
        """
        # Check for termination keywords
        content_upper = last_message.content.upper()
        for keyword in self.config.termination_keywords:
            if keyword.upper() in content_upper:
                return True

        # Check if all agents have completed (single round mode)
        if not self.config.require_all_agents:
            if len(self._agents_spoken_this_round) >= len(self.agents):
                return True

        return False

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._current_index = 0
        self._agents_spoken_this_round.clear()


class OrderedSequentialPattern(SequentialPattern):
    """
    Sequential pattern with explicit ordering.

    Allows specifying a custom order for agent execution that may
    differ from the order agents were provided.
    """

    def __init__(
        self,
        agents: List[Agent],
        order: Optional[List[str]] = None,
        config: Optional[PatternConfig] = None
    ):
        """
        Initialize with custom order.

        Args:
            agents: List of agents
            order: List of agent names in desired execution order
            config: Pattern configuration
        """
        super().__init__(agents, config)

        if order:
            # Reorder agents based on provided order
            agent_map = {a.name: a for a in agents}
            ordered_agents = []
            for name in order:
                if name in agent_map:
                    ordered_agents.append(agent_map[name])
            # Add any agents not in order at the end
            for agent in agents:
                if agent not in ordered_agents:
                    ordered_agents.append(agent)
            self.agents = ordered_agents
            self._agent_map = {a.name: a for a in self.agents}


class PipelinePattern(SequentialPattern):
    """
    Pipeline pattern where output of one agent feeds into the next.

    Similar to Sequential but explicitly designed for data transformation
    pipelines where each agent processes and passes data to the next.
    """

    def __init__(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None,
        transform_output: bool = True
    ):
        """
        Initialize pipeline pattern.

        Args:
            agents: List of agents in pipeline order
            config: Pattern configuration
            transform_output: Whether to pass transformed output between agents
        """
        # Pipeline typically runs once through all agents
        if config is None:
            config = PatternConfig(require_all_agents=False)
        super().__init__(agents, config)
        self.transform_output = transform_output
        self._pipeline_data: Dict[str, Any] = {}

    def get_pipeline_data(self) -> Dict[str, Any]:
        """Get data collected through the pipeline"""
        return self._pipeline_data

    def add_message(self, message: Message):
        """Track pipeline data along with message"""
        super().add_message(message)

        # Store output keyed by agent name
        if message.sender != "user":
            self._pipeline_data[message.sender] = message.content

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._pipeline_data.clear()
