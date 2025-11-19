"""
PHASE 4.1: Specialist System Tests

Basic tests to verify specialist selection logic.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.specialists import (
    get_specialist,
    get_specialists_for_domain,
    select_specialist_for_task,
    SpecialistType,
)


def test_get_specialist():
    """Test getting individual specialists."""
    frontend = get_specialist("frontend")
    assert frontend.specialist_type == SpecialistType.FRONTEND
    assert "React" in frontend.expertise[0] or "Vue" in frontend.expertise[0]

    content_writer = get_specialist("content_writer")
    assert content_writer.specialist_type == SpecialistType.CONTENT_WRITER
    assert "Technical writing" in content_writer.expertise

    researcher = get_specialist("researcher")
    assert researcher.specialist_type == SpecialistType.RESEARCHER
    assert "research" in researcher.name.lower()

    print("✓ test_get_specialist passed")


def test_get_specialists_for_domain():
    """Test domain-to-specialist mapping."""
    # Coding domain should include multiple specialist types
    coding_specialists = get_specialists_for_domain("coding")
    assert len(coding_specialists) > 0
    specialist_types = [s.specialist_type for s in coding_specialists]
    assert SpecialistType.FRONTEND in specialist_types
    assert SpecialistType.BACKEND in specialist_types

    # Finance domain should include data and researcher
    finance_specialists = get_specialists_for_domain("finance")
    finance_types = [s.specialist_type for s in finance_specialists]
    assert SpecialistType.DATA in finance_types
    assert SpecialistType.RESEARCHER in finance_types

    # Legal domain should include researcher and content writer
    legal_specialists = get_specialists_for_domain("legal")
    legal_types = [s.specialist_type for s in legal_specialists]
    assert SpecialistType.RESEARCHER in legal_types
    assert SpecialistType.CONTENT_WRITER in legal_types

    # Content domain should include content writer
    content_specialists = get_specialists_for_domain("content")
    content_types = [s.specialist_type for s in content_specialists]
    assert SpecialistType.CONTENT_WRITER in content_types

    print("✓ test_get_specialists_for_domain passed")


def test_select_specialist_for_task():
    """Test task-based specialist selection."""
    # Frontend task
    frontend_task = "Build a React dashboard with responsive design"
    specialists = select_specialist_for_task(frontend_task)
    assert len(specialists) > 0
    top_specialist, score = specialists[0]
    assert top_specialist.specialist_type == SpecialistType.FRONTEND
    assert score > 0.3

    # Security task
    security_task = "Audit authentication and fix XSS vulnerabilities"
    specialists = select_specialist_for_task(security_task)
    assert len(specialists) > 0
    # Security should be in top specialists
    specialist_types = [s.specialist_type for s, score in specialists]
    assert SpecialistType.SECURITY in specialist_types

    # Content writing task
    content_task = "Write technical documentation and user guides"
    specialists = select_specialist_for_task(content_task)
    assert len(specialists) > 0
    top_specialist, score = specialists[0]
    assert top_specialist.specialist_type == SpecialistType.CONTENT_WRITER

    # Research task
    research_task = "Conduct competitive analysis and market research"
    specialists = select_specialist_for_task(research_task)
    assert len(specialists) > 0
    top_specialist, score = specialists[0]
    assert top_specialist.specialist_type == SpecialistType.RESEARCHER

    print("✓ test_select_specialist_for_task passed")


def test_specialist_cost_multipliers():
    """Test that specialists have appropriate cost multipliers."""
    security = get_specialist("security")
    assert security.cost_multiplier > 1.0  # Security specialists cost more

    qa = get_specialist("qa")
    assert qa.cost_multiplier >= 1.0  # QA at least normal cost

    generic = get_specialist("generic")
    assert generic.cost_multiplier == 1.0  # Generic is baseline

    print("✓ test_specialist_cost_multipliers passed")


if __name__ == "__main__":
    print("Running Specialist System Tests...\n")

    test_get_specialist()
    test_get_specialists_for_domain()
    test_select_specialist_for_task()
    test_specialist_cost_multipliers()

    print("\n✅ All tests passed!")
