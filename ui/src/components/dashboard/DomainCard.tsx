import React, { useState } from 'react';
import { ChevronDown, Terminal, Code, FileText } from 'lucide-react';
import type { DomainStatus, SpecialistSummary } from '../../types';
import { Badge, ProgressBar } from '../common';
import { SpecialistRow } from './SpecialistRow';

export interface DomainCardProps {
  domain: DomainStatus;
  specialists?: SpecialistSummary[];
  onSpecialistClick?: (specialist: SpecialistSummary) => void;
  onClick?: () => void;
  loading?: boolean;
}

const domainIcons: Record<string, React.ElementType> = {
  administration: Terminal,
  code_generation: Code,
  business_documents: FileText,
};

export const DomainCard: React.FC<DomainCardProps> = ({
  domain,
  specialists = [],
  onSpecialistClick,
  onClick: _onClick,
  loading = false,
}) => {
  const [expanded, setExpanded] = useState(false);

  const Icon = domainIcons[domain.name.toLowerCase().replace(/\s+/g, '_')] || Terminal;

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return 'var(--accent-primary)';
    if (score >= 0.7) return 'var(--accent-secondary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  return (
    <div className={`domain-card ${expanded ? 'expanded' : ''}`}>
      <div
        className="domain-card-header"
        onClick={() => setExpanded(!expanded)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && setExpanded(!expanded)}
      >
        <div className="domain-card-icon">
          <Icon className="icon-lg" />
        </div>
        <div className="domain-card-info">
          <div className="domain-card-name">{domain.name}</div>
          <div className="domain-card-meta">
            <span>{domain.specialists} specialists</span>
            <span className="separator">|</span>
            <span>Avg: {domain.avg_score.toFixed(2)}</span>
          </div>
        </div>
        <div className="domain-card-stats">
          <div className="domain-stat">
            <div className="domain-stat-value">{domain.tasks_today}</div>
            <div className="domain-stat-label">Tasks</div>
          </div>
          <div className="domain-stat">
            <div
              className="domain-stat-value"
              style={{ color: getScoreColor(domain.best_score) }}
            >
              {domain.best_score.toFixed(2)}
            </div>
            <div className="domain-stat-label">Best</div>
          </div>
        </div>
        <div className={`domain-card-expand ${expanded ? 'rotated' : ''}`}>
          <ChevronDown className="icon" />
        </div>
      </div>

      {domain.evolution_paused && (
        <div className="domain-card-warning">
          <Badge variant="warning" size="sm" dot>Evolution Paused</Badge>
        </div>
      )}

      {expanded && (
        <div className="domain-card-body">
          <div className="domain-convergence">
            <div className="convergence-label">Convergence Progress</div>
            <ProgressBar
              value={domain.convergence_progress * 100}
              size="sm"
              variant={domain.convergence_progress >= 0.9 ? 'primary' : 'warning'}
            />
          </div>

          <div className="specialist-list">
            {loading ? (
              <div className="skeleton skeleton-card" style={{ height: '60px' }} />
            ) : specialists.length > 0 ? (
              specialists.map((specialist) => (
                <SpecialistRow
                  key={specialist.id}
                  specialist={specialist}
                  onClick={() => onSpecialistClick?.(specialist)}
                />
              ))
            ) : (
              <div className="empty-specialists">No specialists in this domain</div>
            )}
          </div>
        </div>
      )}

      <style>{`
        .domain-card {
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          overflow: hidden;
          transition: all var(--transition-fast);
        }

        .domain-card:hover {
          border-color: var(--border-secondary);
        }

        .domain-card.expanded {
          border-color: var(--accent-primary);
        }

        .domain-card-header {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-4);
          cursor: pointer;
        }

        .domain-card-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
          border-radius: var(--radius-md);
          flex-shrink: 0;
        }

        .domain-card-info {
          flex: 1;
          min-width: 0;
        }

        .domain-card-name {
          font-size: var(--text-md);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .domain-card-meta {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          display: flex;
          gap: var(--space-2);
        }

        .separator {
          color: var(--border-primary);
        }

        .domain-card-stats {
          display: flex;
          gap: var(--space-4);
        }

        .domain-stat {
          text-align: center;
        }

        .domain-stat-value {
          font-size: var(--text-lg);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .domain-stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .domain-card-expand {
          color: var(--text-tertiary);
          transition: transform var(--transition-fast);
        }

        .domain-card-expand.rotated {
          transform: rotate(180deg);
        }

        .domain-card-warning {
          padding: 0 var(--space-4) var(--space-3);
        }

        .domain-card-body {
          padding: 0 var(--space-4) var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .domain-convergence {
          padding: var(--space-3) 0;
        }

        .convergence-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin-bottom: var(--space-2);
        }

        .specialist-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .empty-specialists {
          text-align: center;
          color: var(--text-tertiary);
          font-size: var(--text-sm);
          padding: var(--space-4);
        }
      `}</style>
    </div>
  );
};

export default DomainCard;
