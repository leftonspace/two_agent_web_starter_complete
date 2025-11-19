"""
STAGE 3 INTEGRATION: Unit Tests for inter_agent_bus.py

Tests the inter-agent communication bus system.
"""

import json
import time
import unittest
from pathlib import Path

# Import the inter-agent bus module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import inter_agent_bus


class TestMessage(unittest.TestCase):
    """Test Message data model."""

    def test_message_creation(self):
        """Test creating a message."""
        message = inter_agent_bus.Message(
            id="msg-1",
            timestamp=time.time(),
            from_agent="manager",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.TARGETED_FIX_REQUEST,
            subject="Fix button",
            body={"file": "index.html", "line": 42},
        )

        self.assertEqual(message.from_agent, "manager")
        self.assertEqual(message.to_agent, "employee")
        self.assertEqual(message.message_type, inter_agent_bus.MessageType.TARGETED_FIX_REQUEST)
        self.assertFalse(message.requires_response)

    def test_message_to_dict(self):
        """Test message serialization."""
        message = inter_agent_bus.Message(
            id="msg-1",
            timestamp=time.time(),
            from_agent="manager",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.INFO,
            subject="Test",
            body="Test message",
        )

        msg_dict = message.to_dict()
        self.assertIsInstance(msg_dict, dict)
        self.assertEqual(msg_dict["from_agent"], "manager")
        self.assertEqual(msg_dict["message_type"], "info")


class TestInterAgentBus(unittest.TestCase):
    """Test InterAgentBus class."""

    def setUp(self):
        """Set up test fixtures."""
        self.bus = inter_agent_bus.InterAgentBus()

    def test_send_message(self):
        """Test sending a message."""
        msg_id = self.bus.send_message(
            from_agent="manager",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.TARGETED_FIX_REQUEST,
            subject="Fix button",
            body="Please fix the submit button",
        )

        self.assertIsNotNone(msg_id)
        self.assertIsInstance(msg_id, str)

    def test_get_messages_for_agent(self):
        """Test retrieving messages for an agent."""
        # Send two messages to employee
        self.bus.send_message(
            from_agent="manager",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.TARGETED_FIX_REQUEST,
            subject="Fix 1",
            body="Fix issue 1",
        )

        self.bus.send_message(
            from_agent="supervisor",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.TARGETED_FEEDBACK,
            subject="Feedback",
            body="Good work",
        )

        # Send one message to manager
        self.bus.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=inter_agent_bus.MessageType.CLARIFICATION_REQUEST,
            subject="Question",
            body="Need clarification",
        )

        # Get messages for employee
        employee_messages = self.bus.get_messages_for("employee")
        self.assertEqual(len(employee_messages), 2)

        # Get messages for manager
        manager_messages = self.bus.get_messages_for("manager")
        self.assertEqual(len(manager_messages), 1)

    def test_get_messages_by_type(self):
        """Test filtering messages by type."""
        # Send different types of messages
        self.bus.send_message(
            from_agent="manager",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.TARGETED_FIX_REQUEST,
            subject="Fix",
            body="Fix it",
        )

        self.bus.send_message(
            from_agent="supervisor",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.INFO,
            subject="Info",
            body="FYI",
        )

        # Filter by type
        fix_requests = self.bus.get_messages_for(
            "employee",
            message_type=inter_agent_bus.MessageType.TARGETED_FIX_REQUEST
        )

        self.assertEqual(len(fix_requests), 1)
        self.assertEqual(fix_requests[0].subject, "Fix")

    def test_respond_to_message(self):
        """Test responding to a message."""
        # Send original message
        msg_id = self.bus.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=inter_agent_bus.MessageType.CLARIFICATION_REQUEST,
            subject="Question",
            body="Should button be blue?",
            requires_response=True,
        )

        # Respond to it
        response_id = self.bus.respond_to_message(
            original_message_id=msg_id,
            from_agent="manager",
            subject="Re: Question",
            body="Yes, blue is correct",
        )

        self.assertIsNotNone(response_id)

        # Get original message and check response link
        original_msg = self.bus.get_message(msg_id)
        self.assertEqual(original_msg.response_id, response_id)

        # Get response message
        response_msg = self.bus.get_message(response_id)
        self.assertEqual(response_msg.in_reply_to, msg_id)

    def test_get_response(self):
        """Test getting response to a message."""
        # Send message requiring response
        msg_id = self.bus.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=inter_agent_bus.MessageType.CLARIFICATION_REQUEST,
            subject="Question",
            body="Need help",
            requires_response=True,
        )

        # Respond
        self.bus.respond_to_message(
            original_message_id=msg_id,
            from_agent="manager",
            subject="Re: Question",
            body="Here's the answer",
        )

        # Get response
        response = self.bus.get_response(msg_id)
        self.assertIsNotNone(response)
        self.assertEqual(response.body, "Here's the answer")

    def test_log_callback(self):
        """Test message logging callback."""
        logged_messages = []

        def log_callback(msg):
            logged_messages.append(msg)

        self.bus.set_log_callback(log_callback)

        # Send a message
        self.bus.send_message(
            from_agent="manager",
            to_agent="employee",
            message_type=inter_agent_bus.MessageType.INFO,
            subject="Test",
            body="Test message",
        )

        # Check that callback was called
        self.assertEqual(len(logged_messages), 1)
        self.assertEqual(logged_messages[0].subject, "Test")

    def test_get_unresponded_messages(self):
        """Test getting messages that need responses."""
        # Send message requiring response
        self.bus.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=inter_agent_bus.MessageType.CLARIFICATION_REQUEST,
            subject="Question 1",
            body="Need help",
            requires_response=True,
        )

        # Send message not requiring response
        self.bus.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=inter_agent_bus.MessageType.INFO,
            subject="Info",
            body="FYI",
            requires_response=False,
        )

        # Send another message requiring response
        msg_id = self.bus.send_message(
            from_agent="employee",
            to_agent="manager",
            message_type=inter_agent_bus.MessageType.CLARIFICATION_REQUEST,
            subject="Question 2",
            body="Another question",
            requires_response=True,
        )

        # Respond to one
        self.bus.respond_to_message(msg_id, "manager", "Re: Question 2", "Answer")

        # Get pending requests (unresponded messages)
        pending = self.bus.get_pending_requests("manager")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].subject, "Question 1")


def run_tests():
    """Run all tests."""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
