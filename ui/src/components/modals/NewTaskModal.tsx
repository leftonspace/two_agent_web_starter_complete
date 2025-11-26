import React, { useState } from 'react';
import { Send, FileCode } from 'lucide-react';
import { Modal, Button, Input, Dropdown } from '../common';

export interface NewTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit?: (task: NewTaskData) => void;
  domains?: { id: string; name: string }[];
  specialists?: { id: string; name: string; domain: string }[];
  loading?: boolean;
}

export interface NewTaskData {
  name: string;
  description: string;
  domain?: string;
  specialist_id?: string;
  priority?: 'low' | 'normal' | 'high';
  input?: string;
}

export const NewTaskModal: React.FC<NewTaskModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  domains = [],
  specialists = [],
  loading = false,
}) => {
  const [formData, setFormData] = useState<NewTaskData>({
    name: '',
    description: '',
    priority: 'normal',
  });
  const [errors, setErrors] = useState<Partial<Record<keyof NewTaskData, string>>>({});

  const handleChange = (field: keyof NewTaskData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof NewTaskData, string>> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Task name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onSubmit?.(formData);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      priority: 'normal',
    });
    setErrors({});
    onClose();
  };

  const filteredSpecialists = formData.domain
    ? specialists.filter((s) => s.domain === formData.domain)
    : specialists;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Task" size="md">
      <form onSubmit={handleSubmit} className="new-task-form">
        <Input
          label="Task Name"
          placeholder="Enter task name"
          value={formData.name}
          onChange={(e) => handleChange('name', e.target.value)}
          error={errors.name}
          required
        />

        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className={`form-textarea ${errors.description ? 'error' : ''}`}
            placeholder="Describe the task in detail..."
            value={formData.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={4}
          />
          {errors.description && (
            <span className="form-error">{errors.description}</span>
          )}
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Domain (Optional)</label>
            <Dropdown
              value={formData.domain || ''}
              onChange={(value) => {
                handleChange('domain', value);
                handleChange('specialist_id', '');
              }}
              options={[
                { value: '', label: 'Auto-select' },
                ...domains.map((d) => ({ value: d.id, label: d.name })),
              ]}
              placeholder="Select domain"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Priority</label>
            <Dropdown
              value={formData.priority || 'normal'}
              onChange={(value) => handleChange('priority', value)}
              options={[
                { value: 'low', label: 'Low' },
                { value: 'normal', label: 'Normal' },
                { value: 'high', label: 'High' },
              ]}
            />
          </div>
        </div>

        {filteredSpecialists.length > 0 && (
          <div className="form-group">
            <label className="form-label">Specialist (Optional)</label>
            <Dropdown
              value={formData.specialist_id || ''}
              onChange={(value) => handleChange('specialist_id', value)}
              options={[
                { value: '', label: 'Auto-select best specialist' },
                ...filteredSpecialists.map((s) => ({ value: s.id, label: s.name })),
              ]}
              placeholder="Select specialist"
            />
          </div>
        )}

        <div className="form-group">
          <label className="form-label">
            <FileCode className="icon-sm" />
            Input Data (Optional)
          </label>
          <textarea
            className="form-textarea code"
            placeholder="Enter any input data or code..."
            value={formData.input || ''}
            onChange={(e) => handleChange('input', e.target.value)}
            rows={6}
          />
        </div>

        <div className="form-actions">
          <Button variant="ghost" type="button" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            type="submit"
            icon={Send}
            loading={loading}
          >
            Create Task
          </Button>
        </div>
      </form>

      <style>{`
        .new-task-form {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }

        .form-label {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-size: var(--text-sm);
          font-weight: var(--weight-medium);
          color: var(--text-secondary);
        }

        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-4);
        }

        .form-textarea {
          padding: var(--space-3);
          background: var(--bg-tertiary);
          border: 1px solid var(--border-primary);
          border-radius: var(--radius-md);
          color: var(--text-primary);
          font-family: var(--font-sans);
          font-size: var(--text-sm);
          resize: vertical;
          min-height: 80px;
          transition: border-color var(--transition-fast);
        }

        .form-textarea:focus {
          outline: none;
          border-color: var(--accent-primary);
        }

        .form-textarea.code {
          font-family: var(--font-mono);
          font-size: var(--text-xs);
        }

        .form-textarea.error {
          border-color: var(--accent-danger);
        }

        .form-error {
          font-size: var(--text-xs);
          color: var(--accent-danger);
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: var(--space-2);
          padding-top: var(--space-4);
          border-top: 1px solid var(--border-primary);
        }
      `}</style>
    </Modal>
  );
};

export default NewTaskModal;
