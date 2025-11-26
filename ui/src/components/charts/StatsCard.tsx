import React from 'react';
import { TrendingUp, TrendingDown, Minus, type LucideIcon } from 'lucide-react';

export interface StatsCardProps {
  title: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: number;
  trendLabel?: string;
  subtitle?: string;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const StatsCard: React.FC<StatsCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  trendLabel,
  subtitle,
  variant = 'default',
  size = 'md',
  loading = false,
}) => {
  const getTrendIcon = () => {
    if (trend === undefined || trend === 0) return <Minus className="trend-icon" />;
    if (trend > 0) return <TrendingUp className="trend-icon trend-up" />;
    return <TrendingDown className="trend-icon trend-down" />;
  };

  const getTrendClass = () => {
    if (trend === undefined || trend === 0) return '';
    return trend > 0 ? 'trend-positive' : 'trend-negative';
  };

  if (loading) {
    return (
      <div className={`stats-card size-${size} variant-${variant} loading`}>
        <div className="skeleton skeleton-text" style={{ width: '40%', height: '12px' }} />
        <div className="skeleton skeleton-text" style={{ width: '60%', height: '28px', marginTop: '8px' }} />
        <div className="skeleton skeleton-text" style={{ width: '30%', height: '12px', marginTop: '8px' }} />
        <style>{statsStyles}</style>
      </div>
    );
  }

  return (
    <div className={`stats-card size-${size} variant-${variant}`}>
      <div className="stats-header">
        <span className="stats-title">{title}</span>
        {Icon && (
          <div className="stats-icon">
            <Icon />
          </div>
        )}
      </div>
      <div className="stats-value">{value}</div>
      <div className="stats-footer">
        {trend !== undefined && (
          <span className={`stats-trend ${getTrendClass()}`}>
            {getTrendIcon()}
            <span>{Math.abs(trend)}%</span>
            {trendLabel && <span className="trend-label">{trendLabel}</span>}
          </span>
        )}
        {subtitle && <span className="stats-subtitle">{subtitle}</span>}
      </div>
      <style>{statsStyles}</style>
    </div>
  );
};

const statsStyles = `
  .stats-card {
    padding: var(--space-4);
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    transition: all var(--transition-fast);
  }

  .stats-card:hover {
    border-color: var(--border-secondary);
  }

  .stats-card.size-sm {
    padding: var(--space-3);
  }

  .stats-card.size-lg {
    padding: var(--space-5);
  }

  .stats-card.variant-primary {
    border-left: 3px solid var(--accent-primary);
  }

  .stats-card.variant-success {
    border-left: 3px solid var(--accent-primary);
  }

  .stats-card.variant-warning {
    border-left: 3px solid var(--accent-warning);
  }

  .stats-card.variant-danger {
    border-left: 3px solid var(--accent-danger);
  }

  .stats-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-2);
  }

  .stats-title {
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stats-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-tertiary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
  }

  .variant-primary .stats-icon {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
  }

  .variant-success .stats-icon {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
  }

  .variant-warning .stats-icon {
    background: var(--accent-warning-dim);
    color: var(--accent-warning);
  }

  .variant-danger .stats-icon {
    background: var(--accent-danger-dim);
    color: var(--accent-danger);
  }

  .stats-value {
    font-family: var(--font-mono);
    font-weight: var(--weight-bold);
    color: var(--text-primary);
  }

  .size-sm .stats-value {
    font-size: var(--text-xl);
  }

  .size-md .stats-value {
    font-size: var(--text-2xl);
  }

  .size-lg .stats-value {
    font-size: var(--text-3xl);
  }

  .stats-footer {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-2);
    font-size: var(--text-xs);
  }

  .stats-trend {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    color: var(--text-tertiary);
  }

  .stats-trend.trend-positive {
    color: var(--accent-primary);
  }

  .stats-trend.trend-negative {
    color: var(--accent-danger);
  }

  .trend-icon {
    width: 14px;
    height: 14px;
  }

  .trend-label {
    color: var(--text-tertiary);
    margin-left: var(--space-1);
  }

  .stats-subtitle {
    color: var(--text-tertiary);
  }

  .stats-card.loading {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }
`;

export interface StatsGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4;
}

export const StatsGrid: React.FC<StatsGridProps> = ({
  children,
  columns = 4,
}) => {
  return (
    <div className={`stats-grid cols-${columns}`}>
      {children}
      <style>{`
        .stats-grid {
          display: grid;
          gap: var(--space-4);
        }

        .stats-grid.cols-2 {
          grid-template-columns: repeat(2, 1fr);
        }

        .stats-grid.cols-3 {
          grid-template-columns: repeat(3, 1fr);
        }

        .stats-grid.cols-4 {
          grid-template-columns: repeat(4, 1fr);
        }

        @media (max-width: 1024px) {
          .stats-grid.cols-4 {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 640px) {
          .stats-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default StatsCard;
