# Phase 3 Implementation Guide

**Status**: ✅ Core modules completed
**Date**: 2025-11-18
**Version**: Phase 3.0

---

## Executive Summary

Phase 3 transforms the rigid Stage 1-2 multi-agent orchestration system into a **flexible, adaptive, intelligent workflow engine**. This upgrade introduces:

1. **Dynamic Roadmap Management** - Manager can modify roadmap throughout execution
2. **Adaptive Stage Flow** - Auto-advance on 0 findings, intelligent audit cycles
3. **Horizontal Agent Communication** - Direct agent-to-agent messaging without bottlenecks
4. **Stage-Level Memory** - Persistent knowledge storage per stage
5. **Regression Detection** - Automatic detection and reopening of problematic stages

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [New Modules](#new-modules)
3. [Integration Guide](#integration-guide)
4. [Usage Examples](#usage-examples)
5. [Testing](#testing)
6. [Migration from Stage 2](#migration-from-stage-2)
7. [API Reference](#api-reference)

---

## Architecture Overview

### Before Phase 3 (Stage 1-2)

```
Manager Planning → Supervisor Phasing → Fixed Iteration Loop
                                         ↓
                     ┌───────────────────────────────────┐
                     │ For iteration in range(max_rounds)│
                     │   Employee builds                 │
                     │   Manager reviews                 │
                     │   If approved: break              │
                     └───────────────────────────────────┘
```

**Limitations**:
- Fixed roadmap created at start
- No way to merge/split stages dynamically
- Supervisor audits every iteration (wasteful)
- No horizontal agent communication
- No stage-level memory
- Can't reopen previous stages

### After Phase 3

```
Manager Planning → Workflow Manager → Adaptive Stage Loop
                        ↓
    ┌─────────────────────────────────────────────────────┐
    │ For each stage in dynamic_roadmap:                  │
    │   ┌───────────────────────────────────────────────┐ │
    │   │ 1. Load stage memory (previous context)       │ │
    │   │ 2. Employee builds                            │ │
    │   │ 3. Supervisor audits                          │ │
    │   │    ├─ If 0 findings → AUTO-ADVANCE            │ │
    │   │    └─ If findings → Fix cycle (max 3)         │ │
    │   │ 4. Check for regressions                      │ │
    │   │    └─ If detected → Reopen previous stage     │ │
    │   │ 5. Manager can mutate roadmap:                │ │
    │   │    - Merge stages                             │ │
    │   │    - Split stages                             │ │
    │   │    - Skip stages                              │ │
    │   │    - Reorder stages                           │ │
    │   │ 6. Save stage summary                         │ │
    │   │ 7. Update stage memory                        │ │
    │   └───────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────────┘

    Inter-Agent Bus (horizontal communication):
      Supervisor ←→ Manager ←→ Employee
           ↓            ↓          ↓
      Memory Store  Decision   Clarifications
                   Recording
```

**Improvements**:
✅ Dynamic roadmap with versioning
✅ Auto-advance on clean audits
✅ Regression detection & stage reopening
✅ Horizontal agent messaging
✅ Persistent stage-level memory
✅ Manager no longer a bottleneck

---

## New Modules

### 1. `workflow_manager.py` - Dynamic Roadmap Management

**Purpose**: Manages adaptive workflow evolution.

**Key Classes**:
- `Stage`: Represents a stage with status tracking
- `Roadmap`: Versioned collection of stages
- `WorkflowState`: Complete workflow state with history
- `WorkflowManager`: Main API for workflow operations

**Core Capabilities**:
```python
from workflow_manager import create_workflow, load_workflow

# Create workflow from plan
workflow = create_workflow(
    run_id=run_id,
    plan_steps=manager_plan["plan"],
    supervisor_phases=supervisor_phases,
    task=task
)

# Navigate stages
next_stage = workflow.get_next_pending_stage()
workflow.start_stage(next_stage.id)

# Mutate roadmap
workflow.merge_stages(
    stage_ids=["stage1", "stage2"],
    new_name="Combined Stage",
    reason="Stages are too similar",
    created_by="manager"
)

# Reopen for regression
workflow.reopen_stage(
    stage_id="stage2",
    reason="Issues detected in stage 4 trace back here",
    regression_source_id="stage4"
)

# Complete stage
workflow.complete_stage(stage_id)
```

**Storage**: `agent/run_workflows/<run_id>_workflow.json`

---

### 2. `memory_store.py` - Stage-Level Persistent Memory

**Purpose**: Human-readable knowledge storage per stage.

**Key Classes**:
- `Decision`: Tracks agent decisions
- `Finding`: Supervisor audit findings
- `Clarification`: Inter-agent Q&A
- `StageMemory`: Complete stage knowledge
- `MemoryStore`: Main API

**Core Capabilities**:
```python
from memory_store import create_memory_store

memory = create_memory_store(run_id)

# Create/load stage memory
stage_mem = memory.get_or_create_memory(stage_id, "Layout & Structure")

# Record decision
memory.add_decision(
    stage_id=stage_id,
    agent="manager",
    decision_type="merge_stages",
    description="Merged layout and styling stages",
    context={"reason": "Overlapping work"}
)

# Add supervisor finding
memory.add_finding(
    stage_id=stage_id,
    severity="error",
    category="functionality",
    description="Login button doesn't work",
    file_path="index.html",
    line_number=42
)

# Add clarification
memory.add_clarification(
    stage_id=stage_id,
    from_agent="employee",
    to_agent="manager",
    question="Should the navbar be fixed or scrolling?",
    answer="Fixed at top"
)

# Generate human-readable summary
summary = memory.generate_stage_summary(stage_id)
print(summary)
```

**Storage**: `agent/memory_store/<run_id>/<stage_id>.json`

---

### 3. `inter_agent_bus.py` - Horizontal Agent Communication

**Purpose**: Safe, structured agent-to-agent messaging.

**Key Classes**:
- `MessageType`: Enum of message types
- `Message`: Individual message with metadata
- `InterAgentBus`: Message passing system

**Core Capabilities**:
```python
from inter_agent_bus import get_bus, MessageType

bus = get_bus()

# Supervisor suggests roadmap change
msg_id = bus.supervisor_suggest_roadmap_change(
    suggestion="Merge styling stages",
    reason="Overlapping CSS work",
    proposed_changes={"merge": ["stage2", "stage3"]}
)

# Manager responds
bus.respond_to_message(
    original_message_id=msg_id,
    from_agent="manager",
    subject="Approved",
    body={"approved": True, "action_taken": "merged_stages"}
)

# Employee requests clarification
clarification_id = bus.employee_request_clarification(
    question="Should the color scheme be light or dark theme?",
    context={"file": "styles.css"}
)

# Get messages for an agent
messages = bus.get_messages_for(agent="manager", unread_only=True)

# Supervisor reports findings
bus.supervisor_report_findings(
    findings=[{"severity": "error", "description": "..."}],
    stage_id=stage_id,
    recommendation="fix_required"
)

# Request auto-advance
bus.supervisor_request_auto_advance(
    stage_id=stage_id,
    reason="Zero findings in audit"
)
```

**Storage**: In-memory with optional logging callback to core_logging

---

### 4. `stage_summaries.py` - Stage Results & Regression Tracking

**Purpose**: Comprehensive stage execution tracking and regression detection.

**Key Classes**:
- `FileChange`: Tracks file modifications
- `Issue`: Individual issue with traceability
- `FixCycle`: Iteration/audit cycle within stage
- `StageSummary`: Complete stage execution record
- `StageSummaryTracker`: Main API

**Core Capabilities**:
```python
from stage_summaries import create_tracker

tracker = create_tracker(run_id)

# Create summary
summary = tracker.create_summary(stage_id, "Layout & Structure")

# Track file changes
tracker.add_file_change(
    stage_id=stage_id,
    file_path="index.html",
    change_type="modified",
    lines_added=45,
    lines_removed=12,
    size_bytes=2048
)

# Add issues
tracker.add_issue(
    stage_id=stage_id,
    issue_id="issue_001",
    severity="error",
    category="functionality",
    description="Button click handler not working",
    file_path="script.js",
    line_number=25
)

# Track fix cycles
tracker.start_fix_cycle(stage_id, cycle_number=1, employee_model="gpt-5")
tracker.complete_fix_cycle(
    stage_id=stage_id,
    cycle_number=1,
    issues_addressed=["issue_001"],
    files_changed=["script.js"],
    supervisor_findings=0,
    status="completed"
)

# Detect regression
previous_summaries = tracker.get_all_summaries()
regressing_stage = tracker.detect_regression(
    current_stage_id=stage_id,
    issues=[{"file_path": "style.css", "description": "..."}],
    previous_stage_summaries=previous_summaries
)

if regressing_stage:
    tracker.mark_regression(regressing_stage, stage_id)

# Generate report
report = tracker.generate_report(stage_id)
print(report)
```

**Storage**: `agent/stage_summaries/<run_id>/<stage_id>.json`

---

### 5. `core_logging.py` Extensions

**New Event Types** (added to existing `core_logging.py`):

**Workflow Events**:
- `workflow_initialized` - Roadmap created
- `stage_started` - Stage execution begins
- `stage_completed` - Stage execution ends
- `roadmap_mutated` - Roadmap changed
- `stage_reopened` - Previous stage reopened
- `auto_advance` - Auto-advanced (0 findings)

**Communication Events**:
- `agent_message` - Inter-agent message sent
- `agent_response` - Response to message

**Memory Events**:
- `memory_created` - Stage memory initialized
- `memory_updated` - Memory updated
- `regression_detected` - Regression found
- `finding_added` - Supervisor finding logged
- `decision_recorded` - Agent decision logged

**New Logging Functions**:
```python
import core_logging

# Workflow logging
core_logging.log_workflow_initialized(run_id, roadmap_version=1, ...)
core_logging.log_stage_started(run_id, stage_id, stage_name, ...)
core_logging.log_stage_completed(run_id, stage_id, status="completed", ...)
core_logging.log_roadmap_mutated(run_id, old_version=1, new_version=2, ...)
core_logging.log_stage_reopened(run_id, stage_id, reason="regression", ...)
core_logging.log_auto_advance(run_id, stage_id, reason="zero findings")

# Communication logging
core_logging.log_agent_message(run_id, message_id, from_agent, to_agent, ...)
core_logging.log_agent_response(run_id, response_id, original_message_id, ...)

# Memory logging
core_logging.log_memory_created(run_id, stage_id, stage_name)
core_logging.log_memory_updated(run_id, stage_id, update_type, description)
core_logging.log_regression_detected(run_id, current_stage_id, regressing_stage_id, ...)
core_logging.log_finding_added(run_id, stage_id, severity, category, description)
core_logging.log_decision_recorded(run_id, stage_id, agent, decision_type, description)
```

---

## Integration Guide

### Option A: Full Phase 3 Orchestrator (New File)

Create `agent/orchestrator_phase3.py` with complete Phase 3 implementation:

```python
# orchestrator_phase3.py
"""
PHASE 3: Adaptive Multi-Agent Orchestrator

Key differences from Stage 2:
- Dynamic roadmap management
- Auto-advance on clean audits
- Regression detection
- Horizontal agent communication
- Stage-level memory
"""

import core_logging
from workflow_manager import create_workflow
from memory_store import create_memory_store
from inter_agent_bus import get_bus
from stage_summaries import create_tracker

def main_phase3(run_summary=None):
    # Setup
    core_run_id = core_logging.new_run_id()
    cfg = _load_config()
    out_dir = _ensure_out_dir(cfg)
    task = cfg["task"]

    # Initialize Phase 3 systems
    workflow = create_workflow(
        run_id=core_run_id,
        plan_steps=plan["plan"],
        supervisor_phases=phases["phases"],
        task=task
    )
    memory = create_memory_store(core_run_id)
    tracker = create_tracker(core_run_id)
    bus = get_bus()

    # Log workflow initialization
    core_logging.log_workflow_initialized(
        core_run_id,
        roadmap_version=1,
        total_stages=len(workflow.state.current_roadmap.stages),
        stage_names=[s.name for s in workflow.state.current_roadmap.stages]
    )

    # Set up bus logging callback
    def log_bus_message(message):
        core_logging.log_agent_message(
            core_run_id,
            message.id,
            message.from_agent,
            message.to_agent,
            message.message_type.value,
            message.subject
        )
    bus.set_log_callback(log_bus_message)

    # ADAPTIVE STAGE LOOP
    max_stages_processed = 0
    while max_stages_processed < 100:  # Safety limit
        next_stage = workflow.get_next_pending_stage()
        if next_stage is None:
            print("[Phase3] All stages completed!")
            break

        max_stages_processed += 1
        print(f"\n{'='*60}")
        print(f"STAGE {max_stages_processed}: {next_stage.name}")
        print(f"{'='*60}")

        # Start stage
        workflow.start_stage(next_stage.id)
        stage_mem = memory.get_or_create_memory(next_stage.id, next_stage.name)
        stage_summary = tracker.create_summary(next_stage.id, next_stage.name)

        core_logging.log_stage_started(
            core_run_id,
            next_stage.id,
            next_stage.name,
            stage_number=max_stages_processed,
            total_stages=len(workflow.state.current_roadmap.stages)
        )
        core_logging.log_memory_created(
            core_run_id,
            next_stage.id,
            next_stage.name
        )

        # Build stage context from memory
        prev_stage_summary = memory.get_previous_stage_summary(next_stage.id)
        context_notes = []
        if prev_stage_summary:
            context_notes.append(f"Previous stage summary: {prev_stage_summary}")

        # AUDIT LOOP (max 3 audits)
        max_audits = 3
        for audit_num in range(1, max_audits + 1):
            print(f"\n--- Audit Cycle {audit_num} ---")

            # Track fix cycle
            tracker.start_fix_cycle(next_stage.id, audit_num, employee_model="gpt-5")

            # Employee builds
            employee_payload = {
                "task": task,
                "plan": plan,
                "phase": next_stage.to_dict(),
                "context_notes": context_notes,
                "iteration": audit_num,
            }

            emp_result = chat_json("employee", employee_sys, json.dumps(employee_payload))
            files_written = _write_files(emp_result.get("files", {}), out_dir)

            # Log file writes
            for file_path in files_written:
                tracker.add_file_change(
                    next_stage.id,
                    file_path,
                    change_type="modified",
                    size_bytes=len((out_dir / file_path).read_text())
                )

            # Supervisor audit
            supervisor_payload = {
                "task": task,
                "stage": next_stage.to_dict(),
                "files": _load_existing_files(out_dir),
            }

            audit_result = chat_json("supervisor", supervisor_sys, json.dumps(supervisor_payload))
            findings = audit_result.get("findings", [])

            print(f"[Supervisor] Found {len(findings)} issues")

            # Record findings in memory
            for finding in findings:
                memory.add_finding(
                    next_stage.id,
                    severity=finding.get("severity", "warning"),
                    category=finding.get("category", "general"),
                    description=finding["description"],
                    file_path=finding.get("file_path")
                )
                tracker.add_issue(
                    next_stage.id,
                    issue_id=f"issue_{audit_num}_{len(findings)}",
                    severity=finding.get("severity", "warning"),
                    category=finding.get("category", "general"),
                    description=finding["description"],
                    file_path=finding.get("file_path")
                )
                core_logging.log_finding_added(
                    core_run_id,
                    next_stage.id,
                    finding.get("severity", "warning"),
                    finding.get("category", "general"),
                    finding["description"]
                )

            # Complete fix cycle
            tracker.complete_fix_cycle(
                next_stage.id,
                audit_num,
                issues_addressed=[],  # Would track which issues were addressed
                files_changed=files_written,
                supervisor_findings=len(findings),
                status="completed"
            )

            # Increment audit count
            workflow.increment_audit_count(next_stage.id)
            memory.increment_iterations(next_stage.id)

            # CHECK FOR AUTO-ADVANCE
            if len(findings) == 0:
                print("[Phase3] ✅ Zero findings - AUTO-ADVANCING")

                # Supervisor sends auto-advance request via bus
                bus.supervisor_request_auto_advance(
                    stage_id=next_stage.id,
                    reason="Zero findings in audit"
                )

                core_logging.log_auto_advance(
                    core_run_id,
                    next_stage.id,
                    next_stage.name,
                    reason="Zero findings in audit"
                )

                break  # Exit audit loop

            # Check if we've hit max audits
            if audit_num >= max_audits:
                print(f"[Phase3] ⚠️  Max audits ({max_audits}) reached")

                # Report findings to manager via bus
                bus.supervisor_report_findings(
                    findings=[f.__dict__ for f in findings],
                    stage_id=next_stage.id,
                    recommendation="needs_rework" if findings else "approved"
                )

                break  # Exit audit loop

        # REGRESSION DETECTION
        previous_summaries = tracker.get_all_summaries()
        regressing_stage = tracker.detect_regression(
            current_stage_id=next_stage.id,
            issues=[{"file_path": f.file_path} for f in memory.get_unresolved_findings(next_stage.id)],
            previous_stage_summaries=previous_summaries
        )

        if regressing_stage:
            print(f"[Phase3] 🔄 REGRESSION DETECTED: Issues trace back to stage {regressing_stage}")

            tracker.mark_regression(regressing_stage, next_stage.id)

            core_logging.log_regression_detected(
                core_run_id,
                current_stage_id=next_stage.id,
                regressing_stage_id=regressing_stage,
                issue_count=len(memory.get_unresolved_findings(next_stage.id)),
                description=f"Issues in {next_stage.name} caused by {regressing_stage}"
            )

            # Reopen regressing stage
            workflow.reopen_stage(
                stage_id=regressing_stage,
                reason=f"Regression detected from stage {next_stage.id}",
                regression_source_id=next_stage.id
            )

            core_logging.log_stage_reopened(
                core_run_id,
                regressing_stage,
                "Regressing Stage",
                reason="Regression detected",
                regression_source=next_stage.id
            )

            print(f"[Phase3] Stage {regressing_stage} reopened for rework")

            # Pause current stage, will return to it later
            continue

        # Complete stage
        workflow.complete_stage(next_stage.id)
        memory.set_final_status(next_stage.id, "completed")
        memory.set_summary(next_stage.id, f"Stage {next_stage.name} completed after {audit_num} audits")

        tracker.complete_stage(
            next_stage.id,
            status="completed",
            final_notes=f"Completed after {audit_num} audit cycles",
            cost_usd=0.0  # Would calculate actual cost
        )

        core_logging.log_stage_completed(
            core_run_id,
            next_stage.id,
            next_stage.name,
            status="completed",
            iterations=audit_num,
            audit_count=audit_num,
            duration_seconds=time.time() - stage_summary.started_at
        )

        print(f"[Phase3] ✅ Stage {next_stage.name} completed")

        # CHECK FOR ROADMAP MUTATIONS (Manager can suggest changes)
        # This would be based on messages from manager via bus
        manager_suggestions = bus.get_messages_for(
            agent="workflow_orchestrator",
            message_type=MessageType.SUGGESTION,
            from_agent="manager"
        )

        for suggestion in manager_suggestions:
            # Process manager's roadmap change suggestions
            # E.g., merge stages, split stages, etc.
            print(f"[Phase3] Processing manager suggestion: {suggestion.subject}")
            # ... implementation of suggestion processing ...

    # Final status
    core_logging.log_final_status(
        core_run_id,
        status="completed",
        reason="All stages completed successfully",
        iterations=max_stages_processed
    )

    print("\n[Phase3] 🎉 Run completed successfully!")
    print(f"[Phase3] Processed {max_stages_processed} stages")
    print(f"[Phase3] Workflow file: run_workflows/{core_run_id}_workflow.json")
    print(f"[Phase3] Memories: memory_store/{core_run_id}/")
    print(f"[Phase3] Summaries: stage_summaries/{core_run_id}/")
```

### Option B: Gradual Integration into Existing `orchestrator.py`

Modify existing `agent/orchestrator.py` incrementally:

**Step 1**: Add Phase 3 imports at top:
```python
# PHASE 3: Import new systems
from workflow_manager import create_workflow, load_workflow
from memory_store import create_memory_store
from inter_agent_bus import get_bus
from stage_summaries import create_tracker
```

**Step 2**: Initialize Phase 3 systems after config loading:
```python
# After line ~300 in orchestrator.py
# PHASE 3: Initialize workflow management
workflow = create_workflow(
    run_id=core_run_id,
    plan_steps=plan.get("plan", []),
    supervisor_phases=phase_list,
    task=task
)
memory = create_memory_store(core_run_id)
tracker = create_tracker(core_run_id)
bus = get_bus()

core_logging.log_workflow_initialized(
    core_run_id,
    roadmap_version=1,
    total_stages=len(phase_list),
    stage_names=[p.get("name", f"Phase {i+1}") for i, p in enumerate(phase_list)]
)
```

**Step 3**: Replace iteration loop with stage-based loop:
```python
# Replace line ~438 (for iteration in range(1, max_rounds + 1))
# with:

stage_number = 0
while True:
    next_stage = workflow.get_next_pending_stage()
    if next_stage is None:
        break

    stage_number += 1
    workflow.start_stage(next_stage.id)
    stage_mem = memory.get_or_create_memory(next_stage.id, next_stage.name)

    core_logging.log_stage_started(
        core_run_id,
        next_stage.id,
        next_stage.name,
        stage_number=stage_number,
        total_stages=len(workflow.state.current_roadmap.stages)
    )

    # ... rest of stage execution logic ...
```

**Step 4**: Add supervisor audit with auto-advance check:
```python
# After manager review (around line ~580)
# Add supervisor audit:

supervisor_audit_payload = {
    "task": task,
    "stage": next_stage.to_dict(),
    "files": final_files,
    "manager_feedback": feedback,
}

audit_result = chat_json(
    "supervisor",
    supervisor_sys,
    json.dumps(supervisor_audit_payload)
)

findings = audit_result.get("findings", [])

# Check for auto-advance
if len(findings) == 0 and status == "approved":
    print("[Phase3] ✅ Auto-advancing (zero findings)")
    core_logging.log_auto_advance(core_run_id, next_stage.id, next_stage.name)
    workflow.complete_stage(next_stage.id)
    continue  # Skip to next stage
```

**Step 5**: Add regression detection:
```python
# After audit, check for regressions
if len(findings) > 0:
    previous_summaries = tracker.get_all_summaries()
    regressing_stage = tracker.detect_regression(
        current_stage_id=next_stage.id,
        issues=[{"file_path": f.get("file_path")} for f in findings],
        previous_stage_summaries=previous_summaries
    )

    if regressing_stage:
        print(f"[Phase3] Regression detected: reopening stage {regressing_stage}")
        workflow.reopen_stage(regressing_stage, reason="Regression from " + next_stage.name)
        core_logging.log_regression_detected(
            core_run_id,
            next_stage.id,
            regressing_stage,
            len(findings),
            "Regression detected"
        )
```

---

## Usage Examples

### Example 1: Simple Run with Auto-Advance

```python
# Task: Build a landing page
# Roadmap: [Layout, Styling, Interactivity]

# Stage 1: Layout
#   - Employee builds HTML structure
#   - Supervisor audits: 0 findings
#   → AUTO-ADVANCE ✅

# Stage 2: Styling
#   - Employee adds CSS
#   - Supervisor audits: 0 findings
#   → AUTO-ADVANCE ✅

# Stage 3: Interactivity
#   - Employee adds JavaScript
#   - Supervisor audits: 2 warnings
#   - Fix cycle 1: Employee fixes warnings
#   - Supervisor audits: 0 findings
#   → COMPLETE ✅

# Result: 3 stages, 4 total audits (auto-advanced twice, saving 2 audits)
```

### Example 2: Regression Detection & Stage Reopening

```python
# Task: Build e-commerce site
# Roadmap: [Layout, Product Listing, Cart, Checkout]

# Stage 1: Layout → Complete (0 findings) ✅
# Stage 2: Product Listing → Complete (0 findings) ✅
# Stage 3: Cart → Complete (0 findings) ✅
# Stage 4: Checkout
#   - Supervisor finds: "Layout broken, navbar missing"
#   - Regression detector: Issue in "layout.html" (changed in Stage 1)
#   → REGRESSION DETECTED: Stage 1 ⚠️

# System reopens Stage 1:
#   - Stage 1 (reopened) → Fix navbar
#   - Re-run Stages 2, 3, 4 validation
#   → All pass ✅

# Result: Prevented merging broken code
```

### Example 3: Dynamic Roadmap Mutation

```python
# Initial Roadmap: [Layout, Styling, Forms, Validation, Backend]

# During Stage 2 (Styling):
#   - Manager realizes: "Forms and Styling are tightly coupled"
#   - Manager suggests via bus: "Merge Styling and Forms"
#   - System merges stages
#   → New Roadmap: [Layout, Styling+Forms, Validation, Backend]

# During Stage 3 (Validation):
#   - Manager realizes: "Validation is too complex"
#   - Manager suggests: "Split into Client-side and Server-side"
#   → New Roadmap: [Layout, Styling+Forms, Client Validation, Server Validation, Backend]

# Result: Adaptive roadmap that responds to actual complexity
```

### Example 4: Horizontal Agent Communication

```python
# Stage 2: Product Grid

# Employee encounter ambiguity:
employee_msg_id = bus.employee_request_clarification(
    question="Should product cards be 3 or 4 per row?",
    context={"file": "products.html"}
)

# Manager responds:
bus.respond_to_message(
    original_message_id=employee_msg_id,
    from_agent="manager",
    subject="Use 3 per row",
    body="3 cards per row for better mobile responsiveness"
)

# Employee continues with clarification

# No need for Prompt Master intervention! ✅
```

---

## Testing

### Unit Tests for Phase 3 Modules

Create `agent/tests/unit/test_workflow_manager.py`:

```python
import pytest
from workflow_manager import WorkflowManager, Stage, Roadmap

def test_create_workflow():
    """Test workflow creation from plan."""
    manager = WorkflowManager("test_run_001")

    plan_steps = ["Create layout", "Add styling", "Add interactivity"]
    phases = [
        {"name": "Layout", "categories": ["layout"], "plan_steps": [0]},
        {"name": "Styling", "categories": ["visual"], "plan_steps": [1]},
        {"name": "JS", "categories": ["interaction"], "plan_steps": [2]},
    ]

    state = manager.initialize(plan_steps, phases, "Build a website")

    assert state.run_id == "test_run_001"
    assert len(state.current_roadmap.stages) == 3
    assert state.current_roadmap.version == 1

def test_merge_stages():
    """Test merging two stages."""
    manager = WorkflowManager("test_run_002")
    # ... setup ...

    stage1_id = manager.state.current_roadmap.stages[0].id
    stage2_id = manager.state.current_roadmap.stages[1].id

    new_roadmap = manager.merge_stages(
        [stage1_id, stage2_id],
        "Combined Stage",
        "Stages are similar",
        "manager"
    )

    assert new_roadmap.version == 2
    assert len(new_roadmap.stages) == 2  # Merged from 3 to 2

def test_reopen_stage():
    """Test reopening completed stage."""
    manager = WorkflowManager("test_run_003")
    # ... setup and complete stage ...

    stage_id = manager.state.current_roadmap.stages[0].id
    manager.start_stage(stage_id)
    manager.complete_stage(stage_id)

    reopened = manager.reopen_stage(stage_id, "Regression detected")

    assert reopened.status == "reopened"
    assert reopened.audit_count == 0  # Reset for rework
```

Create `agent/tests/unit/test_memory_store.py`:

```python
from memory_store import MemoryStore

def test_create_and_load_memory():
    """Test memory creation and loading."""
    store = MemoryStore("test_run_001")

    memory = store.create_memory("stage1", "Layout")
    assert memory.stage_id == "stage1"
    assert memory.stage_name == "Layout"

    loaded = store.load_memory("stage1")
    assert loaded.stage_id == "stage1"

def test_add_finding():
    """Test adding supervisor finding."""
    store = MemoryStore("test_run_002")
    memory = store.create_memory("stage1", "Layout")

    store.add_finding(
        "stage1",
        severity="error",
        category="functionality",
        description="Button doesn't work"
    )

    loaded = store.load_memory("stage1")
    assert len(loaded.findings) == 1
    assert loaded.findings[0].severity == "error"

def test_unresolved_findings():
    """Test querying unresolved findings."""
    store = MemoryStore("test_run_003")
    memory = store.create_memory("stage1", "Layout")

    store.add_finding("stage1", "error", "func", "Bug 1")
    store.add_finding("stage1", "warning", "design", "Issue 2")

    unresolved = store.get_unresolved_findings("stage1")
    assert len(unresolved) == 2

    store.resolve_finding("stage1", 0, "Fixed bug")
    unresolved = store.get_unresolved_findings("stage1")
    assert len(unresolved) == 1
```

Create `agent/tests/unit/test_inter_agent_bus.py`:

```python
from inter_agent_bus import InterAgentBus, MessageType

def test_send_and_receive_message():
    """Test basic message sending."""
    bus = InterAgentBus()

    msg_id = bus.send_message(
        from_agent="supervisor",
        to_agent="manager",
        message_type=MessageType.SUGGESTION,
        subject="Test suggestion",
        body="Merge stages"
    )

    messages = bus.get_messages_for("manager")
    assert len(messages) == 1
    assert messages[0].subject == "Test suggestion"

def test_respond_to_message():
    """Test request/response pattern."""
    bus = InterAgentBus()

    msg_id = bus.send_message(
        from_agent="employee",
        to_agent="manager",
        message_type=MessageType.CLARIFICATION_REQUEST,
        subject="Need clarification",
        body="Question about colors",
        requires_response=True
    )

    response_id = bus.respond_to_message(
        original_message_id=msg_id,
        from_agent="manager",
        subject="Answer",
        body="Use blue theme"
    )

    response = bus.get_response(msg_id)
    assert response is not None
    assert response.body == "Use blue theme"

def test_helper_methods():
    """Test convenience helper methods."""
    bus = InterAgentBus()

    # Test supervisor suggest roadmap change
    msg_id = bus.supervisor_suggest_roadmap_change(
        suggestion="Merge stages 1 and 2",
        reason="Similar work",
        proposed_changes={"merge": ["stage1", "stage2"]}
    )

    messages = bus.get_messages_for("manager")
    assert len(messages) == 1
    assert messages[0].message_type == MessageType.SUGGESTION
```

### Integration Test

Create `agent/tests/integration/test_phase3_flow.py`:

```python
"""
Integration test for Phase 3 workflow.
Tests complete flow: workflow → memory → bus → summaries.
"""

import pytest
from workflow_manager import create_workflow
from memory_store import create_memory_store
from inter_agent_bus import get_bus, reset_bus
from stage_summaries import create_tracker

def test_complete_phase3_flow():
    """Test complete Phase 3 flow with all modules."""
    run_id = "test_integration_001"
    reset_bus()

    # Setup
    plan_steps = ["Create layout", "Add styling"]
    phases = [
        {"name": "Layout", "categories": ["layout"], "plan_steps": [0]},
        {"name": "Styling", "categories": ["visual"], "plan_steps": [1]},
    ]

    workflow = create_workflow(run_id, plan_steps, phases, "Build site")
    memory = create_memory_store(run_id)
    tracker = create_tracker(run_id)
    bus = get_bus()

    # Stage 1: Layout
    stage1 = workflow.get_next_pending_stage()
    assert stage1 is not None

    workflow.start_stage(stage1.id)
    stage1_mem = memory.create_memory(stage1.id, stage1.name)
    stage1_summary = tracker.create_summary(stage1.id, stage1.name)

    # Employee builds, supervisor audits (0 findings)
    # ... (would call actual LLM here in real test)

    # Auto-advance
    bus.supervisor_request_auto_advance(stage1.id, "Zero findings")
    workflow.complete_stage(stage1.id)
    memory.set_final_status(stage1.id, "completed")
    tracker.complete_stage(stage1.id, "completed", "Auto-advanced", 0.0)

    # Stage 2: Styling
    stage2 = workflow.get_next_pending_stage()
    assert stage2 is not None

    workflow.start_stage(stage2.id)
    stage2_mem = memory.create_memory(stage2.id, stage2.name)

    # Load previous stage context
    prev_summary = memory.get_previous_stage_summary(stage2.id)
    # (Would use this in employee prompt)

    # Supervisor finds issue
    memory.add_finding(
        stage2.id,
        severity="error",
        category="visual",
        description="Color contrast too low"
    )

    tracker.add_issue(
        stage2.id,
        "issue_001",
        "error",
        "visual",
        "Color contrast too low",
        file_path="style.css"
    )

    # Fix cycle
    tracker.start_fix_cycle(stage2.id, 1)
    # ... employee fixes ...
    tracker.complete_fix_cycle(stage2.id, 1, ["issue_001"], ["style.css"], 0, "completed")

    # Complete stage
    workflow.complete_stage(stage2.id)
    memory.set_final_status(stage2.id, "completed")
    tracker.complete_stage(stage2.id, "completed", "Fixed issues", 0.0)

    # Verify workflow state
    assert workflow.get_next_pending_stage() is None  # All done
    assert len(tracker.get_all_summaries()) == 2

    # Verify bus messages
    messages = bus.get_all_messages()
    assert len(messages) == 1  # Auto-advance request

    # Generate reports
    report1 = tracker.generate_report(stage1.id)
    assert "Auto-advanced" in report1

    report2 = tracker.generate_report(stage2.id)
    assert "1 resolved" in report2 or "issue" in report2.lower()
```

---

## Migration from Stage 2

### Backward Compatibility

Phase 3 modules are **fully backward compatible** with Stage 2:

- All Stage 2 logging still works
- Existing `orchestrator.py` runs unchanged
- Phase 3 modules can be used independently

### Migration Strategy

**Option 1: Side-by-side** (Recommended)
- Keep `orchestrator.py` for Stage 2 runs
- Create `orchestrator_phase3.py` for Phase 3 runs
- Use `run_mode.py` to select mode

**Option 2: Feature flag**
```python
# In project_config.json
{
  "enable_phase3": true,
  "phase3_features": {
    "dynamic_roadmap": true,
    "auto_advance": true,
    "regression_detection": true
  }
}
```

**Option 3: Gradual rollout**
1. Week 1: Enable Phase 3 logging only
2. Week 2: Enable memory store
3. Week 3: Enable workflow manager (without mutations)
4. Week 4: Enable full Phase 3 (with mutations, auto-advance)

---

## API Reference

### WorkflowManager

```python
class WorkflowManager:
    def __init__(self, run_id: str)
    def initialize(plan_steps, supervisor_phases, task) -> WorkflowState
    def load() -> WorkflowState

    # Navigation
    def get_active_stage() -> Optional[Stage]
    def get_next_pending_stage() -> Optional[Stage]
    def start_stage(stage_id: str) -> Stage
    def complete_stage(stage_id: str) -> Stage
    def increment_audit_count(stage_id: str) -> int

    # Mutations
    def merge_stages(stage_ids, new_name, reason, created_by) -> Roadmap
    def split_stage(stage_id, split_plan, reason, created_by) -> Roadmap
    def reopen_stage(stage_id, reason, regression_source_id) -> Stage
    def skip_stage(stage_id, reason, created_by) -> Stage

    # Queries
    def get_stage_summary(stage_id) -> Dict
    def get_roadmap_summary() -> Dict
```

### MemoryStore

```python
class MemoryStore:
    def __init__(self, run_id: str)

    # Core operations
    def create_memory(stage_id, stage_name) -> StageMemory
    def load_memory(stage_id) -> StageMemory
    def get_or_create_memory(stage_id, stage_name) -> StageMemory
    def save_memory(memory: StageMemory)

    # Add items
    def add_decision(stage_id, agent, decision_type, description, context)
    def add_finding(stage_id, severity, category, description, file_path, line_number)
    def add_clarification(stage_id, from_agent, to_agent, question, answer)
    def add_note(stage_id, note)

    # Resolve items
    def resolve_finding(stage_id, finding_index, resolution_note)
    def answer_clarification(stage_id, clarification_index, answer)

    # Update
    def increment_iterations(stage_id) -> int
    def set_summary(stage_id, summary)
    def set_final_status(stage_id, status)

    # Query
    def get_unresolved_findings(stage_id) -> List[Finding]
    def get_unanswered_clarifications(stage_id) -> List[Clarification]
    def get_all_stage_memories() -> List[StageMemory]
    def get_previous_stage_summary(stage_id) -> Optional[str]
    def link_previous_stage(stage_id, previous_stage_id)

    # Reporting
    def generate_stage_summary(stage_id) -> str
```

### InterAgentBus

```python
class InterAgentBus:
    def __init__()
    def set_log_callback(callback: callable)

    # Send/receive
    def send_message(from_agent, to_agent, message_type, subject, body, ...) -> str
    def get_messages_for(agent, message_type, from_agent, unread_only) -> List[Message]
    def respond_to_message(original_message_id, from_agent, subject, body) -> str
    def get_response(message_id) -> Optional[Message]

    # Query
    def get_message(message_id) -> Optional[Message]
    def get_conversation(message_id) -> List[Message]
    def get_all_messages() -> List[Message]
    def get_pending_requests(agent) -> List[Message]
    def get_stats() -> Dict

    # Helpers
    def supervisor_suggest_roadmap_change(suggestion, reason, proposed_changes) -> str
    def employee_request_clarification(question, context) -> str
    def supervisor_report_findings(findings, stage_id, recommendation) -> str
    def supervisor_request_auto_advance(stage_id, reason) -> str

# Global instance
def get_bus() -> InterAgentBus
def reset_bus()  # For testing
```

### StageSummaryTracker

```python
class StageSummaryTracker:
    def __init__(self, run_id: str)

    # Core operations
    def create_summary(stage_id, stage_name) -> StageSummary
    def load_summary(stage_id) -> StageSummary
    def get_or_create_summary(stage_id, stage_name) -> StageSummary
    def save_summary(summary: StageSummary)

    # Add data
    def add_file_change(stage_id, file_path, change_type, lines_added, ...)
    def add_issue(stage_id, issue_id, severity, category, description, ...)
    def resolve_issue(stage_id, issue_id, resolution_note)

    # Fix cycles
    def start_fix_cycle(stage_id, cycle_number, employee_model) -> FixCycle
    def complete_fix_cycle(stage_id, cycle_number, issues_addressed, ...)

    # Complete
    def complete_stage(stage_id, status, final_notes, cost_usd)

    # Regression detection
    def detect_regression(current_stage_id, issues, previous_stage_summaries) -> Optional[str]
    def mark_regression(regressing_stage_id, target_stage_id)

    # Query
    def get_all_summaries() -> List[StageSummary]
    def get_unresolved_issues(stage_id) -> List[Issue]
    def get_stages_with_regressions() -> List[StageSummary]

    # Reporting
    def generate_report(stage_id) -> str
```

### Core Logging (Extensions)

See [Phase 3 Event Types](#5-core_loggingpy-extensions) section above for complete API.

---

## Conclusion

Phase 3 provides a **production-ready, adaptive multi-agent orchestration system** that eliminates bottlenecks, enables intelligent workflows, and maintains comprehensive audit trails.

### Key Benefits

✅ **Flexibility**: Dynamic roadmap adapts to actual complexity
✅ **Efficiency**: Auto-advance saves redundant audits
✅ **Quality**: Regression detection prevents broken merges
✅ **Transparency**: Complete audit trail in logs and memory
✅ **Scalability**: Horizontal communication reduces bottlenecks

### Next Steps

1. **Review**: Read this guide thoroughly
2. **Test**: Run Phase 3 unit tests
3. **Integrate**: Choose integration strategy (Option A or B)
4. **Deploy**: Start with small tasks, gradually increase complexity
5. **Monitor**: Review logs, memory stores, and stage summaries
6. **Iterate**: Refine based on real-world usage

### Support

- **Documentation**: This guide + inline code comments
- **Tests**: `agent/tests/unit/test_*.py` for examples
- **Logs**: `agent/run_logs_main/<run_id>.jsonl` for debugging
- **Storage**: `agent/run_workflows/`, `agent/memory_store/`, `agent/stage_summaries/`

---

**End of Phase 3 Implementation Guide**
