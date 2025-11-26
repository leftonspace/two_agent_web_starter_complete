import React from 'react';
import { Brain, Trash2, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { SpecialistSummary } from '../../types';
import { Badge, StatusBadge } from '../common';

export interface SpecialistRowProps {
  specialist: SpecialistSummary;
  onClick?: () => void;
  onDelete?: () => void;
  showActions?: boolean;
}

export const SpecialistRow: React.FC<SpecialistRowProps> = ({
  specialist,
  onClick,
  onDelete,
  showActions = false,
}) => {
  const getTrendIcon = () => {
    if (!specialist.trend) return <Minus className="icon-xs" />;
    if (specialist.trend > 0) return <TrendingUp className="icon-xs trend-up" />;
    if (specialist.trend < 0) return <TrendingDown className="icon-xs trend-down" />;
    return <Minus className="icon-xs" />;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return 'var(--accent-primary)';
    if (score >= 0.7) return 'var(--accent-secondary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  return (
    <div
      className={`specialist-row ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={(e) => e.key === 'Enter' && onClick?.()}
    >
      <div className="specialist-icon">
        <Brain className="icon" />
      </div>

      <div className="specialist-info">
        <div className="specialist-name">{specialist.name}</div>
        <div className="specialist-meta">
          <span className="specialist-id">#{specialist.id.slice(0, 8)}</span>
          {specialist.generation !== undefined && (
            <>
              <span className="separator">•</span>
              <span>Gen {specialist.generation}</span>
            </>
          )}
        </div>
      </div>

      <div className="specialist-status">
        <StatusBadge status={specialist.status} size="sm" />
      </div>

      <div className="specialist-score">
        <span
          className="score-value"
          style={{ color: getScoreColor(specialist.score) }}
        >
          {specialist.score.toFixed(3)}
        </span>
        <span className="score-trend">{getTrendIcon()}</span>
      </div>

      {specialist.tasks_completed !== undefined && (
        <div className="specialist-tasks">
          <span className="tasks-count">{specialist.tasks_completed}</span>
          <span className="tasks-label">tasks</span>
        </div>
      )}

      {showActions && onDelete && (
        <button
          className="specialist-delete"
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          aria-label="Delete specialist"
        >
          <Trash2 className="icon-sm" />
        </button>
      )}

      <style>{`
        .specialist-row {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
          transition: all var(--transition-fast);
        }

        .specialist-row.clickable {
          cursor: pointer;
        }

        .specialist-row.clickable:hover {
          background: var(--bg-hover);
        }

        .specialist-icon {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-secondary);
          border-radius: var(--radius-sm);
          color: var(--text-secondary);
          flex-shrink: 0;
        }

        .specialist-info {
          flex: 1;
          min-width: 0;
        }

        .specialist-name {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .specialist-meta {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          display: flex;
          gap: var(--space-1);
        }

        .specialist-id {
          font-family: var(--font-mono);
        }

        .separator {
          color: var(--border-primary);
        }

        .specialist-status {
          flex-shrink: 0;
        }

        .specialist-score {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          flex-shrink: 0;
        }

        .score-value {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          font-weight: var(--weight-bold);
        }

        .score-trend {
          display: flex;
          align-items: center;
        }

        .trend-up {
          color: var(--accent-primary);
        }

        .trend-down {
          color: var(--accent-danger);
        }

        .specialist-tasks {
          display: flex;
          flex-direction: column;
          align-items: center;
          flex-shrink: 0;
          min-width: 40px;
        }

        .tasks-count {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .tasks-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .specialist-delete {
          padding: var(--space-1);
          background: transparent;
          border: none;
          color: var(--text-tertiary);
          cursor: pointer;
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
          flex-shrink: 0;
        }

        .specialist-delete:hover {
          background: var(--accent-danger-dim);
          color: var(--accent-danger);
        }
      `}</style>
    </div>
  );
};

export default SpecialistRow;
