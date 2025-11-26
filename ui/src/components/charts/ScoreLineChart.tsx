import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export interface ScoreDataPoint {
  timestamp: string;
  score: number;
  label?: string;
}

export interface ScoreLineChartProps {
  data: ScoreDataPoint[];
  title?: string;
  height?: number;
  showLegend?: boolean;
  fill?: boolean;
  color?: string;
  secondaryData?: ScoreDataPoint[];
  secondaryLabel?: string;
  secondaryColor?: string;
}

export const ScoreLineChart: React.FC<ScoreLineChartProps> = ({
  data,
  title = 'Score Over Time',
  height = 300,
  showLegend = false,
  fill = true,
  color = '#00ff88',
  secondaryData,
  secondaryLabel = 'Secondary',
  secondaryColor = '#00d4ff',
}) => {
  const labels = data.map((point) => {
    const date = new Date(point.timestamp);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  });

  const datasets = [
    {
      label: data[0]?.label || 'Score',
      data: data.map((point) => point.score),
      borderColor: color,
      backgroundColor: fill ? `${color}20` : 'transparent',
      fill: fill,
      tension: 0.4,
      pointRadius: 4,
      pointHoverRadius: 6,
      pointBackgroundColor: color,
      pointBorderColor: 'var(--bg-secondary)',
      pointBorderWidth: 2,
    },
  ];

  if (secondaryData && secondaryData.length > 0) {
    datasets.push({
      label: secondaryLabel,
      data: secondaryData.map((point) => point.score),
      borderColor: secondaryColor,
      backgroundColor: 'transparent',
      fill: false,
      tension: 0.4,
      pointRadius: 3,
      pointHoverRadius: 5,
      pointBackgroundColor: secondaryColor,
      pointBorderColor: 'var(--bg-secondary)',
      pointBorderWidth: 2,
    });
  }

  const chartData = { labels, datasets };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showLegend,
        position: 'top' as const,
        labels: {
          color: '#a0aec0',
          font: {
            family: 'JetBrains Mono, monospace',
            size: 11,
          },
          padding: 16,
          usePointStyle: true,
        },
      },
      title: {
        display: !!title,
        text: title,
        color: '#e2e8f0',
        font: {
          family: 'Inter, sans-serif',
          size: 14,
          weight: '600',
        },
        padding: { bottom: 16 },
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
        displayColors: true,
        callbacks: {
          label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(3)}`,
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: '#2d2d3a',
          lineWidth: 1,
        },
        ticks: {
          color: '#718096',
          font: {
            family: 'JetBrains Mono, monospace',
            size: 10,
          },
        },
        border: {
          color: '#2d2d3a',
        },
      },
      y: {
        min: 0,
        max: 1,
        grid: {
          color: '#2d2d3a',
          lineWidth: 1,
        },
        ticks: {
          color: '#718096',
          font: {
            family: 'JetBrains Mono, monospace',
            size: 10,
          },
          callback: (value) => (typeof value === 'number' ? value.toFixed(2) : value),
        },
        border: {
          color: '#2d2d3a',
        },
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  return (
    <div className="score-line-chart" style={{ height }}>
      <Line data={chartData} options={options} />
      <style>{`
        .score-line-chart {
          width: 100%;
          padding: var(--space-4);
          background: var(--bg-secondary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-lg);
        }
      `}</style>
    </div>
  );
};

export default ScoreLineChart;
