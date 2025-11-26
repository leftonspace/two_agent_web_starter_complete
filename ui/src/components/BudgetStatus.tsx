import React from 'react';
import type { BudgetStatus as BudgetStatusType } from '../types';

interface BudgetStatusProps {
  budget: BudgetStatusType;
}

export const BudgetStatus: React.FC<BudgetStatusProps> = ({ budget }) => {
  const productionPercent = (budget.production_spent_today / budget.production_limit) * 100;
  const benchmarkPercent = (budget.benchmark_spent_today / budget.benchmark_limit) * 100;

  const getBarColor = (percent: number, isWarning: boolean) => {
    if (isWarning || percent >= 90) return 'bg-red-500';
    if (percent >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="flex items-center gap-6">
      {/* Production Budget */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Production:</span>
        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBarColor(productionPercent, budget.is_warning)} transition-all`}
            style={{ width: `${Math.min(productionPercent, 100)}%` }}
          />
        </div>
        <span className="text-sm font-medium">
          ${(budget.production_spent_today || 0).toFixed(2)}
          <span className="text-gray-400">/${(budget.production_limit || 0).toFixed(0)}</span>
        </span>
        {budget.is_warning && (
          <span className="badge badge-warning">Warning</span>
        )}
      </div>

      {/* Benchmark Budget */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600">Benchmark:</span>
        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full ${getBarColor(benchmarkPercent, false)} transition-all`}
            style={{ width: `${Math.min(benchmarkPercent, 100)}%` }}
          />
        </div>
        <span className="text-sm font-medium">
          ${(budget.benchmark_spent_today || 0).toFixed(2)}
          <span className="text-gray-400">/${(budget.benchmark_limit || 0).toFixed(0)}</span>
        </span>
      </div>
    </div>
  );
};

export default BudgetStatus;
