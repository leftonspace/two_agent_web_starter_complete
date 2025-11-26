"""
PHASE 7.5: Hybrid Domain Classifier

Combines fast keyword matching with LLM semantic classification.
Routes incoming requests to the appropriate specialist pool.

Strategy:
1. Try keyword matching first (fast, free)
2. If confidence >= threshold, use keyword result
3. Otherwise, use semantic classification (LLM)
4. Default to "administration" if still unclear

Usage:
    from core.routing import DomainClassifier, get_domain_classifier

    classifier = get_domain_classifier()
    result = await classifier.classify("write a python script")
    print(f"Domain: {result.domain}, Confidence: {result.confidence}")
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .keyword_classifier import (
    KeywordClassifier,
    ClassificationResult,
    get_keyword_classifier,
)
from .semantic_classifier import (
    SemanticClassifier,
    get_semantic_classifier,
)


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Classifier Configuration
# ============================================================================


class DomainClassifierConfig(BaseModel):
    """Configuration for hybrid domain classifier."""

    # Threshold for using keyword result without semantic fallback
    keyword_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Use keyword result if confidence >= this",
    )

    # Minimum confidence to accept any result
    minimum_confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Below this, always fallback to administration",
    )

    # Fallback domain
    fallback_domain: str = Field(
        default="administration",
        description="Domain to use when classification fails",
    )

    # Whether to use semantic classifier
    enable_semantic: bool = Field(
        default=True,
        description="Enable semantic classification fallback",
    )

    # Maximum request length to process
    max_request_length: int = Field(
        default=5000,
        ge=100,
        description="Truncate requests longer than this",
    )


# ============================================================================
# Classification Statistics
# ============================================================================


class ClassificationStats(BaseModel):
    """Statistics for domain classification."""

    total_classifications: int = 0
    keyword_classifications: int = 0
    semantic_classifications: int = 0
    fallback_classifications: int = 0

    # By domain
    domain_counts: Dict[str, int] = Field(default_factory=dict)

    # Confidence distribution
    high_confidence_count: int = 0  # >= 0.8
    medium_confidence_count: int = 0  # 0.5 - 0.8
    low_confidence_count: int = 0  # < 0.5

    # Timing
    avg_keyword_time_ms: float = 0.0
    avg_semantic_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total_classifications,
            "by_method": {
                "keyword": self.keyword_classifications,
                "semantic": self.semantic_classifications,
                "fallback": self.fallback_classifications,
            },
            "by_domain": self.domain_counts,
            "by_confidence": {
                "high": self.high_confidence_count,
                "medium": self.medium_confidence_count,
                "low": self.low_confidence_count,
            },
        }


# ============================================================================
# Domain Classifier
# ============================================================================


class DomainClassifier:
    """
    Hybrid domain classifier using keywords with semantic fallback.

    Classification strategy:
    1. Try keyword matching (fast, free)
    2. If confidence >= 0.8, use keyword result
    3. Otherwise, use semantic classification (LLM)
    4. If semantic confidence < 0.5, default to administration

    Usage:
        classifier = DomainClassifier()

        # Single classification
        result = await classifier.classify("write a python script")

        # Batch classification
        results = await classifier.classify_batch(["request1", "request2"])
    """

    def __init__(
        self,
        config: Optional[DomainClassifierConfig] = None,
        keyword_classifier: Optional[KeywordClassifier] = None,
        semantic_classifier: Optional[SemanticClassifier] = None,
    ):
        """
        Initialize the classifier.

        Args:
            config: Classifier configuration
            keyword_classifier: Keyword classifier instance
            semantic_classifier: Semantic classifier instance
        """
        self._config = config or DomainClassifierConfig()
        self._keyword_classifier = keyword_classifier
        self._semantic_classifier = semantic_classifier

        # Statistics
        self._stats = ClassificationStats()
        self._initialized_at = datetime.utcnow()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> DomainClassifierConfig:
        """Get configuration."""
        return self._config

    @property
    def keyword_classifier(self) -> KeywordClassifier:
        """Get keyword classifier (lazy load)."""
        if self._keyword_classifier is None:
            self._keyword_classifier = get_keyword_classifier()
        return self._keyword_classifier

    @property
    def semantic_classifier(self) -> SemanticClassifier:
        """Get semantic classifier (lazy load)."""
        if self._semantic_classifier is None:
            self._semantic_classifier = get_semantic_classifier()
        return self._semantic_classifier

    @property
    def stats(self) -> ClassificationStats:
        """Get classification statistics."""
        return self._stats

    @property
    def domains(self) -> List[str]:
        """Get list of supported domains."""
        return self.keyword_classifier.domains

    # -------------------------------------------------------------------------
    # Classification
    # -------------------------------------------------------------------------

    async def classify(self, request: str) -> ClassificationResult:
        """
        Classify a request to a domain.

        Args:
            request: The user request to classify

        Returns:
            ClassificationResult with domain and confidence
        """
        self._stats.total_classifications += 1

        # Validate request
        if not request or not request.strip():
            return self._fallback_result("Empty request")

        # Truncate if too long
        if len(request) > self._config.max_request_length:
            request = request[:self._config.max_request_length]

        # Step 1: Try keyword matching (fast, free)
        keyword_result = self.keyword_classifier.classify(request)

        logger.debug(
            f"Keyword classification: {keyword_result.domain} "
            f"(confidence={keyword_result.confidence:.2f})"
        )

        # Step 2: Check if confidence is high enough
        if keyword_result.confidence >= self._config.keyword_confidence_threshold:
            self._stats.keyword_classifications += 1
            self._update_stats(keyword_result)
            return keyword_result

        # Step 3: Use semantic fallback if enabled
        if self._config.enable_semantic:
            semantic_result = await self.semantic_classifier.classify(request)

            logger.debug(
                f"Semantic classification: {semantic_result.domain} "
                f"(confidence={semantic_result.confidence:.2f})"
            )

            # Use semantic if more confident than keyword
            if semantic_result.confidence > keyword_result.confidence:
                self._stats.semantic_classifications += 1
                self._update_stats(semantic_result)

                # Check minimum confidence
                if semantic_result.confidence < self._config.minimum_confidence_threshold:
                    return self._fallback_result(
                        f"Low confidence ({semantic_result.confidence:.2f})"
                    )

                return semantic_result

        # Step 4: Use keyword result if it's at least minimum confidence
        if keyword_result.confidence >= self._config.minimum_confidence_threshold:
            self._stats.keyword_classifications += 1
            self._update_stats(keyword_result)
            return keyword_result

        # Step 5: Fallback to administration
        return self._fallback_result("No confident classification")

    async def classify_batch(
        self,
        requests: List[str],
    ) -> List[ClassificationResult]:
        """
        Classify multiple requests.

        Args:
            requests: List of requests to classify

        Returns:
            List of classification results
        """
        results = []
        for request in requests:
            result = await self.classify(request)
            results.append(result)
        return results

    def _fallback_result(self, reason: str = "") -> ClassificationResult:
        """Create fallback result."""
        self._stats.fallback_classifications += 1

        result = ClassificationResult(
            domain=self._config.fallback_domain,
            confidence=0.3,
            method="fallback",
            reasoning=reason,
        )

        self._update_stats(result)
        return result

    def _update_stats(self, result: ClassificationResult) -> None:
        """Update statistics with classification result."""
        # By domain
        self._stats.domain_counts[result.domain] = (
            self._stats.domain_counts.get(result.domain, 0) + 1
        )

        # By confidence
        if result.confidence >= 0.8:
            self._stats.high_confidence_count += 1
        elif result.confidence >= 0.5:
            self._stats.medium_confidence_count += 1
        else:
            self._stats.low_confidence_count += 1

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return {
            **self._stats.to_dict(),
            "keyword_stats": self.keyword_classifier.get_stats(),
            "semantic_stats": self.semantic_classifier.get_stats(),
            "initialized_at": self._initialized_at.isoformat(),
        }

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self._stats = ClassificationStats()
        self.keyword_classifier.reset_stats()
        self.semantic_classifier.reset_stats()

    def clear_cache(self) -> int:
        """Clear semantic classifier cache."""
        return self.semantic_classifier.clear_cache()


# ============================================================================
# Singleton Instance
# ============================================================================


_domain_classifier: Optional[DomainClassifier] = None


def get_domain_classifier() -> DomainClassifier:
    """Get the global domain classifier."""
    global _domain_classifier
    if _domain_classifier is None:
        _domain_classifier = DomainClassifier()
    return _domain_classifier


def reset_domain_classifier() -> None:
    """Reset the global domain classifier (for testing)."""
    global _domain_classifier
    _domain_classifier = None
