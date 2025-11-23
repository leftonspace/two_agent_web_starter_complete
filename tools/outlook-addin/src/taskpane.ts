/**
 * JARVIS Outlook Add-in - Task Pane
 *
 * Provides AI-powered email features:
 * - Email summarization
 * - Quick reply suggestions
 * - Response drafting
 * - Priority classification
 */

// Configuration
const JARVIS_API_BASE = 'http://localhost:8000/api';

interface EmailData {
  id: string;
  subject: string;
  sender: string;
  senderEmail: string;
  recipients: string[];
  body: string;
  timestamp: string;
  threadId?: string;
}

interface EmailSummary {
  subject: string;
  key_points: string[];
  action_items: string[];
  sentiment: string;
  priority: string;
  category: string;
  participants: string[];
}

interface QuickReply {
  label: string;
  text: string;
}

interface DraftResponse {
  subject: string;
  body: string;
  tone: string;
  alternatives: string[];
}

// Global state
let currentEmail: EmailData | null = null;

/**
 * Initialize the add-in when Office is ready
 */
Office.onReady((info) => {
  if (info.host === Office.HostType.Outlook) {
    document.getElementById('app-body')!.style.display = 'flex';
    document.getElementById('loading')!.style.display = 'none';

    // Set up event handlers
    setupEventHandlers();

    // Load current email data
    loadCurrentEmail();
  }
});

/**
 * Set up UI event handlers
 */
function setupEventHandlers(): void {
  document.getElementById('summarize-btn')?.addEventListener('click', summarizeEmail);
  document.getElementById('quick-reply-btn')?.addEventListener('click', showQuickReplies);
  document.getElementById('classify-btn')?.addEventListener('click', classifyEmail);
  document.getElementById('draft-btn')?.addEventListener('click', showDraftPanel);

  // Tone selector for drafting
  document.querySelectorAll('.tone-option').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      document.querySelectorAll('.tone-option').forEach(b => b.classList.remove('selected'));
      target.classList.add('selected');
    });
  });

  // Generate draft button
  document.getElementById('generate-draft-btn')?.addEventListener('click', generateDraft);

  // Insert reply buttons
  document.getElementById('quick-replies')?.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    if (target.classList.contains('insert-btn')) {
      const text = target.dataset.text;
      if (text) {
        insertReply(text);
      }
    }
  });
}

/**
 * Load current email data from Outlook
 */
async function loadCurrentEmail(): Promise<void> {
  const item = Office.context.mailbox.item;

  if (!item) {
    showError('No email selected');
    return;
  }

  try {
    // Get email data
    const subject = item.subject;
    const sender = item.sender?.displayName || 'Unknown';
    const senderEmail = item.sender?.emailAddress || '';

    // Get recipients
    const recipients: string[] = [];
    if (item.to) {
      item.to.forEach((r: Office.EmailAddressDetails) => {
        recipients.push(r.emailAddress);
      });
    }

    // Get body
    const bodyResult = await new Promise<Office.AsyncResult<string>>((resolve) => {
      item.body.getAsync(Office.CoercionType.Text, resolve);
    });

    const body = bodyResult.status === Office.AsyncResultStatus.Succeeded
      ? bodyResult.value
      : '';

    // Get conversation ID for thread detection
    const conversationId = item.conversationId;

    currentEmail = {
      id: item.itemId || '',
      subject: subject || '',
      sender,
      senderEmail,
      recipients,
      body,
      timestamp: new Date().toISOString(),
      threadId: conversationId
    };

    // Update UI with email info
    updateEmailInfo();

  } catch (error) {
    showError('Failed to load email: ' + error);
  }
}

/**
 * Update UI with current email info
 */
function updateEmailInfo(): void {
  if (!currentEmail) return;

  const infoEl = document.getElementById('email-info');
  if (infoEl) {
    infoEl.innerHTML = `
      <div class="email-subject">${escapeHtml(currentEmail.subject)}</div>
      <div class="email-sender">From: ${escapeHtml(currentEmail.sender)}</div>
    `;
  }
}

/**
 * Summarize the current email
 */
async function summarizeEmail(): Promise<void> {
  if (!currentEmail) {
    showError('No email loaded');
    return;
  }

  showLoading('summarize-btn', true);

  try {
    const response = await fetch(`${JARVIS_API_BASE}/admin/email/summarize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: currentEmail.id,
        subject: currentEmail.subject,
        sender: currentEmail.sender,
        sender_email: currentEmail.senderEmail,
        recipients: currentEmail.recipients,
        body: currentEmail.body,
        timestamp: currentEmail.timestamp
      })
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const summary: EmailSummary = await response.json();
    displaySummary(summary);

  } catch (error) {
    // Fallback to client-side summary if API unavailable
    const summary = generateLocalSummary(currentEmail);
    displaySummary(summary);
  } finally {
    showLoading('summarize-btn', false);
  }
}

/**
 * Display email summary
 */
function displaySummary(summary: EmailSummary): void {
  const resultsEl = document.getElementById('results');
  if (!resultsEl) return;

  resultsEl.innerHTML = `
    <div class="summary-card">
      <h3>Email Summary</h3>

      <div class="summary-meta">
        <span class="badge priority-${summary.priority}">${summary.priority}</span>
        <span class="badge category-${summary.category}">${summary.category}</span>
        <span class="badge sentiment-${summary.sentiment}">${summary.sentiment}</span>
      </div>

      ${summary.key_points.length > 0 ? `
        <div class="summary-section">
          <h4>Key Points</h4>
          <ul>
            ${summary.key_points.map(p => `<li>${escapeHtml(p)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${summary.action_items.length > 0 ? `
        <div class="summary-section">
          <h4>Action Items</h4>
          <ul class="action-items">
            ${summary.action_items.map(a => `<li>${escapeHtml(a)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      <div class="summary-section">
        <h4>Participants</h4>
        <p>${summary.participants.map(p => escapeHtml(p)).join(', ')}</p>
      </div>
    </div>
  `;
}

/**
 * Show quick reply suggestions
 */
async function showQuickReplies(): Promise<void> {
  if (!currentEmail) {
    showError('No email loaded');
    return;
  }

  showLoading('quick-reply-btn', true);

  try {
    const response = await fetch(`${JARVIS_API_BASE}/admin/email/quick-replies`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: currentEmail.id,
        subject: currentEmail.subject,
        sender: currentEmail.sender,
        sender_email: currentEmail.senderEmail,
        recipients: currentEmail.recipients,
        body: currentEmail.body
      })
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const replies: QuickReply[] = await response.json();
    displayQuickReplies(replies);

  } catch (error) {
    // Fallback to local quick replies
    const replies = generateLocalQuickReplies(currentEmail);
    displayQuickReplies(replies);
  } finally {
    showLoading('quick-reply-btn', false);
  }
}

/**
 * Display quick reply options
 */
function displayQuickReplies(replies: QuickReply[]): void {
  const resultsEl = document.getElementById('results');
  if (!resultsEl) return;

  resultsEl.innerHTML = `
    <div class="quick-replies-card">
      <h3>Quick Replies</h3>
      <div id="quick-replies" class="replies-list">
        ${replies.map(r => `
          <div class="reply-option">
            <span class="reply-label">${escapeHtml(r.label)}</span>
            <p class="reply-preview">${escapeHtml(r.text.substring(0, 100))}...</p>
            <button class="insert-btn" data-text="${escapeHtml(r.text)}">
              Insert Reply
            </button>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

/**
 * Classify the current email
 */
async function classifyEmail(): Promise<void> {
  if (!currentEmail) {
    showError('No email loaded');
    return;
  }

  showLoading('classify-btn', true);

  try {
    const response = await fetch(`${JARVIS_API_BASE}/admin/email/classify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id: currentEmail.id,
        subject: currentEmail.subject,
        body: currentEmail.body
      })
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const classification = await response.json();
    displayClassification(classification);

  } catch (error) {
    // Fallback to local classification
    const classification = classifyLocally(currentEmail);
    displayClassification(classification);
  } finally {
    showLoading('classify-btn', false);
  }
}

/**
 * Display email classification
 */
function displayClassification(classification: any): void {
  const resultsEl = document.getElementById('results');
  if (!resultsEl) return;

  resultsEl.innerHTML = `
    <div class="classification-card">
      <h3>Email Classification</h3>
      <div class="classification-result">
        <div class="class-item">
          <span class="class-label">Priority</span>
          <span class="class-value badge priority-${classification.priority}">
            ${classification.priority}
          </span>
        </div>
        <div class="class-item">
          <span class="class-label">Category</span>
          <span class="class-value badge">${classification.category}</span>
        </div>
        <div class="class-item">
          <span class="class-label">Sentiment</span>
          <span class="class-value badge sentiment-${classification.sentiment}">
            ${classification.sentiment}
          </span>
        </div>
        ${classification.requires_action ? `
          <div class="class-item alert">
            <span class="class-label">Action Required</span>
            <span class="class-value">Yes</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

/**
 * Show the draft composition panel
 */
function showDraftPanel(): void {
  const resultsEl = document.getElementById('results');
  if (!resultsEl) return;

  resultsEl.innerHTML = `
    <div class="draft-panel">
      <h3>AI Draft Assistant</h3>

      <div class="form-group">
        <label>What would you like to communicate?</label>
        <textarea id="draft-intent" placeholder="e.g., Politely decline the meeting request and suggest an alternative time..."></textarea>
      </div>

      <div class="form-group">
        <label>Tone</label>
        <div class="tone-options">
          <button class="tone-option selected" data-tone="professional">Professional</button>
          <button class="tone-option" data-tone="friendly">Friendly</button>
          <button class="tone-option" data-tone="formal">Formal</button>
          <button class="tone-option" data-tone="casual">Casual</button>
        </div>
      </div>

      <button id="generate-draft-btn" class="primary-btn">Generate Draft</button>

      <div id="draft-result"></div>
    </div>
  `;

  // Re-attach event handlers for the new elements
  document.querySelectorAll('.tone-option').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      document.querySelectorAll('.tone-option').forEach(b => b.classList.remove('selected'));
      target.classList.add('selected');
    });
  });

  document.getElementById('generate-draft-btn')?.addEventListener('click', generateDraft);
}

/**
 * Generate email draft
 */
async function generateDraft(): Promise<void> {
  if (!currentEmail) {
    showError('No email loaded');
    return;
  }

  const intent = (document.getElementById('draft-intent') as HTMLTextAreaElement)?.value;
  if (!intent) {
    showError('Please describe what you want to communicate');
    return;
  }

  const selectedTone = document.querySelector('.tone-option.selected') as HTMLElement;
  const tone = selectedTone?.dataset.tone || 'professional';

  showLoading('generate-draft-btn', true);

  try {
    const response = await fetch(`${JARVIS_API_BASE}/admin/email/draft`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: {
          id: currentEmail.id,
          subject: currentEmail.subject,
          sender: currentEmail.sender,
          sender_email: currentEmail.senderEmail,
          recipients: currentEmail.recipients,
          body: currentEmail.body
        },
        intent,
        tone
      })
    });

    if (!response.ok) {
      throw new Error('API request failed');
    }

    const draft: DraftResponse = await response.json();
    displayDraft(draft);

  } catch (error) {
    // Fallback to local draft
    const draft = generateLocalDraft(currentEmail, intent, tone);
    displayDraft(draft);
  } finally {
    showLoading('generate-draft-btn', false);
  }
}

/**
 * Display generated draft
 */
function displayDraft(draft: DraftResponse): void {
  const draftResultEl = document.getElementById('draft-result');
  if (!draftResultEl) return;

  draftResultEl.innerHTML = `
    <div class="draft-card">
      <div class="draft-subject">
        <strong>Subject:</strong> ${escapeHtml(draft.subject)}
      </div>
      <div class="draft-body">
        <pre>${escapeHtml(draft.body)}</pre>
      </div>
      <div class="draft-actions">
        <button class="primary-btn" onclick="insertDraft('${encodeURIComponent(draft.body)}')">
          Use This Draft
        </button>
        <button class="secondary-btn" onclick="copyDraft('${encodeURIComponent(draft.body)}')">
          Copy to Clipboard
        </button>
      </div>

      ${draft.alternatives.length > 0 ? `
        <div class="alternatives">
          <h4>Alternative Versions</h4>
          ${draft.alternatives.map((alt, i) => `
            <div class="alternative">
              <p>${escapeHtml(alt)}</p>
              <button class="small-btn" onclick="insertDraft('${encodeURIComponent(alt)}')">
                Use
              </button>
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

/**
 * Insert reply text into compose window
 */
async function insertReply(text: string): Promise<void> {
  try {
    const item = Office.context.mailbox.item;

    if (item && item.body) {
      await new Promise<void>((resolve, reject) => {
        item.body.setAsync(
          text,
          { coercionType: Office.CoercionType.Text },
          (result) => {
            if (result.status === Office.AsyncResultStatus.Succeeded) {
              resolve();
            } else {
              reject(result.error);
            }
          }
        );
      });

      showSuccess('Reply inserted');
    }
  } catch (error) {
    showError('Failed to insert reply: ' + error);
  }
}

// Global functions for inline handlers
(window as any).insertDraft = (encodedText: string) => {
  insertReply(decodeURIComponent(encodedText));
};

(window as any).copyDraft = (encodedText: string) => {
  const text = decodeURIComponent(encodedText);
  navigator.clipboard.writeText(text).then(() => {
    showSuccess('Copied to clipboard');
  });
};

// Local fallback functions

function generateLocalSummary(email: EmailData): EmailSummary {
  const body = email.body.toLowerCase();

  // Simple priority detection
  let priority = 'normal';
  if (body.includes('urgent') || body.includes('asap')) priority = 'urgent';
  else if (body.includes('important') || body.includes('priority')) priority = 'high';

  // Simple category detection
  let category = 'fyi';
  if (body.includes('meeting') || body.includes('calendar')) category = 'meeting';
  else if (body.includes('please') || body.includes('could you')) category = 'action_required';

  // Simple sentiment
  let sentiment = 'neutral';
  if (body.includes('thanks') || body.includes('great')) sentiment = 'positive';
  else if (body.includes('concern') || body.includes('issue')) sentiment = 'negative';

  // Extract key sentences
  const sentences = email.body.split(/[.!?]+/).filter(s => s.trim().length > 20);
  const keyPoints = sentences.slice(0, 3).map(s => s.trim());

  // Look for action items
  const actionPatterns = /please (.+?)[.!?\n]/gi;
  const actionItems: string[] = [];
  let match;
  while ((match = actionPatterns.exec(email.body)) !== null) {
    actionItems.push(match[1].trim());
  }

  return {
    subject: email.subject,
    key_points: keyPoints,
    action_items: actionItems.slice(0, 5),
    sentiment,
    priority,
    category,
    participants: [email.sender, ...email.recipients]
  };
}

function generateLocalQuickReplies(email: EmailData): QuickReply[] {
  const firstName = email.sender.split(' ')[0];

  return [
    {
      label: 'Acknowledge',
      text: `Hi ${firstName},\n\nThank you for your email. I've received it and will review shortly.\n\nBest regards`
    },
    {
      label: 'Will Follow Up',
      text: `Hi ${firstName},\n\nThanks for reaching out. Let me look into this and get back to you.\n\nBest regards`
    },
    {
      label: 'Need More Info',
      text: `Hi ${firstName},\n\nThanks for your message. Could you please provide more details about this?\n\nBest regards`
    }
  ];
}

function classifyLocally(email: EmailData): any {
  const body = email.body.toLowerCase();

  return {
    priority: body.includes('urgent') ? 'urgent' :
              body.includes('important') ? 'high' : 'normal',
    category: body.includes('meeting') ? 'meeting' :
              body.includes('please') ? 'action_required' : 'fyi',
    sentiment: body.includes('thanks') ? 'positive' :
               body.includes('concern') ? 'negative' : 'neutral',
    requires_action: body.includes('please') || body.includes('could you')
  };
}

function generateLocalDraft(email: EmailData, intent: string, tone: string): DraftResponse {
  const firstName = email.sender.split(' ')[0];

  const greetings: Record<string, string> = {
    professional: `Hi ${firstName},`,
    friendly: `Hey ${firstName}!`,
    formal: `Dear ${firstName},`,
    casual: `Hi ${firstName},`
  };

  const body = `${greetings[tone] || greetings.professional}

Thank you for your email. ${intent}

Best regards`;

  return {
    subject: email.subject.startsWith('Re:') ? email.subject : `Re: ${email.subject}`,
    body,
    tone,
    alternatives: []
  };
}

// Utility functions

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showLoading(buttonId: string, loading: boolean): void {
  const btn = document.getElementById(buttonId);
  if (btn) {
    btn.classList.toggle('loading', loading);
    (btn as HTMLButtonElement).disabled = loading;
  }
}

function showError(message: string): void {
  const resultsEl = document.getElementById('results');
  if (resultsEl) {
    resultsEl.innerHTML = `<div class="error-message">${escapeHtml(message)}</div>`;
  }
}

function showSuccess(message: string): void {
  const notification = document.createElement('div');
  notification.className = 'success-notification';
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => notification.remove(), 3000);
}
