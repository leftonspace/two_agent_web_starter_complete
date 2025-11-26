import React, { useEffect, useState, useCallback } from 'react';
import type { DashboardOverview, EvaluationMode } from '../types';
import { dashboardApi } from '../api/client';
import {
  LoadingSpinner,
  BudgetStatus,
  DomainCard,
  EvaluationToggle,
  BenchmarkControls,
  RecentTasks,
} from '../components';

export const Dashboard: React.FC = () => {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchOverview = useCallback(async () => {
    try {
      const data = await dashboardApi.getOverview();
      setOverview(data);
      setError(null);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [fetchOverview]);

  const handleModeChange = (mode: EvaluationMode) => {
    if (overview) {
      setOverview({
        ...overview,
        evaluation: {
          ...overview.evaluation,
          mode,
          scoring_committee_enabled: mode === 'scoring_committee' || mode === 'both',
          ai_council_enabled: mode === 'ai_council' || mode === 'both',
          comparison_tracking: mode === 'both',
        },
      });
    }
  };

  const getHealthBadge = (health: string) => {
    switch (health) {
      case 'healthy':
        return <span className="badge badge-success">Healthy</span>;
      case 'degraded':
        return <span className="badge badge-warning">Degraded</span>;
      case 'unhealthy':
        return <span className="badge badge-danger">Unhealthy</span>;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <LoadingSpinner size="lg" message="Loading JARVIS Dashboard..." />
      </div>
    );
  }

  if (error || !overview) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="card text-center max-w-md">
          <div className="text-red-600 text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold mb-2">Failed to Load Dashboard</h2>
          <p className="text-gray-600 mb-4">{error || 'Unknown error'}</p>
          <button onClick={fetchOverview} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-900">
                🤖 JARVIS Dashboard
              </h1>
              {getHealthBadge(overview.system_health)}
            </div>
            <div className="flex items-center gap-6">
              <BudgetStatus budget={overview.budget} />
              <div className="text-sm text-gray-500">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-3xl font-bold text-jarvis-600">
              {overview.total_specialists}
            </div>
            <div className="text-sm text-gray-500">Total Specialists</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-jarvis-600">
              {overview.domains.length}
            </div>
            <div className="text-sm text-gray-500">Active Domains</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-jarvis-600">
              {overview.total_tasks_today}
            </div>
            <div className="text-sm text-gray-500">Tasks Today</div>
          </div>
          <div className="card text-center">
            <div className="text-3xl font-bold text-jarvis-600">
              ${overview.budget.production_spent_today.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">Spent Today</div>
          </div>
        </div>

        {/* Evaluation Toggle */}
        <EvaluationToggle
          evaluation={overview.evaluation}
          onModeChange={handleModeChange}
        />

        {/* Domain Cards Grid */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Domain Pools
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {overview.domains.map(domain => (
              <DomainCard
                key={domain.name}
                domain={domain}
                onClick={() => {
                  // Could navigate to domain detail page
                  console.log('Navigate to domain:', domain.name);
                }}
              />
            ))}
          </div>
        </div>

        {/* Two Column Layout for Benchmark and Tasks */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <BenchmarkControls />
          <RecentTasks limit={5} />
        </div>

        {/* Full Width Recent Tasks */}
        <RecentTasks limit={15} />
      </main>

      {/* Footer */}
      <footer className="border-t bg-white mt-8">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-500">
          JARVIS v7.5 - Self-Evolving Business AI Platform
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
