"""
Conversational Agent for System-1.2

PHASE 7.1: Provides natural language interface to the orchestration system.
Users can chat with the agent to execute tasks, ask questions,
and build complex systems without writing mission files.

Architecture:
    User Input → Intent Parser → Task Planner → Executor → Response

Usage:
    agent = ConversationalAgent()
    response = await agent.chat("Send an email to john@example.com")
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import core_logging
from config import Config, get_config
from exec_tools import get_tool_metadata
from llm import chat, chat_json


# ══════════════════════════════════════════════════════════════════════
# Enums and Dataclasses
# ══════════════════════════════════════════════════════════════════════


class IntentType(Enum):
    """Types of user intents"""
    SIMPLE_ACTION = "simple_action"  # Single tool call
    COMPLEX_TASK = "complex_task"  # Multi-step task
    QUESTION = "question"  # Answer question
    CLARIFICATION = "clarification"  # Need more info
    CONVERSATION = "conversation"  # Casual chat


@dataclass
class Intent:
    """Parsed user intent"""
    type: IntentType
    confidence: float  # 0.0 - 1.0
    reasoning: str
    suggested_tool: Optional[str] = None
    complexity: Optional[str] = None  # low, medium, high
    parameters: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    estimated_time_seconds: Optional[int] = None


@dataclass
class ConversationMessage:
    """Single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecution:
    """Track execution of a task"""
    task_id: str
    description: str
    status: str  # 'planning', 'executing', 'completed', 'failed'
    steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════
# Main Conversational Agent Class
# ══════════════════════════════════════════════════════════════════════


class ConversationalAgent:
    """
    Main conversational agent class.

    Handles natural language interaction, intent parsing,
    task planning, and autonomous execution.
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize conversational agent"""
        self.config = config or get_config()
        self.conversation_history: List[ConversationMessage] = []
        self.active_tasks: Dict[str, TaskExecution] = {}
        self.session_id = self._generate_session_id()

        # Load tool metadata for intent parsing
        self.available_tools = self._load_available_tools()
        self.tool_schemas = self._load_tool_schemas()

        core_logging.log_event("conversational_agent_initialized", {
            "session_id": self.session_id,
            "available_tools": len(self.available_tools)
        })

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{uuid.uuid4().hex[:12]}"

    def _generate_task_id(self) -> str:
        """Generate unique task ID"""
        return f"task_{uuid.uuid4().hex[:12]}"

    def _load_available_tools(self) -> List[str]:
        """Load list of available tools from tool registry"""
        try:
            metadata = get_tool_metadata()
            return list(metadata.keys())
        except Exception as e:
            core_logging.log_event("tool_loading_error", {"error": str(e)})
            # Return basic tools as fallback
            return ["format_code", "run_tests", "git_diff", "git_status"]

    def _load_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load tool schemas from metadata"""
        try:
            metadata = get_tool_metadata()
            return {
                name: info.get("schema", {})
                for name, info in metadata.items()
            }
        except Exception as e:
            core_logging.log_event("schema_loading_error", {"error": str(e)})
            return {}

    # ══════════════════════════════════════════════════════════════════════
    # Main Chat Interface
    # ══════════════════════════════════════════════════════════════════════

    async def chat(self, user_message: str) -> str:
        """
        Main conversational interface.

        Args:
            user_message: Natural language input from user

        Returns:
            Agent's response as string
        """
        # Add user message to history
        self._add_message("user", user_message)

        try:
            # Step 1: Parse intent
            intent = await self._parse_intent(user_message)

            # Step 2: Route based on intent type
            if intent.type == IntentType.SIMPLE_ACTION:
                response = await self._handle_simple_action(intent, user_message)
            elif intent.type == IntentType.COMPLEX_TASK:
                response = await self._handle_complex_task(intent, user_message)
            elif intent.type == IntentType.QUESTION:
                response = await self._handle_question(user_message)
            elif intent.type == IntentType.CLARIFICATION:
                response = await self._handle_clarification(intent)
            elif intent.type == IntentType.CONVERSATION:
                response = await self._handle_conversation(user_message)
            else:
                response = "I'm not sure how to help with that. Could you rephrase?"

            # Add assistant response to history
            self._add_message("assistant", response)

            return response

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self._add_message("assistant", error_msg)
            core_logging.log_event("conversational_agent_error", {
                "error": str(e),
                "user_message": user_message
            })
            return error_msg

    # ══════════════════════════════════════════════════════════════════════
    # Intent Parsing
    # ══════════════════════════════════════════════════════════════════════

    async def _parse_intent(self, message: str) -> Intent:
        """Use LLM to understand user intent"""
        context = self._build_conversation_context(last_n=5)

        prompt = f"""Analyze user request to determine intent and plan execution.

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE: "{message}"

AVAILABLE TOOLS:
{json.dumps(self._get_tool_summary(), indent=2)}

Classify request as:
- simple_action: Single tool call (send email, query DB, format code, run tests)
- complex_task: Multi-step task (build website, create system, complex workflow)
- question: User asking for information or explanation
- clarification: Missing parameters or unclear request
- conversation: Casual chat, greeting, or off-topic

Return JSON:
{{
    "type": "simple_action|complex_task|question|clarification|conversation",
    "confidence": 0.0-1.0,
    "reasoning": "explain classification in 1-2 sentences",
    "suggested_tool": "tool_name" (if simple_action, else null),
    "complexity": "low|medium|high" (if complex_task, else null),
    "parameters": {{}},
    "requires_approval": true|false,
    "estimated_time_seconds": 30
}}"""

        try:
            response = chat_json(
                role="employee",
                system_prompt="",
                user_content=prompt,
                model="gpt-4o",
                temperature=0.1
            )

            intent = Intent(
                type=IntentType(response["type"]),
                confidence=response["confidence"],
                reasoning=response["reasoning"],
                suggested_tool=response.get("suggested_tool"),
                complexity=response.get("complexity"),
                parameters=response.get("parameters"),
                requires_approval=response.get("requires_approval", False),
                estimated_time_seconds=response.get("estimated_time_seconds")
            )

            core_logging.log_event("intent_parsed", {
                "type": intent.type.value,
                "confidence": intent.confidence,
                "tool": intent.suggested_tool
            })

            return intent

        except Exception as e:
            core_logging.log_event("intent_parsing_error", {"error": str(e)})
            # Fallback: assume it's a question
            return Intent(
                type=IntentType.QUESTION,
                confidence=0.5,
                reasoning="Intent parsing failed, defaulting to question"
            )

    # ══════════════════════════════════════════════════════════════════════
    # Intent Handlers
    # ══════════════════════════════════════════════════════════════════════

    async def _handle_simple_action(self, intent: Intent, user_message: str) -> str:
        """Handle simple actions with single tool call"""
        tool_name = intent.suggested_tool

        if not tool_name:
            return "I'm not sure which tool to use. Could you be more specific?"

        # Get tool schema
        tool_schema = self.tool_schemas.get(tool_name)
        if not tool_schema:
            return f"Tool '{tool_name}' not found."

        # Extract parameters if not provided
        if not intent.parameters:
            intent.parameters = await self._extract_parameters(
                tool_name,
                tool_schema,
                user_message
            )

        # Check for missing required parameters
        missing_params = self._check_missing_parameters(
            tool_schema,
            intent.parameters or {}
        )

        if missing_params:
            return self._ask_for_parameters(tool_name, missing_params)

        # Execute tool (simulated - actual execution would call exec_tools)
        try:
            result = self._execute_tool(tool_name, intent.parameters)

            if result.get("success"):
                core_logging.log_event("simple_action_executed", {
                    "tool": tool_name,
                    "parameters": intent.parameters
                })
                return self._format_success_response(tool_name, result)
            else:
                return f"Failed to execute {tool_name}: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    async def _handle_complex_task(self, intent: Intent, user_message: str) -> str:
        """Handle complex multi-step tasks"""
        # Create task execution tracker
        task = TaskExecution(
            task_id=self._generate_task_id(),
            description=user_message,
            status="planning"
        )
        self.active_tasks[task.task_id] = task

        # Generate execution plan
        plan = await self._create_execution_plan(user_message, intent)

        task.steps = plan["steps"]
        task.status = "executing"

        # Start async execution
        asyncio.create_task(self._execute_plan_async(task))

        # Return immediate response
        estimated_time = intent.estimated_time_seconds or len(plan["steps"]) * 30
        return f"""I understand! I'll {user_message.lower()}.

Plan:
{self._format_plan(plan)}

Estimated time: {estimated_time // 60} minutes

Task ID: {task.task_id}
I'll work on this and update you. You can continue chatting or ask for status with '/task {task.task_id}'."""

    async def _handle_question(self, user_message: str) -> str:
        """Answer user questions"""
        context = self._build_conversation_context(last_n=10)

        prompt = f"""You are a helpful AI assistant for System-1.2, a multi-agent orchestration platform.

CONVERSATION HISTORY:
{context}

USER QUESTION: {user_message}

Answer clearly and concisely. Keep under 200 words unless more detail needed.
If asked about System-1.2 capabilities, mention:
- Multi-agent orchestration (manager, supervisor, employee loops)
- Tool execution (format code, run tests, git operations)
- Web dashboard and CLI interfaces
- Conversational interface (this chat!)"""

        try:
            response = chat(
                role="employee",
                system_prompt="",
                user_content=prompt,
                model="gpt-4o",
                temperature=0.7
            )
            return response
        except Exception as e:
            return f"I had trouble processing that question: {str(e)}"

    async def _handle_clarification(self, intent: Intent) -> str:
        """Handle requests needing clarification"""
        return f"I need more information. {intent.reasoning}"

    async def _handle_conversation(self, user_message: str) -> str:
        """Handle casual conversation"""
        greetings = ["hello", "hi", "hey", "greetings"]
        farewells = ["bye", "goodbye", "see you", "farewell"]

        msg_lower = user_message.lower()

        if any(g in msg_lower for g in greetings):
            return """Hello! I'm the System-1.2 conversational agent. I can help you:
- Execute tasks (format code, run tests, git operations)
- Build complex systems
- Answer questions about the platform
- Automate workflows

What would you like to do?"""

        elif any(f in msg_lower for f in farewells):
            return "Goodbye! Feel free to return anytime you need assistance."

        else:
            # General conversational response
            return "I'm here to help with tasks and questions about System-1.2. What can I do for you?"

    # ══════════════════════════════════════════════════════════════════════
    # Parameter Extraction and Validation
    # ══════════════════════════════════════════════════════════════════════

    async def _extract_parameters(
        self,
        tool_name: str,
        schema: Dict[str, Any],
        message: str
    ) -> Dict[str, Any]:
        """Use LLM to extract parameter values from message"""
        context = self._build_conversation_context(last_n=3)

        prompt = f"""Extract parameters for tool '{tool_name}' from user message.

TOOL SCHEMA:
{json.dumps(schema, indent=2)}

CONVERSATION CONTEXT:
{context}

USER MESSAGE: "{message}"

Extract parameter values and return JSON matching the schema.
For missing optional parameters, omit them or use null.
For missing required parameters, use null (we'll ask user later).

Return only the parameters JSON object."""

        try:
            response = chat_json(
                role="employee",
                system_prompt="",
                user_content=prompt,
                model="gpt-4o",
                temperature=0.1
            )
            return response
        except Exception as e:
            core_logging.log_event("parameter_extraction_error", {"error": str(e)})
            return {}

    def _check_missing_parameters(
        self,
        schema: Dict[str, Any],
        provided: Dict[str, Any]
    ) -> List[str]:
        """Check for missing required parameters"""
        required = schema.get("required", [])
        missing = []

        for param in required:
            if param not in provided or provided[param] is None:
                missing.append(param)

        return missing

    def _ask_for_parameters(self, tool_name: str, missing: List[str]) -> str:
        """Generate message asking for missing parameters"""
        params_str = ", ".join(missing)
        return f"To execute '{tool_name}', I need: {params_str}. Could you provide these?"

    # ══════════════════════════════════════════════════════════════════════
    # Task Planning and Execution
    # ══════════════════════════════════════════════════════════════════════

    async def _create_execution_plan(
        self,
        task_description: str,
        intent: Intent
    ) -> Dict[str, Any]:
        """Create multi-step execution plan for complex task"""
        prompt = f"""Create detailed execution plan for task: "{task_description}"

AVAILABLE TOOLS:
{json.dumps(self._get_tool_summary(), indent=2)}

Break task into concrete steps. Each step should be either:
- tool_call: Execute a specific tool
- code_gen: Generate code/files
- validation: Check results

Return JSON:
{{
    "summary": "brief task summary",
    "steps": [
        {{
            "step_number": 1,
            "description": "what this step does",
            "type": "tool_call|code_gen|validation",
            "tool": "tool_name" (if tool_call),
            "estimated_seconds": 30
        }}
    ],
    "total_estimated_seconds": 300
}}"""

        try:
            response = chat_json(
                role="employee",
                system_prompt="",
                user_content=prompt,
                model="gpt-4o",
                temperature=0.2
            )
            return response
        except Exception as e:
            core_logging.log_event("plan_creation_error", {"error": str(e)})
            # Return simple plan as fallback
            return {
                "summary": task_description,
                "steps": [
                    {
                        "step_number": 1,
                        "description": task_description,
                        "type": "code_gen",
                        "estimated_seconds": 60
                    }
                ],
                "total_estimated_seconds": 60
            }

    async def _execute_plan_async(self, task: TaskExecution):
        """Execute task plan asynchronously in background"""
        try:
            for step_idx, step in enumerate(task.steps):
                task.current_step = step_idx + 1

                # Simulate step execution
                await asyncio.sleep(1)

                # Log progress
                core_logging.log_event("task_step_completed", {
                    "task_id": task.task_id,
                    "step": step_idx + 1,
                    "total": len(task.steps)
                })

            # Mark task complete
            task.status = "completed"
            task.completed_at = datetime.now()
            task.result = {"status": "success", "message": "Task completed"}

            core_logging.log_event("task_completed", {
                "task_id": task.task_id,
                "duration_seconds": (task.completed_at - task.started_at).total_seconds()
            })

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()

            core_logging.log_event("task_failed", {
                "task_id": task.task_id,
                "error": str(e)
            })

    def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        # Simulated tool execution
        # In production, this would call exec_tools.execute_tool()
        core_logging.log_event("tool_executed", {
            "tool": tool_name,
            "parameters": parameters
        })

        # Return mock success
        return {
            "success": True,
            "output": f"Executed {tool_name} successfully",
            "exit_code": 0
        }

    # ══════════════════════════════════════════════════════════════════════
    # Helper Methods
    # ══════════════════════════════════════════════════════════════════════

    def _add_message(self, role: str, content: str):
        """Add message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        self.conversation_history.append(message)

    def _build_conversation_context(self, last_n: int = 5) -> str:
        """Build conversation context from recent messages"""
        recent = self.conversation_history[-last_n:] if last_n > 0 else self.conversation_history

        if not recent:
            return "(No previous conversation)"

        lines = []
        for msg in recent:
            lines.append(f"{msg.role.upper()}: {msg.content}")

        return "\n".join(lines)

    def _get_tool_summary(self) -> List[Dict[str, str]]:
        """Get summary of available tools for prompts"""
        try:
            metadata = get_tool_metadata()
            summary = []
            for name, info in metadata.items():
                summary.append({
                    "name": name,
                    "description": info.get("description", "No description")
                })
            return summary
        except Exception:
            # Fallback summary
            return [
                {"name": "format_code", "description": "Format source code with ruff/black"},
                {"name": "run_tests", "description": "Run pytest test suite"},
                {"name": "git_diff", "description": "Show git diff"},
                {"name": "git_status", "description": "Show git status"}
            ]

    def _format_plan(self, plan: Dict[str, Any]) -> str:
        """Format execution plan for display"""
        lines = [f"Summary: {plan['summary']}", ""]
        for step in plan["steps"]:
            lines.append(
                f"{step['step_number']}. {step['description']} "
                f"({step.get('estimated_seconds', 30)}s)"
            )
        return "\n".join(lines)

    def _format_success_response(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format successful tool execution response"""
        output = result.get("output", "")
        if output:
            return f"Executed {tool_name} successfully:\n{output}"
        else:
            return f"Executed {tool_name} successfully."

    # ══════════════════════════════════════════════════════════════════════
    # Public API for Status Queries
    # ══════════════════════════════════════════════════════════════════════

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get list of active tasks"""
        tasks = []
        for task_id, task in self.active_tasks.items():
            if task.status in ["planning", "executing"]:
                progress = f"{task.current_step}/{len(task.steps)}"
                tasks.append({
                    "task_id": task_id,
                    "description": task.description,
                    "status": task.status,
                    "progress": progress
                })
        return tasks

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a specific task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task_id,
            "description": task.description,
            "status": task.status,
            "current_step": task.current_step,
            "total_steps": len(task.steps),
            "started_at": task.started_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }

    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        core_logging.log_event("conversation_cleared", {"session_id": self.session_id})


# ══════════════════════════════════════════════════════════════════════
# Module Exports
# ══════════════════════════════════════════════════════════════════════

__all__ = [
    "ConversationalAgent",
    "Intent",
    "IntentType",
    "ConversationMessage",
    "TaskExecution",
]
