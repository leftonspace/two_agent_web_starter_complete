# exec_deps.py
"""
Dependency vulnerability scanning module for the multi-agent orchestrator.

Scans Python dependencies for known vulnerabilities using the OSV API.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import requests  # type: ignore[import-untyped]

OSV_API_URL = "https://api.osv.dev/v1/querybatch"
REQUEST_TIMEOUT = 30  # seconds


def scan_dependencies(project_dir: str | Path) -> List[Dict[str, Any]]:
    """
    Scan dependencies in requirements.txt for known vulnerabilities.

    Args:
        project_dir: Path to the project root directory

    Returns:
        List of vulnerability issues found, each with:
        {
            "package": "package-name",
            "version": "version-string or 'unknown'",
            "severity": "critical" | "medium" | "low",
            "summary": "description of the vulnerability"
        }
    """
    issues: List[Dict[str, Any]] = []
    project_path = Path(project_dir)

    # Look for requirements.txt
    requirements_file = project_path / "requirements.txt"
    if not requirements_file.exists():
        # No requirements.txt found, nothing to scan
        return issues

    try:
        content = requirements_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[DepScan] Failed to read requirements.txt: {e}")
        return issues

    # Parse requirements.txt
    packages = _parse_requirements(content)
    if not packages:
        return issues

    # Query OSV API
    try:
        vulnerabilities = _query_osv_api(packages)
        issues.extend(vulnerabilities)
    except Exception as e:  # pragma: no cover - defensive
        print(f"[DepScan] OSV API query failed (gracefully continuing): {e}")
        # Return whatever we have (usually empty) on API failure
        return issues

    return issues


def _parse_requirements(content: str) -> List[Dict[str, str]]:
    """
    Parse requirements.txt and extract package names and versions.

    Returns:
        List of dicts with 'name' and 'version' keys.
        Version is 'unknown' when not specified.
    """
    packages: List[Dict[str, str]] = []
    lines = content.splitlines()

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Skip -e (editable installs) and other flags
        if line.startswith("-"):
            continue

        # Handle formats like:
        # - package==1.2.3
        # - package>=1.2.3
        # - package~=1.2.3
        # - package
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)([=<>~!]+)?(.+)?$", line)
        if not match:
            continue

        package_name = match.group(1)
        version_raw = match.group(3)

        if version_raw:
            version = version_raw.strip()
        else:
            version = "unknown"

        packages.append(
            {
                "name": package_name,
                "version": version,
            }
        )

    return packages


def _query_osv_api(packages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Query the OSV API for vulnerabilities in the given packages.

    Args:
        packages: List of package dicts with 'name' and 'version'

    Returns:
        List of vulnerability issues
    """
    issues: List[Dict[str, Any]] = []

    if not packages:
        return issues

    # Build query batch
    queries: List[Dict[str, Any]] = []
    for pkg in packages:
        name = pkg.get("name", "")
        version = pkg.get("version", "unknown")

        if not name:
            continue

        query: Dict[str, Any] = {
            "package": {
                "name": name,
                "ecosystem": "PyPI",
            }
        }
        # Only add version if we have it
        if version != "unknown":
            query["version"] = version

        queries.append(query)

    if not queries:
        return issues

    payload: Dict[str, Any] = {"queries": queries}

    try:
        response = requests.post(
            OSV_API_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
    except requests.exceptions.Timeout:
        print("[DepScan] OSV API request timed out")
        return issues
    except requests.exceptions.RequestException as e:
        print(f"[DepScan] OSV API request failed: {e}")
        return issues
    except Exception as e:  # pragma: no cover - defensive
        print(f"[DepScan] Unexpected error querying OSV API: {e}")
        return issues

    # Parse results
    results = data.get("results", [])
    if not isinstance(results, list):
        return issues

    for idx, result in enumerate(results):
        if idx >= len(packages):
            break

        package_info = packages[idx]
        vulns = result.get("vulns", [])
        if not isinstance(vulns, list):
            continue

        for vuln in vulns:
            if not isinstance(vuln, dict):
                continue

            vuln_id = str(vuln.get("id", "UNKNOWN"))
            summary = str(vuln.get("summary", "No summary available"))

            # Determine severity
            severity = _extract_severity(vuln)

            issues.append(
                {
                    "package": package_info.get("name", "unknown"),
                    "version": package_info.get("version", "unknown"),
                    "severity": severity,
                    "summary": f"[{vuln_id}] {summary}",
                }
            )

    return issues


def _extract_severity(vuln: Dict[str, Any]) -> str:
    """
    Extract severity from OSV vulnerability data.

    Returns:
        "critical", "medium", or "low"
    """
    # Default if nothing is known
    default = "medium"

    severity_entries = vuln.get("severity", [])
    if isinstance(severity_entries, list):
        for entry in severity_entries:
            if not isinstance(entry, dict):
                continue
            sev_type = entry.get("type")
            score_str = str(entry.get("score", ""))

            # Very rough mapping based on keywords in score/description.
            if sev_type and "CVSS" in str(sev_type).upper():
                upper = score_str.upper()
                if "CRITICAL" in upper or "HIGH" in upper:
                    return "critical"
                if "MEDIUM" in upper:
                    return "medium"
                if "LOW" in upper:
                    return "low"

    db_specific = vuln.get("database_specific", {})
    if isinstance(db_specific, dict):
        sev = str(db_specific.get("severity", "")).upper()
        if sev in ("CRITICAL", "HIGH"):
            return "critical"
        if sev == "MEDIUM":
            return "medium"
        if sev == "LOW":
            return "low"

    return default
