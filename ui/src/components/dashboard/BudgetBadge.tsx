import React from 'react';
import { Wallet, TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import type { BudgetStatus } from '../../types';
import { ProgressBar } from '../common';

export interface BudgetBadgeProps {
  budget?: BudgetStatus;
  onClick?: () => void;
  compact?: boolean;
}

export const BudgetBadge: React.FC<BudgetBadgeProps> = ({
  budget,
  onClick,
  compact = false,
}) => {
  if (!budget) {
    return (
      <div className={`budget-badge loading ${compact ? 'compact' : ''}`}>
        <div className="skeleton skeleton-text" style={{ width: '60px' }} />
        <style>{budgetStyles}</style>
      </div>
    );
  }

  const usedPercentage = (budget.used / budget.daily_limit) * 100;
  const isLow = budget.remaining < budget.daily_limit * 0.2;
  const isCritical = budget.remaining < budget.daily_limit * 0.1;

  const getStatusColor = () => {
    if (isCritical) return 'var(--accent-danger)';
    if (isLow) return 'var(--accent-warning)';
    return 'var(--accent-primary)';
  };

  const formatCurrency = (amount: number) => {
    return `$${amount.toFixed(2)}`;
  };

  if (compact) {
    return (
      <div
        className={`budget-badge compact ${onClick ? 'clickable' : ''}`}
        onClick={onClick}
        role={onClick ? 'button' : undefined}
        tabIndex={onClick ? 0 : undefined}
      >
        <Wallet className="icon-sm" style={{ color: getStatusColor() }} />
        <span className="budget-amount" style={{ color: getStatusColor() }}>
          {formatCurrency(budget.remaining)}
        </span>
        {isCritical && <AlertTriangle className="icon-xs warning-icon" />}
        <style>{budgetStyles}</style>
      </div>
    );
  }

  return (
    <div
      className={`budget-badge ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div className="budget-header">
        <div className="budget-icon">
          <Wallet className="icon" style={{ color: getStatusColor() }} />
        </div>
        <div className="budget-info">
          <div className="budget-label">Daily Budget</div>
          <div className="budget-amounts">
            <span className="budget-used">{formatCurrency(budget.used)}</span>
            <span className="budget-separator">/</span>
            <span className="budget-limit">{formatCurrency(budget.daily_limit)}</span>
          </div>
        </div>
        {(isLow || isCritical) && (
          <AlertTriangle
            className="icon warning-icon"
            style={{ color: getStatusColor() }}
          />
        )}
      </div>

      <ProgressBar
        value={usedPercentage}
        size="sm"
        variant={isCritical ? 'danger' : isLow ? 'warning' : 'primary'}
      />

      <div className="budget-footer">
        <span className="budget-remaining">
          <span style={{ color: getStatusColor() }}>
            {formatCurrency(budget.remaining)}
          </span>
          {' '}remaining
        </span>
        {budget.trend !== undefined && (
          <span className={`budget-trend ${budget.trend > 0 ? 'up' : 'down'}`}>
            {budget.trend > 0 ? (
              <TrendingUp className="icon-xs" />
            ) : (
              <TrendingDown className="icon-xs" />
            )}
            {Math.abs(budget.trend)}%
          </span>
        )}
      </div>

      <style>{budgetStyles}</style>
    </div>
  );
};

const budgetStyles = `
  .budget-badge {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
  }

  .budget-badge.clickable {
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .budget-badge.clickable:hover {
    border-color: var(--border-secondary);
  }

  .budget-badge.compact {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-full);
    background: var(--bg-tertiary);
  }

  .budget-badge.compact .budget-amount {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
  }

  .budget-badge.loading {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .budget-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    margin-bottom: var(--space-3);
  }

  .budget-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
  }

  .budget-info {
    flex: 1;
  }

  .budget-label {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .budget-amounts {
    font-family: var(--font-mono);
    font-size: var(--text-lg);
    font-weight: var(--weight-bold);
  }

  .budget-used {
    color: var(--text-primary);
  }

  .budget-separator {
    color: var(--text-tertiary);
    margin: 0 var(--space-1);
  }

  .budget-limit {
    color: var(--text-secondary);
  }

  .warning-icon {
    animation: pulse 2s ease-in-out infinite;
  }

  .budget-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--space-3);
    font-size: var(--text-sm);
  }

  .budget-remaining {
    color: var(--text-secondary);
  }

  .budget-trend {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    font-weight: var(--weight-medium);
  }

  .budget-trend.up {
    color: var(--accent-danger);
  }

  .budget-trend.down {
    color: var(--accent-primary);
  }
`;

export default BudgetBadge;
