# AI-Assisted Development Guide

This document provides guidance for using AI assistants (like Gemini, Claude, etc.) to help develop and maintain the Fantasy Football Agent.

## Project Structure

The project follows Google ADK's recommended structure:

```
football-agent/
├── app/                 # Core application code
│   ├── agent.py         # Main agent logic
│   ├── server.py        # FastAPI Backend server
│   └── utils/           # Utility functions and helpers
│       ├── config.py    # Configuration management
│       └── tools/       # Agent tools (Yahoo, Browser, Analysis)
├── Makefile             # Common commands
├── pyproject.toml       # Project dependencies and configuration
└── README.md            # Main documentation
```

## Key Components

### Agent (`app/agent.py`)

The main agent class `FantasyFootballAgent` extends Google ADK's `Agent` class. It:
- Coordinates all tools (Yahoo, Browser, Analysis)
- Provides high-level management functions
- Uses LLM for decision-making

### Server (`app/server.py`)

FastAPI backend server that exposes REST API endpoints for:
- Lineup optimization
- Waiver wire evaluation
- Trade evaluation
- Weekly management

### Tools (`app/utils/tools/`)

- **yahoo_tools.py**: Wrapper for Yahoo Fantasy MCP Server
- **browser_tools.py**: Wrapper for Browser MCP
- **analysis_tools.py**: LLM-powered analysis and decision-making

## Development Workflow

### Using Makefile

```bash
make install      # Install dependencies
make run-web      # Start ADK web interface
make run-server   # Start FastAPI server
make test         # Run tests
make lint         # Run linter
make format       # Format code
```

### Using ADK Web Interface

```bash
make run-web
# or
./start_adk_web.sh
```

Access at `http://localhost:8080`

### Using FastAPI Server

```bash
make run-server
# or
python -m app.server
```

API endpoints available at `http://localhost:8080/api/`

## Common Tasks

### Adding a New Tool

1. Create tool class in `app/utils/tools/`
2. Implement `get_tools()` method returning list of Tool objects
3. Import and initialize in `app/agent.py`
4. Add to agent's tools list

### Modifying Agent Behavior

Edit `_get_agent_instruction()` in `app/agent.py` to change agent's decision-making priorities.

### Adding API Endpoints

Add new endpoints to `app/server.py` following FastAPI patterns.

## MCP Integration

The agent uses MCP servers for external integrations:
- Yahoo Fantasy MCP Server: `fantasy-football-mcp-public/`
- Browser MCP: Chrome extension + npm package

Configure in `mcp_config.json`.

## Testing

```bash
make test
```

Or run specific tests:
```bash
pytest tests/test_specific.py
```

## Code Style

- Use `make format` to format code with Black
- Use `make lint` to check code with Ruff
- Follow PEP 8 style guide

## Debugging

- Check logs in console output
- Use ADK web interface for interactive debugging
- Review MCP server logs if issues with external integrations

## Getting Help

- Check `README.md` for setup instructions
- Review `PORT_CONFIGURATION.md` for port setup
- See `REQUIREMENTS.md` for dependency details
- Check `DOCUMENTATION_INDEX.md` for all documentation

