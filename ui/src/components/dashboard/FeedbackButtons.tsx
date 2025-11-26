import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, Send } from 'lucide-react';
import { Button, Input } from '../common';

export interface FeedbackButtonsProps {
  taskId: string;
  specialistId?: string;
  onFeedback?: (feedback: FeedbackData) => void;
  disabled?: boolean;
  showComment?: boolean;
  size?: 'sm' | 'md';
}

export interface FeedbackData {
  taskId: string;
  specialistId?: string;
  type: 'positive' | 'negative';
  comment?: string;
}

export const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({
  taskId,
  specialistId,
  onFeedback,
  disabled = false,
  showComment = true,
  size = 'md',
}) => {
  const [selected, setSelected] = useState<'positive' | 'negative' | null>(null);
  const [showCommentInput, setShowCommentInput] = useState(false);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleFeedback = (type: 'positive' | 'negative') => {
    if (disabled || submitted) return;

    setSelected(type);

    if (showComment) {
      setShowCommentInput(true);
    } else {
      submitFeedback(type);
    }
  };

  const submitFeedback = (type?: 'positive' | 'negative') => {
    const feedbackType = type || selected;
    if (!feedbackType) return;

    onFeedback?.({
      taskId,
      specialistId,
      type: feedbackType,
      comment: comment.trim() || undefined,
    });

    setSubmitted(true);
    setShowCommentInput(false);
  };

  const buttonSize = size === 'sm' ? 'sm' : 'md';

  if (submitted) {
    return (
      <div className={`feedback-buttons submitted ${size}`}>
        <div className="feedback-thanks">
          <span>Thanks for your feedback!</span>
        </div>
        <style>{feedbackStyles}</style>
      </div>
    );
  }

  return (
    <div className={`feedback-buttons ${size}`}>
      <div className="feedback-actions">
        <button
          className={`feedback-btn positive ${selected === 'positive' ? 'selected' : ''}`}
          onClick={() => handleFeedback('positive')}
          disabled={disabled}
          aria-label="Positive feedback"
        >
          <ThumbsUp className={size === 'sm' ? 'icon-sm' : 'icon'} />
        </button>
        <button
          className={`feedback-btn negative ${selected === 'negative' ? 'selected' : ''}`}
          onClick={() => handleFeedback('negative')}
          disabled={disabled}
          aria-label="Negative feedback"
        >
          <ThumbsDown className={size === 'sm' ? 'icon-sm' : 'icon'} />
        </button>
      </div>

      {showCommentInput && (
        <div className="feedback-comment">
          <div className="comment-input-wrapper">
            <MessageSquare className="icon-sm comment-icon" />
            <input
              type="text"
              className="comment-input"
              placeholder="Add a comment (optional)"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submitFeedback()}
              autoFocus
            />
            <button
              className="comment-submit"
              onClick={() => submitFeedback()}
              aria-label="Submit feedback"
            >
              <Send className="icon-sm" />
            </button>
          </div>
          <button
            className="comment-skip"
            onClick={() => submitFeedback()}
          >
            Skip
          </button>
        </div>
      )}

      <style>{feedbackStyles}</style>
    </div>
  );
};

const feedbackStyles = `
  .feedback-buttons {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .feedback-buttons.sm {
    gap: var(--space-1);
  }

  .feedback-actions {
    display: flex;
    gap: var(--space-2);
  }

  .feedback-buttons.sm .feedback-actions {
    gap: var(--space-1);
  }

  .feedback-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-2);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .feedback-buttons.sm .feedback-btn {
    padding: var(--space-1);
    border-radius: var(--radius-sm);
  }

  .feedback-btn:hover:not(:disabled) {
    border-color: var(--border-secondary);
    color: var(--text-primary);
  }

  .feedback-btn.positive:hover:not(:disabled),
  .feedback-btn.positive.selected {
    background: var(--accent-primary-dim);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }

  .feedback-btn.negative:hover:not(:disabled),
  .feedback-btn.negative.selected {
    background: var(--accent-danger-dim);
    border-color: var(--accent-danger);
    color: var(--accent-danger);
  }

  .feedback-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .feedback-comment {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    animation: fadeIn var(--transition-fast);
  }

  .comment-input-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2);
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
  }

  .comment-icon {
    color: var(--text-tertiary);
    flex-shrink: 0;
  }

  .comment-input {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: var(--text-sm);
    outline: none;
  }

  .comment-input::placeholder {
    color: var(--text-tertiary);
  }

  .comment-submit {
    padding: var(--space-1);
    background: var(--accent-primary);
    border: none;
    border-radius: var(--radius-sm);
    color: var(--bg-primary);
    cursor: pointer;
    transition: all var(--transition-fast);
    flex-shrink: 0;
  }

  .comment-submit:hover {
    opacity: 0.9;
  }

  .comment-skip {
    padding: var(--space-2);
    background: transparent;
    border: none;
    color: var(--text-tertiary);
    font-size: var(--text-sm);
    cursor: pointer;
    transition: color var(--transition-fast);
  }

  .comment-skip:hover {
    color: var(--text-secondary);
  }

  .feedback-thanks {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2);
    background: var(--accent-primary-dim);
    border-radius: var(--radius-md);
    color: var(--accent-primary);
    font-size: var(--text-sm);
  }
`;

export default FeedbackButtons;
