"""
Adaptive User Profile Memory System

Stores and learns user-specific information to personalize JARVIS interactions.
Handles both explicit memories ("remember I prefer...") and implicit trait detection.

Memory Categories:
- Personal: Name, role, background, personality traits
- Preferences: Communication style, detail level, formality
- Business: Company info, team members, projects, processes
- Expertise: Technical skills, domain knowledge, experience level
- Interaction: Historical patterns, common requests, peak times

Features:
- Explicit memory storage via natural language
- Implicit trait detection from conversation patterns
- Adaptive personality recommendations
- Multi-user support with profile isolation
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sqlite3


class MemoryCategory(Enum):
    """Categories for organizing user memories."""
    PERSONAL = "personal"           # Name, role, personality, background
    PREFERENCES = "preferences"     # Communication style, detail preferences
    BUSINESS = "business"           # Company, team, projects, processes
    EXPERTISE = "expertise"         # Skills, knowledge areas, experience
    INTERACTION = "interaction"     # Patterns, common requests
    CUSTOM = "custom"               # User-defined categories


class CommunicationStyle(Enum):
    """Detected communication styles."""
    CONCISE = "concise"             # Prefers brief, to-the-point responses
    DETAILED = "detailed"           # Prefers thorough explanations
    TECHNICAL = "technical"         # Uses/prefers technical language
    CASUAL = "casual"               # Informal, conversational
    FORMAL = "formal"               # Professional, structured
    BALANCED = "balanced"           # Default adaptive style


class ExpertiseLevel(Enum):
    """User expertise levels for topic areas."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNKNOWN = "unknown"


@dataclass
class UserTrait:
    """A detected or stated user trait."""
    trait_type: str                 # e.g., "communication_style", "expertise_python"
    value: str                      # e.g., "concise", "advanced"
    confidence: float               # 0.0 to 1.0
    source: str                     # "explicit" or "detected"
    evidence: List[str] = field(default_factory=list)  # Supporting observations
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserTrait":
        return cls(**data)


@dataclass
class UserMemory:
    """A piece of stored user memory."""
    id: str
    category: MemoryCategory
    content: str
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5         # 0.0 to 1.0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    source: str = "explicit"        # "explicit" or "inferred"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserMemory":
        data["category"] = MemoryCategory(data["category"])
        return cls(**data)


@dataclass
class UserProfile:
    """Complete profile for a user."""
    user_id: str
    display_name: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_interaction: float = field(default_factory=time.time)

    # Detected traits
    traits: Dict[str, UserTrait] = field(default_factory=dict)

    # Interaction statistics
    total_messages: int = 0
    avg_message_length: float = 0.0
    common_topics: List[str] = field(default_factory=list)

    # Adaptive settings
    preferred_style: CommunicationStyle = CommunicationStyle.BALANCED
    detail_level: float = 0.5       # 0.0 = minimal, 1.0 = maximum detail
    formality_level: float = 0.5    # 0.0 = casual, 1.0 = formal

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "last_interaction": self.last_interaction,
            "traits": {k: v.to_dict() for k, v in self.traits.items()},
            "total_messages": self.total_messages,
            "avg_message_length": self.avg_message_length,
            "common_topics": self.common_topics,
            "preferred_style": self.preferred_style.value,
            "detail_level": self.detail_level,
            "formality_level": self.formality_level
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        profile = cls(
            user_id=data["user_id"],
            display_name=data.get("display_name"),
            created_at=data.get("created_at", time.time()),
            last_interaction=data.get("last_interaction", time.time()),
            total_messages=data.get("total_messages", 0),
            avg_message_length=data.get("avg_message_length", 0.0),
            common_topics=data.get("common_topics", []),
            preferred_style=CommunicationStyle(data.get("preferred_style", "balanced")),
            detail_level=data.get("detail_level", 0.5),
            formality_level=data.get("formality_level", 0.5)
        )
        profile.traits = {
            k: UserTrait.from_dict(v)
            for k, v in data.get("traits", {}).items()
        }
        return profile


class AdaptiveMemoryManager:
    """
    Manages user profiles and adaptive memory.

    Provides:
    - User profile CRUD operations
    - Memory storage and retrieval by category
    - Implicit trait detection from messages
    - Explicit memory extraction from commands
    - Personality adaptation recommendations
    """

    # Patterns for detecting explicit memory requests
    REMEMBER_PATTERNS = [
        r"remember (?:that )?(?:i |my |i'm |i am )(.+)",
        r"(?:please )?note (?:that )?(.+)",
        r"(?:for )?(?:future )?reference[,:]? (.+)",
        r"keep in mind (?:that )?(.+)",
        r"don't forget (?:that )?(.+)",
        r"(?:my |i )prefer (.+)",
        r"i (?:always |usually |typically )(.+)",
        r"(?:fyi|for your information)[,:]? (.+)",
    ]

    # Patterns for categorizing memories
    CATEGORY_PATTERNS = {
        MemoryCategory.PERSONAL: [
            r"\b(?:my name is|i am|i'm called|call me)\b",
            r"\b(?:my role|my job|i work as|my position)\b",
            r"\b(?:my personality|i'm a .+ person|i tend to be)\b",
        ],
        MemoryCategory.PREFERENCES: [
            r"\b(?:i prefer|i like|i don't like|i hate|i love)\b",
            r"\b(?:keep it|make it|be more) (?:brief|short|detailed|concise)\b",
            r"\b(?:formal|casual|professional|friendly) (?:tone|style)\b",
        ],
        MemoryCategory.BUSINESS: [
            r"\b(?:my company|our company|we work|our team|my team)\b",
            r"\b(?:our project|the project|we're building|we're working on)\b",
            r"\b(?:our client|customer|stakeholder)\b",
        ],
        MemoryCategory.EXPERTISE: [
            r"\b(?:i know|i'm experienced|i specialize|my expertise)\b",
            r"\b(?:i'm new to|i'm learning|i don't know much about)\b",
            r"\b(?:years of experience|senior|junior|lead|expert)\b",
        ],
    }

    # Trait detection patterns
    TRAIT_PATTERNS = {
        "concise_preference": [
            r"\b(?:brief|short|concise|quick|tldr|tl;dr|summary)\b",
            r"\bjust (?:tell me|give me|the)\b",
            r"\bget to the point\b",
        ],
        "detailed_preference": [
            r"\b(?:explain|elaborate|detail|thorough|comprehensive)\b",
            r"\b(?:walk me through|step by step|in depth)\b",
            r"\b(?:why|how come|what's the reason)\b",
        ],
        "technical_level": [
            r"\b(?:api|sdk|framework|algorithm|architecture)\b",
            r"\b(?:code|function|class|method|variable)\b",
            r"\b(?:debug|deploy|compile|runtime)\b",
        ],
    }

    def __init__(self, db_path: str = "data/user_profiles.db"):
        """Initialize the adaptive memory manager."""
        self.db_path = db_path
        self._ensure_db_exists()
        self._init_database()

        # Cache for active profiles
        self._profile_cache: Dict[str, UserProfile] = {}
        self._memory_cache: Dict[str, List[UserMemory]] = {}

    def _ensure_db_exists(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _init_database(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

            # User memories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_memories (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    importance REAL NOT NULL,
                    created_at REAL NOT NULL,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_user
                ON user_memories (user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_category
                ON user_memories (user_id, category)
            """)

            conn.commit()

    # ══════════════════════════════════════════════════════════════════════
    # Profile Management
    # ══════════════════════════════════════════════════════════════════════

    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Get existing profile or create new one."""
        # Check cache first
        if user_id in self._profile_cache:
            return self._profile_cache[user_id]

        # Try to load from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT profile_data FROM user_profiles WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()

            if row:
                profile = UserProfile.from_dict(json.loads(row[0]))
            else:
                # Create new profile
                profile = UserProfile(user_id=user_id)
                self._save_profile(profile)

            self._profile_cache[user_id] = profile
            return profile

    def _save_profile(self, profile: UserProfile):
        """Save profile to database."""
        profile.last_interaction = time.time()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_profiles
                (user_id, profile_data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                profile.user_id,
                json.dumps(profile.to_dict()),
                profile.created_at,
                time.time()
            ))
            conn.commit()

        self._profile_cache[profile.user_id] = profile

    def update_profile_trait(
        self,
        user_id: str,
        trait_type: str,
        value: str,
        confidence: float = 0.5,
        source: str = "detected",
        evidence: Optional[str] = None
    ):
        """Update or add a trait to user profile."""
        profile = self.get_or_create_profile(user_id)

        if trait_type in profile.traits:
            # Update existing trait
            trait = profile.traits[trait_type]
            trait.value = value
            # Increase confidence if consistent, decrease if different
            if evidence:
                trait.evidence.append(evidence)
                # Keep only last 10 evidence items
                trait.evidence = trait.evidence[-10:]
            trait.confidence = min(1.0, trait.confidence + 0.1)
            trait.last_updated = time.time()
        else:
            # Create new trait
            profile.traits[trait_type] = UserTrait(
                trait_type=trait_type,
                value=value,
                confidence=confidence,
                source=source,
                evidence=[evidence] if evidence else []
            )

        self._save_profile(profile)

    # ══════════════════════════════════════════════════════════════════════
    # Memory Storage and Retrieval
    # ══════════════════════════════════════════════════════════════════════

    def store_memory(
        self,
        user_id: str,
        content: str,
        category: MemoryCategory = MemoryCategory.CUSTOM,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        source: str = "explicit"
    ) -> UserMemory:
        """Store a memory for a user."""
        import uuid

        memory = UserMemory(
            id=str(uuid.uuid4()),
            category=category,
            content=content,
            tags=tags or [],
            importance=importance,
            source=source
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_memories
                (id, user_id, category, content, tags, importance,
                 created_at, last_accessed, access_count, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                user_id,
                memory.category.value,
                memory.content,
                json.dumps(memory.tags),
                memory.importance,
                memory.created_at,
                memory.last_accessed,
                memory.access_count,
                memory.source
            ))
            conn.commit()

        # Update cache
        if user_id not in self._memory_cache:
            self._memory_cache[user_id] = []
        self._memory_cache[user_id].append(memory)

        print(f"[UserProfile] Stored memory for {user_id}: {content[:50]}...")
        return memory

    def get_memories(
        self,
        user_id: str,
        category: Optional[MemoryCategory] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[UserMemory]:
        """Retrieve memories for a user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM user_memories WHERE user_id = ?"
            params = [user_id]

            if category:
                query += " AND category = ?"
                params.append(category.value)

            query += " ORDER BY importance DESC, last_accessed DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            memories = []
            for row in rows:
                memory = UserMemory(
                    id=row[0],
                    category=MemoryCategory(row[2]),
                    content=row[3],
                    tags=json.loads(row[4]),
                    importance=row[5],
                    created_at=row[6],
                    last_accessed=row[7],
                    access_count=row[8],
                    source=row[9]
                )

                # Filter by tags if specified
                if tags:
                    if any(tag in memory.tags for tag in tags):
                        memories.append(memory)
                else:
                    memories.append(memory)

            return memories

    def get_all_memories_formatted(self, user_id: str) -> str:
        """Get all memories formatted for context injection."""
        memories = self.get_memories(user_id, limit=50)

        if not memories:
            return ""

        # Group by category
        by_category: Dict[str, List[str]] = {}
        for memory in memories:
            cat = memory.category.value.upper()
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(f"• {memory.content}")

        lines = ["USER MEMORY CONTEXT:"]
        for category, items in by_category.items():
            lines.append(f"\n{category}:")
            lines.extend(items)

        return "\n".join(lines)

    # ══════════════════════════════════════════════════════════════════════
    # Message Analysis and Learning
    # ══════════════════════════════════════════════════════════════════════

    def analyze_message(
        self,
        user_id: str,
        message: str
    ) -> Tuple[Optional[UserMemory], Dict[str, Any]]:
        """
        Analyze a user message for:
        1. Explicit memory requests ("remember that I...")
        2. Implicit trait signals (communication style, expertise)

        Returns:
            Tuple of (stored_memory if explicit, detected_traits dict)
        """
        profile = self.get_or_create_profile(user_id)

        # Update interaction stats
        profile.total_messages += 1
        profile.avg_message_length = (
            (profile.avg_message_length * (profile.total_messages - 1) + len(message))
            / profile.total_messages
        )

        stored_memory = None
        detected_traits = {}

        # Check for explicit memory requests
        memory_content, category = self._extract_explicit_memory(message)
        if memory_content:
            stored_memory = self.store_memory(
                user_id=user_id,
                content=memory_content,
                category=category,
                source="explicit"
            )

        # Detect implicit traits
        detected_traits = self._detect_traits(message)
        for trait_type, value in detected_traits.items():
            self.update_profile_trait(
                user_id=user_id,
                trait_type=trait_type,
                value=value,
                source="detected",
                evidence=message[:100]
            )

        # Update adaptive settings based on traits
        self._update_adaptive_settings(profile)
        self._save_profile(profile)

        return stored_memory, detected_traits

    def _extract_explicit_memory(
        self,
        message: str
    ) -> Tuple[Optional[str], MemoryCategory]:
        """Extract explicit memory request from message."""
        message_lower = message.lower()

        for pattern in self.REMEMBER_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                # Clean up the content
                content = re.sub(r'^that\s+', '', content)
                content = content.rstrip('.')

                # Determine category
                category = self._categorize_memory(content)

                return content, category

        return None, MemoryCategory.CUSTOM

    def _categorize_memory(self, content: str) -> MemoryCategory:
        """Determine the category for a memory."""
        content_lower = content.lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return category

        return MemoryCategory.CUSTOM

    def _detect_traits(self, message: str) -> Dict[str, str]:
        """Detect implicit traits from message."""
        detected = {}
        message_lower = message.lower()

        # Check communication style preferences
        concise_score = sum(
            1 for p in self.TRAIT_PATTERNS["concise_preference"]
            if re.search(p, message_lower)
        )
        detailed_score = sum(
            1 for p in self.TRAIT_PATTERNS["detailed_preference"]
            if re.search(p, message_lower)
        )

        if concise_score > detailed_score and concise_score > 0:
            detected["communication_style"] = "concise"
        elif detailed_score > concise_score and detailed_score > 0:
            detected["communication_style"] = "detailed"

        # Check technical level
        technical_score = sum(
            1 for p in self.TRAIT_PATTERNS["technical_level"]
            if re.search(p, message_lower)
        )
        if technical_score >= 2:
            detected["technical_level"] = "high"

        # Detect formality from message structure
        if message.endswith('?') or len(message.split()) < 10:
            pass  # Neutral
        elif any(word in message_lower for word in ['please', 'kindly', 'would you']):
            detected["formality"] = "formal"
        elif any(word in message_lower for word in ['hey', 'yo', 'sup', 'gonna', 'wanna']):
            detected["formality"] = "casual"

        return detected

    def _update_adaptive_settings(self, profile: UserProfile):
        """Update adaptive settings based on accumulated traits."""
        # Update communication style
        if "communication_style" in profile.traits:
            style_trait = profile.traits["communication_style"]
            if style_trait.value == "concise" and style_trait.confidence > 0.3:
                profile.preferred_style = CommunicationStyle.CONCISE
                profile.detail_level = max(0.2, profile.detail_level - 0.1)
            elif style_trait.value == "detailed" and style_trait.confidence > 0.3:
                profile.preferred_style = CommunicationStyle.DETAILED
                profile.detail_level = min(0.9, profile.detail_level + 0.1)

        # Update formality
        if "formality" in profile.traits:
            formality_trait = profile.traits["formality"]
            if formality_trait.value == "formal":
                profile.formality_level = min(0.9, profile.formality_level + 0.1)
            elif formality_trait.value == "casual":
                profile.formality_level = max(0.2, profile.formality_level - 0.1)

    # ══════════════════════════════════════════════════════════════════════
    # Personality Adaptation
    # ══════════════════════════════════════════════════════════════════════

    def get_adaptation_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get personality adaptation context for response generation.

        Returns dict with:
        - style: Communication style recommendation
        - detail_level: How much detail to include (0-1)
        - formality: How formal to be (0-1)
        - user_context: Relevant memories to consider
        - tone_adjustments: Specific tone recommendations
        """
        profile = self.get_or_create_profile(user_id)
        memories = self.get_all_memories_formatted(user_id)

        # Determine tone adjustments
        tone_adjustments = []

        if profile.preferred_style == CommunicationStyle.CONCISE:
            tone_adjustments.append("Keep responses brief and to the point")
        elif profile.preferred_style == CommunicationStyle.DETAILED:
            tone_adjustments.append("Provide thorough explanations with examples")

        if profile.formality_level > 0.7:
            tone_adjustments.append("Use formal, professional language")
        elif profile.formality_level < 0.3:
            tone_adjustments.append("Be casual and conversational")

        # Check for specific preferences in memories
        pref_memories = self.get_memories(
            user_id,
            category=MemoryCategory.PREFERENCES,
            limit=5
        )
        for mem in pref_memories:
            tone_adjustments.append(f"User preference: {mem.content}")

        return {
            "style": profile.preferred_style.value,
            "detail_level": profile.detail_level,
            "formality": profile.formality_level,
            "user_context": memories,
            "tone_adjustments": tone_adjustments,
            "display_name": profile.display_name,
            "total_interactions": profile.total_messages
        }

    def format_adaptation_prompt(self, user_id: str) -> str:
        """Format adaptation context as a prompt injection."""
        context = self.get_adaptation_context(user_id)

        lines = ["\n--- USER ADAPTATION CONTEXT ---"]

        if context["display_name"]:
            lines.append(f"User: {context['display_name']}")

        lines.append(f"Communication Style: {context['style']}")
        lines.append(f"Detail Level: {context['detail_level']:.1f}/1.0")
        lines.append(f"Formality: {context['formality']:.1f}/1.0")

        if context["tone_adjustments"]:
            lines.append("\nTone Adjustments:")
            for adj in context["tone_adjustments"]:
                lines.append(f"  • {adj}")

        if context["user_context"]:
            lines.append(f"\n{context['user_context']}")

        lines.append("--- END ADAPTATION CONTEXT ---\n")

        return "\n".join(lines)


# Singleton instance
_memory_manager: Optional[AdaptiveMemoryManager] = None


def get_adaptive_memory() -> AdaptiveMemoryManager:
    """Get or create the singleton adaptive memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = AdaptiveMemoryManager()
    return _memory_manager
