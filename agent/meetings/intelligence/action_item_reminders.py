"""
Action Item Reminder System

Integrates meeting action items with CronScheduler and notification system.
Sends reminders for:
- Upcoming due dates (1 day, 2 hours before)
- Overdue items
- Weekly summaries
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import uuid4

try:
    from agent.scheduler.cron import CronExpression, ScheduledTask
except ImportError:
    CronExpression = None
    ScheduledTask = None

try:
    from agent.alerting import AlertingSystem, Alert, AlertSeverity
except ImportError:
    AlertingSystem = None
    Alert = None
    AlertSeverity = None

try:
    from agent.admin.calendar_intelligence import ActionItem
except ImportError:
    # Fallback definition
    @dataclass
    class ActionItem:
        id: str
        description: str
        assignee: Optional[str] = None
        due_date: Optional[datetime] = None
        priority: str = "normal"
        meeting_id: str = ""
        meeting_title: str = ""
        status: str = "pending"


class ReminderType(Enum):
    """Types of action item reminders"""
    DUE_SOON = "due_soon"  # 1 day before
    DUE_TODAY = "due_today"  # Morning of due date
    DUE_IN_2_HOURS = "due_in_2_hours"  # 2 hours before
    OVERDUE = "overdue"  # Past due date
    WEEKLY_SUMMARY = "weekly_summary"  # All pending items


@dataclass
class ReminderConfig:
    """Configuration for action item reminders"""
    enable_due_soon: bool = True  # 1 day before reminder
    enable_due_today: bool = True  # Morning of due date
    enable_due_in_2_hours: bool = True  # 2 hours before
    enable_overdue: bool = True  # Daily overdue check
    enable_weekly_summary: bool = True  # Weekly summary

    # Notification channels
    email_enabled: bool = True
    slack_enabled: bool = True

    # Timing
    daily_check_time: str = "09:00"  # Check overdue items at 9 AM
    weekly_summary_day: str = "MON"  # Monday
    weekly_summary_time: str = "08:00"  # 8 AM Monday

    # Timezone
    timezone: str = "UTC"


@dataclass
class ActionItemStore:
    """In-memory store for action items"""
    items: Dict[str, ActionItem] = field(default_factory=dict)
    reminder_history: Dict[str, Set[str]] = field(default_factory=dict)  # item_id -> set of reminder types sent

    def add_item(self, item: ActionItem):
        """Add or update action item"""
        self.items[item.id] = item
        if item.id not in self.reminder_history:
            self.reminder_history[item.id] = set()

    def get_item(self, item_id: str) -> Optional[ActionItem]:
        """Get action item by ID"""
        return self.items.get(item_id)

    def get_all_pending(self) -> List[ActionItem]:
        """Get all pending action items"""
        return [
            item for item in self.items.values()
            if item.status == "pending"
        ]

    def get_due_soon(self, hours: int = 24) -> List[ActionItem]:
        """Get items due within specified hours"""
        now = datetime.now()
        threshold = now + timedelta(hours=hours)

        return [
            item for item in self.get_all_pending()
            if item.due_date and now <= item.due_date <= threshold
        ]

    def get_overdue(self) -> List[ActionItem]:
        """Get overdue items"""
        now = datetime.now()
        return [
            item for item in self.get_all_pending()
            if item.due_date and item.due_date < now
        ]

    def mark_reminder_sent(self, item_id: str, reminder_type: ReminderType):
        """Mark that a reminder has been sent"""
        if item_id in self.reminder_history:
            self.reminder_history[item_id].add(reminder_type.value)

    def was_reminder_sent(self, item_id: str, reminder_type: ReminderType) -> bool:
        """Check if reminder was already sent"""
        return reminder_type.value in self.reminder_history.get(item_id, set())


class ActionItemReminderSystem:
    """
    Action Item Reminder System

    Integrates meeting action items with CronScheduler and notification system.

    Usage:
        # Initialize system
        reminder_system = ActionItemReminderSystem()

        # Add action items from meetings
        action_item = ActionItem(
            id="meeting_123_action_1",
            description="Review Q4 budget proposal",
            assignee="john@company.com",
            due_date=datetime.now() + timedelta(days=2),
            priority="high"
        )
        reminder_system.add_action_item(action_item)

        # Start reminder system
        await reminder_system.start()
    """

    def __init__(
        self,
        config: Optional[ReminderConfig] = None,
        alerting_system: Optional[AlertingSystem] = None
    ):
        """
        Initialize reminder system.

        Args:
            config: Reminder configuration
            alerting_system: Alerting system for notifications
        """
        self.config = config or ReminderConfig()
        self.store = ActionItemStore()
        self.alerting = alerting_system
        self.running = False
        self.scheduler_tasks: List[ScheduledTask] = []

        # Check if dependencies available
        if CronExpression is None:
            print("[ActionItemReminders] WARNING: CronScheduler not available")
        if AlertingSystem is None and alerting_system is None:
            print("[ActionItemReminders] WARNING: AlertingSystem not available")

    def add_action_item(self, item: ActionItem):
        """
        Add action item to reminder system.

        Args:
            item: Action item to track
        """
        self.store.add_item(item)
        print(f"[ActionItemReminders] Added: {item.description[:50]}... (due: {item.due_date})")

    def add_action_items(self, items: List[ActionItem]):
        """Add multiple action items"""
        for item in items:
            self.add_action_item(item)

    async def start(self):
        """Start the reminder system"""
        if CronExpression is None:
            print("[ActionItemReminders] Cannot start - CronScheduler not available")
            return

        self.running = True
        print("[ActionItemReminders] Starting reminder system...")

        # Schedule reminder checks
        await self._schedule_reminders()

        # Run monitoring loop
        await self._monitor_loop()

    def stop(self):
        """Stop the reminder system"""
        self.running = False
        print("[ActionItemReminders] Stopped")

    async def _schedule_reminders(self):
        """Schedule all reminder checks using CronScheduler"""
        if CronExpression is None:
            return

        # Daily overdue check (9 AM daily)
        if self.config.enable_overdue:
            hour, minute = self.config.daily_check_time.split(":")
            cron_expr = CronExpression(f"{minute} {hour} * * *")
            task = ScheduledTask(
                id=f"reminder_overdue_{uuid4().hex[:8]}",
                name="Check Overdue Action Items",
                cron=cron_expr,
                callback=self._check_overdue,
                timezone=self.config.timezone
            )
            self.scheduler_tasks.append(task)
            print(f"[ActionItemReminders] Scheduled: Daily overdue check at {self.config.daily_check_time}")

        # Weekly summary (Monday 8 AM)
        if self.config.enable_weekly_summary:
            hour, minute = self.config.weekly_summary_time.split(":")
            weekday_map = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}
            weekday = weekday_map.get(self.config.weekly_summary_day, 1)
            cron_expr = CronExpression(f"{minute} {hour} * * {weekday}")
            task = ScheduledTask(
                id=f"reminder_weekly_{uuid4().hex[:8]}",
                name="Weekly Action Item Summary",
                cron=cron_expr,
                callback=self._send_weekly_summary,
                timezone=self.config.timezone
            )
            self.scheduler_tasks.append(task)
            print(f"[ActionItemReminders] Scheduled: Weekly summary on {self.config.weekly_summary_day} at {self.config.weekly_summary_time}")

        # Continuous monitoring for due soon reminders
        print("[ActionItemReminders] Enabled: Continuous monitoring for upcoming deadlines")

    async def _monitor_loop(self):
        """Continuous monitoring loop for time-sensitive reminders"""
        while self.running:
            try:
                await self._check_due_soon()
                await self._check_due_today()
                await self._check_due_in_2_hours()

                # Check every 30 minutes
                await asyncio.sleep(30 * 60)

            except Exception as e:
                print(f"[ActionItemReminders] Error in monitor loop: {e}")
                await asyncio.sleep(60)

    async def _check_due_soon(self):
        """Check for items due in 24 hours"""
        if not self.config.enable_due_soon:
            return

        items = self.store.get_due_soon(hours=24)

        for item in items:
            # Only send once per item
            if self.store.was_reminder_sent(item.id, ReminderType.DUE_SOON):
                continue

            await self._send_reminder(item, ReminderType.DUE_SOON)
            self.store.mark_reminder_sent(item.id, ReminderType.DUE_SOON)

    async def _check_due_today(self):
        """Check for items due today"""
        if not self.config.enable_due_today:
            return

        now = datetime.now()
        items = [
            item for item in self.store.get_all_pending()
            if item.due_date and item.due_date.date() == now.date()
        ]

        for item in items:
            if self.store.was_reminder_sent(item.id, ReminderType.DUE_TODAY):
                continue

            await self._send_reminder(item, ReminderType.DUE_TODAY)
            self.store.mark_reminder_sent(item.id, ReminderType.DUE_TODAY)

    async def _check_due_in_2_hours(self):
        """Check for items due in 2 hours"""
        if not self.config.enable_due_in_2_hours:
            return

        items = self.store.get_due_soon(hours=2)

        for item in items:
            if self.store.was_reminder_sent(item.id, ReminderType.DUE_IN_2_HOURS):
                continue

            await self._send_reminder(item, ReminderType.DUE_IN_2_HOURS)
            self.store.mark_reminder_sent(item.id, ReminderType.DUE_IN_2_HOURS)

    async def _check_overdue(self):
        """Check for overdue items (scheduled task)"""
        if not self.config.enable_overdue:
            return

        items = self.store.get_overdue()

        if not items:
            return

        print(f"[ActionItemReminders] Found {len(items)} overdue items")

        for item in items:
            await self._send_reminder(item, ReminderType.OVERDUE)

    async def _send_weekly_summary(self):
        """Send weekly summary of all pending items (scheduled task)"""
        if not self.config.enable_weekly_summary:
            return

        items = self.store.get_all_pending()

        if not items:
            print("[ActionItemReminders] No pending action items for weekly summary")
            return

        # Group by assignee
        by_assignee: Dict[str, List[ActionItem]] = {}
        for item in items:
            assignee = item.assignee or "Unassigned"
            if assignee not in by_assignee:
                by_assignee[assignee] = []
            by_assignee[assignee].append(item)

        # Generate summary message
        message = f"📋 **Weekly Action Items Summary**\n\n"
        message += f"Total pending: {len(items)}\n\n"

        for assignee, assignee_items in by_assignee.items():
            message += f"**{assignee}** ({len(assignee_items)} items):\n"

            for item in assignee_items:
                due_str = item.due_date.strftime("%Y-%m-%d") if item.due_date else "No due date"
                priority_emoji = {
                    "urgent": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "normal": "⚪",
                    "low": "🔵"
                }.get(item.priority.lower(), "⚪")

                message += f"  {priority_emoji} {item.description[:60]}"
                if len(item.description) > 60:
                    message += "..."
                message += f" (Due: {due_str})\n"

            message += "\n"

        # Send via notification system
        await self._send_notification(
            title="Weekly Action Items Summary",
            message=message,
            severity="info",
            channels=["email", "slack"] if self.config.slack_enabled else ["email"]
        )

        print(f"[ActionItemReminders] Sent weekly summary ({len(items)} items)")

    async def _send_reminder(self, item: ActionItem, reminder_type: ReminderType):
        """
        Send reminder for specific action item.

        Args:
            item: Action item
            reminder_type: Type of reminder
        """
        # Generate reminder message
        message = self._format_reminder_message(item, reminder_type)

        # Determine severity
        severity = "warning" if reminder_type == ReminderType.OVERDUE else "info"

        # Determine channels
        channels = []
        if self.config.email_enabled:
            channels.append("email")
        if self.config.slack_enabled:
            channels.append("slack")

        # Send notification
        await self._send_notification(
            title=f"Action Item Reminder: {item.description[:50]}",
            message=message,
            severity=severity,
            channels=channels,
            recipients=[item.assignee] if item.assignee else None
        )

        print(f"[ActionItemReminders] Sent {reminder_type.value} reminder for: {item.description[:50]}")

    def _format_reminder_message(self, item: ActionItem, reminder_type: ReminderType) -> str:
        """Format reminder message"""
        emoji_map = {
            ReminderType.DUE_SOON: "⏰",
            ReminderType.DUE_TODAY: "📅",
            ReminderType.DUE_IN_2_HOURS: "⚡",
            ReminderType.OVERDUE: "🚨"
        }

        emoji = emoji_map.get(reminder_type, "📌")

        message = f"{emoji} **Action Item Reminder**\n\n"
        message += f"**Description**: {item.description}\n"

        if item.meeting_title:
            message += f"**From Meeting**: {item.meeting_title}\n"

        if item.assignee:
            message += f"**Assigned To**: {item.assignee}\n"

        if item.due_date:
            due_str = item.due_date.strftime("%Y-%m-%d %H:%M")
            message += f"**Due Date**: {due_str}\n"

            # Calculate time remaining/overdue
            now = datetime.now()
            if item.due_date > now:
                delta = item.due_date - now
                if delta.days > 0:
                    message += f"**Time Remaining**: {delta.days} days\n"
                else:
                    hours = delta.seconds // 3600
                    message += f"**Time Remaining**: {hours} hours\n"
            else:
                delta = now - item.due_date
                if delta.days > 0:
                    message += f"**⚠️ OVERDUE BY**: {delta.days} days\n"
                else:
                    hours = delta.seconds // 3600
                    message += f"**⚠️ OVERDUE BY**: {hours} hours\n"

        message += f"**Priority**: {item.priority.upper()}\n"
        message += f"**Status**: {item.status}\n"

        return message

    async def _send_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        channels: Optional[List[str]] = None,
        recipients: Optional[List[str]] = None
    ):
        """
        Send notification via alerting system.

        Args:
            title: Notification title
            message: Notification message
            severity: Severity level
            channels: Notification channels
            recipients: Specific recipients
        """
        if self.alerting is None:
            # Fallback: print to console
            print(f"\n{'='*60}")
            print(f"REMINDER: {title}")
            print(f"{'='*60}")
            print(message)
            print(f"{'='*60}\n")
            return

        # Use AlertingSystem if available
        try:
            if Alert and AlertSeverity:
                severity_map = {
                    "info": AlertSeverity.INFO,
                    "warning": AlertSeverity.WARNING,
                    "error": AlertSeverity.ERROR
                }

                alert = Alert(
                    title=title,
                    message=message,
                    severity=severity_map.get(severity, AlertSeverity.INFO),
                    channels=channels or ["email"],
                    recipients=recipients
                )

                await self.alerting.send_alert(alert)
            else:
                # Fallback if Alert not available
                print(f"[ActionItemReminders] Would send: {title}")

        except Exception as e:
            print(f"[ActionItemReminders] Error sending notification: {e}")

    def get_summary(self) -> Dict[str, int]:
        """Get summary of action items"""
        pending = self.store.get_all_pending()
        overdue = self.store.get_overdue()
        due_soon = self.store.get_due_soon(hours=24)

        return {
            "total_pending": len(pending),
            "overdue": len(overdue),
            "due_in_24_hours": len(due_soon),
            "total_tracked": len(self.store.items)
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_reminder_system(
    config: Optional[ReminderConfig] = None,
    enable_slack: bool = False
) -> ActionItemReminderSystem:
    """
    Quick helper to create reminder system.

    Args:
        config: Custom configuration
        enable_slack: Enable Slack notifications

    Returns:
        ActionItemReminderSystem instance
    """
    if config is None:
        config = ReminderConfig(slack_enabled=enable_slack)

    # Try to initialize alerting system
    alerting = None
    if AlertingSystem:
        try:
            alerting = AlertingSystem()
        except Exception as e:
            print(f"[ActionItemReminders] Could not initialize AlertingSystem: {e}")

    return ActionItemReminderSystem(config=config, alerting_system=alerting)


# =============================================================================
# CLI for Testing
# =============================================================================

async def test_reminder_system():
    """Test the reminder system with sample data"""
    print("\n" + "="*60)
    print("Action Item Reminder System - Test Mode")
    print("="*60 + "\n")

    # Create system
    system = create_reminder_system()

    # Add test action items
    items = [
        ActionItem(
            id="test_1",
            description="Review Q4 budget proposal",
            assignee="john@company.com",
            due_date=datetime.now() + timedelta(hours=1),
            priority="high",
            meeting_title="Budget Planning Meeting",
            status="pending"
        ),
        ActionItem(
            id="test_2",
            description="Update team documentation",
            assignee="sarah@company.com",
            due_date=datetime.now() + timedelta(days=1),
            priority="normal",
            meeting_title="Team Sync",
            status="pending"
        ),
        ActionItem(
            id="test_3",
            description="Prepare presentation slides",
            assignee="john@company.com",
            due_date=datetime.now() - timedelta(days=1),
            priority="urgent",
            meeting_title="Executive Review",
            status="pending"
        ),
    ]

    system.add_action_items(items)

    # Show summary
    summary = system.get_summary()
    print(f"Summary:")
    print(f"  Total tracked: {summary['total_tracked']}")
    print(f"  Pending: {summary['total_pending']}")
    print(f"  Overdue: {summary['overdue']}")
    print(f"  Due in 24h: {summary['due_in_24_hours']}")
    print()

    # Send test reminders
    print("Sending test reminders...\n")
    await system._check_overdue()
    await system._check_due_in_2_hours()
    await system._send_weekly_summary()

    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(test_reminder_system())
