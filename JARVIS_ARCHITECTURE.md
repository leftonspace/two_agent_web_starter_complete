# Jarvis AI Assistant - Complete Architecture Overview

## 1. PROJECT STRUCTURE

```
two_agent_web_starter_complete/
├── orchestrator.py                          # Root shim entry point
├── start_webapp.py                          # Web server launcher
├── agent/
│   ├── orchestrator.py                      # Main multi-agent orchestrator (PHASE 3)
│   ├── conversational_agent.py              # Natural language chat interface
│   ├── jarvis_chat.py                       # Intelligent request router
│   ├── agent_messaging.py                   # Agent-to-user messaging bus
│   ├── llm.py                               # LLM integration layer
│   ├── specialists.py                       # Specialist agent profiles
│   ├── roles.py                             # Role-based profiles system
│   │
│   ├── execution/
│   │   └── employee_pool.py                 # Multi-worker employee pool
│   │
│   ├── webapp/
│   │   ├── app.py                           # FastAPI application root
│   │   ├── chat_api.py                      # Chat API endpoints
│   │   ├── auth.py                          # Authentication system
│   │   ├── auth_routes.py                   # Auth API routes
│   │   ├── templates/
│   │   │   ├── jarvis.html                  # Chat interface UI
│   │   │   ├── index.html                   # Dashboard home
│   │   │   ├── job_detail.html              # Job monitoring
│   │   │   └── ...                          # Other pages
│   │
│   ├── workflows/                           # Task workflow definitions
│   ├── tools/                               # Tool implementations
│   ├── llm/                                 # Phase 9 LLM package
│   ├── memory/                              # Session/memory management
│   │
│   └── ...other modules
```

---

## 2. SYSTEM ARCHITECTURE OVERVIEW

### High-Level Flow Diagram

```
User Input (Chat/UI)
        ↓
    [Jarvis Chat] (jarvis_chat.py)
        ↓
    Intent Analysis (Simple/Complex/File/Conversation)
        ↓
    ┌─────────────────────────────────────────┐
    │                                         │
    ├──→ [Simple Query] → Direct LLM         │
    ├──→ [File Operation] → Targeted Edit    │
    ├──→ [Conversation] → Casual Response    │
    └──→ [Complex Task] → Orchestrator       │
                ↓
    [Multi-Agent Orchestrator] (orchestrator.py)
        ↓
    1. MANAGER PLANNING
        ↓ (Creates initial plan)
        ↓
    2. SUPERVISOR PHASING
        ↓ (Breaks into stages)
        ↓
    3. EMPLOYEE EXECUTION
        ↓ (Executes in phases with audit cycles)
        ↓
    4. MANAGER REVIEW
        ↓ (Validates results)
        ↓
    5. Iteration Loop (repeat if needed)
        ↓
    [Results] → UI/Chat Response
```

---

## 3. ORCHESTRATOR ARCHITECTURE (Main Coordination System)

### Phase 3 Orchestrator Features

**File**: `/home/user/two_agent_web_starter_complete/agent/orchestrator.py` (2200+ lines)

#### Three-Loop Execution Pattern

```python
# From orchestrator.py lines 782-1065

1. MANAGER PLANNING (Line 782-845)
   ├─ Analyzes the task
   ├─ Creates detailed plan with steps
   ├─ Defines acceptance criteria
   └─ Returns: JSON plan with stages

2. SUPERVISOR PHASING (Line 875-922)
   ├─ Takes manager's plan
   ├─ Breaks into phases (2-5 phases)
   ├─ Each phase has categories and steps
   └─ Returns: List of phases with dependencies

3. EMPLOYEE EXECUTION (Line 1065+)
   ├─ Executes one phase at a time
   ├─ Has adaptive fix cycle (audit loops)
   ├─ Receives feedback from supervisor
   ├─ Iterates until phase complete
   └─ Returns: Modified files and artifacts

4. MANAGER REVIEW (After each phase)
   ├─ Audits employee's work
   ├─ Checks against acceptance criteria
   ├─ Can request fixes or approve
   └─ Returns: Approval or feedback
```

### Key Configuration Parameters

```python
cfg = {
    "task": str,                           # What to build
    "project_subdir": str,                 # Where to build
    "max_rounds": int,                     # Max iterations
    "max_audits_per_stage": int,          # Fix cycles per phase
    "max_cost_usd": float,                # Spending limit
    "use_git": bool,                       # Version control
    "use_visual_review": bool,            # DOM analysis
    "mode": "3loop" | "2loop"             # Orchestration pattern
}
```

---

## 4. MULTI-AGENT SYSTEM COORDINATION

### Agent Roles

**File**: `/home/user/two_agent_web_starter_complete/agent/agent_messaging.py`

```python
class AgentRole(Enum):
    MANAGER = "manager"           # Strategic planning & review
    SUPERVISOR = "supervisor"     # Task phasing & decomposition
    EMPLOYEE = "employee"         # Implementation & execution
    SYSTEM = "system"             # System messages
```

### Manager Agent (Strategic Orchestrator)
- **Role**: Plans work, reviews employee output
- **System Prompt**: Provided via `prompts_default.json`
- **Model**: Configurable via model router
- **Task**: Creates hierarchical plans with acceptance criteria
- **Entry Point**: Lines 782-845 in orchestrator.py

### Supervisor Agent (Task Decomposer)
- **Role**: Breaks manager's plan into executable phases
- **System Prompt**: Built from manager prompts (line 599)
- **Task**: Creates 2-5 phases with categories
- **Entry Point**: Lines 875-922 in orchestrator.py

### Employee Agent(s) (Implementer)
- **Role**: Executes phases, creates/modifies files
- **System Prompt**: Injected with:
  - Domain knowledge (if domain routing available)
  - Specialist expertise (if recommended)
  - Available tools list
  - Phase context and previous stage summaries
- **Execution**: Loops through adaptive fix cycles
- **Entry Point**: Lines 1065+ in orchestrator.py

### Inter-Agent Communication

**File**: `/home/user/two_agent_web_starter_complete/agent/inter_agent_bus.py`

```python
class AgentMessageBus:
    """Message bus for horizontal agent communication"""
    
    async def post_message(
        role: AgentRole,              # Who's sending
        content: str,                 # Message
        requires_response: bool,      # Wait for reply?
        response_timeout: int         # How long?
    ) -> Optional[str]:               # User response if needed
        pass
    
    # Used for:
    # - Employee asking manager for clarification
    # - Manager broadcasting updates to team
    # - Waiting for user approval on risky actions
```

---

## 5. WEBAPP ARCHITECTURE

### FastAPI Entry Point

**File**: `/home/user/two_agent_web_starter_complete/agent/webapp/app.py` (1500+ lines)

#### Routes Structure

```python
# Authentication Routes (PHASE 1.1)
/auth/*                    # Login, logout, session management

# Chat Interface Routes
/jarvis                    # Main chat UI (HTML)
/api/chat/*                # Chat API endpoints

# Dashboard Routes
/                          # Redirect to /jarvis
/dashboard                 # Legacy orchestrator dashboard
/run/{run_id}             # View specific run
/projects/{project_id}    # Browse project files
/projects                 # List all projects

# Job Management Routes (STAGE 8)
/jobs                     # List all background jobs
/jobs/{job_id}            # View job details with live logs
/jobs/{job_id}/rerun      # Rerun a job
/run                      # Start new job (form POST)

# API Routes
/api/jobs                 # List jobs (JSON)
/api/history              # Run history (JSON)
/api/projects             # List projects (JSON)
/api/run/{run_id}        # Get run details (JSON)
```

#### Key Endpoints

```python
@app.post("/run")
async def start_run(
    project_subdir: str,
    mode: str,                    # "2loop" or "3loop"
    task: str,
    max_rounds: int,
    max_cost_usd: float,
    current_user: User            # PHASE 1.1: Auth required
):
    """Start background job (non-blocking)"""
    job = job_manager.create_job(config)
    job_manager.start_job(job.id)
    return RedirectResponse(url=f"/jobs/{job.id}")
```

---

## 6. CHAT INTERFACE (Jarvis)

### Entry Point: jarvis_chat.py

**File**: `/home/user/two_agent_web_starter_complete/agent/jarvis_chat.py` (600+ lines)

### Intent-Based Routing System

```python
class IntentType(Enum):
    SIMPLE_QUERY = "simple_query"      # Questions/explanations
    COMPLEX_TASK = "complex_task"      # Build/create projects
    FILE_OPERATION = "file_operation"  # Edit specific files
    CONVERSATION = "conversation"      # Casual chat
```

### Message Flow

```python
async def handle_message(user_message: str) -> Dict:
    # Step 1: Add to history
    self.conversation_history.append(user_message)
    
    # Step 2: Analyze intent using LLM
    intent = await self.analyze_intent(user_message)
    # Returns: IntentType, confidence, reasoning, target files
    
    # Step 3: Route based on type
    if intent.type == IntentType.SIMPLE_QUERY:
        response = await self.handle_simple_query(user_message)
        # → Direct LLM call for question answering
        
    elif intent.type == IntentType.COMPLEX_TASK:
        response = await self.handle_complex_task(user_message)
        # → Spawn orchestrator subprocess
        # → Create project_path = sites/{project_name}
        # → Wait for orchestrator.main() to return
        
    elif intent.type == IntentType.FILE_OPERATION:
        response = await self.handle_file_operation(user_message)
        # → Extract target files from message
        # → Ask for clarification if needed
        
    else:  # CONVERSATION
        response = await self.handle_conversation(user_message)
        # → Direct LLM casual response
    
    # Step 4: Store in memory (if enabled)
    await self.store_interaction(user_message, response)
    
    # Step 5: Return to UI
    return response
```

### Complex Task Handling (Orchestrator Integration)

```python
async def handle_complex_task(message: str, context: Dict, intent: Intent):
    """Route to orchestrator for multi-agent execution"""
    
    # Extract project name from message or generate
    project_name = intent.project_name or self._extract_project_name(message)
    # Examples: "Build a blog" → "blog"
    
    # Prepare orchestrator config
    config = {
        "task": message,
        "project_subdir": project_name,
        "max_rounds": 3,
        "max_cost_usd": 1.5,
        "use_git": True,
        "prompts_file": "prompts_default.json"
    }
    
    # Create orchestrator context
    orch_context = OrchestratorContext.create_default(config)
    
    # Run orchestrator in thread pool (non-blocking)
    result = await asyncio.to_thread(
        orchestrator_main,
        cfg_override=config,
        context=orch_context
    )
    
    # Format response with results
    return {
        "content": f"✓ Task complete! Created {project_name}...",
        "metadata": {
            "type": "complex_task",
            "project_name": project_name,
            "files_created": result.get("files_modified", []),
            "cost": result.get("cost_summary", {}).get("total_usd", 0.0),
            "orchestrator_result": result
        }
    }
```

---

## 7. CHAT API & WEB UI INTEGRATION

**Files**:
- `/home/user/two_agent_web_starter_complete/agent/webapp/chat_api.py`
- `/home/user/two_agent_web_starter_complete/agent/webapp/templates/jarvis.html`

### REST API Endpoints

```python
POST /api/chat/session/start          # Start new session
POST /api/chat/message                # Send message, get response
POST /api/chat/message/stream         # Stream response (SSE)
GET  /api/chat/history                # Get conversation history
POST /api/chat/file/attach            # Attach file to conversation
POST /api/chat/file/upload            # Upload file
GET  /api/chat/file/read              # Read file content
GET  /api/chat/status                 # System status
```

### Frontend Chat Interface (jarvis.html)

```html
<!-- Sidebar: Conversation history -->
<div class="sidebar">
  <div class="conversations">
    <div class="conversation-item active">...</div>
  </div>
</div>

<!-- Main Chat Area -->
<div class="chat-main">
  <div class="chat-header">Chat with Jarvis</div>
  
  <div class="messages-container">
    <!-- Messages inserted here -->
    <div class="message user">
      <div class="message-avatar">👤</div>
      <div class="message-content">Your message</div>
    </div>
    <div class="message assistant">
      <div class="message-avatar">🤖</div>
      <div class="message-content">Jarvis response</div>
    </div>
  </div>
  
  <div class="input-area">
    <textarea id="messageInput" placeholder="Type your message..."></textarea>
    <button onclick="sendMessage()">Send</button>
  </div>
</div>
```

### Frontend JavaScript Logic

```javascript
async function sendMessage() {
    const message = document.getElementById("messageInput").value;
    
    // Add user message to display
    addMessageToUI("user", message);
    
    // Send to API
    const response = await fetch("/api/chat/message", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: message})
    });
    
    const data = await response.json();
    
    // Add assistant response to display
    addMessageToUI("assistant", data.content);
    
    // Handle metadata (files created, orchestrator results, etc.)
    if (data.metadata.type === "complex_task") {
        displayProjectCreated(data.metadata.project_name);
    }
}
```

---

## 8. CONVERSATIONAL INTERACTION PATTERNS

### Follow-Up Question Handling

The system maintains conversation context across interactions:

```python
# From conversational_agent.py

class ConversationalAgent:
    def __init__(self):
        self.conversation_history: List[ConversationMessage] = []
        # Stores all user/assistant messages in order
        
    async def chat(self, user_message: str) -> str:
        # Step 1: Add user message
        self._add_message("user", user_message)
        
        # Step 2: Get memory context for this query
        memory_context = await self.business_memory.get_context_for_query(user_message)
        
        # Step 3: Parse intent WITH context
        intent = await self._parse_intent(user_message, memory_context)
        
        # Step 4: Handle with full conversation history
        response = await self._handle_complex_task(
            intent, 
            user_message, 
            memory_context,
            self.conversation_history  # ← Full context
        )
        
        # Step 5: Add response to history
        self._add_message("assistant", response)
        
        return response
```

### Conversation Context in Intent Analysis

```python
async def analyze_intent(message: str, context: Dict) -> Intent:
    # Build context from recent messages
    history_context = "\n".join([
        f"{msg.role}: {msg.content}"
        for msg in self.conversation_history[-5:]  # Last 5 messages
    ])
    
    prompt = f"""Analyze this user request in context of recent conversation:
    
Recent conversation:
{history_context}

User's new message: {message}

Classify as: simple_query | complex_task | file_operation | conversation"""
    
    # LLM understands conversation flow and can answer follow-ups
    # Example:
    #   User: "Build a website for my business"
    #   → complex_task (creates orchestrator job)
    #   
    #   User: "Add a contact form to the home page"
    #   → file_operation (targets home.html)
    #   → LLM remembers it's for the website from line 1
```

### Multi-Turn Approval Flow

```python
# Agent messaging for approvals

async def request_user_approval(
    message: str,
    requires_response: bool = True,
    response_timeout: int = 300
) -> Optional[str]:
    """Post message to user and wait for response"""
    
    response = await bus.post_message(
        role=AgentRole.MANAGER,
        content=f"⚠️ Risk Alert: {message}. Proceed? [yes/no]",
        requires_response=True,
        response_timeout=300  # Wait 5 minutes
    )
    
    return response  # "yes", "no", or None (timeout)
```

---

## 9. TASK EXECUTION FLOW - DETAILED WALKTHROUGH

### Example: User Asks "Build a landing page"

```
1. User enters in chat: "Build a landing page"
   └─ jarvis_chat.py:handle_message()

2. Intent Analysis
   └─ analyze_intent() detects: COMPLEX_TASK (confidence: 0.95)
   └─ Extracts project_name: "landing-page"

3. Complex Task Handler Triggered
   └─ handle_complex_task()
   └─ Prepares config:
       {
           "task": "Build a landing page",
           "project_subdir": "landing-page",
           "max_rounds": 3,
           "max_cost_usd": 1.5,
           "use_git": True,
           "prompts_file": "prompts_default.json"
       }

4. Orchestrator Started (in thread pool)
   └─ orchestrator.main(cfg_override=config)
   
   4a. MANAGER PLANNING (orchestrator.py:782)
       ├─ LLM call: "Plan how to build a landing page"
       ├─ Manager analyzes task
       ├─ Creates plan: [
       │    {"step": 1, "description": "Create HTML structure"},
       │    {"step": 2, "description": "Style with CSS"},
       │    {"step": 3, "description": "Add interactivity"}
       │   ]
       └─ Defines acceptance criteria
       
   4b. SUPERVISOR PHASING (orchestrator.py:875)
       ├─ LLM call: "Break plan into phases"
       ├─ Supervisor decomposes:
       │   [
       │    {"name": "Structure Phase", "categories": ["html"], "plan_steps": [1]},
       │    {"name": "Styling Phase", "categories": ["css"], "plan_steps": [2]},
       │    {"name": "Interactivity Phase", "categories": ["javascript"], "plan_steps": [3]}
       │   ]
       └─ Returns 3 phases
       
   4c. EMPLOYEE EXECUTION (orchestrator.py:1065)
       
       For each phase:
       ├─ Iteration 1, Audit Cycle 0:
       │  ├─ Load existing files from sites/landing-page/
       │  ├─ Employee receives:
       │  │  ├─ Task description
       │  │  ├─ Current phase (e.g., "Structure Phase")
       │  │  ├─ Plan steps for this phase
       │  │  ├─ Previous phase summaries (if any)
       │  │  ├─ Available tools (write_file, run_tests, git_commit, etc.)
       │  │  └─ System prompt with expertise
       │  │
       │  ├─ LLM call: Employee creates/modifies files
       │  └─ Files written:
       │     ├─ sites/landing-page/index.html
       │     └─ Git commit: "Create HTML structure"
       │
       └─ Audit Cycle 1:
          ├─ Supervisor reviews work: "Are the acceptance criteria met?"
          ├─ If findings: Feedback list generated
          ├─ Manager reviews feedback
          ├─ If fixes needed: Loop back to Employee with feedback
          └─ If complete: Advance to next phase

5. Results Collected
   └─ orchestrator.main() returns:
      {
          "status": "success",
          "files_modified": [
              "sites/landing-page/index.html",
              "sites/landing-page/style.css",
              "sites/landing-page/script.js"
          ],
          "cost_summary": {"total_usd": 0.45},
          "rounds_completed": 2
      }

6. Response Sent to User
   └─ jarvis_chat.py formats response:
      "✓ Task complete!
       
       I've created your project: landing-page
       
       📁 Location: sites/landing-page
       
       📄 Files created (3):
         • index.html
         • style.css
         • script.js
       
       💰 Cost: $0.45
       ⏱️ Rounds: 2
       
       What would you like to do next?"
```

---

## 10. KEY FILES REFERENCE

| File | Lines | Purpose |
|------|-------|---------|
| `orchestrator.py` | 2200+ | Main 3-loop orchestrator with Manager/Supervisor/Employee coordination |
| `jarvis_chat.py` | 600+ | Intent routing and multi-handler system |
| `conversational_agent.py` | 800+ | NLP-based task planning and execution tracking |
| `agent_messaging.py` | 300+ | Agent-to-user message bus with approval workflows |
| `webapp/app.py` | 1500+ | FastAPI routes for dashboard and job management |
| `webapp/chat_api.py` | 270+ | REST API for chat functionality |
| `execution/employee_pool.py` | 250+ | Worker pool for parallel task execution |
| `specialists.py` | 500+ | Specialist profiles with task matching |
| `roles.py` | 380+ | Role-based system with hierarchy levels |
| `llm.py` | 850+ | LLM integration with model routing and cost tracking |

---

## 11. ENTRY POINTS FOR USER INTERACTION

### 1. **Web Chat Interface** (Recommended for most users)
   - **URL**: `http://localhost:8000/jarvis`
   - **Entry**: `webapp/app.py:home()` → Redirects to `/jarvis`
   - **Handler**: `webapp/templates/jarvis.html` (Frontend) → `/api/chat/*` (Backend)
   - **Type**: Conversational, multi-turn, context-aware

### 2. **API Chat Endpoints**
   - **POST** `/api/chat/message` - Send single message
   - **POST** `/api/chat/message/stream` - Stream response
   - **GET** `/api/chat/history` - Get conversation history
   - **Use Case**: Programmatic access, integrations

### 3. **Web Dashboard** (Legacy, still supported)
   - **URL**: `http://localhost:8000/dashboard`
   - **Entry**: `webapp/app.py:dashboard()`
   - **Type**: Form-based project/task submission
   - **Returns**: Job ID for background execution

### 4. **Command Line Orchestrator**
   - **Entry**: `python orchestrator.py`
   - **Type**: Direct Python API
   - **Config**: Via JSON file or programmatically

---

## 12. EXISTING PATTERNS FOR FOLLOW-UP & INTERACTION

### Pattern 1: Conversational Continuity
The system maintains full conversation history and uses it for intent analysis:
```python
# Every message includes last 5 conversation turns
# Allows: "Build a website" → "Add a login page" (understands context)
```

### Pattern 2: Agent Approval Requests
Multi-agent messaging bus supports approval workflows:
```python
# Manager can ask employee: "Should I make this change?"
# Employee awaits response with timeout
# Message appears in user chat with [YES] [NO] buttons
```

### Pattern 3: Task Tracking with Status Updates
Active tasks tracked in conversational agent:
```python
class TaskExecution:
    task_id: str
    status: str  # 'planning', 'executing', 'completed', 'failed'
    steps: List  # Current step tracking
    result: Optional[Any]  # Final results
```

### Pattern 4: Contextual File Handling
Chat can handle file attachments and context:
```python
# User: "Fix the bug in login.js"
# → FILE_OPERATION intent
# → Loads login.js content
# → Sends to employee with full file context
# → Employee modifies and returns
```

### Pattern 5: Business Memory Learning
System learns from interactions:
```python
# Stores: User preferences, project patterns, specialist choices
# Retrieves: Relevant context when similar task appears
# Uses: For intent analysis and prompt enhancement
```

---

## SUMMARY

**Jarvis** is a sophisticated multi-agent AI system that:

1. **Understands Intent** - Analyzes user requests to route to appropriate handler
2. **Maintains Context** - Remembers conversation history for follow-ups
3. **Coordinates Agents** - Manager, Supervisor, Employee working together
4. **Executes Tasks** - Breaks complex work into phases and iterates
5. **Provides Feedback** - Streams progress via message bus and UI
6. **Learns Over Time** - Stores interactions in business memory
7. **Handles Approvals** - Waits for user confirmation on important decisions
8. **Tracks Execution** - Logs all steps, costs, and results

The system bridges natural language interaction (chat) with sophisticated multi-agent orchestration, making it feel conversational while delivering powerful autonomous task execution.

