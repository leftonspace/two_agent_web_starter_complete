# JARVIS 2.0 - Complete Features & Tools Reference

**Version:** 2.0.0
**Date:** November 25, 2025

Complete reference guide for all JARVIS 2.0 features, tools, and API integrations.

---

## Table of Contents

1. [LLM Providers](#1-llm-providers-ai-engines)
2. [Action Tools](#2-action-tools-phase-74)
3. [HR & Communication Tools](#3-hr--communication-tools-phase-23)
4. [Document Generation Tools](#4-document-generation-tools-phase-24)
5. [Meeting Platform Integration](#5-meeting-platform-integration-phase-7a1)
6. [Voice System](#6-voice-system)
7. [Vision System](#7-vision-system)
8. [Code Execution Engine](#8-code-execution-engine-phase-81)
9. [Git Operations](#9-git-operations-phase-83)
10. [Universal API Client](#10-universal-api-client-phase-82)
11. [External Integrations](#11-external-integrations)
12. [Core Platform Features](#12-core-platform-features)
13. [Database Support](#13-database-support)
14. [Quick Setup Checklist](#quick-setup-checklist)

---

## 1. LLM Providers (AI Engines)

| Provider | API Key Required | Models | Setup URL |
|----------|-----------------|--------|-----------|
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | Claude 3 Opus, Sonnet, Haiku | https://console.anthropic.com |
| **OpenAI** | `OPENAI_API_KEY` | GPT-4 Turbo, GPT-4, GPT-3.5 | https://platform.openai.com/api-keys |
| **DeepSeek** | `DEEPSEEK_API_KEY` (optional) | DeepSeek models | https://platform.deepseek.com |
| **Qwen** | `QWEN_API_KEY` (optional) | Qwen models | - |

---

## 2. Action Tools (PHASE 7.4)

### Domain Registration

| Tool | `buy_domain` |
|------|--------------|
| **API** | Namecheap |
| **Required** | `NAMECHEAP_API_KEY`, `NAMECHEAP_API_USER`, `NAMECHEAP_CLIENT_IP` |
| **Setup** | https://ap.www.namecheap.com/settings/tools/apiaccess/ |
| **Features** | Domain availability check, purchase, nameserver config |
| **Cost** | ~$12.98/year (.com) |

### Website Deployment

| Tool | `deploy_website` |
|------|------------------|
| **APIs** | Vercel + GitHub |
| **Required** | `VERCEL_TOKEN`, `GITHUB_TOKEN` |
| **Setup** | https://vercel.com/account/tokens, https://github.com/settings/tokens |
| **Features** | Create GitHub repos, deploy to Vercel, custom domains |

### SMS Messaging

| Tool | `send_sms` |
|------|------------|
| **API** | Twilio |
| **Required** | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` |
| **Setup** | https://console.twilio.com/ |
| **Features** | Send SMS, Unicode support, multi-segment messages |
| **Cost** | ~$0.0079/message (US) |

### Payment Processing

| Tool | `make_payment` |
|------|----------------|
| **API** | Stripe |
| **Required** | `STRIPE_API_KEY` |
| **Setup** | https://dashboard.stripe.com/apikeys |
| **Features** | Process payments, refunds |
| **Note** | Use `sk_test_...` for development! |

---

## 3. HR & Communication Tools (PHASE 2.3)

### Email Sending

| Tool | `send_email` |
|------|--------------|
| **Protocol** | SMTP |
| **Required** | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` |
| **Features** | HTML/text emails, Jinja2 templates, attachments, CC/BCC |
| **Example Config** | Gmail: `smtp.gmail.com:587` |

### Calendar Events

| Tool | `create_calendar_event` |
|------|-------------------------|
| **APIs** | Google Calendar, Microsoft Graph |
| **Required** | OAuth credentials (see Meeting Integration) |
| **Features** | Create events, set reminders, invite attendees |

### HRIS Records

| Tool | `create_hris_record` |
|------|----------------------|
| **Features** | Create employee records, onboarding documents |

---

## 4. Document Generation Tools (PHASE 2.4)

| Tool | Description | Dependencies |
|------|-------------|--------------|
| `generate_pdf` | HTML-to-PDF, reports | `pip install reportlab weasyprint` |
| `generate_word` | Word documents (.docx) | `pip install python-docx` |
| `generate_excel` | Spreadsheets (.xlsx) | `pip install openpyxl` |

**Features:**
- HTML-to-PDF conversion
- Structured reports with tables, headings
- Template rendering
- PDF merging

---

## 5. Meeting Platform Integration (PHASE 7A.1)

### Zoom

| Setting | Value |
|---------|-------|
| **API** | `ZOOM_API_KEY`, `ZOOM_API_SECRET` |
| **SDK** | `ZOOM_SDK_KEY`, `ZOOM_SDK_SECRET` |
| **Setup** | https://marketplace.zoom.us/ (Meeting SDK app) |
| **Features** | Create/join meetings, recording access |

### Microsoft Teams

| Setting | Value |
|---------|-------|
| **Required** | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| **Setup** | https://portal.azure.com/ → Azure AD → App registrations |
| **Features** | Teams meeting creation, calendar integration |

---

## 6. Voice System

### Text-to-Speech (TTS)

| Provider | API Key | Setup | Notes |
|----------|---------|-------|-------|
| **ElevenLabs** (recommended) | `ELEVENLABS_API_KEY`, `VOICE_ID` | https://elevenlabs.io | British JARVIS voice |
| **OpenAI TTS** | `OPENAI_API_KEY` | (same as LLM) | "onyx" voice fallback |

### Speech-to-Text (STT)

| Provider | API Key | Setup | Latency |
|----------|---------|-------|---------|
| **Deepgram** (real-time) | `DEEPGRAM_API_KEY` | https://console.deepgram.com/ | <100ms |
| **OpenAI Whisper** (batch) | `OPENAI_API_KEY` | (same as LLM) | Higher accuracy |

**Audio Dependencies:**

```bash
# Linux
sudo apt-get install ffmpeg libportaudio2

# macOS
brew install ffmpeg portaudio
```

---

## 7. Vision System

| Provider | API Key | Features |
|----------|---------|----------|
| **GPT-4 Vision** | `OPENAI_API_KEY` | Image analysis, OCR |
| **Claude 3 Vision** | `ANTHROPIC_API_KEY` | Image understanding |

**Dependencies:**

```bash
pip install pillow
```

---

## 8. Code Execution Engine (PHASE 8.1)

| Language | Requirements | Features |
|----------|--------------|----------|
| **Python** | Python 3.9+ | Sandboxed execution, timeout protection |
| **JavaScript** | Node.js 18+ | Subprocess isolation |
| **Shell** | - | Whitelisted commands only |

**Security Features:**
- Import validation (blocks dangerous modules)
- Resource limits (timeout, output size)
- Security sandboxing

---

## 9. Git Operations (PHASE 8.3)

| Operation | Description |
|-----------|-------------|
| `init`, `clone` | Repository initialization |
| `add`, `commit`, `push`, `pull` | Standard workflow |
| `create_branch`, `checkout`, `delete_branch` | Branch management |
| `get_status`, `get_diff`, `get_log` | Repository inspection |

---

## 10. Universal API Client (PHASE 8.2)

| Auth Type | Config |
|-----------|--------|
| API Key | `{"type": "api_key", "key": "...", "header": "X-API-Key"}` |
| Bearer Token | `{"type": "bearer", "token": "..."}` |
| Basic Auth | `{"type": "basic", "username": "...", "password": "..."}` |
| OAuth 2.0 | `{"type": "oauth2", "access_token": "..."}` |
| JWT | `{"type": "jwt", "token": "..."}` |

**Features:**
- Connection pooling
- Exponential backoff retry
- Rate limiting
- Automatic JSON handling

---

## 11. External Integrations

### Gmail Add-on

- **Location:** `tools/gmail-addon/`
- **Setup:** Deploy to Google Apps Script
- **Features:** Email summarization, quick replies, AI drafting

### Outlook Add-in

- **Location:** `tools/outlook-addin/`
- **Setup:** Sideload or publish to Microsoft 365
- **Features:** Email summary, compose assistance, taskpane UI

**Deployment:**

```bash
cd tools/
./deploy.sh https://your-jarvis-domain.com
```

---

## 12. Core Platform Features

| Feature | Description |
|---------|-------------|
| **Council System** | Weighted voting for multi-agent decisions |
| **Flow Engine** | Visual workflow execution |
| **Memory System** | Short-term, long-term, entity memory (ChromaDB) |
| **Agents Dashboard** | Real-time AI agent monitoring |

---

## 13. Database Support

| Database | Config | Dependencies |
|----------|--------|--------------|
| **SQLite** (default) | `sqlite:///data/jarvis.db` | Built-in |
| **PostgreSQL** | `postgresql://user:pass@host:5432/db` | `pip install asyncpg` |
| **MySQL** | `mysql://...` | `pip install aiomysql` |

---

## Quick Setup Checklist

### Minimum Required (LLM only)

```env
ANTHROPIC_API_KEY=sk-ant-...   # OR
OPENAI_API_KEY=sk-...
```

### Full Featured

```env
# LLM
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...

# Voice
ELEVENLABS_API_KEY=...
VOICE_ID=...
DEEPGRAM_API_KEY=...

# Actions
NAMECHEAP_API_KEY=...
NAMECHEAP_API_USER=...
VERCEL_TOKEN=...
GITHUB_TOKEN=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
STRIPE_API_KEY=sk_test_...

# Meetings
ZOOM_API_KEY=...
ZOOM_API_SECRET=...
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
```

---

## Related Documentation

- [INSTALLATION.md](./INSTALLATION.md) - Installation guide
- [JARVIS_2_0_CONFIGURATION_GUIDE.md](./JARVIS_2_0_CONFIGURATION_GUIDE.md) - Configuration options
- [DEPLOYMENT_GUIDE.md](../tools/DEPLOYMENT_GUIDE.md) - External tools deployment
- [DEMO_GUIDE.md](./DEMO_GUIDE.md) - Demo walkthrough

---

*Document Version: 1.0 | Last Updated: 2025-11-25*
