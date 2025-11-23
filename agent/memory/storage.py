"""
Memory Storage Backends

Provides various storage implementations for the memory system:
- InMemoryStorage: Fast, volatile storage for development/testing
- SQLiteStorage: Persistent storage with SQL capabilities
- GraphStorage: Entity relationship storage
- VectorStorage: Embedding-based similarity search
"""

from typing import List, Dict, Optional, Any, Iterator, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import json
import sqlite3
import threading
import uuid
import math
from collections import defaultdict


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class MemoryItem:
    """A single memory item"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    score: float = 0.0  # Relevance score from search

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "score": self.score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class Entity:
    """An entity extracted from text"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    entity_type: str = "unknown"  # person, organization, location, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    mentions: List[Dict[str, Any]] = field(default_factory=list)  # context where mentioned
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_mention(self, context: str, metadata: Dict = None):
        self.mentions.append({
            "context": context,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "attributes": self.attributes,
            "mentions": self.mentions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class EntityContext:
    """Context information about an entity"""
    entity: Entity
    related_entities: List[Entity] = field(default_factory=list)
    recent_mentions: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""


@dataclass
class TaskResult:
    """A stored task result"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    result: str = ""
    status: str = "completed"
    files: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "result": self.result,
            "status": self.status,
            "files": self.files,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "embedding": self.embedding
        }


# =============================================================================
# Abstract Base Storage
# =============================================================================

class MemoryStorage(ABC):
    """Abstract base class for memory storage"""

    @abstractmethod
    def add(self, item: MemoryItem) -> str:
        """Add item and return ID"""
        pass

    @abstractmethod
    def get(self, item_id: str) -> Optional[MemoryItem]:
        """Get item by ID"""
        pass

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryItem]:
        """Search by embedding similarity"""
        pass

    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """Delete item by ID"""
        pass

    @abstractmethod
    def clear(self):
        """Clear all items"""
        pass

    @abstractmethod
    def count(self) -> int:
        """Get total item count"""
        pass


# =============================================================================
# In-Memory Storage
# =============================================================================

class InMemoryStorage(MemoryStorage):
    """
    Fast in-memory storage with vector similarity search.

    Suitable for development, testing, and short-term memory.
    """

    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self._items: Dict[str, MemoryItem] = {}
        self._insertion_order: List[str] = []

    def add(self, item: MemoryItem) -> str:
        # Enforce max items (FIFO)
        while len(self._items) >= self.max_items:
            oldest_id = self._insertion_order.pop(0)
            del self._items[oldest_id]

        self._items[item.id] = item
        self._insertion_order.append(item.id)
        return item.id

    def get(self, item_id: str) -> Optional[MemoryItem]:
        return self._items.get(item_id)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryItem]:
        if not query_embedding or not self._items:
            return []

        # Calculate similarities
        scored_items = []
        for item in self._items.values():
            if item.embedding:
                similarity = self._cosine_similarity(query_embedding, item.embedding)
                item_copy = MemoryItem(
                    id=item.id,
                    content=item.content,
                    embedding=item.embedding,
                    metadata=item.metadata,
                    timestamp=item.timestamp,
                    score=similarity
                )
                scored_items.append(item_copy)

        # Sort by similarity descending
        scored_items.sort(key=lambda x: x.score, reverse=True)
        return scored_items[:top_k]

    def search_by_text(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Simple text-based search (fallback when no embeddings)"""
        if not query or not self._items:
            return []

        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_items = []
        for item in self._items.values():
            content_lower = item.content.lower()
            content_words = set(content_lower.split())

            # Simple word overlap scoring
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / max(len(query_words), len(content_words))
                item_copy = MemoryItem(
                    id=item.id,
                    content=item.content,
                    embedding=item.embedding,
                    metadata=item.metadata,
                    timestamp=item.timestamp,
                    score=score
                )
                scored_items.append(item_copy)

        scored_items.sort(key=lambda x: x.score, reverse=True)
        return scored_items[:top_k]

    def delete(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            self._insertion_order.remove(item_id)
            return True
        return False

    def clear(self):
        self._items.clear()
        self._insertion_order.clear()

    def count(self) -> int:
        return len(self._items)

    def get_all(self) -> List[MemoryItem]:
        """Get all items in insertion order"""
        return [self._items[id] for id in self._insertion_order]

    def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """Get n most recent items"""
        recent_ids = self._insertion_order[-n:]
        return [self._items[id] for id in recent_ids]

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# =============================================================================
# SQLite Storage
# =============================================================================

class SQLiteStorage(MemoryStorage):
    """
    Persistent SQLite-based storage.

    Suitable for long-term memory and task history.
    Thread-safe with connection locking.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.RLock()  # Thread safety for connection
        self._create_tables()

    def _create_tables(self):
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_items (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    metadata TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_items(timestamp)
            """)
            self._conn.commit()

    def add(self, item: MemoryItem) -> str:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO memory_items
                   (id, content, embedding, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    item.id,
                    item.content,
                    json.dumps(item.embedding) if item.embedding else None,
                    json.dumps(item.metadata),
                    item.timestamp.isoformat()
                )
            )
            self._conn.commit()
        return item.id

    def get(self, item_id: str) -> Optional[MemoryItem]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, content, embedding, metadata, timestamp FROM memory_items WHERE id = ?",
                (item_id,)
            )
            row = cursor.fetchone()
        if row:
            return self._row_to_item(row)
        return None

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryItem]:
        """Search by embedding similarity (loads all, calculates in memory)"""
        if not query_embedding:
            return []

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT id, content, embedding, metadata, timestamp FROM memory_items WHERE embedding IS NOT NULL"
            )
            rows = cursor.fetchall()

        scored_items = []
        for row in rows:
            item = self._row_to_item(row)
            if item.embedding:
                similarity = InMemoryStorage._cosine_similarity(query_embedding, item.embedding)
                item.score = similarity
                scored_items.append(item)

        scored_items.sort(key=lambda x: x.score, reverse=True)
        return scored_items[:top_k]

    def search_by_text(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Full-text search using LIKE"""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT id, content, embedding, metadata, timestamp
                   FROM memory_items
                   WHERE content LIKE ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (f"%{query}%", top_k)
            )
            rows = cursor.fetchall()

        return [self._row_to_item(row) for row in rows]

    def delete(self, item_id: str) -> bool:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM memory_items WHERE id = ?", (item_id,))
            self._conn.commit()
            return cursor.rowcount > 0

    def clear(self):
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM memory_items")
            self._conn.commit()

    def count(self) -> int:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_items")
            return cursor.fetchone()[0]

    def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """Get n most recent items"""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """SELECT id, content, embedding, metadata, timestamp
                   FROM memory_items
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (n,)
            )
            rows = cursor.fetchall()
        return [self._row_to_item(row) for row in rows]

    def _row_to_item(self, row: tuple) -> MemoryItem:
        return MemoryItem(
            id=row[0],
            content=row[1],
            embedding=json.loads(row[2]) if row[2] else None,
            metadata=json.loads(row[3]) if row[3] else {},
            timestamp=datetime.fromisoformat(row[4])
        )

    def close(self):
        self._conn.close()


# =============================================================================
# Task Storage (SQLite-based)
# =============================================================================

class TaskStorage:
    """
    Specialized storage for task results.

    Supports task history, similarity search, and user preferences.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self._conn.cursor()

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                result TEXT,
                status TEXT DEFAULT 'completed',
                files TEXT,
                metadata TEXT,
                embedding TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT NOT NULL,
                preference_key TEXT NOT NULL,
                preference_value TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (user_id, preference_key)
            )
        """)

        self._conn.commit()

    def store_task(self, task: TaskResult) -> str:
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO tasks
               (id, description, result, status, files, metadata, embedding, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id,
                task.description,
                task.result,
                task.status,
                json.dumps(task.files),
                json.dumps(task.metadata),
                json.dumps(task.embedding) if task.embedding else None,
                task.created_at.isoformat()
            )
        )
        self._conn.commit()
        return task.id

    def get_task(self, task_id: str) -> Optional[TaskResult]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_task(row)
        return None

    def get_similar_tasks(
        self,
        query_embedding: Optional[List[float]] = None,
        description: Optional[str] = None,
        top_k: int = 5
    ) -> List[TaskResult]:
        """Find similar tasks by embedding or text"""
        cursor = self._conn.cursor()

        if query_embedding:
            # Embedding-based search
            cursor.execute("SELECT * FROM tasks WHERE embedding IS NOT NULL")
            tasks = []
            for row in cursor.fetchall():
                task = self._row_to_task(row)
                if task.embedding:
                    similarity = InMemoryStorage._cosine_similarity(
                        query_embedding, task.embedding
                    )
                    task.metadata["similarity_score"] = similarity
                    tasks.append(task)

            tasks.sort(key=lambda t: t.metadata.get("similarity_score", 0), reverse=True)
            return tasks[:top_k]

        elif description:
            # Text-based search
            cursor.execute(
                """SELECT * FROM tasks
                   WHERE description LIKE ?
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (f"%{description}%", top_k)
            )
            return [self._row_to_task(row) for row in cursor.fetchall()]

        return []

    def get_recent_tasks(self, n: int = 10) -> List[TaskResult]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
            (n,)
        )
        return [self._row_to_task(row) for row in cursor.fetchall()]

    def store_preference(self, user_id: str, key: str, value: Any):
        cursor = self._conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO user_preferences
               (user_id, preference_key, preference_value, updated_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, key, json.dumps(value), datetime.now().isoformat())
        )
        self._conn.commit()

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?",
            (user_id,)
        )
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    def _row_to_task(self, row: tuple) -> TaskResult:
        return TaskResult(
            id=row[0],
            description=row[1],
            result=row[2] or "",
            status=row[3],
            files=json.loads(row[4]) if row[4] else [],
            metadata=json.loads(row[5]) if row[5] else {},
            embedding=json.loads(row[6]) if row[6] else None,
            created_at=datetime.fromisoformat(row[7])
        )

    def close(self):
        self._conn.close()


# =============================================================================
# Graph Storage (for Entity Relationships)
# =============================================================================

class GraphStorage:
    """
    Graph-based storage for entity relationships.

    Uses an in-memory adjacency list representation.
    Can be extended to use Neo4j or similar.
    """

    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._name_to_id: Dict[str, str] = {}  # lowercase name -> id
        self._edges: Dict[str, List[Tuple[str, str, Dict]]] = defaultdict(list)  # entity_id -> [(target_id, relation, metadata)]

    def add_entity(self, entity: Entity) -> str:
        """Add or update entity"""
        # Check if entity with same name exists
        name_lower = entity.name.lower()
        if name_lower in self._name_to_id:
            # Update existing entity
            existing_id = self._name_to_id[name_lower]
            existing = self._entities[existing_id]
            existing.attributes.update(entity.attributes)
            existing.mentions.extend(entity.mentions)
            existing.updated_at = datetime.now()
            return existing_id

        # Add new entity
        self._entities[entity.id] = entity
        self._name_to_id[name_lower] = entity.id
        return entity.id

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self._entities.get(entity_id)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        entity_id = self._name_to_id.get(name.lower())
        if entity_id:
            return self._entities.get(entity_id)
        return None

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        metadata: Dict = None
    ):
        """Add a relationship between entities"""
        if source_id in self._entities and target_id in self._entities:
            self._edges[source_id].append((target_id, relation, metadata or {}))

    def get_related_entities(self, entity_id: str) -> List[Tuple[Entity, str, Dict]]:
        """Get entities related to the given entity"""
        related = []
        for target_id, relation, metadata in self._edges.get(entity_id, []):
            target = self._entities.get(target_id)
            if target:
                related.append((target, relation, metadata))
        return related

    def search_entities(
        self,
        query: str = None,
        entity_type: str = None,
        limit: int = 10
    ) -> List[Entity]:
        """Search entities by name or type"""
        results = []

        for entity in self._entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue

            if query:
                if query.lower() not in entity.name.lower():
                    continue

            results.append(entity)
            if len(results) >= limit:
                break

        return results

    def delete_entity(self, entity_id: str) -> bool:
        if entity_id in self._entities:
            entity = self._entities[entity_id]
            del self._name_to_id[entity.name.lower()]
            del self._entities[entity_id]

            # Remove edges
            if entity_id in self._edges:
                del self._edges[entity_id]

            # Remove references in other edges
            for src_id in self._edges:
                self._edges[src_id] = [
                    (t, r, m) for t, r, m in self._edges[src_id]
                    if t != entity_id
                ]

            return True
        return False

    def clear(self):
        self._entities.clear()
        self._name_to_id.clear()
        self._edges.clear()

    def count(self) -> int:
        return len(self._entities)

    def get_all_entities(self) -> List[Entity]:
        return list(self._entities.values())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for persistence"""
        return {
            "entities": {k: v.to_dict() for k, v in self._entities.items()},
            "edges": dict(self._edges)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphStorage":
        """Deserialize from dict representation.

        Creates a fresh instance with its own state to avoid sharing
        between deserialized instances.
        """
        storage = cls()
        # Explicitly reset instance dicts to ensure fresh state
        storage._entities = {}
        storage._name_to_id = {}
        storage._edges = defaultdict(list)

        for entity_id, entity_data in data.get("entities", {}).items():
            entity = Entity(
                id=entity_data["id"],
                name=entity_data["name"],
                entity_type=entity_data.get("entity_type", "unknown"),
                attributes=entity_data.get("attributes", {}),
                mentions=entity_data.get("mentions", [])
            )
            storage._entities[entity_id] = entity
            storage._name_to_id[entity.name.lower()] = entity_id

        # Merge edges from data
        for source_id, edges_list in data.get("edges", {}).items():
            storage._edges[source_id] = edges_list

        return storage


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Data models
    'MemoryItem',
    'Entity',
    'EntityContext',
    'TaskResult',

    # Abstract base
    'MemoryStorage',

    # Implementations
    'InMemoryStorage',
    'SQLiteStorage',
    'TaskStorage',
    'GraphStorage',
]
