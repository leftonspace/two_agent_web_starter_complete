"""
PHASE 7.5: Format Checker Component

Validates document format for business documents domain.
Checks structure, headings, required sections.

Usage:
    from core.evaluation.scoring_committee import FormatChecker

    checker = FormatChecker()
    score = await checker.run(task_result)  # 0.0 to 1.0
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..base import TaskResult


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Format Check Result
# ============================================================================


class FormatIssue(BaseModel):
    """A format issue found."""
    type: str  # e.g., "missing_heading", "invalid_structure"
    message: str
    severity: str = "warning"  # error, warning, info
    location: Optional[str] = None


class FormatCheckResult(BaseModel):
    """Result of format checking."""
    valid: bool = True
    issues: List[FormatIssue] = Field(default_factory=list)
    checks_passed: int = 0
    checks_failed: int = 0
    document_type: Optional[str] = None

    @property
    def score(self) -> float:
        """Calculate 0-1 score."""
        total = self.checks_passed + self.checks_failed
        if total == 0:
            return 1.0
        return self.checks_passed / total


# ============================================================================
# Document Type Definitions
# ============================================================================


DOCUMENT_FORMATS = {
    "report": {
        "required_sections": ["summary", "findings", "recommendations"],
        "optional_sections": ["introduction", "methodology", "appendix"],
        "min_length": 200,
        "max_length": 50000,
    },
    "proposal": {
        "required_sections": ["problem", "solution", "benefits"],
        "optional_sections": ["pricing", "timeline", "team", "risks"],
        "min_length": 300,
        "max_length": 20000,
    },
    "email": {
        "required_sections": [],
        "required_elements": ["greeting", "body", "closing"],
        "min_length": 20,
        "max_length": 5000,
    },
    "documentation": {
        "required_sections": ["overview"],
        "optional_sections": ["installation", "usage", "api", "examples"],
        "min_length": 100,
        "max_length": 100000,
    },
    "presentation": {
        "required_elements": ["title", "slides"],
        "min_slides": 3,
        "max_slides": 50,
    },
}


# ============================================================================
# Format Checker
# ============================================================================


class FormatChecker:
    """
    Check document format validity.

    Validates:
    - Document structure (sections, headings)
    - Required elements for document type
    - Length constraints
    - Formatting consistency

    Usage:
        checker = FormatChecker()
        score = await checker.run(task_result)
    """

    def __init__(self, custom_formats: Optional[Dict[str, Any]] = None):
        """
        Initialize the format checker.

        Args:
            custom_formats: Custom document format definitions
        """
        self._formats = {**DOCUMENT_FORMATS, **(custom_formats or {})}

    async def run(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Check format and return score.

        Args:
            result: Task result to check
            context: Additional context (e.g., document_type)

        Returns:
            Score from 0.0 to 1.0
        """
        # Detect document type
        doc_type = self._detect_document_type(result, context)

        if not doc_type:
            # Unknown type - do basic checks only
            check_result = await self._basic_format_check(result.response)
        else:
            # Check against document type format
            check_result = await self._check_document_format(
                result.response,
                doc_type,
            )

        logger.info(
            f"Format check: {check_result.checks_passed}/{check_result.checks_passed + check_result.checks_failed} passed "
            f"(score={check_result.score:.2f})"
        )

        return check_result.score

    def _detect_document_type(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Detect the document type from context or content."""
        # Check context first
        if context and "document_type" in context:
            return context["document_type"]

        # Check task type
        if result.task_type:
            type_lower = result.task_type.lower()
            for doc_type in self._formats:
                if doc_type in type_lower:
                    return doc_type

        # Detect from request
        request_lower = result.request.lower()
        for doc_type in self._formats:
            if doc_type in request_lower:
                return doc_type

        # Detect from content patterns
        response = result.response.lower()
        if "executive summary" in response or "findings" in response:
            return "report"
        if "dear " in response or "sincerely" in response or "regards" in response:
            return "email"
        if "# " in response and "## " in response:
            return "documentation"

        return None

    async def _basic_format_check(self, content: str) -> FormatCheckResult:
        """Basic format checks for unknown document types."""
        result = FormatCheckResult()

        # Check minimum content
        if len(content.strip()) < 10:
            result.issues.append(FormatIssue(
                type="too_short",
                message="Content is too short",
                severity="error",
            ))
            result.checks_failed += 1
        else:
            result.checks_passed += 1

        # Check for structure (any headings or paragraphs)
        has_structure = bool(
            re.search(r"^#+\s", content, re.MULTILINE) or  # Markdown headings
            re.search(r"\n\n", content)  # Paragraph breaks
        )
        if has_structure:
            result.checks_passed += 1
        else:
            result.issues.append(FormatIssue(
                type="no_structure",
                message="Content lacks clear structure",
                severity="warning",
            ))
            result.checks_failed += 1

        # Check for excessive whitespace
        if re.search(r"\n{4,}", content):
            result.issues.append(FormatIssue(
                type="excessive_whitespace",
                message="Too many consecutive blank lines",
                severity="info",
            ))

        result.valid = result.checks_failed == 0
        return result

    async def _check_document_format(
        self,
        content: str,
        doc_type: str,
    ) -> FormatCheckResult:
        """Check document against type-specific format."""
        result = FormatCheckResult(document_type=doc_type)
        format_def = self._formats.get(doc_type, {})

        # Check required sections
        required_sections = format_def.get("required_sections", [])
        for section in required_sections:
            if self._has_section(content, section):
                result.checks_passed += 1
            else:
                result.issues.append(FormatIssue(
                    type="missing_section",
                    message=f"Missing required section: {section}",
                    severity="error",
                ))
                result.checks_failed += 1

        # Check required elements (for emails, etc.)
        required_elements = format_def.get("required_elements", [])
        for element in required_elements:
            if self._has_element(content, element):
                result.checks_passed += 1
            else:
                result.issues.append(FormatIssue(
                    type="missing_element",
                    message=f"Missing required element: {element}",
                    severity="error",
                ))
                result.checks_failed += 1

        # Check length constraints
        min_length = format_def.get("min_length", 0)
        max_length = format_def.get("max_length", float("inf"))
        content_length = len(content)

        if content_length < min_length:
            result.issues.append(FormatIssue(
                type="too_short",
                message=f"Content too short ({content_length} < {min_length} chars)",
                severity="warning",
            ))
            result.checks_failed += 1
        elif content_length > max_length:
            result.issues.append(FormatIssue(
                type="too_long",
                message=f"Content too long ({content_length} > {max_length} chars)",
                severity="warning",
            ))
            result.checks_failed += 1
        else:
            result.checks_passed += 1

        # Additional checks based on type
        if doc_type == "email":
            result = self._check_email_format(content, result)
        elif doc_type == "presentation":
            result = self._check_presentation_format(content, result, format_def)

        result.valid = result.checks_failed == 0
        return result

    def _has_section(self, content: str, section: str) -> bool:
        """Check if content has a section with given name."""
        section_lower = section.lower()
        content_lower = content.lower()

        # Check for markdown heading
        patterns = [
            rf"^#+\s*{section_lower}",  # # Summary
            rf"^{section_lower}:",       # Summary:
            rf"^\*\*{section_lower}\*\*", # **Summary**
            rf"^{section_lower}\n[=-]+",  # Summary\n======
        ]

        for pattern in patterns:
            if re.search(pattern, content_lower, re.MULTILINE):
                return True

        return False

    def _has_element(self, content: str, element: str) -> bool:
        """Check if content has a specific element."""
        content_lower = content.lower()

        if element == "greeting":
            return bool(re.search(
                r"^(dear|hi|hello|hey|good morning|good afternoon)",
                content_lower,
            ))
        elif element == "closing":
            return bool(re.search(
                r"(sincerely|regards|best|thanks|thank you|cheers)",
                content_lower,
            ))
        elif element == "body":
            # Has content between greeting and closing
            return len(content.strip()) > 50
        elif element == "title":
            return bool(re.search(r"^#\s", content, re.MULTILINE))
        elif element == "slides":
            # Check for slide markers
            return bool(re.search(r"^---\s*$", content, re.MULTILINE))

        return True  # Unknown element, assume present

    def _check_email_format(
        self,
        content: str,
        result: FormatCheckResult,
    ) -> FormatCheckResult:
        """Additional checks for email format."""
        # Check for subject line (if present)
        if "subject:" in content.lower():
            result.checks_passed += 1
        # Not required, so don't penalize

        # Check signature
        if re.search(r"\n--\n", content) or re.search(r"\n\n[A-Z][a-z]+ [A-Z][a-z]+\n", content):
            result.checks_passed += 1
        # Not required

        return result

    def _check_presentation_format(
        self,
        content: str,
        result: FormatCheckResult,
        format_def: Dict[str, Any],
    ) -> FormatCheckResult:
        """Additional checks for presentation format."""
        # Count slides
        slides = re.findall(r"^---\s*$", content, re.MULTILINE)
        slide_count = len(slides) + 1  # First slide doesn't need separator

        min_slides = format_def.get("min_slides", 1)
        max_slides = format_def.get("max_slides", 100)

        if slide_count < min_slides:
            result.issues.append(FormatIssue(
                type="too_few_slides",
                message=f"Too few slides ({slide_count} < {min_slides})",
                severity="warning",
            ))
            result.checks_failed += 1
        elif slide_count > max_slides:
            result.issues.append(FormatIssue(
                type="too_many_slides",
                message=f"Too many slides ({slide_count} > {max_slides})",
                severity="warning",
            ))
            result.checks_failed += 1
        else:
            result.checks_passed += 1

        return result
