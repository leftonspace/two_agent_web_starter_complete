"""
Agent messaging system for streaming agent communications to chat.

PHASE 7.2: Allows Manager/Supervisor/Employee to post messages that appear
in the conversational chat interface in real-time.

Architecture:
    Agent → MessageBus → Listeners (Chat UI, Logging, etc.)

Features:
    - Real-time message streaming
    - Request/response for user approvals
    - Message queueing and delivery
    - Timeout handling for responses
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Enums and Data Classes
# ══════════════════════════════════════════════════════════════════════


class AgentRole(Enum):
    """Agent roles in the system"""
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    EMPLOYEE = "employee"
    SYSTEM = "system"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """Message from an agent"""
    message_id: str
    role: AgentRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_response: bool = False  # True if waiting for user input
    response_timeout: Optional[int] = None  # Seconds to wait
    priority: MessagePriority = MessagePriority.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "message_id": self.message_id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "requires_response": self.requires_response,
            "response_timeout": self.response_timeout,
            "priority": self.priority.value
        }


# ══════════════════════════════════════════════════════════════════════
# Message Bus
# ══════════════════════════════════════════════════════════════════════


class AgentMessageBus:
    """
    Message bus for agent-to-user communication.

    Agents post messages, which are streamed to chat interface.
    Can wait for user responses when approval/input is needed.

    Usage:
        # Subscribe to messages
        bus = AgentMessageBus()
        bus.subscribe(my_callback)

        # Post message
        await bus.post_message(
            role=AgentRole.MANAGER,
            content="Planning task..."
        )

        # Request user response
        response = await bus.post_message(
            role=AgentRole.MANAGER,
            content="Proceed with changes? [yes/no]",
            requires_response=True,
            response_timeout=300
        )
    """

    def __init__(self):
        """Initialize message bus"""
        self.listeners: List[Callable] = []
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_history: List[AgentMessage] = []
        self.max_history: int = 1000

    def subscribe(self, callback: Callable):
        """
        Subscribe to agent messages.

        Args:
            callback: Async function that receives AgentMessage
        """
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback: Callable):
        """
        Unsubscribe from agent messages.

        Args:
            callback: Previously subscribed callback
        """
        if callback in self.listeners:
            self.listeners.remove(callback)

    async def post_message(
        self,
        role: AgentRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        requires_response: bool = False,
        response_timeout: int = 300,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[str]:
        """
        Post message from agent.

        If requires_response=True, blocks until user responds or timeout.

        Args:
            role: Agent role posting the message
            content: Message content
            metadata: Additional metadata
            requires_response: Whether to wait for user response
            response_timeout: Timeout in seconds for response
            priority: Message priority level

        Returns:
            User response if requires_response=True, else None
        """
        message_id = self._generate_message_id()

        message = AgentMessage(
            message_id=message_id,
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
            requires_response=requires_response,
            response_timeout=response_timeout,
            priority=priority
        )

        # Add to history
        self._add_to_history(message)

        # Notify all listeners
        await self._notify_listeners(message)

        # Wait for response if needed
        if requires_response:
            future = asyncio.Future()
            self.pending_responses[message_id] = future

            try:
                response = await asyncio.wait_for(
                    future,
                    timeout=response_timeout
                )
                return response
            except asyncio.TimeoutError:
                # Timeout - return None
                return None
            finally:
                # Clean up
                if message_id in self.pending_responses:
                    del self.pending_responses[message_id]

        return None

    def provide_response(self, message_id: str, response: str) -> bool:
        """
        Provide user response to a pending message.

        Args:
            message_id: ID of message being responded to
            response: User's response text

        Returns:
            True if response was delivered, False if no pending message
        """
        if message_id in self.pending_responses:
            future = self.pending_responses[message_id]
            if not future.done():
                future.set_result(response)
                return True
        return False

    def get_pending_messages(self) -> List[AgentMessage]:
        """
        Get list of messages waiting for user response.

        Returns:
            List of pending messages
        """
        pending = []
        for message in self.message_history:
            if message.requires_response and message.message_id in self.pending_responses:
                pending.append(message)
        return pending

    def get_recent_messages(self, count: int = 50) -> List[AgentMessage]:
        """
        Get recent messages from history.

        Args:
            count: Number of messages to retrieve

        Returns:
            List of recent messages
        """
        return self.message_history[-count:]

    def clear_history(self):
        """Clear message history"""
        self.message_history.clear()

    async def _notify_listeners(self, message: AgentMessage):
        """Notify all subscribed listeners of new message"""
        tasks = []
        for listener in self.listeners:
            # Call listener (could be async or sync)
            if asyncio.iscoroutinefunction(listener):
                tasks.append(asyncio.create_task(listener(message)))
            else:
                # Sync callback - run in executor
                loop = asyncio.get_event_loop()
                tasks.append(loop.run_in_executor(None, listener, message))

        # Wait for all listeners to process
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _add_to_history(self, message: AgentMessage):
        """Add message to history with size limit"""
        self.message_history.append(message)

        # Trim history if too large
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        return f"msg_{uuid.uuid4().hex[:12]}"


# ══════════════════════════════════════════════════════════════════════
# Infinite Loop Detection (R1 Reliability Fix)
# ══════════════════════════════════════════════════════════════════════


class LoopDetector:
    """
    Detects infinite retry loops in agent execution.

    R1 Fix: If same feedback appears 2+ times consecutively,
    alert user instead of continuing infinite retries.
    """

    def __init__(self, max_consecutive: int = 2):
        """
        Initialize loop detector.

        Args:
            max_consecutive: Maximum consecutive identical feedback before alerting
        """
        self.retry_history: List[Dict[str, Any]] = []
        self.max_consecutive = max_consecutive

    def record_retry(self, feedback: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record a retry attempt.

        Args:
            feedback: Feedback that triggered retry
            metadata: Additional context
        """
        self.retry_history.append({
            "feedback": feedback,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        })

        # Keep only last 10 retries
        self.retry_history = self.retry_history[-10:]

    def check_loop(self) -> tuple[bool, Optional[str]]:
        """
        Check if agent is in infinite loop.

        Returns:
            (is_loop, repeated_feedback) tuple
        """
        if len(self.retry_history) < self.max_consecutive:
            return False, None

        # Check last N retries for identical feedback
        recent = self.retry_history[-self.max_consecutive:]
        feedbacks = [r["feedback"] for r in recent]

        # All feedback identical?
        if len(set(feedbacks)) == 1:
            return True, feedbacks[0]

        return False, None

    def reset(self):
        """Reset retry history"""
        self.retry_history.clear()


# ══════════════════════════════════════════════════════════════════════
# Global Instances
# ══════════════════════════════════════════════════════════════════════


# Global message bus - used throughout the system
_global_bus: Optional[AgentMessageBus] = None


def get_message_bus() -> AgentMessageBus:
    """
    Get global message bus instance (singleton).

    Returns:
        Global AgentMessageBus instance
    """
    global _global_bus
    if _global_bus is None:
        _global_bus = AgentMessageBus()
    return _global_bus


def reset_message_bus():
    """Reset global message bus (useful for testing)"""
    global _global_bus
    _global_bus = None


# ══════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════


async def post_manager_message(content: str, **kwargs) -> Optional[str]:
    """Shortcut to post manager message"""
    bus = get_message_bus()
    return await bus.post_message(AgentRole.MANAGER, content, **kwargs)


async def post_supervisor_message(content: str, **kwargs) -> Optional[str]:
    """Shortcut to post supervisor message"""
    bus = get_message_bus()
    return await bus.post_message(AgentRole.SUPERVISOR, content, **kwargs)


async def post_employee_message(content: str, **kwargs) -> Optional[str]:
    """Shortcut to post employee message"""
    bus = get_message_bus()
    return await bus.post_message(AgentRole.EMPLOYEE, content, **kwargs)


async def post_system_message(content: str, **kwargs) -> Optional[str]:
    """Shortcut to post system message"""
    bus = get_message_bus()
    return await bus.post_message(AgentRole.SYSTEM, content, **kwargs)


# ══════════════════════════════════════════════════════════════════════
# Module Exports
# ══════════════════════════════════════════════════════════════════════


__all__ = [
    "AgentRole",
    "MessagePriority",
    "AgentMessage",
    "AgentMessageBus",
    "LoopDetector",
    "get_message_bus",
    "reset_message_bus",
    "post_manager_message",
    "post_supervisor_message",
    "post_employee_message",
    "post_system_message",
]
