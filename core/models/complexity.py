"""
PHASE 7.3: Complexity Assessment for Model Routing

Assesses task complexity to route requests to appropriate model tiers.
Uses rule-based evaluation with feature extraction.

Usage:
    from core.models.complexity import ComplexityAssessor, ComplexityLevel

    assessor = ComplexityAssessor()
    result = assessor.assess(
        request="Design a microservices architecture for...",
        domain="code_generation"
    )
    print(f"Level: {result.level}, Tier: {result.recommended_tier}")
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml


# Configure logging
logger = logging.getLogger(__name__)


# Default rules config path
DEFAULT_RULES_PATH = "config/models/complexity_rules.yaml"


# ============================================================================
# Enums and Data Classes
# ============================================================================


class ComplexityLevel(str, Enum):
    """Task complexity levels."""
    TRIVIAL = "trivial"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplexityFeatures:
    """Features extracted from a request for complexity assessment."""

    # Basic metrics
    token_count: int = 0
    word_count: int = 0

    # Content indicators
    has_code: bool = False
    has_urls: bool = False
    references_external: bool = False

    # Task indicators
    requires_multi_step: bool = False
    requires_creativity: bool = False

    # Extracted values
    financial_amount: Optional[float] = None
    detected_domain: Optional[str] = None
    detected_keywords: Set[str] = field(default_factory=set)

    # Context size
    estimated_output_length: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for rule evaluation."""
        return {
            "token_count": self.token_count,
            "word_count": self.word_count,
            "has_code": self.has_code,
            "has_urls": self.has_urls,
            "references_external": self.references_external,
            "requires_multi_step": self.requires_multi_step,
            "requires_creativity": self.requires_creativity,
            "financial_amount": self.financial_amount,
            "detected_domain": self.detected_domain,
            "estimated_output_length": self.estimated_output_length,
        }


@dataclass
class ComplexityResult:
    """Result of complexity assessment."""

    level: ComplexityLevel
    recommended_tier: str
    confidence: float
    reasons: List[str]
    features: ComplexityFeatures
    matched_rules: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate confidence is in valid range."""
        self.confidence = max(0.0, min(1.0, self.confidence))


# ============================================================================
# Rule Evaluation
# ============================================================================


class RuleCondition:
    """Evaluates a single rule condition."""

    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a is not None and a > b,
        ">=": lambda a, b: a is not None and a >= b,
        "<": lambda a, b: a is not None and a < b,
        "<=": lambda a, b: a is not None and a <= b,
        "in": lambda a, b: a in b if isinstance(b, (list, set)) else False,
        "not_in": lambda a, b: a not in b if isinstance(b, (list, set)) else True,
        "contains": lambda a, b: b in a if isinstance(a, str) else False,
        "contains_any": lambda a, b: any(
            kw.lower() in a.lower() for kw in b
        ) if isinstance(a, str) and isinstance(b, list) else False,
    }

    def __init__(
        self,
        condition_type: str,
        operator: str,
        value: Any,
    ):
        """
        Initialize condition.

        Args:
            condition_type: Type of condition (token_count, has_code, keywords, etc.)
            operator: Comparison operator
            value: Value to compare against
        """
        self.condition_type = condition_type
        self.operator = operator
        self.value = value

        if operator not in self.OPERATORS:
            raise ValueError(f"Unknown operator: {operator}")

    def evaluate(
        self,
        features: ComplexityFeatures,
        request_text: str,
        domain: str,
    ) -> bool:
        """
        Evaluate condition against features.

        Args:
            features: Extracted features
            request_text: Original request text
            domain: Task domain

        Returns:
            True if condition matches
        """
        # Get the value to compare based on condition type
        actual_value: Any
        if self.condition_type == "keywords":
            actual_value = request_text
        elif self.condition_type == "domain":
            actual_value = domain
        elif self.condition_type == "financial_amount":
            actual_value = features.financial_amount
        else:
            # Get from features dict
            features_dict = features.to_dict()
            actual_value = features_dict.get(self.condition_type)

        # Apply operator
        op_func = self.OPERATORS[self.operator]
        return op_func(actual_value, self.value)


class Rule:
    """A complexity assessment rule."""

    def __init__(
        self,
        name: str,
        description: str,
        weight: int,
        conditions: List[RuleCondition],
        level: ComplexityLevel,
        reason: str,
    ):
        """
        Initialize rule.

        Args:
            name: Rule identifier
            description: Human-readable description
            weight: Priority weight (higher = evaluated first)
            conditions: List of conditions (all must match)
            level: Complexity level when rule matches
            reason: Reason string for match explanation
        """
        self.name = name
        self.description = description
        self.weight = weight
        self.conditions = conditions
        self.level = level
        self.reason = reason

    def evaluate(
        self,
        features: ComplexityFeatures,
        request_text: str,
        domain: str,
    ) -> bool:
        """
        Evaluate rule against features.

        Args:
            features: Extracted features
            request_text: Original request
            domain: Task domain

        Returns:
            True if all conditions match
        """
        return all(
            cond.evaluate(features, request_text, domain)
            for cond in self.conditions
        )


# ============================================================================
# Complexity Assessor
# ============================================================================


class ComplexityAssessor:
    """
    Assess task complexity to determine model routing.

    Uses rule-based evaluation with feature extraction to determine
    the appropriate model tier for a given request.
    """

    # Patterns for feature extraction
    CODE_PATTERNS = [
        r"```[\s\S]*?```",  # Code blocks
        r"def\s+\w+\s*\(",  # Python functions
        r"class\s+\w+",     # Class definitions
        r"function\s+\w+",  # JavaScript functions
        r"import\s+\w+",    # Import statements
        r"from\s+\w+\s+import",  # Python imports
    ]

    URL_PATTERN = r"https?://[^\s<>\"{}|\\^`\[\]]+"

    MONEY_PATTERNS = [
        r"\$\s*([\d,]+(?:\.\d{2})?)\s*(?:million|m|mil)?",  # $1,000 or $1M
        r"([\d,]+(?:\.\d{2})?)\s*(?:dollars|usd)",  # 1000 dollars
        r"\$\s*([\d.]+)\s*(?:million|m|mil)",  # $1.5 million
    ]

    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize assessor.

        Args:
            rules_path: Path to rules YAML file (uses default if not specified)
        """
        self._rules: List[Rule] = []
        self._domain_defaults: Dict[str, str] = {}
        self._keywords: Dict[str, List[str]] = {}
        self._tier_mapping: Dict[str, str] = {}
        self._confidence_config: Dict[str, float] = {}

        # Load rules
        self._load_rules(rules_path)

    def _load_rules(self, path: Optional[str] = None) -> None:
        """Load rules from YAML configuration."""
        if path is None:
            path = self._find_rules_path()

        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Rules file not found: {path}, using defaults")
            self._set_default_rules()
            return
        except yaml.YAMLError as e:
            logger.error(f"Error parsing rules YAML: {e}")
            self._set_default_rules()
            return

        # Parse rules
        for rule_data in config.get("rules", []):
            try:
                conditions = [
                    RuleCondition(
                        condition_type=c["type"],
                        operator=c["operator"],
                        value=c["value"],
                    )
                    for c in rule_data.get("conditions", [])
                ]

                rule = Rule(
                    name=rule_data["name"],
                    description=rule_data.get("description", ""),
                    weight=rule_data.get("weight", 50),
                    conditions=conditions,
                    level=ComplexityLevel(rule_data["level"]),
                    reason=rule_data.get("reason", ""),
                )
                self._rules.append(rule)
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping invalid rule: {e}")

        # Sort rules by weight (descending)
        self._rules.sort(key=lambda r: r.weight, reverse=True)

        # Load other config
        self._domain_defaults = config.get("domain_defaults", {"default": "medium"})
        self._keywords = config.get("keywords", {})
        self._tier_mapping = config.get("tier_mapping", {
            "trivial": "low",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "high",
        })
        self._confidence_config = config.get("confidence", {
            "min_confidence": 0.5,
            "multi_match_boost": 0.1,
            "ambiguity_penalty": 0.2,
        })

    def _find_rules_path(self) -> str:
        """Find rules file path."""
        candidates = [
            DEFAULT_RULES_PATH,
            f"../{DEFAULT_RULES_PATH}",
            str(Path(__file__).parent.parent.parent / DEFAULT_RULES_PATH),
        ]

        for candidate in candidates:
            if Path(candidate).exists():
                return candidate

        return DEFAULT_RULES_PATH

    def _set_default_rules(self) -> None:
        """Set default rules when config not available."""
        self._rules = [
            Rule(
                name="default_high",
                description="Default high complexity rule",
                weight=70,
                conditions=[],
                level=ComplexityLevel.HIGH,
                reason="Default high complexity",
            ),
        ]
        self._domain_defaults = {"default": "medium"}
        self._tier_mapping = {
            "trivial": "low",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "critical": "high",
        }
        self._confidence_config = {
            "min_confidence": 0.5,
            "multi_match_boost": 0.1,
            "ambiguity_penalty": 0.2,
        }

    def extract_features(
        self,
        request: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ComplexityFeatures:
        """
        Extract features from a request for complexity assessment.

        Args:
            request: The request text
            domain: Task domain
            context: Optional additional context

        Returns:
            Extracted features
        """
        context = context or {}

        features = ComplexityFeatures()

        # Basic metrics
        features.word_count = len(request.split())
        # Rough token estimate (words * 1.3)
        features.token_count = context.get("token_count", int(features.word_count * 1.3))

        # Detect code
        request_lower = request.lower()
        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                features.has_code = True
                break

        # Check code keywords
        code_keywords = self._keywords.get("code_indicators", [])
        if any(kw.lower() in request_lower for kw in code_keywords):
            features.has_code = True

        # Detect URLs
        features.has_urls = bool(re.search(self.URL_PATTERN, request))
        features.references_external = features.has_urls

        # Detect multi-step
        multi_step_keywords = self._keywords.get("multi_step_indicators", [])
        features.requires_multi_step = any(
            kw.lower() in request_lower for kw in multi_step_keywords
        )

        # Detect creativity
        creativity_keywords = self._keywords.get("creativity_indicators", [])
        features.requires_creativity = any(
            kw.lower() in request_lower for kw in creativity_keywords
        )

        # Extract financial amount
        features.financial_amount = self._extract_financial_amount(request)

        # Detect domain from keywords
        features.detected_domain = self._detect_domain(request)

        # Detect matching keywords
        for level in ["critical", "high", "medium", "low"]:
            keywords = self._keywords.get(level, [])
            for kw in keywords:
                if kw.lower() in request_lower:
                    features.detected_keywords.add(kw)

        # Estimate output length (heuristic based on request type)
        features.estimated_output_length = self._estimate_output_length(
            request, features
        )

        return features

    def _extract_financial_amount(self, text: str) -> Optional[float]:
        """Extract financial amount from text."""
        text_lower = text.lower()

        for pattern in self.MONEY_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    amount_str = match.group(1).replace(",", "")
                    amount = float(amount_str)

                    # Check for million modifier
                    full_match = match.group(0).lower()
                    if "million" in full_match or full_match.endswith("m"):
                        amount *= 1_000_000

                    return amount
                except (ValueError, IndexError):
                    continue

        return None

    def _detect_domain(self, text: str) -> Optional[str]:
        """Detect domain from text content."""
        text_lower = text.lower()

        # Check critical domains first
        critical_keywords = self._keywords.get("critical", [])
        if any(kw.lower() in text_lower for kw in critical_keywords):
            if "legal" in text_lower or "contract" in text_lower:
                return "legal"
            if "compliance" in text_lower or "regulatory" in text_lower:
                return "compliance"
            if "financial" in text_lower or "transaction" in text_lower:
                return "financial"

        # Check for code domain
        code_indicators = self._keywords.get("code_indicators", [])
        if any(kw.lower() in text_lower for kw in code_indicators):
            return "code_generation"

        return None

    def _estimate_output_length(
        self,
        request: str,
        features: ComplexityFeatures,
    ) -> int:
        """Estimate expected output length in lines."""
        # Heuristics based on request type
        base_length = 50

        if features.has_code:
            base_length = 100
            # Look for indicators of large output
            if "full" in request.lower() or "complete" in request.lower():
                base_length = 300
            if "application" in request.lower() or "system" in request.lower():
                base_length = 500

        if features.requires_multi_step:
            base_length = int(base_length * 1.5)

        return base_length

    def assess(
        self,
        request: str,
        domain: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> ComplexityResult:
        """
        Assess complexity of a request.

        Args:
            request: The request text
            domain: Task domain (e.g., "code_generation", "legal")
            context: Optional additional context

        Returns:
            ComplexityResult with level, tier, confidence, and reasons
        """
        # Extract features
        features = self.extract_features(request, domain, context)

        # Evaluate rules in priority order
        matched_rules: List[str] = []
        reasons: List[str] = []
        level: Optional[ComplexityLevel] = None
        confidence = self._confidence_config.get("min_confidence", 0.5)

        for rule in self._rules:
            if rule.evaluate(features, request, domain):
                matched_rules.append(rule.name)
                reasons.append(rule.reason)

                # First match sets the level
                if level is None:
                    level = rule.level

                # Boost confidence for multiple matches
                confidence += self._confidence_config.get("multi_match_boost", 0.1)

        # Apply domain default if no rules matched
        if level is None:
            level_str = self._domain_defaults.get(
                domain,
                self._domain_defaults.get("default", "medium")
            )
            level = ComplexityLevel(level_str)
            reasons.append(f"Domain default for '{domain}'")

        # Map level to tier
        tier = self._tier_mapping.get(level.value, "medium")

        # Apply ambiguity penalty if mixed signals
        if len(matched_rules) > 1:
            # Check if rules suggest different levels
            rule_levels = set()
            for rule_name in matched_rules:
                for rule in self._rules:
                    if rule.name == rule_name:
                        rule_levels.add(rule.level)

            if len(rule_levels) > 1:
                confidence -= self._confidence_config.get("ambiguity_penalty", 0.2)

        return ComplexityResult(
            level=level,
            recommended_tier=tier,
            confidence=confidence,
            reasons=reasons,
            features=features,
            matched_rules=matched_rules,
        )

    def get_tier_for_level(self, level: ComplexityLevel) -> str:
        """Get recommended tier for a complexity level."""
        return self._tier_mapping.get(level.value, "medium")

    def list_rules(self) -> List[Dict[str, Any]]:
        """List all rules with their configuration."""
        return [
            {
                "name": rule.name,
                "description": rule.description,
                "weight": rule.weight,
                "level": rule.level.value,
                "reason": rule.reason,
            }
            for rule in self._rules
        ]


# ============================================================================
# Convenience Functions
# ============================================================================


# Module-level cache
_assessor_cache: Optional[ComplexityAssessor] = None


def get_assessor(rules_path: Optional[str] = None) -> ComplexityAssessor:
    """
    Get complexity assessor (cached).

    Args:
        rules_path: Optional path to rules file

    Returns:
        ComplexityAssessor instance
    """
    global _assessor_cache

    if _assessor_cache is None:
        _assessor_cache = ComplexityAssessor(rules_path)

    return _assessor_cache


def assess_complexity(
    request: str,
    domain: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> ComplexityResult:
    """
    Quick complexity assessment.

    Args:
        request: Request text
        domain: Task domain
        context: Optional context

    Returns:
        ComplexityResult
    """
    return get_assessor().assess(request, domain, context)


def reset_assessor() -> None:
    """Reset cached assessor."""
    global _assessor_cache
    _assessor_cache = None
