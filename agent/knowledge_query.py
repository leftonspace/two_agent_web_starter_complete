"""
PHASE 2.4: Knowledge Graph Query Interface

Convenience functions for querying the knowledge graph:
- Find related missions by domain
- Find files affected by a mission
- Generate evolution reports
- Query mission success rates by domain
- Find similar missions

Usage:
    >>> from agent import knowledge_query as kq
    >>> missions = kq.get_missions_by_domain("coding")
    >>> report = kq.generate_evolution_report(days=30)
    >>> similar = kq.find_similar_missions("build_landing_page")
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Local imports
try:
    from knowledge_graph import KnowledgeGraph
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Mission Queries
# ══════════════════════════════════════════════════════════════════════


def get_missions_by_domain(domain: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all missions for a specific domain.

    Args:
        domain: Domain to filter by (coding, finance, etc.)
        limit: Maximum results

    Returns:
        List of mission dicts
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()
    return kg.get_mission_history(domain=domain, limit=limit)


def get_successful_missions(domain: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all successful missions, optionally filtered by domain.

    Args:
        domain: Optional domain filter
        limit: Maximum results

    Returns:
        List of successful mission dicts
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()
    return kg.get_mission_history(status="success", domain=domain, limit=limit)


def get_failed_missions(domain: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all failed missions, optionally filtered by domain.

    Args:
        domain: Optional domain filter
        limit: Maximum results

    Returns:
        List of failed mission dicts
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()
    return kg.get_mission_history(status="failed", domain=domain, limit=limit)


def get_recent_missions(days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get missions from the last N days.

    Args:
        days: Number of days to look back
        limit: Maximum results

    Returns:
        List of mission dicts
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()
    all_missions = kg.get_mission_history(limit=limit)

    # Filter by date
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_str = cutoff.isoformat() + "Z"

    recent = [
        m for m in all_missions
        if m.get("created_at", "") >= cutoff_str
    ]

    return recent


def find_similar_missions(mission_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Find missions similar to the given mission.

    Similarity based on:
    - Same domain
    - Similar task keywords
    - Similar cost range

    Args:
        mission_id: Mission ID to find similar missions for
        limit: Maximum results

    Returns:
        List of similar mission dicts
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()

    # Get the target mission
    target_entity = kg.find_entity("mission", mission_id)
    if not target_entity:
        return []

    target_metadata = target_entity.get("metadata", {})
    target_domain = target_metadata.get("domain", "")
    target_task = target_metadata.get("task", "").lower()
    target_cost = target_metadata.get("cost_usd", 0.0)

    # Get all missions in same domain
    domain_missions = get_missions_by_domain(target_domain, limit=100)

    # Score by similarity
    scored_missions = []
    for mission in domain_missions:
        if mission["mission_id"] == mission_id:
            continue  # Skip self

        score = 0

        # Same domain: +10
        score += 10

        # Similar keywords in task
        mission_metadata = mission.get("metadata", {})
        mission_task = mission_metadata.get("task", "").lower()

        # Simple keyword matching
        target_words = set(target_task.split())
        mission_words = set(mission_task.split())
        common_words = target_words & mission_words

        # +1 point per common word
        score += len(common_words)

        # Similar cost range: +5 if within 50%
        mission_cost = mission.get("cost_usd", 0.0)
        if target_cost > 0 and mission_cost > 0:
            cost_ratio = min(mission_cost, target_cost) / max(mission_cost, target_cost)
            if cost_ratio >= 0.5:
                score += 5

        scored_missions.append((score, mission))

    # Sort by score descending
    scored_missions.sort(key=lambda x: x[0], reverse=True)

    # Return top N
    return [mission for score, mission in scored_missions[:limit]]


# ══════════════════════════════════════════════════════════════════════
# Domain Statistics
# ══════════════════════════════════════════════════════════════════════


def get_domain_success_rates() -> Dict[str, float]:
    """
    Get success rates for each domain.

    Returns:
        Dict mapping domain -> success rate percentage
    """
    if not KG_AVAILABLE:
        return {}

    kg = KnowledgeGraph()

    # Get all missions grouped by domain
    all_missions = kg.get_mission_history(limit=1000)

    domain_stats = {}

    for mission in all_missions:
        domain = mission.get("domain")
        if not domain:
            continue

        if domain not in domain_stats:
            domain_stats[domain] = {"total": 0, "successful": 0}

        domain_stats[domain]["total"] += 1
        if mission.get("status") == "success":
            domain_stats[domain]["successful"] += 1

    # Compute success rates
    success_rates = {}
    for domain, stats in domain_stats.items():
        total = stats["total"]
        successful = stats["successful"]
        success_rates[domain] = (successful / total * 100) if total > 0 else 0.0

    return success_rates


def get_domain_costs() -> Dict[str, Dict[str, float]]:
    """
    Get cost statistics for each domain.

    Returns:
        Dict mapping domain -> {total_cost, avg_cost, min_cost, max_cost}
    """
    if not KG_AVAILABLE:
        return {}

    kg = KnowledgeGraph()
    all_missions = kg.get_mission_history(limit=1000)

    domain_costs = {}

    for mission in all_missions:
        domain = mission.get("domain")
        cost = mission.get("cost_usd", 0.0)

        if not domain:
            continue

        if domain not in domain_costs:
            domain_costs[domain] = {"costs": []}

        domain_costs[domain]["costs"].append(cost)

    # Compute statistics
    stats = {}
    for domain, data in domain_costs.items():
        costs = data["costs"]
        stats[domain] = {
            "total_cost": sum(costs),
            "avg_cost": sum(costs) / len(costs) if costs else 0.0,
            "min_cost": min(costs) if costs else 0.0,
            "max_cost": max(costs) if costs else 0.0,
            "num_missions": len(costs),
        }

    return stats


# ══════════════════════════════════════════════════════════════════════
# Evolution Reports
# ══════════════════════════════════════════════════════════════════════


def generate_evolution_report(days: int = 30) -> str:
    """
    Generate a comprehensive evolution report.

    Args:
        days: Number of days to analyze

    Returns:
        Multi-line report string
    """
    if not KG_AVAILABLE:
        return "Knowledge graph not available."

    kg = KnowledgeGraph()
    stats = kg.get_stats()

    recent_missions = get_recent_missions(days=days, limit=1000)

    # Success rates by domain
    success_rates = get_domain_success_rates()
    domain_costs = get_domain_costs()

    report_lines = [
        f"KNOWLEDGE GRAPH EVOLUTION REPORT (Last {days} days)",
        "=" * 70,
        "",
        "Overall Statistics:",
        f"  Total entities: {stats['entities']['total']}",
        f"  Total relationships: {stats['relationships']['total']}",
        f"  Total missions: {stats['missions']['total']}",
        f"  Successful missions: {stats['missions']['successful']}",
        f"  Failed missions: {stats['missions']['failed']}",
        f"  Overall success rate: {(stats['missions']['successful'] / stats['missions']['total'] * 100) if stats['missions']['total'] > 0 else 0:.1f}%",
        f"  Total cost: ${stats['missions']['total_cost_usd']:.2f}",
        "",
        f"Recent Activity (Last {days} days):",
        f"  Recent missions: {len(recent_missions)}",
        "",
    ]

    # Success rates by domain
    if success_rates:
        report_lines.extend([
            "Success Rates by Domain:",
        ])
        for domain, rate in sorted(success_rates.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {domain}: {rate:.1f}%")
        report_lines.append("")

    # Cost statistics by domain
    if domain_costs:
        report_lines.extend([
            "Cost Statistics by Domain:",
        ])
        for domain, cost_stats in sorted(domain_costs.items(), key=lambda x: x[1]["total_cost"], reverse=True):
            report_lines.append(
                f"  {domain}: ${cost_stats['total_cost']:.2f} total, "
                f"${cost_stats['avg_cost']:.4f} avg ({cost_stats['num_missions']} missions)"
            )
        report_lines.append("")

    # Entity breakdown
    if stats['entities']['by_type']:
        report_lines.extend([
            "Entity Breakdown:",
        ])
        for entity_type, count in sorted(stats['entities']['by_type'].items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {entity_type}: {count}")
        report_lines.append("")

    # Relationship breakdown
    if stats['relationships']['by_type']:
        report_lines.extend([
            "Relationship Breakdown:",
        ])
        for rel_type, count in sorted(stats['relationships']['by_type'].items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {rel_type}: {count}")
        report_lines.append("")

    report_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    return "\n".join(report_lines)


# ══════════════════════════════════════════════════════════════════════
# File Queries
# ══════════════════════════════════════════════════════════════════════


def find_files_by_mission(mission_id: str) -> List[str]:
    """
    Find all files created or modified by a mission.

    Args:
        mission_id: Mission ID

    Returns:
        List of file paths
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()

    # Find mission entity
    mission_entity = kg.find_entity("mission", mission_id)
    if not mission_entity:
        return []

    mission_entity_id = mission_entity["id"]

    # Find files related to this mission
    related = kg.find_related(mission_entity_id, relationship_type="created", direction="outgoing")
    related += kg.find_related(mission_entity_id, relationship_type="modified", direction="outgoing")

    # Extract file paths
    files = []
    for entity, relationship in related:
        if entity.get("type") == "file":
            files.append(entity.get("name", ""))

    return list(set(files))  # Deduplicate


def find_missions_affecting_file(file_path: str) -> List[str]:
    """
    Find all missions that created or modified a file.

    Args:
        file_path: File path to query

    Returns:
        List of mission IDs
    """
    if not KG_AVAILABLE:
        return []

    kg = KnowledgeGraph()

    # Find file entity
    file_entity = kg.find_entity("file", file_path)
    if not file_entity:
        return []

    file_entity_id = file_entity["id"]

    # Find missions that created/modified this file
    related = kg.find_related(file_entity_id, relationship_type="created", direction="incoming")
    related += kg.find_related(file_entity_id, relationship_type="modified", direction="incoming")

    # Extract mission IDs
    missions = []
    for entity, relationship in related:
        if entity.get("type") == "mission":
            missions.append(entity.get("name", ""))

    return list(set(missions))  # Deduplicate


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """CLI entry point for knowledge queries."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Knowledge Graph Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate evolution report")
    report_parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )

    # Domain command
    domain_parser = subparsers.add_parser("domain", help="Show domain statistics")
    domain_parser.add_argument(
        "domain_name",
        type=str,
        help="Domain name (coding, finance, etc.)",
    )

    # Similar command
    similar_parser = subparsers.add_parser("similar", help="Find similar missions")
    similar_parser.add_argument(
        "mission_id",
        type=str,
        help="Mission ID to find similar missions for",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "report":
        report = generate_evolution_report(days=args.days)
        print(report)

    elif args.command == "domain":
        missions = get_missions_by_domain(args.domain_name, limit=20)
        if not missions:
            print(f"No missions found for domain: {args.domain_name}")
            return

        print(f"\nMissions for domain '{args.domain_name}' (showing {len(missions)}):\n")
        for i, mission in enumerate(missions, 1):
            print(f"{i}. {mission['mission_id']}")
            print(f"   Status: {mission['status']}, Cost: ${mission['cost_usd']:.4f}")
            print(f"   Created: {mission['created_at']}")
            print()

    elif args.command == "similar":
        similar = find_similar_missions(args.mission_id, limit=5)
        if not similar:
            print(f"No similar missions found for: {args.mission_id}")
            return

        print(f"\nSimilar missions to '{args.mission_id}':\n")
        for i, mission in enumerate(similar, 1):
            print(f"{i}. {mission['mission_id']}")
            print(f"   Status: {mission['status']}, Domain: {mission.get('domain', 'unknown')}")
            print(f"   Cost: ${mission['cost_usd']:.4f}")
            print()


if __name__ == "__main__":
    main()
