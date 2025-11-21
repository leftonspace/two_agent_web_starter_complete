"""
Test business memory system.

PHASE 7.3: Tests for automatic fact learning, privacy filtering,
database storage, and GDPR compliance.

Run: pytest agent/tests/test_business_memory.py -v
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agent.business_memory.extractor import FactExtractor
from agent.business_memory.manager import BusinessMemory
from agent.business_memory.privacy import DataExporter, PrivacyFilter, RetentionPolicy
from agent.business_memory.schema import MemoryDatabase


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_db(temp_db):
    """Create MemoryDatabase instance"""
    return MemoryDatabase(temp_db)


@pytest.fixture
def business_memory(temp_db):
    """Create BusinessMemory instance"""
    return BusinessMemory(db_path=temp_db, auto_learn=True)


@pytest.fixture
def privacy_filter():
    """Create PrivacyFilter instance"""
    return PrivacyFilter(strict_mode=True)


@pytest.fixture
def fact_extractor():
    """Create FactExtractor instance"""
    return FactExtractor()


# ══════════════════════════════════════════════════════════════════════
# MemoryDatabase Tests
# ══════════════════════════════════════════════════════════════════════


class TestMemoryDatabase:
    """Test database schema and operations"""

    def test_database_initialization(self, memory_db):
        """Test database tables are created"""
        cursor = memory_db.conn.cursor()

        # Check that all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            "company_info", "team_members", "projects", "preferences",
            "integrations", "facts", "relationships"
        }

        assert expected_tables.issubset(tables)

    def test_store_company_info(self, memory_db):
        """Test storing company information"""
        memory_db.store_company_info("name", "Acme Corp", confidence=1.0)

        info = memory_db.get_company_info("name")
        assert info is not None
        assert info["value"] == "Acme Corp"
        assert info["confidence"] == 1.0

    def test_update_company_info(self, memory_db):
        """Test updating existing company information"""
        memory_db.store_company_info("name", "Acme Corp", confidence=0.8)
        memory_db.store_company_info("name", "Acme Corporation", confidence=1.0)

        info = memory_db.get_company_info("name")
        assert info["value"] == "Acme Corporation"
        assert info["confidence"] == 1.0

    def test_store_team_member(self, memory_db):
        """Test storing team member"""
        memory_db.store_team_member(
            name="John Doe",
            email="john@acme.com",
            role="CFO",
            department="Finance"
        )

        members = memory_db.get_team_members()
        assert len(members) == 1
        assert members[0]["name"] == "John Doe"
        assert members[0]["email"] == "john@acme.com"
        assert members[0]["role"] == "CFO"

    def test_store_preference(self, memory_db):
        """Test storing user preference"""
        memory_db.store_preference(
            category="tool",
            key="communication",
            value="Slack",
            confidence=0.9
        )

        prefs = memory_db.get_preferences("tool")
        assert "communication" in prefs
        assert prefs["communication"]["value"] == "Slack"

    def test_store_and_search_facts(self, memory_db):
        """Test storing and searching facts"""
        memory_db.store_fact(
            category="project",
            fact="Building website with React and TypeScript",
            confidence=0.9
        )

        results = memory_db.search_facts("React")
        assert len(results) > 0
        assert "React" in results[0]["fact"]

    def test_full_text_search(self, memory_db):
        """Test full-text search across facts"""
        memory_db.store_fact("project", "Website redesign project", 0.9)
        memory_db.store_fact("project", "Mobile app development", 0.8)
        memory_db.store_fact("team", "Hiring React developers", 0.7)

        results = memory_db.search_facts("project")
        assert len(results) >= 2

        results = memory_db.search_facts("React")
        assert len(results) >= 1

    def test_export_all_data(self, memory_db):
        """Test GDPR data export"""
        memory_db.store_company_info("name", "Acme Corp")
        memory_db.store_team_member("Jane Smith", "jane@acme.com")
        memory_db.store_preference("tool", "email", "Gmail")
        memory_db.store_fact("general", "Uses Vercel for hosting")

        data = memory_db.export_all_data()

        assert "company_info" in data
        assert "team_members" in data
        assert "preferences" in data
        assert "facts" in data
        assert "export_timestamp" in data

    def test_clear_all_data(self, memory_db):
        """Test GDPR right to be forgotten"""
        memory_db.store_company_info("name", "Acme Corp")
        memory_db.store_team_member("Jane Smith", "jane@acme.com")

        memory_db.clear_all_data()

        assert len(memory_db.get_company_info()) == 0
        assert len(memory_db.get_team_members()) == 0


# ══════════════════════════════════════════════════════════════════════
# PrivacyFilter Tests
# ══════════════════════════════════════════════════════════════════════


class TestPrivacyFilter:
    """Test privacy filtering and sensitive data detection"""

    def test_detect_ssn(self, privacy_filter):
        """Test SSN detection"""
        text = "My SSN is 123-45-6789"
        result = privacy_filter.contains_sensitive_data(text)
        assert result == "ssn"

    def test_detect_credit_card(self, privacy_filter):
        """Test credit card detection"""
        text = "Card number: 4532 1234 5678 9012"
        result = privacy_filter.contains_sensitive_data(text)
        assert result == "credit_card"

    def test_detect_password(self, privacy_filter):
        """Test password detection"""
        text = "My password is: hunter2"
        result = privacy_filter.contains_sensitive_data(text)
        assert result == "password"

    def test_detect_api_key(self, privacy_filter):
        """Test API key detection"""
        text = "Use this key: sk-abc123xyz"
        result = privacy_filter.contains_sensitive_data(text)
        assert result == "api_key"

    def test_no_sensitive_data(self, privacy_filter):
        """Test clean text passes"""
        text = "Our company name is Acme Corp and we use Slack"
        result = privacy_filter.contains_sensitive_data(text)
        assert result is None

    def test_should_store_safe_fact(self, privacy_filter):
        """Test safe fact is allowed"""
        fact = {
            "category": "company.name",
            "value": "Acme Corp"
        }
        assert privacy_filter.should_store(fact) is True

    def test_should_block_sensitive_fact(self, privacy_filter):
        """Test sensitive fact is blocked"""
        fact = {
            "category": "general",
            "value": "Password is hunter2"
        }
        assert privacy_filter.should_store(fact) is False

    def test_sanitize_text(self, privacy_filter):
        """Test text sanitization"""
        text = "My SSN is 123-45-6789 and card is 4532-1234-5678-9012"
        sanitized = privacy_filter.sanitize_text(text)

        assert "123-45-6789" not in sanitized
        assert "4532-1234-5678-9012" not in sanitized
        assert "[REDACTED:SSN]" in sanitized
        assert "[REDACTED:CREDIT_CARD]" in sanitized

    def test_validate_email(self, privacy_filter):
        """Test email validation"""
        assert privacy_filter.validate_email("john@acme.com") is True
        assert privacy_filter.validate_email("invalid-email") is False
        assert privacy_filter.validate_email("@acme.com") is False

    def test_is_business_email(self, privacy_filter):
        """Test business email detection"""
        assert privacy_filter.is_business_email("john@acme.com") is True
        assert privacy_filter.is_business_email("john@gmail.com") is False
        assert privacy_filter.is_business_email("jane@company.io") is True


# ══════════════════════════════════════════════════════════════════════
# FactExtractor Tests
# ══════════════════════════════════════════════════════════════════════


class TestFactExtractor:
    """Test automatic fact extraction"""

    @pytest.mark.asyncio
    async def test_extract_facts_mock(self, fact_extractor):
        """Test fact extraction with mocked LLM"""
        mock_response = [
            {
                "type": "company",
                "category": "company.name",
                "value": "Acme Corp",
                "confidence": 1.0,
                "reasoning": "User explicitly stated company name"
            }
        ]

        with patch('agent.business_memory.extractor.chat_json', return_value=mock_response):
            facts = await fact_extractor.extract_facts(
                "My company is Acme Corp",
                []
            )

        assert len(facts) == 1
        assert facts[0]["category"] == "company.name"
        assert facts[0]["value"] == "Acme Corp"

    def test_validate_fact_valid(self, fact_extractor):
        """Test fact validation with valid fact"""
        fact = {
            "type": "company",
            "category": "company.name",
            "value": "Acme Corp",
            "confidence": 0.9
        }
        assert fact_extractor.validate_fact(fact) is True

    def test_validate_fact_missing_fields(self, fact_extractor):
        """Test fact validation with missing fields"""
        fact = {
            "category": "company.name",
            "value": "Acme Corp"
            # Missing 'type'
        }
        assert fact_extractor.validate_fact(fact) is False

    def test_validate_fact_empty_value(self, fact_extractor):
        """Test fact validation with empty value"""
        fact = {
            "type": "company",
            "category": "company.name",
            "value": "",
            "confidence": 0.9
        }
        assert fact_extractor.validate_fact(fact) is False

    def test_categorize_fact(self, fact_extractor):
        """Test fact categorization"""
        assert fact_extractor.categorize_fact({"type": "company", "category": "company.name"}) == "company"
        assert fact_extractor.categorize_fact({"type": "person", "category": "person.email"}) == "team"
        assert fact_extractor.categorize_fact({"type": "preference", "category": "preference.tool"}) == "preference"
        assert fact_extractor.categorize_fact({"type": "project", "category": "project.name"}) == "project"
        assert fact_extractor.categorize_fact({"type": "other", "category": "general"}) == "general"


# ══════════════════════════════════════════════════════════════════════
# BusinessMemory Integration Tests
# ══════════════════════════════════════════════════════════════════════


class TestBusinessMemory:
    """Test high-level BusinessMemory interface"""

    @pytest.mark.asyncio
    async def test_learn_from_conversation_mock(self, business_memory):
        """Test learning facts from conversation"""
        mock_facts = [
            {
                "type": "company",
                "category": "company.name",
                "value": "Acme Corp",
                "confidence": 1.0
            }
        ]

        with patch.object(business_memory.extractor, 'extract_facts', return_value=mock_facts):
            await business_memory.learn_from_conversation(
                "My company is Acme Corp",
                []
            )

        company_info = business_memory.get_company_info()
        assert "name" in company_info
        assert company_info["name"]["value"] == "Acme Corp"

    @pytest.mark.asyncio
    async def test_privacy_filter_blocks_sensitive(self, business_memory):
        """Test privacy filter blocks sensitive data"""
        mock_facts = [
            {
                "type": "general",
                "category": "credentials",
                "value": "Password is hunter2",
                "confidence": 0.9
            }
        ]

        with patch.object(business_memory.extractor, 'extract_facts', return_value=mock_facts):
            await business_memory.learn_from_conversation(
                "Password is hunter2",
                []
            )

        # Sensitive fact should be blocked
        facts = business_memory.search_facts("password")
        assert len(facts) == 0

    @pytest.mark.asyncio
    async def test_get_context_for_query_mock(self, business_memory):
        """Test context retrieval for query"""
        # Store some facts
        business_memory.db.store_company_info("name", "Acme Corp")
        business_memory.db.store_team_member("John Doe", "john@acme.com", "CFO")
        business_memory.db.store_preference("tool", "communication", "Slack")

        mock_needed = {
            "needed": ["team_members", "company_info"],
            "reasoning": "Need team and company info to send email"
        }

        with patch('agent.business_memory.manager.chat_json', return_value=mock_needed):
            context = await business_memory.get_context_for_query(
                "Send email to the CFO"
            )

        assert "team" in context
        assert "company" in context
        assert len(context["team"]) == 1
        assert context["team"][0]["name"] == "John Doe"

    def test_get_team_members(self, business_memory):
        """Test getting team members"""
        business_memory.db.store_team_member("John Doe", "john@acme.com", "CFO")
        business_memory.db.store_team_member("Jane Smith", "jane@acme.com", "CTO")

        members = business_memory.get_team_members()
        assert len(members) == 2
        assert any(m["name"] == "John Doe" for m in members)
        assert any(m["name"] == "Jane Smith" for m in members)

    def test_get_preferences(self, business_memory):
        """Test getting preferences"""
        business_memory.db.store_preference("tool", "email", "Gmail")
        business_memory.db.store_preference("tool", "chat", "Slack")

        prefs = business_memory.get_preferences()
        assert "tool" in prefs
        assert prefs["tool"]["email"]["value"] == "Gmail"
        assert prefs["tool"]["chat"]["value"] == "Slack"

    def test_search_facts(self, business_memory):
        """Test searching facts"""
        business_memory.db.store_fact("project", "Building React website", 0.9)
        business_memory.db.store_fact("project", "Mobile app in development", 0.8)

        results = business_memory.search_facts("React")
        assert len(results) > 0
        assert "React" in results[0]["fact"]

    def test_export_data_json(self, business_memory):
        """Test JSON data export"""
        business_memory.db.store_company_info("name", "Acme Corp")

        json_export = business_memory.export_data("json")
        assert "Acme Corp" in json_export
        assert "company_info" in json_export

    def test_clear_all(self, business_memory):
        """Test clearing all memory"""
        business_memory.db.store_company_info("name", "Acme Corp")
        business_memory.db.store_team_member("John Doe", "john@acme.com")

        business_memory.clear_all()

        assert len(business_memory.get_company_info()) == 0
        assert len(business_memory.get_team_members()) == 0

    def test_delete_facts_about(self, business_memory):
        """Test deleting facts about a topic"""
        business_memory.db.store_fact("project", "Building React website", 0.9)
        business_memory.db.store_fact("project", "Using TypeScript", 0.8)
        business_memory.db.store_fact("team", "Hiring developers", 0.7)

        deleted = business_memory.delete_facts_about("React")
        assert deleted > 0

        # React fact should be gone
        results = business_memory.search_facts("React")
        assert len(results) == 0

        # Other facts should remain
        results = business_memory.search_facts("TypeScript")
        assert len(results) > 0


# ══════════════════════════════════════════════════════════════════════
# GDPR Compliance Tests
# ══════════════════════════════════════════════════════════════════════


class TestGDPRCompliance:
    """Test GDPR compliance features"""

    def test_data_export_json(self):
        """Test data export in JSON format"""
        exporter = DataExporter()
        data = {
            "company_info": {"name": "Acme"},
            "team_members": [{"name": "John"}]
        }

        json_str = exporter.export_to_json(data)
        assert "Acme" in json_str
        assert "John" in json_str

    def test_data_export_csv(self):
        """Test data export in CSV format"""
        exporter = DataExporter()
        data = [
            {"name": "John", "email": "john@acme.com"},
            {"name": "Jane", "email": "jane@acme.com"}
        ]

        csv_str = exporter.export_to_csv(data)
        assert "name,email" in csv_str
        assert "John" in csv_str
        assert "jane@acme.com" in csv_str

    def test_retention_policy(self):
        """Test retention policy expiration dates"""
        policy = RetentionPolicy()

        # Check different retention periods
        company_exp = policy.get_expiration_date("company")
        team_exp = policy.get_expiration_date("team")
        general_exp = policy.get_expiration_date("general")

        # Company (365 days) should expire later than general (90 days)
        assert company_exp > general_exp


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_extract_facts_llm_error(self, fact_extractor):
        """Test graceful handling of LLM errors"""
        with patch('agent.business_memory.extractor.chat_json', side_effect=Exception("LLM error")):
            facts = await fact_extractor.extract_facts("test message", [])

        # Should return empty list on error, not crash
        assert facts == []

    @pytest.mark.asyncio
    async def test_get_context_llm_error(self, business_memory):
        """Test context retrieval with LLM error"""
        with patch('agent.business_memory.manager.chat_json', side_effect=Exception("LLM error")):
            context = await business_memory.get_context_for_query("test query")

        # Should return context even if LLM fails (fallback behavior)
        assert isinstance(context, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
