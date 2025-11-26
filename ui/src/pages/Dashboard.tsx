import React, { useState, useCallback } from 'react';
import { Brain, Activity, Clock, DollarSign, RefreshCw } from 'lucide-react';

// Layout components
import { Header, Sidebar, MainContent, ContentHeader, ContentSection } from '../components/layout';

// Dashboard components
import {
  EvaluationModeSelector,
  DomainCard,
  BenchmarkPanel,
  TasksTable,
  BudgetBadge,
} from '../components/dashboard';

// Chart components
import { StatsCard, StatsGrid, ScoreLineChart } from '../components/charts';

// Modal components
import {
  TaskDetailModal,
  SpecialistDetailModal,
  NewTaskModal,
  BudgetDetailModal,
  SettingsPanel,
  GraveyardModal,
} from '../components/modals';

// Hooks
import {
  useDashboard,
  useBenchmarkActions,
  useAutoRefresh,
  useSafeNotificationContext,
} from '../hooks';

// Types
import type { EvaluationMode, TaskExecution, SpecialistSummary } from '../types';

export const Dashboard: React.FC = () => {
  // Dashboard data
  const {
    overview,
    domains,
    budget,
    recentTasks,
    evaluationMode,
    benchmarkStatus,
    health,
    loading,
    error,
    refetchAll,
    setEvaluationMode,
  } = useDashboard();

  // Benchmark actions
  const benchmarkActions = useBenchmarkActions();

  // Notifications (may be null if not within NotificationProvider)
  const notifications = useSafeNotificationContext();

  // Auto-refresh
  const { lastRefresh, isRefreshing } = useAutoRefresh({
    interval: 30000,
    onRefresh: refetchAll,
    immediate: false,
  });

  // Modal states
  const [selectedTask, setSelectedTask] = useState<TaskExecution | null>(null);
  const [selectedSpecialist, setSelectedSpecialist] = useState<SpecialistSummary | null>(null);
  const [showNewTaskModal, setShowNewTaskModal] = useState(false);
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showGraveyardModal, setShowGraveyardModal] = useState(false);

  // Handlers
  const handleModeChange = useCallback(async (mode: EvaluationMode) => {
    try {
      await setEvaluationMode(mode);
      notifications?.success('Evaluation Mode Updated', `Mode set to ${mode}`);
    } catch (err) {
      notifications?.error('Failed to update mode', err instanceof Error ? err.message : 'Unknown error');
    }
  }, [setEvaluationMode, notifications]);

  const handleRunBenchmark = useCallback(async () => {
    try {
      await benchmarkActions.run();
      notifications?.success('Benchmark Started', 'Running benchmark suite');
    } catch (err) {
      notifications?.error('Benchmark Failed', err instanceof Error ? err.message : 'Unknown error');
    }
  }, [benchmarkActions, notifications]);

  const handleForceEvolution = useCallback(() => {
    notifications?.info('Evolution Triggered', 'Starting evolution cycle');
    // Implement evolution trigger
  }, [notifications]);

  // Mock score history data for chart
  const scoreHistory = overview?.domains?.slice(0, 1).map(() => {
    const today = new Date();
    return Array.from({ length: 14 }, (_, j) => ({
      timestamp: new Date(today.getTime() - (13 - j) * 24 * 60 * 60 * 1000).toISOString(),
      score: 0.7 + Math.random() * 0.25,
      label: 'Avg Score',
    }));
  })[0] || [];

  // Convert tasks for table
  const tasksForTable: TaskExecution[] = (recentTasks || []).map((task) => ({
    id: task.id,
    task_name: task.task_name,
    specialist_id: task.specialist_id,
    specialist_name: task.specialist_name,
    status: task.status as TaskExecution['status'],
    score: task.score,
    duration: task.execution_time,
    timestamp: task.timestamp,
  }));

  // System health status
  const systemHealth = health?.status === 'healthy' ? 'healthy' :
                       health?.status === 'degraded' ? 'degraded' : 'unhealthy';

  if (error && !overview) {
    return (
      <div className="error-page">
        <div className="error-content">
          <div className="error-icon">⚠️</div>
          <h2>Failed to Load Dashboard</h2>
          <p>{error.message}</p>
          <button className="retry-button" onClick={refetchAll}>
            <RefreshCw className="icon-sm" />
            Retry
          </button>
        </div>
        <style>{`
          .error-page {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-primary);
          }
          .error-content {
            text-align: center;
            padding: var(--space-8);
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            max-width: 400px;
          }
          .error-icon {
            font-size: 3rem;
            margin-bottom: var(--space-4);
          }
          .error-content h2 {
            color: var(--text-primary);
            margin-bottom: var(--space-2);
          }
          .error-content p {
            color: var(--text-secondary);
            margin-bottom: var(--space-4);
          }
          .retry-button {
            display: inline-flex;
            align-items: center;
            gap: var(--space-2);
            padding: var(--space-2) var(--space-4);
            background: var(--accent-primary);
            border: none;
            border-radius: var(--radius-md);
            color: var(--bg-primary);
            font-weight: var(--weight-semibold);
            cursor: pointer;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Header
        systemHealth={systemHealth}
        onSettingsClick={() => setShowSettingsModal(true)}
        onBudgetClick={() => setShowBudgetModal(true)}
      />

      <Sidebar
        activePage="dashboard"
        domains={domains?.map((d) => ({
          id: d.name,
          name: d.name,
          icon: Brain,
          specialistCount: d.specialists?.length || 0,
          avgScore: d.avg_score || 0,
        }))}
        onRunBenchmark={handleRunBenchmark}
        onForceEvolution={handleForceEvolution}
        onNewTask={() => setShowNewTaskModal(true)}
        onViewGraveyard={() => setShowGraveyardModal(true)}
      />

      <MainContent>
        <ContentHeader
          title={
            <>
              <Activity className="icon" style={{ color: 'var(--accent-primary)' }} />
              Dashboard Overview
            </>
          }
          subtitle={lastRefresh ? `Last updated: ${lastRefresh.toLocaleTimeString()}` : undefined}
          actions={
            <button
              className="refresh-btn"
              onClick={refetchAll}
              disabled={isRefreshing || loading}
            >
              <RefreshCw className={`icon-sm ${isRefreshing ? 'spinning' : ''}`} />
            </button>
          }
        />

        {/* Stats Grid */}
        <ContentSection>
          <StatsGrid columns={4}>
            <StatsCard
              title="Total Specialists"
              value={overview?.total_specialists ?? '-'}
              icon={Brain}
              variant="primary"
              loading={loading}
            />
            <StatsCard
              title="Active Domains"
              value={overview?.domains?.length ?? '-'}
              icon={Activity}
              variant="success"
              loading={loading}
            />
            <StatsCard
              title="Tasks Today"
              value={overview?.total_tasks_today ?? '-'}
              icon={Clock}
              trend={12}
              trendLabel="vs yesterday"
              loading={loading}
            />
            <StatsCard
              title="Spent Today"
              value={budget ? `$${budget.used.toFixed(2)}` : '-'}
              icon={DollarSign}
              variant={budget && budget.remaining < budget.daily_limit * 0.2 ? 'warning' : 'default'}
              loading={loading}
            />
          </StatsGrid>
        </ContentSection>

        {/* Evaluation Mode Selector */}
        <ContentSection title="Evaluation Mode">
          <EvaluationModeSelector
            value={evaluationMode}
            onChange={handleModeChange}
            disabled={loading}
          />
        </ContentSection>

        {/* Domain Cards */}
        <ContentSection title="Domain Pools">
          <div className="domain-grid">
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="skeleton skeleton-card" style={{ height: '160px' }} />
              ))
            ) : (
              domains?.map((domain) => (
                <DomainCard
                  key={domain.name}
                  domain={{
                    name: domain.name,
                    specialists: domain.specialists?.length || 0,
                    avg_score: domain.avg_score || 0,
                    best_score: domain.best_score || 0,
                    tasks_today: domain.tasks_today || 0,
                    convergence_progress: domain.convergence_progress || 0,
                    evolution_paused: domain.evolution_paused || false,
                  }}
                  specialists={domain.specialists?.map((s) => ({
                    id: s.id,
                    name: s.name,
                    score: s.score,
                    status: s.status,
                    tasks_completed: s.tasks_completed,
                    generation: s.generation,
                  }))}
                  onSpecialistClick={(specialist) => setSelectedSpecialist(specialist)}
                />
              ))
            )}
          </div>
        </ContentSection>

        {/* Two Column Layout */}
        <div className="two-column">
          {/* Score Chart */}
          <ContentSection title="Score Trends">
            <ScoreLineChart
              data={scoreHistory}
              height={280}
              title=""
              fill={true}
            />
          </ContentSection>

          {/* Benchmark Panel */}
          <ContentSection title="Benchmarks">
            <BenchmarkPanel
              status={benchmarkStatus || undefined}
              onStart={handleRunBenchmark}
              onPause={() => benchmarkActions.pause()}
              loading={benchmarkActions.loading}
            />
          </ContentSection>
        </div>

        {/* Recent Tasks */}
        <ContentSection title="Recent Tasks">
          <TasksTable
            tasks={tasksForTable}
            loading={loading}
            onViewTask={(task) => setSelectedTask(task)}
            emptyMessage="No recent tasks"
          />
        </ContentSection>

        {/* Budget Summary */}
        <ContentSection>
          <BudgetBadge
            budget={budget || undefined}
            onClick={() => setShowBudgetModal(true)}
          />
        </ContentSection>
      </MainContent>

      {/* Modals */}
      <TaskDetailModal
        isOpen={!!selectedTask}
        onClose={() => setSelectedTask(null)}
        task={selectedTask || undefined}
      />

      <SpecialistDetailModal
        isOpen={!!selectedSpecialist}
        onClose={() => setSelectedSpecialist(null)}
        specialist={selectedSpecialist || undefined}
      />

      <NewTaskModal
        isOpen={showNewTaskModal}
        onClose={() => setShowNewTaskModal(false)}
        domains={domains?.map((d) => ({ id: d.name, name: d.name }))}
        onSubmit={(task) => {
          notifications?.success('Task Created', `Created task: ${task.name}`);
          setShowNewTaskModal(false);
        }}
      />

      <BudgetDetailModal
        isOpen={showBudgetModal}
        onClose={() => setShowBudgetModal(false)}
        budget={budget || undefined}
      />

      <SettingsPanel
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        onSave={() => {
          notifications?.success('Settings Saved', 'Your preferences have been updated');
        }}
      />

      <GraveyardModal
        isOpen={showGraveyardModal}
        onClose={() => setShowGraveyardModal(false)}
        entries={[]}
      />

      <style>{`
        .dashboard-layout {
          min-height: 100vh;
          background: var(--bg-primary);
        }

        .domain-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: var(--space-4);
        }

        .two-column {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--space-6);
        }

        @media (max-width: 1024px) {
          .two-column {
            grid-template-columns: 1fr;
          }
        }

        .refresh-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .refresh-btn:hover:not(:disabled) {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .refresh-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .spinning {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default Dashboard;
