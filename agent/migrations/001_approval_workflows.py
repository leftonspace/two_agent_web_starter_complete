#!/usr/bin/env python3
"""
Database Migration: Approval Workflows

This migration creates the approval workflow tables and registers default workflows.

Usage:
    python migrations/001_approval_workflows.py

Author: AI Agent System
Created: Phase 3.1 - Approval Workflows
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from approval_engine import (
    ApprovalEngine,
    create_hr_offer_letter_workflow,
    create_finance_expense_workflow,
    create_legal_contract_workflow
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_migration():
    """Run the approval workflow migration"""
    logger.info("=" * 80)
    logger.info("Starting Approval Workflow Migration")
    logger.info("=" * 80)

    # Initialize engine (this will create tables if they don't exist)
    logger.info("\n1. Initializing Approval Engine...")
    engine = ApprovalEngine()
    logger.info("   ✓ Schema created/verified")

    # Register default workflows
    logger.info("\n2. Registering default workflows...")

    workflows = [
        ("HR Offer Letter", create_hr_offer_letter_workflow()),
        ("Finance Expense Approval", create_finance_expense_workflow()),
        ("Legal Contract Review", create_legal_contract_workflow())
    ]

    for name, workflow in workflows:
        logger.info(f"   Registering: {name}")
        success = engine.register_workflow(workflow)
        if success:
            logger.info(f"   ✓ {name} registered successfully")
        else:
            logger.error(f"   ✗ Failed to register {name}")

    # Verify workflows
    logger.info("\n3. Verifying registered workflows...")
    for name, workflow in workflows:
        loaded = engine.get_workflow(workflow.workflow_id)
        if loaded:
            logger.info(f"   ✓ {name}: {len(loaded.steps)} steps")
            for i, step in enumerate(loaded.steps, 1):
                logger.info(f"      Step {i}: {step.step_name} ({step.approver_role})")
                if step.condition:
                    logger.info(f"              Condition: {step.condition}")
                if step.parallel:
                    logger.info(f"              Parallel: Yes")
        else:
            logger.error(f"   ✗ Failed to load {name}")

    # Show statistics
    logger.info("\n4. Workflow Statistics...")
    for domain in ['hr', 'finance', 'legal']:
        stats = engine.get_statistics(domain=domain)
        logger.info(f"   {domain.upper()}: {stats['total_requests']} total requests")

    logger.info("\n" + "=" * 80)
    logger.info("Migration Complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
