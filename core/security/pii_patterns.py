"""
PHASE 7.2: PII Detection Patterns

Comprehensive regex patterns for detecting Personally Identifiable Information
and sensitive data in text outputs.

Patterns are designed for high precision to minimize false positives while
catching common formats of sensitive data.

Usage:
    from core.security.pii_patterns import PII_PATTERNS, API_KEY_PATTERNS

    for pattern_type, regex in PII_PATTERNS.items():
        if regex.search(text):
            print(f"Found {pattern_type}")
"""

from __future__ import annotations

import re
from typing import Dict, Pattern


# ============================================================================
# Social Security Number Patterns
# ============================================================================

# SSN formats:
# - XXX-XX-XXXX (standard)
# - XXX XX XXXX (space separated)
# - XXXXXXXXX (no separator, 9 digits - must be careful here)
SSN_PATTERN = re.compile(
    r"""
    \b
    (?!000|666|9\d{2})              # SSN cannot start with 000, 666, or 9xx
    (?P<area>\d{3})                 # Area number (3 digits)
    [-\s]?                          # Optional separator
    (?!00)(?P<group>\d{2})          # Group number (2 digits, not 00)
    [-\s]?                          # Optional separator
    (?!0000)(?P<serial>\d{4})       # Serial number (4 digits, not 0000)
    \b
    """,
    re.VERBOSE
)

# Alternative strict SSN pattern (with dashes only)
SSN_STRICT_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


# ============================================================================
# Credit Card Patterns
# ============================================================================

# Credit card formats (13-19 digits with optional separators)
# Covers: Visa, Mastercard, Amex, Discover, JCB, etc.
CREDIT_CARD_PATTERN = re.compile(
    r"""
    \b
    (?:
        # Visa: starts with 4, 13 or 16 digits
        4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,4}
        |
        # Mastercard: starts with 51-55 or 2221-2720, 16 digits
        (?:5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|27[01]\d|2720)
        [-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
        |
        # Amex: starts with 34 or 37, 15 digits
        3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}
        |
        # Discover: starts with 6011, 644-649, 65, 16 digits
        (?:6011|64[4-9]\d|65\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
        |
        # JCB: starts with 3528-3589, 16 digits
        35(?:2[89]|[3-8]\d)[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
        |
        # Diners Club: starts with 300-305, 36, 38, 14 digits
        (?:30[0-5]\d|3[68]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{2}
        |
        # Generic 16-digit pattern (fallback)
        \d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}
    )
    \b
    """,
    re.VERBOSE
)


# ============================================================================
# Phone Number Patterns
# ============================================================================

# US Phone number formats:
# - (XXX) XXX-XXXX
# - XXX-XXX-XXXX
# - XXX.XXX.XXXX
# - +1 XXX XXX XXXX
# - 1-XXX-XXX-XXXX
US_PHONE_PATTERN = re.compile(
    r"""
    (?:
        # With country code
        (?:\+?1[-.\s]?)?
        # Area code in parentheses or not
        \(?([2-9]\d{2})\)?         # Area code (starts with 2-9)
        [-.\s]?
        # Exchange
        ([2-9]\d{2})               # Exchange (starts with 2-9)
        [-.\s]?
        # Subscriber number
        (\d{4})
    )
    (?!\d)                         # Not followed by more digits
    """,
    re.VERBOSE
)


# ============================================================================
# Email Patterns
# ============================================================================

EMAIL_PATTERN = re.compile(
    r"""
    \b
    [A-Za-z0-9._%+-]+              # Local part
    @
    [A-Za-z0-9.-]+                 # Domain
    \.
    [A-Za-z]{2,}                   # TLD
    \b
    """,
    re.VERBOSE | re.IGNORECASE
)


# ============================================================================
# API Key Patterns
# ============================================================================

API_KEY_PATTERNS: Dict[str, Pattern] = {
    # OpenAI
    "openai": re.compile(r"\bsk-[a-zA-Z0-9]{20,}"),
    "openai_project": re.compile(r"\bsk-proj-[a-zA-Z0-9_-]{20,}"),

    # Anthropic
    "anthropic": re.compile(r"\bsk-ant-[a-zA-Z0-9_-]{20,}"),

    # AWS
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aws_secret_key": re.compile(r"\b[A-Za-z0-9/+=]{40}\b"),

    # GitHub
    "github_pat": re.compile(r"\bghp_[a-zA-Z0-9]{36,}\b"),
    "github_oauth": re.compile(r"\bgho_[a-zA-Z0-9]{36,}\b"),
    "github_app": re.compile(r"\bghs_[a-zA-Z0-9]{36,}\b"),

    # Google
    "google_api": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),

    # Stripe
    "stripe_live": re.compile(r"\bsk_live_[0-9a-zA-Z]{24,}\b"),
    "stripe_test": re.compile(r"\bsk_test_[0-9a-zA-Z]{24,}\b"),
    "stripe_restricted": re.compile(r"\brk_live_[0-9a-zA-Z]{24,}\b"),

    # Slack
    "slack_bot": re.compile(r"\bxoxb-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24}\b"),
    "slack_user": re.compile(r"\bxoxp-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24}\b"),

    # Twilio
    "twilio_api": re.compile(r"\bSK[0-9a-fA-F]{32}\b"),
    "twilio_account": re.compile(r"\bAC[0-9a-fA-F]{32}\b"),

    # SendGrid
    "sendgrid": re.compile(r"\bSG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}\b"),

    # Generic patterns (high confidence)
    "generic_api_key": re.compile(r"(?i)api[_-]?key[:\s=]+['\"]?([a-zA-Z0-9_-]{20,})['\"]?"),
    "generic_secret": re.compile(r"(?i)secret[_-]?key[:\s=]+['\"]?([a-zA-Z0-9_-]{20,})['\"]?"),
    "bearer_token": re.compile(r"\bBearer\s+[a-zA-Z0-9_\-\.=]{20,}\b", re.IGNORECASE),

    # Private keys
    "private_key_rsa": re.compile(r"-----BEGIN RSA PRIVATE KEY-----"),
    "private_key_ec": re.compile(r"-----BEGIN EC PRIVATE KEY-----"),
    "private_key_openssh": re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"),
    "private_key_generic": re.compile(r"-----BEGIN PRIVATE KEY-----"),
}


# ============================================================================
# Additional Sensitive Data Patterns
# ============================================================================

# IP Addresses (IPv4)
IPV4_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
)

# IPv6 Addresses (simplified)
IPV6_PATTERN = re.compile(
    r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
    r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|"
    r"\b::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b"
)

# Bitcoin addresses
BITCOIN_PATTERN = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")

# Ethereum addresses
ETHEREUM_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

# Date of Birth (MM/DD/YYYY, MM-DD-YYYY, etc.)
DOB_PATTERN = re.compile(
    r"\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b"
)

# Passport numbers (US format)
PASSPORT_PATTERN = re.compile(r"\b[A-Z]\d{8}\b")

# Bank account numbers (generic, 8-17 digits)
BANK_ACCOUNT_PATTERN = re.compile(r"\b\d{8,17}\b")

# Routing numbers (US, 9 digits with ABA validation prefix)
ROUTING_NUMBER_PATTERN = re.compile(r"\b[0-3]\d{8}\b")


# ============================================================================
# Combined PII Patterns Dictionary
# ============================================================================

PII_PATTERNS: Dict[str, Pattern] = {
    "ssn": SSN_PATTERN,
    "ssn_strict": SSN_STRICT_PATTERN,
    "credit_card": CREDIT_CARD_PATTERN,
    "phone_us": US_PHONE_PATTERN,
    "email": EMAIL_PATTERN,
    "ipv4": IPV4_PATTERN,
    "bitcoin": BITCOIN_PATTERN,
    "ethereum": ETHEREUM_PATTERN,
    "dob": DOB_PATTERN,
    "passport": PASSPORT_PATTERN,
}


# ============================================================================
# Luhn Algorithm for Credit Card Validation
# ============================================================================


def luhn_checksum(card_number: str) -> bool:
    """
    Validate credit card number using Luhn algorithm.

    The Luhn algorithm (mod 10) is used to validate credit card numbers,
    IMEI numbers, and other identification numbers.

    Args:
        card_number: Credit card number (digits only)

    Returns:
        True if valid according to Luhn algorithm

    Examples:
        >>> luhn_checksum("4532015112830366")
        True
        >>> luhn_checksum("4532015112830367")
        False
    """
    # Remove any non-digit characters
    digits = "".join(c for c in card_number if c.isdigit())

    if len(digits) < 13 or len(digits) > 19:
        return False

    # Luhn algorithm
    total = 0
    reverse_digits = digits[::-1]

    for i, digit in enumerate(reverse_digits):
        n = int(digit)
        if i % 2 == 1:  # Double every second digit from right
            n *= 2
            if n > 9:
                n -= 9
        total += n

    return total % 10 == 0


def extract_card_digits(text: str) -> str:
    """
    Extract digits from potential credit card match.

    Args:
        text: Text containing potential card number

    Returns:
        Digits only string
    """
    return "".join(c for c in text if c.isdigit())


# ============================================================================
# Script Detection for Anomaly Detection
# ============================================================================

# Unicode script ranges for detecting unexpected characters
SCRIPT_RANGES: Dict[str, list] = {
    "latin": [
        (0x0041, 0x007A),  # Basic Latin
        (0x00C0, 0x00FF),  # Latin-1 Supplement
        (0x0100, 0x017F),  # Latin Extended-A
        (0x0180, 0x024F),  # Latin Extended-B
    ],
    "cyrillic": [
        (0x0400, 0x04FF),  # Cyrillic
        (0x0500, 0x052F),  # Cyrillic Supplement
    ],
    "chinese": [
        (0x4E00, 0x9FFF),  # CJK Unified Ideographs
        (0x3400, 0x4DBF),  # CJK Unified Ideographs Extension A
    ],
    "japanese": [
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
    ],
    "korean": [
        (0xAC00, 0xD7AF),  # Hangul Syllables
        (0x1100, 0x11FF),  # Hangul Jamo
    ],
    "arabic": [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
    ],
    "thai": [
        (0x0E00, 0x0E7F),  # Thai
    ],
    "hebrew": [
        (0x0590, 0x05FF),  # Hebrew
    ],
    "greek": [
        (0x0370, 0x03FF),  # Greek and Coptic
    ],
}

# Common punctuation and symbols (allowed in all scripts)
COMMON_CHARS = set(" \t\n\r.,;:!?\"'`()[]{}|\\/@#$%^&*-_=+<>~0123456789")


def get_char_script(char: str) -> str:
    """
    Determine the script of a Unicode character.

    Args:
        char: Single character

    Returns:
        Script name or "unknown"
    """
    if char in COMMON_CHARS:
        return "common"

    code_point = ord(char)

    for script_name, ranges in SCRIPT_RANGES.items():
        for start, end in ranges:
            if start <= code_point <= end:
                return script_name

    return "unknown"


def analyze_script_distribution(text: str) -> Dict[str, float]:
    """
    Analyze the distribution of scripts in text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary mapping script names to their percentage
    """
    if not text:
        return {}

    script_counts: Dict[str, int] = {}
    total_chars = 0

    for char in text:
        script = get_char_script(char)
        if script != "common":
            script_counts[script] = script_counts.get(script, 0) + 1
            total_chars += 1

    if total_chars == 0:
        return {}

    return {
        script: count / total_chars * 100
        for script, count in script_counts.items()
    }
