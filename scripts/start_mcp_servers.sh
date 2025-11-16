#!/bin/bash

# Start MCP Servers in HTTP mode (if needed)
# By default, MCP servers use stdio and don't need ports
# This script is only needed if you want HTTP transport

set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting MCP Servers in HTTP mode..."
echo ""
echo "Port assignments:"
echo "  - Yahoo Fantasy MCP Server: 8001"
echo "  - Browser MCP Server: 8002"
echo ""
echo "⚠️  Note: MCP servers typically use stdio (no ports needed)"
echo "   Only use HTTP mode if specifically required"
echo ""

# Start Yahoo Fantasy MCP Server on port 8001
if [ -f "fantasy-football-mcp-public/fastmcp_server.py" ]; then
    echo "Starting Yahoo Fantasy MCP Server on port 8001..."
    cd fantasy-football-mcp-public
    PORT=8001 python fastmcp_server.py &
    YAHOO_PID=$!
    cd ..
    echo "Yahoo Fantasy MCP Server started (PID: $YAHOO_PID)"
else
    echo "⚠️  Yahoo Fantasy MCP Server not found. Run ./scripts/setup.sh first."
fi

# Browser MCP typically uses stdio, but if HTTP is needed:
# npx -y @modelcontextprotocol/server-browser --port 8002

echo ""
echo "MCP Servers started. Press Ctrl+C to stop."
wait

