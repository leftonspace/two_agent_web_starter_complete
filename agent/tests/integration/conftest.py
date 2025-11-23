"""
Integration Test Configuration and Fixtures

Shared fixtures and utilities for integration testing.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Mock LLM Function
# ============================================================================

class MockLLM:
    """Mock LLM for testing without real API calls"""

    def __init__(self):
        self.call_count = 0
        self.responses: Dict[str, str] = {}
        self.default_response = "Mock LLM response"
        self.should_fail = False
        self.fail_count = 0
        self.max_failures = 0

    def set_response(self, pattern: str, response: str):
        """Set a specific response for prompts containing pattern"""
        self.responses[pattern] = response

    def set_failure_mode(self, max_failures: int = 1):
        """Set LLM to fail for first N calls"""
        self.should_fail = True
        self.max_failures = max_failures
        self.fail_count = 0

    async def __call__(self, prompt: str, **kwargs) -> str:
        """Mock LLM call"""
        self.call_count += 1

        # Simulate failures if configured
        if self.should_fail and self.fail_count < self.max_failures:
            self.fail_count += 1
            raise Exception(f"Mock LLM failure {self.fail_count}/{self.max_failures}")

        # Check for pattern matches
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                return response

        return self.default_response

    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.fail_count = 0
        self.should_fail = False


@pytest.fixture
def mock_llm():
    """Provide a mock LLM function"""
    return MockLLM()


# ============================================================================
# Council Fixtures
# ============================================================================

@pytest.fixture
def council_config():
    """Provide council configuration"""
    from council import CouncilConfig
    return CouncilConfig(
        min_councillors=3,
        max_councillors=5,
        default_templates=["coder", "reviewer", "tester"],
        evaluation_interval=5,
    )


@pytest.fixture
async def council(mock_llm, council_config):
    """Provide an initialized council"""
    from council import create_council
    return await create_council(
        llm_func=mock_llm,
        config=council_config
    )


# ============================================================================
# Pattern Fixtures
# ============================================================================

@pytest.fixture
def pattern_agents():
    """Provide agents for pattern testing"""
    from patterns import Agent
    return [
        Agent(name="researcher", role="Research", capabilities=["search", "analyze"]),
        Agent(name="writer", role="Writing", capabilities=["draft", "edit"]),
        Agent(name="reviewer", role="Review", capabilities=["critique", "approve"]),
    ]


@pytest.fixture
def pattern_selector():
    """Provide a pattern selector"""
    from patterns import PatternSelector
    return PatternSelector()


# ============================================================================
# Clarification Fixtures
# ============================================================================

@pytest.fixture
def clarification_manager():
    """Provide a clarification manager"""
    from clarification import ClarificationManager, RequestClarity
    return ClarificationManager(
        clarity_threshold=RequestClarity.SOMEWHAT_CLEAR,
        max_questions=5
    )


# ============================================================================
# Memory Fixtures
# ============================================================================

@pytest.fixture
def memory_store(tmp_path):
    """Provide a temporary memory store"""
    try:
        from memory.vector_store import VectorMemoryStore
        return VectorMemoryStore(persist_directory=str(tmp_path / "memory"))
    except ImportError:
        return None


# ============================================================================
# Human Proxy Fixtures
# ============================================================================

@pytest.fixture
def human_proxy():
    """Provide a human proxy for testing"""
    try:
        from human_proxy import HumanProxy, ApprovalConfig
        proxy = HumanProxy(ApprovalConfig(
            auto_approve_threshold=0.9,
            timeout_seconds=1,  # Short timeout for tests
            default_on_timeout="approve"
        ))
        return proxy
    except ImportError:
        return None


# ============================================================================
# Utility Functions
# ============================================================================

def run_async(coro):
    """Run an async coroutine synchronously"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@pytest.fixture
def event_recorder():
    """Record events during test execution"""
    class EventRecorder:
        def __init__(self):
            self.events: List[Dict[str, Any]] = []

        def record(self, event_type: str, data: Any = None):
            self.events.append({
                "type": event_type,
                "data": data,
            })

        def get_events(self, event_type: Optional[str] = None) -> List[Dict]:
            if event_type:
                return [e for e in self.events if e["type"] == event_type]
            return self.events

        def clear(self):
            self.events = []

    return EventRecorder()


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_llm: marks tests that need real LLM"
    )
