# Fantasy Football Agent - Project Summary

## Overview

This project implements an AI-powered Fantasy Football team management agent using Google ADK (Agent Development Kit). The agent can optimize lineups, manage waiver wire pickups, evaluate trades, and make informed decisions using LLM reasoning and real-time web data.

## Architecture

### Core Components

1. **Main Agent** (`app/agent.py`)
   - FantasyFootballAgent class extending Google ADK Agent
   - Coordinates all tools and decision-making
   - Provides high-level management functions

2. **FastAPI Server** (`app/server.py`)
   - REST API endpoints for agent functionality
   - Exposes lineup optimization, waiver wire, trades, etc.
   - Can be run independently or alongside ADK web interface

3. **Yahoo Fantasy Tools** (`app/utils/tools/yahoo_tools.py`)
   - Compatibility wrapper for Yahoo Fantasy MCP Server
   - Maps agent functions to MCP server tools
   - Actual data access handled by Yahoo Fantasy MCP Server

4. **Browser Automation Tools** (`app/utils/tools/browser_tools.py`)
   - Compatibility wrapper for Browser MCP
   - Maps agent functions to Browser MCP tools
   - Actual browser control handled by Browser MCP (Chrome extension)

5. **Analysis Tools** (`app/utils/tools/analysis_tools.py`)
   - LLM-powered decision making using Google Gemini
   - Analyzes data and makes recommendations
   - Considers league rules, matchups, player research

6. **Configuration** (`app/utils/config.py`)
   - Settings management using pydantic-settings
   - Loads from environment variables and .env file

5. **MCP Servers** (External)
   - **Yahoo Fantasy MCP Server**: https://github.com/derekrbreese/fantasy-football-mcp-public
     - Provides comprehensive Yahoo Fantasy Football API access
     - Advanced lineup optimization, waiver wire analysis, draft assistance
   - **Browser MCP**: https://browsermcp.io/
     - Browser automation using Chrome extension
     - Uses existing browser profile (stays logged in)

### Data Flow

```
User Request
    ↓
FantasyFootballAgent (Google ADK)
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ Yahoo Tools     │ Browser Tools   │ Analysis Tools  │
│ (MCP Wrapper)   │ (MCP Wrapper)  │ (LLM Reasoning) │
└─────────────────┴─────────────────┴─────────────────┘
    ↓                   ↓                   ↓
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│ Yahoo Fantasy │  │ Browser MCP  │  │ Gemini API  │
│ MCP Server    │  │ (Extension)  │  │             │
└───────────────┘  └──────────────┘  └──────────────┘
    ↓                   ↓                   ↓
Yahoo API         Chrome Browser      LLM Analysis
    ↓                   ↓                   ↓
League Data    →  Web Actions  →  Decision Making
    ↓                   ↓                   ↓
    └───────────────────┴───────────────────┘
                    ↓
            Execute Actions via Browser MCP
```

## Key Features

### 1. Lineup Optimization
- Analyzes matchups, player performance, injuries
- Considers weather conditions and team news
- Respects league-specific scoring rules
- Makes recommendations with reasoning

### 2. Waiver Wire Management
- Scans available players
- Evaluates potential value
- Considers team needs and bye weeks
- Executes pickups when beneficial

### 3. Trade Evaluation
- Evaluates pending trade offers
- Proposes new trades when beneficial
- Analyzes long-term implications
- Considers team needs and player values

### 4. Web Research Integration
- Automatically searches for player news
- Fetches latest injury reports
- Gets current statistics and trends
- Consults expert analysis

## Technology Stack

- **Google ADK**: Agent framework and orchestration
- **Google Gemini**: LLM for decision-making
- **Yahoo Fantasy MCP Server**: Yahoo Fantasy Football API access (external repository)
- **Browser MCP**: Browser automation via Chrome extension (https://browsermcp.io/)
- **MCP**: Model Context Protocol for tool integration
- **Python 3.9+**: Programming language

## Project Structure

```
football-agent/
├── agent.py                      # Main agent definition
├── main.py                       # Entry point
├── config.py                     # Configuration management
├── example_usage.py              # Example usage scripts
├── requirements.txt              # Python dependencies
├── setup.sh                      # Setup script
├── mcp_config.json               # MCP server configuration
├── adk_config.yaml               # ADK configuration
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore rules
├── README.md                     # Main documentation
├── QUICKSTART.md                 # Quick start guide
├── SETUP_NOTES.md                # Detailed setup instructions
├── PROJECT_SUMMARY.md            # This file
├── tools/
│   ├── __init__.py
│   ├── yahoo_tools.py           # Yahoo MCP wrapper
│   ├── browser_tools.py         # Browser MCP wrapper
│   └── analysis_tools.py        # LLM analysis
├── fantasy-football-mcp-public/ # Yahoo Fantasy MCP Server (cloned)
│   └── (external repository)
└── mcp_config.json              # MCP server configuration
```

## Setup Requirements

1. **Python Environment**: Python 3.9+
2. **API Keys**: 
   - Google Gemini API key
   - Yahoo Developer credentials (Consumer Key/Secret)
3. **Browser**: Chrome with Browser MCP extension installed
4. **Node.js**: For Browser MCP server (runs via npx)
5. **Yahoo Account**: For browser automation (logged into Chrome)
6. **Git**: For cloning Yahoo Fantasy MCP Server repository

## Usage Modes

### 1. ADK Web Interface (Recommended)
```bash
adk web
```
Interactive web interface for agent interaction and monitoring.

### 2. Direct Python Usage
```python
from agent import agent
import asyncio

result = asyncio.run(agent.optimize_lineup(week=5))
```

### 3. Example Scripts
```bash
python example_usage.py
```

## Configuration

All configuration is done via environment variables in `.env`:

- `GEMINI_API_KEY`: Google Gemini API key
- `YAHOO_CONSUMER_KEY`: Yahoo API consumer key
- `YAHOO_CONSUMER_SECRET`: Yahoo API consumer secret
- `YAHOO_LEAGUE_ID`: Your fantasy league ID
- `YAHOO_ACCESS_TOKEN`: OAuth access token (from Yahoo Fantasy MCP Server setup)
- `YAHOO_REFRESH_TOKEN`: OAuth refresh token (from Yahoo Fantasy MCP Server setup)
- `YAHOO_GUID`: Yahoo GUID (from Yahoo Fantasy MCP Server setup)
- `YAHOO_EMAIL`: Yahoo account email (optional, for reference)
- `YAHOO_PASSWORD`: Yahoo account password (optional, Browser MCP uses your Chrome session)

## Security Considerations

- ⚠️ Never commit `.env` file
- ⚠️ Store credentials securely
- ⚠️ Review agent actions before automatic execution
- ⚠️ Browser automation requires account credentials
- ⚠️ OAuth tokens expire and need refresh

## Limitations

1. **Yahoo API is Read-Only**: All changes must go through browser automation (Browser MCP)
2. **Browser MCP Dependency**: Requires Chrome extension and logged-in session
3. **Browser Automation Fragility**: Website changes can break automation
4. **OAuth Token Expiration**: Tokens need periodic refresh (Yahoo Fantasy MCP Server handles this)
5. **Rate Limiting**: API and browser automation have rate limits
6. **MCP Server Dependencies**: External MCP servers must be properly configured

## Future Enhancements

Potential improvements:
- [ ] Add more sophisticated player projection models
- [ ] Implement trade negotiation logic
- [ ] Add support for multiple leagues
- [ ] Create web dashboard for monitoring
- [ ] Add notification system for important events
- [ ] Implement historical performance tracking
- [ ] Add support for other fantasy platforms

## Testing

Test individual components:
1. Yahoo Fantasy MCP Server connection
2. Browser MCP extension and automation
3. Gemini API access
4. Agent functions

See `SETUP_NOTES.md` for testing instructions. Use `python verify_setup.py` to check your setup.

## Documentation

- **README.md**: Complete project documentation
- **QUICKSTART.md**: Quick setup guide
- **SETUP_NOTES.md**: Detailed setup and troubleshooting
- **PROJECT_SUMMARY.md**: This file - architecture overview

## Support and Resources

- Google ADK: https://google.github.io/adk-docs/
- Yahoo Fantasy MCP Server: https://github.com/derekrbreese/fantasy-football-mcp-public
- Browser MCP: https://browsermcp.io/ and https://docs.browsermcp.io/
- MCP Protocol: https://modelcontextprotocol.io/
- Requirements: See `REQUIREMENTS.md` for dependency details

## License

MIT License - feel free to use and modify for your own fantasy football management.

---

**Built with ❤️ for Fantasy Football enthusiasts**

