import React from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, User, Calendar, Timer, FileCode } from 'lucide-react';
import type { TaskExecution, TaskDetail } from '../../types';
import { Modal, Badge, StatusBadge } from '../common';
import { FeedbackButtons } from '../dashboard';

export interface TaskDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  task?: TaskExecution | TaskDetail;
  onFeedback?: (feedback: { taskId: string; type: 'positive' | 'negative'; comment?: string }) => void;
  onRetry?: () => void;
}

export const TaskDetailModal: React.FC<TaskDetailModalProps> = ({
  isOpen,
  onClose,
  task,
  onFeedback,
  onRetry,
}) => {
  if (!task) return null;

  const getStatusIcon = (status: TaskExecution['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="icon status-completed" />;
      case 'failed':
        return <XCircle className="icon status-failed" />;
      case 'running':
        return <Clock className="icon status-running" />;
      case 'pending':
        return <AlertCircle className="icon status-pending" />;
      default:
        return null;
    }
  };

  const getScoreColor = (score?: number) => {
    if (score === undefined) return 'var(--text-tertiary)';
    if (score >= 0.85) return 'var(--accent-primary)';
    if (score >= 0.7) return 'var(--accent-secondary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs.toFixed(0)}s`;
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  // Check if task has detailed info
  const isDetailedTask = 'input' in task;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Task Details" size="lg">
      <div className="task-detail">
        {/* Header */}
        <div className="task-detail-header">
          <div className="task-status-icon">
            {getStatusIcon(task.status)}
          </div>
          <div className="task-header-info">
            <h3 className="task-title">{task.task_name}</h3>
            <div className="task-id">#{task.id}</div>
          </div>
          <StatusBadge status={task.status} />
        </div>

        {/* Meta Info */}
        <div className="task-meta-grid">
          <div className="meta-item">
            <User className="icon-sm" />
            <div>
              <div className="meta-label">Specialist</div>
              <div className="meta-value">{task.specialist_name || '-'}</div>
            </div>
          </div>
          <div className="meta-item">
            <Calendar className="icon-sm" />
            <div>
              <div className="meta-label">Timestamp</div>
              <div className="meta-value">{formatDate(task.timestamp)}</div>
            </div>
          </div>
          <div className="meta-item">
            <Timer className="icon-sm" />
            <div>
              <div className="meta-label">Duration</div>
              <div className="meta-value">{formatDuration(task.duration)}</div>
            </div>
          </div>
          <div className="meta-item">
            <FileCode className="icon-sm" />
            <div>
              <div className="meta-label">Score</div>
              <div
                className="meta-value score"
                style={{ color: getScoreColor(task.score) }}
              >
                {task.score !== undefined ? task.score.toFixed(3) : '-'}
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Info */}
        {isDetailedTask && (
          <>
            {(task as TaskDetail).input && (
              <div className="task-section">
                <h4 className="section-title">Input</h4>
                <pre className="task-code">{(task as TaskDetail).input}</pre>
              </div>
            )}

            {(task as TaskDetail).output && (
              <div className="task-section">
                <h4 className="section-title">Output</h4>
                <pre className="task-code">{(task as TaskDetail).output}</pre>
              </div>
            )}

            {(task as TaskDetail).error && (
              <div className="task-section error">
                <h4 className="section-title">Error</h4>
                <pre className="task-code error">{(task as TaskDetail).error}</pre>
              </div>
            )}
          </>
        )}

        {/* Feedback Section */}
        {task.status === 'completed' && onFeedback && (
          <div className="task-feedback">
            <h4 className="section-title">Provide Feedback</h4>
            <FeedbackButtons
              taskId={task.id}
              specialistId={task.specialist_id}
              onFeedback={(fb) => onFeedback({
                taskId: fb.taskId,
                type: fb.type,
                comment: fb.comment,
              })}
            />
          </div>
        )}

        {/* Actions */}
        {task.status === 'failed' && onRetry && (
          <div className="task-actions">
            <button className="retry-button" onClick={onRetry}>
              Retry Task
            </button>
          </div>
        )}
      </div>

      <style>{`
        .task-detail {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .task-detail-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--border-primary);
        }

        .task-status-icon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .status-completed {
          color: var(--accent-primary);
        }

        .status-failed {
          color: var(--accent-danger);
        }

        .status-running {
          color: var(--accent-secondary);
          animation: spin 1s linear infinite;
        }

        .status-pending {
          color: var(--text-tertiary);
        }

        .task-header-info {
          flex: 1;
        }

        .task-title {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .task-id {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          color: var(--text-tertiary);
        }

        .task-meta-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-3);
        }

        .meta-item {
          display: flex;
          align-items: flex-start;
          gap: var(--space-2);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
        }

        .meta-item .icon-sm {
          color: var(--text-tertiary);
          margin-top: 2px;
        }

        .meta-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .meta-value {
          font-size: var(--text-sm);
          color: var(--text-primary);
          font-weight: var(--weight-medium);
        }

        .meta-value.score {
          font-family: var(--font-mono);
          font-weight: var(--weight-bold);
        }

        .task-section {
          margin-top: var(--space-2);
        }

        .section-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-2);
        }

        .task-code {
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
          max-height: 200px;
          overflow-y: auto;
        }

        .task-code.error {
          border-color: var(--accent-danger);
          color: var(--accent-danger);
        }

        .task-section.error .section-title {
          color: var(--accent-danger);
        }

        .task-feedback {
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .task-actions {
          display: flex;
          justify-content: flex-end;
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .retry-button {
          padding: var(--space-2) var(--space-4);
          background: var(--accent-warning);
          border: none;
          border-radius: var(--radius-md);
          color: var(--bg-primary);
          font-weight: var(--weight-semibold);
          cursor: pointer;
          transition: opacity var(--transition-fast);
        }

        .retry-button:hover {
          opacity: 0.9;
        }
      `}</style>
    </Modal>
  );
};

export default TaskDetailModal;
