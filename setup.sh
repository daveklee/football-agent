#!/bin/bash

# Setup script for Fantasy Football Agent

set -e

echo "🏈 Setting up Fantasy Football Agent..."

# Check Python version
echo "Checking Python version..."
python3 --version

# Clone Yahoo Fantasy Football MCP Server
if [ ! -d "fantasy-football-mcp-public" ]; then
    echo "Cloning Yahoo Fantasy Football MCP Server..."
    git clone https://github.com/derekrbreese/fantasy-football-mcp-public.git
else
    echo "Yahoo Fantasy Football MCP Server already cloned, updating..."
    cd fantasy-football-mcp-public
    git pull
    cd ..
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies for main project
echo "Installing main project dependencies..."
pip install -r requirements.txt

# Install dependencies for Yahoo Fantasy MCP Server
# The Yahoo Fantasy MCP Server has its own requirements
echo "Installing Yahoo Fantasy MCP Server dependencies..."
if [ -f "fantasy-football-mcp-public/requirements.txt" ]; then
    pip install -r fantasy-football-mcp-public/requirements.txt
else
    echo "⚠️  Yahoo Fantasy MCP Server requirements.txt not found"
    echo "   Make sure the repository was cloned successfully"
fi

# Browser MCP setup instructions
echo ""
echo "📱 Browser MCP Setup:"
echo "1. Install Browser MCP Chrome extension: https://browsermcp.io/"
echo "2. Make sure you're logged into Yahoo Fantasy Football in Chrome"
echo "3. Browser MCP uses your existing browser profile - no ChromeDriver needed!"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cat > .env << EOF
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Yahoo Fantasy Football API Credentials
# Get these from https://developer.yahoo.com/api/
YAHOO_CONSUMER_KEY=your_yahoo_consumer_key
YAHOO_CONSUMER_SECRET=your_yahoo_consumer_secret
YAHOO_LEAGUE_ID=your_league_id
YAHOO_GAME_ID=449

# Yahoo OAuth Tokens (set up via fantasy-football-mcp-public setup scripts)
YAHOO_ACCESS_TOKEN=your_access_token
YAHOO_REFRESH_TOKEN=your_refresh_token
YAHOO_GUID=your_yahoo_guid

# Yahoo Account Credentials (for browser automation)
YAHOO_EMAIL=your_yahoo_email@example.com
YAHOO_PASSWORD=your_yahoo_password

# ADK Configuration
ADK_PROJECT_ID=football-agent
ADK_REGION=us-central1

# ADK Web Server Configuration
ADK_WEB_PORT=8080

# MCP Server Configuration (for HTTP transport if needed)
# Note: MCP servers use stdio by default, these URLs are only for HTTP transport
MCP_YAHOO_SERVER_URL=http://localhost:8001
MCP_BROWSER_SERVER_URL=http://localhost:8002
EOF
    echo "⚠️  Please edit .env file with your actual credentials"
    echo ""
    echo "📝 Next steps:"
    echo "1. Set up Yahoo OAuth using: cd fantasy-football-mcp-public && python setup_yahoo_auth.py"
    echo "2. Or manually authenticate: cd fantasy-football-mcp-public && python reauth_yahoo.py"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the agent: python main.py"
echo "4. Or use ADK web interface: adk web"

