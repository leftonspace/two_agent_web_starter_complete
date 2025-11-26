import React, { useState } from 'react';
import type { EvaluationMode, EvaluationStatus } from '../types';
import { evaluationApi } from '../api/client';

interface EvaluationToggleProps {
  evaluation: EvaluationStatus;
  onModeChange?: (mode: EvaluationMode) => void;
}

const modes: { value: EvaluationMode; label: string; description: string; icon: string }[] = [
  {
    value: 'scoring_committee',
    label: 'Scoring Committee',
    description: 'Tests + Your Feedback',
    icon: '📋',
  },
  {
    value: 'ai_council',
    label: 'AI Council',
    description: 'Specialists Vote',
    icon: '🤖',
  },
  {
    value: 'both',
    label: 'Both',
    description: 'Compare Results',
    icon: '⚖️',
  },
];

export const EvaluationToggle: React.FC<EvaluationToggleProps> = ({
  evaluation,
  onModeChange,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleModeChange = async (mode: EvaluationMode) => {
    if (mode === evaluation.mode || loading) return;

    setLoading(true);
    setError(null);

    try {
      await evaluationApi.setMode(mode);
      onModeChange?.(mode);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change mode');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header mb-0">Evaluation Mode</h3>
        {error && (
          <span className="text-sm text-red-600">{error}</span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {modes.map(mode => (
          <button
            key={mode.value}
            onClick={() => handleModeChange(mode.value)}
            disabled={loading}
            className={`
              p-4 rounded-lg border-2 text-left transition-all
              ${evaluation.mode === mode.value
                ? 'border-jarvis-500 bg-jarvis-50'
                : 'border-gray-200 hover:border-gray-300 bg-white'
              }
              ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">{mode.icon}</span>
              <span className="font-semibold text-gray-800">{mode.label}</span>
              {evaluation.mode === mode.value && (
                <span className="ml-auto text-jarvis-600">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-500">{mode.description}</p>
          </button>
        ))}
      </div>

      {/* Status Indicators */}
      <div className="flex gap-4 mt-4 pt-4 border-t">
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              evaluation.scoring_committee_enabled ? 'bg-green-500' : 'bg-gray-300'
            }`}
          />
          <span className="text-gray-600">Scoring Committee</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`w-2 h-2 rounded-full ${
              evaluation.ai_council_enabled ? 'bg-green-500' : 'bg-gray-300'
            }`}
          />
          <span className="text-gray-600">AI Council</span>
        </div>
        {evaluation.comparison_tracking && (
          <div className="flex items-center gap-2 text-sm">
            <span className="w-2 h-2 rounded-full bg-blue-500" />
            <span className="text-gray-600">Comparison Tracking</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationToggle;
