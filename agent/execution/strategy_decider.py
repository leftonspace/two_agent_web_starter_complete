"""
Execution strategy decision engine.

JARVIS's core intelligence: deciding HOW to execute tasks.
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

from agent.llm_client import LLMClient
from agent.core_logging import log_event


class ExecutionMode(Enum):
    """Execution strategy modes"""
    DIRECT = "direct"  # JARVIS executes immediately, no review
    REVIEWED = "reviewed"  # Employee executes, Supervisor reviews
    FULL_LOOP = "full_loop"  # Manager plans, Employee executes, Supervisor reviews
    HUMAN_APPROVAL = "human_approval"  # Full loop + human must approve


@dataclass
class ExecutionStrategy:
    """Decided execution strategy"""
    mode: ExecutionMode
    rationale: str
    estimated_duration_seconds: int
    estimated_cost_usd: float
    risk_level: str  # low, medium, high
    requires_approval: bool
    suggested_timeout_seconds: int


class StrategyDecider:
    """
    Decides execution strategy for tasks.

    Analyzes:
    - Complexity
    - Risk
    - Cost
    - External dependencies
    - Reversibility
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.overrides = StrategyOverrides()

    async def decide_strategy(
        self,
        task_description: str,
        context: Optional[Dict] = None
    ) -> ExecutionStrategy:
        """
        Analyze task and decide execution strategy.

        Args:
            task_description: What needs to be done
            context: Additional context (who requested, urgency, etc.)

        Returns:
            ExecutionStrategy with chosen mode and rationale
        """
        # Check for manual overrides first
        override_mode = self.overrides.get_override(task_description)
        if override_mode:
            return self._create_override_strategy(override_mode, task_description)

        # Get task analysis from LLM
        analysis = await self._analyze_task(task_description, context)

        # Calculate scores
        complexity = self._calculate_complexity(analysis)
        risk = self._calculate_risk(analysis)
        cost = self._estimate_cost(analysis)

        # Decide strategy based on scores
        strategy = self._choose_strategy(
            complexity=complexity,
            risk=risk,
            cost=cost,
            analysis=analysis
        )

        log_event("execution_strategy_decided", {
            "mode": strategy.mode.value,
            "complexity": complexity,
            "risk": risk,
            "cost": cost
        })

        return strategy

    async def _analyze_task(
        self,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict:
        """
        Use LLM to analyze task characteristics.

        Returns detailed analysis of task requirements and risks.
        """
        prompt = f"""Analyze this task to determine how it should be executed.

TASK: {task_description}

CONTEXT: {context or 'No additional context'}

Analyze and return JSON:
{{
  "task_type": "data_query|code_generation|document_creation|api_call|file_modification|deployment|communication",

  "complexity_factors": {{
    "requires_code_generation": true|false,
    "requires_external_apis": true|false,
    "requires_file_modifications": true|false,
    "requires_database_changes": true|false,
    "multi_step_process": true|false,
    "requires_specialized_knowledge": true|false,
    "estimated_steps": 3
  }},

  "risk_factors": {{
    "modifies_production_data": true|false,
    "irreversible_action": true|false,
    "affects_multiple_users": true|false,
    "involves_money": true|false,
    "security_sensitive": true|false,
    "external_visibility": true|false,
    "can_cause_downtime": true|false
  }},

  "resource_requirements": {{
    "estimated_llm_calls": 5,
    "requires_internet": true|false,
    "requires_file_access": true|false,
    "requires_credentials": true|false
  }},

  "reversibility": "fully_reversible|partially_reversible|irreversible",

  "urgency": "immediate|during_meeting|after_meeting|no_urgency",

  "success_criteria": "Clear description of what success looks like"
}}

Be conservative: overestimate complexity and risk rather than underestimate."""

        try:
            analysis = await self.llm.chat_json(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.1
            )
            return analysis

        except Exception as e:
            log_event("task_analysis_failed", {
                "error": str(e)
            })

            # Return safe defaults (high complexity/risk)
            return {
                "task_type": "unknown",
                "complexity_factors": {
                    "multi_step_process": True,
                    "estimated_steps": 10
                },
                "risk_factors": {
                    "modifies_production_data": True
                },
                "reversibility": "irreversible"
            }

    def _calculate_complexity(self, analysis: Dict) -> float:
        """
        Calculate complexity score (0.0 - 10.0).

        Higher = more complex
        """
        factors = analysis.get("complexity_factors", {})

        score = 0.0

        # Weight different factors
        weights = {
            "requires_code_generation": 2.0,
            "requires_external_apis": 1.5,
            "requires_file_modifications": 1.5,
            "requires_database_changes": 2.5,
            "multi_step_process": 1.0,
            "requires_specialized_knowledge": 1.5
        }

        for factor, weight in weights.items():
            if factors.get(factor, False):
                score += weight

        # Add based on estimated steps
        steps = factors.get("estimated_steps", 1)
        score += min(steps * 0.3, 3.0)  # Cap contribution from steps

        return min(score, 10.0)

    def _calculate_risk(self, analysis: Dict) -> float:
        """
        Calculate risk score (0.0 - 10.0).

        Higher = more risky
        """
        factors = analysis.get("risk_factors", {})

        score = 0.0

        # Weight risk factors
        weights = {
            "modifies_production_data": 3.0,
            "irreversible_action": 3.0,
            "affects_multiple_users": 2.0,
            "involves_money": 2.5,
            "security_sensitive": 2.5,
            "external_visibility": 1.5,
            "can_cause_downtime": 3.0
        }

        for factor, weight in weights.items():
            if factors.get(factor, False):
                score += weight

        # Adjust based on reversibility
        reversibility = analysis.get("reversibility", "irreversible")
        if reversibility == "irreversible":
            score += 2.0
        elif reversibility == "partially_reversible":
            score += 1.0

        return min(score, 10.0)

    def _estimate_cost(self, analysis: Dict) -> float:
        """
        Estimate cost in USD.

        Primarily LLM API costs.
        """
        resources = analysis.get("resource_requirements", {})

        llm_calls = resources.get("estimated_llm_calls", 1)

        # Cost per LLM call (rough estimate)
        # GPT-4o: ~$0.15 per call (average)
        cost_per_call = 0.15

        total_cost = llm_calls * cost_per_call

        return round(total_cost, 2)

    def _choose_strategy(
        self,
        complexity: float,
        risk: float,
        cost: float,
        analysis: Dict
    ) -> ExecutionStrategy:
        """
        Choose execution strategy based on scores.

        Decision logic:
        - Direct: Low complexity, low risk, low cost
        - Reviewed: Medium complexity or risk
        - Full loop: High complexity
        - Human approval: High risk or irreversible
        """
        urgency = analysis.get("urgency", "no_urgency")
        reversibility = analysis.get("reversibility", "irreversible")

        # Decision tree
        if risk >= 7.0 or reversibility == "irreversible":
            # High risk → Human approval required
            mode = ExecutionMode.HUMAN_APPROVAL
            rationale = "High risk or irreversible action requires human approval"
            timeout = 300  # 5 minutes

        elif complexity >= 7.0:
            # High complexity → Full review loop
            mode = ExecutionMode.FULL_LOOP
            rationale = "High complexity requires full Manager + Employee + Supervisor process"
            timeout = 180  # 3 minutes

        elif complexity >= 4.0 or risk >= 4.0:
            # Medium complexity/risk → Employee + Supervisor
            mode = ExecutionMode.REVIEWED
            rationale = "Medium complexity/risk requires Employee execution with Supervisor review"
            timeout = 120  # 2 minutes

        else:
            # Low complexity and risk → Direct execution
            mode = ExecutionMode.DIRECT
            rationale = "Low complexity and risk allows direct execution"
            timeout = 30  # 30 seconds

        # Override for urgent tasks (unless high risk)
        if urgency == "immediate" and mode != ExecutionMode.HUMAN_APPROVAL:
            mode = ExecutionMode.DIRECT
            rationale += " (overridden for immediate urgency)"

        # Estimate duration based on complexity
        estimated_duration = int(30 + (complexity * 15))

        return ExecutionStrategy(
            mode=mode,
            rationale=rationale,
            estimated_duration_seconds=estimated_duration,
            estimated_cost_usd=cost,
            risk_level=self._risk_level_label(risk),
            requires_approval=(mode == ExecutionMode.HUMAN_APPROVAL),
            suggested_timeout_seconds=timeout
        )

    def _risk_level_label(self, risk_score: float) -> str:
        """Convert risk score to label"""
        if risk_score >= 7.0:
            return "high"
        elif risk_score >= 4.0:
            return "medium"
        else:
            return "low"

    def _create_override_strategy(
        self,
        mode: ExecutionMode,
        task_description: str
    ) -> ExecutionStrategy:
        """Create strategy from manual override"""
        # Set defaults based on override mode
        if mode == ExecutionMode.HUMAN_APPROVAL:
            timeout = 300
            duration = 180
            risk = "high"
            cost = 1.0
        elif mode == ExecutionMode.FULL_LOOP:
            timeout = 180
            duration = 120
            risk = "medium"
            cost = 0.75
        elif mode == ExecutionMode.REVIEWED:
            timeout = 120
            duration = 60
            risk = "medium"
            cost = 0.45
        else:  # DIRECT
            timeout = 30
            duration = 20
            risk = "low"
            cost = 0.15

        return ExecutionStrategy(
            mode=mode,
            rationale=f"Manual override applied for task pattern",
            estimated_duration_seconds=duration,
            estimated_cost_usd=cost,
            risk_level=risk,
            requires_approval=(mode == ExecutionMode.HUMAN_APPROVAL),
            suggested_timeout_seconds=timeout
        )


class StrategyOverrides:
    """
    Manual overrides for specific task patterns.

    Allows developers to specify execution strategies for known tasks.
    """

    def __init__(self):
        self.overrides: Dict[str, ExecutionMode] = {}
        self._load_default_overrides()

    def _load_default_overrides(self):
        """Load default strategy overrides"""

        # Tasks that should ALWAYS be human-approved
        self.overrides["deploy_to_production"] = ExecutionMode.HUMAN_APPROVAL
        self.overrides["delete_database"] = ExecutionMode.HUMAN_APPROVAL
        self.overrides["process_payment"] = ExecutionMode.HUMAN_APPROVAL
        self.overrides["send_to_all_users"] = ExecutionMode.HUMAN_APPROVAL
        self.overrides["drop_table"] = ExecutionMode.HUMAN_APPROVAL
        self.overrides["remove_user"] = ExecutionMode.HUMAN_APPROVAL
        self.overrides["revoke_access"] = ExecutionMode.HUMAN_APPROVAL

        # Tasks that can be direct
        self.overrides["query_database_readonly"] = ExecutionMode.DIRECT
        self.overrides["search_documentation"] = ExecutionMode.DIRECT
        self.overrides["create_document"] = ExecutionMode.DIRECT
        self.overrides["read_file"] = ExecutionMode.DIRECT
        self.overrides["search_code"] = ExecutionMode.DIRECT
        self.overrides["get_status"] = ExecutionMode.DIRECT

        # Tasks that need review
        self.overrides["generate_code"] = ExecutionMode.REVIEWED
        self.overrides["modify_configuration"] = ExecutionMode.REVIEWED
        self.overrides["update_schema"] = ExecutionMode.REVIEWED
        self.overrides["change_settings"] = ExecutionMode.REVIEWED

    def get_override(self, task_description: str) -> Optional[ExecutionMode]:
        """
        Check if task matches any override patterns.

        Returns override mode or None.
        """
        task_lower = task_description.lower()

        for pattern, mode in self.overrides.items():
            if pattern.replace("_", " ") in task_lower:
                log_event("strategy_override_applied", {
                    "pattern": pattern,
                    "mode": mode.value
                })
                return mode

        return None

    def add_override(self, pattern: str, mode: ExecutionMode):
        """Add custom override"""
        self.overrides[pattern] = mode
        log_event("strategy_override_added", {
            "pattern": pattern,
            "mode": mode.value
        })

    def remove_override(self, pattern: str):
        """Remove custom override"""
        if pattern in self.overrides:
            del self.overrides[pattern]
            log_event("strategy_override_removed", {
                "pattern": pattern
            })

    def list_overrides(self) -> Dict[str, str]:
        """List all current overrides"""
        return {pattern: mode.value for pattern, mode in self.overrides.items()}
