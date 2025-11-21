"""
Meeting intelligence module.

Analyzes meeting transcripts in real-time to extract:
- Action items
- Decisions
- Questions
- Key points

And executes simple tasks during meetings.
"""

from agent.meetings.intelligence.meeting_analyzer import (
    MeetingAnalyzer,
    ActionItem,
    Decision,
    Question,
    MeetingUnderstanding,
    Priority
)
from agent.meetings.intelligence.action_executor import MeetingActionExecutor

__all__ = [
    "MeetingAnalyzer",
    "ActionItem",
    "Decision",
    "Question",
    "MeetingUnderstanding",
    "Priority",
    "MeetingActionExecutor"
]
