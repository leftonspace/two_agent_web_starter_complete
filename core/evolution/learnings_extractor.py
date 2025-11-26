"""
PHASE 7.5: Learnings Extractor

Extracts actionable learnings from failure patterns.
These learnings are injected into new specialists to prevent
repeating the same mistakes.

Usage:
    from core.evolution import LearningsExtractor

    extractor = LearningsExtractor()
    learnings = extractor.extract(failure_patterns)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .graveyard import FailureCategory, FailurePattern, Learning


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Learning Templates
# ============================================================================


# Templates for generating learnings from patterns
LEARNING_TEMPLATES: Dict[FailureCategory, Dict[str, str]] = {
    FailureCategory.TOOL_MISUSE: {
        "type": "avoidance",
        "template": (
            "TOOL SELECTION: Before executing any tool, verify it matches the task. "
            "Previous failures occurred from: {description}. "
            "Always confirm tool capabilities match requirements."
        ),
        "confidence": 0.8,
    },
    FailureCategory.PROMPT_WEAKNESS: {
        "type": "enhancement",
        "template": (
            "CLARITY: Be explicit about your approach before executing. "
            "Ask clarifying questions if requirements are ambiguous. "
            "Previous failures: {description}"
        ),
        "confidence": 0.75,
    },
    FailureCategory.DOMAIN_GAP: {
        "type": "enhancement",
        "template": (
            "DOMAIN KNOWLEDGE: When uncertain about domain-specific details, "
            "acknowledge limitations and suggest verification. "
            "Gap identified: {description}"
        ),
        "confidence": 0.7,
    },
    FailureCategory.CONSISTENCY: {
        "type": "technique",
        "template": (
            "CONSISTENT APPROACH: Apply the same rigor to all tasks regardless of "
            "perceived difficulty. Use checklists for quality. "
            "Pattern observed: {description}"
        ),
        "confidence": 0.7,
    },
    FailureCategory.EDGE_CASES: {
        "type": "enhancement",
        "template": (
            "EDGE CASES: Always consider boundary conditions - empty inputs, "
            "null values, very large inputs, special characters. "
            "Previous failures on: {description}"
        ),
        "confidence": 0.75,
    },
    FailureCategory.COMPLEXITY_MISMATCH: {
        "type": "technique",
        "template": (
            "COMPLEX TASKS: Break down multi-step tasks into smaller pieces. "
            "Execute incrementally and verify each step. "
            "Struggled with: {description}"
        ),
        "confidence": 0.8,
    },
    FailureCategory.SLOW_RESPONSE: {
        "type": "avoidance",
        "template": (
            "EFFICIENCY: Be concise in responses. Avoid unnecessary elaboration. "
            "Previous issue: {description}"
        ),
        "confidence": 0.6,
    },
    FailureCategory.HALLUCINATION: {
        "type": "avoidance",
        "template": (
            "ACCURACY: Only state facts you are certain about. "
            "When uncertain, say so explicitly. Never fabricate information. "
            "Previous issue: {description}"
        ),
        "confidence": 0.9,
    },
    FailureCategory.FORMAT_ERRORS: {
        "type": "technique",
        "template": (
            "OUTPUT FORMAT: Pay close attention to expected output format. "
            "Validate structure before responding. "
            "Previous issues: {description}"
        ),
        "confidence": 0.7,
    },
    FailureCategory.UNKNOWN: {
        "type": "enhancement",
        "template": (
            "GENERAL IMPROVEMENT: Apply careful analysis to all tasks. "
            "Note: {description}"
        ),
        "confidence": 0.5,
    },
}


# ============================================================================
# Learnings Extractor
# ============================================================================


class LearningsExtractor:
    """
    Extract actionable learnings from failure patterns.

    Transforms failure patterns into instructions that can be
    injected into new specialists' system prompts.

    Usage:
        extractor = LearningsExtractor()
        learnings = extractor.extract(patterns)

        for learning in learnings:
            print(f"[{learning.type}] {learning.instruction}")
    """

    def __init__(
        self,
        min_frequency: int = 1,
        min_severity: float = 0.3,
        custom_templates: Optional[Dict[FailureCategory, Dict[str, str]]] = None,
    ):
        """
        Initialize the extractor.

        Args:
            min_frequency: Minimum pattern frequency to generate learning
            min_severity: Minimum pattern severity to generate learning
            custom_templates: Override default learning templates
        """
        self._min_frequency = min_frequency
        self._min_severity = min_severity
        self._templates = {**LEARNING_TEMPLATES, **(custom_templates or {})}

    # -------------------------------------------------------------------------
    # Main Extraction
    # -------------------------------------------------------------------------

    def extract(self, patterns: List[FailurePattern]) -> List[Learning]:
        """
        Extract learnings from failure patterns.

        Args:
            patterns: List of identified failure patterns

        Returns:
            List of actionable learnings
        """
        if not patterns:
            return []

        learnings: List[Learning] = []

        for pattern in patterns:
            # Skip low-frequency or low-severity patterns
            if pattern.frequency < self._min_frequency:
                continue
            if pattern.severity < self._min_severity:
                continue

            learning = self._create_learning(pattern)
            if learning:
                learnings.append(learning)

        # Sort by confidence (highest first)
        learnings.sort(key=lambda l: l.confidence, reverse=True)

        logger.info(f"Extracted {len(learnings)} learnings from {len(patterns)} patterns")

        return learnings

    def _create_learning(self, pattern: FailurePattern) -> Optional[Learning]:
        """Create a learning from a single pattern."""
        template_info = self._templates.get(pattern.category)

        if not template_info:
            # Use unknown template as fallback
            template_info = self._templates[FailureCategory.UNKNOWN]

        # Generate instruction from template
        instruction = template_info["template"].format(
            description=pattern.description,
            frequency=pattern.frequency,
            suggested_fix=pattern.suggested_fix,
        )

        # Adjust confidence based on pattern severity and frequency
        base_confidence = float(template_info["confidence"])
        confidence = self._calculate_confidence(
            base_confidence,
            pattern.severity,
            pattern.frequency,
        )

        return Learning(
            type=template_info["type"],  # type: ignore
            instruction=instruction,
            source_patterns=[pattern.description],
            confidence=confidence,
        )

    def _calculate_confidence(
        self,
        base_confidence: float,
        severity: float,
        frequency: int,
    ) -> float:
        """
        Calculate learning confidence based on pattern attributes.

        Higher severity and frequency = higher confidence.
        """
        # Frequency bonus (up to 0.1)
        freq_bonus = min(0.1, frequency * 0.02)

        # Severity multiplier
        severity_mult = 0.8 + (severity * 0.4)  # 0.8 to 1.2

        confidence = (base_confidence + freq_bonus) * severity_mult

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    # -------------------------------------------------------------------------
    # Advanced Extraction
    # -------------------------------------------------------------------------

    def extract_combined(self, patterns: List[FailurePattern]) -> List[Learning]:
        """
        Extract learnings and combine related patterns.

        Groups similar patterns before extraction for more
        comprehensive learnings.

        Args:
            patterns: List of failure patterns

        Returns:
            List of combined learnings
        """
        if not patterns:
            return []

        # Group patterns by category
        by_category: Dict[FailureCategory, List[FailurePattern]] = {}
        for pattern in patterns:
            if pattern.category not in by_category:
                by_category[pattern.category] = []
            by_category[pattern.category].append(pattern)

        learnings: List[Learning] = []

        for category, category_patterns in by_category.items():
            # Combine patterns of same category
            combined = self._combine_patterns(category_patterns)
            learning = self._create_learning(combined)
            if learning:
                learnings.append(learning)

        learnings.sort(key=lambda l: l.confidence, reverse=True)
        return learnings

    def _combine_patterns(self, patterns: List[FailurePattern]) -> FailurePattern:
        """Combine multiple patterns of same category into one."""
        if len(patterns) == 1:
            return patterns[0]

        # Combine descriptions
        descriptions = [p.description for p in patterns]
        combined_desc = "; ".join(descriptions)

        # Sum frequencies
        total_freq = sum(p.frequency for p in patterns)

        # Max severity
        max_severity = max(p.severity for p in patterns)

        # Collect example tasks
        all_examples = []
        for p in patterns:
            all_examples.extend(p.example_tasks)

        # Use first pattern's category and suggested fix
        return FailurePattern(
            category=patterns[0].category,
            description=combined_desc,
            frequency=total_freq,
            example_tasks=all_examples[:5],
            suggested_fix=patterns[0].suggested_fix,
            severity=max_severity,
        )

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def prioritize(
        self,
        learnings: List[Learning],
        limit: int = 5,
    ) -> List[Learning]:
        """
        Prioritize learnings to avoid overwhelming new specialists.

        Args:
            learnings: List of learnings
            limit: Maximum learnings to return

        Returns:
            Top N most important learnings
        """
        # Already sorted by confidence, but ensure variety
        # by selecting at most 2 per type
        type_counts: Dict[str, int] = {}
        prioritized: List[Learning] = []

        for learning in learnings:
            type_count = type_counts.get(learning.type, 0)
            if type_count < 2:
                prioritized.append(learning)
                type_counts[learning.type] = type_count + 1

            if len(prioritized) >= limit:
                break

        return prioritized

    def format_for_prompt(self, learnings: List[Learning]) -> str:
        """
        Format learnings for injection into system prompt.

        Args:
            learnings: List of learnings to format

        Returns:
            Formatted string for system prompt
        """
        if not learnings:
            return ""

        sections = {
            "avoidance": [],
            "enhancement": [],
            "technique": [],
        }

        for learning in learnings:
            sections[learning.type].append(learning.instruction)

        parts = []

        if sections["avoidance"]:
            parts.append("## Things to AVOID (from previous failures)")
            for instruction in sections["avoidance"]:
                parts.append(f"- {instruction}")
            parts.append("")

        if sections["enhancement"]:
            parts.append("## Required Behaviors (learned best practices)")
            for instruction in sections["enhancement"]:
                parts.append(f"- {instruction}")
            parts.append("")

        if sections["technique"]:
            parts.append("## Proven Techniques")
            for instruction in sections["technique"]:
                parts.append(f"- {instruction}")
            parts.append("")

        return "\n".join(parts)
