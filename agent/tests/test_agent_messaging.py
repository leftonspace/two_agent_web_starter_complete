"""
Test agent messaging and 3-agent integration.

PHASE 7.2: Tests for Manager/Supervisor/Employee message streaming.

Run: pytest agent/tests/test_agent_messaging.py -v
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from agent_messaging import (
    AgentMessage,
    AgentMessageBus,
    AgentRole,
    LoopDetector,
    MessagePriority,
    get_message_bus,
    post_employee_message,
    post_manager_message,
    post_supervisor_message,
    post_system_message,
    reset_message_bus,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def message_bus():
    """Create fresh message bus for each test"""
    reset_message_bus()
    return AgentMessageBus()


@pytest.fixture
def loop_detector():
    """Create loop detector for testing"""
    return LoopDetector()


# ══════════════════════════════════════════════════════════════════════
# AgentMessage Tests
# ══════════════════════════════════════════════════════════════════════


class TestAgentMessage:
    """Test AgentMessage data class"""

    def test_agent_message_creation(self):
        """Test creating agent message"""
        msg = AgentMessage(
            message_id="msg_123",
            role=AgentRole.MANAGER,
            content="Planning task",
            timestamp=datetime.now(),
            metadata={"phase": "planning"}
        )

        assert msg.message_id == "msg_123"
        assert msg.role == AgentRole.MANAGER
        assert msg.content == "Planning task"
        assert msg.metadata["phase"] == "planning"
        assert msg.requires_response is False

    def test_agent_message_to_dict(self):
        """Test message serialization"""
        timestamp = datetime.now()
        msg = AgentMessage(
            message_id="msg_123",
            role=AgentRole.SUPERVISOR,
            content="Review complete",
            timestamp=timestamp,
            priority=MessagePriority.HIGH
        )

        data = msg.to_dict()

        assert data["message_id"] == "msg_123"
        assert data["role"] == "supervisor"
        assert data["content"] == "Review complete"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["priority"] == "high"


# ══════════════════════════════════════════════════════════════════════
# AgentMessageBus Tests
# ══════════════════════════════════════════════════════════════════════


class TestAgentMessageBus:
    """Test message bus functionality"""

    @pytest.mark.asyncio
    async def test_post_message(self, message_bus):
        """Test posting simple message"""
        messages_received = []

        async def listener(msg):
            messages_received.append(msg)

        message_bus.subscribe(listener)

        await message_bus.post_message(
            role=AgentRole.MANAGER,
            content="Planning task"
        )

        # Wait for async processing
        await asyncio.sleep(0.1)

        assert len(messages_received) == 1
        assert messages_received[0].role == AgentRole.MANAGER
        assert messages_received[0].content == "Planning task"

    @pytest.mark.asyncio
    async def test_post_message_with_metadata(self, message_bus):
        """Test posting message with metadata"""
        messages_received = []

        async def listener(msg):
            messages_received.append(msg)

        message_bus.subscribe(listener)

        await message_bus.post_message(
            role=AgentRole.EMPLOYEE,
            content="Task complete",
            metadata={"task_id": "task_123", "status": "success"}
        )

        await asyncio.sleep(0.1)

        assert len(messages_received) == 1
        msg = messages_received[0]
        assert msg.metadata["task_id"] == "task_123"
        assert msg.metadata["status"] == "success"

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, message_bus):
        """Test subscribing and unsubscribing"""
        messages_received = []

        async def listener(msg):
            messages_received.append(msg)

        # Subscribe
        message_bus.subscribe(listener)
        await message_bus.post_message(AgentRole.MANAGER, "Message 1")
        await asyncio.sleep(0.1)
        assert len(messages_received) == 1

        # Unsubscribe
        message_bus.unsubscribe(listener)
        await message_bus.post_message(AgentRole.MANAGER, "Message 2")
        await asyncio.sleep(0.1)
        assert len(messages_received) == 1  # Should still be 1

    @pytest.mark.asyncio
    async def test_message_requires_response(self, message_bus):
        """Test message requiring user response"""
        async def responder(msg):
            if msg.requires_response:
                # Simulate user responding after delay
                await asyncio.sleep(0.1)
                message_bus.provide_response(msg.message_id, "yes")

        message_bus.subscribe(responder)

        # Post message requiring response
        response = await message_bus.post_message(
            role=AgentRole.MANAGER,
            content="Proceed with changes? [yes/no]",
            requires_response=True,
            response_timeout=5
        )

        assert response == "yes"

    @pytest.mark.asyncio
    async def test_message_response_timeout(self, message_bus):
        """Test message response timeout"""
        # Don't provide response - should timeout
        response = await message_bus.post_message(
            role=AgentRole.SUPERVISOR,
            content="Waiting for response",
            requires_response=True,
            response_timeout=0.2  # Very short timeout
        )

        assert response is None  # Timeout should return None

    @pytest.mark.asyncio
    async def test_multiple_listeners(self, message_bus):
        """Test multiple listeners receive messages"""
        received1 = []
        received2 = []

        async def listener1(msg):
            received1.append(msg)

        async def listener2(msg):
            received2.append(msg)

        message_bus.subscribe(listener1)
        message_bus.subscribe(listener2)

        await message_bus.post_message(AgentRole.EMPLOYEE, "Test message")
        await asyncio.sleep(0.1)

        assert len(received1) == 1
        assert len(received2) == 1
        assert received1[0].content == "Test message"
        assert received2[0].content == "Test message"

    def test_get_recent_messages(self, message_bus):
        """Test retrieving recent messages"""
        # Post several messages (sync for simplicity)
        for i in range(5):
            msg = AgentMessage(
                message_id=f"msg_{i}",
                role=AgentRole.MANAGER,
                content=f"Message {i}",
                timestamp=datetime.now()
            )
            message_bus._add_to_history(msg)

        recent = message_bus.get_recent_messages(count=3)
        assert len(recent) == 3
        assert recent[0].content == "Message 2"
        assert recent[2].content == "Message 4"

    def test_get_pending_messages(self, message_bus):
        """Test retrieving pending messages"""
        # Create pending message
        msg = AgentMessage(
            message_id="msg_pending",
            role=AgentRole.SUPERVISOR,
            content="Waiting for approval",
            timestamp=datetime.now(),
            requires_response=True
        )
        message_bus._add_to_history(msg)

        # Add to pending
        future = asyncio.Future()
        message_bus.pending_responses["msg_pending"] = future

        pending = message_bus.get_pending_messages()
        assert len(pending) == 1
        assert pending[0].content == "Waiting for approval"

    def test_message_history_limit(self, message_bus):
        """Test message history size limit"""
        message_bus.max_history = 10

        # Add 15 messages
        for i in range(15):
            msg = AgentMessage(
                message_id=f"msg_{i}",
                role=AgentRole.EMPLOYEE,
                content=f"Message {i}",
                timestamp=datetime.now()
            )
            message_bus._add_to_history(msg)

        # Should only keep last 10
        assert len(message_bus.message_history) == 10
        assert message_bus.message_history[0].content == "Message 5"


# ══════════════════════════════════════════════════════════════════════
# LoopDetector Tests (R1 Reliability Fix)
# ══════════════════════════════════════════════════════════════════════


class TestLoopDetector:
    """Test infinite loop detection"""

    def test_no_loop_different_feedback(self, loop_detector):
        """Test no loop detected with different feedback"""
        loop_detector.record_retry("fix error X")
        loop_detector.record_retry("fix error Y")

        is_loop, repeated = loop_detector.check_loop()
        assert is_loop is False
        assert repeated is None

    def test_loop_detected_same_feedback(self, loop_detector):
        """Test loop detected with same feedback"""
        loop_detector.record_retry("fix error X")
        loop_detector.record_retry("fix error X")

        is_loop, repeated = loop_detector.check_loop()
        assert is_loop is True
        assert repeated == "fix error X"

    def test_loop_not_detected_insufficient_retries(self, loop_detector):
        """Test loop not detected with only one retry"""
        loop_detector.record_retry("fix error X")

        is_loop, repeated = loop_detector.check_loop()
        assert is_loop is False

    def test_loop_reset(self, loop_detector):
        """Test resetting loop detector"""
        loop_detector.record_retry("fix error X")
        loop_detector.record_retry("fix error X")

        assert loop_detector.check_loop()[0] is True

        loop_detector.reset()
        assert len(loop_detector.retry_history) == 0
        assert loop_detector.check_loop()[0] is False

    def test_loop_detector_history_limit(self, loop_detector):
        """Test loop detector history limit"""
        # Record 15 retries
        for i in range(15):
            loop_detector.record_retry(f"error {i}")

        # Should only keep last 10
        assert len(loop_detector.retry_history) <= 10


# ══════════════════════════════════════════════════════════════════════
# Helper Functions Tests
# ══════════════════════════════════════════════════════════════════════


class TestHelperFunctions:
    """Test helper posting functions"""

    @pytest.mark.asyncio
    async def test_post_manager_message(self):
        """Test manager message shortcut"""
        reset_message_bus()
        bus = get_message_bus()

        messages = []

        async def listener(msg):
            messages.append(msg)

        bus.subscribe(listener)

        await post_manager_message("Planning complete")
        await asyncio.sleep(0.1)

        assert len(messages) == 1
        assert messages[0].role == AgentRole.MANAGER

    @pytest.mark.asyncio
    async def test_post_supervisor_message(self):
        """Test supervisor message shortcut"""
        reset_message_bus()
        bus = get_message_bus()

        messages = []

        async def listener(msg):
            messages.append(msg)

        bus.subscribe(listener)

        await post_supervisor_message("Review complete")
        await asyncio.sleep(0.1)

        assert len(messages) == 1
        assert messages[0].role == AgentRole.SUPERVISOR

    @pytest.mark.asyncio
    async def test_post_employee_message(self):
        """Test employee message shortcut"""
        reset_message_bus()
        bus = get_message_bus()

        messages = []

        async def listener(msg):
            messages.append(msg)

        bus.subscribe(listener)

        await post_employee_message("Task complete")
        await asyncio.sleep(0.1)

        assert len(messages) == 1
        assert messages[0].role == AgentRole.EMPLOYEE

    @pytest.mark.asyncio
    async def test_post_system_message(self):
        """Test system message shortcut"""
        reset_message_bus()
        bus = get_message_bus()

        messages = []

        async def listener(msg):
            messages.append(msg)

        bus.subscribe(listener)

        await post_system_message("System alert")
        await asyncio.sleep(0.1)

        assert len(messages) == 1
        assert messages[0].role == AgentRole.SYSTEM


# ══════════════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════════════


class TestIntegration:
    """Integration tests for message bus"""

    @pytest.mark.asyncio
    async def test_manager_supervisor_employee_flow(self):
        """Test full 3-agent message flow"""
        reset_message_bus()
        bus = get_message_bus()

        messages = []

        async def listener(msg):
            messages.append(msg)

        bus.subscribe(listener)

        # Simulate 3-agent workflow
        await post_manager_message("📋 Planning: Build website")
        await post_supervisor_message("🔍 Reviewing plan")
        await post_employee_message("🛠️ Building HTML structure")
        await post_employee_message("✅ HTML complete")
        await post_supervisor_message("✅ Review passed")

        await asyncio.sleep(0.1)

        assert len(messages) == 5
        assert messages[0].role == AgentRole.MANAGER
        assert messages[1].role == AgentRole.SUPERVISOR
        assert messages[2].role == AgentRole.EMPLOYEE
        assert "Planning" in messages[0].content
        assert "Building" in messages[2].content

    @pytest.mark.asyncio
    async def test_approval_workflow(self):
        """Test approval request workflow"""
        reset_message_bus()
        bus = get_message_bus()

        async def auto_approver(msg):
            if msg.requires_response:
                await asyncio.sleep(0.1)
                bus.provide_response(msg.message_id, "approved")

        bus.subscribe(auto_approver)

        # Request approval
        response = await post_manager_message(
            "Task requires destructive changes. Approve? [approved/denied]",
            requires_response=True,
            response_timeout=5
        )

        assert response == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
