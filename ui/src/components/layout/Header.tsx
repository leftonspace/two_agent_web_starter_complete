import React from 'react';
import { Settings, Bell, Wallet, Activity } from 'lucide-react';
import { Button } from '../common';

export interface HeaderProps {
  systemHealth?: 'healthy' | 'degraded' | 'unhealthy';
  onSettingsClick?: () => void;
  onNotificationsClick?: () => void;
  onBudgetClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  systemHealth = 'healthy',
  onSettingsClick,
  onNotificationsClick,
  onBudgetClick,
}) => {
  const getHealthColor = () => {
    switch (systemHealth) {
      case 'healthy':
        return 'var(--accent-primary)';
      case 'degraded':
        return 'var(--accent-warning)';
      case 'unhealthy':
        return 'var(--accent-danger)';
      default:
        return 'var(--text-tertiary)';
    }
  };

  return (
    <header className="header">
      {/* Logo */}
      <div className="header-logo">
        <div className="logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="var(--accent-primary)" strokeWidth="2" />
            <circle cx="12" cy="12" r="4" fill="var(--accent-primary)" />
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" stroke="var(--accent-primary)" strokeWidth="2" />
          </svg>
        </div>
        <span className="logo-text">JARVIS</span>
        <span className="logo-version">v7.5</span>
      </div>

      {/* System Status */}
      <div className="header-status">
        <Activity
          className="icon-sm"
          style={{ color: getHealthColor() }}
        />
        <span className="status-label" style={{ color: getHealthColor() }}>
          System {systemHealth.charAt(0).toUpperCase() + systemHealth.slice(1)}
        </span>
      </div>

      {/* Actions */}
      <div className="header-actions">
        <Button
          variant="ghost"
          size="sm"
          icon={Wallet}
          onClick={onBudgetClick}
          aria-label="Budget"
        />
        <Button
          variant="ghost"
          size="sm"
          icon={Bell}
          onClick={onNotificationsClick}
          aria-label="Notifications"
        />
        <Button
          variant="ghost"
          size="sm"
          icon={Settings}
          onClick={onSettingsClick}
          aria-label="Settings"
        />
      </div>

      <style>{`
        .header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          height: var(--header-height);
          background: var(--bg-secondary);
          border-bottom: 1px solid var(--border-primary);
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 var(--space-4);
          z-index: var(--z-sticky);
        }

        .header-logo {
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }

        .logo-icon {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .logo-text {
          font-family: var(--font-display);
          font-size: var(--text-xl);
          font-weight: var(--weight-bold);
          color: var(--accent-primary);
          letter-spacing: 2px;
        }

        .logo-version {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
          padding: 2px 6px;
          background: var(--bg-tertiary);
          border-radius: var(--radius-sm);
        }

        .header-status {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          padding: var(--space-1) var(--space-3);
          background: var(--bg-tertiary);
          border-radius: var(--radius-full);
        }

        .status-label {
          font-size: var(--text-xs);
          font-weight: var(--weight-medium);
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: var(--space-1);
        }

        @media (max-width: 768px) {
          .header-status .status-label {
            display: none;
          }
        }
      `}</style>
    </header>
  );
};

export default Header;
