"""
Tests for QA module functionality.

STAGE 10: Tests quality checks, gate evaluation, and pipeline execution.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))

import qa


@pytest.fixture
def temp_html_project(tmp_path):
    """Create a temporary project with HTML files for testing."""
    project = tmp_path / "test_project"
    project.mkdir()

    # Create a good HTML file
    (project / "index.html").write_text("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="Test website description">
    <title>Test Website</title>
</head>
<body>
    <h1>Welcome</h1>
    <img src="test.jpg" alt="Test image">
    <a href="/about">About</a>
    <button>Click me</button>
</body>
</html>
    """)

    # Create a problematic HTML file
    (project / "bad.html").write_text("""
<html>
<head></head>
<body>
    <img src="test.jpg">
    <img src="test2.jpg" alt="">
    <a href="#">Empty link</a>
    <a href="">Another empty link</a>
    <button></button>
</body>
</html>
    """)

    # Create a JS file with console.logs
    (project / "app.js").write_text("""
console.log('Debug message 1');
const data = getData();
console.log('Debug message 2', data);
console.log('Debug message 3');
    """)

    return project


def test_qa_config_from_dict():
    """Test creating QAConfig from dictionary."""
    config_dict = {
        "enabled": True,
        "require_title": True,
        "max_empty_links": 5,
    }

    config = qa.QAConfig.from_dict(config_dict)

    assert config.enabled is True
    assert config.require_title is True
    assert config.max_empty_links == 5
    # Defaults should still be set
    assert config.require_meta_description is True


def test_check_html_structure_good(temp_html_project):
    """Test HTML structure checking on a good file."""
    metrics = qa.check_html_structure(temp_html_project)

    assert metrics.has_title is True
    assert metrics.title_text == "Test Website"
    assert metrics.has_meta_description is True
    assert "Test website description" in metrics.meta_description
    assert metrics.has_lang is True
    assert metrics.lang_value == "en"
    assert metrics.h1_count == 1
    assert metrics.num_empty_links == 0
    assert metrics.num_duplicate_ids == 0


def test_check_html_structure_problems(temp_html_project):
    """Test HTML structure checking on a problematic file."""
    # Rename bad.html to index.html to test it
    index = temp_html_project / "index.html"
    bad = temp_html_project / "bad.html"
    index.unlink()
    bad.rename(index)

    metrics = qa.check_html_structure(temp_html_project)

    assert metrics.has_title is False
    assert metrics.has_meta_description is False
    assert metrics.has_lang is False
    assert metrics.h1_count == 0
    assert metrics.num_empty_links == 2  # Two empty links


def test_check_accessibility(temp_html_project):
    """Test accessibility checking."""
    metrics = qa.check_accessibility(temp_html_project)

    # index.html has 1 image with alt
    # bad.html has 1 image without alt, 1 with empty alt
    assert metrics.total_images == 3
    assert metrics.images_missing_alt == 1
    assert metrics.images_empty_alt == 1

    # index.html has 1 button with text
    # bad.html has 1 button without text
    assert metrics.total_buttons == 2
    assert metrics.buttons_missing_text == 1


def test_check_static_quality(temp_html_project):
    """Test static code quality checking."""
    metrics = qa.check_static_quality(temp_html_project)

    assert metrics.total_files > 0
    assert metrics.console_log_count == 3  # 3 console.log calls in app.js
    assert len(metrics.files_with_console_log) == 1


def test_evaluate_quality_gates_passed():
    """Test quality gate evaluation - all checks pass."""
    checks = qa.QACheckResult()
    checks.html = qa.HTMLMetrics(
        has_title=True,
        has_meta_description=True,
        has_lang=True,
        h1_count=1,
    )
    checks.accessibility = qa.AccessibilityMetrics(
        total_images=5,
        images_missing_alt=0,
    )
    checks.static = qa.StaticMetrics()

    config = qa.QAConfig()

    status, issues = qa.evaluate_quality_gates(checks, config)

    assert status == "passed"
    assert len(issues) == 0


def test_evaluate_quality_gates_warning():
    """Test quality gate evaluation - warnings."""
    checks = qa.QACheckResult()
    checks.html = qa.HTMLMetrics(
        has_title=True,
        has_meta_description=True,
        has_lang=False,  # Warning: missing lang
        h1_count=0,  # Warning: no h1
        num_empty_links=5,
    )
    checks.accessibility = qa.AccessibilityMetrics(
        total_images=5,
        images_missing_alt=0,
        images_empty_alt=2,  # Warning: empty alt
    )

    config = qa.QAConfig()

    status, issues = qa.evaluate_quality_gates(checks, config)

    assert status == "warning"
    assert len(issues) > 0
    assert any(issue.severity == "warning" for issue in issues)


def test_evaluate_quality_gates_failed():
    """Test quality gate evaluation - failures."""
    checks = qa.QACheckResult()
    checks.html = qa.HTMLMetrics(
        has_title=False,  # Error: missing title
        has_meta_description=False,  # Error: missing description
    )
    checks.accessibility = qa.AccessibilityMetrics(
        total_images=5,
        images_missing_alt=3,  # Error: images missing alt
    )

    config = qa.QAConfig(
        require_title=True,
        require_meta_description=True,
        max_images_missing_alt=0,
    )

    status, issues = qa.evaluate_quality_gates(checks, config)

    assert status == "failed"
    assert len(issues) > 0
    assert any(issue.severity == "error" for issue in issues)


def test_generate_summary_passed():
    """Test summary generation for passed status."""
    summary = qa.generate_summary("passed", [])

    assert "passed" in summary.lower()
    assert "✓" in summary


def test_generate_summary_with_issues():
    """Test summary generation with issues."""
    issues = [
        qa.QAIssue("html", "error", "Missing title"),
        qa.QAIssue("accessibility", "warning", "Images missing alt"),
    ]

    summary = qa.generate_summary("failed", issues)

    assert "error" in summary.lower()
    assert "1" in summary  # 1 error


def test_run_qa_for_project(temp_html_project):
    """Test complete QA pipeline execution."""
    config = qa.QAConfig(
        require_title=True,
        require_meta_description=True,
        max_images_missing_alt=0,
    )

    report = qa.run_qa_for_project(temp_html_project, config)

    # Should have warning or failure due to bad.html
    assert report.status in ["warning", "failed"]
    assert report.summary is not None
    assert report.checks is not None
    assert len(report.issues) > 0
    assert report.timestamp is not None


def test_qa_report_to_dict(temp_html_project):
    """Test QA report serialization to dict."""
    config = qa.QAConfig()
    report = qa.run_qa_for_project(temp_html_project, config)

    report_dict = report.to_dict()

    assert "status" in report_dict
    assert "summary" in report_dict
    assert "checks" in report_dict
    assert "issues" in report_dict
    assert isinstance(report_dict["issues"], list)


def test_qa_issue_dataclass():
    """Test QAIssue dataclass creation."""
    issue = qa.QAIssue(
        category="html",
        severity="error",
        message="Missing title tag",
        file="index.html",
        line=1,
    )

    assert issue.category == "html"
    assert issue.severity == "error"
    assert issue.message == "Missing title tag"
    assert issue.file == "index.html"
    assert issue.line == 1
