#!/bin/bash

# Start ADK Web Server on a specific port
# This script ensures the ADK web server uses port 8080 to avoid conflicts

set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set ADK web port (defaults to 8080, can be overridden via .env or command line)
ADK_PORT=${ADK_WEB_PORT:-8080}
if [ ! -z "$1" ]; then
    ADK_PORT=$1
fi

echo "🚀 Starting ADK Web Server..."
echo ""
echo "Port Configuration:"
echo "  ✅ ADK Web Server: port $ADK_PORT"
echo "  ✅ Yahoo Fantasy MCP Server: stdio transport (no port needed)"
echo "  ✅ Browser MCP Server: stdio transport (no port needed)"
echo ""
echo "Access the web interface at: http://localhost:$ADK_PORT"
echo ""
echo "Note: MCP servers use stdio transport by default (configured in mcp_config.json)"
echo "      They communicate via stdin/stdout and don't require ports."
echo ""

# Try different ways to start ADK web server with port
# Method 1: Try with --port flag
if command -v adk &> /dev/null; then
    # Check if adk web supports --port flag
    if adk web --help 2>&1 | grep -q "port\|PORT"; then
        echo "Starting with: adk web --port $ADK_PORT"
        adk web --port $ADK_PORT
    else
        # Method 2: Set port via environment variable
        echo "Starting with: PORT=$ADK_PORT adk web"
        PORT=$ADK_PORT adk web
    fi
else
    echo "❌ Error: 'adk' command not found"
    echo "   Make sure Google ADK is installed and virtual environment is activated"
    exit 1
fi

