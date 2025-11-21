"""
Business memory manager.

PHASE 7.3: High-level interface for storing and retrieving business knowledge.
Coordinates fact extraction, privacy filtering, and database storage.

Usage:
    memory = BusinessMemory()
    await memory.learn_from_conversation("My company is Acme Corp")
    context = await memory.get_context_for_query("Send email to the team")
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from agent.business_memory.extractor import FactExtractor
from agent.business_memory.privacy import DataExporter, PrivacyFilter, RetentionPolicy
from agent.business_memory.schema import MemoryDatabase
from agent.llm import chat_json


class BusinessMemory:
    """
    Manage business knowledge learned from conversations.

    Provides automatic fact extraction, storage, retrieval,
    and context generation for queries.
    """

    def __init__(self, db_path: str = "data/business_memory.db", auto_learn: bool = True):
        """
        Initialize business memory system.

        Args:
            db_path: Path to SQLite database
            auto_learn: Whether to automatically extract facts from conversations
        """
        self.db = MemoryDatabase(db_path)
        self.extractor = FactExtractor()
        self.privacy_filter = PrivacyFilter(strict_mode=True)
        self.retention_policy = RetentionPolicy()
        self.data_exporter = DataExporter()
        self.auto_learn = auto_learn

    # ══════════════════════════════════════════════════════════════════════
    # Learning from Conversations
    # ══════════════════════════════════════════════════════════════════════

    async def learn_from_conversation(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict]] = None
    ):
        """
        Automatically extract and store facts from conversation.

        Called after each user message to learn continuously.

        Args:
            user_message: Current user message
            conversation_context: Recent conversation history
        """
        if not self.auto_learn:
            return

        # Extract facts using LLM
        facts = await self.extractor.extract_facts(
            user_message,
            conversation_context
        )

        # Store each valid, non-sensitive fact
        for fact in facts:
            await self._store_fact_with_validation(fact)

    async def _store_fact_with_validation(self, fact: Dict[str, Any]):
        """
        Store a fact with privacy filtering and conflict resolution.

        Args:
            fact: Fact to store
        """
        # Validate fact structure
        if not self.extractor.validate_fact(fact):
            return

        # Check privacy filter
        if not self.privacy_filter.should_store(fact):
            print(f"[BusinessMemory] Blocked sensitive data: {fact.get('category')}")
            return

        # Determine storage category
        storage_category = self.extractor.categorize_fact(fact)

        # Store based on category
        if storage_category == "company":
            await self._store_company_fact(fact)
        elif storage_category == "team":
            await self._store_team_fact(fact)
        elif storage_category == "preference":
            await self._store_preference_fact(fact)
        elif storage_category == "project":
            await self._store_project_fact(fact)
        else:
            # Store as generic fact
            self.db.store_fact(
                category=fact.get("category", "general"),
                fact=f"{fact['category']}: {fact['value']}",
                confidence=fact.get("confidence", 0.8),
                source="conversation"
            )

    async def _store_company_fact(self, fact: Dict[str, Any]):
        """Store company-related fact"""
        category = fact.get("category", "")
        value = fact.get("value", "")
        confidence = fact.get("confidence", 1.0)

        # Extract key from category (e.g., "company.name" -> "name")
        key = category.split(".", 1)[1] if "." in category else category

        self.db.store_company_info(
            key=key,
            value=value,
            confidence=confidence,
            source="conversation"
        )

    async def _store_team_fact(self, fact: Dict[str, Any]):
        """Store team member fact"""
        category = fact.get("category", "")
        value = fact.get("value", "")

        # Parse team member information
        if "person.name" in category:
            self.db.store_team_member(name=value)
        elif "person.email" in category:
            # Try to extract name from context or use email
            self.db.store_team_member(name=value.split("@")[0], email=value)
        elif "person.role" in category:
            # Store as generic fact for now (would need to link to person)
            self.db.store_fact(
                category="team",
                fact=f"Role: {value}",
                confidence=fact.get("confidence", 0.8)
            )

    async def _store_preference_fact(self, fact: Dict[str, Any]):
        """Store user preference"""
        category_full = fact.get("category", "")
        value = fact.get("value", "")
        confidence = fact.get("confidence", 1.0)

        # Extract category and key (e.g., "preference.tool" -> category="tool", key="primary")
        parts = category_full.split(".", 1)
        category = parts[1] if len(parts) > 1 else "general"
        key = category  # Use category as key for now

        self.db.store_preference(
            category=category,
            key=key,
            value=value,
            confidence=confidence
        )

    async def _store_project_fact(self, fact: Dict[str, Any]):
        """Store project fact"""
        self.db.store_fact(
            category="project",
            fact=f"{fact['category']}: {fact['value']}",
            confidence=fact.get("confidence", 0.8),
            source="conversation"
        )

    # ══════════════════════════════════════════════════════════════════════
    # Context Retrieval
    # ══════════════════════════════════════════════════════════════════════

    async def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """
        Get relevant business context for a user query.

        Args:
            query: User query or request

        Returns:
            Dictionary with relevant context (team members, preferences, etc.)
        """
        # Use LLM to understand what context is needed
        context_prompt = f"""User query: "{query}"

What business context would help fulfill this request?

Return JSON:
{{
  "needed": ["team_members", "company_info", "preferences", "projects"],
  "reasoning": "Brief explanation"
}}

Available context types:
- team_members: Names, emails, roles of team
- company_info: Company name, industry, size
- preferences: User preferences for tools, styles
- projects: Active projects and their status
"""

        try:
            needed = chat_json(
                role="employee",
                system_prompt="",
                user_content=context_prompt,
                model="gpt-4o-mini",
                temperature=0.1
            )
        except Exception:
            # If LLM fails, default to checking all context
            needed = {"needed": ["team_members", "preferences"]}

        # Retrieve relevant context
        context = {}

        needed_types = needed.get("needed", [])

        if "team_members" in needed_types:
            team = self.db.get_team_members()
            if team:
                context["team"] = team

        if "company_info" in needed_types:
            company = self.db.get_company_info()
            if company:
                context["company"] = company

        if "preferences" in needed_types:
            prefs = self.db.get_preferences()
            if prefs:
                context["preferences"] = prefs

        if "projects" in needed_types:
            projects = self.db.search_facts("project")
            if projects:
                context["projects"] = projects

        return context

    # ══════════════════════════════════════════════════════════════════════
    # Direct Accessors
    # ══════════════════════════════════════════════════════════════════════

    def get_team_members(self, department: str = None) -> List[Dict[str, Any]]:
        """Get all team members"""
        return self.db.get_team_members(department)

    def get_preferences(self, category: str = None) -> Dict[str, Any]:
        """Get user preferences"""
        return self.db.get_preferences(category)

    def get_company_info(self) -> Dict[str, Any]:
        """Get company information"""
        return self.db.get_company_info()

    def search_facts(self, query: str) -> List[Dict[str, Any]]:
        """Full-text search across all facts"""
        return self.db.search_facts(query)

    # ══════════════════════════════════════════════════════════════════════
    # Manual Memory Management
    # ══════════════════════════════════════════════════════════════════════

    async def store_manual_fact(self, fact_text: str):
        """
        Store a fact manually (user said "remember that...").

        Args:
            fact_text: User-provided fact
        """
        # Extract facts from the statement
        facts = await self.extractor.extract_facts(fact_text, [])

        for fact in facts:
            await self._store_fact_with_validation(fact)

    def delete_facts_about(self, topic: str) -> int:
        """
        Delete facts about a topic.

        Args:
            topic: Topic to delete facts about

        Returns:
            Number of facts deleted
        """
        # Search for relevant facts
        facts = self.db.search_facts(topic)

        # Delete each fact
        count = 0
        cursor = self.db.conn.cursor()
        for fact in facts:
            cursor.execute("DELETE FROM facts WHERE id = ?", (fact['id'],))
            cursor.execute("DELETE FROM facts_fts WHERE rowid = ?", (fact['id'],))
            count += 1

        self.db.conn.commit()
        return count

    def get_all_facts(self) -> Dict[str, Any]:
        """Get summary of all stored facts"""
        return {
            "company": self.db.get_company_info(),
            "team": self.db.get_team_members(),
            "preferences": self.db.get_preferences(),
            "fact_count": len(self.db._get_all_facts())
        }

    def clear_all(self):
        """Clear all stored data (GDPR right to be forgotten)"""
        self.db.clear_all_data()

    # ══════════════════════════════════════════════════════════════════════
    # GDPR Compliance
    # ══════════════════════════════════════════════════════════════════════

    def export_data(self, format: str = "json") -> str:
        """
        Export all data for GDPR compliance.

        Args:
            format: Export format ("json" or "csv")

        Returns:
            Exported data as string
        """
        data = self.db.export_all_data()

        if format == "json":
            return self.data_exporter.export_to_json(data)
        elif format == "csv":
            # Flatten data for CSV
            all_records = []
            for key, records in data.items():
                if isinstance(records, list):
                    all_records.extend(records)
            return self.data_exporter.export_to_csv(all_records)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def close(self):
        """Close database connection"""
        self.db.close()


__all__ = ["BusinessMemory"]
