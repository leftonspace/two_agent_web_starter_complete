import React, { useState } from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, MoreHorizontal, Eye, RotateCcw, Trash2 } from 'lucide-react';
import type { TaskExecution } from '../../types';
import { Badge, Dropdown } from '../common';

export interface TasksTableProps {
  tasks: TaskExecution[];
  onViewTask?: (task: TaskExecution) => void;
  onRetryTask?: (task: TaskExecution) => void;
  onDeleteTask?: (task: TaskExecution) => void;
  loading?: boolean;
  emptyMessage?: string;
}

export const TasksTable: React.FC<TasksTableProps> = ({
  tasks,
  onViewTask,
  onRetryTask,
  onDeleteTask,
  loading = false,
  emptyMessage = 'No tasks to display',
}) => {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  const getStatusIcon = (status: TaskExecution['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="icon-sm status-completed" />;
      case 'failed':
        return <XCircle className="icon-sm status-failed" />;
      case 'running':
        return <Clock className="icon-sm status-running" />;
      case 'pending':
        return <AlertCircle className="icon-sm status-pending" />;
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

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs.toFixed(0)}s`;
  };

  if (loading) {
    return (
      <div className="tasks-table">
        <div className="tasks-loading">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton skeleton-row" />
          ))}
        </div>
        <style>{tableStyles}</style>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="tasks-table">
        <div className="tasks-empty">
          <p>{emptyMessage}</p>
        </div>
        <style>{tableStyles}</style>
      </div>
    );
  }

  return (
    <div className="tasks-table">
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Task</th>
            <th>Specialist</th>
            <th>Score</th>
            <th>Duration</th>
            <th>Time</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <tr key={task.id} onClick={() => onViewTask?.(task)}>
              <td>
                <div className="status-cell">
                  {getStatusIcon(task.status)}
                </div>
              </td>
              <td>
                <div className="task-cell">
                  <span className="task-name">{task.task_name}</span>
                  <span className="task-id">#{task.id.slice(0, 8)}</span>
                </div>
              </td>
              <td>
                <span className="specialist-name">{task.specialist_name || '-'}</span>
              </td>
              <td>
                <span
                  className="score-value"
                  style={{ color: getScoreColor(task.score) }}
                >
                  {task.score !== undefined ? task.score.toFixed(3) : '-'}
                </span>
              </td>
              <td>
                <span className="duration-value">
                  {formatDuration(task.duration)}
                </span>
              </td>
              <td>
                <span className="time-value">{formatTime(task.timestamp)}</span>
              </td>
              <td>
                <div className="actions-cell">
                  <button
                    className="action-button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setOpenMenuId(openMenuId === task.id ? null : task.id);
                    }}
                  >
                    <MoreHorizontal className="icon-sm" />
                  </button>
                  {openMenuId === task.id && (
                    <div className="action-menu">
                      <button onClick={(e) => {
                        e.stopPropagation();
                        onViewTask?.(task);
                        setOpenMenuId(null);
                      }}>
                        <Eye className="icon-xs" />
                        View Details
                      </button>
                      {task.status === 'failed' && (
                        <button onClick={(e) => {
                          e.stopPropagation();
                          onRetryTask?.(task);
                          setOpenMenuId(null);
                        }}>
                          <RotateCcw className="icon-xs" />
                          Retry
                        </button>
                      )}
                      <button
                        className="delete"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteTask?.(task);
                          setOpenMenuId(null);
                        }}
                      >
                        <Trash2 className="icon-xs" />
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <style>{tableStyles}</style>
    </div>
  );
};

const tableStyles = `
  .tasks-table {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .tasks-table table {
    width: 100%;
    border-collapse: collapse;
  }

  .tasks-table th {
    padding: var(--space-3) var(--space-4);
    text-align: left;
    font-size: var(--text-xs);
    font-weight: var(--weight-semibold);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-primary);
  }

  .tasks-table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-primary);
  }

  .tasks-table tbody tr {
    cursor: pointer;
    transition: background var(--transition-fast);
  }

  .tasks-table tbody tr:hover {
    background: var(--bg-hover);
  }

  .tasks-table tbody tr:last-child td {
    border-bottom: none;
  }

  .status-cell {
    display: flex;
    align-items: center;
    justify-content: center;
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

  .task-cell {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .task-name {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: var(--weight-medium);
  }

  .task-id {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--text-tertiary);
  }

  .specialist-name {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .score-value {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
  }

  .duration-value {
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .time-value {
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }

  .actions-cell {
    position: relative;
  }

  .action-button {
    padding: var(--space-1);
    background: transparent;
    border: none;
    color: var(--text-tertiary);
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
  }

  .action-button:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .action-menu {
    position: absolute;
    right: 0;
    top: 100%;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: var(--z-dropdown);
    min-width: 150px;
  }

  .action-menu button {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    width: 100%;
    padding: var(--space-2) var(--space-3);
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: left;
  }

  .action-menu button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .action-menu button.delete:hover {
    background: var(--accent-danger-dim);
    color: var(--accent-danger);
  }

  .tasks-loading {
    padding: var(--space-4);
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .skeleton-row {
    height: 48px;
    border-radius: var(--radius-sm);
  }

  .tasks-empty {
    padding: var(--space-8);
    text-align: center;
    color: var(--text-tertiary);
  }
`;

export default TasksTable;
