"""
PHASE 1.4: Artifact Logging System

This module provides structured logging of agent outputs (plans, code, QA results)
and generates human-readable HTML reports for each mission.

Artifacts are stored in:
    artifacts/<mission_id>/artifacts.jsonl    # Machine-readable log (JSONL)
    artifacts/<mission_id>/report.html        # Human-readable report
    artifacts/<mission_id>/files/             # Generated files (if any)

Each JSONL entry has the structure:
    {
        "type": "plan" | "code" | "qa" | "review" | "cost" | "error",
        "role": "manager" | "supervisor" | "employee" | "qa_reviewer",
        "timestamp": "2025-01-15T10:30:00Z",
        "content": "...",
        "metadata": {...}
    }
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# PHASE 1.2: Import log sanitizer to prevent sensitive data leakage
import log_sanitizer

# Local imports
from agent import paths


# ══════════════════════════════════════════════════════════════════════
# Artifact Types
# ══════════════════════════════════════════════════════════════════════


class ArtifactType:
    """Artifact type constants."""

    PLAN = "plan"
    CODE = "code"
    QA = "qa"
    REVIEW = "review"
    COST = "cost"
    ERROR = "error"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    FINAL_RESULT = "final_result"


# ══════════════════════════════════════════════════════════════════════
# Artifact Logging
# ══════════════════════════════════════════════════════════════════════


def get_artifacts_file_path(mission_id: str) -> Path:
    """
    Get the path to the artifacts JSONL file for a mission.

    Args:
        mission_id: Mission identifier

    Returns:
        Path to artifacts/<mission_id>/artifacts.jsonl
    """
    mission_artifacts_dir = paths.get_mission_artifacts_dir(mission_id)
    return mission_artifacts_dir / "artifacts.jsonl"


def log_artifact(
    mission_id: str,
    artifact_type: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an artifact entry to the mission's JSONL file.

    Args:
        mission_id: Mission identifier
        artifact_type: Type of artifact (plan, code, qa, etc.)
        role: Agent role (manager, supervisor, employee, qa_reviewer)
        content: Artifact content
        metadata: Optional additional metadata
    """
    # Ensure mission artifacts directory exists
    mission_artifacts_dir = paths.get_mission_artifacts_dir(mission_id)
    paths.ensure_dir(mission_artifacts_dir)

    # Create artifact entry
    entry = {
        "type": artifact_type,
        "role": role,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "content": content,
        "metadata": metadata or {},
    }

    # Append to JSONL file
    artifacts_file = get_artifacts_file_path(mission_id)

    # PHASE 1.2: Sanitize entry before persistence to prevent sensitive data leakage
    sanitized_entry = log_sanitizer.sanitize_log_data(entry)

    with artifacts_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(sanitized_entry, ensure_ascii=False) + "\n")


def log_plan(
    mission_id: str,
    role: str,
    plan_content: str,
    stages: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Log a planning artifact.

    Args:
        mission_id: Mission identifier
        role: Agent role (usually 'manager')
        plan_content: Full plan text
        stages: Optional list of plan stages
    """
    metadata = {}
    if stages:
        metadata["stages"] = stages
        metadata["num_stages"] = len(stages)

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.PLAN,
        role=role,
        content=plan_content,
        metadata=metadata,
    )


def log_code(
    mission_id: str,
    role: str,
    code_summary: str,
    files_modified: Optional[List[str]] = None,
    diff: Optional[str] = None,
) -> None:
    """
    Log a code generation artifact.

    Args:
        mission_id: Mission identifier
        role: Agent role (usually 'employee')
        code_summary: Summary of code changes
        files_modified: Optional list of modified file paths
        diff: Optional git diff output
    """
    metadata = {}
    if files_modified:
        metadata["files_modified"] = files_modified
        metadata["num_files"] = len(files_modified)
    if diff:
        metadata["diff"] = diff

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.CODE,
        role=role,
        content=code_summary,
        metadata=metadata,
    )


def log_qa(
    mission_id: str,
    qa_results: Dict[str, Any],
    passed: bool,
    issues: Optional[List[str]] = None,
) -> None:
    """
    Log a QA check artifact.

    Args:
        mission_id: Mission identifier
        qa_results: Full QA results dictionary
        passed: Whether QA checks passed
        issues: Optional list of issue descriptions
    """
    metadata = {
        "passed": passed,
        "qa_results": qa_results,
    }
    if issues:
        metadata["issues"] = issues
        metadata["num_issues"] = len(issues)

    content = f"QA Check: {'PASSED ✓' if passed else 'FAILED ✗'}"
    if issues:
        content += f"\n{len(issues)} issue(s) found"

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.QA,
        role="qa_reviewer",
        content=content,
        metadata=metadata,
    )


def log_review(
    mission_id: str,
    role: str,
    review_content: str,
    approved: bool,
    feedback: Optional[str] = None,
) -> None:
    """
    Log a review artifact.

    Args:
        mission_id: Mission identifier
        role: Reviewer role (manager, supervisor)
        review_content: Review summary
        approved: Whether work was approved
        feedback: Optional feedback for improvements
    """
    metadata = {
        "approved": approved,
    }
    if feedback:
        metadata["feedback"] = feedback

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.REVIEW,
        role=role,
        content=review_content,
        metadata=metadata,
    )


def log_cost_summary(
    mission_id: str,
    checkpoint: str,
    cost_summary: Dict[str, Any],
) -> None:
    """
    Log a cost tracking checkpoint.

    Args:
        mission_id: Mission identifier
        checkpoint: Checkpoint name (e.g., "planning", "iteration_1", "final")
        cost_summary: Cost summary from cost_tracker
    """
    content = f"Cost checkpoint: {checkpoint}"
    content += f"\nTotal cost: ${cost_summary.get('total_usd', 0):.4f} USD"
    content += f"\nLLM calls: {cost_summary.get('num_calls', 0)}"

    metadata = {
        "checkpoint": checkpoint,
        "cost_summary": cost_summary,
    }

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.COST,
        role="system",
        content=content,
        metadata=metadata,
    )


def log_error(
    mission_id: str,
    error_message: str,
    error_type: Optional[str] = None,
    traceback: Optional[str] = None,
) -> None:
    """
    Log an error artifact.

    Args:
        mission_id: Mission identifier
        error_message: Error message
        error_type: Optional error type/category
        traceback: Optional full traceback
    """
    metadata = {}
    if error_type:
        metadata["error_type"] = error_type
    if traceback:
        metadata["traceback"] = traceback

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.ERROR,
        role="system",
        content=error_message,
        metadata=metadata,
    )


def log_iteration_start(mission_id: str, iteration_num: int, stage_name: Optional[str] = None) -> None:
    """
    Log the start of an iteration.

    Args:
        mission_id: Mission identifier
        iteration_num: Iteration number (1-indexed)
        stage_name: Optional stage name
    """
    content = f"Starting iteration {iteration_num}"
    if stage_name:
        content += f": {stage_name}"

    metadata = {
        "iteration": iteration_num,
    }
    if stage_name:
        metadata["stage_name"] = stage_name

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.ITERATION_START,
        role="system",
        content=content,
        metadata=metadata,
    )


def log_iteration_end(
    mission_id: str,
    iteration_num: int,
    approved: bool,
    feedback: Optional[str] = None,
) -> None:
    """
    Log the end of an iteration.

    Args:
        mission_id: Mission identifier
        iteration_num: Iteration number (1-indexed)
        approved: Whether iteration was approved
        feedback: Optional feedback
    """
    content = f"Iteration {iteration_num}: {'APPROVED ✓' if approved else 'NEEDS REVISION ↻'}"
    if feedback:
        content += f"\n{feedback}"

    metadata = {
        "iteration": iteration_num,
        "approved": approved,
    }
    if feedback:
        metadata["feedback"] = feedback

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.ITERATION_END,
        role="system",
        content=content,
        metadata=metadata,
    )


def log_final_result(
    mission_id: str,
    status: str,
    summary: str,
    total_iterations: int,
    total_cost_usd: float,
) -> None:
    """
    Log the final mission result.

    Args:
        mission_id: Mission identifier
        status: Final status (success, failed, aborted)
        summary: Result summary
        total_iterations: Number of iterations completed
        total_cost_usd: Total cost in USD
    """
    content = f"Mission {status.upper()}\n{summary}"

    metadata = {
        "status": status,
        "total_iterations": total_iterations,
        "total_cost_usd": total_cost_usd,
    }

    log_artifact(
        mission_id=mission_id,
        artifact_type=ArtifactType.FINAL_RESULT,
        role="system",
        content=content,
        metadata=metadata,
    )


# ══════════════════════════════════════════════════════════════════════
# Artifact Reading
# ══════════════════════════════════════════════════════════════════════


def read_artifacts(mission_id: str) -> List[Dict[str, Any]]:
    """
    Read all artifacts for a mission from JSONL file.

    Args:
        mission_id: Mission identifier

    Returns:
        List of artifact dictionaries in chronological order

    Raises:
        FileNotFoundError: If artifacts file doesn't exist
    """
    artifacts_file = get_artifacts_file_path(mission_id)

    if not artifacts_file.exists():
        raise FileNotFoundError(
            f"No artifacts found for mission '{mission_id}'. Expected: {artifacts_file}"
        )

    artifacts = []
    with artifacts_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                artifacts.append(json.loads(line))

    return artifacts


# ══════════════════════════════════════════════════════════════════════
# HTML Report Generation
# ══════════════════════════════════════════════════════════════════════


def generate_report(mission_id: str) -> Path:
    """
    Generate an HTML report from mission artifacts.

    Args:
        mission_id: Mission identifier

    Returns:
        Path to generated report.html file

    Raises:
        FileNotFoundError: If artifacts file doesn't exist
    """
    # Read artifacts
    artifacts = read_artifacts(mission_id)

    if not artifacts:
        raise ValueError(f"No artifacts found for mission '{mission_id}'")

    # Group artifacts by type
    plans = [a for a in artifacts if a["type"] == ArtifactType.PLAN]
    code_artifacts = [a for a in artifacts if a["type"] == ArtifactType.CODE]
    qa_artifacts = [a for a in artifacts if a["type"] == ArtifactType.QA]
    reviews = [a for a in artifacts if a["type"] == ArtifactType.REVIEW]
    costs = [a for a in artifacts if a["type"] == ArtifactType.COST]
    errors = [a for a in artifacts if a["type"] == ArtifactType.ERROR]
    iterations = [a for a in artifacts if a["type"] in (ArtifactType.ITERATION_START, ArtifactType.ITERATION_END)]
    final_results = [a for a in artifacts if a["type"] == ArtifactType.FINAL_RESULT]

    # Generate HTML
    html = _generate_html_report(
        mission_id=mission_id,
        all_artifacts=artifacts,
        plans=plans,
        code_artifacts=code_artifacts,
        qa_artifacts=qa_artifacts,
        reviews=reviews,
        costs=costs,
        errors=errors,
        iterations=iterations,
        final_results=final_results,
    )

    # Write report
    report_path = paths.get_mission_artifacts_dir(mission_id) / "report.html"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(html)

    return report_path


def _generate_html_report(
    mission_id: str,
    all_artifacts: List[Dict[str, Any]],
    plans: List[Dict[str, Any]],
    code_artifacts: List[Dict[str, Any]],
    qa_artifacts: List[Dict[str, Any]],
    reviews: List[Dict[str, Any]],
    costs: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    iterations: List[Dict[str, Any]],
    final_results: List[Dict[str, Any]],
) -> str:
    """Generate HTML report content."""

    # Calculate summary stats
    total_artifacts = len(all_artifacts)
    num_iterations = len([it for it in iterations if it["type"] == ArtifactType.ITERATION_START])

    final_status = "Unknown"
    total_cost = 0.0
    if final_results:
        final_status = final_results[-1]["metadata"].get("status", "Unknown")
    if costs:
        total_cost = costs[-1]["metadata"]["cost_summary"].get("total_usd", 0.0)

    # Start HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mission Report: {mission_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }}
        .summary-item {{
            text-align: center;
        }}
        .summary-item .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .summary-item .label {{
            font-size: 12px;
            text-transform: uppercase;
            color: #6b7280;
            margin-top: 5px;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            font-size: 24px;
            color: #1f2937;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .artifact {{
            background: #f9fafb;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .artifact .artifact-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .artifact .role {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .artifact .timestamp {{
            color: #6b7280;
            font-size: 12px;
        }}
        .artifact .content {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            background: white;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        .status-success {{ color: #10b981; font-weight: bold; }}
        .status-failed {{ color: #ef4444; font-weight: bold; }}
        .status-aborted {{ color: #f59e0b; font-weight: bold; }}
        .empty-section {{
            color: #9ca3af;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }}
        .cost-breakdown {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Mission Report</h1>
            <div class="meta">Mission ID: {mission_id}</div>
        </div>

        <div class="summary">
            <div class="summary-item">
                <div class="value status-{final_status}">{final_status.upper()}</div>
                <div class="label">Status</div>
            </div>
            <div class="summary-item">
                <div class="value">{num_iterations}</div>
                <div class="label">Iterations</div>
            </div>
            <div class="summary-item">
                <div class="value">${total_cost:.4f}</div>
                <div class="label">Total Cost (USD)</div>
            </div>
            <div class="summary-item">
                <div class="value">{total_artifacts}</div>
                <div class="label">Total Artifacts</div>
            </div>
        </div>

        <div class="content">
"""

    # Plans section
    html += """
            <div class="section">
                <h2>📋 Plans</h2>
"""
    if plans:
        for plan in plans:
            html += f"""
                <div class="artifact">
                    <div class="artifact-header">
                        <span class="role">{plan['role']}</span>
                        <span class="timestamp">{plan['timestamp']}</span>
                    </div>
                    <div class="content">{_escape_html(plan['content'])}</div>
"""
            if plan['metadata'].get('stages'):
                html += f"<div style='margin-top: 10px; color: #6b7280; font-size: 12px;'>{len(plan['metadata']['stages'])} stages defined</div>"
            html += "</div>"
    else:
        html += '<div class="empty-section">No plans logged</div>'
    html += "</div>"

    # Code section
    html += """
            <div class="section">
                <h2>💻 Code Changes</h2>
"""
    if code_artifacts:
        for code in code_artifacts:
            html += f"""
                <div class="artifact">
                    <div class="artifact-header">
                        <span class="role">{code['role']}</span>
                        <span class="timestamp">{code['timestamp']}</span>
                    </div>
                    <div class="content">{_escape_html(code['content'])}</div>
"""
            if code['metadata'].get('files_modified'):
                html += f"<div style='margin-top: 10px; color: #6b7280; font-size: 12px;'>{len(code['metadata']['files_modified'])} files modified</div>"
            html += "</div>"
    else:
        html += '<div class="empty-section">No code changes logged</div>'
    html += "</div>"

    # QA section
    html += """
            <div class="section">
                <h2>✅ Quality Assurance</h2>
"""
    if qa_artifacts:
        for qa in qa_artifacts:
            passed = qa['metadata'].get('passed', False)
            border_color = '#10b981' if passed else '#ef4444'
            html += f"""
                <div class="artifact" style="border-left-color: {border_color};">
                    <div class="artifact-header">
                        <span class="role" style="background: {border_color};">qa_reviewer</span>
                        <span class="timestamp">{qa['timestamp']}</span>
                    </div>
                    <div class="content">{_escape_html(qa['content'])}</div>
"""
            if qa['metadata'].get('issues'):
                html += f"<div style='margin-top: 10px; color: #ef4444; font-size: 12px;'>{len(qa['metadata']['issues'])} issues found</div>"
            html += "</div>"
    else:
        html += '<div class="empty-section">No QA checks logged</div>'
    html += "</div>"

    # Cost section
    html += """
            <div class="section">
                <h2>💰 Cost Tracking</h2>
"""
    if costs:
        for cost in costs:
            checkpoint = cost['metadata'].get('checkpoint', 'unknown')
            cost_summary = cost['metadata'].get('cost_summary', {})
            html += f"""
                <div class="artifact">
                    <div class="artifact-header">
                        <span class="role">system</span>
                        <span class="timestamp">{cost['timestamp']}</span>
                    </div>
                    <div class="content">
Checkpoint: {checkpoint}
Total Cost: ${cost_summary.get('total_usd', 0):.4f} USD
LLM Calls: {cost_summary.get('num_calls', 0)}
"""
            if cost_summary.get('by_role'):
                html += "\nBy Role:\n"
                for role, stats in cost_summary['by_role'].items():
                    html += f"  {role}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}\n"
            html += "</div></div>"
    else:
        html += '<div class="empty-section">No cost checkpoints logged</div>'
    html += "</div>"

    # Errors section
    if errors:
        html += """
            <div class="section">
                <h2>⚠️ Errors</h2>
"""
        for error in errors:
            html += f"""
                <div class="artifact" style="border-left-color: #ef4444;">
                    <div class="artifact-header">
                        <span class="role" style="background: #ef4444;">error</span>
                        <span class="timestamp">{error['timestamp']}</span>
                    </div>
                    <div class="content">{_escape_html(error['content'])}</div>
                </div>
"""
        html += "</div>"

    # Final result section
    if final_results:
        html += """
            <div class="section">
                <h2>🎯 Final Result</h2>
"""
        final = final_results[-1]
        status = final['metadata'].get('status', 'unknown')
        status_class = f'status-{status}'
        html += f"""
                <div class="artifact">
                    <div class="artifact-header">
                        <span class="role">system</span>
                        <span class="timestamp">{final['timestamp']}</span>
                    </div>
                    <div class="content">{_escape_html(final['content'])}</div>
                    <div style='margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb;'>
                        <div><strong>Status:</strong> <span class="{status_class}">{status.upper()}</span></div>
                        <div><strong>Iterations:</strong> {final['metadata'].get('total_iterations', 0)}</div>
                        <div><strong>Total Cost:</strong> ${final['metadata'].get('total_cost_usd', 0):.4f} USD</div>
                    </div>
                </div>
"""
        html += "</div>"

    # Close HTML
    html += """
        </div>
    </div>
</body>
</html>
"""

    return html


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def clear_artifacts(mission_id: str) -> None:
    """
    Clear all artifacts for a mission (useful for testing/debugging).

    Args:
        mission_id: Mission identifier
    """
    artifacts_file = get_artifacts_file_path(mission_id)
    if artifacts_file.exists():
        artifacts_file.unlink()
