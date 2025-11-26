"""
PHASE 7.5: Request Routing System

Routes incoming requests to the appropriate specialist domain.
Uses hybrid classification: fast keywords with semantic fallback.

Usage:
    from core.routing import (
        DomainClassifier,
        get_domain_classifier,
        ClassificationResult,
    )

    # Classify a request
    classifier = get_domain_classifier()
    result = await classifier.classify("write a python script")
    print(f"Route to: {result.domain} (confidence={result.confidence})")

    # Check classification method
    if result.method == "keyword":
        print(f"Matched keywords: {result.matched_keywords}")
    elif result.method == "semantic":
        print(f"Reasoning: {result.reasoning}")
"""

from .keyword_classifier import (
    # Result model
    ClassificationResult,
    # Config
    DomainPatterns,
    PatternConfig,
    # Classifier
    KeywordClassifier,
    get_keyword_classifier,
    reset_keyword_classifier,
)

from .semantic_classifier import (
    # Config
    SemanticClassifierConfig,
    # Classifier
    SemanticClassifier,
    get_semantic_classifier,
    reset_semantic_classifier,
    # Prompt
    CLASSIFICATION_PROMPT,
)

from .classifier import (
    # Config
    DomainClassifierConfig,
    # Stats
    ClassificationStats,
    # Classifier
    DomainClassifier,
    get_domain_classifier,
    reset_domain_classifier,
)


__all__ = [
    # Result model
    "ClassificationResult",
    # Keyword classifier
    "DomainPatterns",
    "PatternConfig",
    "KeywordClassifier",
    "get_keyword_classifier",
    "reset_keyword_classifier",
    # Semantic classifier
    "SemanticClassifierConfig",
    "SemanticClassifier",
    "get_semantic_classifier",
    "reset_semantic_classifier",
    "CLASSIFICATION_PROMPT",
    # Main classifier
    "DomainClassifierConfig",
    "ClassificationStats",
    "DomainClassifier",
    "get_domain_classifier",
    "reset_domain_classifier",
]
