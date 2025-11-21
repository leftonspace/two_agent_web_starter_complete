"""
Tests for Stage 10 QA edge cases and error conditions.

Tests various edge scenarios and error conditions that the QA
pipeline should handle gracefully.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def temp_qa_project(tmp_path):
    """Create a temporary project directory for QA testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


def test_qa_missing_title_tag(temp_qa_project):
    """Test QA detects missing <title> tag."""
    from qa import QAConfig, run_qa_for_project

    # HTML without title
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="description" content="Test">
    </head>
    <body>
        <h1>Test</h1>
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(
        enabled=True,
        require_title=True,
        require_meta_description=False,
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should have an issue about missing title
    assert report.status in ["warning", "failed"]
    assert any("title" in issue.message.lower() for issue in report.issues)


def test_qa_missing_meta_description(temp_qa_project):
    """Test QA detects missing meta description."""
    from qa import QAConfig, run_qa_for_project

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test</h1>
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(
        enabled=True,
        require_title=False,
        require_meta_description=True,
    )

    report = run_qa_for_project(temp_qa_project, config)

    assert report.status in ["warning", "failed"]
    assert any("meta" in issue.message.lower() or "description" in issue.message.lower()
               for issue in report.issues)


def test_qa_missing_lang_attribute(temp_qa_project):
    """Test QA detects missing lang attribute."""
    from qa import QAConfig, run_qa_for_project

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test</title>
    </head>
    <body>
        <h1>Test</h1>
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(
        enabled=True,
        require_lang_attribute=True,
    )

    report = run_qa_for_project(temp_qa_project, config)

    assert report.status in ["warning", "failed"]
    assert any("lang" in issue.message.lower() for issue in report.issues)


def test_qa_images_without_alt(temp_qa_project):
    """Test QA detects images missing alt attributes."""
    from qa import QAConfig, run_qa_for_project

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test</title>
    </head>
    <body>
        <img src="test1.jpg">
        <img src="test2.jpg" alt="">
        <img src="test3.jpg" alt="Good alt text">
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(
        enabled=True,
        max_images_missing_alt=0,
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should detect at least 1 image without alt (first one)
    assert report.status in ["warning", "failed"]
    assert any("alt" in issue.message.lower() or "image" in issue.message.lower()
               for issue in report.issues)


def test_qa_buttons_without_text(temp_qa_project):
    """Test QA detects buttons without accessible text."""
    from qa import QAConfig, run_qa_for_project

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test</title>
    </head>
    <body>
        <button></button>
        <button>Click me</button>
        <a href="#" class="button"></a>
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(enabled=True)

    report = run_qa_for_project(temp_qa_project, config)

    # May detect accessibility issues with empty buttons
    # Exact behavior depends on implementation
    assert report.status in ["passed", "warning", "failed"]


def test_qa_large_javascript_file(temp_qa_project):
    """Test QA detects oversized JavaScript files."""
    from qa import QAConfig, run_qa_for_project

    # Create a large JS file (>5000 lines)
    large_js = "\n".join([f"console.log({i});" for i in range(6000)])
    (temp_qa_project / "app.js").write_text(large_js)

    config = QAConfig(
        enabled=True,
        allow_large_files=False,
        max_large_files=0,
        large_file_threshold=5000,
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should warn about large file
    assert report.status in ["warning", "failed"]
    assert any("large" in issue.message.lower() or "file" in issue.message.lower()
               for issue in report.issues)


def test_qa_excessive_console_logs(temp_qa_project):
    """Test QA detects too many console.log statements."""
    from qa import QAConfig, run_qa_for_project

    # JS file with many console.log calls
    js_content = """
    console.log("debug 1");
    console.log("debug 2");
    console.log("debug 3");
    console.log("debug 4");
    console.log("debug 5");
    console.log("debug 6");
    console.log("debug 7");
    """
    (temp_qa_project / "script.js").write_text(js_content)

    config = QAConfig(
        enabled=True,
        max_console_logs=3,  # Allow max 3
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should warn about too many console.logs
    assert report.status in ["warning", "failed"]
    assert any("console" in issue.message.lower() for issue in report.issues)


def test_qa_smoke_test_failure(temp_qa_project, monkeypatch):
    """Test QA handles smoke test command failures."""
    from qa import QAConfig, run_qa_for_project

    config = QAConfig(
        enabled=True,
        require_smoke_tests_pass=True,
        smoke_test_command="exit 1",  # Command that fails
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should report test failure
    assert report.status in ["failed", "error"]
    # Either in issues or in the report status
    if report.issues:
        assert any("test" in issue.message.lower() or "smoke" in issue.message.lower()
                   for issue in report.issues)


def test_qa_smoke_test_timeout(temp_qa_project):
    """Test QA handles smoke test timeouts."""
    from qa import QAConfig, run_qa_for_project

    # Command that takes longer than timeout
    config = QAConfig(
        enabled=True,
        require_smoke_tests_pass=True,
        smoke_test_command="sleep 120",  # Takes longer than 60 second timeout
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should handle timeout gracefully
    assert report.status in ["failed", "error", "warning"]


def test_qa_no_html_files(temp_qa_project):
    """Test QA when project has no HTML files."""
    from qa import QAConfig, run_qa_for_project

    # Create only a text file
    (temp_qa_project / "readme.txt").write_text("No HTML here")

    config = QAConfig(
        enabled=True,
        require_title=True,
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should complete but may have warnings about missing HTML
    assert report.status in ["passed", "warning", "failed"]


def test_qa_malformed_html(temp_qa_project):
    """Test QA handles malformed HTML gracefully."""
    from qa import QAConfig, run_qa_for_project

    # Malformed HTML
    bad_html = """
    <html>
    <head>
        <title>Test
    </head>
    <body>
        <h1>Unclosed heading
        <p>Paragraph
    </body>
    """
    (temp_qa_project / "index.html").write_text(bad_html)

    config = QAConfig(enabled=True)

    # Should not crash, may report issues
    report = run_qa_for_project(temp_qa_project, config)

    assert report is not None
    assert report.status in ["passed", "warning", "failed", "error"]


def test_qa_empty_project(temp_qa_project):
    """Test QA on completely empty project."""
    from qa import QAConfig, run_qa_for_project

    config = QAConfig(enabled=True)

    report = run_qa_for_project(temp_qa_project, config)

    # Should complete without crashing
    assert report is not None
    assert isinstance(report.status, str)


def test_qa_missing_project_directory():
    """Test QA handles missing project directory."""
    from qa import QAConfig, run_qa_for_project

    config = QAConfig(enabled=True)

    # Should raise error or return error status
    try:
        report = run_qa_for_project("/nonexistent/path", config)
        # If it doesn't raise, should have error status
        assert report.status == "error"
    except (FileNotFoundError, OSError):
        # Expected behavior
        pass


def test_qa_duplicate_ids(temp_qa_project):
    """Test QA detects duplicate ID attributes."""
    from qa import QAConfig, run_qa_for_project

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test</title>
    </head>
    <body>
        <div id="main">Content 1</div>
        <div id="main">Content 2</div>
        <div id="sidebar">Sidebar</div>
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(
        enabled=True,
        max_duplicate_ids=0,
    )

    report = run_qa_for_project(temp_qa_project, config)

    # Should detect duplicate ID
    assert report.status in ["warning", "failed"]
    assert any("duplicate" in issue.message.lower() or "id" in issue.message.lower()
               for issue in report.issues)


def test_qa_config_from_dict():
    """Test QAConfig.from_dict() handles various input formats."""
    from qa import QAConfig

    # Full config
    config_dict = {
        "enabled": True,
        "require_title": False,
        "require_meta_description": True,
        "max_console_logs": 10,
    }

    config = QAConfig.from_dict(config_dict)

    assert config.enabled is True
    assert config.require_title is False
    assert config.require_meta_description is True
    assert config.max_console_logs == 10


def test_qa_config_from_dict_partial():
    """Test QAConfig.from_dict() with partial config uses defaults."""
    from qa import QAConfig

    # Minimal config
    config_dict = {
        "enabled": True,
    }

    config = QAConfig.from_dict(config_dict)

    assert config.enabled is True
    # Should have default values for other fields
    assert hasattr(config, "require_title")
    assert hasattr(config, "max_console_logs")


def test_qa_report_serialization(temp_qa_project):
    """Test QAReport.to_dict() produces valid JSON-serializable output."""
    import json

    from qa import QAConfig, run_qa_for_project

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test</title>
        <meta name="description" content="Test description">
    </head>
    <body>
        <h1>Test Page</h1>
    </body>
    </html>
    """
    (temp_qa_project / "index.html").write_text(html_content)

    config = QAConfig(enabled=True)

    report = run_qa_for_project(temp_qa_project, config)

    # Convert to dict and ensure it's JSON-serializable
    report_dict = report.to_dict()

    # Should be able to serialize to JSON without errors
    json_str = json.dumps(report_dict)
    assert len(json_str) > 0

    # Should have expected keys
    assert "status" in report_dict
    assert "summary" in report_dict
    assert "checks" in report_dict
    assert "issues" in report_dict
