"""
PHASE 7.2: Output Guardrails

Validates and sanitizes all outputs before returning to users.

Components:
- PIIDetector: Detects SSN, credit cards, phone numbers, API keys
- AnomalyDetector: Detects script mixing, prompt leakage
- OutputGuardrails: Main validation orchestrator

Usage:
    from core.security.guardrails import OutputGuardrails, GuardrailContext

    guardrails = OutputGuardrails()
    context = GuardrailContext(
        expected_language="en",
        system_prompt_hash="abc123...",
        pii_policy="redact"
    )

    result = guardrails.validate(output_text, context)
    if not result.is_safe:
        output_text = result.sanitized_output or ""
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Set

from .pii_patterns import (
    SSN_PATTERN,
    SSN_STRICT_PATTERN,
    CREDIT_CARD_PATTERN,
    US_PHONE_PATTERN,
    EMAIL_PATTERN,
    API_KEY_PATTERNS,
    PII_PATTERNS,
    luhn_checksum,
    extract_card_digits,
    get_char_script,
    analyze_script_distribution,
)


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================


class PIIPattern(Enum):
    """Types of PII that can be detected."""
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PHONE_US = "phone_us"
    EMAIL = "email"
    API_KEY = "api_key"
    PRIVATE_KEY = "private_key"
    IP_ADDRESS = "ip_address"
    CRYPTO_ADDRESS = "crypto_address"


class IssueSeverity(Enum):
    """Severity levels for detected issues."""
    CRITICAL = "critical"  # Must block
    HIGH = "high"          # Should block unless overridden
    MEDIUM = "medium"      # Should warn
    LOW = "low"            # Informational


@dataclass
class PIIMatch:
    """Represents a detected PII match."""
    pattern_type: PIIPattern
    matched_text: str
    start_pos: int
    end_pos: int
    confidence: float  # 0.0 to 1.0
    context: str = ""  # Surrounding text for debugging

    def __post_init__(self):
        """Validate confidence range."""
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class Anomaly:
    """Represents a detected anomaly in text."""
    anomaly_type: str
    description: str
    location: Optional[str] = None
    severity: IssueSeverity = IssueSeverity.MEDIUM
    confidence: float = 1.0


@dataclass
class Issue:
    """Generic issue detected in output."""
    issue_type: str
    description: str
    severity: IssueSeverity
    location: Optional[str] = None
    suggestion: Optional[str] = None
    pii_match: Optional[PIIMatch] = None
    anomaly: Optional[Anomaly] = None


@dataclass
class GuardrailContext:
    """Context for output validation."""
    expected_language: str = "en"
    system_prompt_hash: str = ""
    pii_policy: Literal["block", "redact", "warn"] = "redact"
    allowed_scripts: List[str] = field(default_factory=lambda: ["latin"])
    max_script_mixing_ratio: float = 0.01  # 1% threshold
    sensitive_phrases: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of output validation."""
    is_safe: bool
    issues: List[Issue] = field(default_factory=list)
    sanitized_output: Optional[str] = None
    blocked_reason: Optional[str] = None
    pii_found: int = 0
    anomalies_found: int = 0

    @property
    def has_critical_issues(self) -> bool:
        """Check if any critical issues were found."""
        return any(i.severity == IssueSeverity.CRITICAL for i in self.issues)

    @property
    def has_high_issues(self) -> bool:
        """Check if any high severity issues were found."""
        return any(i.severity == IssueSeverity.HIGH for i in self.issues)

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[Issue]:
        """Get all issues of a specific severity."""
        return [i for i in self.issues if i.severity == severity]


# ============================================================================
# PII Detector
# ============================================================================


class PIIDetector:
    """
    Detects Personally Identifiable Information in text.

    Supports detection of:
    - Social Security Numbers (SSN)
    - Credit card numbers (with Luhn validation)
    - US phone numbers
    - Email addresses
    - API keys and tokens
    - Private keys
    """

    # Redaction placeholder
    REDACTION_MARKER = "[REDACTED]"

    def __init__(self, strict_mode: bool = True):
        """
        Initialize PII detector.

        Args:
            strict_mode: If True, use stricter detection (fewer false negatives)
        """
        self.strict_mode = strict_mode
        self._stats = {"detections": 0, "redactions": 0}

    def detect(self, text: str) -> List[PIIMatch]:
        """
        Detect all PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            List of PIIMatch objects for each detection
        """
        if not text:
            return []

        matches: List[PIIMatch] = []

        # Detect SSN
        matches.extend(self._detect_ssn(text))

        # Detect credit cards
        matches.extend(self._detect_credit_cards(text))

        # Detect phone numbers
        matches.extend(self._detect_phones(text))

        # Detect emails (only in strict mode - emails are often not sensitive)
        if self.strict_mode:
            matches.extend(self._detect_emails(text))

        # Detect API keys
        matches.extend(self._detect_api_keys(text))

        # Sort by position
        matches.sort(key=lambda m: m.start_pos)

        self._stats["detections"] += len(matches)
        return matches

    def redact(self, text: str, matches: Optional[List[PIIMatch]] = None) -> str:
        """
        Redact PII from text.

        Args:
            text: Text to redact
            matches: Pre-computed matches (if None, will detect)

        Returns:
            Text with PII replaced by [REDACTED]
        """
        if not text:
            return text

        if matches is None:
            matches = self.detect(text)

        if not matches:
            return text

        # Sort by position in reverse to replace from end to start
        sorted_matches = sorted(matches, key=lambda m: m.start_pos, reverse=True)

        result = text
        for match in sorted_matches:
            # Create type-specific redaction marker
            marker = f"[REDACTED-{match.pattern_type.value.upper()}]"
            result = result[:match.start_pos] + marker + result[match.end_pos:]
            self._stats["redactions"] += 1

        return result

    def _detect_ssn(self, text: str) -> List[PIIMatch]:
        """Detect Social Security Numbers."""
        matches = []

        # Use strict pattern first (higher confidence)
        for match in SSN_STRICT_PATTERN.finditer(text):
            ssn = match.group()
            # Additional validation: not all zeros in any section
            parts = ssn.split("-")
            if len(parts) == 3 and all(p != "000" and p != "0000" for p in parts):
                matches.append(PIIMatch(
                    pattern_type=PIIPattern.SSN,
                    matched_text=ssn,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.95,
                    context=text[max(0, match.start()-20):match.end()+20]
                ))

        # If strict mode, also check for SSNs without dashes
        if self.strict_mode:
            for match in SSN_PATTERN.finditer(text):
                # Avoid duplicates
                if not any(m.start_pos == match.start() for m in matches):
                    matches.append(PIIMatch(
                        pattern_type=PIIPattern.SSN,
                        matched_text=match.group(),
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.75,  # Lower confidence without dashes
                        context=text[max(0, match.start()-20):match.end()+20]
                    ))

        return matches

    def _detect_credit_cards(self, text: str) -> List[PIIMatch]:
        """Detect credit card numbers with Luhn validation."""
        matches = []

        for match in CREDIT_CARD_PATTERN.finditer(text):
            card_text = match.group()
            card_digits = extract_card_digits(card_text)

            # Validate with Luhn algorithm
            if luhn_checksum(card_digits):
                matches.append(PIIMatch(
                    pattern_type=PIIPattern.CREDIT_CARD,
                    matched_text=card_text,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.98,  # High confidence with Luhn validation
                    context=text[max(0, match.start()-20):match.end()+20]
                ))
            elif self.strict_mode:
                # Still flag without Luhn validation in strict mode
                matches.append(PIIMatch(
                    pattern_type=PIIPattern.CREDIT_CARD,
                    matched_text=card_text,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.60,  # Lower confidence without validation
                    context=text[max(0, match.start()-20):match.end()+20]
                ))

        return matches

    def _detect_phones(self, text: str) -> List[PIIMatch]:
        """Detect US phone numbers."""
        matches = []

        for match in US_PHONE_PATTERN.finditer(text):
            phone = match.group()
            # Reduce false positives: check context for phone-related terms
            context = text[max(0, match.start()-30):match.end()+30].lower()
            has_context = any(term in context for term in [
                "phone", "tel", "call", "mobile", "cell", "contact",
                "fax", "number", "#", "dial"
            ])

            confidence = 0.85 if has_context else 0.60

            matches.append(PIIMatch(
                pattern_type=PIIPattern.PHONE_US,
                matched_text=phone,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=confidence,
                context=text[max(0, match.start()-20):match.end()+20]
            ))

        return matches

    def _detect_emails(self, text: str) -> List[PIIMatch]:
        """Detect email addresses."""
        matches = []

        for match in EMAIL_PATTERN.finditer(text):
            email = match.group()
            # Skip common example/test emails
            if any(example in email.lower() for example in [
                "example.com", "test.com", "sample.com", "foo.com",
                "bar.com", "placeholder", "noreply", "donotreply"
            ]):
                continue

            matches.append(PIIMatch(
                pattern_type=PIIPattern.EMAIL,
                matched_text=email,
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.90,
                context=text[max(0, match.start()-20):match.end()+20]
            ))

        return matches

    def _detect_api_keys(self, text: str) -> List[PIIMatch]:
        """Detect API keys and tokens."""
        matches = []

        for key_type, pattern in API_KEY_PATTERNS.items():
            for match in pattern.finditer(text):
                # Determine if it's a private key
                is_private_key = "private_key" in key_type

                matches.append(PIIMatch(
                    pattern_type=PIIPattern.PRIVATE_KEY if is_private_key else PIIPattern.API_KEY,
                    matched_text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.95,
                    context=f"key_type={key_type}"
                ))

        return matches

    def get_statistics(self) -> Dict[str, int]:
        """Get detection statistics."""
        return self._stats.copy()


# ============================================================================
# Anomaly Detector
# ============================================================================


class AnomalyDetector:
    """
    Detects anomalies in text output.

    Detects:
    - Unexpected script mixing (e.g., Thai characters in English text)
    - System prompt fragments leaking into output
    - Suspicious character sequences
    """

    # Known suspicious patterns that might indicate prompt injection output
    SUSPICIOUS_PATTERNS = [
        re.compile(r"<\|endoftext\|>", re.IGNORECASE),
        re.compile(r"<\|im_start\|>", re.IGNORECASE),
        re.compile(r"<\|im_end\|>", re.IGNORECASE),
        re.compile(r"\[INST\]", re.IGNORECASE),
        re.compile(r"\[/INST\]", re.IGNORECASE),
        re.compile(r"<<SYS>>", re.IGNORECASE),
        re.compile(r"<</SYS>>", re.IGNORECASE),
        re.compile(r"Human:", re.IGNORECASE),
        re.compile(r"Assistant:", re.IGNORECASE),
    ]

    def __init__(self):
        """Initialize anomaly detector."""
        self._stats = {"script_checks": 0, "prompt_checks": 0, "anomalies": 0}

    def detect_script_mixing(
        self,
        text: str,
        expected_script: str = "latin",
        threshold: float = 0.01
    ) -> List[Anomaly]:
        """
        Detect unexpected script mixing in text.

        For example, detecting Thai or Chinese characters appearing
        in what should be English-only output.

        Args:
            text: Text to analyze
            expected_script: Expected primary script (e.g., "latin")
            threshold: Maximum allowed ratio of unexpected scripts (0.01 = 1%)

        Returns:
            List of detected anomalies
        """
        self._stats["script_checks"] += 1

        if not text:
            return []

        anomalies = []
        distribution = analyze_script_distribution(text)

        if not distribution:
            return []

        # Check for unexpected scripts
        for script, percentage in distribution.items():
            if script != expected_script and script != "unknown":
                ratio = percentage / 100

                if ratio > threshold:
                    anomaly = Anomaly(
                        anomaly_type="script_mixing",
                        description=f"Unexpected {script} characters detected ({percentage:.1f}%)",
                        severity=IssueSeverity.MEDIUM if ratio < 0.05 else IssueSeverity.HIGH,
                        confidence=min(1.0, ratio * 10)  # Higher confidence for more mixing
                    )
                    anomalies.append(anomaly)
                    self._stats["anomalies"] += 1

        return anomalies

    def detect_prompt_leak(
        self,
        text: str,
        system_prompt_hash: str,
        sensitive_phrases: Optional[List[str]] = None
    ) -> bool:
        """
        Detect if system prompt appears to be leaking in output.

        Uses hash comparison and phrase matching to detect leaks
        without exposing the actual system prompt.

        Args:
            text: Output text to check
            system_prompt_hash: SHA-256 hash of system prompt
            sensitive_phrases: List of phrases that shouldn't appear in output

        Returns:
            True if prompt leak detected
        """
        self._stats["prompt_checks"] += 1

        if not text or not system_prompt_hash:
            return False

        # Check if output contains suspicious fragments
        text_lower = text.lower()

        # Check for exact substring match of hashed content
        # (compare rolling hashes of output against system prompt hash)
        # This is a simplified check - full implementation would use n-gram hashing
        for i in range(len(text) - 50):
            chunk = text[i:i+100]
            chunk_hash = hashlib.sha256(chunk.encode()).hexdigest()
            if chunk_hash == system_prompt_hash:
                self._stats["anomalies"] += 1
                return True

        # Check for sensitive phrases
        if sensitive_phrases:
            for phrase in sensitive_phrases:
                if phrase.lower() in text_lower:
                    self._stats["anomalies"] += 1
                    return True

        # Check for suspicious LLM control tokens
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.search(text):
                self._stats["anomalies"] += 1
                return True

        return False

    def detect_suspicious_patterns(self, text: str) -> List[Anomaly]:
        """
        Detect suspicious patterns that might indicate attacks or corruption.

        Args:
            text: Text to analyze

        Returns:
            List of detected anomalies
        """
        anomalies = []

        for pattern in self.SUSPICIOUS_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                anomalies.append(Anomaly(
                    anomaly_type="suspicious_token",
                    description=f"Suspicious token detected: {matches[0]}",
                    severity=IssueSeverity.HIGH,
                    confidence=0.95
                ))
                self._stats["anomalies"] += 1

        return anomalies

    def get_statistics(self) -> Dict[str, int]:
        """Get detection statistics."""
        return self._stats.copy()


# ============================================================================
# Output Guardrails (Main Orchestrator)
# ============================================================================


class OutputGuardrails:
    """
    Main output validation orchestrator.

    Combines PII detection and anomaly detection to validate
    all outputs before returning to users.
    """

    def __init__(
        self,
        pii_detector: Optional[PIIDetector] = None,
        anomaly_detector: Optional[AnomalyDetector] = None
    ):
        """
        Initialize output guardrails.

        Args:
            pii_detector: Custom PII detector (or uses default)
            anomaly_detector: Custom anomaly detector (or uses default)
        """
        self.pii_detector = pii_detector or PIIDetector()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()

    def validate(
        self,
        output: str,
        context: GuardrailContext
    ) -> ValidationResult:
        """
        Validate output text against guardrails.

        Args:
            output: Output text to validate
            context: Validation context with policies

        Returns:
            ValidationResult with safety status and any issues
        """
        if not output:
            return ValidationResult(is_safe=True, sanitized_output=output)

        issues: List[Issue] = []
        pii_matches: List[PIIMatch] = []
        anomalies: List[Anomaly] = []

        # Step 1: Detect PII
        pii_matches = self.pii_detector.detect(output)
        for match in pii_matches:
            severity = self._get_pii_severity(match, context)
            issues.append(Issue(
                issue_type="pii_detected",
                description=f"Detected {match.pattern_type.value}: {self._mask_text(match.matched_text)}",
                severity=severity,
                location=f"position {match.start_pos}-{match.end_pos}",
                suggestion=f"Remove or redact {match.pattern_type.value}",
                pii_match=match
            ))

        # Step 2: Detect script mixing
        script_anomalies = self.anomaly_detector.detect_script_mixing(
            output,
            expected_script=context.allowed_scripts[0] if context.allowed_scripts else "latin",
            threshold=context.max_script_mixing_ratio
        )
        for anomaly in script_anomalies:
            anomalies.append(anomaly)
            issues.append(Issue(
                issue_type="script_mixing",
                description=anomaly.description,
                severity=anomaly.severity,
                suggestion="Check for character encoding issues or injection attempts",
                anomaly=anomaly
            ))

        # Step 3: Detect prompt leakage
        if context.system_prompt_hash:
            if self.anomaly_detector.detect_prompt_leak(
                output,
                context.system_prompt_hash,
                context.sensitive_phrases
            ):
                issues.append(Issue(
                    issue_type="prompt_leak",
                    description="Potential system prompt leakage detected",
                    severity=IssueSeverity.CRITICAL,
                    suggestion="Block output and investigate"
                ))

        # Step 4: Detect suspicious patterns
        suspicious = self.anomaly_detector.detect_suspicious_patterns(output)
        for anomaly in suspicious:
            anomalies.append(anomaly)
            issues.append(Issue(
                issue_type="suspicious_pattern",
                description=anomaly.description,
                severity=anomaly.severity,
                anomaly=anomaly
            ))

        # Determine safety and create result
        is_safe = self._determine_safety(issues, context)
        sanitized_output = None
        blocked_reason = None

        if not is_safe:
            if context.pii_policy == "block":
                blocked_reason = self._get_block_reason(issues)
            elif context.pii_policy == "redact":
                sanitized_output = self.sanitize(output, issues)

        return ValidationResult(
            is_safe=is_safe,
            issues=issues,
            sanitized_output=sanitized_output,
            blocked_reason=blocked_reason,
            pii_found=len(pii_matches),
            anomalies_found=len(anomalies)
        )

    def sanitize(self, output: str, issues: List[Issue]) -> str:
        """
        Sanitize output by redacting detected issues.

        Args:
            output: Output text to sanitize
            issues: List of detected issues

        Returns:
            Sanitized text with sensitive data redacted
        """
        if not output or not issues:
            return output

        # Collect PII matches from issues
        pii_matches = [i.pii_match for i in issues if i.pii_match]

        # Use PII detector to redact
        result = self.pii_detector.redact(output, pii_matches)

        # Also redact any anomaly-detected content
        for issue in issues:
            if issue.anomaly and issue.anomaly.anomaly_type == "suspicious_token":
                # Find and redact suspicious tokens
                for pattern in self.anomaly_detector.SUSPICIOUS_PATTERNS:
                    result = pattern.sub("[SUSPICIOUS-CONTENT-REMOVED]", result)

        return result

    def _get_pii_severity(self, match: PIIMatch, context: GuardrailContext) -> IssueSeverity:
        """Determine severity based on PII type and context."""
        # Critical: API keys, private keys, SSN, credit cards
        if match.pattern_type in [
            PIIPattern.API_KEY, PIIPattern.PRIVATE_KEY,
            PIIPattern.SSN, PIIPattern.CREDIT_CARD
        ]:
            return IssueSeverity.CRITICAL if match.confidence > 0.8 else IssueSeverity.HIGH

        # High: Phone numbers with high confidence
        if match.pattern_type == PIIPattern.PHONE_US and match.confidence > 0.7:
            return IssueSeverity.HIGH

        # Medium: Emails, low-confidence phones
        return IssueSeverity.MEDIUM

    def _determine_safety(self, issues: List[Issue], context: GuardrailContext) -> bool:
        """Determine if output is safe based on issues and policy."""
        if not issues:
            return True

        # Always unsafe if critical issues
        if any(i.severity == IssueSeverity.CRITICAL for i in issues):
            return False

        # Check policy for high issues
        if context.pii_policy == "block":
            if any(i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH] for i in issues):
                return False

        # Warn policy is safe but logs issues
        return True

    def _get_block_reason(self, issues: List[Issue]) -> str:
        """Get human-readable block reason."""
        critical = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical:
            return f"Blocked: {critical[0].description}"

        high = [i for i in issues if i.severity == IssueSeverity.HIGH]
        if high:
            return f"Blocked: {high[0].description}"

        return "Blocked: Security policy violation"

    def _mask_text(self, text: str, visible_chars: int = 4) -> str:
        """Mask sensitive text for logging."""
        if len(text) <= visible_chars * 2:
            return "*" * len(text)
        return text[:visible_chars] + "*" * (len(text) - visible_chars * 2) + text[-visible_chars:]


# ============================================================================
# Convenience Functions
# ============================================================================


def create_guardrails(strict_mode: bool = True) -> OutputGuardrails:
    """
    Create output guardrails with default configuration.

    Args:
        strict_mode: Whether to use strict detection

    Returns:
        Configured OutputGuardrails instance
    """
    return OutputGuardrails(
        pii_detector=PIIDetector(strict_mode=strict_mode),
        anomaly_detector=AnomalyDetector()
    )


def validate_output(
    output: str,
    pii_policy: Literal["block", "redact", "warn"] = "redact",
    system_prompt_hash: str = ""
) -> ValidationResult:
    """
    Quick validation of output text.

    Args:
        output: Text to validate
        pii_policy: How to handle PII ("block", "redact", or "warn")
        system_prompt_hash: Hash of system prompt for leak detection

    Returns:
        ValidationResult
    """
    guardrails = create_guardrails()
    context = GuardrailContext(
        pii_policy=pii_policy,
        system_prompt_hash=system_prompt_hash
    )
    return guardrails.validate(output, context)


def redact_pii(text: str) -> str:
    """
    Quick PII redaction.

    Args:
        text: Text to redact

    Returns:
        Text with PII replaced by [REDACTED-TYPE]
    """
    detector = PIIDetector()
    return detector.redact(text)


def hash_system_prompt(prompt: str) -> str:
    """
    Create hash of system prompt for leak detection.

    Args:
        prompt: System prompt text

    Returns:
        SHA-256 hash of prompt
    """
    return hashlib.sha256(prompt.encode()).hexdigest()
