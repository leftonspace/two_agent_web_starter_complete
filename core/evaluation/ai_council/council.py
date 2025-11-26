"""
PHASE 7.5: AI Council

Experimental evaluator using specialist voting.
Specialists vote on each other's work with structured feedback.

Process:
1. Get voters (domain specialists + JARVIS)
2. Each voter evaluates the task result
3. Remove outliers (> 2 std from mean)
4. Aggregate with JARVIS weighted 1.5x
5. Detect bootstrap bias in young generations

Usage:
    from core.evaluation.ai_council import AICouncil

    council = AICouncil()
    result = await council.evaluate(task_result)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from ..base import (
    BaseEvaluator,
    EvaluationResult,
    EvaluationStatus,
    EvaluatorType,
    TaskResult,
)
from .voter import (
    Vote,
    VoteParseError,
    VOTING_INSTRUCTIONS,
    JARVIS_VOTING_ADDENDUM,
    parse_vote_response,
)
from .aggregator import (
    VoteAggregator,
    AggregationResult,
    NoVotesError,
)


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


class AICouncilConfig:
    """Configuration for the AI Council."""

    def __init__(
        self,
        jarvis_weight: float = 1.5,
        specialist_weight: float = 1.0,
        min_voters: int = 2,
        max_voters: int = 5,
        remove_outliers: bool = True,
        outlier_threshold_std: float = 2.0,
        max_discussion_rounds: int = 3,
        consensus_threshold: float = 0.15,
        max_tokens_per_vote: int = 500,
        timeout_seconds: int = 30,
        council_model: Optional[str] = None,
    ):
        self.jarvis_weight = jarvis_weight
        self.specialist_weight = specialist_weight
        self.min_voters = min_voters
        self.max_voters = max_voters
        self.remove_outliers = remove_outliers
        self.outlier_threshold_std = outlier_threshold_std
        self.max_discussion_rounds = max_discussion_rounds
        self.consensus_threshold = consensus_threshold
        self.max_tokens_per_vote = max_tokens_per_vote
        self.timeout_seconds = timeout_seconds
        self.council_model = council_model

    @classmethod
    def load(cls, path: str = "config/evaluation/config.yaml") -> "AICouncilConfig":
        """Load configuration from YAML file."""
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            ac_config = data.get("ai_council", {})
            return cls(
                jarvis_weight=ac_config.get("jarvis_weight", 1.5),
                specialist_weight=ac_config.get("specialist_weight", 1.0),
                min_voters=ac_config.get("min_voters", 2),
                max_voters=ac_config.get("max_voters", 5),
                remove_outliers=ac_config.get("remove_outliers", True),
                outlier_threshold_std=ac_config.get("outlier_threshold_std", 2.0),
                max_discussion_rounds=ac_config.get("max_discussion_rounds", 3),
                consensus_threshold=ac_config.get("consensus_threshold", 0.15),
                max_tokens_per_vote=ac_config.get("max_tokens_per_vote", 500),
                timeout_seconds=ac_config.get("timeout_seconds", 30),
                council_model=ac_config.get("council_model"),
            )
        except Exception as e:
            logger.warning(f"Failed to load AI Council config: {e}, using defaults")
            return cls()


# ============================================================================
# AI Council
# ============================================================================


class AICouncil(BaseEvaluator):
    """
    Experimental evaluator using specialist voting.

    Voters:
    - Top specialists from the task's domain
    - JARVIS (best admin specialist, weighted 1.5x)

    Process:
    1. Present task result to each voter
    2. Each provides score (0-1) and reasoning
    3. Remove outliers (> 2 std from mean)
    4. Aggregate remaining votes (JARVIS 1.5x weight)
    5. Detect bootstrap bias in young generations

    Bootstrap Protection:
    - If generation < 3 AND variance < 0.05 AND mean > 0.9
    - Flag as "low_confidence"
    - Scores should be verified manually

    Usage:
        council = AICouncil()
        result = await council.evaluate(task_result)
    """

    def __init__(
        self,
        config: Optional[AICouncilConfig] = None,
        pool_manager: Optional[Any] = None,
        model_router: Optional[Any] = None,
    ):
        """
        Initialize the AI Council.

        Args:
            config: Council configuration
            pool_manager: Pool manager for getting specialists
            model_router: Router for LLM calls
        """
        self._council_config = config or AICouncilConfig.load()

        super().__init__({
            "jarvis_weight": self._council_config.jarvis_weight,
            "outlier_threshold": self._council_config.outlier_threshold_std,
        })

        self._pool_manager = pool_manager
        self._model_router = model_router

        # Initialize aggregator
        self._aggregator = VoteAggregator(
            jarvis_weight=self._council_config.jarvis_weight,
            specialist_weight=self._council_config.specialist_weight,
            outlier_threshold_std=self._council_config.outlier_threshold_std,
        )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def pool_manager(self) -> Any:
        """Get pool manager (lazy load if needed)."""
        if self._pool_manager is None:
            from core.specialists import get_pool_manager
            self._pool_manager = get_pool_manager()
        return self._pool_manager

    @property
    def model_router(self) -> Any:
        """Get model router (lazy load if needed)."""
        if self._model_router is None:
            try:
                from core.models import get_model_router
                self._model_router = get_model_router()
            except ImportError:
                logger.warning("Model router not available")
        return self._model_router

    @property
    def aggregator(self) -> VoteAggregator:
        """Get the vote aggregator."""
        return self._aggregator

    # -------------------------------------------------------------------------
    # BaseEvaluator Implementation
    # -------------------------------------------------------------------------

    def get_type(self) -> EvaluatorType:
        """Get evaluator type."""
        return EvaluatorType.AI_COUNCIL

    async def evaluate(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Evaluate a task result using the AI Council.

        Args:
            result: Task result to evaluate
            context: Additional context

        Returns:
            EvaluationResult with consensus score
        """
        start_time = time.time()
        self._increment_count()

        try:
            # Get voters
            voters = await self._get_voters(result.domain)

            if len(voters) < self._council_config.min_voters:
                logger.warning(
                    f"Not enough voters ({len(voters)}) for AI Council "
                    f"(min: {self._council_config.min_voters})"
                )
                return self._create_insufficient_voters_result(result, len(voters))

            # Collect votes
            votes = await self._collect_votes(voters, result)

            if not votes:
                return self._create_no_votes_result(result)

            # Remove outliers
            if self._council_config.remove_outliers:
                votes = self._aggregator.remove_outliers(votes)

            # Aggregate votes
            aggregation = self._aggregator.aggregate(votes)

            # Check for bootstrap bias
            domain_pool = self.pool_manager.get_pool(result.domain)
            bootstrap_warning = self._detect_bootstrap_bias(
                votes=votes,
                generation=domain_pool.generation,
            )

            # Adjust confidence for bootstrap warning
            confidence = aggregation.confidence
            if bootstrap_warning:
                confidence = min(confidence, 0.3)

            duration_ms = int((time.time() - start_time) * 1000)

            return EvaluationResult(
                task_id=result.task_id,
                specialist_id=result.specialist_id,
                score=aggregation.final_score,
                components={
                    "votes": [v.score for v in votes if not v.is_outlier],
                    "vote_count": aggregation.included_votes,
                },
                confidence=confidence,
                evaluator_type=EvaluatorType.AI_COUNCIL,
                status=EvaluationStatus.COMPLETED,
                requires_human_feedback=bootstrap_warning,
                human_feedback_reason="Bootstrap bias detected - verify manually" if bootstrap_warning else None,
                evaluation_duration_ms=duration_ms,
                metadata={
                    "votes": [v.to_dict() for v in votes],
                    "aggregation": aggregation.to_summary(),
                    "total_voters": len(voters),
                    "filtered_count": aggregation.included_votes,
                    "outliers_removed": aggregation.excluded_outliers,
                    "bootstrap_warning": bootstrap_warning,
                    "generation": domain_pool.generation,
                },
            )

        except Exception as e:
            logger.error(f"AI Council evaluation failed: {e}")
            return self._create_error_result(result, str(e))

    # -------------------------------------------------------------------------
    # Voting Methods
    # -------------------------------------------------------------------------

    async def _get_voters(self, domain: str) -> List[Any]:
        """Get voters for evaluation."""
        voters = []

        # Get domain specialists
        domain_pool = self.pool_manager.get_pool(domain)
        for specialist in domain_pool.specialists[:self._council_config.max_voters - 1]:
            if specialist.is_eligible_for_tasks():
                voters.append(specialist)

        # Add JARVIS as voter
        jarvis = self.pool_manager.get_jarvis()
        if jarvis and jarvis not in voters:
            voters.append(jarvis)

        return voters

    async def _collect_votes(
        self,
        voters: List[Any],
        result: TaskResult,
    ) -> List[Vote]:
        """Collect votes from all voters."""
        votes = []

        for voter in voters:
            try:
                vote = await self._get_vote(voter, result)
                if vote:
                    votes.append(vote)
            except Exception as e:
                logger.warning(f"Failed to get vote from {voter.name}: {e}")

        return votes

    async def _get_vote(
        self,
        voter: Any,
        result: TaskResult,
    ) -> Optional[Vote]:
        """
        Ask a specialist to vote on a result.

        Args:
            voter: Specialist to vote
            result: Task result to evaluate

        Returns:
            Vote from the specialist
        """
        # Determine voter type
        is_jarvis = self.pool_manager.is_jarvis(voter)
        voter_type = "jarvis" if is_jarvis else "specialist"

        # Build voting prompt
        prompt = self._build_voting_prompt(result, is_jarvis)

        # Build system prompt
        system_prompt = voter.config.system_prompt
        if is_jarvis:
            system_prompt += JARVIS_VOTING_ADDENDUM

        try:
            start_time = time.time()

            # Use model router if available, otherwise simulate
            if self.model_router:
                response = await self._call_model(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    voter=voter,
                )
            else:
                # Simulation mode - generate reasonable vote
                response = self._simulate_vote(result, voter)

            voting_time_ms = int((time.time() - start_time) * 1000)

            # Parse vote
            vote = parse_vote_response(
                response=response,
                task_id=result.task_id,
                voter_id=voter.id,
                voter_name=voter.name,
                voter_type=voter_type,
            )
            vote.voting_time_ms = voting_time_ms

            logger.debug(
                f"Vote from {voter.name}: score={vote.score:.2f}, "
                f"type={voter_type}"
            )

            return vote

        except VoteParseError as e:
            logger.warning(f"Failed to parse vote from {voter.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting vote from {voter.name}: {e}")
            return None

    def _build_voting_prompt(
        self,
        result: TaskResult,
        is_jarvis: bool = False,
    ) -> str:
        """Build the voting prompt for a specialist."""
        artifacts_str = ", ".join(result.artifacts) if result.artifacts else "None"

        prompt = VOTING_INSTRUCTIONS.format(
            request=result.request,
            response=result.response[:2000],  # Truncate long responses
            artifacts=artifacts_str,
        )

        return prompt

    async def _call_model(
        self,
        prompt: str,
        system_prompt: str,
        voter: Any,
    ) -> str:
        """Call the model to get a vote."""
        # This would use the model router in production
        # For now, we'll use a simple implementation
        if hasattr(self.model_router, "route_and_execute"):
            return await self.model_router.route_and_execute(
                request=prompt,
                domain="evaluation",
                system_prompt=system_prompt,
            )
        raise NotImplementedError("Model router not properly configured")

    def _simulate_vote(self, result: TaskResult, voter: Any) -> str:
        """
        Simulate a vote for testing when model router unavailable.

        In production, this would not be used.
        """
        import random

        # Generate somewhat realistic score based on response length
        base_score = 0.7 + random.uniform(-0.1, 0.2)

        # Adjust based on response characteristics
        if len(result.response) > 100:
            base_score += 0.05
        if result.artifacts:
            base_score += 0.05

        base_score = max(0.0, min(1.0, base_score))

        return json.dumps({
            "correctness": int(base_score * 10),
            "completeness": int(base_score * 9),
            "quality": int(base_score * 10),
            "best_practices": int(base_score * 9),
            "score": round(base_score, 2),
            "reasoning": "Simulated vote for testing",
            "strengths": ["Response addresses the request"],
            "weaknesses": ["Simulated - no real analysis"],
        })

    # -------------------------------------------------------------------------
    # Bootstrap Bias Detection
    # -------------------------------------------------------------------------

    def _detect_bootstrap_bias(
        self,
        votes: List[Vote],
        generation: int,
    ) -> bool:
        """
        Detect if votes might be biased due to bootstrap.

        In early generations, specialists haven't been properly calibrated
        and may give unrealistically high scores.

        Warning triggered if:
        - Generation < 3
        - Variance < 0.05 (all scores very similar)
        - Mean score > 0.9 (suspiciously high)

        Args:
            votes: List of votes
            generation: Pool generation number

        Returns:
            True if bootstrap bias suspected
        """
        # Generation 3+ is considered calibrated
        if generation >= 3:
            return False

        # Need enough votes to detect
        non_outlier_votes = [v for v in votes if not v.is_outlier]
        if len(non_outlier_votes) < 2:
            return False

        scores = [v.score for v in non_outlier_votes]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Suspicious: low variance + high scores in young generation
        if variance < 0.05 and mean_score > 0.9:
            logger.warning(
                f"Bootstrap bias detected: gen={generation}, "
                f"mean={mean_score:.2f}, variance={variance:.4f}"
            )
            return True

        return False

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------

    def _create_insufficient_voters_result(
        self,
        result: TaskResult,
        voter_count: int,
    ) -> EvaluationResult:
        """Create result when not enough voters available."""
        return EvaluationResult(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            score=0.5,
            confidence=0.1,
            evaluator_type=EvaluatorType.AI_COUNCIL,
            status=EvaluationStatus.FAILED,
            requires_human_feedback=True,
            human_feedback_reason=f"Insufficient voters ({voter_count})",
            error=f"Need at least {self._council_config.min_voters} voters",
        )

    def _create_no_votes_result(self, result: TaskResult) -> EvaluationResult:
        """Create result when no votes collected."""
        return EvaluationResult(
            task_id=result.task_id,
            specialist_id=result.specialist_id,
            score=0.5,
            confidence=0.0,
            evaluator_type=EvaluatorType.AI_COUNCIL,
            status=EvaluationStatus.FAILED,
            requires_human_feedback=True,
            human_feedback_reason="No valid votes collected",
            error="Failed to collect any valid votes",
        )


# ============================================================================
# Factory Function
# ============================================================================


def create_ai_council(
    config_path: str = "config/evaluation/config.yaml",
) -> AICouncil:
    """Create a configured AICouncil instance."""
    config = AICouncilConfig.load(config_path)
    return AICouncil(config=config)
