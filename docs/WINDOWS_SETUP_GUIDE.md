# Jarvis AI Agent - Windows PowerShell Setup Guide

**Version:** System-1.2 with Phases 9-11 (Ollama Integration, Business Memory, Production Features)
**Platform:** Windows 10/11
**Prerequisites:** PowerShell 5.1+ (built into Windows)

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installing Python](#2-installing-python)
3. [Installing Git](#3-installing-git)
4. [Setting Up the Project](#4-setting-up-the-project)
5. [Installing Dependencies](#5-installing-dependencies)
6. [Configuring OpenAI API](#6-configuring-openai-api)
7. [Optional: Installing Ollama (Local LLMs)](#7-optional-installing-ollama-local-llms)
8. [Running Jarvis](#8-running-jarvis)
9. [Troubleshooting](#9-troubleshooting)
10. [Using Jarvis](#10-using-jarvis)

---

## 1. System Requirements

### Minimum Requirements
- **OS:** Windows 10 (64-bit) or Windows 11
- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 10GB free space (more if using local LLMs)
- **Network:** Internet connection for API calls and package downloads

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

If Python is not installed or version is below 3.8:

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

**Expected Output:**
```
Python 3.11.7
pip 23.3.1 from C:\Program Files\Python311\Lib\site-packages\pip (python 3.11)
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

2. **Or** use PowerShell to download:

```powershell
# Download Git installer
$gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
$installerPath = "$env:TEMP\git-installer.exe"

# Download
Invoke-WebRequest -Uri $gitUrl -OutFile $installerPath

# Run installer (use default settings)
Start-Process -FilePath $installerPath -Wait

# Verify installation
git --version
```

### Step 2: Verify Git Installation

Close and reopen PowerShell, then:

```powershell
git --version
# Should show: git version 2.43.x
```

---

## 4. Setting Up the Project

### Step 1: Choose Installation Directory

Open PowerShell (regular, not Admin):

```powershell
# Navigate to your preferred location (e.g., Documents)
cd $env:USERPROFILE\Documents

# Or create a dedicated folder
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

**Expected Output:**
```
Path
----
C:\Users\YourName\Documents\AI-Projects\two_agent_web_starter_complete
```

### Step 3: Verify Project Structure

```powershell
# List project contents
dir

# You should see:
# - agent/
# - docs/
# - tests/
# - requirements.txt
# - README.md
```

---

## 5. Installing Dependencies

### Step 1: Create Virtual Environment

**Important:** Virtual environments isolate Python packages for this project.

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

**Expected Output:**
```
(venv) PS C:\Users\YourName\Documents\AI-Projects\two_agent_web_starter_complete>
```

Note the `(venv)` prefix - this means your virtual environment is active.

### Step 2: Upgrade pip

```powershell
# Upgrade pip to latest version
python -m pip install --upgrade pip setuptools wheel
```

### Step 3: Install Core Dependencies

```powershell
# Install required packages
pip install openai anthropic aiohttp fastapi uvicorn

# Install LLM integration
pip install tiktoken

# Install data handling
pip install numpy pandas pydantic python-dotenv pyyaml

# Install vector database for memory
pip install chromadb sentence-transformers

# Install security and utilities
pip install cryptography python-multipart jinja2

# Install async libraries
pip install asyncio aiosqlite
```

### Step 4: Verify Installations

```powershell
# Check installed packages
pip list

# Verify key packages
python -c "import openai; print('OpenAI:', openai.__version__)"
python -c "import chromadb; print('ChromaDB installed successfully')"
```

**Expected Output:**
```
OpenAI: 1.x.x
ChromaDB installed successfully
```

---

## 6. Configuring OpenAI API

### Step 1: Get Your OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Log in to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 2: Create Environment File

```powershell
# Create .env file in project root
$envContent = @"
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-key-here

# Model Selection
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_CHEAP_MODEL=gpt-3.5-turbo

# Anthropic (Claude) - Optional
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# Application Settings
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000

# Database
DATABASE_URL=sqlite:///data/jarvis.db

# Memory Settings
VECTOR_DB_PATH=data/vector_store
EMBEDDING_MODEL=text-embedding-3-small

# Security
SESSION_SECRET=your-random-secret-key-change-this
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/jarvis.log
"@

# Save to .env file
$envContent | Out-File -FilePath .env -Encoding UTF8

Write-Host "Created .env file"
```

### Step 3: Edit .env File with Your API Key

```powershell
# Open .env file in Notepad
notepad .env
```

**Replace** `sk-your-actual-key-here` with your actual OpenAI API key.

**Example:**
```
OPENAI_API_KEY=sk-proj-abc123xyz789yourrealkeyhere
```

Save and close Notepad.

### Step 4: Verify API Key

```powershell
# Test OpenAI connection
python -c "import openai; import os; from dotenv import load_dotenv; load_dotenv(); openai.api_key = os.getenv('OPENAI_API_KEY'); print('API Key loaded:', openai.api_key[:15] + '...')"
```

**Expected Output:**
```
API Key loaded: sk-proj-abc123...
```

---

## 7. Optional: Installing Ollama (Local LLMs)

**Ollama allows you to run local LLMs (Llama 3, Mistral, etc.) without API costs.**

### Step 1: Download Ollama

```powershell
# Download Ollama for Windows
$ollamaUrl = "https://ollama.ai/download/OllamaSetup.exe"
$installerPath = "$env:TEMP\OllamaSetup.exe"

# Download
Invoke-WebRequest -Uri $ollamaUrl -OutFile $installerPath

# Run installer
Start-Process -FilePath $installerPath -Wait
```

**Or** manually download from: https://ollama.ai/download

### Step 2: Verify Ollama Installation

```powershell
# Check Ollama version
ollama --version

# List available models
ollama list
```

### Step 3: Download LLM Models

```powershell
# Download Llama 3 (8B parameters, ~4.7GB)
ollama pull llama3

# Download Mistral (7B parameters, ~4.1GB)
ollama pull mistral

# Download smaller model for testing (3B parameters, ~2GB)
ollama pull phi3
```

**Download times:**
- Llama 3: 10-30 minutes depending on internet speed
- Mistral: 10-25 minutes
- Phi3: 5-15 minutes

### Step 4: Test Ollama

```powershell
# Test Llama 3
ollama run llama3 "Hello, who are you?"

# Test API (in another PowerShell window)
Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method POST -Body '{"model":"llama3","prompt":"Why is the sky blue?","stream":false}' -ContentType "application/json"
```

### Step 5: Configure Jarvis to Use Ollama

```powershell
# Add Ollama configuration to .env
Add-Content -Path .env -Value @"

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_ENABLED=true

# Hybrid Strategy (80% local, 20% cloud)
LLM_HYBRID_MODE=true
LLM_LOCAL_RATIO=0.8
"@
```

---

## 8. Running Jarvis

### Step 1: Create Data Directories

```powershell
# Create required directories
mkdir -p data, logs, artifacts, sites

# Verify directories
dir
```

### Step 2: Initialize Database

```powershell
# Run database migrations
python -c "
from pathlib import Path
import sqlite3

# Create database
db_path = Path('data/jarvis.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute('CREATE TABLE IF NOT EXISTS system_info (key TEXT PRIMARY KEY, value TEXT)')
conn.execute('INSERT OR REPLACE INTO system_info VALUES (?, ?)', ('version', '1.2'))
conn.commit()
conn.close()

print('✓ Database initialized')
"
```

### Step 3: Start Jarvis Web Interface

```powershell
# Make sure virtual environment is active
# (you should see (venv) in prompt)

# Start web server
cd agent\webapp
python app.py
```

**Expected Output:**
```
============================================================
  Jarvis AI Agent - System 1.2
============================================================
  Starting web server on http://127.0.0.1:8000
  Press Ctrl+C to stop
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Access Jarvis Web Interface

1. Open your web browser
2. Navigate to: http://localhost:8000
3. You should see the Jarvis dashboard

### Step 5: Test Jarvis

**Option 1: Web Interface**
- Go to http://localhost:8000
- Click "New Task" or "Create Mission"
- Enter a task (e.g., "Create a simple calculator in Python")
- Click "Execute"

**Option 2: Python REPL**

Open a new PowerShell window and run:

```powershell
# Activate virtual environment
cd C:\Users\YourName\Documents\AI-Projects\two_agent_web_starter_complete
.\venv\Scripts\Activate.ps1

# Start Python REPL
python
```

In Python:

```python
import asyncio
from agent.llm.ollama_client import OllamaClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test OpenAI connection
async def test_openai():
    import openai
    import os

    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello!"}]
    )
    print(response.choices[0].message.content)

# Run test
asyncio.run(test_openai())
```

**Expected Output:**
```
Hello! How can I assist you today?
```

---

## 9. Troubleshooting

### Issue 1: "python: command not found"

**Solution:**
```powershell
# Verify Python is in PATH
$env:Path -split ';' | Select-String -Pattern "Python"

# If not found, add Python to PATH
$pythonPath = "C:\Program Files\Python311"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$pythonPath;$pythonPath\Scripts", "User")

# Restart PowerShell
```

### Issue 2: "Cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
# Enable PowerShell script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Confirm
Get-ExecutionPolicy
```

### Issue 3: "ModuleNotFoundError: No module named 'openai'"

**Solution:**
```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall packages
pip install --upgrade openai

# Verify installation
pip show openai
```

### Issue 4: "OpenAI API Error: Incorrect API key"

**Solution:**
```powershell
# Check .env file
notepad .env

# Verify API key format (should start with sk-)
# Verify no extra spaces or quotes

# Test API key
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key:', os.getenv('OPENAI_API_KEY')[:15])"
```

### Issue 5: Port 8000 Already in Use

**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in app.py
```

### Issue 6: Ollama Connection Refused

**Solution:**
```powershell
# Check if Ollama is running
Get-Process ollama

# If not running, start Ollama
Start-Process ollama

# Verify Ollama API
Invoke-WebRequest -Uri http://localhost:11434/api/tags
```

### Issue 7: ChromaDB Installation Fails

**Solution:**
```powershell
# Install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install pre-built wheel
pip install chromadb --no-build-isolation

# Alternative: Use SQLite for memory instead
```

---

## 10. Using Jarvis

### Basic Task Execution

```powershell
# Create a simple task file
$task = @"
{
  "task": "Create a Python script that calculates fibonacci numbers",
  "requirements": [
    "Function should take n as parameter",
    "Return list of first n fibonacci numbers",
    "Include docstring and type hints"
  ],
  "output_path": "sites/fibonacci"
}
"@

$task | Out-File -FilePath task.json -Encoding UTF8

# Run task
python agent/mission_runner.py task.json
```

### Using the Web Interface

1. **Start the server:**
   ```powershell
   cd agent\webapp
   python app.py
   ```

2. **Open browser:** http://localhost:8000

3. **Create a new task:**
   - Click "New Task"
   - Enter task description
   - Set options (model, temperature, etc.)
   - Click "Execute"

4. **Monitor progress:**
   - View real-time logs
   - Check task status
   - Download results

### Using Ollama for Local LLMs

```python
import asyncio
from agent.llm.ollama_client import OllamaClient

async def test_ollama():
    client = OllamaClient(base_url="http://localhost:11434")

    # List available models
    models = await client.list_models()
    print("Available models:", models)

    # Chat completion
    response = await client.chat(
        prompt="Explain quantum computing in simple terms",
        model="llama3"
    )

    print(response.content)

# Run
asyncio.run(test_ollama())
```

### Using Hybrid LLM Strategy

```python
from agent.llm.hybrid_strategy import HybridStrategy

async def hybrid_example():
    strategy = HybridStrategy(
        local_ratio=0.8,  # 80% local, 20% cloud
        quality_threshold=0.7
    )

    # Automatically routes to best model
    result = await strategy.execute_with_quality_check(
        prompt="Write a Python function to reverse a string",
        task_type="code_generation"
    )

    print(f"Used model: {result['model']}")
    print(f"Response: {result['content']}")

asyncio.run(hybrid_example())
```

---

## Quick Reference Commands

### Activation
```powershell
# Navigate to project
cd C:\Users\YourName\Documents\AI-Projects\two_agent_web_starter_complete

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

### Starting Jarvis
```powershell
# Start web interface
cd agent\webapp
python app.py
```

### Testing Components
```powershell
# Test OpenAI connection
python -c "from dotenv import load_dotenv; load_dotenv(); import openai, os; print(openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')).models.list())"

# Test Ollama connection
ollama list

# Run tests
python -m pytest agent/tests/
```

### Updating
```powershell
# Pull latest changes
git pull origin main

# Update dependencies
pip install --upgrade -r requirements.txt
```

---

## System Capabilities

Jarvis now includes:

**Phase 9: Ollama Integration**
- Local LLM inference (Llama 3, Mistral, Phi3)
- Intelligent model routing
- Performance tracking
- Hybrid cloud/local strategy (80% local, 20% cloud)

**Phase 10: Business Memory**
- Long-term context storage with ChromaDB
- Semantic search and retrieval
- Personal preference learning
- Cross-session continuity

**Phase 11: Production Features**
- **11.1:** Error handling with circuit breakers
- **11.2:** Monitoring with metrics and alerts
- **11.3:** Security with authentication and rate limiting
- **11.4:** Performance optimization with caching

---

## Next Steps

1. **Explore the web interface** at http://localhost:8000
2. **Try sample tasks** in the dashboard
3. **Configure Ollama** for local LLM usage
4. **Read the system manual** at `docs/SYSTEM_1_2_MANUAL.md`
5. **Review examples** in `examples/` directory

---

## Support

- **Documentation:** `docs/` directory
- **Issues:** Report on GitHub
- **API Keys:** Manage at https://platform.openai.com/

---

**Congratulations! Jarvis is now running on your Windows machine.** 🎉
