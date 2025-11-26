/**
 * JARVIS Dashboard API Client
 */

import type {
  DashboardOverview,
  DomainDetail,
  SpecialistDetail,
  BudgetStatus,
  EvaluationMode,
  ScoringCommitteeStats,
  AICouncilStats,
  ComparisonStats,
  BenchmarkStatus,
  BenchmarkInfo,
  BenchmarkRunSummary,
  BenchmarkDiscovery,
  TaskSummary,
  TaskDetail,
  FeedbackStats,
  HealthResponse,
  SpecialistSummary,
} from '../types';

const API_BASE = '/api';

// ============================================================================
// Helper Functions
// ============================================================================

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Dashboard API
// ============================================================================

export const dashboardApi = {
  getOverview: () => fetchJson<DashboardOverview>('/dashboard/overview'),

  getDomains: () => fetchJson<DomainDetail[]>('/dashboard/domains'),

  getDomainDetail: (domain: string) =>
    fetchJson<DomainDetail>(`/dashboard/domains/${domain}`),

  getSpecialists: (params?: { domain?: string; active_only?: boolean; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.domain) searchParams.set('domain', params.domain);
    if (params?.active_only !== undefined) searchParams.set('active_only', String(params.active_only));
    if (params?.limit) searchParams.set('limit', String(params.limit));
    const query = searchParams.toString();
    return fetchJson<SpecialistSummary[]>(`/dashboard/specialists${query ? `?${query}` : ''}`);
  },

  getSpecialistDetail: (id: string) =>
    fetchJson<SpecialistDetail>(`/dashboard/specialists/${id}`),

  getBudget: () => fetchJson<BudgetStatus>('/dashboard/budget'),

  getStats: () => fetchJson<Record<string, unknown>>('/dashboard/stats'),
};

// ============================================================================
// Evaluation API
// ============================================================================

export const evaluationApi = {
  getMode: () =>
    fetchJson<{ mode: EvaluationMode; scoring_committee_enabled: boolean; ai_council_enabled: boolean }>('/evaluation/mode'),

  setMode: (mode: EvaluationMode) =>
    fetchJson<{ mode: EvaluationMode }>('/evaluation/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),

  getStats: () =>
    fetchJson<{
      mode: string;
      scoring_committee: ScoringCommitteeStats;
      ai_council: AICouncilStats;
      comparison: ComparisonStats | null;
    }>('/evaluation/stats'),

  getScoringCommitteeStats: () =>
    fetchJson<ScoringCommitteeStats>('/evaluation/scoring-committee/stats'),

  getAICouncilStats: () =>
    fetchJson<AICouncilStats>('/evaluation/ai-council/stats'),

  getComparisonStats: () =>
    fetchJson<ComparisonStats>('/evaluation/comparison-stats'),

  resetStats: () =>
    fetchJson<{ status: string }>('/evaluation/reset-stats', { method: 'POST' }),
};

// ============================================================================
// Benchmark API
// ============================================================================

export const benchmarkApi = {
  getStatus: () => fetchJson<BenchmarkStatus>('/benchmark/status'),

  discover: () => fetchJson<BenchmarkDiscovery>('/benchmark/discover'),

  list: (domain?: string) => {
    const query = domain ? `?domain=${domain}` : '';
    return fetchJson<BenchmarkInfo[]>(`/benchmark/list${query}`);
  },

  run: (params?: { domain?: string; benchmark_name?: string }) =>
    fetchJson<{ status: string; message: string; run_id?: string }>('/benchmark/run', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    }),

  pause: () =>
    fetchJson<{ status: string; message: string }>('/benchmark/pause', { method: 'POST' }),

  resume: () =>
    fetchJson<{ status: string; message: string }>('/benchmark/resume', { method: 'POST' }),

  cancel: () =>
    fetchJson<{ status: string; message: string }>('/benchmark/cancel', { method: 'POST' }),

  getHistory: (params?: { limit?: number; domain?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.domain) searchParams.set('domain', params.domain);
    const query = searchParams.toString();
    return fetchJson<BenchmarkRunSummary[]>(`/benchmark/history${query ? `?${query}` : ''}`);
  },

  getRunDetail: (runId: string) =>
    fetchJson<BenchmarkRunSummary>(`/benchmark/history/${runId}`),

  getStats: () => fetchJson<Record<string, unknown>>('/benchmark/stats'),
};

// ============================================================================
// Tasks API
// ============================================================================

export const tasksApi = {
  getRecent: (params?: { limit?: number; domain?: string; specialist_id?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.domain) searchParams.set('domain', params.domain);
    if (params?.specialist_id) searchParams.set('specialist_id', params.specialist_id);
    const query = searchParams.toString();
    return fetchJson<TaskSummary[]>(`/tasks/recent${query ? `?${query}` : ''}`);
  },

  getTaskDetail: (taskId: string) =>
    fetchJson<TaskDetail>(`/tasks/${taskId}`),

  submitFeedback: (taskId: string, feedback: {
    rating: number;
    feedback_type?: string;
    comment?: string;
    would_use_again?: boolean;
  }) =>
    fetchJson<{ status: string; feedback_id?: string; score_impact?: number }>(`/tasks/${taskId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    }),

  getPendingFeedback: (limit?: number) => {
    const query = limit ? `?limit=${limit}` : '';
    return fetchJson<TaskSummary[]>(`/tasks/pending-feedback${query}`);
  },

  getFeedbackStats: () => fetchJson<FeedbackStats>('/tasks/feedback/stats'),

  getBySpecialist: (specialistId: string, limit?: number) => {
    const query = limit ? `?limit=${limit}` : '';
    return fetchJson<TaskSummary[]>(`/tasks/by-specialist/${specialistId}${query}`);
  },

  getByDomain: (domain: string, limit?: number) => {
    const query = limit ? `?limit=${limit}` : '';
    return fetchJson<TaskSummary[]>(`/tasks/by-domain/${domain}${query}`);
  },
};

// ============================================================================
// Health API
// ============================================================================

export const healthApi = {
  check: () => fetch('/health').then(r => r.json()) as Promise<HealthResponse>,

  getVersion: () => fetch('/version').then(r => r.json()) as Promise<{
    api_version: string;
    jarvis_version: string;
  }>,
};

// ============================================================================
// Combined API
// ============================================================================

export const api = {
  dashboard: dashboardApi,
  evaluation: evaluationApi,
  benchmark: benchmarkApi,
  tasks: tasksApi,
  health: healthApi,
};

export default api;
