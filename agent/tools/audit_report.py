"""
PHASE 2.2: Audit Report CLI Tool

Command-line tool for viewing and analyzing tool access audit logs.

Features:
- Query logs with filters (role, tool, domain, allowed/denied)
- Display statistics and trends
- Export reports in multiple formats
- Security auditing and compliance

Usage:
    # View all denied access attempts in last 7 days
    python -m agent.tools.audit_report --denied --days 7

    # View all access attempts for hr_recruiter
    python -m agent.tools.audit_report --role hr_recruiter

    # View statistics for last 30 days
    python -m agent.tools.audit_report --stats --days 30

    # View access attempts for specific tool
    python -m agent.tools.audit_report --tool approve_offer

    # Export to JSON
    python -m agent.tools.audit_report --role hr_recruiter --format json

Examples:
    # Show all denied attempts
    python -m agent.tools.audit_report --denied

    # Show hr_manager activity
    python -m agent.tools.audit_report --role hr_manager --days 14

    # Security audit: find all denied attempts for sensitive tools
    python -m agent.tools.audit_report --denied --domain hr --days 90
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from agent.tool_audit_log import (
    ToolAccessEvent,
    get_access_statistics,
    get_audit_logs,
)


# ══════════════════════════════════════════════════════════════════════
# Report Formatting
# ══════════════════════════════════════════════════════════════════════


def format_event_table(events: List[ToolAccessEvent]) -> str:
    """
    Format audit events as a table.

    Args:
        events: List of audit events

    Returns:
        Formatted table string
    """
    if not events:
        return "No events found."

    # Header
    lines = []
    lines.append("=" * 120)
    lines.append(
        f"{'Timestamp':<20} {'Role':<20} {'Tool':<25} {'Domain':<15} {'Status':<10} {'Reason':<30}"
    )
    lines.append("=" * 120)

    # Events
    for event in events:
        timestamp = event.timestamp[:19]  # Remove milliseconds
        role = event.role_id[:18] if len(event.role_id) > 18 else event.role_id
        tool = event.tool_name[:23] if len(event.tool_name) > 23 else event.tool_name
        domain = (event.domain or "N/A")[:13] if event.domain else "N/A"
        status = "✅ ALLOWED" if event.allowed else "❌ DENIED"
        reason = (event.reason or "")[:28] if event.reason else ""

        lines.append(
            f"{timestamp:<20} {role:<20} {tool:<25} {domain:<15} {status:<10} {reason:<30}"
        )

    lines.append("=" * 120)
    lines.append(f"Total events: {len(events)}")

    return "\n".join(lines)


def format_event_json(events: List[ToolAccessEvent]) -> str:
    """
    Format audit events as JSON.

    Args:
        events: List of audit events

    Returns:
        JSON string
    """
    events_dict = []
    for event in events:
        events_dict.append({
            "timestamp": event.timestamp,
            "mission_id": event.mission_id,
            "role_id": event.role_id,
            "tool_name": event.tool_name,
            "domain": event.domain,
            "allowed": event.allowed,
            "reason": event.reason,
            "user_id": event.user_id,
            "permissions_checked": event.permissions_checked,
            "metadata": event.metadata,
        })

    return json.dumps(events_dict, indent=2, ensure_ascii=False)


def format_statistics(stats: dict) -> str:
    """
    Format access statistics as a report.

    Args:
        stats: Statistics dictionary from get_access_statistics()

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("TOOL ACCESS AUDIT REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    lines.append("📊 SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Access Attempts:  {stats['total']}")
    lines.append(f"Granted:                {stats['granted']} ({stats['grant_rate']}%)")
    lines.append(f"Denied:                 {stats['denied']}")
    lines.append("")

    # Top tools
    if stats['top_tools']:
        lines.append("🔧 TOP TOOLS")
        lines.append("-" * 80)
        for tool, count in stats['top_tools'][:10]:
            lines.append(f"  {tool:<40} {count:>5} accesses")
        lines.append("")

    # Top roles
    if stats['top_roles']:
        lines.append("👤 TOP ROLES")
        lines.append("-" * 80)
        for role, count in stats['top_roles'][:10]:
            lines.append(f"  {role:<40} {count:>5} accesses")
        lines.append("")

    # Top domains
    if stats['top_domains']:
        lines.append("🏢 TOP DOMAINS")
        lines.append("-" * 80)
        for domain, count in stats['top_domains'][:10]:
            lines.append(f"  {domain:<40} {count:>5} accesses")
        lines.append("")

    # Top denied tools
    if stats['top_denied_tools']:
        lines.append("⚠️  TOP DENIED TOOLS")
        lines.append("-" * 80)
        for tool, count in stats['top_denied_tools'][:10]:
            lines.append(f"  {tool:<40} {count:>5} denials")
        lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# CLI Commands
# ══════════════════════════════════════════════════════════════════════


def cmd_list_events(args: argparse.Namespace) -> int:
    """
    List audit events with optional filters.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Determine allowed filter
        allowed_filter = None
        if args.denied:
            allowed_filter = False
        elif args.allowed:
            allowed_filter = True

        # Get logs
        events = get_audit_logs(
            role_id=args.role,
            tool_name=args.tool,
            domain=args.domain,
            allowed=allowed_filter,
            days=args.days
        )

        # Format output
        if args.format == "json":
            print(format_event_json(events))
        else:
            print(format_event_table(events))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_statistics(args: argparse.Namespace) -> int:
    """
    Display access statistics.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        stats = get_access_statistics(days=args.days)

        if args.format == "json":
            print(json.dumps(stats, indent=2))
        else:
            print(format_statistics(stats))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_security_audit(args: argparse.Namespace) -> int:
    """
    Run security audit report showing denied access attempts.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Get denied access attempts
        denied_events = get_audit_logs(
            allowed=False,
            days=args.days
        )

        print("")
        print("=" * 80)
        print("🔒 SECURITY AUDIT REPORT - DENIED ACCESS ATTEMPTS")
        print("=" * 80)
        print(f"Period: Last {args.days} days")
        print(f"Total Denied Attempts: {len(denied_events)}")
        print("")

        if denied_events:
            # Group by role
            by_role = {}
            for event in denied_events:
                if event.role_id not in by_role:
                    by_role[event.role_id] = []
                by_role[event.role_id].append(event)

            print("DENIED ATTEMPTS BY ROLE:")
            print("-" * 80)
            for role, events in sorted(by_role.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"\n{role} ({len(events)} denials):")
                for event in events[:5]:  # Show up to 5 per role
                    print(f"  - {event.timestamp[:19]} | {event.tool_name} | {event.reason}")
                if len(events) > 5:
                    print(f"  ... and {len(events) - 5} more")

            print("")
            print("=" * 80)
        else:
            print("✅ No denied access attempts found in the specified period.")
            print("=" * 80)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> int:
    """
    Main CLI entry point.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    parser = argparse.ArgumentParser(
        description="Tool Access Audit Report - View and analyze tool access logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View all denied access attempts in last 7 days
  %(prog)s --denied --days 7

  # View all access attempts for hr_recruiter
  %(prog)s --role hr_recruiter

  # View statistics
  %(prog)s --stats

  # Security audit
  %(prog)s --security-audit --days 30

  # Export to JSON
  %(prog)s --role hr_manager --format json
        """
    )

    # Filters
    parser.add_argument(
        "--role",
        type=str,
        help="Filter by role ID (e.g., hr_recruiter, manager)"
    )
    parser.add_argument(
        "--tool",
        type=str,
        help="Filter by tool name (e.g., approve_offer, send_email)"
    )
    parser.add_argument(
        "--domain",
        type=str,
        help="Filter by domain (e.g., hr, finance, coding)"
    )
    parser.add_argument(
        "--allowed",
        action="store_true",
        help="Show only allowed access attempts"
    )
    parser.add_argument(
        "--denied",
        action="store_true",
        help="Show only denied access attempts"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30)"
    )

    # Output format
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)"
    )

    # Commands
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show access statistics instead of event list"
    )
    parser.add_argument(
        "--security-audit",
        action="store_true",
        help="Run security audit report (denied access attempts)"
    )

    args = parser.parse_args()

    # Execute command
    if args.security_audit:
        return cmd_security_audit(args)
    elif args.stats:
        return cmd_statistics(args)
    else:
        return cmd_list_events(args)


if __name__ == "__main__":
    sys.exit(main())
