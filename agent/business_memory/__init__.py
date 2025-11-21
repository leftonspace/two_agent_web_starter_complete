"""
Business Memory System for System-1.2

PHASE 7.3: Persistent memory that learns facts about the user's business
from conversations and provides relevant context automatically.

Modules:
    - schema: Database schema for storing business knowledge
    - extractor: Automatic fact extraction from conversations
    - manager: High-level memory management interface
    - privacy: Privacy controls and sensitive data filtering
"""

from agent.business_memory.manager import BusinessMemory
from agent.business_memory.schema import MemoryDatabase
from agent.business_memory.extractor import FactExtractor
from agent.business_memory.privacy import PrivacyFilter

__all__ = [
    "BusinessMemory",
    "MemoryDatabase",
    "FactExtractor",
    "PrivacyFilter",
]
