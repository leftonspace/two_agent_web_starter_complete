import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  type ChartOptions,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export interface BarDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface BarChartProps {
  data: BarDataPoint[];
  title?: string;
  height?: number;
  horizontal?: boolean;
  showLegend?: boolean;
  color?: string;
  maxValue?: number;
  formatValue?: (value: number) => string;
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  title,
  height = 300,
  horizontal = false,
  showLegend = false,
  color = '#00ff88',
  maxValue,
  formatValue = (v) => v.toString(),
}) => {
  const chartData = {
    labels: data.map((item) => item.label),
    datasets: [
      {
        label: title || 'Value',
        data: data.map((item) => item.value),
        backgroundColor: data.map((item) => item.color || `${color}80`),
        borderColor: data.map((item) => item.color || color),
        borderWidth: 1,
        borderRadius: 4,
        barThickness: horizontal ? 24 : 'flex',
        maxBarThickness: 48,
      },
    ],
  };

  const options: ChartOptions<'bar'> = {
    indexAxis: horizontal ? 'y' : 'x',
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
        callbacks: {
          label: (context) => formatValue(context.parsed[horizontal ? 'x' : 'y']),
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: '#2d2d3a',
          lineWidth: 1,
          display: !horizontal,
        },
        ticks: {
          color: '#718096',
          font: {
            family: 'JetBrains Mono, monospace',
            size: 10,
          },
          maxRotation: 45,
        },
        border: {
          color: '#2d2d3a',
        },
        max: horizontal ? maxValue : undefined,
      },
      y: {
        grid: {
          color: '#2d2d3a',
          lineWidth: 1,
          display: horizontal,
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
        max: !horizontal ? maxValue : undefined,
      },
    },
  };

  return (
    <div className="bar-chart" style={{ height }}>
      <Bar data={chartData} options={options} />
      <style>{`
        .bar-chart {
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

export default BarChart;
