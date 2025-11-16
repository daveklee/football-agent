# Project Structure

This document describes the project structure, which follows Google ADK's recommended layout.

## Directory Structure

```
football-agent/
├── app/                          # Core application code
│   ├── __init__.py              # Package initialization
│   ├── agent.py                 # Main agent logic (FantasyFootballAgent)
│   ├── server.py                # FastAPI Backend server
│   └── utils/                   # Utility functions and helpers
│       ├── __init__.py          # Utils package initialization
│       ├── config.py            # Configuration management (Settings)
│       └── tools/               # Agent tools
│           ├── __init__.py      # Tools package initialization
│           ├── yahoo_tools.py   # Yahoo Fantasy API wrapper
│           ├── browser_tools.py # Browser automation wrapper
│           └── analysis_tools.py # LLM analysis tools
│
├── fantasy-football-mcp-public/ # Yahoo Fantasy MCP Server (external)
│   └── ...                      # Cloned from GitHub
│
├── main.py                      # Entry point for agent
├── example_usage.py            # Example usage scripts
├── verify_setup.py             # Setup verification script
│
├── mcp_config.json             # MCP server configuration
├── adk_config.yaml             # ADK-specific configuration
├── .env                         # Environment variables (not in git)
│
├── Makefile                     # Common commands
├── pyproject.toml              # Project dependencies and configuration
├── requirements.txt            # Python dependencies
├── setup.sh                    # Setup script
├── start_adk_web.sh            # Start ADK web interface
├── start_mcp_servers.sh         # Start MCP servers (optional HTTP)
│
├── README.md                    # Main documentation
├── QUICKSTART.md               # Quick start guide
├── GEMINI.md                    # AI-assisted development guide
├── STRUCTURE.md                 # This file
├── PORT_CONFIGURATION.md        # Port configuration guide
├── PROJECT_SUMMARY.md           # Project overview
└── ...                          # Other documentation files
```

## Key Files

### Application Code (`app/`)

- **`app/agent.py`**: Main agent class `FantasyFootballAgent` extending Google ADK's `Agent`
- **`app/server.py`**: FastAPI REST API server with endpoints for agent functionality
- **`app/utils/config.py`**: Settings management using `pydantic-settings`
- **`app/utils/tools/`**: Agent tools that wrap MCP server functionality

### Configuration

- **`mcp_config.json`**: MCP server configuration (Yahoo Fantasy, Browser MCP)
- **`adk_config.yaml`**: ADK-specific agent configuration
- **`.env`**: Environment variables (API keys, credentials) - not committed to git

### Entry Points

- **`main.py`**: Main entry point, creates `AgentRunner` for ADK web interface
- **`example_usage.py`**: Example scripts showing how to use the agent

### Build & Development

- **`Makefile`**: Common commands (`make run-web`, `make run-server`, etc.)
- **`pyproject.toml`**: Project metadata, dependencies, and tool configuration
- **`requirements.txt`**: Python dependencies list

## Import Structure

All imports use the `app` package prefix:

```python
# From main.py or other root-level files
from app.agent import agent, FantasyFootballAgent
from app.utils.config import settings
from app.utils.tools.yahoo_tools import YahooFantasyTools

# Within app/ package
from app.utils.config import settings
from app.utils.tools.yahoo_tools import YahooFantasyTools
```

## Running the Application

### ADK Web Interface (Recommended)

```bash
make run-web
# or
./start_adk_web.sh
```

### FastAPI Server

```bash
make run-server
# or
python -m app.server
```

### Direct Agent Usage

```bash
python main.py
# or
make run
```

## ADK Discovery

Google ADK automatically discovers:
- Agent class in `app/agent.py`
- Tools registered in the agent
- MCP servers configured in `mcp_config.json`
- Configuration from `adk_config.yaml` and environment variables

The `app/` directory structure ensures proper discovery by ADK's web interface and CLI tools.

## Adding New Components

### Adding a New Tool

1. Create tool class in `app/utils/tools/your_tool.py`
2. Implement `get_tools()` method returning list of `Tool` objects
3. Import and initialize in `app/agent.py`:

```python
from app.utils.tools.your_tool import YourTool

# In FantasyFootballAgent.__init__()
self.your_tool = YourTool()
all_tools.extend(self.your_tool.get_tools())
```

### Adding a New Utility

1. Create utility module in `app/utils/your_util.py`
2. Import where needed:

```python
from app.utils.your_util import your_function
```

### Adding API Endpoints

Add new endpoints to `app/server.py`:

```python
@app.post("/api/your-endpoint")
async def your_endpoint():
    result = await agent.your_method()
    return {"success": True, "result": result}
```

## Best Practices

1. **Keep `app/` focused**: Only application code, not scripts or configs
2. **Use relative imports within `app/`**: `from app.utils.config import settings`
3. **Use absolute imports from root**: `from app.agent import agent`
4. **Follow ADK patterns**: Structure matches Google ADK examples
5. **Document changes**: Update this file when structure changes

## See Also

- `GEMINI.md` - AI-assisted development guide
- `README.md` - Main documentation
- `QUICKSTART.md` - Quick start guide

