"""
STAGE 3 INTEGRATION: Unit Tests for workflow_manager.py

Tests the dynamic roadmap management and workflow orchestration system.
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

# Import the workflow manager module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import workflow_manager


class TestStage(unittest.TestCase):
    """Test Stage data model."""

    def test_stage_creation(self):
        """Test creating a stage."""
        stage = workflow_manager.Stage(
            id="test-123",
            name="Test Stage",
            description="A test stage",
            categories=["layout_structure"],
            plan_steps=[0, 1, 2],
        )

        self.assertEqual(stage.id, "test-123")
        self.assertEqual(stage.name, "Test Stage")
        self.assertEqual(stage.status, "pending")
        self.assertEqual(len(stage.categories), 1)
        self.assertEqual(stage.audit_count, 0)

    def test_stage_to_dict(self):
        """Test stage serialization."""
        stage = workflow_manager.Stage(
            id="test-123",
            name="Test Stage",
            description="A test stage",
            categories=["layout_structure"],
            plan_steps=[0, 1, 2],
        )

        stage_dict = stage.to_dict()
        self.assertIsInstance(stage_dict, dict)
        self.assertEqual(stage_dict["id"], "test-123")
        self.assertEqual(stage_dict["name"], "Test Stage")

    def test_stage_from_dict(self):
        """Test stage deserialization."""
        data = {
            "id": "test-123",
            "name": "Test Stage",
            "description": "A test stage",
            "categories": ["layout_structure"],
            "plan_steps": [0, 1, 2],
            "status": "pending",
            "created_at": time.time(),
            "completed_at": None,
            "audit_count": 0,
            "regression_source": None,
        }

        stage = workflow_manager.Stage.from_dict(data)
        self.assertEqual(stage.id, "test-123")
        self.assertEqual(stage.name, "Test Stage")


class TestRoadmap(unittest.TestCase):
    """Test Roadmap data model."""

    def test_roadmap_creation(self):
        """Test creating a roadmap."""
        stages = [
            workflow_manager.Stage(
                id="stage-1",
                name="Stage 1",
                description="First stage",
                categories=["layout_structure"],
                plan_steps=[0, 1],
            ),
            workflow_manager.Stage(
                id="stage-2",
                name="Stage 2",
                description="Second stage",
                categories=["visual_design"],
                plan_steps=[2, 3],
            ),
        ]

        roadmap = workflow_manager.Roadmap(
            version=1,
            stages=stages,
            created_by="test",
            mutation_type="initial",
        )

        self.assertEqual(roadmap.version, 1)
        self.assertEqual(len(roadmap.stages), 2)
        self.assertEqual(roadmap.mutation_type, "initial")

    def test_roadmap_to_dict(self):
        """Test roadmap serialization."""
        stages = [
            workflow_manager.Stage(
                id="stage-1",
                name="Stage 1",
                description="First stage",
                categories=["layout_structure"],
                plan_steps=[0, 1],
            ),
        ]

        roadmap = workflow_manager.Roadmap(
            version=1,
            stages=stages,
        )

        roadmap_dict = roadmap.to_dict()
        self.assertIsInstance(roadmap_dict, dict)
        self.assertEqual(roadmap_dict["version"], 1)
        self.assertEqual(len(roadmap_dict["stages"]), 1)


class TestWorkflowManager(unittest.TestCase):
    """Test WorkflowManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_run_id = f"test-run-{int(time.time())}"
        self.wm = workflow_manager.WorkflowManager(run_id=self.test_run_id)

    def tearDown(self):
        """Clean up test artifacts."""
        # Remove test workflow file
        if self.wm.workflow_file.exists():
            self.wm.workflow_file.unlink()

    def test_initialization(self):
        """Test workflow manager initialization."""
        plan_steps = ["Step 1", "Step 2", "Step 3"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0, 1]},
            {"name": "Phase 2", "categories": ["visual_design"], "plan_steps": [2]},
        ]

        state = self.wm.initialize(
            plan_steps=plan_steps,
            supervisor_phases=supervisor_phases,
            task="Test task"
        )

        self.assertIsNotNone(state)
        self.assertEqual(len(state.roadmap_history), 1)
        self.assertEqual(len(state.current_roadmap.stages), 2)
        self.assertTrue(self.wm.workflow_file.exists())

    def test_get_next_pending_stage(self):
        """Test getting next pending stage."""
        plan_steps = ["Step 1"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0]},
        ]

        self.wm.initialize(plan_steps, supervisor_phases, "Test task")

        next_stage = self.wm.get_next_pending_stage()
        self.assertIsNotNone(next_stage)
        self.assertEqual(next_stage.name, "Phase 1")
        self.assertEqual(next_stage.status, "pending")

    def test_start_stage(self):
        """Test starting a stage."""
        plan_steps = ["Step 1"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0]},
        ]

        self.wm.initialize(plan_steps, supervisor_phases, "Test task")

        next_stage = self.wm.get_next_pending_stage()
        started_stage = self.wm.start_stage(next_stage.id)

        self.assertEqual(started_stage.status, "active")
        self.assertEqual(self.wm.state.active_stage_id, next_stage.id)

    def test_complete_stage(self):
        """Test completing a stage."""
        plan_steps = ["Step 1"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0]},
        ]

        self.wm.initialize(plan_steps, supervisor_phases, "Test task")

        next_stage = self.wm.get_next_pending_stage()
        self.wm.start_stage(next_stage.id)
        completed_stage = self.wm.complete_stage(next_stage.id)

        self.assertEqual(completed_stage.status, "completed")
        self.assertIsNotNone(completed_stage.completed_at)
        self.assertIsNone(self.wm.state.active_stage_id)

    def test_increment_audit_count(self):
        """Test incrementing audit count."""
        plan_steps = ["Step 1"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0]},
        ]

        self.wm.initialize(plan_steps, supervisor_phases, "Test task")

        next_stage = self.wm.get_next_pending_stage()
        self.wm.start_stage(next_stage.id)

        audit_count = self.wm.increment_audit_count(next_stage.id)
        self.assertEqual(audit_count, 1)

        audit_count = self.wm.increment_audit_count(next_stage.id)
        self.assertEqual(audit_count, 2)

    def test_reopen_stage(self):
        """Test reopening a completed stage."""
        plan_steps = ["Step 1", "Step 2"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0]},
            {"name": "Phase 2", "categories": ["visual_design"], "plan_steps": [1]},
        ]

        self.wm.initialize(plan_steps, supervisor_phases, "Test task")

        # Complete first stage
        stage1 = self.wm.get_next_pending_stage()
        self.wm.start_stage(stage1.id)
        self.wm.complete_stage(stage1.id)

        # Reopen it
        reopened = self.wm.reopen_stage(
            stage1.id,
            reason="Found regression",
            regression_source_id="stage-2"
        )

        self.assertEqual(reopened.status, "reopened")
        self.assertEqual(reopened.regression_source, "stage-2")
        self.assertEqual(reopened.audit_count, 0)  # Reset on reopen

    def test_persistence(self):
        """Test that workflow state persists to disk."""
        plan_steps = ["Step 1"]
        supervisor_phases = [
            {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0]},
        ]

        self.wm.initialize(plan_steps, supervisor_phases, "Test task")

        # Create new workflow manager with same run ID
        wm2 = workflow_manager.WorkflowManager(run_id=self.test_run_id)
        state2 = wm2.load()

        self.assertEqual(state2.run_id, self.test_run_id)
        self.assertEqual(len(state2.roadmap_history), 1)


def run_tests():
    """Run all tests."""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
