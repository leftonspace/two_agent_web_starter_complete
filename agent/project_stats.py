"""
PHASE 2.2: Project Statistics & Evolution Tracking

Tracks project evolution over time:
- File counts, lines of code
- Mission success rates
- Cost trends
- Agent performance metrics
- Code complexity trends

Usage:
    >>> from agent import project_stats
    >>> stats = project_stats.collect_stats("/path/to/project")
    >>> project_stats.save_stats(stats)
    >>> history = project_stats.get_stats_history(days=30)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports
try:
    import paths as paths_module
    PATHS_AVAILABLE = True
except ImportError:
    PATHS_AVAILABLE = False

try:
    from knowledge_graph import KnowledgeGraph
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Project Statistics Collection
# ══════════════════════════════════════════════════════════════════════


def count_lines_of_code(file_path: Path) -> int:
    """
    Count lines of code in a file (excluding empty lines and comments).

    Args:
        file_path: Path to file

    Returns:
        Number of lines of code
    """
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        # Count non-empty, non-comment lines
        loc = 0
        in_multiline_comment = False

        for line in lines:
            stripped = line.strip()

            # Skip empty lines
            if not stripped:
                continue

            # Python/JS comments
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            # Multiline comments (Python docstrings, JS /* */)
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    # Single line docstring
                    continue
                in_multiline_comment = not in_multiline_comment
                continue

            if stripped.startswith("/*"):
                in_multiline_comment = True
                continue

            if stripped.endswith("*/"):
                in_multiline_comment = False
                continue

            if in_multiline_comment:
                continue

            # Valid line of code
            loc += 1

        return loc

    except Exception:
        return 0


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file content.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of SHA256 hash
    """
    try:
        with file_path.open("rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""


def collect_file_stats(project_dir: Path) -> Dict[str, Any]:
    """
    Collect statistics about files in a project.

    Args:
        project_dir: Project directory path

    Returns:
        Dict with file counts, sizes, LOC by extension
    """
    if not project_dir.exists():
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_loc": 0,
            "by_extension": {},
        }

    file_counts = {}
    file_sizes = {}
    file_locs = {}

    # Iterate through all files (skip .git, node_modules, etc.)
    exclude_dirs = {".git", "node_modules", "__pycache__", ".history", "venv", "env"}

    for file_path in project_dir.rglob("*"):
        # Skip directories and excluded paths
        if file_path.is_dir():
            continue

        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue

        # Get file extension
        ext = file_path.suffix or "(no extension)"

        # Count files
        file_counts[ext] = file_counts.get(ext, 0) + 1

        # Sum file sizes
        try:
            size = file_path.stat().st_size
            file_sizes[ext] = file_sizes.get(ext, 0) + size
        except Exception:
            pass

        # Count LOC for code files
        if ext in {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".go", ".rs", ".java", ".cpp", ".c"}:
            loc = count_lines_of_code(file_path)
            file_locs[ext] = file_locs.get(ext, 0) + loc

    return {
        "total_files": sum(file_counts.values()),
        "total_size_bytes": sum(file_sizes.values()),
        "total_loc": sum(file_locs.values()),
        "by_extension": {
            ext: {
                "count": file_counts.get(ext, 0),
                "size_bytes": file_sizes.get(ext, 0),
                "loc": file_locs.get(ext, 0),
            }
            for ext in set(list(file_counts.keys()) + list(file_sizes.keys()) + list(file_locs.keys()))
        },
    }


def collect_mission_stats() -> Dict[str, Any]:
    """
    Collect statistics about missions from knowledge graph.

    Returns:
        Dict with mission counts, success rates, costs
    """
    if not KG_AVAILABLE:
        return {
            "total_missions": 0,
            "successful_missions": 0,
            "failed_missions": 0,
            "success_rate": 0.0,
            "total_cost_usd": 0.0,
            "avg_cost_usd": 0.0,
        }

    kg = KnowledgeGraph()
    stats = kg.get_stats()

    mission_stats = stats.get("missions", {})
    total = mission_stats.get("total", 0)
    successful = mission_stats.get("successful", 0)

    return {
        "total_missions": total,
        "successful_missions": successful,
        "failed_missions": mission_stats.get("failed", 0),
        "success_rate": (successful / total * 100) if total > 0 else 0.0,
        "total_cost_usd": mission_stats.get("total_cost_usd", 0.0),
        "avg_cost_usd": mission_stats.get("avg_cost_usd", 0.0),
        "avg_duration_seconds": mission_stats.get("avg_duration_seconds", 0.0),
        "total_files_modified": mission_stats.get("total_files_modified", 0),
    }


def collect_stats(project_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Collect comprehensive project statistics.

    Args:
        project_dir: Project directory. If None, uses current directory.

    Returns:
        Dict with all project statistics
    """
    if project_dir is None:
        if PATHS_AVAILABLE:
            project_dir = paths_module.get_root()
        else:
            project_dir = Path.cwd()

    file_stats = collect_file_stats(project_dir)
    mission_stats = collect_mission_stats()

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project_dir": str(project_dir),
        "files": file_stats,
        "missions": mission_stats,
    }


# ══════════════════════════════════════════════════════════════════════
# Statistics Persistence
# ══════════════════════════════════════════════════════════════════════


def get_stats_file_path() -> Path:
    """
    Get path to project stats JSON file.

    Returns:
        Path to data/project_stats.json
    """
    if PATHS_AVAILABLE:
        return paths_module.get_project_stats_path()
    else:
        return Path(__file__).parent.parent / "data" / "project_stats.json"


def save_stats(stats: Dict[str, Any]) -> None:
    """
    Save project statistics to file.

    Appends to history array in JSON file.

    Args:
        stats: Statistics dict from collect_stats()
    """
    stats_file = get_stats_file_path()
    stats_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing history
    if stats_file.exists():
        try:
            with stats_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                history = data.get("history", [])
        except Exception:
            history = []
    else:
        history = []

    # Append new stats
    history.append(stats)

    # Keep only last 1000 entries
    if len(history) > 1000:
        history = history[-1000:]

    # Save updated history
    with stats_file.open("w", encoding="utf-8") as f:
        json.dump({"history": history}, f, indent=2)


def get_stats_history(days: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get historical project statistics.

    Args:
        days: Optional number of days to look back
        limit: Optional maximum number of entries to return

    Returns:
        List of statistics dicts ordered by timestamp (newest first)
    """
    stats_file = get_stats_file_path()

    if not stats_file.exists():
        return []

    try:
        with stats_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            history = data.get("history", [])
    except Exception:
        return []

    # Filter by days if specified
    if days is not None:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat() + "Z"
        history = [s for s in history if s.get("timestamp", "") >= cutoff_str]

    # Sort by timestamp (newest first)
    history.sort(key=lambda s: s.get("timestamp", ""), reverse=True)

    # Apply limit
    if limit is not None:
        history = history[:limit]

    return history


def get_latest_stats() -> Optional[Dict[str, Any]]:
    """
    Get most recent project statistics.

    Returns:
        Latest stats dict or None
    """
    history = get_stats_history(limit=1)
    return history[0] if history else None


# ══════════════════════════════════════════════════════════════════════
# Statistics Analysis
# ══════════════════════════════════════════════════════════════════════


def compute_growth_rate(history: List[Dict[str, Any]], metric_path: str) -> float:
    """
    Compute growth rate for a metric over time.

    Args:
        history: Statistics history (newest first)
        metric_path: Dot-separated path to metric (e.g., "files.total_loc")

    Returns:
        Growth rate as percentage (positive = growth, negative = decline)
    """
    if len(history) < 2:
        return 0.0

    def get_metric(stats: Dict[str, Any], path: str) -> float:
        """Extract metric value from nested dict."""
        keys = path.split(".")
        value = stats
        for key in keys:
            value = value.get(key, {})
            if not isinstance(value, (dict, int, float)):
                break
        return float(value) if isinstance(value, (int, float)) else 0.0

    # Get oldest and newest values
    newest = get_metric(history[0], metric_path)
    oldest = get_metric(history[-1], metric_path)

    if oldest == 0:
        return 0.0

    growth_rate = ((newest - oldest) / oldest) * 100
    return growth_rate


def generate_summary_report(days: int = 30) -> str:
    """
    Generate a human-readable summary report.

    Args:
        days: Number of days to analyze

    Returns:
        Multi-line summary report string
    """
    history = get_stats_history(days=days)

    if not history:
        return "No statistics available."

    latest = history[0]

    report_lines = [
        f"PROJECT STATISTICS SUMMARY (Last {days} days)",
        "=" * 60,
        "",
        "Files:",
        f"  Total files: {latest['files']['total_files']}",
        f"  Total LOC: {latest['files']['total_loc']:,}",
        f"  Total size: {latest['files']['total_size_bytes'] / 1024:.1f} KB",
        "",
        "Missions:",
        f"  Total missions: {latest['missions']['total_missions']}",
        f"  Successful: {latest['missions']['successful_missions']}",
        f"  Failed: {latest['missions']['failed_missions']}",
        f"  Success rate: {latest['missions']['success_rate']:.1f}%",
        f"  Total cost: ${latest['missions']['total_cost_usd']:.2f}",
        f"  Avg cost/mission: ${latest['missions']['avg_cost_usd']:.4f}",
        "",
    ]

    # Growth rates (if we have enough history)
    if len(history) >= 2:
        loc_growth = compute_growth_rate(history, "files.total_loc")
        file_growth = compute_growth_rate(history, "files.total_files")

        report_lines.extend([
            "Growth Trends:",
            f"  LOC growth: {loc_growth:+.1f}%",
            f"  File growth: {file_growth:+.1f}%",
            "",
        ])

    # Top file types
    by_ext = latest['files'].get('by_extension', {})
    if by_ext:
        sorted_exts = sorted(
            by_ext.items(),
            key=lambda x: x[1].get('loc', 0),
            reverse=True
        )[:5]

        report_lines.extend([
            "Top File Types (by LOC):",
        ])

        for ext, stats in sorted_exts:
            loc = stats.get('loc', 0)
            count = stats.get('count', 0)
            if loc > 0:
                report_lines.append(f"  {ext}: {loc:,} LOC in {count} files")

    report_lines.append("")
    report_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    return "\n".join(report_lines)


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for project stats."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Project Statistics Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect and save current statistics")
    collect_parser.add_argument(
        "--project-dir",
        type=str,
        help="Project directory (default: current directory)",
    )

    # Show command
    show_parser = subparsers.add_parser("show", help="Show statistics report")
    show_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )

    # History command
    history_parser = subparsers.add_parser("history", help="Show statistics history")
    history_parser.add_argument(
        "--days",
        type=int,
        help="Number of days to look back",
    )
    history_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of entries (default: 10)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "collect":
        project_dir = Path(args.project_dir) if args.project_dir else None
        stats = collect_stats(project_dir)
        save_stats(stats)
        print(f"✓ Statistics collected and saved")
        print(f"  Files: {stats['files']['total_files']}")
        print(f"  LOC: {stats['files']['total_loc']:,}")
        print(f"  Missions: {stats['missions']['total_missions']}")

    elif args.command == "show":
        report = generate_summary_report(days=args.days)
        print(report)

    elif args.command == "history":
        history = get_stats_history(days=args.days, limit=args.limit)
        if not history:
            print("No statistics history available.")
            return

        print(f"\nStatistics History (showing {len(history)} entries):\n")
        for i, stats in enumerate(history, 1):
            timestamp = stats.get("timestamp", "unknown")
            files = stats.get("files", {})
            missions = stats.get("missions", {})

            print(f"{i}. {timestamp}")
            print(f"   Files: {files.get('total_files', 0)}, LOC: {files.get('total_loc', 0):,}")
            print(f"   Missions: {missions.get('total_missions', 0)} (success rate: {missions.get('success_rate', 0):.1f}%)")
            print()


if __name__ == "__main__":
    main()
