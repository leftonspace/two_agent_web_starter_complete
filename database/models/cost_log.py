"""
Cost Logging Database Models

Tracks API spending for budget enforcement.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Index,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR


from database.base import Base


# ============================================================================
# Custom Types
# ============================================================================


class UUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36).
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


# ============================================================================
# Cost Log Model
# ============================================================================


class CostLog(Base):
    """
    Log of individual API calls and their costs.

    Used for:
    - Detailed cost tracking
    - Budget enforcement
    - Usage analytics
    - Audit trail
    """

    __tablename__ = "cost_log"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Category (production, benchmark, development)
    category = Column(String(20), nullable=False, index=True)

    # Provider info
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)

    # Token counts
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)

    # Cost in CAD (4 decimal precision)
    cost_cad = Column(Float, nullable=False, default=0.0)

    # Optional context
    task_id = Column(UUID, nullable=True, index=True)
    specialist_id = Column(UUID, nullable=True)
    request_id = Column(String(64), nullable=True)

    # Metadata
    success = Column(Boolean, default=True)
    error_message = Column(String(500), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_cost_log_category_timestamp", "category", "timestamp"),
        Index("ix_cost_log_provider_model", "provider", "model"),
    )

    def __repr__(self) -> str:
        return (
            f"<CostLog(id={self.id}, category={self.category}, "
            f"model={self.model}, cost_cad={self.cost_cad:.4f})>"
        )

    @classmethod
    def create(
        cls,
        category: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_cad: float,
        task_id: Optional[uuid.UUID] = None,
        specialist_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> "CostLog":
        """Create a new cost log entry."""
        return cls(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            category=category,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cad=round(cost_cad, 4),
            task_id=task_id,
            specialist_id=specialist_id,
            request_id=request_id,
            success=success,
            error_message=error_message,
        )


# ============================================================================
# Budget State Model
# ============================================================================


class BudgetState(Base):
    """
    Current state of budget spending for each category and period.

    Keys are formatted as: "{category}_{period}"
    Examples: "production_daily", "benchmark_weekly", "development_monthly"
    """

    __tablename__ = "budget_state"

    # Primary key (e.g., "production_daily")
    id = Column(String(50), primary_key=True)

    # Current spending
    spent_cad = Column(Float, default=0.0, nullable=False)

    # Limit for this period
    limit_cad = Column(Float, nullable=False)

    # When this period resets
    reset_at = Column(DateTime, nullable=False)

    # Last update timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<BudgetState(id={self.id}, spent={self.spent_cad:.4f}, "
            f"limit={self.limit_cad:.2f}, reset_at={self.reset_at})>"
        )

    @property
    def remaining(self) -> float:
        """Get remaining budget."""
        diff = float(self.limit_cad) - float(self.spent_cad)
        return max(0.0, diff)

    @property
    def percent_used(self) -> float:
        """Get percentage of budget used."""
        if self.limit_cad <= 0:
            return 100.0
        pct = (float(self.spent_cad) / float(self.limit_cad)) * 100
        return min(100.0, pct)

    @property
    def is_exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return bool(self.spent_cad >= self.limit_cad)

    def needs_reset(self) -> bool:
        """Check if this budget period needs to be reset."""
        return bool(datetime.utcnow() >= self.reset_at)

    @classmethod
    def create(
        cls,
        category: str,
        period: str,
        limit_cad: float,
        reset_at: datetime,
    ) -> "BudgetState":
        """Create a new budget state entry."""
        return cls(
            id=f"{category}_{period}",
            spent_cad=0.0,
            limit_cad=limit_cad,
            reset_at=reset_at,
            updated_at=datetime.utcnow(),
        )


# ============================================================================
# Aggregate Cost Model (for historical data)
# ============================================================================


class CostAggregate(Base):
    """
    Aggregated cost data for historical analysis.

    After retention period, detailed logs are aggregated into this table.
    """

    __tablename__ = "cost_aggregate"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid.uuid4)

    # Period info
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly

    # Category
    category = Column(String(20), nullable=False, index=True)

    # Aggregated data
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)

    # Totals
    request_count = Column(Integer, nullable=False, default=0)
    total_input_tokens = Column(Integer, nullable=False, default=0)
    total_output_tokens = Column(Integer, nullable=False, default=0)
    total_cost_cad = Column(Float, nullable=False, default=0.0)

    # Success/failure counts
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_cost_aggregate_date_category", "date", "category"),
    )

    def __repr__(self) -> str:
        return (
            f"<CostAggregate(date={self.date}, category={self.category}, "
            f"total_cost={self.total_cost_cad:.2f})>"
        )
