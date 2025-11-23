"""
Calendar Intelligence Module for JARVIS

Provides intelligent calendar management:
- Meeting preparation briefs
- Action item extraction from meetings
- Schedule optimization
- Conflict detection
- Time blocking recommendations
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta, time
import re
from collections import defaultdict


class MeetingType(Enum):
    """Types of meetings."""
    ONE_ON_ONE = "one_on_one"
    TEAM = "team"
    ALL_HANDS = "all_hands"
    CLIENT = "client"
    INTERVIEW = "interview"
    REVIEW = "review"
    PLANNING = "planning"
    STANDUP = "standup"
    WORKSHOP = "workshop"
    EXTERNAL = "external"


class MeetingPriority(Enum):
    """Meeting priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    OPTIONAL = "optional"


class TimePreference(Enum):
    """Time preferences for scheduling."""
    MORNING = "morning"  # 9am - 12pm
    MIDDAY = "midday"    # 12pm - 2pm
    AFTERNOON = "afternoon"  # 2pm - 5pm
    FLEXIBLE = "flexible"


@dataclass
class Attendee:
    """Meeting attendee."""
    email: str
    name: str
    required: bool = True
    response_status: str = "pending"  # accepted, declined, tentative, pending


@dataclass
class CalendarEvent:
    """Represents a calendar event."""
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    attendees: List[Attendee] = field(default_factory=list)
    location: Optional[str] = None
    description: Optional[str] = None
    meeting_link: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    organizer: Optional[str] = None
    attachments: List[Dict[str, str]] = field(default_factory=list)
    reminders: List[int] = field(default_factory=list)  # minutes before


@dataclass
class MeetingBrief:
    """Pre-meeting preparation brief."""
    event: CalendarEvent
    meeting_type: MeetingType
    priority: MeetingPriority
    preparation_items: List[str]
    talking_points: List[str]
    relevant_context: List[str]
    previous_meetings: List[Dict[str, Any]]
    attendee_notes: Dict[str, str]
    suggested_questions: List[str]
    estimated_duration_accuracy: str
    recommendations: List[str]


@dataclass
class ActionItem:
    """Action item extracted from a meeting."""
    id: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "normal"
    meeting_id: str = ""
    meeting_title: str = ""
    status: str = "pending"  # pending, in_progress, completed


@dataclass
class MeetingNotes:
    """Structured meeting notes."""
    meeting_id: str
    title: str
    date: datetime
    attendees: List[str]
    summary: str
    key_decisions: List[str]
    action_items: List[ActionItem]
    discussion_points: List[str]
    follow_ups: List[str]
    next_meeting: Optional[str] = None


@dataclass
class ScheduleOptimization:
    """Schedule optimization recommendations."""
    date: str
    total_meeting_hours: float
    focus_time_hours: float
    fragmentation_score: float  # 0-1, lower is better
    recommendations: List[str]
    suggested_reschedules: List[Dict[str, Any]]
    time_blocks: List[Dict[str, Any]]
    productivity_score: float  # 0-100


@dataclass
class TimeSlot:
    """A time slot for scheduling."""
    start: datetime
    end: datetime
    score: float = 0.0  # Higher is better
    conflicts: List[str] = field(default_factory=list)


class CalendarIntelligence:
    """
    Calendar Intelligence Engine for JARVIS.

    Provides smart calendar analysis and meeting preparation.
    """

    def __init__(self):
        """Initialize calendar intelligence."""
        # Meeting type keywords
        self.meeting_patterns = {
            MeetingType.ONE_ON_ONE: ["1:1", "1-1", "one on one", "check-in", "catch up"],
            MeetingType.TEAM: ["team", "department", "group", "weekly team"],
            MeetingType.ALL_HANDS: ["all hands", "all-hands", "company", "town hall"],
            MeetingType.CLIENT: ["client", "customer", "external", "partner"],
            MeetingType.INTERVIEW: ["interview", "candidate", "hiring"],
            MeetingType.REVIEW: ["review", "feedback", "performance", "retrospective"],
            MeetingType.PLANNING: ["planning", "sprint", "roadmap", "strategy"],
            MeetingType.STANDUP: ["standup", "stand-up", "daily", "scrum"],
            MeetingType.WORKSHOP: ["workshop", "training", "session", "brainstorm"],
        }

        # Priority keywords
        self.priority_keywords = {
            MeetingPriority.CRITICAL: ["urgent", "critical", "emergency", "ceo", "board"],
            MeetingPriority.HIGH: ["important", "priority", "deadline", "exec"],
            MeetingPriority.LOW: ["optional", "fyi", "info", "casual"],
        }

        # Focus time preferences (hours of day that are optimal for deep work)
        self.focus_hours = [(9, 11), (14, 16)]  # 9-11am and 2-4pm

    def generate_meeting_brief(
        self,
        event: CalendarEvent,
        past_meetings: Optional[List[CalendarEvent]] = None,
        email_context: Optional[List[Dict[str, str]]] = None
    ) -> MeetingBrief:
        """
        Generate a comprehensive meeting preparation brief.

        Args:
            event: The upcoming meeting
            past_meetings: Previous meetings with same attendees
            email_context: Recent relevant emails

        Returns:
            MeetingBrief with preparation materials
        """
        # Classify meeting type
        meeting_type = self._classify_meeting_type(event)

        # Determine priority
        priority = self._classify_priority(event)

        # Generate preparation items based on meeting type
        prep_items = self._generate_prep_items(event, meeting_type)

        # Generate talking points
        talking_points = self._generate_talking_points(event, meeting_type)

        # Build relevant context
        relevant_context = []
        if event.description:
            relevant_context.append(f"Meeting description: {event.description[:200]}")

        if email_context:
            for email in email_context[:3]:
                relevant_context.append(
                    f"Related email from {email.get('sender', 'Unknown')}: "
                    f"{email.get('subject', 'No subject')}"
                )

        # Analyze past meetings
        previous_meetings = []
        if past_meetings:
            for pm in past_meetings[-5:]:  # Last 5 meetings
                previous_meetings.append({
                    "title": pm.title,
                    "date": pm.start_time.strftime("%Y-%m-%d"),
                    "duration": (pm.end_time - pm.start_time).seconds // 60
                })

        # Generate attendee notes
        attendee_notes = {}
        for attendee in event.attendees:
            notes = self._get_attendee_context(attendee, past_meetings)
            if notes:
                attendee_notes[attendee.name or attendee.email] = notes

        # Generate suggested questions
        questions = self._generate_questions(event, meeting_type)

        # Assess duration accuracy
        duration = (event.end_time - event.start_time).seconds // 60
        duration_accuracy = self._assess_duration(duration, meeting_type)

        # Generate recommendations
        recommendations = self._generate_meeting_recommendations(
            event, meeting_type, priority
        )

        return MeetingBrief(
            event=event,
            meeting_type=meeting_type,
            priority=priority,
            preparation_items=prep_items,
            talking_points=talking_points,
            relevant_context=relevant_context,
            previous_meetings=previous_meetings,
            attendee_notes=attendee_notes,
            suggested_questions=questions,
            estimated_duration_accuracy=duration_accuracy,
            recommendations=recommendations
        )

    def extract_action_items(
        self,
        meeting_notes: str,
        meeting_id: str,
        meeting_title: str,
        attendees: List[str]
    ) -> List[ActionItem]:
        """
        Extract action items from meeting notes.

        Args:
            meeting_notes: Raw meeting notes text
            meeting_id: ID of the meeting
            meeting_title: Title of the meeting
            attendees: List of attendee names/emails

        Returns:
            List of extracted action items
        """
        action_items = []

        # Patterns for action items
        patterns = [
            # "John will do X by Friday"
            r"(\w+)\s+will\s+(.+?)(?:by\s+(\w+))?[.\n]",
            # "Action: John to do X"
            r"action[:\s]+(\w+)\s+(?:to\s+)?(.+?)[.\n]",
            # "TODO: X (John)"
            r"todo[:\s]+(.+?)\s*\((\w+)\)",
            # "[ ] X - John"
            r"\[\s*\]\s*(.+?)\s*[-–]\s*(\w+)",
            # "@John: do X"
            r"@(\w+)[:\s]+(.+?)[.\n]",
        ]

        item_id = 0
        for pattern in patterns:
            matches = re.findall(pattern, meeting_notes, re.IGNORECASE)
            for match in matches:
                item_id += 1

                # Parse match based on pattern structure
                if len(match) >= 2:
                    assignee = match[0] if match[0] in attendees else None
                    description = match[1] if len(match) > 1 else match[0]

                    # Try to extract due date
                    due_date = None
                    if len(match) > 2 and match[2]:
                        due_date = self._parse_relative_date(match[2])

                    action_items.append(ActionItem(
                        id=f"{meeting_id}_action_{item_id}",
                        description=description.strip(),
                        assignee=assignee,
                        due_date=due_date,
                        meeting_id=meeting_id,
                        meeting_title=meeting_title
                    ))

        # Look for bullet points that sound like actions
        bullets = re.findall(r'[-*]\s+(.+?)[\n]', meeting_notes)
        for bullet in bullets:
            if any(word in bullet.lower() for word in
                   ['will', 'should', 'need to', 'must', 'action', 'follow up']):
                item_id += 1
                action_items.append(ActionItem(
                    id=f"{meeting_id}_action_{item_id}",
                    description=bullet.strip(),
                    meeting_id=meeting_id,
                    meeting_title=meeting_title
                ))

        return action_items

    def generate_meeting_summary(
        self,
        event: CalendarEvent,
        notes: str,
        transcript: Optional[str] = None
    ) -> MeetingNotes:
        """
        Generate structured meeting notes from raw notes/transcript.

        Args:
            event: The calendar event
            notes: Raw meeting notes
            transcript: Optional meeting transcript

        Returns:
            Structured MeetingNotes
        """
        text = f"{notes}\n{transcript or ''}"

        # Extract key decisions
        decisions = self._extract_decisions(text)

        # Extract action items
        attendee_names = [a.name or a.email for a in event.attendees]
        action_items = self.extract_action_items(
            text, event.id, event.title, attendee_names
        )

        # Extract discussion points
        discussion_points = self._extract_discussion_points(text)

        # Extract follow-ups
        follow_ups = self._extract_follow_ups(text)

        # Generate summary
        summary = self._generate_summary(event, decisions, action_items)

        # Check for next meeting mention
        next_meeting = self._extract_next_meeting(text)

        return MeetingNotes(
            meeting_id=event.id,
            title=event.title,
            date=event.start_time,
            attendees=attendee_names,
            summary=summary,
            key_decisions=decisions,
            action_items=action_items,
            discussion_points=discussion_points,
            follow_ups=follow_ups,
            next_meeting=next_meeting
        )

    def optimize_schedule(
        self,
        events: List[CalendarEvent],
        date: Optional[datetime] = None,
        work_hours: Tuple[int, int] = (9, 17)
    ) -> ScheduleOptimization:
        """
        Analyze and optimize a day's schedule.

        Args:
            events: List of calendar events
            date: Date to analyze (defaults to today)
            work_hours: Work hours as (start, end) in 24h format

        Returns:
            ScheduleOptimization with recommendations
        """
        date = date or datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        # Filter events for the specified date
        day_events = [
            e for e in events
            if e.start_time.date() == date.date()
        ]

        # Sort by start time
        day_events.sort(key=lambda e: e.start_time)

        # Calculate total meeting time
        total_meeting_mins = sum(
            (e.end_time - e.start_time).seconds // 60
            for e in day_events
        )
        total_meeting_hours = total_meeting_mins / 60

        # Calculate available work hours
        work_duration = work_hours[1] - work_hours[0]
        focus_time_hours = work_duration - total_meeting_hours

        # Calculate fragmentation score
        fragmentation = self._calculate_fragmentation(day_events, work_hours)

        # Generate time blocks
        time_blocks = self._generate_time_blocks(day_events, work_hours, date)

        # Generate recommendations
        recommendations = self._generate_schedule_recommendations(
            day_events, fragmentation, focus_time_hours
        )

        # Suggest reschedules
        suggested_reschedules = self._suggest_reschedules(
            day_events, fragmentation
        )

        # Calculate productivity score
        productivity_score = self._calculate_productivity_score(
            focus_time_hours, fragmentation, len(day_events)
        )

        return ScheduleOptimization(
            date=date_str,
            total_meeting_hours=round(total_meeting_hours, 1),
            focus_time_hours=round(focus_time_hours, 1),
            fragmentation_score=round(fragmentation, 2),
            recommendations=recommendations,
            suggested_reschedules=suggested_reschedules,
            time_blocks=time_blocks,
            productivity_score=round(productivity_score, 1)
        )

    def find_optimal_slots(
        self,
        events: List[CalendarEvent],
        duration_minutes: int,
        date_range: Tuple[datetime, datetime],
        attendee_calendars: Optional[Dict[str, List[CalendarEvent]]] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> List[TimeSlot]:
        """
        Find optimal time slots for a new meeting.

        Args:
            events: Current calendar events
            duration_minutes: Required meeting duration
            date_range: (start_date, end_date) to search
            attendee_calendars: Other attendees' calendars
            preferences: Scheduling preferences

        Returns:
            List of TimeSlot options, sorted by score
        """
        preferences = preferences or {}
        work_hours = preferences.get("work_hours", (9, 17))
        time_pref = preferences.get("time_preference", TimePreference.FLEXIBLE)

        slots = []
        current = date_range[0].replace(
            hour=work_hours[0], minute=0, second=0, microsecond=0
        )
        end_date = date_range[1]

        while current < end_date:
            # Skip weekends
            if current.weekday() >= 5:
                current += timedelta(days=1)
                current = current.replace(hour=work_hours[0], minute=0)
                continue

            # Check if within work hours
            if current.hour >= work_hours[1]:
                current += timedelta(days=1)
                current = current.replace(hour=work_hours[0], minute=0)
                continue

            slot_end = current + timedelta(minutes=duration_minutes)

            # Skip if extends beyond work hours
            if slot_end.hour > work_hours[1]:
                current += timedelta(days=1)
                current = current.replace(hour=work_hours[0], minute=0)
                continue

            # Check for conflicts
            conflicts = self._check_conflicts(
                current, slot_end, events, attendee_calendars
            )

            # Calculate slot score
            score = self._score_time_slot(
                current, slot_end, time_pref, len(conflicts) == 0
            )

            slots.append(TimeSlot(
                start=current,
                end=slot_end,
                score=score,
                conflicts=conflicts
            ))

            # Move to next slot (30-minute increments)
            current += timedelta(minutes=30)

        # Sort by score (descending) and filter to top options
        slots.sort(key=lambda s: s.score, reverse=True)

        return slots[:10]  # Top 10 options

    def detect_conflicts(
        self,
        events: List[CalendarEvent]
    ) -> List[Dict[str, Any]]:
        """
        Detect scheduling conflicts.

        Args:
            events: List of calendar events

        Returns:
            List of conflict descriptions
        """
        conflicts = []
        sorted_events = sorted(events, key=lambda e: e.start_time)

        for i, event1 in enumerate(sorted_events):
            for event2 in sorted_events[i + 1:]:
                # Check for overlap
                if event1.end_time > event2.start_time:
                    overlap_mins = (
                        min(event1.end_time, event2.end_time) -
                        max(event1.start_time, event2.start_time)
                    ).seconds // 60

                    conflicts.append({
                        "event1": {
                            "id": event1.id,
                            "title": event1.title,
                            "time": event1.start_time.isoformat()
                        },
                        "event2": {
                            "id": event2.id,
                            "title": event2.title,
                            "time": event2.start_time.isoformat()
                        },
                        "overlap_minutes": overlap_mins,
                        "severity": "high" if overlap_mins > 30 else "medium"
                    })

        return conflicts

    # Private helper methods

    def _classify_meeting_type(self, event: CalendarEvent) -> MeetingType:
        """Classify the type of meeting."""
        title_lower = event.title.lower()
        desc_lower = (event.description or "").lower()
        combined = f"{title_lower} {desc_lower}"

        for meeting_type, keywords in self.meeting_patterns.items():
            if any(kw in combined for kw in keywords):
                return meeting_type

        # Determine by attendee count
        attendee_count = len(event.attendees)
        if attendee_count <= 2:
            return MeetingType.ONE_ON_ONE
        elif attendee_count <= 8:
            return MeetingType.TEAM

        return MeetingType.TEAM

    def _classify_priority(self, event: CalendarEvent) -> MeetingPriority:
        """Classify meeting priority."""
        combined = f"{event.title} {event.description or ''}".lower()

        for priority, keywords in self.priority_keywords.items():
            if any(kw in combined for kw in keywords):
                return priority

        return MeetingPriority.NORMAL

    def _generate_prep_items(
        self,
        event: CalendarEvent,
        meeting_type: MeetingType
    ) -> List[str]:
        """Generate preparation items for a meeting."""
        items = []

        # Generic items
        items.append("Review meeting agenda and objectives")

        # Type-specific items
        if meeting_type == MeetingType.ONE_ON_ONE:
            items.extend([
                "Review notes from last 1:1",
                "Prepare discussion topics and updates",
                "Think about any blockers or support needed"
            ])
        elif meeting_type == MeetingType.CLIENT:
            items.extend([
                "Review client account status",
                "Prepare relevant materials/demos",
                "Review recent communications with client"
            ])
        elif meeting_type == MeetingType.INTERVIEW:
            items.extend([
                "Review candidate's resume/portfolio",
                "Prepare interview questions",
                "Review role requirements"
            ])
        elif meeting_type == MeetingType.REVIEW:
            items.extend([
                "Gather relevant data and metrics",
                "Prepare examples and talking points",
                "Review previous feedback"
            ])
        elif meeting_type == MeetingType.PLANNING:
            items.extend([
                "Review current status and progress",
                "Prepare proposals or options",
                "Gather input from stakeholders"
            ])

        # Check for attachments
        if event.attachments:
            items.append(f"Review {len(event.attachments)} attached document(s)")

        return items

    def _generate_talking_points(
        self,
        event: CalendarEvent,
        meeting_type: MeetingType
    ) -> List[str]:
        """Generate talking points for a meeting."""
        points = []

        if meeting_type == MeetingType.ONE_ON_ONE:
            points = [
                "Current project status and progress",
                "Blockers and challenges",
                "Upcoming priorities",
                "Career development and goals",
                "Feedback and support needs"
            ]
        elif meeting_type == MeetingType.STANDUP:
            points = [
                "What I accomplished yesterday",
                "What I'm working on today",
                "Any blockers or help needed"
            ]
        elif meeting_type == MeetingType.CLIENT:
            points = [
                "Project updates and milestones",
                "Any concerns or feedback",
                "Next steps and timeline",
                "Additional opportunities"
            ]
        elif meeting_type == MeetingType.REVIEW:
            points = [
                "Key achievements and successes",
                "Areas for improvement",
                "Learnings and insights",
                "Action items for improvement"
            ]
        else:
            points = [
                "Meeting objectives",
                "Key discussion items",
                "Decisions needed",
                "Next steps"
            ]

        return points

    def _get_attendee_context(
        self,
        attendee: Attendee,
        past_meetings: Optional[List[CalendarEvent]]
    ) -> str:
        """Get context about an attendee."""
        if not past_meetings:
            return ""

        # Count meetings with this attendee
        meetings_with = sum(
            1 for m in past_meetings
            if any(a.email == attendee.email for a in m.attendees)
        )

        if meetings_with > 0:
            return f"Met {meetings_with} times previously"
        return ""

    def _generate_questions(
        self,
        event: CalendarEvent,
        meeting_type: MeetingType
    ) -> List[str]:
        """Generate suggested questions for the meeting."""
        questions = []

        if meeting_type == MeetingType.ONE_ON_ONE:
            questions = [
                "How are you feeling about your current workload?",
                "Is there anything blocking your progress?",
                "What support do you need from me?",
                "What would you like to focus on in the coming weeks?"
            ]
        elif meeting_type == MeetingType.CLIENT:
            questions = [
                "Are we meeting your expectations so far?",
                "What could we do better?",
                "Are there any concerns we should address?",
                "What's your timeline for the next phase?"
            ]
        elif meeting_type == MeetingType.INTERVIEW:
            questions = [
                "Tell me about your experience with [relevant skill]",
                "Describe a challenging project you worked on",
                "How do you approach [relevant scenario]?",
                "What questions do you have about the role?"
            ]

        return questions

    def _assess_duration(self, duration: int, meeting_type: MeetingType) -> str:
        """Assess if meeting duration is appropriate."""
        typical_durations = {
            MeetingType.ONE_ON_ONE: (30, 60),
            MeetingType.STANDUP: (15, 15),
            MeetingType.TEAM: (30, 60),
            MeetingType.CLIENT: (45, 90),
            MeetingType.INTERVIEW: (45, 60),
            MeetingType.REVIEW: (30, 60),
            MeetingType.PLANNING: (60, 120),
            MeetingType.WORKSHOP: (90, 180),
        }

        min_dur, max_dur = typical_durations.get(
            meeting_type, (30, 60)
        )

        if duration < min_dur:
            return f"Short - typical {meeting_type.value} meetings are {min_dur}-{max_dur} mins"
        elif duration > max_dur:
            return f"Long - consider if full {duration} mins is needed"
        return "Appropriate for this meeting type"

    def _generate_meeting_recommendations(
        self,
        event: CalendarEvent,
        meeting_type: MeetingType,
        priority: MeetingPriority
    ) -> List[str]:
        """Generate recommendations for the meeting."""
        recommendations = []

        # Check for missing agenda
        if not event.description:
            recommendations.append(
                "Consider adding an agenda to the meeting description"
            )

        # Check attendee count
        if len(event.attendees) > 8:
            recommendations.append(
                "Large meeting - ensure clear roles and facilitation"
            )

        # Check for virtual meeting link
        if not event.meeting_link and not event.location:
            recommendations.append(
                "No meeting link or location specified"
            )

        # Priority-based recommendations
        if priority == MeetingPriority.CRITICAL:
            recommendations.append(
                "High-priority meeting - ensure all key stakeholders can attend"
            )

        return recommendations

    def _extract_decisions(self, text: str) -> List[str]:
        """Extract key decisions from meeting notes."""
        decisions = []

        patterns = [
            r"decided\s+(?:to\s+)?(.+?)[.\n]",
            r"decision[:\s]+(.+?)[.\n]",
            r"agreed\s+(?:to\s+)?(.+?)[.\n]",
            r"concluded\s+(?:that\s+)?(.+?)[.\n]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            decisions.extend(matches)

        return list(dict.fromkeys(decisions))  # Deduplicate

    def _extract_discussion_points(self, text: str) -> List[str]:
        """Extract main discussion points."""
        points = []

        # Look for headers/topics
        headers = re.findall(r'^#+\s*(.+?)$', text, re.MULTILINE)
        points.extend(headers)

        # Look for numbered items
        numbered = re.findall(r'^\d+\.\s*(.+?)$', text, re.MULTILINE)
        points.extend(numbered)

        return points[:10]  # Top 10

    def _extract_follow_ups(self, text: str) -> List[str]:
        """Extract follow-up items."""
        follow_ups = []

        patterns = [
            r"follow[- ]up[:\s]+(.+?)[.\n]",
            r"next\s+step[s]?[:\s]+(.+?)[.\n]",
            r"revisit\s+(.+?)[.\n]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            follow_ups.extend(matches)

        return follow_ups

    def _generate_summary(
        self,
        event: CalendarEvent,
        decisions: List[str],
        action_items: List[ActionItem]
    ) -> str:
        """Generate meeting summary."""
        parts = [f"Meeting: {event.title}"]

        if decisions:
            parts.append(f"Key decisions: {len(decisions)} made")

        if action_items:
            parts.append(f"Action items: {len(action_items)} assigned")

        duration = (event.end_time - event.start_time).seconds // 60
        parts.append(f"Duration: {duration} minutes")

        return ". ".join(parts)

    def _extract_next_meeting(self, text: str) -> Optional[str]:
        """Extract mention of next meeting."""
        patterns = [
            r"next\s+meeting[:\s]+(.+?)[.\n]",
            r"reconvene[:\s]+(.+?)[.\n]",
            r"follow[- ]up\s+meeting[:\s]+(.+?)[.\n]",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """Parse relative date references."""
        text_lower = text.lower()
        today = datetime.now()

        if "today" in text_lower:
            return today
        elif "tomorrow" in text_lower:
            return today + timedelta(days=1)
        elif "next week" in text_lower:
            return today + timedelta(weeks=1)

        # Day names
        days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        for i, day in enumerate(days):
            if day in text_lower:
                days_ahead = i - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)

        return None

    def _calculate_fragmentation(
        self,
        events: List[CalendarEvent],
        work_hours: Tuple[int, int]
    ) -> float:
        """Calculate schedule fragmentation score."""
        if not events:
            return 0.0

        # Count gaps less than 30 minutes
        sorted_events = sorted(events, key=lambda e: e.start_time)
        short_gaps = 0
        total_gaps = 0

        for i in range(len(sorted_events) - 1):
            gap = (sorted_events[i + 1].start_time -
                   sorted_events[i].end_time).seconds // 60

            if gap > 0:
                total_gaps += 1
                if gap < 30:
                    short_gaps += 1

        if total_gaps == 0:
            return 0.0

        return short_gaps / total_gaps

    def _generate_time_blocks(
        self,
        events: List[CalendarEvent],
        work_hours: Tuple[int, int],
        date: datetime
    ) -> List[Dict[str, Any]]:
        """Generate time blocks for the day."""
        blocks = []
        sorted_events = sorted(events, key=lambda e: e.start_time)

        work_start = date.replace(hour=work_hours[0], minute=0)
        work_end = date.replace(hour=work_hours[1], minute=0)

        current = work_start

        for event in sorted_events:
            # Add focus block before meeting
            if event.start_time > current:
                gap_mins = (event.start_time - current).seconds // 60
                if gap_mins >= 30:
                    blocks.append({
                        "type": "focus",
                        "start": current.isoformat(),
                        "end": event.start_time.isoformat(),
                        "duration_minutes": gap_mins,
                        "label": "Focus Time"
                    })

            # Add meeting block
            duration = (event.end_time - event.start_time).seconds // 60
            blocks.append({
                "type": "meeting",
                "start": event.start_time.isoformat(),
                "end": event.end_time.isoformat(),
                "duration_minutes": duration,
                "label": event.title
            })

            current = event.end_time

        # Add final focus block
        if current < work_end:
            gap_mins = (work_end - current).seconds // 60
            if gap_mins >= 30:
                blocks.append({
                    "type": "focus",
                    "start": current.isoformat(),
                    "end": work_end.isoformat(),
                    "duration_minutes": gap_mins,
                    "label": "Focus Time"
                })

        return blocks

    def _generate_schedule_recommendations(
        self,
        events: List[CalendarEvent],
        fragmentation: float,
        focus_time: float
    ) -> List[str]:
        """Generate schedule recommendations."""
        recommendations = []

        if fragmentation > 0.5:
            recommendations.append(
                "High fragmentation - consider consolidating meetings"
            )

        if focus_time < 2:
            recommendations.append(
                "Limited focus time - consider blocking time for deep work"
            )

        if len(events) > 6:
            recommendations.append(
                "Meeting-heavy day - consider declining optional meetings"
            )

        # Check for back-to-back meetings
        sorted_events = sorted(events, key=lambda e: e.start_time)
        back_to_back = 0
        for i in range(len(sorted_events) - 1):
            gap = (sorted_events[i + 1].start_time -
                   sorted_events[i].end_time).seconds // 60
            if gap < 5:
                back_to_back += 1

        if back_to_back > 2:
            recommendations.append(
                f"{back_to_back} back-to-back meetings - add buffer time"
            )

        return recommendations

    def _suggest_reschedules(
        self,
        events: List[CalendarEvent],
        fragmentation: float
    ) -> List[Dict[str, Any]]:
        """Suggest meetings to reschedule."""
        suggestions = []

        if fragmentation > 0.5:
            # Find low-priority meetings that could be moved
            for event in events:
                priority = self._classify_priority(event)
                if priority in [MeetingPriority.LOW, MeetingPriority.OPTIONAL]:
                    suggestions.append({
                        "event_id": event.id,
                        "title": event.title,
                        "reason": "Low priority - consider moving to reduce fragmentation",
                        "suggestion": "Move to day with more availability"
                    })

        return suggestions[:3]  # Top 3 suggestions

    def _calculate_productivity_score(
        self,
        focus_time: float,
        fragmentation: float,
        meeting_count: int
    ) -> float:
        """Calculate overall productivity score."""
        # Base score from focus time (max 50 points)
        focus_score = min(focus_time / 4, 1) * 50

        # Fragmentation penalty (max 30 points)
        frag_score = (1 - fragmentation) * 30

        # Meeting count factor (max 20 points)
        if meeting_count <= 4:
            meeting_score = 20
        elif meeting_count <= 6:
            meeting_score = 15
        elif meeting_count <= 8:
            meeting_score = 10
        else:
            meeting_score = 5

        return focus_score + frag_score + meeting_score

    def _check_conflicts(
        self,
        start: datetime,
        end: datetime,
        events: List[CalendarEvent],
        attendee_calendars: Optional[Dict[str, List[CalendarEvent]]]
    ) -> List[str]:
        """Check for scheduling conflicts."""
        conflicts = []

        # Check own calendar
        for event in events:
            if start < event.end_time and end > event.start_time:
                conflicts.append(f"Conflicts with: {event.title}")

        # Check attendee calendars
        if attendee_calendars:
            for attendee, cal in attendee_calendars.items():
                for event in cal:
                    if start < event.end_time and end > event.start_time:
                        conflicts.append(f"{attendee} unavailable")
                        break

        return conflicts

    def _score_time_slot(
        self,
        start: datetime,
        end: datetime,
        time_pref: TimePreference,
        available: bool
    ) -> float:
        """Score a time slot based on preferences."""
        if not available:
            return 0.0

        score = 50.0  # Base score for available slot

        # Time preference bonus
        hour = start.hour
        if time_pref == TimePreference.MORNING and 9 <= hour < 12:
            score += 30
        elif time_pref == TimePreference.MIDDAY and 12 <= hour < 14:
            score += 30
        elif time_pref == TimePreference.AFTERNOON and 14 <= hour < 17:
            score += 30
        elif time_pref == TimePreference.FLEXIBLE:
            score += 20

        # Avoid very early or late
        if hour < 9 or hour >= 17:
            score -= 20

        # Slight preference for round hours
        if start.minute == 0:
            score += 5

        return score
