# Port Configuration Guide

This document explains port assignments for all services to avoid conflicts.

## Default Port Assignments

| Service | Port | Transport | Notes |
|---------|------|-----------|-------|
| **ADK Web Server** | **8080** | HTTP | Main web interface for agent interaction |
| Yahoo Fantasy MCP Server | stdio | stdio | Uses stdin/stdout (no port needed) |
| Browser MCP Server | stdio | stdio | Uses stdin/stdout (no port needed) |
| Yahoo Fantasy MCP HTTP (optional) | 8001 | HTTP | Only if HTTP transport is needed |
| Browser MCP HTTP (optional) | 8002 | HTTP | Only if HTTP transport is needed |

## Understanding MCP Transport

### stdio Transport (Default)

MCP servers configured in `mcp_config.json` use **stdio transport** by default. This means:
- ✅ **No ports needed** - Communication via stdin/stdout
- ✅ **No conflicts** - No port binding required
- ✅ **Recommended** - Standard MCP communication method

### HTTP Transport (Optional)

If you need HTTP transport for MCP servers:
- Yahoo Fantasy MCP: Set `PORT=8001` environment variable
- Browser MCP: Configure HTTP port in server settings

## Configuration

### ADK Web Server Port

The ADK web server port is configured via:

1. **Environment Variable** (recommended):
   ```bash
   export ADK_WEB_PORT=8080
   adk web
   ```

2. **Command Line** (if supported):
   ```bash
   adk web --port 8080
   ```

3. **Configuration File**: Set in `.env`:
   ```
   ADK_WEB_PORT=8080
   ```

### Yahoo Fantasy MCP Server Port (HTTP mode only)

If running in HTTP mode:
```bash
cd fantasy-football-mcp-public
PORT=8001 python fastmcp_server.py
```

### Browser MCP Server Port (HTTP mode only)

Browser MCP typically uses stdio. For HTTP mode, configure in the server settings.

## Starting Services

### Recommended: Use stdio (No Port Conflicts)

```bash
# Start ADK web server (uses port 8080)
./start_adk_web.sh

# MCP servers run automatically via stdio (no ports needed)
```

### Alternative: HTTP Transport

If you need HTTP transport for MCP servers:

```bash
# Terminal 1: Start ADK web server
./start_adk_web.sh

# Terminal 2: Start MCP servers in HTTP mode
./start_mcp_servers.sh
```

## Verifying Port Usage

Check which ports are in use:

```bash
# macOS/Linux
lsof -i :8080
lsof -i :8001
lsof -i :8002

# Or use netstat
netstat -an | grep LISTEN | grep -E '8080|8001|8002'
```

## Troubleshooting Port Conflicts

### Error: "Port already in use"

1. **Find the process using the port**:
   ```bash
   lsof -i :8080  # or :8001, :8002
   ```

2. **Kill the process** (if safe to do so):
   ```bash
   kill -9 <PID>
   ```

3. **Or change the port**:
   - Update `ADK_WEB_PORT` in `.env`
   - Or use a different port for MCP servers

### MCP Servers Not Connecting

- **Check transport mode**: MCP servers should use stdio by default
- **Verify `mcp_config.json`**: Should have `"type": "stdio"` or no type (defaults to stdio)
- **Check logs**: Look for connection errors in ADK/MCP logs

## Port Assignment Summary

```
┌─────────────────────────────────────────┐
│  ADK Web Server                        │
│  Port: 8080                            │
│  URL: http://localhost:8080            │
└─────────────────────────────────────────┘
              │
              ├───> Yahoo Fantasy MCP (stdio)
              │     No port needed
              │
              └───> Browser MCP (stdio)
                    No port needed

Optional HTTP Mode:
┌─────────────────────────────────────────┐
│  Yahoo Fantasy MCP HTTP                 │
│  Port: 8001                            │
│  URL: http://localhost:8001             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Browser MCP HTTP                      │
│  Port: 8002                            │
│  URL: http://localhost:8002             │
└─────────────────────────────────────────┘
```

## Best Practices

1. **Use stdio for MCP servers** - No port conflicts, standard MCP protocol
2. **ADK web on 8080** - Common web server port, avoids conflicts
3. **Check ports before starting** - Use `lsof` or `netstat` to verify
4. **Use environment variables** - Easy to change ports without code changes

## Environment Variables

Add to your `.env` file:

```bash
# ADK Web Server
ADK_WEB_PORT=8080

# MCP Server URLs (for HTTP transport only, if needed)
MCP_YAHOO_SERVER_URL=http://localhost:8001
MCP_BROWSER_SERVER_URL=http://localhost:8002

# Yahoo Fantasy MCP HTTP port (if using HTTP transport)
PORT=8001
```

---

**Note**: The default configuration uses stdio transport for MCP servers, which requires no ports. Only configure HTTP ports if you specifically need HTTP transport.

