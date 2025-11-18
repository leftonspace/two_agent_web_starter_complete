#!/usr/bin/env python3
"""
Simple script to start the web dashboard.

Usage:
    python start_webapp.py
    python start_webapp.py --port 8001
    python start_webapp.py --host 0.0.0.0 --port 8080
"""

import argparse
import sys
from pathlib import Path

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent / "agent"
sys.path.insert(0, str(agent_dir))


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []

    try:
        import fastapi
    except ImportError:
        missing.append("fastapi")

    try:
        import jinja2
    except ImportError:
        missing.append("jinja2")

    try:
        import uvicorn
    except ImportError:
        missing.append("uvicorn")

    if missing:
        print("=" * 60)
        print("  ⚠️  Missing Dependencies")
        print("=" * 60)
        print()
        print("The following packages are required for the web dashboard:")
        for pkg in missing:
            print(f"  - {pkg}")
        print()
        print("Install them with:")
        print(f"  pip install {' '.join(missing)}")
        print()
        print("Or install all web dashboard dependencies:")
        print("  pip install -r requirements.txt")
        print("=" * 60)
        return False

    return True


def main():
    """Start the web dashboard."""
    parser = argparse.ArgumentParser(
        description="Start the AI Dev Team Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_webapp.py                    # Start on default port 8000
  python start_webapp.py --port 8001        # Use custom port
  python start_webapp.py --host 0.0.0.0    # Allow external connections
        """,
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)",
    )

    args = parser.parse_args()

    # Check dependencies
    if not check_dependencies():
        return 1

    # Import uvicorn
    import uvicorn

    print("=" * 60)
    print("  🤖 AI Dev Team Dashboard")
    print("=" * 60)
    print(f"  Starting web server on http://{args.host}:{args.port}")
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        uvicorn.run(
            "webapp.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
