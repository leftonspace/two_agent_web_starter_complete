"""
PHASE 2.3: Create Calendar Event Tool

Google Calendar integration tool with support for:
- Single and recurring events
- Multiple attendees
- Timezone handling
- Location and description
- Notification settings

Usage:
    from agent.tools.hr.create_calendar_event import CreateCalendarEventTool
    tool = CreateCalendarEventTool()
    result = await tool.execute({
        "summary": "Onboarding Meeting",
        "start_time": "2025-12-01T09:00:00Z",
        "duration_minutes": 60,
        "attendees": [{"email": "john@example.com"}]
    }, context)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
)

logger = logging.getLogger(__name__)


class CreateCalendarEventTool(ToolPlugin):
    """
    Create events in Google Calendar with support for recurring meetings and attendees.

    Features:
    - Single and recurring events
    - Multiple attendees with optional status
    - Timezone support
    - Location and description
    - Send/suppress notifications
    - Dry run mode

    Configuration (in context.config):
        google_calendar:
            credentials_path: Path to Google OAuth2 credentials JSON
            calendar_id: Calendar ID (default: "primary")
    """

    def get_manifest(self) -> ToolManifest:
        """Return tool manifest with metadata and schema"""
        return ToolManifest(
            name="create_calendar_event",
            version="1.0.0",
            description="Create event in Google Calendar with support for recurring events, attendees, and notifications",
            domains=["hr", "ops", "marketing"],
            roles=["manager", "hr_manager", "hr_recruiter", "hr_business_partner"],
            required_permissions=["calendar_write"],

            input_schema={
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "maxLength": 200,
                        "description": "Event title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description/notes"
                    },
                    "start_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Event start time (ISO 8601)"
                    },
                    "end_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Event end time (ISO 8601)"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Event duration in minutes (alternative to end_time)"
                    },
                    "timezone": {
                        "type": "string",
                        "default": "UTC",
                        "description": "Timezone for the event"
                    },
                    "location": {
                        "type": "string",
                        "description": "Event location or meeting room"
                    },
                    "attendees": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "email": {"type": "string", "format": "email"},
                                "optional": {"type": "boolean", "default": False},
                                "display_name": {"type": "string"}
                            },
                            "required": ["email"]
                        },
                        "description": "List of attendees"
                    },
                    "send_notifications": {
                        "type": "boolean",
                        "default": True,
                        "description": "Send email notifications to attendees"
                    },
                    "recurrence": {
                        "type": "object",
                        "properties": {
                            "frequency": {
                                "type": "string",
                                "enum": ["daily", "weekly", "monthly", "yearly"],
                                "description": "Recurrence frequency"
                            },
                            "count": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "Number of occurrences"
                            },
                            "until": {
                                "type": "string",
                                "format": "date",
                                "description": "Recurrence end date"
                            },
                            "interval": {
                                "type": "integer",
                                "minimum": 1,
                                "default": 1,
                                "description": "Recurrence interval (e.g., every 2 weeks)"
                            }
                        },
                        "required": ["frequency"],
                        "description": "Recurrence rule"
                    },
                    "reminders": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method": {"type": "string", "enum": ["email", "popup"]},
                                "minutes": {"type": "integer", "minimum": 0}
                            }
                        },
                        "description": "Custom reminders"
                    }
                },
                "required": ["summary", "start_time"],
            },

            output_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string"},
                    "event_link": {"type": "string"},
                    "created": {"type": "boolean"},
                    "dry_run": {"type": "boolean"}
                },
                "required": ["event_id", "event_link", "created"]
            },

            cost_estimate=0.0,
            timeout_seconds=20,
            requires_network=True,

            examples=[
                {
                    "description": "Create onboarding meeting",
                    "input": {
                        "summary": "Onboarding Meeting - John Doe",
                        "start_time": "2025-12-01T09:00:00Z",
                        "duration_minutes": 60,
                        "attendees": [
                            {"email": "john.doe@example.com"},
                            {"email": "hr@example.com"}
                        ],
                        "location": "Conference Room A",
                        "description": "Welcome meeting for new employee John Doe"
                    },
                    "output": {
                        "event_id": "abc123xyz",
                        "event_link": "https://calendar.google.com/event?eid=abc123",
                        "created": True
                    }
                },
                {
                    "description": "Create recurring weekly 1:1",
                    "input": {
                        "summary": "Weekly 1:1 with Manager",
                        "start_time": "2025-12-01T14:00:00Z",
                        "duration_minutes": 30,
                        "attendees": [{"email": "manager@example.com"}],
                        "recurrence": {
                            "frequency": "weekly",
                            "count": 12
                        }
                    },
                    "output": {
                        "event_id": "rec456xyz",
                        "event_link": "https://calendar.google.com/event?eid=rec456",
                        "created": True
                    }
                }
            ],

            tags=["calendar", "scheduling", "meetings", "google"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute calendar event creation.

        Args:
            params: Tool parameters (see input_schema)
            context: Execution context with configuration

        Returns:
            ToolResult with event_id and event_link
        """
        try:
            # Get Google Calendar configuration
            calendar_config = context.config.get("google_calendar", {})
            credentials_path = calendar_config.get("credentials_path")
            calendar_id = calendar_config.get("calendar_id", "primary")

            # Validate configuration
            if not credentials_path and not context.dry_run:
                return ToolResult(
                    success=False,
                    error="Google Calendar credentials not configured. Set google_calendar.credentials_path in context.config",
                    metadata={
                        "help": "Set up Google Calendar API credentials",
                        "docs": "https://developers.google.com/calendar/api/quickstart/python"
                    }
                )

            # Parse start/end times
            start_time = datetime.fromisoformat(params["start_time"].replace("Z", "+00:00"))

            if params.get("duration_minutes"):
                end_time = start_time + timedelta(minutes=params["duration_minutes"])
            elif params.get("end_time"):
                end_time = datetime.fromisoformat(params["end_time"].replace("Z", "+00:00"))
            else:
                # Default to 30 minutes
                end_time = start_time + timedelta(minutes=30)

            timezone = params.get("timezone", "UTC")

            # Build event object for Google Calendar API
            event = {
                "summary": params["summary"],
                "description": params.get("description", ""),
                "location": params.get("location", ""),
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": timezone
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": timezone
                },
            }

            # Add attendees
            if params.get("attendees"):
                event["attendees"] = [
                    {
                        "email": attendee["email"],
                        "optional": attendee.get("optional", False),
                        "displayName": attendee.get("display_name")
                    }
                    for attendee in params["attendees"]
                ]

            # Add recurrence rule
            if params.get("recurrence"):
                recurrence_rule = self._build_recurrence_rule(params["recurrence"])
                event["recurrence"] = [recurrence_rule]

            # Add custom reminders
            if params.get("reminders"):
                event["reminders"] = {
                    "useDefault": False,
                    "overrides": [
                        {"method": r["method"], "minutes": r["minutes"]}
                        for r in params["reminders"]
                    ]
                }

            # Dry run mode - don't actually create
            if context.dry_run:
                logger.info(
                    f"[DRY RUN] Would create calendar event: {params['summary']} "
                    f"at {start_time.isoformat()}"
                )
                return ToolResult(
                    success=True,
                    data={
                        "event_id": "dry_run_event_id",
                        "event_link": "https://calendar.google.com/dry_run",
                        "created": False,
                        "dry_run": True
                    },
                    metadata={
                        "note": "Dry run mode - event not actually created",
                        "summary": params["summary"],
                        "start_time": start_time.isoformat()
                    }
                )

            # Create event via Google Calendar API
            logger.info(f"Creating calendar event: {params['summary']}")

            created_event = await self._create_google_calendar_event(
                event,
                calendar_id,
                credentials_path,
                send_notifications=params.get("send_notifications", True)
            )

            logger.info(f"Calendar event created: {created_event['id']}")

            return ToolResult(
                success=True,
                data={
                    "event_id": created_event["id"],
                    "event_link": created_event["htmlLink"],
                    "created": True
                },
                metadata={
                    "summary": params["summary"],
                    "start_time": start_time.isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to create calendar event: {str(e)}"
            )

    def _build_recurrence_rule(self, recurrence: Dict) -> str:
        """
        Build RFC 5545 recurrence rule (RRULE).

        Args:
            recurrence: Recurrence parameters

        Returns:
            RRULE string (e.g., "RRULE:FREQ=WEEKLY;COUNT=10")
        """
        freq = recurrence["frequency"].upper()
        interval = recurrence.get("interval", 1)

        rule = f"RRULE:FREQ={freq}"

        if interval > 1:
            rule += f";INTERVAL={interval}"

        if recurrence.get("count"):
            rule += f";COUNT={recurrence['count']}"
        elif recurrence.get("until"):
            # Format: YYYYMMDD
            until_date = recurrence["until"].replace("-", "")
            rule += f";UNTIL={until_date}"

        return rule

    async def _create_google_calendar_event(
        self,
        event: Dict,
        calendar_id: str,
        credentials_path: str,
        send_notifications: bool = True
    ) -> Dict:
        """
        Create event using Google Calendar API.

        Args:
            event: Event data
            calendar_id: Calendar to create event in
            credentials_path: Path to OAuth2 credentials
            send_notifications: Whether to notify attendees

        Returns:
            Created event data

        Raises:
            Exception: If API call fails
        """
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from pathlib import Path
            import json
            import os

            # Load credentials
            creds = None
            creds_path = Path(credentials_path)

            if creds_path.exists():
                # Try to load from authorized user file
                try:
                    creds = Credentials.from_authorized_user_file(str(creds_path))
                except:
                    # Try loading as service account or other format
                    with open(creds_path) as f:
                        creds_data = json.load(f)
                        # This is simplified - real implementation would handle
                        # different credential types properly
                        pass

            # Refresh token if needed
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            if not creds or not creds.valid:
                raise ValueError(
                    "Invalid or expired Google Calendar credentials. "
                    "Run authorization flow to generate new credentials."
                )

            # Build service
            service = build("calendar", "v3", credentials=creds)

            # Create event
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendNotifications=send_notifications
            ).execute()

            return created_event

        except ImportError:
            raise ImportError(
                "Google Calendar API not available. "
                "Install: pip install google-api-python-client google-auth"
            )
        except Exception as e:
            logger.error(f"Google Calendar API error: {e}")
            raise
