"""
Tests for meeting intelligence.

PHASE 7A.4: Tests for action item extraction, decision tracking,
question identification, and real-time action execution.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from agent.meetings.intelligence.meeting_analyzer import (
    MeetingAnalyzer,
    Priority,
    ActionItem,
    Decision,
    Question,
    MeetingUnderstanding
)
from agent.meetings.intelligence.action_executor import MeetingActionExecutor


# ══════════════════════════════════════════════════════════════════════
# Action Item Extraction Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_action_item_extraction():
    """Test extracting action items from transcript"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [{
            "task": "Update budget spreadsheet",
            "assignee": "John",
            "deadline": "2024-12-31T17:00:00",
            "priority": "high",
            "context": "Need updated Q4 numbers",
            "mentioned_by": "CEO"
        }],
        "decisions": [],
        "questions": [],
        "key_points": [],
        "topics_discussed": ["budget"],
        "sentiment": "neutral",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        transcript="John, can you update the budget spreadsheet by end of year?",
        speaker="CEO",
        timestamp=datetime.now()
    )

    assert len(understanding.action_items) == 1
    assert understanding.action_items[0].task == "Update budget spreadsheet"
    assert understanding.action_items[0].assignee == "John"
    assert understanding.action_items[0].priority == Priority.HIGH


@pytest.mark.asyncio
async def test_multiple_action_items():
    """Test extracting multiple action items from one segment"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [
            {
                "task": "Update budget",
                "assignee": "John",
                "deadline": None,
                "priority": "medium",
                "context": "",
                "mentioned_by": "CEO"
            },
            {
                "task": "Review deck",
                "assignee": "Alice",
                "deadline": None,
                "priority": "high",
                "context": "",
                "mentioned_by": "CEO"
            }
        ],
        "decisions": [],
        "questions": [],
        "key_points": [],
        "topics_discussed": [],
        "sentiment": "neutral",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        transcript="John, update the budget. Alice, review the deck.",
        speaker="CEO"
    )

    assert len(understanding.action_items) == 2
    assert understanding.action_items[0].assignee == "John"
    assert understanding.action_items[1].assignee == "Alice"


@pytest.mark.asyncio
async def test_no_action_items_from_vague_statement():
    """Test that vague statements don't create action items"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [],  # Should be empty for vague statement
        "decisions": [],
        "questions": [],
        "key_points": ["Need to think about budget"],
        "topics_discussed": ["budget"],
        "sentiment": "neutral",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        transcript="We should think about the budget sometime",
        speaker="CEO"
    )

    # Vague statement shouldn't create action items
    assert len(understanding.action_items) == 0


# ══════════════════════════════════════════════════════════════════════
# Decision Tracking Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_decision_extraction():
    """Test extracting decisions from transcript"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [],
        "decisions": [{
            "decision": "Go with Option A",
            "rationale": "Lower cost and faster implementation",
            "decided_by": "CEO",
            "alternatives_considered": ["Option B", "Option C"],
            "impact": "Q4 budget and timeline"
        }],
        "questions": [],
        "key_points": [],
        "topics_discussed": ["vendor selection"],
        "sentiment": "positive",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        transcript="After reviewing all options, let's go with Option A",
        speaker="CEO"
    )

    assert len(understanding.decisions) == 1
    assert understanding.decisions[0].decision == "Go with Option A"
    assert understanding.decisions[0].decided_by == "CEO"
    assert "Option B" in understanding.decisions[0].alternatives_considered


@pytest.mark.asyncio
async def test_no_decision_from_consideration():
    """Test that mere consideration doesn't create a decision"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [],
        "decisions": [],  # Should be empty for consideration
        "questions": [],
        "key_points": ["Considering Option A"],
        "topics_discussed": ["vendor selection"],
        "sentiment": "neutral",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        transcript="We're considering Option A",
        speaker="CEO"
    )

    # Consideration shouldn't create a decision
    assert len(understanding.decisions) == 0


# ══════════════════════════════════════════════════════════════════════
# Question Tracking Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_question_identification():
    """Test identifying questions needing answers"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [],
        "decisions": [],
        "questions": [{
            "question": "What's our current burn rate?",
            "asked_by": "CFO",
            "answered": False
        }],
        "key_points": [],
        "topics_discussed": ["finances"],
        "sentiment": "neutral",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        transcript="What's our current burn rate?",
        speaker="CFO"
    )

    assert len(understanding.questions) == 1
    assert understanding.questions[0].question == "What's our current burn rate?"
    assert understanding.questions[0].asked_by == "CFO"
    assert understanding.questions[0].answered is False


# ══════════════════════════════════════════════════════════════════════
# Real-Time Action Execution Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_jarvis_action_execution():
    """Test JARVIS executing simple action during meeting"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "query_type": "search",
        "query": "Q3 revenue",
        "endpoint": None
    })
    llm_mock.chat = AsyncMock(return_value="Q3 revenue: $2.5M")

    executor = MeetingActionExecutor(llm_mock)

    action = {
        "action_type": "query_data",
        "description": "Pull up Q3 revenue",
        "urgency": "immediate",
        "parameters": {
            "query": "Q3 revenue"
        }
    }

    result = await executor._execute_action(action)

    assert result is not None
    assert result["action_type"] == "query_data"
    assert "result" in result


@pytest.mark.asyncio
async def test_action_executor_only_executes_immediate_actions():
    """Test that only immediate/during-meeting actions are executed"""
    llm_mock = Mock()
    executor = MeetingActionExecutor(llm_mock)

    understanding = MeetingUnderstanding(
        action_items=[],
        decisions=[],
        questions=[],
        key_points=[],
        topics_discussed=[],
        sentiment="neutral",
        needs_jarvis_action=True,
        suggested_actions=[
            {
                "action_type": "query_data",
                "description": "Immediate action",
                "urgency": "immediate",
                "parameters": {}
            },
            {
                "action_type": "query_data",
                "description": "After meeting action",
                "urgency": "after_meeting",
                "parameters": {}
            }
        ]
    )

    # Mock the _execute_action method
    executor._execute_action = AsyncMock(return_value={"action_type": "query_data"})

    actions_taken = await executor.process_understanding(understanding)

    # Only immediate action should be executed
    assert len(actions_taken) == 1
    executor._execute_action.assert_called_once()


@pytest.mark.asyncio
async def test_search_info_action():
    """Test search info action execution"""
    llm_mock = Mock()
    executor = MeetingActionExecutor(llm_mock)

    action = {
        "action_type": "search_info",
        "description": "Search for exchange rate",
        "urgency": "immediate",
        "parameters": {
            "query": "USD to EUR exchange rate"
        }
    }

    result = await executor._execute_action(action)

    assert result is not None
    assert result["action_type"] == "search_info"
    assert "result" in result


@pytest.mark.asyncio
async def test_create_document_action():
    """Test document creation action"""
    llm_mock = Mock()
    llm_mock.chat = AsyncMock(return_value="# Q4 Plan\n\nContent here...")
    executor = MeetingActionExecutor(llm_mock)

    action = {
        "action_type": "create_document",
        "description": "Create Q4 plan doc",
        "urgency": "during_meeting",
        "parameters": {
            "title": "Q4 Plan",
            "type": "plan"
        }
    }

    result = await executor._execute_action(action)

    assert result is not None
    assert result["action_type"] == "create_document"
    assert result["result"]["title"] == "Q4 Plan"


# ══════════════════════════════════════════════════════════════════════
# Meeting Context Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_meeting_context_accumulation():
    """Test that meeting context accumulates correctly"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [],
        "decisions": [],
        "questions": [],
        "key_points": [],
        "topics_discussed": ["budget", "hiring"],
        "sentiment": "neutral",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    # First segment
    await analyzer.analyze_transcript_segment(
        "Let's discuss the budget",
        "CEO"
    )

    # Second segment
    await analyzer.analyze_transcript_segment(
        "And also hiring plans",
        "CEO"
    )

    # Check context accumulated
    assert "budget" in analyzer.meeting_context["topics_so_far"]
    assert "hiring" in analyzer.meeting_context["topics_so_far"]


@pytest.mark.asyncio
async def test_deadline_parsing_relative():
    """Test parsing relative deadlines"""
    analyzer = MeetingAnalyzer(Mock())

    # Test various relative deadlines
    today_deadline = analyzer._parse_deadline("today")
    assert today_deadline is not None
    assert today_deadline.hour == 17  # EOD

    tomorrow_deadline = analyzer._parse_deadline("tomorrow")
    assert tomorrow_deadline is not None

    next_week_deadline = analyzer._parse_deadline("next week")
    assert next_week_deadline is not None


@pytest.mark.asyncio
async def test_actions_summary():
    """Test getting summary of executed actions"""
    llm_mock = Mock()
    executor = MeetingActionExecutor(llm_mock)

    # Simulate some executed actions
    executor.executed_actions = [
        {
            "action_type": "query_data",
            "description": "Pulled Q3 revenue",
            "timestamp": "2024-01-01T10:00:00"
        },
        {
            "action_type": "create_document",
            "description": "Created Q4 plan doc",
            "timestamp": "2024-01-01T10:05:00"
        }
    ]

    summary = executor.get_actions_summary()

    assert "2 actions" in summary
    assert "Pulled Q3 revenue" in summary
    assert "Created Q4 plan doc" in summary


@pytest.mark.asyncio
async def test_empty_actions_summary():
    """Test summary when no actions taken"""
    llm_mock = Mock()
    executor = MeetingActionExecutor(llm_mock)

    summary = executor.get_actions_summary()

    assert "No actions taken" in summary


# ══════════════════════════════════════════════════════════════════════
# Sentiment Analysis Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_sentiment_detection():
    """Test sentiment analysis in transcripts"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "action_items": [],
        "decisions": [],
        "questions": [],
        "key_points": [],
        "topics_discussed": ["results"],
        "sentiment": "positive",
        "needs_jarvis_action": False,
        "suggested_actions": []
    })

    analyzer = MeetingAnalyzer(llm_mock)

    understanding = await analyzer.analyze_transcript_segment(
        "Great results this quarter! We exceeded all targets.",
        "CEO"
    )

    assert understanding.sentiment == "positive"


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_analysis_error_handling():
    """Test graceful handling of analysis errors"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(side_effect=Exception("API error"))

    analyzer = MeetingAnalyzer(llm_mock)

    # Should return empty understanding on error
    understanding = await analyzer.analyze_transcript_segment(
        "Some transcript",
        "Speaker"
    )

    assert len(understanding.action_items) == 0
    assert len(understanding.decisions) == 0
    assert understanding.sentiment == "neutral"


@pytest.mark.asyncio
async def test_action_execution_error_handling():
    """Test graceful handling of action execution errors"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(side_effect=Exception("Execution error"))

    executor = MeetingActionExecutor(llm_mock)

    action = {
        "action_type": "query_data",
        "description": "Query that fails",
        "urgency": "immediate",
        "parameters": {"query": "test"}
    }

    # Should return None on error
    result = await executor._execute_action(action)

    assert result is None
