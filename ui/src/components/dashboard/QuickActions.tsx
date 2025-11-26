import React from 'react';
import { Play, Zap, Plus, RefreshCw, type LucideIcon } from 'lucide-react';
import { Button } from '../common';

export interface QuickAction {
  id: string;
  label: string;
  icon: LucideIcon;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'warning';
  disabled?: boolean;
  loading?: boolean;
}

export interface QuickActionsProps {
  actions?: QuickAction[];
  onRunBenchmark?: () => void;
  onForceEvolution?: () => void;
  onNewTask?: () => void;
  onRefreshAll?: () => void;
  onOpenSettings?: () => void;
  onViewLogs?: () => void;
  loading?: boolean;
  layout?: 'horizontal' | 'vertical' | 'grid';
}

const defaultActions = (props: QuickActionsProps): QuickAction[] => [
  {
    id: 'benchmark',
    label: 'Run Benchmark',
    icon: Play,
    onClick: () => props.onRunBenchmark?.(),
    variant: 'primary',
  },
  {
    id: 'evolution',
    label: 'Force Evolution',
    icon: Zap,
    onClick: () => props.onForceEvolution?.(),
    variant: 'secondary',
  },
  {
    id: 'new-task',
    label: 'New Task',
    icon: Plus,
    onClick: () => props.onNewTask?.(),
    variant: 'ghost',
  },
  {
    id: 'refresh',
    label: 'Refresh All',
    icon: RefreshCw,
    onClick: () => props.onRefreshAll?.(),
    variant: 'ghost',
  },
];

export const QuickActions: React.FC<QuickActionsProps> = (props) => {
  const {
    actions,
    loading = false,
    layout = 'horizontal',
  } = props;

  const actionList = actions || defaultActions(props);

  return (
    <div className={`quick-actions layout-${layout}`}>
      {actionList.map((action) => (
        <Button
          key={action.id}
          variant={action.variant || 'ghost'}
          size="md"
          icon={action.icon}
          onClick={action.onClick}
          disabled={action.disabled || loading}
          loading={action.loading}
          className="quick-action-btn"
        >
          {action.label}
        </Button>
      ))}

      <style>{`
        .quick-actions {
          display: flex;
          gap: var(--space-2);
        }

        .quick-actions.layout-horizontal {
          flex-direction: row;
          flex-wrap: wrap;
        }

        .quick-actions.layout-vertical {
          flex-direction: column;
        }

        .quick-actions.layout-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        }

        .quick-action-btn {
          justify-content: flex-start;
        }

        .quick-actions.layout-grid .quick-action-btn {
          justify-content: center;
        }
      `}</style>
    </div>
  );
};

export interface QuickActionCardProps {
  title: string;
  description?: string;
  icon: LucideIcon;
  onClick: () => void;
  variant?: 'default' | 'primary' | 'warning' | 'danger';
  disabled?: boolean;
  loading?: boolean;
}

export const QuickActionCard: React.FC<QuickActionCardProps> = ({
  title,
  description,
  icon: Icon,
  onClick,
  variant = 'default',
  disabled = false,
  loading = false,
}) => {
  return (
    <button
      className={`quick-action-card variant-${variant} ${disabled ? 'disabled' : ''}`}
      onClick={onClick}
      disabled={disabled || loading}
    >
      <div className="action-card-icon">
        {loading ? (
          <RefreshCw className="icon spinning" />
        ) : (
          <Icon className="icon" />
        )}
      </div>
      <div className="action-card-content">
        <div className="action-card-title">{title}</div>
        {description && (
          <div className="action-card-description">{description}</div>
        )}
      </div>

      <style>{`
        .quick-action-card {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          width: 100%;
          padding: var(--space-4);
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }

        .quick-action-card:hover:not(:disabled) {
          border-color: var(--border-secondary);
          transform: translateY(-2px);
        }

        .quick-action-card.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .quick-action-card.variant-primary:hover:not(:disabled) {
          border-color: var(--accent-primary);
          background: var(--accent-primary-dim);
        }

        .quick-action-card.variant-warning:hover:not(:disabled) {
          border-color: var(--accent-warning);
          background: var(--accent-warning-dim);
        }

        .quick-action-card.variant-danger:hover:not(:disabled) {
          border-color: var(--accent-danger);
          background: var(--accent-danger-dim);
        }

        .action-card-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          flex-shrink: 0;
        }

        .variant-primary .action-card-icon {
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
        }

        .variant-warning .action-card-icon {
          background: var(--accent-warning-dim);
          color: var(--accent-warning);
        }

        .variant-danger .action-card-icon {
          background: var(--accent-danger-dim);
          color: var(--accent-danger);
        }

        .action-card-content {
          flex: 1;
          min-width: 0;
        }

        .action-card-title {
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .action-card-description {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          margin-top: var(--space-1);
        }

        .spinning {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </button>
  );
};

export default QuickActions;
