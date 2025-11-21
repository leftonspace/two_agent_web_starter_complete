# Conversational Agent

**PHASE 7.1** - Natural Language Interface for System-1.2

## Overview

The Conversational Agent provides a natural language interface to System-1.2, allowing users to interact with the multi-agent orchestration platform through chat instead of writing mission files or using CLI commands.

### Key Features

- **Natural Language Understanding**: Chat naturally - the agent parses intent and figures out what you need
- **Multi-Step Task Execution**: Handles both simple actions (format code, run tests) and complex tasks (build websites, create systems)
- **Background Processing**: Long-running tasks execute asynchronously while you continue chatting
- **Multiple Interfaces**: Available via web dashboard (`/chat`) and CLI (`python -m agent.cli_chat`)
- **Conversation Context**: Maintains conversation history for contextual understanding
- **Task Tracking**: Monitor active tasks and their progress in real-time

## Architecture

```
User Input → Intent Parser → Task Planner → Executor → Response
                ↓                 ↓            ↓
            LLM Analysis    Multi-Step    Tool Registry
                            Planning
```

### Intent Types

The agent classifies user messages into five intent types:

1. **Simple Action**: Single tool call (e.g., "format the code", "run tests")
2. **Complex Task**: Multi-step tasks (e.g., "create a website", "build an API")
3. **Question**: Information requests (e.g., "what tools are available?")
4. **Clarification**: Requests needing more information
5. **Conversation**: Casual chat, greetings, farewells

## Usage

### Web Interface

1. Start the web dashboard:
   ```bash
   python -m agent.webapp.app
   ```

2. Navigate to `http://127.0.0.1:8000/chat`

3. Chat naturally with the agent:
   ```
   You: Format the code in src/
   Agent: ✓ Executed format_code successfully: 15 files formatted

   You: What tools do I have available?
   Agent: You have access to: format_code, run_tests, git_diff, git_status...

   You: Create a portfolio website
   Agent: I understand! I'll create a portfolio website.

   Plan:
   Summary: Create portfolio website
   1. Create project directory (5s)
   2. Generate HTML structure (60s)
   3. Add CSS styling (45s)
   4. Create JavaScript interactivity (30s)

   Estimated time: 2 minutes
   Task ID: task_a1b2c3d4
   ```

### CLI Interface

Run the interactive CLI chat:

```bash
python -m agent.cli_chat
```

**Commands:**
- `/status` - Show active tasks
- `/task <id>` - Show detailed task status
- `/clear` - Clear conversation history
- `/history` - Show conversation history
- `/help` - Show help
- `/exit`, `/quit`, `/q` - Exit chat

**Example Session:**

```
You: Hello!

Agent: Hello! I'm the System-1.2 conversational agent. I can help you:
- Execute tasks (format code, run tests, git operations)
- Build complex systems
- Answer questions about the platform
- Automate workflows

What would you like to do?

You: Run the test suite

Agent: ✓ Executed run_tests successfully:
======================== test session starts =========================
collected 47 items

tests/test_agent.py ......................................... [ 87%]
tests/test_tools.py ......                                   [100%]

======================== 47 passed in 2.31s ==========================

You: /exit

Goodbye!
```

### Python API

Use the agent programmatically:

```python
import asyncio
from agent.conversational_agent import ConversationalAgent

async def main():
    # Initialize agent
    agent = ConversationalAgent()

    # Chat with agent
    response = await agent.chat("Format code in ./src")
    print(response)

    # Check active tasks
    tasks = agent.get_active_tasks()
    for task in tasks:
        print(f"Task: {task['description']}")
        print(f"Status: {task['status']} ({task['progress']})")

    # Get specific task status
    task_status = agent.get_task_status("task_abc123")
    if task_status:
        print(f"Progress: {task_status['current_step']}/{task_status['total_steps']}")

asyncio.run(main())
```

## Configuration

Configure the conversational agent in `agent/project_config.json`:

```json
{
  "conversational": {
    "enabled": true,
    "default_model": "gpt-4o",
    "intent_model": "gpt-4o",
    "planning_model": "gpt-4o",
    "max_history_messages": 50,
    "context_window_messages": 10,
    "temperature": 0.7,
    "max_concurrent_tasks": 3,
    "task_timeout_seconds": 3600,
    "enable_background_execution": true,
    "require_approval_for_destructive": true,
    "allowed_tools": null,
    "denied_tools": [],
    "enable_web_chat": true,
    "enable_cli_chat": true
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `true` | Enable conversational agent |
| `default_model` | str | `"gpt-4o"` | Default LLM for chat |
| `intent_model` | str | `"gpt-4o"` | Model for intent classification |
| `planning_model` | str | `"gpt-4o"` | Model for task planning |
| `max_history_messages` | int | `50` | Maximum conversation history size |
| `context_window_messages` | int | `10` | Messages to include in LLM prompts |
| `temperature` | float | `0.7` | Temperature for conversational responses |
| `max_concurrent_tasks` | int | `3` | Maximum simultaneous tasks |
| `task_timeout_seconds` | int | `3600` | Default task timeout (1 hour) |
| `enable_background_execution` | bool | `true` | Allow async task execution |
| `require_approval_for_destructive` | bool | `true` | Require approval for destructive ops |
| `allowed_tools` | list\|null | `null` | Whitelist of tools (null = all) |
| `denied_tools` | list | `[]` | Blacklist of tools |
| `enable_web_chat` | bool | `true` | Enable web chat at `/chat` |
| `enable_cli_chat` | bool | `true` | Enable CLI chat interface |

## API Endpoints

### Web Chat Endpoints

#### `GET /chat`
Serves the web chat interface.

**Response:** HTML page

---

#### `POST /api/chat`
Main chat endpoint for message processing.

**Request:**
```json
{
  "message": "your message here"
}
```

**Response:**
```json
{
  "response": "agent response text",
  "active_tasks": [
    {
      "task_id": "task_abc123",
      "description": "Build website",
      "status": "executing",
      "progress": "2/4"
    }
  ]
}
```

---

#### `GET /api/chat/tasks`
Get list of all active tasks.

**Response:**
```json
{
  "tasks": [
    {
      "task_id": "task_abc123",
      "description": "Build website",
      "status": "executing",
      "progress": "2/4"
    }
  ]
}
```

---

#### `GET /api/chat/task/{task_id}`
Get detailed status of a specific task.

**Response:**
```json
{
  "task_id": "task_abc123",
  "description": "Build website",
  "status": "executing",
  "current_step": 2,
  "total_steps": 4,
  "started_at": "2025-01-15T10:30:00",
  "completed_at": null,
  "result": null,
  "error": null
}
```

## Examples

### Simple Actions

**Format Code:**
```
You: Format the Python files in src/
Agent: ✓ Executed format_code successfully: 15 files formatted
```

**Run Tests:**
```
You: Run the test suite
Agent: ✓ Executed run_tests successfully: 47 tests passed
```

**Git Operations:**
```
You: Show me the git diff
Agent: ✓ Executed git_diff successfully:
diff --git a/src/main.py b/src/main.py
...
```

### Complex Tasks

**Create Website:**
```
You: Create a simple portfolio website

Agent: I understand! I'll create a simple portfolio website.

Plan:
Summary: Create portfolio website
1. Create project directory (5s)
2. Generate HTML structure with header, about, projects sections (60s)
3. Add responsive CSS styling (45s)
4. Create JavaScript for smooth scrolling (30s)
5. Generate sample content (30s)

Estimated time: 2 minutes

Task ID: task_a1b2c3d4
I'll work on this and update you.
```

**Build API:**
```
You: Build a REST API for user management

Agent: I'll build a REST API for user management.

Plan:
Summary: Build REST API for user management
1. Set up Flask project structure (10s)
2. Create user model and database schema (30s)
3. Implement CRUD endpoints (GET, POST, PUT, DELETE) (120s)
4. Add authentication middleware (60s)
5. Write API documentation (40s)
6. Create unit tests (80s)

Estimated time: 5 minutes

Task ID: task_b2c3d4e5
```

### Questions

**Available Tools:**
```
You: What tools can I use?

Agent: System-1.2 provides these tools:
- format_code: Format source code with ruff/black
- run_tests: Run pytest test suite
- git_diff: Show git diff
- git_status: Show git status
- And more...
```

**System Capabilities:**
```
You: What can System-1.2 do?

Agent: System-1.2 is a multi-agent orchestration platform that can:
- Execute automated workflows
- Coordinate multiple AI agents (manager, supervisor, employee)
- Run code formatting, testing, and quality checks
- Manage git operations
- Build complex systems through conversational interface
- Track costs and provide analytics
```

## Task Management

### Tracking Tasks

When complex tasks are created, they run in the background. Track them with:

**Web Interface:**
- Active tasks appear in the sidebar
- Click task ID for details
- Real-time progress updates

**CLI Interface:**
```
You: /status

Active Tasks:
  [task_a1b2c3d4] Create portfolio website
    Status: executing (2/5)

You: /task task_a1b2c3d4

Task: Create portfolio website
Status: executing
Progress: 2/5
Started: 2025-01-15T10:30:00
```

**Python API:**
```python
# Get all active tasks
tasks = agent.get_active_tasks()

# Get specific task
status = agent.get_task_status("task_a1b2c3d4")
print(f"Progress: {status['current_step']}/{status['total_steps']}")
```

## Troubleshooting

### Agent Not Responding

**Problem:** Chat returns "Conversational agent not initialized"

**Solution:**
- Restart the web server
- Check that startup logs show "Conversational agent initialized"
- Verify config has `conversational.enabled: true`

### Intent Parsing Errors

**Problem:** Agent misunderstands requests

**Solution:**
- Be more specific in your request
- Include relevant context (file paths, parameters)
- Use conversation history (agent remembers context)
- Try rephrasing the request

### Tool Execution Failures

**Problem:** "Failed to execute {tool_name}"

**Solution:**
- Check that required parameters are provided
- Verify file paths exist
- Ensure tool is not in `denied_tools` list
- Check tool execution logs for details

### Task Timeout

**Problem:** Long-running tasks fail with timeout

**Solution:**
- Increase `task_timeout_seconds` in config
- Break large tasks into smaller steps
- Check system resources (CPU, memory)

### API Key / Authentication Issues

**Problem:** LLM calls fail with authentication errors

**Solution:**
- Set `OPENAI_API_KEY` environment variable
- Verify API key is valid and has credits
- Check network connectivity

## Performance Tips

1. **Intent Parsing**: Uses ~100-200 tokens per message (< 3 seconds)
2. **Simple Actions**: Execute in < 10 seconds
3. **Complex Tasks**: Background execution, immediate response
4. **Conversation History**: Limited to 50 messages (configurable)
5. **Concurrent Tasks**: Max 3 simultaneous (configurable)

## Security Considerations

- **Tool Whitelisting**: Use `allowed_tools` to restrict available tools
- **Tool Blacklisting**: Use `denied_tools` to block specific tools
- **Approval Required**: Set `require_approval_for_destructive: true` for safety
- **Conversation Privacy**: History stored in-memory only (not persisted)
- **Authentication**: Web interface inherits dashboard authentication

## Testing

Run the test suite:

```bash
# All tests
pytest agent/tests/test_conversational_agent.py -v

# Specific test class
pytest agent/tests/test_conversational_agent.py::TestIntentParsing -v

# With coverage
pytest agent/tests/test_conversational_agent.py --cov=conversational_agent
```

## Architecture Details

### Intent Classification Flow

```
User Message
    ↓
Build Context (last N messages)
    ↓
LLM Prompt (user message + context + available tools)
    ↓
LLM Response (JSON with intent type, confidence, tool suggestion)
    ↓
Intent Object (parsed and validated)
    ↓
Route to Handler (simple_action, complex_task, question, etc.)
```

### Task Execution Flow

```
Complex Task Identified
    ↓
Create TaskExecution Object
    ↓
Generate Execution Plan (LLM breaks into steps)
    ↓
Start Background Async Task
    ↓
Return Immediate Response to User
    ↓
Execute Steps (iterate, log progress)
    ↓
Update Task Status (completed/failed)
```

### Conversation Context

The agent maintains context by:
1. Storing all messages in `conversation_history`
2. Including last N messages in LLM prompts
3. Using conversation context for parameter extraction
4. Maintaining session state across messages

## Limitations

- **No Persistent Storage**: Conversation history cleared on restart
- **No Multi-User Sessions**: Single global agent instance (web)
- **No Streaming**: Responses returned after full LLM completion
- **Simulated Tool Execution**: Currently mocked (integration pending)
- **No Interruption**: Running tasks can't be cancelled mid-execution

## Future Enhancements

Planned improvements (future phases):

- **Persistent Conversations**: Save/load conversation history
- **Multi-User Support**: Per-user agent instances with auth
- **Streaming Responses**: Real-time token streaming
- **Tool Integration**: Full integration with exec_tools.py
- **Task Cancellation**: Ability to stop running tasks
- **Conversation Search**: Search through chat history
- **Voice Interface**: Speech-to-text integration
- **Suggested Actions**: Proactive task suggestions

## Support

For issues or questions:

1. Check this documentation
2. Review test cases in `agent/tests/test_conversational_agent.py`
3. Check logs in `agent/run_logs_main/`
4. Open issue on GitHub

## Related Documentation

- [Main README](../README.md) - System overview
- [Orchestrator Guide](./ORCHESTRATOR.md) - Multi-agent execution
- [Tool Registry](./TOOLS.md) - Available tools
- [Web Dashboard](./DASHBOARD.md) - Web interface guide
