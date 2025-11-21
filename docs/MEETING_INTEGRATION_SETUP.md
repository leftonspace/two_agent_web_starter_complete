# Meeting Platform Integration Setup

**PHASE 7A.1**: This guide explains how to set up JARVIS to join Zoom, Microsoft Teams, and other video meeting platforms to capture audio and participate in real-time conversations.

---

## Table of Contents

1. [Overview](#overview)
2. [Why Meeting Integration?](#why-meeting-integration)
3. [Architecture](#architecture)
4. [Supported Platforms](#supported-platforms)
5. [Setup Instructions](#setup-instructions)
   - [Zoom Setup](#zoom-setup)
   - [Microsoft Teams Setup](#microsoft-teams-setup)
   - [Live Audio Setup](#live-audio-setup)
6. [Configuration](#configuration)
7. [Usage Examples](#usage-examples)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Privacy & Compliance](#privacy--compliance)

---

## Overview

Meeting integration allows JARVIS to:

- **Join video meetings** as a participant (Zoom, Teams, etc.)
- **Capture audio streams** in real-time (16kHz PCM mono)
- **List participants** currently in the meeting
- **Send chat messages** to the meeting
- **Extract action items** from conversations

This solves a critical gap: **80%+ of business action items come from meetings**, but traditional bots are blind to them.

---

## Why Meeting Integration?

### The Problem

Most business decisions, action items, and important discussions happen in real-time meetings:

- Weekly standups
- Sprint planning
- Customer calls
- All-hands meetings
- 1-on-1s

Without meeting integration, JARVIS can only react to **written** communication (emails, Slack, tasks), missing the majority of business context.

### The Solution

With meeting bots, JARVIS can:

1. **Listen** to meeting audio in real-time
2. **Transcribe** conversations using speech-to-text
3. **Extract** action items, decisions, and key points
4. **Execute** on action items automatically (with approval)
5. **Follow up** with participants via email/Slack

**Example workflow:**

```
Meeting occurs:
  "Alice: Bob, can you deploy the new feature to staging by EOD?"
  "Bob: Sure, I'll handle that."

JARVIS hears this → Transcribes → Extracts action item:
  - Assignee: Bob
  - Task: Deploy new feature to staging
  - Deadline: End of day

JARVIS creates ticket → Notifies Bob → Offers to deploy automatically
```

---

## Architecture

### Abstract Base Class

All meeting bots inherit from `MeetingBot` (in `agent/meetings/base.py`):

```python
class MeetingBot(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to platform API/SDK"""

    @abstractmethod
    async def join_meeting(self) -> bool:
        """Join specific meeting as participant"""

    @abstractmethod
    async def start_audio_capture(self) -> bool:
        """Start capturing audio stream"""

    @abstractmethod
    async def get_audio_stream(self) -> AsyncIterator[AudioChunk]:
        """Stream audio chunks (1 second at 16kHz)"""

    @abstractmethod
    async def get_participants(self) -> List[Dict[str, Any]]:
        """Get current participants"""

    @abstractmethod
    async def send_chat_message(self, message: str) -> bool:
        """Send message to meeting chat"""

    @abstractmethod
    async def leave_meeting(self) -> bool:
        """Leave meeting and cleanup"""

    @abstractmethod
    async def get_recording_url(self) -> Optional[str]:
        """Get recording URL if available"""
```

This abstraction allows JARVIS to work with **any platform** using the same interface.

### Factory Pattern

Use `create_meeting_bot()` to instantiate the correct bot:

```python
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

meeting_info = MeetingInfo(
    platform=MeetingPlatform.ZOOM,
    meeting_id="123456789",
    title="Weekly Standup",
    participants=["Alice", "Bob"],
    start_time=datetime.now(),
    scheduled_duration_minutes=30,
    meeting_url="https://zoom.us/j/123456789"
)

bot = create_meeting_bot(meeting_info)
```

---

## Supported Platforms

| Platform | Status | Implementation | Authentication |
|----------|--------|----------------|----------------|
| **Zoom** | ✅ Ready (simulation) | `ZoomBot` | API Key + SDK Key |
| **Microsoft Teams** | ✅ Ready (simulation) | `TeamsBot` | Azure AD (OAuth2) |
| **Google Meet** | 🚧 Planned | `GoogleMeetBot` (stub) | Google Cloud (OAuth2) |
| **Live Audio** | ✅ Ready | `LiveAudioBot` | PyAudio (local mic) |

**Note:** Zoom and Teams implementations are currently in **simulation mode** because they require:
- Marketplace approval from vendors
- Live meeting SDK installation
- Corporate credentials

The code demonstrates the **interface** and **workflow** but uses simulated audio data until real SDKs are integrated.

---

## Setup Instructions

### Zoom Setup

#### Prerequisites

1. **Zoom Account** (Pro or higher recommended)
2. **Zoom Marketplace Developer Account**: https://marketplace.zoom.us/
3. **Meeting SDK Credentials** (requires approval)

#### Step 1: Create a Zoom App

1. Go to https://marketplace.zoom.us/
2. Click **Develop** → **Build App**
3. Choose **Meeting SDK** app type
4. Fill in app details:
   - App name: "JARVIS Meeting Bot"
   - Description: "AI assistant that joins meetings"
   - Company name: Your company

#### Step 2: Get Credentials

After creating the app:

1. **API Key/Secret** (for REST API):
   - Found in **App Credentials** tab
   - Used for meeting management API calls

2. **SDK Key/Secret** (for Meeting SDK):
   - Found in **App Credentials** → **Meeting SDK**
   - Used to join meetings programmatically

#### Step 3: Enable Permissions

In the **Scopes** tab, enable:

- `meeting:read:admin` - Read meeting details
- `meeting:write:admin` - Join meetings
- `user:read:admin` - Get participant info

#### Step 4: Install Zoom Meeting SDK (Production Only)

For production use, install the Zoom Meeting SDK:

```bash
# Linux
wget https://zoom.us/client/latest/zoom_sdk_linux_x86_64.tar.gz
tar -xzf zoom_sdk_linux_x86_64.tar.gz

# macOS
# Download from: https://marketplace.zoom.us/docs/sdk/native-sdks/macos/

# SDK documentation:
# https://developers.zoom.us/docs/meeting-sdk/
```

#### Step 5: Set Environment Variables

Add to `.env`:

```bash
# Zoom API Credentials
ZOOM_API_KEY=your_api_key_here
ZOOM_API_SECRET=your_api_secret_here

# Zoom SDK Credentials
ZOOM_SDK_KEY=your_sdk_key_here
ZOOM_SDK_SECRET=your_sdk_secret_here
```

#### Step 6: Test Connection

```python
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

meeting_info = MeetingInfo(
    platform=MeetingPlatform.ZOOM,
    meeting_id="123456789",
    title="Test Meeting",
    participants=[],
    start_time=datetime.now(),
    scheduled_duration_minutes=30,
    meeting_url="https://zoom.us/j/123456789",
    password="meeting_password"
)

bot = create_meeting_bot(meeting_info)
connected = await bot.connect()
print(f"Connected: {connected}")
```

---

### Microsoft Teams Setup

#### Prerequisites

1. **Microsoft 365 Account** (Business/Enterprise)
2. **Azure Active Directory** access
3. **Teams Admin Center** access

#### Step 1: Register Azure AD Application

1. Go to https://portal.azure.com/
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**:
   - Name: "JARVIS Teams Bot"
   - Supported account types: Single tenant
   - Redirect URI: `https://yourdomain.com/auth/callback`

#### Step 2: Configure API Permissions

In **API permissions**, add:

**Microsoft Graph Permissions:**
- `Calls.AccessMedia.All` - Access media in calls (Application)
- `Calls.Initiate.All` - Initiate calls (Application)
- `Calls.JoinGroupCall.All` - Join group calls (Application)
- `OnlineMeetings.Read.All` - Read meeting details (Application)
- `User.Read.All` - Read user profiles (Application)

Click **Grant admin consent** after adding permissions.

#### Step 3: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Description: "JARVIS Meeting Bot Secret"
4. Expiration: 24 months (recommended)
5. **Copy the secret value immediately** (it won't be shown again)

#### Step 4: Get Tenant Information

From the **Overview** tab, copy:
- **Application (client) ID**
- **Directory (tenant) ID**

#### Step 5: Configure Bot Framework

1. Go to https://dev.botframework.com/
2. Create a new bot:
   - Display name: "JARVIS"
   - Bot handle: "jarvis-meeting-bot"
   - Messaging endpoint: `https://yourdomain.com/api/messages`

3. Link to Azure AD app created in Step 1

#### Step 6: Set Environment Variables

Add to `.env`:

```bash
# Azure AD Credentials
AZURE_TENANT_ID=your_tenant_id_here
AZURE_CLIENT_ID=your_client_id_here
AZURE_CLIENT_SECRET=your_client_secret_here
```

#### Step 7: Install Required Libraries (Production Only)

```bash
pip install azure-identity msgraph-core
```

#### Step 8: Test Connection

```python
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

meeting_info = MeetingInfo(
    platform=MeetingPlatform.TEAMS,
    meeting_id="19:meeting_abc123",
    title="Test Meeting",
    participants=[],
    start_time=datetime.now(),
    scheduled_duration_minutes=30,
    meeting_url="https://teams.microsoft.com/l/meetup-join/..."
)

bot = create_meeting_bot(meeting_info)
connected = await bot.connect()
print(f"Connected: {connected}")
```

---

### Live Audio Setup

For **in-person meetings** or when screen-sharing, use `LiveAudioBot` to capture audio from your computer's microphone.

#### Step 1: Install PyAudio

```bash
# macOS
brew install portaudio
pip install pyaudio

# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio

# Windows
pip install pyaudio
```

#### Step 2: Test Microphone

```bash
python -c "import pyaudio; p = pyaudio.PyAudio(); print(f'Found {p.get_device_count()} audio devices')"
```

#### Step 3: Use LiveAudioBot

```python
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

meeting_info = MeetingInfo(
    platform=MeetingPlatform.LIVE_AUDIO,
    meeting_id="live_001",
    title="In-Person Meeting",
    participants=["Alice"],
    start_time=datetime.now(),
    scheduled_duration_minutes=60
)

bot = create_meeting_bot(meeting_info)

if await bot.connect():
    print("Microphone ready!")
    await bot.join_meeting()
    await bot.start_audio_capture()

    # Stream audio for 10 seconds
    count = 0
    async for chunk in bot.get_audio_stream():
        print(f"Got audio chunk: {len(chunk)} bytes")
        count += 1
        if count >= 10:
            break

    await bot.leave_meeting()
```

---

## Configuration

### Meeting Config Options

Edit `agent/config.py` or set environment variables:

```python
from agent.config import get_config

config = get_config()

# Meeting settings
config.meetings.enabled = True  # Enable meeting integration
config.meetings.auto_join_scheduled = False  # Auto-join calendar meetings
config.meetings.send_join_notification = True  # Announce when joining

# Audio settings
config.meetings.audio_sample_rate = 16000  # 16kHz (standard for speech)
config.meetings.audio_channels = 1  # Mono
config.meetings.audio_chunk_duration_ms = 1000  # 1-second chunks

# Behavior
config.meetings.leave_after_minutes = 0  # 0 = stay until meeting ends
config.meetings.max_meeting_duration_hours = 4
config.meetings.record_audio = True  # Capture for transcription

# Privacy
config.meetings.announce_recording = True  # Legal requirement in many jurisdictions
config.meetings.obfuscate_participant_info = False  # Hide emails in logs
```

---

## Usage Examples

### Example 1: Join a Zoom Meeting

```python
import asyncio
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

async def join_zoom_meeting():
    meeting_info = MeetingInfo(
        platform=MeetingPlatform.ZOOM,
        meeting_id="123456789",
        title="Weekly Standup",
        participants=["Alice", "Bob", "Charlie"],
        start_time=datetime.now(),
        scheduled_duration_minutes=30,
        meeting_url="https://zoom.us/j/123456789",
        password="secret123"
    )

    bot = create_meeting_bot(meeting_info)

    # Connect and join
    if await bot.connect():
        print("✓ Connected to Zoom")

        if await bot.join_meeting():
            print("✓ Joined meeting")

            # Get participants
            participants = await bot.get_participants()
            print(f"Participants: {[p['name'] for p in participants]}")

            # Send greeting
            await bot.send_chat_message("JARVIS has joined the meeting")

            # Capture audio for 60 seconds
            await bot.start_audio_capture()
            chunk_count = 0

            async for chunk in bot.get_audio_stream():
                print(f"Audio chunk {chunk_count}: {chunk.duration_seconds}s")
                # TODO: Send to speech-to-text API
                chunk_count += 1

                if chunk_count >= 60:  # 60 seconds
                    break

            # Leave cleanly
            await bot.leave_meeting()
            print("✓ Left meeting")

asyncio.run(join_zoom_meeting())
```

### Example 2: Capture Live Audio from Microphone

```python
import asyncio
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

async def record_in_person_meeting():
    meeting_info = MeetingInfo(
        platform=MeetingPlatform.LIVE_AUDIO,
        meeting_id="live_meeting_001",
        title="Product Review",
        participants=["Team"],
        start_time=datetime.now(),
        scheduled_duration_minutes=30
    )

    bot = create_meeting_bot(meeting_info)

    if await bot.connect():
        print("✓ Microphone connected")

        await bot.join_meeting()
        await bot.start_audio_capture()

        print("Recording... (Press Ctrl+C to stop)")

        try:
            async for chunk in bot.get_audio_stream():
                # Process audio chunk
                print(f"Captured {chunk.duration_seconds}s of audio")
                # TODO: Transcribe with Whisper API

        except KeyboardInterrupt:
            print("\nStopping recording...")

        await bot.leave_meeting()
        print("✓ Recording stopped")

asyncio.run(record_in_person_meeting())
```

### Example 3: Extract Action Items from Meeting

```python
import asyncio
from agent.meetings import create_meeting_bot, MeetingInfo, MeetingPlatform
from datetime import datetime

# Hypothetical transcription service
async def transcribe_audio(audio_bytes: bytes) -> str:
    # Use OpenAI Whisper, Google Speech-to-Text, etc.
    return "Alice: Bob, can you deploy the feature by Friday?"

async def extract_action_items_from_meeting():
    meeting_info = MeetingInfo(
        platform=MeetingPlatform.ZOOM,
        meeting_id="987654321",
        title="Sprint Planning",
        participants=["Alice", "Bob", "Charlie"],
        start_time=datetime.now(),
        scheduled_duration_minutes=60,
        meeting_url="https://zoom.us/j/987654321"
    )

    bot = create_meeting_bot(meeting_info)
    await bot.connect()
    await bot.join_meeting()
    await bot.start_audio_capture()

    transcript_segments = []

    # Collect 5 minutes of audio
    count = 0
    async for chunk in bot.get_audio_stream():
        # Transcribe each chunk
        text = await transcribe_audio(chunk.audio_bytes)
        transcript_segments.append(text)

        count += 1
        if count >= 300:  # 5 minutes
            break

    await bot.leave_meeting()

    # Analyze transcript for action items
    full_transcript = " ".join(transcript_segments)

    # Use LLM to extract action items
    # (This would call your conversational agent)
    action_items = [
        {"assignee": "Bob", "task": "Deploy feature", "deadline": "Friday"}
    ]

    print("Action Items:")
    for item in action_items:
        print(f"  - [{item['assignee']}] {item['task']} (Due: {item['deadline']})")

asyncio.run(extract_action_items_from_meeting())
```

---

## Testing

### Run Tests

```bash
# Run all meeting bot tests
pytest agent/tests/test_meeting_bots.py -v

# Run specific test
pytest agent/tests/test_meeting_bots.py::test_zoom_bot_connect -v

# Run with coverage
pytest agent/tests/test_meeting_bots.py --cov=agent.meetings --cov-report=html
```

### Test Coverage

The test suite includes:

- ✅ Data model tests (MeetingInfo, AudioChunk)
- ✅ Factory pattern tests
- ✅ ZoomBot tests (connection, join, audio, participants, chat)
- ✅ TeamsBot tests
- ✅ LiveAudioBot tests
- ✅ GoogleMeetBot stub tests
- ✅ Integration tests (full meeting lifecycle)

---

## Troubleshooting

### Zoom Issues

#### "pyJWT not installed"

```bash
pip install pyjwt
```

#### "aiohttp not installed"

```bash
pip install aiohttp
```

#### "Invalid SDK credentials"

- Verify `ZOOM_SDK_KEY` and `ZOOM_SDK_SECRET` are correct
- Check that your Zoom app is **activated** in the Marketplace
- Ensure Meeting SDK is enabled for your app

#### "Cannot join meeting - Authentication failed"

- Check that your Zoom app has the required **scopes**
- Verify the meeting ID and password are correct
- Make sure your API key has not expired

### Teams Issues

#### "AADSTS50105: User not assigned to a role"

- Go to Azure AD → Enterprise applications
- Find your app → Users and groups
- Assign your user account to the app

#### "Insufficient privileges to complete the operation"

- Ensure you've granted **admin consent** for all permissions
- Check that permissions are **Application** type (not Delegated)

#### "Graph API rate limit exceeded"

- Teams API has rate limits: 1,200 requests/minute
- Implement exponential backoff in production

### Live Audio Issues

#### "PyAudio not installed"

```bash
# macOS
brew install portaudio
pip install pyaudio

# Linux
sudo apt-get install portaudio19-dev
pip install pyaudio
```

#### "No audio devices found"

- Check that a microphone is connected
- On Linux, verify ALSA is configured:
  ```bash
  arecord -l  # List recording devices
  ```

#### "Audio stream error: [Errno -9981] Input overflowed"

- Reduce `frames_per_buffer` in `live_audio_bot.py` (line 89)
- Or add `exception_on_overflow=False` when reading audio

---

## Privacy & Compliance

### Legal Requirements

**Recording Consent:**

In many jurisdictions, you **must** obtain consent before recording meetings:

- **United States**: Varies by state
  - 1-party consent states: Only one person needs to know (12 states)
  - 2-party consent states: All participants must consent (11 states + DC)
  - Remaining states: Unclear or mixed

- **European Union (GDPR)**: Requires explicit consent from all participants
- **California (CCPA)**: Requires disclosure and opt-out option
- **Canada**: 1-party consent federally, but provinces vary

**Best practice:** Always announce when the bot joins and is recording.

### Configuration

```python
# Enable recording announcement
config.meetings.announce_recording = True  # Sends chat: "JARVIS is recording this meeting"

# Obfuscate personal info in logs
config.meetings.obfuscate_participant_info = True  # Hides emails, only stores names
```

### Data Retention

Meeting audio should be:

- **Encrypted at rest** (use encrypted storage for audio files)
- **Deleted after transcription** (unless required for compliance)
- **Access-controlled** (only authorized users can access recordings)

Example retention policy:

```python
# After transcription
async def cleanup_audio(meeting_id: str):
    audio_path = f"data/meetings/{meeting_id}/audio.pcm"
    transcript_path = f"data/meetings/{meeting_id}/transcript.txt"

    # Ensure transcript exists
    if os.path.exists(transcript_path):
        # Delete raw audio
        os.remove(audio_path)
        print(f"Deleted audio for {meeting_id} (transcript preserved)")
```

### GDPR Compliance

For GDPR compliance:

1. **Data minimization**: Only capture necessary data
2. **Purpose limitation**: Only use audio for stated purposes
3. **Storage limitation**: Delete audio after transcription
4. **Right to erasure**: Allow users to request deletion
5. **Data portability**: Allow users to export their data

---

## Next Steps

1. **Transcription Integration**
   - Integrate with OpenAI Whisper, Google Speech-to-Text, or Azure Speech
   - Real-time transcription with speaker diarization

2. **Action Item Extraction**
   - Use LLM to extract action items from transcripts
   - Automatically create tasks in project management tools

3. **Meeting Summaries**
   - Generate meeting summaries with key decisions
   - Send summaries to participants via email

4. **Calendar Integration**
   - Auto-join scheduled meetings from Google Calendar / Outlook
   - Send meeting reminders with JARVIS availability

5. **Multi-Meeting Support**
   - Join multiple meetings concurrently
   - Handle meeting queue and scheduling

---

## Resources

- **Zoom SDK Documentation**: https://developers.zoom.us/docs/meeting-sdk/
- **Microsoft Graph Calls API**: https://learn.microsoft.com/en-us/graph/api/resources/call
- **PyAudio Documentation**: https://people.csail.mit.edu/hubert/pyaudio/docs/
- **OpenAI Whisper API**: https://platform.openai.com/docs/guides/speech-to-text

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review test cases in `agent/tests/test_meeting_bots.py`
3. Check logs in `data/logs/` for detailed error messages
4. Open an issue in the repository

---

**End of Meeting Integration Setup Guide**
