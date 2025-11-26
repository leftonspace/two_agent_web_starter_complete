/**
 * JARVIS Dashboard Type Definitions
 */

// ============================================================================
// Domain Types
// ============================================================================

export interface DomainStatus {
  name: string;
  specialists: number;
  best_score: number;
  avg_score: number;
  evolution_paused: boolean;
  convergence_progress: number;
  tasks_today: number;
  current_jarvis: string | null;
}

export interface SpecialistSummary {
  id: string;
  name: string;
  generation: number;
  score: number;
  task_count: number;
  is_active: boolean;
}

export interface SpecialistDetail extends SpecialistSummary {
  domain: string;
  created_at: string;
  total_tasks: number;
  successful_tasks: number;
  success_rate: number;
  avg_score: number;
  recent_scores: number[];
  system_prompt_preview: string;
  model_preference: string | null;
  temperature: number;
  parent_id: string | null;
  mutation_summary: string | null;
  learnings_applied: number;
}

export interface DomainDetail {
  name: string;
  description: string;
  specialists: SpecialistSummary[];
  pool_size: number;
  min_pool_size: number;
  max_pool_size: number;
  evolution_paused: boolean;
  pause_reason: string | null;
  generations_completed: number;
  convergence_status: Record<string, unknown>;
  tasks_today: number;
  tasks_total: number;
  avg_score: number;
  best_score: number;
  score_trend: 'improving' | 'stable' | 'declining';
  recent_tasks: TaskSummary[];
  last_evolution_at: string | null;
}

// ============================================================================
// Budget Types
// ============================================================================

export interface BudgetStatus {
  production_spent_today: number;
  production_remaining: number;
  production_limit: number;
  benchmark_spent_today: number;
  benchmark_remaining: number;
  benchmark_limit: number;
  is_warning: boolean;
  warning_threshold: number;
}

// ============================================================================
// Evaluation Types
// ============================================================================

export interface EvaluationStatus {
  mode: EvaluationMode;
  scoring_committee_enabled: boolean;
  ai_council_enabled: boolean;
  comparison_tracking: boolean;
}

export type EvaluationMode = 'scoring_committee' | 'ai_council' | 'both';

export interface ScoringCommitteeStats {
  total_evaluations: number;
  avg_score: number;
  avg_confidence: number;
  checkers_active: string[];
  recent_scores: number[];
}

export interface AICouncilStats {
  total_sessions: number;
  total_votes: number;
  outliers_removed: number;
  avg_score: number;
  avg_confidence: number;
  bootstrap_warnings: number;
  voter_count: number;
}

export interface ComparisonStats {
  comparisons_count: number;
  agreement_rate: number;
  correlation: number;
  mean_difference: number;
  std_difference: number;
  recent_comparisons: ComparisonEntry[];
}

export interface ComparisonEntry {
  task_id: string;
  sc_score: number;
  ac_score: number;
  difference: number;
  timestamp: string;
}

// ============================================================================
// Benchmark Types
// ============================================================================

export interface BenchmarkInfo {
  name: string;
  domain: string;
  version: string;
  description: string;
  task_count: number;
  easy_count: number;
  medium_count: number;
  hard_count: number;
}

export interface BenchmarkStatus {
  is_running: boolean;
  is_paused: boolean;
  current_run: BenchmarkRunSummary | null;
  progress_percent: number;
  current_task: string | null;
  estimated_completion: string | null;
}

export interface BenchmarkRunSummary {
  id: string;
  benchmark_name: string;
  domain: string;
  status: 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  tasks_completed: number;
  tasks_total: number;
  avg_score: number;
  pass_rate: number;
  cost_spent: number;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

export interface BenchmarkDiscovery {
  domains: Record<string, string[]>;
  total_benchmarks: number;
}

// ============================================================================
// Task Types
// ============================================================================

export interface TaskSummary {
  id: string;
  domain: string;
  specialist_id: string | null;
  specialist_name: string | null;
  request_preview: string;
  response_preview: string;
  score: number | null;
  model_used: string;
  execution_time_ms: number;
  cost_cad: number;
  created_at: string;
  has_feedback: boolean;
}

export interface TaskDetail extends TaskSummary {
  request: string;
  response: string;
  evaluation_details: Record<string, unknown> | null;
  tokens_used: number;
  feedback: UserFeedback | null;
}

export interface UserFeedback {
  rating: number;
  feedback_type: 'helpful' | 'accurate' | 'fast' | 'creative' | 'other';
  comment: string | null;
  would_use_again: boolean;
  created_at: string;
}

export interface FeedbackStats {
  total_feedback: number;
  positive_rate: number;
  avg_rating: number;
  pending_count: number;
  feedback_by_domain: Record<string, number>;
}

// ============================================================================
// Dashboard Overview
// ============================================================================

export interface DashboardOverview {
  domains: DomainStatus[];
  budget: BudgetStatus;
  evaluation: EvaluationStatus;
  total_tasks_today: number;
  total_specialists: number;
  system_health: 'healthy' | 'degraded' | 'unhealthy';
  last_updated: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  services: Record<string, string>;
}
