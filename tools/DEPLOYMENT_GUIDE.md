# External Tools Deployment Guide

This guide covers deployment configuration for JARVIS external integrations:
- Gmail Add-on
- Outlook Add-in
- Slack Integration (future)

---

## Prerequisites

Before deploying any external tool:

1. **JARVIS Backend Running**: Ensure the JARVIS web server is accessible at your deployment URL
2. **HTTPS Required**: All external integrations require HTTPS endpoints
3. **Static Assets**: Icon files must be hosted at the configured URLs

---

## Configuration Placeholders

All configuration files use the `${JARVIS_BASE_URL}` placeholder which must be replaced with your actual deployment URL before deployment.

### Placeholder Format

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `${JARVIS_BASE_URL}` | Base URL of your JARVIS deployment | `https://jarvis.yourcompany.com` |

### Files Requiring Configuration

| File | Placeholders | Purpose |
|------|--------------|---------|
| `gmail-addon/appsscript.json` | 2 | Gmail add-on manifest |
| `outlook-addin/manifest.xml` | 14 | Outlook add-in manifest |

---

## Deployment Script

Use the provided deployment script to automatically replace placeholders:

```bash
# From the tools/ directory
./deploy.sh https://your-actual-domain.com
```

Or manually replace using sed:

```bash
# Replace placeholders in Gmail add-on
sed -i 's|\${JARVIS_BASE_URL}|https://jarvis.yourcompany.com|g' gmail-addon/appsscript.json

# Replace placeholders in Outlook add-in
sed -i 's|\${JARVIS_BASE_URL}|https://jarvis.yourcompany.com|g' outlook-addin/manifest.xml
```

---

## Gmail Add-on Deployment

### 1. Configure URLs

Replace `${JARVIS_BASE_URL}` in `gmail-addon/appsscript.json`:
- `logoUrl`: Icon displayed in Gmail
- `openLink.url`: Help documentation URL

### 2. Create Google Apps Script Project

1. Go to [Google Apps Script](https://script.google.com)
2. Create new project
3. Copy contents of `gmail-addon/*.gs` files
4. Copy configured `appsscript.json` to project

### 3. Deploy as Add-on

1. Click "Deploy" → "Test deployments"
2. Select "Gmail Add-on"
3. Test with your account
4. For production: "Deploy" → "New deployment"

### Required Assets

Ensure these icon files are accessible:
- `${JARVIS_BASE_URL}/assets/icon-128.png` (128x128 PNG)

---

## Outlook Add-in Deployment

### 1. Configure URLs

Replace `${JARVIS_BASE_URL}` in `outlook-addin/manifest.xml`:

| Element | Count | Purpose |
|---------|-------|---------|
| `IconUrl` | 1 | Main icon (64x64) |
| `HighResolutionIconUrl` | 1 | High-res icon (128x128) |
| `SupportUrl` | 1 | Support page link |
| `AppDomain` | 1 | Allowed domain for security |
| `SourceLocation` (FormSettings) | 2 | Taskpane HTML pages |
| `bt:Image` | 3 | Button icons (16, 32, 80) |
| `bt:Url` | 3 | Taskpane and function URLs |

**Total: 14 placeholder instances**

### 2. Host Required Assets

Ensure these files are accessible at your domain:

```
${JARVIS_BASE_URL}/
├── assets/
│   ├── icon-16.png    (16x16)
│   ├── icon-32.png    (32x32)
│   ├── icon-64.png    (64x64)
│   ├── icon-80.png    (80x80)
│   └── icon-128.png   (128x128)
├── outlook/
│   ├── taskpane.html
│   ├── compose.html
│   └── functions.html
└── support/
    └── index.html
```

### 3. Sideload for Testing

1. Open Outlook on the web
2. Go to Settings → View all Outlook settings
3. Go to Mail → Customize actions
4. Click "Add custom add-ins" → "Add from file"
5. Upload the configured `manifest.xml`

### 4. Production Deployment

For organization-wide deployment:
1. Upload to Microsoft 365 Admin Center
2. Or publish to AppSource (public marketplace)

---

## Validation Checklist

Before deploying, verify:

- [ ] All `${JARVIS_BASE_URL}` placeholders replaced
- [ ] HTTPS certificate valid for your domain
- [ ] All icon files accessible (test each URL)
- [ ] Taskpane HTML files accessible
- [ ] CORS configured on JARVIS backend (if needed)
- [ ] OAuth credentials configured (Gmail)
- [ ] Azure AD app registered (Outlook, if using auth)

---

## Troubleshooting

### "Add-on failed to load"
- Check browser console for CORS errors
- Verify all URLs are accessible via HTTPS

### "Icon not displaying"
- Confirm icon files exist at configured paths
- Check icon dimensions match requirements

### "Authentication failed"
- Verify OAuth scopes in manifest
- Check API credentials are valid

---

## Environment-Specific Configurations

For multiple environments, create separate config files:

```
tools/
├── gmail-addon/
│   ├── appsscript.json          # Template with placeholders
│   ├── appsscript.dev.json      # Development URLs
│   ├── appsscript.staging.json  # Staging URLs
│   └── appsscript.prod.json     # Production URLs
└── outlook-addin/
    ├── manifest.xml             # Template with placeholders
    ├── manifest.dev.xml         # Development URLs
    ├── manifest.staging.xml     # Staging URLs
    └── manifest.prod.xml        # Production URLs
```

---

*Document Version: 1.0 | Last Updated: 2025-11-25*
