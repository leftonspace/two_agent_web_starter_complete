"""
Cross-Meeting Context System

Links meeting insights across sessions to provide continuity and context.

Features:
- Track participants across meetings
- Link related meetings (same project, recurring series)
- Track action items across sessions
- Maintain conversation history
- Detect patterns and trends
- Provide contextual recommendations

Usage:
    context = CrossMeetingContext()

    # Add meeting
    context.add_meeting(meeting_data)

    # Get context for participant
    participant_context = context.get_participant_context("john@company.com")

    # Get related meetings
    related = context.get_related_meetings(meeting_id)

    # Track action items across meetings
    action_items = context.get_participant_action_items("john@company.com")
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    from .intelligence.meeting_analyzer import ActionItem
except ImportError:
    @dataclass
    class ActionItem:
        id: str
        description: str
        assignee: Optional[str] = None
        due_date: Optional[datetime] = None
        priority: str = "normal"


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class MeetingRecord:
    """Record of a meeting"""

    meeting_id: str
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    # Participants
    participants: List[str] = field(default_factory=list)
    organizer: Optional[str] = None

    # Content
    key_points: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)

    # Metadata
    meeting_type: str = "general"  # standup, planning, review, 1on1, etc.
    project: Optional[str] = None
    series_id: Optional[str] = None  # For recurring meetings
    parent_meeting_id: Optional[str] = None  # For follow-up meetings

    # Topics discussed
    topics: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ParticipantContext:
    """Context for a participant across meetings"""

    participant_email: str
    meetings_attended: int = 0
    last_meeting: Optional[datetime] = None

    # Contributions
    total_action_items: int = 0
    completed_action_items: int = 0
    pending_action_items: List[ActionItem] = field(default_factory=list)

    # Topics and interests
    frequent_topics: Dict[str, int] = field(default_factory=dict)  # topic -> count
    projects: Set[str] = field(default_factory=set)

    # Patterns
    meeting_types: Dict[str, int] = field(default_factory=dict)  # type -> count
    average_meeting_duration_minutes: float = 0.0


@dataclass
class MeetingSeries:
    """A series of related meetings"""

    series_id: str
    title_pattern: str  # Pattern for series (e.g., "Daily Standup")
    meetings: List[str] = field(default_factory=list)  # meeting IDs

    # Statistics
    total_meetings: int = 0
    average_duration_minutes: float = 0.0
    average_participants: float = 0.0

    # Trends
    topics_over_time: List[Dict[str, Any]] = field(default_factory=list)
    action_items_over_time: List[int] = field(default_factory=list)


# =============================================================================
# Cross-Meeting Context System
# =============================================================================

class CrossMeetingContext:
    """
    Cross-Meeting Context System

    Maintains context and relationships across meetings.

    Example:
        context = CrossMeetingContext()

        # Add meeting
        meeting = MeetingRecord(
            meeting_id="meeting_123",
            title="Sprint Planning",
            started_at=datetime.now(),
            participants=["john@company.com", "sarah@company.com"],
            project="Project Alpha",
        )
        context.add_meeting(meeting)

        # Get participant context
        john_context = context.get_participant_context("john@company.com")
        print(f"John attended {john_context.meetings_attended} meetings")

        # Get related meetings
        related = context.get_related_meetings("meeting_123", max_results=5)
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize cross-meeting context system.

        Args:
            storage_path: Path to store context data
        """
        self.storage_path = storage_path or Path(".jarvis/meeting_context")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory storage
        self.meetings: Dict[str, MeetingRecord] = {}
        self.participant_contexts: Dict[str, ParticipantContext] = {}
        self.meeting_series: Dict[str, MeetingSeries] = {}

        # Indexes for fast lookup
        self.meetings_by_participant: Dict[str, List[str]] = defaultdict(list)
        self.meetings_by_project: Dict[str, List[str]] = defaultdict(list)
        self.meetings_by_type: Dict[str, List[str]] = defaultdict(list)
        self.meetings_by_date: List[tuple[datetime, str]] = []  # (date, meeting_id)

        # Load existing data
        self._load_context()

        print(f"[CrossMeetingContext] Initialized with {len(self.meetings)} meetings")

    # =========================================================================
    # Meeting Management
    # =========================================================================

    def add_meeting(self, meeting: MeetingRecord):
        """
        Add meeting to context.

        Args:
            meeting: Meeting record to add
        """
        self.meetings[meeting.meeting_id] = meeting

        # Update indexes
        for participant in meeting.participants:
            self.meetings_by_participant[participant].append(meeting.meeting_id)
            self._update_participant_context(participant, meeting)

        if meeting.project:
            self.meetings_by_project[meeting.project].append(meeting.meeting_id)

        if meeting.meeting_type:
            self.meetings_by_type[meeting.meeting_type].append(meeting.meeting_id)

        self.meetings_by_date.append((meeting.started_at, meeting.meeting_id))
        self.meetings_by_date.sort(key=lambda x: x[0], reverse=True)

        # Update series if applicable
        if meeting.series_id:
            self._update_meeting_series(meeting)

        # Persist
        self._save_meeting(meeting)

        print(f"[CrossMeetingContext] Added meeting: {meeting.title}")

    def get_meeting(self, meeting_id: str) -> Optional[MeetingRecord]:
        """Get meeting by ID"""
        return self.meetings.get(meeting_id)

    def get_recent_meetings(self, limit: int = 10) -> List[MeetingRecord]:
        """Get recent meetings"""
        recent_ids = [mid for _, mid in self.meetings_by_date[:limit]]
        return [self.meetings[mid] for mid in recent_ids if mid in self.meetings]

    # =========================================================================
    # Participant Context
    # =========================================================================

    def get_participant_context(self, participant_email: str) -> ParticipantContext:
        """
        Get context for participant.

        Args:
            participant_email: Participant email

        Returns:
            ParticipantContext with meeting history and patterns
        """
        if participant_email not in self.participant_contexts:
            self.participant_contexts[participant_email] = ParticipantContext(
                participant_email=participant_email
            )

        return self.participant_contexts[participant_email]

    def _update_participant_context(
        self,
        participant_email: str,
        meeting: MeetingRecord,
    ):
        """Update participant context with new meeting"""
        context = self.get_participant_context(participant_email)

        # Update meeting count
        context.meetings_attended += 1
        context.last_meeting = meeting.started_at

        # Update topics
        for topic in meeting.topics:
            context.frequent_topics[topic] = context.frequent_topics.get(topic, 0) + 1

        # Update projects
        if meeting.project:
            context.projects.add(meeting.project)

        # Update meeting types
        if meeting.meeting_type:
            context.meeting_types[meeting.meeting_type] = \
                context.meeting_types.get(meeting.meeting_type, 0) + 1

        # Update action items for this participant
        for action_item in meeting.action_items:
            if action_item.assignee == participant_email:
                context.total_action_items += 1
                if action_item.status == "pending":
                    context.pending_action_items.append(action_item)
                elif action_item.status == "completed":
                    context.completed_action_items += 1

    def get_participant_action_items(
        self,
        participant_email: str,
        status: Optional[str] = None,
    ) -> List[ActionItem]:
        """
        Get action items for participant across all meetings.

        Args:
            participant_email: Participant email
            status: Optional status filter (pending, completed)

        Returns:
            List of action items
        """
        action_items = []

        for meeting_id in self.meetings_by_participant[participant_email]:
            meeting = self.meetings.get(meeting_id)
            if not meeting:
                continue

            for action_item in meeting.action_items:
                if action_item.assignee == participant_email:
                    if status is None or action_item.status == status:
                        action_items.append(action_item)

        return action_items

    # =========================================================================
    # Related Meetings
    # =========================================================================

    def get_related_meetings(
        self,
        meeting_id: str,
        max_results: int = 5,
    ) -> List[MeetingRecord]:
        """
        Get meetings related to the given meeting.

        Relatedness based on:
        - Same project
        - Same meeting series
        - Overlapping participants
        - Similar topics

        Args:
            meeting_id: Meeting to find relations for
            max_results: Maximum number of results

        Returns:
            List of related meetings, sorted by relevance
        """
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return []

        # Calculate relevance scores
        related_scores: Dict[str, float] = {}

        # Same series (highest priority)
        if meeting.series_id and meeting.series_id in self.meeting_series:
            series = self.meeting_series[meeting.series_id]
            for series_meeting_id in series.meetings:
                if series_meeting_id != meeting_id:
                    related_scores[series_meeting_id] = \
                        related_scores.get(series_meeting_id, 0) + 10.0

        # Same project
        if meeting.project:
            for project_meeting_id in self.meetings_by_project[meeting.project]:
                if project_meeting_id != meeting_id:
                    related_scores[project_meeting_id] = \
                        related_scores.get(project_meeting_id, 0) + 5.0

        # Overlapping participants
        for participant in meeting.participants:
            for participant_meeting_id in self.meetings_by_participant[participant]:
                if participant_meeting_id != meeting_id:
                    # More overlap = higher score
                    other_meeting = self.meetings[participant_meeting_id]
                    overlap = len(set(meeting.participants) & set(other_meeting.participants))
                    score = overlap / len(meeting.participants) * 3.0
                    related_scores[participant_meeting_id] = \
                        related_scores.get(participant_meeting_id, 0) + score

        # Similar topics
        meeting_topics = set(meeting.topics)
        for other_id, other_meeting in self.meetings.items():
            if other_id != meeting_id:
                other_topics = set(other_meeting.topics)
                common_topics = meeting_topics & other_topics
                if common_topics:
                    score = len(common_topics) / len(meeting_topics) * 2.0
                    related_scores[other_id] = \
                        related_scores.get(other_id, 0) + score

        # Sort by relevance
        sorted_related = sorted(
            related_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return top results
        result = []
        for related_id, _ in sorted_related[:max_results]:
            related_meeting = self.meetings.get(related_id)
            if related_meeting:
                result.append(related_meeting)

        return result

    # =========================================================================
    # Meeting Series
    # =========================================================================

    def _update_meeting_series(self, meeting: MeetingRecord):
        """Update meeting series with new meeting"""
        if not meeting.series_id:
            return

        if meeting.series_id not in self.meeting_series:
            self.meeting_series[meeting.series_id] = MeetingSeries(
                series_id=meeting.series_id,
                title_pattern=meeting.title,
            )

        series = self.meeting_series[meeting.series_id]
        series.meetings.append(meeting.meeting_id)
        series.total_meetings += 1

        # Update statistics
        if meeting.ended_at:
            duration = (meeting.ended_at - meeting.started_at).total_seconds() / 60
            series.average_duration_minutes = (
                (series.average_duration_minutes * (series.total_meetings - 1) + duration)
                / series.total_meetings
            )

        series.average_participants = (
            (series.average_participants * (series.total_meetings - 1) + len(meeting.participants))
            / series.total_meetings
        )

    def get_meeting_series(self, series_id: str) -> Optional[MeetingSeries]:
        """Get meeting series by ID"""
        return self.meeting_series.get(series_id)

    # =========================================================================
    # Contextual Recommendations
    # =========================================================================

    def get_contextual_recommendations(
        self,
        meeting_id: str,
    ) -> List[str]:
        """
        Get contextual recommendations for meeting.

        Args:
            meeting_id: Meeting to get recommendations for

        Returns:
            List of recommendation strings
        """
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return []

        recommendations = []

        # Check for related meetings
        related = self.get_related_meetings(meeting_id, max_results=3)
        if related:
            recommendations.append(
                f"Related meetings: {', '.join(m.title for m in related[:3])}"
            )

        # Check for pending action items from participants
        pending_items = []
        for participant in meeting.participants:
            items = self.get_participant_action_items(participant, status="pending")
            pending_items.extend(items)

        if pending_items:
            recommendations.append(
                f"Participants have {len(pending_items)} pending action items from previous meetings"
            )

        # Check for recurring topics
        if meeting.topics:
            for topic in meeting.topics:
                # Find how many times this topic was discussed
                topic_count = sum(
                    1 for m in self.meetings.values()
                    if topic in m.topics
                )
                if topic_count > 3:
                    recommendations.append(
                        f"Topic '{topic}' has been discussed in {topic_count} previous meetings"
                    )

        return recommendations

    # =========================================================================
    # Pattern Detection
    # =========================================================================

    def detect_patterns(self) -> Dict[str, Any]:
        """
        Detect patterns across meetings.

        Returns:
            Dict with detected patterns
        """
        patterns = {
            "most_active_participants": [],
            "most_common_topics": [],
            "most_productive_meeting_types": [],
            "action_item_completion_rate": 0.0,
        }

        # Most active participants
        participant_counts = {
            email: len(meetings)
            for email, meetings in self.meetings_by_participant.items()
        }
        patterns["most_active_participants"] = sorted(
            participant_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Most common topics
        topic_counts: Dict[str, int] = defaultdict(int)
        for meeting in self.meetings.values():
            for topic in meeting.topics:
                topic_counts[topic] += 1

        patterns["most_common_topics"] = sorted(
            topic_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Most productive meeting types (by action items generated)
        type_productivity: Dict[str, int] = defaultdict(int)
        for meeting in self.meetings.values():
            type_productivity[meeting.meeting_type] += len(meeting.action_items)

        patterns["most_productive_meeting_types"] = sorted(
            type_productivity.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Action item completion rate
        total_items = 0
        completed_items = 0
        for context in self.participant_contexts.values():
            total_items += context.total_action_items
            completed_items += context.completed_action_items

        if total_items > 0:
            patterns["action_item_completion_rate"] = completed_items / total_items

        return patterns

    # =========================================================================
    # Persistence
    # =========================================================================

    def _save_meeting(self, meeting: MeetingRecord):
        """Save meeting to disk"""
        try:
            meeting_file = self.storage_path / f"{meeting.meeting_id}.json"

            meeting_dict = {
                "meeting_id": meeting.meeting_id,
                "title": meeting.title,
                "started_at": meeting.started_at.isoformat(),
                "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
                "participants": meeting.participants,
                "organizer": meeting.organizer,
                "key_points": meeting.key_points,
                "decisions": meeting.decisions,
                "questions": meeting.questions,
                "meeting_type": meeting.meeting_type,
                "project": meeting.project,
                "series_id": meeting.series_id,
                "parent_meeting_id": meeting.parent_meeting_id,
                "topics": meeting.topics,
                "tags": meeting.tags,
                # Action items simplified
                "action_items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "assignee": item.assignee,
                        "priority": item.priority,
                    }
                    for item in meeting.action_items
                ],
            }

            with meeting_file.open("w") as f:
                json.dump(meeting_dict, f, indent=2)

        except Exception as e:
            print(f"[CrossMeetingContext] Error saving meeting: {e}")

    def _load_context(self):
        """Load context from disk"""
        try:
            for meeting_file in self.storage_path.glob("*.json"):
                with meeting_file.open("r") as f:
                    data = json.load(f)

                meeting = MeetingRecord(
                    meeting_id=data["meeting_id"],
                    title=data["title"],
                    started_at=datetime.fromisoformat(data["started_at"]),
                    ended_at=datetime.fromisoformat(data["ended_at"]) if data.get("ended_at") else None,
                    participants=data.get("participants", []),
                    organizer=data.get("organizer"),
                    key_points=data.get("key_points", []),
                    decisions=data.get("decisions", []),
                    questions=data.get("questions", []),
                    meeting_type=data.get("meeting_type", "general"),
                    project=data.get("project"),
                    series_id=data.get("series_id"),
                    parent_meeting_id=data.get("parent_meeting_id"),
                    topics=data.get("topics", []),
                    tags=data.get("tags", []),
                )

                # Reconstruct action items
                for item_data in data.get("action_items", []):
                    action_item = ActionItem(
                        id=item_data["id"],
                        description=item_data["description"],
                        assignee=item_data.get("assignee"),
                        priority=item_data.get("priority", "normal"),
                    )
                    meeting.action_items.append(action_item)

                self.add_meeting(meeting)

        except Exception as e:
            print(f"[CrossMeetingContext] Error loading context: {e}")


# =============================================================================
# Convenience Functions
# =============================================================================

def create_cross_meeting_context(
    storage_path: Optional[Path] = None,
) -> CrossMeetingContext:
    """
    Create cross-meeting context system.

    Args:
        storage_path: Optional custom storage path

    Returns:
        Configured CrossMeetingContext
    """
    return CrossMeetingContext(storage_path=storage_path)
