"""
PHASE 3.2: Orchestrator Mode Selector

Implements the 2-loop preference policy from the hardening guide:
- Default to 2-loop (Manager ↔ Employee) for 80% of tasks
- Escalate to 3-loop (with Supervisor) only for high complexity/risk tasks

Complexity Indicators (trigger 3-loop):
- Task mentions multiple systems/integrations
- Task involves financial operations
- Task involves security-sensitive operations
- Task involves database schema changes
- Task involves deployment/production changes
- Task is explicitly marked as complex

Risk Indicators (trigger 3-loop):
- Task involves deletion operations
- Task involves external API calls with side effects
- Task involves user data
- Task involves authentication/authorization

Usage:
    from orchestrator_selector import select_orchestrator_mode, OrchestratorMode

    # Auto-select based on task analysis
    mode = select_orchestrator_mode(task="Build a simple landing page")
    # Returns: OrchestratorMode.TWO_LOOP

    mode = select_orchestrator_mode(task="Implement payment processing with Stripe")
    # Returns: OrchestratorMode.THREE_LOOP
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from agent.core_logging import log_event


class OrchestratorMode(Enum):
    """Available orchestrator modes."""
    TWO_LOOP = "2loop"      # Manager ↔ Employee (simpler, faster, cheaper)
    THREE_LOOP = "3loop"    # Manager ↔ Supervisor ↔ Employee (complex tasks)
    AUTO = "auto"           # Auto-select based on task analysis


# ============================================================================
# Complexity and Risk Patterns
# ============================================================================

# Patterns that indicate HIGH COMPLEXITY (should use 3-loop)
HIGH_COMPLEXITY_PATTERNS: List[str] = [
    # Multi-system integration
    r"(?i)integrat(e|ion|ing)\s+with\s+",
    r"(?i)connect\s+to\s+multiple",
    r"(?i)orchestrat(e|ion)",
    r"(?i)microservices?",
    r"(?i)distributed\s+system",

    # Database operations
    r"(?i)database\s+migration",
    r"(?i)schema\s+change",
    r"(?i)data\s+model\s+redesign",

    # Deployment/Infrastructure
    r"(?i)deploy\s+to\s+production",
    r"(?i)kubernetes|k8s",
    r"(?i)docker\s+compose",
    r"(?i)ci/?cd\s+pipeline",
    r"(?i)infrastructure\s+as\s+code",

    # Architecture
    r"(?i)refactor\s+(the\s+)?(entire|whole|complete)",
    r"(?i)redesign\s+(the\s+)?(architecture|system)",
    r"(?i)major\s+(change|update|overhaul)",
]

# Patterns that indicate HIGH RISK (should use 3-loop)
HIGH_RISK_PATTERNS: List[str] = [
    # Financial operations
    r"(?i)payment\s+processing",
    r"(?i)stripe|paypal|braintree",
    r"(?i)billing|invoice|charge",
    r"(?i)transaction",
    r"(?i)financial\s+data",

    # Security-sensitive
    r"(?i)authentication|auth\s+system",
    r"(?i)authorization|permissions?|rbac",
    r"(?i)password|credential",
    r"(?i)encrypt|decrypt",
    r"(?i)api\s+key|secret|token",
    r"(?i)oauth|jwt|saml",

    # Data-sensitive
    r"(?i)user\s+data|pii|personal\s+information",
    r"(?i)gdpr|ccpa|compliance",
    r"(?i)backup\s+and\s+restore",

    # Destructive operations
    r"(?i)delete\s+(all|everything|database)",
    r"(?i)drop\s+(table|database|collection)",
    r"(?i)truncate",
    r"(?i)purge|wipe|erase",
    r"(?i)irreversible",
]

# Patterns that indicate LOW COMPLEXITY (can use 2-loop)
LOW_COMPLEXITY_PATTERNS: List[str] = [
    r"(?i)simple\s+(page|component|feature)",
    r"(?i)basic\s+(crud|form|layout)",
    r"(?i)add\s+(a\s+)?button",
    r"(?i)update\s+(the\s+)?(css|style|color|font)",
    r"(?i)fix\s+(a\s+)?(typo|bug|error)",
    r"(?i)landing\s+page",
    r"(?i)hello\s+world",
    r"(?i)readme|documentation",
]

# Keywords that explicitly request 3-loop
EXPLICIT_3LOOP_KEYWORDS: List[str] = [
    "complex",
    "critical",
    "production",
    "enterprise",
    "mission-critical",
    "high-risk",
    "supervisor",
    "3-loop",
    "three-loop",
]


@dataclass
class ComplexityAnalysis:
    """Result of task complexity analysis."""
    recommended_mode: OrchestratorMode
    complexity_score: float  # 0.0 (simple) to 1.0 (very complex)
    risk_score: float        # 0.0 (low risk) to 1.0 (high risk)
    complexity_indicators: List[str]
    risk_indicators: List[str]
    reason: str


def analyze_task_complexity(task: str) -> ComplexityAnalysis:
    """
    Analyze task complexity and risk to determine orchestrator mode.

    Args:
        task: Task description to analyze

    Returns:
        ComplexityAnalysis with recommendation
    """
    if not task:
        return ComplexityAnalysis(
            recommended_mode=OrchestratorMode.TWO_LOOP,
            complexity_score=0.0,
            risk_score=0.0,
            complexity_indicators=[],
            risk_indicators=[],
            reason="Empty task - defaulting to 2-loop",
        )

    task_lower = task.lower()
    complexity_indicators = []
    risk_indicators = []

    # Check for explicit 3-loop request
    for keyword in EXPLICIT_3LOOP_KEYWORDS:
        if keyword in task_lower:
            return ComplexityAnalysis(
                recommended_mode=OrchestratorMode.THREE_LOOP,
                complexity_score=1.0,
                risk_score=1.0,
                complexity_indicators=[f"Explicit keyword: {keyword}"],
                risk_indicators=[],
                reason=f"Task explicitly marked as '{keyword}' - using 3-loop",
            )

    # Check for low complexity patterns (early exit to 2-loop)
    low_complexity_matches = 0
    for pattern in LOW_COMPLEXITY_PATTERNS:
        if re.search(pattern, task):
            low_complexity_matches += 1

    if low_complexity_matches >= 2:
        return ComplexityAnalysis(
            recommended_mode=OrchestratorMode.TWO_LOOP,
            complexity_score=0.1,
            risk_score=0.0,
            complexity_indicators=[],
            risk_indicators=[],
            reason="Multiple low-complexity indicators - using 2-loop",
        )

    # Check high complexity patterns
    for pattern in HIGH_COMPLEXITY_PATTERNS:
        match = re.search(pattern, task)
        if match:
            complexity_indicators.append(match.group(0))

    # Check high risk patterns
    for pattern in HIGH_RISK_PATTERNS:
        match = re.search(pattern, task)
        if match:
            risk_indicators.append(match.group(0))

    # Calculate scores
    complexity_score = min(1.0, len(complexity_indicators) * 0.25)
    risk_score = min(1.0, len(risk_indicators) * 0.3)

    # Combined score (risk weighted higher)
    combined_score = (complexity_score * 0.4) + (risk_score * 0.6)

    # Decision threshold
    ESCALATION_THRESHOLD = 0.3

    if combined_score >= ESCALATION_THRESHOLD:
        reason_parts = []
        if complexity_indicators:
            reason_parts.append(f"Complexity: {', '.join(complexity_indicators[:3])}")
        if risk_indicators:
            reason_parts.append(f"Risk: {', '.join(risk_indicators[:3])}")

        return ComplexityAnalysis(
            recommended_mode=OrchestratorMode.THREE_LOOP,
            complexity_score=complexity_score,
            risk_score=risk_score,
            complexity_indicators=complexity_indicators,
            risk_indicators=risk_indicators,
            reason=f"High complexity/risk detected - {'; '.join(reason_parts)}",
        )

    return ComplexityAnalysis(
        recommended_mode=OrchestratorMode.TWO_LOOP,
        complexity_score=complexity_score,
        risk_score=risk_score,
        complexity_indicators=complexity_indicators,
        risk_indicators=risk_indicators,
        reason="Standard task - using efficient 2-loop mode",
    )


def select_orchestrator_mode(
    task: str,
    force_mode: Optional[str] = None,
    log_analysis: bool = True,
) -> str:
    """
    Select the appropriate orchestrator mode for a task.

    PHASE 3.2: Implements 2-loop preference policy.

    Args:
        task: Task description
        force_mode: Override auto-selection ("2loop", "3loop", or None for auto)
        log_analysis: Whether to log the analysis

    Returns:
        Mode string ("2loop" or "3loop")
    """
    # Check environment override
    env_mode = os.getenv("JARVIS_ORCHESTRATOR_MODE", "").lower()
    if env_mode in ("2loop", "3loop"):
        if log_analysis:
            log_event("orchestrator_mode_env_override", {"mode": env_mode})
        return env_mode

    # Check explicit force
    if force_mode in ("2loop", "3loop"):
        if log_analysis:
            log_event("orchestrator_mode_forced", {"mode": force_mode})
        return force_mode

    # Auto-select based on task analysis
    analysis = analyze_task_complexity(task)

    if log_analysis:
        log_event("orchestrator_mode_selected", {
            "mode": analysis.recommended_mode.value,
            "complexity_score": analysis.complexity_score,
            "risk_score": analysis.risk_score,
            "reason": analysis.reason,
            "complexity_indicators": analysis.complexity_indicators[:5],
            "risk_indicators": analysis.risk_indicators[:5],
        })

        print(f"[OrchestratorSelector] Mode: {analysis.recommended_mode.value}")
        print(f"[OrchestratorSelector] Reason: {analysis.reason}")
        if analysis.complexity_score > 0 or analysis.risk_score > 0:
            print(f"[OrchestratorSelector] Scores: complexity={analysis.complexity_score:.2f}, risk={analysis.risk_score:.2f}")

    return analysis.recommended_mode.value


def get_mode_description(mode: str) -> str:
    """Get a human-readable description of an orchestrator mode."""
    descriptions = {
        "2loop": "Manager ↔ Employee (efficient, for standard tasks)",
        "3loop": "Manager ↔ Supervisor ↔ Employee (thorough, for complex/risky tasks)",
        "auto": "Auto-select based on task complexity analysis",
    }
    return descriptions.get(mode, f"Unknown mode: {mode}")
