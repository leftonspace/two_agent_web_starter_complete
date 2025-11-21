"""
Privacy controls for business memory.

PHASE 7.3: Filters sensitive data from being stored in memory.
Ensures GDPR compliance and prevents accidental storage of
passwords, SSNs, credit cards, API keys, etc.

Features:
    - Pattern-based sensitive data detection
    - Configurable sensitivity levels
    - Data export for GDPR compliance
    - Retention policy enforcement
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class PrivacyFilter:
    """
    Filter sensitive data from business memory.

    Prevents storage of:
        - Social Security Numbers
        - Credit card numbers
        - Passwords and API keys
        - Personal health information
        - Financial account numbers
    """

    # Regex patterns for sensitive data
    SENSITIVE_PATTERNS = {
        "ssn": r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "password": r"(?i)(password|passwd|pwd)[:\s=]+\S+",
        "api_key": r"(?i)(sk-|pk_live_|pk_test_|api[_-]?key[:\s=]+)\w+",
        "private_key": r"-----BEGIN (RSA |)PRIVATE KEY-----",
        "email_with_password": r"(?i)(email|username)[:\s=]+\S+\s+(password|pwd)[:\s=]+\S+",
        "phone": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "bitcoin": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b",
    }

    # Keywords that suggest sensitive content
    SENSITIVE_KEYWORDS = [
        "confidential",
        "secret",
        "private key",
        "password",
        "passcode",
        "pin code",
        "security question",
        "maiden name",
        "ssn",
        "social security",
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize privacy filter.

        Args:
            strict_mode: If True, blocks more aggressively
        """
        self.strict_mode = strict_mode

    def contains_sensitive_data(self, text: str) -> Optional[str]:
        """
        Check if text contains sensitive data.

        Args:
            text: Text to check

        Returns:
            Name of sensitive pattern found, or None if clean
        """
        if not text:
            return None

        # Check regex patterns
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return pattern_name

        # Check sensitive keywords (only in strict mode)
        if self.strict_mode:
            text_lower = text.lower()
            for keyword in self.SENSITIVE_KEYWORDS:
                if keyword in text_lower:
                    return f"keyword:{keyword}"

        return None

    def should_store(self, fact: Dict[str, Any]) -> bool:
        """
        Determine if fact should be stored.

        Args:
            fact: Fact dictionary with 'value' field

        Returns:
            True if safe to store, False if contains sensitive data
        """
        value = str(fact.get("value", ""))
        category = fact.get("category", "")

        # Check value for sensitive data
        if self.contains_sensitive_data(value):
            return False

        # Check category - some categories are inherently sensitive
        sensitive_categories = [
            "password",
            "secret",
            "private_key",
            "ssn",
            "credit_card",
        ]

        if any(s in category.lower() for s in sensitive_categories):
            return False

        return True

    def sanitize_text(self, text: str) -> str:
        """
        Remove sensitive data from text.

        Args:
            text: Text to sanitize

        Returns:
            Text with sensitive data redacted
        """
        sanitized = text

        # Replace each sensitive pattern with [REDACTED]
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            sanitized = re.sub(
                pattern,
                f"[REDACTED:{pattern_name.upper()}]",
                sanitized,
                flags=re.IGNORECASE
            )

        return sanitized

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email to validate

        Returns:
            True if valid email format
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def is_business_email(self, email: str) -> bool:
        """
        Check if email is likely a business email (not personal).

        Args:
            email: Email to check

        Returns:
            True if appears to be business email
        """
        if not self.validate_email(email):
            return False

        # Personal email providers
        personal_providers = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "mail.com",
        ]

        domain = email.split("@")[1].lower()
        return domain not in personal_providers


class RetentionPolicy:
    """
    Enforce data retention policies for GDPR compliance.

    Automatically expires old data based on configured retention periods.
    """

    def __init__(self, default_retention_days: int = 180):
        """
        Initialize retention policy.

        Args:
            default_retention_days: Default retention period in days
        """
        self.default_retention_days = default_retention_days

        # Category-specific retention periods
        self.retention_periods = {
            "company": 365,  # 1 year
            "team": 180,  # 6 months
            "preference": 365,  # 1 year
            "project": 90,  # 3 months
            "integration": 180,  # 6 months
            "general": 90,  # 3 months
        }

    def get_expiration_date(self, category: str) -> datetime:
        """
        Calculate expiration date for a category.

        Args:
            category: Fact category

        Returns:
            Expiration datetime
        """
        days = self.retention_periods.get(category, self.default_retention_days)
        return datetime.now() + timedelta(days=days)

    def is_expired(self, created_at: datetime, category: str) -> bool:
        """
        Check if data has expired.

        Args:
            created_at: When data was created
            category: Data category

        Returns:
            True if expired
        """
        expiration = created_at + timedelta(
            days=self.retention_periods.get(category, self.default_retention_days)
        )
        return datetime.now() > expiration


class DataExporter:
    """
    Export user data for GDPR compliance.

    Provides data portability as required by GDPR Article 20.
    """

    def export_to_json(self, data: Dict[str, Any]) -> str:
        """
        Export data to JSON format.

        Args:
            data: Data to export

        Returns:
            JSON string
        """
        import json
        return json.dumps(data, indent=2, default=str)

    def export_to_csv(self, data: List[Dict[str, Any]]) -> str:
        """
        Export data to CSV format.

        Args:
            data: List of records to export

        Returns:
            CSV string
        """
        if not data:
            return ""

        import csv
        import io

        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        return output.getvalue()


__all__ = ["PrivacyFilter", "RetentionPolicy", "DataExporter"]
