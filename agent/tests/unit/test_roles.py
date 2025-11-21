"""
PHASE 2.5: Role-Based Department Profiles - Unit Tests

Tests for the role definition system with department-specific roles.
"""

import pytest
from pathlib import Path
from typing import Dict, Any

from agent.roles import (
    RoleProfile,
    RoleRegistry,
    RoleLevel,
    get_role_registry,
)
from agent.permissions import Permission
from agent.domain_router import select_role_for_task, get_role_and_domain_info


# ══════════════════════════════════════════════════════════════════════
# Test Role Loading
# ══════════════════════════════════════════════════════════════════════


def test_role_registry_loads_roles():
    """Test that role registry loads roles from JSON files"""
    registry = RoleRegistry()

    # Should have loaded roles from hr_roles.json, finance_roles.json, legal_roles.json
    assert len(registry.roles) >= 9, "Should have at least 9 roles (3 per department)"

    # Check that roles are loaded
    stats = registry.get_statistics()
    assert stats["total_roles"] >= 9
    assert "hr" in stats["departments"]
    assert "finance" in stats["departments"]
    assert "legal" in stats["departments"]


def test_hr_roles_loaded():
    """Test that HR roles are loaded correctly"""
    registry = RoleRegistry()

    # Check HR Hiring Manager
    hiring_manager = registry.get_role("hr_hiring_manager")
    assert hiring_manager is not None
    assert hiring_manager.role_name == "Hiring Manager"
    assert hiring_manager.department == "hr"
    assert hiring_manager.level == RoleLevel.MANAGER
    assert "recruitment" in hiring_manager.expertise_areas
    assert "interviewing" in hiring_manager.expertise_areas

    # Check HR Recruiter
    recruiter = registry.get_role("hr_recruiter")
    assert recruiter is not None
    assert recruiter.role_name == "Recruiter"
    assert recruiter.level == RoleLevel.INDIVIDUAL_CONTRIBUTOR
    assert "sourcing" in recruiter.expertise_areas

    # Check HR Business Partner
    hrbp = registry.get_role("hr_business_partner")
    assert hrbp is not None
    assert hrbp.role_name == "HR Business Partner"
    assert "employee_relations" in hrbp.expertise_areas


def test_finance_roles_loaded():
    """Test that Finance roles are loaded correctly"""
    registry = RoleRegistry()

    # Check Finance Controller
    controller = registry.get_role("finance_controller")
    assert controller is not None
    assert controller.role_name == "Finance Controller"
    assert controller.department == "finance"
    assert controller.level == RoleLevel.MANAGER
    assert "financial_reporting" in controller.expertise_areas

    # Check Staff Accountant
    accountant = registry.get_role("finance_accountant")
    assert accountant is not None
    assert accountant.level == RoleLevel.INDIVIDUAL_CONTRIBUTOR

    # Check Financial Analyst
    analyst = registry.get_role("finance_analyst")
    assert analyst is not None
    assert "financial_modeling" in analyst.expertise_areas


def test_legal_roles_loaded():
    """Test that Legal roles are loaded correctly"""
    registry = RoleRegistry()

    # Check Legal Counsel
    counsel = registry.get_role("legal_counsel")
    assert counsel is not None
    assert counsel.role_name == "Legal Counsel"
    assert counsel.department == "legal"
    assert counsel.level == RoleLevel.MANAGER
    assert "contract_law" in counsel.expertise_areas

    # Check Contract Manager
    contract_mgr = registry.get_role("legal_contract_manager")
    assert contract_mgr is not None
    assert "contract_drafting" in contract_mgr.expertise_areas

    # Check Paralegal
    paralegal = registry.get_role("legal_paralegal")
    assert paralegal is not None
    assert "legal_research" in paralegal.expertise_areas


# ══════════════════════════════════════════════════════════════════════
# Test Role Selection
# ══════════════════════════════════════════════════════════════════════


def test_role_selection_for_hiring_task():
    """Test role selection for hiring-related tasks"""
    registry = RoleRegistry()

    # Task with "interviewing" keyword should match an HR role
    role_id = registry.select_role_for_task(
        task="Interview candidates for software engineer position",
        department="hr"
    )
    assert role_id in ["hr_hiring_manager", "hr_recruiter"]

    # Task with "sourcing" keyword should match Recruiter
    role_id = registry.select_role_for_task(
        task="Source candidates on LinkedIn for data scientist role",
        department="hr"
    )
    assert role_id == "hr_recruiter"


def test_role_selection_for_finance_task():
    """Test role selection for finance-related tasks"""
    registry = RoleRegistry()

    # Financial reporting task should match finance role
    role_id = registry.select_role_for_task(
        task="Prepare monthly financial reports and budget analysis",
        department="finance"
    )
    assert role_id in ["finance_controller", "finance_analyst", "finance_accountant"]

    # Financial modeling task should match Analyst or Accountant
    role_id = registry.select_role_for_task(
        task="Build financial model for new product launch",
        department="finance"
    )
    assert role_id in ["finance_analyst", "finance_accountant"]


def test_role_selection_for_legal_task():
    """Test role selection for legal-related tasks"""
    registry = RoleRegistry()

    # Contract review should match legal role
    role_id = registry.select_role_for_task(
        task="Review vendor contract for compliance and litigation risk",
        department="legal"
    )
    assert role_id in ["legal_counsel", "legal_contract_manager"]

    # Legal research should match paralegal or contract manager
    role_id = registry.select_role_for_task(
        task="Conduct legal research on employment law",
        department="legal"
    )
    assert role_id in ["legal_paralegal", "legal_contract_manager"]


def test_role_selection_fallback():
    """Test that role selection falls back gracefully when no match"""
    registry = RoleRegistry()

    # Generic task with no keyword matches
    role_id = registry.select_role_for_task(
        task="General administrative work",
        department="hr"
    )
    # Should return some role (defaults to first IC role)
    assert role_id is not None


# ══════════════════════════════════════════════════════════════════════
# Test Permission Enforcement
# ══════════════════════════════════════════════════════════════════════


def test_role_permissions():
    """Test that roles have correct permissions"""
    registry = RoleRegistry()

    # Hiring Manager should have write permissions
    hiring_manager = registry.get_role("hr_hiring_manager")
    assert hiring_manager.has_permission(Permission.FILESYSTEM_WRITE)
    assert hiring_manager.has_permission(Permission.EMAIL_SEND)
    assert hiring_manager.has_permission(Permission.HRIS_WRITE)

    # Recruiter should have limited permissions (no HRIS write)
    recruiter = registry.get_role("hr_recruiter")
    assert recruiter.has_permission(Permission.EMAIL_SEND)
    assert recruiter.has_permission(Permission.HRIS_READ)
    assert not recruiter.has_permission(Permission.FILESYSTEM_WRITE)


def test_role_tool_access():
    """Test that roles have correct tool access"""
    registry = RoleRegistry()

    # Hiring Manager can use all HR tools
    hiring_manager = registry.get_role("hr_hiring_manager")
    assert hiring_manager.can_use_tool("send_email")
    assert hiring_manager.can_use_tool("create_calendar_event")
    assert hiring_manager.can_use_tool("create_hris_record")
    assert hiring_manager.can_use_tool("generate_word_document")

    # Recruiter has limited tools (no HRIS record creation)
    recruiter = registry.get_role("hr_recruiter")
    assert recruiter.can_use_tool("send_email")
    assert recruiter.can_use_tool("create_calendar_event")
    assert not recruiter.can_use_tool("create_hris_record")


def test_role_workflow_access():
    """Test that roles have correct workflow access"""
    registry = RoleRegistry()

    hiring_manager = registry.get_role("hr_hiring_manager")
    assert hiring_manager.can_execute_workflow("candidate_screening")
    assert hiring_manager.can_execute_workflow("offer_generation")

    recruiter = registry.get_role("hr_recruiter")
    assert recruiter.can_execute_workflow("candidate_sourcing")
    assert not recruiter.can_execute_workflow("offer_generation")


# ══════════════════════════════════════════════════════════════════════
# Test System Prompt Generation
# ══════════════════════════════════════════════════════════════════════


def test_system_prompt_generation():
    """Test that system prompts are generated correctly"""
    registry = RoleRegistry()

    hiring_manager = registry.get_role("hr_hiring_manager")
    task = "Interview candidates for software engineer position"

    prompt = hiring_manager.build_system_prompt(task, context={})

    # Should contain role information
    assert "Hiring Manager" in prompt
    assert "recruitment" in prompt
    assert task in prompt


def test_system_prompt_with_context():
    """Test system prompt generation with additional context"""
    registry = RoleRegistry()

    hiring_manager = registry.get_role("hr_hiring_manager")
    task = "Review candidate applications"
    context = {
        "company_name": "Acme Corp",
        "department_name": "Engineering"
    }

    prompt = hiring_manager.build_system_prompt(task, context=context)

    # Should contain role and task
    assert "Hiring Manager" in prompt
    assert task in prompt


def test_system_prompt_includes_escalation():
    """Test that system prompts include escalation role"""
    registry = RoleRegistry()

    recruiter = registry.get_role("hr_recruiter")
    task = "Screen candidates"

    prompt = recruiter.build_system_prompt(task, context={})

    # Should mention escalation to hiring manager
    assert "hr_hiring_manager" in prompt or "Hiring Manager" in prompt.lower()


# ══════════════════════════════════════════════════════════════════════
# Test Decision Authority
# ══════════════════════════════════════════════════════════════════════


def test_decision_authority_checks():
    """Test that decision authority is checked correctly"""
    registry = RoleRegistry()

    # Hiring Manager can approve offers up to $100k
    hiring_manager = registry.get_role("hr_hiring_manager")
    assert hiring_manager.check_decision_authority("can_approve_offers_up_to", amount=80000)
    assert hiring_manager.check_decision_authority("can_approve_offers_up_to", amount=100000)
    assert not hiring_manager.check_decision_authority("can_approve_offers_up_to", amount=150000)

    # Recruiter cannot extend offers
    recruiter = registry.get_role("hr_recruiter")
    assert not recruiter.check_decision_authority("can_extend_offers")
    assert recruiter.check_decision_authority("can_schedule_interviews")


def test_finance_decision_authority():
    """Test finance role decision authority"""
    registry = RoleRegistry()

    controller = registry.get_role("finance_controller")
    assert controller.check_decision_authority("can_approve_expenses_up_to", amount=20000)
    assert not controller.check_decision_authority("can_approve_expenses_up_to", amount=30000)

    accountant = registry.get_role("finance_accountant")
    assert accountant.check_decision_authority("can_process_invoices_up_to", amount=4000)
    assert not accountant.check_decision_authority("can_process_invoices_up_to", amount=10000)


def test_legal_decision_authority():
    """Test legal role decision authority"""
    registry = RoleRegistry()

    counsel = registry.get_role("legal_counsel")
    assert counsel.check_decision_authority("can_provide_legal_opinions")
    assert counsel.check_decision_authority("can_approve_contracts_up_to", amount=50000)

    paralegal = registry.get_role("legal_paralegal")
    assert not paralegal.check_decision_authority("can_provide_legal_advice")
    assert paralegal.check_decision_authority("can_conduct_research")


# ══════════════════════════════════════════════════════════════════════
# Test Department Queries
# ══════════════════════════════════════════════════════════════════════


def test_get_roles_for_department():
    """Test getting all roles for a department"""
    registry = RoleRegistry()

    hr_roles = registry.get_roles_for_department("hr")
    assert len(hr_roles) == 3
    role_ids = [r.role_id for r in hr_roles]
    assert "hr_hiring_manager" in role_ids
    assert "hr_recruiter" in role_ids
    assert "hr_business_partner" in role_ids

    finance_roles = registry.get_roles_for_department("finance")
    assert len(finance_roles) == 3

    legal_roles = registry.get_roles_for_department("legal")
    assert len(legal_roles) == 3


def test_get_roles_by_level():
    """Test getting roles by organizational level"""
    registry = RoleRegistry()

    managers = registry.get_roles_by_level(RoleLevel.MANAGER)
    assert len(managers) >= 4  # At least HR Hiring Manager, HRBP, Finance Controller, Legal Counsel

    ics = registry.get_roles_by_level(RoleLevel.INDIVIDUAL_CONTRIBUTOR)
    assert len(ics) >= 5  # At least HR Recruiter, Staff Accountant, Financial Analyst, Paralegal, Contract Manager


# ══════════════════════════════════════════════════════════════════════
# Test Domain Router Integration
# ══════════════════════════════════════════════════════════════════════


def test_domain_router_role_selection():
    """Test that domain router can select roles"""
    # HR hiring task
    role_id, dept = select_role_for_task("Interview software engineer candidates")
    assert dept == "hr"
    assert role_id in ["hr_hiring_manager", "hr_recruiter"]

    # Finance task
    role_id, dept = select_role_for_task("Prepare quarterly financial forecast")
    assert dept == "finance"
    assert role_id in ["finance_controller", "finance_analyst", "finance_accountant"]

    # Legal task
    role_id, dept = select_role_for_task("Review vendor contract terms")
    assert dept == "legal"
    assert role_id in ["legal_counsel", "legal_contract_manager", "legal_paralegal"]


def test_domain_router_with_explicit_department():
    """Test role selection with explicit department"""
    role_id, dept = select_role_for_task(
        "Review compensation package",
        department="hr"
    )
    assert dept == "hr"
    assert role_id is not None


def test_get_role_and_domain_info():
    """Test combined domain and role information"""
    info = get_role_and_domain_info("Screen candidates for data scientist role")

    assert info["department"] == "hr"
    assert info["role_id"] is not None
    assert info["role_profile"] is not None
    assert info["role_profile"].department == "hr"


# ══════════════════════════════════════════════════════════════════════
# Test Global Registry
# ══════════════════════════════════════════════════════════════════════


def test_global_registry_singleton():
    """Test that global registry is a singleton"""
    registry1 = get_role_registry()
    registry2 = get_role_registry()

    assert registry1 is registry2
    assert registry1.roles == registry2.roles


# ══════════════════════════════════════════════════════════════════════
# Test Role Statistics
# ══════════════════════════════════════════════════════════════════════


def test_role_statistics():
    """Test role registry statistics"""
    registry = RoleRegistry()
    stats = registry.get_statistics()

    assert stats["total_roles"] == 9
    assert "hr" in stats["departments"]
    assert "finance" in stats["departments"]
    assert "legal" in stats["departments"]

    # Check level distribution
    assert "MANAGER" in stats["levels"]
    assert "INDIVIDUAL_CONTRIBUTOR" in stats["levels"]

    # Check role IDs are present
    assert "hr_hiring_manager" in stats["role_ids"]
    assert "finance_controller" in stats["role_ids"]
    assert "legal_counsel" in stats["role_ids"]


# ══════════════════════════════════════════════════════════════════════
# Test Role Serialization
# ══════════════════════════════════════════════════════════════════════


def test_role_to_dict():
    """Test role serialization to dictionary"""
    registry = RoleRegistry()
    role = registry.get_role("hr_hiring_manager")

    role_dict = role.to_dict()

    assert role_dict["role_id"] == "hr_hiring_manager"
    assert role_dict["role_name"] == "Hiring Manager"
    assert role_dict["department"] == "hr"
    assert role_dict["level"] == "MANAGER"
    assert "recruitment" in role_dict["expertise_areas"]
    assert "FILESYSTEM_WRITE" in role_dict["base_permissions"]


# ══════════════════════════════════════════════════════════════════════
# Summary Test
# ══════════════════════════════════════════════════════════════════════


def test_summary():
    """
    Summary test to verify all acceptance criteria:
    ✓ 9 roles defined across HR, Finance, Legal
    ✓ Roles loaded from JSON files
    ✓ Role-specific system prompts generated correctly
    ✓ Tool access filtered by role
    ✓ Permission enforcement works
    ✓ Decision authority checks work
    ✓ Role selection for tasks works
    ✓ Domain router integration works
    """
    registry = RoleRegistry()

    # ✓ 9 roles defined
    assert len(registry.roles) == 9

    # ✓ 3 departments
    stats = registry.get_statistics()
    assert len(stats["departments"]) == 3

    # ✓ System prompts work
    role = registry.get_role("hr_hiring_manager")
    prompt = role.build_system_prompt("Test task", {})
    assert len(prompt) > 0
    assert "Hiring Manager" in prompt

    # ✓ Tool access works
    assert role.can_use_tool("send_email")

    # ✓ Permissions work
    assert role.has_permission(Permission.EMAIL_SEND)

    # ✓ Decision authority works
    assert role.check_decision_authority("can_reject_candidates")

    # ✓ Role selection works
    selected_role_id = registry.select_role_for_task("Interview candidates", "hr")
    assert selected_role_id is not None

    # ✓ Domain router integration works
    role_id, dept = select_role_for_task("Review employment contracts")
    assert role_id is not None
    assert dept in ["hr", "legal"]

    print("\n✓ All acceptance criteria verified!")
    print(f"✓ {stats['total_roles']} roles loaded across {len(stats['departments'])} departments")
    print(f"✓ Departments: {', '.join(stats['departments'].keys())}")
    print(f"✓ Role levels: {', '.join(stats['levels'].keys())}")
