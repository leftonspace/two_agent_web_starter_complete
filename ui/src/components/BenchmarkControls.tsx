import React, { useEffect, useState } from 'react';
import type { BenchmarkStatus, BenchmarkRunSummary, BenchmarkDiscovery } from '../types';
import { benchmarkApi } from '../api/client';

interface BenchmarkControlsProps {
  className?: string;
}

export const BenchmarkControls: React.FC<BenchmarkControlsProps> = ({ className = '' }) => {
  const [status, setStatus] = useState<BenchmarkStatus | null>(null);
  const [discovery, setDiscovery] = useState<BenchmarkDiscovery | null>(null);
  const [history, setHistory] = useState<BenchmarkRunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadStatus, 5000); // Poll status every 5s
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    await Promise.all([loadStatus(), loadDiscovery(), loadHistory()]);
  };

  const loadStatus = async () => {
    try {
      const data = await benchmarkApi.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load benchmark status:', err);
    }
  };

  const loadDiscovery = async () => {
    try {
      const data = await benchmarkApi.discover();
      setDiscovery(data);
    } catch (err) {
      console.error('Failed to discover benchmarks:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await benchmarkApi.getHistory({ limit: 5 });
      setHistory(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleRun = async (domain?: string) => {
    setLoading(true);
    setError(null);
    try {
      await benchmarkApi.run(domain ? { domain } : undefined);
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start benchmark');
    } finally {
      setLoading(false);
    }
  };

  const handlePause = async () => {
    setLoading(true);
    try {
      await benchmarkApi.pause();
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to pause');
    } finally {
      setLoading(false);
    }
  };

  const handleResume = async () => {
    setLoading(true);
    try {
      await benchmarkApi.resume();
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resume');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    setLoading(true);
    try {
      await benchmarkApi.cancel();
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (runStatus: string) => {
    switch (runStatus) {
      case 'completed': return 'text-green-600';
      case 'running': return 'text-blue-600';
      case 'paused': return 'text-yellow-600';
      case 'failed': return 'text-red-600';
      case 'cancelled': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header mb-0">Benchmark Mode</h3>
        {status?.is_running && (
          <span className="badge badge-info animate-pulse">Running</span>
        )}
        {status?.is_paused && (
          <span className="badge badge-warning">Paused</span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => handleRun()}
          disabled={loading || status?.is_running}
          className="btn-primary"
        >
          ▶ Run All
        </button>

        {discovery && Object.keys(discovery.domains).map(domain => (
          <button
            key={domain}
            onClick={() => handleRun(domain)}
            disabled={loading || status?.is_running}
            className="btn-secondary"
          >
            ▶ {domain.replace(/_/g, ' ')}
          </button>
        ))}

        <div className="flex-1" />

        {status?.is_running && (
          <button onClick={handlePause} disabled={loading} className="btn-secondary">
            ⏸ Pause
          </button>
        )}

        {status?.is_paused && (
          <button onClick={handleResume} disabled={loading} className="btn-success">
            ▶ Resume
          </button>
        )}

        {(status?.is_running || status?.is_paused) && (
          <button onClick={handleCancel} disabled={loading} className="btn-danger">
            ⏹ Cancel
          </button>
        )}
      </div>

      {/* Current Progress */}
      {status?.current_run && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex justify-between items-center mb-2">
            <span className="font-medium">{status.current_run.benchmark_name}</span>
            <span className="text-sm text-gray-600">
              {status.current_run.tasks_completed}/{status.current_run.tasks_total} tasks
            </span>
          </div>
          <div className="w-full h-2 bg-blue-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all"
              style={{ width: `${status.progress_percent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{status.progress_percent.toFixed(1)}%</span>
            {status.current_task && (
              <span>Current: {status.current_task}</span>
            )}
          </div>
        </div>
      )}

      {/* Recent History */}
      {history.length > 0 && (
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-600 mb-2">Recent Runs</h4>
          <div className="space-y-2">
            {history.map(run => (
              <div
                key={run.id}
                className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded"
              >
                <div>
                  <span className="font-medium">{run.benchmark_name}</span>
                  <span className={`ml-2 ${getStatusColor(run.status)}`}>
                    {run.status}
                  </span>
                </div>
                <div className="text-right text-gray-500">
                  <div>
                    {run.tasks_completed}/{run.tasks_total} tasks |{' '}
                    <span className="font-medium">{(run.avg_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="text-xs">${run.cost_spent.toFixed(4)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      {discovery && (
        <div className="mt-4 pt-4 border-t text-sm text-gray-500">
          {discovery.total_benchmarks} benchmarks available across{' '}
          {Object.keys(discovery.domains).length} domains
        </div>
      )}
    </div>
  );
};

export default BenchmarkControls;
