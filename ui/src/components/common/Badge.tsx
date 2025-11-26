import React from 'react';

export type BadgeVariant =
  | 'primary'
  | 'secondary'
  | 'warning'
  | 'danger'
  | 'neutral'
  | 'active'
  | 'idle'
  | 'running'
  | 'completed'
  | 'failed'
  | 'pending'
  | 'probation';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  className = '',
}) => {
  const sizeClass = size === 'sm' ? 'badge-sm' : '';
  const dotClass = dot ? 'badge-dot' : '';

  return (
    <span
      className={`badge badge-${variant} ${sizeClass} ${dotClass} ${className}`.trim()}
    >
      {children}
    </span>
  );
};

// Convenience components for common status badges
export const StatusBadge: React.FC<{
  status: 'active' | 'idle' | 'running' | 'completed' | 'failed' | 'pending' | 'probation';
  size?: 'sm' | 'md';
}> = ({ status, size = 'md' }) => {
  const labels: Record<string, string> = {
    active: 'Active',
    idle: 'Idle',
    running: 'Running',
    completed: 'Completed',
    failed: 'Failed',
    pending: 'Pending',
    probation: 'Probation',
  };

  return (
    <Badge variant={status} size={size} dot>
      {labels[status] || status}
    </Badge>
  );
};

export default Badge;
