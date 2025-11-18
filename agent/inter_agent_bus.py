# inter_agent_bus.py
"""
PHASE 3: Inter-Agent Communication Bus

This module provides a safe, structured system for horizontal communication between agents:
- Supervisor → Manager suggestions
- Employee → Manager clarifications
- Manager → Tools (metadata access, tool execution requests)
- Employee → Tools (direct execution via orchestrator)
- Supervisor → Employee targeted fix requests

KEY FEATURES:
- In-memory message queue (no threading/async complexity)
- All messages logged to core_logging for debugging
- Type-safe message structure
- Support for request/response patterns
- Prevents dependency on Prompt Master for micro-interactions

MESSAGE FLOW:
  Agent A --[send_message]--> Bus --[get_messages_for]--> Agent B
  Agent B --[respond_to_message]--> Bus --[get_response]--> Agent A
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Message Types
# ══════════════════════════════════════════════════════════════════════


class MessageType(str, Enum):
    """Types of messages that can be sent between agents."""

    # Supervisor → Manager
    SUGGESTION = "suggestion"  # Suggest roadmap change, stage merge, etc.
    FINDING_REPORT = "finding_report"  # Report findings from audit
    AUTO_ADVANCE_REQUEST = "auto_advance_request"  # Request auto-advance (0 findings)

    # Employee → Manager
    CLARIFICATION_REQUEST = "clarification_request"  # Ask for task clarification
    BLOCKER_REPORT = "blocker_report"  # Report blocking issue

    # Manager → Supervisor
    AUDIT_REQUEST = "audit_request"  # Request audit of work
    CLARIFICATION_RESPONSE = "clarification_response"  # Answer clarification

    # Manager → Employee
    TARGETED_FIX_REQUEST = "targeted_fix_request"  # Request specific fix

    # Supervisor → Employee
    TARGETED_FEEDBACK = "targeted_feedback"  # Direct feedback on specific issue

    # Any agent → Tools
    TOOL_EXECUTION_REQUEST = "tool_execution_request"  # Request tool execution

    # Tools → Any agent
    TOOL_EXECUTION_RESULT = "tool_execution_result"  # Tool execution result

    # Generic
    INFO = "info"  # Informational message
    ERROR = "error"  # Error message


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class Message:
    """
    A message in the inter-agent bus.

    Attributes:
        id: Unique message identifier
        timestamp: Unix timestamp when message was created
        from_agent: Sender agent (manager, supervisor, employee, tools)
        to_agent: Recipient agent
        message_type: Type of message
        subject: Brief subject line
        body: Message content (can be text or structured data)
        context: Additional context/metadata
        in_reply_to: ID of message this is replying to (if any)
        requires_response: Whether this message expects a response
        response_id: ID of response message (if responded)
    """
    id: str
    timestamp: float
    from_agent: str
    to_agent: str
    message_type: MessageType
    subject: str
    body: Any
    context: Dict[str, Any] = field(default_factory=dict)
    in_reply_to: Optional[str] = None
    requires_response: bool = False
    response_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        """Create from dict."""
        data["message_type"] = MessageType(data["message_type"])
        return cls(**data)


# ══════════════════════════════════════════════════════════════════════
# Inter-Agent Bus Class
# ══════════════════════════════════════════════════════════════════════


class InterAgentBus:
    """
    Manages message passing between agents.

    Provides:
    - Send/receive messages
    - Request/response patterns
    - Message filtering by type/agent
    - Message history for debugging
    """

    def __init__(self):
        """Initialize the message bus."""
        self._messages: Dict[str, Message] = {}  # message_id -> Message
        self._agent_inboxes: Dict[str, List[str]] = {}  # agent -> [message_ids]
        self._message_log_callback: Optional[callable] = None

    def set_log_callback(self, callback: callable):
        """
        Set callback for logging messages.

        Args:
            callback: Function(message: Message) -> None
        """
        self._message_log_callback = callback

    # ──────────────────────────────────────────────────────────────────
    # Send/Receive Operations
    # ──────────────────────────────────────────────────────────────────

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: MessageType,
        subject: str,
        body: Any,
        context: Optional[Dict[str, Any]] = None,
        in_reply_to: Optional[str] = None,
        requires_response: bool = False
    ) -> str:
        """
        Send a message from one agent to another.

        Args:
            from_agent: Sender agent name
            to_agent: Recipient agent name
            message_type: Type of message
            subject: Brief subject line
            body: Message content
            context: Additional context/metadata
            in_reply_to: ID of message being replied to
            requires_response: Whether response is expected

        Returns:
            Message ID
        """
        message_id = str(uuid.uuid4())

        message = Message(
            id=message_id,
            timestamp=time.time(),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            subject=subject,
            body=body,
            context=context or {},
            in_reply_to=in_reply_to,
            requires_response=requires_response,
        )

        # Store message
        self._messages[message_id] = message

        # Add to recipient's inbox
        if to_agent not in self._agent_inboxes:
            self._agent_inboxes[to_agent] = []
        self._agent_inboxes[to_agent].append(message_id)

        # Log message if callback set
        if self._message_log_callback:
            try:
                self._message_log_callback(message)
            except Exception:
                pass  # Best effort logging

        return message_id

    def get_messages_for(
        self,
        agent: str,
        message_type: Optional[MessageType] = None,
        from_agent: Optional[str] = None,
        unread_only: bool = False
    ) -> List[Message]:
        """
        Get messages for an agent.

        Args:
            agent: Agent name
            message_type: Filter by message type (if provided)
            from_agent: Filter by sender (if provided)
            unread_only: Only return messages without responses

        Returns:
            List of Message objects
        """
        if agent not in self._agent_inboxes:
            return []

        message_ids = self._agent_inboxes[agent]
        messages = []

        for msg_id in message_ids:
            msg = self._messages.get(msg_id)
            if msg is None:
                continue

            # Apply filters
            if message_type and msg.message_type != message_type:
                continue
            if from_agent and msg.from_agent != from_agent:
                continue
            if unread_only and msg.response_id is not None:
                continue

            messages.append(msg)

        return messages

    def respond_to_message(
        self,
        original_message_id: str,
        from_agent: str,
        subject: str,
        body: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a response to a message.

        Args:
            original_message_id: ID of message being responded to
            from_agent: Responder agent name
            subject: Response subject
            body: Response content
            context: Additional context

        Returns:
            Response message ID

        Raises:
            ValueError: If original message not found
        """
        original_msg = self._messages.get(original_message_id)
        if original_msg is None:
            raise ValueError(f"Message not found: {original_message_id}")

        # Send response
        response_id = self.send_message(
            from_agent=from_agent,
            to_agent=original_msg.from_agent,
            message_type=MessageType.INFO,  # Responses are generic
            subject=subject,
            body=body,
            context=context,
            in_reply_to=original_message_id,
            requires_response=False,
        )

        # Mark original as responded
        original_msg.response_id = response_id

        return response_id

    def get_response(self, message_id: str) -> Optional[Message]:
        """
        Get response to a message (if any).

        Args:
            message_id: Original message ID

        Returns:
            Response Message, or None if not yet responded
        """
        original_msg = self._messages.get(message_id)
        if original_msg is None or original_msg.response_id is None:
            return None

        return self._messages.get(original_msg.response_id)

    # ──────────────────────────────────────────────────────────────────
    # Query Operations
    # ──────────────────────────────────────────────────────────────────

    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Get a specific message by ID.

        Args:
            message_id: Message identifier

        Returns:
            Message object, or None if not found
        """
        return self._messages.get(message_id)

    def get_conversation(self, message_id: str) -> List[Message]:
        """
        Get full conversation thread for a message.

        Args:
            message_id: Any message ID in the thread

        Returns:
            List of messages in thread, ordered by timestamp
        """
        # Find root message
        current = self._messages.get(message_id)
        if current is None:
            return []

        while current.in_reply_to:
            parent = self._messages.get(current.in_reply_to)
            if parent is None:
                break
            current = parent

        root_id = current.id

        # Collect all messages in thread
        thread = [current]
        to_check = [root_id]
        checked = {root_id}

        while to_check:
            parent_id = to_check.pop(0)
            for msg in self._messages.values():
                if msg.in_reply_to == parent_id and msg.id not in checked:
                    thread.append(msg)
                    to_check.append(msg.id)
                    checked.add(msg.id)

        # Sort by timestamp
        thread.sort(key=lambda m: m.timestamp)
        return thread

    def get_all_messages(self) -> List[Message]:
        """
        Get all messages in the bus.

        Returns:
            List of all Message objects
        """
        return list(self._messages.values())

    def get_pending_requests(self, agent: str) -> List[Message]:
        """
        Get all messages requiring response from an agent.

        Args:
            agent: Agent name

        Returns:
            List of Message objects awaiting response
        """
        messages = self.get_messages_for(agent, unread_only=True)
        return [m for m in messages if m.requires_response]

    # ──────────────────────────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """
        Get message bus statistics.

        Returns:
            Dict with statistics
        """
        total_messages = len(self._messages)
        messages_by_type = {}
        pending_responses = 0

        for msg in self._messages.values():
            msg_type = msg.message_type.value
            messages_by_type[msg_type] = messages_by_type.get(msg_type, 0) + 1
            if msg.requires_response and msg.response_id is None:
                pending_responses += 1

        return {
            "total_messages": total_messages,
            "messages_by_type": messages_by_type,
            "pending_responses": pending_responses,
            "agents_with_messages": len(self._agent_inboxes),
        }

    # ──────────────────────────────────────────────────────────────────
    # Helper Methods for Common Patterns
    # ──────────────────────────────────────────────────────────────────

    def supervisor_suggest_roadmap_change(
        self,
        suggestion: str,
        reason: str,
        proposed_changes: Dict[str, Any]
    ) -> str:
        """
        Supervisor suggests a roadmap change to Manager.

        Args:
            suggestion: Brief description of suggestion
            reason: Why this change is recommended
            proposed_changes: Structured description of changes

        Returns:
            Message ID
        """
        return self.send_message(
            from_agent="supervisor",
            to_agent="manager",
            message_type=MessageType.SUGGESTION,
            subject=f"Roadmap Change: {suggestion}",
            body={
                "suggestion": suggestion,
                "reason": reason,
                "proposed_changes": proposed_changes,
            },
            requires_response=True,
        )

    def employee_request_clarification(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Employee requests clarification from Manager.

        Args:
            question: The clarification question
            context: Context about why clarification is needed

        Returns:
            Message ID
        """
        return self.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=MessageType.CLARIFICATION_REQUEST,
            subject="Clarification Needed",
            body={
                "question": question,
                "context": context,
            },
            requires_response=True,
        )

    def supervisor_report_findings(
        self,
        findings: List[Dict[str, Any]],
        stage_id: str,
        recommendation: str
    ) -> str:
        """
        Supervisor reports audit findings to Manager.

        Args:
            findings: List of finding dicts
            stage_id: Stage being audited
            recommendation: Supervisor's recommendation

        Returns:
            Message ID
        """
        return self.send_message(
            from_agent="supervisor",
            to_agent="manager",
            message_type=MessageType.FINDING_REPORT,
            subject=f"Audit Report: {len(findings)} findings",
            body={
                "findings": findings,
                "stage_id": stage_id,
                "recommendation": recommendation,
            },
            context={"stage_id": stage_id},
        )

    def supervisor_request_auto_advance(
        self,
        stage_id: str,
        reason: str = "Zero findings in audit"
    ) -> str:
        """
        Supervisor requests auto-advance (zero findings).

        Args:
            stage_id: Stage that passed audit
            reason: Reason for auto-advance

        Returns:
            Message ID
        """
        return self.send_message(
            from_agent="supervisor",
            to_agent="manager",
            message_type=MessageType.AUTO_ADVANCE_REQUEST,
            subject="Request Auto-Advance",
            body={
                "stage_id": stage_id,
                "reason": reason,
            },
            context={"stage_id": stage_id},
            requires_response=True,
        )


# ══════════════════════════════════════════════════════════════════════
# Global Bus Instance
# ══════════════════════════════════════════════════════════════════════

# Global instance for use across orchestrator
_global_bus: Optional[InterAgentBus] = None


def get_bus() -> InterAgentBus:
    """
    Get the global inter-agent bus instance.

    Returns:
        Global InterAgentBus instance
    """
    global _global_bus
    if _global_bus is None:
        _global_bus = InterAgentBus()
    return _global_bus


def reset_bus():
    """Reset the global bus (for testing)."""
    global _global_bus
    _global_bus = InterAgentBus()
