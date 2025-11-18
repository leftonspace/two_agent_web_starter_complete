#!/usr/bin/env python3
# dev/view_logs.py
"""
View orchestrator logs in a browser.

Reads run_summary.json or session_summary.json files and displays them
in a simple HTML viewer with no external dependencies.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import webbrowser
from pathlib import Path


def main() -> None:
    """View orchestrator logs in browser."""
    parser = argparse.ArgumentParser(description="View orchestrator logs in browser")
    parser.add_argument(
        "log_path",
        nargs="?",
        help="Path to specific run_summary.json or session_summary.json (optional)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all runs from run_logs/ directory",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Show latest run only",
    )

    args = parser.parse_args()

    # Find project root
    project_root = Path(__file__).resolve().parent.parent
    run_logs_dir = project_root / "run_logs"

    # Collect log data
    log_data = []

    if args.log_path:
        # Load specific log file
        log_file = Path(args.log_path)
        if not log_file.exists():
            print(f"❌ Error: Log file not found: {log_file}")
            sys.exit(1)

        try:
            log_data.append(json.loads(log_file.read_text(encoding="utf-8")))
            print(f"📄 Loaded: {log_file}")
        except Exception as e:
            print(f"❌ Error loading {log_file}: {e}")
            sys.exit(1)

    elif args.all:
        # Load all logs from run_logs/
        if not run_logs_dir.exists():
            print(f"❌ Error: run_logs/ directory not found")
            sys.exit(1)

        print(f"📁 Scanning {run_logs_dir}...")

        for log_dir in sorted(run_logs_dir.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True):
            if not log_dir.is_dir():
                continue

            # Check for session_summary.json first
            session_file = log_dir / "session_summary.json"
            if session_file.exists():
                try:
                    log_data.append(json.loads(session_file.read_text(encoding="utf-8")))
                    print(f"   ✓ Session: {log_dir.name}")
                except Exception as e:
                    print(f"   ⚠️  Failed to load {session_file}: {e}")
                continue

            # Otherwise check for run_summary.json
            run_file = log_dir / "run_summary.json"
            if run_file.exists():
                try:
                    log_data.append(json.loads(run_file.read_text(encoding="utf-8")))
                    print(f"   ✓ Run: {log_dir.name}")
                except Exception as e:
                    print(f"   ⚠️  Failed to load {run_file}: {e}")

        print(f"\n📊 Loaded {len(log_data)} log(s)")

    else:
        # Default: load latest run
        if not run_logs_dir.exists():
            print(f"❌ Error: run_logs/ directory not found")
            sys.exit(1)

        log_dirs = sorted(
            [d for d in run_logs_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )

        if not log_dirs:
            print(f"❌ Error: No logs found in {run_logs_dir}")
            sys.exit(1)

        latest_dir = log_dirs[0]

        # Check for session or run summary
        session_file = latest_dir / "session_summary.json"
        run_file = latest_dir / "run_summary.json"

        if session_file.exists():
            log_data.append(json.loads(session_file.read_text(encoding="utf-8")))
            print(f"📄 Loaded latest session: {latest_dir.name}")
        elif run_file.exists():
            log_data.append(json.loads(run_file.read_text(encoding="utf-8")))
            print(f"📄 Loaded latest run: {latest_dir.name}")
        else:
            print(f"❌ Error: No summary file found in {latest_dir}")
            sys.exit(1)

    if not log_data:
        print("❌ No logs to display")
        sys.exit(1)

    # Load HTML template
    template_path = Path(__file__).parent / "templates" / "log_viewer.html"
    if not template_path.exists():
        print(f"❌ Error: Template not found: {template_path}")
        sys.exit(1)

    html_template = template_path.read_text(encoding="utf-8")

    # Inject log data
    log_data_json = json.dumps(log_data, indent=2)
    html_content = html_template.replace("{{LOG_DATA_PLACEHOLDER}}", log_data_json)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_content)
        temp_file = f.name

    print(f"🌐 Opening in browser...")
    print(f"   Temp file: {temp_file}")

    # Open in browser
    webbrowser.open(f"file://{temp_file}")

    print(f"\n✅ Log viewer opened in browser")
    print(f"   (Temporary file will remain at: {temp_file})")


if __name__ == "__main__":
    main()
