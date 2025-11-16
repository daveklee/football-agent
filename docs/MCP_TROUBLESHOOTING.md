# MCP Server Troubleshooting Guide

## Yahoo Fantasy MCP Server Connection Issues

### Symptoms
- "Cleaning up disconnected session: stdio_session"
- "Connection closed" errors
- MCP tools not available

### Common Causes

1. **PYTHONPATH Not Set Correctly**
   - The Yahoo Fantasy MCP server imports from `src` module
   - Solution: Ensure `PYTHONPATH` includes `fantasy-football-mcp-public` directory
   - Fixed in `app/agent.py` - PYTHONPATH is automatically set

2. **Environment Variables Missing**
   - Server needs `YAHOO_ACCESS_TOKEN`, `YAHOO_REFRESH_TOKEN`, etc.
   - Solution: Check `mcp_config.json` has all required env vars
   - Verify tokens are valid (they expire)

3. **Script Path Issues**
   - Relative paths might not work
   - Solution: Code now uses absolute paths

4. **Server Exiting Immediately**
   - MCP stdio servers need active stdin/stdout
   - If stdin closes, server exits
   - This is normal behavior for stdio servers

### Debugging Steps

1. **Check Server Can Start**:
   ```bash
   cd fantasy-football-mcp-public
   PYTHONPATH=. python fantasy_football_multi_league.py
   ```
   Server should wait for stdin (this is normal - it's waiting for MCP protocol messages)

2. **Check Environment Variables**:
   ```bash
   python -c "import json; config = json.load(open('mcp_config.json')); print(config['mcpServers']['yahoo-fantasy']['env'].keys())"
   ```

3. **Check PYTHONPATH**:
   ```bash
   python -c "from app.agent import root_agent; print('Tools:', len(root_agent.tools))"
   ```
   Look for log message showing PYTHONPATH

4. **Check Server Logs**:
   - ADK web server logs show MCP connection attempts
   - Look for "Yahoo MCP: Script=..." log message
   - Check for any error messages during toolset creation

### Current Configuration

The agent now:
- ✅ Sets PYTHONPATH automatically
- ✅ Uses absolute script paths
- ✅ Merges environment variables correctly
- ✅ Has increased timeout (60 seconds)
- ✅ Logs configuration for debugging

### If Still Not Working

1. **Verify Tokens Are Valid**:
   - Yahoo OAuth tokens expire
   - Run: `cd fantasy-football-mcp-public && python reauth_yahoo.py`

2. **Check Server Dependencies**:
   ```bash
   cd fantasy-football-mcp-public
   pip install -r requirements.txt
   ```

3. **Test Server Manually**:
   ```bash
   cd fantasy-football-mcp-public
   PYTHONPATH=. python fantasy_football_multi_league.py
   ```
   Send MCP protocol messages via stdin to test

4. **Check ADK Logs**:
   - Look for "Yahoo MCP: Script=..." message
   - Check for any exceptions during toolset creation
   - Look for MCP session errors

### Browser MCP

Browser MCP is currently disabled because:
- npm package `@modelcontextprotocol/server-browser` doesn't exist
- Browser MCP uses Chrome extension + different transport
- See `BROWSER_MCP_SETUP.md` for details

### Getting Help

1. Check logs in ADK web interface
2. Review `mcp_config.json` configuration
3. Verify Yahoo tokens are valid
4. Check `fantasy-football-mcp-public` repository for server-specific issues

