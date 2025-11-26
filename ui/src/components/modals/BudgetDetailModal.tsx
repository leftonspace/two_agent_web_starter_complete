import React from 'react';
import { Wallet, TrendingUp, TrendingDown, Calendar, DollarSign, Clock, AlertTriangle } from 'lucide-react';
import type { BudgetStatus, BudgetHistory } from '../../types';
import { Modal, ProgressBar } from '../common';

export interface BudgetDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  budget?: BudgetStatus;
  history?: BudgetHistory[];
  onUpdateLimit?: (newLimit: number) => void;
}

export const BudgetDetailModal: React.FC<BudgetDetailModalProps> = ({
  isOpen,
  onClose,
  budget,
  history = [],
  onUpdateLimit,
}) => {
  if (!budget) return null;

  const usedPercentage = (budget.used / budget.daily_limit) * 100;
  const isLow = budget.remaining < budget.daily_limit * 0.2;
  const isCritical = budget.remaining < budget.daily_limit * 0.1;

  const getStatusColor = () => {
    if (isCritical) return 'var(--accent-danger)';
    if (isLow) return 'var(--accent-warning)';
    return 'var(--accent-primary)';
  };

  const formatCurrency = (amount: number) => `$${amount.toFixed(2)}`;

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Budget Details" size="lg">
      <div className="budget-detail">
        {/* Main Budget Display */}
        <div className="budget-main">
          <div className="budget-icon" style={{ background: `${getStatusColor()}20` }}>
            <Wallet className="icon-lg" style={{ color: getStatusColor() }} />
          </div>
          <div className="budget-info">
            <div className="budget-amounts">
              <span className="amount-used">{formatCurrency(budget.used)}</span>
              <span className="amount-separator">/</span>
              <span className="amount-limit">{formatCurrency(budget.daily_limit)}</span>
            </div>
            <div className="budget-label">Daily Budget Usage</div>
          </div>
          {(isLow || isCritical) && (
            <div className="budget-warning">
              <AlertTriangle className="icon" style={{ color: getStatusColor() }} />
              <span style={{ color: getStatusColor() }}>
                {isCritical ? 'Critical' : 'Low'} budget
              </span>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="budget-progress-section">
          <ProgressBar
            value={usedPercentage}
            size="lg"
            variant={isCritical ? 'danger' : isLow ? 'warning' : 'primary'}
          />
          <div className="progress-labels">
            <span>0%</span>
            <span className="remaining-text">
              <span style={{ color: getStatusColor() }}>
                {formatCurrency(budget.remaining)}
              </span>
              {' '}remaining
            </span>
            <span>100%</span>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="stats-row">
          <div className="stat-card">
            <DollarSign className="icon" />
            <div>
              <div className="stat-value">{formatCurrency(budget.used)}</div>
              <div className="stat-label">Spent Today</div>
            </div>
          </div>
          <div className="stat-card">
            <Clock className="icon" />
            <div>
              <div className="stat-value">{budget.reset_time || '00:00 UTC'}</div>
              <div className="stat-label">Reset Time</div>
            </div>
          </div>
          {budget.trend !== undefined && (
            <div className="stat-card">
              {budget.trend > 0 ? (
                <TrendingUp className="icon" style={{ color: 'var(--accent-danger)' }} />
              ) : (
                <TrendingDown className="icon" style={{ color: 'var(--accent-primary)' }} />
              )}
              <div>
                <div className="stat-value">{Math.abs(budget.trend)}%</div>
                <div className="stat-label">
                  {budget.trend > 0 ? 'Increase' : 'Decrease'} vs avg
                </div>
              </div>
            </div>
          )}
        </div>

        {/* History */}
        {history.length > 0 && (
          <div className="budget-history">
            <h4 className="section-title">Recent History</h4>
            <div className="history-list">
              {history.slice(0, 7).map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-date">
                    <Calendar className="icon-xs" />
                    {formatDate(item.date)}
                  </div>
                  <div className="history-bar">
                    <div
                      className="history-fill"
                      style={{
                        width: `${(item.used / budget.daily_limit) * 100}%`,
                        background: item.used > budget.daily_limit
                          ? 'var(--accent-danger)'
                          : 'var(--accent-primary)',
                      }}
                    />
                  </div>
                  <div className="history-amount">{formatCurrency(item.used)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Update Limit Section */}
        {onUpdateLimit && (
          <div className="budget-settings">
            <h4 className="section-title">Budget Settings</h4>
            <div className="settings-row">
              <label className="settings-label">Daily Limit</label>
              <div className="limit-options">
                {[5, 10, 20, 50].map((limit) => (
                  <button
                    key={limit}
                    className={`limit-option ${budget.daily_limit === limit ? 'active' : ''}`}
                    onClick={() => onUpdateLimit(limit)}
                  >
                    ${limit}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .budget-detail {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .budget-main {
          display: flex;
          align-items: center;
          gap: var(--space-4);
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .budget-icon {
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-lg);
        }

        .budget-info {
          flex: 1;
        }

        .budget-amounts {
          font-family: var(--font-mono);
          font-size: var(--text-2xl);
          font-weight: var(--weight-bold);
        }

        .amount-used {
          color: var(--text-primary);
        }

        .amount-separator {
          color: var(--text-tertiary);
          margin: 0 var(--space-2);
        }

        .amount-limit {
          color: var(--text-secondary);
        }

        .budget-label {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          margin-top: var(--space-1);
        }

        .budget-warning {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2) var(--space-3);
          background: var(--bg-secondary);
          border-radius: var(--radius-md);
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
        }

        .budget-progress-section {
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .progress-labels {
          display: flex;
          justify-content: space-between;
          margin-top: var(--space-2);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .remaining-text {
          color: var(--text-secondary);
        }

        .stats-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-3);
        }

        .stat-card {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .stat-card .icon {
          color: var(--text-tertiary);
        }

        .stat-value {
          font-size: var(--text-md);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .budget-history {
          border-top: 1px solid var(--border-primary);
          padding-top: var(--space-4);
        }

        .section-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-3);
        }

        .history-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .history-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
        }

        .history-date {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          min-width: 70px;
        }

        .history-bar {
          flex: 1;
          height: 8px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
          overflow: hidden;
        }

        .history-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width var(--transition-normal);
        }

        .history-amount {
          font-family: var(--font-mono);
          font-size: var(--text-xs);
          color: var(--text-secondary);
          min-width: 50px;
          text-align: right;
        }

        .budget-settings {
          border-top: 1px solid var(--border-primary);
          padding-top: var(--space-4);
        }

        .settings-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .settings-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .limit-options {
          display: flex;
          gap: var(--space-2);
        }

        .limit-option {
          padding: var(--space-2) var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .limit-option:hover {
          border-color: var(--border-secondary);
          color: var(--text-primary);
        }

        .limit-option.active {
          background: var(--accent-primary-dim);
          border-color: var(--accent-primary);
          color: var(--accent-primary);
        }
      `}</style>
    </Modal>
  );
};

export default BudgetDetailModal;
