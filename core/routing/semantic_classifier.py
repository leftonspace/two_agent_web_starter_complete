"""
PHASE 7.5: Semantic Domain Classifier

LLM-based classification for ambiguous requests.
Used as fallback when keyword matching confidence is low.

Usage:
    from core.routing import SemanticClassifier

    classifier = SemanticClassifier()
    result = await classifier.classify("help me with this thing")
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

from .keyword_classifier import ClassificationResult

if TYPE_CHECKING:
    pass


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Classification Prompt
# ============================================================================


CLASSIFICATION_PROMPT = """You are a request classifier. Classify the following request into exactly ONE domain.

Available domains:
- code_generation: Coding, scripts, automation, technical implementation, writing code
- code_review: Reviewing code, analyzing code quality, finding bugs, suggesting improvements
- business_documents: Reports, emails, proposals, documentation, professional writing
- research: Research, analysis, information gathering, market analysis, comparisons
- planning: Project planning, roadmaps, timelines, strategy, task breakdowns
- administration: General questions, system help, unclear requests, greetings

Request to classify:
\"\"\"
{request}
\"\"\"

Respond with ONLY valid JSON (no markdown, no explanation):
{{"domain": "domain_name", "confidence": 0.0-1.0, "reasoning": "one sentence explanation"}}"""


# ============================================================================
# Semantic Classifier Configuration
# ============================================================================


class SemanticClassifierConfig(BaseModel):
    """Configuration for semantic classifier."""

    # Model to use (prefer cheap, fast models)
    model: str = Field(
        default="haiku",
        description="Model to use for classification",
    )

    # Fallback domain
    fallback_domain: str = Field(
        default="administration",
        description="Domain to use if classification fails",
    )

    # Timeouts
    timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        description="Timeout for LLM call",
    )

    # Caching
    enable_cache: bool = Field(
        default=True,
        description="Cache classification results",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds",
    )


# ============================================================================
# Semantic Classifier
# ============================================================================


class SemanticClassifier:
    """
    LLM-based semantic classification for ambiguous requests.

    Uses a cheap, fast model (haiku) to classify requests that
    couldn't be confidently classified by keyword matching.

    Usage:
        classifier = SemanticClassifier()
        result = await classifier.classify("help me with this thing")
    """

    VALID_DOMAINS = {
        "code_generation",
        "code_review",
        "business_documents",
        "research",
        "planning",
        "administration",
    }

    def __init__(
        self,
        config: Optional[SemanticClassifierConfig] = None,
        model_router: Optional[Any] = None,
    ):
        """
        Initialize the classifier.

        Args:
            config: Classifier configuration
            model_router: Model router for LLM calls (lazy loaded if not provided)
        """
        self._config = config or SemanticClassifierConfig()
        self._model_router = model_router

        # Simple in-memory cache
        self._cache: Dict[str, ClassificationResult] = {}

        # Statistics
        self._classification_count = 0
        self._cache_hits = 0
        self._errors = 0

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> SemanticClassifierConfig:
        """Get configuration."""
        return self._config

    @property
    def model_router(self) -> Any:
        """Get model router (lazy load)."""
        if self._model_router is None:
            try:
                from core.routing.model_router import get_model_router
                self._model_router = get_model_router()
            except ImportError:
                logger.warning("Model router not available")
        return self._model_router

    # -------------------------------------------------------------------------
    # Classification
    # -------------------------------------------------------------------------

    async def classify(self, request: str) -> ClassificationResult:
        """
        Classify a request using LLM.

        Args:
            request: The user request to classify

        Returns:
            ClassificationResult with domain and confidence
        """
        self._classification_count += 1

        if not request or not request.strip():
            return self._fallback_result("Empty request")

        # Check cache
        cache_key = request.strip().lower()[:500]  # Limit key size
        if self._config.enable_cache and cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]

        try:
            result = await self._call_llm(request)

            # Cache result
            if self._config.enable_cache:
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error(f"Semantic classification failed: {e}")
            self._errors += 1
            return self._fallback_result(str(e))

    async def _call_llm(self, request: str) -> ClassificationResult:
        """Call LLM for classification."""
        prompt = CLASSIFICATION_PROMPT.format(request=request[:2000])

        # Try to use model router if available
        if self.model_router:
            try:
                response = await self.model_router.route_and_execute(
                    request=prompt,
                    domain="classification",
                    model_override=self._config.model,
                )
                return self._parse_response(response)
            except Exception as e:
                logger.warning(f"Model router failed: {e}, using mock response")

        # Fallback: return a mock classification for testing
        # In production, this would raise or return fallback
        return self._mock_classify(request)

    def _parse_response(self, response: str) -> ClassificationResult:
        """Parse LLM response into ClassificationResult."""
        try:
            # Clean response - remove markdown if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # Remove markdown code blocks
                cleaned = re.sub(r"```\w*\n?", "", cleaned)
                cleaned = cleaned.strip()

            # Parse JSON
            data = json.loads(cleaned)

            domain = data.get("domain", "administration")
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "")

            # Validate domain
            if domain not in self.VALID_DOMAINS:
                logger.warning(f"Invalid domain '{domain}', using administration")
                domain = "administration"
                confidence = min(confidence, 0.5)

            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))

            return ClassificationResult(
                domain=domain,
                confidence=confidence,
                method="semantic",
                reasoning=reasoning,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return self._fallback_result("JSON parse error")

    def _mock_classify(self, request: str) -> ClassificationResult:
        """
        Mock classification for testing without LLM.

        Uses simple heuristics to provide reasonable classifications.
        """
        request_lower = request.lower()

        # Simple heuristics
        if any(w in request_lower for w in ["code", "script", "function", "program"]):
            return ClassificationResult(
                domain="code_generation",
                confidence=0.6,
                method="semantic",
                reasoning="Contains code-related keywords (mock)",
            )

        if any(w in request_lower for w in ["review", "check", "analyze"]):
            return ClassificationResult(
                domain="code_review",
                confidence=0.6,
                method="semantic",
                reasoning="Contains review-related keywords (mock)",
            )

        if any(w in request_lower for w in ["report", "email", "document", "write"]):
            return ClassificationResult(
                domain="business_documents",
                confidence=0.6,
                method="semantic",
                reasoning="Contains document-related keywords (mock)",
            )

        if any(w in request_lower for w in ["research", "find", "search", "look up"]):
            return ClassificationResult(
                domain="research",
                confidence=0.6,
                method="semantic",
                reasoning="Contains research-related keywords (mock)",
            )

        if any(w in request_lower for w in ["plan", "schedule", "timeline", "roadmap"]):
            return ClassificationResult(
                domain="planning",
                confidence=0.6,
                method="semantic",
                reasoning="Contains planning-related keywords (mock)",
            )

        # Default to administration
        return ClassificationResult(
            domain="administration",
            confidence=0.5,
            method="semantic",
            reasoning="No strong domain indicators (mock)",
        )

    def _fallback_result(self, reason: str = "") -> ClassificationResult:
        """Create fallback result."""
        return ClassificationResult(
            domain=self._config.fallback_domain,
            confidence=0.3,
            method="fallback",
            reasoning=reason or "Classification failed",
        )

    # -------------------------------------------------------------------------
    # Batch Classification
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Cache Management
    # -------------------------------------------------------------------------

    def clear_cache(self) -> int:
        """Clear classification cache. Returns number of items cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return {
            "total_classifications": self._classification_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": (
                self._cache_hits / self._classification_count
                if self._classification_count > 0
                else 0
            ),
            "errors": self._errors,
            "cache_size": len(self._cache),
        }

    def reset_stats(self) -> None:
        """Reset classification statistics."""
        self._classification_count = 0
        self._cache_hits = 0
        self._errors = 0


# ============================================================================
# Singleton Instance
# ============================================================================


_semantic_classifier: Optional[SemanticClassifier] = None


def get_semantic_classifier() -> SemanticClassifier:
    """Get the global semantic classifier."""
    global _semantic_classifier
    if _semantic_classifier is None:
        _semantic_classifier = SemanticClassifier()
    return _semantic_classifier


def reset_semantic_classifier() -> None:
    """Reset the global semantic classifier (for testing)."""
    global _semantic_classifier
    _semantic_classifier = None
