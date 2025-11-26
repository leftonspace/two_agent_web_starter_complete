import React, { useState } from 'react';
import { Moon, Bell, Zap, Save, RotateCcw } from 'lucide-react';
import { Modal, Button, Dropdown } from '../common';

export interface SettingsData {
  theme: 'dark' | 'light' | 'system';
  autoRefresh: boolean;
  refreshInterval: number;
  notifications: boolean;
  soundEffects: boolean;
  evaluationMode: 'scoring_committee' | 'ai_council' | 'both';
  evolutionAutoStart: boolean;
  budgetWarningThreshold: number;
}

export interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  settings?: Partial<SettingsData>;
  onSave?: (settings: SettingsData) => void;
  onReset?: () => void;
}

const defaultSettings: SettingsData = {
  theme: 'dark',
  autoRefresh: true,
  refreshInterval: 30,
  notifications: true,
  soundEffects: false,
  evaluationMode: 'both',
  evolutionAutoStart: true,
  budgetWarningThreshold: 20,
};

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
  settings: initialSettings,
  onSave,
  onReset,
}) => {
  const [settings, setSettings] = useState<SettingsData>({
    ...defaultSettings,
    ...initialSettings,
  });
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = <K extends keyof SettingsData>(
    key: K,
    value: SettingsData[K]
  ) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave?.(settings);
    setHasChanges(false);
    onClose();
  };

  const handleReset = () => {
    setSettings(defaultSettings);
    onReset?.();
    setHasChanges(true);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Settings" size="md">
      <div className="settings-panel">
        {/* Appearance Section */}
        <div className="settings-section">
          <h4 className="section-title">
            <Moon className="icon-sm" />
            Appearance
          </h4>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Theme</label>
              <span className="setting-description">Choose your preferred color scheme</span>
            </div>
            <Dropdown
              value={settings.theme}
              onChange={(value) => handleChange('theme', value as SettingsData['theme'])}
              options={[
                { value: 'dark', label: 'Dark' },
                { value: 'light', label: 'Light' },
                { value: 'system', label: 'System' },
              ]}
            />
          </div>
        </div>

        {/* Refresh Section */}
        <div className="settings-section">
          <h4 className="section-title">
            <RotateCcw className="icon-sm" />
            Data Refresh
          </h4>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Auto Refresh</label>
              <span className="setting-description">Automatically refresh dashboard data</span>
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={settings.autoRefresh}
                onChange={(e) => handleChange('autoRefresh', e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
          </div>
          {settings.autoRefresh && (
            <div className="setting-row">
              <div className="setting-info">
                <label className="setting-label">Refresh Interval</label>
                <span className="setting-description">How often to fetch new data</span>
              </div>
              <Dropdown
                value={String(settings.refreshInterval)}
                onChange={(value) => handleChange('refreshInterval', Number(value))}
                options={[
                  { value: '10', label: '10 seconds' },
                  { value: '30', label: '30 seconds' },
                  { value: '60', label: '1 minute' },
                  { value: '300', label: '5 minutes' },
                ]}
              />
            </div>
          )}
        </div>

        {/* Notifications Section */}
        <div className="settings-section">
          <h4 className="section-title">
            <Bell className="icon-sm" />
            Notifications
          </h4>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Enable Notifications</label>
              <span className="setting-description">Show alerts for important events</span>
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={(e) => handleChange('notifications', e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
          </div>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Sound Effects</label>
              <span className="setting-description">Play sounds for notifications</span>
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={settings.soundEffects}
                onChange={(e) => handleChange('soundEffects', e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
          </div>
        </div>

        {/* Evolution Section */}
        <div className="settings-section">
          <h4 className="section-title">
            <Zap className="icon-sm" />
            Evolution
          </h4>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Evaluation Mode</label>
              <span className="setting-description">How specialists are evaluated</span>
            </div>
            <Dropdown
              value={settings.evaluationMode}
              onChange={(value) => handleChange('evaluationMode', value as SettingsData['evaluationMode'])}
              options={[
                { value: 'scoring_committee', label: 'Scoring Committee' },
                { value: 'ai_council', label: 'AI Council' },
                { value: 'both', label: 'Both' },
              ]}
            />
          </div>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Auto-start Evolution</label>
              <span className="setting-description">Automatically trigger evolution cycles</span>
            </div>
            <label className="toggle">
              <input
                type="checkbox"
                checked={settings.evolutionAutoStart}
                onChange={(e) => handleChange('evolutionAutoStart', e.target.checked)}
              />
              <span className="toggle-slider" />
            </label>
          </div>
          <div className="setting-row">
            <div className="setting-info">
              <label className="setting-label">Budget Warning (%)</label>
              <span className="setting-description">Alert when budget falls below this</span>
            </div>
            <Dropdown
              value={String(settings.budgetWarningThreshold)}
              onChange={(value) => handleChange('budgetWarningThreshold', Number(value))}
              options={[
                { value: '10', label: '10%' },
                { value: '20', label: '20%' },
                { value: '30', label: '30%' },
                { value: '50', label: '50%' },
              ]}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="settings-actions">
          <Button variant="ghost" onClick={handleReset}>
            Reset to Defaults
          </Button>
          <div className="action-group">
            <Button variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              icon={Save}
              onClick={handleSave}
              disabled={!hasChanges}
            >
              Save Changes
            </Button>
          </div>
        </div>
      </div>

      <style>{`
        .settings-panel {
          display: flex;
          flex-direction: column;
          gap: var(--space-5);
        }

        .settings-section {
          padding-bottom: var(--space-4);
          border-bottom: 1px solid var(--border-primary);
        }

        .settings-section:last-of-type {
          border-bottom: none;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--text-sm);
          font-weight: var(--weight-semibold);
          color: var(--text-primary);
          margin-bottom: var(--space-3);
        }

        .setting-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-3) 0;
        }

        .setting-info {
          flex: 1;
        }

        .setting-label {
          display: block;
          font-size: var(--text-sm);
          color: var(--text-primary);
          margin-bottom: var(--space-1);
        }

        .setting-description {
          font-size: var(--text-xs);
          color: var(--text-tertiary);
        }

        .toggle {
          position: relative;
          display: inline-block;
          width: 44px;
          height: 24px;
          cursor: pointer;
        }

        .toggle input {
          opacity: 0;
          width: 0;
          height: 0;
        }

        .toggle-slider {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-full);
          transition: all var(--transition-fast);
        }

        .toggle-slider::before {
          content: '';
          position: absolute;
          width: 18px;
          height: 18px;
          left: 2px;
          bottom: 2px;
          background: var(--text-tertiary);
          border-radius: 50%;
          transition: all var(--transition-fast);
        }

        .toggle input:checked + .toggle-slider {
          background: var(--accent-primary-dim);
          border-color: var(--accent-primary);
        }

        .toggle input:checked + .toggle-slider::before {
          transform: translateX(20px);
          background: var(--accent-primary);
        }

        .settings-actions {
          display: flex;
          justify-content: space-between;
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }

        .action-group {
          display: flex;
          gap: var(--space-2);
        }
      `}</style>
    </Modal>
  );
};

export default SettingsPanel;
