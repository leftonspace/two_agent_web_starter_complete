"""
Pattern Selector Implementation

Analyzes tasks and recommends the most appropriate orchestration pattern.
"""

from typing import List, Dict, Optional, Any, Type, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from .base import Pattern, Agent, PatternConfig
from .sequential import SequentialPattern, OrderedSequentialPattern, PipelinePattern
from .hierarchical import HierarchicalPattern, HierarchyLevel
from .autoselect import AutoSelectPattern, KeywordSelector
from .roundrobin import RoundRobinPattern, WeightedRoundRobinPattern, ManualPattern


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class TaskType(Enum):
    """Types of tasks that patterns handle"""
    LINEAR = "linear"  # Sequential steps
    HIERARCHICAL = "hierarchical"  # Delegation-based
    COLLABORATIVE = "collaborative"  # Multiple agents discussing
    SPECIALIZED = "specialized"  # Expert selection needed
    INTERACTIVE = "interactive"  # User involvement needed
    PIPELINE = "pipeline"  # Data transformation chain


@dataclass
class TaskAnalysis:
    """Analysis of a task for pattern selection"""
    task_type: TaskType
    complexity: TaskComplexity
    agent_count: int
    requires_order: bool
    requires_hierarchy: bool
    requires_iteration: bool
    requires_user_input: bool
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class PatternRecommendation:
    """A recommended pattern with reasoning"""
    pattern_class: Type[Pattern]
    pattern_name: str
    score: float
    reasoning: str
    config_suggestions: Dict[str, Any] = field(default_factory=dict)

    def create_instance(
        self,
        agents: List[Agent],
        config: Optional[PatternConfig] = None
    ) -> Pattern:
        """Create an instance of the recommended pattern"""
        if config is None and self.config_suggestions:
            config = PatternConfig(**self.config_suggestions)
        return self.pattern_class(agents, config)


class PatternSelector:
    """
    Analyzes tasks and recommends orchestration patterns.

    Usage:
        selector = PatternSelector()
        recommendations = selector.analyze_and_recommend(
            task="Research AI trends and write an article",
            agents=[researcher, writer, editor]
        )
        best_pattern = recommendations[0].create_instance(agents)
    """

    # Pattern keywords for matching
    PATTERN_KEYWORDS = {
        "sequential": [
            "step by step", "in order", "first then", "sequence",
            "one after another", "stages", "phases", "workflow"
        ],
        "hierarchical": [
            "delegate", "manage", "supervise", "report", "approve",
            "review", "escalate", "chain of command", "leadership"
        ],
        "autoselect": [
            "best expert", "most suitable", "whoever", "appropriate",
            "specialized", "expert", "knowledgeable"
        ],
        "roundrobin": [
            "take turns", "everyone", "each agent", "rotate",
            "discuss", "debate", "collaborate", "all together"
        ],
        "manual": [
            "i will decide", "let me choose", "interactive",
            "my choice", "user control", "manual selection"
        ],
        "pipeline": [
            "transform", "process", "convert", "pipeline",
            "data flow", "chain", "feed into"
        ]
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        "simple": [
            "simple", "quick", "easy", "basic", "straightforward",
            "just", "only", "single"
        ],
        "moderate": [
            "some", "a few", "moderate", "standard", "typical"
        ],
        "complex": [
            "complex", "multiple", "several", "detailed", "thorough",
            "comprehensive", "extensive"
        ],
        "very_complex": [
            "very complex", "extremely", "highly", "intricate",
            "sophisticated", "advanced", "enterprise"
        ]
    }

    def __init__(self):
        """Initialize the pattern selector"""
        self._pattern_registry: Dict[str, Type[Pattern]] = {
            "sequential": SequentialPattern,
            "ordered_sequential": OrderedSequentialPattern,
            "pipeline": PipelinePattern,
            "hierarchical": HierarchicalPattern,
            "autoselect": AutoSelectPattern,
            "roundrobin": RoundRobinPattern,
            "weighted_roundrobin": WeightedRoundRobinPattern,
            "manual": ManualPattern,
        }

    def analyze_task(
        self,
        task: str,
        agents: Optional[List[Agent]] = None
    ) -> TaskAnalysis:
        """
        Analyze a task description.

        Args:
            task: Task description
            agents: Optional list of agents (for context)

        Returns:
            TaskAnalysis with task characteristics
        """
        task_lower = task.lower()
        agent_count = len(agents) if agents else 0

        # Determine task type
        task_type = self._detect_task_type(task_lower)

        # Determine complexity
        complexity = self._detect_complexity(task_lower, agent_count)

        # Check requirements
        requires_order = self._check_requires_order(task_lower)
        requires_hierarchy = self._check_requires_hierarchy(task_lower, agents)
        requires_iteration = self._check_requires_iteration(task_lower)
        requires_user_input = self._check_requires_user_input(task_lower)

        # Extract keywords
        keywords = self._extract_keywords(task_lower)

        # Calculate confidence
        confidence = self._calculate_confidence(
            task_type, keywords, agent_count
        )

        reasoning = self._generate_analysis_reasoning(
            task_type, complexity, requires_order,
            requires_hierarchy, agent_count
        )

        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            agent_count=agent_count,
            requires_order=requires_order,
            requires_hierarchy=requires_hierarchy,
            requires_iteration=requires_iteration,
            requires_user_input=requires_user_input,
            keywords=keywords,
            confidence=confidence,
            reasoning=reasoning
        )

    def _detect_task_type(self, task: str) -> TaskType:
        """Detect the type of task"""
        scores = {}

        for task_type, keywords in [
            (TaskType.LINEAR, self.PATTERN_KEYWORDS["sequential"]),
            (TaskType.HIERARCHICAL, self.PATTERN_KEYWORDS["hierarchical"]),
            (TaskType.SPECIALIZED, self.PATTERN_KEYWORDS["autoselect"]),
            (TaskType.COLLABORATIVE, self.PATTERN_KEYWORDS["roundrobin"]),
            (TaskType.INTERACTIVE, self.PATTERN_KEYWORDS["manual"]),
            (TaskType.PIPELINE, self.PATTERN_KEYWORDS["pipeline"]),
        ]:
            count = sum(1 for kw in keywords if kw in task)
            scores[task_type] = count

        if not any(scores.values()):
            return TaskType.LINEAR  # Default

        return max(scores, key=scores.get)

    def _detect_complexity(self, task: str, agent_count: int) -> TaskComplexity:
        """Detect task complexity"""
        # Check keyword indicators
        for complexity, keywords in self.COMPLEXITY_INDICATORS.items():
            if any(kw in task for kw in keywords):
                return TaskComplexity(complexity)

        # Infer from agent count
        if agent_count <= 2:
            return TaskComplexity.SIMPLE
        elif agent_count <= 4:
            return TaskComplexity.MODERATE
        elif agent_count <= 6:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.VERY_COMPLEX

    def _check_requires_order(self, task: str) -> bool:
        """Check if task requires ordered execution"""
        order_indicators = [
            "first", "then", "after", "before", "next",
            "step", "phase", "stage", "sequence"
        ]
        return any(ind in task for ind in order_indicators)

    def _check_requires_hierarchy(
        self,
        task: str,
        agents: Optional[List[Agent]]
    ) -> bool:
        """Check if task requires hierarchical structure"""
        hierarchy_indicators = [
            "manager", "supervisor", "lead", "senior",
            "approve", "delegate", "report"
        ]

        if any(ind in task for ind in hierarchy_indicators):
            return True

        # Check if agents have hierarchy-related roles
        if agents:
            for agent in agents:
                role_lower = agent.role.lower()
                if any(ind in role_lower for ind in hierarchy_indicators):
                    return True

        return False

    def _check_requires_iteration(self, task: str) -> bool:
        """Check if task requires iterative processing"""
        iteration_indicators = [
            "iterate", "refine", "improve", "repeat",
            "revision", "feedback", "cycle", "loop"
        ]
        return any(ind in task for ind in iteration_indicators)

    def _check_requires_user_input(self, task: str) -> bool:
        """Check if task requires user input"""
        user_indicators = [
            "ask user", "user decision", "interactive",
            "confirm", "approval", "user choice"
        ]
        return any(ind in task for ind in user_indicators)

    def _extract_keywords(self, task: str) -> List[str]:
        """Extract relevant keywords from task"""
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on",
            "at", "to", "for", "of", "with", "is", "are", "was",
            "be", "have", "has", "had", "do", "does", "did"
        }

        words = re.findall(r'\b\w+\b', task)
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:20]  # Limit to 20 keywords

    def _calculate_confidence(
        self,
        task_type: TaskType,
        keywords: List[str],
        agent_count: int
    ) -> float:
        """Calculate confidence in the analysis"""
        confidence = 0.5  # Base confidence

        # More keywords = more confident
        if len(keywords) > 5:
            confidence += 0.1
        if len(keywords) > 10:
            confidence += 0.1

        # Agent count affects confidence
        if agent_count > 0:
            confidence += 0.1

        # Cap at 0.95
        return min(0.95, confidence)

    def _generate_analysis_reasoning(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        requires_order: bool,
        requires_hierarchy: bool,
        agent_count: int
    ) -> str:
        """Generate reasoning for the analysis"""
        parts = [
            f"Detected {task_type.value} task type",
            f"with {complexity.value} complexity"
        ]

        if requires_order:
            parts.append("requiring ordered execution")
        if requires_hierarchy:
            parts.append("with hierarchical structure")
        if agent_count > 0:
            parts.append(f"involving {agent_count} agents")

        return ", ".join(parts) + "."

    def recommend(
        self,
        analysis: TaskAnalysis,
        agents: Optional[List[Agent]] = None
    ) -> List[PatternRecommendation]:
        """
        Recommend patterns based on task analysis.

        Args:
            analysis: Task analysis result
            agents: Optional list of agents

        Returns:
            List of pattern recommendations sorted by score
        """
        recommendations = []

        # Score each pattern
        for name, pattern_class in self._pattern_registry.items():
            score, reasoning, config = self._score_pattern(
                name, pattern_class, analysis, agents
            )
            if score > 0:
                recommendations.append(PatternRecommendation(
                    pattern_class=pattern_class,
                    pattern_name=name,
                    score=score,
                    reasoning=reasoning,
                    config_suggestions=config
                ))

        # Sort by score descending
        recommendations.sort(key=lambda r: r.score, reverse=True)

        return recommendations

    def _score_pattern(
        self,
        name: str,
        pattern_class: Type[Pattern],
        analysis: TaskAnalysis,
        agents: Optional[List[Agent]]
    ) -> Tuple[float, str, Dict[str, Any]]:
        """Score a pattern for the given analysis"""
        score = 0.0
        reasons = []
        config = {}

        # Match by task type
        type_matches = {
            TaskType.LINEAR: ["sequential", "ordered_sequential", "pipeline"],
            TaskType.HIERARCHICAL: ["hierarchical"],
            TaskType.SPECIALIZED: ["autoselect"],
            TaskType.COLLABORATIVE: ["roundrobin", "weighted_roundrobin"],
            TaskType.INTERACTIVE: ["manual"],
            TaskType.PIPELINE: ["pipeline"],
        }

        if name in type_matches.get(analysis.task_type, []):
            score += 0.4
            reasons.append(f"matches {analysis.task_type.value} task type")

        # Check requirements
        if analysis.requires_order and name in ["sequential", "ordered_sequential", "pipeline"]:
            score += 0.2
            reasons.append("supports ordered execution")

        if analysis.requires_hierarchy and name == "hierarchical":
            score += 0.3
            reasons.append("supports hierarchical delegation")

        if analysis.requires_user_input and name == "manual":
            score += 0.3
            reasons.append("allows user control")

        if analysis.requires_iteration and name in ["roundrobin", "autoselect"]:
            score += 0.2
            reasons.append("supports iterative processing")
            config["max_rounds"] = 15

        # Adjust for complexity
        if analysis.complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
            if name in ["hierarchical", "autoselect"]:
                score += 0.1
                reasons.append("handles complex tasks well")
        elif analysis.complexity == TaskComplexity.SIMPLE:
            if name in ["sequential", "roundrobin"]:
                score += 0.1
                reasons.append("efficient for simple tasks")

        # Agent count considerations
        if analysis.agent_count > 5 and name == "hierarchical":
            score += 0.1
            reasons.append("scales well with many agents")
        elif analysis.agent_count <= 3 and name == "sequential":
            score += 0.1
            reasons.append("ideal for small teams")

        # Keyword matching
        pattern_keywords = self.PATTERN_KEYWORDS.get(name.split("_")[0], [])
        keyword_matches = sum(
            1 for kw in pattern_keywords
            if any(k in kw or kw in k for k in analysis.keywords)
        )
        if keyword_matches > 0:
            score += 0.1 * min(keyword_matches, 3)
            reasons.append(f"keyword matches ({keyword_matches})")

        reasoning = "; ".join(reasons) if reasons else "general suitability"

        return score, reasoning, config

    def analyze_and_recommend(
        self,
        task: str,
        agents: Optional[List[Agent]] = None
    ) -> List[PatternRecommendation]:
        """
        Analyze task and provide pattern recommendations.

        Convenience method that combines analyze_task and recommend.

        Args:
            task: Task description
            agents: Optional list of agents

        Returns:
            List of pattern recommendations sorted by score
        """
        analysis = self.analyze_task(task, agents)
        return self.recommend(analysis, agents)

    def get_best_pattern(
        self,
        task: str,
        agents: List[Agent],
        config: Optional[PatternConfig] = None
    ) -> Pattern:
        """
        Get the best pattern for a task, instantiated and ready to use.

        Args:
            task: Task description
            agents: List of agents
            config: Optional pattern configuration

        Returns:
            Instantiated Pattern object
        """
        recommendations = self.analyze_and_recommend(task, agents)

        if not recommendations:
            # Default to sequential
            return SequentialPattern(agents, config)

        return recommendations[0].create_instance(agents, config)

    def register_pattern(
        self,
        name: str,
        pattern_class: Type[Pattern],
        keywords: Optional[List[str]] = None
    ):
        """
        Register a custom pattern.

        Args:
            name: Pattern name
            pattern_class: Pattern class
            keywords: Optional keywords for matching
        """
        self._pattern_registry[name] = pattern_class
        if keywords:
            self.PATTERN_KEYWORDS[name] = keywords


# Convenience function
def select_pattern(
    task: str,
    agents: List[Agent],
    config: Optional[PatternConfig] = None
) -> Pattern:
    """
    Select and instantiate the best pattern for a task.

    Args:
        task: Task description
        agents: List of agents
        config: Optional pattern configuration

    Returns:
        Instantiated Pattern object
    """
    selector = PatternSelector()
    return selector.get_best_pattern(task, agents, config)
