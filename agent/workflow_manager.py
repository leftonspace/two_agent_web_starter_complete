# workflow_manager.py
"""
PHASE 3: Dynamic Roadmap Management & Workflow Orchestration

This module manages the adaptive, intelligent multi-stage workflow system:
- Dynamic roadmap creation and mutation (merge, split, reorder stages)
- Stage transition logic with auto-advancement
- Backward stage reopening for regression fixes
- Roadmap versioning and history tracking

KEY CONCEPTS:
- **Stage**: A logical unit of work (e.g., "Layout & Structure", "API Integration")
- **Roadmap**: An ordered list of stages that can be dynamically modified
- **Roadmap Version**: Immutable snapshot of roadmap at a point in time
- **Stage Status**: pending, active, completed, reopened, skipped
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════

WORKFLOWS_DIR = Path(__file__).resolve().parent / "run_workflows"
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════


@dataclass
class Stage:
    """
    A single stage in the roadmap.

    Attributes:
        id: Unique identifier for this stage (UUID)
        name: Human-readable name (e.g., "Layout & Structure")
        description: Brief description of stage goals
        categories: List of categories (from prompts.py persona types)
        plan_steps: Indices into the original plan that this stage covers
        status: Current status (pending, active, completed, reopened, skipped)
        created_at: Unix timestamp when stage was created
        completed_at: Unix timestamp when stage was completed (if completed)
        audit_count: Number of supervisor audits performed on this stage
        regression_source: If reopened, the stage ID that caused regression
    """
    id: str
    name: str
    description: str
    categories: List[str]
    plan_steps: List[int]
    status: str = "pending"  # pending, active, completed, reopened, skipped
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    audit_count: int = 0
    regression_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Stage:
        """Create Stage from dict."""
        return cls(**data)


@dataclass
class Roadmap:
    """
    A versioned roadmap containing ordered stages.

    Attributes:
        version: Roadmap version number (increments on each mutation)
        stages: Ordered list of stages
        created_at: Unix timestamp when this version was created
        created_by: Reason/agent that created this version (e.g., "manager", "regression_detector")
        mutation_type: Type of mutation (initial, merge, split, reorder, reopen, skip)
        mutation_reason: Human-readable reason for the mutation
    """
    version: int
    stages: List[Stage]
    created_at: float = field(default_factory=time.time)
    created_by: str = "system"
    mutation_type: str = "initial"  # initial, merge, split, reorder, reopen, skip
    mutation_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "version": self.version,
            "stages": [s.to_dict() for s in self.stages],
            "created_at": self.created_at,
            "created_by": self.created_by,
            "mutation_type": self.mutation_type,
            "mutation_reason": self.mutation_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Roadmap:
        """Create Roadmap from dict."""
        stages = [Stage.from_dict(s) for s in data["stages"]]
        return cls(
            version=data["version"],
            stages=stages,
            created_at=data.get("created_at", time.time()),
            created_by=data.get("created_by", "system"),
            mutation_type=data.get("mutation_type", "initial"),
            mutation_reason=data.get("mutation_reason", ""),
        )


@dataclass
class WorkflowState:
    """
    Complete workflow state including roadmap history.

    Attributes:
        run_id: Unique identifier for this run
        roadmap_history: List of all roadmap versions (most recent last)
        active_stage_id: ID of currently active stage (if any)
        created_at: Unix timestamp when workflow was created
        updated_at: Unix timestamp when workflow was last updated
    """
    run_id: str
    roadmap_history: List[Roadmap]
    active_stage_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def current_roadmap(self) -> Roadmap:
        """Get the current (most recent) roadmap version."""
        if not self.roadmap_history:
            raise ValueError("Workflow has no roadmap history")
        return self.roadmap_history[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "run_id": self.run_id,
            "roadmap_history": [r.to_dict() for r in self.roadmap_history],
            "active_stage_id": self.active_stage_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowState:
        """Create WorkflowState from dict."""
        roadmap_history = [Roadmap.from_dict(r) for r in data["roadmap_history"]]
        return cls(
            run_id=data["run_id"],
            roadmap_history=roadmap_history,
            active_stage_id=data.get("active_stage_id"),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


# ══════════════════════════════════════════════════════════════════════
# Workflow Manager Class
# ══════════════════════════════════════════════════════════════════════


class WorkflowManager:
    """
    Manages dynamic workflow evolution throughout a run.

    Key Responsibilities:
    - Create initial roadmap from manager's plan
    - Mutate roadmap (merge, split, reorder, skip stages)
    - Advance through stages with auto-skip logic
    - Reopen previous stages for regression fixes
    - Persist workflow state to disk
    """

    def __init__(self, run_id: str):
        """
        Initialize workflow manager for a run.

        Args:
            run_id: Unique identifier for this run
        """
        self.run_id = run_id
        self.workflow_file = WORKFLOWS_DIR / f"{run_id}_workflow.json"
        self.state: Optional[WorkflowState] = None

    # ──────────────────────────────────────────────────────────────────
    # Initialization & Persistence
    # ──────────────────────────────────────────────────────────────────

    def initialize(
        self,
        plan_steps: List[str],
        supervisor_phases: List[Dict[str, Any]],
        task: str
    ) -> WorkflowState:
        """
        Initialize workflow from manager's plan and supervisor's phases.

        Args:
            plan_steps: List of plan steps from manager
            supervisor_phases: List of phases from supervisor with categories
            task: Original task description

        Returns:
            Initial WorkflowState
        """
        # Convert supervisor phases to stages
        stages = []
        for idx, phase in enumerate(supervisor_phases):
            stage = Stage(
                id=str(uuid.uuid4()),
                name=phase.get("name", f"Stage {idx + 1}"),
                description=f"Complete: {', '.join(phase.get('categories', []))}",
                categories=phase.get("categories", []),
                plan_steps=phase.get("plan_steps", []),
                status="pending",
            )
            stages.append(stage)

        # Create initial roadmap
        initial_roadmap = Roadmap(
            version=1,
            stages=stages,
            created_by="supervisor",
            mutation_type="initial",
            mutation_reason="Initial roadmap created from supervisor phases",
        )

        # Create workflow state
        self.state = WorkflowState(
            run_id=self.run_id,
            roadmap_history=[initial_roadmap],
        )

        # Persist to disk
        self._save()
        return self.state

    def load(self) -> WorkflowState:
        """
        Load workflow state from disk.

        Returns:
            WorkflowState loaded from file

        Raises:
            FileNotFoundError: If workflow file doesn't exist
        """
        if not self.workflow_file.exists():
            raise FileNotFoundError(f"Workflow file not found: {self.workflow_file}")

        data = json.loads(self.workflow_file.read_text(encoding="utf-8"))
        self.state = WorkflowState.from_dict(data)
        return self.state

    def _save(self):
        """Save current workflow state to disk (best effort)."""
        if self.state is None:
            return

        try:
            self.state.updated_at = time.time()
            data = self.state.to_dict()
            self.workflow_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            # Best effort - don't crash on save failures
            print(f"[WorkflowManager] Warning: Failed to save workflow state: {e}")

    # ──────────────────────────────────────────────────────────────────
    # Stage Navigation
    # ──────────────────────────────────────────────────────────────────

    def get_active_stage(self) -> Optional[Stage]:
        """Get the currently active stage (if any)."""
        if self.state is None or self.state.active_stage_id is None:
            return None

        for stage in self.state.current_roadmap.stages:
            if stage.id == self.state.active_stage_id:
                return stage
        return None

    def get_next_pending_stage(self) -> Optional[Stage]:
        """Get the next pending stage in the roadmap."""
        if self.state is None:
            return None

        for stage in self.state.current_roadmap.stages:
            if stage.status == "pending":
                return stage
        return None

    def start_stage(self, stage_id: str) -> Stage:
        """
        Mark a stage as active.

        Args:
            stage_id: ID of stage to activate

        Returns:
            The activated Stage

        Raises:
            ValueError: If stage not found or already active
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        stage = self._find_stage(stage_id)
        if stage.status != "pending" and stage.status != "reopened":
            raise ValueError(f"Cannot start stage {stage_id} with status {stage.status}")

        stage.status = "active"
        self.state.active_stage_id = stage_id
        self._save()
        return stage

    def complete_stage(self, stage_id: str) -> Stage:
        """
        Mark a stage as completed.

        Args:
            stage_id: ID of stage to complete

        Returns:
            The completed Stage

        Raises:
            ValueError: If stage not found or not active
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        stage = self._find_stage(stage_id)
        if stage.status != "active":
            raise ValueError(f"Cannot complete stage {stage_id} with status {stage.status}")

        stage.status = "completed"
        stage.completed_at = time.time()
        self.state.active_stage_id = None
        self._save()
        return stage

    def increment_audit_count(self, stage_id: str) -> int:
        """
        Increment the audit count for a stage.

        Args:
            stage_id: ID of stage

        Returns:
            New audit count
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        stage = self._find_stage(stage_id)
        stage.audit_count += 1
        self._save()
        return stage.audit_count

    # ──────────────────────────────────────────────────────────────────
    # Roadmap Mutations
    # ──────────────────────────────────────────────────────────────────

    def merge_stages(
        self,
        stage_ids: List[str],
        new_name: str,
        reason: str,
        created_by: str = "manager"
    ) -> Roadmap:
        """
        Merge multiple stages into one.

        Args:
            stage_ids: List of stage IDs to merge (must be consecutive)
            new_name: Name for the merged stage
            reason: Reason for merging
            created_by: Agent requesting merge

        Returns:
            New Roadmap version

        Raises:
            ValueError: If stages are not consecutive or don't exist
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        current_roadmap = self.state.current_roadmap
        stages_to_merge = [self._find_stage(sid) for sid in stage_ids]

        # Validate stages are consecutive
        indices = [current_roadmap.stages.index(s) for s in stages_to_merge]
        if sorted(indices) != list(range(min(indices), max(indices) + 1)):
            raise ValueError("Stages to merge must be consecutive")

        # Create merged stage
        merged_stage = Stage(
            id=str(uuid.uuid4()),
            name=new_name,
            description=f"Merged from: {', '.join(s.name for s in stages_to_merge)}",
            categories=sum([s.categories for s in stages_to_merge], []),
            plan_steps=sum([s.plan_steps for s in stages_to_merge], []),
            status="pending",
        )

        # Build new stages list
        new_stages = []
        i = 0
        while i < len(current_roadmap.stages):
            if i == min(indices):
                # Replace first merged stage with merged stage
                new_stages.append(merged_stage)
                i = max(indices) + 1  # Skip all merged stages
            else:
                new_stages.append(current_roadmap.stages[i])
                i += 1

        # Create new roadmap version
        new_roadmap = Roadmap(
            version=current_roadmap.version + 1,
            stages=new_stages,
            created_by=created_by,
            mutation_type="merge",
            mutation_reason=reason,
        )

        self.state.roadmap_history.append(new_roadmap)
        self._save()
        return new_roadmap

    def split_stage(
        self,
        stage_id: str,
        split_plan: List[Dict[str, Any]],
        reason: str,
        created_by: str = "manager"
    ) -> Roadmap:
        """
        Split a stage into multiple stages.

        Args:
            stage_id: ID of stage to split
            split_plan: List of dicts with {name, description, categories, plan_steps}
            reason: Reason for splitting
            created_by: Agent requesting split

        Returns:
            New Roadmap version
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        current_roadmap = self.state.current_roadmap
        stage_to_split = self._find_stage(stage_id)
        stage_index = current_roadmap.stages.index(stage_to_split)

        # Create new stages from split plan
        new_stages_list = []
        for sp in split_plan:
            new_stage = Stage(
                id=str(uuid.uuid4()),
                name=sp["name"],
                description=sp.get("description", ""),
                categories=sp.get("categories", []),
                plan_steps=sp.get("plan_steps", []),
                status="pending",
            )
            new_stages_list.append(new_stage)

        # Build new roadmap
        new_roadmap_stages = (
            current_roadmap.stages[:stage_index] +
            new_stages_list +
            current_roadmap.stages[stage_index + 1:]
        )

        new_roadmap = Roadmap(
            version=current_roadmap.version + 1,
            stages=new_roadmap_stages,
            created_by=created_by,
            mutation_type="split",
            mutation_reason=reason,
        )

        self.state.roadmap_history.append(new_roadmap)
        self._save()
        return new_roadmap

    def reopen_stage(
        self,
        stage_id: str,
        reason: str,
        regression_source_id: Optional[str] = None,
        created_by: str = "regression_detector"
    ) -> Stage:
        """
        Reopen a completed stage for rework.

        Args:
            stage_id: ID of stage to reopen
            reason: Reason for reopening
            regression_source_id: ID of stage that caused regression (if known)
            created_by: Agent requesting reopen

        Returns:
            The reopened Stage
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        stage = self._find_stage(stage_id)
        if stage.status != "completed":
            raise ValueError(f"Can only reopen completed stages, got {stage.status}")

        stage.status = "reopened"
        stage.regression_source = regression_source_id
        stage.audit_count = 0  # Reset audit count for rework

        # Create new roadmap version to record the reopen
        current_roadmap = self.state.current_roadmap
        new_roadmap = Roadmap(
            version=current_roadmap.version + 1,
            stages=current_roadmap.stages.copy(),
            created_by=created_by,
            mutation_type="reopen",
            mutation_reason=reason,
        )

        self.state.roadmap_history.append(new_roadmap)
        self._save()
        return stage

    def skip_stage(
        self,
        stage_id: str,
        reason: str,
        created_by: str = "manager"
    ) -> Stage:
        """
        Skip a pending stage.

        Args:
            stage_id: ID of stage to skip
            reason: Reason for skipping
            created_by: Agent requesting skip

        Returns:
            The skipped Stage
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        stage = self._find_stage(stage_id)
        if stage.status != "pending":
            raise ValueError(f"Can only skip pending stages, got {stage.status}")

        stage.status = "skipped"

        # Create new roadmap version
        current_roadmap = self.state.current_roadmap
        new_roadmap = Roadmap(
            version=current_roadmap.version + 1,
            stages=current_roadmap.stages.copy(),
            created_by=created_by,
            mutation_type="skip",
            mutation_reason=reason,
        )

        self.state.roadmap_history.append(new_roadmap)
        self._save()
        return stage

    # ──────────────────────────────────────────────────────────────────
    # Query Methods
    # ──────────────────────────────────────────────────────────────────

    def get_stage_summary(self, stage_id: str) -> Dict[str, Any]:
        """
        Get summary information about a stage.

        Returns:
            Dict with stage info and statistics
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        stage = self._find_stage(stage_id)
        duration = None
        if stage.completed_at and stage.created_at:
            duration = stage.completed_at - stage.created_at

        return {
            "id": stage.id,
            "name": stage.name,
            "status": stage.status,
            "audit_count": stage.audit_count,
            "duration_seconds": duration,
            "categories": stage.categories,
            "plan_steps": stage.plan_steps,
            "regression_source": stage.regression_source,
        }

    def get_roadmap_summary(self) -> Dict[str, Any]:
        """
        Get summary of current roadmap state.

        Returns:
            Dict with roadmap statistics
        """
        if self.state is None:
            raise ValueError("Workflow not initialized")

        roadmap = self.state.current_roadmap
        stages_by_status = {}
        for stage in roadmap.stages:
            stages_by_status.setdefault(stage.status, []).append(stage.name)

        return {
            "version": roadmap.version,
            "total_stages": len(roadmap.stages),
            "active_stage": self.get_active_stage().name if self.get_active_stage() else None,
            "stages_by_status": stages_by_status,
            "mutation_history": [
                {"version": v, "type": r.mutation_type, "reason": r.mutation_reason}
                for v, r in enumerate(self.state.roadmap_history, start=1)
            ],
        }

    # ──────────────────────────────────────────────────────────────────
    # Helper Methods
    # ──────────────────────────────────────────────────────────────────

    def _find_stage(self, stage_id: str) -> Stage:
        """Find stage by ID in current roadmap."""
        if self.state is None:
            raise ValueError("Workflow not initialized")

        for stage in self.state.current_roadmap.stages:
            if stage.id == stage_id:
                return stage
        raise ValueError(f"Stage not found: {stage_id}")


# ══════════════════════════════════════════════════════════════════════
# Public API Functions
# ══════════════════════════════════════════════════════════════════════


def create_workflow(
    run_id: str,
    plan_steps: List[str],
    supervisor_phases: List[Dict[str, Any]],
    task: str
) -> WorkflowManager:
    """
    Create and initialize a new workflow.

    Args:
        run_id: Unique run identifier
        plan_steps: Manager's plan steps
        supervisor_phases: Supervisor's phases
        task: Original task description

    Returns:
        Initialized WorkflowManager
    """
    manager = WorkflowManager(run_id)
    manager.initialize(plan_steps, supervisor_phases, task)
    return manager


def load_workflow(run_id: str) -> WorkflowManager:
    """
    Load an existing workflow from disk.

    Args:
        run_id: Unique run identifier

    Returns:
        WorkflowManager with loaded state
    """
    manager = WorkflowManager(run_id)
    manager.load()
    return manager
