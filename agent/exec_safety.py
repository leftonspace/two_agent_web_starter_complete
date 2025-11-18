# exec_safety.py
"""
Safety checks orchestrator for the multi-agent system.

Coordinates static analysis, dependency scanning, and runtime tests.

STAGE 5: Enhanced with status codes and safe I/O.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List

from exec_analysis import analyze_project
from exec_deps import scan_dependencies
from safe_io import safe_json_write, safe_mkdir, safe_timestamp
from status_codes import SAFETY_FAILED_STATUS, SAFETY_PASSED


def run_safety_checks(project_dir: str, task_description: str) -> Dict[str, Any]:
    """
    Run comprehensive safety checks on the project.

    Performs:
    - Static code analysis (syntax, code quality)
    - Dependency vulnerability scanning
    - Docker/runtime tests (stub for now)

    Args:
        project_dir: Path to the project directory to check
        task_description: Original task description (for context)

    Returns:
        {
            "static_issues": [...],
            "dependency_issues": [...],
            "docker_tests": {"status": "...", "details": "..."},
            "status": "passed" | "failed",
            "run_id": "<unique-id>",
            "timestamp": <unix-timestamp>,
            "timestamp_iso": "<ISO8601 string>",
            "task_description": "<original task>",
        }

    Safety check fails if:
    - Any static_issues with severity="error"
    - OR any dependency_issues with severity="critical"
    """
    run_id = _generate_run_id()
    timestamp = time.time()
    timestamp_iso = safe_timestamp()

    print("\n[Safety] Running safety checks...")
    print(f"[Safety] Run ID: {run_id}")
    print(f"[Safety] Project: {project_dir}")

    # 1. Static analysis
    print("[Safety] Running static analysis...")
    static_issues = analyze_project(project_dir)
    print(f"[Safety] Found {len(static_issues)} static analysis issues")

    # 2. Dependency scanning
    print("[Safety] Scanning dependencies...")
    dependency_issues = scan_dependencies(project_dir)
    print(f"[Safety] Found {len(dependency_issues)} dependency issues")

    # 3. Docker/runtime tests (stub for now)
    print("[Safety] Running docker/runtime tests (stub)...")
    docker_tests = _run_docker_tests_stub(project_dir)

    # Determine overall status
    status = _determine_status(static_issues, dependency_issues, docker_tests)
    print(f"[Safety] Overall status: {status}")

    # Build result structure
    result: Dict[str, Any] = {
        "static_issues": static_issues,
        "dependency_issues": dependency_issues,
        "docker_tests": docker_tests,
        "status": status,
        "run_id": run_id,
        "timestamp": timestamp,
        "timestamp_iso": timestamp_iso,
        "task_description": task_description,
    }

    # Log results
    _log_safety_run(result, project_dir)

    return result


def _generate_run_id() -> str:
    """Generate a short unique run ID."""
    import uuid

    return str(uuid.uuid4())[:8]


def _run_docker_tests_stub(project_dir: str) -> Dict[str, str]:
    """
    Stub for docker/runtime tests.

    In a full implementation, this would:
    - Build a Docker container
    - Run the application
    - Execute smoke tests
    - Check for runtime errors

    For now, returns a passing stub.
    """
    return {
        "status": SAFETY_PASSED,
        "details": "Docker tests not yet implemented (stub)",
    }


def _determine_status(
    static_issues: List[Dict[str, Any]],
    dependency_issues: List[Dict[str, Any]],
    docker_tests: Dict[str, str],
) -> str:
    """
    Determine overall safety status.

    STAGE 5: Uses status code constants.

    Fails if:
    - Any static issue with severity="error"
    - Any dependency issue with severity="critical"
    - Docker tests failed

    Args:
        static_issues: List of static analysis issues
        dependency_issues: List of dependency vulnerabilities
        docker_tests: Docker test results

    Returns:
        SAFETY_PASSED or SAFETY_FAILED_STATUS
    """
    # Check for error-level static issues
    for issue in static_issues:
        if issue.get("severity") == "error":
            return SAFETY_FAILED_STATUS

    # Check for critical dependency issues
    for issue in dependency_issues:
        if issue.get("severity") == "critical":
            return SAFETY_FAILED_STATUS

    # Check docker tests
    if docker_tests.get("status") in {SAFETY_FAILED_STATUS, "failed"}:
        return SAFETY_FAILED_STATUS

    return SAFETY_PASSED


def _log_safety_run(result: Dict[str, Any], project_dir: str) -> None:
    """
    Log safety check results to run_logs_exec/.

    Creates a directory structure:
        run_logs_exec/<run_id>/
            - result.json (full results)
            - summary.txt (human-readable summary)
    """
    # Get project root (parent of agent/)
    agent_dir = Path(__file__).resolve().parent
    project_root = agent_dir.parent

    # Create logs directory
    logs_dir = project_root / "run_logs_exec" / result["run_id"]
    if not safe_mkdir(logs_dir):
        print(f"[Safety] Failed to create logs directory: {logs_dir}")
        return

    # Write JSON results via safe I/O
    result_file = logs_dir / "result.json"
    if safe_json_write(result_file, result):
        print(f"[Safety] Logged results to {result_file}")
    else:
        print(f"[Safety] Failed to write result.json at {result_file}")

    # Write human-readable summary
    summary_file = logs_dir / "summary.txt"
    try:
        summary = _format_summary(result)
        summary_file.write_text(summary, encoding="utf-8")
        print(f"[Safety] Logged summary to {summary_file}")
    except Exception as e:  # noqa: BLE001
        print(f"[Safety] Failed to write summary.txt: {e}")


def _format_summary(result: Dict[str, Any]) -> str:
    """Format a human-readable summary of safety check results."""
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("SAFETY CHECK SUMMARY")
    lines.append("=" * 70)
    lines.append(f"Run ID: {result.get('run_id')}")
    lines.append(f"Status: {str(result.get('status', 'unknown')).upper()}")
    lines.append(f"Timestamp: {result.get('timestamp')}")
    if "timestamp_iso" in result:
        lines.append(f"Timestamp ISO: {result.get('timestamp_iso')}")
    lines.append("")

    # Static issues
    static = result.get("static_issues", []) or []
    lines.append(f"Static Analysis Issues: {len(static)}")
    if static:
        by_severity: Dict[str, List[Dict[str, Any]]] = {
            "error": [],
            "warning": [],
            "info": [],
        }
        for issue in static:
            sev = issue.get("severity", "info")
            by_severity.setdefault(sev, []).append(issue)

        for sev in ["error", "warning", "info"]:
            issues = by_severity.get(sev, [])
            if issues:
                lines.append(f"  - {sev.upper()}: {len(issues)}")
                for issue in issues[:5]:
                    file = issue.get("file", "<unknown>")
                    line_no = issue.get("line", "?")
                    msg = issue.get("message", "")
                    lines.append(f"    * {file}:{line_no} - {msg}")
                if len(issues) > 5:
                    lines.append(f"    ... and {len(issues) - 5} more")

    lines.append("")

    # Dependency issues
    deps = result.get("dependency_issues", []) or []
    lines.append(f"Dependency Issues: {len(deps)}")
    if deps:
        by_severity = {"critical": [], "medium": [], "low": []}
        for issue in deps:
            sev = issue.get("severity", "medium")
            by_severity.setdefault(sev, []).append(issue)

        for sev in ["critical", "medium", "low"]:
            issues = by_severity.get(sev, [])
            if issues:
                lines.append(f"  - {sev.upper()}: {len(issues)}")
                for issue in issues[:3]:
                    pkg = issue.get("package", "<unknown>")
                    ver = issue.get("version", "unknown")
                    summary = issue.get("summary", "")
                    lines.append(f"    * {pkg} ({ver})")
                    lines.append(f"      {summary}")
                if len(issues) > 3:
                    lines.append(f"    ... and {len(issues) - 3} more")

    lines.append("")

    # Docker tests
    docker = result.get("docker_tests", {}) or {}
    lines.append(f"Docker Tests: {str(docker.get('status', 'unknown')).upper()}")
    lines.append(f"  {docker.get('details', 'No details')}")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)
