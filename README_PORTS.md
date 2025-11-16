# Port Configuration - Quick Reference

## Default Setup (Recommended)

**MCP servers use stdio transport** - No ports needed! This is the standard MCP protocol.

```
ADK Web Server:     Port 8080  (HTTP)
Yahoo Fantasy MCP:   stdio      (no port)
Browser MCP:         stdio      (no port)
```

## Starting Services

### Standard Setup (stdio MCP servers)

```bash
# Start ADK web server (port 8080)
./start_adk_web.sh

# MCP servers start automatically via stdio (no ports needed)
```

### If You Need HTTP Transport for MCP Servers

```bash
# Terminal 1: ADK web server
./start_adk_web.sh

# Terminal 2: Yahoo Fantasy MCP HTTP server (port 8001)
cd fantasy-football-mcp-public
PORT=8001 python fastmcp_server.py

# Terminal 3: Browser MCP HTTP (if needed, port 8002)
# Configure in Browser MCP settings
```

## Port Assignments

| Service | Port | Transport | When Needed |
|---------|------|-----------|-------------|
| ADK Web Server | 8080 | HTTP | Always (main interface) |
| Yahoo Fantasy MCP | stdio | stdio | Default (recommended) |
| Yahoo Fantasy MCP HTTP | 8001 | HTTP | Only if HTTP transport needed |
| Browser MCP | stdio | stdio | Default (recommended) |
| Browser MCP HTTP | 8002 | HTTP | Only if HTTP transport needed |

## Configuration

### Change ADK Web Port

```bash
# Via environment variable
export ADK_WEB_PORT=9000
./start_adk_web.sh

# Or edit .env file
ADK_WEB_PORT=9000
```

### Verify Port Usage

```bash
# Check what's using ports
lsof -i :8080
lsof -i :8001
lsof -i :8002
```

## Troubleshooting

**Port 8000 conflict?**
- ADK web server now uses 8080 by default
- MCP servers use stdio (no ports needed)
- If you see port 8000 conflicts, check for other services

**MCP servers not connecting?**
- Verify `mcp_config.json` uses stdio transport (default)
- Check that MCP server processes are running
- Review ADK/MCP logs for connection errors

See `PORT_CONFIGURATION.md` for complete details.

