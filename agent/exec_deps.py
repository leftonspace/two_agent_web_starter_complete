# exec_deps.py
"""
Dependency vulnerability scanning module for the multi-agent orchestrator.

Scans Python dependencies for known vulnerabilities using the OSV API.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Dict, Any

import requests


OSV_API_URL = "https://api.osv.dev/v1/querybatch"
REQUEST_TIMEOUT = 30  # seconds


def scan_dependencies(project_dir: str) -> List[Dict[str, Any]]:
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
            "summary": "description of the vulnerability",
            "scan_completed": True  # Always present; False if scan failed
        }

    Note:
        If the OSV API fails or times out, returns an empty list with no issues.
        This is graceful degradation - we don't fail the safety run just because
        the vulnerability database is unreachable. However, users should be aware
        that no scan occurred.
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
    except Exception as e:
        print(f"[DepScan] ⚠️  OSV API query failed (gracefully continuing): {e}")
        # Add a marker issue to indicate scan did not complete
        # This helps distinguish "no vulnerabilities" from "scan failed"
        issues.append({
            "package": "_scan_status",
            "version": "n/a",
            "severity": "low",
            "summary": f"Dependency scan did not complete: {str(e)}",
            "scan_completed": False
        })
        return issues

    return issues


def _parse_requirements(content: str) -> List[Dict[str, str]]:
    """
    Parse requirements.txt and extract package names and versions.

    Returns:
        List of dicts with 'name' and 'version' keys
    """
    packages = []
    lines = content.split("\n")

    for line in lines:
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        # Skip -e (editable installs) and other flags
        if line.startswith("-"):
            continue

        # Try to extract package name and version
        # Handle formats like:
        # - package==1.2.3
        # - package>=1.2.3
        # - package~=1.2.3
        # - package
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)([=<>~!]+)?(.+)?", line)
        if match:
            package_name = match.group(1)
            version = match.group(3) if match.group(3) else "unknown"

            packages.append({
                "name": package_name,
                "version": version.strip() if version != "unknown" else "unknown"
            })

    return packages


def _query_osv_api(packages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Query the OSV API for vulnerabilities in the given packages.

    Args:
        packages: List of package dicts with 'name' and 'version'

    Returns:
        List of vulnerability issues

    Raises:
        Exception: If API request fails (timeout, network error, etc.)
                   Caller should handle this gracefully
    """
    issues = []

    # Build query batch
    queries = []
    for pkg in packages:
        query = {
            "package": {
                "name": pkg["name"],
                "ecosystem": "PyPI"
            }
        }
        # Only add version if we have it
        if pkg["version"] != "unknown":
            query["version"] = pkg["version"]

        queries.append(query)

    # Make API request
    payload = {"queries": queries}

    try:
        response = requests.post(
            OSV_API_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        print("[DepScan] OSV API request timed out")
        raise  # Re-raise so caller can add scan_completed marker
    except requests.exceptions.RequestException as e:
        print(f"[DepScan] OSV API request failed: {e}")
        raise  # Re-raise so caller can add scan_completed marker
    except Exception as e:
        print(f"[DepScan] Unexpected error querying OSV API: {e}")
        raise  # Re-raise so caller can add scan_completed marker

    # Parse results
    results = data.get("results", [])

    for idx, result in enumerate(results):
        if idx >= len(packages):
            break

        package_info = packages[idx]
        vulns = result.get("vulns", [])

        for vuln in vulns:
            # Extract vulnerability details
            vuln_id = vuln.get("id", "UNKNOWN")
            summary = vuln.get("summary", "No summary available")

            # Determine severity
            # OSV uses "severity" field with various schemas
            severity = _extract_severity(vuln)

            issues.append({
                "package": package_info["name"],
                "version": package_info["version"],
                "severity": severity,
                "summary": f"[{vuln_id}] {summary}",
                "scan_completed": True
            })

    return issues


def _extract_severity(vuln: Dict[str, Any]) -> str:
    """
    Extract severity from OSV vulnerability data.

    Returns:
        "critical", "medium", or "low"
    """
    # Check if severity field exists
    severity_entries = vuln.get("severity", [])

    if not severity_entries:
        # Default to medium if no severity info
        return "medium"

    # OSV can have multiple severity entries (CVSS, etc.)
    for entry in severity_entries:
        if entry.get("type") == "CVSS_V3":
            score_str = entry.get("score", "")
            # Parse CVSS score (format: "CVSS:3.1/AV:N/AC:L/...")
            # Extract the base score
            try:
                # Look for common patterns or compute from vector
                # For simplicity, check if "CRITICAL" or "HIGH" in score
                if "CRITICAL" in score_str.upper():
                    return "critical"
                elif "HIGH" in score_str.upper():
                    return "critical"
                elif "MEDIUM" in score_str.upper():
                    return "medium"
                elif "LOW" in score_str.upper():
                    return "low"
            except Exception:
                pass

    # If we have database_specific severity
    db_specific = vuln.get("database_specific", {})
    sev = db_specific.get("severity", "").upper()
    if sev in ("CRITICAL", "HIGH"):
        return "critical"
    elif sev == "MEDIUM":
        return "medium"
    elif sev == "LOW":
        return "low"

    # Default to medium
    return "medium"
