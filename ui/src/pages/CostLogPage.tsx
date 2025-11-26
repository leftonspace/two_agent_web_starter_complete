import React, { useState, useMemo } from 'react';
import { DollarSign, Download, Filter, Calendar, RefreshCw } from 'lucide-react';
import { Header, Sidebar, MainContent, ContentHeader, ContentSection } from '../components/layout';
import { StatsCard, StatsGrid } from '../components/charts';

interface CostEntry {
  id: string;
  timestamp: string;
  category: string;
  description: string;
  amount: number;
  specialist_id?: string;
  specialist_name?: string;
  domain?: string;
}

// Mock cost data
const mockCostData: CostEntry[] = [
  { id: '1', timestamp: '2024-01-15T10:30:00Z', category: 'API Calls', description: 'GPT-4 inference', amount: 0.42, specialist_name: 'code-gen-v3', domain: 'coding' },
  { id: '2', timestamp: '2024-01-15T11:15:00Z', category: 'API Calls', description: 'Claude evaluation', amount: 0.18, specialist_name: 'eval-specialist', domain: 'evaluation' },
  { id: '3', timestamp: '2024-01-15T12:00:00Z', category: 'Embedding', description: 'Document embedding', amount: 0.05, specialist_name: 'doc-indexer', domain: 'indexing' },
  { id: '4', timestamp: '2024-01-15T14:30:00Z', category: 'API Calls', description: 'GPT-4 inference', amount: 0.38, specialist_name: 'code-review-v2', domain: 'coding' },
  { id: '5', timestamp: '2024-01-15T15:45:00Z', category: 'Evolution', description: 'Specialist mutation', amount: 0.25, domain: 'system' },
  { id: '6', timestamp: '2024-01-14T09:00:00Z', category: 'API Calls', description: 'Claude inference', amount: 0.22, specialist_name: 'planning-v1', domain: 'planning' },
  { id: '7', timestamp: '2024-01-14T10:30:00Z', category: 'Benchmark', description: 'HumanEval run', amount: 0.85, domain: 'benchmark' },
  { id: '8', timestamp: '2024-01-14T13:00:00Z', category: 'API Calls', description: 'GPT-4 inference', amount: 0.45, specialist_name: 'debug-specialist', domain: 'coding' },
];

const categories = ['All', 'API Calls', 'Embedding', 'Evolution', 'Benchmark'];

export const CostLogPage: React.FC = () => {
  const [dateRange, setDateRange] = useState<'today' | '7d' | '30d' | 'all'>('7d');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter costs based on selections
  const filteredCosts = useMemo(() => {
    let filtered = [...mockCostData];

    // Date filter
    const now = new Date();
    if (dateRange === 'today') {
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      filtered = filtered.filter(c => new Date(c.timestamp) >= today);
    } else if (dateRange === '7d') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(c => new Date(c.timestamp) >= weekAgo);
    } else if (dateRange === '30d') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(c => new Date(c.timestamp) >= monthAgo);
    }

    // Category filter
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(c => c.category === selectedCategory);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(c =>
        c.description.toLowerCase().includes(query) ||
        c.specialist_name?.toLowerCase().includes(query) ||
        c.domain?.toLowerCase().includes(query)
      );
    }

    return filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [dateRange, selectedCategory, searchQuery]);

  // Calculate summary stats
  const stats = useMemo(() => {
    const total = filteredCosts.reduce((sum, c) => sum + c.amount, 0);
    const byCategory = filteredCosts.reduce((acc, c) => {
      acc[c.category] = (acc[c.category] || 0) + c.amount;
      return acc;
    }, {} as Record<string, number>);
    const avgPerEntry = filteredCosts.length > 0 ? total / filteredCosts.length : 0;
    return { total, byCategory, avgPerEntry, count: filteredCosts.length };
  }, [filteredCosts]);

  // Export to CSV
  const exportCSV = () => {
    const headers = ['Timestamp', 'Category', 'Description', 'Amount', 'Specialist', 'Domain'];
    const rows = filteredCosts.map(c => [
      c.timestamp,
      c.category,
      c.description,
      c.amount.toFixed(4),
      c.specialist_name || '',
      c.domain || '',
    ]);
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cost-log-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const formatTimestamp = (ts: string) => {
    const date = new Date(ts);
    return date.toLocaleString();
  };

  return (
    <div className="dashboard-layout">
      <Header systemHealth="healthy" />
      <Sidebar activePage="cost-log" />

      <MainContent>
        <ContentHeader
          title={
            <>
              <DollarSign className="icon" style={{ color: 'var(--accent-warning)' }} />
              Cost Log
            </>
          }
          subtitle="Track and analyze API usage costs"
          actions={
            <button className="export-btn" onClick={exportCSV}>
              <Download className="icon-sm" />
              Export CSV
            </button>
          }
        />

        {/* Summary Stats */}
        <ContentSection>
          <StatsGrid columns={4}>
            <StatsCard
              title="Total Spent"
              value={`$${stats.total.toFixed(2)}`}
              icon={DollarSign}
              variant="warning"
            />
            <StatsCard
              title="Transactions"
              value={stats.count}
              icon={Filter}
            />
            <StatsCard
              title="Avg per Entry"
              value={`$${stats.avgPerEntry.toFixed(3)}`}
              icon={DollarSign}
            />
            <StatsCard
              title="Top Category"
              value={Object.entries(stats.byCategory).sort((a, b) => b[1] - a[1])[0]?.[0] || '-'}
              icon={Filter}
            />
          </StatsGrid>
        </ContentSection>

        {/* Filters */}
        <ContentSection>
          <div className="filters-bar">
            <div className="filter-group">
              <Calendar className="icon-sm" />
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value as typeof dateRange)}
              >
                <option value="today">Today</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="all">All Time</option>
              </select>
            </div>

            <div className="filter-group">
              <Filter className="icon-sm" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="filter-group search">
              <input
                type="text"
                placeholder="Search descriptions, specialists..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <button className="refresh-btn" onClick={() => window.location.reload()}>
              <RefreshCw className="icon-sm" />
            </button>
          </div>
        </ContentSection>

        {/* Cost Table */}
        <ContentSection title="Cost Entries">
          <div className="cost-table-wrapper">
            <table className="cost-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Category</th>
                  <th>Description</th>
                  <th>Specialist</th>
                  <th>Domain</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {filteredCosts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-row">No cost entries found</td>
                  </tr>
                ) : (
                  filteredCosts.map(cost => (
                    <tr key={cost.id}>
                      <td className="timestamp">{formatTimestamp(cost.timestamp)}</td>
                      <td>
                        <span className={`category-badge category-${cost.category.toLowerCase().replace(/\s+/g, '-')}`}>
                          {cost.category}
                        </span>
                      </td>
                      <td>{cost.description}</td>
                      <td>{cost.specialist_name || '-'}</td>
                      <td>{cost.domain || '-'}</td>
                      <td className="amount">${cost.amount.toFixed(4)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </ContentSection>

        {/* Category Breakdown */}
        <ContentSection title="Cost by Category">
          <div className="category-breakdown">
            {Object.entries(stats.byCategory)
              .sort((a, b) => b[1] - a[1])
              .map(([category, amount]) => (
                <div key={category} className="category-row">
                  <span className="category-name">{category}</span>
                  <div className="category-bar-container">
                    <div
                      className="category-bar"
                      style={{ width: `${(amount / stats.total) * 100}%` }}
                    />
                  </div>
                  <span className="category-amount">${amount.toFixed(2)}</span>
                  <span className="category-percent">
                    {((amount / stats.total) * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
          </div>
        </ContentSection>
      </MainContent>

      <style>{styles}</style>
    </div>
  );
};

const styles = `
  .dashboard-layout {
    min-height: 100vh;
    background: var(--bg-primary);
  }

  .export-btn {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    background: var(--accent-primary);
    border: none;
    border-radius: var(--radius-md);
    color: var(--bg-primary);
    font-weight: var(--weight-semibold);
    cursor: pointer;
    transition: opacity var(--transition-fast);
  }

  .export-btn:hover {
    opacity: 0.9;
  }

  .filters-bar {
    display: flex;
    gap: var(--space-4);
    flex-wrap: wrap;
    align-items: center;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-3);
  }

  .filter-group select,
  .filter-group input {
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: var(--text-sm);
    outline: none;
  }

  .filter-group.search {
    flex: 1;
    min-width: 200px;
  }

  .filter-group.search input {
    width: 100%;
  }

  .refresh-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .refresh-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .cost-table-wrapper {
    overflow-x: auto;
  }

  .cost-table {
    width: 100%;
    border-collapse: collapse;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
  }

  .cost-table th {
    padding: var(--space-3) var(--space-4);
    text-align: left;
    font-size: var(--text-xs);
    font-weight: var(--weight-semibold);
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-primary);
  }

  .cost-table td {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--border-primary);
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .cost-table tbody tr:hover {
    background: var(--bg-hover);
  }

  .cost-table tbody tr:last-child td {
    border-bottom: none;
  }

  .cost-table .timestamp {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--text-tertiary);
  }

  .cost-table .amount {
    font-family: var(--font-mono);
    font-weight: var(--weight-semibold);
    color: var(--accent-warning);
  }

  .empty-row {
    text-align: center;
    color: var(--text-tertiary);
    padding: var(--space-8) !important;
  }

  .category-badge {
    display: inline-block;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--text-xs);
    font-weight: var(--weight-medium);
    background: var(--bg-tertiary);
    color: var(--text-secondary);
  }

  .category-badge.category-api-calls {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
  }

  .category-badge.category-embedding {
    background: var(--accent-secondary-dim);
    color: var(--accent-secondary);
  }

  .category-badge.category-evolution {
    background: var(--accent-warning-dim);
    color: var(--accent-warning);
  }

  .category-badge.category-benchmark {
    background: var(--accent-danger-dim);
    color: var(--accent-danger);
  }

  .category-breakdown {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .category-row {
    display: flex;
    align-items: center;
    gap: var(--space-4);
  }

  .category-name {
    width: 100px;
    font-size: var(--text-sm);
    color: var(--text-secondary);
  }

  .category-bar-container {
    flex: 1;
    height: 8px;
    background: var(--bg-tertiary);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .category-bar {
    height: 100%;
    background: var(--accent-primary);
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
  }

  .category-amount {
    width: 70px;
    text-align: right;
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    color: var(--text-primary);
  }

  .category-percent {
    width: 50px;
    text-align: right;
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }
`;

export default CostLogPage;
