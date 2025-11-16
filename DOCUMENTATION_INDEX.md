# Documentation Index

This document provides an overview of all documentation files and their purposes.

## Quick Reference

- **New to the project?** → Start with [QUICKSTART.md](QUICKSTART.md)
- **Setting up?** → See [SETUP_NOTES.md](SETUP_NOTES.md) for detailed instructions
- **Understanding architecture?** → Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **Dependency questions?** → Check [REQUIREMENTS.md](REQUIREMENTS.md)
- **MCP server details?** → See [MCP_SERVER_INFO.md](MCP_SERVER_INFO.md) and [BROWSER_MCP_INFO.md](BROWSER_MCP_INFO.md)

## Documentation Files

### Core Documentation

1. **[README.md](README.md)** - Main project documentation
   - Overview and features
   - Complete setup instructions
   - Usage guide
   - Troubleshooting
   - Links to all resources

2. **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
   - Step-by-step setup for new users
   - Prerequisites checklist
   - Common issues and solutions
   - Testing instructions

3. **[SETUP_NOTES.md](SETUP_NOTES.md)** - Detailed setup information
   - Google ADK installation options
   - Yahoo OAuth setup
   - MCP server configuration
   - Testing procedures
   - Troubleshooting guide

### Architecture & Design

4. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture overview
   - Component descriptions
   - Data flow diagrams
   - Technology stack
   - Project structure
   - Configuration details

5. **[UPDATE_NOTES.md](UPDATE_NOTES.md)** - Recent changes
   - Migration to MCP-based architecture
   - What changed and why
   - Migration guide for existing setups
   - Available MCP tools

### MCP Server Documentation

6. **[MCP_SERVER_INFO.md](MCP_SERVER_INFO.md)** - Yahoo Fantasy MCP Server
   - Features and capabilities
   - Available tools
   - Installation and setup
   - Configuration details
   - Credits

7. **[BROWSER_MCP_INFO.md](BROWSER_MCP_INFO.md)** - Browser MCP
   - What is Browser MCP
   - Installation (Chrome extension)
   - Available tools
   - How it works
   - Benefits over Selenium
   - Troubleshooting

### Dependencies & Requirements

8. **[REQUIREMENTS.md](REQUIREMENTS.md)** - Dependency documentation
   - Core agent dependencies
   - MCP server dependencies
   - What's included and why
   - What's excluded and why
   - Installation process
   - Updating dependencies

### Configuration Files

- **[mcp_config.json](mcp_config.json)** - MCP server configuration
- **[adk_config.yaml](adk_config.yaml)** - ADK configuration
- **[.env.example](.env.example)** - Environment variables template (if exists)

### Other Files

- **[verify_setup.py](verify_setup.py)** - Setup verification script
- **[example_usage.py](example_usage.py)** - Usage examples
- **[setup.sh](setup.sh)** - Automated setup script

## Key Concepts

### MCP Architecture

This project uses **MCP (Model Context Protocol) servers** for external integrations:

1. **Yahoo Fantasy MCP Server** (External Repository)
   - Location: `fantasy-football-mcp-public/` (cloned during setup)
   - Purpose: Yahoo Fantasy Football API access
   - Provides: League data, lineup optimization, waiver wire analysis, etc.

2. **Browser MCP** (Chrome Extension + npm package)
   - Extension: Install from https://browsermcp.io/
   - Server: Runs via npx (configured in `mcp_config.json`)
   - Purpose: Browser automation using your Chrome profile

### Agent Structure

The agent itself has minimal dependencies and acts as a coordinator:

- **Agent Core** (`agent.py`) - Main agent logic
- **Yahoo Tools** (`tools/yahoo_tools.py`) - Wrapper for Yahoo Fantasy MCP Server
- **Browser Tools** (`tools/browser_tools.py`) - Wrapper for Browser MCP
- **Analysis Tools** (`tools/analysis_tools.py`) - LLM decision-making

## Setup Flow

1. **Prerequisites** → Install Python, Node.js, Chrome
2. **Run Setup** → `./setup.sh` clones repos and installs dependencies
3. **Configure** → Set up `.env` with API keys and credentials
4. **OAuth** → Complete Yahoo OAuth flow via MCP server scripts
5. **Browser MCP** → Install Chrome extension
6. **Verify** → Run `python verify_setup.py`
7. **Start** → Run `adk web` or `python main.py`

## Common Tasks

### First Time Setup
→ [QUICKSTART.md](QUICKSTART.md)

### Understanding Dependencies
→ [REQUIREMENTS.md](REQUIREMENTS.md)

### Configuring MCP Servers
→ [MCP_SERVER_INFO.md](MCP_SERVER_INFO.md) and [BROWSER_MCP_INFO.md](BROWSER_MCP_INFO.md)

### Troubleshooting
→ [SETUP_NOTES.md](SETUP_NOTES.md) and [README.md](README.md)

### Understanding Architecture
→ [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## Documentation Updates

All documentation has been updated to reflect the MCP-based architecture:

- ✅ Removed Selenium/ChromeDriver references
- ✅ Added Browser MCP setup instructions
- ✅ Updated Yahoo Fantasy MCP Server information
- ✅ Clarified dependency structure
- ✅ Updated troubleshooting sections
- ✅ Added MCP-specific testing procedures

## Need Help?

1. Check the relevant documentation file above
2. Review error messages and logs
3. Verify all prerequisites are installed
4. Run `python verify_setup.py` to check your setup
5. Check MCP server logs for connection issues

---

**Last Updated**: Documentation reflects MCP-based architecture with Yahoo Fantasy MCP Server and Browser MCP integration.

