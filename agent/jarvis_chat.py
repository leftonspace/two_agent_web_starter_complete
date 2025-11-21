"""
Jarvis Conversational Interface

Intelligent chat interface that routes requests to appropriate handlers:
- Simple queries → Direct LLM response
- Complex tasks → Multi-agent orchestrator
- File operations → Targeted file edits
"""

import asyncio
import json
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

# Import existing components
try:
    from memory.session_manager import SessionManager
    from memory.vector_store import VectorMemoryStore, MemoryType
    from memory.context_retriever import ContextRetriever
except ImportError:
    SessionManager = None
    VectorMemoryStore = None
    ContextRetriever = None

# Import orchestrator
try:
    from orchestrator import main as orchestrator_main
    from orchestrator_context import OrchestratorContext
except ImportError:
    orchestrator_main = None
    OrchestratorContext = None

# Import existing LLM infrastructure
try:
    from llm import chat as llm_chat
except ImportError:
    llm_chat = None


class IntentType(Enum):
    """Types of user intents"""
    SIMPLE_QUERY = "simple_query"          # Questions, explanations
    COMPLEX_TASK = "complex_task"          # Build, create projects
    FILE_OPERATION = "file_operation"      # Edit, fix specific files
    CONVERSATION = "conversation"          # Casual chat


@dataclass
class Intent:
    """User intent analysis result"""
    type: IntentType
    confidence: float
    reasoning: str
    requires_orchestrator: bool
    target_files: List[str] = None
    project_name: Optional[str] = None

    @staticmethod
    def from_json(data: Dict) -> 'Intent':
        """Parse intent from JSON"""
        return Intent(
            type=IntentType(data.get("type", "simple_query")),
            confidence=data.get("confidence", 0.5),
            reasoning=data.get("reasoning", ""),
            requires_orchestrator=data.get("requires_orchestrator", False),
            target_files=data.get("target_files", []),
            project_name=data.get("project_name")
        )


@dataclass
class ChatMessage:
    """Chat message structure"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }


class JarvisChat:
    """
    Conversational interface with intelligent routing.

    Routes user messages to:
    1. Direct LLM (simple queries)
    2. Multi-agent orchestrator (complex tasks)
    3. File operation tools (targeted edits)
    """

    def __init__(
        self,
        memory_enabled: bool = True
    ):
        """Initialize Jarvis chat"""
        self.memory_enabled = memory_enabled

        # Initialize memory components if available
        if memory_enabled and SessionManager:
            try:
                self.session_manager = SessionManager(
                    VectorMemoryStore(persist_directory="data/chat_memory")
                )
                self.vector_store = VectorMemoryStore(persist_directory="data/chat_memory")
                self.context_retriever = ContextRetriever(self.vector_store)
            except Exception as e:
                print(f"[Jarvis] Memory initialization failed: {e}")
                self.memory_enabled = False
        else:
            self.memory_enabled = False

        # Use existing LLM infrastructure
        self.llm_available = llm_chat is not None

        # Conversation state
        self.current_session = None
        self.conversation_history: List[ChatMessage] = []

    async def start_session(self, user_id: str = "default_user") -> str:
        """Start a new conversation session"""
        if self.memory_enabled:
            try:
                session = await self.session_manager.start_session(user=user_id)
                self.current_session = session
                return session.id
            except Exception as e:
                print(f"[Jarvis] Session start failed: {e}")

        # Fallback: create simple session ID
        session_id = f"session_{int(time.time())}"
        self.current_session = {"id": session_id, "user": user_id}
        return session_id

    async def handle_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for handling user messages.

        Args:
            user_message: User's message
            context: Optional context (files, project path, etc.)

        Returns:
            Response dictionary with content and metadata
        """
        try:
            # Store user message
            user_msg = ChatMessage(
                role="user",
                content=user_message,
                timestamp=time.time(),
                metadata=context
            )
            self.conversation_history.append(user_msg)

            # Analyze intent
            intent = await self.analyze_intent(user_message, context or {})

            print(f"[Jarvis] Intent: {intent.type.value} (confidence: {intent.confidence:.2f})")
            print(f"[Jarvis] Reasoning: {intent.reasoning}")

            # Route to appropriate handler
            if intent.type == IntentType.SIMPLE_QUERY:
                response = await self.handle_simple_query(user_message, context)

            elif intent.type == IntentType.COMPLEX_TASK:
                response = await self.handle_complex_task(user_message, context, intent)

            elif intent.type == IntentType.FILE_OPERATION:
                response = await self.handle_file_operation(user_message, context, intent)

            else:  # CONVERSATION
                response = await self.handle_conversation(user_message, context)

            # Store assistant response
            assistant_msg = ChatMessage(
                role="assistant",
                content=response["content"],
                timestamp=time.time(),
                metadata=response.get("metadata", {})
            )
            self.conversation_history.append(assistant_msg)

            # Store in memory
            if self.memory_enabled:
                await self.store_interaction(user_message, response["content"])

            return response

        except Exception as e:
            print(f"[Jarvis] Error handling message: {e}")
            import traceback
            traceback.print_exc()

            return {
                "content": f"I apologize, but I encountered an error: {str(e)}",
                "metadata": {"error": True, "error_message": str(e)}
            }

    async def analyze_intent(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Intent:
        """
        Analyze user intent to determine routing.

        Uses LLM to classify the request type.
        """
        if not self.llm_available:
            # Fallback: simple heuristics
            return self._fallback_intent_analysis(message)

        try:
            # Build context for analysis
            history_context = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in self.conversation_history[-5:]  # Last 5 messages
            ])

            prompt = f"""Analyze this user request and determine how to handle it.

Recent conversation:
{history_context}

User's new message: {message}

Context: {json.dumps(context, indent=2) if context else "None"}

Classify as one of:
1. "simple_query" - Questions, explanations, info lookup, definitions
   Examples: "What is Python?", "Explain recursion", "How do I use async?"

2. "complex_task" - Building projects, creating applications, multi-step work
   Examples: "Build a website", "Create a REST API", "Make a game"

3. "file_operation" - Editing, fixing, updating specific files
   Examples: "Fix bug in login.js", "Update header color", "Add error handling"

4. "conversation" - Casual chat, greetings, unclear requests
   Examples: "Hello", "Thanks!", "Can you help?"

Consider:
- Complexity: Single answer vs multi-step process?
- Scope: Conceptual question vs concrete file work?
- Specificity: Vague vs specific files/project mentioned?

Return ONLY valid JSON (no markdown):
{{
  "type": "simple_query|complex_task|file_operation|conversation",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation",
  "requires_orchestrator": true|false,
  "target_files": ["file1.py", "file2.js"],
  "project_name": "optional_project_name"
}}"""

            # Use existing LLM infrastructure
            result_text = await asyncio.to_thread(
                llm_chat,
                role="employee",
                system_prompt="You are a task classification assistant. Return valid JSON only.",
                user_content=prompt,
                temperature=0.3
            )

            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result_json = json.loads(result_text.strip())
            return Intent.from_json(result_json)

        except Exception as e:
            print(f"[Jarvis] Intent analysis error: {e}")
            return self._fallback_intent_analysis(message)

    def _fallback_intent_analysis(self, message: str) -> Intent:
        """Fallback intent analysis using heuristics"""
        message_lower = message.lower()

        # Complex task keywords
        complex_keywords = [
            "build", "create", "make", "develop", "implement",
            "website", "app", "application", "api", "system"
        ]

        # File operation keywords
        file_keywords = [
            "fix", "update", "change", "modify", "edit",
            "bug", ".py", ".js", ".css", ".html", "line"
        ]

        if any(kw in message_lower for kw in complex_keywords):
            return Intent(
                type=IntentType.COMPLEX_TASK,
                confidence=0.7,
                reasoning="Detected build/create keywords",
                requires_orchestrator=True
            )

        if any(kw in message_lower for kw in file_keywords):
            return Intent(
                type=IntentType.FILE_OPERATION,
                confidence=0.7,
                reasoning="Detected file operation keywords",
                requires_orchestrator=False
            )

        # Default to simple query
        return Intent(
            type=IntentType.SIMPLE_QUERY,
            confidence=0.6,
            reasoning="Default classification",
            requires_orchestrator=False
        )

    async def handle_simple_query(
        self,
        message: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Handle simple questions - direct LLM response"""
        if not self.llm_available:
            return {
                "content": "I apologize, but I cannot process queries without an LLM client configured.",
                "metadata": {"error": True}
            }

        try:
            # Build conversation context
            history_text = ""
            for msg in self.conversation_history[-10:]:
                history_text += f"{msg.role}: {msg.content}\n"

            full_prompt = f"""Previous conversation:
{history_text}

User: {message}

Jarvis:"""

            # Use existing LLM infrastructure
            response_text = await asyncio.to_thread(
                llm_chat,
                role="employee",
                system_prompt="You are Jarvis, a helpful AI assistant. Answer questions clearly and concisely.",
                user_content=full_prompt,
                temperature=0.7
            )

            return {
                "content": response_text,
                "metadata": {
                    "type": "simple_query"
                }
            }

        except Exception as e:
            print(f"[Jarvis] Simple query error: {e}")
            return {
                "content": f"I encountered an error processing your question: {str(e)}",
                "metadata": {"error": True}
            }

    async def handle_complex_task(
        self,
        message: str,
        context: Optional[Dict],
        intent: Intent
    ) -> Dict[str, Any]:
        """Handle complex tasks - route to multi-agent orchestrator"""
        try:
            print("\n[Jarvis] 🚀 This is a complex task. Let me coordinate my team...")

            # Extract or generate project name
            project_name = intent.project_name or self._extract_project_name(message)
            project_path = Path("sites") / project_name

            # Prepare orchestrator config
            config = {
                "task": message,
                "project_path": str(project_path),
                "max_rounds": 3,
                "mode": "3-loop",
            }

            # Run orchestrator if available
            if orchestrator_main and OrchestratorContext:
                print("[Jarvis] Running multi-agent orchestrator...")

                # Create orchestrator context
                orch_context = OrchestratorContext.create_default(config)

                result = await asyncio.to_thread(orchestrator_main, orch_context)

                # Format response
                files_created = result.get("files_modified", [])
                cost = result.get("cost_summary", {}).get("total_usd", 0.0)

                response_content = f"""✓ Task complete!

I've created your project: **{project_name}**

📁 Location: `{project_path}`

📄 Files created ({len(files_created)}):
{self._format_file_list(files_created)}

💰 Cost: ${cost:.2f}
⏱️ Rounds: {result.get('rounds_completed', 'N/A')}

What would you like to do next?"""

                return {
                    "content": response_content,
                    "metadata": {
                        "type": "complex_task",
                        "project_name": project_name,
                        "project_path": str(project_path),
                        "files_created": files_created,
                        "cost": cost,
                        "orchestrator_result": result
                    }
                }
            else:
                return {
                    "content": "I can help with that, but the multi-agent orchestrator is not available. Please ensure the orchestrator module is properly installed.",
                    "metadata": {"error": True, "type": "complex_task"}
                }

        except Exception as e:
            print(f"[Jarvis] Complex task error: {e}")
            import traceback
            traceback.print_exc()

            return {
                "content": f"I encountered an error executing this task: {str(e)}",
                "metadata": {"error": True, "type": "complex_task"}
            }

    async def handle_file_operation(
        self,
        message: str,
        context: Optional[Dict],
        intent: Intent
    ) -> Dict[str, Any]:
        """Handle file operations - targeted edits"""
        try:
            # Find target files
            target_files = intent.target_files or []

            if not target_files:
                # Try to extract file names from message
                import re
                file_patterns = r'\b\w+\.(py|js|html|css|json|md|txt)\b'
                found_files = re.findall(file_patterns, message)
                target_files = found_files

            if not target_files:
                return {
                    "content": "I'd like to help, but I need you to specify which file(s) you want me to work on. Can you provide the filename?",
                    "metadata": {"type": "file_operation", "needs_clarification": True}
                }

            # For now, provide guidance
            response_content = f"""I can help you with {', '.join(target_files)}.

To make specific changes, I'll need to:
1. Locate the file(s) in your project
2. Read the current content
3. Apply your requested changes
4. Save the updated file(s)

Could you provide more details about what changes you'd like me to make?"""

            return {
                "content": response_content,
                "metadata": {
                    "type": "file_operation",
                    "target_files": target_files
                }
            }

        except Exception as e:
            print(f"[Jarvis] File operation error: {e}")
            return {
                "content": f"I encountered an error: {str(e)}",
                "metadata": {"error": True}
            }

    async def handle_conversation(
        self,
        message: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Handle casual conversation"""
        return await self.handle_simple_query(message, context)

    def _extract_project_name(self, message: str) -> str:
        """Extract project name from message"""
        # Simple extraction - look for keywords
        words = message.lower().split()

        # Common patterns: "build a {name}", "create {name}", "{name} website"
        keywords = ["build", "create", "make"]

        for i, word in enumerate(words):
            if word in keywords and i + 1 < len(words):
                next_word = words[i + 1]
                if next_word not in ["a", "an", "the"]:
                    return next_word.replace(" ", "-")
                elif i + 2 < len(words):
                    return words[i + 2].replace(" ", "-")

        # Fallback: use timestamp
        return f"project_{int(time.time())}"

    def _format_file_list(self, files: List[str]) -> str:
        """Format file list for display"""
        if not files:
            return "  (no files)"

        return "\n".join(f"  • {file}" for file in files[:10]) + \
               (f"\n  ... and {len(files) - 10} more" if len(files) > 10 else "")

    async def store_interaction(
        self,
        user_message: str,
        assistant_response: str
    ):
        """Store interaction in memory"""
        if not self.memory_enabled:
            return

        try:
            # Store as conversation memory
            await self.vector_store.store_memory(
                content=f"User: {user_message}\nJarvis: {assistant_response}",
                memory_type=MemoryType.OBSERVATION,
                metadata={
                    "session_id": self.current_session.id if self.current_session else "unknown",
                    "timestamp": time.time()
                }
            )
        except Exception as e:
            print(f"[Jarvis] Failed to store interaction: {e}")

    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return [msg.to_dict() for msg in self.conversation_history]

    async def stream_response(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream response tokens as they're generated"""
        if not self.llm_available:
            yield {
                "type": "error",
                "content": "LLM client not configured",
                "timestamp": time.time()
            }
            return

        try:
            # Build conversation context
            history_text = ""
            for msg in self.conversation_history[-10:]:
                history_text += f"{msg.role}: {msg.content}\n"

            full_prompt = f"""Previous conversation:
{history_text}

User: {message}

Jarvis:"""

            # Get full response (streaming not supported with current infrastructure)
            response_text = await asyncio.to_thread(
                llm_chat,
                role="employee",
                system_prompt="You are Jarvis, a helpful AI assistant.",
                user_content=full_prompt,
                temperature=0.7
            )

            # Simulate streaming by chunking the response
            words = response_text.split()
            for i, word in enumerate(words):
                yield {
                    "type": "token",
                    "content": word + (" " if i < len(words) - 1 else ""),
                    "timestamp": time.time()
                }
                await asyncio.sleep(0.02)  # Small delay for smoother effect

            yield {
                "type": "complete",
                "timestamp": time.time()
            }

        except Exception as e:
            yield {
                "type": "error",
                "content": str(e),
                "timestamp": time.time()
            }
