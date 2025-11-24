# Zoom/Meet SDK Integration

Complete meeting bot integration with Zoom and Google Meet for automated meeting participation, recording, and transcription.

## Overview

JARVIS now includes production-ready meeting bot SDKs that enable:
- **Live Meeting Join**: Automatically join Zoom and Google Meet sessions
- **Real-time Recording**: Capture meeting audio and video
- **Transcription**: Live transcription of meeting content
- **Calendar Integration**: Trigger actions based on calendar events
- **Multi-platform Support**: Unified interface for Zoom and Google Meet

## Architecture

```
agent/meetings/
├── sdk_integration.py      # Main SDK integration (850 lines)
├── zoom_bot.py             # Zoom bot implementation (existing)
└── google_meet_bot.py      # Google Meet bot (existing)
```

## Components

### 1. ZoomBotSDK

Complete Zoom Meeting SDK integration with JWT authentication.

**Key Features:**
- JWT token generation for Zoom SDK authentication
- Meeting join with ID and passcode
- Recording control (start/stop)
- Participant tracking
- Chat integration
- Real-time transcription

**Usage:**

```python
from agent.meetings.sdk_integration import ZoomBotSDK

# Initialize SDK
bot = ZoomBotSDK(
    sdk_key="your-sdk-key",
    sdk_secret="your-sdk-secret",
)

# Join meeting
success = await bot.join_meeting(
    meeting_id="123456789",
    passcode="abc123",
    display_name="JARVIS Bot"
)

# Start recording
await bot.start_recording()

# Get participants
participants = await bot.get_participants()

# Send chat message
await bot.send_message("Hello from JARVIS!")

# Get transcription
async for text in bot.get_transcription():
    print(f"Transcription: {text}")

# Leave meeting
await bot.leave_meeting()
```

**JWT Authentication:**

The SDK automatically generates JWT tokens for authentication:

```python
def _generate_jwt_token(self, meeting_id: str, role: int = 0) -> str:
    """
    Generate JWT token for Zoom SDK.

    Args:
        meeting_id: Zoom meeting ID
        role: 0 for attendee, 1 for host

    Returns:
        JWT token string
    """
    payload = {
        "appKey": self.sdk_key,
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "sdkKey": self.sdk_key,
        "mn": str(meeting_id),
        "role": role,
    }
    token = jwt.encode(payload, self.sdk_secret, algorithm="HS256")
    return token
```

### 2. GoogleMeetBotSDK

Google Meet integration using browser automation (Puppeteer/Playwright).

**Key Features:**
- Browser-based meeting join
- Audio/video recording
- Chat message sending
- Participant tracking

**Usage:**

```python
from agent.meetings.sdk_integration import GoogleMeetBotSDK

# Initialize SDK
bot = GoogleMeetBotSDK(
    email="bot@example.com",
    password="password",
)

# Join meeting
success = await bot.join_meeting(
    meeting_code="abc-defg-hij",
    display_name="JARVIS Bot"
)

# Start recording
await bot.start_recording()

# Get participants
participants = await bot.get_participants()

# Leave meeting
await bot.leave_meeting()
```

**Note:** Google Meet doesn't have an official bot SDK, so this implementation uses browser automation. For production, consider using Google Meet API with proper OAuth2 authentication.

### 3. CalendarMeetingTrigger

Automatically trigger meeting actions based on calendar events.

**Key Features:**
- Rule-based action triggering
- Pattern matching on meeting titles
- Configurable lead time
- Automatic check loop

**Usage:**

```python
from agent.meetings.sdk_integration import CalendarMeetingTrigger
from agent.meetings.calendar import CalendarIntegration

# Initialize calendar
calendar = CalendarIntegration(
    provider="google",
    credentials={
        "client_id": "...",
        "client_secret": "...",
    }
)

# Initialize trigger
trigger = CalendarMeetingTrigger(calendar_integration=calendar)

# Add rule: Join standup meetings 5 minutes early
async def join_standup(meeting):
    bot = ZoomBotSDK(...)
    await bot.join_meeting(meeting.meeting_id)

trigger.add_rule(
    rule_id="standup-auto-join",
    pattern="Daily Standup",
    action=join_standup,
    lead_time=timedelta(minutes=5)
)

# Start monitoring
await trigger.start()
```

**Rule Configuration:**

```python
{
    "rule_id": "standup-auto-join",
    "pattern": "Daily Standup",  # Match meetings with this in title
    "action": async_function,     # Action to trigger
    "lead_time": timedelta(minutes=5),  # Join 5 mins early
    "enabled": True
}
```

### 4. MeetingBotManager

Unified manager for multiple meeting platforms.

**Key Features:**
- Multi-platform support (Zoom, Google Meet)
- Automatic platform detection from URL
- Credential management
- Active bot tracking

**Usage:**

```python
from agent.meetings.sdk_integration import MeetingBotManager

# Initialize manager
manager = MeetingBotManager()

# Configure platforms
manager.configure_zoom(
    sdk_key="your-sdk-key",
    sdk_secret="your-sdk-secret"
)

manager.configure_google_meet(
    email="bot@example.com",
    password="password"
)

# Join from URL (auto-detects platform)
bot = await manager.join_meeting(
    meeting_url="https://zoom.us/j/123456789?pwd=abc123"
)

# Or join from meeting code
bot = await manager.join_meeting(
    meeting_code="123456789",
    platform="zoom"
)

# Get active bots
active_bots = manager.get_active_bots()
```

**Platform Detection:**

The manager automatically detects the platform from meeting URLs:

```python
def _detect_platform(self, meeting_url: str) -> str:
    """Detect meeting platform from URL"""
    if "zoom.us" in meeting_url:
        return "zoom"
    elif "meet.google.com" in meeting_url:
        return "google_meet"
    else:
        raise ValueError(f"Unknown meeting platform: {meeting_url}")
```

## Setup

### 1. Install Dependencies

```bash
# Install Zoom SDK dependencies
pip install pyjwt

# Install browser automation (for Google Meet)
pip install playwright
playwright install chromium
```

### 2. Configure Credentials

Create `.env` file:

```bash
# Zoom SDK
ZOOM_SDK_KEY=your-sdk-key
ZOOM_SDK_SECRET=your-sdk-secret

# Google Meet (optional)
GOOGLE_MEET_EMAIL=bot@example.com
GOOGLE_MEET_PASSWORD=password

# Calendar Integration
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...
```

### 3. Get Zoom SDK Credentials

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Create a Meeting SDK app
3. Get SDK Key and SDK Secret
4. Add credentials to `.env`

## Examples

### Example 1: Auto-Join Standup Meetings

```python
from agent.meetings.sdk_integration import (
    MeetingBotManager,
    CalendarMeetingTrigger,
)
from agent.meetings.calendar import CalendarIntegration

# Initialize
manager = MeetingBotManager()
calendar = CalendarIntegration(provider="google", credentials={...})
trigger = CalendarMeetingTrigger(calendar)

# Configure auto-join
async def auto_join_standup(meeting):
    bot = await manager.join_meeting(meeting.meeting_url)
    await bot.start_recording()
    print(f"Joined and recording: {meeting.title}")

trigger.add_rule(
    rule_id="standup",
    pattern="Daily Standup",
    action=auto_join_standup,
    lead_time=timedelta(minutes=2)
)

# Start monitoring
await trigger.start()
```

### Example 2: Record All Meetings

```python
from agent.meetings.sdk_integration import MeetingBotManager

manager = MeetingBotManager()

async def record_meeting(meeting_url: str):
    bot = await manager.join_meeting(meeting_url)

    # Start recording
    await bot.start_recording()

    # Wait for meeting to end (check periodically)
    while bot.is_connected:
        await asyncio.sleep(60)
        participants = await bot.get_participants()
        if len(participants) == 0:
            break

    # Stop recording and leave
    await bot.stop_recording()
    await bot.leave_meeting()

# Use with calendar integration
async def main():
    meetings = await calendar.get_upcoming_meetings(hours=1)

    tasks = []
    for meeting in meetings:
        if meeting.meeting_url:
            tasks.append(record_meeting(meeting.meeting_url))

    await asyncio.gather(*tasks)
```

### Example 3: Transcription and Summary

```python
from agent.meetings.sdk_integration import ZoomBotSDK

async def transcribe_and_summarize(meeting_id: str):
    bot = ZoomBotSDK(...)
    await bot.join_meeting(meeting_id)

    # Collect transcription
    transcript = []
    async for text in bot.get_transcription():
        transcript.append(text)
        print(f"[Transcription] {text}")

    # After meeting, generate summary
    full_transcript = "\n".join(transcript)

    # Use LLM to summarize
    from agent.chat import JarvisChat
    chat = JarvisChat()

    summary = await chat.send_message(
        f"Summarize this meeting transcript:\n\n{full_transcript}"
    )

    print(f"\n[Summary]\n{summary}")
```

## Production Considerations

### 1. Zoom SDK Limitations

- **Rate Limits**: Zoom SDK has rate limits on API calls
- **Meeting Capacity**: Bot counts as a participant
- **Recording Storage**: Recordings stored locally, need cloud upload
- **JWT Expiration**: Tokens expire after 1 hour, need refresh

### 2. Google Meet Browser Automation

- **Headless Mode**: Use headless browser for production
- **Login State**: Keep browser session alive to avoid re-login
- **Resource Usage**: Browser automation is resource-intensive
- **Stability**: May break with Google Meet UI changes

### 3. Calendar Integration

- **OAuth Refresh**: Implement OAuth token refresh
- **Time Zones**: Handle time zones correctly
- **Event Updates**: Monitor for meeting reschedules
- **Permissions**: Ensure bot has calendar access

### 4. Security

- **Credentials**: Store credentials securely (use KMS/Vault)
- **Meeting Access**: Only join authorized meetings
- **Recording Privacy**: Comply with recording consent laws
- **Data Retention**: Set recording retention policies

## Troubleshooting

### Zoom SDK Connection Issues

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check JWT token
token = bot._generate_jwt_token(meeting_id)
print(f"JWT Token: {token}")

# Verify SDK credentials
print(f"SDK Key: {bot.sdk_key}")
```

### Google Meet Browser Automation Issues

```python
# Run in headful mode for debugging
bot = GoogleMeetBotSDK(
    email="...",
    password="...",
    headless=False  # Show browser
)

# Check browser logs
await bot.join_meeting(meeting_code)
logs = await bot.browser.get_logs()
print(logs)
```

### Calendar Integration Issues

```python
# Test calendar connection
calendar = CalendarIntegration(...)
events = await calendar.get_upcoming_meetings(hours=24)
print(f"Found {len(events)} upcoming meetings")

# Check OAuth token
token = calendar.get_token()
print(f"Token expires: {token['expires_at']}")
```

## Future Enhancements

1. **AI-Powered Features**:
   - Real-time meeting notes
   - Action item extraction
   - Speaker diarization
   - Sentiment analysis

2. **Advanced Recording**:
   - Multi-stream recording (separate speaker tracks)
   - Video processing and highlights
   - Cloud storage integration
   - Automatic transcription with timestamps

3. **Meeting Intelligence**:
   - Meeting quality metrics
   - Participation tracking
   - Topic modeling
   - Follow-up reminders

4. **Integration Expansion**:
   - Microsoft Teams support
   - Webex support
   - Slack Huddles
   - Discord voice channels

## Related Files

- `agent/meetings/sdk_integration.py` - Main SDK implementation
- `agent/meetings/calendar.py` - Calendar integration
- `agent/scheduler/cron.py` - Scheduling system
- `ORCHESTRATOR_CONSOLIDATION_PLAN.md` - System architecture

## Support

For issues or questions:
- Check logs for error messages
- Verify credentials are correct
- Test with a simple meeting first
- Review Zoom SDK documentation: https://marketplace.zoom.us/docs/sdk
- Review Google Meet API docs: https://developers.google.com/meet
