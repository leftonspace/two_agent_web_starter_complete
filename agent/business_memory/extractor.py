"""
Automatic fact extraction from conversations.

PHASE 7.3: Uses LLM to identify and extract business facts from
user messages without explicit commands. Learns continuously.

Fact Types Extracted:
    - Company information (name, industry, size)
    - Team members (names, emails, roles)
    - Preferences (tools, styles, workflows)
    - Projects (names, statuses, paths)
    - Integrations (services, accounts)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from agent.llm import chat_json


class FactExtractor:
    """
    Extract structured facts from conversation messages.

    Uses LLM to identify business-relevant information
    without requiring explicit "remember that" commands.
    """

    def __init__(self):
        """Initialize fact extractor"""
        self.extraction_model = "gpt-4o-mini"  # Faster, cheaper for extraction

    async def extract_facts(
        self,
        message: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract structured facts from user message.

        Args:
            message: Current user message
            conversation_context: Recent conversation history

        Returns:
            List of extracted facts with type, category, value, confidence
        """
        # Build context string from recent messages
        context_str = ""
        if conversation_context:
            context_str = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in conversation_context[-5:]
            ])

        prompt = f"""Extract business facts from this conversation.

CONVERSATION CONTEXT:
{context_str}

CURRENT MESSAGE: "{message}"

Extract any of the following fact types:

1. COMPANY INFO
   - company.name: "Acme Corp"
   - company.industry: "Software"
   - company.size: "50 employees"
   - company.location: "San Francisco"

2. TEAM MEMBERS
   - person.name: "John Doe"
   - person.email: "john@acme.com"
   - person.role: "CFO"
   - person.department: "Finance"

3. PREFERENCES
   - preference.tool: "Slack" (for team communication)
   - preference.style: "professional" (email tone)
   - preference.hosting: "Vercel" (for deployments)
   - preference.framework: "React"

4. PROJECTS
   - project.name: "Website Redesign"
   - project.status: "in progress"
   - project.deadline: "Q4 2025"

5. INTEGRATIONS
   - integration.service: "GitHub"
   - integration.account: "@acmecorp"
   - integration.api: "enabled"

Return JSON array of facts:
[
  {{
    "type": "company|person|preference|project|integration|other",
    "category": "company.name",
    "value": "Acme Corp",
    "confidence": 0.9,
    "reasoning": "User explicitly stated company name"
  }}
]

Guidelines:
- Only extract EXPLICIT facts stated by the user
- Don't infer or assume information
- Confidence: 1.0 = explicit mention, 0.8 = strong context, 0.6 = weak implication
- Return empty array [] if no facts found
- Don't extract sensitive data (passwords, SSN, credit cards)
"""

        try:
            response = chat_json(
                role="employee",
                system_prompt="",
                user_content=prompt,
                model=self.extraction_model,
                temperature=0.1
            )

            # Ensure response is a list
            if isinstance(response, dict) and "facts" in response:
                facts = response["facts"]
            elif isinstance(response, list):
                facts = response
            else:
                facts = []

            return facts

        except Exception as e:
            # Log error but don't crash
            print(f"[FactExtractor] Extraction failed: {e}")
            return []

    async def detect_conflicts(
        self,
        new_fact: Dict[str, Any],
        existing_facts: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if new fact conflicts with existing facts.

        Args:
            new_fact: Newly extracted fact
            existing_facts: Previously stored facts

        Returns:
            Conflicting fact if found, None otherwise
        """
        for existing in existing_facts:
            # Check if same category but different value
            if (existing.get("category") == new_fact.get("category") and
                existing.get("value") != new_fact.get("value")):
                return existing

        return None

    async def resolve_conflict(
        self,
        new_fact: Dict[str, Any],
        existing_fact: Dict[str, Any]
    ) -> str:
        """
        Determine how to resolve a conflict between facts.

        Args:
            new_fact: New fact
            existing_fact: Existing conflicting fact

        Returns:
            Resolution strategy: "keep_new", "keep_existing", "ask_user"
        """
        # If new fact has higher confidence, prefer it
        new_conf = new_fact.get("confidence", 0.5)
        existing_conf = existing_fact.get("confidence", 0.5)

        confidence_diff = new_conf - existing_conf

        if confidence_diff > 0.2:
            return "keep_new"
        elif confidence_diff < -0.2:
            return "keep_existing"
        else:
            # Similar confidence - ask user
            return "ask_user"

    def validate_fact(self, fact: Dict[str, Any]) -> bool:
        """
        Validate that a fact has required fields and sensible values.

        Args:
            fact: Fact to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not all(k in fact for k in ["type", "category", "value"]):
            return False

        # Check confidence range
        if "confidence" in fact:
            if not (0.0 <= fact["confidence"] <= 1.0):
                return False

        # Check value is not empty
        if not fact["value"] or not str(fact["value"]).strip():
            return False

        return True

    def categorize_fact(self, fact: Dict[str, Any]) -> str:
        """
        Determine storage category for a fact.

        Args:
            fact: Fact to categorize

        Returns:
            Storage category: "company", "team", "preference", "project", etc.
        """
        fact_type = fact.get("type", "other")
        category = fact.get("category", "")

        # Map fact types to storage categories
        if fact_type == "company" or category.startswith("company."):
            return "company"
        elif fact_type == "person" or category.startswith("person."):
            return "team"
        elif fact_type == "preference" or category.startswith("preference."):
            return "preference"
        elif fact_type == "project" or category.startswith("project."):
            return "project"
        elif fact_type == "integration" or category.startswith("integration."):
            return "integration"
        else:
            return "general"


__all__ = ["FactExtractor"]
