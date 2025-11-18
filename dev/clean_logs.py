#!/usr/bin/env python3
# dev/clean_logs.py
"""
Clean or archive run logs safely.

Supports:
- --hard: Delete all logs permanently
- --archive <path>: Move logs to archive location
- Default: Interactive confirmation before deletion
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    """Clean or archive run logs."""
    parser = argparse.ArgumentParser(
        description="Clean or archive orchestrator run logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--hard",
        action="store_true",
        help="Delete logs permanently without confirmation",
    )
    parser.add_argument(
        "--archive",
        type=str,
        metavar="PATH",
        help="Archive logs to specified path instead of deleting",
    )
    parser.add_argument(
        "--exec",
        action="store_true",
        help="Also clean execution safety logs (run_logs_exec/)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts",
    )

    args = parser.parse_args()

    # Find log directories
    project_root = Path(__file__).resolve().parent.parent
    run_logs_dir = project_root / "run_logs"
    exec_logs_dir = project_root / "run_logs_exec"

    # Determine what to clean
    dirs_to_clean = []
    if run_logs_dir.exists():
        dirs_to_clean.append(("run_logs", run_logs_dir))

    if args.exec and exec_logs_dir.exists():
        dirs_to_clean.append(("run_logs_exec", exec_logs_dir))

    if not dirs_to_clean:
        print("✓ No log directories found. Nothing to clean.")
        return

    # Count log entries
    total_size = 0
    total_entries = 0
    for name, log_dir in dirs_to_clean:
        entries = list(log_dir.iterdir())
        total_entries += len(entries)

        # Calculate size
        for entry in entries:
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())

    print(f"\n📊 Log Statistics:")
    print(f"   Directories:     {', '.join(name for name, _ in dirs_to_clean)}")
    print(f"   Total entries:   {total_entries}")
    print(f"   Total size:      {total_size / 1024 / 1024:.2f} MB\n")

    # Handle archive mode
    if args.archive:
        archive_path = Path(args.archive).resolve()

        if not args.yes:
            print(f"📦 Archive logs to: {archive_path}")
            response = input("   Continue? [y/N]: ").strip().lower()
            if response not in ("y", "yes"):
                print("❌ Cancelled.")
                return

        # Create archive directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_target = archive_path / f"run_logs_{timestamp}"
        archive_target.mkdir(parents=True, exist_ok=True)

        print(f"\n📦 Archiving logs...")
        for name, log_dir in dirs_to_clean:
            target_dir = archive_target / name
            print(f"   Moving {name}/ -> {target_dir}")
            shutil.move(str(log_dir), str(target_dir))

        print(f"\n✅ Logs archived to: {archive_target}")
        return

    # Handle deletion
    if args.hard and not args.yes:
        print(f"⚠️  WARNING: This will permanently delete {total_entries} log entries!")
        response = input("   Type 'DELETE' to confirm: ").strip()
        if response != "DELETE":
            print("❌ Cancelled.")
            return
    elif not args.hard and not args.yes:
        print(f"🗑️  Delete {total_entries} log entries?")
        response = input("   Continue? [y/N]: ").strip().lower()
        if response not in ("y", "yes"):
            print("❌ Cancelled.")
            return

    # Delete logs
    print(f"\n🗑️  Deleting logs...")
    for name, log_dir in dirs_to_clean:
        print(f"   Removing {name}/")
        shutil.rmtree(log_dir)

    print(f"\n✅ Logs deleted successfully.")


if __name__ == "__main__":
    main()
