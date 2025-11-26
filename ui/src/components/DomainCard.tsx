import React, { useEffect, useState } from 'react';
import type { DomainStatus, SpecialistSummary } from '../types';
import { dashboardApi } from '../api/client';

interface DomainCardProps {
  domain: DomainStatus;
  onClick?: () => void;
}

export const DomainCard: React.FC<DomainCardProps> = ({ domain, onClick }) => {
  const [specialists, setSpecialists] = useState<SpecialistSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSpecialists();
  }, [domain.name]);

  const loadSpecialists = async () => {
    try {
      const data = await dashboardApi.getSpecialists({
        domain: domain.name,
        active_only: true,
        limit: 5,
      });
      setSpecialists(data);
    } catch (error) {
      console.error('Failed to load specialists:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDomainName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div
      className="card hover:shadow-lg transition-shadow cursor-pointer"
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">
            {formatDomainName(domain.name)}
          </h3>
          {domain.current_jarvis && (
            <span className="badge badge-info mt-1">
              JARVIS: {domain.current_jarvis}
            </span>
          )}
        </div>
        <span
          className={`badge ${domain.evolution_paused ? 'badge-warning' : 'badge-success'}`}
        >
          {domain.evolution_paused ? 'Paused' : 'Active'}
        </span>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-center">
        <div>
          <div className="text-2xl font-bold text-gray-800">{domain.specialists}</div>
          <div className="text-xs text-gray-500">Specialists</div>
        </div>
        <div>
          <div className={`text-2xl font-bold ${getScoreColor(domain.best_score)}`}>
            {(domain.best_score * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-gray-500">Best Score</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-800">{domain.tasks_today}</div>
          <div className="text-xs text-gray-500">Today</div>
        </div>
      </div>

      {/* Convergence Progress */}
      {domain.convergence_progress > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Convergence</span>
            <span>{domain.convergence_progress.toFixed(0)}%</span>
          </div>
          <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-jarvis-500 transition-all"
              style={{ width: `${domain.convergence_progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Specialist Rankings */}
      <div className="border-t pt-3">
        <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
          Top Specialists
        </h4>
        {loading ? (
          <div className="text-sm text-gray-400">Loading...</div>
        ) : specialists.length === 0 ? (
          <div className="text-sm text-gray-400">No specialists yet</div>
        ) : (
          <div className="space-y-1">
            {specialists.slice(0, 3).map((spec, index) => (
              <div
                key={spec.id}
                className="flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-2">
                  <span className="text-gray-400 w-4">{index + 1}.</span>
                  <span className="truncate max-w-[120px]" title={spec.name}>
                    {spec.name}
                  </span>
                  <span className="text-xs text-gray-400">G{spec.generation}</span>
                </div>
                <span className={`font-medium ${getScoreColor(spec.score)}`}>
                  {(spec.score * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DomainCard;
