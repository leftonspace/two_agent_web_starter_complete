"""
Command-line chat interface for conversational agent.

PHASE 7.1: Provides interactive CLI for chatting with the System-1.2 agent.

Usage:
    python -m agent.cli_chat

Commands:
    /status - Show active tasks
    /task <id> - Show task details
    /clear - Clear conversation
    /help - Show help
    /exit - Exit chat
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from conversational_agent import ConversationalAgent
from config import Config


class CLIChat:
    """Command-line chat interface"""

    def __init__(self):
        self.agent: Optional[ConversationalAgent] = None
        self.running = False

    async def start(self):
        """Start chat session"""
        print("\nInitializing conversational agent...")
        self.agent = ConversationalAgent()
        self.running = True

        self._print_welcome()

        while self.running:
            try:
                user_input = await self._get_input()

                if not user_input.strip():
                    continue

                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                    continue

                print("\nAgent: ", end="", flush=True)
                response = await self.agent.chat(user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}\n")

    async def _get_input(self) -> str:
        """Get user input (async)"""
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, input, "\nYou: ")
        except EOFError:
            raise KeyboardInterrupt

    async def _handle_command(self, command: str):
        """Handle special commands"""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit", "/q"]:
            print("\nGoodbye!")
            self.running = False

        elif cmd == "/status":
            tasks = self.agent.get_active_tasks()
            if not tasks:
                print("\nNo active tasks.\n")
            else:
                print("\nActive Tasks:")
                for task in tasks:
                    print(f"  [{task['task_id']}] {task['description']}")
                    print(f"    Status: {task['status']} ({task['progress']})")
                print()

        elif cmd == "/task":
            if len(parts) < 2:
                print("\nUsage: /task <task_id>\n")
                return

            task_id = parts[1]
            status = self.agent.get_task_status(task_id)

            if not status:
                print(f"\nTask {task_id} not found.\n")
            else:
                print(f"\nTask: {status['description']}")
                print(f"Status: {status['status']}")
                print(f"Progress: {status['current_step']}/{status['total_steps']}")
                print(f"Started: {status['started_at']}")
                if status['completed_at']:
                    print(f"Completed: {status['completed_at']}")
                if status['error']:
                    print(f"Error: {status['error']}")
                if status['result']:
                    print(f"Result: {status['result']}")
                print()

        elif cmd == "/clear":
            self.agent.clear_conversation()
            print("\nConversation cleared.\n")

        elif cmd == "/help":
            self._print_help()

        elif cmd == "/history":
            self._print_history()

        else:
            print(f"\nUnknown command: {cmd}")
            print("Type /help for available commands.\n")

    def _print_welcome(self):
        """Print welcome message"""
        print("\n" + "=" * 60)
        print("  System-1.2 Conversational Agent")
        print("=" * 60)
        print("\nChat with me naturally! I can:")
        print("  • Execute tasks (format code, run tests, git operations)")
        print("  • Build complex systems")
        print("  • Answer questions")
        print("  • Automate workflows")
        print("\nCommands: /status /task /clear /history /help /exit")
        print("=" * 60)

    def _print_help(self):
        """Print help message"""
        print("\nAvailable Commands:")
        print("  /status          - Show active tasks")
        print("  /task <id>       - Show detailed task status")
        print("  /clear           - Clear conversation history")
        print("  /history         - Show conversation history")
        print("  /help            - Show this help")
        print("  /exit, /quit, /q - Exit chat")
        print("\nExamples:")
        print("  'Format the code in src/'")
        print("  'Run the test suite'")
        print("  'What tools are available?'")
        print("  'Create a simple website'")
        print()

    def _print_history(self):
        """Print conversation history"""
        if not self.agent.conversation_history:
            print("\nNo conversation history.\n")
            return

        print("\nConversation History:")
        print("-" * 60)
        for msg in self.agent.conversation_history:
            timestamp = msg.timestamp.strftime("%H:%M:%S")
            role = msg.role.upper()
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            print(f"[{timestamp}] {role}: {content}")
        print("-" * 60)
        print()


async def main():
    """Main entry point"""
    cli = CLIChat()
    await cli.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
