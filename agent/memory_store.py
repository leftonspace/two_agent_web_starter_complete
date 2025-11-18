# memory_store.py
"""
PHASE 3: Stage-Level Persistent Memory System

This module provides lightweight, human-readable storage for stage-level knowledge:
- Decisions made during a stage
- Rejections and their reasons
- Revisions and iterations
- Supervisor findings
- Manager clarifications
- Links to previous stage summaries

Memory is stored as JSON files in memory_store/<run_id>/<stage_id>.json

KEY FEATURES:
- Human-readable JSON format
- Indexed by run_id and stage_id
- Supports querying previous stage memories
- Integrates with existing logs (Stage 2.2)
- Best-effort persistence (failures don't crash)
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

MEMORY_DIR = Path(__file__).resolve().parent / "memory_store"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class Decision:
    """
    A decision made during a stage.

    Attributes:
        timestamp: When the decision was made
        agent: Agent that made the decision (manager, supervisor, employee)
        decision_type: Type of decision (e.g., "roadmap_change", "skip_task", "merge_stages")
        description: Human-readable description
        context: Additional context/data
    """
    timestamp: float
    agent: str
    decision_type: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Decision:
        """Create from dict."""
        return cls(**data)


@dataclass
class Finding:
    """
    A finding from supervisor audit.

    Attributes:
        timestamp: When finding was reported
        severity: Severity level (error, warning, info)
        category: Category (e.g., "functionality", "design", "performance")
        description: Human-readable description
        file_path: Related file path (if applicable)
        line_number: Line number (if applicable)
        resolved: Whether finding has been resolved
        resolution_note: How it was resolved (if resolved)
    """
    timestamp: float
    severity: str  # error, warning, info
    category: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    resolved: bool = False
    resolution_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Finding:
        """Create from dict."""
        return cls(**data)


@dataclass
class Clarification:
    """
    A clarification request/response between agents.

    Attributes:
        timestamp: When clarification was requested
        from_agent: Agent requesting clarification
        to_agent: Agent providing clarification
        question: The question/request
        answer: The answer/response
        answered_at: When answered (if answered)
    """
    timestamp: float
    from_agent: str
    to_agent: str
    question: str
    answer: Optional[str] = None
    answered_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Clarification:
        """Create from dict."""
        return cls(**data)


@dataclass
class StageMemory:
    """
    Complete memory for a single stage.

    Attributes:
        run_id: Run identifier
        stage_id: Stage identifier
        stage_name: Human-readable stage name
        created_at: When memory was created
        updated_at: When memory was last updated
        decisions: List of decisions made
        findings: List of supervisor findings
        clarifications: List of clarification exchanges
        iterations: Number of iterations performed
        final_status: Final status (completed, reopened, skipped)
        summary: Human-readable summary of stage
        previous_stage_refs: IDs of previous stages referenced
        notes: Freeform notes
    """
    run_id: str
    stage_id: str
    stage_name: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    decisions: List[Decision] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    clarifications: List[Clarification] = field(default_factory=list)
    iterations: int = 0
    final_status: Optional[str] = None
    summary: str = ""
    previous_stage_refs: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "run_id": self.run_id,
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "decisions": [d.to_dict() for d in self.decisions],
            "findings": [f.to_dict() for f in self.findings],
            "clarifications": [c.to_dict() for c in self.clarifications],
            "iterations": self.iterations,
            "final_status": self.final_status,
            "summary": self.summary,
            "previous_stage_refs": self.previous_stage_refs,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StageMemory:
        """Create from dict."""
        return cls(
            run_id=data["run_id"],
            stage_id=data["stage_id"],
            stage_name=data["stage_name"],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            decisions=[Decision.from_dict(d) for d in data.get("decisions", [])],
            findings=[Finding.from_dict(f) for f in data.get("findings", [])],
            clarifications=[Clarification.from_dict(c) for c in data.get("clarifications", [])],
            iterations=data.get("iterations", 0),
            final_status=data.get("final_status"),
            summary=data.get("summary", ""),
            previous_stage_refs=data.get("previous_stage_refs", []),
            notes=data.get("notes", []),
        )


# ══════════════════════════════════════════════════════════════════════
# Memory Store Class
# ══════════════════════════════════════════════════════════════════════


class MemoryStore:
    """
    Manages persistent memory for stages in a run.

    Provides:
    - Create/load/save stage memories
    - Query previous stage memories
    - Add decisions, findings, clarifications
    - Generate stage summaries
    """

    def __init__(self, run_id: str):
        """
        Initialize memory store for a run.

        Args:
            run_id: Unique run identifier
        """
        self.run_id = run_id
        self.run_dir = MEMORY_DIR / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, StageMemory] = {}

    # ──────────────────────────────────────────────────────────────────
    # Core Operations
    # ──────────────────────────────────────────────────────────────────

    def create_memory(self, stage_id: str, stage_name: str) -> StageMemory:
        """
        Create a new stage memory.

        Args:
            stage_id: Unique stage identifier
            stage_name: Human-readable stage name

        Returns:
            New StageMemory instance
        """
        memory = StageMemory(
            run_id=self.run_id,
            stage_id=stage_id,
            stage_name=stage_name,
        )
        self._memory_cache[stage_id] = memory
        self._save_memory(memory)
        return memory

    def load_memory(self, stage_id: str) -> StageMemory:
        """
        Load stage memory from disk.

        Args:
            stage_id: Stage identifier

        Returns:
            Loaded StageMemory

        Raises:
            FileNotFoundError: If memory file doesn't exist
        """
        # Check cache first
        if stage_id in self._memory_cache:
            return self._memory_cache[stage_id]

        # Load from disk
        memory_file = self.run_dir / f"{stage_id}.json"
        if not memory_file.exists():
            raise FileNotFoundError(f"Memory file not found: {memory_file}")

        data = json.loads(memory_file.read_text(encoding="utf-8"))
        memory = StageMemory.from_dict(data)
        self._memory_cache[stage_id] = memory
        return memory

    def get_or_create_memory(self, stage_id: str, stage_name: str) -> StageMemory:
        """
        Get existing memory or create if doesn't exist.

        Args:
            stage_id: Stage identifier
            stage_name: Stage name (used only if creating)

        Returns:
            StageMemory instance
        """
        try:
            return self.load_memory(stage_id)
        except FileNotFoundError:
            return self.create_memory(stage_id, stage_name)

    def save_memory(self, memory: StageMemory):
        """
        Save stage memory to disk.

        Args:
            memory: StageMemory to save
        """
        self._memory_cache[memory.stage_id] = memory
        self._save_memory(memory)

    def _save_memory(self, memory: StageMemory):
        """Internal: Save memory to disk (best effort)."""
        try:
            memory.updated_at = time.time()
            memory_file = self.run_dir / f"{memory.stage_id}.json"
            data = memory.to_dict()
            memory_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            # Best effort - don't crash on save failures
            print(f"[MemoryStore] Warning: Failed to save memory: {e}")

    # ──────────────────────────────────────────────────────────────────
    # Add Memory Items
    # ──────────────────────────────────────────────────────────────────

    def add_decision(
        self,
        stage_id: str,
        agent: str,
        decision_type: str,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Add a decision to stage memory.

        Args:
            stage_id: Stage identifier
            agent: Agent making decision
            decision_type: Type of decision
            description: Human-readable description
            context: Additional context data
        """
        try:
            memory = self.load_memory(stage_id)
        except FileNotFoundError:
            return  # Best effort - ignore if memory doesn't exist

        decision = Decision(
            timestamp=time.time(),
            agent=agent,
            decision_type=decision_type,
            description=description,
            context=context or {},
        )
        memory.decisions.append(decision)
        self.save_memory(memory)

    def add_finding(
        self,
        stage_id: str,
        severity: str,
        category: str,
        description: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None
    ):
        """
        Add a supervisor finding to stage memory.

        Args:
            stage_id: Stage identifier
            severity: Severity level (error, warning, info)
            category: Finding category
            description: Human-readable description
            file_path: Related file (if applicable)
            line_number: Line number (if applicable)
        """
        try:
            memory = self.load_memory(stage_id)
        except FileNotFoundError:
            return  # Best effort

        finding = Finding(
            timestamp=time.time(),
            severity=severity,
            category=category,
            description=description,
            file_path=file_path,
            line_number=line_number,
        )
        memory.findings.append(finding)
        self.save_memory(memory)

    def resolve_finding(
        self,
        stage_id: str,
        finding_index: int,
        resolution_note: str
    ):
        """
        Mark a finding as resolved.

        Args:
            stage_id: Stage identifier
            finding_index: Index of finding in memory.findings list
            resolution_note: How it was resolved
        """
        try:
            memory = self.load_memory(stage_id)
            if 0 <= finding_index < len(memory.findings):
                finding = memory.findings[finding_index]
                finding.resolved = True
                finding.resolution_note = resolution_note
                self.save_memory(memory)
        except (FileNotFoundError, IndexError):
            pass  # Best effort

    def add_clarification(
        self,
        stage_id: str,
        from_agent: str,
        to_agent: str,
        question: str,
        answer: Optional[str] = None
    ):
        """
        Add a clarification exchange to stage memory.

        Args:
            stage_id: Stage identifier
            from_agent: Agent requesting clarification
            to_agent: Agent providing clarification
            question: The question
            answer: The answer (if available)
        """
        try:
            memory = self.load_memory(stage_id)
        except FileNotFoundError:
            return  # Best effort

        clarification = Clarification(
            timestamp=time.time(),
            from_agent=from_agent,
            to_agent=to_agent,
            question=question,
            answer=answer,
            answered_at=time.time() if answer else None,
        )
        memory.clarifications.append(clarification)
        self.save_memory(memory)

    def answer_clarification(
        self,
        stage_id: str,
        clarification_index: int,
        answer: str
    ):
        """
        Answer a pending clarification.

        Args:
            stage_id: Stage identifier
            clarification_index: Index of clarification
            answer: The answer
        """
        try:
            memory = self.load_memory(stage_id)
            if 0 <= clarification_index < len(memory.clarifications):
                clarification = memory.clarifications[clarification_index]
                clarification.answer = answer
                clarification.answered_at = time.time()
                self.save_memory(memory)
        except (FileNotFoundError, IndexError):
            pass  # Best effort

    def add_note(self, stage_id: str, note: str):
        """
        Add a freeform note to stage memory.

        Args:
            stage_id: Stage identifier
            note: Text note
        """
        try:
            memory = self.load_memory(stage_id)
            memory.notes.append(note)
            self.save_memory(memory)
        except FileNotFoundError:
            pass  # Best effort

    def increment_iterations(self, stage_id: str) -> int:
        """
        Increment iteration count for a stage.

        Args:
            stage_id: Stage identifier

        Returns:
            New iteration count
        """
        try:
            memory = self.load_memory(stage_id)
            memory.iterations += 1
            self.save_memory(memory)
            return memory.iterations
        except FileNotFoundError:
            return 0

    def set_summary(self, stage_id: str, summary: str):
        """
        Set stage summary text.

        Args:
            stage_id: Stage identifier
            summary: Summary text
        """
        try:
            memory = self.load_memory(stage_id)
            memory.summary = summary
            self.save_memory(memory)
        except FileNotFoundError:
            pass  # Best effort

    def set_final_status(self, stage_id: str, status: str):
        """
        Set final status for a stage.

        Args:
            stage_id: Stage identifier
            status: Final status (completed, reopened, skipped)
        """
        try:
            memory = self.load_memory(stage_id)
            memory.final_status = status
            self.save_memory(memory)
        except FileNotFoundError:
            pass  # Best effort

    # ──────────────────────────────────────────────────────────────────
    # Query Operations
    # ──────────────────────────────────────────────────────────────────

    def get_unresolved_findings(self, stage_id: str) -> List[Finding]:
        """
        Get all unresolved findings for a stage.

        Args:
            stage_id: Stage identifier

        Returns:
            List of unresolved Finding objects
        """
        try:
            memory = self.load_memory(stage_id)
            return [f for f in memory.findings if not f.resolved]
        except FileNotFoundError:
            return []

    def get_unanswered_clarifications(self, stage_id: str) -> List[Clarification]:
        """
        Get all unanswered clarifications for a stage.

        Args:
            stage_id: Stage identifier

        Returns:
            List of unanswered Clarification objects
        """
        try:
            memory = self.load_memory(stage_id)
            return [c for c in memory.clarifications if c.answer is None]
        except FileNotFoundError:
            return []

    def get_all_stage_memories(self) -> List[StageMemory]:
        """
        Get memories for all stages in this run.

        Returns:
            List of StageMemory objects
        """
        memories = []
        for memory_file in self.run_dir.glob("*.json"):
            try:
                data = json.loads(memory_file.read_text(encoding="utf-8"))
                memory = StageMemory.from_dict(data)
                memories.append(memory)
            except Exception:
                continue  # Skip invalid files
        return memories

    def get_previous_stage_summary(self, stage_id: str) -> Optional[str]:
        """
        Get summary from previous stage (if exists).

        Args:
            stage_id: Current stage identifier

        Returns:
            Summary text from previous stage, or None
        """
        try:
            memory = self.load_memory(stage_id)
            if memory.previous_stage_refs:
                prev_stage_id = memory.previous_stage_refs[0]
                prev_memory = self.load_memory(prev_stage_id)
                return prev_memory.summary
        except (FileNotFoundError, IndexError):
            pass
        return None

    def link_previous_stage(self, stage_id: str, previous_stage_id: str):
        """
        Link a stage to a previous stage for context.

        Args:
            stage_id: Current stage identifier
            previous_stage_id: Previous stage identifier
        """
        try:
            memory = self.load_memory(stage_id)
            if previous_stage_id not in memory.previous_stage_refs:
                memory.previous_stage_refs.append(previous_stage_id)
                self.save_memory(memory)
        except FileNotFoundError:
            pass  # Best effort

    # ──────────────────────────────────────────────────────────────────
    # Summary Generation
    # ──────────────────────────────────────────────────────────────────

    def generate_stage_summary(self, stage_id: str) -> str:
        """
        Generate a human-readable summary of stage memory.

        Args:
            stage_id: Stage identifier

        Returns:
            Formatted summary text
        """
        try:
            memory = self.load_memory(stage_id)
        except FileNotFoundError:
            return f"No memory found for stage {stage_id}"

        lines = []
        lines.append(f"=== Stage: {memory.stage_name} ===")
        lines.append(f"Status: {memory.final_status or 'in_progress'}")
        lines.append(f"Iterations: {memory.iterations}")
        lines.append("")

        if memory.decisions:
            lines.append("Decisions:")
            for d in memory.decisions:
                lines.append(f"  - [{d.agent}] {d.decision_type}: {d.description}")
            lines.append("")

        if memory.findings:
            unresolved = [f for f in memory.findings if not f.resolved]
            resolved = [f for f in memory.findings if f.resolved]
            lines.append(f"Findings: {len(unresolved)} unresolved, {len(resolved)} resolved")
            if unresolved:
                for f in unresolved[:5]:  # Show first 5
                    lines.append(f"  - [{f.severity}] {f.category}: {f.description}")
            lines.append("")

        if memory.clarifications:
            answered = [c for c in memory.clarifications if c.answer]
            pending = [c for c in memory.clarifications if not c.answer]
            lines.append(f"Clarifications: {len(answered)} answered, {len(pending)} pending")
            lines.append("")

        if memory.summary:
            lines.append("Summary:")
            lines.append(memory.summary)
            lines.append("")

        if memory.notes:
            lines.append("Notes:")
            for note in memory.notes[-3:]:  # Show last 3
                lines.append(f"  - {note}")

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# Public API Functions
# ══════════════════════════════════════════════════════════════════════


def create_memory_store(run_id: str) -> MemoryStore:
    """
    Create a new memory store for a run.

    Args:
        run_id: Unique run identifier

    Returns:
        MemoryStore instance
    """
    return MemoryStore(run_id)
