import React from 'react';

export interface MainContentProps {
  children: React.ReactNode;
  className?: string;
}

export const MainContent: React.FC<MainContentProps> = ({
  children,
  className = '',
}) => {
  return (
    <main className={`main-content ${className}`}>
      {children}

      <style>{`
        .main-content {
          margin-top: var(--header-height);
          margin-left: var(--sidebar-width);
          padding: var(--space-6);
          min-height: calc(100vh - var(--header-height));
          background: var(--bg-primary);
        }

        @media (max-width: 1024px) {
          .main-content {
            margin-left: 0;
          }
        }
      `}</style>
    </main>
  );
};

export interface ContentHeaderProps {
  title: React.ReactNode;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const ContentHeader: React.FC<ContentHeaderProps> = ({
  title,
  subtitle,
  actions,
}) => {
  return (
    <div className="content-header">
      <div>
        <h1 className="content-title">{title}</h1>
        {subtitle && <p className="content-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="content-actions">{actions}</div>}

      <style>{`
        .content-header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: var(--space-6);
        }

        .content-title {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          font-size: var(--text-2xl);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
        }

        .content-subtitle {
          font-size: var(--text-sm);
          color: var(--text-secondary);
          margin-top: var(--space-1);
        }

        .content-actions {
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }
      `}</style>
    </div>
  );
};

export interface ContentSectionProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const ContentSection: React.FC<ContentSectionProps> = ({
  title,
  children,
  className = '',
}) => {
  return (
    <section className={`content-section ${className}`}>
      {title && <h2 className="section-title">{title}</h2>}
      {children}

      <style>{`
        .content-section {
          margin-bottom: var(--space-6);
        }

        .section-title {
          font-size: var(--text-lg);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
          margin-bottom: var(--space-4);
        }
      `}</style>
    </section>
  );
};

export default MainContent;
