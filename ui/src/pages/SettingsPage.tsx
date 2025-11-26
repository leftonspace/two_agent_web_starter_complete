import React, { useState } from 'react';
import { Settings, Save, RotateCcw, Bell, Moon, Zap, DollarSign, Shield } from 'lucide-react';
import { Header, Sidebar, MainContent, ContentHeader, ContentSection } from '../components/layout';

interface SettingsState {
  theme: 'dark' | 'light' | 'system';
  notifications: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  dailyBudgetLimit: number;
  budgetWarningThreshold: number;
  evolutionEnabled: boolean;
  evolutionInterval: number;
  minPoolSize: number;
  maxPoolSize: number;
}

const defaultSettings: SettingsState = {
  theme: 'dark',
  notifications: true,
  autoRefresh: true,
  refreshInterval: 30,
  dailyBudgetLimit: 50,
  budgetWarningThreshold: 80,
  evolutionEnabled: true,
  evolutionInterval: 60,
  minPoolSize: 3,
  maxPoolSize: 10,
};

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SettingsState>(defaultSettings);
  const [hasChanges, setHasChanges] = useState(false);

  const updateSetting = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    // In real app, save to API/localStorage
    console.log('Saving settings:', settings);
    setHasChanges(false);
    alert('Settings saved successfully!');
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    setHasChanges(true);
  };

  return (
    <div className="dashboard-layout">
      <Header systemHealth="healthy" />
      <Sidebar activePage="settings" />

      <MainContent>
        <ContentHeader
          title={
            <>
              <Settings className="icon" style={{ color: 'var(--accent-secondary)' }} />
              Settings
            </>
          }
          subtitle="Configure your JARVIS dashboard"
          actions={
            <div className="header-actions">
              <button className="reset-btn" onClick={handleReset}>
                <RotateCcw className="icon-sm" />
                Reset
              </button>
              <button className="save-btn" onClick={handleSave} disabled={!hasChanges}>
                <Save className="icon-sm" />
                Save Changes
              </button>
            </div>
          }
        />

        {/* Appearance */}
        <ContentSection title="Appearance">
          <div className="settings-group">
            <div className="setting-row">
              <div className="setting-info">
                <Moon className="setting-icon" />
                <div>
                  <h4>Theme</h4>
                  <p>Choose your preferred color scheme</p>
                </div>
              </div>
              <select
                value={settings.theme}
                onChange={(e) => updateSetting('theme', e.target.value as SettingsState['theme'])}
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
                <option value="system">System</option>
              </select>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <Bell className="setting-icon" />
                <div>
                  <h4>Notifications</h4>
                  <p>Show desktop notifications for important events</p>
                </div>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.notifications}
                  onChange={(e) => updateSetting('notifications', e.target.checked)}
                />
                <span className="toggle-slider" />
              </label>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <Zap className="setting-icon" />
                <div>
                  <h4>Auto-refresh</h4>
                  <p>Automatically refresh dashboard data</p>
                </div>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.autoRefresh}
                  onChange={(e) => updateSetting('autoRefresh', e.target.checked)}
                />
                <span className="toggle-slider" />
              </label>
            </div>

            {settings.autoRefresh && (
              <div className="setting-row sub-setting">
                <div className="setting-info">
                  <div>
                    <h4>Refresh Interval</h4>
                    <p>How often to refresh data (seconds)</p>
                  </div>
                </div>
                <input
                  type="number"
                  value={settings.refreshInterval}
                  onChange={(e) => updateSetting('refreshInterval', parseInt(e.target.value) || 30)}
                  min={10}
                  max={300}
                />
              </div>
            )}
          </div>
        </ContentSection>

        {/* Budget */}
        <ContentSection title="Budget">
          <div className="settings-group">
            <div className="setting-row">
              <div className="setting-info">
                <DollarSign className="setting-icon" />
                <div>
                  <h4>Daily Budget Limit</h4>
                  <p>Maximum daily spend in USD</p>
                </div>
              </div>
              <div className="input-with-prefix">
                <span>$</span>
                <input
                  type="number"
                  value={settings.dailyBudgetLimit}
                  onChange={(e) => updateSetting('dailyBudgetLimit', parseFloat(e.target.value) || 50)}
                  min={1}
                  step={1}
                />
              </div>
            </div>

            <div className="setting-row">
              <div className="setting-info">
                <Shield className="setting-icon" />
                <div>
                  <h4>Warning Threshold</h4>
                  <p>Show warning when budget usage exceeds this percentage</p>
                </div>
              </div>
              <div className="input-with-suffix">
                <input
                  type="number"
                  value={settings.budgetWarningThreshold}
                  onChange={(e) => updateSetting('budgetWarningThreshold', parseInt(e.target.value) || 80)}
                  min={50}
                  max={100}
                />
                <span>%</span>
              </div>
            </div>
          </div>
        </ContentSection>

        {/* Evolution */}
        <ContentSection title="Evolution">
          <div className="settings-group">
            <div className="setting-row">
              <div className="setting-info">
                <Zap className="setting-icon" />
                <div>
                  <h4>Auto Evolution</h4>
                  <p>Automatically evolve specialist pools</p>
                </div>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings.evolutionEnabled}
                  onChange={(e) => updateSetting('evolutionEnabled', e.target.checked)}
                />
                <span className="toggle-slider" />
              </label>
            </div>

            {settings.evolutionEnabled && (
              <>
                <div className="setting-row sub-setting">
                  <div className="setting-info">
                    <div>
                      <h4>Evolution Interval</h4>
                      <p>Minutes between evolution cycles</p>
                    </div>
                  </div>
                  <div className="input-with-suffix">
                    <input
                      type="number"
                      value={settings.evolutionInterval}
                      onChange={(e) => updateSetting('evolutionInterval', parseInt(e.target.value) || 60)}
                      min={15}
                      max={1440}
                    />
                    <span>min</span>
                  </div>
                </div>

                <div className="setting-row sub-setting">
                  <div className="setting-info">
                    <div>
                      <h4>Pool Size Range</h4>
                      <p>Min and max specialists per pool</p>
                    </div>
                  </div>
                  <div className="range-inputs">
                    <input
                      type="number"
                      value={settings.minPoolSize}
                      onChange={(e) => updateSetting('minPoolSize', parseInt(e.target.value) || 3)}
                      min={1}
                      max={settings.maxPoolSize}
                    />
                    <span>to</span>
                    <input
                      type="number"
                      value={settings.maxPoolSize}
                      onChange={(e) => updateSetting('maxPoolSize', parseInt(e.target.value) || 10)}
                      min={settings.minPoolSize}
                      max={50}
                    />
                  </div>
                </div>
              </>
            )}
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

  .header-actions {
    display: flex;
    gap: var(--space-2);
  }

  .save-btn, .reset-btn {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border: none;
    border-radius: var(--radius-md);
    font-weight: var(--weight-semibold);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .save-btn {
    background: var(--accent-primary);
    color: var(--bg-primary);
  }

  .save-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .reset-btn {
    background: var(--bg-tertiary);
    color: var(--text-secondary);
    border: 1px solid var(--border-primary);
  }

  .reset-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .settings-group {
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .setting-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4);
    border-bottom: 1px solid var(--border-primary);
  }

  .setting-row:last-child {
    border-bottom: none;
  }

  .setting-row.sub-setting {
    padding-left: var(--space-8);
    background: var(--bg-tertiary);
  }

  .setting-info {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .setting-icon {
    width: 20px;
    height: 20px;
    color: var(--text-tertiary);
  }

  .setting-info h4 {
    margin: 0;
    font-size: var(--text-sm);
    font-weight: var(--weight-medium);
    color: var(--text-primary);
  }

  .setting-info p {
    margin: var(--space-1) 0 0;
    font-size: var(--text-xs);
    color: var(--text-tertiary);
  }

  .setting-row select {
    padding: var(--space-2) var(--space-3);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-sm);
  }

  .setting-row input[type="number"] {
    width: 80px;
    padding: var(--space-2) var(--space-3);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: var(--text-sm);
    text-align: center;
  }

  .input-with-prefix,
  .input-with-suffix {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .input-with-prefix span,
  .input-with-suffix span {
    color: var(--text-tertiary);
    font-size: var(--text-sm);
  }

  .range-inputs {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .range-inputs span {
    color: var(--text-tertiary);
    font-size: var(--text-sm);
  }

  /* Toggle Switch */
  .toggle {
    position: relative;
    display: inline-block;
    width: 48px;
    height: 24px;
  }

  .toggle input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: 24px;
    transition: all var(--transition-fast);
  }

  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 2px;
    bottom: 2px;
    background-color: var(--text-tertiary);
    border-radius: 50%;
    transition: all var(--transition-fast);
  }

  .toggle input:checked + .toggle-slider {
    background-color: var(--accent-primary);
    border-color: var(--accent-primary);
  }

  .toggle input:checked + .toggle-slider:before {
    transform: translateX(24px);
    background-color: var(--bg-primary);
  }
`;

export default SettingsPage;
