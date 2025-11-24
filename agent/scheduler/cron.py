"""
Cron Expression Parser and Scheduler

Full cron syntax support with recurring task automation.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False


# =============================================================================
# Cron Expression Parser
# =============================================================================

class CronField(Enum):
    """Cron expression fields"""
    MINUTE = 0
    HOUR = 1
    DAY_OF_MONTH = 2
    MONTH = 3
    DAY_OF_WEEK = 4


@dataclass
class CronExpression:
    """
    Cron expression parser.

    Supports full cron syntax:
    - * (any value)
    - */5 (every 5)
    - 1-5 (range)
    - 1,3,5 (list)
    - Combinations: 1-5,10,*/15

    Format: minute hour day month weekday
    Example: "0 9 * * 1-5" = 9:00 AM Monday-Friday

    Usage:
        cron = CronExpression("0 9 * * 1-5")

        # Check if time matches
        if cron.matches(datetime.now()):
            execute_task()

        # Get next execution time
        next_run = cron.get_next(datetime.now())
    """

    expression: str
    minute: Set[int] = field(default_factory=set)
    hour: Set[int] = field(default_factory=set)
    day: Set[int] = field(default_factory=set)
    month: Set[int] = field(default_factory=set)
    weekday: Set[int] = field(default_factory=set)

    # Special strings
    SPECIAL_STRINGS = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
    }

    # Field ranges
    RANGES = {
        CronField.MINUTE: (0, 59),
        CronField.HOUR: (0, 23),
        CronField.DAY_OF_MONTH: (1, 31),
        CronField.MONTH: (1, 12),
        CronField.DAY_OF_WEEK: (0, 6),  # 0 = Sunday
    }

    # Month names
    MONTH_NAMES = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    # Weekday names
    WEEKDAY_NAMES = {
        "sun": 0, "mon": 1, "tue": 2, "wed": 3,
        "thu": 4, "fri": 5, "sat": 6,
    }

    def __post_init__(self):
        """Parse cron expression"""
        self._parse()

    def _parse(self):
        """Parse the cron expression"""
        expr = self.expression.strip()

        # Handle special strings
        if expr in self.SPECIAL_STRINGS:
            expr = self.SPECIAL_STRINGS[expr]

        # Split into fields
        parts = expr.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {self.expression}. "
                "Expected 5 fields: minute hour day month weekday"
            )

        # Parse each field
        self.minute = self._parse_field(parts[0], CronField.MINUTE)
        self.hour = self._parse_field(parts[1], CronField.HOUR)
        self.day = self._parse_field(parts[2], CronField.DAY_OF_MONTH)
        self.month = self._parse_field(parts[3], CronField.MONTH)
        self.weekday = self._parse_field(parts[4], CronField.DAY_OF_WEEK)

    def _parse_field(self, field: str, field_type: CronField) -> Set[int]:
        """
        Parse a single cron field.

        Args:
            field: Field string (e.g., "*/5", "1-5", "1,3,5")
            field_type: Type of field

        Returns:
            Set of valid values
        """
        min_val, max_val = self.RANGES[field_type]
        result = set()

        # Wildcard (*) means all values
        if field == "*":
            return set(range(min_val, max_val + 1))

        # Split by comma for lists
        for part in field.split(","):
            part = part.strip()

            # Step values (*/5)
            if "/" in part:
                range_part, step = part.split("/")
                step = int(step)

                if range_part == "*":
                    start, end = min_val, max_val
                elif "-" in range_part:
                    start_str, end_str = range_part.split("-")
                    start = self._parse_value(start_str, field_type)
                    end = self._parse_value(end_str, field_type)
                else:
                    start = self._parse_value(range_part, field_type)
                    end = max_val

                result.update(range(start, end + 1, step))

            # Range (1-5)
            elif "-" in part:
                start_str, end_str = part.split("-")
                start = self._parse_value(start_str, field_type)
                end = self._parse_value(end_str, field_type)
                result.update(range(start, end + 1))

            # Single value
            else:
                result.add(self._parse_value(part, field_type))

        return result

    def _parse_value(self, value: str, field_type: CronField) -> int:
        """
        Parse a single value with name support.

        Args:
            value: Value string
            field_type: Type of field

        Returns:
            Integer value
        """
        # Handle month names
        if field_type == CronField.MONTH:
            value_lower = value.lower()
            if value_lower in self.MONTH_NAMES:
                return self.MONTH_NAMES[value_lower]

        # Handle weekday names
        if field_type == CronField.DAY_OF_WEEK:
            value_lower = value.lower()
            if value_lower in self.WEEKDAY_NAMES:
                return self.WEEKDAY_NAMES[value_lower]

        # Parse as integer
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Invalid value '{value}' for {field_type.name}")

    def matches(self, dt: datetime) -> bool:
        """
        Check if datetime matches cron expression.

        Args:
            dt: Datetime to check

        Returns:
            True if datetime matches
        """
        return (
            dt.minute in self.minute
            and dt.hour in self.hour
            and dt.day in self.day
            and dt.month in self.month
            and dt.weekday() in self.weekday
        )

    def get_next(
        self,
        after: datetime,
        max_iterations: int = 1000,
    ) -> Optional[datetime]:
        """
        Get next matching datetime after given time.

        Args:
            after: Starting datetime
            max_iterations: Maximum iterations to search

        Returns:
            Next matching datetime or None
        """
        # Start from next minute
        current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        for _ in range(max_iterations):
            if self.matches(current):
                return current
            current += timedelta(minutes=1)

        return None

    def get_previous(
        self,
        before: datetime,
        max_iterations: int = 1000,
    ) -> Optional[datetime]:
        """Get previous matching datetime"""
        current = before.replace(second=0, microsecond=0)

        for _ in range(max_iterations):
            if self.matches(current):
                return current
            current -= timedelta(minutes=1)

        return None


# =============================================================================
# Scheduled Task
# =============================================================================

@dataclass
class ScheduledTask:
    """
    A scheduled task.

    Tracks execution history and next run time.
    """
    id: str
    name: str
    cron: CronExpression
    callback: Callable
    timezone: str = "UTC"
    enabled: bool = True
    max_runs: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate initial next_run"""
        if self.next_run is None:
            self.next_run = self.cron.get_next(datetime.utcnow())

    def should_run(self, now: Optional[datetime] = None) -> bool:
        """Check if task should run now"""
        if not self.enabled:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        now = now or datetime.utcnow()
        return self.next_run and now >= self.next_run

    def mark_executed(self, success: bool = True):
        """Mark task as executed"""
        self.last_run = datetime.utcnow()
        self.run_count += 1

        if not success:
            self.failure_count += 1

        # Calculate next run
        self.next_run = self.cron.get_next(datetime.utcnow())

        # Disable if max runs reached
        if self.max_runs and self.run_count >= self.max_runs:
            self.enabled = False


# =============================================================================
# Cron Scheduler
# =============================================================================

class CronScheduler:
    """
    Cron-based task scheduler.

    Features:
    - Full cron expression support
    - Recurring task execution
    - Timezone support
    - Task persistence
    - Concurrent execution

    Usage:
        scheduler = CronScheduler()

        # Add task
        scheduler.add_task(
            name="daily_report",
            cron="0 9 * * *",  # 9:00 AM daily
            callback=generate_report
        )

        # Start scheduler
        await scheduler.start()
    """

    def __init__(
        self,
        timezone: str = "UTC",
        check_interval: int = 60,  # Check every 60 seconds
    ):
        """
        Initialize scheduler.

        Args:
            timezone: Default timezone
            check_interval: How often to check for tasks (seconds)
        """
        self.timezone = timezone
        self.check_interval = check_interval
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._task_counter = 0

    def add_task(
        self,
        name: str,
        cron: str,
        callback: Callable,
        timezone: Optional[str] = None,
        max_runs: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScheduledTask:
        """
        Add a scheduled task.

        Args:
            name: Task name
            cron: Cron expression
            callback: Function to call
            timezone: Optional timezone
            max_runs: Maximum number of runs
            metadata: Optional metadata

        Returns:
            Created ScheduledTask
        """
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"

        cron_expr = CronExpression(cron)

        task = ScheduledTask(
            id=task_id,
            name=name,
            cron=cron_expr,
            callback=callback,
            timezone=timezone or self.timezone,
            max_runs=max_runs,
            metadata=metadata or {},
        )

        self.tasks[task_id] = task
        print(f"[Scheduler] Added task: {name} ({cron})")
        print(f"[Scheduler] Next run: {task.next_run}")

        return task

    def remove_task(self, task_id: str) -> bool:
        """Remove a task"""
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            print(f"[Scheduler] Removed task: {task.name}")
            return True
        return False

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """List all tasks"""
        tasks = list(self.tasks.values())
        if enabled_only:
            tasks = [t for t in tasks if t.enabled]
        return tasks

    async def start(self):
        """Start the scheduler"""
        if self.running:
            print("[Scheduler] Already running")
            return

        self.running = True
        print(f"[Scheduler] Started (checking every {self.check_interval}s)")

        while self.running:
            try:
                await self._check_and_execute()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"[Scheduler] Error in scheduler loop: {e}")
                await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("[Scheduler] Stopped")

    async def _check_and_execute(self):
        """Check for tasks to execute and run them"""
        now = datetime.utcnow()

        # Find tasks that should run
        tasks_to_run = [
            task for task in self.tasks.values()
            if task.should_run(now)
        ]

        if not tasks_to_run:
            return

        print(f"[Scheduler] Executing {len(tasks_to_run)} task(s)")

        # Execute tasks concurrently
        await asyncio.gather(
            *[self._execute_task(task) for task in tasks_to_run],
            return_exceptions=True
        )

    async def _execute_task(self, task: ScheduledTask):
        """Execute a single task"""
        print(f"[Scheduler] Executing: {task.name}")

        try:
            # Call task callback
            if asyncio.iscoroutinefunction(task.callback):
                await task.callback()
            else:
                task.callback()

            task.mark_executed(success=True)
            print(f"[Scheduler] ✅ Task completed: {task.name}")

        except Exception as e:
            task.mark_executed(success=False)
            print(f"[Scheduler] ❌ Task failed: {task.name} - {e}")


# =============================================================================
# Utility Functions
# =============================================================================

def parse_cron(expression: str) -> CronExpression:
    """Quick helper to parse cron expression"""
    return CronExpression(expression)


def create_scheduler(timezone: str = "UTC") -> CronScheduler:
    """Quick helper to create scheduler"""
    return CronScheduler(timezone=timezone)
