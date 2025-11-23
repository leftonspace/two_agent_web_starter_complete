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

    # Maximum sizes to prevent unbounded memory growth
    MAX_CONVERSATION_HISTORY = 100
    MAX_AGENT_MESSAGES = 50
    MAX_ACTIVE_TASKS = 20

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
        # PHASE 7.2: Subscribe to agent messages from Manager/Supervisor/Employee
        self.message_bus = get_message_bus()
        self.message_bus.subscribe(self._handle_agent_message)
        self.pending_agent_messages: List[AgentMessage] = []
        self.agent_message_queue: List[AgentMessage] = []  # Queue for streaming to web UI

        # PHASE 7.3: Initialize business memory for persistent learning
        memory_config = self.config.memory if hasattr(self.config, 'memory') else None
        self.business_memory = BusinessMemory(
            db_path=memory_config.memory_db_path if memory_config else "data/business_memory.db",
            auto_learn=memory_config.auto_learn if memory_config else True
        )

        core_logging.log_event("conversational_agent_initialized", {
            "session_id": self.session_id,
            "available_tools": len(self.available_tools),
            "agent_messaging_enabled": True,
            "business_memory_enabled": True
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
        Main conversational interface with business memory.

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
            # PHASE 7.3: Get relevant context from business memory
            memory_context = await self.business_memory.get_context_for_query(user_message)

            # Step 1: Parse intent with memory context
            intent = await self._parse_intent(user_message, memory_context)

            # Step 2: Route based on intent type
            if intent.type == IntentType.SIMPLE_ACTION:
                response = await self._handle_simple_action(intent, user_message, memory_context)
            elif intent.type == IntentType.COMPLEX_TASK:
                response = await self._handle_complex_task(intent, user_message, memory_context)
            elif intent.type == IntentType.QUESTION:
                response = await self._handle_question(user_message, memory_context)
            elif intent.type == IntentType.CLARIFICATION:
                response = await self._handle_clarification(intent)
            elif intent.type == IntentType.CONVERSATION:
                response = await self._handle_conversation(user_message)
            else:
                response = "I'm not sure how to help with that. Could you rephrase?"

            # Add assistant response to history
            self._add_message("assistant", response)

            # PHASE 7.3: Learn from this conversation
            await self.business_memory.learn_from_conversation(
                user_message,
                self._get_recent_messages_for_learning()
            )

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

    async def _parse_intent(self, message: str, memory_context: Optional[Dict[str, Any]] = None) -> Intent:
        """Use LLM to understand user intent with business memory context"""
        context = self._build_conversation_context(last_n=5)

        # PHASE 7.3: Add business memory context if available
        memory_info = ""
        if memory_context:
            memory_info = f"""
BUSINESS CONTEXT (from memory):
{json.dumps(memory_context, indent=2)}
"""

        prompt = f"""Analyze user request to determine intent and plan execution.

CONVERSATION CONTEXT:
{context}

{memory_info}
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
    async def _handle_simple_action(self, intent: Intent, user_message: str, memory_context: Optional[Dict[str, Any]] = None) -> str:
        """Handle simple actions with single tool call"""
        tool_name = intent.suggested_tool

        if not tool_name:
            return "I'm not sure which tool to use. Could you be more specific?"

        # Get tool schema
        tool_schema = self.tool_schemas.get(tool_name)
        if not tool_schema:
            return f"Tool '{tool_name}' not found."

        # Extract parameters if not provided
        # Extract parameters if not provided (with memory context)
        if not intent.parameters:
            intent.parameters = await self._extract_parameters(
                tool_name,
                tool_schema,
                user_message
                user_message,
                memory_context
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
    async def _handle_complex_task(self, intent: Intent, user_message: str, memory_context: Optional[Dict[str, Any]] = None) -> str:
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

{memory_info}
USER QUESTION: {user_message}

Answer clearly and concisely. Keep under 200 words unless more detail needed.
If asked about System-1.2 capabilities, mention:
- Multi-agent orchestration (manager, supervisor, employee loops)
- Tool execution (format code, run tests, git operations)
- Web dashboard and CLI interfaces
- Conversational interface (this chat!)"""
- Conversational interface (this chat!)

Use the business context if relevant to answer the question accurately."""

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
            return (
    "Hello! I'm the System-1.2 conversational agent. "
    "I can help you run coding tasks, manage jobs, explore projects, "
    "and tune your AI workflows."
)


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

        message: str,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Use LLM to extract parameter values from message with business memory"""
        context = self._build_conversation_context(last_n=3)

        # PHASE 7.3: Add business memory context
        memory_info = ""
        if memory_context:
            memory_info = f"""
BUSINESS CONTEXT (from memory):
{json.dumps(memory_context, indent=2)}
"""

        prompt = f"""Extract parameters for tool '{tool_name}' from user message.

TOOL SCHEMA:
{json.dumps(schema, indent=2)}

CONVERSATION CONTEXT:
{context}

{memory_info}
USER MESSAGE: "{message}"

Extract parameter values and return JSON matching the schema.
For missing optional parameters, omit them or use null.
For missing required parameters, use null (we'll ask user later).
Use business context to fill in parameters where possible (e.g., team member emails, company info).

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
        intent: Intent,
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create multi-step execution plan for complex task with business memory"""
        # PHASE 7.3: Add business memory context
        memory_info = ""
        if memory_context:
            memory_info = f"""
BUSINESS CONTEXT (from memory):
{json.dumps(memory_context, indent=2)}
"""

        prompt = f"""Create detailed execution plan for task: "{task_description}"

AVAILABLE TOOLS:
{json.dumps(self._get_tool_summary(), indent=2)}

{memory_info}
Break task into concrete steps. Each step should be either:
- tool_call: Execute a specific tool
- code_gen: Generate code/files
- validation: Check results

Use business context to inform the plan (e.g., know who to email, what tools to use).

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
    def _add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now()
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.conversation_history.append(message)

        # Prune conversation history to prevent unbounded growth
        if len(self.conversation_history) > self.MAX_CONVERSATION_HISTORY:
            self.conversation_history = self.conversation_history[-self.MAX_CONVERSATION_HISTORY:]

    def _build_conversation_context(self, last_n: int = 5) -> str:
        """Build conversation context from recent messages"""
        recent = self.conversation_history[-last_n:] if last_n > 0 else self.conversation_history

        if not recent:
            return "(No previous conversation)"

        lines = []
        for msg in recent:
            lines.append(f"{msg.role.upper()}: {msg.content}")

        return "\n".join(lines)

    def _get_recent_messages_for_learning(self, last_n: int = 5) -> List[Dict[str, str]]:
        """
        Get recent messages formatted for business memory learning.

        PHASE 7.3: Provides conversation context to fact extractor.

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        recent = self.conversation_history[-last_n:] if last_n > 0 else self.conversation_history

        return [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in recent
        ]

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
    # PHASE 7.3: Business Memory Management
    # ══════════════════════════════════════════════════════════════════════

    def get_business_facts(self) -> Dict[str, Any]:
        """
        Get summary of all stored business facts.

        Returns:
            Dictionary with company, team, preferences, and fact count
        """
        return self.business_memory.get_all_facts()

    def get_team_members(self) -> List[Dict[str, Any]]:
        """Get all stored team members"""
        return self.business_memory.get_team_members()

    def get_preferences(self) -> Dict[str, Any]:
        """Get all stored preferences"""
        return self.business_memory.get_preferences()

    def get_company_info(self) -> Dict[str, Any]:
        """Get stored company information"""
        return self.business_memory.get_company_info()

    async def remember_fact(self, fact_text: str):
        """
        Manually store a fact (user said "remember that...").

        Args:
            fact_text: Fact to remember
        """
        await self.business_memory.store_manual_fact(fact_text)
        core_logging.log_event("manual_fact_stored", {"fact_preview": fact_text[:100]})

    def forget_about(self, topic: str) -> int:
        """
        Delete facts about a topic.

        Args:
            topic: Topic to forget about

        Returns:
            Number of facts deleted
        """
        count = self.business_memory.delete_facts_about(topic)
        core_logging.log_event("facts_deleted", {"topic": topic, "count": count})
        return count

    def export_business_data(self, format: str = "json") -> str:
        """
        Export all business memory data (GDPR compliance).

        Args:
            format: Export format ("json" or "csv")

        Returns:
            Exported data as string
        """
        return self.business_memory.export_data(format)

    def clear_business_memory(self):
        """Clear all stored business memory (GDPR right to be forgotten)"""
        self.business_memory.clear_all()
        core_logging.log_event("business_memory_cleared", {"session_id": self.session_id})

    # ══════════════════════════════════════════════════════════════════════
    # PHASE 7.2: Agent Message Handling
    # ══════════════════════════════════════════════════════════════════════

    async def _handle_agent_message(self, message: AgentMessage):
        """
        Handle messages from Manager/Supervisor/Employee.

        Stream to chat interface and store for display.

        Args:
            message: AgentMessage from the message bus
        """
        # Format message with agent role and emoji
        role_emoji = {
            AgentRole.MANAGER: "👔",
            AgentRole.SUPERVISOR: "🔍",
            AgentRole.EMPLOYEE: "🛠️",
            AgentRole.SYSTEM: "⚙️"
        }

        emoji = role_emoji.get(message.role, "🤖")
        formatted = f"{emoji} {message.role.value.title()}: {message.content}"

        # Add to conversation history
        self._add_message(
            "assistant",
            formatted,
            metadata={
                "agent_role": message.role.value,
                "agent_message": True,
                "message_id": message.message_id,
                "requires_response": message.requires_response,
                **message.metadata
            }
        )

        # Add to queue for web UI streaming (with pruning)
        self.agent_message_queue.append(message)
        if len(self.agent_message_queue) > self.MAX_AGENT_MESSAGES:
            self.agent_message_queue = self.agent_message_queue[-self.MAX_AGENT_MESSAGES:]

        # If requires response, track it (with pruning)
        if message.requires_response:
            self.pending_agent_messages.append(message)
            if len(self.pending_agent_messages) > self.MAX_AGENT_MESSAGES:
                self.pending_agent_messages = self.pending_agent_messages[-self.MAX_AGENT_MESSAGES:]

        # Log event
        core_logging.log_event("agent_message_received", {
            "role": message.role.value,
            "content_preview": message.content[:100],
            "requires_response": message.requires_response
        })

    def get_agent_messages(self, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get agent messages for streaming to web UI.

        Args:
            since_id: Only return messages after this ID (optional)

        Returns:
            List of message dicts
        """
        messages = []

        if since_id:
            # Find index of since_id
            found_index = None
            for idx, msg in enumerate(self.agent_message_queue):
                if msg.message_id == since_id:
                    found_index = idx
                    break

            # Return messages after that index
            if found_index is not None:
                messages = self.agent_message_queue[found_index + 1:]
            else:
                messages = self.agent_message_queue
        else:
            messages = self.agent_message_queue

        return [msg.to_dict() for msg in messages]

    def get_pending_agent_responses(self) -> List[Dict[str, Any]]:
        """
        Get list of agent messages waiting for user response.

        Returns:
            List of pending message dicts
        """
        return [msg.to_dict() for msg in self.pending_agent_messages]

    def respond_to_agent(self, message_id: str, response: str) -> bool:
        """
        Provide user response to an agent's question.

        Args:
            message_id: ID of message to respond to
            response: User's response text

        Returns:
            True if response was delivered
        """
        success = self.message_bus.provide_response(message_id, response)

        if success:
            # Remove from pending list
            self.pending_agent_messages = [
                msg for msg in self.pending_agent_messages
                if msg.message_id != message_id
            ]

            # Log response
            core_logging.log_event("agent_response_provided", {
                "message_id": message_id,
                "response_preview": response[:100]
            })

        return success


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
