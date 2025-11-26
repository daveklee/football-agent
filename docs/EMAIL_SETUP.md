# Email Summary Setup

This document explains how to set up email summaries for the daily fantasy football agent runs.

## Overview
After each daily run, the agent can send a nicely formatted HTML email summarizing:
- Lineup optimizations
- Trade actions
- Waiver wire pickups
- Injury management
- Agent reasoning and decisions

## Gmail SMTP Setup

### Step 1: Enable 2-Step Verification
1. Go to your [Google Account](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification**
3. Follow the prompts to enable 2-Step Verification (required for app passwords)

### Step 2: Generate App Password
1. Still in **Security**, scroll down to **2-Step Verification**
2. Click on **App passwords** (you may need to sign in again)
3. Select **Mail** from the "Select app" dropdown
4. Select **Other (Custom name)** from the "Select device" dropdown
5. Enter "Fantasy Football Agent" or similar
6. Click **Generate**
7. Copy the 16-character password (you won't see it again)

### Step 3: Configure Environment Variables
Add the following to your `.env` file:

```bash
# Email Notifications
GMAIL_SENDER_EMAIL=your_email@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop  # 16-char app password from step 2
GMAIL_RECIPIENT_EMAIL=your_email@gmail.com  # Can be same as sender or different
```

**Important**: 
- Use the app password, not your regular Gmail password
- The app password format is 16 characters (often shown with spaces, which is fine)
- You can send to yourself or a different email address

## Testing

Run the daily setup script to test:

```bash
python scripts/run_daily_setup.py
```

Check your email inbox for the summary. The email will include:
- 🏈 Fantasy Football Daily Summary header
- Organized sections for different types of actions
- Agent reasoning and explanations
- Metadata about the run

## Troubleshooting

### "Email not configured" message
- Make sure all three environment variables are set in `.env`
- Restart your terminal session to pick up new environment variables

### "Authentication failed" error
- Verify you're using the App Password, not your regular Gmail password
- Regenerate the app password if needed
- Check that 2-Step Verification is still enabled

### Email not received
- Check your spam folder
- Verify the recipient email address is correct
- Check the logs for any error messages

## Disabling Email Summaries

Simply remove or comment out the email environment variables in `.env`:

```bash
# GMAIL_SENDER_EMAIL=your_email@gmail.com
# GMAIL_APP_PASSWORD=your_app_password
# GMAIL_RECIPIENT_EMAIL=your_email@gmail.com
```

The script will log "Email not configured - skipping email summary" and continue normally.
