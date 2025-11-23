"""
Meeting intelligence engine.

Analyzes meeting transcripts to extract:
- Action items
- Decisions
- Questions
- Key points
- Topics discussed
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from agent.llm_client import LLMClient
from agent.core_logging import log_event


class Priority(Enum):
    """Action item priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ActionItem:
    """Extracted action item"""
    task: str
    assignee: Optional[str]  # Who should do it
    deadline: Optional[datetime]  # When it's due
    priority: Priority
    context: str  # Surrounding discussion
    mentioned_by: Optional[str]  # Who mentioned it
    mentioned_at: datetime
    status: str = "pending"  # pending, in_progress, completed


@dataclass
class Decision:
    """Tracked decision"""
    decision: str
    rationale: Optional[str]
    decided_by: Optional[str]  # Who made the decision
    decided_at: datetime
    alternatives_considered: List[str]
    impact: str  # What this affects


@dataclass
class Question:
    """Question needing answer"""
    question: str
    asked_by: Optional[str]
    asked_at: datetime
    answered: bool = False
    answer: Optional[str] = None
    answered_by: Optional[str] = None


@dataclass
class MeetingUnderstanding:
    """Complete understanding of meeting segment"""
    action_items: List[ActionItem]
    decisions: List[Decision]
    questions: List[Question]
    key_points: List[str]
    topics_discussed: List[str]
    sentiment: str  # overall: positive, neutral, negative
    needs_jarvis_action: bool  # Should JARVIS do something now?
    suggested_actions: List[Dict]  # What JARVIS should do


class MeetingAnalyzer:
    """
    Analyzes meeting transcripts to extract intelligence.

    Processes in real-time: every 10-30 seconds of meeting.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

        # Meeting context (accumulates throughout meeting)
        self.meeting_context = {
            "meeting_title": "",
            "participants": [],
            "start_time": None,
            "topics_so_far": [],
            "decisions_so_far": [],
            "action_items_so_far": []
        }

    async def analyze_transcript_segment(
        self,
        transcript: str,
        speaker: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> MeetingUnderstanding:
        """
        Analyze a segment of meeting transcript.

        Called every 10-30 seconds during meeting with latest transcript.

        Args:
            transcript: Text of what was just said
            speaker: Who said it
            timestamp: When it was said

        Returns:
            MeetingUnderstanding with extracted information
        """
        timestamp = timestamp or datetime.now()

        prompt = self._build_analysis_prompt(transcript, speaker, timestamp)

        try:
            # Call LLM to extract intelligence
            response = await self.llm.chat_json(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.1  # Low temp for consistent extraction
            )

            # Parse response into MeetingUnderstanding
            understanding = self._parse_llm_response(response, timestamp)

            # Update meeting context
            self._update_context(understanding)

            log_event("meeting_segment_analyzed", {
                "num_action_items": len(understanding.action_items),
                "num_decisions": len(understanding.decisions),
                "num_questions": len(understanding.questions),
                "needs_action": understanding.needs_jarvis_action
            })

            return understanding

        except Exception as e:
            log_event("meeting_analysis_failed", {
                "error": str(e)
            })

            # Return empty understanding
            return MeetingUnderstanding(
                action_items=[],
                decisions=[],
                questions=[],
                key_points=[],
                topics_discussed=[],
                sentiment="neutral",
                needs_jarvis_action=False,
                suggested_actions=[]
            )

    def _build_analysis_prompt(
        self,
        transcript: str,
        speaker: Optional[str],
        timestamp: datetime
    ) -> str:
        """Build prompt for LLM analysis"""

        # Get recent context
        recent_topics = self.meeting_context["topics_so_far"][-5:]
        recent_decisions = self.meeting_context["decisions_so_far"][-3:]

        prompt = f"""Analyze this meeting transcript segment and extract key information.

MEETING CONTEXT:
Meeting: {self.meeting_context['meeting_title']}
Participants: {', '.join(self.meeting_context['participants'])}
Time: {timestamp.strftime('%I:%M %p')}
Recent topics: {', '.join(recent_topics) if recent_topics else 'N/A'}
Recent decisions: {', '.join(recent_decisions) if recent_decisions else 'N/A'}

CURRENT TRANSCRIPT:
Speaker: {speaker or 'Unknown'}
"{transcript}"

Extract and return JSON:
{{
  "action_items": [
    {{
      "task": "Clear description of what needs to be done",
      "assignee": "Name of person or null",
      "deadline": "ISO datetime or null",
      "priority": "low|medium|high|urgent",
      "context": "Why this task is needed",
      "mentioned_by": "{speaker}"
    }}
  ],

  "decisions": [
    {{
      "decision": "What was decided",
      "rationale": "Why this decision was made",
      "decided_by": "{speaker} or null",
      "alternatives_considered": ["Option A", "Option B"],
      "impact": "What this decision affects"
    }}
  ],

  "questions": [
    {{
      "question": "The question that was asked",
      "asked_by": "{speaker}",
      "answered": false
    }}
  ],

  "key_points": [
    "Important information mentioned"
  ],

  "topics_discussed": [
    "Main topics in this segment"
  ],

  "sentiment": "positive|neutral|negative",

  "needs_jarvis_action": true|false,

  "suggested_actions": [
    {{
      "action_type": "create_document|query_data|send_message|schedule_meeting|search_info",
      "description": "What JARVIS should do",
      "urgency": "immediate|during_meeting|after_meeting",
      "parameters": {{}}
    }}
  ]
}}

IMPORTANT GUIDELINES:
- Action items: Only extract if someone explicitly requests something to be done
  - "Can someone update the spreadsheet?" → action item
  - "We should think about this" → NOT an action item

- Decisions: Only extract if a clear choice was made
  - "Let's go with Option A" → decision
  - "We're considering Option A" → NOT a decision

- JARVIS actions: Only suggest if task is:
  - Simple (can be done in <30 seconds)
  - Low risk (won't cause problems if wrong)
  - Requested or clearly helpful

- Be conservative: Better to miss than to create false positives

Return ONLY valid JSON, no other text."""

        return prompt

    def _parse_llm_response(
        self,
        response: Dict,
        timestamp: datetime
    ) -> MeetingUnderstanding:
        """Parse LLM JSON response into MeetingUnderstanding"""

        # Parse action items
        action_items = []
        for item in response.get("action_items", []):
            action_items.append(ActionItem(
                task=item["task"],
                assignee=item.get("assignee"),
                deadline=self._parse_deadline(item.get("deadline")),
                priority=Priority(item.get("priority", "medium")),
                context=item.get("context", ""),
                mentioned_by=item.get("mentioned_by"),
                mentioned_at=timestamp
            ))

        # Parse decisions
        decisions = []
        for dec in response.get("decisions", []):
            decisions.append(Decision(
                decision=dec["decision"],
                rationale=dec.get("rationale"),
                decided_by=dec.get("decided_by"),
                decided_at=timestamp,
                alternatives_considered=dec.get("alternatives_considered", []),
                impact=dec.get("impact", "")
            ))

        # Parse questions
        questions = []
        for q in response.get("questions", []):
            questions.append(Question(
                question=q["question"],
                asked_by=q.get("asked_by"),
                asked_at=timestamp,
                answered=q.get("answered", False),
                answer=q.get("answer"),
                answered_by=q.get("answered_by")
            ))

        return MeetingUnderstanding(
            action_items=action_items,
            decisions=decisions,
            questions=questions,
            key_points=response.get("key_points", []),
            topics_discussed=response.get("topics_discussed", []),
            sentiment=response.get("sentiment", "neutral"),
            needs_jarvis_action=response.get("needs_jarvis_action", False),
            suggested_actions=response.get("suggested_actions", [])
        )

    def _parse_deadline(self, deadline_str: Optional[str]) -> Optional[datetime]:
        """Parse deadline string to datetime"""
        if not deadline_str:
            return None

        try:
            return datetime.fromisoformat(deadline_str)
        except (ValueError, TypeError):
            # Try to parse relative deadlines
            lower = deadline_str.lower()

            if "today" in lower or "eod" in lower:
                return datetime.now().replace(hour=17, minute=0, second=0)
            elif "tomorrow" in lower:
                return datetime.now() + timedelta(days=1)
            elif "next week" in lower:
                return datetime.now() + timedelta(weeks=1)
            elif "end of week" in lower:
                # Next Friday
                days_until_friday = (4 - datetime.now().weekday()) % 7
                return datetime.now() + timedelta(days=days_until_friday)

            return None

    def _update_context(self, understanding: MeetingUnderstanding):
        """Update ongoing meeting context"""

        # Add topics
        self.meeting_context["topics_so_far"].extend(
            understanding.topics_discussed
        )

        # Add decisions
        for decision in understanding.decisions:
            self.meeting_context["decisions_so_far"].append(
                decision.decision
            )

        # Add action items
        for item in understanding.action_items:
            self.meeting_context["action_items_so_far"].append(
                item.task
            )
