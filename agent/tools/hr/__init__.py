"""
PHASE 2.3: HR Tool Suite

This package contains HR-specific tools for the department-in-a-box system:
- send_email: Email sending with template support
- create_calendar_event: Google Calendar integration
- create_hris_record: HRIS system integration (BambooHR, Workday, etc.)

These tools demonstrate the plugin architecture from Phase 2.1 and serve as
reference implementations for future department-specific tools.
"""

__all__ = [
    "SendEmailTool",
    "CreateCalendarEventTool",
    "CreateHRISRecordTool",
]
