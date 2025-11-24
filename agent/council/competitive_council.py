"""
Council System - Competitive Parallel Council

Implements the competitive parallel execution model where multiple
supervisor+employee sets work on the SAME task simultaneously,
then vote on whose answer is best.

Architecture:
    JARVIS (Manager)
        │
        ├── Set 1: Supervisor A + Employee A
        ├── Set 2: Supervisor B + Employee B
        └── Set 3: Supervisor C + Employee C
                │
                ▼
        All vote on "whose answer is best?"
                │
                ▼ (every 10 rounds)
        3 lowest performers → 💀 Graveyard
        + Spawn 3 new AIs

Example:
    council = CompetitiveCouncil()
    await council.initialize(llm_func)

    # Process task with parallel execution
    result = await council.process_task("Build a unicorn website")
    # All sets work on it, then vote on best answer
"""

import asyncio
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import json

from .models import (
    Councillor, CouncillorStatus, Specialization,
    Vote, VotingSession, VoteType,
    TaskComplexity
)
from .voting import VotingManager
from .happiness import HappinessManager, HappinessEvent
from .factory import CouncillorFactory, FactoryConfig
from .graveyard import Graveyard, GraveyardRecord


@dataclass
class AgentSet:
    """A supervisor + employee pair that works as a team"""
    id: str
    supervisor: Councillor
    employee: Councillor
    set_name: str = ""

    def __post_init__(self):
        if not self.set_name:
            self.set_name = f"Team {self.supervisor.name.split()[0]}"

    @property
    def members(self) -> List[Councillor]:
        return [self.supervisor, self.employee]

    @property
    def is_active(self) -> bool:
        return (
            self.supervisor.status in [CouncillorStatus.ACTIVE, CouncillorStatus.PROBATION] and
            self.employee.status in [CouncillorStatus.ACTIVE, CouncillorStatus.PROBATION]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "set_name": self.set_name,
            "supervisor": self.supervisor.to_dict(),
            "employee": self.employee.to_dict(),
            "is_active": self.is_active,
        }


@dataclass
class CompetitiveResult:
    """Result from a competitive round"""
    task_id: str
    task_description: str
    answers: Dict[str, str]  # set_id -> answer
    votes: List[Vote]
    winner_set_id: str
    winner_answer: str
    vote_session: VotingSession
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_description": self.task_description[:100],
            "answers": {k: v[:200] + "..." if len(v) > 200 else v for k, v in self.answers.items()},
            "winner_set_id": self.winner_set_id,
            "vote_session": self.vote_session.to_dict() if self.vote_session else None,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CompetitiveConfig:
    """Configuration for competitive council"""
    num_sets: int = 3                    # Number of parallel supervisor+employee sets
    rounds_before_evaluation: int = 10   # Rounds before graveyard evaluation
    num_to_terminate: int = 3            # Number of lowest performers to terminate
    db_path: str = "data/council/competitive.db"
    graveyard_path: str = "data/council/graveyard.db"

    # Supervisor templates
    supervisor_templates: List[str] = field(default_factory=lambda: ["architect", "reviewer", "coder"])
    # Employee templates
    employee_templates: List[str] = field(default_factory=lambda: ["coder", "coder", "coder"])


class CompetitiveCouncil:
    """
    Competitive Parallel Council

    Multiple supervisor+employee sets work on the SAME task in parallel.
    All agents then vote on whose answer is the BEST.
    After N rounds, the lowest performers are sent to the graveyard.

    This creates healthy competition and ensures quality through
    democratic selection of the best work.
    """

    def __init__(self, config: Optional[CompetitiveConfig] = None):
        self.config = config or CompetitiveConfig()

        # Core components
        self.sets: List[AgentSet] = []
        self.voting_manager = VotingManager()
        self.happiness_manager = HappinessManager()
        self.factory = CouncillorFactory(FactoryConfig(
            min_councillors=self.config.num_sets * 2,
            max_councillors=self.config.num_sets * 2 + 4,
        ))
        self.graveyard = Graveyard(self.config.graveyard_path)

        # State tracking
        self.rounds_completed: int = 0
        self.round_history: List[CompetitiveResult] = []
        self._initialized: bool = False
        self._llm_func: Optional[Callable] = None

        # Database
        self.db_path = Path(self.config.db_path)
        self._conn: Optional[sqlite3.Connection] = None

    async def initialize(
        self,
        llm_func: Optional[Callable] = None,
    ):
        """
        Initialize the competitive council with agent sets.

        Args:
            llm_func: LLM function for agent execution
        """
        self._llm_func = llm_func

        # Initialize database
        self._init_database()

        # Initialize graveyard
        self.graveyard.initialize()

        # Set up factory
        if llm_func:
            self.factory.set_execute_func(self._create_execute_func(llm_func))

        # Load or create agent sets
        existing_sets = self._load_sets_from_db()
        if existing_sets and len(existing_sets) >= self.config.num_sets:
            self.sets = existing_sets[:self.config.num_sets]
            print(f"[CompetitiveCouncil] Loaded {len(self.sets)} existing sets from database")
        else:
            # Create new sets
            self.sets = self._create_agent_sets()
            self._save_sets_to_db()
            print(f"[CompetitiveCouncil] Created {len(self.sets)} new agent sets")

        # Load round count
        self.rounds_completed = self._load_round_count()

        self._initialized = True
        print(f"[CompetitiveCouncil] Initialized with {len(self.sets)} sets, {self.rounds_completed} rounds completed")

    def _init_database(self):
        """Initialize SQLite database for councillor persistence"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

        # Create tables
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS councillors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                set_id TEXT,
                specializations TEXT,
                status TEXT,
                happiness REAL,
                base_vote_weight REAL,
                metrics TEXT,
                metadata TEXT,
                created_at TEXT
            )
        """)

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_sets (
                id TEXT PRIMARY KEY,
                set_name TEXT,
                supervisor_id TEXT,
                employee_id TEXT,
                created_at TEXT
            )
        """)

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS council_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self._conn.commit()

    def _create_execute_func(self, llm_func: Callable) -> Callable:
        """Create execution function for councillors"""
        async def execute(task: str, context: Dict[str, Any]) -> str:
            name = context.get("councillor_name", "Agent")
            role = context.get("role", "assistant")
            specializations = context.get("specializations", [])

            prompt = f"""You are {name}, a {role} specialist in {', '.join(specializations)}.

Task: {task}

Provide a comprehensive, high-quality response. Your answer will be judged against other teams.
Be thorough, creative, and demonstrate your expertise."""

            return await llm_func(prompt)

        return execute

    def _create_agent_sets(self) -> List[AgentSet]:
        """Create the initial agent sets"""
        sets = []

        for i in range(self.config.num_sets):
            sup_template = self.config.supervisor_templates[i % len(self.config.supervisor_templates)]
            emp_template = self.config.employee_templates[i % len(self.config.employee_templates)]

            supervisor = self.factory.spawn(sup_template, reason="initial_competitive_team")
            supervisor.metadata["role"] = "supervisor"
            supervisor.base_vote_weight = 1.2  # Supervisors have slightly higher vote weight

            employee = self.factory.spawn(emp_template, reason="initial_competitive_team")
            employee.metadata["role"] = "employee"

            agent_set = AgentSet(
                id=f"set_{i+1}",
                supervisor=supervisor,
                employee=employee,
                set_name=f"Team {supervisor.name.split()[0]}"
            )
            sets.append(agent_set)

        return sets

    def _save_sets_to_db(self):
        """Save agent sets to database"""
        if not self._conn:
            return

        for agent_set in self.sets:
            # Save supervisor
            self._save_councillor(agent_set.supervisor, agent_set.id, "supervisor")
            # Save employee
            self._save_councillor(agent_set.employee, agent_set.id, "employee")
            # Save set
            self._conn.execute("""
                INSERT OR REPLACE INTO agent_sets (id, set_name, supervisor_id, employee_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_set.id, agent_set.set_name, agent_set.supervisor.id,
                  agent_set.employee.id, datetime.now().isoformat()))

        self._conn.commit()

    def _save_councillor(self, councillor: Councillor, set_id: str, role: str):
        """Save a councillor to database"""
        metrics_dict = {
            "tasks_completed": councillor.metrics.tasks_completed,
            "tasks_failed": councillor.metrics.tasks_failed,
            "competitive_rounds": councillor.metrics.competitive_rounds,
            "competitive_wins": councillor.metrics.competitive_wins,
            "competitive_losses": councillor.metrics.competitive_losses,
            "round_history": councillor.metrics.round_history,
            "votes_won": councillor.metrics.votes_won,
            "votes_lost": councillor.metrics.votes_lost,
        }

        self._conn.execute("""
            INSERT OR REPLACE INTO councillors
            (id, name, role, set_id, specializations, status, happiness,
             base_vote_weight, metrics, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            councillor.id,
            councillor.name,
            role,
            set_id,
            json.dumps([s.value for s in councillor.specializations]),
            councillor.status.value,
            councillor.happiness,
            councillor.base_vote_weight,
            json.dumps(metrics_dict),
            json.dumps(councillor.metadata),
            councillor.created_at.isoformat()
        ))

    def _load_sets_from_db(self) -> List[AgentSet]:
        """Load agent sets from database"""
        if not self._conn:
            return []

        sets = []
        cursor = self._conn.execute("SELECT * FROM agent_sets")

        for row in cursor.fetchall():
            supervisor = self._load_councillor(row["supervisor_id"])
            employee = self._load_councillor(row["employee_id"])

            if supervisor and employee:
                sets.append(AgentSet(
                    id=row["id"],
                    supervisor=supervisor,
                    employee=employee,
                    set_name=row["set_name"]
                ))

        return sets

    def _load_councillor(self, councillor_id: str) -> Optional[Councillor]:
        """Load a councillor from database"""
        cursor = self._conn.execute(
            "SELECT * FROM councillors WHERE id = ?", (councillor_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        metrics_dict = json.loads(row["metrics"])
        from .models import PerformanceMetrics

        councillor = Councillor(
            id=row["id"],
            name=row["name"],
            specializations=[Specialization(s) for s in json.loads(row["specializations"])],
            status=CouncillorStatus(row["status"]),
            happiness=row["happiness"],
            base_vote_weight=row["base_vote_weight"],
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

        # Restore metrics
        councillor.metrics.tasks_completed = metrics_dict.get("tasks_completed", 0)
        councillor.metrics.tasks_failed = metrics_dict.get("tasks_failed", 0)
        councillor.metrics.competitive_rounds = metrics_dict.get("competitive_rounds", 0)
        councillor.metrics.competitive_wins = metrics_dict.get("competitive_wins", 0)
        councillor.metrics.competitive_losses = metrics_dict.get("competitive_losses", 0)
        councillor.metrics.round_history = metrics_dict.get("round_history", [])
        councillor.metrics.votes_won = metrics_dict.get("votes_won", 0)
        councillor.metrics.votes_lost = metrics_dict.get("votes_lost", 0)

        # Restore execution function
        if self._llm_func:
            councillor._execute_func = self._create_execute_func(self._llm_func)

        return councillor

    def _load_round_count(self) -> int:
        """Load round count from database"""
        cursor = self._conn.execute(
            "SELECT value FROM council_state WHERE key = 'rounds_completed'"
        )
        row = cursor.fetchone()
        return int(row["value"]) if row else 0

    def _save_round_count(self):
        """Save round count to database"""
        self._conn.execute("""
            INSERT OR REPLACE INTO council_state (key, value)
            VALUES ('rounds_completed', ?)
        """, (str(self.rounds_completed),))
        self._conn.commit()

    async def process_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CompetitiveResult:
        """
        Process a task through competitive parallel execution.

        Flow:
        1. JARVIS creates plan/phases (handled externally)
        2. All 3 sets work on the SAME task in parallel
        3. All agents vote on whose answer is BEST
        4. Winner's answer is selected
        5. Update metrics and check for graveyard

        Args:
            task_description: The task to process
            context: Optional additional context

        Returns:
            CompetitiveResult with winning answer
        """
        if not self._initialized:
            await self.initialize()

        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n[CompetitiveCouncil] Starting competitive round for: {task_description[:50]}...")

        # Step 1: Parallel execution - all sets work on the same task
        answers = await self._execute_parallel(task_description, context or {})
        print(f"[CompetitiveCouncil] Received {len(answers)} answers from teams")

        # Step 2: Vote on best answer
        winner_set_id, vote_session = await self._vote_best_answer(
            task_description, answers
        )
        print(f"[CompetitiveCouncil] Winner: {winner_set_id}")

        # Step 3: Update metrics
        self._update_metrics_after_round(winner_set_id, task_id)

        # Step 4: Record result
        result = CompetitiveResult(
            task_id=task_id,
            task_description=task_description,
            answers=answers,
            votes=vote_session.votes,
            winner_set_id=winner_set_id,
            winner_answer=answers.get(winner_set_id, ""),
            vote_session=vote_session,
        )
        self.round_history.append(result)
        self.rounds_completed += 1
        self._save_round_count()

        # Step 5: Check for graveyard evaluation
        if self.rounds_completed % self.config.rounds_before_evaluation == 0:
            await self._graveyard_evaluation()

        # Save updated state
        self._save_sets_to_db()

        return result

    async def _execute_parallel(
        self,
        task_description: str,
        context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Execute task in parallel across all sets"""
        answers = {}

        async def execute_set(agent_set: AgentSet) -> Tuple[str, str]:
            """Execute task for one set (supervisor + employee collaboration)"""
            # Supervisor plans
            sup_context = {
                "councillor_name": agent_set.supervisor.name,
                "role": "supervisor",
                "specializations": [s.value for s in agent_set.supervisor.specializations],
                **context
            }
            supervisor_plan = await agent_set.supervisor.execute(
                f"As supervisor, create a plan for: {task_description}",
                sup_context
            )

            # Employee executes based on plan
            emp_context = {
                "councillor_name": agent_set.employee.name,
                "role": "employee",
                "specializations": [s.value for s in agent_set.employee.specializations],
                "supervisor_plan": supervisor_plan,
                **context
            }
            employee_result = await agent_set.employee.execute(
                f"""Execute this task following the supervisor's plan:

Task: {task_description}

Supervisor's Plan:
{supervisor_plan}

Provide a complete, high-quality implementation.""",
                emp_context
            )

            # Combined answer
            combined = f"""## {agent_set.set_name}'s Answer

### Supervisor's Plan ({agent_set.supervisor.name}):
{supervisor_plan}

### Implementation ({agent_set.employee.name}):
{employee_result}"""

            return agent_set.id, combined

        # Execute all sets in parallel
        tasks = [execute_set(agent_set) for agent_set in self.sets if agent_set.is_active]
        results = await asyncio.gather(*tasks)

        for set_id, answer in results:
            answers[set_id] = answer

        return answers

    async def _vote_best_answer(
        self,
        task_description: str,
        answers: Dict[str, str]
    ) -> Tuple[str, VotingSession]:
        """All agents vote on whose answer is best"""

        # Create voting session
        session = self.voting_manager.create_session(
            vote_type=VoteType.BEST_ANSWER,
            question=f"Which team provided the BEST answer for: {task_description}",
            options=list(answers.keys()),
            metadata={"answers": {k: v[:500] for k, v in answers.items()}}
        )

        # All councillors vote (can't vote for own team)
        all_councillors = []
        for agent_set in self.sets:
            all_councillors.extend(agent_set.members)

        for councillor in all_councillors:
            # Find which set this councillor belongs to
            councillor_set_id = None
            for agent_set in self.sets:
                if councillor.id in [agent_set.supervisor.id, agent_set.employee.id]:
                    councillor_set_id = agent_set.id
                    break

            # Generate vote (excluding own team)
            vote = await self._generate_best_answer_vote(
                session, councillor, answers, exclude_set=councillor_set_id
            )
            session.add_vote(vote)

        # Close session and get winner
        winner = self.voting_manager.close_session(session.id)

        return winner, session

    async def _generate_best_answer_vote(
        self,
        session: VotingSession,
        councillor: Councillor,
        answers: Dict[str, str],
        exclude_set: Optional[str] = None
    ) -> Vote:
        """Generate a vote for best answer"""
        # Available options (excluding own team)
        options = [opt for opt in session.options if opt != exclude_set]

        if not options:
            options = session.options  # Fallback if only one team

        # Simple heuristic: vote based on answer length and keywords
        # In production, this could use LLM evaluation
        scores = {}
        for set_id in options:
            answer = answers.get(set_id, "")
            score = len(answer) / 100  # Length score
            # Bonus for structure
            if "##" in answer:
                score += 5
            if "```" in answer:
                score += 3
            scores[set_id] = score

        # Pick highest scoring
        best = max(scores, key=scores.get) if scores else options[0]

        # Confidence based on score difference
        if len(scores) > 1:
            sorted_scores = sorted(scores.values(), reverse=True)
            confidence = min(0.95, 0.5 + (sorted_scores[0] - sorted_scores[1]) / 20)
        else:
            confidence = 0.7

        return Vote(
            councillor_id=councillor.id,
            councillor_name=councillor.name,
            choice=best,
            confidence=confidence,
            weight=councillor.vote_weight,
            reasoning=f"Selected based on quality assessment"
        )

    def _update_metrics_after_round(self, winner_set_id: str, task_id: str):
        """Update all councillor metrics after a round"""
        for agent_set in self.sets:
            won = agent_set.id == winner_set_id

            # Update both supervisor and employee
            for councillor in agent_set.members:
                councillor.metrics.record_competitive_round(
                    won=won,
                    task_id=task_id,
                    score=1.0 if won else 0.0
                )

                # Happiness adjustment
                if won:
                    councillor.adjust_happiness(5)  # Win bonus
                    councillor.metrics.record_task_success(quality=0.9)
                else:
                    councillor.adjust_happiness(-2)  # Small loss penalty
                    # Not a failure, just not the winner

            if won:
                print(f"[CompetitiveCouncil] 🏆 {agent_set.set_name} wins this round!")

    async def _graveyard_evaluation(self):
        """
        Evaluate all councillors and send lowest performers to graveyard.

        After every N rounds (default 10), the 3 lowest performers
        are permanently terminated and replaced with fresh AIs.
        """
        print(f"\n[CompetitiveCouncil] ⚰️ GRAVEYARD EVALUATION after {self.rounds_completed} rounds")

        # Collect all councillors with their competitive scores
        all_councillors = []
        for agent_set in self.sets:
            for councillor in agent_set.members:
                all_councillors.append({
                    "councillor": councillor,
                    "set": agent_set,
                    "score": councillor.metrics.competitive_score
                })

        # Sort by score (lowest first = worst performers)
        all_councillors.sort(key=lambda x: x["score"])

        # Get the N lowest performers
        to_terminate = all_councillors[:self.config.num_to_terminate]

        terminated_count = 0
        affected_sets = set()

        for item in to_terminate:
            councillor = item["councillor"]
            agent_set = item["set"]

            print(f"[Graveyard] 💀 Terminating {councillor.name} (score: {item['score']:.1f})")

            # Send to graveyard
            self.graveyard.terminate(
                councillor,
                reason=f"Lowest performer after {self.rounds_completed} rounds (score: {item['score']:.1f})",
                vote_history=councillor.metrics.round_history
            )

            # Delete from database
            self._delete_councillor_from_db(councillor.id)

            affected_sets.add(agent_set.id)
            terminated_count += 1

        # Spawn replacements for affected sets
        await self._respawn_terminated(affected_sets)

        print(f"[CompetitiveCouncil] Terminated {terminated_count}, respawned replacements")

        # Apply team event for remaining councillors
        remaining = [c["councillor"] for c in all_councillors[self.config.num_to_terminate:]]
        self.happiness_manager.apply_team_event(remaining, HappinessEvent.COLLEAGUE_FIRED)

    def _delete_councillor_from_db(self, councillor_id: str):
        """Completely delete a councillor from the database"""
        if self._conn:
            self._conn.execute("DELETE FROM councillors WHERE id = ?", (councillor_id,))
            self._conn.commit()

    async def _respawn_terminated(self, affected_set_ids: set):
        """Respawn councillors for affected sets"""
        for agent_set in self.sets:
            if agent_set.id not in affected_set_ids:
                continue

            # Check supervisor
            if agent_set.supervisor.status == CouncillorStatus.FIRED:
                template_idx = self.sets.index(agent_set) % len(self.config.supervisor_templates)
                template = self.config.supervisor_templates[template_idx]
                new_sup = self.factory.spawn(template, reason="graveyard_replacement")
                new_sup.metadata["role"] = "supervisor"
                new_sup.base_vote_weight = 1.2
                agent_set.supervisor = new_sup
                print(f"[CompetitiveCouncil] Spawned new supervisor: {new_sup.name}")

            # Check employee
            if agent_set.employee.status == CouncillorStatus.FIRED:
                template_idx = self.sets.index(agent_set) % len(self.config.employee_templates)
                template = self.config.employee_templates[template_idx]
                new_emp = self.factory.spawn(template, reason="graveyard_replacement")
                new_emp.metadata["role"] = "employee"
                agent_set.employee = new_emp
                print(f"[CompetitiveCouncil] Spawned new employee: {new_emp.name}")

        # Save updated sets
        self._save_sets_to_db()

    def get_status(self) -> Dict[str, Any]:
        """Get current council status"""
        return {
            "rounds_completed": self.rounds_completed,
            "rounds_until_evaluation": self.config.rounds_before_evaluation - (
                self.rounds_completed % self.config.rounds_before_evaluation
            ),
            "num_sets": len(self.sets),
            "sets": [s.to_dict() for s in self.sets],
            "graveyard_deaths": self.graveyard.get_death_count(),
        }

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Get councillor leaderboard by competitive score"""
        all_councillors = []
        for agent_set in self.sets:
            for councillor in agent_set.members:
                all_councillors.append({
                    "name": councillor.name,
                    "set": agent_set.set_name,
                    "role": councillor.metadata.get("role", "unknown"),
                    "competitive_score": councillor.metrics.competitive_score,
                    "win_rate": councillor.metrics.competitive_win_rate,
                    "rounds": councillor.metrics.competitive_rounds,
                    "wins": councillor.metrics.competitive_wins,
                    "happiness": councillor.happiness,
                })

        # Sort by score descending
        all_councillors.sort(key=lambda x: -x["competitive_score"])

        # Add ranks
        for i, c in enumerate(all_councillors):
            c["rank"] = i + 1

        return all_councillors

    def close(self):
        """Close database connections"""
        if self._conn:
            self._conn.close()
            self._conn = None
        self.graveyard.close()


# Convenience function
async def create_competitive_council(
    llm_func: Optional[Callable] = None,
    config: Optional[CompetitiveConfig] = None
) -> CompetitiveCouncil:
    """
    Create and initialize a competitive council.

    Args:
        llm_func: LLM function for agent execution
        config: Optional configuration

    Returns:
        Initialized CompetitiveCouncil
    """
    council = CompetitiveCouncil(config)
    await council.initialize(llm_func)
    return council
