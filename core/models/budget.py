"""
PHASE 7.3: Budget Controller

Manages API spending limits with separate budgets for production,
benchmark, and development workloads.

Usage:
    from core.models.budget import BudgetController, BudgetCategory

    controller = BudgetController()

    # Check if we can afford a request
    if controller.can_afford(0.05, BudgetCategory.PRODUCTION):
        # Make the API call
        ...
        # Record the spending
        controller.record_spend(SpendingRecord(...))

    # Get current status
    status = controller.get_status(BudgetCategory.PRODUCTION)
    print(f"Daily: ${status.daily_spent:.4f} / ${status.daily_limit:.2f}")
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import uuid

import yaml
from pydantic import BaseModel


# Configure logging
logger = logging.getLogger(__name__)


# Default config path
DEFAULT_BUDGET_CONFIG_PATH = "config/models/budget.yaml"

# Precision for cost calculations
COST_PRECISION = 4


# ============================================================================
# Enums
# ============================================================================


class BudgetCategory(str, Enum):
    """Budget categories for different workload types."""
    PRODUCTION = "production"
    BENCHMARK = "benchmark"
    DEVELOPMENT = "development"


class BudgetPeriod(str, Enum):
    """Budget period types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class OverflowBehavior(str, Enum):
    """What to do when budget is exceeded."""
    QUEUE = "queue"       # Queue for later
    DOWNGRADE = "downgrade"  # Try cheaper model
    REJECT = "reject"     # Reject request
    WARN = "warn"         # Allow but warn


class AlertLevel(str, Enum):
    """Alert severity levels."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


# ============================================================================
# Data Models
# ============================================================================


class BudgetStatus(BaseModel):
    """Current status of a budget category."""
    category: BudgetCategory
    daily_spent: float
    daily_limit: float
    daily_remaining: float
    weekly_spent: float
    weekly_limit: float
    weekly_remaining: float
    monthly_spent: float
    monthly_limit: float
    monthly_remaining: float
    is_exceeded: bool
    is_warning: bool
    alert_level: AlertLevel
    next_reset: datetime

    class Config:
        use_enum_values = True


class SpendingRecord(BaseModel):
    """Record of a single API call spending."""
    timestamp: datetime
    category: BudgetCategory
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_cad: float
    task_id: Optional[str] = None
    specialist_id: Optional[str] = None
    request_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True

    @classmethod
    def create(
        cls,
        category: BudgetCategory,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_cad: float,
        **kwargs
    ) -> "SpendingRecord":
        """Create a spending record with current timestamp."""
        return cls(
            timestamp=datetime.utcnow(),
            category=category,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cad=round(cost_cad, COST_PRECISION),
            **kwargs
        )


@dataclass
class BudgetLimits:
    """Budget limits for a category."""
    daily_cad: float
    weekly_cad: float
    monthly_cad: float


# ============================================================================
# In-Memory Budget State (for non-database use)
# ============================================================================


@dataclass
class PeriodState:
    """State for a single budget period."""
    spent: float = 0.0
    limit: float = 0.0
    reset_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.reset_at is None:
            self.reset_at = datetime.utcnow()

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.spent)

    @property
    def percent_used(self) -> float:
        if self.limit <= 0:
            return 100.0
        return min(100.0, (self.spent / self.limit) * 100)

    @property
    def is_exceeded(self) -> bool:
        return self.spent >= self.limit

    def needs_reset(self) -> bool:
        if self.reset_at is None:
            return False
        return datetime.utcnow() >= self.reset_at


class CategoryState:
    """Budget state for a category across all periods."""

    def __init__(self, category: BudgetCategory, limits: BudgetLimits):
        self.category = category
        self.limits = limits
        now = datetime.utcnow()

        self.daily = PeriodState(
            limit=limits.daily_cad,
            reset_at=self._next_daily_reset(now),
        )
        self.weekly = PeriodState(
            limit=limits.weekly_cad,
            reset_at=self._next_weekly_reset(now),
        )
        self.monthly = PeriodState(
            limit=limits.monthly_cad,
            reset_at=self._next_monthly_reset(now),
        )

    def _next_daily_reset(self, now: datetime) -> datetime:
        """Calculate next daily reset time."""
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return tomorrow

    def _next_weekly_reset(self, now: datetime) -> datetime:
        """Calculate next weekly reset time (Monday)."""
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        return next_monday

    def _next_monthly_reset(self, now: datetime) -> datetime:
        """Calculate next monthly reset time (1st of month)."""
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return next_month

    def reset_if_needed(self) -> bool:
        """Reset periods that have passed their reset time."""
        now = datetime.utcnow()
        reset_occurred = False

        if self.daily.needs_reset():
            self.daily.spent = 0.0
            self.daily.reset_at = self._next_daily_reset(now)
            reset_occurred = True
            logger.info(f"Reset daily budget for {self.category.value}")

        if self.weekly.needs_reset():
            self.weekly.spent = 0.0
            self.weekly.reset_at = self._next_weekly_reset(now)
            reset_occurred = True
            logger.info(f"Reset weekly budget for {self.category.value}")

        if self.monthly.needs_reset():
            self.monthly.spent = 0.0
            self.monthly.reset_at = self._next_monthly_reset(now)
            reset_occurred = True
            logger.info(f"Reset monthly budget for {self.category.value}")

        return reset_occurred

    def add_spending(self, amount: float) -> None:
        """Add spending to all periods."""
        amount = round(amount, COST_PRECISION)
        self.daily.spent = round(self.daily.spent + amount, COST_PRECISION)
        self.weekly.spent = round(self.weekly.spent + amount, COST_PRECISION)
        self.monthly.spent = round(self.monthly.spent + amount, COST_PRECISION)

    def can_afford(self, amount: float) -> bool:
        """Check if all periods can afford the amount."""
        return (
            self.daily.remaining >= amount and
            self.weekly.remaining >= amount and
            self.monthly.remaining >= amount
        )

    def get_alert_level(self, warn_percent: float, critical_percent: float) -> AlertLevel:
        """Get highest alert level across all periods."""
        max_percent = max(
            self.daily.percent_used,
            self.weekly.percent_used,
            self.monthly.percent_used,
        )

        if max_percent >= 100:
            return AlertLevel.EXCEEDED
        elif max_percent >= critical_percent:
            return AlertLevel.CRITICAL
        elif max_percent >= warn_percent:
            return AlertLevel.WARNING
        return AlertLevel.NORMAL


# ============================================================================
# Budget Controller
# ============================================================================


class BudgetController:
    """
    Manage API spending limits.

    Tracks spending across multiple categories (production, benchmark, development)
    with daily, weekly, and monthly limits. Supports automatic period resets
    and configurable overflow behavior.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        use_database: bool = False,
    ):
        """
        Initialize budget controller.

        Args:
            config_path: Path to budget YAML config
            use_database: Whether to persist to database (False = in-memory)
        """
        self._use_database = use_database
        self._config = self._load_config(config_path)
        self._state: Dict[BudgetCategory, CategoryState] = {}
        self._spending_log: List[SpendingRecord] = []
        self._alert_callbacks: List[Callable[[BudgetCategory, AlertLevel, BudgetStatus], None]] = []

        # Initialize state for each category
        self._initialize_state()

    def _load_config(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Load budget configuration."""
        if path is None:
            path = self._find_config_path()

        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Budget config not found: {path}, using defaults")
            return self._default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing budget config: {e}")
            return self._default_config()

    def _find_config_path(self) -> str:
        """Find config file path."""
        candidates = [
            DEFAULT_BUDGET_CONFIG_PATH,
            f"../{DEFAULT_BUDGET_CONFIG_PATH}",
            str(Path(__file__).parent.parent.parent / DEFAULT_BUDGET_CONFIG_PATH),
        ]

        for candidate in candidates:
            if Path(candidate).exists():
                return candidate

        return DEFAULT_BUDGET_CONFIG_PATH

    def _default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            "budgets": {
                "production": {
                    "daily_cad": 20.0,
                    "weekly_cad": 100.0,
                    "monthly_cad": 300.0,
                },
                "benchmark": {
                    "daily_cad": 5.0,
                    "weekly_cad": 25.0,
                    "monthly_cad": 75.0,
                },
                "development": {
                    "daily_cad": 10.0,
                    "weekly_cad": 50.0,
                    "monthly_cad": 150.0,
                },
            },
            "overflow_behavior": "downgrade",
            "alerts": {
                "warn_percent": 80,
                "critical_percent": 95,
            },
        }

    def _initialize_state(self) -> None:
        """Initialize budget state for all categories."""
        budgets = self._config.get("budgets", {})

        for category in BudgetCategory:
            if category.value in budgets:
                limits_data = budgets[category.value]
                limits = BudgetLimits(
                    daily_cad=limits_data.get("daily_cad", 0),
                    weekly_cad=limits_data.get("weekly_cad", 0),
                    monthly_cad=limits_data.get("monthly_cad", 0),
                )
                self._state[category] = CategoryState(category, limits)

    @property
    def overflow_behavior(self) -> OverflowBehavior:
        """Get configured overflow behavior."""
        behavior = self._config.get("overflow_behavior", "downgrade")
        return OverflowBehavior(behavior)

    @property
    def warn_percent(self) -> float:
        """Get warning threshold percentage."""
        return self._config.get("alerts", {}).get("warn_percent", 80)

    @property
    def critical_percent(self) -> float:
        """Get critical threshold percentage."""
        return self._config.get("alerts", {}).get("critical_percent", 95)

    def can_afford(
        self,
        estimated_cost: float,
        category: BudgetCategory = BudgetCategory.PRODUCTION,
    ) -> bool:
        """
        Check if budget allows this cost.

        Args:
            estimated_cost: Estimated cost in CAD
            category: Budget category

        Returns:
            True if cost is within all budget limits
        """
        # Reset if needed first
        self.reset_if_needed()

        if category not in self._state:
            logger.warning(f"Unknown budget category: {category}")
            return True  # Allow if category not configured

        return self._state[category].can_afford(estimated_cost)

    def record_spend(self, record: SpendingRecord) -> None:
        """
        Record spending from an API call.

        Args:
            record: Spending record with cost details
        """
        category = BudgetCategory(record.category) if isinstance(record.category, str) else record.category

        # Reset if needed first
        self.reset_if_needed()

        # Add to state
        if category in self._state:
            self._state[category].add_spending(record.cost_cad)

        # Log spending
        self._spending_log.append(record)

        # Check for alerts
        self._check_alerts(category)

        # Persist to database if enabled
        if self._use_database:
            self._persist_to_database(record)

        logger.debug(
            f"Recorded spend: {record.provider}:{record.model} "
            f"${record.cost_cad:.4f} CAD ({category.value})"
        )

    def _persist_to_database(self, record: SpendingRecord) -> None:
        """Persist spending record to database."""
        try:
            from database import get_session
            from database.models import CostLog

            with get_session() as session:
                log = CostLog.create(
                    category=record.category if isinstance(record.category, str) else record.category.value,
                    provider=record.provider,
                    model=record.model,
                    input_tokens=record.input_tokens,
                    output_tokens=record.output_tokens,
                    cost_cad=record.cost_cad,
                    task_id=uuid.UUID(record.task_id) if record.task_id else None,
                    specialist_id=uuid.UUID(record.specialist_id) if record.specialist_id else None,
                    request_id=record.request_id,
                    success=record.success,
                    error_message=record.error_message,
                )
                session.add(log)
        except Exception as e:
            logger.error(f"Failed to persist spending to database: {e}")

    def get_status(self, category: BudgetCategory) -> BudgetStatus:
        """
        Get current budget status for a category.

        Args:
            category: Budget category

        Returns:
            BudgetStatus with current spending and limits
        """
        # Reset if needed first
        self.reset_if_needed()

        if category not in self._state:
            raise ValueError(f"Unknown budget category: {category}")

        state = self._state[category]
        alert_level = state.get_alert_level(self.warn_percent, self.critical_percent)

        return BudgetStatus(
            category=category,
            daily_spent=state.daily.spent,
            daily_limit=state.daily.limit,
            daily_remaining=state.daily.remaining,
            weekly_spent=state.weekly.spent,
            weekly_limit=state.weekly.limit,
            weekly_remaining=state.weekly.remaining,
            monthly_spent=state.monthly.spent,
            monthly_limit=state.monthly.limit,
            monthly_remaining=state.monthly.remaining,
            is_exceeded=not state.can_afford(0),
            is_warning=alert_level in (AlertLevel.WARNING, AlertLevel.CRITICAL),
            alert_level=alert_level,
            next_reset=state.daily.reset_at or datetime.utcnow(),
        )

    def get_all_status(self) -> Dict[BudgetCategory, BudgetStatus]:
        """
        Get status for all budget categories.

        Returns:
            Dict mapping categories to their status
        """
        return {
            category: self.get_status(category)
            for category in self._state.keys()
        }

    def reset_if_needed(self) -> bool:
        """
        Reset any periods that have passed their reset time.

        Returns:
            True if any resets occurred
        """
        reset_occurred = False
        for category, state in self._state.items():
            if state.reset_if_needed():
                reset_occurred = True
        return reset_occurred

    def force_reset(
        self,
        category: BudgetCategory,
        period: Optional[BudgetPeriod] = None,
    ) -> None:
        """
        Force reset a budget (admin action).

        Args:
            category: Category to reset
            period: Specific period to reset (None = all)
        """
        if category not in self._state:
            return

        state = self._state[category]
        now = datetime.utcnow()

        if period is None or period == BudgetPeriod.DAILY:
            state.daily.spent = 0.0
            state.daily.reset_at = state._next_daily_reset(now)

        if period is None or period == BudgetPeriod.WEEKLY:
            state.weekly.spent = 0.0
            state.weekly.reset_at = state._next_weekly_reset(now)

        if period is None or period == BudgetPeriod.MONTHLY:
            state.monthly.spent = 0.0
            state.monthly.reset_at = state._next_monthly_reset(now)

        logger.info(f"Force reset budget: {category.value} {period.value if period else 'all'}")

    def set_limit(
        self,
        category: BudgetCategory,
        period: BudgetPeriod,
        limit_cad: float,
    ) -> None:
        """
        Update a budget limit.

        Args:
            category: Category to update
            period: Period to update
            limit_cad: New limit in CAD
        """
        if category not in self._state:
            return

        state = self._state[category]

        if period == BudgetPeriod.DAILY:
            state.daily.limit = limit_cad
            state.limits.daily_cad = limit_cad
        elif period == BudgetPeriod.WEEKLY:
            state.weekly.limit = limit_cad
            state.limits.weekly_cad = limit_cad
        elif period == BudgetPeriod.MONTHLY:
            state.monthly.limit = limit_cad
            state.limits.monthly_cad = limit_cad

        logger.info(f"Updated limit: {category.value} {period.value} = ${limit_cad:.2f}")

    def add_alert_callback(
        self,
        callback: Callable[[BudgetCategory, AlertLevel, BudgetStatus], None],
    ) -> None:
        """
        Register a callback for budget alerts.

        Args:
            callback: Function called when alert level changes
        """
        self._alert_callbacks.append(callback)

    def _check_alerts(self, category: BudgetCategory) -> None:
        """Check and trigger alerts if needed."""
        if category not in self._state:
            return

        status = self.get_status(category)

        if status.alert_level != AlertLevel.NORMAL:
            for callback in self._alert_callbacks:
                try:
                    callback(category, status.alert_level, status)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

    def get_spending_history(
        self,
        category: Optional[BudgetCategory] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SpendingRecord]:
        """
        Get spending history.

        Args:
            category: Filter by category (None = all)
            since: Filter by timestamp
            limit: Maximum records to return

        Returns:
            List of spending records
        """
        records = self._spending_log

        if category:
            records = [r for r in records if r.category == category.value]

        if since:
            records = [r for r in records if r.timestamp >= since]

        # Sort by timestamp descending
        records = sorted(records, key=lambda r: r.timestamp, reverse=True)

        return records[:limit]

    def get_total_spent(
        self,
        category: BudgetCategory,
        period: BudgetPeriod,
    ) -> float:
        """Get total spent for a category and period."""
        if category not in self._state:
            return 0.0

        state = self._state[category]

        if period == BudgetPeriod.DAILY:
            return state.daily.spent
        elif period == BudgetPeriod.WEEKLY:
            return state.weekly.spent
        elif period == BudgetPeriod.MONTHLY:
            return state.monthly.spent

        return 0.0


# ============================================================================
# Convenience Functions
# ============================================================================


# Module-level cache
_controller_cache: Optional[BudgetController] = None


def get_budget_controller(
    config_path: Optional[str] = None,
    use_database: bool = False,
) -> BudgetController:
    """
    Get budget controller (cached).

    Args:
        config_path: Path to config file
        use_database: Whether to persist to database

    Returns:
        BudgetController instance
    """
    global _controller_cache

    if _controller_cache is None:
        _controller_cache = BudgetController(config_path, use_database)

    return _controller_cache


def reset_budget_controller() -> None:
    """Reset cached budget controller."""
    global _controller_cache
    _controller_cache = None


def can_afford(
    estimated_cost: float,
    category: BudgetCategory = BudgetCategory.PRODUCTION,
) -> bool:
    """
    Quick check if budget allows this cost.

    Args:
        estimated_cost: Estimated cost in CAD
        category: Budget category

    Returns:
        True if affordable
    """
    return get_budget_controller().can_afford(estimated_cost, category)
