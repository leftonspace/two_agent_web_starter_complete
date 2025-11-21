"""
Meeting session manager.

Orchestrates entire meeting flow:
- Join meeting
- Listen and transcribe
- Analyze and understand
- Execute actions
- Generate summary
"""

import asyncio
from typing import Optional, Dict, List
from datetime import datetime

from agent.meetings.factory import create_meeting_bot
from agent.meetings.base import MeetingInfo, MeetingPlatform
from agent.meetings.transcription.manager import TranscriptionManager
from agent.meetings.diarization.speaker_manager import SpeakerManager
from agent.meetings.intelligence.meeting_analyzer import MeetingAnalyzer
from agent.meetings.intelligence.action_executor import MeetingActionExecutor
from agent.llm_client import LLMClient
from agent.core_logging import log_event


class MeetingSession:
    """
    Complete meeting session orchestrator.

    Handles end-to-end meeting participation.
    """

    def __init__(
        self,
        meeting_info: MeetingInfo,
        llm_client: LLMClient
    ):
        self.meeting_info = meeting_info
        self.llm = llm_client

        # Components
        self.bot = None
        self.transcription_manager = TranscriptionManager()
        self.speaker_manager = None  # Will be initialized with engine
        self.meeting_analyzer = MeetingAnalyzer(llm_client)
        self.action_executor = MeetingActionExecutor(llm_client)

        # Meeting data
        self.meeting_title = meeting_info.title
        self.start_time = None
        self.end_time = None
        self.full_transcript = []
        self.all_action_items = []
        self.all_decisions = []
        self.all_questions = []

    async def join_and_participate(self):
        """
        Join meeting and participate actively.

        Main entry point for JARVIS meeting participation.
        """
        try:
            # 1. Join meeting
            await self._join_meeting()

            # 2. Get participants
            await self._setup_participants()

            # 3. Listen, understand, and act
            await self._active_participation_loop()

            # 4. Leave meeting
            await self._leave_meeting()

            # 5. Generate summary
            summary = await self._generate_meeting_summary()

            return summary

        except Exception as e:
            log_event("meeting_session_failed", {
                "error": str(e)
            })
            raise

    async def _join_meeting(self):
        """Join the meeting"""
        log_event("joining_meeting", {
            "platform": self.meeting_info.platform.value,
            "meeting_id": self.meeting_info.meeting_id
        })

        # Create bot
        self.bot = create_meeting_bot(self.meeting_info)

        # Connect and join
        await self.bot.connect()
        await self.bot.join_meeting()

        self.start_time = datetime.now()

        log_event("meeting_joined", {
            "start_time": self.start_time.isoformat()
        })

    async def _setup_participants(self):
        """Get and setup participant information"""
        participants = await self.bot.get_participants()

        # Initialize speaker manager if we have diarization
        try:
            from agent.meetings.diarization.pyannote_engine import PyannoteEngine
            diarization_engine = PyannoteEngine()
            self.speaker_manager = SpeakerManager(diarization_engine)
            self.speaker_manager.set_meeting_participants(participants)
        except ImportError:
            log_event("diarization_unavailable", {
                "message": "Pyannote not installed, skipping speaker diarization"
            })
            self.speaker_manager = None

        self.meeting_analyzer.meeting_context["participants"] = [
            p["name"] for p in participants
        ]

        log_event("participants_setup", {
            "num_participants": len(participants)
        })

    async def _active_participation_loop(self):
        """
        Main loop: Listen → Transcribe → Understand → Act

        Runs throughout the meeting.
        """
        audio_stream = self.bot.get_audio_stream()

        # Start transcription
        transcript_stream = self.transcription_manager.start_transcription(
            audio_stream
        )

        # Buffer for accumulating transcript
        transcript_buffer = []
        last_analysis_time = datetime.now()

        async for transcript_segment in transcript_stream:
            # Add to buffer
            transcript_buffer.append(transcript_segment.text)
            self.full_transcript.append({
                "text": transcript_segment.text,
                "timestamp": datetime.now(),
                "is_final": transcript_segment.is_final
            })

            # Analyze every 30 seconds or when final segment
            time_since_analysis = (datetime.now() - last_analysis_time).total_seconds()

            if transcript_segment.is_final and time_since_analysis > 30:
                # Combine buffered transcript
                combined_transcript = " ".join(transcript_buffer)

                # Analyze
                understanding = await self.meeting_analyzer.analyze_transcript_segment(
                    transcript=combined_transcript,
                    speaker=None,  # Would be from diarization
                    timestamp=datetime.now()
                )

                # Execute actions if needed
                actions_taken = await self.action_executor.process_understanding(
                    understanding
                )

                # Store extracted information
                self.all_action_items.extend(understanding.action_items)
                self.all_decisions.extend(understanding.decisions)
                self.all_questions.extend(understanding.questions)

                # Announce actions in meeting
                if actions_taken:
                    for action in actions_taken:
                        await self._announce_action(action)

                # Clear buffer and reset timer
                transcript_buffer = []
                last_analysis_time = datetime.now()

    async def _announce_action(self, action: Dict):
        """Announce action taken in meeting chat"""
        message = f"✓ {action.get('description', 'Action completed')}"

        # Send to meeting chat (if supported)
        if hasattr(self.bot, 'send_chat_message'):
            try:
                await self.bot.send_chat_message(message)
            except Exception as e:
                log_event("chat_message_failed", {
                    "error": str(e)
                })

        log_event("action_announced", {
            "action_type": action.get("action_type"),
            "description": action.get("description")
        })

    async def _leave_meeting(self):
        """Leave the meeting"""
        if self.bot:
            await self.bot.leave_meeting()

        self.end_time = datetime.now()

        log_event("meeting_left", {
            "end_time": self.end_time.isoformat(),
            "duration_minutes": (self.end_time - self.start_time).total_seconds() / 60
        })

    async def _generate_meeting_summary(self) -> str:
        """Generate comprehensive meeting summary"""
        duration = self.end_time - self.start_time

        summary = f"""# Meeting Summary

**Meeting:** {self.meeting_title}
**Date:** {self.start_time.strftime('%Y-%m-%d')}
**Time:** {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}
**Duration:** {duration.total_seconds() / 60:.0f} minutes
**Participants:** {', '.join(self.meeting_analyzer.meeting_context['participants'])}

## Action Items ({len(self.all_action_items)})

"""

        for i, item in enumerate(self.all_action_items, 1):
            summary += f"{i}. **{item.task}**\n"
            summary += f"   - Assignee: {item.assignee or 'Unassigned'}\n"
            summary += f"   - Deadline: {item.deadline.strftime('%Y-%m-%d') if item.deadline else 'No deadline'}\n"
            summary += f"   - Priority: {item.priority.value}\n\n"

        summary += f"\n## Decisions ({len(self.all_decisions)})\n\n"

        for i, decision in enumerate(self.all_decisions, 1):
            summary += f"{i}. {decision.decision}\n"
            summary += f"   - Decided by: {decision.decided_by or 'Group decision'}\n"
            summary += f"   - Rationale: {decision.rationale or 'N/A'}\n\n"

        summary += f"\n## Questions ({len(self.all_questions)})\n\n"

        for i, question in enumerate(self.all_questions, 1):
            status = "✓ Answered" if question.answered else "⚠ Unanswered"
            summary += f"{i}. {question.question} ({status})\n"
            summary += f"   - Asked by: {question.asked_by or 'Unknown'}\n"
            if question.answered:
                summary += f"   - Answer: {question.answer}\n"
            summary += "\n"

        summary += "\n## JARVIS Actions\n\n"
        summary += self.action_executor.get_actions_summary()

        # Save summary
        summary_path = f"./meetings/summaries/{self.meeting_info.meeting_id}_{self.start_time.strftime('%Y%m%d')}.md"

        log_event("meeting_summary_generated", {
            "summary_path": summary_path,
            "action_items": len(self.all_action_items),
            "decisions": len(self.all_decisions)
        })

        return summary
