#!/usr/bin/env python3
# make.py
"""
Command dispatcher for multi-agent orchestrator development.

A lightweight argparse-based CLI tool for common development tasks.
No external dependencies required.

Usage:
    python3 make.py <command> [args]

Commands:
    run       - Run single orchestrator run
    auto      - Run auto-pilot mode
    safety    - Run safety checks only
    clean     - Clean logs
    docs      - Generate documentation
    profile   - Profile a run
    fixture   - Generate test fixture
    view      - View logs in browser
    test      - Run sanity tests
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Main command dispatcher."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Orchestrator - Development Commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 make.py run           # Run single orchestrator run
  python3 make.py auto          # Run auto-pilot mode
  python3 make.py clean --hard  # Delete all logs
  python3 make.py view --all    # View all logs in browser
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run command
    run_parser = subparsers.add_parser("run", help="Run single orchestrator run")

    # auto command
    auto_parser = subparsers.add_parser("auto", help="Run auto-pilot mode")

    # safety command
    safety_parser = subparsers.add_parser("safety", help="Run safety checks only")
    safety_parser.add_argument("project_dir", nargs="?", help="Project directory to check")

    # clean command
    clean_parser = subparsers.add_parser("clean", help="Clean logs")
    clean_parser.add_argument("--hard", action="store_true", help="Delete without confirmation")
    clean_parser.add_argument("--archive", metavar="PATH", help="Archive to path")
    clean_parser.add_argument("--exec", action="store_true", help="Include exec logs")
    clean_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")

    # docs command
    docs_parser = subparsers.add_parser("docs", help="Generate documentation")

    # profile command
    profile_parser = subparsers.add_parser("profile", help="Profile a run")

    # fixture command
    fixture_parser = subparsers.add_parser("fixture", help="Generate test fixture")

    # view command
    view_parser = subparsers.add_parser("view", help="View logs in browser")
    view_parser.add_argument("log_path", nargs="?", help="Specific log file path")
    view_parser.add_argument("--all", action="store_true", help="Show all logs")
    view_parser.add_argument("--latest", action="store_true", help="Show latest log")

    # test command
    test_parser = subparsers.add_parser("test", help="Run sanity tests")

    # help command
    help_parser = subparsers.add_parser("help", help="Show detailed help")

    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Get project root
    project_root = Path(__file__).resolve().parent

    # Route to appropriate handler
    if args.command == "run":
        run_command(project_root)
    elif args.command == "auto":
        auto_command(project_root)
    elif args.command == "safety":
        safety_command(project_root, args.project_dir)
    elif args.command == "clean":
        clean_command(project_root, args)
    elif args.command == "docs":
        docs_command(project_root)
    elif args.command == "profile":
        profile_command(project_root)
    elif args.command == "fixture":
        fixture_command(project_root)
    elif args.command == "view":
        view_command(project_root, args)
    elif args.command == "test":
        test_command(project_root)
    elif args.command == "help":
        parser.print_help()
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


def run_command(project_root: Path) -> None:
    """Run single orchestrator run."""
    script = project_root / "dev" / "run_once.py"
    run_script(script)


def auto_command(project_root: Path) -> None:
    """Run auto-pilot mode."""
    script = project_root / "dev" / "run_autopilot.py"
    run_script(script)


def safety_command(project_root: Path, project_dir: str | None) -> None:
    """Run safety checks."""
    if not project_dir:
        # Default to fixtures if available
        fixtures_dir = project_root / "sites" / "fixtures"
        if fixtures_dir.exists():
            project_dir = str(fixtures_dir)
        else:
            print("❌ Error: Please specify project directory")
            print("   Usage: python3 make.py safety <project_dir>")
            sys.exit(1)

    print(f"🛡️  Running safety checks on: {project_dir}\n")

    # Run safety checks via Python
    cmd = [
        sys.executable,
        "-c",
        f"import sys; sys.path.insert(0, '{project_root}/agent'); "
        f"from exec_safety import run_safety_checks; "
        f"result = run_safety_checks('{project_dir}', 'Safety check'); "
        f"print(f'\\nStatus: {{result[\"status\"]}}')",
    ]

    subprocess.run(cmd)


def clean_command(project_root: Path, args: argparse.Namespace) -> None:
    """Clean logs."""
    script = project_root / "dev" / "clean_logs.py"
    cmd = [sys.executable, str(script)]

    if args.hard:
        cmd.append("--hard")
    if args.archive:
        cmd.extend(["--archive", args.archive])
    if args.exec:
        cmd.append("--exec")
    if args.yes:
        cmd.append("--yes")

    subprocess.run(cmd)


def docs_command(project_root: Path) -> None:
    """Generate documentation."""
    script = project_root / "docs" / "generate_docs.py"
    run_script(script)


def profile_command(project_root: Path) -> None:
    """Profile a run."""
    script = project_root / "dev" / "profile_run.py"
    run_script(script)


def fixture_command(project_root: Path) -> None:
    """Generate test fixture."""
    script = project_root / "dev" / "generate_fixture.py"
    run_script(script)


def view_command(project_root: Path, args: argparse.Namespace) -> None:
    """View logs in browser."""
    script = project_root / "dev" / "view_logs.py"
    cmd = [sys.executable, str(script)]

    if args.log_path:
        cmd.append(args.log_path)
    if args.all:
        cmd.append("--all")
    if args.latest:
        cmd.append("--latest")

    subprocess.run(cmd)


def test_command(project_root: Path) -> None:
    """Run sanity tests."""
    script = project_root / "agent" / "tests_sanity" / "test_sanity.py"
    run_script(script)


def run_script(script_path: Path) -> None:
    """Run a Python script."""
    if not script_path.exists():
        print(f"❌ Error: Script not found: {script_path}")
        sys.exit(1)

    subprocess.run([sys.executable, str(script_path)])


if __name__ == "__main__":
    main()
