# Update Notes - MCP-Based Architecture

## Changes Made

This project now uses **MCP (Model Context Protocol) servers** for all external integrations:

1. **[Yahoo Fantasy Football MCP Server](https://github.com/derekrbreese/fantasy-football-mcp-public)** - For Yahoo Fantasy API access
2. **[Browser MCP](https://browsermcp.io/)** - For browser automation

### What Changed

1. **MCP Configuration** (`mcp_config.json`)
   - Configured Yahoo Fantasy MCP Server (external repository)
   - Configured Browser MCP Server (via npx)
   - Added OAuth token environment variables

2. **Setup Script** (`setup.sh`)
   - Automatically clones the Yahoo Fantasy MCP Server repository
   - Installs dependencies for agent and Yahoo Fantasy MCP Server
   - Removed ChromeDriver installation (not needed with Browser MCP)

3. **Yahoo Tools** (`tools/yahoo_tools.py`)
   - Refactored to be a compatibility wrapper
   - Documents which MCP tools are used for each function
   - Actual implementation handled by Yahoo Fantasy MCP Server

4. **Browser Tools** (`tools/browser_tools.py`)
   - Completely refactored to use Browser MCP instead of Selenium
   - Removed all Selenium/ChromeDriver code
   - Uses Browser MCP Chrome extension for automation

5. **Requirements** (`requirements.txt`)
   - Minimized to only core agent dependencies
   - Removed Selenium, Playwright, yahoofantasy (handled by MCP servers)
   - Added clear documentation about MCP server dependencies

6. **Configuration** (`config.py`)
   - Added OAuth token fields (YAHOO_ACCESS_TOKEN, YAHOO_REFRESH_TOKEN, YAHOO_GUID)

7. **Documentation**
   - Updated all documentation files to reflect MCP architecture
   - Created MCP_SERVER_INFO.md for Yahoo Fantasy MCP Server details
   - Created BROWSER_MCP_INFO.md for Browser MCP details
   - Created REQUIREMENTS.md explaining dependency structure
   - Updated QUICKSTART.md, SETUP_NOTES.md, PROJECT_SUMMARY.md

### Benefits

**Yahoo Fantasy MCP Server:**
- **More Features**: Advanced lineup optimization, draft assistance, sentiment analysis, and more
- **Better Maintained**: Active development and maintenance by the community
- **Proven**: Used by many users, well-tested
- **Rich Toolset**: 20+ tools available vs. basic read-only access

**Browser MCP:**
- **No ChromeDriver**: Uses Chrome extension, no driver management needed
- **Stays Logged In**: Uses your existing browser profile
- **Fast**: Local automation, no network latency
- **Private**: All automation stays on your device
- **Stealth**: Uses real browser fingerprint, avoids detection

### Migration Notes

If you had a previous setup:

1. **Run `./setup.sh` again** to clone the Yahoo Fantasy MCP Server
2. **Install Browser MCP Chrome extension**: https://browsermcp.io/
3. **Set up Yahoo OAuth** using the MCP server's scripts (see QUICKSTART.md)
4. **Add OAuth tokens** to your `.env` file (YAHOO_ACCESS_TOKEN, YAHOO_REFRESH_TOKEN, YAHOO_GUID)
5. **Make sure you're logged into Yahoo Fantasy Football in Chrome** (Browser MCP uses your session)
6. **Remove Selenium/ChromeDriver** if you had it installed (no longer needed)
7. The agent will automatically use the new MCP servers

### Available MCP Tools

See `MCP_SERVER_INFO.md` for a complete list of available tools. Key tools include:

- `ff_build_lineup` - Advanced lineup optimization
- `ff_get_waiver_wire` - Smart waiver wire analysis
- `ff_get_matchup` - Detailed matchup analysis
- `ff_analyze_reddit_sentiment` - Social media sentiment
- And many more...

The agent's `YahooFantasyTools` class maps to these MCP tools for compatibility.

