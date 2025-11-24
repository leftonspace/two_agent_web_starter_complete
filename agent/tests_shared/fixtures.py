"""
Shared test fixtures and utilities.

Provides reusable fixtures for creating temporary projects, run logs,
jobs, and other common test data structures.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytest


@pytest.fixture
def temp_agent_dir(tmp_path):
    """Create a temporary agent directory structure."""
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()

    sites_dir = tmp_path / "sites"
    sites_dir.mkdir()

    run_logs_dir = tmp_path / "run_logs"
    run_logs_dir.mkdir()

    return tmp_path


@pytest.fixture
def sample_project_dir(temp_agent_dir):
    """Create a sample project directory with basic HTML/CSS/JS files."""
    sites_dir = temp_agent_dir / "sites"
    project_dir = sites_dir / "sample_project"
    project_dir.mkdir()

    # Create HTML file
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="Sample project for testing">
    <title>Sample Project</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Welcome to Sample Project</h1>
    <p>This is a test project.</p>
    <img src="image.jpg" alt="Sample image">
    <a href="#section">Jump to section</a>
    <script src="script.js"></script>
</body>
</html>"""
    (project_dir / "index.html").write_text(html_content)

    # Create CSS file
    css_content = """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
}"""
    (project_dir / "style.css").write_text(css_content)

    # Create JavaScript file
    js_content = """console.log("Sample project loaded");

function init() {
    console.log("Initialized");
}

document.addEventListener("DOMContentLoaded", init);"""
    (project_dir / "script.js").write_text(js_content)

    return project_dir


@pytest.fixture
def sample_project_with_snapshots(sample_project_dir):
    """Create a sample project with iteration snapshots."""
    history_dir = sample_project_dir / ".history"
    history_dir.mkdir()

    # Create iteration 1
    iter1_dir = history_dir / "iteration_1"
    iter1_dir.mkdir()
    (iter1_dir / "index.html").write_text(
        "<html><body><h1>Version 1</h1></body></html>"
    )

    # Create iteration 2
    iter2_dir = history_dir / "iteration_2"
    iter2_dir.mkdir()
    (iter2_dir / "index.html").write_text(
        "<html><body><h1>Version 2</h1><p>Added content</p></body></html>"
    )

    # Create iteration 3
    iter3_dir = history_dir / "iteration_3"
    iter3_dir.mkdir()
    (iter3_dir / "index.html").write_text(
        "<html><body><h1>Version 3</h1><p>More content</p></body></html>"
    )
    (iter3_dir / "style.css").write_text("body { color: blue; }")

    return sample_project_dir


@pytest.fixture
def sample_run_summary():
    """Create a sample run summary dict."""
    return {
        "run_id": "run_sample_123",
        "started_at": "2024-01-01T10:00:00.000Z",
        "finished_at": "2024-01-01T10:05:00.000Z",
        "mode": "3loop",
        "project_dir": "/sites/sample_project",
        "task": "Build a sample website",
        "max_rounds": 3,
        "rounds_completed": 2,
        "final_status": "completed",
        "cost_summary": {
            "total_usd": 0.45,
            "total_input_tokens": 5000,
            "total_output_tokens": 2000,
            "by_model": {
                "gpt-4o": {
                    "input_tokens": 3000,
                    "output_tokens": 1200,
                    "cost_usd": 0.28,
                },
                "gpt-4o-mini": {
                    "input_tokens": 2000,
                    "output_tokens": 800,
                    "cost_usd": 0.17,
                },
            },
        },
        "config": {
            "use_visual_review": True,
            "use_git": True,
        },
        "iterations": [
            {
                "index": 1,
                "role": "manager",
                "status": "ok",
                "notes": "Planning phase completed",
                "timestamp": "2024-01-01T10:01:00.000Z",
            },
            {
                "index": 2,
                "role": "employee",
                "status": "ok",
                "notes": "Implementation completed",
                "timestamp": "2024-01-01T10:03:00.000Z",
            },
            {
                "index": 3,
                "role": "manager",
                "status": "approved",
                "notes": "Work approved",
                "timestamp": "2024-01-01T10:05:00.000Z",
                "safety_status": "passed",
            },
        ],
    }


@pytest.fixture
def sample_run_logs(temp_agent_dir, sample_run_summary):
    """Create sample run logs in the run_logs directory."""
    run_logs_dir = temp_agent_dir / "run_logs"

    # Create multiple run log entries
    for i in range(1, 4):
        run_id = f"run_sample_{i}"
        run_dir = run_logs_dir / run_id
        run_dir.mkdir()

        run_summary = sample_run_summary.copy()
        run_summary["run_id"] = run_id
        run_summary["started_at"] = f"2024-01-0{i}T10:00:00.000Z"
        run_summary["finished_at"] = f"2024-01-0{i}T10:05:00.000Z"

        (run_dir / "run_summary.json").write_text(json.dumps(run_summary, indent=2))

    return run_logs_dir


@pytest.fixture
def sample_job():
    """Create a sample Job object."""
    try:
        from jobs import Job
    except ImportError:
        pytest.skip("jobs module not available")

    return Job(
        id="job_sample_123",
        status="completed",
        config={
            "mode": "3loop",
            "project_subdir": "sample_project",
            "task": "Build a sample website",
            "max_rounds": 3,
        },
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        started_at=datetime.now().isoformat(),
        finished_at=datetime.now().isoformat(),
        logs_path="run_logs/job_sample_123/job.log",
        result_summary={
            "run_id": "run_123",
            "final_status": "completed",
        },
    )


@pytest.fixture
def sample_jobs_state(temp_agent_dir, sample_job):
    """Create a sample jobs_state.json file."""
    jobs_file = temp_agent_dir / "agent" / "jobs_state.json"
    jobs_file.parent.mkdir(exist_ok=True)

    jobs_data = {
        "jobs": [
            {
                "id": "job_sample_1",
                "status": "completed",
                "config": {"mode": "3loop", "project_subdir": "sample_project"},
                "created_at": "2024-01-01T10:00:00.000Z",
                "updated_at": "2024-01-01T10:05:00.000Z",
            },
            {
                "id": "job_sample_2",
                "status": "running",
                "config": {"mode": "2loop", "project_subdir": "another_project"},
                "created_at": "2024-01-02T11:00:00.000Z",
                "updated_at": "2024-01-02T11:02:00.000Z",
            },
        ]
    }

    jobs_file.write_text(json.dumps(jobs_data, indent=2))

    return jobs_file


@pytest.fixture
def sample_qa_config():
    """Create a sample QA configuration dict."""
    return {
        "enabled": True,
        "require_title": True,
        "require_meta_description": True,
        "require_lang_attribute": True,
        "require_h1": True,
        "max_empty_links": 10,
        "max_images_missing_alt": 0,
        "max_duplicate_ids": 0,
        "max_console_logs": 5,
        "allow_large_files": True,
        "max_large_files": 5,
        "large_file_threshold": 5000,
        "require_smoke_tests_pass": False,
        "smoke_test_command": None,
    }


@pytest.fixture
def sample_qa_report():
    """Create a sample QA report dict."""
    return {
        "status": "passed",
        "summary": "All quality checks passed. No issues found.",
        "checks": {
            "html": {
                "has_title": True,
                "title_text": "Sample Project",
                "has_meta_description": True,
                "meta_description": "Sample project for testing",
                "has_lang": True,
                "lang_value": "en",
                "h1_count": 1,
                "num_empty_links": 0,
                "num_duplicate_ids": 0,
                "duplicate_ids": [],
            },
            "accessibility": {
                "total_images": 1,
                "images_missing_alt": 0,
                "images_empty_alt": 0,
                "total_buttons": 0,
                "buttons_missing_text": 0,
                "total_links": 1,
            },
            "static": {
                "total_files": 3,
                "total_lines": 50,
                "large_files": 0,
                "console_log_count": 2,
                "files_with_console_log": ["script.js"],
            },
            "tests": None,
        },
        "issues": [],
        "config": sample_qa_config(),
        "timestamp": "2024-01-01T10:00:00.000Z",
    }


def create_minimal_html_project(
    path: Path,
    title: str = "Test Page",
    has_meta: bool = True,
    has_lang: bool = True,
    has_h1: bool = True,
) -> Path:
    """
    Helper function to create a minimal HTML project.

    Args:
        path: Directory path to create the project in
        title: Page title (omit <title> if None)
        has_meta: Include meta description
        has_lang: Include lang attribute on <html>
        has_h1: Include <h1> tag

    Returns:
        Path to the project directory
    """
    path.mkdir(parents=True, exist_ok=True)

    html_parts = ['<!DOCTYPE html>']

    if has_lang:
        html_parts.append('<html lang="en">')
    else:
        html_parts.append('<html>')

    html_parts.append('<head>')
    html_parts.append('    <meta charset="UTF-8">')

    if has_meta:
        html_parts.append('    <meta name="description" content="Test page description">')

    if title:
        html_parts.append(f'    <title>{title}</title>')

    html_parts.append('</head>')
    html_parts.append('<body>')

    if has_h1:
        html_parts.append('    <h1>Main Heading</h1>')

    html_parts.append('    <p>Test content</p>')
    html_parts.append('</body>')
    html_parts.append('</html>')

    html_content = '\n'.join(html_parts)
    (path / 'index.html').write_text(html_content)

    return path


def create_project_config(
    path: Path,
    config_data: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Helper function to create a project_config.json file.

    Args:
        path: Directory path to create the config in (usually agent/)
        config_data: Configuration data (uses defaults if None)

    Returns:
        Path to the created config file
    """
    if config_data is None:
        config_data = {
            "project_name": "Test Project",
            "project_subdir": "test_project",
            "mode": "3loop",
            "max_rounds": 3,
            "use_visual_review": True,
            "use_git": True,
        }

    path.mkdir(parents=True, exist_ok=True)
    config_file = path / "project_config.json"
    config_file.write_text(json.dumps(config_data, indent=2))

    return config_file
