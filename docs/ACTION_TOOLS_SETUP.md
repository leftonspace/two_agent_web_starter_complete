# Action Execution Tools Setup Guide

**PHASE 7.4: Real-World Action Execution**

This guide covers setup and usage of action tools that interact with external services to perform real-world actions like purchasing domains, deploying websites, sending SMS, and processing payments.

## Table of Contents

- [Overview](#overview)
- [Security & Approvals](#security--approvals)
- [Tool Setup](#tool-setup)
  - [Domain Purchase (Namecheap)](#1-domain-purchase-namecheap)
  - [Website Deployment (Vercel)](#2-website-deployment-vercel)
  - [SMS (Twilio)](#3-sms-twilio)
  - [Payments (Stripe)](#4-payments-stripe)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## Overview

Action tools extend System-1.2 with the ability to execute real-world actions:

- **buy_domain**: Purchase domains via Namecheap
- **deploy_website**: Deploy to Vercel (GitHub + Vercel)
- **send_sms**: Send SMS messages via Twilio
- **make_payment**: Process payments via Stripe

### Key Features

✓ **Approval Workflows**: Paid or risky actions require user approval
✓ **Cost Estimation**: Know the cost before execution
✓ **Rollback Support**: Undo actions when possible (refunds, deletions)
✓ **Audit Logging**: Complete trail of all action attempts
✓ **Risk Assessment**: LOW/MEDIUM/HIGH/CRITICAL risk levels
✓ **Dry Run Mode**: Test without actually executing

## Security & Approvals

### Risk Levels

| Risk Level | Cost Range | Requires Approval | Requires 2FA |
|------------|------------|-------------------|--------------|
| LOW        | < $1       | No                | No           |
| MEDIUM     | $1 - $10   | Yes               | No           |
| HIGH       | $10 - $100 | Yes               | No           |
| CRITICAL   | > $100     | Yes               | Yes          |

### Approval Workflow

1. Agent estimates cost
2. Agent assesses risk level
3. If approval needed:
   - Agent sends approval request via message bus
   - User has 5 minutes to respond (yes/no)
   - Action proceeds only if approved
4. Action executes
5. Audit log created

**Example Approval Message:**

```
⚠️ Action Approval Required

Action: buy_domain
Description: Purchase domain 'example.com' for 1 year(s)
Cost: $12.98
Risk Level: MEDIUM

Details:
  domain: example.com
  years: 1

Approve this action? [yes/no]
```

## Tool Setup

### 1. Domain Purchase (Namecheap)

**Step 1: Enable API Access**

1. Log in to Namecheap: https://www.namecheap.com
2. Navigate to Profile → Tools → API Access
3. Enable API Access (requires account approval)
4. Whitelist your server IP address

**Step 2: Get API Credentials**

```bash
# API Key: Found in Profile → Tools → API Access
# Username: Your Namecheap username
```

**Step 3: Set Environment Variables**

```bash
export NAMECHEAP_API_KEY="your_api_key_here"
export NAMECHEAP_API_USER="your_username"
export NAMECHEAP_CLIENT_IP="your_whitelisted_ip"
```

**Step 4: Test in Sandbox**

```python
# Use sandbox mode for testing
params = {
    "domain": "example.com",
    "years": 1,
    "sandbox": True  # Uses sandbox API
}
```

**Resources:**

- API Docs: https://www.namecheap.com/support/api/intro/
- Sandbox: https://www.sandbox.namecheap.com/

---

### 2. Website Deployment (Vercel)

**Step 1: Create Vercel Account**

1. Sign up: https://vercel.com/signup
2. Install Vercel CLI (optional): `npm install -g vercel`

**Step 2: Get API Token**

1. Go to: https://vercel.com/account/tokens
2. Create new token
3. Copy token value

**Step 3: Create GitHub Personal Access Token**

1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Permissions needed:
   - `repo` (full repository access)
   - `workflow` (if using GitHub Actions)

**Step 4: Set Environment Variables**

```bash
export VERCEL_TOKEN="your_vercel_token"
export GITHUB_TOKEN="your_github_token"
```

**Step 5: Configure Git**

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

**Resources:**

- Vercel API: https://vercel.com/docs/rest-api
- GitHub Tokens: https://docs.github.com/en/authentication

---

### 3. SMS (Twilio)

**Step 1: Create Twilio Account**

1. Sign up: https://www.twilio.com/try-twilio
2. Get free trial credits ($15)

**Step 2: Get Phone Number**

1. Go to Phone Numbers → Buy a Number
2. Select a number with SMS capability
3. Purchase number (~$1/month)

**Step 3: Get API Credentials**

1. Go to Console Dashboard
2. Copy Account SID
3. Copy Auth Token

**Step 4: Set Environment Variables**

```bash
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_PHONE_NUMBER="+12345678900"  # Your Twilio number
```

**Step 5: Test SMS**

```python
params = {
    "to": "+14155552671",  # Recipient (E.164 format)
    "message": "Hello from System-1.2!"
}
```

**Cost:**

- US/Canada SMS: ~$0.0079 per message
- International: Varies by country
- Cost calculator: https://www.twilio.com/sms/pricing

**Resources:**

- Twilio Console: https://console.twilio.com/
- API Docs: https://www.twilio.com/docs/usage/api

---

### 4. Payments (Stripe)

⚠️ **CRITICAL**: Payments always require approval, even for small amounts.

**Step 1: Create Stripe Account**

1. Sign up: https://dashboard.stripe.com/register
2. Verify business information

**Step 2: Get API Keys**

1. Go to Developers → API Keys
2. Copy Secret Key (starts with `sk_`)
3. Use Test Mode keys for development

**Step 3: Set Environment Variable**

```bash
# Test mode (recommended for development)
export STRIPE_API_KEY="sk_test_..."

# Live mode (production only)
export STRIPE_API_KEY="sk_live_..."
```

**Step 4: Create Payment Method**

```python
# First create a payment method in Stripe Dashboard or via API
# Then use the payment_method_id in tool calls
```

**Step 5: Test Payment**

```python
params = {
    "amount": 10.00,  # USD
    "payment_method_id": "pm_1234567890",
    "description": "Test payment",
    "customer_id": "cus_abc123"  # Optional
}
```

**Rollback:**

- Payments can be refunded via rollback()
- Refunds typically process in 5-10 days
- Stripe charges are not refunded (2.9% + $0.30)

**Resources:**

- Stripe Dashboard: https://dashboard.stripe.com/
- API Docs: https://stripe.com/docs/api
- Testing: https://stripe.com/docs/testing

## Configuration

### Environment Variables

Create a `.env` file (never commit this!):

```bash
# Namecheap
NAMECHEAP_API_KEY=your_key
NAMECHEAP_API_USER=your_username
NAMECHEAP_CLIENT_IP=your_ip

# Vercel & GitHub
VERCEL_TOKEN=your_token
GITHUB_TOKEN=your_github_token

# Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+12345678900

# Stripe
STRIPE_API_KEY=sk_test_your_key
```

### agent/config.py

Customize action tool behavior:

```python
@dataclass
class ActionToolsConfig:
    # Approval settings
    require_approval_for_paid_actions: bool = True
    require_2fa_above_usd: float = 100.0
    approval_timeout_seconds: int = 300

    # Cost limits
    daily_spending_limit_usd: float = 500.0
    per_action_limit_usd: float = 200.0

    # Rollback
    auto_rollback_on_failure: bool = True
    rollback_timeout_seconds: int = 60

    # Sandbox mode
    use_sandbox_apis: bool = False

    # Audit logging
    log_all_action_attempts: bool = True
    log_approval_decisions: bool = True
```

## Usage Examples

### Example 1: Buy Domain

```python
from agent.tools.actions.buy_domain import BuyDomainTool
from agent.tools.base import ToolExecutionContext
from pathlib import Path

tool = BuyDomainTool()
context = ToolExecutionContext(
    mission_id="mission_123",
    project_path=Path("/project"),
    permissions=["domain_purchase"],
    user_id="user_456"
)

# Execute (will prompt for approval)
result = await tool.execute(
    {
        "domain": "example.com",
        "years": 1,
        "nameservers": ["ns1.example.com", "ns2.example.com"]  # Optional
    },
    context
)

if result.success:
    print(f"Domain purchased: {result.data['domain']}")
    print(f"Cost: ${result.data['cost']}")
    print(f"Expires: {result.data['expires_at']}")
    print(f"Execution ID: {result.metadata['execution_id']}")
else:
    print(f"Failed: {result.error}")
```

### Example 2: Deploy Website

```python
from agent.tools.actions.deploy_website import DeployWebsiteTool

tool = DeployWebsiteTool()

result = await tool.execute(
    {
        "project_path": "/output/my-website",
        "custom_domain": "example.com",
        "framework": "nextjs",
        "env_vars": {
            "API_KEY": "secret123",
            "NODE_ENV": "production"
        }
    },
    context
)

if result.success:
    print(f"Deployed to: {result.data['url']}")
    print(f"GitHub repo: {result.data['github_repo']}")

    # Rollback if needed
    # success = await tool.rollback(result.metadata['execution_id'], context)
```

### Example 3: Send SMS

```python
from agent.tools.actions.send_sms import SendSMSTool

tool = SendSMSTool()

result = await tool.execute(
    {
        "to": "+14155552671",
        "message": "Your verification code is 123456"
    },
    context
)

if result.success:
    print(f"SMS sent: {result.data['message_sid']}")
    print(f"Cost: ${result.data['cost']}")
```

### Example 4: Process Payment

```python
from agent.tools.actions.make_payment import MakePaymentTool

tool = MakePaymentTool()

# Requires approval (HIGH risk for $50)
result = await tool.execute(
    {
        "amount": 50.00,
        "payment_method_id": "pm_1234567890",
        "description": "Invoice #12345",
        "metadata": {
            "invoice_id": "12345",
            "customer_email": "customer@example.com"
        }
    },
    context
)

if result.success:
    print(f"Payment succeeded: {result.data['payment_intent_id']}")

    # Refund if needed
    # success = await tool.rollback(result.metadata['execution_id'], context)
```

### Example 5: Dry Run

```python
# Test without actually executing
context.dry_run = True

result = await tool.execute(params, context)

print(f"Simulated: {result.data['simulated']}")
print(f"Estimated cost: ${result.data['estimated_cost']}")
print(f"Would require approval: {result.metadata['would_require_approval']}")
```

## Troubleshooting

### Domain Purchase Issues

**Error: "Domain not available"**
- Domain is already registered
- Try alternative domain names
- Check typos in domain name

**Error: "Namecheap API credentials not configured"**
- Set `NAMECHEAP_API_KEY` and `NAMECHEAP_API_USER`
- Verify API access is enabled in Namecheap account
- Check IP is whitelisted

**Error: "API error: Invalid IP"**
- Your IP is not whitelisted
- Set `NAMECHEAP_CLIENT_IP` or update whitelist

### Deployment Issues

**Error: "GitHub push failed"**
- Check `GITHUB_TOKEN` has `repo` permission
- Verify git is configured (`git config --global user.email`)
- Check repository doesn't already exist with same name

**Error: "Vercel deployment failed"**
- Verify `VERCEL_TOKEN` is valid
- Check project framework detection
- Review Vercel build logs in dashboard

**Error: "Path is outside project directory"**
- Deployment path must be within project root
- Use absolute paths or relative to `context.project_path`

### SMS Issues

**Error: "Twilio credentials not configured"**
- Set all three variables: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- Verify credentials in Twilio console

**Error: "Invalid phone number"**
- Use E.164 format: `+[country][number]`
- Example: `+14155552671` (not `415-555-2671`)

**Error: "Account not authorized"**
- Trial accounts can only send to verified numbers
- Verify number in Twilio console: https://console.twilio.com/us1/develop/phone-numbers/manage/verified

### Payment Issues

**Error: "Payment failed: card declined"**
- Check payment method is valid
- Verify sufficient funds
- Check with card issuer

**Error: "Stripe API key not configured"**
- Set `STRIPE_API_KEY`
- Use test key (`sk_test_...`) for development
- Use live key (`sk_live_...`) for production

**Error: "Cannot rollback payment"**
- Payment succeeded, but refund failed
- Check Stripe dashboard manually
- Refunds can take 5-10 days to process

### General Issues

**Error: "requests library not installed"**
```bash
pip install requests
```

**Error: "Action declined by user"**
- User declined approval request
- Check approval timeout (default: 5 minutes)
- Verify approval message was delivered

**Error: "Cost exceeds limit"**
- Increase `max_cost_usd` in context
- Increase `per_action_limit_usd` in config
- Split into multiple smaller actions

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for all API keys
3. **Enable 2FA** for critical actions (>$100)
4. **Review audit logs** regularly
5. **Use test/sandbox APIs** during development
6. **Set cost limits** appropriate for your use case
7. **Require approvals** for all paid actions
8. **Monitor spending** via service dashboards

## Cost Monitoring

### Daily Spending Limits

```python
# In agent/config.py
action_tools = ActionToolsConfig(
    daily_spending_limit_usd=500.0,  # Max $500/day
    per_action_limit_usd=200.0       # Max $200/action
)
```

### Audit Logs

All action attempts are logged:

```python
# View logs
grep "action_executed" logs/core_events.log

# View approvals
grep "approval_response_received" logs/core_events.log

# View costs
grep "cost" logs/core_events.log | grep "action_executed"
```

### Service Dashboards

- **Namecheap**: https://ap.www.namecheap.com/domains/list/
- **Vercel**: https://vercel.com/dashboard
- **Twilio**: https://console.twilio.com/us1/billing
- **Stripe**: https://dashboard.stripe.com/balance

## Next Steps

1. Set up one service at a time
2. Test with dry-run mode first
3. Use sandbox/test APIs for development
4. Enable approval workflows
5. Monitor costs and audit logs
6. Integrate with conversational agent

## Support

- **Documentation**: docs/ACTION_TOOLS_SETUP.md
- **API References**: See service-specific docs linked above
- **Issues**: https://github.com/your-repo/issues
