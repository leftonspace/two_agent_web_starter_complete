import React from 'react';
import {
  LayoutDashboard,
  Terminal,
  Code,
  FileText,
  Play,
  Zap,
  Plus,
  Skull,
  type LucideIcon,
} from 'lucide-react';
import { Button } from '../common';

export interface NavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  active?: boolean;
}

export interface DomainInfo {
  id: string;
  name: string;
  icon: LucideIcon;
  specialistCount: number;
  avgScore: number;
}

export interface SidebarProps {
  activePage?: string;
  domains?: DomainInfo[];
  onNavigate?: (pageId: string) => void;
  onDomainClick?: (domainId: string) => void;
  onRunBenchmark?: () => void;
  onForceEvolution?: () => void;
  onNewTask?: () => void;
  onViewGraveyard?: () => void;
}

const defaultDomains: DomainInfo[] = [
  { id: 'administration', name: 'Administration', icon: Terminal, specialistCount: 3, avgScore: 0.87 },
  { id: 'code_generation', name: 'Code Generation', icon: Code, specialistCount: 2, avgScore: 0.78 },
  { id: 'business_documents', name: 'Business Docs', icon: FileText, specialistCount: 1, avgScore: 0.82 },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activePage = 'dashboard',
  domains = defaultDomains,
  onNavigate,
  onDomainClick,
  onRunBenchmark,
  onForceEvolution,
  onNewTask,
  onViewGraveyard,
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 0.85) return 'var(--accent-primary)';
    if (score >= 0.7) return 'var(--accent-secondary)';
    if (score >= 0.5) return 'var(--accent-warning)';
    return 'var(--accent-danger)';
  };

  return (
    <aside className="sidebar">
      {/* Main Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section">
          <div className="nav-section-title">Navigation</div>
          <button
            className={`nav-item ${activePage === 'dashboard' ? 'active' : ''}`}
            onClick={() => onNavigate?.('dashboard')}
          >
            <LayoutDashboard className="icon" />
            <span>Dashboard</span>
          </button>
        </div>

        {/* Domains */}
        <div className="nav-section">
          <div className="nav-section-title">Domains</div>
          {domains.map((domain) => (
            <button
              key={domain.id}
              className="nav-item domain-item"
              onClick={() => onDomainClick?.(domain.id)}
            >
              <domain.icon className="icon" />
              <span className="domain-name">{domain.name}</span>
              <span
                className="domain-score"
                style={{ color: getScoreColor(domain.avgScore) }}
              >
                {domain.avgScore.toFixed(2)}
              </span>
            </button>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="nav-section">
          <div className="nav-section-title">Quick Actions</div>
          <Button
            variant="ghost"
            size="sm"
            icon={Play}
            onClick={onRunBenchmark}
            fullWidth
            className="justify-start"
          >
            Run Benchmark
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={Zap}
            onClick={onForceEvolution}
            fullWidth
            className="justify-start"
          >
            Force Evolution
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={Plus}
            onClick={onNewTask}
            fullWidth
            className="justify-start"
          >
            New Task
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon={Skull}
            onClick={onViewGraveyard}
            fullWidth
            className="justify-start"
          >
            Graveyard
          </Button>
        </div>
      </nav>

      <style>{`
        .sidebar {
          position: fixed;
          top: var(--header-height);
          left: 0;
          bottom: 0;
          width: var(--sidebar-width);
          background: var(--bg-secondary);
          border-right: 1px solid var(--border-primary);
          overflow-y: auto;
          z-index: var(--z-sticky);
        }

        .sidebar-nav {
          padding: var(--space-4);
        }

        .nav-section {
          margin-bottom: var(--space-6);
        }

        .nav-section-title {
          font-size: var(--text-xs);
          font-weight: var(--weight-semibold);
          color: var(--text-tertiary);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: var(--space-2);
          padding: 0 var(--space-2);
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          width: 100%;
          padding: var(--space-2);
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-family: var(--font-mono);
          font-size: var(--text-sm);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-align: left;
        }

        .nav-item:hover {
          background: var(--bg-hover);
          color: var(--text-primary);
        }

        .nav-item.active {
          background: var(--accent-primary-dim);
          color: var(--accent-primary);
        }

        .domain-item {
          justify-content: flex-start;
        }

        .domain-name {
          flex: 1;
        }

        .domain-score {
          font-weight: var(--weight-semibold);
          font-size: var(--text-xs);
        }

        @media (max-width: 1024px) {
          .sidebar {
            transform: translateX(-100%);
            transition: transform var(--transition-normal);
          }

          .sidebar.open {
            transform: translateX(0);
          }
        }
      `}</style>
    </aside>
  );
};

export default Sidebar;
