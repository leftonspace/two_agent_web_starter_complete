#!/usr/bin/env python3
"""
JARVIS CLI - Command-line interface for JARVIS AI Assistant.

Features:
- Chat with JARVIS
- Analyze code files
- Generate commit messages from git diff
- Review code and PRs
- Pipe input support for integration with other tools

Usage:
    jarvis chat "How do I implement a binary search?"
    jarvis analyze file.py
    jarvis commit-msg
    jarvis review file.py
    cat file.py | jarvis analyze --stdin
    git diff | jarvis commit-msg --stdin
"""

import argparse
import sys
import os
import json
import requests
from pathlib import Path
from typing import Optional

# Default server URL
DEFAULT_SERVER = os.environ.get("JARVIS_SERVER", "http://localhost:8000")

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def colored(text: str, color: str) -> str:
    """Apply color to text if terminal supports it."""
    if sys.stdout.isatty():
        return f"{color}{text}{Colors.END}"
    return text

def print_error(message: str):
    """Print error message in red."""
    print(colored(f"Error: {message}", Colors.RED), file=sys.stderr)

def print_success(message: str):
    """Print success message in green."""
    print(colored(message, Colors.GREEN))

def print_header(message: str):
    """Print header in bold cyan."""
    print(colored(f"\n{message}", Colors.BOLD + Colors.CYAN))
    print(colored("=" * len(message), Colors.CYAN))

def get_language_from_file(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.cs': 'csharp',
        '.vue': 'vue',
        '.sql': 'sql',
        '.sh': 'bash',
        '.bash': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.md': 'markdown',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
    }
    ext = Path(file_path).suffix.lower()
    return ext_map.get(ext, 'unknown')


def api_request(endpoint: str, data: dict, server: str = DEFAULT_SERVER) -> dict:
    """Make API request to JARVIS server."""
    url = f"{server}{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to JARVIS server at {server}")
        print("Make sure the server is running: python start_webapp.py")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print_error("Request timed out. The server might be busy.")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print_error(f"Server error: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print_error("Invalid response from server")
        sys.exit(1)


def cmd_chat(args):
    """Chat with JARVIS."""
    if args.message:
        message = ' '.join(args.message)
    elif not sys.stdin.isatty():
        message = sys.stdin.read().strip()
    else:
        print_error("No message provided. Use: jarvis chat 'your message'")
        sys.exit(1)

    print_header("JARVIS")

    response = api_request("/api/chat/message", {
        "message": message,
        "context": {}
    }, args.server)

    print(response.get("content", "No response"))


def cmd_analyze(args):
    """Analyze code file or stdin."""
    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No input provided. Use: jarvis analyze file.py or cat file.py | jarvis analyze --stdin")
        sys.exit(1)

    print_header(f"Analyzing: {file_name}")

    response = api_request("/api/code/action", {
        "action": args.type,
        "code": code,
        "language": language,
        "file_name": file_name
    }, args.server)

    print(response.get("result", "No analysis result"))


def cmd_review(args):
    """Review code file."""
    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No input provided. Use: jarvis review file.py")
        sys.exit(1)

    print_header(f"Code Review: {file_name}")

    response = api_request("/api/code/action", {
        "action": "review",
        "code": code,
        "language": language,
        "file_name": file_name
    }, args.server)

    print(response.get("result", "No review result"))


def cmd_security(args):
    """Security scan code file."""
    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No input provided. Use: jarvis security file.py")
        sys.exit(1)

    print_header(f"Security Scan: {file_name}")

    # First do quick regex scan
    quick_response = api_request("/api/code/quick-scan", {
        "code": code,
        "language": language
    }, args.server)

    findings = quick_response.get("findings", [])
    if findings:
        print(colored("\nQuick Scan Findings:", Colors.YELLOW))
        for f in findings:
            severity_color = Colors.RED if f['severity'] == 'high' else Colors.YELLOW
            print(f"  {colored(f['severity'].upper(), severity_color)} Line {f['line']}: {f['category']}")
            print(f"    Match: {f['match']}")

    # Then do full LLM security analysis
    if args.full:
        print(colored("\nFull Security Analysis:", Colors.CYAN))
        response = api_request("/api/code/action", {
            "action": "security_scan",
            "code": code,
            "language": language,
            "file_name": file_name
        }, args.server)
        print(response.get("result", "No security analysis"))
    else:
        print(colored(f"\nTotal quick-scan issues: {len(findings)}", Colors.BOLD))
        print("Use --full for comprehensive LLM-based security analysis")


def cmd_commit_msg(args):
    """Generate commit message from git diff."""
    import subprocess

    if args.stdin or not sys.stdin.isatty():
        diff = sys.stdin.read()
    else:
        # Get git diff
        try:
            # Try staged changes first
            diff = subprocess.check_output(
                ["git", "diff", "--staged"],
                stderr=subprocess.DEVNULL
            ).decode('utf-8')

            if not diff.strip():
                # Fall back to unstaged changes
                diff = subprocess.check_output(
                    ["git", "diff"],
                    stderr=subprocess.DEVNULL
                ).decode('utf-8')

        except subprocess.CalledProcessError:
            print_error("Not in a git repository or git not available")
            sys.exit(1)
        except FileNotFoundError:
            print_error("git command not found")
            sys.exit(1)

    if not diff.strip():
        print_error("No changes to commit")
        sys.exit(1)

    print_header("Generating Commit Message")

    response = api_request("/api/code/commit-message", {
        "diff": diff
    }, args.server)

    message = response.get("message", "")

    if args.copy:
        try:
            import pyperclip
            pyperclip.copy(message)
            print_success("Commit message copied to clipboard!")
        except ImportError:
            print("(Install pyperclip to enable clipboard copy)")

    print(colored("\nSuggested commit message:", Colors.GREEN))
    print(f"\n{message}\n")

    if args.apply:
        # Actually commit with the message
        try:
            subprocess.run(["git", "commit", "-m", message], check=True)
            print_success("Commit created successfully!")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to create commit: {e}")


def cmd_explain(args):
    """Explain code."""
    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No input provided. Use: jarvis explain file.py")
        sys.exit(1)

    print_header(f"Explaining: {file_name}")

    response = api_request("/api/code/action", {
        "action": "explain",
        "code": code,
        "language": language,
        "file_name": file_name
    }, args.server)

    print(response.get("result", "No explanation"))


def cmd_improve(args):
    """Suggest improvements for code."""
    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No input provided. Use: jarvis improve file.py")
        sys.exit(1)

    print_header(f"Improving: {file_name}")

    response = api_request("/api/code/action", {
        "action": "improve",
        "code": code,
        "language": language,
        "file_name": file_name
    }, args.server)

    print(response.get("result", "No improvements suggested"))


def cmd_tests(args):
    """Generate tests for code."""
    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No input provided. Use: jarvis tests file.py")
        sys.exit(1)

    print_header(f"Generating Tests: {file_name}")

    response = api_request("/api/code/action", {
        "action": "generate_tests",
        "code": code,
        "language": language,
        "file_name": file_name
    }, args.server)

    print(response.get("result", "No tests generated"))


def cmd_ask(args):
    """Ask a question about code."""
    if not args.question:
        print_error("No question provided. Use: jarvis ask 'your question' file.py")
        sys.exit(1)

    if args.stdin or not sys.stdin.isatty():
        code = sys.stdin.read()
        file_name = "stdin"
        language = args.language or "unknown"
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print_error(f"File not found: {args.file}")
            sys.exit(1)
        code = file_path.read_text()
        file_name = file_path.name
        language = args.language or get_language_from_file(str(file_path))
    else:
        print_error("No code input provided")
        sys.exit(1)

    print_header(f"Question about: {file_name}")
    print(f"Q: {args.question}\n")

    response = api_request("/api/code/action", {
        "action": "ask",
        "code": code,
        "language": language,
        "file_name": file_name,
        "question": args.question
    }, args.server)

    print(response.get("result", "No answer"))


def main():
    parser = argparse.ArgumentParser(
        description="JARVIS CLI - AI-powered coding assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  jarvis chat "How do I implement a binary search?"
  jarvis analyze file.py
  jarvis review src/main.js
  jarvis security app.py --full
  jarvis commit-msg
  jarvis explain file.py
  jarvis improve file.py
  jarvis tests file.py
  jarvis ask "What does this function do?" file.py

  # Pipe support
  cat file.py | jarvis analyze --stdin
  git diff | jarvis commit-msg --stdin
        """
    )

    parser.add_argument(
        "--server", "-s",
        default=DEFAULT_SERVER,
        help=f"JARVIS server URL (default: {DEFAULT_SERVER})"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with JARVIS")
    chat_parser.add_argument("message", nargs="*", help="Message to send")
    chat_parser.set_defaults(func=cmd_chat)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze code")
    analyze_parser.add_argument("file", nargs="?", help="File to analyze")
    analyze_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    analyze_parser.add_argument("--language", "-l", help="Programming language")
    analyze_parser.add_argument("--type", "-t", default="general",
                               choices=["general", "complexity", "dependencies"],
                               help="Analysis type")
    analyze_parser.set_defaults(func=cmd_analyze)

    # Review command
    review_parser = subparsers.add_parser("review", help="Review code")
    review_parser.add_argument("file", nargs="?", help="File to review")
    review_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    review_parser.add_argument("--language", "-l", help="Programming language")
    review_parser.set_defaults(func=cmd_review)

    # Security command
    security_parser = subparsers.add_parser("security", help="Security scan")
    security_parser.add_argument("file", nargs="?", help="File to scan")
    security_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    security_parser.add_argument("--language", "-l", help="Programming language")
    security_parser.add_argument("--full", action="store_true",
                                help="Run full LLM-based security analysis")
    security_parser.set_defaults(func=cmd_security)

    # Commit message command
    commit_parser = subparsers.add_parser("commit-msg", help="Generate commit message")
    commit_parser.add_argument("--stdin", action="store_true", help="Read diff from stdin")
    commit_parser.add_argument("--copy", "-c", action="store_true",
                              help="Copy to clipboard")
    commit_parser.add_argument("--apply", "-a", action="store_true",
                              help="Apply commit with generated message")
    commit_parser.set_defaults(func=cmd_commit_msg)

    # Explain command
    explain_parser = subparsers.add_parser("explain", help="Explain code")
    explain_parser.add_argument("file", nargs="?", help="File to explain")
    explain_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    explain_parser.add_argument("--language", "-l", help="Programming language")
    explain_parser.set_defaults(func=cmd_explain)

    # Improve command
    improve_parser = subparsers.add_parser("improve", help="Suggest code improvements")
    improve_parser.add_argument("file", nargs="?", help="File to improve")
    improve_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    improve_parser.add_argument("--language", "-l", help="Programming language")
    improve_parser.set_defaults(func=cmd_improve)

    # Tests command
    tests_parser = subparsers.add_parser("tests", help="Generate tests")
    tests_parser.add_argument("file", nargs="?", help="File to generate tests for")
    tests_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    tests_parser.add_argument("--language", "-l", help="Programming language")
    tests_parser.set_defaults(func=cmd_tests)

    # Ask command
    ask_parser = subparsers.add_parser("ask", help="Ask about code")
    ask_parser.add_argument("question", help="Question to ask")
    ask_parser.add_argument("file", nargs="?", help="File to ask about")
    ask_parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    ask_parser.add_argument("--language", "-l", help="Programming language")
    ask_parser.set_defaults(func=cmd_ask)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
