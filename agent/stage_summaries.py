# stage_summaries.py
"""
PHASE 3: Stage Summaries & Regression Detection

This module tracks stage completion details and detects regressions:
- What changed in each stage
- Final result of each stage
- Issues found during stage
- Fix cycles performed
- Regression analysis (do issues in Stage N trace back to Stage K?)

KEY FEATURES:
- Comprehensive stage result tracking
- Regression detection logic
- Change diff tracking
- Issue categorization and linking
- Integration with memory_store and workflow_manager
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════

SUMMARIES_DIR = Path(__file__).resolve().parent / "stage_summaries"
SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class FileChange:
    """
    A change to a file during a stage.

    Attributes:
        file_path: Path to file
        change_type: created, modified, deleted
        lines_added: Number of lines added
        lines_removed: Number of lines removed
        size_bytes: Final file size
    """
    file_path: str
    change_type: str  # created, modified, deleted
    lines_added: int = 0
    lines_removed: int = 0
    size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FileChange:
        """Create from dict."""
        return cls(**data)


@dataclass
class Issue:
    """
    An issue found during a stage.

    Attributes:
        id: Unique issue identifier
        severity: error, warning, info
        category: Category (e.g., functionality, design, performance, security)
        description: Human-readable description
        file_path: Related file (if applicable)
        line_number: Line number (if applicable)
        detected_in_stage: Stage where issue was first detected
        introduced_in_stage: Stage where issue was likely introduced (if known)
        resolved_in_stage: Stage where issue was resolved (if resolved)
        resolution_note: How it was resolved
        created_at: When issue was created
    """
    id: str
    severity: str
    category: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    detected_in_stage: Optional[str] = None
    introduced_in_stage: Optional[str] = None
    resolved_in_stage: Optional[str] = None
    resolution_note: Optional[str] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Issue:
        """Create from dict."""
        return cls(**data)


@dataclass
class FixCycle:
    """
    A fix cycle (iteration) within a stage.

    Attributes:
        cycle_number: 1-indexed cycle number
        started_at: Unix timestamp
        completed_at: Unix timestamp (if completed)
        issues_addressed: List of issue IDs addressed
        files_changed: List of file paths changed
        employee_model: Model used for employee
        supervisor_findings: Number of findings from supervisor
        status: in_progress, completed, failed
    """
    cycle_number: int
    started_at: float
    completed_at: Optional[float] = None
    issues_addressed: List[str] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    employee_model: Optional[str] = None
    supervisor_findings: int = 0
    status: str = "in_progress"  # in_progress, completed, failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FixCycle:
        """Create from dict."""
        return cls(**data)


@dataclass
class StageSummary:
    """
    Complete summary of a stage's execution.

    Attributes:
        run_id: Run identifier
        stage_id: Stage identifier
        stage_name: Human-readable stage name
        started_at: When stage started
        completed_at: When stage completed (if completed)
        status: completed, reopened, skipped, failed
        files_changed: List of FileChange objects
        fix_cycles: List of FixCycle objects
        issues: List of Issue objects (all issues for this stage)
        regression_detected: Whether this stage caused regression
        regression_target_stage: Stage that had regression (if any)
        cost_usd: Estimated cost for this stage
        iterations_count: Total iterations performed
        final_notes: Final notes/summary from manager
    """
    run_id: str
    stage_id: str
    stage_name: str
    started_at: float
    completed_at: Optional[float] = None
    status: str = "in_progress"
    files_changed: List[FileChange] = field(default_factory=list)
    fix_cycles: List[FixCycle] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
    regression_detected: bool = False
    regression_target_stage: Optional[str] = None
    cost_usd: float = 0.0
    iterations_count: int = 0
    final_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "run_id": self.run_id,
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "files_changed": [f.to_dict() for f in self.files_changed],
            "fix_cycles": [c.to_dict() for c in self.fix_cycles],
            "issues": [i.to_dict() for i in self.issues],
            "regression_detected": self.regression_detected,
            "regression_target_stage": self.regression_target_stage,
            "cost_usd": self.cost_usd,
            "iterations_count": self.iterations_count,
            "final_notes": self.final_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StageSummary:
        """Create from dict."""
        return cls(
            run_id=data["run_id"],
            stage_id=data["stage_id"],
            stage_name=data["stage_name"],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            status=data.get("status", "in_progress"),
            files_changed=[FileChange.from_dict(f) for f in data.get("files_changed", [])],
            fix_cycles=[FixCycle.from_dict(c) for c in data.get("fix_cycles", [])],
            issues=[Issue.from_dict(i) for i in data.get("issues", [])],
            regression_detected=data.get("regression_detected", False),
            regression_target_stage=data.get("regression_target_stage"),
            cost_usd=data.get("cost_usd", 0.0),
            iterations_count=data.get("iterations_count", 0),
            final_notes=data.get("final_notes", ""),
        )


# ══════════════════════════════════════════════════════════════════════
# Stage Summary Tracker Class
# ══════════════════════════════════════════════════════════════════════


class StageSummaryTracker:
    """
    Tracks and manages stage summaries for a run.

    Provides:
    - Create/load/save stage summaries
    - Add file changes, issues, fix cycles
    - Detect regressions between stages
    - Generate reports
    """

    def __init__(self, run_id: str):
        """
        Initialize tracker for a run.

        Args:
            run_id: Unique run identifier
        """
        self.run_id = run_id
        self.run_dir = SUMMARIES_DIR / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._summaries: Dict[str, StageSummary] = {}

    # ──────────────────────────────────────────────────────────────────
    # Core Operations
    # ──────────────────────────────────────────────────────────────────

    def create_summary(self, stage_id: str, stage_name: str) -> StageSummary:
        """
        Create a new stage summary.

        Args:
            stage_id: Stage identifier
            stage_name: Human-readable stage name

        Returns:
            New StageSummary instance
        """
        summary = StageSummary(
            run_id=self.run_id,
            stage_id=stage_id,
            stage_name=stage_name,
            started_at=time.time(),
        )
        self._summaries[stage_id] = summary
        self._save_summary(summary)
        return summary

    def load_summary(self, stage_id: str) -> StageSummary:
        """
        Load stage summary from disk.

        Args:
            stage_id: Stage identifier

        Returns:
            Loaded StageSummary

        Raises:
            FileNotFoundError: If summary doesn't exist
        """
        # Check cache first
        if stage_id in self._summaries:
            return self._summaries[stage_id]

        # Load from disk
        summary_file = self.run_dir / f"{stage_id}.json"
        if not summary_file.exists():
            raise FileNotFoundError(f"Summary not found: {summary_file}")

        data = json.loads(summary_file.read_text(encoding="utf-8"))
        summary = StageSummary.from_dict(data)
        self._summaries[stage_id] = summary
        return summary

    def get_or_create_summary(self, stage_id: str, stage_name: str) -> StageSummary:
        """
        Get existing summary or create if doesn't exist.

        Args:
            stage_id: Stage identifier
            stage_name: Stage name (used only if creating)

        Returns:
            StageSummary instance
        """
        try:
            return self.load_summary(stage_id)
        except FileNotFoundError:
            return self.create_summary(stage_id, stage_name)

    def save_summary(self, summary: StageSummary):
        """
        Save stage summary to disk.

        Args:
            summary: StageSummary to save
        """
        self._summaries[summary.stage_id] = summary
        self._save_summary(summary)

    def _save_summary(self, summary: StageSummary):
        """Internal: Save summary to disk (best effort)."""
        try:
            summary_file = self.run_dir / f"{summary.stage_id}.json"
            data = summary.to_dict()
            summary_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            print(f"[StageSummaryTracker] Warning: Failed to save summary: {e}")

    # ──────────────────────────────────────────────────────────────────
    # Add Data to Summary
    # ──────────────────────────────────────────────────────────────────

    def add_file_change(
        self,
        stage_id: str,
        file_path: str,
        change_type: str,
        lines_added: int = 0,
        lines_removed: int = 0,
        size_bytes: int = 0
    ):
        """
        Add a file change to stage summary.

        Args:
            stage_id: Stage identifier
            file_path: Path to file
            change_type: created, modified, deleted
            lines_added: Lines added
            lines_removed: Lines removed
            size_bytes: Final file size
        """
        try:
            summary = self.load_summary(stage_id)
            change = FileChange(
                file_path=file_path,
                change_type=change_type,
                lines_added=lines_added,
                lines_removed=lines_removed,
                size_bytes=size_bytes,
            )
            summary.files_changed.append(change)
            self.save_summary(summary)
        except FileNotFoundError:
            pass  # Best effort

    def add_issue(
        self,
        stage_id: str,
        issue_id: str,
        severity: str,
        category: str,
        description: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ):
        """
        Add an issue to stage summary.

        Args:
            stage_id: Stage identifier
            issue_id: Unique issue ID
            severity: error, warning, info
            category: Issue category
            description: Human-readable description
            file_path: Related file (if applicable)
            line_number: Line number (if applicable)
        """
        try:
            summary = self.load_summary(stage_id)
            issue = Issue(
                id=issue_id,
                severity=severity,
                category=category,
                description=description,
                file_path=file_path,
                line_number=line_number,
                detected_in_stage=stage_id,
            )
            summary.issues.append(issue)
            self.save_summary(summary)
        except FileNotFoundError:
            pass  # Best effort

    def resolve_issue(
        self,
        stage_id: str,
        issue_id: str,
        resolution_note: str
    ):
        """
        Mark an issue as resolved.

        Args:
            stage_id: Stage where issue was resolved
            issue_id: Issue identifier
            resolution_note: How it was resolved
        """
        try:
            summary = self.load_summary(stage_id)
            for issue in summary.issues:
                if issue.id == issue_id:
                    issue.resolved_in_stage = stage_id
                    issue.resolution_note = resolution_note
                    self.save_summary(summary)
                    break
        except FileNotFoundError:
            pass  # Best effort

    def start_fix_cycle(
        self,
        stage_id: str,
        cycle_number: int,
        employee_model: Optional[str] = None
    ) -> FixCycle:
        """
        Start a new fix cycle.

        Args:
            stage_id: Stage identifier
            cycle_number: Cycle number (1-indexed)
            employee_model: Model used for employee

        Returns:
            New FixCycle instance
        """
        try:
            summary = self.load_summary(stage_id)
            cycle = FixCycle(
                cycle_number=cycle_number,
                started_at=time.time(),
                employee_model=employee_model,
            )
            summary.fix_cycles.append(cycle)
            self.save_summary(summary)
            return cycle
        except FileNotFoundError:
            return FixCycle(cycle_number=cycle_number, started_at=time.time())

    def complete_fix_cycle(
        self,
        stage_id: str,
        cycle_number: int,
        issues_addressed: List[str],
        files_changed: List[str],
        supervisor_findings: int,
        status: str = "completed"
    ):
        """
        Complete a fix cycle.

        Args:
            stage_id: Stage identifier
            cycle_number: Cycle number
            issues_addressed: List of issue IDs addressed
            files_changed: List of file paths changed
            supervisor_findings: Number of findings from supervisor
            status: completed or failed
        """
        try:
            summary = self.load_summary(stage_id)
            for cycle in summary.fix_cycles:
                if cycle.cycle_number == cycle_number:
                    cycle.completed_at = time.time()
                    cycle.issues_addressed = issues_addressed
                    cycle.files_changed = files_changed
                    cycle.supervisor_findings = supervisor_findings
                    cycle.status = status
                    self.save_summary(summary)
                    break
        except FileNotFoundError:
            pass  # Best effort

    def complete_stage(
        self,
        stage_id: str,
        status: str,
        final_notes: str = "",
        cost_usd: float = 0.0
    ):
        """
        Mark stage as completed.

        Args:
            stage_id: Stage identifier
            status: Final status (completed, skipped, failed)
            final_notes: Final summary notes
            cost_usd: Estimated cost for stage
        """
        try:
            summary = self.load_summary(stage_id)
            summary.completed_at = time.time()
            summary.status = status
            summary.final_notes = final_notes
            summary.cost_usd = cost_usd
            self.save_summary(summary)
        except FileNotFoundError:
            pass  # Best effort

    # ──────────────────────────────────────────────────────────────────
    # Regression Detection
    # ──────────────────────────────────────────────────────────────────

    def detect_regression(
        self,
        current_stage_id: str,
        issues: List[Dict[str, Any]],
        previous_stage_summaries: List[StageSummary]
    ) -> Optional[str]:
        """
        Detect if issues in current stage are regressions from previous stages.

        Analyzes issues to determine if they were introduced by work in earlier stages.

        Args:
            current_stage_id: Current stage identifier
            issues: List of issue dicts from current stage
            previous_stage_summaries: List of previous stage summaries

        Returns:
            Stage ID where regression was likely introduced, or None
        """
        if not issues or not previous_stage_summaries:
            return None

        # Simple heuristic: Check if issues mention files changed in previous stages
        issue_files = set()
        for issue in issues:
            if "file_path" in issue and issue["file_path"]:
                issue_files.add(issue["file_path"])

        if not issue_files:
            return None

        # Check previous stages in reverse order (most recent first)
        for prev_summary in reversed(previous_stage_summaries):
            prev_files = {fc.file_path for fc in prev_summary.files_changed}
            overlap = issue_files & prev_files

            # If >50% of issue files were changed in previous stage, likely regression
            if len(overlap) > len(issue_files) * 0.5:
                return prev_summary.stage_id

        return None

    def mark_regression(
        self,
        regressing_stage_id: str,
        target_stage_id: str
    ):
        """
        Mark a stage as causing regression in another stage.

        Args:
            regressing_stage_id: Stage that caused regression
            target_stage_id: Stage where regression was detected
        """
        try:
            summary = self.load_summary(regressing_stage_id)
            summary.regression_detected = True
            summary.regression_target_stage = target_stage_id
            self.save_summary(summary)
        except FileNotFoundError:
            pass  # Best effort

    # ──────────────────────────────────────────────────────────────────
    # Query Operations
    # ──────────────────────────────────────────────────────────────────

    def get_all_summaries(self) -> List[StageSummary]:
        """
        Get all stage summaries for this run.

        Returns:
            List of StageSummary objects
        """
        summaries = []
        for summary_file in self.run_dir.glob("*.json"):
            try:
                data = json.loads(summary_file.read_text(encoding="utf-8"))
                summary = StageSummary.from_dict(data)
                summaries.append(summary)
            except Exception:
                continue  # Skip invalid files
        return summaries

    def get_unresolved_issues(self, stage_id: str) -> List[Issue]:
        """
        Get all unresolved issues for a stage.

        Args:
            stage_id: Stage identifier

        Returns:
            List of unresolved Issue objects
        """
        try:
            summary = self.load_summary(stage_id)
            return [i for i in summary.issues if i.resolved_in_stage is None]
        except FileNotFoundError:
            return []

    def get_stages_with_regressions(self) -> List[StageSummary]:
        """
        Get all stages that caused regressions.

        Returns:
            List of StageSummary objects with regression_detected=True
        """
        all_summaries = self.get_all_summaries()
        return [s for s in all_summaries if s.regression_detected]

    # ──────────────────────────────────────────────────────────────────
    # Reporting
    # ──────────────────────────────────────────────────────────────────

    def generate_report(self, stage_id: str) -> str:
        """
        Generate human-readable report for a stage.

        Args:
            stage_id: Stage identifier

        Returns:
            Formatted report text
        """
        try:
            summary = self.load_summary(stage_id)
        except FileNotFoundError:
            return f"No summary found for stage {stage_id}"

        lines = []
        lines.append(f"=== Stage Report: {summary.stage_name} ===")
        lines.append(f"Status: {summary.status}")
        lines.append(f"Iterations: {summary.iterations_count}")
        lines.append(f"Fix Cycles: {len(summary.fix_cycles)}")
        lines.append(f"Cost: ${summary.cost_usd:.4f} USD")
        lines.append("")

        # Duration
        if summary.completed_at:
            duration = summary.completed_at - summary.started_at
            lines.append(f"Duration: {duration:.1f} seconds")
            lines.append("")

        # Files changed
        if summary.files_changed:
            lines.append(f"Files Changed: {len(summary.files_changed)}")
            created = sum(1 for f in summary.files_changed if f.change_type == "created")
            modified = sum(1 for f in summary.files_changed if f.change_type == "modified")
            deleted = sum(1 for f in summary.files_changed if f.change_type == "deleted")
            lines.append(f"  Created: {created}, Modified: {modified}, Deleted: {deleted}")
            total_lines_added = sum(f.lines_added for f in summary.files_changed)
            total_lines_removed = sum(f.lines_removed for f in summary.files_changed)
            lines.append(f"  +{total_lines_added} -{total_lines_removed} lines")
            lines.append("")

        # Issues
        if summary.issues:
            unresolved = [i for i in summary.issues if i.resolved_in_stage is None]
            resolved = [i for i in summary.issues if i.resolved_in_stage is not None]
            lines.append(f"Issues: {len(unresolved)} unresolved, {len(resolved)} resolved")
            if unresolved:
                lines.append("  Unresolved:")
                for issue in unresolved[:5]:  # Show first 5
                    lines.append(f"    - [{issue.severity}] {issue.description}")
            lines.append("")

        # Fix cycles
        if summary.fix_cycles:
            lines.append("Fix Cycles:")
            for cycle in summary.fix_cycles:
                status_emoji = "✓" if cycle.status == "completed" else "✗"
                lines.append(f"  {status_emoji} Cycle {cycle.cycle_number}: {cycle.supervisor_findings} findings")
            lines.append("")

        # Regression
        if summary.regression_detected:
            lines.append(f"⚠️  Regression detected in stage: {summary.regression_target_stage}")
            lines.append("")

        # Final notes
        if summary.final_notes:
            lines.append("Final Notes:")
            lines.append(summary.final_notes)

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# Public API Functions
# ══════════════════════════════════════════════════════════════════════


def create_tracker(run_id: str) -> StageSummaryTracker:
    """
    Create a new stage summary tracker for a run.

    Args:
        run_id: Unique run identifier

    Returns:
        StageSummaryTracker instance
    """
    return StageSummaryTracker(run_id)
