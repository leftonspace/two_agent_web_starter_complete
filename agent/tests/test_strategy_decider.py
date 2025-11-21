"""
Tests for execution strategy decider.

PHASE 7B.1: Tests for intelligent execution strategy selection.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from agent.execution.strategy_decider import (
    StrategyDecider,
    ExecutionMode,
    ExecutionStrategy,
    StrategyOverrides
)


# ══════════════════════════════════════════════════════════════════════
# Strategy Decision Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_simple_task_direct_execution():
    """Test simple task gets direct execution"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "data_query",
        "complexity_factors": {
            "requires_code_generation": False,
            "requires_external_apis": False,
            "requires_file_modifications": False,
            "requires_database_changes": False,
            "multi_step_process": False,
            "requires_specialized_knowledge": False,
            "estimated_steps": 1
        },
        "risk_factors": {
            "modifies_production_data": False,
            "irreversible_action": False,
            "affects_multiple_users": False,
            "involves_money": False,
            "security_sensitive": False,
            "external_visibility": False,
            "can_cause_downtime": False
        },
        "resource_requirements": {
            "estimated_llm_calls": 1,
            "requires_internet": False,
            "requires_file_access": False,
            "requires_credentials": False
        },
        "reversibility": "fully_reversible",
        "urgency": "no_urgency",
        "success_criteria": "Return revenue number"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy("What is our Q3 revenue?")

    assert strategy.mode == ExecutionMode.DIRECT
    assert strategy.risk_level == "low"
    assert strategy.requires_approval is False


@pytest.mark.asyncio
async def test_medium_complexity_task_reviewed():
    """Test medium complexity task gets reviewed execution"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "code_generation",
        "complexity_factors": {
            "requires_code_generation": True,
            "requires_external_apis": False,
            "requires_file_modifications": True,
            "requires_database_changes": False,
            "multi_step_process": True,
            "requires_specialized_knowledge": False,
            "estimated_steps": 5
        },
        "risk_factors": {
            "modifies_production_data": False,
            "irreversible_action": False,
            "affects_multiple_users": False,
            "involves_money": False,
            "security_sensitive": False,
            "external_visibility": False,
            "can_cause_downtime": False
        },
        "resource_requirements": {
            "estimated_llm_calls": 3,
            "requires_internet": False,
            "requires_file_access": True,
            "requires_credentials": False
        },
        "reversibility": "fully_reversible",
        "urgency": "no_urgency",
        "success_criteria": "Script works correctly"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy("Write a script to analyze logs")

    assert strategy.mode == ExecutionMode.REVIEWED
    assert strategy.risk_level in ["low", "medium"]


@pytest.mark.asyncio
async def test_complex_task_full_loop():
    """Test complex task gets full review loop"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "code_generation",
        "complexity_factors": {
            "requires_code_generation": True,
            "requires_external_apis": True,
            "requires_file_modifications": True,
            "requires_database_changes": True,
            "multi_step_process": True,
            "requires_specialized_knowledge": True,
            "estimated_steps": 10
        },
        "risk_factors": {
            "modifies_production_data": False,
            "irreversible_action": False,
            "affects_multiple_users": True,
            "involves_money": False,
            "security_sensitive": True,
            "external_visibility": False,
            "can_cause_downtime": False
        },
        "resource_requirements": {
            "estimated_llm_calls": 10,
            "requires_internet": True,
            "requires_file_access": True,
            "requires_credentials": True
        },
        "reversibility": "partially_reversible",
        "urgency": "no_urgency",
        "success_criteria": "Authentication system works securely"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy(
        "Build a new authentication system"
    )

    assert strategy.mode == ExecutionMode.FULL_LOOP
    assert strategy.estimated_duration_seconds > 100


@pytest.mark.asyncio
async def test_risky_task_human_approval():
    """Test risky task requires human approval"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "deployment",
        "complexity_factors": {
            "requires_code_generation": False,
            "requires_external_apis": True,
            "requires_file_modifications": True,
            "requires_database_changes": False,
            "multi_step_process": True,
            "requires_specialized_knowledge": False,
            "estimated_steps": 5
        },
        "risk_factors": {
            "modifies_production_data": True,
            "irreversible_action": True,
            "affects_multiple_users": True,
            "involves_money": False,
            "security_sensitive": True,
            "external_visibility": True,
            "can_cause_downtime": True
        },
        "resource_requirements": {
            "estimated_llm_calls": 3,
            "requires_internet": True,
            "requires_file_access": True,
            "requires_credentials": True
        },
        "reversibility": "irreversible",
        "urgency": "no_urgency",
        "success_criteria": "Deployment successful with no downtime"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy("Deploy to production")

    assert strategy.mode == ExecutionMode.HUMAN_APPROVAL
    assert strategy.requires_approval is True
    assert strategy.risk_level == "high"


@pytest.mark.asyncio
async def test_irreversible_task_human_approval():
    """Test irreversible action requires human approval"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "data_modification",
        "complexity_factors": {
            "requires_code_generation": False,
            "requires_external_apis": False,
            "requires_file_modifications": False,
            "requires_database_changes": True,
            "multi_step_process": False,
            "requires_specialized_knowledge": False,
            "estimated_steps": 2
        },
        "risk_factors": {
            "modifies_production_data": True,
            "irreversible_action": True,
            "affects_multiple_users": False,
            "involves_money": False,
            "security_sensitive": False,
            "external_visibility": False,
            "can_cause_downtime": False
        },
        "resource_requirements": {
            "estimated_llm_calls": 1,
            "requires_internet": False,
            "requires_file_access": False,
            "requires_credentials": True
        },
        "reversibility": "irreversible",
        "urgency": "no_urgency",
        "success_criteria": "Table deleted"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy("Delete old user table")

    assert strategy.mode == ExecutionMode.HUMAN_APPROVAL
    assert strategy.requires_approval is True


# ══════════════════════════════════════════════════════════════════════
# Strategy Override Tests
# ══════════════════════════════════════════════════════════════════════


def test_strategy_overrides_human_approval():
    """Test manual strategy overrides for high-risk tasks"""
    overrides = StrategyOverrides()

    # Should override to human approval
    mode = overrides.get_override("deploy to production server")
    assert mode == ExecutionMode.HUMAN_APPROVAL

    mode = overrides.get_override("delete database tables")
    assert mode == ExecutionMode.HUMAN_APPROVAL

    mode = overrides.get_override("process payment for customer")
    assert mode == ExecutionMode.HUMAN_APPROVAL


def test_strategy_overrides_direct():
    """Test manual strategy overrides for safe tasks"""
    overrides = StrategyOverrides()

    # Should override to direct
    mode = overrides.get_override("query database for user count")
    assert mode == ExecutionMode.DIRECT

    mode = overrides.get_override("search documentation for API")
    assert mode == ExecutionMode.DIRECT

    mode = overrides.get_override("create document with meeting notes")
    assert mode == ExecutionMode.DIRECT


def test_strategy_overrides_reviewed():
    """Test manual strategy overrides for tasks needing review"""
    overrides = StrategyOverrides()

    # Should override to reviewed
    mode = overrides.get_override("generate code for new feature")
    assert mode == ExecutionMode.REVIEWED

    mode = overrides.get_override("modify configuration settings")
    assert mode == ExecutionMode.REVIEWED


def test_strategy_override_no_match():
    """Test that unmatched tasks return None"""
    overrides = StrategyOverrides()

    mode = overrides.get_override("some random unique task description")
    assert mode is None


def test_add_custom_override():
    """Test adding custom override"""
    overrides = StrategyOverrides()

    overrides.add_override("custom_task", ExecutionMode.FULL_LOOP)

    mode = overrides.get_override("custom task execution")
    assert mode == ExecutionMode.FULL_LOOP


def test_remove_override():
    """Test removing override"""
    overrides = StrategyOverrides()

    # Add and then remove
    overrides.add_override("temp_task", ExecutionMode.DIRECT)
    mode = overrides.get_override("temp task")
    assert mode == ExecutionMode.DIRECT

    overrides.remove_override("temp_task")
    mode = overrides.get_override("temp task")
    assert mode is None


# ══════════════════════════════════════════════════════════════════════
# Urgency Override Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_urgent_task_override():
    """Test urgent tasks get direct execution (unless high risk)"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "document_creation",
        "complexity_factors": {
            "requires_code_generation": False,
            "requires_external_apis": False,
            "requires_file_modifications": True,
            "requires_database_changes": False,
            "multi_step_process": True,
            "requires_specialized_knowledge": False,
            "estimated_steps": 3
        },
        "risk_factors": {
            "modifies_production_data": False,
            "irreversible_action": False,
            "affects_multiple_users": False,
            "involves_money": False,
            "security_sensitive": False,
            "external_visibility": False,
            "can_cause_downtime": False
        },
        "resource_requirements": {
            "estimated_llm_calls": 2,
            "requires_internet": False,
            "requires_file_access": True,
            "requires_credentials": False
        },
        "reversibility": "fully_reversible",
        "urgency": "immediate",
        "success_criteria": "Summary created"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy(
        "Create meeting summary",
        context={"urgency": "immediate"}
    )

    # Should be direct despite some complexity, due to urgency
    assert strategy.mode == ExecutionMode.DIRECT
    assert "urgency" in strategy.rationale.lower()


@pytest.mark.asyncio
async def test_urgent_high_risk_still_requires_approval():
    """Test urgent high-risk tasks still require approval"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(return_value={
        "task_type": "deployment",
        "complexity_factors": {
            "multi_step_process": True,
            "estimated_steps": 3
        },
        "risk_factors": {
            "modifies_production_data": True,
            "irreversible_action": True,
            "can_cause_downtime": True
        },
        "resource_requirements": {
            "estimated_llm_calls": 2
        },
        "reversibility": "irreversible",
        "urgency": "immediate",
        "success_criteria": "Hotfix deployed"
    })

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy(
        "Deploy hotfix to production immediately",
        context={"urgency": "immediate"}
    )

    # Should still require approval despite urgency
    assert strategy.mode == ExecutionMode.HUMAN_APPROVAL


# ══════════════════════════════════════════════════════════════════════
# Score Calculation Tests
# ══════════════════════════════════════════════════════════════════════


def test_complexity_calculation():
    """Test complexity score calculation"""
    llm_mock = Mock()
    decider = StrategyDecider(llm_mock)

    # Simple task
    analysis = {
        "complexity_factors": {
            "requires_code_generation": False,
            "multi_step_process": False,
            "estimated_steps": 1
        }
    }
    complexity = decider._calculate_complexity(analysis)
    assert complexity < 2.0

    # Complex task
    analysis = {
        "complexity_factors": {
            "requires_code_generation": True,
            "requires_database_changes": True,
            "multi_step_process": True,
            "requires_specialized_knowledge": True,
            "estimated_steps": 10
        }
    }
    complexity = decider._calculate_complexity(analysis)
    assert complexity >= 7.0


def test_risk_calculation():
    """Test risk score calculation"""
    llm_mock = Mock()
    decider = StrategyDecider(llm_mock)

    # Low risk task
    analysis = {
        "risk_factors": {
            "modifies_production_data": False,
            "irreversible_action": False
        },
        "reversibility": "fully_reversible"
    }
    risk = decider._calculate_risk(analysis)
    assert risk < 2.0

    # High risk task
    analysis = {
        "risk_factors": {
            "modifies_production_data": True,
            "irreversible_action": True,
            "can_cause_downtime": True,
            "affects_multiple_users": True
        },
        "reversibility": "irreversible"
    }
    risk = decider._calculate_risk(analysis)
    assert risk >= 7.0


def test_cost_estimation():
    """Test cost estimation"""
    llm_mock = Mock()
    decider = StrategyDecider(llm_mock)

    # Low cost task
    analysis = {
        "resource_requirements": {
            "estimated_llm_calls": 1
        }
    }
    cost = decider._estimate_cost(analysis)
    assert cost < 0.5

    # High cost task
    analysis = {
        "resource_requirements": {
            "estimated_llm_calls": 10
        }
    }
    cost = decider._estimate_cost(analysis)
    assert cost > 1.0


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_llm_failure_defaults_to_safe():
    """Test that LLM failure defaults to safe (high complexity/risk)"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock(side_effect=Exception("API error"))

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy("Some task")

    # Should default to human approval for safety
    assert strategy.mode == ExecutionMode.HUMAN_APPROVAL


@pytest.mark.asyncio
async def test_strategy_override_bypasses_llm():
    """Test that override bypasses LLM analysis"""
    llm_mock = Mock()
    llm_mock.chat_json = AsyncMock()  # Should not be called

    decider = StrategyDecider(llm_mock)
    strategy = await decider.decide_strategy("deploy to production")

    # Should use override, not call LLM
    assert strategy.mode == ExecutionMode.HUMAN_APPROVAL
    llm_mock.chat_json.assert_not_called()
