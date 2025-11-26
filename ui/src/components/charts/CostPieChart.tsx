import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

export interface CostDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface CostPieChartProps {
  data: CostDataPoint[];
  title?: string;
  height?: number;
  showLegend?: boolean;
  showTotal?: boolean;
  formatValue?: (value: number) => string;
}

const defaultColors = [
  '#00ff88',
  '#00d4ff',
  '#ff6b6b',
  '#ffd93d',
  '#6c5ce7',
  '#a29bfe',
  '#fd79a8',
  '#00b894',
];

export const CostPieChart: React.FC<CostPieChartProps> = ({
  data,
  title,
  height = 300,
  showLegend = true,
  showTotal = true,
  formatValue = (v) => `$${v.toFixed(2)}`,
}) => {
  const total = data.reduce((sum, item) => sum + item.value, 0);

  const chartData = {
    labels: data.map((item) => item.label),
    datasets: [
      {
        data: data.map((item) => item.value),
        backgroundColor: data.map((item, index) => item.color || defaultColors[index % defaultColors.length]),
        borderColor: '#0a0a0f',
        borderWidth: 2,
        hoverOffset: 8,
      },
    ],
  };

  const options: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '65%',
    plugins: {
      legend: {
        display: showLegend,
        position: 'right' as const,
        labels: {
          color: '#a0aec0',
          font: {
            family: 'JetBrains Mono, monospace',
            size: 11,
          },
          padding: 12,
          usePointStyle: true,
          pointStyle: 'circle',
          generateLabels: (chart) => {
            const dataset = chart.data.datasets[0];
            return chart.data.labels?.map((label, index) => {
              const value = dataset.data[index] as number;
              const percentage = ((value / total) * 100).toFixed(1);
              return {
                text: `${label} (${percentage}%)`,
                fillStyle: (dataset.backgroundColor as string[])[index],
                strokeStyle: 'transparent',
                lineWidth: 0,
                hidden: false,
                index,
                fontColor: '#a0aec0',
              };
            }) || [];
          },
        },
      },
      tooltip: {
        backgroundColor: '#1a1a24',
        borderColor: '#2d2d3a',
        borderWidth: 1,
        titleColor: '#e2e8f0',
        bodyColor: '#a0aec0',
        titleFont: {
          family: 'Inter, sans-serif',
          size: 12,
          weight: '600',
        },
        bodyFont: {
          family: 'JetBrains Mono, monospace',
          size: 12,
        },
        padding: 12,
        cornerRadius: 8,
        callbacks: {
          label: (context) => {
            const value = context.parsed;
            const percentage = ((value / total) * 100).toFixed(1);
            return `${formatValue(value)} (${percentage}%)`;
          },
        },
      },
    },
  };

  return (
    <div className="cost-pie-chart">
      {title && <div className="chart-title">{title}</div>}
      <div className="chart-container" style={{ height }}>
        <Doughnut data={chartData} options={options} />
        {showTotal && (
          <div className="chart-center">
            <div className="total-label">Total</div>
            <div className="total-value">{formatValue(total)}</div>
          </div>
        )}
      </div>
      <style>{`
        .cost-pie-chart {
          padding: var(--space-4);
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
        }

        .chart-title {
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
          margin-bottom: var(--space-4);
        }

        .chart-container {
          position: relative;
        }

        .chart-center {
          position: absolute;
          top: 50%;
          left: calc(50% - 60px);
          transform: translate(-50%, -50%);
          text-align: center;
        }

        .total-label {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .total-value {
          font-family: var(--font-mono);
          font-size: var(--text-xl);
          font-weight: var(--weight-bold);
          color: var(--text-primary);
        }
      `}</style>
    </div>
  );
};

export default CostPieChart;
