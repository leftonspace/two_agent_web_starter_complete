#!/usr/bin/env python3
# view_run.py
"""
CLI dashboard to inspect orchestrator main run logs.

STAGE 2.3: Provides a simple text-based viewer for run_logs_main/<run_id>.jsonl.

Usage:
    python view_run.py <run_id>                # Show full summary and timeline
    python view_run.py <run_id> --only-errors  # Show summary and errors only

This tool reads the structured event logs created by core_logging.py
and presents a human-readable summary of what happened during a run.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Import core_logging to reuse event loading logic
import core_logging


# ══════════════════════════════════════════════════════════════════════
# Summary Computation
# ══════════════════════════════════════════════════════════════════════


def compute_summary(events: List[core_logging.LogEvent]) -> Dict[str, Any]:
    """
    Compute a summary from a list of log events.

    Returns:
        Dict with:
        - run_id: str
        - start_time: float (unix timestamp)
        - end_time: float (unix timestamp)
        - duration_seconds: float
        - num_iterations: int
        - models_used: set of str
        - safety_status: str or None
        - final_status: str or None
        - error_events: list of LogEvent
        - total_events: int
    """
    if not events:
        return {}

    run_id = events[0].run_id
    start_time = None
    end_time = None
    iterations = set()
    models = set()
    safety_status = None
    final_status = None
    error_events = []

    for event in events:
        # Start time
        if event.event_type == "start":
            start_time = event.timestamp

        # End time
        if event.event_type == "final_status":
            end_time = event.timestamp
            final_status = event.payload.get("status")

        # Iterations
        if event.event_type in ("iteration_begin", "iteration_end"):
            iteration = event.payload.get("iteration")
            if iteration is not None:
                iterations.add(iteration)

        # Models
        if event.event_type == "llm_call":
            model = event.payload.get("model")
            if model:
                models.add(model)

        # Safety
        if event.event_type == "safety_check":
            status = event.payload.get("summary_status")
            if status == "failed":
                safety_status = "failed"
            elif safety_status is None:  # Don't overwrite "failed"
                safety_status = status

        # Errors
        if event.event_type == "error":
            error_events.append(event)
        # Also track safety failures as errors
        if event.event_type == "safety_check" and event.payload.get("summary_status") == "failed":
            error_events.append(event)
        # Final status failures
        if event.event_type == "final_status" and event.payload.get("status") not in ("success", "approved"):
            # Only add if not already in error_events
            if event not in error_events:
                error_events.append(event)

    # Compute duration
    duration = None
    if start_time and end_time:
        duration = end_time - start_time

    return {
        "run_id": run_id,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "num_iterations": len(iterations),
        "models_used": sorted(models),
        "safety_status": safety_status,
        "final_status": final_status,
        "error_events": error_events,
        "total_events": len(events)
    }


# ══════════════════════════════════════════════════════════════════════
# Output Formatting
# ══════════════════════════════════════════════════════════════════════


def format_timestamp(ts: float) -> str:
    """Convert unix timestamp to human-readable format."""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def print_summary(summary: Dict[str, Any]) -> None:
    """Print a human-readable summary of the run."""
    print("=" * 70)
    print(f"Run {summary['run_id']}")
    print("=" * 70)

    if summary.get("start_time"):
        print(f"Start:      {format_timestamp(summary['start_time'])}")
    else:
        print("Start:      <unknown>")

    if summary.get("end_time"):
        print(f"End:        {format_timestamp(summary['end_time'])}")
    else:
        print("End:        <not finished>")

    if summary.get("duration_seconds") is not None:
        duration = summary["duration_seconds"]
        print(f"Duration:   {duration:.2f} seconds")
    else:
        print("Duration:   <unknown>")

    print(f"Iterations: {summary.get('num_iterations', 0)}")

    models = summary.get("models_used", [])
    if models:
        print(f"Models used: {', '.join(models)}")
    else:
        print("Models used: <none>")

    safety = summary.get("safety_status")
    if safety:
        safety_emoji = "✓" if safety == "passed" else "✗"
        print(f"Safety:     {safety_emoji} {safety}")
        if safety == "failed":
            # Show error/warning counts if available
            error_count = sum(
                e.payload.get("error_count", 0)
                for e in summary.get("error_events", [])
                if e.event_type == "safety_check"
            )
            warning_count = sum(
                e.payload.get("warning_count", 0)
                for e in summary.get("error_events", [])
                if e.event_type == "safety_check"
            )
            if error_count or warning_count:
                print(f"            (errors: {error_count}, warnings: {warning_count})")
    else:
        print("Safety:     <not run>")

    final = summary.get("final_status", "unknown")
    final_emoji = "✓" if final in ("success", "approved") else "✗"
    print(f"Final status: {final_emoji} {final}")

    print()


def print_timeline(events: List[core_logging.LogEvent], only_errors: bool = False) -> None:
    """
    Print a timeline of events.

    Args:
        events: List of LogEvent objects
        only_errors: If True, only show error/warning events
    """
    if not events:
        print("No events to display.")
        return

    start_time = events[0].timestamp if events else 0

    print("Timeline:")
    print("-" * 70)

    for event in events:
        # Skip non-error events if only_errors is True
        if only_errors:
            is_error_event = (
                event.event_type == "error"
                or event.event_type == "warning"
                or (event.event_type == "safety_check" and event.payload.get("summary_status") == "failed")
                or (event.event_type == "final_status" and event.payload.get("status") not in ("success", "approved"))
            )
            if not is_error_event:
                continue

        # Calculate time offset
        offset = event.timestamp - start_time

        # Format event info
        event_info = _format_event_info(event)

        # Print
        print(f"[+{offset:7.2f}s] {event.event_type:20s} {event_info}")

    print("-" * 70)
    print()


def _format_event_info(event: core_logging.LogEvent) -> str:
    """Format event-specific information for display."""
    payload = event.payload

    if event.event_type == "start":
        return f"Task: {payload.get('task_description', '<no description>')[:50]}..."

    elif event.event_type == "iteration_begin":
        iteration = payload.get("iteration", "?")
        return f"Iteration {iteration} started"

    elif event.event_type == "iteration_end":
        iteration = payload.get("iteration", "?")
        status = payload.get("status", "unknown")
        return f"Iteration {iteration} ended: {status}"

    elif event.event_type == "llm_call":
        role = payload.get("role", "unknown")
        model = payload.get("model", "unknown")
        iteration = payload.get("iteration", "")
        if iteration:
            return f"{role} ({model}) - iteration {iteration}"
        else:
            return f"{role} ({model})"

    elif event.event_type == "file_write":
        files = payload.get("files", [])
        count = payload.get("file_count", len(files))
        return f"{count} file(s) written"

    elif event.event_type == "safety_check":
        status = payload.get("summary_status", "unknown")
        error_count = payload.get("error_count", 0)
        warning_count = payload.get("warning_count", 0)
        emoji = "✓" if status == "passed" else "✗"
        return f"{emoji} {status} (errors: {error_count}, warnings: {warning_count})"

    elif event.event_type == "final_status":
        status = payload.get("status", "unknown")
        iterations = payload.get("iterations", 0)
        emoji = "✓" if status in ("success", "approved") else "✗"
        return f"{emoji} {status} after {iterations} iteration(s)"

    elif event.event_type == "error":
        message = payload.get("message", "No message")
        return f"ERROR: {message[:50]}"

    elif event.event_type == "warning":
        message = payload.get("message", "No message")
        return f"WARNING: {message[:50]}"

    else:
        # Generic fallback
        return str(payload)


# ══════════════════════════════════════════════════════════════════════
# Main CLI
# ══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="View main orchestrator run logs",
        epilog="Example: python view_run.py abc123def456 --only-errors"
    )
    parser.add_argument(
        "run_id",
        help="Run ID to inspect (e.g., abc123def456)"
    )
    parser.add_argument(
        "--only-errors",
        action="store_true",
        help="Only show events related to errors/warnings"
    )

    args = parser.parse_args()

    # Load events
    events = core_logging.load_run_events(args.run_id)

    if not events:
        log_file = core_logging.LOGS_DIR / f"{args.run_id}.jsonl"
        if not log_file.exists():
            print(f"Error: Log file not found: {log_file}", file=sys.stderr)
            print(f"\nAvailable run IDs:", file=sys.stderr)
            # List available run IDs
            if core_logging.LOGS_DIR.exists():
                log_files = sorted(core_logging.LOGS_DIR.glob("*.jsonl"))
                if log_files:
                    for lf in log_files[:10]:  # Show first 10
                        run_id = lf.stem
                        print(f"  - {run_id}", file=sys.stderr)
                    if len(log_files) > 10:
                        print(f"  ... and {len(log_files) - 10} more", file=sys.stderr)
                else:
                    print("  (none found)", file=sys.stderr)
            else:
                print("  (logs directory does not exist)", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Error: Log file exists but is empty or malformed: {log_file}", file=sys.stderr)
            sys.exit(1)

    # Compute summary
    summary = compute_summary(events)

    # Print summary
    print_summary(summary)

    # Print timeline
    if args.only_errors:
        error_events = [
            e for e in events
            if (
                e.event_type == "error"
                or e.event_type == "warning"
                or (e.event_type == "safety_check" and e.payload.get("summary_status") == "failed")
                or (e.event_type == "final_status" and e.payload.get("status") not in ("success", "approved"))
            )
        ]
        if error_events:
            print(f"Showing {len(error_events)} error/warning event(s):")
            print_timeline(error_events, only_errors=False)
        else:
            print("No errors or warnings found in this run.")
    else:
        print_timeline(events, only_errors=False)


if __name__ == "__main__":
    main()
