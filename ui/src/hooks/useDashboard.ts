import { useCallback, useMemo } from 'react';
import { useApiOnMount, useMutation, clearCacheEntry } from './useApi';
import { api } from '../api/client';
import type {
  DashboardOverview,
  DomainDetail,
  SpecialistSummary,
  SpecialistDetail,
  BudgetStatus,
  TaskSummary,
  TaskDetail,
  EvaluationMode,
  BenchmarkStatus,
} from '../types';

export function useDashboardOverview() {
  return useApiOnMount<DashboardOverview>(
    () => api.dashboard.getOverview(),
    { cacheKey: 'dashboard:overview', cacheDuration: 10000 }
  );
}

export function useDomains() {
  return useApiOnMount<DomainDetail[]>(
    () => api.dashboard.getDomains(),
    { cacheKey: 'dashboard:domains', cacheDuration: 30000 }
  );
}

export function useDomainDetail(domain: string) {
  return useApiOnMount<DomainDetail>(
    () => api.dashboard.getDomainDetail(domain),
    { cacheKey: `dashboard:domain:${domain}`, cacheDuration: 30000 }
  );
}

export function useSpecialists(params?: { domain?: string; active_only?: boolean; limit?: number }) {
  const cacheKey = `dashboard:specialists:${JSON.stringify(params || {})}`;
  return useApiOnMount<SpecialistSummary[]>(
    () => api.dashboard.getSpecialists(params),
    { cacheKey, cacheDuration: 30000 }
  );
}

export function useSpecialistDetail(id: string) {
  return useApiOnMount<SpecialistDetail>(
    () => api.dashboard.getSpecialistDetail(id),
    { cacheKey: `dashboard:specialist:${id}`, cacheDuration: 30000 }
  );
}

export function useBudget() {
  return useApiOnMount<BudgetStatus>(
    () => api.dashboard.getBudget(),
    { cacheKey: 'dashboard:budget', cacheDuration: 10000 }
  );
}

export function useRecentTasks(params?: { limit?: number; domain?: string; specialist_id?: string }) {
  const cacheKey = `tasks:recent:${JSON.stringify(params || {})}`;
  return useApiOnMount<TaskSummary[]>(
    () => api.tasks.getRecent(params),
    { cacheKey, cacheDuration: 15000 }
  );
}

export function useTaskDetail(taskId: string) {
  return useApiOnMount<TaskDetail>(
    () => api.tasks.getTaskDetail(taskId),
    { cacheKey: `tasks:detail:${taskId}`, cacheDuration: 60000 }
  );
}

export function useEvaluationMode() {
  const query = useApiOnMount(
    () => api.evaluation.getMode(),
    { cacheKey: 'evaluation:mode', cacheDuration: 30000 }
  );

  const mutation = useMutation(
    (mode: EvaluationMode) => api.evaluation.setMode(mode),
    {
      onSuccess: () => {
        clearCacheEntry('evaluation:mode');
        query.refetch();
      },
    }
  );

  return {
    mode: query.data?.mode || 'both',
    scoringCommitteeEnabled: query.data?.scoring_committee_enabled ?? true,
    aiCouncilEnabled: query.data?.ai_council_enabled ?? true,
    loading: query.loading || mutation.loading,
    error: query.error || mutation.error,
    setMode: mutation.mutate,
    refetch: query.refetch,
  };
}

export function useBenchmarkStatus() {
  return useApiOnMount<BenchmarkStatus>(
    () => api.benchmark.getStatus(),
    { cacheKey: 'benchmark:status', cacheDuration: 5000 }
  );
}

export function useBenchmarkActions() {
  const runMutation = useMutation(
    (params?: { domain?: string; benchmark_name?: string }) => api.benchmark.run(params)
  );

  const pauseMutation = useMutation(() => api.benchmark.pause());
  const resumeMutation = useMutation(() => api.benchmark.resume());
  const cancelMutation = useMutation(() => api.benchmark.cancel());

  return {
    run: runMutation.mutate,
    pause: pauseMutation.mutate,
    resume: resumeMutation.mutate,
    cancel: cancelMutation.mutate,
    loading: runMutation.loading || pauseMutation.loading || resumeMutation.loading || cancelMutation.loading,
    error: runMutation.error || pauseMutation.error || resumeMutation.error || cancelMutation.error,
  };
}

export function useTaskFeedback() {
  return useMutation(
    ({ taskId, feedback }: { taskId: string; feedback: { rating: number; comment?: string } }) =>
      api.tasks.submitFeedback(taskId, feedback),
    {
      onSuccess: () => {
        clearCacheEntry('tasks:recent');
        clearCacheEntry('tasks:pending-feedback');
      },
    }
  );
}

export function useHealthCheck() {
  return useApiOnMount(
    () => api.health.check(),
    { cacheKey: 'health:check', cacheDuration: 10000 }
  );
}

// Combined dashboard hook for convenience
export function useDashboard() {
  const overview = useDashboardOverview();
  const domains = useDomains();
  const budget = useBudget();
  const recentTasks = useRecentTasks({ limit: 10 });
  const evaluationMode = useEvaluationMode();
  const benchmarkStatus = useBenchmarkStatus();
  const health = useHealthCheck();

  const loading = useMemo(
    () =>
      overview.loading ||
      domains.loading ||
      budget.loading ||
      recentTasks.loading ||
      health.loading,
    [overview.loading, domains.loading, budget.loading, recentTasks.loading, health.loading]
  );

  const error = useMemo(
    () =>
      overview.error ||
      domains.error ||
      budget.error ||
      recentTasks.error ||
      health.error,
    [overview.error, domains.error, budget.error, recentTasks.error, health.error]
  );

  const refetchAll = useCallback(() => {
    overview.refetch();
    domains.refetch();
    budget.refetch();
    recentTasks.refetch();
    evaluationMode.refetch();
    benchmarkStatus.refetch();
    health.refetch();
  }, [overview, domains, budget, recentTasks, evaluationMode, benchmarkStatus, health]);

  return {
    overview: overview.data,
    domains: domains.data,
    budget: budget.data,
    recentTasks: recentTasks.data,
    evaluationMode: evaluationMode.mode,
    benchmarkStatus: benchmarkStatus.data,
    health: health.data,
    loading,
    error,
    refetchAll,
    setEvaluationMode: evaluationMode.setMode,
  };
}

export default useDashboard;
