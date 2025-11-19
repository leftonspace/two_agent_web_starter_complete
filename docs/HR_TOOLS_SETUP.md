# HR Tools Setup Guide

**PHASE 2.3: HR Tool Suite**

This guide explains how to set up and configure the HR tools (email, calendar, HRIS) for the department-in-a-box system.

## Overview

The HR tool suite provides three essential tools for HR workflows:

1. **send_email** - Send emails via SMTP with template support
2. **create_calendar_event** - Create Google Calendar events
3. **create_hris_record** - Create employee records in HRIS systems (BambooHR, Workday, etc.)

All tools support:
- Dry run mode for testing
- Comprehensive error handling
- Role-based access control (RBAC)
- Audit logging

---

## 1. Send Email Tool

### Features

- Plain text and HTML emails
- Jinja2 template rendering
- Multiple recipients (to, cc, bcc)
- Attachments (base64 encoded)
- Reply-to headers
- SMTP integration

### Configuration

Add SMTP configuration to your execution context:

```python
context = ToolExecutionContext(
    mission_id="mission_123",
    project_path=Path("/path/to/project"),
    config={
        "smtp": {
            "host": "smtp.gmail.com",  # SMTP server
            "port": 587,  # SMTP port (587 for TLS, 465 for SSL)
            "username": "your-email@gmail.com",
            "password": "your-app-password",  # Use app password, not account password
            "from_address": "noreply@yourcompany.com",  # Default sender
            "use_tls": True  # Enable TLS
        }
    }
)
```

### Gmail Setup

For Gmail users:

1. **Enable 2-Factor Authentication**
   - Go to Google Account → Security → 2-Step Verification
   - Turn on 2-Step Verification

2. **Generate App Password**
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Use this password in config (NOT your Google account password)

3. **Alternative: OAuth2**
   - For production, consider using OAuth2 instead of app passwords
   - See Google's [Gmail API documentation](https://developers.google.com/gmail/api)

### Usage Examples

#### Send Plain Text Email

```python
from agent.tools.hr.send_email import SendEmailTool

tool = SendEmailTool()
result = await tool.execute({
    "to": "candidate@example.com",
    "subject": "Welcome to Acme Corp!",
    "body": "We're excited to have you join our team."
}, context)

if result.success:
    print(f"Email sent: {result.data['message_id']}")
```

#### Send HTML Email

```python
result = await tool.execute({
    "to": ["user1@example.com", "user2@example.com"],
    "cc": ["manager@example.com"],
    "subject": "Team Meeting",
    "body_html": "<h1>Meeting at 2pm</h1><p>Conference Room A</p>"
}, context)
```

#### Send Templated Email

```python
result = await tool.execute({
    "to": "john.doe@example.com",
    "subject": "Welcome to Acme Corp!",
    "template_name": "welcome_email",
    "template_vars": {
        "candidate_name": "John Doe",
        "company_name": "Acme Corp",
        "job_title": "Software Engineer",
        "start_date": "2025-12-01",
        "manager_name": "Jane Smith",
        "department": "Engineering"
    }
}, context)
```

### Email Templates

Templates are stored in `agent/templates/email/` and use Jinja2 syntax.

**Create a new template:**

1. Create `agent/templates/email/your_template.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ subject }}</title>
</head>
<body>
    <h1>Hello {{ recipient_name }}!</h1>
    <p>{{ message }}</p>

    {% if include_footer %}
    <footer>
        <p>Best regards,<br>{{ company_name }}</p>
    </footer>
    {% endif %}
</body>
</html>
```

2. Use it:

```python
result = await tool.execute({
    "to": "user@example.com",
    "subject": "Custom Email",
    "template_name": "your_template",
    "template_vars": {
        "recipient_name": "Alice",
        "message": "This is a custom message.",
        "include_footer": True,
        "company_name": "Acme Corp"
    }
}, context)
```

### Dry Run Mode

Test without sending actual emails:

```python
context.dry_run = True
result = await tool.execute(params, context)
# Email is NOT sent, but you get full validation
```

---

## 2. Create Calendar Event Tool

### Features

- Google Calendar integration
- Single and recurring events
- Multiple attendees
- Timezone support
- Location and description
- Custom reminders

### Configuration

#### Step 1: Set Up Google Calendar API

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable Google Calendar API**
   - Go to APIs & Services → Library
   - Search for "Google Calendar API"
   - Click "Enable"

3. **Create OAuth2 Credentials**
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Download JSON file

4. **Authorize Application**
   ```bash
   # Run authorization flow (one-time)
   python scripts/authorize_google_calendar.py --credentials /path/to/client_secret.json
   ```

   This creates `token.json` with authorized credentials.

#### Step 2: Configure Tool

```python
context = ToolExecutionContext(
    mission_id="mission_123",
    project_path=Path("/path/to/project"),
    config={
        "google_calendar": {
            "credentials_path": "/path/to/token.json",  # Authorized credentials
            "calendar_id": "primary"  # Or specific calendar ID
        }
    }
)
```

### Usage Examples

#### Create Single Event

```python
from agent.tools.hr.create_calendar_event import CreateCalendarEventTool

tool = CreateCalendarEventTool()
result = await tool.execute({
    "summary": "Onboarding Meeting - John Doe",
    "start_time": "2025-12-01T09:00:00Z",
    "duration_minutes": 60,
    "attendees": [
        {"email": "john.doe@example.com"},
        {"email": "hr@example.com"}
    ],
    "location": "Conference Room A",
    "description": "Welcome meeting for new employee"
}, context)

if result.success:
    print(f"Event created: {result.data['event_link']}")
```

#### Create Recurring Event

```python
result = await tool.execute({
    "summary": "Weekly 1:1 with Manager",
    "start_time": "2025-12-01T14:00:00Z",
    "duration_minutes": 30,
    "attendees": [{"email": "manager@example.com"}],
    "recurrence": {
        "frequency": "weekly",  # daily, weekly, monthly, yearly
        "count": 12  # 12 occurrences
    }
}, context)
```

#### Recurring Until Date

```python
result = await tool.execute({
    "summary": "Daily Standup",
    "start_time": "2025-12-01T09:00:00Z",
    "duration_minutes": 15,
    "recurrence": {
        "frequency": "daily",
        "until": "2025-12-31",  # Repeat until this date
        "interval": 1  # Every day
    }
}, context)
```

### Timezone Handling

```python
result = await tool.execute({
    "summary": "Meeting",
    "start_time": "2025-12-01T14:00:00",  # No Z = use timezone param
    "end_time": "2025-12-01T15:00:00",
    "timezone": "America/Los_Angeles"  # Pacific Time
}, context)
```

---

## 3. Create HRIS Record Tool

### Features

- BambooHR API integration
- Workday API integration (stub)
- Generic HTTP API support
- Employee data validation
- Custom fields support

### Configuration

#### BambooHR Setup

1. **Get API Key**
   - Log in to BambooHR
   - Go to Settings → API Keys
   - Generate new API key

2. **Configure Tool**

```python
context = ToolExecutionContext(
    mission_id="mission_123",
    project_path=Path("/path/to/project"),
    config={
        "hris": {
            "bamboohr": {
                "api_key": "your-bamboohr-api-key",
                "subdomain": "your-company"  # From your-company.bamboohr.com
            }
        }
    }
)
```

#### Generic HRIS Setup

For custom HRIS systems:

```python
context = ToolExecutionContext(
    config={
        "hris": {
            "generic": {
                "base_url": "https://hris.yourcompany.com",
                "api_key": "your-api-key",
                "auth_header": "Authorization",  # Header name
                "endpoint": "/api/employees"  # POST endpoint
            }
        }
    }
)
```

### Usage Examples

#### Create Employee in BambooHR

```python
from agent.tools.hr.create_hris_record import CreateHRISRecordTool

tool = CreateHRISRecordTool()
result = await tool.execute({
    "system": "bamboohr",
    "employee_data": {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "job_title": "Software Engineer",
        "department": "Engineering",
        "start_date": "2025-12-01",
        "employment_type": "full_time",
        "manager_email": "jane.smith@example.com",
        "location": "San Francisco",
        "phone": "+1-555-0100"
    }
}, context)

if result.success:
    print(f"Employee ID: {result.data['employee_id']}")
    print(f"Profile: {result.data['profile_url']}")
```

#### With Custom Fields

```python
result = await tool.execute({
    "system": "bamboohr",
    "employee_data": {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "start_date": "2025-12-01",
        "custom_fields": {
            "shirtSize": "M",
            "dietaryRestrictions": "Vegetarian",
            "emergencyContactName": "John Smith",
            "emergencyContactPhone": "+1-555-0200"
        }
    }
}, context)
```

---

## Testing

### Run All Tests

```bash
pytest agent/tests/unit/test_hr_tools.py -v
```

### Test Individual Tools

```bash
# Test send_email only
pytest agent/tests/unit/test_hr_tools.py -k send_email -v

# Test calendar events only
pytest agent/tests/unit/test_hr_tools.py -k calendar -v

# Test HRIS only
pytest agent/tests/unit/test_hr_tools.py -k hris -v
```

### Dry Run Testing

All tools support dry run mode for testing without actual API calls:

```python
context.dry_run = True

# Test all tools without sending emails, creating events, or modifying HRIS
email_result = await email_tool.execute(params, context)
calendar_result = await calendar_tool.execute(params, context)
hris_result = await hris_tool.execute(params, context)

# All return success=True with dry_run=True in result.data
```

---

## Permissions

HR tools require specific permissions (from Phase 2.2):

- **send_email**: Requires `email_send` permission
- **create_calendar_event**: Requires `calendar_write` permission
- **create_hris_record**: Requires `hris_write` permission

### Allowed Roles

- **send_email**: manager, hr_manager, hr_recruiter, hr_business_partner
- **create_calendar_event**: manager, hr_manager, hr_recruiter, hr_business_partner
- **create_hris_record**: hr_manager, hr_business_partner (NOT recruiters)

---

## Troubleshooting

### Send Email Issues

**Problem**: "SMTP authentication failed"
- **Solution**: Use app password, not account password (for Gmail)
- **Check**: 2FA is enabled on Google account

**Problem**: "SMTP connection timeout"
- **Solution**: Check firewall allows outbound port 587/465
- **Check**: SMTP host and port are correct

**Problem**: "Template not found"
- **Solution**: Ensure template exists in `agent/templates/email/`
- **Check**: Template name doesn't include `.html` extension

### Calendar Event Issues

**Problem**: "Google Calendar credentials not configured"
- **Solution**: Run OAuth authorization flow to generate `token.json`
- **Check**: credentials_path points to valid file

**Problem**: "Invalid credentials"
- **Solution**: Re-run authorization flow (credentials may be expired)
- **Command**: `python scripts/authorize_google_calendar.py`

### HRIS Issues

**Problem**: "BambooHR API error (401 Unauthorized)"
- **Solution**: Check API key is correct
- **Check**: API key has proper permissions

**Problem**: "Employee creation failed: Missing required field"
- **Solution**: Ensure first_name, last_name, email, start_date are provided
- **Check**: BambooHR account has required custom fields set up

---

## Security Best Practices

1. **Never Commit Credentials**
   - Add credentials files to `.gitignore`
   - Use environment variables or secret management

2. **Use App Passwords**
   - For Gmail, use app passwords (not account password)
   - Rotate passwords regularly

3. **Limit API Key Permissions**
   - Create API keys with minimal required permissions
   - Use separate keys for dev/staging/production

4. **Enable Audit Logging**
   - All tool usage is logged to `data/tool_access_log.jsonl`
   - Review logs regularly for suspicious activity

5. **Use Dry Run for Testing**
   - Always test with `dry_run=True` first
   - Verify parameters before actual execution

---

## Examples

See complete examples in:
- `agent/tools/hr/send_email.py` (examples in manifest)
- `agent/tools/hr/create_calendar_event.py` (examples in manifest)
- `agent/tools/hr/create_hris_record.py` (examples in manifest)
- `agent/tests/unit/test_hr_tools.py` (25+ test cases)

---

## Support

For issues or questions:
- Check `docs/TOOL_PLUGIN_GUIDE.md` for plugin architecture
- See `agent/tools/base.py` for ToolPlugin interface
- Review test cases in `agent/tests/unit/test_hr_tools.py`

---

## Next Steps

After setting up HR tools:

1. Create email templates for your company
2. Set up Google Calendar authorization
3. Configure HRIS integration
4. Test tools in dry run mode
5. Deploy to production with proper credentials

**Ready to build more tools?** See `docs/TOOL_PLUGIN_GUIDE.md` for creating custom department tools.
