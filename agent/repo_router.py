# repo_router.py
"""
STAGE 4.3: Multi-Repo Orchestration & Routing

This module provides routing logic for multi-repo projects.

KEY FEATURES:
- Determine which repo(s) a stage should operate on
- Resolve repo paths from config (single-repo or multi-repo mode)
- Keyword-based heuristic routing for ambiguous cases
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

# Import paths module for consistent path resolution
try:
    import paths as paths_module
    PATHS_AVAILABLE = True
except ImportError:
    paths_module = None
    PATHS_AVAILABLE = False


def get_repos_from_config(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract repo configuration from project config.

    Supports two modes:
    1. Legacy single-repo: {"project_folder": "../sites/project"}
    2. Multi-repo: {"repos": [{"name": "backend", "path": "..."}, ...]}

    Args:
        config: Project configuration dict

    Returns:
        List of repo dicts with 'name' and 'path' keys
        If single-repo mode, returns [{"name": "default", "path": ...}]
    """
    # Check for multi-repo mode
    repos = config.get("repos", [])
    if repos and isinstance(repos, list) and len(repos) > 0:
        # Multi-repo mode
        result = []
        for repo in repos:
            if isinstance(repo, dict) and "name" in repo and "path" in repo:
                result.append({
                    "name": repo["name"],
                    "path": repo["path"],
                })
        return result

    # Legacy single-repo mode
    project_folder = config.get("project_folder")
    if project_folder:
        return [{"name": "default", "path": project_folder}]

    # Fallback to project_subdir (older format)
    project_subdir = config.get("project_subdir")
    if project_subdir:
        # Use paths module for consistent absolute path resolution
        if PATHS_AVAILABLE and paths_module:
            abs_path = paths_module.resolve_project_path(project_subdir)
            return [{"name": "default", "path": str(abs_path)}]
        else:
            # Fallback: construct absolute path from this file's location
            agent_dir = Path(__file__).resolve().parent
            root_dir = agent_dir.parent
            abs_path = root_dir / "sites" / project_subdir
            return [{"name": "default", "path": str(abs_path)}]

    # No repo config found
    return []


def resolve_repo_path(
    config: Dict[str, Any],
    stage: Optional[Dict[str, Any]] = None,
    repo_name: Optional[str] = None,
) -> Path:
    """
    Resolve the repository path for a given stage.

    Args:
        config: Project configuration dict
        stage: Optional stage dict (with metadata like categories, name, etc.)
        repo_name: Optional explicit repo name to use

    Returns:
        Path to the repository

    Logic:
    1. If repo_name is provided, use it
    2. If stage has a 'repo_name' field, use it
    3. Otherwise, use keyword-based heuristic routing
    4. Fall back to first repo (default)
    """
    repos = get_repos_from_config(config)

    if not repos:
        # No repos configured, use current directory as fallback
        return Path.cwd()

    # If explicit repo_name provided
    if repo_name:
        for repo in repos:
            if repo["name"] == repo_name:
                return Path(repo["path"]).resolve()
        # If not found, fall back to first repo
        return Path(repos[0]["path"]).resolve()

    # If stage has explicit repo_name
    if stage and isinstance(stage, dict):
        stage_repo = stage.get("repo_name")
        if stage_repo:
            for repo in repos:
                if repo["name"] == stage_repo:
                    return Path(repo["path"]).resolve()

        # Use keyword-based routing
        repo_hint = _infer_repo_from_stage(stage, repos)
        if repo_hint:
            return Path(repo_hint["path"]).resolve()

    # Default to first repo
    return Path(repos[0]["path"]).resolve()


def _infer_repo_from_stage(
    stage: Dict[str, Any],
    repos: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Infer which repo a stage belongs to based on keywords.

    Heuristics:
    - If stage name/description contains "API", "backend", "service" -> backend
    - If it contains "UI", "frontend", "web", "page" -> frontend
    - Otherwise -> None (use default)

    Args:
        stage: Stage dict with 'name' and optionally 'description'
        repos: List of repo dicts

    Returns:
        Repo dict if a match is found, None otherwise
    """
    if not stage:
        return None

    # Build searchable text from stage
    stage_name = stage.get("name", "").lower()
    stage_desc = stage.get("description", "").lower()
    stage_categories = stage.get("categories", [])

    # Convert categories to lowercase strings
    if isinstance(stage_categories, list):
        stage_categories = [str(c).lower() for c in stage_categories]
    else:
        stage_categories = []

    search_text = f"{stage_name} {stage_desc} {' '.join(stage_categories)}"

    # Backend keywords
    backend_keywords = ["api", "backend", "service", "server", "database", "db"]
    # Frontend keywords
    frontend_keywords = ["ui", "frontend", "web", "page", "component", "layout", "visual"]

    # Count keyword matches
    backend_score = sum(1 for kw in backend_keywords if kw in search_text)
    frontend_score = sum(1 for kw in frontend_keywords if kw in search_text)

    # Find matching repos
    backend_repo = None
    frontend_repo = None

    for repo in repos:
        repo_name = repo["name"].lower()
        if any(kw in repo_name for kw in ["backend", "api", "server"]):
            backend_repo = repo
        elif any(kw in repo_name for kw in ["frontend", "ui", "web", "client"]):
            frontend_repo = repo

    # Return best match
    if backend_score > frontend_score and backend_repo:
        return backend_repo
    elif frontend_score > backend_score and frontend_repo:
        return frontend_repo

    return None


def get_all_repo_paths(config: Dict[str, Any]) -> List[Path]:
    """
    Get all repository paths from config.

    Args:
        config: Project configuration dict

    Returns:
        List of Path objects for all repos
    """
    repos = get_repos_from_config(config)
    return [Path(repo["path"]).resolve() for repo in repos]
