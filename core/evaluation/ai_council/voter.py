"""
PHASE 7.5: AI Council Voter

Vote model and voting instructions for AI Council evaluation.
Specialists vote on each other's work with structured feedback.

Usage:
    from core.evaluation.ai_council import Vote, VOTING_INSTRUCTIONS

    vote = Vote(
        voter_id=specialist.id,
        voter_type="specialist",
        score=0.85,
        reasoning="Well-structured code with good error handling",
        strengths=["Clear structure", "Good comments"],
        weaknesses=["Could use more tests"],
    )
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Voting Instructions Template
# ============================================================================


VOTING_INSTRUCTIONS = """
You are evaluating another specialist's work. Be objective and thorough.

=== TASK BEING EVALUATED ===

Request: {request}

Response:
{response}

Artifacts Created: {artifacts}

=== EVALUATION CRITERIA ===

Score the work on these criteria (1-10 each, then average for final 0-1 score):

1. **Correctness** (Does it correctly address the request?)
   - Addresses all requirements
   - No logical errors
   - Output is accurate

2. **Completeness** (Is anything missing?)
   - All aspects covered
   - Edge cases handled
   - No obvious gaps

3. **Quality** (Is the output high quality?)
   - Well-structured
   - Clear and readable
   - Professional presentation

4. **Best Practices** (Does it follow best practices?)
   - Follows conventions
   - Maintainable
   - Efficient approach

=== OUTPUT FORMAT ===

Respond with ONLY a JSON object (no markdown, no explanation outside JSON):

{{
    "correctness": 8,
    "completeness": 7,
    "quality": 9,
    "best_practices": 8,
    "score": 0.80,
    "reasoning": "Brief 1-2 sentence overall assessment",
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"]
}}

IMPORTANT:
- Be honest and objective
- Don't inflate scores to be nice
- Don't penalize for things outside the request
- Score is 0.0 to 1.0 (average of criteria / 10)
"""


JARVIS_VOTING_ADDENDUM = """

As JARVIS, you have additional perspective:
- Consider user experience and communication clarity
- Weight practicality and usefulness highly
- Your vote carries 1.5x weight, so be thoughtful
"""


# ============================================================================
# Vote Model
# ============================================================================


class VoteCriteria(BaseModel):
    """Individual criteria scores."""
    correctness: int = Field(ge=1, le=10, description="Score 1-10")
    completeness: int = Field(ge=1, le=10, description="Score 1-10")
    quality: int = Field(ge=1, le=10, description="Score 1-10")
    best_practices: int = Field(ge=1, le=10, description="Score 1-10")

    @property
    def average(self) -> float:
        """Calculate average score (0-1)."""
        total = self.correctness + self.completeness + self.quality + self.best_practices
        return total / 40.0  # 4 criteria * 10 max = 40


class Vote(BaseModel):
    """
    A vote from a specialist on another's work.

    Includes score, reasoning, and specific strengths/weaknesses.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    voter_id: UUID
    voter_name: Optional[str] = None
    voter_type: Literal["specialist", "jarvis"] = "specialist"

    # Score
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall score (0-1)",
    )

    # Criteria breakdown (optional)
    criteria: Optional[VoteCriteria] = None

    # Reasoning
    reasoning: str = Field(
        default="",
        max_length=500,
        description="Brief explanation of the score",
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="List of strengths identified",
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="List of weaknesses identified",
    )

    # Metadata
    model_used: Optional[str] = None
    tokens_used: int = 0
    voting_time_ms: int = 0

    # Status
    is_outlier: bool = Field(
        default=False,
        description="Whether this vote was flagged as outlier",
    )
    outlier_reason: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def weight(self) -> float:
        """Get vote weight (JARVIS = 1.5x, others = 1.0x)."""
        return 1.5 if self.voter_type == "jarvis" else 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "task_id": str(self.task_id),
            "voter_id": str(self.voter_id),
            "voter_name": self.voter_name,
            "voter_type": self.voter_type,
            "score": self.score,
            "weight": self.weight,
            "reasoning": self.reasoning,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "is_outlier": self.is_outlier,
            "created_at": self.created_at.isoformat(),
        }

    def to_summary(self) -> Dict[str, Any]:
        """Get a brief summary of the vote."""
        return {
            "voter": self.voter_name or str(self.voter_id)[:8],
            "type": self.voter_type,
            "score": round(self.score, 2),
            "weight": self.weight,
            "outlier": self.is_outlier,
        }


# ============================================================================
# Vote Parsing
# ============================================================================


class VoteParseError(Exception):
    """Error parsing vote from model response."""
    pass


def parse_vote_response(
    response: str,
    task_id: UUID,
    voter_id: UUID,
    voter_name: Optional[str] = None,
    voter_type: Literal["specialist", "jarvis"] = "specialist",
) -> Vote:
    """
    Parse a vote from model response.

    Args:
        response: Raw model response (should be JSON)
        task_id: Task being evaluated
        voter_id: Specialist who voted
        voter_name: Name of voter
        voter_type: Type of voter

    Returns:
        Parsed Vote object

    Raises:
        VoteParseError: If response cannot be parsed
    """
    import json
    import re

    # Try to extract JSON from response
    # Handle cases where model wraps JSON in markdown
    json_match = re.search(r"\{[\s\S]*\}", response)
    if not json_match:
        raise VoteParseError(f"No JSON found in response: {response[:100]}")

    try:
        data = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise VoteParseError(f"Invalid JSON: {e}")

    # Extract score
    score = data.get("score")
    if score is None:
        # Try to calculate from criteria
        if all(k in data for k in ["correctness", "completeness", "quality", "best_practices"]):
            score = (
                data["correctness"] + data["completeness"] +
                data["quality"] + data["best_practices"]
            ) / 40.0
        else:
            raise VoteParseError("No score found in response")

    # Validate score
    if not isinstance(score, (int, float)):
        raise VoteParseError(f"Invalid score type: {type(score)}")
    score = max(0.0, min(1.0, float(score)))

    # Extract criteria if present
    criteria = None
    if all(k in data for k in ["correctness", "completeness", "quality", "best_practices"]):
        try:
            criteria = VoteCriteria(
                correctness=int(data["correctness"]),
                completeness=int(data["completeness"]),
                quality=int(data["quality"]),
                best_practices=int(data["best_practices"]),
            )
        except (ValueError, TypeError):
            pass  # Criteria optional

    return Vote(
        task_id=task_id,
        voter_id=voter_id,
        voter_name=voter_name,
        voter_type=voter_type,
        score=score,
        criteria=criteria,
        reasoning=str(data.get("reasoning", "")),
        strengths=list(data.get("strengths", [])),
        weaknesses=list(data.get("weaknesses", [])),
    )
