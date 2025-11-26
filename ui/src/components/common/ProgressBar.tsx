import React from 'react';

export interface ProgressBarProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'warning' | 'danger';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'primary',
  showLabel = false,
  label,
  className = '',
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const sizeClass = size !== 'md' ? `progress-bar-${size}` : '';

  return (
    <div className={className}>
      {(showLabel || label) && (
        <div className="flex justify-between text-sm mb-1">
          <span className="text-secondary">{label}</span>
          <span className="text-primary font-medium">{percentage.toFixed(0)}%</span>
        </div>
      )}
      <div className={`progress-bar ${sizeClass}`}>
        <div
          className={`progress-bar-fill ${variant !== 'primary' ? variant : ''}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export interface CircularProgressProps {
  value: number;
  max?: number;
  size?: number;
  strokeWidth?: number;
  showLabel?: boolean;
  className?: string;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  max = 100,
  size = 80,
  strokeWidth = 8,
  showLabel = true,
  className = '',
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className={`progress-circular ${className}`} style={{ width: size, height: size }}>
      <svg className="progress-circular-svg" width={size} height={size}>
        <circle
          className="progress-circular-track"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="progress-circular-fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      {showLabel && (
        <span className="progress-circular-text">
          {percentage.toFixed(0)}%
        </span>
      )}
    </div>
  );
};

export default ProgressBar;
