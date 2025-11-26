import React, { useState } from 'react';
import { Skull, RotateCcw, Trash2, Search, Clock, TrendingDown } from 'lucide-react';
import { Header, Sidebar, MainContent, ContentHeader, ContentSection } from '../components/layout';
import { StatsCard, StatsGrid } from '../components/charts';

interface RetiredSpecialist {
  id: string;
  name: string;
  domain: string;
  generation: number;
  retired_at: string;
  reason: string;
  final_score: number;
  tasks_completed: number;
  lifespan_days: number;
}

// Mock graveyard data
const mockGraveyardData: RetiredSpecialist[] = [
  { id: 'sp-001', name: 'code-gen-v1', domain: 'coding', generation: 1, retired_at: '2024-01-10T08:00:00Z', reason: 'Low performance', final_score: 0.45, tasks_completed: 23, lifespan_days: 5 },
  { id: 'sp-002', name: 'debug-helper-v2', domain: 'coding', generation: 2, retired_at: '2024-01-12T14:30:00Z', reason: 'Superseded by better variant', final_score: 0.68, tasks_completed: 45, lifespan_days: 8 },
  { id: 'sp-003', name: 'doc-writer-v1', domain: 'documentation', generation: 1, retired_at: '2024-01-08T10:00:00Z', reason: 'Low performance', final_score: 0.52, tasks_completed: 12, lifespan_days: 3 },
  { id: 'sp-004', name: 'test-gen-v3', domain: 'testing', generation: 3, retired_at: '2024-01-14T16:00:00Z', reason: 'Pool convergence', final_score: 0.71, tasks_completed: 67, lifespan_days: 12 },
  { id: 'sp-005', name: 'refactor-v1', domain: 'coding', generation: 1, retired_at: '2024-01-05T09:00:00Z', reason: 'Experimental variant', final_score: 0.38, tasks_completed: 8, lifespan_days: 2 },
];

export const GraveyardPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'tasks'>('date');

  const filteredSpecialists = mockGraveyardData
    .filter(s =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.domain.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'date') return new Date(b.retired_at).getTime() - new Date(a.retired_at).getTime();
      if (sortBy === 'score') return b.final_score - a.final_score;
      return b.tasks_completed - a.tasks_completed;
    });

  const stats = {
    total: mockGraveyardData.length,
    avgScore: mockGraveyardData.reduce((sum, s) => sum + s.final_score, 0) / mockGraveyardData.length,
    totalTasks: mockGraveyardData.reduce((sum, s) => sum + s.tasks_completed, 0),
    avgLifespan: mockGraveyardData.reduce((sum, s) => sum + s.lifespan_days, 0) / mockGraveyardData.length,
  };

  const formatDate = (ts: string) => new Date(ts).toLocaleDateString();

  const getScoreColor = (score: number) => {
    if (score >= 0.7) return 'var(--accent-primary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  return (
    <div className="dashboard-layout">
      <Header systemHealth="healthy" />
      <Sidebar activePage="graveyard" />

      <MainContent>
        <ContentHeader
          title={
            <>
              <Skull className="icon" style={{ color: 'var(--text-tertiary)' }} />
              Specialist Graveyard
            </>
          }
          subtitle="Retired and superseded specialists"
        />

        {/* Summary Stats */}
        <ContentSection>
          <StatsGrid columns={4}>
            <StatsCard
              title="Total Retired"
              value={stats.total}
              icon={Skull}
            />
            <StatsCard
              title="Avg Final Score"
              value={stats.avgScore.toFixed(2)}
              icon={TrendingDown}
              variant="warning"
            />
            <StatsCard
              title="Total Tasks Run"
              value={stats.totalTasks}
              icon={Clock}
            />
            <StatsCard
              title="Avg Lifespan"
              value={`${stats.avgLifespan.toFixed(1)}d`}
              icon={Clock}
            />
          </StatsGrid>
        </ContentSection>

        {/* Filters */}
        <ContentSection>
          <div className="filters-bar">
            <div className="search-group">
              <Search className="icon-sm" />
              <input
                type="text"
                placeholder="Search specialists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="sort-group">
              <span>Sort by:</span>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}>
                <option value="date">Retirement Date</option>
                <option value="score">Final Score</option>
                <option value="tasks">Tasks Completed</option>
              </select>
            </div>
          </div>
        </ContentSection>

        {/* Graveyard List */}
        <ContentSection title="Retired Specialists">
          <div className="graveyard-list">
            {filteredSpecialists.length === 0 ? (
              <div className="empty-state">
                <Skull className="empty-icon" />
                <p>No retired specialists found</p>
              </div>
            ) : (
              filteredSpecialists.map(specialist => (
                <div key={specialist.id} className="graveyard-card">
                  <div className="card-header">
                    <div className="specialist-info">
                      <h3>{specialist.name}</h3>
                      <span className="domain-badge">{specialist.domain}</span>
                      <span className="generation">Gen {specialist.generation}</span>
                    </div>
                    <div className="card-actions">
                      <button className="action-btn" title="Resurrect specialist">
                        <RotateCcw className="icon-sm" />
                      </button>
                      <button className="action-btn danger" title="Permanently delete">
                        <Trash2 className="icon-sm" />
                      </button>
                    </div>
                  </div>

                  <div className="card-stats">
                    <div className="stat">
                      <span className="stat-label">Final Score</span>
                      <span className="stat-value" style={{ color: getScoreColor(specialist.final_score) }}>
                        {specialist.final_score.toFixed(3)}
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Tasks</span>
                      <span className="stat-value">{specialist.tasks_completed}</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Lifespan</span>
                      <span className="stat-value">{specialist.lifespan_days}d</span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Retired</span>
                      <span className="stat-value">{formatDate(specialist.retired_at)}</span>
                    </div>
                  </div>

                  <div className="card-reason">
                    <span className="reason-label">Reason:</span>
                    <span className="reason-text">{specialist.reason}</span>
                  </div>
                </div>
              ))
            )}
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

  .filters-bar {
    display: flex;
    gap: var(--space-4);
    flex-wrap: wrap;
    align-items: center;
  }

  .search-group {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
    flex: 1;
    min-width: 200px;
  }

  .search-group input {
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: var(--text-sm);
    outline: none;
    width: 100%;
  }

  .sort-group {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .sort-group select {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .graveyard-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .graveyard-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    transition: border-color var(--transition-fast);
  }

  .graveyard-card:hover {
    border-color: var(--border-secondary);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--space-3);
  }

  .specialist-info {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    flex-wrap: wrap;
  }

  .specialist-info h3 {
    font-size: var(--text-base);
    color: var(--text-primary);
    margin: 0;
  }

  .domain-badge {
    padding: var(--space-1) var(--space-2);
    background: var(--bg-tertiary);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    color: var(--text-secondary);
  }

  .generation {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    font-family: var(--font-mono);
  }

  .card-actions {
    display: flex;
    gap: var(--space-2);
  }

  .action-btn {
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
    transition: all var(--transition-fast);
  }

  .action-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .action-btn.danger:hover {
    background: var(--accent-danger-dim);
    border-color: var(--accent-danger);
    color: var(--accent-danger);
  }

  .card-stats {
    display: flex;
    gap: var(--space-6);
    margin-bottom: var(--space-3);
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .stat-label {
    font-size: var(--text-xs);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: var(--text-sm);
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
    font-family: var(--font-mono);
  }

  .card-reason {
    padding-top: var(--space-3);
    border-top: 1px solid var(--border-primary);
    font-size: var(--text-sm);
  }

  .reason-label {
    color: var(--text-tertiary);
    margin-right: var(--space-2);
  }

  .reason-text {
    color: var(--text-secondary);
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-12);
    color: var(--text-tertiary);
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    margin-bottom: var(--space-4);
    opacity: 0.5;
  }
`;

export default GraveyardPage;
