"""
JARVIS Agent - Autonomous Tool-Using Agent

An agent that proactively uses tools to answer questions and complete tasks,
similar to Claude Code. Features:
- Proactive tool usage (read files, search code, run commands)
- Streaming thoughts and actions in real-time
- Task cancellation and user interrupts
- Visible reasoning process
"""

import asyncio
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

# Import tools
try:
    from jarvis_tools import JarvisTools, ToolType, ToolResult, get_jarvis_tools
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    JarvisTools = None

# Import LLM
import importlib.util
from pathlib import Path

llm_chat = None
try:
    llm_file = Path(__file__).parent / "llm.py"
    if llm_file.exists():
        spec = importlib.util.spec_from_file_location("llm_module", llm_file)
        llm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(llm_module)
        llm_chat = llm_module.chat
except Exception as e:
    print(f"[JarvisAgent] LLM import failed: {e}")


class EventType(Enum):
    """Types of events emitted by the agent"""
    THINKING = "thinking"           # Agent is reasoning
    TOOL_CALL = "tool_call"         # Agent is calling a tool
    TOOL_RESULT = "tool_result"     # Tool returned a result
    RESPONSE = "response"           # Final or partial response
    ERROR = "error"                 # An error occurred
    STATUS = "status"               # Status update
    CANCELLED = "cancelled"         # Task was cancelled
    COMPLETE = "complete"           # Task completed


@dataclass
class AgentEvent:
    """An event emitted by the agent"""
    type: EventType
    content: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class AgentTask:
    """A task being executed by the agent"""
    id: str
    message: str
    context: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, cancelled, error
    created_at: float = field(default_factory=time.time)
    events: List[AgentEvent] = field(default_factory=list)
    result: Optional[str] = None
    cancel_requested: bool = False


class JarvisAgent:
    """
    Autonomous agent that uses tools proactively.

    The agent follows a loop:
    1. Analyze the request
    2. Decide if tools are needed
    3. Execute tools and observe results
    4. Continue or respond

    All steps are streamed as events for visibility.
    """

    def __init__(self, tools: Optional[JarvisTools] = None):
        """Initialize the agent"""
        self.tools = tools or (get_jarvis_tools() if TOOLS_AVAILABLE else None)
        self.active_tasks: Dict[str, AgentTask] = {}
        self.max_iterations = 10  # Prevent infinite loops
        self.event_listeners: List[Callable[[AgentEvent], None]] = []

        # System prompt that encourages tool usage
        self.system_prompt = """You are JARVIS, an intelligent AI assistant with access to powerful tools.

IMPORTANT: You should PROACTIVELY use your tools to gather information and complete tasks.
Do NOT just respond from memory when you can use tools to get accurate, current information.

## Available Tools

You have access to these tools (use them by including <tool>...</tool> tags in your response):

1. **read** - Read files from disk
   <tool name="read">{"path": "path/to/file.py"}</tool>
   <tool name="read">{"path": "config.json", "line_start": 10, "line_end": 20}</tool>

2. **edit** - Make targeted string replacements
   <tool name="edit">{"path": "file.py", "old": "old_text", "new": "new_text"}</tool>

3. **write** - Create or overwrite files
   <tool name="write">{"path": "new_file.py", "content": "file content here"}</tool>

4. **bash** - Execute shell commands
   <tool name="bash">{"command": "git status"}</tool>
   <tool name="bash">{"command": "npm test", "timeout": 120}</tool>

5. **grep** - Search for patterns in code
   <tool name="grep">{"pattern": "TODO", "file_pattern": "*.py"}</tool>

6. **glob** - Find files by pattern
   <tool name="glob">{"pattern": "**/*.js"}</tool>

7. **web_search** - Search the web
   <tool name="web_search">{"query": "Python async best practices"}</tool>

8. **web_fetch** - Fetch a webpage
   <tool name="web_fetch">{"url": "https://docs.python.org/3/library/asyncio.html"}</tool>

## When to Use Tools

- **Questions about code**: READ the files first, don't guess
- **Finding something**: Use GREP or GLOB to search
- **Running commands**: Use BASH for git, npm, pip, etc.
- **Making changes**: READ first, then EDIT
- **Need current info**: Use WEB_SEARCH or WEB_FETCH

## Response Format

Think through your approach, then use tools as needed:

<thinking>
I need to understand what's in config.py before I can help with this.
Let me read the file first.
</thinking>

<tool name="read">{"path": "config.py"}</tool>

After receiving tool results, continue reasoning and either use more tools or provide your response.

## Important Rules

1. Always READ files before suggesting changes
2. Use GREP to find code patterns instead of guessing locations
3. Show your reasoning in <thinking> blocks
4. Be thorough - use multiple tools if needed
5. If a task fails, explain why and suggest alternatives

Remember: You're not just an AI that answers questions - you're an agent that DOES things.
Use your tools proactively to provide accurate, helpful responses.
"""

    def add_event_listener(self, callback: Callable[[AgentEvent], None]):
        """Add a listener for agent events"""
        self.event_listeners.append(callback)

    def remove_event_listener(self, callback: Callable[[AgentEvent], None]):
        """Remove an event listener"""
        if callback in self.event_listeners:
            self.event_listeners.remove(callback)

    def _emit_event(self, event: AgentEvent):
        """Emit an event to all listeners"""
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"[JarvisAgent] Event listener error: {e}")

    async def run(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncIterator[AgentEvent]:
        """
        Run the agent on a message, yielding events as they occur.

        This is the main entry point for the agent. It:
        1. Creates a task
        2. Runs the agent loop
        3. Yields events for each step
        4. Returns the final response

        Args:
            message: User's message
            context: Optional context (attached files, etc.)
            conversation_history: Previous conversation messages

        Yields:
            AgentEvent objects for each step
        """
        # Create task
        task_id = str(uuid.uuid4())[:8]
        task = AgentTask(
            id=task_id,
            message=message,
            context=context or {}
        )
        self.active_tasks[task_id] = task
        task.status = "running"

        try:
            yield AgentEvent(
                type=EventType.STATUS,
                content=f"Starting task {task_id}",
                metadata={"task_id": task_id, "message": message}
            )

            # Build initial prompt
            prompt = self._build_prompt(message, context, conversation_history)

            # Agent loop
            iteration = 0
            accumulated_response = ""

            while iteration < self.max_iterations:
                iteration += 1

                # Check for cancellation
                if task.cancel_requested:
                    yield AgentEvent(
                        type=EventType.CANCELLED,
                        content="Task cancelled by user",
                        metadata={"task_id": task_id, "iteration": iteration}
                    )
                    task.status = "cancelled"
                    return

                yield AgentEvent(
                    type=EventType.STATUS,
                    content=f"Iteration {iteration}/{self.max_iterations}",
                    metadata={"iteration": iteration}
                )

                # Get LLM response
                if not llm_chat:
                    yield AgentEvent(
                        type=EventType.ERROR,
                        content="LLM not available",
                        metadata={"task_id": task_id}
                    )
                    task.status = "error"
                    return

                try:
                    llm_response = await asyncio.to_thread(
                        llm_chat,
                        role="employee",
                        system_prompt=self.system_prompt,
                        user_content=prompt,
                        temperature=0.7
                    )
                except Exception as e:
                    yield AgentEvent(
                        type=EventType.ERROR,
                        content=f"LLM error: {str(e)}",
                        metadata={"task_id": task_id}
                    )
                    task.status = "error"
                    return

                # Parse response for thinking and tool calls
                thinking_blocks = self._extract_thinking(llm_response)
                tool_calls = self._extract_tool_calls(llm_response)

                # Emit thinking events
                for thinking in thinking_blocks:
                    yield AgentEvent(
                        type=EventType.THINKING,
                        content=thinking,
                        metadata={"iteration": iteration}
                    )

                # Execute tool calls
                tool_results = []
                for tool_call in tool_calls:
                    # Emit tool call event
                    yield AgentEvent(
                        type=EventType.TOOL_CALL,
                        content=f"Calling {tool_call['name']}",
                        metadata={
                            "tool": tool_call["name"],
                            "args": tool_call["args"],
                            "iteration": iteration
                        }
                    )

                    # Execute tool
                    result = await self._execute_tool(tool_call["name"], tool_call["args"])

                    # Emit result event
                    yield AgentEvent(
                        type=EventType.TOOL_RESULT,
                        content=result.output if result.success else result.error,
                        metadata={
                            "tool": tool_call["name"],
                            "success": result.success,
                            "execution_time": result.execution_time
                        }
                    )

                    tool_results.append({
                        "tool": tool_call["name"],
                        "args": tool_call["args"],
                        "result": result.output if result.success else f"Error: {result.error}",
                        "success": result.success
                    })

                # If there were tool calls, continue the loop with results
                if tool_calls:
                    # Add tool results to prompt for next iteration
                    results_text = "\n\n## Tool Results\n\n"
                    for tr in tool_results:
                        results_text += f"### {tr['tool']}\n"
                        results_text += f"**Args:** {json.dumps(tr['args'])}\n"
                        results_text += f"**Result:**\n```\n{tr['result'][:3000]}\n```\n\n"

                    prompt = f"""{prompt}

## Previous Response (iteration {iteration})
{llm_response}

{results_text}

Continue your analysis based on the tool results above.
If you have enough information, provide your final response.
If you need more information, use more tools.
Do NOT repeat tool calls you've already made."""
                else:
                    # No tool calls - this is the final response
                    # Clean up the response (remove tool tags if any slipped through)
                    final_response = self._clean_response(llm_response)
                    accumulated_response = final_response

                    yield AgentEvent(
                        type=EventType.RESPONSE,
                        content=final_response,
                        metadata={"task_id": task_id, "iterations": iteration}
                    )
                    break

            # Mark task complete
            task.status = "completed"
            task.result = accumulated_response

            yield AgentEvent(
                type=EventType.COMPLETE,
                content="Task completed",
                metadata={
                    "task_id": task_id,
                    "iterations": iteration,
                    "response_length": len(accumulated_response)
                }
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield AgentEvent(
                type=EventType.ERROR,
                content=str(e),
                metadata={"task_id": task_id}
            )
            task.status = "error"

        finally:
            # Clean up
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    def cancel_task(self, task_id: str) -> bool:
        """Request cancellation of a running task"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel_requested = True
            return True
        return False

    def get_active_tasks(self) -> List[Dict]:
        """Get list of active tasks"""
        return [
            {
                "id": task.id,
                "message": task.message[:100],
                "status": task.status,
                "created_at": task.created_at
            }
            for task in self.active_tasks.values()
        ]

    def _build_prompt(
        self,
        message: str,
        context: Optional[Dict],
        history: Optional[List[Dict]]
    ) -> str:
        """Build the prompt for the LLM"""
        prompt_parts = []

        # Add conversation history
        if history:
            prompt_parts.append("## Conversation History\n")
            for msg in history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")[:500]
                prompt_parts.append(f"**{role}:** {content}\n")
            prompt_parts.append("\n")

        # Add context
        if context:
            if context.get("attached_files"):
                prompt_parts.append("## Attached Files\n")
                for file_info in context["attached_files"]:
                    name = file_info.get("name", "unknown")
                    content = file_info.get("content", "")[:5000]
                    prompt_parts.append(f"### {name}\n```\n{content}\n```\n")
                prompt_parts.append("\n")

            if context.get("working_directory"):
                prompt_parts.append(f"**Working Directory:** {context['working_directory']}\n\n")

        # Add current message
        prompt_parts.append(f"## User Request\n\n{message}\n\n")
        prompt_parts.append("## Your Response\n\nAnalyze the request and use tools as needed. Show your thinking process.")

        return "".join(prompt_parts)

    def _extract_thinking(self, response: str) -> List[str]:
        """Extract thinking blocks from response"""
        pattern = r'<thinking>(.*?)</thinking>'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        return [m.strip() for m in matches]

    def _extract_tool_calls(self, response: str) -> List[Dict]:
        """Extract tool calls from response"""
        tool_calls = []
        pattern = r'<tool\s+name="(\w+)">(.*?)</tool>'
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)

        for name, args_str in matches:
            try:
                args = json.loads(args_str.strip())
                tool_calls.append({"name": name, "args": args})
            except json.JSONDecodeError:
                # Try to parse as simple key-value
                print(f"[JarvisAgent] Failed to parse tool args: {args_str}")
                continue

        return tool_calls

    def _clean_response(self, response: str) -> str:
        """Clean up the response by removing tool tags and thinking blocks"""
        # Remove thinking blocks
        response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL | re.IGNORECASE)
        # Remove tool calls
        response = re.sub(r'<tool\s+name="\w+".*?>.*?</tool>', '', response, flags=re.DOTALL | re.IGNORECASE)
        # Clean up extra whitespace
        response = re.sub(r'\n{3,}', '\n\n', response)
        return response.strip()

    async def _execute_tool(self, tool_name: str, args: Dict) -> ToolResult:
        """Execute a tool and return the result"""
        if not self.tools:
            return ToolResult(
                success=False,
                tool=ToolType.READ,
                output=None,
                error="Tools not available"
            )

        try:
            if tool_name == "read":
                return await self.tools.read(
                    args.get("path", ""),
                    line_start=args.get("line_start"),
                    line_end=args.get("line_end")
                )

            elif tool_name == "edit":
                return await self.tools.edit(
                    args.get("path", ""),
                    args.get("old", ""),
                    args.get("new", ""),
                    replace_all=args.get("replace_all", False)
                )

            elif tool_name == "write":
                return await self.tools.write(
                    args.get("path", ""),
                    args.get("content", "")
                )

            elif tool_name == "bash":
                return await self.tools.bash(
                    args.get("command", ""),
                    timeout=args.get("timeout", 60)
                )

            elif tool_name == "grep":
                return await self.tools.grep(
                    args.get("pattern", ""),
                    path=args.get("path"),
                    file_pattern=args.get("file_pattern", "*"),
                    case_insensitive=args.get("case_insensitive", False)
                )

            elif tool_name == "glob":
                return await self.tools.glob(
                    args.get("pattern", ""),
                    path=args.get("path")
                )

            elif tool_name == "web_search":
                return await self.tools.web_search(
                    args.get("query", "")
                )

            elif tool_name == "web_fetch":
                return await self.tools.web_fetch(
                    args.get("url", "")
                )

            else:
                return ToolResult(
                    success=False,
                    tool=ToolType.READ,
                    output=None,
                    error=f"Unknown tool: {tool_name}"
                )

        except Exception as e:
            return ToolResult(
                success=False,
                tool=ToolType.READ,
                output=None,
                error=str(e)
            )


# Convenience function for quick agent usage
async def run_agent(
    message: str,
    context: Optional[Dict] = None,
    on_event: Optional[Callable[[AgentEvent], None]] = None
) -> str:
    """
    Run the agent and return the final response.

    Args:
        message: User's message
        context: Optional context
        on_event: Optional callback for events

    Returns:
        The agent's final response
    """
    agent = JarvisAgent()
    final_response = ""

    async for event in agent.run(message, context):
        if on_event:
            on_event(event)

        if event.type == EventType.RESPONSE:
            final_response = event.content
        elif event.type == EventType.ERROR:
            final_response = f"Error: {event.content}"

    return final_response


# Global agent instance
_agent_instance: Optional[JarvisAgent] = None


def get_agent() -> JarvisAgent:
    """Get or create the global agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = JarvisAgent()
    return _agent_instance
