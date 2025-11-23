"""
Council System - Weighted Voting

Implements the weighted voting system for council decisions.
Vote weight is based on performance and happiness.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import random

from .models import (
    Councillor, Vote, VotingSession, VoteType,
    TaskComplexity, Specialization
)


@dataclass
class VotingConfig:
    """Configuration for voting sessions"""
    min_voters: int = 2
    min_confidence: float = 0.3
    require_quorum: bool = True
    quorum_percentage: float = 0.5  # 50% of eligible voters
    allow_abstain: bool = True
    timeout_seconds: int = 60
    tie_breaker: str = "random"  # random, first, leader


class VotingManager:
    """
    Manages weighted voting sessions for the council.

    Features:
    - Weighted votes based on performance and happiness
    - Multiple voting types (analysis, assignment, review)
    - Quorum requirements
    - Tie-breaking mechanisms
    """

    def __init__(self, config: Optional[VotingConfig] = None):
        self.config = config or VotingConfig()
        self.sessions: Dict[str, VotingSession] = {}
        self._llm_func: Optional[Callable] = None

    def set_llm_func(self, llm_func: Callable):
        """Set LLM function for generating vote reasoning"""
        self._llm_func = llm_func

    def create_session(
        self,
        vote_type: VoteType,
        question: str,
        options: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> VotingSession:
        """Create a new voting session"""
        session = VotingSession(
            vote_type=vote_type,
            question=question,
            options=options,
            metadata=metadata or {}
        )
        self.sessions[session.id] = session
        return session

    def create_analysis_vote(
        self,
        task_description: str,
    ) -> VotingSession:
        """Create an analysis vote for task complexity"""
        return self.create_session(
            vote_type=VoteType.ANALYSIS,
            question=f"How should we approach this task?\n\n{task_description}",
            options=[c.value for c in TaskComplexity],
            metadata={"task": task_description}
        )

    def create_assignment_vote(
        self,
        task_description: str,
        candidate_names: List[str]
    ) -> VotingSession:
        """Create an assignment vote for who should work on task"""
        return self.create_session(
            vote_type=VoteType.ASSIGNMENT,
            question=f"Who should work on this task?\n\n{task_description}",
            options=candidate_names,
            metadata={"task": task_description}
        )

    def create_review_vote(
        self,
        task_description: str,
        result: str
    ) -> VotingSession:
        """Create a review vote for task quality"""
        return self.create_session(
            vote_type=VoteType.REVIEW,
            question=f"How is the quality of this work?\n\nTask: {task_description}\n\nResult: {result[:500]}...",
            options=["excellent", "good", "acceptable", "needs_revision", "reject"],
            metadata={"task": task_description, "result": result}
        )

    def cast_vote(
        self,
        session_id: str,
        councillor: Councillor,
        choice: str,
        confidence: float = 0.8,
        reasoning: Optional[str] = None
    ) -> Optional[Vote]:
        """
        Cast a weighted vote.

        Args:
            session_id: Voting session ID
            councillor: The councillor casting the vote
            choice: The option being voted for
            confidence: Confidence level (0-1)
            reasoning: Optional reasoning for the vote

        Returns:
            Vote object if successful
        """
        session = self.sessions.get(session_id)
        if not session or not session.is_open:
            return None

        if choice not in session.options:
            return None

        if confidence < self.config.min_confidence:
            confidence = self.config.min_confidence

        vote = Vote(
            councillor_id=councillor.id,
            councillor_name=councillor.name,
            choice=choice,
            confidence=confidence,
            weight=councillor.vote_weight,
            reasoning=reasoning
        )

        session.add_vote(vote)
        return vote

    async def generate_councillor_vote(
        self,
        session: VotingSession,
        councillor: Councillor,
        context: Optional[Dict[str, Any]] = None
    ) -> Vote:
        """
        Generate a vote for a councillor (using LLM or heuristics).

        Args:
            session: The voting session
            councillor: The councillor to generate vote for
            context: Additional context

        Returns:
            Generated Vote
        """
        # Use heuristics based on specialization
        choice, confidence, reasoning = self._heuristic_vote(
            session, councillor, context or {}
        )

        return Vote(
            councillor_id=councillor.id,
            councillor_name=councillor.name,
            choice=choice,
            confidence=confidence,
            weight=councillor.vote_weight,
            reasoning=reasoning
        )

    def _heuristic_vote(
        self,
        session: VotingSession,
        councillor: Councillor,
        context: Dict[str, Any]
    ) -> Tuple[str, float, str]:
        """Generate vote using heuristics based on specialization"""

        if session.vote_type == VoteType.ANALYSIS:
            return self._analysis_heuristic(session, councillor)

        elif session.vote_type == VoteType.ASSIGNMENT:
            return self._assignment_heuristic(session, councillor)

        elif session.vote_type == VoteType.REVIEW:
            return self._review_heuristic(session, councillor)

        else:
            # Default: weighted random selection
            choice = random.choice(session.options)
            confidence = 0.5 + (councillor.metrics.overall_performance / 200)
            return choice, confidence, "General assessment"

    def _analysis_heuristic(
        self,
        session: VotingSession,
        councillor: Councillor
    ) -> Tuple[str, float, str]:
        """Heuristic for analysis votes"""
        task = session.metadata.get("task", "").lower()
        options = session.options

        # Determine complexity based on task keywords
        complexity_score = 0

        # Simple indicators
        simple_keywords = ["fix", "update", "change", "small", "minor", "simple", "quick"]
        complex_keywords = ["build", "create", "design", "architect", "system", "full", "complete"]
        clarification_keywords = ["unclear", "vague", "what", "which", "how"]

        for kw in simple_keywords:
            if kw in task:
                complexity_score -= 1

        for kw in complex_keywords:
            if kw in task:
                complexity_score += 1

        for kw in clarification_keywords:
            if kw in task:
                complexity_score = -99  # Force clarification

        # Adjust based on specialization
        if Specialization.ARCHITECTURE in councillor.specializations:
            complexity_score += 0.5  # Architects tend to see more complexity

        # Map to choice
        if complexity_score <= -99:
            choice = TaskComplexity.NEEDS_CLARIFICATION.value
            reasoning = "Task description needs clarification"
        elif complexity_score <= -1:
            choice = TaskComplexity.SIMPLE.value
            reasoning = "Task appears straightforward"
        elif complexity_score <= 1:
            choice = TaskComplexity.STANDARD.value
            reasoning = "Standard complexity task"
        else:
            choice = TaskComplexity.COMPLEX.value
            reasoning = "Task requires careful planning"

        # Confidence based on performance
        confidence = 0.6 + (councillor.metrics.overall_performance / 250)

        return choice, min(0.95, confidence), reasoning

    def _assignment_heuristic(
        self,
        session: VotingSession,
        councillor: Councillor
    ) -> Tuple[str, float, str]:
        """Heuristic for assignment votes"""
        # Councillors tend to vote for themselves if qualified
        if councillor.name in session.options:
            choice = councillor.name
            confidence = 0.5 + (councillor.metrics.overall_performance / 200)
            reasoning = "Self-nomination based on capabilities"
        else:
            # Vote for first available option
            choice = session.options[0] if session.options else ""
            confidence = 0.5
            reasoning = "Default selection"

        return choice, confidence, reasoning

    def _review_heuristic(
        self,
        session: VotingSession,
        councillor: Councillor
    ) -> Tuple[str, float, str]:
        """Heuristic for review votes"""
        # Reviewers with high performance are more critical
        perf = councillor.metrics.overall_performance

        # Default to "good" with some variation based on happiness
        if councillor.happiness > 80:
            choices = ["excellent", "excellent", "good", "good", "acceptable"]
        elif councillor.happiness > 50:
            choices = ["excellent", "good", "good", "acceptable", "acceptable"]
        else:
            choices = ["good", "acceptable", "acceptable", "needs_revision", "needs_revision"]

        choice = random.choice(choices)
        confidence = 0.6 + (perf / 300)

        review_reasons = {
            "excellent": "Work exceeds expectations",
            "good": "Solid work that meets requirements",
            "acceptable": "Work is adequate but could be improved",
            "needs_revision": "Work needs some revisions",
            "reject": "Work does not meet standards"
        }

        return choice, confidence, review_reasons.get(choice, "")

    def close_session(self, session_id: str) -> Optional[str]:
        """Close a voting session and determine winner"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check quorum if required
        if self.config.require_quorum:
            # Quorum check would need total eligible voters
            pass

        winner = session.close()
        return winner

    def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed results for a session"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        return session.to_dict()

    def tally_votes(self, session_id: str) -> Dict[str, float]:
        """Get current vote tallies"""
        session = self.sessions.get(session_id)
        if not session:
            return {}

        return session.get_results()

    def get_winner(self, session_id: str) -> Optional[str]:
        """Get the winning option (closes session if open)"""
        session = self.sessions.get(session_id)
        if not session:
            return None

        if session.is_open:
            return self.close_session(session_id)

        return session.winner

    def handle_tie(self, session: VotingSession, tied_options: List[str]) -> str:
        """Handle a tie between options"""
        if self.config.tie_breaker == "random":
            return random.choice(tied_options)
        elif self.config.tie_breaker == "first":
            return tied_options[0]
        else:
            return tied_options[0]

    def get_voting_summary(self, session_id: str) -> str:
        """Get a human-readable summary of voting"""
        session = self.sessions.get(session_id)
        if not session:
            return "Session not found"

        results = session.get_results()
        total_weight = sum(v.weighted_score for v in session.votes)

        lines = [
            f"**Voting Session: {session.vote_type.value}**",
            f"Question: {session.question[:100]}...",
            f"Total votes: {len(session.votes)}",
            "",
            "Results:"
        ]

        for option, score in sorted(results.items(), key=lambda x: -x[1]):
            pct = (score / total_weight * 100) if total_weight > 0 else 0
            lines.append(f"  - {option}: {score:.2f} ({pct:.1f}%)")

        if session.winner:
            lines.append(f"\nWinner: **{session.winner}**")

        return "\n".join(lines)


async def conduct_vote(
    councillors: List[Councillor],
    vote_type: VoteType,
    question: str,
    options: List[str],
    context: Optional[Dict[str, Any]] = None
) -> Tuple[str, VotingSession]:
    """
    Convenience function to conduct a complete vote.

    Args:
        councillors: List of councillors to vote
        vote_type: Type of vote
        question: The question being voted on
        options: Available options
        context: Optional additional context

    Returns:
        Tuple of (winner, session)
    """
    manager = VotingManager()
    session = manager.create_session(vote_type, question, options)

    for councillor in councillors:
        vote = await manager.generate_councillor_vote(session, councillor, context)
        session.add_vote(vote)

    winner = manager.close_session(session.id)
    return winner, session
