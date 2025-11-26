import React from 'react';
import { Play, Pause, RotateCcw, Clock, CheckCircle, XCircle } from 'lucide-react';
import type { BenchmarkStatus, BenchmarkResult } from '../../types';
import { Button, Badge, ProgressBar } from '../common';

export interface BenchmarkPanelProps {
  status?: BenchmarkStatus;
  results?: BenchmarkResult[];
  onStart?: () => void;
  onPause?: () => void;
  onReset?: () => void;
  loading?: boolean;
}

export const BenchmarkPanel: React.FC<BenchmarkPanelProps> = ({
  status,
  results = [],
  onStart,
  onPause,
  onReset,
  loading = false,
}) => {
  const isRunning = status?.running ?? false;
  const progress = status?.progress ?? 0;
  const currentTask = status?.current_task;

  const getStatusIcon = (passed: boolean) => {
    return passed ? (
      <CheckCircle className="icon-sm status-pass" />
    ) : (
      <XCircle className="icon-sm status-fail" />
    );
  };

  return (
    <div className="benchmark-panel">
      <div className="benchmark-header">
        <h3 className="benchmark-title">Benchmark Suite</h3>
        <div className="benchmark-actions">
          {isRunning ? (
            <Button
              variant="warning"
              size="sm"
              icon={Pause}
              onClick={onPause}
              loading={loading}
            >
              Pause
            </Button>
          ) : (
            <Button
              variant="primary"
              size="sm"
              icon={Play}
              onClick={onStart}
              loading={loading}
            >
              Run All
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            icon={RotateCcw}
            onClick={onReset}
            disabled={isRunning || loading}
          >
            Reset
          </Button>
        </div>
      </div>

      {isRunning && (
        <div className="benchmark-progress">
          <div className="progress-info">
            <span className="progress-label">Progress</span>
            <span className="progress-value">{Math.round(progress * 100)}%</span>
          </div>
          <ProgressBar value={progress * 100} variant="primary" animated />
          {currentTask && (
            <div className="current-task">
              <Clock className="icon-xs" />
              <span>Running: {currentTask}</span>
            </div>
          )}
        </div>
      )}

      {results.length > 0 && (
        <div className="benchmark-results">
          <div className="results-header">
            <span>Recent Results</span>
            <Badge variant="info" size="sm">
              {results.filter(r => r.passed).length}/{results.length} passed
            </Badge>
          </div>
          <div className="results-list">
            {results.slice(0, 5).map((result, index) => (
              <div key={index} className="result-row">
                {getStatusIcon(result.passed)}
                <span className="result-name">{result.task_name}</span>
                <span className="result-score">{(result.score || 0).toFixed(3)}</span>
                <span className="result-time">{(result.execution_time || 0).toFixed(1)}s</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!isRunning && results.length === 0 && (
        <div className="benchmark-empty">
          <p>No benchmark results yet.</p>
          <p className="empty-hint">Click "Run All" to start the benchmark suite.</p>
        </div>
      )}

      <style>{`
        .benchmark-panel {
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          padding: var(--space-4);
        }

        .benchmark-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-4);
        }

        .benchmark-title {
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .benchmark-actions {
          display: flex;
          gap: var(--space-2);
        }

        .benchmark-progress {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-md);
          margin-bottom: var(--space-4);
        }

        .progress-info {
          display: flex;
          justify-content: space-between;
          margin-bottom: var(--space-2);
        }

        .progress-label {
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .progress-value {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--accent-primary);
        }

        .current-task {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          margin-top: var(--space-2);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .benchmark-results {
          border-top: 1px solid var(--border-primary);
          padding-top: var(--space-4);
        }

        .results-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--space-3);
          font-size: var(--text-sm);
          color: var(--text-secondary);
        }

        .results-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .result-row {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-2);
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .status-pass {
          color: var(--accent-primary);
        }

        .status-fail {
          color: var(--accent-danger);
        }

        .result-name {
          flex: 1;
          font-size: var(--text-sm);
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .result-score {
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--accent-secondary);
        }

        .result-time {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          min-width: 40px;
          text-align: right;
        }

        .benchmark-empty {
          text-align: center;
          padding: var(--space-6);
          color: var(--text-secondary);
        }

        .empty-hint {
          font-size: var(--text-sm);
          color: var(--text-tertiary);
          margin-top: var(--space-2);
        }
      `}</style>
    </div>
  );
};

export default BenchmarkPanel;
