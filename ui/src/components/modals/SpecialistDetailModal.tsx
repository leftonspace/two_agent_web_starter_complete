import React from 'react';
import { Brain, Activity, TrendingUp, TrendingDown, Minus, Calendar, Target, Trash2 } from 'lucide-react';
import type { SpecialistDetail, SpecialistSummary } from '../../types';
import { Modal, Badge, StatusBadge, ProgressBar, Button } from '../common';

export interface SpecialistDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  specialist?: SpecialistDetail | SpecialistSummary;
  onDelete?: () => void;
  onViewTasks?: () => void;
}

export const SpecialistDetailModal: React.FC<SpecialistDetailModalProps> = ({
  isOpen,
  onClose,
  specialist,
  onDelete,
  onViewTasks,
}) => {
  if (!specialist) return null;

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return 'var(--accent-primary)';
    if (score >= 0.7) return 'var(--accent-secondary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  const getTrendIcon = () => {
    if (!specialist.trend) return <Minus className="icon-sm" />;
    if (specialist.trend > 0) return <TrendingUp className="icon-sm trend-up" />;
    if (specialist.trend < 0) return <TrendingDown className="icon-sm trend-down" />;
    return <Minus className="icon-sm" />;
  };

  const isDetailedSpecialist = 'model' in specialist;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Specialist Details" size="lg">
      <div className="specialist-detail">
        {/* Header */}
        <div className="specialist-header">
          <div className="specialist-avatar">
            <Brain className="icon-lg" />
          </div>
          <div className="specialist-header-info">
            <h3 className="specialist-name">{specialist.name}</h3>
            <div className="specialist-id">#{specialist.id}</div>
            {specialist.generation !== undefined && (
              <Badge variant="info" size="sm">
                Generation {specialist.generation}
              </Badge>
            )}
          </div>
          <StatusBadge status={specialist.status} />
        </div>

        {/* Score Display */}
        <div className="score-display">
          <div className="score-main">
            <span className="score-label">Current Score</span>
            <span
              className="score-value"
              style={{ color: getScoreColor(specialist.score || 0) }}
            >
              {(specialist.score || 0).toFixed(3)}
            </span>
            <span className="score-trend">{getTrendIcon()}</span>
          </div>
          <ProgressBar
            value={(specialist.score || 0) * 100}
            variant={(specialist.score || 0) >= 0.85 ? 'primary' : (specialist.score || 0) >= 0.7 ? 'secondary' : 'warning'}
          />
        </div>

        {/* Stats Grid */}
        <div className="stats-grid">
          {specialist.tasks_completed !== undefined && (
            <div className="stat-item">
              <Target className="icon" />
              <div className="stat-info">
                <span className="stat-value">{specialist.tasks_completed}</span>
                <span className="stat-label">Tasks Completed</span>
              </div>
            </div>
          )}
          {isDetailedSpecialist && (specialist as SpecialistDetail).success_rate !== undefined && (
            <div className="stat-item">
              <Activity className="icon" />
              <div className="stat-info">
                <span className="stat-value">
                  {((specialist as SpecialistDetail).success_rate! * 100).toFixed(1)}%
                </span>
                <span className="stat-label">Success Rate</span>
              </div>
            </div>
          )}
          {isDetailedSpecialist && (specialist as SpecialistDetail).created_at && (
            <div className="stat-item">
              <Calendar className="icon" />
              <div className="stat-info">
                <span className="stat-value">
                  {new Date((specialist as SpecialistDetail).created_at!).toLocaleDateString()}
                </span>
                <span className="stat-label">Created</span>
              </div>
            </div>
          )}
        </div>

        {/* Detailed Info */}
        {isDetailedSpecialist && (
          <>
            <div className="detail-section">
              <h4 className="section-title">Configuration</h4>
              <div className="config-grid">
                <div className="config-item">
                  <span className="config-label">Model</span>
                  <span className="config-value">
                    {(specialist as SpecialistDetail).model || '-'}
                  </span>
                </div>
                <div className="config-item">
                  <span className="config-label">Domain</span>
                  <span className="config-value">
                    {(specialist as SpecialistDetail).domain || '-'}
                  </span>
                </div>
                {(specialist as SpecialistDetail).temperature !== undefined && (
                  <div className="config-item">
                    <span className="config-label">Temperature</span>
                    <span className="config-value">
                      {(specialist as SpecialistDetail).temperature}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {(specialist as SpecialistDetail).system_prompt && (
              <div className="detail-section">
                <h4 className="section-title">System Prompt</h4>
                <pre className="prompt-preview">
                  {(specialist as SpecialistDetail).system_prompt}
                </pre>
              </div>
            )}
          </>
        )}

        {/* Actions */}
        <div className="specialist-actions">
          {onViewTasks && (
            <Button variant="secondary" onClick={onViewTasks}>
              View Tasks
            </Button>
          )}
          {onDelete && (
            <Button variant="danger" icon={Trash2} onClick={onDelete}>
              Delete Specialist
            </Button>
          )}
        </div>
      </div>

      <style>{`
        .specialist-detail {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .specialist-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--border-primary);
        }

        .specialist-avatar {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
          border-radius: var(--radius-lg);
        }

        .specialist-header-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: var(--space-1);
        }

        .specialist-name {
          font-size: var(--text-xl);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .specialist-id {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }

        .score-display {
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .score-main {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          margin-bottom: var(--space-3);
        }

        .score-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .score-value {
          font-family: var(--font-mono);
          font-size: var(--text-2xl);
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

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-3);
        }

        .stat-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .stat-item .icon {
          color: var(--text-tertiary);
        }

        .stat-info {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: var(--text-lg);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .detail-section {
          margin-top: var(--space-2);
        }

        .section-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-2);
        }

        .config-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-2);
        }

        .config-item {
          padding: var(--space-2);
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .config-label {
          display: block;
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin-bottom: var(--space-1);
        }

        .config-value {
          font-size: var(--text-sm);
          color: var(--text-primary);
          font-weight: var(--weight-medium);
        }

        .prompt-preview {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-primary);
          overflow-x: auto;
          white-space: pre-wrap;
          word-break: break-word;
          max-height: 150px;
          overflow-y: auto;
        }

        .specialist-actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-2);
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }
      `}</style>
    </Modal>
  );
};

export default SpecialistDetailModal;
