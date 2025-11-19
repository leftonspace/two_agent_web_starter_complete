"""
PHASE 2.1: Personal Knowledge Graph

SQLite-backed knowledge graph for tracking:
- Entities: missions, files, concepts, functions, agents
- Relationships: depends_on, implements, related_to, created_in, modified_in
- Evolution: How the project changes over time

Schema:
    entities: id, type, name, metadata (JSON), created_at, updated_at
    relationships: id, from_id, to_id, type, metadata (JSON), created_at
    mission_history: id, mission_id, status, cost, iterations, created_at, metadata (JSON)

Usage:
    >>> kg = KnowledgeGraph()
    >>> mission_id = kg.add_entity("mission", "build_landing_page", {"domain": "coding"})
    >>> file_id = kg.add_entity("file", "index.html", {"path": "sites/project/index.html"})
    >>> kg.add_relationship(mission_id, file_id, "created", {"iteration": 1})
    >>> related = kg.find_related(file_id, "created")
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Local imports
try:
    import paths as paths_module
    PATHS_AVAILABLE = True
except ImportError:
    PATHS_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Schema Definitions
# ══════════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
-- Entities: missions, files, concepts, functions, agents
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,           -- mission, file, concept, function, agent, module
    name TEXT NOT NULL,           -- Identifier or human-readable name
    metadata TEXT,                -- JSON metadata (domain, path, complexity, etc.)
    created_at TEXT NOT NULL,     -- ISO timestamp
    updated_at TEXT NOT NULL,     -- ISO timestamp
    UNIQUE(type, name)            -- Prevent duplicate entities
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);

-- Relationships between entities
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER NOT NULL,     -- Source entity ID
    to_id INTEGER NOT NULL,       -- Target entity ID
    type TEXT NOT NULL,           -- created, modified, depends_on, implements, related_to
    metadata TEXT,                -- JSON metadata (iteration, cost, reason, etc.)
    created_at TEXT NOT NULL,     -- ISO timestamp
    FOREIGN KEY (from_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_relationships_from ON relationships(from_id);
CREATE INDEX IF NOT EXISTS idx_relationships_to ON relationships(to_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type);

-- Mission execution history with outcomes and costs
CREATE TABLE IF NOT EXISTS mission_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mission_id TEXT NOT NULL,      -- Mission identifier (can link to entities)
    status TEXT NOT NULL,          -- success, failed, aborted
    domain TEXT,                   -- coding, finance, research, etc.
    cost_usd REAL,                 -- Total cost in USD
    iterations INTEGER,            -- Number of iterations completed
    duration_seconds REAL,         -- Execution duration
    files_modified INTEGER,        -- Number of files changed
    metadata TEXT,                 -- JSON metadata (task, config, errors, etc.)
    created_at TEXT NOT NULL,      -- ISO timestamp
    UNIQUE(mission_id)             -- One entry per mission
);

CREATE INDEX IF NOT EXISTS idx_mission_history_status ON mission_history(status);
CREATE INDEX IF NOT EXISTS idx_mission_history_domain ON mission_history(domain);
CREATE INDEX IF NOT EXISTS idx_mission_history_created ON mission_history(created_at);

-- File evolution tracking (snapshots of file states)
CREATE TABLE IF NOT EXISTS file_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,       -- Relative path from project root
    mission_id TEXT,               -- Mission that created/modified this snapshot
    size_bytes INTEGER,            -- File size
    lines_of_code INTEGER,         -- LOC count
    hash TEXT,                     -- Content hash (SHA256)
    created_at TEXT NOT NULL,      -- ISO timestamp
    metadata TEXT                  -- JSON metadata (language, complexity, etc.)
);

CREATE INDEX IF NOT EXISTS idx_file_snapshots_path ON file_snapshots(file_path);
CREATE INDEX IF NOT EXISTS idx_file_snapshots_mission ON file_snapshots(mission_id);
CREATE INDEX IF NOT EXISTS idx_file_snapshots_created ON file_snapshots(created_at);
"""


# ══════════════════════════════════════════════════════════════════════
# Knowledge Graph Class
# ══════════════════════════════════════════════════════════════════════


class KnowledgeGraph:
    """
    SQLite-backed knowledge graph for project evolution tracking.

    Tracks entities (missions, files, concepts, functions) and their
    relationships over time.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize knowledge graph with SQLite database.

        Args:
            db_path: Path to SQLite database file. If None, uses data/knowledge_graph.db
        """
        if db_path is None:
            if PATHS_AVAILABLE:
                db_path = paths_module.get_knowledge_graph_path()
            else:
                # Fallback to default location
                db_path = Path(__file__).parent.parent / "data" / "knowledge_graph.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def _now(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"

    # ══════════════════════════════════════════════════════════════════
    # Entity Operations
    # ══════════════════════════════════════════════════════════════════

    def add_entity(
        self,
        entity_type: str,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add an entity to the knowledge graph.

        Args:
            entity_type: Type of entity (mission, file, concept, function, agent, module)
            name: Entity name/identifier
            metadata: Optional metadata dictionary

        Returns:
            Entity ID (integer)
        """
        now = self._now()
        metadata_json = json.dumps(metadata or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Try to insert, if exists update
            cursor.execute("""
                INSERT INTO entities (type, name, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(type, name) DO UPDATE SET
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at
            """, (entity_type, name, metadata_json, now, now))

            # Get the entity ID
            cursor.execute("""
                SELECT id FROM entities WHERE type = ? AND name = ?
            """, (entity_type, name))

            entity_id = cursor.fetchone()[0]
            conn.commit()

            return entity_id

    def get_entity(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """
        Get entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity dict with id, type, name, metadata, created_at, updated_at
            None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM entities WHERE id = ?
            """, (entity_id,))

            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "id": row["id"],
                "type": row["type"],
                "name": row["name"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def find_entity(self, entity_type: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Find entity by type and name.

        Args:
            entity_type: Entity type
            name: Entity name

        Returns:
            Entity dict or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM entities WHERE type = ? AND name = ?
            """, (entity_type, name))

            row = cursor.fetchone()
            if row is None:
                return None

            return {
                "id": row["id"],
                "type": row["type"],
                "name": row["name"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def list_entities(
        self,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List entities, optionally filtered by type.

        Args:
            entity_type: Optional entity type filter
            limit: Maximum number of results

        Returns:
            List of entity dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if entity_type:
                cursor.execute("""
                    SELECT * FROM entities WHERE type = ?
                    ORDER BY updated_at DESC LIMIT ?
                """, (entity_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM entities
                    ORDER BY updated_at DESC LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "type": row["type"],
                    "name": row["name"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in rows
            ]

    # ══════════════════════════════════════════════════════════════════
    # Relationship Operations
    # ══════════════════════════════════════════════════════════════════

    def add_relationship(
        self,
        from_id: int,
        to_id: int,
        relationship_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a relationship between two entities.

        Args:
            from_id: Source entity ID
            to_id: Target entity ID
            relationship_type: Type (created, modified, depends_on, implements, related_to)
            metadata: Optional metadata

        Returns:
            Relationship ID
        """
        now = self._now()
        metadata_json = json.dumps(metadata or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO relationships (from_id, to_id, type, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (from_id, to_id, relationship_type, metadata_json, now))

            relationship_id = cursor.lastrowid
            conn.commit()

            return relationship_id

    def find_related(
        self,
        entity_id: int,
        relationship_type: Optional[str] = None,
        direction: str = "outgoing"
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Find entities related to a given entity.

        Args:
            entity_id: Entity ID to search from
            relationship_type: Optional relationship type filter
            direction: "outgoing" (from this entity), "incoming" (to this entity), or "both"

        Returns:
            List of (related_entity, relationship) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            results = []

            # Outgoing relationships (this entity -> others)
            if direction in ("outgoing", "both"):
                if relationship_type:
                    cursor.execute("""
                        SELECT e.*, r.type as rel_type, r.metadata as rel_metadata, r.created_at as rel_created
                        FROM relationships r
                        JOIN entities e ON r.to_id = e.id
                        WHERE r.from_id = ? AND r.type = ?
                    """, (entity_id, relationship_type))
                else:
                    cursor.execute("""
                        SELECT e.*, r.type as rel_type, r.metadata as rel_metadata, r.created_at as rel_created
                        FROM relationships r
                        JOIN entities e ON r.to_id = e.id
                        WHERE r.from_id = ?
                    """, (entity_id,))

                for row in cursor.fetchall():
                    results.append((
                        {
                            "id": row["id"],
                            "type": row["type"],
                            "name": row["name"],
                            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        },
                        {
                            "type": row["rel_type"],
                            "metadata": json.loads(row["rel_metadata"]) if row["rel_metadata"] else {},
                            "created_at": row["rel_created"],
                        }
                    ))

            # Incoming relationships (others -> this entity)
            if direction in ("incoming", "both"):
                if relationship_type:
                    cursor.execute("""
                        SELECT e.*, r.type as rel_type, r.metadata as rel_metadata, r.created_at as rel_created
                        FROM relationships r
                        JOIN entities e ON r.from_id = e.id
                        WHERE r.to_id = ? AND r.type = ?
                    """, (entity_id, relationship_type))
                else:
                    cursor.execute("""
                        SELECT e.*, r.type as rel_type, r.metadata as rel_metadata, r.created_at as rel_created
                        FROM relationships r
                        JOIN entities e ON r.from_id = e.id
                        WHERE r.to_id = ?
                    """, (entity_id,))

                for row in cursor.fetchall():
                    results.append((
                        {
                            "id": row["id"],
                            "type": row["type"],
                            "name": row["name"],
                            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                        },
                        {
                            "type": row["rel_type"],
                            "metadata": json.loads(row["rel_metadata"]) if row["rel_metadata"] else {},
                            "created_at": row["rel_created"],
                        }
                    ))

            return results

    # ══════════════════════════════════════════════════════════════════
    # Mission History Operations
    # ══════════════════════════════════════════════════════════════════

    def log_mission(
        self,
        mission_id: str,
        status: str,
        domain: Optional[str] = None,
        cost_usd: float = 0.0,
        iterations: int = 0,
        duration_seconds: float = 0.0,
        files_modified: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a mission execution to history.

        Args:
            mission_id: Mission identifier
            status: Mission status (success, failed, aborted)
            domain: Task domain (coding, finance, etc.)
            cost_usd: Total cost in USD
            iterations: Number of iterations
            duration_seconds: Execution duration
            files_modified: Number of files changed
            metadata: Additional metadata (task, config, errors, etc.)
        """
        now = self._now()
        metadata_json = json.dumps(metadata or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO mission_history (
                    mission_id, status, domain, cost_usd, iterations,
                    duration_seconds, files_modified, metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mission_id) DO UPDATE SET
                    status = excluded.status,
                    domain = excluded.domain,
                    cost_usd = excluded.cost_usd,
                    iterations = excluded.iterations,
                    duration_seconds = excluded.duration_seconds,
                    files_modified = excluded.files_modified,
                    metadata = excluded.metadata,
                    created_at = excluded.created_at
            """, (
                mission_id, status, domain, cost_usd, iterations,
                duration_seconds, files_modified, metadata_json, now
            ))

            conn.commit()

    def get_mission_history(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get mission execution history.

        Args:
            status: Optional status filter
            domain: Optional domain filter
            limit: Maximum results

        Returns:
            List of mission history dicts
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM mission_history WHERE 1=1"
            params = []

            if status:
                query += " AND status = ?"
                params.append(status)

            if domain:
                query += " AND domain = ?"
                params.append(domain)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "mission_id": row["mission_id"],
                    "status": row["status"],
                    "domain": row["domain"],
                    "cost_usd": row["cost_usd"],
                    "iterations": row["iterations"],
                    "duration_seconds": row["duration_seconds"],
                    "files_modified": row["files_modified"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregate statistics from the knowledge graph.

        Returns:
            Dict with counts, totals, averages
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Entity counts
            cursor.execute("SELECT type, COUNT(*) as count FROM entities GROUP BY type")
            entity_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Relationship counts
            cursor.execute("SELECT type, COUNT(*) as count FROM relationships GROUP BY type")
            relationship_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Mission stats
            cursor.execute("""
                SELECT
                    COUNT(*) as total_missions,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(cost_usd) as total_cost,
                    AVG(cost_usd) as avg_cost,
                    AVG(duration_seconds) as avg_duration,
                    SUM(files_modified) as total_files_modified
                FROM mission_history
            """)

            mission_stats = cursor.fetchone()

            return {
                "entities": {
                    "total": sum(entity_counts.values()),
                    "by_type": entity_counts,
                },
                "relationships": {
                    "total": sum(relationship_counts.values()),
                    "by_type": relationship_counts,
                },
                "missions": {
                    "total": mission_stats[0] or 0,
                    "successful": mission_stats[1] or 0,
                    "failed": mission_stats[2] or 0,
                    "total_cost_usd": mission_stats[3] or 0.0,
                    "avg_cost_usd": mission_stats[4] or 0.0,
                    "avg_duration_seconds": mission_stats[5] or 0.0,
                    "total_files_modified": mission_stats[6] or 0,
                }
            }

    # ══════════════════════════════════════════════════════════════════
    # File Snapshot Operations
    # ══════════════════════════════════════════════════════════════════

    def log_file_snapshot(
        self,
        file_path: str,
        mission_id: Optional[str] = None,
        size_bytes: Optional[int] = None,
        lines_of_code: Optional[int] = None,
        content_hash: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Log a file snapshot (state at a point in time).

        Args:
            file_path: Relative path from project root
            mission_id: Mission that created/modified this snapshot
            size_bytes: File size
            lines_of_code: LOC count
            content_hash: SHA256 hash of content
            metadata: Additional metadata (language, complexity, etc.)

        Returns:
            Snapshot ID
        """
        now = self._now()
        metadata_json = json.dumps(metadata or {})

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO file_snapshots (
                    file_path, mission_id, size_bytes, lines_of_code,
                    hash, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path, mission_id, size_bytes, lines_of_code,
                content_hash, now, metadata_json
            ))

            snapshot_id = cursor.lastrowid
            conn.commit()

            return snapshot_id

    def get_file_history(self, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get evolution history for a specific file.

        Args:
            file_path: File path to query
            limit: Maximum results

        Returns:
            List of file snapshots ordered by time (newest first)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM file_snapshots
                WHERE file_path = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (file_path, limit))

            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "file_path": row["file_path"],
                    "mission_id": row["mission_id"],
                    "size_bytes": row["size_bytes"],
                    "lines_of_code": row["lines_of_code"],
                    "hash": row["hash"],
                    "created_at": row["created_at"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]


# ══════════════════════════════════════════════════════════════════════
# PHASE 2.1b: Enhanced Query Functions
# ══════════════════════════════════════════════════════════════════════

    def get_files_for_mission(self, mission_id: str) -> List[Dict[str, Any]]:
        """
        Get all files worked on by a specific mission.

        Args:
            mission_id: Mission identifier

        Returns:
            List of file entity dicts with relationship metadata
        """
        # Find the mission entity
        mission_entity = self.find_entity("mission", mission_id)
        if not mission_entity:
            return []

        # Find all files related via "worked_on" relationship
        related = self.find_related(
            mission_entity["id"],
            relationship_type="worked_on",
            direction="outgoing"
        )

        return [
            {
                "file": entity,
                "relationship": rel_info,
            }
            for entity, rel_info in related
            if entity["type"] == "file"
        ]

    def get_missions_for_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all missions that touched a specific file.

        Args:
            file_path: File path to query

        Returns:
            List of mission entity dicts with relationship metadata
        """
        # Find the file entity
        file_entity = self.find_entity("file", file_path)
        if not file_entity:
            return []

        # Find all missions related via "worked_on" relationship
        related = self.find_related(
            file_entity["id"],
            relationship_type="worked_on",
            direction="incoming"
        )

        return [
            {
                "mission": entity,
                "relationship": rel_info,
            }
            for entity, rel_info in related
            if entity["type"] == "mission"
        ]

    def get_bug_relationships(self, mission_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all bug/fix relationships for a mission.

        Args:
            mission_id: Mission identifier

        Returns:
            Dict with "caused_bugs" and "fixed_bugs" lists
        """
        # Find the mission entity
        mission_entity = self.find_entity("mission", mission_id)
        if not mission_entity:
            return {"caused_bugs": [], "fixed_bugs": []}

        # Find bugs caused
        caused = self.find_related(
            mission_entity["id"],
            relationship_type="caused_bug",
            direction="outgoing"
        )

        # Find bugs fixed
        fixed = self.find_related(
            mission_entity["id"],
            relationship_type="fixed_bug",
            direction="outgoing"
        )

        return {
            "caused_bugs": [
                {"entity": entity, "relationship": rel_info}
                for entity, rel_info in caused
            ],
            "fixed_bugs": [
                {"entity": entity, "relationship": rel_info}
                for entity, rel_info in fixed
            ],
        }

    def get_risky_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get files with highest bug counts or failure associations.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of file dicts with risk scores
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Count bugs associated with each file via missions
            cursor.execute("""
                SELECT
                    f.id,
                    f.name as file_path,
                    COUNT(DISTINCT r_bug.id) as bug_count,
                    COUNT(DISTINCT r_work.id) as mission_count,
                    COUNT(DISTINCT CASE WHEN m.status = 'failed' THEN m.mission_id END) as failed_mission_count
                FROM entities f
                LEFT JOIN relationships r_work ON f.id = r_work.to_id AND r_work.type = 'worked_on'
                LEFT JOIN entities mission_entity ON r_work.from_id = mission_entity.id AND mission_entity.type = 'mission'
                LEFT JOIN mission_history m ON mission_entity.name = m.mission_id
                LEFT JOIN relationships r_bug ON mission_entity.id = r_bug.from_id AND r_bug.type = 'caused_bug'
                WHERE f.type = 'file'
                GROUP BY f.id, f.name
                HAVING mission_count > 0
                ORDER BY bug_count DESC, failed_mission_count DESC, mission_count DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [
                {
                    "file_path": row["file_path"],
                    "bug_count": row["bug_count"],
                    "mission_count": row["mission_count"],
                    "failed_mission_count": row["failed_mission_count"],
                    "risk_score": row["bug_count"] * 10 + row["failed_mission_count"] * 5,
                }
                for row in rows
            ]


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def get_knowledge_graph() -> KnowledgeGraph:
    """
    Get the singleton knowledge graph instance.

    Returns:
        KnowledgeGraph instance
    """
    return KnowledgeGraph()
