# Phase 7: Hybrid Guardrails Proposal

> *"The most sophisticated security systems, sir, are those that combine multiple detection methods. A single sensor can be fooled; a symphony of sensors working in concert is far more difficult to deceive."*

**Document Version:** 1.0.0
**Status:** Proposal
**Author:** JARVIS Architecture Team
**Date:** 2025-11-25

---

## Executive Summary

This document proposes Phase 7 enhancements to JARVIS's security architecture, implementing a **Hybrid Semantic Router** that combines dense embeddings with sparse term matching, along with symmetric output guardrails. This approach addresses edge cases where pure semantic analysis fails and closes the gap in output validation.

---

## Current JARVIS Architecture vs. Hybrid Approach

### What JARVIS Already Has

| Hybrid Framework Component | JARVIS Equivalent | Location |
|---------------------------|-------------------|----------|
| Dense Semantic Vectors | Intent classification in `jarvis_chat.py` | `agent/jarvis_chat.py` |
| Pattern Matching | `INJECTION_PATTERNS` regex | `agent/prompt_security.py` |
| Input Guardrails | Phase 1 security layer | `agent/security/` |
| LLM Prompting | System prompts with safety instructions | `agent/config/agents.yaml` |
| Decision Layer | Approval workflows | `agent/permissions.py` |

### What's Missing or Underdeveloped

1. **True Hybrid Router** - Current approach uses serial checks (pattern → semantic), not weighted parallel scoring
2. **Sparse Term Matching (BM25/TF-IDF)** - Only regex patterns, no statistical term importance
3. **Dedicated Output Guardrails** - Mentioned but not implemented as distinct layer
4. **Hierarchical Topic Routing** - No explicit "allowed/forbidden topics" structure
5. **Fast Vector-Based Routing** - Relies heavily on LLM for classification

---

## Proposed Improvements

### Phase 7.1: Hybrid Semantic Router

```python
# agent/security/hybrid_router.py
"""
PHASE 7.1: Hybrid Semantic Router
Combines dense embeddings + sparse term matching for fast, accurate routing.
"""

from dataclasses import dataclass
from typing import Literal
import numpy as np

@dataclass
class RouteDecision:
    route: Literal["allow", "block", "escalate", "redirect"]
    confidence: float
    matched_category: str
    reasoning: str

class HybridRouter:
    """
    Combines dense semantic vectors with sparse term matching.

    Why Hybrid?
    - Dense alone: "Sell my Tesla" vs "Sell my BYD" look identical semantically
    - Sparse alone: Misses paraphrases and synonyms
    - Hybrid: 51% → 96% accuracy improvement on edge cases
    """

    def __init__(
        self,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        threshold: float = 0.85,
    ):
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.threshold = threshold

        # Pre-computed route embeddings
        self.route_embeddings = {}  # category -> dense vector
        self.route_terms = {}       # category -> BM25 index

        # Define routing categories
        self.categories = {
            "allowed": [
                "code_assistance",
                "file_operations",
                "meeting_management",
                "document_generation",
                "general_conversation",
            ],
            "blocked": [
                "competitor_promotion",
                "illegal_activities",
                "harmful_content",
                "data_exfiltration",
                "prompt_injection",
            ],
            "escalate": [
                "financial_transactions",
                "external_communications",
                "system_modifications",
                "sensitive_data_access",
            ],
        }

    async def route(self, query: str) -> RouteDecision:
        """Route query using hybrid scoring."""

        # Parallel scoring (fast!)
        dense_scores = await self._dense_similarity(query)
        sparse_scores = self._sparse_similarity(query)

        # Weighted combination
        hybrid_scores = {}
        for category in set(dense_scores.keys()) | set(sparse_scores.keys()):
            dense = dense_scores.get(category, 0.0)
            sparse = sparse_scores.get(category, 0.0)
            hybrid_scores[category] = (
                self.dense_weight * dense +
                self.sparse_weight * sparse
            )

        # Find best match
        best_category = max(hybrid_scores, key=hybrid_scores.get)
        confidence = hybrid_scores[best_category]

        # Determine route type
        route = self._category_to_route(best_category)

        return RouteDecision(
            route=route,
            confidence=confidence,
            matched_category=best_category,
            reasoning=self._explain_decision(dense_scores, sparse_scores, best_category)
        )

    async def _dense_similarity(self, query: str) -> dict[str, float]:
        """Compute dense semantic similarity using embeddings."""
        from agent.llm.embeddings import get_embedding

        query_embedding = await get_embedding(query)

        scores = {}
        for category, category_embedding in self.route_embeddings.items():
            # Cosine similarity
            similarity = np.dot(query_embedding, category_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(category_embedding)
            )
            scores[category] = float(similarity)

        return scores

    def _sparse_similarity(self, query: str) -> dict[str, float]:
        """Compute sparse term-based similarity using BM25."""
        from rank_bm25 import BM25Okapi

        query_tokens = self._tokenize(query)

        scores = {}
        for category, bm25_index in self.route_terms.items():
            score = bm25_index.get_scores(query_tokens).max()
            scores[category] = float(score)

        # Normalize to 0-1 range
        max_score = max(scores.values()) if scores else 1.0
        return {k: v / max_score for k, v in scores.items()}

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization for BM25."""
        import re
        return re.findall(r'\w+', text.lower())

    def _category_to_route(self, category: str) -> str:
        """Map category to route type."""
        for route_type, categories in self.categories.items():
            if category in categories:
                return route_type
        return "allow"  # Default

    def _explain_decision(
        self,
        dense_scores: dict,
        sparse_scores: dict,
        best_category: str
    ) -> str:
        """Generate human-readable explanation."""
        return (
            f"Category '{best_category}' selected. "
            f"Dense score: {dense_scores.get(best_category, 0):.3f}, "
            f"Sparse score: {sparse_scores.get(best_category, 0):.3f}"
        )
```

**Why this matters:** The current `prompt_security.py` uses sequential pattern matching then semantic analysis. A true hybrid approach scores both in parallel and combines them, catching edge cases that either method alone would miss.

---

### Phase 7.2: Output Guardrails Layer

```python
# agent/security/output_guardrails.py
"""
PHASE 7.2: Post-Response Guardrails
Validates LLM output before returning to user.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

@dataclass
class CheckResult:
    passed: bool
    check_name: str
    details: str = ""

@dataclass
class GuardrailResult:
    passed: bool
    blocked_by: Optional[str] = None
    sanitized_response: str = ""

class OutputGuardrails:
    """
    Screens LLM responses for:
    - Leaked system prompts
    - PII in responses
    - Hallucinated harmful content
    - Off-topic responses
    - Competitor mentions
    """

    def __init__(self):
        from agent.security.pii_detector import PIIDetector
        from agent.security.hybrid_router import HybridRouter

        self.pii_detector = PIIDetector()
        self.topic_router = HybridRouter()  # Reuse for output!
        self.forbidden_patterns = self._load_forbidden_patterns()

    async def check(self, response: str, original_query: str) -> GuardrailResult:
        """Check response against all output guardrails."""

        checks = await asyncio.gather(
            self._check_prompt_leak(response),
            self._check_pii_exposure(response),
            self._check_topic_drift(response, original_query),
            self._check_harmful_content(response),
            self._check_competitor_mentions(response),
        )

        # Any failure blocks the response
        failures = [c for c in checks if not c.passed]

        if failures:
            return GuardrailResult(
                passed=False,
                blocked_by=failures[0].check_name,
                sanitized_response=self._generate_safe_response(failures),
            )

        return GuardrailResult(passed=True, sanitized_response=response)

    async def _check_prompt_leak(self, response: str) -> CheckResult:
        """Detect if LLM leaked system prompt."""
        leak_indicators = [
            "my system prompt",
            "i was instructed to",
            "my instructions say",
            "as an ai assistant, i",
            "my guidelines state",
            "my programming requires",
            "i am programmed to",
        ]

        response_lower = response.lower()
        for indicator in leak_indicators:
            if indicator in response_lower:
                return CheckResult(
                    passed=False,
                    check_name="prompt_leak",
                    details=f"Potential prompt leak: '{indicator}'"
                )

        return CheckResult(passed=True, check_name="prompt_leak")

    async def _check_pii_exposure(self, response: str) -> CheckResult:
        """Check for PII in response."""
        pii_found = self.pii_detector.detect(response)

        if pii_found:
            return CheckResult(
                passed=False,
                check_name="pii_exposure",
                details=f"PII detected: {[p.type for p in pii_found]}"
            )

        return CheckResult(passed=True, check_name="pii_exposure")

    async def _check_topic_drift(
        self,
        response: str,
        original_query: str
    ) -> CheckResult:
        """Ensure response stays on-topic and within allowed domains."""

        # Route the response through same hybrid router
        route_decision = await self.topic_router.route(response)

        if route_decision.route == "block":
            return CheckResult(
                passed=False,
                check_name="topic_drift",
                details=f"Response drifted to blocked topic: {route_decision.matched_category}"
            )

        return CheckResult(passed=True, check_name="topic_drift")

    async def _check_harmful_content(self, response: str) -> CheckResult:
        """Check for harmful content in response."""
        harmful_patterns = [
            r"how to (make|create|build) (a )?(bomb|weapon|explosive)",
            r"step[s]? to (hack|break into|compromise)",
            r"(kill|harm|hurt) (yourself|themselves|someone)",
        ]

        import re
        for pattern in harmful_patterns:
            if re.search(pattern, response.lower()):
                return CheckResult(
                    passed=False,
                    check_name="harmful_content",
                    details=f"Harmful content pattern matched"
                )

        return CheckResult(passed=True, check_name="harmful_content")

    async def _check_competitor_mentions(self, response: str) -> CheckResult:
        """Check for unauthorized competitor mentions."""
        # This would be configured per-deployment
        competitors = []  # e.g., ["CompetitorA", "CompetitorB"]

        response_lower = response.lower()
        for competitor in competitors:
            if competitor.lower() in response_lower:
                return CheckResult(
                    passed=False,
                    check_name="competitor_mention",
                    details=f"Competitor mentioned: {competitor}"
                )

        return CheckResult(passed=True, check_name="competitor_mention")

    def _generate_safe_response(self, failures: list[CheckResult]) -> str:
        """Generate a safe response when guardrail fails."""
        return (
            "I apologize, but I'm unable to provide that response. "
            "Please rephrase your request or ask something else."
        )

    def _load_forbidden_patterns(self) -> list[str]:
        """Load forbidden patterns from configuration."""
        return []
```

**Why this matters:** JARVIS currently focuses heavily on input validation. But an LLM can still generate problematic outputs even with clean inputs—hallucinations, prompt leaks, or topic drift. Output guardrails are the "internal alarms" in the security analogy.

---

### Phase 7.3: Hierarchical Topic Routing

```python
# agent/security/topic_hierarchy.py
"""
PHASE 7.3: Hierarchical Topic Routing
Defines explicit allowed/forbidden topic boundaries.
"""

from typing import Literal, Optional
from dataclasses import dataclass

@dataclass
class TopicRouteDecision:
    route: Literal["allow", "block", "escalate"]
    path: list[str]
    matched_rule: str

TOPIC_HIERARCHY = {
    "root": {
        "allowed": {
            "software_development": {
                "allowed": ["code_review", "debugging", "architecture", "testing"],
                "blocked": ["malware_creation", "exploit_development"],
                "escalate": ["production_deployment", "security_changes"],
            },
            "business_operations": {
                "allowed": ["scheduling", "documentation", "analysis"],
                "blocked": ["competitor_sabotage", "fraud"],
                "escalate": ["contracts", "financial_transactions"],
            },
            "communication": {
                "allowed": ["drafting_emails", "meeting_notes", "summaries"],
                "blocked": ["impersonation", "spam", "harassment"],
                "escalate": ["external_announcements", "legal_communications"],
            },
        },
        "blocked": {
            "illegal_activities": ["hacking", "fraud", "violence"],
            "harmful_content": ["self_harm", "hate_speech", "misinformation"],
            "data_theft": ["credential_harvesting", "exfiltration"],
        },
        "escalate": {
            "sensitive_operations": ["financial", "legal", "hr_related"],
        },
    }
}

class TopicRouter:
    """Navigate topic hierarchy to determine routing."""

    def __init__(self, hierarchy: dict = None):
        self.hierarchy = hierarchy or TOPIC_HIERARCHY
        self._blocked_topics = self._collect_topics("blocked")
        self._escalate_topics = self._collect_topics("escalate")

    def route(self, classified_topic: str) -> TopicRouteDecision:
        """Traverse hierarchy to find appropriate route."""
        path = self._find_topic_path(classified_topic)

        # Check path from most specific to root
        for node in reversed(path):
            if node in self._blocked_topics:
                return TopicRouteDecision(
                    route="block",
                    path=path,
                    matched_rule=f"blocked:{node}"
                )
            if node in self._escalate_topics:
                return TopicRouteDecision(
                    route="escalate",
                    path=path,
                    matched_rule=f"escalate:{node}"
                )

        return TopicRouteDecision(
            route="allow",
            path=path,
            matched_rule="default:allow"
        )

    def _find_topic_path(self, topic: str) -> list[str]:
        """Find the path to a topic in the hierarchy."""
        def search(node: dict, target: str, path: list) -> Optional[list]:
            for key, value in node.items():
                current_path = path + [key]
                if key == target:
                    return current_path
                if isinstance(value, dict):
                    result = search(value, target, current_path)
                    if result:
                        return result
                elif isinstance(value, list) and target in value:
                    return current_path + [target]
            return None

        result = search(self.hierarchy, topic, [])
        return result or [topic]

    def _collect_topics(self, route_type: str) -> set[str]:
        """Collect all topics of a given route type."""
        topics = set()

        def traverse(node: dict):
            for key, value in node.items():
                if key == route_type:
                    if isinstance(value, dict):
                        topics.update(value.keys())
                        for v in value.values():
                            if isinstance(v, list):
                                topics.update(v)
                    elif isinstance(value, list):
                        topics.update(value)
                elif isinstance(value, dict):
                    traverse(value)

        traverse(self.hierarchy)
        return topics
```

**Why this matters:** The current JARVIS approach has implicit topic boundaries. Explicit hierarchy makes it clear what's allowed where, supports easier auditing, and allows domain-specific customization.

---

## Architecture Comparison

### Current JARVIS Flow

```
User Input
    ↓
[Pattern Matching] ─────→ Block if matched
    ↓
[Semantic Analysis] ────→ Block if injection detected
    ↓
[LLM Processing] ───────→ Response
    ↓
[Audit Logging] ────────→ Record
    ↓
User Output
```

### Proposed Hybrid Architecture

```
User Input
    ↓
┌─────────────────────────────────────┐
│ HYBRID ROUTER (Parallel)            │
│ ┌───────────────┬─────────────────┐ │
│ │ Dense Vectors │ Sparse BM25     │ │
│ │ (Semantic)    │ (Term Match)    │ │
│ └───────┬───────┴────────┬────────┘ │
│         └────────┬───────┘          │
│          Weighted Score             │
└──────────────────┬──────────────────┘
                   ↓
┌──────────────────┴──────────────────┐
│ TOPIC HIERARCHY ROUTER              │
│ allow / block / escalate / redirect │
└──────────────────┬──────────────────┘
        ┌──────────┼──────────┐
        ↓          ↓          ↓
     [Block]   [Escalate]  [Allow]
        │          │          ↓
        │          │    ┌───────────────────┐
        │          │    │ LLM + Safe Prompt │
        │          │    └─────────┬─────────┘
        │          │              ↓
        │          │    ┌───────────────────┐
        │          │    │ OUTPUT GUARDRAILS │ ←── NEW!
        │          │    │ (Same hybrid      │
        │          │    │  router on output)│
        │          │    └─────────┬─────────┘
        │          │              ↓
        ↓          ↓         [Pass/Fail]
   Pre-written  Human           ↓
   Response     Approval    Response
        │          │            │
        └──────────┼────────────┘
                   ↓
           [Audit Logging]
                   ↓
             User Output
```

---

## Recommended Changes

### 1. Add BM25 to the Stack

**Current:** Regex patterns only
**Proposed:** Add `rank_bm25` for statistical term importance

```
# requirements.txt addition
rank-bm25>=0.2.2
```

**Why:** Regex catches exact patterns but misses variations. BM25 understands that "delete all customer records" and "remove every client entry" are similarly dangerous based on term frequency analysis, without needing exhaustive pattern lists.

### 2. Pre-compute Route Embeddings

**Current:** Classification happens at request time via LLM
**Proposed:** Pre-compute embeddings for known categories at startup

```python
# Startup: compute once, use many times
CATEGORY_EMBEDDINGS = {
    "code_review": embed("Review code, analyze functions, check quality..."),
    "malware": embed("Create virus, hack system, steal credentials..."),
    # ... cached vectors
}
```

**Why:** Pre-computing makes routing O(1) vector comparisons instead of O(n) LLM calls. The sources emphasize that Hybrid routers are "insanely fast" compared to LLM-based classification.

### 3. Symmetric Input/Output Guardrails

**Current:** Asymmetric (heavy input, light output)
**Proposed:** Same guardrail infrastructure for both directions

```python
# Reuse the same router
input_decision = await hybrid_router.route(user_input)
# ... LLM processing ...
output_decision = await hybrid_router.route(llm_response)
```

**Why:** If a topic is forbidden for users to ask about, it should also be forbidden for the LLM to discuss unsolicited. Jailbreak attacks often work by getting the LLM to volunteer information it wouldn't directly answer.

### 4. Confidence-Based Escalation

**Current:** Binary allow/block
**Proposed:** Confidence thresholds for routing

```python
if decision.confidence > 0.95:
    # High confidence → act immediately
    return handle_route(decision.route)
elif decision.confidence > 0.70:
    # Medium confidence → allow with monitoring
    return handle_route(decision.route, enhanced_logging=True)
else:
    # Low confidence → escalate to human or secondary classifier
    return escalate_to_llm_classifier(query)
```

**Why:** Edge cases (the 51% accuracy problem mentioned) often have low confidence. Instead of guessing, escalate ambiguous queries to a more expensive but accurate classifier (or human).

### 5. Domain-Specific Sparse Indexes

**Current:** Generic patterns
**Proposed:** Separate BM25 indexes per domain

```python
DOMAIN_INDEXES = {
    "financial": BM25Index(["transaction", "payment", "transfer", "invoice"...]),
    "code": BM25Index(["function", "class", "import", "execute"...]),
    "competitor": BM25Index(["Tesla", "OpenAI", "Google", "Microsoft"...]),
}
```

**Why:** The Tesla/BYD example shows domain-specific terms matter. A car company's chatbot needs term matching on competitor names, while a code assistant needs it on dangerous function names.

---

## Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| 1 | Output Guardrails | Medium | High - Closes major gap |
| 2 | Hybrid Router | Medium | High - Speed + accuracy |
| 3 | BM25 Integration | Low | Medium - Better term matching |
| 4 | Topic Hierarchy | Low | Medium - Clearer boundaries |
| 5 | Pre-computed Embeddings | Low | Medium - Performance boost |

---

## New Dependencies

```
# requirements.txt additions for Phase 7
rank-bm25>=0.2.2          # Sparse term matching (BM25)
numpy>=1.24.0             # Vector operations (likely already present)
```

---

## Integration Points

### With Existing Security Modules

| Existing Module | Integration |
|-----------------|-------------|
| `prompt_security.py` | Hybrid router replaces/augments pattern matching |
| `pii_detector.py` | Used by output guardrails |
| `audit_logger.py` | Logs all routing decisions |
| `financial_guardrails.py` | Called when route = "escalate" for financial topics |

### With Existing Flow

```python
# agent/jarvis_chat.py - Integration point

async def process_message(self, message: str) -> str:
    # Phase 7.1: Hybrid input routing
    input_decision = await self.hybrid_router.route(message)

    if input_decision.route == "block":
        return self._get_block_response(input_decision)

    if input_decision.route == "escalate":
        await self._request_approval(message, input_decision)
        return "This request requires approval..."

    # Existing LLM processing
    response = await self._process_with_llm(message)

    # Phase 7.2: Output guardrails (NEW)
    output_result = await self.output_guardrails.check(response, message)

    if not output_result.passed:
        return output_result.sanitized_response

    return response
```

---

## Summary

The Hybrid approach is **strongly complementary** to JARVIS's existing architecture. The key insights:

1. **Hybrid > Pure Semantic**: JARVIS's current semantic analysis is good, but adding BM25 sparse matching would catch the "Tesla vs BYD" edge cases where meaning is similar but terms matter.

2. **Output Guardrails are Critical**: This is the biggest gap. JARVIS validates inputs thoroughly but trusts LLM outputs too much. Adding symmetric output checking would be high-impact.

3. **Speed Matters**: Pre-computing embeddings and using vector similarity instead of LLM calls for routing makes the system viable at scale without latency spikes.

4. **Defense in Depth Confirmed**: The multi-layer approach (input → LLM prompting → output) aligns perfectly with JARVIS's phase-based hardening philosophy.

---

## References

- Hybrid Semantic Routing research (dense + sparse combination)
- BM25/Okapi algorithm for term frequency analysis
- JARVIS Hardening Guide Phases 1-6

---

**Next Steps:**
1. Review and approve this proposal
2. Add `rank-bm25` to requirements.txt
3. Implement Phase 7.1 (Hybrid Router)
4. Implement Phase 7.2 (Output Guardrails)
5. Update THE_JARVIS_BIBLE.md with Phase 7 documentation
