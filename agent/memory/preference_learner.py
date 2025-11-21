"""
PHASE 10.3: Personal Preferences Learning

Learn and track user preferences to personalize interactions:
- Communication style preferences
- Tool and technology preferences
- Working hours and patterns
- Task and workflow preferences

Features:
- Automatic preference extraction from interactions
- Confidence scoring for preferences
- Preference evolution over time
- Category-based organization
- Conflict resolution for contradictory preferences
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from datetime import datetime, time as dt_time
from enum import Enum
from typing import Any, Dict, List, Optional, Set

try:
    from .vector_store import VectorMemoryStore, MemoryType
except ImportError:
    from vector_store import VectorMemoryStore, MemoryType


class PreferenceCategory(Enum):
    """Categories of learnable preferences."""
    COMMUNICATION = "communication"
    TOOLS = "tools"
    WORKING_HOURS = "working_hours"
    TASK_STYLE = "task_style"
    NOTIFICATION = "notification"
    MEETING = "meeting"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


@dataclass
class Preference:
    """Represents a learned preference."""
    category: PreferenceCategory
    key: str
    value: str
    confidence: float  # 0.0-1.0
    source: str  # How it was learned (explicit, inferred, observed)
    first_seen: float
    last_updated: float
    observation_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "first_seen": self.first_seen,
            "last_updated": self.last_updated,
            "observation_count": self.observation_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Preference:
        """Create from dictionary."""
        return cls(
            category=PreferenceCategory(data["category"]),
            key=data["key"],
            value=data["value"],
            confidence=data["confidence"],
            source=data["source"],
            first_seen=data["first_seen"],
            last_updated=data["last_updated"],
            observation_count=data.get("observation_count", 1),
        )


class PreferenceLearner:
    """
    Learn and track user preferences over time.

    Automatically extracts preferences from user interactions
    and stores them with confidence scores.
    """

    def __init__(self, vector_store: VectorMemoryStore, user_id: str):
        """
        Initialize preference learner.

        Args:
            vector_store: Vector store for persistence
            user_id: User identifier
        """
        self.vector_store = vector_store
        self.user_id = user_id

        # In-memory preference cache
        self.preferences: Dict[str, Preference] = {}

        # Pattern matching for preference extraction
        self._init_patterns()

        # Statistics
        self.total_learned = 0
        self.total_observations = 0

    def _init_patterns(self):
        """Initialize regex patterns for preference extraction."""
        self.patterns = {
            PreferenceCategory.COMMUNICATION: [
                (r"prefer\s+(\w+)\s+over\s+(\w+)", "preference_comparison"),
                (r"like\s+to\s+receive\s+(.+?)\s+via\s+(\w+)", "communication_channel"),
                (r"don'?t\s+like\s+(\w+)", "negative_preference"),
                (r"always\s+use\s+(\w+)", "strong_preference"),
            ],
            PreferenceCategory.TOOLS: [
                (r"prefer\s+(\w+)\s+for\s+(.+)", "tool_for_task"),
                (r"use\s+(\w+)\s+for\s+all\s+(.+)", "tool_for_category"),
                (r"favorite\s+(\w+)\s+is\s+(\w+)", "favorite_tool"),
            ],
            PreferenceCategory.WORKING_HOURS: [
                (r"work\s+from\s+(\d+)\s*(?:am|pm)?\s+to\s+(\d+)\s*(?:am|pm)?", "work_hours"),
                (r"available\s+(?:from\s+)?(\d+)\s*(?:am|pm)?", "availability_start"),
                (r"usually\s+start\s+at\s+(\d+)\s*(?:am|pm)?", "start_time"),
            ],
            PreferenceCategory.NOTIFICATION: [
                (r"notify\s+me\s+via\s+(\w+)", "notification_channel"),
                (r"send\s+(\w+)\s+instead\s+of\s+(\w+)", "channel_preference"),
            ],
        }

    async def learn_from_text(
        self,
        text: str,
        source: str = "explicit",
        confidence: float = 0.8,
    ) -> List[Preference]:
        """
        Extract and learn preferences from text.

        Args:
            text: Text to analyze
            source: Source of learning (explicit, inferred, observed)
            confidence: Base confidence score

        Returns:
            List of newly learned or updated preferences
        """
        self.total_observations += 1
        learned_prefs = []

        # Try pattern matching for each category
        for category, patterns in self.patterns.items():
            for pattern, pattern_type in patterns:
                matches = re.finditer(pattern, text.lower())
                for match in matches:
                    pref = self._create_preference_from_match(
                        category, pattern_type, match, source, confidence
                    )
                    if pref:
                        await self._store_preference(pref)
                        learned_prefs.append(pref)

        return learned_prefs

    def _create_preference_from_match(
        self,
        category: PreferenceCategory,
        pattern_type: str,
        match: re.Match,
        source: str,
        confidence: float,
    ) -> Optional[Preference]:
        """Create preference from regex match."""
        groups = match.groups()

        if pattern_type == "preference_comparison":
            # "prefer X over Y"
            preferred, not_preferred = groups
            return Preference(
                category=category,
                key=f"prefer_{preferred}",
                value=f"prefer {preferred} over {not_preferred}",
                confidence=confidence,
                source=source,
                first_seen=time.time(),
                last_updated=time.time(),
            )

        elif pattern_type == "communication_channel":
            # "receive X via Y"
            content_type, channel = groups
            return Preference(
                category=category,
                key=f"channel_for_{content_type.replace(' ', '_')}",
                value=channel,
                confidence=confidence,
                source=source,
                first_seen=time.time(),
                last_updated=time.time(),
            )

        elif pattern_type == "tool_for_task":
            # "prefer X for Y"
            tool, task = groups
            return Preference(
                category=PreferenceCategory.TOOLS,
                key=f"tool_for_{task.replace(' ', '_')}",
                value=tool,
                confidence=confidence,
                source=source,
                first_seen=time.time(),
                last_updated=time.time(),
            )

        elif pattern_type == "work_hours":
            # "work from X to Y"
            start, end = groups
            return Preference(
                category=PreferenceCategory.WORKING_HOURS,
                key="work_hours",
                value=f"{start}:00-{end}:00",
                confidence=confidence,
                source=source,
                first_seen=time.time(),
                last_updated=time.time(),
            )

        return None

    async def _store_preference(self, pref: Preference):
        """Store or update preference."""
        pref_key = f"{pref.category.value}:{pref.key}"

        # Check if preference already exists
        if pref_key in self.preferences:
            existing = self.preferences[pref_key]

            # Update confidence (increase with repeated observations)
            new_confidence = min(
                1.0,
                existing.confidence + (1.0 - existing.confidence) * 0.2
            )

            existing.confidence = new_confidence
            existing.last_updated = time.time()
            existing.observation_count += 1

            # If value changed, store as conflict and update
            if existing.value != pref.value:
                print(f"[PreferenceLearner] Preference conflict detected: "
                      f"{pref_key} changed from '{existing.value}' to '{pref.value}'")
                existing.value = pref.value

            pref = existing
        else:
            self.preferences[pref_key] = pref
            self.total_learned += 1

        # Store in vector database
        await self.vector_store.store_memory(
            content=f"{pref.key}: {pref.value}",
            memory_type=MemoryType.PREFERENCE,
            metadata={
                "user": self.user_id,
                "category": pref.category.value,
                "key": pref.key,
                "value": pref.value,
                "confidence": pref.confidence,
                "source": pref.source,
                **pref.to_dict(),
            },
            memory_id=f"pref_{self.user_id}_{pref_key.replace(':', '_')}",
        )

    async def record_explicit_preference(
        self,
        category: PreferenceCategory,
        key: str,
        value: str,
    ):
        """
        Record an explicitly stated preference.

        Args:
            category: Preference category
            key: Preference key
            value: Preference value
        """
        pref = Preference(
            category=category,
            key=key,
            value=value,
            confidence=1.0,  # Explicit preferences have full confidence
            source="explicit",
            first_seen=time.time(),
            last_updated=time.time(),
        )

        await self._store_preference(pref)

    async def infer_preference(
        self,
        category: PreferenceCategory,
        key: str,
        value: str,
        confidence: float = 0.6,
    ):
        """
        Record an inferred preference (lower confidence).

        Args:
            category: Preference category
            key: Preference key
            value: Preference value
            confidence: Confidence score (default 0.6)
        """
        pref = Preference(
            category=category,
            key=key,
            value=value,
            confidence=confidence,
            source="inferred",
            first_seen=time.time(),
            last_updated=time.time(),
        )

        await self._store_preference(pref)

    def get_preference(
        self,
        category: PreferenceCategory,
        key: str,
    ) -> Optional[Preference]:
        """
        Get specific preference.

        Args:
            category: Preference category
            key: Preference key

        Returns:
            Preference or None
        """
        pref_key = f"{category.value}:{key}"
        return self.preferences.get(pref_key)

    def get_all_preferences(
        self,
        category: Optional[PreferenceCategory] = None,
        min_confidence: float = 0.5,
    ) -> List[Preference]:
        """
        Get all preferences, optionally filtered.

        Args:
            category: Filter by category
            min_confidence: Minimum confidence threshold

        Returns:
            List of preferences
        """
        prefs = list(self.preferences.values())

        # Filter by category
        if category:
            prefs = [p for p in prefs if p.category == category]

        # Filter by confidence
        prefs = [p for p in prefs if p.confidence >= min_confidence]

        # Sort by confidence (descending)
        prefs.sort(key=lambda p: p.confidence, reverse=True)

        return prefs

    def get_working_hours(self) -> Optional[Dict[str, str]]:
        """
        Get user's working hours preference.

        Returns:
            Dict with start and end times, or None
        """
        pref = self.get_preference(PreferenceCategory.WORKING_HOURS, "work_hours")
        if pref and pref.confidence >= 0.5:
            # Parse "HH:MM-HH:MM" format
            if "-" in pref.value:
                start, end = pref.value.split("-")
                return {"start": start, "end": end}

        return None

    def is_working_hours(self, check_time: Optional[datetime] = None) -> bool:
        """
        Check if given time is within user's working hours.

        Args:
            check_time: Time to check (default: now)

        Returns:
            True if within working hours
        """
        if check_time is None:
            check_time = datetime.now()

        working_hours = self.get_working_hours()
        if not working_hours:
            return True  # Assume always available if no preference

        try:
            start_hour = int(working_hours["start"].split(":")[0])
            end_hour = int(working_hours["end"].split(":")[0])

            current_hour = check_time.hour

            return start_hour <= current_hour < end_hour

        except (ValueError, KeyError):
            return True

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of learned preferences.

        Returns:
            Summary dict with statistics
        """
        by_category = {}
        for pref in self.preferences.values():
            cat = pref.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(pref)

        return {
            "user_id": self.user_id,
            "total_preferences": len(self.preferences),
            "total_learned": self.total_learned,
            "total_observations": self.total_observations,
            "by_category": {
                cat: len(prefs) for cat, prefs in by_category.items()
            },
            "high_confidence": len([p for p in self.preferences.values() if p.confidence >= 0.8]),
            "medium_confidence": len([p for p in self.preferences.values() if 0.5 <= p.confidence < 0.8]),
            "low_confidence": len([p for p in self.preferences.values() if p.confidence < 0.5]),
        }
