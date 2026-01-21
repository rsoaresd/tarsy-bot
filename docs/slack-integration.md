# Slack Integration

TARSy can send automatic notifications to Slack when alert processing completes or fails. This feature is **disabled by default** and requires configuration to enable.

## Table of Contents
- [Overview](#overview)
- [How It Works](#how-it-works)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Alert Data Format](#alert-data-format)

## Overview

When enabled, TARSy automatically:
- Sends threaded replies to Slack when alerts are processed
- Includes analysis summary with link to detailed dashboard view
- Reports errors when alert processing fails
- Correlates notifications with target message via fingerprint

**Default State**: Slack integration is **disabled by default**. TARSy will process alerts normally without sending any Slack notifications until you configure it.

## How It Works

1. **Alert arrives** with a fingerprint (unique identifier)
2. **TARSy processes** the alert
3. **After processing**, TARSy searches Slack channel history (last 24 hours) for the message with the fingerprint
4. **Finds target message**, posts a threaded reply with:
   - Analysis summary or error message
   - Link to full analysis in dashboard (`<dashboard-url>/sessions/<session-id>`)

## Setup Instructions

### Step 1: Create a Slack App

1. Go to https://api.slack.com/apps
2. Create your Slack app

### Step 2: Configure Bot Permissions

In your app's **OAuth & Permissions** page, under **Bot Token Scopes**, add these scopes:

| Scope | Purpose |
|-------|---------|
| `channels:history` | Read messages in public channels (to find original alerts) |
| `groups:history` | Read messages in private channels |
| `chat:write` | Post messages and replies |
| `channels:read` | View basic channel info |
| `groups:read` | View basic private channel info |


### Step 3: Install App to Workspace

1. Under OAuth Tokens, click **"Install to Workspace"** (or **"Reinstall App"** if updating scopes)
2. Authorize the app
3. **Copy the Bot User OAuth Token** (starts with `xoxb-`)

### Step 4: Invite Bot to Channel

In your Slack channel, invite your bot: /invite @your-bot-name


### Step 5: Get Channel ID

Right-click on your channel → **"View channel details"** → Copy the Channel ID (e.g., `C12345678`)

Or find it in the channel URL: `https://your-workspace.slack.com/archives/C12345678`


## Configuration

Edit `backend/.env` and add your Slack credentials:

# =============================================================================
# Slack Notification Configuration
# =============================================================================

# Slack Bot token (starts with xoxb-)
SLACK_BOT_TOKEN=xoxb-your-token-here

# Slack channel ID (e.g., C12345678 or channel-name)
SLACK_CHANNEL=C12345678

You should also add your Dashboard URL in CORS_ORIGIN setting:

# =============================================================================
# CORS Configuration
# =============================================================================
# Allowed origins for CORS (comma-separated list)
# For development, include your alert dev UI URL
# For production, use your actual domain
CORS_ORIGINS=<your-dashboard-url>


## Alert Data Format
Alert data must include a fingerprint field. Example:

```
UserSignup: user
Cluster: rm1
Namespace: user-namespace
Fingerprint: fingerprint-123
Message: High CPU Usage
```

Without a fingerprint, alerts are processed normally but Slack notifications are skipped.