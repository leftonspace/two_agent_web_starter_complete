# JARVIS 2.0 Installation Guide

**Version:** 2.0.0
**Date:** November 23, 2025

Complete installation guide for JARVIS 2.0 - the AI Agent Orchestration Platform.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Install](#quick-install)
3. [Detailed Installation](#detailed-installation)
4. [Configuration Files](#configuration-files)
5. [Voice System Setup](#voice-system-setup)
6. [Vision System Setup](#vision-system-setup)
7. [Database Setup](#database-setup)
8. [Verification](#verification)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Operating System
- **Linux** (Ubuntu 20.04+, Debian 10+, CentOS 8+) - Recommended
- **macOS** (10.15+)
- **Windows** (WSL2 recommended) - See [WINDOWS_SETUP_GUIDE.md](./WINDOWS_SETUP_GUIDE.md)

### Hardware
- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 20GB free space (more for local LLMs)
- **GPU:** Optional, for local LLM inference

### Software Prerequisites
- Python 3.9+ (3.11 recommended)
- Git 2.30+
- SQLite3
- Node.js 18+ (optional, for frontend development)

---

## Quick Install

```bash
# Clone repository
git clone https://github.com/your-org/jarvis.git
cd jarvis

# Run automated setup
./scripts/install.sh

# Configure environment
cp .env.example .env
nano .env  # Add your API keys

# Start JARVIS
python -m agent.webapp.app
```

---

## Detailed Installation

### Part 1: System Dependencies

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv python3-dev \
    git sqlite3 libsqlite3-dev \
    build-essential libssl-dev libffi-dev pkg-config \
    ffmpeg libportaudio2  # For voice system
```

#### macOS

```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 git sqlite3 openssl libffi pkg-config
brew install ffmpeg portaudio  # For voice system
```

#### CentOS/RHEL

```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3 python3-pip python3-devel \
    git sqlite sqlite-devel openssl-devel libffi-devel \
    ffmpeg portaudio-devel
```

### Part 2: Python Environment

```bash
cd /home/user/two_agent_web_starter_complete

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Part 3: Install Python Dependencies

```bash
# Install all requirements
pip install -r requirements.txt
```

**Or install manually:**

```bash
# Core Web Framework
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 jinja2==3.1.2 python-multipart==0.0.6

# HTTP Client & Async
pip install aiohttp==3.9.0 httpx==0.25.2

# LLM Providers
pip install anthropic>=0.18.0 openai>=1.12.0

# Security & Encryption
pip install cryptography==41.0.7 pyjwt==2.8.0

# Database Drivers
pip install asyncpg==0.29.0 aiomysql==0.2.0 aiosqlite==0.19.0

# Data Validation & Configuration
pip install pydantic==2.5.0 python-dotenv==1.0.0 pyyaml==6.0.1

# Memory System
pip install chromadb==0.4.22 sentence-transformers==2.2.2

# Voice System (optional)
pip install elevenlabs==0.2.27 openai-whisper==20231117 sounddevice==0.4.6 numpy==1.26.2

# Vision System (optional)
pip install pillow==10.1.0

# Utilities
pip install requests==2.31.0 python-dateutil==2.8.2 networkx==3.2.1
```

### Part 4: Create Configuration Directory

```bash
mkdir -p config
mkdir -p data
mkdir -p logs
mkdir -p artifacts
```

### Part 5: Environment Configuration

Create `.env` file:

```bash
cat > .env << 'EOF'
# =============================================================================
# JARVIS 2.0 Environment Configuration
# =============================================================================

# LLM Provider API Keys (at least one required)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# Optional LLM Providers
DEEPSEEK_API_KEY=
QWEN_API_KEY=

# Voice System (optional - for voice features)
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
CONNECTION_POOL_SIZE=10

# Application
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000
EOF

# Secure the file
chmod 600 .env
```

### Part 6: YAML Configuration Files

#### agents.yaml

```bash
cat > config/agents.yaml << 'EOF'
version: "2.0"
metadata:
  author: "admin"
  description: "Default JARVIS 2.0 agent configuration"

agents:
  - id: jarvis
    name: "JARVIS"
    role: "Master Orchestrator"
    goal: "Orchestrate all AI agents and assist users with any task"
    backstory: |
      JARVIS is the master AI assistant, inspired by the AI from Iron Man.
      Speaks with a refined British butler persona, always professional
      and slightly witty.
    specialization: orchestration
    llm_config:
      provider: anthropic
      model: claude-3-sonnet
      temperature: 0.7

  - id: developer
    name: "Code Employee"
    role: "Software Developer"
    goal: "Write clean, efficient, well-tested code"
    specialization: coding
    tools:
      - code_executor
      - file_manager
      - git_operations
    llm_config:
      provider: anthropic
      model: claude-3-sonnet
      temperature: 0.3
EOF
```

#### llm_config.yaml

```bash
cat > config/llm_config.yaml << 'EOF'
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
EOF
```

---

## Configuration Files

JARVIS 2.0 uses YAML-based configuration:

| File | Purpose |
|------|---------|
| `config/agents.yaml` | Agent definitions |
| `config/tasks.yaml` | Task templates |
| `config/llm_config.yaml` | LLM provider settings |
| `config/flows.yaml` | Workflow definitions |
| `config/memory.yaml` | Memory system settings |
| `config/council.yaml` | Council voting settings |
| `config/patterns.yaml` | Orchestration patterns |

See [JARVIS_2_0_CONFIGURATION_GUIDE.md](./JARVIS_2_0_CONFIGURATION_GUIDE.md) for detailed configuration options.

---

## Voice System Setup

### Option 1: ElevenLabs (Recommended for JARVIS voice)

1. **Get API Key:**
   - Sign up at https://elevenlabs.io
   - Get API key from dashboard
   - Add to `.env`: `ELEVENLABS_API_KEY=...`

2. **Clone/Create Voice:**
   - Go to ElevenLabs Voice Lab
   - Clone a British accent voice or create custom
   - Copy voice ID to `.env`: `VOICE_ID=...`

### Option 2: OpenAI TTS (Fallback)

```bash
# Already configured if OPENAI_API_KEY is set
# Uses "onyx" voice by default
```

### Speech-to-Text (Whisper)

```bash
# Install Whisper for local STT
pip install openai-whisper

# Download model (first use will auto-download)
python -c "import whisper; whisper.load_model('base')"
```

### Audio Dependencies

```bash
# Linux
sudo apt-get install -y ffmpeg libportaudio2

# macOS
brew install ffmpeg portaudio

# Test audio
python -c "import sounddevice; print(sounddevice.query_devices())"
```

---

## Vision System Setup

### GPT-4 Vision

```bash
# Already configured if OPENAI_API_KEY is set
# Supports image analysis via GPT-4 Vision
```

### Claude Vision

```bash
# Already configured if ANTHROPIC_API_KEY is set
# Supports image analysis via Claude 3 Vision
```

### Image Processing

```bash
# Install Pillow for image processing
pip install pillow

# Test
python -c "from PIL import Image; print('Pillow OK')"
```

---

## Database Setup

### SQLite (Default - Development)

```bash
# Initialize database
python -c "
from pathlib import Path
import sqlite3

db_path = Path('data/jarvis.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('CREATE TABLE IF NOT EXISTS system_info (key TEXT PRIMARY KEY, value TEXT)')
conn.execute('INSERT OR REPLACE INTO system_info VALUES (?, ?)', ('version', '2.0.0'))
conn.commit()
conn.close()
print('✓ Database initialized')
"
```

### PostgreSQL (Production)

```bash
# Install driver
pip install asyncpg

# Update .env
DATABASE_URL=postgresql://user:pass@localhost:5432/jarvis

# Create database
psql -U postgres << EOF
CREATE DATABASE jarvis;
CREATE USER jarvis_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE jarvis TO jarvis_user;
EOF
```

### Run Migrations

```bash
python -m agent.migrate.database --auto
```

---

## Verification

### Step 1: Verify Dependencies

```bash
python3 << 'EOF'
import sys
print(f"Python: {sys.version}")

modules = [
    'fastapi', 'uvicorn', 'aiohttp', 'anthropic', 'openai',
    'cryptography', 'pydantic', 'yaml', 'jinja2', 'chromadb'
]

print("\nChecking modules:")
for module in modules:
    try:
        __import__(module)
        print(f"  ✓ {module}")
    except ImportError:
        print(f"  ✗ {module} (MISSING)")
EOF
```

### Step 2: Validate Configuration

```bash
python -m agent.config validate
```

### Step 3: Test LLM Connection

```bash
python -c "
from agent.llm import get_router
import asyncio

async def test():
    router = get_router()
    result = await router.health_check()
    print('LLM Health:', result)

asyncio.run(test())
"
```

### Step 4: Start Server

```bash
cd agent/webapp
python app.py
```

### Step 5: Test Endpoints

```bash
# Health check
curl http://127.0.0.1:8000/health

# API docs
open http://127.0.0.1:8000/docs
```

### Step 6: Access Web Interface

Open browser: http://127.0.0.1:8000/jarvis

---

## Production Deployment

### 1. Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name jarvis.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Systemd Service

```bash
sudo cat > /etc/systemd/system/jarvis.service << 'EOF'
[Unit]
Description=JARVIS 2.0 AI Agent Platform
After=network.target

[Service]
Type=simple
User=jarvis
WorkingDirectory=/home/user/two_agent_web_starter_complete
Environment="PATH=/home/user/two_agent_web_starter_complete/venv/bin"
ExecStart=/home/user/two_agent_web_starter_complete/venv/bin/python -m agent.webapp.app
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jarvis
sudo systemctl start jarvis
```

### 3. SSL with Certbot

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d jarvis.yourdomain.com
```

### 4. Production Environment

```bash
# Update .env for production
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=WARNING
SECRET_KEY=<generate-strong-key>
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Database locked | Use PostgreSQL for production |
| API key invalid | Check `.env` file, no quotes needed |
| Voice not working | Install ffmpeg and portaudio |
| Camera permission denied | Use HTTPS in production |

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export APP_DEBUG=true
python -m agent.webapp.app
```

### View Logs

```bash
tail -f logs/jarvis.log
```

### Full Diagnostics

```bash
python -m agent.diagnostics --full-report
```

---

## Features Overview

### Core Features
| Feature | Description |
|---------|-------------|
| **Voice System** | Text-to-speech and speech-to-text |
| **Vision System** | Image analysis, OCR, camera capture |
| **Agents Dashboard** | Real-time AI agent monitoring |
| **Council System** | Weighted voting for decisions |
| **Flow Engine** | Visual workflow execution |
| **Memory System** | Short-term, long-term, entity memory |
| **Document Processing** | Resume generation, document analysis |

### Professional Tools
| Category | Tools |
|----------|-------|
| **Administration** | Email integration, Calendar intelligence, Workflow automation |
| **Finance** | Spreadsheet processing, Invoice/receipt scanning, Financial templates |
| **Engineering** | VS Code extension, CLI tool, Code review agent |

### Document Processing
JARVIS can process attached files and generate outputs:
- **Resume Generation** - Create professional resumes from uploaded documents
- **Document Summary** - Summarize long documents
- **Information Extraction** - Extract key data from files
- **Format Options** - Export to PDF, Word, Plain Text, or Markdown

---

## Next Steps

1. **Read Demo Guide:** [DEMO_GUIDE.md](./DEMO_GUIDE.md)
2. **Configure Agents:** [JARVIS_2_0_CONFIGURATION_GUIDE.md](./JARVIS_2_0_CONFIGURATION_GUIDE.md)
3. **Development:** [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)
4. **Troubleshooting:** [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
5. **Windows Users:** [WINDOWS_SETUP_GUIDE.md](./WINDOWS_SETUP_GUIDE.md)
6. **Admin Tools:** [ADMIN_TOOLS.md](./ADMIN_TOOLS.md)

---

**Installation complete! JARVIS 2.0 is ready.**

Start with: `python -m agent.webapp.app`
