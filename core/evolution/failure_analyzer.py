"""
PHASE 7.5: Failure Analyzer

Analyzes why specialists failed by examining their task history
and identifying patterns.

Usage:
    from core.evolution import FailureAnalyzer

    analyzer = FailureAnalyzer()
    patterns = await analyzer.analyze(specialist)
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from .graveyard import FailureCategory, FailurePattern

if TYPE_CHECKING:
    from core.specialists import Specialist


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Task Result for Analysis
# ============================================================================


class TaskAnalysisResult:
    """Simplified task result for failure analysis."""

    def __init__(
        self,
        id: UUID,
        score: float,
        request: str,
        response: str,
        error: Optional[str] = None,
        execution_time_ms: int = 0,
        tools_used: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.score = score
        self.request = request
        self.response = response
        self.error = error
        self.execution_time_ms = execution_time_ms
        self.tools_used = tools_used or []
        self.metadata = metadata or {}


# ============================================================================
# Failure Analyzer
# ============================================================================


class FailureAnalyzer:
    """
    Analyze why specialists failed.

    Examines task history to identify patterns:
    - Prompt weaknesses
    - Tool misuse
    - Domain gaps
    - Consistency issues
    - Edge case failures
    - Complexity mismatches

    Usage:
        analyzer = FailureAnalyzer()
        patterns = await analyzer.analyze(specialist)
    """

    def __init__(
        self,
        low_score_threshold: float = 0.6,
        db_session: Optional[Any] = None,
    ):
        """
        Initialize the analyzer.

        Args:
            low_score_threshold: Score below which tasks are considered failures
            db_session: Database session for querying task history
        """
        self._low_score_threshold = low_score_threshold
        self._db_session = db_session

    # -------------------------------------------------------------------------
    # Main Analysis
    # -------------------------------------------------------------------------

    async def analyze(self, specialist: "Specialist") -> List[FailurePattern]:
        """
        Analyze a specialist's failures and identify patterns.

        Args:
            specialist: The specialist to analyze

        Returns:
            List of identified failure patterns
        """
        logger.info(f"Analyzing failures for {specialist.name}")

        # Get low-scoring tasks
        low_scores = await self._get_low_scoring_tasks(
            specialist.id,
            threshold=self._low_score_threshold,
        )

        if not low_scores:
            logger.info(f"No low-scoring tasks found for {specialist.name}")
            return []

        patterns: List[FailurePattern] = []

        # Run all pattern detectors
        detectors = [
            self._detect_tool_misuse,
            self._detect_consistency_issues,
            self._detect_complexity_mismatch,
            self._detect_edge_case_failures,
            self._detect_prompt_weakness,
            self._detect_domain_gap,
            self._detect_hallucination,
            self._detect_format_errors,
            self._detect_slow_response,
        ]

        for detector in detectors:
            pattern = detector(low_scores, specialist)
            if pattern:
                patterns.append(pattern)

        logger.info(
            f"Found {len(patterns)} failure patterns for {specialist.name}"
        )

        return patterns

    # -------------------------------------------------------------------------
    # Task Retrieval
    # -------------------------------------------------------------------------

    async def _get_low_scoring_tasks(
        self,
        specialist_id: UUID,
        threshold: float,
        limit: int = 50,
    ) -> List[TaskAnalysisResult]:
        """
        Get tasks with scores below threshold.

        Args:
            specialist_id: Specialist to query
            threshold: Score threshold
            limit: Maximum tasks to retrieve

        Returns:
            List of low-scoring tasks
        """
        # Try database first
        if self._db_session:
            try:
                return await self._query_db_tasks(specialist_id, threshold, limit)
            except Exception as e:
                logger.warning(f"Failed to query DB: {e}")

        # Fall back to in-memory/simulated
        return self._get_simulated_tasks(specialist_id, threshold)

    async def _query_db_tasks(
        self,
        specialist_id: UUID,
        threshold: float,
        limit: int,
    ) -> List[TaskAnalysisResult]:
        """Query database for low-scoring tasks."""
        from database.models import SpecialistTaskLog
        from sqlalchemy import select

        stmt = (
            select(SpecialistTaskLog)
            .where(SpecialistTaskLog.specialist_id == specialist_id)
            .where(SpecialistTaskLog.score < threshold)
            .order_by(SpecialistTaskLog.created_at.desc())
            .limit(limit)
        )

        result = await self._db_session.execute(stmt)
        rows = result.scalars().all()

        return [
            TaskAnalysisResult(
                id=row.task_id,
                score=row.score,
                request=row.request or "",
                response=row.response or "",
                error=row.error,
                execution_time_ms=row.execution_time_ms or 0,
                metadata=row.metadata or {},
            )
            for row in rows
        ]

    def _get_simulated_tasks(
        self,
        specialist_id: UUID,
        threshold: float,
    ) -> List[TaskAnalysisResult]:
        """
        Return simulated tasks for testing.

        In production, this would not be used.
        """
        from uuid import uuid4

        # Return empty list - real implementation uses DB
        return []

    # -------------------------------------------------------------------------
    # Pattern Detectors
    # -------------------------------------------------------------------------

    def _detect_tool_misuse(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect if specialist frequently misuses tools."""
        tool_errors = []

        for task in tasks:
            # Check for tool-related errors
            if self._has_tool_error(task):
                tool_errors.append(task)

        if len(tool_errors) >= 2:
            return FailurePattern(
                category=FailureCategory.TOOL_MISUSE,
                description="Frequently selected wrong tools or used them incorrectly",
                frequency=len(tool_errors),
                example_tasks=[t.id for t in tool_errors[:3]],
                suggested_fix="Add clearer tool selection guidance and examples to system prompt",
                severity=0.7,
            )

        return None

    def _detect_consistency_issues(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect inconsistent performance."""
        perf = specialist.performance

        # High variance in scores suggests inconsistency
        if perf.worst_score < 0.3 and perf.best_score > 0.8:
            score_range = perf.best_score - perf.worst_score
            if score_range > 0.5:
                return FailurePattern(
                    category=FailureCategory.CONSISTENCY,
                    description=(
                        f"Highly variable performance "
                        f"(best: {perf.best_score:.2f}, worst: {perf.worst_score:.2f})"
                    ),
                    frequency=len(tasks),
                    example_tasks=[t.id for t in tasks[:3]],
                    suggested_fix="Add more specific instructions for different task types",
                    severity=0.6,
                )

        return None

    def _detect_complexity_mismatch(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect if specialist struggles with complex tasks."""
        complex_failures = []

        for task in tasks:
            # Heuristic: long requests often indicate complex tasks
            if len(task.request) > 500 and task.score < 0.5:
                complex_failures.append(task)

        if len(complex_failures) >= 2:
            return FailurePattern(
                category=FailureCategory.COMPLEXITY_MISMATCH,
                description="Struggles with complex multi-step tasks",
                frequency=len(complex_failures),
                example_tasks=[t.id for t in complex_failures[:3]],
                suggested_fix="Add step-by-step task breakdown instructions",
                severity=0.7,
            )

        return None

    def _detect_edge_case_failures(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect failures on edge cases."""
        edge_cases = []

        edge_keywords = [
            "empty", "null", "none", "zero", "negative",
            "special character", "unicode", "large", "maximum",
            "minimum", "boundary", "edge"
        ]

        for task in tasks:
            request_lower = task.request.lower()
            if any(kw in request_lower for kw in edge_keywords):
                edge_cases.append(task)

        if len(edge_cases) >= 2:
            return FailurePattern(
                category=FailureCategory.EDGE_CASES,
                description="Fails on unusual inputs or edge cases",
                frequency=len(edge_cases),
                example_tasks=[t.id for t in edge_cases[:3]],
                suggested_fix="Add explicit handling for edge cases: empty, null, boundaries",
                severity=0.6,
            )

        return None

    def _detect_prompt_weakness(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect if failures indicate prompt weakness."""
        # Look for responses that suggest confusion about instructions
        confused_responses = []

        confusion_indicators = [
            "i'm not sure",
            "unclear what",
            "could you clarify",
            "i don't understand",
            "what do you mean",
        ]

        for task in tasks:
            response_lower = task.response.lower()
            if any(ind in response_lower for ind in confusion_indicators):
                confused_responses.append(task)

        if len(confused_responses) >= 2:
            return FailurePattern(
                category=FailureCategory.PROMPT_WEAKNESS,
                description="System prompt missing clarity or specific instructions",
                frequency=len(confused_responses),
                example_tasks=[t.id for t in confused_responses[:3]],
                suggested_fix="Make system prompt more specific with clear examples",
                severity=0.8,
            )

        return None

    def _detect_domain_gap(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect missing domain knowledge."""
        # Look for tasks where response shows lack of domain knowledge
        knowledge_gaps = []

        gap_indicators = [
            "i don't have information about",
            "outside my knowledge",
            "i cannot access",
            "i'm not familiar with",
        ]

        for task in tasks:
            response_lower = task.response.lower()
            if any(ind in response_lower for ind in gap_indicators):
                knowledge_gaps.append(task)

        if len(knowledge_gaps) >= 2:
            return FailurePattern(
                category=FailureCategory.DOMAIN_GAP,
                description=f"Missing specific knowledge for {specialist.domain} domain",
                frequency=len(knowledge_gaps),
                example_tasks=[t.id for t in knowledge_gaps[:3]],
                suggested_fix=f"Add more {specialist.domain}-specific context to system prompt",
                severity=0.7,
            )

        return None

    def _detect_hallucination(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect hallucination patterns."""
        hallucinations = []

        # Check metadata for hallucination flags
        for task in tasks:
            if task.metadata.get("hallucination_detected"):
                hallucinations.append(task)
            elif task.error and "hallucination" in task.error.lower():
                hallucinations.append(task)

        if len(hallucinations) >= 2:
            return FailurePattern(
                category=FailureCategory.HALLUCINATION,
                description="Generates false or unsupported information",
                frequency=len(hallucinations),
                example_tasks=[t.id for t in hallucinations[:3]],
                suggested_fix="Add instruction to cite sources and verify facts",
                severity=0.9,
            )

        return None

    def _detect_format_errors(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect output formatting issues."""
        format_errors = []

        for task in tasks:
            if task.metadata.get("format_error"):
                format_errors.append(task)
            elif task.error and "format" in task.error.lower():
                format_errors.append(task)

        if len(format_errors) >= 2:
            return FailurePattern(
                category=FailureCategory.FORMAT_ERRORS,
                description="Output does not match expected format",
                frequency=len(format_errors),
                example_tasks=[t.id for t in format_errors[:3]],
                suggested_fix="Add explicit output format examples to system prompt",
                severity=0.5,
            )

        return None

    def _detect_slow_response(
        self,
        tasks: List[TaskAnalysisResult],
        specialist: "Specialist",
    ) -> Optional[FailurePattern]:
        """Detect consistently slow responses."""
        slow_tasks = []

        # Consider > 30 seconds as slow
        slow_threshold_ms = 30000

        for task in tasks:
            if task.execution_time_ms > slow_threshold_ms:
                slow_tasks.append(task)

        if len(slow_tasks) >= 3:
            avg_time = sum(t.execution_time_ms for t in slow_tasks) / len(slow_tasks)
            return FailurePattern(
                category=FailureCategory.SLOW_RESPONSE,
                description=f"Consistently slow responses (avg: {avg_time/1000:.1f}s)",
                frequency=len(slow_tasks),
                example_tasks=[t.id for t in slow_tasks[:3]],
                suggested_fix="Optimize prompt for conciseness, avoid verbose instructions",
                severity=0.4,
            )

        return None

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _has_tool_error(self, task: TaskAnalysisResult) -> bool:
        """Check if task has tool-related error."""
        tool_error_patterns = [
            r"tool.*failed",
            r"invalid.*tool",
            r"wrong.*tool",
            r"tool.*not.*found",
            r"unable.*execute",
        ]

        if task.error:
            for pattern in tool_error_patterns:
                if re.search(pattern, task.error, re.IGNORECASE):
                    return True

        return False
