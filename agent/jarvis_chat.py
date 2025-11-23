"""
Jarvis Conversational Interface

Intelligent chat interface that routes requests to appropriate handlers:
- Simple queries → Direct LLM response
- Complex tasks → Multi-agent orchestrator
- File operations → Targeted file edits
"""

import asyncio
import importlib.util
import json
import os
import random
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

# Import JARVIS persona
from jarvis_persona import (
    JARVIS_SYSTEM_PROMPT,
    JARVIS_GREETINGS,
    JARVIS_FAREWELLS,
    format_task_acknowledgment,
    format_task_completion,
    format_error_response,
)

# Import file operations module for file system access and document generation
try:
    from file_operations import (
        FileOperationHandler,
        normalize_path,
        list_directory,
        read_file,
        write_file,
        create_document,
        create_pdf,
        create_word_document,
        create_excel_spreadsheet,
        get_available_formats,
    )
    FILE_OPERATIONS_AVAILABLE = True
except ImportError as e:
    print(f"[Jarvis] File operations module not available: {e}")
    FILE_OPERATIONS_AVAILABLE = False
    FileOperationHandler = None

# Import existing components
try:
    from memory.session_manager import SessionManager
    from memory.vector_store import VectorMemoryStore, MemoryType
    from memory.context_retriever import ContextRetriever
except ImportError:
    SessionManager = None
    VectorMemoryStore = None
    ContextRetriever = None

# Import clarification system
try:
    from clarification import (
        ClarificationManager,
        ClarificationPhase,
        should_request_clarification,
        RequestClarity,
    )
    CLARIFICATION_AVAILABLE = True
except ImportError:
    ClarificationManager = None
    ClarificationPhase = None
    should_request_clarification = None
    RequestClarity = None
    CLARIFICATION_AVAILABLE = False

# Import adaptive user profile memory
try:
    from memory.user_profile import (
        AdaptiveMemoryManager,
        get_adaptive_memory,
        MemoryCategory,
        CommunicationStyle,
    )
    ADAPTIVE_MEMORY_AVAILABLE = True
except ImportError:
    AdaptiveMemoryManager = None
    get_adaptive_memory = None
    MemoryCategory = None
    CommunicationStyle = None
    ADAPTIVE_MEMORY_AVAILABLE = False

# Import LLM module explicitly (bypass llm/ package shadowing)
# The llm/ directory (Phase 9) shadows llm.py - we need to load llm.py explicitly
llm_chat = None
try:
    # Find the llm.py file (not the llm/ package)
    llm_file = Path(__file__).parent / "llm.py"
    if llm_file.exists():
        spec = importlib.util.spec_from_file_location("llm_module", llm_file)
        llm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(llm_module)
        llm_chat = llm_module.chat
        print(f"[Jarvis] LLM module loaded from {llm_file}")
except Exception as e:
    print(f"[Jarvis] LLM import failed: {e}")
    llm_chat = None

# Import orchestrator - must also handle the llm/ shadowing issue
orchestrator_main = None
OrchestratorContext = None
try:
    # Import OrchestratorContext first (doesn't depend on llm)
    from orchestrator_context import OrchestratorContext

    # For orchestrator, we need to ensure llm.py is used, not llm/ package
    # Temporarily fix the import by loading orchestrator after llm_module is set
    orchestrator_file = Path(__file__).parent / "orchestrator.py"
    if orchestrator_file.exists():
        # The orchestrator will use whatever 'llm' is in sys.modules
        # We need a different approach - just import and catch errors
        try:
            from orchestrator import main as orchestrator_main
        except ImportError as e:
            print(f"[Jarvis] Orchestrator import failed: {e}")
            orchestrator_main = None
except ImportError as e:
    print(f"[Jarvis] OrchestratorContext import failed: {e}")
    OrchestratorContext = None


class IntentType(Enum):
    """Types of user intents"""
    SIMPLE_QUERY = "simple_query"          # Questions, explanations
    COMPLEX_TASK = "complex_task"          # Build, create projects
    FILE_OPERATION = "file_operation"      # Edit, fix specific files
    CONVERSATION = "conversation"          # Casual chat
    DOCUMENT_PROCESSING = "document_processing"  # Analyze/process attached documents
    FILE_CREATION = "file_creation"        # Create files (PDF, Word, Excel, etc.)
    FILE_SYSTEM_ACCESS = "file_system_access"  # List directories, read external files


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
                self.vector_store = VectorMemoryStore(persist_directory="data/chat_memory")
                self.session_manager = SessionManager(
                    vector_store=self.vector_store,
                    user_id="default_user"  # Default user for single-user mode
                )
                self.context_retriever = ContextRetriever(self.vector_store)
            except Exception as e:
                print(f"[Jarvis] Memory initialization failed: {e}")
                self.memory_enabled = False
        else:
            self.memory_enabled = False

        # Use existing LLM infrastructure
        self.llm_available = llm_chat is not None

        # Initialize clarification manager
        if CLARIFICATION_AVAILABLE and ClarificationManager:
            self.clarification_manager = ClarificationManager(
                clarity_threshold=RequestClarity.SOMEWHAT_CLEAR,
                max_questions=5
            )
            self.active_clarification_session = None
        else:
            self.clarification_manager = None
            self.active_clarification_session = None

        # Initialize adaptive user memory for personalization
        if ADAPTIVE_MEMORY_AVAILABLE and get_adaptive_memory:
            try:
                self.adaptive_memory = get_adaptive_memory()
                print("[Jarvis] Adaptive memory initialized - personalization enabled")
            except Exception as e:
                print(f"[Jarvis] Adaptive memory failed: {e}")
                self.adaptive_memory = None
        else:
            self.adaptive_memory = None

        # Initialize file operations handler
        if FILE_OPERATIONS_AVAILABLE and FileOperationHandler:
            try:
                self.file_handler = FileOperationHandler()
                print("[Jarvis] File operations initialized - file creation enabled")
            except Exception as e:
                print(f"[Jarvis] File operations init failed: {e}")
                self.file_handler = None
        else:
            self.file_handler = None

        # Conversation state
        self.current_session = None
        self.current_user_id = "default_user"
        self.conversation_history: List[ChatMessage] = []

    async def start_session(self, user_id: str = "default_user") -> str:
        """Start a new conversation session"""
        self.current_user_id = user_id

        # Initialize user profile for adaptive personalization
        if self.adaptive_memory:
            try:
                profile = self.adaptive_memory.get_or_create_profile(user_id)
                if profile.display_name:
                    print(f"[Jarvis] Welcome back, {profile.display_name}!")
                else:
                    print(f"[Jarvis] New user profile created: {user_id}")
            except Exception as e:
                print(f"[Jarvis] Profile load failed: {e}")

        if self.memory_enabled:
            try:
                session = self.session_manager.start_session(metadata={"user": user_id})
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

            # Analyze message for adaptive learning and memory extraction
            stored_memory = None
            if self.adaptive_memory:
                try:
                    stored_memory, detected_traits = self.adaptive_memory.analyze_message(
                        self.current_user_id,
                        user_message
                    )
                    if stored_memory:
                        print(f"[Jarvis] Memory stored: {stored_memory.category.value}")
                    if detected_traits:
                        print(f"[Jarvis] Traits detected: {list(detected_traits.keys())}")
                except Exception as e:
                    print(f"[Jarvis] Adaptive learning error: {e}")

            # Check if we're in an active clarification loop
            if self.clarification_manager and self.active_clarification_session:
                session = self.active_clarification_session
                if session.phase == ClarificationPhase.ASKING:
                    # Process answer to clarification questions
                    result = self.clarification_manager.process_answer(user_message)
                    print(f"[Jarvis] Clarification: {result.get('status', 'unknown')}")

                    if result.get("status") in ["complete", "skipped"]:
                        # Ready to proceed with enhanced task
                        enhanced_task = session.enhanced_request or session.original_request

                        # Create intent for complex task
                        intent = Intent(
                            type=IntentType.COMPLEX_TASK,
                            confidence=0.9,
                            reasoning="Clarification completed",
                            requires_orchestrator=True
                        )

                        response = await self.handle_complex_task(enhanced_task, context, intent)
                        response["metadata"]["clarification"] = {
                            "session_id": session.session_id,
                            "answers_count": len(session.answers),
                            "status": result.get("status")
                        }

                        # Clear active session
                        self.active_clarification_session = None
                    else:
                        # Need more answers - send next question
                        next_question = result.get("next_question")
                        if next_question:
                            response = {
                                "content": f"Thanks! Next question:\n\n{next_question.question}",
                                "metadata": {
                                    "type": "clarification",
                                    "session_id": session.session_id,
                                    "progress": session.progress
                                }
                            }
                        else:
                            # No more questions - complete
                            self.clarification_manager.complete_clarification()
                            enhanced_task = session.enhanced_request or session.original_request
                            intent = Intent(
                                type=IntentType.COMPLEX_TASK,
                                confidence=0.9,
                                reasoning="Clarification completed",
                                requires_orchestrator=True
                            )
                            response = await self.handle_complex_task(enhanced_task, context, intent)
                            self.active_clarification_session = None

                    # Store and return
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=response["content"],
                        timestamp=time.time(),
                        metadata=response.get("metadata", {})
                    )
                    self.conversation_history.append(assistant_msg)
                    return response

            # Check if user is explicitly asking JARVIS to remember something
            # and provide immediate feedback
            if stored_memory and self._is_explicit_memory_request(user_message):
                memory_response = self._format_memory_confirmation(stored_memory)
                assistant_msg = ChatMessage(
                    role="assistant",
                    content=memory_response,
                    timestamp=time.time(),
                    metadata={"type": "memory_stored", "category": stored_memory.category.value}
                )
                self.conversation_history.append(assistant_msg)
                return {
                    "content": memory_response,
                    "metadata": {
                        "type": "memory_stored",
                        "category": stored_memory.category.value,
                        "memory_id": stored_memory.id
                    }
                }

            # Check for memory query commands (e.g., "what do you remember about me?")
            if self._is_memory_query(user_message):
                memory_response = await self._handle_memory_query(user_message)
                return memory_response

            # Check for self-analysis command (JARVIS reviews his own docs/code)
            if self._is_self_analysis_request(user_message):
                analysis_response = await self._handle_self_analysis(user_message)
                return analysis_response

            # Analyze intent
            intent = await self.analyze_intent(user_message, context or {})

            print(f"[Jarvis] Intent: {intent.type.value} (confidence: {intent.confidence:.2f})")
            print(f"[Jarvis] Reasoning: {intent.reasoning}")

            # Check if clarification is needed for complex tasks
            if intent.type == IntentType.COMPLEX_TASK and self.clarification_manager:
                needs_clarification, analysis = self.clarification_manager.should_clarify(user_message)

                if needs_clarification:
                    print(f"[Jarvis] Clarification needed: {analysis.clarity_level.value}")

                    # Start clarification session
                    session = self.clarification_manager.start_session(user_message, analysis)
                    self.active_clarification_session = session

                    # Format first question
                    first_question = session.current_question
                    if first_question:
                        question_text = f"I'd like to understand your requirements better:\n\n"
                        question_text += f"**Question 1/{len(session.questions)}:** {first_question.question}"

                        if first_question.options:
                            question_text += "\n\nOptions:"
                            for i, opt in enumerate(first_question.options):
                                question_text += f"\n  {chr(97+i)}) {opt}"

                        question_text += "\n\n_(You can say 'skip' to proceed with defaults)_"

                        response = {
                            "content": question_text,
                            "metadata": {
                                "type": "clarification",
                                "session_id": session.session_id,
                                "questions_total": len(session.questions),
                                "clarity_level": analysis.clarity_level.value
                            }
                        }
                    else:
                        # No questions generated, proceed directly
                        response = await self.handle_complex_task(user_message, context, intent)
                        self.active_clarification_session = None

                    # Store and return
                    assistant_msg = ChatMessage(
                        role="assistant",
                        content=response["content"],
                        timestamp=time.time(),
                        metadata=response.get("metadata", {})
                    )
                    self.conversation_history.append(assistant_msg)
                    return response

            # Route to appropriate handler
            if intent.type == IntentType.SIMPLE_QUERY:
                response = await self.handle_simple_query(user_message, context)

            elif intent.type == IntentType.DOCUMENT_PROCESSING:
                response = await self.handle_document_processing(user_message, context, intent)

            elif intent.type == IntentType.COMPLEX_TASK:
                response = await self.handle_complex_task(user_message, context, intent)

            elif intent.type == IntentType.FILE_OPERATION:
                response = await self.handle_file_operation(user_message, context, intent)

            elif intent.type in (IntentType.FILE_CREATION, IntentType.FILE_SYSTEM_ACCESS):
                response = await self.handle_file_system_request(user_message, context)

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

2. "complex_task" - Building projects, creating applications, multi-step CODE GENERATION
   Examples: "Build a website", "Create a REST API", "Code a game"
   Note: Use this ONLY for tasks that require CREATING/BUILDING new code
   NEVER use for code analysis, code review, or examining existing code

3. "document_processing" - Analyze/process/transform attached documents into output
   Examples: "Make me a resume from this document", "Summarize this file",
   "Extract info from this PDF", "Create a report based on this data"
   Note: Use when user attaches a file and wants analysis/transformation (NOT code)

4. "file_operation" - Editing, fixing, updating specific files
   Examples: "Fix bug in login.js", "Update header color", "Add error handling"

5. "file_creation" - Creating physical files (PDF, Word, Excel, etc.)
   Examples: "Save that as a PDF", "Create a PDF at D:/Documents/report.pdf",
   "Make this into a Word document", "Export to Excel"
   Note: Use when user wants to create actual files from content

6. "file_system_access" - Listing directories, reading external files, CODE ANALYSIS
   Examples: "List files in D:/Documents", "Show me what's in /home/user",
   "Read the file at C:/Users/Kevin/notes.txt", "Open D:/project/config.json",
   "Analyze the code in D:/myproject", "Review files in /home/user/src"
   Note: Use when user wants to browse, read, ANALYZE, or REVIEW files from external paths
   IMPORTANT: Code analysis/review requests with paths should use THIS type, NOT complex_task

7. "conversation" - Casual chat, greetings, unclear requests
   Examples: "Hello", "Thanks!", "Can you help?"

Consider:
- Does user have attached files that need analysis? -> document_processing
- Is the output NEW code/software being CREATED? -> complex_task
- Is it processing documents to produce documents? -> document_processing
- Is user asking to create/save a file (PDF, Word, etc.)? -> file_creation
- Is user asking to browse directories or read external files? -> file_system_access
- Is user asking to ANALYZE, REVIEW, or EXAMINE existing code? -> file_system_access (NOT complex_task!)
- Does the request mention an external path AND analysis/review keywords? -> file_system_access

Return ONLY valid JSON (no markdown):
{{
  "type": "simple_query|complex_task|document_processing|file_operation|file_creation|file_system_access|conversation",
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

    def _fallback_intent_analysis(self, message: str, context: Optional[Dict] = None) -> Intent:
        """Fallback intent analysis using heuristics"""
        message_lower = message.lower()

        # File creation keywords - check early for save/export requests
        file_creation_keywords = [
            "save as", "save to", "export to", "create a pdf", "create pdf",
            "make it a pdf", "make a pdf", "to pdf", "as pdf", "into pdf",
            "create a word", "make it word", "to word", "as docx", "to docx",
            "create excel", "to xlsx", "as excel", "export excel",
            "save that", "save this", "export that", "export this"
        ]

        # File system access keywords - detect external path access
        file_system_keywords = [
            "list files", "show files", "what's in", "contents of",
            "files in", "list directory", "show directory",
            "read file", "open file", "read the file", "show me the file"
        ]

        # CODE ANALYSIS keywords - these should READ code, not BUILD things
        code_analysis_keywords = [
            "analyze", "review", "investigate", "check", "inspect",
            "look at", "examine", "audit", "find inconsistencies",
            "find issues", "find bugs", "find errors", "scan"
        ]

        # Path patterns indicating external file system access
        import re
        has_windows_path = bool(re.search(r'[A-Za-z]:[/\\]', message))
        has_unix_path = bool(re.search(r'(?:^|[^a-zA-Z])/[a-zA-Z0-9_\-]+/', message))
        has_external_path = has_windows_path or has_unix_path

        # Check for file creation intent
        if any(kw in message_lower for kw in file_creation_keywords):
            return Intent(
                type=IntentType.FILE_CREATION,
                confidence=0.85,
                reasoning="Detected file creation/export keywords",
                requires_orchestrator=False
            )

        # CODE ANALYSIS with external path - should READ, not BUILD
        if has_external_path and any(kw in message_lower for kw in code_analysis_keywords):
            return Intent(
                type=IntentType.FILE_SYSTEM_ACCESS,
                confidence=0.90,
                reasoning="Detected code analysis request with external path - will read and analyze",
                requires_orchestrator=False
            )

        # Check for file system access with external paths
        if has_external_path and any(kw in message_lower for kw in file_system_keywords):
            return Intent(
                type=IntentType.FILE_SYSTEM_ACCESS,
                confidence=0.85,
                reasoning="Detected file system access with external path",
                requires_orchestrator=False
            )

        # If just an external path is mentioned with list/show/read keywords
        if has_external_path:
            return Intent(
                type=IntentType.FILE_SYSTEM_ACCESS,
                confidence=0.75,
                reasoning="Detected external file path reference",
                requires_orchestrator=False
            )

        # Document processing keywords (check if files are attached)
        has_attached_files = context and context.get("attached_files")
        doc_processing_keywords = [
            "resume", "summarize", "extract", "analyze", "report",
            "from this", "based on this", "this document", "this file",
            "convert", "transform"
        ]

        # If files are attached and document-related keywords present
        if has_attached_files and any(kw in message_lower for kw in doc_processing_keywords):
            return Intent(
                type=IntentType.DOCUMENT_PROCESSING,
                confidence=0.85,
                reasoning="Detected document processing request with attached files",
                requires_orchestrator=False
            )

        # Complex task keywords (for CODE GENERATION - building new things)
        # Note: "analyze", "review" should NOT trigger this
        complex_keywords = [
            "build", "develop", "implement", "program",
            "website", "app", "application", "api", "system",
            "create a", "make a", "generate a"
        ]

        # File operation keywords
        file_keywords = [
            "fix", "update", "change", "modify", "edit",
            "bug", ".py", ".js", ".css", ".html", "line"
        ]

        # Only use complex_task for actual code-BUILDING tasks (not analysis)
        is_analysis_request = any(kw in message_lower for kw in code_analysis_keywords)
        if any(kw in message_lower for kw in complex_keywords) and not has_attached_files and not is_analysis_request:
            return Intent(
                type=IntentType.COMPLEX_TASK,
                confidence=0.7,
                reasoning="Detected build/create keywords for code generation",
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

            # Get adaptive personalization context
            adaptation_prompt = ""
            if self.adaptive_memory:
                try:
                    adaptation_prompt = self.adaptive_memory.format_adaptation_prompt(
                        self.current_user_id
                    )
                except Exception as e:
                    print(f"[Jarvis] Adaptation context error: {e}")

            # Process attached files if present
            files_context = ""
            if context and context.get("attached_files"):
                files_context = "\n\n=== ATTACHED FILES ===\n"
                for file_info in context["attached_files"]:
                    file_name = file_info.get("name", "unknown")
                    file_content = file_info.get("content", "")
                    # Limit content to prevent token overflow
                    if len(file_content) > 15000:
                        file_content = file_content[:15000] + "\n... (content truncated)"
                    files_context += f"\n--- {file_name} ---\n{file_content}\n"
                files_context += "=== END ATTACHED FILES ===\n"
                print(f"[Jarvis] Processing {len(context['attached_files'])} attached file(s)")

            full_prompt = f"""Previous conversation:
{history_text}
{adaptation_prompt}{files_context}
User: {message}

Jarvis:"""

            # Use existing LLM infrastructure
            response_text = await asyncio.to_thread(
                llm_chat,
                role="employee",
                system_prompt=JARVIS_SYSTEM_PROMPT,
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

    async def handle_document_processing(
        self,
        message: str,
        context: Optional[Dict],
        intent: Intent
    ) -> Dict[str, Any]:
        """Handle document processing tasks - analyze files and produce output"""
        if not self.llm_available:
            return {
                "content": "I need an LLM client to process documents. Please ensure it's configured.",
                "metadata": {"error": True}
            }

        try:
            print("\n[Jarvis] 📄 Document processing request detected...")

            # Build conversation history for context
            history_text = ""
            last_jarvis_output = None
            for msg in self.conversation_history[-10:]:
                history_text += f"{msg.role}: {msg.content}\n"
                if msg.role == "assistant":
                    last_jarvis_output = msg.content

            # Check if this is a follow-up request referencing previous output
            message_lower = message.lower()
            follow_up_indicators = [
                "that", "this", "it", "the summary", "what you", "you just",
                "make it", "convert it", "save it", "export it", "into a pdf",
                "into pdf", "to pdf", "as pdf", "pdf format", "word format"
            ]
            is_follow_up = any(indicator in message_lower for indicator in follow_up_indicators)

            # If it's a follow-up about previous output and no new files attached
            if is_follow_up and last_jarvis_output and (not context or not context.get("attached_files")):
                print("[Jarvis] Detected follow-up request about previous output")
                # Handle the follow-up with the previous output
                return await self._handle_output_conversion(message, last_jarvis_output)

            # Check for attached files
            if not context or not context.get("attached_files"):
                # If no files but we have previous output, offer to work with that
                if last_jarvis_output and len(last_jarvis_output) > 100:
                    return {
                        "content": "I don't see any new attached files, sir. However, I do have my previous output available. Would you like me to convert that into a different format? Just specify: PDF, Word, Plain Text, or Markdown.",
                        "metadata": {"type": "document_processing", "has_previous_output": True}
                    }
                return {
                    "content": "I'd be happy to help with that! However, I don't see any attached files. Please attach the document you'd like me to process.",
                    "metadata": {"type": "document_processing", "needs_file": True}
                }

            # Build document context
            files_context = ""
            file_names = []
            for file_info in context["attached_files"]:
                file_name = file_info.get("name", "unknown")
                file_content = file_info.get("content", "")
                file_names.append(file_name)
                # Limit content to prevent token overflow
                if len(file_content) > 20000:
                    file_content = file_content[:20000] + "\n... (content truncated)"
                files_context += f"\n=== {file_name} ===\n{file_content}\n"

            print(f"[Jarvis] Processing {len(file_names)} document(s): {', '.join(file_names)}")

            # Determine the type of document task
            message_lower = message.lower()

            # Check if user specified a format
            format_keywords = {
                "pdf": "PDF", "word": "Word (DOCX)", "docx": "Word (DOCX)",
                "txt": "Plain Text", "text": "Plain Text", "markdown": "Markdown",
                "html": "HTML"
            }
            requested_format = None
            for fmt_key, fmt_name in format_keywords.items():
                if fmt_key in message_lower:
                    requested_format = fmt_name
                    break

            # Resume-specific handling
            if "resume" in message_lower or "cv" in message_lower:
                system_prompt = """You are JARVIS, an expert document processor and resume writer.
Your task is to analyze the provided document(s) and create a professional resume.

Guidelines:
1. Extract ALL relevant information from the document (work experience, education, skills, achievements)
2. Organize information in a clear, professional resume format
3. Use bullet points for experience and achievements
4. Highlight quantifiable achievements where possible
5. Format the output as a clean, readable resume (not HTML/code)
6. If information is missing, note what additional details would strengthen the resume

Output a complete, formatted resume based on the document provided."""
                is_document_creation = True

            elif "summar" in message_lower:
                system_prompt = """You are JARVIS, an expert document analyst.
Your task is to summarize the provided document(s).

Guidelines:
1. Identify the main topics and key points
2. Highlight important facts, figures, and conclusions
3. Keep the summary concise but comprehensive
4. Use bullet points for clarity
5. Note any action items or important dates"""
                is_document_creation = False  # Summary doesn't need format export

            elif "extract" in message_lower or "info" in message_lower:
                system_prompt = """You are JARVIS, an expert at information extraction.
Your task is to extract specific information from the provided document(s).

Guidelines:
1. Identify and extract all relevant data points
2. Organize information in a structured format
3. Use tables or lists where appropriate
4. Note any missing or unclear information"""
                is_document_creation = False

            elif any(word in message_lower for word in ["letter", "report", "proposal", "memo", "cover letter"]):
                system_prompt = """You are JARVIS, an expert document creator.
Your task is to create a professional document based on the provided source material.

Guidelines:
1. Extract relevant information from the source document(s)
2. Create a well-structured, professional document
3. Use appropriate tone and formatting for the document type
4. Include all necessary sections and components
5. Proofread for clarity and professionalism"""
                is_document_creation = True

            else:
                system_prompt = """You are JARVIS, an expert document processor.
Your task is to analyze and process the provided document(s) according to the user's request.

Guidelines:
1. Carefully read and understand the document content
2. Process it according to the user's specific request
3. Provide clear, well-organized output
4. Ask clarifying questions if the request is unclear"""
                is_document_creation = "create" in message_lower or "make" in message_lower or "generate" in message_lower

            # Build the full prompt
            full_prompt = f"""User Request: {message}

DOCUMENTS PROVIDED:
{files_context}

Please process these document(s) according to the user's request. Provide a complete, well-formatted response."""

            # Process with LLM
            response_text = await asyncio.to_thread(
                llm_chat,
                role="employee",
                system_prompt=system_prompt,
                user_content=full_prompt,
                temperature=0.5  # Lower temperature for more focused output
            )

            # Add format preference prompt for document creation tasks
            if is_document_creation and not requested_format:
                format_prompt = """

---
📄 **Output Format Options**

I've prepared this document above. Would you like me to generate it in a specific format?
- **PDF** - Professional, ready to print/share
- **Word (DOCX)** - Editable document format
- **Plain Text** - Simple text file
- **Markdown** - Formatted text for web/docs

Just let me know your preferred format and I'll create the file for you!"""
                response_text += format_prompt
                metadata = {
                    "type": "document_processing",
                    "files_processed": file_names,
                    "awaiting_format": True,
                    "document_type": "resume" if "resume" in message_lower or "cv" in message_lower else "document"
                }
            elif is_document_creation and requested_format:
                # User already specified format - note it in metadata
                metadata = {
                    "type": "document_processing",
                    "files_processed": file_names,
                    "requested_format": requested_format
                }
                response_text += f"\n\n📁 *You requested {requested_format} format. I can generate this file for you - just say 'generate' or 'create the file'!*"
            else:
                metadata = {
                    "type": "document_processing",
                    "files_processed": file_names
                }

            return {
                "content": response_text,
                "metadata": metadata
            }

        except Exception as e:
            print(f"[Jarvis] Document processing error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "content": f"I encountered an error processing your document: {str(e)}",
                "metadata": {"error": True, "type": "document_processing"}
            }

    async def _handle_output_conversion(
        self,
        message: str,
        previous_output: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle conversion of previous output to different formats with actual file creation"""
        try:
            message_lower = message.lower()

            # Detect requested format
            if "pdf" in message_lower:
                format_type = "pdf"
                format_display = "PDF"
            elif "word" in message_lower or "docx" in message_lower:
                format_type = "docx"
                format_display = "Word (DOCX)"
            elif "excel" in message_lower or "xlsx" in message_lower:
                format_type = "xlsx"
                format_display = "Excel (XLSX)"
            elif "markdown" in message_lower or "md" in message_lower:
                format_type = "md"
                format_display = "Markdown"
            elif "text" in message_lower or "txt" in message_lower:
                format_type = "txt"
                format_display = "Plain Text"
            else:
                format_type = None
                format_display = None

            if format_type:
                # Check if file operations are available
                if not self.file_handler:
                    return {
                        "content": f"""I'm afraid the file generation system is not available at the moment, sir.

However, here is your content ready for {format_display} format:

---
{previous_output}
---

You may copy this content and save it manually.""",
                        "metadata": {
                            "type": "output_conversion",
                            "format": format_display,
                            "file_created": False
                        }
                    }

                # Extract filename from message or generate one
                filename = self._extract_filename(message) or f"jarvis_output_{int(time.time())}"

                # Determine output path
                if output_path:
                    file_path = normalize_path(output_path)
                else:
                    # Try to extract path from message
                    extracted_path = self._extract_path_from_message(message)
                    if extracted_path:
                        file_path = normalize_path(extracted_path)
                        # If extracted path is a directory, append filename
                        if file_path.is_dir() or not file_path.suffix:
                            file_path = file_path / filename
                    else:
                        # Use default output directory
                        file_path = Path.cwd() / "outputs" / filename

                # Create the file
                result = create_document(
                    path=str(file_path),
                    content=previous_output,
                    format=format_type,
                    title=filename.replace('_', ' ').title()
                )

                if result["success"]:
                    response = f"""Very good, sir. I have created your {format_display} file.

📁 **File Created:** `{result['path']}`
📊 **Size:** {result.get('size', 0):,} bytes

The document has been saved successfully. Is there anything else you'd like me to do with it?"""

                    return {
                        "content": response,
                        "metadata": {
                            "type": "output_conversion",
                            "format": format_display,
                            "file_created": True,
                            "file_path": result["path"],
                            "file_size": result.get("size", 0)
                        }
                    }
                else:
                    return {
                        "content": f"""I'm afraid I encountered an issue creating the {format_display} file, sir.

Error: {result.get('error', 'Unknown error')}

Here is your content that I attempted to save:

---
{previous_output[:2000]}{'...(truncated)' if len(previous_output) > 2000 else ''}
---

Would you like me to try a different location or format?""",
                        "metadata": {
                            "type": "output_conversion",
                            "format": format_display,
                            "file_created": False,
                            "error": result.get("error")
                        }
                    }
            else:
                # Ask for format preference with available formats
                available = get_available_formats() if FILE_OPERATIONS_AVAILABLE else {}
                format_list = []
                if available.get("pdf", False):
                    format_list.append("- **PDF** - Professional, ready to print/share")
                if available.get("docx", False):
                    format_list.append("- **Word (DOCX)** - Editable document format")
                if available.get("xlsx", False):
                    format_list.append("- **Excel (XLSX)** - Spreadsheet format")
                format_list.append("- **Markdown** - Formatted text for web/docs")
                format_list.append("- **Plain Text** - Simple text file")

                return {
                    "content": f"""Of course, sir. I have my previous output ready. Which format would you prefer?

{chr(10).join(format_list)}

Simply tell me the format and I shall create the file accordingly.
You may also specify a path, for example: "Save as PDF to D:/Documents/report.pdf" """,
                    "metadata": {
                        "type": "output_conversion",
                        "awaiting_format": True
                    }
                }

        except Exception as e:
            print(f"[Jarvis] Output conversion error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "content": f"I encountered an issue preparing the format conversion: {str(e)}",
                "metadata": {"error": True}
            }

    def _extract_filename(self, message: str) -> Optional[str]:
        """Extract filename from user message"""
        import re

        # Look for explicit filename patterns
        patterns = [
            r'(?:name|call|save as|filename)[:\s]+["\']?([a-zA-Z0-9_\-\.]+)["\']?',
            r'["\']([a-zA-Z0-9_\-\.]+\.(pdf|docx|xlsx|md|txt))["\']',
            r'as\s+["\']?([a-zA-Z0-9_\-]+)["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                filename = match.group(1)
                # Remove extension if present (will be added by create_document)
                return filename.rsplit('.', 1)[0] if '.' in filename else filename

        return None

    def _extract_path_from_message(self, message: str) -> Optional[str]:
        """Extract file path from user message"""
        import re

        # Look for path patterns
        patterns = [
            # Windows paths: D:\folder\file or D:/folder/file
            r'([A-Za-z]:[/\\][^\s"\'<>|*?]+)',
            # Unix paths: /home/user/folder
            r'(/[^\s"\'<>|*?]+/[^\s"\'<>|*?]+)',
            # Relative paths with to/in/at keywords
            r'(?:to|in|at)\s+["\']?([./][^\s"\']+)["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)

        return None

    async def handle_file_system_request(
        self,
        message: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Handle file system access requests - list directories, read files, create files"""
        try:
            message_lower = message.lower()

            if not self.file_handler:
                return {
                    "content": """I'm afraid the file system access module is not available at the moment, sir.

This capability requires the file_operations module to be properly initialized.
Please ensure the required dependencies are installed:
- reportlab (for PDF)
- python-docx (for Word)
- openpyxl (for Excel)""",
                    "metadata": {"type": "file_system", "error": True}
                }

            # Extract path from message
            target_path = self._extract_path_from_message(message)

            # Detect operation type
            if any(word in message_lower for word in ["list", "show", "what's in", "contents of", "files in", "directory", "folder"]):
                # List directory operation
                if not target_path:
                    return {
                        "content": """Of course, sir. Which directory would you like me to list?

Please provide a path, for example:
- "List files in D:/Documents"
- "Show contents of /home/user/projects"
- "What's in C:/Users/Kevin/Desktop" """,
                        "metadata": {"type": "file_system", "awaiting_path": True}
                    }

                result = list_directory(target_path, recursive=False)

                if result["success"]:
                    # Format directory listing
                    dirs = result.get("directories", [])
                    files = result.get("files", [])

                    listing = f"📁 **Directory:** `{result['path']}`\n\n"

                    if dirs:
                        listing += "**Folders:**\n"
                        for d in dirs[:20]:  # Limit to 20
                            listing += f"  📂 {d['name']}\n"
                        if len(dirs) > 20:
                            listing += f"  ... and {len(dirs) - 20} more folders\n"
                        listing += "\n"

                    if files:
                        listing += "**Files:**\n"
                        for f in files[:30]:  # Limit to 30
                            size_kb = f.get('size', 0) / 1024
                            listing += f"  📄 {f['name']} ({size_kb:.1f} KB)\n"
                        if len(files) > 30:
                            listing += f"  ... and {len(files) - 30} more files\n"

                    if not dirs and not files:
                        listing += "*The directory is empty.*"

                    return {
                        "content": f"""Very good, sir. Here are the contents:

{listing}

Total: {result.get('total_directories', 0)} folders, {result.get('total_files', 0)} files""",
                        "metadata": {
                            "type": "file_system",
                            "operation": "list",
                            "path": result["path"],
                            "total_files": result.get("total_files", 0),
                            "total_directories": result.get("total_directories", 0)
                        }
                    }
                else:
                    return {
                        "content": f"""I'm afraid I couldn't access that directory, sir.

Error: {result.get('error', 'Unknown error')}

Please verify the path exists and I have permission to access it.""",
                        "metadata": {"type": "file_system", "error": True}
                    }

            elif any(word in message_lower for word in ["read", "open", "show me", "display", "view", "cat"]):
                # Read file operation
                if not target_path:
                    return {
                        "content": """Certainly, sir. Which file would you like me to read?

Please provide a file path, for example:
- "Read D:/Documents/report.txt"
- "Show me /home/user/config.json"
- "Open C:/Users/Kevin/notes.md" """,
                        "metadata": {"type": "file_system", "awaiting_path": True}
                    }

                result = read_file(target_path)

                if result["success"]:
                    if result.get("is_binary"):
                        return {
                            "content": f"""I'm afraid that's a binary file, sir. I cannot display its contents as text.

📄 **File:** `{result['path']}`
📊 **Size:** {result.get('size', 0):,} bytes
🔒 **Type:** Binary

Would you like me to do something else with this file?""",
                            "metadata": {"type": "file_system", "is_binary": True}
                        }

                    content = result.get("content", "")
                    # Truncate very long files
                    if len(content) > 5000:
                        content = content[:5000] + "\n\n... (content truncated, file is too large to display fully)"

                    return {
                        "content": f"""Very good, sir. Here are the contents of `{result['path']}`:

```
{content}
```

📄 Size: {result.get('size', 0):,} bytes""",
                        "metadata": {
                            "type": "file_system",
                            "operation": "read",
                            "path": result["path"],
                            "size": result.get("size", 0)
                        }
                    }
                else:
                    return {
                        "content": f"""I'm afraid I couldn't read that file, sir.

Error: {result.get('error', 'Unknown error')}

Please verify the file exists and I have permission to read it.""",
                        "metadata": {"type": "file_system", "error": True}
                    }

            elif any(word in message_lower for word in ["create", "make", "generate", "save", "write"]):
                # Create file operation - detect format
                if "pdf" in message_lower:
                    format_type = "pdf"
                elif "word" in message_lower or "docx" in message_lower:
                    format_type = "docx"
                elif "excel" in message_lower or "xlsx" in message_lower:
                    format_type = "xlsx"
                elif "markdown" in message_lower or "md" in message_lower:
                    format_type = "md"
                else:
                    format_type = "txt"

                # Check if we have content to write
                content_to_write = context.get("content") if context else None

                if not content_to_write:
                    # Check conversation history for content
                    for msg in reversed(self.conversation_history[-5:]):
                        if msg.role == "assistant" and len(msg.content) > 100:
                            content_to_write = msg.content
                            break

                if not content_to_write:
                    return {
                        "content": """I'd be happy to create a file for you, sir. What content would you like me to include?

You can either:
1. Tell me what to write and I'll create the file
2. Ask me to generate content first, then say "save that as a PDF" """,
                        "metadata": {"type": "file_system", "awaiting_content": True}
                    }

                # Get filename
                filename = self._extract_filename(message) or f"jarvis_document_{int(time.time())}"

                # Determine path
                if target_path:
                    file_path = normalize_path(target_path)
                else:
                    file_path = Path.cwd() / "outputs" / filename

                result = create_document(
                    path=str(file_path),
                    content=content_to_write,
                    format=format_type,
                    title=filename.replace('_', ' ').title()
                )

                if result["success"]:
                    return {
                        "content": f"""Very good, sir. I have created your file.

📁 **File Created:** `{result['path']}`
📊 **Size:** {result.get('size', 0):,} bytes
📝 **Format:** {format_type.upper()}

The file has been saved successfully.""",
                        "metadata": {
                            "type": "file_system",
                            "operation": "create",
                            "path": result["path"],
                            "format": format_type
                        }
                    }
                else:
                    return {
                        "content": f"""I'm afraid I couldn't create the file, sir.

Error: {result.get('error', 'Unknown error')}

Would you like me to try a different location or format?""",
                        "metadata": {"type": "file_system", "error": True}
                    }

            else:
                # General file system help
                return {
                    "content": """Certainly, sir. I can assist with file system operations. Here's what I can do:

**List Directory Contents:**
- "List files in D:/Documents"
- "Show me what's in /home/user/projects"

**Read Files:**
- "Read D:/Documents/report.txt"
- "Open /home/user/config.json"

**Create Files:**
- "Create a PDF at D:/Documents/report.pdf"
- "Save this as a Word document to /home/user/doc.docx"

**Supported formats:** PDF, Word (DOCX), Excel (XLSX), Markdown, Plain Text

What would you like me to do?""",
                    "metadata": {"type": "file_system", "awaiting_operation": True}
                }

        except Exception as e:
            print(f"[Jarvis] File system error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "content": f"I encountered an issue with the file operation: {str(e)}",
                "metadata": {"type": "file_system", "error": True}
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

            # Prepare orchestrator config - must include project_subdir for orchestrator
            config = {
                "task": message,
                "project_subdir": project_name,  # Key field for orchestrator
                "max_rounds": 3,
                "max_cost_usd": 1.5,
                "cost_warning_usd": 0.8,
                "use_git": True,
                "use_visual_review": False,
                "prompts_file": "prompts_default.json",
            }

            # Pass attached files to orchestrator if present
            if context and context.get("attached_files"):
                files_content = "\n\n=== ATTACHED FILES (User provided these for reference) ===\n"
                for file_info in context["attached_files"]:
                    file_name = file_info.get("name", "unknown")
                    file_content = file_info.get("content", "")
                    # Limit content to prevent token overflow
                    if len(file_content) > 15000:
                        file_content = file_content[:15000] + "\n... (content truncated)"
                    files_content += f"\n--- {file_name} ---\n{file_content}\n"
                files_content += "=== END ATTACHED FILES ===\n"

                # Prepend file content to the task so orchestrator can see it
                config["task"] = f"{message}\n{files_content}"
                print(f"[Jarvis] Including {len(context['attached_files'])} attached file(s) in orchestrator task")

            # Run orchestrator if available
            if orchestrator_main and OrchestratorContext:
                print("[Jarvis] Running multi-agent orchestrator...")

                # Create orchestrator context with config
                orch_context = OrchestratorContext.create_default(config)

                # Pass config as cfg_override and context properly using keyword args
                result = await asyncio.to_thread(
                    orchestrator_main,
                    run_summary=None,
                    mission_id=None,
                    cfg_override=config,
                    context=orch_context
                )

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

    # ══════════════════════════════════════════════════════════════════════
    # Adaptive Memory Management
    # ══════════════════════════════════════════════════════════════════════

    def _is_explicit_memory_request(self, message: str) -> bool:
        """Check if user is explicitly asking to remember something."""
        message_lower = message.lower()
        explicit_patterns = [
            "remember that", "remember i", "remember my", "remember this",
            "please note", "keep in mind", "don't forget",
            "note that", "for future reference", "fyi",
            "i prefer", "i always", "i usually"
        ]
        return any(pattern in message_lower for pattern in explicit_patterns)

    def _is_memory_query(self, message: str) -> bool:
        """Check if user is asking about their stored memories."""
        message_lower = message.lower()
        query_patterns = [
            "what do you remember", "what do you know about me",
            "show my memories", "show my profile", "my preferences",
            "what have i told you", "recall my", "my information"
        ]
        return any(pattern in message_lower for pattern in query_patterns)

    def _format_memory_confirmation(self, memory) -> str:
        """Format confirmation message for stored memory."""
        category_labels = {
            "personal": "personal information",
            "preferences": "your preferences",
            "business": "business context",
            "expertise": "your expertise",
            "interaction": "interaction patterns",
            "custom": "general notes"
        }
        category_label = category_labels.get(memory.category.value, "memory")

        confirmations = [
            f"Noted, sir. I've committed that to memory under {category_label}.",
            f"Understood. I'll remember that as part of {category_label}.",
            f"Very good, sir. That's now stored in my {category_label} records.",
            f"Consider it remembered. I've filed that under {category_label}.",
        ]
        import random
        return random.choice(confirmations)

    async def _handle_memory_query(self, message: str) -> Dict[str, Any]:
        """Handle user queries about their stored memories."""
        if not self.adaptive_memory:
            return {
                "content": "I apologize, sir, but my memory systems are not currently active.",
                "metadata": {"type": "memory_query", "error": True}
            }

        try:
            profile = self.adaptive_memory.get_or_create_profile(self.current_user_id)
            memories = self.adaptive_memory.get_memories(self.current_user_id, limit=20)

            response_parts = ["Certainly, sir. Here's what I have in my records about you:\n"]

            # Profile information
            if profile.display_name:
                response_parts.append(f"**Name:** {profile.display_name}")

            response_parts.append(f"**Communication Style:** {profile.preferred_style.value}")
            response_parts.append(f"**Total Interactions:** {profile.total_messages}")

            # Detected traits
            if profile.traits:
                response_parts.append("\n**Detected Preferences:**")
                for trait_type, trait in profile.traits.items():
                    if trait.confidence > 0.3:
                        response_parts.append(f"  • {trait_type}: {trait.value} (confidence: {trait.confidence:.0%})")

            # Stored memories by category
            if memories:
                response_parts.append("\n**Stored Memories:**")
                by_category = {}
                for mem in memories:
                    cat = mem.category.value
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(mem.content)

                for category, items in by_category.items():
                    response_parts.append(f"\n*{category.title()}:*")
                    for item in items[:5]:
                        response_parts.append(f"  • {item}")
                    if len(items) > 5:
                        response_parts.append(f"  ... and {len(items) - 5} more")

            if not memories and not profile.traits:
                response_parts.append("\nI don't have much stored yet, sir. Feel free to tell me things you'd like me to remember, such as your preferences, business context, or how you prefer to communicate.")

            return {
                "content": "\n".join(response_parts),
                "metadata": {
                    "type": "memory_query",
                    "memories_count": len(memories),
                    "traits_count": len(profile.traits)
                }
            }

        except Exception as e:
            print(f"[Jarvis] Memory query error: {e}")
            return {
                "content": "I encountered an error accessing my memory banks, sir. My apologies.",
                "metadata": {"type": "memory_query", "error": True}
            }

    async def store_memory_explicit(
        self,
        content: str,
        category: str = "custom",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Explicitly store a memory for the current user."""
        if not self.adaptive_memory:
            return {"success": False, "error": "Adaptive memory not available"}

        try:
            # Map string category to enum
            category_map = {
                "personal": MemoryCategory.PERSONAL,
                "preferences": MemoryCategory.PREFERENCES,
                "business": MemoryCategory.BUSINESS,
                "expertise": MemoryCategory.EXPERTISE,
                "custom": MemoryCategory.CUSTOM
            }
            mem_category = category_map.get(category, MemoryCategory.CUSTOM)

            memory = self.adaptive_memory.store_memory(
                user_id=self.current_user_id,
                content=content,
                category=mem_category,
                tags=tags,
                source="explicit"
            )

            return {
                "success": True,
                "memory_id": memory.id,
                "category": memory.category.value
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════
    # Self-Analysis (JARVIS reviewing own documentation/code)
    # ══════════════════════════════════════════════════════════════════════

    def _is_self_analysis_request(self, message: str) -> bool:
        """Check if user is asking JARVIS to analyze himself."""
        message_lower = message.lower()
        self_analysis_patterns = [
            "analyze yourself", "review yourself", "self-analyze",
            "improve yourself", "self-improvement", "self improvement",
            "review your code", "analyze your code", "check your documentation",
            "look at your docs", "review your documentation", "introspection",
            "what can you improve", "how can you be better", "self-reflection"
        ]
        return any(pattern in message_lower for pattern in self_analysis_patterns)

    async def _handle_self_analysis(self, user_message: str) -> Dict[str, Any]:
        """
        JARVIS analyzes his own documentation and code for self-improvement.
        Only runs when explicitly requested by user.
        """
        print("[Jarvis] Self-analysis mode activated")

        try:
            # Find JARVIS's documentation and code files
            base_path = Path(__file__).parent
            docs_path = base_path.parent / "docs"

            analysis_results = {
                "documentation_found": [],
                "code_files_found": [],
                "insights": [],
                "improvement_suggestions": []
            }

            # Scan documentation
            if docs_path.exists():
                for doc_file in docs_path.glob("*.md"):
                    analysis_results["documentation_found"].append(doc_file.name)

            # Find key code files
            key_files = [
                "jarvis_chat.py", "jarvis_persona.py", "jarvis_voice.py",
                "jarvis_vision.py", "conversational_agent.py"
            ]
            for fname in key_files:
                fpath = base_path / fname
                if fpath.exists():
                    analysis_results["code_files_found"].append(fname)

            # Read specific documentation for analysis
            doc_content = ""
            key_docs = ["DEVELOPER_GUIDE.md", "REFERENCE.md", "TROUBLESHOOTING.md"]
            for doc_name in key_docs:
                doc_path = docs_path / doc_name
                if doc_path.exists():
                    try:
                        content = doc_path.read_text(encoding='utf-8')[:5000]
                        doc_content += f"\n\n=== {doc_name} ===\n{content}"
                    except Exception:
                        pass

            # Use LLM to analyze
            if self.llm_available and doc_content:
                analysis_prompt = f"""As JARVIS, I am performing self-analysis to identify areas for improvement.

MY DOCUMENTATION SUMMARY:
{doc_content[:8000]}

Based on this documentation, provide:
1. A brief summary of my current capabilities
2. Any gaps or areas that could be improved
3. Specific suggestions for enhancement
4. Potential new features that would help users

Be constructive and specific. Speak as JARVIS analyzing himself."""

                analysis_text = await asyncio.to_thread(
                    llm_chat,
                    role="employee",
                    system_prompt="You are JARVIS performing self-analysis. Be insightful and constructive.",
                    user_content=analysis_prompt,
                    temperature=0.7
                )
            else:
                analysis_text = "I apologize, sir, but I require an active LLM connection to perform deep self-analysis."

            # Build response
            response_parts = [
                "Very good, sir. I've conducted a thorough self-analysis.\n",
                f"**Documentation Files Found:** {len(analysis_results['documentation_found'])}",
                f"**Core Code Modules:** {len(analysis_results['code_files_found'])}",
                "\n**Analysis Results:**\n",
                analysis_text
            ]

            return {
                "content": "\n".join(response_parts),
                "metadata": {
                    "type": "self_analysis",
                    "docs_analyzed": len(analysis_results['documentation_found']),
                    "code_files": analysis_results['code_files_found']
                }
            }

        except Exception as e:
            print(f"[Jarvis] Self-analysis error: {e}")
            return {
                "content": f"I encountered an error during self-analysis, sir: {str(e)}",
                "metadata": {"type": "self_analysis", "error": True}
            }

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
                system_prompt=JARVIS_SYSTEM_PROMPT,
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
