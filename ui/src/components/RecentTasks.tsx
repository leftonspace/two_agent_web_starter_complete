import React, { useEffect, useState } from 'react';
import type { TaskSummary } from '../types';
import { tasksApi } from '../api/client';

interface RecentTasksProps {
  className?: string;
  limit?: number;
}

export const RecentTasks: React.FC<RecentTasksProps> = ({
  className = '',
  limit = 10,
}) => {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedbackPending, setFeedbackPending] = useState<string | null>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState<TaskSummary | null>(null);

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [limit]);

  const loadTasks = async () => {
    try {
      const data = await tasksApi.getRecent({ limit });
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFeedback = async (taskId: string, rating: number) => {
    setFeedbackPending(taskId);
    try {
      await tasksApi.submitFeedback(taskId, { rating });
      // Optimistically update UI
      setTasks(prev =>
        prev.map(t => (t.id === taskId ? { ...t, has_feedback: true } : t))
      );
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setFeedbackPending(null);
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-400';
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  const formatDomain = (domain: string) => {
    return domain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  if (loading) {
    return (
      <div className={`card ${className}`}>
        <h3 className="card-header">Recent Tasks</h3>
        <div className="text-gray-400 text-center py-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="card-header mb-0">Recent Tasks</h3>
        <button onClick={loadTasks} className="text-sm text-jarvis-600 hover:underline">
          Refresh
        </button>
      </div>

      {tasks.length === 0 ? (
        <div className="text-gray-400 text-center py-8">
          No tasks yet. Start using JARVIS to see tasks here.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2 font-medium">Task</th>
                <th className="pb-2 font-medium">Domain</th>
                <th className="pb-2 font-medium">Specialist</th>
                <th className="pb-2 font-medium text-right">Score</th>
                <th className="pb-2 font-medium text-right">Cost</th>
                <th className="pb-2 font-medium">Time</th>
                <th className="pb-2 font-medium text-center">Feedback</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map(task => (
                <tr key={task.id} className="border-b last:border-b-0 hover:bg-gray-50">
                  <td className="py-3 max-w-[200px]">
                    <div
                      className="truncate text-gray-800"
                      title={task.request_preview}
                    >
                      {task.request_preview}
                    </div>
                  </td>
                  <td className="py-3">
                    <span className="badge badge-info">
                      {formatDomain(task.domain)}
                    </span>
                  </td>
                  <td className="py-3 text-gray-600">
                    {task.specialist_name || '-'}
                  </td>
                  <td className={`py-3 text-right font-medium ${getScoreColor(task.score)}`}>
                    {task.score != null ? `${((task.score || 0) * 100).toFixed(0)}%` : '-'}
                  </td>
                  <td className="py-3 text-right text-gray-500">
                    ${(task.cost_cad || 0).toFixed(4)}
                  </td>
                  <td className="py-3 text-gray-500">
                    {formatTime(task.created_at)}
                  </td>
                  <td className="py-3 text-center">
                    {task.has_feedback ? (
                      <span className="text-green-600" title="Feedback received">✓</span>
                    ) : feedbackPending === task.id ? (
                      <span className="text-gray-400">...</span>
                    ) : (
                      <div className="flex justify-center gap-1">
                        <button
                          onClick={() => handleQuickFeedback(task.id, 5)}
                          className="p-1 hover:bg-green-100 rounded"
                          title="Great!"
                        >
                          👍
                        </button>
                        <button
                          onClick={() => handleQuickFeedback(task.id, 2)}
                          className="p-1 hover:bg-red-100 rounded"
                          title="Needs work"
                        >
                          👎
                        </button>
                        <button
                          onClick={() => setShowFeedbackModal(task)}
                          className="p-1 hover:bg-gray-100 rounded text-gray-500"
                          title="Detailed feedback"
                        >
                          ⋯
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <FeedbackModal
          task={showFeedbackModal}
          onClose={() => setShowFeedbackModal(null)}
          onSubmit={async (feedback) => {
            await tasksApi.submitFeedback(showFeedbackModal.id, feedback);
            setTasks(prev =>
              prev.map(t => (t.id === showFeedbackModal.id ? { ...t, has_feedback: true } : t))
            );
            setShowFeedbackModal(null);
          }}
        />
      )}
    </div>
  );
};

// Feedback Modal Component
interface FeedbackModalProps {
  task: TaskSummary;
  onClose: () => void;
  onSubmit: (feedback: { rating: number; feedback_type: string; comment?: string }) => Promise<void>;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ task, onClose, onSubmit }) => {
  const [rating, setRating] = useState(3);
  const [feedbackType, setFeedbackType] = useState('other');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onSubmit({ rating, feedback_type: feedbackType, comment: comment || undefined });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold mb-4">Provide Feedback</h3>

        <div className="mb-4">
          <div className="text-sm text-gray-600 mb-2 truncate">
            Task: {task.request_preview}
          </div>
        </div>

        {/* Rating */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Rating
          </label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map(value => (
              <button
                key={value}
                onClick={() => setRating(value)}
                className={`w-10 h-10 rounded-lg border-2 font-medium transition-colors ${
                  rating === value
                    ? 'border-jarvis-500 bg-jarvis-50 text-jarvis-700'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {value}
              </button>
            ))}
          </div>
        </div>

        {/* Feedback Type */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What stood out?
          </label>
          <select
            value={feedbackType}
            onChange={e => setFeedbackType(e.target.value)}
            className="input"
          >
            <option value="helpful">Helpful</option>
            <option value="accurate">Accurate</option>
            <option value="fast">Fast</option>
            <option value="creative">Creative</option>
            <option value="other">Other</option>
          </select>
        </div>

        {/* Comment */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Comment (optional)
          </label>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Any additional feedback..."
            className="input h-24 resize-none"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="btn-primary"
          >
            {submitting ? 'Submitting...' : 'Submit'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RecentTasks;
