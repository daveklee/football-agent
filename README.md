# Fantasy Football Agent

An AI-powered agent built with Google ADK (Agent Development Kit) that manages your Yahoo Fantasy Football team. The agent uses LLM reasoning to optimize lineups, evaluate trades, manage waiver wire pickups, and make informed decisions based on current player data and news.

## 🎯 Current Use

This agent is **actively managing** a Yahoo Fantasy Football team in the 2025 season. You can follow along with the journey, see real-world results, and learn about the challenges and successes of AI-powered fantasy football management on **[Dave's Stupid Robot](https://davesstupidrobot.substack.com/)** - a Substack documenting the experience of letting an AI agent manage a fantasy football team.

The Substack covers:
- Real game results and team performance
- Agent decision-making processes and reasoning
- Challenges encountered and how they were solved
- Insights into agentic AI development
- Lessons learned from hands-on AI team management

This Google ADK approach is actually version 3 of the football agent, but you can read more about it on the blog.

## Features

- 🤖 **AI-Powered Decision Making**: Uses Google Gemini to analyze matchups, player performance, and make strategic decisions
- 📊 **Yahoo Fantasy Integration**: Reads team data, league settings, and player stats via Yahoo Fantasy Football API
- 🌐 **Web Research**: Automatically searches the internet for latest player news, injury reports, and statistics
- 🖥️ **Browser Automation**: Makes actual changes to your team via automated browser control (since Yahoo's API is read-only)
- 🔄 **MCP Server Integration**: Uses Model Context Protocol servers for Yahoo Fantasy data and browser control
- 📈 **Comprehensive Management**: 
  - Optimize weekly lineups
  - Evaluate and execute waiver wire pickups
  - Analyze and propose trades
  - Monitor team performance
  - Consider league-specific scoring and rules

## Prerequisites

- Python 3.9 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Yahoo Fantasy Football account
- Yahoo Developer API credentials ([Register here](https://developer.yahoo.com/api/))
- Chrome browser (for Browser MCP extension)
- Node.js (for browsermcp MCP server)
- Git (for cloning the Yahoo Fantasy MCP Server)

## Setup

### 1. Clone and Navigate

```bash
cd /Users/daveklee/Documents/github/football-agent
```

### 2. Run Setup Script

```bash
./scripts/setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create a `.env` file template

### 3. Configure Environment Variables

Edit the `.env` file with your credentials:

```bash
# Google Gemini API
GEMINI_API_KEY=your_actual_gemini_api_key

# Yahoo Fantasy Football API Credentials
# Get these from https://developer.yahoo.com/api/
YAHOO_CONSUMER_KEY=your_yahoo_consumer_key
YAHOO_CONSUMER_SECRET=your_yahoo_consumer_secret
YAHOO_LEAGUE_ID=your_league_id  # Found in your Yahoo Fantasy URL
YAHOO_GAME_ID=449  # NFL game ID

# Yahoo Account Credentials (for browser automation)
YAHOO_EMAIL=your_yahoo_email@example.com
YAHOO_PASSWORD=your_yahoo_password

# ADK Configuration
ADK_PROJECT_ID=football-agent
ADK_REGION=us-central1
```

### 4. Install Browser MCP Chrome Extension

This project uses Browser MCP for browser automation, which requires the Chrome extension:

1. Go to https://browsermcp.io/
2. Click "Add to Chrome" to install the Browser MCP extension
3. The extension enables AI apps to control your browser

**Note**: Browser MCP uses your existing browser profile, so make sure you're logged into Yahoo Fantasy Football in Chrome. No ChromeDriver installation needed!

### 5. Set Up Yahoo OAuth

The Yahoo Fantasy API requires OAuth authentication. The setup script clones the [Yahoo Fantasy Football MCP Server](https://github.com/derekrbreese/fantasy-football-mcp-public) which includes OAuth setup scripts.

1. Register your application at [Yahoo Developer Network](https://developer.yahoo.com/api/)
2. Set up OAuth callback URL (can be `http://localhost:8080/callback` for local development)
3. Complete the OAuth flow using the MCP server's setup script:

```bash
cd fantasy-football-mcp-public
python setup_yahoo_auth.py
# Or for re-authentication:
python reauth_yahoo.py
```

This will generate the `YAHOO_ACCESS_TOKEN`, `YAHOO_REFRESH_TOKEN`, and `YAHOO_GUID` needed for the MCP server. Add these to your `.env` file.

### 6. Install Browser MCP Extension

This project uses [Browser MCP](https://browsermcp.io/) for browser automation. Browser MCP uses your existing Chrome browser profile, so you stay logged in to Yahoo Fantasy Football.

**Install the Browser MCP Chrome Extension:**
1. Go to https://browsermcp.io/
2. Click "Add to Chrome" to install the extension
3. The extension enables AI apps to control your browser

**Benefits of Browser MCP:**
- ✅ Uses your existing browser profile (stays logged in)
- ✅ Fast - automation happens locally
- ✅ Private - browser activity stays on your device
- ✅ Stealth - avoids basic bot detection
- ✅ No ChromeDriver needed

The Browser MCP server is already configured in `mcp_config.json` and will be used automatically by the agent.

## Usage

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Run the Agent

#### Option 1: Using ADK Web Interface (Recommended)

```bash
# Use the helper script (recommended)
./scripts/start_adk_web.sh

# Or manually specify port
adk web --port 8080
```

This will start the ADK development web interface where you can:
- Interact with the agent
- Monitor agent actions
- View logs and traces
- Test individual tools

Access the interface at `http://localhost:8080` (default port, configurable via `ADK_WEB_PORT`).

**Port Configuration**:
- **ADK Web Server**: Port 8080 (configurable via `ADK_WEB_PORT` env var)
- **MCP Servers**: Use stdio transport (no ports needed - standard MCP protocol)
- **Optional HTTP MCP**: Yahoo Fantasy on 8001, Browser MCP on 8002 (only if HTTP transport needed)

See `docs/PORT_CONFIGURATION.md` for complete port configuration details.

#### Option 2: Run FastAPI Server

```bash
make run-server
# or
python -m app.server
```

This starts a FastAPI REST API server with endpoints for:
- `/api/optimize-lineup` - Optimize lineup for a week
- `/api/evaluate-waiver-wire` - Evaluate waiver wire pickups
- `/api/evaluate-trades` - Evaluate pending trades
- `/api/weekly-management` - Run all weekly management tasks
- `/api/team-data` - Get current team data

#### Option 3: Run Directly

```bash
python main.py
```

Or use the Makefile:

```bash
make run          # Run agent directly
make run-web      # Start ADK web interface
make run-server   # Start FastAPI server
```

### Using the Agent

The agent provides several management functions:

#### Optimize Lineup

```python
from agent import agent
import asyncio

result = asyncio.run(agent.optimize_lineup(week=5))
print(result)
```

#### Evaluate Waiver Wire

```python
result = asyncio.run(agent.evaluate_waiver_wire())
print(result)
```

#### Evaluate Trades

```python
result = asyncio.run(agent.evaluate_trades())
print(result)
```

#### Run Full Weekly Management

```python
result = asyncio.run(agent.run_weekly_management())
print(result)
```

## Project Structure

```
football-agent/
├── app/                     # Main application code
│   ├── agent.py            # Main agent definition
│   ├── server.py           # FastAPI server
│   └── utils/              # Utility modules
│       ├── config.py       # Configuration management
│       └── tools/          # Tool implementations
├── scripts/                # Setup and utility scripts
│   ├── setup.sh           # Initial setup script
│   ├── start_adk_web.sh   # Start ADK web interface
│   ├── start_mcp_servers.sh # Start MCP servers (if needed)
│   └── verify_setup.py     # Verify installation
├── docs/                   # Documentation
│   ├── MCP_SERVER_INFO.md  # Yahoo Fantasy MCP Server info
│   ├── BROWSER_MCP_INFO.md # Browser MCP documentation
│   ├── PORT_CONFIGURATION.md # Port configuration details
│   └── TROUBLESHOOTING.md  # Troubleshooting guide
├── fantasy-football-mcp-public/  # Yahoo Fantasy MCP Server (cloned)
├── main.py                 # Entry point
├── mcp_config.json         # MCP server configuration
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## How It Works

1. **Data Collection**: The agent uses Yahoo Fantasy Football API (via MCP server) to read team data, league settings, and player information.

2. **Research**: For each decision, the agent searches the web for:
   - Latest player news and injury reports
   - Recent performance statistics
   - Matchup analysis
   - Weather conditions
   - Expert opinions

3. **Analysis**: The LLM (Gemini) analyzes all collected data considering:
   - Your league's unique scoring system
   - Roster requirements and constraints
   - Short-term and long-term implications
   - Risk vs. reward

4. **Decision Making**: The agent makes recommendations with reasoning, considering multiple factors.

5. **Execution**: When changes are needed, the agent uses Browser MCP to:
   - Navigate to Yahoo Fantasy Football pages (using your logged-in session)
   - Take snapshots to understand page structure
   - Click, type, and drag elements to make changes
   - Make lineup changes, add/drop players, or propose trades

## MCP Servers

The agent uses two MCP servers:

1. **Yahoo Fantasy Server** ([fantasy-football-mcp-public](https://github.com/derekrbreese/fantasy-football-mcp-public)): Provides comprehensive Yahoo Fantasy Football data access with advanced features:
   - Lineup optimization with multiple strategies
   - Waiver wire analysis
   - Draft assistance
   - Player research and sentiment analysis
   - League and team management
   - See the [server's README](https://github.com/derekrbreese/fantasy-football-mcp-public) for full tool list

2. **Browser MCP** ([browsermcp.io](https://browsermcp.io/)): Controls Chrome browser for making changes
   - Uses your existing browser profile (stays logged in)
   - Requires Chrome extension installation
   - Provides tools for navigation, clicking, typing, screenshots, etc.

Configure these in `mcp_config.json`. The Yahoo Fantasy MCP Server is automatically cloned during setup.

## Customization

### League-Specific Rules

The agent automatically reads your league's scoring rules and roster settings. To ensure optimal decisions:

1. Verify your league settings are correctly read
2. Adjust the agent's instruction in `agent.py` if needed
3. Modify analysis prompts in `tools/analysis_tools.py` for specific considerations

### Agent Instructions

Edit the `_get_agent_instruction()` method in `agent.py` to customize the agent's behavior and decision-making priorities.

## Troubleshooting

### Browser MCP Issues

If browser automation isn't working:
- Make sure the Browser MCP Chrome extension is installed: https://browsermcp.io/
- Verify you're logged into Yahoo Fantasy Football in Chrome
- Check that the MCP server is running (configured in `mcp_config.json`)
- Review Browser MCP documentation: https://docs.browsermcp.io/

### Yahoo API Authentication

If Yahoo API calls fail:
- Verify your Consumer Key and Secret are correct
- Complete the OAuth flow to get access tokens
- Check that your application has the necessary permissions

### MCP Server Connection

If MCP servers don't connect:
- Verify `mcp_config.json` is correctly formatted
- Check that MCP server processes are running
- Review logs for connection errors

## Security Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- Store passwords securely - consider using environment variables or a secrets manager
- The browser automation requires your Yahoo password - ensure your system is secure
- Review all agent actions before allowing automatic execution

## Limitations

- Yahoo Fantasy Football API is read-only, so all changes must be made via browser automation
- Browser MCP uses your existing browser session - make sure you're logged into Yahoo Fantasy Football
- Browser automation can be fragile if Yahoo changes their website structure
- OAuth tokens expire and need to be refreshed periodically
- The agent makes recommendations based on available data - always review before critical decisions

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License - feel free to use and modify for your own fantasy football management.

## Resources

- **[Dave's Stupid Robot](https://davesstupidrobot.substack.com/)** - Follow the journey of AI-powered fantasy football management
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Yahoo Fantasy Football MCP Server](https://github.com/derekrbreese/fantasy-football-mcp-public)
- [Browser MCP](https://browsermcp.io/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started quickly
- [MCP Server Info](docs/MCP_SERVER_INFO.md) - Yahoo Fantasy MCP Server details
- [Browser MCP Info](docs/BROWSER_MCP_INFO.md) - Browser automation setup
- [Port Configuration](docs/PORT_CONFIGURATION.md) - Port usage details
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in the console
3. Verify all credentials and configurations

---

**Happy Fantasy Football Managing! 🏈**

