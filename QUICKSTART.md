# Quick Start Guide

This guide will help you get your Fantasy Football Agent up and running quickly.

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- [ ] Yahoo Fantasy Football account
- [ ] Yahoo Developer API credentials
- [ ] Chrome browser installed
- [ ] Node.js installed (for browsermcp)

## Step-by-Step Setup

### 1. Get Yahoo Developer Credentials

1. Go to [Yahoo Developer Network](https://developer.yahoo.com/api/)
2. Sign in with your Yahoo account
3. Create a new application
4. Note down your **Consumer Key** and **Consumer Secret**
5. Set callback URL to: `http://localhost:8080/callback`

### 2. Find Your League ID

1. Go to your Yahoo Fantasy Football league
2. Look at the URL: `https://football.fantasysports.yahoo.com/f1/XXXXXX/...`
3. The number after `/f1/` is your **League ID**

### 3. Run Setup

```bash
# Make sure you're in the project directory
cd /Users/daveklee/Documents/github/football-agent

# Run the setup script
./setup.sh
```

### 4. Configure Environment

Edit the `.env` file that was created:

```bash
# Open in your editor
nano .env
# or
code .env
```

Fill in all the required values (see README.md for details).

### 5. Set Up Yahoo OAuth

The Yahoo API requires OAuth authentication. The setup script has cloned the Yahoo Fantasy MCP Server which includes OAuth setup scripts:

```bash
# Activate virtual environment
source venv/bin/activate

# Navigate to the MCP server directory
cd fantasy-football-mcp-public

# Run the OAuth setup script
python setup_yahoo_auth.py

# Or if you need to re-authenticate:
python reauth_yahoo.py
```

This will generate `YAHOO_ACCESS_TOKEN`, `YAHOO_REFRESH_TOKEN`, and `YAHOO_GUID`. Add these to your `.env` file, then return to the project root:

```bash
cd ..
```

### 6. Install Browser MCP Chrome Extension

This project uses Browser MCP for browser automation. You need to install the Chrome extension:

1. Go to https://browsermcp.io/
2. Click "Add to Chrome" to install the Browser MCP extension
3. Make sure you're logged into Yahoo Fantasy Football in Chrome (Browser MCP uses your existing session)

**Note**: Browser MCP server runs via npx (configured in `mcp_config.json`), so you don't need to install it separately. The Chrome extension is the main requirement.

### 7. Start the Agent

#### Option A: ADK Web Interface (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Start ADK web interface (uses port 8080 by default)
./start_adk_web.sh

# Or manually:
adk web --port 8080
```

Then open your browser to `http://localhost:8080`.

**Note**: The ADK web server uses port 8080 to avoid conflicts. MCP servers use stdio transport (no ports needed). See `PORT_CONFIGURATION.md` for details.

#### Option B: Run Directly

```bash
source venv/bin/activate
python main.py
```

## Testing the Agent

### Test Individual Functions

In the ADK web interface or Python REPL:

```python
from agent import agent
import asyncio

# Test getting team data
team_data = asyncio.run(agent.yahoo_tools.get_team_data())
print(team_data)

# Test lineup optimization
result = asyncio.run(agent.optimize_lineup(week=5))
print(result)
```

### Run Full Weekly Management

```python
result = asyncio.run(agent.run_weekly_management())
print(result)
```

## Common Issues

### "Browser MCP not working"

1. Make sure Browser MCP Chrome extension is installed: https://browsermcp.io/
2. Verify you're logged into Yahoo Fantasy Football in Chrome
3. Check that the extension is enabled in Chrome
4. Verify `mcp_config.json` has correct Browser MCP configuration

### "Yahoo Fantasy MCP Server not found"

1. Make sure `setup.sh` ran successfully and cloned the repository
2. Check that `fantasy-football-mcp-public/` directory exists
3. Verify dependencies were installed: `pip install -r fantasy-football-mcp-public/requirements.txt`

### "Yahoo API authentication failed"

1. Verify your Consumer Key and Secret are correct
2. Complete the OAuth flow
3. Check that your application has the right permissions

### "MCP server connection failed"

1. Verify `mcp_config.json` is correct
2. Check that MCP server processes can start
3. Review logs for errors

### "Module not found" errors

Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

Reinstall dependencies if needed:
```bash
# Agent dependencies
pip install -r requirements.txt

# Yahoo Fantasy MCP Server dependencies
pip install -r fantasy-football-mcp-public/requirements.txt
```

## Next Steps

1. **Customize Agent Instructions**: Edit `agent.py` to adjust decision-making priorities
2. **Test Browser Automation**: Verify Browser MCP extension is working and can navigate Yahoo Fantasy
3. **Review Decisions**: Always review agent recommendations before allowing automatic execution
4. **Monitor Performance**: Check logs and adjust as needed
5. **Verify MCP Servers**: Ensure both Yahoo Fantasy MCP Server and Browser MCP are connected

## Getting Help

- Check the full [README.md](README.md) for detailed documentation
- Review logs for error messages
- Verify all credentials and configurations
- Test individual components before running full agent

---

**Ready to dominate your fantasy league! 🏈**

