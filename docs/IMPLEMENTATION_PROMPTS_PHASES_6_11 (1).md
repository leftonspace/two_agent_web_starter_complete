# System-1.2 Implementation Prompts: Phases 6-11
# Conversational Autonomous Agent Evolution

**Version:** 2.0  
**Date:** November 2025  
**Based on:** SYSTEM_1_2_COMPLETE_ROADMAP.md  
**Target System:** System-1.2 Conversational Autonomous Agent Platform

---

## Table of Contents

1. [Phase 6: Critical Reliability Fixes (Integrated)](#phase-6-critical-reliability-fixes-integrated)
2. [Phase 7: Conversational Agent Mode (Weeks 1-6)](#phase-7-conversational-agent-mode-weeks-1-6)
3. [Phase 8: True Action Execution (Weeks 7-12)](#phase-8-true-action-execution-weeks-7-12)
4. [Phase 9: Local LLM Support (Weeks 13-16)](#phase-9-local-llm-support-weeks-13-16)
5. [Phase 10: Business Memory & Context (Weeks 17-20)](#phase-10-business-memory--context-weeks-17-20)
6. [Phase 11: Production Hardening (Weeks 21-24)](#phase-11-production-hardening-weeks-21-24)

---

## Phase 6: Critical Reliability Fixes (Integrated)

### Overview
**Objective:** Address critical reliability vulnerabilities from original Phase 4.3 analysis

**Note:** These fixes are integrated into Phases 7, 10, and 11 rather than being a standalone phase. Each fix is listed here with its target phase for implementation.

**Reliability Issues:**
- R1: Infinite retry loops (→ Phase 7, Week 2)
- R2: Knowledge graph write contention (→ Phase 10, Week 1)
- R3: LLM timeout fallback (→ Phase 9, Week 3)
- R4: Checkpoint/resume support (→ Phase 11, Week 1)
- R5: Cost tracker instance-based (→ Phase 11, Week 2)
- R6: Workflow enforcement (→ Phase 7, Week 2)
- R7: Job manager atomic writes (→ Phase 11, Week 1)

**Reference:** These fixes are extracted from original Prompt 4.3 and distributed to appropriate implementation phases.

---

## Phase 7: Conversational Agent Mode (Weeks 1-6)

### Overview
**Objective:** Transform System-1.2 from mission-file driven platform to natural language conversational interface

**Timeline:** Weeks 1-6  
**Priority:** P0 (Critical - Core Feature)  
**Success Metrics:**
- ✅ Users can chat naturally (like ChatGPT)
- ✅ Intent parsing >85% accuracy
- ✅ Simple actions execute <10 seconds
- ✅ Complex tasks start <30 seconds
- ✅ All 3 agents visible in real-time
- ✅ User satisfaction >80%

---

### Prompt 7.1: Implement Core Conversational Agent

**Context:**
Current state: System-1.2 requires users to create mission files (`missions/*.json`) and manually trigger execution via CLI (`python -m agent.mission_runner run`) or web dashboard. There is no conversational interface. Users cannot simply say "send an email to john@example.com" or "create a website" and have the agent figure out what to do.

The existing infrastructure provides all necessary building blocks:
- `agent/orchestrator.py` (2,047 lines) - 3-loop execution engine
- `agent/llm.py` (326 lines) - LLM abstraction layer
- `agent/exec_tools.py` (850 lines) - Tool registry
- `agent/model_router.py` (271 lines) - Intelligent model selection

What's missing: A conversational wrapper that accepts natural language input, understands intent, dynamically selects tools, and executes tasks autonomously without requiring pre-defined mission files.

**Task:**
Implement a conversational agent interface that allows users to interact with System-1.2 through natural language. The agent should understand intent, plan execution steps, select appropriate tools, and execute tasks autonomously.

**Requirements:**

1. **Core Conversational Agent Module**
   
   Create `agent/conversational_agent.py` with the following components:

   ```python
   """
   Conversational Agent for System-1.2
   
   Provides natural language interface to the orchestration system.
   Users can chat with the agent to execute tasks, ask questions,
   and build complex systems without writing mission files.
   
   Architecture:
       User Input → Intent Parser → Task Planner → Executor → Response
   
   Usage:
       agent = ConversationalAgent()
       response = await agent.chat("Send an email to john@example.com")
   """
   
   from typing import Dict, List, Any, Optional
   from dataclasses import dataclass, field
   from datetime import datetime
   from enum import Enum
   import asyncio
   import json
   
   from agent.orchestrator import Orchestrator
   from agent.llm import chat_json, chat
   from agent.exec_tools import ToolRegistry
   from agent.config import Config
   from agent.core_logging import log_event
   
   
   class IntentType(Enum):
       """Types of user intents"""
       SIMPLE_ACTION = "simple_action"      # Single tool call
       COMPLEX_TASK = "complex_task"        # Multi-step task
       QUESTION = "question"                # Answer question
       CLARIFICATION = "clarification"      # Need more info
       CONVERSATION = "conversation"        # Casual chat
   
   
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
       timestamp: datetime
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
   
   
   class ConversationalAgent:
       """
       Main conversational agent class.
       
       Handles natural language interaction, intent parsing,
       task planning, and autonomous execution.
       """
       
       def __init__(self, config: Optional[Config] = None):
           """Initialize conversational agent"""
           self.config = config or Config()
           self.conversation_history: List[ConversationMessage] = []
           self.orchestrator = Orchestrator()
           self.tool_registry = ToolRegistry()
           self.active_tasks: Dict[str, TaskExecution] = {}
           self.session_id = self._generate_session_id()
           
           # Load tool metadata for intent parsing
           self.available_tools = self.tool_registry.list_tools()
           self.tool_schemas = {
               tool_name: self.tool_registry.get_tool_schema(tool_name)
               for tool_name in self.available_tools
           }
           
           log_event("conversational_agent_initialized", {
               "session_id": self.session_id,
               "available_tools": len(self.available_tools)
           })
       
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
               log_event("conversational_agent_error", {
                   "error": str(e),
                   "user_message": user_message
               })
               return error_msg
       
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
   - simple_action: Single tool call (send email, query DB)
   - complex_task: Multi-step task (build website, create system)
   - question: User asking for information
   - clarification: Missing parameters
   - conversation: Casual chat
   
   Return JSON:
   {{
       "type": "simple_action|complex_task|question|clarification|conversation",
       "confidence": 0.0-1.0,
       "reasoning": "explain classification",
       "suggested_tool": "tool_name" (if simple_action),
       "complexity": "low|medium|high" (if complex_task),
       "parameters": {{}},
       "requires_approval": true|false,
       "estimated_time_seconds": 30
   }}"""
           
           response = await chat_json(
               messages=[{"role": "user", "content": prompt}],
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
           
           log_event("intent_parsed", {
               "type": intent.type.value,
               "confidence": intent.confidence,
               "tool": intent.suggested_tool
           })
           
           return intent
       
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
               intent.parameters
           )
           
           if missing_params:
               return self._ask_for_parameters(tool_name, missing_params)
           
           # Execute tool
           try:
               result = await self.tool_registry.execute_tool(
                   tool_name,
                   intent.parameters
               )
               
               if result.success:
                   log_event("simple_action_executed", {
                       "tool": tool_name,
                       "parameters": intent.parameters
                   })
                   return self._format_success_response(tool_name, result)
               else:
                   return f"❌ Failed to execute {tool_name}: {result.error}"
                   
           except Exception as e:
               return f"❌ Error executing {tool_name}: {str(e)}"
       
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
           return f"""🤖 I understand! I'll {user_message.lower()}.
   
   📋 Plan:
   {self._format_plan(plan)}
   
   ⏱️ Estimated time: {estimated_time // 60} minutes
   
   🔄 Task ID: {task.task_id}
   I'll work on this and update you. You can continue chatting or ask for status."""
       
       async def _handle_question(self, user_message: str) -> str:
           """Answer user questions"""
           context = self._build_conversation_context(last_n=10)
           
           prompt = f"""You are a helpful AI assistant.
   
   CONVERSATION HISTORY:
   {context}
   
   USER QUESTION: {user_message}
   
   Answer clearly and concisely. Keep under 200 words unless more detail needed."""
           
           response = await chat(
               messages=[{"role": "user", "content": prompt}],
               model="gpt-4o",
               temperature=0.7
           )
           
           return response
       
       # ... Additional helper methods (implementation details)
   ```

2. **Intent Parsing System**
   
   Key methods to implement in `ConversationalAgent`:
   
   - `_parse_intent(message: str) -> Intent`
     - Use LLM to classify user message
     - Extract task complexity, required tools
     - Estimate execution time
     - Determine if approval needed
   
   - `_extract_parameters(tool_name: str, schema: Dict, message: str) -> Dict`
     - Use LLM to pull parameter values from message
     - Use conversation context if needed
     - Return dict of parameter values
   
   - `_check_missing_parameters(schema: Dict, provided: Dict) -> List[str]`
     - Compare required vs provided parameters
     - Return list of missing parameter names
   
   - `_build_conversation_context(last_n: int) -> str`
     - Format recent conversation for prompt inclusion
     - Include last N messages with roles

3. **Task Planning System**
   
   - `_create_execution_plan(task_description: str, intent: Intent) -> Dict`
     - Use LLM to break task into steps
     - Return plan with step descriptions, types, estimated times
     - Example plan structure:
       ```json
       {
         "summary": "Create portfolio website",
         "steps": [
           {
             "step_number": 1,
             "description": "Create project directory",
             "type": "tool_call",
             "tool": "create_directory",
             "estimated_seconds": 5
           },
           {
             "step_number": 2,
             "description": "Generate HTML structure",
             "type": "code_gen",
             "estimated_seconds": 60
           }
         ],
         "total_estimated_seconds": 300
       }
       ```
   
   - `_execute_plan_async(task: TaskExecution)`
     - Background task execution
     - Iterate through steps
     - Log progress
     - Handle failures
     - Update task status

4. **CLI Chat Interface**
   
   Create `agent/cli_chat.py`:
   
   ```python
   """
   Command-line chat interface for conversational agent.
   
   Usage:
       python -m agent.cli_chat
       
   Commands:
       /status - Show active tasks
       /task <id> - Show task details
       /clear - Clear conversation
       /help - Show help
       /exit - Exit chat
   """
   
   import asyncio
   import sys
   from typing import Optional
   
   from agent.conversational_agent import ConversationalAgent
   from agent.config import Config
   
   
   class CLIChat:
       """Command-line chat interface"""
       
       def __init__(self):
           self.agent: Optional[ConversationalAgent] = None
           self.running = False
       
       async def start(self):
           """Start chat session"""
           self.agent = ConversationalAgent()
           self.running = True
           
           self._print_welcome()
           
           while self.running:
               try:
                   user_input = await self._get_input()
                   
                   if user_input.startswith("/"):
                       await self._handle_command(user_input)
                       continue
                   
                   print("\n🤖 Agent: ", end="", flush=True)
                   response = await self.agent.chat(user_input)
                   print(response)
                   print()
                   
               except KeyboardInterrupt:
                   print("\n\n👋 Goodbye!")
                   break
               except Exception as e:
                   print(f"\n❌ Error: {str(e)}\n")
       
       async def _get_input(self) -> str:
           """Get user input (async)"""
           loop = asyncio.get_event_loop()
           return await loop.run_in_executor(None, input, "You: ")
       
       async def _handle_command(self, command: str):
           """Handle special commands"""
           parts = command.split()
           cmd = parts[0].lower()
           
           if cmd in ["/exit", "/quit"]:
               print("👋 Goodbye!")
               self.running = False
           
           elif cmd == "/status":
               tasks = self.agent.get_active_tasks()
               if not tasks:
                   print("No active tasks.\n")
               else:
                   print("\nActive Tasks:")
                   for task in tasks:
                       print(f"  [{task['task_id']}] {task['description']}")
                       print(f"    Status: {task['status']} ({task['progress']})")
                   print()
           
           elif cmd == "/task":
               if len(parts) < 2:
                   print("Usage: /task <task_id>\n")
                   return
               
               task_id = parts[1]
               status = self.agent.get_task_status(task_id)
               
               if not status:
                   print(f"Task {task_id} not found.\n")
               else:
                   print(f"\nTask: {status['description']}")
                   print(f"Status: {status['status']}")
                   print(f"Progress: {status['current_step']}/{status['total_steps']}")
                   if status['error']:
                       print(f"Error: {status['error']}")
                   print()
           
           elif cmd == "/clear":
               self.agent.conversation_history.clear()
               print("Conversation cleared.\n")
           
           elif cmd == "/help":
               self._print_help()
           
           else:
               print(f"Unknown command: {cmd}")
               print("Type /help for available commands.\n")
       
       def _print_welcome(self):
           """Print welcome message"""
           print("\n" + "="*60)
           print("  🤖 System-1.2 Conversational Agent")
           print("="*60)
           print("\nChat with me naturally! I can:")
           print("  • Execute tasks (send emails, create files)")
           print("  • Build systems (websites, APIs, automations)")
           print("  • Answer questions")
           print("  • Automate workflows")
           print("\nCommands: /status /task /clear /help /exit")
           print("="*60 + "\n")
       
       def _print_help(self):
           """Print help message"""
           print("\nAvailable Commands:")
           print("  /status          - Show active tasks")
           print("  /task <id>       - Show task details")
           print("  /clear           - Clear conversation history")
           print("  /help            - Show this help")
           print("  /exit, /quit     - Exit chat\n")
   
   
   async def main():
       """Main entry point"""
       cli = CLIChat()
       await cli.start()
   
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

5. **Web Chat Integration**
   
   Modify `agent/webapp/app.py` to add chat endpoints:
   
   ```python
   # Add to agent/webapp/app.py
   
   from agent.conversational_agent import ConversationalAgent
   
   # Global agent instance (one per server)
   conversational_agent = ConversationalAgent()
   
   @app.post("/api/chat")
   async def chat_endpoint(request: Request):
       """
       Conversational chat endpoint.
       
       POST /api/chat
       Body: {"message": "send email to john@example.com"}
       Response: {"response": "✓ Email sent", "task_id": "task_abc123"}
       """
       data = await request.json()
       message = data.get("message", "")
       
       if not message:
           return JSONResponse({"error": "Message required"}, status_code=400)
       
       try:
           response = await conversational_agent.chat(message)
           
           return JSONResponse({
               "response": response,
               "active_tasks": conversational_agent.get_active_tasks()
           })
       
       except Exception as e:
           return JSONResponse({
               "error": str(e)
           }, status_code=500)
   
   
   @app.get("/api/chat/tasks")
   async def get_active_tasks():
       """Get list of active tasks"""
       return JSONResponse({
           "tasks": conversational_agent.get_active_tasks()
       })
   
   
   @app.get("/api/chat/task/{task_id}")
   async def get_task_status(task_id: str):
       """Get status of specific task"""
       status = conversational_agent.get_task_status(task_id)
       
       if not status:
           return JSONResponse({"error": "Task not found"}, status_code=404)
       
       return JSONResponse(status)
   
   
   @app.get("/chat")
   async def chat_page():
       """Serve chat interface"""
       return FileResponse("agent/webapp/templates/chat.html")
   ```

6. **Web Chat UI**
   
   Create `agent/webapp/templates/chat.html`:
   
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <title>Chat - System-1.2</title>
       <style>
           body {
               font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
               margin: 0;
               padding: 0;
               background: #1a1a1a;
               color: #fff;
           }
           
           .container {
               max-width: 1200px;
               margin: 0 auto;
               padding: 20px;
           }
           
           .chat-container {
               display: flex;
               flex-direction: column;
               height: calc(100vh - 100px);
               background: #2a2a2a;
               border-radius: 10px;
               overflow: hidden;
           }
           
           .chat-header {
               background: #333;
               padding: 20px;
               border-bottom: 2px solid #00ff88;
           }
           
           .chat-messages {
               flex: 1;
               overflow-y: auto;
               padding: 20px;
           }
           
           .message {
               margin-bottom: 20px;
               padding: 15px;
               border-radius: 8px;
               max-width: 80%;
           }
           
           .message.user {
               background: #0066cc;
               margin-left: auto;
           }
           
           .message.assistant {
               background: #333;
               border-left: 4px solid #00ff88;
           }
           
           .chat-input {
               display: flex;
               padding: 20px;
               background: #333;
               border-top: 1px solid #444;
           }
           
           .chat-input input {
               flex: 1;
               padding: 15px;
               background: #1a1a1a;
               border: 1px solid #444;
               border-radius: 5px;
               color: #fff;
               font-size: 16px;
           }
           
           .chat-input button {
               margin-left: 10px;
               padding: 15px 30px;
               background: #00ff88;
               border: none;
               border-radius: 5px;
               color: #000;
               font-weight: bold;
               cursor: pointer;
           }
           
           .chat-input button:hover {
               background: #00dd77;
           }
           
           .typing-indicator {
               padding: 15px;
               color: #888;
               font-style: italic;
           }
       </style>
   </head>
   <body>
       <div class="container">
           <div class="chat-container">
               <div class="chat-header">
                   <h1>🤖 Conversational Agent</h1>
                   <p>Chat naturally - I'll figure out what you need!</p>
               </div>
               
               <div class="chat-messages" id="messages"></div>
               
               <div class="chat-input">
                   <input 
                       type="text" 
                       id="messageInput" 
                       placeholder="Type your message..."
                       onkeypress="if(event.keyCode==13) sendMessage()"
                   />
                   <button onclick="sendMessage()">Send</button>
               </div>
           </div>
       </div>
       
       <script>
           async function sendMessage() {
               const input = document.getElementById('messageInput');
               const message = input.value.trim();
               
               if (!message) return;
               
               addMessage('user', message);
               input.value = '';
               
               showTyping();
               
               try {
                   const response = await fetch('/api/chat', {
                       method: 'POST',
                       headers: {'Content-Type': 'application/json'},
                       body: JSON.stringify({message: message})
                   });
                   
                   const data = await response.json();
                   
                   hideTyping();
                   addMessage('assistant', data.response);
                   
               } catch (error) {
                   hideTyping();
                   addMessage('assistant', '❌ Error: ' + error.message);
               }
           }
           
           function addMessage(role, content) {
               const messagesDiv = document.getElementById('messages');
               const msgDiv = document.createElement('div');
               msgDiv.className = `message ${role}`;
               msgDiv.textContent = content;
               messagesDiv.appendChild(msgDiv);
               messagesDiv.scrollTop = messagesDiv.scrollHeight;
           }
           
           function showTyping() {
               const messagesDiv = document.getElementById('messages');
               const typing = document.createElement('div');
               typing.id = 'typing';
               typing.className = 'typing-indicator';
               typing.textContent = '🤖 Agent is thinking...';
               messagesDiv.appendChild(typing);
               messagesDiv.scrollTop = messagesDiv.scrollHeight;
           }
           
           function hideTyping() {
               const typing = document.getElementById('typing');
               if (typing) typing.remove();
           }
       </script>
   </body>
   </html>
   ```

7. **Testing Suite**
   
   Create `agent/tests/test_conversational_agent.py`:
   
   ```python
   """
   Unit tests for conversational agent.
   
   Run: pytest agent/tests/test_conversational_agent.py -v
   """
   
   import pytest
   import asyncio
   from agent.conversational_agent import ConversationalAgent, IntentType
   
   
   class TestConversationalAgent:
       
       @pytest.fixture
       async def agent(self):
           """Create agent instance for testing"""
           return ConversationalAgent()
       
       @pytest.mark.asyncio
       async def test_simple_question(self, agent):
           """Test answering simple question"""
           response = await agent.chat("What's 2+2?")
           assert "4" in response.lower()
       
       @pytest.mark.asyncio
       async def test_greeting(self, agent):
           """Test conversational greeting"""
           response = await agent.chat("Hello!")
           assert len(response) > 0
           assert any(word in response.lower() for word in ["hello", "hi", "help"])
       
       @pytest.mark.asyncio
       async def test_intent_parsing_simple_action(self, agent):
           """Test intent parsing for simple action"""
           intent = await agent._parse_intent("Send an email to test@example.com")
           assert intent.type == IntentType.SIMPLE_ACTION
           assert intent.confidence > 0.7
       
       @pytest.mark.asyncio
       async def test_intent_parsing_complex_task(self, agent):
           """Test intent parsing for complex task"""
           intent = await agent._parse_intent("Create a website for my restaurant")
           assert intent.type == IntentType.COMPLEX_TASK
           assert intent.confidence > 0.7
           assert intent.complexity in ["medium", "high"]
       
       @pytest.mark.asyncio
       async def test_conversation_history(self, agent):
           """Test conversation history tracking"""
           await agent.chat("Hello")
           await agent.chat("What can you do?")
           
           assert len(agent.conversation_history) == 4  # 2 user + 2 assistant
           assert agent.conversation_history[0].role == "user"
           assert agent.conversation_history[1].role == "assistant"
       
       # Add 5+ more test cases...
   ```

8. **Documentation**
   
   Create `docs/CONVERSATIONAL_AGENT.md` with:
   - Overview and features
   - Usage examples (CLI, Python API, Web)
   - Architecture diagram
   - Configuration options
   - Troubleshooting guide

**Acceptance Criteria:**

- [ ] ConversationalAgent class implemented with all core methods
- [ ] Intent parsing works with >85% accuracy on test cases
- [ ] Simple actions execute correctly (email, database query, file creation)
- [ ] Complex tasks create execution plans and start background jobs
- [ ] Questions answered correctly without execution
- [ ] CLI chat interface functional with all commands
- [ ] Web chat interface accessible at /chat
- [ ] Conversation history tracked across messages
- [ ] Active tasks displayed in real-time
- [ ] API endpoints documented and tested
- [ ] All unit tests pass (minimum 10 test cases)
- [ ] Documentation complete with examples
- [ ] Performance: Intent parsing <3 seconds, simple actions <10 seconds

**Files to Create:**
- `agent/conversational_agent.py` (main agent class, ~800 lines)
- `agent/cli_chat.py` (CLI interface, ~200 lines)
- `agent/webapp/templates/chat.html` (web UI, ~150 lines)
- `agent/tests/test_conversational_agent.py` (test suite, ~300 lines)
- `docs/CONVERSATIONAL_AGENT.md` (documentation, ~500 lines)

**Files to Modify:**
- `agent/webapp/app.py` — Add chat endpoints (`/api/chat`, `/chat`)
- `agent/config.py` — Add ConversationalConfig class
- `README.md` — Add conversational agent section

**References:**
- Current orchestrator: `agent/orchestrator.py:1-2047`
- Tool registry: `agent/exec_tools.py:1-850`
- LLM interface: `agent/llm.py:1-326`
- Mission runner pattern: `agent/mission_runner.py:1-570`

---

### Prompt 7.2: Integrate Manager/Supervisor/Employee into Chat

**Context:**
Current state: The 3-agent loop (Manager → Supervisor → Employee) runs separately in `agent/orchestrator.py` with no visibility during execution. User submits a mission, waits, and gets final result. The quality assurance process (Supervisor reviews, Employee revisions, iterative improvements) is completely hidden.

With conversational agent from Prompt 7.1, users can start tasks naturally, but they still don't see the 3-agent collaboration happening. This defeats one of the core value propositions: showing users that work is being reviewed and refined before delivery.

**Task:**
Stream the Manager/Supervisor/Employee interactions into the chat interface in real-time so users see planning, review, and execution as it happens. Enable agents to ask clarifying questions and request user approval during execution.

**Requirements:**

1. **Agent Messaging System**
   
   Create `agent/agent_messaging.py`:
   
   ```python
   """
   Agent messaging system for streaming agent communications to chat.
   
   Allows Manager/Supervisor/Employee to post messages that appear
   in the conversational chat interface.
   """
   
   from typing import Dict, Any, Optional, Callable
   from dataclasses import dataclass
   from datetime import datetime
   from enum import Enum
   import asyncio
   
   
   class AgentRole(Enum):
       """Agent roles in the system"""
       MANAGER = "manager"
       SUPERVISOR = "supervisor"
       EMPLOYEE = "employee"
   
   
   @dataclass
   class AgentMessage:
       """Message from an agent"""
       role: AgentRole
       content: str
       timestamp: datetime
       metadata: Dict[str, Any]
       requires_response: bool = False  # True if waiting for user input
       response_timeout: Optional[int] = None  # Seconds to wait
   
   
   class AgentMessageBus:
       """
       Message bus for agent-to-user communication.
       
       Agents post messages, which are streamed to chat interface.
       Can wait for user responses when needed.
       """
       
       def __init__(self):
           self.listeners: list[Callable] = []
           self.pending_responses: Dict[str, asyncio.Future] = {}
       
       def subscribe(self, callback: Callable):
           """Subscribe to agent messages"""
           self.listeners.append(callback)
       
       async def post_message(
           self,
           role: AgentRole,
           content: str,
           metadata: Dict[str, Any] = None,
           requires_response: bool = False,
           response_timeout: int = 300
       ) -> Optional[str]:
           """
           Post message from agent.
           
           If requires_response=True, blocks until user responds.
           """
           message = AgentMessage(
               role=role,
               content=content,
               timestamp=datetime.now(),
               metadata=metadata or {},
               requires_response=requires_response,
               response_timeout=response_timeout
           )
           
           # Notify all listeners
           for listener in self.listeners:
               await listener(message)
           
           # Wait for response if needed
           if requires_response:
               message_id = self._generate_message_id()
               future = asyncio.Future()
               self.pending_responses[message_id] = future
               
               try:
                   response = await asyncio.wait_for(
                       future,
                       timeout=response_timeout
                   )
                   return response
               except asyncio.TimeoutError:
                   return None
               finally:
                   del self.pending_responses[message_id]
           
           return None
       
       def provide_response(self, message_id: str, response: str):
           """User provides response to pending message"""
           if message_id in self.pending_responses:
               self.pending_responses[message_id].set_result(response)
       
       def _generate_message_id(self) -> str:
           import uuid
           return str(uuid.uuid4())
   
   
   # Global message bus instance
   agent_message_bus = AgentMessageBus()
   ```

2. **Orchestrator Integration**
   
   Modify `agent/orchestrator.py` to post messages:
   
   ```python
   # Add to agent/orchestrator.py
   
   from agent.agent_messaging import agent_message_bus, AgentRole
   
   class Orchestrator:
       
       async def run(self, task: str, project_path: str, config: Config):
           """Modified run method with message streaming"""
           
           # Manager planning phase
           await agent_message_bus.post_message(
               role=AgentRole.MANAGER,
               content=f"📋 Planning: {task}",
               metadata={"phase": "planning", "iteration": 0}
           )
           
           manager_response = await self._manager_plan(task, context)
           
           await agent_message_bus.post_message(
               role=AgentRole.MANAGER,
               content=f"📝 Plan created:\n{self._format_plan(manager_response)}",
               metadata={"phase": "planning", "plan": manager_response}
           )
           
           # Check if approval needed for high-impact tasks
           if self._requires_approval(manager_response):
               approval = await agent_message_bus.post_message(
                   role=AgentRole.MANAGER,
                   content="⚠️ This task will modify external systems. Proceed? [yes/no]",
                   requires_response=True,
                   response_timeout=300
               )
               
               if approval.lower() != "yes":
                   await agent_message_bus.post_message(
                       role=AgentRole.MANAGER,
                       content="❌ Task cancelled by user"
                   )
                   return {"status": "cancelled"}
           
           # Execution iterations
           for iteration in range(max_iterations):
               
               # Supervisor breakdown
               await agent_message_bus.post_message(
                   role=AgentRole.SUPERVISOR,
                   content=f"🔍 Reviewing plan (iteration {iteration + 1})...",
                   metadata={"phase": "review", "iteration": iteration}
               )
               
               supervisor_tasks = await self._supervisor_breakdown(manager_response)
               
               await agent_message_bus.post_message(
                   role=AgentRole.SUPERVISOR,
                   content=f"✅ Review complete. {len(supervisor_tasks)} tasks identified.",
                   metadata={"tasks": supervisor_tasks}
               )
               
               # Employee execution
               for idx, task in enumerate(supervisor_tasks):
                   await agent_message_bus.post_message(
                       role=AgentRole.EMPLOYEE,
                       content=f"🛠️ Working on: {task['description']} ({idx+1}/{len(supervisor_tasks)})",
                       metadata={"task": task, "progress": f"{idx+1}/{len(supervisor_tasks)}"}
                   )
                   
                   result = await self._employee_execute(task)
                   
                   if result.success:
                       await agent_message_bus.post_message(
                           role=AgentRole.EMPLOYEE,
                           content=f"✅ Completed: {task['description']}",
                           metadata={"task": task, "result": result}
                       )
                   else:
                       await agent_message_bus.post_message(
                           role=AgentRole.EMPLOYEE,
                           content=f"⚠️ Issue with: {task['description']} - {result.error}",
                           metadata={"task": task, "error": result.error}
                       )
               
               # Supervisor review of execution
               await agent_message_bus.post_message(
                   role=AgentRole.SUPERVISOR,
                   content="🔍 Reviewing execution results...",
                   metadata={"phase": "validation"}
               )
               
               validation = await self._supervisor_validate(results)
               
               if validation["approved"]:
                   await agent_message_bus.post_message(
                       role=AgentRole.SUPERVISOR,
                       content="✅ All tasks completed successfully!",
                       metadata={"approved": True}
                   )
                   break
               else:
                   await agent_message_bus.post_message(
                       role=AgentRole.SUPERVISOR,
                       content=f"⚠️ Issues found. Requesting revisions:\n{validation['feedback']}",
                       metadata={"approved": False, "feedback": validation['feedback']}
                   )
   ```

3. **ConversationalAgent Integration**
   
   Modify `agent/conversational_agent.py` to listen for agent messages:
   
   ```python
   # Add to ConversationalAgent class
   
   from agent.agent_messaging import agent_message_bus, AgentMessage, AgentRole
   
   class ConversationalAgent:
       
       def __init__(self, config: Optional[Config] = None):
           # ... existing init code ...
           
           # Subscribe to agent messages
           agent_message_bus.subscribe(self._handle_agent_message)
           
           # Track pending agent responses
           self.pending_agent_messages: List[AgentMessage] = []
       
       async def _handle_agent_message(self, message: AgentMessage):
           """
           Handle messages from Manager/Supervisor/Employee.
           
           Stream to chat interface and store for display.
           """
           # Format message with agent role
           role_emoji = {
               AgentRole.MANAGER: "👔",
               AgentRole.SUPERVISOR: "🔍",
               AgentRole.EMPLOYEE: "🛠️"
           }
           
           formatted = f"{role_emoji[message.role]} {message.role.value.title()}: {message.content}"
           
           # Add to conversation history
           self._add_message("assistant", formatted, metadata={
               "agent_role": message.role.value,
               "agent_message": True
           })
           
           # If requires response, track it
           if message.requires_response:
               self.pending_agent_messages.append(message)
       
       async def _handle_complex_task(self, intent: Intent, user_message: str) -> str:
           """
           Modified to use orchestrator with message streaming.
           """
           # Start orchestrator (will stream messages via message bus)
           result = await self.orchestrator.run(
               task=user_message,
               project_path=f"./sites/{self._generate_project_name(user_message)}",
               config=self.config
           )
           
           # Return summary (detailed updates already streamed)
           return f"✅ Task completed! {result.get('summary', '')}"
   ```

4. **Web UI Updates for Agent Visibility**
   
   Update `agent/webapp/templates/chat.html` to show agent roles:
   
   ```html
   <style>
       .message.manager {
           background: #1a4d7a;
           border-left: 4px solid #2196F3;
       }
       
       .message.supervisor {
           background: #7a4d1a;
           border-left: 4px solid #FF9800;
       }
       
       .message.employee {
           background: #1a7a4d;
           border-left: 4px solid #4CAF50;
       }
       
       .agent-icon {
           display: inline-block;
           margin-right: 8px;
           font-size: 20px;
       }
   </style>
   
   <script>
       function addMessage(role, content, metadata = {}) {
           const messagesDiv = document.getElementById('messages');
           const msgDiv = document.createElement('div');
           
           // Determine CSS class
           let cssClass = `message ${role}`;
           if (metadata.agent_role) {
               cssClass = `message ${metadata.agent_role}`;
           }
           
           msgDiv.className = cssClass;
           
           // Add agent icon if agent message
           if (metadata.agent_message) {
               const icons = {
                   'manager': '👔',
                   'supervisor': '🔍',
                   'employee': '🛠️'
               };
               const icon = icons[metadata.agent_role] || '';
               msgDiv.innerHTML = `<span class="agent-icon">${icon}</span>${content}`;
           } else {
               msgDiv.textContent = content;
           }
           
           messagesDiv.appendChild(msgDiv);
           messagesDiv.scrollTop = messagesDiv.scrollHeight;
       }
       
       // Poll for new messages (alternative: WebSocket)
       setInterval(async () => {
           try {
               const response = await fetch('/api/chat/stream');
               const data = await response.json();
               
               for (const msg of data.new_messages) {
                   addMessage('assistant', msg.content, msg.metadata);
               }
           } catch (error) {
               console.error('Failed to fetch messages:', error);
           }
       }, 1000);
   </script>
   ```

5. **Infinite Loop Prevention (R1 Reliability Fix)**
   
   Add to `agent/orchestrator.py`:
   
   ```python
   class Orchestrator:
       
       def __init__(self):
           # ... existing init ...
           self.retry_history: List[Dict] = []
       
       async def _check_infinite_loop(self, feedback: str) -> bool:
           """
           Detect if agent is stuck in infinite retry loop.
           
           R1 Fix: If same feedback appears 2+ times consecutively,
           force escalation instead of retrying.
           """
           self.retry_history.append({
               "feedback": feedback,
               "timestamp": datetime.now()
           })
           
           # Keep only last 5 retries
           self.retry_history = self.retry_history[-5:]
           
           # Check for consecutive identical feedback
           if len(self.retry_history) >= 2:
               last_two = self.retry_history[-2:]
               if last_two[0]["feedback"] == last_two[1]["feedback"]:
                   await agent_message_bus.post_message(
                       role=AgentRole.SUPERVISOR,
                       content="⚠️ Detected retry loop. Escalating to human review.",
                       metadata={"loop_detected": True}
                   )
                   return True
           
           return False
   ```

6. **Workflow Enforcement (R6 Reliability Fix)**
   
   Add to `agent/config.py`:
   
   ```python
   class WorkflowConfig:
       """Workflow enforcement settings"""
       enforcement_mode: str = "strict"  # "strict", "warn", "disabled"
       block_on_failure: bool = True
       require_supervisor_approval: bool = True
   ```
   
   Add to `agent/orchestrator.py`:
   
   ```python
   async def _execute_employee_tasks(self, tasks: List[Dict]) -> List[Dict]:
       """
       Execute employee tasks with workflow enforcement.
       
       R6 Fix: Block file writes if workflow validation fails.
       """
       results = []
       
       for task in tasks:
           # Execute task
           result = await self._employee_execute(task)
           
           # Validate with supervisor
           validation = await self._supervisor_validate_single(task, result)
           
           # Enforce workflow
           if not validation["approved"]:
               if self.config.workflow.enforcement_mode == "strict":
                   # Block file writes
                   if result.get("files_modified"):
                       await self._rollback_files(result["files_modified"])
                       
                       await agent_message_bus.post_message(
                           role=AgentRole.SUPERVISOR,
                           content=f"❌ Blocked file writes. Validation failed: {validation['reason']}",
                           metadata={"blocked": True}
                       )
                   
                   result["blocked"] = True
           
           results.append(result)
       
       return results
   ```

7. **Testing**
   
   Create `agent/tests/test_agent_messaging.py`:
   
   ```python
   """Test agent messaging and 3-agent integration"""
   
   import pytest
   import asyncio
   from agent.agent_messaging import agent_message_bus, AgentRole
   from agent.conversational_agent import ConversationalAgent
   
   
   @pytest.mark.asyncio
   async def test_agent_message_streaming():
       """Test messages stream to chat"""
       messages_received = []
       
       async def listener(msg):
           messages_received.append(msg)
       
       agent_message_bus.subscribe(listener)
       
       await agent_message_bus.post_message(
           role=AgentRole.MANAGER,
           content="Planning task"
       )
       
       await asyncio.sleep(0.1)
       
       assert len(messages_received) == 1
       assert messages_received[0].role == AgentRole.MANAGER
   
   
   @pytest.mark.asyncio
   async def test_agent_requires_response():
       """Test agent can ask for user input"""
       async def responder(msg):
           if msg.requires_response:
               agent_message_bus.provide_response(msg.message_id, "yes")
       
       agent_message_bus.subscribe(responder)
       
       response = await agent_message_bus.post_message(
           role=AgentRole.MANAGER,
           content="Proceed?",
           requires_response=True,
           response_timeout=5
       )
       
       assert response == "yes"
   
   
   @pytest.mark.asyncio
   async def test_infinite_loop_detection():
       """Test R1 fix: infinite loop prevention"""
       orchestrator = Orchestrator()
       
       # Simulate same feedback twice
       orchestrator.retry_history = [
           {"feedback": "fix error X", "timestamp": datetime.now()},
           {"feedback": "fix error X", "timestamp": datetime.now()}
       ]
       
       is_loop = await orchestrator._check_infinite_loop("fix error X")
       assert is_loop is True
   ```

**Acceptance Criteria:**

- [ ] Agent messages stream to chat in real-time
- [ ] Manager planning visible to user
- [ ] Supervisor reviews visible to user
- [ ] Employee execution updates visible to user
- [ ] Agent roles distinguished visually (colors, icons)
- [ ] Agents can ask clarifying questions
- [ ] User can approve/reject during execution
- [ ] Infinite loop detection works (R1 fix)
- [ ] Workflow enforcement works (R6 fix)
- [ ] All tests pass (minimum 15 test cases)
- [ ] Performance: Message streaming <100ms latency

**Files to Create:**
- `agent/agent_messaging.py` (message bus, ~300 lines)
- `agent/tests/test_agent_messaging.py` (tests, ~200 lines)

**Files to Modify:**
- `agent/orchestrator.py` — Add message streaming throughout
- `agent/conversational_agent.py` — Subscribe to agent messages
- `agent/webapp/templates/chat.html` — Add agent role styling
- `agent/config.py` — Add WorkflowConfig

**References:**
- Original orchestrator: `agent/orchestrator.py:1-2047`
- Reliability issue R1: Infinite loops
- Reliability issue R6: Workflow enforcement

---

### Prompt 7.3: Implement Business Memory System

**Context:**
Current state: ConversationalAgent from Prompt 7.1 forgets everything between sessions. If user says "send report to the team" in one conversation, then says it again tomorrow, agent must re-ask "who is the team?" every time.

This defeats the purpose of an AI "employee" - real employees remember context about the business, team members, common workflows, and user preferences. Without memory, the conversational agent feels like a stateless chatbot rather than a persistent assistant.

**Task:**
Implement a persistent business memory system that automatically learns facts about the user's business, team, preferences, and common workflows from conversations. The agent should use this context automatically in future interactions.

**Requirements:**

1. **Memory Database Schema**
   
   Create `agent/business_memory/schema.py`:
   
   ```python
   """
   Business memory database schema.
   
   Stores structured information about user's business
   learned from conversations.
   """
   
   import sqlite3
   from datetime import datetime
   from typing import Dict, Any, List, Optional
   
   
   class MemoryDatabase:
       """Database for business memory"""
       
       def __init__(self, db_path: str = "data/business_memory.db"):
           self.db_path = db_path
           self.conn = sqlite3.connect(db_path)
           self._init_schema()
       
       def _init_schema(self):
           """Initialize database schema"""
           cursor = self.conn.cursor()
           
           # Company information
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS company_info (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   key TEXT NOT NULL UNIQUE,
                   value TEXT NOT NULL,
                   confidence REAL DEFAULT 1.0,
                   source TEXT,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)
           
           # Team members
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS team_members (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   email TEXT UNIQUE,
                   role TEXT,
                   department TEXT,
                   metadata JSON,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)
           
           # Projects
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS projects (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   description TEXT,
                   status TEXT DEFAULT 'active',
                   path TEXT,
                   metadata JSON,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)
           
           # User preferences
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS preferences (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   category TEXT NOT NULL,
                   key TEXT NOT NULL,
                   value TEXT NOT NULL,
                   confidence REAL DEFAULT 1.0,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   UNIQUE(category, key)
               )
           """)
           
           # Integration credentials (encrypted)
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS integrations (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   service_name TEXT NOT NULL UNIQUE,
                   credentials_encrypted TEXT NOT NULL,
                   metadata JSON,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)
           
           # Generic facts
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS facts (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   category TEXT NOT NULL,
                   fact TEXT NOT NULL,
                   confidence REAL DEFAULT 0.8,
                   source TEXT,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   expires_at TIMESTAMP
               )
           """)
           
           # Relationships between entities
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS relationships (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   entity1_type TEXT NOT NULL,
                   entity1_id INTEGER NOT NULL,
                   relationship_type TEXT NOT NULL,
                   entity2_type TEXT NOT NULL,
                   entity2_id INTEGER NOT NULL,
                   metadata JSON,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
           """)
           
           # Full-text search index
           cursor.execute("""
               CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts 
               USING fts5(category, fact, content='facts', content_rowid='id')
           """)
           
           self.conn.commit()
   ```

2. **Automatic Fact Extraction**
   
   Create `agent/business_memory/extractor.py`:
   
   ```python
   """
   Automatic fact extraction from conversations.
   
   Uses LLM to identify and extract business facts from
   user messages without explicit commands.
   """
   
   from typing import List, Dict, Any
   from agent.llm import chat_json
   
   
   class FactExtractor:
       """Extract facts from conversation messages"""
       
       async def extract_facts(
           self,
           message: str,
           conversation_context: List[Dict] = None
       ) -> List[Dict[str, Any]]:
           """
           Extract structured facts from user message.
           
           Returns list of facts with type, key, value, confidence.
           """
           context_str = ""
           if conversation_context:
               context_str = "\n".join([
                   f"{msg['role']}: {msg['content']}"
                   for msg in conversation_context[-5:]
               ])
           
           prompt = f"""Extract business facts from this conversation.
   
   CONTEXT:
   {context_str}
   
   CURRENT MESSAGE: "{message}"
   
   Extract any of the following fact types:
   
   1. COMPANY INFO
      - company.name: "Acme Corp"
      - company.industry: "Software"
      - company.size: "50 employees"
   
   2. TEAM MEMBERS
      - person.name: "John Doe"
      - person.email: "john@acme.com"
      - person.role: "CFO"
   
   3. PREFERENCES
      - preference.tool: "Slack" (for communication)
      - preference.style: "professional" (email tone)
      - preference.hosting: "Vercel"
   
   4. PROJECTS
      - project.name: "Website Redesign"
      - project.status: "in progress"
   
   5. INTEGRATIONS
      - integration.service: "GitHub"
      - integration.account: "@acmecorp"
   
   Return JSON array of facts:
   [
     {{
       "type": "company|person|preference|project|integration|other",
       "category": "company.name",
       "value": "Acme Corp",
       "confidence": 0.9,
       "reasoning": "User explicitly stated company name"
     }}
   ]
   
   Only extract explicit facts. Don't infer or assume.
   Confidence: 1.0 = explicit, 0.8 = strong implication, 0.6 = weak implication.
   """
           
           response = await chat_json(
               messages=[{"role": "user", "content": prompt}],
               model="gpt-4o",
               temperature=0.1
           )
           
           return response if isinstance(response, list) else []
       
       async def detect_conflicts(
           self,
           new_fact: Dict,
           existing_facts: List[Dict]
       ) -> Optional[Dict]:
           """
           Detect if new fact conflicts with existing facts.
           
           Returns conflicting fact if found, None otherwise.
           """
           for existing in existing_facts:
               if (existing["category"] == new_fact["category"] and
                   existing["value"] != new_fact["value"]):
                   return existing
           
           return None
   ```

3. **Memory Manager**
   
   Create `agent/business_memory/manager.py`:
   
   ```python
   """
   Business memory manager.
   
   High-level interface for storing and retrieving business knowledge.
   """
   
   from typing import List, Dict, Any, Optional
   from datetime import datetime, timedelta
   
   from agent.business_memory.schema import MemoryDatabase
   from agent.business_memory.extractor import FactExtractor
   from agent.llm import chat_json
   
   
   class BusinessMemory:
       """Manage business knowledge"""
       
       def __init__(self, db_path: str = "data/business_memory.db"):
           self.db = MemoryDatabase(db_path)
           self.extractor = FactExtractor()
       
       async def learn_from_conversation(
           self,
           user_message: str,
           conversation_context: List[Dict] = None
       ):
           """
           Automatically extract and store facts from conversation.
           
           Called after each user message to learn continuously.
           """
           # Extract facts
           facts = await self.extractor.extract_facts(
               user_message,
               conversation_context
           )
           
           # Store each fact
           for fact in facts:
               await self._store_fact(fact)
       
       async def _store_fact(self, fact: Dict):
           """Store a single fact with conflict resolution"""
           # Check for conflicts
           existing = await self._get_facts(fact["category"])
           conflict = await self.extractor.detect_conflicts(fact, existing)
           
           if conflict:
               # Ask user which is correct
               # (This would be handled by ConversationalAgent)
               # For now, prefer higher confidence
               if fact["confidence"] > conflict["confidence"]:
                   await self._update_fact(fact)
           else:
               await self._insert_fact(fact)
       
       async def get_context_for_query(self, query: str) -> Dict[str, Any]:
           """
           Get relevant context for a user query.
           
           Example:
               query: "Send report to the team"
               returns: {
                   "team_emails": ["alice@...", "bob@..."],
                   "report_location": "/reports/Q4.pdf"
               }
           """
           # Use LLM to understand what context is needed
           context_prompt = f"""User query: "{query}"
           
           What business context would help fulfill this request?
           
           Return JSON:
           {{
             "needed": ["team_members", "project_info", "preferences"],
             "reasoning": "User mentioned 'team' so need team emails"
           }}"""
           
           needed = await chat_json(
               messages=[{"role": "user", "content": context_prompt}],
               model="gpt-4o-mini",
               temperature=0.1
           )
           
           # Retrieve relevant facts
           context = {}
           
           if "team_members" in needed.get("needed", []):
               context["team"] = await self.get_team_members()
           
           if "preferences" in needed.get("needed", []):
               context["preferences"] = await self.get_preferences()
           
           if "project_info" in needed.get("needed", []):
               context["projects"] = await self.get_active_projects()
           
           return context
       
       async def get_team_members(self) -> List[Dict]:
           """Get all team members"""
           cursor = self.db.conn.cursor()
           cursor.execute("""
               SELECT name, email, role, department
               FROM team_members
           """)
           
           return [
               {
                   "name": row[0],
                   "email": row[1],
                   "role": row[2],
                   "department": row[3]
               }
               for row in cursor.fetchall()
           ]
       
       async def get_preferences(self, category: str = None) -> Dict[str, str]:
           """Get user preferences"""
           cursor = self.db.conn.cursor()
           
           if category:
               cursor.execute("""
                   SELECT key, value FROM preferences
                   WHERE category = ?
               """, (category,))
           else:
               cursor.execute("SELECT key, value FROM preferences")
           
           return {row[0]: row[1] for row in cursor.fetchall()}
       
       async def search_facts(self, query: str) -> List[Dict]:
           """Full-text search across all facts"""
           cursor = self.db.conn.cursor()
           cursor.execute("""
               SELECT f.category, f.fact, f.confidence
               FROM facts f
               JOIN facts_fts ON facts_fts.rowid = f.id
               WHERE facts_fts MATCH ?
               ORDER BY f.confidence DESC
               LIMIT 10
           """, (query,))
           
           return [
               {
                   "category": row[0],
                   "fact": row[1],
                   "confidence": row[2]
               }
               for row in cursor.fetchall()
           ]
       
       # Additional methods: update_fact, delete_fact, export_data, etc.
   ```

4. **ConversationalAgent Integration**
   
   Modify `agent/conversational_agent.py`:
   
   ```python
   # Add to ConversationalAgent class
   
   from agent.business_memory.manager import BusinessMemory
   
   class ConversationalAgent:
       
       def __init__(self, config: Optional[Config] = None):
           # ... existing init ...
           self.business_memory = BusinessMemory()
       
       async def chat(self, user_message: str) -> str:
           """Modified chat with memory learning"""
           self._add_message("user", user_message)
           
           try:
               # Get relevant context from memory
               context = await self.business_memory.get_context_for_query(user_message)
               
               # Parse intent with context
               intent = await self._parse_intent(user_message, context)
               
               # Handle request...
               response = await self._handle_request(intent, user_message, context)
               
               # Learn from this conversation
               await self.business_memory.learn_from_conversation(
                   user_message,
                   self.conversation_history[-5:]
               )
               
               self._add_message("assistant", response)
               return response
               
           except Exception as e:
               # ... error handling ...
       
       async def _parse_intent(
           self,
           message: str,
           context: Dict = None
       ) -> Intent:
           """Modified intent parsing with memory context"""
           
           conversation_context = self._build_conversation_context(last_n=5)
           
           # Include memory context in prompt
           context_str = ""
           if context:
               context_str = f"\nRELEVANT CONTEXT FROM MEMORY:\n{json.dumps(context, indent=2)}\n"
           
           prompt = f"""Analyze user request with business context.
   
   CONVERSATION HISTORY:
   {conversation_context}
   {context_str}
   CURRENT MESSAGE: "{message}"
   
   AVAILABLE TOOLS:
   {json.dumps(self._get_tool_summary(), indent=2)}
   
   Use the context from memory to enrich your understanding.
   For example, if context shows team members, you don't need to ask "who is the team?"
   
   Return JSON classification...
   """
           
           # ... rest of intent parsing ...
   ```

5. **Memory Management Commands**
   
   Add memory commands to conversational agent:
   
   ```python
   # Add to ConversationalAgent class
   
   async def _handle_memory_command(self, command: str) -> str:
       """Handle memory-related commands"""
       
       if command.startswith("remember that"):
           # Manual fact storage
           fact = command.replace("remember that", "").strip()
           await self.business_memory.store_manual_fact(fact)
           return f"✓ I'll remember: {fact}"
       
       elif command.startswith("forget about"):
           # Delete facts
           topic = command.replace("forget about", "").strip()
           deleted = await self.business_memory.delete_facts_about(topic)
           return f"✓ Forgot {deleted} facts about {topic}"
       
       elif command == "what do you know about me?":
           # Show stored facts
           facts = await self.business_memory.get_all_facts()
           return self._format_facts_summary(facts)
       
       elif command == "clear my data":
           # Delete all memory
           await self.business_memory.clear_all()
           return "✓ All memory cleared"
       
       return "Unknown memory command"
   ```

6. **Privacy & Consent**
   
   Add to `agent/config.py`:
   
   ```python
   class MemoryConfig:
       """Business memory settings"""
       enabled: bool = True
       auto_learn: bool = True
       categories_enabled: Dict[str, bool] = {
           "company": True,
           "team": True,
           "preferences": True,
           "projects": True,
           "integrations": True
       }
       retention_days: int = 180  # Auto-delete after 6 months
       sensitive_data_filter: bool = True  # Block SSN, credit cards, etc.
   ```
   
   Create `agent/business_memory/privacy.py`:
   
   ```python
   """Privacy controls for business memory"""
   
   import re
   from typing import Optional
   
   
   class PrivacyFilter:
       """Filter sensitive data from memory"""
       
       SENSITIVE_PATTERNS = {
           "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
           "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
           "password": r"password[:\s]+\S+",
           "api_key": r"(sk-|pk_live_|pk_test_)\w+"
       }
       
       def contains_sensitive_data(self, text: str) -> Optional[str]:
           """Check if text contains sensitive data"""
           for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
               if re.search(pattern, text, re.IGNORECASE):
                   return pattern_name
           return None
       
       def should_store(self, fact: Dict) -> bool:
           """Determine if fact should be stored"""
           value = fact.get("value", "")
           
           if self.contains_sensitive_data(value):
               return False
           
           return True
   ```

7. **Knowledge Graph Integration (R2 Reliability Fix)**
   
   Modify `agent/knowledge_graph.py` to add write queue:
   
   ```python
   # Add to agent/knowledge_graph.py
   
   import asyncio
   from queue import Queue
   from threading import Thread
   
   class KnowledgeGraph:
       
       def __init__(self, db_path: str):
           self.db_path = db_path
           self.conn = sqlite3.connect(db_path, check_same_thread=False)
           
           # R2 Fix: Write queue to prevent database lock contention
           self.write_queue: Queue = Queue()
           self.writer_thread = Thread(target=self._write_worker, daemon=True)
           self.writer_thread.start()
       
       def _write_worker(self):
           """
           Background worker that processes write queue.
           
           R2 Fix: Batch writes to reduce lock contention.
           """
           while True:
               # Collect writes for 100ms
               writes = []
               deadline = time.time() + 0.1
               
               while time.time() < deadline:
                   try:
                       write = self.write_queue.get(timeout=0.01)
                       writes.append(write)
                   except:
                       break
               
               if writes:
                   # Execute all writes in single transaction
                   cursor = self.conn.cursor()
                   cursor.execute("BEGIN")
                   
                   try:
                       for write_op in writes:
                           write_op["execute"](cursor)
                       cursor.execute("COMMIT")
                   except Exception as e:
                       cursor.execute("ROLLBACK")
                       print(f"Write batch failed: {e}")
       
       def add_entity_async(self, entity_type: str, name: str, metadata: Dict):
           """
           Async entity addition via write queue.
           
           R2 Fix: No blocking on database lock.
           """
           def execute(cursor):
               cursor.execute("""
                   INSERT INTO entities (type, name, metadata)
                   VALUES (?, ?, ?)
               """, (entity_type, name, json.dumps(metadata)))
           
           self.write_queue.put({"execute": execute})
   ```

8. **Testing**
   
   Create `agent/tests/test_business_memory.py`:
   
   ```python
   """Tests for business memory system"""
   
   import pytest
   import asyncio
   from agent.business_memory.manager import BusinessMemory
   from agent.business_memory.extractor import FactExtractor
   
   
   @pytest.mark.asyncio
   async def test_fact_extraction():
       """Test extracting facts from message"""
       extractor = FactExtractor()
       
       message = "My company is Acme Corp and we're in the software industry"
       facts = await extractor.extract_facts(message)
       
       assert len(facts) >= 2
       assert any(f["category"] == "company.name" for f in facts)
       assert any(f["value"] == "Acme Corp" for f in facts)
   
   
   @pytest.mark.asyncio
   async def test_team_member_memory():
       """Test storing and retrieving team members"""
       memory = BusinessMemory(":memory:")
       
       await memory.store_team_member({
           "name": "Alice",
           "email": "alice@acme.com",
           "role": "Engineer"
       })
       
       team = await memory.get_team_members()
       assert len(team) == 1
       assert team[0]["name"] == "Alice"
   
   
   @pytest.mark.asyncio
   async def test_context_retrieval():
       """Test getting relevant context for query"""
       memory = BusinessMemory(":memory:")
       
       # Store some facts
       await memory.store_team_member({
           "name": "Bob",
           "email": "bob@acme.com"
       })
       
       # Query for context
       context = await memory.get_context_for_query("Send email to the team")
       
       assert "team" in context
       assert len(context["team"]) > 0
   
   
   @pytest.mark.asyncio
   async def test_privacy_filter():
       """Test sensitive data is not stored"""
       from agent.business_memory.privacy import PrivacyFilter
       
       filter = PrivacyFilter()
       
       # Should block SSN
       assert filter.contains_sensitive_data("My SSN is 123-45-6789")
       
       # Should block credit card
       assert filter.contains_sensitive_data("Card: 4111 1111 1111 1111")
       
       # Should allow normal data
       assert filter.contains_sensitive_data("Company is Acme Corp") is None
   ```

**Acceptance Criteria:**

- [ ] Memory database schema created
- [ ] Automatic fact extraction works
- [ ] Facts stored correctly with confidence scores
- [ ] Context retrieval provides relevant facts for queries
- [ ] Team member recognition works ("the team" → email list)
- [ ] Preferences applied automatically
- [ ] Memory commands work (remember, forget, show, clear)
- [ ] Privacy filter blocks sensitive data
- [ ] Conflict resolution asks user for clarification
- [ ] Knowledge graph write queue prevents lock contention (R2 fix)
- [ ] GDPR-compliant data export/deletion
- [ ] All tests pass (minimum 20 test cases)
- [ ] Documentation complete

**Files to Create:**
- `agent/business_memory/schema.py` (~200 lines)
- `agent/business_memory/extractor.py` (~250 lines)
- `agent/business_memory/manager.py` (~400 lines)
- `agent/business_memory/privacy.py` (~150 lines)
- `agent/tests/test_business_memory.py` (~300 lines)

**Files to Modify:**
- `agent/conversational_agent.py` — Integrate memory system
- `agent/knowledge_graph.py` — Add write queue (R2 fix)
- `agent/config.py` — Add MemoryConfig

**References:**
- Reliability issue R2: Database lock contention
- GDPR compliance requirements
- Privacy best practices

---

### Prompt 7.4: Implement Action Execution Tools

**Context:**
Current state: ConversationalAgent can understand requests and plan tasks, but cannot execute real-world actions like buying domains, deploying websites, sending SMS, or provisioning servers. It can only work with local files and existing integrations (databases, BambooHR).

This limitation means users still can't say "create a website and put it online" and have it actually happen. The agent generates code but doesn't deploy. It plans to buy a domain but doesn't execute the purchase.

**Task:**
Implement action execution tools that interact with external services (Namecheap, Vercel, Twilio, Stripe, AWS) to perform real-world actions. Include approval workflows for paid actions and audit logging for all executions.

**Requirements:**

1. **Action Tool Base Class**
   
   Create `agent/tools/actions/base.py`:
   
   ```python
   """
   Base class for action tools that interact with external services.
   
   Action tools can:
   - Execute paid operations (domain purchases, server provisioning)
   - Modify external systems (deploy websites, create databases)
   - Send notifications (email, SMS, push)
   
   All actions require audit logging and may require user approval.
   """
   
   from typing import Dict, Any, Optional
   from dataclasses import dataclass
   from abc import ABC, abstractmethod
   from enum import Enum
   
   from agent.tools.base import ToolPlugin, ToolResult, ToolExecutionContext
   from agent.core_logging import log_event
   
   
   class ActionRisk(Enum):
       """Risk level of action"""
       LOW = "low"          # Read-only, no cost
       MEDIUM = "medium"    # Modifies data, low cost (<$10)
       HIGH = "high"        # High cost or irreversible
       CRITICAL = "critical"  # Security impact or very expensive
   
   
   @dataclass
   class ActionApproval:
       """Approval request for action"""
       action_name: str
       description: str
       cost_usd: Optional[float]
       risk_level: ActionRisk
       details: Dict[str, Any]
       requires_2fa: bool = False
   
   
   class ActionTool(ToolPlugin):
       """
       Base class for action execution tools.
       
       Provides:
       - Cost estimation before execution
       - User approval workflow
       - Rollback support
       - Audit logging
       """
       
       @abstractmethod
       async def estimate_cost(self, params: Dict[str, Any]) -> float:
           """
           Estimate cost in USD before execution.
           
           Returns 0.0 for free actions.
           """
           pass
       
       @abstractmethod
       async def execute_action(
           self,
           params: Dict[str, Any],
           context: ToolExecutionContext
       ) -> ToolResult:
           """
           Execute the actual action.
           
           Called only after approval granted.
           """
           pass
       
       @abstractmethod
       async def rollback(
           self,
           execution_id: str,
           context: ToolExecutionContext
       ) -> bool:
           """
           Attempt to rollback/undo action.
           
           Returns True if rollback successful.
           """
           pass
       
       async def execute(
           self,
           params: Dict[str, Any],
           context: ToolExecutionContext
       ) -> ToolResult:
           """
           Main execution with approval workflow.
           
           Orchestrates: cost estimation → approval → execution → audit log
           """
           # Step 1: Estimate cost
           cost = await self.estimate_cost(params)
           
           # Step 2: Determine risk level
           risk = self._assess_risk(params, cost)
           
           # Step 3: Get approval if needed
           if risk in [ActionRisk.MEDIUM, ActionRisk.HIGH, ActionRisk.CRITICAL]:
               approval = await self._request_approval(
                   ActionApproval(
                       action_name=self.get_manifest().name,
                       description=self._format_approval_message(params),
                       cost_usd=cost,
                       risk_level=risk,
                       details=params,
                       requires_2fa=(risk == ActionRisk.CRITICAL)
                   ),
                   context
               )
               
               if not approval:
                   log_event("action_declined", {
                       "action": self.get_manifest().name,
                       "cost": cost,
                       "risk": risk.value
                   })
                   return ToolResult(
                       success=False,
                       error="Action declined by user"
                   )
           
           # Step 4: Execute action
           try:
               result = await self.execute_action(params, context)
               
               # Step 5: Audit log
               await self._audit_log(params, result, cost, context)
               
               return result
               
           except Exception as e:
               log_event("action_failed", {
                   "action": self.get_manifest().name,
                   "error": str(e)
               })
               return ToolResult(success=False, error=str(e))
       
       async def _request_approval(
           self,
           approval: ActionApproval,
           context: ToolExecutionContext
       ) -> bool:
           """
           Request user approval via agent messaging system.
           
           Returns True if approved, False if declined.
           """
           from agent.agent_messaging import agent_message_bus, AgentRole
           
           # Format approval message
           message = self._format_approval_message(approval)
           
           # Request via message bus
           response = await agent_message_bus.post_message(
               role=AgentRole.MANAGER,
               content=message,
               metadata={
                   "type": "approval_request",
                   "cost": approval.cost_usd,
                   "risk": approval.risk_level.value
               },
               requires_response=True,
               response_timeout=300  # 5 minutes
           )
           
           return response and response.lower() in ["yes", "approve", "y"]
       
       def _format_approval_message(self, approval: ActionApproval) -> str:
           """Format user-friendly approval message"""
           msg = f"⚠️ Action Approval Required\n\n"
           msg += f"Action: {approval.action_name}\n"
           msg += f"Description: {approval.description}\n"
           
           if approval.cost_usd and approval.cost_usd > 0:
               msg += f"Cost: ${approval.cost_usd:.2f}\n"
           
           msg += f"Risk Level: {approval.risk_level.value}\n\n"
           msg += "Approve? [yes/no]"
           
           return msg
       
       async def _audit_log(
           self,
           params: Dict,
           result: ToolResult,
           cost: float,
           context: ToolExecutionContext
       ):
           """Log action execution to audit trail"""
           log_event("action_executed", {
               "action": self.get_manifest().name,
               "params": params,
               "success": result.success,
               "cost": cost,
               "user_id": context.user_id,
               "timestamp": datetime.now().isoformat()
           })
       
       def _assess_risk(self, params: Dict, cost: float) -> ActionRisk:
           """Assess risk level of action"""
           if cost > 100:
               return ActionRisk.CRITICAL
           elif cost > 10:
               return ActionRisk.HIGH
           elif cost > 0:
               return ActionRisk.MEDIUM
           else:
               return ActionRisk.LOW
   ```

2. **Domain Purchase Tool**
   
   Create `agent/tools/actions/buy_domain.py`:
   
   ```python
   """
   Buy domain via Namecheap API.
   
   Requires: NAMECHEAP_API_KEY, NAMECHEAP_API_USER in environment
   """
   
   from typing import Dict, Any
   import requests
   
   from agent.tools.actions.base import ActionTool, ActionRisk
   from agent.tools.base import ToolManifest, ToolResult, ToolExecutionContext
   
   
   class BuyDomainTool(ActionTool):
       """Buy domain from Namecheap"""
       
       def get_manifest(self) -> ToolManifest:
           return ToolManifest(
               name="buy_domain",
               version="1.0.0",
               description="Purchase domain name via Namecheap",
               domains=["infrastructure", "web"],
               roles=["admin", "devops"],
               required_permissions=["domain_purchase"],
               input_schema={
                   "type": "object",
                   "properties": {
                       "domain": {
                           "type": "string",
                           "pattern": "^[a-z0-9-]+\\.[a-z]{2,}$",
                           "description": "Domain to purchase (e.g., example.com)"
                       },
                       "years": {
                           "type": "integer",
                           "minimum": 1,
                           "maximum": 10,
                           "default": 1
                       }
                   },
                   "required": ["domain"]
               },
               output_schema={
                   "type": "object",
                   "properties": {
                       "domain": {"type": "string"},
                       "cost": {"type": "number"},
                       "nameservers": {"type": "array"},
                       "expires_at": {"type": "string"}
                   }
               },
               cost_estimate=12.0,
               timeout_seconds=30,
               requires_network=True,
               examples=[
                   {
                       "input": {"domain": "example.com", "years": 1},
                       "output": {
                           "domain": "example.com",
                           "cost": 12.98,
                           "nameservers": ["ns1.namecheap.com", "ns2.namecheap.com"],
                           "expires_at": "2026-11-20"
                       }
                   }
               ]
           )
       
       async def estimate_cost(self, params: Dict[str, Any]) -> float:
           """Get domain pricing from Namecheap"""
           domain = params["domain"]
           years = params.get("years", 1)
           
           # Check availability and get price
           api_response = await self._namecheap_api_call(
               "namecheap.domains.check",
               {"DomainList": domain}
           )
           
           if not api_response.get("available"):
               raise ValueError(f"Domain {domain} not available")
           
           price_per_year = api_response.get("price", 12.98)
           return price_per_year * years
       
       async def execute_action(
           self,
           params: Dict[str, Any],
           context: ToolExecutionContext
       ) -> ToolResult:
           """Purchase domain"""
           domain = params["domain"]
           years = params.get("years", 1)
           
           try:
               # Purchase via Namecheap API
               response = await self._namecheap_api_call(
                   "namecheap.domains.create",
                   {
                       "DomainName": domain,
                       "Years": years
                   }
               )
               
               return ToolResult(
                   success=True,
                   data={
                       "domain": domain,
                       "cost": response["cost"],
                       "nameservers": response["nameservers"],
                       "expires_at": response["expiration_date"],
                       "registration_id": response["id"]
                   }
               )
               
           except Exception as e:
               return ToolResult(
                   success=False,
                   error=f"Failed to purchase domain: {str(e)}"
               )
       
       async def rollback(
           self,
           execution_id: str,
           context: ToolExecutionContext
       ) -> bool:
           """
           Attempt refund (within 24 hours of purchase).
           
           Note: Namecheap has limited refund policy.
           """
           # Implementation depends on Namecheap refund API
           return False
       
       async def _namecheap_api_call(
           self,
           command: str,
           params: Dict[str, Any]
       ) -> Dict:
           """Make Namecheap API call"""
           import os
           
           api_key = os.getenv("NAMECHEAP_API_KEY")
           api_user = os.getenv("NAMECHEAP_API_USER")
           
           if not api_key or not api_user:
               raise ValueError("Namecheap API credentials not configured")
           
           # Construct API URL
           url = "https://api.namecheap.com/xml.response"
           
           params.update({
               "ApiUser": api_user,
               "ApiKey": api_key,
               "UserName": api_user,
               "Command": command,
               "ClientIp": self._get_client_ip()
           })
           
           response = requests.get(url, params=params)
           
           # Parse XML response (simplified)
           # Real implementation would use proper XML parsing
           if response.status_code != 200:
               raise Exception(f"API error: {response.status_code}")
           
           return self._parse_namecheap_response(response.text)
       
       def _parse_namecheap_response(self, xml: str) -> Dict:
           """Parse Namecheap XML response"""
           # Simplified - real implementation would use xml.etree
           return {}
   ```

3. **Website Deployment Tool**
   
   Create `agent/tools/actions/deploy_website.py`:
   
   ```python
   """
   Deploy website to Vercel.
   
   Takes local project, pushes to GitHub, deploys to Vercel.
   """
   
   from typing import Dict, Any
   import os
   import subprocess
   
   from agent.tools.actions.base import ActionTool
   from agent.tools.base import ToolManifest, ToolResult, ToolExecutionContext
   
   
   class DeployWebsiteTool(ActionTool):
       """Deploy website to Vercel"""
       
       def get_manifest(self) -> ToolManifest:
           return ToolManifest(
               name="deploy_website",
               version="1.0.0",
               description="Deploy website to Vercel with custom domain",
               domains=["web", "infrastructure"],
               roles=["admin", "developer"],
               required_permissions=["deploy"],
               input_schema={
                   "type": "object",
                   "properties": {
                       "project_path": {
                           "type": "string",
                           "description": "Local path to project"
                       },
                       "custom_domain": {
                           "type": "string",
                           "description": "Custom domain (optional)"
                       },
                       "framework": {
                           "type": "string",
                           "enum": ["nextjs", "react", "vue", "static"],
                           "default": "static"
                       }
                   },
                   "required": ["project_path"]
               },
               cost_estimate=0.0,  # Free tier available
               timeout_seconds=300,
               requires_network=True
           )
       
       async def estimate_cost(self, params: Dict[str, Any]) -> float:
           """Vercel has free tier"""
           return 0.0
       
       async def execute_action(
           self,
           params: Dict[str, Any],
           context: ToolExecutionContext
       ) -> ToolResult:
           """Deploy to Vercel"""
           project_path = params["project_path"]
           custom_domain = params.get("custom_domain")
           framework = params.get("framework", "static")
           
           try:
               # Step 1: Initialize git if not already
               if not os.path.exists(os.path.join(project_path, ".git")):
                   subprocess.run(["git", "init"], cwd=project_path, check=True)
                   subprocess.run(["git", "add", "."], cwd=project_path, check=True)
                   subprocess.run(
                       ["git", "commit", "-m", "Initial commit"],
                       cwd=project_path,
                       check=True
                   )
               
               # Step 2: Create GitHub repo and push
               repo_url = await self._create_github_repo(project_path)
               
               subprocess.run(
                   ["git", "remote", "add", "origin", repo_url],
                   cwd=project_path,
                   check=True
               )
               subprocess.run(
                   ["git", "push", "-u", "origin", "main"],
                   cwd=project_path,
                   check=True
               )
               
               # Step 3: Deploy to Vercel
               deployment = await self._deploy_to_vercel(
                   repo_url,
                   framework,
                   custom_domain
               )
               
               return ToolResult(
                   success=True,
                   data={
                       "url": deployment["url"],
                       "deployment_id": deployment["id"],
                       "custom_domain": custom_domain,
                       "framework": framework
                   }
               )
               
           except Exception as e:
               return ToolResult(
                   success=False,
                   error=f"Deployment failed: {str(e)}"
               )
       
       async def rollback(
           self,
           execution_id: str,
           context: ToolExecutionContext
       ) -> bool:
           """Delete deployment"""
           # Call Vercel API to delete deployment
           return True
       
       async def _create_github_repo(self, project_path: str) -> str:
           """Create GitHub repository"""
           import requests
           
           github_token = os.getenv("GITHUB_TOKEN")
           
           response = requests.post(
               "https://api.github.com/user/repos",
               headers={
                   "Authorization": f"token {github_token}",
                   "Accept": "application/vnd.github.v3+json"
               },
               json={
                   "name": os.path.basename(project_path),
                   "private": False
               }
           )
           
           return response.json()["clone_url"]
       
       async def _deploy_to_vercel(
           self,
           repo_url: str,
           framework: str,
           custom_domain: str = None
       ) -> Dict:
           """Deploy via Vercel API"""
           import requests
           
           vercel_token = os.getenv("VERCEL_TOKEN")
           
           response = requests.post(
               "https://api.vercel.com/v13/deployments",
               headers={
                   "Authorization": f"Bearer {vercel_token}"
               },
               json={
                   "gitSource": {
                       "type": "github",
                       "repo": repo_url
                   },
                   "framework": framework,
                   "customDomain": custom_domain
               }
           )
           
           return response.json()
   ```

4. **SMS Tool**
   
   Create `agent/tools/actions/send_sms.py`:
   
   ```python
   """Send SMS via Twilio"""
   
   from agent.tools.actions.base import ActionTool
   
   class SendSMSTool(ActionTool):
       """Send SMS message via Twilio"""
       
       # Implementation similar to above
       # Cost: $0.01 per message
       # Risk: LOW (inexpensive, non-destructive)
   ```

5. **Payment Tool**
   
   Create `agent/tools/actions/make_payment.py`:
   
   ```python
   """Execute payment via Stripe"""
   
   from agent.tools.actions.base import ActionTool, ActionRisk
   
   class MakePaymentTool(ActionTool):
       """Process payment via Stripe"""
       
       def _assess_risk(self, params: Dict, cost: float) -> ActionRisk:
           """Payments always require approval"""
           if cost > 100:
               return ActionRisk.CRITICAL  # Requires 2FA
           else:
               return ActionRisk.HIGH
       
       # Implementation handles Stripe API
       # Always requires approval
       # Supports refunds via rollback()
   ```

6. **Configuration**
   
   Add to `agent/config.py`:
   
   ```python
   class ActionToolsConfig:
       """Configuration for action execution tools"""
       
       # Approval settings
       require_approval_for_paid_actions: bool = True
       require_2fa_above_usd: float = 100.0
       approval_timeout_seconds: int = 300
       
       # Cost limits
       daily_spending_limit_usd: float = 500.0
       per_action_limit_usd: float = 200.0
       
       # Rollback settings
       auto_rollback_on_failure: bool = True
       rollback_timeout_seconds: int = 60
       
       # API credentials (from environment)
       namecheap_api_key: str = os.getenv("NAMECHEAP_API_KEY", "")
       vercel_token: str = os.getenv("VERCEL_TOKEN", "")
       github_token: str = os.getenv("GITHUB_TOKEN", "")
       twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
       twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
       stripe_api_key: str = os.getenv("STRIPE_API_KEY", "")
   ```

7. **Testing**
   
   Create `agent/tests/test_action_tools.py`:
   
   ```python
   """Tests for action execution tools"""
   
   import pytest
   from unittest.mock import Mock, patch
   
   from agent.tools.actions.buy_domain import BuyDomainTool
   from agent.tools.actions.deploy_website import DeployWebsiteTool
   
   
   @pytest.mark.asyncio
   async def test_domain_cost_estimation():
       """Test domain cost estimation"""
       tool = BuyDomainTool()
       
       with patch.object(tool, '_namecheap_api_call') as mock_api:
           mock_api.return_value = {
               "available": True,
               "price": 12.98
           }
           
           cost = await tool.estimate_cost({"domain": "example.com"})
           assert cost == 12.98
   
   
   @pytest.mark.asyncio
   async def test_approval_required_for_paid_action():
       """Test approval workflow for paid actions"""
       tool = BuyDomainTool()
       context = Mock()
       
       # Mock approval to return False (user declines)
       with patch.object(tool, '_request_approval') as mock_approval:
           mock_approval.return_value = False
           
           result = await tool.execute(
               {"domain": "example.com"},
               context
           )
           
           assert result.success is False
           assert "declined" in result.error.lower()
   
   
   @pytest.mark.asyncio
   async def test_rollback_on_failure():
       """Test rollback functionality"""
       tool = DeployWebsiteTool()
       
       # Mock deployment failure
       with patch.object(tool, '_deploy_to_vercel') as mock_deploy:
           mock_deploy.side_effect = Exception("Deployment failed")
           
           result = await tool.execute(
               {"project_path": "/tmp/test"},
               Mock()
           )
           
           assert result.success is False
   ```

**Acceptance Criteria:**

- [ ] ActionTool base class implemented
- [ ] Domain purchase tool works with Namecheap API
- [ ] Website deployment tool works with Vercel
- [ ] SMS tool works with Twilio
- [ ] Payment tool works with Stripe
- [ ] Cost estimation works for all tools
- [ ] Approval workflow functions correctly
- [ ] Paid actions always require approval
- [ ] High-cost actions (>$100) require 2FA
- [ ] Rollback works for reversible actions
- [ ] Complete audit trail for all executions
- [ ] Daily spending limits enforced
- [ ] All tests pass (minimum 20 test cases)
- [ ] Documentation includes setup guides for each service

**Files to Create:**
- `agent/tools/actions/base.py` (~400 lines)
- `agent/tools/actions/buy_domain.py` (~300 lines)
- `agent/tools/actions/deploy_website.py` (~350 lines)
- `agent/tools/actions/send_sms.py` (~200 lines)
- `agent/tools/actions/make_payment.py` (~300 lines)
- `agent/tests/test_action_tools.py` (~400 lines)
- `docs/ACTION_TOOLS_SETUP.md` (~600 lines)

**Files to Modify:**
- `agent/config.py` — Add ActionToolsConfig
- `agent/tools/base.py` — Ensure compatibility
- `README.md` — Add action tools section

**References:**
- Namecheap API: https://www.namecheap.com/support/api/
- Vercel API: https://vercel.com/docs/rest-api
- Twilio API: https://www.twilio.com/docs/usage/api
- Stripe API: https://stripe.com/docs/api

---

## Phase 7A: Meeting Integration (Weeks 7-8)

### Overview
**Objective:** Enable JARVIS to listen to meetings (Zoom/Teams/Live), transcribe in real-time, understand context, take notes, and execute actions during conversations.

**Timeline:** Weeks 7-8  
**Priority:** P0 (Critical - Makes JARVIS Proactive)  
**Success Metrics:**
- ✅ JARVIS joins Zoom/Teams meetings as bot
- ✅ Real-time transcription <2 second latency
- ✅ Speaker identification >90% accuracy
- ✅ Action item extraction >85% accuracy
- ✅ Executes simple actions during meeting
- ✅ Generates comprehensive meeting notes

---

### Prompt 7A.1: Zoom and Teams Bot Integration

**Context:**
Current state: ConversationalAgent from Prompt 7.1 only works with text chat interface. It cannot join video meetings, listen to audio, or participate in real-time conversations. Users must manually copy action items from meetings to chat with JARVIS.

This creates friction: meetings generate 80%+ of business action items, but JARVIS is blind to them. To be a true business assistant (like Tony Stark's JARVIS), the system must attend meetings, listen actively, and take action autonomously.

**Task:**
Implement meeting bot integration that allows JARVIS to join Zoom and Microsoft Teams meetings as a participant, capture audio streams, and maintain meeting context. Support both scheduled meetings (automatic join) and ad-hoc meetings (join on command).

**Requirements:**

1. **Meeting Platform Abstraction**
   
   Create `agent/meetings/base.py`:
   
   ```python
   """
   Base classes for meeting platform integration.
   
   Provides abstraction for Zoom, Teams, Google Meet, and live audio.
   """
   
   from abc import ABC, abstractmethod
   from typing import AsyncIterator, Dict, Any, Optional
   from dataclasses import dataclass
   from datetime import datetime
   from enum import Enum
   
   
   class MeetingPlatform(Enum):
       """Supported meeting platforms"""
       ZOOM = "zoom"
       TEAMS = "teams"
       GOOGLE_MEET = "google_meet"
       LIVE_AUDIO = "live"
   
   
   @dataclass
   class MeetingInfo:
       """Meeting metadata"""
       platform: MeetingPlatform
       meeting_id: str
       title: str
       participants: list[str]
       start_time: datetime
       scheduled_duration_minutes: int
       meeting_url: Optional[str] = None
   
   
   @dataclass
   class AudioChunk:
       """Audio data chunk"""
       audio_bytes: bytes
       timestamp: datetime
       duration_ms: int
       sample_rate: int = 16000
       channels: int = 1
   
   
   class MeetingBot(ABC):
       """
       Abstract base class for meeting bots.
       
       Each platform (Zoom, Teams) implements this interface.
       """
       
       def __init__(self, meeting_info: MeetingInfo):
           self.meeting_info = meeting_info
           self.is_connected = False
           self.is_recording = False
       
       @abstractmethod
       async def connect(self) -> bool:
           """
           Connect to meeting platform.
           
           Returns True if connection successful.
           """
           pass
       
       @abstractmethod
       async def join_meeting(self) -> bool:
           """
           Join the specific meeting.
           
           Bot appears as participant in meeting.
           Returns True if join successful.
           """
           pass
       
       @abstractmethod
       async def start_audio_capture(self) -> bool:
           """
           Start capturing audio stream.
           
           Returns True if capture started successfully.
           """
           pass
       
       @abstractmethod
       async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
           """
           Stream audio chunks as they arrive.
           
           Yields AudioChunk objects continuously.
           """
           pass
       
       @abstractmethod
       async def get_participants(self) -> list[Dict[str, Any]]:
           """
           Get current meeting participants.
           
           Returns list of participant info dicts.
           """
           pass
       
       @abstractmethod
       async def send_chat_message(self, message: str) -> bool:
           """
           Send message to meeting chat.
           
           Returns True if message sent successfully.
           """
           pass
       
       @abstractmethod
       async def leave_meeting(self) -> bool:
           """
           Leave meeting and disconnect.
           
           Returns True if left successfully.
           """
           pass
       
       @abstractmethod
       async def get_recording_url(self) -> Optional[str]:
           """
           Get URL of meeting recording (if available).
           
           Returns URL or None if not available.
           """
           pass
   ```

2. **Zoom Bot Implementation**
   
   Create `agent/meetings/zoom_bot.py`:
   
   ```python
   """
   Zoom meeting bot implementation.
   
   Uses Zoom SDK to join meetings and capture audio.
   Requires: Zoom SDK credentials (JWT or OAuth)
   """
   
   import asyncio
   import os
   from typing import AsyncIterator, Dict, Any, Optional
   import aiohttp
   import jwt
   from datetime import datetime, timedelta
   
   from agent.meetings.base import (
       MeetingBot, MeetingInfo, AudioChunk, MeetingPlatform
   )
   from agent.core_logging import log_event
   
   
   class ZoomBot(MeetingBot):
       """Zoom meeting bot implementation"""
       
       def __init__(self, meeting_info: MeetingInfo):
           super().__init__(meeting_info)
           
           # Zoom API credentials
           self.api_key = os.getenv("ZOOM_API_KEY")
           self.api_secret = os.getenv("ZOOM_API_SECRET")
           self.zoom_sdk_key = os.getenv("ZOOM_SDK_KEY")
           self.zoom_sdk_secret = os.getenv("ZOOM_SDK_SECRET")
           
           if not all([self.api_key, self.api_secret]):
               raise ValueError("Zoom API credentials not configured")
           
           # SDK connection
           self.zoom_session = None
           self.audio_stream_active = False
       
       async def connect(self) -> bool:
           """Connect to Zoom SDK"""
           try:
               # Generate JWT token for SDK auth
               token = self._generate_jwt_token()
               
               # Initialize Zoom SDK session
               # Note: Actual implementation depends on Zoom SDK version
               # This is pseudocode showing the concept
               
               self.zoom_session = await self._init_zoom_sdk(token)
               self.is_connected = True
               
               log_event("zoom_bot_connected", {
                   "meeting_id": self.meeting_info.meeting_id
               })
               
               return True
               
           except Exception as e:
               log_event("zoom_bot_connection_failed", {
                   "error": str(e)
               })
               return False
       
       async def join_meeting(self) -> bool:
           """Join Zoom meeting"""
           if not self.is_connected:
               await self.connect()
           
           try:
               # Join meeting via SDK
               join_response = await self.zoom_session.join_meeting(
                   meeting_number=self.meeting_info.meeting_id,
                   display_name="JARVIS (AI Assistant)",
                   meeting_password=await self._get_meeting_password()
               )
               
               if join_response.success:
                   log_event("zoom_meeting_joined", {
                       "meeting_id": self.meeting_info.meeting_id,
                       "participants": len(await self.get_participants())
                   })
                   return True
               
               return False
               
           except Exception as e:
               log_event("zoom_meeting_join_failed", {
                   "error": str(e)
               })
               return False
       
       async def start_audio_capture(self) -> bool:
           """Start capturing audio from meeting"""
           try:
               # Enable audio stream from SDK
               await self.zoom_session.start_audio_stream(
                   sample_rate=16000,
                   channels=1
               )
               
               self.audio_stream_active = True
               self.is_recording = True
               
               log_event("zoom_audio_capture_started", {
                   "meeting_id": self.meeting_info.meeting_id
               })
               
               return True
               
           except Exception as e:
               log_event("zoom_audio_capture_failed", {
                   "error": str(e)
               })
               return False
       
       async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
           """
           Stream audio chunks from Zoom meeting.
           
           Yields 1-second audio chunks at 16kHz.
           """
           if not self.audio_stream_active:
               await self.start_audio_capture()
           
           while self.audio_stream_active:
               try:
                   # Get audio from SDK
                   # SDK provides raw PCM audio data
                   audio_data = await self.zoom_session.read_audio_data(
                       chunk_size=16000  # 1 second at 16kHz
                   )
                   
                   if audio_data:
                       yield AudioChunk(
                           audio_bytes=audio_data,
                           timestamp=datetime.now(),
                           duration_ms=1000,
                           sample_rate=16000,
                           channels=1
                       )
                   
                   # Small delay to prevent tight loop
                   await asyncio.sleep(0.01)
                   
               except Exception as e:
                   log_event("zoom_audio_stream_error", {
                       "error": str(e)
                   })
                   break
       
       async def get_participants(self) -> list[Dict[str, Any]]:
           """Get list of current participants"""
           try:
               participants = await self.zoom_session.get_participants()
               
               return [
                   {
                       "id": p.user_id,
                       "name": p.display_name,
                       "email": p.email,
                       "is_host": p.is_host,
                       "is_cohost": p.is_cohost,
                       "audio_state": "muted" if p.is_audio_muted else "unmuted",
                       "video_state": "off" if p.is_video_muted else "on"
                   }
                   for p in participants
               ]
               
           except Exception as e:
               log_event("zoom_get_participants_failed", {
                   "error": str(e)
               })
               return []
       
       async def send_chat_message(self, message: str) -> bool:
           """Send message to meeting chat"""
           try:
               await self.zoom_session.send_chat_message(
                   message=message,
                   to_all=True
               )
               
               log_event("zoom_chat_message_sent", {
                   "message_length": len(message)
               })
               
               return True
               
           except Exception as e:
               log_event("zoom_chat_message_failed", {
                   "error": str(e)
               })
               return False
       
       async def leave_meeting(self) -> bool:
           """Leave meeting and cleanup"""
           try:
               # Stop audio capture
               self.audio_stream_active = False
               self.is_recording = False
               
               # Leave meeting
               await self.zoom_session.leave_meeting()
               
               # Disconnect SDK
               await self.zoom_session.disconnect()
               self.is_connected = False
               
               log_event("zoom_meeting_left", {
                   "meeting_id": self.meeting_info.meeting_id
               })
               
               return True
               
           except Exception as e:
               log_event("zoom_leave_meeting_failed", {
                   "error": str(e)
               })
               return False
       
       async def get_recording_url(self) -> Optional[str]:
           """
           Get recording URL via Zoom API.
           
           Recording must be enabled in meeting settings.
           """
           try:
               # Use Zoom API to get recording
               async with aiohttp.ClientSession() as session:
                   headers = {
                       "Authorization": f"Bearer {self._generate_jwt_token()}"
                   }
                   
                   async with session.get(
                       f"https://api.zoom.us/v2/meetings/{self.meeting_info.meeting_id}/recordings",
                       headers=headers
                   ) as resp:
                       if resp.status == 200:
                           data = await resp.json()
                           recordings = data.get("recording_files", [])
                           
                           # Return first audio recording
                           for recording in recordings:
                               if recording["file_type"] == "MP4":
                                   return recording["download_url"]
               
               return None
               
           except Exception as e:
               log_event("zoom_get_recording_failed", {
                   "error": str(e)
               })
               return None
       
       def _generate_jwt_token(self) -> str:
           """Generate JWT token for Zoom API"""
           payload = {
               "iss": self.api_key,
               "exp": datetime.now() + timedelta(hours=1)
           }
           
           return jwt.encode(payload, self.api_secret, algorithm="HS256")
       
       async def _get_meeting_password(self) -> Optional[str]:
           """
           Get meeting password if required.
           
           Can retrieve from calendar integration or prompt user.
           """
           # Try to get from meeting info
           if hasattr(self.meeting_info, "password"):
               return self.meeting_info.password
           
           # Could also query Zoom API for meeting details
           return None
   ```

3. **Microsoft Teams Bot Implementation**
   
   Create `agent/meetings/teams_bot.py`:
   
   ```python
   """
   Microsoft Teams meeting bot implementation.
   
   Uses Microsoft Graph API and Bot Framework SDK.
   Requires: Azure app registration with Teams permissions
   """
   
   import asyncio
   import os
   from typing import AsyncIterator, Dict, Any, Optional
   from azure.identity import ClientSecretCredential
   from msgraph import GraphServiceClient
   from botbuilder.core import BotFrameworkAdapter, TurnContext
   from botbuilder.schema import Activity
   
   from agent.meetings.base import (
       MeetingBot, MeetingInfo, AudioChunk, MeetingPlatform
   )
   from agent.core_logging import log_event
   
   
   class TeamsBot(MeetingBot):
       """Microsoft Teams meeting bot implementation"""
       
       def __init__(self, meeting_info: MeetingInfo):
           super().__init__(meeting_info)
           
           # Azure credentials
           self.tenant_id = os.getenv("AZURE_TENANT_ID")
           self.client_id = os.getenv("AZURE_CLIENT_ID")
           self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
           
           if not all([self.tenant_id, self.client_id, self.client_secret]):
               raise ValueError("Azure credentials not configured")
           
           # Graph API client
           self.graph_client = None
           self.call_id = None
           self.audio_socket = None
       
       async def connect(self) -> bool:
           """Connect to Microsoft Graph"""
           try:
               # Authenticate with Azure AD
               credential = ClientSecretCredential(
                   tenant_id=self.tenant_id,
                   client_id=self.client_id,
                   client_secret=self.client_secret
               )
               
               # Initialize Graph client
               self.graph_client = GraphServiceClient(credential)
               self.is_connected = True
               
               log_event("teams_bot_connected", {
                   "meeting_id": self.meeting_info.meeting_id
               })
               
               return True
               
           except Exception as e:
               log_event("teams_bot_connection_failed", {
                   "error": str(e)
               })
               return False
       
       async def join_meeting(self) -> bool:
           """Join Teams meeting"""
           if not self.is_connected:
               await self.connect()
           
           try:
               # Create call using Graph API
               call_request = {
                   "@odata.type": "#microsoft.graph.call",
                   "callbackUri": f"https://{os.getenv('PUBLIC_URL')}/api/teams/callback",
                   "source": {
                       "identity": {
                           "application": {
                               "id": self.client_id,
                               "displayName": "JARVIS (AI Assistant)"
                           }
                       }
                   },
                   "direction": "incoming",
                   "subject": "JARVIS joining meeting",
                   "meetingInfo": {
                       "joinWebUrl": self.meeting_info.meeting_url
                   },
                   "mediaConfig": {
                       "audio": "enabled",
                       "video": "disabled"
                   }
               }
               
               call_response = await self.graph_client.communications.calls.post(
                   call_request
               )
               
               self.call_id = call_response.id
               
               log_event("teams_meeting_joined", {
                   "meeting_id": self.meeting_info.meeting_id,
                   "call_id": self.call_id
               })
               
               return True
               
           except Exception as e:
               log_event("teams_meeting_join_failed", {
                   "error": str(e)
               })
               return False
       
       async def start_audio_capture(self) -> bool:
           """Start capturing audio from Teams meeting"""
           try:
               # Subscribe to audio stream via Media Platform
               await self.graph_client.communications.calls[self.call_id].subscribe_to_tone.post()
               
               # Open audio socket
               self.audio_socket = await self._open_audio_socket()
               
               self.audio_stream_active = True
               self.is_recording = True
               
               log_event("teams_audio_capture_started", {
                   "call_id": self.call_id
               })
               
               return True
               
           except Exception as e:
               log_event("teams_audio_capture_failed", {
                   "error": str(e)
               })
               return False
       
       async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
           """
           Stream audio chunks from Teams meeting.
           
           Teams provides PCM audio at 16kHz.
           """
           if not self.audio_stream_active:
               await self.start_audio_capture()
           
           while self.audio_stream_active:
               try:
                   # Read from audio socket
                   audio_data = await self.audio_socket.recv(16000)
                   
                   if audio_data:
                       yield AudioChunk(
                           audio_bytes=audio_data,
                           timestamp=datetime.now(),
                           duration_ms=1000,
                           sample_rate=16000,
                           channels=1
                       )
                   
                   await asyncio.sleep(0.01)
                   
               except Exception as e:
                   log_event("teams_audio_stream_error", {
                       "error": str(e)
                   })
                   break
       
       async def get_participants(self) -> list[Dict[str, Any]]:
           """Get Teams meeting participants"""
           try:
               participants = await self.graph_client.communications.calls[self.call_id].participants.get()
               
               return [
                   {
                       "id": p.id,
                       "name": p.info.identity.user.display_name,
                       "email": p.info.identity.user.id,
                       "is_muted": p.is_muted
                   }
                   for p in participants.value
               ]
               
           except Exception as e:
               log_event("teams_get_participants_failed", {
                   "error": str(e)
               })
               return []
       
       async def send_chat_message(self, message: str) -> bool:
           """Send message to Teams meeting chat"""
           try:
               chat_message = {
                   "body": {
                       "content": message
                   }
               }
               
               await self.graph_client.chats[self.meeting_info.meeting_id].messages.post(
                   chat_message
               )
               
               log_event("teams_chat_message_sent", {
                   "message_length": len(message)
               })
               
               return True
               
           except Exception as e:
               log_event("teams_chat_message_failed", {
                   "error": str(e)
               })
               return False
       
       async def leave_meeting(self) -> bool:
           """Leave Teams meeting"""
           try:
               # Stop audio
               self.audio_stream_active = False
               
               if self.audio_socket:
                   await self.audio_socket.close()
               
               # Delete call
               await self.graph_client.communications.calls[self.call_id].delete()
               
               self.is_connected = False
               
               log_event("teams_meeting_left", {
                   "call_id": self.call_id
               })
               
               return True
               
           except Exception as e:
               log_event("teams_leave_meeting_failed", {
                   "error": str(e)
               })
               return False
       
       async def get_recording_url(self) -> Optional[str]:
           """Get Teams meeting recording URL"""
           try:
               # Query for recording
               recordings = await self.graph_client.communications.calls[self.call_id].recordings.get()
               
               if recordings.value:
                   return recordings.value[0].content_url
               
               return None
               
           except Exception as e:
               log_event("teams_get_recording_failed", {
                   "error": str(e)
               })
               return None
       
       async def _open_audio_socket(self):
           """Open websocket for audio streaming"""
           # Implementation depends on Azure Media Platform SDK
           pass
   ```

4. **Live Audio Capture (Microphone)**
   
   Create `agent/meetings/live_audio_bot.py`:
   
   ```python
   """
   Live audio capture from microphone.
   
   For in-person meetings or when screen-sharing tools used.
   Uses PyAudio to capture from default microphone.
   """
   
   import asyncio
   import pyaudio
   import numpy as np
   from typing import AsyncIterator
   from datetime import datetime
   
   from agent.meetings.base import MeetingBot, MeetingInfo, AudioChunk
   from agent.core_logging import log_event
   
   
   class LiveAudioBot(MeetingBot):
       """Capture live audio from microphone"""
       
       def __init__(self, meeting_info: MeetingInfo):
           super().__init__(meeting_info)
           
           self.pyaudio = pyaudio.PyAudio()
           self.stream = None
       
       async def connect(self) -> bool:
           """Check microphone availability"""
           try:
               # List audio devices
               device_count = self.pyaudio.get_device_count()
               
               if device_count == 0:
                   raise ValueError("No audio devices found")
               
               self.is_connected = True
               
               log_event("live_audio_connected", {
                   "devices": device_count
               })
               
               return True
               
           except Exception as e:
               log_event("live_audio_connection_failed", {
                   "error": str(e)
               })
               return False
       
       async def join_meeting(self) -> bool:
           """'Join' by starting to listen"""
           if not self.is_connected:
               await self.connect()
           
           log_event("live_audio_started", {
               "meeting_id": self.meeting_info.meeting_id
           })
           
           return True
       
       async def start_audio_capture(self) -> bool:
           """Open microphone stream"""
           try:
               self.stream = self.pyaudio.open(
                   format=pyaudio.paInt16,
                   channels=1,
                   rate=16000,
                   input=True,
                   frames_per_buffer=1024
               )
               
               self.audio_stream_active = True
               self.is_recording = True
               
               log_event("live_audio_capture_started")
               
               return True
               
           except Exception as e:
               log_event("live_audio_capture_failed", {
                   "error": str(e)
               })
               return False
       
       async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
           """Stream microphone audio"""
           if not self.audio_stream_active:
               await self.start_audio_capture()
           
           while self.audio_stream_active:
               try:
                   # Read 1 second of audio (16 chunks)
                   frames = []
                   for _ in range(16):
                       data = self.stream.read(1024, exception_on_overflow=False)
                       frames.append(data)
                   
                   audio_bytes = b''.join(frames)
                   
                   yield AudioChunk(
                       audio_bytes=audio_bytes,
                       timestamp=datetime.now(),
                       duration_ms=1000,
                       sample_rate=16000,
                       channels=1
                   )
                   
               except Exception as e:
                   log_event("live_audio_stream_error", {
                       "error": str(e)
                   })
                   break
       
       async def get_participants(self) -> list:
           """Cannot detect participants from microphone"""
           return []
       
       async def send_chat_message(self, message: str) -> bool:
           """Cannot send chat in live audio"""
           return False
       
       async def leave_meeting(self) -> bool:
           """Stop microphone capture"""
           try:
               self.audio_stream_active = False
               
               if self.stream:
                   self.stream.stop_stream()
                   self.stream.close()
               
               self.pyaudio.terminate()
               self.is_connected = False
               
               log_event("live_audio_stopped")
               
               return True
               
           except Exception as e:
               log_event("live_audio_stop_failed", {
                   "error": str(e)
               })
               return False
       
       async def get_recording_url(self) -> Optional[str]:
           """No recording for live audio"""
           return None
   ```

5. **Meeting Bot Factory**
   
   Create `agent/meetings/factory.py`:
   
   ```python
   """Factory for creating appropriate meeting bot"""
   
   from agent.meetings.base import MeetingBot, MeetingInfo, MeetingPlatform
   from agent.meetings.zoom_bot import ZoomBot
   from agent.meetings.teams_bot import TeamsBot
   from agent.meetings.live_audio_bot import LiveAudioBot
   
   
   def create_meeting_bot(meeting_info: MeetingInfo) -> MeetingBot:
       """
       Create appropriate bot for meeting platform.
       
       Args:
           meeting_info: Meeting details
           
       Returns:
           MeetingBot instance for the platform
       """
       if meeting_info.platform == MeetingPlatform.ZOOM:
           return ZoomBot(meeting_info)
       
       elif meeting_info.platform == MeetingPlatform.TEAMS:
           return TeamsBot(meeting_info)
       
       elif meeting_info.platform == MeetingPlatform.LIVE_AUDIO:
           return LiveAudioBot(meeting_info)
       
       else:
           raise ValueError(f"Unsupported platform: {meeting_info.platform}")
   ```

6. **Configuration**
   
   Add to `agent/config.py`:
   
   ```python
   class MeetingConfig:
       """Meeting integration settings"""
       
       # Zoom credentials
       zoom_api_key: str = os.getenv("ZOOM_API_KEY", "")
       zoom_api_secret: str = os.getenv("ZOOM_API_SECRET", "")
       zoom_sdk_key: str = os.getenv("ZOOM_SDK_KEY", "")
       zoom_sdk_secret: str = os.getenv("ZOOM_SDK_SECRET", "")
       
       # Teams credentials
       azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
       azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
       azure_client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")
       
       # Meeting settings
       auto_join_scheduled_meetings: bool = True
       auto_join_delay_seconds: int = 30  # Join 30s after start
       auto_leave_after_silence_minutes: int = 5
       enable_chat_responses: bool = True
       announce_presence: bool = True  # Say "JARVIS joined"
   ```

7. **Testing**
   
   Create `agent/tests/test_meeting_bots.py`:
   
   ```python
   """Tests for meeting bot implementations"""
   
   import pytest
   from unittest.mock import Mock, AsyncMock, patch
   from datetime import datetime
   
   from agent.meetings.base import MeetingInfo, MeetingPlatform
   from agent.meetings.zoom_bot import ZoomBot
   from agent.meetings.teams_bot import TeamsBot
   from agent.meetings.live_audio_bot import LiveAudioBot
   from agent.meetings.factory import create_meeting_bot
   
   
   @pytest.fixture
   def zoom_meeting_info():
       """Sample Zoom meeting info"""
       return MeetingInfo(
           platform=MeetingPlatform.ZOOM,
           meeting_id="123456789",
           title="Test Meeting",
           participants=["user1@example.com"],
           start_time=datetime.now(),
           scheduled_duration_minutes=60,
           meeting_url="https://zoom.us/j/123456789"
       )
   
   
   @pytest.mark.asyncio
   async def test_zoom_bot_connection(zoom_meeting_info):
       """Test Zoom bot can connect"""
       bot = ZoomBot(zoom_meeting_info)
       
       with patch.object(bot, '_init_zoom_sdk') as mock_sdk:
           mock_sdk.return_value = AsyncMock()
           
           connected = await bot.connect()
           assert connected is True
           assert bot.is_connected is True
   
   
   @pytest.mark.asyncio
   async def test_zoom_bot_join_meeting(zoom_meeting_info):
       """Test Zoom bot can join meeting"""
       bot = ZoomBot(zoom_meeting_info)
       bot.is_connected = True
       bot.zoom_session = AsyncMock()
       bot.zoom_session.join_meeting = AsyncMock(return_value=Mock(success=True))
       
       joined = await bot.join_meeting()
       assert joined is True
   
   
   @pytest.mark.asyncio
   async def test_meeting_bot_factory():
       """Test factory creates correct bot type"""
       zoom_info = MeetingInfo(
           platform=MeetingPlatform.ZOOM,
           meeting_id="123",
           title="Test",
           participants=[],
           start_time=datetime.now(),
           scheduled_duration_minutes=60
       )
       
       bot = create_meeting_bot(zoom_info)
       assert isinstance(bot, ZoomBot)
   
   
   @pytest.mark.asyncio
   async def test_live_audio_bot_stream():
       """Test live audio bot captures from mic"""
       meeting_info = MeetingInfo(
           platform=MeetingPlatform.LIVE_AUDIO,
           meeting_id="live_001",
           title="Live Meeting",
           participants=[],
           start_time=datetime.now(),
           scheduled_duration_minutes=60
       )
       
       bot = LiveAudioBot(meeting_info)
       
       # Mock PyAudio
       with patch('pyaudio.PyAudio'):
           await bot.connect()
           assert bot.is_connected is True
   ```

**Acceptance Criteria:**

- [ ] MeetingBot base class defined with all required methods
- [ ] ZoomBot implementation works with Zoom SDK
- [ ] TeamsBot implementation works with Graph API
- [ ] LiveAudioBot captures from microphone
- [ ] Factory creates correct bot for platform
- [ ] Bot can join meetings automatically
- [ ] Audio stream provides 16kHz PCM chunks
- [ ] Bot can send chat messages
- [ ] Bot can get participant list
- [ ] Bot leaves meeting cleanly
- [ ] All tests pass (minimum 15 test cases)
- [ ] Documentation includes setup guides for each platform

**Files to Create:**
- `agent/meetings/__init__.py` (~20 lines)
- `agent/meetings/base.py` (~200 lines)
- `agent/meetings/zoom_bot.py` (~400 lines)
- `agent/meetings/teams_bot.py` (~350 lines)
- `agent/meetings/live_audio_bot.py` (~200 lines)
- `agent/meetings/factory.py` (~50 lines)
- `agent/tests/test_meeting_bots.py` (~300 lines)
- `docs/MEETING_INTEGRATION_SETUP.md` (~800 lines)

**Files to Modify:**
- `agent/config.py` — Add MeetingConfig class
- `.env.example` — Add meeting platform credentials

**References:**
- Zoom SDK: https://developers.zoom.us/docs/meeting-sdk/
- Microsoft Graph: https://learn.microsoft.com/en-us/graph/api/resources/call
- PyAudio: https://people.csail.mit.edu/hubert/pyaudio/docs/

**Notes:**
- Zoom SDK requires approval from Zoom marketplace
- Teams bot requires Azure app registration
- Both platforms have rate limits and quotas
- Consider GDPR compliance for recording consent

---

### Prompt 7A.2: Real-Time Speech Transcription

**Context:**
Current state: Meeting bots from Prompt 7A.1 can capture audio streams from Zoom/Teams/Live, but raw audio bytes are useless for understanding content. JARVIS needs text transcription to understand what's being discussed, extract action items, and respond intelligently.

Traditional batch transcription (send full recording after meeting) defeats the purpose - JARVIS must understand IN REAL-TIME to take notes and execute actions during the meeting, not after.

**Task:**
Implement real-time speech-to-text transcription system that converts audio chunks to text with <2 second latency. Support multiple transcription services (OpenAI Whisper, Deepgram, Google Speech) with automatic failover and quality optimization.

**Requirements:**

1. **Transcription Engine Base Class**
   
   Create `agent/meetings/transcription/base.py`:
   
   ```python
   """
   Base class for speech transcription engines.
   
   Supports multiple providers: Whisper, Deepgram, Google, Azure
   """
   
   from abc import ABC, abstractmethod
   from typing import Optional, Dict, Any
   from dataclasses import dataclass
   from datetime import datetime
   from enum import Enum
   
   
   class TranscriptionProvider(Enum):
       """Supported transcription providers"""
       WHISPER = "whisper"          # OpenAI Whisper (best accuracy)
       DEEPGRAM = "deepgram"        # Deepgram (best real-time)
       GOOGLE = "google"            # Google Speech-to-Text
       AZURE = "azure"              # Azure Speech Service
   
   
   @dataclass
   class TranscriptSegment:
       """Single transcription result"""
       text: str
       confidence: float  # 0.0 - 1.0
       start_time: datetime
       end_time: datetime
       speaker_id: Optional[str] = None
       language: str = "en"
       is_final: bool = False  # False for interim results
   
   
   class TranscriptionEngine(ABC):
       """Abstract base for transcription engines"""
       
       @abstractmethod
       async def transcribe_chunk(
           self,
           audio_bytes: bytes,
           sample_rate: int = 16000
       ) -> TranscriptSegment:
           """
           Transcribe single audio chunk.
           
           Args:
               audio_bytes: Raw PCM audio data
               sample_rate: Sample rate in Hz
               
           Returns:
               TranscriptSegment with text and metadata
           """
           pass
       
       @abstractmethod
       async def start_stream(self):
           """Initialize streaming connection"""
           pass
       
       @abstractmethod
       async def end_stream(self):
           """Close streaming connection"""
           pass
       
       @abstractmethod
       def supports_streaming(self) -> bool:
           """Does this engine support streaming?"""
           pass
       
       @abstractmethod
       async def get_supported_languages(self) -> list[str]:
           """Get list of supported language codes"""
           pass
   ```

2. **OpenAI Whisper Implementation**
   
   Create `agent/meetings/transcription/whisper_engine.py`:
   
   ```python
   """
   OpenAI Whisper transcription engine.
   
   Best accuracy, but slower (not true real-time streaming).
   Good for high-quality batch transcription.
   """
   
   import asyncio
   import openai
   from io import BytesIO
   from datetime import datetime
   
   from agent.meetings.transcription.base import (
       TranscriptionEngine, TranscriptSegment
   )
   from agent.core_logging import log_event
   
   
   class WhisperEngine(TranscriptionEngine):
       """OpenAI Whisper transcription"""
       
       def __init__(self, api_key: str, model: str = "whisper-1"):
           self.client = openai.AsyncOpenAI(api_key=api_key)
           self.model = model
           self.is_streaming = False
       
       async def transcribe_chunk(
           self,
           audio_bytes: bytes,
           sample_rate: int = 16000
       ) -> TranscriptSegment:
           """
           Transcribe audio chunk with Whisper.
           
           Note: Whisper is batch-based, not streaming.
           Each chunk is transcribed independently.
           """
           try:
               start_time = datetime.now()
               
               # Convert bytes to file-like object
               audio_file = BytesIO(audio_bytes)
               audio_file.name = "audio.wav"
               
               # Call Whisper API
               response = await self.client.audio.transcriptions.create(
                   model=self.model,
                   file=audio_file,
                   response_format="verbose_json",
                   timestamp_granularities=["segment"]
               )
               
               end_time = datetime.now()
               
               # Extract text and confidence
               text = response.text.strip()
               
               # Whisper doesn't provide confidence directly
               # Estimate based on no_speech_prob
               confidence = 1.0 - response.get("no_speech_prob", 0.0)
               
               segment = TranscriptSegment(
                   text=text,
                   confidence=confidence,
                   start_time=start_time,
                   end_time=end_time,
                   language=response.language,
                   is_final=True
               )
               
               log_event("whisper_transcription_complete", {
                   "text_length": len(text),
                   "confidence": confidence,
                   "latency_ms": (end_time - start_time).total_seconds() * 1000
               })
               
               return segment
               
           except Exception as e:
               log_event("whisper_transcription_failed", {
                   "error": str(e)
               })
               
               # Return empty segment on error
               return TranscriptSegment(
                   text="",
                   confidence=0.0,
                   start_time=datetime.now(),
                   end_time=datetime.now(),
                   is_final=True
               )
       
       async def start_stream(self):
           """Whisper doesn't support true streaming"""
           self.is_streaming = True
       
       async def end_stream(self):
           """End pseudo-stream"""
           self.is_streaming = False
       
       def supports_streaming(self) -> bool:
           """Whisper is batch-based"""
           return False
       
       async def get_supported_languages(self) -> list[str]:
           """
           Whisper supports 99 languages.
           
           Returns list of ISO 639-1 language codes.
           """
           return [
               "en", "es", "fr", "de", "it", "pt", "nl", "ru",
               "zh", "ja", "ko", "ar", "hi", "tr", "pl", "uk"
               # ... (full list of 99 languages)
           ]
   ```

3. **Deepgram Streaming Implementation**
   
   Create `agent/meetings/transcription/deepgram_engine.py`:
   
   ```python
   """
   Deepgram transcription engine.
   
   True real-time streaming with <100ms latency.
   Best for live transcription during meetings.
   """
   
   import asyncio
   import json
   import websockets
   from datetime import datetime
   from typing import AsyncIterator
   
   from agent.meetings.transcription.base import (
       TranscriptionEngine, TranscriptSegment
   )
   from agent.core_logging import log_event
   
   
   class DeepgramEngine(TranscriptionEngine):
       """Deepgram streaming transcription"""
       
       def __init__(self, api_key: str, model: str = "nova-2"):
           self.api_key = api_key
           self.model = model
           self.websocket = None
           self.is_streaming = False
       
       async def start_stream(self):
           """Open WebSocket connection to Deepgram"""
           try:
               # Deepgram WebSocket URL
               url = f"wss://api.deepgram.com/v1/listen?model={self.model}&punctuate=true&diarize=true"
               
               # Connect with API key
               headers = {
                   "Authorization": f"Token {self.api_key}"
               }
               
               self.websocket = await websockets.connect(
                   url,
                   extra_headers=headers
               )
               
               self.is_streaming = True
               
               log_event("deepgram_stream_started", {
                   "model": self.model
               })
               
           except Exception as e:
               log_event("deepgram_stream_start_failed", {
                   "error": str(e)
               })
               raise
       
       async def transcribe_chunk(
           self,
           audio_bytes: bytes,
           sample_rate: int = 16000
       ) -> TranscriptSegment:
           """
           Send audio chunk and get transcription.
           
           For streaming, call transcribe_stream() instead.
           """
           if not self.is_streaming:
               await self.start_stream()
           
           try:
               # Send audio to Deepgram
               await self.websocket.send(audio_bytes)
               
               # Receive response
               response_json = await self.websocket.recv()
               response = json.loads(response_json)
               
               # Parse Deepgram response
               if response.get("type") == "Results":
                   channel = response["channel"]["alternatives"][0]
                   
                   return TranscriptSegment(
                       text=channel["transcript"],
                       confidence=channel["confidence"],
                       start_time=datetime.now(),
                       end_time=datetime.now(),
                       speaker_id=None,  # Parse from diarization if needed
                       is_final=response["is_final"]
                   )
               
               # Empty result
               return TranscriptSegment(
                   text="",
                   confidence=0.0,
                   start_time=datetime.now(),
                   end_time=datetime.now(),
                   is_final=False
               )
               
           except Exception as e:
               log_event("deepgram_transcription_failed", {
                   "error": str(e)
               })
               
               return TranscriptSegment(
                   text="",
                   confidence=0.0,
                   start_time=datetime.now(),
                   end_time=datetime.now(),
                   is_final=False
               )
       
       async def transcribe_stream(
           self,
           audio_stream: AsyncIterator[bytes]
       ) -> AsyncIterator[TranscriptSegment]:
           """
           Stream audio and get continuous transcription.
           
           Yields interim and final results as they arrive.
           """
           if not self.is_streaming:
               await self.start_stream()
           
           # Create tasks for sending and receiving
           send_task = asyncio.create_task(
               self._send_audio_loop(audio_stream)
           )
           
           receive_task = asyncio.create_task(
               self._receive_transcripts_loop()
           )
           
           # Yield transcripts as they arrive
           async for segment in self._receive_transcripts_loop():
               yield segment
           
           # Wait for tasks to complete
           await send_task
           await receive_task
       
       async def _send_audio_loop(self, audio_stream: AsyncIterator[bytes]):
           """Send audio chunks to Deepgram"""
           try:
               async for audio_chunk in audio_stream:
                   if self.websocket and self.is_streaming:
                       await self.websocket.send(audio_chunk)
                   else:
                       break
               
               # Send close message
               if self.websocket:
                   await self.websocket.send(json.dumps({"type": "CloseStream"}))
               
           except Exception as e:
               log_event("deepgram_send_audio_failed", {
                   "error": str(e)
               })
       
       async def _receive_transcripts_loop(self) -> AsyncIterator[TranscriptSegment]:
           """Receive transcription results from Deepgram"""
           try:
               while self.is_streaming:
                   response_json = await self.websocket.recv()
                   response = json.loads(response_json)
                   
                   if response.get("type") == "Results":
                       channel = response["channel"]["alternatives"][0]
                       
                       segment = TranscriptSegment(
                           text=channel["transcript"],
                           confidence=channel["confidence"],
                           start_time=datetime.now(),
                           end_time=datetime.now(),
                           is_final=response["is_final"]
                       )
                       
                       if segment.text:  # Only yield non-empty
                           yield segment
                   
                   elif response.get("type") == "Metadata":
                       # Connection metadata
                       log_event("deepgram_metadata", response)
                   
           except websockets.exceptions.ConnectionClosed:
               log_event("deepgram_connection_closed")
           except Exception as e:
               log_event("deepgram_receive_failed", {
                   "error": str(e)
               })
       
       async def end_stream(self):
           """Close Deepgram connection"""
           try:
               self.is_streaming = False
               
               if self.websocket:
                   await self.websocket.close()
                   self.websocket = None
               
               log_event("deepgram_stream_ended")
               
           except Exception as e:
               log_event("deepgram_stream_end_failed", {
                   "error": str(e)
               })
       
       def supports_streaming(self) -> bool:
           """Deepgram supports true streaming"""
           return True
       
       async def get_supported_languages(self) -> list[str]:
           """Deepgram supports 36+ languages"""
           return [
               "en", "es", "fr", "de", "it", "pt", "nl", "ru",
               "zh", "ja", "ko", "ar", "hi", "tr", "pl", "uk"
               # ... (36 languages)
           ]
   ```

4. **Transcription Manager with Failover**
   
   Create `agent/meetings/transcription/manager.py`:
   
   ```python
   """
   Transcription manager with multi-provider support and failover.
   
   Automatically falls back to alternative providers if primary fails.
   """
   
   import asyncio
   from typing import AsyncIterator, Optional
   from datetime import datetime
   
   from agent.meetings.transcription.base import (
       TranscriptionEngine, TranscriptSegment, TranscriptionProvider
   )
   from agent.meetings.transcription.whisper_engine import WhisperEngine
   from agent.meetings.transcription.deepgram_engine import DeepgramEngine
   from agent.core_logging import log_event
   
   
   class TranscriptionManager:
       """
       Manages transcription with automatic failover.
       
       Tries providers in order: Deepgram → Whisper → Google
       """
       
       def __init__(
           self,
           primary_provider: TranscriptionProvider = TranscriptionProvider.DEEPGRAM,
           fallback_providers: list[TranscriptionProvider] = None
       ):
           self.primary_provider = primary_provider
           self.fallback_providers = fallback_providers or [
               TranscriptionProvider.WHISPER
           ]
           
           # Initialize engines
           self.engines: dict[TranscriptionProvider, TranscriptionEngine] = {}
           self._init_engines()
           
           # Current active engine
           self.active_engine: Optional[TranscriptionEngine] = None
           self.active_provider: Optional[TranscriptionProvider] = None
       
       def _init_engines(self):
           """Initialize all configured engines"""
           import os
           
           # Deepgram
           deepgram_key = os.getenv("DEEPGRAM_API_KEY")
           if deepgram_key:
               self.engines[TranscriptionProvider.DEEPGRAM] = DeepgramEngine(
                   api_key=deepgram_key,
                   model="nova-2"
               )
           
           # Whisper
           openai_key = os.getenv("OPENAI_API_KEY")
           if openai_key:
               self.engines[TranscriptionProvider.WHISPER] = WhisperEngine(
                   api_key=openai_key
               )
       
       async def start_transcription(
           self,
           audio_stream: AsyncIterator[bytes]
       ) -> AsyncIterator[TranscriptSegment]:
           """
           Start transcribing audio stream with automatic failover.
           
           Args:
               audio_stream: Iterator of audio chunks
               
           Yields:
               TranscriptSegment objects as transcription completes
           """
           # Try primary provider first
           providers_to_try = [self.primary_provider] + self.fallback_providers
           
           for provider in providers_to_try:
               engine = self.engines.get(provider)
               
               if not engine:
                   log_event("transcription_provider_unavailable", {
                       "provider": provider.value
                   })
                   continue
               
               try:
                   self.active_engine = engine
                   self.active_provider = provider
                   
                   log_event("transcription_started", {
                       "provider": provider.value,
                       "streaming": engine.supports_streaming()
                   })
                   
                   if engine.supports_streaming():
                       # Use streaming transcription
                       await engine.start_stream()
                       
                       async for segment in engine.transcribe_stream(audio_stream):
                           yield segment
                   else:
                       # Use chunk-based transcription
                       await engine.start_stream()
                       
                       async for audio_chunk in audio_stream:
                           segment = await engine.transcribe_chunk(audio_chunk)
                           
                           if segment.text:
                               yield segment
                   
                   # Success - no need to try fallbacks
                   break
                   
               except Exception as e:
                   log_event("transcription_provider_failed", {
                       "provider": provider.value,
                       "error": str(e)
                   })
                   
                   # Try next provider
                   continue
           
           # All providers failed
           if self.active_engine is None:
               log_event("transcription_all_providers_failed")
               raise Exception("All transcription providers failed")
       
       async def transcribe_chunk(
           self,
           audio_bytes: bytes,
           sample_rate: int = 16000
       ) -> TranscriptSegment:
           """
           Transcribe single audio chunk.
           
           Uses active engine or initializes primary.
           """
           if not self.active_engine:
               # Initialize primary provider
               self.active_provider = self.primary_provider
               self.active_engine = self.engines[self.primary_provider]
               await self.active_engine.start_stream()
           
           try:
               return await self.active_engine.transcribe_chunk(
                   audio_bytes,
                   sample_rate
               )
           except Exception as e:
               log_event("transcription_chunk_failed", {
                   "provider": self.active_provider.value,
                   "error": str(e)
               })
               
               # Try failover
               return await self._failover_transcribe_chunk(audio_bytes, sample_rate)
       
       async def _failover_transcribe_chunk(
           self,
           audio_bytes: bytes,
           sample_rate: int
       ) -> TranscriptSegment:
           """Try fallback providers for chunk transcription"""
           for provider in self.fallback_providers:
               engine = self.engines.get(provider)
               
               if not engine:
                   continue
               
               try:
                   await engine.start_stream()
                   segment = await engine.transcribe_chunk(audio_bytes, sample_rate)
                   
                   # Success - switch to this provider
                   self.active_engine = engine
                   self.active_provider = provider
                   
                   log_event("transcription_failover_success", {
                       "new_provider": provider.value
                   })
                   
                   return segment
                   
               except Exception as e:
                   log_event("transcription_failover_attempt_failed", {
                       "provider": provider.value,
                       "error": str(e)
                   })
                   continue
           
           # All failed
           return TranscriptSegment(
               text="",
               confidence=0.0,
               start_time=datetime.now(),
               end_time=datetime.now(),
               is_final=True
           )
       
       async def stop_transcription(self):
           """Stop active transcription"""
           if self.active_engine:
               await self.active_engine.end_stream()
               self.active_engine = None
               self.active_provider = None
       
       def get_active_provider(self) -> Optional[TranscriptionProvider]:
           """Get currently active provider"""
           return self.active_provider
   ```

5. **Configuration**
   
   Add to `agent/config.py`:
   
   ```python
   class TranscriptionConfig:
       """Transcription settings"""
       
       # Provider API keys
       deepgram_api_key: str = os.getenv("DEEPGRAM_API_KEY", "")
       google_credentials_path: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "")
       azure_speech_key: str = os.getenv("AZURE_SPEECH_KEY", "")
       
       # Provider preferences
       primary_provider: str = "deepgram"  # deepgram, whisper, google, azure
       fallback_providers: list[str] = ["whisper"]
       
       # Quality settings
       sample_rate: int = 16000
       enable_punctuation: bool = True
       enable_speaker_diarization: bool = True
       language: str = "en"
       
       # Performance settings
       streaming_chunk_size: int = 16000  # 1 second at 16kHz
       max_latency_ms: int = 2000  # Fail if latency exceeds this
   ```

6. **Testing**
   
   Create `agent/tests/test_transcription.py`:
   
   ```python
   """Tests for transcription engines"""
   
   import pytest
   import asyncio
   from unittest.mock import AsyncMock, patch, Mock
   
   from agent.meetings.transcription.whisper_engine import WhisperEngine
   from agent.meetings.transcription.deepgram_engine import DeepgramEngine
   from agent.meetings.transcription.manager import TranscriptionManager
   from agent.meetings.transcription.base import TranscriptionProvider
   
   
   @pytest.mark.asyncio
   async def test_whisper_transcription():
       """Test Whisper transcribes audio correctly"""
       engine = WhisperEngine(api_key="test_key")
       
       # Mock OpenAI API
       mock_response = Mock()
       mock_response.text = "Hello world"
       mock_response.language = "en"
       mock_response.get.return_value = 0.1
       
       with patch.object(engine.client.audio.transcriptions, 'create', 
                        return_value=mock_response):
           segment = await engine.transcribe_chunk(b"fake_audio_bytes")
           
           assert segment.text == "Hello world"
           assert segment.language == "en"
           assert segment.is_final is True
   
   
   @pytest.mark.asyncio
   async def test_deepgram_streaming():
       """Test Deepgram streaming transcription"""
       engine = DeepgramEngine(api_key="test_key")
       
       # Mock WebSocket
       mock_ws = AsyncMock()
       mock_ws.recv.return_value = '''
       {
           "type": "Results",
           "is_final": true,
           "channel": {
               "alternatives": [{
                   "transcript": "Test transcription",
                   "confidence": 0.95
               }]
           }
       }
       '''
       
       with patch('websockets.connect', return_value=mock_ws):
           await engine.start_stream()
           segment = await engine.transcribe_chunk(b"audio")
           
           assert segment.text == "Test transcription"
           assert segment.confidence == 0.95
           assert engine.supports_streaming() is True
   
   
   @pytest.mark.asyncio
   async def test_transcription_failover():
       """Test manager fails over to backup provider"""
       manager = TranscriptionManager(
           primary_provider=TranscriptionProvider.DEEPGRAM,
           fallback_providers=[TranscriptionProvider.WHISPER]
       )
       
       # Mock primary to fail
       deepgram_engine = Mock()
       deepgram_engine.transcribe_chunk = AsyncMock(
           side_effect=Exception("Primary failed")
       )
       manager.engines[TranscriptionProvider.DEEPGRAM] = deepgram_engine
       
       # Mock fallback to succeed
       whisper_engine = Mock()
       whisper_mock_segment = Mock()
       whisper_mock_segment.text = "Fallback success"
       whisper_engine.transcribe_chunk = AsyncMock(
           return_value=whisper_mock_segment
       )
       whisper_engine.start_stream = AsyncMock()
       manager.engines[TranscriptionProvider.WHISPER] = whisper_engine
       
       # Should use fallback
       segment = await manager.transcribe_chunk(b"audio")
       
       assert segment.text == "Fallback success"
       assert manager.get_active_provider() == TranscriptionProvider.WHISPER
   ```

**Acceptance Criteria:**

- [ ] TranscriptionEngine base class defined
- [ ] WhisperEngine works with OpenAI API
- [ ] DeepgramEngine supports true streaming
- [ ] TranscriptionManager implements failover
- [ ] Latency <2 seconds for Whisper, <100ms for Deepgram
- [ ] Confidence scores provided
- [ ] Multiple languages supported
- [ ] Streaming and chunk-based modes both work
- [ ] All tests pass (minimum 12 test cases)
- [ ] Documentation includes API setup guides

**Files to Create:**
- `agent/meetings/transcription/__init__.py` (~20 lines)
- `agent/meetings/transcription/base.py` (~150 lines)
- `agent/meetings/transcription/whisper_engine.py` (~200 lines)
- `agent/meetings/transcription/deepgram_engine.py` (~350 lines)
- `agent/meetings/transcription/manager.py` (~250 lines)
- `agent/tests/test_transcription.py` (~250 lines)

**Files to Modify:**
- `agent/config.py` — Add TranscriptionConfig
- `.env.example` — Add transcription API keys

**References:**
- OpenAI Whisper API: https://platform.openai.com/docs/guides/speech-to-text
- Deepgram API: https://developers.deepgram.com/
- Google Speech-to-Text: https://cloud.google.com/speech-to-text/docs

---

