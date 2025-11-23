"""
JARVIS Administration Module

Comprehensive administrative tools including:
- Email Integration: Summarization, response drafting, Outlook/Gmail plugins
- Calendar Intelligence: Meeting briefs, action items, schedule optimization
- Workflow Automation: Zapier/Make integration, custom triggers, multi-step execution
"""

from .email_integration import (
    EmailIntegration,
    EmailMessage,
    EmailSummary,
    DraftResponse,
    DailyDigest,
    EmailPriority,
    EmailCategory,
    ResponseTone,
)

from .calendar_intelligence import (
    CalendarIntelligence,
    CalendarEvent,
    MeetingBrief,
    ActionItem,
    MeetingNotes,
    ScheduleOptimization,
    TimeSlot,
    Attendee,
    MeetingType,
    MeetingPriority,
    TimePreference,
)

from .workflow_automation import (
    WorkflowEngine,
    Workflow,
    WorkflowStep,
    TriggerConfig,
    ActionConfig,
    ExecutionContext,
    ExecutionLog,
    IntegrationConfig,
    TriggerType,
    ActionType,
    WorkflowStatus,
    IntegrationType,
)

__all__ = [
    # Email Integration
    "EmailIntegration",
    "EmailMessage",
    "EmailSummary",
    "DraftResponse",
    "DailyDigest",
    "EmailPriority",
    "EmailCategory",
    "ResponseTone",
    # Calendar Intelligence
    "CalendarIntelligence",
    "CalendarEvent",
    "MeetingBrief",
    "ActionItem",
    "MeetingNotes",
    "ScheduleOptimization",
    "TimeSlot",
    "Attendee",
    "MeetingType",
    "MeetingPriority",
    "TimePreference",
    # Workflow Automation
    "WorkflowEngine",
    "Workflow",
    "WorkflowStep",
    "TriggerConfig",
    "ActionConfig",
    "ExecutionContext",
    "ExecutionLog",
    "IntegrationConfig",
    "TriggerType",
    "ActionType",
    "WorkflowStatus",
    "IntegrationType",
]
