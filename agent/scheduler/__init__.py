"""
JARVIS Cron Scheduler

Production-grade task scheduler with:
- Full cron expression parsing
- Recurring task automation
- Calendar integration
- Task persistence
- Timezone support
"""

from .cron import (
    CronExpression,
    CronScheduler,
    ScheduledTask,
)

from .calendar import (
    CalendarIntegration,
    CalendarEvent,
)

from .persistence import (
    TaskStore,
    SchedulerState,
)

__all__ = [
    "CronExpression",
    "CronScheduler",
    "ScheduledTask",
    "CalendarIntegration",
    "CalendarEvent",
    "TaskStore",
    "SchedulerState",
]

__version__ = "1.0.0"
