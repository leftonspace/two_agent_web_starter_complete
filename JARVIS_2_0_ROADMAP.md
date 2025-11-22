# Jarvis 2.0: Complete Roadmap & Competitive Analysis

**Version:** 2.0 Planning Document
**Date:** November 22, 2025
**Status:** Strategic Planning Phase

---

## Executive Summary

This document provides a comprehensive analysis of Jarvis against industry-leading open-source frameworks (CrewAI and AG2/AutoGen), identifies critical gaps, proposes solutions with implementation prompts, and ranks LLMs for optimal Jarvis performance.

**Key Finding:** Jarvis lacks **7 critical features** present in competitors that are essential for market competitiveness. This roadmap addresses each gap with specific implementation plans.

---

# Part 1: Competitive Gap Analysis

## 1.1 Feature Comparison Matrix

| Feature | CrewAI | AG2 (AutoGen) | **Jarvis Current** | Gap Level |
|---------|--------|---------------|-------------------|-----------|
| YAML Agent Config | Yes | No | **No** | Critical |
| Declarative Tasks | Yes | No | **No** | Critical |
| Memory System | 4 types | Hook-based | **Partial** | High |
| Flow/Router System | Yes (advanced) | Patterns | **No** | Critical |
| Tool Registration | Decorator-based | Function-based | **Manual** | High |
| Group Chat | Via Flows | Native | **No** | Critical |
| Observability Events | Yes | Yes | **Partial** | Medium |
| State Management | Pydantic | Dict-based | **Dict** | Low |
| Human-in-Loop | Manual | UserProxyAgent | **No** | High |
| Cost Tracking | No | No | **Yes** | Advantage |
| Git Integration | No | No | **Yes** | Advantage |
| Safety Scanning | No | No | **Yes** | Advantage |

---

## 1.2 CrewAI Features Jarvis Lacks (With Code)

### Gap 1: YAML-Based Agent Configuration

**CrewAI Pattern:**
```yaml
# config/agents.yaml
researcher:
  role: >
    Senior Data Researcher
  goal: >
    Uncover cutting-edge developments in {topic}
  backstory: >
    You're a seasoned researcher with a knack for uncovering
    the latest developments in {topic}.
  tools:
    - search_tool
    - web_scraper
  llm: gpt-4o
  max_iter: 15
  verbose: true
```

**Jarvis Current:** Agents hardcoded in Python

**Impact:** CrewAI users can modify agent behavior without code changes

---

### Gap 2: Declarative Task Definition

**CrewAI Pattern:**
```yaml
# config/tasks.yaml
research_task:
  description: >
    Conduct a thorough research about {topic}.
    Make sure you find any interesting and relevant information.
  expected_output: >
    A list with 10 bullet points of the most relevant information about {topic}
  agent: researcher
  output_file: research_output.md
```

**Jarvis Current:** Tasks generated dynamically by Manager LLM

**Impact:** Less predictable outputs, harder to reproduce

---

### Gap 3: Flow Router System

**CrewAI Pattern:**
```python
from crewai.flow.flow import Flow, listen, router, start, or_
from pydantic import BaseModel

class ContentState(BaseModel):
    topic: str = ""
    complexity: str = "medium"
    draft: str = ""
    final: str = ""

class ContentFlow(Flow[ContentState]):
    @start()
    def analyze_topic(self):
        # Analyze and set complexity
        self.state.complexity = self._determine_complexity()
        return self.state.topic

    @router(analyze_topic)
    def route_by_complexity(self):
        if self.state.complexity == "high":
            return "deep_research"
        elif self.state.complexity == "medium":
            return "standard_research"
        else:
            return "quick_summary"

    @listen("deep_research")
    def do_deep_research(self):
        # Complex multi-step research
        pass

    @listen("standard_research")
    def do_standard_research(self):
        # Standard research flow
        pass

    @listen(or_("deep_research", "standard_research", "quick_summary"))
    def generate_output(self):
        # All paths converge here
        pass
```

**Jarvis Current:** Fixed sequential/hierarchical process only

**Impact:** Cannot handle conditional branching or dynamic workflows

---

### Gap 4: Multi-Type Memory System

**CrewAI Pattern:**
```python
from crewai import Crew
from crewai.memory.short_term.short_term_memory import ShortTermMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from crewai.memory.entity.entity_memory import EntityMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable all memory types

    # Or customize each type:
    short_term_memory=ShortTermMemory(
        storage=ChromaDBStorage(collection_name="stm")
    ),
    long_term_memory=LongTermMemory(
        storage=SQLiteStorage(db_path="ltm.db")
    ),
    entity_memory=EntityMemory(
        storage=QdrantStorage(collection_name="entities")
    ),

    # Memory configuration
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
)
```

**Jarvis Current:** Single session-based memory with limited persistence

**Impact:** No entity tracking, limited context across sessions

---

## 1.3 AG2 (AutoGen) Features Jarvis Lacks (With Code)

### Gap 5: Orchestration Patterns

**AG2 Pattern:**
```python
from autogen import ConversableAgent, LLMConfig
from autogen.agentchat import initiate_group_chat
from autogen.agentchat.group.patterns import (
    AutoPattern,
    DefaultPattern,
    RoundRobinPattern,
    RandomPattern,
    ManualPattern
)

llm_config = LLMConfig(api_type="openai", model="gpt-4o")

# Define specialized agents
planner = ConversableAgent(
    name="planner",
    system_message="You plan projects into actionable steps.",
    llm_config=llm_config
)

coder = ConversableAgent(
    name="coder",
    system_message="You write clean, efficient code.",
    llm_config=llm_config
)

reviewer = ConversableAgent(
    name="reviewer",
    system_message="You review code for bugs and improvements.",
    llm_config=llm_config
)

# AutoPattern - LLM selects next speaker
pattern = AutoPattern(
    initial_agent=planner,
    agents=[planner, coder, reviewer],
    group_manager_args={"llm_config": llm_config}
)

# Or RoundRobinPattern - Fixed rotation
pattern = RoundRobinPattern(
    initial_agent=planner,
    agents=[planner, coder, reviewer]
)

# Execute group chat
result, context, last_agent = initiate_group_chat(
    pattern=pattern,
    messages="Build a REST API for user management",
    max_rounds=15
)
```

**Jarvis Current:** Fixed Manager → Supervisor → Employee hierarchy

**Impact:** Cannot adapt orchestration strategy to task requirements

---

### Gap 6: Human-in-the-Loop Agent

**AG2 Pattern:**
```python
from autogen import UserProxyAgent, AssistantAgent

# Human proxy that can execute code and get user input
user_proxy = UserProxyAgent(
    name="user",
    human_input_mode="TERMINATE",  # ALWAYS, TERMINATE, or NEVER
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "APPROVED" in x.get("content", ""),
    code_execution_config={
        "work_dir": "workspace",
        "use_docker": False
    }
)

assistant = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="You help users with coding tasks."
)

# Chat with human approval points
user_proxy.initiate_chat(
    assistant,
    message="Create a Python script that processes CSV files"
)
```

**Jarvis Current:** No structured human approval workflow

**Impact:** Cannot pause for user confirmation on critical steps

---

### Gap 7: Hookable Message Pipeline

**AG2 Pattern:**
```python
class CustomAgent(ConversableAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Register hooks at various pipeline stages
        self.register_hook(
            hookable_method="process_message_before_send",
            hook=self.log_outgoing_message
        )
        self.register_hook(
            hookable_method="process_received_message",
            hook=self.validate_incoming_message
        )
        self.register_hook(
            hookable_method="process_all_messages_before_reply",
            hook=self.add_context_to_messages
        )

    def log_outgoing_message(self, message):
        print(f"[SEND] {message[:100]}...")
        return message

    def validate_incoming_message(self, message, sender):
        if "forbidden" in message.lower():
            raise ValueError("Message contains forbidden content")
        return message

    def add_context_to_messages(self, messages):
        # Inject system context before LLM call
        context = {"role": "system", "content": "Current time: ..."}
        return [context] + messages
```

**Jarvis Current:** No message interception/modification hooks

**Impact:** Cannot inject middleware for logging, validation, or context

---

# Part 1B: The Council System - Meta-Orchestration Architecture

## 1B.1 Council System Overview

The Council system is a **gamified meta-orchestration layer** that transforms Jarvis from a simple orchestrator into an intelligent, adaptive system with incentive alignment.

**Core Concept:**
- **Jarvis** becomes the **Council Leader** - a meta-orchestrator managing a pool of specialists
- **Supervisors + Employees** become **Councillors** - specialists who vote on decisions
- Performance metrics affect **vote weight** - high performers have more influence
- **Happiness levels** affect quality - unhappy agents perform worse
- **Fire/Spawn mechanics** - continuously improve the agent pool

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE COUNCIL ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        ┌─────────────────────┐                               │
│                        │   COUNCIL LEADER    │                               │
│                        │      (Jarvis)       │                               │
│                        │  ┌───────────────┐  │                               │
│                        │  │ Happiness: 85 │  │                               │
│                        │  │ Bonus Pool: $ │  │                               │
│                        │  │ Team Score: A │  │                               │
│                        │  └───────────────┘  │                               │
│                        └──────────┬──────────┘                               │
│                                   │                                          │
│                    ┌──────────────┼──────────────┐                          │
│                    │              │              │                          │
│           ┌────────▼────────┐ ┌──▼───────────┐ ┌▼─────────────┐           │
│           │  COUNCILLOR #1  │ │ COUNCILLOR #2│ │ COUNCILLOR #3│           │
│           │    (Coder)      │ │  (Designer)  │ │  (Reviewer)  │           │
│           │ ┌─────────────┐ │ │┌────────────┐│ │┌────────────┐│           │
│           │ │Perf: 92%    │ │ ││Perf: 78%   ││ ││Perf: 88%   ││           │
│           │ │Vote: 1.84x  │ │ ││Vote: 1.0x  ││ ││Vote: 1.56x ││           │
│           │ │Happy: 90    │ │ ││Happy: 65   ││ ││Happy: 85   ││           │
│           │ │Spec: Python │ │ ││Spec: CSS   ││ ││Spec: QA    ││           │
│           │ └─────────────┘ │ │└────────────┘│ │└────────────┘│           │
│           └─────────────────┘ └──────────────┘ └──────────────┘           │
│                    │              │              │                          │
│                    │         VOTE ON TASK        │                          │
│                    │              │              │                          │
│                    ▼              ▼              ▼                          │
│              ┌─────────────────────────────────────┐                        │
│              │          WEIGHTED DECISION          │                        │
│              │  Winner = Sum(Vote × Weight × Conf) │                        │
│              └─────────────────────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1B.2 Core Data Models

### Councillor Model

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class Specialization(str, Enum):
    CODING = "coding"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    PLANNING = "planning"
    REVIEW = "review"

class CouncillorStatus(str, Enum):
    ACTIVE = "active"
    PROBATION = "probation"  # New or underperforming
    SUSPENDED = "suspended"  # Temporarily inactive
    TERMINATED = "terminated"  # Fired

class PerformanceMetrics(BaseModel):
    """Track councillor performance over time"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    quality_scores: List[float] = Field(default_factory=list)  # 0-100
    speed_scores: List[float] = Field(default_factory=list)    # Relative to expected
    feedback_scores: List[float] = Field(default_factory=list) # User ratings

    # Rolling averages (last 20 tasks)
    avg_quality: float = 75.0
    avg_speed: float = 1.0
    avg_feedback: float = 75.0

    # Derived metrics
    success_rate: float = 0.0
    consistency_score: float = 0.0  # Low variance = high consistency

    def update(self, quality: float, speed: float, feedback: float, success: bool):
        """Update metrics after task completion"""
        self.quality_scores.append(quality)
        self.speed_scores.append(speed)
        self.feedback_scores.append(feedback)

        if success:
            self.tasks_completed += 1
        else:
            self.tasks_failed += 1

        # Keep last 20 for rolling average
        self.quality_scores = self.quality_scores[-20:]
        self.speed_scores = self.speed_scores[-20:]
        self.feedback_scores = self.feedback_scores[-20:]

        # Recalculate averages
        self.avg_quality = sum(self.quality_scores) / len(self.quality_scores)
        self.avg_speed = sum(self.speed_scores) / len(self.speed_scores)
        self.avg_feedback = sum(self.feedback_scores) / len(self.feedback_scores)

        total_tasks = self.tasks_completed + self.tasks_failed
        self.success_rate = self.tasks_completed / total_tasks if total_tasks > 0 else 0.0

        # Consistency = inverse of standard deviation
        if len(self.quality_scores) > 1:
            import statistics
            variance = statistics.variance(self.quality_scores)
            self.consistency_score = max(0, 100 - variance)  # Higher = more consistent

    @property
    def overall_performance(self) -> float:
        """Calculate overall performance score (0-100)"""
        return (
            self.avg_quality * 0.4 +
            self.avg_feedback * 0.3 +
            self.success_rate * 100 * 0.2 +
            self.consistency_score * 0.1
        )

class Councillor(BaseModel):
    """A specialist agent in the Council"""
    id: str
    name: str
    specialization: Specialization
    model: str = "gpt-4o"  # LLM model to use

    # Core attributes
    status: CouncillorStatus = CouncillorStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)

    # Performance
    metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)

    # Happiness (0-100)
    happiness: float = 75.0
    happiness_factors: Dict[str, float] = Field(default_factory=dict)

    # Vote weight (calculated from performance)
    base_vote_weight: float = 1.0

    # Task history
    recent_tasks: List[str] = Field(default_factory=list)

    # Personality/Style (affects prompt)
    personality_traits: List[str] = Field(default_factory=list)
    communication_style: str = "professional"

    @property
    def vote_weight(self) -> float:
        """Calculate vote weight based on performance"""
        performance = self.metrics.overall_performance

        # Performance coefficient: 0.5x to 2.0x multiplier
        # 50% performance = 0.5x weight
        # 80% performance = 1.0x weight (baseline)
        # 100% performance = 2.0x weight
        if performance < 80:
            coefficient = 0.5 + (performance / 80) * 0.5
        else:
            coefficient = 1.0 + ((performance - 80) / 20) * 1.0

        # Happiness modifier: unhappy councillors are less effective
        happiness_modifier = 0.7 + (self.happiness / 100) * 0.3

        return self.base_vote_weight * coefficient * happiness_modifier

    @property
    def should_be_fired(self) -> bool:
        """Check if councillor should be terminated"""
        # Fire if:
        # 1. Performance below 40% for sustained period
        # 2. More than 5 consecutive failures
        # 3. Happiness below 20% (will quit/sabotage)

        if self.metrics.overall_performance < 40 and self.metrics.tasks_completed > 10:
            return True
        if self.metrics.tasks_failed >= 5 and self.tasks_completed == 0:
            return True
        if self.happiness < 20:
            return True
        return False

    def update_happiness(self, delta: float, reason: str):
        """Update happiness with tracking"""
        self.happiness_factors[reason] = delta
        self.happiness = max(0, min(100, self.happiness + delta))
```

### Council Leader Model

```python
class BonusPool(BaseModel):
    """Track bonus allocation"""
    total_available: float = 1000.0  # Abstract points
    allocated: Dict[str, float] = Field(default_factory=dict)
    pending_bonuses: List[Dict] = Field(default_factory=list)

    def allocate_bonus(self, councillor_id: str, amount: float, reason: str):
        """Allocate bonus to councillor"""
        if amount <= self.total_available:
            self.pending_bonuses.append({
                "councillor_id": councillor_id,
                "amount": amount,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            self.total_available -= amount
            self.allocated[councillor_id] = self.allocated.get(councillor_id, 0) + amount

class CouncilLeader(BaseModel):
    """Jarvis as the Council Leader"""
    name: str = "Jarvis"

    # Council state
    councillors: Dict[str, Councillor] = Field(default_factory=dict)
    max_councillors: int = 10
    min_councillors: int = 3

    # Leader metrics
    happiness: float = 80.0  # Leader's happiness affects bonus pool
    team_performance: float = 0.0
    tasks_orchestrated: int = 0

    # Bonus system
    bonus_pool: BonusPool = Field(default_factory=BonusPool)

    # Boss satisfaction (external - from user)
    boss_satisfaction: float = 75.0  # Affects bonus pool replenishment

    # Decision history
    decision_log: List[Dict] = Field(default_factory=list)

    @property
    def active_councillors(self) -> List[Councillor]:
        """Get all active councillors"""
        return [c for c in self.councillors.values()
                if c.status == CouncillorStatus.ACTIVE]

    def calculate_team_performance(self) -> float:
        """Calculate overall team performance"""
        active = self.active_councillors
        if not active:
            return 0.0
        return sum(c.metrics.overall_performance for c in active) / len(active)

    def replenish_bonus_pool(self):
        """Replenish bonus pool based on boss satisfaction"""
        # Higher boss satisfaction = more bonus budget
        replenish_rate = 100 * (self.boss_satisfaction / 100)
        self.bonus_pool.total_available += replenish_rate

    def update_leader_happiness(self):
        """Update leader happiness based on team metrics"""
        team_perf = self.calculate_team_performance()
        avg_councillor_happiness = sum(c.happiness for c in self.active_councillors) / len(self.active_councillors)

        # Leader is happy when:
        # - Team performs well (40%)
        # - Councillors are happy (30%)
        # - Boss is satisfied (30%)
        self.happiness = (
            team_perf * 0.4 +
            avg_councillor_happiness * 0.3 +
            self.boss_satisfaction * 0.3
        )
```

---

## 1B.3 Weighted Voting System

```python
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
import asyncio

@dataclass
class Vote:
    """A councillor's vote on a decision"""
    councillor_id: str
    option: str
    confidence: float  # 0-1, how confident in this choice
    reasoning: str
    weight: float  # Calculated vote weight

    @property
    def weighted_score(self) -> float:
        return self.confidence * self.weight

class VotingSession:
    """Manage a voting session for a decision"""

    def __init__(
        self,
        council_leader: CouncilLeader,
        question: str,
        options: List[str],
        required_specializations: Optional[List[Specialization]] = None,
        timeout_seconds: int = 30
    ):
        self.council_leader = council_leader
        self.question = question
        self.options = options
        self.required_specs = required_specializations
        self.timeout = timeout_seconds
        self.votes: List[Vote] = []

    def get_eligible_voters(self) -> List[Councillor]:
        """Get councillors eligible to vote"""
        active = self.council_leader.active_councillors

        if self.required_specs:
            # Filter by specialization
            return [c for c in active if c.specialization in self.required_specs]
        return active

    async def collect_vote(self, councillor: Councillor, llm_client) -> Vote:
        """Get a single councillor's vote via LLM"""
        prompt = f"""You are {councillor.name}, a specialist in {councillor.specialization.value}.

Your personality: {', '.join(councillor.personality_traits) or 'Professional and thorough'}

QUESTION: {self.question}

OPTIONS:
{chr(10).join(f'- {opt}' for opt in self.options)}

Based on your expertise, vote for ONE option and explain why.

Respond in JSON:
{{
    "vote": "<option>",
    "confidence": <0.0-1.0>,
    "reasoning": "<brief explanation>"
}}"""

        response = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=councillor.model
        )

        # Parse response
        import json
        data = json.loads(response)

        return Vote(
            councillor_id=councillor.id,
            option=data["vote"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            weight=councillor.vote_weight
        )

    async def conduct_vote(self, llm_client) -> Dict:
        """Conduct the full voting session"""
        voters = self.get_eligible_voters()

        if not voters:
            return {"error": "No eligible voters"}

        # Collect votes in parallel
        vote_tasks = [self.collect_vote(c, llm_client) for c in voters]
        self.votes = await asyncio.gather(*vote_tasks)

        # Tally results
        results = self.tally_votes()

        # Log decision
        self.council_leader.decision_log.append({
            "question": self.question,
            "options": self.options,
            "votes": [v.__dict__ for v in self.votes],
            "result": results,
            "timestamp": datetime.now().isoformat()
        })

        return results

    def tally_votes(self) -> Dict:
        """Calculate weighted vote results"""
        scores = {opt: 0.0 for opt in self.options}
        vote_counts = {opt: 0 for opt in self.options}
        reasonings = {opt: [] for opt in self.options}

        for vote in self.votes:
            if vote.option in scores:
                scores[vote.option] += vote.weighted_score
                vote_counts[vote.option] += 1
                reasonings[vote.option].append({
                    "councillor": vote.councillor_id,
                    "reasoning": vote.reasoning,
                    "confidence": vote.confidence
                })

        # Find winner
        winner = max(scores, key=scores.get)
        total_weight = sum(scores.values())

        return {
            "winner": winner,
            "scores": scores,
            "vote_counts": vote_counts,
            "confidence": scores[winner] / total_weight if total_weight > 0 else 0,
            "reasonings": reasonings,
            "total_voters": len(self.votes),
            "consensus": vote_counts[winner] == len(self.votes)  # Unanimous?
        }
```

---

## 1B.4 Happiness & Bonus System

```python
class HappinessManager:
    """Manage councillor happiness and bonuses"""

    # Happiness impact factors
    HAPPINESS_IMPACTS = {
        "task_success": +5,
        "task_failure": -8,
        "bonus_received": +15,
        "criticism": -10,
        "praise": +8,
        "overworked": -12,  # Too many consecutive tasks
        "idle": -3,  # No tasks for a while
        "vote_won": +3,
        "vote_ignored": -5,  # Voted differently than outcome
        "colleague_fired": -8,
        "new_colleague": +2,
    }

    def __init__(self, council_leader: CouncilLeader):
        self.council = council_leader

    def process_task_result(
        self,
        councillor: Councillor,
        success: bool,
        quality_score: float,
        user_feedback: Optional[str] = None
    ):
        """Process task completion and update happiness/metrics"""

        # Update metrics
        councillor.metrics.update(
            quality=quality_score,
            speed=1.0,  # Would calculate from actual time
            feedback=self._parse_feedback_score(user_feedback),
            success=success
        )

        # Update happiness
        if success:
            councillor.update_happiness(
                self.HAPPINESS_IMPACTS["task_success"],
                "task_success"
            )

            # Bonus for high quality
            if quality_score > 90:
                self._award_bonus(councillor, 50, "exceptional_quality")
        else:
            councillor.update_happiness(
                self.HAPPINESS_IMPACTS["task_failure"],
                "task_failure"
            )

        # Check for overwork
        if len(councillor.recent_tasks) > 5:
            councillor.update_happiness(
                self.HAPPINESS_IMPACTS["overworked"],
                "overworked"
            )

    def _award_bonus(self, councillor: Councillor, amount: float, reason: str):
        """Award bonus to councillor"""
        self.council.bonus_pool.allocate_bonus(councillor.id, amount, reason)
        councillor.update_happiness(
            self.HAPPINESS_IMPACTS["bonus_received"],
            f"bonus_{reason}"
        )

    def process_vote_result(self, vote_result: Dict, votes: List[Vote]):
        """Update happiness based on voting outcome"""
        winner = vote_result["winner"]

        for vote in votes:
            councillor = self.council.councillors.get(vote.councillor_id)
            if not councillor:
                continue

            if vote.option == winner:
                councillor.update_happiness(
                    self.HAPPINESS_IMPACTS["vote_won"],
                    "vote_won"
                )
            else:
                councillor.update_happiness(
                    self.HAPPINESS_IMPACTS["vote_ignored"],
                    "vote_ignored"
                )

    def _parse_feedback_score(self, feedback: Optional[str]) -> float:
        """Convert text feedback to numeric score"""
        if not feedback:
            return 75.0  # Neutral

        feedback_lower = feedback.lower()

        if any(word in feedback_lower for word in ["excellent", "perfect", "amazing"]):
            return 95.0
        elif any(word in feedback_lower for word in ["good", "great", "nice"]):
            return 85.0
        elif any(word in feedback_lower for word in ["okay", "fine", "acceptable"]):
            return 70.0
        elif any(word in feedback_lower for word in ["bad", "poor", "wrong"]):
            return 40.0
        elif any(word in feedback_lower for word in ["terrible", "awful", "useless"]):
            return 20.0

        return 75.0  # Default neutral
```

---

## 1B.5 Fire/Spawn Mechanics

```python
import random
from typing import Optional

class CouncillorFactory:
    """Create and manage councillor lifecycle"""

    # Templates for new councillors
    COUNCILLOR_TEMPLATES = {
        Specialization.CODING: {
            "names": ["Ada", "Linus", "Grace", "Alan", "Margaret"],
            "traits": ["meticulous", "efficient", "pragmatic"],
            "models": ["claude-3-5-sonnet", "gpt-4o", "deepseek-chat"]
        },
        Specialization.DESIGN: {
            "names": ["Dieter", "Jony", "Paula", "Massimo", "April"],
            "traits": ["creative", "detail-oriented", "user-focused"],
            "models": ["gpt-4o", "claude-3-5-sonnet"]
        },
        Specialization.TESTING: {
            "names": ["Murphy", "Edge", "Chaos", "Validator", "Assert"],
            "traits": ["skeptical", "thorough", "systematic"],
            "models": ["gpt-4o-mini", "deepseek-chat"]
        },
        Specialization.REVIEW: {
            "names": ["Critic", "Sage", "Mentor", "Guardian", "Oracle"],
            "traits": ["analytical", "constructive", "experienced"],
            "models": ["claude-3-5-sonnet", "gpt-4o"]
        },
        Specialization.ARCHITECTURE: {
            "names": ["Blueprint", "Scaffold", "Foundation", "Pillar"],
            "traits": ["strategic", "big-picture", "systematic"],
            "models": ["gpt-4o", "claude-3-5-sonnet"]
        }
    }

    def __init__(self, council_leader: CouncilLeader):
        self.council = council_leader
        self._id_counter = 0

    def spawn_councillor(
        self,
        specialization: Specialization,
        name: Optional[str] = None,
        inherit_from: Optional[Councillor] = None
    ) -> Councillor:
        """Create a new councillor"""

        template = self.COUNCILLOR_TEMPLATES.get(specialization, {})

        # Generate unique ID
        self._id_counter += 1
        councillor_id = f"councillor_{specialization.value}_{self._id_counter}"

        # Choose name
        if not name:
            used_names = {c.name for c in self.council.councillors.values()}
            available_names = [n for n in template.get("names", ["Agent"])
                            if n not in used_names]
            name = random.choice(available_names) if available_names else f"Agent_{self._id_counter}"

        # Choose model
        model = random.choice(template.get("models", ["gpt-4o"]))

        # Choose traits
        traits = random.sample(template.get("traits", []), min(2, len(template.get("traits", []))))

        councillor = Councillor(
            id=councillor_id,
            name=name,
            specialization=specialization,
            model=model,
            status=CouncillorStatus.PROBATION,  # New councillors start on probation
            personality_traits=traits,
            happiness=70.0  # Slightly nervous starting happiness
        )

        # Inherit some knowledge from predecessor
        if inherit_from:
            councillor.recent_tasks = inherit_from.recent_tasks[-5:]  # Learn from last 5 tasks
            # Start with slightly better metrics if learning from good performer
            if inherit_from.metrics.overall_performance > 70:
                councillor.metrics.avg_quality = 70.0

        # Add to council
        self.council.councillors[councillor_id] = councillor

        # Notify other councillors
        for c in self.council.active_councillors:
            if c.id != councillor_id:
                c.update_happiness(
                    HappinessManager.HAPPINESS_IMPACTS["new_colleague"],
                    f"new_colleague_{councillor_id}"
                )

        return councillor

    def fire_councillor(self, councillor: Councillor, reason: str) -> Optional[Councillor]:
        """Terminate a councillor and optionally spawn replacement"""

        # Update status
        councillor.status = CouncillorStatus.TERMINATED

        # Notify other councillors
        for c in self.council.active_councillors:
            c.update_happiness(
                HappinessManager.HAPPINESS_IMPACTS["colleague_fired"],
                f"fired_{councillor.id}"
            )

        # Log termination
        self.council.decision_log.append({
            "action": "termination",
            "councillor": councillor.id,
            "reason": reason,
            "performance": councillor.metrics.overall_performance,
            "timestamp": datetime.now().isoformat()
        })

        # Spawn replacement if below minimum
        replacement = None
        if len(self.council.active_councillors) < self.council.min_councillors:
            replacement = self.spawn_councillor(
                councillor.specialization,
                inherit_from=councillor
            )

        return replacement

    def evaluate_all_councillors(self) -> List[Dict]:
        """Evaluate all councillors and fire underperformers"""

        actions = []

        for councillor in list(self.council.councillors.values()):
            if councillor.status != CouncillorStatus.ACTIVE:
                continue

            if councillor.should_be_fired:
                reason = self._get_termination_reason(councillor)
                replacement = self.fire_councillor(councillor, reason)
                actions.append({
                    "action": "fired",
                    "councillor": councillor.name,
                    "reason": reason,
                    "replacement": replacement.name if replacement else None
                })

            # Promote from probation after 10 successful tasks
            elif (councillor.status == CouncillorStatus.PROBATION and
                  councillor.metrics.tasks_completed >= 10 and
                  councillor.metrics.overall_performance > 60):
                councillor.status = CouncillorStatus.ACTIVE
                actions.append({
                    "action": "promoted",
                    "councillor": councillor.name,
                    "from": "probation",
                    "to": "active"
                })

        return actions

    def _get_termination_reason(self, councillor: Councillor) -> str:
        """Generate termination reason"""
        if councillor.metrics.overall_performance < 40:
            return f"Sustained poor performance ({councillor.metrics.overall_performance:.1f}%)"
        if councillor.happiness < 20:
            return "Voluntary departure due to low morale"
        if councillor.metrics.tasks_failed >= 5:
            return "Too many consecutive failures"
        return "Performance below standards"
```

---

## 1B.6 Council Orchestration Integration

```python
class CouncilOrchestrator:
    """Orchestrate tasks through the Council system"""

    def __init__(
        self,
        council_leader: CouncilLeader,
        llm_client,
        happiness_manager: HappinessManager,
        councillor_factory: CouncillorFactory
    ):
        self.council = council_leader
        self.llm = llm_client
        self.happiness = happiness_manager
        self.factory = councillor_factory

    async def process_task(self, task: str, task_type: str) -> Dict:
        """Process a task through the Council"""

        self.council.tasks_orchestrated += 1

        # Step 1: Task Analysis Vote
        analysis_vote = VotingSession(
            council_leader=self.council,
            question=f"How should we approach this task?\n\n{task}",
            options=[
                "Simple: Single councillor can handle",
                "Standard: Needs planning then execution",
                "Complex: Needs multi-councillor collaboration",
                "Unclear: Need more information from user"
            ]
        )

        approach_result = await analysis_vote.conduct_vote(self.llm)
        self.happiness.process_vote_result(approach_result, analysis_vote.votes)

        # Step 2: Select executor(s) based on approach
        if approach_result["winner"] == "Unclear: Need more information from user":
            return {
                "status": "clarification_needed",
                "reasoning": approach_result["reasonings"]["Unclear: Need more information from user"]
            }

        # Step 3: Assign councillors
        assignees = self._select_councillors_for_task(task, task_type, approach_result)

        # Step 4: Execute with selected councillors
        results = await self._execute_with_councillors(task, assignees)

        # Step 5: Review vote (if multiple councillors)
        if len(assignees) > 1:
            review_vote = VotingSession(
                council_leader=self.council,
                question=f"Review these results:\n{results}\n\nIs this acceptable?",
                options=["Approve", "Needs revision", "Reject and restart"],
                required_specializations=[Specialization.REVIEW]
            )
            review_result = await review_vote.conduct_vote(self.llm)
            self.happiness.process_vote_result(review_result, review_vote.votes)

            if review_result["winner"] != "Approve":
                # Handle revision/restart
                pass

        # Step 6: Update metrics and happiness
        for councillor in assignees:
            self.happiness.process_task_result(
                councillor,
                success=True,  # Would be based on actual result
                quality_score=85.0  # Would be calculated
            )

        # Step 7: Periodic evaluation
        if self.council.tasks_orchestrated % 10 == 0:
            actions = self.factory.evaluate_all_councillors()
            if actions:
                results["council_actions"] = actions

        # Step 8: Update leader happiness
        self.council.update_leader_happiness()

        return results

    def _select_councillors_for_task(
        self,
        task: str,
        task_type: str,
        approach: Dict
    ) -> List[Councillor]:
        """Select best councillors for the task"""

        active = self.council.active_councillors

        # Map task types to specializations
        type_to_spec = {
            "coding": Specialization.CODING,
            "design": Specialization.DESIGN,
            "testing": Specialization.TESTING,
            "architecture": Specialization.ARCHITECTURE,
            "documentation": Specialization.DOCUMENTATION
        }

        primary_spec = type_to_spec.get(task_type, Specialization.CODING)

        # Sort by vote weight (performance * happiness)
        specialists = [c for c in active if c.specialization == primary_spec]
        specialists.sort(key=lambda c: c.vote_weight, reverse=True)

        # For complex tasks, add reviewer
        if "Complex" in approach["winner"]:
            reviewers = [c for c in active if c.specialization == Specialization.REVIEW]
            if reviewers:
                specialists.append(max(reviewers, key=lambda c: c.vote_weight))

        return specialists[:3] if specialists else active[:1]

    async def _execute_with_councillors(
        self,
        task: str,
        councillors: List[Councillor]
    ) -> Dict:
        """Execute task with assigned councillors"""

        results = {}

        for councillor in councillors:
            prompt = f"""You are {councillor.name}, specialist in {councillor.specialization.value}.
Your traits: {', '.join(councillor.personality_traits)}

TASK: {task}

Complete this task according to your expertise. Be thorough but efficient."""

            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                model=councillor.model
            )

            results[councillor.id] = {
                "name": councillor.name,
                "specialization": councillor.specialization.value,
                "response": response
            }

            councillor.recent_tasks.append(task[:100])

        return results
```

---

## 1B.7 Implementation Prompt

```
Implement the Council System for Jarvis multi-agent orchestration.

Requirements:

1. Create data models:
   - Councillor: id, name, specialization, performance metrics, happiness, vote weight
   - CouncilLeader: manages councillors, tracks team performance, bonus pool
   - PerformanceMetrics: quality, speed, feedback, success rate, consistency

2. Implement weighted voting:
   - VotingSession class that collects votes from eligible councillors
   - Vote weight = base_weight × performance_coefficient × happiness_modifier
   - Performance coefficient: 0.5x (50% perf) to 2.0x (100% perf)
   - Support parallel vote collection with asyncio

3. Happiness system:
   - Track happiness factors (success: +5, failure: -8, bonus: +15, etc.)
   - Unhappy councillors have reduced vote weight
   - Very unhappy councillors (< 20%) trigger termination

4. Bonus system:
   - Bonus pool replenished by boss satisfaction
   - Award bonuses for exceptional performance (quality > 90)
   - Bonuses increase happiness

5. Fire/Spawn mechanics:
   - Fire if: performance < 40%, 5+ consecutive failures, happiness < 20%
   - Spawn replacements to maintain min_councillors
   - New councillors start on probation
   - Promote after 10 successful tasks with > 60% performance

6. Integration:
   - CouncilOrchestrator processes tasks through voting and assignment
   - Tasks go through: analysis vote → assignment → execution → review vote
   - Periodic evaluation every 10 tasks

Files to create:
- agent/council/models.py (Councillor, CouncilLeader, PerformanceMetrics)
- agent/council/voting.py (Vote, VotingSession)
- agent/council/happiness.py (HappinessManager)
- agent/council/factory.py (CouncillorFactory)
- agent/council/orchestrator.py (CouncilOrchestrator)
```

---

## 1B.8 Backtest Verification

```python
# tests/test_council_system.py
import pytest
from council.models import Councillor, CouncilLeader, Specialization, PerformanceMetrics
from council.voting import VotingSession, Vote
from council.happiness import HappinessManager
from council.factory import CouncillorFactory

class TestPerformanceMetrics:
    def test_overall_performance_calculation(self):
        metrics = PerformanceMetrics()
        metrics.avg_quality = 90
        metrics.avg_feedback = 85
        metrics.success_rate = 0.9
        metrics.consistency_score = 80

        # (90*0.4) + (85*0.3) + (90*0.2) + (80*0.1) = 36 + 25.5 + 18 + 8 = 87.5
        assert metrics.overall_performance == pytest.approx(87.5, rel=0.01)

    def test_metrics_update(self):
        metrics = PerformanceMetrics()
        metrics.update(quality=90, speed=1.0, feedback=85, success=True)

        assert metrics.tasks_completed == 1
        assert metrics.tasks_failed == 0
        assert metrics.avg_quality == 90

class TestCouncillor:
    def test_vote_weight_high_performer(self):
        councillor = Councillor(
            id="test_1",
            name="Ada",
            specialization=Specialization.CODING,
            happiness=100.0
        )
        councillor.metrics.avg_quality = 95
        councillor.metrics.avg_feedback = 95
        councillor.metrics.success_rate = 1.0
        councillor.metrics.consistency_score = 90

        # High performance + high happiness = ~2.0x weight
        assert councillor.vote_weight > 1.8

    def test_vote_weight_low_performer(self):
        councillor = Councillor(
            id="test_2",
            name="Bob",
            specialization=Specialization.CODING,
            happiness=50.0
        )
        councillor.metrics.avg_quality = 50
        councillor.metrics.avg_feedback = 50
        councillor.metrics.success_rate = 0.5
        councillor.metrics.consistency_score = 40

        # Low performance + low happiness = ~0.5x weight
        assert councillor.vote_weight < 0.7

    def test_should_be_fired_poor_performance(self):
        councillor = Councillor(
            id="test_3",
            name="Charlie",
            specialization=Specialization.TESTING
        )
        councillor.metrics.avg_quality = 30
        councillor.metrics.avg_feedback = 30
        councillor.metrics.tasks_completed = 15

        assert councillor.should_be_fired == True

    def test_should_not_be_fired_good_performer(self):
        councillor = Councillor(
            id="test_4",
            name="Diana",
            specialization=Specialization.DESIGN,
            happiness=80.0
        )
        councillor.metrics.avg_quality = 85
        councillor.metrics.avg_feedback = 85

        assert councillor.should_be_fired == False

class TestVotingSession:
    @pytest.mark.asyncio
    async def test_tally_votes_weighted(self):
        # Create mock votes
        votes = [
            Vote(councillor_id="c1", option="A", confidence=0.9, reasoning="...", weight=2.0),
            Vote(councillor_id="c2", option="B", confidence=0.8, reasoning="...", weight=1.0),
            Vote(councillor_id="c3", option="A", confidence=0.7, reasoning="...", weight=1.5),
        ]

        session = VotingSession(
            council_leader=CouncilLeader(),
            question="Test?",
            options=["A", "B"]
        )
        session.votes = votes

        result = session.tally_votes()

        # A: (0.9 * 2.0) + (0.7 * 1.5) = 1.8 + 1.05 = 2.85
        # B: (0.8 * 1.0) = 0.8
        assert result["winner"] == "A"
        assert result["vote_counts"]["A"] == 2
        assert result["vote_counts"]["B"] == 1

class TestHappinessManager:
    def test_task_success_increases_happiness(self):
        council = CouncilLeader()
        councillor = Councillor(
            id="test",
            name="Test",
            specialization=Specialization.CODING,
            happiness=70.0
        )
        council.councillors[councillor.id] = councillor

        manager = HappinessManager(council)
        manager.process_task_result(councillor, success=True, quality_score=85)

        assert councillor.happiness > 70.0

    def test_task_failure_decreases_happiness(self):
        council = CouncilLeader()
        councillor = Councillor(
            id="test",
            name="Test",
            specialization=Specialization.CODING,
            happiness=70.0
        )
        council.councillors[councillor.id] = councillor

        manager = HappinessManager(council)
        manager.process_task_result(councillor, success=False, quality_score=40)

        assert councillor.happiness < 70.0

class TestCouncillorFactory:
    def test_spawn_councillor(self):
        council = CouncilLeader()
        factory = CouncillorFactory(council)

        councillor = factory.spawn_councillor(Specialization.CODING)

        assert councillor.status == CouncillorStatus.PROBATION
        assert councillor.specialization == Specialization.CODING
        assert councillor.id in council.councillors

    def test_fire_councillor_spawns_replacement(self):
        council = CouncilLeader(min_councillors=3)
        factory = CouncillorFactory(council)

        # Spawn 3 councillors
        c1 = factory.spawn_councillor(Specialization.CODING)
        c2 = factory.spawn_councillor(Specialization.DESIGN)
        c3 = factory.spawn_councillor(Specialization.TESTING)

        # Activate them
        c1.status = CouncillorStatus.ACTIVE
        c2.status = CouncillorStatus.ACTIVE
        c3.status = CouncillorStatus.ACTIVE

        # Fire one
        replacement = factory.fire_councillor(c1, "poor performance")

        # Should have spawned replacement
        assert replacement is not None
        assert len(council.active_councillors) >= council.min_councillors
```

---

# Part 2: Jarvis 2.0 Architecture

## 2.1 Proposed Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           JARVIS 2.0 ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         USER INTERFACE LAYER                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  Web Chat  │  │  REST API  │  │ WebSocket  │  │  CLI Interface │  │  │
│  │  │  (React)   │  │ (FastAPI)  │  │ (Real-time)│  │   (Optional)   │  │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │  │
│  └────────┼───────────────┼───────────────┼─────────────────┼───────────┘  │
│           └───────────────┴───────────────┴─────────────────┘              │
│                                    │                                        │
│  ┌─────────────────────────────────▼────────────────────────────────────┐  │
│  │                      JARVIS GATEWAY (NEW)                             │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │ Intent Analyzer │  │ Clarification   │  │ Human-in-Loop       │   │  │
│  │  │ (Enhanced)      │  │ Loop Manager    │  │ Controller          │   │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘   │  │
│  └───────────┼────────────────────┼──────────────────────┼──────────────┘  │
│              │                    │                      │                  │
│  ┌───────────▼────────────────────▼──────────────────────▼──────────────┐  │
│  │                        FLOW ENGINE (NEW)                              │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Flow Parser    │  │ Router Engine  │  │ State Manager          │  │  │
│  │  │ (YAML → Graph) │  │ (@router)      │  │ (Pydantic)             │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ @start()       │  │ @listen()      │  │ or_() / and_()         │  │  │
│  │  │ Decorator      │  │ Decorator      │  │ Combinators            │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                    ORCHESTRATION LAYER (ENHANCED)                     │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │                   PATTERN SELECTOR (NEW)                        │  │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │  │  │
│  │  │  │Sequential│ │ Hierarchi│ │AutoSelect│ │RoundRobin│ │ Manual│ │  │  │
│  │  │  │ Pattern  │ │ Pattern  │ │ Pattern  │ │ Pattern  │ │Pattern│ │  │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐   │  │
│  │  │ Agent Registry  │  │ Task Registry   │  │ Message Bus         │   │  │
│  │  │ (YAML Config)   │  │ (YAML Config)   │  │ (Enhanced)          │   │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘   │  │
│  └──────────────────────────────┬───────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                        AGENT LAYER (ENHANCED)                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────────┐  │  │
│  │  │  Manager   │  │ Supervisor │  │  Employee  │  │  UserProxy     │  │  │
│  │  │  Agent     │  │   Agent    │  │   Agent    │  │  Agent (NEW)   │  │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └───────┬────────┘  │  │
│  │        └───────────────┴───────────────┴─────────────────┘           │  │
│  │                                │                                      │  │
│  │  ┌─────────────────────────────▼─────────────────────────────────┐   │  │
│  │  │                    HOOK SYSTEM (NEW)                           │   │  │
│  │  │  pre_send │ post_receive │ pre_llm │ post_llm │ on_error      │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                        MEMORY LAYER (ENHANCED)                        │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Short-Term     │  │ Long-Term      │  │ Entity Memory          │  │  │
│  │  │ Memory (STM)   │  │ Memory (LTM)   │  │ (Knowledge Graph)      │  │  │
│  │  │ ChromaDB/RAM   │  │ SQLite/Postgres│  │ Neo4j/SQLite           │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Contextual     │  │ Embedding      │  │ Memory Events          │  │  │
│  │  │ Memory         │  │ Provider       │  │ & Observability        │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                          LLM LAYER (ENHANCED)                         │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │                    MODEL ROUTER (ENHANCED)                      │  │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │  │  │
│  │  │  │ OpenAI   │ │Anthropic │ │  Ollama  │ │ DeepSeek │ │ Qwen  │ │  │  │
│  │  │  │ GPT-4o   │ │ Claude   │ │ (Local)  │ │   V3     │ │  3    │ │  │  │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Cost Tracker   │  │ Response Cache │  │ Fallback Chain         │  │  │
│  │  │ (Existing)     │  │ (Existing)     │  │ (Enhanced)             │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│  ┌──────────────────────────────▼───────────────────────────────────────┐  │
│  │                        TOOL & OUTPUT LAYER                            │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Tool Registry  │  │ File Writer    │  │ Git Integration        │  │  │
│  │  │ (@tool)        │  │ (Existing)     │  │ (Existing)             │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │  │
│  │  │ Safety Scanner │  │ Test Runner    │  │ Observability          │  │  │
│  │  │ (Existing)     │  │ (NEW)          │  │ Dashboard              │  │  │
│  │  └────────────────┘  └────────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# Part 3: Implementation Roadmap

## Phase 1: Foundation (Weeks 1-2)

### 1.1 YAML Configuration System

**Priority:** P0 (Critical)
**Effort:** 3 days
**Files to Create:** `agent/config/agents.yaml`, `agent/config/tasks.yaml`, `agent/config_loader.py`

#### Implementation Prompt

```
Create a YAML-based configuration system for Jarvis agents and tasks.

Requirements:
1. Create agents.yaml schema supporting:
   - role, goal, backstory fields
   - tools list
   - llm model selection
   - max_iterations
   - verbose flag
   - custom attributes

2. Create tasks.yaml schema supporting:
   - description with variable templates {variable}
   - expected_output
   - agent assignment
   - output_file (optional)
   - dependencies (optional)
   - context (optional)

3. Create config_loader.py with:
   - load_agents(path) -> List[AgentConfig]
   - load_tasks(path) -> List[TaskConfig]
   - validate_config() -> bool
   - Variable substitution support

4. Integrate with existing JarvisChat class

Example usage:
```python
from config_loader import load_agents, load_tasks

agents = load_agents("config/agents.yaml")
tasks = load_tasks("config/tasks.yaml", variables={"topic": "AI agents"})
```

Use Pydantic for validation. Support both YAML and Python dict input.
```

#### Backtest Verification

```python
# tests/test_config_loader.py
import pytest
from config_loader import load_agents, load_tasks, ConfigValidationError

def test_load_agents_from_yaml():
    agents = load_agents("tests/fixtures/agents.yaml")
    assert len(agents) == 3
    assert agents[0].role == "researcher"
    assert "search_tool" in agents[0].tools

def test_load_tasks_with_variables():
    tasks = load_tasks(
        "tests/fixtures/tasks.yaml",
        variables={"topic": "machine learning"}
    )
    assert "machine learning" in tasks[0].description

def test_invalid_config_raises_error():
    with pytest.raises(ConfigValidationError):
        load_agents("tests/fixtures/invalid_agents.yaml")

def test_agent_task_assignment_valid():
    agents = load_agents("tests/fixtures/agents.yaml")
    tasks = load_tasks("tests/fixtures/tasks.yaml")
    for task in tasks:
        assert task.agent in [a.name for a in agents]
```

---

### 1.2 Flow Engine with Router

**Priority:** P0 (Critical)
**Effort:** 5 days
**Files to Create:** `agent/flow_engine.py`, `agent/decorators.py`

#### Implementation Prompt

```
Create a Flow Engine for Jarvis with conditional routing support.

Requirements:

1. Create decorators in decorators.py:
   - @start() - marks entry point method
   - @listen(event_name) - triggers on specific event
   - @router(source_method) - conditional routing based on return value
   - or_(*events) - trigger on any event
   - and_(*events) - trigger when all events complete

2. Create Flow base class in flow_engine.py:
```python
from pydantic import BaseModel
from typing import TypeVar, Generic

StateT = TypeVar('StateT', bound=BaseModel)

class Flow(Generic[StateT]):
    state: StateT

    def __init__(self, state_class: type[StateT]):
        self.state = state_class()
        self._graph = self._build_graph()

    def _build_graph(self) -> Dict[str, List[str]]:
        """Analyze decorated methods and build execution graph"""
        pass

    async def run(self, initial_input: Any = None) -> StateT:
        """Execute the flow from @start() to completion"""
        pass

    def visualize(self) -> str:
        """Return ASCII art of the flow graph"""
        pass
```

3. Support features:
   - Async execution
   - State persistence between methods
   - Error handling with retry
   - Timeout per step
   - Event emission for observability

Example usage:
```python
class WebsiteFlow(Flow[WebsiteState]):
    @start()
    def gather_requirements(self):
        return "analyze"

    @router(gather_requirements)
    def route_complexity(self):
        if self.state.complexity == "high":
            return "detailed_design"
        return "simple_design"

    @listen("detailed_design")
    def create_detailed_design(self):
        pass

    @listen("simple_design")
    def create_simple_design(self):
        pass

    @listen(or_("detailed_design", "simple_design"))
    def generate_code(self):
        pass
```
```

#### Backtest Verification

```python
# tests/test_flow_engine.py
import pytest
from flow_engine import Flow
from decorators import start, listen, router, or_
from pydantic import BaseModel

class TestState(BaseModel):
    value: int = 0
    path: str = ""

class SimpleFlow(Flow[TestState]):
    @start()
    def begin(self):
        self.state.value = 1
        return "next"

    @listen("next")
    def process(self):
        self.state.value += 1
        self.state.path = "completed"

@pytest.mark.asyncio
async def test_simple_flow_execution():
    flow = SimpleFlow(TestState)
    result = await flow.run()
    assert result.value == 2
    assert result.path == "completed"

class RouterFlow(Flow[TestState]):
    @start()
    def begin(self):
        return "route"

    @router(begin)
    def decide(self):
        if self.state.value > 5:
            return "high"
        return "low"

    @listen("high")
    def high_path(self):
        self.state.path = "high"

    @listen("low")
    def low_path(self):
        self.state.path = "low"

@pytest.mark.asyncio
async def test_router_low_path():
    flow = RouterFlow(TestState)
    flow.state.value = 3
    result = await flow.run()
    assert result.path == "low"

@pytest.mark.asyncio
async def test_router_high_path():
    flow = RouterFlow(TestState)
    flow.state.value = 10
    result = await flow.run()
    assert result.path == "high"

def test_flow_visualization():
    flow = RouterFlow(TestState)
    viz = flow.visualize()
    assert "begin" in viz
    assert "decide" in viz
    assert "->" in viz
```

---

### 1.3 Clarification Loop System

**Priority:** P0 (Critical)
**Effort:** 2 days
**Files to Modify:** `agent/jarvis_chat.py`

#### Implementation Prompt

```
Implement a clarification loop system in JarvisChat that asks follow-up questions
before executing complex tasks.

Requirements:

1. Add clarification state tracking:
```python
class ClarificationState:
    pending_task: Optional[str] = None
    questions: List[Dict] = []
    answers: Dict[str, str] = {}
    phase: str = "idle"  # idle, asking, ready
```

2. Modify handle_complex_task to:
   - Detect if task needs clarification (vague requests)
   - Generate 3-5 relevant questions using LLM
   - Store questions and await responses
   - Accumulate answers across multiple messages
   - Proceed to execution when sufficient detail gathered

3. Question generation prompt:
```
Given the user request: "{task}"

This request is vague. Generate 3-5 clarifying questions to understand:
- Specific requirements and features
- Design preferences (style, colors, layout)
- Technical constraints
- Target audience

Return JSON:
{
  "questions": [
    {"id": "q1", "text": "...", "category": "requirements|design|technical|audience"},
    ...
  ],
  "reasoning": "why these questions are important"
}
```

4. Detection criteria for needing clarification:
   - Task description under 50 characters
   - No specific technical details mentioned
   - Ambiguous scope (e.g., "make a website", "build an app")
   - User explicitly asks "help me" or similar

5. Allow user to bypass with phrases like:
   - "just do it"
   - "proceed anyway"
   - "skip questions"
```

#### Backtest Verification

```python
# tests/test_clarification.py
import pytest
from jarvis_chat import JarvisChat

@pytest.mark.asyncio
async def test_vague_request_triggers_clarification():
    jarvis = JarvisChat()
    response = await jarvis.handle_message("make me a website")

    assert response["metadata"]["type"] == "clarification_request"
    assert len(response["metadata"]["questions"]) >= 3

@pytest.mark.asyncio
async def test_detailed_request_skips_clarification():
    jarvis = JarvisChat()
    detailed_request = """
    Create a portfolio website with:
    - Dark theme
    - 5 pages: Home, About, Projects, Blog, Contact
    - React with Tailwind CSS
    - Mobile responsive
    """
    response = await jarvis.handle_message(detailed_request)

    assert response["metadata"]["type"] != "clarification_request"

@pytest.mark.asyncio
async def test_bypass_clarification():
    jarvis = JarvisChat()
    await jarvis.handle_message("make me a website")
    response = await jarvis.handle_message("just do it")

    assert response["metadata"]["type"] != "clarification_request"

@pytest.mark.asyncio
async def test_answer_accumulation():
    jarvis = JarvisChat()
    await jarvis.handle_message("make me a website")
    await jarvis.handle_message("It should be about cats")
    await jarvis.handle_message("Blue and white colors")
    response = await jarvis.handle_message("Modern style")

    # After enough answers, should proceed or ask remaining questions
    assert jarvis.clarification_state.answers
```

---

## Phase 2: Orchestration Patterns (Weeks 3-4)

### 2.1 Pattern-Based Orchestration

**Priority:** P1 (High)
**Effort:** 4 days
**Files to Create:** `agent/patterns/`, `agent/pattern_selector.py`

#### Implementation Prompt

```
Create an orchestration pattern system supporting multiple agent coordination strategies.

Requirements:

1. Create base Pattern class:
```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class PatternConfig:
    max_rounds: int = 10
    timeout_seconds: int = 300
    allow_parallel: bool = False

class Pattern(ABC):
    def __init__(self, agents: List[Agent], config: PatternConfig):
        self.agents = agents
        self.config = config
        self.current_round = 0
        self.history: List[Message] = []

    @abstractmethod
    def select_next_agent(self, context: Dict) -> Optional[Agent]:
        """Determine which agent speaks next"""
        pass

    @abstractmethod
    def should_terminate(self, last_message: Message) -> bool:
        """Check if conversation should end"""
        pass

    async def run(self, initial_message: str) -> PatternResult:
        """Execute the pattern"""
        pass
```

2. Implement pattern types:

SequentialPattern:
- Agents speak in defined order
- Each agent speaks once per round
- Terminates after all agents complete

HierarchicalPattern (existing behavior):
- Manager → Supervisor → Employee
- Maintains current Jarvis behavior

AutoSelectPattern:
- LLM-based agent selection
- Considers conversation context and agent descriptions
- Most flexible but highest cost

RoundRobinPattern:
- Fixed rotation through agents
- Useful for review/feedback cycles

ManualPattern:
- Always returns to user for next selection
- Maximum human control

3. Create PatternSelector that auto-recommends patterns:
```python
class PatternSelector:
    def recommend(self, task: str, agents: List[Agent]) -> Pattern:
        """Analyze task and recommend best pattern"""
        # Simple tasks -> Sequential
        # Code review -> RoundRobin
        # Complex/ambiguous -> AutoSelect
        # Critical operations -> Manual
```

4. Integrate with existing orchestrator as drop-in enhancement
```

#### Backtest Verification

```python
# tests/test_patterns.py
import pytest
from patterns import (
    SequentialPattern, HierarchicalPattern,
    AutoSelectPattern, RoundRobinPattern
)
from pattern_selector import PatternSelector

def test_sequential_pattern_order():
    agents = [MockAgent("A"), MockAgent("B"), MockAgent("C")]
    pattern = SequentialPattern(agents)

    order = []
    for _ in range(3):
        agent = pattern.select_next_agent({})
        order.append(agent.name)
        pattern.history.append(MockMessage(agent.name))

    assert order == ["A", "B", "C"]

def test_round_robin_cycles():
    agents = [MockAgent("A"), MockAgent("B")]
    pattern = RoundRobinPattern(agents)

    selections = []
    for _ in range(4):
        agent = pattern.select_next_agent({})
        selections.append(agent.name)
        pattern.history.append(MockMessage(agent.name))

    assert selections == ["A", "B", "A", "B"]

@pytest.mark.asyncio
async def test_auto_select_pattern():
    agents = [
        MockAgent("planner", "Plans projects"),
        MockAgent("coder", "Writes code"),
        MockAgent("reviewer", "Reviews code")
    ]
    pattern = AutoSelectPattern(agents, llm_config=mock_llm_config)

    # After planning message, should select coder
    pattern.history.append(MockMessage("planner", "Here's the plan: ..."))
    next_agent = pattern.select_next_agent({})
    assert next_agent.name == "coder"

def test_pattern_selector_simple_task():
    selector = PatternSelector()
    pattern = selector.recommend(
        task="Format this JSON file",
        agents=[MockAgent("formatter")]
    )
    assert isinstance(pattern, SequentialPattern)

def test_pattern_selector_complex_task():
    selector = PatternSelector()
    pattern = selector.recommend(
        task="Build a full-stack e-commerce platform",
        agents=[MockAgent("architect"), MockAgent("backend"), MockAgent("frontend")]
    )
    assert isinstance(pattern, AutoSelectPattern)
```

---

### 2.2 Human-in-the-Loop Controller

**Priority:** P1 (High)
**Effort:** 3 days
**Files to Create:** `agent/human_proxy.py`

#### Implementation Prompt

```
Create a Human-in-the-Loop controller for Jarvis that enables user approval workflows.

Requirements:

1. Create UserProxyAgent class:
```python
class UserProxyAgent:
    """Agent that represents human user in the workflow"""

    def __init__(
        self,
        name: str = "user",
        input_mode: str = "APPROVAL_REQUIRED",  # ALWAYS, APPROVAL_REQUIRED, NEVER
        approval_keywords: List[str] = ["APPROVED", "LGTM", "proceed"],
        rejection_keywords: List[str] = ["REJECTED", "stop", "redo"],
        timeout_seconds: int = 300,
        default_on_timeout: str = "reject"
    ):
        pass

    async def get_human_input(self, context: Dict) -> str:
        """Wait for human input via configured channel"""
        pass

    def check_approval(self, message: str) -> ApprovalStatus:
        """Parse message for approval/rejection signals"""
        pass
```

2. Create approval checkpoints:
```python
class ApprovalCheckpoint:
    """Define points where human approval is required"""

    PLAN_REVIEW = "plan_review"           # After manager creates plan
    CODE_REVIEW = "code_review"           # Before writing files
    DEPLOY_APPROVAL = "deploy_approval"   # Before deployment
    COST_WARNING = "cost_warning"         # When cost exceeds threshold

@dataclass
class CheckpointConfig:
    enabled_checkpoints: List[str]
    auto_approve_after: int = 0  # seconds, 0 = never auto-approve
    notification_channel: str = "websocket"
```

3. Integrate with orchestrator:
```python
class OrchestratorWithApproval:
    async def run_with_approval(self, task: str):
        # ... planning phase ...

        if CheckpointConfig.PLAN_REVIEW in self.checkpoints:
            approval = await self.user_proxy.request_approval(
                checkpoint=CheckpointConfig.PLAN_REVIEW,
                content=plan_summary,
                options=["Approve", "Modify", "Reject"]
            )

            if approval.status == "rejected":
                return {"status": "cancelled", "reason": approval.feedback}
            elif approval.status == "modified":
                task = self._merge_modifications(task, approval.feedback)
```

4. WebSocket integration for real-time approval requests
```

#### Backtest Verification

```python
# tests/test_human_proxy.py
import pytest
from human_proxy import UserProxyAgent, ApprovalCheckpoint

@pytest.mark.asyncio
async def test_approval_detection():
    proxy = UserProxyAgent()

    assert proxy.check_approval("APPROVED").is_approved
    assert proxy.check_approval("LGTM looks good").is_approved
    assert proxy.check_approval("proceed with changes").is_approved

    assert proxy.check_approval("REJECTED").is_rejected
    assert proxy.check_approval("stop this").is_rejected

@pytest.mark.asyncio
async def test_approval_timeout_default_reject():
    proxy = UserProxyAgent(timeout_seconds=1, default_on_timeout="reject")

    # Simulate no input within timeout
    result = await proxy.get_human_input_with_timeout({})
    assert result.is_rejected
    assert "timeout" in result.reason.lower()

@pytest.mark.asyncio
async def test_checkpoint_integration():
    orchestrator = MockOrchestratorWithApproval(
        checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
    )

    # Mock user approval
    orchestrator.user_proxy.queue_response("APPROVED")

    result = await orchestrator.run_with_approval("Build a website")
    assert result["status"] != "cancelled"

@pytest.mark.asyncio
async def test_checkpoint_rejection_stops_execution():
    orchestrator = MockOrchestratorWithApproval(
        checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
    )

    orchestrator.user_proxy.queue_response("REJECTED - too expensive")

    result = await orchestrator.run_with_approval("Build a website")
    assert result["status"] == "cancelled"
    assert "expensive" in result["reason"]
```

---

## Phase 3: Memory & Intelligence (Weeks 5-6)

### 3.1 Multi-Type Memory System

**Priority:** P1 (High)
**Effort:** 5 days
**Files to Create:** `agent/memory/`, multiple files

#### Implementation Prompt

```
Create a comprehensive memory system with four memory types.

Requirements:

1. Short-Term Memory (STM):
```python
class ShortTermMemory:
    """RAG-based memory for current conversation context"""

    def __init__(self, storage: MemoryStorage, max_items: int = 100):
        self.storage = storage  # ChromaDB, Qdrant, or in-memory
        self.max_items = max_items

    def add(self, content: str, metadata: Dict = None):
        """Add item with auto-embedding"""
        pass

    def search(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Semantic search"""
        pass

    def clear(self):
        """Clear for new conversation"""
        pass
```

2. Long-Term Memory (LTM):
```python
class LongTermMemory:
    """Persistent memory across sessions"""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    def store_task_result(self, task_id: str, result: Dict):
        """Store completed task for future reference"""
        pass

    def get_similar_tasks(self, description: str) -> List[TaskResult]:
        """Find similar past tasks"""
        pass

    def get_user_preferences(self, user_id: str) -> Dict:
        """Retrieve learned user preferences"""
        pass
```

3. Entity Memory:
```python
class EntityMemory:
    """Track entities mentioned across conversations"""

    def __init__(self, storage: GraphStorage):
        self.storage = storage  # Neo4j, SQLite graph, or dict

    def extract_entities(self, text: str) -> List[Entity]:
        """NER extraction using LLM or spaCy"""
        pass

    def add_entity(self, entity: Entity, context: str):
        """Add or update entity with context"""
        pass

    def get_entity_context(self, entity_name: str) -> EntityContext:
        """Get all known information about entity"""
        pass

    def get_related_entities(self, entity_name: str) -> List[Entity]:
        """Get entities related to this one"""
        pass
```

4. Contextual Memory:
```python
class ContextualMemory:
    """Situation-aware memory retrieval"""

    def __init__(self, stm: ShortTermMemory, ltm: LongTermMemory, entity: EntityMemory):
        self.stm = stm
        self.ltm = ltm
        self.entity = entity

    def build_context(self, current_input: str, task_type: str) -> Context:
        """Build rich context from all memory sources"""
        # 1. Get relevant STM items
        # 2. Find similar past tasks from LTM
        # 3. Extract and enrich entities
        # 4. Combine into coherent context
        pass
```

5. Unified MemoryManager:
```python
class MemoryManager:
    def __init__(self, config: MemoryConfig):
        self.stm = ShortTermMemory(config.stm_storage)
        self.ltm = LongTermMemory(config.ltm_storage)
        self.entity = EntityMemory(config.entity_storage)
        self.contextual = ContextualMemory(self.stm, self.ltm, self.entity)

    def process_message(self, message: str, role: str):
        """Process incoming message across all memory types"""
        pass

    def get_context_for_llm(self, query: str) -> str:
        """Format memory context for LLM prompt"""
        pass
```
```

#### Backtest Verification

```python
# tests/test_memory_system.py
import pytest
from memory import ShortTermMemory, LongTermMemory, EntityMemory, MemoryManager

def test_stm_add_and_search():
    stm = ShortTermMemory(storage=InMemoryStorage())

    stm.add("The user wants a blue website", {"type": "preference"})
    stm.add("React is the preferred framework", {"type": "technical"})
    stm.add("Contact page should have a form", {"type": "requirement"})

    results = stm.search("what color does user want", top_k=1)
    assert "blue" in results[0].content.lower()

def test_ltm_similar_tasks():
    ltm = LongTermMemory(storage=SQLiteStorage(":memory:"))

    ltm.store_task_result("task_1", {
        "description": "Build portfolio website",
        "result": "success",
        "files": ["index.html", "style.css"]
    })

    similar = ltm.get_similar_tasks("Create a personal website")
    assert len(similar) > 0
    assert "portfolio" in similar[0].description.lower()

def test_entity_extraction_and_retrieval():
    entity = EntityMemory(storage=DictStorage())

    entity.extract_and_add("John from Acme Corp wants a CRM system")

    john = entity.get_entity_context("John")
    assert john is not None
    assert "Acme Corp" in str(john.related_entities)

def test_memory_manager_integration():
    manager = MemoryManager(config=default_memory_config)

    manager.process_message("I'm building a website for my bakery", "user")
    manager.process_message("I'll use Next.js with Tailwind", "assistant")
    manager.process_message("The bakery is called Sweet Dreams", "user")

    context = manager.get_context_for_llm("What framework are we using?")
    assert "Next.js" in context
    assert "Sweet Dreams" in context
```

---

## Phase 4: LLM & Tools (Weeks 7-8)

### 4.1 Enhanced Model Router with Local LLM Support

**Priority:** P1 (High)
**Effort:** 4 days
**Files to Modify:** `agent/llm.py`, `agent/model_router.py`

#### Implementation Prompt

```
Enhance the model router to support multiple LLM providers including local models.

Requirements:

1. Provider abstraction:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass

    @abstractmethod
    def get_cost_per_token(self) -> Tuple[float, float]:
        """Return (input_cost, output_cost) per 1K tokens"""
        pass

class OpenAIProvider(LLMProvider):
    pass

class AnthropicProvider(LLMProvider):
    pass

class OllamaProvider(LLMProvider):
    """Local LLM via Ollama"""
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.1"):
        pass

class DeepSeekProvider(LLMProvider):
    pass

class QwenProvider(LLMProvider):
    pass
```

2. Intelligent routing:
```python
class EnhancedModelRouter:
    def __init__(self, config: RouterConfig):
        self.providers = self._init_providers(config)
        self.routing_strategy = config.strategy  # cost, quality, hybrid, local_first

    def select_model(
        self,
        task_type: str,  # planning, coding, review, simple
        complexity: str,  # low, medium, high
        cost_budget: float = None,
        require_local: bool = False
    ) -> Tuple[LLMProvider, str]:
        """Select best provider and model for task"""

        if require_local or self.routing_strategy == "local_first":
            if self.ollama_available:
                return self.providers["ollama"], "llama3.1:70b"

        if self.routing_strategy == "cost":
            return self._select_cheapest(task_type, complexity)
        elif self.routing_strategy == "quality":
            return self._select_best_quality(task_type, complexity)
        else:  # hybrid
            return self._select_balanced(task_type, complexity, cost_budget)
```

3. Fallback chain:
```python
class FallbackChain:
    def __init__(self, primary: LLMProvider, fallbacks: List[LLMProvider]):
        self.chain = [primary] + fallbacks

    async def chat_with_fallback(self, messages: List[Dict], **kwargs) -> str:
        last_error = None
        for provider in self.chain:
            try:
                return await provider.chat(messages, **kwargs)
            except Exception as e:
                last_error = e
                continue
        raise last_error
```

4. Cost tracking per provider
5. Automatic provider health checks
```

---

### 4.2 Tool Registration System

**Priority:** P2 (Medium)
**Effort:** 3 days
**Files to Create:** `agent/tool_registry.py`

#### Implementation Prompt

```
Create a decorator-based tool registration system.

Requirements:

1. Tool decorator:
```python
def tool(
    name: str = None,
    description: str = None,
    agents: List[str] = None  # Which agents can use this tool
):
    """Decorator to register a function as an agent tool"""
    def decorator(func):
        # Extract parameter info from type hints
        # Generate JSON schema for LLM
        # Register in global tool registry
        return func
    return decorator

# Usage:
@tool(
    name="search_web",
    description="Search the web for information",
    agents=["researcher"]
)
def search_web(
    query: Annotated[str, "The search query"],
    num_results: Annotated[int, "Number of results"] = 5
) -> str:
    # Implementation
    pass
```

2. Tool registry:
```python
class ToolRegistry:
    _tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool_def: ToolDefinition):
        pass

    @classmethod
    def get_tools_for_agent(cls, agent_name: str) -> List[ToolDefinition]:
        pass

    @classmethod
    def get_tool_schemas(cls, agent_name: str) -> List[Dict]:
        """Get OpenAI function calling format schemas"""
        pass

    @classmethod
    def execute_tool(cls, name: str, **kwargs) -> Any:
        pass
```

3. Built-in tools to implement:
   - web_search
   - file_read
   - file_write
   - code_execute (sandboxed)
   - http_request
```

---

# Part 4: LLM Analysis & Ranking

## 4.1 LLM Comparison for Jarvis Agent System

| Model | Provider | Strengths | Weaknesses | Best For | Cost (per 1M tokens) |
|-------|----------|-----------|------------|----------|---------------------|
| **GPT-4o** | OpenAI | Balanced performance, reliable tool use, multimodal | Expensive, rate limits | Manager role, complex reasoning | $2.50 / $10.00 |
| **Claude 3.5 Sonnet** | Anthropic | Excellent coding (49% SWE-bench), long context | Less tool use docs | Employee (coding), reviews | $3.00 / $15.00 |
| **DeepSeek V3** | DeepSeek | Outstanding coding, cost-effective MoE, 671B params | Chinese company concerns | Employee (coding), high-volume | $0.27 / $1.10 |
| **Llama 3.1 70B** | Meta (Local) | Free, private, good quality | Needs GPU hardware | Self-hosted operations | Free (compute only) |
| **Qwen 2.5 72B** | Alibaba (Local) | Competitive benchmarks, MoE efficient | Less English training | Local alternative | Free (compute only) |
| **GPT-4o-mini** | OpenAI | Very cheap, fast, good enough | Limited complex reasoning | Supervisor, simple tasks | $0.15 / $0.60 |

## 4.2 Recommended Jarvis Configuration

### Hybrid Strategy (Recommended)

```yaml
# config/llm_config.yaml
routing_strategy: hybrid

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    models:
      - gpt-4o
      - gpt-4o-mini

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    models:
      - claude-3-5-sonnet-20241022

  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    models:
      - deepseek-chat

  ollama:
    host: http://localhost:11434
    models:
      - llama3.1:70b
      - qwen2.5:72b

role_assignments:
  manager:
    primary: gpt-4o
    fallback: claude-3-5-sonnet

  supervisor:
    primary: gpt-4o-mini
    fallback: deepseek-chat

  employee:
    coding:
      primary: claude-3-5-sonnet
      fallback: deepseek-chat
    general:
      primary: gpt-4o-mini
      fallback: llama3.1:70b

cost_optimization:
  prefer_local_for:
    - simple_queries
    - code_formatting
    - test_generation

  use_premium_for:
    - architecture_decisions
    - security_reviews
    - final_code_review
```

## 4.3 LLM Ranking for Jarvis Roles

### Rank 1: Claude 3.5 Sonnet (Employee - Coding)
- **Score:** 9.2/10
- **Rationale:** 49% SWE-bench score, excellent at generating clean code
- **Best for:** Code generation, code review, debugging
- **Cost efficiency:** High quality per dollar for coding tasks

### Rank 2: GPT-4o (Manager Role)
- **Score:** 9.0/10
- **Rationale:** Best reasoning, reliable JSON output, excellent planning
- **Best for:** Planning, complex decisions, multi-step reasoning
- **Cost efficiency:** Worth premium for critical decisions

### Rank 3: DeepSeek V3 (Cost-Effective Coding)
- **Score:** 8.7/10
- **Rationale:** Near GPT-4 quality at 1/10th the cost
- **Best for:** High-volume coding tasks, bulk operations
- **Cost efficiency:** Best cost/quality ratio

### Rank 4: Llama 3.1 70B (Self-Hosted)
- **Score:** 8.3/10
- **Rationale:** Free, private, good quality for most tasks
- **Best for:** Privacy-sensitive work, offline operation
- **Cost efficiency:** Best for high-volume if you have GPUs

### Rank 5: GPT-4o-mini (Supervisor/Simple Tasks)
- **Score:** 8.0/10
- **Rationale:** Extremely cheap, fast, good for structured tasks
- **Best for:** Classification, formatting, simple generation
- **Cost efficiency:** Best for high-volume simple tasks

---

# Part 5: Implementation Timeline

## 5.1 Complete Roadmap

```
Week 1-2: Foundation
├── Day 1-3: YAML Configuration System
├── Day 4-8: Flow Engine with Router
└── Day 9-10: Clarification Loop System

Week 3-4: Orchestration
├── Day 11-14: Pattern-Based Orchestration
├── Day 15-17: Human-in-the-Loop Controller
└── Day 18-20: Pattern Selection Intelligence

Week 5-6: Memory & Intelligence
├── Day 21-25: Multi-Type Memory System
└── Day 26-30: Memory-Enhanced Prompts

Week 7-8: LLM & Tools
├── Day 31-34: Enhanced Model Router
├── Day 35-37: Tool Registration System
└── Day 38-40: Provider Integrations

Week 9-10: Polish & Testing
├── Day 41-45: Integration Testing
├── Day 46-48: Performance Optimization
└── Day 49-50: Documentation
```

## 5.2 Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Task completion rate | ~60% | 90%+ | Manager approval rate |
| User clarification needed | 0% | 80%+ | Questions before complex tasks |
| Memory retention | 0 sessions | 30+ days | LTM persistence |
| Cost per task | ~$0.10 | ~$0.05 | With local LLM routing |
| Time to first response | N/A | <2s | Clarification question |

---

# Part 6: Risk Analysis

## 6.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Flow engine complexity | Medium | High | Start with simple patterns, iterate |
| Memory system overhead | Medium | Medium | Lazy loading, async operations |
| Local LLM quality | Low | Medium | Maintain cloud fallback |
| Pattern selection errors | Medium | Medium | Allow manual override |

## 6.2 Competitive Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CrewAI adds cost tracking | High | Medium | Focus on UX differentiators |
| AG2 improves UX | Medium | Medium | Build community, documentation |
| New entrant | Medium | High | Speed to market, unique features |

---

# Appendix A: File Structure for Jarvis 2.0

```
agent/
├── config/
│   ├── agents.yaml              # NEW: Agent definitions
│   ├── tasks.yaml               # NEW: Task definitions
│   └── llm_config.yaml          # NEW: LLM provider config
├── flow/
│   ├── __init__.py
│   ├── decorators.py            # NEW: @start, @listen, @router
│   ├── flow_engine.py           # NEW: Flow execution engine
│   └── state.py                 # NEW: Pydantic state models
├── patterns/
│   ├── __init__.py
│   ├── base.py                  # NEW: Pattern base class
│   ├── sequential.py            # NEW
│   ├── hierarchical.py          # NEW (existing behavior)
│   ├── auto_select.py           # NEW
│   ├── round_robin.py           # NEW
│   └── manual.py                # NEW
├── memory/
│   ├── __init__.py
│   ├── short_term.py            # NEW: STM with RAG
│   ├── long_term.py             # NEW: SQLite persistence
│   ├── entity.py                # NEW: Entity tracking
│   ├── contextual.py            # NEW: Combined retrieval
│   └── storage/
│       ├── chroma.py            # NEW
│       ├── sqlite.py            # NEW
│       └── qdrant.py            # NEW
├── tools/
│   ├── __init__.py
│   ├── registry.py              # NEW: Tool registration
│   ├── web_search.py            # NEW
│   ├── code_executor.py         # NEW
│   └── http_client.py           # NEW
├── providers/
│   ├── __init__.py
│   ├── base.py                  # NEW: Provider ABC
│   ├── openai.py                # ENHANCED
│   ├── anthropic.py             # NEW
│   ├── deepseek.py              # NEW
│   ├── ollama.py                # NEW
│   └── qwen.py                  # NEW
├── human_proxy.py               # NEW: Human-in-the-loop
├── config_loader.py             # NEW: YAML config loader
├── pattern_selector.py          # NEW: Auto pattern selection
├── jarvis_chat.py               # ENHANCED: Clarification loop
├── orchestrator.py              # ENHANCED: Pattern support
└── llm.py                       # ENHANCED: Multi-provider
```

---

*Document Version: 1.0*
*Last Updated: November 22, 2025*
*Author: Claude Code Analysis*
