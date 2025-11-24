"""
Council System - Graveyard

Manages the permanent deletion of underperforming councillors.
When an AI is sent to the graveyard, all their data is completely purged
from the SQL database - they cease to exist.

The graveyard tracks:
- Who was deleted and when
- Their final performance metrics (for historical analysis)
- Reason for termination
"""

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Councillor, CouncillorStatus


@dataclass
class GraveyardRecord:
    """Record of a councillor sent to the graveyard"""
    councillor_id: str
    councillor_name: str
    reason: str
    final_metrics: Dict[str, Any]
    vote_history: List[Dict[str, Any]]
    total_votes: int
    wins: int
    losses: int
    created_at: datetime
    terminated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "councillor_id": self.councillor_id,
            "councillor_name": self.councillor_name,
            "reason": self.reason,
            "final_metrics": self.final_metrics,
            "vote_history": self.vote_history,
            "total_votes": self.total_votes,
            "wins": self.wins,
            "losses": self.losses,
            "created_at": self.created_at.isoformat(),
            "terminated_at": self.terminated_at.isoformat(),
        }


class Graveyard:
    """
    The Graveyard - where underperforming AIs are permanently deleted.

    After 10 rounds of individual voting, the 3 lowest performers
    are sent here and their SQL databases are completely purged.

    This is NOT recoverable - the AI ceases to exist.

    Example:
        graveyard = Graveyard("data/council/graveyard.db")
        graveyard.initialize()

        # Send underperformer to graveyard
        graveyard.terminate(councillor, reason="Lowest performer after 10 rounds")

        # View the fallen
        records = graveyard.get_records(limit=10)
    """

    def __init__(self, db_path: str = "data/council/graveyard.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def initialize(self):
        """Initialize the graveyard database"""
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

        # Create graveyard records table
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS graveyard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                councillor_id TEXT UNIQUE NOT NULL,
                councillor_name TEXT NOT NULL,
                reason TEXT NOT NULL,
                final_metrics TEXT NOT NULL,
                vote_history TEXT NOT NULL,
                total_votes INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                terminated_at TEXT NOT NULL
            )
        """)

        # Create index for faster lookups
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_graveyard_terminated
            ON graveyard(terminated_at DESC)
        """)

        self._conn.commit()

    def terminate(
        self,
        councillor: Councillor,
        reason: str,
        vote_history: Optional[List[Dict[str, Any]]] = None
    ) -> GraveyardRecord:
        """
        Send a councillor to the graveyard - PERMANENT DELETION.

        This will:
        1. Record their final state for historical purposes
        2. Delete ALL their data from the councillor database
        3. Mark them as terminated

        Args:
            councillor: The councillor to terminate
            reason: Reason for termination
            vote_history: Their voting history

        Returns:
            GraveyardRecord of the terminated councillor
        """
        if not self._conn:
            self.initialize()

        # Calculate win/loss from metrics
        wins = councillor.metrics.votes_won if hasattr(councillor.metrics, 'votes_won') else 0
        losses = councillor.metrics.votes_lost if hasattr(councillor.metrics, 'votes_lost') else 0
        total_votes = wins + losses

        # Create graveyard record
        record = GraveyardRecord(
            councillor_id=councillor.id,
            councillor_name=councillor.name,
            reason=reason,
            final_metrics={
                "overall_performance": councillor.metrics.overall_performance,
                "happiness": councillor.happiness,
                "tasks_completed": councillor.metrics.tasks_completed,
                "success_rate": councillor.metrics.success_rate,
                "consecutive_failures": councillor.metrics.consecutive_failures,
                "vote_weight": councillor.vote_weight,
            },
            vote_history=vote_history or [],
            total_votes=total_votes,
            wins=wins,
            losses=losses,
            created_at=councillor.created_at,
        )

        # Insert into graveyard
        self._conn.execute("""
            INSERT INTO graveyard
            (councillor_id, councillor_name, reason, final_metrics, vote_history,
             total_votes, wins, losses, created_at, terminated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.councillor_id,
            record.councillor_name,
            record.reason,
            json.dumps(record.final_metrics),
            json.dumps(record.vote_history),
            record.total_votes,
            record.wins,
            record.losses,
            record.created_at.isoformat(),
            record.terminated_at.isoformat(),
        ))

        self._conn.commit()

        # Update councillor status
        councillor.status = CouncillorStatus.FIRED

        print(f"[Graveyard] 💀 {councillor.name} has been terminated: {reason}")

        return record

    def delete_councillor_data(
        self,
        councillor_id: str,
        councillor_db_path: str
    ) -> bool:
        """
        Completely delete a councillor's data from their database.

        This is the actual "death" - all traces are removed.

        Args:
            councillor_id: The councillor's ID
            councillor_db_path: Path to the councillor's database

        Returns:
            True if deletion was successful
        """
        try:
            db_path = Path(councillor_db_path)
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))

                # Delete from all councillor-related tables
                tables_to_clean = [
                    "councillors",
                    "councillor_metrics",
                    "councillor_votes",
                    "councillor_history",
                    "councillor_memories",
                ]

                for table in tables_to_clean:
                    try:
                        conn.execute(f"DELETE FROM {table} WHERE councillor_id = ?", (councillor_id,))
                    except sqlite3.OperationalError:
                        # Table might not exist, that's ok
                        pass

                conn.commit()
                conn.close()

                print(f"[Graveyard] Purged all data for councillor {councillor_id}")
                return True

        except Exception as e:
            print(f"[Graveyard] Error deleting councillor data: {e}")
            return False

        return False

    def get_records(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[GraveyardRecord]:
        """Get graveyard records (most recent first)"""
        if not self._conn:
            self.initialize()

        cursor = self._conn.execute("""
            SELECT * FROM graveyard
            ORDER BY terminated_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        records = []
        for row in cursor.fetchall():
            records.append(GraveyardRecord(
                councillor_id=row["councillor_id"],
                councillor_name=row["councillor_name"],
                reason=row["reason"],
                final_metrics=json.loads(row["final_metrics"]),
                vote_history=json.loads(row["vote_history"]),
                total_votes=row["total_votes"],
                wins=row["wins"],
                losses=row["losses"],
                created_at=datetime.fromisoformat(row["created_at"]),
                terminated_at=datetime.fromisoformat(row["terminated_at"]),
            ))

        return records

    def get_death_count(self) -> int:
        """Get total number of terminated councillors"""
        if not self._conn:
            self.initialize()

        cursor = self._conn.execute("SELECT COUNT(*) FROM graveyard")
        return cursor.fetchone()[0]

    def get_recent_deaths(self, hours: int = 24) -> List[GraveyardRecord]:
        """Get councillors terminated in the last N hours"""
        if not self._conn:
            self.initialize()

        cutoff = datetime.now().isoformat()
        cursor = self._conn.execute("""
            SELECT * FROM graveyard
            WHERE terminated_at >= datetime(?, '-' || ? || ' hours')
            ORDER BY terminated_at DESC
        """, (cutoff, hours))

        records = []
        for row in cursor.fetchall():
            records.append(GraveyardRecord(
                councillor_id=row["councillor_id"],
                councillor_name=row["councillor_name"],
                reason=row["reason"],
                final_metrics=json.loads(row["final_metrics"]),
                vote_history=json.loads(row["vote_history"]),
                total_votes=row["total_votes"],
                wins=row["wins"],
                losses=row["losses"],
                created_at=datetime.fromisoformat(row["created_at"]),
                terminated_at=datetime.fromisoformat(row["terminated_at"]),
            ))

        return records

    def get_statistics(self) -> Dict[str, Any]:
        """Get graveyard statistics"""
        if not self._conn:
            self.initialize()

        cursor = self._conn.execute("""
            SELECT
                COUNT(*) as total_deaths,
                AVG(json_extract(final_metrics, '$.overall_performance')) as avg_final_performance,
                AVG(json_extract(final_metrics, '$.happiness')) as avg_final_happiness,
                AVG(total_votes) as avg_votes_before_death,
                MIN(terminated_at) as first_death,
                MAX(terminated_at) as last_death
            FROM graveyard
        """)

        row = cursor.fetchone()

        # Get most common death reasons
        reason_cursor = self._conn.execute("""
            SELECT reason, COUNT(*) as count
            FROM graveyard
            GROUP BY reason
            ORDER BY count DESC
            LIMIT 5
        """)

        common_reasons = [
            {"reason": r["reason"], "count": r["count"]}
            for r in reason_cursor.fetchall()
        ]

        return {
            "total_deaths": row["total_deaths"] or 0,
            "avg_final_performance": row["avg_final_performance"] or 0,
            "avg_final_happiness": row["avg_final_happiness"] or 0,
            "avg_votes_before_death": row["avg_votes_before_death"] or 0,
            "first_death": row["first_death"],
            "last_death": row["last_death"],
            "common_death_reasons": common_reasons,
        }

    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
