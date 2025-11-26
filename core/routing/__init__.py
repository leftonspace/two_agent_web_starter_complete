"""
PHASE 7.5: Request Routing System

Routes incoming requests to the appropriate specialist domain.
Uses hybrid classification: fast keywords with semantic fallback.

Usage:
    from core.routing import (
        # Classification
        DomainClassifier,
        get_domain_classifier,
        ClassificationResult,

        # Full routing
        TaskRouter,
        get_task_router,
        RoutingResult,
        TaskResult,
    )

    # Classify a request
    classifier = get_domain_classifier()
    result = await classifier.classify("write a python script")

    # Full routing and execution
    router = get_task_router()
    routing, result = await router.route_and_execute("write a python script")
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

from .router import (
    # Errors
    ExecutionError,
    # Models
    ModelSelection,
    RoutingResult,
    TaskResult,
    # Config
    RouterConfig,
    # Router
    TaskRouter,
    get_task_router,
    reset_task_router,
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
    # Router
    "ExecutionError",
    "ModelSelection",
    "RoutingResult",
    "TaskResult",
    "RouterConfig",
    "TaskRouter",
    "get_task_router",
    "reset_task_router",
]
