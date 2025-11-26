import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Brain, ArrowLeft, TrendingUp, Clock, Users, Zap, RefreshCw } from 'lucide-react';
import { Header, Sidebar, MainContent, ContentHeader, ContentSection } from '../components/layout';
import { StatsCard, StatsGrid, ScoreLineChart } from '../components/charts';
import { TasksTable, SpecialistRow } from '../components/dashboard';
import type { DomainDetail, SpecialistSummary, TaskExecution } from '../types';
import { api } from '../api/client';

export const DomainDetailPage: React.FC = () => {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [domain, setDomain] = useState<DomainDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!name) return;

    const fetchDomain = async () => {
      setLoading(true);
      try {
        const data = await api.dashboard.getDomainDetail(name);
        setDomain(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load domain'));
      } finally {
        setLoading(false);
      }
    };

    fetchDomain();
  }, [name]);

  // Score history will be populated from real data
  const scoreHistory: Array<{ timestamp: string; score: number; label: string }> = [];

  // Convert specialists for display
  const specialists: SpecialistSummary[] = domain?.specialists?.map(s => ({
    id: s.id,
    name: s.name,
    score: s.score,
    status: s.status || 'active',
    tasks_completed: s.tasks_completed || 0,
    generation: s.generation,
    trend: Math.random() > 0.5 ? 'up' : 'down',
  })) || [];

  // Tasks will be populated from real data
  const tasks: TaskExecution[] = [];

  if (loading) {
    return (
      <div className="dashboard-layout">
        <Header systemHealth="healthy" />
        <Sidebar activePage="dashboard" />
        <MainContent>
          <div className="loading-state">
            <RefreshCw className="spinning" />
            <p>Loading domain...</p>
          </div>
        </MainContent>
        <style>{styles}</style>
      </div>
    );
  }

  if (error || !domain) {
    return (
      <div className="dashboard-layout">
        <Header systemHealth="healthy" />
        <Sidebar activePage="dashboard" />
        <MainContent>
          <div className="error-state">
            <h2>Failed to load domain</h2>
            <p>{error?.message || 'Domain not found'}</p>
            <button onClick={() => navigate('/')}>
              <ArrowLeft className="icon-sm" />
              Back to Dashboard
            </button>
          </div>
        </MainContent>
        <style>{styles}</style>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      <Header systemHealth="healthy" />
      <Sidebar activePage="dashboard" />

      <MainContent>
        <ContentHeader
          title={
            <>
              <button className="back-btn" onClick={() => navigate('/')}>
                <ArrowLeft className="icon-sm" />
              </button>
              <Brain className="icon" style={{ color: 'var(--accent-primary)' }} />
              {domain.name}
            </>
          }
          subtitle={`Domain pool with ${domain.specialists?.length || 0} specialists`}
          actions={
            <div className="header-actions">
              <button className="action-btn">
                <Zap className="icon-sm" />
                Force Evolution
              </button>
              <button className="action-btn primary">
                <RefreshCw className="icon-sm" />
                Refresh
              </button>
            </div>
          }
        />

        {/* Domain Stats */}
        <ContentSection>
          <StatsGrid columns={4}>
            <StatsCard
              title="Specialists"
              value={domain.specialists?.length || 0}
              icon={Users}
              variant="primary"
            />
            <StatsCard
              title="Avg Score"
              value={(domain.avg_score || 0).toFixed(3)}
              icon={TrendingUp}
              variant="success"
            />
            <StatsCard
              title="Best Score"
              value={(domain.best_score || 0).toFixed(3)}
              icon={TrendingUp}
            />
            <StatsCard
              title="Tasks Today"
              value={domain.tasks_today || 0}
              icon={Clock}
            />
          </StatsGrid>
        </ContentSection>

        {/* Score Trend */}
        <ContentSection title="Score Trend">
          <ScoreLineChart
            data={scoreHistory}
            height={300}
            title=""
            fill={true}
          />
        </ContentSection>

        {/* Specialists */}
        <ContentSection title="Specialists">
          <div className="specialists-list">
            {specialists.length === 0 ? (
              <div className="empty-state">
                <Users className="empty-icon" />
                <p>No specialists in this domain</p>
              </div>
            ) : (
              specialists.map(specialist => (
                <SpecialistRow
                  key={specialist.id}
                  specialist={specialist}
                  onClick={() => console.log('View specialist:', specialist.id)}
                />
              ))
            )}
          </div>
        </ContentSection>

        {/* Recent Tasks */}
        <ContentSection title="Recent Tasks">
          <TasksTable
            tasks={tasks}
            emptyMessage="No recent tasks in this domain"
          />
        </ContentSection>

        {/* Evolution Status */}
        <ContentSection title="Evolution Status">
          <div className="evolution-status">
            <div className="evolution-stat">
              <span className="stat-label">Convergence Progress</span>
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${(domain.convergence_progress || 0) * 100}%` }}
                />
              </div>
              <span className="stat-value">{((domain.convergence_progress || 0) * 100).toFixed(1)}%</span>
            </div>
            <div className="evolution-info">
              <div className="info-item">
                <span className="info-label">Evolution Status</span>
                <span className={`info-value ${domain.evolution_paused ? 'paused' : 'active'}`}>
                  {domain.evolution_paused ? 'Paused' : 'Active'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Generation</span>
                <span className="info-value">
                  {Math.max(...(specialists.map(s => s.generation || 0)), 0)}
                </span>
              </div>
            </div>
          </div>
        </ContentSection>
      </MainContent>

      <style>{styles}</style>
    </div>
  );
};

const styles = `
  .dashboard-layout {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .back-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    margin-right: var(--space-2);
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .header-actions {
    display: flex;
    gap: var(--space-2);
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-weight: var(--weight-medium);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .action-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .action-btn.primary {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: var(--bg-primary);
  }

  .action-btn.primary:hover {
    opacity: 0.9;
  }

  .loading-state,
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    color: var(--text-tertiary);
  }

  .loading-state .spinning {
    animation: spin 1s linear infinite;
    margin-bottom: var(--space-4);
  }

  .error-state h2 {
    color: var(--text-primary);
    margin-bottom: var(--space-2);
  }

  .error-state button {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-4);
    padding: var(--space-2) var(--space-4);
    background: var(--accent-primary);
    border: none;
    border-radius: var(--radius-md);
    color: var(--bg-primary);
    cursor: pointer;
  }

  .specialists-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: var(--space-8);
    color: var(--text-tertiary);
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    margin-bottom: var(--space-4);
    opacity: 0.5;
  }

  .evolution-status {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
  }

  .evolution-stat {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    margin-bottom: var(--space-4);
  }

  .stat-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    min-width: 150px;
  }

  .progress-bar {
    flex: 1;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--accent-primary);
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .stat-value {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    color: var(--text-primary);
    min-width: 60px;
    text-align: right;
  }

  .evolution-info {
    display: flex;
    gap: var(--space-8);
    padding-top: var(--space-4);
    border-top: 1px solid var(--border-primary);
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .info-label {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .info-value {
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
  }

  .info-value.active {
    color: var(--accent-primary);
  }

  .info-value.paused {
    color: var(--accent-warning);
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;

export default DomainDetailPage;
