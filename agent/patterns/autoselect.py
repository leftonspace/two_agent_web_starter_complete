"""
AutoSelect Pattern Implementation

LLM-based agent selection that considers conversation context
to dynamically choose the most appropriate agent.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
import re

from .base import Pattern, Agent, Message, PatternConfig, PatternResult, PatternStatus

logger = logging.getLogger(__name__)


@dataclass
class SelectionCriteria:
    """Criteria for agent selection"""
    keywords: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    preferred_roles: List[str] = field(default_factory=list)
    context_patterns: List[str] = field(default_factory=list)
    min_relevance_score: float = 0.3


class AgentSelector(ABC):
    """Abstract base class for agent selection strategies"""

    @abstractmethod
    async def select(
        self,
        agents: List[Agent],
        context: Dict[str, Any],
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Agent]:
        """Select the most appropriate agent"""
        pass


class KeywordSelector(AgentSelector):
    """Select agents based on keyword matching"""

    async def select(
        self,
        agents: List[Agent],
        context: Dict[str, Any],
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Agent]:
        """Select agent with highest keyword match score"""
        if not agents:
            return None

        last_message = context.get("last_message")
        if not last_message:
            return agents[0]

        content = last_message.content.lower()
        criteria = criteria or SelectionCriteria()

        scores = []
        for agent in agents:
            score = self._calculate_score(agent, content, criteria)
            scores.append((agent, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        if scores and scores[0][1] >= criteria.min_relevance_score:
            return scores[0][0]

        # Fall back to first agent if no good match
        return agents[0]

    def _calculate_score(
        self,
        agent: Agent,
        content: str,
        criteria: SelectionCriteria
    ) -> float:
        """Calculate relevance score for an agent"""
        score = 0.0
        total_weight = 0.0

        # Check agent capabilities
        if agent.capabilities:
            weight = 0.4
            matches = sum(1 for cap in agent.capabilities if cap.lower() in content)
            if matches > 0:
                score += weight * (matches / len(agent.capabilities))
            total_weight += weight

        # Check role relevance
        if agent.role:
            weight = 0.3
            if agent.role.lower() in content:
                score += weight
            total_weight += weight

        # Check description relevance
        if agent.description:
            weight = 0.2
            desc_words = agent.description.lower().split()
            matches = sum(1 for word in desc_words if word in content)
            if matches > 0:
                score += weight * min(1.0, matches / 5)
            total_weight += weight

        # Check criteria keywords
        if criteria.keywords:
            weight = 0.1
            agent_text = f"{agent.role} {agent.description} {' '.join(agent.capabilities)}".lower()
            matches = sum(1 for kw in criteria.keywords if kw.lower() in agent_text)
            if matches > 0:
                score += weight * (matches / len(criteria.keywords))
            total_weight += weight

        return score


class LLMSelector(AgentSelector):
    """Select agents using LLM reasoning"""

    def __init__(
        self,
        llm_callback: Optional[Callable[[str], Awaitable[str]]] = None
    ):
        """
        Initialize LLM selector.

        Args:
            llm_callback: Async function that takes a prompt and returns LLM response
        """
        self.llm_callback = llm_callback

    async def select(
        self,
        agents: List[Agent],
        context: Dict[str, Any],
        criteria: Optional[SelectionCriteria] = None
    ) -> Optional[Agent]:
        """Use LLM to select the most appropriate agent"""
        if not agents:
            return None

        if not self.llm_callback:
            # Fall back to keyword selection if no LLM
            keyword_selector = KeywordSelector()
            return await keyword_selector.select(agents, context, criteria)

        # Build selection prompt
        prompt = self._build_selection_prompt(agents, context, criteria)

        try:
            response = await self.llm_callback(prompt)
            selected_name = self._parse_selection(response, agents)

            if selected_name:
                for agent in agents:
                    if agent.name.lower() == selected_name.lower():
                        return agent

        except Exception as e:
            # Log the error instead of silently swallowing it
            logger.warning(f"LLM selection failed, falling back to keyword selection: {e}")

        # Fall back to keyword selection
        keyword_selector = KeywordSelector()
        return await keyword_selector.select(agents, context, criteria)

    def _build_selection_prompt(
        self,
        agents: List[Agent],
        context: Dict[str, Any],
        criteria: Optional[SelectionCriteria] = None
    ) -> str:
        """Build the LLM prompt for agent selection"""
        agent_descriptions = []
        for agent in agents:
            desc = f"- {agent.name}: {agent.role}"
            if agent.description:
                desc += f" - {agent.description}"
            if agent.capabilities:
                desc += f" (capabilities: {', '.join(agent.capabilities)})"
            agent_descriptions.append(desc)

        history_text = ""
        history = context.get("history", [])
        if history:
            recent = history[-5:]  # Last 5 messages
            history_lines = [f"{m.sender}: {m.content[:100]}..." for m in recent]
            history_text = "\n".join(history_lines)

        last_message = context.get("last_message")
        last_content = last_message.content if last_message else "No message"

        prompt = f"""Select the most appropriate agent to respond next.

Available agents:
{chr(10).join(agent_descriptions)}

Recent conversation:
{history_text}

Last message: {last_content}

Which agent should respond next? Reply with just the agent name."""

        return prompt

    def _parse_selection(self, response: str, agents: List[Agent]) -> Optional[str]:
        """Parse the LLM response to extract agent name"""
        response_lower = response.lower().strip()

        # Try exact match first
        for agent in agents:
            if agent.name.lower() in response_lower:
                return agent.name

        # Try to find agent name pattern
        for agent in agents:
            pattern = rf'\b{re.escape(agent.name)}\b'
            if re.search(pattern, response, re.IGNORECASE):
                return agent.name

        return None


class AutoSelectPattern(Pattern):
    """
    Auto-select orchestration pattern.

    Uses intelligent selection (keyword matching or LLM) to dynamically
    choose the most appropriate agent based on conversation context.

    Example:
        pattern = AutoSelectPattern(
            agents=[researcher, writer, editor],
            selector=LLMSelector(llm_callback=my_llm_function)
        )
        result = await pattern.run("Write a technical article about AI")
    """

    def __init__(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None,
        selector: Optional[AgentSelector] = None,
        criteria: Optional[SelectionCriteria] = None,
        avoid_repeat: bool = True,
        max_same_agent: int = 2
    ):
        """
        Initialize auto-select pattern.

        Args:
            agents: List of agents to select from
            config: Pattern configuration
            selector: Agent selection strategy (default: KeywordSelector)
            criteria: Selection criteria
            avoid_repeat: Whether to avoid selecting same agent consecutively
            max_same_agent: Maximum consecutive selections of same agent
        """
        super().__init__(agents, config)
        self.selector = selector or KeywordSelector()
        self.criteria = criteria or SelectionCriteria()
        self.avoid_repeat = avoid_repeat
        self.max_same_agent = max_same_agent

        self._selection_history: List[str] = []
        self._agent_scores: Dict[str, float] = {}

    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Select the next agent using keyword-based scoring.

        This synchronous method provides consistent selection with the async
        version by using the same KeywordSelector logic. The async version
        may additionally use LLM-based selection if configured.
        """
        if not self.agents:
            return None

        last_message = context.get("last_message")
        if not last_message:
            return self.agents[0]

        # Filter out agents that have been selected too many times
        available_agents = self._get_available_agents()
        if not available_agents:
            # Reset if all agents exhausted (consistent with async behavior)
            self._selection_history.clear()
            available_agents = self.agents

        # Use KeywordSelector for consistent sync behavior
        # This matches what LLMSelector falls back to
        content = last_message.content.lower()
        best_agent = None
        best_score = -1.0

        for agent in available_agents:
            score = self._calculate_keyword_score(agent, content)
            if score > best_score:
                best_score = score
                best_agent = agent

        selected = best_agent or available_agents[0]
        self._selection_history.append(selected.name)
        return selected

    def _calculate_keyword_score(self, agent: Agent, content: str) -> float:
        """Calculate keyword-based relevance score for consistent sync/async behavior."""
        score = 0.0

        # Check agent capabilities (weight: 0.4)
        if agent.capabilities:
            matches = sum(1 for cap in agent.capabilities if cap.lower() in content)
            if matches > 0:
                score += 0.4 * (matches / len(agent.capabilities))

        # Check role relevance (weight: 0.3)
        if agent.role and agent.role.lower() in content:
            score += 0.3

        # Check description relevance (weight: 0.2)
        if agent.description:
            desc_words = agent.description.lower().split()
            matches = sum(1 for word in desc_words if word in content)
            if matches > 0:
                score += 0.2 * min(1.0, matches / 5)

        # Check criteria keywords (weight: 0.1)
        if self.criteria.keywords:
            agent_text = f"{agent.role} {agent.description} {' '.join(agent.capabilities)}".lower()
            matches = sum(1 for kw in self.criteria.keywords if kw.lower() in agent_text)
            if matches > 0:
                score += 0.1 * (matches / len(self.criteria.keywords))

        return score

    async def _select_next_agent_async(self, context: Dict[str, Any]) -> Optional[Agent]:
        """Async version of agent selection"""
        if not self.agents:
            return None

        available_agents = self._get_available_agents()
        if not available_agents:
            # Reset if all agents exhausted
            self._selection_history.clear()
            available_agents = self.agents

        selected = await self.selector.select(available_agents, context, self.criteria)

        if selected:
            self._selection_history.append(selected.name)

        return selected

    def _get_available_agents(self) -> List[Agent]:
        """Get agents that can be selected based on history"""
        if not self.avoid_repeat:
            return self.agents

        available = []
        for agent in self.agents:
            # Count recent consecutive selections
            consecutive = 0
            for name in reversed(self._selection_history):
                if name == agent.name:
                    consecutive += 1
                else:
                    break

            if consecutive < self.max_same_agent:
                available.append(agent)

        return available

    def should_terminate(self, last_message: Message) -> bool:
        """Check if pattern should terminate"""
        # Check termination keywords
        content_upper = last_message.content.upper()
        for keyword in self.config.termination_keywords:
            if keyword.upper() in content_upper:
                return True

        return False

    async def run(self, initial_message: str) -> PatternResult:
        """Execute the pattern with async agent selection"""
        from datetime import datetime
        import asyncio

        start_time = datetime.now()
        self.status = PatternStatus.RUNNING
        agents_used = set()

        try:
            # Add initial message
            user_message = Message(
                content=initial_message,
                sender="user",
                role=self._get_message_role("USER")
            )
            self.add_message(user_message)

            # Execute rounds
            while self.current_round < self.config.max_rounds:
                self.current_round += 1
                context = self.get_context()

                # Use async selection
                next_agent = await self._select_next_agent_async(context)

                if next_agent is None:
                    break

                # Trigger callbacks
                for callback in self._on_agent_selected:
                    callback(next_agent)

                # Execute agent
                agents_used.add(next_agent.name)
                last_content = self.history[-1].content if self.history else initial_message

                try:
                    response = await asyncio.wait_for(
                        next_agent.execute(last_content, context),
                        timeout=self.config.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    self.status = PatternStatus.TIMEOUT
                    return PatternResult(
                        status=PatternStatus.TIMEOUT,
                        messages=self.history,
                        rounds_completed=self.current_round,
                        agents_used=list(agents_used),
                        duration_seconds=(datetime.now() - start_time).total_seconds(),
                        error=f"Timeout waiting for {next_agent.name}"
                    )

                # Add response
                agent_message = Message(
                    content=response,
                    sender=next_agent.name,
                    role=self._get_message_role("AGENT")
                )
                self.add_message(agent_message)

                # Check termination
                if self.should_terminate(agent_message):
                    break

                # Trigger round complete
                for callback in self._on_round_complete:
                    callback(self.current_round)

            self.status = PatternStatus.COMPLETED
            return PatternResult(
                status=PatternStatus.COMPLETED,
                messages=self.history,
                final_output=self.history[-1].content if self.history else None,
                rounds_completed=self.current_round,
                agents_used=list(agents_used),
                duration_seconds=(datetime.now() - start_time).total_seconds()
            )

        except Exception as e:
            self.status = PatternStatus.FAILED
            return PatternResult(
                status=PatternStatus.FAILED,
                messages=self.history,
                rounds_completed=self.current_round,
                agents_used=list(agents_used),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )

    def _get_message_role(self, role_name: str):
        """Get MessageRole enum value"""
        from .base import MessageRole
        return getattr(MessageRole, role_name)

    def reset(self):
        """Reset pattern state"""
        super().reset()
        self._selection_history.clear()
        self._agent_scores.clear()

    def get_selection_stats(self) -> Dict[str, Any]:
        """Get statistics about agent selections"""
        from collections import Counter
        counts = Counter(self._selection_history)
        return {
            "total_selections": len(self._selection_history),
            "selection_counts": dict(counts),
            "most_selected": counts.most_common(1)[0] if counts else None
        }
