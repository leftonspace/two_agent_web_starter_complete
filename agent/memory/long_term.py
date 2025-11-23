"""
Long-Term Memory (LTM)

Persistent memory across sessions for task history,
learned patterns, and user preferences.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
import json

from .storage import TaskStorage, TaskResult, SQLiteStorage, MemoryItem


@dataclass
class LTMConfig:
    """Configuration for Long-Term Memory"""
    db_path: str = ":memory:"
    max_similar_results: int = 10
    preference_expiry_days: int = 90
    auto_learn_preferences: bool = True


@dataclass
class LearnedPattern:
    """A pattern learned from past interactions"""
    id: str
    pattern_type: str  # "preference", "workflow", "correction", etc.
    description: str
    examples: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None


class LongTermMemory:
    """
    Persistent memory across sessions.

    Provides:
    - Task history storage and retrieval
    - Similar task finding for learning from past work
    - User preference storage and retrieval
    - Pattern learning from interactions

    Usage:
        ltm = LongTermMemory(storage=SQLiteStorage("memory.db"))

        ltm.store_task_result("task_1", {
            "description": "Build portfolio website",
            "result": "success",
            "files": ["index.html", "style.css"]
        })

        similar = ltm.get_similar_tasks("Create a personal website")
    """

    def __init__(
        self,
        storage: Optional[TaskStorage] = None,
        config: Optional[LTMConfig] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        async_embedding_fn: Optional[Callable[[str], Awaitable[List[float]]]] = None
    ):
        """
        Initialize Long-Term Memory.

        Args:
            storage: TaskStorage backend
            config: LTM configuration
            embedding_fn: Sync function to generate embeddings
            async_embedding_fn: Async function to generate embeddings
        """
        self.config = config or LTMConfig()
        self.storage = storage or TaskStorage(db_path=self.config.db_path)
        self.embedding_fn = embedding_fn
        self.async_embedding_fn = async_embedding_fn

        # Learned patterns cache - loaded from and persisted to storage
        self._patterns: Dict[str, LearnedPattern] = {}
        self._load_patterns_from_storage()

    def _load_patterns_from_storage(self):
        """Load persisted patterns from storage on startup."""
        try:
            # Get patterns from storage metadata
            patterns_data = self.storage.get_metadata("learned_patterns")
            if patterns_data:
                for pattern_id, pdata in patterns_data.items():
                    self._patterns[pattern_id] = LearnedPattern(
                        id=pdata["id"],
                        pattern_type=pdata["pattern_type"],
                        description=pdata["description"],
                        examples=pdata.get("examples", []),
                        confidence=pdata.get("confidence", 0.0),
                        usage_count=pdata.get("usage_count", 0),
                        last_used=datetime.fromisoformat(pdata["last_used"]) if pdata.get("last_used") else None
                    )
        except Exception:
            # Storage may not support metadata yet, start with empty patterns
            pass

    def _persist_patterns_to_storage(self):
        """Persist patterns cache to storage."""
        try:
            patterns_data = {}
            for pattern_id, pattern in self._patterns.items():
                patterns_data[pattern_id] = {
                    "id": pattern.id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "examples": pattern.examples,
                    "confidence": pattern.confidence,
                    "usage_count": pattern.usage_count,
                    "last_used": pattern.last_used.isoformat() if pattern.last_used else None
                }
            self.storage.set_metadata("learned_patterns", patterns_data)
        except Exception:
            # Storage may not support metadata, patterns stay in memory only
            pass

    def store_task_result(
        self,
        task_id: str,
        result: Dict[str, Any],
        generate_embedding: bool = True
    ) -> str:
        """
        Store completed task for future reference.

        Args:
            task_id: Unique task identifier
            result: Task result data including:
                - description: Task description
                - result: Outcome/output
                - status: "success", "failed", etc.
                - files: List of files created/modified
                - metadata: Additional data
            generate_embedding: Whether to generate embedding for similarity search

        Returns:
            Task ID
        """
        description = result.get("description", "")
        embedding = None

        if generate_embedding and description and self.embedding_fn:
            embedding = self.embedding_fn(description)

        task = TaskResult(
            id=task_id,
            description=description,
            result=result.get("result", ""),
            status=result.get("status", "completed"),
            files=result.get("files", []),
            metadata=result.get("metadata", {}),
            embedding=embedding
        )

        return self.storage.store_task(task)

    async def store_task_result_async(
        self,
        task_id: str,
        result: Dict[str, Any],
        generate_embedding: bool = True
    ) -> str:
        """Async version of store_task_result"""
        description = result.get("description", "")
        embedding = None

        if generate_embedding and description and self.async_embedding_fn:
            embedding = await self.async_embedding_fn(description)

        task = TaskResult(
            id=task_id,
            description=description,
            result=result.get("result", ""),
            status=result.get("status", "completed"),
            files=result.get("files", []),
            metadata=result.get("metadata", {}),
            embedding=embedding
        )

        return self.storage.store_task(task)

    def get_similar_tasks(
        self,
        description: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[TaskResult]:
        """
        Find similar past tasks.

        Args:
            description: Task description to match
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of similar TaskResults
        """
        if self.embedding_fn:
            query_embedding = self.embedding_fn(description)
            results = self.storage.get_similar_tasks(
                query_embedding=query_embedding,
                top_k=top_k
            )
            # Filter by similarity threshold
            results = [
                r for r in results
                if r.metadata.get("similarity_score", 0) >= min_similarity
            ]
        else:
            # Fall back to text search
            results = self.storage.get_similar_tasks(
                description=description,
                top_k=top_k
            )

        return results

    async def get_similar_tasks_async(
        self,
        description: str,
        top_k: int = 5,
        min_similarity: float = 0.5
    ) -> List[TaskResult]:
        """Async version of get_similar_tasks"""
        if self.async_embedding_fn:
            query_embedding = await self.async_embedding_fn(description)
            results = self.storage.get_similar_tasks(
                query_embedding=query_embedding,
                top_k=top_k
            )
            results = [
                r for r in results
                if r.metadata.get("similarity_score", 0) >= min_similarity
            ]
        else:
            results = self.storage.get_similar_tasks(
                description=description,
                top_k=top_k
            )

        return results

    def get_task(self, task_id: str) -> Optional[TaskResult]:
        """Get a specific task by ID"""
        return self.storage.get_task(task_id)

    def get_recent_tasks(self, n: int = 10) -> List[TaskResult]:
        """Get n most recent tasks"""
        return self.storage.get_recent_tasks(n)

    # User Preferences

    def store_user_preference(
        self,
        user_id: str,
        key: str,
        value: Any
    ):
        """
        Store a user preference.

        Args:
            user_id: User identifier
            key: Preference key (e.g., "preferred_framework", "color_scheme")
            value: Preference value
        """
        self.storage.store_preference(user_id, key, value)

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve learned user preferences.

        Args:
            user_id: User identifier

        Returns:
            Dict of preference key -> value
        """
        return self.storage.get_preferences(user_id)

    def get_user_preference(
        self,
        user_id: str,
        key: str,
        default: Any = None
    ) -> Any:
        """Get a specific user preference"""
        prefs = self.get_user_preferences(user_id)
        return prefs.get(key, default)

    # Pattern Learning

    def learn_pattern(
        self,
        pattern_type: str,
        description: str,
        example: Dict[str, Any]
    ) -> str:
        """
        Learn a pattern from an interaction.

        Args:
            pattern_type: Type of pattern ("preference", "workflow", etc.)
            description: Pattern description
            example: Example of the pattern

        Returns:
            Pattern ID
        """
        # Generate pattern ID from description
        import hashlib
        pattern_id = hashlib.md5(
            f"{pattern_type}:{description}".encode()
        ).hexdigest()[:12]

        if pattern_id in self._patterns:
            # Update existing pattern
            pattern = self._patterns[pattern_id]
            pattern.examples.append(example)
            pattern.usage_count += 1
            pattern.confidence = min(1.0, pattern.confidence + 0.1)
            pattern.last_used = datetime.now()
        else:
            # Create new pattern
            pattern = LearnedPattern(
                id=pattern_id,
                pattern_type=pattern_type,
                description=description,
                examples=[example],
                confidence=0.5,
                usage_count=1,
                last_used=datetime.now()
            )
            self._patterns[pattern_id] = pattern

        # Persist patterns to storage
        self._persist_patterns_to_storage()

        return pattern_id

    def get_patterns(
        self,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.0
    ) -> List[LearnedPattern]:
        """Get learned patterns"""
        patterns = list(self._patterns.values())

        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        patterns = [p for p in patterns if p.confidence >= min_confidence]

        # Sort by confidence descending
        patterns.sort(key=lambda p: p.confidence, reverse=True)

        return patterns

    def apply_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get pattern data for application.

        Also updates usage statistics.
        """
        pattern = self._patterns.get(pattern_id)
        if pattern:
            pattern.usage_count += 1
            pattern.last_used = datetime.now()
            return {
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "examples": pattern.examples,
                "confidence": pattern.confidence
            }
        return None

    # Statistics and Insights

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored tasks"""
        tasks = self.storage.get_recent_tasks(100)

        if not tasks:
            return {"total": 0}

        successful = sum(1 for t in tasks if t.status == "completed")
        failed = sum(1 for t in tasks if t.status == "failed")

        return {
            "total": len(tasks),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(tasks) if tasks else 0,
            "most_common_files": self._get_common_files(tasks),
        }

    def _get_common_files(self, tasks: List[TaskResult]) -> List[str]:
        """Get most commonly created files"""
        from collections import Counter
        all_files = []
        for task in tasks:
            all_files.extend(task.files)

        counter = Counter(all_files)
        return [f for f, _ in counter.most_common(10)]

    def get_insights(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get insights from long-term memory.

        Returns aggregated learnings and patterns.
        """
        insights = {
            "task_statistics": self.get_task_statistics(),
            "learned_patterns": len(self._patterns),
            "high_confidence_patterns": len([
                p for p in self._patterns.values()
                if p.confidence >= 0.8
            ]),
        }

        if user_id:
            prefs = self.get_user_preferences(user_id)
            insights["user_preferences"] = len(prefs)
            insights["preference_keys"] = list(prefs.keys())

        return insights

    def close(self):
        """Close storage connections"""
        if hasattr(self.storage, 'close'):
            self.storage.close()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'LTMConfig',
    'LongTermMemory',
    'LearnedPattern',
]
