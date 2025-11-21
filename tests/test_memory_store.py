"""
STAGE 3 INTEGRATION: Unit Tests for memory_store.py

Tests the stage-level persistent memory system.
"""

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

# Import the memory store module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import memory_store


class TestFinding(unittest.TestCase):
    """Test Finding data model."""

    def test_finding_creation(self):
        """Test creating a finding."""
        finding = memory_store.Finding(
            timestamp=time.time(),
            severity="error",
            category="functionality",
            description="Button doesn't work",
            file_path="index.html",
            line_number=42,
        )

        self.assertEqual(finding.severity, "error")
        self.assertEqual(finding.category, "functionality")
        self.assertFalse(finding.resolved)

    def test_finding_to_dict(self):
        """Test finding serialization."""
        finding = memory_store.Finding(
            timestamp=time.time(),
            severity="warning",
            category="design",
            description="Color contrast too low",
        )

        finding_dict = finding.to_dict()
        self.assertIsInstance(finding_dict, dict)
        self.assertEqual(finding_dict["severity"], "warning")


class TestDecision(unittest.TestCase):
    """Test Decision data model."""

    def test_decision_creation(self):
        """Test creating a decision."""
        decision = memory_store.Decision(
            timestamp=time.time(),
            agent="manager",
            decision_type="skip_task",
            description="Skipped task 3 due to time constraints",
            context={"task_id": 3},
        )

        self.assertEqual(decision.agent, "manager")
        self.assertEqual(decision.decision_type, "skip_task")
        self.assertEqual(decision.context["task_id"], 3)


class TestMemoryStore(unittest.TestCase):
    """Test MemoryStore class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_run_id = f"test-run-{int(time.time())}"
        self.mem_store = memory_store.MemoryStore(run_id=self.test_run_id)

    def tearDown(self):
        """Clean up test artifacts."""
        # Remove test memory directory
        if self.mem_store.run_dir.exists():
            for file in self.mem_store.run_dir.glob("*.json"):
                file.unlink()
            self.mem_store.run_dir.rmdir()

    def test_create_memory(self):
        """Test creating a stage memory."""
        memory = self.mem_store.create_memory(
            stage_id="stage-1",
            stage_name="Test Stage"
        )

        self.assertIsNotNone(memory)
        self.assertEqual(memory.stage_id, "stage-1")
        self.assertEqual(memory.stage_name, "Test Stage")
        self.assertEqual(len(memory.findings), 0)

    def test_load_memory(self):
        """Test loading a stage memory."""
        # Create memory
        self.mem_store.create_memory("stage-1", "Test Stage")

        # Load it
        memory = self.mem_store.load_memory("stage-1")

        self.assertIsNotNone(memory)
        self.assertEqual(memory.stage_id, "stage-1")

    def test_get_or_create_memory(self):
        """Test get_or_create pattern."""
        # Should create new memory
        memory1 = self.mem_store.get_or_create_memory("stage-1", "Test Stage")
        self.assertEqual(memory1.stage_name, "Test Stage")

        # Should load existing memory
        memory2 = self.mem_store.get_or_create_memory("stage-1", "Different Name")
        self.assertEqual(memory2.stage_name, "Test Stage")  # Original name preserved

    def test_add_finding(self):
        """Test adding a finding to memory."""
        self.mem_store.create_memory("stage-1", "Test Stage")

        self.mem_store.add_finding(
            stage_id="stage-1",
            severity="error",
            category="functionality",
            description="Button doesn't work",
            file_path="index.html",
            line_number=42,
        )

        memory = self.mem_store.load_memory("stage-1")
        self.assertEqual(len(memory.findings), 1)
        self.assertEqual(memory.findings[0].severity, "error")
        self.assertEqual(memory.findings[0].description, "Button doesn't work")

    def test_resolve_finding(self):
        """Test resolving a finding."""
        self.mem_store.create_memory("stage-1", "Test Stage")

        # Add finding
        self.mem_store.add_finding(
            stage_id="stage-1",
            severity="error",
            category="functionality",
            description="Button doesn't work",
        )

        # Resolve it
        self.mem_store.resolve_finding(
            stage_id="stage-1",
            finding_index=0,
            resolution_note="Fixed by updating onClick handler"
        )

        memory = self.mem_store.load_memory("stage-1")
        self.assertTrue(memory.findings[0].resolved)
        self.assertEqual(memory.findings[0].resolution_note, "Fixed by updating onClick handler")

    def test_get_unresolved_findings(self):
        """Test getting unresolved findings."""
        self.mem_store.create_memory("stage-1", "Test Stage")

        # Add multiple findings
        self.mem_store.add_finding("stage-1", "error", "func", "Issue 1")
        self.mem_store.add_finding("stage-1", "warning", "design", "Issue 2")
        self.mem_store.add_finding("stage-1", "error", "func", "Issue 3")

        # Resolve one
        self.mem_store.resolve_finding("stage-1", 1, "Fixed")

        # Get unresolved
        unresolved = self.mem_store.get_unresolved_findings("stage-1")

        self.assertEqual(len(unresolved), 2)
        self.assertEqual(unresolved[0].description, "Issue 1")
        self.assertEqual(unresolved[1].description, "Issue 3")

    def test_add_decision(self):
        """Test adding a decision to memory."""
        self.mem_store.create_memory("stage-1", "Test Stage")

        self.mem_store.add_decision(
            stage_id="stage-1",
            agent="manager",
            decision_type="roadmap_change",
            description="Merged stages 2 and 3",
            context={"merged_stages": [2, 3]},
        )

        memory = self.mem_store.load_memory("stage-1")
        self.assertEqual(len(memory.decisions), 1)
        self.assertEqual(memory.decisions[0].decision_type, "roadmap_change")

    def test_add_clarification(self):
        """Test adding a clarification to memory."""
        self.mem_store.create_memory("stage-1", "Test Stage")

        self.mem_store.add_clarification(
            stage_id="stage-1",
            from_agent="employee",
            to_agent="manager",
            question="Should the button be blue or green?",
            answer="Blue, to match the brand colors",
        )

        memory = self.mem_store.load_memory("stage-1")
        self.assertEqual(len(memory.clarifications), 1)
        self.assertEqual(memory.clarifications[0].question, "Should the button be blue or green?")
        self.assertEqual(memory.clarifications[0].answer, "Blue, to match the brand colors")

    def test_persistence(self):
        """Test that memory persists to disk."""
        self.mem_store.create_memory("stage-1", "Test Stage")
        self.mem_store.add_finding("stage-1", "error", "func", "Test finding")

        # Create new memory store with same run ID
        mem_store2 = memory_store.MemoryStore(run_id=self.test_run_id)
        memory2 = mem_store2.load_memory("stage-1")

        self.assertEqual(memory2.stage_id, "stage-1")
        self.assertEqual(len(memory2.findings), 1)
        self.assertEqual(memory2.findings[0].description, "Test finding")


def run_tests():
    """Run all tests."""
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
