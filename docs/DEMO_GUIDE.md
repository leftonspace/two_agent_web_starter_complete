# JARVIS 2.0 Complete Demo Guide

**Version:** 2.0.0
**Date:** November 23, 2025

Complete guide to demonstrating JARVIS 2.0 - the AI Agent Orchestration Platform with voice, vision, council system, and multi-agent coordination.

---

## Table of Contents

1. [Prerequisites Check](#prerequisites-check)
2. [Quick Start](#quick-start)
3. [Part 1: Core System Demo](#part-1-core-system-demo)
4. [Part 2: JARVIS Voice System](#part-2-jarvis-voice-system)
5. [Part 3: JARVIS Vision System](#part-3-jarvis-vision-system)
6. [Part 4: AI Agents Dashboard](#part-4-ai-agents-dashboard)
7. [Part 5: Council System](#part-5-council-system)
8. [Part 6: Flow Engine Demo](#part-6-flow-engine-demo)
9. [Part 7: Approval Workflows](#part-7-approval-workflows)
10. [Part 8: Integration Framework](#part-8-integration-framework)
11. [Troubleshooting](#troubleshooting)
12. [Summary](#summary)

---

## Prerequisites Check

### Step 1: Verify Python Dependencies

```bash
cd /home/user/two_agent_web_starter_complete
python3 -c "import aiohttp, cryptography, fastapi, pydantic; print('✓ Core dependencies OK')"
```

**Expected output:** `✓ Core dependencies OK`

### Step 2: Verify Configuration Files

```bash
# Check YAML configs exist
ls -la config/*.yaml
```

**Expected:** `agents.yaml`, `tasks.yaml`, `llm_config.yaml`, `flows.yaml`, `memory.yaml`, `council.yaml`, `patterns.yaml`

### Step 3: Check Environment Variables

```bash
# Verify .env file exists with required keys
cat .env | grep -E "ANTHROPIC_API_KEY|OPENAI_API_KEY" | head -2
```

**If missing, see [INSTALLATION.md](./INSTALLATION.md) for complete setup.**

---

## Quick Start

```bash
# 1. Start the server
cd /home/user/two_agent_web_starter_complete/agent/webapp
python app.py

# 2. Open browser
# Main Dashboard: http://127.0.0.1:8000
# JARVIS Chat: http://127.0.0.1:8000/jarvis
```

---

## Part 1: Core System Demo

### Step 1: Start the Web Application

```bash
cd /home/user/two_agent_web_starter_complete/agent/webapp
python app.py
```

**Expected output:**
```
============================================================
  JARVIS 2.0 - AI Agent Orchestration Platform
============================================================
  Starting web server on http://127.0.0.1:8000
  Voice System: Enabled
  Vision System: Enabled
  Council System: Enabled
  Press Ctrl+C to stop
============================================================
```

### Step 2: Verify Server Health

```bash
curl http://127.0.0.1:8000/health
```

**Expected:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "features": {
    "voice": true,
    "vision": true,
    "council": true,
    "memory": true,
    "flows": true
  }
}
```

### Step 3: Access JARVIS Chat Interface

**Browser:** Open `http://127.0.0.1:8000/jarvis`

**You should see:**
- Chat interface with JARVIS
- Microphone button (voice input)
- Camera button (vision input)
- Image upload button
- Agents dashboard toggle
- British butler persona responses

### Step 4: Test Basic Chat

Type in the chat:
```
Hello JARVIS, what can you do?
```

**Expected response (British butler tone):**
```
Good day, sir/madam. I am JARVIS, your personal AI assistant. I am at your
service for a variety of tasks including:

- Software development and code review
- Project planning and task orchestration
- Image analysis and visual understanding
- Voice-based interaction
- Multi-agent coordination for complex tasks

How may I assist you today?
```

---

## Part 2: JARVIS Voice System

### Step 5: Enable Voice Input

**In the JARVIS chat interface:**

1. Click the **microphone button** (🎤)
2. Grant microphone permission when prompted
3. Speak: "Hello JARVIS, what's the weather like?"
4. Click to stop recording

**Expected:**
- Speech transcribed to text
- JARVIS responds in text
- If voice output enabled, JARVIS speaks the response

### Step 6: Test Voice API (Programmatic)

```bash
# Text-to-Speech
curl -X POST http://127.0.0.1:8000/api/voice/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Good afternoon, sir. How may I assist you?"}'
```

**Expected response:**
```json
{
  "success": true,
  "audio_url": "/api/voice/audio/abc123.mp3",
  "duration_seconds": 2.5
}
```

### Step 7: Configure Voice Settings

```bash
# Check voice configuration
curl http://127.0.0.1:8000/api/voice/config
```

**Expected:**
```json
{
  "tts_provider": "elevenlabs",
  "stt_provider": "whisper",
  "voice_id": "jarvis_voice",
  "language": "en-GB"
}
```

---

## Part 3: JARVIS Vision System

### Step 8: Upload an Image for Analysis

**In the JARVIS chat interface:**

1. Click the **image button** (🖼️)
2. Select an image file (PNG, JPG, etc.)
3. Type: "What do you see in this image?"
4. Send message

**Expected:**
- Image preview shown in chat
- JARVIS analyzes and describes the image content

### Step 9: Use Camera Capture

1. Click the **camera button** (📷)
2. Grant camera permission when prompted
3. Position subject in frame
4. Click "Capture" button
5. Ask: "What can you see?"

**Expected:**
- Camera preview opens
- Photo captured and sent to JARVIS
- Analysis returned

### Step 10: Test Vision API (Programmatic)

```bash
# Analyze image from URL
curl -X POST http://127.0.0.1:8000/api/vision/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/sample.jpg",
    "prompt": "Describe what you see in detail"
  }'
```

**Expected:**
```json
{
  "success": true,
  "analysis": "The image shows a modern office space with...",
  "objects_detected": ["desk", "computer", "chair", "window"],
  "confidence": 0.92
}
```

### Step 11: OCR (Text Extraction)

```bash
curl -X POST http://127.0.0.1:8000/api/vision/ocr \
  -F "image=@/path/to/document.png"
```

**Expected:**
```json
{
  "success": true,
  "text": "Extracted text from the document...",
  "language": "en",
  "confidence": 0.95
}
```

---

## Part 4: AI Agents Dashboard

### Step 12: Open Agents Dashboard

**In JARVIS chat interface:**

1. Click the **Agents** button in the top right
2. Slide-out panel opens showing all agents

**You should see agents:**
- **JARVIS** (Master Orchestrator) - Active
- **Manager Agent** - Idle
- **Supervisor Agent** - Idle
- **Code Employee** - Idle
- **Test Employee** - Idle
- **Docs Employee** - Idle
- **Security Specialist** - Idle
- **Performance Specialist** - Idle

### Step 13: View Real-Time Agent Activity

```bash
# WebSocket connection for real-time updates
curl -N http://127.0.0.1:8000/api/agents/stream
```

**Or via JavaScript:**
```javascript
const ws = new WebSocket('ws://127.0.0.1:8000/api/agents/stream');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Agent update:', data);
};
```

### Step 14: Check Agent Status API

```bash
curl http://127.0.0.1:8000/api/agents/status
```

**Expected:**
```json
{
  "agents": [
    {
      "id": "jarvis",
      "name": "JARVIS",
      "role": "Master Orchestrator",
      "status": "active",
      "current_task": null,
      "tasks_completed": 42,
      "uptime_seconds": 3600
    },
    {
      "id": "manager",
      "name": "Manager Agent",
      "role": "Task Planning",
      "status": "idle",
      "tasks_completed": 15
    }
  ],
  "total_active": 1,
  "total_idle": 7
}
```

### Step 15: Trigger Multi-Agent Task

In JARVIS chat:
```
Create a Python web scraper with tests and documentation
```

**Watch the Agents Dashboard - you'll see:**
1. JARVIS activates (orchestrating)
2. Manager Agent activates (planning)
3. Code Employee activates (writing code)
4. Test Employee activates (writing tests)
5. Docs Employee activates (documentation)

---

## Part 5: Council System

### Step 16: View Council Status

```bash
curl http://127.0.0.1:8000/api/council/status
```

**Expected:**
```json
{
  "enabled": true,
  "councillors": [
    {
      "id": "ada",
      "name": "Ada",
      "specialization": "coding",
      "performance_score": 0.92,
      "happiness": 85,
      "vote_weight": 1.84
    },
    {
      "id": "bob",
      "name": "Bob",
      "specialization": "review",
      "performance_score": 0.78,
      "happiness": 72,
      "vote_weight": 1.12
    }
  ],
  "total_councillors": 5,
  "average_happiness": 78
}
```

### Step 17: Trigger Council Vote

```bash
curl -X POST http://127.0.0.1:8000/api/council/vote \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How should we approach implementing user authentication?",
    "options": ["simple_jwt", "oauth2_full", "session_based", "need_clarification"]
  }'
```

**Expected:**
```json
{
  "success": true,
  "session_id": "vote_123",
  "question": "How should we approach implementing user authentication?",
  "votes": [
    {"councillor": "ada", "vote": "oauth2_full", "confidence": 0.85, "weight": 1.84},
    {"councillor": "bob", "vote": "simple_jwt", "confidence": 0.7, "weight": 1.12}
  ],
  "winner": "oauth2_full",
  "weighted_score": 3.24
}
```

### Step 18: View Council History

```bash
curl http://127.0.0.1:8000/api/council/history?limit=5
```

---

## Part 6: Flow Engine Demo

### Step 19: List Available Flows

```bash
curl http://127.0.0.1:8000/api/flows
```

**Expected:**
```json
{
  "flows": [
    {
      "id": "feature_development",
      "name": "Feature Development Flow",
      "steps": 8,
      "description": "Complete flow for developing a new feature"
    },
    {
      "id": "quick_fix",
      "name": "Quick Fix Flow",
      "steps": 4,
      "description": "Streamlined flow for small fixes"
    }
  ]
}
```

### Step 20: Execute a Flow

```bash
curl -X POST http://127.0.0.1:8000/api/flows/feature_development/execute \
  -H "Content-Type: application/json" \
  -d '{
    "initial_state": {
      "feature_name": "user_notifications",
      "requirements": ["email alerts", "push notifications", "in-app messages"],
      "priority": "high"
    }
  }'
```

**Expected:**
```json
{
  "success": true,
  "execution_id": "flow_exec_456",
  "status": "running",
  "current_step": "analyze_requirements",
  "progress": 0.125
}
```

### Step 21: Monitor Flow Progress

```bash
curl http://127.0.0.1:8000/api/flows/executions/flow_exec_456
```

---

## Part 7: Approval Workflows

### Step 22: Create HR Approval Request

```bash
curl -X POST http://127.0.0.1:8000/api/approvals \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "hr_offer_letter_v1",
    "payload": {
      "candidate_name": "Jane Developer",
      "position": "Senior Software Engineer",
      "salary": 145000,
      "department": "Engineering"
    }
  }'
```

### Step 23: View Pending Approvals

**Browser:** `http://127.0.0.1:8000/approvals`

**Or API:**
```bash
curl http://127.0.0.1:8000/api/approvals?status=pending
```

### Step 24: Approve/Reject Request

```bash
# Approve
curl -X POST http://127.0.0.1:8000/api/approvals/{request_id}/approve \
  -F "approver_user_id=manager_001" \
  -F "comments=Approved - great candidate"

# Reject
curl -X POST http://127.0.0.1:8000/api/approvals/{request_id}/reject \
  -F "approver_user_id=manager_001" \
  -F "comments=Budget constraints"
```

---

## Part 8: Integration Framework

### Step 25: Add Database Integration

```bash
curl -X POST http://127.0.0.1:8000/api/integrations \
  -H "Content-Type: application/json" \
  -d '{
    "type": "sqlite",
    "engine": "sqlite",
    "database": "/home/user/two_agent_web_starter_complete/data/test_hr.db"
  }'
```

### Step 26: Test Integration

```bash
curl http://127.0.0.1:8000/api/integrations/{connector_id}/test
```

### Step 27: Query via Integration

```bash
curl -X POST http://127.0.0.1:8000/api/integrations/{connector_id}/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM employees WHERE status = '\''active'\''"}'
```

---

## Troubleshooting

### Voice System Issues

```bash
# Check voice API health
curl http://127.0.0.1:8000/api/voice/health

# Verify ElevenLabs API key
echo $ELEVENLABS_API_KEY
```

### Vision System Issues

```bash
# Check vision API health
curl http://127.0.0.1:8000/api/vision/health

# Test with local image
curl -X POST http://127.0.0.1:8000/api/vision/analyze \
  -F "image=@test_image.png" \
  -F "prompt=Describe this image"
```

### Council System Issues

```bash
# Check council configuration
cat config/council.yaml

# Verify councillors loaded
curl http://127.0.0.1:8000/api/council/councillors
```

### Agent Dashboard Issues

```bash
# Check agents API
curl http://127.0.0.1:8000/api/agents/status

# Verify WebSocket endpoint
websocat ws://127.0.0.1:8000/api/agents/stream
```

### Port Already in Use

```bash
lsof -ti:8000 | xargs kill -9
cd /home/user/two_agent_web_starter_complete/agent/webapp && python app.py
```

---

## Summary

### Features Demonstrated

| Feature | Endpoint | Status |
|---------|----------|--------|
| JARVIS Chat | `/jarvis` | ✅ |
| Voice Input/Output | `/api/voice/*` | ✅ |
| Vision/Image Analysis | `/api/vision/*` | ✅ |
| AI Agents Dashboard | `/api/agents/*` | ✅ |
| Council Voting | `/api/council/*` | ✅ |
| Flow Engine | `/api/flows/*` | ✅ |
| Approval Workflows | `/api/approvals/*` | ✅ |
| Integrations | `/api/integrations/*` | ✅ |
| Memory System | `/api/memory/*` | ✅ |

### Key URLs

| Page | URL |
|------|-----|
| Main Dashboard | http://127.0.0.1:8000/ |
| JARVIS Chat | http://127.0.0.1:8000/jarvis |
| Approvals | http://127.0.0.1:8000/approvals |
| Integrations | http://127.0.0.1:8000/integrations |
| Jobs | http://127.0.0.1:8000/jobs |
| Health Check | http://127.0.0.1:8000/health |

### JARVIS 2.0 Capabilities

- **Voice**: Talk to JARVIS using natural speech (ElevenLabs TTS, Whisper STT)
- **Vision**: Upload images or use camera for JARVIS to analyze
- **Council**: Weighted voting system for complex decisions
- **Patterns**: 5 orchestration patterns (Sequential, Hierarchical, AutoSelect, RoundRobin, Manual)
- **Memory**: Short-term, long-term, and entity memory systems
- **Flows**: Visual workflow execution with conditional routing
- **Multi-Agent**: Real-time coordination of specialized AI agents

---

## Next Steps

1. **Customize Agents**: Edit `config/agents.yaml`
2. **Create Workflows**: Define flows in `config/flows.yaml`
3. **Tune Council**: Adjust voting weights in `config/council.yaml`
4. **Add Integrations**: Connect databases, APIs, HR systems
5. **Configure Voice**: Set up custom voice in ElevenLabs

---

**Congratulations! You've completed the JARVIS 2.0 Demo.**

For detailed documentation, see:
- [INSTALLATION.md](./INSTALLATION.md) - Setup guide
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Development reference
- [JARVIS_2_0_CONFIGURATION_GUIDE.md](./JARVIS_2_0_CONFIGURATION_GUIDE.md) - Configuration options
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions
