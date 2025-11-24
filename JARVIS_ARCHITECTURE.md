# JARVIS AI Assistant - Complete Architecture (v2.1)

> Last Updated: 2025-11-24
> Version: 2.1.0 (Autonomous Agent with Claude Code-like Tools)

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Project Structure](#2-project-structure)
3. [Architecture Diagram](#3-architecture-diagram)
4. [Core Components](#4-core-components)
5. [Tools System](#5-tools-system)
6. [Memory System](#6-memory-system)
7. [Multi-Agent Orchestrator](#7-multi-agent-orchestrator)
8. [Configuration System](#8-configuration-system)
9. [API Reference](#9-api-reference)
10. [Web Interface](#10-web-interface)
11. [Related Documentation](#11-related-documentation)

---

## 1. System Overview

JARVIS is a sophisticated AI assistant that combines:

| Feature | Description |
|---------|-------------|
| **Natural Language Chat** | Conversational interface with intent routing |
| **Claude Code-like Tools** | File operations, code search, shell execution |
| **Autonomous Agent** | Proactive tool usage with streaming visibility |
| **Multi-Agent Orchestration** | Manager/Supervisor/Employee coordination |
| **Persistent Memory** | User profiles, preferences, and context retention |
| **Vision & Voice** | Image analysis and speech capabilities |
| **Session Isolation** | Per-chat history with shared long-term memory |

### Key Design Principles

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                           │
│                    (Chat / Voice / Vision / API)                     │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         JARVIS CHAT ROUTER                           │
│               (jarvis_chat.py - Intent Classification)               │
│                                                                      │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│   │ Simple  │  │ Complex │  │  File   │  │  Tool   │  │Conversa-│  │
│   │ Query   │  │  Task   │  │Operation│  │Operation│  │  tion   │  │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  │
└────────┼───────────┼────────────┼────────────┼────────────┼────────┘
         │           │            │            │            │
         ▼           ▼            ▼            ▼            ▼
    Direct LLM   Orchestrator   Targeted    Autonomous   Casual
    Response     (3-Loop)       Edit        Agent        Response
```

---

## 2. Project Structure

```
two_agent_web_starter_complete/
├── orchestrator.py                      # Root entry point
├── start_webapp.py                      # Web server launcher
├── JARVIS_ARCHITECTURE.md               # This document
│
├── agent/
│   ├── jarvis_chat.py                   # Intent router & main handler
│   ├── jarvis_tools.py                  # Claude Code-like tools system
│   ├── jarvis_agent.py                  # Autonomous tool-using agent
│   ├── jarvis_persona.py                # JARVIS personality definition
│   ├── jarvis_vision.py                 # Image analysis capabilities
│   ├── jarvis_voice.py                  # Speech synthesis/recognition
│   ├── jarvis_voice_chat.py             # Voice conversation handler
│   │
│   ├── orchestrator.py                  # Multi-agent orchestrator (3-loop)
│   ├── conversational_agent.py          # NLP-based task planning
│   ├── agent_messaging.py               # Agent-to-user message bus
│   ├── inter_agent_bus.py               # Agent-to-agent communication
│   ├── llm.py                           # LLM integration layer
│   ├── specialists.py                   # Specialist agent profiles
│   ├── roles.py                         # Role-based profiles
│   │
│   ├── config/
│   │   ├── agents.yaml                  # Agent definitions & tools
│   │   └── tasks.yaml                   # Task templates & workflows
│   │
│   ├── memory/
│   │   ├── session_manager.py           # Session & conversation state
│   │   ├── user_profile.py              # Adaptive user profiles
│   │   ├── long_term.py                 # Persistent memory storage
│   │   ├── short_term.py                # Working memory
│   │   ├── vector_store.py              # Semantic search (ChromaDB)
│   │   ├── entity.py                    # Entity extraction
│   │   ├── preference_learner.py        # Learns user preferences
│   │   └── context_retriever.py         # Context fetching
│   │
│   ├── webapp/
│   │   ├── app.py                       # FastAPI application root
│   │   ├── chat_api.py                  # Chat REST endpoints
│   │   ├── agent_api.py                 # Agent WebSocket/REST endpoints
│   │   ├── code_api.py                  # Code operations API
│   │   ├── finance_api.py               # Finance tools API
│   │   ├── admin_api.py                 # Administration API
│   │   ├── auth.py                      # Authentication system
│   │   └── templates/
│   │       ├── jarvis.html              # Main chat interface
│   │       ├── index.html               # Dashboard
│   │       └── ...
│   │
│   ├── tools/
│   │   ├── base.py                      # Tool base classes
│   │   ├── plugin_loader.py             # Dynamic tool loading
│   │   ├── audit_report.py              # Audit report generation
│   │   └── compliance_audit_report.py   # Compliance checking
│   │
│   └── execution/
│       └── employee_pool.py             # Worker pool for parallel execution
│
└── docs/
    ├── WINDOWS_SETUP_GUIDE.md           # Installation & setup
    ├── JARVIS_2_0_CONFIGURATION_GUIDE.md
    ├── JARVIS_2_0_MEMORY_GUIDE.md
    ├── JARVIS_2_0_API_REFERENCE.md
    └── ...
```

---

## 3. Architecture Diagram

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                 │
├─────────────────┬─────────────────┬──────────────────┬─────────────────────┤
│   Web Chat UI   │   REST API      │   WebSocket      │   Voice/Vision      │
│  (jarvis.html)  │ (/api/chat/*)   │ (/api/agent/ws)  │ (/api/vision/*)     │
└────────┬────────┴────────┬────────┴────────┬─────────┴──────────┬──────────┘
         │                 │                 │                    │
         └─────────────────┴────────┬────────┴────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JARVIS CHAT ROUTER                                 │
│                          (agent/jarvis_chat.py)                              │
│                                                                              │
│  ┌─────────────────┐    ┌──────────────────────────────────────────────┐   │
│  │ Intent Analysis │───▶│  Routes to:                                   │   │
│  │  (LLM-powered)  │    │  • simple_query    → Direct LLM response     │   │
│  │                 │    │  • complex_task    → Orchestrator            │   │
│  │  Detects:       │    │  • file_operation  → Targeted file edit      │   │
│  │  • Type         │    │  • tool_operation  → Autonomous Agent        │   │
│  │  • Confidence   │    │  • conversation    → Casual chat             │   │
│  │  • Target files │    │  • code_analysis   → Code search/explain     │   │
│  └─────────────────┘    └──────────────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────────┐    ┌─────────────────────────┐
│  AUTONOMOUS      │    │  MULTI-AGENT         │    │  MEMORY SYSTEM          │
│  AGENT           │    │  ORCHESTRATOR        │    │                         │
│  (jarvis_agent)  │    │  (orchestrator.py)   │    │  ┌─────────────────┐   │
│                  │    │                      │    │  │ Session Manager │   │
│  ┌────────────┐  │    │  Manager             │    │  │ (Per-Chat)      │   │
│  │ Tools      │  │    │    ↓                 │    │  └────────┬────────┘   │
│  │ System     │  │    │  Supervisor          │    │           │            │
│  │(jarvis_    │  │    │    ↓                 │    │  ┌────────▼────────┐   │
│  │ tools.py)  │  │    │  Employee(s)         │    │  │ User Profile    │   │
│  │            │  │    │    ↓                 │    │  │ (Persistent)    │   │
│  │ • read     │  │    │  Review Loop         │    │  └────────┬────────┘   │
│  │ • edit     │  │    │                      │    │           │            │
│  │ • write    │  │    │  Creates:            │    │  ┌────────▼────────┐   │
│  │ • bash     │  │    │  • Files             │    │  │ Adaptive Memory │   │
│  │ • grep     │  │    │  • Tests             │    │  │ (Long-term)     │   │
│  │ • glob     │  │    │  • Documentation     │    │  └─────────────────┘   │
│  │ • todo     │  │    │                      │    │                         │
│  │ • web_*    │  │    └──────────────────────┘    └─────────────────────────┘
│  └────────────┘  │
│                  │
│  Streams:        │
│  • thinking      │
│  • tool_call     │
│  • tool_result   │
│  • response      │
└──────────────────┘
```

### Memory System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MEMORY SYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────┐     ┌─────────────────────────────────┐   │
│  │    PER-CHAT (Isolated)      │     │     PERSISTENT (Shared)          │   │
│  │                             │     │                                   │   │
│  │  conversation_history[]     │     │  AdaptiveMemoryManager            │   │
│  │                             │     │  ┌───────────────────────────┐   │   │
│  │  • Cleared on "New Chat"    │     │  │ User Profile              │   │   │
│  │  • Stored in SessionManager │     │  │ • display_name            │   │   │
│  │  • Messages: user/assistant │     │  │ • traits (detected/stated)│   │   │
│  │                             │     │  │ • communication_style     │   │   │
│  │  Why isolated?              │     │  │ • expertise_levels        │   │   │
│  │  → Each chat is separate    │     │  │ • preferences             │   │   │
│  │  → No "continuing previous" │     │  └───────────────────────────┘   │   │
│  │                             │     │                                   │   │
│  └─────────────────────────────┘     │  ┌───────────────────────────┐   │   │
│                                      │  │ User Memories             │   │   │
│  ┌─────────────────────────────┐     │  │ • Personal (name, role)   │   │   │
│  │    WORKING MEMORY           │     │  │ • Preferences             │   │   │
│  │                             │     │  │ • Business context        │   │   │
│  │  • Current task context     │     │  │ • Custom ("remember...")  │   │   │
│  │  • Active projects          │     │  └───────────────────────────┘   │   │
│  │  • Recent file operations   │     │                                   │   │
│  │  • Tool execution history   │     │  Persistence: SQLite + JSON       │   │
│  └─────────────────────────────┘     │  Location: data/memory/           │   │
│                                      └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Core Components

### 4.1 JARVIS Chat Router (`jarvis_chat.py`)

The central routing system that classifies user intent and delegates to appropriate handlers.

**File**: `agent/jarvis_chat.py` (~2300 lines)

```python
class IntentType(Enum):
    SIMPLE_QUERY = "simple_query"       # Questions, explanations
    COMPLEX_TASK = "complex_task"       # Build projects, multi-step work
    FILE_OPERATION = "file_operation"   # Edit specific files
    TOOL_OPERATION = "tool_operation"   # Use Claude Code-like tools
    CONVERSATION = "conversation"       # Casual chat
    CODE_ANALYSIS = "code_analysis"     # Analyze, explain code

class JarvisChat:
    async def handle_message(self, user_message: str, context: Dict) -> Dict:
        # 1. Add to conversation history
        # 2. Analyze intent using LLM
        # 3. Route to appropriate handler
        # 4. Store interaction in memory
        # 5. Return response
```

**Related Docs**: [CONVERSATIONAL_AGENT.md](docs/CONVERSATIONAL_AGENT.md)

---

### 4.2 JARVIS Persona (`jarvis_persona.py`)

Defines the canonical JARVIS personality - a sophisticated British butler AI.

**File**: `agent/jarvis_persona.py`

**Key Traits**:
- Upper-class British English, dry wit
- Addresses user as "sir" or "madam"
- Anticipates needs, acts without being asked
- Multilingual capabilities
- Self-diagnosis abilities
- Context memory awareness

**Creator Acknowledgment**: Recognizes Kevin as creator

**Related Docs**: [JARVIS_2_0_PATTERN_GUIDE.md](docs/JARVIS_2_0_PATTERN_GUIDE.md)

---

### 4.3 Vision System (`jarvis_vision.py`)

Visual perception capabilities for image analysis.

**File**: `agent/jarvis_vision.py`

| Feature | Description |
|---------|-------------|
| Image Analysis | GPT-4 Vision / Claude Vision |
| Scene Understanding | Object and scene detection |
| OCR | Text extraction from images |
| Camera Feed | Real-time frame analysis |

**API Endpoint**: `POST /api/vision/chat`

---

### 4.4 Voice System (`jarvis_voice.py`)

Text-to-speech and speech-to-text capabilities.

**File**: `agent/jarvis_voice.py`

| Provider | Description |
|----------|-------------|
| ElevenLabs | Premium voice cloning (recommended) |
| OpenAI TTS | "Onyx" British voice (fallback) |
| Browser STT | Web Speech API recognition |

**Related Docs**: See voice setup in [WINDOWS_SETUP_GUIDE.md](docs/WINDOWS_SETUP_GUIDE.md)

---

## 5. Tools System

### 5.1 JARVIS Tools (`jarvis_tools.py`)

Claude Code-like capabilities for file operations, code search, and execution.

**File**: `agent/jarvis_tools.py`

```python
class ToolType(Enum):
    READ = "read"           # Read file contents
    EDIT = "edit"           # Find & replace in files
    WRITE = "write"         # Create/overwrite files
    BASH = "bash"           # Execute shell commands
    GREP = "grep"           # Search file contents (regex)
    GLOB = "glob"           # Find files by pattern
    TODO = "todo"           # Track tasks visibly
    WEB_SEARCH = "web_search"   # Search the web
    WEB_FETCH = "web_fetch"     # Fetch web page content
```

#### Tool Reference

| Tool | Method | Description | Safety |
|------|--------|-------------|--------|
| `read` | `tools.read(path, start, end)` | Read file lines | Max 10MB |
| `edit` | `tools.edit(path, old, new)` | Replace string | Backup created |
| `write` | `tools.write(path, content)` | Create file | Directory created |
| `bash` | `tools.bash(cmd, timeout)` | Run command | Blocked: rm -rf, format, etc. |
| `grep` | `tools.grep(pattern, path)` | Regex search | Max 1000 matches |
| `glob` | `tools.glob(pattern, path)` | Find files | Respects .gitignore |
| `todo` | `tools.todo(action, item)` | Manage tasks | In-memory storage |
| `web_search` | `tools.web_search(query)` | Search web | Requires aiohttp |
| `web_fetch` | `tools.web_fetch(url)` | Fetch URL | Requires bs4 |

#### Safety Features

```python
BLOCKED_COMMANDS = [
    "rm -rf /", "rm -rf /*", "format", "mkfs",
    "dd if=/dev/zero", ":(){ :|:& };:",
    "> /dev/sda", "chmod -R 777 /",
    "wget .* | sh", "curl .* | sh"
]

RESTRICTED_PATHS = [
    "/etc/passwd", "/etc/shadow", "~/.ssh",
    "/boot", "/sys", "/proc"
]
```

---

### 5.2 Autonomous Agent (`jarvis_agent.py`)

Proactive tool-using agent with streaming visibility.

**File**: `agent/jarvis_agent.py`

```python
class EventType(Enum):
    THINKING = "thinking"       # Agent reasoning
    TOOL_CALL = "tool_call"     # Calling a tool
    TOOL_RESULT = "tool_result" # Tool returned
    RESPONSE = "response"       # Final/partial response
    ERROR = "error"             # Error occurred
    STATUS = "status"           # Status update
    CANCELLED = "cancelled"     # Task cancelled
    COMPLETE = "complete"       # Task finished

class JarvisAgent:
    async def run(self, message, context) -> AsyncIterator[AgentEvent]:
        """Execute task, streaming events"""

    def cancel_task(self, task_id: str) -> bool:
        """Cancel running task"""
```

#### Agent Loop

```
┌────────────────────────────────────────────────────────┐
│                    AGENT LOOP                          │
├────────────────────────────────────────────────────────┤
│                                                        │
│  1. ANALYZE REQUEST                                    │
│     │                                                  │
│     ▼                                                  │
│  2. DECIDE: Tools needed?                              │
│     │                                                  │
│     ├──[No]──▶ Generate direct response               │
│     │                                                  │
│     └──[Yes]──▶ 3. EXECUTE TOOL                       │
│                    │                                   │
│                    ▼                                   │
│                 4. OBSERVE RESULT                      │
│                    │                                   │
│                    ▼                                   │
│                 5. More tools needed?                  │
│                    │                                   │
│                    ├──[Yes]──▶ Loop back to step 3    │
│                    │                                   │
│                    └──[No]──▶ Generate final response │
│                                                        │
│  All steps emit streaming events for visibility        │
└────────────────────────────────────────────────────────┘
```

#### WebSocket Streaming

```javascript
// Connect to agent WebSocket
const ws = new WebSocket('ws://localhost:8000/api/agent/ws/client123');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
        case 'thinking':    showThinking(data.content);    break;
        case 'tool_call':   showToolCall(data.content);    break;
        case 'tool_result': showToolResult(data.content);  break;
        case 'response':    showResponse(data.content);    break;
    }
};

// Send request
ws.send(JSON.stringify({
    type: 'run',
    message: 'Find all TODO comments in the codebase'
}));

// Cancel if needed
ws.send(JSON.stringify({
    type: 'cancel',
    task_id: 'task-123'
}));
```

**Related Docs**: [WINDOWS_SETUP_GUIDE.md Section 13](docs/WINDOWS_SETUP_GUIDE.md)

---

## 6. Memory System

### 6.1 Session Manager (`memory/session_manager.py`)

Manages per-chat conversation state.

**Key Feature**: Conversation history is **cleared on new chat** to ensure session isolation.

```python
class SessionManager:
    def start_session(self, metadata=None) -> Session:
        # Clear conversation history for new session
        self.conversation_history = []
        # Create new session
        session = Session(id=uuid.uuid4(), ...)
        return session
```

---

### 6.2 User Profile (`memory/user_profile.py`)

Persistent user information across all chats.

```python
class MemoryCategory(Enum):
    PERSONAL = "personal"       # Name, role, background
    PREFERENCES = "preferences" # Communication style
    BUSINESS = "business"       # Company, team, projects
    EXPERTISE = "expertise"     # Skills, knowledge
    INTERACTION = "interaction" # Patterns, history
    CUSTOM = "custom"           # User-defined

class UserProfile:
    user_id: str
    display_name: Optional[str]
    traits: Dict[str, UserTrait]
    preferred_style: CommunicationStyle
    detail_level: float
    formality_level: float

class AdaptiveMemoryManager:
    def store_memory(category, content, importance)
    def recall_memories(query, categories, limit)
    def detect_implicit_trait(message)  # Learns from conversation
    def extract_explicit_memory(message)  # "Remember that I..."
```

**Related Docs**: [JARVIS_2_0_MEMORY_GUIDE.md](docs/JARVIS_2_0_MEMORY_GUIDE.md)

---

### 6.3 Vector Store (`memory/vector_store.py`)

Semantic search using ChromaDB embeddings.

```python
class VectorMemoryStore:
    def store(text, metadata, collection)
    def search(query, n_results, collection)
    def delete(ids, collection)
```

---

## 7. Multi-Agent Orchestrator

### 7.1 Architecture Philosophy

JARVIS serves as the **primary orchestrator** (effectively the "manager"), delegating complex tasks to specialized agents when needed. This simplifies the hierarchy:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     JARVIS AS ORCHESTRATOR                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                           ┌─────────────┐                                   │
│                           │   JARVIS    │                                   │
│                           │  (Manager)  │                                   │
│                           └──────┬──────┘                                   │
│                                  │                                          │
│                    ┌─────────────┼─────────────┐                           │
│                    │             │             │                            │
│                    ▼             ▼             ▼                            │
│             ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│             │Supervisor│  │Supervisor│  │  Direct  │                       │
│             │(Complex) │  │(Quality) │  │Employees │                       │
│             └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
│                  │             │             │                              │
│                  ▼             ▼             ▼                              │
│             ┌─────────────────────────────────────┐                        │
│             │         EMPLOYEE AGENTS             │                        │
│             │  researcher | writer | coder | reviewer                       │
│             └─────────────────────────────────────┘                        │
│                                                                              │
│  For simple tasks: JARVIS → Employee directly                               │
│  For complex tasks: JARVIS → Supervisor → Employee                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Execution Flow

**File**: `agent/orchestrator.py` (~2200 lines)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 1. JARVIS PLANNING (Manager Role)                                    │   │
│  │    • Analyzes the task                                               │   │
│  │    • Creates hierarchical plan                                       │   │
│  │    • Defines acceptance criteria                                     │   │
│  │    • Returns: JSON plan with steps                                   │   │
│  └────────────────────────────────────┬────────────────────────────────┘   │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 2. SUPERVISOR PHASING (Optional for complex tasks)                   │   │
│  │    • Takes JARVIS's plan                                             │   │
│  │    • Breaks into 2-5 phases                                          │   │
│  │    • Assigns categories per phase                                    │   │
│  │    • Returns: List of executable phases                              │   │
│  └────────────────────────────────────┬────────────────────────────────┘   │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 3. EMPLOYEE EXECUTION (Per Phase)                                    │   │
│  │    ┌──────────────────────────────────────────────────────────┐     │   │
│  │    │ Iteration Loop:                                           │     │   │
│  │    │  • Load existing files                                    │     │   │
│  │    │  • Execute phase tasks                                    │     │   │
│  │    │  • Create/modify files                                    │     │   │
│  │    │  • Git commit changes                                     │     │   │
│  │    │                                                           │     │   │
│  │    │ Audit Cycle:                                              │     │   │
│  │    │  • Supervisor reviews work                                │     │   │
│  │    │  • JARVIS validates                                       │     │   │
│  │    │  • If issues: feedback → retry                           │     │   │
│  │    │  • If complete: next phase                               │     │   │
│  │    └──────────────────────────────────────────────────────────┘     │   │
│  └────────────────────────────────────┬────────────────────────────────┘   │
│                                       │                                     │
│                                       ▼                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 4. RESULTS                                                           │   │
│  │    • Files created/modified                                          │   │
│  │    • Cost summary                                                    │   │
│  │    • Rounds completed                                                │   │
│  │    • Success/failure status                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Agent Roles

**File**: `agent/agent_messaging.py`

```python
class AgentRole(Enum):
    MANAGER = "manager"         # JARVIS - Strategic planning & review
    SUPERVISOR = "supervisor"   # Task phasing & decomposition (optional)
    EMPLOYEE = "employee"       # Implementation & execution
    SYSTEM = "system"           # System messages
```

---

### 7.4 Council System & AI Happiness

For advanced multi-agent scenarios, JARVIS includes a **Council System** with gamified mechanics:

| Feature | Description |
|---------|-------------|
| **Councillors** | Named AI agents with personalities and specializations |
| **Voting System** | Democratic decision-making with weighted votes |
| **Happiness System** | Agent satisfaction (0-100) affects performance |
| **Performance Metrics** | Track success rates, response quality |
| **Fire/Spawn Mechanics** | Underperformers replaced, probation periods |

**Vote Weight Formula**:
```
vote_weight = base × performance_coefficient × happiness_modifier × specialization_bonus
```

**Happiness Effects**:
- 80-100: Enthusiastic, bonus vote weight
- 50-79: Normal operation
- 30-49: Demotivated, reduced quality
- 0-29: At risk of being "fired"

**Full Documentation**: [JARVIS_2_0_COUNCIL_GUIDE.md](docs/JARVIS_2_0_COUNCIL_GUIDE.md) - Comprehensive 890-line guide

**Code Location**: `agent/council/`
- `happiness.py` - Happiness management
- `voting.py` - Voting system
- `orchestrator.py` - Council orchestration
- `models.py` - Data models
- `factory.py` - Councillor creation

---

## 8. Configuration System

### 8.1 Agents Configuration (`config/agents.yaml`)

Defines available agents and their capabilities.

**File**: `agent/config/agents.yaml`

```yaml
# Available Tools:
#   read, edit, write, bash, grep, glob, todo, web_search, web_fetch

researcher:
  role: "Senior Research Analyst"
  llm: gpt-4o
  temperature: 0.7
  tools:
    - web_search
    - web_fetch
    - read
    - grep
    - glob
  capabilities:
    - data_analysis
    - trend_identification

writer:
  role: "Expert Content Writer"
  llm: claude-3-5-sonnet
  tools: [read, write, edit]

coder:
  role: "Senior Software Engineer"
  llm: deepseek-chat
  tools: [read, write, edit, bash, grep, glob]

reviewer:
  role: "Quality Assurance Specialist"
  llm: gpt-4o
  tools: [read, bash, grep, glob]
```

---

### 8.2 Tasks Configuration (`config/tasks.yaml`)

Defines task templates and workflows.

**File**: `agent/config/tasks.yaml`

```yaml
# Task Fields:
#   name, description, expected_output, agent, depends_on,
#   priority, output_format, output_file, timeout_seconds,
#   success_criteria, variables

research_task:
  name: "Market Research"
  description: "Research {topic}..."
  agent: researcher
  priority: high
  output_format: markdown
  success_criteria:
    - "Contains 10+ findings"
    - "Includes 5+ sources"

code_implementation:
  name: "Implement Solution"
  agent: coder
  depends_on: [research_task]
  tools_required: [read, write, edit, bash]
```

**Related Docs**: [JARVIS_2_0_CONFIGURATION_GUIDE.md](docs/JARVIS_2_0_CONFIGURATION_GUIDE.md)

---

## 9. API Reference

### 9.1 Chat API (`webapp/chat_api.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/session/start` | POST | Start new chat session |
| `/api/chat/message` | POST | Send message, get response |
| `/api/chat/message/stream` | POST | Stream response (SSE) |
| `/api/chat/history` | GET | Get conversation history |
| `/api/chat/file/attach` | POST | Attach file to conversation |
| `/api/chat/file/upload` | POST | Upload file |
| `/api/chat/file/read` | GET | Read file content |
| `/api/chat/status` | GET | System status |
| `/api/chat/tasks` | GET | Active tasks |

---

### 9.2 Agent API (`webapp/agent_api.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent/ws/{client_id}` | WebSocket | Real-time streaming |
| `/api/agent/run` | POST | Start agent task |
| `/api/agent/cancel` | POST | Cancel running task |
| `/api/agent/tasks` | GET | List active tasks |
| `/api/agent/status` | GET | Agent status |

#### WebSocket Protocol

```json
// Client → Server
{"type": "run", "message": "...", "context": {}}
{"type": "cancel", "task_id": "..."}
{"type": "interrupt", "message": "..."}

// Server → Client
{"type": "thinking", "content": "...", "timestamp": ...}
{"type": "tool_call", "content": {"tool": "read", "args": {...}}}
{"type": "tool_result", "content": {"success": true, "output": "..."}}
{"type": "response", "content": "...", "metadata": {...}}
{"type": "complete", "content": {...}}
```

---

### 9.3 Vision API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vision/chat` | POST | Analyze image with prompt |
| `/api/vision/analyze` | POST | General image analysis |

---

### 9.4 Other APIs

**Code API** (`webapp/code_api.py`): Code operations, execution
**Finance API** (`webapp/finance_api.py`): Financial calculations
**Admin API** (`webapp/admin_api.py`): System administration

**Full API Reference**: [JARVIS_2_0_API_REFERENCE.md](docs/JARVIS_2_0_API_REFERENCE.md)

---

## 10. Web Interface

### 10.1 Main Chat Interface (`templates/jarvis.html`)

**URL**: `http://localhost:8000/jarvis`

**Features**:
- Sidebar: Chat history (localStorage persistence)
- Main area: Message display with avatars
- Input: Text + image upload + camera + voice
- Agents panel: Dashboard of available agents
- Mobile responsive

**Chat History**:
- Stored in browser localStorage
- Per-chat isolation (each chat has unique ID)
- Delete individual chats
- Auto-save on every message

---

### 10.2 Dashboard (`templates/index.html`)

**URL**: `http://localhost:8000/dashboard`

**Features**:
- Job management
- Project browser
- Run history
- System status

---

## 11. Related Documentation

### Core Guides

| Document | Description | Link |
|----------|-------------|------|
| Windows Setup | Installation & configuration | [WINDOWS_SETUP_GUIDE.md](docs/WINDOWS_SETUP_GUIDE.md) |
| Configuration | YAML config deep dive | [JARVIS_2_0_CONFIGURATION_GUIDE.md](docs/JARVIS_2_0_CONFIGURATION_GUIDE.md) |
| Memory System | How memory works | [JARVIS_2_0_MEMORY_GUIDE.md](docs/JARVIS_2_0_MEMORY_GUIDE.md) |
| API Reference | All endpoints | [JARVIS_2_0_API_REFERENCE.md](docs/JARVIS_2_0_API_REFERENCE.md) |
| Pattern Guide | Design patterns | [JARVIS_2_0_PATTERN_GUIDE.md](docs/JARVIS_2_0_PATTERN_GUIDE.md) |

### Feature Guides

| Document | Description | Link |
|----------|-------------|------|
| Conversational Agent | NLP-based routing | [CONVERSATIONAL_AGENT.md](docs/CONVERSATIONAL_AGENT.md) |
| Tool Plugin Guide | Creating custom tools | [TOOL_PLUGIN_GUIDE.md](docs/TOOL_PLUGIN_GUIDE.md) |
| Model Routing | LLM selection | [MODEL_ROUTING.md](docs/MODEL_ROUTING.md) |
| Council Guide | Multi-agent decisions & **AI Happiness System** | [JARVIS_2_0_COUNCIL_GUIDE.md](docs/JARVIS_2_0_COUNCIL_GUIDE.md) |

### Advanced Topics

| Document | Description | Link |
|----------|-------------|------|
| Security | Prompt injection defense | [SECURITY_PROMPT_INJECTION.md](docs/SECURITY_PROMPT_INJECTION.md) |
| Threading | Concurrency patterns | [THREADING_AND_CONCURRENCY.md](docs/THREADING_AND_CONCURRENCY.md) |
| Migration | 1.x to 2.x upgrade | [MIGRATION_GUIDE_1x_to_2x.md](docs/MIGRATION_GUIDE_1x_to_2x.md) |
| Enterprise | Future roadmap | [ENTERPRISE_ROADMAP.md](docs/ENTERPRISE_ROADMAP.md) |

---

## Document Cross-Reference Map

```
JARVIS_ARCHITECTURE.md (This File)
        │
        ├── Setup & Installation
        │   └── docs/WINDOWS_SETUP_GUIDE.md
        │       ├── Section 12: Tools System
        │       └── Section 13: Agent Streaming
        │
        ├── Configuration
        │   ├── docs/JARVIS_2_0_CONFIGURATION_GUIDE.md
        │   ├── agent/config/agents.yaml
        │   └── agent/config/tasks.yaml
        │
        ├── Memory System
        │   ├── docs/JARVIS_2_0_MEMORY_GUIDE.md
        │   └── agent/memory/*.py
        │
        ├── API Endpoints
        │   ├── docs/JARVIS_2_0_API_REFERENCE.md
        │   └── agent/webapp/*_api.py
        │
        ├── Core Components
        │   ├── agent/jarvis_chat.py      (Intent Router)
        │   ├── agent/jarvis_tools.py     (Tools System)
        │   ├── agent/jarvis_agent.py     (Autonomous Agent)
        │   ├── agent/jarvis_persona.py   (Personality)
        │   ├── agent/jarvis_vision.py    (Vision)
        │   └── agent/jarvis_voice.py     (Voice)
        │
        ├── Multi-Agent System
        │   ├── agent/orchestrator.py
        │   └── agent/agent_messaging.py
        │
        └── Council System & AI Happiness
            ├── docs/JARVIS_2_0_COUNCIL_GUIDE.md (Full Guide)
            └── agent/council/
                ├── happiness.py
                ├── voting.py
                ├── orchestrator.py
                ├── models.py
                └── factory.py
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1.0 | 2024-11-24 | Added Claude Code-like tools, autonomous agent, session isolation |
| 2.0.0 | 2024-10 | Memory system, adaptive profiles, YAML config |
| 1.2.0 | 2024-09 | Multi-agent orchestrator, 3-loop pattern |
| 1.0.0 | 2024-08 | Initial release |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key  # Optional

# 3. Start the server
python start_webapp.py

# 4. Open browser
# http://localhost:8000/jarvis
```

---

*For the most up-to-date information, always refer to the individual documentation files in the `docs/` directory.*
