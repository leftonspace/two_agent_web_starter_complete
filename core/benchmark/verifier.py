"""
PHASE 7.5: Benchmark Verifier

Verify task results against verification rules.
Supports multiple verification types for different task categories.

Usage:
    from core.benchmark import Verifier, get_verifier

    verifier = get_verifier()

    # Verify a result against rules
    score = await verifier.verify(task_result, verification_rules)

    # Run individual check
    check_result = await verifier.run_check(task_result, rule)
"""

from __future__ import annotations

import ast
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from .loader import VerificationRule

if TYPE_CHECKING:
    from core.routing import TaskResult


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Verification Result
# ============================================================================


class VerificationResult(BaseModel):
    """Result of a single verification check."""

    rule_type: str = Field(..., description="Type of verification rule")
    passed: bool = Field(..., description="Whether the check passed")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score for this check",
    )
    details: str = Field(default="", description="Details about the check")
    error: Optional[str] = Field(default=None, description="Error if check failed")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_type": self.rule_type,
            "passed": self.passed,
            "score": round(self.score, 3),
            "details": self.details,
            "error": self.error,
        }


class VerificationSummary(BaseModel):
    """Summary of all verification checks for a task."""

    total_rules: int = Field(default=0, description="Total rules evaluated")
    passed_rules: int = Field(default=0, description="Rules that passed")
    failed_rules: int = Field(default=0, description="Rules that failed")
    final_score: float = Field(default=0.0, description="Weighted final score")
    results: List[VerificationResult] = Field(
        default_factory=list,
        description="Individual check results",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_rules": self.total_rules,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "final_score": round(self.final_score, 3),
            "pass_rate": round(self.passed_rules / max(self.total_rules, 1), 3),
        }


# ============================================================================
# Abstract Checker Base
# ============================================================================


class BaseChecker(ABC):
    """Base class for verification checkers."""

    @property
    @abstractmethod
    def check_type(self) -> str:
        """Return the check type this checker handles."""
        pass

    @abstractmethod
    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        """
        Run the verification check.

        Args:
            response: The task response to verify
            params: Parameters for the check

        Returns:
            VerificationResult with score and details
        """
        pass


# ============================================================================
# Code Verification Checkers
# ============================================================================


class SyntaxValidChecker(BaseChecker):
    """Check that code parses without syntax errors."""

    @property
    def check_type(self) -> str:
        return "syntax_valid"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        # Extract code blocks from response
        code = self._extract_code(response, params.get("language", "python"))

        if not code:
            return VerificationResult(
                rule_type=self.check_type,
                passed=False,
                score=0.0,
                details="No code block found in response",
            )

        language = params.get("language", "python")

        if language == "python":
            return await self._check_python(code)
        elif language == "javascript":
            return await self._check_javascript(code)
        else:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.5,
                details=f"Syntax check not implemented for {language}",
            )

    async def _check_python(self, code: str) -> VerificationResult:
        """Check Python syntax."""
        try:
            ast.parse(code)
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=1.0,
                details="Python syntax is valid",
            )
        except SyntaxError as e:
            return VerificationResult(
                rule_type=self.check_type,
                passed=False,
                score=0.0,
                details=f"Syntax error at line {e.lineno}: {e.msg}",
                error=str(e),
            )

    async def _check_javascript(self, code: str) -> VerificationResult:
        """Basic JavaScript syntax check (heuristic)."""
        # Basic bracket matching
        brackets = {"(": ")", "[": "]", "{": "}"}
        stack = []

        for char in code:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    return VerificationResult(
                        rule_type=self.check_type,
                        passed=False,
                        score=0.0,
                        details="Mismatched brackets",
                    )

        if stack:
            return VerificationResult(
                rule_type=self.check_type,
                passed=False,
                score=0.0,
                details="Unclosed brackets",
            )

        return VerificationResult(
            rule_type=self.check_type,
            passed=True,
            score=0.8,  # Not as confident as AST parsing
            details="JavaScript syntax appears valid (basic check)",
        )

    def _extract_code(self, response: str, language: str) -> str:
        """Extract code block from markdown response."""
        # Try to find language-specific code block
        pattern = rf"```{language}\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Try generic code block
        pattern = r"```\s*(.*?)```"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Return full response if no code block
        return response.strip()


class HasErrorHandlingChecker(BaseChecker):
    """Check that code includes error handling."""

    @property
    def check_type(self) -> str:
        return "has_error_handling"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        language = params.get("language", "python")

        if language == "python":
            patterns = [
                r"\btry\s*:",
                r"\bexcept\s+",
                r"\braise\s+",
            ]
        elif language in ("javascript", "typescript"):
            patterns = [
                r"\btry\s*{",
                r"\bcatch\s*\(",
                r"\bthrow\s+",
            ]
        else:
            patterns = [r"\btry\b", r"\bcatch\b", r"\bexcept\b"]

        matches = sum(1 for p in patterns if re.search(p, response))

        if matches >= 2:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=1.0,
                details=f"Found {matches} error handling patterns",
            )
        elif matches == 1:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.7,
                details="Found some error handling",
            )
        else:
            return VerificationResult(
                rule_type=self.check_type,
                passed=False,
                score=0.0,
                details="No error handling found",
            )


class HasDocstringsChecker(BaseChecker):
    """Check that functions have docstrings."""

    @property
    def check_type(self) -> str:
        return "has_docstrings"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        language = params.get("language", "python")

        if language == "python":
            # Count function definitions
            func_pattern = r"\bdef\s+\w+\s*\("
            functions = len(re.findall(func_pattern, response))

            # Count docstrings (triple quotes after def)
            docstring_pattern = r'def\s+\w+\s*\([^)]*\)\s*(?:->.*?)?\s*:\s*\n\s*["\'][\'"]{2}'
            docstrings = len(re.findall(docstring_pattern, response))

            if functions == 0:
                return VerificationResult(
                    rule_type=self.check_type,
                    passed=True,
                    score=0.5,
                    details="No functions found to check",
                )

            ratio = docstrings / functions
            passed = ratio >= 0.8

            return VerificationResult(
                rule_type=self.check_type,
                passed=passed,
                score=ratio,
                details=f"{docstrings}/{functions} functions have docstrings",
            )

        return VerificationResult(
            rule_type=self.check_type,
            passed=True,
            score=0.5,
            details=f"Docstring check not implemented for {language}",
        )


class HasTypeHintsChecker(BaseChecker):
    """Check that Python functions have type hints."""

    @property
    def check_type(self) -> str:
        return "has_type_hints"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        # Count function definitions
        func_pattern = r"\bdef\s+\w+\s*\("
        functions = len(re.findall(func_pattern, response))

        # Count functions with return type hints
        typed_pattern = r"\bdef\s+\w+\s*\([^)]*\)\s*->"
        typed_functions = len(re.findall(typed_pattern, response))

        if functions == 0:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.5,
                details="No functions found to check",
            )

        ratio = typed_functions / functions
        passed = ratio >= 0.8

        return VerificationResult(
            rule_type=self.check_type,
            passed=passed,
            score=ratio,
            details=f"{typed_functions}/{functions} functions have type hints",
        )


# ============================================================================
# Content Verification Checkers
# ============================================================================


class ContainsChecker(BaseChecker):
    """Check that response contains specific content."""

    @property
    def check_type(self) -> str:
        return "contains"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        required = params.get("required", [])
        if isinstance(required, str):
            required = [required]

        case_sensitive = params.get("case_sensitive", False)
        check_text = response if case_sensitive else response.lower()

        found = []
        missing = []

        for item in required:
            check_item = item if case_sensitive else item.lower()
            if check_item in check_text:
                found.append(item)
            else:
                missing.append(item)

        if not required:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.5,
                details="No required content specified",
            )

        ratio = len(found) / len(required)
        passed = len(missing) == 0

        return VerificationResult(
            rule_type=self.check_type,
            passed=passed,
            score=ratio,
            details=f"Found {len(found)}/{len(required)} required items"
            + (f", missing: {missing}" if missing else ""),
        )


class NotContainsChecker(BaseChecker):
    """Check that response doesn't contain prohibited content."""

    @property
    def check_type(self) -> str:
        return "not_contains"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        prohibited = params.get("prohibited", [])
        if isinstance(prohibited, str):
            prohibited = [prohibited]

        case_sensitive = params.get("case_sensitive", False)
        check_text = response if case_sensitive else response.lower()

        found = []
        for item in prohibited:
            check_item = item if case_sensitive else item.lower()
            if check_item in check_text:
                found.append(item)

        if not prohibited:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.5,
                details="No prohibited content specified",
            )

        passed = len(found) == 0

        return VerificationResult(
            rule_type=self.check_type,
            passed=passed,
            score=1.0 if passed else 0.0,
            details="No prohibited content found" if passed else f"Found prohibited: {found}",
        )


class MinLengthChecker(BaseChecker):
    """Check that response meets minimum length."""

    @property
    def check_type(self) -> str:
        return "min_length"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        min_chars = params.get("min_chars", 0)
        min_words = params.get("min_words", 0)
        min_lines = params.get("min_lines", 0)

        char_count = len(response)
        word_count = len(response.split())
        line_count = len(response.splitlines())

        issues = []
        if min_chars > 0 and char_count < min_chars:
            issues.append(f"chars: {char_count}/{min_chars}")
        if min_words > 0 and word_count < min_words:
            issues.append(f"words: {word_count}/{min_words}")
        if min_lines > 0 and line_count < min_lines:
            issues.append(f"lines: {line_count}/{min_lines}")

        passed = len(issues) == 0

        return VerificationResult(
            rule_type=self.check_type,
            passed=passed,
            score=1.0 if passed else 0.3,
            details=f"Length OK ({char_count} chars, {word_count} words)"
            if passed
            else f"Below minimum: {', '.join(issues)}",
        )


class RegexMatchChecker(BaseChecker):
    """Check that response matches a regex pattern."""

    @property
    def check_type(self) -> str:
        return "regex_match"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        pattern = params.get("pattern", "")
        if not pattern:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.5,
                details="No pattern specified",
            )

        try:
            flags = 0
            if params.get("case_insensitive", False):
                flags |= re.IGNORECASE
            if params.get("multiline", False):
                flags |= re.MULTILINE

            match = re.search(pattern, response, flags)
            passed = match is not None

            return VerificationResult(
                rule_type=self.check_type,
                passed=passed,
                score=1.0 if passed else 0.0,
                details=f"Pattern {'matched' if passed else 'not found'}: {pattern[:50]}",
            )
        except re.error as e:
            return VerificationResult(
                rule_type=self.check_type,
                passed=False,
                score=0.0,
                details="Invalid regex pattern",
                error=str(e),
            )


# ============================================================================
# Document Verification Checkers
# ============================================================================


class FormatValidChecker(BaseChecker):
    """Check that document format is correct."""

    @property
    def check_type(self) -> str:
        return "format_valid"

    async def check(
        self,
        response: str,
        params: Dict[str, Any],
    ) -> VerificationResult:
        format_type = params.get("format", "markdown")

        if format_type == "markdown":
            return await self._check_markdown(response)
        elif format_type == "json":
            return await self._check_json(response)
        elif format_type == "email":
            return await self._check_email(response)
        else:
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=0.5,
                details=f"Format check not implemented for {format_type}",
            )

    async def _check_markdown(self, response: str) -> VerificationResult:
        """Check markdown structure."""
        has_headers = bool(re.search(r"^#+\s+\w+", response, re.MULTILINE))
        has_structure = bool(
            re.search(r"(\n-\s+|\n\d+\.\s+|\n\*\s+)", response)
        )

        score = 0.5
        if has_headers:
            score += 0.25
        if has_structure:
            score += 0.25

        return VerificationResult(
            rule_type=self.check_type,
            passed=score >= 0.5,
            score=score,
            details=f"Markdown format: headers={has_headers}, structure={has_structure}",
        )

    async def _check_json(self, response: str) -> VerificationResult:
        """Check JSON validity."""
        import json

        # Extract JSON block
        json_match = re.search(r"```json\s*(.*?)```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response

        try:
            json.loads(json_str.strip())
            return VerificationResult(
                rule_type=self.check_type,
                passed=True,
                score=1.0,
                details="Valid JSON",
            )
        except json.JSONDecodeError as e:
            return VerificationResult(
                rule_type=self.check_type,
                passed=False,
                score=0.0,
                details="Invalid JSON",
                error=str(e),
            )

    async def _check_email(self, response: str) -> VerificationResult:
        """Check email format."""
        has_subject = bool(
            re.search(r"(subject:|re:|fwd:)", response, re.IGNORECASE)
        )
        has_greeting = bool(
            re.search(r"(dear|hi|hello|good\s+(morning|afternoon|evening))", response, re.IGNORECASE)
        )
        has_closing = bool(
            re.search(r"(regards|sincerely|best|thanks|cheers)", response, re.IGNORECASE)
        )

        score = sum([has_greeting, has_closing]) / 2

        return VerificationResult(
            rule_type=self.check_type,
            passed=score >= 0.5,
            score=score,
            details=f"Email format: greeting={has_greeting}, closing={has_closing}",
        )


# ============================================================================
# Verifier
# ============================================================================


class Verifier:
    """
    Verify task results against verification rules.

    Verification types supported:
    - syntax_valid: Code parses without errors
    - has_error_handling: Code includes try/except
    - has_docstrings: Functions have docstrings
    - has_type_hints: Functions have type hints
    - contains: Response contains required content
    - not_contains: Response doesn't contain prohibited content
    - min_length: Response meets minimum length
    - regex_match: Response matches a pattern
    - format_valid: Document format is correct

    Usage:
        verifier = Verifier()
        score = await verifier.verify(task_result, rules)
    """

    def __init__(self):
        """Initialize the verifier with available checkers."""
        self._checkers: Dict[str, BaseChecker] = {}
        self._register_default_checkers()

        # Statistics
        self._verification_count = 0
        self._check_counts: Dict[str, int] = {}

    def _register_default_checkers(self) -> None:
        """Register all default checkers."""
        checkers = [
            SyntaxValidChecker(),
            HasErrorHandlingChecker(),
            HasDocstringsChecker(),
            HasTypeHintsChecker(),
            ContainsChecker(),
            NotContainsChecker(),
            MinLengthChecker(),
            RegexMatchChecker(),
            FormatValidChecker(),
        ]
        for checker in checkers:
            self._checkers[checker.check_type] = checker

    # -------------------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------------------

    async def verify(
        self,
        result: Any,  # TaskResult or just response string
        rules: List[VerificationRule],
    ) -> float:
        """
        Verify a result against rules.

        Args:
            result: TaskResult or response string
            rules: List of verification rules

        Returns:
            Weighted score (0.0 to 1.0)
        """
        summary = await self.verify_detailed(result, rules)
        return summary.final_score

    async def verify_detailed(
        self,
        result: Any,
        rules: List[VerificationRule],
    ) -> VerificationSummary:
        """
        Verify a result with detailed results.

        Args:
            result: TaskResult or response string
            rules: List of verification rules

        Returns:
            VerificationSummary with all check results
        """
        self._verification_count += 1

        # Extract response string
        if hasattr(result, "response"):
            response = result.response
        elif isinstance(result, str):
            response = result
        else:
            response = str(result)

        if not rules:
            return VerificationSummary(
                total_rules=0,
                passed_rules=0,
                failed_rules=0,
                final_score=0.5,  # Neutral score for no rules
                results=[],
            )

        results = []
        total_weight = 0.0

        for rule in rules:
            check_result = await self.run_check(response, rule)
            results.append(check_result)
            total_weight += rule.weight

            # Update stats
            self._check_counts[rule.type] = self._check_counts.get(rule.type, 0) + 1

        # Calculate weighted score
        if total_weight > 0:
            weighted_score = sum(
                r.score * rules[i].weight
                for i, r in enumerate(results)
            ) / total_weight
        else:
            weighted_score = sum(r.score for r in results) / len(results)

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return VerificationSummary(
            total_rules=len(rules),
            passed_rules=passed,
            failed_rules=failed,
            final_score=weighted_score,
            results=results,
        )

    async def run_check(
        self,
        response: str,
        rule: VerificationRule,
    ) -> VerificationResult:
        """
        Run a single verification check.

        Args:
            response: Response string to verify
            rule: Verification rule to apply

        Returns:
            VerificationResult
        """
        checker = self._checkers.get(rule.type)

        if not checker:
            logger.warning(f"Unknown verification type: {rule.type}")
            return VerificationResult(
                rule_type=rule.type,
                passed=True,
                score=0.5,
                details=f"Unknown verification type: {rule.type}",
            )

        try:
            return await checker.check(response, rule.params)
        except Exception as e:
            logger.error(f"Verification check failed: {e}")
            return VerificationResult(
                rule_type=rule.type,
                passed=False,
                score=0.0,
                details="Check execution failed",
                error=str(e),
            )

    # -------------------------------------------------------------------------
    # Checker Management
    # -------------------------------------------------------------------------

    def register_checker(self, checker: BaseChecker) -> None:
        """Register a custom checker."""
        self._checkers[checker.check_type] = checker

    def get_available_checks(self) -> List[str]:
        """Get list of available check types."""
        return list(self._checkers.keys())

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        return {
            "total_verifications": self._verification_count,
            "check_counts": self._check_counts.copy(),
            "available_checks": self.get_available_checks(),
        }

    def reset_stats(self) -> None:
        """Reset verification statistics."""
        self._verification_count = 0
        self._check_counts.clear()


# ============================================================================
# Singleton Instance
# ============================================================================


_verifier: Optional[Verifier] = None


def get_verifier() -> Verifier:
    """Get the global verifier."""
    global _verifier
    if _verifier is None:
        _verifier = Verifier()
    return _verifier


def reset_verifier() -> None:
    """Reset the global verifier (for testing)."""
    global _verifier
    _verifier = None
