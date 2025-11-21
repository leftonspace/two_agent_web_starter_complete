"""
Unit tests for conversational agent.

PHASE 7.1: Tests for natural language chat interface.

Run: pytest agent/tests/test_conversational_agent.py -v
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the modules we're testing
from conversational_agent import (
    ConversationalAgent,
    ConversationMessage,
    Intent,
    IntentType,
    TaskExecution,
)
from config import Config, ConversationalConfig


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_config():
    """Create mock configuration"""
    config = Config()
    config.conversational = ConversationalConfig()
    return config


@pytest.fixture
def agent(mock_config):
    """Create agent instance for testing"""
    with patch("conversational_agent.get_tool_metadata") as mock_metadata:
        mock_metadata.return_value = {
            "format_code": {
                "description": "Format source code",
                "schema": {
                    "required": ["project_dir"],
                    "properties": {
                        "project_dir": {"type": "string"},
                        "formatter": {"type": "string"}
                    }
                }
            },
            "run_tests": {
                "description": "Run test suite",
                "schema": {
                    "required": ["project_dir"],
                    "properties": {
                        "project_dir": {"type": "string"}
                    }
                }
            }
        }
        return ConversationalAgent(config=mock_config)


# ══════════════════════════════════════════════════════════════════════
# Basic Functionality Tests
# ══════════════════════════════════════════════════════════════════════


class TestConversationalAgentBasics:
    """Test basic agent functionality"""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert len(agent.conversation_history) == 0
        assert len(agent.active_tasks) == 0
        assert agent.session_id.startswith("session_")

    def test_session_id_generation(self, agent):
        """Test session ID is unique"""
        session_id1 = agent._generate_session_id()
        session_id2 = agent._generate_session_id()
        assert session_id1 != session_id2
        assert session_id1.startswith("session_")

    def test_task_id_generation(self, agent):
        """Test task ID is unique"""
        task_id1 = agent._generate_task_id()
        task_id2 = agent._generate_task_id()
        assert task_id1 != task_id2
        assert task_id1.startswith("task_")

    def test_conversation_history_tracking(self, agent):
        """Test conversation messages are tracked"""
        agent._add_message("user", "Hello")
        agent._add_message("assistant", "Hi there!")

        assert len(agent.conversation_history) == 2
        assert agent.conversation_history[0].role == "user"
        assert agent.conversation_history[0].content == "Hello"
        assert agent.conversation_history[1].role == "assistant"
        assert agent.conversation_history[1].content == "Hi there!"

    def test_clear_conversation(self, agent):
        """Test conversation history can be cleared"""
        agent._add_message("user", "Test message")
        assert len(agent.conversation_history) == 1

        agent.clear_conversation()
        assert len(agent.conversation_history) == 0


# ══════════════════════════════════════════════════════════════════════
# Intent Parsing Tests
# ══════════════════════════════════════════════════════════════════════


class TestIntentParsing:
    """Test intent classification and parsing"""

    @pytest.mark.asyncio
    async def test_parse_simple_action_intent(self, agent):
        """Test parsing simple action intent"""
        with patch("conversational_agent.chat_json") as mock_chat:
            mock_chat.return_value = {
                "type": "simple_action",
                "confidence": 0.9,
                "reasoning": "User wants to format code",
                "suggested_tool": "format_code",
                "parameters": {"project_dir": "./src"},
                "requires_approval": False,
                "estimated_time_seconds": 30
            }

            intent = await agent._parse_intent("Format the code in ./src")

            assert intent.type == IntentType.SIMPLE_ACTION
            assert intent.confidence == 0.9
            assert intent.suggested_tool == "format_code"
            assert intent.parameters == {"project_dir": "./src"}

    @pytest.mark.asyncio
    async def test_parse_complex_task_intent(self, agent):
        """Test parsing complex task intent"""
        with patch("conversational_agent.chat_json") as mock_chat:
            mock_chat.return_value = {
                "type": "complex_task",
                "confidence": 0.85,
                "reasoning": "Multi-step website creation",
                "complexity": "high",
                "requires_approval": True,
                "estimated_time_seconds": 600
            }

            intent = await agent._parse_intent("Create a portfolio website")

            assert intent.type == IntentType.COMPLEX_TASK
            assert intent.complexity == "high"
            assert intent.requires_approval is True

    @pytest.mark.asyncio
    async def test_parse_question_intent(self, agent):
        """Test parsing question intent"""
        with patch("conversational_agent.chat_json") as mock_chat:
            mock_chat.return_value = {
                "type": "question",
                "confidence": 0.95,
                "reasoning": "User is asking for information",
                "estimated_time_seconds": 10
            }

            intent = await agent._parse_intent("What tools are available?")

            assert intent.type == IntentType.QUESTION
            assert intent.confidence == 0.95

    @pytest.mark.asyncio
    async def test_parse_conversation_intent(self, agent):
        """Test parsing conversational greeting"""
        with patch("conversational_agent.chat_json") as mock_chat:
            mock_chat.return_value = {
                "type": "conversation",
                "confidence": 0.99,
                "reasoning": "User is greeting",
                "estimated_time_seconds": 5
            }

            intent = await agent._parse_intent("Hello!")

            assert intent.type == IntentType.CONVERSATION
            assert intent.confidence == 0.99

    @pytest.mark.asyncio
    async def test_intent_parsing_error_handling(self, agent):
        """Test intent parsing handles errors gracefully"""
        with patch("conversational_agent.chat_json") as mock_chat:
            mock_chat.side_effect = Exception("API Error")

            intent = await agent._parse_intent("Test message")

            # Should fall back to question type
            assert intent.type == IntentType.QUESTION
            assert intent.confidence == 0.5


# ══════════════════════════════════════════════════════════════════════
# Chat Interaction Tests
# ══════════════════════════════════════════════════════════════════════


class TestChatInteraction:
    """Test chat interface and message handling"""

    @pytest.mark.asyncio
    async def test_greeting_response(self, agent):
        """Test agent responds to greetings"""
        with patch.object(agent, "_parse_intent") as mock_parse:
            mock_parse.return_value = Intent(
                type=IntentType.CONVERSATION,
                confidence=0.95,
                reasoning="Greeting"
            )

            response = await agent.chat("Hello!")

            assert len(response) > 0
            assert any(word in response.lower() for word in ["hello", "hi", "help"])
            assert len(agent.conversation_history) == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_question_answering(self, agent):
        """Test agent answers questions"""
        with patch.object(agent, "_parse_intent") as mock_parse, \
             patch("conversational_agent.chat") as mock_chat:

            mock_parse.return_value = Intent(
                type=IntentType.QUESTION,
                confidence=0.9,
                reasoning="Information request"
            )
            mock_chat.return_value = "System-1.2 is a multi-agent orchestration platform."

            response = await agent.chat("What is System-1.2?")

            assert "System-1.2" in response
            assert len(agent.conversation_history) == 2

    @pytest.mark.asyncio
    async def test_simple_action_execution(self, agent):
        """Test simple action gets executed"""
        with patch.object(agent, "_parse_intent") as mock_parse, \
             patch.object(agent, "_execute_tool") as mock_execute:

            mock_parse.return_value = Intent(
                type=IntentType.SIMPLE_ACTION,
                confidence=0.9,
                reasoning="Format code request",
                suggested_tool="format_code",
                parameters={"project_dir": "./src"}
            )
            mock_execute.return_value = {
                "success": True,
                "output": "Code formatted successfully"
            }

            response = await agent.chat("Format code in ./src")

            assert "success" in response.lower()
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_chat(self, agent):
        """Test chat handles errors gracefully"""
        with patch.object(agent, "_parse_intent") as mock_parse:
            mock_parse.side_effect = Exception("Unexpected error")

            response = await agent.chat("Test message")

            assert "error" in response.lower()
            assert len(agent.conversation_history) == 2


# ══════════════════════════════════════════════════════════════════════
# Task Management Tests
# ══════════════════════════════════════════════════════════════════════


class TestTaskManagement:
    """Test task creation and tracking"""

    @pytest.mark.asyncio
    async def test_complex_task_creation(self, agent):
        """Test complex tasks are created and tracked"""
        with patch.object(agent, "_parse_intent") as mock_parse, \
             patch.object(agent, "_create_execution_plan") as mock_plan:

            mock_parse.return_value = Intent(
                type=IntentType.COMPLEX_TASK,
                confidence=0.85,
                reasoning="Multi-step task",
                complexity="medium",
                estimated_time_seconds=300
            )
            mock_plan.return_value = {
                "summary": "Build website",
                "steps": [
                    {
                        "step_number": 1,
                        "description": "Create structure",
                        "type": "code_gen",
                        "estimated_seconds": 60
                    }
                ],
                "total_estimated_seconds": 60
            }

            response = await agent.chat("Build a website")

            assert "Plan:" in response or "plan" in response.lower()
            assert "Task ID:" in response or "task" in response.lower()
            assert len(agent.active_tasks) == 1

    def test_get_active_tasks(self, agent):
        """Test getting list of active tasks"""
        # Create mock active task
        task = TaskExecution(
            task_id="task_123",
            description="Test task",
            status="executing",
            steps=[{"step": 1}, {"step": 2}],
            current_step=1
        )
        agent.active_tasks["task_123"] = task

        active = agent.get_active_tasks()

        assert len(active) == 1
        assert active[0]["task_id"] == "task_123"
        assert active[0]["status"] == "executing"
        assert active[0]["progress"] == "1/2"

    def test_get_task_status(self, agent):
        """Test getting specific task status"""
        task = TaskExecution(
            task_id="task_456",
            description="Another task",
            status="completed",
            steps=[{"step": 1}],
            current_step=1
        )
        agent.active_tasks["task_456"] = task

        status = agent.get_task_status("task_456")

        assert status is not None
        assert status["task_id"] == "task_456"
        assert status["status"] == "completed"
        assert status["total_steps"] == 1

    def test_get_nonexistent_task(self, agent):
        """Test getting status of nonexistent task"""
        status = agent.get_task_status("nonexistent")
        assert status is None


# ══════════════════════════════════════════════════════════════════════
# Parameter Handling Tests
# ══════════════════════════════════════════════════════════════════════


class TestParameterHandling:
    """Test parameter extraction and validation"""

    def test_check_missing_parameters(self, agent):
        """Test missing parameter detection"""
        schema = {
            "required": ["project_dir", "formatter"],
            "properties": {
                "project_dir": {"type": "string"},
                "formatter": {"type": "string"}
            }
        }
        provided = {"project_dir": "./src"}

        missing = agent._check_missing_parameters(schema, provided)

        assert "formatter" in missing
        assert len(missing) == 1

    def test_no_missing_parameters(self, agent):
        """Test when all parameters provided"""
        schema = {
            "required": ["project_dir"],
            "properties": {
                "project_dir": {"type": "string"}
            }
        }
        provided = {"project_dir": "./src"}

        missing = agent._check_missing_parameters(schema, provided)

        assert len(missing) == 0

    def test_ask_for_parameters(self, agent):
        """Test parameter request message"""
        message = agent._ask_for_parameters("format_code", ["project_dir", "formatter"])

        assert "format_code" in message
        assert "project_dir" in message
        assert "formatter" in message


# ══════════════════════════════════════════════════════════════════════
# Helper Method Tests
# ══════════════════════════════════════════════════════════════════════


class TestHelperMethods:
    """Test utility and helper methods"""

    def test_build_conversation_context(self, agent):
        """Test conversation context building"""
        agent._add_message("user", "Hello")
        agent._add_message("assistant", "Hi there!")
        agent._add_message("user", "How are you?")

        context = agent._build_conversation_context(last_n=2)

        assert "Hi there!" in context
        assert "How are you?" in context
        assert "Hello" not in context  # Should be excluded (more than 2 messages ago)

    def test_build_empty_context(self, agent):
        """Test context building with no history"""
        context = agent._build_conversation_context(last_n=5)
        assert "No previous conversation" in context

    def test_get_tool_summary(self, agent):
        """Test tool summary generation"""
        summary = agent._get_tool_summary()

        assert isinstance(summary, list)
        assert len(summary) > 0
        assert all("name" in tool and "description" in tool for tool in summary)

    def test_format_plan(self, agent):
        """Test execution plan formatting"""
        plan = {
            "summary": "Test task",
            "steps": [
                {
                    "step_number": 1,
                    "description": "First step",
                    "estimated_seconds": 30
                },
                {
                    "step_number": 2,
                    "description": "Second step",
                    "estimated_seconds": 60
                }
            ]
        }

        formatted = agent._format_plan(plan)

        assert "Test task" in formatted
        assert "First step" in formatted
        assert "Second step" in formatted
        assert "30s" in formatted
        assert "60s" in formatted

    def test_format_success_response(self, agent):
        """Test success response formatting"""
        result = {
            "success": True,
            "output": "Operation completed"
        }

        response = agent._format_success_response("format_code", result)

        assert "format_code" in response.lower()
        assert "success" in response.lower()
        assert "Operation completed" in response


# ══════════════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════════════


class TestIntegration:
    """Integration tests for end-to-end flows"""

    @pytest.mark.asyncio
    async def test_full_conversation_flow(self, agent):
        """Test complete conversation flow"""
        with patch("conversational_agent.chat_json") as mock_chat_json, \
             patch("conversational_agent.chat") as mock_chat:

            # First message: greeting
            mock_chat_json.return_value = {
                "type": "conversation",
                "confidence": 0.95,
                "reasoning": "Greeting"
            }
            response1 = await agent.chat("Hello!")
            assert len(agent.conversation_history) == 2

            # Second message: question
            mock_chat_json.return_value = {
                "type": "question",
                "confidence": 0.9,
                "reasoning": "Information request"
            }
            mock_chat.return_value = "We have format_code and run_tests."
            response2 = await agent.chat("What tools are available?")
            assert len(agent.conversation_history) == 4

            # Verify context is maintained
            context = agent._build_conversation_context(last_n=10)
            assert "Hello!" in context
            assert "What tools are available?" in context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
