# Meeting Bot SDK Activation Guide

This guide will help you activate the Zoom and Google Meet bot SDKs for full production functionality.

## Current Status

✅ **SDK Infrastructure**: Complete and ready for activation
✅ **Fallback Mode**: System works in stub mode without credentials
⚠️ **Production Mode**: Requires SDK credentials and dependencies

## Quick Start

### Option 1: Zoom Bot (Recommended)

Zoom has an official SDK and is the easiest to set up.

#### 1. Get Zoom SDK Credentials

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Click "Develop" → "Build App"
3. Choose "Meeting SDK" app type
4. Fill in app details (name, company, description)
5. Get your credentials:
   - **SDK Key**: Found in "App Credentials" section
   - **SDK Secret**: Found in "App Credentials" section

#### 2. Install Zoom SDK

```bash
pip install zoomus
```

#### 3. Set Environment Variables

Add to your `.env` file:

```bash
ZOOM_SDK_KEY=your_sdk_key_here
ZOOM_SDK_SECRET=your_sdk_secret_here
```

#### 4. Test Zoom Bot

```python
from agent.meetings.sdk_integration import ZoomBotSDK
import asyncio
import os

async def test_zoom():
    bot = ZoomBotSDK(
        sdk_key=os.getenv("ZOOM_SDK_KEY"),
        sdk_secret=os.getenv("ZOOM_SDK_SECRET")
    )

    # Join meeting (replace with real meeting ID)
    success = await bot.join_meeting("123-456-789", passcode="abc123")

    if success:
        print("✅ Joined meeting!")

        # Start recording
        recording = await bot.start_recording(local=True)
        print(f"🔴 Recording: {recording.recording_id}")

        # Get participants
        participants = await bot.get_participants()
        print(f"👥 Participants: {len(participants)}")

        # Send message
        await bot.send_message("JARVIS bot has joined the meeting!")

        # Leave meeting
        await bot.leave_meeting()
    else:
        print("❌ Failed to join")

asyncio.run(test_zoom())
```

### Option 2: Google Meet Bot (Advanced)

Google Meet doesn't have an official bot SDK, so we use browser automation with Playwright.

#### 1. Install Playwright

```bash
# Install Playwright
pip install playwright

# Install browsers
playwright install chromium
```

#### 2. Set Up Google OAuth2 Credentials (Optional)

For authenticated meetings:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Download `credentials.json`
6. Save to your project root

#### 3. Test Google Meet Bot

```python
from agent.meetings.sdk_integration import GoogleMeetBotSDK
import asyncio

async def test_meet():
    bot = GoogleMeetBotSDK(credentials_path="credentials.json")

    # Join meeting (replace with real meeting code)
    success = await bot.join_meeting("abc-defg-hij")

    if success:
        print("✅ Joined Google Meet!")

        # Wait in meeting
        await asyncio.sleep(60)

        # Leave meeting
        await bot.leave_meeting()
    else:
        print("❌ Failed to join")

asyncio.run(test_meet())
```

## Using Meeting Bot Manager

The `MeetingBotManager` provides a unified interface for both platforms:

```python
from agent.meetings.sdk_integration import MeetingBotManager
import asyncio
import os

async def main():
    manager = MeetingBotManager()

    # Configure Zoom
    manager.configure_zoom(
        sdk_key=os.getenv("ZOOM_SDK_KEY"),
        sdk_secret=os.getenv("ZOOM_SDK_SECRET")
    )

    # Configure Google Meet
    manager.configure_google_meet(
        credentials_path="credentials.json"
    )

    # Join meeting from URL (automatically detects platform)
    bot = await manager.join_meeting(
        "https://zoom.us/j/123456789",
        auto_record=True
    )

    # Or join Google Meet
    # bot = await manager.join_meeting(
    #     "https://meet.google.com/abc-defg-hij",
    #     auto_record=True
    # )

asyncio.run(main())
```

## Calendar Integration

Auto-join meetings from your calendar:

```python
from agent.meetings.sdk_integration import (
    CalendarMeetingTrigger,
    MeetingBotManager,
    CalendarMeeting
)
import asyncio

async def setup_calendar_auto_join():
    manager = MeetingBotManager()
    trigger = manager.calendar_trigger

    # Add rule: Join all "Daily Standup" meetings
    trigger.add_rule(
        rule_id="standup",
        pattern="Daily Standup",
        action=lambda meeting: manager.join_meeting(
            meeting.meeting_url,
            auto_record=True
        ),
        lead_time_minutes=2  # Join 2 minutes before start
    )

    # Add rule: Join all meetings with "JARVIS" in title
    trigger.add_rule(
        rule_id="jarvis_meetings",
        pattern="JARVIS",
        action=lambda meeting: manager.join_meeting(
            meeting.meeting_url,
            auto_record=True
        ),
        lead_time_minutes=1
    )

    # Start monitoring calendar
    await trigger.start(check_interval_seconds=60)

asyncio.run(setup_calendar_auto_join())
```

## Action Item Reminders

The new action item reminder system is now integrated!

```python
from agent.meetings.intelligence.action_item_reminders import (
    ActionItemReminderSystem,
    ReminderConfig,
    ActionItem
)
from datetime import datetime, timedelta
import asyncio

async def setup_reminders():
    # Configure reminders
    config = ReminderConfig(
        enable_due_soon=True,
        enable_due_today=True,
        enable_overdue=True,
        enable_weekly_summary=True,
        email_enabled=True,
        slack_enabled=True,
        daily_check_time="09:00",  # Check overdue at 9 AM
        weekly_summary_day="MON",  # Monday summary
        weekly_summary_time="08:00"  # 8 AM
    )

    # Create reminder system
    system = ActionItemReminderSystem(config=config)

    # Add action items from meeting
    item = ActionItem(
        id="meeting_123_action_1",
        description="Review Q4 budget proposal",
        assignee="john@company.com",
        due_date=datetime.now() + timedelta(days=2),
        priority="high",
        meeting_title="Budget Planning Meeting",
        status="pending"
    )

    system.add_action_item(item)

    # Start reminder system
    await system.start()

asyncio.run(setup_reminders())
```

## Full Integration Example

Combine everything for complete meeting intelligence:

```python
from agent.meetings.sdk_integration import MeetingBotManager
from agent.meetings.intelligence.action_item_reminders import (
    ActionItemReminderSystem,
    create_reminder_system
)
from agent.admin.calendar_intelligence import CalendarIntelligence
import asyncio
import os

async def full_meeting_intelligence():
    # 1. Set up meeting bot manager
    manager = MeetingBotManager()
    manager.configure_zoom(
        sdk_key=os.getenv("ZOOM_SDK_KEY"),
        sdk_secret=os.getenv("ZOOM_SDK_SECRET")
    )

    # 2. Set up calendar intelligence
    calendar_ai = CalendarIntelligence()

    # 3. Set up action item reminders
    reminder_system = create_reminder_system(enable_slack=True)

    # 4. Join meeting
    bot = await manager.join_meeting(
        "https://zoom.us/j/123456789",
        auto_record=True,
        auto_transcribe=True
    )

    # 5. Wait for meeting to end
    # (In production, this would be event-driven)
    await asyncio.sleep(3600)  # 1 hour

    # 6. Get meeting transcript/notes
    # meeting_notes = "..." (from transcription)

    # 7. Extract action items
    action_items = calendar_ai.extract_action_items(
        meeting_notes="...",
        meeting_id="123",
        meeting_title="Team Sync",
        attendees=["john@company.com", "sarah@company.com"]
    )

    # 8. Add to reminder system
    reminder_system.add_action_items(action_items)

    # 9. Start monitoring reminders
    await reminder_system.start()

asyncio.run(full_meeting_intelligence())
```

## Troubleshooting

### Zoom SDK Issues

**Error: "Invalid SDK Key"**
- Verify `ZOOM_SDK_KEY` and `ZOOM_SDK_SECRET` are set correctly
- Check that SDK credentials are from "Meeting SDK" app (not OAuth app)

**Error: "JWT token expired"**
- JWT tokens expire after 2 hours by default
- The system automatically regenerates tokens, but check system time is correct

**Error: "zoomus module not found"**
```bash
pip install zoomus
```

### Google Meet Issues

**Error: "playwright._impl._api_types.Error"**
```bash
# Reinstall Playwright browsers
playwright install chromium
```

**Error: "Timeout waiting for selector"**
- Google Meet UI may have changed
- Update selector in `sdk_integration.py` line 457
- Check meeting URL is correct format: `https://meet.google.com/abc-defg-hij`

**Error: "Authentication required"**
- For private meetings, set up Google OAuth2 credentials
- Add authentication logic to `join_meeting()` method

### Action Item Reminder Issues

**Error: "CronScheduler not available"**
- The system falls back to console printing
- All functionality works, just notifications are limited

**Error: "AlertingSystem not available"**
- Reminders will print to console instead
- Set up alerting system: `agent/alerting.py`

## Next Steps

1. **Get Zoom credentials** (5 minutes)
   - Sign up at [Zoom Marketplace](https://marketplace.zoom.us/)
   - Create Meeting SDK app
   - Copy SDK Key and Secret

2. **Install dependencies**
   ```bash
   pip install zoomus playwright
   playwright install chromium
   ```

3. **Test with a meeting**
   - Schedule a test Zoom meeting
   - Run the test script above
   - Verify bot joins, records, and leaves

4. **Set up calendar integration** (optional)
   - Configure calendar rules
   - Enable auto-join for specific meetings

5. **Configure action item reminders**
   - Set reminder times
   - Configure notification channels (email, Slack)
   - Test with sample action items

## Production Deployment

### Security Best Practices

1. **Never commit credentials**
   ```bash
   # Add to .gitignore
   .env
   credentials.json
   ```

2. **Use environment variables**
   - Store in `.env` file locally
   - Use secret management in production (AWS Secrets Manager, etc.)

3. **Rotate credentials regularly**
   - Zoom SDK keys should be rotated every 90 days
   - Google OAuth tokens expire automatically

### Performance Optimization

1. **Connection pooling**
   - Reuse bot instances for multiple meetings
   - Close connections properly to avoid leaks

2. **Resource limits**
   - Limit concurrent meetings (max 5-10 per instance)
   - Monitor CPU/memory usage

3. **Graceful shutdown**
   ```python
   import signal

   def signal_handler(sig, frame):
       await bot.leave_meeting()
       sys.exit(0)

   signal.signal(signal.SIGINT, signal_handler)
   ```

## Support

- **Zoom SDK Documentation**: https://marketplace.zoom.us/docs/sdk/meeting/
- **Playwright Documentation**: https://playwright.dev/python/
- **Google Meet API**: https://developers.google.com/meet

## What's Working Right Now (Even Without SDK Credentials)

The meeting bot system works in **stub mode** without credentials:
- ✅ Meeting management (session tracking, state management)
- ✅ Calendar integration (action item extraction, meeting briefs)
- ✅ Action item reminder system (schedules, notifications)
- ✅ Meeting intelligence (analysis, action items, decisions)
- ⚠️ Cannot join real meetings (needs SDK credentials)
- ⚠️ Cannot record audio/video (needs SDK credentials)

## What You Get With SDK Credentials

- ✅ Join real Zoom/Meet meetings programmatically
- ✅ Record meetings (audio + video)
- ✅ Real-time transcription
- ✅ Participant tracking and management
- ✅ Send chat messages during meetings
- ✅ Auto-join from calendar triggers

---

**Quick Summary**:
- **Zoom**: 5 minutes to set up, works great
- **Google Meet**: 15 minutes to set up, requires Playwright
- **Action Items**: Works immediately, no setup needed!
