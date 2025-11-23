# JARVIS Administration Tools

Comprehensive administrative automation for email, calendar, and workflow management.

## Overview

The Administration module provides three core capabilities:

1. **Email Integration** - Summarization, response drafting, Outlook/Gmail plugins
2. **Calendar Intelligence** - Meeting briefs, action items, schedule optimization
3. **Workflow Automation** - Zapier/Make style triggers, multi-step execution

## Table of Contents

- [Quick Start](#quick-start)
- [Email Integration](#email-integration)
- [Calendar Intelligence](#calendar-intelligence)
- [Workflow Automation](#workflow-automation)
- [Email Plugins](#email-plugins)
- [API Reference](#api-reference)

---

## Quick Start

### API Endpoints

All admin APIs are available at `/api/admin/`:

```bash
# Health check
curl http://localhost:8000/api/admin/health

# Summarize an email
curl -X POST http://localhost:8000/api/admin/email/summarize \
  -H "Content-Type: application/json" \
  -d '{"id": "123", "subject": "Project Update", "sender": "John", ...}'

# Generate meeting brief
curl -X POST http://localhost:8000/api/admin/calendar/meeting-brief \
  -H "Content-Type: application/json" \
  -d '{"id": "mtg1", "title": "Weekly Sync", "start_time": "...", ...}'

# Create workflow
curl -X POST http://localhost:8000/api/admin/workflow/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Auto-reply", "trigger_config": {...}, "steps": [...]}'
```

---

## Email Integration

AI-powered email management with summarization, drafting, and classification.

### Features

| Feature | Description |
|---------|-------------|
| **Summarization** | Extract key points and action items from emails |
| **Thread Summary** | Summarize entire email threads with timeline |
| **Quick Replies** | Generate contextual quick reply options |
| **Draft Response** | AI-generated responses with tone control |
| **Classification** | Auto-categorize by priority, type, sentiment |
| **Daily Digest** | Summary of all daily emails |

### API: Summarize Email

```http
POST /api/admin/email/summarize
Content-Type: application/json

{
  "id": "email_123",
  "subject": "Q3 Budget Review",
  "sender": "John Smith",
  "sender_email": "john@company.com",
  "recipients": ["team@company.com"],
  "body": "Hi team, please review the attached Q3 budget...",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Response:**
```json
{
  "subject": "Q3 Budget Review",
  "key_points": [
    "Q3 budget needs review by team",
    "Attached document contains updated figures"
  ],
  "action_items": [
    "review the attached Q3 budget"
  ],
  "sentiment": "neutral",
  "priority": "normal",
  "category": "action_required",
  "participants": ["John Smith", "team@company.com"]
}
```

### API: Draft Response

```http
POST /api/admin/email/draft
Content-Type: application/json

{
  "email": {
    "id": "email_123",
    "subject": "Meeting Request",
    "sender": "Client",
    "sender_email": "client@external.com",
    "recipients": ["me@company.com"],
    "body": "Can we schedule a call next week?"
  },
  "intent": "Accept the meeting request and propose Tuesday afternoon",
  "tone": "professional"
}
```

**Response:**
```json
{
  "subject": "Re: Meeting Request",
  "body": "Hi Client,\n\nThank you for reaching out. I'd be happy to schedule a call. How about Tuesday afternoon? I'm available between 2-5 PM.\n\nBest regards",
  "tone": "professional",
  "suggested_recipients": ["client@external.com"],
  "alternatives": [
    "Got it, thanks! Tuesday afternoon works for me - 2-5 PM?"
  ]
}
```

### API: Quick Replies

```http
POST /api/admin/email/quick-replies
Content-Type: application/json

{
  "id": "email_123",
  "subject": "Can you review this?",
  "sender": "Alice",
  "sender_email": "alice@company.com",
  "recipients": ["me@company.com"],
  "body": "Hi, could you please review the attached document?"
}
```

**Response:**
```json
[
  {
    "label": "On it",
    "text": "Hi Alice,\n\nThanks for reaching out. I'll take care of this and update you once done.\n\nBest regards"
  },
  {
    "label": "Need more info",
    "text": "Hi Alice,\n\nThanks for this. Before I proceed, could you clarify...\n\nBest regards"
  },
  {
    "label": "Delegate",
    "text": "Hi Alice,\n\nI've looped in the right person to help with this.\n\nBest regards"
  }
]
```

### Response Tones

| Tone | Description | Use Case |
|------|-------------|----------|
| `professional` | Balanced, business appropriate | Default for work |
| `friendly` | Warm, approachable | Known colleagues |
| `formal` | Traditional, respectful | Executives, external |
| `casual` | Relaxed, conversational | Close teammates |
| `empathetic` | Understanding, supportive | Sensitive situations |
| `assertive` | Direct, confident | Negotiations |

---

## Calendar Intelligence

Smart calendar management with meeting preparation and optimization.

### Features

| Feature | Description |
|---------|-------------|
| **Meeting Briefs** | Pre-meeting preparation materials |
| **Action Items** | Extract tasks from meeting notes |
| **Meeting Summary** | Structured notes from raw text |
| **Schedule Optimization** | Analyze and improve calendar |
| **Slot Finding** | Find optimal meeting times |
| **Conflict Detection** | Identify scheduling conflicts |

### API: Meeting Brief

```http
POST /api/admin/calendar/meeting-brief
Content-Type: application/json

{
  "id": "mtg_123",
  "title": "1:1 with Manager",
  "start_time": "2025-01-15T14:00:00Z",
  "end_time": "2025-01-15T14:30:00Z",
  "attendees": [
    {"email": "manager@company.com", "name": "Manager", "required": true}
  ],
  "description": "Weekly check-in"
}
```

**Response:**
```json
{
  "meeting_type": "one_on_one",
  "priority": "normal",
  "preparation_items": [
    "Review meeting agenda and objectives",
    "Review notes from last 1:1",
    "Prepare discussion topics and updates",
    "Think about any blockers or support needed"
  ],
  "talking_points": [
    "Current project status and progress",
    "Blockers and challenges",
    "Upcoming priorities",
    "Career development and goals"
  ],
  "relevant_context": [
    "Meeting description: Weekly check-in"
  ],
  "suggested_questions": [
    "How are you feeling about your current workload?",
    "Is there anything blocking your progress?",
    "What support do you need from me?"
  ],
  "recommendations": []
}
```

### API: Extract Action Items

```http
POST /api/admin/calendar/action-items
Content-Type: application/json

{
  "meeting_notes": "Meeting notes:\n- John will send the report by Friday\n- TODO: Update the dashboard\n- Alice to follow up with client",
  "meeting_id": "mtg_123",
  "meeting_title": "Team Sync",
  "attendees": ["John", "Alice", "Bob"]
}
```

**Response:**
```json
[
  {
    "id": "mtg_123_action_1",
    "description": "send the report",
    "assignee": "John",
    "due_date": "2025-01-17T00:00:00Z",
    "priority": "normal",
    "status": "pending"
  },
  {
    "id": "mtg_123_action_2",
    "description": "Update the dashboard",
    "assignee": null,
    "due_date": null,
    "priority": "normal",
    "status": "pending"
  }
]
```

### API: Schedule Optimization

```http
POST /api/admin/calendar/optimize-schedule
Content-Type: application/json

{
  "events": [
    {"id": "1", "title": "Standup", "start_time": "2025-01-15T09:00:00", "end_time": "2025-01-15T09:15:00"},
    {"id": "2", "title": "Team Sync", "start_time": "2025-01-15T10:00:00", "end_time": "2025-01-15T11:00:00"},
    {"id": "3", "title": "Client Call", "start_time": "2025-01-15T11:30:00", "end_time": "2025-01-15T12:00:00"},
    {"id": "4", "title": "1:1", "start_time": "2025-01-15T14:00:00", "end_time": "2025-01-15T14:30:00"}
  ],
  "date": "2025-01-15",
  "work_hours": [9, 17]
}
```

**Response:**
```json
{
  "date": "2025-01-15",
  "total_meeting_hours": 2.25,
  "focus_time_hours": 5.75,
  "fragmentation_score": 0.33,
  "productivity_score": 78.5,
  "recommendations": [
    "Consider consolidating meetings to reduce context switching"
  ],
  "suggested_reschedules": [],
  "time_blocks": [
    {"type": "focus", "start": "...", "end": "...", "duration_minutes": 45, "label": "Focus Time"},
    {"type": "meeting", "start": "...", "end": "...", "duration_minutes": 15, "label": "Standup"}
  ]
}
```

### Meeting Types Detected

| Type | Keywords | Preparation Focus |
|------|----------|------------------|
| `one_on_one` | 1:1, check-in, catch up | Previous notes, discussion topics |
| `team` | team, department, weekly | Status updates, blockers |
| `client` | client, customer, partner | Account status, materials |
| `interview` | interview, candidate | Resume, questions |
| `review` | review, feedback, retro | Data, examples |
| `planning` | planning, sprint, roadmap | Proposals, options |
| `standup` | standup, daily, scrum | Yesterday/today/blockers |

---

## Workflow Automation

Build automated workflows with triggers, conditions, and actions.

### Features

| Feature | Description |
|---------|-------------|
| **Webhook Triggers** | Receive external webhooks |
| **Schedule Triggers** | Cron-based scheduling |
| **Email Triggers** | Trigger on email keywords |
| **HTTP Actions** | Make API requests |
| **Email Actions** | Send emails |
| **AI Processing** | Run AI tasks |
| **Data Transform** | Filter, map, aggregate data |
| **Conditional Logic** | Branch based on conditions |

### API: Create Workflow

```http
POST /api/admin/workflow/create
Content-Type: application/json

{
  "name": "New Lead Notification",
  "description": "Notify sales team when new lead arrives",
  "trigger_config": {
    "type": "webhook",
    "name": "Lead Webhook",
    "config": {"path": "/webhook/new-lead"}
  },
  "steps": [
    {
      "type": "transform",
      "name": "Extract Lead Data",
      "config": {
        "type": "extract",
        "fields": ["name", "email", "company"]
      }
    },
    {
      "type": "http_request",
      "name": "Notify Slack",
      "config": {
        "url": "https://hooks.slack.com/...",
        "method": "POST",
        "body": {"text": "New lead: {{name}} from {{company}}"}
      }
    }
  ],
  "tags": ["sales", "leads"]
}
```

### API: Execute Workflow

```http
POST /api/admin/workflow/{workflow_id}/execute
Content-Type: application/json

{
  "trigger_data": {
    "name": "John Doe",
    "email": "john@prospect.com",
    "company": "Acme Inc"
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_123",
  "workflow_id": "wf_456",
  "status": "completed",
  "started_at": "2025-01-15T10:30:00Z",
  "step_outputs": {
    "step_1": {"name": "John Doe", "email": "john@prospect.com"},
    "step_2": {"status_code": 200}
  }
}
```

### Workflow Templates

#### Zapier-style Webhook

```http
POST /api/admin/workflow/templates/zapier-webhook
Content-Type: application/json

{
  "name": "Form to CRM",
  "webhook_path": "/webhook/form-submit",
  "target_url": "https://api.crm.com/leads",
  "transform": {
    "type": "map",
    "mapping": {"firstName": "name", "emailAddress": "email"}
  }
}
```

#### Email Automation

```http
POST /api/admin/workflow/templates/email-automation
Content-Type: application/json

{
  "name": "Support Auto-Reply",
  "trigger_keywords": ["support", "help", "issue"],
  "response_template": "Thanks for contacting support. We'll respond within 24 hours.",
  "ai_process": true
}
```

#### Scheduled Report

```http
POST /api/admin/workflow/templates/scheduled-report
Content-Type: application/json

{
  "name": "Daily Metrics",
  "schedule": "0 9 * * *",
  "data_source_url": "https://api.analytics.com/metrics",
  "recipients": ["team@company.com"]
}
```

### Trigger Types

| Type | Description | Config |
|------|-------------|--------|
| `webhook` | HTTP webhook receiver | `path` |
| `schedule` | Cron-based schedule | `cron` expression |
| `email` | Email keyword trigger | `keywords` array |
| `calendar` | Calendar event trigger | `event_type` |
| `manual` | Manual execution | - |

### Action Types

| Type | Description | Config |
|------|-------------|--------|
| `http_request` | HTTP API call | `url`, `method`, `body` |
| `email_send` | Send email | `to`, `subject`, `body` |
| `ai_process` | AI processing | `task`, `input` |
| `transform` | Data transformation | `type`, `config` |
| `conditional` | Branch logic | `condition` |
| `delay` | Wait period | `seconds` |

---

## Email Plugins

### Outlook Add-in

The Outlook add-in provides JARVIS features directly in Microsoft Outlook.

#### Installation

1. Copy `tools/outlook-addin/manifest.xml`
2. Update URLs in manifest to your JARVIS server
3. Sideload in Outlook or deploy via Microsoft 365 Admin Center

#### Features

- **Summarize** - Get AI summary of current email
- **Quick Reply** - One-click reply suggestions
- **Classify** - See priority/category classification
- **AI Draft** - Generate response with tone selection

#### Building

```bash
cd tools/outlook-addin
npm install
npm run build
```

### Gmail Add-on

The Gmail add-on integrates JARVIS into Gmail's sidebar.

#### Installation

1. Open Google Apps Script: script.google.com
2. Create new project
3. Copy `tools/gmail-addon/Code.gs` and `appsscript.json`
4. Deploy as Gmail Add-on

#### Features

- **Summarize** - AI summary with key points
- **Quick Replies** - Context-aware reply options
- **Classify** - Auto-categorization
- **AI Draft** - Generate responses in compose
- **Settings** - Configure API URL and defaults

---

## Python SDK Usage

### Email Integration

```python
from agent.admin import EmailIntegration, EmailMessage, ResponseTone

email = EmailIntegration()

# Summarize email
message = EmailMessage(
    id="123",
    subject="Project Update",
    sender="Alice",
    sender_email="alice@company.com",
    recipients=["team@company.com"],
    body="Please review the attached updates..."
)

summary = email.summarize_email(message)
print(f"Priority: {summary.priority.value}")
print(f"Action Items: {summary.action_items}")

# Draft response
draft = email.draft_response(
    email=message,
    intent="Acknowledge and confirm review",
    tone=ResponseTone.PROFESSIONAL
)
print(draft.body)
```

### Calendar Intelligence

```python
from agent.admin import CalendarIntelligence, CalendarEvent, Attendee
from datetime import datetime

calendar = CalendarIntelligence()

# Generate meeting brief
event = CalendarEvent(
    id="mtg_123",
    title="Q4 Planning",
    start_time=datetime(2025, 1, 15, 14, 0),
    end_time=datetime(2025, 1, 15, 15, 0),
    attendees=[Attendee(email="team@company.com", name="Team")],
    description="Quarterly planning session"
)

brief = calendar.generate_meeting_brief(event)
print(f"Meeting Type: {brief.meeting_type.value}")
print(f"Prep Items: {brief.preparation_items}")

# Extract action items from notes
notes = """
Meeting notes:
- John will finalize budget by Friday
- TODO: Update roadmap
- Sarah to schedule follow-up
"""

items = calendar.extract_action_items(
    notes, "mtg_123", "Q4 Planning", ["John", "Sarah"]
)
for item in items:
    print(f"- {item.description} ({item.assignee})")
```

### Workflow Automation

```python
from agent.admin import WorkflowEngine
import asyncio

engine = WorkflowEngine()

# Create a webhook workflow
workflow = engine.create_zapier_webhook_workflow(
    name="Form Handler",
    webhook_path="/webhook/contact-form",
    target_url="https://api.crm.com/contacts",
    transform_config={
        "type": "map",
        "mapping": {"firstName": "first_name"}
    }
)

# Execute workflow
async def run():
    result = await engine.execute_workflow(
        workflow.id,
        {"firstName": "John", "email": "john@example.com"}
    )
    print(f"Status: {result.status.value}")

asyncio.run(run())
```

---

## Use Cases

### 1. Email Triage Dashboard

```javascript
async function triageInbox(emails) {
  // Classify all emails
  const classified = await Promise.all(
    emails.map(email =>
      fetch('/api/admin/email/classify', {
        method: 'POST',
        body: JSON.stringify(email)
      }).then(r => r.json())
    )
  );

  // Group by priority
  return {
    urgent: classified.filter(c => c.priority === 'urgent'),
    action_required: classified.filter(c => c.category === 'action_required'),
    fyi: classified.filter(c => c.category === 'fyi')
  };
}
```

### 2. Meeting Preparation Automation

```python
# Daily meeting prep job
def prepare_for_meetings(calendar_events):
    for event in calendar_events:
        brief = calendar.generate_meeting_brief(event)

        # Send prep email
        send_reminder_email(
            subject=f"Prep for: {event.title}",
            body=format_brief(brief),
            meeting_time=event.start_time
        )
```

### 3. Lead Processing Workflow

```python
# Create lead processing workflow
engine.create_workflow(
    name="Lead Processor",
    description="Enrich and route new leads",
    trigger_config={
        "type": "webhook",
        "config": {"path": "/webhook/new-lead"}
    },
    steps=[
        {
            "type": "ai_process",
            "name": "Qualify Lead",
            "config": {"task": "lead_scoring", "input": "{{lead}}"}
        },
        {
            "type": "conditional",
            "name": "Route Lead",
            "config": {
                "condition": {"field": "score", "operator": "greater_than", "value": "70"}
            }
        },
        {
            "type": "http_request",
            "name": "Add to CRM",
            "config": {
                "url": "https://api.crm.com/leads",
                "method": "POST"
            }
        }
    ]
)
```

---

## Configuration

### Environment Variables

```bash
# Email integration
JARVIS_EMAIL_DEFAULT_TONE=professional

# Calendar
JARVIS_CALENDAR_WORK_HOURS_START=9
JARVIS_CALENDAR_WORK_HOURS_END=17

# Workflow
JARVIS_WORKFLOW_MAX_RETRIES=3
JARVIS_WORKFLOW_TIMEOUT_SECONDS=30
```

---

## Changelog

### v1.0.0 (2025-11-23)
- Initial release
- Email Integration: summarization, drafting, classification
- Calendar Intelligence: briefs, action items, optimization
- Workflow Automation: triggers, actions, templates
- Outlook Add-in and Gmail Add-on
