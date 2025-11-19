"""
PHASE 1.3: Mission Runner CLI

This module provides the command-line interface for running missions.
Missions are defined in JSON/YAML files and executed via the orchestrator.

Usage:
    python -m agent.mission_runner run missions/my_mission.json
    python -m agent.mission_runner list
    python -m agent.mission_runner status <mission_id>

Mission File Format (JSON):
    {
        "mission_id": "unique_mission_id",
        "task": "Task description",
        "project_path": "sites/my_project",  // optional, defaults to project_subdir
        "mode": "3loop",  // optional, defaults to config
        "max_rounds": 3,  // optional
        "cost_cap_usd": 5.0,  // optional
        "tags": ["prototype", "urgent"],  // optional
        "domain": "coding"  // optional, auto-detected if not provided
    }
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Local imports
from agent import config, cost_tracker, domain_router, paths

# PHASE 2.3: Import knowledge graph for mission tracking
try:
    from agent import knowledge_graph, project_stats
    KG_AVAILABLE = True
except ImportError:
    KG_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Mission Loading
# ══════════════════════════════════════════════════════════════════════


def load_mission_file(mission_file_path: Path) -> Dict[str, Any]:
    """
    Load a mission definition from JSON or YAML file.

    Args:
        mission_file_path: Path to mission file

    Returns:
        Mission configuration dictionary

    Raises:
        FileNotFoundError: If mission file doesn't exist
        ValueError: If mission file is invalid
    """
    if not mission_file_path.exists():
        raise FileNotFoundError(f"Mission file not found: {mission_file_path}")

    # Determine format from extension
    suffix = mission_file_path.suffix.lower()

    if suffix == ".json":
        with mission_file_path.open("r", encoding="utf-8") as f:
            mission_data = json.load(f)
    elif suffix in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "YAML support requires PyYAML: pip install pyyaml"
            ) from None
        with mission_file_path.open("r", encoding="utf-8") as f:
            mission_data = yaml.safe_load(f)
    else:
        raise ValueError(
            f"Unsupported mission file format: {suffix}. Use .json or .yaml"
        )

    # Validate required fields
    if "mission_id" not in mission_data:
        raise ValueError("Mission file must contain 'mission_id' field")
    if "task" not in mission_data:
        raise ValueError("Mission file must contain 'task' field")

    return mission_data


def validate_mission(mission_data: Dict[str, Any]) -> None:
    """
    Validate mission configuration.

    Args:
        mission_data: Mission configuration dictionary

    Raises:
        ValueError: If mission configuration is invalid
    """
    # Check mission_id format (alphanumeric + underscores/hyphens)
    mission_id = mission_data["mission_id"]
    if not mission_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError(
            f"Invalid mission_id '{mission_id}': must be alphanumeric with underscores/hyphens"
        )

    # Validate mode if provided
    if "mode" in mission_data:
        valid_modes = ["2loop", "3loop", "autopilot"]
        if mission_data["mode"] not in valid_modes:
            raise ValueError(
                f"Invalid mode '{mission_data['mode']}': must be one of {valid_modes}"
            )

    # Validate max_rounds if provided
    if "max_rounds" in mission_data:
        if not isinstance(mission_data["max_rounds"], int) or mission_data["max_rounds"] < 1:
            raise ValueError("max_rounds must be a positive integer")

    # Validate cost_cap_usd if provided
    if "cost_cap_usd" in mission_data:
        try:
            cost_cap = float(mission_data["cost_cap_usd"])
            if cost_cap < 0:
                raise ValueError("cost_cap_usd must be >= 0")
        except (TypeError, ValueError) as e:
            raise ValueError(f"cost_cap_usd must be a valid number: {e}") from e

    # Validate domain if provided
    if "domain" in mission_data:
        valid_domains = [d.value for d in domain_router.Domain]
        if mission_data["domain"] not in valid_domains:
            raise ValueError(
                f"Invalid domain '{mission_data['domain']}': must be one of {valid_domains}"
            )


# ══════════════════════════════════════════════════════════════════════
# Mission Execution
# ══════════════════════════════════════════════════════════════════════


def run_mission(mission_file_path: Path) -> Dict[str, Any]:
    """
    Run a mission from a mission file.

    Args:
        mission_file_path: Path to mission JSON/YAML file

    Returns:
        Mission result dictionary with outcome, costs, and metadata

    Raises:
        FileNotFoundError: If mission file doesn't exist
        ValueError: If mission configuration is invalid
    """
    print(f"\n{'='*70}")
    print(f"🚀 MISSION RUNNER - Starting mission from {mission_file_path.name}")
    print(f"{'='*70}\n")

    # Load and validate mission
    mission_data = load_mission_file(mission_file_path)
    validate_mission(mission_data)

    mission_id = mission_data["mission_id"]
    task = mission_data["task"]

    print(f"📋 Mission ID: {mission_id}")
    print(f"📝 Task: {task}")

    # Classify domain (use provided domain or auto-detect)
    if "domain" in mission_data:
        domain = domain_router.Domain(mission_data["domain"])
        print(f"🏷️  Domain: {domain.value} (specified in mission file)")
    else:
        domain = domain_router.classify_task(task)
        print(f"🏷️  Domain: {domain.value} (auto-detected)")

    # Get domain-specific configuration
    domain_info = domain_router.get_domain_info(task)
    print(f"🛠️  Tools: {len(domain_info['tools'])} domain-specific tools available")

    # Initialize cost tracking
    cost_tracker.reset()
    print(f"💰 Cost tracking initialized")

    # Get base config
    cfg = config.get_config()

    # Override config with mission-specific settings
    mission_config = cfg.to_dict()
    if "mode" in mission_data:
        mission_config["mode"] = mission_data["mode"]
    if "max_rounds" in mission_data:
        mission_config["max_rounds"] = mission_data["max_rounds"]
    if "cost_cap_usd" in mission_data:
        mission_config["max_cost_usd"] = mission_data["cost_cap_usd"]
    if "project_path" in mission_data:
        mission_config["project_subdir"] = mission_data["project_path"]

    # Update task
    mission_config["task"] = task

    print(f"⚙️  Mode: {mission_config['mode']}")
    print(f"🔄 Max rounds: {mission_config['max_rounds']}")
    if mission_config.get("max_cost_usd", 0) > 0:
        print(f"💵 Cost cap: ${mission_config['max_cost_usd']:.2f} USD")
    else:
        print(f"💵 Cost cap: None (unlimited)")

    print(f"\n{'─'*70}")
    print(f"▶️  Starting orchestrator execution...")
    print(f"{'─'*70}\n")

    # Execute mission
    start_time = time.time()
    start_timestamp = datetime.utcnow().isoformat()

    try:
        # Import orchestrator here to avoid circular imports
        from agent import orchestrator

        result = orchestrator.run(mission_config)
        success = result.get("status") == "success"
        error_message = None

    except Exception as e:
        print(f"\n❌ Mission execution failed with error: {e}")
        success = False
        error_message = str(e)
        result = {"status": "error", "error": error_message}

    end_time = time.time()
    end_timestamp = datetime.utcnow().isoformat()
    duration_seconds = end_time - start_time

    # Get cost summary
    cost_summary = cost_tracker.get_summary()

    print(f"\n{'─'*70}")
    print(f"✅ Mission execution completed")
    print(f"{'─'*70}\n")

    print(f"📊 Results:")
    print(f"   Status: {'SUCCESS ✓' if success else 'FAILED ✗'}")
    print(f"   Duration: {duration_seconds:.1f}s")
    print(f"   Total cost: ${cost_summary['total_usd']:.4f} USD")
    print(f"   LLM calls: {cost_summary['num_calls']}")

    if cost_summary['num_calls'] > 0:
        print(f"\n💰 Cost breakdown by role:")
        for role, stats in cost_summary['by_role'].items():
            print(f"   {role}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}")

        print(f"\n🤖 Cost breakdown by model:")
        for model, stats in cost_summary['by_model'].items():
            print(f"   {model}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}")

    # Build mission result
    mission_result = {
        "mission_id": mission_id,
        "task": task,
        "domain": domain.value,
        "status": "success" if success else "failed",
        "start_time": start_timestamp,
        "end_time": end_timestamp,
        "duration_seconds": duration_seconds,
        "config": {
            "mode": mission_config["mode"],
            "max_rounds": mission_config["max_rounds"],
            "cost_cap_usd": mission_config.get("max_cost_usd", 0),
        },
        "cost_summary": cost_summary,
        "tags": mission_data.get("tags", []),
    }

    if error_message:
        mission_result["error"] = error_message

    if "rounds_completed" in result:
        mission_result["rounds_completed"] = result["rounds_completed"]

    # Write mission log
    log_path = write_mission_log(mission_result)
    print(f"\n📁 Mission log written to: {log_path}")

    # PHASE 2.3: Log mission to knowledge graph
    if KG_AVAILABLE:
        try:
            kg = knowledge_graph.KnowledgeGraph()

            # Log mission to history
            kg.log_mission(
                mission_id=mission_id,
                status="success" if success else "failed",
                domain=domain.value,
                cost_usd=cost_summary.get("total_usd", 0.0),
                iterations=mission_result.get("rounds_completed", mission_config["max_rounds"]),
                duration_seconds=duration_seconds,
                files_modified=0,  # TODO: Track from orchestrator result
                metadata={
                    "task": task,
                    "config": mission_result["config"],
                    "tags": mission_data.get("tags", []),
                    "error": error_message if error_message else None,
                }
            )

            # Create mission entity
            mission_entity_id = kg.add_entity(
                "mission",
                mission_id,
                {
                    "domain": domain.value,
                    "task": task,
                    "status": "success" if success else "failed",
                    "cost_usd": cost_summary.get("total_usd", 0.0),
                }
            )

            # Create domain entity and relate to mission
            domain_entity_id = kg.add_entity("domain", domain.value, {})
            kg.add_relationship(
                mission_entity_id,
                domain_entity_id,
                "has_domain",
                {"task": task}
            )

            print(f"📊 Mission logged to knowledge graph")

            # Collect and save project stats
            stats = project_stats.collect_stats()
            project_stats.save_stats(stats)
            print(f"📈 Project statistics updated")

        except Exception as e:
            print(f"⚠️  Warning: Failed to log to knowledge graph: {e}")

    print(f"\n{'='*70}")
    print(f"{'✅ MISSION COMPLETED SUCCESSFULLY' if success else '❌ MISSION FAILED'}")
    print(f"{'='*70}\n")

    return mission_result


def write_mission_log(mission_result: Dict[str, Any]) -> Path:
    """
    Write mission execution log to missions/logs/<mission_id>.json

    Args:
        mission_result: Mission result dictionary

    Returns:
        Path to written log file
    """
    # Ensure logs directory exists
    logs_dir = paths.get_mission_logs_dir()
    paths.ensure_dir(logs_dir)

    # Write log file
    mission_id = mission_result["mission_id"]
    log_path = logs_dir / f"{mission_id}.json"

    with log_path.open("w", encoding="utf-8") as f:
        json.dump(mission_result, f, indent=2, default=str)

    return log_path


# ══════════════════════════════════════════════════════════════════════
# Mission Management Commands
# ══════════════════════════════════════════════════════════════════════


def list_missions() -> None:
    """List all available mission files in missions/ directory."""
    missions_dir = paths.get_missions_dir()

    if not missions_dir.exists():
        print("No missions directory found. Run `ensure_all_dirs()` first.")
        return

    # Find all mission files
    mission_files = sorted(missions_dir.glob("*.json")) + sorted(missions_dir.glob("*.yaml"))
    mission_files = [f for f in mission_files if f.is_file()]

    if not mission_files:
        print("No mission files found in missions/ directory.")
        print(f"Create a mission file like: {missions_dir}/my_mission.json")
        return

    print(f"\n📂 Available missions in {missions_dir}:\n")

    for mission_file in mission_files:
        try:
            mission_data = load_mission_file(mission_file)
            mission_id = mission_data.get("mission_id", "unknown")
            task = mission_data.get("task", "No task description")
            domain = mission_data.get("domain", "auto-detect")

            # Check if log exists
            log_path = paths.get_mission_logs_dir() / f"{mission_id}.json"
            status = "✓ completed" if log_path.exists() else "○ not run"

            print(f"  {status} {mission_file.name}")
            print(f"      ID: {mission_id}")
            print(f"      Domain: {domain}")
            print(f"      Task: {task[:80]}{'...' if len(task) > 80 else ''}")
            print()

        except Exception as e:
            print(f"  ⚠️  {mission_file.name} (invalid: {e})")
            print()


def show_mission_status(mission_id: str) -> None:
    """
    Show status and details of a completed mission.

    Args:
        mission_id: Mission identifier
    """
    log_path = paths.get_mission_logs_dir() / f"{mission_id}.json"

    if not log_path.exists():
        print(f"❌ No log found for mission '{mission_id}'")
        print(f"   Expected: {log_path}")
        return

    with log_path.open("r", encoding="utf-8") as f:
        mission_result = json.load(f)

    print(f"\n{'='*70}")
    print(f"📊 MISSION STATUS: {mission_id}")
    print(f"{'='*70}\n")

    print(f"Task: {mission_result['task']}\n")
    print(f"Domain: {mission_result['domain']}")
    print(f"Status: {mission_result['status'].upper()}")
    print(f"Start time: {mission_result['start_time']}")
    print(f"End time: {mission_result['end_time']}")
    print(f"Duration: {mission_result['duration_seconds']:.1f}s")

    if mission_result.get("tags"):
        print(f"Tags: {', '.join(mission_result['tags'])}")

    print(f"\n⚙️  Configuration:")
    print(f"   Mode: {mission_result['config']['mode']}")
    print(f"   Max rounds: {mission_result['config']['max_rounds']}")
    if mission_result.get("rounds_completed"):
        print(f"   Rounds completed: {mission_result['rounds_completed']}")
    print(f"   Cost cap: ${mission_result['config']['cost_cap_usd']:.2f}")

    cost = mission_result["cost_summary"]
    print(f"\n💰 Cost Summary:")
    print(f"   Total: ${cost['total_usd']:.4f} USD")
    print(f"   LLM calls: {cost['num_calls']}")

    if cost.get("by_role"):
        print(f"\n   By role:")
        for role, stats in cost["by_role"].items():
            print(f"      {role}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}")

    if cost.get("by_model"):
        print(f"\n   By model:")
        for model, stats in cost["by_model"].items():
            print(f"      {model}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}")

    if mission_result.get("error"):
        print(f"\n❌ Error: {mission_result['error']}")

    print(f"\n{'='*70}\n")


# ══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Mission Runner CLI - Execute multi-agent orchestrator missions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a mission
  python -m agent.mission_runner run missions/my_mission.json

  # List all missions
  python -m agent.mission_runner list

  # Show mission status
  python -m agent.mission_runner status my_mission_id
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a mission from a file")
    run_parser.add_argument(
        "mission_file",
        type=str,
        help="Path to mission JSON or YAML file",
    )

    # List command
    subparsers.add_parser("list", help="List all available missions")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show mission status")
    status_parser.add_argument(
        "mission_id",
        type=str,
        help="Mission ID to show status for",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Ensure directory structure exists
    paths.ensure_all_dirs()

    # Execute command
    if args.command == "run":
        mission_file_path = Path(args.mission_file)
        try:
            result = run_mission(mission_file_path)
            sys.exit(0 if result["status"] == "success" else 1)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    elif args.command == "list":
        list_missions()

    elif args.command == "status":
        show_mission_status(args.mission_id)


if __name__ == "__main__":
    main()
