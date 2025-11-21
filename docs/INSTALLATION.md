# Complete Installation Guide

Complete installation requirements for the Department-in-a-Box system from scratch.

## System Requirements

### Operating System
- **Linux** (Ubuntu 20.04+, Debian 10+, CentOS 8+)
- **macOS** (10.15+)
- **Windows** (WSL2 recommended)

### Hardware
- **CPU:** 2+ cores
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 10GB free space
- **Network:** Internet connection for package downloads

---

## Part 1: Core System Dependencies

### 1. Python 3.8+

**Check if installed:**
```bash
python3 --version
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-dev
```

**macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip python3-devel
```

**Windows (WSL2):**
```bash
# First install WSL2, then:
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-dev
```

### 2. Git

**Check if installed:**
```bash
git --version
```

**Ubuntu/Debian:**
```bash
sudo apt-get install -y git
```

**macOS:**
```bash
brew install git
```

**CentOS/RHEL:**
```bash
sudo yum install -y git
```

### 3. SQLite3

**Check if installed:**
```bash
sqlite3 --version
```

**Ubuntu/Debian:**
```bash
sudo apt-get install -y sqlite3 libsqlite3-dev
```

**macOS:**
```bash
brew install sqlite3
```

**CentOS/RHEL:**
```bash
sudo yum install -y sqlite sqlite-devel
```

### 4. Build Tools (Required for Python packages)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    pkg-config
```

**macOS:**
```bash
xcode-select --install
brew install openssl libffi pkg-config
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y openssl-devel libffi-devel
```

---

## Part 2: Python Dependencies

### 1. Create Virtual Environment (Recommended)

```bash
cd /home/user/two_agent_web_starter_complete

# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows WSL)
source venv/bin/activate
```

### 2. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 3. Install Core Dependencies

**Required for all functionality:**
```bash
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    aiohttp==3.9.0 \
    jinja2==3.1.2 \
    python-multipart==0.0.6 \
    cryptography==41.0.7
```

**Explanation:**
- `fastapi` - Web framework for REST API
- `uvicorn` - ASGI server for FastAPI
- `aiohttp` - Async HTTP client for integrations
- `jinja2` - Template engine for web UI
- `python-multipart` - Form data parsing
- `cryptography` - Credential encryption (Fernet)

### 4. Install Database Drivers

**For PostgreSQL support:**
```bash
pip install asyncpg==0.29.0
```

**For MySQL support:**
```bash
pip install aiomysql==0.2.0
```

**For SQLite support (async):**
```bash
pip install aiosqlite==0.19.0
```

**Install all database drivers:**
```bash
pip install asyncpg==0.29.0 aiomysql==0.2.0 aiosqlite==0.19.0
```

### 5. Install Optional Dependencies

**For enhanced functionality:**
```bash
pip install \
    python-dotenv==1.0.0 \
    pyyaml==6.0.1 \
    requests==2.31.0 \
    pydantic==2.5.0
```

**Explanation:**
- `python-dotenv` - Environment variable management
- `pyyaml` - YAML configuration files
- `requests` - Synchronous HTTP client (for tools)
- `pydantic` - Data validation

---

## Part 3: Complete Requirements File

### Create requirements.txt

```bash
cat > /home/user/two_agent_web_starter_complete/requirements.txt << 'EOF'
# Core Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6

# HTTP Client & Async
aiohttp==3.9.0
httpx==0.25.2

# Security & Encryption
cryptography==41.0.7

# Database Drivers
asyncpg==0.29.0        # PostgreSQL
aiomysql==0.2.0        # MySQL
aiosqlite==0.19.0      # SQLite

# Data Validation & Parsing
pydantic==2.5.0
python-dotenv==1.0.0
pyyaml==6.0.1

# Utilities
requests==2.31.0
python-dateutil==2.8.2

# Optional: Enhanced Features
# Uncomment if needed:
# redis==5.0.1          # For caching
# celery==5.3.4         # For background tasks
# prometheus-client     # For metrics
EOF
```

### Install from requirements.txt

```bash
cd /home/user/two_agent_web_starter_complete
pip install -r requirements.txt
```

---

## Part 4: Optional Database Servers

### PostgreSQL (Optional - for production)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE department_box;
CREATE USER dbuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE department_box TO dbuser;
\q
EOF
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb department_box
```

**Connection String:**
```
postgresql://dbuser:your_password@localhost:5432/department_box
```

### MySQL (Optional - for production)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql

# Secure installation
sudo mysql_secure_installation

# Create database and user
sudo mysql << EOF
CREATE DATABASE department_box;
CREATE USER 'dbuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON department_box.* TO 'dbuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

**macOS:**
```bash
brew install mysql
brew services start mysql

# Create database
mysql -u root << EOF
CREATE DATABASE department_box;
EXIT;
EOF
```

**Connection String:**
```
mysql://dbuser:your_password@localhost:3306/department_box
```

---

## Part 5: System Configuration

### 1. Create Data Directory

```bash
cd /home/user/two_agent_web_starter_complete
mkdir -p data
mkdir -p logs
mkdir -p run_logs_main
mkdir -p run_workflows

# Set permissions
chmod 755 data
chmod 755 logs
```

### 2. Create Environment File

```bash
cat > /home/user/two_agent_web_starter_complete/.env << 'EOF'
# Application Settings
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000

# Database (if using PostgreSQL/MySQL)
# DATABASE_URL=postgresql://dbuser:password@localhost:5432/department_box
# DATABASE_URL=mysql://dbuser:password@localhost:3306/department_box

# Integration Security
INTEGRATION_MASTER_KEY=your-secure-key-here-change-in-production

# Session Secret (change in production)
SESSION_SECRET=your-session-secret-here-change-in-production

# API Keys (add as needed)
# BAMBOOHR_API_KEY=your-bamboohr-key
# GOOGLE_API_KEY=your-google-key

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

chmod 600 .env
```

### 3. Initialize Database Schema

```bash
cd /home/user/two_agent_web_starter_complete

# Run approval workflow migration
python agent/migrations/001_approval_workflows.py
```

**Expected output:**
```
================================================================================
Starting Approval Workflow Migration
================================================================================
...
✓ Migration Complete!
```

---

## Part 6: Verification & Testing

### 1. Verify Python Installation

```bash
python3 << 'EOF'
import sys
print(f"Python version: {sys.version}")

# Check required modules
modules = [
    'fastapi',
    'uvicorn',
    'aiohttp',
    'cryptography',
    'asyncpg',
    'aiomysql',
    'aiosqlite',
    'jinja2',
    'pydantic'
]

print("\nChecking installed modules:")
for module in modules:
    try:
        __import__(module)
        print(f"  ✓ {module}")
    except ImportError:
        print(f"  ✗ {module} (MISSING)")
EOF
```

**Expected output:**
```
Python version: 3.x.x
Checking installed modules:
  ✓ fastapi
  ✓ uvicorn
  ✓ aiohttp
  ✓ cryptography
  ✓ asyncpg
  ✓ aiomysql
  ✓ aiosqlite
  ✓ jinja2
  ✓ pydantic
```

### 2. Run Unit Tests

```bash
cd /home/user/two_agent_web_starter_complete
python tests/test_approval_workflows.py
```

**Expected output:**
```
================================================================================
TEST SUMMARY
================================================================================
Total Tests: 10
Passed: 10 (100.0%)
Failed: 0 (0.0%)
================================================================================
```

### 3. Start Web Server

```bash
cd /home/user/two_agent_web_starter_complete/agent/webapp
python app.py
```

**Expected output:**
```
============================================================
  AI Dev Team Dashboard
============================================================
  Starting web server on http://127.0.0.1:8000
  Press Ctrl+C to stop
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 4. Test Web Server

In a new terminal:
```bash
curl http://127.0.0.1:8000/health
```

**Expected output:**
```json
{"status":"ok"}
```

### 5. Test Web UI

Open browser: `http://127.0.0.1:8000`

**You should see:**
- Main dashboard
- Navigation menu
- Project selection

---

## Part 7: Optional Enhancements

### 1. Redis (For Caching)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Python client
pip install redis==5.0.1
```

**macOS:**
```bash
brew install redis
brew services start redis

pip install redis==5.0.1
```

### 2. Nginx (For Production Deployment)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y nginx

# Create site configuration
sudo cat > /etc/nginx/sites-available/department-box << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/department-box /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### 3. Systemd Service (For Production)

```bash
sudo cat > /etc/systemd/system/department-box.service << 'EOF'
[Unit]
Description=Department in a Box
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/user/two_agent_web_starter_complete/agent/webapp
Environment="PATH=/home/user/two_agent_web_starter_complete/venv/bin"
ExecStart=/home/user/two_agent_web_starter_complete/venv/bin/python app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable department-box
sudo systemctl start department-box
```

### 4. SSL/TLS with Certbot

```bash
# Ubuntu/Debian
sudo apt-get install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com
```

---

## Part 8: Development Tools (Optional)

### 1. Code Quality Tools

```bash
pip install \
    black==23.11.0 \
    flake8==6.1.0 \
    mypy==1.7.1 \
    pylint==3.0.3 \
    isort==5.12.0
```

### 2. Testing Tools

```bash
pip install \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    httpx==0.25.2
```

### 3. Documentation Tools

```bash
pip install \
    sphinx==7.2.6 \
    sphinx-rtd-theme==2.0.0
```

---

## Part 9: Troubleshooting

### Common Issues

**1. Permission Denied Errors**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER /home/user/two_agent_web_starter_complete
chmod -R 755 /home/user/two_agent_web_starter_complete
chmod 600 /home/user/two_agent_web_starter_complete/.env
```

**2. Port 8000 Already in Use**
```bash
# Find process
lsof -ti:8000

# Kill process
lsof -ti:8000 | xargs kill -9
```

**3. Python Module Not Found**
```bash
# Verify Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Reinstall packages
pip install --force-reinstall -r requirements.txt
```

**4. Database Connection Errors**
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Check MySQL
sudo systemctl status mysql

# Check SQLite permissions
ls -la data/*.db
chmod 644 data/*.db
```

**5. Cryptography Installation Fails**
```bash
# Ubuntu/Debian - Install dependencies
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev

# macOS - Install OpenSSL
brew install openssl
export LDFLAGS="-L/usr/local/opt/openssl/lib"
export CPPFLAGS="-I/usr/local/opt/openssl/include"
pip install cryptography
```

---

## Part 10: Quick Start Script

### All-in-One Installation Script

```bash
#!/bin/bash
# Save as: install.sh

set -e

echo "================================"
echo "Installing Department in a Box"
echo "================================"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y \
        python3 python3-pip python3-venv python3-dev \
        git sqlite3 libsqlite3-dev \
        build-essential libssl-dev libffi-dev pkg-config
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install python@3.11 git sqlite3 openssl libffi pkg-config
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Create virtual environment
cd /home/user/two_agent_web_starter_complete
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p data logs run_logs_main run_workflows

# Initialize database
python agent/migrations/001_approval_workflows.py

# Run tests
python tests/test_approval_workflows.py

echo "================================"
echo "✓ Installation complete!"
echo "================================"
echo ""
echo "Start the server with:"
echo "  cd agent/webapp && python app.py"
echo ""
echo "Then visit: http://127.0.0.1:8000"
```

**Make executable and run:**
```bash
chmod +x install.sh
./install.sh
```

---

## Summary Checklist

After completing this guide, you should have:

- ✅ Python 3.8+ installed
- ✅ Git installed
- ✅ SQLite3 installed
- ✅ Build tools installed
- ✅ Virtual environment created
- ✅ All Python dependencies installed
- ✅ Database drivers installed (PostgreSQL, MySQL, SQLite)
- ✅ Data directories created
- ✅ Environment file configured
- ✅ Database schema initialized
- ✅ Unit tests passing (10/10)
- ✅ Web server running
- ✅ Web UI accessible

---

## Minimum Installation (For Testing)

If you just want to test quickly:

```bash
# 1. Install Python and SQLite
sudo apt-get update && sudo apt-get install -y python3 python3-pip sqlite3

# 2. Install core dependencies
pip install fastapi uvicorn aiohttp cryptography aiosqlite jinja2 python-multipart

# 3. Run migration
python agent/migrations/001_approval_workflows.py

# 4. Start server
cd agent/webapp && python app.py
```

---

## Next Steps

After installation:
1. **Follow Demo Guide:** See [DEMO_GUIDE.md](./DEMO_GUIDE.md)
2. **Configure Integrations:** Add BambooHR, databases, etc.
3. **Customize Workflows:** Modify approval workflows for your needs
4. **Deploy to Production:** Set up Nginx, SSL, systemd service

---

## Support Resources

- **Demo Guide:** `docs/DEMO_GUIDE.md`
- **Phase 3.1 Documentation:** `docs/PHASE_3_1_APPROVAL_WORKFLOWS.md`
- **Phase 3.2 Documentation:** `docs/PHASE_3_2_INTEGRATION_FRAMEWORK.md`
- **GitHub Issues:** Report problems and get help

---

**Installation Complete! You're ready to run the system.** 🎉

For the full demo walkthrough, proceed to [DEMO_GUIDE.md](./DEMO_GUIDE.md).
