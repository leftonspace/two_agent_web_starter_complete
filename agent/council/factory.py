"""
Council System - Councillor Factory

Manages councillor lifecycle: spawning, firing, promoting.
Maintains minimum councillor count and handles replacements.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import random

from .models import (
    Councillor, CouncillorStatus, Specialization,
    PerformanceMetrics
)


# Councillor name pools
FIRST_NAMES = [
    "Ada", "Bob", "Carol", "Dan", "Eve", "Frank", "Grace", "Hank",
    "Ivy", "Jack", "Kim", "Leo", "Maya", "Nate", "Olivia", "Pat",
    "Quinn", "Ray", "Sam", "Tara", "Uma", "Vic", "Wendy", "Xena",
    "Yuki", "Zack", "Alex", "Blake", "Casey", "Drew", "Ellis", "Finn"
]

LAST_NAMES = [
    "Smith", "Chen", "Garcia", "Kim", "Singh", "Brown", "Wilson",
    "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson",
    "White", "Harris", "Martin", "Thompson", "Robinson", "Clark", "Lewis"
]

# Specialization templates
SPECIALIZATION_TEMPLATES = {
    "coder": {
        "specializations": [Specialization.CODING],
        "capabilities": ["python", "javascript", "sql", "debugging"],
        "base_happiness": 65,
    },
    "designer": {
        "specializations": [Specialization.DESIGN],
        "capabilities": ["ui", "ux", "css", "responsive"],
        "base_happiness": 70,
    },
    "tester": {
        "specializations": [Specialization.TESTING],
        "capabilities": ["unit_tests", "integration", "qa", "automation"],
        "base_happiness": 60,
    },
    "reviewer": {
        "specializations": [Specialization.REVIEW],
        "capabilities": ["code_review", "pr_review", "standards"],
        "base_happiness": 65,
    },
    "architect": {
        "specializations": [Specialization.ARCHITECTURE, Specialization.CODING],
        "capabilities": ["system_design", "patterns", "scalability"],
        "base_happiness": 70,
    },
    "devops": {
        "specializations": [Specialization.DEVOPS],
        "capabilities": ["ci_cd", "docker", "kubernetes", "aws"],
        "base_happiness": 60,
    },
    "security": {
        "specializations": [Specialization.SECURITY],
        "capabilities": ["security_audit", "penetration", "compliance"],
        "base_happiness": 55,
    },
    "data": {
        "specializations": [Specialization.DATA],
        "capabilities": ["analytics", "ml", "etl", "visualization"],
        "base_happiness": 65,
    },
    "researcher": {
        "specializations": [Specialization.RESEARCH],
        "capabilities": ["analysis", "documentation", "learning"],
        "base_happiness": 70,
    },
    "generalist": {
        "specializations": [Specialization.CODING, Specialization.REVIEW],
        "capabilities": ["versatile", "adaptable"],
        "base_happiness": 65,
    },
}


@dataclass
class FiringDecision:
    """Record of a firing decision"""
    councillor_id: str
    councillor_name: str
    reason: str
    metrics_snapshot: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    vetoed: bool = False
    veto_reason: Optional[str] = None


@dataclass
class SpawnDecision:
    """Record of a spawn decision"""
    councillor_id: str
    councillor_name: str
    template: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FactoryConfig:
    """Configuration for councillor factory"""
    min_councillors: int = 3
    max_councillors: int = 10
    default_templates: List[str] = field(default_factory=lambda: ["coder", "reviewer", "tester"])
    probation_tasks: int = 10
    promotion_performance: float = 60.0
    fire_performance_threshold: float = 40.0
    fire_consecutive_failures: int = 5
    fire_happiness_threshold: float = 20.0
    auto_replace: bool = True


class CouncillorFactory:
    """
    Factory for creating, firing, and promoting councillors.

    Responsibilities:
    - Spawn new councillors with templates
    - Evaluate and fire underperformers
    - Promote probationary councillors
    - Maintain minimum councillor count
    """

    def __init__(self, config: Optional[FactoryConfig] = None):
        self.config = config or FactoryConfig()
        self._used_names: set = set()
        self._firing_history: List[FiringDecision] = []
        self._spawn_history: List[SpawnDecision] = []
        self._execute_func: Optional[Callable] = None

    def set_execute_func(self, func: Callable):
        """Set the execution function for new councillors"""
        self._execute_func = func

    def _generate_name(self) -> str:
        """Generate a unique councillor name"""
        for _ in range(100):  # Max attempts
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            if name not in self._used_names:
                self._used_names.add(name)
                return name
        # Fallback with number
        return f"Councillor_{len(self._used_names) + 1}"

    def spawn(
        self,
        template: str = "generalist",
        name: Optional[str] = None,
        reason: str = "pool_maintenance"
    ) -> Councillor:
        """
        Spawn a new councillor.

        Args:
            template: Template name from SPECIALIZATION_TEMPLATES
            name: Optional custom name
            reason: Reason for spawning

        Returns:
            New Councillor on probation
        """
        template_data = SPECIALIZATION_TEMPLATES.get(template, SPECIALIZATION_TEMPLATES["generalist"])

        councillor_name = name or self._generate_name()

        councillor = Councillor(
            name=councillor_name,
            specializations=template_data["specializations"].copy(),
            status=CouncillorStatus.PROBATION,
            happiness=template_data.get("base_happiness", 65),
            base_vote_weight=0.8,  # Reduced weight during probation
            metadata={
                "template": template,
                "capabilities": template_data.get("capabilities", []),
                "spawn_reason": reason,
            }
        )

        if self._execute_func:
            councillor._execute_func = self._execute_func

        # Record spawn
        self._spawn_history.append(SpawnDecision(
            councillor_id=councillor.id,
            councillor_name=councillor.name,
            template=template,
            reason=reason
        ))

        return councillor

    def spawn_team(
        self,
        templates: Optional[List[str]] = None,
        count: Optional[int] = None
    ) -> List[Councillor]:
        """
        Spawn a team of councillors.

        Args:
            templates: List of templates to use
            count: Number to spawn (uses templates length if not specified)

        Returns:
            List of new Councillors
        """
        templates = templates or self.config.default_templates
        count = count or len(templates)

        councillors = []
        for i in range(count):
            template = templates[i % len(templates)]
            councillor = self.spawn(template, reason="initial_team")
            councillors.append(councillor)

        return councillors

    def should_fire(self, councillor: Councillor) -> Tuple[bool, str]:
        """
        Determine if a councillor should be fired.

        Criteria:
        - Performance below threshold (40%)
        - 5+ consecutive failures
        - Happiness below threshold (20%)

        Args:
            councillor: The councillor to evaluate

        Returns:
            Tuple of (should_fire, reason)
        """
        # Check performance
        if councillor.metrics.overall_performance < self.config.fire_performance_threshold:
            return True, f"Performance below {self.config.fire_performance_threshold}%"

        # Check consecutive failures
        if councillor.metrics.consecutive_failures >= self.config.fire_consecutive_failures:
            return True, f"{councillor.metrics.consecutive_failures} consecutive failures"

        # Check happiness
        if councillor.happiness < self.config.fire_happiness_threshold:
            return True, f"Happiness below {self.config.fire_happiness_threshold}"

        return False, ""

    def fire(
        self,
        councillor: Councillor,
        reason: str = "performance"
    ) -> FiringDecision:
        """
        Fire a councillor.

        Args:
            councillor: The councillor to fire
            reason: Reason for firing

        Returns:
            FiringDecision record
        """
        decision = FiringDecision(
            councillor_id=councillor.id,
            councillor_name=councillor.name,
            reason=reason,
            metrics_snapshot={
                "performance": councillor.metrics.overall_performance,
                "happiness": councillor.happiness,
                "consecutive_failures": councillor.metrics.consecutive_failures,
                "tasks_completed": councillor.metrics.tasks_completed,
                "success_rate": councillor.metrics.success_rate,
            }
        )

        councillor.status = CouncillorStatus.FIRED
        self._used_names.discard(councillor.name)
        self._firing_history.append(decision)

        return decision

    def can_promote(self, councillor: Councillor) -> Tuple[bool, str]:
        """
        Check if councillor can be promoted from probation.

        Criteria:
        - On probation
        - 10+ tasks completed
        - Performance >= 60%

        Args:
            councillor: The councillor to check

        Returns:
            Tuple of (can_promote, reason)
        """
        if councillor.status != CouncillorStatus.PROBATION:
            return False, "Not on probation"

        if councillor.metrics.tasks_completed < self.config.probation_tasks:
            return False, f"Only {councillor.metrics.tasks_completed}/{self.config.probation_tasks} tasks"

        if councillor.metrics.overall_performance < self.config.promotion_performance:
            return False, f"Performance {councillor.metrics.overall_performance:.1f}% < {self.config.promotion_performance}%"

        return True, "Meets all criteria"

    def promote(self, councillor: Councillor) -> bool:
        """
        Promote a councillor from probation to active.

        Args:
            councillor: The councillor to promote

        Returns:
            True if promoted
        """
        can, _ = self.can_promote(councillor)
        if not can:
            return False

        councillor.status = CouncillorStatus.ACTIVE
        councillor.base_vote_weight = 1.0  # Full vote weight
        councillor.adjust_happiness(15)  # Promotion happiness boost

        return True

    def evaluate_team(
        self,
        councillors: List[Councillor]
    ) -> Dict[str, Any]:
        """
        Evaluate the team and recommend actions.

        Args:
            councillors: List of councillors

        Returns:
            Evaluation report with recommendations
        """
        active = [c for c in councillors if c.status in [CouncillorStatus.ACTIVE, CouncillorStatus.PROBATION]]

        to_fire = []
        to_promote = []

        for c in active:
            should, reason = self.should_fire(c)
            if should:
                to_fire.append({"councillor": c, "reason": reason})

            can, reason = self.can_promote(c)
            if can:
                to_promote.append({"councillor": c, "reason": reason})

        # Calculate spawn needs
        spawn_needed = max(0, self.config.min_councillors - (len(active) - len(to_fire)))

        return {
            "total_councillors": len(councillors),
            "active_councillors": len(active),
            "to_fire": to_fire,
            "to_promote": to_promote,
            "spawn_needed": spawn_needed,
            "team_performance": sum(c.metrics.overall_performance for c in active) / len(active) if active else 0,
            "team_happiness": sum(c.happiness for c in active) / len(active) if active else 0,
        }

    def maintain_team(
        self,
        councillors: List[Councillor]
    ) -> Dict[str, Any]:
        """
        Maintain team size and quality.

        Fires underperformers, promotes ready councillors, spawns replacements.

        Args:
            councillors: Current list of councillors

        Returns:
            Report of actions taken
        """
        evaluation = self.evaluate_team(councillors)
        actions = {
            "fired": [],
            "promoted": [],
            "spawned": [],
        }

        # Fire underperformers
        for item in evaluation["to_fire"]:
            c = item["councillor"]
            decision = self.fire(c, item["reason"])
            actions["fired"].append(decision)
            councillors.remove(c)

        # Promote ready councillors
        for item in evaluation["to_promote"]:
            c = item["councillor"]
            if self.promote(c):
                actions["promoted"].append(c.name)

        # Spawn replacements if auto_replace is enabled
        if self.config.auto_replace and evaluation["spawn_needed"] > 0:
            for i in range(evaluation["spawn_needed"]):
                template = self.config.default_templates[i % len(self.config.default_templates)]
                new_councillor = self.spawn(template, reason="replacement")
                councillors.append(new_councillor)
                actions["spawned"].append(new_councillor.name)

        return actions

    def get_firing_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent firing history"""
        return [
            {
                "councillor_name": d.councillor_name,
                "reason": d.reason,
                "metrics": d.metrics_snapshot,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in self._firing_history[-limit:]
        ]

    def get_spawn_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent spawn history"""
        return [
            {
                "councillor_name": d.councillor_name,
                "template": d.template,
                "reason": d.reason,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in self._spawn_history[-limit:]
        ]

    def get_template_info(self, template: str) -> Optional[Dict[str, Any]]:
        """Get information about a template"""
        data = SPECIALIZATION_TEMPLATES.get(template)
        if data:
            return {
                "name": template,
                "specializations": [s.value for s in data["specializations"]],
                "capabilities": data.get("capabilities", []),
                "base_happiness": data.get("base_happiness", 65),
            }
        return None

    def list_templates(self) -> List[str]:
        """List available templates"""
        return list(SPECIALIZATION_TEMPLATES.keys())
