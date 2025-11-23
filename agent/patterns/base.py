"""
Orchestration Pattern Base Classes

Base classes and data models for multi-agent coordination patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class PatternStatus(Enum):
    """Status of pattern execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"
    TIMEOUT = "timeout"


class MessageRole(Enum):
    """Role of message sender"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class Agent:
    """Represents an agent in the pattern"""
    name: str
    role: str = ""
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = more important
    metadata: Dict[str, Any] = field(default_factory=dict)

    async def execute(self, message: str, context: Dict[str, Any] = None) -> str:
        """Execute agent task - override in subclass"""
        return f"[{self.name}] Response to: {message}"

    def matches_task(self, task_keywords: List[str]) -> float:
        """Calculate relevance score for task keywords"""
        if not task_keywords:
            return 0.0

        text = f"{self.role} {self.description} {' '.join(self.capabilities)}".lower()
        matches = sum(1 for kw in task_keywords if kw.lower() in text)
        return matches / len(task_keywords)


@dataclass
class Message:
    """A message in the conversation"""
    content: str
    sender: str
    role: MessageRole  # Required - no default to ensure explicit role assignment
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "sender": self.sender,
            "role": self.role.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class PatternConfig:
    """Configuration for pattern execution"""
    max_rounds: int = 10
    timeout_seconds: int = 300
    allow_parallel: bool = False
    require_all_agents: bool = True
    termination_keywords: List[str] = field(default_factory=lambda: ["DONE", "COMPLETE", "FINISHED"])
    max_consecutive_same_agent: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternResult:
    """Result of pattern execution"""
    status: PatternStatus
    messages: List[Message]
    final_output: Optional[str] = None
    rounds_completed: int = 0
    agents_used: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "messages": [m.to_dict() for m in self.messages],
            "final_output": self.final_output,
            "rounds_completed": self.rounds_completed,
            "agents_used": self.agents_used,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
            "metadata": self.metadata
        }


class Pattern(ABC):
    """
    Abstract base class for orchestration patterns.

    Patterns determine how multiple agents coordinate to complete a task.
    """

    def __init__(self, agents: List[Agent], config: Optional[PatternConfig] = None):
        """
        Initialize pattern.

        Args:
            agents: List of agents to coordinate
            config: Pattern configuration
        """
        self.agents = agents
        self.config = config or PatternConfig()
        self.current_round = 0
        self.history: List[Message] = []
        self.status = PatternStatus.PENDING
        self._agent_map = {a.name: a for a in agents}
        self._consecutive_same_agent = 0
        self._last_agent_name: Optional[str] = None

        # Callbacks
        self._on_message: List[Callable[[Message], None]] = []
        self._on_round_complete: List[Callable[[int], None]] = []
        self._on_agent_selected: List[Callable[[Agent], None]] = []

    @property
    def agent_names(self) -> List[str]:
        """Get list of agent names"""
        return [a.name for a in self.agents]

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self._agent_map.get(name)

    @abstractmethod
    def select_next_agent(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Determine which agent speaks next.

        Args:
            context: Current conversation context

        Returns:
            Next agent to speak, or None if pattern complete
        """
        pass

    @abstractmethod
    def should_terminate(self, last_message: Message) -> bool:
        """
        Check if conversation should end.

        Args:
            last_message: Most recent message

        Returns:
            True if pattern should terminate
        """
        pass

    def add_message(self, message: Message):
        """Add message to history"""
        self.history.append(message)

        # Track consecutive same agent
        if message.sender == self._last_agent_name:
            self._consecutive_same_agent += 1
        else:
            self._consecutive_same_agent = 1
            self._last_agent_name = message.sender

        # Trigger callbacks
        for callback in self._on_message:
            callback(message)

    def get_context(self) -> Dict[str, Any]:
        """Get current context for agent selection"""
        return {
            "round": self.current_round,
            "history": self.history,
            "last_message": self.history[-1] if self.history else None,
            "agents": self.agents,
            "agent_names": self.agent_names,
            "config": self.config,
            "consecutive_same_agent": self._consecutive_same_agent,
            "last_agent_name": self._last_agent_name
        }

    async def _select_agent_for_run(self, context: Dict[str, Any]) -> Optional[Agent]:
        """
        Select next agent during run loop. Override in subclasses for async selection.

        Args:
            context: Current conversation context

        Returns:
            Next agent to speak, or None if pattern complete
        """
        return self.select_next_agent(context)

    async def run(self, initial_message: str) -> PatternResult:
        """
        Execute the pattern.

        Args:
            initial_message: Initial user message

        Returns:
            PatternResult with execution details
        """
        start_time = datetime.now()
        self.status = PatternStatus.RUNNING
        agents_used = set()

        try:
            # Add initial message
            user_message = Message(
                content=initial_message,
                sender="user",
                role=MessageRole.USER
            )
            self.add_message(user_message)

            # Execute rounds
            while self.current_round < self.config.max_rounds:
                self.current_round += 1
                context = self.get_context()

                # Select next agent (allows async override)
                next_agent = await self._select_agent_for_run(context)

                if next_agent is None:
                    # No more agents to select
                    break

                # Trigger agent selected callback
                for callback in self._on_agent_selected:
                    callback(next_agent)

                # Check consecutive same agent limit
                if (self._consecutive_same_agent >= self.config.max_consecutive_same_agent
                        and next_agent.name == self._last_agent_name):
                    break

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

                # Add agent response
                agent_message = Message(
                    content=response,
                    sender=next_agent.name,
                    role=MessageRole.AGENT
                )
                self.add_message(agent_message)

                # Check termination
                if self.should_terminate(agent_message):
                    break

                # Trigger round complete callback
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

    def reset(self):
        """Reset pattern state"""
        self.current_round = 0
        self.history = []
        self.status = PatternStatus.PENDING
        self._consecutive_same_agent = 0
        self._last_agent_name = None

    # Event registration
    def on_message(self, callback: Callable[[Message], None]):
        """Register message callback"""
        self._on_message.append(callback)

    def on_round_complete(self, callback: Callable[[int], None]):
        """Register round complete callback"""
        self._on_round_complete.append(callback)

    def on_agent_selected(self, callback: Callable[[Agent], None]):
        """Register agent selected callback"""
        self._on_agent_selected.append(callback)
