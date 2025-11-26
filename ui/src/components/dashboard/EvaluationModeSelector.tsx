import React from 'react';
import { Scale, Users, GitCompare } from 'lucide-react';
import type { EvaluationMode } from '../../types';

export interface EvaluationModeSelectorProps {
  mode: EvaluationMode;
  onChange: (mode: EvaluationMode) => void;
  disabled?: boolean;
}

export const EvaluationModeSelector: React.FC<EvaluationModeSelectorProps> = ({
  mode,
  onChange,
  disabled = false,
}) => {
  const modes: Array<{
    value: EvaluationMode;
    label: string;
    icon: React.ReactNode;
    description: string;
  }> = [
    {
      value: 'scoring_committee',
      label: 'Scoring Committee',
      icon: <Scale className="icon-md" />,
      description: 'Multi-checker evaluation',
    },
    {
      value: 'ai_council',
      label: 'AI Council',
      icon: <Users className="icon-md" />,
      description: 'Bootstrap consensus voting',
    },
    {
      value: 'both',
      label: 'Both (Compare)',
      icon: <GitCompare className="icon-md" />,
      description: 'Run both and compare',
    },
  ];

  return (
    <div className="evaluation-selector">
      <div className="evaluation-selector-label">Evaluation Mode</div>
      <div className="evaluation-selector-options">
        {modes.map((m) => (
          <button
            key={m.value}
            className={`evaluation-option ${mode === m.value ? 'active' : ''}`}
            onClick={() => onChange(m.value)}
            disabled={disabled}
          >
            <div className="evaluation-option-icon">{m.icon}</div>
            <div className="evaluation-option-info">
              <div className="evaluation-option-label">{m.label}</div>
              <div className="evaluation-option-desc">{m.description}</div>
            </div>
          </button>
        ))}
      </div>

      <style>{`
        .evaluation-selector {
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
          padding: var(--space-4);
        }

        .evaluation-selector-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-secondary);
          margin-bottom: var(--space-3);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .evaluation-selector-options {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: var(--space-2);
        }

        .evaluation-option {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: var(--space-3);
          background: var(--bg-primary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }

        .evaluation-option:hover:not(:disabled) {
          border-color: var(--accent-primary);
        }

        .evaluation-option.active {
          background: var(--accent-primary-dim);
          border-color: var(--accent-primary);
        }

        .evaluation-option:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .evaluation-option-icon {
          color: var(--text-tertiary);
        }

        .evaluation-option.active .evaluation-option-icon {
          color: var(--accent-primary);
        }

        .evaluation-option-info {
          flex: 1;
        }

        .evaluation-option-label {
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-primary);
        }

        .evaluation-option.active .evaluation-option-label {
          color: var(--accent-primary);
        }

        .evaluation-option-desc {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          margin-top: 2px;
        }

        @media (max-width: 768px) {
          .evaluation-selector-options {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default EvaluationModeSelector;
