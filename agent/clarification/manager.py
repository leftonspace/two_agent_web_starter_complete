"""
Clarification Session Manager

Manage the state of clarification sessions and user responses.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from .detector import VagueRequestDetector, ClarityAnalysis, RequestClarity, RequestType
from .generator import QuestionGenerator, ClarifyingQuestion, QuestionSet, QuestionPriority


class SessionStatus(Enum):
    """Status of a clarification session"""
    PENDING = "pending"           # Waiting for user response
    IN_PROGRESS = "in_progress"   # Some questions answered
    COMPLETED = "completed"       # All critical questions answered
    CANCELLED = "cancelled"       # User skipped clarification
    EXPIRED = "expired"           # Session timed out


class ClarificationPhase(Enum):
    """Phase of clarification process (alias for compatibility)"""
    ASKING = "asking"             # Currently asking questions
    READY = "ready"               # All required questions answered
    SKIPPED = "skipped"           # User skipped clarification
    TIMEOUT = "timeout"           # Session timed out
    COMPLETE = "complete"         # Session completed


@dataclass
class Answer:
    """A user's answer to a clarifying question"""
    question: ClarifyingQuestion
    response: str
    answered_at: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0  # How confident the system is in the answer

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "question": self.question.question,
            "related_detail": self.question.related_detail,
            "response": self.response,
            "answered_at": self.answered_at.isoformat(),
            "confidence": self.confidence
        }


@dataclass
class ClarificationSession:
    """A clarification session for a single request"""
    session_id: str
    original_request: str
    analysis: ClarityAnalysis
    question_set: QuestionSet
    status: SessionStatus = SessionStatus.PENDING
    answers: List[Answer] = field(default_factory=list)
    current_question_index: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def current_question(self) -> Optional[ClarifyingQuestion]:
        """Get the current unanswered question"""
        if self.current_question_index < len(self.question_set.questions):
            return self.question_set.questions[self.current_question_index]
        return None

    @property
    def remaining_questions(self) -> List[ClarifyingQuestion]:
        """Get all remaining unanswered questions"""
        return self.question_set.questions[self.current_question_index:]

    @property
    def critical_remaining(self) -> int:
        """Count of remaining critical questions"""
        return len([q for q in self.remaining_questions
                   if q.priority == QuestionPriority.CRITICAL])

    @property
    def progress(self) -> float:
        """Get completion progress (0-1)"""
        total = len(self.question_set.questions)
        if total == 0:
            return 1.0
        return self.current_question_index / total

    @property
    def is_complete(self) -> bool:
        """Check if session is complete"""
        return self.status == SessionStatus.COMPLETED or self.critical_remaining == 0

    @property
    def phase(self) -> ClarificationPhase:
        """Get current phase (alias for compatibility)"""
        if self.status == SessionStatus.COMPLETED:
            return ClarificationPhase.READY
        elif self.status == SessionStatus.CANCELLED:
            return ClarificationPhase.SKIPPED
        elif self.status == SessionStatus.EXPIRED:
            return ClarificationPhase.TIMEOUT
        elif self.status == SessionStatus.IN_PROGRESS or self.status == SessionStatus.PENDING:
            return ClarificationPhase.ASKING
        return ClarificationPhase.ASKING

    @phase.setter
    def phase(self, value: ClarificationPhase):
        """Set phase (updates status)"""
        if value == ClarificationPhase.READY or value == ClarificationPhase.COMPLETE:
            self.status = SessionStatus.COMPLETED
        elif value == ClarificationPhase.SKIPPED:
            self.status = SessionStatus.CANCELLED
        elif value == ClarificationPhase.TIMEOUT:
            self.status = SessionStatus.EXPIRED
        elif value == ClarificationPhase.ASKING:
            self.status = SessionStatus.IN_PROGRESS

    @property
    def enhanced_request(self) -> Optional[str]:
        """Get enhanced request with clarifications"""
        if not self.answers:
            return None
        return self.get_clarified_request()

    @enhanced_request.setter
    def enhanced_request(self, value: str):
        """Set enhanced request (stored in metadata)"""
        self.metadata['enhanced_request'] = value

    @property
    def questions(self) -> List[ClarifyingQuestion]:
        """Get list of questions (alias for question_set.questions)"""
        return self.question_set.questions

    def get_clarified_request(self) -> str:
        """Get the original request enriched with clarifications"""
        if not self.answers:
            return self.original_request

        parts = [self.original_request, "\n\nAdditional details:"]
        for answer in self.answers:
            parts.append(f"- {answer.question.related_detail.replace('_', ' ').title()}: {answer.response}")

        return "\n".join(parts)

    def get_context(self) -> Dict[str, Any]:
        """Get clarification context for downstream processing"""
        return {
            "original_request": self.original_request,
            "request_type": self.analysis.detected_type.value,
            "clarity_level": self.analysis.clarity_level.value,
            "answers": {a.question.related_detail: a.response for a in self.answers},
            "specific_elements": self.analysis.specific_elements,
            "session_id": self.session_id
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "original_request": self.original_request,
            "status": self.status.value,
            "progress": self.progress,
            "answers": [a.to_dict() for a in self.answers],
            "remaining_questions": len(self.remaining_questions),
            "critical_remaining": self.critical_remaining,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class ClarificationManager:
    """Manage clarification sessions"""

    def __init__(
        self,
        clarity_threshold: RequestClarity = RequestClarity.SOMEWHAT_CLEAR,
        max_questions: int = 10,
        skip_phrases: Optional[List[str]] = None
    ):
        """Initialize the manager

        Args:
            clarity_threshold: Clarity level below which to request clarification
            max_questions: Maximum questions per session
            skip_phrases: Phrases that skip clarification
        """
        self.detector = VagueRequestDetector()
        self.generator = QuestionGenerator()
        self.clarity_threshold = clarity_threshold
        self.max_questions = max_questions
        self.skip_phrases = skip_phrases or [
            "just do it", "skip questions", "no questions",
            "figure it out", "use defaults", "your choice", "surprise me"
        ]

        # Active sessions
        self._sessions: Dict[str, ClarificationSession] = {}
        self._active_session_id: Optional[str] = None

        # Settings for test compatibility
        self.allow_skip: bool = True
        self.timeout_minutes: float = 30.0
        self.auto_proceed_on_timeout: bool = False

        # Event callbacks
        self._on_session_start: List[Callable] = []
        self._on_question_asked: List[Callable] = []
        self._on_answer_received: List[Callable] = []
        self._on_session_complete: List[Callable] = []

    @property
    def sessions(self) -> Dict[str, ClarificationSession]:
        """Get all sessions"""
        return self._sessions

    @property
    def active_session_id(self) -> Optional[str]:
        """Get active session ID"""
        return self._active_session_id

    def should_clarify(self, request: str) -> tuple[bool, ClarityAnalysis]:
        """Check if a request needs clarification

        Args:
            request: User's request text

        Returns:
            Tuple of (should_clarify, analysis)
        """
        # Check for skip phrases
        request_lower = request.lower()
        if any(phrase in request_lower for phrase in self.skip_phrases):
            # Still analyze but don't require clarification
            analysis = self.detector.analyze(request)
            return False, analysis

        # Analyze the request
        analysis = self.detector.analyze(request)

        # Check clarity level
        clarity_levels = [
            RequestClarity.VERY_VAGUE,
            RequestClarity.VAGUE,
            RequestClarity.SOMEWHAT_CLEAR,
            RequestClarity.CLEAR
        ]
        request_level = clarity_levels.index(analysis.clarity_level)
        threshold_level = clarity_levels.index(self.clarity_threshold)

        should_clarify = request_level < threshold_level

        return should_clarify, analysis

    def start_session(
        self,
        request: str,
        analysis: Optional[ClarityAnalysis] = None,
        questions: Optional[List[ClarifyingQuestion]] = None,
        session_id: Optional[str] = None
    ) -> ClarificationSession:
        """Start a new clarification session

        Args:
            request: User's request text
            analysis: Optional pre-computed analysis
            questions: Optional pre-defined questions
            session_id: Optional session ID

        Returns:
            New ClarificationSession
        """
        # Use provided analysis or analyze request
        if analysis is None:
            analysis = self.detector.analyze(request)

        # Use provided questions or generate them
        if questions is not None:
            question_set = QuestionSet(
                questions=questions,
                request_type=analysis.detected_type,
                clarity_level=analysis.clarity_level,
                summary="Custom questions provided"
            )
        else:
            question_set = self.generator.generate(analysis)

        # Limit questions
        if len(question_set.questions) > self.max_questions:
            question_set.questions = question_set.questions[:self.max_questions]

        # Create session
        session = ClarificationSession(
            session_id=session_id or str(uuid.uuid4()),
            original_request=request,
            analysis=analysis,
            question_set=question_set,
            status=SessionStatus.PENDING
        )

        # Store session
        self._sessions[session.session_id] = session
        self._active_session_id = session.session_id

        # Trigger callbacks
        for callback in self._on_session_start:
            callback(session)

        return session

    def get_session(self, session_id: str) -> Optional[ClarificationSession]:
        """Get a session by ID

        Args:
            session_id: Session ID

        Returns:
            ClarificationSession if found
        """
        return self._sessions.get(session_id)

    def answer_question(
        self,
        session_id: str,
        response: str,
        confidence: float = 1.0
    ) -> Optional[ClarifyingQuestion]:
        """Record an answer and get the next question

        Args:
            session_id: Session ID
            response: User's response
            confidence: Confidence in the answer (0-1)

        Returns:
            Next question if any, None if complete
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELLED]:
            return None

        # Record answer
        current_question = session.current_question
        if current_question:
            answer = Answer(
                question=current_question,
                response=response,
                confidence=confidence
            )
            session.answers.append(answer)
            session.current_question_index += 1
            session.updated_at = datetime.now()

            # Trigger callbacks
            for callback in self._on_answer_received:
                callback(session, answer)

        # Update status
        if session.status == SessionStatus.PENDING:
            session.status = SessionStatus.IN_PROGRESS

        # Check if complete
        if session.is_complete:
            session.status = SessionStatus.COMPLETED
            for callback in self._on_session_complete:
                callback(session)
            return None

        # Get next question
        next_question = session.current_question
        if next_question:
            for callback in self._on_question_asked:
                callback(session, next_question)

        return next_question

    def skip_session(self, session_id: str) -> bool:
        """Skip/cancel a clarification session

        Args:
            session_id: Session ID

        Returns:
            True if session was cancelled
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.status = SessionStatus.CANCELLED
        session.updated_at = datetime.now()
        return True

    def complete_session(self, session_id: str) -> Optional[ClarificationSession]:
        """Mark a session as complete (even with remaining questions)

        Args:
            session_id: Session ID

        Returns:
            Completed session
        """
        session = self._sessions.get(session_id)
        if not session:
            return None

        session.status = SessionStatus.COMPLETED
        session.updated_at = datetime.now()

        for callback in self._on_session_complete:
            callback(session)

        return session

    def get_quick_clarification(
        self,
        request: str,
        max_questions: int = 3
    ) -> tuple[ClarificationSession, List[ClarifyingQuestion]]:
        """Get a quick clarification with minimal questions

        Args:
            request: User's request
            max_questions: Maximum questions to ask

        Returns:
            Tuple of (session, critical_questions)
        """
        session = self.start_session(request)
        questions = self.generator.generate_quick_questions(
            session.analysis,
            max_questions
        )
        return session, questions

    def process_batch_answers(
        self,
        session_id: str,
        answers: Dict[str, str]
    ) -> bool:
        """Process multiple answers at once

        Args:
            session_id: Session ID
            answers: Dict of detail_name -> response

        Returns:
            True if all answers processed
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Map answers to questions
        for question in session.question_set.questions:
            if question.related_detail in answers:
                answer = Answer(
                    question=question,
                    response=answers[question.related_detail]
                )
                session.answers.append(answer)

        session.current_question_index = len(session.answers)
        session.updated_at = datetime.now()

        # Check completion
        if session.is_complete:
            session.status = SessionStatus.COMPLETED
            for callback in self._on_session_complete:
                callback(session)

        return True

    # Event registration methods
    def on_session_start(self, callback: Callable[[ClarificationSession], None]):
        """Register callback for session start"""
        self._on_session_start.append(callback)

    def on_question_asked(self, callback: Callable[[ClarificationSession, ClarifyingQuestion], None]):
        """Register callback for question asked"""
        self._on_question_asked.append(callback)

    def on_answer_received(self, callback: Callable[[ClarificationSession, Answer], None]):
        """Register callback for answer received"""
        self._on_answer_received.append(callback)

    def on_session_complete(self, callback: Callable[[ClarificationSession], None]):
        """Register callback for session complete"""
        self._on_session_complete.append(callback)

    # Utility methods
    def get_active_sessions(self) -> List[ClarificationSession]:
        """Get all active (non-completed) sessions"""
        return [s for s in self._sessions.values()
                if s.status not in [SessionStatus.COMPLETED, SessionStatus.CANCELLED, SessionStatus.EXPIRED]]

    def cleanup_sessions(self, max_age_hours: int = 24):
        """Remove old sessions

        Args:
            max_age_hours: Maximum age in hours before removal
        """
        now = datetime.now()
        to_remove = []

        for session_id, session in self._sessions.items():
            age = (now - session.created_at).total_seconds() / 3600
            if age > max_age_hours:
                to_remove.append(session_id)

        for session_id in to_remove:
            del self._sessions[session_id]

    def process_answer(
        self,
        response: str,
        question_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process an answer for the active session

        Args:
            response: User's response
            question_id: Optional specific question ID

        Returns:
            Dict with status and next question info
        """
        if not self._active_session_id:
            return {"status": "error", "message": "No active session"}

        session = self._sessions.get(self._active_session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        # Handle skip
        if response.lower() == "skip" and self.allow_skip:
            # Apply defaults for remaining questions
            for q in session.remaining_questions:
                if q.default:
                    session.answers.append(Answer(question=q, response=q.default))
            session.status = SessionStatus.CANCELLED
            return {"status": "skipped"}

        # Get current question or find by ID
        if question_id:
            question = next((q for q in session.question_set.questions if q.id == question_id), None)
        else:
            question = session.current_question

        if not question:
            return {"status": "error", "message": "No current question"}

        # Parse response based on question type
        from .generator import QuestionType
        parsed_response = response

        if question.question_type == QuestionType.MULTIPLE_CHOICE and question.options:
            # Handle letter selection (a, b, c)
            if len(response) == 1 and response.lower() in 'abcdefghij':
                idx = ord(response.lower()) - ord('a')
                if idx < len(question.options):
                    parsed_response = question.options[idx]
            # Handle number selection (1, 2, 3)
            elif response.isdigit():
                idx = int(response) - 1
                if 0 <= idx < len(question.options):
                    parsed_response = question.options[idx]
            # Direct match
            elif response in question.options:
                parsed_response = response

        elif question.question_type == QuestionType.SELECTION and question.options:
            # Handle comma-separated selections
            selected = [s.strip() for s in response.split(',')]
            valid_selections = [s for s in selected if s in question.options]
            parsed_response = valid_selections if valid_selections else selected

        # Store answer (use dict-like access for test compatibility)
        if not hasattr(session, '_answers_dict'):
            session._answers_dict = {}
        session._answers_dict[question.id] = parsed_response

        # Also store as Answer object
        answer = Answer(question=question, response=str(parsed_response))
        if question_id:
            # Find and update existing or add new
            existing = next((i for i, a in enumerate(session.answers) if a.question.id == question_id), None)
            if existing is not None:
                session.answers[existing] = answer
            else:
                session.answers.append(answer)
        else:
            session.answers.append(answer)
            session.current_question_index += 1

        session.updated_at = datetime.now()

        # Update status
        if session.status == SessionStatus.PENDING:
            session.status = SessionStatus.IN_PROGRESS

        # Check if all required questions answered
        required_unanswered = [
            q for q in session.remaining_questions
            if q.required and q.id not in session._answers_dict
        ]

        if not required_unanswered or session.is_complete:
            session.status = SessionStatus.COMPLETED
            # Generate enhanced request
            self._generate_enhanced_request(session)
            return {"status": "complete", "next_question": None}

        return {
            "status": "continue",
            "next_question": session.current_question
        }

    def _generate_enhanced_request(self, session: ClarificationSession):
        """Generate enhanced request from session answers"""
        parts = [session.original_request, "\n\n## Clarifications:"]

        # Use _answers_dict if available, otherwise use answers list
        if hasattr(session, '_answers_dict') and session._answers_dict:
            for key, value in session._answers_dict.items():
                if isinstance(value, list):
                    value = ", ".join(value)
                parts.append(f"- {key.replace('_', ' ').title()}: {value}")
        else:
            for answer in session.answers:
                parts.append(f"- {answer.question.related_detail.replace('_', ' ').title()}: {answer.response}")

        parts.append(f"\n## Project Type: {session.analysis.detected_type.value}")
        session.metadata['enhanced_request'] = "\n".join(parts)

    def complete_clarification(self) -> Dict[str, Any]:
        """Complete the active clarification session

        Returns:
            Dict with completion info
        """
        if not self._active_session_id:
            return {"status": "error", "message": "No active session"}

        session = self._sessions.get(self._active_session_id)
        if not session:
            return {"status": "error", "message": "Session not found"}

        session.status = SessionStatus.COMPLETED
        self._generate_enhanced_request(session)

        for callback in self._on_session_complete:
            callback(session)

        return {
            "status": "complete",
            "enhanced_request": session.enhanced_request
        }

    def timeout_check(self) -> List[str]:
        """Check for timed out sessions

        Returns:
            List of timed out session IDs
        """
        now = datetime.now()
        timed_out = []

        for session_id, session in self._sessions.items():
            if session.status in [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]:
                age_minutes = (now - session.created_at).total_seconds() / 60
                if age_minutes > self.timeout_minutes:
                    session.status = SessionStatus.EXPIRED
                    timed_out.append(session_id)

                    # Auto-proceed with defaults if enabled
                    if self.auto_proceed_on_timeout:
                        for q in session.remaining_questions:
                            if q.default:
                                if not hasattr(session, '_answers_dict'):
                                    session._answers_dict = {}
                                session._answers_dict[q.id] = q.default

        return timed_out

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a session

        Args:
            session_id: Session ID

        Returns:
            Dict with session summary
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "is_complete": session.is_complete,
            "questions_total": len(session.question_set.questions),
            "questions_answered": len(session.answers),
            "phase": session.phase.value,
            "enhanced_request": session.enhanced_request
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics"""
        sessions = list(self._sessions.values())

        if not sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "completed_sessions": 0,
                "average_questions_answered": 0,
                "average_completion_rate": 0
            }

        completed = [s for s in sessions if s.status == SessionStatus.COMPLETED]
        active = [s for s in sessions if s.status in [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]]

        avg_answered = sum(len(s.answers) for s in sessions) / len(sessions)
        avg_completion = sum(s.progress for s in sessions) / len(sessions)

        return {
            "total_sessions": len(sessions),
            "active_sessions": len(active),
            "completed_sessions": len(completed),
            "average_questions_answered": round(avg_answered, 2),
            "average_completion_rate": round(avg_completion * 100, 1)
        }


# Convenience function for simple usage
def clarify_request(
    request: str,
    threshold: RequestClarity = RequestClarity.SOMEWHAT_CLEAR
) -> tuple[bool, Optional[QuestionSet], ClarityAnalysis]:
    """Quick check if request needs clarification

    Args:
        request: User's request text
        threshold: Clarity threshold

    Returns:
        Tuple of (needs_clarification, questions, analysis)
    """
    manager = ClarificationManager(clarity_threshold=threshold)
    needs_clarification, analysis = manager.should_clarify(request)

    if needs_clarification:
        generator = QuestionGenerator()
        questions = generator.generate(analysis)
        return True, questions, analysis

    return False, None, analysis
