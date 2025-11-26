"""
PHASE 7.5: Scoring Committee

Production evaluator using external ground truth verification.
NO AI judging AI - only external tools and user feedback.

Usage:
    from core.evaluation.scoring_committee import (
        ScoringCommittee,
        TestRunner,
        Linter,
        FormatChecker,
        SpellChecker,
        UserFeedback,
        UserFeedbackCollector,
        get_feedback_collector,
    )

    # Create committee
    committee = ScoringCommittee()

    # Evaluate
    result = await committee.evaluate(task_result)

    # Submit user feedback
    collector = get_feedback_collector()
    await collector.submit(UserFeedback(...))
"""

from .committee import (
    ScoringCommittee,
    ScoringCommitteeConfig,
    create_scoring_committee,
)

from .test_runner import (
    TestRunner,
    TestRunResult,
    TestCaseResult,
)

from .linter import (
    Linter,
    LintResult,
    LintIssue,
)

from .format_checker import (
    FormatChecker,
    FormatCheckResult,
    FormatIssue,
)

from .spell_checker import (
    SpellChecker,
    SpellCheckResult,
    SpellingError,
)

from .user_feedback import (
    UserFeedback,
    FeedbackRequest,
    UserFeedbackCollector,
    get_feedback_collector,
    reset_feedback_collector,
)


__all__ = [
    # Committee
    "ScoringCommittee",
    "ScoringCommitteeConfig",
    "create_scoring_committee",
    # Test Runner
    "TestRunner",
    "TestRunResult",
    "TestCaseResult",
    # Linter
    "Linter",
    "LintResult",
    "LintIssue",
    # Format Checker
    "FormatChecker",
    "FormatCheckResult",
    "FormatIssue",
    # Spell Checker
    "SpellChecker",
    "SpellCheckResult",
    "SpellingError",
    # User Feedback
    "UserFeedback",
    "FeedbackRequest",
    "UserFeedbackCollector",
    "get_feedback_collector",
    "reset_feedback_collector",
]
