# Browser MCP Setup Issue

## Current Status

Browser MCP is **temporarily disabled** because the npm package `@modelcontextprotocol/server-browser` doesn't exist in the npm registry.

## The Problem

The current `mcp_config.json` configuration tries to use:
```json
{
  "browsermcp": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-browser"]
  }
}
```

This fails with:
```
npm error 404 Not Found - GET https://registry.npmjs.org/@modelcontextprotocol%2fserver-browser - Not found
```

## Browser MCP Architecture

Browser MCP works differently than standard MCP servers:

1. **Chrome Extension**: Browser MCP uses a Chrome extension (install from https://browsermcp.io/)
2. **Local Server**: The extension connects to a local MCP server
3. **Transport**: Likely uses SSE (Server-Sent Events) or HTTP transport, not stdio

## Solutions

### Option 1: Use Browser MCP with SSE Transport

Browser MCP may need to be configured with SSE transport instead of stdio. Check the Browser MCP documentation for the correct setup.

### Option 2: Use Alternative Browser Automation

For now, the agent works with Yahoo Fantasy MCP for data access. Browser automation can be added later when Browser MCP is properly configured.

### Option 3: Manual Browser Actions

You can manually make changes in your browser while the agent provides recommendations via Yahoo Fantasy MCP tools.

## Current Workaround

The agent is configured to work with:
- ✅ **Yahoo Fantasy MCP Server** - Full data access and analysis
- ❌ **Browser MCP** - Temporarily disabled

The agent can still:
- Get team data, league settings, matchups
- Analyze lineups and make recommendations
- Evaluate waiver wire and trades
- Provide detailed analysis

You'll need to manually execute browser actions (lineup changes, add/drop players, trades) based on the agent's recommendations.

## Next Steps

1. Check Browser MCP documentation: https://browsermcp.io/
2. Verify if Browser MCP uses SSE transport
3. Update `mcp_config.json` with correct Browser MCP configuration
4. Re-enable Browser MCP in `app/agent.py` (change `if False` to `if True`)

## References

- Browser MCP Website: https://browsermcp.io/
- Browser MCP Documentation: https://docs.browsermcp.io/
- MCP Protocol: https://modelcontextprotocol.io/

