# Requirements and Dependencies

This document explains the dependencies for the Fantasy Football Agent project.

## Architecture Overview

This project uses **MCP (Model Context Protocol) servers** for external integrations:

1. **Yahoo Fantasy Football MCP Server** - Handles all Yahoo Fantasy API access
2. **Browser MCP Server** - Handles all browser automation

The agent itself has minimal dependencies since it delegates to these MCP servers.

## Core Agent Dependencies

The `requirements.txt` file contains only the essential dependencies for the agent itself:

### Required

- **google-adk** - Google Agent Development Kit framework
- **google-generativeai** - Google Gemini API for LLM decision-making
- **python-dotenv** - Environment variable management
- **pydantic** & **pydantic-settings** - Configuration management

### Standard Library (No Installation Needed)

- `asyncio` - Async support (Python 3.7+)
- `logging` - Logging functionality
- `typing` - Type hints
- `sys` - System utilities

## MCP Server Dependencies

### Yahoo Fantasy Football MCP Server

**Repository**: https://github.com/derekrbreese/fantasy-football-mcp-public

**Dependencies**: Installed separately via `fantasy-football-mcp-public/requirements.txt`

**What it provides**:
- Yahoo Fantasy Football API access
- League and team data
- Player information
- Lineup optimization
- Waiver wire analysis
- Draft assistance

**Installation**: Automatically handled by `setup.sh` which clones the repository and installs its dependencies.

### Browser MCP Server

**Website**: https://browsermcp.io/

**Dependencies**: 
- Chrome extension (install from website)
- npm package: `@modelcontextprotocol/server-browser` (installed via npx)

**What it provides**:
- Browser navigation
- Click, type, hover actions
- Screenshots and snapshots
- Drag and drop
- Console log access

**Installation**: 
1. Install Chrome extension: https://browsermcp.io/
2. Server runs via npx (configured in `mcp_config.json`)

## What's NOT Included

The following are **not** in `requirements.txt` because:

- **yahoofantasy** - Yahoo Fantasy MCP Server handles this
- **selenium/playwright** - Browser MCP handles browser automation
- **requests/beautifulsoup4** - Not directly used in agent code
- **aiohttp** - Not directly used in agent code
- **python-dateutil/pytz** - Not directly used in agent code

If you need these for custom extensions, install them separately.

## Installation Process

When you run `./setup.sh`, it:

1. Clones Yahoo Fantasy MCP Server repository
2. Creates Python virtual environment
3. Installs agent dependencies (`requirements.txt`)
4. Installs Yahoo Fantasy MCP Server dependencies (`fantasy-football-mcp-public/requirements.txt`)
5. Prompts you to install Browser MCP Chrome extension

## Verification

Run `python verify_setup.py` to check:
- Python version
- Core dependencies
- Environment variables
- Gemini API connection
- Browser MCP (if extension installed)

## Updating Dependencies

### Agent Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Yahoo Fantasy MCP Server
```bash
cd fantasy-football-mcp-public
git pull
pip install -r requirements.txt
cd ..
```

### Browser MCP
- Update Chrome extension from Chrome Web Store
- Server updates automatically via npx

## Troubleshooting

### Missing Dependencies

If you get import errors:
1. Make sure virtual environment is activated: `source venv/bin/activate`
2. Reinstall requirements: `pip install -r requirements.txt`
3. Check Yahoo Fantasy MCP Server dependencies: `pip install -r fantasy-football-mcp-public/requirements.txt`

### MCP Server Issues

- **Yahoo Fantasy MCP**: Check that repository was cloned and dependencies installed
- **Browser MCP**: Verify Chrome extension is installed and enabled

## Summary

The agent has **minimal dependencies** because it uses MCP servers for external integrations. This keeps the agent lightweight and makes it easy to update or replace MCP servers without changing the agent code.

