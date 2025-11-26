"""
PHASE 7.5: Keyword-Based Domain Classifier

Fast, free classification using pattern matching.
No LLM calls required.

Usage:
    from core.routing import KeywordClassifier

    classifier = KeywordClassifier()
    result = classifier.classify("write a python script")
    # ClassificationResult(domain="code_generation", confidence=0.9, method="keyword")
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple

import yaml
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Classification Result
# ============================================================================


class ClassificationResult(BaseModel):
    """Result of domain classification."""

    domain: str = Field(..., description="Classified domain")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence",
    )
    method: Literal["keyword", "semantic", "fallback"] = Field(
        ...,
        description="Classification method used",
    )
    matched_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that matched (for keyword method)",
    )
    reasoning: str = Field(
        default="",
        description="Explanation (for semantic method)",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "matched_keywords": self.matched_keywords,
            "reasoning": self.reasoning,
        }


# ============================================================================
# Pattern Configuration
# ============================================================================


class DomainPatterns(BaseModel):
    """Patterns for a single domain."""

    description: str = ""
    high_confidence: List[str] = Field(default_factory=list)
    medium_confidence: List[str] = Field(default_factory=list)
    low_confidence: List[str] = Field(default_factory=list)


class PatternConfig(BaseModel):
    """Full pattern configuration."""

    domains: Dict[str, DomainPatterns] = Field(default_factory=dict)
    fallback: Dict[str, Any] = Field(
        default_factory=lambda: {
            "domain": "administration",
            "confidence": 0.3,
        }
    )
    thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "high_confidence_score": 0.9,
            "medium_confidence_score": 0.7,
            "low_confidence_score": 0.5,
            "semantic_fallback_threshold": 0.8,
            "minimum_confidence": 0.3,
        }
    )


# ============================================================================
# Keyword Classifier
# ============================================================================


class KeywordClassifier:
    """
    Fast keyword-based domain classification.

    Uses pattern matching from config/routing/patterns.yaml.
    No LLM calls required - instant classification.

    Usage:
        classifier = KeywordClassifier()
        result = classifier.classify("write a python script to process data")
        # Returns: ClassificationResult(domain="code_generation", confidence=0.9, ...)
    """

    DEFAULT_CONFIG_PATH = "config/routing/patterns.yaml"

    def __init__(
        self,
        config_path: Optional[str] = None,
        config: Optional[PatternConfig] = None,
    ):
        """
        Initialize the classifier.

        Args:
            config_path: Path to patterns YAML file
            config: Pre-loaded configuration (overrides config_path)
        """
        if config:
            self._config = config
        else:
            self._config = self._load_config(config_path or self.DEFAULT_CONFIG_PATH)

        # Pre-compile patterns for faster matching
        self._compiled_patterns = self._compile_patterns()

        # Statistics
        self._classification_count = 0
        self._domain_counts: Dict[str, int] = {}

    # -------------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------------

    def _load_config(self, path: str) -> PatternConfig:
        """Load configuration from YAML file."""
        config_path = Path(path)

        if not config_path.exists():
            logger.warning(f"Pattern config not found at {path}, using defaults")
            return PatternConfig()

        try:
            with open(config_path, "r") as f:
                raw = yaml.safe_load(f)

            # Parse domains
            domains = {}
            for domain_name, domain_data in raw.get("domains", {}).items():
                domains[domain_name] = DomainPatterns(**domain_data)

            return PatternConfig(
                domains=domains,
                fallback=raw.get("fallback", {}),
                thresholds=raw.get("thresholds", {}),
            )

        except Exception as e:
            logger.error(f"Failed to load pattern config: {e}")
            return PatternConfig()

    def _compile_patterns(self) -> Dict[str, Dict[str, List[re.Pattern]]]:
        """Compile patterns for faster matching."""
        compiled: Dict[str, Dict[str, List[re.Pattern]]] = {}

        for domain_name, patterns in self._config.domains.items():
            compiled[domain_name] = {
                "high": [
                    re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                    for kw in patterns.high_confidence
                ],
                "medium": [
                    re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                    for kw in patterns.medium_confidence
                ],
                "low": [
                    re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
                    for kw in patterns.low_confidence
                ],
            }

        return compiled

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> PatternConfig:
        """Get pattern configuration."""
        return self._config

    @property
    def domains(self) -> List[str]:
        """Get list of configured domains."""
        return list(self._config.domains.keys())

    @property
    def thresholds(self) -> Dict[str, float]:
        """Get confidence thresholds."""
        return self._config.thresholds

    # -------------------------------------------------------------------------
    # Classification
    # -------------------------------------------------------------------------

    def classify(self, request: str) -> ClassificationResult:
        """
        Classify a request to a domain using keyword matching.

        Args:
            request: The user request to classify

        Returns:
            ClassificationResult with domain and confidence
        """
        self._classification_count += 1

        if not request or not request.strip():
            return self._fallback_result()

        request_lower = request.lower()

        # Track best match
        best_domain: Optional[str] = None
        best_confidence = 0.0
        matched_keywords: List[str] = []

        # Check each domain
        for domain_name, patterns in self._compiled_patterns.items():
            domain_confidence, domain_matches = self._check_domain(
                request_lower,
                patterns,
            )

            if domain_confidence > best_confidence:
                best_domain = domain_name
                best_confidence = domain_confidence
                matched_keywords = domain_matches

        # Update statistics
        if best_domain:
            self._domain_counts[best_domain] = (
                self._domain_counts.get(best_domain, 0) + 1
            )

        # Return result
        if best_domain and best_confidence > 0:
            return ClassificationResult(
                domain=best_domain,
                confidence=best_confidence,
                method="keyword",
                matched_keywords=matched_keywords,
            )

        return self._fallback_result()

    def _check_domain(
        self,
        request: str,
        patterns: Dict[str, List[re.Pattern]],
    ) -> Tuple[float, List[str]]:
        """
        Check how well a request matches a domain's patterns.

        Returns:
            Tuple of (confidence, matched_keywords)
        """
        matched: List[str] = []
        best_confidence = 0.0

        thresholds = self._config.thresholds

        # Check high confidence patterns
        for pattern in patterns["high"]:
            if pattern.search(request):
                matched.append(pattern.pattern.replace(r"\b", ""))
                confidence = thresholds.get("high_confidence_score", 0.9)
                if confidence > best_confidence:
                    best_confidence = confidence

        # Check medium confidence if no high found
        if best_confidence < thresholds.get("high_confidence_score", 0.9):
            for pattern in patterns["medium"]:
                if pattern.search(request):
                    matched.append(pattern.pattern.replace(r"\b", ""))
                    confidence = thresholds.get("medium_confidence_score", 0.7)
                    if confidence > best_confidence:
                        best_confidence = confidence

        # Check low confidence if nothing better
        if best_confidence < thresholds.get("medium_confidence_score", 0.7):
            for pattern in patterns["low"]:
                if pattern.search(request):
                    matched.append(pattern.pattern.replace(r"\b", ""))
                    confidence = thresholds.get("low_confidence_score", 0.5)
                    if confidence > best_confidence:
                        best_confidence = confidence

        return best_confidence, matched

    def _fallback_result(self) -> ClassificationResult:
        """Create fallback result."""
        fallback = self._config.fallback
        return ClassificationResult(
            domain=fallback.get("domain", "administration"),
            confidence=fallback.get("confidence", 0.3),
            method="fallback",
            matched_keywords=[],
        )

    # -------------------------------------------------------------------------
    # Batch Classification
    # -------------------------------------------------------------------------

    def classify_batch(self, requests: List[str]) -> List[ClassificationResult]:
        """
        Classify multiple requests.

        Args:
            requests: List of requests to classify

        Returns:
            List of classification results
        """
        return [self.classify(request) for request in requests]

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return {
            "total_classifications": self._classification_count,
            "domain_counts": self._domain_counts.copy(),
            "configured_domains": self.domains,
        }

    def reset_stats(self) -> None:
        """Reset classification statistics."""
        self._classification_count = 0
        self._domain_counts.clear()


# ============================================================================
# Singleton Instance
# ============================================================================


_keyword_classifier: Optional[KeywordClassifier] = None


def get_keyword_classifier() -> KeywordClassifier:
    """Get the global keyword classifier."""
    global _keyword_classifier
    if _keyword_classifier is None:
        _keyword_classifier = KeywordClassifier()
    return _keyword_classifier


def reset_keyword_classifier() -> None:
    """Reset the global keyword classifier (for testing)."""
    global _keyword_classifier
    _keyword_classifier = None
