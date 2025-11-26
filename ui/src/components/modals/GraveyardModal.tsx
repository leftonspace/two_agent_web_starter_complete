import React, { useState } from 'react';
import { Skull, Brain, Calendar, RotateCcw, Trash2, Search } from 'lucide-react';
import type { SpecialistSummary } from '../../types';
import { Modal, Button, Input, Badge } from '../common';

export interface GraveyardEntry extends SpecialistSummary {
  retired_at: string;
  reason?: string;
  final_score: number;
  lifetime_tasks: number;
}

export interface GraveyardModalProps {
  isOpen: boolean;
  onClose: () => void;
  entries?: GraveyardEntry[];
  onRestore?: (specialistId: string) => void;
  onPermanentDelete?: (specialistId: string) => void;
  loading?: boolean;
}

export const GraveyardModal: React.FC<GraveyardModalProps> = ({
  isOpen,
  onClose,
  entries = [],
  onRestore,
  onPermanentDelete,
  loading = false,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filteredEntries = entries.filter(
    (entry) =>
      entry.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entry.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.85) return 'var(--accent-primary)';
    if (score >= 0.7) return 'var(--accent-secondary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Specialist Graveyard" size="lg">
      <div className="graveyard-modal">
        {/* Header */}
        <div className="graveyard-header">
          <div className="header-icon">
            <Skull className="icon-lg" />
          </div>
          <div className="header-info">
            <p className="header-description">
              Retired specialists that underperformed or were replaced by evolution.
              You can restore them or permanently delete them.
            </p>
            <Badge variant="ghost" size="sm">
              {entries.length} retired specialists
            </Badge>
          </div>
        </div>

        {/* Search */}
        <div className="graveyard-search">
          <Input
            placeholder="Search by name or ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            icon={Search}
          />
        </div>

        {/* List */}
        <div className="graveyard-list">
          {loading ? (
            <div className="graveyard-loading">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton skeleton-card" style={{ height: '80px' }} />
              ))}
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="graveyard-empty">
              {searchQuery ? (
                <p>No specialists match your search.</p>
              ) : (
                <>
                  <Skull className="icon-xl empty-icon" />
                  <p>The graveyard is empty.</p>
                  <p className="empty-hint">No specialists have been retired yet.</p>
                </>
              )}
            </div>
          ) : (
            filteredEntries.map((entry) => (
              <div
                key={entry.id}
                className={`graveyard-entry ${selectedId === entry.id ? 'selected' : ''}`}
                onClick={() => setSelectedId(selectedId === entry.id ? null : entry.id)}
              >
                <div className="entry-icon">
                  <Brain className="icon" />
                </div>
                <div className="entry-info">
                  <div className="entry-name">{entry.name}</div>
                  <div className="entry-meta">
                    <span className="entry-id">#{entry.id.slice(0, 8)}</span>
                    {entry.generation !== undefined && (
                      <>
                        <span className="separator">•</span>
                        <span>Gen {entry.generation}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="entry-stats">
                  <div className="stat">
                    <span className="stat-value" style={{ color: getScoreColor(entry.final_score || 0) }}>
                      {(entry.final_score || 0).toFixed(3)}
                    </span>
                    <span className="stat-label">Final Score</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{entry.lifetime_tasks}</span>
                    <span className="stat-label">Tasks</span>
                  </div>
                </div>
                <div className="entry-date">
                  <Calendar className="icon-xs" />
                  {formatDate(entry.retired_at)}
                </div>

                {selectedId === entry.id && (
                  <div className="entry-details">
                    {entry.reason && (
                      <div className="entry-reason">
                        <strong>Reason:</strong> {entry.reason}
                      </div>
                    )}
                    <div className="entry-actions">
                      {onRestore && (
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={RotateCcw}
                          onClick={(e) => {
                            e.stopPropagation();
                            onRestore(entry.id);
                          }}
                        >
                          Restore
                        </Button>
                      )}
                      {onPermanentDelete && (
                        <Button
                          variant="danger"
                          size="sm"
                          icon={Trash2}
                          onClick={(e) => {
                            e.stopPropagation();
                            onPermanentDelete(entry.id);
                          }}
                        >
                          Delete Forever
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <style>{`
        .graveyard-modal {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .graveyard-header {
          display: flex;
          gap: var(--space-4);
          padding: var(--space-4);
          background: var(--bg-tertiary);
          border-radius: var(--radius-lg);
        }

        .header-icon {
          width: 56px;
          height: 56px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--accent-danger-dim);
          color: var(--accent-danger);
          border-radius: var(--radius-lg);
          flex-shrink: 0;
        }

        .header-info {
          flex: 1;
        }

        .header-description {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-bottom: var(--space-2);
        }

        .graveyard-search {
          margin-bottom: var(--space-2);
        }

        .graveyard-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
          max-height: 400px;
          overflow-y: auto;
        }

        .graveyard-entry {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .graveyard-entry:hover {
          border-color: var(--border-secondary);
        }

        .graveyard-entry.selected {
          border-color: var(--accent-danger);
          background: var(--accent-danger-dim);
        }

        .entry-icon {
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-secondary);
          border-radius: var(--radius-md);
          color: var(--text-tertiary);
        }

        .entry-info {
          flex: 1;
          min-width: 120px;
        }

        .entry-name {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
        }

        .entry-meta {
          display: flex;
          gap: var(--space-1);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .entry-id {
          font-family: var(--font-mono);
        }

        .separator {
          color: var(--border-primary);
        }

        .entry-stats {
          display: flex;
          gap: var(--space-4);
        }

        .stat {
          text-align: center;
        }

        .stat-value {
          display: block;
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }

        .stat-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .entry-date {
          display: flex;
          align-items: center;
          gap: var(--space-1);
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .entry-details {
          width: 100%;
          padding-top: var(--space-3);
          margin-top: var(--space-2);
          border-top: 1px solid var(--border-primary);
        }

        .entry-reason {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-bottom: var(--space-3);
        }

        .entry-actions {
          display: flex;
          gap: var(--space-2);
        }

        .graveyard-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: var(--space-8);
          color: var(--text-tertiary);
          text-align: center;
        }

        .empty-icon {
          margin-bottom: var(--space-3);
          opacity: 0.5;
        }

        .empty-hint {
          font-size: var(--text-sm);
          margin-top: var(--space-2);
        }

        .graveyard-loading {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }
      `}</style>
    </Modal>
  );
};

export default GraveyardModal;
