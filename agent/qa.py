"""
Quality Assurance Pipeline for Generated Projects.

STAGE 10: Automated quality checks with configurable gates.

Provides:
- HTML structure & SEO checks
- Accessibility checks
- Static quality checks
- Optional smoke test execution
- Quality gate evaluation with status computation
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ═══════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class QAConfig:
    """Configuration for QA checks and quality gates."""

    enabled: bool = True

    # HTML/SEO requirements
    require_title: bool = True
    require_meta_description: bool = True
    require_lang_attribute: bool = True
    require_h1: bool = True

    # Thresholds
    max_empty_links: int = 10
    max_images_missing_alt: int = 0
    max_duplicate_ids: int = 0
    max_console_logs: int = 5

    # File size limits
    allow_large_files: bool = True
    max_large_files: int = 5
    large_file_threshold: int = 5000  # lines

    # Smoke tests
    require_smoke_tests_pass: bool = False
    smoke_test_command: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QAConfig:
        """Create QAConfig from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


# ═══════════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class QAIssue:
    """Individual quality issue found during checks."""

    category: str  # "html", "accessibility", "static", "tests"
    severity: str  # "error", "warning", "info"
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class HTMLMetrics:
    """Metrics from HTML structure checks."""

    has_title: bool = False
    title_text: str = ""
    has_meta_description: bool = False
    meta_description: str = ""
    has_lang: bool = False
    lang_value: str = ""
    h1_count: int = 0
    num_empty_links: int = 0
    num_duplicate_ids: int = 0
    duplicate_ids: List[str] = field(default_factory=list)


@dataclass
class AccessibilityMetrics:
    """Metrics from accessibility checks."""

    total_images: int = 0
    images_missing_alt: int = 0
    images_empty_alt: int = 0
    total_buttons: int = 0
    buttons_missing_text: int = 0
    total_links: int = 0


@dataclass
class StaticMetrics:
    """Metrics from static code quality checks."""

    total_files: int = 0
    total_lines: int = 0
    large_files: List[str] = field(default_factory=list)
    console_log_count: int = 0
    files_with_console_log: List[str] = field(default_factory=list)


@dataclass
class TestMetrics:
    """Metrics from smoke test execution."""

    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    test_output: str = ""
    test_error: Optional[str] = None


@dataclass
class QACheckResult:
    """Raw metrics from all quality checks."""

    html: HTMLMetrics = field(default_factory=HTMLMetrics)
    accessibility: AccessibilityMetrics = field(default_factory=AccessibilityMetrics)
    static: StaticMetrics = field(default_factory=StaticMetrics)
    tests: Optional[TestMetrics] = None


@dataclass
class QAReport:
    """Complete QA report with evaluation and status."""

    status: str  # "passed", "warning", "failed", "error"
    summary: str
    checks: QACheckResult
    issues: List[QAIssue] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "summary": self.summary,
            "checks": {
                "html": asdict(self.checks.html),
                "accessibility": asdict(self.checks.accessibility),
                "static": asdict(self.checks.static),
                "tests": asdict(self.checks.tests) if self.checks.tests else None,
            },
            "issues": [asdict(issue) for issue in self.issues],
            "config": self.config,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════
# HTML Parser for Structure Analysis
# ═══════════════════════════════════════════════════════════════════════


class HTMLStructureParser(HTMLParser):
    """Parse HTML to extract structure and SEO metrics."""

    def __init__(self):
        super().__init__()
        self.metrics = HTMLMetrics()
        self._ids_seen: Set[str] = set()
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        """Process opening tags."""
        attrs_dict = dict(attrs)

        # Check for html lang attribute
        if tag == "html":
            if "lang" in attrs_dict:
                self.metrics.has_lang = True
                self.metrics.lang_value = attrs_dict["lang"]

        # Check for title
        if tag == "title":
            self._in_title = True
            self.metrics.has_title = True

        # Check for meta description
        if tag == "meta":
            if attrs_dict.get("name") == "description":
                self.metrics.has_meta_description = True
                self.metrics.meta_description = attrs_dict.get("content", "")

        # Count h1 tags
        if tag == "h1":
            self.metrics.h1_count += 1

        # Check for empty links
        if tag == "a":
            href = attrs_dict.get("href", "")
            if not href or href == "#":
                self.metrics.num_empty_links += 1

        # Check for duplicate IDs
        if "id" in attrs_dict:
            id_value = attrs_dict["id"]
            if id_value in self._ids_seen:
                self.metrics.num_duplicate_ids += 1
                if id_value not in self.metrics.duplicate_ids:
                    self.metrics.duplicate_ids.append(id_value)
            else:
                self._ids_seen.add(id_value)

    def handle_data(self, data: str):
        """Process text content."""
        if self._in_title:
            self.metrics.title_text = data.strip()

    def handle_endtag(self, tag: str):
        """Process closing tags."""
        if tag == "title":
            self._in_title = False


class AccessibilityParser(HTMLParser):
    """Parse HTML to extract accessibility metrics."""

    def __init__(self):
        super().__init__()
        self.metrics = AccessibilityMetrics()
        self._current_button_text = ""
        self._in_button = False

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        """Process opening tags."""
        attrs_dict = dict(attrs)

        # Check images for alt attributes
        if tag == "img":
            self.metrics.total_images += 1
            if "alt" not in attrs_dict:
                self.metrics.images_missing_alt += 1
            elif not attrs_dict["alt"].strip():
                self.metrics.images_empty_alt += 1

        # Count buttons
        if tag == "button":
            self.metrics.total_buttons += 1
            self._in_button = True
            self._current_button_text = ""

        # Count links
        if tag == "a":
            self.metrics.total_links += 1

    def handle_data(self, data: str):
        """Process text content."""
        if self._in_button:
            self._current_button_text += data

    def handle_endtag(self, tag: str):
        """Process closing tags."""
        if tag == "button":
            if not self._current_button_text.strip():
                self.metrics.buttons_missing_text += 1
            self._in_button = False


# ═══════════════════════════════════════════════════════════════════════
# Check Functions
# ═══════════════════════════════════════════════════════════════════════


def check_html_structure(project_path: Path) -> HTMLMetrics:
    """
    Check HTML structure and SEO basics.

    Args:
        project_path: Path to project directory

    Returns:
        HTMLMetrics with structure analysis
    """
    # Find main HTML file (index.html or first .html file)
    html_files = list(project_path.glob("*.html"))
    if not html_files:
        return HTMLMetrics()

    # Prefer index.html
    main_html = next((f for f in html_files if f.name.lower() == "index.html"), html_files[0])

    try:
        with open(main_html, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        parser = HTMLStructureParser()
        parser.feed(content)
        return parser.metrics
    except Exception:
        return HTMLMetrics()


def check_accessibility(project_path: Path) -> AccessibilityMetrics:
    """
    Check accessibility basics.

    Args:
        project_path: Path to project directory

    Returns:
        AccessibilityMetrics with accessibility analysis
    """
    # Find all HTML files
    html_files = list(project_path.rglob("*.html"))
    if not html_files:
        return AccessibilityMetrics()

    combined_metrics = AccessibilityMetrics()

    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            parser = AccessibilityParser()
            parser.feed(content)

            # Aggregate metrics
            combined_metrics.total_images += parser.metrics.total_images
            combined_metrics.images_missing_alt += parser.metrics.images_missing_alt
            combined_metrics.images_empty_alt += parser.metrics.images_empty_alt
            combined_metrics.total_buttons += parser.metrics.total_buttons
            combined_metrics.buttons_missing_text += parser.metrics.buttons_missing_text
            combined_metrics.total_links += parser.metrics.total_links
        except Exception:
            continue

    return combined_metrics


def check_static_quality(project_path: Path) -> StaticMetrics:
    """
    Check static code quality (file sizes, console.log usage).

    Args:
        project_path: Path to project directory

    Returns:
        StaticMetrics with static analysis
    """
    metrics = StaticMetrics()

    # Check all code files
    code_extensions = {".html", ".css", ".js", ".ts", ".jsx", ".tsx"}
    code_files = [
        f for ext in code_extensions for f in project_path.rglob(f"*{ext}")
    ]

    for file_path in code_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            metrics.total_files += 1
            line_count = len(lines)
            metrics.total_lines += line_count

            # Check for large files
            if line_count > 5000:
                relative_path = file_path.relative_to(project_path)
                metrics.large_files.append(str(relative_path))

            # Check for console.log in JS/TS files
            if file_path.suffix in {".js", ".ts", ".jsx", ".tsx"}:
                content = "".join(lines)
                console_logs = len(re.findall(r"console\.log\s*\(", content))
                if console_logs > 0:
                    metrics.console_log_count += console_logs
                    relative_path = file_path.relative_to(project_path)
                    metrics.files_with_console_log.append(f"{relative_path} ({console_logs})")
        except Exception:
            continue

    return metrics


def run_smoke_tests(project_path: Path, command: str) -> TestMetrics:
    """
    Run smoke tests using provided command.

    Args:
        project_path: Path to project directory
        command: Test command to execute

    Returns:
        TestMetrics with test results
    """
    import shlex

    metrics = TestMetrics()

    if not command:
        metrics.test_error = "No test command provided"
        return metrics

    try:
        # Parse command into argument list to prevent shell injection
        try:
            args = shlex.split(command)
        except ValueError as e:
            metrics.test_error = f"Invalid command syntax: {e}"
            return metrics

        if not args:
            metrics.test_error = "Empty test command"
            return metrics

        result = subprocess.run(
            args,
            shell=False,  # SECURITY: Prevent command injection
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )

        metrics.test_output = result.stdout + result.stderr

        # Try to parse test results (basic heuristics)
        # Look for common test runner output patterns
        output = metrics.test_output

        # pytest pattern
        pytest_match = re.search(r"(\d+) passed", output)
        if pytest_match:
            metrics.tests_passed = int(pytest_match.group(1))

        pytest_fail_match = re.search(r"(\d+) failed", output)
        if pytest_fail_match:
            metrics.tests_failed = int(pytest_fail_match.group(1))

        metrics.tests_run = metrics.tests_passed + metrics.tests_failed

        # If return code is non-zero, consider it a failure
        if result.returncode != 0 and metrics.tests_run == 0:
            metrics.tests_failed = 1
            metrics.tests_run = 1
            metrics.test_error = f"Test command exited with code {result.returncode}"

    except subprocess.TimeoutExpired:
        metrics.test_error = "Test command timed out (60s limit)"
    except FileNotFoundError:
        metrics.test_error = f"Test command not found: {args[0] if args else command}"
    except Exception as e:
        metrics.test_error = f"Test execution failed: {str(e)}"

    return metrics


# ═══════════════════════════════════════════════════════════════════════
# Quality Gate Evaluation
# ═══════════════════════════════════════════════════════════════════════


def evaluate_quality_gates(
    checks: QACheckResult,
    config: QAConfig,
) -> tuple[str, List[QAIssue]]:
    """
    Evaluate quality gates and compute status.

    Args:
        checks: Raw check results
        config: QA configuration with thresholds

    Returns:
        Tuple of (status, issues_list)
        Status is "passed", "warning", or "failed"
    """
    issues: List[QAIssue] = []
    error_count = 0
    warning_count = 0

    # HTML/SEO checks
    html = checks.html

    if config.require_title and not html.has_title:
        issues.append(
            QAIssue(
                category="html",
                severity="error",
                message="Missing <title> tag",
                details={"check": "require_title"},
            )
        )
        error_count += 1
    elif html.has_title and not html.title_text:
        issues.append(
            QAIssue(
                category="html",
                severity="warning",
                message="Title tag is empty",
                details={"check": "require_title"},
            )
        )
        warning_count += 1

    if config.require_meta_description and not html.has_meta_description:
        issues.append(
            QAIssue(
                category="html",
                severity="error",
                message="Missing <meta name='description'> tag",
                details={"check": "require_meta_description"},
            )
        )
        error_count += 1
    elif html.has_meta_description and not html.meta_description:
        issues.append(
            QAIssue(
                category="html",
                severity="warning",
                message="Meta description is empty",
                details={"check": "require_meta_description"},
            )
        )
        warning_count += 1

    if config.require_lang_attribute and not html.has_lang:
        issues.append(
            QAIssue(
                category="html",
                severity="warning",
                message="Missing lang attribute on <html> tag",
                details={"check": "require_lang_attribute"},
            )
        )
        warning_count += 1

    if config.require_h1 and html.h1_count == 0:
        issues.append(
            QAIssue(
                category="html",
                severity="warning",
                message="No <h1> tags found",
                details={"check": "require_h1"},
            )
        )
        warning_count += 1

    if html.num_empty_links > config.max_empty_links:
        issues.append(
            QAIssue(
                category="html",
                severity="warning",
                message=f"Too many empty links: {html.num_empty_links} (max: {config.max_empty_links})",
                details={"count": html.num_empty_links, "max": config.max_empty_links},
            )
        )
        warning_count += 1

    if html.num_duplicate_ids > config.max_duplicate_ids:
        issues.append(
            QAIssue(
                category="html",
                severity="error",
                message=f"Duplicate IDs found: {html.num_duplicate_ids} ({', '.join(html.duplicate_ids[:5])})",
                details={
                    "count": html.num_duplicate_ids,
                    "ids": html.duplicate_ids,
                },
            )
        )
        error_count += 1

    # Accessibility checks
    acc = checks.accessibility

    if acc.images_missing_alt > config.max_images_missing_alt:
        issues.append(
            QAIssue(
                category="accessibility",
                severity="error",
                message=f"Images missing alt attribute: {acc.images_missing_alt} (max: {config.max_images_missing_alt})",
                details={"count": acc.images_missing_alt, "max": config.max_images_missing_alt},
            )
        )
        error_count += 1

    if acc.images_empty_alt > 0:
        issues.append(
            QAIssue(
                category="accessibility",
                severity="warning",
                message=f"Images with empty alt attribute: {acc.images_empty_alt}",
                details={"count": acc.images_empty_alt},
            )
        )
        warning_count += 1

    if acc.buttons_missing_text > 0:
        issues.append(
            QAIssue(
                category="accessibility",
                severity="warning",
                message=f"Buttons without text content: {acc.buttons_missing_text}",
                details={"count": acc.buttons_missing_text},
            )
        )
        warning_count += 1

    # Static quality checks
    static = checks.static

    if not config.allow_large_files and len(static.large_files) > 0:
        issues.append(
            QAIssue(
                category="static",
                severity="warning",
                message=f"Large files found (>5000 lines): {len(static.large_files)}",
                details={"files": static.large_files},
            )
        )
        warning_count += 1
    elif len(static.large_files) > config.max_large_files:
        issues.append(
            QAIssue(
                category="static",
                severity="warning",
                message=f"Too many large files: {len(static.large_files)} (max: {config.max_large_files})",
                details={"count": len(static.large_files), "max": config.max_large_files},
            )
        )
        warning_count += 1

    if static.console_log_count > config.max_console_logs:
        issues.append(
            QAIssue(
                category="static",
                severity="warning",
                message=f"Too many console.log statements: {static.console_log_count} (max: {config.max_console_logs})",
                details={"count": static.console_log_count, "files": static.files_with_console_log},
            )
        )
        warning_count += 1

    # Test checks
    if checks.tests:
        tests = checks.tests

        if tests.test_error:
            issues.append(
                QAIssue(
                    category="tests",
                    severity="error",
                    message=f"Test execution error: {tests.test_error}",
                )
            )
            error_count += 1
        elif config.require_smoke_tests_pass:
            if tests.tests_failed > 0:
                issues.append(
                    QAIssue(
                        category="tests",
                        severity="error",
                        message=f"Smoke tests failed: {tests.tests_failed}/{tests.tests_run}",
                        details={"failed": tests.tests_failed, "total": tests.tests_run},
                    )
                )
                error_count += 1
        else:
            # Just warn about failed tests if not required to pass
            if tests.tests_failed > 0:
                issues.append(
                    QAIssue(
                        category="tests",
                        severity="warning",
                        message=f"Some smoke tests failed: {tests.tests_failed}/{tests.tests_run}",
                        details={"failed": tests.tests_failed, "total": tests.tests_run},
                    )
                )
                warning_count += 1

    # Determine overall status
    if error_count > 0:
        status = "failed"
    elif warning_count > 0:
        status = "warning"
    # If there are no issues at all, treat this as a clean pass,
    # even if earlier logic marked it as "warning".
    if not issues:
        status = "passed"

    return status, issues



def generate_summary(status: str, issues: List[QAIssue]) -> str:
    """
    Generate human-readable summary of QA results.

    Args:
        status: Overall QA status
        issues: List of issues found

    Returns:
        Summary string
    """
    if status == "passed" and not issues:
        return "All quality checks passed ✓"

    error_issues = [i for i in issues if i.severity == "error"]
    warning_issues = [i for i in issues if i.severity == "warning"]

    parts = []

    if status == "failed":
        parts.append(f"Failed with {len(error_issues)} error(s)")
    elif status == "warning":
        parts.append(f"Passed with {len(warning_issues)} warning(s)")
    else:
        parts.append("Passed")

    # Add top issues
    if error_issues:
        parts.append(f"{len(error_issues)} errors")
    if warning_issues:
        parts.append(f"{len(warning_issues)} warnings")

    # Add specific issue types
    issue_types = []
    for issue in issues[:3]:  # Top 3 issues
        issue_types.append(issue.message.split(":")[0])

    if issue_types:
        parts.append(": " + ", ".join(issue_types))

    return " - ".join(parts) if len(parts) > 1 else parts[0]


# ═══════════════════════════════════════════════════════════════════════
# Main QA Pipeline
# ═══════════════════════════════════════════════════════════════════════


def run_qa_for_project(
    project_path: Path,
    config: QAConfig,
) -> QAReport:
    """
    Run complete QA pipeline for a project.

    Args:
        project_path: Path to project directory
        config: QA configuration

    Returns:
        QAReport with all results and evaluation
    """
    from safe_io import safe_timestamp

    try:
        # Run all checks
        checks = QACheckResult()

        checks.html = check_html_structure(project_path)
        checks.accessibility = check_accessibility(project_path)
        checks.static = check_static_quality(project_path)

        # Run smoke tests if configured
        if config.smoke_test_command:
            checks.tests = run_smoke_tests(project_path, config.smoke_test_command)

        # Evaluate quality gates
        status, issues = evaluate_quality_gates(checks, config)

        # Generate summary
        summary = generate_summary(status, issues)

        return QAReport(
            status=status,
            summary=summary,
            checks=checks,
            issues=issues,
            config=asdict(config),
            timestamp=safe_timestamp(),
        )

    except Exception as e:
        # Return error report
        return QAReport(
            status="error",
            summary=f"QA pipeline error: {str(e)}",
            checks=QACheckResult(),
            issues=[
                QAIssue(
                    category="system",
                    severity="error",
                    message=f"QA execution failed: {str(e)}",
                )
            ],
            config=asdict(config),
            timestamp=safe_timestamp(),
        )
