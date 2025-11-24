"""
Council System - Core Models

Data models for the gamified meta-orchestration council system.
Includes Councillor, Vote, Task, and Performance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid


class Specialization(Enum):
    """Councillor specializations"""
    CODING = "coding"
    DESIGN = "design"
    TESTING = "testing"
    REVIEW = "review"
    ARCHITECTURE = "architecture"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    SECURITY = "security"
    DATA = "data"
    RESEARCH = "research"


class CouncillorStatus(Enum):
    """Councillor employment status"""
    PROBATION = "probation"  # New councillor, being evaluated
    ACTIVE = "active"        # Full councillor
    SUSPENDED = "suspended"  # Temporarily inactive
    FIRED = "fired"          # Terminated


class TaskComplexity(Enum):
    """Task complexity levels from council voting"""
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"
    NEEDS_CLARIFICATION = "needs_clarification"


class VoteType(Enum):
    """Types of council votes"""
    ANALYSIS = "analysis"           # How to approach task
    ASSIGNMENT = "assignment"       # Who should work on task
    REVIEW = "review"               # Quality review
    DECISION = "decision"           # General decision
    FIRE_COUNCILLOR = "fire"        # Vote to fire
    SPAWN_COUNCILLOR = "spawn"      # Vote to hire
    BEST_ANSWER = "best_answer"     # Vote on whose answer is best (competitive)


@dataclass
class PerformanceMetrics:
    """Performance tracking for a councillor"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_quality_score: float = 0.0
    total_speed_score: float = 0.0
    positive_feedback: int = 0
    negative_feedback: int = 0
    votes_won: int = 0
    votes_lost: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_task_at: Optional[datetime] = None
    joined_at: datetime = field(default_factory=datetime.now)

    # Competitive council tracking
    competitive_rounds: int = 0          # Total rounds participated in
    competitive_wins: int = 0            # Times voted as "best answer"
    competitive_losses: int = 0          # Times NOT voted as best
    current_round_streak: int = 0        # Current win/loss streak (positive = wins)
    round_history: List[Dict] = field(default_factory=list)  # Last N rounds

    @property
    def success_rate(self) -> float:
        """Calculate task success rate"""
        total = self.tasks_completed + self.tasks_failed
        if total == 0:
            return 0.5  # Default for new councillors
        return self.tasks_completed / total

    @property
    def quality_average(self) -> float:
        """Calculate average quality score"""
        if self.tasks_completed == 0:
            return 0.5
        return self.total_quality_score / self.tasks_completed

    @property
    def speed_average(self) -> float:
        """Calculate average speed score"""
        if self.tasks_completed == 0:
            return 0.5
        return self.total_speed_score / self.tasks_completed

    @property
    def feedback_ratio(self) -> float:
        """Calculate positive feedback ratio"""
        total = self.positive_feedback + self.negative_feedback
        if total == 0:
            return 0.5
        return self.positive_feedback / total

    @property
    def overall_performance(self) -> float:
        """
        Calculate overall performance score (0-100).

        Weighted combination of:
        - Success rate (40%)
        - Quality average (30%)
        - Speed average (15%)
        - Feedback ratio (15%)
        """
        return (
            self.success_rate * 40 +
            self.quality_average * 30 +
            self.speed_average * 15 +
            self.feedback_ratio * 15
        )

    def record_task_success(self, quality: float = 0.8, speed: float = 0.8):
        """Record a successful task completion"""
        self.tasks_completed += 1
        self.total_quality_score += quality
        self.total_speed_score += speed
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_task_at = datetime.now()

    def record_task_failure(self):
        """Record a task failure"""
        self.tasks_failed += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_task_at = datetime.now()

    def record_feedback(self, positive: bool):
        """Record user feedback"""
        if positive:
            self.positive_feedback += 1
        else:
            self.negative_feedback += 1

    def record_vote_result(self, won: bool):
        """Record vote outcome"""
        if won:
            self.votes_won += 1
        else:
            self.votes_lost += 1

    def record_competitive_round(self, won: bool, task_id: str = "", score: float = 0.0):
        """Record a competitive round result (best answer voting)"""
        self.competitive_rounds += 1

        if won:
            self.competitive_wins += 1
            if self.current_round_streak >= 0:
                self.current_round_streak += 1
            else:
                self.current_round_streak = 1
        else:
            self.competitive_losses += 1
            if self.current_round_streak <= 0:
                self.current_round_streak -= 1
            else:
                self.current_round_streak = -1

        # Keep last 20 rounds of history
        self.round_history.append({
            "task_id": task_id,
            "won": won,
            "score": score,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.round_history) > 20:
            self.round_history = self.round_history[-20:]

    @property
    def competitive_win_rate(self) -> float:
        """Calculate competitive win rate"""
        total = self.competitive_wins + self.competitive_losses
        if total == 0:
            return 0.5
        return self.competitive_wins / total

    @property
    def competitive_score(self) -> float:
        """
        Calculate competitive score for graveyard evaluation.
        Lower score = higher risk of termination.

        Based on:
        - Win rate (60%)
        - Recent performance from round_history (30%)
        - Streak bonus/penalty (10%)
        """
        win_rate_score = self.competitive_win_rate * 60

        # Recent performance (last 10 rounds)
        recent = self.round_history[-10:] if self.round_history else []
        if recent:
            recent_wins = sum(1 for r in recent if r.get("won", False))
            recent_score = (recent_wins / len(recent)) * 30
        else:
            recent_score = 15  # Neutral for new councillors

        # Streak bonus/penalty
        streak_score = min(10, max(-10, self.current_round_streak)) + 10  # 0-20 range, normalized to 0-10

        return win_rate_score + recent_score + (streak_score / 2)


@dataclass
class Councillor:
    """
    A specialist agent in the council with performance metrics and happiness.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    specializations: List[Specialization] = field(default_factory=list)
    status: CouncillorStatus = CouncillorStatus.PROBATION
    happiness: float = 70.0  # 0-100 scale
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    base_vote_weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    # Execution function (set externally)
    _execute_func: Optional[Callable] = field(default=None, repr=False)

    def __post_init__(self):
        if not self.name:
            self.name = f"Councillor_{self.id}"

    @property
    def performance_coefficient(self) -> float:
        """
        Calculate performance coefficient for vote weight.

        - 100% performance = 2.0x
        - 75% performance = 1.5x
        - 50% performance = 1.0x (baseline)
        - 25% performance = 0.5x
        """
        perf = self.metrics.overall_performance / 100
        return 0.5 + (perf * 1.5)

    @property
    def happiness_modifier(self) -> float:
        """
        Calculate happiness modifier for vote weight.

        Uses unified linear formula for smooth transitions:
        - 100 happiness = 1.3x
        - 70 happiness = 1.09x
        - 50 happiness = 0.95x
        - 0 happiness = 0.6x
        """
        # Unified linear formula: 0.6 at happiness=0, 1.3 at happiness=100
        # This avoids discontinuity at the old boundary (happiness=70)
        return 0.6 + (self.happiness / 100 * 0.7)

    @property
    def vote_weight(self) -> float:
        """
        Calculate total vote weight.

        vote_weight = base × performance_coefficient × happiness_modifier
        """
        return self.base_vote_weight * self.performance_coefficient * self.happiness_modifier

    def is_fireable(
        self,
        performance_threshold: float = 40.0,
        consecutive_failures_threshold: int = 5,
        happiness_threshold: float = 20.0
    ) -> bool:
        """
        Check if councillor meets firing criteria.

        Args:
            performance_threshold: Fire if performance below this (default: 40%)
            consecutive_failures_threshold: Fire if consecutive failures >= this (default: 5)
            happiness_threshold: Fire if happiness below this (default: 20)

        Returns:
            True if councillor should be fired
        """
        return (
            self.metrics.overall_performance < performance_threshold or
            self.metrics.consecutive_failures >= consecutive_failures_threshold or
            self.happiness < happiness_threshold
        )

    def is_promotable(
        self,
        min_tasks: int = 10,
        min_performance: float = 60.0
    ) -> bool:
        """
        Check if councillor can be promoted from probation.

        Args:
            min_tasks: Minimum tasks completed (default: 10)
            min_performance: Minimum performance score (default: 60%)

        Returns:
            True if councillor can be promoted
        """
        return (
            self.status == CouncillorStatus.PROBATION and
            self.metrics.tasks_completed >= min_tasks and
            self.metrics.overall_performance >= min_performance
        )

    def has_specialization(self, spec: Specialization) -> bool:
        """Check if councillor has a specialization"""
        return spec in self.specializations

    def adjust_happiness(self, amount: float):
        """Adjust happiness, clamping to 0-100"""
        self.happiness = max(0, min(100, self.happiness + amount))

    async def execute(self, task: str, context: Dict[str, Any] = None) -> str:
        """Execute a task"""
        if self._execute_func:
            return await self._execute_func(task, context or {})
        return f"[{self.name}] Processed: {task}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "specializations": [s.value for s in self.specializations],
            "status": self.status.value,
            "happiness": self.happiness,
            "vote_weight": self.vote_weight,
            "performance": self.metrics.overall_performance,
            "tasks_completed": self.metrics.tasks_completed,
            "success_rate": self.metrics.success_rate,
        }


@dataclass
class Vote:
    """A vote cast by a councillor"""
    councillor_id: str
    councillor_name: str
    choice: str
    confidence: float  # 0-1
    weight: float
    reasoning: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def weighted_score(self) -> float:
        """Calculate weighted vote score"""
        return self.confidence * self.weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            "councillor_id": self.councillor_id,
            "councillor_name": self.councillor_name,
            "choice": self.choice,
            "confidence": self.confidence,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "reasoning": self.reasoning,
        }


@dataclass
class VotingSession:
    """A voting session with multiple councillors"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    vote_type: VoteType = VoteType.DECISION
    question: str = ""
    options: List[str] = field(default_factory=list)
    votes: List[Vote] = field(default_factory=list)
    winner: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_open(self) -> bool:
        """Check if voting is still open"""
        return self.closed_at is None

    @property
    def total_votes(self) -> int:
        """Get total number of votes"""
        return len(self.votes)

    def add_vote(self, vote: Vote):
        """Add a vote to the session"""
        if self.is_open:
            self.votes.append(vote)

    def get_results(self) -> Dict[str, float]:
        """Get weighted vote totals for each option"""
        results = {option: 0.0 for option in self.options}
        for vote in self.votes:
            if vote.choice in results:
                results[vote.choice] += vote.weighted_score
        return results

    def close(self) -> str:
        """Close voting and determine winner"""
        if not self.is_open:
            return self.winner

        self.closed_at = datetime.now()
        results = self.get_results()

        if results:
            self.winner = max(results, key=results.get)
        else:
            self.winner = self.options[0] if self.options else None

        return self.winner

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vote_type": self.vote_type.value,
            "question": self.question,
            "options": self.options,
            "votes": [v.to_dict() for v in self.votes],
            "results": self.get_results(),
            "winner": self.winner,
            "is_open": self.is_open,
        }


@dataclass
class CouncilTask:
    """A task being processed by the council"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    complexity: Optional[TaskComplexity] = None
    assigned_councillors: List[str] = field(default_factory=list)
    analysis_vote: Optional[VotingSession] = None
    review_vote: Optional[VotingSession] = None
    status: str = "pending"  # pending, in_progress, review, completed, failed
    result: Optional[str] = None
    quality_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description[:100],
            "complexity": self.complexity.value if self.complexity else None,
            "assigned_councillors": self.assigned_councillors,
            "status": self.status,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class BonusPool:
    """Bonus pool for rewarding councillors"""
    balance: float = 100.0
    max_balance: float = 500.0
    replenish_rate: float = 5.0  # Per successful user satisfaction
    history: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, amount: float, reason: str = ""):
        """Add to the bonus pool"""
        old_balance = self.balance
        self.balance = min(self.max_balance, self.balance + amount)
        self.history.append({
            "type": "add",
            "amount": amount,
            "reason": reason,
            "old_balance": old_balance,
            "new_balance": self.balance,
            "timestamp": datetime.now().isoformat()
        })

    def withdraw(self, amount: float, recipient: str, reason: str = "") -> float:
        """Withdraw from bonus pool (returns actual amount withdrawn)"""
        actual = min(amount, self.balance)
        old_balance = self.balance
        self.balance -= actual
        self.history.append({
            "type": "withdraw",
            "amount": actual,
            "recipient": recipient,
            "reason": reason,
            "old_balance": old_balance,
            "new_balance": self.balance,
            "timestamp": datetime.now().isoformat()
        })
        return actual

    def replenish(self, user_satisfaction: float = 1.0):
        """Replenish based on user satisfaction (0-1)"""
        amount = self.replenish_rate * user_satisfaction
        self.add(amount, f"User satisfaction: {user_satisfaction:.0%}")
