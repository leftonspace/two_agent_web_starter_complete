/**
 * JARVIS Gmail Add-on
 *
 * AI-powered email features for Gmail:
 * - Email summarization
 * - Quick reply suggestions
 * - Response drafting
 * - Priority classification
 * - Calendar integration
 */

// Configuration
const JARVIS_API_BASE = 'http://localhost:8000/api';
const CACHE_DURATION = 300; // 5 minutes

/**
 * Homepage card when add-on is opened
 */
function onHomepage(e) {
  return createHomepageCard();
}

/**
 * Create the homepage card
 */
function createHomepageCard() {
  const header = CardService.newCardHeader()
    .setTitle('JARVIS Email Assistant')
    .setSubtitle('AI-powered email management')
    .setImageUrl('https://your-domain.com/assets/icon-48.png')
    .setImageStyle(CardService.ImageStyle.CIRCLE);

  const welcomeSection = CardService.newCardSection()
    .addWidget(CardService.newTextParagraph()
      .setText('Welcome to JARVIS! Select an email to get started with AI-powered features.'));

  const featuresSection = CardService.newCardSection()
    .setHeader('Features')
    .addWidget(CardService.newDecoratedText()
      .setText('Email Summarization')
      .setBottomLabel('Get AI summaries of emails and threads')
      .setStartIcon(CardService.newIconImage()
        .setIcon(CardService.Icon.DESCRIPTION)))
    .addWidget(CardService.newDecoratedText()
      .setText('Quick Replies')
      .setBottomLabel('One-click smart reply suggestions')
      .setStartIcon(CardService.newIconImage()
        .setIcon(CardService.Icon.EMAIL)))
    .addWidget(CardService.newDecoratedText()
      .setText('AI Drafting')
      .setBottomLabel('Generate professional responses')
      .setStartIcon(CardService.newIconImage()
        .setIcon(CardService.Icon.PENCIL)))
    .addWidget(CardService.newDecoratedText()
      .setText('Smart Classification')
      .setBottomLabel('Auto-categorize and prioritize')
      .setStartIcon(CardService.newIconImage()
        .setIcon(CardService.Icon.BOOKMARK)));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(welcomeSection)
    .addSection(featuresSection)
    .build();

  return card;
}

/**
 * Triggered when viewing an email
 */
function onGmailMessage(e) {
  const accessToken = e.gmail.accessToken;
  const messageId = e.gmail.messageId;

  // Get email data
  GmailApp.setCurrentMessageAccessToken(accessToken);
  const message = GmailApp.getMessageById(messageId);

  if (!message) {
    return createErrorCard('Could not load email');
  }

  // Extract email data
  const emailData = {
    id: messageId,
    subject: message.getSubject(),
    sender: message.getFrom(),
    senderEmail: extractEmail(message.getFrom()),
    recipients: message.getTo().split(',').map(r => r.trim()),
    body: message.getPlainBody(),
    date: message.getDate().toISOString(),
    threadId: message.getThread().getId()
  };

  // Create the main action card
  return createEmailActionsCard(emailData);
}

/**
 * Create the main actions card for an email
 */
function createEmailActionsCard(emailData) {
  const header = CardService.newCardHeader()
    .setTitle('JARVIS Assistant')
    .setSubtitle(truncate(emailData.subject, 40));

  // Quick actions section
  const actionsSection = CardService.newCardSection()
    .setHeader('Quick Actions')
    .addWidget(CardService.newButtonSet()
      .addButton(CardService.newTextButton()
        .setText('Summarize')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('summarizeEmail')
          .setParameters({ emailData: JSON.stringify(emailData) })))
      .addButton(CardService.newTextButton()
        .setText('Quick Reply')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('showQuickReplies')
          .setParameters({ emailData: JSON.stringify(emailData) }))))
    .addWidget(CardService.newButtonSet()
      .addButton(CardService.newTextButton()
        .setText('Classify')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('classifyEmail')
          .setParameters({ emailData: JSON.stringify(emailData) })))
      .addButton(CardService.newTextButton()
        .setText('AI Draft')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('showDraftForm')
          .setParameters({ emailData: JSON.stringify(emailData) }))));

  // Email info section
  const infoSection = CardService.newCardSection()
    .setHeader('Email Info')
    .addWidget(CardService.newDecoratedText()
      .setText(emailData.sender)
      .setTopLabel('From')
      .setWrapText(true))
    .addWidget(CardService.newDecoratedText()
      .setText(formatDate(new Date(emailData.date)))
      .setTopLabel('Date'));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(actionsSection)
    .addSection(infoSection)
    .build();

  return card;
}

/**
 * Summarize email action
 */
function summarizeEmail(e) {
  const emailData = JSON.parse(e.parameters.emailData);

  try {
    // Try API call first
    const summary = callJarvisAPI('/admin/email/summarize', emailData);
    return createSummaryCard(summary);
  } catch (error) {
    // Fallback to local processing
    const summary = generateLocalSummary(emailData);
    return createSummaryCard(summary);
  }
}

/**
 * Create summary result card
 */
function createSummaryCard(summary) {
  const header = CardService.newCardHeader()
    .setTitle('Email Summary');

  const metaSection = CardService.newCardSection()
    .addWidget(CardService.newDecoratedText()
      .setText(summary.priority.toUpperCase())
      .setTopLabel('Priority')
      .setStartIcon(getPriorityIcon(summary.priority)))
    .addWidget(CardService.newDecoratedText()
      .setText(summary.category.replace('_', ' ').toUpperCase())
      .setTopLabel('Category'))
    .addWidget(CardService.newDecoratedText()
      .setText(summary.sentiment.toUpperCase())
      .setTopLabel('Sentiment'));

  let keyPointsText = '';
  if (summary.key_points && summary.key_points.length > 0) {
    keyPointsText = summary.key_points.map((p, i) => `${i + 1}. ${p}`).join('\n\n');
  }

  const keyPointsSection = CardService.newCardSection()
    .setHeader('Key Points')
    .addWidget(CardService.newTextParagraph()
      .setText(keyPointsText || 'No key points identified'));

  let actionItemsText = '';
  if (summary.action_items && summary.action_items.length > 0) {
    actionItemsText = summary.action_items.map(a => `• ${a}`).join('\n');
  }

  const actionItemsSection = CardService.newCardSection()
    .setHeader('Action Items')
    .addWidget(CardService.newTextParagraph()
      .setText(actionItemsText || 'No action items identified'));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(metaSection)
    .addSection(keyPointsSection)
    .addSection(actionItemsSection)
    .build();

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().pushCard(card))
    .build();
}

/**
 * Show quick reply options
 */
function showQuickReplies(e) {
  const emailData = JSON.parse(e.parameters.emailData);

  try {
    const replies = callJarvisAPI('/admin/email/quick-replies', emailData);
    return createQuickRepliesCard(replies, emailData);
  } catch (error) {
    const replies = generateLocalQuickReplies(emailData);
    return createQuickRepliesCard(replies, emailData);
  }
}

/**
 * Create quick replies card
 */
function createQuickRepliesCard(replies, emailData) {
  const header = CardService.newCardHeader()
    .setTitle('Quick Replies');

  const repliesSection = CardService.newCardSection();

  replies.forEach((reply, index) => {
    repliesSection.addWidget(CardService.newDecoratedText()
      .setText(reply.label)
      .setBottomLabel(truncate(reply.text, 80))
      .setWrapText(true)
      .setOnClickAction(CardService.newAction()
        .setFunctionName('insertQuickReply')
        .setParameters({
          replyText: reply.text,
          emailData: JSON.stringify(emailData)
        })));
  });

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(repliesSection)
    .build();

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().pushCard(card))
    .build();
}

/**
 * Insert quick reply and create draft
 */
function insertQuickReply(e) {
  const replyText = e.parameters.replyText;
  const emailData = JSON.parse(e.parameters.emailData);

  // Create draft reply
  const thread = GmailApp.getThreadById(emailData.threadId);
  const draft = thread.createDraftReply(replyText);

  return CardService.newActionResponseBuilder()
    .setNotification(CardService.newNotification()
      .setText('Draft created! Check your drafts folder.'))
    .build();
}

/**
 * Classify email
 */
function classifyEmail(e) {
  const emailData = JSON.parse(e.parameters.emailData);

  try {
    const classification = callJarvisAPI('/admin/email/classify', emailData);
    return createClassificationCard(classification);
  } catch (error) {
    const classification = classifyLocally(emailData);
    return createClassificationCard(classification);
  }
}

/**
 * Create classification result card
 */
function createClassificationCard(classification) {
  const header = CardService.newCardHeader()
    .setTitle('Email Classification');

  const classSection = CardService.newCardSection()
    .addWidget(CardService.newDecoratedText()
      .setText(classification.priority.toUpperCase())
      .setTopLabel('Priority')
      .setStartIcon(getPriorityIcon(classification.priority)))
    .addWidget(CardService.newDecoratedText()
      .setText(classification.category.replace('_', ' ').toUpperCase())
      .setTopLabel('Category'))
    .addWidget(CardService.newDecoratedText()
      .setText(classification.sentiment.toUpperCase())
      .setTopLabel('Sentiment'));

  if (classification.requires_action) {
    classSection.addWidget(CardService.newDecoratedText()
      .setText('Yes')
      .setTopLabel('Action Required')
      .setStartIcon(CardService.newIconImage()
        .setIcon(CardService.Icon.INVITE)));
  }

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(classSection)
    .build();

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().pushCard(card))
    .build();
}

/**
 * Show draft composition form
 */
function showDraftForm(e) {
  const emailData = JSON.parse(e.parameters.emailData);

  const header = CardService.newCardHeader()
    .setTitle('AI Draft Assistant');

  const formSection = CardService.newCardSection()
    .addWidget(CardService.newTextInput()
      .setFieldName('intent')
      .setTitle('What would you like to communicate?')
      .setHint('e.g., Politely decline and suggest alternative time')
      .setMultiline(true))
    .addWidget(CardService.newSelectionInput()
      .setFieldName('tone')
      .setTitle('Tone')
      .setType(CardService.SelectionInputType.DROPDOWN)
      .addItem('Professional', 'professional', true)
      .addItem('Friendly', 'friendly', false)
      .addItem('Formal', 'formal', false)
      .addItem('Casual', 'casual', false))
    .addWidget(CardService.newTextButton()
      .setText('Generate Draft')
      .setTextButtonStyle(CardService.TextButtonStyle.FILLED)
      .setOnClickAction(CardService.newAction()
        .setFunctionName('generateDraft')
        .setParameters({ emailData: JSON.stringify(emailData) })));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(formSection)
    .build();

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().pushCard(card))
    .build();
}

/**
 * Generate AI draft
 */
function generateDraft(e) {
  const emailData = JSON.parse(e.parameters.emailData);
  const intent = e.formInput.intent;
  const tone = e.formInput.tone;

  if (!intent) {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('Please describe what you want to communicate'))
      .build();
  }

  try {
    const draft = callJarvisAPI('/admin/email/draft', {
      email: emailData,
      intent: intent,
      tone: tone
    });
    return createDraftResultCard(draft, emailData);
  } catch (error) {
    const draft = generateLocalDraft(emailData, intent, tone);
    return createDraftResultCard(draft, emailData);
  }
}

/**
 * Create draft result card
 */
function createDraftResultCard(draft, emailData) {
  const header = CardService.newCardHeader()
    .setTitle('Generated Draft');

  const draftSection = CardService.newCardSection()
    .addWidget(CardService.newDecoratedText()
      .setText(draft.subject)
      .setTopLabel('Subject'))
    .addWidget(CardService.newTextParagraph()
      .setText(draft.body))
    .addWidget(CardService.newButtonSet()
      .addButton(CardService.newTextButton()
        .setText('Create Draft')
        .setTextButtonStyle(CardService.TextButtonStyle.FILLED)
        .setOnClickAction(CardService.newAction()
          .setFunctionName('createGmailDraft')
          .setParameters({
            subject: draft.subject,
            body: draft.body,
            emailData: JSON.stringify(emailData)
          })))
      .addButton(CardService.newTextButton()
        .setText('Copy Text')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('copyToClipboard')
          .setParameters({ text: draft.body }))));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(draftSection)
    .build();

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().pushCard(card))
    .build();
}

/**
 * Create Gmail draft with generated content
 */
function createGmailDraft(e) {
  const subject = e.parameters.subject;
  const body = e.parameters.body;
  const emailData = JSON.parse(e.parameters.emailData);

  // Create reply draft
  const thread = GmailApp.getThreadById(emailData.threadId);
  thread.createDraftReply(body);

  return CardService.newActionResponseBuilder()
    .setNotification(CardService.newNotification()
      .setText('Draft created successfully!'))
    .build();
}

/**
 * Compose trigger - AI assistance while composing
 */
function onCompose(e) {
  const header = CardService.newCardHeader()
    .setTitle('AI Writing Assistant');

  const assistSection = CardService.newCardSection()
    .addWidget(CardService.newTextInput()
      .setFieldName('instruction')
      .setTitle('How can I help?')
      .setHint('e.g., Make this more professional, Fix grammar, Shorten this')
      .setMultiline(true))
    .addWidget(CardService.newTextButton()
      .setText('Improve Draft')
      .setTextButtonStyle(CardService.TextButtonStyle.FILLED)
      .setOnClickAction(CardService.newAction()
        .setFunctionName('improveDraft')));

  const suggestionsSection = CardService.newCardSection()
    .setHeader('Quick Actions')
    .addWidget(CardService.newTextButton()
      .setText('Make Professional')
      .setOnClickAction(CardService.newAction()
        .setFunctionName('applyStyle')
        .setParameters({ style: 'professional' })))
    .addWidget(CardService.newTextButton()
      .setText('Make Concise')
      .setOnClickAction(CardService.newAction()
        .setFunctionName('applyStyle')
        .setParameters({ style: 'concise' })))
    .addWidget(CardService.newTextButton()
      .setText('Fix Grammar')
      .setOnClickAction(CardService.newAction()
        .setFunctionName('applyStyle')
        .setParameters({ style: 'grammar' })));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(assistSection)
    .addSection(suggestionsSection)
    .build();

  return card;
}

/**
 * Settings card
 */
function showSettings(e) {
  const header = CardService.newCardHeader()
    .setTitle('Settings');

  const settingsSection = CardService.newCardSection()
    .addWidget(CardService.newTextInput()
      .setFieldName('apiUrl')
      .setTitle('JARVIS API URL')
      .setValue(getUserProperty('apiUrl') || JARVIS_API_BASE))
    .addWidget(CardService.newSelectionInput()
      .setFieldName('defaultTone')
      .setTitle('Default Response Tone')
      .setType(CardService.SelectionInputType.DROPDOWN)
      .addItem('Professional', 'professional', true)
      .addItem('Friendly', 'friendly', false)
      .addItem('Formal', 'formal', false))
    .addWidget(CardService.newTextButton()
      .setText('Save Settings')
      .setTextButtonStyle(CardService.TextButtonStyle.FILLED)
      .setOnClickAction(CardService.newAction()
        .setFunctionName('saveSettings')));

  const card = CardService.newCardBuilder()
    .setHeader(header)
    .addSection(settingsSection)
    .build();

  return CardService.newActionResponseBuilder()
    .setNavigation(CardService.newNavigation().pushCard(card))
    .build();
}

/**
 * Save user settings
 */
function saveSettings(e) {
  const apiUrl = e.formInput.apiUrl;
  const defaultTone = e.formInput.defaultTone;

  setUserProperty('apiUrl', apiUrl);
  setUserProperty('defaultTone', defaultTone);

  return CardService.newActionResponseBuilder()
    .setNotification(CardService.newNotification()
      .setText('Settings saved!'))
    .build();
}

// API Helper Functions

function callJarvisAPI(endpoint, data) {
  const apiUrl = getUserProperty('apiUrl') || JARVIS_API_BASE;

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(data),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(apiUrl + endpoint, options);
  const responseCode = response.getResponseCode();

  if (responseCode !== 200) {
    throw new Error('API request failed: ' + responseCode);
  }

  return JSON.parse(response.getContentText());
}

// Local Fallback Functions

function generateLocalSummary(emailData) {
  const body = emailData.body.toLowerCase();

  let priority = 'normal';
  if (body.includes('urgent') || body.includes('asap')) priority = 'urgent';
  else if (body.includes('important')) priority = 'high';

  let category = 'fyi';
  if (body.includes('meeting')) category = 'meeting';
  else if (body.includes('please') || body.includes('could you')) category = 'action_required';

  let sentiment = 'neutral';
  if (body.includes('thanks') || body.includes('great')) sentiment = 'positive';
  else if (body.includes('concern') || body.includes('issue')) sentiment = 'negative';

  const sentences = emailData.body.split(/[.!?]+/).filter(s => s.trim().length > 20);
  const keyPoints = sentences.slice(0, 3).map(s => s.trim());

  const actionItems = [];
  const actionPatterns = /please (.+?)[.!?\n]/gi;
  let match;
  while ((match = actionPatterns.exec(emailData.body)) !== null) {
    actionItems.push(match[1].trim());
  }

  return {
    key_points: keyPoints,
    action_items: actionItems.slice(0, 5),
    sentiment: sentiment,
    priority: priority,
    category: category
  };
}

function generateLocalQuickReplies(emailData) {
  const firstName = emailData.sender.split(' ')[0].replace(/[<>]/g, '');

  return [
    {
      label: 'Acknowledge',
      text: 'Hi ' + firstName + ',\n\nThank you for your email. I\'ve received it and will review shortly.\n\nBest regards'
    },
    {
      label: 'Will Follow Up',
      text: 'Hi ' + firstName + ',\n\nThanks for reaching out. Let me look into this and get back to you.\n\nBest regards'
    },
    {
      label: 'Need More Info',
      text: 'Hi ' + firstName + ',\n\nThanks for your message. Could you please provide more details?\n\nBest regards'
    }
  ];
}

function classifyLocally(emailData) {
  const body = emailData.body.toLowerCase();

  return {
    priority: body.includes('urgent') ? 'urgent' : body.includes('important') ? 'high' : 'normal',
    category: body.includes('meeting') ? 'meeting' : body.includes('please') ? 'action_required' : 'fyi',
    sentiment: body.includes('thanks') ? 'positive' : body.includes('concern') ? 'negative' : 'neutral',
    requires_action: body.includes('please') || body.includes('could you')
  };
}

function generateLocalDraft(emailData, intent, tone) {
  const firstName = emailData.sender.split(' ')[0].replace(/[<>]/g, '');

  const greetings = {
    professional: 'Hi ' + firstName + ',',
    friendly: 'Hey ' + firstName + '!',
    formal: 'Dear ' + firstName + ',',
    casual: 'Hi ' + firstName + ','
  };

  const body = (greetings[tone] || greetings.professional) +
    '\n\nThank you for your email. ' + intent +
    '\n\nBest regards';

  return {
    subject: emailData.subject.startsWith('Re:') ? emailData.subject : 'Re: ' + emailData.subject,
    body: body,
    tone: tone
  };
}

// Utility Functions

function extractEmail(fromString) {
  const match = fromString.match(/<(.+)>/);
  return match ? match[1] : fromString;
}

function truncate(str, maxLen) {
  if (!str) return '';
  return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function formatDate(date) {
  return Utilities.formatDate(date, Session.getScriptTimeZone(), 'MMM d, yyyy h:mm a');
}

function getPriorityIcon(priority) {
  switch (priority) {
    case 'urgent':
      return CardService.newIconImage().setIcon(CardService.Icon.INVITE);
    case 'high':
      return CardService.newIconImage().setIcon(CardService.Icon.STAR);
    default:
      return CardService.newIconImage().setIcon(CardService.Icon.DESCRIPTION);
  }
}

function getUserProperty(key) {
  return PropertiesService.getUserProperties().getProperty(key);
}

function setUserProperty(key, value) {
  PropertiesService.getUserProperties().setProperty(key, value);
}

function createErrorCard(message) {
  return CardService.newCardBuilder()
    .addSection(CardService.newCardSection()
      .addWidget(CardService.newTextParagraph()
        .setText('Error: ' + message)))
    .build();
}
