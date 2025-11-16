# Setup Notes and Important Information

## Google ADK Installation

The Google ADK (Agent Development Kit) may require special installation steps:

### Option 1: Install from PyPI (if available)
```bash
pip install google-adk
```

### Option 2: Install from GitHub
```bash
pip install git+https://github.com/google/adk-python.git
```

### Option 3: Manual Installation
1. Clone the repository: `git clone https://github.com/google/adk-python.git`
2. Navigate to the directory: `cd adk-python`
3. Install: `pip install -e .`

**Note**: The exact package name and installation method may vary. Check the [official ADK documentation](https://google.github.io/adk-docs/) for the most current instructions.

## Yahoo Fantasy API Setup

### Getting OAuth Credentials

1. **Register Application**:
   - Go to https://developer.yahoo.com/api/
   - Sign in with your Yahoo account
   - Click "Create an App"
   - Fill in application details
   - Set callback URL: `http://localhost:8080/callback` (for local development)

2. **Get Credentials**:
   - After creating the app, you'll receive:
     - Consumer Key (Client ID)
     - Consumer Secret (Client Secret)

3. **OAuth Flow**:
   - The `yahoofantasy` library handles OAuth, but you'll need to complete the initial authorization
   - Run the OAuth setup script (you may need to create one) or use the library's built-in methods

### Finding Your League ID

Your League ID is in the URL when you view your league:
```
https://football.fantasysports.yahoo.com/f1/XXXXXX/...
                                    ^^^^^^
                                 This is your League ID
```

## MCP Server Setup

### Yahoo Fantasy Football MCP Server

**Repository**: https://github.com/derekrbreese/fantasy-football-mcp-public

The Yahoo Fantasy MCP Server is automatically cloned during `setup.sh`. It provides comprehensive Yahoo Fantasy Football API access.

**Setup**:
1. The repository is cloned to `fantasy-football-mcp-public/`
2. Dependencies are installed via `fantasy-football-mcp-public/requirements.txt`
3. Configured in `mcp_config.json` to run via Python
4. Requires OAuth tokens (see Yahoo OAuth setup above)

**Features**:
- League and team data access
- Advanced lineup optimization
- Waiver wire analysis
- Draft assistance
- Player research and sentiment analysis

See `MCP_SERVER_INFO.md` for complete details.

### Browser MCP Server

**Website**: https://browsermcp.io/

Browser MCP provides browser automation using your existing Chrome profile.

**Setup**:
1. **Install Chrome Extension**: Go to https://browsermcp.io/ and click "Add to Chrome"
2. **Server Configuration**: Already configured in `mcp_config.json` to run via npx
3. **Login**: Make sure you're logged into Yahoo Fantasy Football in Chrome

**Benefits**:
- Uses your existing browser session (stays logged in)
- No ChromeDriver needed
- Fast local automation
- Private (stays on your device)

**Server Command**: Runs automatically via `npx -y @modelcontextprotocol/server-browser` (configured in `mcp_config.json`)

See `BROWSER_MCP_INFO.md` for complete details.

## Environment Variables

Create a `.env` file with all required variables. See `.env.example` (if created) or the README for the full list.

**Important**: Never commit your `.env` file to version control!

## Testing the Setup

### 1. Test Yahoo Fantasy MCP Server

The Yahoo Fantasy MCP Server should be accessible via MCP. Test by checking if the server starts:

```bash
cd fantasy-football-mcp-public
python fantasy_football_multi_league.py
```

Or test via the agent:
```python
from agent import agent
import asyncio

# This uses the Yahoo Fantasy MCP Server
result = asyncio.run(agent.yahoo_tools.get_team_data())
print(result)
```

### 2. Test Browser MCP

1. Make sure Browser MCP Chrome extension is installed and enabled
2. Verify you're logged into Yahoo Fantasy Football in Chrome
3. Test via the agent:
```python
from agent import agent
import asyncio

# This uses Browser MCP
result = asyncio.run(agent.browser_tools.navigate_to_yahoo_fantasy())
print(result)
```

### 3. Test Gemini API

```python
import google.generativeai as genai
genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content("Hello!")
print(response.text)
```

### 4. Test Agent

```python
from agent import agent
import asyncio

# Test getting team data
result = asyncio.run(agent.yahoo_tools.get_team_data())
print(result)
```

## Common Issues and Solutions

### Issue: "google.adk module not found"

**Solution**: 
- Check ADK installation (see above)
- Verify Python environment is activated
- Try: `pip install --upgrade google-adk`

### Issue: "Browser MCP not connecting"

**Solution**:
- Verify Browser MCP Chrome extension is installed: https://browsermcp.io/
- Check that extension is enabled in Chrome
- Make sure you're logged into Yahoo Fantasy Football in Chrome
- Verify `mcp_config.json` has correct Browser MCP configuration
- Check that Node.js/npx is available: `which npx`

### Issue: "Yahoo Fantasy MCP Server not found"

**Solution**:
- Run `setup.sh` again to clone the repository
- Check that `fantasy-football-mcp-public/` directory exists
- Install dependencies: `pip install -r fantasy-football-mcp-public/requirements.txt`
- Verify OAuth tokens are set in `.env`

### Issue: "Yahoo OAuth failed"

**Solution**:
- Verify Consumer Key and Secret are correct
- Complete the OAuth flow manually first
- Check callback URL matches your app settings

### Issue: "MCP server connection failed"

**Solution**:
- Verify `mcp_config.json` syntax is correct
- Check that MCP server processes can start
- Review server logs for errors

## Next Steps After Setup

1. **Complete OAuth Flow**: Set up Yahoo API authentication
2. **Test Individual Components**: Verify each tool works independently
3. **Run Test Examples**: Use `example_usage.py` to test agent functions
4. **Start ADK Web Interface**: Run `adk web` to use the interactive interface
5. **Customize Agent**: Adjust instructions in `agent.py` for your preferences

## Getting Help

- **ADK Documentation**: https://google.github.io/adk-docs/
- **Yahoo Fantasy MCP Server**: https://github.com/derekrbreese/fantasy-football-mcp-public
- **Browser MCP**: https://browsermcp.io/ and https://docs.browsermcp.io/
- **MCP Documentation**: https://modelcontextprotocol.io/
- **Requirements Documentation**: See `REQUIREMENTS.md` for dependency details

## Security Reminders

- ⚠️ Never commit `.env` file
- ⚠️ Store credentials securely
- ⚠️ Review agent actions before allowing automatic execution
- ⚠️ Use environment variables or secrets manager in production
- ⚠️ Keep browser automation secure (don't leave browser sessions open)

