# STAGE 10: Automated Quality Assurance Pipeline

**Status**: ✅ Implemented

**Purpose**: Automatically verify the quality of generated projects through configurable checks and quality gates, with integrated reporting in the web dashboard.

---

## Overview

Stage 10 adds a comprehensive QA (Quality Assurance) pipeline that automatically checks generated projects for:

- **HTML Structure & SEO**: Title tags, meta descriptions, heading structure, valid markup
- **Accessibility**: Image alt attributes, interactive element labels, semantic HTML
- **Static Code Quality**: File sizes, console.log usage, code patterns
- **Optional Smoke Tests**: Configurable test command execution

The QA system provides:
- **Configurable quality gates** with pass/warning/fail status
- **Detailed issue reporting** with severity levels
- **Web dashboard integration** for easy access to QA results
- **On-demand re-checks** without re-running the entire project

---

## Quick Start

### 1. Enable QA in Configuration

QA is enabled by default. Configure thresholds in `agent/project_config.json`:

```json
{
  "qa": {
    "enabled": true,
    "require_title": true,
    "require_meta_description": true,
    "max_images_missing_alt": 0,
    "max_empty_links": 10
  }
}
```

### 2. Run a Project

QA checks run automatically after successful project completion:

```bash
python -m agent.webapp.app
# Start a job from the web dashboard
# QA results appear automatically on job completion
```

### 3. View QA Results

**In Web Dashboard:**
- **Jobs List**: QA status badge for each job
- **Job Detail**: Full QA section with status, summary, and issues
- **On-Demand**: Click "Re-run QA" button to re-check

---

## Architecture

### Core Components

1. **`agent/qa.py`** - QA engine with all check functions
2. **`agent/runner.py`** - Integration with orchestrator pipeline
3. **`agent/webapp/app.py`** - Web API endpoints for QA
4. **Templates** - UI components for displaying QA results

### Data Models

#### `QAConfig`
Configuration for QA checks and thresholds:
```python
@dataclass
class QAConfig:
    enabled: bool = True
    require_title: bool = True
    require_meta_description: bool = True
    max_images_missing_alt: int = 0
    max_empty_links: int = 10
    max_console_logs: int = 5
    # ... more settings
```

#### `QAReport`
Complete QA results with evaluation:
```python
@dataclass
class QAReport:
    status: str  # "passed", "warning", "failed", "error"
    summary: str  # Human-readable summary
    checks: QACheckResult  # Raw metrics
    issues: List[QAIssue]  # List of found issues
```

#### `QAIssue`
Individual quality issue:
```python
@dataclass
class QAIssue:
    category: str  # "html", "accessibility", "static", "tests"
    severity: str  # "error", "warning", "info"
    message: str
    file: Optional[str]
    line: Optional[int]
```

---

## Quality Checks

### 1. HTML Structure & SEO

**Checks performed on main HTML file (index.html):**

- ✓ **Title tag present and non-empty**
  - Error if missing and `require_title=true`
  - Warning if empty

- ✓ **Meta description present and non-empty**
  - Error if missing and `require_meta_description=true`
  - Warning if empty

- ✓ **HTML lang attribute**
  - Warning if missing and `require_lang_attribute=true`

- ✓ **H1 tag present**
  - Warning if missing and `require_h1=true`

- ✓ **Empty links (href="#" or href="")**
  - Warning if count exceeds `max_empty_links`

- ✓ **Duplicate ID attributes**
  - Error if any duplicates found and `max_duplicate_ids=0`

**Example Issue:**
```
Category: html
Severity: error
Message: Missing <title> tag
```

### 2. Accessibility

**Checks performed on all HTML files:**

- ✓ **Images with missing alt attributes**
  - Error if count exceeds `max_images_missing_alt`
  - Checks all `<img>` tags

- ✓ **Images with empty alt attributes**
  - Warning (decorative images should use alt="")

- ✓ **Buttons without text content**
  - Warning for accessibility

- ✓ **Link counts**
  - Informational metric tracking

**Example Issue:**
```
Category: accessibility
Severity: error
Message: Images missing alt attribute: 3 (max: 0)
```

### 3. Static Code Quality

**Checks performed on code files (.html, .css, .js, .ts):**

- ✓ **Large files (>5000 lines)**
  - Warning if count exceeds `max_large_files`
  - Can be disabled with `allow_large_files=true`

- ✓ **console.log usage in JavaScript**
  - Warning if count exceeds `max_console_logs`
  - Helps catch debug code in production

- ✓ **File and line counts**
  - Informational metrics

**Example Issue:**
```
Category: static
Severity: warning
Message: Too many console.log statements: 12 (max: 5)
Details: app.js (8), utils.js (4)
```

### 4. Smoke Tests (Optional)

**Run custom test commands:**

Configure a test command to run:
```json
{
  "qa": {
    "require_smoke_tests_pass": false,
    "smoke_test_command": "npm test"
  }
}
```

**Features:**
- Executes provided command in project directory
- 60-second timeout
- Parses pytest/jest output for pass/fail counts
- Error if tests fail and `require_smoke_tests_pass=true`

**Example Issue:**
```
Category: tests
Severity: error
Message: Smoke tests failed: 2/10
```

---

## Quality Gates

### Status Computation

QA status is computed based on severity of issues found:

| Status | Condition |
|--------|-----------|
| `passed` | No errors, no warnings |
| `warning` | No errors, but warnings present |
| `failed` | One or more errors found |
| `error` | QA pipeline execution failed |

### Severity Levels

- **Error**: Critical issue that causes `failed` status
  - Missing required HTML tags
  - Accessibility violations (when threshold is 0)
  - Duplicate IDs
  - Failed smoke tests (when required)

- **Warning**: Non-critical issue that causes `warning` status
  - Empty meta tags
  - Missing lang attribute
  - Too many empty links
  - Too many console.log statements
  - Large files

- **Info**: Informational only, doesn't affect status

### Configuration Examples

#### Strict Mode (Production)
```json
{
  "qa": {
    "enabled": true,
    "require_title": true,
    "require_meta_description": true,
    "require_lang_attribute": true,
    "require_h1": true,
    "max_empty_links": 0,
    "max_images_missing_alt": 0,
    "max_duplicate_ids": 0,
    "max_console_logs": 0,
    "allow_large_files": false,
    "require_smoke_tests_pass": true,
    "smoke_test_command": "npm test"
  }
}
```

#### Lenient Mode (Development)
```json
{
  "qa": {
    "enabled": true,
    "require_title": true,
    "require_meta_description": false,
    "max_empty_links": 20,
    "max_images_missing_alt": 5,
    "max_console_logs": 50,
    "allow_large_files": true,
    "require_smoke_tests_pass": false
  }
}
```

---

## Web Dashboard Integration

### Jobs List Page

**QA Status Column** added to jobs table:

| Job ID | Project | Mode | Status | **QA** | Created | Actions |
|--------|---------|------|--------|--------|---------|---------|
| abc123 | my_site | 3loop | completed | **✓ passed** | 2024-01-15 | View |
| def456 | blog | 3loop | completed | **⚠ warning** | 2024-01-14 | View |
| ghi789 | landing | 2loop | completed | **✗ failed** | 2024-01-13 | View |

**Status badges:**
- Green "passed" - All checks passed
- Yellow "warning" - Warnings present
- Red "failed" - Errors found
- Gray "-" - QA not run

**Tooltips:** Hover over badge to see summary

### Job Detail Page

**QA Section** displays full results:

```
✓ Quality Assurance

Status: ⚠ Warning
[Re-run QA Button]

Passed with 3 warnings: Images with empty alt, Too many empty links, Missing lang attribute

Issues Found:
┌─────────────────────────────────────────────────────────┐
│ Accessibility (warning): Images with empty alt          │
│ attribute: 2                                            │
├─────────────────────────────────────────────────────────┤
│ HTML (warning): Too many empty links: 12 (max: 10)     │
├─────────────────────────────────────────────────────────┤
│ HTML (warning): Missing lang attribute on <html> tag   │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Visual status badge with icon
- "Re-run QA" button for on-demand checks
- Issue list with severity color-coding
- First 10 issues shown (with count of additional issues)

**If QA not run:**
```
✓ Quality Assurance

QA checks have not been run for this job.
[Run QA Checks Button]
```

---

## API Endpoints

### POST `/api/jobs/{job_id}/qa`

Run QA checks on a job's project.

**Request:**
```http
POST /api/jobs/abc123/qa
```

**Response:**
```json
{
  "status": "warning",
  "summary": "Passed with 2 warnings",
  "checks": {
    "html": {
      "has_title": true,
      "has_meta_description": true,
      "h1_count": 1,
      "num_empty_links": 3
    },
    "accessibility": {
      "total_images": 5,
      "images_missing_alt": 0
    },
    "static": {
      "total_files": 8,
      "console_log_count": 2
    }
  },
  "issues": [
    {
      "category": "html",
      "severity": "warning",
      "message": "Too many empty links: 3"
    }
  ]
}
```

**Behavior:**
- Runs QA on job's project directory
- Updates job's QA fields
- Returns complete QA report

### GET `/api/jobs/{job_id}/qa`

Get existing QA report for a job.

**Request:**
```http
GET /api/jobs/abc123/qa
```

**Response:** Same as POST endpoint, or:
```json
{
  "status": null,
  "summary": "QA not run for this job"
}
```

---

## Programmatic Usage

### Run QA from Python

```python
from pathlib import Path
from qa import QAConfig, run_qa_for_project

# Configure QA
config = QAConfig(
    require_title=True,
    max_images_missing_alt=0
)

# Run checks
project_path = Path("sites/my_project")
report = run_qa_for_project(project_path, config)

# Check status
if report.status == "passed":
    print("✓ All checks passed")
elif report.status == "warning":
    print(f"⚠ {report.summary}")
else:
    print(f"✗ {report.summary}")
    for issue in report.issues:
        if issue.severity == "error":
            print(f"  - {issue.message}")
```

### Integrate with Runner

```python
from runner import run_project, run_qa_only

# Run project with auto QA
config = {
    "mode": "3loop",
    "project_subdir": "my_site",
    "task": "Build a landing page",
    "qa": {"enabled": True}
}

result = run_project(config)
print(f"QA Status: {result.qa_status}")

# Or run QA separately
qa_report = run_qa_only(Path("sites/my_site"))
print(qa_report.summary)
```

---

## Configuration Reference

### Complete QA Configuration

```json
{
  "qa": {
    // Enable/disable QA pipeline
    "enabled": true,

    // HTML/SEO requirements
    "require_title": true,
    "require_meta_description": true,
    "require_lang_attribute": true,
    "require_h1": true,

    // Quality thresholds
    "max_empty_links": 10,
    "max_images_missing_alt": 0,
    "max_duplicate_ids": 0,
    "max_console_logs": 5,

    // File size limits
    "allow_large_files": true,
    "max_large_files": 5,
    "large_file_threshold": 5000,  // lines

    // Smoke tests
    "require_smoke_tests_pass": false,
    "smoke_test_command": null  // e.g., "npm test" or "pytest"
  }
}
```

### Per-Job Configuration

Override defaults via web UI or API:

```python
config = {
    "project_subdir": "my_site",
    "qa": {
        "enabled": True,
        "max_images_missing_alt": 2  # Override default
    }
}
```

---

## Testing

### Run QA Tests

```bash
cd agent/
pytest tests_stage10/ -v
```

### Test Coverage

- ✓ QA check functions (HTML, accessibility, static)
- ✓ Quality gate evaluation
- ✓ Config loading and defaults
- ✓ Report generation and serialization
- ✓ Integration with runner
- ✓ Error handling

### Manual Testing

1. Create a test project with quality issues
2. Run through orchestrator
3. Check QA results in web dashboard
4. Test "Re-run QA" button
5. Modify QA config and re-run
6. Verify different status levels

---

## Troubleshooting

### QA Status Shows "error"

**Cause**: QA pipeline execution failed

**Solution**:
1. Check job logs for Python exceptions
2. Verify project directory exists
3. Check HTML files are valid (not corrupted)
4. Ensure QA config is valid JSON

### QA Not Running Automatically

**Cause**: QA disabled in configuration

**Solution**:
1. Check `project_config.json`: `qa.enabled` should be `true`
2. Verify job completed successfully (QA only runs on `COMPLETED` status)
3. Check job config includes `qa` section

### Too Many False Positives

**Cause**: QA gates too strict

**Solution**:
1. Adjust thresholds in `project_config.json`
2. Increase `max_empty_links`, `max_console_logs`, etc.
3. Set `allow_large_files=true` for larger projects
4. Disable specific checks by setting `require_*=false`

### Smoke Tests Not Running

**Cause**: Missing test command or tests disabled

**Solution**:
1. Set `smoke_test_command` in QA config
2. Ensure command works when run manually in project directory
3. Check 60-second timeout isn't exceeded

---

## Future Enhancements

Potential improvements for future stages:

1. **Advanced Linting**
   - ESLint integration for JavaScript
   - HTMLHint for HTML validation
   - Stylelint for CSS

2. **Performance Checks**
   - Page load time analysis
   - Bundle size limits
   - Lighthouse score integration

3. **Security Checks**
   - XSS vulnerability scanning
   - Dependency vulnerability checks
   - CSP header validation

4. **Visual Regression**
   - Screenshot comparison
   - Layout shift detection
   - Cross-browser rendering

5. **Custom Rules**
   - Plugin system for custom checks
   - Project-specific quality rules
   - Industry-specific compliance (WCAG, etc.)

---

## Summary

Stage 10 provides a complete automated QA pipeline that:

- ✅ Runs automatically after each successful build
- ✅ Provides configurable quality gates
- ✅ Integrates seamlessly with web dashboard
- ✅ Supports on-demand re-checks
- ✅ Generates detailed, actionable reports
- ✅ Helps ensure production-ready code quality

The QA system complements the orchestrator by providing objective quality metrics and catching common issues before deployment, improving the overall reliability of generated projects.

---

For questions or issues, see the main README or create an issue on GitHub.
