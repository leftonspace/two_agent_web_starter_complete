# JARVIS 2.0 - Windows PowerShell Setup Guide

**Version:** 2.1.0
**Platform:** Windows 10/11
**Prerequisites:** PowerShell 5.1+ (built into Windows)

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installing Python](#2-installing-python)
3. [Installing Git](#3-installing-git)
4. [Setting Up the Project](#4-setting-up-the-project)
5. [Installing Dependencies](#5-installing-dependencies)
6. [Configuring API Keys](#6-configuring-api-keys)
7. [YAML Configuration](#7-yaml-configuration)
8. [Optional: Voice System Setup](#8-optional-voice-system-setup)
9. [Optional: Installing Ollama](#9-optional-installing-ollama-local-llms)
10. [Running JARVIS](#10-running-jarvis)
11. [Using JARVIS 2.0](#11-using-jarvis-20)
12. [Claude Code-like Tools System](#12-claude-code-like-tools-system)
13. [Real-time Agent Streaming](#13-real-time-agent-streaming)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. System Requirements

### Minimum Requirements
- **OS:** Windows 10 (64-bit) or Windows 11
- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 20GB free space (more if using local LLMs)
- **Network:** Internet connection for API calls

### Software Prerequisites
- PowerShell 5.1+ (included in Windows 10/11)
- Administrator access for installations

---

## 2. Installing Python

### Step 1: Download Python

Open PowerShell as **Administrator** (Right-click Start → Windows PowerShell (Admin))

```powershell
# Check if Python is already installed
python --version
```

If Python is not installed or version is below 3.9:

1. Download Python 3.11 for Windows:
   - Visit: https://www.python.org/downloads/windows/
   - Download "Windows installer (64-bit)" for Python 3.11.x

2. **Or** use PowerShell to download:

```powershell
# Download Python installer
$pythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe"
$installerPath = "$env:TEMP\python-installer.exe"

# Download
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath

# Run installer
Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait

# Verify installation
python --version
```

### Step 2: Verify Python Installation

Close and reopen PowerShell, then:

```powershell
# Check Python version
python --version
# Should show: Python 3.11.x

# Check pip (package manager)
pip --version
# Should show: pip 23.x.x
```

---

## 3. Installing Git

### Step 1: Download Git for Windows

```powershell
# Check if Git is already installed
git --version
```

If Git is not installed:

1. Download Git for Windows:
   - Visit: https://git-scm.com/download/win
   - Download "64-bit Git for Windows Setup"

2. **Or** use PowerShell:

```powershell
# Download Git installer
$gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
$installerPath = "$env:TEMP\git-installer.exe"

Invoke-WebRequest -Uri $gitUrl -OutFile $installerPath
Start-Process -FilePath $installerPath -Wait

git --version
```

---

## 4. Setting Up the Project

### Step 1: Choose Installation Directory

Open PowerShell (regular, not Admin):

```powershell
# Navigate to your preferred location
cd $env:USERPROFILE\Documents

# Create dedicated folder
mkdir AI-Projects
cd AI-Projects
```

### Step 2: Clone the Repository

```powershell
# Clone the repository
git clone https://github.com/leftonspace/two_agent_web_starter_complete.git

# Navigate to project directory
cd two_agent_web_starter_complete

# Check current location
pwd
```

### Step 3: Verify Project Structure

```powershell
dir
# You should see:
# - agent/
# - docs/
# - config/
# - tests/
# - requirements.txt
# - README.md
```

---

## 5. Installing Dependencies

### Step 1: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**If you get an execution policy error:**
```powershell
# Enable script execution (one-time setup)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activating again
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` prefix in your prompt.

### Step 2: Upgrade pip

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### Step 3: Install Core Dependencies

```powershell
# Core Web Framework
pip install fastapi uvicorn[standard] jinja2 python-multipart websockets

# HTTP Client & Async
pip install aiohttp httpx

# LLM Providers
pip install anthropic openai

# Security & Encryption
pip install cryptography pyjwt

# Database Drivers
pip install aiosqlite asyncpg aiomysql

# Data Validation & Configuration
pip install pydantic python-dotenv pyyaml

# Memory System
pip install chromadb sentence-transformers

# Voice System (optional)
pip install elevenlabs sounddevice numpy

# Vision System
pip install pillow

# Claude Code-like Tools System (NEW in 2.1)
pip install aiohttp beautifulsoup4

# Utilities
pip install requests python-dateutil networkx
```

### Step 4: Verify Installations

```powershell
python -c "import fastapi, anthropic, openai; print('Core dependencies OK')"
python -c "import chromadb; print('ChromaDB OK')"
python -c "import aiohttp; from bs4 import BeautifulSoup; print('Tools System OK')"
```

---

## 6. Configuring API Keys

### Step 1: Get Your API Keys

1. **Anthropic (Claude):** https://console.anthropic.com/
2. **OpenAI:** https://platform.openai.com/api-keys
3. **ElevenLabs (voice, optional):** https://elevenlabs.io

### Step 2: Create Environment File

```powershell
$envContent = @"
# =============================================================================
# JARVIS 2.0 Environment Configuration
# =============================================================================

# LLM Provider API Keys (at least one required)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Optional LLM Providers
DEEPSEEK_API_KEY=
QWEN_API_KEY=

# Voice System (optional)
ELEVENLABS_API_KEY=
VOICE_ID=

# Database
DATABASE_URL=sqlite:///data/jarvis.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_EXPIRATION_HOURS=24

# Features (true/false)
ENABLE_COUNCIL=true
ENABLE_MEMORY=true
ENABLE_FLOWS=true
ENABLE_VOICE=true
ENABLE_VISION=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=logs/jarvis.log

# Performance
MAX_CONCURRENT_TASKS=10
CACHE_TTL_SECONDS=3600

# Application
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000
"@

$envContent | Out-File -FilePath .env -Encoding UTF8
Write-Host "Created .env file"
```

### Step 3: Edit .env File

```powershell
notepad .env
```

Replace the placeholder API keys with your actual keys.

---

## 7. YAML Configuration

JARVIS 2.0 uses YAML files for configuration. Create the config directory and files:

### Step 1: Create Config Directory

```powershell
mkdir config
```

### Step 2: Create agents.yaml

```powershell
$agentsYaml = @"
version: "2.0"
metadata:
  author: "admin"
  description: "JARVIS 2.0 agent configuration"

agents:
  - id: jarvis
    name: "JARVIS"
    role: "Master Orchestrator"
    goal: "Orchestrate AI agents and assist users"
    backstory: |
      JARVIS is the master AI assistant inspired by Iron Man.
      Speaks with a refined British butler persona.
    specialization: orchestration
    llm_config:
      provider: anthropic
      model: claude-3-sonnet
      temperature: 0.7

  - id: developer
    name: "Code Employee"
    role: "Software Developer"
    goal: "Write clean, efficient code"
    specialization: coding
    tools:
      - code_executor
      - file_manager
    llm_config:
      provider: anthropic
      model: claude-3-sonnet
      temperature: 0.3

  - id: tester
    name: "Test Employee"
    role: "QA Engineer"
    goal: "Ensure code quality through testing"
    specialization: testing
    llm_config:
      provider: anthropic
      model: claude-3-haiku
      temperature: 0.2
"@

$agentsYaml | Out-File -FilePath config\agents.yaml -Encoding UTF8
Write-Host "Created config/agents.yaml"
```

### Step 3: Create llm_config.yaml

```powershell
$llmConfig = @"
version: "2.0"

defaults:
  provider: anthropic
  model: claude-3-sonnet
  temperature: 0.7
  max_tokens: 4096
  timeout_seconds: 60

providers:
  anthropic:
    enabled: true
    api_key_env: ANTHROPIC_API_KEY
    models:
      claude-3-opus:
        max_tokens: 4096
        supports_vision: true
      claude-3-sonnet:
        max_tokens: 4096
        supports_vision: true
      claude-3-haiku:
        max_tokens: 4096
        supports_vision: true

  openai:
    enabled: true
    api_key_env: OPENAI_API_KEY
    models:
      gpt-4-turbo:
        max_tokens: 128000
        supports_vision: true
      gpt-4:
        max_tokens: 8192
      gpt-3.5-turbo:
        max_tokens: 16385

routing:
  cost_optimization: true
  failover_enabled: true
"@

$llmConfig | Out-File -FilePath config\llm_config.yaml -Encoding UTF8
Write-Host "Created config/llm_config.yaml"
```

---

## 8. Optional: Voice System Setup

### Install Voice Dependencies

```powershell
# Install voice packages
pip install elevenlabs sounddevice numpy

# Install FFmpeg (required for audio processing)
# Option 1: Using Chocolatey
choco install ffmpeg

# Option 2: Manual download from https://ffmpeg.org/download.html
```

### Configure ElevenLabs

1. Sign up at https://elevenlabs.io
2. Get API key from dashboard
3. Create or clone a British voice in Voice Lab
4. Copy voice ID
5. Update .env:

```powershell
notepad .env
# Add:
# ELEVENLABS_API_KEY=your-key
# VOICE_ID=your-voice-id
```

### Test Voice

```powershell
python -c "from elevenlabs import generate; print('ElevenLabs OK')"
```

---

## 9. Optional: Installing Ollama (Local LLMs)

### Step 1: Download Ollama

```powershell
$ollamaUrl = "https://ollama.ai/download/OllamaSetup.exe"
$installerPath = "$env:TEMP\OllamaSetup.exe"

Invoke-WebRequest -Uri $ollamaUrl -OutFile $installerPath
Start-Process -FilePath $installerPath -Wait
```

Or download from: https://ollama.ai/download

### Step 2: Download Models

```powershell
# Download Llama 3 (8B)
ollama pull llama3

# Download Mistral (7B)
ollama pull mistral

# Download smaller model
ollama pull phi3
```

### Step 3: Test Ollama

```powershell
ollama run llama3 "Hello, who are you?"
```

### Step 4: Update Configuration

Add to .env:
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_ENABLED=true
```

---

## 10. Running JARVIS

### Step 1: Create Data Directories

```powershell
mkdir data, logs, artifacts -ErrorAction SilentlyContinue
```

### Step 2: Initialize Database

```powershell
python -c @"
from pathlib import Path
import sqlite3

db_path = Path('data/jarvis.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('CREATE TABLE IF NOT EXISTS system_info (key TEXT PRIMARY KEY, value TEXT)')
conn.execute('INSERT OR REPLACE INTO system_info VALUES (?, ?)', ('version', '2.0.0'))
conn.commit()
conn.close()
print('Database initialized')
"@
```

### Step 3: Start JARVIS Web Interface

```powershell
# Make sure virtual environment is active
# (venv) should be in prompt

cd agent\webapp
python app.py
```

**Expected Output:**
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

### Step 4: Access Web Interface

Open browser: http://localhost:8000/jarvis

---

## 11. Using JARVIS 2.0

### JARVIS Chat Interface

Navigate to http://localhost:8000/jarvis

**Features available:**
- **Text Chat**: Type messages to interact with JARVIS
- **Voice Input**: Click microphone button to speak
- **Image Upload**: Click image button to upload photos
- **Camera**: Click camera button for live capture
- **Agents Dashboard**: Click "Agents" to see AI agent status

### Example Interactions

**Text Chat:**
```
You: Hello JARVIS, what can you do?
JARVIS: Good day, sir. I am at your service for software development,
        code review, project planning, image analysis, and multi-agent
        task coordination. How may I assist you?
```

**Code Request:**
```
You: Create a Python function to calculate factorial
JARVIS: Certainly, sir. Here is a recursive implementation...
```

**Image Analysis:**
1. Click the 🖼️ button
2. Select an image
3. Ask: "What do you see in this image?"

### API Testing

```powershell
# Test health endpoint
Invoke-RestMethod -Uri http://localhost:8000/health

# Test chat
$body = @{message="Hello JARVIS"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/chat -Method Post -Body $body -ContentType "application/json"
```

---

## 12. Claude Code-like Tools System

JARVIS 2.1 includes a powerful tools system inspired by Claude Code, enabling autonomous code analysis, file operations, and shell command execution.

### Available Tools

| Tool | Description | Example Usage |
|------|-------------|---------------|
| **Read** | Read files with line numbers | "Read the config.py file" |
| **Edit** | Find and replace in files | "Replace 'DEBUG=False' with 'DEBUG=True' in settings.py" |
| **Write** | Create or overwrite files | "Create a new utils.py file" |
| **Bash** | Execute shell commands | "Run git status", "npm install" |
| **Grep** | Search for patterns in code | "Search for TODO in all Python files" |
| **Glob** | Find files by pattern | "Find all *.py files in src/" |
| **WebSearch** | Search the web | "Search the web for Python async patterns" |
| **WebFetch** | Fetch and parse web pages | "Fetch the docs at https://..." |

### Using Tools with JARVIS

**Via Chat Interface:**
```
You: Run git status
JARVIS: ✅ Tool executed successfully
        On branch main
        Your branch is up to date...
        ⏱️ Execution time: 0.15s

You: Search for TODO in all Python files
JARVIS: ✅ Found 5 matches:
        src/main.py:42: # TODO: Add error handling
        ...
```

**Via API:**
```powershell
# Using REST API
$body = @{message="git status"} | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/chat -Method Post -Body $body -ContentType "application/json"
```

### Tool Safety Features

The tools system includes safety measures:
- **Blocked Commands**: Dangerous commands like `rm -rf /` are blocked
- **File Size Limits**: Maximum 10MB per file read
- **Restricted Paths**: System directories (/etc, /usr, etc.) are protected
- **Timeout Protection**: Commands timeout after 60 seconds by default
- **Allowed Extensions**: Only safe file types can be read/edited

### Configuring Tools

Tools are automatically enabled when dependencies are installed. Verify with:

```powershell
python -c "from jarvis_tools import get_jarvis_tools; t = get_jarvis_tools(); print('Tools OK')"
```

---

## 13. Real-time Agent Streaming

JARVIS 2.1 introduces an autonomous agent that proactively uses tools while streaming its thought process in real-time.

### Agent Features

- **Visible Thinking**: See JARVIS's reasoning process as `<thinking>` blocks
- **Tool Visibility**: Watch tool calls and results in real-time
- **Task Cancellation**: Cancel running tasks at any time
- **User Interrupts**: Add input while JARVIS is working

### WebSocket Connection

Connect to the agent via WebSocket for real-time streaming:

```javascript
// JavaScript Example
const ws = new WebSocket('ws://localhost:8000/api/agent/ws/my-client-id');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch(data.type) {
        case 'thinking':
            console.log('🧠 Thinking:', data.content);
            break;
        case 'tool_call':
            console.log('🔧 Calling:', data.metadata.tool);
            break;
        case 'tool_result':
            console.log('📋 Result:', data.content);
            break;
        case 'response':
            console.log('💬 Response:', data.content);
            break;
    }
};

// Send a message
ws.send(JSON.stringify({
    type: 'run',
    message: 'What files are in this project?'
}));

// Cancel current task
ws.send(JSON.stringify({type: 'cancel'}));
```

### PowerShell WebSocket Example

```powershell
# Simple REST API call (synchronous)
$body = @{
    message = "Search for TODO comments in all Python files"
    context = @{}
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri http://localhost:8000/api/agent/run -Method Post -Body $body -ContentType "application/json"
$response.events | ForEach-Object { Write-Host "$($_.type): $($_.content)" }
```

### Agent API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agent/ws/{client_id}` | WebSocket | Real-time streaming connection |
| `/api/agent/run` | POST | Synchronous agent execution |
| `/api/agent/cancel` | POST | Cancel a running task |
| `/api/agent/tasks` | GET | List active tasks |
| `/api/agent/status` | GET | Agent system status |

### Event Types

| Event | Description |
|-------|-------------|
| `thinking` | Agent's reasoning/planning |
| `tool_call` | Tool being invoked |
| `tool_result` | Output from tool execution |
| `response` | Final or partial response |
| `status` | Progress updates |
| `error` | Error occurred |
| `cancelled` | Task was cancelled |
| `complete` | Task finished |

### Example: Watching JARVIS Work

When you ask JARVIS to analyze code, you'll see:

```
[STATUS] Starting task abc123
[THINKING] I need to find Python files first, then search for patterns...
[TOOL_CALL] Calling glob with pattern **/*.py
[TOOL_RESULT] Found 15 files: main.py, utils.py, ...
[THINKING] Now I'll search for TODO comments in these files...
[TOOL_CALL] Calling grep with pattern TODO
[TOOL_RESULT] Found 8 matches in 4 files
[RESPONSE] I found 8 TODO comments across 4 Python files:
           1. main.py:42 - TODO: Add error handling
           2. utils.py:15 - TODO: Optimize this function
           ...
[COMPLETE] Task completed (3 iterations)
```

---

## 14. Troubleshooting

### Issue 1: "python: command not found"

```powershell
# Add Python to PATH
$pythonPath = "C:\Program Files\Python311"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$pythonPath;$pythonPath\Scripts", "User")

# Restart PowerShell
```

### Issue 2: "Scripts disabled" error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 3: "ModuleNotFoundError"

```powershell
# Ensure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall packages
pip install --upgrade -r requirements.txt
```

### Issue 4: "API key invalid"

```powershell
# Check .env file
notepad .env

# Verify format (no quotes needed)
# ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Issue 5: Port 8000 in use

```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or use different port
python app.py --port 8001
```

### Issue 6: Voice not working

```powershell
# Check FFmpeg
ffmpeg -version

# Check audio devices
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### Issue 7: ChromaDB installation fails

```powershell
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Then retry
pip install chromadb --no-build-isolation
```

### Issue 8: YAML configuration errors

```powershell
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config/agents.yaml'))"
```

### Issue 9: Tools system not working

```powershell
# Verify aiohttp and beautifulsoup4 are installed
pip install aiohttp beautifulsoup4

# Test tools import
python -c "from jarvis_tools import get_jarvis_tools; print('Tools OK')"

# Check if tools are initialized in logs
# Look for: "[Jarvis] Tools system initialized"
```

### Issue 10: WebSocket connection fails

```powershell
# Ensure websockets package is installed
pip install websockets

# Test WebSocket endpoint
python -c "import asyncio; import websockets; print('WebSockets OK')"

# Check firewall isn't blocking WebSocket connections
# WebSocket uses same port as HTTP (8000)
```

### Issue 11: Agent not responding

```powershell
# Verify agent module loads
python -c "from jarvis_agent import get_agent; a = get_agent(); print('Agent OK')"

# Check for startup messages:
# "[Jarvis] Agent initialized - proactive tool usage enabled"

# If missing, check LLM configuration (agent requires working LLM)
```

### Issue 12: Bash commands timeout

```powershell
# Default timeout is 60 seconds
# For long-running commands, the timeout can be adjusted

# Check if command works directly in PowerShell first
git status  # Should complete quickly

# If commands hang, check network connectivity for git/npm
```

---

## Quick Reference Commands

### Activation
```powershell
cd $env:USERPROFILE\Documents\AI-Projects\two_agent_web_starter_complete
.\venv\Scripts\Activate.ps1
```

### Starting JARVIS
```powershell
cd agent\webapp
python app.py
```

### Testing
```powershell
# Test dependencies
python -c "import fastapi, anthropic; print('OK')"

# Run tests
python -m pytest tests/
```

### Updating
```powershell
git pull origin main
pip install --upgrade -r requirements.txt
```

---

## JARVIS 2.0 Features

### New in Version 2.1

| Feature | Description |
|---------|-------------|
| **Claude Code-like Tools** | Read, Edit, Write, Bash, Grep, Glob, WebSearch, WebFetch |
| **Autonomous Agent** | Proactive tool usage with visible reasoning |
| **Real-time Streaming** | WebSocket streaming of thoughts and actions |
| **Task Cancellation** | Cancel running tasks, add interrupts |
| **Voice System** | Talk to JARVIS using speech |
| **Vision System** | Image analysis, OCR, camera capture |
| **Agents Dashboard** | Real-time view of AI agents |
| **Council System** | Weighted voting for decisions |
| **Flow Engine** | Visual workflow execution |
| **Memory System** | Short-term, long-term, entity memory |
| **YAML Configuration** | Declarative agent/task setup |
| **Pattern Orchestration** | 5 coordination patterns |
| **Multi-Provider LLM** | Anthropic, OpenAI, DeepSeek, Ollama |
| **Document Processing** | Resume generation, document analysis with format options |

### Professional Tools

| Category | Features |
|----------|----------|
| **Administration** | Email summarization/drafting, Calendar intelligence, Workflow automation |
| **Finance** | Spreadsheet processing, Invoice/receipt scanning, Financial templates |
| **Engineering** | VS Code extension, CLI tool, Code review agent |

### Document Processing

JARVIS can process attached files and generate professional outputs:

```
You: [Attach resume_draft.pdf] Make me a professional resume from this document
JARVIS: I've analyzed your document and created a professional resume...

📄 Output Format Options
- PDF - Professional, ready to print/share
- Word (DOCX) - Editable document format
- Plain Text - Simple text file
- Markdown - Formatted text for web/docs

Just let me know your preferred format!
```

### Key URLs

| Page | URL |
|------|-----|
| Main Dashboard | http://localhost:8000/ |
| JARVIS Chat | http://localhost:8000/jarvis |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Agent Status | http://localhost:8000/api/agent/status |
| Agent WebSocket | ws://localhost:8000/api/agent/ws/{client_id} |

---

## Next Steps

1. **Explore Chat Interface:** http://localhost:8000/jarvis
2. **Try Voice Features:** Click microphone button
3. **Test Vision:** Upload an image for analysis
4. **Configure Agents:** Edit `config/agents.yaml`
5. **Read Documentation:** `docs/` directory

---

## Support

- **Documentation:** `docs/` directory
- **Issues:** Report on GitHub
- **API Keys:**
  - Anthropic: https://console.anthropic.com/
  - OpenAI: https://platform.openai.com/
  - ElevenLabs: https://elevenlabs.io

---

**JARVIS 2.0 is now running on your Windows machine!**
