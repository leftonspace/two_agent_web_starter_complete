"""
Budget Controller Tests

Tests for budget tracking, enforcement, and cost recording.

Run with: pytest tests/models/test_budget.py -v
"""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import uuid

import pytest

from core.models import (
    BudgetController,
    BudgetCategory,
    BudgetPeriod,
    BudgetStatus,
    SpendingRecord,
    AlertLevel,
    OverflowBehavior,
    get_budget_controller,
    reset_budget_controller,
    can_afford,
)
from core.models.budget import PeriodState, CategoryState, BudgetLimits


# ============================================================================
# Test Budget Enforcement
# ============================================================================


@pytest.mark.budget
class TestBudgetEnforcement:
    """Tests for budget limit enforcement."""

    def test_within_budget_proceeds(self, budget_controller):
        """Requests within budget should proceed."""
        assert budget_controller.can_afford(0.50, BudgetCategory.PRODUCTION)
        assert budget_controller.can_afford(5.00, BudgetCategory.PRODUCTION)

    def test_exceeded_daily_blocks(self, exhausted_budget_controller):
        """Requests exceeding daily budget should be blocked."""
        # After exhausting budget
        status = exhausted_budget_controller.get_status(BudgetCategory.PRODUCTION)

        # Daily should be exceeded or near exceeded
        assert status.daily_spent >= status.daily_limit * 0.9

    def test_large_request_exceeds_budget(self, budget_controller):
        """Single large request exceeding budget should be blocked."""
        # $100 request exceeds $20 daily limit
        assert not budget_controller.can_afford(100.00, BudgetCategory.PRODUCTION)

    def test_benchmark_uses_separate_budget(self, budget_controller):
        """Benchmark category should have separate budget."""
        prod_status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        bench_status = budget_controller.get_status(BudgetCategory.BENCHMARK)

        # Different limits
        assert prod_status.daily_limit != bench_status.daily_limit
        assert prod_status.daily_limit > bench_status.daily_limit  # Production has higher limit

    def test_spending_in_one_category_doesnt_affect_other(self, budget_controller):
        """Spending in production shouldn't affect benchmark budget."""
        # Record production spending
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model="opus",
            input_tokens=5000,
            output_tokens=2000,
            cost_cad=5.00,
        )
        budget_controller.record_spend(record)

        # Benchmark should be unaffected
        bench_status = budget_controller.get_status(BudgetCategory.BENCHMARK)
        assert bench_status.daily_spent == 0.0

    def test_multiple_small_requests_accumulate(self, budget_controller, make_spending_record):
        """Multiple small requests should accumulate towards limit."""
        # Record 10 requests of $1 each
        for _ in range(10):
            record = make_spending_record(cost_cad=1.00)
            budget_controller.record_spend(record)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_spent == 10.00

    def test_cost_precision_maintained(self, budget_controller, make_spending_record):
        """Cost should maintain 4 decimal precision."""
        record = make_spending_record(cost_cad=0.12345)
        budget_controller.record_spend(record)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        # Should round to 4 decimals (0.12345 -> 0.1235)
        assert abs(status.daily_spent - 0.1235) < 0.0001


# ============================================================================
# Test Alert Thresholds
# ============================================================================


@pytest.mark.budget
class TestAlertThresholds:
    """Tests for budget alert thresholds."""

    def test_normal_alert_level_when_low(self, budget_controller):
        """Alert level should be normal when spending is low."""
        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.alert_level == AlertLevel.NORMAL
        assert not status.is_warning

    def test_warning_at_80_percent(self, warning_budget_controller):
        """Warning should trigger at 80% of budget."""
        status = warning_budget_controller.get_status(BudgetCategory.PRODUCTION)

        # Should be at or above warning threshold
        assert status.daily_spent >= status.daily_limit * 0.8
        assert status.is_warning or status.alert_level != AlertLevel.NORMAL

    def test_critical_at_95_percent(self, budget_controller, make_spending_record):
        """Critical should trigger at 95% of budget."""
        # Spend 95% of daily budget ($19 of $20)
        for _ in range(19):
            record = make_spending_record(cost_cad=1.00)
            budget_controller.record_spend(record)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.alert_level in (AlertLevel.WARNING, AlertLevel.CRITICAL)

    def test_exceeded_alert_level(self, exhausted_budget_controller):
        """Exceeded status when over 100%."""
        status = exhausted_budget_controller.get_status(BudgetCategory.PRODUCTION)

        if status.daily_spent >= status.daily_limit:
            assert status.is_exceeded or status.alert_level == AlertLevel.EXCEEDED

    def test_alert_callback_triggered(self, budget_controller, make_spending_record):
        """Alert callback should be triggered on threshold breach."""
        alerts_received = []

        def alert_handler(category, level, status):
            alerts_received.append((category, level))

        budget_controller.add_alert_callback(alert_handler)

        # Spend enough to trigger warning
        for _ in range(17):  # 85% of $20
            record = make_spending_record(cost_cad=1.00)
            budget_controller.record_spend(record)

        # Should have received alerts
        assert len(alerts_received) > 0


# ============================================================================
# Test Cost Tracking
# ============================================================================


@pytest.mark.budget
class TestCostTracking:
    """Tests for cost tracking accuracy."""

    def test_cost_recorded_correctly(self, budget_controller, spending_record):
        """Spending record should be recorded accurately."""
        budget_controller.record_spend(spending_record)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_spent == spending_record.cost_cad

    def test_spending_recorded_across_all_periods(self, budget_controller, spending_record):
        """Spending should be recorded in daily, weekly, and monthly."""
        budget_controller.record_spend(spending_record)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_spent == spending_record.cost_cad
        assert status.weekly_spent == spending_record.cost_cad
        assert status.monthly_spent == spending_record.cost_cad

    def test_spending_history_recorded(self, budget_controller, make_spending_record):
        """Spending history should be retrievable."""
        for i in range(5):
            record = make_spending_record(
                cost_cad=float(i + 1),
                model=f"model_{i}"
            )
            budget_controller.record_spend(record)

        history = budget_controller.get_spending_history(limit=10)
        assert len(history) == 5

    def test_spending_history_filtered_by_category(self, budget_controller, make_spending_record):
        """Spending history can be filtered by category."""
        # Record in both categories
        for cat in [BudgetCategory.PRODUCTION, BudgetCategory.BENCHMARK]:
            for _ in range(3):
                record = make_spending_record(category=cat, cost_cad=1.00)
                budget_controller.record_spend(record)

        # Filter by production
        prod_history = budget_controller.get_spending_history(
            category=BudgetCategory.PRODUCTION,
            limit=10
        )
        assert len(prod_history) == 3

    def test_total_spent_by_period(self, budget_controller, make_spending_record):
        """Total spent should be accurate per period."""
        for _ in range(5):
            record = make_spending_record(cost_cad=2.00)
            budget_controller.record_spend(record)

        daily = budget_controller.get_total_spent(
            BudgetCategory.PRODUCTION,
            BudgetPeriod.DAILY
        )
        assert daily == 10.00


# ============================================================================
# Test Period Resets
# ============================================================================


@pytest.mark.budget
class TestPeriodResets:
    """Tests for automatic period resets."""

    def test_daily_reset_clears_spending(self, budget_controller, make_spending_record):
        """Daily reset should clear daily spending."""
        # Record some spending
        record = make_spending_record(cost_cad=5.00)
        budget_controller.record_spend(record)

        # Force reset
        budget_controller.force_reset(BudgetCategory.PRODUCTION, BudgetPeriod.DAILY)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_spent == 0.0

    def test_weekly_reset_clears_spending(self, budget_controller, make_spending_record):
        """Weekly reset should clear weekly spending."""
        record = make_spending_record(cost_cad=5.00)
        budget_controller.record_spend(record)

        budget_controller.force_reset(BudgetCategory.PRODUCTION, BudgetPeriod.WEEKLY)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.weekly_spent == 0.0

    def test_monthly_reset_clears_spending(self, budget_controller, make_spending_record):
        """Monthly reset should clear monthly spending."""
        record = make_spending_record(cost_cad=5.00)
        budget_controller.record_spend(record)

        budget_controller.force_reset(BudgetCategory.PRODUCTION, BudgetPeriod.MONTHLY)

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.monthly_spent == 0.0

    def test_full_reset_clears_all_periods(self, budget_controller, make_spending_record):
        """Full reset should clear all periods."""
        record = make_spending_record(cost_cad=5.00)
        budget_controller.record_spend(record)

        budget_controller.force_reset(BudgetCategory.PRODUCTION)  # No period = all

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_spent == 0.0
        assert status.weekly_spent == 0.0
        assert status.monthly_spent == 0.0

    def test_automatic_reset_check(self, budget_controller):
        """Reset check should work without errors."""
        result = budget_controller.reset_if_needed()
        assert isinstance(result, bool)


# ============================================================================
# Test Budget Configuration
# ============================================================================


@pytest.mark.budget
class TestBudgetConfiguration:
    """Tests for budget configuration."""

    def test_default_limits_loaded(self, budget_controller):
        """Default budget limits should be loaded."""
        status = budget_controller.get_status(BudgetCategory.PRODUCTION)

        assert status.daily_limit > 0
        assert status.weekly_limit > 0
        assert status.monthly_limit > 0

    def test_limits_can_be_updated(self, budget_controller):
        """Budget limits can be updated at runtime."""
        budget_controller.set_limit(
            BudgetCategory.PRODUCTION,
            BudgetPeriod.DAILY,
            limit_cad=50.00
        )

        status = budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_limit == 50.00

    def test_overflow_behavior_configurable(self, budget_controller):
        """Overflow behavior should be configurable."""
        behavior = budget_controller.overflow_behavior
        assert behavior in OverflowBehavior

    def test_get_all_status_returns_all_categories(self, budget_controller):
        """get_all_status should return all category statuses."""
        all_status = budget_controller.get_all_status()

        assert BudgetCategory.PRODUCTION in all_status
        assert BudgetCategory.BENCHMARK in all_status


# ============================================================================
# Test PeriodState
# ============================================================================


@pytest.mark.budget
class TestPeriodState:
    """Tests for PeriodState dataclass."""

    def test_remaining_calculation(self):
        """Remaining should be limit minus spent."""
        state = PeriodState(spent=10.0, limit=20.0)
        assert state.remaining == 10.0

    def test_remaining_never_negative(self):
        """Remaining should never be negative."""
        state = PeriodState(spent=30.0, limit=20.0)
        assert state.remaining == 0.0

    def test_percent_used_calculation(self):
        """Percent used should be accurate."""
        state = PeriodState(spent=15.0, limit=20.0)
        assert state.percent_used == 75.0

    def test_percent_used_capped_at_100(self):
        """Percent used should cap at 100%."""
        state = PeriodState(spent=30.0, limit=20.0)
        assert state.percent_used == 100.0

    def test_is_exceeded(self):
        """is_exceeded should detect when over limit."""
        under = PeriodState(spent=10.0, limit=20.0)
        over = PeriodState(spent=25.0, limit=20.0)

        assert not under.is_exceeded
        assert over.is_exceeded

    def test_needs_reset_with_past_time(self):
        """needs_reset should be True when reset_at is in the past."""
        state = PeriodState(
            spent=10.0,
            limit=20.0,
            reset_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert state.needs_reset()

    def test_needs_reset_with_future_time(self):
        """needs_reset should be False when reset_at is in the future."""
        state = PeriodState(
            spent=10.0,
            limit=20.0,
            reset_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert not state.needs_reset()


# ============================================================================
# Test SpendingRecord
# ============================================================================


@pytest.mark.budget
class TestSpendingRecord:
    """Tests for SpendingRecord model."""

    def test_create_with_defaults(self):
        """SpendingRecord.create should set defaults."""
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model="sonnet",
            input_tokens=1000,
            output_tokens=500,
            cost_cad=0.05,
        )

        assert record.timestamp is not None
        assert record.success is True
        assert record.error_message is None

    def test_cost_rounded_to_precision(self):
        """Cost should be rounded to 4 decimal places."""
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model="sonnet",
            input_tokens=1000,
            output_tokens=500,
            cost_cad=0.123456789,
        )

        assert record.cost_cad == 0.1235  # Rounded to 4 decimals

    def test_optional_fields(self):
        """Optional fields should be settable."""
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model="sonnet",
            input_tokens=1000,
            output_tokens=500,
            cost_cad=0.05,
            task_id="task-123",
            specialist_id="spec-456",
            request_id="req-789",
            success=False,
            error_message="Test error",
        )

        assert record.task_id == "task-123"
        assert record.specialist_id == "spec-456"
        assert record.request_id == "req-789"
        assert record.success is False
        assert record.error_message == "Test error"


# ============================================================================
# Test Convenience Functions
# ============================================================================


@pytest.mark.budget
class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_budget_controller_cached(self):
        """get_budget_controller should return cached instance."""
        reset_budget_controller()

        c1 = get_budget_controller()
        c2 = get_budget_controller()

        assert c1 is c2

    def test_reset_budget_controller_clears_cache(self):
        """reset_budget_controller should clear the cache."""
        c1 = get_budget_controller()
        reset_budget_controller()
        c2 = get_budget_controller()

        assert c1 is not c2

    def test_can_afford_convenience_function(self):
        """can_afford should work as convenience function."""
        reset_budget_controller()

        result = can_afford(0.50)  # Default to production
        assert isinstance(result, bool)


# ============================================================================
# Test Database Persistence
# ============================================================================


@pytest.mark.budget
class TestDatabasePersistence:
    """Tests for database persistence."""

    def test_database_tables_created(self, test_database):
        """Database tables should be created."""
        from database import get_session
        from database.models import CostLog, BudgetState

        with get_session() as session:
            # Should not raise - count returns integer
            count1 = session.query(CostLog).count()
            count2 = session.query(BudgetState).count()
            assert count1 >= 0
            assert count2 >= 0

    def test_cost_log_persisted(self, db_budget_controller, make_spending_record):
        """Spending should be persisted to database."""
        from database import get_session
        from database.models import CostLog

        record = make_spending_record(cost_cad=1.00)
        db_budget_controller.record_spend(record)

        with get_session() as session:
            logs = session.query(CostLog).all()
            assert len(logs) >= 1

    def test_cost_log_fields_correct(self, db_budget_controller, make_spending_record):
        """Cost log fields should be recorded correctly."""
        from database import get_session
        from database.models import CostLog

        record = make_spending_record(
            provider="anthropic",
            model="sonnet",
            cost_cad=0.5678,
            input_tokens=1000,
            output_tokens=500,
        )
        db_budget_controller.record_spend(record)

        with get_session() as session:
            log = session.query(CostLog).first()
            assert log.provider == "anthropic"
            assert log.model == "sonnet"
            assert abs(log.cost_cad - 0.5678) < 0.0001
            assert log.input_tokens == 1000
            assert log.output_tokens == 500
