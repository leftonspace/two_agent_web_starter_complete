"""
PHASE 0.2: Path Helpers Module

This module provides centralized path resolution for the multi-agent orchestrator.
All directories and file paths are resolved through these functions to ensure
platform independence and easy configuration.

Directory Structure:
    repo_root/
    ├── agent/              # Core orchestrator code
    ├── missions/           # Mission specifications (PHASE 1)
    ├── artifacts/          # Generated outputs per mission (PHASE 1)
    ├── data/               # Personal knowledge graph, stats (PHASE 2)
    ├── sites/              # Legacy output directory
    ├── dev/                # Developer tools
    └── docs/               # Documentation
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════════════════
# Root Directory Resolution
# ══════════════════════════════════════════════════════════════════════


def get_root() -> Path:
    """
    Get the repository root directory.

    The root is the parent directory of the agent/ folder.
    Can be overridden via AGENT_ROOT environment variable.

    Returns:
        Absolute path to repository root
    """
    # Check environment override
    env_root = os.getenv("AGENT_ROOT")
    if env_root:
        return Path(env_root).resolve()

    # Default: parent of agent/ directory
    return Path(__file__).resolve().parent.parent


def get_agent_dir() -> Path:
    """
    Get the agent/ directory containing core orchestrator code.

    Returns:
        Absolute path to agent/ directory
    """
    return Path(__file__).resolve().parent


# ══════════════════════════════════════════════════════════════════════
# Phase 1: Mission System Directories
# ══════════════════════════════════════════════════════════════════════


def get_missions_dir() -> Path:
    """
    Get the missions/ directory for mission specifications.

    Directory structure:
        missions/
        ├── <mission_id>.json     # Mission specifications
        └── logs/                 # Mission execution logs
            └── <mission_id>.json

    Returns:
        Absolute path to missions/ directory
    """
    root = get_root()
    return root / "missions"


def get_mission_logs_dir() -> Path:
    """
    Get the missions/logs/ directory for mission execution logs.

    Returns:
        Absolute path to missions/logs/ directory
    """
    return get_missions_dir() / "logs"


def get_artifacts_dir() -> Path:
    """
    Get the artifacts/ directory for generated outputs.

    Directory structure:
        artifacts/
        └── <mission_id>/
            ├── artifacts.jsonl       # Artifact log (plans, code, QA)
            ├── report.html           # Human-readable report
            └── files/                # Generated files
                └── ...

    Returns:
        Absolute path to artifacts/ directory
    """
    root = get_root()
    return root / "artifacts"


def get_mission_artifacts_dir(mission_id: str) -> Path:
    """
    Get the artifacts directory for a specific mission.

    Args:
        mission_id: Mission identifier

    Returns:
        Absolute path to artifacts/<mission_id>/ directory
    """
    return get_artifacts_dir() / mission_id


# ══════════════════════════════════════════════════════════════════════
# Phase 2: Knowledge Graph & Stats Directories
# ══════════════════════════════════════════════════════════════════════


def get_data_dir() -> Path:
    """
    Get the data/ directory for persistent data storage.

    Directory structure:
        data/
        ├── personal_graph.db     # SQLite knowledge graph
        ├── project_stats.json    # Project evolution metrics
        └── cache/                # Cached computations
            └── ...

    Returns:
        Absolute path to data/ directory
    """
    root = get_root()
    return root / "data"


def get_knowledge_graph_path() -> Path:
    """
    Get the path to the personal knowledge graph database.

    Returns:
        Absolute path to data/personal_graph.db
    """
    return get_data_dir() / "personal_graph.db"


def get_project_stats_path() -> Path:
    """
    Get the path to the project statistics file.

    Returns:
        Absolute path to data/project_stats.json
    """
    return get_data_dir() / "project_stats.json"


# ══════════════════════════════════════════════════════════════════════
# Legacy & Existing Directories
# ══════════════════════════════════════════════════════════════════════


def get_sites_dir() -> Path:
    """
    Get the sites/ directory (legacy output directory).

    This is the original output directory for website generation.
    New mission-based workflows use artifacts/ instead.

    Returns:
        Absolute path to sites/ directory
    """
    root = get_root()
    return root / "sites"


def get_dev_dir() -> Path:
    """
    Get the dev/ directory containing developer tools.

    Returns:
        Absolute path to dev/ directory
    """
    root = get_root()
    return root / "dev"


def get_docs_dir() -> Path:
    """
    Get the docs/ directory containing documentation.

    Returns:
        Absolute path to docs/ directory
    """
    root = get_root()
    return root / "docs"


# ══════════════════════════════════════════════════════════════════════
# Agent Subdirectories
# ══════════════════════════════════════════════════════════════════════


def get_run_logs_dir() -> Path:
    """
    Get the agent/run_logs/ directory for legacy run logs.

    Returns:
        Absolute path to agent/run_logs/ directory
    """
    return get_agent_dir() / "run_logs"


def get_run_logs_main_dir() -> Path:
    """
    Get the agent/run_logs_main/ directory for structured run logs.

    Returns:
        Absolute path to agent/run_logs_main/ directory
    """
    return get_agent_dir() / "run_logs_main"


def get_cost_logs_dir() -> Path:
    """
    Get the agent/cost_logs/ directory for cost tracking logs.

    Returns:
        Absolute path to agent/cost_logs/ directory
    """
    return get_agent_dir() / "cost_logs"


def get_tests_dir() -> Path:
    """
    Get the agent/tests/ directory for test files.

    Returns:
        Absolute path to agent/tests/ directory
    """
    return get_agent_dir() / "tests"


# ══════════════════════════════════════════════════════════════════════
# Utility Functions
# ══════════════════════════════════════════════════════════════════════


def ensure_dir(path: Path, parents: bool = True, exist_ok: bool = True) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
        parents: Create parent directories if needed
        exist_ok: Don't raise error if directory already exists

    Returns:
        The directory path (for chaining)

    Raises:
        OSError: If directory cannot be created
    """
    path.mkdir(parents=parents, exist_ok=exist_ok)
    return path


def ensure_all_dirs() -> None:
    """
    Ensure all standard directories exist.

    This should be called at system startup to initialize directory structure.
    Creates:
    - missions/ and missions/logs/
    - artifacts/
    - data/ and data/cache/
    - agent/run_logs/, agent/run_logs_main/, agent/cost_logs/
    """
    # Phase 1 directories
    ensure_dir(get_missions_dir())
    ensure_dir(get_mission_logs_dir())
    ensure_dir(get_artifacts_dir())

    # Phase 2 directories
    ensure_dir(get_data_dir())
    ensure_dir(get_data_dir() / "cache")

    # Agent subdirectories
    ensure_dir(get_run_logs_dir())
    ensure_dir(get_run_logs_main_dir())
    ensure_dir(get_cost_logs_dir())

    # Legacy directories (if needed)
    ensure_dir(get_sites_dir())


def get_relative_path(absolute_path: Path, base: Optional[Path] = None) -> Path:
    """
    Convert an absolute path to a relative path from base.

    Args:
        absolute_path: Absolute path to convert
        base: Base directory (defaults to repository root)

    Returns:
        Relative path from base

    Raises:
        ValueError: If path is not under base directory
    """
    if base is None:
        base = get_root()

    try:
        return absolute_path.relative_to(base)
    except ValueError as e:
        raise ValueError(
            f"Path {absolute_path} is not under base directory {base}"
        ) from e


def resolve_project_path(project_subdir: str, base: Optional[Path] = None) -> Path:
    """
    Resolve a project subdirectory path.

    Args:
        project_subdir: Project subdirectory name
        base: Base directory (defaults to sites/)

    Returns:
        Absolute path to project directory
    """
    if base is None:
        base = get_sites_dir()

    project_path = base / project_subdir
    ensure_dir(project_path)
    return project_path


# ══════════════════════════════════════════════════════════════════════
# Path Validation
# ══════════════════════════════════════════════════════════════════════


def is_under_root(path: Path) -> bool:
    """
    Check if a path is under the repository root.

    Args:
        path: Path to check

    Returns:
        True if path is under repository root
    """
    try:
        path.resolve().relative_to(get_root())
        return True
    except ValueError:
        return False


def is_safe_path(path: Path) -> bool:
    """
    Check if a path is safe to write to.

    Prevents writing outside repository root and to critical system paths.

    Args:
        path: Path to validate

    Returns:
        True if path is safe to write to
    """
    # Must be under repository root
    if not is_under_root(path):
        return False

    # Don't allow writes to agent/ directory (except logs)
    agent_dir = get_agent_dir()
    if path.resolve().is_relative_to(agent_dir):
        # Allow writes to log directories
        if path.is_relative_to(get_run_logs_dir()):
            return True
        if path.is_relative_to(get_run_logs_main_dir()):
            return True
        if path.is_relative_to(get_cost_logs_dir()):
            return True
        # Don't allow writes elsewhere in agent/
        return False

    # All other paths under root are safe
    return True
