# test_repo_router.py
"""
Unit tests for repo_router module (Stage 4.3).
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Import the module we're testing
import repo_router


def test_get_repos_from_config_multi_repo():
    """Test multi-repo configuration parsing."""
    config = {
        "repos": [
            {"name": "backend", "path": "/path/to/backend"},
            {"name": "frontend", "path": "/path/to/frontend"},
        ]
    }

    repos = repo_router.get_repos_from_config(config)

    assert len(repos) == 2
    assert repos[0]["name"] == "backend"
    assert repos[0]["path"] == "/path/to/backend"
    assert repos[1]["name"] == "frontend"
    assert repos[1]["path"] == "/path/to/frontend"


def test_get_repos_from_config_single_repo_project_folder():
    """Test single-repo configuration with project_folder."""
    config = {
        "project_folder": "/path/to/project",
    }

    repos = repo_router.get_repos_from_config(config)

    assert len(repos) == 1
    assert repos[0]["name"] == "default"
    assert repos[0]["path"] == "/path/to/project"


def test_get_repos_from_config_single_repo_project_subdir():
    """Test single-repo configuration with project_subdir (legacy)."""
    config = {
        "project_subdir": "my_project",
    }

    repos = repo_router.get_repos_from_config(config)

    assert len(repos) == 1
    assert repos[0]["name"] == "default"
    assert repos[0]["path"] == "../sites/my_project"


def test_get_repos_from_config_empty():
    """Test configuration with no repos."""
    config = {}

    repos = repo_router.get_repos_from_config(config)

    assert len(repos) == 0


def test_resolve_repo_path_explicit_repo_name():
    """Test repo path resolution with explicit repo_name."""
    config = {
        "repos": [
            {"name": "backend", "path": "/path/to/backend"},
            {"name": "frontend", "path": "/path/to/frontend"},
        ]
    }

    path = repo_router.resolve_repo_path(config, repo_name="frontend")

    assert "frontend" in str(path)


def test_resolve_repo_path_stage_repo_name():
    """Test repo path resolution from stage metadata."""
    config = {
        "repos": [
            {"name": "backend", "path": "/path/to/backend"},
            {"name": "frontend", "path": "/path/to/frontend"},
        ]
    }

    stage = {
        "repo_name": "backend",
        "name": "API Implementation",
    }

    path = repo_router.resolve_repo_path(config, stage=stage)

    assert "backend" in str(path)


def test_resolve_repo_path_keyword_routing_backend():
    """Test keyword-based routing for backend."""
    config = {
        "repos": [
            {"name": "backend", "path": "/path/to/backend"},
            {"name": "frontend", "path": "/path/to/frontend"},
        ]
    }

    stage = {
        "name": "API Integration",
        "description": "Implement backend services",
        "categories": ["api", "database"],
    }

    path = repo_router.resolve_repo_path(config, stage=stage)

    assert "backend" in str(path)


def test_resolve_repo_path_keyword_routing_frontend():
    """Test keyword-based routing for frontend."""
    config = {
        "repos": [
            {"name": "backend-service", "path": "/path/to/backend"},
            {"name": "frontend-app", "path": "/path/to/frontend"},
        ]
    }

    stage = {
        "name": "UI Components",
        "description": "Build web page layout",
        "categories": ["visual", "layout"],
    }

    path = repo_router.resolve_repo_path(config, stage=stage)

    assert "frontend" in str(path)


def test_resolve_repo_path_default_fallback():
    """Test that first repo is used as fallback."""
    config = {
        "repos": [
            {"name": "default-repo", "path": "/path/to/default"},
            {"name": "other-repo", "path": "/path/to/other"},
        ]
    }

    stage = {
        "name": "Ambiguous Task",
        "description": "No clear routing hints",
    }

    path = repo_router.resolve_repo_path(config, stage=stage)

    assert "default" in str(path)


def test_get_all_repo_paths():
    """Test getting all repo paths."""
    config = {
        "repos": [
            {"name": "backend", "path": "/path/to/backend"},
            {"name": "frontend", "path": "/path/to/frontend"},
            {"name": "shared", "path": "/path/to/shared"},
        ]
    }

    paths = repo_router.get_all_repo_paths(config)

    assert len(paths) == 3
    assert all(isinstance(p, Path) for p in paths)


def test_infer_repo_from_stage_backend_keywords():
    """Test backend inference from keywords."""
    stage = {
        "name": "Database Migration",
        "description": "Update API endpoints",
        "categories": ["api", "service"],
    }

    repos = [
        {"name": "backend", "path": "/backend"},
        {"name": "frontend", "path": "/frontend"},
    ]

    result = repo_router._infer_repo_from_stage(stage, repos)

    assert result is not None
    assert result["name"] == "backend"


def test_infer_repo_from_stage_frontend_keywords():
    """Test frontend inference from keywords."""
    stage = {
        "name": "UI Redesign",
        "description": "Update web components",
        "categories": ["layout", "visual"],
    }

    repos = [
        {"name": "backend", "path": "/backend"},
        {"name": "ui", "path": "/ui"},
    ]

    result = repo_router._infer_repo_from_stage(stage, repos)

    assert result is not None
    assert result["name"] == "ui"


def test_infer_repo_from_stage_no_match():
    """Test that ambiguous stages return None."""
    stage = {
        "name": "General Task",
        "description": "Do something",
        "categories": [],
    }

    repos = [
        {"name": "backend", "path": "/backend"},
        {"name": "frontend", "path": "/frontend"},
    ]

    result = repo_router._infer_repo_from_stage(stage, repos)

    # Should return None for ambiguous cases
    assert result is None
