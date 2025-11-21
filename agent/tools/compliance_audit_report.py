"""
PHASE 5.1: Compliance Audit Report CLI Tool

Command-line tool for querying and exporting immutable audit logs
for compliance purposes (WORM - Write-Once-Read-Many).

Features:
- Query logs with filters (user, action, entity type, date range)
- Verify log integrity (tamper detection)
- Export reports in multiple formats (CSV, JSON, PDF)
- Security auditing and compliance reporting
- Statistics and trends analysis

Usage:
    # View all actions by user in last 30 days
    python -m agent.tools.compliance_audit_report --user hr_manager@company.com --days 30

    # View file write operations
    python -m agent.tools.compliance_audit_report --action file_write --days 7

    # Security audit: verify log integrity
    python -m agent.tools.compliance_audit_report --verify-integrity

    # Export to CSV for compliance
    python -m agent.tools.compliance_audit_report --user hr_manager@company.com --format csv --output report.csv

    # Export to PDF
    python -m agent.tools.compliance_audit_report --days 30 --format pdf --output audit_report.pdf

    # View statistics
    python -m agent.tools.compliance_audit_report --stats

Examples:
    # HR manager activity report
    python -m agent.tools.compliance_audit_report --user hr_manager@company.com --days 30 --format csv

    # All approval decisions in Q1 2025
    python -m agent.tools.compliance_audit_report --action approval_decision --start-date 2025-01-01 --end-date 2025-03-31

    # Security audit: all file deletions
    python -m agent.tools.compliance_audit_report --action file_delete --days 90
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from audit_log import AuditEntry, AuditLogger, get_audit_logger


# ══════════════════════════════════════════════════════════════════════
# Report Formatting
# ══════════════════════════════════════════════════════════════════════


def format_entry_table(entries: List[AuditEntry]) -> str:
    """
    Format audit entries as a table.

    Args:
        entries: List of audit entries

    Returns:
        Formatted table string
    """
    if not entries:
        return "No entries found."

    lines = []
    lines.append("")
    lines.append("=" * 140)
    lines.append(
        f"{'ID':<6} {'Timestamp':<20} {'User':<30} {'Action':<20} {'Entity':<25} {'Reason':<35}"
    )
    lines.append("=" * 140)

    for entry in entries:
        entry_id = str(entry.entry_id)
        timestamp = entry.timestamp[:19]  # Remove milliseconds
        user = entry.user_id[:28] if len(entry.user_id) > 28 else entry.user_id
        action = entry.action[:18] if len(entry.action) > 18 else entry.action
        entity = f"{entry.entity_type}:{entry.entity_id}"
        entity = entity[:23] if len(entity) > 23 else entity
        reason = entry.reason[:33] if entry.reason and len(entry.reason) > 33 else (entry.reason or "")

        lines.append(f"{entry_id:<6} {timestamp:<20} {user:<30} {action:<20} {entity:<25} {reason:<35}")

    lines.append("=" * 140)
    lines.append(f"Total entries: {len(entries)}")
    lines.append("")

    return "\n".join(lines)


def format_entry_json(entries: List[AuditEntry]) -> str:
    """
    Format audit entries as JSON.

    Args:
        entries: List of audit entries

    Returns:
        JSON string
    """
    entries_dict = []
    for entry in entries:
        entries_dict.append({
            "entry_id": entry.entry_id,
            "user_id": entry.user_id,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "timestamp": entry.timestamp,
            "changes": entry.changes,
            "reason": entry.reason,
            "metadata": entry.metadata,
            "signature": entry.signature,
            "prev_signature": entry.prev_signature,
        })

    return json.dumps(entries_dict, indent=2, ensure_ascii=False)


def export_to_csv(entries: List[AuditEntry], output_file: Path) -> None:
    """
    Export audit entries to CSV file.

    Args:
        entries: List of audit entries
        output_file: Path to output CSV file
    """
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "Entry ID",
            "Timestamp",
            "User ID",
            "Action",
            "Entity Type",
            "Entity ID",
            "Changes",
            "Reason",
            "Metadata",
            "Signature",
        ])

        # Data
        for entry in entries:
            writer.writerow([
                entry.entry_id,
                entry.timestamp,
                entry.user_id,
                entry.action,
                entry.entity_type,
                entry.entity_id,
                json.dumps(entry.changes) if entry.changes else "",
                entry.reason,
                json.dumps(entry.metadata) if entry.metadata else "",
                entry.signature,
            ])

    print(f"✅ Exported {len(entries)} entries to: {output_file}")


def export_to_pdf(entries: List[AuditEntry], output_file: Path) -> None:
    """
    Export audit entries to PDF file.

    Note: This requires reportlab library. If not available, falls back to HTML.

    Args:
        entries: List of audit entries
        output_file: Path to output PDF file
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        # Create PDF
        doc = SimpleDocTemplate(str(output_file), pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("Compliance Audit Report", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Summary
        summary_text = f"""
        <b>Report Generated:</b> {datetime.utcnow().isoformat()}<br/>
        <b>Total Entries:</b> {len(entries)}<br/>
        <b>Date Range:</b> {entries[-1].timestamp if entries else 'N/A'} to {entries[0].timestamp if entries else 'N/A'}
        """
        summary = Paragraph(summary_text, styles["Normal"])
        elements.append(summary)
        elements.append(Spacer(1, 0.3 * inch))

        # Table data
        table_data = [["ID", "Timestamp", "User", "Action", "Entity", "Reason"]]
        for entry in entries[:100]:  # Limit to first 100 for PDF
            table_data.append([
                str(entry.entry_id),
                entry.timestamp[:16],
                entry.user_id[:20],
                entry.action[:15],
                f"{entry.entity_type}:{entry.entity_id}"[:25],
                entry.reason[:30] if entry.reason else "",
            ])

        # Create table
        table = Table(table_data, colWidths=[0.5 * inch, 1.2 * inch, 1.5 * inch, 1.2 * inch, 2 * inch, 2.5 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)

        if len(entries) > 100:
            elements.append(Spacer(1, 0.2 * inch))
            note = Paragraph(f"<i>Note: Showing first 100 of {len(entries)} entries. Use CSV export for complete data.</i>", styles["Italic"])
            elements.append(note)

        # Build PDF
        doc.build(elements)
        print(f"✅ Exported {len(entries)} entries to PDF: {output_file}")

    except ImportError:
        print("⚠️  reportlab library not installed. Falling back to HTML export.")
        html_file = output_file.with_suffix(".html")
        export_to_html(entries, html_file)


def export_to_html(entries: List[AuditEntry], output_file: Path) -> None:
    """
    Export audit entries to HTML file.

    Args:
        entries: List of audit entries
        output_file: Path to output HTML file
    """
    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Compliance Audit Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
        td { border: 1px solid #ddd; padding: 8px; }
        tr:nth-child(even) { background: #f2f2f2; }
        .timestamp { font-family: monospace; }
        .signature { font-family: monospace; font-size: 0.9em; color: #666; }
    </style>
</head>
<body>
    <h1>Compliance Audit Report</h1>
    <div class="summary">
        <p><strong>Report Generated:</strong> {generated_at}</p>
        <p><strong>Total Entries:</strong> {total_entries}</p>
        <p><strong>Date Range:</strong> {date_range}</p>
    </div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Reason</th>
                <th>Signature</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>
    """

    rows = []
    for entry in entries:
        rows.append(f"""
            <tr>
                <td>{entry.entry_id}</td>
                <td class="timestamp">{entry.timestamp}</td>
                <td>{entry.user_id}</td>
                <td>{entry.action}</td>
                <td>{entry.entity_type}:{entry.entity_id}</td>
                <td>{entry.reason or ''}</td>
                <td class="signature">{entry.signature[:16]}...</td>
            </tr>
        """)

    date_range = "N/A"
    if entries:
        date_range = f"{entries[-1].timestamp} to {entries[0].timestamp}"

    html = html.format(
        generated_at=datetime.utcnow().isoformat(),
        total_entries=len(entries),
        date_range=date_range,
        rows="\n".join(rows),
    )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Exported {len(entries)} entries to HTML: {output_file}")


def format_statistics(stats: dict) -> str:
    """
    Format audit statistics as a report.

    Args:
        stats: Statistics dictionary from audit_logger.get_stats()

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("")
    lines.append("=" * 80)
    lines.append("COMPLIANCE AUDIT STATISTICS")
    lines.append("=" * 80)
    lines.append("")

    lines.append("📊 SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Entries:      {stats['total_entries']}")
    lines.append(f"Unique Users:       {stats['unique_users']}")
    lines.append(f"Unique Actions:     {stats['unique_actions']}")

    if stats['date_range']:
        lines.append(f"Date Range:         {stats['date_range']['start']} to {stats['date_range']['end']}")

    lines.append("")

    # Actions by type
    if stats.get('actions_by_type'):
        lines.append("🔧 ACTIONS BY TYPE")
        lines.append("-" * 80)
        for action, count in sorted(stats['actions_by_type'].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {action:<40} {count:>5} actions")
        lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# CLI Commands
# ══════════════════════════════════════════════════════════════════════


def cmd_list_entries(args: argparse.Namespace) -> int:
    """
    List audit entries with optional filters.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        audit = get_audit_logger()

        # Get logs
        entries = audit.query_logs(
            user_id=args.user,
            action=args.action,
            entity_type=args.entity_type,
            start_date=args.start_date,
            end_date=args.end_date,
            limit=args.limit,
        )

        # Filter by days if specified
        if args.days and not args.start_date:
            cutoff = (datetime.utcnow() - timedelta(days=args.days)).isoformat() + "Z"
            entries = [e for e in entries if e.timestamp >= cutoff]

        # Output based on format
        if args.output:
            output_path = Path(args.output)
            if args.format == "csv":
                export_to_csv(entries, output_path)
            elif args.format == "pdf":
                export_to_pdf(entries, output_path)
            elif args.format == "html":
                export_to_html(entries, output_path)
            elif args.format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(format_entry_json(entries))
                print(f"✅ Exported {len(entries)} entries to JSON: {output_path}")
            return 0
        else:
            # Print to stdout
            if args.format == "json":
                print(format_entry_json(entries))
            else:
                print(format_entry_table(entries))

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_verify_integrity(args: argparse.Namespace) -> int:
    """
    Verify audit log integrity (tamper detection).

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = tampering detected)
    """
    try:
        audit = get_audit_logger()

        print("")
        print("=" * 80)
        print("🔒 AUDIT LOG INTEGRITY VERIFICATION")
        print("=" * 80)
        print("")

        is_valid, issues = audit.verify_log_integrity()

        if is_valid:
            print("✅ Audit log integrity verified - No tampering detected")
            print("")
            print("Checks passed:")
            print("  ✓ All signatures valid (HMAC-SHA256)")
            print("  ✓ Signature chain unbroken (blockchain-style)")
            print("  ✓ Entry IDs monotonic (no gaps or duplicates)")
            print("")
            print("=" * 80)
            return 0
        else:
            print("❌ TAMPERING DETECTED - Audit log has been modified")
            print("")
            print(f"Issues found: {len(issues)}")
            print("")
            for issue in issues:
                print(f"  ⚠️  {issue}")
            print("")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_statistics(args: argparse.Namespace) -> int:
    """
    Display audit statistics.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        audit = get_audit_logger()
        stats = audit.get_stats()

        if args.format == "json":
            print(json.dumps(stats, indent=2))
        else:
            print(format_statistics(stats))

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
        description="Compliance Audit Report - Query and export immutable audit logs (WORM)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View all actions by user in last 30 days
  %(prog)s --user hr_manager@company.com --days 30

  # View file write operations
  %(prog)s --action file_write --days 7

  # Verify log integrity
  %(prog)s --verify-integrity

  # Export to CSV
  %(prog)s --user hr_manager@company.com --format csv --output report.csv

  # Export to PDF
  %(prog)s --days 30 --format pdf --output audit.pdf

  # Statistics
  %(prog)s --stats
        """
    )

    # Filters
    parser.add_argument("--user", type=str, help="Filter by user ID (email, username)")
    parser.add_argument("--action", type=str, help="Filter by action type (file_write, tool_execution, etc.)")
    parser.add_argument("--entity-type", type=str, help="Filter by entity type (file, tool, approval, etc.)")
    parser.add_argument("--start-date", type=str, help="Filter by start date (ISO 8601: 2025-01-01)")
    parser.add_argument("--end-date", type=str, help="Filter by end date (ISO 8601: 2025-01-31)")
    parser.add_argument("--days", type=int, help="Number of days to look back (default: all)")
    parser.add_argument("--limit", type=int, help="Maximum number of entries to return")

    # Output
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv", "pdf", "html"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument("--output", type=str, help="Output file path (for csv/pdf/html/json export)")

    # Commands
    parser.add_argument("--stats", action="store_true", help="Show audit statistics")
    parser.add_argument("--verify-integrity", action="store_true", help="Verify log integrity (tamper detection)")

    args = parser.parse_args()

    # Execute command
    if args.verify_integrity:
        return cmd_verify_integrity(args)
    elif args.stats:
        return cmd_statistics(args)
    else:
        return cmd_list_entries(args)


if __name__ == "__main__":
    sys.exit(main())
