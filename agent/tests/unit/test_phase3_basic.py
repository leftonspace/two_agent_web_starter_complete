# test_phase3_basic.py
"""
Basic sanity tests for Phase 3 modules.

Tests basic functionality of:
- workflow_manager
- memory_store
- inter_agent_bus
- stage_summaries
- core_logging Phase 3 extensions
"""

import pytest
from pathlib import Path
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

def test_workflow_manager_import():
    """Test that workflow_manager can be imported."""
    from workflow_manager import WorkflowManager, Stage, Roadmap, create_workflow
    assert WorkflowManager is not None
    assert Stage is not None
    assert Roadmap is not None

def test_workflow_manager_basic():
    """Test basic workflow manager operations."""
    from workflow_manager import WorkflowManager

    manager = WorkflowManager("test_run_001")

    plan_steps = ["Step 1", "Step 2", "Step 3"]
    phases = [
        {"name": "Phase 1", "categories": ["layout"], "plan_steps": [0, 1]},
        {"name": "Phase 2", "categories": ["visual"], "plan_steps": [2]},
    ]

    state = manager.initialize(plan_steps, phases, "Test task")

    assert state.run_id == "test_run_001"
    assert len(state.current_roadmap.stages) == 2
    assert state.current_roadmap.version == 1

    # Get next stage
    next_stage = manager.get_next_pending_stage()
    assert next_stage is not None
    assert next_stage.status == "pending"

    # Start stage
    started = manager.start_stage(next_stage.id)
    assert started.status == "active"

    # Complete stage
    completed = manager.complete_stage(next_stage.id)
    assert completed.status == "completed"

def test_memory_store_import():
    """Test that memory_store can be imported."""
    from memory_store import MemoryStore, StageMemory, Decision, Finding
    assert MemoryStore is not None
    assert StageMemory is not None

def test_memory_store_basic():
    """Test basic memory store operations."""
    from memory_store import MemoryStore

    store = MemoryStore("test_run_002")

    # Create memory
    memory = store.create_memory("stage1", "Test Stage")
    assert memory.stage_id == "stage1"
    assert memory.stage_name == "Test Stage"

    # Add decision
    store.add_decision(
        "stage1",
        agent="manager",
        decision_type="merge",
        description="Merge two stages"
    )

    # Load memory
    loaded = store.load_memory("stage1")
    assert len(loaded.decisions) == 1
    assert loaded.decisions[0].agent == "manager"

    # Add finding
    store.add_finding(
        "stage1",
        severity="error",
        category="functionality",
        description="Button doesn't work"
    )

    loaded = store.load_memory("stage1")
    assert len(loaded.findings) == 1
    assert loaded.findings[0].severity == "error"

def test_inter_agent_bus_import():
    """Test that inter_agent_bus can be imported."""
    from inter_agent_bus import InterAgentBus, MessageType, Message, get_bus
    assert InterAgentBus is not None
    assert MessageType is not None
    assert get_bus is not None

def test_inter_agent_bus_basic():
    """Test basic inter-agent bus operations."""
    from inter_agent_bus import InterAgentBus, MessageType

    bus = InterAgentBus()

    # Send message
    msg_id = bus.send_message(
        from_agent="supervisor",
        to_agent="manager",
        message_type=MessageType.SUGGESTION,
        subject="Test suggestion",
        body="Merge stages"
    )

    assert msg_id is not None

    # Get messages
    messages = bus.get_messages_for("manager")
    assert len(messages) == 1
    assert messages[0].subject == "Test suggestion"

    # Respond
    response_id = bus.respond_to_message(
        original_message_id=msg_id,
        from_agent="manager",
        subject="Approved",
        body="Sounds good"
    )

    assert response_id is not None

    # Get response
    response = bus.get_response(msg_id)
    assert response is not None
    assert response.body == "Sounds good"

def test_stage_summaries_import():
    """Test that stage_summaries can be imported."""
    from stage_summaries import StageSummaryTracker, StageSummary, Issue, FixCycle
    assert StageSummaryTracker is not None
    assert StageSummary is not None

def test_stage_summaries_basic():
    """Test basic stage summary operations."""
    from stage_summaries import StageSummaryTracker

    tracker = StageSummaryTracker("test_run_003")

    # Create summary
    summary = tracker.create_summary("stage1", "Test Stage")
    assert summary.stage_id == "stage1"
    assert summary.stage_name == "Test Stage"

    # Add file change
    tracker.add_file_change(
        "stage1",
        file_path="index.html",
        change_type="created",
        lines_added=50,
        size_bytes=1024
    )

    # Load summary
    loaded = tracker.load_summary("stage1")
    assert len(loaded.files_changed) == 1
    assert loaded.files_changed[0].file_path == "index.html"

    # Add issue
    tracker.add_issue(
        "stage1",
        issue_id="issue_001",
        severity="error",
        category="functionality",
        description="Test issue"
    )

    loaded = tracker.load_summary("stage1")
    assert len(loaded.issues) == 1
    assert loaded.issues[0].id == "issue_001"

def test_core_logging_phase3_imports():
    """Test that Phase 3 core_logging extensions can be imported."""
    import core_logging

    # Test Phase 3 functions exist
    assert hasattr(core_logging, 'log_workflow_initialized')
    assert hasattr(core_logging, 'log_stage_started')
    assert hasattr(core_logging, 'log_stage_completed')
    assert hasattr(core_logging, 'log_roadmap_mutated')
    assert hasattr(core_logging, 'log_stage_reopened')
    assert hasattr(core_logging, 'log_auto_advance')
    assert hasattr(core_logging, 'log_agent_message')
    assert hasattr(core_logging, 'log_agent_response')
    assert hasattr(core_logging, 'log_memory_created')
    assert hasattr(core_logging, 'log_regression_detected')

def test_phase3_event_types():
    """Test that Phase 3 event types are registered."""
    import core_logging

    # Check Phase 3 event types exist
    assert "workflow_initialized" in core_logging.EVENT_TYPES
    assert "stage_started" in core_logging.EVENT_TYPES
    assert "stage_completed" in core_logging.EVENT_TYPES
    assert "roadmap_mutated" in core_logging.EVENT_TYPES
    assert "stage_reopened" in core_logging.EVENT_TYPES
    assert "auto_advance" in core_logging.EVENT_TYPES
    assert "agent_message" in core_logging.EVENT_TYPES
    assert "memory_created" in core_logging.EVENT_TYPES
    assert "regression_detected" in core_logging.EVENT_TYPES


if __name__ == "__main__":
    """Run basic tests manually."""
    print("Running Phase 3 basic tests...")

    print("\n1. Testing workflow_manager...")
    test_workflow_manager_import()
    test_workflow_manager_basic()
    print("   ✅ workflow_manager OK")

    print("\n2. Testing memory_store...")
    test_memory_store_import()
    test_memory_store_basic()
    print("   ✅ memory_store OK")

    print("\n3. Testing inter_agent_bus...")
    test_inter_agent_bus_import()
    test_inter_agent_bus_basic()
    print("   ✅ inter_agent_bus OK")

    print("\n4. Testing stage_summaries...")
    test_stage_summaries_import()
    test_stage_summaries_basic()
    print("   ✅ stage_summaries OK")

    print("\n5. Testing core_logging Phase 3...")
    test_core_logging_phase3_imports()
    test_phase3_event_types()
    print("   ✅ core_logging Phase 3 OK")

    print("\n" + "="*60)
    print("✅ All Phase 3 basic tests passed!")
    print("="*60)
