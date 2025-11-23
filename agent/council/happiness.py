"""
Council System - Happiness Management

Manages councillor happiness levels based on events and interactions.
Happiness affects work quality and vote weight.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .models import Councillor, BonusPool


class HappinessEvent(Enum):
    """Events that affect councillor happiness"""
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    BONUS_RECEIVED = "bonus_received"
    CRITICISM = "criticism"
    PRAISE = "praise"
    OVERWORKED = "overworked"
    VOTE_WON = "vote_won"
    VOTE_LOST = "vote_lost"  # Added: for when vote didn't win (no impact)
    VOTE_IGNORED = "vote_ignored"
    COLLEAGUE_FIRED = "colleague_fired"
    NEW_COLLEAGUE = "new_colleague"
    PROMOTION = "promotion"
    REST_DAY = "rest_day"
    CHALLENGING_TASK = "challenging_task"
    BORING_TASK = "boring_task"
    TEAM_SUCCESS = "team_success"
    TEAM_FAILURE = "team_failure"
    DECAY = "decay"  # Added: for natural happiness decay


# Happiness impact values
HAPPINESS_IMPACTS: Dict[HappinessEvent, float] = {
    HappinessEvent.TASK_SUCCESS: +5,
    HappinessEvent.TASK_FAILURE: -8,
    HappinessEvent.BONUS_RECEIVED: +15,
    HappinessEvent.CRITICISM: -10,
    HappinessEvent.PRAISE: +8,
    HappinessEvent.OVERWORKED: -12,
    HappinessEvent.VOTE_WON: +3,
    HappinessEvent.VOTE_LOST: 0,  # No impact for normal vote loss
    HappinessEvent.VOTE_IGNORED: -5,
    HappinessEvent.COLLEAGUE_FIRED: -8,
    HappinessEvent.NEW_COLLEAGUE: +2,
    HappinessEvent.PROMOTION: +20,
    HappinessEvent.REST_DAY: +5,
    HappinessEvent.CHALLENGING_TASK: +3,
    HappinessEvent.BORING_TASK: -3,
    HappinessEvent.TEAM_SUCCESS: +5,
    HappinessEvent.TEAM_FAILURE: -5,
    HappinessEvent.DECAY: 0,  # Decay impact is calculated dynamically
}


@dataclass
class HappinessRecord:
    """Record of a happiness change"""
    councillor_id: str
    event: HappinessEvent
    impact: float
    old_happiness: float
    new_happiness: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "councillor_id": self.councillor_id,
            "event": self.event.value,
            "impact": self.impact,
            "old_happiness": self.old_happiness,
            "new_happiness": self.new_happiness,
            "timestamp": self.timestamp.isoformat(),
        }


class HappinessManager:
    """
    Manages councillor happiness levels.

    Happiness affects:
    - Vote weight (happy councillors have more influence)
    - Work quality (simulated)
    - Risk of leaving/being fired

    Events trigger happiness changes according to HAPPINESS_IMPACTS.
    """

    def __init__(self, custom_impacts: Optional[Dict[HappinessEvent, float]] = None):
        """
        Initialize happiness manager.

        Args:
            custom_impacts: Optional custom impact values to override defaults
        """
        self.impacts = HAPPINESS_IMPACTS.copy()
        if custom_impacts:
            self.impacts.update(custom_impacts)

        self.history: List[HappinessRecord] = []
        self._decay_rate = 0.5  # Happiness decay per evaluation period
        self._min_happiness = 0.0
        self._max_happiness = 100.0
        self._warning_threshold = 30.0
        self._critical_threshold = 20.0

    def apply_event(
        self,
        councillor: Councillor,
        event: HappinessEvent,
        multiplier: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HappinessRecord:
        """
        Apply a happiness event to a councillor.

        Args:
            councillor: The councillor to affect
            event: The happiness event
            multiplier: Optional multiplier for the impact
            metadata: Optional additional data

        Returns:
            HappinessRecord documenting the change
        """
        base_impact = self.impacts.get(event, 0)
        actual_impact = base_impact * multiplier

        old_happiness = councillor.happiness
        councillor.adjust_happiness(actual_impact)

        record = HappinessRecord(
            councillor_id=councillor.id,
            event=event,
            impact=actual_impact,
            old_happiness=old_happiness,
            new_happiness=councillor.happiness,
            metadata=metadata or {}
        )

        self.history.append(record)
        return record

    def apply_task_result(
        self,
        councillor: Councillor,
        success: bool,
        quality_score: Optional[float] = None,
        was_challenging: bool = False
    ) -> List[HappinessRecord]:
        """
        Apply happiness changes for a task result.

        Args:
            councillor: The councillor who did the task
            success: Whether the task succeeded
            quality_score: Optional quality score (0-1)
            was_challenging: Whether the task was challenging

        Returns:
            List of happiness records
        """
        records = []

        # Base success/failure impact
        if success:
            record = self.apply_event(councillor, HappinessEvent.TASK_SUCCESS)
            records.append(record)

            # Extra boost for high quality
            if quality_score and quality_score >= 0.9:
                record = self.apply_event(
                    councillor,
                    HappinessEvent.PRAISE,
                    multiplier=0.5,
                    metadata={"reason": "high_quality_work"}
                )
                records.append(record)
        else:
            record = self.apply_event(councillor, HappinessEvent.TASK_FAILURE)
            records.append(record)

        # Challenging task bonus
        if was_challenging and success:
            record = self.apply_event(councillor, HappinessEvent.CHALLENGING_TASK)
            records.append(record)

        return records

    def apply_vote_result(
        self,
        councillor: Councillor,
        won: bool,
        was_ignored: bool = False
    ) -> HappinessRecord:
        """
        Apply happiness change for a vote result.

        Args:
            councillor: The councillor who voted
            won: Whether their vote choice won
            was_ignored: Whether their vote was ignored

        Returns:
            HappinessRecord
        """
        if was_ignored:
            return self.apply_event(councillor, HappinessEvent.VOTE_IGNORED)
        elif won:
            return self.apply_event(councillor, HappinessEvent.VOTE_WON)
        else:
            # Record vote loss with correct event type (no happiness impact)
            record = HappinessRecord(
                councillor_id=councillor.id,
                event=HappinessEvent.VOTE_LOST,
                impact=0,
                old_happiness=councillor.happiness,
                new_happiness=councillor.happiness
            )
            self.history.append(record)
            return record

    def apply_bonus(
        self,
        councillor: Councillor,
        bonus_pool: BonusPool,
        amount: float,
        reason: str = "performance"
    ) -> Optional[HappinessRecord]:
        """
        Award a bonus from the pool.

        Args:
            councillor: The councillor receiving bonus
            bonus_pool: The bonus pool to withdraw from
            amount: Requested amount
            reason: Reason for bonus

        Returns:
            HappinessRecord if bonus was awarded
        """
        actual = bonus_pool.withdraw(amount, councillor.name, reason)
        if actual > 0:
            # Scale happiness impact by actual bonus amount
            multiplier = actual / 10  # 10 units = full impact
            return self.apply_event(
                councillor,
                HappinessEvent.BONUS_RECEIVED,
                multiplier=min(2.0, multiplier),
                metadata={"amount": actual, "reason": reason}
            )
        return None

    def apply_feedback(
        self,
        councillor: Councillor,
        positive: bool,
        source: str = "user"
    ) -> HappinessRecord:
        """
        Apply happiness change for feedback.

        Args:
            councillor: The councillor receiving feedback
            positive: Whether feedback is positive
            source: Source of feedback (user, peer, leader)

        Returns:
            HappinessRecord
        """
        event = HappinessEvent.PRAISE if positive else HappinessEvent.CRITICISM

        # User feedback has more impact
        multiplier = 1.5 if source == "user" else 1.0

        return self.apply_event(
            councillor,
            event,
            multiplier=multiplier,
            metadata={"source": source}
        )

    def apply_team_event(
        self,
        councillors: List[Councillor],
        event: HappinessEvent
    ) -> List[HappinessRecord]:
        """
        Apply a team-wide event to all councillors.

        Args:
            councillors: List of councillors
            event: The event (e.g., TEAM_SUCCESS, COLLEAGUE_FIRED)

        Returns:
            List of HappinessRecords
        """
        records = []
        for councillor in councillors:
            record = self.apply_event(councillor, event)
            records.append(record)
        return records

    # Maximum workload multiplier to prevent excessive happiness penalties
    MAX_WORKLOAD_MULTIPLIER = 3.0

    def check_workload(
        self,
        councillor: Councillor,
        recent_tasks: int,
        threshold: int = 5
    ) -> Optional[HappinessRecord]:
        """
        Check if councillor is overworked.

        Args:
            councillor: The councillor to check
            recent_tasks: Number of recent tasks assigned
            threshold: Threshold for overwork

        Returns:
            HappinessRecord if overworked
        """
        if recent_tasks > threshold:
            # Calculate multiplier with cap to prevent instant councillor burnout
            raw_multiplier = 1 + (recent_tasks - threshold) * 0.2
            capped_multiplier = min(raw_multiplier, self.MAX_WORKLOAD_MULTIPLIER)
            return self.apply_event(
                councillor,
                HappinessEvent.OVERWORKED,
                multiplier=capped_multiplier,
                metadata={
                    "recent_tasks": recent_tasks,
                    "multiplier_capped": raw_multiplier > self.MAX_WORKLOAD_MULTIPLIER
                }
            )
        return None

    def apply_decay(
        self,
        councillors: List[Councillor],
        toward: float = 50.0
    ) -> List[HappinessRecord]:
        """
        Apply natural happiness decay/recovery toward baseline.

        Happiness slowly moves toward the baseline (50).

        Args:
            councillors: List of councillors
            toward: Target happiness level

        Returns:
            List of HappinessRecords
        """
        records = []
        for councillor in councillors:
            if councillor.happiness == toward:
                continue

            old = councillor.happiness
            if councillor.happiness > toward:
                councillor.happiness = max(toward, old - self._decay_rate)
            else:
                councillor.happiness = min(toward, old + self._decay_rate)

            record = HappinessRecord(
                councillor_id=councillor.id,
                event=HappinessEvent.DECAY,
                impact=councillor.happiness - old,
                old_happiness=old,
                new_happiness=councillor.happiness,
                metadata={"type": "decay", "target": toward}
            )
            records.append(record)

        return records

    def get_mood(self, happiness: float) -> str:
        """Get mood description from happiness level"""
        if happiness >= 90:
            return "ecstatic"
        elif happiness >= 75:
            return "happy"
        elif happiness >= 60:
            return "content"
        elif happiness >= 45:
            return "neutral"
        elif happiness >= 30:
            return "unhappy"
        elif happiness >= 15:
            return "miserable"
        else:
            return "critical"

    def get_councillor_status(self, councillor: Councillor) -> Dict[str, Any]:
        """Get happiness status for a councillor"""
        return {
            "id": councillor.id,
            "name": councillor.name,
            "happiness": councillor.happiness,
            "mood": self.get_mood(councillor.happiness),
            "is_warning": councillor.happiness < self._warning_threshold,
            "is_critical": councillor.happiness < self._critical_threshold,
            "happiness_modifier": councillor.happiness_modifier,
        }

    def get_team_morale(self, councillors: List[Councillor]) -> Dict[str, Any]:
        """Get team morale summary"""
        if not councillors:
            return {"average": 0, "mood": "none", "at_risk": 0}

        avg = sum(c.happiness for c in councillors) / len(councillors)
        at_risk = sum(1 for c in councillors if c.happiness < self._warning_threshold)

        return {
            "average": round(avg, 1),
            "mood": self.get_mood(avg),
            "at_risk": at_risk,
            "total_councillors": len(councillors),
            "individual": [self.get_councillor_status(c) for c in councillors]
        }

    def get_history_for_councillor(
        self,
        councillor_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent happiness history for a councillor"""
        records = [
            r.to_dict() for r in self.history
            if r.councillor_id == councillor_id
        ]
        return records[-limit:]
